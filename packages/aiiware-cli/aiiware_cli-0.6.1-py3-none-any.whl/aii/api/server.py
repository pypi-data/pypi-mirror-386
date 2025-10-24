"""
FastAPI-based HTTP server for AII API mode.

Features:
- RESTful API for function execution
- WebSocket streaming for real-time responses
- API key authentication
- Rate limiting per key
- CORS support for web integrations
- OpenAPI documentation
"""

from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from typing import Optional
from datetime import datetime
import secrets
import os

# Get version from package metadata (single source of truth: pyproject.toml)
try:
    from importlib.metadata import version
    __version__ = version("aiiware-cli")
except Exception:
    __version__ = "0.5.2"  # Fallback if package not installed

logger = logging.getLogger(__name__)

from aii.core.engine import AIIEngine
from aii.core.models import ExecutionResult
from aii.config.manager import ConfigManager
from aii.cli.output_mode_formatter import OutputMode
from aii.api.models import (
    ExecuteRequest, ExecuteResponse,
    FunctionsResponse, FunctionInfo,
    StatusResponse, MCPStatusRequest
)


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via AII_DEBUG environment variable."""
    return os.environ.get("AII_DEBUG", "0") == "1"


def debug_print(message: str) -> None:
    """Print debug message only if AII_DEBUG=1."""
    if is_debug_enabled():
        import sys
        print(f"[DEBUG] {message}", file=sys.stderr, flush=True)


def format_completion_metadata(result: ExecutionResult) -> dict:
    """
    Extract token metadata from ExecutionResult for API completion responses.

    Ensures parity between REST and WebSocket API metadata structure.
    Resolves AII-CLI-WS-001: WebSocket token metadata bug.

    Args:
        result: ExecutionResult from function execution

    Returns:
        dict: Formatted metadata with tokens, cost, model, execution_time

    Example:
        >>> result = ExecutionResult(...)
        >>> metadata = format_completion_metadata(result)
        >>> metadata
        {
            "tokens": {"input": 245, "output": 182},
            "cost": 0.0042,
            "model": "gemini-2.0-flash-exp",
            "execution_time": 3.94
        }
    """
    # Initialize metadata dict
    metadata = {
        "execution_time": getattr(result, "execution_time", None)
    }

    # Extract result data (functions store token info in result.data dict)
    result_data = result.data if result.data else {}

    # Extract token usage from result.data
    # Functions store tokens as 'input_tokens' and 'output_tokens'
    input_tokens = result_data.get("input_tokens")
    output_tokens = result_data.get("output_tokens")

    # Add tokens if available (both must be present)
    if input_tokens is not None and output_tokens is not None:
        metadata["tokens"] = {
            "input": int(input_tokens) if input_tokens is not None else 0,
            "output": int(output_tokens) if output_tokens is not None else 0
        }
    else:
        metadata["tokens"] = None

    # Extract cost (may be in result.data or calculated separately)
    cost = result_data.get("cost") or result_data.get("estimated_cost")
    metadata["cost"] = float(cost) if cost is not None else None

    # Extract model name
    model = result_data.get("model") or result_data.get("provider")
    if model:
        metadata["model"] = str(model)

    # Extract confidence (optional, if available)
    confidence = result_data.get("confidence")
    if confidence is not None:
        metadata["confidence"] = float(confidence)

    # Extract reasoning (for THINKING and VERBOSE modes)
    reasoning = result_data.get("reasoning")
    if reasoning:
        metadata["reasoning"] = str(reasoning)

    # Extract session ID from SessionManager (for VERBOSE mode)
    from ..core.session.manager import SessionManager
    session = SessionManager.get_current_session()
    if session:
        metadata["session_id"] = session.session_id
        # Add success rate for quality assessment
        metadata["success_rate"] = session.success_rate if hasattr(session, 'success_rate') else None
        metadata["total_functions"] = session.total_functions if hasattr(session, 'total_functions') else None

    # Special handling for git_commit - include commit preview data
    if result_data.get("requires_commit_confirmation"):
        metadata["requires_commit_confirmation"] = True
        metadata["git_diff"] = result_data.get("git_diff")
        metadata["commit_message"] = result_data.get("commit_message")

    # Special handling for shell commands - include explanation and risks (v0.6.0)
    if result_data.get("requires_execution_confirmation"):
        metadata["requires_execution_confirmation"] = True
        metadata["command"] = result_data.get("command")
        metadata["explanation"] = result_data.get("explanation")
        metadata["risks"] = result_data.get("safety_notes") or result_data.get("risks", [])

    return metadata


app = FastAPI(
    title="Aii API",
    description="AI-powered command-line assistant API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Make configurable via config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> set[str]:
        """Load API keys from config."""
        keys = self.config.get("api.keys", [])
        return set(keys)

    def verify_key(self, api_key: str) -> bool:
        """Verify API key is valid."""
        return api_key in self.api_keys

    def add_key(self, api_key: str):
        """Add new API key and persist to config."""
        self.api_keys.add(api_key)

        # Persist to config
        keys = list(self.api_keys)
        self.config.set("api.keys", keys)


class RateLimiter:
    """Rate limiter per API key."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.limits: Dict[str, tuple[int, datetime]] = {}  # api_key -> (count, window_start)
        self.max_requests = config.get("api.rate_limit.max_requests", 100)
        self.window_seconds = config.get("api.rate_limit.window_seconds", 60)

    def allow(self, api_key: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.now()

        if api_key not in self.limits:
            self.limits[api_key] = (1, now)
            return True

        count, window_start = self.limits[api_key]

        # Check if window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            # Reset window
            self.limits[api_key] = (1, now)
            return True

        # Check if limit exceeded
        if count >= self.max_requests:
            return False

        # Increment count
        self.limits[api_key] = (count + 1, window_start)
        return True

    def get_remaining(self, api_key: str) -> int:
        """Get remaining requests in current window."""
        if api_key not in self.limits:
            return self.max_requests

        count, window_start = self.limits[api_key]
        now = datetime.now()

        # Window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            return self.max_requests

        return max(0, self.max_requests - count)


class APIServer:
    """
    HTTP server for AII API mode.

    Lifecycle:
    1. Initialize with AIIEngine and ConfigManager
    2. Start server with uvicorn
    3. Handle requests with authentication and rate limiting
    4. Shutdown gracefully

    Security:
    - API key authentication via AII-API-Key header
    - Rate limiting per key (100 req/min default)
    - Request/response logging
    - CORS configuration
    """

    def __init__(self, engine: AIIEngine, config: ConfigManager, initialization_status: dict = None):
        self.engine = engine
        self.config = config
        self.rate_limiter = RateLimiter(config)
        self.auth = APIKeyAuth(config)
        self.start_time = datetime.now()
        self.server: Optional[uvicorn.Server] = None
        # Track initialization status for client guidance
        self.initialization_status = initialization_status or {
            "llm_provider": True,  # Assume initialized by default
            "llm_error": None,
            "web_search": False,
            "web_error": None
        }

    async def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start HTTP server with uvicorn."""
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        self.server = uvicorn.Server(config)

        # Start server
        await self.server.serve()

    async def shutdown(self):
        """Graceful shutdown."""
        if self.server:
            self.server.should_exit = True

    def get_uptime(self) -> float:
        """Get server uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


# Global server instance (set by start_api_server)
server: Optional[APIServer] = None


def generate_api_key() -> str:
    """
    Generate default API key.

    Returns the standard development API key for local testing.
    For production, users should generate their own keys.
    """
    # Default key for local development and testing
    return "aii_sk_7WyvfQ0PRzufJ1G66Qn8Sm4gW9Tealpo6vOWDDUeiv4"


# Authentication middleware
async def verify_api_key(aii_api_key: str = Header(None, alias="AII-API-Key")) -> str:
    """Verify API key from AII-API-Key header."""
    if not aii_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include AII-API-Key header."
        )

    if not server or not server.auth.verify_key(aii_api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return aii_api_key


# Rate limiting middleware
async def check_rate_limit(api_key: str = Depends(verify_api_key)):
    """Check rate limit for API key."""
    if not server:
        return

    if not server.rate_limiter.allow(api_key):
        remaining = server.rate_limiter.get_remaining(api_key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. {remaining} requests remaining.",
            headers={
                "X-RateLimit-Limit": str(server.rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(server.rate_limiter.window_seconds)
            }
        )


# POST /api/execute - Execute function
@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_function(
    request: ExecuteRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute AII function with parameters.

    Example:
    ```bash
    curl -X POST http://localhost:16169/api/execute \\
      -H "Content-Type: application/json" \\
      -H "AII-API-Key: aii_sk_..." \\
      -d '{
        "function": "translate",
        "params": {"text": "hello", "to": "spanish"}
      }'
    ```

    Response:
    ```json
    {
      "success": true,
      "result": "hola",
      "metadata": {
        "tokens": {"input": 145, "output": 28},
        "cost": 0.0004,
        "execution_time": 1.23
      }
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    try:
        # For API mode, use function name directly from request
        # API clients specify the function explicitly, no need for intent recognition
        from aii.core.models import RecognitionResult, RouteSource

        function_name = request.function
        parameters = request.params or {}

        # Validate function exists
        if function_name not in server.engine.function_registry.plugins:
            raise HTTPException(
                status_code=404,
                detail=f"Function '{function_name}' not found"
            )

        # Create recognition result for API execution
        recognition_result = RecognitionResult(
            intent=function_name,
            confidence=1.0,  # API clients explicitly specify function
            parameters=parameters,
            function_name=function_name,
            requires_confirmation=False,  # API execution doesn't require confirmation
            reasoning="Direct API invocation",
            source=RouteSource.DIRECT_MATCH
        )

        # Execute function via execution engine
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=request.get_formatted_input(),
            chat_context=None,
            config=server.engine.config,
            llm_provider=server.engine.llm_provider,
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False
        )

        return ExecuteResponse(
            success=result.success,
            result=result.data if result.success else None,
            error=result.message if not result.success else None,
            metadata=format_completion_metadata(result)
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


# GET /api/functions - List available functions
@app.get("/api/functions", response_model=FunctionsResponse)
async def list_functions(
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    List all available AII functions.

    Response:
    ```json
    {
      "functions": [
        {
          "name": "translate",
          "description": "Translate text to another language",
          "parameters": {...},
          "safety": "safe",
          "default_output_mode": "clean"
        }
      ]
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Get all registered plugins
    plugins = server.engine.function_registry.plugins.values()

    functions_list = []
    for f in plugins:
        # Handle different attribute names (function_name vs name)
        name = getattr(f, 'function_name', None) or getattr(f, 'name', 'unknown')
        description = getattr(f, 'function_description', None) or getattr(f, 'description', '')

        # Get default output mode safely
        default_mode = None
        if hasattr(f, 'default_output_mode'):
            mode_attr = getattr(f, 'default_output_mode', None)
            if mode_attr and hasattr(mode_attr, 'value'):
                default_mode = mode_attr.value

        functions_list.append(FunctionInfo(
            name=name,
            description=description,
            parameters=f.get_parameters_schema() if hasattr(f, 'get_parameters_schema') else {},
            safety=f.get_function_safety().value if hasattr(f, 'get_function_safety') else 'unknown',
            default_output_mode=default_mode
        ))

    return FunctionsResponse(functions=functions_list)


# GET /health - Simple health check (no auth required)
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint for server monitoring.

    Used by CLI to detect if server is running.
    Returns 200 OK if server is healthy.

    No authentication required for health check.

    Response:
    ```json
    {
      "status": "healthy",
      "version": "0.6.0"
    }
    ```
    """
    return {
        "status": "healthy",
        "version": __version__
    }


# GET /api/status - Server status (no auth required)
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    Get server health status.

    No authentication required for status endpoint.

    Response:
    ```json
    {
      "status": "healthy",
      "version": "0.4.12",
      "uptime": 3600.5,
      "mcp_servers": {
        "total": 7,
        "enabled": 7
      }
    }
    ```
    """

    if not server:
        return StatusResponse(
            status="initializing",
            version=__version__,
            uptime=0.0
        )

    mcp_info = None
    try:
        # Load MCP server config from mcp_servers.json
        from pathlib import Path
        import json

        mcp_config_path = Path.home() / ".aii" / "mcp_servers.json"
        if mcp_config_path.exists():
            with open(mcp_config_path, "r") as f:
                config = json.load(f)
                servers = config.get("mcpServers", {})

                # Count total and enabled servers
                total = len(servers)
                enabled = sum(1 for s in servers.values() if s.get("enabled", True))

                mcp_info = {
                    "total": total,
                    "enabled": enabled
                }
    except Exception as e:
        # Silently fail for status endpoint
        logger.debug(f"Failed to load MCP server info: {e}")
        pass

    return StatusResponse(
        status="healthy",
        version=__version__,
        uptime=server.get_uptime(),
        mcp_servers=mcp_info,
        initialization=server.initialization_status
    )


# POST /api/mcp/status - Get MCP server health
@app.post("/api/mcp/status")
async def mcp_status(
    request: MCPStatusRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get health status for MCP servers.

    Request:
    ```json
    {
      "server_name": "github"  // optional, null for all
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Execute mcp_status function if available
    try:
        result = await server.engine.process_input(
            user_input=f"mcp status {request.server_name or ''}",
            context=None
        )

        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=500, detail=result.message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming
@app.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    """
    WebSocket endpoint for streaming function execution.

    Protocol:
    ```
    Client → Server: {"api_key": "...", "function": "translate", "params": {...}}
    Server → Client: {"type": "token", "data": "h"}
    Server → Client: {"type": "token", "data": "o"}
    Server → Client: {"type": "token", "data": "l"}
    Server → Client: {"type": "token", "data": "a"}
    Server → Client: {"type": "complete", "metadata": {...}}
    ```

    Error handling:
    ```
    Server → Client: {"type": "error", "message": "..."}
    ```
    """
    debug_print("SERVER: WebSocket endpoint called")

    await websocket.accept()
    debug_print("SERVER: WebSocket accepted")

    # v0.6.0: Create WebSocket handler for bidirectional communication (MCP delegation)
    from aii.api.websocket_handler import WebSocketHandler
    ws_handler = WebSocketHandler(websocket)
    # NOTE: Don't start listener yet - start AFTER reading initial request to avoid recv() conflict

    try:
        # Receive request
        debug_print("SERVER: Waiting for client data...")
        data = await websocket.receive_json()
        debug_print(f"SERVER: Received data: {data}")

        # NOW start background listener for MCP responses (after initial request is read)
        ws_handler.start_listening()
        debug_print("SERVER: Background listener started for MCP responses")

        # Verify API key
        api_key = data.get("api_key")
        if not api_key or not server or not server.auth.verify_key(api_key):
            await websocket.send_json({
                "type": "error",
                "message": "Invalid or missing API key"
            })
            await websocket.close()
            return

        # Check rate limit
        if not server.rate_limiter.allow(api_key):
            await websocket.send_json({
                "type": "error",
                "message": "Rate limit exceeded"
            })
            await websocket.close()
            return

        # v0.6.0 UNIFIED ENDPOINT: Support both command patterns via system_prompt parameter
        # Pattern 1 (LLM-First): system_prompt=null → Server performs intent recognition
        # Pattern 2 (Domain Ops): system_prompt="..." → Server executes with provided prompts

        from aii.core.models import RecognitionResult, RouteSource

        system_prompt = data.get("system_prompt")  # Can be None or string
        user_prompt = data.get("user_prompt")      # Always required for LLM-first

        debug_print(f"SERVER: system_prompt = {system_prompt}, user_prompt = {user_prompt}")

        # Legacy support: Handle old request formats
        # Old format 1: action="recognize" → Map to system_prompt=null
        # Old format 2: function="auto" → Map to system_prompt=null
        # Old format 3: function="translate", params={} → Direct execution (backward compat)

        function_name = data.get("function", "")
        parameters = data.get("params", {})
        action = data.get("action", "execute")

        debug_print(f"SERVER: function_name = {function_name}, action = {action}, params keys = {list(parameters.keys())}")

        # Determine execution pattern (v0.6.1 adds Pattern 3 for prompt library)
        is_llm_first = False
        is_direct_llm_call = False

        if system_prompt is not None and isinstance(system_prompt, str) and user_prompt:
            # Pattern 3: Direct LLM Call (v0.6.1 Prompt Library natural_language mode)
            # system_prompt provided → bypass intent recognition, call LLM directly
            is_direct_llm_call = True
            debug_print(f"SERVER: Direct LLM Call mode (v0.6.1) - system_prompt provided")
        elif system_prompt is None and user_prompt:
            # Pattern 1: LLM-First (new unified format)
            is_llm_first = True
            user_input = user_prompt
            debug_print(f"SERVER: LLM-First mode (unified) - user_prompt = {user_prompt}")
        elif action == "recognize":
            # Legacy: Old recognize action
            is_llm_first = True
            user_input = data.get("user_input", "")
            debug_print(f"SERVER: Legacy recognize mode - user_input = {user_input}")
        elif function_name == "auto":
            # Legacy: Old auto mode
            is_llm_first = True
            user_input = parameters.get("user_input", "")
            debug_print(f"SERVER: Legacy auto mode - user_input = {user_input}")
        else:
            # Pattern 2: Direct execution (old format or domain ops)
            is_llm_first = False
            debug_print(f"SERVER: Direct execution mode - function = {function_name}")

        # Handle Direct LLM Call pattern (v0.6.1 Prompt Library natural_language mode)
        if is_direct_llm_call:
            # Call LLM directly with system_prompt + user_prompt (no intent recognition)
            # Use universal_generate function for simplicity and consistency
            try:
                debug_print(f"SERVER: Direct LLM call - system_prompt length: {len(system_prompt)}, user_prompt: {user_prompt[:50]}...")

                # Assemble full prompt (system_prompt + user_input)
                assembled_prompt = f"{system_prompt}\n\nUser Input:\n{user_prompt}"

                # Route to universal_generate function
                function_name = "universal_generate"
                parameters = {
                    "request": assembled_prompt,
                    "format": "auto"
                }

                # Create recognition result for direct invocation
                recognition_result = RecognitionResult(
                    intent=function_name,
                    confidence=1.0,
                    parameters=parameters,
                    function_name=function_name,
                    requires_confirmation=False,
                    reasoning="Direct LLM call via system prompt (v0.6.1 Prompt Library)",
                    source=RouteSource.DIRECT_MATCH
                )

                # Continue to standard execution flow below
                debug_print(f"SERVER: Routed direct LLM call to universal_generate")

            except Exception as e:
                debug_print(f"SERVER: Direct LLM call routing error - {e}")
                if is_debug_enabled():
                    import traceback
                    traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Direct LLM call failed: {str(e)}"
                })
                await websocket.close()
                return

        # Handle LLM-First pattern (intent recognition)
        elif is_llm_first:
            if not user_input:
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing user input for LLM-first mode"
                })
                await websocket.close()
                return

            # Perform intent recognition
            try:
                debug_print("SERVER: Starting intent recognition...")
                recognition_result = await server.engine.intent_recognizer.recognize_intent(user_input)
                function_name = recognition_result.function_name
                parameters = recognition_result.parameters
                debug_print(f"SERVER: Intent recognized - {function_name}, params: {parameters}")

                # Get function plugin to check safety and generate metadata
                function_plugin = server.engine.function_registry.plugins.get(function_name)
                if not function_plugin:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Function '{function_name}' not found"
                    })
                    await websocket.close()
                    return

                # Get safety level and description
                from aii.core.models import FunctionSafety
                safety_level = function_plugin.safety_level
                requires_confirmation = safety_level in [FunctionSafety.RISKY, FunctionSafety.DESTRUCTIVE]
                description = function_plugin.description if hasattr(function_plugin, 'description') else f"Execute {function_name}"

                # For backward compatibility with old "recognize" action, send recognition response
                if action == "recognize":
                    await websocket.send_json({
                        "type": "recognition",
                        "function": function_name,
                        "parameters": parameters,
                        "safety": str(safety_level.value) if hasattr(safety_level, 'value') else str(safety_level),
                        "description": description,
                        "requires_confirmation": requires_confirmation
                    })
                    await websocket.close()
                    return

                # New unified flow: Continue to execution with complete metadata
                # Update recognition_result to include confirmation requirement
                recognition_result = RecognitionResult(
                    intent=function_name,
                    confidence=recognition_result.confidence,
                    parameters=parameters,
                    function_name=function_name,
                    requires_confirmation=requires_confirmation,
                    reasoning=recognition_result.reasoning,
                    source=recognition_result.source
                )

            except Exception as e:
                debug_print(f"SERVER: Intent recognition error - {e}")
                if is_debug_enabled():
                    import traceback
                    traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Intent recognition failed: {str(e)}"
                })
                await websocket.close()
                return
        else:
            # Pattern 2: Direct execution (domain operations or legacy format)
            # Validate function exists first
            if function_name not in server.engine.function_registry.plugins:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Function '{function_name}' not found"
                })
                return

            # Create recognition result for direct invocation
            recognition_result = RecognitionResult(
                intent=function_name,
                confidence=1.0,
                parameters=parameters,
                function_name=function_name,
                requires_confirmation=False,
                reasoning="Direct WebSocket invocation",
                source=RouteSource.DIRECT_MATCH
            )

        # At this point, both branches have set: function_name, parameters, recognition_result
        # Validate function exists (for LLM-first flow)
        if function_name not in server.engine.function_registry.plugins:
            await websocket.send_json({
                "type": "error",
                "message": f"Function '{function_name}' not found"
            })
            return

        # Check if LLM provider is required but not initialized
        if not server.initialization_status.get("llm_provider"):
            # Check if this function requires LLM
            function_plugin = server.engine.function_registry.plugins.get(function_name)
            requires_llm = hasattr(function_plugin, 'requires_llm') and function_plugin.requires_llm

            # Most functions require LLM, so assume yes unless explicitly stated
            if requires_llm or not hasattr(function_plugin, 'requires_llm'):
                llm_error = server.initialization_status.get("llm_error", "Unknown error")

                # Check if user has actually configured LLM (not just auto-created config)
                from pathlib import Path
                import yaml
                config_file = Path.home() / ".aii" / "config.yaml"
                secrets_file = Path.home() / ".aii" / "secrets.yaml"

                llm_configured = False
                if config_file.exists() and secrets_file.exists():
                    try:
                        with open(config_file) as f:
                            config_data = yaml.safe_load(f) or {}
                        # Check if provider and model are set (not null)
                        llm_provider = config_data.get("llm", {}).get("provider")
                        llm_model = config_data.get("llm", {}).get("model")
                        llm_configured = bool(llm_provider and llm_model)
                    except Exception:
                        pass

                if llm_configured:
                    # Config exists with valid LLM settings but server hasn't picked it up
                    # This happens when user runs `aii config init` while server is running
                    guidance_msg = (
                        "Configuration detected but not loaded yet.\n\n"
                        "Restart the server to apply changes:\n"
                        "  aii serve restart"
                    )
                else:
                    # No valid config - needs initial setup
                    guidance_msg = "To set up AII, run: aii config init\n(Takes ~2 minutes)"

                await websocket.send_json({
                    "type": "error",
                    "message": "Prerequisites not met: LLM provider required",
                    "details": {
                        "reason": "LLM provider not initialized",
                        "error": llm_error,
                        "guidance": guidance_msg
                    }
                })
                await websocket.close()
                return

        # Create streaming callback for real-time token delivery
        async def streaming_callback(token: str):
            """Send each token immediately to the client"""
            try:
                await websocket.send_json({
                    "type": "token",
                    "data": token  # Match the working test pattern
                })
            except Exception as e:
                # WebSocket may have disconnected
                print(f"Failed to send token via WebSocket: {e}")

        # Pass streaming callback to execution engine
        # The engine will use it for LLM streaming if available
        debug_print(f"SERVER: Starting function execution - {function_name}")
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=f"{function_name} {parameters}",
            chat_context=None,
            config=server.engine.config,
            llm_provider=server.engine.llm_provider,
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False,
            streaming_callback=streaming_callback,  # Enable real streaming
            websocket_handler=ws_handler  # v0.6.0: For MCP client-side execution
        )
        debug_print(f"SERVER: Function execution complete - Success: {result.success}")

        # Debug: Log generated content for verification
        if result.message:
            debug_print(f"SERVER: Generated result (first 200 chars): {result.message[:200]}...")
        if result.data:
            # Log specific data fields for common operations
            if isinstance(result.data, dict):
                if "commit_message" in result.data:
                    debug_print(f"SERVER: Commit message generated: {result.data['commit_message'][:200]}...")
                if "git_diff" in result.data:
                    debug_print(f"SERVER: Git diff size: {len(result.data.get('git_diff', ''))} chars")
                debug_print(f"SERVER: Data fields: {list(result.data.keys())}")

        # Send completion with full metadata (v0.5.1 fix for AII-CLI-WS-001)
        # v0.6.0: Include data field for client-side domain operations
        debug_print("SERVER: Sending completion message...")
        await websocket.send_json({
            "type": "complete",
            "success": result.success,
            "function_name": function_name,  # Add function name for debugging
            "result": result.message,  # Include the actual result text
            "data": result.data,  # v0.6.0: Include data field for git_commit and other functions
            "metadata": format_completion_metadata(result)
        })
        debug_print("SERVER: Completion message sent")

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Send error
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        # v0.6.0: Stop WebSocket handler background listener
        if ws_handler:
            await ws_handler.stop_listening()

        # Close connection
        try:
            await websocket.close()
        except:
            pass

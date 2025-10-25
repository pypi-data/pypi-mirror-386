"""
AII-specific MCP data models

These models wrap the MCP SDK types with additional AII-specific metadata
for tracking which server provides each tool/resource.
"""

# Copyright 2025-present aiiware.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class ConnectionState(Enum):
    """State of MCP server connection"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP Tool with server tracking"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str  # Which server provides this tool


@dataclass
class MCPResource:
    """MCP Resource with server tracking"""
    uri: str
    name: str
    description: Optional[str]
    mime_type: Optional[str]
    server_name: str  # Which server provides this resource


@dataclass
class MCPPrompt:
    """MCP Prompt with server tracking"""
    name: str
    description: Optional[str]
    arguments: Optional[List[Dict[str, Any]]]
    server_name: str  # Which server provides this prompt


@dataclass
class ServerConnection:
    """Connection state for an MCP server"""
    name: str
    state: ConnectionState
    session: Any = None  # ClientSession from MCP SDK
    stdio_context: Any = None  # stdio_client context manager (must keep alive)
    _session_context: Any = None  # ClientSession context manager (v0.4.10)
    error: Optional[str] = None
    tools: List[MCPTool] = None
    resources: List[MCPResource] = None
    prompts: List[MCPPrompt] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.resources is None:
            self.resources = []
        if self.prompts is None:
            self.prompts = []


@dataclass
class ToolCallResult:
    """Result from tool invocation"""
    success: bool
    content: Any
    error: Optional[str] = None
    server_name: Optional[str] = None
    is_error: bool = False

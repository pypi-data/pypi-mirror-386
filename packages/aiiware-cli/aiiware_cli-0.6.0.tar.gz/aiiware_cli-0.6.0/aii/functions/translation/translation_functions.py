"""Translation Functions - Language translation with auto-detection and multi-language support"""

import re
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class TranslationFunction(FunctionPlugin):
    """Translate text between languages with auto-detection"""

    @property
    def name(self) -> str:
        return "translate"

    @property
    def description(self) -> str:
        return "Translate text between languages with automatic language detection"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.TRANSLATION

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "text": ParameterSchema(
                name="text",
                type="string",
                required=True,
                description="Text to translate",
            ),
            "target_language": ParameterSchema(
                name="target_language",
                type="string",
                required=False,
                default="auto-detect",
                description="Target language (e.g., 'spanish', 'french', 'german')",
            ),
            "source_language": ParameterSchema(
                name="source_language",
                type="string",
                required=False,
                default="auto-detect",
                description="Source language (auto-detected if not specified)",
            ),
            "preserve_formatting": ParameterSchema(
                name="preserve_formatting",
                type="boolean",
                required=False,
                default=True,
                description="Preserve original formatting and structure",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Translation should show clean output by default (just the translation)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Translation supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available for translation"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for translation"]
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute translation"""
        try:
            text = parameters.get("text", "").strip()
            if not text:
                return ExecutionResult(
                    success=False, message="No text provided for translation"
                )

            target_language = parameters.get("target_language", "auto-detect")
            source_language = parameters.get("source_language", "auto-detect")
            preserve_formatting = parameters.get("preserve_formatting", True)

            # Auto-detect target language if needed
            if target_language == "auto-detect":
                target_language = await self._detect_target_language(
                    text, context.llm_provider
                )

            # Perform translation
            translation_result = await self._translate_text(
                text=text,
                target_language=target_language,
                source_language=source_language,
                preserve_formatting=preserve_formatting,
                llm_provider=context.llm_provider,
            )

            # Create thinking mode output
            source_lang = self._detect_source_language(text)
            reasoning = translation_result.get(
                "reasoning",
                f"Translating '{text}' from {source_lang} to {target_language}. Ensuring accurate meaning and appropriate tone.",
            )

            return ExecutionResult(
                success=True,
                message=translation_result["translation"],  # For clean mode
                data={
                    "clean_output": translation_result["translation"],  # Clean mode: just the translation
                    "original_text": text,
                    "translated_text": translation_result["translation"],
                    "source_language": translation_result.get(
                        "detected_source", source_lang
                    ),
                    "target_language": target_language,
                    "confidence": translation_result.get("confidence", 85.0),
                    "reasoning": reasoning,
                    "input_tokens": translation_result.get("input_tokens"),
                    "output_tokens": translation_result.get("output_tokens"),
                    "thinking_mode": True,
                    "provider": (
                        context.llm_provider.model_info
                        if context.llm_provider
                        else "LLM"
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Translation failed: {str(e)}"
            )

    async def _detect_target_language(self, text: str, llm_provider: Any) -> str:
        """Detect appropriate target language based on context"""
        prompt = f"""Determine the most appropriate target language for translating this text:

Text: "{text[:200]}{"..." if len(text) > 200 else ""}"

Consider:
1. If the text is in English, suggest a commonly requested language
2. If the text is in another language, suggest English
3. Consider the content context

Respond with just the language name in lowercase (e.g., "english", "spanish", "french", "german", "chinese", "japanese")."""

        try:
            response = await llm_provider.complete(prompt)
            target_lang = response.strip().lower()

            # Validate and normalize language names
            language_map = {
                "english": "english",
                "spanish": "spanish",
                "french": "french",
                "german": "german",
                "italian": "italian",
                "portuguese": "portuguese",
                "chinese": "chinese",
                "japanese": "japanese",
                "korean": "korean",
                "russian": "russian",
                "arabic": "arabic",
            }

            return language_map.get(target_lang, "english")

        except Exception:
            # Fallback: if text seems non-English, target English; otherwise Spanish
            if self._is_likely_english(text):
                return "spanish"
            else:
                return "english"

    def _detect_source_language(self, text: str) -> str:
        """Simple source language detection based on character patterns"""
        # This is a simplified detection - in production you'd use proper language detection
        if re.search(r"[äöüß]", text.lower()):
            return "german"
        elif re.search(r"[àâäéèêëïîôùûüÿç]", text.lower()):
            return "french"
        elif re.search(r"[áéíñóúü¿¡]", text.lower()):
            return "spanish"
        elif re.search(r"[àáâãäåçèéêëìíîïðñòóôõöøùúûüýþ]", text.lower()):
            return "portuguese"
        elif re.search(r"[一-龯]", text):
            return "chinese"
        elif re.search(r"[ひらがなカタカナ]", text):
            return "japanese"
        elif re.search(r"[가-힣]", text):
            return "korean"
        elif re.search(r"[а-яё]", text.lower()):
            return "russian"
        elif re.search(r"[ا-ي]", text):
            return "arabic"
        else:
            return "english"  # Default assumption

    def _is_likely_english(self, text: str) -> bool:
        """Simple check if text is likely English"""
        # Check for common English words and patterns
        english_indicators = [
            r"\\bthe\\b",
            r"\\band\\b",
            r"\\bof\\b",
            r"\\bto\\b",
            r"\\ba\\b",
            r"\\bin\\b",
            r"\\bis\\b",
            r"\\bit\\b",
            r"\\byou\\b",
            r"\\bthat\\b",
        ]

        english_count = sum(
            1 for pattern in english_indicators if re.search(pattern, text.lower())
        )
        return english_count >= 2

    async def _translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str,
        preserve_formatting: bool,
        llm_provider: Any,
    ) -> dict[str, Any]:
        """Perform the actual translation using LLM"""
        # Build translation prompt
        formatting_instruction = (
            "Preserve all formatting, line breaks, and structure exactly."
            if preserve_formatting
            else ""
        )
        source_hint = (
            f" (source language: {source_language})"
            if source_language != "auto-detect"
            else ""
        )

        # Enhanced prompt with reasoning request
        prompt = f"""Translate the following text to {target_language}{source_hint}.

Text to translate: "{text}"

Please provide:
1. The translation
2. Brief reasoning about your translation choices (in one sentence)
3. Confidence level (percentage)

Format your response as:
TRANSLATION: [your translation here]
REASONING: [brief explanation of translation approach]
CONFIDENCE: [percentage]

Rules:
- Maintain the original meaning and tone
- Use natural, fluent language in the target language
- {formatting_instruction}
- If the text is already in the target language, return it unchanged"""

        try:
            # NOTE: Don't use streaming for translate function
            # Translation needs to parse the raw response before displaying
            # Streaming would show "TRANSLATION: ..." raw format to users

            # Use complete_with_usage for accurate token tracking
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=None  # Disable streaming for translation
                )
                response = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                response = await llm_provider.complete(prompt)
                # Fallback to estimates if usage tracking unavailable
                usage = {
                    "input_tokens": len(prompt.split()) + len(text.split()),
                    "output_tokens": len(response.split()) if response else 0
                }

            # Parse the structured response
            translation, reasoning, confidence = self._parse_translation_response(
                response, text, target_language
            )

            # Detect actual source language from the translation context
            detected_source = self._detect_source_language(text)

            return {
                "translation": translation,
                "detected_source": detected_source,
                "confidence": confidence,
                "reasoning": reasoning,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }

        except Exception as e:
            raise RuntimeError(f"Translation API call failed: {str(e)}") from e

    def _parse_translation_response(
        self, response: str, original_text: str, target_language: str
    ) -> tuple[str, str, float]:
        """Parse the structured LLM response into translation, reasoning, and confidence"""
        try:
            lines = response.strip().split("\n")
            translation = ""
            reasoning = ""
            confidence = 85.0

            for line in lines:
                line = line.strip()
                if line.startswith("TRANSLATION:"):
                    translation = line[12:].strip()
                elif line.startswith("REASONING:"):
                    reasoning = line[10:].strip()
                elif line.startswith("CONFIDENCE:"):
                    conf_text = line[11:].strip().rstrip("%")
                    try:
                        confidence = float(conf_text)
                    except ValueError:
                        confidence = 85.0

            # Fallback if structured parsing fails
            if not translation:
                # Try to extract just the translated text
                translation = response.strip()
                # Remove common prefixes
                prefixes = ["Translation:", "TRANSLATION:", "Result:", "Output:"]
                for prefix in prefixes:
                    if translation.startswith(prefix):
                        translation = translation[len(prefix) :].strip()
                        break

                # Generate default reasoning if not provided
                reasoning = f"Simple translation of '{original_text}' to {target_language}, preserving meaning and tone."

            return translation, reasoning, confidence

        except Exception:
            # Complete fallback
            return (
                response.strip(),
                f"Translation from source language to {target_language}.",
                80.0,
            )

    async def _get_language_examples(self, language: str) -> str:
        """Get example phrases in the specified language for context"""
        examples = {
            "spanish": "Hola, ¿cómo estás? Me gusta la música.",
            "french": "Bonjour, comment allez-vous? J'aime la musique.",
            "german": "Hallo, wie geht es Ihnen? Ich mag Musik.",
            "italian": "Ciao, come stai? Mi piace la musica.",
            "portuguese": "Olá, como está? Eu gosto de música.",
            "chinese": "你好，你好吗？我喜欢音乐。",
            "japanese": "こんにちは、元気ですか？音楽が好きです。",
            "korean": "안녕하세요, 어떻게 지내세요? 음악을 좋아해요.",
            "russian": "Привет, как дела? Мне нравится музыка.",
            "arabic": "مرحبا، كيف حالك؟ أحب الموسيقى.",
        }
        return examples.get(language.lower(), "")


class LanguageDetectionFunction(FunctionPlugin):
    """Identify and detect what language text is written in"""

    @property
    def name(self) -> str:
        return "detect_language"

    @property
    def description(self) -> str:
        return """Identify and detect what language a given text is written in.

IMPORTANT: This function ONLY identifies the language name (e.g., 'french', 'spanish', 'japanese').
It does NOT translate the text. For translation, use the 'translate' function instead.

Use this function when the user asks:
- "what language is this"
- "detect the language of [text]"
- "identify language: [text]"
- "which language is this written in"
- "is this written in [language]?"

Do NOT use this if the user wants translation (e.g., "translate to spanish") - use 'translate' function for that.

Returns: Just the language name in lowercase (e.g., "french", "spanish", "chinese")"""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.TRANSLATION

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "text": ParameterSchema(
                name="text",
                type="string",
                required=True,
                description="Text to analyze for language detection",
            )
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Language detection should show clean output by default (just the language name)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Language detection supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for language detection"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Detect language of text"""
        try:
            text = parameters.get("text", "").strip()
            if not text:
                return ExecutionResult(
                    success=False, message="No text provided for language detection"
                )

            # Use LLM for accurate language detection
            prompt = f"""Detect the language of this text and provide confidence score:

Text: "{text}"

Respond in JSON format:
{{
  "language": "language_name",
  "confidence": 0.95,
  "reasoning": "brief explanation"
}}

Common languages: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Russian, Arabic"""

            # Use complete_with_usage for accurate token tracking
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                response = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                response = await context.llm_provider.complete(prompt)
                # Fallback to estimates if usage tracking unavailable
                usage = {
                    "input_tokens": len(prompt.split()) + len(text.split()),
                    "output_tokens": len(response.split()) if response else 0
                }

            # Parse JSON response
            import json

            try:
                result = json.loads(response.strip())
                language = result.get("language", "unknown")
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")
            except json.JSONDecodeError:
                # Fallback to simple detection
                language = self._simple_language_detection(text)
                confidence = 0.7
                reasoning = "Pattern-based detection"

            # Create reasoning for THINKING/VERBOSE modes
            if reasoning:
                # Use LLM-provided reasoning
                thinking_reasoning = f"Detected {language} based on {reasoning.lower()}"
            else:
                thinking_reasoning = f"Detected {language} with {confidence:.0%} confidence based on linguistic patterns and character analysis"

            return ExecutionResult(
                success=True,
                message=f"Detected language: {language} (confidence: {confidence:.0%})",
                data={
                    "clean_output": language,  # For CLEAN mode - just the language name
                    "language": language,
                    "confidence": confidence,
                    "reasoning": thinking_reasoning,  # For THINKING/VERBOSE modes
                    "text_sample": text[:100] + "..." if len(text) > 100 else text,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Language detection failed: {str(e)}"
            )

    def _simple_language_detection(self, text: str) -> str:
        """Fallback simple language detection"""
        text_lower = text.lower()

        # Character-based detection
        if re.search(r"[一-龯]", text):
            return "Chinese"
        elif re.search(r"[ひらがなカタカナ]", text):
            return "Japanese"
        elif re.search(r"[가-힣]", text):
            return "Korean"
        elif re.search(r"[а-яё]", text):
            return "Russian"
        elif re.search(r"[ا-ي]", text):
            return "Arabic"

        # European language patterns
        if re.search(r"[äöüß]", text_lower):
            return "German"
        elif re.search(r"[àâäéèêëïîôùûüÿç]", text_lower):
            return "French"
        elif re.search(r"[áéíñóúü¿¡]", text_lower):
            return "Spanish"

        return "English"  # Default fallback

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming translation

        Args:
            parameters: Function parameters containing text and language info

        Returns:
            str: Formatted prompt for LLM
        """
        text = parameters.get("text", "").strip()
        target_language = parameters.get("target_language", "english")
        source_language = parameters.get("source_language", "auto")
        preserve_formatting = parameters.get("preserve_formatting", True)

        # Build translation prompt
        if source_language == "auto" or source_language == "auto-detect":
            source_info = "from the detected language"
        else:
            source_info = f"from {source_language}"

        formatting_instruction = (
            "Preserve all formatting, structure, and style from the original text."
            if preserve_formatting
            else "Provide a natural translation without preserving specific formatting."
        )

        prompt = f"""Translate the following text {source_info} to {target_language}.

{formatting_instruction}

Text to translate:
{text}

Provide only the translation, no explanations or additional text."""

        return prompt

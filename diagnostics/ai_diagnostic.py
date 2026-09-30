"""AI-Powered Diagnostic Engine and Interface.

Phase 6B & Phase 6D-B: Provider-Independent AI Diagnostic Architecture.
Provides prompt construction, an abstract AIProvider interface, a deterministic
MockAIProvider for offline testing and diagnostics, the GroqAIProvider for production
Groq API integration, and structured DiagnosticResponse representations.
"""

import os
import sys
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure workspace root is in sys.path when running directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from diagnostics.error_handler import Diagnostic, DiagnosticErrorHandler


# ==============================================================================
# Exceptions
# ==============================================================================

class GroqDiagnosticError(Exception):
    """Base exception for Groq diagnostic provider errors."""
    pass


class GroqConfigurationError(GroqDiagnosticError):
    """Raised when Groq API key or required configuration is missing or invalid."""
    pass


class GroqAPIError(GroqDiagnosticError):
    """Raised when an error occurs during API communication with Groq."""
    pass


class GroqResponseParseError(GroqDiagnosticError):
    """Raised when the Groq response cannot be parsed into structured diagnostic fields."""
    pass


# ==============================================================================
# Part 1: Diagnostic Response
# ==============================================================================

@dataclass
class DiagnosticResponse:
    """Structured response containing explanatory analysis and remediation suggestions."""
    explanation: str
    cause: str
    suggestion: str
    corrected_code: str

    def format_response(self) -> str:
        """Format the response into human-readable sections."""
        lines = [
            "Explanation:",
            self.explanation.strip(),
            "",
            "Cause:",
            self.cause.strip(),
            "",
            "Suggested Fix:",
            self.suggestion.strip(),
            "",
            "Corrected Code:",
            self.corrected_code.strip(),
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_response()


# ==============================================================================
# Part 2: AI Provider Interface
# ==============================================================================

class AIProvider(ABC):
    """Abstract base class for all AI diagnostic providers."""

    @abstractmethod
    def diagnose(self, prompt: str) -> DiagnosticResponse:
        """Analyze a diagnostic prompt and return a structured DiagnosticResponse.
        
        Subclasses must implement this method without modifying compiler behavior.
        """
        pass


# ==============================================================================
# Part 3: Prompt Builder
# ==============================================================================

class PromptBuilder:
    """Builds deterministic, context-rich prompts from structured Diagnostic instances."""

    COMPILER_NAME = "AI-Powered Python-Like (.pyl) Compiler"
    LANGUAGE_NAME = ".pyl (Pedagogical Python-Like Language)"

    LANGUAGE_SPECIFICATION = (
        "Language Specification & Constraints:\n"
        "The .pyl language is intentionally minimal and strictly typed:\n"
        "- Supported Types: int, float, str, bool (no other types exist).\n"
        "- Statements: variable assignments, if/elif/else conditionals, while loops.\n"
        "- Scoping: lexical block scopes (indentation-based).\n"
        "- Operators: arithmetic (+, -, *, /), relational (<, >, ==, !=), logical (and, or, not).\n"
        "- Strict Rules: No truthiness coercion (conditions must be bool). Variables must be defined before use.\n"
        "- NOT Supported: functions, classes, imports, lists, dicts, tuples, decorators, try/except.\n"
        "CRITICAL INSTRUCTION: Do not invent language features or compiler rules. Suggest fixes strictly within .pyl."
    )

    def build_prompt(self, diagnostic: Diagnostic) -> str:
        """Generate a complete diagnostic prompt for an LLM/AI provider."""
        sections = [
            f"You are an expert compiler assistant for the {self.COMPILER_NAME}.",
            f"Target Language: {self.LANGUAGE_NAME}",
            "",
            self.LANGUAGE_SPECIFICATION,
            "",
            "============================================================",
            "COMPILER ERROR REPORT",
            "============================================================",
            f"Phase: {diagnostic.phase.upper()}",
            f"Error Category: {diagnostic.error_type}",
            f"Message: {diagnostic.message}",
            f"File: {diagnostic.filename or '<anonymous>'}",
            f"Line: {diagnostic.line if diagnostic.line is not None else 'Unknown'}",
            f"Column: {diagnostic.column if diagnostic.column is not None else 'Unknown'}",
        ]

        if diagnostic.source_line:
            sections.append(f"Source Line: {diagnostic.source_line}")

        if diagnostic.context:
            sections.append("")
            sections.append("Source Code Context:")
            sections.append(diagnostic.context)
        elif diagnostic.pointer:
            sections.append("")
            sections.append(f"Pointer: {diagnostic.pointer}")

        sections.extend([
            "",
            "============================================================",
            "INSTRUCTIONS FOR DIAGNOSTIC RESPONSE",
            "============================================================",
            "Provide a response containing exactly four parts:",
            "1. Explanation: A clear, beginner-friendly explanation of what the error means.",
            "2. Cause: Why the compiler rejected this code based on .pyl rules.",
            "3. Suggested Fix: Concrete guidance on how to fix the error.",
            "4. Corrected Code: Valid .pyl code fixing the error adhering strictly to .pyl syntax.",
        ])

        return "\n".join(sections)

    def build(self, diagnostic: Diagnostic) -> str:
        """Alias for build_prompt()."""
        return self.build_prompt(diagnostic)


# ==============================================================================
# Part 4: Mock AI Provider
# ==============================================================================

class MockAIProvider(AIProvider):
    """Deterministic, offline diagnostic provider for testing and fallback."""

    def diagnose(self, prompt: str) -> DiagnosticResponse:
        """Inspect prompt for error patterns and return deterministic explanations."""
        lower_prompt = prompt.lower()

        # 1. Undefined variable
        if "undefined variable" in lower_prompt or "undefined symbol" in lower_prompt:
            return DiagnosticResponse(
                explanation="A variable was referenced before it was defined in the current or any enclosing scope.",
                cause="The compiler's static analysis requires variables to be declared via an initial assignment before they can be read in expressions.",
                suggestion="Assign an initial value to the variable before referencing it.",
                corrected_code="x = 10\ny = x + 20",
            )

        # 2. Type mismatch / operator compatibility
        if "cannot be applied to operands of type" in lower_prompt or "cannot compare incompatible" in lower_prompt or "type mismatch" in lower_prompt:
            return DiagnosticResponse(
                explanation="An operator was applied to operands with incompatible types (int + str). The .pyl language does not allow mixing integers and strings in arithmetic or concatenation operations.",
                cause="The .pyl language enforces strict static typing and only allows compatible operand combinations. String concatenation with '+' requires both operands to be of type 'str', but an 'int' and a 'str' were provided.",
                suggestion="Ensure both operands have compatible string types. Changing 'x' to a string makes the expression valid.",
                corrected_code='x = "10"\nmessage = x + "items"',
            )

        # 3. Invalid boolean operation
        if "boolean operator" in lower_prompt or "requires operands of type 'bool'" in lower_prompt:
            return DiagnosticResponse(
                explanation="A boolean operator ('and' or 'or') was applied to non-boolean operands.",
                cause="In .pyl, logical operators ('and', 'or', 'not') strictly require 'bool' operands; general truthiness is not supported.",
                suggestion="Use boolean values or relational expressions (such as <, >, ==) as operands for logical operations.",
                corrected_code="a = True\nb = False\nc = a and b",
            )

        # 4. Invalid condition (if/elif/while)
        if "condition must" in lower_prompt or "if condition" in lower_prompt or "while condition" in lower_prompt:
            return DiagnosticResponse(
                explanation="A control flow condition does not evaluate to a boolean.",
                cause="In .pyl, 'if', 'elif', and 'while' loop conditions must strictly evaluate to type 'bool'. Truthiness coercion is not supported.",
                suggestion="Use a comparison or relational expression that produces a boolean result.",
                corrected_code="x = 10\nif x > 0:\n    y = 20",
            )

        # 5. Generic syntax / parser error
        if "syntax error" in lower_prompt or "phase: parser" in lower_prompt or "unexpected token" in lower_prompt:
            return DiagnosticResponse(
                explanation="A syntax error occurred because the token sequence does not conform to the language grammar.",
                cause="The parser encountered an unexpected token or malformed statement structure.",
                suggestion="Check statement syntax, punctuation (such as colons after if/while), and indentation.",
                corrected_code="if x > 5:\n    y = 10",
            )

        # 6. Generic lexer error
        if "lexical error" in lower_prompt or "phase: lexer" in lower_prompt or "unexpected character" in lower_prompt:
            return DiagnosticResponse(
                explanation="A lexical error occurred while scanning source characters.",
                cause="The source code contains an illegal character or unrecognized token pattern.",
                suggestion="Remove or replace the invalid character with supported language tokens.",
                corrected_code="x = 10 + 20",
            )

        # Generic Fallback
        return DiagnosticResponse(
            explanation="The compiler encountered an error during compilation.",
            cause="A rule violation was detected during the compilation phase.",
            suggestion="Review the source code at the indicated line and column and adjust to conform with .pyl language rules.",
            corrected_code="x = 10",
        )


# ==============================================================================
# Part 5: Groq Response Parser Helper
# ==============================================================================

def _parse_groq_response(text: str) -> DiagnosticResponse:
    """Robustly parse four sections: Explanation, Cause, Suggested Fix, Corrected Code."""
    patterns = [
        ("explanation", r"(?:^|\n)(?:\*\*|#+\s*)?Explanation(?:\*\*|:|\s*:)+\s*(.*?)(?=\n(?:\*\*|#+\s*)?(?:Cause|Why)|$)"),
        ("cause", r"(?:^|\n)(?:\*\*|#+\s*)?(?:Cause|Why)(?:\*\*|:|\s*:)+\s*(.*?)(?=\n(?:\*\*|#+\s*)?(?:Suggested Fix|Suggestion|Fix)|$)"),
        ("suggestion", r"(?:^|\n)(?:\*\*|#+\s*)?(?:Suggested Fix|Suggestion|Fix)(?:\*\*|:|\s*:)+\s*(.*?)(?=\n(?:\*\*|#+\s*)?(?:Corrected Code|Correction|Code)|$)"),
        ("corrected_code", r"(?:^|\n)(?:\*\*|#+\s*)?(?:Corrected Code|Correction|Code)(?:\*\*|:|\s*:)+\s*(.*)"),
    ]

    extracted = {}
    for key, pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if key == "corrected_code":
                # Strip markdown code blocks if wrapped
                val = re.sub(r"^```[a-zA-Z]*\n?", "", val)
                val = re.sub(r"\n?```$", "", val).strip()
            extracted[key] = val
        else:
            extracted[key] = None

    missing = [k for k, v in extracted.items() if not v]
    if missing:
        raise GroqResponseParseError(
            f"Failed to parse structured diagnostic from Groq response: missing {missing}."
        )

    return DiagnosticResponse(
        explanation=extracted["explanation"],
        cause=extracted["cause"],
        suggestion=extracted["suggestion"],
        corrected_code=extracted["corrected_code"],
    )


# ==============================================================================
# Part 6: Groq AI Provider
# ==============================================================================

_DEFAULT_KEY = object()


class GroqAIProvider(AIProvider):
    """Real AI diagnostic provider using the official Groq client SDK."""

    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Any = _DEFAULT_KEY,
    ) -> None:
        self.model = model or self.DEFAULT_MODEL

        # 1. No api_key argument supplied -> use GROQ_API_KEY environment variable
        if api_key is _DEFAULT_KEY:
            resolved_key = os.environ.get("GROQ_API_KEY")
            if not resolved_key:
                raise GroqConfigurationError(
                    "GROQ_API_KEY environment variable is not set."
                )
        # 2. api_key explicitly supplied
        else:
            if not api_key:
                # Explicit empty string or None -> do NOT fall back to environment
                raise GroqConfigurationError(
                    "Explicitly provided api_key cannot be empty."
                )
            resolved_key = str(api_key)

        self._api_key = resolved_key
        try:
            from groq import Groq
            self._client = Groq(api_key=resolved_key)
        except Exception as e:
            raise GroqConfigurationError(f"Failed to initialize Groq client: {e}")

    def diagnose(self, prompt: str) -> DiagnosticResponse:
        """Send prompt to Groq API and parse response into DiagnosticResponse."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert compiler diagnostic assistant for the .pyl programming language. "
                    "You must diagnose the compilation error and respond strictly in the following format:\n\n"
                    "Explanation:\n<brief explanation>\n\n"
                    "Cause:\n<compiler cause based on .pyl rules>\n\n"
                    "Suggested Fix:\n<clear guidance>\n\n"
                    "Corrected Code:\n<valid .pyl code fixing the error>"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            chat_completion = self._client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2,
            )
        except Exception as e:
            err_msg = str(e).replace(self._api_key, "[REDACTED]")
            raise GroqAPIError(f"Groq API request failed: {err_msg}")

        if not chat_completion.choices:
            raise GroqAPIError("Groq API returned an empty choices list.")

        content = chat_completion.choices[0].message.content
        if not content or not content.strip():
            raise GroqAPIError("Groq API returned empty message content.")

        return _parse_groq_response(content)


# ==============================================================================
# Part 7: Convenience Function
# ==============================================================================

def diagnose_with_provider(diagnostic: Diagnostic, provider: AIProvider) -> DiagnosticResponse:
    """Convert a Diagnostic into an AI prompt, submit to provider, and return response."""
    builder = PromptBuilder()
    prompt = builder.build_prompt(diagnostic)
    return provider.diagnose(prompt)


# ==============================================================================
# Part 8: Self-Tests
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 6D-B: GROQ AI PROVIDER TEST SUITE")
    print("=" * 60)

    print("\n" + "=" * 40)
    print("DETERMINISTIC TESTS")
    print("=" * 40)

    handler = DiagnosticErrorHandler(default_filename="test_sample.pyl")
    builder = PromptBuilder()
    mock_provider = MockAIProvider()

    # --------------------------------------------------------------------------
    # TEST 1: DiagnosticResponse formatting
    # --------------------------------------------------------------------------
    print("\n--- TEST 1: DiagnosticResponse formatting ---")
    resp = DiagnosticResponse(
        explanation="The variable 'x' is used before it is defined.",
        cause="The semantic analyzer requires variables to be defined before use.",
        suggestion="Define x before using it.",
        corrected_code="x = 10\ny = x + 20",
    )
    formatted_resp = resp.format_response()
    assert "Explanation:" in formatted_resp
    assert "Cause:" in formatted_resp
    assert "Suggested Fix:" in formatted_resp
    assert "Corrected Code:" in formatted_resp
    assert "x = 10" in formatted_resp
    print("[PASS] Test 1: DiagnosticResponse formats properly into clean sections.")

    # --------------------------------------------------------------------------
    # TEST 2: AIProvider base interface
    # --------------------------------------------------------------------------
    print("\n--- TEST 2: AIProvider base interface ---")
    try:
        AIProvider()  # type: ignore
        raise AssertionError("Expected TypeError when instantiating abstract AIProvider")
    except TypeError:
        print("[PASS] Test 2: AIProvider correctly enforces abstract interface.")

    # --------------------------------------------------------------------------
    # TEST 3: PromptBuilder
    # --------------------------------------------------------------------------
    print("\n--- TEST 3: PromptBuilder ---")
    diag_sample = handler.create_diagnostic(
        phase="semantic",
        message="Undefined variable 'x'",
        filename="prog.pyl",
        line=2,
        column=5,
        source="y = 10\nz = x + 2\n",
    )
    built_prompt = builder.build_prompt(diag_sample)
    assert "AI-Powered Python-Like (.pyl) Compiler" in built_prompt
    assert "Do not invent language features or compiler rules" in built_prompt
    assert "Undefined variable 'x'" in built_prompt
    assert "Line: 2" in built_prompt
    print("[PASS] Test 3: PromptBuilder generated complete prompt with constraints.")

    # --------------------------------------------------------------------------
    # TEST 4: MockAIProvider
    # --------------------------------------------------------------------------
    print("\n--- TEST 4: MockAIProvider ---")
    diag_type = handler.create_diagnostic(
        phase="semantic",
        message="Operator '+' cannot be applied to operands of type 'int' and 'str'",
        filename="types.pyl",
        line=3,
        column=7,
        source='x = 10\ny = "hello"\nz = x + y\n',
    )
    prompt_type = builder.build_prompt(diag_type)
    resp_type = mock_provider.diagnose(prompt_type)
    assert "incompatible types" in resp_type.explanation
    assert "compatible operand combinations" in resp_type.cause
    assert 'x = "10"' in resp_type.corrected_code
    print("[PASS] Test 4: MockAIProvider returned targeted responses for compiler errors.")

    # --------------------------------------------------------------------------
    # TEST 5: Groq provider configuration without API call
    # --------------------------------------------------------------------------
    print("\n--- TEST 5: Groq provider configuration without API call ---")
    # Verify explicitly empty API key raises GroqConfigurationError without falling back
    try:
        GroqAIProvider(api_key="")
        raise AssertionError("Expected GroqConfigurationError when api_key is empty string")
    except GroqConfigurationError:
        pass

    try:
        GroqAIProvider(api_key=None)
        raise AssertionError("Expected GroqConfigurationError when api_key is None")
    except GroqConfigurationError:
        pass

    # Verify custom model and offline initialization with explicit test key
    offline_provider = GroqAIProvider(api_key="gsk_offline_test_key", model="openai/gpt-oss-120b")
    assert offline_provider.model == "openai/gpt-oss-120b"
    assert offline_provider._client is not None

    # Verify GroqAIProvider() uses environment variable when present (never printing key)
    if os.environ.get("GROQ_API_KEY"):
        env_provider = GroqAIProvider()
        assert env_provider.model == GroqAIProvider.DEFAULT_MODEL
        assert env_provider._client is not None

    # Verify response parser on valid content
    test_raw_response = (
        "Explanation:\nType mismatch between int and str.\n\n"
        "Cause:\n.pyl enforces static typing.\n\n"
        "Suggested Fix:\nUse string operand.\n\n"
        "Corrected Code:\nx = '10'\nmessage = x + 'items'\n"
    )
    parsed_resp = _parse_groq_response(test_raw_response)
    assert parsed_resp.explanation == "Type mismatch between int and str."
    assert "x = '10'" in parsed_resp.corrected_code

    # Verify parser raises error on malformed content
    try:
        _parse_groq_response("Invalid unstructured output without sections")
        raise AssertionError("Expected GroqResponseParseError")
    except GroqResponseParseError:
        pass
    print("[PASS] Test 5: GroqAIProvider configuration, error handling, and parser verified offline.")

    # --------------------------------------------------------------------------
    # TEST 6: Provider helper compatibility
    # --------------------------------------------------------------------------
    print("\n--- TEST 6: Provider helper compatibility ---")
    sample_diag_helper = handler.create_diagnostic(
        phase="semantic",
        message="Undefined variable 'val'",
        filename="test.pyl",
        line=1,
        column=5,
        source="x = val + 1\n",
    )
    helper_resp = diagnose_with_provider(sample_diag_helper, mock_provider)
    assert isinstance(helper_resp, DiagnosticResponse)
    assert hasattr(GroqAIProvider, "diagnose")
    print("[PASS] Test 6: diagnose_with_provider() works seamlessly with AIProvider implementations.")

    # --------------------------------------------------------------------------
    # LIVE GROQ API TEST
    # --------------------------------------------------------------------------
    print("\n" + "=" * 40)
    print("LIVE GROQ API TEST")
    print("=" * 40)
    print("\n--- TEST 7: Live Groq API integration ---")

    live_status = "WARN"
    api_key_env = os.environ.get("GROQ_API_KEY")

    if not api_key_env:
        print("[WARN] Live Groq test could not complete: GROQ_API_KEY environment variable is not set.")
        live_status = "WARN"
    else:
        try:
            live_diag = handler.create_diagnostic(
                phase="semantic",
                message="Operator '+' cannot be applied to operands of type 'int' and 'str'",
                filename="shopping.pyl",
                line=2,
                column=7,
                source='x = 10\nmessage = x + "items"\n',
            )
            # Use GroqAIProvider() so it automatically obtains key from GROQ_API_KEY
            groq_provider = GroqAIProvider()
            live_resp = diagnose_with_provider(live_diag, groq_provider)

            assert isinstance(live_resp, DiagnosticResponse), "Expected DiagnosticResponse from Groq"
            assert len(live_resp.explanation) > 0, "Empty explanation"
            assert len(live_resp.cause) > 0, "Empty cause"
            assert len(live_resp.suggestion) > 0, "Empty suggestion"
            assert len(live_resp.corrected_code) > 0, "Empty corrected code"

            print("[PASS] Live Groq API integration succeeded.")
            print("\nLive Groq Diagnostic Response:")
            print("-" * 40)
            print(live_resp.format_response())
            print("-" * 40)
            live_status = "PASS"
        except Exception as e:
            print(f"[WARN] Live Groq test could not complete: {e}")
            live_status = "WARN"

    print("\n" + "=" * 60)
    print("PHASE 6D-B TESTS COMPLETE")
    print("=" * 60)
    print("Deterministic tests: PASS")
    print(f"Live Groq test: {live_status}")

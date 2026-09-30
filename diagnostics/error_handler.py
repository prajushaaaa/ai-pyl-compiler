"""Deterministic Diagnostic and Error Handling Architecture.

Phase 6A: Diagnostic Architecture & Context Specification.
Provides structured diagnostic representation and error collection across compiler phases:
- Lexer (lexical errors)
- Parser (syntax/grammar errors)
- Semantic (scoping & type errors)
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Ensure workspace root is in sys.path when running directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from diagnostics.context_extractor import (
    SourceContext,
    ContextExtractor,
    extract_source_context,
)


# ==============================================================================
# Phase to Error Type Mapping
# ==============================================================================

PHASE_ERROR_TYPE_MAP: Dict[str, str] = {
    "lexer": "Lexical Error",
    "parser": "Syntax Error",
    "semantic": "Semantic Error",
}


# ==============================================================================
# Diagnostic Data Class
# ==============================================================================

@dataclass
class Diagnostic:
    """Encapsulates a compiler error with full source location and contextual information."""
    phase: str
    error_type: str
    message: str
    filename: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    source_line: Optional[str] = None
    context: Optional[str] = None
    pointer: Optional[str] = None

    def __str__(self) -> str:
        handler = DiagnosticErrorHandler()
        return handler.format_diagnostic(self)


# ==============================================================================
# Diagnostic Error Handler
# ==============================================================================

class DiagnosticErrorHandler:
    """Collects, structures, and formats compiler errors into diagnostics."""

    def __init__(self, default_filename: str = "<anonymous>") -> None:
        self.diagnostics: List[Diagnostic] = []
        self.default_filename = default_filename

    def create_diagnostic(
        self,
        phase: str,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        filename: Optional[str] = None,
        source: Optional[str] = None,
        error_type: Optional[str] = None,
        exception: Optional[Exception] = None,
    ) -> Diagnostic:
        """Create a structured Diagnostic instance from error details or an exception.
        
        Args:
            phase: Compiler phase ('lexer', 'parser', or 'semantic').
            message: Descriptive error message.
            line: 1-indexed error line number.
            column: 1-indexed error column number.
            filename: Name of the source file.
            source: Complete source code string for context extraction.
            error_type: Human-readable error category. Defaults to phase mapping.
            exception: Optional source exception for fallback coordinate extraction.
        """
        # Coordinate fallback from exception if not explicitly supplied
        resolved_line = line
        resolved_column = column
        if exception is not None:
            if resolved_line is None:
                resolved_line = getattr(exception, "line", None) or getattr(exception, "lineno", None)
            if resolved_column is None:
                resolved_column = getattr(exception, "column", None) or getattr(exception, "col", None)

        # Determine error category label
        if error_type is None:
            resolved_type = PHASE_ERROR_TYPE_MAP.get(phase.lower(), f"{phase.capitalize()} Error")
        else:
            resolved_type = error_type

        resolved_filename = filename if filename is not None else self.default_filename

        # Extract source context if source and line are available
        source_line: Optional[str] = None
        context_str: Optional[str] = None
        pointer_str: Optional[str] = None

        if source is not None and resolved_line is not None:
            src_ctx = extract_source_context(
                source=source,
                line=resolved_line,
                column=resolved_column,
                surrounding_lines=2,
            )
            source_line = src_ctx.source_line
            context_str = src_ctx.formatted_context
            pointer_str = src_ctx.pointer_line

        diagnostic = Diagnostic(
            phase=phase.lower(),
            error_type=resolved_type,
            message=message,
            filename=resolved_filename,
            line=resolved_line,
            column=resolved_column,
            source_line=source_line,
            context=context_str,
            pointer=pointer_str,
        )
        return diagnostic

    def add_diagnostic(self, diagnostic: Diagnostic) -> None:
        """Add a diagnostic to the collection."""
        self.diagnostics.append(diagnostic)

    def has_errors(self) -> bool:
        """Check if any diagnostics have been recorded."""
        return len(self.diagnostics) > 0

    def get_errors(self) -> List[Diagnostic]:
        """Return a copy of all collected diagnostics."""
        return list(self.diagnostics)

    def clear(self) -> None:
        """Clear all collected diagnostics."""
        self.diagnostics.clear()

    def format_diagnostic(self, diagnostic: Diagnostic) -> str:
        """Format a single diagnostic into a standardized, readable report block."""
        header_title = diagnostic.error_type.upper()
        divider = "=" * 60
        lines: List[str] = [divider, header_title, divider]

        file_label = diagnostic.filename if diagnostic.filename else self.default_filename
        lines.append(f"File: {file_label}")

        loc_parts: List[str] = []
        if diagnostic.line is not None:
            loc_parts.append(f"Line: {diagnostic.line}")
        if diagnostic.column is not None:
            loc_parts.append(f"Column: {diagnostic.column}")
        if loc_parts:
            lines.append(", ".join(loc_parts))

        lines.append("")
        lines.append("Message:")
        lines.append(diagnostic.message)
        lines.append("")

        if diagnostic.context:
            lines.append("Source:")
            lines.append(diagnostic.context)
        elif diagnostic.source_line:
            lines.append("Source:")
            lineno_str = f"{diagnostic.line} | " if diagnostic.line is not None else ""
            lines.append(f"{lineno_str}{diagnostic.source_line}")
            if diagnostic.pointer:
                lines.append(diagnostic.pointer)

        lines.append("")
        lines.append(divider)
        return "\n".join(lines)


# ==============================================================================
# Self-Tests
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 6A: DIAGNOSTIC SYSTEM TEST SUITE")
    print("=" * 60)

    handler = DiagnosticErrorHandler(default_filename="test_program.pyl")

    sample_program = (
        "x = 10\n"
        'y = x + "hello"\n'
        "z = y * 2\n"
        "active = True\n"
    )

    # --------------------------------------------------------------------------
    # TEST 1: Basic context extraction
    # --------------------------------------------------------------------------
    print("\n--- TEST 1: Basic context extraction ---")
    ctx1 = extract_source_context(sample_program, line=2, column=7)
    assert ctx1.line_number == 2
    assert ctx1.column == 7
    assert ctx1.source_line == 'y = x + "hello"'
    assert len(ctx1.context_lines) == 4
    assert "^" in ctx1.formatted_context
    print("[PASS] Test 1: Basic context extracted with accurate line mapping.")

    # --------------------------------------------------------------------------
    # TEST 2: First-line error
    # --------------------------------------------------------------------------
    print("\n--- TEST 2: First-line error ---")
    ctx2 = extract_source_context(sample_program, line=1, column=5)
    assert ctx2.line_number == 1
    assert ctx2.source_line == "x = 10"
    assert any(" 1 | x = 10" in line for line in ctx2.formatted_context.splitlines())
    print("[PASS] Test 2: First-line boundary error correctly framed.")

    # --------------------------------------------------------------------------
    # TEST 3: Last-line error
    # --------------------------------------------------------------------------
    print("\n--- TEST 3: Last-line error ---")
    ctx3 = extract_source_context(sample_program, line=4, column=1)
    assert ctx3.line_number == 4
    assert ctx3.source_line == "active = True"
    assert any(" 4 | active = True" in line for line in ctx3.formatted_context.splitlines())
    print("[PASS] Test 3: Last-line boundary error correctly framed.")

    # --------------------------------------------------------------------------
    # TEST 4: Caret/column positioning
    # --------------------------------------------------------------------------
    print("\n--- TEST 4: Caret/column positioning ---")
    single_line = "alpha = 100"
    ctx4 = extract_source_context(single_line, line=1, column=9)
    # The pointer line format is: " 1 | alpha = 100\n   |         ^"
    # Column 9 means 8 spaces before the caret after the gutter delimiter
    ptr_line = ctx4.pointer_line
    assert "^" in ptr_line
    gutter_part, caret_part = ptr_line.split("|")
    caret_indent = len(caret_part) - len(caret_part.lstrip())
    assert caret_indent == 9, f"Expected 9 leading spaces in caret portion (1 space padding + 8 column spaces), got {caret_indent}"
    print("[PASS] Test 4: Caret positioned precisely at column 9.")

    # --------------------------------------------------------------------------
    # TEST 5: Diagnostic creation
    # --------------------------------------------------------------------------
    print("\n--- TEST 5: Diagnostic creation ---")
    diag = handler.create_diagnostic(
        phase="semantic",
        message="Operator '+' cannot be applied to operands of type 'int' and 'str'",
        filename="example.pyl",
        line=2,
        column=7,
        source=sample_program,
    )
    assert diag.phase == "semantic"
    assert diag.error_type == "Semantic Error"
    assert diag.line == 2
    assert diag.column == 7
    assert diag.filename == "example.pyl"
    assert diag.source_line == 'y = x + "hello"'
    assert diag.context is not None

    formatted = handler.format_diagnostic(diag)
    assert "SEMANTIC ERROR" in formatted
    assert "File: example.pyl" in formatted
    assert "Line: 2, Column: 7" in formatted
    assert "Operator '+' cannot be applied" in formatted
    assert "^" in formatted
    print("[PASS] Test 5: Structured diagnostic created and formatted cleanly.")
    print("\nFormatted Diagnostic Output:")
    print(formatted)

    # --------------------------------------------------------------------------
    # TEST 6: Multiple diagnostics
    # --------------------------------------------------------------------------
    print("\n--- TEST 6: Multiple diagnostics ---")
    handler.clear()
    d1 = handler.create_diagnostic("lexer", "Unexpected character '@'", line=1, column=3)
    d2 = handler.create_diagnostic("parser", "Unexpected token 'else'", line=2, column=1)
    d3 = handler.create_diagnostic("semantic", "Undefined variable 'foo'", line=3, column=5)
    handler.add_diagnostic(d1)
    handler.add_diagnostic(d2)
    handler.add_diagnostic(d3)

    assert handler.has_errors() is True
    errors = handler.get_errors()
    assert len(errors) == 3
    assert errors[0].phase == "lexer" and errors[0].error_type == "Lexical Error"
    assert errors[1].phase == "parser" and errors[1].error_type == "Syntax Error"
    assert errors[2].phase == "semantic" and errors[2].error_type == "Semantic Error"
    print("[PASS] Test 6: Multiple diagnostics recorded across lexer, parser, and semantic phases.")

    # --------------------------------------------------------------------------
    # TEST 7: Clearing diagnostics
    # --------------------------------------------------------------------------
    print("\n--- TEST 7: Clearing diagnostics ---")
    assert handler.has_errors() is True
    handler.clear()
    assert handler.has_errors() is False
    assert len(handler.get_errors()) == 0
    print("[PASS] Test 7: Diagnostics cleared successfully.")

    print("\n" + "=" * 60)
    print("PHASE 6A TESTS COMPLETE")
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")

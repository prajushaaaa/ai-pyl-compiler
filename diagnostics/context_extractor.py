"""Source Code Context Extractor for Compiler Diagnostics.

Phase 6A: Diagnostic Architecture & Context Specification.
Extracts source code lines surrounding error coordinates, aligns line numbers,
and generates visual pointer carets (^) indicating the precise error location.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple


# ==============================================================================
# Source Context Representation
# ==============================================================================

@dataclass
class SourceContext:
    """Encapsulates extracted source code context around an error coordinate."""
    source_line: str
    line_number: int
    column: int
    context_lines: List[Tuple[int, str]]
    formatted_context: str
    pointer_line: str

    def __str__(self) -> str:
        return self.formatted_context


# ==============================================================================
# Context Extraction Logic
# ==============================================================================

def extract_source_context(
    source: str,
    line: int,
    column: Optional[int] = None,
    surrounding_lines: int = 2,
) -> SourceContext:
    """Extract source lines surrounding an error coordinate and format with a caret pointer.
    
    Args:
        source: Complete source code string.
        line: 1-indexed error line number.
        column: 1-indexed error column number (defaults to 1 if None or <= 0).
        surrounding_lines: Number of lines before and after error line to include (default 2).
        
    Returns:
        SourceContext containing extracted lines, caret pointer, and formatted snippet.
    """
    lines = source.splitlines() if source else []
    total_lines = len(lines)
    col = column if column is not None and column > 0 else 1

    # Handle empty source or line numbers outside valid range
    if total_lines == 0:
        pointer_str = f"  | {' ' * (col - 1)}^"
        return SourceContext(
            source_line="",
            line_number=line,
            column=col,
            context_lines=[],
            formatted_context=f"  | <empty source>\n{pointer_str}",
            pointer_line=pointer_str,
        )

    if line < 1 or line > total_lines:
        msg = f"<line {line} out of range (total lines: {total_lines})>"
        pointer_str = f"  | {' ' * (col - 1)}^"
        return SourceContext(
            source_line="",
            line_number=line,
            column=col,
            context_lines=[],
            formatted_context=f"  | {msg}\n{pointer_str}",
            pointer_line=pointer_str,
        )

    # Valid line within bounds (1-indexed)
    source_line = lines[line - 1]

    # Calculate surrounding context window
    start_line = max(1, line - surrounding_lines)
    end_line = min(total_lines, line + surrounding_lines)

    context_lines: List[Tuple[int, str]] = [
        (i, lines[i - 1]) for i in range(start_line, end_line + 1)
    ]

    # Format lines with gutter and caret
    gutter_width = max(len(str(end_line)), 2)
    formatted_rows: List[str] = []
    pointer_line = ""

    for curr_line_num, curr_line_text in context_lines:
        prefix = f"{curr_line_num:>{gutter_width}} | "
        formatted_rows.append(f"{prefix}{curr_line_text}")

        # Insert caret pointer immediately below the target error line
        if curr_line_num == line:
            indent_spaces = " " * max(0, col - 1)
            pointer_line = f"{' ' * gutter_width} | {indent_spaces}^"
            formatted_rows.append(pointer_line)

    formatted_context = "\n".join(formatted_rows)

    return SourceContext(
        source_line=source_line,
        line_number=line,
        column=col,
        context_lines=context_lines,
        formatted_context=formatted_context,
        pointer_line=pointer_line,
    )


# ==============================================================================
# Context Extractor Class Interface
# ==============================================================================

class ContextExtractor:
    """Configurable wrapper for extracting source context."""

    def __init__(self, surrounding_lines: int = 2) -> None:
        self.surrounding_lines = surrounding_lines

    def extract(
        self,
        source: str,
        line: int,
        column: Optional[int] = None,
        surrounding_lines: Optional[int] = None,
    ) -> SourceContext:
        """Extract context around line/column using configured or overridden window."""
        window = surrounding_lines if surrounding_lines is not None else self.surrounding_lines
        return extract_source_context(
            source=source,
            line=line,
            column=column,
            surrounding_lines=window,
        )


# ==============================================================================
# Self-Tests
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONTEXT EXTRACTOR SELF-TEST")
    print("=" * 60)

    sample_src = (
        "x = 10\n"
        "y = x + amount\n"
        "z = y * 2\n"
        "print(z)\n"
    )

    # Test 1: Basic middle line extraction
    ctx1 = extract_source_context(sample_src, line=2, column=9)
    assert ctx1.line_number == 2
    assert ctx1.column == 9
    assert ctx1.source_line == "y = x + amount"
    assert len(ctx1.context_lines) == 4
    assert "^" in ctx1.formatted_context
    print("[PASS] Test 1: Middle line context extraction.")
    print("Formatted snippet:\n" + ctx1.formatted_context)

    # Test 2: First-line error
    ctx2 = extract_source_context(sample_src, line=1, column=5)
    assert ctx2.line_number == 1
    assert ctx2.source_line == "x = 10"
    print("\n[PASS] Test 2: First-line error extraction.")

    # Test 3: Last-line error
    ctx3 = extract_source_context(sample_src, line=4, column=1)
    assert ctx3.line_number == 4
    assert ctx3.source_line == "print(z)"
    print("[PASS] Test 3: Last-line error extraction.")

    # Test 4: Single line program
    ctx4 = extract_source_context("a = 1", line=1, column=1)
    assert ctx4.line_number == 1
    assert len(ctx4.context_lines) == 1
    print("[PASS] Test 4: Single-line source extraction.")

    # Test 5: Out of range line number
    ctx5 = extract_source_context(sample_src, line=99, column=1)
    assert "out of range" in ctx5.formatted_context
    print("[PASS] Test 5: Out-of-range line number handled gracefully.")

    print("\n" + "=" * 60)
    print("CONTEXT EXTRACTOR TESTS COMPLETE")
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")

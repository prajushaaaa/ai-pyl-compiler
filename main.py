"""AI-Powered Python-Like (.pyl) Compiler CLI Entry Point.

Phase 6E: Compiler Pipeline CLI Integration.
Integrates the complete compilation pipeline:
  Source File
      ↓
  Lexer (IndentationLexer)
      ↓
  Parser (PLY LALR(1))
      ↓
  AST Tree
      ↓
  Semantic Analyzer (Type Checking & Scoping)
      ↓
  TAC Generator (Three-Address Code IR)
      ↓
  SUCCESS / ERROR

On compilation errors:
  Compiler Error
      ↓
  Diagnostic Creation (DiagnosticErrorHandler)
      ↓
  Source Context Extraction (ContextExtractor)
      ↓
  AI Diagnostic Assistant (GroqAIProvider / MockAIProvider)
      ↓
  Structured Diagnostic & Remediation Output
"""

import os
import sys
from typing import Optional, List, Callable

# Ensure UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexer.lexer import tokenize
from parser.parser import parse_source, ParseError
from semantics.semantic_analyzer import SemanticAnalyzer, SemanticError
from codegen.tac_generator import TACGenerator
from diagnostics.error_handler import DiagnosticErrorHandler, Diagnostic
from diagnostics.ai_diagnostic import (
    AIProvider,
    GroqAIProvider,
    MockAIProvider,
    GroqDiagnosticError,
    GroqConfigurationError,
    diagnose_with_provider,
)


def _handle_ai_diagnostic(
    diagnostic: Diagnostic,
    provider: Optional[AIProvider] = None,
    output_writer: Callable[[str], None] = print,
) -> None:
    """Invoke AI diagnostic provider safely without crashing the compiler."""
    output_writer("\nAI Diagnostic:")
    try:
        if provider is None:
            provider = GroqAIProvider()
        response = diagnose_with_provider(diagnostic, provider)
        output_writer(response.format_response())
    except GroqConfigurationError as e:
        output_writer(f"Unavailable — {e}")
    except GroqDiagnosticError as e:
        output_writer(f"Unavailable — {e}")
    except Exception as e:
        output_writer(f"Unavailable — {e}")


def compile_source(
    source: str,
    filename: str = "<source>",
    ai_provider: Optional[AIProvider] = None,
    output_writer: Callable[[str], None] = print,
) -> int:
    """Execute the complete compiler pipeline on a source code string.

    Returns:
        0 on success, non-zero (1) on compiler or analysis error.
    """
    output_writer("=" * 60)
    output_writer(".pyl COMPILER")
    output_writer("=" * 60)
    output_writer(f"\nFile: {filename}\n")

    handler = DiagnosticErrorHandler(default_filename=filename)

    # --------------------------------------------------------------------------
    # Stage 1: Lexical Analysis
    # --------------------------------------------------------------------------
    tokens_list, lex_errors = tokenize(source)
    if lex_errors:
        output_writer("[1/4] Lexical Analysis ........ FAIL\n")
        first_err = lex_errors[0]
        diag = handler.create_diagnostic(
            phase="lexer",
            message=first_err.get("message", "Lexical error"),
            line=first_err.get("line"),
            column=first_err.get("column"),
            filename=filename,
            source=source,
        )
        handler.add_diagnostic(diag)
        output_writer(handler.format_diagnostic(diag))
        _handle_ai_diagnostic(diag, ai_provider, output_writer)
        return 1

    output_writer("[1/4] Lexical Analysis ........ PASS")

    # --------------------------------------------------------------------------
    # Stage 2: Syntactic Analysis (Parser) & AST Construction
    # --------------------------------------------------------------------------
    try:
        ast = parse_source(source)
        output_writer("[2/4] Parsing .................. PASS")
    except ParseError as e:
        output_writer("[2/4] Parsing .................. FAIL\n")
        diag = handler.create_diagnostic(
            phase="parser",
            message=e.message,
            line=e.line,
            column=e.column,
            filename=filename,
            source=source,
            exception=e,
        )
        handler.add_diagnostic(diag)
        output_writer(handler.format_diagnostic(diag))
        _handle_ai_diagnostic(diag, ai_provider, output_writer)
        return 1
    except Exception as e:
        output_writer("[2/4] Parsing .................. FAIL\n")
        diag = handler.create_diagnostic(
            phase="parser",
            message=str(e),
            filename=filename,
            source=source,
            exception=e,
        )
        handler.add_diagnostic(diag)
        output_writer(handler.format_diagnostic(diag))
        _handle_ai_diagnostic(diag, ai_provider, output_writer)
        return 1

    # --------------------------------------------------------------------------
    # Stage 3: Semantic Analysis & Type Validation
    # --------------------------------------------------------------------------
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
        output_writer("[3/4] Semantic Analysis ........ PASS")
    except SemanticError as e:
        output_writer("[3/4] Semantic Analysis ........ FAIL\n")
        diag = handler.create_diagnostic(
            phase="semantic",
            message=e.message,
            line=e.line,
            column=e.column,
            filename=filename,
            source=source,
            exception=e,
        )
        handler.add_diagnostic(diag)
        output_writer(handler.format_diagnostic(diag))
        _handle_ai_diagnostic(diag, ai_provider, output_writer)
        return 1
    except Exception as e:
        output_writer("[3/4] Semantic Analysis ........ FAIL\n")
        diag = handler.create_diagnostic(
            phase="semantic",
            message=str(e),
            filename=filename,
            source=source,
            exception=e,
        )
        handler.add_diagnostic(diag)
        output_writer(handler.format_diagnostic(diag))
        _handle_ai_diagnostic(diag, ai_provider, output_writer)
        return 1

    # --------------------------------------------------------------------------
    # Stage 4: Three-Address Code (TAC) Generation
    # --------------------------------------------------------------------------
    generator = TACGenerator()
    try:
        tac_instructions = generator.generate(ast)
        output_writer("[4/4] TAC Generation ........... PASS")
    except Exception as e:
        output_writer("[4/4] TAC Generation ........... FAIL\n")
        output_writer(f"Error during TAC generation: {e}")
        return 1

    # --------------------------------------------------------------------------
    # Compilation Success
    # --------------------------------------------------------------------------
    output_writer("\n" + "=" * 60)
    output_writer("COMPILATION SUCCESS")
    output_writer("=" * 60)
    output_writer("\nThree Address Code:")
    output_writer("-" * 40)
    for instr in tac_instructions:
        output_writer(str(instr))
    output_writer("-" * 40)

    return 0


def compile_file(
    filepath: str,
    ai_provider: Optional[AIProvider] = None,
    output_writer: Callable[[str], None] = print,
) -> int:
    """Read a .pyl source file and compile it through the compiler pipeline."""
    if not os.path.exists(filepath):
        output_writer(f"Error: File '{filepath}' not found.")
        return 1

    if os.path.isdir(filepath):
        output_writer(f"Error: '{filepath}' is a directory, not a .pyl source file.")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        output_writer(f"Error reading file '{filepath}': {e}")
        return 1

    return compile_source(
        source=source,
        filename=filepath,
        ai_provider=ai_provider,
        output_writer=output_writer,
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point for the .pyl compiler."""
    if argv is None:
        argv = sys.argv[1:]

    mock_ai = False
    no_ai = False
    files: List[str] = []

    for arg in argv:
        if arg == "--mock-ai":
            mock_ai = True
        elif arg == "--no-ai":
            no_ai = True
        elif arg.startswith("-"):
            # Unknown flag - ignore or treat as option
            pass
        else:
            files.append(arg)

    if not files:
        print("Usage: python main.py <source_file.pyl>")
        return 1

    filepath = files[0]

    provider: Optional[AIProvider] = None
    if no_ai:
        class DisabledAIProvider(AIProvider):
            def diagnose(self, prompt: str):
                raise GroqConfigurationError("AI diagnostics disabled.")
        provider = DisabledAIProvider()
    elif mock_ai or os.environ.get("PYL_AI_PROVIDER") == "mock":
        provider = MockAIProvider()

    return compile_file(filepath=filepath, ai_provider=provider)


if __name__ == "__main__":
    sys.exit(main())

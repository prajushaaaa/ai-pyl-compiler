"""Phase 7: Full End-to-End Compiler Validation & Quality Test Suite.

Comprehensive end-to-end verification of the .pyl compiler pipeline:
  .pyl source
      ↓
  Lexer (IndentationLexer)
      ↓
  Parser (PLY LALR(1))
      ↓
  AST Tree
      ↓
  Semantic Analyzer (Scoped SymbolTable & Type Checker)
      ↓
  TAC Generator (Three-Address Code IR)

Tests included:
1. Full Pipeline on Valid Programs (Arithmetic, Precedence, Parentheses, Boolean,
   If, If-Else, If-Elif-Else, While, Nested Control Flow, Multiple Assignments)
2. Comprehensive Invalid Program Rejections (Undefined variable, Type mismatch,
   Invalid boolean op, Invalid condition, Indentation error, Illegal character,
   Syntax error, Incompatible comparison)
3. AI Diagnostic Integration (Real compiler error -> Context -> Prompt -> MockAIProvider)
"""

import os
import sys
import unittest
from typing import List, Tuple, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexer.lexer import tokenize
from parser.parser import parse_source, ParseError
from semantics.semantic_analyzer import SemanticAnalyzer, SemanticError
from codegen.tac_generator import TACGenerator, TACInstruction
from diagnostics.error_handler import DiagnosticErrorHandler, Diagnostic
from diagnostics.ai_diagnostic import (
    MockAIProvider,
    PromptBuilder,
    DiagnosticResponse,
    diagnose_with_provider,
)


def run_pipeline(source: str, filename: str = "test.pyl") -> Tuple[bool, Optional[str], Optional[List[TACInstruction]], Optional[Diagnostic]]:
    """Execute the compiler pipeline in strict order.

    Returns:
        (success, phase_failed, tac_instructions, diagnostic)
    """
    handler = DiagnosticErrorHandler(default_filename=filename)

    # 1. Lexical Analysis
    tokens_list, lex_errors = tokenize(source)
    if lex_errors:
        err = lex_errors[0]
        diag = handler.create_diagnostic(
            phase="lexer",
            message=err.get("message", "Lexical error"),
            line=err.get("line"),
            column=err.get("column"),
            filename=filename,
            source=source,
        )
        return False, "lexer", None, diag

    # 2. Parsing & AST
    try:
        ast = parse_source(source)
    except ParseError as e:
        diag = handler.create_diagnostic(
            phase="parser",
            message=e.message,
            line=e.line,
            column=e.column,
            filename=filename,
            source=source,
            exception=e,
        )
        return False, "parser", None, diag
    except Exception as e:
        diag = handler.create_diagnostic(
            phase="parser",
            message=str(e),
            filename=filename,
            source=source,
            exception=e,
        )
        return False, "parser", None, diag

    # 3. Semantic Analysis
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
    except SemanticError as e:
        diag = handler.create_diagnostic(
            phase="semantic",
            message=e.message,
            line=e.line,
            column=e.column,
            filename=filename,
            source=source,
            exception=e,
        )
        return False, "semantic", None, diag
    except Exception as e:
        diag = handler.create_diagnostic(
            phase="semantic",
            message=str(e),
            filename=filename,
            source=source,
            exception=e,
        )
        return False, "semantic", None, diag

    # 4. TAC Generation
    generator = TACGenerator()
    tac_instructions = generator.generate(ast)
    return True, None, tac_instructions, None


# ==============================================================================
# Part 1: Valid Programs End-to-End Tests
# ==============================================================================

class TestValidPipelineEndToEnd(unittest.TestCase):
    """Verifies that complete valid programs compile through the full pipeline to TAC."""

    def test_01_basic_arithmetic(self):
        source = "x = 10 + 20\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success, f"Pipeline failed at phase: {failed_phase}")
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("t1 = 10 + 20", tac_str)
        self.assertIn("x = t1", tac_str)

    def test_02_operator_precedence(self):
        source = "x = 10 + 20 * 5\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("t1 = 20 * 5", tac_str)
        self.assertIn("t2 = 10 + t1", tac_str)
        self.assertIn("x = t2", tac_str)

    def test_03_parentheses(self):
        source = "x = (10 + 20) * 5\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("t1 = 10 + 20", tac_str)
        self.assertIn("t2 = t1 * 5", tac_str)
        self.assertIn("x = t2", tac_str)

    def test_04_boolean_expressions(self):
        source = (
            "a = True\n"
            "b = False\n"
            "c = a and b\n"
            "d = not c\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("a = True", tac_str)
        self.assertIn("b = False", tac_str)
        self.assertIn("t1 = a and b", tac_str)
        self.assertIn("c = t1", tac_str)
        self.assertIn("t2 = not c", tac_str)
        self.assertIn("d = t2", tac_str)

    def test_05_if_statement(self):
        source = (
            "x = 10\n"
            "if x > 5:\n"
            "    y = 20\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("t1 = x > 5", tac_str)
        self.assertIn("if_false t1 goto L1", tac_str)
        self.assertIn("y = 20", tac_str)
        self.assertIn("L1:", tac_str)

    def test_06_if_else_statement(self):
        source = (
            "x = 10\n"
            "if x > 5:\n"
            "    y = 20\n"
            "else:\n"
            "    y = 30\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("t1 = x > 5", tac_str)
        self.assertIn("if_false t1 goto L1", tac_str)
        self.assertIn("y = 20", tac_str)
        self.assertIn("goto L2", tac_str)
        self.assertIn("L1:", tac_str)
        self.assertIn("y = 30", tac_str)
        self.assertIn("L2:", tac_str)

    def test_07_if_elif_else_statement(self):
        source = (
            "x = 10\n"
            "if x > 10:\n"
            "    y = 1\n"
            "elif x > 5:\n"
            "    y = 2\n"
            "else:\n"
            "    y = 3\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        # Should have conditional jumps to elif and else labels, and unconditional gotos to end
        self.assertTrue(any("if_false" in line for line in tac_str))
        self.assertTrue(any("goto" in line for line in tac_str))
        self.assertIn("y = 1", tac_str)
        self.assertIn("y = 2", tac_str)
        self.assertIn("y = 3", tac_str)

    def test_08_while_loop(self):
        source = (
            "count = 5\n"
            "while count > 0:\n"
            "    count = count - 1\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("count = 5", tac_str)
        self.assertIn("L1:", tac_str)
        self.assertIn("t1 = count > 0", tac_str)
        self.assertIn("if_false t1 goto L2", tac_str)
        self.assertIn("t2 = count - 1", tac_str)
        self.assertIn("count = t2", tac_str)
        self.assertIn("goto L1", tac_str)
        self.assertIn("L2:", tac_str)

    def test_09_nested_control_flow(self):
        source = (
            "x = 10\n"
            "if x > 5:\n"
            "    if x > 8:\n"
            "        y = 1\n"
            "    else:\n"
            "        y = 2\n"
            "    x = 20\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("x = 10", tac_str)
        self.assertIn("y = 1", tac_str)
        self.assertIn("y = 2", tac_str)
        self.assertIn("x = 20", tac_str)
        self.assertTrue(len(tac) >= 10)

    def test_10_multiple_assignments(self):
        source = (
            "a = 1\n"
            "b = 2\n"
            "c = 3\n"
            "total = a + b + c\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertTrue(success)
        self.assertIsNotNone(tac)
        tac_str = [str(i) for i in tac]
        self.assertIn("a = 1", tac_str)
        self.assertIn("b = 2", tac_str)
        self.assertIn("c = 3", tac_str)
        self.assertIn("total = t2", tac_str)


# ==============================================================================
# Part 2: Comprehensive Invalid Programs End-to-End Tests
# ==============================================================================

class TestInvalidProgramsEndToEnd(unittest.TestCase):
    """Verifies that invalid programs are accurately detected and halted in the correct phase."""

    def test_01_undefined_variable(self):
        source = "x = y + 10\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNone(tac, "TAC must not be produced when semantic error occurs")
        self.assertIsNotNone(diag)
        self.assertEqual(diag.phase, "semantic")
        self.assertIn("Undefined variable 'y'", diag.message)
        self.assertIn("^", diag.context or "")

    def test_02_type_mismatch_int_str(self):
        source = (
            "x = 10\n"
            'message = x + "items"\n'
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("Operator '+' cannot be applied", diag.message)
        self.assertIn("int", diag.message)
        self.assertIn("str", diag.message)

    def test_03_invalid_boolean_operation(self):
        source = (
            "x = 10\n"
            "y = 20\n"
            "z = x and y\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("requires operands of type 'bool'", diag.message)

    def test_04_invalid_condition(self):
        source = (
            "x = 10\n"
            "if x:\n"
            "    y = 20\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("must evaluate to 'bool'", diag.message)

    def test_05_invalid_indentation(self):
        source = (
            "if True:\n"
            "    x = 10\n"
            "      y = 20\n"
        )
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "lexer")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("Indentation error", diag.message)

    def test_06_invalid_character(self):
        source = "x = 10 @ 20\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "lexer")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("Unexpected character '@'", diag.message)

    def test_07_syntax_error(self):
        source = "x = 10 + * 20\n"
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "parser")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("SyntaxError", diag.message)

    def test_08_invalid_operator_combination(self):
        source = 'x = 10 == "hello"\n'
        success, failed_phase, tac, diag = run_pipeline(source)
        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNone(tac)
        self.assertIsNotNone(diag)
        self.assertIn("cannot compare incompatible types", diag.message)


# ==============================================================================
# Part 3: AI Diagnostic Integration Test (Deterministic / Offline)
# ==============================================================================

class TestAIDiagnosticIntegrationEndToEnd(unittest.TestCase):
    """Verifies that real compiler errors flow seamlessly to the AI diagnostic provider."""

    def test_real_error_to_mock_ai_response(self):
        source = (
            "x = 10\n"
            'message = x + "items"\n'
        )
        success, failed_phase, tac, diag = run_pipeline(source, filename="shopping.pyl")

        self.assertFalse(success)
        self.assertEqual(failed_phase, "semantic")
        self.assertIsNotNone(diag)

        # 1. Structured Diagnostic Verification
        self.assertEqual(diag.phase, "semantic")
        self.assertEqual(diag.error_type, "Semantic Error")
        self.assertEqual(diag.line, 2)
        self.assertIn("shopping.pyl", diag.filename or "")
        self.assertIn("message = x + \"items\"", diag.context or "")
        self.assertIn("^", diag.context or "")

        # 2. Prompt Construction
        builder = PromptBuilder()
        prompt = builder.build_prompt(diag)
        self.assertIn(".pyl", prompt)
        self.assertIn("SEMANTIC", prompt)
        self.assertIn("shopping.pyl", prompt)
        self.assertIn("Do not invent language features", prompt)

        # 3. AI Provider Diagnostic Response
        provider = MockAIProvider()
        response = diagnose_with_provider(diag, provider)

        self.assertIsInstance(response, DiagnosticResponse)
        self.assertTrue(len(response.explanation) > 0, "Explanation must not be empty")
        self.assertTrue(len(response.cause) > 0, "Cause must not be empty")
        self.assertTrue(len(response.suggestion) > 0, "Suggested Fix must not be empty")
        self.assertTrue(len(response.corrected_code) > 0, "Corrected Code must not be empty")

        formatted = response.format_response()
        self.assertIn("Explanation:", formatted)
        self.assertIn("Cause:", formatted)
        self.assertIn("Suggested Fix:", formatted)
        self.assertIn("Corrected Code:", formatted)


# ==============================================================================
# Test Runner
# ==============================================================================

def run_tests():
    """Execute all Phase 7 end-to-end tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestValidPipelineEndToEnd))
    suite.addTests(loader.loadTestsFromTestCase(TestInvalidProgramsEndToEnd))
    suite.addTests(loader.loadTestsFromTestCase(TestAIDiagnosticIntegrationEndToEnd))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

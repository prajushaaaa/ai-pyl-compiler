"""Phase 6E: Dedicated Automated CLI Regression Test Suite.

Verifies end-to-end command-line behavior of the .pyl compiler:
  python main.py <source_file.pyl>

Automated Tests:
- TEST 1: No command-line argument -> usage & non-zero exit code
- TEST 2: Missing source file -> clear file-not-found error & non-zero exit code
- TEST 3: Valid .pyl program -> exit code 0, 4/4 PASS, COMPILATION SUCCESS, TAC output
- TEST 4: Valid control-flow program -> exit code 0, branch/conditional TAC
- TEST 5: Lexical error -> exit code non-zero, [1/4] FAIL, LEXICAL ERROR, context & caret
- TEST 6: Indentation error -> exit code non-zero, [1/4] FAIL, indentation error, context & caret
- TEST 7: Semantic error -> exit code non-zero, [1/4] & [2/4] PASS, [3/4] FAIL, SEMANTIC ERROR
- TEST 8: AI failure fallback -> compiler does not crash, authoritative error preserved
"""

import os
import sys
import tempfile
import subprocess
import unittest
from typing import Optional, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")

from main import compile_file, compile_source
from diagnostics.ai_diagnostic import AIProvider, DiagnosticResponse, GroqAPIError


class MockFailingAIProvider(AIProvider):
    """Simulates an AI provider that fails during network or API communication."""
    def diagnose(self, prompt: str) -> DiagnosticResponse:
        raise GroqAPIError("Connection refused by remote host.")


class TestCompilerCLI(unittest.TestCase):
    """Automated CLI test suite for Phase 6E."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        # Clean environment without GROQ_API_KEY for deterministic offline CLI testing
        self.clean_env = os.environ.copy()
        self.clean_env.pop("GROQ_API_KEY", None)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_temp_file(self, content: str, filename: str = "temp.pyl") -> str:
        filepath = os.path.join(self.temp_dir.name, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def _run_cli(self, args: list, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        target_env = env if env is not None else self.clean_env
        cmd = [sys.executable, MAIN_PY] + args
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=target_env,
            cwd=PROJECT_ROOT,
        )

    # --------------------------------------------------------------------------
    # TEST 1: No command-line argument
    # --------------------------------------------------------------------------
    def test_1_no_argument(self):
        proc = self._run_cli([])
        output = proc.stdout + proc.stderr

        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code when no arguments provided")
        self.assertIn("Usage: python main.py <source_file.pyl>", output)
        self.assertNotIn("Traceback", output)

    # --------------------------------------------------------------------------
    # TEST 2: Missing source file
    # --------------------------------------------------------------------------
    def test_2_missing_file(self):
        missing_path = os.path.join(self.temp_dir.name, "nonexistent_source.pyl")
        proc = self._run_cli([missing_path])
        output = proc.stdout + proc.stderr

        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code for missing file")
        self.assertIn("Error: File", output)
        self.assertIn("not found", output)
        self.assertNotIn("Traceback", output)

    # --------------------------------------------------------------------------
    # TEST 3: Valid .pyl program
    # --------------------------------------------------------------------------
    def test_3_valid_program(self):
        source = (
            "x = 10\n"
            "y = 20\n"
            "z = x + y\n"
        )
        filepath = self._create_temp_file(source, "valid_prog.pyl")
        proc = self._run_cli([filepath])
        output = proc.stdout

        self.assertEqual(proc.returncode, 0, f"Expected exit code 0 for valid program, got {proc.returncode}.\nOutput: {output}")
        self.assertIn("[1/4] Lexical Analysis ........ PASS", output)
        self.assertIn("[2/4] Parsing .................. PASS", output)
        self.assertIn("[3/4] Semantic Analysis ........ PASS", output)
        self.assertIn("[4/4] TAC Generation ........... PASS", output)
        self.assertIn("COMPILATION SUCCESS", output)
        self.assertIn("Three Address Code:", output)
        self.assertIn("x = 10", output)
        self.assertIn("y = 20", output)
        self.assertIn("z = ", output)
        self.assertNotIn("Traceback", proc.stderr)

    # --------------------------------------------------------------------------
    # TEST 4: Valid control-flow program
    # --------------------------------------------------------------------------
    def test_4_control_flow(self):
        source = (
            "x = 10\n"
            "if x > 5:\n"
            "    y = 20\n"
        )
        filepath = self._create_temp_file(source, "valid_control.pyl")
        proc = self._run_cli([filepath])
        output = proc.stdout

        self.assertEqual(proc.returncode, 0, f"Expected exit code 0 for control flow, got {proc.returncode}")
        self.assertIn("[1/4] Lexical Analysis ........ PASS", output)
        self.assertIn("[2/4] Parsing .................. PASS", output)
        self.assertIn("[3/4] Semantic Analysis ........ PASS", output)
        self.assertIn("[4/4] TAC Generation ........... PASS", output)
        self.assertIn("COMPILATION SUCCESS", output)
        self.assertIn("Three Address Code:", output)
        # Check for branch representation: if_false, goto, and jump label L1:
        self.assertTrue(
            ("if_false" in output or "goto" in output or "L1:" in output),
            "Expected branch/conditional TAC instructions in output"
        )
        self.assertNotIn("Traceback", proc.stderr)

    # --------------------------------------------------------------------------
    # TEST 5: Lexical error
    # --------------------------------------------------------------------------
    def test_5_lexical_error(self):
        source = "x = 10 @ 20\n"
        filepath = self._create_temp_file(source, "lex_err.pyl")
        proc = self._run_cli([filepath])
        output = proc.stdout + proc.stderr

        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code on lexical error")
        self.assertIn("[1/4] Lexical Analysis ........ FAIL", output)
        self.assertIn("LEXICAL ERROR", output)
        self.assertIn("x = 10 @ 20", output)
        self.assertIn("^", output)
        self.assertNotIn("[2/4] Parsing .................. PASS", output)
        self.assertNotIn("[3/4] Semantic Analysis ........ PASS", output)
        self.assertNotIn("[4/4] TAC Generation ........... PASS", output)
        self.assertNotIn("COMPILATION SUCCESS", output)
        self.assertNotIn("Traceback", output)

    # --------------------------------------------------------------------------
    # TEST 6: Indentation error
    # --------------------------------------------------------------------------
    def test_6_indentation_error(self):
        source = (
            "if True:\n"
            "    x = 10\n"
            "      y = 20\n"
        )
        filepath = self._create_temp_file(source, "indent_err.pyl")
        proc = self._run_cli([filepath])
        output = proc.stdout + proc.stderr

        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code on indentation error")
        self.assertIn("[1/4] Lexical Analysis ........ FAIL", output)
        self.assertIn("Indentation error", output)
        self.assertIn("y = 20", output)
        self.assertIn("^", output)
        self.assertNotIn("[2/4] Parsing .................. PASS", output)
        self.assertNotIn("COMPILATION SUCCESS", output)
        self.assertNotIn("Traceback", output)

    # --------------------------------------------------------------------------
    # TEST 7: Semantic error
    # --------------------------------------------------------------------------
    def test_7_semantic_error(self):
        source = (
            "x = 10\n"
            'message = x + "items"\n'
        )
        filepath = self._create_temp_file(source, "semantic_err.pyl")
        proc = self._run_cli([filepath])
        output = proc.stdout + proc.stderr

        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code on semantic error")
        self.assertIn("[1/4] Lexical Analysis ........ PASS", output)
        self.assertIn("[2/4] Parsing .................. PASS", output)
        self.assertIn("[3/4] Semantic Analysis ........ FAIL", output)
        self.assertIn("SEMANTIC ERROR", output)
        self.assertIn("Operator '+' cannot be applied to operands of type 'int' and 'str'", output)
        self.assertNotIn("[4/4] TAC Generation ........... PASS", output)
        self.assertNotIn("COMPILATION SUCCESS", output)
        self.assertNotIn("Traceback", output)

    # --------------------------------------------------------------------------
    # TEST 8: AI failure does not break compiler
    # --------------------------------------------------------------------------
    def test_8_ai_failure_fallback(self):
        source = "x = undefined_variable + 10\n"
        filepath = self._create_temp_file(source, "ai_fail.pyl")

        # 8a: Verify via subprocess with unset GROQ_API_KEY
        proc = self._run_cli([filepath])
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, "Expected non-zero exit code")
        self.assertIn("SEMANTIC ERROR", output)
        self.assertIn("Undefined variable 'undefined_variable'", output)
        self.assertIn("AI Diagnostic:", output)
        self.assertIn("Unavailable — GROQ_API_KEY environment variable is not set.", output)
        self.assertNotIn("Traceback", output)

        # 8b: Verify in-process with MockFailingAIProvider simulating API failure
        output_buffer = []
        exit_code = compile_file(
            filepath=filepath,
            ai_provider=MockFailingAIProvider(),
            output_writer=output_buffer.append,
        )
        self.assertNotEqual(exit_code, 0, "Expected non-zero exit code when AI provider fails")
        in_process_output = "\n".join(output_buffer)
        self.assertIn("SEMANTIC ERROR", in_process_output)
        self.assertIn("AI Diagnostic:", in_process_output)
        self.assertIn("Unavailable — Connection refused by remote host.", in_process_output)
        self.assertNotIn("Traceback", in_process_output)


def run_tests():
    """Run all 8 CLI tests and format output according to academic specifications."""
    print("=" * 60)
    print("PHASE 6E: CLI TEST SUITE")
    print("=" * 60)
    print()

    tests = [
        ("TEST 1: No argument", "test_1_no_argument"),
        ("TEST 2: Missing file", "test_2_missing_file"),
        ("TEST 3: Valid program", "test_3_valid_program"),
        ("TEST 4: Control flow", "test_4_control_flow"),
        ("TEST 5: Lexical error", "test_5_lexical_error"),
        ("TEST 6: Indentation error", "test_6_indentation_error"),
        ("TEST 7: Semantic error", "test_7_semantic_error"),
        ("TEST 8: AI failure fallback", "test_8_ai_failure_fallback"),
    ]

    all_passed = True
    test_case = TestCompilerCLI()

    for label, method_name in tests:
        test_case.setUp()
        try:
            getattr(test_case, method_name)()
            status = "PASS"
        except Exception as e:
            status = f"FAIL ({e})"
            all_passed = False
        finally:
            test_case.tearDown()

        dots = "." * (36 - len(label))
        print(f"{label} {dots} {status}")

    print()
    print("=" * 60)
    print("PHASE 6E CLI TESTS COMPLETE")
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY!\n")
    else:
        print("SOME TESTS FAILED!\n")

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

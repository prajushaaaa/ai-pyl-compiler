"""Phase 5C: Full Front-End -> TAC Integration Testing.

Verifies the end-to-end compiler pipeline:
    .pyl Source Code
           ↓
      Lexer (PLY)
           ↓
     Parser (LALR)
           ↓
       AST Nodes
           ↓
   Semantic Analyzer (Scoping & Type Checking)
           ↓
     TAC Generator (Three-Address Code)

Ensures that:
1. Valid programs pass through all stages and emit correct, deterministic TAC.
2. Semantic errors halt the pipeline before TAC generation.
3. Syntax/indentation errors halt the pipeline before semantic analysis and TAC generation.
"""

import os
import sys
from typing import List, Tuple, Any

# Ensure workspace root is in sys.path when running tests
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import real compiler pipeline stages
from lexer.lexer import build_lexer, tokenize
from parser.parser import parse_source, ParseError
from parser.ast_nodes import ASTNode
from semantics.semantic_analyzer import SemanticAnalyzer, SemanticError
from codegen.tac_generator import TACGenerator, TACInstruction


# ==============================================================================
# Full Pipeline Compilation Helper
# ==============================================================================

def compile_to_tac(source: str) -> Tuple[List[TACInstruction], SemanticAnalyzer, ASTNode]:
    """Execute the full compiler pipeline on a .pyl source code string.
    
    Stages:
        1. Lexer & Parser -> Constructs AST
        2. Semantic Analyzer -> Scoped Symbol Table & Type Validation
        3. TAC Generator -> Intermediate Three-Address Code
        
    Returns:
        A tuple of (instructions, analyzer, ast)
        
    Raises:
        ParseError: If syntax or indentation is invalid.
        SemanticError: If scoping or type checking fails.
    """
    # Stage 1: Lexing + Parsing -> AST
    ast = parse_source(source)

    # Stage 2: Semantic Analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # Stage 3: Three-Address Code Generation
    generator = TACGenerator()
    instructions = generator.generate(ast)

    return instructions, analyzer, ast


# ==============================================================================
# Integration Test Suite
# ==============================================================================

def run_integration_tests():
    print("=" * 60)
    print("PHASE 5C: FULL FRONT-END → TAC INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------------------------------
    # TEST 1: Basic arithmetic
    # --------------------------------------------------------------------------
    print("\n--- TEST 1: Basic arithmetic ---")
    t1_src = "x = 10 + 20 * 5\n"
    instructions, analyzer, ast = compile_to_tac(t1_src)
    tac_lines = [str(instr) for instr in instructions]

    assert "t1 = 20 * 5" in tac_lines, f"Expected 't1 = 20 * 5' in TAC, got: {tac_lines}"
    assert "t2 = 10 + t1" in tac_lines, f"Expected 't2 = 10 + t1' in TAC, got: {tac_lines}"
    assert "x = t2" in tac_lines, f"Expected 'x = t2' in TAC, got: {tac_lines}"
    print("[PASS] Arithmetic precedence correctly preserved and lowered to TAC.")
    print("Generated TAC:")
    for line in tac_lines:
        print(f"  {line}")

    # --------------------------------------------------------------------------
    # TEST 2: Conditional
    # --------------------------------------------------------------------------
    print("\n--- TEST 2: Conditional ---")
    t2_src = (
        "x = 10\n"
        "if x > 5:\n"
        "    y = x + 20\n"
    )
    instructions, analyzer, ast = compile_to_tac(t2_src)
    tac_lines = [str(instr) for instr in instructions]

    # Verify key properties
    assert any(line == "x = 10" for line in tac_lines), "Missing 'x = 10'"
    assert any("x > 5" in line for line in tac_lines), "Missing relational condition 'x > 5'"
    assert any(line.startswith("if_false") for line in tac_lines), "Missing if_false jump"
    assert any("y =" in line for line in tac_lines), "Missing assignment to 'y'"
    assert any(line.endswith(":") for line in tac_lines), "Missing jump label"
    print("[PASS] Conditional statement correctly validated and transformed into branch TAC.")

    # --------------------------------------------------------------------------
    # TEST 3: If-else
    # --------------------------------------------------------------------------
    print("\n--- TEST 3: If-else ---")
    t3_src = (
        "x = 10\n"
        "if x > 5:\n"
        "    y = 20\n"
        "else:\n"
        "    y = 30\n"
    )
    instructions, analyzer, ast = compile_to_tac(t3_src)
    tac_lines = [str(instr) for instr in instructions]

    assert any("x > 5" in line for line in tac_lines), "Missing condition TAC"
    assert any(line.startswith("if_false") for line in tac_lines), "Missing if_false instruction"
    assert any("y = 20" in line for line in tac_lines), "Missing 'then' branch assignment"
    assert any("y = 30" in line for line in tac_lines), "Missing 'else' branch assignment"
    assert any(line.startswith("goto") for line in tac_lines), "Missing unconditional goto jump"
    labels = [line for line in tac_lines if line.endswith(":")]
    assert len(labels) >= 2, f"Expected at least 2 labels, got: {labels}"
    print("[PASS] If-else branches, unconditional goto, and labels verified.")

    # --------------------------------------------------------------------------
    # TEST 4: While loop
    # --------------------------------------------------------------------------
    print("\n--- TEST 4: While loop ---")
    t4_src = (
        "x = 3\n"
        "while x > 0:\n"
        "    x = x - 1\n"
    )
    instructions, analyzer, ast = compile_to_tac(t4_src)
    tac_lines = [str(instr) for instr in instructions]

    labels = [line for line in tac_lines if line.endswith(":")]
    assert len(labels) == 2, f"Expected loop header and exit labels, got: {labels}"
    start_label = labels[0][:-1]
    assert any("x > 0" in line for line in tac_lines), "Missing while condition 'x > 0'"
    assert any(line.startswith("if_false") for line in tac_lines), "Missing if_false exit jump"
    assert any("x - 1" in line for line in tac_lines), "Missing decrement expression 'x - 1'"
    assert f"goto {start_label}" in tac_lines, f"Missing back-edge 'goto {start_label}'"
    print("[PASS] While loop header, exit condition, back-edge jump verified.")

    # --------------------------------------------------------------------------
    # TEST 5: Nested control flow
    # --------------------------------------------------------------------------
    print("\n--- TEST 5: Nested control flow ---")
    t5_src = (
        "x = 10\n"
        "while x > 0:\n"
        "    if x > 5:\n"
        "        y = x * 2\n"
        "    else:\n"
        "        y = x + 2\n"
        "    x = x - 1\n"
    )
    instructions, analyzer, ast = compile_to_tac(t5_src)
    tac_lines = [str(instr) for instr in instructions]

    labels = [line for line in tac_lines if line.endswith(":")]
    assert len(labels) >= 4, f"Expected at least 4 labels for nested control flow, got: {labels}"
    assert any("x > 0" in line for line in tac_lines), "Missing outer loop condition"
    assert any("x > 5" in line for line in tac_lines), "Missing nested if condition"
    assert any("x * 2" in line for line in tac_lines), "Missing then arithmetic 'x * 2'"
    assert any("x + 2" in line for line in tac_lines), "Missing else arithmetic 'x + 2'"
    assert any("x - 1" in line for line in tac_lines), "Missing decrement 'x - 1'"
    assert any(line.startswith("goto L1") for line in tac_lines), "Missing loop back-edge to L1"
    print("[PASS] Nested control flow (while containing if-else) generated correctly.")
    print("Generated TAC:")
    for line in tac_lines:
        print(f"  {line}")

    # --------------------------------------------------------------------------
    # TEST 6: Semantic failure must stop TAC generation
    # --------------------------------------------------------------------------
    print("\n--- TEST 6: Semantic failure must stop TAC generation ---")
    t6_src = (
        "x = 10\n"
        'y = x + "hello"\n'
    )
    tac_generated = False
    try:
        compile_to_tac(t6_src)
        tac_generated = True
    except SemanticError as e:
        print(f"[PASS] Semantic analyzer halted pipeline on type mismatch: {e.message}")
    assert not tac_generated, "TAC generation must NOT be performed on semantic failure!"

    # --------------------------------------------------------------------------
    # TEST 7: Undefined variable must stop TAC generation
    # --------------------------------------------------------------------------
    print("\n--- TEST 7: Undefined variable must stop TAC generation ---")
    t7_src = "x = y + 10\n"
    tac_generated = False
    try:
        compile_to_tac(t7_src)
        tac_generated = True
    except SemanticError as e:
        print(f"[PASS] Semantic analyzer halted pipeline on undefined variable: {e.message}")
    assert not tac_generated, "TAC generation must NOT be performed on undefined variable!"

    # --------------------------------------------------------------------------
    # TEST 8: Invalid indentation/syntax must stop the pipeline
    # --------------------------------------------------------------------------
    print("\n--- TEST 8: Invalid indentation/syntax must stop pipeline ---")
    t8_src = (
        "if x > 5:\n"
        "x = 10\n"
    )
    semantic_or_tac_reached = False
    try:
        compile_to_tac(t8_src)
        semantic_or_tac_reached = True
    except ParseError as e:
        print(f"[PASS] Parser halted pipeline on missing indent: {e.message}")
    assert not semantic_or_tac_reached, "Pipeline must halt at parsing on invalid indentation!"

    print("\n" + "=" * 60)
    print("PHASE 5C INTEGRATION TEST COMPLETE")
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!\n")
    print("Lexer → Parser → AST → Semantic Analyzer → TAC Generator")
    print("                         ALL CONNECTED")


if __name__ == "__main__":
    run_integration_tests()

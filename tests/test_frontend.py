"""Front-End Integration Test for .pyl Compiler.

Phase 3D: Front-End Integration Test.
Verifies the complete pipeline:
  Source Code (.pyl) -> Lexer (Tokens) -> Parser (CST/AST) -> AST Node Structure
"""

import os
import sys

# Ensure workspace root is in sys.path when running tests
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from lexer.lexer import build_lexer, tokenize
from parser.parser import parse_source, build_parser
from parser.ast_nodes import (
    ProgramNode,
    BlockNode,
    AssignmentNode,
    IdentifierNode,
    LiteralNode,
    BinaryOpNode,
    IfNode,
    print_tree,
)


def test_basic_frontend():
    print("==================================================")
    print("TEST 1: Basic Front-End Pipeline")
    print("==================================================")

    source = """x = 10
if x > 5:
    y = x + 20
    z = y * 2
"""
    print("\n[1] Source Code:")
    for line in source.strip().split("\n"):
        print(f"    {line}")

    # 1. Build lexer and tokenize
    lexer = build_lexer()
    tokens, errors = tokenize(source, lexer=lexer)
    assert not errors, f"Lexical errors encountered: {errors}"

    # 2. Show token sequence
    print("\n[2] Token Sequence:")
    token_reprs = []
    for tok in tokens:
        val_str = r"\n" if tok.type == "NEWLINE" else str(tok.value)
        token_reprs.append(f"{tok.type}({val_str})")
    print("    " + " -> ".join(token_reprs))

    # 3. Parse source into AST
    ast = parse_source(source)

    # 4. Print resulting AST
    print("\n[3] Resulting AST Tree:")
    print_tree(ast)

    # 5. Verify ProgramNode root
    assert isinstance(ast, ProgramNode), f"Expected ProgramNode, got {type(ast).__name__}"

    # 6. Verify two top-level statements (AssignmentNode, IfNode)
    assert len(ast.statements) == 2, f"Expected 2 top-level statements, got {len(ast.statements)}"
    stmt1, stmt2 = ast.statements
    assert isinstance(stmt1, AssignmentNode), f"Expected AssignmentNode, got {type(stmt1).__name__}"
    assert isinstance(stmt2, IfNode), f"Expected IfNode, got {type(stmt2).__name__}"
    assert stmt1.target.name == "x", f"Expected assignment target 'x', got '{stmt1.target.name}'"

    # 7. Verify IfNode contains a BlockNode
    assert isinstance(stmt2.then_block, BlockNode), (
        f"Expected IfNode.then_block to be BlockNode, got {type(stmt2.then_block).__name__}"
    )

    # 8. Verify the block contains two assignments
    block_stmts = stmt2.then_block.statements
    assert len(block_stmts) == 2, f"Expected 2 block statements, got {len(block_stmts)}"
    assert isinstance(block_stmts[0], AssignmentNode), (
        f"Expected AssignmentNode for statement 1, got {type(block_stmts[0]).__name__}"
    )
    assert isinstance(block_stmts[1], AssignmentNode), (
        f"Expected AssignmentNode for statement 2, got {type(block_stmts[1]).__name__}"
    )
    assert block_stmts[0].target.name == "y", f"Expected target 'y', got '{block_stmts[0].target.name}'"
    assert block_stmts[1].target.name == "z", f"Expected target 'z', got '{block_stmts[1].target.name}'"

    print("\n[OK] Test 1 Assertions Passed successfully.")


def test_nested_frontend():
    print("\n==================================================")
    print("TEST 2: Nested Block Front-End Pipeline")
    print("==================================================")

    source = """if x > 5:
    if y > 2:
        z = 10
    x = 20
"""
    print("\n[1] Source Code:")
    for line in source.strip().split("\n"):
        print(f"    {line}")

    # Tokenize and parse
    tokens, errors = tokenize(source)
    assert not errors, f"Lexical errors encountered: {errors}"

    ast = parse_source(source)

    # Print AST tree
    print("\n[2] Resulting AST Tree:")
    print_tree(ast)

    # Verify structural hierarchy
    assert isinstance(ast, ProgramNode), f"Expected ProgramNode, got {type(ast).__name__}"
    assert len(ast.statements) == 1, f"Expected 1 top-level statement, got {len(ast.statements)}"

    outer_if = ast.statements[0]
    assert isinstance(outer_if, IfNode), f"Expected IfNode, got {type(outer_if).__name__}"

    outer_block = outer_if.then_block
    assert isinstance(outer_block, BlockNode), f"Expected BlockNode, got {type(outer_block).__name__}"
    assert len(outer_block.statements) == 2, (
        f"Expected 2 statements in outer block, got {len(outer_block.statements)}"
    )

    inner_stmt1, inner_stmt2 = outer_block.statements
    assert isinstance(inner_stmt1, IfNode), (
        f"Expected first statement in outer block to be IfNode, got {type(inner_stmt1).__name__}"
    )
    assert isinstance(inner_stmt2, AssignmentNode), (
        f"Expected second statement in outer block to be AssignmentNode, got {type(inner_stmt2).__name__}"
    )
    assert inner_stmt2.target.name == "x", f"Expected target 'x', got '{inner_stmt2.target.name}'"

    # Verify inner if statement
    inner_block = inner_stmt1.then_block
    assert isinstance(inner_block, BlockNode), f"Expected BlockNode, got {type(inner_block).__name__}"
    assert len(inner_block.statements) == 1, (
        f"Expected 1 statement in inner block, got {len(inner_block.statements)}"
    )
    inner_assign = inner_block.statements[0]
    assert isinstance(inner_assign, AssignmentNode), (
        f"Expected AssignmentNode, got {type(inner_assign).__name__}"
    )
    assert inner_assign.target.name == "z", f"Expected target 'z', got '{inner_assign.target.name}'"

    print("\n[OK] Test 2 Assertions Passed successfully.")


def main():
    try:
        test_basic_frontend()
        test_nested_frontend()
        print("\n==================================================")
        print("FRONT-END INTEGRATION TEST PASSED")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

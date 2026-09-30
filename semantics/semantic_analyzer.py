"""Semantic Analyzer for Python-Like Language (.pyl).

Phase 4B: Semantic Analysis & Type Checking.
Traverses the Abstract Syntax Tree (AST) produced by parser.py, uses the Scoped
SymbolTable to perform static type validation, variable declaration/reassignment
tracking, scoping management, and semantic verification according to language rules.
"""

import os
import sys
from typing import Optional, Any

# Ensure project root is in sys.path when running directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from parser.ast_nodes import (
    ASTNode,
    ProgramNode,
    BlockNode,
    AssignmentNode,
    IdentifierNode,
    LiteralNode,
    BinaryOpNode,
    UnaryOpNode,
    IfNode,
    ElifNode,
    WhileNode,
)
from semantics.symbol_table import (
    SymbolTable,
    Symbol,
    UndefinedSymbolError,
    DuplicateSymbolError,
    ScopeError,
)


# ==============================================================================
# Semantic Error Exception
# ==============================================================================

class SemanticError(Exception):
    """Custom exception raised for static semantic and type errors."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ) -> None:
        self.message = message
        self.line = line
        self.column = column

        loc_parts = []
        if line is not None:
            loc_parts.append(f"line {line}")
        if column is not None:
            loc_parts.append(f"column {column}")

        loc_str = f" at {', '.join(loc_parts)}" if loc_parts else ""
        full_message = f"SemanticError{loc_str}: {message}"
        super().__init__(full_message)

    def __str__(self) -> str:
        loc_parts = []
        if self.line is not None:
            loc_parts.append(f"line {self.line}")
        if self.column is not None:
            loc_parts.append(f"column {self.column}")
        loc_str = f" at {', '.join(loc_parts)}" if loc_parts else ""
        return f"SemanticError{loc_str}: {self.message}"


# ==============================================================================
# Semantic Analyzer Visitor
# ==============================================================================

class SemanticAnalyzer:
    """AST visitor that enforces static typing and lexical scoping rules."""

    def __init__(self, symbol_table: Optional[SymbolTable] = None) -> None:
        self.symbol_table: SymbolTable = (
            symbol_table if symbol_table is not None else SymbolTable()
        )

    def get_symbol_table(self) -> SymbolTable:
        """Return the active symbol table."""
        return self.symbol_table

    def analyze(self, ast: ASTNode) -> SymbolTable:
        """Entry point for performing semantic analysis on an AST."""
        self.visit(ast)
        return self.symbol_table

    def visit(self, node: ASTNode) -> Any:
        """Dispatch visit call based on AST node class name."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> Any:
        """Fallback visitor for unhandled node types."""
        raise NotImplementedError(
            f"No semantic visitor defined for AST node: {node.__class__.__name__}"
        )

    # --------------------------------------------------------------------------
    # Program and Block Visitors
    # --------------------------------------------------------------------------

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        """Visit program root statements in the top-level (global) scope."""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_BlockNode(self, node: BlockNode) -> None:
        """Visit a nested block of statements within an isolated lexical scope."""
        self.symbol_table.enter_scope()
        try:
            for stmt in node.statements:
                self.visit(stmt)
        finally:
            self.symbol_table.exit_scope()

    # --------------------------------------------------------------------------
    # Statement Visitors
    # --------------------------------------------------------------------------

    def visit_AssignmentNode(self, node: AssignmentNode) -> str:
        """Check and record variable definition or reassignment.
        
        Scoping Rules:
        - If the variable exists in the CURRENT scope: update its type.
        - If the variable does NOT exist in the CURRENT scope: define it in the CURRENT scope.
        - Outer scope variables are shadowed, not automatically updated.
        """
        val_type = self.visit(node.value)
        target_name = node.target.name

        existing_symbol = self.symbol_table.lookup_current_scope(target_name)
        if existing_symbol is not None:
            existing_symbol.type = val_type
        else:
            line = node.target.lineno or node.lineno
            column = node.target.column or node.column
            self.symbol_table.define(
                name=target_name,
                type_name=val_type,
                line=line,
                column=column,
            )
        return val_type

    def visit_IfNode(self, node: IfNode) -> None:
        """Verify conditional branch statement."""
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            line = node.condition.lineno or node.lineno
            col = node.condition.column or node.column
            raise SemanticError(
                f"If condition must evaluate to 'bool', but got '{cond_type}'",
                line=line,
                column=col,
            )

        self.visit(node.then_block)

        for elif_clause in node.elif_clauses:
            self.visit(elif_clause)

        if node.else_block is not None:
            self.visit(node.else_block)

    def visit_ElifNode(self, node: ElifNode) -> None:
        """Verify elif branch statement."""
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            line = node.condition.lineno or node.lineno
            col = node.condition.column or node.column
            raise SemanticError(
                f"Elif condition must evaluate to 'bool', but got '{cond_type}'",
                line=line,
                column=col,
            )

        self.visit(node.then_block)

    def visit_WhileNode(self, node: WhileNode) -> None:
        """Verify while loop construct."""
        cond_type = self.visit(node.condition)
        if cond_type != "bool":
            line = node.condition.lineno or node.lineno
            col = node.condition.column or node.column
            raise SemanticError(
                f"While condition must evaluate to 'bool', but got '{cond_type}'",
                line=line,
                column=col,
            )

        self.visit(node.body)

    # --------------------------------------------------------------------------
    # Expression Visitors
    # --------------------------------------------------------------------------

    def visit_IdentifierNode(self, node: IdentifierNode) -> str:
        """Look up variable in symbol table and return its inferred type."""
        try:
            sym = self.symbol_table.lookup(node.name)
            return sym.type
        except UndefinedSymbolError:
            raise SemanticError(
                f"Undefined variable '{node.name}'",
                line=node.lineno,
                column=node.column,
            )

    def visit_LiteralNode(self, node: LiteralNode) -> str:
        """Return the literal's type."""
        type_name = node.type_name
        if type_name not in ("int", "float", "str", "bool"):
            raise SemanticError(
                f"Unsupported literal type '{type_name}'",
                line=node.lineno,
                column=node.column,
            )
        return type_name

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        """Infer and type-check binary operations."""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        op = node.operator

        # 1. Addition and String Concatenation
        if op == "+":
            if left_type == "int" and right_type == "int":
                return "int"
            if (left_type == "int" and right_type == "float") or \
               (left_type == "float" and right_type == "int") or \
               (left_type == "float" and right_type == "float"):
                return "float"
            if left_type == "str" and right_type == "str":
                return "str"
            raise SemanticError(
                f"Operator '+' cannot be applied to operands of type '{left_type}' and '{right_type}'",
                line=node.lineno,
                column=node.column,
            )

        # 2. Arithmetic Subtraction, Multiplication, Division
        if op in ("-", "*", "/"):
            if left_type == "int" and right_type == "int":
                return "int"
            if (left_type == "int" and right_type == "float") or \
               (left_type == "float" and right_type == "int") or \
               (left_type == "float" and right_type == "float"):
                return "float"
            raise SemanticError(
                f"Operator '{op}' cannot be applied to operands of type '{left_type}' and '{right_type}'",
                line=node.lineno,
                column=node.column,
            )

        # 3. Relational Ordering (<, >)
        if op in ("<", ">"):
            if left_type in ("int", "float") and right_type in ("int", "float"):
                return "bool"
            raise SemanticError(
                f"Relational operator '{op}' cannot be applied to operands of type '{left_type}' and '{right_type}'",
                line=node.lineno,
                column=node.column,
            )

        # 4. Relational Equality (==, !=)
        if op in ("==", "!="):
            # Numeric int/float are cross-compatible
            if left_type in ("int", "float") and right_type in ("int", "float"):
                return "bool"
            # Identical types are compatible (str == str, bool == bool)
            if left_type == right_type:
                return "bool"
            raise SemanticError(
                f"Comparison operator '{op}' cannot compare incompatible types '{left_type}' and '{right_type}'",
                line=node.lineno,
                column=node.column,
            )

        # 5. Boolean Operators (and, or)
        if op in ("and", "or"):
            if left_type == "bool" and right_type == "bool":
                return "bool"
            raise SemanticError(
                f"Boolean operator '{op}' requires operands of type 'bool', but got '{left_type}' and '{right_type}'",
                line=node.lineno,
                column=node.column,
            )

        raise SemanticError(
            f"Unsupported binary operator '{op}'",
            line=node.lineno,
            column=node.column,
        )

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        """Infer and type-check unary operations."""
        operand_type = self.visit(node.operand)
        op = node.operator

        if op == "-":
            if operand_type in ("int", "float"):
                return operand_type
            raise SemanticError(
                f"Unary operator '-' cannot be applied to operand of type '{operand_type}'",
                line=node.lineno,
                column=node.column,
            )

        if op == "not":
            if operand_type == "bool":
                return "bool"
            raise SemanticError(
                f"Unary operator 'not' requires operand of type 'bool', but got '{operand_type}'",
                line=node.lineno,
                column=node.column,
            )

        raise SemanticError(
            f"Unsupported unary operator '{op}'",
            line=node.lineno,
            column=node.column,
        )


# ==============================================================================
# Self-Tests
# ==============================================================================

if __name__ == "__main__":
    from parser.parser import parse_source

    print("=" * 60)
    print("PHASE 4B: SEMANTIC ANALYZER TEST SUITE")
    print("=" * 60)

    failed_tests = []
    last_successful_analyzer = None

    def run_test(test_num: int, title: str, source: str, should_pass: bool, expected_error_substr: Optional[str] = None):
        global last_successful_analyzer
        print(f"\n--- TEST {test_num}: {title} ---")
        try:
            ast = parse_source(source)
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)

            if should_pass:
                last_successful_analyzer = analyzer
                print(f"[PASS] Test {test_num} passed as expected.")
                return True
            else:
                print(f"[FAIL] Test {test_num} failed: expected SemanticError but analysis passed.")
                failed_tests.append(test_num)
                return False

        except SemanticError as e:
            if not should_pass:
                if expected_error_substr is None or expected_error_substr in str(e):
                    print(f"[PASS] Test {test_num} correctly raised SemanticError: {e}")
                    return True
                else:
                    print(f"[FAIL] Test {test_num} raised SemanticError, but expected substring '{expected_error_substr}'. Got: {e}")
                    failed_tests.append(test_num)
                    return False
            else:
                print(f"[FAIL] Test {test_num} failed with unexpected SemanticError: {e}")
                failed_tests.append(test_num)
                return False
        except Exception as e:
            print(f"[FAIL] Test {test_num} failed with unexpected exception ({type(e).__name__}): {e}")
            failed_tests.append(test_num)
            return False

    # TEST 1: Valid basic program
    t1_src = "x = 10\ny = x + 20\n"
    if run_test(1, "Valid basic program", t1_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("x").type == "int"
        assert st.lookup("y").type == "int"

    # TEST 2: Float promotion
    t2_src = "x = 10\ny = 2.5\nz = x + y\n"
    if run_test(2, "Float promotion", t2_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("z").type == "float"

    # TEST 3: String concatenation
    t3_src = 'first = "Hello "\nsecond = "World"\nmessage = first + second\n'
    if run_test(3, "String concatenation", t3_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("message").type == "str"

    # TEST 4: Boolean expression
    t4_src = "a = True\nb = False\nc = a and b\nd = not c\n"
    if run_test(4, "Boolean expression", t4_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("c").type == "bool"
        assert st.lookup("d").type == "bool"

    # TEST 5: Relational expression
    t5_src = "x = 10\ny = 20\nresult = x < y\n"
    if run_test(5, "Relational expression", t5_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("result").type == "bool"

    # TEST 6: Undefined variable
    t6_src = "y = x + 10\n"
    run_test(6, "Undefined variable", t6_src, should_pass=False, expected_error_substr="Undefined variable 'x'")

    # TEST 7: Invalid type operation
    t7_src = 'x = 10\ny = "hello"\nz = x + y\n'
    run_test(7, "Invalid type operation", t7_src, should_pass=False)

    # TEST 8: Invalid boolean operation
    t8_src = "x = 10\ny = 20\nz = x and y\n"
    run_test(8, "Invalid boolean operation", t8_src, should_pass=False)

    # TEST 9: Invalid if condition
    t9_src = "x = 10\nif x:\n    y = 20\n"
    run_test(9, "Invalid if condition", t9_src, should_pass=False)

    # TEST 10: Valid nested block
    t10_src = "x = 10\nif x > 5:\n    y = 20\n    if y > 10:\n        z = 30\n"
    run_test(10, "Valid nested block", t10_src, should_pass=True)

    # TEST 11: Variable outside block
    t11_src = "x = 10\nif x > 5:\n    y = 20\nz = y + 5\n"
    run_test(11, "Variable outside block", t11_src, should_pass=False, expected_error_substr="Undefined variable 'y'")

    # TEST 12: Unary operations
    t12_src = "x = -10\ny = 5.5\nz = -y\n"
    if run_test(12, "Unary operations", t12_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        assert st.lookup("x").type == "int"
        assert st.lookup("y").type == "float"
        assert st.lookup("z").type == "float"

    # TEST 13: Nested-scope shadowing
    t13_src = (
        "x = 10\n"
        "if x > 5:\n"
        "    y = 20\n"
        "    y = 30\n"
        '    x = "shadowed"\n'
    )
    if run_test(13, "Nested-scope shadowing", t13_src, should_pass=True):
        st = last_successful_analyzer.get_symbol_table()
        # Verify global x remains int
        global_x = st.lookup("x")
        assert global_x.type == "int", f"Expected global x to remain int, got {global_x.type}"
        assert global_x.scope_name == "global"

        # Verify nested scope exists independently and contains shadowed x and updated y
        nested_scope = st.all_scopes[1]
        assert "x" in nested_scope.symbols, "Nested x was not found in nested scope"
        assert nested_scope.symbols["x"].type == "str", f"Expected nested x to be str, got {nested_scope.symbols['x'].type}"
        assert nested_scope.symbols["x"].scope_name == "scope_1"
        assert "y" in nested_scope.symbols, "Nested y was not found in nested scope"
        assert nested_scope.symbols["y"].type == "int"

    print("\n" + "=" * 60)
    print("SEMANTIC ANALYZER TESTS COMPLETE")
    print("=" * 60)

    if failed_tests:
        print(f"FAILED TESTS: {failed_tests}")
    else:
        print("ALL 13 TESTS PASSED SUCCESSFULLY!")

    if last_successful_analyzer is not None:
        print("\nSymbol Table from Successful Test (Test 13 - Global Scope):")
        print("-" * 40)
        last_successful_analyzer.get_symbol_table().print_table()
        print("-" * 40)

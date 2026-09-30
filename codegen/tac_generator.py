"""Three-Address Code (TAC) Generator for Python-Like Language (.pyl).

Phase 5B: Intermediate Representation (IR) Generation.
Transforms the Abstract Syntax Tree (AST) produced by parser.py into linear
Three-Address Code (TAC) instructions, generating synthetic temporaries (t1, t2, ...)
and jump labels (L1, L2, ...) for expressions and control flow structures.
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Any

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


# ==============================================================================
# TAC Instruction Representation
# ==============================================================================

@dataclass
class TACInstruction:
    """Represents a single Three-Address Code instruction.
    
    Structure:
    - op: Operator or opcode (e.g. '+', '-', '*', '/', '=', 'if_false', 'goto', 'label', 'not')
    - arg1: First operand (variable, temporary, literal, or None)
    - arg2: Second operand (for binary operations, or None)
    - result: Destination temporary/variable, or label target
    """
    op: str
    arg1: Optional[Any] = None
    arg2: Optional[Any] = None
    result: Optional[str] = None

    def to_tuple(self) -> tuple:
        """Return a tuple representation of this instruction."""
        return (self.op, self.arg1, self.arg2, self.result)

    def __str__(self) -> str:
        """Render instruction in standard human-readable TAC format."""
        if self.op == "label":
            return f"{self.result}:"
        elif self.op == "goto":
            return f"goto {self.result}"
        elif self.op == "if_false":
            return f"if_false {self.arg1} goto {self.result}"
        elif self.op == "if_true":
            return f"if_true {self.arg1} goto {self.result}"
        elif self.op == "=":
            return f"{self.result} = {self.arg1}"
        elif self.op in ("-", "not") and self.arg2 is None:
            # Unary operations
            if self.op == "not":
                return f"{self.result} = not {self.arg1}"
            else:
                return f"{self.result} = -{self.arg1}"
        else:
            # Binary operations: +, -, *, /, <, >, ==, !=, and, or
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"


# ==============================================================================
# TAC Generator
# ==============================================================================

class TACGenerator:
    """Traverses an AST and emits linear Three-Address Code."""

    def __init__(self) -> None:
        self.instructions: List[TACInstruction] = []
        self.temp_counter: int = 0
        self.label_counter: int = 0

    def new_temp(self) -> str:
        """Generate a fresh synthetic temporary variable (t1, t2, ...)."""
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self) -> str:
        """Generate a fresh jump label (L1, L2, ...)."""
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(
        self,
        op: str,
        arg1: Optional[Any] = None,
        arg2: Optional[Any] = None,
        result: Optional[str] = None,
    ) -> TACInstruction:
        """Emit a new TAC instruction and append it to the instruction list."""
        instr = TACInstruction(op=op, arg1=arg1, arg2=arg2, result=result)
        self.instructions.append(instr)
        return instr

    def generate(self, ast: ASTNode) -> List[TACInstruction]:
        """Generate TAC for the given AST root node and return instruction list."""
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.visit(ast)
        return self.instructions

    def to_string(self) -> str:
        """Return the emitted TAC as formatted multiline string."""
        return "\n".join(str(instr) for instr in self.instructions)

    def dump(self) -> str:
        """Alias for to_string()."""
        return self.to_string()

    def print_tac(self) -> None:
        """Print the emitted TAC to stdout."""
        print(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    # --------------------------------------------------------------------------
    # Visitor Dispatcher
    # --------------------------------------------------------------------------

    def visit(self, node: ASTNode) -> Any:
        """Dispatch visit call based on AST node class name."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> Any:
        """Fallback visitor for unhandled node types."""
        raise NotImplementedError(
            f"No TAC visitor defined for AST node: {node.__class__.__name__}"
        )

    # --------------------------------------------------------------------------
    # Structural Node Visitors
    # --------------------------------------------------------------------------

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        """Visit all top-level statements in the program."""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_BlockNode(self, node: BlockNode) -> None:
        """Visit all statements in an indented block."""
        for stmt in node.statements:
            self.visit(stmt)

    # --------------------------------------------------------------------------
    # Statement Visitors
    # --------------------------------------------------------------------------

    def visit_AssignmentNode(self, node: AssignmentNode) -> None:
        """Emit assignment: target = evaluated_value."""
        val = self.visit(node.value)
        self.emit("=", arg1=val, arg2=None, result=node.target.name)

    # --------------------------------------------------------------------------
    # Expression Visitors
    # --------------------------------------------------------------------------

    def visit_IdentifierNode(self, node: IdentifierNode) -> str:
        """Return variable name."""
        return node.name

    def visit_LiteralNode(self, node: LiteralNode) -> str:
        """Return formatted literal representation."""
        if isinstance(node.value, bool):
            return str(node.value)
        elif isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        """Emit binary operation: temp = left op right."""
        left = self.visit(node.left)
        right = self.visit(node.right)
        temp = self.new_temp()
        self.emit(op=node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        """Emit unary operation: temp = op operand."""
        operand = self.visit(node.operand)
        temp = self.new_temp()
        self.emit(op=node.operator, arg1=operand, arg2=None, result=temp)
        return temp

    # --------------------------------------------------------------------------
    # Control Flow Visitors
    # --------------------------------------------------------------------------

    def visit_IfNode(self, node: IfNode) -> None:
        """Emit TAC for if, if-else, or if-elif-else construct."""
        # Simple if statement (no elif, no else)
        if not node.elif_clauses and not node.else_block:
            end_label = self.new_label()
            cond = self.visit(node.condition)
            self.emit("if_false", arg1=cond, arg2=None, result=end_label)
            self.visit(node.then_block)
            self.emit("label", arg1=None, arg2=None, result=end_label)
            return

        # Multi-branch if (with elif clauses and/or else block)
        branch_labels = [self.new_label() for _ in node.elif_clauses]
        if node.else_block:
            branch_labels.append(self.new_label())
        end_label = self.new_label()

        # 1. Main 'if' branch
        next_label = branch_labels[0]
        cond = self.visit(node.condition)
        self.emit("if_false", arg1=cond, arg2=None, result=next_label)
        self.visit(node.then_block)
        self.emit("goto", arg1=None, arg2=None, result=end_label)

        # 2. 'elif' branches
        for i, elif_clause in enumerate(node.elif_clauses):
            self.emit("label", arg1=None, arg2=None, result=branch_labels[i])
            if i + 1 < len(branch_labels):
                next_target = branch_labels[i + 1]
            else:
                next_target = end_label

            elif_cond = self.visit(elif_clause.condition)
            self.emit("if_false", arg1=elif_cond, arg2=None, result=next_target)
            self.visit(elif_clause.then_block)
            self.emit("goto", arg1=None, arg2=None, result=end_label)

        # 3. Optional 'else' branch
        if node.else_block:
            else_label = branch_labels[-1]
            self.emit("label", arg1=None, arg2=None, result=else_label)
            self.visit(node.else_block)

        # 4. End label
        self.emit("label", arg1=None, arg2=None, result=end_label)

    def visit_ElifNode(self, node: ElifNode) -> None:
        """Normally handled inside visit_IfNode; fallback if visited directly."""
        cond = self.visit(node.condition)
        self.visit(node.then_block)

    def visit_WhileNode(self, node: WhileNode) -> None:
        """Emit TAC for while loop construct."""
        start_label = self.new_label()
        end_label = self.new_label()

        self.emit("label", arg1=None, arg2=None, result=start_label)
        cond = self.visit(node.condition)
        self.emit("if_false", arg1=cond, arg2=None, result=end_label)
        self.visit(node.body)
        self.emit("goto", arg1=None, arg2=None, result=start_label)
        self.emit("label", arg1=None, arg2=None, result=end_label)


# ==============================================================================
# Self-Tests
# ==============================================================================

if __name__ == "__main__":
    from parser.parser import parse_source

    print("=" * 60)
    print("PHASE 5B: THREE-ADDRESS CODE (TAC) GENERATOR TEST SUITE")
    print("=" * 60)

    test_cases = [
        (
            1,
            "Simple Assignment",
            "x = 10\n",
            ["x = 10"],
        ),
        (
            2,
            "Arithmetic Precedence",
            "x = 10 + 20 * 5\n",
            [
                "t1 = 20 * 5",
                "t2 = 10 + t1",
                "x = t2",
            ],
        ),
        (
            3,
            "Parentheses",
            "x = (10 + 20) * 5\n",
            [
                "t1 = 10 + 20",
                "t2 = t1 * 5",
                "x = t2",
            ],
        ),
        (
            4,
            "Boolean Expression",
            "a = True\nb = False\nc = a and b\nd = not c\n",
            [
                "a = True",
                "b = False",
                "t1 = a and b",
                "c = t1",
                "t2 = not c",
                "d = t2",
            ],
        ),
        (
            5,
            "Relational Expression",
            "x = 10\ny = 20\nresult = x < y\n",
            [
                "x = 10",
                "y = 20",
                "t1 = x < y",
                "result = t1",
            ],
        ),
        (
            6,
            "If Statement",
            "if x > 5:\n    y = 10\n",
            [
                "t1 = x > 5",
                "if_false t1 goto L1",
                "y = 10",
                "L1:",
            ],
        ),
        (
            7,
            "If-Else Statement",
            "if x > 5:\n    y = 10\nelse:\n    y = 20\n",
            [
                "t1 = x > 5",
                "if_false t1 goto L1",
                "y = 10",
                "goto L2",
                "L1:",
                "y = 20",
                "L2:",
            ],
        ),
        (
            8,
            "If-Elif-Else Statement",
            "if x > 5:\n    y = 10\nelif x == 0:\n    y = 0\nelse:\n    y = 20\n",
            [
                "t1 = x > 5",
                "if_false t1 goto L1",
                "y = 10",
                "goto L3",
                "L1:",
                "t2 = x == 0",
                "if_false t2 goto L2",
                "y = 0",
                "goto L3",
                "L2:",
                "y = 20",
                "L3:",
            ],
        ),
        (
            9,
            "While Loop",
            "while x > 0:\n    x = x - 1\n",
            [
                "L1:",
                "t1 = x > 0",
                "if_false t1 goto L2",
                "t2 = x - 1",
                "x = t2",
                "goto L1",
                "L2:",
            ],
        ),
        (
            10,
            "Nested Control Flow",
            "if x > 5:\n    while y < 10:\n        y = y + 1\n",
            [
                "t1 = x > 5",
                "if_false t1 goto L1",
                "L2:",
                "t2 = y < 10",
                "if_false t2 goto L3",
                "t3 = y + 1",
                "y = t3",
                "goto L2",
                "L3:",
                "L1:",
            ],
        ),
        (
            11,
            "Complex Expression",
            "result = -(a + b) * (c - d) / 2\n",
            [
                "t1 = a + b",
                "t2 = -t1",
                "t3 = c - d",
                "t4 = t2 * t3",
                "t5 = t4 / 2",
                "result = t5",
            ],
        ),
    ]

    failed = 0
    generator = TACGenerator()

    for test_num, title, source, expected_lines in test_cases:
        print(f"\n--- TEST {test_num}: {title} ---")
        try:
            ast = parse_source(source)
            instructions = generator.generate(ast)
            actual_lines = [str(instr) for instr in instructions]

            # Verify line-by-line equality
            match = (actual_lines == expected_lines)
            if match:
                print(f"[PASS] Test {test_num} generated expected TAC ({len(instructions)} instructions).")
                print("Generated TAC:")
                for line in actual_lines:
                    print(f"  {line}")
            else:
                failed += 1
                print(f"[FAIL] Test {test_num} mismatch!")
                print("Expected:")
                for line in expected_lines:
                    print(f"  {line}")
                print("Actual:")
                for line in actual_lines:
                    print(f"  {line}")

        except Exception as e:
            failed += 1
            print(f"[FAIL] Test {test_num} raised unexpected exception: {e}")

    print("\n" + "=" * 60)
    print("TAC GENERATOR TESTS COMPLETE")
    print("=" * 60)
    if failed == 0:
        print(f"ALL {len(test_cases)} TESTS PASSED SUCCESSFULLY!")
    else:
        print(f"TESTS FAILED: {failed} / {len(test_cases)}")

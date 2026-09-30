"""Abstract Syntax Tree (AST) Node Definitions for Python-Like Language (.pyl).

Phase 3A: AST Design.
Defines a clean, strongly-typed AST node hierarchy representing:
- Program and Block structures (indented blocks)
- Assignments and Identifiers
- Literal values (int, float, string, boolean) with inferred type tags
- Binary and Unary expressions
- Conditional branches (if, elif, else)
- While loops
- Hierarchical tree-printing utilities for AST visualization
"""

import sys
from typing import List, Optional, Any


# ============================================================================
# Base AST Node
# ============================================================================

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    def __init__(self, lineno: Optional[int] = None, column: Optional[int] = None):
        self.lineno = lineno
        self.column = column

    def get_children(self) -> List["ASTNode"]:
        """Return a list of direct child AST nodes for traversal."""
        return []

    def label(self) -> str:
        """Display label used by tree visualization utilities."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# ============================================================================
# Program and Block Structure Nodes
# ============================================================================

class ProgramNode(ASTNode):
    """Root node representing an entire .pyl program."""

    def __init__(
        self,
        statements: Optional[List[ASTNode]] = None,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.statements: List[ASTNode] = statements if statements is not None else []

    def get_children(self) -> List[ASTNode]:
        return list(self.statements)

    def label(self) -> str:
        return "Program"

    def __repr__(self) -> str:
        return f"ProgramNode(statements={self.statements!r})"


class BlockNode(ASTNode):
    """Node representing an indented block of statements."""

    def __init__(
        self,
        statements: Optional[List[ASTNode]] = None,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.statements: List[ASTNode] = statements if statements is not None else []

    def get_children(self) -> List[ASTNode]:
        return list(self.statements)

    def label(self) -> str:
        return "Block"

    def __repr__(self) -> str:
        return f"BlockNode(statements={self.statements!r})"


# ============================================================================
# Statements and Identifiers
# ============================================================================

class IdentifierNode(ASTNode):
    """Leaf node representing an identifier/variable reference."""

    def __init__(
        self,
        name: str,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.name: str = name

    def get_children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return f"Identifier({self.name})"

    def __repr__(self) -> str:
        return f"IdentifierNode(name={self.name!r})"


class AssignmentNode(ASTNode):
    """Node representing a variable assignment statement (target = value)."""

    def __init__(
        self,
        target: IdentifierNode,
        value: ASTNode,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.target: IdentifierNode = target
        self.value: ASTNode = value

    def get_children(self) -> List[ASTNode]:
        return [self.target, self.value]

    def label(self) -> str:
        return "Assignment"

    def __repr__(self) -> str:
        return f"AssignmentNode(target={self.target!r}, value={self.value!r})"


# ============================================================================
# Literals and Expressions
# ============================================================================

class LiteralNode(ASTNode):
    """Leaf node representing a literal value (int, float, str, bool)."""

    def __init__(
        self,
        value: Any,
        type_name: Optional[str] = None,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.value: Any = value

        if type_name is not None:
            self.type_name = type_name
        else:
            # Auto-infer primitive type name
            if isinstance(value, bool):
                self.type_name = "bool"
            elif isinstance(value, int):
                self.type_name = "int"
            elif isinstance(value, float):
                self.type_name = "float"
            elif isinstance(value, str):
                self.type_name = "str"
            else:
                self.type_name = type(value).__name__

    def get_children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        if isinstance(self.value, str):
            return f'Literal("{self.value}")'
        return f"Literal({self.value})"

    def __repr__(self) -> str:
        return f"LiteralNode(value={self.value!r}, type={self.type_name!r})"


class BinaryOpNode(ASTNode):
    """Node representing a binary operation (left op right).
    
    Covers:
    - Arithmetic: +, -, *, /
    - Relational: <, >, ==, !=
    - Boolean: and, or
    """

    def __init__(
        self,
        operator: str,
        left: ASTNode,
        right: ASTNode,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.operator: str = operator
        self.left: ASTNode = left
        self.right: ASTNode = right

    def get_children(self) -> List[ASTNode]:
        return [self.left, self.right]

    def label(self) -> str:
        return f"BinaryOp({self.operator})"

    def __repr__(self) -> str:
        return (
            f"BinaryOpNode(op={self.operator!r}, left={self.left!r}, right={self.right!r})"
        )


class UnaryOpNode(ASTNode):
    """Node representing a unary operation (op operand).
    
    Covers:
    - Arithmetic negation: -
    - Logical negation: not
    """

    def __init__(
        self,
        operator: str,
        operand: ASTNode,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.operator: str = operator
        self.operand: ASTNode = operand

    def get_children(self) -> List[ASTNode]:
        return [self.operand]

    def label(self) -> str:
        return f"UnaryOp({self.operator})"

    def __repr__(self) -> str:
        return f"UnaryOpNode(op={self.operator!r}, operand={self.operand!r})"


# ============================================================================
# Control Flow Nodes
# ============================================================================

class ElifNode(ASTNode):
    """Node representing an 'elif' branch in an if-statement."""

    def __init__(
        self,
        condition: ASTNode,
        then_block: BlockNode,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.condition: ASTNode = condition
        self.then_block: BlockNode = then_block

    def get_children(self) -> List[ASTNode]:
        return [self.condition, self.then_block]

    def label(self) -> str:
        return "Elif"

    def __repr__(self) -> str:
        return f"ElifNode(condition={self.condition!r}, then_block={self.then_block!r})"


class IfNode(ASTNode):
    """Node representing an 'if-elif-else' conditional statement."""

    def __init__(
        self,
        condition: ASTNode,
        then_block: BlockNode,
        elif_clauses: Optional[List[ElifNode]] = None,
        else_block: Optional[BlockNode] = None,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.condition: ASTNode = condition
        self.then_block: BlockNode = then_block
        self.elif_clauses: List[ElifNode] = elif_clauses if elif_clauses is not None else []
        self.else_block: Optional[BlockNode] = else_block

    def get_children(self) -> List[ASTNode]:
        children: List[ASTNode] = [self.condition, self.then_block]
        children.extend(self.elif_clauses)
        if self.else_block is not None:
            children.append(self.else_block)
        return children

    def label(self) -> str:
        return "If"

    def __repr__(self) -> str:
        return (
            f"IfNode(condition={self.condition!r}, then_block={self.then_block!r}, "
            f"elif_clauses={self.elif_clauses!r}, else_block={self.else_block!r})"
        )


class WhileNode(ASTNode):
    """Node representing a 'while' loop construct."""

    def __init__(
        self,
        condition: ASTNode,
        body: BlockNode,
        lineno: Optional[int] = None,
        column: Optional[int] = None,
    ):
        super().__init__(lineno, column)
        self.condition: ASTNode = condition
        self.body: BlockNode = body

    def get_children(self) -> List[ASTNode]:
        return [self.condition, self.body]

    def label(self) -> str:
        return "While"

    def __repr__(self) -> str:
        return f"WhileNode(condition={self.condition!r}, body={self.body!r})"


# ============================================================================
# AST Tree Printing Utility
# ============================================================================

def dump_tree(node: ASTNode, use_ascii: bool = False) -> str:
    """Format an AST node and its subtrees into a formatted ASCII/Unicode tree string."""
    branch_mid = "+-- " if use_ascii else "├── "
    branch_end = "\\-- " if use_ascii else "└── "
    pipe_cont = "|   " if use_ascii else "│   "
    space_cont = "    "

    def _format(n: ASTNode, prefix: str, is_last: bool) -> List[str]:
        branch = branch_end if is_last else branch_mid
        lines = [f"{prefix}{branch}{n.label()}"]
        new_prefix = prefix + (space_cont if is_last else pipe_cont)
        children = n.get_children()
        for idx, child in enumerate(children):
            last = (idx == len(children) - 1)
            lines.extend(_format(child, new_prefix, last))
        return lines

    lines = [node.label()]
    children = node.get_children()
    for idx, child in enumerate(children):
        last = (idx == len(children) - 1)
        lines.extend(_format(child, "", last))
    return "\n".join(lines)


def print_tree(node: ASTNode) -> None:
    """Print the formatted AST tree to stdout with Unicode/ASCII fallback."""
    tree_str = dump_tree(node)
    try:
        print(tree_str)
    except UnicodeEncodeError:
        print(dump_tree(node, use_ascii=True))


# ============================================================================
# Self-Test Section
# ============================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    # Test 1: Exactly matches the user specification prompt:
    # x = 10 + 20 * 5
    expr_ast = ProgramNode([
        AssignmentNode(
            target=IdentifierNode("x"),
            value=BinaryOpNode(
                operator="+",
                left=LiteralNode(10),
                right=BinaryOpNode(
                    operator="*",
                    left=LiteralNode(20),
                    right=LiteralNode(5),
                ),
            ),
        )
    ])

    print("--- Test 1: Expression AST ---")
    print_tree(expr_ast)
    print()

    # Test 2: Full language constructs: If-Elif-Else and While loop
    # if x > 5:
    #     y = 20
    # elif x == 0:
    #     y = 0
    # else:
    #     y = 10
    # while x > 0:
    #     x = x - 1
    prog_ast = ProgramNode([
        IfNode(
            condition=BinaryOpNode(">", IdentifierNode("x"), LiteralNode(5)),
            then_block=BlockNode([
                AssignmentNode(IdentifierNode("y"), LiteralNode(20))
            ]),
            elif_clauses=[
                ElifNode(
                    condition=BinaryOpNode("==", IdentifierNode("x"), LiteralNode(0)),
                    then_block=BlockNode([
                        AssignmentNode(IdentifierNode("y"), LiteralNode(0))
                    ]),
                )
            ],
            else_block=BlockNode([
                AssignmentNode(IdentifierNode("y"), LiteralNode(10))
            ]),
        ),
        WhileNode(
            condition=BinaryOpNode(">", IdentifierNode("x"), LiteralNode(0)),
            body=BlockNode([
                AssignmentNode(
                    IdentifierNode("x"),
                    BinaryOpNode("-", IdentifierNode("x"), LiteralNode(1)),
                )
            ]),
        ),
    ])

    print("--- Test 2: Control Flow AST ---")
    print_tree(prog_ast)

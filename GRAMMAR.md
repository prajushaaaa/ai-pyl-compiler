# Context-Free Grammar (CFG) Specification for .pyl Language

## Phase 3B: Formal Grammar & Syntactic Design

This document defines the formal Context-Free Grammar (CFG) for our restricted Python-like language (`.pyl`), derived from [`LANGUAGE_SPECIFICATION.md`](LANGUAGE_SPECIFICATION.md). The grammar is designed to integrate seamlessly with the deterministic PLY lexer ([`lexer/lexer.py`](lexer/lexer.py)) and the AST hierarchy ([`parser/ast_nodes.py`](parser/ast_nodes.py)).

---

## 1. Lexical Token Terminals

The grammar operates over the following terminal tokens produced by our Phase 2 lexer:

| Category | Token Terminals |
| :--- | :--- |
| **Keywords** | `IF`, `ELIF`, `ELSE`, `WHILE`, `AND`, `OR`, `NOT` |
| **Literals** | `INT`, `FLOAT`, `STRING`, `BOOLEAN` |
| **Identifiers** | `IDENTIFIER` |
| **Arithmetic Operators** | `PLUS` (`+`), `MINUS` (`-`), `MULTIPLY` (`*`), `DIVIDE` (`/`) |
| **Relational Operators** | `LESS` (`<`), `GREATER` (`>`), `EQUALS` (`==`), `NOT_EQUALS` (`!=`) |
| **Assignment Operator** | `ASSIGN` (`=`) |
| **Punctuation** | `COLON` (`:`), `LPAREN` (`(`), `RPAREN` (`)`) |
| **Indentation & Layout** | `NEWLINE`, `INDENT`, `DEDENT` |

---

## 2. Complete Context-Free Grammar (CFG)

```ebnf
(* ===========================================================================
   Program & Statement Structure
   =========================================================================== *)

program
    : statement_list
    | empty

statement_list
    : statement_list statement
    | statement

statement
    : simple_statement
    | compound_statement

simple_statement
    : assignment_statement

assignment_statement
    : IDENTIFIER ASSIGN expr NEWLINE

compound_statement
    : if_statement
    | while_statement

block
    : INDENT statement_list DEDENT

(* ===========================================================================
   Control Flow Statements
   =========================================================================== *)

if_statement
    : IF expr COLON NEWLINE block elif_list else_opt

elif_list
    : elif_list elif_clause
    | empty

elif_clause
    : ELIF expr COLON NEWLINE block

else_opt
    : ELSE COLON NEWLINE block
    | empty

while_statement
    : WHILE expr COLON NEWLINE block

(* ===========================================================================
   Expressions & Precedence Hierarchy (Lowest to Highest)
   =========================================================================== *)

(* Level 1: Logical OR (Left-associative) *)
expr
    : expr OR and_expr
    | and_expr

(* Level 2: Logical AND (Left-associative) *)
and_expr
    : and_expr AND not_expr
    | not_expr

(* Level 3: Logical NOT (Unary prefix) *)
not_expr
    : NOT not_expr
    | comparison

(* Level 4: Relational Comparisons (Non-associative binary) *)
comparison
    : arith_expr comp_op arith_expr
    | arith_expr

comp_op
    : LESS
    | GREATER
    | EQUALS
    | NOT_EQUALS

(* Level 5: Addition & Subtraction (Left-associative) *)
arith_expr
    : arith_expr PLUS term
    | arith_expr MINUS term
    | term

(* Level 6: Multiplication & Division (Left-associative) *)
term
    : term MULTIPLY factor
    | term DIVIDE factor
    | factor

(* Level 7: Unary Arithmetic Negation (Prefix) *)
factor
    : MINUS factor
    | primary

(* Level 8: Primaries, Grouping & Literals (Highest) *)
primary
    : IDENTIFIER
    | literal
    | LPAREN expr RPAREN

literal
    : INT
    | FLOAT
    | STRING
    | BOOLEAN

(* Empty epsilon transition *)
empty
    : (* empty *)
```

---

## 3. Explanation of Non-Terminals

| Non-Terminal | Description |
| :--- | :--- |
| `program` | The start symbol representing the entire source file. May be empty or a list of top-level statements. |
| `statement_list` | A contiguous non-empty sequence of one or more statements. |
| `statement` | A single program statement, categorized into simple (assignment) or compound (if, while). |
| `simple_statement` | A statement contained entirely on a single logical line terminated by `NEWLINE`. |
| `assignment_statement` | Assigns an expression value to an identifier (`target = expr`). |
| `compound_statement` | A multi-line block header statement followed by an indented `block`. |
| `block` | An indented block delineated by synthetic `INDENT` and `DEDENT` tokens. |
| `if_statement` | Conditional branching construct supporting `if`, zero or more `elif` clauses, and an optional `else`. |
| `elif_list` | A sequence of zero or more `elif` branches attached to an `if_statement`. |
| `elif_clause` | A single `elif condition: block` branch. |
| `else_opt` | An optional trailing `else: block` branch. |
| `while_statement` | A conditional repetition loop (`while condition: block`). |
| `expr` | The top-level expression non-terminal, resolving `or` boolean expressions. |
| `and_expr` | Resolves boolean `and` expressions. |
| `not_expr` | Resolves unary boolean `not` expressions. |
| `comparison` | Resolves relational comparisons (`<`, `>`, `==`, `!=`) between arithmetic expressions. |
| `comp_op` | The relational operator symbol. |
| `arith_expr` | Resolves addition (`+`) and subtraction (`-`). |
| `term` | Resolves multiplication (`*`) and division (`/`). |
| `factor` | Resolves unary arithmetic minus (`-`) negation. |
| `primary` | Atomic operands: identifiers, primitive literals, or parenthesized expressions `(expr)`. |
| `literal` | Primitive data values (`INT`, `FLOAT`, `STRING`, `BOOLEAN`). |
| `empty` | Epsilon ($\epsilon$) production representing optional constructs. |

---

## 4. Operator Precedence and Associativity

Precedence is enforced structurally through the cascading grammar rules from lowest to highest:

| Precedence | Operator | Description | Associativity | Grammar Level |
| :---: | :---: | :--- | :---: | :--- |
| **1 (Lowest)** | `or` | Logical OR | Left | `expr` |
| **2** | `and` | Logical AND | Left | `and_expr` |
| **3** | `not` | Logical NOT | Unary (Right) | `not_expr` |
| **4** | `<`, `>`, `==`, `!=` | Relational Comparisons | Non-associative | `comparison` |
| **5** | `+`, `-` | Addition, Subtraction | Left | `arith_expr` |
| **6** | `*`, `/` | Multiplication, Division | Left | `term` |
| **7** | `-` (unary) | Arithmetic Negation | Unary (Right) | `factor` |
| **8 (Highest)**| `()`, Literals, Names | Parentheses, Atomics | N/A | `primary` |

### Key Precedence Properties:
- **Parentheses override all precedence**: `LPAREN expr RPAREN` returns evaluation back to the top-level `expr`.
- **Relational operators bind tighter than boolean operators**: In `x > 5 and y < 10`, `x > 5` and `y < 10` are reduced to `comparison` before `and` is evaluated.
- **Unary minus binds tighter than binary arithmetic**: `- x * 2` is parsed as `(-x) * 2`.
- **`not` binds tighter than `and`/`or`**: `not a and b` is parsed as `(not a) and b`.

---

## 5. Indentation Semantics (INDENT & DEDENT)

In Python-like syntax, code blocks are structurally represented by matched pairs of synthetic `INDENT` and `DEDENT` tokens emitted by the lexer:

### 1. Simple Block Structure
```python
if x > 5:
    y = 20
```
Lexer token sequence:
```text
IF -> expr -> COLON -> NEWLINE -> INDENT -> IDENTIFIER(y) -> ASSIGN -> INT(20) -> NEWLINE -> DEDENT
```
The grammar parses this as:
```text
if_statement
├── IF expr COLON NEWLINE
└── block
    ├── INDENT
    ├── statement_list
    │   └── assignment_statement (y = 20 NEWLINE)
    └── DEDENT
```

### 2. If-Else Structure
```python
if x > 5:
    y = 20
else:
    y = 30
```
Lexer token sequence:
```text
IF -> expr -> COLON -> NEWLINE
INDENT -> y = 20 -> NEWLINE -> DEDENT
ELSE -> COLON -> NEWLINE
INDENT -> y = 30 -> NEWLINE -> DEDENT
```
Notice that the first block closes with `DEDENT` *before* the `ELSE` token is encountered. The grammar consumes the `if` block, finds `ELSE`, and parses the second `block`.

### 3. Nested Blocks
```python
if x > 5:
    if y > 2:
        z = 10
    x = 20
```
Lexer token sequence:
```text
IF -> expr -> COLON -> NEWLINE
INDENT
    IF -> expr -> COLON -> NEWLINE
    INDENT
        z = 10 -> NEWLINE
    DEDENT
    x = 20 -> NEWLINE
DEDENT
```
1. Outer block opens with `INDENT`.
2. Inner `if` statement opens with a second `INDENT`.
3. Inner block terminates with `DEDENT` (returning indentation from level 8 to level 4).
4. `x = 20` is parsed as the second statement of the outer `statement_list`.
5. Outer block terminates with its own `DEDENT` (returning indentation from level 4 to level 0).

---

## 6. Derivation Examples

### Example 1: Arithmetic Precedence
**Input:** `x = 10 + 20 * 5\n`

**Derivation steps:**
```text
program
=> statement_list
=> statement
=> simple_statement
=> assignment_statement
=> IDENTIFIER(x) ASSIGN expr NEWLINE
=> IDENTIFIER(x) ASSIGN and_expr NEWLINE
=> IDENTIFIER(x) ASSIGN not_expr NEWLINE
=> IDENTIFIER(x) ASSIGN comparison NEWLINE
=> IDENTIFIER(x) ASSIGN arith_expr NEWLINE
=> IDENTIFIER(x) ASSIGN arith_expr PLUS term NEWLINE
=> IDENTIFIER(x) ASSIGN term PLUS term NEWLINE
=> IDENTIFIER(x) ASSIGN factor PLUS term NEWLINE
=> IDENTIFIER(x) ASSIGN primary PLUS term NEWLINE
=> IDENTIFIER(x) ASSIGN literal(10) PLUS (term MULTIPLY factor) NEWLINE
=> IDENTIFIER(x) ASSIGN 10 PLUS (factor MULTIPLY factor) NEWLINE
=> IDENTIFIER(x) ASSIGN 10 PLUS (primary MULTIPLY primary) NEWLINE
=> IDENTIFIER(x) ASSIGN 10 PLUS (literal(20) MULTIPLY literal(5)) NEWLINE
=> x = 10 + 20 * 5 \n
```

---

### Example 2: Simple Conditional Statement
**Input:**
```python
if x > 5:
    y = 20
```

**Derivation steps:**
```text
program
=> statement_list
=> statement
=> compound_statement
=> if_statement
=> IF expr COLON NEWLINE block elif_list else_opt
=> IF (comparison: arith_expr GREATER arith_expr) COLON NEWLINE block empty empty
=> IF (IDENTIFIER(x) GREATER literal(5)) COLON NEWLINE (INDENT statement_list DEDENT)
=> IF x > 5 : NEWLINE INDENT (assignment_statement: y = 20 NEWLINE) DEDENT
```

---

### Example 3: Nested Conditional Blocks
**Input:**
```python
if x > 5:
    if y > 2:
        z = 10
    x = 20
```

**Derivation steps:**
```text
program
=> statement_list
=> statement
=> compound_statement
=> if_statement
=> IF (x > 5) COLON NEWLINE block elif_list else_opt
=> IF (x > 5) COLON NEWLINE (INDENT statement_list DEDENT)
=> IF (x > 5) COLON NEWLINE INDENT
      statement_list
      statement (x = 20 NEWLINE)
   DEDENT
=> IF (x > 5) COLON NEWLINE INDENT
      statement (compound: if y > 2: INDENT z = 10 NEWLINE DEDENT)
      statement (simple: x = 20 NEWLINE)
   DEDENT
```

---

## 7. Grammar Construct to AST Node Mapping

When parser actions are implemented in Phase 3C, each grammar production maps directly to an AST node defined in [`parser/ast_nodes.py`](parser/ast_nodes.py):

| Grammar Production Rule | AST Class Instantiated | Node Fields |
| :--- | :--- | :--- |
| `program -> statement_list` | `ProgramNode` | `statements=[...]` |
| `block -> INDENT statement_list DEDENT` | `BlockNode` | `statements=[...]` |
| `assignment_statement -> IDENTIFIER ASSIGN expr NEWLINE` | `AssignmentNode` | `target=IdentifierNode(name)`, `value=expr` |
| `primary -> IDENTIFIER` | `IdentifierNode` | `name=str` |
| `literal -> INT \| FLOAT \| STRING \| BOOLEAN` | `LiteralNode` | `value=val`, `type_name=type` |
| `expr -> expr OR and_expr` | `BinaryOpNode` | `operator='or'`, `left=expr`, `right=and_expr` |
| `and_expr -> and_expr AND not_expr` | `BinaryOpNode` | `operator='and'`, `left=and_expr`, `right=not_expr` |
| `comparison -> arith_expr comp_op arith_expr` | `BinaryOpNode` | `operator=op`, `left=arith1`, `right=arith2` |
| `arith_expr -> arith_expr PLUS term` | `BinaryOpNode` | `operator='+'`, `left=arith`, `right=term` |
| `arith_expr -> arith_expr MINUS term` | `BinaryOpNode` | `operator='-'`, `left=arith`, `right=term` |
| `term -> term MULTIPLY factor` | `BinaryOpNode` | `operator='*'`, `left=term`, `right=factor` |
| `term -> term DIVIDE factor` | `BinaryOpNode` | `operator='/'`, `left=term`, `right=factor` |
| `not_expr -> NOT not_expr` | `UnaryOpNode` | `operator='not'`, `operand=not_expr` |
| `factor -> MINUS factor` | `UnaryOpNode` | `operator='-'`, `operand=factor` |
| `primary -> LPAREN expr RPAREN` | *(Transparent pass-through)* | Returns the enclosed `expr` node |
| `if_statement -> IF expr COLON NEWLINE block elif_list else_opt` | `IfNode` | `condition=expr`, `then_block=block`, `elif_clauses=[...]`, `else_block=...` |
| `elif_clause -> ELIF expr COLON NEWLINE block` | `ElifNode` | `condition=expr`, `then_block=block` |
| `while_statement -> WHILE expr COLON NEWLINE block` | `WhileNode` | `condition=expr`, `body=block` |

---

## 8. Verification & Consistency Audit

1. **Tokens Verification**: All terminal token names (`IF`, `ELIF`, `ELSE`, `WHILE`, `AND`, `OR`, `NOT`, `INT`, `FLOAT`, `STRING`, `BOOLEAN`, `IDENTIFIER`, `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `ASSIGN`, `EQUALS`, `NOT_EQUALS`, `LESS`, `GREATER`, `COLON`, `LPAREN`, `RPAREN`, `NEWLINE`, `INDENT`, `DEDENT`) match [`lexer/lexer.py`](lexer/lexer.py) `tokens` tuple with 100% fidelity.
2. **AST Verification**: All target AST node classes (`ProgramNode`, `BlockNode`, `AssignmentNode`, `IdentifierNode`, `LiteralNode`, `BinaryOpNode`, `UnaryOpNode`, `ElifNode`, `IfNode`, `WhileNode`) match [`parser/ast_nodes.py`](parser/ast_nodes.py) signatures with 100% fidelity.
3. **Ambiguity Prevention**: Operator precedence is strictly stratified via cascading grammar levels, preventing shift/reduce expression ambiguities in LR/LALR(1) parser generators such as PLY `yacc`.

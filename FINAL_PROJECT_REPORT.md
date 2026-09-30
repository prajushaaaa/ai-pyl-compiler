# PROJECT REPORT

## AI-Powered Compiler & Diagnostic Assistant for a Python-Like Language (`.pyl`)

---

## CHAPTER 1 — INTRODUCTION

### 1.1 Background
Compiler design is a foundational pillar of computer science and software engineering, dealing with the formal transformation of human-readable source code into intermediate representations and machine-executable forms. Historically, the front-end phases of a compiler—lexical analysis, syntactic analysis, and semantic analysis—have adhered to rigorous, deterministic mathematical models, such as regular expressions, finite automata, context-free grammars (CFGs), and LALR(1) shift-reduce parsing algorithms.

In pedagogical environments, understanding how source tokens are systematically organized into an Abstract Syntax Tree (AST), validated against type and scoping rules, and flattened into an intermediate representation like Three-Address Code (TAC) is critical for students. At the same time, recent advances in Artificial Intelligence (AI) and Large Language Models (LLMs) have introduced new possibilities for automated software assistance. However, compilers demand formal, deterministic validation rules that generative models cannot provide natively. This project bridges this gap by maintaining an authoritative, deterministic compiler pipeline while utilizing AI strictly as a decoupled, advisory diagnostic assistant.

### 1.2 Problem Statement
Traditional compiler diagnostic messages are often terse, heavily technical, and difficult for beginner programmers to interpret. A typical error such as `SyntaxError: unexpected token` or `SemanticError: incompatible operands` identifies that a formal rule was violated, but does not provide adequate pedagogical context regarding *why* the rule exists, *how* the program structure led to the rejection, or *what* concrete remediation is required.

Conversely, attempting to replace traditional compilers with generative AI models introduces severe vulnerabilities: LLMs suffer from non-deterministic hallucinations, cannot guarantee grammatical or type-theoretic validity, frequently invent non-existent syntax, and cannot reliably verify code correctness. Therefore, a hybrid architectural solution is necessary: a system where a strict, deterministic compiler acts as the sole gatekeeper of validity, and an isolated, constrained AI diagnostic engine activates exclusively upon compilation failure to explain compiler-verified errors.

### 1.3 Motivation
The primary motivation of this project is to develop an educational compiler for a Python-like language (`.pyl`) that exemplifies classical compiler construction principles while demonstrating the safe, disciplined integration of AI. By designing a complete front-end and intermediate code generator from scratch using PLY (Python Lex-Yacc), students and developers can observe each stage of compilation:
- Handling indentation-based syntax without curly braces or explicit block delimiters.
- Enforcing static typing and lexical scope boundaries on a Python-like syntax.
- Lowering complex hierarchical syntax trees into linear Three-Address Code instructions.
- Extracting localized source context (including line numbers, gutters, and caret pointers) upon compilation failure.
- Routing structured error context into an LLM assistant strictly bounded by the language grammar to generate clear, pedagogical remediation and suggested fixes.

### 1.4 Objectives
The concrete, implemented objectives of this project are:
1. **Design and Implement a Lexical Analyzer:** Construct a token scanner using `ply.lex` equipped with an explicit indentation stack (`IndentationLexer`) to manage indentation levels and emit synthetic `INDENT` and `DEDENT` tokens.
2. **Implement an LALR(1) Syntactic Parser:** Build a shift-reduce parser using `ply.yacc` that enforces a formal Context-Free Grammar, resolves operator precedence structurally, and constructs an explicit Abstract Syntax Tree (AST).
3. **Develop a Scoped Semantic Analyzer:** Construct a hierarchical symbol table managing lexical block scopes, enforcing declaration-before-use semantics, and performing static type checking across expressions and control-flow conditions.
4. **Implement an Intermediate Representation (IR) Generator:** Lower validated ASTs into linear Three-Address Code (TAC) instructions with synthetic temporaries and jump labels.
5. **Construct a Contextual Diagnostic Engine:** Implement an automated error-handling engine that captures exact line/column coordinates and formats surrounding source code lines with a visual caret (`^`) pointer.
6. **Integrate an Advisory AI Diagnostic Assistant:** Implement an abstract provider interface supporting both real-time Groq LLM queries (`openai/gpt-oss-120b`) and an offline, deterministic mock provider (`MockAIProvider`) that formats remediation into four clear sections (*Explanation*, *Cause*, *Suggested Fix*, *Corrected Code*).
7. **Deliver a Unified Command-Line Interface (CLI):** Provide a cohesive CLI executable (`main.py`) with stage-by-stage progression indicators and CLI flags (`--mock-ai`, `--no-ai`).

### 1.5 Scope
The scope of this project is strictly defined to ensure academic rigor and architectural completeness:
- **Scope Boundary:** The `.pyl` language is a pedagogical source language whose compiler lowers validated programs to Three-Address Code (TAC). It does not generate target machine code or execute the resulting TAC instructions.
- **AI Role:** The AI assistant is diagnostic-only. It has no authority over compiler validity, cannot replace the compiler, cannot alter the AST or TAC, and never automatically modifies source files on disk. Any corrected code provided by the assistant is presented solely as a suggestion.

---

## CHAPTER 2 — TECHNOLOGY & LANGUAGE SPECIFICATION

### 2.1 Technology Stack
The `.pyl` compiler relies exclusively on a minimal, verified technology stack:
- **Implementation Language:** Python 3.10+ (Standard Library: `sys`, `os`, `re`, `dataclasses`, `abc`, `unittest`).
- **Lexer & Parser Framework:** PLY (Python Lex-Yacc, version 3.11), providing `ply.lex` for regular expression token matching and `ply.yacc` for LALR(1) parsing.
- **Terminal Presentation:** `rich` (used for formatted terminal token table inspection in the lexer module).
- **AI Cloud Client:** `groq` (official Groq SDK client used by `GroqAIProvider` for querying `openai/gpt-oss-120b`).
- **Testing Framework:** Python standard library `unittest` module and standalone test suites.

### 2.2 `.pyl` Language Overview
`.pyl` (Python-Like) is a statically typed pedagogical language whose syntax is heavily inspired by Python. Unlike full standard Python, `.pyl` removes dynamic runtime overhead and enforces strict compile-time type verification, explicit variable initialization prior to reference, and lexical block scoping governed by indentation.

### 2.3 Data Types
The language supports four fundamental primitive types:
1. `int`: Integer literals consisting of contiguous digit sequences (e.g., `0`, `10`, `-42`).
2. `float`: Real numbers denoted with a decimal point (e.g., `0.5`, `3.14`, `10.0`).
3. `str`: String literals bounded by single or double quotes (e.g., `"compiler"`, `'pyl'`).
4. `bool`: Boolean literals represented strictly by the keywords `True` and `False`.

### 2.4 Variables and Scope
- **Declaration-Before-Use:** A variable is introduced into the symbol table via an assignment statement (`target = expr`). Reading a variable prior to assignment triggers a compile-time semantic error.
- **Static Typing via Inference:** The variable adopts the static type of its assigned expression.
- **Lexical Block Scoping:** Entering an indented block creates a new, nested lexical scope. Variables defined in outer scopes are accessible inside inner scopes. A variable defined within an inner block with the same identifier as an outer variable creates a local binding that shadows the outer variable.

### 2.5 Operators and Precedence
The language specifies arithmetic, relational, and logical operators. Precedence is enforced structurally within the grammar:

| Precedence Level | Operators | Description | Associativity |
| :--- | :--- | :--- | :--- |
| **8 (Highest)** | `( )`, Identifiers, Literals | Grouping and Atomic Primaries | N/A |
| **7** | `-` (prefix) | Unary Arithmetic Negation | Right |
| **6** | `*`, `/` | Multiplication, Division | Left |
| **5** | `+`, `-` | Addition, Subtraction | Left |
| **4** | `<`, `>`, `==`, `!=` | Relational Comparisons | Non-associative |
| **3** | `not` | Logical Negation | Right |
| **2** | `and` | Logical Conjunction | Left |
| **1 (Lowest)** | `or` | Logical Disjunction | Left |

### 2.6 Control Flow
- **Conditional Branches:** Supported via `if`, zero or more `elif` clauses, and an optional `else` clause. The branch header must end with a colon (`:`) followed by a newline and an indented block.
- **Loops:** Supported via `while condition:` followed by an indented block.
- **Strict Boolean Condition Rule:** All conditions for `if`, `elif`, and `while` must evaluate strictly to `bool`. No truthiness coercion (e.g., treating integer `0` as `False` or non-empty strings as `True`) is permitted.

### 2.7 Supported Features Summary
- Primitive static types (`int`, `float`, `str`, `bool`).
- Explicit variable assignments with scope tracking.
- Binary and unary arithmetic operations.
- Automatic integer-to-float promotion in mixed arithmetic.
- String concatenation using `+` strictly between `str` operands.
- Relational comparisons (`<`, `>`, `==`, `!=`).
- Boolean logic (`and`, `or`, `not`) strictly on `bool` operands.
- Parenthesized expression grouping.
- Indentation-based block structuring (`INDENT`/`DEDENT`).
- Full conditional structures (`if`, `elif`, `else`).
- Iteration constructs (`while`).
- Nested control-flow blocks.
- Single-line comments (`#`).
- Three-Address Code intermediate representation.

### 2.8 Unsupported Features
To maintain architectural clarity and avoid runtime complexity, the following features are deliberately excluded from `.pyl`:
- Functions and lambdas (`def`, `lambda`, `return`).
- Object-oriented classes, instances, and inheritance (`class`).
- Module imports and packaging (`import`, `from`).
- Composite collections (`list`, `dict`, `tuple`, `set`).
- Exception handling mechanisms (`try`, `except`, `finally`, `raise`).
- Implicit type coercion / truthiness checks on non-boolean types.
- Target machine assembly generation or execution environments.

---

## CHAPTER 3 — SYSTEM DESIGN

### 3.1 Overall System Architecture
The `.pyl` compiler architecture cleanly decouples the deterministic translation pipeline from the advisory diagnostic engine.

```
                                +---------------------------+
                                |     Source Code (.pyl)    |
                                +---------------------------+
                                              |
                                              v
                                +---------------------------+
                                |  Stage 1: Lexical Scanner |
                                |    (IndentationLexer)     |
                                +---------------------------+
                                              |
                                         Token Stream
                                              |
                                              v
                                +---------------------------+
                                |  Stage 2: LALR(1) Parser  |
                                |     (PLY Parser & AST)    |
                                +---------------------------+
                                              |
                                    Abstract Syntax Tree
                                              |
                                              v
                                +---------------------------+
                                | Stage 3: Semantic Analyzer|
                                |   (Scoped Symbol Table)   |
                                +---------------------------+
                                              |
                                       Validated AST
                                              |
                                              v
                                +---------------------------+
                                | Stage 4: TAC IR Generator |
                                +---------------------------+
                                              |
                                              v
                                +---------------------------+
                                |    Three-Address Code     |
                                |   (Compilation Success)   |
                                +---------------------------+
                                              |
                       [Failure at any stage 1, 2, or 3]
                                              |
                                              v
                                +---------------------------+
                                |    Diagnostic Engine      |
                                | (ContextExtractor/Handler)|
                                +---------------------------+
                                              |
                                       Structured Prompt
                                              |
                                              v
                                +---------------------------+
                                |   AI Diagnostic Engine    |
                                | (GroqAIProvider / MockAI) |
                                +---------------------------+
                                              |
                                              v
                                +---------------------------+
                                | Remediation Output to CLI |
                                +---------------------------+
```

[FIGURE: Overall Compiler Architecture]

### 3.2 Compiler Pipeline
The compiler executes strictly in four sequential stages:
1. **Lexical Analysis:** Scans the raw character stream, translates characters into typed tokens, strips comments, and injects synthetic `INDENT`/`DEDENT` tokens.
2. **Syntactic Analysis:** Validates token sequences against grammar rules and constructs an Abstract Syntax Tree.
3. **Semantic Analysis:** Walks the AST, manages scope entries/exits, verifies declaration-before-use, checks type compatibility, and validates boolean conditions.
4. **Intermediate Code Generation:** Traverses the validated AST and emits linear Three-Address Code instructions.

### 3.3 Module Architecture
The codebase is structured into modular Python packages:
- `lexer/`: Contains token definitions, regex rules, coordinate tracking, and the `IndentationLexer` class.
- `parser/`: Contains AST node class definitions (`ast_nodes.py`) and grammar reduction rules (`parser.py`).
- `semantics/`: Contains the `Scope` and `SymbolTable` abstractions (`symbol_table.py`) and the AST visitor type checker (`semantic_analyzer.py`).
- `codegen/`: Contains the `TACInstruction` data model and linear code generator (`tac_generator.py`).
- `diagnostics/`: Contains context extraction (`context_extractor.py`), diagnostic aggregation (`error_handler.py`), and AI provider implementations (`ai_diagnostic.py`).
- `main.py`: Orchestrates CLI argument parsing, stage execution, and output formatting.

### 3.4 AI Diagnostic Architecture
The AI subsystem is organized around the Strategy design pattern:
- **`AIProvider` (Abstract Base Class):** Defines the abstract method `diagnose(prompt: str) -> DiagnosticResponse`.
- **`GroqAIProvider`:** Implements real-time cloud inference via the official Groq client SDK.
- **`MockAIProvider`:** Implements deterministic, pattern-based offline diagnostic generation.
- **`PromptBuilder`:** Converts compiler-generated `Diagnostic` instances into structured prompts containing strict `.pyl` constraints.
- **`DiagnosticResponse`:** Encapsulates the four-part structured output (*Explanation*, *Cause*, *Suggested Fix*, *Corrected Code*).

[FIGURE: AI Diagnostic Flow]

### 3.5 Error Handling Flow
When an unrecoverable error occurs in any compiler stage:
1. The compiler halts immediately; subsequent stages are bypassed.
2. The exception or error dictionary provides the error coordinates (`line`, `column`) and message.
3. `ContextExtractor` reads the source code and extracts the relevant lines with a column-aligned caret.
4. `DiagnosticErrorHandler` formats a structured text block with headers, coordinates, and code context.
5. If AI diagnostics are enabled, the diagnostic is sent to the configured `AIProvider`.
6. The formatted diagnostic and AI suggested fixes are written to standard output, and the process exits with status code `1`.

### 3.6 CLI Workflow
The driver script `main.py` manages input arguments:
- Checks if a target `.pyl` file is specified.
- Configures the AI provider based on flags: `--mock-ai` selects `MockAIProvider`, `--no-ai` installs a disabled provider, and the default without flags selects `GroqAIProvider` (requiring `GROQ_API_KEY`).
- Reads the input file and invokes `compile_source()`.
- Prints progress indicators (`[1/4]`, `[2/4]`, `[3/4]`, `[4/4]`).
- On success: Prints `COMPILATION SUCCESS` followed by the generated Three-Address Code, exiting with code `0`.
- On error: Prints the failure status, diagnostic block, and AI suggested remediation, exiting with code `1`.

---

## CHAPTER 4 — IMPLEMENTATION

### 4.1 Lexical Analysis
Implemented in `lexer/lexer.py`, lexical analysis converts source text into tokens. Reserved words are mapped using a dictionary:
```python
reserved = {
    'if': 'IF', 'elif': 'ELIF', 'else': 'ELSE', 'while': 'WHILE',
    'and': 'AND', 'or': 'OR', 'not': 'NOT',
    'True': 'BOOLEAN', 'False': 'BOOLEAN',
}
```
Tokens are matched using PLY regex conventions:
- Single-character operators (`+`, `-`, `*`, `/`, `:`, `(`, `)`) use standard string patterns.
- Multi-character operators (`==`, `!=`) precede single-character operators (`=`) to ensure correct prefix matching.
- Comments matching `\#[^\r\n]*` are ignored by `t_COMMENT`.
- Coordinate tracking uses a custom `find_column()` helper that counts the character offset from the preceding newline character.

### 4.2 Indentation Handling
Because PLY does not natively manage Python-style whitespace blocks, the project wraps the raw scanner in an `IndentationLexer` class:
1. The raw token stream is partitioned into logical lines ending in `NEWLINE`. Blank or comment-only lines are eliminated.
2. Leading whitespace is measured using 4-space tab stops via `compute_indent()`.
3. An internal stack `indentation_stack` (initialized to `[0]`) records active column offsets.
4. When indentation increases after a line ending in a `COLON`, the new level is pushed onto the stack and an `INDENT` token is emitted. An indentation increase without a preceding colon triggers a lexical error.
5. When indentation decreases, the lexer verifies that the new level exists in `indentation_stack`. It pops levels until the top matches the new indentation, emitting a `DEDENT` token for each popped level. If the level does not match an existing stack entry, an indentation mismatch error is recorded.
6. At EOF, synthetic `DEDENT` tokens are emitted until the stack returns to level `0`.

[FIGURE: Lexer Indentation Stack]

### 4.3 Syntax Analysis
Implemented in `parser/parser.py`, syntactic analysis uses PLY's LALR(1) parser generator. The grammar is defined using BNF-style docstrings in parser functions:
- Statement lists are parsed via left-recursive rules (`statement_list : statement_list statement | statement`).
- The parser handles both simple statements (assignments terminated by `NEWLINE`) and compound statements (`if` and `while` headers followed by an indented `block`).
- An indented `block` is defined as `INDENT statement_list DEDENT`.
- If an invalid token is encountered, `p_error(p)` creates a `ParseError` containing the token's value, line number, and column offset.

### 4.4 AST Construction
Implemented in `parser/ast_nodes.py`, the parser constructs explicit syntax tree nodes rather than evaluating expressions immediately:
- Node base class: `ASTNode` provides `lineno`, `column`, `get_children()`, and tree formatting methods.
- Structural nodes: `ProgramNode` and `BlockNode`.
- Leaf nodes: `IdentifierNode` and `LiteralNode`.
- Operation nodes: `AssignmentNode`, `BinaryOpNode`, and `UnaryOpNode`.
- Control flow nodes: `IfNode`, `ElifNode`, and `WhileNode`.

All nodes preserve line number and column coordinate attributes for downstream error reporting.

[FIGURE: AST Example]

### 4.5 Semantic Analysis
Implemented in `semantics/semantic_analyzer.py`, the `SemanticAnalyzer` uses the visitor pattern to traverse the AST:
- **Type Checking:** Every visited expression returns its evaluated type (`int`, `float`, `str`, or `bool`).
- **Widening:** In arithmetic expressions (`+`, `-`, `*`, `/`), if one operand is `int` and the other is `float`, the result type is inferred as `float`.
- **String Handling:** Operator `+` allows `str + str -> str`. Any attempt to combine `str` with numeric or boolean types raises a `SemanticError`.
- **Condition Validation:** `visit_IfNode`, `visit_ElifNode`, and `visit_WhileNode` evaluate their condition sub-trees; if the inferred type is not `"bool"`, compilation is halted with an explicit `SemanticError`.

### 4.6 Symbol Table and Scope Management
Implemented in `semantics/symbol_table.py`, lexical scoping is managed through the `SymbolTable` class:
- A `scope_stack` tracks active lexical scopes from global (`level 0`) to deeply nested blocks.
- `enter_scope()` creates a child `Scope` object linked to its parent.
- `exit_scope()` pops the active scope when a block completes.
- In `visit_AssignmentNode`:
  ```python
  existing_symbol = self.symbol_table.lookup_current_scope(target_name)
  if existing_symbol is not None:
      existing_symbol.type = val_type
  else:
      self.symbol_table.define(name=target_name, type_name=val_type, line=line, column=column)
  ```
  This logic ensures that assignments inside blocks define local bindings that shadow outer variables without overwriting their outer types.

[FIGURE: Semantic Analysis / Symbol Table]

### 4.7 Three-Address Code Generation
Implemented in `codegen/tac_generator.py`, the `TACGenerator` lowers the AST into a list of `TACInstruction` objects:
- Temporaries are sequentially numbered: `t1 = self.new_temp()`.
- Jump labels are sequentially numbered: `L1 = self.new_label()`.
- **Arithmetic Example:**
  For the input program:
  ```python
  x = 10 + 20 * 5
  ```
  The generator evaluates the binary multiplication first according to AST precedence, then the addition, emitting:
  ```text
  t1 = 20 * 5
  t2 = 10 + t1
  x = t2
  ```
- **Control Flow Example:**
  For an `if-else` construct, `if_false` evaluates the condition temporary and branches to the `else` label, while the end of the `then` block emits an unconditional `goto` skipping the `else` body.

[FIGURE: TAC Generation]

### 4.8 Diagnostic Engine
Implemented in `diagnostics/context_extractor.py` and `diagnostics/error_handler.py`:
- `extract_source_context()` isolates a 2-line window surrounding the offending line, adds formatted right-aligned line numbers in a gutter, and computes the exact indentation needed for the caret pointer (`^`).
- `DiagnosticErrorHandler` formats the complete message into a standardized console box with header, file, coordinates, error text, and source context.

### 4.9 AI Diagnostic Assistant
Implemented in `diagnostics/ai_diagnostic.py`:
- `PromptBuilder` formats the compiler diagnostic and embeds the complete language boundary specification into the LLM system prompt, warning the model against suggesting full Python features like functions or imports.
- The assistant produces a four-part response:
  1. **Explanation:** Clear description of the syntax or type violation.
  2. **Cause:** Formal explanation of the `.pyl` rule that was violated.
  3. **Suggested Fix:** Concrete steps to correct the error.
  4. **Corrected Code:** An illustrative `.pyl` snippet demonstrating valid syntax.
- **Safety Boundaries:** The AI does not determine compiler validity, does not replace the compiler, does not modify source files on disk, and presents corrected code strictly as a suggestion. The deterministic compiler remains the sole authority.

### 4.10 Groq Integration
`GroqAIProvider` manages live LLM requests:
- Reads `GROQ_API_KEY` from the environment.
- Configures model `openai/gpt-oss-120b` with a low temperature (0.2) to encourage more consistent diagnostic responses.
- Uses regex patterns in `_parse_groq_response()` to extract the four structured sections.
- If an API communication failure occurs, any occurrence of the secret API key in exception strings is redacted with `[REDACTED]` before reporting.

### 4.11 Mock AI Provider
`MockAIProvider` enables full offline testing without API keys or internet access:
- Inspects compiler diagnostic messages for specific patterns (`"undefined variable"`, `"cannot be applied to operands of type"`, `"boolean operator"`, `"condition must"`, `"syntax error"`, `"lexical error"`).
- Returns deterministic, pre-formulated four-part remediation text matching the exact behavior of the live model.

### 4.12 CLI Implementation
The command-line interface in `main.py` manages execution:
- Parses sys.argv for file paths and flags (`--mock-ai`, `--no-ai`).
- Directs output through a configurable writer callback (enabling seamless capture during tests).
- Returns explicit exit codes: `0` for successful compilation, `1` for any compiler failure.

---

## CHAPTER 5 — TESTING AND RESULTS

### 5.1 Testing Strategy
The testing methodology enforces strict phase-by-phase validation:
- **Unit & Pipeline Integration Tests:** Every phase from lexical scanning to TAC generation is verified with automated tests.
- **Offline Determinism:** All test suites run completely offline using deterministic assertions or `MockAIProvider`.
- **Negative Testing:** Invalid programs across lexical, syntactic, and semantic categories verify that errors are caught at the appropriate stage.

### 5.2 Frontend Tests
- **File:** `tests/test_frontend.py`
- **Scope:** Verifies the complete front-end pipeline (Source Code $\rightarrow$ Lexer Tokens $\rightarrow$ LALR(1) Parser $\rightarrow$ AST Nodes).
- **Execution & Result:** Executed directly via `python tests/test_frontend.py`. Passed both basic and nested block tests successfully (**PASS**).

### 5.3 TAC Integration Tests
- **File:** `tests/test_tac_integration.py`
- **Scope:** Verifies the full pipeline through TAC generation across 8 distinct scenarios, including arithmetic precedence, branching, loops, nested control flow, and error halts.
- **Execution & Result:** Executed directly via `python tests/test_tac_integration.py`. All 8 integration tests passed (**8/8 PASS**).

### 5.4 Diagnostic Integration Tests
- **File:** `tests/test_diagnostic_integration.py`
- **Scope:** Verifies that real compiler exceptions (lexical, syntax, semantic) are caught, wrapped into structured `Diagnostic` objects with accurate caret pointers, and transformed into valid prompts.
- **Execution & Result:** Executed directly via `python tests/test_diagnostic_integration.py`. All 10 diagnostic scenarios passed (**10/10 PASS**).

### 5.5 AI Provider Tests
- **File:** `diagnostics/ai_diagnostic.py`
- **Scope:** Verifies prompt building, `DiagnosticResponse` formatting, `MockAIProvider` pattern matching, and `GroqAIProvider` configuration. Contains an isolated live test that warns gracefully if `GROQ_API_KEY` is unset.
- **Execution & Result:** Executed directly via `python diagnostics/ai_diagnostic.py`. All 6 deterministic tests passed (**6 PASS**).

### 5.6 CLI Tests
- **File:** `tests/test_cli.py`
- **Scope:** Automated regression suite verifying CLI invocation, argument errors, missing files, valid programs, and error halts.
- **Execution & Result:** Executed via `python tests/test_cli.py`. All 8 tests passed (**8/8 PASS**):
  - Test 1: No arguments provided $\rightarrow$ Usage message & exit code 1.
  - Test 2: Missing source file $\rightarrow$ File not found & exit code 1.
  - Test 3: Valid program $\rightarrow$ 4/4 PASS & exit code 0.
  - Test 4: Control flow $\rightarrow$ Valid TAC branch emission & exit code 0.
  - Test 5: Lexical error $\rightarrow$ Stage 1 FAIL, caret context, exit code 1.
  - Test 6: Indentation error $\rightarrow$ Stage 1 FAIL, caret context, exit code 1.
  - Test 7: Semantic error $\rightarrow$ Stage 3 FAIL, caret context, exit code 1.
  - Test 8: AI failure fallback $\rightarrow$ Compiler preserves authoritative diagnostic without crashing.

### 5.7 End-to-End Tests
- **File:** `tests/test_end_to_end.py`
- **Scope:** Full validation suite exercising valid programs, comprehensive invalid program rejections, and AI diagnostic integration.
- **Execution & Result:** Executed via `python tests/test_end_to_end.py`. All 19 tests passed (**19/19 PASS**):
  - 10 valid program matrix tests (arithmetic, precedence, parentheses, booleans, conditionals, loops, nested control flow, reassignments).
  - 8 invalid program rejection tests (undefined variable, type mismatch, invalid boolean op, non-boolean condition, indentation error, invalid character, syntax error, invalid comparison).
  - 1 end-to-end AI diagnostic integration test.

### 5.8 Demonstration Programs
Five purpose-built demonstration programs in `tests/demo/` were created and validated in Phase 8B:
1. `demo_complete.pyl`: Demonstrates assignments, precedence, float arithmetic, boolean logic, `if`/`elif`/`else`, and a `while` loop containing nested `if`/`else` branches. Compiled with `python main.py tests/demo/demo_complete.pyl --no-ai`. Result: Stages 1 through 4 passed; generated complete Three-Address Code (**PASS**).
2. `demo_type_error.pyl`: Demonstrates an `int + str` type error (`count + " items"`). Compiled with `python main.py tests/demo/demo_type_error.pyl --mock-ai`. Result: Stages 1 and 2 passed; Stage 3 failed with `SemanticError`; delivered structured AI explanation and suggested fix (**PASS**).
3. `demo_undefined_variable.pyl`: Demonstrates an uninitialized variable reference (`total = x + 10`). Compiled with `--mock-ai`. Result: Stage 3 failed with `Undefined variable 'x'` (**PASS**).
4. `demo_syntax_error.pyl`: Demonstrates an operator sequence syntax error (`x = 10 + * 20`). Compiled with `--mock-ai`. Result: Stage 1 passed; Stage 2 failed with `SyntaxError at line 2, Column 10: Unexpected token '*'` (**PASS**).
5. `demo_indentation_error.pyl`: Demonstrates an indentation level mismatch (level 6 instead of 4). Compiled with `--mock-ai`. Result: Stage 1 failed with `Indentation error` (**PASS**).

All demonstration programs behaved exactly as intended.

### 5.9 Sample Outputs

#### 1. Successful Compilation Output
```text
============================================================
.pyl COMPILER
============================================================

File: tests/valid/example.pyl

[1/4] Lexical Analysis ........ PASS
[2/4] Parsing .................. PASS
[3/4] Semantic Analysis ........ PASS
[4/4] TAC Generation ........... PASS

============================================================
COMPILATION SUCCESS
============================================================

Three Address Code:
----------------------------------------
t1 = 20 * 5
t2 = 10 + t1
x = t2
----------------------------------------
```
[SCREENSHOT: Successful Compilation]

#### 2. Semantic Error with AI Diagnostic Remediation
For source code containing a type mismatch:
```python
x = 10
message = x + "items"
```
The semantic analysis stage rejects the `int + str` operation. The compiler halts at Stage 3, outputs the structured diagnostic with visual caret, and produces the AI diagnostic explanation and suggested fix:
```text
============================================================
.pyl COMPILER
============================================================

File: tests/invalid/cli_semantic_error.pyl

[1/4] Lexical Analysis ........ PASS
[2/4] Parsing .................. PASS
[3/4] Semantic Analysis ........ FAIL

============================================================
SEMANTIC ERROR
============================================================
File: tests/invalid/cli_semantic_error.pyl
Line: 2, Column: 13

Message:
Operator '+' cannot be applied to operands of type 'int' and 'str'

Source:
 1 | x = 10
 2 | message = x + "items"
   |             ^

============================================================

AI Diagnostic:
Explanation:
An operator was applied to operands with incompatible types (int + str). The .pyl language does not allow mixing integers and strings in arithmetic or concatenation operations.

Cause:
The .pyl language enforces strict static typing and only allows compatible operand combinations. String concatenation with '+' requires both operands to be of type 'str', but an 'int' and a 'str' were provided.

Suggested Fix:
Ensure both operands have compatible string types. Changing 'x' to a string makes the expression valid.

Corrected Code:
x = "10"
message = x + "items"
```
[SCREENSHOT: Semantic Error + AI Diagnostic]

#### 3. Syntax Error Output
For source code containing an unexpected operator token:
```python
x = 10 + * 20
```
Output:
```text
============================================================
.pyl COMPILER
============================================================

File: tests/demo/demo_syntax_error.pyl

[1/4] Lexical Analysis ........ PASS
[2/4] Parsing .................. FAIL

============================================================
SYNTAX ERROR
============================================================
File: tests/demo/demo_syntax_error.pyl
Line: 2, Column: 10

Message:
SyntaxError at line 2, Column 10: Unexpected token '*' (type: MULTIPLY)

Source:
 1 | # Demonstration of parser syntax error (unexpected operator sequence)
 2 | x = 10 + * 20
   |          ^

============================================================
```
[SCREENSHOT: Syntax Error]

#### 4. Indentation Error Output
For source code containing unaligned block indentation:
```python
if True:
    x = 10
      y = 20
```
Output:
```text
============================================================
.pyl COMPILER
============================================================

File: tests/demo/demo_indentation_error.pyl

[1/4] Lexical Analysis ........ FAIL

============================================================
LEXICAL ERROR
============================================================
File: tests/demo/demo_indentation_error.pyl
Line: 4, Column: 7

Message:
Indentation error: indentation level 6 does not match a previously established indentation level

Source:
 2 | if True:
 3 |     x = 10
 4 |       y = 20
   |       ^

============================================================
```
[SCREENSHOT: Indentation Error]

### 5.10 Overall Results
Across all verification phases:
- **Pipeline Correctness:** The compiler pipeline systematically processes valid `.pyl` programs from raw source code to verified Three-Address Code.
- **Gatekeeping Accuracy:** Errors across all three front-end stages (lexical, syntactic, semantic) are caught deterministically, preventing invalid ASTs from reaching TAC generation.
- **Diagnostic Precision:** Coordinate extraction and caret positioning accurately identify error locations across single-line and multi-line test programs.
- **AI Decoupling:** The AI diagnostic assistant safely explains compiler errors and provides suggested fixes without risking compiler correctness or mutating files on disk.

---

## CHAPTER 6 — LIMITATIONS AND FUTURE SCOPE

### 6.1 Limitations
The current implementation adheres strictly to its design scope and carries the following inherent limitations:
1. **Absence of User-Defined Functions:** The `.pyl` language does not support `def`, parameters, return values, or function call frames.
2. **Exclusion of Composite Data Structures:** Arrays, lists, dictionaries, and tuples are unsupported.
3. **No Machine Code Generation:** The compiler terminates at Three-Address Code; it does not perform register allocation or target binary compilation.
4. **Single-File Compilation Unit:** The compiler processes one `.pyl` source file per execution; multi-module linking is not supported.
5. **External API Dependency for Live Mode:** Live AI diagnostic generation requires network connectivity and a valid Groq API key (though offline deterministic fallback is fully supported via `--mock-ai`).

### 6.2 Future Scope
The modular architecture of the `.pyl` compiler allows for several natural extensions:
1. **Subroutines and Call-Stack IR:** Extending the grammar and symbol table to support functions (`def`), local call-frame allocations, and Three-Address Code call conventions (`param`, `call`, `return`).
2. **Collection Types:** Introducing homogeneous arrays with static size checking and indexed dereferencing in TAC.
3. **Intermediate Representation Optimization:** Implementing an optimization phase on the Three-Address Code representation, including constant folding, dead code elimination, and basic block graph analysis.
4. **Machine Code Emission:** Building a back-end code generator that lowers Three-Address Code into MIPS, LLVM IR, or x86-64 assembly.

---

## CHAPTER 7 — CONCLUSION

The **AI-Powered Compiler & Diagnostic Assistant for a Python-Like Language (`.pyl`)** project successfully demonstrates the design and construction of an academic compiler coupled with an advisory AI assistant.

By leveraging PLY (`ply.lex` and `ply.yacc`), the project realizes a complete, deterministic front-end pipeline:
- An indentation-aware scanner that translates whitespace changes into formal `INDENT` and `DEDENT` tokens.
- An LALR(1) parser that enforces a Context-Free Grammar and constructs a clean AST.
- A scoped symbol table that enforces lexical block scoping, variable shadowing, and static typing rules.
- A code generator that lowers validated syntax trees into clean, linear Three-Address Code intermediate representations.

Crucially, the architecture resolves the tension between formal compiler determinism and generative AI capabilities. The compiler retains sole authority over program validity, while the diagnostic engine captures structured coordinates and visual caret context to guide the AI assistant. By constraining LLM prompts to the formal language specification, the assistant provides clear, pedagogical explanations and suggested fixes while constraining its responses to the .pyl language specification, without altering compiler behavior, and without modifying source code on disk.

All phases—from initial lexical scanning to end-to-end validation—have been fully implemented, verified, and demonstrated against comprehensive automated test suites.

---

## REFERENCES

1. **Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D.** *Compilers: Principles, Techniques, and Tools* (2nd Edition). Addison-Wesley, 2006. (Foundational reference for lexical analysis, LALR(1) shift-reduce parsing, symbol table design, and Three-Address Code generation).
2. **Beazley, D. M.** *PLY (Python Lex-Yacc)*, Version 3.11. Official Documentation and Implementation Guide. Available online: [https://www.dabeaz.com/ply/](https://www.dabeaz.com/ply/)
3. **Groq Cloud Developer Documentation.** *Groq API Client and Model Reference (`openai/gpt-oss-120b`)*. Available online: [https://console.groq.com/docs](https://console.groq.com/docs)
4. **Python Software Foundation.** *The Python Language Reference & Standard Library Documentation*. Available online: [https://docs.python.org/3/](https://docs.python.org/3/)
5. **Project Technical Specification & Grammar Documentation:**
   - `LANGUAGE_SPECIFICATION.md` (Formal `.pyl` language specification).
   - `GRAMMAR.md` (Context-Free Grammar and precedence rules).
   - `README.md` (System architecture, installation, and CLI reference).

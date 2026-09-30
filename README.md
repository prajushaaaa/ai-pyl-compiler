# AI-Powered Compiler & Diagnostic Assistant for a Python-Like Language (.pyl)

## 1. Project Purpose
An academic compiler and intelligent diagnostic assistant designed for a Python-like, statically typed pedagogical language (`.pyl`). The compiler implements a complete, deterministic pipeline from lexical scanning through Three-Address Code (TAC) intermediate representation generation, coupled with a decoupled AI diagnostic assistant for explaining compiler errors and recommending remediation.

## 2. What .pyl Is
`.pyl` is a minimal, pedagogical language inspired by Python syntax with strict static typing, explicit declaration-before-use semantics, and block scoping enforced through indentation. It demonstrates foundational compiler construction principles without the runtime complexities of full Python.

## 3. Supported Language Features

### Data Types
- `int` (e.g. `10`, `-5`)
- `float` (e.g. `3.14`, `0.5`)
- `str` (e.g. `"hello"`, `'world'`)
- `bool` (`True`, `False`)

### Operators & Precedence
- **Arithmetic:** `+`, `-`, `*`, `/` (standard precedence: `*`, `/` over `+`, `-`)
- **Unary:** `-` (negation)
- **Relational:** `<`, `>`, `==`, `!=`
- **Boolean / Logical:** `and`, `or`, `not` (strictly requires `bool` operands; no truthiness coercion)
- **Grouping:** Parentheses `( )` override precedence

### Statements & Control Flow
- **Variable Assignments:** `x = 10`
- **Conditional Branching:** `if`, `elif`, `else` with indentation-delimited blocks
- **Loops:** `while` with boolean conditions

### Explicitly Unsupported Features
The language scope deliberately excludes runtime overhead and object models:
- Functions and lambdas (`def`, `lambda`)
- Classes and OOP (`class`)
- Module imports (`import`)
- Data structures (`list`, `dict`, `tuple`, `set`)
- Exception handling (`try`, `except`)
- Assembly and machine code generation (stops at TAC IR)

---

## 4. Compiler Architecture & AI Diagnostic Role

```
                   DETERMINISTIC COMPILER (Source of Truth)
                                      │
  Source Code ──> Lexer ──> Parser ──> AST ──> Semantic Analyzer ──> TAC Generator ──> IR Output
                                      │
                               Compiler Error
                                      │
                                      ▼
                        DIAGNOSTIC INFRASTRUCTURE
                        - Context Extractor (Caret & Surrounding Lines)
                        - Structured Diagnostic Object
                                      │
                                      ▼
                             AI DIAGNOSTIC ENGINE
                        - PromptBuilder
                        - GroqAIProvider / MockAIProvider
                        - Structured Remediation (Explanation, Cause, Fix, Code)
```

### Architectural Principles:
1. **Deterministic Authority:** The compiler is the sole arbiter of syntactic and semantic validity. AI never determines compiler validity or modifies source files. Any corrected code returned by AI is only a diagnostic suggestion and is never automatically applied.
2. **Decoupled Diagnostics:** If the AI provider or network is unavailable, the compiler reports the authoritative compiler diagnostic cleanly without crashing.

---

## 5. Project Structure

```
ai_pyl_compiler/
├── codegen/          # Phase 5: Three-Address Code (TAC) generation
├── diagnostics/      # Phase 6: Diagnostic error handler, context extractor, AI providers
├── lexer/            # Phase 2: PLY scanner and indentation stack logic
├── parser/           # Phase 3: PLY LALR(1) parser and AST node hierarchy
├── semantics/        # Phase 4: Scoped symbol tables and static type checking
├── tests/            # Automated test suites and regression tests
├── main.py           # CLI driver
├── LANGUAGE_SPECIFICATION.md
├── GRAMMAR.md
├── requirements.txt
└── README.md
```

---

## 6. Installation

Clone the repository and install required dependencies in a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 7. Running the Compiler

Run the compiler via the command line:

```bash
python main.py <source_file.pyl>
```

Optional CLI flags:
- `--mock-ai`: Uses offline `MockAIProvider` for deterministic diagnostic evaluation without external API calls.
- `--no-ai`: Disables AI diagnostic requests entirely.

---

## 8. Groq API Configuration

To enable live AI diagnostics for compilation errors, configure the `GROQ_API_KEY` environment variable:

### Windows PowerShell:
```powershell
$env:GROQ_API_KEY="YOUR_API_KEY"
```

### Linux / macOS / Bash:
```bash
export GROQ_API_KEY="YOUR_API_KEY"
```

*Note: Never commit or hardcode actual API keys into source files or documentation.*

---

## 9. Example Usage

### Valid Program Example (`tests/valid/example.pyl`):
```python
x = 10 + 20 * 5
```

Execution:
```bash
python main.py tests/valid/example.pyl
```

Output:
```
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

### Compiler Error Example:
```python
x = 10
message = x + "items"
```

Output:
```
============================================================
.pyl COMPILER
============================================================

File: invalid.pyl

[1/4] Lexical Analysis ........ PASS
[2/4] Parsing .................. PASS
[3/4] Semantic Analysis ........ FAIL

============================================================
SEMANTIC ERROR
============================================================
File: invalid.pyl
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

---

## 10. Running Test Suites

Execute all automated verification suites:

```bash
# Phase 2 & 3: Front-End Pipeline
python tests/test_frontend.py

# Phase 4 & 5: Three-Address Code Integration
python tests/test_tac_integration.py

# Phase 6A, 6B & 6C: Diagnostic & Mock AI Integration
python tests/test_diagnostic_integration.py

# Phase 6D: Groq AI Provider (Deterministic & Optional Live)
python diagnostics/ai_diagnostic.py

# Phase 6E: Automated CLI Regression Suite
python tests/test_cli.py

# Phase 7: Full End-to-End Compiler Validation Suite
python tests/test_end_to_end.py
```

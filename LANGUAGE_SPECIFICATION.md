LANGUAGE SPECIFICATION
0.1 Project identity

Project title:

AI-Powered Compiler & Diagnostic Assistant for a Python-Like Language

Source file extension:

.pyl

Example:

program.pyl

The intended project is a compiler for a restricted Python-like language, not a full Python compiler.

0.2 What our compiler will accept

Our language will support five main categories:

1. Variables & Assignments
2. Data Types
3. Expressions & Operators
4. Conditional Statements
5. While Loops

Let's define each one precisely.

0.3 Variables

We allow normal Python-like identifiers.

Examples:

x
age
total
student_name
count1

Rules:

✓ Can contain letters
✓ Can contain digits
✓ Can contain underscore
✓ Cannot start with a digit
✓ Cannot be a keyword

Valid:

x = 10
student_name = "Ginni"
count1 = 5

Invalid:

1student = 10
0.4 Data types

The project specification defines these primitive types:

int
float
str
bool

Integer
x = 10

Type:

int
Float
price = 10.5

Type:

float
String
name = "Ginni"

Type:

str
Boolean
is_valid = True

Type:

bool
0.5 Assignments

Basic assignment:

x = 10

Expression assignment:

x = 10 + 20

Variable assignment:

x = 10
y = x

Complex expression:

result = x + y * 5

We will support assignments as one of the fundamental statements.

0.6 Arithmetic operators

We will support:

+
-
*
/

Examples:

x = 10 + 5
x = 10 - 5
x = 10 * 5
x = 10 / 5

Operator precedence will follow the standard mathematical ordering:

()
  ↓
* /
  ↓
+ -

So:

x = 10 + 5 * 2

is interpreted as:

10 + (5 * 2)

not:

(10 + 5) * 2

This matters when we construct the AST.

0.7 Relational operators

The specification includes:

<
>
==
!=

Examples:

x < y
x > y
x == y
x != y

These will primarily be used in conditions.

Example:

if x > 10:
    y = 20
0.8 Boolean operators

The previous implementation plan proposed:

and
or
not

for the language.

We'll include them, but we'll keep their implementation simple.

Examples:

if x > 5 and y < 20:
    z = 10

and:

if not valid:
    x = 0

If implementation becomes unnecessarily complicated, we can keep the initial supported combinations conservative rather than turning this into a full Python boolean-expression implementation.

0.9 Parentheses

We'll support:

x = (10 + 5) * 2

and:

if (x > 5):
    y = 10

Parentheses are important because they make expression parsing more interesting and demonstrate grammar precedence.

0.10 IF statement

Basic:

if x > 5:
    y = 10

Notice the colon:

if condition:

followed by an indented block.

0.11 IF–ELSE
if x > 5:
    y = 10
else:
    y = 20
0.12 IF–ELIF–ELSE

We'll support:

if x > 10:
    y = 1
elif x > 5:
    y = 2
else:
    y = 3

This is specifically part of the proposed project scope.

0.13 WHILE loop

Basic:

x = 5

while x > 0:
    x = x - 1

The body is determined by indentation.

0.14 Indentation

This is one of the important compiler-design features of our project.

We are not going to ignore spaces.

Example:

if x > 5:
    y = 10
    z = 20

The lexer should conceptually produce:

IF
IDENTIFIER
GREATER
INT
COLON
NEWLINE
INDENT

IDENTIFIER
ASSIGN
INT
NEWLINE

IDENTIFIER
ASSIGN
INT
NEWLINE

DEDENT

The project design specifically requires an indentation stack that emits INDENT and DEDENT.

0.15 Nested blocks

We should support nesting.

Example:

x = 10

if x > 5:
    y = 20

    if y > 10:
        z = 30

Conceptually:

IF
│
└── BLOCK
    │
    ├── y = 20
    │
    └── IF
        │
        └── BLOCK
            │
            └── z = 30

This will later test whether our INDENT/DEDENT implementation actually works.

0.16 What we are NOT supporting

This is equally important.

We are not building Python.

The project boundaries explicitly exclude things such as OOP, imports/modules, decorators, and target machine assembly/register allocation.

Therefore:

❌ Functions
def calculate():
    ...

Not supported.

❌ Classes
class Student:
    ...

Not supported.

❌ Imports
import math

Not supported.

❌ Lists
numbers = [1, 2, 3]

Not part of our initial language.

❌ Dictionaries
data = {"name": "Ginni"}

Not supported.

❌ Tuples
x = (1, 2)

We have to be careful here because parentheses are supported for expressions. A tuple syntax like (1,2) is not.

❌ Functions/lambdas
lambda x: x + 1

Not supported.

❌ Classes/inheritance

Not supported.

❌ Exceptions
try:
    ...
except:
    ...

Not supported.

❌ Machine code

We're stopping at Three Address Code.

That's exactly what the project needs.

0.17 Our first complete valid program

This will be one of our main test programs.

Create mentally this:

x = 10
y = 20
z = x + y

if z > 20:
    result = z * 2
else:
    result = z - 2

Our compiler should eventually be able to process the entire thing:

SOURCE
  ↓
LEXER
  ↓
TOKENS
  ↓
PARSER
  ↓
AST
  ↓
SEMANTIC ANALYSIS
  ↓
SYMBOL TABLE
  ↓
TAC
0.18 Another complete program — WHILE
count = 5

while count > 0:
    count = count - 1

Eventually TAC should look approximately like:

L1:
t1 = count > 0
if_false t1 goto L2
t2 = count - 1
count = t2
goto L1
L2:

The exact formatting will be decided during Phase 5/6, but the conceptual structure is what we're targeting.

0.19 Error categories

Our compiler will intentionally demonstrate three types of errors.

Lexical error

Something the lexer cannot recognize.

x = 10 @ 20

Potential result:

LEXICAL ERROR
Unexpected character '@'
Line: 1
Syntax error

The tokens exist, but their arrangement violates the grammar.

if x > 5
    y = 10

Missing:

:

Result:

SYNTAX ERROR
Expected ':'
Line: 1
Semantic error

The syntax is valid, but the meaning is invalid.

x = y + 10

if y hasn't been defined:

SEMANTIC ERROR
Variable 'y' is not declared.

Or:

x = "hello"
y = x + 10

Potential result:

SEMANTIC ERROR
Incompatible operands: str + int

Type checking and declaration-before-use are explicitly part of the intended semantic phase.

0.20 AI's role

This is extremely important.

Our architecture is:

                 COMPILER
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
     Lexer        Parser      Semantic
       │            │            │
       └────────────┼────────────┘
                    │
                 ERROR?
                    │
                    ↓
             DIAGNOSTIC ENGINE
                    │
                    ↓
                    AI

AI does not decide whether the program is syntactically valid.

The compiler does that.

AI receives the compiler's error information and makes it easier for the user to understand.

For example:

Compiler:
SyntaxError at line 4
Expected ':'

AI:

Your if statement is missing a colon.

Change:

if x > 5

to:

if x > 5:

That's consistent with the project's intended AI fallback design.

✅ PHASE 0 FINAL SPECIFICATION

So our language is officially:

Feature	Support
Variables	✅
Assignment	✅
int	✅
float	✅
str	✅
bool	✅
+	✅
-	✅
*	✅
/	✅
<	✅
>	✅
==	✅
!=	✅
and	✅
or	✅
not	✅
Parentheses	✅
if	✅
elif	✅
else	✅
while	✅
Indentation	✅
Nested blocks	✅
Symbol table	✅
Static type checking	✅
AST	✅
TAC	✅
AI diagnostics	✅
Functions	❌
Classes	❌
Imports	❌
Decorators	❌
Machine code	❌

This gives us a clear contract for the entire project.


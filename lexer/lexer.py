"""Lexical Analyzer (Scanner) for Python-Like Language (.pyl).

Phase 2A & 2B:
- Deterministic token recognition using PLY (lex).
- Python-like indentation handling with an indentation stack [0], emitting INDENT and DEDENT.
- Accurate line and column position tracking.
- Clear lexical and indentation error reporting.
"""

import sys
import ply.lex as lex
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ============================================================================
# Token Definitions
# ============================================================================

# Reserved keywords mapping
reserved = {
    'if': 'IF',
    'elif': 'ELIF',
    'else': 'ELSE',
    'while': 'WHILE',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'True': 'BOOLEAN',
    'False': 'BOOLEAN',
}

# Complete list of token types
tokens = (
    # Literals
    'INT',
    'FLOAT',
    'STRING',
    'BOOLEAN',

    # Identifiers
    'IDENTIFIER',

    # Keywords
    'IF',
    'ELIF',
    'ELSE',
    'WHILE',
    'AND',
    'OR',
    'NOT',

    # Arithmetic operators
    'PLUS',
    'MINUS',
    'MULTIPLY',
    'DIVIDE',

    # Assignment and relational operators
    'ASSIGN',
    'EQUALS',
    'NOT_EQUALS',
    'LESS',
    'GREATER',

    # Punctuation
    'COLON',
    'LPAREN',
    'RPAREN',

    # Newline & Indentation
    'NEWLINE',
    'INDENT',
    'DEDENT',
)

# ============================================================================
# Regular Expression Rules for Simple Tokens
# ============================================================================

# Arithmetic operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTIPLY = r'\*'
t_DIVIDE = r'/'

# Relational and assignment operators
# PLY sorts string regexes by length descending, ensuring '==' and '!=' precede '='.
t_EQUALS = r'=='
t_NOT_EQUALS = r'!='
t_ASSIGN = r'='
t_LESS = r'<'
t_GREATER = r'>'

# Punctuation
t_COLON = r':'
t_LPAREN = r'\('
t_RPAREN = r'\)'

# Ignored characters: spaces and tabs only (newlines are NOT ignored)
t_ignore = ' \t'


# ============================================================================
# Regular Expression Rules with Actions (Function Rules)
# ============================================================================

def t_COMMENT(t):
    r'\#[^\r\n]*'
    # Ignore comments until end of line
    pass


def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_STRING(t):
    r'("([^"\\\n\r]|\\.)*"|\'([^\'\\\n\r]|\\.)*\')'
    # Strip enclosing quotes to retain the literal string value
    t.value = t.value[1:-1]
    return t


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if identifier is a reserved keyword or boolean literal
    t.type = reserved.get(t.value, 'IDENTIFIER')
    if t.type == 'BOOLEAN':
        t.value = True if t.value == 'True' else False
    return t


def t_NEWLINE(t):
    r'\r?\n'
    t.lexer.lineno += 1
    t.value = '\n'
    return t


# ============================================================================
# Position and Error Handling
# ============================================================================

def find_column(input_text: str, token) -> int:
    """Calculate 1-based column position of token in input text."""
    line_start = input_text.rfind('\n', 0, token.lexpos)
    if line_start < 0:
        return token.lexpos + 1
    return token.lexpos - line_start


def t_error(t):
    """Handle illegal/unexpected characters clearly."""
    col = find_column(t.lexer.lexdata, t)
    char = t.value[0]
    msg = f"Unexpected character '{char}' at line {t.lineno}, column {col}"
    if hasattr(t.lexer, 'errors'):
        t.lexer.errors.append({
            'message': msg,
            'line': t.lineno,
            'column': col,
            'char': char
        })
    else:
        print(f"LEXICAL ERROR: {msg}")
    t.lexer.skip(1)


# ============================================================================
# Helper Functions for Indentation Handling
# ============================================================================

def compute_indent(whitespace: str) -> int:
    """Calculate the column indentation width of leading whitespace.
    
    Standard tab stop calculation (tab size = 4).
    """
    indent = 0
    for ch in whitespace:
        if ch == ' ':
            indent += 1
        elif ch == '\t':
            indent = (indent // 4 + 1) * 4
    return indent


def make_token(tok_type: str, value, lineno: int, lexpos: int, column: int = 1) -> lex.LexToken:
    """Construct a synthetic LexToken with coordinate metadata."""
    tok = lex.LexToken()
    tok.type = tok_type
    tok.value = value
    tok.lineno = lineno
    tok.lexpos = lexpos
    tok.column = column
    return tok


# ============================================================================
# Indentation Lexer (Phase 2B)
# ============================================================================

class IndentationLexer:
    """Lexer wrapper implementing Python-like indentation logic with PLY.
    
    Manages an indentation stack initialized as [0].
    Processes logical lines, injects INDENT and DEDENT tokens deterministically,
    filters empty/comment-only lines, emits EOF DEDENTs, and verifies block structure.
    """

    def __init__(self, raw_lexer=None):
        self.raw_lexer = raw_lexer if raw_lexer is not None else build_raw_lexer()
        self.source_code = ""
        self.tokens_queue = []
        self.errors = []
        self.lineno = 1
        self.lexpos = 0

    def input(self, source_code: str):
        self.source_code = source_code
        self.errors = []
        self.tokens_queue = self._process_tokens(source_code)
        self.lineno = 1
        self.lexpos = 0

    def token(self):
        """Fetch the next token from the processed token queue."""
        if self.tokens_queue:
            tok = self.tokens_queue.pop(0)
            self.lineno = tok.lineno
            self.lexpos = tok.lexpos
            return tok
        return None

    def _process_tokens(self, source_code: str):
        # 1. Scan raw tokens using the underlying PLY lexer
        self.raw_lexer.lineno = 1
        self.raw_lexer.errors = []
        self.raw_lexer.input(source_code)

        raw_tokens = []
        while True:
            tok = self.raw_lexer.token()
            if not tok:
                break
            tok.column = find_column(source_code, tok)
            raw_tokens.append(tok)

        # Propagate raw lexical errors
        if hasattr(self.raw_lexer, 'errors'):
            self.errors.extend(self.raw_lexer.errors)

        # 2. Group raw tokens into logical lines
        # A logical line contains non-NEWLINE tokens and is terminated by a NEWLINE.
        # Blank lines and comment-only lines have no tokens before NEWLINE and are ignored.
        logical_lines = []
        current_line_tokens = []

        for tok in raw_tokens:
            if tok.type == 'NEWLINE':
                if current_line_tokens:
                    logical_lines.append((current_line_tokens, tok))
                    current_line_tokens = []
            else:
                current_line_tokens.append(tok)

        # If file ends without a trailing newline, synthesize a NEWLINE for the final line
        if current_line_tokens:
            last_tok = current_line_tokens[-1]
            nl_pos = last_tok.lexpos + len(str(last_tok.value))
            nl_col = find_column(source_code, last_tok) + len(str(last_tok.value))
            nl_tok = make_token(
                tok_type='NEWLINE',
                value='\n',
                lineno=last_tok.lineno,
                lexpos=nl_pos,
                column=nl_col
            )
            logical_lines.append((current_line_tokens, nl_tok))

        # 3. Process indentation stack across logical lines
        output_tokens = []
        indentation_stack = [0]
        prev_line_ended_with_colon = False
        last_lineno = 1

        for line_tokens, nl_tok in logical_lines:
            tok_1 = line_tokens[0]
            last_lineno = line_tokens[-1].lineno

            # Determine leading whitespace before the first token of this logical line
            line_start = source_code.rfind('\n', 0, tok_1.lexpos)
            if line_start < 0:
                line_start = 0
            else:
                line_start = line_start + 1

            leading_whitespace = source_code[line_start:tok_1.lexpos]
            current_indent = compute_indent(leading_whitespace)

            # Apply indentation algorithm:
            if current_indent > indentation_stack[-1]:
                if prev_line_ended_with_colon:
                    indentation_stack.append(current_indent)
                    indent_tok = make_token(
                        tok_type='INDENT',
                        value='',
                        lineno=tok_1.lineno,
                        lexpos=line_start,
                        column=1
                    )
                    output_tokens.append(indent_tok)
                else:
                    # Indentation increased without a preceding block header (colon)
                    msg = (
                        f"Indentation error: indentation level {current_indent} "
                        f"does not match a previously established indentation level"
                    )
                    self.errors.append({
                        'message': msg,
                        'line': tok_1.lineno,
                        'column': tok_1.column,
                        'char': ''
                    })
            elif current_indent == indentation_stack[-1]:
                # Current indentation matches block level; emit neither INDENT nor DEDENT
                pass
            elif current_indent < indentation_stack[-1]:
                if current_indent in indentation_stack:
                    while indentation_stack[-1] > current_indent:
                        indentation_stack.pop()
                        dedent_tok = make_token(
                            tok_type='DEDENT',
                            value='',
                            lineno=tok_1.lineno,
                            lexpos=line_start,
                            column=1
                        )
                        output_tokens.append(dedent_tok)
                else:
                    # Indentation does not match any existing level after popping
                    msg = (
                        f"Indentation error: indentation level {current_indent} "
                        f"does not match a previously established indentation level"
                    )
                    self.errors.append({
                        'message': msg,
                        'line': tok_1.lineno,
                        'column': tok_1.column,
                        'char': ''
                    })

            # Emit all tokens on this logical line
            output_tokens.extend(line_tokens)

            # Emit the terminating NEWLINE
            output_tokens.append(nl_tok)

            # Check if this line ended with a COLON
            prev_line_ended_with_colon = (line_tokens[-1].type == 'COLON')

        # 4. At EOF, emit DEDENT tokens for all remaining indentation levels until stack returns to [0]
        while len(indentation_stack) > 1:
            indentation_stack.pop()
            dedent_tok = make_token(
                tok_type='DEDENT',
                value='',
                lineno=last_lineno,
                lexpos=len(source_code),
                column=1
            )
            output_tokens.append(dedent_tok)

        return output_tokens


# ============================================================================
# Lexer Factory and Tokenizer API
# ============================================================================

def build_raw_lexer(**kwargs):
    """Construct and return the underlying PLY lexer instance."""
    return lex.lex(**kwargs)


def build_lexer(**kwargs):
    """Construct and return the full IndentationLexer instance."""
    raw = build_raw_lexer(**kwargs)
    return IndentationLexer(raw)


def tokenize(source_code: str, lexer=None):
    """Tokenize source code string into a list of tokens and recorded errors."""
    if lexer is None:
        lexer = build_lexer()

    lexer.input(source_code)

    tokens_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens_list.append(tok)

    return tokens_list, getattr(lexer, 'errors', [])


# ============================================================================
# CLI Test Runner
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python lexer/lexer.py <path-to-pyl-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        sys.exit(1)

    tokens_list, errors = tokenize(code)

    console = Console()
    table = Table(
        title=f"Token Stream for [bold cyan]{filepath}[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_blue",
    )
    table.add_column("TOKEN TYPE", style="cyan", no_wrap=True)
    table.add_column("VALUE", style="green")
    table.add_column("LINE", justify="right", style="yellow")
    table.add_column("POSITION", justify="right", style="blue")

    for tok in tokens_list:
        if tok.type == "NEWLINE":
            val_display = r"\n"
        elif tok.type == "STRING":
            val_display = f'"{tok.value}"'
        elif tok.type == "BOOLEAN":
            val_display = str(tok.value)
        elif tok.type in ("INDENT", "DEDENT"):
            val_display = ""
        else:
            val_display = str(tok.value)

        table.add_row(
            tok.type,
            val_display,
            str(tok.lineno),
            f"Col {tok.column} (Pos {tok.lexpos})"
        )

    console.print(table)

    if errors:
        error_lines = [
            f"[bold red]Line {e['line']}, Col {e['column']}:[/bold red] {e['message']}"
            for e in errors
        ]
        console.print(Panel(
            "\n".join(error_lines),
            title="[bold red]Lexical / Indentation Errors[/bold red]",
            border_style="red"
        ))
        sys.exit(1)
    else:
        console.print("[bold green][OK] Lexical analysis successful: 0 errors detected.[/bold green]")


if __name__ == '__main__':
    main()

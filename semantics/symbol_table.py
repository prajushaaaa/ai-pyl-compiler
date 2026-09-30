"""Scoped Symbol Table for the .pyl compiler.

Manages symbols, lexical scopes, symbol resolution, and scope lifecycles
for static semantic analysis.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Set

# Supported language types in .pyl
VALID_TYPES: Set[str] = {"int", "float", "str", "bool"}


# ==============================================================================
# Error Hierarchy
# ==============================================================================

class SymbolTableError(Exception):
    """Base exception for all symbol table errors."""
    pass


class DuplicateSymbolError(SymbolTableError):
    """Raised when a symbol is defined more than once within the same scope."""
    pass


class UndefinedSymbolError(SymbolTableError):
    """Raised when looking up or modifying an undefined symbol."""
    pass


class ScopeError(SymbolTableError):
    """Raised when an invalid scope operation is attempted."""
    pass


# ==============================================================================
# Symbol Representation
# ==============================================================================

@dataclass
class Symbol:
    """Represents an identifier declared in the program."""
    name: str
    type: str
    scope_name: str
    scope_level: int = 0
    line: Optional[int] = None
    column: Optional[int] = None

    def __repr__(self) -> str:
        loc = f", line={self.line}, col={self.column}" if self.line is not None else ""
        return f"Symbol(name='{self.name}', type='{self.type}', scope='{self.scope_name}', level={self.scope_level}{loc})"


# ==============================================================================
# Scope Representation
# ==============================================================================

class Scope:
    """Represents a single lexical scope containing symbols and parent link."""

    def __init__(self, name: str, level: int = 0, parent: Optional["Scope"] = None) -> None:
        self.name: str = name
        self.level: int = level
        self.parent: Optional["Scope"] = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        """Add a symbol to this scope."""
        self.symbols[symbol.name] = symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol strictly in this scope."""
        return self.symbols.get(name)

    def __repr__(self) -> str:
        return f"Scope(name='{self.name}', level={self.level}, symbols={list(self.symbols.keys())})"


# ==============================================================================
# Symbol Table
# ==============================================================================

class SymbolTable:
    """Scoped Symbol Table for tracking identifiers across nested scopes."""

    def __init__(self) -> None:
        self._scope_counter: int = 0
        global_scope = Scope(name="global", level=0, parent=None)
        self.scope_stack: List[Scope] = [global_scope]
        self.all_scopes: List[Scope] = [global_scope]

    @property
    def current_scope(self) -> Scope:
        """Return the current active scope at the top of the stack."""
        return self.scope_stack[-1]

    def current_scope_name(self) -> str:
        """Return the identifier of the current active scope."""
        return self.current_scope.name

    def current_scope_level(self) -> int:
        """Return the nesting level of the current active scope (0 for global)."""
        return self.current_scope.level

    def enter_scope(self, name: Optional[str] = None) -> Scope:
        """Create and enter a new nested scope, pushing it onto the scope stack."""
        self._scope_counter += 1
        scope_name = name if name is not None else f"scope_{self._scope_counter}"
        new_scope = Scope(
            name=scope_name,
            level=self.current_scope.level + 1,
            parent=self.current_scope
        )
        self.scope_stack.append(new_scope)
        self.all_scopes.append(new_scope)
        return new_scope

    def exit_scope(self) -> Scope:
        """Exit the current scope and return to its parent scope.
        
        Raises:
            ScopeError: If attempting to exit the global scope.
        """
        if len(self.scope_stack) <= 1:
            raise ScopeError("Cannot exit the global scope.")
        return self.scope_stack.pop()

    def define(
        self,
        name: str,
        type_name: str,
        line: Optional[int] = None,
        column: Optional[int] = None
    ) -> Symbol:
        """Define a new symbol in the current scope.
        
        Raises:
            SymbolTableError: If type_name is not one of the supported language types.
            DuplicateSymbolError: If name is already defined in the current scope.
        """
        if type_name not in VALID_TYPES:
            raise SymbolTableError(
                f"Unsupported type '{type_name}'. Supported types are: {sorted(VALID_TYPES)}"
            )

        if name in self.current_scope.symbols:
            raise DuplicateSymbolError(
                f"Duplicate symbol '{name}' already defined in current scope '{self.current_scope.name}'."
            )

        symbol = Symbol(
            name=name,
            type=type_name,
            scope_name=self.current_scope.name,
            scope_level=self.current_scope.level,
            line=line,
            column=column
        )
        self.current_scope.define(symbol)
        return symbol

    def update(self, name: str, type_name: str) -> Symbol:
        """Update the type of an existing symbol in the nearest enclosing scope.
        
        Raises:
            SymbolTableError: If type_name is not supported.
            UndefinedSymbolError: If name does not exist in any enclosing scope.
        """
        if type_name not in VALID_TYPES:
            raise SymbolTableError(
                f"Unsupported type '{type_name}'. Supported types are: {sorted(VALID_TYPES)}"
            )

        symbol = self.lookup(name)
        symbol.type = type_name
        return symbol

    def lookup(self, name: str) -> Symbol:
        """Look up a symbol from the current scope up through enclosing parent scopes.
        
        Raises:
            UndefinedSymbolError: If the symbol cannot be found in any enclosing scope.
        """
        curr: Optional[Scope] = self.current_scope
        while curr is not None:
            if name in curr.symbols:
                return curr.symbols[name]
            curr = curr.parent

        raise UndefinedSymbolError(
            f"Symbol '{name}' is not defined in current scope '{self.current_scope.name}' or any parent scope."
        )

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Look up a symbol strictly within the current scope.
        
        Returns:
            The Symbol if found, or None if not defined in the current scope.
        """
        return self.current_scope.lookup_local(name)

    def exists(self, name: str, current_only: bool = False) -> bool:
        """Check whether a symbol exists.
        
        Args:
            name: The symbol name to check.
            current_only: If True, only search the current scope; otherwise search all enclosing scopes.
            
        Returns:
            True if found, False otherwise.
        """
        if current_only:
            return name in self.current_scope.symbols
        try:
            self.lookup(name)
            return True
        except UndefinedSymbolError:
            return False

    def __contains__(self, name: str) -> bool:
        """Enable 'name in symbol_table' syntax."""
        return self.exists(name, current_only=False)

    def dump(self) -> str:
        """Display the active symbol table scopes and their symbols."""
        lines = []
        for scope in self.scope_stack:
            lines.append(f"Scope: {scope.name}")
            lines.append("-" * 32)
            lines.append(f"{'Name':<12} {'Type':<10}")
            lines.append("-" * 32)
            if not scope.symbols:
                lines.append("(empty)")
            else:
                for sym in scope.symbols.values():
                    lines.append(f"{sym.name:<12} {sym.type:<10}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def print_table(self) -> None:
        """Print the formatted symbol table to standard output."""
        print(self.dump())


# ==============================================================================
# Self Tests
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4A: Symbol Table Self-Tests")
    print("=" * 60)

    # --------------------------------------------------------------------------
    # Test 1: Create a symbol table and define global variables
    # --------------------------------------------------------------------------
    st = SymbolTable()
    st.define("x", "int", line=1, column=1)
    st.define("name", "str", line=2, column=1)
    st.define("active", "bool", line=3, column=1)

    sym_x = st.lookup("x")
    sym_name = st.lookup("name")
    sym_active = st.lookup("active")

    assert sym_x.name == "x" and sym_x.type == "int" and sym_x.scope_name == "global"
    assert sym_name.name == "name" and sym_name.type == "str" and sym_name.scope_name == "global"
    assert sym_active.name == "active" and sym_active.type == "bool" and sym_active.scope_name == "global"
    print("[PASS] Test 1: Created symbol table and verified global lookups (x, name, active).")

    # --------------------------------------------------------------------------
    # Test 2: Enter nested scope and verify local & parent lookups
    # --------------------------------------------------------------------------
    nested_scope = st.enter_scope()
    assert st.current_scope_name() == "scope_1"
    assert st.current_scope_level() == 1

    st.define("y", "float", line=5, column=5)

    sym_y = st.lookup("y")
    assert sym_y.name == "y" and sym_y.type == "float" and sym_y.scope_name == "scope_1"

    sym_x_parent = st.lookup("x")
    assert sym_x_parent.name == "x" and sym_x_parent.type == "int" and sym_x_parent.scope_name == "global"
    print("[PASS] Test 2: Nested scope entered; verified local 'y' and parent-scope lookup for 'x'.")

    # --------------------------------------------------------------------------
    # Test 3: Verify lookup_current_scope() isolation
    # --------------------------------------------------------------------------
    assert st.lookup_current_scope("y") is not None
    assert st.lookup_current_scope("x") is None
    print("[PASS] Test 3: lookup_current_scope() confirmed 'x' is not found in nested scope's current-only lookup.")

    # --------------------------------------------------------------------------
    # Test 4: Try defining in the SAME scope again (DuplicateSymbolError)
    # --------------------------------------------------------------------------
    # Subtest 4a: Redefining 'y' in the current scope raises DuplicateSymbolError
    try:
        st.define("y", "float", line=6, column=5)
        raise AssertionError("Expected DuplicateSymbolError when defining 'y' twice in the same scope")
    except DuplicateSymbolError:
        pass

    # Subtest 4b: Defining 'x' in current scope shadows global 'x', but defining 'x' again in current scope raises
    st.define("x", "int", line=7, column=5)
    try:
        st.define("x", "int", line=8, column=5)
        raise AssertionError("Expected DuplicateSymbolError when defining 'x' twice in the same scope")
    except DuplicateSymbolError:
        pass
    print("[PASS] Test 4: Duplicate symbol definition in the same scope raises DuplicateSymbolError.")

    # --------------------------------------------------------------------------
    # Test 5: Exit nested scope and verify accessibility
    # --------------------------------------------------------------------------
    st.exit_scope()
    assert st.current_scope_name() == "global"
    assert st.current_scope_level() == 0

    # Verify 'y' is no longer accessible
    try:
        st.lookup("y")
        raise AssertionError("Expected UndefinedSymbolError for 'y' after exiting nested scope")
    except UndefinedSymbolError:
        pass

    # Verify 'x' is accessible again from global scope
    sym_x_restored = st.lookup("x")
    assert sym_x_restored.scope_name == "global"
    assert sym_x_restored.type == "int"
    print("[PASS] Test 5: Exited nested scope; 'y' is no longer accessible and global 'x' is accessible.")

    # --------------------------------------------------------------------------
    # Test 6: Verify UndefinedSymbolError on unknown identifier
    # --------------------------------------------------------------------------
    try:
        st.lookup("unknown")
        raise AssertionError("Expected UndefinedSymbolError for 'unknown'")
    except UndefinedSymbolError:
        pass
    print("[PASS] Test 6: Lookup of undefined variable 'unknown' correctly raised UndefinedSymbolError.")

    # --------------------------------------------------------------------------
    # Additional Verification: update(), exists(), print_table()
    # --------------------------------------------------------------------------
    st.update("x", "float")
    assert st.lookup("x").type == "float"
    st.update("x", "int")  # Restore to int
    assert "x" in st
    assert "unknown" not in st
    print("[PASS] Extra: Verified update(), exists(), and membership containment.")

    print("\n" + "=" * 60)
    print("SYMBOL TABLE DUMP DEMONSTRATION")
    print("=" * 60)
    st.print_table()
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")

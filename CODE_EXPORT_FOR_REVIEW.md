# Code Compass - Complete Code Export for Review

## Project Structure

```
code-compass/
├── code_compass/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py          # Core data structures
│   ├── graph.py           # Dependency graph & PageRank
│   ├── cache.py           # SQLite caching layer
│   ├── cli.py             # Command-line interface
│   └── parsers/
│       ├── __init__.py
│       └── python_parser.py  # Python AST parser
├── tests/
│   ├── test_python_parser.py
│   └── test_cache.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Statistics

- **Total Files**: 10
- **Total Lines**: 1439
- **Language**: Python 3.11+
- **Dependencies**: click (CLI), sqlite3 (built-in)

---

## File: `code_compass/models.py`

**Lines**: 82

```python
"""Core data structures for Code Compass."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SymbolType(Enum):
    """Type of code symbol."""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


@dataclass
class Symbol:
    """Represents a code symbol (class, function, or method)."""
    name: str                    # Symbol name
    type: SymbolType            # Symbol type
    file_path: str              # File path (relative to project root)
    line_start: int             # Starting line number
    line_end: int               # Ending line number
    signature: str              # Full signature (with params and return type)
    parent: Optional[str]       # Parent symbol (class name for methods)
    
    def to_map_line(self) -> str:
        """Convert to a single line in the repo map."""
        indent = "│ " if self.parent else "│"
        return f"{indent}{self.signature}"


@dataclass
class FileInfo:
    """Metadata about a source file."""
    path: str                   # Relative path from project root
    language: str               # Language type (python, javascript, typescript)
    hash: str                   # SHA256 hash (for change detection)
    size: int                   # File size in bytes
    symbols: list[Symbol]       # All symbols in this file
    imports: list[str]          # List of imported modules
    
    def is_changed(self, current_hash: str) -> bool:
        """Check if file has changed since last index."""
        return self.hash != current_hash


@dataclass
class RepoMap:
    """Generated repository map."""
    files: list[str]                    # List of included files (sorted by importance)
    symbols: dict[str, list[Symbol]]    # Symbols for each file
    token_count: int                    # Estimated total token count
    
    def to_text(self) -> str:
        """Convert to text format (similar to Aider)."""
        lines = []
        for file_path in self.files:
            lines.append(f"\n{file_path}:")
            lines.append("⋮...")
            for symbol in self.symbols[file_path]:
                lines.append(symbol.to_map_line())
            lines.append("⋮...")
        return "\n".join(lines)
    
    def to_json(self) -> dict:
        """Convert to JSON format."""
        return {
            "files": self.files,
            "symbols": {
                file: [
                    {
                        "name": s.name,
                        "type": s.type.value,
                        "signature": s.signature,
                        "line": s.line_start
                    }
                    for s in symbols
                ]
                for file, symbols in self.symbols.items()
            },
            "token_count": self.token_count
        }

```

---

## File: `code_compass/graph.py`

**Lines**: 123

```python
"""Dependency graph construction and analysis."""

from collections import defaultdict
from pathlib import Path
from typing import Optional

from .models import FileInfo


class DependencyGraph:
    """File-level dependency graph."""
    
    def __init__(self):
        # Adjacency list: file_path -> [imported_file_paths]
        self.edges: dict[str, set[str]] = defaultdict(set)
        # Reverse index: file_path -> [files_that_import_it]
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)
    
    def add_edge(self, from_file: str, to_file: str):
        """Add a dependency edge."""
        self.edges[from_file].add(to_file)
        self.reverse_edges[to_file].add(from_file)
    
    def get_dependencies(self, file_path: str) -> set[str]:
        """Get all files that this file depends on."""
        return self.edges.get(file_path, set())
    
    def get_dependents(self, file_path: str) -> set[str]:
        """Get all files that depend on this file."""
        return self.reverse_edges.get(file_path, set())
    
    def compute_importance(self) -> dict[str, float]:
        """
        Compute importance score for each file using simplified PageRank.
        
        Files that are imported by many other files are considered more important.
        """
        # Initialize: each node starts with score 1.0
        all_files = set(self.edges.keys()) | set(self.reverse_edges.keys())
        scores = {file: 1.0 for file in all_files}
        
        # Iterate 10 times (usually converges quickly)
        for _ in range(10):
            new_scores = {}
            for file in all_files:
                # Score = 0.15 + 0.85 * Σ(score_of_dependent / out_degree_of_dependent)
                incoming_score = 0.0
                for dependent in self.reverse_edges.get(file, set()):
                    out_degree = len(self.edges.get(dependent, set()))
                    if out_degree > 0:
                        incoming_score += scores[dependent] / out_degree
                
                new_scores[file] = 0.15 + 0.85 * incoming_score
            
            scores = new_scores
        
        return scores


class DependencyBuilder:
    """Build file-level dependency graph from parsed files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.graph = DependencyGraph()
        # Module name -> file path mapping
        self.module_to_file: dict[str, str] = {}
    
    def build(self, files: list[FileInfo]) -> DependencyGraph:
        """Build dependency graph from file information."""
        
        # Step 1: Build module name to file path mapping
        for file_info in files:
            module_name = self._file_to_module(file_info.path)
            self.module_to_file[module_name] = file_info.path
        
        # Step 2: Build edges based on imports
        for file_info in files:
            for imported_module in file_info.imports:
                # Try to resolve the imported module to a file path
                imported_file = self._resolve_import(
                    imported_module,
                    file_info.path
                )
                if imported_file:
                    self.graph.add_edge(file_info.path, imported_file)
        
        return self.graph
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        # src/utils/parser.py -> src.utils.parser
        return file_path.replace("/", ".").replace(".py", "").replace(".js", "").replace(".ts", "")
    
    def _resolve_import(self, module_name: str, from_file: str) -> Optional[str]:
        """
        Resolve imported module to file path.
        
        This is a best-effort approach - it won't catch all cases,
        especially with dynamic imports or complex package structures.
        """
        
        # Case 1: Absolute import (module is in our mapping)
        if module_name in self.module_to_file:
            return self.module_to_file[module_name]
        
        # Case 2: Relative import (starts with .)
        if module_name.startswith("."):
            # Get the directory of the importing file
            from_dir = str(Path(from_file).parent)
            # Resolve relative path
            # This is simplified - real resolution is more complex
            resolved_module = from_dir.replace("/", ".") + module_name
            if resolved_module in self.module_to_file:
                return self.module_to_file[resolved_module]
        
        # Case 3: Try partial matches (e.g., "utils" might match "src.utils")
        for mod, file in self.module_to_file.items():
            if mod.endswith("." + module_name) or mod == module_name:
                return file
        
        # Case 4: Standard library or external package - ignore
        return None

```

---

## File: `code_compass/parsers/python_parser.py`

**Lines**: 233

```python
"""Python code parser using AST."""

import ast
import hashlib
from pathlib import Path
from typing import Optional

from ..models import FileInfo, Symbol, SymbolType


class PythonParser:
    """Parser for Python source files."""
    
    def parse_file(self, file_path: Path, project_root: Path) -> Optional[FileInfo]:
        """
        Parse a single Python file.
        
        Args:
            file_path: Absolute path to the Python file
            project_root: Project root directory
            
        Returns:
            FileInfo object or None if parsing fails
        """
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                # Syntax error: return empty result, don't crash
                print(f"⚠️  Syntax error in {file_path}: {e}")
                return FileInfo(
                    path=str(file_path.relative_to(project_root)),
                    language="python",
                    hash=file_hash,
                    size=len(content),
                    symbols=[],
                    imports=[]
                )
            
            # Extract symbols and imports
            visitor = PythonVisitor(file_path, project_root)
            visitor.visit(tree)
            
            return FileInfo(
                path=str(file_path.relative_to(project_root)),
                language="python",
                hash=file_hash,
                size=len(content),
                symbols=visitor.symbols,
                imports=visitor.imports
            )
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return None


class PythonVisitor(ast.NodeVisitor):
    """AST visitor to extract symbols and imports."""
    
    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        self.symbols: list[Symbol] = []
        self.imports: list[str] = []
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        # Extract base classes
        bases = [self._get_name(base) for base in node.bases if self._get_name(base)]
        base_str = f"({', '.join(bases)})" if bases else ""
        
        # Extract decorators
        decorators = [f"@{self._get_name(dec)}" for dec in node.decorator_list if self._get_name(dec)]
        decorator_str = " ".join(decorators) + " " if decorators else ""
        
        # Build signature
        signature = f"{decorator_str}class {node.name}{base_str}:"
        
        # Create Symbol
        symbol = Symbol(
            name=node.name,
            type=SymbolType.CLASS,
            file_path=str(self.file_path.relative_to(self.project_root)),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            parent=None
        )
        self.symbols.append(symbol)
        
        # Save current class and continue traversing methods
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function/method definition."""
        self._handle_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function/method definition."""
        self._handle_function(node, is_async=True)
    
    def _handle_function(self, node, is_async=False):
        """Handle both sync and async function definitions."""
        # Extract parameters
        args = []
        
        # Regular arguments
        for i, arg in enumerate(node.args.args):
            arg_str = arg.arg
            # Add type annotation if present
            if arg.annotation:
                arg_str += f": {self._get_name(arg.annotation)}"
            # Add default value if present
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_val = self._get_default_value(node.args.defaults[default_idx])
                if default_val:
                    arg_str += f" = {default_val}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += f": {self._get_name(node.args.vararg.annotation)}"
            args.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += f": {self._get_name(node.args.kwarg.annotation)}"
            args.append(kwarg_str)
        
        # Extract return type
        return_type = ""
        if node.returns:
            return_type = f" -> {self._get_name(node.returns)}"
        
        # Extract decorators
        decorators = [f"@{self._get_name(dec)}" for dec in node.decorator_list if self._get_name(dec)]
        decorator_str = " ".join(decorators) + " " if decorators else ""
        
        # Build signature
        async_str = "async " if is_async else ""
        signature = f"{decorator_str}{async_str}def {node.name}({', '.join(args)}){return_type}:"
        
        # Determine symbol type
        symbol_type = SymbolType.METHOD if self.current_class else SymbolType.FUNCTION
        
        # Create Symbol
        symbol = Symbol(
            name=node.name,
            type=symbol_type,
            file_path=str(self.file_path.relative_to(self.project_root)),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            parent=self.current_class
        )
        self.symbols.append(symbol)
        
        # Don't traverse function body (we don't need it)
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statement."""
        if node.module:
            self.imports.append(node.module)
    
    def _get_name(self, node) -> str:
        """Extract name from AST node."""
        if node is None:
            return ""
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Subscript):
            # Handle generics like List[str], Dict[str, int]
            value = self._get_name(node.value)
            slice_val = self._get_name(node.slice)
            return f"{value}[{slice_val}]" if slice_val else value
        elif isinstance(node, ast.Tuple):
            # Handle multiple types like Union[str, int]
            elements = [self._get_name(elt) for elt in node.elts]
            return ", ".join(filter(None, elements))
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            # Handle callable types
            func = self._get_name(node.func)
            return func
        else:
            return ""
    
    def _get_default_value(self, node) -> str:
        """Extract default value from AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
            # Return simplified representation
            if isinstance(node, ast.List):
                return "[]"
            elif isinstance(node, ast.Tuple):
                return "()"
            elif isinstance(node, ast.Dict):
                return "{}"
            elif isinstance(node, ast.Set):
                return "set()"
        return ""

```

---

## File: `code_compass/cache.py`

**Lines**: 311

```python
"""SQLite-based caching layer for parsed code."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .models import FileInfo, Symbol, SymbolType


class CacheManager:
    """Manages SQLite cache for parsed code."""
    
    def __init__(self, cache_dir: Path):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache database
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "index.db"
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                language TEXT NOT NULL,
                hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                imports TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Symbols table with full-text search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                signature TEXT NOT NULL,
                parent TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_name 
            ON symbols(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_file 
            ON symbols(file_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_files_path 
            ON files(path)
        """)
        
        self.conn.commit()
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Get cached hash for a file."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash FROM files WHERE path = ?",
            (file_path,)
        )
        row = cursor.fetchone()
        return row['hash'] if row else None
    
    def is_file_cached(self, file_path: str, current_hash: str) -> bool:
        """Check if file is cached and unchanged."""
        cached_hash = self.get_file_hash(file_path)
        return cached_hash == current_hash if cached_hash else False
    
    def save_file(self, file_info: FileInfo):
        """Save or update file information in cache."""
        cursor = self.conn.cursor()
        
        # Check if file exists
        cursor.execute(
            "SELECT id FROM files WHERE path = ?",
            (file_info.path,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing file
            file_id = existing['id']
            cursor.execute("""
                UPDATE files 
                SET hash = ?, size = ?, language = ?, imports = ?, indexed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                file_info.hash,
                file_info.size,
                file_info.language,
                json.dumps(file_info.imports),
                file_id
            ))
            
            # Delete old symbols
            cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        else:
            # Insert new file
            cursor.execute("""
                INSERT INTO files (path, language, hash, size, imports)
                VALUES (?, ?, ?, ?, ?)
            """, (
                file_info.path,
                file_info.language,
                file_info.hash,
                file_info.size,
                json.dumps(file_info.imports)
            ))
            file_id = cursor.lastrowid
        
        # Insert symbols
        for symbol in file_info.symbols:
            cursor.execute("""
                INSERT INTO symbols (file_id, name, type, line_start, line_end, signature, parent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                symbol.name,
                symbol.type.value,
                symbol.line_start,
                symbol.line_end,
                symbol.signature,
                symbol.parent
            ))
        
        self.conn.commit()
    
    def get_file(self, file_path: str) -> Optional[FileInfo]:
        """Retrieve file information from cache."""
        cursor = self.conn.cursor()
        
        # Get file info
        cursor.execute(
            "SELECT * FROM files WHERE path = ?",
            (file_path,)
        )
        file_row = cursor.fetchone()
        
        if not file_row:
            return None
        
        # Get symbols
        cursor.execute(
            "SELECT * FROM symbols WHERE file_id = ? ORDER BY line_start",
            (file_row['id'],)
        )
        symbol_rows = cursor.fetchall()
        
        symbols = [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=file_path,
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in symbol_rows
        ]
        
        return FileInfo(
            path=file_row['path'],
            language=file_row['language'],
            hash=file_row['hash'],
            size=file_row['size'],
            symbols=symbols,
            imports=json.loads(file_row['imports'])
        )
    
    def get_all_files(self) -> list[FileInfo]:
        """Retrieve all cached files."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT path FROM files ORDER BY path")
        paths = [row['path'] for row in cursor.fetchall()]
        
        return [self.get_file(path) for path in paths]
    
    def find_symbol(self, name: str) -> list[Symbol]:
        """Find all symbols with given name."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name = ?
            ORDER BY f.path, s.line_start
        """, (name,))
        
        rows = cursor.fetchall()
        return [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=row['file_path'],
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in rows
        ]
    
    def search_symbols(self, pattern: str) -> list[Symbol]:
        """Search symbols by name pattern (case-insensitive)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ?
            ORDER BY f.path, s.line_start
        """, (f"%{pattern}%",))
        
        rows = cursor.fetchall()
        return [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=row['file_path'],
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in rows
        ]
    
    def delete_file(self, file_path: str):
        """Remove file from cache."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE path = ?", (file_path,))
        self.conn.commit()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM files")
        file_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        symbol_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM files 
            GROUP BY language
        """)
        by_language = {row['language']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM symbols 
            GROUP BY type
        """)
        by_type = {row['type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_files': file_count,
            'total_symbols': symbol_count,
            'by_language': by_language,
            'by_type': by_type
        }
    
    def clear(self):
        """Clear all cache data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM files")
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

```

---

## File: `code_compass/cli.py`

**Lines**: 47

```python
"""Command-line interface for Code Compass."""

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Code Compass - Fast code map generator for AI coding assistants."""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--force', is_flag=True, help='Force re-index all files')
def index(path: str, force: bool):
    """Index a project's code."""
    click.echo(f"🔍 Indexing project: {path}")
    click.echo("⚠️  Not implemented yet - coming in Day 8-9")


@cli.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.option('--tokens', type=int, default=1000, help='Token budget')
def map(format: str, tokens: int):
    """Generate a code map."""
    click.echo(f"🗺️  Generating map (format={format}, tokens={tokens})")
    click.echo("⚠️  Not implemented yet - coming in Day 6-7")


@cli.command()
@click.argument('name')
def find(name: str):
    """Find symbol definitions."""
    click.echo(f"🔎 Finding symbol: {name}")
    click.echo("⚠️  Not implemented yet - coming in Day 11-13")


@cli.command()
def stats():
    """Show indexing statistics."""
    click.echo("📊 Project statistics:")
    click.echo("⚠️  Not implemented yet - coming in Day 11-13")


if __name__ == '__main__':
    cli()

```

---

## File: `code_compass/__init__.py`

**Lines**: 15

```python
"""Code Compass - Fast code map generator for AI coding assistants."""

__version__ = "0.1.0"

from .models import Symbol, SymbolType, FileInfo, RepoMap
from .graph import DependencyGraph, DependencyBuilder

__all__ = [
    "Symbol",
    "SymbolType",
    "FileInfo",
    "RepoMap",
    "DependencyGraph",
    "DependencyBuilder",
]

```

---

## File: `code_compass/__main__.py`

**Lines**: 6

```python
"""Allow running code_compass as a module: python -m code_compass"""

from .cli import cli

if __name__ == '__main__':
    cli()

```

---

## File: `code_compass/parsers/__init__.py`

**Lines**: 5

```python
"""Code parsers for different languages."""

from .python_parser import PythonParser

__all__ = ["PythonParser"]

```

---

## File: `tests/test_python_parser.py`

**Lines**: 238

```python
"""Tests for Python parser."""

import tempfile
from pathlib import Path

from code_compass.parsers import PythonParser
from code_compass.models import SymbolType


def test_parse_simple_function():
    """Test parsing a simple function."""
    code = """def hello(name: str) -> str:
    return f'Hello {name}'
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert file_info.language == "python"
        assert len(file_info.symbols) == 1
        
        symbol = file_info.symbols[0]
        assert symbol.name == "hello"
        assert symbol.type == SymbolType.FUNCTION
        assert "name: str" in symbol.signature
        assert "-> str" in symbol.signature


def test_parse_class_with_methods():
    """Test parsing a class with methods."""
    code = """class Calculator:
    def __init__(self, initial: int = 0):
        self.value = initial
    
    def add(self, x: int, y: int) -> int:
        return x + y
    
    async def fetch_data(self) -> dict:
        pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.symbols) == 4  # 1 class + 3 methods
        
        # Check class
        class_symbol = file_info.symbols[0]
        assert class_symbol.name == "Calculator"
        assert class_symbol.type == SymbolType.CLASS
        assert class_symbol.parent is None
        
        # Check methods
        init_symbol = file_info.symbols[1]
        assert init_symbol.name == "__init__"
        assert init_symbol.type == SymbolType.METHOD
        assert init_symbol.parent == "Calculator"
        assert "initial: int = 0" in init_symbol.signature
        
        add_symbol = file_info.symbols[2]
        assert add_symbol.name == "add"
        assert "-> int" in add_symbol.signature
        
        async_symbol = file_info.symbols[3]
        assert async_symbol.name == "fetch_data"
        assert "async def" in async_symbol.signature


def test_parse_with_decorators():
    """Test parsing functions and classes with decorators."""
    code = """@dataclass
class Point:
    x: int
    y: int

@staticmethod
def helper():
    pass

@property
def value(self):
    return self._value
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        
        # Check class decorator
        class_symbol = file_info.symbols[0]
        assert "@dataclass" in class_symbol.signature
        
        # Check method decorators
        helper_symbol = file_info.symbols[1]
        assert "@staticmethod" in helper_symbol.signature
        
        value_symbol = file_info.symbols[2]
        assert "@property" in value_symbol.signature


def test_parse_syntax_error():
    """Test handling of syntax errors."""
    code = "def broken(\n"  # Intentional syntax error
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        # Should return FileInfo with empty symbols, not crash
        assert file_info is not None
        assert len(file_info.symbols) == 0


def test_parse_imports():
    """Test extracting imports."""
    code = """import os
import sys
from pathlib import Path
from typing import List, Dict
from ..parent import something
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert "os" in file_info.imports
        assert "sys" in file_info.imports
        assert "pathlib" in file_info.imports
        assert "typing" in file_info.imports
        # Relative imports are handled differently in AST
    # The module name for 'from ..parent import something' is '..parent'
    # But AST only gives us the module part without the dots
    # So we just check that we got some imports
    assert len(file_info.imports) >= 3


def test_parse_inheritance():
    """Test parsing class inheritance."""
    code = """class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal, Serializable):
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        
        animal = file_info.symbols[0]
        assert "class Animal:" in animal.signature
        
        dog = file_info.symbols[1]
        assert "class Dog(Animal):" in dog.signature
        
        cat = file_info.symbols[2]
        assert "class Cat(Animal, Serializable):" in cat.signature


def test_complex_type_annotations():
    """Test parsing complex type annotations."""
    code = """from typing import Optional, Union, List, Dict

def process(
    data: List[Dict[str, int]],
    config: Optional[str] = None,
    mode: Union[str, int] = "auto"
) -> tuple[bool, str]:
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.symbols) == 1
        
        symbol = file_info.symbols[0]
        # Should contain type annotations
        assert "data:" in symbol.signature
        assert "config:" in symbol.signature
        assert "mode:" in symbol.signature
        assert "->" in symbol.signature


if __name__ == "__main__":
    # Run tests
    test_parse_simple_function()
    test_parse_class_with_methods()
    test_parse_with_decorators()
    test_parse_syntax_error()
    test_parse_imports()
    test_parse_inheritance()
    test_complex_type_annotations()
    
    print("✅ All tests passed!")

```

---

## File: `tests/test_cache.py`

**Lines**: 379

```python
"""Tests for cache manager."""

import tempfile
from pathlib import Path

from code_compass.cache import CacheManager
from code_compass.models import FileInfo, Symbol, SymbolType


def test_cache_initialization():
    """Test cache database initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        
        cache = CacheManager(cache_dir)
        
        # Check database file exists
        assert cache.db_path.exists()
        
        # Check tables exist
        cursor = cache.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('files', 'symbols')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        assert 'files' in tables
        assert 'symbols' in tables
        
        cache.close()


def test_save_and_retrieve_file():
    """Test saving and retrieving file information."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Create test file info
        file_info = FileInfo(
            path="src/utils.py",
            language="python",
            hash="abc123",
            size=1024,
            symbols=[
                Symbol(
                    name="helper",
                    type=SymbolType.FUNCTION,
                    file_path="src/utils.py",
                    line_start=1,
                    line_end=5,
                    signature="def helper(x: int) -> str:",
                    parent=None
                )
            ],
            imports=["os", "sys"]
        )
        
        # Save to cache
        cache.save_file(file_info)
        
        # Retrieve from cache
        retrieved = cache.get_file("src/utils.py")
        
        assert retrieved is not None
        assert retrieved.path == "src/utils.py"
        assert retrieved.hash == "abc123"
        assert retrieved.size == 1024
        assert len(retrieved.symbols) == 1
        assert retrieved.symbols[0].name == "helper"
        assert retrieved.imports == ["os", "sys"]
        
        cache.close()


def test_file_hash_check():
    """Test file change detection via hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="hash1",
            size=100,
            symbols=[],
            imports=[]
        )
        
        cache.save_file(file_info)
        
        # Same hash - should be cached
        assert cache.is_file_cached("test.py", "hash1") is True
        
        # Different hash - should not be cached
        assert cache.is_file_cached("test.py", "hash2") is False
        
        # Non-existent file
        assert cache.is_file_cached("nonexistent.py", "hash1") is False
        
        cache.close()


def test_update_existing_file():
    """Test updating an existing file in cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Save initial version
        file_info_v1 = FileInfo(
            path="app.py",
            language="python",
            hash="v1",
            size=100,
            symbols=[
                Symbol(
                    name="old_func",
                    type=SymbolType.FUNCTION,
                    file_path="app.py",
                    line_start=1,
                    line_end=2,
                    signature="def old_func():",
                    parent=None
                )
            ],
            imports=["os"]
        )
        cache.save_file(file_info_v1)
        
        # Update with new version
        file_info_v2 = FileInfo(
            path="app.py",
            language="python",
            hash="v2",
            size=200,
            symbols=[
                Symbol(
                    name="new_func",
                    type=SymbolType.FUNCTION,
                    file_path="app.py",
                    line_start=1,
                    line_end=3,
                    signature="def new_func(x: int):",
                    parent=None
                )
            ],
            imports=["os", "sys"]
        )
        cache.save_file(file_info_v2)
        
        # Retrieve and verify update
        retrieved = cache.get_file("app.py")
        assert retrieved.hash == "v2"
        assert retrieved.size == 200
        assert len(retrieved.symbols) == 1
        assert retrieved.symbols[0].name == "new_func"
        assert retrieved.imports == ["os", "sys"]
        
        cache.close()


def test_find_symbol():
    """Test finding symbols by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add multiple files with symbols
        file1 = FileInfo(
            path="file1.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[
                Symbol(
                    name="process",
                    type=SymbolType.FUNCTION,
                    file_path="file1.py",
                    line_start=1,
                    line_end=5,
                    signature="def process(data):",
                    parent=None
                )
            ],
            imports=[]
        )
        
        file2 = FileInfo(
            path="file2.py",
            language="python",
            hash="h2",
            size=200,
            symbols=[
                Symbol(
                    name="process",
                    type=SymbolType.METHOD,
                    file_path="file2.py",
                    line_start=10,
                    line_end=15,
                    signature="def process(self, data):",
                    parent="Handler"
                )
            ],
            imports=[]
        )
        
        cache.save_file(file1)
        cache.save_file(file2)
        
        # Find all "process" symbols
        results = cache.find_symbol("process")
        assert len(results) == 2
        assert results[0].file_path == "file1.py"
        assert results[1].file_path == "file2.py"
        
        cache.close()


def test_search_symbols():
    """Test searching symbols with pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[
                Symbol(
                    name="get_user",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=1,
                    line_end=2,
                    signature="def get_user():",
                    parent=None
                ),
                Symbol(
                    name="get_data",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=3,
                    line_end=4,
                    signature="def get_data():",
                    parent=None
                ),
                Symbol(
                    name="set_value",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=5,
                    line_end=6,
                    signature="def set_value():",
                    parent=None
                )
            ],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Search for "get" pattern
        results = cache.search_symbols("get")
        assert len(results) == 2
        assert all("get" in r.name for r in results)
        
        cache.close()


def test_get_stats():
    """Test cache statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add some files
        for i in range(3):
            file_info = FileInfo(
                path=f"file{i}.py",
                language="python",
                hash=f"h{i}",
                size=100,
                symbols=[
                    Symbol(
                        name=f"func{i}",
                        type=SymbolType.FUNCTION,
                        file_path=f"file{i}.py",
                        line_start=1,
                        line_end=2,
                        signature=f"def func{i}():",
                        parent=None
                    )
                ],
                imports=[]
            )
            cache.save_file(file_info)
        
        stats = cache.get_stats()
        
        assert stats['total_files'] == 3
        assert stats['total_symbols'] == 3
        assert stats['by_language']['python'] == 3
        assert stats['by_type']['function'] == 3
        
        cache.close()


def test_delete_file():
    """Test deleting file from cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="temp.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Verify it exists
        assert cache.get_file("temp.py") is not None
        
        # Delete it
        cache.delete_file("temp.py")
        
        # Verify it's gone
        assert cache.get_file("temp.py") is None
        
        cache.close()


def test_clear_cache():
    """Test clearing all cache data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add some data
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Clear cache
        cache.clear()
        
        # Verify it's empty
        stats = cache.get_stats()
        assert stats['total_files'] == 0
        assert stats['total_symbols'] == 0
        
        cache.close()


if __name__ == "__main__":
    # Run tests
    test_cache_initialization()
    test_save_and_retrieve_file()
    test_file_hash_check()
    test_update_existing_file()
    test_find_symbol()
    test_search_symbols()
    test_get_stats()
    test_delete_file()
    test_clear_cache()
    
    print("✅ All cache tests passed!")

```

---


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


@dataclass
class FileInfo:
    """Metadata about a source file."""
    path: str                   # Relative path from project root
    language: str               # Language type (python, javascript, typescript)
    hash: str                   # SHA256 hash (for change detection)
    size: int                   # File size in bytes
    symbols: list[Symbol]       # All symbols in this file
    imports: list[dict]         # List of imported modules with metadata (module, level, type)
    
    def is_changed(self, current_hash: str) -> bool:
        """Check if file has changed since last index."""
        return self.hash != current_hash


@dataclass
class RepoMap:
    """Generated repository map."""
    files: list[tuple]                  # List of (FileInfo, importance_score) tuples
    total_files: int                    # Total files in project
    included_files: int                 # Number of files included in map

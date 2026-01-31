"""Code Compass - Fast code map generator for AI coding assistants."""

__version__ = "0.1.2"

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

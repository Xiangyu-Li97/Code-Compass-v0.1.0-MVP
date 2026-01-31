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
        
        # Handle edge case: no files or single file with no imports
        if not all_files:
            return {}
        
        if len(all_files) == 1:
            # Single file: return score 1.0
            return {list(all_files)[0]: 1.0}
        
        # Check if there are any edges at all
        has_edges = any(len(deps) > 0 for deps in self.edges.values())
        if not has_edges:
            # No imports: all files have equal importance
            return {file: 1.0 for file in all_files}
        
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
        """Convert file path to module name.
        
        Examples:
            __init__.py -> (empty string, represents package root)
            exceptions.py -> exceptions
            subdir/__init__.py -> subdir
            subdir/utils.py -> subdir.utils
        """
        # Remove file extension
        path = file_path.replace(".py", "").replace(".js", "").replace(".ts", "")
        
        # Handle __init__ files - they represent the package itself
        if path.endswith("/__init__"):
            # subdir/__init__ -> subdir
            path = path[:-9]  # Remove "/__init__"
        elif path == "__init__":
            # Root __init__.py -> empty string (package root)
            return ""
        
        # Convert path separators to dots
        return path.replace("/", ".")
    
    def _resolve_import(self, import_info: dict, from_file: str) -> Optional[str]:
        """
        Resolve imported module to file path.
        
        Args:
            import_info: Dict with 'module', 'level', 'type' keys
            from_file: The file doing the importing
            
        Returns:
            Resolved file path or None if not found/external
        """
        module_name = import_info['module']
        level = import_info['level']
        
        # Case 1: Absolute import (level=0)
        if level == 0:
            # Direct lookup
            if module_name in self.module_to_file:
                return self.module_to_file[module_name]
            
            # Try partial matches (e.g., "utils" might match "src.utils")
            for mod, file in self.module_to_file.items():
                if mod.endswith("." + module_name) or mod == module_name:
                    return file
            
            # Standard library or external package - ignore
            return None
        
        # Case 2: Relative import (level > 0)
        # Calculate the base package based on the importing file's location
        from_path = Path(from_file)
        from_module = self._file_to_module(from_file)
        
        # Special case: if from_module is empty string (root __init__.py)
        # then we're in the package root
        if from_module == "":
            # from . import x in __init__.py means import from same package
            if level == 1:
                # from . import exceptions -> exceptions
                base_parts = []
            else:
                # Can't go up from root
                return None
        else:
            # Split module into parts
            parts = from_module.split('.') if from_module else []
            
            # Go up 'level' directories
            # level=1: from . import x (current package)
            # level=2: from .. import x (parent package)
            if level > len(parts):
                # Can't go up that many levels - invalid import
                return None
            
            # Remove filename and go up (level-1) more directories
            # For level=1, we stay in the same package (remove 0 parts)
            base_parts = parts[:-(level-1)] if level > 1 else parts
        
        # Add the imported module name if present
        if module_name:
            resolved_module = '.'.join(base_parts + [module_name])
        else:
            # "from . import x" - just the base package
            resolved_module = '.'.join(base_parts)
        
        # Look up in our mapping
        if resolved_module in self.module_to_file:
            return self.module_to_file[resolved_module]
        
        # Try to find __init__.py in the package
        init_module = resolved_module + '.__init__'
        if init_module in self.module_to_file:
            return self.module_to_file[init_module]
        
        return None

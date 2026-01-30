"""Map generator for creating repository maps."""

import hashlib
from pathlib import Path
from typing import Optional
from code_compass.models import FileInfo, RepoMap
from code_compass.parsers import PythonParser
from code_compass.cache import CacheManager
from code_compass.graph import DependencyBuilder
from code_compass.formatter import RepoMapFormatter, SymbolFormatter


class MapGenerator:
    """Generate repository maps with configurable options."""
    
    def __init__(self, project_root: Path, cache_dir: Optional[Path] = None):
        """
        Initialize map generator.
        
        Args:
            project_root: Root directory of the project
            cache_dir: Directory for cache storage (default: project_root/.code-compass)
        """
        self.project_root = Path(project_root).resolve()
        
        if cache_dir is None:
            cache_dir = self.project_root / ".code-compass"
        
        self.cache_dir = Path(cache_dir)
        self.cache = CacheManager(self.cache_dir)
        self.parser = PythonParser()
    
    def index(self, force: bool = False) -> dict:
        """
        Index all Python files in the project.
        
        Args:
            force: If True, re-index all files even if cached
        
        Returns:
            Statistics about the indexing process
        """
        # Find all Python files
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)]
        py_files = [f for f in py_files if ".code-compass" not in str(f)]
        
        stats = {
            'total_files': len(py_files),
            'parsed_files': 0,
            'cached_files': 0,
            'failed_files': 0,
            'total_symbols': 0,
            'total_imports': 0
        }
        
        for py_file in py_files:
            try:
                # Check if file is cached and unchanged
                if not force:
                    # Get current file hash
                    content = py_file.read_text(encoding='utf-8')
                    current_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Check cache
                    rel_path = str(py_file.relative_to(self.project_root))
                    if self.cache.is_file_cached(rel_path, current_hash):
                        stats['cached_files'] += 1
                        cached_file = self.cache.get_file(rel_path)
                        if cached_file:
                            stats['total_symbols'] += len(cached_file.symbols)
                            stats['total_imports'] += len(cached_file.imports)
                        continue
                
                # Parse file
                file_info = self.parser.parse_file(py_file, self.project_root)
                
                if file_info:
                    # Save to cache
                    self.cache.save_file(file_info)
                    stats['parsed_files'] += 1
                    stats['total_symbols'] += len(file_info.symbols)
                    stats['total_imports'] += len(file_info.imports)
                else:
                    stats['failed_files'] += 1
                    
            except Exception as e:
                print(f"⚠️  Error indexing {py_file}: {e}")
                stats['failed_files'] += 1
        
        return stats
    
    def generate_map(
        self,
        top_percent: float = 0.2,
        max_symbols_per_file: int = 50,
        format: str = 'text'
    ) -> str:
        """
        Generate repository map.
        
        Args:
            top_percent: Percentage of top files to include (0.0-1.0)
            max_symbols_per_file: Maximum symbols to show per file
            format: Output format ('text' or 'json')
        
        Returns:
            Repository map as string
        """
        # Get all files from cache
        all_files = self.cache.get_all_files()
        
        if not all_files:
            return "No files indexed. Run 'code-compass index' first."
        
        # Build dependency graph
        builder = DependencyBuilder(self.project_root)
        graph = builder.build(all_files)
        
        # Compute importance
        importance = graph.compute_importance()
        
        # Sort by importance
        sorted_files = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Select top files
        top_count = max(1, int(len(all_files) * top_percent))
        top_files = sorted_files[:top_count]
        
        # Create RepoMap
        repo_map = RepoMap(
            files=[],
            total_files=len(all_files),
            included_files=top_count
        )
        
        for file_path, score in top_files:
            file_info = next((f for f in all_files if f.path == file_path), None)
            if file_info:
                # Limit symbols per file
                limited_file = FileInfo(
                    path=file_info.path,
                    language=file_info.language,
                    hash=file_info.hash,
                    size=file_info.size,
                    symbols=file_info.symbols[:max_symbols_per_file],
                    imports=file_info.imports
                )
                repo_map.files.append((limited_file, score))
        
        # Format output
        formatter = RepoMapFormatter()
        if format == 'json':
            return formatter.to_json(repo_map)
        else:
            return formatter.to_text(repo_map)
    
    def find_symbol(self, name: str, fuzzy: bool = False) -> list[tuple[FileInfo, str]]:
        """
        Find symbols by name.
        
        Args:
            name: Symbol name to search for
            fuzzy: If True, use fuzzy matching
        
        Returns:
            List of (FileInfo, symbol_name) tuples
        """
        if fuzzy:
            symbols = self.cache.search_symbols(name)
        else:
            symbols = self.cache.find_symbol(name)
        
        results = []
        for symbol in symbols:
            # Get file info
            file_info = self.cache.get_file(symbol.file_path)
            if file_info:
                results.append((file_info, symbol.name))
        
        return results
    
    def get_stats(self) -> dict:
        """Get indexing statistics."""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
    
    def close(self):
        """Close cache connection."""
        self.cache.close()

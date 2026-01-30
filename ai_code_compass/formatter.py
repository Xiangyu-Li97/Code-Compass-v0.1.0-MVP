"""Formatters for converting data models to various output formats."""

import json
from .models import Symbol, RepoMap, SymbolType


class RepoMapFormatter:
    """Format RepoMap to different output formats."""
    
    @staticmethod
    def to_text(repo_map: RepoMap) -> str:
        """
        Convert RepoMap to text format (similar to Aider).
        
        Format:
            # Repository Map (Top N files, X%)
            
            ## file/path.py (importance: 1.234)
            ⋮...
            │class ClassName:
            │  def method(self, arg: str) -> None:
            ⋮...
        """
        lines = []
        lines.append(f"# Repository Map (Top {repo_map.included_files} files, {repo_map.included_files/repo_map.total_files*100:.0f}%)\n")
        
        for file_info, score in repo_map.files:
            lines.append(f"\n## {file_info.path} (importance: {score:.3f})")
            lines.append("⋮...")
            for symbol in file_info.symbols:
                lines.append(SymbolFormatter.to_map_line(symbol))
            if len(file_info.symbols) > 0:
                lines.append("⋮...")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_json(repo_map: RepoMap) -> str:
        """
        Convert RepoMap to JSON format.
        
        Returns a JSON string.
        """
        data = {
            'total_files': repo_map.total_files,
            'included_files': repo_map.included_files,
            'files': []
        }
        
        for file_info, score in repo_map.files:
            file_data = {
                'path': file_info.path,
                'importance': score,
                'symbols': [SymbolFormatter.to_dict(s) for s in file_info.symbols]
            }
            data['files'].append(file_data)
        
        return json.dumps(data, indent=2)


class SymbolFormatter:
    """Format Symbol to different output formats."""
    
    @staticmethod
    def to_map_line(symbol: Symbol) -> str:
        """
        Convert Symbol to a single line in the repo map.
        
        Args:
            symbol: The symbol to format
            
        Returns:
            Formatted line with appropriate indentation
        """
        indent = "│  " if symbol.parent else "│"
        return f"{indent}{symbol.signature}"
    
    @staticmethod
    def to_dict(symbol: Symbol) -> dict:
        """
        Convert Symbol to a dictionary.
        
        Returns:
            Dictionary representation of the symbol
        """
        return {
            'name': symbol.name,
            'type': symbol.type.value,
            'file_path': symbol.file_path,
            'line_start': symbol.line_start,
            'line_end': symbol.line_end,
            'signature': symbol.signature,
            'parent': symbol.parent
        }
    
    @staticmethod
    def to_text(symbol: Symbol) -> str:
        """
        Convert Symbol to human-readable text.
        
        Returns:
            Human-readable string representation
        """
        parent_info = f" (in {symbol.parent})" if symbol.parent else ""
        location = f"{symbol.file_path}:{symbol.line_start}"
        return f"{symbol.type.value.capitalize()} {symbol.name}{parent_info} @ {location}\n  {symbol.signature}"

"""Export all code for review."""

from pathlib import Path

def export_code():
    """Export all Python files with headers."""
    
    project_root = Path(__file__).parent
    output_file = project_root / "CODE_EXPORT_FOR_REVIEW.md"
    
    # Files to export in order
    files = [
        "code_compass/models.py",
        "code_compass/graph.py",
        "code_compass/parsers/python_parser.py",
        "code_compass/cache.py",
        "code_compass/cli.py",
        "code_compass/__init__.py",
        "code_compass/__main__.py",
        "code_compass/parsers/__init__.py",
        "tests/test_python_parser.py",
        "tests/test_cache.py",
    ]
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# Code Compass - Complete Code Export for Review\n\n")
        out.write("## Project Structure\n\n")
        out.write("```\n")
        out.write("code-compass/\n")
        out.write("├── code_compass/\n")
        out.write("│   ├── __init__.py\n")
        out.write("│   ├── __main__.py\n")
        out.write("│   ├── models.py          # Core data structures\n")
        out.write("│   ├── graph.py           # Dependency graph & PageRank\n")
        out.write("│   ├── cache.py           # SQLite caching layer\n")
        out.write("│   ├── cli.py             # Command-line interface\n")
        out.write("│   └── parsers/\n")
        out.write("│       ├── __init__.py\n")
        out.write("│       └── python_parser.py  # Python AST parser\n")
        out.write("├── tests/\n")
        out.write("│   ├── test_python_parser.py\n")
        out.write("│   └── test_cache.py\n")
        out.write("├── pyproject.toml\n")
        out.write("├── README.md\n")
        out.write("└── LICENSE\n")
        out.write("```\n\n")
        
        out.write("## Statistics\n\n")
        
        total_lines = 0
        total_files = 0
        
        for file_path in files:
            full_path = project_root / file_path
            if full_path.exists():
                lines = len(full_path.read_text().splitlines())
                total_lines += lines
                total_files += 1
        
        out.write(f"- **Total Files**: {total_files}\n")
        out.write(f"- **Total Lines**: {total_lines}\n")
        out.write(f"- **Language**: Python 3.11+\n")
        out.write(f"- **Dependencies**: click (CLI), sqlite3 (built-in)\n\n")
        
        out.write("---\n\n")
        
        # Export each file
        for file_path in files:
            full_path = project_root / file_path
            
            if not full_path.exists():
                continue
            
            out.write(f"## File: `{file_path}`\n\n")
            out.write(f"**Lines**: {len(full_path.read_text().splitlines())}\n\n")
            out.write("```python\n")
            out.write(full_path.read_text())
            out.write("\n```\n\n")
            out.write("---\n\n")
    
    print(f"✅ Code exported to: {output_file}")
    print(f"📊 Total: {total_files} files, {total_lines} lines")

if __name__ == "__main__":
    export_code()

"""Test on real project (Code Compass itself)."""

import tempfile
from pathlib import Path

from ai_code_compass.parsers import PythonParser
from ai_code_compass.cache import CacheManager
from ai_code_compass.graph import DependencyBuilder


def test_parse_code_compass():
    """Test parsing Code Compass's own codebase."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code_compass"
    
    print(f"\n📂 Project root: {project_root}")
    print(f"📂 Code directory: {code_dir}")
    
    parser = PythonParser()
    files = []
    errors = []
    
    # Parse all Python files in code_compass/
    for py_file in code_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        print(f"\n  Parsing: {py_file.relative_to(project_root)}")
        
        try:
            file_info = parser.parse_file(py_file, project_root)
            if file_info:
                files.append(file_info)
                print(f"    ✅ {len(file_info.symbols)} symbols, {len(file_info.imports)} imports")
                
                # Show some symbols
                for symbol in file_info.symbols[:3]:
                    print(f"       - {symbol.type.value}: {symbol.name}")
                if len(file_info.symbols) > 3:
                    print(f"       ... and {len(file_info.symbols) - 3} more")
                
                # Show some imports
                if file_info.imports:
                    print(f"    📦 Imports:")
                    for imp in file_info.imports[:3]:
                        level_str = f"level={imp['level']}" if imp['level'] > 0 else "absolute"
                        print(f"       - {imp['module'] or '(current package)'} ({level_str})")
                    if len(file_info.imports) > 3:
                        print(f"       ... and {len(file_info.imports) - 3} more")
            else:
                errors.append((py_file, "Returned None"))
        except Exception as e:
            errors.append((py_file, str(e)))
            print(f"    ❌ Error: {e}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total files parsed: {len(files)}")
    print(f"   Total symbols: {sum(len(f.symbols) for f in files)}")
    print(f"   Total imports: {sum(len(f.imports) for f in files)}")
    print(f"   Errors: {len(errors)}")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for file, error in errors:
            print(f"   - {file}: {error}")
    
    # Must not crash and must parse at least some files
    assert len(files) > 0, "No files were parsed"
    assert len(errors) == 0, f"Encountered {len(errors)} errors"
    
    return files


def test_build_dependency_graph():
    """Test building dependency graph for Code Compass."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code_compass"
    
    print(f"\n🔗 Building dependency graph...")
    
    # Parse all files
    parser = PythonParser()
    files = []
    for py_file in code_dir.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            file_info = parser.parse_file(py_file, project_root)
            if file_info:
                files.append(file_info)
    
    # Build graph
    builder = DependencyBuilder(project_root)
    graph = builder.build(files)
    
    # Check that we have edges
    total_edges = sum(len(deps) for deps in graph.edges.values())
    print(f"   Total dependency edges: {total_edges}")
    
    # Compute importance
    importance = graph.compute_importance()
    
    # Show top 5 most important files
    sorted_files = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n   Top 5 most important files:")
    for file, score in sorted_files[:5]:
        print(f"      {score:.2f} - {file}")
    
    assert total_edges > 0, "No dependency edges found"
    assert len(importance) > 0, "No importance scores computed"


def test_cache_real_project():
    """Test caching Code Compass codebase."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code_compass"
    
    print(f"\n💾 Testing cache on real project...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Parse and cache all files
        parser = PythonParser()
        for py_file in code_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                file_info = parser.parse_file(py_file, project_root)
                if file_info:
                    cache.save_file(file_info)
        
        # Get stats
        stats = cache.get_stats()
        print(f"   Files cached: {stats['total_files']}")
        print(f"   Symbols cached: {stats['total_symbols']}")
        
        # Test retrieval
        first_file = cache.get_all_files()[0]
        retrieved = cache.get_file(first_file.path)
        assert retrieved is not None
        print(f"   ✅ Successfully retrieved: {retrieved.path}")
        
        # Test search
        results = cache.find_symbol("Parser")
        print(f"   Found {len(results)} symbols matching 'Parser'")
        
        cache.close()
        
        assert stats['total_files'] > 0
        assert stats['total_symbols'] > 0


def test_relative_imports_in_real_code():
    """Test that relative imports in Code Compass are parsed correctly."""
    project_root = Path(__file__).parent.parent
    
    # parsers/__init__.py should have relative imports
    parsers_init = project_root / "code_compass" / "parsers" / "__init__.py"
    
    if parsers_init.exists():
        parser = PythonParser()
        file_info = parser.parse_file(parsers_init, project_root)
        
        print(f"\n🔍 Checking relative imports in parsers/__init__.py:")
        
        if file_info and file_info.imports:
            relative_imports = [imp for imp in file_info.imports if imp['level'] > 0]
            print(f"   Found {len(relative_imports)} relative imports")
            for imp in relative_imports:
                print(f"      level={imp['level']}, module={imp['module']}")
            
            # Should have at least one relative import
            assert len(relative_imports) > 0, "Expected relative imports in parsers/__init__.py"
        else:
            print("   ⚠️  No imports found (file might be empty)")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Code Compass on itself")
    print("=" * 60)
    
    # Run tests
    files = test_parse_code_compass()
    test_build_dependency_graph()
    test_cache_real_project()
    test_relative_imports_in_real_code()
    
    print("\n" + "=" * 60)
    print("✅ All real project tests passed!")
    print("=" * 60)

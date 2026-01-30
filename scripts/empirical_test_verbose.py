"""Empirical testing with verbose output to show intermediate steps."""

import time
import tempfile
from pathlib import Path
from ai_code_compass.parsers import PythonParser
from ai_code_compass.cache import CacheManager
from ai_code_compass.graph import DependencyBuilder
from ai_code_compass.formatter import SymbolFormatter


def count_tokens_rough(text: str) -> int:
    """Rough token count (1 token ≈ 4 characters for English)."""
    return len(text) // 4


def test_project_verbose(project_path: Path, project_name: str, max_files_to_show=5):
    """Test Code Compass on a real project with verbose output."""
    print(f"\n{'='*80}")
    print(f"Testing: {project_name}")
    print(f"Path: {project_path}")
    print(f"{'='*80}\n")
    
    # Find all Python files
    py_files = list(project_path.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f) and ".tox" not in str(f)]
    
    print(f"📂 Found {len(py_files)} Python files:")
    for i, f in enumerate(py_files[:10], 1):
        print(f"   {i}. {f.relative_to(project_path)}")
    if len(py_files) > 10:
        print(f"   ... and {len(py_files) - 10} more")
    
    # Parse all files
    parser = PythonParser()
    parsed_files = []
    failed_files = []
    
    print(f"\n{'─'*80}")
    print(f"🔍 STEP 1: Parsing files")
    print(f"{'─'*80}\n")
    
    start_time = time.time()
    
    for i, py_file in enumerate(py_files[:max_files_to_show], 1):
        print(f"📄 File {i}/{len(py_files)}: {py_file.relative_to(project_path)}")
        try:
            file_info = parser.parse_file(py_file, project_path)
            if file_info:
                parsed_files.append(file_info)
                print(f"   ✅ Success: {len(file_info.symbols)} symbols, {len(file_info.imports)} imports")
                
                # Show first 3 symbols
                if file_info.symbols:
                    print(f"   📦 Symbols:")
                    for symbol in file_info.symbols[:3]:
                        print(f"      • {symbol.type.value}: {symbol.name}")
                    if len(file_info.symbols) > 3:
                        print(f"      ... and {len(file_info.symbols) - 3} more")
                
                # Show first 3 imports
                if file_info.imports:
                    print(f"   🔗 Imports:")
                    for imp in file_info.imports[:3]:
                        level_str = f"level={imp['level']}" if imp['level'] > 0 else "absolute"
                        module = imp['module'] or '(current package)'
                        print(f"      • {module} ({level_str})")
                    if len(file_info.imports) > 3:
                        print(f"      ... and {len(file_info.imports) - 3} more")
            else:
                failed_files.append((py_file, "Returned None"))
                print(f"   ❌ Failed: Returned None")
        except Exception as e:
            failed_files.append((py_file, str(e)))
            print(f"   ❌ Failed: {str(e)[:100]}")
        print()
    
    # Parse remaining files silently
    if len(py_files) > max_files_to_show:
        print(f"⏩ Parsing remaining {len(py_files) - max_files_to_show} files silently...")
        for py_file in py_files[max_files_to_show:]:
            try:
                file_info = parser.parse_file(py_file, project_path)
                if file_info:
                    parsed_files.append(file_info)
                else:
                    failed_files.append((py_file, "Returned None"))
            except Exception as e:
                failed_files.append((py_file, str(e)))
        print(f"   ✅ Done\n")
    
    parse_time = time.time() - start_time
    
    # Statistics
    total_symbols = sum(len(f.symbols) for f in parsed_files)
    total_imports = sum(len(f.imports) for f in parsed_files)
    success_rate = len(parsed_files) / len(py_files) * 100 if py_files else 0
    
    print(f"{'─'*80}")
    print(f"📊 Parsing Summary:")
    print(f"{'─'*80}")
    print(f"   ✅ Successfully parsed: {len(parsed_files)}/{len(py_files)} ({success_rate:.1f}%)")
    print(f"   ❌ Failed to parse: {len(failed_files)}")
    print(f"   ⏱️  Total time: {parse_time:.2f}s")
    print(f"   ⚡ Speed: {len(py_files)/parse_time:.1f} files/s")
    print(f"   📦 Total symbols: {total_symbols}")
    print(f"   🔗 Total imports: {total_imports}")
    
    if failed_files:
        print(f"\n   ❌ Failed files:")
        for file, error in failed_files:
            print(f"      • {file.relative_to(project_path)}: {error[:80]}")
    
    # Build dependency graph
    print(f"\n{'─'*80}")
    print(f"🔗 STEP 2: Building dependency graph")
    print(f"{'─'*80}\n")
    
    start_time = time.time()
    builder = DependencyBuilder(project_path)
    
    print(f"📋 Module to file mapping:")
    for module, file in list(builder.module_to_file.items())[:10]:
        print(f"   {module} → {Path(file).relative_to(project_path)}")
    if len(builder.module_to_file) > 10:
        print(f"   ... and {len(builder.module_to_file) - 10} more")
    
    print(f"\n🔨 Building graph...")
    graph = builder.build(parsed_files)
    graph_time = time.time() - start_time
    
    total_edges = sum(len(deps) for deps in graph.edges.values())
    print(f"   ✅ Built graph in {graph_time:.2f}s")
    print(f"   📊 Total edges: {total_edges}")
    
    # Show some edges
    if total_edges > 0:
        print(f"\n   🔗 Sample edges (first 10):")
        count = 0
        for file, deps in graph.edges.items():
            if deps and count < 10:
                rel_file = Path(file).relative_to(project_path) if project_path in Path(file).parents else file
                print(f"      {rel_file} →")
                for dep in list(deps)[:3]:
                    rel_dep = Path(dep).relative_to(project_path) if project_path in Path(dep).parents else dep
                    print(f"         • {rel_dep}")
                if len(deps) > 3:
                    print(f"         ... and {len(deps) - 3} more")
                count += 1
    else:
        print(f"\n   ⚠️  No edges found! This might indicate a problem with import resolution.")
        print(f"   🔍 Debugging: Let's check some imports...")
        for file_info in parsed_files[:3]:
            print(f"\n   📄 {file_info.path}")
            print(f"      Imports: {file_info.imports}")
            for imp in file_info.imports[:3]:
                # file_info.path is already relative to project_root
                full_path = project_path / file_info.path
                resolved = builder._resolve_import(imp, str(full_path))
                print(f"         {imp['module']} (level={imp['level']}) → {resolved}")
    
    # Compute importance
    print(f"\n{'─'*80}")
    print(f"⭐ STEP 3: Computing file importance (PageRank)")
    print(f"{'─'*80}\n")
    
    start_time = time.time()
    importance = graph.compute_importance()
    rank_time = time.time() - start_time
    print(f"   ✅ Computed in {rank_time:.2f}s")
    
    # Show top 10 most important files
    sorted_files = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n   📊 Top 10 most important files:")
    for i, (file, score) in enumerate(sorted_files[:10], 1):
        rel_path = Path(file).relative_to(project_path) if project_path in Path(file).parents else file
        print(f"      {i:2}. {score:.3f} - {rel_path}")
    
    # Generate sample repo map
    print(f"\n{'─'*80}")
    print(f"🗺️  STEP 4: Generating sample repo map (top 3 files)")
    print(f"{'─'*80}\n")
    
    for i, (file, score) in enumerate(sorted_files[:3], 1):
        file_info = next((f for f in parsed_files if f.path == file), None)
        if file_info:
            rel_path = Path(file).relative_to(project_path) if project_path in Path(file).parents else file
            print(f"📄 {rel_path} (importance: {score:.3f})")
            print(f"⋮...")
            for symbol in file_info.symbols[:5]:
                line = SymbolFormatter.to_map_line(symbol)
                print(f"{line}")
            if len(file_info.symbols) > 5:
                print(f"⋮... and {len(file_info.symbols) - 5} more symbols")
            print()
    
    # Token analysis
    print(f"{'─'*80}")
    print(f"💰 STEP 5: Token Analysis")
    print(f"{'─'*80}\n")
    
    # Count tokens in original files
    original_tokens = 0
    for py_file in py_files[:len(parsed_files)]:
        try:
            content = py_file.read_text(encoding='utf-8')
            original_tokens += count_tokens_rough(content)
        except:
            pass
    
    # Count tokens in signatures only
    signature_tokens = 0
    for file_info in parsed_files:
        for symbol in file_info.symbols:
            signature_tokens += count_tokens_rough(symbol.signature)
    
    # Count tokens in a hypothetical repo map (top 20% files)
    top_20_percent = int(len(parsed_files) * 0.2) or 1
    map_files = sorted_files[:top_20_percent]
    map_tokens = 0
    for file, _ in map_files:
        file_info = next((f for f in parsed_files if f.path == file), None)
        if file_info:
            for symbol in file_info.symbols:
                map_tokens += count_tokens_rough(symbol.signature)
            map_tokens += 20  # File header overhead
    
    print(f"   📄 Original code: ~{original_tokens:,} tokens")
    print(f"   ✂️  All signatures: ~{signature_tokens:,} tokens ({signature_tokens/original_tokens*100:.1f}% of original)")
    print(f"   🗺️  Repo map (top {top_20_percent} files, 20%): ~{map_tokens:,} tokens ({map_tokens/original_tokens*100:.1f}% of original)")
    print(f"   💾 Token savings: ~{original_tokens - map_tokens:,} tokens ({(1-map_tokens/original_tokens)*100:.1f}% reduction)")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY for {project_name}")
    print(f"{'='*80}")
    print(f"Files: {len(py_files)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Parse speed: {len(py_files)/parse_time:.1f} files/s")
    print(f"Symbols: {total_symbols}")
    print(f"Dependencies: {total_edges} edges")
    print(f"Token reduction: {(1-map_tokens/original_tokens)*100:.1f}%")
    print(f"{'='*80}\n")


def main():
    """Run verbose empirical tests."""
    print("\n" + "="*80)
    print("Code Compass - Empirical Validation (VERBOSE)")
    print("="*80)
    
    test_projects_dir = Path(__file__).parent / "test_projects"
    
    # Test requests (smaller project first)
    requests_path = test_projects_dir / "requests" / "src" / "requests"
    if requests_path.exists():
        test_project_verbose(requests_path, "requests", max_files_to_show=5)
    else:
        print(f"⚠️  requests not found at {requests_path}")


if __name__ == "__main__":
    main()

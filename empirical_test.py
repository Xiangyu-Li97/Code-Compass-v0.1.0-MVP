"""Empirical testing on real-world projects."""

import time
import tempfile
from pathlib import Path
from code_compass.parsers import PythonParser
from code_compass.cache import CacheManager
from code_compass.graph import DependencyBuilder
from code_compass.formatter import RepoMapFormatter


def count_tokens_rough(text: str) -> int:
    """Rough token count (1 token ≈ 4 characters for English)."""
    return len(text) // 4


def test_project(project_path: Path, project_name: str):
    """Test Code Compass on a real project."""
    print(f"\n{'='*60}")
    print(f"Testing: {project_name}")
    print(f"Path: {project_path}")
    print(f"{'='*60}\n")
    
    # Find all Python files
    py_files = list(project_path.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f) and ".tox" not in str(f)]
    
    print(f"📂 Found {len(py_files)} Python files\n")
    
    # Parse all files
    parser = PythonParser()
    parsed_files = []
    failed_files = []
    parse_errors = []
    
    print("🔍 Parsing files...")
    start_time = time.time()
    
    for py_file in py_files:
        try:
            file_info = parser.parse_file(py_file, project_path)
            if file_info:
                parsed_files.append(file_info)
            else:
                failed_files.append((py_file, "Returned None"))
        except Exception as e:
            failed_files.append((py_file, str(e)))
            parse_errors.append(str(e))
    
    parse_time = time.time() - start_time
    
    # Statistics
    total_symbols = sum(len(f.symbols) for f in parsed_files)
    total_imports = sum(len(f.imports) for f in parsed_files)
    success_rate = len(parsed_files) / len(py_files) * 100 if py_files else 0
    
    print(f"\n📊 Parsing Results:")
    print(f"   ✅ Successfully parsed: {len(parsed_files)}/{len(py_files)} ({success_rate:.1f}%)")
    print(f"   ❌ Failed to parse: {len(failed_files)}")
    print(f"   ⏱️  Total time: {parse_time:.2f}s")
    print(f"   ⚡ Speed: {len(py_files)/parse_time:.1f} files/s")
    print(f"   📦 Total symbols: {total_symbols}")
    print(f"   🔗 Total imports: {total_imports}")
    
    if failed_files:
        print(f"\n❌ Failed files (showing first 5):")
        for file, error in failed_files[:5]:
            print(f"   - {file.relative_to(project_path)}: {error[:80]}")
        if len(failed_files) > 5:
            print(f"   ... and {len(failed_files) - 5} more")
    
    # Build dependency graph
    print(f"\n🔗 Building dependency graph...")
    start_time = time.time()
    builder = DependencyBuilder(project_path)
    graph = builder.build(parsed_files)
    graph_time = time.time() - start_time
    
    total_edges = sum(len(deps) for deps in graph.edges.values())
    print(f"   ✅ Built graph in {graph_time:.2f}s")
    print(f"   📊 Total edges: {total_edges}")
    
    # Compute importance
    print(f"\n⭐ Computing file importance (PageRank)...")
    start_time = time.time()
    importance = graph.compute_importance()
    rank_time = time.time() - start_time
    print(f"   ✅ Computed in {rank_time:.2f}s")
    
    # Show top 10 most important files
    sorted_files = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n   Top 10 most important files:")
    for i, (file, score) in enumerate(sorted_files[:10], 1):
        rel_path = Path(file).relative_to(project_path) if project_path in Path(file).parents else file
        print(f"      {i:2}. {score:.3f} - {rel_path}")
    
    # Test caching
    print(f"\n💾 Testing cache performance...")
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # First write
        start_time = time.time()
        for file_info in parsed_files:
            cache.save_file(file_info)
        write_time = time.time() - start_time
        
        # Read back
        start_time = time.time()
        all_files = cache.get_all_files()
        read_time = time.time() - start_time
        
        cache.close()
        
        print(f"   ✅ Write: {len(parsed_files)} files in {write_time:.2f}s ({len(parsed_files)/write_time:.0f} files/s)")
        print(f"   ✅ Read: {len(all_files)} files in {read_time:.3f}s ({len(all_files)/read_time:.0f} files/s)")
    
    # Calculate token savings (rough estimate)
    print(f"\n💰 Token Analysis (rough estimate):")
    
    # Count tokens in original files
    original_tokens = 0
    for py_file in py_files[:len(parsed_files)]:  # Only count successfully parsed files
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
    print(f"   🗺️  Repo map (top 20% files): ~{map_tokens:,} tokens ({map_tokens/original_tokens*100:.1f}% of original)")
    print(f"   💾 Token savings: ~{original_tokens - map_tokens:,} tokens ({(1-map_tokens/original_tokens)*100:.1f}% reduction)")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary for {project_name}:")
    print(f"{'='*60}")
    print(f"Files: {len(py_files)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Parse speed: {len(py_files)/parse_time:.1f} files/s")
    print(f"Symbols: {total_symbols}")
    print(f"Dependencies: {total_edges} edges")
    print(f"Token reduction: {(1-map_tokens/original_tokens)*100:.1f}%")
    print(f"{'='*60}\n")
    
    return {
        'project_name': project_name,
        'total_files': len(py_files),
        'parsed_files': len(parsed_files),
        'failed_files': len(failed_files),
        'success_rate': success_rate,
        'parse_time': parse_time,
        'parse_speed': len(py_files)/parse_time,
        'total_symbols': total_symbols,
        'total_imports': total_imports,
        'total_edges': total_edges,
        'original_tokens': original_tokens,
        'signature_tokens': signature_tokens,
        'map_tokens': map_tokens,
        'token_reduction': (1-map_tokens/original_tokens)*100,
    }


def main():
    """Run empirical tests on real projects."""
    print("\n" + "="*60)
    print("Code Compass - Empirical Validation")
    print("="*60)
    
    test_projects_dir = Path(__file__).parent / "test_projects"
    
    results = []
    
    # Test requests
    requests_path = test_projects_dir / "requests" / "src" / "requests"
    if requests_path.exists():
        result = test_project(requests_path, "requests")
        results.append(result)
    else:
        print(f"⚠️  requests not found at {requests_path}")
    
    # Test flask
    flask_path = test_projects_dir / "flask" / "src" / "flask"
    if flask_path.exists():
        result = test_project(flask_path, "flask")
        results.append(result)
    else:
        print(f"⚠️  flask not found at {flask_path}")
    
    # Overall summary
    if results:
        print("\n" + "="*60)
        print("OVERALL SUMMARY")
        print("="*60)
        print(f"\n{'Project':<15} {'Files':<8} {'Success':<10} {'Speed':<12} {'Symbols':<10} {'Token↓':<10}")
        print("-" * 60)
        for r in results:
            print(f"{r['project_name']:<15} {r['total_files']:<8} {r['success_rate']:<9.1f}% {r['parse_speed']:<11.1f}f/s {r['total_symbols']:<10} {r['token_reduction']:<9.1f}%")
        
        # Averages
        avg_success = sum(r['success_rate'] for r in results) / len(results)
        avg_speed = sum(r['parse_speed'] for r in results) / len(results)
        avg_reduction = sum(r['token_reduction'] for r in results) / len(results)
        
        print("-" * 60)
        print(f"{'AVERAGE':<15} {'':<8} {avg_success:<9.1f}% {avg_speed:<11.1f}f/s {'':<10} {avg_reduction:<9.1f}%")
        print("="*60)
        
        # Key findings
        print("\n🔑 Key Findings:")
        print(f"   • Average success rate: {avg_success:.1f}%")
        print(f"   • Average parse speed: {avg_speed:.1f} files/s")
        print(f"   • Average token reduction: {avg_reduction:.1f}%")
        
        if avg_success < 95:
            print(f"\n⚠️  Warning: Success rate below 95% - AST parser struggles with real code")
        
        if avg_reduction < 80:
            print(f"\n⚠️  Warning: Token reduction below 80% - Map may not be efficient enough")
        else:
            print(f"\n✅ Token reduction is significant - validates core value proposition")


if __name__ == "__main__":
    main()

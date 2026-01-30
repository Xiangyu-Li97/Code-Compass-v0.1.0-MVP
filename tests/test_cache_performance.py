"""Performance tests for cache manager."""

import tempfile
import time
from pathlib import Path

from code_compass.cache import CacheManager
from code_compass.models import FileInfo, Symbol, SymbolType


def test_pragma_settings():
    """Test that PRAGMA settings are applied correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        cursor = cache.conn.cursor()
        
        # Check journal_mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal", f"Expected WAL mode, got {journal_mode}"
        
        # Check synchronous
        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]
        # NORMAL = 1, FULL = 2
        assert synchronous in (1, 2), f"Expected synchronous=1 or 2, got {synchronous}"
        
        # Check cache_size
        cursor.execute("PRAGMA cache_size")
        cache_size = cursor.fetchone()[0]
        # Should be negative (KB) and around -10000
        assert cache_size < 0, f"Expected negative cache_size, got {cache_size}"
        
        cache.close()
        print(f"✅ PRAGMA settings: journal_mode={journal_mode}, synchronous={synchronous}, cache_size={cache_size}")


def test_bulk_insert_performance():
    """Test performance of bulk inserts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Create 100 fake files with 10 symbols each
        num_files = 100
        symbols_per_file = 10
        
        start_time = time.time()
        
        for i in range(num_files):
            symbols = [
                Symbol(
                    name=f"func_{j}",
                    type=SymbolType.FUNCTION,
                    file_path=f"file_{i}.py",
                    line_start=j * 10,
                    line_end=j * 10 + 5,
                    signature=f"def func_{j}(x: int) -> str:",
                    parent=None
                )
                for j in range(symbols_per_file)
            ]
            
            file_info = FileInfo(
                path=f"file_{i}.py",
                language="python",
                hash=f"hash_{i}",
                size=1000,
                symbols=symbols,
                imports=[]
            )
            
            cache.save_file(file_info)
        
        elapsed = time.time() - start_time
        
        # Check that all files were saved
        stats = cache.get_stats()
        assert stats['total_files'] == num_files
        assert stats['total_symbols'] == num_files * symbols_per_file
        
        cache.close()
        
        # Performance expectation: Should complete in < 2 seconds
        print(f"✅ Bulk insert: {num_files} files, {num_files * symbols_per_file} symbols in {elapsed:.2f}s")
        assert elapsed < 2.0, f"Bulk insert too slow: {elapsed:.2f}s"


def test_query_performance():
    """Test query performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Insert some test data
        for i in range(50):
            file_info = FileInfo(
                path=f"file_{i}.py",
                language="python",
                hash=f"hash_{i}",
                size=1000,
                symbols=[
                    Symbol(
                        name=f"process_{i}",
                        type=SymbolType.FUNCTION,
                        file_path=f"file_{i}.py",
                        line_start=10,
                        line_end=20,
                        signature=f"def process_{i}():",
                        parent=None
                    )
                ],
                imports=[]
            )
            cache.save_file(file_info)
        
        # Test find_symbol performance
        start_time = time.time()
        for i in range(50):
            results = cache.find_symbol(f"process_{i}")
            assert len(results) == 1
        elapsed = time.time() - start_time
        
        cache.close()
        
        # Should be very fast with indexes
        print(f"✅ Query performance: 50 lookups in {elapsed:.3f}s ({elapsed/50*1000:.2f}ms per query)")
        assert elapsed < 0.5, f"Queries too slow: {elapsed:.3f}s"


def test_update_performance():
    """Test update performance (simulating incremental indexing)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Initial insert
        file_info_v1 = FileInfo(
            path="app.py",
            language="python",
            hash="v1",
            size=1000,
            symbols=[
                Symbol(
                    name="old_func",
                    type=SymbolType.FUNCTION,
                    file_path="app.py",
                    line_start=1,
                    line_end=5,
                    signature="def old_func():",
                    parent=None
                )
            ],
            imports=[]
        )
        cache.save_file(file_info_v1)
        
        # Update 100 times
        start_time = time.time()
        for i in range(100):
            file_info_v2 = FileInfo(
                path="app.py",
                language="python",
                hash=f"v{i+2}",
                size=1000,
                symbols=[
                    Symbol(
                        name=f"new_func_{i}",
                        type=SymbolType.FUNCTION,
                        file_path="app.py",
                        line_start=1,
                        line_end=5,
                        signature=f"def new_func_{i}():",
                        parent=None
                    )
                ],
                imports=[]
            )
            cache.save_file(file_info_v2)
        elapsed = time.time() - start_time
        
        # Verify final state
        final = cache.get_file("app.py")
        assert final.hash == "v101"
        
        cache.close()
        
        print(f"✅ Update performance: 100 updates in {elapsed:.2f}s ({elapsed/100*1000:.2f}ms per update)")
        assert elapsed < 1.0, f"Updates too slow: {elapsed:.2f}s"


if __name__ == "__main__":
    # Run tests
    test_pragma_settings()
    test_bulk_insert_performance()
    test_query_performance()
    test_update_performance()
    
    print("\n✅ All performance tests passed!")

"""Tests for cache manager."""

import tempfile
from pathlib import Path

from ai_code_compass.cache import CacheManager
from ai_code_compass.models import FileInfo, Symbol, SymbolType


def test_cache_initialization():
    """Test cache database initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        
        cache = CacheManager(cache_dir)
        
        # Check database file exists
        assert cache.db_path.exists()
        
        # Check tables exist
        cursor = cache.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('files', 'symbols')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        assert 'files' in tables
        assert 'symbols' in tables
        
        cache.close()


def test_save_and_retrieve_file():
    """Test saving and retrieving file information."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Create test file info
        file_info = FileInfo(
            path="src/utils.py",
            language="python",
            hash="abc123",
            size=1024,
            symbols=[
                Symbol(
                    name="helper",
                    type=SymbolType.FUNCTION,
                    file_path="src/utils.py",
                    line_start=1,
                    line_end=5,
                    signature="def helper(x: int) -> str:",
                    parent=None
                )
            ],
            imports=["os", "sys"]
        )
        
        # Save to cache
        cache.save_file(file_info)
        
        # Retrieve from cache
        retrieved = cache.get_file("src/utils.py")
        
        assert retrieved is not None
        assert retrieved.path == "src/utils.py"
        assert retrieved.hash == "abc123"
        assert retrieved.size == 1024
        assert len(retrieved.symbols) == 1
        assert retrieved.symbols[0].name == "helper"
        assert retrieved.imports == ["os", "sys"]
        
        cache.close()


def test_file_hash_check():
    """Test file change detection via hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="hash1",
            size=100,
            symbols=[],
            imports=[]
        )
        
        cache.save_file(file_info)
        
        # Same hash - should be cached
        assert cache.is_file_cached("test.py", "hash1") is True
        
        # Different hash - should not be cached
        assert cache.is_file_cached("test.py", "hash2") is False
        
        # Non-existent file
        assert cache.is_file_cached("nonexistent.py", "hash1") is False
        
        cache.close()


def test_update_existing_file():
    """Test updating an existing file in cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Save initial version
        file_info_v1 = FileInfo(
            path="app.py",
            language="python",
            hash="v1",
            size=100,
            symbols=[
                Symbol(
                    name="old_func",
                    type=SymbolType.FUNCTION,
                    file_path="app.py",
                    line_start=1,
                    line_end=2,
                    signature="def old_func():",
                    parent=None
                )
            ],
            imports=["os"]
        )
        cache.save_file(file_info_v1)
        
        # Update with new version
        file_info_v2 = FileInfo(
            path="app.py",
            language="python",
            hash="v2",
            size=200,
            symbols=[
                Symbol(
                    name="new_func",
                    type=SymbolType.FUNCTION,
                    file_path="app.py",
                    line_start=1,
                    line_end=3,
                    signature="def new_func(x: int):",
                    parent=None
                )
            ],
            imports=["os", "sys"]
        )
        cache.save_file(file_info_v2)
        
        # Retrieve and verify update
        retrieved = cache.get_file("app.py")
        assert retrieved.hash == "v2"
        assert retrieved.size == 200
        assert len(retrieved.symbols) == 1
        assert retrieved.symbols[0].name == "new_func"
        assert retrieved.imports == ["os", "sys"]
        
        cache.close()


def test_find_symbol():
    """Test finding symbols by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add multiple files with symbols
        file1 = FileInfo(
            path="file1.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[
                Symbol(
                    name="process",
                    type=SymbolType.FUNCTION,
                    file_path="file1.py",
                    line_start=1,
                    line_end=5,
                    signature="def process(data):",
                    parent=None
                )
            ],
            imports=[]
        )
        
        file2 = FileInfo(
            path="file2.py",
            language="python",
            hash="h2",
            size=200,
            symbols=[
                Symbol(
                    name="process",
                    type=SymbolType.METHOD,
                    file_path="file2.py",
                    line_start=10,
                    line_end=15,
                    signature="def process(self, data):",
                    parent="Handler"
                )
            ],
            imports=[]
        )
        
        cache.save_file(file1)
        cache.save_file(file2)
        
        # Find all "process" symbols
        results = cache.find_symbol("process")
        assert len(results) == 2
        assert results[0].file_path == "file1.py"
        assert results[1].file_path == "file2.py"
        
        cache.close()


def test_search_symbols():
    """Test searching symbols with pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[
                Symbol(
                    name="get_user",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=1,
                    line_end=2,
                    signature="def get_user():",
                    parent=None
                ),
                Symbol(
                    name="get_data",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=3,
                    line_end=4,
                    signature="def get_data():",
                    parent=None
                ),
                Symbol(
                    name="set_value",
                    type=SymbolType.FUNCTION,
                    file_path="test.py",
                    line_start=5,
                    line_end=6,
                    signature="def set_value():",
                    parent=None
                )
            ],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Search for "get" pattern
        results = cache.search_symbols("get")
        assert len(results) == 2
        assert all("get" in r.name for r in results)
        
        cache.close()


def test_get_stats():
    """Test cache statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add some files
        for i in range(3):
            file_info = FileInfo(
                path=f"file{i}.py",
                language="python",
                hash=f"h{i}",
                size=100,
                symbols=[
                    Symbol(
                        name=f"func{i}",
                        type=SymbolType.FUNCTION,
                        file_path=f"file{i}.py",
                        line_start=1,
                        line_end=2,
                        signature=f"def func{i}():",
                        parent=None
                    )
                ],
                imports=[]
            )
            cache.save_file(file_info)
        
        stats = cache.get_stats()
        
        assert stats['total_files'] == 3
        assert stats['total_symbols'] == 3
        assert stats['by_language']['python'] == 3
        assert stats['by_type']['function'] == 3
        
        cache.close()


def test_delete_file():
    """Test deleting file from cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        file_info = FileInfo(
            path="temp.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Verify it exists
        assert cache.get_file("temp.py") is not None
        
        # Delete it
        cache.delete_file("temp.py")
        
        # Verify it's gone
        assert cache.get_file("temp.py") is None
        
        cache.close()


def test_clear_cache():
    """Test clearing all cache data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / ".code-compass"
        cache = CacheManager(cache_dir)
        
        # Add some data
        file_info = FileInfo(
            path="test.py",
            language="python",
            hash="h1",
            size=100,
            symbols=[],
            imports=[]
        )
        cache.save_file(file_info)
        
        # Clear cache
        cache.clear()
        
        # Verify it's empty
        stats = cache.get_stats()
        assert stats['total_files'] == 0
        assert stats['total_symbols'] == 0
        
        cache.close()


if __name__ == "__main__":
    # Run tests
    test_cache_initialization()
    test_save_and_retrieve_file()
    test_file_hash_check()
    test_update_existing_file()
    test_find_symbol()
    test_search_symbols()
    test_get_stats()
    test_delete_file()
    test_clear_cache()
    
    print("✅ All cache tests passed!")

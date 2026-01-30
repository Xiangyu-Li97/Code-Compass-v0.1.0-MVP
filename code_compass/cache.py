"""SQLite-based caching layer for parsed code."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .models import FileInfo, Symbol, SymbolType


class CacheManager:
    """Manages SQLite cache for parsed code."""
    
    def __init__(self, cache_dir: Path):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache database
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "index.db"
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema with performance optimizations."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Performance optimizations
        # WAL mode: Write-Ahead Logging for better concurrency and performance
        cursor.execute("PRAGMA journal_mode=WAL")
        # NORMAL synchronous mode: Balance between safety and speed
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size to 10MB (default is ~2MB)
        cursor.execute("PRAGMA cache_size=-10000")  # Negative means KB
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                language TEXT NOT NULL,
                hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                imports TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Symbols table with full-text search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                signature TEXT NOT NULL,
                parent TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_name 
            ON symbols(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbols_file 
            ON symbols(file_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_files_path 
            ON files(path)
        """)
        
        self.conn.commit()
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Get cached hash for a file."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash FROM files WHERE path = ?",
            (file_path,)
        )
        row = cursor.fetchone()
        return row['hash'] if row else None
    
    def is_file_cached(self, file_path: str, current_hash: str) -> bool:
        """Check if file is cached and unchanged."""
        cached_hash = self.get_file_hash(file_path)
        return cached_hash == current_hash if cached_hash else False
    
    def save_file(self, file_info: FileInfo):
        """Save or update file information in cache."""
        cursor = self.conn.cursor()
        
        # Check if file exists
        cursor.execute(
            "SELECT id FROM files WHERE path = ?",
            (file_info.path,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing file
            file_id = existing['id']
            cursor.execute("""
                UPDATE files 
                SET hash = ?, size = ?, language = ?, imports = ?, indexed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                file_info.hash,
                file_info.size,
                file_info.language,
                json.dumps(file_info.imports),
                file_id
            ))
            
            # Delete old symbols
            cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        else:
            # Insert new file
            cursor.execute("""
                INSERT INTO files (path, language, hash, size, imports)
                VALUES (?, ?, ?, ?, ?)
            """, (
                file_info.path,
                file_info.language,
                file_info.hash,
                file_info.size,
                json.dumps(file_info.imports)
            ))
            file_id = cursor.lastrowid
        
        # Insert symbols
        for symbol in file_info.symbols:
            cursor.execute("""
                INSERT INTO symbols (file_id, name, type, line_start, line_end, signature, parent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                symbol.name,
                symbol.type.value,
                symbol.line_start,
                symbol.line_end,
                symbol.signature,
                symbol.parent
            ))
        
        self.conn.commit()
    
    def get_file(self, file_path: str) -> Optional[FileInfo]:
        """Retrieve file information from cache."""
        cursor = self.conn.cursor()
        
        # Get file info
        cursor.execute(
            "SELECT * FROM files WHERE path = ?",
            (file_path,)
        )
        file_row = cursor.fetchone()
        
        if not file_row:
            return None
        
        # Get symbols
        cursor.execute(
            "SELECT * FROM symbols WHERE file_id = ? ORDER BY line_start",
            (file_row['id'],)
        )
        symbol_rows = cursor.fetchall()
        
        symbols = [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=file_path,
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in symbol_rows
        ]
        
        return FileInfo(
            path=file_row['path'],
            language=file_row['language'],
            hash=file_row['hash'],
            size=file_row['size'],
            symbols=symbols,
            imports=json.loads(file_row['imports'])
        )
    
    def get_all_files(self) -> list[FileInfo]:
        """Retrieve all cached files."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT path FROM files ORDER BY path")
        paths = [row['path'] for row in cursor.fetchall()]
        
        return [self.get_file(path) for path in paths]
    
    def find_symbol(self, name: str) -> list[Symbol]:
        """Find all symbols with given name."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name = ?
            ORDER BY f.path, s.line_start
        """, (name,))
        
        rows = cursor.fetchall()
        return [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=row['file_path'],
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in rows
        ]
    
    def search_symbols(self, pattern: str) -> list[Symbol]:
        """Search symbols by name pattern (case-insensitive)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ?
            ORDER BY f.path, s.line_start
        """, (f"%{pattern}%",))
        
        rows = cursor.fetchall()
        return [
            Symbol(
                name=row['name'],
                type=SymbolType(row['type']),
                file_path=row['file_path'],
                line_start=row['line_start'],
                line_end=row['line_end'],
                signature=row['signature'],
                parent=row['parent']
            )
            for row in rows
        ]
    
    def delete_file(self, file_path: str):
        """Remove file from cache."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE path = ?", (file_path,))
        self.conn.commit()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM files")
        file_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        symbol_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM files 
            GROUP BY language
        """)
        by_language = {row['language']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM symbols 
            GROUP BY type
        """)
        by_type = {row['type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_files': file_count,
            'total_symbols': symbol_count,
            'by_language': by_language,
            'by_type': by_type
        }
    
    def clear(self):
        """Clear all cache data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM files")
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

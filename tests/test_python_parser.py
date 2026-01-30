"""Tests for Python parser."""

import tempfile
from pathlib import Path

from code_compass.parsers import PythonParser
from code_compass.models import SymbolType


def test_parse_simple_function():
    """Test parsing a simple function."""
    code = """def hello(name: str) -> str:
    return f'Hello {name}'
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert file_info.language == "python"
        assert len(file_info.symbols) == 1
        
        symbol = file_info.symbols[0]
        assert symbol.name == "hello"
        assert symbol.type == SymbolType.FUNCTION
        assert "name: str" in symbol.signature
        assert "-> str" in symbol.signature


def test_parse_class_with_methods():
    """Test parsing a class with methods."""
    code = """class Calculator:
    def __init__(self, initial: int = 0):
        self.value = initial
    
    def add(self, x: int, y: int) -> int:
        return x + y
    
    async def fetch_data(self) -> dict:
        pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.symbols) == 4  # 1 class + 3 methods
        
        # Check class
        class_symbol = file_info.symbols[0]
        assert class_symbol.name == "Calculator"
        assert class_symbol.type == SymbolType.CLASS
        assert class_symbol.parent is None
        
        # Check methods
        init_symbol = file_info.symbols[1]
        assert init_symbol.name == "__init__"
        assert init_symbol.type == SymbolType.METHOD
        assert init_symbol.parent == "Calculator"
        assert "initial: int = 0" in init_symbol.signature
        
        add_symbol = file_info.symbols[2]
        assert add_symbol.name == "add"
        assert "-> int" in add_symbol.signature
        
        async_symbol = file_info.symbols[3]
        assert async_symbol.name == "fetch_data"
        assert "async def" in async_symbol.signature


def test_parse_with_decorators():
    """Test parsing functions and classes with decorators."""
    code = """@dataclass
class Point:
    x: int
    y: int

@staticmethod
def helper():
    pass

@property
def value(self):
    return self._value
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        
        # Check class decorator
        class_symbol = file_info.symbols[0]
        assert "@dataclass" in class_symbol.signature
        
        # Check method decorators
        helper_symbol = file_info.symbols[1]
        assert "@staticmethod" in helper_symbol.signature
        
        value_symbol = file_info.symbols[2]
        assert "@property" in value_symbol.signature


def test_parse_syntax_error():
    """Test handling of syntax errors."""
    code = "def broken(\n"  # Intentional syntax error
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        # Should return FileInfo with empty symbols, not crash
        assert file_info is not None
        assert len(file_info.symbols) == 0


def test_parse_imports():
    """Test extracting imports."""
    code = """import os
import sys
from pathlib import Path
from typing import List, Dict
from ..parent import something
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        # imports is now a list of dicts, not strings
        import_modules = [imp['module'] for imp in file_info.imports]
        assert "os" in import_modules
        assert "sys" in import_modules
        assert "pathlib" in import_modules
        assert "typing" in import_modules
        # Check we got the relative import
        assert len(file_info.imports) >= 5


def test_parse_inheritance():
    """Test parsing class inheritance."""
    code = """class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal, Serializable):
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        
        animal = file_info.symbols[0]
        assert "class Animal:" in animal.signature
        
        dog = file_info.symbols[1]
        assert "class Dog(Animal):" in dog.signature
        
        cat = file_info.symbols[2]
        assert "class Cat(Animal, Serializable):" in cat.signature


def test_complex_type_annotations():
    """Test parsing complex type annotations."""
    code = """from typing import Optional, Union, List, Dict

def process(
    data: List[Dict[str, int]],
    config: Optional[str] = None,
    mode: Union[str, int] = "auto"
) -> tuple[bool, str]:
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.symbols) == 1
        
        symbol = file_info.symbols[0]
        # Should contain type annotations
        assert "data:" in symbol.signature
        assert "config:" in symbol.signature
        assert "mode:" in symbol.signature
        assert "->" in symbol.signature


if __name__ == "__main__":
    # Run tests
    test_parse_simple_function()
    test_parse_class_with_methods()
    test_parse_with_decorators()
    test_parse_syntax_error()
    test_parse_imports()
    test_parse_inheritance()
    test_complex_type_annotations()
    
    print("✅ All tests passed!")

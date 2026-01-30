"""Tests for robust type annotation handling."""

import sys
import tempfile
from pathlib import Path

from code_compass.parsers import PythonParser


def test_python310_union_syntax():
    """Test Python 3.10+ Union syntax (str | int)."""
    # This syntax is only valid in Python 3.10+
    if sys.version_info < (3, 10):
        print("⏭️  Skipping Python 3.10+ test (current version: {}.{})".format(*sys.version_info[:2]))
        return
    
    code = """def process(value: str | int) -> bool | None:
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
        # Should not crash and should contain the union type
        assert "str | int" in symbol.signature or "Any" in symbol.signature
        assert "bool | None" in symbol.signature or "Any" in symbol.signature


def test_complex_nested_generics():
    """Test deeply nested generic types."""
    code = """from typing import Dict, List, Optional, Union

def complex_func(
    data: Dict[str, List[Dict[str, Union[int, str, None]]]],
    config: Optional[Dict[str, List[int]]] = None
) -> List[Optional[Dict[str, int]]]:
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
        # Should not crash - that's the main goal
        assert symbol.signature is not None
        assert "complex_func" in symbol.signature


def test_callable_types():
    """Test Callable type annotations."""
    code = """from typing import Callable

def higher_order(
    func: Callable[[int, str], bool],
    callback: Callable[[], None]
) -> Callable[[str], int]:
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
        # Should not crash
        assert "higher_order" in symbol.signature


def test_literal_types():
    """Test Literal type annotations."""
    code = """from typing import Literal

def set_mode(mode: Literal["read", "write", "append"]) -> None:
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
        # Should not crash
        assert "set_mode" in symbol.signature


def test_protocol_types():
    """Test Protocol type annotations."""
    code = """from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None:
        ...

def render(obj: Drawable) -> None:
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        # Should extract both the Protocol class and the function
        assert len(file_info.symbols) >= 2


def test_type_var():
    """Test TypeVar annotations."""
    code = """from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def get(self) -> T:
        pass
    
    def set(self, value: T) -> None:
        pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        # Should extract class and methods
        assert len(file_info.symbols) >= 3


def test_forward_references():
    """Test forward reference annotations (strings)."""
    code = """def create_node(parent: 'Node') -> 'Node':
    pass

class Node:
    def add_child(self, child: 'Node') -> None:
        pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        # Should not crash
        assert len(file_info.symbols) >= 2


def test_ellipsis_in_types():
    """Test ellipsis in type annotations."""
    code = """from typing import Tuple

def variadic(args: Tuple[int, ...]) -> None:
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


def test_malformed_annotations():
    """Test that malformed annotations don't crash the parser."""
    # This code has intentionally weird annotations
    code = """def weird(x: 1 + 2) -> []:
    pass
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        # Should not crash, even with weird annotations
        try:
            file_info = parser.parse_file(test_file, project_root)
            # If it parses, great
            if file_info:
                assert len(file_info.symbols) >= 0
        except SyntaxError:
            # If Python itself can't parse it, that's fine too
            pass


def test_no_annotations():
    """Test functions without any type annotations."""
    code = """def old_style(a, b, c):
    return a + b + c
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
        assert "old_style(a, b, c)" in symbol.signature


if __name__ == "__main__":
    # Run tests
    test_python310_union_syntax()
    test_complex_nested_generics()
    test_callable_types()
    test_literal_types()
    test_protocol_types()
    test_type_var()
    test_forward_references()
    test_ellipsis_in_types()
    test_malformed_annotations()
    test_no_annotations()
    
    print("✅ All type annotation tests passed!")

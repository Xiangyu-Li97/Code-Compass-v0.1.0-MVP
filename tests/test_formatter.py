"""Tests for formatter module."""

from code_compass.models import Symbol, RepoMap, SymbolType
from code_compass.formatter import SymbolFormatter, RepoMapFormatter


def test_symbol_to_map_line():
    """Test formatting symbol to map line."""
    # Function (no parent)
    func = Symbol(
        name="helper",
        type=SymbolType.FUNCTION,
        file_path="utils.py",
        line_start=10,
        line_end=15,
        signature="def helper(x: int) -> str:",
        parent=None
    )
    
    line = SymbolFormatter.to_map_line(func)
    assert line == "│def helper(x: int) -> str:"
    
    # Method (has parent)
    method = Symbol(
        name="process",
        type=SymbolType.METHOD,
        file_path="app.py",
        line_start=20,
        line_end=25,
        signature="def process(self, data: dict) -> None:",
        parent="Handler"
    )
    
    line = SymbolFormatter.to_map_line(method)
    assert line == "│ def process(self, data: dict) -> None:"


def test_symbol_to_dict():
    """Test converting symbol to dictionary."""
    symbol = Symbol(
        name="MyClass",
        type=SymbolType.CLASS,
        file_path="models.py",
        line_start=5,
        line_end=20,
        signature="class MyClass:",
        parent=None
    )
    
    d = SymbolFormatter.to_dict(symbol)
    
    assert d['name'] == "MyClass"
    assert d['type'] == "class"
    assert d['file_path'] == "models.py"
    assert d['line_start'] == 5
    assert d['line_end'] == 20
    assert d['signature'] == "class MyClass:"
    assert d['parent'] is None


def test_symbol_to_text():
    """Test converting symbol to human-readable text."""
    symbol = Symbol(
        name="calculate",
        type=SymbolType.METHOD,
        file_path="math_utils.py",
        line_start=42,
        line_end=50,
        signature="def calculate(self, x: float, y: float) -> float:",
        parent="Calculator"
    )
    
    text = SymbolFormatter.to_text(symbol)
    
    assert "Method calculate" in text
    assert "(in Calculator)" in text
    assert "math_utils.py:42" in text
    assert "def calculate" in text


def test_repo_map_to_text():
    """Test formatting RepoMap to text."""
    symbols = {
        "app.py": [
            Symbol(
                name="main",
                type=SymbolType.FUNCTION,
                file_path="app.py",
                line_start=1,
                line_end=10,
                signature="def main():",
                parent=None
            )
        ],
        "utils.py": [
            Symbol(
                name="Helper",
                type=SymbolType.CLASS,
                file_path="utils.py",
                line_start=1,
                line_end=5,
                signature="class Helper:",
                parent=None
            ),
            Symbol(
                name="process",
                type=SymbolType.METHOD,
                file_path="utils.py",
                line_start=2,
                line_end=4,
                signature="def process(self):",
                parent="Helper"
            )
        ]
    }
    
    repo_map = RepoMap(
        files=["app.py", "utils.py"],
        symbols=symbols,
        token_count=100
    )
    
    text = RepoMapFormatter.to_text(repo_map)
    
    # Check structure
    assert "app.py:" in text
    assert "utils.py:" in text
    assert "⋮..." in text
    assert "def main():" in text
    assert "class Helper:" in text
    assert "│ def process(self):" in text  # Indented method


def test_repo_map_to_json():
    """Test formatting RepoMap to JSON."""
    symbols = {
        "test.py": [
            Symbol(
                name="test_func",
                type=SymbolType.FUNCTION,
                file_path="test.py",
                line_start=1,
                line_end=5,
                signature="def test_func():",
                parent=None
            )
        ]
    }
    
    repo_map = RepoMap(
        files=["test.py"],
        symbols=symbols,
        token_count=50
    )
    
    json_data = RepoMapFormatter.to_json(repo_map)
    
    assert json_data['files'] == ["test.py"]
    assert 'test.py' in json_data['symbols']
    assert len(json_data['symbols']['test.py']) == 1
    assert json_data['symbols']['test.py'][0]['name'] == "test_func"
    assert json_data['token_count'] == 50


if __name__ == "__main__":
    # Run tests
    test_symbol_to_map_line()
    test_symbol_to_dict()
    test_symbol_to_text()
    test_repo_map_to_text()
    test_repo_map_to_json()
    
    print("✅ All formatter tests passed!")

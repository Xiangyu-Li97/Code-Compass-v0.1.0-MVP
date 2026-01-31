"""Python code parser using AST."""

import ast
import hashlib
from pathlib import Path
from typing import Optional

from ..models import FileInfo, Symbol, SymbolType


class PythonParser:
    """Parser for Python source files."""
    
    def parse_file(self, file_path: Path, project_root: Path) -> Optional[FileInfo]:
        """
        Parse a single Python file.
        
        Args:
            file_path: Absolute path to the Python file
            project_root: Project root directory
            
        Returns:
            FileInfo object or None if parsing fails
        """
        try:
            # Read file content with multiple encoding attempts
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk']
            
            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if content is None:
                print(f"⚠️  Could not decode {file_path} with any supported encoding")
                return None
            
            # Remove BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
            
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                # Syntax error: return empty result, don't crash
                print(f"⚠️  Syntax error in {file_path}: {e}")
                return FileInfo(
                    path=str(file_path.relative_to(project_root)),
                    language="python",
                    hash=file_hash,
                    size=len(content),
                    symbols=[],
                    imports=[]
                )
            
            # Extract symbols and imports
            visitor = PythonVisitor(file_path, project_root)
            visitor.visit(tree)
            
            return FileInfo(
                path=str(file_path.relative_to(project_root)),
                language="python",
                hash=file_hash,
                size=len(content),
                symbols=visitor.symbols,
                imports=visitor.imports
            )
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return None


class PythonVisitor(ast.NodeVisitor):
    """AST visitor to extract symbols and imports."""
    
    def __init__(self, file_path: Path, project_root: Path):
        self.file_path = file_path
        self.project_root = project_root
        self.symbols: list[Symbol] = []
        self.imports: list[str] = []
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        # Extract base classes
        bases = [self._get_name(base) for base in node.bases if self._get_name(base)]
        base_str = f"({', '.join(bases)})" if bases else ""
        
        # Extract decorators
        decorators = [f"@{self._get_name(dec)}" for dec in node.decorator_list if self._get_name(dec)]
        decorator_str = " ".join(decorators) + " " if decorators else ""
        
        # Build signature
        signature = f"{decorator_str}class {node.name}{base_str}:"
        
        # Create Symbol
        symbol = Symbol(
            name=node.name,
            type=SymbolType.CLASS,
            file_path=str(self.file_path.relative_to(self.project_root)),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            parent=None
        )
        self.symbols.append(symbol)
        
        # Save current class and continue traversing methods
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function/method definition."""
        self._handle_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function/method definition."""
        self._handle_function(node, is_async=True)
    
    def _handle_function(self, node, is_async=False):
        """Handle both sync and async function definitions."""
        # Extract parameters
        args = []
        
        # Regular arguments
        for i, arg in enumerate(node.args.args):
            arg_str = arg.arg
            # Add type annotation if present
            if arg.annotation:
                arg_str += f": {self._get_name(arg.annotation)}"
            # Add default value if present
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_val = self._get_default_value(node.args.defaults[default_idx])
                if default_val:
                    arg_str += f" = {default_val}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg_str += f": {self._get_name(node.args.vararg.annotation)}"
            args.append(vararg_str)
        
        # **kwargs
        if node.args.kwarg:
            kwarg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg_str += f": {self._get_name(node.args.kwarg.annotation)}"
            args.append(kwarg_str)
        
        # Extract return type
        return_type = ""
        if node.returns:
            return_type = f" -> {self._get_name(node.returns)}"
        
        # Extract decorators
        decorators = [f"@{self._get_name(dec)}" for dec in node.decorator_list if self._get_name(dec)]
        decorator_str = " ".join(decorators) + " " if decorators else ""
        
        # Build signature
        async_str = "async " if is_async else ""
        signature = f"{decorator_str}{async_str}def {node.name}({', '.join(args)}){return_type}:"
        
        # Determine symbol type
        symbol_type = SymbolType.METHOD if self.current_class else SymbolType.FUNCTION
        
        # Create Symbol
        symbol = Symbol(
            name=node.name,
            type=symbol_type,
            file_path=str(self.file_path.relative_to(self.project_root)),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            parent=self.current_class
        )
        self.symbols.append(symbol)
        
        # Don't traverse function body (we don't need it)
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'level': 0,  # Absolute import
                'type': 'import'
            })
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statement."""
        # Handle both absolute and relative imports
        # level=0: from x import y (absolute)
        # level=1: from . import y (current package)
        # level=2: from .. import y (parent package)
        module = node.module or ''  # module can be None for "from . import x"
        level = node.level or 0
        
        self.imports.append({
            'module': module,
            'level': level,
            'type': 'from'
        })
    
    def _get_name(self, node) -> str:
        """Extract name from AST node with robust error handling."""
        try:
            if node is None:
                return ""
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                value = self._get_name(node.value)
                return f"{value}.{node.attr}" if value else node.attr
            elif isinstance(node, ast.Subscript):
                # Handle generics like List[str], Dict[str, int]
                value = self._get_name(node.value)
                slice_val = self._get_name(node.slice)
                return f"{value}[{slice_val}]" if slice_val else value
            elif isinstance(node, ast.Tuple):
                # Handle multiple types like Union[str, int]
                elements = [self._get_name(elt) for elt in node.elts]
                return ", ".join(filter(None, elements))
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.Call):
                # Handle callable types
                func = self._get_name(node.func)
                return func
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                # Handle Python 3.10+ Union syntax: str | int
                left = self._get_name(node.left)
                right = self._get_name(node.right)
                return f"{left} | {right}" if left and right else "Any"
            elif isinstance(node, ast.List):
                # Handle list of types (rare but possible)
                elements = [self._get_name(elt) for elt in node.elts]
                return "[" + ", ".join(filter(None, elements)) + "]"
            else:
                # Unknown node type - return a safe fallback
                return "Any"
        except Exception as e:
            # Absolutely never crash - return a safe fallback
            print(f"⚠️  Warning: Failed to extract type annotation: {e}")
            return "Any"
    
    def _get_default_value(self, node) -> str:
        """Extract default value from AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
            # Return simplified representation
            if isinstance(node, ast.List):
                return "[]"
            elif isinstance(node, ast.Tuple):
                return "()"
            elif isinstance(node, ast.Dict):
                return "{}"
            elif isinstance(node, ast.Set):
                return "set()"
        return ""

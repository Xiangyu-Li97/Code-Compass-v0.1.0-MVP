"""Tests for relative import resolution."""

import tempfile
from pathlib import Path

from ai_code_compass.parsers import PythonParser
from ai_code_compass.graph import DependencyBuilder


def test_parse_relative_imports():
    """Test parsing relative imports."""
    code = """from . import utils
from .. import config
from ...parent import helper
import os
from typing import List
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.imports) == 5
        
        # Check relative imports
        imports_by_level = {imp['level']: imp for imp in file_info.imports}
        
        # from . import utils (module is empty, level is 1)
        assert 1 in imports_by_level
        assert imports_by_level[1]['module'] == ''  # AST gives us empty module for "from . import x"
        assert imports_by_level[1]['type'] == 'from'
        
        # from .. import config (module is empty, level is 2)
        assert 2 in imports_by_level
        assert imports_by_level[2]['module'] == ''
        
        # from ...parent import helper (module is 'parent', level is 3)
        assert 3 in imports_by_level
        assert imports_by_level[3]['module'] == 'parent'
        
        # import os (absolute)
        os_import = next(imp for imp in file_info.imports if imp['module'] == 'os')
        assert os_import['level'] == 0
        assert os_import['type'] == 'import'


def test_resolve_relative_imports():
    """Test resolving relative imports to file paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create a package structure:
        # myapp/
        #   __init__.py
        #   main.py (imports from . import utils)
        #   utils.py
        #   sub/
        #     __init__.py
        #     worker.py (imports from .. import utils)
        
        myapp_dir = project_root / "myapp"
        myapp_dir.mkdir()
        (myapp_dir / "__init__.py").write_text("")
        (myapp_dir / "utils.py").write_text("def helper(): pass")
        
        main_code = """from . import utils
from .utils import helper
"""
        (myapp_dir / "main.py").write_text(main_code)
        
        sub_dir = myapp_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "__init__.py").write_text("")
        
        worker_code = """from .. import utils
from ..utils import helper
"""
        (sub_dir / "worker.py").write_text(worker_code)
        
        # Parse all files
        parser = PythonParser()
        files = []
        
        for py_file in project_root.rglob("*.py"):
            if py_file.name != "__pycache__":
                file_info = parser.parse_file(py_file, project_root)
                if file_info:
                    files.append(file_info)
        
        # Build dependency graph
        builder = DependencyBuilder(project_root)
        graph = builder.build(files)
        
        # Check that main.py depends on utils.py
        main_deps = graph.get_dependencies("myapp/main.py")
        assert "myapp/utils.py" in main_deps or "myapp/utils" in str(main_deps)
        
        # Check that worker.py depends on utils.py
        worker_deps = graph.get_dependencies("myapp/sub/worker.py")
        # Should resolve "../utils" from "myapp/sub/worker.py" to "myapp/utils.py"
        assert any("utils" in dep for dep in worker_deps)


def test_from_dot_import():
    """Test 'from . import x' (module is empty string)."""
    code = """from . import utils, config
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        # "from . import utils, config" creates one ImportFrom node
        # with module=None (empty string after our handling)
        assert len(file_info.imports) >= 1
        
        # Check that we captured the relative import
        relative_import = next((imp for imp in file_info.imports if imp['level'] > 0), None)
        assert relative_import is not None
        assert relative_import['level'] == 1


def test_mixed_imports():
    """Test a file with mixed absolute and relative imports."""
    code = """import os
import sys
from pathlib import Path
from . import local_utils
from .. import parent_utils
from typing import List, Dict
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.py"
        test_file.write_text(code)
        
        parser = PythonParser()
        file_info = parser.parse_file(test_file, project_root)
        
        assert file_info is not None
        assert len(file_info.imports) == 6
        
        # Count by level
        absolute_imports = [imp for imp in file_info.imports if imp['level'] == 0]
        relative_imports = [imp for imp in file_info.imports if imp['level'] > 0]
        
        assert len(absolute_imports) == 4  # os, sys, pathlib, typing
        assert len(relative_imports) == 2  # local_utils, parent_utils


if __name__ == "__main__":
    # Run tests
    test_parse_relative_imports()
    test_resolve_relative_imports()
    test_from_dot_import()
    test_mixed_imports()
    
    print("✅ All relative import tests passed!")

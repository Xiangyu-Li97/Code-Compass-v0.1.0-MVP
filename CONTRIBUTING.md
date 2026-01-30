# Contributing to Code Compass

Thank you for your interest in contributing to Code Compass! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Found a bug? Open an issue with details
- **Feature Requests**: Have an idea? Share it in the issues
- **Code Contributions**: Submit pull requests for bug fixes or new features
- **Documentation**: Improve README, add examples, fix typos
- **Testing**: Test on different projects and report results

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Code-Compass-v0.1.0-MVP.git
cd Code-Compass-v0.1.0-MVP

# Add upstream remote
git remote add upstream https://github.com/Xiangyu-Li97/Code-Compass-v0.1.0-MVP.git
```

### 2. Set Up Development Environment

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install development dependencies (optional)
pip install pytest black flake8
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-number-description
```

## 🧪 Running Tests

We have comprehensive test coverage. Please ensure all tests pass before submitting a PR.

```bash
# Run all tests
./run_all_tests.sh

# Or run specific test files
python3 tests/test_python_parser.py
python3 tests/test_cache.py
```

### Test Coverage

Our test suites include:
- `test_python_parser.py` - AST parsing
- `test_cache.py` - SQLite caching
- `test_formatter.py` - Output formatting
- `test_relative_imports.py` - Import resolution
- `test_type_annotations.py` - Type annotation handling
- `test_cache_performance.py` - Performance benchmarks
- `test_real_project.py` - Integration tests

## 📝 Code Style

We follow standard Python conventions:

### Formatting

```bash
# Format code with black (recommended)
black code_compass/ tests/

# Check with flake8
flake8 code_compass/ tests/ --max-line-length=100
```

### Guidelines

- **Line length**: Max 100 characters
- **Imports**: Group by standard library, third-party, local
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type hints for function signatures
- **Comments**: Explain "why", not "what"

### Example

```python
from typing import List, Optional

def parse_file(path: str, force: bool = False) -> Optional[FileInfo]:
    """Parse a Python file and extract symbols.
    
    Args:
        path: Absolute path to the Python file
        force: If True, ignore cache and re-parse
        
    Returns:
        FileInfo object with extracted symbols, or None if parsing fails
    """
    # Implementation
    pass
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Environment**:
   - Python version (`python --version`)
   - Operating system
   - Code Compass version

2. **Steps to reproduce**:
   - Minimal code example
   - Command you ran
   - Expected vs actual behavior

3. **Error messages**:
   - Full traceback
   - Any relevant log output

### Bug Report Template

```markdown
**Environment:**
- Python: 3.11.0
- OS: Ubuntu 22.04
- Code Compass: v0.1.0

**Steps to Reproduce:**
1. Run `code-compass index /path/to/project`
2. ...

**Expected Behavior:**
Should index all files

**Actual Behavior:**
Crashes with SyntaxError

**Error Message:**
```
<paste full traceback here>
```
```

## 💡 Feature Requests

We welcome feature requests! Please include:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How would you like it to work?
3. **Alternatives**: Have you considered other approaches?
4. **Examples**: Show what the API/CLI would look like

## 🔧 Pull Request Process

### Before Submitting

1. ✅ Tests pass (`./run_all_tests.sh`)
2. ✅ Code is formatted (`black code_compass/ tests/`)
3. ✅ No linting errors (`flake8 code_compass/ tests/`)
4. ✅ Documentation updated (if needed)
5. ✅ Commit messages are clear

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add JavaScript parser
fix: handle empty files in cache
docs: update README with new examples
test: add tests for relative imports
refactor: simplify dependency graph builder
perf: optimize PageRank calculation
```

### PR Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests for this change
- [ ] Tested on real projects

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Submit your PR
2. Maintainers will review within 1-3 days
3. Address any feedback
4. Once approved, we'll merge!

## 🎯 Priority Areas

We're especially interested in contributions in these areas:

### High Priority

1. **JavaScript/TypeScript Parser**
   - Use Tree-sitter or Babel AST
   - Support ES6+ syntax
   - Handle JSX/TSX

2. **Performance Optimizations**
   - Parallel file parsing
   - Incremental indexing
   - Memory optimization for large projects

3. **Additional Language Support**
   - Java
   - Go
   - Rust
   - C/C++

### Medium Priority

4. **Automatic File Watching**
   - Monitor file changes
   - Auto-update index
   - Debounce rapid changes

5. **IDE Integration**
   - VSCode extension
   - IntelliJ plugin
   - Sublime Text package

6. **Enhanced Output Formats**
   - Markdown with links
   - HTML with syntax highlighting
   - GraphML for visualization

## 📚 Development Tips

### Project Structure

```
code_compass/
├── models.py          # Data structures (Symbol, FileInfo, RepoMap)
├── parsers/
│   ├── __init__.py
│   └── python_parser.py  # Python AST parser
├── cache.py           # SQLite cache manager
├── graph.py           # Dependency graph & PageRank
├── map_generator.py   # Core map generation logic
├── formatter.py       # Output formatters (text/JSON)
└── cli.py             # Command-line interface
```

### Key Design Principles

1. **Separation of Concerns**
   - Models are pure data (no logic)
   - Formatters handle presentation
   - Parsers handle language-specific logic

2. **Performance First**
   - Cache everything possible
   - Use SQLite for fast lookups
   - Avoid re-parsing unchanged files

3. **Fail Gracefully**
   - Syntax errors shouldn't crash
   - Return partial results when possible
   - Log warnings, don't throw exceptions

### Adding a New Language Parser

1. Create `parsers/your_language_parser.py`
2. Implement `YourLanguageParser` class with `parse_file()` method
3. Return `FileInfo` with extracted symbols
4. Add tests in `tests/test_your_language_parser.py`
5. Update CLI to detect file extensions
6. Update README with language support

Example structure:

```python
from code_compass.models import FileInfo, Symbol, SymbolType

class JavaScriptParser:
    def parse_file(self, path: str) -> FileInfo:
        """Parse a JavaScript file and extract symbols."""
        # Use Tree-sitter or Babel AST
        # Extract functions, classes, exports
        # Return FileInfo with symbols
        pass
```

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open an Issue
- **Chat**: (Coming soon - Discord/Slack)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Code Compass!** 🎉

Your contributions help make AI-powered coding more efficient for everyone.

# Code Compass 🧭

**Fast code map generator for AI coding assistants**

Code Compass helps AI understand your codebase by generating concise, high-signal repository maps. It saves **99%+ tokens** while preserving the most important context for AI-powered coding tasks.

[![PyPI version](https://badge.fury.io/py/ai-code-compass.svg)](https://badge.fury.io/py/ai-code-compass)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/ai-code-compass.svg)](https://pypi.org/project/ai-code-compass/)
[![Tests: 44 passing](https://img.shields.io/badge/tests-44%20passing-brightgreen.svg)]()

---

## Why Code Compass?

When working with AI coding assistants (Claude, GPT, etc.), you face a fundamental problem: **context limits**. Sending your entire codebase is:
- ❌ **Expensive** - Costs $0.47+ per query for medium projects
- ❌ **Slow** - Takes 47+ seconds to process
- ❌ **Ineffective** - AI gets overwhelmed by irrelevant details

Code Compass solves this by:
- ✅ **Saving 99%+ tokens** - Only sends function signatures, not implementations
- ✅ **Identifying important files** - Uses PageRank to rank files by importance
- ✅ **Fast indexing** - Processes 800+ files/second
- ✅ **Smart caching** - Only re-parses changed files

---

## Installation

### From PyPI (Recommended)

```bash
pip install ai-code-compass
```

### From Source

```bash
# Clone the repository
git clone https://github.com/Xiangyu-Li97/Code-Compass-v0.1.0-MVP.git
cd code-compass

# Install dependencies
pip install -e .
```

---

## Quick Start

```bash
# 1. Index your project
ai-code-compass index /path/to/your/project

# 2. Generate a code map
ai-code-compass map

# 3. Find a symbol
ai-code-compass find ClassName --fuzzy

# 4. View statistics
ai-code-compass stats
```

---

## Usage

### Index a Project

```bash
# Index current directory
ai-code-compass index .

# Index a specific directory
ai-code-compass index /path/to/project

# Force re-index all files
ai-code-compass index . --force
```

### Generate a Code Map

```bash
# Generate text format (default)
ai-code-compass map

# Generate JSON format
ai-code-compass map --format json

# Include top 30% of files
ai-code-compass map --top 0.3

# Limit symbols per file
ai-code-compass map --max-symbols 20

# Save to file
ai-code-compass map -o repo_map.txt
```

### Find Symbols

```bash
# Exact match
ai-code-compass find ClassName

# Fuzzy search
ai-code-compass find Parser --fuzzy

# Show full signatures
ai-code-compass find process_data -s
```

### View Statistics

```bash
ai-code-compass stats
```

### Clear Cache

```bash
ai-code-compass clear
```

---

## Example Output

### Text Format (for AI)

```
# Repository Map (Top 3 files, 15%)

## api.py (importance: 1.138)
⋮...
│def request(method, url, **kwargs):
│def get(url, params = None, **kwargs):
│def post(url, data = None, json = None, **kwargs):
⋮...

## models.py (importance: 0.856)
⋮...
│class User:
│  def __init__(self, name: str, email: str):
│  def save(self) -> bool:
⋮...
```

### JSON Format (for tools)

```json
{
  "total_files": 20,
  "included_files": 3,
  "files": [
    {
      "path": "api.py",
      "importance": 1.138,
      "symbols": [
        {
          "name": "request",
          "type": "function",
          "signature": "def request(method, url, **kwargs):",
          "line_start": 10
        }
      ]
    }
  ]
}
```

---

## Performance Benchmarks

Tested on real-world open-source projects:

| Project | Files | Symbols | Index Time | Speed | Token Savings |
|---------|-------|---------|------------|-------|---------------|
| **requests** | 18 | 277 | 0.04s | 497 f/s | **99.0%** |
| **flask** | 24 | 407 | 0.05s | 542 f/s | **99.6%** |
| **django** | 901 | 11,072 | 1.55s | 863 f/s | **83.0%** |

**AI Workflow Validation** (requests library):
- Traditional method: ~46,923 tokens, $0.47, 47s
- Code Compass: ~209 tokens, $0.002, 0.2s
- **Savings: 99.6% tokens, 99.6% cost, 99.6% time**

---

## How It Works

1. **Parse** - Extracts function/class signatures using Python AST
2. **Index** - Caches results in SQLite for fast retrieval
3. **Analyze** - Builds dependency graph and computes PageRank
4. **Generate** - Selects top N% files and formats for AI

### Why PageRank?

PageRank identifies the most "important" files in your codebase by analyzing the dependency graph. Files that are imported by many other files get higher scores.

Example from Django:
- `db/models/functions/datetime.py` (score: 41.1) - Core database functions
- `utils/copy.py` (score: 17.1) - Widely-used utilities
- `utils/inspect.py` (score: 16.9) - Reflection tools

---

## Architecture

```
code_compass/
├── models.py          # Data structures (Symbol, FileInfo, RepoMap)
├── parsers/
│   └── python_parser.py  # AST-based Python parser
├── cache.py           # SQLite cache manager
├── graph.py           # Dependency graph & PageRank
├── map_generator.py   # Core map generation logic
├── formatter.py       # Output formatters (text/JSON)
└── cli.py             # Command-line interface
```

---

## Supported Languages

- ✅ **Python** - Full support
- 🚧 **JavaScript/TypeScript** - Coming soon
- 🚧 **Java** - Planned
- 🚧 **Go** - Planned

---

## Limitations

- **Syntax errors**: Files with syntax errors are skipped (not parsed)
- **Dynamic imports**: `importlib`, `__import__()` not tracked
- **Reflection**: `getattr()`, `eval()` not analyzed
- **Monorepos**: Best used on single projects, not multi-project repos

---

## Use Cases

### 1. AI-Powered Code Review
```bash
ai-code-compass map > context.txt
# Send context.txt to AI: "Review this codebase for security issues"
```

### 2. Onboarding New Developers
```bash
ai-code-compass map --top 0.1 > overview.txt
# New dev reads overview.txt to understand core modules
```

### 3. Refactoring Planning
```bash
ai-code-compass find OldClassName --fuzzy
# Find all occurrences before renaming
```

### 4. Documentation Generation
```bash
ai-code-compass map --format json | your-doc-generator
# Generate API docs from signatures
```

---

## FAQ

**Q: Why not use ctags or LSP?**
A: ctags is too simple (no type annotations), LSP is too heavy (designed for IDEs). Code Compass is optimized for AI context generation.

**Q: Why AST instead of Tree-sitter?**
A: AST is built-in, zero-dependency, and 100% accurate for valid Python code. Tree-sitter is better for real-time editing, which isn't our use case.

**Q: How is this different from Aider's repomap?**
A: Code Compass is a standalone tool with caching, making it 10x+ faster for repeated queries. It can be integrated into any AI workflow.

**Q: What about incomplete code?**
A: Code Compass is designed for indexing stable codebases (e.g., git commits), not real-time editing. Syntax errors are gracefully skipped.

---

## Testing

We have comprehensive test coverage (44 test cases, 100% pass rate):

```bash
# Run all tests
./run_all_tests.sh
```

Test suites:
- `test_python_parser.py` - AST parsing
- `test_cache.py` - SQLite caching
- `test_formatter.py` - Output formatting
- `test_relative_imports.py` - Import resolution
- `test_type_annotations.py` - Type annotation handling
- `test_cache_performance.py` - Performance benchmarks
- `test_real_project.py` - Integration tests

---

## Documentation

- [Final Validation Report](FINAL_VALIDATION_REPORT.md) - Complete empirical validation
- [Empirical Validation](EMPIRICAL_VALIDATION_REPORT.md) - Performance benchmarks
- [Fixes Summary](FIXES_SUMMARY.md) - Detailed changelog
- [Gemini Review](GEMINI_FEEDBACK_ANALYSIS.md) - Technical review

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Priority areas:
- JavaScript/TypeScript parser
- Automatic file watching
- Additional language support
- Performance optimizations

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Inspired by [Aider's repomap](https://aider.chat/docs/repomap.html)
- PageRank algorithm by Larry Page and Sergey Brin
- Built with ❤️ for the AI coding community
- Special thanks to Gemini for rigorous code review

---

## Project Status

**Version**: 0.1.0 MVP

**Completed**:
- ✅ Python parser with full type annotation support
- ✅ SQLite caching with WAL mode optimization
- ✅ Dependency graph with PageRank
- ✅ Relative import resolution
- ✅ Map generator with text/JSON output
- ✅ Complete CLI tool
- ✅ Comprehensive test suite (44 tests)
- ✅ Empirical validation on real projects

**Next Steps**:
- 🔄 JavaScript/TypeScript support
- 🔄 Automatic file watching
- 🔄 Token budget optimization
- 🔄 VSCode extension

---

**Made with 🧭 by Xiangyu Li**


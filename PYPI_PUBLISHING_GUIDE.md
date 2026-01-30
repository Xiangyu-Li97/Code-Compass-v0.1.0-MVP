# PyPI Publishing Guide for Code Compass

**Version**: 0.1.0  
**Date**: 2026-01-30  
**Status**: ✅ Ready to publish

---

## 📦 Package Information

- **Package Name**: `code-compass`
- **Version**: 0.1.0
- **PyPI URL**: https://pypi.org/project/code-compass/ (after publishing)
- **Install Command**: `pip install code-compass`

---

## ✅ Pre-Publishing Checklist

All items completed:

- [x] Optimize `pyproject.toml` with metadata
- [x] Add `__version__` to `__init__.py`
- [x] Create `MANIFEST.in` for file inclusion
- [x] Build distribution packages
- [x] Verify packages with `twine check`
- [x] Test installation in virtual environment
- [x] Test CLI commands work correctly

---

## 📊 Build Results

```bash
$ ls -lh dist/
-rw-rw-r-- 1 ubuntu ubuntu 21K code_compass-0.1.0-py3-none-any.whl
-rw-rw-r-- 1 ubuntu ubuntu 25K code_compass-0.1.0.tar.gz

$ twine check dist/*
Checking dist/code_compass-0.1.0-py3-none-any.whl: PASSED ✅
Checking dist/code_compass-0.1.0.tar.gz: PASSED ✅
```

**Test Installation**:
```bash
$ pip install dist/code_compass-0.1.0-py3-none-any.whl
Successfully installed click-8.3.1 code-compass-0.1.0 ✅

$ code-compass --version
code-compass, version 0.1.0 ✅

$ code-compass --help
Usage: code-compass [OPTIONS] COMMAND [ARGS]...
  Code Compass - Fast code map generator for AI coding assistants.
Commands:
  clear  Clear the index cache.
  find   Find symbol definitions.
  index  Index a project's code.
  map    Generate a code map.
  stats  Show indexing statistics.
✅ All commands working!
```

---

## 🚀 Publishing Steps

### Step 1: Create PyPI Account

If you don't have a PyPI account:

1. Go to https://pypi.org/account/register/
2. Create an account
3. Verify your email

### Step 2: Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `code-compass-upload`
4. Scope: "Entire account" (or specific to `code-compass` after first upload)
5. Copy the token (starts with `pypi-`)

**⚠️ Important**: Save the token immediately - you won't be able to see it again!

### Step 3: Configure Twine

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**Security**: Make sure this file is only readable by you:
```bash
chmod 600 ~/.pypirc
```

### Step 4: Test on TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ code-compass

# Test it works
code-compass --version
code-compass --help
```

### Step 5: Publish to PyPI

```bash
cd ~/code-compass

# Upload to PyPI
twine upload dist/*

# You'll see:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading code_compass-0.1.0-py3-none-any.whl
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 21.0/21.0 kB • 00:00 • ?
# Uploading code_compass-0.1.0.tar.gz
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.0/25.0 kB • 00:00 • ?
# 
# View at:
# https://pypi.org/project/code-compass/0.1.0/
```

### Step 6: Verify Publication

1. Visit https://pypi.org/project/code-compass/
2. Check that all metadata is correct
3. Test installation:
   ```bash
   pip install code-compass
   code-compass --version
   ```

---

## 🎯 Post-Publishing Tasks

### Update GitHub Repository

1. Add PyPI badge to README:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/code-compass.svg)](https://pypi.org/project/code-compass/)
   ```

2. Update installation instructions:
   ```markdown
   ## Installation
   
   ```bash
   pip install code-compass
   ```
   ```

3. Commit and push changes:
   ```bash
   git add README.md
   git commit -m "docs: add PyPI installation instructions"
   git push origin main
   ```

### Create GitHub Release

```bash
git tag -a v0.1.0 -m "Release v0.1.0 - First PyPI release"
git push origin v0.1.0
```

Then create a release on GitHub with the same notes.

### Announce on Social Media

**Twitter/X**:
```
🚀 Just published Code Compass v0.1.0 to PyPI!

A fast code map generator for AI coding assistants that saves 99%+ tokens.

pip install code-compass

✨ Features:
- 863 files/s indexing speed
- PageRank-based file importance
- Python support (JS/TS coming soon)

#Python #AI #DevTools

https://pypi.org/project/code-compass/
```

**Reddit** (r/Python, r/MachineLearning):
```
Title: [P] Code Compass - Save 99%+ tokens when using AI coding assistants

I built a tool that generates compact code maps for AI assistants like Claude/GPT.

Key features:
- Indexes large projects in seconds (863 files/s on Django)
- Uses PageRank to identify important files
- Saves 99%+ tokens while preserving context
- Simple CLI: `code-compass index . && code-compass map`

Just published v0.1.0 to PyPI: pip install code-compass

GitHub: https://github.com/Xiangyu-Li97/Code-Compass-v0.1.0-MVP
PyPI: https://pypi.org/project/code-compass/

Feedback welcome!
```

**Hacker News**:
```
Title: Code Compass – Fast code map generator for AI coding assistants

https://github.com/Xiangyu-Li97/Code-Compass-v0.1.0-MVP
```

---

## 🔄 Future Releases

### Version Bumping

For future releases:

1. Update version in `code_compass/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

3. Clean old builds:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

4. Build new packages:
   ```bash
   python3 -m build
   ```

5. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes

**Planned releases**:
- v0.1.1: Bug fixes
- v0.2.0: JavaScript/TypeScript support
- v0.3.0: Auto file watching
- v1.0.0: Production-ready, stable API

---

## 🐛 Troubleshooting

### Issue: "The user 'YOUR_USERNAME' isn't allowed to upload to project 'code-compass'"

**Solution**: You're trying to upload a package that already exists. Either:
1. Bump the version number
2. Choose a different package name

### Issue: "HTTPError: 403 Forbidden"

**Solution**: Check your API token:
1. Make sure it's correctly set in `~/.pypirc`
2. Verify the token hasn't expired
3. Create a new token if needed

### Issue: "WARNING: Duplicate files found"

**Solution**: Clean build artifacts:
```bash
rm -rf build/ dist/ *.egg-info
python3 -m build
```

### Issue: Package installs but command not found

**Solution**: 
1. Check `[project.scripts]` in `pyproject.toml`
2. Reinstall: `pip uninstall code-compass && pip install code-compass`
3. Check PATH: `which code-compass`

---

## 📚 Resources

- **PyPI Documentation**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Setuptools Documentation**: https://setuptools.pypa.io/
- **PEP 621** (pyproject.toml): https://peps.python.org/pep-0621/

---

## ✅ Publishing Checklist

Before publishing:

- [ ] All tests pass (`./run_all_tests.sh`)
- [ ] Version number updated
- [ ] CHANGELOG.md updated (if exists)
- [ ] README.md is accurate
- [ ] Build packages (`python3 -m build`)
- [ ] Check packages (`twine check dist/*`)
- [ ] Test installation locally
- [ ] Upload to TestPyPI (optional)
- [ ] Upload to PyPI (`twine upload dist/*`)
- [ ] Verify on PyPI website
- [ ] Update GitHub README with PyPI badge
- [ ] Create GitHub release
- [ ] Announce on social media

After publishing:

- [ ] Test `pip install code-compass` works
- [ ] Test CLI commands work
- [ ] Monitor PyPI download stats
- [ ] Respond to issues on GitHub
- [ ] Plan next release

---

## 🎉 Ready to Publish!

Everything is prepared and tested. You can now publish Code Compass to PyPI!

**Quick publish**:
```bash
cd ~/code-compass
twine upload dist/*
```

Good luck! 🚀

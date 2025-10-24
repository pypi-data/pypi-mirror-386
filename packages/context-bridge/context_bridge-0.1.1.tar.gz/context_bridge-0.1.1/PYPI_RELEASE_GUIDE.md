# PyPI Release Guide for Context Bridge

This guide provides step-by-step instructions for publishing Context Bridge to PyPI (Python Package Index).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Account Setup](#account-setup)
- [Package Configuration](#package-configuration)
- [Testing on Test PyPI](#testing-on-test-pypi)
- [Publishing to Production PyPI](#publishing-to-production-pypi)
- [Post-Publication](#post-publication)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- Python 3.8+ installed
- uv package manager (or pip)
- Git and GitHub account (optional but recommended)
- PyPI account (create below)

### Software Installation

```bash
# Install build tools
pip install build twine

# Or with uv (if using uv)
uv pip install build twine
```

## Account Setup

### 1. Create PyPI Account

**Production PyPI**:
1. Go to https://pypi.org/account/register/
2. Create account with:
   - **Username**: Ideally same as GitHub username
   - **Email**: Your email address
   - **Password**: Strong password
3. Verify email address

**Test PyPI** (strongly recommended):
1. Go to https://test.pypi.org/account/register/
2. Create account with same credentials as above
3. Verify email address

### 2. Generate API Tokens

#### Production PyPI Token

1. Log in to https://pypi.org/account/login/
2. Navigate to "Account settings" → "API tokens"
3. Click "Add API token"
4. Name: `context-bridge-release`
5. Scope: Entire account (or select project when available)
6. Copy token (starts with `pypi-`): **Save this securely!**

#### Test PyPI Token

1. Log in to https://test.pypi.org/account/login/
2. Navigate to "Account settings" → "API tokens"
3. Click "Add API token"
4. Name: `context-bridge-test`
5. Scope: Entire account
6. Copy token: **Save this securely!**

### 3. Store Credentials Locally

**Option A: Using .pypirc file** (Not recommended for security)

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    test-pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[test-pypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

**Option B: Using environment variables** (More secure)

```bash
# In PowerShell
$env:TWINE_REPOSITORY_URL = "https://upload.pypi.org/legacy/"
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-YOUR_TOKEN_HERE"
```

**Option C: Using keyring** (Recommended)

```bash
pip install keyring keyring-pass

# Store credentials
keyring set https://upload.pypi.org/legacy/ __token__
# Paste your token when prompted
```

## Package Configuration

### 1. Verify pyproject.toml

Ensure all required metadata is present:

```toml
[project]
name = "context-bridge"
version = "0.1.0"  # Update this for releases
description = "Unified Python package for RAG documentation management"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = [
    "rag",
    "documentation",
    "embedding",
    "vector-search",
    "mcp",
    "ai-agents",
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/context_bridge"
Repository = "https://github.com/YOUR_USERNAME/context_bridge"
Issues = "https://github.com/YOUR_USERNAME/context_bridge/issues"
```

### 2. Check for Required Files

- ✅ `README.md` - Display on PyPI page
- ✅ `LICENSE` - License file (MIT)
- ✅ `.gitignore` - Git ignore rules
- ✅ `CHANGELOG.md` - Release notes
- ✅ `pyproject.toml` - Package configuration

### 3. Verify Package Structure

```
context_bridge/
├── __init__.py          # Must have __version__
├── config.py
├── core.py
├── database/
├── service/
└── ...other modules...
```

## Testing on Test PyPI

### 1. Build Distributions

```bash
cd z:\code\ctx_bridge

# Build wheel and source distribution
python -m build

# Output:
# dist/context_bridge-0.1.0-py3-none-any.whl
# dist/context_bridge-0.1.0.tar.gz
```

### 2. Validate Package

```bash
# Check metadata
twine check dist/*

# Expected output:
# Checking dist/context_bridge-0.1.0-py3-none-any.whl: PASSED
# Checking dist/context_bridge-0.1.0.tar.gz: PASSED
```

### 3. Upload to Test PyPI

```bash
# Using environment variables
set TWINE_REPOSITORY_URL=https://test.pypi.org/legacy/
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-YOUR_TEST_TOKEN

twine upload dist/*

# Or specify directly
twine upload --repository test-pypi dist/*
```

Expected output:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading context_bridge-0.1.0-py3-none-any.whl
Uploading context_bridge-0.1.0.tar.gz
View at: https://test.pypi.org/project/context-bridge/
```

### 4. Test Installation

```bash
# Fresh environment (or use virtualenv)
pip install --index-url https://test.pypi.org/simple/ context-bridge

# Test import
python -c "import context_bridge; print(context_bridge.__version__)"

# Should output: 0.1.0
```

### 5. Verify Package Page

Visit: https://test.pypi.org/project/context-bridge/

Check:
- ✅ Project name displays
- ✅ Description shows correctly
- ✅ README renders
- ✅ Requirements listed
- ✅ Classifiers appear
- ✅ Links work (Homepage, Repository, Issues)

### 6. Clean Up Test

```bash
# Delete test distribution files (optional)
cd dist
rm -r *
```

## Publishing to Production PyPI

### 1. Build Clean Distributions

```bash
# Clean old builds
rm -r build/ dist/ *.egg-info/

# Build fresh distributions
python -m build

# Verify
twine check dist/*
```

### 2. Upload to Production PyPI

```bash
# Using environment variables
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-YOUR_PRODUCTION_TOKEN

twine upload dist/*

# Or specify repository
twine upload --repository pypi dist/*
```

**Do NOT upload to production until:**
- ✅ Test PyPI upload successful
- ✅ Test installation works
- ✅ README renders correctly
- ✅ All tests passing
- ✅ Version number updated
- ✅ CHANGELOG updated
- ✅ GitHub release created

### 3. Verify Production Upload

1. Visit https://pypi.org/project/context-bridge/
2. Verify within 5-10 minutes (PyPI cache)
3. Check package details display correctly

### 4. Test Production Installation

```bash
# Wait 5-10 minutes for PyPI indexing
pip install --upgrade pip
pip install context-bridge

# Test
python -c "import context_bridge; print(context_bridge.__version__)"
```

## Post-Publication

### 1. Update Version for Next Development

```python
# context_bridge/__init__.py
__version__ = "0.2.0.dev0"  # Next version
```

```toml
# pyproject.toml
version = "0.2.0.dev0"
```

### 2. Commit and Push

```bash
git add context_bridge/__init__.py pyproject.toml
git commit -m "Bump development version to 0.2.0.dev0"
git push origin main
```

### 3. Update GitHub with Release Info

```bash
# Create GitHub release (if not done)
gh release create v0.1.0 \
  --title "Release v0.1.0" \
  --notes "Published to PyPI: https://pypi.org/project/context-bridge/0.1.0/"
```

### 4. Announce Release

- Post on social media
- Announce on relevant forums/communities
- Update project website
- Share in documentation

## Package Variants

### Installation with Extras

Users can install with optional dependencies:

```bash
# Core only (default)
pip install context-bridge

# With MCP server
pip install context-bridge[mcp]

# With Streamlit UI
pip install context-bridge[ui]

# With all features
pip install context-bridge[all]

# With development tools
pip install context-bridge[dev]
```

These are defined in `pyproject.toml`:
```toml
[project.optional-dependencies]
mcp = ["mcp[cli]>=1.0.0"]
ui = ["streamlit>=1.28.0"]
dev = [...]
all = ["context-bridge[mcp,ui,dev]"]
```

## Troubleshooting

### "Invalid distribution" Error

**Issue**: `twine check` fails with validation errors

**Solution**:
1. Check `pyproject.toml` syntax
2. Ensure `README.md` is valid Markdown
3. Verify classifiers are correct
4. Check for special characters in metadata

```bash
# Validate with more detail
python -m build --verbose
```

### "403 Forbidden" Error

**Issue**: Upload fails with 403 error

**Solution**:
1. Check token is correct and not expired
2. Verify token has upload permissions
3. Check package name isn't already taken
4. Ensure you own the package namespace

### "Project already exists" Error

**Issue**: Can't upload new version

**Solution**:
1. Check version number in `pyproject.toml`
2. Don't reuse existing version numbers
3. Follow semantic versioning

### Files Not Uploading

**Issue**: `twine` says files already uploaded

**Solution**:
```bash
# Delete local dist and rebuild
rm -r dist/
python -m build

# Re-check and upload
twine check dist/*
twine upload dist/* --skip-existing
```

### Can't Find Package After Upload

**Issue**: `pip install` fails to find package

**Solution**:
1. Wait 5-10 minutes for PyPI indexing
2. Check exact package name: `pip search context-bridge`
3. Verify on https://pypi.org/project/context-bridge/
4. Try installing from test PyPI first

## Security Best Practices

1. ✅ Use API tokens instead of passwords
2. ✅ Store tokens securely (keyring, environment variables)
3. ✅ Use different tokens for test and production PyPI
4. ✅ Rotate tokens periodically
5. ✅ Don't commit tokens to git (add to `.gitignore`)
6. ✅ Use HTTPS for all connections
7. ✅ Keep build tools updated

## Useful Commands

```bash
# List all packages you maintain
pip index packages

# Show package info
pip show context-bridge

# Download package for inspection
pip download context-bridge --no-deps

# Install specific version
pip install context-bridge==0.1.0

# Show versions available
pip index versions context-bridge

# Uninstall
pip uninstall context-bridge
```

## Resources

- **PyPI Help**: https://pypi.org/help/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Python Packaging**: https://packaging.python.org/
- **PEP 427 - Wheel Format**: https://peps.python.org/pep-0427/
- **Semantic Versioning**: https://semver.org/

## Release Checklist Summary

```
✅ Prerequisites installed (build, twine)
✅ PyPI accounts created (main and test)
✅ API tokens generated and stored
✅ pyproject.toml metadata correct
✅ README.md and LICENSE files present
✅ Package structure verified
✅ Tests passing (254/254)
✅ Version number updated
✅ CHANGELOG updated
✅ Test PyPI upload successful
✅ Test installation verified
✅ Production PyPI upload successful
✅ Production installation verified
✅ GitHub release created
✅ Development version bumped
✅ Release announced
```

---

**Current Version**: 0.1.0  
**Status**: Ready for PyPI Release  
**Last Updated**: 2025-10-23

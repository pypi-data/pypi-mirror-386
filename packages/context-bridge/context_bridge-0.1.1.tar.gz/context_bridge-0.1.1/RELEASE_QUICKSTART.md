# Release Quick Start Guide

Complete guide to release Context Bridge on GitHub and PyPI.

## 📋 Quick Summary

1. **Prepare** - Update versions, test code
2. **Build** - Create distribution packages
3. **Test** - Upload to Test PyPI
4. **Release** - Upload to production PyPI
5. **Publish** - Create GitHub release

**Time estimate**: 30 minutes (including waiting for PyPI indexing)

---

## Step 1: Prepare Release (5 minutes)

### Update Documentation

```bash
cd z:\code\ctx_bridge

# Update CHANGELOG.md with release notes
# Update version numbers:
# - context_bridge/__init__.py: __version__ = "0.1.0"
# - pyproject.toml: version = "0.1.0"
```

### Verify Everything Works

```bash
# Run tests
uv run pytest tests/unit/ -q

# Check code quality
uv run black --check context_bridge/
uv run ruff check context_bridge/
```

**Expected**: All tests passing (254/254), no formatting issues

---

## Step 2: Build Distributions (2 minutes)

```bash
# Clean old builds
rm -r build/ dist/ *.egg-info/

# Build
python -m build

# Check built files
ls dist/

# Validate
twine check dist/*
```

**Expected**: 
- `dist/context_bridge-0.1.0-py3-none-any.whl`
- `dist/context_bridge-0.1.0.tar.gz`

---

## Step 3: Setup PyPI Accounts (If First Time)

### Create Accounts

1. **PyPI** → https://pypi.org/account/register/
2. **Test PyPI** → https://test.pypi.org/account/register/

### Create API Tokens

1. **Production**: https://pypi.org/manage/account/tokens/
   - Click "Add API token"
   - Copy token (save securely!)

2. **Test**: https://test.pypi.org/manage/account/tokens/
   - Click "Add API token"
   - Copy token (save securely!)

### Store Credentials

**Option A: Environment Variables** (Recommended for automation)

```bash
# PowerShell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-YOUR_TOKEN_HERE"  # From PyPI account
```

**Option B: keyring** (Most secure)

```bash
pip install keyring

keyring set https://upload.pypi.org/legacy/ __token__
# Paste your production PyPI token when prompted
```

---

## Step 4: Test on Test PyPI (10 minutes)

### Upload to Test PyPI

```bash
# Set test token environment variable or use keyring
twine upload --repository test-pypi dist/*
```

**Expected output**:
```
Uploading context_bridge-0.1.0-py3-none-any.whl
Uploading context_bridge-0.1.0.tar.gz
View at: https://test.pypi.org/project/context-bridge/
```

### Verify Test Upload

```bash
# Visit: https://test.pypi.org/project/context-bridge/

# Test installation
pip install --index-url https://test.pypi.org/simple/ context-bridge

python -c "import context_bridge; print(context_bridge.__version__)"
# Should print: 0.1.0
```

**Checklist**:
- ✅ Package displays on Test PyPI
- ✅ README renders correctly
- ✅ Installation works
- ✅ Version is correct

---

## Step 5: Setup GitHub Repository

### Create Repository

1. Go to https://github.com/new
2. Fill in:
   - **Name**: `context_bridge` or `context-bridge`
   - **Description**: "Unified Python package for RAG documentation management"
   - **Public** ✓
   - Initialize with: None

3. Add topics: `rag`, `documentation`, `vector-search`, `mcp`, `ai`, `python`

### Initialize Git Locally

```bash
cd z:\code\ctx_bridge

git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

git add .
git commit -m "Initial commit: Context Bridge v0.1.0"

git remote add origin https://github.com/YOUR_USERNAME/context_bridge.git
git branch -M main
git push -u origin main
```

### Create and Push Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

## Step 6: Release to Production PyPI (5 minutes)

### Upload to PyPI

```bash
# Set production token environment variable or use keyring
twine upload dist/*

# You'll see:
# Uploading context_bridge-0.1.0-py3-none-any.whl
# Uploading context_bridge-0.1.0.tar.gz
# View at: https://pypi.org/project/context-bridge/
```

### Verify Production Upload

```bash
# Wait 5-10 minutes for indexing

# Check: https://pypi.org/project/context-bridge/

# Test installation
pip install context-bridge

python -c "import context_bridge; print(context_bridge.__version__)"
```

---

## Step 7: Create GitHub Release

### Using Web UI

1. Go to https://github.com/YOUR_USERNAME/context_bridge/releases
2. Click "Draft a new release"
3. Select tag: `v0.1.0`
4. Title: "Release v0.1.0"
5. Description: Copy from CHANGELOG.md
6. Click "Publish release"

### Using GitHub CLI

```bash
gh release create v0.1.0 \
  --title "Release v0.1.0" \
  --notes-file CHANGELOG.md
```

---

## Automated Release Script

Use the provided `release.py` script:

```bash
# Just check everything is ready
python release.py --version 0.1.0 --check

# Build distributions
python release.py --version 0.1.0 --build

# Test on Test PyPI
python release.py --version 0.1.0 --test

# Full release (checks, builds, uploads)
python release.py --version 0.1.0 --release
```

---

## Post-Release (5 minutes)

### Update Version for Next Development

```python
# context_bridge/__init__.py
__version__ = "0.2.0.dev0"

# pyproject.toml
version = "0.2.0.dev0"
```

### Commit

```bash
git add context_bridge/__init__.py pyproject.toml
git commit -m "Bump development version to 0.2.0.dev0"
git push origin main
```

### Announce

- Post on Twitter/LinkedIn
- Share in Python communities
- Update project website
- Share release link

---

## Troubleshooting

### "403 Forbidden" on PyPI Upload

- Check token is correct and not expired
- Verify token has upload permissions
- Make sure package name is available

### Package Not Found After Upload

- Wait 5-10 minutes for PyPI to index
- Check https://pypi.org/project/context-bridge/ directly
- Try installing after waiting

### Can't Push to GitHub

- Check you have write permissions
- Verify personal access token is valid
- Use HTTPS or SSH properly configured

---

## Verification Checklist

Before release, verify:

```
✅ All tests passing (254/254)
✅ Code quality checks pass (black, ruff)
✅ CHANGELOG updated
✅ Version numbers updated
✅ Build succeeds locally
✅ Package validates (twine check)
✅ Test PyPI upload successful
✅ Test PyPI installation works
✅ Production PyPI upload successful
✅ Production installation works
✅ GitHub repository created
✅ Code pushed to GitHub
✅ Tag pushed to GitHub
✅ GitHub release created
✅ Development version bumped
```

---

## Key Files

- **Release automation**: `release.py`
- **Detailed guides**: 
  - `GITHUB_RELEASE_GUIDE.md` - GitHub setup and release
  - `PYPI_RELEASE_GUIDE.md` - PyPI setup and release
- **Configuration**: `pyproject.toml`
- **Changelog**: `CHANGELOG.md`
- **Package**: `context_bridge/__init__.py`

---

## Resources

- **PyPI**: https://pypi.org
- **Test PyPI**: https://test.pypi.org
- **GitHub**: https://github.com
- **Semantic Versioning**: https://semver.org
- **Python Packaging**: https://packaging.python.org

---

**Status**: Ready for release  
**Current Version**: 0.1.0  
**Estimated Time**: 30-45 minutes

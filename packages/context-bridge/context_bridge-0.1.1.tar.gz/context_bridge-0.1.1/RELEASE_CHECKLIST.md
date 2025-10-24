# Release Checklist for Context Bridge

Complete this checklist before releasing a new version to PyPI and GitHub.

## Pre-Release Verification

- [ ] **All tests passing**
  ```bash
  uv run pytest tests/ -v
  ```
  Current status: ✅ 254/254 unit tests passing, 10/18 E2E tests passing
  
- [ ] **Code quality checks**
  ```bash
  uv run black --check context_bridge/
  uv run ruff check context_bridge/
  uv run mypy context_bridge/
  ```

- [ ] **Build succeeds locally**
  ```bash
  uv build
  ```

- [ ] **Coverage acceptable** (aim for >80%)
  ```bash
  uv run pytest tests/ --cov=context_bridge --cov-report=term-missing
  ```

## Version Management

- [ ] **Update version number**
  - [ ] Update `context_bridge/__init__.py` - `__version__`
  - [ ] Update `pyproject.toml` - `[project]` version field
  - [ ] Update `CHANGELOG.md` with release notes

- [ ] **Semantic versioning check**
  - [ ] Patch (0.1.x): Bug fixes only
  - [ ] Minor (0.x.0): New features (backward compatible)
  - [ ] Major (x.0.0): Breaking changes

## Documentation

- [ ] **Update CHANGELOG.md** with:
  - [ ] Version number and date
  - [ ] New features
  - [ ] Bug fixes
  - [ ] Breaking changes
  - [ ] Dependencies updated

- [ ] **Review README.md** for accuracy
  
- [ ] **Update GitHub docs** if using GitHub Pages
  ```bash
  mkdocs build
  ```

- [ ] **Check inline code docstrings** are complete

## GitHub Preparation

- [ ] **Create/update GitHub repository**
  - [ ] Repository name: `context_bridge` or `context-bridge`
  - [ ] Description: "Unified Python package for RAG documentation management"
  - [ ] Add topics: `rag`, `documentation`, `vector-search`, `mcp`, `ai`, `python`

- [ ] **Update pyproject.toml URLs**
  ```toml
  [project.urls]
  Homepage = "https://github.com/YOUR_USERNAME/context_bridge"
  Documentation = "https://github.com/YOUR_USERNAME/context_bridge#readme"
  Repository = "https://github.com/YOUR_USERNAME/context_bridge"
  Issues = "https://github.com/YOUR_USERNAME/context_bridge/issues"
  ```

- [ ] **Update author info in pyproject.toml**
  ```toml
  authors = [
      {name = "Your Name", email = "your.email@example.com"},
  ]
  ```

- [ ] **Initialize Git repository** (if not already)
  ```bash
  git init
  git add .
  git commit -m "Initial commit: context_bridge v0.1.0"
  git remote add origin https://github.com/YOUR_USERNAME/context_bridge.git
  git branch -M main
  git push -u origin main
  ```

- [ ] **Create GitHub release**
  - [ ] Tag: `v0.1.0` (or appropriate version)
  - [ ] Title: "Release v0.1.0"
  - [ ] Description: Copy from CHANGELOG.md
  - [ ] Attach built distributions (optional)

## PyPI Preparation

- [ ] **Create PyPI accounts**
  - [ ] Main account: https://pypi.org/account/register/
  - [ ] Test PyPI: https://test.pypi.org/account/register/

- [ ] **Create PyPI API token**
  - [ ] For production PyPI: https://pypi.org/manage/account/
  - [ ] For test PyPI: https://test.pypi.org/manage/account/

- [ ] **Configure local publishing**
  - [ ] Create `~/.pypirc` (or use GitHub Actions)
  ```ini
  [distutils]
  index-servers =
      pypi
      test-pypi

  [pypi]
  repository = https://upload.pypi.org/legacy/
  username = __token__
  password = pypi-AgEIcHlwaS5vcmc...

  [test-pypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = pypi-AgEIcHRlc3QucHl...
  ```

- [ ] **Verify package metadata**
  ```bash
  python -m build
  twine check dist/*
  ```

## Publishing

### Test PyPI First (Recommended)

- [ ] **Build distribution packages**
  ```bash
  uv build
  ```

- [ ] **Upload to Test PyPI**
  ```bash
  twine upload --repository test-pypi dist/*
  ```

- [ ] **Test installation from Test PyPI**
  ```bash
  pip install --index-url https://test.pypi.org/simple/ context-bridge
  python -c "import context_bridge; print(context_bridge.__version__)"
  ```

### Publish to Production PyPI

- [ ] **Upload to Production PyPI**
  ```bash
  twine upload dist/*
  ```

- [ ] **Verify on PyPI**
  - [ ] Visit https://pypi.org/project/context-bridge/
  - [ ] Check package info displays correctly
  - [ ] Verify documentation renders

- [ ] **Test installation**
  ```bash
  pip install context-bridge
  python -c "import context_bridge; print(context_bridge.__version__)"
  ```

## Post-Release

- [ ] **Create GitHub release** with release notes
  - [ ] Tag: `v0.1.0`
  - [ ] Include changelog highlights
  - [ ] Add installation instructions

- [ ] **Announce release**
  - [ ] GitHub Discussions (if enabled)
  - [ ] Social media / community forums
  - [ ] Package tracking sites

- [ ] **Monitor for issues**
  - [ ] Watch GitHub issues for user reports
  - [ ] Check PyPI statistics

- [ ] **Plan next release**
  - [ ] Backlog items
  - [ ] Known issues to address
  - [ ] Community feedback

## Additional Resources

### Build & Publishing Tools
- **Hatchling**: Build backend (configured in pyproject.toml)
- **Build**: Standard build tool - `pip install build`
- **Twine**: Upload to PyPI - `pip install twine`

### Useful Commands
```bash
# Install build tools
pip install build twine

# Build distributions
python -m build

# Check package metadata
twine check dist/*

# Upload to test PyPI
twine upload --repository test-pypi dist/*

# Upload to production PyPI
twine upload dist/*

# Install from PyPI
pip install context-bridge

# Install with extras
pip install context-bridge[mcp,ui]
pip install context-bridge[all]
```

### PyPI Project URLs
- Production: https://pypi.org/project/context-bridge/
- Test: https://test.pypi.org/project/context-bridge/

### GitHub Setup
- Create personal access token: https://github.com/settings/tokens
- Configure Actions secrets if using CI/CD
- Set up branch protection rules

---

**Current Status**: Ready for v0.1.0 release preparation
**Last Updated**: 2025-10-23

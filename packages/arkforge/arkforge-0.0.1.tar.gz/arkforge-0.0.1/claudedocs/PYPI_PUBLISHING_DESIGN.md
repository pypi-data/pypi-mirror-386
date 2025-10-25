# PyPI Publishing Design Document

**Project**: ArkForge Python SDK
**Version**: 0.1.0
**Date**: 2025-10-24
**Status**: Design Phase

## Executive Summary

This document outlines the design and implementation plan for publishing the ArkForge Python SDK to PyPI (Python Package Index), transitioning from GitHub-only distribution to public package availability via `pip install arkforge`.

---

## 🔴 CRITICAL: Public Code Exposure

### Does Code Get Exposed Publicly on PyPI?

**YES - All packaged code will be publicly accessible.**

When you publish to PyPI:
- ✅ **Source code is public**: Anyone can download and inspect your package source
- ✅ **No private packages**: PyPI is a public index (private options require paid hosting)
- ✅ **Downloadable by anyone**: `pip download arkforge` exposes all code
- ✅ **Version control**: All published versions remain accessible indefinitely

### What Gets Included in the PyPI Package?

Based on current `pyproject.toml` configuration:

```toml
[tool.hatch.build.targets.wheel]
packages = ["arkforge"]
```

**✅ INCLUDED (Public)**:
- `arkforge/` directory (all SDK source code)
  - Client implementation
  - Models and validation logic
  - HTTP handling and retry logic
  - Rate limiting algorithms
  - Error handling
  - Configuration management

**❌ EXCLUDED (Not in package)**:
- `tests/` - Test suite (root level, not packaged)
- `examples/` - Example code (not packaged)
- `test_local.py` - Local testing script (not packaged)
- `.github/` - CI/CD workflows (not packaged)
- Documentation files in root (README included in metadata only)

### Security Implications

🔴 **BEFORE PUBLISHING - VERIFY**:
1. ✅ No hardcoded API keys in `arkforge/` code (verified clean)
2. ✅ No proprietary algorithms you want to protect
3. ✅ No business logic considered trade secrets
4. ✅ No sensitive configuration or credentials
5. ⚠️ Note: `test_local.py` contains actual-looking API key but won't be packaged

**Recommendation**:
- Review all code in `arkforge/` directory for sensitive information
- Consider if portfolio optimization algorithms should be public
- Ensure DeFi strategies are acceptable to expose

---

## Current State Analysis

### ✅ Already Configured

Your project is **90% ready** for PyPI publishing:

1. **Build System**: ✅ Hatchling configured in pyproject.toml
2. **Package Metadata**: ✅ Complete (name, version, description, dependencies)
3. **Package Structure**: ✅ Proper `arkforge/` directory structure
4. **Dependencies**: ✅ Specified in pyproject.toml
5. **License**: ✅ MIT License declared
6. **README**: ✅ Comprehensive documentation
7. **Classifiers**: ✅ PyPI classifiers defined
8. **Type Hints**: ✅ Fully typed with mypy validation
9. **Tests**: ✅ Comprehensive test suite with pytest

### ❌ Missing for PyPI

1. Build tools not installed
2. PyPI account not created
3. Upload tools not configured
4. Publishing workflow not documented
5. README doesn't document PyPI installation
6. No automated publishing via GitHub Actions
7. No .gitignore file (recommended but not required)

---

## PyPI Publishing Requirements

### 1. Tools Installation

```bash
# Install build tools
pip install --upgrade build twine

# Verify installation
python -m build --version
twine --version
```

**Tools Purpose**:
- `build`: Creates wheel (.whl) and source distribution (.tar.gz)
- `twine`: Securely uploads packages to PyPI

### 2. PyPI Account Setup

**Steps**:
1. Create account at https://pypi.org/account/register/
2. Verify email address
3. Enable 2FA (required for new projects)
4. Create API token at https://pypi.org/manage/account/token/
5. Save token securely (starts with `pypi-`)

**API Token Scopes**:
- **Project-specific**: Recommended after first upload
- **Account-wide**: Required for first upload (no project exists yet)

### 3. Build Process

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build package
python -m build

# Verify build artifacts
ls -lh dist/
# Should show:
# - arkforge-0.1.0-py3-none-any.whl
# - arkforge-0.1.0.tar.gz
```

### 4. Upload Process

**Test PyPI (Recommended First)**:
```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ arkforge
```

**Production PyPI**:
```bash
# Upload to production PyPI
python -m twine upload dist/*

# Verify upload
pip install arkforge
```

### 5. Authentication Configuration

**Method 1: Interactive (First Time)**:
```bash
twine upload dist/*
# Username: __token__
# Password: pypi-AgEIcHlwaS5vcmcC... (your API token)
```

**Method 2: .pypirc File (Automated)**:
```ini
# ~/.pypirc
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...
```

**Method 3: Environment Variables (CI/CD)**:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcC...
twine upload dist/*
```

---

## Publishing Workflow Design

### Manual Publishing Workflow

```bash
# 1. Update version in pyproject.toml
# [project]
# version = "0.1.1"

# 2. Update CHANGELOG.md
# Add release notes for new version

# 3. Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main --tags

# 4. Clean and build
rm -rf dist/ build/ *.egg-info/
python -m build

# 5. Upload to PyPI
twine upload dist/*

# 6. Verify installation
pip install --upgrade arkforge
python -c "from arkforge import __version__; print(__version__)"
```

### Automated Publishing with GitHub Actions

**Workflow File**: `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for trusted publishing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

**GitHub Secrets Configuration**:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secret: `PYPI_API_TOKEN` with your PyPI API token
3. Create GitHub release to trigger workflow

### Trusted Publishing (Recommended)

PyPI supports "Trusted Publishing" via OIDC (no API tokens needed):

**Benefits**:
- No long-lived API tokens
- More secure authentication
- Automatic rotation
- GitHub-native integration

**Setup**:
1. Create package on PyPI (first upload with API token)
2. Configure trusted publisher at https://pypi.org/manage/project/arkforge/settings/
3. Add GitHub repository and workflow details
4. Remove `password:` from GitHub Actions (uses OIDC)

---

## Version Management Strategy

### Semantic Versioning (SemVer)

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (0.x.x → 1.0.0)
- **MINOR**: New features, backwards compatible (0.1.0 → 0.2.0)
- **PATCH**: Bug fixes, backwards compatible (0.1.0 → 0.1.1)

### Version Lifecycle

**Pre-release Versions**:
- `0.1.0a1` - Alpha release
- `0.1.0b1` - Beta release
- `0.1.0rc1` - Release candidate

**Current Status**:
- Version `0.1.0` indicates beta/initial development
- Recommend: Stay in 0.x.x until API stabilizes
- Move to 1.0.0 when API is stable and battle-tested

### Version Update Locations

1. `pyproject.toml` → `[project] version = "0.1.0"`
2. `arkforge/version.py` → Check if exists, update if present
3. `CHANGELOG.md` → Document changes for each version

---

## Documentation Updates

### README.md Changes

**Add PyPI Installation Section**:

```markdown
## Installation

### From PyPI (Recommended)

```bash
# Install latest stable version
pip install arkforge

# Install specific version
pip install arkforge==0.1.0

# Install with optional dependencies
pip install arkforge[dev]  # Development tools
pip install arkforge[docs]  # Documentation tools
```

### From GitHub (Development)

```bash
# Install from main branch
pip install git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git
```
```

**Add PyPI Badge**:
```markdown
[![PyPI version](https://badge.fury.io/py/arkforge.svg)](https://badge.fury.io/py/arkforge)
[![PyPI downloads](https://img.shields.io/pypi/dm/arkforge.svg)](https://pypi.org/project/arkforge/)
```

### Update Project URLs

Already configured in `pyproject.toml`:
```toml
[project.urls]
Homepage = "https://github.com/arkonix-project/arkforge-sdk-py"
Repository = "https://github.com/arkonix-project/arkforge-sdk-py"
Changelog = "https://github.com/arkonix-project/arkforge-sdk-py/blob/main/CHANGELOG.md"
Issues = "https://github.com/arkonix-project/arkforge-sdk-py/issues"
```

**Recommend Adding**:
```toml
Documentation = "https://docs.arkforge.io"  # If docs site exists
PyPI = "https://pypi.org/project/arkforge/"
```

---

## Package Verification

### Pre-Publishing Checklist

```bash
# 1. Build package locally
python -m build

# 2. Check package contents
tar -tzf dist/arkforge-0.1.0.tar.gz | head -20

# 3. Verify wheel contents
unzip -l dist/arkforge-0.1.0-py3-none-any.whl

# 4. Run twine check
twine check dist/*

# 5. Test installation locally
pip install dist/arkforge-0.1.0-py3-none-any.whl

# 6. Verify imports
python -c "from arkforge import ArkForgeClient; print('Success')"

# 7. Run tests against installed package
pytest tests/

# 8. Check metadata
pip show arkforge
```

### Post-Publishing Verification

```bash
# 1. Install from PyPI
pip install arkforge

# 2. Verify version
python -c "import arkforge; print(arkforge.__version__)"

# 3. Check PyPI page
# Visit: https://pypi.org/project/arkforge/

# 4. Test in fresh environment
python -m venv test_env
source test_env/bin/activate
pip install arkforge
python -c "from arkforge import ArkForgeClient"
```

---

## Security & Best Practices

### Pre-Publishing Security Review

**Code Audit**:
- [ ] No hardcoded credentials in `arkforge/` directory
- [ ] No API keys or tokens in source code
- [ ] No sensitive business logic you want protected
- [ ] No proprietary algorithms considered trade secrets
- [ ] Environment variables used for configuration

**Package Security**:
- [ ] Dependencies are pinned or have minimum versions
- [ ] No known vulnerabilities in dependencies
- [ ] License is appropriate (MIT is permissive)
- [ ] Copyright notices are correct

### Token Management

**Never commit**:
- PyPI API tokens
- `.pypirc` file
- Any credentials in code

**Recommended**:
- Use GitHub Secrets for CI/CD
- Enable 2FA on PyPI account
- Use project-scoped API tokens (not account-wide)
- Rotate tokens periodically

### .gitignore Recommendations

**Create `.gitignore`**:
```gitignore
# Build artifacts
dist/
build/
*.egg-info/
__pycache__/
*.pyc

# Virtual environments
venv/
env/
.venv/

# PyPI credentials
.pypirc

# IDE
.vscode/
.idea/
*.swp

# Testing
.coverage
htmlcov/
.pytest_cache/

# Local testing
test_local.py
*.local.py
```

---

## Migration Strategy

### Phase 1: Preparation (Current)
- ✅ Review code for public exposure concerns
- ✅ Understand PyPI publishing process
- ✅ Design publishing workflow
- ⏳ Create PyPI account
- ⏳ Install build tools

### Phase 2: Test Publishing
- ⏳ Build package locally
- ⏳ Upload to Test PyPI
- ⏳ Verify installation from Test PyPI
- ⏳ Test all functionality
- ⏳ Review package on Test PyPI site

### Phase 3: Production Publishing
- ⏳ Upload to production PyPI
- ⏳ Verify installation
- ⏳ Update documentation
- ⏳ Announce availability

### Phase 4: Automation (Optional)
- ⏳ Set up GitHub Actions workflow
- ⏳ Configure trusted publishing
- ⏳ Test automated release process

---

## Step-by-Step Implementation Guide

### Getting Started (What You Need to Do)

**1. Install Tools (5 minutes)**
```bash
pip install --upgrade build twine
```

**2. Create PyPI Account (10 minutes)**
- Visit: https://pypi.org/account/register/
- Verify email
- Enable 2FA
- Create API token (save securely)

**3. Test Build Locally (5 minutes)**
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build package
python -m build

# Check build
twine check dist/*
```

**4. Upload to Test PyPI (10 minutes)**
```bash
# Create Test PyPI account: https://test.pypi.org/account/register/
# Create Test PyPI API token

# Upload
twine upload --repository testpypi dist/*
# Username: __token__
# Password: <your-testpypi-token>

# Test installation
pip install --index-url https://test.pypi.org/simple/ arkforge
```

**5. Upload to Production PyPI (5 minutes)**
```bash
twine upload dist/*
# Username: __token__
# Password: <your-pypi-token>
```

**6. Verify Publication (5 minutes)**
```bash
# Install from PyPI
pip install arkforge

# Test import
python -c "from arkforge import ArkForgeClient; print('Success!')"

# Check PyPI page
# https://pypi.org/project/arkforge/
```

**7. Update Documentation (15 minutes)**
- Update README.md with PyPI installation instructions
- Add PyPI badges
- Update CHANGELOG.md

**Total Time**: ~1 hour for first publication

---

## Common Issues & Solutions

### Issue: Package name already taken
**Solution**: Choose different name in `pyproject.toml`

### Issue: Version already exists on PyPI
**Solution**: Bump version number, rebuild, reupload

### Issue: Twine authentication fails
**Solution**: Verify username is `__token__` (not your username)

### Issue: Package won't install
**Solution**: Check dependencies are available on PyPI

### Issue: Import fails after installation
**Solution**: Verify package name matches import name

---

## Comparison: GitHub vs PyPI Distribution

| Aspect | GitHub | PyPI |
|--------|--------|------|
| **Installation** | `pip install git+ssh://git@...` | `pip install arkforge` |
| **Authentication** | SSH keys or tokens | None (public) |
| **Version Control** | Git tags/branches | Version numbers |
| **Discovery** | GitHub search | PyPI search, pip install |
| **Private Code** | Possible (private repo) | Not possible (public only) |
| **Dependency Resolution** | Manual | Automatic with pip |
| **Corporate Firewalls** | Often blocked | Usually allowed |
| **Professional Perception** | Development/beta | Production-ready |
| **Update Notifications** | None | pip-outdated, dependabot |

---

## Recommendations

### 🔴 Before Publishing Decision

**Evaluate if PyPI is appropriate**:
- ✅ Code can be public
- ✅ Ready for wider adoption
- ✅ Prepared to support public users
- ✅ No proprietary algorithms to protect
- ✅ License is appropriate (MIT is permissive)

**If code must remain private**:
- Keep GitHub-only distribution
- Use private PyPI server (e.g., Gemfury, Artifactory)
- Use git+ssh installation method

### 🟡 Publishing Strategy

**Recommended Approach**:
1. Start with Test PyPI to practice
2. Publish 0.1.0 as "Beta" on production PyPI
3. Gather feedback from public users
4. Stabilize API based on feedback
5. Release 1.0.0 when ready for production use

**Version Strategy**:
- Stay in 0.x.x during beta phase
- Breaking changes OK in 0.x.x versions
- Move to 1.0.0 when API is stable

### 🟢 Future Enhancements

1. **Automated Publishing**: GitHub Actions on release
2. **Trusted Publishing**: OIDC authentication (no tokens)
3. **Documentation Site**: mkdocs-material with GitHub Pages
4. **Package Signing**: Sign packages with GPG
5. **Download Analytics**: Monitor usage via PyPI stats

---

## Conclusion

Your project is **already well-configured** for PyPI publishing. The main tasks are:

1. ✅ **Decision**: Confirm code can be public
2. ⏳ **Setup**: Create PyPI account and install tools
3. ⏳ **Test**: Upload to Test PyPI first
4. ⏳ **Publish**: Upload to production PyPI
5. ⏳ **Document**: Update README with pip install instructions

**Estimated Effort**: 1-2 hours for initial setup and first publication

**Code Exposure**: YES - All code in `arkforge/` will be publicly visible

**Benefits**: Easier installation, better discovery, professional package management

**Risks**: Code becomes public, anyone can inspect implementation details

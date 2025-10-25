# PyPI Publishing Guide

Complete step-by-step guide for publishing ArkForge SDK to PyPI.

## Prerequisites

✅ **Already Done**:
- [x] Build tools installed (`build` and `twine`)
- [x] Package built and validated locally
- [x] `.gitignore` configured
- [x] Sensitive API key removed from test files

## Quick Start

If you're already set up with PyPI credentials, just run:

```bash
# Build package
python -m build

# Upload to PyPI
twine upload dist/*
```

## First Time Setup

### 1. Create PyPI Account

**Production PyPI** (recommended to start here):
1. Visit: https://pypi.org/account/register/
2. Fill out registration form
3. Verify your email address
4. **Enable Two-Factor Authentication** (required for new projects)

**Test PyPI** (optional, for practice):
1. Visit: https://test.pypi.org/account/register/
2. Separate account from production PyPI
3. Good for testing before real publication

### 2. Create API Token

**For Production PyPI**:
1. Log in to https://pypi.org
2. Go to Account Settings: https://pypi.org/manage/account/
3. Scroll to "API tokens" section
4. Click "Add API token"
5. Token name: "ArkForge Publishing" (or any name you prefer)
6. Scope: "Entire account" (for first upload, then create project-specific token)
7. Click "Create token"
8. **IMPORTANT**: Copy the token immediately! It starts with `pypi-` and you won't see it again
9. Save it in a secure password manager

**For Test PyPI** (optional):
1. Same process at https://test.pypi.org/manage/account/

### 3. Configure Authentication

**Option A: Interactive (Recommended for First Time)**

When you run `twine upload`, you'll be prompted:
- Username: `__token__` (yes, literally the word "__token__")
- Password: `pypi-AgE...` (your full API token)

**Option B: Save in .pypirc (For Repeated Use)**

Create `~/.pypirc` file:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...  # Your actual token

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...  # Your Test PyPI token
```

**IMPORTANT**: Never commit `.pypirc` to git! It's already in `.gitignore`.

**Option C: Environment Variables (For CI/CD)**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcC...
twine upload dist/*
```

## Publishing Process

### Step 1: Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/

# Build wheel and source distribution
python -m build
```

**Output**: Creates `dist/` directory with:
- `arkforge-0.1.0-py3-none-any.whl` (wheel)
- `arkforge-0.1.0.tar.gz` (source distribution)

### Step 2: Validate Package

```bash
# Check package metadata and description
twine check dist/*
```

Should show:
```
Checking dist/arkforge-0.1.0-py3-none-any.whl: PASSED
Checking dist/arkforge-0.1.0.tar.gz: PASSED
```

### Step 3: Upload to Test PyPI (Optional but Recommended)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*
```

**Verify on Test PyPI**:
- Visit: https://test.pypi.org/project/arkforge/
- Check if package page looks correct
- Test installation:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ arkforge
  ```

### Step 4: Upload to Production PyPI

```bash
# Upload to production PyPI
twine upload dist/*
```

You'll see:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading arkforge-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading arkforge-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/arkforge/0.1.0/
```

### Step 5: Verify Publication

```bash
# Install from PyPI
pip install arkforge

# Test import
python -c "from arkforge import ArkForgeClient; print('Success!')"

# Check version
python -c "import arkforge; print(arkforge.__version__)"
```

**Check PyPI Page**:
- Visit: https://pypi.org/project/arkforge/
- Verify README displays correctly
- Check metadata (author, license, links)

## Updating to New Version

### 1. Update Version Number

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.1"  # Bump version
```

### 2. Update Changelog

Add entry to `CHANGELOG.md`:
```markdown
## [0.1.1] - 2025-10-24

### Added
- New feature description

### Fixed
- Bug fix description
```

### 3. Commit and Tag

```bash
# Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.1"

# Create git tag
git tag v0.1.1

# Push with tags
git push origin main --tags
```

### 4. Build and Upload

```bash
# Clean and rebuild
rm -rf dist/ build/
python -m build

# Validate
twine check dist/*

# Upload new version
twine upload dist/*
```

## Automated Publishing with GitHub Actions

### Setup GitHub Secrets

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI API token (starts with `pypi-`)
5. Click "Add secret"

### GitHub Actions Workflow

File: `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest

    permissions:
      contents: read

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

      - name: Check package
        run: twine check dist/*

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

### Using Automated Workflow

1. Make your changes and commit
2. Update version in `pyproject.toml`
3. Push to GitHub
4. Create a GitHub Release:
   - Go to Releases → Create new release
   - Tag: `v0.1.1`
   - Release title: `v0.1.1`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"
5. GitHub Actions will automatically build and publish to PyPI

## Trusted Publishing (Advanced - Most Secure)

PyPI supports OpenID Connect (OIDC) for GitHub Actions - no API tokens needed!

### Setup (After First Manual Upload)

1. Go to https://pypi.org/manage/project/arkforge/settings/
2. Click "Add a new publisher"
3. Fill in:
   - Owner: `arkonix-project`
   - Repository name: `arkforge-sdk-py`
   - Workflow name: `publish.yml`
   - Environment name: (leave empty)
4. Click "Add"

### Updated Workflow (No Secrets)

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
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

No `PYPI_API_TOKEN` secret needed with trusted publishing!

## Troubleshooting

### Error: "403 Forbidden: Invalid or non-existent authentication information"

**Solution**: Check authentication:
- Username must be `__token__` (not your PyPI username)
- Password must be full API token starting with `pypi-`
- Token must have correct scope (entire account for first upload)

### Error: "400 Bad Request: File already exists"

**Solution**: You can't re-upload the same version
- Bump version number in `pyproject.toml`
- Rebuild package
- Upload new version

### Error: "Package name already taken"

**Solution**: Someone else owns that package name
- Choose a different name in `pyproject.toml`
- Update all references in code
- Rebuild and upload

### Error: "Project name 'ArkForge' and 'arkforge' conflict"

**Solution**: PyPI treats names case-insensitively
- Package names are normalized (hyphens, underscores, case)
- Check if similar name exists: https://pypi.org/search/?q=arkforge

### Warning: Long description rendering failed

**Solution**: README has invalid syntax
- Check markdown formatting
- Validate with: `twine check dist/*`
- Fix README.md and rebuild

## Security Best Practices

### ✅ Do's

- ✅ Use API tokens (not username/password)
- ✅ Create project-scoped tokens after first upload
- ✅ Store tokens in password manager
- ✅ Enable 2FA on PyPI account
- ✅ Use trusted publishing for GitHub Actions
- ✅ Rotate tokens periodically
- ✅ Review package contents before uploading

### ❌ Don'ts

- ❌ Never commit `.pypirc` to git
- ❌ Never share API tokens
- ❌ Never use account-wide tokens in production
- ❌ Never hardcode tokens in scripts
- ❌ Never disable 2FA

## Package Verification Checklist

Before uploading to PyPI:

- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] Tests passing: `pytest`
- [ ] Type checking passing: `mypy arkforge`
- [ ] Linting passing: `ruff check arkforge`
- [ ] Package builds: `python -m build`
- [ ] Package validates: `twine check dist/*`
- [ ] No sensitive data in package: `tar -tzf dist/*.tar.gz`
- [ ] README renders correctly
- [ ] Git committed and tagged

## Common Commands Reference

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ arkforge

# Install from PyPI
pip install arkforge

# Upgrade installed package
pip install --upgrade arkforge
```

## Version Strategy

**Current Status**: `0.1.0` (Beta)

**Semantic Versioning**:
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- Breaking changes → bump MAJOR (1.0.0 → 2.0.0)
- New features → bump MINOR (1.0.0 → 1.1.0)
- Bug fixes → bump PATCH (1.0.0 → 1.0.1)

**Pre-1.0 Strategy**:
- Stay in `0.x.x` while API is unstable
- Breaking changes OK in 0.x.x versions
- Move to `1.0.0` when API is stable

**Pre-release Versions**:
- Alpha: `0.2.0a1`, `0.2.0a2`
- Beta: `0.2.0b1`, `0.2.0b2`
- Release Candidate: `0.2.0rc1`

## Support

**PyPI Help**:
- Documentation: https://packaging.python.org/
- PyPI Help: https://pypi.org/help/
- Status: https://status.python.org/

**ArkForge SDK**:
- Issues: https://github.com/arkonix-project/arkforge-sdk-py/issues
- Email: support@arkforge.io

## Next Steps

After publishing to PyPI:

1. ✅ Update README with PyPI installation instructions
2. ✅ Add PyPI badges to README
3. ✅ Announce release (social media, blog, etc.)
4. ✅ Monitor PyPI download stats
5. ✅ Set up automated publishing with GitHub Actions
6. ✅ Create project-scoped API token
7. ✅ Consider trusted publishing (OIDC)

---

**Congratulations!** You're now ready to publish to PyPI! 🎉

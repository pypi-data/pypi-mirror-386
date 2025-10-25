# Quick Start: Publishing to PyPI

**Everything is ready!** Your package is built and validated. Here's what you need to do:

## ✅ What's Already Done

- [x] Build tools installed (`build` and `twine`)
- [x] Package built successfully: `dist/arkforge-0.1.0-py3-none-any.whl`
- [x] Package validated with `twine check` - PASSED
- [x] `.gitignore` configured
- [x] Sensitive data removed
- [x] README updated with PyPI installation instructions
- [x] GitHub Actions workflow created for automation

## 🚀 Next Steps (First Time Publishing)

### 1. Create PyPI Account (5 minutes)

1. Go to: https://pypi.org/account/register/
2. Fill out the registration form
3. Verify your email
4. Enable Two-Factor Authentication (required)

### 2. Create API Token (2 minutes)

1. Log in to PyPI
2. Go to: https://pypi.org/manage/account/
3. Scroll to "API tokens"
4. Click "Add API token"
5. Name it: "ArkForge Publishing"
6. Scope: "Entire account" (for first upload)
7. **Copy the token immediately!** (starts with `pypi-`)
8. Save it in a password manager

### 3. Upload to PyPI (1 minute)

```bash
# From the project root directory
twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-AgE...` (paste your API token)

### 4. Verify Publication (1 minute)

```bash
# Visit the PyPI page
open https://pypi.org/project/arkforge/

# Or test installation
pip install arkforge
python -c "from arkforge import ArkForgeClient; print('Success!')"
```

## 🎯 That's It!

Your package is now live on PyPI! Anyone can install it with:

```bash
pip install arkforge
```

---

## 📚 Additional Resources

- **Complete Guide**: See `PUBLISHING.md` for detailed instructions
- **Update Version**: See section below for publishing new versions
- **Automate**: See `PUBLISHING.md` for GitHub Actions setup

---

## 🔄 Publishing Updates

When you want to publish a new version:

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.1"  # Bump version number
```

### 2. Rebuild Package

```bash
rm -rf dist/ build/
python -m build
```

### 3. Upload

```bash
twine upload dist/*
```

**Note**: You can't re-upload the same version number!

---

## 🤖 Automated Publishing (Optional)

### Setup GitHub Secret

1. Go to: https://github.com/arkonix-project/arkforge-sdk-py/settings/secrets/actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token (starts with `pypi-`)
5. Save

### Trigger Automated Publishing

1. Create a new release on GitHub
2. Tag: `v0.1.1`
3. Publish the release
4. GitHub Actions will automatically build and publish to PyPI!

---

## ⚠️ Common Issues

### "403 Forbidden: Invalid authentication"
- Username must be `__token__` (exactly, not your PyPI username)
- Password must be the full API token

### "File already exists"
- You can't re-upload the same version
- Bump version in `pyproject.toml` and rebuild

### "Package name already taken"
- Someone else owns that name
- Choose a different name in `pyproject.toml`

---

## 📞 Need Help?

- PyPI Documentation: https://packaging.python.org/
- Complete guide: See `PUBLISHING.md` in this repo
- PyPI Help: https://pypi.org/help/

---

**Ready to publish? Run:**

```bash
twine upload dist/*
```

🎉 **Good luck!**

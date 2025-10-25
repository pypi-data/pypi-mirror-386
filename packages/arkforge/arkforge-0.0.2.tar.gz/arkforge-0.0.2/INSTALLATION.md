# Installation Guide

This guide covers different ways to install the ArkForge Python SDK from a private GitHub repository.

## Prerequisites

- Python 3.8 or higher
- Git installed
- GitHub account with access to the repository

## Method 1: Install from GitHub (Recommended)

### SSH Installation (Most Secure for Private Repos)

**Setup SSH Keys** (one-time setup):

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key and add to GitHub Settings > SSH Keys
cat ~/.ssh/id_ed25519.pub
```

**Install the SDK**:

```bash
# Install latest version
pip install git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git

# Install specific version/tag
pip install git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git@v0.1.0

# Install from specific branch
pip install git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git@develop
```

### HTTPS Installation with Personal Access Token

**Create GitHub Personal Access Token** (one-time setup):

1. Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (for private repositories)
4. Copy the token (you won't see it again!)

**Install the SDK**:

```bash
# Replace <YOUR_TOKEN> with your personal access token
pip install git+https://<YOUR_TOKEN>@github.com/arkonix-project/arkforge-sdk-py.git

# Install specific version
pip install git+https://<YOUR_TOKEN>@github.com/arkonix-project/arkforge-sdk-py.git@v0.1.0
```

**Security Note**: Don't commit your token to version control!

## Method 2: Local Development Installation

**For development and contributing**:

```bash
# Clone the repository
git clone git@github.com:arkonix-project/arkforge-sdk-py.git
cd arkforge-sdk-py

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import arkforge; print(arkforge.__version__)"
```

## Method 3: Using requirements.txt

Add to your `requirements.txt`:

```txt
# Using SSH (recommended)
arkforge @ git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git

# Using HTTPS with token
arkforge @ git+https://${GITHUB_TOKEN}@github.com/arkonix-project/arkforge-sdk-py.git

# Specific version
arkforge @ git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git@v0.1.0
```

Then install:

```bash
pip install -r requirements.txt
```

## Method 4: Using pyproject.toml

Add to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "arkforge @ git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git",
]

# Or with specific version
[project]
dependencies = [
    "arkforge @ git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git@v0.1.0",
]
```

Then install:

```bash
pip install .
```

## Method 5: Using Poetry

Add to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
arkforge = {git = "ssh://git@github.com/arkonix-project/arkforge-sdk-py.git"}

# Or with specific version
arkforge = {git = "ssh://git@github.com/arkonix-project/arkforge-sdk-py.git", tag = "v0.1.0"}

# Or with specific branch
arkforge = {git = "ssh://git@github.com/arkonix-project/arkforge-sdk-py.git", branch = "develop"}
```

Then install:

```bash
poetry install
```

## Method 6: Docker Installation

**Dockerfile example**:

```dockerfile
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy SSH key for private repo access
# IMPORTANT: Use Docker secrets or build args, don't commit keys!
ARG SSH_PRIVATE_KEY
RUN mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Install SDK
RUN pip install git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git

# Clean up SSH key
RUN rm -rf /root/.ssh

WORKDIR /app
```

**Build with SSH key**:

```bash
docker build --build-arg SSH_PRIVATE_KEY="$(cat ~/.ssh/id_rsa)" -t myapp .
```

## Verification

After installation, verify the SDK is working:

```python
import arkforge

# Check version
print(f"ArkForge SDK version: {arkforge.__version__}")

# Test basic import
from arkforge import ArkForgeClient, KeyManagementClient
from arkforge.models import OptimizePortfolioRequest

print("✅ SDK installed successfully!")
```

Run from command line:

```bash
python -c "import arkforge; print(arkforge.__version__)"
```

## Upgrading

**Upgrade to latest version**:

```bash
# SSH
pip install --upgrade git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git

# HTTPS
pip install --upgrade git+https://<YOUR_TOKEN>@github.com/arkonix-project/arkforge-sdk-py.git
```

**Upgrade to specific version**:

```bash
pip install --upgrade git+ssh://git@github.com/arkonix-project/arkforge-sdk-py.git@v0.2.0
```

## Uninstalling

```bash
pip uninstall arkforge
```

## Troubleshooting

### Issue: "Permission denied (publickey)"

**Solution**: Set up SSH keys properly (see SSH Installation section above)

### Issue: "Repository not found"

**Solutions**:
- Verify you have access to the repository
- Check your GitHub credentials
- Ensure your SSH key is added to GitHub
- For HTTPS, verify your personal access token is valid

### Issue: "Failed building wheel"

**Solutions**:
- Ensure Python 3.8+ is installed: `python --version`
- Update pip: `pip install --upgrade pip`
- Install build tools: `pip install build wheel`

### Issue: "Could not find a version that satisfies the requirement"

**Solutions**:
- Check Python version compatibility (3.8+)
- Verify the repository URL is correct
- Try installing with verbose output: `pip install -v git+ssh://...`

### Issue: Token authentication in CI/CD

**Solution**: Use environment variables:

```yaml
# GitHub Actions example
- name: Install SDK
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    pip install git+https://${GITHUB_TOKEN}@github.com/arkonix-project/arkforge-sdk-py.git
```

## Best Practices

1. **Use SSH for private repositories**: More secure and no token management
2. **Pin versions in production**: Use specific tags (e.g., `@v0.1.0`)
3. **Use environment variables for tokens**: Never commit tokens to version control
4. **Keep dependencies updated**: Regularly upgrade to get bug fixes and features
5. **Test after installation**: Verify the SDK works in your environment

## Getting Help

- 📝 Read the [README](README.md) for usage examples
- 🐛 Report issues: https://github.com/arkonix-project/arkforge-sdk-py/issues
- 📖 Check the [CHANGELOG](CHANGELOG.md) for version history

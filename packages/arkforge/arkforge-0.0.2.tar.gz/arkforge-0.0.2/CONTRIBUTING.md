# Contributing to ArkForge Python SDK

Thank you for your interest in contributing to the ArkForge Python SDK! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- GitHub account with repository access

### Repository Access

This is a private repository. Ensure you have the necessary permissions before contributing.

## Development Setup

1. **Clone the repository**:

   ```bash
   git clone git@github.com:arkonix-project/arkforge-sdk-py.git
   cd arkforge-sdk-py
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**:

   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation**:

   ```bash
   python -c "import arkforge; print(arkforge.__version__)"
   pytest --version
   mypy --version
   ```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Branch

```bash
# For new features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b bugfix/issue-description

# For hotfixes
git checkout -b hotfix/critical-fix
```

### Making Changes

1. Make your changes in your feature branch
2. Write/update tests for your changes
3. Update documentation as needed
4. Ensure all tests pass
5. Commit your changes with clear messages

## Coding Standards

### Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Organized with isort
- **Formatting**: Black code formatter
- **Type hints**: Required for all functions

### Code Quality Tools

Run these before committing:

```bash
# Format code
black arkforge tests

# Sort imports
ruff check --fix arkforge

# Type checking
mypy arkforge

# Linting
ruff check arkforge
```

Or run all at once:

```bash
make format  # If using Makefile
# Or manually:
black arkforge tests && ruff check --fix arkforge && mypy arkforge
```

### Type Hints

All functions must have type hints:

```python
# Good
def optimize_portfolio(
    self,
    request: OptimizePortfolioRequest
) -> PortfolioRecommendation:
    ...

# Bad
def optimize_portfolio(self, request):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of the function.

    Longer description if needed, explaining the purpose and behavior.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised

    Example:
        >>> result = example_function("test", 42)
        >>> print(result)
        True
    """
    ...
```

### Error Handling

- Use the existing exception hierarchy from `arkforge.errors`
- Create specific exceptions for specific error cases
- Include helpful error messages with context

```python
# Good
if not assets:
    raise ValidationError(
        "At least one asset is required",
        code="E_NO_ASSETS"
    )

# Bad
if not assets:
    raise Exception("No assets")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arkforge --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_client.py

# Run specific test
pytest tests/unit/test_client.py::test_optimize_portfolio

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration -m integration
```

### Writing Tests

#### Unit Tests

```python
import pytest
from arkforge import ArkForgeClient
from arkforge.models import OptimizePortfolioRequest

def test_optimize_portfolio_request_validation():
    """Test portfolio request validation."""
    # Valid request
    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH"],
        risk_profile="moderate"
    )
    assert request.assets == ["BTC", "ETH"]

    # Invalid request
    with pytest.raises(ValidationError):
        OptimizePortfolioRequest(
            assets=[],  # Empty assets
            risk_profile="moderate"
        )
```

#### Integration Tests

```python
import pytest
from arkforge import ArkForgeClient

@pytest.mark.integration
def test_portfolio_optimization_integration():
    """Test portfolio optimization against live API."""
    client = ArkForgeClient(api_key="test-key")
    # ... integration test logic
```

### Test Coverage

- Aim for >85% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Pull Request Process

### Before Submitting

1. **Update your branch**:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Run all quality checks**:

   ```bash
   pytest --cov=arkforge
   mypy arkforge
   ruff check arkforge
   black --check arkforge
   ```

3. **Update documentation**:
   - Update README.md if needed
   - Update CHANGELOG.md
   - Add/update docstrings

### Submitting a Pull Request

1. **Push your branch**:

   ```bash
   git push origin your-feature-branch
   ```

2. **Create Pull Request**:
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template
   - Link related issues

3. **PR Checklist**:
   - [ ] Tests pass
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] No merge conflicts
   - [ ] Reviewers assigned

### PR Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. Address review comments
4. Maintain clean commit history

### Commit Messages

Use conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

**Examples**:

```bash
feat(client): add async support for portfolio optimization

fix(retry): correct exponential backoff calculation

docs(readme): update installation instructions

test(models): add validation tests for portfolio request
```

## Project Structure

```
arkforge-sdk-py/
├── arkforge/              # Main package
│   ├── __init__.py       # Public API
│   ├── client.py         # Main client
│   ├── models/           # Data models
│   ├── _http.py          # HTTP layer (private)
│   └── errors.py         # Exceptions
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── examples/            # Usage examples
└── docs/               # Documentation
```

## Questions?

- 📧 Email: support@arkforge.io
- 💬 Discussions: Use GitHub Discussions
- 🐛 Issues: https://github.com/arkonix-project/arkforge-sdk-py/issues

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

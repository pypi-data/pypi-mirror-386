# Contributing to Pocket-Recs

Thank you for your interest in contributing to Pocket-Recs! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Code samples** or test cases
- **Environment details** (OS, Python version, package versions)
- **Stack traces** or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear use case** and motivation
- **Detailed description** of the proposed functionality
- **Examples** of how it would be used
- **Potential drawbacks** or trade-offs

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow coding standards** (see below)
3. **Add tests** for any new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass** (`pytest`)
6. **Run linting** (`ruff check .`)
7. **Run type checking** (`mypy pocket_recs`)
8. **Write clear commit messages**

## Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/amjad/pocket-recs.git
cd pocket-recs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with all dependencies
pip install -e .[dev,ann,api,onnx]
```

### 2. Install Pre-commit Hooks

```bash
pre-commit install
```

This will run automated checks before each commit.

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pocket_recs --cov-report=html

# Run specific test file
pytest tests/test_fit.py

# Run with verbose output
pytest -v
```

### 4. Run Linting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### 5. Run Type Checking

```bash
mypy pocket_recs
```

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions/classes (Google style)
- Keep functions **focused and small** (single responsibility)
- Prefer **explicit over implicit**

### Code Organization

```python
"""Module docstring explaining purpose."""

from __future__ import annotations

import standard_library
from typing import Optional

import third_party
import another_third_party

from pocket_recs import local_module


class MyClass:
    """Class docstring.
    
    Args:
        param: Description
    """
    
    def my_method(self, param: str) -> bool:
        """Method docstring.
        
        Args:
            param: Parameter description
            
        Returns:
            Description of return value
        """
        pass
```

### Testing Standards

- Write tests for **all new functionality**
- Aim for **>80% code coverage**
- Use **descriptive test names**: `test_<function>_<scenario>_<expected_result>`
- Use **pytest fixtures** for common setup
- Test **edge cases** and **error conditions**

Example:
```python
def test_sessionize_empty_dataframe_returns_empty():
    """Test that sessionizing empty DataFrame returns empty result."""
    df = pl.DataFrame(schema={"user_id": pl.Utf8, "timestamp": pl.Int64})
    result = sessionize(df)
    assert result.is_empty()
```

### Documentation Standards

- Update **README.md** for user-facing changes
- Update **docstrings** for API changes
- Add **examples** for new features
- Update **type hints** when signatures change
- Keep docs **clear, concise, and accurate**

## Project Structure

```
pocket-recs/
├── pocket_recs/           # Main package
│   ├── __init__.py       # Package exports
│   ├── types.py          # Type definitions
│   ├── config.py         # Configuration
│   ├── offline/          # Offline training
│   │   ├── fit.py        # Main pipeline
│   │   ├── sessionize.py
│   │   ├── covis.py
│   │   ├── brand_pop.py
│   │   ├── embed.py
│   │   ├── index_ann.py
│   │   └── train_ranker.py
│   ├── online/           # Online inference
│   │   ├── recommender.py
│   │   ├── mmr.py
│   │   ├── reasons.py
│   │   └── ann_utils.py
│   ├── api/              # REST API
│   │   └── app.py
│   └── cli.py            # CLI tool
├── tests/                # Test suite
├── examples/             # Example scripts
├── README.md
├── CONTRIBUTING.md
└── pyproject.toml
```

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add cross-encoder reranking support
fix: Handle empty catalog in recommender
docs: Update API examples in README
test: Add tests for MMR diversification
refactor: Extract user vector building logic
perf: Optimize ANN index loading
```

Prefixes:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

## Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Refactoring
- `test/description` - Test additions

## Release Process

1. Update version in `pyproject.toml` and `pocket_recs/__init__.py`
2. Update `CHANGELOG.md` with notable changes
3. Create pull request to `main`
4. After merge, create Git tag: `git tag v0.x.0`
5. Push tag: `git push origin v0.x.0`
6. GitHub Actions will build and publish to PyPI

## Questions?

- Open a [GitHub Discussion](https://github.com/amjad/pocket-recs/discussions)
- Check existing [Issues](https://github.com/amjad/pocket-recs/issues)
- Read the [README](README.md)

Thank you for contributing to Pocket-Recs!


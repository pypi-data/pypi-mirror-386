# 🤝 Contributing to SkillForge

**We welcome contributions from the community!**

Thank you for your interest in contributing to SkillForge. This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct that could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**
1. Check [existing issues](https://github.com/omarpiosedev/SkillForge/issues)
2. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Collect diagnostic information

**Bug report should include:**
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, SkillForge version)
- Relevant logs or error messages
- Screenshots if applicable

**Use this template:**
```markdown
### Bug Description
Brief description of the issue

### Steps to Reproduce
1. Go to '...'
2. Run command '...'
3. See error

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: macOS 14.0
- Python: 3.11.5
- SkillForge: 1.0.0
- Claude Code: latest

### Logs
```
paste relevant logs here
```

### Additional Context
Any other relevant information
```

### Suggesting Enhancements

**Enhancement suggestions should include:**
- Clear description of the feature
- Use cases and benefits
- Possible implementation approach
- Mockups or examples if applicable

### Contributing Code

We welcome:
- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Tests**
- 🔨 **Skill templates**

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pipx or pip
- Claude Code installed

### Fork and Clone

```bash
# Fork repository on GitHub
# Then clone your fork

git clone https://github.com/YOUR_USERNAME/SkillForge.git
cd SkillForge

# Add upstream remote
git remote add upstream https://github.com/omarpiosedev/SkillForge.git
```

### Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Verify installation
skillforge --version
pytest --version
```

### Install Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Manually run all hooks
pre-commit run --all-files
```

---

## Contribution Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/amazing-feature

# Or for bug fix
git checkout -b fix/issue-123
```

### Branch Naming Convention

- `feature/<feature-name>` - New features
- `fix/<bug-description>` - Bug fixes
- `docs/<doc-change>` - Documentation only
- `refactor/<component>` - Code refactoring
- `test/<test-description>` - Adding tests
- `chore/<task>` - Maintenance tasks

### 2. Make Your Changes

**Follow these guidelines:**
- Write clear, readable code
- Add comments for complex logic
- Follow existing code style
- Write/update tests
- Update documentation
- Keep commits focused

### 3. Test Your Changes

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test file
pytest tests/unit/test_skill_generator.py -v

# Run with coverage
pytest --cov=skillforge --cov-report=html

# Check coverage report
open htmlcov/index.html
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add amazing feature"

# Push to your fork
git push origin feature/amazing-feature
```

---

## Coding Standards

### Python Style

**Follow PEP 8** with these specifics:

- **Line length**: 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized (stdlib → third-party → local)

**Example:**
```python
"""Module docstring explaining purpose."""

import os
from pathlib import Path
from typing import Dict, List, Optional

from pyyaml import safe_load

from skillforge.generators.config import Config


class SkillGenerator:
    """Generate personalized skills from templates.

    Args:
        profile: User profile dictionary
        config: Optional configuration override

    Example:
        >>> generator = SkillGenerator(profile)
        >>> skill_path = generator.generate("nextjs-fullstack")
    """

    def __init__(self, profile: Dict, config: Optional[Config] = None):
        self.profile = profile
        self.config = config or Config()

    def generate(self, skill_type: str) -> Path:
        """Generate a skill.

        Args:
            skill_type: Type of skill to generate

        Returns:
            Path to generated SKILL.md

        Raises:
            ValueError: If skill_type is invalid
        """
        # Implementation
        pass
```

### Type Hints

**Use type hints for all public functions:**

```python
from typing import Dict, List, Optional, Union

def process_template(
    template: str,
    variables: Dict[str, Any],
    strict: bool = False
) -> str:
    """Process template with variables."""
    pass
```

### Docstrings

**Use Google-style docstrings:**

```python
def complex_function(arg1: str, arg2: int, arg3: Optional[bool] = None) -> Dict:
    """Brief one-line description.

    Longer description explaining what the function does,
    how it works, and any important details.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        arg3: Description of arg3 (defaults to None)

    Returns:
        Description of return value

    Raises:
        ValueError: When arg2 is negative
        FileNotFoundError: When file doesn't exist

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key'])
        'value'
    """
    pass
```

### Error Handling

```python
# Use specific exceptions
class SkillGenerationError(Exception):
    """Raised when skill generation fails."""
    pass

# Always provide context
try:
    result = generate_skill(skill_type)
except TemplateError as e:
    raise SkillGenerationError(
        f"Failed to generate {skill_type}: {e}"
    ) from e

# Use context managers for resources
with open(file_path, 'r') as f:
    content = f.read()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")

# Include context
logger.info(f"Generating skill: {skill_type}")
logger.error(f"Failed to fetch docs for {library}: {error}")
```

---

## Testing Guidelines

### Test Organization

```
tests/
├── unit/               # Unit tests (fast, isolated)
├── integration/        # Integration tests (components together)
└── e2e/               # End-to-end tests (full workflows)
```

### Writing Tests

**Use pytest with fixtures:**

```python
import pytest
from skillforge.generators import SkillGenerator


@pytest.fixture
def sample_profile():
    """Sample user profile for testing."""
    return {
        "tech_stack": {"frontend": "Next.js"},
        "preferences": {"naming": "camelCase"}
    }


@pytest.fixture
def generator(sample_profile):
    """Configured generator instance."""
    return SkillGenerator(sample_profile)


def test_generate_skill_success(generator, tmp_path):
    """Test successful skill generation."""
    # Arrange
    skill_type = "nextjs-fullstack"

    # Act
    result = generator.generate(skill_type)

    # Assert
    assert result.exists()
    assert result.name == "SKILL.md"
    assert result.stat().st_size > 0


def test_generate_skill_invalid_type(generator):
    """Test error handling for invalid skill type."""
    with pytest.raises(ValueError, match="Unknown skill type"):
        generator.generate("invalid-skill")
```

### Test Coverage

- **Minimum**: 80% code coverage
- **Target**: 90%+ for new code
- **Priority**: Critical paths must be 100% covered

```bash
# Check coverage
pytest --cov=skillforge --cov-report=term-missing

# Generate HTML report
pytest --cov=skillforge --cov-report=html
open htmlcov/index.html
```

### Test Markers

```python
@pytest.mark.unit
def test_unit():
    """Fast, isolated test."""
    pass


@pytest.mark.integration
def test_integration():
    """Test component interaction."""
    pass


@pytest.mark.e2e
@pytest.mark.slow
def test_e2e():
    """Full workflow test (slow)."""
    pass
```

---

## Documentation

### Code Documentation

- **All public APIs** must have docstrings
- **Complex logic** should have inline comments
- **Examples** in docstrings when helpful

### User Documentation

When adding features, update:
- `README.md` - If changing core functionality
- `docs/QUICKSTART.md` - If affecting getting started
- `docs/COMMANDS.md` - If adding/changing commands
- `docs/API.md` - If changing Python API
- `docs/FAQ.md` - For common questions

### Changelog

Update `CHANGELOG.md` with your changes:

```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Changed behavior description

### Fixed
- Bug fix description
```

---

## Commit Messages

### Conventional Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(generator): add support for Vue.js templates"

# Bug fix
git commit -m "fix(orchestration): resolve duplicate skill loading"

# Documentation
git commit -m "docs(readme): update installation instructions"

# With body
git commit -m "feat(learning): implement pattern confidence decay

- Add time-based confidence decay
- Update pattern detection algorithm
- Add tests for decay calculation

Closes #123"
```

### Commit Best Practices

- One logical change per commit
- Write clear, concise messages
- Reference issues when applicable
- Keep commits focused

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main
- [ ] Self-reviewed code

```bash
# Final checks
./scripts/run-tests.sh
black skillforge/ tests/
flake8 skillforge/ tests/
mypy skillforge/
```

### Creating Pull Request

1. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

2. **Open PR on GitHub**

3. **Fill out PR template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-reviewed code
   - [ ] Commented complex logic
   - [ ] Updated documentation
   - [ ] No new warnings

   ## Related Issues
   Closes #123
   ```

### Code Review

**What to expect:**
- Reviewers may request changes
- Be patient and respectful
- Address all feedback
- Update PR as needed

**Responding to feedback:**
```bash
# Make requested changes
git add .
git commit -m "refactor: address review feedback"
git push origin feature/amazing-feature
```

### Merging

Once approved:
- PR will be squashed and merged
- Your contribution will be in the next release
- Thank you! 🎉

---

## Adding Skill Templates

### Template Structure

```handlebars
---
name: "{{skill_name}}"
description: >
  {{description}}
version: "{{version}}"
---

# {{skill_name}}

## Overview
{{overview}}

## Best Practices
{{#each best_practices}}
- {{this}}
{{/each}}

## User Conventions
{{#if user_conventions}}
Based on your preferences:
{{#each user_conventions}}
- {{this}}
{{/each}}
{{/if}}
```

### Adding Template

1. Create template file:
   ```bash
   vi skillforge/data/templates/tech-stack/your-framework.template
   ```

2. Add to supported types in `SkillGenerator`

3. Add documentation:
   - Update `docs/TEMPLATES.md`
   - Add examples

4. Test thoroughly:
   ```python
   def test_generate_your_framework(generator):
       skill = generator.generate("your-framework")
       assert skill.exists()
   ```

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Discord**: Real-time chat (coming soon)

### Getting Help

- Read [documentation](../README.md)
- Check [FAQ](FAQ.md)
- Search [existing issues](https://github.com/omarpiosedev/SkillForge/issues)
- Ask in [Discussions](https://github.com/omarpiosedev/SkillForge/discussions)

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md`
- Release notes
- Project README

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to SkillForge!** 🚀

Every contribution, no matter how small, helps make SkillForge better for everyone.

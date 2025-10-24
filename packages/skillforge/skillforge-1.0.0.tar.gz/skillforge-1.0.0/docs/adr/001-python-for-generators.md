# ADR 001: Python for Generator Scripts

## Status
**Accepted** - 2025-10-22

## Context
SkillForge needs to generate skills programmatically. We must choose a language for:
- Generator scripts (wizard, skill generation)
- Analyzers (intent analysis, pattern detection)
- Utility functions (caching, validation)

**Options considered**:
1. Python
2. JavaScript/TypeScript
3. Shell scripts (bash)
4. Go

## Decision
Use **Python 3.11+** for all generator and analyzer scripts.

## Rationale

### Why Python

**✅ Pros**:
1. **Text Processing Excellence**
   - Native string manipulation
   - Markdown/YAML parsing libraries (pyyaml)
   - Template engines (Jinja2, or custom)

2. **Rich Ecosystem**
   - `requests` for HTTP (Context7 API calls)
   - `click` for CLI interface
   - `pytest` for testing
   - `json` built-in for data persistence

3. **Type Safety**
   - Type hints (Python 3.11+)
   - mypy for static checking
   - IDE support excellent

4. **Easy Installation**
   - Standard on macOS/Linux
   - Simple `pip install`
   - Virtual environments (`venv`)

5. **Readable Code**
   - Clear syntax for complex logic
   - Easy to maintain
   - Good for open source contributions

6. **Already in Ecosystem**
   - Claude Code users likely have Python
   - Common in dev environments
   - No additional install burden

### Why NOT JavaScript

**❌ Cons**:
1. Different ecosystem than Claude Code skills (Markdown-based)
2. Would need Node.js installation
3. Package management complexity (npm/yarn/pnpm)
4. Less natural for text processing vs Python

### Why NOT Shell Scripts

**❌ Cons**:
1. Complex logic hard to test
2. Poor error handling
3. Platform-specific issues (bash vs zsh vs Windows)
4. Not suitable for complex analysis algorithms

### Why NOT Go

**❌ Cons**:
1. Compilation required
2. Heavier installation
3. Less familiar to average dev
4. Overkill for script tasks

## Consequences

### Positive
- ✅ Fast development (Python's expressiveness)
- ✅ Easy testing (pytest ecosystem)
- ✅ Good documentation generation (Sphinx)
- ✅ Type safety available (type hints)
- ✅ Cross-platform (works everywhere Python does)

### Negative
- ⚠️ Requires Python 3.11+ (not 3.10 or earlier)
- ⚠️ Additional dependency for users
- ⚠️ Performance not as fast as Go (but not critical for skill generation)

### Mitigation
- Use `pipx` for isolated installation (recommended)
- Document Python version requirement clearly
- Provide installation troubleshooting guide

## Implementation Notes

### Package Structure
```
skillforge/
├── generators/
│   ├── __init__.py
│   ├── wizard_engine.py
│   ├── skill_generator.py
│   └── ...
├── analyzers/
│   ├── __init__.py
│   └── ...
└── setup.py
```

### Distribution
```bash
# Via PyPI
pipx install skillforge

# Via pip (alternative)
pip install skillforge
```

### Dependencies
```
python_requires: ">=3.11"
install_requires:
  - pyyaml>=6.0
  - requests>=2.31.0
  - click>=8.0
```

## References
- Python Documentation: https://docs.python.org/3/
- pipx: https://pypa.github.io/pipx/
- Type Hints PEP: https://peps.python.org/pep-0484/

## Alternatives Considered
See "Options considered" section above.

## Review
Will review if:
- Python 3.11+ adoption is too low (<50% of users)
- Performance becomes critical bottleneck
- Alternative language provides clear benefits

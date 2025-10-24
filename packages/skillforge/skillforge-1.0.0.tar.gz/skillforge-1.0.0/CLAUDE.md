# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillForge is a meta-programming framework for Claude Code that generates, orchestrates, and continuously improves personalized skills. It transforms Claude Code from a generic assistant into an expert developer who knows YOUR stack, YOUR conventions, and YOUR patterns.

**Core Concept**: SkillForge operates on three levels:
1. **User Profile**: Global preferences stored in `~/.claude/skills/skillforge/data/user_profile.json`
2. **Generated Skills**: Tech-specific skills in `~/.claude/skills/` injected with user preferences
3. **Runtime Orchestration**: Intelligent skill loading based on intent analysis per project

## Architecture

### Four Core Components

1. **Generator** (`skillforge/generators/`): Creates personalized skills
   - `wizard_engine.py`: Interactive wizard for gathering preferences
   - `skill_generator.py`: Main orchestrator (7-step generation process)
   - `template_processor.py`: Handlebars template processing
   - `doc_fetcher.py`: Context7 MCP integration for fetching docs
   - `config.py`: Configuration and data persistence

2. **Orchestrator** (via `skillforge/analyzers/skill_discovery.py`): Intelligently selects skills
   - Scans `~/.claude/skills/` for available skills
   - Multi-strategy discovery (explicit, pattern, domain, dependency)
   - Priority-based ranking with confidence scoring
   - Progressive loading (metadata → core → full)

3. **Learner** (`skillforge/analyzers/`): Detects and applies patterns
   - `usage_tracker.py`: Tracks every skill usage and outcome
   - `pattern_detector.py`: Identifies recurring patterns (confidence-based)
   - `learning_pipeline.py`: Coordinates learning and auto-application
   - Auto-updates skills when patterns reach 80%+ confidence

4. **Optimizer** (`skillforge/analyzers/skill_optimizer.py`): Improves skills
   - Token reduction without losing meaning
   - Redundancy detection and merge suggestions
   - Documentation updates
   - Unused skill detection

### Data Flow

```
User Request → IntentAnalyzer → SkillDiscovery → Load Skills → Claude Code
                                                              ↓
                                                      UsageTracker
                                                              ↓
                                                      PatternDetector
                                                              ↓
                                                    (≥80% confidence)
                                                              ↓
                                                  Auto-update skills
```

### Key Design Patterns

**Intent Analysis** (`skillforge/analyzers/intent_analyzer.py`):
- Extracts entities (frameworks, libraries, features) using regex patterns
- Determines action type (create, update, debug, test, etc.)
- Identifies domain (frontend, backend, fullstack, devops, testing)
- Assesses complexity (simple, moderate, complex, enterprise)
- Matches against learned patterns with similarity scoring

**Skill Discovery** (`skillforge/analyzers/skill_discovery.py`):
- Discovery strategies with priority scores:
  - Explicit Match: 100 (user mentions skill name)
  - Pattern Match: 70-90 (learned patterns)
  - Domain Match: 60 (domain-specific skills)
  - Dependency Match: 40 (required by other skills)
- Caches skill metadata for performance
- Integrates usage analytics for relevance ranking

**Configuration Management** (`skillforge/generators/config.py`):
- Centralized paths: `~/.claude/skills/skillforge/`
- JSON-based persistence (user_profile, analytics, patterns)
- Context7 documentation caching (7-day TTL)
- Directory auto-creation with `ensure_directories()`

## Development Commands

### Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run unit + integration tests (fast, with coverage)
./scripts/run-tests.sh

# Run without coverage (faster)
./scripts/run-tests.sh --no-coverage

# Run all tests including E2E (slow)
./scripts/run-tests.sh --full

# Run specific test file
pytest tests/unit/test_intent_analyzer.py -v

# Run specific test function
pytest tests/unit/test_intent_analyzer.py::TestIntentAnalyzer::test_extract_entities -v

# Run with extra verbosity
./scripts/run-tests.sh --verbose
```

### Package Management

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Install test dependencies only
pip install -e ".[test]"

# Verify installation
skillforge --version
skillforge status
```

### Linting and Formatting

```bash
# Format code (Black)
black skillforge/ tests/

# Check types (MyPy)
mypy skillforge/

# Run flake8
flake8 skillforge/
```

## Testing Strategy

### Test Organization

- **Unit Tests** (`tests/unit/`): Individual component testing
  - Each module has a corresponding `test_*.py` file
  - Use pytest fixtures from `tests/conftest.py`
  - Mock external dependencies (MCP, filesystem)

- **Integration Tests** (`tests/integration/`): Component interaction testing
  - `test_wizard_to_generation.py`: Wizard → skill generation flow
  - `test_orchestration_flow.py`: Intent → discovery → loading
  - `test_learning_cycle.py`: Usage → pattern detection → skill update
  - `test_skill_lifecycle.py`: Full lifecycle from creation to optimization

- **E2E Tests** (`tests/e2e/`): Full user scenarios
  - `test_first_time_setup.py`: Complete wizard + generation
  - `test_daily_usage.py`: Typical usage patterns
  - `test_skill_update.py`: Documentation updates
  - `test_optimization.py`: Optimization cycle

### Test Markers

```python
@pytest.mark.unit          # Unit test (fast)
@pytest.mark.integration   # Integration test
@pytest.mark.e2e          # End-to-end test (slow)
@pytest.mark.slow         # Any slow test
```

### Test Configuration

See `pyproject.toml` for pytest configuration:
- Coverage thresholds
- Test discovery patterns
- Marker definitions
- Coverage exclusions

## Code Style and Conventions

### Python Code

- **Python Version**: 3.11+ (uses modern typing features)
- **Line Length**: 100 characters (Black config)
- **Imports**: Standard library → third-party → local
- **Type Hints**: Required for all public functions (MyPy enabled)
- **Docstrings**: Google style for all public modules, classes, and functions

### Naming Conventions

- **Classes**: PascalCase (e.g., `IntentAnalyzer`, `SkillGenerator`)
- **Functions/Methods**: snake_case (e.g., `extract_entities`, `generate_skill`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_CONFIG`, `FRAMEWORKS`)
- **Private members**: Prefix with `_` (e.g., `_calculate_confidence`)

### Error Handling

- Use custom exceptions for domain-specific errors:
  - `SkillGenerationError`: Skill generation failures
  - `ValidationError`: Skill validation failures
  - `TemplateError`: Template processing failures
  - `DocFetchError`: Documentation fetching failures
- Always provide context in exception messages
- Use `try-except-finally` for resource cleanup

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels:
logger.debug("Detailed diagnostic info")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
```

## Key Implementation Details

### Intent Analysis Flow

The `IntentAnalyzer` uses ordered pattern matching:

1. **Entity Extraction**: Regex patterns in priority order
   - Frameworks (Next.js, React, Django, etc.)
   - Libraries (Supabase, Prisma, Tailwind, etc.)
   - Features (authentication, dashboard, API, etc.)
   - File types (component, page, route, etc.)

2. **Action Detection**: Check action keywords in order
   - More specific first (document, deploy, test, debug)
   - Generic last (create is default fallback)

3. **Domain Classification**: Score-based identification
   - Keyword scoring (text + entities)
   - Framework categorization (frontend/backend/fullstack)
   - Highest score wins, default to 'fullstack'

4. **Complexity Assessment**: Multi-factor analysis
   - Explicit keywords (simple, complex, enterprise)
   - Entity count (more entities = higher complexity)
   - Feature indicators (auth + dashboard + api → complex)

### Skill Generation Process

The `SkillGenerator` follows a 7-step process:

1. Load user profile (or create via WizardEngine)
2. Select/load template based on skill_type
3. Fetch latest documentation via DocFetcher (with caching)
4. Prepare template variables (merge profile + docs)
5. Process template via TemplateProcessor (Handlebars)
6. Validate generated SKILL.md (YAML frontmatter, sections, token budget)
7. Save to `~/.claude/skills/generated/{skill_name}/SKILL.md`

**Validation Requirements**:
- Valid YAML frontmatter with required fields
- Mandatory sections present
- Token budget check (configurable, default 5000)
- Rollback on failure for data integrity

### Pattern Learning

Pattern detection requires:
- Minimum 10 samples (configurable via `min_samples_for_pattern`)
- 80%+ confidence score for auto-application
- Tracked metrics: usage_count, success_rate, last_used
- Stored in `~/.claude/skills/skillforge/data/learned_patterns.json`

Pattern matching uses:
- Keyword overlap scoring
- Entity matching
- Sequence similarity (difflib.SequenceMatcher)
- Average of all scores for final confidence

## Project Status

**Current Phase**: Alpha (Phase 1 - Foundation)

Completed:
- ✅ Core architecture design
- ✅ Intent analyzer implementation
- ✅ Pattern detector implementation
- ✅ Skill generator implementation
- ✅ Template processor implementation
- ✅ Configuration management
- ✅ Complete test suite (unit + integration + e2e)

In Progress:
- ⏳ Skill discovery implementation
- ⏳ Orchestration flow
- ⏳ Slash commands system

Not Yet Implemented:
- ❌ Wizard engine (interactive mode)
- ❌ Learning pipeline (auto-application)
- ❌ Skill optimizer
- ❌ Documentation fetcher (Context7 integration)
- ❌ CLI commands (init, generate, update, optimize)

## Special Notes

### Template System

Templates use Handlebars syntax and are stored in:
- `skillforge/data/templates/` (package data)
- `skillforge/templates/` (module code)

Template variable interpolation:
- `{{user.preferences.naming.variables}}` → User preferences
- `{{docs.best_practices}}` → Fetched documentation
- `{{skill.metadata.version}}` → Skill metadata

### MCP Integration

SkillForge uses the Context7 MCP server for documentation:
- Library ID format: `/org/project` or `/org/project/version`
- Must call `resolve-library-id` before `get-library-docs`
- Documentation is cached in `~/.claude/skills/skillforge/data/cache/context7/`
- Cache TTL: 7 days (configurable via `is_cache_valid`)

### Data Persistence

All user data is stored locally:
- `~/.claude/skills/skillforge/data/user_profile.json`
- `~/.claude/skills/skillforge/data/usage_analytics.json`
- `~/.claude/skills/skillforge/data/learned_patterns.json`

JSON structure is versioned for migration support.

## Troubleshooting

### Common Issues

**Import Errors**: Ensure package is installed in editable mode
```bash
pip install -e .
```

**Test Failures**: Check virtual environment is activated
```bash
source venv/bin/activate
pytest
```

**Config Issues**: Reset configuration to defaults
```python
from skillforge.generators.config import Config
Config.reset_config()
```

**Cache Issues**: Clear Context7 cache
```bash
rm -rf ~/.claude/skills/skillforge/data/cache/context7/*
```

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Inspect generated skills:
```bash
# View skill metadata
cat ~/.claude/skills/{skill-name}/SKILL.md | head -50

# Check skill size
wc -l ~/.claude/skills/{skill-name}/SKILL.md
```

## Contributing

When adding new features:

1. **Add tests first** (TDD approach)
   - Unit tests for new functions
   - Integration tests for component interactions
   - Update existing tests if behavior changes

2. **Update data classes** if adding new fields
   - Add to dataclass definition
   - Implement `to_dict()` and `from_dict()` methods
   - Update JSON schema validation

3. **Document in docstrings** (Google style)
   - Module-level docstring explaining purpose
   - Class docstrings with attributes
   - Function docstrings with Args, Returns, Examples

4. **Run full test suite** before committing
   ```bash
   ./scripts/run-tests.sh --full
   ```

5. **Follow commit conventions** (Conventional Commits)
   - `feat:` for new features
   - `fix:` for bug fixes
   - `refactor:` for refactoring
   - `test:` for test changes
   - `docs:` for documentation

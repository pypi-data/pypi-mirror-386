# 📚 SkillForge Python API Documentation

**Complete API reference for programmatic access**

This document provides comprehensive documentation for SkillForge's Python API, allowing you to integrate SkillForge into your own tools and workflows.

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
  - [Config](#config)
  - [WizardEngine](#wizardengine)
  - [SkillGenerator](#skillgenerator)
  - [TemplateProcessor](#templateprocessor)
  - [DocFetcher](#docfetcher)
  - [IntentAnalyzer](#intentanalyzer)
  - [SkillDiscovery](#skilldiscovery)
  - [UsageTracker](#usagetracker)
  - [PatternDetector](#patterndetector)
  - [LearningPipeline](#learningpipeline)
  - [SkillOptimizer](#skilloptimizer)
- [Data Classes](#data-classes)
- [Examples](#examples)

---

## Installation

```bash
# Install SkillForge package
pip install skillforge

# Or in development mode
pip install -e .
```

---

## Quick Start

```python
from skillforge.generators import SkillGenerator, WizardEngine
from skillforge.generators.config import Config
from skillforge.analyzers import IntentAnalyzer, SkillDiscovery

# Initialize configuration
config = Config()

# Run wizard
wizard = WizardEngine()
profile = wizard.run()

# Generate a skill
generator = SkillGenerator(profile)
skill_path = generator.generate("nextjs-fullstack")

# Analyze intent
analyzer = IntentAnalyzer()
intent = analyzer.analyze("Create a login component with Supabase")

# Discover relevant skills
discovery = SkillDiscovery()
skills = discovery.discover(intent)
```

---

## Core Modules

### Config

**Module**: `skillforge.generators.config`

Manages configuration and data persistence.

#### Class: `Config`

```python
from skillforge.generators.config import Config

class Config:
    """Configuration management for SkillForge."""

    # Class attributes
    SKILLFORGE_HOME: Path
    DATA_DIR: Path
    CACHE_DIR: Path
    DEFAULT_CONFIG: Dict[str, Any]
```

#### Methods

**`ensure_directories()`**

Creates necessary directory structure.

```python
Config.ensure_directories()
# Creates:
# - ~/.claude/skills/skillforge/
# - ~/.claude/skills/skillforge/data/
# - ~/.claude/skills/skillforge/data/cache/
```

**`load_user_profile() -> Dict[str, Any]`**

Loads user profile from disk.

```python
profile = Config.load_user_profile()
print(profile["preferences"]["naming"]["variables"])  # "camelCase"
```

**`save_user_profile(profile: Dict[str, Any])`**

Saves user profile to disk.

```python
profile["preferences"]["naming"]["variables"] = "snake_case"
Config.save_user_profile(profile)
```

**`load_analytics() -> Dict[str, Any]`**

Loads usage analytics.

```python
analytics = Config.load_analytics()
usage = analytics["skill_usage"]
```

**`save_analytics(analytics: Dict[str, Any])`**

Saves usage analytics.

```python
analytics["skill_usage"]["nextjs-fullstack"]["total_uses"] += 1
Config.save_analytics(analytics)
```

---

### WizardEngine

**Module**: `skillforge.generators.wizard_engine`

Interactive setup wizard for gathering user preferences.

#### Class: `WizardEngine`

```python
from skillforge.generators.wizard_engine import WizardEngine

class WizardEngine:
    """Interactive wizard for skill generation setup."""

    def __init__(self):
        """Initialize wizard with empty state."""
        pass
```

#### Methods

**`run() -> Dict[str, Any]`**

Runs the interactive wizard.

```python
wizard = WizardEngine()
profile = wizard.run()

# Returns user profile dictionary:
{
    "setup_completed": True,
    "tech_stack": {
        "frontend": "Next.js",
        "backend": "Next.js API Routes",
        "database": "Supabase"
    },
    "preferences": {
        "naming": {"variables": "camelCase"},
        "imports": {"style": "absolute", "alias": "@/"}
    }
}
```

**`detect_stack() -> Dict[str, str]`**

Auto-detects tech stack from current directory.

```python
wizard = WizardEngine()
detected = wizard.detect_stack()

# Returns:
{
    "frontend": "Next.js",
    "version": "15.0.0",
    "ui": "Tailwind CSS",
    "state": "Zustand"
}
```

**`ask_question(question: str, options: List[str], allow_multiple: bool = False) -> Any`**

Asks a question with multiple choice options.

```python
answer = wizard.ask_question(
    "What's your variable naming convention?",
    ["camelCase", "snake_case", "PascalCase"],
    allow_multiple=False
)
# Returns: "camelCase"
```

---

### SkillGenerator

**Module**: `skillforge.generators.skill_generator`

Main orchestrator for skill generation.

#### Class: `SkillGenerator`

```python
from skillforge.generators.skill_generator import SkillGenerator

class SkillGenerator:
    """Generate personalized skills from templates."""

    def __init__(self, profile: Optional[Dict] = None, config: Optional[Config] = None):
        """Initialize generator with user profile."""
        pass
```

#### Methods

**`generate(skill_type: str, force: bool = False, fetch_docs: bool = True) -> Path`**

Generates a skill.

```python
generator = SkillGenerator(profile)

# Basic generation
skill_path = generator.generate("nextjs-fullstack")
# Returns: Path('~/.claude/skills/nextjs-fullstack/SKILL.md')

# Force overwrite
skill_path = generator.generate("nextjs-fullstack", force=True)

# Skip documentation fetch
skill_path = generator.generate("nextjs-fullstack", fetch_docs=False)
```

**`validate_skill(skill_path: Path) -> bool`**

Validates generated skill.

```python
is_valid = generator.validate_skill(skill_path)

# Checks:
# - Valid YAML frontmatter
# - Required sections present
# - Token budget within limits
# - No placeholder text remaining
```

**`list_available_types() -> List[str]`**

Lists all available skill types.

```python
types = generator.list_available_types()
# Returns: ['nextjs-fullstack', 'react-spa', 'vue-app', ...]
```

---

### TemplateProcessor

**Module**: `skillforge.generators.template_processor`

Handlebars-style template engine.

#### Class: `TemplateProcessor`

```python
from skillforge.generators.template_processor import TemplateProcessor

class TemplateProcessor:
    """Process templates with variables."""

    def __init__(self, strict: bool = False):
        """Initialize processor.

        Args:
            strict: Raise error on missing variables (default: False)
        """
        pass
```

#### Methods

**`process(template: str, variables: Dict[str, Any]) -> str`**

Processes template with variables.

```python
processor = TemplateProcessor()

template = """
# {{skill_name}}

{{#if has_typescript}}
## TypeScript Configuration
{{/if}}

{{#each best_practices}}
- {{this}}
{{/each}}
"""

variables = {
    "skill_name": "Next.js Fullstack",
    "has_typescript": True,
    "best_practices": ["Use Server Components", "Optimize images"]
}

result = processor.process(template, variables)
```

**Supported Syntax:**

**Variables**: `{{variable_name}}`
```handlebars
{{user.name}}  # Simple
{{user.preferences.naming.variables}}  # Nested
```

**Conditionals**: `{{#if}}...{{/if}}`
```handlebars
{{#if condition}}
  Content when true
{{/if}}
```

**Loops**: `{{#each}}...{{/each}}`
```handlebars
{{#each items}}
  - {{name}} ({{this}})
{{/each}}
```

---

### DocFetcher

**Module**: `skillforge.generators.doc_fetcher`

Fetches documentation via Context7 MCP.

#### Class: `DocFetcher`

```python
from skillforge.generators.doc_fetcher import DocFetcher

class DocFetcher:
    """Fetch documentation via Context7 MCP."""

    def __init__(self, cache_ttl_days: int = 7):
        """Initialize fetcher with cache TTL."""
        pass
```

#### Methods

**`fetch(library_name: str, topic: Optional[str] = None) -> str`**

Fetches documentation for a library.

```python
fetcher = DocFetcher()

# Fetch Next.js docs
docs = fetcher.fetch("Next.js", topic="App Router")

# Fetch Supabase docs
docs = fetcher.fetch("Supabase", topic="Authentication")
```

**`resolve_library_id(library_name: str) -> str`**

Resolves library name to Context7 ID.

```python
library_id = fetcher.resolve_library_id("Next.js")
# Returns: "/vercel/next.js"
```

**`get_cached_docs(library_id: str) -> Optional[str]`**

Gets documentation from cache.

```python
cached = fetcher.get_cached_docs("/vercel/next.js")

if cached:
    print("Using cached docs")
else:
    docs = fetcher.fetch("Next.js")
```

---

### IntentAnalyzer

**Module**: `skillforge.analyzers.intent_analyzer`

Analyzes user requests to understand intent.

#### Class: `IntentAnalyzer`

```python
from skillforge.analyzers.intent_analyzer import IntentAnalyzer, Intent

class IntentAnalyzer:
    """Analyze user requests to extract intent."""

    def __init__(self):
        """Initialize analyzer with pattern database."""
        pass
```

#### Methods

**`analyze(request: str) -> Intent`**

Analyzes a user request.

```python
analyzer = IntentAnalyzer()

intent = analyzer.analyze("Create a login component with Supabase auth")

print(intent.entities)    # ["login", "component", "Supabase", "auth"]
print(intent.action)      # "create"
print(intent.domain)      # "fullstack"
print(intent.complexity)  # "moderate"
print(intent.confidence)  # 0.92
```

**`extract_entities(text: str) -> List[str]`**

Extracts entities from text.

```python
entities = analyzer.extract_entities("Create Next.js dashboard with charts")
# Returns: ["Next.js", "dashboard", "charts"]
```

**`determine_action(text: str) -> str`**

Determines action type.

```python
action = analyzer.determine_action("Fix the login bug")
# Returns: "fix"

action = analyzer.determine_action("Build a new feature")
# Returns: "create"
```

#### Data Class: `Intent`

```python
@dataclass
class Intent:
    entities: List[str]       # Extracted entities
    action: str               # Action type
    domain: str               # Domain classification
    complexity: str           # Complexity level
    patterns: List[Pattern]   # Matched patterns
    confidence: float         # Confidence score (0.0-1.0)
```

---

### SkillDiscovery

**Module**: `skillforge.analyzers.skill_discovery`

Discovers relevant skills for a given intent.

#### Class: `SkillDiscovery`

```python
from skillforge.analyzers.skill_discovery import SkillDiscovery, Skill

class SkillDiscovery:
    """Discover relevant skills for an intent."""

    def __init__(self):
        """Initialize discovery with skill cache."""
        pass
```

#### Methods

**`discover(intent: Intent) -> List[Skill]`**

Discovers relevant skills.

```python
discovery = SkillDiscovery()
analyzer = IntentAnalyzer()

intent = analyzer.analyze("Create login with Supabase")
skills = discovery.discover(intent)

for skill in skills:
    print(f"{skill.name} (priority: {skill.priority})")

# Output:
# nextjs-fullstack (priority: 100)
# supabase-integration (priority: 100)
# git-workflow (priority: 40)
```

**`load_available_skills() -> List[Skill]`**

Loads all available skills.

```python
all_skills = discovery.load_available_skills()
print(f"Found {len(all_skills)} skills")
```

**`get_domain_skills(domain: str) -> List[Skill]`**

Gets skills for specific domain.

```python
frontend_skills = discovery.get_domain_skills("frontend")
```

#### Data Class: `Skill`

```python
@dataclass
class Skill:
    name: str                 # Skill name
    path: Path                # Path to SKILL.md
    description: str          # Skill description
    triggers: List[str]       # Keywords that trigger
    dependencies: List[str]   # Required skills
    priority: int             # Discovery priority
    usage_count: int          # Times used
    success_rate: float       # Success percentage
    last_used: datetime       # Last usage timestamp
```

---

### UsageTracker

**Module**: `skillforge.analyzers.usage_tracker`

Tracks skill usage for learning.

#### Class: `UsageTracker`

```python
from skillforge.analyzers.usage_tracker import UsageTracker

class UsageTracker:
    """Track skill usage for pattern learning."""

    def __init__(self):
        """Initialize tracker with analytics data."""
        pass
```

#### Methods

**`track_usage(skills: List[Skill], request: str, outcome: str, duration: float)`**

Records a usage event.

```python
tracker = UsageTracker()

tracker.track_usage(
    skills=[nextjs_skill, supabase_skill],
    request="Create login component",
    outcome="success",
    duration=12.3
)
```

**`get_statistics() -> Dict[str, Any]`**

Gets usage statistics.

```python
stats = tracker.get_statistics()

print(stats["skill_usage"]["nextjs-fullstack"])
# {
#     "total_uses": 89,
#     "successes": 84,
#     "failures": 5,
#     "success_rate": 0.94,
#     "avg_duration": 45.2
# }
```

**`get_skill_combinations() -> Dict[str, int]`**

Gets common skill combinations.

```python
combinations = tracker.get_skill_combinations()
# {
#     "nextjs-fullstack+supabase-integration": 43,
#     "nextjs-fullstack+tailwind-styling": 38
# }
```

---

### PatternDetector

**Module**: `skillforge.analyzers.pattern_detector`

Detects patterns from usage data.

#### Class: `PatternDetector`

```python
from skillforge.analyzers.pattern_detector import PatternDetector, Pattern

class PatternDetector:
    """Detect patterns from usage data."""

    def __init__(self, min_samples: int = 10, confidence_threshold: float = 0.8):
        """Initialize detector with thresholds."""
        pass
```

#### Methods

**`detect_patterns() -> List[Pattern]`**

Detects patterns from usage data.

```python
detector = PatternDetector(min_samples=10, confidence_threshold=0.8)

patterns = detector.detect_patterns()

for pattern in patterns:
    print(f"{pattern.name}: {pattern.confidence:.2f}")
    if pattern.confidence >= 0.8:
        print("  -> Ready to apply")
```

**`calculate_confidence(pattern: Pattern) -> float`**

Calculates pattern confidence.

```python
confidence = detector.calculate_confidence(pattern)
# Returns: 0.0 to 1.0

# Formula:
# confidence = (
#     (frequency_weight * 0.4) +
#     (success_weight * 0.4) +
#     (recency_weight * 0.2)
# )
```

#### Data Class: `Pattern`

```python
@dataclass
class Pattern:
    name: str                         # Pattern name
    type: str                         # "combination", "style", "workflow"
    description: str                  # Human-readable description
    samples_count: int                # Number of samples
    confidence: float                 # Confidence score (0.0-1.0)
    recommended_skills: List[str]     # Skills to load
    recommendations: Dict[str, str]   # Key-value recommendations
```

---

### LearningPipeline

**Module**: `skillforge.analyzers.learning_pipeline`

Orchestrates learning cycles.

#### Class: `LearningPipeline`

```python
from skillforge.analyzers.learning_pipeline import LearningPipeline

class LearningPipeline:
    """Orchestrate learning cycles."""

    def __init__(self):
        """Initialize pipeline with dependencies."""
        pass
```

#### Methods

**`run_learning_cycle() -> Dict[str, Any]`**

Runs a complete learning cycle.

```python
pipeline = LearningPipeline()

report = pipeline.run_learning_cycle()

print(f"Detected {report['patterns_detected']} patterns")
print(f"Applied {report['patterns_applied']} patterns")
```

**`apply_pattern(pattern: Pattern, skill: Skill) -> bool`**

Applies a pattern to a skill.

```python
success = pipeline.apply_pattern(pattern, skill)

if success:
    print(f"Pattern {pattern.name} applied to {skill.name}")
else:
    print("Pattern application failed (rolled back)")
```

---

### SkillOptimizer

**Module**: `skillforge.analyzers.skill_optimizer`

Optimizes existing skills.

#### Class: `SkillOptimizer`

```python
from skillforge.analyzers.skill_optimizer import SkillOptimizer

class SkillOptimizer:
    """Optimize existing skills."""

    def __init__(self):
        """Initialize optimizer."""
        pass
```

#### Methods

**`optimize_all_skills() -> Dict[str, Any]`**

Optimizes all skills.

```python
optimizer = SkillOptimizer()

report = optimizer.optimize_all_skills()

print(f"Analyzed {report['analyzed']} skills")
print(f"Found {len(report['optimizations'])} opportunities")
print(f"Token savings: {report['total_token_savings']}")
```

**`find_redundancies() -> List[Tuple[Skill, Skill, float]]`**

Finds redundant skills.

```python
redundancies = optimizer.find_redundancies()

for skill1, skill2, overlap in redundancies:
    if overlap > 0.7:
        print(f"{skill1.name} and {skill2.name}: {overlap:.0%} overlap")
```

**`suggest_merges() -> List[Dict[str, Any]]`**

Suggests skill merges.

```python
suggestions = optimizer.suggest_merges()

for suggestion in suggestions:
    print(f"Merge {suggestion['skills']}")
    print(f"  Reason: {suggestion['reason']}")
    print(f"  Savings: {suggestion['token_savings']} tokens")
```

---

## Data Classes

### Common Data Structures

All data classes support serialization:

```python
from dataclasses import asdict

# Convert to dictionary
data = asdict(intent)

# Convert to JSON
import json
json_str = json.dumps(asdict(intent))
```

---

## Examples

### Example 1: Programmatic Skill Generation

```python
from skillforge.generators import SkillGenerator
from skillforge.generators.config import Config

# Load existing profile
profile = Config.load_user_profile()

# Or create custom profile
profile = {
    "tech_stack": {
        "frontend": "Next.js",
        "ui": "Tailwind CSS",
        "state": "Zustand"
    },
    "preferences": {
        "naming": {"variables": "camelCase"},
        "imports": {"style": "absolute", "alias": "@/"}
    }
}

# Generate skill
generator = SkillGenerator(profile)
skill_path = generator.generate("nextjs-fullstack")

print(f"Skill generated: {skill_path}")
```

### Example 2: Intent Analysis Pipeline

```python
from skillforge.analyzers import IntentAnalyzer, SkillDiscovery

# Analyze user request
analyzer = IntentAnalyzer()
intent = analyzer.analyze("Create a dashboard with real-time data")

print(f"Entities: {intent.entities}")
print(f"Action: {intent.action}")
print(f"Domain: {intent.domain}")

# Discover relevant skills
discovery = SkillDiscovery()
skills = discovery.discover(intent)

print(f"\nRelevant skills ({len(skills)}):")
for skill in skills:
    print(f"  - {skill.name} (priority: {skill.priority})")
```

### Example 3: Usage Tracking & Pattern Learning

```python
from skillforge.analyzers import UsageTracker, PatternDetector, LearningPipeline

# Track usage
tracker = UsageTracker()
tracker.track_usage(
    skills=[nextjs_skill, supabase_skill],
    request="Create auth component",
    outcome="success",
    duration=15.2
)

# Detect patterns (after 10+ samples)
detector = PatternDetector()
patterns = detector.detect_patterns()

# Apply patterns
pipeline = LearningPipeline()
report = pipeline.run_learning_cycle()

print(f"Applied {report['patterns_applied']} patterns")
```

### Example 4: Skill Optimization

```python
from skillforge.analyzers import SkillOptimizer

# Analyze and optimize
optimizer = SkillOptimizer()
report = optimizer.optimize_all_skills()

# Review optimizations
for opt in report['optimizations']:
    print(f"\nType: {opt['type']}")
    print(f"Target: {opt.get('skill') or opt.get('skills')}")
    print(f"Reason: {opt['reason']}")

    if opt['type'] == 'merge':
        print(f"Token savings: {opt['token_savings']}")
```

### Example 5: Custom Template Processing

```python
from skillforge.generators import TemplateProcessor

processor = TemplateProcessor(strict=True)

template = """
# {{title}}

## Configuration

{{#each config}}
- **{{@key}}**: {{this}}
{{/each}}

{{#if has_examples}}
## Examples
{{#each examples}}
### {{title}}
```{{language}}
{{code}}
```
{{/each}}
{{/if}}
"""

variables = {
    "title": "Custom Skill",
    "config": {
        "environment": "production",
        "debug": False
    },
    "has_examples": True,
    "examples": [
        {
            "title": "Basic Usage",
            "language": "typescript",
            "code": "const result = doSomething();"
        }
    ]
}

result = processor.process(template, variables)
print(result)
```

---

## Error Handling

All modules raise specific exceptions:

```python
from skillforge.generators.skill_generator import SkillGenerationError
from skillforge.generators.template_processor import TemplateError
from skillforge.generators.doc_fetcher import DocFetchError

try:
    generator.generate("invalid-skill")
except SkillGenerationError as e:
    print(f"Generation failed: {e}")

try:
    processor.process(template, incomplete_vars)
except TemplateError as e:
    print(f"Template processing failed: {e}")

try:
    docs = fetcher.fetch("NonexistentLibrary")
except DocFetchError as e:
    print(f"Doc fetch failed: {e}")
```

---

## Further Reading

- [Quick Start Guide](QUICKSTART.md)
- [Architecture](ARCHITECTURE.md)
- [Commands Reference](COMMANDS.md)
- [Contributing](CONTRIBUTING.md)

---

**Questions?** Open an issue on [GitHub](https://github.com/omarpiosedev/SkillForge/issues)

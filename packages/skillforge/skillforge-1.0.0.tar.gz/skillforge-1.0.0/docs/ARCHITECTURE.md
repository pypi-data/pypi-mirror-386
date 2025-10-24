# 🏗️ SkillForge Architecture

**Technical Architecture & Design Documentation**

This document explains SkillForge's internal architecture, design patterns, data flows, and implementation details.

---

## 📋 Table of Contents

- [High-Level Overview](#high-level-overview)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [File Structure](#file-structure)
- [Design Patterns](#design-patterns)
- [Integration Points](#integration-points)
- [Performance & Optimization](#performance--optimization)

---

## High-Level Overview

### The Three Levels

SkillForge operates on three distinct levels:

```
┌──────────────────────────────────────────────────────────┐
│                    LEVEL 1: User Profile                 │
│                    (Global Preferences)                  │
│                                                          │
│  Location: ~/.claude/skills/skillforge/data/             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  user_profile.json                                 │  │
│  │  ├─ Naming conventions (camelCase, PascalCase)     │  │
│  │  ├─ Import style (absolute with @/)                │  │
│  │  ├─ Preferred libraries (Zustand, Zod)             │  │
│  │  ├─ Code patterns (feature-based structure)        │  │
│  │  └─ Workflow (conventional commits)                │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                             ↓
                    Injected into
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              LEVEL 2: Generated Skills                      │
│           (Tech-Specific + User Preferences)                │
│                                                             │
│  Location: ~/.claude/skills/<skill-name>/                   │
│                                                             │
│  Each skill contains:                                       │
│  ├─ SKILL.md (main file)                                    │
│  │  ├─ Framework best practices                             │
│  │  ├─ Code examples                                        │
│  │  ├─ YOUR conventions injected                            │
│  │  └─ Latest documentation                                 │
│  ├─ templates/ (optional)                                   │
│  └─ docs/ (optional)                                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
                  Orchestrated at runtime
                             ↓
┌─────────────────────────────────────────────────────────────┐
│             LEVEL 3: Runtime Orchestration                  │
│                 (Per-Request Intelligence)                  │
│                                                             │
│  For each Claude Code request:                              │
│  1. Analyze intent                                          │
│  2. Identify relevant skills                                │
│  3. Calculate token budget                                  │
│  4. Load skills progressively                               │
│  5. Track usage for learning                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

SkillForge consists of four main pillars, each with specific responsibilities.

### 1. Generator (`skillforge/generators/`)

**Purpose**: Creates personalized skills from templates + documentation + user preferences.

#### Components

**WizardEngine** (`wizard_engine.py` - 956 lines)
```python
class WizardEngine:
    """Interactive setup wizard for gathering user preferences"""

    def run(self) -> UserProfile:
        """
        Main wizard flow:
        1. Auto-detect tech stack from current directory
        2. Ask 10-12 questions about preferences
        3. Generate user_profile.json
        4. Suggest skills to generate
        """

    def detect_stack(self) -> Dict[str, str]:
        """
        Auto-detects tech stack by analyzing:
        - package.json (Node.js projects)
        - requirements.txt (Python projects)
        - Cargo.toml (Rust projects)
        - go.mod (Go projects)
        - Config files (tsconfig.json, etc.)

        Returns: {framework: version, ...}
        """
```

**Key Features:**
- Detects 59+ technology patterns
- Branching question logic (asks relevant follow-ups)
- Session save/resume capability
- Progress indicator
- Validation with helpful error messages

**SkillGenerator** (`skill_generator.py` - 956 lines)
```python
class SkillGenerator:
    """Main orchestrator for skill generation"""

    def generate_skill(
        self,
        profile: UserProfile,
        skill_type: str,
        force_overwrite: bool = False
    ) -> Path:
        """
        7-step generation process:

        1. Load user profile
        2. Select & load template
        3. Fetch latest documentation (Context7)
        4. Prepare template variables
        5. Process template (TemplateProcessor)
        6. Validate generated SKILL.md
        7. Save to ~/.claude/skills/

        Returns: Path to generated SKILL.md
        """
```

**Generation Pipeline:**
```
User Profile → Load Template → Fetch Docs → Merge Data
     ↓              ↓              ↓            ↓
  Conventions   Structure    Best Practices  Variables
                                              ↓
                                      TemplateProcessor
                                              ↓
                                       SKILL.md (raw)
                                              ↓
                                         Validation
                                              ↓
                                   ~/.claude/skills/
```

**TemplateProcessor** (`template_processor.py` - 527 lines)
```python
class TemplateProcessor:
    """Handlebars/Mustache-style template engine"""

    def process(self, template: str, variables: Dict) -> str:
        """
        Supports:
        - Variables: {{variable_name}}
        - Conditionals: {{#if condition}}...{{/if}}
        - Loops: {{#each items}}...{{/each}}
        - Partials: {{> partial_name}}
        - Escaping: {{{raw_html}}}
        """
```

**Template Syntax Examples:**
```handlebars
{{! Variables }}
# {{skill_name}} Development

{{! Conditionals }}
{{#if use_typescript}}
## TypeScript Configuration
...
{{/if}}

{{! Loops }}
## Best Practices
{{#each best_practices}}
- ✅ {{this}}
{{/each}}

{{! Nested data }}
{{#each user.preferences.naming}}
- {{key}}: {{value}}
{{/each}}
```

**DocFetcher** (`doc_fetcher.py` - 677 lines)
```python
class DocFetcher:
    """Fetches documentation via Context7 MCP"""

    def fetch(self, library_name: str, topic: Optional[str] = None) -> str:
        """
        Fetching process:
        1. Resolve library ID (e.g., "Next.js" → "/vercel/next.js")
        2. Call Context7 get-library-docs
        3. Parse and extract relevant sections
        4. Cache for 7 days
        5. Return formatted documentation
        """

    def get_cached_docs(self, library_id: str) -> Optional[str]:
        """
        Cache structure:
        data/cache/context7/
        └─ {library_id}-{timestamp}.json

        TTL: 7 days
        """
```

**Caching Strategy:**
```python
# Cache key: library_id + timestamp
cache_key = f"{library_id}-{timestamp}"
cache_path = CACHE_DIR / f"{cache_key}.json"

# Check if cache is valid (< 7 days old)
if cache_exists and age < 7_days:
    return cached_docs

# Otherwise fetch fresh
docs = context7.get_library_docs(library_id)
cache_docs(library_id, docs)
```

---

### 2. Orchestrator (`skillforge/analyzers/`)

**Purpose**: Intelligently selects and loads the right skills for each request.

#### Components

**IntentAnalyzer** (`intent_analyzer.py` - 704 lines)
```python
@dataclass
class Intent:
    """Analyzed user intent"""
    entities: List[str]      # ["Next.js", "Supabase", "auth"]
    action: str              # "create", "build", "fix", "analyze"
    domain: str              # "frontend", "backend", "fullstack"
    complexity: str          # "simple", "moderate", "complex"
    patterns: List[Pattern]  # Matched learned patterns
    confidence: float        # 0.0 to 1.0

class IntentAnalyzer:
    """Analyzes user requests to understand intent"""

    def analyze(self, user_request: str) -> Intent:
        """
        5-step analysis:
        1. Extract entities (frameworks, libraries, features)
        2. Determine action (create, update, fix, etc.)
        3. Identify domain (frontend, backend, fullstack)
        4. Assess complexity (simple, moderate, complex)
        5. Match against learned patterns
        """
```

**Entity Extraction Patterns:**
```python
FRAMEWORK_PATTERNS = {
    'nextjs': [r'next\.?js', r'nextjs', r'app router', r'pages router'],
    'react': [r'react(?!.*native)', r'jsx', r'tsx'],
    'vue': [r'vue\.?js', r'vue 3', r'composition api'],
    'svelte': [r'svelte', r'sveltekit'],
    # ... 50+ more patterns
}

FEATURE_PATTERNS = {
    'auth': [r'auth', r'login', r'signup', r'authentication'],
    'dashboard': [r'dashboard', r'admin panel'],
    'api': [r'api', r'endpoint', r'route handler'],
    # ... more patterns
}
```

**SkillDiscovery** (`skill_discovery.py` - 768 lines)
```python
@dataclass
class Skill:
    """Metadata about a skill"""
    name: str
    path: Path
    description: str
    triggers: List[str]      # Keywords that trigger this skill
    dependencies: List[str]  # Other skills required
    priority: int            # Discovery priority score
    usage_count: int         # Times used
    success_rate: float      # Success percentage
    last_used: datetime

class SkillDiscovery:
    """Discovers relevant skills for a given intent"""

    def discover(self, intent: Intent) -> List[Skill]:
        """
        Multi-strategy discovery:

        1. Explicit Match (Priority: 100)
           - User mentions skill name directly
           - "Use nextjs-fullstack skill"

        2. Pattern Match (Priority: 70-90)
           - Learned patterns suggest skills
           - Based on historical usage

        3. Domain Match (Priority: 60)
           - Domain requires certain skills
           - Frontend → UI framework skill

        4. Dependency Match (Priority: 40)
           - Other skills require this
           - nextjs-fullstack requires git-workflow

        5. Entity Match (Priority: 50)
           - Entities match skill triggers
           - "Supabase" → supabase-integration
        """
```

**Discovery Algorithm:**
```python
def discover(self, intent: Intent) -> List[Skill]:
    # Load all available skills
    all_skills = self.load_available_skills()

    # Apply discovery strategies
    candidates = []

    # 1. Explicit mentions
    for skill in all_skills:
        if skill.name in intent.text.lower():
            skill.priority = 100
            candidates.append(skill)

    # 2. Pattern matches
    for pattern in intent.patterns:
        for skill_name in pattern.recommended_skills:
            skill = find_skill(skill_name)
            skill.priority = pattern.confidence * 90
            candidates.append(skill)

    # 3. Domain matches
    domain_skills = self.get_domain_skills(intent.domain)
    for skill in domain_skills:
        skill.priority = 60
        candidates.append(skill)

    # 4. Entity matches
    for entity in intent.entities:
        matching_skills = self.find_skills_for_entity(entity)
        for skill in matching_skills:
            skill.priority = 50
            candidates.append(skill)

    # 5. Dependencies
    required_deps = self.resolve_dependencies(candidates)
    for dep in required_deps:
        dep.priority = 40
        candidates.append(dep)

    # Remove duplicates, sort by priority
    unique_skills = deduplicate(candidates)
    sorted_skills = sorted(unique_skills, key=lambda s: s.priority, reverse=True)

    # Apply token budget filter
    return self.filter_by_token_budget(sorted_skills)
```

---

### 3. Learner (`skillforge/analyzers/`)

**Purpose**: Detects patterns in usage and updates skills automatically.

#### Components

**UsageTracker** (`usage_tracker.py` - 686 lines)
```python
class UsageTracker:
    """Tracks skill usage for pattern learning"""

    def track_usage(
        self,
        skills: List[Skill],
        request: str,
        outcome: str,  # "success" or "failure"
        duration_seconds: float
    ) -> None:
        """
        Records usage event with metadata
        """

    def get_statistics(self) -> Dict:
        """
        Returns analytics:
        - Success rates per skill
        - Common skill combinations
        - Usage trends
        - Performance metrics
        """
```

**Data Schema:**
```json
{
  "skill_usage": {
    "nextjs-fullstack": {
      "total_uses": 156,
      "successes": 147,
      "failures": 9,
      "success_rate": 0.942,
      "last_used": "2025-10-23T10:00:00Z",
      "avg_duration_seconds": 45.2,
      "common_with": ["supabase-integration", "shadcn-ui"]
    }
  },
  "combinations": {
    "nextjs-fullstack+supabase-integration": {
      "count": 89,
      "success_rate": 0.96,
      "contexts": ["auth", "database", "api"]
    }
  },
  "patterns": {
    "create_auth_component": {
      "frequency": 23,
      "skills": ["nextjs-fullstack", "supabase-integration"],
      "confidence": 0.92,
      "first_detected": "2025-09-15",
      "last_reinforced": "2025-10-22"
    }
  }
}
```

**PatternDetector** (`pattern_detector.py` - 825 lines)
```python
@dataclass
class Pattern:
    """A detected usage pattern"""
    name: str
    type: str  # "combination", "style", "workflow"
    description: str
    samples_count: int
    confidence: float  # 0.0 to 1.0
    recommended_skills: List[str]
    recommendations: Dict[str, str]  # Key → value recommendations

class PatternDetector:
    """Detects patterns from usage data"""

    def detect_patterns(self) -> List[Pattern]:
        """
        Pattern detection algorithm:

        1. Collect samples (min 10 required)
        2. Group by similarity
        3. Calculate frequency
        4. Calculate confidence score
        5. Validate pattern quality
        6. Filter by thresholds (min 80% confidence)
        """

    def calculate_confidence(self, pattern: Pattern) -> float:
        """
        Confidence = weighted average of:
        - Frequency weight (40%): How often it occurs
        - Success weight (40%): Success rate when applied
        - Recency weight (20%): How recent the pattern is

        Formula:
        confidence = (
            (min(count / 50, 1.0) * 0.4) +  # Frequency (max at 50 uses)
            (success_rate * 0.4) +           # Success rate
            (recency_bonus * 0.2)            # Recency (decays over time)
        )
        """
```

**LearningPipeline** (`learning_pipeline.py` - 596 lines)
```python
class LearningPipeline:
    """Orchestrates learning cycles"""

    def run_learning_cycle(self) -> LearningReport:
        """
        Automatic learning cycle (runs after N uses, default 10):

        1. Collect usage data
        2. Run pattern detection
        3. Validate patterns
        4. Check confidence thresholds (>= 0.8)
        5. Apply high-confidence patterns to skills
        6. Update skills with new patterns
        7. Notify user of changes
        8. Save state
        """

    def apply_pattern(self, pattern: Pattern, skill: Skill) -> bool:
        """
        Applies a learned pattern to a skill:
        1. Backup skill before changes
        2. Update SKILL.md with pattern recommendations
        3. Validate changes
        4. If validation fails, rollback
        5. Track application for future learning
        """
```

**Pattern Application Flow:**
```
Usage Data (10+ samples)
         ↓
  Pattern Detection
         ↓
  Confidence >= 0.8?
    ↙       ↘
  NO        YES
  ↓          ↓
Store for  Apply Pattern
later         ↓
           Backup Skill
              ↓
           Update SKILL.md
              ↓
           Validate
           ↙    ↘
        FAIL   SUCCESS
         ↓       ↓
      Rollback  Save
         ↓       ↓
      Notify   Notify User
      Error   of Learning
```

---

### 4. Optimizer (`skillforge/analyzers/`)

**Purpose**: Continuously improves skills for performance and quality.

**SkillOptimizer** (`skill_optimizer.py` - 850 lines)
```python
class SkillOptimizer:
    """Optimizes existing skills"""

    def optimize_all_skills(self) -> OptimizationReport:
        """
        5 optimization strategies:

        1. Merge Similar Skills (>70% overlap)
           - Detect content similarity
           - Suggest merge candidates
           - Preserve unique content

        2. Update Documentation (>90 days old)
           - Check last update date
           - Fetch latest docs
           - Update examples and best practices

        3. Compress Verbose Content (>3000 tokens)
           - Identify redundant sections
           - Compress without losing meaning
           - Maintain readability

        4. Restructure for Progressive Disclosure
           - Move details to later sections
           - Improve section organization
           - Optimize token usage

        5. Remove Unused Skills (0 uses in 60 days)
           - Identify unused skills
           - Suggest removal
           - Archive before deletion
        """
```

**Optimization Report Example:**
```json
{
  "analyzed": 12,
  "optimizations": [
    {
      "type": "merge",
      "skills": ["react-spa", "react-vite"],
      "reason": "82% content overlap",
      "token_savings": 1200,
      "action_required": "user_approval"
    },
    {
      "type": "update",
      "skill": "nextjs-fullstack",
      "reason": "Documentation outdated (Next.js 14 → 15)",
      "confidence": 0.95,
      "action_required": "auto_apply"
    },
    {
      "type": "compress",
      "skill": "python-fastapi",
      "current_tokens": 3450,
      "target_tokens": 2800,
      "savings": 650,
      "action_required": "user_review"
    },
    {
      "type": "remove",
      "skill": "vue-legacy",
      "reason": "0 uses in 90 days",
      "action_required": "user_confirmation"
    }
  ],
  "total_token_savings": 3050
}
```

---

## Data Flow

### Complete Request Flow

```
┌──────────────────────────────────────────────────────────────┐
│  USER MAKES REQUEST IN CLAUDE CODE                           │
│  "Create a login component with Supabase auth"               │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  1. INTENT ANALYSIS (IntentAnalyzer)                         │
├──────────────────────────────────────────────────────────────┤
│  Extracts:                                                   │
│  - Entities: ["login", "component", "Supabase", "auth"]      │
│  - Action: "create"                                          │
│  - Domain: "fullstack"                                       │
│  - Complexity: "moderate"                                    │
│  - Patterns: [auth_component_pattern]                        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  2. SKILL DISCOVERY (SkillDiscovery)                         │
├──────────────────────────────────────────────────────────────┤
│  Discovers:                                                  │
│  - nextjs-fullstack (explicit entity match)                  │
│  - supabase-integration (explicit entity match)              │
│  - git-workflow (dependency of nextjs-fullstack)             │
│                                                              │
│  Sorted by priority:                                         │
│  1. nextjs-fullstack (priority: 100, 2534 lines)             │
│  2. supabase-integration (priority: 100, 1823 lines)         │
│  3. git-workflow (priority: 40, 634 lines)                   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  3. TOKEN BUDGET ALLOCATION                                  │
├──────────────────────────────────────────────────────────────┤
│  Budget: 5000 tokens                                         │
│                                                              │
│  Allocation:                                                 │
│  - nextjs-fullstack: 2000 tokens (40%)                       │
│  - supabase-integration: 1800 tokens (36%)                   │
│  - git-workflow: 400 tokens (8%)                             │
│  - Reserved: 800 tokens (16%)                                │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  4. PROGRESSIVE LOADING                                      │
├──────────────────────────────────────────────────────────────┤
│  Level 1 (Metadata): Load YAML frontmatter                   │
│  Level 2 (Core): Load critical sections                      │
│  Level 3 (Full): Load complete content (if needed)           │
│                                                              │
│  For this request: Load Level 2 (sufficient)                 │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  5. CLAUDE CODE EXECUTES WITH LOADED SKILLS                  │
├──────────────────────────────────────────────────────────────┤
│  Claude receives:                                            │
│  - Full context about Next.js patterns                       │
│  - Supabase auth integration patterns                        │
│  - User's conventions injected                               │
│  - Best practices for auth components                        │
│                                                              │
│  Generates:                                                  │
│  src/features/auth/components/LoginForm.tsx                  │
│  - Perfect code with YOUR conventions                        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  6. USAGE TRACKING (UsageTracker)                            │
├──────────────────────────────────────────────────────────────┤
│  Records:                                                    │
│  - Skills used: [nextjs-fullstack, supabase-integration]     │
│  - Request type: "create auth component"                     │
│  - Outcome: "success"                                        │
│  - Duration: 12.3 seconds                                    │
│  - Context: user accepted code without modifications         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  7. PATTERN LEARNING (After 10+ samples)                     │
├──────────────────────────────────────────────────────────────┤
│  Detects:                                                    │
│  - Pattern "auth_component_pattern" occurred 23 times        │
│  - Confidence: 92%                                           │
│  - Always uses: nextjs-fullstack + supabase-integration      │
│                                                              │
│  Action: Apply pattern → Update skills                       │
└──────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Complete Directory Tree

```
~/.claude/skills/skillforge/
│
├── SKILL.md                          # Entry point (meta-skill, 466 lines)
│   └─ Contains: @include references to core files
│
├── core/                             # Behavioral files (11,052 lines total)
│   ├── SKILLFORGE.md                # Core configuration (840 lines)
│   ├── ORCHESTRATION.md             # Orchestration logic (1,912 lines)
│   ├── GENERATOR.md                 # Generation system (1,885 lines)
│   ├── PATTERNS.md                  # Pattern learning (2,042 lines)
│   ├── RULES.md                     # Behavioral rules (831 lines)
│   ├── WORKFLOWS.md                 # Workflow automation (2,283 lines)
│   └── MCP_INTEGRATION.md           # MCP integrations (1,259 lines)
│
├── commands/sf/                      # Slash commands (~2,000 lines total)
│   ├── wizard.md                    # /sf:wizard (287 lines)
│   ├── generate.md                  # /sf:generate (376 lines)
│   ├── analyze.md                   # /sf:analyze (595 lines)
│   ├── optimize.md                  # /sf:optimize (161 lines)
│   ├── update.md                    # /sf:update (89 lines)
│   ├── list.md                      # /sf:list (46 lines)
│   ├── status.md                    # /sf:status (69 lines)
│   ├── config.md                    # /sf:config (74 lines)
│   ├── introspect.md                # /sf:introspect (122 lines)
│   └── reset.md                     # /sf:reset (146 lines)
│
├── skillforge/                       # Python package (16,500 lines total)
│   ├── __init__.py
│   ├── cli.py                       # CLI entry point (82 lines)
│   │
│   ├── generators/                  # Generation engine (3,116 lines)
│   │   ├── __init__.py
│   │   ├── wizard_engine.py        # Interactive wizard (956 lines)
│   │   ├── skill_generator.py      # Main orchestrator (956 lines)
│   │   ├── template_processor.py   # Template engine (527 lines)
│   │   ├── doc_fetcher.py          # Context7 integration (677 lines)
│   │   └── config.py               # Configuration (267 lines)
│   │
│   ├── analyzers/                   # Intelligence system (4,579 lines)
│   │   ├── __init__.py
│   │   ├── intent_analyzer.py      # Intent analysis (704 lines)
│   │   ├── skill_discovery.py      # Skill discovery (768 lines)
│   │   ├── usage_tracker.py        # Usage tracking (686 lines)
│   │   ├── pattern_detector.py     # Pattern detection (825 lines)
│   │   ├── learning_pipeline.py    # Learning orchestration (596 lines)
│   │   └── skill_optimizer.py      # Skill optimization (850 lines)
│   │
│   └── data/
│       ├── skill_files/            # Framework files to be deployed
│       │   ├── SKILL.md
│       │   └── core/
│       │
│       └── templates/              # Skill templates
│           ├── base-skill.template
│           ├── tech-stack/
│           │   ├── nextjs-fullstack.template
│           │   ├── react-spa.template
│           │   ├── vue-spa.template
│           │   ├── python-fastapi.template
│           │   └── ...
│           └── workflow/
│               ├── git-workflow.template
│               └── testing-suite.template
│
├── data/                            # Persistent user data
│   ├── user_profile.json           # User preferences
│   ├── usage_analytics.json        # Usage statistics
│   ├── learned_patterns.json       # Detected patterns
│   └── cache/
│       └── context7/                # Documentation cache (7-day TTL)
│           ├── vercel-nextjs-{timestamp}.json
│           ├── supabase-supabase-{timestamp}.json
│           └── ...
│
├── tests/                           # Test suite (6,279 lines)
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/                       # Unit tests
│   │   ├── test_config.py
│   │   ├── test_wizard_engine.py
│   │   ├── test_skill_generator.py
│   │   ├── test_template_processor.py
│   │   ├── test_doc_fetcher.py
│   │   ├── test_intent_analyzer.py
│   │   ├── test_skill_discovery.py
│   │   ├── test_usage_tracker.py
│   │   ├── test_pattern_detector.py
│   │   ├── test_learning_pipeline.py
│   │   └── test_skill_optimizer.py
│   ├── integration/                # Integration tests
│   └── e2e/                        # End-to-end tests
│
├── scripts/
│   ├── run-tests.sh                # Test runner
│   └── validate-core-files.sh      # Validation script
│
├── docs/                            # Documentation
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md (this file)
│   ├── COMMANDS.md
│   ├── TEMPLATES.md
│   ├── API.md
│   ├── FAQ.md
│   └── TROUBLESHOOTING.md
│
├── setup.py                         # Package setup
├── pyproject.toml                   # Modern Python packaging
├── requirements.txt                 # Dependencies
├── pytest.ini                       # Pytest configuration
└── README.md                        # Project README

Generated skills (created by SkillForge):
~/.claude/skills/
├── nextjs-fullstack/
│   └── SKILL.md
├── supabase-integration/
│   └── SKILL.md
├── git-workflow/
│   └── SKILL.md
└── ... (more generated skills)
```

---

## Design Patterns

### 1. Progressive Disclosure

**Problem**: Skills can be 2000+ lines. Loading all at once wastes tokens.

**Solution**: Three-level loading strategy

```python
# Level 1: Metadata Only (50-100 tokens)
metadata = load_yaml_frontmatter(skill_path)

# Level 2: Core Sections (500-1000 tokens)
core = load_sections(skill_path, ["Overview", "Best Practices", "Common Patterns"])

# Level 3: Full Content (2000+ tokens)
full = load_full_skill(skill_path)

# Decision logic
if intent.complexity == "simple":
    load_level = 1  # Metadata sufficient
elif intent.complexity == "moderate":
    load_level = 2  # Core sections
else:
    load_level = 3  # Full content
```

### 2. Template Method Pattern

**Used in**: SkillGenerator

```python
class SkillGenerator:
    def generate_skill(self, profile, skill_type):
        """Template method defining the algorithm skeleton"""
        # Step 1: Load template (varies by skill_type)
        template = self.load_template(skill_type)

        # Step 2: Fetch docs (varies by framework)
        docs = self.fetch_documentation(skill_type)

        # Step 3: Prepare variables (common)
        variables = self.prepare_variables(profile, docs)

        # Step 4: Process template (common)
        content = self.processor.process(template, variables)

        # Step 5: Validate (common)
        self.validate(content)

        # Step 6: Save (common)
        return self.save(content, skill_type)

    def load_template(self, skill_type):
        """Hook method - subclasses can override"""
        pass

    def fetch_documentation(self, skill_type):
        """Hook method - subclasses can override"""
        pass
```

### 3. Strategy Pattern

**Used in**: SkillDiscovery

```python
class DiscoveryStrategy(ABC):
    @abstractmethod
    def discover(self, intent: Intent) -> List[Skill]:
        pass

class ExplicitMatchStrategy(DiscoveryStrategy):
    def discover(self, intent):
        # Find skills explicitly mentioned
        return [skill for skill in skills if skill.name in intent.text]

class PatternMatchStrategy(DiscoveryStrategy):
    def discover(self, intent):
        # Find skills based on learned patterns
        return pattern_based_skills

class DomainMatchStrategy(DiscoveryStrategy):
    def discover(self, intent):
        # Find skills based on domain
        return domain_skills

class SkillDiscovery:
    def __init__(self):
        self.strategies = [
            ExplicitMatchStrategy(),
            PatternMatchStrategy(),
            DomainMatchStrategy(),
        ]

    def discover(self, intent):
        all_candidates = []
        for strategy in self.strategies:
            candidates = strategy.discover(intent)
            all_candidates.extend(candidates)
        return self.merge_and_rank(all_candidates)
```

### 4. Observer Pattern

**Used in**: UsageTracker → PatternDetector

```python
class UsageTracker:
    def __init__(self):
        self.observers = []

    def attach(self, observer):
        self.observers.append(observer)

    def track_usage(self, event):
        # Track usage
        self.save_event(event)

        # Notify observers
        for observer in self.observers:
            observer.on_usage_event(event)

class PatternDetector:
    def on_usage_event(self, event):
        """Called by UsageTracker when new usage occurs"""
        self.samples.append(event)

        # Check if we have enough samples
        if len(self.samples) >= MIN_SAMPLES:
            self.detect_patterns()
```

### 5. Builder Pattern

**Used in**: WizardEngine

```python
class ProfileBuilder:
    def __init__(self):
        self.profile = UserProfile()

    def with_tech_stack(self, stack):
        self.profile.tech_stack = stack
        return self

    def with_naming_conventions(self, conventions):
        self.profile.naming = conventions
        return self

    def with_import_style(self, style):
        self.profile.imports = style
        return self

    def build(self):
        return self.profile

# Usage in wizard
builder = ProfileBuilder()
profile = (builder
    .with_tech_stack(detected_stack)
    .with_naming_conventions(user_answers['naming'])
    .with_import_style(user_answers['imports'])
    .build())
```

---

## Integration Points

### 1. Claude Code Native Skills

SkillForge extends Claude Code's native skill system:

```
Claude Code Startup:
1. Scans ~/.claude/skills/
2. Finds skillforge/SKILL.md
3. Loads SKILL.md (with @include references)
4. SkillForge becomes available

When user makes request:
1. SkillForge analyzes intent
2. Discovers relevant skills
3. Loads skills dynamically
4. Claude receives perfect context
```

### 2. Context7 MCP Server

Integration via Model Context Protocol:

```python
# SkillForge → Context7 communication
from mcp import MCPClient

client = MCPClient("context7")

# Step 1: Resolve library ID
library_id = client.call_tool(
    "resolve-library-id",
    {"libraryName": "Next.js"}
)
# Returns: "/vercel/next.js"

# Step 2: Get documentation
docs = client.call_tool(
    "get-library-docs",
    {
        "context7CompatibleLibraryID": library_id,
        "topic": "App Router",
        "tokens": 2000
    }
)
# Returns: Latest Next.js App Router documentation
```

### 3. Sequential Thinking MCP (Optional)

For complex orchestration decisions:

```python
# Use Sequential Thinking for complex analysis
thought_chain = sequential_thinking(
    prompt="Analyze which skills to load for: 'Create complex dashboard with real-time data'",
    max_thoughts=10
)

# Returns: Detailed reasoning chain
# → Thought 1: User wants dashboard (visual component)
# → Thought 2: Real-time suggests WebSocket or SSE
# → Thought 3: Need frontend framework skill
# → Thought 4: Need real-time integration skill
# → Decision: Load nextjs-fullstack + supabase-realtime
```

---

## Performance & Optimization

### Token Budget Management

**Goal**: Keep total skill tokens under 5000 to optimize Claude's context window.

**Strategy**:
```python
TOTAL_BUDGET = 5000  # tokens
RESERVED = 800       # for future expansion

def allocate_token_budget(skills: List[Skill]) -> Dict[Skill, int]:
    available = TOTAL_BUDGET - RESERVED  # 4200 tokens

    # Calculate priority-weighted allocation
    total_priority = sum(skill.priority for skill in skills)

    allocation = {}
    for skill in skills:
        weight = skill.priority / total_priority
        skill_tokens = int(available * weight)
        allocation[skill] = skill_tokens

    return allocation
```

### Caching Strategy

**Documentation Cache** (7-day TTL):
```python
# Cache structure
cache_dir = ~/.claude/skills/skillforge/data/cache/context7/
cache_file = f"{library_id}-{timestamp}.json"

# Cache validation
def is_cache_valid(cache_file):
    age = now() - cache_file.mtime
    return age < timedelta(days=7)

# Usage
if cache_exists and is_cache_valid(cache_file):
    return load_from_cache()
else:
    docs = fetch_fresh_docs()
    cache_docs(docs)
    return docs
```

**Skill Metadata Cache** (in-memory):
```python
# Load all skill metadata once at startup
skill_cache = {}
for skill_path in glob("~/.claude/skills/*/SKILL.md"):
    metadata = load_yaml_frontmatter(skill_path)
    skill_cache[metadata['name']] = {
        'path': skill_path,
        'description': metadata['description'],
        'triggers': metadata.get('triggers', []),
        'size_lines': count_lines(skill_path)
    }

# Fast lookups during orchestration
relevant_skills = [
    skill_cache[name]
    for name in discovered_skill_names
]
```

### Progressive Loading

**Load only what you need**:
```python
class SkillLoader:
    def load(self, skill_path, level=2):
        if level == 1:
            # Metadata only (fastest)
            return self.load_frontmatter(skill_path)

        elif level == 2:
            # Core sections (balanced)
            content = self.load_frontmatter(skill_path)
            content += self.load_sections(
                skill_path,
                ['Overview', 'Best Practices', 'Common Patterns']
            )
            return content

        else:
            # Full content (slowest)
            return self.load_full(skill_path)
```

---

## Extension Points

### Adding New Skill Types

1. Create template in `templates/tech-stack/`
2. Add detection pattern to WizardEngine
3. Add to SkillGenerator supported types
4. Test generation pipeline

### Adding New Discovery Strategies

1. Implement `DiscoveryStrategy` interface
2. Add to `SkillDiscovery.strategies` list
3. Set priority score
4. Test with sample intents

### Adding New Pattern Types

1. Add pattern type to `PatternDetector.PATTERN_TYPES`
2. Implement detection algorithm
3. Define confidence calculation
4. Add application logic to `LearningPipeline`

---

## Security Considerations

### Data Privacy

- **All data stored locally**: No external servers except Context7 (public docs only)
- **No sensitive data collection**: Only tracks public code patterns
- **User control**: Opt-out available for all tracking

### Validation

- **Input validation**: All user inputs validated before processing
- **Template injection prevention**: Sandboxed template processing
- **File path validation**: Only allow writes to `~/.claude/skills/`

### Safe Pattern Application

- **Backup before changes**: Always create backup before updating skills
- **Validation after changes**: Verify YAML and structure
- **Rollback on failure**: Automatic rollback if validation fails
- **User notification**: Always notify user of learned patterns

---

## Testing Strategy

### Unit Tests (413 tests, 88% passing)

```bash
# Run unit tests
pytest tests/unit/ -v

# Coverage report
pytest tests/unit/ --cov=skillforge --cov-report=html
```

### Integration Tests

```bash
# Test full pipelines
pytest tests/integration/ -v
```

### E2E Tests

```bash
# Test real usage scenarios
pytest tests/e2e/ -v -m e2e
```

---

## Further Reading

- [Quick Start Guide](QUICKSTART.md) - Get started in 10 minutes
- [Commands Reference](COMMANDS.md) - All slash commands
- [API Documentation](API.md) - Python API reference
- [Template Guide](TEMPLATES.md) - Create custom templates
- [FAQ](FAQ.md) - Common questions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**For developers, by developers. Built with Claude Code.**

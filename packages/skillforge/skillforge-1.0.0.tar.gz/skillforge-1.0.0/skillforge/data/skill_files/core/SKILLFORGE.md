# SkillForge Core Configuration

**Central configuration for SkillForge's meta-programming framework**

This file defines the core philosophy, operational modes, algorithms, and rules that govern how SkillForge generates, orchestrates, and optimizes Claude Code skills.

---

## 1. Core Philosophy

SkillForge is built on four fundamental principles that guide all decision-making:

### Principle 1: Personalization Over Generalization

**Philosophy**: Every developer has unique preferences, conventions, and workflows. Generic solutions create friction and require manual adjustments.

**Implementation**:
- Generate skills tailored to user's specific tech stack
- Incorporate user's naming conventions, code style, and patterns
- Learn from user's modifications and adapt over time
- Never assume "best practices" are universal

**Example**:
```
Generic Skill: "Use React hooks for state management"
Personalized Skill: "Use Zustand for global state (user preference),
                     useState for component state, file names in camelCase"
```

### Principle 2: Intelligence Over Automation

**Philosophy**: Blindly automating tasks without understanding context leads to poor results. Intelligence means knowing WHEN and HOW to act.

**Implementation**:
- Analyze intent before selecting skills
- Understand project context before generating code
- Ask clarifying questions when ambiguous
- Provide reasoning for decisions made
- Suggest alternatives when appropriate

**Example**:
```
Bad Automation: "User mentioned 'auth' → Generate auth component"
Intelligent Action: "User mentioned 'auth' → Analyze: What auth provider?
                     What UI library? Existing auth setup? → Then generate"
```

### Principle 3: Evolution Over Stasis

**Philosophy**: Technology changes rapidly. Static knowledge becomes outdated. Skills must evolve continuously.

**Implementation**:
- Fetch latest documentation via Context7 before generating
- Track when skills were last updated
- Detect outdated patterns and suggest updates
- Learn from usage patterns and improve over time
- Decay confidence in unused patterns

**Example**:
```
Static: "Always use getServerSideProps" (Next.js 12 pattern)
Evolving: "Check Next.js version → Use App Router patterns for v13+"
```

### Principle 4: Efficiency Over Completeness

**Philosophy**: Token budgets are finite. Loading all possible information is wasteful. Progressive disclosure maximizes value per token.

**Implementation**:
- Load only relevant skills for current task
- Use hierarchical loading (overview → details)
- Cache frequently used information
- Compress without losing essential information
- Prioritize high-value content

**Example**:
```
Inefficient: Load all 8 skills (12,000 tokens) for simple task
Efficient: Load 2 relevant skills (3,000 tokens), expand if needed
```

---

## 2. Operational Modes

SkillForge operates in different modes based on context. Each mode has specific triggers, behaviors, and outputs.

### Mode 1: Setup Mode

**When**: First-time use, no user profile exists, user runs `/sf:wizard`

**Triggers**:
- `user_profile.json` does not exist
- User explicitly requests setup/configuration
- User mentions "initialize", "setup", "configure"

**Behavior**:
1. Greet user, explain SkillForge
2. Auto-detect tech stack from current directory
3. Run interactive questionnaire (10-12 questions)
4. Generate user_profile.json
5. Suggest skills to generate based on profile
6. Optionally generate initial skills
7. Notify user to restart Claude Code

**Output**:
- `data/user_profile.json` created
- Initial skills generated in `~/.claude/skills/generated/`
- Setup completion message

**Token Budget**: ~8000 tokens (comprehensive guidance)

### Mode 2: Orchestration Mode (DEFAULT)

**When**: User has profile, making coding request

**Triggers**:
- Any development task (build, fix, refactor, etc.)
- User mentions specific frameworks/libraries
- User requests feature implementation

**Behavior**:
1. Analyze user intent (entities, action, domain, complexity)
2. Discover relevant skills from installed skills
3. Load skills progressively (essential → detailed)
4. Execute task using loaded skills
5. Track usage for learning
6. Update analytics in background

**Output**:
- Generated code following user conventions
- Usage data recorded
- Skills used logged

**Token Budget**: ~5000 tokens (focused on task)

### Mode 3: Learning Mode (BACKGROUND)

**When**: Continuously after N skill uses (default: 10)

**Triggers**:
- Skill usage counter reaches threshold
- Periodic trigger (daily)
- User explicitly runs `/sf:analyze`

**Behavior**:
1. Load usage analytics
2. Detect patterns (naming, preferences, combinations)
3. Calculate confidence scores
4. Filter patterns by threshold (>0.8)
5. Identify skills to update
6. Generate update suggestions
7. Notify user of learnings (if significant)

**Output**:
- `data/learned_patterns.json` updated
- Skill update suggestions
- Optional user notification

**Token Budget**: ~3000 tokens (analytical)

### Mode 4: Optimization Mode (PERIODIC)

**When**: User runs `/sf:optimize`, weekly automatic trigger

**Triggers**:
- User explicitly requests optimization
- Skills not optimized in 7+ days
- Token usage exceeds budget frequently

**Behavior**:
1. Analyze all generated skills
2. Identify redundancies and overlaps
3. Calculate token usage per skill
4. Suggest merges for similar skills (>70% overlap)
5. Identify outdated documentation
6. Generate optimization report
7. Apply safe optimizations (with confirmation)

**Output**:
- Optimization report with suggestions
- Merged skills (if approved)
- Updated skills with latest docs
- Token savings summary

**Token Budget**: ~4000 tokens (comprehensive analysis)

### Mode 5: Update Mode (WEEKLY)

**When**: User runs `/sf:update`, skills outdated

**Triggers**:
- Skills older than 30 days
- User mentions "update" or "outdated"
- Framework version changes detected

**Behavior**:
1. Check last update date for each skill
2. Identify skills needing updates
3. Fetch latest documentation via Context7
4. Compare current vs. new patterns
5. Generate skill updates
6. Validate updated skills
7. Backup old versions
8. Apply updates (with confirmation)

**Output**:
- Updated skills with latest patterns
- Changelog of what changed
- Backed up old versions
- Update summary

**Token Budget**: ~6000 tokens (comprehensive updates)

---

## 3. Skill Discovery Algorithm

**Purpose**: Given a user's intent, discover which skills should be loaded and in what order.

### Algorithm (Pseudocode)

```python
def discover_skills(intent: Intent, user_profile: Profile) -> List[Skill]:
    """
    Discover relevant skills for user's intent.

    Steps:
    1. Extract entities from intent
    2. Find explicitly mentioned skills
    3. Find domain-required skills
    4. Find pattern-suggested skills
    5. Find dependency skills
    6. Remove duplicates
    7. Sort by priority
    8. Filter by token budget
    """

    discovered_skills = []

    # Step 1: Explicit mentions (highest priority)
    for entity in intent.entities:
        skill = find_skill_by_name(entity)
        if skill:
            discovered_skills.append({
                'skill': skill,
                'priority': 100,
                'reason': 'explicit_mention'
            })

    # Step 2: Domain requirements
    domain_skills = get_domain_skills(intent.domain)
    for skill in domain_skills:
        if skill not in discovered_skills:
            discovered_skills.append({
                'skill': skill,
                'priority': 80,
                'reason': 'domain_requirement'
            })

    # Step 3: Pattern matches (learned from history)
    patterns = match_patterns(intent, user_profile.learned_patterns)
    for pattern in patterns:
        for skill_name in pattern.skills:
            skill = find_skill_by_name(skill_name)
            if skill and skill not in discovered_skills:
                discovered_skills.append({
                    'skill': skill,
                    'priority': 70 + (pattern.confidence * 20),
                    'reason': f'pattern:{pattern.name}'
                })

    # Step 4: Dependencies
    dependencies = resolve_dependencies(discovered_skills)
    for dep_skill in dependencies:
        if dep_skill not in discovered_skills:
            discovered_skills.append({
                'skill': dep_skill,
                'priority': 60,
                'reason': 'dependency'
            })

    # Step 5: Remove duplicates
    discovered_skills = deduplicate(discovered_skills)

    # Step 6: Sort by priority (descending)
    discovered_skills.sort(key=lambda x: x['priority'], reverse=True)

    # Step 7: Apply token budget constraints
    budget_remaining = 5000  # Default token budget
    filtered_skills = []

    for item in discovered_skills:
        skill_tokens = estimate_skill_tokens(item['skill'])
        if budget_remaining >= skill_tokens:
            filtered_skills.append(item)
            budget_remaining -= skill_tokens
        else:
            # Use minimal version if essential
            if item['priority'] >= 90:
                minimal_tokens = skill_tokens * 0.3  # Load only essentials
                filtered_skills.append({
                    **item,
                    'load_mode': 'minimal'
                })
                budget_remaining -= minimal_tokens

    return filtered_skills
```

### Concrete Example

**User Request**: "Create a Next.js login component with Supabase"

**Intent Analysis**:
```python
Intent(
    entities=['Next.js', 'login component', 'Supabase'],
    action='create',
    domain='fullstack',
    complexity='moderate'
)
```

**Discovery Process**:

1. **Explicit Mentions** (Priority 100)
   - `nextjs-fullstack` (mentioned: "Next.js")
   - `supabase-integration` (mentioned: "Supabase")

2. **Domain Requirements** (Priority 80)
   - `typescript-patterns` (domain: fullstack, if TypeScript in profile)

3. **Pattern Matches** (Priority 70-90)
   - Pattern "auth_component_pattern" matched (confidence: 0.92)
   - Suggests: `ui-components` (user's UI library)

4. **Dependencies** (Priority 60)
   - `nextjs-fullstack` requires: `react-patterns`

5. **Sorted by Priority**:
   ```
   1. nextjs-fullstack (100) - 2000 tokens
   2. supabase-integration (100) - 1500 tokens
   3. ui-components (88) - 800 tokens
   4. typescript-patterns (80) - 600 tokens
   5. react-patterns (60) - 400 tokens
   ```

6. **Token Budget Allocation** (5000 token budget):
   - Total needed: 5300 tokens
   - Loads: Items 1-5 (all fit)
   - Final: 5 skills loaded, ~5300 tokens

**Result**: Perfect skill combination for the task, all user preferences included.

---

## 4. Token Economics

**Core Principle**: Maximize value delivered per token spent.

### Budget Allocation Strategy

**Total Budget**: 5000 tokens (configurable in user_profile.json)

**Allocation**:
```
Core Framework Files:  1000 tokens (20%)
  - This file (SKILLFORGE.md)
  - RULES.md

User Skills:          3500 tokens (70%)
  - Primary skills for task
  - Supporting skills
  - Dependencies

User Profile/Context:  500 tokens (10%)
  - User conventions
  - Learned patterns
  - Recent history
```

### Token Optimization Techniques

1. **Progressive Disclosure**
   - Load overview first, details on demand
   - Example: Skill header (200 tokens) → Full content (2000 tokens)

2. **Hierarchical Loading**
   ```
   Level 1: Skill name + description (50 tokens)
   Level 2: + Core concepts (200 tokens)
   Level 3: + Best practices (500 tokens)
   Level 4: + Full examples (2000 tokens)
   ```

3. **Caching Strategy**
   - Cache frequently used skills in conversation context
   - Don't reload unchanged content
   - Reference previous loads: "Using cached nextjs-fullstack"

4. **Compression**
   - Remove verbose explanations, keep actionable content
   - Use bullet points over paragraphs
   - Code examples over text descriptions

5. **Prioritization**
   - Essential content first (80/20 rule)
   - Nice-to-have content only if budget allows
   - Defer low-priority content to follow-up

### Token Breakdown by Category

**High Value** (Always include):
- User conventions (naming, style, preferences)
- Framework-specific patterns for user's stack
- Error handling patterns
- Current best practices

**Medium Value** (Include if budget allows):
- Code examples
- Anti-patterns
- Related skills references
- Alternative approaches

**Low Value** (Defer or omit):
- Historical context
- Verbose explanations
- Redundant examples
- Deprecated patterns

---

## 5. Skill Generation Rules

### CRITICAL RULES (ALWAYS FOLLOW)

🔴 **RULE 1**: ALWAYS fetch latest documentation via Context7
- Never use potentially outdated Claude knowledge
- Always call `resolve-library-id` → `get-library-docs`
- Cache results for 7 days
- Fallback to web_search only if Context7 fails

🔴 **RULE 2**: ALWAYS validate user profile exists
- Check `data/user_profile.json` exists
- If missing → prompt user to run `/sf:wizard`
- Never generate without knowing user's stack

🔴 **RULE 3**: ALWAYS validate YAML frontmatter
- Use PyYAML to validate before writing file
- Required fields: name, description, version, allowed-tools
- Fail generation if YAML invalid

🔴 **RULE 4**: ALWAYS use absolute paths
- Never use relative paths in generated content
- Always reference `~/.claude/skills/skillforge/`
- Avoid assumptions about working directory

🔴 **RULE 5**: NEVER expose sensitive data
- Sanitize file paths (remove usernames)
- Never include API keys, credentials
- Scrub any PII from examples

### Context7 Integration

**Before Every Skill Generation**:

```python
# 1. Resolve library ID
library_id = resolve_library_id(library_name="next.js")
# Returns: "/vercel/next.js" or similar

# 2. Fetch latest documentation
docs = get_library_docs(
    library_id=library_id,
    topic="app-router",  # Focus on relevant topic
    tokens=3000  # Limit to prevent overflow
)

# 3. Cache for future use
cache_docs(library_id, docs, ttl_days=7)

# 4. Extract key information
best_practices = extract_patterns(docs)
code_examples = extract_examples(docs)
version_info = extract_version(docs)
```

### Structure Requirements

Every generated SKILL.md MUST have:

```markdown
---
name: "skill-name"
description: "Clear, specific description"
version: "1.0.0"
generated_at: "2025-01-22T10:00:00Z"
based_on: "Framework X v14.0"
allowed-tools: [...]
---

# Skill Name

## Overview
[What this skill does]

## When to Use
[Specific scenarios]

## Core Concepts
[Key concepts with examples]

## Best Practices
[Do's and Don'ts from latest docs]

## User Conventions
[User's specific preferences]

## Common Patterns
[Code patterns with full examples]

## Anti-Patterns
[What to avoid]

## Related Skills
[Links to other skills]

## Resources
[Documentation links]
```

### User Conventions Integration

**ALWAYS incorporate from user_profile.json**:

```json
{
  "conventions": {
    "naming": {
      "files": "kebab-case",
      "components": "PascalCase",
      "functions": "camelCase"
    },
    "imports": {
      "style": "absolute",
      "order": ["react", "libraries", "local"]
    },
    "error_handling": "try-catch with custom error classes",
    "testing": "Vitest with @testing-library"
  }
}
```

Apply conventions to ALL generated code examples.

### Composability Rules

1. **Single Responsibility**: Each skill focuses on ONE technology/concept
2. **Clear Dependencies**: Document what skills this requires
3. **No Overlap**: Don't duplicate content from other skills
4. **Cross-References**: Link to related skills explicitly
5. **Modular**: Skills can be used independently or combined

---

## 6. Pattern Learning System

### Data Schema

```json
{
  "pattern_id": "always_use_zod",
  "type": "tool_preference",
  "detected_at": "2025-01-20T10:00:00Z",
  "confidence": 0.92,
  "occurrences": 23,
  "description": "User always uses Zod for validation",
  "evidence": [
    {"task": "form_validation", "used": "zod", "timestamp": "..."},
    {"task": "api_validation", "used": "zod", "timestamp": "..."}
  ],
  "applied_to_skills": ["nextjs-fullstack", "api-routes"],
  "user_confirmed": true
}
```

### Learning Process (5 Steps)

1. **Collection** (Continuous)
   - Track every skill usage
   - Record user modifications to generated code
   - Note library choices
   - Track naming patterns

2. **Analysis** (After 10+ uses)
   - Group similar behaviors
   - Calculate frequency
   - Identify consistent patterns
   - Filter noise (random variations)

3. **Validation** (Confidence > 0.7)
   - Ensure pattern is statistically significant
   - Check pattern is recent (last 30 days)
   - Verify pattern is consistent (not conflicting)

4. **Notification** (Confidence > 0.8)
   - Show pattern to user
   - Explain evidence
   - Ask for confirmation
   - Allow opt-out

5. **Application** (User confirmed)
   - Update affected skills
   - Add pattern to user_profile
   - Track pattern effectiveness

### Update Triggers

- **Immediate**: User confirms high-confidence pattern (>0.9)
- **Batched**: Multiple medium-confidence patterns (0.8-0.9) weekly
- **Manual**: User runs `/sf:optimize`

---

## 7. MCP Integration Strategy

### Primary MCP Servers

1. **Context7** (PRIMARY - Documentation)
   - When: Before every skill generation
   - Purpose: Fetch latest framework documentation
   - Priority: HIGHEST

2. **Sequential Thinking** (SECONDARY - Complex reasoning)
   - When: Complex multi-step tasks
   - Purpose: Break down complex problems
   - Priority: MEDIUM

3. **Web Search/Fetch** (FALLBACK)
   - When: Context7 unavailable
   - Purpose: Backup documentation source
   - Priority: LOW

### When to Use Each

**Use Context7 when**:
- Generating new skill
- Updating existing skill
- User asks about latest features
- Framework version changed

**Use Sequential Thinking when**:
- Task requires >5 steps
- Multiple skills need coordination
- Complex architectural decision
- Optimization requires deep analysis

**Use Web Search when**:
- Context7 fails (network error)
- Niche/unofficial library
- User-specific question
- Troubleshooting specific error

---

## 8. Error Recovery

### Common Scenarios & Recovery

**Scenario 1: Context7 API Failure**
```
Error: Cannot reach Context7 MCP
Recovery:
  1. Check cache for recent docs (<7 days)
  2. If cached → Use cached docs
  3. If no cache → Fallback to web_search
  4. If web_search fails → Use Claude built-in knowledge
  5. ALWAYS inform user of data source and freshness
```

**Scenario 2: Invalid YAML Generated**
```
Error: YAML parsing error in generated SKILL.md
Recovery:
  1. Log the error with details
  2. Identify the YAML issue
  3. Fix and retry generation ONCE
  4. If still fails → Alert user, request bug report
  5. Rollback any partial generation
```

**Scenario 3: Skill Already Exists**
```
Error: Skill "nextjs-fullstack" already exists
Recovery:
  1. Load existing skill
  2. Show user current version
  3. Ask: Update or create variant?
  4. If update → Run update flow
  5. If variant → Append -v2 or ask for new name
```

**Scenario 4: Token Budget Exceeded**
```
Warning: Skills would use 7500 tokens (budget: 5000)
Recovery:
  1. Prioritize skills by importance
  2. Load top 3 in full (3500 tokens)
  3. Load remaining in minimal mode (headers only)
  4. Inform user of constraint
  5. Suggest running /sf:optimize
```

### Fallback Mechanisms

**Chain of Fallbacks**:
```
Primary → Context7 MCP
    ↓ (on failure)
Fallback 1 → Cache (if <7 days old)
    ↓ (if no cache)
Fallback 2 → Web Search
    ↓ (if fails)
Fallback 3 → Claude built-in knowledge
    ↓ (always notify)
User Notification: "Using [source], may be outdated"
```

---

## 9. Quality Standards

### Generated Skills Checklist

**MUST HAVE** ✅:
- [ ] Valid YAML frontmatter (all required fields)
- [ ] Clear, specific description (not generic)
- [ ] Latest patterns from documentation (Context7)
- [ ] User conventions integrated throughout
- [ ] Complete code examples (no placeholders like `// TODO`)
- [ ] Error handling patterns
- [ ] Testing approaches
- [ ] Related skills referenced
- [ ] Version and generation timestamp

**MUST NOT HAVE** ❌:
- [ ] Generic placeholder text ("Add your code here")
- [ ] Outdated patterns (deprecated APIs)
- [ ] Hardcoded paths or credentials
- [ ] Conflicting advice
- [ ] Incomplete examples
- [ ] Missing sections
- [ ] Broken markdown formatting
- [ ] Invalid YAML

### Pre-Generation Validation

Before starting generation:
```python
def validate_pre_generation(user_profile, library_name):
    checks = []

    # Check 1: User profile exists
    if not user_profile.exists():
        return Error("User profile required. Run /sf:wizard")

    # Check 2: Tech stack defined
    if not user_profile.tech_stack:
        return Error("Tech stack not defined in profile")

    # Check 3: Library is relevant
    if library_name not in user_profile.tech_stack.values():
        return Warning("Library not in user's stack. Continue anyway?")

    # Check 4: Context7 accessible
    if not test_context7_connection():
        return Warning("Context7 unavailable. Will use fallback.")

    return Success("Pre-generation checks passed")
```

### Post-Generation Validation

After skill generated:
```python
def validate_post_generation(skill_path):
    skill_content = read_file(skill_path)

    # Validate YAML
    yaml_valid, yaml_data = validate_yaml_frontmatter(skill_content)
    if not yaml_valid:
        return Error("Invalid YAML frontmatter")

    # Check required sections
    required_sections = [
        "# ", "## Overview", "## When to Use",
        "## Best Practices", "## User Conventions"
    ]
    for section in required_sections:
        if section not in skill_content:
            return Error(f"Missing required section: {section}")

    # Check for placeholders
    placeholders = ["TODO", "FIXME", "[Add your", "placeholder"]
    for placeholder in placeholders:
        if placeholder in skill_content:
            return Error(f"Contains placeholder: {placeholder}")

    # Check code examples are complete
    code_blocks = extract_code_blocks(skill_content)
    for block in code_blocks:
        if len(block.strip()) < 20:  # Too short to be real code
            return Error("Code examples too minimal")

    return Success("Post-generation validation passed")
```

---

## 🎯 Summary

This configuration file defines:
- **4 Core Principles** guiding all decisions
- **5 Operational Modes** for different contexts
- **Skill Discovery Algorithm** with concrete example
- **Token Economics** maximizing value per token
- **Generation Rules** ensuring quality and consistency
- **Pattern Learning** for continuous improvement
- **MCP Integration** with fallback strategies
- **Error Recovery** for robustness
- **Quality Standards** for excellence

**These configurations ensure SkillForge generates personalized, up-to-date, efficient skills that evolve with the user.**

---

*Last Updated: 2025-01-22*
*Version: 0.0.1-dev*

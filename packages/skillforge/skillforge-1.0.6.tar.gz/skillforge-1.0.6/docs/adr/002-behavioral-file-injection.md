# ADR 002: Behavioral File Injection Pattern

## Status
**Accepted** - 2025-10-22

## Context
SkillForge needs to provide guidance to Claude Code on how to:
- Generate skills properly
- Orchestrate multiple skills
- Apply learned patterns
- Optimize existing skills

**Options considered**:
1. All-in-one SKILL.md (monolithic)
2. Behavioral file injection (modular)
3. External Python scripts only
4. Hardcoded prompts in Python

## Decision
Use **Behavioral File Injection** pattern inspired by SuperClaude Framework.

## Pattern Description

### Structure
```
~/.claude/skills/skillforge/
├── SKILL.md                      # Entry point with @references
│
├── core/                         # Behavioral instruction files
│   ├── SKILLFORGE.md            # Core configuration
│   ├── ORCHESTRATION.md         # Orchestration logic
│   ├── GENERATOR.md             # Generation system
│   ├── PATTERNS.md              # Pattern learning
│   ├── RULES.md                 # Behavioral rules
│   ├── WORKFLOWS.md             # Workflows
│   └── MCP_INTEGRATION.md       # MCP integration
│
└── commands/sf/                  # Slash commands
    ├── wizard.md
    └── ...
```

### SKILL.md References Core Files
```markdown
---
name: "SkillForge"
description: "Meta-programming framework..."
---

# SkillForge

## Configuration System
@core/SKILLFORGE.md
@core/ORCHESTRATION.md
@core/GENERATOR.md
...
```

## Rationale

### Why Behavioral Injection

**✅ Pros**:

1. **Modularity**
   - Each file focused on single concern
   - Easy to update individual aspects
   - Clear separation of responsibilities

2. **Progressive Disclosure**
   - SKILL.md loaded always (small)
   - Core files loaded when needed
   - Reduces token overhead

3. **Maintainability**
   - Update orchestration logic without touching generation
   - Version control friendly (clear diffs)
   - Multiple developers can work simultaneously

4. **Scalability**
   - Add new behavioral aspects (new file)
   - Remove deprecated behaviors (delete file)
   - No monolithic file to manage

5. **Testability**
   - Test each behavioral aspect independently
   - Validate individual file structure
   - Easy to identify which file causes issues

6. **Proven Pattern**
   - SuperClaude successfully uses this
   - Claude Code supports @references
   - Community familiar with pattern

### Why NOT Monolithic

**❌ Cons**:
1. Single 5000+ line SKILL.md
   - Hard to navigate
   - Difficult to maintain
   - Large token overhead
   - Merge conflicts
   - Unclear structure

2. All changes touch same file
   - Version control conflicts
   - Hard to track what changed
   - Testing is all-or-nothing

### Why NOT Python-Only

**❌ Cons**:
1. Claude Code can't read Python guidance naturally
2. Separates behavior from skills system
3. Harder to share knowledge (code vs docs)
4. Less transparent to users

### Why NOT Hardcoded Prompts

**❌ Cons**:
1. Can't update without code changes
2. Not transparent to users
3. Hard to customize
4. Loses flexibility

## Consequences

### Positive
- ✅ **Clear structure**: Easy to find relevant instructions
- ✅ **Efficient**: Only load what's needed (progressive disclosure)
- ✅ **Maintainable**: Update specific aspects independently
- ✅ **Scalable**: Add new behaviors without restructuring
- ✅ **Community friendly**: Standard Markdown, git-friendly

### Negative
- ⚠️ **Multiple files**: More files to manage
- ⚠️ **Cross-references**: Need to ensure references stay valid
- ⚠️ **Learning curve**: Users need to understand structure

### Mitigation
- Validation script checks all @references exist
- Documentation explains structure clearly
- Templates for new behavioral files

## Implementation Guidelines

### File Naming Convention
```
Core files: UPPERCASE.md (e.g., SKILLFORGE.md)
Commands: lowercase-kebab.md (e.g., wizard.md)
```

### File Size Targets
```
SKILL.md:           < 500 lines (entry point)
Core files:         < 600 lines each (focused)
Command files:      < 300 lines each (specific)
```

### Validation
```python
def validate_references(skill_path):
    """Validate all @references exist"""
    with open(skill_path / "SKILL.md") as f:
        content = f.read()

    references = re.findall(r'@(\S+\.md)', content)

    for ref in references:
        ref_path = skill_path / ref
        if not ref_path.exists():
            raise ValidationError(f"Missing reference: {ref}")

    return True
```

## Content Guidelines

### Declarative, Not Imperative

**✅ Good** (Declarative):
```markdown
## Skill Generation Rules
- ALWAYS fetch latest documentation via Context7
- NEVER generate skills without user profile
- ALWAYS validate YAML frontmatter
```

**❌ Bad** (Imperative):
```markdown
## Skill Generation
First, call context7_fetch().
Then, load the user profile.
After that, validate the YAML...
```

### Structured Sections

Each core file should have:
1. **Overview** - What this file covers
2. **Principles** - Guiding philosophy
3. **Rules** - Specific behaviors
4. **Examples** - Concrete illustrations
5. **Edge Cases** - How to handle exceptions

## References
- SuperClaude Framework: https://github.com/SuperClaude-Org/SuperClaude_Framework
- Research: docs/research/superclaude-patterns.md
- Claude Code Skills Docs: https://docs.claude.com/en/docs/claude-code/skills

## Review Criteria
Will reconsider if:
- File count becomes unmanageable (>15 core files)
- Cross-reference maintenance becomes error-prone
- Alternative pattern proves more effective
- Community feedback indicates confusion

## Timeline
- **Fase 2**: Create all core behavioral files
- **Fase 6**: Create all command files
- **Fase 8**: Add validation tests for references

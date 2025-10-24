---
name: "SkillForge"
description: >
  Meta-programming framework that transforms Claude Code into an intelligent development partner.
  Automatically generates personalized skills for your tech stack, orchestrates multi-skill workflows,
  learns from your patterns and preferences, and keeps skills updated with latest documentation.
  Use this skill when you need to: set up personalized development skills, generate skills for new
  tech stacks, optimize existing skills, or analyze usage patterns.
version: "1.0.2"
author: "SkillForge Team"
allowed-tools:
  - bash_tool
  - view
  - create_file
  - str_replace
  - web_search
  - web_fetch
  - mcp__context7__resolve-library-id
  - mcp__context7__get-library-docs
  - mcp__sequential-thinking__sequentialthinking
---

# 🔨 SkillForge - Meta-Programming Framework

**Transform Claude Code into an Expert Team Member for YOUR Stack**

---

## 🎯 Core Identity

### What SkillForge IS

SkillForge is a **meta-programming framework** that generates, orchestrates, and optimizes Claude Code skills automatically. It's NOT just another skill - it's a **skill factory and orchestrator** that creates personalized development environments.

**Core Purpose**: Make Claude Code an expert in YOUR tech stack, following YOUR conventions, learning YOUR patterns.

### What SkillForge is NOT

- ❌ Not a static skill with fixed knowledge
- ❌ Not a replacement for Claude's core capabilities
- ❌ Not a one-size-fits-all solution
- ❌ Not just a template generator

### The Four Pillars

1. **GENERATION** - Creates personalized skills for your tech stack
2. **ORCHESTRATION** - Intelligently loads the right skills at the right time
3. **LEARNING** - Detects patterns and improves skills over time
4. **OPTIMIZATION** - Keeps skills updated and token-efficient

---

## 📋 Configuration System

SkillForge uses a modular configuration system with specialized behavioral files.
Claude should load these files progressively based on the task at hand.

### Core Configuration Files

These files define SkillForge's behavior and capabilities:

- **@core/SKILLFORGE.md** - Core philosophy, operational modes, skill discovery algorithm, token economics
- **@core/ORCHESTRATION.md** - Intelligent skill loading, dependency resolution, progressive disclosure
- **@core/VISUAL_OUTPUT.md** - **⚡ CRITICAL** - Visual feedback system, user communication, output formatting (ALWAYS follow)
- **@core/GENERATOR.md** - Skill generation pipeline, wizard system, template processing
- **@core/PATTERNS.md** - Pattern learning system, data collection, pattern application
- **@core/RULES.md** - Critical rules, decision trees, quality gates (ALWAYS follow)
- **@core/WORKFLOWS.md** - Common workflows, automation patterns
- **@core/MCP_INTEGRATION.md** - Context7 integration, documentation fetching, caching

**Note**: Core files available and ready to use.

### Available Commands

SkillForge provides slash commands for user interaction:

- `/sf:wizard` - Interactive setup wizard (generates personalized skills)
- `/sf:generate <type>` - Generate specific skill
- `/sf:analyze` - Analyze skills and usage patterns
- `/sf:optimize` - Optimize existing skills
- `/sf:update` - Update skills with latest documentation
- `/sf:introspect` - Analyze current project and suggest skills
- `/sf:list` - List installed SkillForge skills
- `/sf:status` - Show SkillForge installation status
- `/sf:config` - View/edit configuration
- `/sf:reset` - Reset SkillForge to defaults

**Note**: Command implementations in `commands/sf/*.md` (Phase 6)

---

## 🧠 How Claude Should Use SkillForge

### Operational Flow

```
User Request → Intent Analysis → Skill Discovery → Skill Loading → Task Execution → Usage Tracking
```

**IMPORTANT**: Follow **@core/VISUAL_OUTPUT.md** for ALL user communication during orchestration.
Every orchestration step MUST have visible feedback so users know SkillForge is active.

### When to Activate SkillForge

Activate SkillForge when the user:

1. **First Time Setup**
   - Mentions "setup", "configure", "initialize"
   - Asks about personalization or customization
   - → Run `/sf:wizard` workflow

2. **Skill Generation**
   - Mentions specific frameworks/libraries
   - Needs skills for new tech stack
   - → Check if skill exists, generate if needed

3. **Skill Management**
   - Asks to update, optimize, or analyze skills
   - Mentions outdated documentation
   - → Run appropriate `/sf:*` command

4. **Development Tasks**
   - Any coding task (build feature, fix bug, refactor)
   - → Automatically orchestrate relevant skills

### Progressive Disclosure Strategy

**DO NOT** load all SkillForge configuration at once. Use progressive disclosure:

**Level 1 - Always Loaded** (This file only)
- Core identity
- Available commands
- When to use SkillForge

**Level 2 - Load for Setup** (First run / configuration)
- @core/GENERATOR.md
- @core/MCP_INTEGRATION.md
- Wizard command

**Level 3 - Load for Orchestration** (During development tasks)
- @core/ORCHESTRATION.md
- @core/RULES.md
- Generated user skills

**Level 4 - Load for Analysis** (Optimization/learning tasks)
- @core/PATTERNS.md
- @core/WORKFLOWS.md
- Usage analytics

**Token Budget**: Aim for <5000 tokens for skill context, prioritize based on task relevance.

---

## 🎓 Pattern Learning System

SkillForge learns from your development patterns to improve skills over time.

### What is Tracked

**Code Patterns**:
- Naming conventions (files, functions, variables)
- Import preferences
- Error handling style
- Testing approaches

**Workflow Patterns**:
- Commit message format
- Branch naming conventions
- PR description structure
- Review checklists

**Tech Preferences**:
- Preferred libraries (e.g., always use Zod for validation)
- Avoided libraries
- Configuration patterns

**Architecture Patterns**:
- File organization
- Component structure
- Separation of concerns

### How Learning Works

1. **Data Collection** (Background)
   - Track skill usage and outcomes
   - Record user modifications to generated code
   - Identify repeated patterns

2. **Pattern Detection** (After 10+ uses)
   - Analyze usage data
   - Calculate confidence scores
   - Identify statistically significant patterns

3. **Pattern Application** (Confidence > 0.8)
   - Update affected skills
   - Notify user of improvements
   - Allow opt-out

4. **Continuous Improvement**
   - Reinforce successful patterns
   - Decay unused patterns
   - Adapt to changing preferences

### Privacy & Control

- ✅ All data stored locally (`~/.claude/skills/skillforge/data/`)
- ✅ User can view all tracked data
- ✅ User can disable learning (in user_profile.json)
- ✅ User can reject specific patterns
- ✅ User can delete all data (`/sf:reset`)

---

## ⚠️ Critical Behaviors

### DO's - Essential Practices

✅ **ALWAYS fetch latest documentation via Context7** before generating skills
✅ **ALWAYS validate user_profile.json exists** before generating skills
✅ **ALWAYS validate generated SKILL.md** has valid YAML frontmatter
✅ **ALWAYS use absolute paths** (never relative paths)
✅ **ALWAYS check skill already exists** before generating
✅ **ALWAYS ask user confirmation** for destructive actions
✅ **ALWAYS track usage** when skills are used (if learning enabled)
✅ **ALWAYS apply user conventions** when generating code
✅ **THINK before generating** - analyze user needs, don't just template

### DON'Ts - Never Do These

❌ **NEVER generate skills without user profile** - run wizard first
❌ **NEVER modify user data without permission** - always ask
❌ **NEVER use outdated documentation** - fetch latest or use cached
❌ **NEVER expose sensitive data in skills** - sanitize paths, credentials
❌ **NEVER create generic skills** - personalize for user's stack
❌ **NEVER skip validation** - always validate YAML and structure
❌ **NEVER overwhelm token budget** - use progressive disclosure
❌ **NEVER apply patterns with confidence < 0.8** - too risky

### Quality Standards for Generated Skills

Every generated skill MUST have:
- ✅ Valid YAML frontmatter
- ✅ Clear, specific description (not generic)
- ✅ Complete code examples (no placeholders)
- ✅ User conventions integrated
- ✅ Latest best practices from docs
- ✅ Error handling patterns
- ✅ Related skills references

Every generated skill MUST NOT have:
- ❌ Generic placeholder text
- ❌ Outdated patterns or deprecated APIs
- ❌ Missing sections
- ❌ Incomplete code examples
- ❌ Hardcoded paths or credentials

---

## 🔄 Automatic Orchestration Example

**User Request**: "Create a Next.js login component with Supabase authentication"

**SkillForge Orchestration Flow**:

```
1. Intent Analysis
   - Entities: ["Next.js", "login component", "Supabase", "authentication"]
   - Action: "create"
   - Domain: "fullstack"
   - Complexity: "moderate"

2. Skill Discovery
   - Check if "nextjs-fullstack" skill exists
   - Check if "supabase-integration" skill exists
   - Check if "auth-patterns" skill exists
   - If missing → suggest generation via /sf:wizard

3. Skill Loading (Progressive)
   - Load nextjs-fullstack skill (user's Next.js conventions)
   - Load supabase-integration skill (Supabase patterns)
   - Load user conventions from user_profile.json

4. Task Execution
   - Generate login component following user's:
     * File naming conventions
     * Component structure patterns
     * Import preferences
     * Error handling style
   - Use latest Next.js 15 + Supabase patterns from fetched docs

5. Usage Tracking
   - Record: nextjs-fullstack + supabase-integration used together
   - Record: "create auth component" pattern
   - If pattern frequency > 10 → suggest automation
```

**Result**: Perfect code matching user's style, using latest patterns, zero manual adjustments needed.

---

## 🚨 Error Handling & Fallbacks

### Common Scenarios

**Scenario 1: User Profile Not Found**
```
Error: No user profile found
Action: Suggest /sf:wizard to create profile
Fallback: Cannot generate skills without profile
```

**Scenario 2: Context7 API Fails**
```
Error: Cannot fetch documentation from Context7
Action: Check cache for recent docs (< 7 days)
Fallback 1: Use cached docs if available
Fallback 2: Use Claude's built-in knowledge (inform user it may be outdated)
Fallback 3: Suggest user manually provides documentation URL
```

**Scenario 3: Skill Generation Fails**
```
Error: Generated SKILL.md has invalid YAML
Action: Rollback generation, log error
Fallback: Fix YAML and retry once
Ultimate Fallback: Ask user to report bug
```

**Scenario 4: Pattern Detection Low Confidence**
```
Warning: Pattern detected but confidence only 0.65
Action: Do not apply pattern
Info: Show pattern to user, ask if it should be applied manually
```

**Scenario 5: Token Budget Exceeded**
```
Warning: Token budget would exceed 5000
Action: Use minimal skill loading
Fallback: Only load essential sections of skills
Info: Suggest /sf:optimize to reduce skill sizes
```

### Recovery Strategies

1. **Graceful Degradation** - Work with what's available
2. **Transparent Communication** - Tell user what went wrong
3. **Actionable Suggestions** - Tell user how to fix it
4. **Safe Defaults** - Never break user's environment

---

## 📍 Current Status

**Development Phase**: Production Release (v1.0.0)
**Version**: 1.0.0
**Status**: Complete framework available on PyPI, all core systems operational

### ✅ Core Systems (Complete)

✅ Configuration management (`Config` class)
✅ Directory structure and installation system
✅ User profile persistence
✅ Analytics tracking system
✅ Package available on PyPI (`pip install skillforge`)
✅ CLI commands (complete)

### ✅ Generation System (Complete)

✅ Core behavioral files (8 files: SKILLFORGE.md, ORCHESTRATION.md, VISUAL_OUTPUT.md, etc.)
✅ Skill generation wizard (`/sf:wizard`)
✅ Template processing engine
✅ Context7 MCP integration
✅ Documentation fetching and caching

### ✅ Intelligence Systems (Complete)

✅ Intent analysis (action, domain, complexity detection)
✅ Pattern learning and detection
✅ Usage tracking and analytics
✅ Skill discovery and orchestration
✅ Skill optimization system

### ✅ User Interface (Complete)

✅ 10 slash commands (`/sf:wizard`, `/sf:generate`, `/sf:analyze`, etc.)
✅ Visual output system with 3 modes (VERBOSE, COMPACT, SILENT)
✅ Beautiful installation experience
✅ Comprehensive error handling and recovery

---

## 🎯 Decision Tree: When to Use Which Command

```
User mentions setup/configure?
├─ YES → /sf:wizard
└─ NO ↓

User wants to generate specific skill?
├─ YES → /sf:generate <skill-type>
└─ NO ↓

User asks about skill status/analytics?
├─ YES → /sf:analyze or /sf:status
└─ NO ↓

User mentions outdated skills/docs?
├─ YES → /sf:update
└─ NO ↓

User wants to optimize performance?
├─ YES → /sf:optimize
└─ NO ↓

User has coding task?
├─ YES → Automatic orchestration (load relevant skills)
└─ NO → Use Claude Code normally
```

---

## 💡 Pro Tips for Claude

1. **Start Small** - Don't load all configuration at once
2. **Ask First** - When unsure, ask user for clarification
3. **Learn Incrementally** - Build up pattern knowledge over time
4. **Optimize Aggressively** - Token budget is precious
5. **Validate Everything** - Better to catch errors early
6. **Document Assumptions** - Make your reasoning transparent
7. **Empower Users** - Give control, don't make decisions for them

---

## 🔗 Related Resources

- **User Guide**: `docs/QUICKSTART.md` (when available)
- **Architecture**: `docs/ARCHITECTURE.md` (when available)
- **Development**: `docs/skillforge-complete-roadmap.md`
- **Data Location**: `~/.claude/skills/skillforge/data/`
- **Logs**: Check Claude Code terminal for errors

---

## 🚀 Quick Start for Users

**First Time Setup**:
```bash
# 1. Install SkillForge (future - not yet available)
pipx install skillforge

# 2. In Claude Code, run setup wizard
/sf:wizard

# 3. Answer questions about your tech stack (5 minutes)
# 4. SkillForge generates personalized skills
# 5. Restart Claude Code
# 6. Start coding with your intelligent assistant!
```

**Daily Usage**:
```
# Just code normally! SkillForge orchestrates automatically
# When you need new skills:
/sf:generate nextjs-fullstack
/sf:generate supabase-integration

# Weekly maintenance:
/sf:analyze      # Check usage patterns
/sf:optimize     # Optimize skills
/sf:update       # Update documentation
```

---

**🎉 Remember: SkillForge makes Claude Code YOUR expert team member.**

**Every skill is personalized. Every pattern is learned. Every day it gets better.**

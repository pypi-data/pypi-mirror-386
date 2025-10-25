# 🔨 SkillForge - Claude Code Context Briefing

**Last Updated**: 2025-10-22
**Version**: Pre-development (Planning Phase)
**Status**: Ready to start implementation

---

## 🎯 What is SkillForge?

SkillForge is a **meta-programming framework** that transforms Claude Code from a generic AI assistant into an expert team member specialized in YOUR tech stack, following YOUR conventions, and continuously improving from YOUR patterns.

**In one sentence**: SkillForge generates, orchestrates, and optimizes personalized Claude Code skills automatically.

---

## 💡 The Problem

Claude Code has a powerful native skills system (`~/.claude/skills/`) but with critical limitations:

1. **Generic Skills** - Official skills are one-size-fits-all, don't know YOUR stack
2. **No Orchestration** - Claude must guess which skills to use, can waste tokens or miss relevant skills
3. **No Memory** - Each session starts from zero, no learning across sessions
4. **Static** - Skills don't update or improve over time
5. **Manual Creation** - Creating custom skills requires expertise and maintenance

**Result**: Claude Code generates "good enough" code that requires 15-30 minutes of manual adjustments to match your style.

---

## ✨ The Solution

SkillForge has **4 core components**:

### 1. Generator
- Interactive wizard that learns your tech stack
- Fetches latest documentation via Context7 MCP
- Generates personalized SKILL.md files
- Creates templates, scripts, and supporting files
- **Output**: Skills customized for YOUR stack and conventions

### 2. Orchestrator
- Analyzes user requests to identify intent
- Discovers relevant skills intelligently
- Loads skills with token budget optimization
- Coordinates multiple skills for complex tasks
- **Output**: Right skills loaded at right time with optimal token usage

### 3. Learner
- Tracks skill usage patterns (with privacy)
- Detects recurring patterns (code style, workflows, tool preferences)
- Applies high-confidence patterns (>0.8) to skills
- Updates skills automatically based on YOUR behavior
- **Output**: Skills improve over time, reflecting YOUR way of working

### 4. Optimizer
- Analyzes existing skills for redundancies
- Suggests merging overlapping skills
- Updates outdated documentation automatically
- Compresses verbose content without losing meaning
- **Output**: Optimized token usage and up-to-date skills

---

## 🏗️ Architecture

```
~/.claude/skills/skillforge/
│
├── SKILL.md                      # Entry point (meta-skill)
│
├── core/                         # Behavioral files
│   ├── SKILLFORGE.md            # Core configuration
│   ├── ORCHESTRATION.md         # Orchestration logic
│   ├── GENERATOR.md             # Generation system
│   ├── PATTERNS.md              # Pattern learning
│   ├── RULES.md                 # Behavioral rules
│   ├── WORKFLOWS.md             # Automated workflows
│   └── MCP_INTEGRATION.md       # MCP integrations
│
├── commands/sf/                  # Slash commands
│   ├── wizard.md                # /sf:wizard
│   ├── generate.md              # /sf:generate
│   ├── analyze.md               # /sf:analyze
│   ├── optimize.md              # /sf:optimize
│   └── ...
│
├── generators/                   # Python generators
│   ├── wizard_engine.py         # Interactive wizard
│   ├── skill_generator.py       # Skill generator
│   ├── template_processor.py   # Template engine
│   └── doc_fetcher.py           # Context7 integration
│
├── analyzers/                    # Intelligence
│   ├── intent_analyzer.py       # Analyze user requests
│   ├── skill_discovery.py       # Find relevant skills
│   ├── usage_tracker.py         # Track usage
│   ├── pattern_detector.py      # Detect patterns
│   └── skill_optimizer.py       # Optimize skills
│
├── templates/                    # Skill templates
│   ├── base-skill.template
│   ├── tech-stack/
│   │   ├── nextjs-fullstack.template
│   │   ├── react-spa.template
│   │   ├── python-api.template
│   │   └── supabase-integration.template
│   └── workflow/
│       └── git-workflow.template
│
└── data/                         # Persistent data
    ├── user_profile.json        # User setup
    ├── usage_analytics.json     # Usage stats
    ├── learned_patterns.json    # Learned patterns
    └── cache/context7/          # Cached docs
```

---

## 🎯 User Journey

### Setup (Once)
```bash
1. Run /sf:wizard
2. Answer 10-12 questions about tech stack
3. SkillForge generates personalized skills
4. Restart Claude Code
5. Done!
```

### Daily Use (Automatic)
```
You: "Create a login component with Supabase auth"

SkillForge (invisible):
├─ Analyzes intent
├─ Loads nextjs-fullstack + supabase-integration skills
├─ Tracks usage
└─ Claude generates perfect code in YOUR style

Result: 0 modifications needed ✅
```

### After 2 Weeks (Learning)
```
SkillForge detected patterns:
- You always use Zod for validation (92% confidence)
- You prefer feature-based colocation
- You use server actions over API routes

→ Skills automatically updated with YOUR preferences
```

---

## 📊 Current Status

**Phase**: Planning Complete
**Next Step**: Begin implementation

**Documents Available**:
- `skillforge-briefing-completo.md` - Full project briefing (1568 lines)
- `skillforge-complete-roadmap.md` - Complete roadmap (3654 lines)
- `CLAUDE_BRIEFING.md` - This file (for Claude Code context)

**Development Approach Decided**: MVP-first
- Week 1-2: Foundation + Context7 validation
- Week 3-4: Generator + 1 template (Next.js)
- Week 5: Alpha testing (dogfooding)
- Week 6: Commands + Polish
- Week 7-8: Documentation + Release MVP (v0.5)

**Tech Stack**:
- Language: Python 3.11+
- Config: YAML + Markdown
- Storage: JSON
- Integration: MCP (Context7 primary)
- Testing: pytest + pytest-cov

---

## 🚀 Key Commands (When Built)

- `/sf:wizard` - Interactive setup wizard
- `/sf:generate <type>` - Generate specific skill
- `/sf:analyze` - Analyze skills and usage patterns
- `/sf:optimize` - Optimize existing skills
- `/sf:update` - Update skills with latest docs
- `/sf:list` - List installed skills
- `/sf:status` - Show SkillForge status

---

## 💡 Meta-Development Approach

**Critical**: We're using Claude Code to build SkillForge itself!

This means:
- You (Claude Code) are both the developer AND the target user
- Test features as you build them
- Identify real pain points through dogfooding
- Validate that SkillForge solves actual problems

---

## 🎯 Core Philosophy

### 4 Principles

1. **Personalization Over Generalization**
   - YOUR stack, YOUR conventions, YOUR style

2. **Intelligence Over Automation**
   - Smart skill selection, not brute force

3. **Evolution Over Stasis**
   - Skills improve continuously

4. **Efficiency Over Completeness**
   - Progressive disclosure, token optimization

---

## 📝 How to Use This Briefing

**When starting a new conversation about SkillForge**:

1. Read this file first for context
2. Reference `skillforge-briefing-completo.md` for deep details
3. Reference `skillforge-complete-roadmap.md` for implementation steps
4. Ask user which phase/component to work on
5. Execute with full context

**When user says "continue SkillForge work"**:

1. Check current status in this file
2. Review last completed phase
3. Identify next steps from roadmap
4. Proceed with implementation

**When user mentions "the meta-framework"**:

- They mean SkillForge
- Read this briefing for context
- Continue with current work

---

## ⚠️ Critical Dependencies

### Must Validate Early
- **Context7 MCP**: Core for documentation fetching (validate Week 1!)
- **SKILL.md Format**: Claude Code must load generated skills (test ASAP!)
- **Template Quality**: Generated code must be production-ready

### Fallbacks Required
- If Context7 fails → Use web_search
- If web_search fails → Use cached/builtin docs
- Always inform user of documentation source

---

## 🎨 Example: Before vs After

### Before SkillForge
```typescript
// Generic Next.js component
// May use Pages Router (outdated)
// May not follow your conventions
// Requires 15-30 min adjustments
export default function LoginForm() {
  // Generic implementation
}
```

### After SkillForge
```typescript
// YOUR Next.js component
// App Router (latest)
// YOUR naming conventions
// YOUR folder structure
// YOUR preferred libraries
// 0 modifications needed ✅
'use client'

import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/lib/store/auth'
// ... perfect code following YOUR patterns
```

---

## 📚 Quick Reference

**Project Root**: `/Users/omarpioselli/SkillForge/`

**Key Files**:
- This file: Context briefing
- `skillforge-briefing-completo.md`: Full details
- `skillforge-complete-roadmap.md`: Implementation plan

**Development Environment**: Not yet set up (Week 1 task)

**Current Focus**: Ready to begin Fase 0 (Setup)

---

## 🔄 Update Protocol

**When to update this file**:
- Major milestone completed (update Status section)
- Architecture decisions changed (update Architecture section)
- New phase started (update Current Focus)
- Critical learnings discovered (add to relevant section)

**Format**: Keep concise, focus on "what Claude Code needs to know quickly"

---

## 🎯 Success Criteria

SkillForge succeeds when:

✅ Setup takes < 10 minutes
✅ Generated skills work in Claude Code without modifications
✅ Generated code matches user's style perfectly
✅ Skills improve automatically over time
✅ Token usage is optimized
✅ Users prefer SkillForge-assisted development over vanilla Claude Code

---

**Remember**: SkillForge isn't just a tool - it's about making YOU (Claude Code) a better development partner by deeply understanding each user's unique way of working.

Let's build it! 🚀

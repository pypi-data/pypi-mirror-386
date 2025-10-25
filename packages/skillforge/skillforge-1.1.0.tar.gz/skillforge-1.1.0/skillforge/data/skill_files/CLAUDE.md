# SkillForge - Meta-Programming Framework for Claude Code

## What is SkillForge

SkillForge is a meta-programming framework that transforms Claude Code into an expert developer personalized for the user's tech stack, conventions, and preferences.

**YOU ARE**: Claude Code + SkillForge Framework + User's Personalized Skills

## ⚡ When to Activate SkillForge

SkillForge should **ONLY** be activated when the user needs technical/development assistance.

### ✅ ACTIVATE SkillForge For:

1. **Coding Requests**:
   - "Create a Next.js component"
   - "Fix this bug in my code"
   - "Refactor this function"
   - "Write a test for..."
   - "Build a feature that..."

2. **Technical Questions**:
   - "How do I use Supabase with Next.js?"
   - "What's the best way to handle auth?"
   - "Explain this code pattern"
   - "Review my architecture"

3. **Project Setup/Analysis**:
   - "Set up a new React project"
   - "Analyze my codebase"
   - "Suggest improvements"
   - "Add TypeScript to my project"

4. **Skill Management Commands**:
   - `/sf:wizard`
   - `/sf:generate`
   - `/sf:list`
   - `/sf:status`
   - `/sf:analyze`
   - Any command starting with `/sf:`

### ❌ DO NOT Activate SkillForge For:

1. **General Conversation**:
   - "Hello", "Hi", "How are you?"
   - "What's the weather?"
   - "Tell me a joke"
   - General chitchat

2. **Non-Technical Questions**:
   - "What is AI?"
   - "Explain quantum physics"
   - "Write me a poem"
   - "What's your favorite color?"

3. **Documentation Reading** (unless code-related):
   - "Summarize this article"
   - "What does this blog post say?"
   - "Explain this concept" (non-coding)

### 🤔 Decision Tree

```
User Request
     ↓
Is it related to:
  - Writing code?
  - Fixing code?
  - Tech stack?
  - Project setup?
  - /sf:* command?
     ↓
    YES → ✅ Activate SkillForge
     ↓
    NO → ❌ Respond normally (don't load SkillForge)
```

## 🎯 Activation Protocol (When Triggered)

When SkillForge activation conditions are met:

### Step 1: Check User Profile
```
Read: ~/.claude/skillforge/data/user_profile.json

If not found:
  → Suggest: "Would you like to set up SkillForge? Run /sf:wizard"
  → Continue without SkillForge (use generic knowledge)

If found:
  → Load user preferences into context
  → Proceed to Step 2
```

### Step 2: Intent Analysis
```
Analyze user request:
  - Entities: [frameworks, libraries, features mentioned]
  - Action: [create, fix, refactor, test, deploy, etc.]
  - Domain: [frontend, backend, fullstack, devops, testing]
  - Complexity: [simple, moderate, complex]
```

### Step 3: Skill Discovery
```
Scan: ~/.claude/skills/
Match skills based on:
  - Entities in request
  - User's tech stack
  - Domain relevance

Rank by confidence score (0-1)
Select top 2-3 relevant skills
```

### Step 4: Progressive Loading
```
Load only what's needed:

Level 1 - Profile + Intent:
  - user_profile.json (~1KB)
  - Intent analysis result

Level 2 - Orchestration (if needed):
  @include ~/.claude/skillforge/core/ORCHESTRATION.md
  @include ~/.claude/skillforge/core/RULES.md

Level 3 - Relevant Skills:
  @include ~/.claude/skills/{skill-1}/SKILL.md
  @include ~/.claude/skills/{skill-2}/SKILL.md
  (max 2-3 skills per request)

Token Budget: Maximum 5000 tokens for SkillForge context
```

### Step 5: Contextualized Execution
```
Apply from user profile:
  - Code style preferences
  - Naming conventions
  - Tech stack patterns
  - Preferred libraries

Use patterns from loaded skills:
  - Framework-specific best practices
  - User's custom patterns
  - Latest documentation (from Context7)

Generate personalized code
Track usage (if learning enabled)
```

## 📋 Framework Structure

```
~/.claude/
  ├── CLAUDE.md (this file)          # Entry point
  │
  ├── skillforge/                     # Framework
  │   ├── SKILLFORGE.md               # Overview
  │   ├── core/                       # Behavioral files
  │   │   ├── ORCHESTRATION.md
  │   │   ├── RULES.md
  │   │   ├── GENERATOR.md
  │   │   ├── PATTERNS.md
  │   │   ├── VISUAL_OUTPUT.md
  │   │   ├── MCP_INTEGRATION.md
  │   │   └── WORKFLOWS.md
  │   ├── data/                       # User data
  │   │   ├── user_profile.json
  │   │   ├── usage_analytics.json
  │   │   └── cache/
  │   └── templates/                  # Generation templates
  │
  ├── commands/                       # Slash commands
  │   └── sf/
  │       ├── wizard.md
  │       ├── generate.md
  │       └── ...
  │
  └── skills/                         # User-generated skills
      ├── nextjs-fullstack/
      ├── supabase-integration/
      └── ...
```

## 🚀 Available Commands

Execute via SlashCommand tool when user requests:

- `/sf:wizard` - Interactive setup wizard (first time users)
- `/sf:generate <skill>` - Generate specific skill
- `/sf:list` - List all generated skills
- `/sf:status` - Check SkillForge configuration
- `/sf:analyze` - Analyze usage patterns and suggest improvements
- `/sf:optimize` - Optimize skills (reduce token usage)
- `/sf:update <skill>` - Update skill with latest documentation
- `/sf:config` - View/edit SkillForge configuration
- `/sf:reset` - Reset SkillForge to defaults
- `/sf:introspect` - Analyze current project and suggest skills

## ⚠️ Critical Rules (When Active)

### Orchestration Rules
🚨 **NEVER** start coding without checking user profile
🚨 **NEVER** skip intent analysis and skill discovery
🚨 **ALWAYS** load relevant skills before generating code
🚨 **ALWAYS** apply user conventions from profile

### Skill Generation Rules
🚨 **NEVER** generate skills without user profile
🚨 **NEVER** use outdated documentation (fetch latest via Context7)
🚨 **ALWAYS** validate YAML frontmatter in generated skills
🚨 **ALWAYS** personalize skills with user preferences

### Learning Rules
🚨 **ALWAYS** track usage when skills are used (if enabled)
🚨 **NEVER** apply patterns with confidence < 0.8
🚨 **ALWAYS** ask permission before modifying user data

### Token Management Rules
🚨 **NEVER** load all skills at once
🚨 **ALWAYS** use progressive disclosure
🚨 **NEVER** exceed 5000 token budget for framework context

## 🔗 Reference Files (Load When Needed)

**Core Framework**:
- @include ~/.claude/skillforge/SKILLFORGE.md
- @include ~/.claude/skillforge/core/ORCHESTRATION.md
- @include ~/.claude/skillforge/core/RULES.md

**Setup Mode** (when user runs /sf:wizard):
- @include ~/.claude/skillforge/core/GENERATOR.md
- @include ~/.claude/skillforge/core/MCP_INTEGRATION.md
- @include ~/.claude/commands/sf/wizard.md

**Analysis Mode** (when user runs /sf:analyze):
- @include ~/.claude/skillforge/core/PATTERNS.md
- @include ~/.claude/skillforge/core/WORKFLOWS.md

## 🎓 Examples

### Example 1: Coding Request (✅ Activate)
```
User: "Create a Next.js login page with Supabase auth"

Claude:
1. ✅ Recognizes: coding request
2. ✅ Activates SkillForge
3. ✅ Loads: user_profile.json
4. ✅ Discovers: nextjs-fullstack, supabase-integration skills
5. ✅ Loads: both skills
6. ✅ Generates: personalized code matching user's conventions
```

### Example 2: General Chat (❌ Don't Activate)
```
User: "Hi Claude, how are you today?"

Claude:
1. ✅ Recognizes: general conversation
2. ❌ Does NOT activate SkillForge
3. ✅ Responds: normally without loading any framework files
4. Result: Fast response, no unnecessary overhead
```

### Example 3: Tech Question (✅ Activate)
```
User: "What's the best way to handle authentication in Next.js?"

Claude:
1. ✅ Recognizes: technical question about user's stack
2. ✅ Activates SkillForge
3. ✅ Loads: user_profile.json (sees Next.js in stack)
4. ✅ Discovers: nextjs-fullstack skill
5. ✅ Answers: using patterns from user's skill + profile
```

### Example 4: Command (✅ Activate)
```
User: "/sf:list"

Claude:
1. ✅ Recognizes: SkillForge command
2. ✅ Activates SkillForge
3. ✅ Executes: command implementation
4. ✅ Shows: all user's generated skills
```

## 💡 Success Indicators

You're using SkillForge correctly when:
- ✅ You mention checking user profile before coding
- ✅ You reference loaded skills by name
- ✅ Generated code matches user's exact conventions
- ✅ You DON'T load SkillForge for general chat
- ✅ Response is fast for non-technical queries

## 🔄 Error Handling

### Profile Not Found
```
I notice you don't have a SkillForge profile yet.

SkillForge can help me become an expert in YOUR specific tech stack
by generating personalized skills based on your preferences.

Would you like to set it up? (takes 3-5 minutes)
→ /sf:wizard

Or I can help you without SkillForge using my general knowledge.
```

### No Relevant Skills
```
I found your profile but no skills match this request.

Would you like me to generate a skill for [detected tech]?
→ /sf:generate [skill-name]

Or I can help you using my general knowledge for now.
```

## 🎯 Remember

**SkillForge is a power-up, not a requirement.**

- For coding: SkillForge makes you an expert in user's stack
- For chat: You're already great at conversation
- For questions: Use SkillForge only if tech-related

**Activate intelligently. Respond quickly. Stay efficient.**

---

**Version**: 1.1.0
**Framework**: SkillForge Meta-Programming System
**Installation**: `pip install skillforge && skillforge install`

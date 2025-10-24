# ⚡ SkillForge Quick Start Guide

**Get started with SkillForge in 10 minutes**

This guide will walk you through installing SkillForge, running the setup wizard, and generating your first personalized skill.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Your First Skill](#your-first-skill)
- [Using Skills](#using-skills)
- [Next Steps](#next-steps)

---

## Prerequisites

Before installing SkillForge, ensure you have:

- ✅ **Python 3.11+** installed ([Download Python](https://www.python.org/downloads/))
- ✅ **Claude Code** installed ([Get Claude Code](https://docs.claude.com/en/docs/claude-code))
- ✅ **pipx** (recommended) or pip installed

Verify your setup:

```bash
# Check Python version
python3 --version
# Should show: Python 3.11.x or higher

# Check Claude Code
claude --version
```

---

## Installation

### Step 1: Install SkillForge Package

**Option A: Using pipx (Recommended)**
```bash
pipx install skillforge
```

**Option B: Using pip**
```bash
pip install --user skillforge
```

### Step 2: Verify Installation

```bash
# Check SkillForge CLI is available
skillforge --version

# Should output: SkillForge v1.0.0 (or similar)
```

### Step 3: Initialize SkillForge

```bash
# Initialize SkillForge directory structure
skillforge install
```

This creates:
- `~/.claude/skills/skillforge/` - Main SkillForge directory
- `~/.claude/skills/skillforge/data/` - Your preferences and analytics
- `~/.claude/skills/skillforge/core/` - Core behavioral files

**Output:**
```
🔨 SkillForge Installer
=======================

✅ Creating directory structure...
   ~/.claude/skills/skillforge/

✅ Installing core files...
   ├─ SKILL.md
   ├─ core/
   └─ data/

✅ Installation complete!

Next step: Run /sf:wizard in Claude Code
```

---

## First-Time Setup

### Step 1: Open Claude Code in Your Main Project

Navigate to your most representative project (one that uses your typical tech stack):

```bash
cd ~/projects/my-main-project
claude
```

**Why?** The wizard will auto-detect technologies from this project and use them as defaults.

### Step 2: Run the Setup Wizard

In Claude Code, execute:

```
> /sf:wizard
```

### Step 3: Follow the Wizard

The wizard will guide you through 3 main phases:

#### Phase 1: Tech Stack Detection

```
╔════════════════════════════════════════════════╗
║  🧙 SkillForge Setup Wizard                    ║
║  Building YOUR personal development profile    ║
╚════════════════════════════════════════════════╝

🔍 Auto-detecting from current directory...
   /Users/you/projects/my-nextjs-app

✅ Detected:
   ├─ Next.js 15.0.0 (package.json)
   ├─ TypeScript 5.3 (tsconfig.json)
   ├─ Tailwind CSS (tailwind.config.js)
   ├─ Supabase (package.json dependencies)
   └─ Vitest (package.json devDependencies)

Use these as defaults? [Y/n]
```

**Tip:** Type `Y` to accept detected technologies. The wizard will still ask about your preferences.

#### Phase 2: Personal Preferences (8-10 questions)

The wizard asks about YOUR coding style:

**1. Variable Naming Convention**
```
How do you name variables?
  [1] camelCase (recommended for JS/TS)
  [2] snake_case (common in Python)
  [3] PascalCase (for classes/components only)
> 1
```

**2. Import Style**
```
What's your preferred import style?
  [1] Absolute imports with alias (@/components/...)
  [2] Relative imports (../../components/...)
  [3] Mix of both
> 1
```

**3. Component Import Alias**
```
If using aliases, what's your preferred prefix?
  [1] @/ (e.g., @/components/Button)
  [2] ~/ (e.g., ~/components/Button)
  [3] #/ (e.g., #/components/Button)
> 1
```

**4. State Management** (Frontend only)
```
What's your preferred state management solution?
  [1] Zustand (lightweight, recommended)
  [2] Redux Toolkit (complex apps)
  [3] Context API (simple apps)
  [4] Jotai (atomic state)
> 1
```

**5. Data Fetching** (Frontend only)
```
How do you fetch data?
  [1] React Query / TanStack Query (recommended)
  [2] SWR
  [3] Native fetch with useState
  [4] Server Components only (Next.js)
> 1
```

**6. Validation Library**
```
What's your preferred validation library?
  [1] Zod (TypeScript-first, recommended)
  [2] Yup (schema validation)
  [3] Joi (Node.js focused)
  [4] None / manual validation
> 1
```

**7. Testing Framework**
```
What testing framework do you use?
  [1] Vitest (modern, fast, recommended)
  [2] Jest (popular, established)
  [3] None / minimal testing
> 1
```

**8. Folder Structure**
```
How do you organize your code?
  [1] Feature-based (group by feature/domain)
  [2] Type-based (components/, utils/, hooks/)
  [3] Hybrid (mix of both)
> 1

Example feature-based structure:
  src/
  ├─ features/
  │  ├─ auth/
  │  │  ├─ components/
  │  │  ├─ hooks/
  │  │  └─ api/
  │  └─ dashboard/
  └─ shared/
```

**9. Git Commit Style**
```
What commit message format do you follow?
  [1] Conventional Commits (feat:, fix:, docs:)
  [2] Semantic (Add, Fix, Update, Remove)
  [3] Free-form / no convention
> 1
```

**10. Error Handling**
```
How do you handle errors?
  [1] try/catch with custom error classes
  [2] try/catch with standard errors
  [3] Error boundaries (React)
  [4] Result types (Result<T, Error>)
> 1
```

#### Phase 3: Skill Generation

After answering all questions:

```
╔════════════════════════════════════════════════╗
║  📝 Summary of Your Profile                    ║
╚════════════════════════════════════════════════╝

Tech Stack:
  Frontend: Next.js 15.0.0
  UI: Tailwind CSS
  State: Zustand
  Backend: Next.js API Routes
  Database: Supabase
  Testing: Vitest

Conventions:
  Naming: camelCase
  Imports: Absolute with @/
  Structure: Feature-based
  Commits: Conventional Commits
  Validation: Zod

Looks good? [Y/n]
```

Type `Y` to proceed:

```
╔════════════════════════════════════════════════╗
║  ⚙️ Generating Skills...                       ║
╚════════════════════════════════════════════════╝

[1/3] 📦 Fetching Next.js 15 documentation...
      └─ ✅ Fetched 2,341 lines (Context7 MCP)

[2/3] 🔨 Generating nextjs-fullstack skill...
      ├─ Loading template
      ├─ Injecting YOUR conventions
      ├─ Creating SKILL.md (2,534 lines)
      ├─ Adding code examples
      └─ ✅ Skill generated

[3/3] 🔨 Generating supabase-integration skill...
      ├─ Fetching Supabase docs...
      ├─ Creating SKILL.md (1,823 lines)
      └─ ✅ Skill generated

╔════════════════════════════════════════════════╗
║  ✅ Setup Complete!                            ║
╚════════════════════════════════════════════════╝

Skills installed in ~/.claude/skills/:
  ├─ nextjs-fullstack/
  │  └─ SKILL.md (2,534 lines)
  ├─ supabase-integration/
  │  └─ SKILL.md (1,823 lines)
  └─ git-workflow/
     └─ SKILL.md (634 lines)

Your profile saved to:
  ~/.claude/skills/skillforge/data/user_profile.json

🎉 SkillForge is ready!

Next steps:
  1. Restart Claude Code (for skills to load)
  2. Try: "Create a login component with Supabase auth"
  3. Watch SkillForge work its magic!
```

---

## Your First Skill

### Restart Claude Code

After wizard completion, restart Claude Code to load the new skills:

```bash
# Exit Claude Code
Ctrl+D or type "exit"

# Restart
cd ~/projects/my-main-project
claude
```

### Test Your Skills

Try a task that uses your new skills:

**Example 1: Create a Component**
```
You: Create a login component with Supabase authentication

[SkillForge automatically:]
├─ Detects: "login", "component", "Supabase", "authentication"
├─ Loads: nextjs-fullstack + supabase-integration skills
├─ Injects: YOUR conventions
└─ Claude generates: Perfect code

Result: Login component with:
├─ Next.js 15 App Router structure
├─ Shadcn/ui form components
├─ Zustand for auth state
├─ Zod validation schema
├─ Supabase auth integration
├─ @/ import aliases
├─ Feature-based location: src/features/auth/components/LoginForm.tsx
└─ Error boundary wrapper
```

**Example 2: Create an API Route**
```
You: Create an API route to fetch user profile from Supabase

Result: API route with:
├─ app/api/profile/route.ts (Next.js 15)
├─ Supabase client initialization
├─ Type-safe response with Zod
├─ Error handling with try/catch
└─ Proper HTTP status codes
```

**Example 3: Full Feature**
```
You: Create a dashboard with user stats, charts, and data table

Result: Complete feature with:
├─ src/features/dashboard/
│  ├─ components/
│  │  ├─ DashboardLayout.tsx
│  │  ├─ StatsCards.tsx
│  │  ├─ Charts.tsx
│  │  └─ DataTable.tsx
│  ├─ hooks/
│  │  └─ useDashboardData.ts
│  └─ api/
│     └─ getDashboardStats.ts
├─ Proper imports with @/
├─ Zustand store for state
├─ React Query for data fetching
└─ Responsive Tailwind styling
```

---

## Using Skills

### Automatic Orchestration

SkillForge works invisibly. Just make requests naturally:

```
✅ "Create a signup form"
✅ "Add authentication middleware"
✅ "Create a dashboard page"
✅ "Fix the login error handling"
✅ "Add tests for the auth flow"
```

SkillForge automatically:
1. Analyzes your intent
2. Identifies relevant skills
3. Loads them with token optimization
4. Tracks usage for learning

### Manual Skill Generation

Generate additional skills as needed:

```bash
# Generate a specific skill
> /sf:generate vue-spa

# Generate from current project detection
> /sf:generate --from-current

# Generate with documentation update
> /sf:generate nextjs-fullstack --fetch-docs

# Generate with preview (don't save)
> /sf:generate python-fastapi --preview
```

### View Installed Skills

```bash
# List all skills
> /sf:list

Output:
┌────────────────────────────────────────────────────┐
│  📚 Installed Skills (3)                           │
├────────────────────────────────────────────────────┤
│                                                    │
│  nextjs-fullstack                                  │
│  ├─ Type: Frontend Framework                      │
│  ├─ Size: 2,534 lines (~3,200 tokens)            │
│  ├─ Uses: 47 times (94% success)                 │
│  └─ Updated: 2 days ago                           │
│                                                    │
│  supabase-integration                              │
│  ├─ Type: Backend Integration                     │
│  ├─ Size: 1,823 lines (~2,300 tokens)            │
│  ├─ Uses: 23 times (96% success)                 │
│  └─ Updated: 2 days ago                           │
│                                                    │
│  git-workflow                                      │
│  ├─ Type: Workflow                                │
│  ├─ Size: 634 lines (~800 tokens)                │
│  ├─ Uses: 12 times (100% success)                │
│  └─ Updated: 2 days ago                           │
│                                                    │
│  Total Token Budget: ~6,300 tokens                │
└────────────────────────────────────────────────────┘
```

---

## Next Steps

### 1. Generate More Skills

As you work on different projects:

```bash
# Vue.js project
> /sf:generate vue-spa

# Python backend
> /sf:generate python-fastapi

# Testing
> /sf:generate testing-vitest
```

### 2. Let SkillForge Learn

Use Claude Code naturally for 1-2 weeks. SkillForge will:
- Track your patterns
- Detect recurring preferences
- Auto-update skills (with 80%+ confidence)

### 3. Analyze & Optimize

After ~50 uses:

```bash
# View analytics
> /sf:analyze

# See learned patterns
> /sf:analyze --patterns

# Optimize skills
> /sf:optimize
```

### 4. Keep Skills Updated

```bash
# Update specific skill
> /sf:update nextjs-fullstack

# Update all skills
> /sf:update --all

# Check for updates
> /sf:update --check
```

---

## Common First-Time Issues

### Issue 1: "skillforge: command not found"

**Solution:**
```bash
# Ensure pipx bin directory is in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or reinstall with pip
pip install --user skillforge
```

### Issue 2: Claude Code doesn't load skills

**Solution:**
```bash
# Verify skills are installed
ls ~/.claude/skills/

# Should see:
# skillforge/
# nextjs-fullstack/
# supabase-integration/
# git-workflow/

# Restart Claude Code completely
killall claude
claude
```

### Issue 3: Wizard fails during documentation fetch

**Solution:**
```bash
# Generate without fetching docs (uses built-in knowledge)
> /sf:generate nextjs-fullstack --no-docs

# Or check Context7 MCP is installed
claude --list-mcps
# Should see: context7
```

### Issue 4: Generated code doesn't match my conventions

**Solution:**
```bash
# Re-run wizard to update preferences
> /sf:wizard --update

# Or manually edit profile
code ~/.claude/skills/skillforge/data/user_profile.json

# Then regenerate skills
> /sf:generate nextjs-fullstack --force
```

---

## Quick Reference

### Essential Commands

| Command | Purpose |
|---------|---------|
| `/sf:wizard` | Run setup wizard |
| `/sf:generate <skill>` | Generate specific skill |
| `/sf:list` | List installed skills |
| `/sf:status` | View SkillForge status |
| `/sf:analyze` | Analyze usage & patterns |
| `/sf:optimize` | Optimize skills |
| `/sf:update --all` | Update all skills |

### File Locations

| Path | Contains |
|------|----------|
| `~/.claude/skills/skillforge/` | Main SkillForge directory |
| `~/.claude/skills/skillforge/data/user_profile.json` | Your preferences |
| `~/.claude/skills/<skill-name>/` | Generated skills |

### Need More Help?

- 📖 [Full Documentation](../README.md)
- 🏗️ [Architecture Guide](ARCHITECTURE.md)
- 📋 [Commands Reference](COMMANDS.md)
- ❓ [FAQ](FAQ.md)
- 🔧 [Troubleshooting](TROUBLESHOOTING.md)
- 🐛 [Report Issues](https://github.com/omarpiosedev/SkillForge/issues)

---

## What's Next?

You're ready to use SkillForge! Here's what happens now:

1. **Use Claude Code naturally** - SkillForge orchestrates skills automatically
2. **SkillForge learns** - After 10-20 uses, patterns emerge
3. **Skills improve** - Auto-updates when patterns reach 80%+ confidence
4. **You save time** - Less manual editing, more consistent code

**Welcome to personalized AI pair programming! 🚀**

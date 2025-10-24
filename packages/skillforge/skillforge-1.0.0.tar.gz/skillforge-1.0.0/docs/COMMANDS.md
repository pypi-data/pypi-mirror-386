# 📋 SkillForge Commands Reference

**Complete reference for all SkillForge slash commands**

This document provides detailed documentation for every SkillForge command available in Claude Code.

---

## 📑 Table of Contents

- [Quick Reference](#quick-reference)
- [Core Commands](#core-commands)
  - [/sf:wizard](#sfwizard)
  - [/sf:generate](#sfgenerate)
  - [/sf:list](#sflist)
  - [/sf:status](#sfstatus)
- [Analysis & Optimization](#analysis--optimization)
  - [/sf:analyze](#sfanalyze)
  - [/sf:optimize](#sfoptimize)
  - [/sf:update](#sfupdate)
- [Configuration & Debug](#configuration--debug)
  - [/sf:config](#sfconfig)
  - [/sf:introspect](#sfintrospect)
  - [/sf:reset](#sfreset)

---

## Quick Reference

| Command | Purpose | Frequency |
|---------|---------|-----------|
| `/sf:wizard` | Interactive setup wizard | Once / per tech stack |
| `/sf:generate <skill>` | Generate specific skill | As needed |
| `/sf:list` | List all skills | Anytime |
| `/sf:status` | View SkillForge status | Anytime |
| `/sf:analyze` | Analyze usage & patterns | Weekly |
| `/sf:optimize` | Optimize skills | Monthly |
| `/sf:update <skill>` | Update skill docs | As needed |
| `/sf:config` | Configure settings | Rarely |
| `/sf:introspect` | Debug decisions | When troubleshooting |
| `/sf:reset` | Reset data | Rarely |

---

## Core Commands

### /sf:wizard

**Interactive skill generation wizard**

#### Purpose
Launch the interactive wizard that guides you through setting up SkillForge for the first time or adding a new tech stack. The wizard auto-detects your technologies and asks about your personal coding preferences.

#### When to Use
- ✅ First time setup
- ✅ Adding new tech stack (Vue, Python, etc.)
- ✅ Onboarding new project
- ✅ Updating preferences

#### Syntax
```
/sf:wizard [--update]
```

#### Options
- `--update` - Update existing profile instead of creating new one

#### Process

**Step 1: Auto-Detection**
```
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

**Step 2: Questionnaire (10-12 questions)**
- Role (Frontend, Backend, Fullstack, etc.)
- Frontend Framework
- UI Library
- State Management
- Backend Framework
- Database
- Auth Provider
- Testing Tools
- Code Style Preferences
- Workflow Preferences

**Step 3: Profile Generation**
```
╔════════════════════════════════════════════════╗
║  📝 Summary of Your Profile                    ║
╚════════════════════════════════════════════════╝

Tech Stack:
  Frontend: Next.js 15.0.0
  UI: Tailwind CSS + shadcn/ui
  State: Zustand
  Backend: Next.js API Routes
  Database: Supabase

Conventions:
  Naming: camelCase
  Imports: Absolute with @/
  Structure: Feature-based
  Commits: Conventional Commits

Looks good? [Y/n]
```

**Step 4: Skill Generation**
```
[1/3] 📦 Fetching Next.js documentation...
      └─ ✅ Fetched (Context7 MCP)

[2/3] 🔨 Generating nextjs-fullstack skill...
      └─ ✅ Skill generated (2,534 lines)

[3/3] 🔨 Generating supabase-integration skill...
      └─ ✅ Skill generated (1,823 lines)

✅ Setup Complete!
```

#### Output
- `~/.claude/skills/skillforge/data/user_profile.json` - Your preferences
- `~/.claude/skills/<skill-name>/` - Generated skills

#### Examples
```bash
# First-time setup
> /sf:wizard

# Update existing profile
> /sf:wizard --update
```

---

### /sf:generate

**Generate a specific skill**

#### Purpose
Quickly generate a single skill without running the full wizard. Perfect for adding one skill at a time or regenerating an existing skill with updated documentation.

#### Syntax
```
/sf:generate <skill-type> [--force] [--preview] [--no-docs]
```

#### Skill Types

**Frontend Frameworks**
- `nextjs-fullstack` - Next.js fullstack (App Router, API routes, Server Components)
- `react-spa` - React single-page application
- `vue-app` - Vue.js application (Composition API, Pinia)
- `svelte-app` - Svelte/SvelteKit
- `angular-app` - Angular application

**Backend Frameworks**
- `express-api` - Express.js REST API
- `fastapi-api` - FastAPI Python REST API
- `django-api` - Django REST Framework
- `nestjs-api` - NestJS API
- `flask-api` - Flask Python API

**Database & Services**
- `supabase-integration` - Supabase (Auth, Database, Storage, Realtime)
- `mongodb-integration` - MongoDB
- `postgresql-integration` - PostgreSQL
- `prisma-orm` - Prisma ORM
- `firebase-integration` - Firebase (Auth, Firestore, Functions)

**Testing & DevOps**
- `testing-suite` - Comprehensive testing setup
- `e2e-testing` - End-to-end testing with Playwright/Cypress
- `git-workflow` - Git workflow and best practices
- `deployment-pipeline` - CI/CD and deployment automation
- `docker-setup` - Docker and containerization

**UI & Styling**
- `tailwind-styling` - Tailwind CSS styling patterns
- `component-library` - Component library setup (shadcn/ui, MUI)
- `responsive-design` - Responsive design patterns

**Additional**
- `auth-implementation` - Authentication implementation
- `api-integration` - External API integration
- `error-handling` - Error handling and logging
- `performance-optimization` - Performance optimization

#### Options

**`--force`** - Overwrite existing skill without prompting
```bash
/sf:generate nextjs-fullstack --force
```

**`--preview`** - Show what would be generated without creating files
```bash
/sf:generate react-spa --preview
```

**`--no-docs`** - Skip documentation fetching (use cached/built-in)
```bash
/sf:generate supabase-integration --no-docs
```

#### Generation Process

1. **Validate Skill Type** - Check if skill type is recognized
2. **Check Existing** - Look for existing skill (prompt if found)
3. **Load Profile** - Read user profile, use defaults if not found
4. **Fetch Documentation** - Get latest docs via Context7 (unless --no-docs)
5. **Generate SKILL.md** - Process template with your preferences
6. **Validate** - Check YAML, structure, token budget
7. **Save** - Write to `~/.claude/skills/<skill-name>/`

#### Examples

**Generate Next.js skill**
```bash
> /sf:generate nextjs-fullstack

Output:
📦 Fetching Next.js 15 documentation...
   └─ ✅ Fetched from Context7

🔨 Generating nextjs-fullstack skill...
   ├─ Loading template
   ├─ Injecting YOUR preferences
   ├─ Creating SKILL.md (2,534 lines)
   └─ ✅ Generated

Saved to: ~/.claude/skills/nextjs-fullstack/SKILL.md
```

**Preview without creating**
```bash
> /sf:generate vue-app --preview

Output:
📋 Preview Mode - No files will be created

Skill: vue-app
Size: ~1,842 lines (~2,300 tokens)

Sections:
  ├─ Overview
  ├─ Composition API Patterns
  ├─ State Management (Pinia)
  ├─ Vue Router
  ├─ Best Practices
  └─ User Conventions

To generate: /sf:generate vue-app
```

**Force overwrite existing**
```bash
> /sf:generate supabase-integration --force

Output:
⚠️  Skill 'supabase-integration' already exists

🔄 Overwriting (--force flag)...
   └─ ✅ Regenerated with latest docs
```

---

### /sf:list

**List all installed skills**

#### Purpose
Quick overview of all skills installed in your Claude Code environment.

#### Syntax
```
/sf:list [--category <category>] [--sort <field>]
```

#### Options

**`--category`** - Filter by skill category
```bash
/sf:list --category frontend
```

**`--sort`** - Sort by field (name, uses, updated, tokens)
```bash
/sf:list --sort uses
```

#### Output

```
┌────────────────────────────────────────────────────┐
│  📚 Installed Skills (8)                           │
├────────────────────────────────────────────────────┤
│                                                    │
│  nextjs-fullstack                                  │
│  ├─ Type: Frontend Framework                      │
│  ├─ Size: 2,534 lines (~3,200 tokens)            │
│  ├─ Uses: 89 times (94% success)                 │
│  ├─ Updated: 2 days ago                           │
│  └─ Path: ~/.claude/skills/nextjs-fullstack/     │
│                                                    │
│  supabase-integration                              │
│  ├─ Type: Backend Integration                     │
│  ├─ Size: 1,823 lines (~2,300 tokens)            │
│  ├─ Uses: 67 times (96% success)                 │
│  ├─ Updated: 2 days ago                           │
│  └─ Path: ~/.claude/skills/supabase-integration/ │
│                                                    │
│  git-workflow                                      │
│  ├─ Type: Workflow                                │
│  ├─ Size: 634 lines (~800 tokens)                │
│  ├─ Uses: 45 times (100% success)                │
│  ├─ Updated: 5 days ago                           │
│  └─ Path: ~/.claude/skills/git-workflow/         │
│                                                    │
│  ... (5 more skills)                              │
│                                                    │
│  Total Token Budget: ~12,500 tokens               │
│  Efficiency: Excellent ✅                         │
└────────────────────────────────────────────────────┘
```

#### Examples

**List all skills**
```bash
> /sf:list
```

**List frontend skills**
```bash
> /sf:list --category frontend
```

**List sorted by usage**
```bash
> /sf:list --sort uses
```

---

### /sf:status

**View SkillForge system status**

#### Purpose
Health check and status overview of the SkillForge system.

#### Syntax
```
/sf:status [--verbose]
```

#### Options

**`--verbose`** - Show detailed diagnostic information
```bash
/sf:status --verbose
```

#### Output

```
╔════════════════════════════════════════════════╗
║  🔨 SkillForge System Status                   ║
╚════════════════════════════════════════════════╝

Installation:
  ✅ SkillForge installed
  ✅ Core files present (7/7)
  ✅ Commands registered (10/10)
  📍 Version: 1.0.0

Profile:
  ✅ User profile configured
  📅 Last updated: 2 days ago
  🎯 Tech Stack: Next.js, Supabase, Tailwind

Skills:
  ✅ 8 skills installed
  ✅ 12,500 tokens used (~25% of budget)
  📊 Average success rate: 96%

Learning:
  ✅ Pattern learning enabled
  📈 3 patterns detected (2 applied)
  💾 89 usage events tracked

Optimization:
  ✅ Last run: 1 week ago
  💡 2 optimization suggestions available

MCP Integration:
  ✅ Context7 connected
  ✅ Documentation cache valid

System Health: Excellent ✅
```

#### Examples

**Basic status**
```bash
> /sf:status
```

**Detailed diagnostics**
```bash
> /sf:status --verbose
```

---

## Analysis & Optimization

### /sf:analyze

**Analyze skills, usage, and patterns**

#### Purpose
Comprehensive analysis system providing insights into:
- Skill health and usage
- Learned patterns and confidence
- Optimization opportunities
- Token efficiency
- Usage trends

#### Syntax
```
/sf:analyze [--detailed] [--patterns] [--health] [--export]
```

#### Options

**`--detailed`** - Detailed analysis per skill
```bash
/sf:analyze --detailed
```

**`--patterns`** - Focus on learned patterns
```bash
/sf:analyze --patterns
```

**`--health`** - Run health check
```bash
/sf:analyze --health
```

**`--export`** - Export report to JSON
```bash
/sf:analyze --export
```

#### Output Sections

**1. Skills Overview**
```
Skills Overview:
  Total Skills: 8
  SkillForge Generated: 5
  Native Anthropic: 3
  Total Token Usage: ~12,500 tokens
  Efficiency: Excellent (25% of budget)
```

**2. Usage Statistics**
```
Usage Statistics (Last 30 days):
  Most Used:
    1. nextjs-fullstack (89 uses, 94% success)
    2. supabase-integration (67 uses, 96% success)
    3. git-workflow (45 uses, 100% success)

  Common Combinations:
    1. nextjs-fullstack + supabase-integration (43 times)
    2. nextjs-fullstack + tailwind-styling (38 times)

  Trends:
    📈 Usage increased 23% vs last month
    ⏱️  Average task duration: 45 seconds
```

**3. Learned Patterns**
```
Learned Patterns (3):
  ✅ always_use_zod (confidence: 92%, applied)
     - Detected from 23 samples
     - Applied to: nextjs-fullstack, react-spa

  ✅ error_boundary_pattern (confidence: 88%, applied)
     - Detected from 18 samples
     - Applied to: nextjs-fullstack

  ⏳ feature_colocation (confidence: 75%, pending)
     - Needs 5 more samples to reach 80% threshold
```

**4. Optimization Opportunities**
```
Optimization Opportunities:
  ⚡ Merge react-spa + react-vite (82% overlap, save 1,200 tokens)
  📝 Update nextjs-fullstack (Next.js 14 → 15 available)
  🧹 Remove vue-legacy skill (0 uses in 90 days)

  Potential Token Savings: 3,050 tokens
```

**5. Health Check**
```
Health Check:
  ✅ All YAML frontmatter valid
  ✅ No broken references
  ⚠️  1 skill has outdated docs (>90 days)
  ✅ All dependencies met

Overall Health: Good
```

#### Examples

**Basic analysis**
```bash
> /sf:analyze
```

**Focus on patterns**
```bash
> /sf:analyze --patterns
```

**Full health check**
```bash
> /sf:analyze --health
```

**Export report**
```bash
> /sf:analyze --export

Output:
📊 Analysis complete
💾 Exported to: ~/.claude/skills/skillforge/data/analysis-2025-10-23.json
```

---

### /sf:optimize

**Optimize existing skills**

#### Purpose
Apply optimization strategies to improve skills:
- Merge similar skills
- Update outdated documentation
- Compress verbose content
- Remove unused skills
- Improve structure

#### Syntax
```
/sf:optimize [--auto] [--dry-run] [--target <skill>]
```

#### Options

**`--auto`** - Auto-apply safe optimizations without prompting
```bash
/sf:optimize --auto
```

**`--dry-run`** - Show what would be optimized without applying
```bash
/sf:optimize --dry-run
```

**`--target <skill>`** - Optimize specific skill only
```bash
/sf:optimize --target nextjs-fullstack
```

#### Optimization Strategies

**1. Merge Similar Skills (>70% overlap)**
```
Found: react-spa and react-vite share 82% content

Suggestion: Merge into 'react-spa'
  - Keep unique content from both
  - Save 1,200 tokens
  - Improve consistency

Proceed with merge? [Y/n]
```

**2. Update Outdated Documentation (>90 days)**
```
Found: nextjs-fullstack uses Next.js 14 docs

Suggestion: Update to Next.js 15
  - Fetch latest documentation
  - Update code examples
  - Add new features (Partial Prerendering, etc.)

Update documentation? [Y/n]
```

**3. Compress Verbose Content (>3,000 tokens)**
```
Found: python-fastapi is 3,450 tokens (target: <3,000)

Suggestion: Compress content
  - Remove redundant examples
  - Consolidate similar sections
  - Save ~650 tokens

Compress skill? [Y/n]
```

**4. Restructure for Progressive Disclosure**
```
Found: supabase-integration loads all content upfront

Suggestion: Restructure
  - Move advanced topics to later sections
  - Improve section organization
  - Enable progressive loading

Restructure skill? [Y/n]
```

**5. Remove Unused Skills (0 uses in 60+ days)**
```
Found: vue-legacy has 0 uses in 90 days

Suggestion: Remove (archive first)
  - Create backup in data/archives/
  - Free up token budget
  - Can restore later if needed

Remove skill? [Y/n]
```

#### Output

```
╔════════════════════════════════════════════════╗
║  ⚡ Optimization Report                        ║
╚════════════════════════════════════════════════╝

Analyzed: 8 skills
Optimizations Found: 5

Applied:
  ✅ Updated nextjs-fullstack docs (Next.js 14 → 15)
  ✅ Compressed python-fastapi (saved 650 tokens)
  ⏭️  Merge suggestion (react-spa + react-vite) - user deferred
  ⏭️  Remove vue-legacy - user deferred

Token Savings: 650 tokens
Time Saved: ~2 minutes per task

Run /sf:analyze to see updated stats
```

#### Examples

**Interactive optimization**
```bash
> /sf:optimize
```

**Auto-apply safe changes**
```bash
> /sf:optimize --auto
```

**Preview changes**
```bash
> /sf:optimize --dry-run
```

**Optimize specific skill**
```bash
> /sf:optimize --target nextjs-fullstack
```

---

### /sf:update

**Update skill documentation**

#### Purpose
Update one or all skills with the latest documentation from Context7.

#### Syntax
```
/sf:update [<skill-name>] [--all] [--check] [--force]
```

#### Options

**`--all`** - Update all skills
```bash
/sf:update --all
```

**`--check`** - Check for available updates without applying
```bash
/sf:update --check
```

**`--force`** - Force update even if docs are recent
```bash
/sf:update nextjs-fullstack --force
```

#### Update Process

1. **Check Current Version** - Read current documentation version
2. **Fetch Latest** - Query Context7 for latest docs
3. **Compare** - Check if update is available
4. **Show Diff** - Display what's changed
5. **Confirm** - Ask for user confirmation
6. **Update** - Apply new documentation
7. **Validate** - Ensure skill still valid
8. **Backup** - Keep old version in archives

#### Examples

**Update specific skill**
```bash
> /sf:update nextjs-fullstack

Output:
📦 Checking for Next.js updates...
   Current: Next.js 14.2.1
   Latest:  Next.js 15.0.2

📝 Changes found:
   - New: Partial Prerendering
   - New: Server Actions improvements
   - Updated: Caching behavior
   - Deprecated: getServerSideProps

Update to Next.js 15.0.2? [Y/n] Y

🔄 Updating nextjs-fullstack...
   ├─ Backing up current version
   ├─ Fetching latest documentation
   ├─ Updating code examples
   ├─ Validating changes
   └─ ✅ Updated successfully

Restart Claude Code to use updated skill
```

**Check all skills for updates**
```bash
> /sf:update --check

Output:
📊 Checking all skills for updates...

Updates Available (2):
  ├─ nextjs-fullstack: 14.2.1 → 15.0.2
  └─ supabase-integration: 2.38.4 → 2.39.0

Up to Date (6):
  ├─ react-spa
  ├─ git-workflow
  ├─ tailwind-styling
  ├─ testing-suite
  ├─ python-fastapi
  └─ mongodb-integration

To update all: /sf:update --all
```

**Update all skills**
```bash
> /sf:update --all

Output:
🔄 Updating all skills with new documentation...

[1/2] nextjs-fullstack
      └─ ✅ Updated (14.2.1 → 15.0.2)

[2/2] supabase-integration
      └─ ✅ Updated (2.38.4 → 2.39.0)

✅ All skills updated successfully
```

---

## Configuration & Debug

### /sf:config

**Configure SkillForge settings**

#### Purpose
View and modify SkillForge configuration settings.

#### Syntax
```
/sf:config [get <key>] [set <key> <value>] [--reset]
```

#### Options

**`get <key>`** - Get configuration value
```bash
/sf:config get learning.enabled
```

**`set <key> <value>`** - Set configuration value
```bash
/sf:config set learning.enabled true
```

**`--reset`** - Reset to default configuration
```bash
/sf:config --reset
```

#### Configuration Keys

**Learning Settings**
```
learning.enabled                  (true/false) - Enable pattern learning
learning.min_samples              (number) - Minimum samples for pattern (default: 10)
learning.confidence_threshold     (0.0-1.0) - Minimum confidence to apply (default: 0.8)
learning.auto_apply               (true/false) - Auto-apply patterns
```

**Optimization Settings**
```
optimization.auto_optimize        (true/false) - Auto-optimization
optimization.token_budget         (number) - Token budget per skill (default: 3000)
optimization.check_updates        (true/false) - Auto-check for updates
optimization.update_frequency     (days) - Update check frequency (default: 7)
```

**User Preferences**
```
preferences.naming.variables      (string) - camelCase, snake_case, etc.
preferences.imports.style         (string) - absolute, relative
preferences.imports.alias         (string) - @/, ~/, etc.
```

#### Examples

**View all configuration**
```bash
> /sf:config

Output:
╔════════════════════════════════════════════════╗
║  ⚙️  SkillForge Configuration                  ║
╚════════════════════════════════════════════════╝

Learning:
  enabled: true
  min_samples: 10
  confidence_threshold: 0.8
  auto_apply: true

Optimization:
  auto_optimize: true
  token_budget: 3000
  check_updates: true
  update_frequency: 7 days

User Preferences:
  naming.variables: camelCase
  imports.style: absolute
  imports.alias: @/

To modify: /sf:config set <key> <value>
```

**Get specific value**
```bash
> /sf:config get learning.enabled

Output:
learning.enabled = true
```

**Set value**
```bash
> /sf:config set learning.min_samples 15

Output:
✅ Configuration updated
   learning.min_samples: 10 → 15
```

**Reset to defaults**
```bash
> /sf:config --reset

Output:
⚠️  This will reset ALL configuration to defaults

Current configuration will be backed up to:
  ~/.claude/skills/skillforge/data/config-backup-2025-10-23.json

Continue? [y/N] y

✅ Configuration reset to defaults
```

---

### /sf:introspect

**Debug orchestration and learning**

#### Purpose
Introspection tool for debugging SkillForge's decision-making process. Shows how intent was analyzed, which skills were discovered, and why certain patterns were applied.

#### Syntax
```
/sf:introspect [--orchestration] [--learning] [--last] [--request <text>]
```

#### Options

**`--orchestration`** - Debug skill discovery decisions
```bash
/sf:introspect --orchestration
```

**`--learning`** - Debug pattern learning
```bash
/sf:introspect --learning
```

**`--last`** - Show analysis for last request
```bash
/sf:introspect --last
```

**`--request <text>`** - Analyze hypothetical request
```bash
/sf:introspect --request "Create auth component"
```

#### Output

**Orchestration Debug**
```
╔════════════════════════════════════════════════╗
║  🔍 Orchestration Introspection                ║
╚════════════════════════════════════════════════╝

Last Request: "Create a login component with Supabase auth"

1. Intent Analysis:
   ├─ Entities: ["login", "component", "Supabase", "auth"]
   ├─ Action: "create"
   ├─ Domain: "fullstack"
   ├─ Complexity: "moderate"
   └─ Patterns Matched: [auth_component_pattern]

2. Skill Discovery:
   Discovered 3 skills using multiple strategies:

   nextjs-fullstack (Priority: 100)
   ├─ Strategy: Explicit Match
   ├─ Reason: "component" triggers this skill
   └─ Token Allocation: 2,000 tokens (40%)

   supabase-integration (Priority: 100)
   ├─ Strategy: Explicit Match
   ├─ Reason: "Supabase" triggers this skill
   └─ Token Allocation: 1,800 tokens (36%)

   git-workflow (Priority: 40)
   ├─ Strategy: Dependency
   ├─ Reason: Required by nextjs-fullstack
   └─ Token Allocation: 400 tokens (8%)

3. Loading Decision:
   ├─ Total Skills: 3
   ├─ Token Budget: 5,000 tokens
   ├─ Allocated: 4,200 tokens (84%)
   ├─ Reserved: 800 tokens (16%)
   └─ Loading Level: 2 (Core Sections)

4. Pattern Application:
   Applied 2 learned patterns:
   ├─ always_use_zod (confidence: 92%)
   └─ error_boundary_pattern (confidence: 88%)
```

**Learning Debug**
```
╔════════════════════════════════════════════════╗
║  🧠 Learning Introspection                     ║
╚════════════════════════════════════════════════╝

Pattern Detection Status:

Active Patterns (2):
  always_use_zod
  ├─ Confidence: 92%
  ├─ Samples: 23
  ├─ Success Rate: 95%
  ├─ First Detected: 2025-09-15
  └─ Status: Applied to 2 skills

  error_boundary_pattern
  ├─ Confidence: 88%
  ├─ Samples: 18
  ├─ Success Rate: 94%
  ├─ First Detected: 2025-09-20
  └─ Status: Applied to 1 skill

Pending Patterns (1):
  feature_colocation
  ├─ Confidence: 75%
  ├─ Samples: 15
  ├─ Success Rate: 93%
  ├─ Needs: 5 more samples (target: 20)
  └─ Status: Monitoring

Recent Learning Activity:
  ├─ Last cycle: 2 hours ago
  ├─ Events processed: 12
  ├─ Patterns updated: 3
  └─ Next cycle: in 8 hours
```

#### Examples

**Debug last request**
```bash
> /sf:introspect --last
```

**Debug orchestration**
```bash
> /sf:introspect --orchestration
```

**Debug learning**
```bash
> /sf:introspect --learning
```

**Simulate request**
```bash
> /sf:introspect --request "Create a dashboard with charts"
```

---

### /sf:reset

**Reset SkillForge data**

#### Purpose
Reset various parts of SkillForge data. Useful for troubleshooting or starting fresh.

#### Syntax
```
/sf:reset [--profile] [--analytics] [--patterns] [--cache] [--all]
```

#### Options

**`--profile`** - Reset user profile only
```bash
/sf:reset --profile
```

**`--analytics`** - Clear usage analytics
```bash
/sf:reset --analytics
```

**`--patterns`** - Clear learned patterns
```bash
/sf:reset --patterns
```

**`--cache`** - Clear documentation cache
```bash
/sf:reset --cache
```

**`--all`** - Reset everything (nuclear option)
```bash
/sf:reset --all
```

#### Reset Levels

**1. Profile Reset**
- Clears user preferences
- Keeps skills intact
- Requires re-running wizard
- Backs up old profile

**2. Analytics Reset**
- Clears usage statistics
- Resets success rates
- Fresh start for tracking
- Patterns remain

**3. Patterns Reset**
- Clears learned patterns
- Patterns will re-learn
- Does not affect skills
- Analytics remain

**4. Cache Reset**
- Clears documentation cache
- Forces fresh fetches
- Temporary files only
- No data loss

**5. Full Reset (--all)**
- Resets everything
- Keeps generated skills
- Complete fresh start
- Full backup created

#### Examples

**Reset user profile**
```bash
> /sf:reset --profile

Output:
⚠️  Reset User Profile

This will:
  - Clear your preferences
  - Require re-running /sf:wizard
  - NOT delete generated skills

Backup will be saved to:
  ~/.claude/skills/skillforge/data/profile-backup-2025-10-23.json

Continue? [y/N] y

✅ Profile reset
   Next: Run /sf:wizard to set up new profile
```

**Clear cache**
```bash
> /sf:reset --cache

Output:
🧹 Clearing documentation cache...
   ├─ Removed 12 cached files
   └─ Freed 2.3 MB

✅ Cache cleared
   Next fetches will get latest documentation
```

**Nuclear reset**
```bash
> /sf:reset --all

Output:
⚠️  WARNING: Full Reset

This will reset:
  ✓ User profile
  ✓ Usage analytics
  ✓ Learned patterns
  ✓ Documentation cache

Generated skills will NOT be deleted

Full backup will be created at:
  ~/.claude/skills/skillforge/data/backup-2025-10-23/

This cannot be undone. Continue? [y/N] y

🔄 Creating full backup...
   └─ ✅ Backup created

🧹 Resetting all data...
   ├─ ✅ Profile reset
   ├─ ✅ Analytics cleared
   ├─ ✅ Patterns cleared
   └─ ✅ Cache cleared

✅ SkillForge reset complete

Next steps:
  1. Run /sf:wizard to set up profile
  2. Skills will start learning from scratch
  3. You can restore backup if needed
```

---

## Command Combinations

### Common Workflows

**Initial Setup**
```bash
1. /sf:wizard           # Set up profile
2. /sf:list             # Verify skills created
3. /sf:status           # Check system health
```

**Weekly Maintenance**
```bash
1. /sf:analyze          # Review usage & patterns
2. /sf:update --check   # Check for updates
3. /sf:optimize --dry-run  # Preview optimizations
```

**Monthly Review**
```bash
1. /sf:analyze --detailed  # Deep analysis
2. /sf:optimize --auto     # Apply optimizations
3. /sf:update --all        # Update all docs
4. /sf:status             # Verify health
```

**Troubleshooting**
```bash
1. /sf:introspect --last     # Debug last request
2. /sf:introspect --learning # Check learning status
3. /sf:status --verbose      # Detailed diagnostics
```

**Adding New Tech Stack**
```bash
1. /sf:wizard --update     # Update profile
2. /sf:generate <skill>    # Generate new skill
3. /sf:list               # Verify installation
```

---

## Best Practices

### Command Frequency

- **Daily**: Natural usage, no commands needed (SkillForge orchestrates automatically)
- **Weekly**: `/sf:analyze` - Review patterns and usage
- **Monthly**: `/sf:optimize` - Apply optimizations
- **As Needed**: `/sf:generate` - Add new skills
- **Rarely**: `/sf:config`, `/sf:reset` - Only when changing settings

### Performance Tips

1. **Use --preview** before generating to check output
2. **Use --no-docs** for faster generation (uses cache)
3. **Use --auto** on `/sf:optimize` for hands-off optimization
4. **Check --dry-run** before applying changes

### Maintenance

1. Run `/sf:analyze` weekly to stay informed
2. Update documentation monthly with `/sf:update --all`
3. Let patterns learn naturally (10+ samples required)
4. Review and apply optimization suggestions

---

## Further Reading

- [Quick Start Guide](QUICKSTART.md) - Get started in 10 minutes
- [Architecture](ARCHITECTURE.md) - Technical deep dive
- [API Documentation](API.md) - Python API reference
- [Templates Guide](TEMPLATES.md) - Create custom templates
- [FAQ](FAQ.md) - Common questions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**Questions?** Open an issue on [GitHub](https://github.com/omarpiosedev/SkillForge/issues)

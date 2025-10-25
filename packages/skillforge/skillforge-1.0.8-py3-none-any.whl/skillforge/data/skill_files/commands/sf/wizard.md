---
name: wizard
description: Launch interactive skill generation wizard. Analyzes your tech stack and generates personalized skills.
---

# /sf:wizard - Claude-Assisted Setup Wizard

## Purpose
YOU (Claude Code) will act as the interactive wizard, guiding the user through SkillForge setup by asking questions conversationally and saving their preferences.

## When to Use
- **First time setup** - Initialize SkillForge for the first time
- **Adding new tech stack** - Expand your skills with new frameworks
- **Onboarding new project** - Set up skills for a new codebase
- **User requests setup/configuration** - When explicitly asked to configure

## CRITICAL IMPLEMENTATION NOTES

**DO NOT** call `skillforge wizard` via Bash - it cannot work in non-interactive environments!

**YOU MUST**:
1. Act as the wizard yourself
2. Use Read/Glob to scan project files
3. Use AskUserQuestion tool for multiple-choice questions
4. Use Write to save the user_profile.json
5. Guide the user conversationally

## Step-by-Step Implementation

### Step 1: Welcome & Auto-Detection

1. **Greet the user warmly**:
   ```
   🧙 Welcome to the SkillForge Setup Wizard!

   I'll help you create personalized Claude Code skills tailored to YOUR tech stack.

   This will take about 3-5 minutes. I'll:
   • Auto-detect your technologies
   • Ask about your preferences
   • Generate a profile for skill generation
   ```

2. **Scan project files** to detect tech stack:
   - Use Read to check these files (if they exist):
     - `package.json` - Node.js dependencies
     - `requirements.txt` or `pyproject.toml` - Python
     - `go.mod` - Go
     - `Gemfile` - Ruby
     - `composer.json` - PHP
     - `tsconfig.json` - TypeScript
     - `.eslintrc*` - ESLint
     - `tailwind.config.*` - Tailwind

3. **Extract and show detected technologies**:
   ```
   📍 Auto-detected in your project:
     ✓ Next.js 15.0.0 (from package.json)
     ✓ React 19 (from package.json)
     ✓ TypeScript 5.3 (from tsconfig.json)
     ✓ Tailwind CSS (from tailwind.config.ts)
     ✓ Supabase (from package.json)
   ```

### Step 2: Interactive Questionnaire

Use **AskUserQuestion** tool to ask these questions. Pre-select detected values as defaults.

**Question 1: Developer Role**
```
header: "Role"
question: "What type of developer are you?"
options:
  - label: "Full-Stack Developer"
    description: "Work on both frontend and backend"
  - label: "Frontend Developer"
    description: "Focus on UI/UX and client-side code"
  - label: "Backend Developer"
    description: "Focus on APIs, databases, server-side logic"
  - label: "DevOps Engineer"
    description: "Focus on infrastructure, CI/CD, deployment"
```

**Question 2: Frontend Framework** (skip if Backend Developer)
```
header: "Frontend"
question: "Which frontend framework do you primarily use?"
options:
  - label: "Next.js"
    description: "React framework with SSR/SSG"
  - label: "React"
    description: "JavaScript library for UI"
  - label: "Vue.js"
    description: "Progressive JavaScript framework"
  - label: "Svelte"
    description: "Compiled JavaScript framework"
```

**Question 3: UI Library** (multiSelect: true)
```
header: "UI Library"
question: "Which UI libraries/frameworks do you use?"
multiSelect: true
options:
  - label: "Tailwind CSS"
    description: "Utility-first CSS framework"
  - label: "shadcn/ui"
    description: "Re-usable components built with Radix UI and Tailwind"
  - label: "Material-UI (MUI)"
    description: "React components implementing Material Design"
  - label: "CSS Modules"
    description: "Scoped CSS files"
```

**Question 4: State Management** (multiSelect: true)
```
header: "State"
question: "How do you manage state?"
multiSelect: true
options:
  - label: "Zustand"
    description: "Lightweight state management"
  - label: "Redux Toolkit"
    description: "Official Redux toolset"
  - label: "Context API"
    description: "Built-in React state management"
  - label: "Server State Only"
    description: "No client state management (use server components)"
```

**Question 5: Backend Framework** (skip if Frontend Developer)
```
header: "Backend"
question: "Which backend framework do you use?"
options:
  - label: "Next.js API Routes"
    description: "Built into Next.js"
  - label: "Express.js"
    description: "Minimal Node.js framework"
  - label: "FastAPI"
    description: "Modern Python framework"
  - label: "Django"
    description: "Full-featured Python framework"
```

**Question 6: Database** (multiSelect: true)
```
header: "Database"
question: "Which database(s) do you work with?"
multiSelect: true
options:
  - label: "Supabase"
    description: "PostgreSQL with real-time & auth"
  - label: "PostgreSQL"
    description: "Relational database"
  - label: "MongoDB"
    description: "NoSQL document database"
  - label: "Redis"
    description: "In-memory cache/database"
```

**Question 7: Authentication** (multiSelect: true)
```
header: "Auth"
question: "How do you handle authentication?"
multiSelect: true
options:
  - label: "Supabase Auth"
    description: "Built into Supabase"
  - label: "NextAuth.js"
    description: "Authentication for Next.js"
  - label: "Clerk"
    description: "Complete user management"
  - label: "Custom JWT"
    description: "Roll your own JWT auth"
```

**Question 8: Testing Tools** (multiSelect: true)
```
header: "Testing"
question: "Which testing tools do you use?"
multiSelect: true
options:
  - label: "Vitest"
    description: "Fast unit test framework"
  - label: "Jest"
    description: "JavaScript testing framework"
  - label: "Playwright"
    description: "End-to-end testing"
  - label: "Cypress"
    description: "E2E testing framework"
```

**Question 9: Code Style** (multiSelect: true)
```
header: "Code Style"
question: "What are your code style preferences?"
multiSelect: true
options:
  - label: "TypeScript Strict Mode"
    description: "Strictest type checking"
  - label: "ESLint + Prettier"
    description: "Linting and formatting"
  - label: "Functional Programming"
    description: "Prefer pure functions, immutability"
  - label: "Object-Oriented"
    description: "Classes and inheritance"
```

**Question 10: Deployment** (multiSelect: true)
```
header: "Deployment"
question: "Where do you deploy your applications?"
multiSelect: true
options:
  - label: "Vercel"
    description: "Optimized for Next.js"
  - label: "Netlify"
    description: "JAMstack hosting"
  - label: "AWS"
    description: "Amazon Web Services"
  - label: "Docker"
    description: "Containerized deployment"
```

### Step 3: Generate & Save Profile

1. **Build the profile structure**:
```json
{
  "setup_completed": true,
  "created_at": "2025-01-24T10:30:00Z",
  "role": "Full-Stack Developer",
  "tech_stack": {
    "frontend": "Next.js",
    "ui": ["Tailwind CSS", "shadcn/ui"],
    "state": ["Zustand"],
    "backend": "Next.js API Routes",
    "database": ["Supabase"],
    "auth": ["Supabase Auth"],
    "testing": ["Vitest", "Playwright"],
    "build": "Vite"
  },
  "preferences": {
    "code_style": ["TypeScript Strict Mode", "ESLint + Prettier"],
    "deployment": ["Vercel"],
    "package_manager": "pnpm"
  },
  "conventions": {
    "typescript": true,
    "linting": true,
    "formatting": true,
    "paradigm": ["functional"]
  }
}
```

2. **Show summary to user**:
```
═══════════════════════════════════════════════════
📋 Your SkillForge Configuration
═══════════════════════════════════════════════════

👤 Role: Full-Stack Developer

🔧 Tech Stack:
   • Frontend: Next.js
   • UI: Tailwind CSS, shadcn/ui
   • State: Zustand
   • Backend: Next.js API Routes
   • Database: Supabase
   • Auth: Supabase Auth
   • Testing: Vitest, Playwright

✨ Preferences:
   • Code Style: TypeScript Strict Mode, ESLint + Prettier
   • Deployment: Vercel
```

3. **Save to file**:
   - Use Write tool to save to `~/.claude/skills/skillforge/data/user_profile.json`
   - Create directories if needed
   - Pretty-print JSON with 2-space indent

### Step 4: Determine & Generate Skills Automatically

**CRITICAL**: After saving the profile, you MUST automatically generate skills based on the tech stack!

1. **Determine which skills to generate** based on tech_stack:

```python
# Mapping logic:
tech_stack = profile["tech_stack"]

skills_to_generate = []

# Frontend skills
if "Next.js" in tech_stack.get("frontend", ""):
    skills_to_generate.append("nextjs-fullstack")
elif "React" in tech_stack.get("frontend", ""):
    skills_to_generate.append("react-components")
elif "Vue" in tech_stack.get("frontend", ""):
    skills_to_generate.append("vue-components")

# Database skills
if "Supabase" in tech_stack.get("database", []):
    skills_to_generate.append("supabase-integration")
elif "PostgreSQL" in tech_stack.get("database", []):
    skills_to_generate.append("postgresql-integration")

# UI/Styling skills
if "Tailwind CSS" in tech_stack.get("ui", []):
    skills_to_generate.append("tailwind-styling")
if "shadcn/ui" in tech_stack.get("ui", []):
    skills_to_generate.append("shadcn-components")

# Testing skills
if tech_stack.get("testing"):
    skills_to_generate.append("testing-suite")

# Backend skills (if not using Next.js API routes)
if "Express" in tech_stack.get("backend", ""):
    skills_to_generate.append("express-api")
elif "FastAPI" in tech_stack.get("backend", ""):
    skills_to_generate.append("fastapi-backend")
```

2. **Show what will be generated**:
```
🚀 Generating {count} skills based on your tech stack...

📦 Skills to create:
   1. nextjs-fullstack - Next.js app development
   2. supabase-integration - Supabase client & auth
   3. tailwind-styling - Tailwind CSS patterns
   4. testing-suite - Vitest + Playwright setup

This will take about 1-2 minutes...
```

3. **Generate each skill with FULL AI-powered generation**:

For each skill, you MUST:

**A) Fetch latest documentation** (if available via Context7 MCP):
```
# Use mcp__context7__resolve_library_id first
library_id = mcp__context7__resolve_library_id("Next.js")
# Example result: "/vercel/next.js"

# Then fetch docs
docs = mcp__context7__get_library_docs(
  context7CompatibleLibraryID=library_id,
  topic="app router, server components, data fetching",
  tokens=5000
)
```

**B) Generate comprehensive skill content** using:
- Latest documentation from Context7
- User preferences from profile
- Your AI reasoning and expertise
- Best practices and patterns

**C) Structure the skill file** with these sections:

```markdown
---
name: nextjs-fullstack
version: 1.0.0
description: Next.js full-stack development with App Router
tags: [next.js, react, typescript, server-components]
tech_stack:
  frontend: Next.js
  state: Zustand
  styling: Tailwind CSS
  database: Supabase
user_preferences:
  role: Full-Stack Developer
  code_style: [TypeScript Strict Mode, ESLint + Prettier]
  paradigm: [functional]
last_updated: 2025-01-24T10:30:00Z
---

# Next.js Full-Stack Development

## Overview
[AI-generated comprehensive overview based on latest docs]

## Core Patterns

### App Router & Server Components
[Latest patterns from Next.js docs]

### Data Fetching
[Server Components, async/await patterns]

### State Management with Zustand
[Integration patterns specific to user's choice]

### Supabase Integration
[Database patterns for user's stack]

## User Preferences

### Code Style
- TypeScript Strict Mode enabled
- ESLint + Prettier for formatting
- Functional programming paradigm

### Naming Conventions
[Based on user's preferences]

## Common Tasks

### Creating a New Page
[Step-by-step with user's conventions]

### Building API Routes
[Patterns matching user's stack]

### Database Operations
[Supabase-specific patterns]

## Examples
[AI-generated examples using user's exact stack and preferences]

## Best Practices
[Latest from docs + user preferences]
```

**D) Show progress** as each skill is generated:
```
🔄 Generating nextjs-fullstack...
   📚 Fetching Next.js documentation...
   ✅ Generated: nextjs-fullstack (3,245 tokens)

🔄 Generating supabase-integration...
   📚 Fetching Supabase documentation...
   ✅ Generated: supabase-integration (2,156 tokens)

🔄 Generating tailwind-styling...
   📚 Fetching Tailwind CSS documentation...
   ✅ Generated: tailwind-styling (1,890 tokens)

🔄 Generating testing-suite...
   ✅ Generated: testing-suite (2,340 tokens)
```

**E) Save each skill** to:
- `~/.claude/skills/{skill-name}/SKILL.md`
- Create parent directory if needed

### Step 5: Completion Message

```
═══════════════════════════════════════════════════
🎉 SkillForge Setup Complete!
═══════════════════════════════════════════════════

✅ Profile saved to:
   ~/.claude/skills/skillforge/data/user_profile.json

✅ Generated 4 skills with latest documentation:
   • nextjs-fullstack (3,245 tokens)
   • supabase-integration (2,156 tokens)
   • tailwind-styling (1,890 tokens)
   • testing-suite (2,340 tokens)

📊 Total: 4 skills | 9,631 tokens

💡 These skills are now active and will be automatically loaded
   when you work on tasks matching your tech stack!

📋 Try it now:
   • "Create a Next.js page with Supabase auth"
   • "Build a React component with Tailwind styling"
   • "Set up Vitest tests for a component"

🔧 Manage your skills:
   • /sf:list - View all skills
   • /sf:status - Check configuration
   • /sf:update <skill> - Refresh with latest docs
   • /sf:optimize - Reduce token usage

🚀 You're all set! I'm now an expert in YOUR stack.
```

## Error Handling

### If user_profile.json already exists:
```
⚠️  I found an existing SkillForge profile!

Created: 2025-01-20
Role: Full-Stack Developer
Tech Stack: Next.js, React, Supabase...

Would you like to:
1. Keep existing and update it
2. Start fresh (overwrites current profile)
3. Cancel
```

### If project has no config files:
```
🔍 I couldn't auto-detect any technologies in this directory.

No problem! I'll ask you about your tech stack manually.
```

Continue with questions but skip showing detected section.

### If user cancels mid-wizard:
Save partial progress to `~/.claude/skills/skillforge/data/wizard_session.json` for future resume capability.

## Technical Details

**Directories to create** (if they don't exist):
- `~/.claude/skills/skillforge/`
- `~/.claude/skills/skillforge/data/`

**Detection Logic**:

From `package.json` dependencies:
- `"next"` → Next.js
- `"react"` → React
- `"vue"` → Vue.js
- `"tailwindcss"` → Tailwind CSS
- `"@supabase/supabase-js"` → Supabase
- `"zustand"` → Zustand
- `"@reduxjs/toolkit"` → Redux Toolkit
- `"next-auth"` → NextAuth.js
- `"vitest"` → Vitest
- `"playwright"` → Playwright

From `tsconfig.json` existence → TypeScript

From `requirements.txt` or `pyproject.toml`:
- `django` → Django
- `fastapi` → FastAPI
- `pytest` → pytest

**Package Manager Detection**:
- Check for `pnpm-lock.yaml` → pnpm
- Check for `yarn.lock` → yarn
- Check for `bun.lockb` → bun
- Default → npm

## Example Conversation Flow

### First Time Setup

```
User: /sf:wizard

Claude:
🧙 Welcome to the SkillForge Setup Wizard!

I'll help you create personalized Claude Code skills tailored to YOUR tech stack.

This will take about 3-5 minutes. I'll:
• Auto-detect your technologies
• Ask about your preferences
• Generate a profile for skill generation

Let me scan your project...

📍 Auto-detected in your project:
  ✓ Next.js 15.0.0 (from package.json)
  ✓ React 19 (from package.json)
  ✓ TypeScript 5.3 (from tsconfig.json)
  ✓ Tailwind CSS (from tailwind.config.ts)
  ✓ Supabase (from package.json)

Great! Now let me ask you a few questions to understand your preferences...

[Claude uses AskUserQuestion tool with the 10 questions listed above]

User: [Answers the questions via Claude Code's UI]

Claude:
═══════════════════════════════════════════════════
📋 Your SkillForge Configuration
═══════════════════════════════════════════════════

👤 Role: Full-Stack Developer

🔧 Tech Stack:
   • Frontend: Next.js
   • UI: Tailwind CSS, shadcn/ui
   • State: Zustand
   • Backend: Next.js API Routes
   • Database: Supabase
   • Auth: Supabase Auth
   • Testing: Vitest, Playwright

✨ Preferences:
   • Code Style: TypeScript Strict Mode, ESLint + Prettier
   • Deployment: Vercel

═══════════════════════════════════════════════════
🎉 Setup Complete!
═══════════════════════════════════════════════════

✅ Profile saved to:
   ~/.claude/skills/skillforge/data/user_profile.json

📦 Suggested skills to generate based on your stack:
   1. nextjs-fullstack - Next.js app development
   2. react-components - React component patterns
   3. supabase-integration - Supabase client & auth
   4. tailwind-styling - Tailwind CSS patterns
   5. testing-suite - Vitest + Playwright setup

📋 Next steps:
   • /sf:generate nextjs-fullstack - Generate a specific skill
   • /sf:list - View all available skills
   • /sf:status - Check SkillForge status

💡 Skills will be automatically loaded when you work on tasks
   matching your tech stack!

Would you like me to generate your first skill now?
I recommend starting with "nextjs-fullstack" based on your stack.
```

### Profile Already Exists

```
User: /sf:wizard

Claude:
⚠️  I found an existing SkillForge profile!

Created: 2025-01-20
Role: Full-Stack Developer
Tech Stack: Next.js, React, Supabase, Tailwind CSS

Would you like to update it or start fresh?
```

## Related Commands
- `/sf:generate` - Generate a specific skill without full wizard
- `/sf:update` - Update existing skills with latest docs
- `/sf:list` - List all generated skills
- `/sf:status` - Check SkillForge setup status
- `/sf:reset` - Reset SkillForge to start fresh

## Important Notes

### For Users
- Run `/sf:wizard` in your project directory for best auto-detection
- You can re-run the wizard to update your profile later
- Your preferences are saved and reused for future skills
- All questions can be skipped - use detected defaults when unsure

### For Claude Code
- **NEVER** call `skillforge wizard` via Bash tool
- **ALWAYS** implement the wizard conversationally using Read/Write/AskUserQuestion
- Auto-detect first, then ask questions
- Save to `~/.claude/skills/skillforge/data/user_profile.json`
- Pre-select detected technologies in questions
- Skip questions when answers can be inferred (e.g., skip backend if Frontend Developer)
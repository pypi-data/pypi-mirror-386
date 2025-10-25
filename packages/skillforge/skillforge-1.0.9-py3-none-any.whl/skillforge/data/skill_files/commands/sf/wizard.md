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
3. Ask questions conversationally with numbered options
4. Accept BOTH number selection AND custom text responses
5. Use Write to save the user_profile.json
6. Ask ONE question at a time and wait for response

**QUESTION FORMAT - CRITICAL**:
- Present options numbered 1, 2, 3, etc.
- ALWAYS include option for "Other" or custom text
- Wait for user response after each question
- Accept either the number OR custom text
- Do NOT use AskUserQuestion tool - use normal conversation

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

**CRITICAL**: Ask questions ONE AT A TIME conversationally. Present numbered options and ALWAYS allow custom text input.

**Question 1: Developer Role**
```
🎯 Question 1/10: Developer Role

What type of developer are you?

1. Full-Stack Developer - Work on both frontend and backend
2. Frontend Developer - Focus on UI/UX and client-side code
3. Backend Developer - Focus on APIs, databases, server-side logic
4. DevOps Engineer - Focus on infrastructure, CI/CD, deployment
5. Other - (type your role)

Enter your choice (1-5 or type your role):
```

**Question 2: Frontend Framework** (skip if Backend Developer/DevOps)
```
🎯 Question 2/10: Frontend Framework

Which frontend framework do you primarily use?

1. Next.js - React framework with SSR/SSG
2. React - JavaScript library for UI
3. Vue.js - Progressive JavaScript framework
4. Svelte - Compiled JavaScript framework
5. Angular - Full-featured framework
6. Other - (type framework name)

Enter your choice (1-6 or type framework name):
```

**Question 3: UI Library** (allow multiple - ask user to list numbers or names)
```
🎯 Question 3/10: UI Library

Which UI libraries/frameworks do you use? (can select multiple)

1. Tailwind CSS - Utility-first CSS framework
2. shadcn/ui - Re-usable components built with Radix UI
3. Material-UI (MUI) - React components with Material Design
4. CSS Modules - Scoped CSS files
5. Styled Components - CSS-in-JS
6. None / Other - (type library names)

Enter your choices (e.g., "1, 2" or "Tailwind, shadcn"):
```

**Question 4: State Management** (allow multiple)
```
🎯 Question 4/10: State Management

How do you manage state? (can select multiple)

1. Zustand - Lightweight state management
2. Redux Toolkit - Official Redux toolset
3. Context API - Built-in React state management
4. Server State Only - No client state (server components)
5. Jotai - Primitive and flexible state
6. Other - (type state management tools)

Enter your choices (e.g., "1, 3" or "Zustand, Context API"):
```

**Question 5: Backend Framework** (skip if Frontend Developer)
```
🎯 Question 5/10: Backend Framework

Which backend framework do you use?

1. Next.js API Routes - Built into Next.js
2. Express.js - Minimal Node.js framework
3. FastAPI - Modern Python framework
4. Django - Full-featured Python framework
5. NestJS - Progressive Node.js framework
6. Other - (type framework name)

Enter your choice (1-6 or type framework name):
```

**Question 6: Database** (allow multiple)
```
🎯 Question 6/10: Database

Which database(s) do you work with? (can select multiple)

1. Supabase - PostgreSQL with real-time & auth
2. PostgreSQL - Relational database
3. MongoDB - NoSQL document database
4. Redis - In-memory cache/database
5. MySQL - Relational database
6. Other - (type database names)

Enter your choices (e.g., "1" or "Supabase, Redis"):
```

**Question 7: Authentication** (allow multiple)
```
🎯 Question 7/10: Authentication

How do you handle authentication? (can select multiple)

1. Supabase Auth - Built into Supabase
2. NextAuth.js - Authentication for Next.js
3. Clerk - Complete user management
4. Custom JWT - Roll your own JWT auth
5. Auth0 - Authentication as a service
6. Other - (type auth solution)

Enter your choices (e.g., "1" or "Custom JWT"):
```

**Question 8: Testing Tools** (allow multiple)
```
🎯 Question 8/10: Testing Tools

Which testing tools do you use? (can select multiple)

1. Vitest - Fast unit test framework
2. Jest - JavaScript testing framework
3. Playwright - End-to-end testing
4. Cypress - E2E testing framework
5. Testing Library - React/Vue/etc testing utilities
6. None / Other - (type testing tools)

Enter your choices (e.g., "1, 3" or "Vitest, Playwright"):
```

**Question 9: Code Style** (allow multiple)
```
🎯 Question 9/10: Code Style

What are your code style preferences? (can select multiple)

1. TypeScript Strict Mode - Strictest type checking
2. ESLint + Prettier - Linting and formatting
3. Functional Programming - Pure functions, immutability
4. Object-Oriented - Classes and inheritance
5. Minimal/Flexible - No strict rules
6. Other - (describe your style)

Enter your choices (e.g., "1, 2, 3" or "Strict TypeScript, FP"):
```

**Question 10: Deployment** (allow multiple)
```
🎯 Question 10/10: Deployment

Where do you deploy your applications? (can select multiple)

1. Vercel - Optimized for Next.js
2. Netlify - JAMstack hosting
3. AWS - Amazon Web Services
4. Docker - Containerized deployment
5. Railway - Simple deployment platform
6. Other - (type deployment platforms)

Enter your choices (e.g., "1" or "Vercel, AWS"):
```

### Step 3: Parse User Responses

**CRITICAL**: Parse user responses flexibly:
- If user enters a number (e.g., "1") → map to corresponding option
- If user enters multiple numbers (e.g., "1, 3") → map to multiple options
- If user enters text (e.g., "Custom JWT") → use as-is
- If user enters mix (e.g., "1, Custom Auth") → combine both

Example parsing logic:
```javascript
// User input: "1, 3"
// Options: ["Zustand", "Redux Toolkit", "Context API", "Server State Only"]
// Result: ["Zustand", "Context API"]

// User input: "Zustand, Context API"
// Result: ["Zustand", "Context API"]

// User input: "1, Custom State"
// Result: ["Zustand", "Custom State"]
```

### Step 4: Generate & Save Profile

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

### Step 5: Determine & Suggest Skills

**After saving profile, suggest skills to generate** based on tech_stack:

```
🚀 Based on your tech stack, I recommend generating these skills:

📦 Recommended Skills:
   1. nextjs-fullstack - Next.js app development with App Router
   2. supabase-integration - Supabase client, auth & database
   3. tailwind-styling - Tailwind CSS patterns & components
   4. testing-suite - Vitest + Playwright testing setup

💡 Would you like me to generate these skills now?

Options:
1. Generate all recommended skills (3-5 minutes)
2. Let me choose which skills to generate
3. Skip for now (generate later with /sf:generate)

Enter your choice (1-3):
```

### Step 6: Generate Skills (if user chooses)

If user chooses to generate skills:

1. **Show what will be generated**:
```
🚀 Generating 4 skills based on your tech stack...

This will take about 3-5 minutes. I'll fetch the latest documentation
and create personalized skills tailored to your preferences.
```

2. **Generate each skill with FULL AI-powered generation**:

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

### Step 7: Completion Message

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

Enter your choice (1-3):
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
• Generate skills based on your stack

Let me scan your project...

📍 Auto-detected in your project:
  ✓ Next.js 15.0.0 (from package.json)
  ✓ React 19 (from package.json)
  ✓ TypeScript 5.3 (from tsconfig.json)
  ✓ Tailwind CSS (from tailwind.config.ts)
  ✓ Supabase (from package.json)

Great! Now let me ask you a few questions to understand your preferences...

🎯 Question 1/10: Developer Role

What type of developer are you?

1. Full-Stack Developer - Work on both frontend and backend
2. Frontend Developer - Focus on UI/UX and client-side code
3. Backend Developer - Focus on APIs, databases, server-side logic
4. DevOps Engineer - Focus on infrastructure, CI/CD, deployment
5. Other - (type your role)

Enter your choice (1-5 or type your role):

User: 1

Claude:
Great! You're a Full-Stack Developer.

🎯 Question 2/10: Frontend Framework

Which frontend framework do you primarily use?
(I detected Next.js - just press Enter to use it, or choose another)

1. Next.js - React framework with SSR/SSG ✓ detected
2. React - JavaScript library for UI
3. Vue.js - Progressive JavaScript framework
4. Svelte - Compiled JavaScript framework
5. Angular - Full-featured framework
6. Other - (type framework name)

Enter your choice (1-6 or type framework name):

User: [presses Enter or types "1"]

Claude:
Perfect! Using Next.js.

🎯 Question 3/10: UI Library
...
[continues through all questions]
...

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

✅ Profile saved!

🚀 Based on your tech stack, I recommend generating these skills:

📦 Recommended Skills:
   1. nextjs-fullstack - Next.js app development with App Router
   2. supabase-integration - Supabase client, auth & database
   3. tailwind-styling - Tailwind CSS patterns & components
   4. testing-suite - Vitest + Playwright testing setup

💡 Would you like me to generate these skills now?

Options:
1. Generate all recommended skills (3-5 minutes)
2. Let me choose which skills to generate
3. Skip for now (generate later with /sf:generate)

Enter your choice (1-3):

User: 1

Claude:
🚀 Generating 4 skills based on your tech stack...

🔄 Generating nextjs-fullstack...
   📚 Fetching Next.js documentation...
   ✅ Generated: nextjs-fullstack (3,245 tokens)

🔄 Generating supabase-integration...
   📚 Fetching Supabase documentation...
   ✅ Generated: supabase-integration (2,156 tokens)

...

═══════════════════════════════════════════════════
🎉 SkillForge Setup Complete!
═══════════════════════════════════════════════════

✅ Generated 4 skills with latest documentation
📊 Total: 9,631 tokens

🚀 You're all set! I'm now an expert in YOUR stack.
```

### Profile Already Exists

```
User: /sf:wizard

Claude:
⚠️  I found an existing SkillForge profile!

Created: 2025-01-20
Role: Full-Stack Developer
Tech Stack: Next.js, React, Supabase, Tailwind CSS

Would you like to:
1. Keep existing and update it
2. Start fresh (overwrites current profile)
3. Cancel

Enter your choice (1-3):
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
- You can enter numbers (1, 2, 3) OR type custom responses

### For Claude Code
- **NEVER** call `skillforge wizard` via Bash tool
- **NEVER** use AskUserQuestion tool - use normal conversation
- **ALWAYS** ask ONE question at a time and wait for response
- **ALWAYS** accept BOTH numbered selections AND custom text
- Auto-detect first, then ask questions
- Save to `~/.claude/skills/skillforge/data/user_profile.json`
- Pre-select detected technologies in questions
- Skip questions when answers can be inferred (e.g., skip backend if Frontend Developer)
- Parse user responses flexibly (numbers, text, or mix)

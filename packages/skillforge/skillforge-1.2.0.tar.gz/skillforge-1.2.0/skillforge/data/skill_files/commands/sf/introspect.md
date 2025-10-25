---
name: introspect
description: Analyze current project and suggest appropriate skills to generate
---

# /sf:introspect - Project Analysis

## Purpose
Analyzes your current project to understand the tech stack and suggest which skills would be most useful.

## Syntax
```
/sf:introspect [--auto-generate] [--export]
```


## Implementation

When user runs `/sf:introspect`, Claude Code should execute:

```bash
skillforge introspect
```

**Note**: Optional: --project /path/to/project

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Example Output

```
User: /sf:introspect

Output:
🔍 Analyzing current project...
═══════════════════════════════════════════════════════════

PROJECT ANALYSIS
───────────────────────────────────────────────────────────
  Location: /Users/me/projects/my-app
  Type: Fullstack web application

DETECTED TECHNOLOGIES
───────────────────────────────────────────────────────────
  Frontend:
    ✓ Next.js 15.0.0 (package.json)
    ✓ React 19.0.0 (package.json)
    ✓ Tailwind CSS 4.0 (tailwind.config.js)
    ✓ TypeScript 5.3 (tsconfig.json)

  State Management:
    ✓ Zustand (detected in imports)

  Backend:
    ✓ Next.js API Routes (detected /app/api/)
    ✓ Supabase Client (package.json)

  Database:
    ✓ Supabase/PostgreSQL (.env references)

  Testing:
    ✓ Vitest (vitest.config.ts)
    ✓ Playwright (playwright.config.ts)

  Other:
    ✓ Zod validation (package.json)
    ✓ React Hook Form (package.json)

RECOMMENDED SKILLS
───────────────────────────────────────────────────────────
  High Priority (Core to your stack):
    1. nextjs-fullstack - Next.js patterns and best practices
    2. supabase-integration - Supabase auth, DB, storage
    3. testing-suite - Vitest + Playwright setup

  Medium Priority (Would be helpful):
    4. react-components - Advanced React patterns
    5. tailwind-styling - Tailwind utilities and patterns
    6. typescript-patterns - TypeScript best practices

  Low Priority (Nice to have):
    7. git-workflow - Git branching and commits
    8. deployment-pipeline - Vercel deployment

EXISTING SKILLS
───────────────────────────────────────────────────────────
  ✓ You already have: nextjs-fullstack, testing-suite

  Missing:
    ✗ supabase-integration
    ✗ react-components
    ✗ tailwind-styling

RECOMMENDATIONS
───────────────────────────────────────────────────────────
  Suggested action:
    /sf:generate supabase-integration
    /sf:generate react-components
    /sf:generate tailwind-styling

  Or generate all at once:
    /sf:introspect --auto-generate

═══════════════════════════════════════════════════════════
💡 Run /sf:wizard to generate all recommended skills
📊 Your project uses 8 technologies, 5 skills recommended
```

## Auto-Generate

```
User: /sf:introspect --auto-generate

Output:
🔍 Analyzing project... Done!
🚀 Auto-generating recommended skills...

Generating 3 skills:
  ✅ supabase-integration (2,156 tokens)
  ✅ react-components (1,920 tokens)
  ✅ tailwind-styling (1,687 tokens)

Complete! 3 skills generated.
Restart Claude Code to use new skills.
```

## Options
- `--auto-generate` - Automatically generate suggested skills
- `--export` - Export analysis to JSON
- `--minimal` - Show only essential recommendations

## Related Commands
- `/sf:wizard` - Full setup with customization
- `/sf:generate` - Generate specific skills
- `/sf:list` - See existing skills

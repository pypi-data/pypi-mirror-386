---
name: wizard
description: Launch interactive skill generation wizard. Analyzes your tech stack and generates personalized skills.
---

# /sf:wizard - Interactive Skill Generation Wizard

## Purpose
Interactive wizard that guides you through generating personalized skills for your tech stack. Perfect for first-time setup or adding new technology stacks to your workflow.

## When to Use
- **First time setup** - Initialize SkillForge for the first time
- **Adding new tech stack** - Expand your skills with new frameworks
- **Onboarding new project** - Set up skills for a new codebase
- **User requests setup/configuration** - When explicitly asked to configure

## Behavior

### Step 1: Welcome & Auto-Detection
1. Greet user warmly
2. Explain what the wizard will do
3. Auto-detect tech stack from current directory by scanning:
   - `package.json` (Node.js/frontend frameworks)
   - `requirements.txt`, `pyproject.toml` (Python)
   - `Gemfile` (Ruby)
   - `composer.json` (PHP)
   - `go.mod` (Go)
   - Configuration files (`.eslintrc`, `tsconfig.json`, etc.)
4. Show detected technologies with versions
5. Ask for confirmation

### Step 2: Interactive Questionnaire
Ask questions about user preferences:

1. **Role** - What type of developer? (Frontend, Backend, Fullstack, etc.)
2. **Frontend Framework** - React, Vue, Svelte, Angular, etc.
3. **UI Library** - Tailwind, Material-UI, shadcn/ui, etc.
4. **State Management** - Redux, Zustand, Jotai, Context API, etc.
5. **Backend Framework** - Express, FastAPI, Django, Next.js API, etc.
6. **Database** - PostgreSQL, MongoDB, MySQL, Supabase, etc.
7. **Auth Provider** - NextAuth, Supabase Auth, Auth0, Clerk, etc.
8. **Testing Tools** - Jest, Vitest, Pytest, Playwright, Cypress, etc.
9. **Code Style Preferences** - Naming conventions, import style, error handling
10. **Workflow Preferences** - Commit format, branch naming, testing workflow
11. **Package Manager** - npm, yarn, pnpm, bun
12. **Deployment Target** - Vercel, Netlify, AWS, Docker, etc.

### Step 3: Generate Profile
1. Show comprehensive summary of all answers
2. Display what skills will be generated
3. Ask for final confirmation
4. Generate `user_profile.json` with all settings
5. Save to `~/.claude/skills/skillforge/data/`

### Step 4: Generate Skills
For each technology in the stack:
1. Determine appropriate skill type
2. Fetch latest documentation via Context7 MCP
3. Generate customized SKILL.md with user preferences
4. Create supporting files if needed
5. Save to `~/.claude/skills/<skill-name>.md`
6. Show progress indicator

### Step 5: Completion
1. Show list of all generated skills with paths
2. Provide summary statistics (skills created, token estimate)
3. Explain next steps for using the skills
4. Suggest restarting Claude Code to activate skills
5. Mention related commands for ongoing management

## Error Handling

### User Interrupts
- **Auto-save state** - Save progress every step
- **Allow resume** - Next run continues from last step
- **Clear option** - Offer to start fresh

### Network Errors
- **Use cached docs** - Fall back to cached documentation
- **Continue anyway** - Generate with built-in templates
- **Retry option** - Allow user to retry fetch

### Generation Failures
- **Rollback** - Remove partially created files
- **Show detailed error** - Help user debug issue
- **Continue with others** - Don't stop entire process

### Missing Profile
- **Detect scenario** - Check if user_profile.json exists
- **Offer to run wizard** - Suggest completing wizard first
- **Provide default** - Use sensible defaults if user insists


## Implementation

When user runs `/sf:wizard`, Claude Code should execute:

```bash
skillforge wizard
```

**Important**: This command runs interactively in the terminal. Claude should:
1. Use the Bash tool to execute the command
2. Allow the user to interact with the command directly
3. Not interrupt or try to automate the interactive prompts

## Example Usage

### Basic Usage

```
User: /sf:wizard

Output:
🧙 SkillForge Setup Wizard
═══════════════════════════════════════════════════════════

Welcome! I'll help you create personalized skills for your tech stack.

📍 Auto-detected in current directory:
  ✓ Next.js 15.0.0 (package.json)
  ✓ Tailwind CSS 4.0 (tailwind.config.js)
  ✓ TypeScript 5.3 (tsconfig.json)
  ✓ Supabase (detected from imports)
  ✓ Zod 3.22 (package.json)

Is this correct? [Y/n] y

Great! Let's configure your preferences...

1/12: What's your primary role?
  1) Frontend Developer
  2) Backend Developer
  3) Fullstack Developer
  4) DevOps Engineer
  5) Other

Choice [3]: 3

2/12: Which state management do you prefer?
  1) Redux Toolkit
  2) Zustand
  3) Jotai
  4) Context API
  5) None/Server State Only

Choice [2]: 2

...

═══════════════════════════════════════════════════════════
📋 Summary of Your Setup
═══════════════════════════════════════════════════════════

Role: Fullstack Developer
Frontend: Next.js 15 + React 19
UI: Tailwind CSS 4 + shadcn/ui
State: Zustand
Backend: Next.js API Routes
Database: Supabase (PostgreSQL)
Auth: Supabase Auth
Testing: Vitest + Playwright
Style: camelCase, grouped imports, try/catch
Workflow: Conventional commits, feature/ branches

Skills to generate:
  1. nextjs-fullstack
  2. react-components
  3. supabase-integration
  4. tailwind-styling
  5. testing-suite

Proceed? [Y/n] y

🚀 Generating 5 skills...

✅ Generated: ~/.claude/skills/nextjs-fullstack.md (2,845 tokens)
✅ Generated: ~/.claude/skills/react-components.md (1,920 tokens)
✅ Generated: ~/.claude/skills/supabase-integration.md (2,156 tokens)
✅ Generated: ~/.claude/skills/tailwind-styling.md (1,687 tokens)
✅ Generated: ~/.claude/skills/testing-suite.md (2,234 tokens)

═══════════════════════════════════════════════════════════
🎉 Setup complete!
═══════════════════════════════════════════════════════════

📚 5 skills generated (10,842 tokens total)
💡 Restart Claude Code to activate your new skills.

📋 Next steps:
  • /sf:list - View all your skills
  • /sf:analyze - See usage patterns
  • /sf:optimize - Optimize your skills
```

### Resume Interrupted Setup

```
User: /sf:wizard

Output:
🧙 SkillForge Setup Wizard
═══════════════════════════════════════════════════════════

I found an incomplete setup from earlier.

Progress: 6/12 questions answered
Last step: Testing tools selection

Would you like to:
  1) Resume from where you left off
  2) Start fresh
  3) Cancel

Choice [1]: 1

Resuming...

7/12: What testing tools do you use?
...
```

## Related Commands
- `/sf:generate` - Generate a specific skill without full wizard
- `/sf:update` - Update existing skills with latest docs
- `/sf:list` - List all generated skills
- `/sf:status` - Check SkillForge setup status
- `/sf:reset` - Reset SkillForge to start fresh

## Tips
- Run wizard in your project directory for best auto-detection
- You can re-run wizard to add more skills later
- Your preferences are saved and reused for future skills
- Use `/sf:config` to modify preferences without re-running wizard

## Troubleshooting

**Nothing detected?**
- Ensure you're in a project directory with config files
- Wizard can still run without auto-detection

**Wrong framework detected?**
- You can correct it in the questionnaire
- Detection is just a helpful starting point

**Too many questions?**
- All questions are optional with smart defaults
- Press Enter to accept the suggested default

**Skills not appearing?**
- Restart Claude Code after generation
- Check `~/.claude/skills/` directory for files
- Run `/sf:list` to verify
---
name: generate
description: Generate a specific skill without running full wizard. Syntax - /sf:generate <skill-type> [options]
---

# /sf:generate - Generate Specific Skill

## Purpose
Generate a single skill quickly without going through the full wizard. Perfect for adding one skill at a time or regenerating an existing skill with updated documentation.

## Syntax
```
/sf:generate <skill-type> [--force] [--preview] [--no-docs]
```

## Skill Types

### Frontend Frameworks
- `nextjs-fullstack` - Next.js fullstack development (App Router, API routes, Server Components)
- `react-spa` - React single-page application (with routing, state management)
- `vue-app` - Vue.js application (Composition API, Pinia, Vue Router)
- `svelte-app` - Svelte/SvelteKit application
- `angular-app` - Angular application

### Backend Frameworks
- `express-api` - Express.js REST API
- `fastapi-api` - FastAPI Python REST API
- `django-api` - Django REST Framework API
- `nestjs-api` - NestJS API
- `flask-api` - Flask Python API

### Database & Services
- `supabase-integration` - Supabase (Auth, Database, Storage, Realtime)
- `mongodb-integration` - MongoDB database integration
- `postgresql-integration` - PostgreSQL database operations
- `prisma-orm` - Prisma ORM integration
- `firebase-integration` - Firebase (Auth, Firestore, Functions)

### Testing & DevOps
- `testing-suite` - Comprehensive testing setup (unit, integration, e2e)
- `e2e-testing` - End-to-end testing with Playwright/Cypress
- `git-workflow` - Git workflow and best practices
- `deployment-pipeline` - CI/CD and deployment automation
- `docker-setup` - Docker and containerization

### UI & Styling
- `tailwind-styling` - Tailwind CSS styling patterns
- `component-library` - Component library setup (shadcn/ui, MUI, etc.)
- `responsive-design` - Responsive design patterns

### Additional
- `auth-implementation` - Authentication implementation
- `api-integration` - External API integration patterns
- `error-handling` - Error handling and logging
- `performance-optimization` - Performance optimization techniques

## Options

### `--force`
Overwrite existing skill without prompting

```bash
/sf:generate nextjs-fullstack --force
```

### `--preview`
Show what would be generated without creating files. Useful for checking before committing to generation.

```bash
/sf:generate react-spa --preview
```

### `--no-docs`
Skip documentation fetching and use cached or built-in templates. Faster but may not have latest features.

```bash
/sf:generate supabase-integration --no-docs
```

## Behavior

### Generation Process

1. **Validate Skill Type**
   - Check if skill type is recognized
   - Show available types if invalid

2. **Check Existing Skill**
   - Look for existing skill with same name
   - Prompt for confirmation if found (unless --force)

3. **Load User Profile**
   - Read from `~/.claude/skills/skillforge/data/user_profile.json`
   - Use defaults if profile not found
   - Suggest running `/sf:wizard` if no profile

4. **Fetch Documentation** (unless --no-docs)
   - Use Context7 MCP to get latest docs
   - Cache for 7 days
   - Fall back to built-in templates on failure

5. **Generate SKILL.md**
   - Use appropriate template for skill type
   - Inject user preferences and conventions
   - Include latest best practices
   - Add code examples

6. **Create Supporting Files**
   - Add template snippets if applicable
   - Create example configurations
   - Set up directory structure hints

7. **Validate Output**
   - Check YAML frontmatter validity
   - Verify required sections present
   - Estimate token count
   - Ensure content quality

8. **Show Summary**
   - Display file path
   - Show token count
   - List key features included
   - Suggest next steps


## Implementation

When user runs `/sf:generate`, Claude Code should execute:

```bash
skillforge generate
```

**Note**: Takes skill_type as argument and optional flags (--force, --preview, --no-docs)

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Examples

### Basic Generation

```
User: /sf:generate nextjs-fullstack

Output:
🔧 Generating nextjs-fullstack skill...

📚 Fetching latest Next.js documentation...
✓ Context7 lookup successful (Next.js 15.0.0)

✍️  Generating skill with your preferences:
  • TypeScript enabled
  • App Router patterns
  • Server Components
  • Tailwind CSS integration
  • Your code style (camelCase, grouped imports)

✅ Generated: ~/.claude/skills/nextjs-fullstack.md

📊 Summary:
  • Token count: 2,845 tokens
  • Sections: 12
  • Code examples: 15
  • Version: Next.js 15.0.0

💡 Restart Claude Code to use this skill
```

### Preview Mode

```
User: /sf:generate react-spa --preview

Output:
🔍 Preview: react-spa skill

Would generate: ~/.claude/skills/react-spa.md

Estimated content:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTIONS:
  1. Core React Patterns (React 19)
  2. Component Architecture
  3. State Management (Zustand)
  4. Routing (React Router v6)
  5. Data Fetching (React Query)
  6. Styling (Tailwind CSS)
  7. Forms (React Hook Form + Zod)
  8. Testing (Vitest + Testing Library)
  9. Performance Optimization
  10. Code Splitting
  11. Error Boundaries
  12. Best Practices

CODE EXAMPLES:
  • Component structure (5 examples)
  • Hooks usage (8 examples)
  • State management (4 examples)
  • Routing patterns (3 examples)
  • Form handling (4 examples)

Estimated token count: ~1,920 tokens

To create this skill, run:
  /sf:generate react-spa
```

### Force Overwrite

```
User: /sf:generate supabase-integration --force

Output:
⚠️  Existing skill found: ~/.claude/skills/supabase-integration.md
🔄 Overwriting with --force flag...

📚 Fetching latest Supabase documentation...
✓ Documentation updated

✅ Generated: ~/.claude/skills/supabase-integration.md
   (replaced previous version)

Changes:
  • Updated to Supabase v2.38
  • Added new Realtime features
  • Improved error handling examples
  • Updated authentication flows
```

### Skip Documentation Fetch

```
User: /sf:generate mongodb-integration --no-docs

Output:
🔧 Generating mongodb-integration skill...

⚡ Using cached/built-in templates (--no-docs)

✅ Generated: ~/.claude/skills/mongodb-integration.md

⚠️  Note: Documentation not fetched. May not include latest features.
    Run without --no-docs for latest docs.
```

## Error Handling

### Unknown Skill Type

```
User: /sf:generate unknown-skill

Output:
❌ Error: Unknown skill type 'unknown-skill'

Available skill types:
  Frontend: nextjs-fullstack, react-spa, vue-app, svelte-app
  Backend: express-api, fastapi-api, django-api, nestjs-api
  Database: supabase-integration, mongodb-integration, postgresql-integration
  Testing: testing-suite, e2e-testing
  DevOps: git-workflow, deployment-pipeline, docker-setup
  UI: tailwind-styling, component-library
  Other: auth-implementation, api-integration

Syntax: /sf:generate <skill-type> [--force] [--preview] [--no-docs]

Examples:
  /sf:generate nextjs-fullstack
  /sf:generate react-spa --preview
```

### Skill Already Exists

```
User: /sf:generate nextjs-fullstack

Output:
⚠️  Skill already exists: ~/.claude/skills/nextjs-fullstack.md

Options:
  1) Overwrite with new version
  2) Keep existing and cancel
  3) Preview changes first

Choice [2]: 1

🔄 Regenerating nextjs-fullstack...
✅ Done!
```

### Missing User Profile

```
User: /sf:generate nextjs-fullstack

Output:
⚠️  No user profile found

I can generate a basic skill, but it won't be customized to your preferences.

Recommended: Run /sf:wizard first to set up your profile

Options:
  1) Run /sf:wizard now
  2) Generate with defaults anyway
  3) Cancel

Choice [1]: 1

🧙 Launching SkillForge wizard...
```

### Network Error

```
User: /sf:generate nextjs-fullstack

Output:
🔧 Generating nextjs-fullstack skill...

📚 Fetching latest Next.js documentation...
❌ Network error: Unable to reach Context7

Fallback options:
  1) Use cached documentation (Next.js 14.2, cached 3 days ago)
  2) Use built-in templates
  3) Retry fetch
  4) Cancel

Choice [1]: 1

✓ Using cached documentation
✅ Generated: ~/.claude/skills/nextjs-fullstack.md

⚠️  Note: Using cached docs. Run again later for latest features.
```

## Related Commands
- `/sf:wizard` - Run full setup wizard
- `/sf:update` - Update existing skill with latest docs
- `/sf:list` - View all generated skills
- `/sf:analyze` - Analyze skill usage
- `/sf:optimize` - Optimize and merge skills

## Tips

- **Use preview first** - Check what will be generated before creating
- **Update regularly** - Regenerate skills periodically for latest docs
- **Customize after** - You can manually edit generated skills
- **Force when needed** - Use --force to quickly update stale skills
- **Profile matters** - User profile ensures consistency across skills

## Quick Reference

```bash
# Generate with latest docs
/sf:generate nextjs-fullstack

# Preview first
/sf:generate react-spa --preview

# Overwrite existing
/sf:generate supabase-integration --force

# Fast generation (cached)
/sf:generate testing-suite --no-docs

# Combine options
/sf:generate vue-app --force --no-docs
```

## Troubleshooting

**Generation is slow?**
- Use `--no-docs` flag to skip documentation fetch
- Docs are cached for 7 days, subsequent runs are faster

**Skill not working?**
- Restart Claude Code after generation
- Verify file was created: `ls ~/.claude/skills/`
- Check skill with `/sf:list`

**Want different content?**
- Manually edit the generated `.md` file
- Or run `/sf:wizard` to update preferences, then regenerate

**Need custom skill type?**
- Manually create skill in `~/.claude/skills/`
- Or request new skill type as feature

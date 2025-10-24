---
name: update
description: Update existing skills with latest documentation and best practices
---

# /sf:update - Update Skills

## Purpose
Update one or more skills with the latest documentation, framework versions, and best practices.

## Syntax
```
/sf:update [skill-name | --all] [--force] [--preview]
```


## Implementation

When user runs `/sf:update`, Claude Code should execute:

```bash
skillforge update
```

**Note**: Optional flags: --skill SKILL_NAME, --all

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Examples

### Update Single Skill
```
/sf:update nextjs-fullstack

Output:
🔄 Updating nextjs-fullstack...

📚 Fetching latest documentation...
✓ Next.js 15.0.0 docs retrieved

Changes detected:
  • Added: Server Actions patterns
  • Added: Improved caching strategies
  • Updated: App Router best practices
  • Updated: 8 code examples

Apply update? [Y/n] y

✅ Updated: nextjs-fullstack.md
   Version: 14.2.5 → 15.0.0
   Token count: 2,845 → 2,967 (+122)
```

### Update All Skills
```
/sf:update --all

Output:
🔄 Updating all skills...

Checking 8 skills for updates...

Updates available:
  1. nextjs-fullstack (Next.js 14.2 → 15.0)
  2. supabase-integration (Supabase 2.36 → 2.38)
  3. testing-suite (Vitest 1.0 → 1.2)

Update all? [Y/n] y

✅ Updated 3 skills
⏭ 5 skills already current
```

### Preview Changes
```
/sf:update nextjs-fullstack --preview

Output:
🔍 Preview: nextjs-fullstack update

Current: Next.js 14.2.5
Available: Next.js 15.0.0

New features:
  • Server Actions
  • Improved caching
  • Partial prerendering

Would add ~120 tokens

To apply: /sf:update nextjs-fullstack
```

## Options
- `--all` - Update all skills at once
- `--force` - Update even if no changes detected
- `--preview` - Show what would change

## Related Commands
- `/sf:generate` - Regenerate a skill from scratch
- `/sf:optimize` - Optimize along with update
- `/sf:analyze` - See which skills need updates

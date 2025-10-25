---
name: list
description: List all available skills with key information
---

# /sf:list - List Skills

## Purpose
Quick overview of all skills in your collection.

## Syntax
```
/sf:list [--detailed] [--usage] [--filter=<category>]
```


## Implementation

When user runs `/sf:list`, Claude Code should execute:

```bash
skillforge list
```

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Example Output

```
User: /sf:list

Output:
📋 Your Skills
═══════════════════════════════════════════════════════════

SKILLFORGE GENERATED (5)
───────────────────────────────────────────────────────────
  ✓ nextjs-fullstack          2,845 tokens  Updated 2d ago
  ✓ react-components          1,920 tokens  Updated 3d ago
  ✓ supabase-integration      2,156 tokens  Updated 5d ago
  ✓ testing-suite             2,234 tokens  Updated 18d ago ⚠️
  ✓ git-workflow              1,687 tokens  Updated 12d ago

NATIVE ANTHROPIC (3)
───────────────────────────────────────────────────────────
  • python-expert
  • web-development
  • debugging-assistant

═══════════════════════════════════════════════════════════
Total: 8 skills  |  SkillForge: 10,842 tokens
```

## Options
- `--detailed` - Show full paths and descriptions
- `--usage` - Include usage statistics
- `--filter=frontend` - Filter by category

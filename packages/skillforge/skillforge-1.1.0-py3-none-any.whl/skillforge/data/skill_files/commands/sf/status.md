---
name: status
description: Show SkillForge system status and configuration
---

# /sf:status - System Status

## Purpose
Check SkillForge installation, configuration, and system health.

## Syntax
```
/sf:status [--verbose]
```


## Implementation

When user runs `/sf:status`, Claude Code should execute:

```bash
skillforge status
```

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Example Output

```
User: /sf:status

Output:
🔍 SkillForge Status
═══════════════════════════════════════════════════════════

INSTALLATION
───────────────────────────────────────────────────────────
  ✓ SkillForge installed
  ✓ Version: 0.0.1-dev
  ✓ Python: 3.11.5
  ✓ Location: ~/.claude/skills/skillforge/

CONFIGURATION
───────────────────────────────────────────────────────────
  ✓ User profile configured
  ✓ Setup completed: Yes
  ✓ Tech stack: Next.js, Supabase, TypeScript
  ✓ Learning enabled: Yes
  ✓ Auto-update: No

SKILLS
───────────────────────────────────────────────────────────
  ✓ SkillForge skills: 5
  ✓ Native skills: 3
  ✓ Total token usage: 10,842 tokens
  ⚠️ 1 skill needs update

LEARNING
───────────────────────────────────────────────────────────
  ✓ Pattern detection active
  ✓ Patterns learned: 3 applied, 1 pending
  ✓ Last learning cycle: 2 days ago
  ✓ Next cycle: ~8 more uses

DATA STORAGE
───────────────────────────────────────────────────────────
  ✓ User profile: 2.4 KB
  ✓ Usage analytics: 18.7 KB
  ✓ Patterns: 5.2 KB
  ✓ Cache: 247 KB (7 docs cached)

HEALTH
───────────────────────────────────────────────────────────
  ✓ Overall health: 94% (7/8 skills healthy)
  ⚠️ 1 warning: testing-suite outdated

═══════════════════════════════════════════════════════════
💡 Run /sf:update testing-suite to fix warning
📊 Run /sf:analyze for detailed insights
```

---
name: reset
description: Reset SkillForge configuration, analytics, or all data
---

# /sf:reset - Reset SkillForge

## Purpose
Reset various aspects of SkillForge to start fresh or troubleshoot issues.

## Syntax
```
/sf:reset [--config | --analytics | --patterns | --cache | --all]
```

## Options

### `--config`
Reset user profile and preferences
```
/sf:reset --config

Output:
⚠️  Reset Configuration

This will:
  • Delete user profile
  • Reset all preferences to defaults
  • Keep skills and analytics intact

Continue? [y/N] y

✓ Configuration reset
💡 Run /sf:wizard to set up again
```

### `--analytics`
Clear usage statistics and tracking data
```
/sf:reset --analytics

Output:
⚠️  Reset Analytics

This will:
  • Clear all usage statistics
  • Remove pattern learning data
  • Keep skills and configuration

Continue? [y/N] y

✓ Analytics cleared
📊 Usage tracking will start fresh
```

### `--patterns`
Remove all learned patterns
```
/sf:reset --patterns

Output:
⚠️  Reset Patterns

This will:
  • Remove all learned patterns
  • Clear pattern applications
  • Keep usage data for re-learning

Continue? [y/N] y

✓ Patterns reset
🧠 Will re-learn from continued usage
```

### `--cache`
Clear documentation cache
```
/sf:reset --cache

Output:
⚠️  Clear Cache

This will:
  • Delete cached documentation (247 KB)
  • Next generation will fetch fresh docs

Continue? [y/N] y

✓ Cache cleared
📚 Will re-fetch docs as needed
```

### `--all`
Complete reset (nuclear option)
```
/sf:reset --all

Output:
🚨 COMPLETE RESET

This will DELETE:
  • User profile and preferences
  • All usage analytics
  • All learned patterns
  • Documentation cache
  • Skill files remain untouched

This cannot be undone!
Type 'RESET' to confirm: RESET

✓ SkillForge reset complete
💡 Run /sf:wizard to set up again
```

## What's NOT Reset

Skills themselves are never deleted by reset commands. They remain in `~/.claude/skills/` unless you manually delete them.

To remove skills:
- Manually delete from `~/.claude/skills/`
- Or selectively remove with file manager

## When to Use

- **--config**: Changed tech stack, want fresh preferences
- **--analytics**: Privacy concerns, want clean slate
- **--patterns**: Patterns seem wrong, want to re-learn
- **--cache**: Docs seem outdated, force refresh
- **--all**: Complete fresh start

## Recovery

No automatic backup is created. If you want to backup:

```bash
# Backup before reset
cp -r ~/.claude/skills/skillforge/data ~/skillforge-backup

# Restore if needed
cp -r ~/skillforge-backup/* ~/.claude/skills/skillforge/data/
```

## Related Commands
- `/sf:wizard` - Re-run setup after reset
- `/sf:status` - Check what would be reset
- `/sf:config` - Modify specific settings without reset


## Implementation

When user runs `/sf:reset`, Claude Code should execute:

```bash
skillforge reset
```

**Note**: Requires confirmation. Use --confirm to skip prompt.

**Important**: This command runs interactively in the terminal. Claude should:
1. Use the Bash tool to execute the command
2. Allow the user to interact with the command directly
3. Not interrupt or try to automate the interactive prompts

---
name: config
description: View and modify SkillForge configuration settings
---

# /sf:config - Configuration

## Purpose
View and modify SkillForge preferences and settings.

## Syntax
```
/sf:config [get|set|list] [key] [value]
```


## Implementation

When user runs `/sf:config`, Claude Code should execute:

```bash
skillforge config
```

**Note**: Usage: skillforge config [KEY] [VALUE]

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Examples

### View All Settings
```
/sf:config list

Output:
⚙️  SkillForge Configuration
═══════════════════════════════════════════════════════════

USER PREFERENCES
───────────────────────────────────────────────────────────
  role: fullstack_developer
  frontend: nextjs
  ui_library: tailwind
  backend: nextjs_api
  database: supabase
  naming_convention: camelCase
  import_style: grouped

LEARNING
───────────────────────────────────────────────────────────
  enabled: true
  auto_apply_patterns: true
  min_confidence: 0.8
  cycle_frequency: 10

OPTIMIZATION
───────────────────────────────────────────────────────────
  auto_optimize: false
  token_budget: 5000

To modify: /sf:config set <key> <value>
```

### Change Setting
```
/sf:config set learning.enabled false

Output:
✓ Updated: learning.enabled = false
  Learning cycles will not run automatically.
```

### View Single Setting
```
/sf:config get naming_convention

Output:
naming_convention: camelCase
```

## Common Settings
- `learning.enabled` - Enable/disable pattern learning
- `learning.auto_apply_patterns` - Auto-apply learned patterns
- `learning.min_confidence` - Minimum confidence for pattern (0.0-1.0)
- `optimization.auto_optimize` - Auto-optimize skills
- `naming_convention` - Preferred naming style
- `import_style` - Preferred import organization

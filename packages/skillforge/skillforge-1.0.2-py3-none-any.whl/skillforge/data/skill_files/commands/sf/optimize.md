---
name: optimize
description: Optimize skills by merging similar ones, removing redundancies, and improving token efficiency
---

# /sf:optimize - Optimize Skills

## Purpose
Applies the optimization suggestions from `/sf:analyze` to improve your skill collection by:
- Merging similar skills
- Removing redundancies
- Updating outdated documentation
- Compressing verbose content
- Restructuring for better organization

## Syntax
```
/sf:optimize [--auto] [--merge] [--compress] [--preview]
```

## Options

### `--auto`
Automatically apply all safe optimizations without prompts

### `--merge`
Focus only on merging similar skills

### `--compress`
Focus only on token optimization

### `--preview`
Show what would be optimized without making changes

## Behavior

1. **Analyze** - Run optimization analysis
2. **Categorize** - Group suggestions by priority
3. **Present** - Show optimization opportunities
4. **Confirm** - Ask for user approval (unless --auto)
5. **Execute** - Apply approved optimizations
6. **Validate** - Verify all changes
7. **Report** - Show results and token savings


## Implementation

When user runs `/sf:optimize`, Claude Code should execute:

```bash
skillforge optimize
```

**Note**: Optional flags: --skill SKILL_NAME, --all

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Examples

### Interactive Optimization

```
User: /sf:optimize

Output:
🔧 SkillForge Optimizer
═══════════════════════════════════════════════════════════

Analyzing skills for optimization opportunities...

Found 5 optimization opportunities (potential savings: 2,450 tokens)

HIGH PRIORITY (2)
───────────────────────────────────────────────────────────
  1. MERGE: react-spa + react-vite
     Overlap: 82%
     Token savings: 1,200 tokens
     Recommendation: High overlap, safe to merge

  2. UPDATE: nextjs-fullstack
     Current: Next.js 14.2.5
     Available: Next.js 15.0.0
     Impact: New features, improved performance

MEDIUM PRIORITY (2)
───────────────────────────────────────────────────────────
  3. COMPRESS: supabase-integration
     Current: 2,156 tokens
     Target: 1,800 tokens
     Savings: 356 tokens (verbose sections detected)

  4. REMOVE: tailwind-styling
     Usage: 0 uses in 30 days
     Savings: 687 tokens
     Can be consolidated into other skills

LOW PRIORITY (1)
───────────────────────────────────────────────────────────
  5. RESTRUCTURE: testing-suite
     Add missing YAML frontmatter
     Improve section organization

Apply optimizations? [Y/n/selective] selective

Which optimizations to apply? (1,2,3,4,5 or ranges like 1-3)
Selection: 1,2,3

Applying selected optimizations...

✅ Merged react-spa + react-vite → react-fullstack.md
   Saved: 1,200 tokens

✅ Updated nextjs-fullstack to Next.js 15.0.0
   Added: Server Actions, improved caching docs

✅ Compressed supabase-integration
   Saved: 356 tokens

═══════════════════════════════════════════════════════════
OPTIMIZATION COMPLETE
═══════════════════════════════════════════════════════════
  Applied: 3/5 optimizations
  Token savings: 1,556 tokens (12.5%)
  Skills before: 8
  Skills after: 7 (1 merged)

  Updated skills:
    • nextjs-fullstack.md
    • react-fullstack.md (new, merged from 2 skills)
    • supabase-integration.md

💡 Restart Claude Code to use optimized skills
📊 Run /sf:analyze to see updated metrics
```

### Auto Optimization

```
User: /sf:optimize --auto

Output:
🔧 Auto-Optimizing Skills...

Applying safe optimizations automatically...

✓ Compressed 3 verbose skills (saved 894 tokens)
✓ Updated 2 outdated skills
✓ Fixed 1 structure issue

Complete! Saved 894 tokens total.
```

### Preview Mode

```
User: /sf:optimize --preview

Output:
🔍 Optimization Preview

Would apply:
  1. Merge react-spa + react-vite (save 1,200 tokens)
  2. Update nextjs-fullstack to v15.0.0
  3. Compress supabase-integration (save 356 tokens)

Total savings: 1,556 tokens

To apply: /sf:optimize
```

## Related Commands
- `/sf:analyze` - Find optimization opportunities
- `/sf:update` - Update specific skills
- `/sf:list` - View all skills

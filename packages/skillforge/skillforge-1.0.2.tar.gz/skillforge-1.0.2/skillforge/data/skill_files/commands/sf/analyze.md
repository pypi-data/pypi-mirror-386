---
name: analyze
description: Analyze current skills, usage patterns, and optimization opportunities
---

# /sf:analyze - Analyze Skills & Usage

## Purpose
Comprehensive analysis system that provides insights into:
- Existing skills and their health
- Usage patterns and trends
- Optimization opportunities
- Learned patterns and their confidence
- Token usage and efficiency metrics

Perfect for understanding how you're using SkillForge and finding ways to improve.

## Syntax
```
/sf:analyze [--detailed] [--patterns] [--health] [--export]
```

## Options

### `--detailed`
Show detailed analysis for each individual skill

```bash
/sf:analyze --detailed
```

### `--patterns`
Focus output on learned patterns and recommendations

```bash
/sf:analyze --patterns
```

### `--health`
Run comprehensive health check on all skills

```bash
/sf:analyze --health
```

### `--export`
Export analysis report to JSON file

```bash
/sf:analyze --export
```

## Output Sections

### 1. Skills Overview
High-level statistics about your skill collection:
- Total skills installed
- SkillForge-generated vs native Claude skills
- Last update dates for each skill
- Total token usage and efficiency
- Skill distribution by category

### 2. Usage Statistics
Behavioral analysis from actual usage:
- Most frequently used skills
- Success rates per skill
- Common skill combinations
- Usage trends over time (7, 30, 90 days)
- Peak usage times
- Underutilized skills

### 3. Learned Patterns
Intelligence gathered from your workflow:
- Detected patterns (combination, style, workflow)
- Confidence levels for each pattern
- Application status (applied, pending, rejected)
- Pattern effectiveness metrics
- Suggestions for new patterns

### 4. Optimization Opportunities
Actionable improvements:
- Redundancies found between skills
- Merge suggestions with overlap percentages
- Update recommendations for outdated docs
- Token savings potential
- Skills that could be removed
- Missing skills that would be helpful

### 5. Health Check
Quality and maintenance status:
- Skills with outdated documentation
- Broken links or references
- Invalid YAML frontmatter
- Missing required sections
- Dependencies not met
- Performance issues


## Implementation

When user runs `/sf:analyze`, Claude Code should execute:

```bash
skillforge analyze
```

**Note**: Optional flags: --detailed, --days N

**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.

## Example Output

### Basic Analysis

```
User: /sf:analyze

Output:
📊 SkillForge Analysis Report
═══════════════════════════════════════════════════════════
Generated: 2025-10-22 21:30:45
Period: Last 30 days

SKILLS OVERVIEW
───────────────────────────────────────────────────────────
  Total Skills: 8
  SkillForge Generated: 5
  Native Anthropic: 3

  Categories:
    Frontend: 3 skills
    Backend: 2 skills
    DevOps: 2 skills
    Testing: 1 skill

  Token Usage:
    Total: 12,487 tokens
    Average per skill: 1,561 tokens
    Efficiency: Good ✓

  Last Updated:
    nextjs-fullstack: 2 days ago
    supabase-integration: 5 days ago
    git-workflow: 12 days ago
    testing-suite: 18 days ago ⚠️
    react-components: 3 days ago

USAGE STATISTICS (Last 30 days)
───────────────────────────────────────────────────────────
  Total Invocations: 247
  Average per day: 8.2

  Most Used:
    1. nextjs-fullstack     89 uses (36%)  ✓ 94% success
    2. supabase-integration 67 uses (27%)  ✓ 96% success
    3. git-workflow         45 uses (18%)  ✓ 100% success
    4. testing-suite        28 uses (11%)  ✓ 89% success
    5. react-components     18 uses (7%)   ✓ 92% success

  Common Combinations:
    • nextjs-fullstack + supabase-integration (42 times)
    • react-components + tailwind-styling (31 times)
    • testing-suite + git-workflow (24 times)

  Trends:
    ↗ nextjs-fullstack: +15% vs last period
    ↗ supabase-integration: +22% vs last period
    → git-workflow: stable
    ↘ testing-suite: -8% vs last period

  Underutilized:
    ⚠️  tailwind-styling: 0 uses in 30 days
    ⚠️  docker-setup: 2 uses in 60 days

LEARNED PATTERNS (3 active, 1 pending)
───────────────────────────────────────────────────────────
  Applied Patterns:
    ✓ always_use_zod
      Type: style
      Confidence: 0.92 (high)
      Applied to: 4 skills
      Impact: Improved validation consistency
      Based on: 23 observations

    ✓ error_boundary_pattern
      Type: combination
      Confidence: 0.88 (high)
      Applied to: 3 skills
      Impact: Better error handling
      Based on: 18 observations

    ✓ feature_colocation
      Type: workflow
      Confidence: 0.81 (good)
      Applied to: 2 skills
      Impact: Improved organization
      Based on: 15 observations

  Pending Patterns:
    ⏳ server_components_preference
      Type: style
      Confidence: 0.75 (moderate)
      Status: Needs more observations
      Based on: 9 observations
      Action: Continue using, pattern will strengthen

OPTIMIZATION OPPORTUNITIES
───────────────────────────────────────────────────────────
  High Priority:
    ⚡ Merge Suggestion
       Skills: react-spa + react-vite
       Overlap: 82%
       Token savings: ~1,200 tokens
       Recommendation: Run /sf:optimize --merge

    📝 Update Available
       Skill: nextjs-fullstack
       Current: Next.js 14.2.5
       Available: Next.js 15.0.0
       Recommendation: Run /sf:update nextjs-fullstack

  Medium Priority:
    🧹 Remove Unused
       Skill: tailwind-styling
       Usage: 0 uses in 30 days
       Token cost: 687 tokens
       Recommendation: Consider removing or consolidating

    🔄 Refresh Documentation
       Skill: supabase-integration
       Age: 45 days old
       Recommendation: Regenerate for latest features

  Token Optimization:
    • Compress verbose sections: Save ~800 tokens
    • Remove redundant examples: Save ~450 tokens
    • Total potential savings: ~2,450 tokens (20%)

HEALTH CHECK
───────────────────────────────────────────────────────────
  Overall Health: ✅ Good (94% healthy)

  All Clear:
    ✓ All YAML frontmatter valid
    ✓ All required sections present
    ✓ No broken links detected
    ✓ Dependencies satisfied

  Warnings:
    ⚠️  testing-suite: Documentation outdated (90+ days)
       Action: Run /sf:update testing-suite

    ⚠️  docker-setup: Low usage (underutilized)
       Action: Review if still needed

═══════════════════════════════════════════════════════════
RECOMMENDATIONS
───────────────────────────────────────────────────────────
  1. Update nextjs-fullstack to Next.js 15 (/sf:update)
  2. Merge react-spa and react-vite (/sf:optimize --merge)
  3. Consider removing tailwind-styling if not needed
  4. Regenerate testing-suite for latest test tools

💡 Run /sf:optimize to apply recommended optimizations
📊 Run /sf:analyze --export to save this report
```

### Detailed Analysis

```
User: /sf:analyze --detailed

Output:
📊 SkillForge Detailed Analysis
═══════════════════════════════════════════════════════════

SKILL: nextjs-fullstack
───────────────────────────────────────────────────────────
Path: ~/.claude/skills/nextjs-fullstack.md
Token Count: 2,845 tokens
Last Updated: 2 days ago
Health: ✅ Healthy

Usage (30 days):
  Invocations: 89
  Success Rate: 94% (84 successful, 5 failed)
  Avg Duration: 12.3s
  Contexts: 127 (files/components referenced)

Effectiveness:
  ⭐⭐⭐⭐⭐ Excellent
  Patterns Applied: 3
  User Satisfaction: High (based on retry rate)

Content Analysis:
  Sections: 12
  Code Examples: 15
  Best Practices: 23
  Links: 8 (all valid)
  Version: Next.js 15.0.0 ✓ Latest

Recommendations:
  ✓ No issues found
  💡 Consider adding Server Actions examples
  💡 Could expand on caching strategies

───────────────────────────────────────────────────────────
SKILL: supabase-integration
───────────────────────────────────────────────────────────
Path: ~/.claude/skills/supabase-integration.md
Token Count: 2,156 tokens
Last Updated: 5 days ago
Health: ✅ Healthy

Usage (30 days):
  Invocations: 67
  Success Rate: 96% (64 successful, 3 failed)
  Avg Duration: 8.7s
  Contexts: 93

Effectiveness:
  ⭐⭐⭐⭐⭐ Excellent
  Patterns Applied: 2
  User Satisfaction: High

Content Analysis:
  Sections: 10
  Code Examples: 18
  Best Practices: 15
  Links: 12 (all valid)
  Version: Supabase v2.38.0 ✓ Latest

Recommendations:
  ✓ Performing well
  💡 Add Real-time subscription patterns
  ⚠️  Consider adding Edge Functions examples

[... more skills ...]
```

### Patterns Focus

```
User: /sf:analyze --patterns

Output:
🧠 Pattern Analysis Report
═══════════════════════════════════════════════════════════

LEARNED PATTERNS SUMMARY
───────────────────────────────────────────────────────────
  Total Patterns Detected: 4
  Applied: 3
  Pending: 1
  Rejected: 0

PATTERN DETAILS
───────────────────────────────────────────────────────────

Pattern: always_use_zod
  Type: Style Pattern
  Confidence: 0.92 (High)
  Status: ✅ Applied

  Description:
    User consistently uses Zod for validation across
    all form inputs and API endpoints.

  Evidence:
    • 23 observations over 28 days
    • 100% consistency in new code
    • Applied in all React components with forms
    • Applied in all API route handlers

  Applied To:
    ✓ nextjs-fullstack
    ✓ react-components
    ✓ api-integration
    ✓ testing-suite

  Impact:
    • Improved type safety
    • Better error messages
    • Consistent validation patterns
    • Reduced validation bugs by ~40%

  Recommendation:
    ✓ Pattern is working well. Keep using Zod.

───────────────────────────────────────────────────────────

Pattern: error_boundary_pattern
  Type: Combination Pattern
  Confidence: 0.88 (High)
  Status: ✅ Applied

  Description:
    User always implements error boundaries when
    using async components or data fetching.

  Evidence:
    • 18 observations over 21 days
    • Appears in 85% of component hierarchies
    • Often combined with loading states
    • Includes toast notifications

  Applied To:
    ✓ nextjs-fullstack
    ✓ react-components
    ✓ supabase-integration

  Implementation Added:
    • Error boundary component template
    • Try/catch in async operations
    • User-friendly error messages
    • Error logging patterns

  Impact:
    • Better user experience
    • Easier debugging
    • Improved app stability
    • 30% reduction in unhandled errors

  Recommendation:
    ✓ Excellent pattern. Keep applying.

───────────────────────────────────────────────────────────

Pattern: server_components_preference
  Type: Style Pattern
  Confidence: 0.75 (Moderate)
  Status: ⏳ Pending

  Description:
    User seems to prefer Server Components over
    Client Components when possible.

  Evidence:
    • 9 observations over 12 days
    • Need ~5 more observations for high confidence
    • Currently at 75% consistency

  Why Not Applied Yet:
    • Below 0.80 confidence threshold
    • Not enough observations to confirm
    • Waiting for pattern to strengthen

  Next Steps:
    • Continue coding normally
    • Pattern will auto-apply at 0.80+
    • Or manually apply with /sf:optimize --apply-pattern

  Current Usage:
    • Server Components: 9 times
    • Client Components: 3 times
    • Ratio: 75% server preference

  Recommendation:
    ⏳ Let pattern develop naturally.
       Should reach threshold in ~1 week.

═══════════════════════════════════════════════════════════
PATTERN RECOMMENDATIONS
───────────────────────────────────────────────────────────
  ✓ Your patterns are healthy and beneficial
  💡 1 pattern pending (server_components_preference)
  📈 Pattern learning is active and working well

  Suggested Actions:
    • Continue using Zod for validation
    • Keep implementing error boundaries
    • Use Server Components when possible to strengthen pattern
```

### Health Check Focus

```
User: /sf:analyze --health

Output:
🏥 Skills Health Check
═══════════════════════════════════════════════════════════

OVERALL HEALTH: ✅ 94% Healthy (7/8 skills excellent, 1 warning)

CRITICAL ISSUES: None ✅

WARNINGS (1)
───────────────────────────────────────────────────────────
  ⚠️  testing-suite
      Issue: Documentation outdated
      Age: 92 days since last update
      Impact: May miss new testing features
      Action: Run /sf:update testing-suite
      Priority: Medium

HEALTH CHECKS BY CATEGORY
───────────────────────────────────────────────────────────

✅ YAML Frontmatter (8/8 pass)
   All skills have valid YAML frontmatter

✅ Required Sections (8/8 pass)
   All skills have required sections:
   • Purpose
   • When to Use
   • Core Patterns
   • Examples

✅ Links & References (8/8 pass)
   All external links are valid
   No broken documentation references

✅ Dependencies (8/8 pass)
   All skill dependencies are satisfied
   No missing required tools/libraries

⚠️  Documentation Freshness (7/8 pass)
   7 skills have fresh documentation
   1 skill needs update

✅ Token Efficiency (8/8 pass)
   All skills within reasonable token limits
   Average: 1,561 tokens (target: <3,000)

✅ Content Quality (8/8 pass)
   Adequate code examples in all skills
   Best practices documented
   Clear explanations

PER-SKILL HEALTH
───────────────────────────────────────────────────────────
  ✅ nextjs-fullstack       100% healthy
  ✅ react-components       100% healthy
  ✅ supabase-integration   100% healthy
  ✅ git-workflow           100% healthy
  ⚠️  testing-suite         88% healthy (outdated docs)
  ✅ tailwind-styling       100% healthy
  ✅ docker-setup           100% healthy
  ✅ api-integration        100% healthy

RECOMMENDATIONS
───────────────────────────────────────────────────────────
  1. Update testing-suite documentation
  2. Consider scheduling regular updates (monthly)
  3. Enable auto-update notifications

═══════════════════════════════════════════════════════════
💡 Run /sf:update testing-suite to fix the warning
📊 Run /sf:analyze next month for ongoing monitoring
```

## Related Commands
- `/sf:optimize` - Apply optimization suggestions
- `/sf:update` - Update specific skills
- `/sf:list` - Quick overview of skills
- `/sf:status` - System status check

## Tips

- **Run regularly** - Monthly analysis helps catch issues early
- **Use --patterns** - Track how your workflow evolves
- **Export reports** - Keep historical data with --export
- **Act on recommendations** - Suggestions are based on real usage

## Troubleshooting

**No usage data?**
- Usage tracking may be disabled
- Check with `/sf:status`
- Enable in `/sf:config`

**Patterns not detecting?**
- Need at least 10 skill uses for pattern detection
- Patterns require consistent behavior
- Check confidence thresholds in config

**Analysis seems wrong?**
- Clear analytics: `/sf:reset --analytics-only`
- Rebuild from fresh data
- Report issues if persistent

## Advanced Usage

### Export to JSON

```bash
/sf:analyze --export

# Creates: ~/.claude/skills/skillforge/data/analysis_report_<date>.json
```

### Combine Options

```bash
# Detailed analysis with pattern focus
/sf:analyze --detailed --patterns

# Health check with export
/sf:analyze --health --export
```

### Scheduled Analysis

Consider running analysis:
- **Weekly** - Quick check for immediate issues
- **Monthly** - Comprehensive review and optimization
- **After major changes** - Verify impact of updates

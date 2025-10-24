# VISUAL OUTPUT SYSTEM

**Version**: 1.0.0
**Purpose**: Standardized visual communication system for SkillForge operations

---

## 📋 Core Principle

**SkillForge MUST be visible and transparent to the user.**

Every SkillForge operation must provide clear visual feedback so users understand:
- ✅ When SkillForge is active
- ✅ Which skills are being loaded
- ✅ Progress of orchestration
- ✅ Success/failure states
- ✅ Next steps

---

## 🎨 Visual Identity

### Brand Elements

**Primary Emoji**: 🔨 (Hammer - represents "forging" skills)
**Secondary Emojis**:
- 🎯 Intent Analysis
- 📦 Skill Loading
- ⚡ Orchestration Active
- ✨ Learning/Optimization
- 📊 Analytics
- 🎨 Generation
- 🔍 Discovery

**Color Coding** (when supported):
- 🟢 Green: Success, Active, Loaded
- 🔵 Blue: Information, Progress
- 🟡 Yellow: Warning, Attention Needed
- 🔴 Red: Error, Failed
- 🟣 Purple: SkillForge System Message

---

## 📢 Output Events

### Event 1: SkillForge Activation

**When**: SkillForge detects it should handle the request
**What to Show**: Banner indicating SkillForge is taking over

**Format**:
```
┌─────────────────────────────────────────────────────────┐
│ 🔨 SkillForge Active                                    │
│ Orchestrating personalized development environment...   │
└─────────────────────────────────────────────────────────┘
```

**Example Output**:
```markdown
🔨 **SkillForge Active**
Analyzing your request and loading relevant skills...
```

---

### Event 2: Intent Analysis

**When**: Analyzing user request
**What to Show**: What SkillForge understood from the request

**Format**:
```
🎯 Intent Analysis
├─ Action: create
├─ Domain: fullstack
├─ Technologies: Next.js, Supabase, TypeScript
└─ Complexity: moderate
```

**Example Output**:
```markdown
🎯 **Intent Analysis**
- **Action**: Create new component
- **Stack**: Next.js 15, Supabase, TypeScript
- **Domain**: Fullstack
```

---

### Event 3: Skill Discovery

**When**: SkillForge identifies which skills to load
**What to Show**: List of discovered skills with priority

**Format**:
```
🔍 Skill Discovery
┌─────────────────────────────────────────────────────────┐
│ Found 3 relevant skills:                                │
│                                                          │
│ [1] nextjs-fullstack         Priority: 100  (2.5k tok)  │
│     └─ Next.js development patterns                     │
│                                                          │
│ [2] supabase-integration     Priority: 95   (1.8k tok)  │
│     └─ Supabase auth & database                         │
│                                                          │
│ [3] git-workflow            Priority: 60   (600 tok)    │
│     └─ Git conventions & commits                        │
│                                                          │
│ Total Token Budget: 4,900 / 5,000                       │
└─────────────────────────────────────────────────────────┘
```

**Compact Alternative** (for simple requests):
```markdown
📦 **Loading Skills**
- `nextjs-fullstack` (your Next.js conventions)
- `supabase-integration` (your auth setup)
```

---

### Event 4: Progressive Loading

**When**: Loading skills with priority order
**What to Show**: Real-time progress of loading

**Format** (with progress indicator):
```
⚡ Loading Skills
[████████████████████░░] 80% (2/3 skills loaded)

✅ nextjs-fullstack loaded (2,534 lines)
✅ supabase-integration loaded (1,823 lines)
⏳ git-workflow loading...
```

**Compact Format**:
```markdown
⚡ **Skills Loaded**
✅ nextjs-fullstack
✅ supabase-integration
✅ git-workflow
```

---

### Event 5: Orchestration Complete

**When**: All skills loaded, ready to execute
**What to Show**: Summary and confirmation

**Format**:
```
✨ Orchestration Complete

Loaded 3 skills with your personalized conventions:
├─ Naming: camelCase variables, PascalCase components
├─ Imports: Absolute with @/ alias
├─ State: Zustand
├─ Validation: Zod
└─ Testing: Vitest

Ready to generate code your way! 🚀
```

---

### Event 6: Skill Usage Tracking

**When**: After completing the task
**What to Show** (optional, only if user requested analytics):
```
📊 Usage Tracked
└─ Skills: nextjs-fullstack + supabase-integration
   Pattern: auth_component_pattern (12th occurrence)
   Success: ✅ Code accepted without modifications
```

**Default**: Track silently, don't show unless `/sf:analyze` is used

---

### Event 7: Pattern Detection

**When**: SkillForge detects a new pattern (≥80% confidence)
**What to Show**: Notification of learned pattern

**Format**:
```
✨ Pattern Learned!

I've noticed you always use Zod validation with Supabase forms.
📈 Confidence: 92% (23/25 times)

Would you like me to:
[1] Always include Zod by default ✅ (recommended)
[2] Ask each time
[3] Ignore this pattern

This will update your skills to be even more personalized.
```

---

### Event 8: Error States

**When**: Something goes wrong
**What to Show**: Clear error with recovery options

**Format**:
```
❌ SkillForge Error

Failed to load skill: nextjs-fullstack
Reason: File not found

Recovery Options:
[1] Continue with available skills
[2] Regenerate missing skill (/sf:generate nextjs-fullstack)
[3] Use Claude's default knowledge

Proceeding with option [1]...
```

---

## 🎯 Output Modes

SkillForge has 3 output modes based on user preference:

### Mode 1: VERBOSE (Default for first-time users)

Shows all orchestration steps with detailed feedback.

**Example**:
```markdown
┌─────────────────────────────────────────────────────────┐
│ 🔨 SkillForge Active                                    │
└─────────────────────────────────────────────────────────┘

🎯 **Intent Analysis**
- Action: Create component
- Stack: Next.js + Supabase
- Complexity: Moderate

🔍 **Skill Discovery**
Found 3 relevant skills...

📦 **Loading Skills**
✅ nextjs-fullstack (2,534 lines)
✅ supabase-integration (1,823 lines)
✅ git-workflow (634 lines)

✨ **Ready!**
Generating code with YOUR conventions...
```

### Mode 2: COMPACT (Default after 10+ uses)

Shows minimal, essential info only.

**Example**:
```markdown
🔨 **SkillForge** → Loading: nextjs-fullstack, supabase-integration ✅

[proceeds with code generation]
```

### Mode 3: SILENT (User explicitly disabled)

No output. Works invisibly in background.

**Note**: Still tracks usage for learning, just doesn't show it.

---

## 📐 Formatting Guidelines

### Banner Style

Use box drawing for important messages:

```
┌─────────────────────────────────────────────────────────┐
│ 🔨 SkillForge Active                                    │
│ Message content here...                                 │
└─────────────────────────────────────────────────────────┘
```

### List Formatting

Use tree structure for hierarchical info:

```
🎯 Intent Analysis
├─ Action: create
├─ Domain: fullstack
├─ Stack:
│  ├─ Next.js 15
│  ├─ Supabase
│  └─ TypeScript
└─ Complexity: moderate
```

### Skill List

Use clear structure with metadata:

```
📦 Skills
[1] nextjs-fullstack         2,534 lines  Priority: 100
    └─ Next.js App Router development
[2] supabase-integration     1,823 lines  Priority: 95
    └─ Supabase authentication & DB
```

### Status Indicators

Use emoji for quick status scanning:

- ✅ Success/Completed
- ⏳ Loading/In Progress
- ❌ Error/Failed
- ⚠️ Warning/Attention
- 📊 Analytics/Data
- 🎯 Target/Goal
- 🔍 Search/Discovery
- ⚡ Active/Running
- ✨ New/Special

---

## 🔧 Implementation Rules

### Rule 1: Always Announce Activation

**WHEN**: SkillForge takes over orchestration
**MUST**: Show activation banner before any orchestration
**EXCEPTION**: Silent mode enabled

```python
# Pseudocode
if orchestration_needed and mode != "silent":
    display_activation_banner()
    display_intent_analysis()
    display_skill_discovery()
```

### Rule 2: Progressive Disclosure

**WHEN**: Loading multiple skills
**MUST**: Show loading progress if >2 skills OR >5 seconds
**REASON**: Gives user confidence system is working

```python
if skill_count > 2 or estimated_time > 5:
    show_progressive_loading()
else:
    show_compact_loading()
```

### Rule 3: Confirm Completion

**WHEN**: Skills loaded and ready
**MUST**: Show completion message with summary
**REASON**: Clear transition from setup to execution

```python
display_completion_summary(
    loaded_skills,
    user_conventions_applied,
    ready_message
)
```

### Rule 4: Silent Tracking

**WHEN**: Task completed
**MUST**: Track usage silently (don't interrupt flow)
**SHOW ONLY IF**: User runs `/sf:analyze` later

```python
# Track silently
track_usage(skills, outcome, duration)

# Only display if explicitly requested
if user_command == "/sf:analyze":
    display_usage_analytics()
```

### Rule 5: Learn Transparently

**WHEN**: New pattern detected (≥80% confidence)
**MUST**: Notify user and ask for confirmation
**REASON**: Maintain user control over learning

```python
if pattern.confidence >= 0.8:
    notify_pattern_detected(pattern)
    ask_user_preference()
    apply_only_if_approved()
```

---

## 🎬 Complete Example Flow

### User Request:
```
"Create a login component with Supabase authentication"
```

### SkillForge Output (VERBOSE mode):

```markdown
┌─────────────────────────────────────────────────────────┐
│ 🔨 SkillForge Active                                    │
│ Orchestrating personalized development environment...   │
└─────────────────────────────────────────────────────────┘

🎯 **Intent Analysis**
- **Action**: Create component
- **Feature**: Authentication (login)
- **Stack**: Next.js, Supabase
- **Domain**: Fullstack

🔍 **Skill Discovery**
Found 3 relevant skills:

📦 **Loading Skills**
[████████████████████████████████████████] 100%

✅ **nextjs-fullstack** (2,534 lines)
   └─ Your Next.js conventions loaded

✅ **supabase-integration** (1,823 lines)
   └─ Your Supabase auth patterns loaded

✅ **git-workflow** (634 lines)
   └─ Your commit style loaded

✨ **Orchestration Complete!**

Ready to create your login component with:
├─ Next.js 15 App Router
├─ Supabase Auth
├─ Your naming: camelCase
├─ Your imports: @/ absolute
├─ Your state: Zustand
├─ Your validation: Zod
└─ Your structure: Feature-based

Let's build it! 🚀

---

[Proceeds with code generation using loaded skills]
```

### Same Request in COMPACT mode:

```markdown
🔨 **SkillForge** → nextjs-fullstack, supabase-integration ✅

[Proceeds with code generation]
```

---

## 🎚️ User Controls

### Setting Output Mode

Users can control verbosity via `/sf:config`:

```
/sf:config output-mode verbose   # Show all details
/sf:config output-mode compact   # Minimal info
/sf:config output-mode silent    # No output
```

### Default Behavior

1. **First 10 uses**: VERBOSE (help user understand SkillForge)
2. **After 10 uses**: Automatically switch to COMPACT
3. **User can override**: Any time via `/sf:config`

---

## 📊 Analytics Output

When user runs `/sf:analyze`, show detailed analytics:

```markdown
📊 **SkillForge Analytics**

### Usage Summary (Last 30 Days)
┌────────────────────────────────────────────────────────┐
│ Skills Used: 5                                         │
│ Total Sessions: 47                                     │
│ Success Rate: 94% (44/47)                              │
│ Avg. Response Time: 8.2s                               │
└────────────────────────────────────────────────────────┘

### Most Used Skills
[1] nextjs-fullstack          32 uses   Success: 96%
[2] supabase-integration      28 uses   Success: 93%
[3] git-workflow             12 uses   Success: 100%

### Detected Patterns
✨ **Always use Zod with Supabase forms**
   Confidence: 92% (23/25 times)
   → Recommended: Auto-apply ✅

⚡ **Prefer server actions over API routes**
   Confidence: 85% (17/20 times)
   → Recommended: Auto-apply ✅

### Skills Performance
┌────────────────────────────────────────────────────────┐
│ nextjs-fullstack                                       │
│ Size: 2,534 lines (3.2k tokens)                        │
│ Load Time: 1.2s                                        │
│ Last Updated: 2 days ago                               │
│ Optimization: 🟢 Good                                  │
└────────────────────────────────────────────────────────┘
```

---

## 🔍 Introspection Output

When user runs `/sf:introspect`, show orchestration decisions:

```markdown
🔍 **SkillForge Introspection**

### Current Project Analysis
📁 Project: /Users/you/my-nextjs-app
🔍 Detected:
├─ Next.js 15.0.0
├─ TypeScript 5.3
├─ Supabase
└─ Tailwind CSS

### Recommended Skills
✅ **Already Installed**
- nextjs-fullstack
- supabase-integration
- git-workflow

⚠️ **Missing Skills**
- tailwind-ui (optional) - Would help with styling
- testing-vitest (optional) - Would help with testing

### Orchestration Decision Tree
For request: "Create login component"
│
├─ Intent: create + component + login
├─ Entities: Next.js, Supabase, auth
│
├─ Skill Selection:
│  ├─ nextjs-fullstack (explicit match: Next.js)
│  ├─ supabase-integration (explicit match: Supabase)
│  └─ git-workflow (dependency of nextjs-fullstack)
│
└─ Priority Ranking:
   [1] nextjs-fullstack: 100 (explicit + high usage)
   [2] supabase-integration: 95 (explicit + pattern match)
   [3] git-workflow: 60 (dependency)
```

---

## ✅ Implementation Checklist

When implementing SkillForge orchestration, Claude MUST:

- [ ] Show activation banner when orchestrating
- [ ] Display intent analysis results
- [ ] List discovered skills with priorities
- [ ] Show progressive loading for >2 skills
- [ ] Confirm completion with summary
- [ ] Track usage silently (don't interrupt)
- [ ] Notify on pattern detection (≥80% confidence)
- [ ] Use appropriate emoji for each event type
- [ ] Format with boxes/trees for readability
- [ ] Respect user's output mode preference
- [ ] Handle errors gracefully with recovery options

---

## 🎯 Success Criteria

A good SkillForge output should:

✅ **Inform**: User knows SkillForge is active
✅ **Clarify**: User understands which skills are being used
✅ **Reassure**: User sees their conventions are being applied
✅ **Guide**: User knows what's happening at each step
✅ **Educate**: First-time users learn how SkillForge works
✅ **Respect**: Experienced users get concise, non-intrusive output

---

## 🔧 Maintenance

This file should be updated when:
- New output events are added
- User feedback suggests improvements
- New emoji/formatting standards emerge
- Output modes need adjustment

**Last Review**: 2025-10-23
**Next Review**: 2025-11-23

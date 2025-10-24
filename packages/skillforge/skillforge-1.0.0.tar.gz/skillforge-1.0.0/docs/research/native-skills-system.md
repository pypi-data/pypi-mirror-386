# Claude Code Native Skills System - Research Document

**Date**: 2025-10-22
**Source**: https://docs.claude.com/en/docs/claude-code/skills
**Purpose**: Understanding the native skills system for SkillForge development

---

## Executive Summary

Claude Code has a **model-invoked** skills system where:
- Skills are discovered automatically from 3 locations
- Activation is based on description quality (not user commands)
- Progressive disclosure manages context efficiently
- Tool access can be restricted via `allowed-tools`
- Changes require Claude Code restart

**Key Insight for SkillForge**: Description quality is THE primary discovery mechanism. SkillForge must generate highly specific, context-rich descriptions.

---

## 1. Skill Discovery & Loading

### Three Sources (loaded at startup)

```
1. Personal Skills:  ~/.claude/skills/
2. Project Skills:   .claude/skills/ (within project)
3. Plugin Skills:    bundled with installed plugins
```

**Loading Behavior**:
- All skills loaded at startup
- Remain available throughout session
- **Changes require restart** ⚠️

**Implication for SkillForge**:
- Generated skills go to `~/.claude/skills/[skill-name]/`
- Users must restart Claude Code after generation
- Consider adding "restart reminder" in wizard output

---

## 2. SKILL.md Format Structure

### Required Components

```yaml
---
name: "Skill Name"
description: "What this does and when to use it"
allowed-tools: [optional_tool_list]  # Optional
---

# Skill Title

## Section 1
Content...

## Section 2
Content...
```

### Critical Fields

1. **name** (required)
   - Identifies the skill
   - Should be unique
   - CamelCase or kebab-case

2. **description** (CRITICAL ⭐)
   - Determines when Claude activates skill
   - Must specify:
     * What the skill does
     * When to use it
     * Trigger keywords
   - Quality directly affects discovery rate

3. **allowed-tools** (optional, security)
   - Restricts Claude's capabilities
   - Use for read-only or limited-scope skills
   - Format: `[Read, Grep, Glob]`

**Example Good Description**:
```yaml
description: >
  Extract text and tables from PDF files, fill forms,
  merge documents. Use when working with PDF files or
  when the user mentions PDFs, forms, or document extraction.
```

**Example Bad Description** (vague):
```yaml
description: "PDF helper"
```

**Implication for SkillForge**:
- Generator must create rich, context-aware descriptions
- Include user's tech stack keywords in descriptions
- Template descriptions with specific trigger terms
- Test generated descriptions for clarity

---

## 3. Progressive Disclosure Mechanism

### How It Works

```
SKILL.md (always loaded)
    ↓
User request matches → Load supporting files on-demand
    ↓
reference.md, examples.md, scripts/ (loaded when needed)
```

**Benefits**:
- Reduces token overhead
- Keeps context manageable
- Maintains accessibility

**File Types**:
- `SKILL.md` - Always in context
- `reference.md` - Technical reference (loaded when needed)
- `examples.md` - Code examples (loaded when needed)
- `scripts/` - Helper scripts (executed when needed)
- `templates/` - File templates (used when needed)

**Implication for SkillForge**:
- SKILL.md should be concise but complete
- Move verbose content to reference.md
- Store extensive examples in examples.md
- Optimize SKILL.md token count aggressively

---

## 4. Skill Activation Logic

### Model-Invoked, Not User-Invoked ⚠️

**Key Difference**:
- Slash commands: `/command` - User invokes
- Skills: automatic - Claude decides

**Activation Factors**:
1. Request content matches skill description
2. Description quality and specificity
3. Context relevance
4. Presence of trigger keywords

**Example Flow**:
```
User: "Extract data from this PDF"
    ↓
Claude analyzes request
    ↓
Matches "PDF", "extract" in skill description
    ↓
Activates PDF skill
    ↓
Uses skill instructions
```

**Anti-Pattern**:
```
Vague description: "PDF helper"
    ↓
Claude uncertain when to use
    ↓
Skill underutilized or never used
```

**Implication for SkillForge**:
- **Orchestrator must NOT rely on user commands**
- Instead: optimize descriptions for Claude's matching algorithm
- Test: Generate description → Test with various queries → Measure activation rate
- Learning system should track: "When was skill activated vs when it should have been?"

---

## 5. Directory Structure

### Standard Layout

```
~/.claude/skills/my-skill/
│
├── SKILL.md              # Required, always loaded
│
├── reference.md          # Optional, loaded on-demand
│   └── Technical details, API reference, etc.
│
├── examples.md           # Optional, loaded on-demand
│   └── Code examples, use cases
│
├── scripts/              # Optional, executed when needed
│   ├── helper.py
│   └── processor.sh
│
└── templates/            # Optional, used when needed
    ├── component.tsx
    └── config.yaml
```

**File Naming**: Use forward slashes (Unix-style), even on Windows.

**Implication for SkillForge**:
- Generator must create this exact structure
- Validation: check SKILL.md exists
- Supporting files: generated based on skill complexity
- Scripts: generate only if skill needs automation
- Templates: generate for common patterns (components, configs)

---

## 6. Tool Access Control

### allowed-tools Field

**Purpose**: Restrict Claude's capabilities when skill is active

**Use Cases**:
1. **Read-only skills** (data analysis, reporting)
   ```yaml
   allowed-tools: [Read, Grep, Glob]
   ```

2. **Limited file operations** (backup, archive)
   ```yaml
   allowed-tools: [Read, Write, Bash]
   ```

3. **Full access** (development tasks)
   ```yaml
   # No allowed-tools field = ask permission per tool
   ```

**Available Tools** (common):
- `Read`, `Write`, `Edit`
- `Bash`, `WebSearch`, `WebFetch`
- `Grep`, `Glob`
- MCP tools (e.g., `mcp__context7__get-library-docs`)

**Implication for SkillForge**:
- Default: don't restrict (let Claude ask)
- For specialized skills: add appropriate restrictions
- Example: "Git Workflow" skill might restrict to `[Read, Bash]`
- Security: never allow unrestricted Write in untrusted environments

---

## 7. Best Practices from Official Docs

### Keep Skills Focused

❌ **Bad**: Single "document-processing" skill
✅ **Good**: Separate skills for PDF, Excel, Word

**Why**: Clearer activation signals, easier maintenance, better descriptions

**Implication for SkillForge**:
- Generate separate skills per technology
- Don't merge "nextjs + react + supabase" into one
- Instead: nextjs-fullstack, react-spa, supabase-integration as separate skills
- Orchestrator coordinates multiple skills when needed

### Make Descriptions Specific

❌ **Bad**: "Helps with Next.js development"
✅ **Good**: "Build Next.js 15 applications using App Router, Server Components, and TypeScript. Use when creating Next.js apps, implementing features with App Router, or when user mentions Next.js, Server Components, or app directory."

**Formula**: `[What it does] + [Technologies] + [When to use] + [Trigger keywords]`

**Implication for SkillForge**:
- Template: "Build {framework} {version} applications using {features}. Use when {scenarios} or when user mentions {keywords}."
- Variables filled from user profile
- Context7 docs provide version and features
- User conventions add to trigger keywords

### Team Testing

**Official Recommendation**: Have teammates test skills and provide feedback on clarity.

**Implication for SkillForge**:
- After generation, suggest user test with various queries
- Learning system tracks activation success rate
- Low activation rate → regenerate description with better triggers

### Version Documentation

**Official Recommendation**: Track changes in SKILL.md to help teammates.

**Implication for SkillForge**:
- Add `## Version History` section to generated SKILL.md
- Learner updates this section when applying patterns
- Optimizer logs optimizations here
- Format:
  ```markdown
  ## Version History
  - v1.2.1 (2025-10-25): Pattern learned - Always use Zod (confidence: 0.92)
  - v1.2.0 (2025-10-20): Updated Next.js 14 → 15 docs
  - v1.1.0 (2025-10-15): Added Server Actions patterns
  - v1.0.0 (2025-10-10): Initial generation
  ```

---

## 8. Limitations & Constraints

### Fundamental Constraints

1. **No User Invocation** ⚠️
   - Skills cannot be called like `/skill-name`
   - Only model decides when to use
   - **Workaround**: Use slash commands for explicit invocation (separate from skills)

2. **Restart Required** ⚠️
   - Changes don't take effect until restart
   - **Implication**: Generator must remind user to restart
   - **Future**: Could add "hot reload" feature via plugin

3. **Claude Code Only** ⚠️
   - `allowed-tools` doesn't work in other Claude products
   - **Implication**: Skills are Claude Code-specific

4. **File Path Format** ⚠️
   - Must use forward slashes: `path/to/file`
   - **Implication**: Generator must normalize paths on Windows

5. **YAML Syntax Errors** ⚠️
   - Invalid YAML prevents skill loading
   - **Implication**: Generator must validate YAML before writing

6. **Environment Dependencies** ⚠️
   - Skills assume tools are installed (Python, Node, etc.)
   - **Implication**: Include prerequisite checks in skills

---

## 9. Loading Order and Priority

### Current Behavior

**Documentation doesn't specify priority**:
- Skills from all 3 sources loaded simultaneously
- No documented conflict resolution
- No priority ranking system

**Official Recommendation**: Use distinct trigger terms in descriptions (not priority resolution)

**Implication for SkillForge**:
- Don't rely on loading order
- Ensure generated skills have unique, specific descriptions
- Avoid overlapping trigger keywords between skills
- If overlap necessary: make one description MORE specific
- Example:
  ```yaml
  # Generic
  nextjs-basics:
    description: "Basic Next.js development..."

  # Specific (will activate over generic)
  nextjs-fullstack:
    description: "Advanced Next.js 15 full-stack development with App Router, Server Components, and Supabase integration..."
  ```

---

## 10. Key Insights for SkillForge

### Critical Success Factors

1. **Description Quality is Everything**
   - 80% of skill effectiveness comes from description
   - Generate rich, keyword-dense, context-aware descriptions
   - Test and iterate on descriptions

2. **Progressive Disclosure is Our Friend**
   - Keep SKILL.md concise (target: <2000 tokens)
   - Move details to supporting files
   - This allows more skills to coexist

3. **Model-Invoked Paradigm**
   - Orchestrator CANNOT force skill loading
   - Instead: optimize descriptions for natural activation
   - Track activation rates to improve descriptions

4. **Restart Friction**
   - Users must restart after generation
   - Make this clear in wizard output
   - Consider automation: "Restart Claude Code now? [Y/n]"

5. **Validation is Critical**
   - Invalid YAML = broken skill
   - Generator must validate before writing
   - Include validation in CI/CD

### SkillForge Architecture Decisions

**DO**:
- ✅ Generate separate skills per technology (not monoliths)
- ✅ Create rich, specific descriptions with trigger keywords
- ✅ Use progressive disclosure (SKILL.md + reference.md + examples.md)
- ✅ Validate YAML frontmatter before writing
- ✅ Include version history in generated skills
- ✅ Test activation rates and iterate

**DON'T**:
- ❌ Rely on loading order/priority
- ❌ Create vague descriptions
- ❌ Put everything in SKILL.md (bloats tokens)
- ❌ Assume restart happens automatically
- ❌ Skip YAML validation

---

## 11. Questions for Further Research

1. **Token Limits**: What's the max size for SKILL.md before performance degrades?
2. **Activation Algorithm**: Does Claude use semantic matching or keyword matching for descriptions?
3. **Multiple Matches**: If 2+ skills match, how does Claude choose?
4. **Context Window**: Do all SKILL.md files count against context window, or only active ones?
5. **Caching**: Does Claude Code cache parsed skills between sessions?

**Action**: Test these empirically during development.

---

## 12. References

- Official Documentation: https://docs.claude.com/en/docs/claude-code/skills
- Related: Claude Code Plugin System (for future research)
- Related: MCP Integration (separate research doc)

---

## Next Steps

1. ✅ Complete research documentation
2. Create SKILL.md template based on best practices learned
3. Design SkillForge's SKILL.md (entry point)
4. Test: Create minimal skill manually and verify Claude loads it
5. Validate description effectiveness with test queries

---

**Research Completed**: 2025-10-22
**Confidence Level**: High (based on official documentation)
**Action Items**:
- Design description generation algorithm
- Create SKILL.md validation schema
- Plan activation rate tracking system

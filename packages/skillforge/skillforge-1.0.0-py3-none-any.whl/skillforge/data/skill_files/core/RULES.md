# SkillForge Framework Rules

**Version**: 1.0.0
**Last Updated**: 2025-10-22
**Purpose**: Governing rules for AI agents using SkillForge framework

---

## Priority System

All rules are categorized by priority level:

- 🔴 **CRITICAL**: Security, data safety, must-follow requirements. Violations may cause data loss or security breaches.
- 🟡 **IMPORTANT**: Quality, best practices, strong preferences. Deviations should be documented and justified.
- 🟢 **RECOMMENDED**: Optimization, style, apply when practical. May be skipped under time/resource constraints.

---

## Core Rules

### 🔴 CRITICAL Rules

**C1. Documentation Integrity**
- NEVER modify or delete existing skill documentation without explicit user confirmation
- ALWAYS preserve original intent when updating skills
- MUST backup skills before major modifications
- Rationale: Prevents loss of valuable domain knowledge

**C2. Validation Before Action**
- ALWAYS validate skill syntax before loading into context
- MUST check for conflicting instructions across skills
- NEVER execute skills with failed validation checks
- Rationale: Prevents unpredictable behavior and context pollution

**C3. Security & Privacy**
- NEVER include credentials, API keys, or sensitive data in skills
- MUST sanitize user inputs before skill generation
- ALWAYS respect user data privacy in learning mechanisms
- Rationale: Protects user security and data integrity

**C4. Token Budget Enforcement**
- MUST respect maximum token limits for skill loading
- NEVER exceed configured budget without user approval
- ALWAYS prioritize CRITICAL skills when budget is constrained
- Rationale: Prevents context overflow and performance degradation

**C5. Version Control**
- MUST maintain version history for all skill modifications
- ALWAYS tag breaking changes with version increments
- NEVER overwrite without backup
- Rationale: Enables rollback and change tracking

**C6. Explicit User Consent**
- MUST ask before generating new skills
- ALWAYS confirm before deleting or merging skills
- NEVER auto-apply learned patterns without notification
- Rationale: Maintains user control and transparency

**C7. Data Safety**
- ALWAYS validate file paths before write operations
- MUST check for file existence before overwrite
- NEVER perform destructive operations without confirmation
- Rationale: Prevents accidental data loss

**C8. Error Isolation**
- MUST handle skill loading errors gracefully
- NEVER let one failed skill block entire orchestration
- ALWAYS log errors with context for debugging
- Rationale: Ensures system resilience

### 🟡 IMPORTANT Rules

**I1. Quality Standards**
- Skills SHOULD be clear, concise, and actionable
- SHOULD include examples for complex instructions
- SHOULD specify success criteria where applicable
- Rationale: Improves skill effectiveness and maintainability

**I2. Testing Protocol**
- SHOULD validate new skills with test scenarios
- SHOULD verify skill interactions in multi-skill contexts
- SHOULD document test results for reference
- Rationale: Ensures reliability before production use

**I3. Naming Conventions**
- Skills SHOULD use descriptive, lowercase names with underscores
- SHOULD follow pattern: `{domain}_{action}_{context}.md`
- SHOULD avoid generic names like "helper" or "utils"
- Rationale: Improves discoverability and organization

**I4. Dependency Management**
- SHOULD explicitly declare skill dependencies
- SHOULD specify required context or prerequisites
- SHOULD document interaction patterns with other skills
- Rationale: Prevents integration issues

**I5. Performance Awareness**
- SHOULD optimize skill size for token efficiency
- SHOULD remove redundant or obsolete content
- SHOULD monitor loading times and context usage
- Rationale: Maintains system responsiveness

**I6. Consistency Standards**
- SHOULD maintain consistent formatting across skills
- SHOULD use standard templates for common patterns
- SHOULD align with project conventions
- Rationale: Reduces cognitive load and errors

**I7. Change Documentation**
- SHOULD log rationale for significant changes
- SHOULD document migration paths for breaking changes
- SHOULD maintain changelog for complex skills
- Rationale: Facilitates maintenance and knowledge transfer

**I8. Context Preservation**
- SHOULD preserve user preferences across sessions
- SHOULD maintain skill state where relevant
- SHOULD document context requirements
- Rationale: Improves user experience continuity

### 🟢 RECOMMENDED Rules

**R1. Optimization Practices**
- Consider combining related mini-skills into cohesive units
- Consider lazy loading for infrequently used skills
- Consider caching validated skills to reduce overhead
- Rationale: Improves performance and efficiency

**R2. Learning Opportunities**
- Track patterns in user requests for skill suggestions
- Analyze skill usage frequency for prioritization
- Identify gaps in skill coverage
- Rationale: Enables continuous improvement

**R3. Style Guidelines**
- Use active voice in skill instructions
- Prefer bullet points over dense paragraphs
- Include practical examples over theoretical explanations
- Rationale: Enhances clarity and usability

**R4. Documentation Extras**
- Add metadata tags for searchability
- Include version history in complex skills
- Provide usage statistics when available
- Rationale: Improves long-term maintainability

**R5. User Experience**
- Provide helpful error messages with actionable guidance
- Offer suggestions when skills are missing
- Display progress for long-running operations
- Rationale: Reduces user frustration

**R6. Modularity**
- Design skills for reusability across contexts
- Avoid hard-coding project-specific details
- Create composable skill building blocks
- Rationale: Increases flexibility and adaptability

---

## Skill Generation Rules

### Pre-Generation Checklist

```
[ ] User has explicitly requested skill creation
[ ] No existing skill covers this functionality
[ ] Skill purpose is clearly defined
[ ] Target directory is valid and writable
[ ] Skill name follows naming conventions
[ ] Token budget can accommodate new skill
[ ] Dependencies are identified and available
```

### Generation Process

**Step 1: Requirement Analysis**
- Extract core requirements from user request
- Identify success criteria and constraints
- Determine skill priority level
- Check for conflicts with existing skills

**Step 2: Template Selection**
- Choose appropriate template based on skill type
- Customize template for specific use case
- Include required metadata sections

**Step 3: Content Creation**
- Write clear, actionable instructions
- Add examples for complex scenarios
- Specify validation criteria
- Document prerequisites and dependencies

**Step 4: Validation**
- Check syntax and formatting
- Verify completeness of required sections
- Test against sample scenarios
- Review for conflicts with existing skills

**Step 5: Deployment**
- Save to appropriate directory
- Update skill registry
- Log creation event
- Confirm with user

### Post-Generation Validation

```
✓ File exists at expected path
✓ Syntax is valid Markdown
✓ Required metadata is present
✓ Instructions are clear and actionable
✓ No conflicts detected with existing skills
✓ Token budget is within limits
✓ User has confirmed satisfaction
```

### Naming Conventions

**Pattern**: `{domain}_{action}_{context}.md`

**Examples**:
- `python_code_review.md` - Python code review guidelines
- `api_design_rest.md` - REST API design principles
- `database_migration_postgres.md` - PostgreSQL migration workflow
- `testing_unit_pytest.md` - Pytest unit testing standards

**Avoid**:
- Generic names: `helper.md`, `utils.md`, `misc.md`
- Vague names: `skill1.md`, `new_skill.md`
- Overly long names: `comprehensive_guide_to_advanced_typescript_patterns.md`
- Special characters: `skill#1.md`, `test@skill.md`

---

## Orchestration Rules

### Skill Loading Priorities

**Priority Order** (highest to lowest):
1. 🔴 CRITICAL skills (security, safety, core framework)
2. 🟡 IMPORTANT skills (quality, standards, conventions)
3. 🟢 RECOMMENDED skills (optimization, extras)
4. User-requested skills (explicitly loaded for session)
5. Context-specific skills (auto-loaded based on task)
6. Learning-suggested skills (recommended by framework)

**Loading Strategy**:
```
IF token_budget < MINIMUM_SAFE_THRESHOLD:
    Load only CRITICAL skills
ELIF token_budget < COMFORTABLE_THRESHOLD:
    Load CRITICAL + IMPORTANT skills
ELSE:
    Load CRITICAL + IMPORTANT + RECOMMENDED + user-requested
```

### Token Budget Enforcement

**Budget Allocation**:
- Framework overhead: 10% of total budget
- CRITICAL skills: 30% of total budget
- IMPORTANT skills: 25% of total budget
- RECOMMENDED skills: 15% of total budget
- User context: 20% of total budget

**Enforcement Actions**:
- Monitor total tokens loaded in real-time
- Warn when approaching 80% of budget
- Halt loading at 95% of budget
- Provide suggestions for budget optimization

**Budget Exceeded Response**:
```
1. Identify lowest priority skills currently loaded
2. Suggest skills that can be unloaded
3. Ask user to choose: reduce skills OR increase budget
4. Log budget violation for analysis
```

### Conflict Resolution Hierarchy

**When conflicting instructions are detected**:

```
Priority 1: User explicit instruction (highest)
    ↓
Priority 2: Project-specific skills
    ↓
Priority 3: Domain-specific skills
    ↓
Priority 4: Framework core skills
    ↓
Priority 5: General best practices (lowest)
```

**Resolution Process**:
1. Identify conflicting rules
2. Determine priority of each source
3. Apply highest priority rule
4. Log conflict and resolution
5. Notify user if resolution is ambiguous

### Error Handling Protocol

**Skill Loading Errors**:
```
ON skill_load_error:
    1. Log error with full context
    2. Skip failed skill (don't block others)
    3. Continue loading remaining skills
    4. Report failed skills to user
    5. Suggest remediation actions
```

**Runtime Errors**:
```
ON skill_execution_error:
    1. Capture error state
    2. Attempt graceful degradation
    3. Notify user of limitation
    4. Log for post-mortem analysis
    5. Continue with available skills
```

**Critical Errors**:
```
ON critical_error:
    1. Halt all skill operations
    2. Preserve current state
    3. Notify user immediately
    4. Provide rollback options
    5. Require explicit user action to proceed
```

---

## File Organization Rules

### Directory Structure

```
skillforge/
└── data/
    └── skill_files/
        ├── core/              # Framework core skills (CRITICAL)
        │   ├── RULES.md
        │   ├── SKILLFORGE_CORE.md
        │   └── ORCHESTRATOR.md
        ├── domain/            # Domain-specific skills
        │   ├── python/
        │   ├── javascript/
        │   ├── database/
        │   └── devops/
        ├── project/           # Project-specific skills
        │   └── {project_name}/
        ├── user/              # User custom skills
        │   └── {user_id}/
        └── templates/         # Skill templates
            └── skill_template.md
```

### Placement Rules

**Where to place generated skills**:

| Skill Type | Directory | Priority | Example |
|------------|-----------|----------|---------|
| Framework core | `core/` | 🔴 CRITICAL | RULES.md |
| Language-specific | `domain/{language}/` | 🟡 IMPORTANT | python/code_review.md |
| Technology-specific | `domain/{tech}/` | 🟡 IMPORTANT | database/postgres_migration.md |
| Project-specific | `project/{name}/` | 🟡 IMPORTANT | myapp/api_conventions.md |
| User custom | `user/{id}/` | 🟢 RECOMMENDED | user123/personal_workflow.md |
| Experimental | `user/{id}/experimental/` | 🟢 RECOMMENDED | user123/experimental/test_skill.md |

### Naming & Organization

**File Naming**:
- Use lowercase letters
- Separate words with underscores
- Use `.md` extension
- Keep names under 50 characters
- Be descriptive but concise

**Directory Naming**:
- Use lowercase letters
- No spaces or special characters
- Group by logical domain
- Limit nesting to 3 levels max

### No Scattered Files Policy

🔴 **CRITICAL**: Skills MUST be placed in designated directories

**Violations**:
- ❌ Skills in project root
- ❌ Skills mixed with source code
- ❌ Skills in arbitrary locations
- ❌ Duplicate skills in multiple locations

**Enforcement**:
- Validate file paths before creation
- Reject operations outside designated directories
- Offer correct path when violation detected
- Log violations for audit

---

## Decision Trees

### When to Generate New Skill?

```
User requests functionality
        ↓
    Does exact skill exist?
    ├─ YES → Use existing skill
    │         ↓
    │     Is it adequate?
    │     ├─ YES → Done
    │     └─ NO → [Go to "Update Existing?"]
    │
    └─ NO → Does similar skill exist?
            ├─ YES → Can it be extended?
            │        ├─ YES → [Go to "Update Existing?"]
            │        └─ NO → [Go to "Should Merge?"]
            │
            └─ NO → Is scope well-defined?
                    ├─ YES → Is it reusable?
                    │        ├─ YES → GENERATE NEW SKILL
                    │        └─ NO → [Ask user: "One-time task?"]
                    │
                    └─ NO → [Ask user for clarification]
```

### When to Update Existing Skill?

```
Modification requested/needed
        ↓
    Is change breaking?
    ├─ YES → Would it affect other users/contexts?
    │        ├─ YES → Create new version (increment major)
    │        └─ NO → Get user confirmation
    │                 ├─ Confirmed → Update with backup
    │                 └─ Denied → Keep original
    │
    └─ NO → Is change additive?
            ├─ YES → Is skill becoming too large?
            │        ├─ YES → [Go to "Should Split?"]
            │        └─ NO → Update (increment minor)
            │
            └─ NO → Is it a fix/refinement?
                    ├─ YES → Update (increment patch)
                    └─ NO → [Ask user for intent]
```

### When to Merge Skills?

```
Multiple similar skills detected
        ↓
    Do they serve same purpose?
    ├─ YES → Are they conflicting?
    │        ├─ YES → Which has higher priority?
    │        │        ↓
    │        │    Apply priority hierarchy
    │        │    Merge lower into higher
    │        │    Archive deprecated version
    │        │
    │        └─ NO → Are they complementary?
    │                 ├─ YES → Merge into comprehensive skill
    │                 └─ NO → Keep separate
    │
    └─ NO → Do they share common patterns?
            ├─ YES → Extract common parts to base skill
            │        Keep specific parts separate
            │
            └─ NO → Keep separate (no merge needed)
```

### When to Ask User?

```
Decision point reached
        ↓
    Is outcome ambiguous?
    ├─ YES → ASK USER
    │
    └─ NO → Could decision affect workflow?
            ├─ YES → Is it reversible?
            │        ├─ YES → Proceed (notify user)
            │        └─ NO → ASK USER
            │
            └─ NO → Is it a preference matter?
                    ├─ YES → Check learned preferences
                    │        ├─ Found → Apply preference
                    │        └─ Not found → ASK USER (learn for next time)
                    │
                    └─ NO → Apply default behavior (log decision)
```

### Should Split Skill?

```
Skill exceeds recommended size
        ↓
    Does it cover multiple domains?
    ├─ YES → Split by domain
    │        Create cross-reference links
    │
    └─ NO → Does it have distinct use cases?
            ├─ YES → Split by use case
            │        Create base + specific skills
            │
            └─ NO → Can it be modularized?
                    ├─ YES → Extract reusable components
                    │        Keep high-level orchestration
                    │
                    └─ NO → Optimize content
                            Remove redundancy
                            Consider summary format
```

---

## Quality Gates

### Validation Checkpoints

**Checkpoint 1: Pre-Generation**
```
✓ User intent is clear
✓ Skill scope is defined
✓ No duplicate exists
✓ Name follows conventions
✓ Target directory is valid
```

**Checkpoint 2: Post-Generation**
```
✓ File is valid Markdown
✓ Required sections present
✓ Instructions are actionable
✓ Examples are included (if applicable)
✓ Metadata is complete
```

**Checkpoint 3: Pre-Loading**
```
✓ Syntax validation passed
✓ No circular dependencies
✓ Token budget allows loading
✓ Priority level assigned
✓ Conflicts resolved
```

**Checkpoint 4: Post-Loading**
```
✓ Skill is accessible in context
✓ Instructions are parseable
✓ No runtime errors detected
✓ Performance is acceptable
✓ User feedback collected
```

### Success Criteria

**Skill Generation Success**:
- File created at correct path
- Content matches requirements
- Validation passes all checks
- User confirms satisfaction
- Logged in registry

**Skill Loading Success**:
- Skill loaded within token budget
- No conflicts with existing skills
- Instructions are accessible
- Performance metrics acceptable
- Error rate < 1%

**Orchestration Success**:
- All required skills loaded
- Priority order respected
- Token budget not exceeded
- No critical errors
- User objectives achievable

### Failure Handling

**Generation Failure**:
```
1. Identify failure point
2. Log error with context
3. Clean up partial artifacts
4. Notify user with specifics
5. Suggest corrective action
6. Offer retry or alternative
```

**Loading Failure**:
```
1. Skip failed skill
2. Continue loading others
3. Log failure details
4. Assess impact on objectives
5. Notify user if critical
6. Suggest workarounds
```

**Validation Failure**:
```
1. Reject invalid skill
2. Preserve original if update
3. Provide detailed error report
4. Suggest corrections
5. Offer manual fix option
6. Prevent system corruption
```

---

## Learning Rules

### When to Track Data

🟡 **IMPORTANT**: Learning should enhance, not replace, explicit user control

**Track**:
- ✅ Skill usage frequency
- ✅ Common task patterns
- ✅ User preferences (when expressed)
- ✅ Error patterns and resolutions
- ✅ Performance metrics

**Do NOT Track**:
- ❌ Sensitive user data
- ❌ Private content
- ❌ Credentials or secrets
- ❌ Personal information

### When to Apply Patterns

**Auto-Apply** (with notification):
- Skill loading order based on usage
- Performance optimizations
- Error prevention tactics
- Formatting consistency

**Suggest** (require confirmation):
- New skill generation based on patterns
- Skill merging opportunities
- Workflow optimizations
- Template customizations

**Never Apply** (always ask):
- Changes to existing skills
- Deletion of skills
- Security-related decisions
- Workflow modifications

### Confidence Thresholds

**High Confidence (≥ 90%)**:
- Apply automatically with brief notification
- Example: "Loading frequently used skills first"

**Medium Confidence (70-89%)**:
- Suggest with clear rationale
- Example: "Detected pattern: Consider creating skill for X?"

**Low Confidence (50-69%)**:
- Mention as observation
- Example: "Note: Similar tasks done 3 times. Want to create skill?"

**Insufficient Confidence (< 50%)**:
- Do not suggest
- Continue learning silently

### User Notification Requirements

**Always Notify**:
- 🔴 Auto-applied learned patterns
- 🔴 Suggestions based on learning
- 🔴 Data being tracked for learning
- 🔴 Confidence level of suggestions

**Notification Format**:
```
[LEARNED] {action_taken}
Reason: {pattern_detected}
Confidence: {percentage}
Undo: {how_to_reverse}
```

**Example**:
```
[LEARNED] Loading python_code_review.md automatically
Reason: Used in 8 of last 10 Python sessions
Confidence: 95%
Undo: Use --no-auto-load flag or update preferences
```

### Privacy & Data Handling

🔴 **CRITICAL**: User privacy is paramount

**Principles**:
- Learning data stays local
- No external transmission without consent
- User can inspect learned patterns
- User can clear learning data anytime
- Transparent about what is learned

**User Controls**:
```
skillforge learn --status          # View what has been learned
skillforge learn --clear           # Clear all learning data
skillforge learn --disable         # Disable learning
skillforge learn --export          # Export patterns for review
```

---

## Examples for Unclear Cases

### Example 1: Conflicting Instructions

**Scenario**: Project skill says "use tabs" but Python domain skill says "use spaces"

**Resolution**:
```
1. Apply hierarchy: Project-specific > Domain-specific
2. Result: Use tabs (project preference wins)
3. Log: "Conflict resolved: tabs (project) > spaces (python)"
4. Notify: "Using tabs per project convention"
```

### Example 2: Ambiguous Scope

**Scenario**: User says "help with API design"

**Response**:
```
Decision Tree: "When to Ask User?"
- Outcome ambiguous? YES
- Action: ASK USER

Questions:
1. Which API type? (REST, GraphQL, gRPC, other)
2. New API or existing refinement?
3. Should this be a reusable skill?

Based on answers → Generate appropriate skill
```

### Example 3: Token Budget Exceeded

**Scenario**: Loading skills exceeds 95% of budget

**Response**:
```
1. Halt loading (per enforcement rules)
2. Identify loaded skills by priority
3. Suggest: "Unload these RECOMMENDED skills to free 15%?"
4. Alternatives:
   - Increase token budget
   - Use lazy loading for some skills
   - Create skill summaries
5. Await user decision
```

### Example 4: Learned Pattern - Create Skill?

**Scenario**: User has manually done "Python + PostgreSQL migrations" 5 times

**Response**:
```
Confidence: 85% (Medium-High)
Action: Suggest (not auto-apply)

Message:
"[LEARNED PATTERN] Detected: Python + PostgreSQL migrations (5 occurrences)
Suggestion: Create skill 'database_migration_postgres.md'?
Benefits: Consistent process, save time, capture best practices
Confidence: 85%
Create now? [Y/n]"
```

### Example 5: Multiple Skills for Same Task

**Scenario**: `api_rest.md`, `api_design.md`, `rest_api_guide.md` all exist

**Response**:
```
Decision Tree: "When to Merge Skills?"
- Same purpose? Likely YES
- Conflicting? Need to check content
- Complementary? Need to review

Actions:
1. Analyze all three skills
2. Identify overlaps and unique content
3. Suggest merge plan:
   "Merge into 'api_design_rest.md' containing:
   - Core principles from api_design.md
   - REST specifics from api_rest.md
   - Practical guide from rest_api_guide.md
   Archive old versions? [Y/n]"
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-22 | Initial RULES.md creation |

---

## See Also

- `SKILLFORGE_CORE.md` - Framework core capabilities
- `ORCHESTRATOR.md` - Skill orchestration engine
- `templates/skill_template.md` - Standard skill template

---

**End of RULES.md**

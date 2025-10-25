# 📝 SkillForge Template Guide

**Create custom skill templates for your tech stack**

This guide explains how to create custom templates for SkillForge skill generation.

---

## 📋 Table of Contents

- [Template Overview](#template-overview)
- [Template Syntax](#template-syntax)
- [Template Structure](#template-structure)
- [Variables](#variables)
- [Creating Custom Templates](#creating-custom-templates)
- [Testing Templates](#testing-templates)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Template Overview

### What Are Templates?

Templates are Handlebars-style files that define the structure and content of generated skills. SkillForge uses templates to create personalized SKILL.md files by combining:

- Framework-specific best practices
- Latest documentation (via Context7)
- User's personal conventions
- Code examples and patterns

### Template Types

**Tech Stack Templates** (`templates/tech-stack/`)
- Frontend frameworks (Next.js, React, Vue)
- Backend frameworks (FastAPI, Django, Express)
- UI libraries (Tailwind, shadcn/ui)

**Workflow Templates** (`templates/workflow/`)
- Git workflows
- Testing strategies
- Deployment pipelines

**Integration Templates** (`templates/integration/`)
- Database integrations (Supabase, MongoDB)
- Auth providers (NextAuth, Auth0)
- External APIs

---

## Template Syntax

SkillForge uses Handlebars/Mustache-style syntax.

### Variables

**Simple variables:**
```handlebars
{{variable_name}}
```

**Nested variables:**
```handlebars
{{user.preferences.naming.variables}}
{{framework.version}}
```

### Conditionals

```handlebars
{{#if condition}}
  Content when true
{{/if}}

{{#if condition}}
  Content when true
{{else}}
  Content when false
{{/if}}
```

### Loops

```handlebars
{{#each items}}
  - {{this}}
{{/each}}

{{#each items}}
  - {{name}}: {{description}}
{{/each}}
```

### Comments

```handlebars
{{! This is a comment }}
{{! Comments are not included in output }}
```

---

## Template Structure

### Required Components

Every template must have:

1. **YAML Frontmatter**
2. **Core sections**
3. **User conventions integration**
4. **Examples**

### Basic Template Structure

```handlebars
---
name: "{{skill_name}}"
description: >
  {{description}}
version: "{{version}}"
author: "SkillForge Auto-Generated"
generated_at: "{{timestamp}}"
based_on: "{{framework_name}} {{framework_version}}"
allowed-tools:
  - bash_tool
  - view
  - create_file
  - str_replace
{{#if additional_tools}}
{{#each additional_tools}}
  - {{this}}
{{/each}}
{{/if}}
---

# {{skill_name}}

## Overview

{{overview}}

{{#if framework_description}}
### About {{framework_name}}

{{framework_description}}
{{/if}}

## When to Use

Use this skill when:
{{#each use_cases}}
- {{this}}
{{/each}}

## Prerequisites

{{#each prerequisites}}
- {{this}}
{{/each}}

## Core Concepts

{{#each core_concepts}}
### {{name}}

{{description}}

{{#if code_example}}
```{{language}}
{{code_example}}
```
{{/if}}

{{/each}}

## Best Practices

{{#each best_practices}}
### {{category}}

{{#each items}}
- ✅ **DO**: {{do}}
- ❌ **DON'T**: {{dont}}
{{/each}}
{{/each}}

## User Conventions

{{#if has_user_conventions}}
Based on your preferences:

### Naming Conventions
{{#each user.preferences.naming}}
- **{{@key}}**: {{this}}
{{/each}}

### Import Style
- Style: {{user.preferences.imports.style}}
{{#if user.preferences.imports.alias}}
- Alias: `{{user.preferences.imports.alias}}`
{{/if}}

### Folder Structure
- Approach: {{user.preferences.structure}}
{{/if}}

## Common Patterns

{{#each patterns}}
### {{name}}

**Use Case**: {{use_case}}

**Implementation**:
```{{language}}
{{code}}
```

**Explanation**: {{explanation}}
{{/each}}

## Related Skills

{{#each related_skills}}
- `{{name}}` - {{description}}
{{/each}}

## Resources

{{#each resources}}
- [{{title}}]({{url}})
{{/each}}
```

---

## Variables

### Standard Variables

These variables are available in all templates:

**Metadata**
```handlebars
{{skill_name}}         - Skill name (e.g., "nextjs-fullstack")
{{description}}        - Brief description
{{version}}            - Skill version
{{timestamp}}          - Generation timestamp
```

**Framework**
```handlebars
{{framework_name}}     - Framework name (e.g., "Next.js")
{{framework_version}}  - Version (e.g., "15.0.0")
{{framework_description}} - Description from docs
```

**Documentation**
```handlebars
{{docs.overview}}           - Overview section
{{docs.best_practices}}     - Best practices array
{{docs.code_examples}}      - Code examples array
{{docs.api_reference}}      - API reference
```

**User Preferences**
```handlebars
{{user.preferences.naming.variables}}     - Variable naming (camelCase, etc.)
{{user.preferences.naming.components}}    - Component naming
{{user.preferences.imports.style}}        - Import style (absolute/relative)
{{user.preferences.imports.alias}}        - Import alias (@/, ~/, etc.)
{{user.preferences.structure}}            - Folder structure preference
```

**Arrays**
```handlebars
{{use_cases}}          - Array of use cases
{{prerequisites}}      - Array of prerequisites
{{core_concepts}}      - Array of core concepts
{{best_practices}}     - Array of best practices
{{patterns}}           - Array of common patterns
{{anti_patterns}}      - Array of anti-patterns
{{related_skills}}     - Array of related skills
{{resources}}          - Array of resource links
```

---

## Creating Custom Templates

### Step 1: Create Template File

```bash
# Create template file
mkdir -p ~/.claude/skills/skillforge/templates/custom/
vi ~/.claude/skills/skillforge/templates/custom/my-framework.template
```

### Step 2: Define Template Content

```handlebars
---
name: "{{skill_name}}"
description: >
  {{description}}
version: "1.0.0"
---

# {{framework_name}} Development

## Overview

{{framework_description}}

## Installation

```bash
{{#if package_manager}}
{{package_manager}} install {{framework_name}}
{{else}}
npm install {{framework_name}}
{{/if}}
```

## Quick Start

```{{language}}
{{quick_start_code}}
```

## User Conventions

{{#if user.preferences.naming.variables}}
- Variables: {{user.preferences.naming.variables}}
{{/if}}

{{#if user.preferences.imports.style}}
- Imports: {{user.preferences.imports.style}}
{{#if user.preferences.imports.alias}}
  with alias `{{user.preferences.imports.alias}}`
{{/if}}
{{/if}}

## Best Practices

{{#each best_practices}}
- ✅ {{this}}
{{/each}}
```

### Step 3: Register Template

Add your template to SkillGenerator:

```python
# In skillforge/generators/skill_generator.py

AVAILABLE_TEMPLATES = {
    # ... existing templates
    "my-framework": "custom/my-framework.template"
}
```

### Step 4: Test Template

```bash
# Generate skill using your template
/sf:generate my-framework --preview
```

---

## Testing Templates

### Manual Testing

```bash
# Preview generated output
/sf:generate my-framework --preview

# Generate and inspect
/sf:generate my-framework
cat ~/.claude/skills/my-framework/SKILL.md
```

### Automated Testing

```python
import pytest
from skillforge.generators import SkillGenerator

def test_custom_template():
    """Test custom template generation."""
    profile = {
        "tech_stack": {"framework": "MyFramework"},
        "preferences": {
            "naming": {"variables": "camelCase"},
            "imports": {"style": "absolute", "alias": "@/"}
        }
    }

    generator = SkillGenerator(profile)
    skill_path = generator.generate("my-framework")

    # Verify file exists
    assert skill_path.exists()

    # Verify content
    content = skill_path.read_text()
    assert "MyFramework" in content
    assert "camelCase" in content
    assert "@/" in content

    # Verify YAML frontmatter
    assert content.startswith("---")
```

---

## Best Practices

### 1. Start with Base Template

Copy an existing template as starting point:

```bash
cp skillforge/data/templates/tech-stack/nextjs-fullstack.template \
   ~/.claude/skills/skillforge/templates/custom/my-framework.template
```

### 2. Use Descriptive Variable Names

```handlebars
{{! Good }}
{{user.preferences.naming.variables}}

{{! Bad }}
{{naming}}
```

### 3. Provide Fallbacks

```handlebars
{{#if framework_version}}
Version: {{framework_version}}
{{else}}
Version: Latest
{{/if}}
```

### 4. Include User Conventions

Always inject user preferences:

```handlebars
## User Conventions

Based on your preferences:

{{#if user.preferences.naming}}
### Naming
{{#each user.preferences.naming}}
- **{{@key}}**: {{this}}
{{/each}}
{{/if}}

{{#if user.preferences.imports}}
### Imports
- Style: {{user.preferences.imports.style}}
{{#if user.preferences.imports.alias}}
- Alias: `{{user.preferences.imports.alias}}`
{{/if}}
{{/if}}
```

### 5. Add Real Examples

Include working code examples:

```handlebars
## Example Component

```{{language}}
{{#if user.preferences.naming.variables == "camelCase"}}
const myComponent = () => {
  const userName = "John";
  return <div>{userName}</div>;
};
{{else}}
const my_component = () => {
  const user_name = "John";
  return <div>{user_name}</div>;
};
{{/if}}
```
```

### 6. Structure for Progressive Disclosure

Organize content for progressive loading:

```handlebars
## Overview
[Critical, always loaded]

## Quick Start
[Core section, usually loaded]

## Best Practices
[Core section, usually loaded]

## Advanced Topics
[Details, loaded on demand]

## API Reference
[Details, loaded on demand]
```

### 7. Validate Template

Check for common issues:

```bash
# Check YAML frontmatter
head -20 generated-skill.md

# Verify all variables substituted
grep "{{" generated-skill.md  # Should return nothing

# Check file size
wc -l generated-skill.md  # Aim for 1500-3000 lines
```

---

## Examples

### Example 1: Frontend Framework Template

```handlebars
---
name: "{{framework_name}}-spa"
description: >
  {{framework_name}} single-page application development with YOUR conventions
version: "1.0.0"
---

# {{framework_name}} SPA Development

## Overview

{{framework_description}}

## Setup

```bash
{{package_manager}} create {{framework_name}}@latest my-app
cd my-app
{{package_manager}} install
```

## Project Structure

```
{{#if user.preferences.structure == "feature-based"}}
src/
├─ features/
│  ├─ auth/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  └─ api/
│  └─ dashboard/
└─ shared/
{{else}}
src/
├─ components/
├─ hooks/
├─ utils/
└─ api/
{{/if}}
```

## Component Pattern

```{{language}}
{{#if user.preferences.naming.components == "PascalCase"}}
const UserProfile = () => {
  {{#if user.preferences.naming.variables == "camelCase"}}
  const userName = "John";
  {{else}}
  const user_name = "John";
  {{/if}}
  return <div>{userName}</div>;
};
{{/if}}
```
```

### Example 2: Backend API Template

```handlebars
---
name: "{{framework_name}}-api"
description: >
  {{framework_name}} REST API development
---

# {{framework_name}} API Development

## Project Structure

```
app/
{{#if user.preferences.structure == "feature-based"}}
├─ features/
│  ├─ users/
│  │  ├─ routes.{{file_ext}}
│  │  ├─ models.{{file_ext}}
│  │  └─ services.{{file_ext}}
{{else}}
├─ routes/
├─ models/
├─ services/
{{/if}}
```

## Route Example

```{{language}}
{{#if language == "python"}}
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/{user_id}")
{{#if user.preferences.naming.functions == "snake_case"}}
async def get_user(user_id: int):
{{else}}
async def getUser(userId: int):
{{/if}}
    return {"id": user_id}
{{/if}}
```
```

### Example 3: Git Workflow Template

```handlebars
---
name: "git-workflow"
description: >
  Git workflow based on YOUR preferences
---

# Git Workflow

## Commit Messages

{{#if user.workflow.commit_format == "conventional"}}
Follow Conventional Commits:

```
<type>(<scope>): <description>

[optional body]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
{{else}}
Use semantic commit messages:
- Add: New feature
- Fix: Bug fix
- Update: Changes to existing
{{/if}}

## Branch Naming

{{#if user.workflow.branch_naming}}
Format: `{{user.workflow.branch_naming}}`

Examples:
- feature/user-authentication
- bugfix/api-cors-error
{{/if}}
```

---

## Variable Reference

### Complete Variable List

See [API Documentation](API.md) for full variable reference.

**Common variables:**

```json
{
  "skill_name": "nextjs-fullstack",
  "description": "Next.js fullstack development",
  "version": "1.0.0",
  "timestamp": "2025-10-23T10:00:00Z",
  "framework_name": "Next.js",
  "framework_version": "15.0.0",
  "language": "typescript",
  "user": {
    "preferences": {
      "naming": {
        "variables": "camelCase",
        "functions": "camelCase",
        "components": "PascalCase"
      },
      "imports": {
        "style": "absolute",
        "alias": "@/"
      },
      "structure": "feature-based"
    },
    "workflow": {
      "commit_format": "conventional",
      "branch_naming": "<type>/<description>"
    }
  },
  "docs": {
    "overview": "Documentation overview...",
    "best_practices": ["Practice 1", "Practice 2"],
    "code_examples": [...]
  }
}
```

---

## Troubleshooting

### Template Not Found

```bash
# Check template exists
ls ~/.claude/skills/skillforge/templates/custom/

# Register in SkillGenerator
vi skillforge/generators/skill_generator.py
```

### Variables Not Substituted

```bash
# Check variable names match
cat generated-skill.md | grep "{{"

# Ensure variable is provided in generator
```

### YAML Frontmatter Invalid

```bash
# Validate YAML
python3 -c "
import yaml
with open('generated-skill.md') as f:
    content = f.read()
    frontmatter = content.split('---')[1]
    yaml.safe_load(frontmatter)
"
```

---

## Contributing Templates

Want to share your template?

1. **Test thoroughly**
2. **Document variables**
3. **Add examples**
4. **Submit PR**

See [Contributing Guide](CONTRIBUTING.md) for details.

---

## Further Reading

- [Architecture](ARCHITECTURE.md) - How templates are processed
- [API Documentation](API.md) - TemplateProcessor API
- [Examples](../examples/) - Real template examples

---

**Happy templating!** 🎨

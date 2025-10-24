"""
Shared pytest fixtures and utilities for SkillForge test suite.
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


@pytest.fixture
def temp_home(tmp_path):
    """
    Create temporary SkillForge home directory for testing.

    This fixture creates a temporary directory structure that mimics the
    real SkillForge installation and configures the Config class to use it.

    Returns:
        Path: Path to temporary SkillForge home directory
    """
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)

    # Override Config paths
    from skillforge.generators.config import Config
    original_home = Config.SKILLFORGE_HOME
    original_data = Config.DATA_DIR
    original_cache = Config.CACHE_DIR

    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache"
    Config.ensure_directories()

    yield home

    # Restore original paths
    Config.SKILLFORGE_HOME = original_home
    Config.DATA_DIR = original_data
    Config.CACHE_DIR = original_cache


@pytest.fixture
def sample_profile() -> Dict[str, Any]:
    """
    Sample user profile for testing.

    Returns:
        Dict: Complete user profile with tech stack and preferences
    """
    return {
        "setup_completed": True,
        "setup_date": "2025-10-22",
        "tech_stack": {
            "frontend": "Next.js",
            "frontend_version": "14.0.0",
            "ui": "Tailwind CSS",
            "ui_version": "3.3.0",
            "state": "Zustand",
            "state_version": "4.4.0",
            "backend": "Next.js API Routes",
            "database": "Supabase",
            "database_version": "2.38.0",
            "testing": "Vitest",
            "testing_version": "1.0.0",
        },
        "preferences": {
            "naming": {
                "components": "PascalCase",
                "files": "kebab-case",
                "functions": "camelCase",
            },
            "structure": "feature-based",
            "styling": "Tailwind CSS utility classes",
            "testing": "Vitest with React Testing Library",
        },
        "workflows": {
            "git": {
                "commit_format": "conventional",
                "branch_format": "type/issue-description",
            }
        },
        "analytics_enabled": True,
    }


@pytest.fixture
def minimal_profile() -> Dict[str, Any]:
    """
    Minimal user profile for testing basic functionality.

    Returns:
        Dict: Minimal user profile
    """
    return {
        "setup_completed": True,
        "tech_stack": {
            "frontend": "React",
        },
    }


@pytest.fixture
def sample_usage_data() -> Dict[str, Any]:
    """
    Sample usage analytics for testing pattern detection.

    Returns:
        Dict: Usage analytics with skill usage data
    """
    return {
        "skill_usage": {
            "nextjs-fullstack": {
                "total_uses": 50,
                "successes": 47,
                "failures": 3,
                "last_used": "2025-10-22T10:30:00",
                "common_with": ["supabase-integration", "tailwind-styling"],
                "usage_history": [
                    {"date": "2025-10-20", "uses": 15},
                    {"date": "2025-10-21", "uses": 20},
                    {"date": "2025-10-22", "uses": 15},
                ]
            },
            "supabase-integration": {
                "total_uses": 45,
                "successes": 44,
                "failures": 1,
                "last_used": "2025-10-22T11:00:00",
                "common_with": ["nextjs-fullstack"],
                "usage_history": [
                    {"date": "2025-10-20", "uses": 12},
                    {"date": "2025-10-21", "uses": 18},
                    {"date": "2025-10-22", "uses": 15},
                ]
            },
        },
        "total_sessions": 30,
        "total_skill_loads": 95,
    }


@pytest.fixture
def sample_patterns() -> Dict[str, Any]:
    """
    Sample detected patterns for testing learning pipeline.

    Returns:
        Dict: Detected patterns with confidence scores
    """
    return {
        "combination": [
            {
                "pattern": ["nextjs-fullstack", "supabase-integration"],
                "confidence": 0.85,
                "occurrences": 42,
                "description": "Next.js with Supabase is used together frequently",
            }
        ],
        "style": [
            {
                "pattern": "prefer-server-components",
                "confidence": 0.90,
                "occurrences": 38,
                "description": "User prefers Server Components over Client Components",
            }
        ],
        "workflow": [
            {
                "pattern": "test-driven-development",
                "confidence": 0.75,
                "occurrences": 25,
                "description": "User writes tests before implementation",
            }
        ],
    }


@pytest.fixture
def mock_doc_content() -> str:
    """
    Mock documentation content from Context7.

    Returns:
        str: Sample documentation content
    """
    return """
# Next.js Documentation

## Server Components

Server Components are the default in Next.js App Router.

### Usage

```typescript
async function ServerComponent() {
  const data = await fetch('https://api.example.com/data')
  return <div>{data}</div>
}
```

## Best Practices

- Use Server Components by default
- Only mark components as 'use client' when needed
- Colocate components with routes
"""


def create_mock_skill(path: Path, name: str, content: str = None):
    """
    Create a mock SKILL.md file for testing with rich metadata.

    Args:
        path: Directory path where skill should be created
        name: Skill name
        content: Optional custom content (will use default if not provided)
    """
    if content is None:
        # Define skill-specific metadata for realistic testing
        skill_metadata = {
            "nextjs-fullstack": {
                "description": "Build fullstack Next.js applications with best practices",
                "triggers": ["next.js", "nextjs", "react", "fullstack", "app router"],
                "domain": "fullstack",
                "priority": 90,
            },
            "supabase-integration": {
                "description": "Integrate Supabase for auth, database, and storage",
                "triggers": ["supabase", "authentication", "auth", "database", "postgres"],
                "domain": "backend",
                "priority": 85,
            },
            "tailwind-styling": {
                "description": "Style applications using Tailwind CSS",
                "triggers": ["tailwind", "css", "styling", "ui", "design"],
                "domain": "frontend",
                "priority": 75,
            },
            "react-components": {
                "description": "Create reusable React components",
                "triggers": ["react", "component", "hooks", "ui", "frontend"],
                "domain": "frontend",
                "priority": 80,
            },
            "api-design": {
                "description": "Design RESTful and GraphQL APIs",
                "triggers": ["api", "rest", "graphql", "backend", "endpoint"],
                "domain": "backend",
                "priority": 70,
            },
        }

        metadata = skill_metadata.get(name, {
            "description": f"Mock skill for testing {name}",
            "triggers": [name.replace("-", " "), "testing"],
            "domain": "fullstack",
            "priority": 50,
        })

        triggers_yaml = "\n  - ".join(metadata["triggers"])

        content = f"""---
name: "{name}"
description: "{metadata['description']}"
version: "1.0.0"
triggers:
  - {triggers_yaml}
domain: "{metadata['domain']}"
priority: {metadata['priority']}
dependencies: []
---

# {name}

## Overview

{metadata['description']}

This skill provides comprehensive guidance and best practices.

## When to Use

- When building features with {name.replace('-', ' ')}
- For testing skill loading and discovery
- For testing pattern detection

## Core Concepts

### Key Concept

Understanding the fundamentals.

```typescript
// Example code
const example = {{
  skill: "{name}",
  type: "mock"
}};
```

## Best Practices

- Follow {name} best practices
- Write clear, testable code
- Use type-safe implementations

## Examples

```typescript
// Practical example
export function example() {{
  return {{ success: true }};
}}
```
"""

    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(content)


def create_mock_template(path: Path, template_name: str = None, skill_type: str = None):
    """
    Create a mock Handlebars template file for testing.

    Args:
        path: Directory path where template should be created (or full path to template file)
        template_name: Template filename (optional if path includes filename)
        skill_type: Type of skill (for content customization)
    """
    if template_name:
        full_path = path / template_name
    else:
        full_path = path

    content = f"""---
name: "{{{{skill_name}}}}"
description: "Production-ready {{{{skill_name}}}} implementation with comprehensive best practices and examples"
version: "{{{{version}}}}"
domain: "{{{{domain}}}}"
priority: 80
created_by: "SkillForge Test Suite"
created_at: "{{{{current_date}}}}"
---

# {{{{skill_name}}}}

## Overview

{{{{overview}}}}

{{% if tech_stack %}}
**Tech Stack**: {{{{tech_stack}}}}
{{% /if %}}

## When to Use

{{% each use_cases %}}
- {{{{this}}}}
{{% /each %}}

## Usage

This skill provides guidance for:
- Implementing {{{{skill_name}}}} features effectively
- Following industry-standard best practices
- Ensuring code quality and maintainability

## Best Practices

{{% if best_practices %}}
{{% each best_practices %}}
- {{{{this}}}}
{{% /each %}}
{{% else %}}
- Follow framework best practices
- Write comprehensive tests
- Use type-safe implementations
{{% /if %}}

## Examples

```typescript
// Example code
export function example() {{
  return {{ success: true }};
}}
```
"""

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)


@pytest.fixture
def skill_templates(temp_home, monkeypatch):
    """
    Create mock skill templates for testing skill generation.

    Args:
        temp_home: Temporary home directory fixture
        monkeypatch: Pytest fixture for patching

    Returns:
        Path: Path to templates directory
    """
    # Create temporary templates directory
    templates_dir = temp_home / "templates"

    # Create templates for commonly tested skill types
    skill_types = {
        "nextjs": "tech-stack/nextjs.hbs",
        "supabase": "integration/supabase.hbs",
        "git-workflow": "workflow/git-workflow.hbs",
        "react-component": "tech-stack/react-component.hbs",
        "api-endpoint": "tech-stack/api-endpoint.hbs",
    }

    for skill_type, rel_path in skill_types.items():
        template_path = templates_dir / rel_path
        create_mock_template(template_path, skill_type=skill_type)

    # Patch SkillGenerator to use our temporary templates directory
    from skillforge.generators.skill_generator import SkillGenerator
    monkeypatch.setattr(SkillGenerator, 'template_dir', templates_dir, raising=False)

    # Also need to add mappings for our test templates
    test_mappings = {
        'nextjs': 'tech-stack/nextjs.hbs',
        'supabase': 'integration/supabase.hbs',
        'git-workflow': 'workflow/git-workflow.hbs',
    }
    original_mappings = SkillGenerator.TEMPLATE_MAPPINGS.copy()
    SkillGenerator.TEMPLATE_MAPPINGS.update(test_mappings)

    yield templates_dir

    # Restore original mappings
    SkillGenerator.TEMPLATE_MAPPINGS = original_mappings


@pytest.fixture
def sample_skill_path(temp_home):
    """
    Create a sample skill file for testing.

    Args:
        temp_home: Temporary home directory fixture

    Returns:
        Path: Path to created skill
    """
    # Skills should be in ~/.claude/skills/ (parent of skillforge)
    skills_root = temp_home.parent
    skill_dir = skills_root / "nextjs-fullstack"
    create_mock_skill(skill_dir, "nextjs-fullstack")
    return skill_dir / "SKILL.md"


@pytest.fixture
def multiple_skills(temp_home):
    """
    Create multiple skills for testing discovery and orchestration.

    Args:
        temp_home: Temporary home directory fixture

    Returns:
        Dict[str, Path]: Dictionary mapping skill names to paths
    """
    skills = {}

    skill_names = [
        "nextjs-fullstack",
        "supabase-integration",
        "tailwind-styling",
        "react-components",
        "api-design",
    ]

    # Skills should be in ~/.claude/skills/ (parent of skillforge)
    skills_root = temp_home.parent

    for skill_name in skill_names:
        skill_dir = skills_root / skill_name
        create_mock_skill(skill_dir, skill_name)
        skills[skill_name] = skill_dir / "SKILL.md"

    return skills


@pytest.fixture
def config_with_profile(temp_home, sample_profile):
    """
    Create a Config instance with a saved user profile.

    Args:
        temp_home: Temporary home directory fixture
        sample_profile: Sample profile fixture

    Returns:
        Config: Configured Config instance
    """
    from skillforge.generators.config import Config

    config = Config()
    config.save_profile(sample_profile)

    return config


@pytest.fixture
def config_with_usage(temp_home, sample_usage_data):
    """
    Create a Config instance with saved usage analytics.

    Args:
        temp_home: Temporary home directory fixture
        sample_usage_data: Sample usage data fixture

    Returns:
        Config: Configured Config instance
    """
    from skillforge.generators.config import Config

    config = Config()
    config.save_analytics(sample_usage_data)

    return config


@pytest.fixture
def mock_context7_response():
    """
    Mock response from Context7 MCP server.

    Returns:
        Dict: Mock Context7 response
    """
    return {
        "library_id": "/vercel/next.js",
        "version": "14.0.0",
        "documentation": """
        # Next.js 14 Documentation

        ## App Router

        The App Router is the new paradigm for building applications with Next.js.

        ### Server Components

        All components are Server Components by default.

        ```typescript
        // This is a Server Component
        async function Page() {
          const data = await fetch('https://api.example.com')
          return <div>{data}</div>
        }
        ```
        """,
        "code_snippets": [
            {
                "title": "Server Component Example",
                "language": "typescript",
                "code": "async function ServerComponent() { ... }",
            }
        ],
        "best_practices": [
            "Use Server Components by default",
            "Only mark 'use client' when necessary",
        ],
    }


# Pytest configuration helpers

def pytest_configure(config):
    """
    Configure pytest with custom settings.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take more than 5 seconds"
    )

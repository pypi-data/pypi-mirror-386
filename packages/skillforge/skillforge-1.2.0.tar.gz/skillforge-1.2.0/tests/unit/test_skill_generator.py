"""
Unit tests for SkillGenerator class

Tests skill generation orchestration including:
- Variable preparation from profile and docs
- Generated skill validation
- Template path resolution
- Integration flow (with mocked components)
- Rollback functionality
"""

import json
import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from skillforge.generators.skill_generator import (
    SkillGenerator,
    SkillGenerationError,
    ValidationError
)
from skillforge.generators.doc_fetcher import LibraryDocs, DocSource
import time


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for templates and output"""
    template_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"

    template_dir.mkdir()
    output_dir.mkdir()

    # Create template subdirectories
    (template_dir / "tech-stack").mkdir()
    (template_dir / "workflow").mkdir()
    (template_dir / "integration").mkdir()

    return template_dir, output_dir


@pytest.fixture
def generator(temp_dirs):
    """Create SkillGenerator with temp directories and mock profile"""
    template_dir, output_dir = temp_dirs

    profile = {
        "setup_completed": True,
        "role": "Full-Stack Developer",
        "tech_stack": {
            "frontend": "React",
            "backend": "Express.js (Node)",
            "database": ["PostgreSQL"]
        },
        "preferences": {
            "role": "Full-Stack Developer",
            "code_style": ["TypeScript strict mode", "ESLint + Prettier"],
            "workflow": ["Git hooks (Husky)"]
        },
        "conventions": {
            "typescript": True,
            "linting": True,
            "formatting": True,
            "paradigm": ["functional"]
        }
    }

    return SkillGenerator(
        template_dir=template_dir,
        output_dir=output_dir,
        profile=profile
    )


@pytest.fixture
def sample_template():
    """Sample skill template"""
    return """---
name: {{skill_name}}
description: "Comprehensive {{framework_name}} guide covering modern component architecture, state management patterns, and production-ready best practices"
version: 1.0.0
created_by: {{generated_by}}
created_at: "{{creation_date}}"
---

# {{skill_name}}

## Overview

This skill helps you work with {{framework_name}}.

## Best Practices

{{#each best_practices}}
- {{this}}
{{/each}}

## Examples

{{#each code_examples}}
### {{description}}

```{{language}}
{{code}}
```
{{/each}}

## Usage

Use this skill with Claude Code by typing @{{skill_name}}.
"""


@pytest.fixture
def sample_docs():
    """Sample library documentation"""
    source = DocSource(
        type="mock",
        timestamp=time.time(),
        library_id="/facebook/react",
        version="18.2.0"
    )

    return LibraryDocs(
        library_id="/facebook/react",
        library_name="React",
        version="18.2.0",
        content="# React\n\nReact documentation.",
        examples=[
            {
                "code": "const [count, setCount] = useState(0);",
                "language": "javascript",
                "description": "useState hook example"
            },
            {
                "code": "useEffect(() => { fetchData(); }, []);",
                "language": "javascript",
                "description": "useEffect hook example"
            }
        ],
        best_practices=[
            "Use functional components with hooks",
            "Keep components small and focused",
            "Implement proper error boundaries"
        ],
        source=source,
        topics_covered=["hooks", "components", "state"],
        raw_data={}
    )


class TestPrepareVariables:
    """Test template variable preparation"""

    def test_prepare_variables_basic(self, generator, sample_docs):
        """Test basic variable preparation"""
        variables = generator.prepare_variables(
            skill_type="react-component",
            skill_name="my-react-skill",
            profile=generator.profile,
            docs=sample_docs
        )

        assert variables["skill_name"] == "my-react-skill"
        assert variables["skill_type"] == "react-component"
        assert variables["framework_name"] == "react"
        assert variables["framework_version"] == "18.2.0"
        assert variables["generated_by"] == "SkillForge"

    def test_prepare_variables_with_docs(self, generator, sample_docs):
        """Test variable preparation with documentation"""
        variables = generator.prepare_variables(
            skill_type="react-component",
            skill_name="test-skill",
            profile=generator.profile,
            docs=sample_docs
        )

        assert len(variables["best_practices"]) > 0
        assert len(variables["code_examples"]) > 0
        assert variables["documentation_source"] == "mock"
        assert len(variables["topics_covered"]) > 0

    def test_prepare_variables_without_docs(self, generator):
        """Test variable preparation without documentation"""
        variables = generator.prepare_variables(
            skill_type="react-component",
            skill_name="test-skill",
            profile=generator.profile,
            docs=None
        )

        assert variables["framework_version"] == "latest"
        assert len(variables["best_practices"]) > 0  # Should use defaults
        assert variables["code_examples"] == []
        assert variables["dependencies"] == []

    def test_prepare_variables_includes_profile_data(self, generator):
        """Test that variables include user profile data"""
        variables = generator.prepare_variables(
            skill_type="react-component",
            skill_name="test-skill",
            profile=generator.profile,
            docs=None
        )

        assert "user_tech_stack" in variables
        assert variables["user_tech_stack"]["frontend"] == "React"

        assert "user_preferences" in variables
        assert "user_conventions" in variables
        assert variables["user_conventions"]["typescript"] is True

    def test_prepare_variables_extracts_framework_name(self, generator):
        """Test framework name extraction from skill type"""
        # Test various skill types
        test_cases = [
            ("react-component", "react"),
            ("nextjs-page", "next.js"),
            ("vue-component", "vue"),
            ("express-api", "express"),
        ]

        for skill_type, expected_framework in test_cases:
            variables = generator.prepare_variables(
                skill_type=skill_type,
                skill_name="test",
                profile=generator.profile,
                docs=None
            )
            assert variables["framework_name"] == expected_framework

    def test_prepare_variables_includes_metadata(self, generator):
        """Test that generation metadata is included"""
        variables = generator.prepare_variables(
            skill_type="react-component",
            skill_name="test-skill",
            profile=generator.profile,
            docs=None
        )

        assert "generation_metadata" in variables
        metadata = variables["generation_metadata"]
        assert "version" in metadata
        assert "timestamp" in metadata
        assert "template" in metadata
        assert metadata["has_docs"] is False

    def test_prepare_variables_limits_examples(self, generator):
        """Test that examples are limited to avoid bloat"""
        # Create docs with many examples
        many_examples = [
            {"code": f"example{i}", "language": "js", "description": f"Ex {i}"}
            for i in range(20)
        ]

        source = DocSource("mock", time.time(), "/test/lib", "1.0.0")
        docs = LibraryDocs(
            library_id="/test/lib",
            library_name="test",
            version="1.0.0",
            content="Content",
            examples=many_examples,
            best_practices=["practice"] * 20,
            source=source,
            topics_covered=["topic"] * 20,
            raw_data={}
        )

        variables = generator.prepare_variables(
            skill_type="test-skill",
            skill_name="test",
            profile=generator.profile,
            docs=docs
        )

        # Should be limited
        assert len(variables["code_examples"]) <= 5
        assert len(variables["best_practices"]) <= 10
        assert len(variables["topics_covered"]) <= 5


class TestValidateGeneratedSkill:
    """Test validation of generated SKILL.md content"""

    def test_validate_skill_valid(self, generator):
        """Test validation of valid skill content"""
        valid_skill = """---
name: test-skill
description: A comprehensive skill for testing React components with best practices and modern patterns
version: 1.0.0
created_by: SkillForge
created_at: "2024-01-01"
---

# Test Skill

## Overview

This is a test skill for validation.

## Best Practices

- Use hooks properly
- Keep components focused

## Examples

### Example 1

```javascript
const Component = () => <div>Test</div>;
```

## Usage

Use this skill with @test-skill
"""

        # Should not raise error
        generator.validate_generated_skill(valid_skill, "test-skill")

    def test_validate_skill_missing_yaml(self, generator):
        """Test validation fails without YAML frontmatter"""
        invalid_skill = """# Test Skill

Some content without YAML frontmatter.
"""

        with pytest.raises(ValidationError, match="Missing or invalid YAML"):
            generator.validate_generated_skill(invalid_skill, "test-skill")

    def test_validate_skill_missing_required_fields(self, generator):
        """Test validation fails with missing required YAML fields"""
        invalid_skill = """---
name: test-skill
description: Test
---

# Content
"""

        with pytest.raises(ValidationError, match="Missing required YAML field"):
            generator.validate_generated_skill(invalid_skill, "test-skill")

    def test_validate_skill_missing_sections(self, generator):
        """Test validation fails with missing required sections"""
        invalid_skill = """---
name: test-skill
description: A comprehensive test skill with proper documentation
version: 1.0.0
created_by: SkillForge
created_at: 2024-01-01
---

# Test Skill

## Overview

Just an overview, missing other sections.
"""

        with pytest.raises(ValidationError, match="Missing required section"):
            generator.validate_generated_skill(invalid_skill, "test-skill")

    def test_validate_skill_with_placeholders(self, generator):
        """Test validation fails with unresolved placeholders"""
        invalid_skill = """---
name: test-skill
description: A comprehensive skill for {{framework_name}} development
version: 1.0.0
created_by: SkillForge
created_at: 2024-01-01
---

# Test Skill

## Overview
TODO: Add overview

## Best Practices
- Practice 1

## Examples
Example here

## Usage
Usage here
"""

        with pytest.raises(ValidationError, match="unresolved placeholders"):
            generator.validate_generated_skill(invalid_skill, "test-skill")

    def test_validate_skill_empty_code_blocks(self, generator):
        """Test validation fails with empty code blocks"""
        invalid_skill = """---
name: test-skill
description: A comprehensive test skill with examples
version: 1.0.0
created_by: SkillForge
created_at: 2024-01-01
---

# Test Skill

## Overview
Overview content

## Best Practices
- Best practice

## Examples

```javascript

```

## Usage
Usage info
"""

        with pytest.raises(ValidationError, match="empty code blocks"):
            generator.validate_generated_skill(invalid_skill, "test-skill")

    def test_validate_skill_generic_description(self, generator):
        """Test validation fails with generic description"""
        invalid_skill = """---
name: test-skill
description: "skill for testing"
version: 1.0.0
created_by: SkillForge
created_at: "2024-01-01"
---

# Test Skill

## Overview
Content

## Best Practices
- Practice

## Examples

```js
code()
```

## Usage
Usage
"""

        with pytest.raises(ValidationError, match="too generic"):
            generator.validate_generated_skill(invalid_skill, "test-skill")


class TestGetTemplatePath:
    """Test template path resolution"""

    def test_get_template_path_known_type(self, generator, temp_dirs):
        """Test getting template path for known skill type"""
        template_dir, _ = temp_dirs

        # Create a template file
        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text("Template content")

        result = generator.get_template_path("react-component")

        assert result == template_path
        assert result.exists()

    def test_get_template_path_unknown_type(self, generator):
        """Test getting template path for unknown skill type"""
        with pytest.raises(SkillGenerationError, match="Unknown skill type"):
            generator.get_template_path("nonexistent-skill-type")

    def test_get_template_path_mapped_but_missing(self, generator, temp_dirs):
        """Test error when template is mapped but file doesn't exist"""
        # react-component is mapped but file doesn't exist
        with pytest.raises(FileNotFoundError, match="Template mapped but not found"):
            generator.get_template_path("react-component")

    def test_get_template_path_searches_subdirs(self, generator, temp_dirs):
        """Test that template search works across subdirectories"""
        template_dir, _ = temp_dirs

        # Create template in workflow subdir with custom name
        custom_template = template_dir / "workflow" / "custom-skill.hbs"
        custom_template.write_text("Custom template")

        # Should find it even though not in TEMPLATE_MAPPINGS
        result = generator.get_template_path("custom-skill")
        assert result == custom_template


class TestIntegrationFlow:
    """Test integrated skill generation flow with mocks"""

    def test_generate_skill_complete_flow(self, generator, temp_dirs, sample_template, sample_docs):
        """Test complete skill generation flow"""
        template_dir, output_dir = temp_dirs

        # Create template file
        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text(sample_template)

        # Mock DocFetcher to return sample docs and prevent stdin issues
        with patch.object(generator.doc_fetcher, 'fetch', return_value=sample_docs):
            with patch('builtins.input', return_value=''):
                with patch('builtins.print'):
                    skill_path = generator.generate_skill(
                        skill_type="react-component",
                        skill_name="test-react-skill"
                    )

        assert skill_path.exists()
        assert skill_path.name == "SKILL.md"

        # Verify content
        content = skill_path.read_text()
        assert "test-react-skill" in content
        assert "React" in content or "react" in content
        assert "useState" in content  # From sample docs

    def test_generate_skill_creates_directory(self, generator, temp_dirs, sample_template):
        """Test that skill directory is created"""
        template_dir, output_dir = temp_dirs

        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text(sample_template)

        with patch.object(generator.doc_fetcher, 'fetch', return_value=None):
            with patch('builtins.input', return_value=''):
                with patch('builtins.print'):
                    skill_path = generator.generate_skill(
                        skill_type="react-component",
                        skill_name="test-skill"
                    )

        skill_dir = skill_path.parent
        assert skill_dir.exists()
        assert skill_dir.name == "test-skill"
        assert (skill_dir / "examples").exists()

    def test_generate_skill_saves_metadata(self, generator, temp_dirs, sample_template):
        """Test that metadata file is created"""
        template_dir, output_dir = temp_dirs

        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text(sample_template)

        with patch.object(generator.doc_fetcher, 'fetch', return_value=None):
            with patch('builtins.input', return_value=''):
                with patch('builtins.print'):
                    skill_path = generator.generate_skill(
                        skill_type="react-component",
                        skill_name="test-skill"
                    )

        metadata_path = skill_path.parent / ".skillforge.json"
        assert metadata_path.exists()

        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["skill_name"] == "test-skill"
        assert metadata["skill_type"] == "react-component"

    def test_generate_skill_handles_template_error(self, generator, temp_dirs):
        """Test that generation handles template processing errors"""
        template_dir, output_dir = temp_dirs

        # Create invalid template
        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text("---\ninvalid: {{missing_required_field\n---\nContent")

        with pytest.raises(SkillGenerationError):
            generator.generate_skill(
                skill_type="react-component",
                skill_name="test-skill"
            )

    def test_generate_skill_rollback_on_error(self, generator, temp_dirs, sample_template):
        """Test that failed generation triggers rollback"""
        template_dir, output_dir = temp_dirs

        # Create template that will fail validation
        invalid_template = """---
name: {{skill_name}}
description: TODO
version: 1.0.0
created_by: {{generated_by}}
created_at: {{creation_date}}
---

# {{skill_name}}

Missing required sections
"""
        template_path = template_dir / "tech-stack" / "react-component.hbs"
        template_path.write_text(invalid_template)

        with pytest.raises(SkillGenerationError):
            generator.generate_skill(
                skill_type="react-component",
                skill_name="test-skill"
            )

        # Skill directory should not exist after rollback
        skill_dir = output_dir / "test-skill"
        assert not skill_dir.exists()


class TestRollback:
    """Test rollback functionality"""

    def test_rollback_removes_directory(self, generator, temp_dirs):
        """Test that rollback removes skill directory"""
        _, output_dir = temp_dirs

        # Create skill directory with files
        skill_dir = output_dir / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("Content")
        (skill_dir / "examples").mkdir()

        # Rollback
        generator.rollback("test-skill")

        assert not skill_dir.exists()

    def test_rollback_handles_nonexistent_directory(self, generator):
        """Test that rollback handles nonexistent directory gracefully"""
        # Should not raise error
        generator.rollback("nonexistent-skill")


class TestHelperMethods:
    """Test helper methods"""

    def test_extract_framework_name(self, generator):
        """Test framework name extraction"""
        assert generator._extract_framework_name("react-component") == "react"
        assert generator._extract_framework_name("nextjs-page") == "next.js"
        assert generator._extract_framework_name("vue-component") == "vue"
        assert generator._extract_framework_name("express-api") == "express"

    def test_extract_topic_from_skill_type(self, generator):
        """Test topic extraction from skill type"""
        assert generator._extract_topic_from_skill_type("react-hooks") == "hooks"
        assert generator._extract_topic_from_skill_type("nextjs-routing") == "routing"
        assert generator._extract_topic_from_skill_type("vue-composition-api") == "composition-api"
        assert generator._extract_topic_from_skill_type("react") is None

    def test_get_default_best_practices(self, generator):
        """Test getting default best practices"""
        react_practices = generator._get_default_best_practices("react")
        assert len(react_practices) > 0
        assert any("functional" in p.lower() for p in react_practices)

        express_practices = generator._get_default_best_practices("express")
        assert len(express_practices) > 0
        assert any("middleware" in p.lower() for p in express_practices)

        # Unknown framework should return generic practices
        unknown_practices = generator._get_default_best_practices("unknown")
        assert len(unknown_practices) > 0

    def test_list_available_templates(self, generator):
        """Test listing available template types"""
        templates = generator._list_available_templates()

        assert "react-component" in templates
        assert "nextjs-page" in templates
        assert "express-api" in templates
        assert isinstance(templates, list)

    def test_extract_yaml_frontmatter_valid(self, generator):
        """Test YAML frontmatter extraction"""
        content = """---
name: test
version: 1.0.0
---

# Content here
"""
        yaml_data, markdown = generator._extract_yaml_frontmatter(content)

        assert yaml_data is not None
        assert yaml_data["name"] == "test"
        assert yaml_data["version"] == "1.0.0"
        assert "Content here" in markdown

    def test_extract_yaml_frontmatter_invalid(self, generator):
        """Test YAML extraction with invalid YAML"""
        content = """---
invalid: yaml: here:
---

Content
"""
        yaml_data, markdown = generator._extract_yaml_frontmatter(content)

        assert yaml_data is None
        assert "Content" in markdown

    def test_has_section(self, generator):
        """Test section detection in markdown"""
        content = """
# Main Title

## Overview

Some content

## Examples

More content
"""
        assert generator._has_section(content, "Overview") is True
        assert generator._has_section(content, "Examples") is True
        assert generator._has_section(content, "Nonexistent") is False

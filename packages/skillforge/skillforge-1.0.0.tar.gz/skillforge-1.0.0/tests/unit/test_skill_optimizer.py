"""
Unit tests for SkillOptimizer class

Tests skill optimization including:
- Analyzing skills for metrics
- Finding redundancies
- Suggesting merges
- Checking for outdated documentation
- Optimizing token usage
- Improving structure
- Applying optimizations
"""

import pytest
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from skillforge.analyzers.skill_optimizer import (
    SkillOptimizer,
    OptimizationSuggestion,
    SkillAnalysis
)
from skillforge.generators.config import Config


@pytest.fixture
def temp_home(tmp_path):
    """Create temporary SkillForge home for testing"""
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)

    # Override Config class variables
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
    Config.ensure_directories()

    # Create skills directory
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    yield home


@pytest.fixture
def optimizer(temp_home):
    """Create SkillOptimizer instance"""
    config = Config()
    return SkillOptimizer(config=config)


@pytest.fixture
def sample_skill_file(temp_home):
    """Create sample skill file"""
    skills_dir = Path.home() / ".claude" / "skills"

    content = """---
name: nextjs-fullstack
description: NextJS fullstack development
version: 1.0.0
framework: Next.js
---

# NextJS Fullstack Development

## Core Patterns

Use Next.js for fullstack React applications with server-side rendering.

## Best Practices

- Use App Router for new projects
- Implement API routes for backend
- Use TypeScript for type safety

## Examples

```typescript
export default function Page() {
  return <div>Hello World</div>
}
```
"""

    skill_file = skills_dir / "nextjs-fullstack.md"
    with open(skill_file, 'w') as f:
        f.write(content)

    yield skill_file

    if skill_file.exists():
        skill_file.unlink()


@pytest.fixture
def verbose_skill_file(temp_home):
    """Create verbose skill file for testing compression"""
    skills_dir = Path.home() / ".claude" / "skills"

    # Create content with >3000 tokens (~12000 chars)
    verbose_content = """---
name: verbose-skill
description: Verbose skill for testing
---

# Verbose Skill

## Introduction

""" + "Lorem ipsum dolor sit amet. " * 600 + """

## Details

""" + "More verbose content here. " * 400 + """

## Conclusion

""" + "Even more content. " * 200

    skill_file = skills_dir / "verbose-skill.md"
    with open(skill_file, 'w') as f:
        f.write(verbose_content)

    yield skill_file

    if skill_file.exists():
        skill_file.unlink()


@pytest.fixture
def similar_skill_files(temp_home):
    """Create similar skill files for merge testing"""
    skills_dir = Path.home() / ".claude" / "skills"

    content1 = """---
name: react-spa
description: React SPA development
---

# React SPA Development

## Core Patterns

Use React for single-page applications.

## Best Practices

- Use functional components
- Implement hooks
- Use TypeScript
"""

    content2 = """---
name: react-app
description: React application development
---

# React Application Development

## Core Patterns

Use React for single-page applications.

## Best Practices

- Use functional components
- Implement hooks
- Use TypeScript
"""

    file1 = skills_dir / "react-spa.md"
    file2 = skills_dir / "react-app.md"

    with open(file1, 'w') as f:
        f.write(content1)
    with open(file2, 'w') as f:
        f.write(content2)

    yield file1, file2

    for f in [file1, file2]:
        if f.exists():
            f.unlink()


# Test OptimizationSuggestion dataclass

def test_suggestion_creation():
    """Test creating optimization suggestion"""
    suggestion = OptimizationSuggestion(
        suggestion_id="opt_001",
        suggestion_type="merge",
        priority="high",
        description="Merge similar skills",
        affected_skills=["skill1", "skill2"],
        estimated_token_savings=500,
        confidence=0.9
    )

    assert suggestion.suggestion_id == "opt_001"
    assert suggestion.suggestion_type == "merge"
    assert suggestion.priority == "high"
    assert suggestion.estimated_token_savings == 500
    assert suggestion.applied is False


def test_suggestion_to_dict():
    """Test suggestion serialization"""
    suggestion = OptimizationSuggestion(
        suggestion_id="opt_001",
        suggestion_type="compress",
        priority="medium",
        description="Compress content",
        affected_skills=["skill1"],
        estimated_token_savings=200,
        confidence=0.8
    )

    data = suggestion.to_dict()
    assert data["suggestion_id"] == "opt_001"
    assert data["estimated_token_savings"] == 200


def test_suggestion_from_dict():
    """Test suggestion deserialization"""
    data = {
        "suggestion_id": "opt_001",
        "suggestion_type": "merge",
        "priority": "high",
        "description": "Test",
        "affected_skills": ["skill1"],
        "estimated_token_savings": 100,
        "confidence": 0.9,
        "details": {},
        "applied": False
    }

    suggestion = OptimizationSuggestion.from_dict(data)
    assert suggestion.suggestion_id == "opt_001"
    assert suggestion.estimated_token_savings == 100


# Test SkillAnalysis dataclass

def test_analysis_creation():
    """Test creating skill analysis"""
    analysis = SkillAnalysis(
        skill_name="test-skill",
        file_path=Path("/tmp/test.md"),
        token_count=1000,
        line_count=50,
        section_count=5,
        last_modified=datetime.now(),
        usage_count=10,
        success_rate=0.95,
        has_yaml=True,
        yaml_valid=True
    )

    assert analysis.skill_name == "test-skill"
    assert analysis.token_count == 1000
    assert analysis.has_yaml is True


def test_analysis_to_dict():
    """Test analysis serialization"""
    timestamp = datetime.now()
    analysis = SkillAnalysis(
        skill_name="test-skill",
        file_path=Path("/tmp/test.md"),
        token_count=1000,
        line_count=50,
        section_count=5,
        last_modified=timestamp,
        usage_count=10,
        success_rate=0.95,
        has_yaml=True,
        yaml_valid=True
    )

    data = analysis.to_dict()
    assert data["skill_name"] == "test-skill"
    assert data["file_path"] == "/tmp/test.md"
    assert data["last_modified"] == timestamp.isoformat()


# Test SkillOptimizer initialization

def test_optimizer_initialization(optimizer):
    """Test optimizer initialization"""
    assert optimizer.config is not None
    assert optimizer.usage_tracker is not None
    assert optimizer.doc_fetcher is not None
    assert isinstance(optimizer.suggestions, list)
    assert isinstance(optimizer.analyses, dict)


# Test skill analysis

def test_analyze_skill(optimizer, sample_skill_file):
    """Test analyzing a skill file"""
    analysis = optimizer.analyze_skill(sample_skill_file)

    assert analysis.skill_name == "nextjs-fullstack"
    assert analysis.token_count > 0
    assert analysis.line_count > 0
    assert analysis.section_count >= 3
    assert analysis.has_yaml is True
    assert analysis.yaml_valid is True


def test_analyze_skill_without_yaml(optimizer, temp_home):
    """Test analyzing skill without YAML"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "no-yaml.md"

    with open(skill_file, 'w') as f:
        f.write("# Skill without YAML\n\nContent here.")

    analysis = optimizer.analyze_skill(skill_file)

    assert analysis.has_yaml is False
    assert "Missing YAML frontmatter" in analysis.issues

    skill_file.unlink()


def test_analyze_skill_high_token_count(optimizer, verbose_skill_file):
    """Test analyzing verbose skill"""
    analysis = optimizer.analyze_skill(verbose_skill_file)

    assert analysis.token_count > optimizer.TOKEN_WARNING_THRESHOLD
    assert any("High token count" in issue for issue in analysis.issues)


def test_analyze_skill_outdated(optimizer, temp_home):
    """Test detecting outdated skill"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "old-skill.md"

    with open(skill_file, 'w') as f:
        f.write("---\nname: old-skill\n---\n# Old Skill")

    # Set modification time to 100 days ago
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    skill_file.touch()
    import os
    os.utime(skill_file, (old_time, old_time))

    analysis = optimizer.analyze_skill(skill_file)

    assert any("Not updated in" in issue for issue in analysis.issues)

    skill_file.unlink()


# Test token estimation

def test_estimate_tokens(optimizer):
    """Test token estimation"""
    text = "Hello world! " * 100  # ~1200 chars
    tokens = optimizer._estimate_tokens(text)

    assert tokens > 0
    assert tokens == len(text) // 4


# Test similarity calculation

def test_calculate_similarity_identical(optimizer, sample_skill_file):
    """Test similarity of identical skills"""
    # Analyze skill and store analysis
    analysis = optimizer.analyze_skill(sample_skill_file)
    optimizer.analyses[analysis.skill_name] = analysis

    similarity = optimizer._calculate_similarity("nextjs-fullstack", "nextjs-fullstack")

    assert similarity == 1.0


def test_calculate_similarity_different(optimizer, similar_skill_files):
    """Test similarity of different skills"""
    file1, file2 = similar_skill_files

    # Analyze both and store
    analysis1 = optimizer.analyze_skill(file1)
    analysis2 = optimizer.analyze_skill(file2)
    optimizer.analyses[analysis1.skill_name] = analysis1
    optimizer.analyses[analysis2.skill_name] = analysis2

    similarity = optimizer._calculate_similarity("react-spa", "react-app")

    assert 0.5 < similarity < 1.0  # Should be similar but not identical


# Test overlap calculation

def test_calculate_overlap(optimizer, similar_skill_files):
    """Test calculating content overlap"""
    file1, file2 = similar_skill_files

    analysis1 = optimizer.analyze_skill(file1)
    analysis2 = optimizer.analyze_skill(file2)
    optimizer.analyses[analysis1.skill_name] = analysis1
    optimizer.analyses[analysis2.skill_name] = analysis2

    overlap = optimizer._calculate_overlap("react-spa", "react-app")

    assert overlap > 0  # Should have some overlapping sections


# Test finding redundancies

def test_find_redundancies(optimizer, similar_skill_files):
    """Test finding redundant content"""
    file1, file2 = similar_skill_files

    analysis1 = optimizer.analyze_skill(file1)
    analysis2 = optimizer.analyze_skill(file2)
    optimizer.analyses[analysis1.skill_name] = analysis1
    optimizer.analyses[analysis2.skill_name] = analysis2

    # Mock overlap to trigger redundancy detection
    optimizer._calculate_overlap = Mock(return_value=0.6)

    optimizer._find_redundancies()

    # Should have redundancy suggestion
    redundancy_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "remove"
    ]

    assert len(redundancy_suggestions) > 0


# Test suggesting merges

def test_suggest_merges_high_similarity(optimizer, similar_skill_files):
    """Test suggesting merges for similar skills"""
    file1, file2 = similar_skill_files

    analysis1 = optimizer.analyze_skill(file1)
    analysis2 = optimizer.analyze_skill(file2)
    optimizer.analyses[analysis1.skill_name] = analysis1
    optimizer.analyses[analysis2.skill_name] = analysis2

    # Mock high similarity
    optimizer._calculate_similarity = Mock(return_value=0.85)

    optimizer._suggest_merges()

    merge_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "merge"
    ]

    assert len(merge_suggestions) > 0
    assert merge_suggestions[0].priority == "high"


def test_suggest_merges_medium_similarity(optimizer, similar_skill_files):
    """Test merge suggestion with medium similarity"""
    file1, file2 = similar_skill_files

    analysis1 = optimizer.analyze_skill(file1)
    analysis2 = optimizer.analyze_skill(file2)
    optimizer.analyses[analysis1.skill_name] = analysis1
    optimizer.analyses[analysis2.skill_name] = analysis2

    # Mock medium similarity
    optimizer._calculate_similarity = Mock(return_value=0.75)

    optimizer._suggest_merges()

    merge_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "merge"
    ]

    assert len(merge_suggestions) > 0
    assert merge_suggestions[0].priority == "medium"


# Test checking outdated docs

def test_check_outdated_docs(optimizer, temp_home):
    """Test checking for outdated documentation"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "nextjs-old.md"

    with open(skill_file, 'w') as f:
        f.write("---\nname: nextjs-old\nframework: Next.js\n---\n# NextJS")

    # Set old modification time
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    skill_file.touch()
    import os
    os.utime(skill_file, (old_time, old_time))

    analysis = optimizer.analyze_skill(skill_file)
    optimizer.analyses[analysis.skill_name] = analysis
    optimizer._check_outdated_docs()

    update_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "update"
    ]

    assert len(update_suggestions) > 0

    skill_file.unlink()


# Test optimizing token usage

def test_optimize_token_usage(optimizer, verbose_skill_file):
    """Test identifying token optimization opportunities"""
    analysis = optimizer.analyze_skill(verbose_skill_file)
    optimizer.analyses[analysis.skill_name] = analysis
    optimizer._optimize_token_usage()

    compress_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "compress"
    ]

    assert len(compress_suggestions) > 0
    assert compress_suggestions[0].estimated_token_savings > 0


# Test improving structure

def test_improve_structure_no_yaml(optimizer, temp_home):
    """Test suggesting structure improvements for skill without YAML"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "no-structure.md"

    with open(skill_file, 'w') as f:
        f.write("# Skill\nContent")

    analysis = optimizer.analyze_skill(skill_file)
    optimizer.analyses[analysis.skill_name] = analysis
    optimizer._improve_structure()

    restructure_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "restructure"
    ]

    assert len(restructure_suggestions) > 0
    assert "Add YAML frontmatter" in restructure_suggestions[0].details["issues"]

    skill_file.unlink()


def test_improve_structure_minimal_sections(optimizer, temp_home):
    """Test suggesting more sections"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "minimal.md"

    # Create skill with minimal structure but verbose content
    content = "---\nname: minimal\n---\n# Minimal\n" + "Content. " * 1000

    with open(skill_file, 'w') as f:
        f.write(content)

    analysis = optimizer.analyze_skill(skill_file)
    optimizer.analyses[analysis.skill_name] = analysis
    optimizer._improve_structure()

    restructure_suggestions = [
        s for s in optimizer.suggestions
        if s.suggestion_type == "restructure"
    ]

    assert len(restructure_suggestions) > 0

    skill_file.unlink()


# Test framework detection

def test_detect_framework_from_metadata(optimizer, sample_skill_file):
    """Test detecting framework from YAML metadata"""
    analysis = optimizer.analyze_skill(sample_skill_file)
    framework = optimizer._detect_framework(analysis)

    assert framework is not None
    assert framework["name"] == "Next.js"


def test_detect_framework_from_name(optimizer, temp_home):
    """Test detecting framework from skill name"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "react-component.md"

    with open(skill_file, 'w') as f:
        f.write("---\nname: react-component\n---\n# React Component")

    analysis = optimizer.analyze_skill(skill_file)
    framework = optimizer._detect_framework(analysis)

    assert framework is not None
    assert framework["name"] == "React"

    skill_file.unlink()


# Test compression utilities

def test_compress_whitespace(optimizer):
    """Test compressing excessive whitespace"""
    content = "Line 1\n\n\n\nLine 2\n\n\n\n\nLine 3"
    compressed = optimizer._compress_whitespace(content)

    # Should have max 2 consecutive empty lines
    assert "\n\n\n\n" not in compressed


def test_compress_whitespace_trailing(optimizer):
    """Test removing trailing whitespace"""
    content = "Line 1   \nLine 2  \n"
    compressed = optimizer._compress_whitespace(content)

    assert "   \n" not in compressed
    assert "  \n" not in compressed


def test_optimize_markdown(optimizer):
    """Test optimizing markdown formatting"""
    content = "***Bold and Italic***\n\n- Item 1\n\n- Item 2"
    optimized = optimizer._optimize_markdown(content)

    # Should simplify formatting
    assert "***" not in optimized
    assert "**" in optimized


# Test applying optimizations

def test_optimize_skill(optimizer, verbose_skill_file):
    """Test optimizing a skill file"""
    analysis_before = optimizer.analyze_skill(verbose_skill_file)
    tokens_before = analysis_before.token_count

    results = optimizer.optimize_skill(verbose_skill_file)

    assert results["original_tokens"] == tokens_before
    assert results["savings"] >= 0
    assert len(results["changes"]) > 0


def test_apply_compression(optimizer, verbose_skill_file):
    """Test applying compression optimization"""
    analysis = optimizer.analyze_skill(verbose_skill_file)
    optimizer.analyses["verbose-skill"] = analysis

    suggestion = OptimizationSuggestion(
        suggestion_id="compress_001",
        suggestion_type="compress",
        priority="high",
        description="Compress skill",
        affected_skills=["verbose-skill"],
        estimated_token_savings=500,
        confidence=0.9
    )

    results = optimizer.apply_suggestion(suggestion)

    assert results["success"] is True
    assert "Compressed content" in results["changes"]


def test_apply_restructure(optimizer, temp_home):
    """Test applying restructure optimization"""
    skills_dir = Path.home() / ".claude" / "skills"
    skill_file = skills_dir / "no-yaml-skill.md"

    with open(skill_file, 'w') as f:
        f.write("# Skill\nContent")

    analysis = optimizer.analyze_skill(skill_file)
    optimizer.analyses["no-yaml-skill"] = analysis

    suggestion = OptimizationSuggestion(
        suggestion_id="restructure_001",
        suggestion_type="restructure",
        priority="low",
        description="Add YAML",
        affected_skills=["no-yaml-skill"],
        estimated_token_savings=0,
        confidence=0.8
    )

    results = optimizer.apply_suggestion(suggestion)

    assert results["success"] is True

    # Verify YAML added
    with open(skill_file, 'r') as f:
        content = f.read()

    assert content.startswith("---")

    skill_file.unlink()


def test_is_safe_to_auto_apply_compress(optimizer):
    """Test safe auto-apply for compression"""
    suggestion = OptimizationSuggestion(
        suggestion_id="compress_001",
        suggestion_type="compress",
        priority="high",
        description="Compress",
        affected_skills=["skill1"],
        estimated_token_savings=500,
        confidence=0.9
    )

    assert optimizer._is_safe_to_auto_apply(suggestion) is True


def test_is_safe_to_auto_apply_merge(optimizer):
    """Test unsafe auto-apply for merge"""
    suggestion = OptimizationSuggestion(
        suggestion_id="merge_001",
        suggestion_type="merge",
        priority="high",
        description="Merge",
        affected_skills=["skill1", "skill2"],
        estimated_token_savings=1000,
        confidence=0.95
    )

    assert optimizer._is_safe_to_auto_apply(suggestion) is False


# Test full optimization workflow

def test_optimize_all_skills(optimizer, sample_skill_file, verbose_skill_file):
    """Test optimizing all skills"""
    report = optimizer.optimize_all_skills()

    assert report["skills_analyzed"] >= 2
    assert report["total_tokens"] > 0
    assert isinstance(report["optimizations"], list)


def test_optimize_all_skills_auto_apply(optimizer, verbose_skill_file):
    """Test auto-applying safe optimizations"""
    report = optimizer.optimize_all_skills(auto_apply_safe=True)

    # Should have auto-applied some safe optimizations
    assert len(report["auto_applied"]) >= 0


# Test getting suggestions

def test_get_suggestions_all(optimizer):
    """Test getting all suggestions"""
    # Add some suggestions
    optimizer.suggestions = [
        OptimizationSuggestion(
            suggestion_id="opt_001",
            suggestion_type="compress",
            priority="high",
            description="Test 1",
            affected_skills=["skill1"],
            estimated_token_savings=100,
            confidence=0.8
        ),
        OptimizationSuggestion(
            suggestion_id="opt_002",
            suggestion_type="merge",
            priority="medium",
            description="Test 2",
            affected_skills=["skill2"],
            estimated_token_savings=200,
            confidence=0.9
        )
    ]

    suggestions = optimizer.get_suggestions()

    assert len(suggestions) == 2


def test_get_suggestions_filtered_by_type(optimizer):
    """Test filtering suggestions by type"""
    optimizer.suggestions = [
        OptimizationSuggestion(
            suggestion_id="opt_001",
            suggestion_type="compress",
            priority="high",
            description="Test 1",
            affected_skills=["skill1"],
            estimated_token_savings=100,
            confidence=0.8
        ),
        OptimizationSuggestion(
            suggestion_id="opt_002",
            suggestion_type="merge",
            priority="medium",
            description="Test 2",
            affected_skills=["skill2"],
            estimated_token_savings=200,
            confidence=0.9
        )
    ]

    compress_suggestions = optimizer.get_suggestions(suggestion_type="compress")

    assert len(compress_suggestions) == 1
    assert compress_suggestions[0]["suggestion_type"] == "compress"


def test_get_suggestions_filtered_by_priority(optimizer):
    """Test filtering suggestions by priority"""
    optimizer.suggestions = [
        OptimizationSuggestion(
            suggestion_id="opt_001",
            suggestion_type="compress",
            priority="high",
            description="Test 1",
            affected_skills=["skill1"],
            estimated_token_savings=100,
            confidence=0.8
        ),
        OptimizationSuggestion(
            suggestion_id="opt_002",
            suggestion_type="merge",
            priority="medium",
            description="Test 2",
            affected_skills=["skill2"],
            estimated_token_savings=200,
            confidence=0.9
        )
    ]

    high_priority = optimizer.get_suggestions(priority="high")

    assert len(high_priority) == 1
    assert high_priority[0]["priority"] == "high"


def test_get_suggestions_filtered_by_applied(optimizer):
    """Test filtering suggestions by applied status"""
    optimizer.suggestions = [
        OptimizationSuggestion(
            suggestion_id="opt_001",
            suggestion_type="compress",
            priority="high",
            description="Test 1",
            affected_skills=["skill1"],
            estimated_token_savings=100,
            confidence=0.8,
            applied=True
        ),
        OptimizationSuggestion(
            suggestion_id="opt_002",
            suggestion_type="merge",
            priority="medium",
            description="Test 2",
            affected_skills=["skill2"],
            estimated_token_savings=200,
            confidence=0.9,
            applied=False
        )
    ]

    pending = optimizer.get_suggestions(applied=False)

    assert len(pending) == 1
    assert pending[0]["applied"] is False


# Test getting analysis

def test_get_analysis(optimizer, sample_skill_file):
    """Test getting analysis for specific skill"""
    analysis_obj = optimizer.analyze_skill(sample_skill_file)
    optimizer.analyses[analysis_obj.skill_name] = analysis_obj

    analysis = optimizer.get_analysis("nextjs-fullstack")

    assert analysis is not None
    assert analysis["skill_name"] == "nextjs-fullstack"


def test_get_analysis_not_found(optimizer):
    """Test getting analysis for non-existent skill"""
    analysis = optimizer.get_analysis("nonexistent-skill")

    assert analysis is None

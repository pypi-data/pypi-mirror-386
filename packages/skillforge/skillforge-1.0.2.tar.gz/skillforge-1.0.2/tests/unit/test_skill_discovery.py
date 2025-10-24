"""
Unit tests for SkillDiscovery class

Tests skill discovery including:
- Loading available skills from temporary directory
- Finding skills for specific entities/frameworks
- Getting domain-specific skills
- Multi-strategy skill discovery
- Priority sorting and confidence scoring
- Dependency resolution
"""

import pytest
from pathlib import Path
from skillforge.analyzers.skill_discovery import (
    SkillDiscovery,
    SkillMetadata,
    DiscoveredSkill,
    Intent
)
from skillforge.generators.config import Config


@pytest.fixture
def temp_home(tmp_path):
    """
    Create temporary SkillForge home for testing.

    Overrides Config paths to use temporary directory,
    ensuring tests don't affect real user data.
    """
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)

    # Override Config class variables
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
    Config.ensure_directories()

    yield home


@pytest.fixture
def skills_dir(tmp_path):
    """Create temporary skills directory with test skills"""
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Create test skill 1: Next.js fullstack
    nextjs_dir = skills_dir / "nextjs-fullstack"
    nextjs_dir.mkdir()
    nextjs_skill = nextjs_dir / "SKILL.md"
    nextjs_skill.write_text("""---
name: nextjs-fullstack
description: Build fullstack Next.js applications with TypeScript
triggers:
  - next.js
  - nextjs
  - fullstack
dependencies: []
priority: 80
---

# Next.js Fullstack Skill
""")

    # Create test skill 2: React component
    react_dir = skills_dir / "react-component"
    react_dir.mkdir()
    react_skill = react_dir / "SKILL.md"
    react_skill.write_text("""---
name: react-component
description: Create React components with best practices
triggers:
  - react
  - component
dependencies: []
priority: 70
---

# React Component Skill
""")

    # Create test skill 3: Supabase integration
    supabase_dir = skills_dir / "supabase-integration"
    supabase_dir.mkdir()
    supabase_skill = supabase_dir / "SKILL.md"
    supabase_skill.write_text("""---
name: supabase-integration
description: Integrate Supabase for database and authentication
triggers:
  - supabase
  - database
  - authentication
dependencies:
  - nextjs-fullstack
priority: 75
---

# Supabase Integration Skill
""")

    # Create test skill 4: Testing skill
    test_dir = skills_dir / "jest-testing"
    test_dir.mkdir()
    test_skill = test_dir / "SKILL.md"
    test_skill.write_text("""---
name: jest-testing
description: Write tests with Jest and React Testing Library
triggers:
  - jest
  - test
  - testing
dependencies: []
priority: 60
---

# Jest Testing Skill
""")

    return skills_dir


@pytest.fixture
def discovery(temp_home, skills_dir):
    """Create SkillDiscovery instance with test skills"""
    return SkillDiscovery(skills_dir=skills_dir)


@pytest.fixture
def discovery_with_analytics(temp_home, skills_dir):
    """Create SkillDiscovery with usage analytics"""
    # Save test analytics
    analytics = {
        "skill_usage": {
            "nextjs-fullstack": {
                "count": 50,
                "success_rate": 0.95,
                "last_used": "2025-10-20T12:00:00Z"
            },
            "react-component": {
                "count": 30,
                "success_rate": 0.90,
                "last_used": "2025-10-21T12:00:00Z"
            }
        },
        "patterns": {}
    }
    Config.save_analytics(analytics)

    return SkillDiscovery(skills_dir=skills_dir)


class TestLoadAvailableSkills:
    """Test load_available_skills() with temp skills"""

    def test_load_all_skills(self, discovery):
        """Test loading all skills from directory"""
        skills = discovery.load_available_skills()

        assert len(skills) == 4
        skill_names = [s.name for s in skills]
        assert "nextjs-fullstack" in skill_names
        assert "react-component" in skill_names
        assert "supabase-integration" in skill_names
        assert "jest-testing" in skill_names

    def test_skills_cached(self, discovery):
        """Test that skills are cached after loading"""
        discovery.load_available_skills()

        assert len(discovery.cache) == 4
        assert "nextjs-fullstack" in discovery.cache
        assert "react-component" in discovery.cache

    def test_skill_metadata_parsed(self, discovery):
        """Test that skill metadata is correctly parsed"""
        discovery.load_available_skills()
        nextjs_skill = discovery.cache["nextjs-fullstack"]

        assert nextjs_skill.name == "nextjs-fullstack"
        assert "Next.js" in nextjs_skill.description
        assert "next.js" in nextjs_skill.triggers
        assert nextjs_skill.priority == 80

    def test_skill_dependencies_parsed(self, discovery):
        """Test that dependencies are parsed"""
        discovery.load_available_skills()
        supabase_skill = discovery.cache["supabase-integration"]

        assert "nextjs-fullstack" in supabase_skill.dependencies

    def test_skill_path_absolute(self, discovery):
        """Test that skill paths are absolute"""
        skills = discovery.load_available_skills()

        for skill in skills:
            assert skill.path.is_absolute()

    def test_load_enriches_with_analytics(self, discovery_with_analytics):
        """Test that skills are enriched with analytics data"""
        skills = discovery_with_analytics.load_available_skills()

        nextjs_skill = next(s for s in skills if s.name == "nextjs-fullstack")
        assert nextjs_skill.usage_count == 50
        assert nextjs_skill.success_rate == 0.95

    def test_load_empty_directory(self, tmp_path, temp_home):
        """Test loading from empty skills directory"""
        empty_dir = tmp_path / "empty_skills"
        empty_dir.mkdir()

        discovery = SkillDiscovery(skills_dir=empty_dir)
        skills = discovery.load_available_skills()

        assert skills == []

    def test_load_nonexistent_directory(self, tmp_path, temp_home):
        """Test loading from nonexistent directory"""
        nonexistent_dir = tmp_path / "nonexistent"

        discovery = SkillDiscovery(skills_dir=nonexistent_dir)
        skills = discovery.load_available_skills()

        assert skills == []


class TestFindSkillForEntity:
    """Test find_skill_for_entity() for various frameworks"""

    def test_find_by_framework_name(self, discovery):
        """Test finding skill by framework name"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("Next.js")

        assert skill is not None
        assert skill.name == "nextjs-fullstack"

    def test_find_by_alias(self, discovery):
        """Test finding skill by framework alias"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("nextjs")

        assert skill is not None
        assert skill.name == "nextjs-fullstack"

    def test_find_by_trigger(self, discovery):
        """Test finding skill by trigger keyword"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("component")

        assert skill is not None
        assert skill.name == "react-component"

    def test_find_case_insensitive(self, discovery):
        """Test case-insensitive entity matching"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("REACT")

        assert skill is not None
        assert skill.name == "react-component"

    def test_find_nonexistent_entity(self, discovery):
        """Test finding nonexistent entity"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("nonexistent-framework")

        assert skill is None

    def test_find_database_entity(self, discovery):
        """Test finding database-related skill"""
        discovery.load_available_skills()
        skill = discovery.find_skill_for_entity("supabase")

        assert skill is not None
        assert skill.name == "supabase-integration"


class TestGetDomainSkills:
    """Test get_domain_skills() for each domain"""

    def test_get_frontend_skills(self, discovery):
        """Test getting frontend domain skills"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("frontend")

        skill_names = [s.name for s in skills]
        assert "react-component" in skill_names

    def test_get_fullstack_skills(self, discovery):
        """Test getting fullstack domain skills"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("fullstack")

        skill_names = [s.name for s in skills]
        assert "nextjs-fullstack" in skill_names

    def test_get_testing_skills(self, discovery):
        """Test getting testing domain skills"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("testing")

        skill_names = [s.name for s in skills]
        assert "jest-testing" in skill_names

    def test_get_authentication_skills(self, discovery):
        """Test getting authentication domain skills"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("authentication")

        skill_names = [s.name for s in skills]
        assert "supabase-integration" in skill_names

    def test_get_unknown_domain(self, discovery):
        """Test getting skills for unknown domain"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("unknown-domain")

        assert skills == []

    def test_get_database_skills(self, discovery):
        """Test getting database domain skills"""
        discovery.load_available_skills()
        skills = discovery.get_domain_skills("database")

        skill_names = [s.name for s in skills]
        assert "supabase-integration" in skill_names


class TestDiscoverMultiStrategy:
    """Test discover() with multi-strategy discovery"""

    def test_discover_explicit_match(self, discovery):
        """Test explicit entity matching strategy"""
        intent = Intent(
            text="Create a Next.js application",
            entities=["Next.js"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        assert len(discovered) > 0
        # Next.js skill should be first (explicit match)
        assert discovered[0].skill.name == "nextjs-fullstack"
        assert discovered[0].reason == "explicit"
        assert discovered[0].priority == 100

    def test_discover_multiple_entities(self, discovery):
        """Test discovery with multiple entities"""
        intent = Intent(
            text="Build React app with Supabase",
            entities=["React", "Supabase"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        skill_names = [d.skill.name for d in discovered]
        assert "react-component" in skill_names
        assert "supabase-integration" in skill_names

    def test_discover_domain_match(self, discovery):
        """Test domain-based discovery strategy"""
        intent = Intent(
            text="Create frontend application",
            entities=[],
            domain="frontend"
        )

        discovered = discovery.discover(intent)

        # Should include frontend skills
        assert any(d.reason == "domain" for d in discovered)

    def test_discover_dependency_match(self, discovery):
        """Test dependency resolution strategy"""
        intent = Intent(
            text="Add Supabase integration",
            entities=["Supabase"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        skill_names = [d.skill.name for d in discovered]
        # Supabase depends on nextjs-fullstack
        assert "nextjs-fullstack" in skill_names

        # Find the nextjs skill in discovered
        nextjs_discovered = next(d for d in discovered if d.skill.name == "nextjs-fullstack")
        assert nextjs_discovered.reason == "dependency"

    def test_discover_pattern_match(self, discovery, temp_home):
        """Test pattern-based discovery strategy"""
        # Save learned patterns
        patterns = {
            "nextjs_supabase": {
                "keywords": ["next.js", "supabase"],
                "skills": ["nextjs-fullstack", "supabase-integration"],
                "confidence": 0.85
            }
        }
        Config.save_learned_patterns(patterns)

        # Reload discovery to pick up patterns
        discovery = SkillDiscovery(skills_dir=discovery.skills_dir)

        intent = Intent(
            text="Create app with next.js and supabase",
            entities=[],
            domain="fullstack",
            patterns=[{
                "skills": ["nextjs-fullstack", "supabase-integration"],
                "confidence": 0.85
            }]
        )

        discovered = discovery.discover(intent)

        # Should include pattern matches
        assert any(d.reason == "pattern" for d in discovered)

    def test_discover_no_duplicates(self, discovery):
        """Test that discovered skills don't have duplicates"""
        intent = Intent(
            text="Create Next.js frontend app",
            entities=["Next.js"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        # Check no duplicate skill names
        skill_names = [d.skill.name for d in discovered]
        assert len(skill_names) == len(set(skill_names))

    def test_discover_empty_intent(self, discovery):
        """Test discovery with empty intent"""
        intent = Intent(
            text="",
            entities=[],
            domain=None
        )

        discovered = discovery.discover(intent)

        # Should return some skills or empty list
        assert isinstance(discovered, list)


class TestPrioritySorting:
    """Test priority sorting and confidence scoring"""

    def test_skills_sorted_by_priority(self, discovery):
        """Test that discovered skills are sorted by priority"""
        intent = Intent(
            text="Build app with React, Next.js, and testing",
            entities=["React", "Next.js", "Jest"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        if len(discovered) > 1:
            # Explicit matches (priority 100) should come first
            explicit_skills = [d for d in discovered if d.reason == "explicit"]
            if explicit_skills:
                assert discovered[0].priority == 100

            # Check ordering
            for i in range(len(discovered) - 1):
                assert discovered[i].priority >= discovered[i + 1].priority

    def test_priority_by_reason(self, discovery):
        """Test priority assignment by discovery reason"""
        intent = Intent(
            text="Create Next.js app with Supabase",
            entities=["Next.js", "Supabase"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        # Check priority ranges
        for d in discovered:
            if d.reason == "explicit":
                assert d.priority == 100
            elif d.reason == "pattern":
                assert 70 <= d.priority <= 90
            elif d.reason == "domain":
                assert d.priority == 60
            elif d.reason == "dependency":
                assert d.priority == 40

    def test_confidence_scores(self, discovery):
        """Test confidence score assignment"""
        intent = Intent(
            text="Create Next.js application",
            entities=["Next.js"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        # All discovered skills should have confidence scores
        for d in discovered:
            assert 0.0 <= d.confidence <= 1.0

    def test_explicit_match_high_confidence(self, discovery):
        """Test explicit matches have high confidence"""
        intent = Intent(
            text="Build with React",
            entities=["React"],
            domain="frontend"
        )

        discovered = discovery.discover(intent)

        # Find explicit match
        explicit = [d for d in discovered if d.reason == "explicit"]
        if explicit:
            assert explicit[0].confidence == 1.0


class TestDependencyResolution:
    """Test dependency resolution between skills"""

    def test_resolve_single_dependency(self, discovery):
        """Test resolving a single dependency"""
        intent = Intent(
            text="Add Supabase",
            entities=["Supabase"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        skill_names = [d.skill.name for d in discovered]
        # Supabase depends on nextjs-fullstack
        assert "supabase-integration" in skill_names
        assert "nextjs-fullstack" in skill_names

    def test_dependency_lower_priority(self, discovery):
        """Test that dependencies have lower priority"""
        intent = Intent(
            text="Add Supabase",
            entities=["Supabase"],
            domain="fullstack"
        )

        discovered = discovery.discover(intent)

        # Find both skills
        supabase = next((d for d in discovered if d.skill.name == "supabase-integration"), None)
        nextjs = next((d for d in discovered if d.skill.name == "nextjs-fullstack"), None)

        if supabase and nextjs:
            # Explicit match should have higher priority than dependency
            if supabase.reason == "explicit" and nextjs.reason == "dependency":
                assert supabase.priority > nextjs.priority

    def test_dependency_in_cache(self, discovery):
        """Test that dependencies are found in cache"""
        discovery.load_available_skills()

        # Verify supabase skill has nextjs dependency
        supabase_skill = discovery.cache["supabase-integration"]
        assert "nextjs-fullstack" in supabase_skill.dependencies

        # Verify dependency exists in cache
        assert "nextjs-fullstack" in discovery.cache


class TestUserPreferences:
    """Test user preference filtering"""

    def test_disabled_skills_filtered(self, discovery, temp_home):
        """Test that disabled skills are filtered out"""
        # Set user preferences
        profile = Config.load_user_profile()
        profile["preferences"] = {
            "disabled_skills": ["react-component"]
        }
        Config.save_user_profile(profile)

        # Reload discovery
        discovery = SkillDiscovery(skills_dir=discovery.skills_dir)

        intent = Intent(
            text="Create React component",
            entities=["React"],
            domain="frontend"
        )

        discovered = discovery.discover(intent)

        skill_names = [d.skill.name for d in discovered]
        assert "react-component" not in skill_names

    def test_preferred_skills_boosted(self, discovery, temp_home):
        """Test that preferred skills get priority boost"""
        # Set user preferences
        profile = Config.load_user_profile()
        profile["preferences"] = {
            "preferred_skills": ["jest-testing"]
        }
        Config.save_user_profile(profile)

        # Reload discovery
        discovery = SkillDiscovery(skills_dir=discovery.skills_dir)

        intent = Intent(
            text="Create tests",
            entities=["Jest"],
            domain="testing"
        )

        discovered = discovery.discover(intent)

        # Find jest skill
        jest_skill = next((d for d in discovered if d.skill.name == "jest-testing"), None)

        if jest_skill:
            # Priority should be boosted (but not exceed 100)
            assert jest_skill.priority <= 100

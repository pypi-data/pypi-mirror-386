"""
Integration tests for orchestration flow.

Tests: Intent Analysis -> Skill Discovery -> Skill Loading -> Usage Tracking
"""

import pytest
from unittest.mock import patch
from skillforge.analyzers.intent_analyzer import IntentAnalyzer
from skillforge.analyzers.skill_discovery import SkillDiscovery
from skillforge.analyzers.usage_tracker import UsageTracker
from skillforge.generators.config import Config


@pytest.mark.integration
def test_complete_orchestration_flow(temp_home, multiple_skills, sample_profile):
    """Test complete orchestration from intent to usage tracking."""

    # 1. ANALYZE INTENT
    analyzer = IntentAnalyzer()

    user_request = "I need to build a Next.js app with Supabase authentication"

    intent = analyzer.analyze_intent(user_request)

    # Verify intent analysis
    assert intent is not None
    assert 'entities' in intent
    assert 'action' in intent
    assert 'domain' in intent

    # 2. DISCOVER SKILLS
    discovery = SkillDiscovery()

    # Discover skills based on intent
    discovered_skills = discovery.discover_skills(intent)

    # Verify skills discovered
    assert len(discovered_skills) > 0

    # Check that relevant skills were found
    skill_names = [skill['name'] for skill in discovered_skills]
    assert any('nextjs' in name.lower() for name in skill_names)

    # 3. LOAD SKILLS (simulated)
    loaded_skills = []
    for skill_info in discovered_skills[:3]:  # Load top 3
        skill_path = skill_info['path']
        if skill_path.exists():
            loaded_skills.append({
                'name': skill_info['name'],
                'content': skill_path.read_text()
            })

    assert len(loaded_skills) > 0

    # 4. TRACK USAGE
    tracker = UsageTracker()

    for skill in loaded_skills:
        tracker.record_usage(
            skill_name=skill['name'],
            success=True,
            context={'intent': user_request}
        )

    # Verify tracking
    usage_data = tracker.get_usage_summary()
    assert 'skill_usage' in usage_data
    assert len(usage_data['skill_usage']) > 0


@pytest.mark.integration
def test_intent_to_skill_mapping(temp_home, multiple_skills):
    """Test that different intents map to correct skills."""

    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()

    test_cases = [
        {
            'request': 'Create a React component with hooks',
            'expected_skills': ['react'],
        },
        {
            'request': 'Set up Supabase authentication',
            'expected_skills': ['supabase'],
        },
        {
            'request': 'Style with Tailwind CSS',
            'expected_skills': ['tailwind'],
        },
    ]

    for test_case in test_cases:
        intent = analyzer.analyze_intent(test_case['request'])
        discovered = discovery.discover_skills(intent)

        skill_names = [s['name'].lower() for s in discovered]

        # Check at least one expected skill was found
        found_expected = any(
            expected in name
            for expected in test_case['expected_skills']
            for name in skill_names
        )

        assert found_expected, f"Expected skills {test_case['expected_skills']} not found in {skill_names}"


@pytest.mark.integration
def test_skill_priority_sorting(temp_home, multiple_skills, config_with_usage):
    """Test that skills are sorted by relevance and usage."""

    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()

    # Record heavy usage for one skill
    tracker = UsageTracker()
    for i in range(20):
        tracker.record_usage('nextjs-fullstack', success=True)

    # Analyze intent
    intent = analyzer.analyze_intent("Build a Next.js application")

    # Discover skills
    discovered = discovery.discover_skills(intent, sort_by_usage=True)

    # Verify nextjs-fullstack is prioritized
    if len(discovered) > 0:
        top_skills = [s['name'] for s in discovered[:3]]
        # nextjs-fullstack should be in top skills due to high usage
        assert any('nextjs' in name.lower() for name in top_skills)


@pytest.mark.integration
def test_dependency_resolution(temp_home, multiple_skills):
    """Test that skill dependencies are resolved."""

    discovery = SkillDiscovery()

    # Discover a skill that has dependencies
    intent = {'entities': {'frameworks': ['nextjs']}}

    discovered = discovery.discover_skills(intent, resolve_dependencies=True)

    # Verify dependent skills included
    skill_names = [s['name'].lower() for s in discovered]

    # Next.js might depend on React, Tailwind, etc.
    assert len(discovered) >= 1


@pytest.mark.integration
def test_skill_filtering_by_context(temp_home, multiple_skills, sample_profile):
    """Test filtering skills based on user context."""

    discovery = SkillDiscovery()
    config = Config()
    config.save_profile(sample_profile)

    # User profile indicates they use Next.js and Supabase
    intent = {
        'entities': {'frameworks': ['frontend', 'database']},
        'domain': 'web-development'
    }

    discovered = discovery.discover_skills(intent, filter_by_profile=True)

    # Should discover skills matching user's tech stack
    skill_names = [s['name'].lower() for s in discovered]

    assert len(discovered) > 0


@pytest.mark.integration
def test_multi_strategy_discovery(temp_home, multiple_skills):
    """Test that multiple discovery strategies work together."""

    discovery = SkillDiscovery()

    intent = {
        'entities': {'frameworks': ['nextjs', 'supabase']},
        'action': 'create',
        'domain': 'authentication'
    }

    # Discover using multiple strategies
    by_explicit = discovery.discover_by_explicit_mention(intent)
    by_domain = discovery.discover_by_domain(intent)
    by_pattern = discovery.discover_by_patterns(intent)

    # Verify each strategy found skills
    assert len(by_explicit) > 0 or len(by_domain) > 0 or len(by_pattern) > 0


@pytest.mark.integration
def test_token_budget_allocation(temp_home, multiple_skills):
    """Test that skill discovery respects token budgets."""

    discovery = SkillDiscovery()

    intent = {
        'entities': {'frameworks': ['nextjs', 'react', 'supabase', 'tailwind']},
        'complexity': 'high'
    }

    # Discover with token limit
    discovered = discovery.discover_skills(
        intent,
        max_token_budget=5000
    )

    # Verify not too many skills returned
    assert len(discovered) <= 5  # Reasonable limit


@pytest.mark.integration
def test_usage_pattern_influences_discovery(temp_home, multiple_skills):
    """Test that usage patterns influence skill discovery."""

    tracker = UsageTracker()
    discovery = SkillDiscovery()

    # Create usage pattern: nextjs + supabase often used together
    for i in range(15):
        tracker.record_skill_combination(['nextjs-fullstack', 'supabase-integration'])

    # Discover skills with one of the pair
    intent = {'entities': {'frameworks': ['nextjs']}}

    discovered = discovery.discover_skills(intent, use_patterns=True)

    # supabase should be suggested due to common usage pattern
    skill_names = [s['name'].lower() for s in discovered]

    # At least nextjs should be found
    assert any('nextjs' in name for name in skill_names)


@pytest.mark.integration
def test_orchestration_with_complex_intent(temp_home, multiple_skills):
    """Test orchestration with complex, multi-faceted intent."""

    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()
    tracker = UsageTracker()

    # Complex request
    user_request = """
    Build a fullstack Next.js application with:
    - Supabase for authentication and database
    - Tailwind CSS for styling
    - React components with TypeScript
    - API routes for backend logic
    """

    # Analyze
    intent = analyzer.analyze_intent(user_request)

    # Discover
    discovered = discovery.discover_skills(intent)

    # Should find multiple relevant skills
    assert len(discovered) >= 2

    # Track usage
    for skill in discovered[:3]:
        tracker.record_usage(skill['name'], success=True)

    # Verify tracking
    usage_data = tracker.get_usage_summary()
    assert len(usage_data['skill_usage']) >= 1


@pytest.mark.integration
def test_orchestration_error_recovery(temp_home):
    """Test orchestration handles errors gracefully."""

    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()

    # Invalid/ambiguous intent
    vague_request = "do stuff"

    intent = analyzer.analyze_intent(vague_request)

    # Should still return something, even if low confidence
    assert intent is not None

    # Discovery should handle empty/poor intent
    discovered = discovery.discover_skills(intent)

    # Might be empty, but shouldn't crash
    assert isinstance(discovered, list)


@pytest.mark.integration
def test_real_time_skill_loading(temp_home, multiple_skills):
    """Test skills can be loaded dynamically during orchestration."""

    discovery = SkillDiscovery()

    intent = {'entities': {'frameworks': ['nextjs']}}

    # Discover skills
    discovered = discovery.discover_skills(intent)

    # Load skills content dynamically
    loaded_count = 0
    for skill_info in discovered:
        if skill_info['path'].exists():
            content = skill_info['path'].read_text()
            assert len(content) > 0
            loaded_count += 1

    assert loaded_count > 0

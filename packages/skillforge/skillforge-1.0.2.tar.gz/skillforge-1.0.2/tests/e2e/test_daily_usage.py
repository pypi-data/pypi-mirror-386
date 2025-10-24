"""
End-to-end tests for daily usage patterns.

Simulates typical day-to-day usage of SkillForge.
"""

import pytest
from unittest.mock import patch
from skillforge.analyzers.usage_tracker import UsageTracker
from skillforge.analyzers.pattern_detector import PatternDetector
from skillforge.analyzers.intent_analyzer import IntentAnalyzer
from skillforge.analyzers.skill_discovery import SkillDiscovery
from skillforge.generators.skill_generator import SkillGenerator


@pytest.mark.e2e
@pytest.mark.slow
def test_typical_day_usage(temp_home, multiple_skills, sample_profile):
    """
    Test typical daily usage:
    - Morning: Start new feature
    - Afternoon: Multiple skill uses
    - Evening: Review patterns
    """

    tracker = UsageTracker()
    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()

    # MORNING: Start building authentication feature
    morning_intent = analyzer.analyze_intent(
        "Build user authentication with Supabase"
    )

    morning_skills = discovery.discover_skills(morning_intent)

    for skill in morning_skills[:2]:
        tracker.record_usage(skill['name'], success=True,
                           context={'session': 'morning', 'task': 'auth'})

    # AFTERNOON: Build UI components
    afternoon_intent = analyzer.analyze_intent(
        "Create responsive UI with Tailwind CSS"
    )

    afternoon_skills = discovery.discover_skills(afternoon_intent)

    for skill in afternoon_skills[:2]:
        tracker.record_usage(skill['name'], success=True,
                           context={'session': 'afternoon', 'task': 'ui'})

    # EVENING: Database operations
    evening_intent = analyzer.analyze_intent(
        "Set up database schema in Supabase"
    )

    evening_skills = discovery.discover_skills(evening_intent)

    for skill in evening_skills[:1]:
        tracker.record_usage(skill['name'], success=True,
                           context={'session': 'evening', 'task': 'database'})

    # REVIEW: Check usage
    usage_summary = tracker.get_usage_summary()

    assert usage_summary['total_sessions'] >= 3
    assert len(usage_summary['skill_usage']) > 0


@pytest.mark.e2e
@pytest.mark.slow
def test_week_long_pattern_emergence(temp_home, multiple_skills):
    """
    Test pattern detection over a week of usage.
    """

    tracker = UsageTracker()
    detector = PatternDetector()

    # Week of consistent usage patterns
    for day in range(7):
        # Daily routine: Next.js + Supabase combo
        for i in range(3):
            tracker.record_usage('nextjs-fullstack', success=True,
                               context={'day': day, 'session': i})
            tracker.record_usage('supabase-integration', success=True,
                               context={'day': day, 'session': i})
            detector.record_combination(['nextjs-fullstack', 'supabase-integration'])

        # Style preference: Server components
        detector.record_style_preference('prefer-server-components', confidence=0.85)

    # Detect patterns at end of week
    patterns = detector.detect_patterns()

    # Should detect combination pattern
    assert 'combination' in patterns
    assert len(patterns['combination']) > 0

    # Should detect style pattern
    assert 'style' in patterns


@pytest.mark.e2e
@pytest.mark.slow
def test_context_switching_workflow(temp_home, multiple_skills):
    """
    Test switching between different types of work.
    """

    tracker = UsageTracker()

    # Feature development
    for i in range(5):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'work_type': 'feature'})
        tracker.record_usage('react-components', success=True,
                           context={'work_type': 'feature'})

    # Bug fixing
    for i in range(3):
        tracker.record_usage('api-design', success=True,
                           context={'work_type': 'bugfix'})

    # Code review
    for i in range(2):
        tracker.record_usage('tailwind-styling', success=True,
                           context={'work_type': 'review'})

    usage_summary = tracker.get_usage_summary()

    # All work types should be tracked
    assert len(usage_summary['skill_usage']) >= 3


@pytest.mark.e2e
@pytest.mark.slow
def test_collaborative_development_patterns(temp_home, multiple_skills):
    """
    Test patterns that emerge from team collaboration.
    """

    tracker = UsageTracker()
    detector = PatternDetector()

    # Team convention: Always use TypeScript
    for i in range(20):
        detector.record_style_preference('use-typescript', confidence=0.9)

    # Team workflow: Test-driven development
    for i in range(15):
        detector.record_workflow('write-tests-first')

    # Common skill combinations in team
    for i in range(18):
        detector.record_combination(['nextjs-fullstack', 'supabase-integration', 'tailwind-styling'])

    patterns = detector.detect_patterns()

    # Should detect team patterns
    assert patterns is not None
    assert len(patterns) > 0


@pytest.mark.e2e
@pytest.mark.slow
def test_error_recovery_workflow(temp_home, multiple_skills):
    """
    Test handling errors and retrying with different skills.
    """

    tracker = UsageTracker()

    # First attempt fails
    tracker.record_usage('api-design', success=False,
                       error='Connection timeout')

    # Retry with different approach
    tracker.record_usage('api-design', success=False,
                       error='Configuration error')

    # Finally succeeds
    tracker.record_usage('api-design', success=True)

    usage_data = tracker.get_usage_summary()

    skill_stats = usage_data['skill_usage']['api-design']
    assert skill_stats['failures'] == 2
    assert skill_stats['successes'] == 1
    assert skill_stats['total_uses'] == 3


@pytest.mark.e2e
@pytest.mark.slow
def test_multi_project_usage(temp_home, sample_profile):
    """
    Test using SkillForge across multiple projects.
    """

    tracker = UsageTracker()
    generator = SkillGenerator()

    # Project 1: E-commerce site
    for i in range(10):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'project': 'ecommerce'})
        tracker.record_usage('supabase-integration', success=True,
                           context={'project': 'ecommerce'})

    # Project 2: Blog
    for i in range(7):
        tracker.record_usage('react-components', success=True,
                           context={'project': 'blog'})
        tracker.record_usage('tailwind-styling', success=True,
                           context={'project': 'blog'})

    # Project 3: Dashboard
    for i in range(5):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'project': 'dashboard'})
        tracker.record_usage('api-design', success=True,
                           context={'project': 'dashboard'})

    usage_summary = tracker.get_usage_summary()

    # Should track usage across projects
    assert usage_summary['total_skill_loads'] >= 22


@pytest.mark.e2e
@pytest.mark.slow
def test_learning_from_daily_usage(temp_home, multiple_skills):
    """
    Test that daily usage leads to learning.
    """

    from skillforge.analyzers.learning_pipeline import LearningPipeline

    tracker = UsageTracker()
    detector = PatternDetector()
    pipeline = LearningPipeline()

    # Week 1: Build usage data
    for day in range(7):
        for i in range(5):
            tracker.record_usage('nextjs-fullstack', success=True)
            detector.record_style_preference('prefer-server-components',
                                            confidence=0.85)

    # Run learning cycle
    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True
        results = pipeline.run_learning_cycle(min_confidence=0.7)

    assert results is not None


@pytest.mark.e2e
@pytest.mark.slow
def test_progressive_skill_discovery(temp_home, sample_profile):
    """
    Test discovering new skills based on usage patterns.
    """

    analyzer = IntentAnalyzer()
    discovery = SkillDiscovery()
    tracker = UsageTracker()

    # Start with basic needs
    intent1 = analyzer.analyze_intent("Create a React component")
    skills1 = discovery.discover_skills(intent1)

    # Track usage
    for skill in skills1[:1]:
        tracker.record_usage(skill['name'], success=True)

    # Evolve to more complex needs
    intent2 = analyzer.analyze_intent(
        "Create a Next.js server component with Supabase"
    )
    skills2 = discovery.discover_skills(intent2)

    # Should discover more advanced skills
    assert len(skills2) >= len(skills1)


@pytest.mark.e2e
@pytest.mark.slow
def test_weekend_project_workflow(temp_home, multiple_skills, sample_profile):
    """
    Test intensive weekend project workflow.
    """

    tracker = UsageTracker()

    # Intensive weekend coding session
    skill_sequence = [
        'nextjs-fullstack',
        'supabase-integration',
        'tailwind-styling',
        'nextjs-fullstack',
        'react-components',
        'api-design',
        'supabase-integration',
        'tailwind-styling',
    ]

    for i, skill_name in enumerate(skill_sequence):
        tracker.record_usage(
            skill_name,
            success=True,
            context={'session': 'weekend', 'order': i}
        )

    usage_summary = tracker.get_usage_summary()

    # Should track sequential usage
    assert usage_summary['total_skill_loads'] == len(skill_sequence)


@pytest.mark.e2e
@pytest.mark.slow
def test_skill_usage_trends(temp_home, multiple_skills):
    """
    Test identifying usage trends over time.
    """

    tracker = UsageTracker()

    # Week 1: Primarily Next.js
    for i in range(20):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'week': 1})

    # Week 2: Add Supabase
    for i in range(15):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'week': 2})
    for i in range(15):
        tracker.record_usage('supabase-integration', success=True,
                           context={'week': 2})

    # Week 3: Diversify
    for i in range(10):
        tracker.record_usage('nextjs-fullstack', success=True,
                           context={'week': 3})
    for i in range(10):
        tracker.record_usage('supabase-integration', success=True,
                           context={'week': 3})
    for i in range(10):
        tracker.record_usage('tailwind-styling', success=True,
                           context={'week': 3})

    usage_summary = tracker.get_usage_summary()

    # Trends should be visible in usage data
    assert len(usage_summary['skill_usage']) >= 3

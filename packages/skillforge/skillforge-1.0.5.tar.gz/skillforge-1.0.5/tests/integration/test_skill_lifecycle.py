"""
Integration tests for complete skill lifecycle.

Tests: Generate -> Use -> Track -> Learn -> Update cycle.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from skillforge.generators.skill_generator import SkillGenerator
from skillforge.generators.config import Config
from skillforge.analyzers.usage_tracker import UsageTracker
from skillforge.analyzers.pattern_detector import PatternDetector
from skillforge.analyzers.learning_pipeline import LearningPipeline
from skillforge.analyzers.skill_optimizer import SkillOptimizer


@pytest.mark.integration
def test_complete_skill_lifecycle(temp_home, sample_profile):
    """Test complete lifecycle: generate -> use -> track -> learn -> optimize."""

    # 1. GENERATE SKILL
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Next.js docs',
            'code_snippets': [{'title': 'Example', 'code': 'const x = 1'}],
            'best_practices': ['Use Server Components'],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-fullstack'
        )

    assert skill_path.exists()

    # 2. USE SKILL (simulate usage)
    tracker = UsageTracker()

    # Simulate multiple uses
    for i in range(10):
        tracker.record_usage(
            skill_name='nextjs-fullstack',
            success=True,
            context={'task': f'build_feature_{i}'}
        )

    # Record some related skill usage
    for i in range(8):
        tracker.record_usage(
            skill_name='supabase-integration',
            success=True,
            context={'task': f'database_task_{i}'}
        )

    # 3. TRACK USAGE
    usage_data = tracker.get_usage_summary()

    assert 'nextjs-fullstack' in usage_data['skill_usage']
    assert usage_data['skill_usage']['nextjs-fullstack']['total_uses'] == 10
    assert usage_data['skill_usage']['nextjs-fullstack']['successes'] == 10

    # 4. DETECT PATTERNS
    detector = PatternDetector()

    # Record skill combinations
    for i in range(8):
        detector.record_combination(['nextjs-fullstack', 'supabase-integration'])

    patterns = detector.detect_patterns()

    # Verify combination pattern detected
    assert 'combination' in patterns
    combination_patterns = [p for p in patterns['combination']
                          if 'nextjs-fullstack' in p['pattern'] and
                             'supabase-integration' in p['pattern']]
    assert len(combination_patterns) > 0

    # 5. APPLY PATTERNS (Learning)
    pipeline = LearningPipeline()

    # Run learning cycle
    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True

        results = pipeline.run_learning_cycle(
            min_confidence=0.7,
            dry_run=False
        )

    # Verify learning results
    assert 'patterns_detected' in results
    assert 'patterns_applied' in results

    # 6. OPTIMIZE SKILLS
    optimizer = SkillOptimizer()

    analysis = optimizer.analyze_all_skills()

    # Verify optimization analysis
    assert 'skills_analyzed' in analysis
    assert 'total_skills' in analysis


@pytest.mark.integration
def test_usage_tracking_persistence(temp_home):
    """Test that usage tracking persists across sessions."""
    tracker1 = UsageTracker()

    # Record usage in first session
    tracker1.record_usage('test-skill', success=True)
    tracker1.record_usage('test-skill', success=True)
    tracker1.record_usage('test-skill', success=False)

    # Create new tracker instance (simulating new session)
    tracker2 = UsageTracker()

    # Load usage data
    usage_data = tracker2.get_usage_summary()

    # Verify data persisted
    assert 'test-skill' in usage_data['skill_usage']
    assert usage_data['skill_usage']['test-skill']['total_uses'] == 3
    assert usage_data['skill_usage']['test-skill']['successes'] == 2
    assert usage_data['skill_usage']['test-skill']['failures'] == 1


@pytest.mark.integration
def test_pattern_detection_over_time(temp_home):
    """Test pattern detection as usage accumulates."""
    detector = PatternDetector()

    # Day 1: Few uses, no pattern
    for i in range(3):
        detector.record_combination(['skill-a', 'skill-b'])

    patterns_day1 = detector.detect_patterns()

    # Day 2: More uses, pattern emerges
    for i in range(7):
        detector.record_combination(['skill-a', 'skill-b'])

    patterns_day2 = detector.detect_patterns()

    # Verify pattern confidence increases with more data
    if patterns_day1.get('combination'):
        pattern1_confidence = patterns_day1['combination'][0]['confidence']
        pattern2_confidence = patterns_day2['combination'][0]['confidence']
        assert pattern2_confidence >= pattern1_confidence


@pytest.mark.integration
def test_learning_pipeline_with_real_patterns(temp_home, sample_profile):
    """Test learning pipeline applies real detected patterns."""

    # 1. Generate initial skill
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='react',
            skill_name='react-components'
        )

    original_content = skill_path.read_text()

    # 2. Simulate usage that creates pattern
    tracker = UsageTracker()
    for i in range(15):
        tracker.record_usage('react-components', success=True,
                           context={'pattern': 'functional-components'})

    # 3. Detect patterns
    detector = PatternDetector()
    detector.record_style_preference('functional-components', confidence=0.85)

    # 4. Run learning pipeline
    pipeline = LearningPipeline()

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True

        results = pipeline.run_learning_cycle(min_confidence=0.8)

    # Verify pipeline ran successfully
    assert results is not None
    assert isinstance(results, dict)


@pytest.mark.integration
def test_skill_optimization_after_usage(temp_home, multiple_skills):
    """Test skill optimization identifies issues after usage."""

    # Simulate usage for different skills
    tracker = UsageTracker()

    # Heavily used skill
    for i in range(50):
        tracker.record_usage('nextjs-fullstack', success=True)

    # Rarely used skill
    for i in range(2):
        tracker.record_usage('api-design', success=True)

    # Run optimization
    optimizer = SkillOptimizer()
    analysis = optimizer.analyze_all_skills()

    # Verify analysis includes usage-based insights
    assert analysis is not None
    assert 'skills_analyzed' in analysis


@pytest.mark.integration
def test_skill_update_workflow(temp_home, sample_profile):
    """Test workflow for updating an existing skill."""

    # 1. Generate initial version
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Version 1.0 docs',
            'code_snippets': [],
            'best_practices': ['Old practice'],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-test'
        )

    v1_content = skill_path.read_text()
    assert 'Version 1.0' in v1_content or 'Old practice' in v1_content

    # 2. Update with new documentation
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Version 2.0 docs',
            'code_snippets': [],
            'best_practices': ['New practice'],
        }

        updated_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-test',
            force_overwrite=True
        )

    v2_content = updated_path.read_text()

    # Verify content was updated
    assert v2_content != v1_content


@pytest.mark.integration
def test_multi_skill_collaboration(temp_home, sample_profile):
    """Test that multiple skills work together in a workflow."""

    # Generate related skills
    generator = SkillGenerator()
    skills = ['nextjs', 'supabase', 'tailwind']

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        generated_skills = []
        for skill_type in skills:
            skill_path = generator.generate_skill(
                profile=sample_profile,
                skill_type=skill_type,
                skill_name=f'{skill_type}-skill'
            )
            generated_skills.append(skill_path)

    # Track combined usage
    tracker = UsageTracker()

    # Simulate using skills together
    for i in range(10):
        tracker.record_skill_combination(
            ['nextjs-skill', 'supabase-skill', 'tailwind-skill']
        )

    # Verify combination tracking
    usage_data = tracker.get_usage_summary()
    assert 'skill_combinations' in usage_data or len(usage_data['skill_usage']) >= 3


@pytest.mark.integration
def test_skill_rollback_after_bad_update(temp_home, sample_profile):
    """Test rolling back a skill after a problematic update."""

    # Generate initial skill
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Good docs',
            'code_snippets': [],
            'best_practices': ['Good practice'],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='react',
            skill_name='react-test'
        )

    original_content = skill_path.read_text()

    # Apply learning that might cause issues
    pipeline = LearningPipeline()

    # Create backup
    backup_path = pipeline._create_backup(skill_path)
    assert backup_path.exists()

    # Simulate bad update
    skill_path.write_text("Bad content")

    # Rollback
    pipeline._restore_backup(skill_path, backup_path)

    # Verify rollback worked
    restored_content = skill_path.read_text()
    assert restored_content == original_content


@pytest.mark.integration
def test_concurrent_skill_usage(temp_home):
    """Test tracking when multiple skills are used concurrently."""
    tracker = UsageTracker()

    # Simulate concurrent usage
    skills_in_use = ['skill-a', 'skill-b', 'skill-c']

    for skill in skills_in_use:
        tracker.record_usage(skill, success=True, context={'concurrent': True})

    # Verify all recorded
    usage_data = tracker.get_usage_summary()

    for skill in skills_in_use:
        assert skill in usage_data['skill_usage']
        assert usage_data['skill_usage'][skill]['total_uses'] >= 1

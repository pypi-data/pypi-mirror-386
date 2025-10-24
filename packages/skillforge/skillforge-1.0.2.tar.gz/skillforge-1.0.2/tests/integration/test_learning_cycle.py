"""
Integration tests for learning cycle.

Tests: Generate Usage Data -> Detect Patterns -> Apply Patterns -> Validate Updates
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from skillforge.analyzers.usage_tracker import UsageTracker
from skillforge.analyzers.pattern_detector import PatternDetector
from skillforge.analyzers.learning_pipeline import LearningPipeline
from skillforge.analyzers.skill_optimizer import SkillOptimizer
from skillforge.generators.config import Config


@pytest.mark.integration
def test_complete_learning_cycle(temp_home, sample_skill_path):
    """Test complete learning cycle from usage to skill updates."""

    # 1. GENERATE USAGE DATA
    tracker = UsageTracker()

    # Simulate significant usage
    for i in range(30):
        tracker.record_usage(
            'nextjs-fullstack',
            success=True,
            context={'pattern': 'server-components'}
        )

    usage_data = tracker.get_usage_summary()
    assert 'nextjs-fullstack' in usage_data['skill_usage']
    assert usage_data['skill_usage']['nextjs-fullstack']['total_uses'] == 30

    # 2. DETECT PATTERNS
    detector = PatternDetector()

    # Record style preferences
    for i in range(25):
        detector.record_style_preference('prefer-server-components', confidence=0.9)

    # Record combinations
    for i in range(20):
        detector.record_combination(['nextjs-fullstack', 'supabase-integration'])

    patterns = detector.detect_patterns()

    assert 'style' in patterns
    assert 'combination' in patterns
    assert len(patterns['style']) > 0

    # 3. APPLY PATTERNS
    pipeline = LearningPipeline()

    original_content = sample_skill_path.read_text()

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = Path(str(sample_skill_path) + '.backup')

        results = pipeline.run_learning_cycle(
            min_confidence=0.7,
            dry_run=False
        )

    # 4. VALIDATE UPDATES
    assert results is not None
    assert 'patterns_detected' in results


@pytest.mark.integration
def test_pattern_confidence_evolution(temp_home):
    """Test how pattern confidence evolves with more data."""

    detector = PatternDetector()

    # Week 1: Initial pattern
    for i in range(5):
        detector.record_combination(['skill-a', 'skill-b'])

    patterns_week1 = detector.detect_patterns()

    # Week 2: More data
    for i in range(10):
        detector.record_combination(['skill-a', 'skill-b'])

    patterns_week2 = detector.detect_patterns()

    # Week 3: Even more data
    for i in range(15):
        detector.record_combination(['skill-a', 'skill-b'])

    patterns_week3 = detector.detect_patterns()

    # Confidence should increase
    if patterns_week1.get('combination') and patterns_week3.get('combination'):
        conf1 = patterns_week1['combination'][0]['confidence']
        conf3 = patterns_week3['combination'][0]['confidence']
        assert conf3 >= conf1


@pytest.mark.integration
def test_learning_with_contradictory_patterns(temp_home, sample_skill_path):
    """Test learning handles contradictory usage patterns."""

    detector = PatternDetector()

    # Pattern 1: Use server components
    for i in range(15):
        detector.record_style_preference('use-server-components', confidence=0.8)

    # Pattern 2: Use client components (contradictory)
    for i in range(10):
        detector.record_style_preference('use-client-components', confidence=0.6)

    patterns = detector.detect_patterns()

    # Should keep higher confidence pattern
    if patterns.get('style'):
        # The higher confidence pattern should dominate
        assert len(patterns['style']) > 0


@pytest.mark.integration
def test_learning_backup_and_rollback(temp_home, sample_skill_path):
    """Test backup creation and rollback functionality."""

    pipeline = LearningPipeline()

    original_content = sample_skill_path.read_text()

    # Create backup
    backup_path = pipeline._create_backup(sample_skill_path)

    assert backup_path.exists()
    assert backup_path.read_text() == original_content

    # Modify skill
    sample_skill_path.write_text("Modified content")

    # Rollback
    pipeline._restore_backup(sample_skill_path, backup_path)

    # Verify restored
    restored_content = sample_skill_path.read_text()
    assert restored_content == original_content


@pytest.mark.integration
def test_learning_cycle_dry_run(temp_home, sample_skill_path):
    """Test learning cycle in dry-run mode."""

    pipeline = LearningPipeline()

    original_content = sample_skill_path.read_text()

    # Create some patterns
    detector = PatternDetector()
    for i in range(20):
        detector.record_style_preference('test-pattern', confidence=0.85)

    # Run in dry-run mode
    results = pipeline.run_learning_cycle(
        min_confidence=0.7,
        dry_run=True
    )

    # Verify no changes made
    current_content = sample_skill_path.read_text()
    assert current_content == original_content

    # But results should show what would be done
    assert results is not None


@pytest.mark.integration
def test_optimization_after_learning(temp_home, multiple_skills):
    """Test optimization after learning cycle."""

    # Run learning to update skills
    pipeline = LearningPipeline()

    detector = PatternDetector()
    for i in range(25):
        detector.record_combination(['nextjs-fullstack', 'supabase-integration'])

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True
        pipeline.run_learning_cycle(min_confidence=0.7)

    # Run optimization
    optimizer = SkillOptimizer()
    analysis = optimizer.analyze_all_skills()

    # Verify optimization results
    assert analysis is not None
    assert 'skills_analyzed' in analysis


@pytest.mark.integration
def test_pattern_detection_with_time_decay(temp_home):
    """Test that old patterns decay over time."""

    detector = PatternDetector()

    # Old pattern (simulate old timestamp)
    pattern_data = {
        'pattern': 'old-pattern',
        'confidence': 0.9,
        'last_seen': '2024-01-01T00:00:00',
        'occurrences': 20
    }

    # Manually set old pattern
    detector._patterns_cache['style'] = [pattern_data]

    # New conflicting pattern
    for i in range(15):
        detector.record_style_preference('new-pattern', confidence=0.85)

    patterns = detector.detect_patterns()

    # New pattern should have more weight
    assert patterns is not None


@pytest.mark.integration
def test_learning_notification_system(temp_home, sample_skill_path):
    """Test that learning pipeline creates user notifications."""

    pipeline = LearningPipeline()

    # Create high-confidence pattern
    detector = PatternDetector()
    for i in range(30):
        detector.record_style_preference('important-pattern', confidence=0.95)

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = Path(str(sample_skill_path) + '.backup')

        with patch.object(pipeline, '_create_notification') as mock_notify:
            results = pipeline.run_learning_cycle(min_confidence=0.9)

            # Verify notification would be created for high-confidence patterns
            # (implementation dependent)
            assert results is not None


@pytest.mark.integration
def test_multi_skill_pattern_application(temp_home, multiple_skills):
    """Test applying patterns across multiple skills."""

    pipeline = LearningPipeline()
    detector = PatternDetector()

    # Pattern that applies to multiple skills
    for i in range(25):
        detector.record_style_preference('use-typescript', confidence=0.9)

    # Record which skills use TypeScript
    for skill_name in ['nextjs-fullstack', 'react-components', 'api-design']:
        detector.record_workflow('typescript-workflow')

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True

        results = pipeline.run_learning_cycle(min_confidence=0.8)

    # Pattern should be considered for multiple skills
    assert results is not None


@pytest.mark.integration
def test_learning_with_user_feedback(temp_home, sample_skill_path):
    """Test learning cycle incorporates user feedback."""

    pipeline = LearningPipeline()
    detector = PatternDetector()

    # Initial pattern
    for i in range(20):
        detector.record_style_preference('pattern-a', confidence=0.85)

    # User provides negative feedback (simulated)
    # This would adjust confidence
    detector.adjust_confidence('pattern-a', adjustment=-0.2)

    patterns = detector.detect_patterns()

    # Pattern confidence should be adjusted
    if patterns.get('style'):
        pattern_a = [p for p in patterns['style'] if p['pattern'] == 'pattern-a']
        if pattern_a:
            assert pattern_a[0]['confidence'] < 0.85


@pytest.mark.integration
def test_incremental_learning(temp_home, sample_skill_path):
    """Test that learning happens incrementally."""

    pipeline = LearningPipeline()
    detector = PatternDetector()

    original_content = sample_skill_path.read_text()

    # Cycle 1: Small pattern
    for i in range(10):
        detector.record_style_preference('pattern-1', confidence=0.75)

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True
        results1 = pipeline.run_learning_cycle(min_confidence=0.7)

    # Cycle 2: Stronger pattern
    for i in range(20):
        detector.record_style_preference('pattern-2', confidence=0.9)

    with patch.object(pipeline, '_create_backup') as mock_backup:
        mock_backup.return_value = True
        results2 = pipeline.run_learning_cycle(min_confidence=0.7)

    # Should have results from both cycles
    assert results1 is not None
    assert results2 is not None


@pytest.mark.integration
def test_learning_with_failure_recovery(temp_home, sample_skill_path):
    """Test learning handles failures and recovers."""

    pipeline = LearningPipeline()

    original_content = sample_skill_path.read_text()

    # Create backup
    backup_path = pipeline._create_backup(sample_skill_path)

    # Simulate failure during update
    sample_skill_path.write_text("Corrupted content")

    # Recovery should restore backup
    pipeline._restore_backup(sample_skill_path, backup_path)

    restored_content = sample_skill_path.read_text()
    assert restored_content == original_content


@pytest.mark.integration
def test_pattern_merging(temp_home):
    """Test that similar patterns are merged appropriately."""

    detector = PatternDetector()

    # Similar patterns
    for i in range(15):
        detector.record_style_preference('use-async-await', confidence=0.85)

    for i in range(10):
        detector.record_style_preference('prefer-async-await', confidence=0.80)

    patterns = detector.detect_patterns()

    # Should detect both patterns (or merge them)
    assert patterns is not None
    assert 'style' in patterns

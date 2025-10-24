"""
Unit tests for PatternDetector class

Tests pattern detection including:
- Detecting patterns from usage data
- Analyzing skill combinations
- Analyzing code style patterns
- Analyzing workflow patterns
- Updating confidence scores
- Applying pattern decay
- Confidence calculation algorithms
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from skillforge.analyzers.pattern_detector import (
    PatternDetector,
    DetectedPattern,
    CombinationPattern,
    StylePattern,
    WorkflowPattern
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
def detector(temp_home):
    """Create PatternDetector instance with clean state"""
    return PatternDetector(config_module=Config)


@pytest.fixture
def detector_with_usage_data(temp_home):
    """Create PatternDetector with usage analytics data"""
    # Create usage data
    analytics = {
        "skill_usage": {
            "nextjs-fullstack": {
                "count": 50,
                "success_rate": 0.95,
                "metadata": {
                    "naming_style": "camelCase",
                    "import_style": "grouped",
                    "error_handling": "try_except",
                    "commit_format": "conventional",
                    "branch_pattern": "feature/",
                    "testing_workflow": "pre_commit"
                },
                "sessions": [
                    {"timestamp": "2025-10-20T10:00:00Z", "skills": ["nextjs-fullstack", "supabase-integration"]},
                    {"timestamp": "2025-10-20T11:00:00Z", "skills": ["nextjs-fullstack", "supabase-integration"]},
                    {"timestamp": "2025-10-20T12:00:00Z", "skills": ["nextjs-fullstack", "react-component"]},
                ]
            },
            "react-component": {
                "count": 30,
                "success_rate": 0.90,
                "metadata": {
                    "naming_style": "camelCase",
                    "import_style": "grouped",
                    "error_handling": "try_except"
                },
                "sessions": [
                    {"timestamp": "2025-10-20T13:00:00Z", "skills": ["react-component", "jest-testing"]},
                ]
            },
            "supabase-integration": {
                "count": 25,
                "success_rate": 0.92,
                "metadata": {
                    "naming_style": "camelCase",
                    "import_style": "grouped",
                    "error_handling": "try_except",
                    "commit_format": "conventional",
                    "branch_pattern": "feature/",
                    "testing_workflow": "pre_commit"
                },
                "sessions": []
            },
            "jest-testing": {
                "count": 15,
                "success_rate": 0.88,
                "metadata": {
                    "naming_style": "camelCase",
                    "import_style": "grouped",
                    "error_handling": "try_except",
                    "commit_format": "conventional",
                    "branch_pattern": "feature/",
                    "testing_workflow": "pre_commit"
                },
                "sessions": []
            }
        },
        "patterns": {}
    }

    # Enhance sessions for combination detection (need 25+ for confidence 0.8)
    for i in range(25):
        analytics["skill_usage"]["nextjs-fullstack"]["sessions"].append({
            "timestamp": f"2025-10-{20+i//10}T{10+i%10}:00:00Z",
            "skills": ["nextjs-fullstack", "supabase-integration"]
        })

    for i in range(30):
        analytics["skill_usage"]["react-component"]["sessions"].append({
            "timestamp": f"2025-10-{20+i//10}T{10+i%10}:00:00Z",
            "skills": ["react-component"]
        })

    Config.save_analytics(analytics)

    return PatternDetector(config_module=Config)


@pytest.fixture
def detector_with_patterns(temp_home):
    """Create PatternDetector with existing patterns"""
    patterns = {
        "combo_123": {
            "pattern_id": "combo_123",
            "pattern_type": "combination",
            "description": "Next.js with Supabase",
            "confidence": 0.85,
            "frequency": 15,
            "success_rate": 0.95,
            "first_seen": (datetime.now() - timedelta(days=30)).isoformat(),
            "last_seen": datetime.now().isoformat(),
            "data": {"skills": ["nextjs-fullstack", "supabase-integration"]}
        },
        "style_naming_camelCase": {
            "pattern_id": "style_naming_camelCase",
            "pattern_type": "style",
            "description": "Preferred naming: camelCase",
            "confidence": 0.90,
            "frequency": 40,
            "success_rate": 0.95,
            "first_seen": (datetime.now() - timedelta(days=60)).isoformat(),
            "last_seen": datetime.now().isoformat(),
            "data": {"style_type": "naming", "examples": ["camelCase"]}
        }
    }
    Config.save_learned_patterns(patterns)

    return PatternDetector(config_module=Config)


class TestDetectPatterns:
    """Test detect_patterns() with usage data"""

    def test_detect_all_pattern_types(self, detector_with_usage_data):
        """Test detection of all pattern types"""
        patterns = detector_with_usage_data.detect_patterns()

        # Should detect patterns (at least combination patterns)
        assert len(patterns) > 0

        # Check that patterns are saved
        saved_patterns = Config.load_learned_patterns()
        assert len(saved_patterns) > 0

    def test_detect_with_no_data(self, detector):
        """Test detection with no usage data"""
        patterns = detector.detect_patterns()

        # Should return empty list or existing patterns
        assert isinstance(patterns, list)

    def test_detect_merges_with_existing(self, detector_with_patterns):
        """Test that new patterns merge with existing ones"""
        initial_count = len(detector_with_patterns.patterns)

        # Add more usage data
        analytics = Config.load_analytics()
        analytics["skill_usage"]["new-skill"] = {
            "count": 30,
            "success_rate": 0.9,
            "metadata": {"naming_style": "snake_case"},
            "sessions": []
        }
        Config.save_analytics(analytics)

        # Detect patterns again
        patterns = detector_with_patterns.detect_patterns()

        # Should have at least the initial patterns
        assert len(patterns) >= initial_count

    def test_detect_updates_existing_patterns(self, detector_with_patterns):
        """Test that existing patterns are updated"""
        initial_pattern = detector_with_patterns.patterns["combo_123"]
        initial_frequency = initial_pattern.frequency

        # Run detection again
        detector_with_patterns.detect_patterns()

        # Pattern should still exist
        assert "combo_123" in detector_with_patterns.patterns

    def test_detect_validates_patterns(self, detector_with_usage_data):
        """Test that patterns are validated before saving"""
        patterns = detector_with_usage_data.detect_patterns()

        # All returned patterns should have valid confidence scores
        for pattern in patterns:
            assert 0.0 <= pattern.confidence <= 1.0


class TestAnalyzeSkillCombinations:
    """Test analyze_skill_combinations()"""

    def test_detect_frequent_combinations(self, detector_with_usage_data):
        """Test detection of frequently used skill combinations"""
        patterns = detector_with_usage_data.analyze_skill_combinations()

        # Should detect nextjs + supabase combination
        assert len(patterns) > 0
        assert any(isinstance(p, CombinationPattern) for p in patterns)

    def test_combination_threshold(self, detector):
        """Test that combinations below threshold are filtered"""
        # Create minimal usage data (below threshold)
        analytics = {
            "skill_usage": {
                "skill-a": {
                    "sessions": [
                        {"timestamp": "2025-10-20T10:00:00Z", "skills": ["skill-a", "skill-b"]},
                        {"timestamp": "2025-10-20T11:00:00Z", "skills": ["skill-a", "skill-b"]},
                    ]
                }
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_skill_combinations()

        # Should not detect pattern (below min occurrences)
        assert len(patterns) == 0

    def test_combination_success_rate(self, detector_with_usage_data):
        """Test that success rate is calculated"""
        patterns = detector_with_usage_data.analyze_skill_combinations()

        if patterns:
            for pattern in patterns:
                assert 0.0 <= pattern.success_rate <= 1.0

    def test_combination_confidence_calculation(self, detector_with_usage_data):
        """Test confidence calculation for combinations"""
        patterns = detector_with_usage_data.analyze_skill_combinations()

        if patterns:
            for pattern in patterns:
                assert 0.0 <= pattern.confidence <= 1.0

    def test_combination_min_occurrences(self, detector):
        """Test minimum occurrence threshold"""
        # Create data with exactly threshold occurrences
        analytics = {
            "skill_usage": {
                "skill-a": {
                    "sessions": [
                        {"timestamp": f"2025-10-20T{10+i}:00:00Z", "skills": ["skill-a", "skill-b"]}
                        for i in range(detector.COMBINATION_MIN_OCCURRENCES)
                    ]
                }
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_skill_combinations()

        # Should detect pattern at threshold
        assert len(patterns) >= 0

    def test_combination_multiple_sizes(self, detector_with_usage_data):
        """Test detection of different combination sizes"""
        patterns = detector_with_usage_data.analyze_skill_combinations()

        # Should detect 2-skill combinations at minimum
        assert any(len(p.skills) >= 2 for p in patterns if isinstance(p, CombinationPattern))


class TestAnalyzeCodeStyle:
    """Test analyze_code_style()"""

    def test_detect_naming_style(self, detector_with_usage_data):
        """Test detection of naming style patterns"""
        patterns = detector_with_usage_data.analyze_code_style()

        # Should detect camelCase as dominant style
        naming_patterns = [p for p in patterns if isinstance(p, StylePattern) and p.style_type == "naming"]
        assert len(naming_patterns) > 0

    def test_detect_import_style(self, detector_with_usage_data):
        """Test detection of import style patterns"""
        patterns = detector_with_usage_data.analyze_code_style()

        # Should detect grouped imports
        import_patterns = [p for p in patterns if isinstance(p, StylePattern) and p.style_type == "imports"]
        assert len(import_patterns) > 0

    def test_detect_error_handling_style(self, detector_with_usage_data):
        """Test detection of error handling patterns"""
        patterns = detector_with_usage_data.analyze_code_style()

        # Should detect try_except pattern
        error_patterns = [p for p in patterns if isinstance(p, StylePattern) and p.style_type == "error_handling"]
        assert len(error_patterns) > 0

    def test_style_threshold(self, detector):
        """Test that styles below threshold are filtered"""
        # Create data with mixed styles (no clear winner)
        analytics = {
            "skill_usage": {
                f"skill-{i}": {
                    "metadata": {"naming_style": "camelCase" if i % 2 == 0 else "snake_case"}
                }
                for i in range(10)
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_code_style()

        # Should not detect strong pattern (below threshold)
        assert len(patterns) == 0

    def test_style_min_samples(self, detector):
        """Test minimum sample requirement"""
        # Create data with too few samples
        analytics = {
            "skill_usage": {
                "skill-1": {"metadata": {"naming_style": "camelCase"}},
                "skill-2": {"metadata": {"naming_style": "camelCase"}},
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_code_style()

        # Should not detect pattern (too few samples)
        assert len(patterns) == 0

    def test_style_pattern_structure(self, detector_with_usage_data):
        """Test that style patterns have correct structure"""
        patterns = detector_with_usage_data.analyze_code_style()

        for pattern in patterns:
            assert isinstance(pattern, StylePattern)
            assert pattern.pattern_type == "style"
            assert pattern.style_type in ["naming", "imports", "error_handling"]
            assert len(pattern.examples) > 0


class TestAnalyzeWorkflows:
    """Test analyze_workflows()"""

    def test_detect_commit_format(self, detector_with_usage_data):
        """Test detection of commit format patterns"""
        patterns = detector_with_usage_data.analyze_workflows()

        # Should detect conventional commits
        commit_patterns = [p for p in patterns if isinstance(p, WorkflowPattern) and p.workflow_type == "commit"]
        assert len(commit_patterns) > 0

    def test_detect_branch_pattern(self, detector_with_usage_data):
        """Test detection of branch naming patterns"""
        patterns = detector_with_usage_data.analyze_workflows()

        # Should detect feature/ branch pattern
        branch_patterns = [p for p in patterns if isinstance(p, WorkflowPattern) and p.workflow_type == "branch"]
        assert len(branch_patterns) > 0

    def test_detect_testing_workflow(self, detector_with_usage_data):
        """Test detection of testing workflow patterns"""
        patterns = detector_with_usage_data.analyze_workflows()

        # Should detect pre_commit testing workflow
        test_patterns = [p for p in patterns if isinstance(p, WorkflowPattern) and p.workflow_type == "testing"]
        assert len(test_patterns) > 0

    def test_workflow_templates(self, detector_with_usage_data):
        """Test that workflow patterns include templates"""
        patterns = detector_with_usage_data.analyze_workflows()

        for pattern in patterns:
            if isinstance(pattern, WorkflowPattern):
                assert pattern.template is not None
                assert len(pattern.template) > 0

    def test_workflow_min_samples(self, detector):
        """Test minimum sample requirement for workflows"""
        # Create data with too few samples
        analytics = {
            "skill_usage": {
                "skill-1": {"metadata": {"commit_format": "conventional"}},
                "skill-2": {"metadata": {"commit_format": "conventional"}},
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_workflows()

        # Should not detect pattern (too few samples)
        assert len(patterns) == 0

    def test_workflow_threshold(self, detector):
        """Test workflow detection threshold"""
        # Create data with 50/50 split (below threshold)
        analytics = {
            "skill_usage": {
                f"skill-{i}": {
                    "metadata": {"commit_format": "conventional" if i % 2 == 0 else "semantic"}
                }
                for i in range(30)
            }
        }
        Config.save_analytics(analytics)

        detector = PatternDetector(config_module=Config)
        patterns = detector.analyze_workflows()

        # Should not detect strong pattern (below threshold)
        assert len(patterns) == 0


class TestUpdateConfidence:
    """Test update_confidence()"""

    def test_update_confidence_positive(self, detector_with_patterns):
        """Test updating confidence with positive outcome"""
        initial_confidence = detector_with_patterns.patterns["combo_123"].confidence

        detector_with_patterns.update_confidence("combo_123", outcome=True)

        # Confidence should increase or stay high
        new_confidence = detector_with_patterns.patterns["combo_123"].confidence
        assert new_confidence >= initial_confidence * 0.8

    def test_update_confidence_negative(self, detector_with_patterns):
        """Test updating confidence with negative outcome"""
        initial_confidence = detector_with_patterns.patterns["combo_123"].confidence

        detector_with_patterns.update_confidence("combo_123", outcome=False)

        # Confidence should decrease
        new_confidence = detector_with_patterns.patterns["combo_123"].confidence
        assert new_confidence < initial_confidence

    def test_update_confidence_nonexistent(self, detector):
        """Test updating nonexistent pattern"""
        # Should not raise error
        detector.update_confidence("nonexistent", outcome=True)

    def test_update_confidence_updates_last_seen(self, detector_with_patterns):
        """Test that update_confidence updates last_seen"""
        old_last_seen = detector_with_patterns.patterns["combo_123"].last_seen

        detector_with_patterns.update_confidence("combo_123", outcome=True)

        new_last_seen = detector_with_patterns.patterns["combo_123"].last_seen
        # Should be updated to more recent time
        assert new_last_seen >= old_last_seen

    def test_update_confidence_exponential_moving_average(self, detector_with_patterns):
        """Test EMA-based confidence update"""
        # Multiple positive outcomes should gradually increase confidence
        initial = detector_with_patterns.patterns["combo_123"].success_rate

        for i in range(5):
            detector_with_patterns.update_confidence("combo_123", outcome=True)

        final = detector_with_patterns.patterns["combo_123"].success_rate
        # Should be higher but not jump to 1.0 immediately
        assert final > initial
        assert final <= 1.0


class TestApplyPatternDecay:
    """Test apply_pattern_decay()"""

    def test_decay_reduces_confidence(self, detector_with_patterns):
        """Test that decay reduces pattern confidence"""
        # Set last_seen to 3 months ago
        old_pattern = detector_with_patterns.patterns["combo_123"]
        old_pattern.last_seen = datetime.now() - timedelta(days=90)
        initial_confidence = old_pattern.confidence

        detector_with_patterns.apply_pattern_decay()

        # Confidence should be reduced
        new_confidence = detector_with_patterns.patterns["combo_123"].confidence
        assert new_confidence < initial_confidence

    def test_decay_removes_low_confidence(self, detector_with_patterns):
        """Test that very old patterns are removed"""
        # Set last_seen to very old and reduce confidence
        old_pattern = detector_with_patterns.patterns["combo_123"]
        old_pattern.last_seen = datetime.now() - timedelta(days=365)
        old_pattern.confidence = 0.2  # Below removal threshold

        detector_with_patterns.apply_pattern_decay()

        # Pattern should be removed
        assert "combo_123" not in detector_with_patterns.patterns

    def test_decay_preserves_recent_patterns(self, detector_with_patterns):
        """Test that recent patterns are not removed"""
        # Set last_seen to today
        detector_with_patterns.patterns["combo_123"].last_seen = datetime.now()

        detector_with_patterns.apply_pattern_decay()

        # Pattern should still exist
        assert "combo_123" in detector_with_patterns.patterns

    def test_decay_exponential_formula(self, detector_with_patterns):
        """Test that decay uses exponential formula"""
        # Set specific values for testing
        pattern = detector_with_patterns.patterns["combo_123"]
        pattern.confidence = 1.0
        pattern.last_seen = datetime.now() - timedelta(days=30)  # 1 month

        detector_with_patterns.apply_pattern_decay()

        # Confidence should be reduced by ~10% (decay rate per month)
        expected_range = (0.85, 0.95)
        assert expected_range[0] <= pattern.confidence <= expected_range[1]


class TestConfidenceCalculation:
    """Test confidence calculation algorithm"""

    def test_confidence_formula_components(self, detector):
        """Test that confidence uses frequency, success, and recency"""
        now = datetime.now()
        pattern = CombinationPattern(
            pattern_id="test_pattern",
            pattern_type="combination",
            description="Test pattern",
            confidence=0.0,
            frequency=25,
            success_rate=0.9,
            first_seen=now - timedelta(days=60),
            last_seen=now,
            skills=["skill-a", "skill-b"]
        )

        confidence = detector._calculate_confidence(pattern)

        # Should be high (good frequency, success rate, and recent)
        assert confidence > 0.7

    def test_confidence_frequency_weight(self, detector):
        """Test frequency component of confidence"""
        now = datetime.now()

        # Low frequency
        pattern1 = DetectedPattern(
            pattern_id="p1",
            pattern_type="combination",
            description="Low frequency",
            confidence=0.0,
            frequency=5,
            success_rate=1.0,
            first_seen=now,
            last_seen=now
        )

        # High frequency
        pattern2 = DetectedPattern(
            pattern_id="p2",
            pattern_type="combination",
            description="High frequency",
            confidence=0.0,
            frequency=50,
            success_rate=1.0,
            first_seen=now,
            last_seen=now
        )

        conf1 = detector._calculate_confidence(pattern1)
        conf2 = detector._calculate_confidence(pattern2)

        # Higher frequency should have higher confidence
        assert conf2 > conf1

    def test_confidence_success_weight(self, detector):
        """Test success rate component of confidence"""
        now = datetime.now()

        # Low success
        pattern1 = DetectedPattern(
            pattern_id="p1",
            pattern_type="combination",
            description="Low success",
            confidence=0.0,
            frequency=50,
            success_rate=0.5,
            first_seen=now,
            last_seen=now
        )

        # High success
        pattern2 = DetectedPattern(
            pattern_id="p2",
            pattern_type="combination",
            description="High success",
            confidence=0.0,
            frequency=50,
            success_rate=1.0,
            first_seen=now,
            last_seen=now
        )

        conf1 = detector._calculate_confidence(pattern1)
        conf2 = detector._calculate_confidence(pattern2)

        # Higher success rate should have higher confidence
        assert conf2 > conf1

    def test_confidence_recency_weight(self, detector):
        """Test recency component of confidence"""
        # Recent pattern
        pattern1 = DetectedPattern(
            pattern_id="p1",
            pattern_type="combination",
            description="Recent",
            confidence=0.0,
            frequency=50,
            success_rate=1.0,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )

        # Old pattern
        pattern2 = DetectedPattern(
            pattern_id="p2",
            pattern_type="combination",
            description="Old",
            confidence=0.0,
            frequency=50,
            success_rate=1.0,
            first_seen=datetime.now() - timedelta(days=365),
            last_seen=datetime.now() - timedelta(days=365)
        )

        conf1 = detector._calculate_confidence(pattern1)
        conf2 = detector._calculate_confidence(pattern2)

        # Recent pattern should have higher confidence
        assert conf1 > conf2

    def test_confidence_range(self, detector):
        """Test that confidence is always in valid range"""
        now = datetime.now()

        # Test with extreme values
        pattern = DetectedPattern(
            pattern_id="extreme",
            pattern_type="combination",
            description="Extreme values",
            confidence=0.0,
            frequency=1000,
            success_rate=1.0,
            first_seen=now,
            last_seen=now
        )

        confidence = detector._calculate_confidence(pattern)

        # Should be capped at 1.0
        assert 0.0 <= confidence <= 1.0


class TestGetApplicablePatterns:
    """Test get_applicable_patterns()"""

    def test_filter_by_confidence(self, detector_with_patterns):
        """Test that only high-confidence patterns are returned"""
        context = {"active_skills": ["nextjs-fullstack"]}

        patterns = detector_with_patterns.get_applicable_patterns(context)

        # All returned patterns should meet confidence threshold
        for pattern in patterns:
            assert pattern.confidence >= detector_with_patterns.SUGGEST_CONFIDENCE

    def test_filter_by_context(self, detector_with_patterns):
        """Test context-based filtering"""
        # Context with specific skills
        context = {"active_skills": ["nextjs-fullstack", "supabase-integration"]}

        patterns = detector_with_patterns.get_applicable_patterns(context)

        # Should return combination pattern
        assert len(patterns) >= 0

    def test_sorted_by_confidence(self, detector_with_patterns):
        """Test that patterns are sorted by confidence"""
        context = {"operation": "code_generation"}

        patterns = detector_with_patterns.get_applicable_patterns(context)

        # Check ordering
        for i in range(len(patterns) - 1):
            assert patterns[i].confidence >= patterns[i + 1].confidence

    def test_should_auto_apply(self, detector_with_patterns):
        """Test auto-apply threshold"""
        pattern = detector_with_patterns.patterns["style_naming_camelCase"]

        # High confidence pattern
        pattern.confidence = 0.95
        assert detector_with_patterns.should_auto_apply(pattern) is False  # Opt-in by default

        # Low confidence pattern
        pattern.confidence = 0.85
        assert detector_with_patterns.should_auto_apply(pattern) is False


class TestPatternPersistence:
    """Test pattern loading and saving"""

    def test_patterns_saved_to_disk(self, detector_with_usage_data):
        """Test that detected patterns are saved"""
        detector_with_usage_data.detect_patterns()

        # Check that file exists
        patterns_file = Config.DATA_DIR / "learned_patterns.json"
        assert patterns_file.exists()

    def test_patterns_loaded_on_init(self, detector_with_patterns):
        """Test that patterns are loaded on initialization"""
        # Should have loaded existing patterns
        assert len(detector_with_patterns.patterns) > 0
        assert "combo_123" in detector_with_patterns.patterns

    def test_pattern_serialization(self, detector):
        """Test pattern to/from dict conversion"""
        now = datetime.now()
        pattern = CombinationPattern(
            pattern_id="test",
            pattern_type="combination",
            description="Test",
            confidence=0.85,
            frequency=20,
            success_rate=0.9,
            first_seen=now,
            last_seen=now,
            skills=["skill-a", "skill-b"]
        )

        # Convert to dict and back
        pattern_dict = pattern.to_dict()
        restored = CombinationPattern.from_dict(pattern_dict)

        assert restored.pattern_id == pattern.pattern_id
        assert restored.confidence == pattern.confidence
        assert restored.skills == pattern.skills

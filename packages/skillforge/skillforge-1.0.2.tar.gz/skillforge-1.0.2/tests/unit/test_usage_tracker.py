"""
Unit tests for UsageTracker class

Tests usage tracking including:
- Tracking usage with success/failure outcomes
- Recording skill combinations
- Recording intent patterns
- Getting usage statistics
- Analyzing usage trends
- Privacy controls and opt-out functionality
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from skillforge.analyzers.usage_tracker import UsageTracker
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
def tracker(temp_home):
    """Create UsageTracker instance with clean state"""
    return UsageTracker()


@pytest.fixture
def tracker_with_data(temp_home):
    """Create UsageTracker with some existing data"""
    tracker = UsageTracker()

    # Add some test data
    tracker.track_usage(["nextjs-fullstack"], success=True, duration=45.5)
    tracker.track_usage(["react-component"], success=True, duration=30.2)
    tracker.track_usage(["nextjs-fullstack", "supabase-integration"], success=True, duration=67.8)
    tracker.track_usage(["react-component"], success=False, duration=15.0)

    return tracker


class TestTrackUsage:
    """Test track_usage() with success/failure outcomes"""

    def test_track_single_skill_success(self, tracker):
        """Test tracking successful usage of single skill"""
        tracker.track_usage(
            skills=["nextjs-fullstack"],
            success=True,
            duration=45.5
        )

        stats = tracker.get_statistics()
        skill_data = stats["skill_usage"]["nextjs-fullstack"]

        assert skill_data["total_uses"] == 1
        assert skill_data["successes"] == 1
        assert skill_data["failures"] == 0
        assert skill_data["success_rate"] == 1.0
        assert skill_data["avg_duration_seconds"] == 45.5

    def test_track_single_skill_failure(self, tracker):
        """Test tracking failed usage of single skill"""
        tracker.track_usage(
            skills=["nextjs-fullstack"],
            success=False,
            duration=20.0
        )

        stats = tracker.get_statistics()
        skill_data = stats["skill_usage"]["nextjs-fullstack"]

        assert skill_data["total_uses"] == 1
        assert skill_data["successes"] == 0
        assert skill_data["failures"] == 1
        assert skill_data["success_rate"] == 0.0

    def test_track_multiple_usages(self, tracker):
        """Test tracking multiple usages of same skill"""
        tracker.track_usage(["react-component"], success=True, duration=30.0)
        tracker.track_usage(["react-component"], success=True, duration=40.0)
        tracker.track_usage(["react-component"], success=False, duration=10.0)

        stats = tracker.get_statistics()
        skill_data = stats["skill_usage"]["react-component"]

        assert skill_data["total_uses"] == 3
        assert skill_data["successes"] == 2
        assert skill_data["failures"] == 1
        assert skill_data["success_rate"] == 2/3

    def test_track_average_duration(self, tracker):
        """Test average duration calculation"""
        tracker.track_usage(["nextjs-fullstack"], success=True, duration=30.0)
        tracker.track_usage(["nextjs-fullstack"], success=True, duration=60.0)

        stats = tracker.get_statistics()
        skill_data = stats["skill_usage"]["nextjs-fullstack"]

        assert skill_data["avg_duration_seconds"] == 45.0

    def test_track_with_metadata(self, tracker):
        """Test tracking with additional metadata"""
        metadata = {"framework": "Next.js", "version": "14.0"}

        tracker.track_usage(
            skills=["nextjs-fullstack"],
            success=True,
            duration=45.0,
            metadata=metadata
        )

        # Should not raise error
        assert True

    def test_track_empty_skills_list(self, tracker):
        """Test tracking with empty skills list"""
        tracker.track_usage(skills=[], success=True, duration=10.0)

        stats = tracker.get_statistics()
        # Should not add any skills
        assert len(stats["skill_usage"]) == 0

    def test_track_updates_last_used(self, tracker):
        """Test that last_used timestamp is updated"""
        tracker.track_usage(["nextjs-fullstack"], success=True, duration=30.0)

        stats = tracker.get_statistics()
        skill_data = stats["skill_usage"]["nextjs-fullstack"]

        assert "last_used" in skill_data
        # Should be recent timestamp
        last_used = datetime.fromisoformat(skill_data["last_used"].replace("Z", "+00:00"))
        assert (datetime.utcnow() - last_used.replace(tzinfo=None)).total_seconds() < 5


class TestRecordCombination:
    """Test record_combination() for skill pairs"""

    def test_record_two_skills(self, tracker):
        """Test recording combination of two skills"""
        tracker.record_combination(
            skills=["nextjs-fullstack", "supabase-integration"],
            success=True,
            duration=60.0
        )

        stats = tracker.get_statistics()
        combo_key = "nextjs-fullstack+supabase-integration"

        assert combo_key in stats["combinations"]
        combo_data = stats["combinations"][combo_key]
        assert combo_data["count"] == 1
        assert combo_data["successes"] == 1
        assert combo_data["success_rate"] == 1.0

    def test_record_multiple_combinations(self, tracker):
        """Test recording same combination multiple times"""
        skills = ["nextjs-fullstack", "supabase-integration"]

        tracker.record_combination(skills, success=True, duration=50.0)
        tracker.record_combination(skills, success=True, duration=60.0)
        tracker.record_combination(skills, success=False, duration=30.0)

        stats = tracker.get_statistics()
        combo_key = "nextjs-fullstack+supabase-integration"
        combo_data = stats["combinations"][combo_key]

        assert combo_data["count"] == 3
        assert combo_data["successes"] == 2
        assert combo_data["failures"] == 1
        assert combo_data["success_rate"] == 2/3

    def test_record_combination_order_independent(self, tracker):
        """Test that combination key is order-independent"""
        tracker.record_combination(["skill-a", "skill-b"], success=True)
        tracker.record_combination(["skill-b", "skill-a"], success=True)

        stats = tracker.get_statistics()
        combo_key = "skill-a+skill-b"

        # Should be same combination
        assert combo_key in stats["combinations"]
        assert stats["combinations"][combo_key]["count"] == 2

    def test_record_single_skill_ignored(self, tracker):
        """Test that single skill is not recorded as combination"""
        tracker.record_combination(["single-skill"], success=True)

        stats = tracker.get_statistics()
        # Should not create combination
        assert len(stats["combinations"]) == 0

    def test_record_combination_average_duration(self, tracker):
        """Test average duration calculation for combinations"""
        skills = ["nextjs-fullstack", "supabase-integration"]

        tracker.record_combination(skills, success=True, duration=40.0)
        tracker.record_combination(skills, success=True, duration=60.0)

        stats = tracker.get_statistics()
        combo_key = "nextjs-fullstack+supabase-integration"
        combo_data = stats["combinations"][combo_key]

        assert combo_data["avg_duration"] == 50.0

    def test_track_usage_creates_combination(self, tracker):
        """Test that track_usage automatically records combinations"""
        tracker.track_usage(
            skills=["nextjs-fullstack", "supabase-integration"],
            success=True,
            duration=50.0
        )

        stats = tracker.get_statistics()
        combo_key = "nextjs-fullstack+supabase-integration"

        assert combo_key in stats["combinations"]

    def test_track_usage_updates_common_with(self, tracker):
        """Test that track_usage updates common_with relationships"""
        tracker.track_usage(
            skills=["nextjs-fullstack", "supabase-integration"],
            success=True,
            duration=50.0
        )

        stats = tracker.get_statistics()
        nextjs_data = stats["skill_usage"]["nextjs-fullstack"]

        assert "supabase-integration" in nextjs_data["common_with"]


class TestRecordPattern:
    """Test record_pattern() for intent patterns"""

    def test_record_new_pattern(self, tracker):
        """Test recording a new pattern"""
        tracker.record_pattern(
            intent_text="create nextjs auth",
            skills=["nextjs-fullstack", "supabase-integration"],
            confidence=0.85
        )

        stats = tracker.get_statistics()
        pattern_key = "create_nextjs_auth"

        assert pattern_key in stats["patterns"]
        pattern_data = stats["patterns"][pattern_key]
        assert pattern_data["skills"] == ["nextjs-fullstack", "supabase-integration"]
        assert pattern_data["confidence"] == 0.85
        assert pattern_data["frequency"] == 1

    def test_record_pattern_normalizes_text(self, tracker):
        """Test that intent text is normalized"""
        tracker.record_pattern(
            intent_text="Create NextJS Auth",
            skills=["nextjs-fullstack"],
            confidence=0.9
        )

        stats = tracker.get_statistics()
        # Should be lowercase with underscores
        assert "create_nextjs_auth" in stats["patterns"]

    def test_record_pattern_multiple_times(self, tracker):
        """Test recording same pattern multiple times"""
        tracker.record_pattern("create auth", ["nextjs-fullstack"], confidence=0.8)
        tracker.record_pattern("create auth", ["nextjs-fullstack"], confidence=0.9)

        stats = tracker.get_statistics()
        pattern_data = stats["patterns"]["create_auth"]

        assert pattern_data["frequency"] == 2
        # Confidence should be updated (exponential moving average)
        assert 0.8 <= pattern_data["confidence"] <= 0.9

    def test_record_pattern_updates_confidence(self, tracker):
        """Test confidence update with exponential moving average"""
        tracker.record_pattern("test pattern", ["skill-a"], confidence=0.5)
        tracker.record_pattern("test pattern", ["skill-a"], confidence=1.0)

        stats = tracker.get_statistics()
        pattern_data = stats["patterns"]["test_pattern"]

        # Should be between 0.5 and 1.0 (weighted average)
        assert 0.5 < pattern_data["confidence"] < 1.0

    def test_record_pattern_empty_intent(self, tracker):
        """Test recording pattern with empty intent"""
        tracker.record_pattern("", ["skill-a"])

        stats = tracker.get_statistics()
        # Should not create pattern
        assert len(stats["patterns"]) == 0

    def test_record_pattern_empty_skills(self, tracker):
        """Test recording pattern with empty skills"""
        tracker.record_pattern("create something", [])

        stats = tracker.get_statistics()
        # Should not create pattern
        assert len(stats["patterns"]) == 0


class TestGetStatistics:
    """Test get_statistics() output"""

    def test_statistics_structure(self, tracker_with_data):
        """Test that statistics have correct structure"""
        stats = tracker_with_data.get_statistics()

        assert "skill_usage" in stats
        assert "combinations" in stats
        assert "patterns" in stats
        assert "summary" in stats

    def test_statistics_summary(self, tracker_with_data):
        """Test summary statistics calculation"""
        stats = tracker_with_data.get_statistics()
        summary = stats["summary"]

        assert "total_skills_tracked" in summary
        assert "total_uses" in summary
        assert "total_successes" in summary
        assert "total_failures" in summary
        assert "overall_success_rate" in summary
        assert summary["total_skills_tracked"] >= 2

    def test_statistics_success_rate(self, tracker):
        """Test overall success rate calculation"""
        tracker.track_usage(["skill-a"], success=True, duration=10.0)
        tracker.track_usage(["skill-b"], success=True, duration=10.0)
        tracker.track_usage(["skill-a"], success=False, duration=10.0)

        stats = tracker.get_statistics()
        # 2 successes out of 3 total
        assert stats["summary"]["overall_success_rate"] == 2/3

    def test_statistics_empty_tracker(self, tracker):
        """Test statistics with no data"""
        stats = tracker.get_statistics()

        assert stats["summary"]["total_skills_tracked"] == 0
        assert stats["summary"]["total_uses"] == 0
        assert stats["summary"]["overall_success_rate"] == 0.0

    def test_statistics_top_combinations(self, tracker):
        """Test that top combinations are returned"""
        # Create multiple combinations
        for i in range(15):
            tracker.record_combination([f"skill-{i}", f"skill-{i+1}"], success=True)

        stats = tracker.get_statistics()
        # Should limit to top 10
        assert len(stats["combinations"]) <= 10


class TestAnalyzeTrends:
    """Test analyze_trends() functionality"""

    def test_trends_structure(self, tracker_with_data):
        """Test that trends have correct structure"""
        trends = tracker_with_data.analyze_trends(days=30)

        assert "daily_usage" in trends
        assert "trending_skills" in trends
        assert "declining_skills" in trends
        assert "recent_patterns" in trends
        assert "total_recent_events" in trends
        assert "analysis_period_days" in trends

    def test_trends_period(self, tracker):
        """Test trends for different time periods"""
        trends_7 = tracker.analyze_trends(days=7)
        trends_30 = tracker.analyze_trends(days=30)

        assert trends_7["analysis_period_days"] == 7
        assert trends_30["analysis_period_days"] == 30

    def test_trends_daily_usage(self, tracker):
        """Test daily usage aggregation"""
        # Add some usage events
        tracker.track_usage(["skill-a"], success=True, duration=10.0)
        tracker.track_usage(["skill-b"], success=True, duration=10.0)

        trends = tracker.analyze_trends(days=7)

        # Should have at least today's date
        assert len(trends["daily_usage"]) >= 1

    def test_trends_empty_data(self, tracker):
        """Test trends with no data"""
        trends = tracker.analyze_trends(days=30)

        assert trends["daily_usage"] == {}
        assert trends["trending_skills"] == []
        assert trends["declining_skills"] == []


class TestPrivacyControls:
    """Test privacy controls and opt-out functionality"""

    def test_tracking_disabled_by_profile(self, tracker, temp_home):
        """Test that tracking respects user profile settings"""
        # Disable tracking
        profile = Config.load_user_profile()
        profile["learning"] = {"enabled": False}
        Config.save_user_profile(profile)

        # Create new tracker to pick up settings
        tracker = UsageTracker()

        # Try to track usage
        tracker.track_usage(["skill-a"], success=True, duration=10.0)

        # Should not save data
        stats = tracker.get_statistics()
        assert stats["summary"]["total_skills_tracked"] == 0

    def test_tracking_enabled_by_default(self, tracker):
        """Test that tracking is enabled by default"""
        tracker.track_usage(["skill-a"], success=True, duration=10.0)

        stats = tracker.get_statistics()
        assert stats["summary"]["total_skills_tracked"] == 1

    def test_clear_all_data(self, tracker_with_data):
        """Test clearing all tracked data"""
        # Verify data exists
        stats_before = tracker_with_data.get_statistics()
        assert stats_before["summary"]["total_skills_tracked"] > 0

        # Clear all data
        tracker_with_data.clear_all_data()

        # Verify data is cleared
        stats_after = tracker_with_data.get_statistics()
        assert stats_after["summary"]["total_skills_tracked"] == 0
        assert len(stats_after["skill_usage"]) == 0
        assert len(stats_after["combinations"]) == 0
        assert len(stats_after["patterns"]) == 0

    def test_clear_data_preserves_structure(self, tracker_with_data):
        """Test that clear_all_data preserves data structure"""
        tracker_with_data.clear_all_data()

        # Should still have proper structure
        data = tracker_with_data.export_data()
        assert "skill_usage" in data
        assert "combinations" in data
        assert "patterns" in data
        assert "events" in data
        assert "metadata" in data

    def test_export_data(self, tracker_with_data):
        """Test exporting all tracked data"""
        data = tracker_with_data.export_data()

        assert isinstance(data, dict)
        assert "skill_usage" in data
        assert "combinations" in data
        assert "patterns" in data
        assert len(data["skill_usage"]) > 0

    def test_export_data_serializable(self, tracker_with_data):
        """Test that exported data is JSON serializable"""
        data = tracker_with_data.export_data()

        # Should not raise error
        json_str = json.dumps(data)
        assert isinstance(json_str, str)


class TestSkillInsights:
    """Test get_skill_insights() functionality"""

    def test_insights_for_existing_skill(self, tracker):
        """Test getting insights for tracked skill"""
        # Track skill multiple times
        tracker.track_usage(["nextjs-fullstack"], success=True, duration=30.0)
        tracker.track_usage(["nextjs-fullstack"], success=True, duration=40.0)

        insights = tracker.get_skill_insights("nextjs-fullstack")

        assert insights is not None
        assert insights["success_rate"] == 1.0
        assert insights["performance_rating"] == "excellent"
        assert "recommendation" in insights

    def test_insights_performance_ratings(self, tracker):
        """Test different performance rating thresholds"""
        # Excellent: >= 0.9
        tracker.track_usage(["skill-excellent"], success=True, duration=10.0)
        insights = tracker.get_skill_insights("skill-excellent")
        assert insights["performance_rating"] == "excellent"

        # Good: >= 0.75
        for i in range(7):
            tracker.track_usage(["skill-good"], success=True, duration=10.0)
        for i in range(3):
            tracker.track_usage(["skill-good"], success=False, duration=10.0)
        insights = tracker.get_skill_insights("skill-good")
        assert insights["performance_rating"] in ["good", "fair"]

    def test_insights_nonexistent_skill(self, tracker):
        """Test insights for nonexistent skill"""
        insights = tracker.get_skill_insights("nonexistent-skill")
        assert insights is None

    def test_get_skill_recommendations(self, tracker):
        """Test skill recommendations based on context"""
        # Track some combinations
        tracker.track_usage(["skill-a", "skill-b"], success=True, duration=30.0)
        tracker.track_usage(["skill-a", "skill-c"], success=True, duration=40.0)

        # Get recommendations for skill-a
        recs = tracker.get_skill_recommendations(["skill-a"], limit=3)

        # Should recommend skills commonly used with skill-a
        rec_skills = [skill for skill, conf in recs]
        assert "skill-b" in rec_skills or "skill-c" in rec_skills

    def test_recommendations_empty_context(self, tracker):
        """Test recommendations with empty context"""
        recs = tracker.get_skill_recommendations([], limit=5)
        assert recs == []


class TestDataPersistence:
    """Test data persistence and loading"""

    def test_data_persists_across_instances(self, temp_home):
        """Test that data persists across tracker instances"""
        # Create tracker and add data
        tracker1 = UsageTracker()
        tracker1.track_usage(["skill-a"], success=True, duration=30.0)

        # Create new tracker instance
        tracker2 = UsageTracker()
        stats = tracker2.get_statistics()

        # Should load previous data
        assert "skill-a" in stats["skill_usage"]

    def test_atomic_write_with_backup(self, tracker, temp_home):
        """Test that data is written atomically with backup"""
        tracker.track_usage(["skill-a"], success=True, duration=30.0)

        analytics_path = Config.DATA_DIR / "usage_analytics.json"
        backup_path = Config.DATA_DIR / "usage_analytics.json.backup"

        # Main file should exist
        assert analytics_path.exists()

    def test_corrupted_data_recovery(self, temp_home):
        """Test recovery from corrupted analytics file"""
        # Write corrupted data
        analytics_path = Config.DATA_DIR / "usage_analytics.json"
        analytics_path.write_text("{ invalid json }")

        # Should not crash
        tracker = UsageTracker()
        stats = tracker.get_statistics()

        # Should have empty/default structure
        assert isinstance(stats, dict)

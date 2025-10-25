"""
Unit tests for Config class

Tests configuration management including:
- Directory creation
- User profile management
- Analytics management
- Learned patterns management
- Cache management
"""

import pytest
import json
import tempfile
from pathlib import Path
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

    # Cleanup is automatic with tmp_path


class TestConfigDirectories:
    """Test directory creation and management"""

    def test_ensure_directories_creates_structure(self, temp_home):
        """Test that ensure_directories creates all required directories"""
        Config.ensure_directories()

        assert Config.SKILLFORGE_HOME.exists()
        assert Config.DATA_DIR.exists()
        assert Config.CACHE_DIR.exists()

    def test_ensure_directories_idempotent(self, temp_home):
        """Test that calling ensure_directories multiple times is safe"""
        Config.ensure_directories()
        Config.ensure_directories()  # Should not raise error

        assert Config.SKILLFORGE_HOME.exists()


class TestUserProfile:
    """Test user profile management"""

    def test_load_user_profile_default(self, temp_home):
        """Test loading default profile when file doesn't exist"""
        profile = Config.load_user_profile()

        assert "setup_completed" in profile
        assert profile["setup_completed"] is False
        assert "tech_stack" in profile
        assert "preferences" in profile
        assert "conventions" in profile

    def test_save_and_load_user_profile(self, temp_home):
        """Test saving and loading user profile"""
        test_profile = {
            "setup_completed": True,
            "tech_stack": {
                "frontend": "Next.js",
                "ui": "Tailwind CSS"
            },
            "preferences": {
                "naming": "camelCase"
            },
            "conventions": {}
        }

        Config.save_user_profile(test_profile)
        loaded = Config.load_user_profile()

        assert loaded["setup_completed"] is True
        assert loaded["tech_stack"]["frontend"] == "Next.js"
        assert loaded["preferences"]["naming"] == "camelCase"

    def test_save_user_profile_creates_directory(self, temp_home):
        """Test that save creates data directory if it doesn't exist"""
        # Remove data directory
        import shutil
        if Config.DATA_DIR.exists():
            shutil.rmtree(Config.DATA_DIR)

        profile = {"setup_completed": True}
        Config.save_user_profile(profile)

        assert Config.DATA_DIR.exists()
        assert (Config.DATA_DIR / "user_profile.json").exists()

    def test_load_user_profile_handles_corrupted_json(self, temp_home):
        """Test that corrupted JSON returns default profile"""
        profile_path = Config.DATA_DIR / "user_profile.json"

        # Write corrupted JSON
        with open(profile_path, 'w') as f:
            f.write("{ invalid json }")

        profile = Config.load_user_profile()

        # Should return default profile without crashing
        assert "setup_completed" in profile
        assert profile["setup_completed"] is False


class TestAnalytics:
    """Test usage analytics management"""

    def test_load_analytics_default(self, temp_home):
        """Test loading default analytics when file doesn't exist"""
        analytics = Config.load_analytics()

        assert "skill_usage" in analytics
        assert "patterns" in analytics
        assert isinstance(analytics["skill_usage"], dict)
        assert isinstance(analytics["patterns"], dict)

    def test_save_and_load_analytics(self, temp_home):
        """Test saving and loading analytics"""
        test_analytics = {
            "skill_usage": {
                "nextjs-fullstack": {
                    "total_uses": 50,
                    "successes": 47,
                    "failures": 3
                }
            },
            "patterns": {
                "combination_1": {"count": 10}
            }
        }

        Config.save_analytics(test_analytics)
        loaded = Config.load_analytics()

        assert loaded["skill_usage"]["nextjs-fullstack"]["total_uses"] == 50
        assert loaded["patterns"]["combination_1"]["count"] == 10

    def test_load_analytics_handles_corrupted_json(self, temp_home):
        """Test that corrupted analytics JSON returns empty structure"""
        analytics_path = Config.DATA_DIR / "usage_analytics.json"

        # Write corrupted JSON
        with open(analytics_path, 'w') as f:
            f.write("{ invalid json }")

        analytics = Config.load_analytics()

        # Should return empty structure without crashing
        assert analytics == {"skill_usage": {}, "patterns": {}}


class TestLearnedPatterns:
    """Test learned patterns management"""

    def test_load_learned_patterns_default(self, temp_home):
        """Test loading default learned patterns when file doesn't exist"""
        patterns = Config.load_learned_patterns()

        assert isinstance(patterns, dict)
        assert len(patterns) == 0

    def test_save_and_load_learned_patterns(self, temp_home):
        """Test saving and loading learned patterns"""
        test_patterns = {
            "always_use_zod": {
                "confidence": 0.92,
                "occurrences": 23,
                "description": "Always use Zod for validation"
            }
        }

        Config.save_learned_patterns(test_patterns)
        loaded = Config.load_learned_patterns()

        assert "always_use_zod" in loaded
        assert loaded["always_use_zod"]["confidence"] == 0.92


class TestCache:
    """Test cache management"""

    def test_get_cache_path(self, temp_home):
        """Test getting cache path for a library"""
        cache_path = Config.get_cache_path("next.js")

        assert cache_path.parent == Config.CACHE_DIR
        assert "next" in cache_path.name
        assert cache_path.suffix == ".json"

    def test_get_cache_path_sanitizes_special_chars(self, temp_home):
        """Test that special characters are sanitized in cache path"""
        cache_path = Config.get_cache_path("@types/react")

        # Should not contain @ or /
        assert "@" not in cache_path.name
        assert "/" not in cache_path.name

    def test_is_cache_valid_no_file(self, temp_home):
        """Test cache validity when file doesn't exist"""
        assert Config.is_cache_valid("nonexistent") is False

    def test_is_cache_valid_fresh_file(self, temp_home):
        """Test cache validity for fresh file"""
        cache_path = Config.get_cache_path("test-lib")
        cache_path.write_text('{"docs": "test"}')

        assert Config.is_cache_valid("test-lib", max_age_days=7) is True

    def test_is_cache_valid_stale_file(self, temp_home):
        """Test cache validity for stale file"""
        import time
        import os

        cache_path = Config.get_cache_path("test-lib")
        cache_path.write_text('{"docs": "test"}')

        # Set file modification time to 10 days ago
        old_time = time.time() - (10 * 86400)  # 10 days in seconds
        os.utime(cache_path, (old_time, old_time))

        assert Config.is_cache_valid("test-lib", max_age_days=7) is False


class TestResetConfig:
    """Test configuration reset"""

    def test_reset_config_removes_data_files(self, temp_home):
        """Test that reset removes all data files but preserves cache"""
        # Create data files
        Config.save_user_profile({"setup_completed": True})
        Config.save_analytics({"skill_usage": {}})
        Config.save_learned_patterns({"pattern": {}})

        # Create cache file
        cache_path = Config.get_cache_path("test-lib")
        cache_path.write_text('{"docs": "test"}')

        # Reset
        Config.reset_config()

        # Data files should be gone
        assert not (Config.DATA_DIR / "user_profile.json").exists()
        assert not (Config.DATA_DIR / "usage_analytics.json").exists()
        assert not (Config.DATA_DIR / "learned_patterns.json").exists()

        # Cache should still exist
        assert cache_path.exists()

    def test_reset_config_idempotent(self, temp_home):
        """Test that resetting when files don't exist doesn't raise error"""
        Config.reset_config()  # Should not raise error
        Config.reset_config()  # Second call should also not raise error


# Integration test
class TestConfigIntegration:
    """Integration tests for Config class"""

    def test_full_workflow(self, temp_home):
        """Test complete workflow: setup -> use -> reset"""
        # 1. Initial state - everything empty
        profile = Config.load_user_profile()
        assert profile["setup_completed"] is False

        # 2. User completes wizard
        profile["setup_completed"] = True
        profile["tech_stack"] = {"frontend": "Next.js"}
        Config.save_user_profile(profile)

        # 3. Skills are used, analytics tracked
        analytics = Config.load_analytics()
        analytics["skill_usage"]["nextjs-fullstack"] = {
            "total_uses": 10,
            "successes": 9,
            "failures": 1
        }
        Config.save_analytics(analytics)

        # 4. Patterns learned
        patterns = Config.load_learned_patterns()
        patterns["pattern1"] = {"confidence": 0.85}
        Config.save_learned_patterns(patterns)

        # 5. Verify everything persisted
        assert Config.load_user_profile()["setup_completed"] is True
        assert Config.load_analytics()["skill_usage"]["nextjs-fullstack"]["total_uses"] == 10
        assert Config.load_learned_patterns()["pattern1"]["confidence"] == 0.85

        # 6. Reset
        Config.reset_config()

        # 7. Verify reset
        assert Config.load_user_profile()["setup_completed"] is False
        assert Config.load_analytics() == {"skill_usage": {}, "patterns": {}}
        assert Config.load_learned_patterns() == {}

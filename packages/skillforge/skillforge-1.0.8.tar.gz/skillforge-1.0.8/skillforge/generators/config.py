"""
Configuration management for SkillForge

This module provides the Config class for managing:
- User profiles and preferences
- Usage analytics and patterns
- Cache management
- Directory structure
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Manages SkillForge configuration and data persistence"""

    # Default paths - can be overridden for testing
    SKILLFORGE_HOME = Path.home() / ".claude" / "skills" / "skillforge"
    DATA_DIR = SKILLFORGE_HOME / "data"
    CACHE_DIR = DATA_DIR / "cache" / "context7"
    CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

    # Default configuration structure
    DEFAULT_CONFIG = {
        "version": "0.0.1-dev",
        "user_profile": {
            "setup_completed": False,
            "tech_stack": {},
            "preferences": {},
            "conventions": {}
        },
        "learning": {
            "enabled": True,
            "min_samples_for_pattern": 10
        },
        "optimization": {
            "auto_optimize": True,
            "token_budget": 5000
        }
    }

    @classmethod
    def ensure_directories(cls) -> None:
        """
        Create necessary directories if they don't exist.

        Creates:
        - SKILLFORGE_HOME: ~/.claude/skills/skillforge/
        - DATA_DIR: ~/.claude/skills/skillforge/data/
        - CACHE_DIR: ~/.claude/skills/skillforge/data/cache/context7/
        """
        cls.SKILLFORGE_HOME.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_user_profile(cls) -> Dict[str, Any]:
        """
        Load user profile from disk or return default.

        Returns:
            Dict containing user profile with tech_stack, preferences, conventions

        Example:
            >>> profile = Config.load_user_profile()
            >>> print(profile["setup_completed"])
            False
        """
        cls.ensure_directories()
        profile_path = cls.DATA_DIR / "user_profile.json"

        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load user profile: {e}")
                print("Returning default profile.")
                return cls.DEFAULT_CONFIG["user_profile"].copy()
        else:
            return cls.DEFAULT_CONFIG["user_profile"].copy()

    @classmethod
    def save_user_profile(cls, profile: Dict[str, Any]) -> None:
        """
        Save user profile to disk.

        Args:
            profile: User profile dictionary to save

        Raises:
            OSError: If file cannot be written
        """
        cls.ensure_directories()
        profile_path = cls.DATA_DIR / "user_profile.json"

        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise OSError(f"Failed to save user profile: {e}")

    @classmethod
    def load_analytics(cls) -> Dict[str, Any]:
        """
        Load usage analytics from disk or return empty structure.

        Returns:
            Dict containing skill_usage and patterns data

        Example:
            >>> analytics = Config.load_analytics()
            >>> print(analytics["skill_usage"])
            {}
        """
        cls.ensure_directories()
        analytics_path = cls.DATA_DIR / "usage_analytics.json"

        if analytics_path.exists():
            try:
                with open(analytics_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load analytics: {e}")
                print("Returning empty analytics.")
                return {"skill_usage": {}, "patterns": {}}
        else:
            return {"skill_usage": {}, "patterns": {}}

    @classmethod
    def save_analytics(cls, analytics: Dict[str, Any]) -> None:
        """
        Save usage analytics to disk.

        Args:
            analytics: Analytics dictionary to save

        Raises:
            OSError: If file cannot be written
        """
        cls.ensure_directories()
        analytics_path = cls.DATA_DIR / "usage_analytics.json"

        try:
            with open(analytics_path, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise OSError(f"Failed to save analytics: {e}")

    @classmethod
    def load_learned_patterns(cls) -> Dict[str, Any]:
        """
        Load learned patterns from disk or return empty structure.

        Returns:
            Dict containing learned patterns with confidence scores
        """
        cls.ensure_directories()
        patterns_path = cls.DATA_DIR / "learned_patterns.json"

        if patterns_path.exists():
            try:
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load learned patterns: {e}")
                print("Returning empty patterns.")
                return {}
        else:
            return {}

    @classmethod
    def save_learned_patterns(cls, patterns: Dict[str, Any]) -> None:
        """
        Save learned patterns to disk.

        Args:
            patterns: Patterns dictionary to save

        Raises:
            OSError: If file cannot be written
        """
        cls.ensure_directories()
        patterns_path = cls.DATA_DIR / "learned_patterns.json"

        try:
            with open(patterns_path, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise OSError(f"Failed to save learned patterns: {e}")

    @classmethod
    def get_cache_path(cls, library_id: str) -> Path:
        """
        Get cache file path for a specific library.

        Args:
            library_id: Library identifier (e.g., "next.js", "react", "@types/react")

        Returns:
            Path to cache file for the library
        """
        cls.ensure_directories()
        # Sanitize library_id for filesystem - remove all special chars
        safe_id = library_id.replace('/', '_').replace('.', '_').replace('@', '_')
        return cls.CACHE_DIR / f"{safe_id}.json"

    @classmethod
    def is_cache_valid(cls, library_id: str, max_age_days: int = 7) -> bool:
        """
        Check if cached documentation is still valid.

        Args:
            library_id: Library identifier
            max_age_days: Maximum age in days before cache is considered stale

        Returns:
            True if cache exists and is fresh, False otherwise
        """
        cache_path = cls.get_cache_path(library_id)

        if not cache_path.exists():
            return False

        try:
            import time
            file_age_days = (time.time() - cache_path.stat().st_mtime) / 86400
            return file_age_days <= max_age_days
        except OSError:
            return False

    @classmethod
    def reset_config(cls) -> None:
        """
        Reset all configuration to defaults.

        WARNING: This will delete:
        - User profile
        - Usage analytics
        - Learned patterns

        Cache is preserved.
        """
        cls.ensure_directories()

        # Delete data files (but preserve cache)
        data_files = [
            cls.DATA_DIR / "user_profile.json",
            cls.DATA_DIR / "usage_analytics.json",
            cls.DATA_DIR / "learned_patterns.json"
        ]

        for file_path in data_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError as e:
                    print(f"Warning: Could not delete {file_path}: {e}")

    # Aliases for backward compatibility
    @classmethod
    def save_profile(cls, profile: Dict[str, Any]) -> None:
        """
        Alias for save_user_profile() method - for backward compatibility.

        Args:
            profile: User profile dictionary to save

        Raises:
            OSError: If file cannot be written
        """
        return cls.save_user_profile(profile)

    @classmethod
    def load_profile(cls) -> Dict[str, Any]:
        """
        Alias for load_user_profile() method - for backward compatibility.

        Returns:
            Dict containing user profile
        """
        return cls.load_user_profile()

    @classmethod
    def get_installed_skills(cls) -> list[str]:
        """
        Get list of all installed SkillForge-generated skills.

        Returns:
            List of skill names (directory names in ~/.claude/skills/)
            Excludes the skillforge meta-skill itself.

        Example:
            >>> skills = Config.get_installed_skills()
            >>> print(skills)
            ['nextjs-fullstack', 'supabase-integration', 'git-workflow']
        """
        if not cls.CLAUDE_SKILLS_DIR.exists():
            return []

        skills = []
        for item in cls.CLAUDE_SKILLS_DIR.iterdir():
            # Skip skillforge meta-skill
            if item.name == "skillforge":
                continue

            # Only include directories with SKILL.md file
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skills.append(item.name)

        return sorted(skills)

"""
Usage Tracker - Tracks skill usage patterns and statistics

This module provides the UsageTracker class for:
- Tracking individual skill usage metrics
- Recording skill combinations and success rates
- Analyzing intent→skills patterns
- Generating usage statistics and trends
- Managing privacy and user control over data

Privacy-focused: Only metadata is tracked, no code content.
"""

import json
import shutil
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..generators.config import Config


class UsageTracker:
    """
    Tracks skill usage, combinations, and patterns for learning and optimization.

    Features:
    - Individual skill usage tracking (success rate, duration, frequency)
    - Skill combination analysis
    - Intent→skills pattern recognition
    - Trend analysis over time
    - Privacy controls and opt-out support

    Data stored in: ~/.claude/skills/skillforge/data/usage_analytics.json

    Example:
        >>> tracker = UsageTracker()
        >>> tracker.track_usage(["nextjs-fullstack"], success=True, duration=45.3)
        >>> stats = tracker.get_statistics()
        >>> print(stats["skill_usage"]["nextjs-fullstack"]["success_rate"])
        1.0
    """

    def __init__(self):
        """Initialize UsageTracker and load existing data."""
        self._data = self._load_data()
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Ensure data structure has all required keys."""
        if "skill_usage" not in self._data:
            self._data["skill_usage"] = {}
        if "combinations" not in self._data:
            self._data["combinations"] = {}
        if "patterns" not in self._data:
            self._data["patterns"] = {}
        if "events" not in self._data:
            self._data["events"] = []
        if "metadata" not in self._data:
            self._data["metadata"] = {
                "created_at": self._timestamp(),
                "last_updated": self._timestamp(),
                "total_events": 0
            }

    def _load_data(self) -> Dict[str, Any]:
        """
        Load analytics data from disk.

        Returns:
            Analytics data structure
        """
        try:
            data = Config.load_analytics()
            # Migrate old format if needed
            if "skill_usage" not in data:
                data = {
                    "skill_usage": data.get("skill_usage", {}),
                    "combinations": data.get("combinations", {}),
                    "patterns": data.get("patterns", {}),
                    "events": [],
                    "metadata": {
                        "created_at": self._timestamp(),
                        "last_updated": self._timestamp(),
                        "total_events": 0
                    }
                }
            return data
        except Exception as e:
            print(f"Warning: Could not load analytics data: {e}")
            return {}

    def _save_data(self) -> None:
        """
        Save analytics data to disk with atomic write and backup.

        Uses atomic write pattern:
        1. Write to temporary file
        2. Create backup of existing file
        3. Rename temp file to target
        """
        if not self._is_tracking_enabled():
            return

        try:
            # Update metadata
            self._data["metadata"]["last_updated"] = self._timestamp()

            # Atomic write with backup
            analytics_path = Config.DATA_DIR / "usage_analytics.json"
            backup_path = Config.DATA_DIR / "usage_analytics.json.backup"
            temp_path = Config.DATA_DIR / "usage_analytics.json.tmp"

            Config.ensure_directories()

            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)

            # Backup existing file if it exists
            if analytics_path.exists():
                shutil.copy2(analytics_path, backup_path)

            # Atomic rename
            temp_path.replace(analytics_path)

        except Exception as e:
            print(f"Error saving analytics data: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()

    def _is_tracking_enabled(self) -> bool:
        """
        Check if usage tracking is enabled in user profile.

        Returns:
            True if tracking is enabled, False otherwise
        """
        try:
            profile = Config.load_user_profile()
            learning_config = profile.get("learning", {})
            return learning_config.get("enabled", True)
        except Exception:
            return True  # Default to enabled

    @staticmethod
    def _timestamp() -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO 8601 timestamp string
        """
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def _combination_key(skills: List[str]) -> str:
        """
        Create consistent key for skill combinations.

        Args:
            skills: List of skill names

        Returns:
            Sorted, joined key (e.g., "nextjs-fullstack+supabase-integration")
        """
        return "+".join(sorted(skills))

    def track_usage(
        self,
        skills: List[str],
        success: bool,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track usage of skills.

        Args:
            skills: List of skill identifiers used
            success: Whether the task was successful
            duration: Duration in seconds
            metadata: Optional additional metadata (no sensitive data)

        Example:
            >>> tracker.track_usage(
            ...     skills=["nextjs-fullstack", "supabase-integration"],
            ...     success=True,
            ...     duration=67.2
            ... )
        """
        if not self._is_tracking_enabled() or not skills:
            return

        timestamp = self._timestamp()

        # Track individual skills
        for skill in skills:
            if skill not in self._data["skill_usage"]:
                self._data["skill_usage"][skill] = {
                    "total_uses": 0,
                    "successes": 0,
                    "failures": 0,
                    "last_used": timestamp,
                    "avg_duration_seconds": 0.0,
                    "total_duration_seconds": 0.0,
                    "common_with": []
                }

            skill_data = self._data["skill_usage"][skill]
            skill_data["total_uses"] += 1

            if success:
                skill_data["successes"] += 1
            else:
                skill_data["failures"] += 1

            skill_data["last_used"] = timestamp

            # Update average duration
            skill_data["total_duration_seconds"] += duration
            skill_data["avg_duration_seconds"] = (
                skill_data["total_duration_seconds"] / skill_data["total_uses"]
            )

        # Track combinations if multiple skills used
        if len(skills) > 1:
            self.record_combination(skills, success, duration)

            # Update common_with relationships
            for skill in skills:
                others = [s for s in skills if s != skill]
                skill_data = self._data["skill_usage"][skill]

                # Update common_with list (keep top 5)
                common_dict = defaultdict(int)
                for other in skill_data.get("common_with", []):
                    common_dict[other] += 1
                for other in others:
                    common_dict[other] += 1

                skill_data["common_with"] = sorted(
                    common_dict.keys(),
                    key=lambda x: common_dict[x],
                    reverse=True
                )[:5]

        # Record event
        self._record_event("skill_used", {
            "skills": skills,
            "success": success,
            "duration": duration,
            "metadata": metadata or {}
        })

        self._save_data()

    def record_combination(
        self,
        skills: List[str],
        success: bool,
        duration: Optional[float] = None
    ) -> None:
        """
        Record a skill combination and its outcome.

        Args:
            skills: List of skill identifiers used together
            success: Whether the combination was successful
            duration: Optional duration in seconds

        Example:
            >>> tracker.record_combination(
            ...     skills=["nextjs-fullstack", "supabase-integration"],
            ...     success=True,
            ...     duration=67.2
            ... )
        """
        if not self._is_tracking_enabled() or len(skills) < 2:
            return

        combo_key = self._combination_key(skills)

        if combo_key not in self._data["combinations"]:
            self._data["combinations"][combo_key] = {
                "count": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_duration": 0.0,
                "last_seen": self._timestamp()
            }

        combo_data = self._data["combinations"][combo_key]
        combo_data["count"] += 1

        if success:
            combo_data["successes"] += 1
        else:
            combo_data["failures"] += 1

        combo_data["success_rate"] = combo_data["successes"] / combo_data["count"]
        combo_data["last_seen"] = self._timestamp()

        if duration is not None:
            combo_data["total_duration"] += duration
            combo_data["avg_duration"] = (
                combo_data["total_duration"] / combo_data["count"]
            )

        self._save_data()

    def record_pattern(
        self,
        intent_text: str,
        skills: List[str],
        confidence: Optional[float] = None
    ) -> None:
        """
        Record an intent→skills pattern.

        Args:
            intent_text: The intent or task description (normalized)
            skills: List of skill identifiers associated with this intent
            confidence: Optional confidence score (0.0-1.0)

        Example:
            >>> tracker.record_pattern(
            ...     intent_text="create_auth_component",
            ...     skills=["nextjs-fullstack", "supabase-integration"],
            ...     confidence=0.92
            ... )
        """
        if not self._is_tracking_enabled() or not intent_text or not skills:
            return

        # Normalize intent text (lowercase, replace spaces with underscores)
        pattern_key = intent_text.lower().replace(" ", "_")

        if pattern_key not in self._data["patterns"]:
            self._data["patterns"][pattern_key] = {
                "skills": skills,
                "frequency": 0,
                "confidence": confidence or 0.5,
                "last_seen": self._timestamp(),
                "first_seen": self._timestamp()
            }

        pattern_data = self._data["patterns"][pattern_key]
        pattern_data["frequency"] += 1
        pattern_data["last_seen"] = self._timestamp()

        # Update skills if they've changed
        if set(skills) != set(pattern_data["skills"]):
            # Blend old and new skills, preferring newer
            pattern_data["skills"] = skills

        # Update confidence if provided
        if confidence is not None:
            # Use exponential moving average
            alpha = 0.3
            pattern_data["confidence"] = (
                alpha * confidence + (1 - alpha) * pattern_data["confidence"]
            )

        self._save_data()

    def _record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Record a tracking event.

        Args:
            event_type: Type of event (skill_loaded, skill_used, etc.)
            data: Event data
        """
        event = {
            "type": event_type,
            "timestamp": self._timestamp(),
            "data": data
        }

        self._data["events"].append(event)
        self._data["metadata"]["total_events"] += 1

        # Keep only last 1000 events to prevent unbounded growth
        if len(self._data["events"]) > 1000:
            self._data["events"] = self._data["events"][-1000:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.

        Returns:
            Dictionary containing:
            - skill_usage: Per-skill statistics
            - combinations: Most common combinations
            - patterns: Detected patterns
            - summary: Overall summary statistics

        Example:
            >>> stats = tracker.get_statistics()
            >>> print(stats["summary"]["total_skills_tracked"])
            5
            >>> print(stats["summary"]["overall_success_rate"])
            0.94
        """
        # Calculate success rates for skills
        skill_stats = {}
        for skill_id, data in self._data["skill_usage"].items():
            total = data["total_uses"]
            skill_stats[skill_id] = {
                **data,
                "success_rate": data["successes"] / total if total > 0 else 0.0
            }

        # Calculate overall statistics
        total_uses = sum(s["total_uses"] for s in self._data["skill_usage"].values())
        total_successes = sum(s["successes"] for s in self._data["skill_usage"].values())

        # Get top combinations
        top_combinations = sorted(
            self._data["combinations"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]

        # Get top patterns
        top_patterns = sorted(
            self._data["patterns"].items(),
            key=lambda x: x[1]["frequency"],
            reverse=True
        )[:10]

        return {
            "skill_usage": skill_stats,
            "combinations": dict(top_combinations),
            "patterns": dict(top_patterns),
            "summary": {
                "total_skills_tracked": len(self._data["skill_usage"]),
                "total_uses": total_uses,
                "total_successes": total_successes,
                "total_failures": total_uses - total_successes,
                "overall_success_rate": (
                    total_successes / total_uses if total_uses > 0 else 0.0
                ),
                "total_combinations": len(self._data["combinations"]),
                "total_patterns": len(self._data["patterns"]),
                "total_events": self._data["metadata"]["total_events"],
                "last_updated": self._data["metadata"]["last_updated"]
            }
        }

    def analyze_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze usage trends over time.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary containing:
            - daily_usage: Usage counts per day
            - trending_skills: Skills with increasing usage
            - declining_skills: Skills with decreasing usage
            - recent_patterns: Recently discovered patterns

        Example:
            >>> trends = tracker.analyze_trends(days=7)
            >>> print(trends["trending_skills"])
            ["nextjs-fullstack", "supabase-integration"]
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat() + "Z"

        # Filter recent events
        recent_events = [
            e for e in self._data["events"]
            if e["timestamp"] >= cutoff_str
        ]

        # Analyze daily usage
        daily_usage = defaultdict(int)
        for event in recent_events:
            if event["type"] == "skill_used":
                date = event["timestamp"][:10]  # YYYY-MM-DD
                daily_usage[date] += 1

        # Find trending skills (used in last week vs previous week)
        week_ago = datetime.utcnow() - timedelta(days=7)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)

        week_ago_str = week_ago.isoformat() + "Z"
        two_weeks_ago_str = two_weeks_ago.isoformat() + "Z"

        recent_week_usage = defaultdict(int)
        previous_week_usage = defaultdict(int)

        for event in recent_events:
            if event["type"] == "skill_used":
                skills = event["data"].get("skills", [])
                timestamp = event["timestamp"]

                for skill in skills:
                    if timestamp >= week_ago_str:
                        recent_week_usage[skill] += 1
                    elif timestamp >= two_weeks_ago_str:
                        previous_week_usage[skill] += 1

        # Calculate trends
        trending_skills = []
        declining_skills = []

        all_skills = set(recent_week_usage.keys()) | set(previous_week_usage.keys())
        for skill in all_skills:
            recent = recent_week_usage[skill]
            previous = previous_week_usage[skill]

            if previous > 0:
                change_ratio = (recent - previous) / previous
                if change_ratio > 0.2:  # 20% increase
                    trending_skills.append((skill, change_ratio))
                elif change_ratio < -0.2:  # 20% decrease
                    declining_skills.append((skill, change_ratio))

        # Sort by change ratio
        trending_skills.sort(key=lambda x: x[1], reverse=True)
        declining_skills.sort(key=lambda x: x[1])

        # Find recent patterns
        recent_patterns = {
            k: v for k, v in self._data["patterns"].items()
            if v["last_seen"] >= cutoff_str
        }

        return {
            "daily_usage": dict(sorted(daily_usage.items())),
            "trending_skills": [s[0] for s in trending_skills[:5]],
            "declining_skills": [s[0] for s in declining_skills[:5]],
            "trending_details": dict(trending_skills[:5]),
            "declining_details": dict(declining_skills[:5]),
            "recent_patterns": recent_patterns,
            "total_recent_events": len(recent_events),
            "analysis_period_days": days
        }

    def get_skill_recommendations(
        self,
        context_skills: List[str],
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get skill recommendations based on context.

        Args:
            context_skills: Skills currently being used
            limit: Maximum number of recommendations

        Returns:
            List of (skill_id, confidence) tuples

        Example:
            >>> recs = tracker.get_skill_recommendations(["nextjs-fullstack"])
            >>> print(recs)
            [("supabase-integration", 0.89), ("shadcn-ui", 0.76)]
        """
        if not context_skills:
            return []

        recommendations = defaultdict(float)

        # Analyze common_with relationships
        for skill in context_skills:
            if skill in self._data["skill_usage"]:
                skill_data = self._data["skill_usage"][skill]
                for related_skill in skill_data.get("common_with", []):
                    if related_skill not in context_skills:
                        recommendations[related_skill] += 0.5

        # Analyze successful combinations
        for combo_key, combo_data in self._data["combinations"].items():
            combo_skills = combo_key.split("+")

            # Check if any context skills are in this combination
            overlap = set(context_skills) & set(combo_skills)
            if overlap and combo_data["success_rate"] > 0.7:
                # Recommend the other skills in this combination
                for skill in combo_skills:
                    if skill not in context_skills:
                        recommendations[skill] += (
                            combo_data["success_rate"] * 0.6
                        )

        # Sort by confidence and return top N
        sorted_recs = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_recs[:limit]

    def clear_all_data(self) -> None:
        """
        Clear all tracked data (privacy control).

        This removes all usage analytics but preserves the file structure.
        User must explicitly call this method.
        """
        self._data = {
            "skill_usage": {},
            "combinations": {},
            "patterns": {},
            "events": [],
            "metadata": {
                "created_at": self._timestamp(),
                "last_updated": self._timestamp(),
                "total_events": 0,
                "cleared_at": self._timestamp()
            }
        }
        self._save_data()

    def export_data(self) -> Dict[str, Any]:
        """
        Export all tracked data for user review.

        Returns:
            Complete analytics data structure

        Example:
            >>> data = tracker.export_data()
            >>> print(json.dumps(data, indent=2))
        """
        return self._data.copy()

    def get_skill_insights(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed insights for a specific skill.

        Args:
            skill_id: Skill identifier

        Returns:
            Insights dictionary or None if skill not found

        Example:
            >>> insights = tracker.get_skill_insights("nextjs-fullstack")
            >>> print(insights["performance_rating"])
            "excellent"
        """
        if skill_id not in self._data["skill_usage"]:
            return None

        data = self._data["skill_usage"][skill_id]
        success_rate = data["successes"] / data["total_uses"]

        # Determine performance rating
        if success_rate >= 0.9:
            rating = "excellent"
        elif success_rate >= 0.75:
            rating = "good"
        elif success_rate >= 0.6:
            rating = "fair"
        else:
            rating = "needs_improvement"

        return {
            **data,
            "success_rate": success_rate,
            "performance_rating": rating,
            "total_uses": data["total_uses"],
            "recommendation": self._get_skill_recommendation(skill_id, success_rate)
        }

    def _get_skill_recommendation(self, skill_id: str, success_rate: float) -> str:
        """Generate recommendation text for a skill."""
        if success_rate >= 0.9:
            return f"{skill_id} performs excellently. Continue using it."
        elif success_rate >= 0.75:
            return f"{skill_id} performs well. Consider optimization."
        elif success_rate >= 0.6:
            return f"{skill_id} has moderate success. Review and improve."
        else:
            return f"{skill_id} needs improvement. Consider revision."

    # Aliases for backward compatibility
    def record_usage(
        self,
        skills: Optional[List[str]] = None,
        success: bool = True,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        skill_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Alias for track_usage() method - for backward compatibility.
        Supports both new and legacy signatures.

        Args:
            skills: List of skill identifiers (or use skill_name for single skill)
            success: Whether the task was successful
            duration: Duration in seconds (defaults to 1.0 if not provided)
            metadata: Optional additional metadata
            skill_name: Legacy param - single skill name
            context: Legacy param - equivalent to metadata
        """
        # Handle legacy signature: record_usage(skill_name="x", success=True, context={...})
        if skill_name is not None:
            skills = [skill_name]

        if skills is None:
            raise ValueError("Must provide either 'skills' or 'skill_name'")

        if context is not None and metadata is None:
            metadata = context

        if duration is None:
            duration = 1.0  # Default duration

        return self.track_usage(skills, success, duration, metadata)

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Alias for get_statistics() - for backward compatibility.

        Returns:
            Statistics dictionary
        """
        return self.get_statistics()

    # Alias for backward compatibility
    def record_skill_combination(
        self,
        skills: List[str],
        success: bool = True,
        duration: Optional[float] = None
    ) -> None:
        """
        Alias for record_combination() method - for backward compatibility.

        Args:
            skills: List of skill identifiers used together
            success: Whether the combination was successful (default: True)
            duration: Optional duration in seconds
        """
        return self.record_combination(skills, success, duration)

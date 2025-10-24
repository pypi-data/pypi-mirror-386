"""
Learning Pipeline - Orchestrates pattern learning and application

This module provides the LearningPipeline class for:
- Running learning cycles automatically or on-demand
- Collecting usage data and detecting patterns
- Applying high-confidence patterns to skills
- Notifying users of learned patterns and changes
- Managing opt-out and rollback functionality

Safety-focused: Only applies patterns with >0.8 confidence, always creates backups.
"""

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

from ..generators.config import Config
from .pattern_detector import PatternDetector, DetectedPattern
from .usage_tracker import UsageTracker


@dataclass
class Notification:
    """Notification about learned patterns and changes"""
    notification_id: str
    notification_type: str          # "pattern_learned", "skill_updated", "optimization"
    timestamp: datetime
    pattern: Dict[str, Any]         # Pattern details
    applied_to: List[str]           # Affected skills
    action: str                     # "skill_updated", "pattern_detected", etc.
    user_action: Optional[str] = None  # "accepted", "rejected", "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class LearningState:
    """State of the learning system"""
    last_cycle: Optional[datetime] = None
    total_cycles: int = 0
    patterns_detected: int = 0
    patterns_applied: int = 0
    skills_updated: int = 0
    learning_enabled: bool = True
    auto_apply_enabled: bool = True
    min_confidence: float = 0.8
    cycle_frequency: int = 10  # Run after N uses

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        result = asdict(self)
        if self.last_cycle:
            result['last_cycle'] = self.last_cycle.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningState':
        """Create state from dictionary"""
        data = data.copy()
        if data.get('last_cycle'):
            data['last_cycle'] = datetime.fromisoformat(data['last_cycle'])
        return cls(**data)


class LearningPipeline:
    """
    Orchestrates the pattern learning and application process.

    The learning pipeline:
    1. Monitors usage and triggers learning cycles
    2. Collects and analyzes usage data
    3. Detects patterns with confidence scoring
    4. Applies high-confidence patterns to skills
    5. Notifies users of changes
    6. Manages rollbacks and opt-outs

    Example:
        >>> pipeline = LearningPipeline()
        >>> results = pipeline.run_learning_cycle()
        >>> print(f"Patterns detected: {results['patterns_detected']}")
        >>> notifications = pipeline.get_notifications()
    """

    # Safety thresholds
    MIN_CONFIDENCE = 0.8
    MIN_FREQUENCY = 3
    BACKUP_RETENTION_DAYS = 30

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the learning pipeline.

        Args:
            config: Optional Config instance (creates new if not provided)
        """
        self.config = config or Config()
        self.pattern_detector = PatternDetector()
        self.usage_tracker = UsageTracker()
        self.state = self._load_state()
        self.notifications: List[Notification] = self._load_notifications()

    def _load_state(self) -> LearningState:
        """Load learning state from disk"""
        state_path = Config.DATA_DIR / "learning_state.json"
        try:
            if state_path.exists():
                with open(state_path, 'r') as f:
                    data = json.load(f)
                    return LearningState.from_dict(data)
        except Exception as e:
            print(f"Warning: Could not load learning state: {e}")

        return LearningState()

    def _save_state(self) -> None:
        """Save learning state to disk"""
        state_path = Config.DATA_DIR / "learning_state.json"
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(state_path, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving learning state: {e}")

    def _load_notifications(self) -> List[Notification]:
        """Load notifications from disk"""
        notif_path = Config.DATA_DIR / "notifications.json"
        try:
            if notif_path.exists():
                with open(notif_path, 'r') as f:
                    data = json.load(f)
                    return [Notification.from_dict(n) for n in data]
        except Exception as e:
            print(f"Warning: Could not load notifications: {e}")

        return []

    def _save_notifications(self) -> None:
        """Save notifications to disk"""
        notif_path = Config.DATA_DIR / "notifications.json"
        try:
            notif_path.parent.mkdir(parents=True, exist_ok=True)
            with open(notif_path, 'w') as f:
                json.dump([n.to_dict() for n in self.notifications], f, indent=2)
        except Exception as e:
            print(f"Error saving notifications: {e}")

    def should_run_cycle(self) -> bool:
        """
        Determine if a learning cycle should run.

        Returns:
            True if cycle should run based on usage count
        """
        if not self.state.learning_enabled:
            return False

        stats = self.usage_tracker.get_statistics()
        total_events = stats.get("metadata", {}).get("total_events", 0)

        # Run cycle every N uses
        if self.state.last_cycle is None:
            return total_events >= self.state.cycle_frequency

        # Check if we've had enough new events since last cycle
        last_cycle_events = self.state.total_cycles * self.state.cycle_frequency
        return total_events >= last_cycle_events + self.state.cycle_frequency

    def run_learning_cycle(self, force: bool = False) -> Dict[str, Any]:
        """
        Run a complete learning cycle.

        Steps:
        1. Collect usage data
        2. Run pattern detection
        3. Validate patterns
        4. Check confidence thresholds
        5. Apply high-confidence patterns (if enabled)
        6. Update skills
        7. Notify user of changes
        8. Save state

        Args:
            force: Force cycle to run even if conditions not met

        Returns:
            Dictionary with cycle results
        """
        if not force and not self.should_run_cycle():
            return {
                "success": False,
                "reason": "Cycle conditions not met",
                "patterns_detected": 0,
                "patterns_applied": 0
            }

        results = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "patterns_detected": 0,
            "patterns_applied": 0,
            "skills_updated": [],
            "notifications": []
        }

        try:
            # Step 1-2: Collect data and detect patterns
            patterns = self.collect_and_analyze()
            results["patterns_detected"] = len(patterns)

            # Step 3-4: Validate and filter patterns
            valid_patterns = self.validate_patterns(patterns)

            # Step 5-6: Apply patterns if enabled
            if self.state.auto_apply_enabled:
                applied = self.apply_patterns(valid_patterns)
                results["patterns_applied"] = applied["count"]
                results["skills_updated"] = applied["skills_updated"]

            # Step 7: Notify user
            for pattern in valid_patterns:
                notification = self.notify_user(pattern, results["skills_updated"])
                results["notifications"].append(notification.to_dict())

            # Step 8: Save state
            self.state.last_cycle = datetime.now()
            self.state.total_cycles += 1
            self.state.patterns_detected += len(patterns)
            self.state.patterns_applied += results["patterns_applied"]
            self.state.skills_updated += len(results["skills_updated"])
            self._save_state()

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            print(f"Error in learning cycle: {e}")

        return results

    def collect_and_analyze(self) -> List[DetectedPattern]:
        """
        Collect usage data and run pattern detection.

        Returns:
            List of detected patterns
        """
        # Get usage statistics
        stats = self.usage_tracker.get_statistics()

        # Run pattern detection
        patterns = self.pattern_detector.detect_all_patterns(
            skill_usage=stats.get("skill_usage", {}),
            combinations=stats.get("combinations", {}),
            patterns=stats.get("patterns", {})
        )

        return patterns

    def validate_patterns(self, patterns: List[DetectedPattern]) -> List[DetectedPattern]:
        """
        Validate patterns against safety thresholds.

        Args:
            patterns: List of detected patterns

        Returns:
            List of valid patterns that meet safety criteria
        """
        valid = []

        for pattern in patterns:
            # Check confidence threshold
            if pattern.confidence < self.state.min_confidence:
                continue

            # Check minimum frequency
            if pattern.frequency < self.MIN_FREQUENCY:
                continue

            # Pattern is valid
            valid.append(pattern)

        return valid

    def apply_patterns(self, patterns: List[DetectedPattern]) -> Dict[str, Any]:
        """
        Apply validated patterns to skills.

        Args:
            patterns: List of patterns to apply

        Returns:
            Dictionary with application results
        """
        results = {
            "count": 0,
            "skills_updated": [],
            "errors": []
        }

        for pattern in patterns:
            try:
                # Determine affected skills
                affected_skills = self._determine_affected_skills(pattern)

                # Apply pattern to each skill
                for skill_name in affected_skills:
                    try:
                        self._apply_pattern_to_skill(pattern, skill_name)
                        if skill_name not in results["skills_updated"]:
                            results["skills_updated"].append(skill_name)
                        results["count"] += 1
                    except Exception as e:
                        results["errors"].append({
                            "skill": skill_name,
                            "pattern": pattern.pattern_id,
                            "error": str(e)
                        })

            except Exception as e:
                results["errors"].append({
                    "pattern": pattern.pattern_id,
                    "error": str(e)
                })

        return results

    def _determine_affected_skills(self, pattern: DetectedPattern) -> List[str]:
        """
        Determine which skills should be updated based on pattern.

        Args:
            pattern: Pattern to analyze

        Returns:
            List of skill names to update
        """
        affected = []

        if pattern.pattern_type == "combination":
            # Combination patterns affect the involved skills
            affected = pattern.data.get("skills", [])

        elif pattern.pattern_type == "style":
            # Style patterns affect all skills in the same domain
            # For now, return skills from user profile
            profile = self.config.load_user_profile()
            tech_stack = profile.get("tech_stack", {})
            affected = list(tech_stack.get("frameworks", {}).keys())

        elif pattern.pattern_type == "workflow":
            # Workflow patterns affect all skills
            profile = self.config.load_user_profile()
            tech_stack = profile.get("tech_stack", {})
            affected = list(tech_stack.get("frameworks", {}).keys())

        return affected

    def _apply_pattern_to_skill(self, pattern: DetectedPattern, skill_name: str) -> None:
        """
        Apply a pattern to a specific skill file.

        Args:
            pattern: Pattern to apply
            skill_name: Name of skill to update
        """
        # Find skill file
        skills_dir = Path.home() / ".claude" / "skills"
        skill_file = skills_dir / f"{skill_name}.md"

        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_file}")

        # Create backup
        self._backup_skill(skill_file)

        try:
            # Read current skill content
            with open(skill_file, 'r') as f:
                content = f.read()

            # Parse YAML frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2]
            else:
                frontmatter = {}
                body = content

            # Update frontmatter with pattern
            if 'learned_patterns' not in frontmatter:
                frontmatter['learned_patterns'] = []

            pattern_ref = {
                'pattern_id': pattern.pattern_id,
                'type': pattern.pattern_type,
                'confidence': pattern.confidence,
                'applied_at': datetime.now().isoformat()
            }

            frontmatter['learned_patterns'].append(pattern_ref)

            # Add pattern instructions to body
            pattern_section = self._generate_pattern_section(pattern)
            body += f"\n\n{pattern_section}"

            # Write updated content
            updated_content = f"---\n{yaml.dump(frontmatter)}---{body}"
            with open(skill_file, 'w') as f:
                f.write(updated_content)

            # Validate updated file
            self._validate_skill_file(skill_file)

        except Exception as e:
            # Rollback on error
            self._rollback_skill(skill_file)
            raise Exception(f"Failed to apply pattern: {e}")

    def _generate_pattern_section(self, pattern: DetectedPattern) -> str:
        """Generate markdown section for pattern"""
        section = f"\n## Learned Pattern: {pattern.description}\n\n"
        section += f"**Type**: {pattern.pattern_type}\n"
        section += f"**Confidence**: {pattern.confidence:.2%}\n"
        section += f"**Based on**: {pattern.frequency} observations\n\n"

        if pattern.pattern_type == "combination":
            section += "**Related Skills**: " + ", ".join(pattern.data.get("skills", [])) + "\n"

        elif pattern.pattern_type == "style":
            section += f"**Style Type**: {pattern.data.get('style_type', 'N/A')}\n"
            examples = pattern.data.get('examples', [])
            if examples:
                section += "\n**Examples**:\n"
                for example in examples[:3]:  # Show max 3 examples
                    section += f"- {example}\n"

        return section

    def _backup_skill(self, skill_file: Path) -> None:
        """Create backup of skill file"""
        backup_dir = Config.DATA_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{skill_file.stem}_{timestamp}.md"

        shutil.copy2(skill_file, backup_file)

        # Clean old backups
        self._cleanup_old_backups(backup_dir)

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.BACKUP_RETENTION_DAYS)

        for backup in backup_dir.glob("*.md"):
            if backup.stat().st_mtime < cutoff_date.timestamp():
                backup.unlink()

    def _rollback_skill(self, skill_file: Path) -> None:
        """Rollback skill to most recent backup"""
        backup_dir = Config.DATA_DIR / "backups"

        # Find most recent backup
        backups = sorted(
            backup_dir.glob(f"{skill_file.stem}_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if backups:
            shutil.copy2(backups[0], skill_file)
        else:
            raise Exception("No backup found for rollback")

    def _validate_skill_file(self, skill_file: Path) -> None:
        """Validate skill file after modification"""
        with open(skill_file, 'r') as f:
            content = f.read()

        # Basic validation: check YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml.safe_load(parts[1])  # Will raise if invalid

    def notify_user(self, pattern: DetectedPattern, applied_to: List[str]) -> Notification:
        """
        Create user notification about learned pattern.

        Args:
            pattern: Pattern that was detected/applied
            applied_to: List of skills that were updated

        Returns:
            Notification object
        """
        notification = Notification(
            notification_id=f"notif_{datetime.now().timestamp()}",
            notification_type="pattern_learned",
            timestamp=datetime.now(),
            pattern={
                "name": pattern.pattern_id,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "based_on": pattern.frequency
            },
            applied_to=applied_to,
            action="skill_updated" if applied_to else "pattern_detected"
        )

        self.notifications.append(notification)
        self._save_notifications()

        return notification

    def get_notifications(self, unread_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get user notifications.

        Args:
            unread_only: Only return notifications without user action

        Returns:
            List of notification dictionaries
        """
        notifications = self.notifications

        if unread_only:
            notifications = [n for n in notifications if n.user_action is None]

        return [n.to_dict() for n in notifications]

    def respond_to_notification(self, notification_id: str, action: str) -> bool:
        """
        Record user response to notification.

        Args:
            notification_id: ID of notification
            action: User action ("accept", "reject")

        Returns:
            True if successful
        """
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.user_action = action
                self._save_notifications()

                # Handle rejection by rolling back
                if action == "reject":
                    self._handle_rejection(notification)

                return True

        return False

    def _handle_rejection(self, notification: Notification) -> None:
        """Handle user rejection of pattern"""
        # Rollback affected skills
        for skill_name in notification.applied_to:
            skills_dir = Path.home() / ".claude" / "skills"
            skill_file = skills_dir / f"{skill_name}.md"

            try:
                self._rollback_skill(skill_file)
            except Exception as e:
                print(f"Error rolling back {skill_name}: {e}")

    def disable_learning(self) -> None:
        """Disable automatic learning"""
        self.state.learning_enabled = False
        self._save_state()

    def enable_learning(self) -> None:
        """Enable automatic learning"""
        self.state.learning_enabled = True
        self._save_state()

    def get_state(self) -> Dict[str, Any]:
        """Get current learning state"""
        return self.state.to_dict()

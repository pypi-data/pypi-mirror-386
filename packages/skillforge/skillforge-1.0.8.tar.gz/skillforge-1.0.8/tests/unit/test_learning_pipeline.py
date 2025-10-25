"""
Unit tests for LearningPipeline class

Tests learning pipeline including:
- Running learning cycles
- Collecting and analyzing data
- Validating patterns
- Applying patterns to skills
- Creating notifications
- Handling user responses
- Managing opt-out and rollback
"""

import pytest
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from skillforge.analyzers.learning_pipeline import (
    LearningPipeline,
    Notification,
    LearningState
)
from skillforge.analyzers.pattern_detector import (
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
    """
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)

    # Override Config class variables
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
    Config.ensure_directories()

    # Create skills directory
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    yield home


@pytest.fixture
def pipeline(temp_home):
    """Create LearningPipeline instance with clean state"""
    config = Config()
    return LearningPipeline(config=config)


@pytest.fixture
def sample_pattern():
    """Create sample detected pattern"""
    return CombinationPattern(
        pattern_id="combo_001",
        pattern_type="combination",
        description="NextJS + Supabase combination",
        confidence=0.92,
        frequency=15,
        success_rate=0.95,
        first_seen=datetime.now() - timedelta(days=30),
        last_seen=datetime.now(),
        skills=["nextjs-fullstack", "supabase-integration"]
    )


@pytest.fixture
def sample_style_pattern():
    """Create sample style pattern"""
    return StylePattern(
        pattern_id="style_001",
        pattern_type="style",
        description="Always use camelCase naming",
        confidence=0.88,
        frequency=20,
        success_rate=0.93,
        first_seen=datetime.now() - timedelta(days=20),
        last_seen=datetime.now(),
        style_type="naming",
        examples=["myVariable", "getUserData", "handleClick"]
    )


@pytest.fixture
def sample_skill_file(temp_home):
    """Create sample skill file for testing"""
    skills_dir = Path.home() / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    skill_content = """---
name: nextjs-fullstack
description: NextJS fullstack development
version: 1.0.0
learned_patterns: []
---

# NextJS Fullstack Development

## Core Patterns

Use NextJS for fullstack development.
"""

    skill_file = skills_dir / "nextjs-fullstack.md"
    with open(skill_file, 'w') as f:
        f.write(skill_content)

    yield skill_file

    # Cleanup
    if skill_file.exists():
        skill_file.unlink()


# Test Notification dataclass

def test_notification_creation():
    """Test creating notification"""
    notif = Notification(
        notification_id="notif_001",
        notification_type="pattern_learned",
        timestamp=datetime.now(),
        pattern={"name": "test", "confidence": 0.9},
        applied_to=["skill1"],
        action="skill_updated"
    )

    assert notif.notification_id == "notif_001"
    assert notif.notification_type == "pattern_learned"
    assert notif.pattern["confidence"] == 0.9
    assert notif.applied_to == ["skill1"]


def test_notification_to_dict():
    """Test notification serialization"""
    timestamp = datetime.now()
    notif = Notification(
        notification_id="notif_001",
        notification_type="pattern_learned",
        timestamp=timestamp,
        pattern={"name": "test"},
        applied_to=["skill1"],
        action="skill_updated"
    )

    data = notif.to_dict()
    assert data["notification_id"] == "notif_001"
    assert data["timestamp"] == timestamp.isoformat()
    assert isinstance(data["timestamp"], str)


def test_notification_from_dict():
    """Test notification deserialization"""
    timestamp = datetime.now()
    data = {
        "notification_id": "notif_001",
        "notification_type": "pattern_learned",
        "timestamp": timestamp.isoformat(),
        "pattern": {"name": "test"},
        "applied_to": ["skill1"],
        "action": "skill_updated",
        "user_action": None
    }

    notif = Notification.from_dict(data)
    assert notif.notification_id == "notif_001"
    assert isinstance(notif.timestamp, datetime)


# Test LearningState dataclass

def test_learning_state_defaults():
    """Test learning state default values"""
    state = LearningState()

    assert state.last_cycle is None
    assert state.total_cycles == 0
    assert state.learning_enabled is True
    assert state.auto_apply_enabled is True
    assert state.min_confidence == 0.8
    assert state.cycle_frequency == 10


def test_learning_state_to_dict():
    """Test learning state serialization"""
    timestamp = datetime.now()
    state = LearningState(
        last_cycle=timestamp,
        total_cycles=5,
        patterns_detected=10
    )

    data = state.to_dict()
    assert data["total_cycles"] == 5
    assert data["patterns_detected"] == 10
    assert data["last_cycle"] == timestamp.isoformat()


def test_learning_state_from_dict():
    """Test learning state deserialization"""
    timestamp = datetime.now()
    data = {
        "last_cycle": timestamp.isoformat(),
        "total_cycles": 5,
        "patterns_detected": 10,
        "patterns_applied": 3,
        "skills_updated": 2,
        "learning_enabled": True,
        "auto_apply_enabled": True,
        "min_confidence": 0.8,
        "cycle_frequency": 10
    }

    state = LearningState.from_dict(data)
    assert state.total_cycles == 5
    assert isinstance(state.last_cycle, datetime)


# Test LearningPipeline initialization

def test_pipeline_initialization(pipeline):
    """Test pipeline initialization"""
    assert pipeline.config is not None
    assert pipeline.pattern_detector is not None
    assert pipeline.usage_tracker is not None
    assert isinstance(pipeline.state, LearningState)
    assert isinstance(pipeline.notifications, list)


def test_pipeline_load_state(temp_home):
    """Test loading existing state"""
    # Create state file
    state_path = Config.DATA_DIR / "learning_state.json"
    state_data = {
        "last_cycle": datetime.now().isoformat(),
        "total_cycles": 3,
        "patterns_detected": 5,
        "patterns_applied": 2,
        "skills_updated": 1,
        "learning_enabled": True,
        "auto_apply_enabled": False,
        "min_confidence": 0.85,
        "cycle_frequency": 15
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        json.dump(state_data, f)

    # Create pipeline
    config = Config()
    pipeline = LearningPipeline(config=config)

    # Verify state loaded
    assert pipeline.state.total_cycles == 3
    assert pipeline.state.auto_apply_enabled is False
    assert pipeline.state.min_confidence == 0.85


def test_pipeline_save_state(pipeline, temp_home):
    """Test saving state"""
    pipeline.state.total_cycles = 5
    pipeline.state.patterns_detected = 10
    pipeline._save_state()

    # Verify file created
    state_path = Config.DATA_DIR / "learning_state.json"
    assert state_path.exists()

    # Verify content
    with open(state_path, 'r') as f:
        data = json.load(f)

    assert data["total_cycles"] == 5
    assert data["patterns_detected"] == 10


# Test learning cycle conditions

def test_should_run_cycle_disabled(pipeline):
    """Test should_run_cycle when learning disabled"""
    pipeline.state.learning_enabled = False
    assert pipeline.should_run_cycle() is False


def test_should_run_cycle_first_time(pipeline):
    """Test should_run_cycle on first run"""
    # Mock usage tracker
    pipeline.usage_tracker.get_statistics = Mock(return_value={
        "metadata": {"total_events": 10}
    })

    assert pipeline.should_run_cycle() is True


def test_should_run_cycle_not_enough_events(pipeline):
    """Test should_run_cycle with insufficient events"""
    pipeline.state.last_cycle = datetime.now()
    pipeline.state.total_cycles = 1

    # Mock usage tracker
    pipeline.usage_tracker.get_statistics = Mock(return_value={
        "metadata": {"total_events": 15}
    })

    assert pipeline.should_run_cycle() is False


def test_should_run_cycle_enough_events(pipeline):
    """Test should_run_cycle with sufficient events"""
    pipeline.state.last_cycle = datetime.now()
    pipeline.state.total_cycles = 1

    # Mock usage tracker
    pipeline.usage_tracker.get_statistics = Mock(return_value={
        "metadata": {"total_events": 25}
    })

    assert pipeline.should_run_cycle() is True


# Test collect and analyze

def test_collect_and_analyze(pipeline, sample_pattern):
    """Test data collection and analysis"""
    # Mock dependencies
    pipeline.usage_tracker.get_statistics = Mock(return_value={
        "skill_usage": {"skill1": {"count": 10}},
        "combinations": {},
        "patterns": {}
    })

    pipeline.pattern_detector.detect_all_patterns = Mock(
        return_value=[sample_pattern]
    )

    patterns = pipeline.collect_and_analyze()

    assert len(patterns) == 1
    assert patterns[0].pattern_id == "combo_001"


# Test pattern validation

def test_validate_patterns_high_confidence(pipeline, sample_pattern):
    """Test validating patterns with high confidence"""
    sample_pattern.confidence = 0.92
    sample_pattern.frequency = 10

    valid = pipeline.validate_patterns([sample_pattern])

    assert len(valid) == 1
    assert valid[0] == sample_pattern


def test_validate_patterns_low_confidence(pipeline, sample_pattern):
    """Test rejecting patterns with low confidence"""
    sample_pattern.confidence = 0.7  # Below threshold

    valid = pipeline.validate_patterns([sample_pattern])

    assert len(valid) == 0


def test_validate_patterns_low_frequency(pipeline, sample_pattern):
    """Test rejecting patterns with low frequency"""
    sample_pattern.frequency = 2  # Below threshold

    valid = pipeline.validate_patterns([sample_pattern])

    assert len(valid) == 0


def test_validate_patterns_mixed(pipeline, sample_pattern, sample_style_pattern):
    """Test validating mix of patterns"""
    sample_pattern.confidence = 0.92
    sample_style_pattern.confidence = 0.7  # Too low

    valid = pipeline.validate_patterns([sample_pattern, sample_style_pattern])

    assert len(valid) == 1
    assert valid[0].pattern_id == "combo_001"


# Test determine affected skills

def test_determine_affected_skills_combination(pipeline, sample_pattern):
    """Test determining affected skills for combination pattern"""
    affected = pipeline._determine_affected_skills(sample_pattern)

    assert "nextjs-fullstack" in affected
    assert "supabase-integration" in affected


def test_determine_affected_skills_style(pipeline, sample_style_pattern, temp_home):
    """Test determining affected skills for style pattern"""
    # Create user profile
    profile = {
        "tech_stack": {
            "frameworks": {
                "nextjs": {"name": "Next.js"},
                "react": {"name": "React"}
            }
        }
    }

    profile_path = Config.DATA_DIR / "user_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, 'w') as f:
        json.dump(profile, f)

    affected = pipeline._determine_affected_skills(sample_style_pattern)

    assert "nextjs" in affected or "react" in affected


# Test pattern application

def test_apply_patterns_success(pipeline, sample_pattern, sample_skill_file):
    """Test applying patterns successfully"""
    # Mock affected skills
    pipeline._determine_affected_skills = Mock(return_value=["nextjs-fullstack"])

    results = pipeline.apply_patterns([sample_pattern])

    assert results["count"] == 1
    assert "nextjs-fullstack" in results["skills_updated"]
    assert len(results["errors"]) == 0


def test_apply_patterns_skill_not_found(pipeline, sample_pattern):
    """Test applying pattern to non-existent skill"""
    # Mock affected skills with non-existent skill
    pipeline._determine_affected_skills = Mock(return_value=["nonexistent-skill"])

    results = pipeline.apply_patterns([sample_pattern])

    assert results["count"] == 0
    assert len(results["errors"]) > 0


def test_apply_pattern_to_skill(pipeline, sample_pattern, sample_skill_file):
    """Test applying pattern to specific skill"""
    # Apply pattern
    pipeline._apply_pattern_to_skill(sample_pattern, "nextjs-fullstack")

    # Verify backup created
    backup_dir = Config.DATA_DIR / "backups"
    assert backup_dir.exists()

    # Verify skill updated
    with open(sample_skill_file, 'r') as f:
        content = f.read()

    assert "combo_001" in content
    assert "Learned Pattern" in content


def test_apply_pattern_backup_created(pipeline, sample_pattern, sample_skill_file):
    """Test backup is created before applying pattern"""
    pipeline._apply_pattern_to_skill(sample_pattern, "nextjs-fullstack")

    backup_dir = Config.DATA_DIR / "backups"
    backups = list(backup_dir.glob("nextjs-fullstack_*.md"))

    assert len(backups) > 0


def test_generate_pattern_section_combination(pipeline, sample_pattern):
    """Test generating pattern section for combination"""
    section = pipeline._generate_pattern_section(sample_pattern)

    assert "NextJS + Supabase" in section
    assert "combination" in section
    assert "92.00%" in section
    assert "Related Skills" in section


def test_generate_pattern_section_style(pipeline, sample_style_pattern):
    """Test generating pattern section for style"""
    section = pipeline._generate_pattern_section(sample_style_pattern)

    assert "camelCase" in section
    assert "style" in section
    assert "naming" in section
    assert "Examples" in section


# Test notifications

def test_notify_user(pipeline, sample_pattern):
    """Test creating user notification"""
    notification = pipeline.notify_user(sample_pattern, ["skill1", "skill2"])

    assert notification.notification_type == "pattern_learned"
    assert notification.pattern["name"] == "combo_001"
    assert notification.pattern["confidence"] == 0.92
    assert "skill1" in notification.applied_to
    assert notification.action == "skill_updated"


def test_get_notifications_all(pipeline, sample_pattern):
    """Test getting all notifications"""
    pipeline.notify_user(sample_pattern, ["skill1"])
    pipeline.notify_user(sample_pattern, ["skill2"])

    notifications = pipeline.get_notifications(unread_only=False)

    assert len(notifications) == 2


def test_get_notifications_unread_only(pipeline, sample_pattern):
    """Test getting only unread notifications"""
    # Create notifications
    notif1 = pipeline.notify_user(sample_pattern, ["skill1"])
    notif2 = pipeline.notify_user(sample_pattern, ["skill2"])

    # Mark one as read
    pipeline.respond_to_notification(notif1.notification_id, "accept")

    # Get unread
    unread = pipeline.get_notifications(unread_only=True)

    assert len(unread) == 1
    assert unread[0]["notification_id"] == notif2.notification_id


def test_respond_to_notification_accept(pipeline, sample_pattern):
    """Test accepting notification"""
    notification = pipeline.notify_user(sample_pattern, ["skill1"])

    success = pipeline.respond_to_notification(notification.notification_id, "accept")

    assert success is True
    assert notification.user_action == "accept"


def test_respond_to_notification_reject(pipeline, sample_pattern, sample_skill_file):
    """Test rejecting notification triggers rollback"""
    # Apply pattern first
    pipeline._apply_pattern_to_skill(sample_pattern, "nextjs-fullstack")

    # Create notification
    notification = pipeline.notify_user(sample_pattern, ["nextjs-fullstack"])

    # Mock rollback
    pipeline._rollback_skill = Mock()

    # Reject
    pipeline.respond_to_notification(notification.notification_id, "reject")

    # Verify rollback called
    pipeline._rollback_skill.assert_called_once()


# Test backup and rollback

def test_backup_skill(pipeline, sample_skill_file):
    """Test creating skill backup"""
    pipeline._backup_skill(sample_skill_file)

    backup_dir = Config.DATA_DIR / "backups"
    backups = list(backup_dir.glob("nextjs-fullstack_*.md"))

    assert len(backups) > 0


def test_rollback_skill(pipeline, sample_skill_file):
    """Test rolling back skill"""
    # Create backup
    pipeline._backup_skill(sample_skill_file)

    # Modify skill
    with open(sample_skill_file, 'w') as f:
        f.write("Modified content")

    # Rollback
    pipeline._rollback_skill(sample_skill_file)

    # Verify restored
    with open(sample_skill_file, 'r') as f:
        content = f.read()

    assert "NextJS Fullstack Development" in content
    assert "Modified content" not in content


def test_cleanup_old_backups(pipeline, temp_home):
    """Test cleaning up old backups"""
    backup_dir = Config.DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Create old backup
    old_backup = backup_dir / "old_skill.md"
    old_backup.write_text("old")

    # Set modification time to 40 days ago
    old_time = (datetime.now() - timedelta(days=40)).timestamp()
    old_backup.touch()
    import os
    os.utime(old_backup, (old_time, old_time))

    # Create recent backup
    recent_backup = backup_dir / "recent_skill.md"
    recent_backup.write_text("recent")

    # Cleanup
    pipeline._cleanup_old_backups(backup_dir)

    # Verify old removed, recent kept
    assert not old_backup.exists()
    assert recent_backup.exists()


# Test full learning cycle

def test_run_learning_cycle_conditions_not_met(pipeline):
    """Test cycle doesn't run when conditions not met"""
    pipeline.usage_tracker.get_statistics = Mock(return_value={
        "metadata": {"total_events": 5}  # Not enough
    })

    results = pipeline.run_learning_cycle(force=False)

    assert results["success"] is False
    assert "conditions not met" in results["reason"].lower()


def test_run_learning_cycle_force(pipeline, sample_pattern):
    """Test forcing cycle to run"""
    # Mock dependencies
    pipeline.collect_and_analyze = Mock(return_value=[sample_pattern])
    pipeline.validate_patterns = Mock(return_value=[sample_pattern])
    pipeline.apply_patterns = Mock(return_value={
        "count": 1,
        "skills_updated": ["skill1"],
        "errors": []
    })

    results = pipeline.run_learning_cycle(force=True)

    assert results["success"] is True
    assert results["patterns_detected"] == 1
    assert results["patterns_applied"] == 1


def test_run_learning_cycle_auto_apply_disabled(pipeline, sample_pattern):
    """Test cycle with auto-apply disabled"""
    pipeline.state.auto_apply_enabled = False

    # Mock dependencies
    pipeline.collect_and_analyze = Mock(return_value=[sample_pattern])
    pipeline.validate_patterns = Mock(return_value=[sample_pattern])

    results = pipeline.run_learning_cycle(force=True)

    assert results["success"] is True
    assert results["patterns_detected"] == 1
    assert results["patterns_applied"] == 0  # Not applied


def test_run_learning_cycle_updates_state(pipeline, sample_pattern):
    """Test cycle updates state"""
    initial_cycles = pipeline.state.total_cycles

    # Mock dependencies
    pipeline.collect_and_analyze = Mock(return_value=[sample_pattern])
    pipeline.validate_patterns = Mock(return_value=[sample_pattern])
    pipeline.apply_patterns = Mock(return_value={
        "count": 1,
        "skills_updated": ["skill1"],
        "errors": []
    })

    pipeline.run_learning_cycle(force=True)

    assert pipeline.state.total_cycles == initial_cycles + 1
    assert pipeline.state.last_cycle is not None


# Test opt-out and control

def test_disable_learning(pipeline):
    """Test disabling learning"""
    pipeline.disable_learning()

    assert pipeline.state.learning_enabled is False


def test_enable_learning(pipeline):
    """Test enabling learning"""
    pipeline.state.learning_enabled = False
    pipeline.enable_learning()

    assert pipeline.state.learning_enabled is True


def test_get_state(pipeline):
    """Test getting learning state"""
    state = pipeline.get_state()

    assert "total_cycles" in state
    assert "learning_enabled" in state
    assert "auto_apply_enabled" in state
    assert isinstance(state, dict)


# Test error handling

def test_apply_pattern_invalid_yaml_rollback(pipeline, sample_pattern, sample_skill_file):
    """Test rollback on invalid YAML after pattern application"""
    # Create invalid skill file
    with open(sample_skill_file, 'w') as f:
        f.write("---\ninvalid: yaml: content\n---\nBody")

    # Create backup first
    pipeline._backup_skill(sample_skill_file)

    # This should raise and trigger rollback
    with pytest.raises(Exception):
        pipeline._apply_pattern_to_skill(sample_pattern, "nextjs-fullstack")


def test_validate_skill_file_valid(pipeline, sample_skill_file):
    """Test validating valid skill file"""
    # Should not raise
    pipeline._validate_skill_file(sample_skill_file)


def test_validate_skill_file_invalid_yaml(pipeline, temp_home):
    """Test validating invalid skill file"""
    invalid_file = Path.home() / ".claude" / "skills" / "invalid.md"
    with open(invalid_file, 'w') as f:
        f.write("---\ninvalid: yaml: content\n---\nBody")

    with pytest.raises(yaml.YAMLError):
        pipeline._validate_skill_file(invalid_file)

    invalid_file.unlink()

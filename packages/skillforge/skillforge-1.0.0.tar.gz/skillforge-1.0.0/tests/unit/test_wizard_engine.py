"""
Unit tests for WizardEngine class

Tests interactive wizard functionality including:
- Tech stack detection from project files
- Question validation and answering
- Profile building and structure
- Session save/load functionality
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from skillforge.generators.wizard_engine import WizardEngine


@pytest.fixture
def temp_project(tmp_path):
    """
    Create temporary project directory with various config files.

    Simulates a real project with package.json, requirements.txt, etc.
    for testing auto-detection functionality.
    """
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def wizard(temp_project):
    """Create WizardEngine instance with temp project directory"""
    return WizardEngine(current_dir=temp_project)


@pytest.fixture
def sample_package_json():
    """Sample package.json with common dependencies"""
    return {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "next": "^13.4.0",
            "@mui/material": "^5.13.0",
            "redux": "^4.2.0",
            "express": "^4.18.0"
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "eslint": "^8.0.0",
            "prettier": "^2.8.0",
            "jest": "^29.0.0"
        }
    }


class TestStackDetection:
    """Test technology stack auto-detection"""

    def test_detect_stack_empty_directory(self, wizard):
        """Test detection in directory with no config files"""
        detected = wizard.detect_stack()

        assert isinstance(detected, dict)
        assert len(detected) == 0

    def test_detect_stack_from_package_json(self, wizard, temp_project, sample_package_json):
        """Test detection from package.json dependencies"""
        package_json_path = temp_project / "package.json"
        package_json_path.write_text(json.dumps(sample_package_json))

        detected = wizard.detect_stack()

        # Should detect frontend framework
        assert "frontend_framework" in detected
        assert "React" in detected["frontend_framework"] or "Next.js" in detected["frontend_framework"]

        # Should detect UI library
        assert "ui_library" in detected
        assert "Material-UI (MUI)" in detected["ui_library"]

        # Should detect state management
        assert "state_management" in detected
        assert "Redux" in detected["state_management"]

        # Should detect backend framework
        assert "backend_framework" in detected
        assert "Express.js (Node)" in detected["backend_framework"]

    def test_detect_stack_from_requirements_txt(self, wizard, temp_project):
        """Test detection from Python requirements.txt"""
        requirements = """
django==4.2.0
fastapi==0.95.0
pytest==7.3.0
psycopg2-binary==2.9.6
redis==4.5.0
"""
        requirements_path = temp_project / "requirements.txt"
        requirements_path.write_text(requirements)

        detected = wizard.detect_stack()

        # Should detect backend frameworks
        assert "backend_framework" in detected
        detected_backends = detected["backend_framework"]
        assert "Django (Python)" in detected_backends or "FastAPI (Python)" in detected_backends

        # Should detect testing tools
        assert "testing_tools" in detected
        assert "pytest" in detected["testing_tools"]

        # Should detect databases
        assert "database" in detected
        assert "PostgreSQL" in detected["database"]

    def test_detect_stack_handles_invalid_json(self, wizard, temp_project):
        """Test that invalid JSON doesn't crash detection"""
        package_json_path = temp_project / "package.json"
        package_json_path.write_text("{ invalid json }")

        # Should not raise exception
        detected = wizard.detect_stack()
        assert isinstance(detected, dict)

    def test_detect_stack_multiple_files(self, wizard, temp_project, sample_package_json):
        """Test detection from multiple config files"""
        # Create package.json
        package_json_path = temp_project / "package.json"
        package_json_path.write_text(json.dumps(sample_package_json))

        # Create requirements.txt
        requirements_path = temp_project / "requirements.txt"
        requirements_path.write_text("fastapi==0.95.0\npytest==7.3.0")

        detected = wizard.detect_stack()

        # Should detect from both files
        assert "frontend_framework" in detected  # From package.json
        assert "testing_tools" in detected  # From both files
        # Could have both Jest and pytest
        assert len(detected["testing_tools"]) >= 1


class TestQuestionValidation:
    """Test question asking and answer validation"""

    def test_validate_answer_single_choice(self, wizard):
        """Test validation for single choice questions"""
        options = ["Option A", "Option B", "Option C"]

        # Valid input
        result = wizard.validate_answer("2", options, allow_multiple=False)
        assert result == "Option B"

        # Another valid input
        result = wizard.validate_answer("1", options, allow_multiple=False)
        assert result == "Option A"

    def test_validate_answer_multiple_choice(self, wizard):
        """Test validation for multiple choice questions"""
        options = ["Option A", "Option B", "Option C"]

        # Comma-separated
        result = wizard.validate_answer("1,3", options, allow_multiple=True)
        assert result == ["Option A", "Option C"]

        # Space-separated
        result = wizard.validate_answer("1 2 3", options, allow_multiple=True)
        assert result == ["Option A", "Option B", "Option C"]

    def test_validate_answer_out_of_range(self, wizard):
        """Test validation rejects out-of-range choices"""
        options = ["Option A", "Option B", "Option C"]

        with pytest.raises(ValueError):
            wizard.validate_answer("5", options, allow_multiple=False)

        with pytest.raises(ValueError):
            wizard.validate_answer("0", options, allow_multiple=False)

    def test_validate_answer_invalid_input(self, wizard):
        """Test validation rejects invalid input"""
        options = ["Option A", "Option B", "Option C"]

        with pytest.raises(ValueError, match="Invalid choice"):
            wizard.validate_answer("abc", options, allow_multiple=False)

        with pytest.raises(ValueError):
            wizard.validate_answer("1,abc,2", options, allow_multiple=True)


class TestProfileBuilding:
    """Test profile construction and structure"""

    def test_build_tech_stack(self, wizard):
        """Test tech stack section building from answers"""
        wizard.profile = {
            "frontend_framework": "React",
            "ui_library": ["Tailwind CSS", "Material-UI (MUI)"],
            "backend_framework": "Express.js (Node)",
            "database": ["PostgreSQL", "Redis"],
            "testing_tools": ["Jest", "Playwright"]
        }

        tech_stack = wizard._build_tech_stack()

        assert "frontend" in tech_stack
        assert tech_stack["frontend"] == "React"

        assert "ui" in tech_stack
        assert "Tailwind CSS" in tech_stack["ui"]

        assert "backend" in tech_stack
        assert tech_stack["backend"] == "Express.js (Node)"

        assert "database" in tech_stack
        assert "PostgreSQL" in tech_stack["database"]

    def test_build_preferences(self, wizard):
        """Test preferences section building"""
        wizard.profile = {
            "role": "Full-Stack Developer",
            "deployment_platform": ["Vercel", "AWS"],
            "code_style": ["TypeScript strict mode", "ESLint + Prettier"],
            "workflow_preferences": ["Git hooks (Husky)", "CI/CD pipelines"]
        }

        preferences = wizard._build_preferences()

        assert preferences["role"] == "Full-Stack Developer"
        assert "Vercel" in preferences["deployment"]
        assert "TypeScript strict mode" in preferences["code_style"]
        assert "Git hooks (Husky)" in preferences["workflow"]

    def test_build_conventions(self, wizard):
        """Test conventions section building from code style"""
        wizard.profile = {
            "code_style": [
                "TypeScript strict mode",
                "ESLint + Prettier",
                "Functional programming"
            ]
        }

        conventions = wizard._build_conventions()

        assert conventions["typescript"] is True
        assert conventions["linting"] is True
        assert conventions["formatting"] is True
        assert "functional" in conventions["paradigm"]

    def test_build_conventions_python(self, wizard):
        """Test conventions with Python-specific preferences"""
        wizard.profile = {
            "code_style": ["Black (Python)", "Object-oriented"]
        }

        conventions = wizard._build_conventions()

        assert conventions["formatting"] is True
        assert "oop" in conventions["paradigm"]


class TestSessionManagement:
    """Test save/load session functionality"""

    def test_save_session(self, wizard, tmp_path):
        """Test saving session state"""
        # Override Config paths for test
        from skillforge.generators.config import Config
        Config.DATA_DIR = tmp_path
        Config.ensure_directories()

        wizard.profile = {"role": "Full-Stack Developer"}
        wizard.detected_tech = {"frontend_framework": {"React"}}
        wizard.current_question_idx = 5

        wizard._save_session()

        session_path = Config.DATA_DIR / "wizard_session.json"
        assert session_path.exists()

        with open(session_path, 'r') as f:
            data = json.load(f)

        assert data["profile"]["role"] == "Full-Stack Developer"
        assert data["current_question_idx"] == 5
        assert "React" in data["detected_tech"]["frontend_framework"]

    def test_load_session(self, wizard, tmp_path):
        """Test loading saved session"""
        from skillforge.generators.config import Config
        Config.DATA_DIR = tmp_path
        Config.ensure_directories()

        # Create session file
        session_data = {
            "profile": {"role": "Backend Developer"},
            "detected_tech": {"database": ["PostgreSQL"]},
            "history": [{"question_id": "role", "answer": "Backend Developer"}],
            "current_question_idx": 3
        }

        session_path = Config.DATA_DIR / "wizard_session.json"
        with open(session_path, 'w') as f:
            json.dump(session_data, f)

        # Load session
        loaded = wizard._load_session()

        assert loaded is True
        assert wizard.profile["role"] == "Backend Developer"
        assert "PostgreSQL" in wizard.detected_tech["database"]
        assert wizard.current_question_idx == 3

    def test_load_session_nonexistent(self, wizard, tmp_path):
        """Test loading session when file doesn't exist"""
        from skillforge.generators.config import Config
        Config.DATA_DIR = tmp_path
        Config.ensure_directories()

        loaded = wizard._load_session()
        assert loaded is False

    def test_load_session_corrupted(self, wizard, tmp_path):
        """Test loading corrupted session file"""
        from skillforge.generators.config import Config
        Config.DATA_DIR = tmp_path
        Config.ensure_directories()

        session_path = Config.DATA_DIR / "wizard_session.json"
        session_path.write_text("{ invalid json }")

        loaded = wizard._load_session()
        assert loaded is False

    def test_clear_session(self, wizard, tmp_path):
        """Test clearing session after completion"""
        from skillforge.generators.config import Config
        Config.DATA_DIR = tmp_path
        Config.ensure_directories()

        # Create session file
        session_path = Config.DATA_DIR / "wizard_session.json"
        session_path.write_text('{"test": "data"}')

        wizard._clear_session()

        assert not session_path.exists()


class TestQuestionSkipping:
    """Test conditional question skipping logic"""

    def test_should_skip_frontend_for_backend_dev(self, wizard):
        """Test that frontend questions are skipped for backend developers"""
        answers = {"role": "Backend Developer"}

        frontend_question = next(
            q for q in wizard.QUESTIONS if q["id"] == "frontend_framework"
        )

        should_skip = wizard._should_skip_question(frontend_question, answers)
        assert should_skip is True

    def test_should_skip_ui_for_no_frontend(self, wizard):
        """Test that UI questions are skipped when no frontend is selected"""
        answers = {"frontend_framework": "None (Backend only)"}

        ui_question = next(
            q for q in wizard.QUESTIONS if q["id"] == "ui_library"
        )

        should_skip = wizard._should_skip_question(ui_question, answers)
        assert should_skip is True

    def test_should_not_skip_when_condition_false(self, wizard):
        """Test that questions are not skipped when conditions are not met"""
        answers = {"role": "Full-Stack Developer"}

        frontend_question = next(
            q for q in wizard.QUESTIONS if q["id"] == "frontend_framework"
        )

        should_skip = wizard._should_skip_question(frontend_question, answers)
        assert should_skip is False

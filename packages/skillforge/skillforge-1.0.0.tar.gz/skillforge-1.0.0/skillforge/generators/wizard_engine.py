"""
SkillForge Interactive Wizard Engine

This module provides an interactive wizard for:
- Detecting existing tech stack from project files
- Asking targeted questions about developer preferences
- Building a comprehensive user profile
- Saving configuration for skill generation

The wizard features:
- Auto-detection from package.json, requirements.txt, etc.
- Smart skip logic for detected technologies
- Branching questions based on previous answers
- Progress indicators and navigation
- Save/resume capability
- Colorful terminal output
"""

import json
import logging
import os
import re
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from skillforge.generators.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WizardEngine:
    """
    Interactive wizard engine for SkillForge setup and configuration.

    This class orchestrates the entire wizard flow, including:
    - Technology stack detection
    - Interactive question/answer sessions
    - Profile generation and persistence
    - Session management (save/resume)

    Attributes:
        current_dir: Working directory for project detection
        profile: User profile being built
        detected_tech: Auto-detected technologies
        session_state: Current wizard state for resume capability
        history: Question/answer history for navigation
    """

    # Question database with dependencies and conditions
    QUESTIONS = [
        {
            "id": "role",
            "question": "What type of developer are you?",
            "emoji": "👤",
            "options": [
                "Full-Stack Developer",
                "Frontend Developer",
                "Backend Developer",
                "DevOps Engineer",
                "Mobile Developer",
                "Data Engineer"
            ],
            "allow_multiple": False,
            "required": True
        },
        {
            "id": "frontend_framework",
            "question": "Which frontend framework do you primarily use?",
            "emoji": "⚛️",
            "options": [
                "React",
                "Vue.js",
                "Angular",
                "Svelte",
                "Next.js",
                "Nuxt.js",
                "Vanilla JavaScript",
                "None (Backend only)"
            ],
            "allow_multiple": False,
            "skip_if": lambda answers: "Backend" in answers.get("role", ""),
            "detect_from": ["package.json"]
        },
        {
            "id": "ui_library",
            "question": "Which UI component library do you use?",
            "emoji": "🎨",
            "options": [
                "Material-UI (MUI)",
                "Ant Design",
                "Chakra UI",
                "Tailwind CSS",
                "Bootstrap",
                "Styled Components",
                "CSS Modules",
                "None"
            ],
            "allow_multiple": True,
            "skip_if": lambda answers: answers.get("frontend_framework") == "None (Backend only)",
            "detect_from": ["package.json"]
        },
        {
            "id": "state_management",
            "question": "How do you manage state in your applications?",
            "emoji": "🔄",
            "options": [
                "Redux",
                "Redux Toolkit",
                "Zustand",
                "Recoil",
                "MobX",
                "Context API",
                "Pinia (Vue)",
                "None"
            ],
            "allow_multiple": True,
            "skip_if": lambda answers: answers.get("frontend_framework") == "None (Backend only)",
            "detect_from": ["package.json"]
        },
        {
            "id": "backend_framework",
            "question": "Which backend framework do you use?",
            "emoji": "🔧",
            "options": [
                "Express.js (Node)",
                "Fastify (Node)",
                "NestJS (Node)",
                "Django (Python)",
                "FastAPI (Python)",
                "Flask (Python)",
                "Ruby on Rails",
                "Laravel (PHP)",
                "Spring Boot (Java)",
                "Go (Gin/Echo)",
                "None (Frontend only)"
            ],
            "allow_multiple": False,
            "skip_if": lambda answers: "Frontend" in answers.get("role", ""),
            "detect_from": ["package.json", "requirements.txt", "go.mod", "composer.json"]
        },
        {
            "id": "database",
            "question": "Which database(s) do you work with?",
            "emoji": "💾",
            "options": [
                "PostgreSQL",
                "MySQL/MariaDB",
                "MongoDB",
                "Redis",
                "SQLite",
                "DynamoDB",
                "Firestore",
                "Supabase",
                "PlanetScale",
                "None"
            ],
            "allow_multiple": True,
            "detect_from": ["package.json", "requirements.txt", "go.mod"]
        },
        {
            "id": "auth_provider",
            "question": "How do you handle authentication?",
            "emoji": "🔐",
            "options": [
                "NextAuth.js",
                "Auth0",
                "Clerk",
                "Supabase Auth",
                "Firebase Auth",
                "JWT (Custom)",
                "Passport.js",
                "OAuth2",
                "None"
            ],
            "allow_multiple": True,
            "detect_from": ["package.json", "requirements.txt"]
        },
        {
            "id": "testing_tools",
            "question": "Which testing tools do you use?",
            "emoji": "🧪",
            "options": [
                "Jest",
                "Vitest",
                "Playwright",
                "Cypress",
                "Testing Library",
                "pytest",
                "unittest",
                "Mocha/Chai",
                "None"
            ],
            "allow_multiple": True,
            "detect_from": ["package.json", "requirements.txt"]
        },
        {
            "id": "build_tools",
            "question": "What build tools are in your workflow?",
            "emoji": "🏗️",
            "options": [
                "Vite",
                "Webpack",
                "Turbopack",
                "esbuild",
                "Rollup",
                "Parcel",
                "tsc (TypeScript)",
                "Babel",
                "None"
            ],
            "allow_multiple": True,
            "detect_from": ["package.json"]
        },
        {
            "id": "deployment_platform",
            "question": "Where do you deploy your applications?",
            "emoji": "🚀",
            "options": [
                "Vercel",
                "Netlify",
                "AWS",
                "Google Cloud",
                "Azure",
                "Heroku",
                "Railway",
                "Render",
                "DigitalOcean",
                "Self-hosted"
            ],
            "allow_multiple": True
        },
        {
            "id": "code_style",
            "question": "What are your code style preferences?",
            "emoji": "✨",
            "options": [
                "TypeScript strict mode",
                "ESLint + Prettier",
                "Airbnb style guide",
                "Standard.js",
                "Google style guide",
                "Black (Python)",
                "Functional programming",
                "Object-oriented",
                "Flexible"
            ],
            "allow_multiple": True
        },
        {
            "id": "workflow_preferences",
            "question": "What workflow features are important to you?",
            "emoji": "⚙️",
            "options": [
                "Git hooks (Husky)",
                "Pre-commit linting",
                "Conventional commits",
                "CI/CD pipelines",
                "Code review automation",
                "Automated testing",
                "Documentation generation",
                "Performance monitoring"
            ],
            "allow_multiple": True
        }
    ]

    # Technology detection patterns
    TECH_PATTERNS = {
        "package.json": {
            "react": ["React"],
            "vue": ["Vue.js"],
            "@angular/core": ["Angular"],
            "svelte": ["Svelte"],
            "next": ["Next.js"],
            "nuxt": ["Nuxt.js"],
            "@mui/material": ["Material-UI (MUI)"],
            "antd": ["Ant Design"],
            "@chakra-ui/react": ["Chakra UI"],
            "tailwindcss": ["Tailwind CSS"],
            "bootstrap": ["Bootstrap"],
            "styled-components": ["Styled Components"],
            "redux": ["Redux"],
            "@reduxjs/toolkit": ["Redux Toolkit"],
            "zustand": ["Zustand"],
            "recoil": ["Recoil"],
            "mobx": ["MobX"],
            "pinia": ["Pinia (Vue)"],
            "express": ["Express.js (Node)"],
            "fastify": ["Fastify (Node)"],
            "@nestjs/core": ["NestJS (Node)"],
            "next-auth": ["NextAuth.js"],
            "@auth0/nextjs-auth0": ["Auth0"],
            "@clerk/nextjs": ["Clerk"],
            "@supabase/supabase-js": ["Supabase", "Supabase Auth"],
            "firebase": ["Firebase Auth"],
            "passport": ["Passport.js"],
            "jest": ["Jest"],
            "vitest": ["Vitest"],
            "playwright": ["Playwright"],
            "cypress": ["Cypress"],
            "@testing-library/react": ["Testing Library"],
            "mocha": ["Mocha/Chai"],
            "vite": ["Vite"],
            "webpack": ["Webpack"],
            "esbuild": ["esbuild"],
            "rollup": ["Rollup"],
            "parcel": ["Parcel"],
            "typescript": ["tsc (TypeScript)", "TypeScript strict mode"],
            "eslint": ["ESLint + Prettier"],
            "prettier": ["ESLint + Prettier"],
            "husky": ["Git hooks (Husky)"],
            "pg": ["PostgreSQL"],
            "mysql": ["MySQL/MariaDB"],
            "mongodb": ["MongoDB"],
            "redis": ["Redis"],
            "sqlite3": ["SQLite"]
        },
        "requirements.txt": {
            "django": ["Django (Python)"],
            "fastapi": ["FastAPI (Python)"],
            "flask": ["Flask (Python)"],
            "pytest": ["pytest"],
            "psycopg2": ["PostgreSQL"],
            "pymongo": ["MongoDB"],
            "redis": ["Redis"],
            "sqlalchemy": ["PostgreSQL", "MySQL/MariaDB"],
            "black": ["Black (Python)"]
        },
        "go.mod": {
            "github.com/gin-gonic/gin": ["Go (Gin/Echo)"],
            "github.com/labstack/echo": ["Go (Gin/Echo)"]
        },
        "composer.json": {
            "laravel/framework": ["Laravel (PHP)"]
        }
    }

    def __init__(self, current_dir: Optional[Path] = None):
        """
        Initialize the wizard engine.

        Args:
            current_dir: Working directory for detection (defaults to cwd)
        """
        self.current_dir = current_dir or Path.cwd()
        self.profile: Dict[str, Any] = {}
        self.detected_tech: Dict[str, Set[str]] = {}
        self.session_state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.current_question_idx = 0

        # Setup signal handlers for graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum: int, frame: Any) -> None:
        """
        Handle Ctrl+C gracefully by saving session state.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print("\n\n⚠️  Wizard interrupted!")
        print("💾 Saving your progress...")

        try:
            self._save_session()
            print("✅ Progress saved. Run the wizard again to resume.")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            print("❌ Could not save progress.")

        sys.exit(0)

    def _save_session(self) -> None:
        """Save current session state for resume capability."""
        session_data = {
            "profile": self.profile,
            "detected_tech": {k: list(v) for k, v in self.detected_tech.items()},
            "history": self.history,
            "current_question_idx": self.current_question_idx
        }

        session_path = Config.DATA_DIR / "wizard_session.json"
        Config.ensure_directories()

        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

    def _load_session(self) -> bool:
        """
        Load saved session if it exists.

        Returns:
            True if session was loaded, False otherwise
        """
        session_path = Config.DATA_DIR / "wizard_session.json"

        if not session_path.exists():
            return False

        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            self.profile = session_data.get("profile", {})
            self.detected_tech = {
                k: set(v) for k, v in session_data.get("detected_tech", {}).items()
            }
            self.history = session_data.get("history", [])
            self.current_question_idx = session_data.get("current_question_idx", 0)

            return True
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def _clear_session(self) -> None:
        """Clear saved session after successful completion."""
        session_path = Config.DATA_DIR / "wizard_session.json"
        if session_path.exists():
            try:
                session_path.unlink()
            except OSError as e:
                logger.warning(f"Could not delete session file: {e}")

    def detect_stack(self) -> Dict[str, Set[str]]:
        """
        Auto-detect tech stack from project files.

        Scans common dependency files (package.json, requirements.txt, etc.)
        and extracts technology information.

        Returns:
            Dictionary mapping question IDs to detected technologies

        Example:
            {
                "frontend_framework": {"React", "Next.js"},
                "ui_library": {"Tailwind CSS"},
                "database": {"PostgreSQL"}
            }
        """
        detected: Dict[str, Set[str]] = {}

        # Check each type of config file
        for filename, patterns in self.TECH_PATTERNS.items():
            file_path = self.current_dir / filename

            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse JSON files
                if filename.endswith('.json'):
                    try:
                        data = json.loads(content)
                        dependencies = {}

                        # Collect all dependency fields
                        for key in ['dependencies', 'devDependencies', 'peerDependencies']:
                            if key in data:
                                dependencies.update(data[key])

                        # Match against patterns
                        for package, techs in patterns.items():
                            if package in dependencies:
                                self._add_detected_techs(detected, techs)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse {filename}")

                # Parse text files (requirements.txt, go.mod, etc.)
                else:
                    for pattern, techs in patterns.items():
                        if pattern in content:
                            self._add_detected_techs(detected, techs)

            except OSError as e:
                logger.warning(f"Could not read {filename}: {e}")

        self.detected_tech = detected
        return detected

    def _add_detected_techs(
        self,
        detected: Dict[str, Set[str]],
        techs: List[str]
    ) -> None:
        """
        Add detected technologies to the appropriate question categories.

        Args:
            detected: Dictionary to add technologies to
            techs: List of technology names to categorize
        """
        for tech in techs:
            # Find which question this tech belongs to
            for question in self.QUESTIONS:
                if tech in question["options"]:
                    question_id = question["id"]
                    if question_id not in detected:
                        detected[question_id] = set()
                    detected[question_id].add(tech)
                    break

    def show_detected(self) -> None:
        """Display auto-detected technologies in a formatted way."""
        if not self.detected_tech:
            print("🔍 No technologies auto-detected from project files.")
            print("   (Make sure you're running this in your project directory)")
            return

        print("\n🎯 Auto-detected Technologies:")
        print("=" * 60)

        for question in self.QUESTIONS:
            question_id = question["id"]
            if question_id in self.detected_tech and self.detected_tech[question_id]:
                techs = sorted(self.detected_tech[question_id])
                print(f"\n{question['emoji']} {question['question']}")
                for tech in techs:
                    print(f"   ✓ {tech}")

        print("\n" + "=" * 60)

    def ask_question(
        self,
        question: Dict[str, Any],
        detected: Optional[Set[str]] = None
    ) -> Union[str, List[str], None]:
        """
        Ask a single question and get user input.

        Args:
            question: Question dictionary with options and metadata
            detected: Pre-detected answers for this question

        Returns:
            User's answer(s) or None if skipped
        """
        question_id = question["id"]
        emoji = question["emoji"]
        text = question["question"]
        options = question["options"]
        allow_multiple = question["allow_multiple"]

        # Show question header
        print(f"\n{emoji} {text}")
        print("-" * 60)

        # Show detected technologies if any
        if detected:
            print(f"\n✨ Auto-detected: {', '.join(sorted(detected))}")

        # Show options
        print()
        for idx, option in enumerate(options, 1):
            marker = "✓" if detected and option in detected else " "
            print(f"  [{marker}] {idx}. {option}")

        print()
        if allow_multiple:
            print("💡 Tip: You can select multiple options (e.g., '1,3,5' or '1 3 5')")
        print("💡 Type 'b' to go back, 's' to skip, or 'q' to quit")

        # Get user input
        while True:
            if allow_multiple:
                prompt = f"\n👉 Your choice(s) [1-{len(options)}]: "
            else:
                prompt = f"\n👉 Your choice [1-{len(options)}]: "

            user_input = input(prompt).strip().lower()

            # Handle special commands
            if user_input == 'q':
                raise KeyboardInterrupt
            elif user_input == 's':
                return None
            elif user_input == 'b':
                return 'BACK'
            elif user_input == '':
                if detected:
                    # Use detected values
                    return list(detected) if allow_multiple else list(detected)[0]
                continue

            # Validate and parse input
            try:
                result = self.validate_answer(user_input, options, allow_multiple)
                if result:
                    return result
                else:
                    print("❌ Invalid input. Please try again.")
            except ValueError as e:
                print(f"❌ {e}")

    def validate_answer(
        self,
        user_input: str,
        options: List[str],
        allow_multiple: bool
    ) -> Union[str, List[str], None]:
        """
        Validate user input and return selected option(s).

        Args:
            user_input: Raw user input string
            options: Available options
            allow_multiple: Whether multiple selections are allowed

        Returns:
            Validated answer(s) or None if invalid

        Raises:
            ValueError: If input format is invalid
        """
        # Parse comma or space-separated input
        if allow_multiple:
            # Accept both "1,2,3" and "1 2 3"
            choices = re.split(r'[,\s]+', user_input)
        else:
            choices = [user_input]

        # Convert to indices and validate
        selected = []
        for choice in choices:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    selected.append(options[idx])
                else:
                    raise ValueError(f"Choice {choice} is out of range")
            except ValueError:
                raise ValueError(f"Invalid choice: {choice}")

        if not selected:
            return None

        return selected if allow_multiple else selected[0]

    def _should_skip_question(
        self,
        question: Dict[str, Any],
        answers: Dict[str, Any]
    ) -> bool:
        """
        Determine if a question should be skipped based on previous answers.

        Args:
            question: Question to evaluate
            answers: Previous answers

        Returns:
            True if question should be skipped
        """
        if "skip_if" in question:
            try:
                return question["skip_if"](answers)
            except Exception as e:
                logger.warning(f"Skip condition failed for {question['id']}: {e}")
                return False
        return False

    def run(self) -> Dict[str, Any]:
        """
        Main wizard entry point.

        Orchestrates the entire wizard flow:
        1. Check for saved session
        2. Detect tech stack
        3. Ask questions in sequence
        4. Handle navigation (back/skip)
        5. Save profile
        6. Show summary

        Returns:
            Complete user profile dictionary
        """
        # Show welcome message
        self._show_welcome()

        # Check for existing session
        if self._load_session():
            print("\n📂 Found saved progress from previous session!")
            resume = input("Would you like to resume? [Y/n]: ").strip().lower()
            if resume in ('n', 'no'):
                self.profile = {}
                self.history = []
                self.current_question_idx = 0

        # Detect tech stack
        print("\n🔍 Scanning your project for technologies...")
        self.detect_stack()

        if self.detected_tech:
            self.show_detected()
            input("\n👉 Press Enter to continue...")

        # Main question loop
        while self.current_question_idx < len(self.QUESTIONS):
            question = self.QUESTIONS[self.current_question_idx]
            question_id = question["id"]

            # Check if should skip
            if self._should_skip_question(question, self.profile):
                self.current_question_idx += 1
                continue

            # Show progress
            progress = f"Question {self.current_question_idx + 1}/{len(self.QUESTIONS)}"
            print(f"\n{'=' * 60}")
            print(f"📍 {progress}")
            print(f"{'=' * 60}")

            # Get detected values for this question
            detected = self.detected_tech.get(question_id)

            # Ask question
            try:
                answer = self.ask_question(question, detected)

                # Handle special responses
                if answer == 'BACK':
                    if self.current_question_idx > 0:
                        self.current_question_idx -= 1
                        # Remove last answer from profile
                        prev_question = self.QUESTIONS[self.current_question_idx]
                        self.profile.pop(prev_question["id"], None)
                    continue

                # Save answer
                if answer is not None:
                    self.profile[question_id] = answer
                    self.history.append({
                        "question_id": question_id,
                        "question": question["question"],
                        "answer": answer
                    })

                # Save session after each answer
                self._save_session()

                # Move to next question
                self.current_question_idx += 1

            except KeyboardInterrupt:
                # Handled by signal handler
                raise

        # Complete the profile
        self.profile["setup_completed"] = True
        self.profile["tech_stack"] = self._build_tech_stack()
        self.profile["preferences"] = self._build_preferences()
        self.profile["conventions"] = self._build_conventions()

        # Save final profile
        self.save_profile()

        # Show summary
        self.show_summary()

        # Clear session
        self._clear_session()

        return self.profile

    def _show_welcome(self) -> None:
        """Display welcome message and instructions."""
        print("\n" + "=" * 60)
        print("🎯 Welcome to SkillForge Setup Wizard!")
        print("=" * 60)
        print()
        print("This wizard will help me understand your development environment")
        print("and preferences so I can generate personalized Claude Code skills.")
        print()
        print("✨ Features:")
        print("   • Auto-detects technologies from your project")
        print("   • Smart questions based on your workflow")
        print("   • Save and resume anytime")
        print("   • Navigate back to previous questions")
        print()
        print("⏱️  This will take about 3-5 minutes")
        print()
        input("👉 Press Enter to start...")

    def _build_tech_stack(self) -> Dict[str, Any]:
        """
        Build tech stack section from profile answers.

        Returns:
            Dictionary with categorized technologies
        """
        tech_stack = {}

        # Map question IDs to tech stack categories
        mappings = {
            "frontend_framework": "frontend",
            "ui_library": "ui",
            "state_management": "state",
            "backend_framework": "backend",
            "database": "database",
            "auth_provider": "auth",
            "testing_tools": "testing",
            "build_tools": "build"
        }

        for question_id, category in mappings.items():
            if question_id in self.profile:
                tech_stack[category] = self.profile[question_id]

        return tech_stack

    def _build_preferences(self) -> Dict[str, Any]:
        """
        Build preferences section from profile answers.

        Returns:
            Dictionary with user preferences
        """
        preferences = {
            "role": self.profile.get("role"),
            "deployment": self.profile.get("deployment_platform", []),
            "code_style": self.profile.get("code_style", []),
            "workflow": self.profile.get("workflow_preferences", [])
        }

        return preferences

    def _build_conventions(self) -> Dict[str, Any]:
        """
        Build conventions section based on code style preferences.

        Returns:
            Dictionary with coding conventions
        """
        code_style = self.profile.get("code_style", [])

        conventions = {
            "typescript": "TypeScript strict mode" in code_style,
            "linting": "ESLint + Prettier" in code_style,
            "formatting": "ESLint + Prettier" in code_style or "Black (Python)" in code_style,
            "paradigm": []
        }

        if "Functional programming" in code_style:
            conventions["paradigm"].append("functional")
        if "Object-oriented" in code_style:
            conventions["paradigm"].append("oop")

        return conventions

    def save_profile(self) -> None:
        """
        Save the complete user profile to disk.

        Raises:
            OSError: If profile cannot be saved
        """
        try:
            Config.save_user_profile(self.profile)
            logger.info("User profile saved successfully")
        except OSError as e:
            logger.error(f"Failed to save profile: {e}")
            raise

    def show_summary(self) -> None:
        """Display a comprehensive summary of the configuration."""
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)

        print("\n📋 Your Configuration Summary:")
        print("-" * 60)

        # Show role
        if "role" in self.profile:
            print(f"\n👤 Role: {self.profile['role']}")

        # Show tech stack
        tech_stack = self.profile.get("tech_stack", {})
        if tech_stack:
            print("\n🔧 Tech Stack:")
            for category, tech in tech_stack.items():
                if tech:
                    if isinstance(tech, list):
                        print(f"   • {category.title()}: {', '.join(tech)}")
                    else:
                        print(f"   • {category.title()}: {tech}")

        # Show preferences
        preferences = self.profile.get("preferences", {})
        if preferences.get("deployment"):
            print(f"\n🚀 Deployment: {', '.join(preferences['deployment'])}")

        if preferences.get("code_style"):
            print(f"\n✨ Code Style: {', '.join(preferences['code_style'])}")

        if preferences.get("workflow"):
            print(f"\n⚙️  Workflow: {', '.join(preferences['workflow'])}")

        print("\n" + "=" * 60)
        print("💾 Profile saved to:", Config.DATA_DIR / "user_profile.json")
        print("=" * 60)

        # Suggest next steps
        self._show_next_steps()

    def _show_next_steps(self) -> None:
        """Display suggested next steps based on configuration."""
        print("\n🎯 Suggested Next Steps:")
        print("-" * 60)

        tech_stack = self.profile.get("tech_stack", {})

        # Suggest skills based on tech stack
        suggested_skills = []

        if "frontend" in tech_stack:
            frontend = tech_stack["frontend"]
            if "React" in frontend or "Next.js" in frontend:
                suggested_skills.append("react-component")
            if "Next.js" in frontend:
                suggested_skills.append("nextjs-page")

        if "backend" in tech_stack:
            backend = tech_stack["backend"]
            if "Express" in backend or "NestJS" in backend:
                suggested_skills.append("express-api")
            if "FastAPI" in backend or "Django" in backend:
                suggested_skills.append("python-api")

        if "testing" in tech_stack:
            suggested_skills.append("test-suite")

        if suggested_skills:
            print("\n📦 Recommended skills to generate:")
            for idx, skill in enumerate(suggested_skills, 1):
                print(f"   {idx}. {skill}")

        print("\n🚀 To generate skills, use Claude Code:")
        print("   /sf:generate <skill-name>")
        print("\n📚 To see all available skills:")
        print("   /sf:list")
        print()

    # Aliases for backward compatibility
    def _detect_technologies(self, project_path: Optional[Path] = None) -> Dict[str, Set[str]]:
        """
        Alias for detect_stack() - for backward compatibility.

        Args:
            project_path: Optional project path (updates current_dir if provided)

        Returns:
            Dictionary mapping question IDs to detected technologies
        """
        if project_path is not None:
            self.current_dir = Path(project_path)
        return self.detect_stack()

    def save_session(self, session_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Public alias for _save_session() - for backward compatibility.

        Args:
            session_data: Optional session data (ignored, uses internal state)
        """
        return self._save_session()

    def run_wizard(self) -> Dict[str, Any]:
        """
        Alias for run() method - for backward compatibility.

        Returns:
            Complete user profile dictionary
        """
        return self.run()

    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Public alias for _load_session() - for backward compatibility.

        Returns:
            Loaded session data if exists, None otherwise
        """
        if self._load_session():
            return self.answers
        return None

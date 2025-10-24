"""
SkillForge Main Skill Generator

This is the primary orchestrator that brings together WizardEngine, TemplateProcessor,
and DocFetcher to generate personalized Claude Code skills.

The SkillGenerator follows a 7-step process:
1. Load user profile (or create via wizard)
2. Select/load template based on skill_type
3. Fetch latest documentation via DocFetcher
4. Prepare template variables (merge profile + docs)
5. Process template via TemplateProcessor
6. Validate generated SKILL.md (YAML, sections, etc.)
7. Save to ~/.claude/skills/generated/{skill_name}/SKILL.md

Key Features:
- Intelligent template selection based on skill type
- Documentation fetching with caching
- Comprehensive validation of generated skills
- Rollback on failure for data integrity
- Progress indicators and detailed error messages
"""

import logging
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from .config import Config
from .doc_fetcher import DocFetcher, DocFetchError, LibraryDocs
from .template_processor import TemplateProcessor, TemplateError
from .wizard_engine import WizardEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkillGenerationError(Exception):
    """Raised when skill generation fails"""
    pass


class ValidationError(Exception):
    """Raised when generated skill validation fails"""
    pass


class SkillGenerator:
    """
    Main orchestrator for generating personalized Claude Code skills.

    This class coordinates:
    - User profile management (via WizardEngine)
    - Template selection and processing (via TemplateProcessor)
    - Documentation fetching (via DocFetcher)
    - Skill validation and persistence

    Attributes:
        template_dir: Path to skill templates
        output_dir: Path where generated skills are saved
        doc_fetcher: DocFetcher instance for retrieving documentation
        template_processor: TemplateProcessor instance for rendering templates
        profile: Current user profile (loaded or created)

    Example:
        >>> generator = SkillGenerator()
        >>> skill_path = generator.generate_skill("react-component")
        >>> print(f"Generated skill at: {skill_path}")
    """

    # Template type mappings for common skill types
    TEMPLATE_MAPPINGS = {
        # Frontend frameworks
        "react-component": "tech-stack/react-component.hbs",
        "nextjs-page": "tech-stack/nextjs-page.hbs",
        "vue-component": "tech-stack/vue-component.hbs",
        "svelte-component": "tech-stack/svelte-component.hbs",

        # Backend frameworks
        "express-api": "tech-stack/express-api.hbs",
        "fastapi-endpoint": "tech-stack/fastapi-endpoint.hbs",
        "django-view": "tech-stack/django-view.hbs",
        "nestjs-controller": "tech-stack/nestjs-controller.hbs",

        # Testing
        "test-suite": "workflow/test-suite.hbs",
        "e2e-test": "workflow/e2e-test.hbs",

        # Integration
        "api-integration": "integration/api-integration.hbs",
        "database-query": "integration/database-query.hbs",
        "auth-integration": "integration/auth-integration.hbs",

        # Workflow
        "git-workflow": "workflow/git-workflow.hbs",
        "deployment": "workflow/deployment.hbs",
        "ci-cd": "workflow/ci-cd.hbs",
    }

    # Required YAML fields in SKILL.md frontmatter
    REQUIRED_YAML_FIELDS = {
        "name": str,
        "description": str,
        "version": str,
        "created_by": str,
        "created_at": str,
    }

    # Required sections in SKILL.md
    REQUIRED_SECTIONS = [
        "Overview",
        "Best Practices",
        "Examples",
        "Usage",
    ]

    # Placeholder patterns that shouldn't appear in final output
    PLACEHOLDER_PATTERNS = [
        r'\bTODO\b',
        r'\bFIXME\b',
        r'\bXXX\b',
        r'\{\{[^}]+\}\}',  # Unprocessed template variables
        r'\[\[.*?\]\]',    # Placeholder brackets
        r'<PLACEHOLDER>',
    ]

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        profile: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the SkillGenerator.

        Args:
            template_dir: Path to templates (defaults to skillforge/templates)
            output_dir: Path for generated skills (defaults to ~/.claude/skills/generated)
            profile: User profile (if None, will be loaded or created)
        """
        # Setup paths
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        self.template_dir = Path(template_dir)

        if output_dir is None:
            output_dir = Path.home() / ".claude" / "skills" / "generated"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.doc_fetcher = DocFetcher(cache_ttl_days=7, use_mcp=False)
        self.template_processor = TemplateProcessor(
            template_dir=self.template_dir,
            strict_mode=False  # Don't fail on missing optional variables
        )

        # Load or create user profile
        self.profile = profile if profile else self._ensure_profile()

        logger.info(f"SkillGenerator initialized")
        logger.info(f"Template dir: {self.template_dir}")
        logger.info(f"Output dir: {self.output_dir}")

    def generate_skill(
        self,
        skill_type: str,
        skill_name: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        force_wizard: bool = False
    ) -> Path:
        """
        Main entry point for skill generation.

        This method orchestrates the entire 7-step generation process:
        1. Load/create user profile
        2. Select template
        3. Fetch documentation
        4. Prepare variables
        5. Process template
        6. Validate output
        7. Save skill

        Args:
            skill_type: Type of skill to generate (e.g., "react-component")
            skill_name: Optional custom name (defaults to skill_type)
            profile: Optional profile override
            force_wizard: Force wizard run even if profile exists

        Returns:
            Path to generated SKILL.md file

        Raises:
            SkillGenerationError: If generation fails at any step
            ValidationError: If generated skill fails validation

        Example:
            >>> generator = SkillGenerator()
            >>> skill_path = generator.generate_skill("react-component")
            >>> print(f"Skill generated: {skill_path}")
        """
        skill_name = skill_name or skill_type
        logger.info(f"Starting skill generation: {skill_name} (type: {skill_type})")

        # Print welcome message
        self._print_header("SkillForge - Skill Generation")
        print(f"\nGenerating skill: {skill_name}")
        print(f"Type: {skill_type}")
        print(f"Output: {self.output_dir / skill_name}\n")

        try:
            # Step 1: Load or create user profile
            print("Step 1/7: Loading user profile...")
            profile = self._load_or_create_profile(profile, force_wizard)
            print("✓ Profile loaded\n")

            # Step 2: Select and load template
            print("Step 2/7: Selecting template...")
            template_path = self.get_template_path(skill_type)
            template_content = self._load_template(template_path)
            print(f"✓ Template loaded: {template_path}\n")

            # Step 3: Fetch documentation
            print("Step 3/7: Fetching documentation...")
            docs = self._fetch_docs_for_skill(skill_type, skill_name)
            if docs:
                print(f"✓ Documentation fetched: {docs.library_name} v{docs.version}")
                print(f"  - {len(docs.examples)} examples")
                print(f"  - {len(docs.best_practices)} best practices\n")
            else:
                print("⚠ No documentation fetched (will use profile data)\n")

            # Step 4: Prepare template variables
            print("Step 4/7: Preparing template variables...")
            variables = self.prepare_variables(
                skill_type=skill_type,
                skill_name=skill_name,
                profile=profile,
                docs=docs
            )
            print(f"✓ {len(variables)} variables prepared\n")

            # Step 5: Process template
            print("Step 5/7: Processing template...")
            skill_content = self.process_template(template_content, variables)
            print(f"✓ Template processed ({len(skill_content)} chars)\n")

            # Step 6: Validate generated skill
            print("Step 6/7: Validating generated skill...")
            self.validate_generated_skill(skill_content, skill_name)
            print("✓ Validation passed\n")

            # Step 7: Save skill to disk
            print("Step 7/7: Saving skill...")
            skill_path = self._save_skill(
                skill_name=skill_name,
                skill_content=skill_content,
                variables=variables
            )
            print(f"✓ Skill saved: {skill_path}\n")

            # Success message
            self._print_success(skill_name, skill_path)

            return skill_path

        except Exception as e:
            logger.error(f"Skill generation failed: {e}")
            self._print_error(skill_name, str(e))

            # Attempt rollback
            try:
                self.rollback(skill_name)
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")

            raise SkillGenerationError(f"Failed to generate skill '{skill_name}': {e}")

    def fetch_documentation(
        self,
        library_name: str,
        topic: Optional[str] = None
    ) -> Optional[LibraryDocs]:
        """
        Fetch documentation for a library using DocFetcher.

        Args:
            library_name: Name of library (e.g., "react", "next.js")
            topic: Optional topic to focus on (e.g., "hooks", "routing")

        Returns:
            LibraryDocs object if successful, None otherwise

        Example:
            >>> generator = SkillGenerator()
            >>> docs = generator.fetch_documentation("react", topic="hooks")
            >>> if docs:
            ...     print(f"Found {len(docs.examples)} examples")
        """
        logger.info(f"Fetching documentation: {library_name} (topic={topic})")

        try:
            docs = self.doc_fetcher.fetch(library_name, topic=topic)
            if docs:
                logger.info(f"Documentation fetched successfully for {library_name}")
            else:
                logger.warning(f"No documentation found for {library_name}")
            return docs
        except DocFetchError as e:
            logger.error(f"Failed to fetch documentation: {e}")
            return None

    def process_template(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Process a template with variables using TemplateProcessor.

        Args:
            template: Template string (with Handlebars-like syntax)
            variables: Dictionary of variables to substitute

        Returns:
            Processed template string

        Raises:
            TemplateError: If template processing fails
        """
        logger.info("Processing template with variables")

        try:
            processed = self.template_processor.process(
                template=template,
                variables=variables,
                validate=False  # Don't fail on missing optional variables
            )
            logger.info("Template processed successfully")
            return processed

        except TemplateError as e:
            logger.error(f"Template processing failed: {e}")
            raise

    def validate_generated_skill(
        self,
        skill_content: str,
        skill_name: str
    ) -> None:
        """
        Validate that generated SKILL.md meets all requirements.

        Checks performed:
        1. YAML frontmatter is valid
        2. Required YAML fields are present
        3. Required sections are present
        4. No placeholder text remains
        5. Code examples are complete
        6. Description is specific (not generic)

        Args:
            skill_content: Generated skill content (markdown with YAML frontmatter)
            skill_name: Name of the skill (for error messages)

        Raises:
            ValidationError: If any validation check fails
        """
        logger.info(f"Validating skill: {skill_name}")
        errors = []

        # Extract YAML frontmatter and content
        yaml_data, markdown_content = self._extract_yaml_frontmatter(skill_content)

        # Validation 1: YAML frontmatter is valid
        if yaml_data is None:
            errors.append("Missing or invalid YAML frontmatter")
        else:
            # Validation 2: Required YAML fields are present and correct type
            for field, field_type in self.REQUIRED_YAML_FIELDS.items():
                if field not in yaml_data:
                    errors.append(f"Missing required YAML field: {field}")
                elif not isinstance(yaml_data[field], field_type):
                    errors.append(
                        f"YAML field '{field}' has wrong type "
                        f"(expected {field_type.__name__}, got {type(yaml_data[field]).__name__})"
                    )

        # Validation 3: Required sections are present
        if markdown_content:
            for section in self.REQUIRED_SECTIONS:
                if not self._has_section(markdown_content, section):
                    errors.append(f"Missing required section: {section}")

        # Validation 4: No placeholder text remains
        placeholders = self._find_placeholders(skill_content)
        if placeholders:
            errors.append(f"Found {len(placeholders)} unresolved placeholders: {placeholders[:3]}")

        # Validation 5: Code examples are complete (not empty)
        if markdown_content:
            empty_code_blocks = self._find_empty_code_blocks(markdown_content)
            if empty_code_blocks:
                errors.append(f"Found {empty_code_blocks} empty code blocks")

        # Validation 6: Description is specific (not too generic)
        if yaml_data and "description" in yaml_data:
            if self._is_generic_description(yaml_data["description"]):
                errors.append("Description is too generic or placeholder-like")

        # Report validation results
        if errors:
            logger.error(f"Validation failed with {len(errors)} errors")
            for error in errors:
                logger.error(f"  - {error}")
            raise ValidationError(
                f"Skill validation failed with {len(errors)} errors:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        logger.info("Validation passed successfully")

    def get_template_path(self, skill_type: str) -> Path:
        """
        Find the appropriate template file for a skill type.

        Args:
            skill_type: Type of skill (e.g., "react-component")

        Returns:
            Path to template file

        Raises:
            FileNotFoundError: If template doesn't exist
            SkillGenerationError: If skill_type is unknown

        Example:
            >>> generator = SkillGenerator()
            >>> path = generator.get_template_path("react-component")
            >>> print(path)
            PosixPath('.../templates/tech-stack/react-component.hbs')
        """
        logger.info(f"Looking up template for skill type: {skill_type}")

        # Check if we have a mapping for this skill type
        if skill_type in self.TEMPLATE_MAPPINGS:
            template_path = self.template_dir / self.TEMPLATE_MAPPINGS[skill_type]

            # Check if template exists
            if template_path.exists():
                logger.info(f"Found template: {template_path}")
                return template_path
            else:
                # Template mapped but doesn't exist - log available templates
                available = self._list_available_templates()
                raise FileNotFoundError(
                    f"Template mapped but not found: {template_path}\n"
                    f"Available templates:\n" + "\n".join(f"  - {t}" for t in available)
                )

        # No mapping found - try to find by name directly
        logger.warning(f"No template mapping for '{skill_type}', searching...")

        # Search in all subdirectories
        for subdir in ["tech-stack", "workflow", "integration"]:
            template_path = self.template_dir / subdir / f"{skill_type}.hbs"
            if template_path.exists():
                logger.info(f"Found template: {template_path}")
                return template_path

        # Template not found - show available options
        available = self._list_available_templates()
        raise SkillGenerationError(
            f"Unknown skill type: {skill_type}\n"
            f"Available skill types:\n" + "\n".join(f"  - {t}" for t in available)
        )

    def prepare_variables(
        self,
        skill_type: str,
        skill_name: str,
        profile: Dict[str, Any],
        docs: Optional[LibraryDocs] = None
    ) -> Dict[str, Any]:
        """
        Prepare template variables by merging profile and documentation.

        Variables prepared:
        - skill_name: Name of the skill
        - skill_type: Type of skill
        - framework_name: Extracted from skill_type
        - framework_version: From docs (if available)
        - best_practices: List from docs or profile
        - code_examples: List from docs
        - user_conventions: From profile
        - user_tech_stack: From profile
        - dependencies: From docs
        - generated_at: ISO timestamp
        - generated_by: "SkillForge"
        - generation_metadata: Version and timestamp info

        Args:
            skill_type: Type of skill being generated
            skill_name: Name for the skill
            profile: User profile dictionary
            docs: Optional documentation data

        Returns:
            Dictionary of template variables

        Example:
            >>> generator = SkillGenerator()
            >>> profile = Config.load_user_profile()
            >>> docs = generator.fetch_documentation("react")
            >>> vars = generator.prepare_variables("react-component", "my-skill", profile, docs)
            >>> print(vars.keys())
            dict_keys(['skill_name', 'skill_type', 'framework_name', ...])
        """
        logger.info(f"Preparing variables for {skill_name}")

        # Extract framework name from skill type (e.g., "react-component" -> "react")
        framework_name = self._extract_framework_name(skill_type)

        # Base variables
        variables = {
            "skill_name": skill_name,
            "skill_type": skill_type,
            "framework_name": framework_name,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "SkillForge",
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Add documentation data if available
        if docs:
            variables.update({
                "framework_version": docs.version or "latest",
                "best_practices": docs.best_practices[:10],  # Limit to 10
                "code_examples": [
                    {
                        "code": ex["code"],
                        "language": ex["language"],
                        "description": ex["description"]
                    }
                    for ex in docs.examples[:5]  # Limit to 5
                ],
                "dependencies": self._extract_dependencies(docs),
                "documentation_source": docs.source.type,
                "topics_covered": docs.topics_covered[:5],
            })
        else:
            # Use placeholder data
            variables.update({
                "framework_version": "latest",
                "best_practices": self._get_default_best_practices(framework_name),
                "code_examples": [],
                "dependencies": [],
                "topics_covered": [],
            })

        # Add user profile data
        tech_stack = profile.get("tech_stack", {})
        preferences = profile.get("preferences", {})
        conventions = profile.get("conventions", {})

        variables.update({
            "user_tech_stack": tech_stack,
            "user_preferences": preferences,
            "user_conventions": conventions,
            "user_role": preferences.get("role", "Developer"),
            "code_style": preferences.get("code_style", []),
        })

        # Add generation metadata
        variables["generation_metadata"] = {
            "version": "0.0.1-dev",
            "timestamp": time.time(),
            "template": skill_type,
            "has_docs": docs is not None,
            "profile_complete": profile.get("setup_completed", False)
        }

        logger.info(f"Prepared {len(variables)} template variables")
        return variables

    def create_supporting_files(self, skill_name: str) -> None:
        """
        Create supporting files and directories for a skill.

        Creates:
        - skill_name/SKILL.md (main skill file)
        - skill_name/examples/ (example directory)
        - skill_name/README.md (usage documentation)

        Args:
            skill_name: Name of the skill

        Raises:
            OSError: If directories cannot be created
        """
        logger.info(f"Creating supporting files for {skill_name}")

        skill_dir = self.output_dir / skill_name

        try:
            # Create main directory
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Create examples directory
            examples_dir = skill_dir / "examples"
            examples_dir.mkdir(exist_ok=True)

            logger.info(f"Created supporting files for {skill_name}")

        except OSError as e:
            logger.error(f"Failed to create supporting files: {e}")
            raise

    def rollback(self, skill_name: str) -> None:
        """
        Rollback a failed skill generation by cleaning up artifacts.

        Removes:
        - Generated skill directory and all contents
        - Any temporary files created during generation

        Args:
            skill_name: Name of the skill to rollback

        Example:
            >>> generator = SkillGenerator()
            >>> try:
            ...     generator.generate_skill("bad-skill")
            ... except SkillGenerationError:
            ...     generator.rollback("bad-skill")
        """
        logger.info(f"Rolling back skill generation: {skill_name}")

        skill_dir = self.output_dir / skill_name

        if skill_dir.exists():
            try:
                shutil.rmtree(skill_dir)
                logger.info(f"Removed skill directory: {skill_dir}")
            except OSError as e:
                logger.error(f"Failed to remove skill directory: {e}")
                raise

        logger.info("Rollback completed")

    # --- Private Helper Methods ---

    def _ensure_profile(self) -> Dict[str, Any]:
        """Load or create user profile."""
        profile = Config.load_user_profile()

        if not profile.get("setup_completed", False):
            logger.info("User profile not complete, prompting to run wizard")
            print("\n⚠️  User profile not found or incomplete.")
            print("To generate personalized skills, please complete the setup wizard.\n")

            response = input("Run setup wizard now? [Y/n]: ").strip().lower()
            if response not in ('n', 'no'):
                wizard = WizardEngine()
                profile = wizard.run()
            else:
                logger.warning("User declined wizard, using default profile")
                print("Continuing with default profile...")

        return profile

    def _load_or_create_profile(
        self,
        profile: Optional[Dict[str, Any]],
        force_wizard: bool
    ) -> Dict[str, Any]:
        """Load or create user profile with wizard if needed."""
        if profile:
            return profile

        # Use instance profile if available
        if self.profile:
            return self.profile

        if force_wizard:
            wizard = WizardEngine()
            return wizard.run()

        return self._ensure_profile()

    def _load_template(self, template_path: Path) -> str:
        """Load template file from disk."""
        try:
            return self.template_processor.load_template(template_path)
        except FileNotFoundError:
            raise SkillGenerationError(f"Template not found: {template_path}")
        except Exception as e:
            raise SkillGenerationError(f"Error loading template: {e}")

    def _fetch_docs_for_skill(
        self,
        skill_type: str,
        skill_name: str
    ) -> Optional[LibraryDocs]:
        """Fetch documentation relevant to the skill type."""
        # Extract library name from skill type
        library_name = self._extract_framework_name(skill_type)

        # Extract topic if present (e.g., "react-hooks" -> topic="hooks")
        topic = self._extract_topic_from_skill_type(skill_type)

        return self.fetch_documentation(library_name, topic=topic)

    def _save_skill(
        self,
        skill_name: str,
        skill_content: str,
        variables: Dict[str, Any]
    ) -> Path:
        """Save generated skill to disk."""
        # Create skill directory
        skill_dir = self.output_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Save main SKILL.md
        skill_path = skill_dir / "SKILL.md"
        try:
            skill_path.write_text(skill_content, encoding='utf-8')
            logger.info(f"Saved skill to {skill_path}")
        except OSError as e:
            raise SkillGenerationError(f"Failed to save skill: {e}")

        # Create supporting files
        self.create_supporting_files(skill_name)

        # Save metadata
        self._save_metadata(skill_dir, variables)

        return skill_path

    def _save_metadata(self, skill_dir: Path, variables: Dict[str, Any]) -> None:
        """Save generation metadata to .skillforge.json"""
        metadata_path = skill_dir / ".skillforge.json"

        metadata = {
            "skill_name": variables["skill_name"],
            "skill_type": variables["skill_type"],
            "generated_at": variables["generated_at"],
            "generated_by": variables["generated_by"],
            "generation_metadata": variables.get("generation_metadata", {}),
        }

        try:
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
        except OSError as e:
            logger.warning(f"Failed to save metadata: {e}")

    def _extract_yaml_frontmatter(
        self,
        content: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Extract YAML frontmatter and markdown content from skill file."""
        # Pattern: ---\nYAML\n---\nMarkdown
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return None, content

        yaml_str = match.group(1)
        markdown = match.group(2)

        try:
            yaml_data = yaml.safe_load(yaml_str)
            return yaml_data, markdown
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return None, markdown

    def _has_section(self, content: str, section_name: str) -> bool:
        """Check if a section exists in markdown content."""
        # Look for markdown headers: ## Section Name or # Section Name
        pattern = rf'^##?\s+{re.escape(section_name)}\s*$'
        return bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))

    def _find_placeholders(self, content: str) -> List[str]:
        """Find unresolved placeholders in content."""
        placeholders = []

        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, content)
            placeholders.extend(matches)

        return placeholders

    def _find_empty_code_blocks(self, content: str) -> int:
        """Count empty code blocks in markdown."""
        # Pattern: ```language\n\n```
        pattern = r'```\w*\s*\n\s*\n```'
        matches = re.findall(pattern, content)
        return len(matches)

    def _is_generic_description(self, description: str) -> bool:
        """Check if description is too generic."""
        generic_patterns = [
            r'\[.*?\]',  # [Description here]
            r'<.*?>',    # <description>
            r'TODO',
            r'PLACEHOLDER',
            # Note: 'skill for' removed as it can appear in valid descriptions
        ]

        description_lower = description.lower()

        # Check for generic patterns
        for pattern in generic_patterns:
            if re.search(pattern, description_lower):
                return True

        # Check for very short descriptions
        if len(description.strip()) < 20:
            return True

        return False

    def _extract_framework_name(self, skill_type: str) -> str:
        """Extract framework name from skill type."""
        # Common patterns:
        # "react-component" -> "react"
        # "nextjs-page" -> "next.js"
        # "express-api" -> "express"

        mappings = {
            "nextjs": "next.js",
            "vuejs": "vue.js",
        }

        # Get first part before hyphen
        parts = skill_type.split("-")
        framework = parts[0]

        # Apply known mappings
        return mappings.get(framework, framework)

    def _extract_topic_from_skill_type(self, skill_type: str) -> Optional[str]:
        """Extract topic from skill type if present."""
        # "react-hooks" -> "hooks"
        # "nextjs-routing" -> "routing"

        parts = skill_type.split("-")
        if len(parts) > 1:
            # Return everything after the framework name
            return "-".join(parts[1:])

        return None

    def _extract_dependencies(self, docs: LibraryDocs) -> List[str]:
        """Extract dependencies from documentation."""
        # Look for npm packages, pip packages, etc. in content
        dependencies = []

        # Simple extraction from content
        # (This could be enhanced with more sophisticated parsing)
        content = docs.content.lower()

        common_patterns = [
            r'npm install ([^\s\n]+)',
            r'pip install ([^\s\n]+)',
            r'yarn add ([^\s\n]+)',
        ]

        for pattern in common_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)

        # Remove duplicates
        return list(set(dependencies))[:10]  # Limit to 10

    def _get_default_best_practices(self, framework_name: str) -> List[str]:
        """Get default best practices when docs aren't available."""
        defaults = {
            "react": [
                "Use functional components with hooks",
                "Keep components small and focused",
                "Implement proper error boundaries",
                "Use React.memo for performance optimization",
                "Follow the principle of composition over inheritance",
            ],
            "vue": [
                "Use Composition API for better code organization",
                "Keep computed properties pure",
                "Use proper prop validation",
                "Implement lifecycle hooks appropriately",
            ],
            "express": [
                "Use middleware for cross-cutting concerns",
                "Implement proper error handling",
                "Use environment variables for configuration",
                "Follow RESTful API design principles",
            ],
            "fastapi": [
                "Use type hints for automatic validation",
                "Implement dependency injection",
                "Use async/await for I/O operations",
                "Document endpoints with proper descriptions",
            ],
        }

        return defaults.get(framework_name, [
            "Follow framework conventions",
            "Write clean, maintainable code",
            "Implement proper error handling",
            "Add comprehensive tests",
            "Document your code thoroughly",
        ])

    def _list_available_templates(self) -> List[str]:
        """List all available template skill types."""
        return sorted(self.TEMPLATE_MAPPINGS.keys())

    def _print_header(self, title: str) -> None:
        """Print a formatted header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def _print_success(self, skill_name: str, skill_path: Path) -> None:
        """Print success message."""
        print("\n" + "=" * 70)
        print("  ✅ Skill Generated Successfully!")
        print("=" * 70)
        print(f"\nSkill: {skill_name}")
        print(f"Location: {skill_path}")
        print(f"\nNext steps:")
        print(f"  1. Review the generated SKILL.md")
        print(f"  2. Customize as needed")
        print(f"  3. Use in Claude Code with: @{skill_name}")
        print("\n" + "=" * 70 + "\n")

    def _print_error(self, skill_name: str, error: str) -> None:
        """Print error message."""
        print("\n" + "=" * 70)
        print("  ❌ Skill Generation Failed")
        print("=" * 70)
        print(f"\nSkill: {skill_name}")
        print(f"Error: {error}")
        print("\n" + "=" * 70 + "\n")

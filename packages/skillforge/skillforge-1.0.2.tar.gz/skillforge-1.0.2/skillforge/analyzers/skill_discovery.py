"""
Skill Discovery System for SkillForge

This module implements intelligent skill discovery that identifies the most relevant
skills for a given user intent. It scans available skills, analyzes their metadata,
and applies multiple discovery strategies to find the best matches.

The SkillDiscovery class provides:
- Automatic skill scanning from ~/.claude/skills/
- Multi-strategy discovery (explicit, pattern, domain, dependency)
- Priority-based ranking with confidence scoring
- Skill metadata caching for performance
- Integration with learned patterns and user profile

Discovery Strategies (by priority):
1. Explicit Match (100): User mentions framework/skill name directly
2. Pattern Match (70-90): Learned patterns suggest skills
3. Domain Match (60): Domain requires certain skills
4. Dependency Match (40): Other skills require this

Example:
    >>> discovery = SkillDiscovery()
    >>> intent = Intent(
    ...     text="Create a Next.js login component with Supabase auth",
    ...     entities=["Next.js", "Supabase", "authentication"],
    ...     domain="fullstack"
    ... )
    >>> discovered = discovery.discover(intent)
    >>> for skill in discovered:
    ...     print(f"{skill.skill.name} (priority={skill.priority}, reason={skill.reason})")
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from ..generators.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SkillMetadata:
    """
    Metadata about a discovered skill.

    This class holds all relevant information about a skill including its
    location, description, triggers, dependencies, and performance metrics.

    Attributes:
        name: Skill name (from YAML frontmatter or directory name)
        path: Absolute path to SKILL.md file
        description: Skill description (from YAML frontmatter)
        triggers: Keywords/patterns that trigger this skill
        dependencies: Other skills required by this skill
        priority: Base priority (0-100, used for initial ranking)
        usage_count: Historical usage count (from analytics)
        success_rate: Success rate (0.0 to 1.0)
        last_used: When skill was last used (None if never)
    """
    name: str
    path: Path
    description: str
    triggers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 50  # Default medium priority
    usage_count: int = 0
    success_rate: float = 1.0
    last_used: Optional[datetime] = None

    def __post_init__(self):
        """Validate metadata after initialization."""
        # Ensure path is absolute
        if not self.path.is_absolute():
            self.path = self.path.resolve()

        # Validate priority range
        self.priority = max(0, min(100, self.priority))

        # Validate success rate range
        self.success_rate = max(0.0, min(1.0, self.success_rate))


@dataclass
class DiscoveredSkill:
    """
    A skill discovered for a specific intent.

    This class wraps SkillMetadata with context-specific information about
    why the skill was discovered and how confident we are about it.

    Attributes:
        skill: The underlying SkillMetadata
        priority: Final calculated priority for this discovery (0-100)
        reason: Why this skill was discovered (e.g., "explicit", "pattern")
        confidence: Confidence score (0.0 to 1.0)
    """
    skill: SkillMetadata
    priority: int
    reason: str  # "explicit", "pattern", "domain", "dependency"
    confidence: float

    def __post_init__(self):
        """Validate after initialization."""
        self.priority = max(0, min(100, self.priority))
        self.confidence = max(0.0, min(1.0, self.confidence))

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access - delegates to SkillMetadata."""
        if hasattr(self, key):
            return getattr(self, key)
        elif hasattr(self.skill, key):
            return getattr(self.skill, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return hasattr(self, key) or hasattr(self.skill, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get()."""
        if hasattr(self, key):
            return getattr(self, key)
        elif hasattr(self.skill, key):
            return getattr(self.skill, key)
        return default


@dataclass
class Intent:
    """
    User intent parsed from a request.

    This is a simple representation of user intent. In a full implementation,
    this would come from IntentAnalyzer.

    Attributes:
        text: Original user request text
        entities: Extracted entities (frameworks, libraries, technologies)
        domain: Inferred domain (e.g., "frontend", "backend", "fullstack")
        patterns: Learned patterns that match this intent
        action: Main action (e.g., "create", "fix", "refactor")
    """
    text: str
    entities: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    action: Optional[str] = None


# ============================================================================
# Main SkillDiscovery Class
# ============================================================================

class SkillDiscovery:
    """
    Intelligent skill discovery system.

    This class implements multi-strategy skill discovery that finds the most
    relevant skills for a given user intent. It scans available skills,
    caches metadata, and applies various discovery strategies.

    Attributes:
        skills_dir: Base directory for skills (default: ~/.claude/skills/)
        cache: In-memory cache of SkillMetadata
        analytics: Usage analytics (loaded from Config)
        patterns: Learned patterns (loaded from Config)
        user_profile: User preferences (loaded from Config)

    Example:
        >>> discovery = SkillDiscovery()
        >>> # Discover skills for an intent
        >>> intent = Intent(
        ...     text="Create a React component",
        ...     entities=["React", "component"]
        ... )
        >>> skills = discovery.discover(intent)
        >>> print(f"Found {len(skills)} relevant skills")
    """

    # Domain-to-skill mappings
    DOMAIN_MAPPINGS = {
        "frontend": ["react", "vue", "svelte", "nextjs", "ui", "component"],
        "backend": ["api", "express", "fastapi", "django", "database"],
        "fullstack": ["nextjs", "fullstack", "api", "database"],
        "testing": ["test", "jest", "vitest", "e2e", "playwright"],
        "deployment": ["docker", "ci-cd", "deployment", "kubernetes"],
        "authentication": ["auth", "supabase", "firebase", "oauth"],
        "database": ["database", "postgresql", "mongodb", "prisma", "supabase"],
    }

    # Framework name variations and aliases
    FRAMEWORK_ALIASES = {
        "next.js": ["nextjs", "next"],
        "react": ["react", "reactjs"],
        "vue.js": ["vue", "vuejs"],
        "svelte": ["svelte", "sveltekit"],
        "fastapi": ["fastapi", "fast-api"],
        "express": ["express", "expressjs"],
        "supabase": ["supabase", "supa"],
        "firebase": ["firebase", "fb"],
        "postgresql": ["postgresql", "postgres", "pg"],
        "mongodb": ["mongodb", "mongo"],
    }

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize the SkillDiscovery system.

        Args:
            skills_dir: Base directory for skills (defaults to Config.SKILLFORGE_HOME.parent)
        """
        # Set skills directory - use Config.SKILLFORGE_HOME.parent for consistency
        if skills_dir is None:
            # Config.SKILLFORGE_HOME is ~/.claude/skills/skillforge/
            # Skills are in ~/.claude/skills/
            skills_dir = Config.SKILLFORGE_HOME.parent
        self.skills_dir = Path(skills_dir)

        # In-memory cache of skill metadata
        self.cache: Dict[str, SkillMetadata] = {}

        # Load analytics and patterns
        self.analytics = Config.load_analytics()
        self.patterns = Config.load_learned_patterns()
        self.user_profile = Config.load_user_profile()

        logger.info(f"SkillDiscovery initialized with skills_dir: {self.skills_dir}")

    # ========================================================================
    # Main Discovery Method
    # ========================================================================

    def discover(self, intent: Intent) -> List[DiscoveredSkill]:
        """
        Main discovery method - finds relevant skills for an intent.

        This method applies all discovery strategies in priority order:
        1. Explicit matches (user mentioned skill/framework directly)
        2. Pattern matches (learned patterns suggest skills)
        3. Domain matches (domain requires certain skills)
        4. Dependency matches (other skills require this)

        Args:
            intent: User intent with entities, domain, patterns

        Returns:
            List of DiscoveredSkill objects, sorted by priority (descending)

        Example:
            >>> intent = Intent(
            ...     text="Create a Next.js page with Supabase auth",
            ...     entities=["Next.js", "Supabase"],
            ...     domain="fullstack"
            ... )
            >>> skills = discovery.discover(intent)
            >>> # Returns skills like "nextjs-fullstack" and "supabase-integration"
        """
        logger.info(f"Discovering skills for intent: {intent.text[:50]}...")

        # Ensure skills are loaded
        if not self.cache:
            self.load_available_skills()

        discovered: List[DiscoveredSkill] = []
        discovered_names: Set[str] = set()  # Track to avoid duplicates

        # Strategy 1: Explicit matches (priority 100)
        explicit_skills = self._discover_explicit_matches(intent)
        for skill_meta, confidence in explicit_skills:
            if skill_meta.name not in discovered_names:
                discovered.append(DiscoveredSkill(
                    skill=skill_meta,
                    priority=100,
                    reason="explicit",
                    confidence=confidence
                ))
                discovered_names.add(skill_meta.name)

        # Strategy 2: Pattern matches (priority 70-90)
        pattern_skills = self._discover_pattern_matches(intent)
        for skill_meta, pattern_confidence in pattern_skills:
            if skill_meta.name not in discovered_names:
                # Priority based on pattern confidence
                priority = int(70 + (pattern_confidence * 20))  # 70-90
                discovered.append(DiscoveredSkill(
                    skill=skill_meta,
                    priority=priority,
                    reason="pattern",
                    confidence=pattern_confidence
                ))
                discovered_names.add(skill_meta.name)

        # Strategy 3: Dependency matches (priority 65)
        # For each discovered skill, check if it requires other skills
        # Process dependencies BEFORE domain matches to give them higher priority
        dependency_skills = self._discover_dependencies(discovered)
        for skill_meta in dependency_skills:
            if skill_meta.name not in discovered_names:
                discovered.append(DiscoveredSkill(
                    skill=skill_meta,
                    priority=65,
                    reason="dependency",
                    confidence=0.6
                ))
                discovered_names.add(skill_meta.name)

        # Strategy 4: Domain matches (priority 60)
        domain_skills = self._discover_domain_matches(intent)
        for skill_meta in domain_skills:
            if skill_meta.name not in discovered_names:
                discovered.append(DiscoveredSkill(
                    skill=skill_meta,
                    priority=60,
                    reason="domain",
                    confidence=0.7
                ))
                discovered_names.add(skill_meta.name)

        # Apply user preferences filter
        discovered = self._apply_user_preferences(discovered)

        # Sort by priority (descending), then confidence (descending)
        discovered.sort(key=lambda x: (x.priority, x.confidence), reverse=True)

        logger.info(f"Discovered {len(discovered)} skills")
        for ds in discovered[:5]:  # Log top 5
            logger.info(f"  - {ds.skill.name} (priority={ds.priority}, reason={ds.reason}, confidence={ds.confidence:.2f})")

        return discovered

    # ========================================================================
    # Entity-based Discovery
    # ========================================================================

    def find_skill_for_entity(self, entity: str) -> Optional[SkillMetadata]:
        """
        Find a skill that matches a specific entity (framework/library).

        This method searches for skills whose name or triggers match the
        given entity, accounting for aliases and variations.

        Args:
            entity: Framework, library, or technology name

        Returns:
            SkillMetadata if found, None otherwise

        Example:
            >>> skill = discovery.find_skill_for_entity("Next.js")
            >>> if skill:
            ...     print(f"Found skill: {skill.name}")
        """
        logger.info(f"Finding skill for entity: {entity}")

        # Ensure skills are loaded
        if not self.cache:
            self.load_available_skills()

        # Normalize entity
        entity_lower = entity.lower()

        # Get aliases for this entity
        aliases = self._get_entity_aliases(entity_lower)

        # Search for matches in cache
        for skill in self.cache.values():
            skill_name_lower = skill.name.lower()

            # Check name match
            if any(alias in skill_name_lower for alias in aliases):
                logger.info(f"Found skill by name: {skill.name}")
                return skill

            # Check triggers
            for trigger in skill.triggers:
                trigger_lower = trigger.lower()
                if any(alias in trigger_lower for alias in aliases):
                    logger.info(f"Found skill by trigger: {skill.name}")
                    return skill

        logger.info(f"No skill found for entity: {entity}")
        return None

    # ========================================================================
    # Domain-based Discovery
    # ========================================================================

    def get_domain_skills(self, domain: str) -> List[SkillMetadata]:
        """
        Get skills relevant to a specific domain.

        Uses domain mappings to identify skills that are typically used
        in a given domain (frontend, backend, testing, etc.).

        Args:
            domain: Domain name (e.g., "frontend", "backend", "fullstack")

        Returns:
            List of SkillMetadata for the domain

        Example:
            >>> skills = discovery.get_domain_skills("frontend")
            >>> # Returns skills like react-component, vue-spa, etc.
        """
        logger.info(f"Getting skills for domain: {domain}")

        # Ensure skills are loaded
        if not self.cache:
            self.load_available_skills()

        # Get domain keywords
        domain_keywords = self.DOMAIN_MAPPINGS.get(domain.lower(), [])
        if not domain_keywords:
            logger.warning(f"Unknown domain: {domain}")
            return []

        # Find skills that match domain keywords
        matching_skills = []
        for skill in self.cache.values():
            skill_name_lower = skill.name.lower()

            # Check if any domain keyword is in skill name or triggers
            if any(keyword in skill_name_lower for keyword in domain_keywords):
                matching_skills.append(skill)
                continue

            # Check triggers
            for trigger in skill.triggers:
                if any(keyword in trigger.lower() for keyword in domain_keywords):
                    matching_skills.append(skill)
                    break

        logger.info(f"Found {len(matching_skills)} skills for domain '{domain}'")
        return matching_skills

    # ========================================================================
    # Pattern-based Discovery
    # ========================================================================

    def get_pattern_skills(self, patterns: List[Dict[str, Any]]) -> List[SkillMetadata]:
        """
        Get skills suggested by learned patterns.

        Analyzes learned patterns to identify skills that are frequently
        used together or in specific contexts.

        Args:
            patterns: List of pattern dictionaries with 'skills' and 'confidence'

        Returns:
            List of SkillMetadata suggested by patterns

        Example:
            >>> patterns = [
            ...     {"skills": ["nextjs-fullstack", "supabase-integration"], "confidence": 0.9}
            ... ]
            >>> skills = discovery.get_pattern_skills(patterns)
        """
        logger.info(f"Getting skills from {len(patterns)} patterns")

        # Ensure skills are loaded
        if not self.cache:
            self.load_available_skills()

        # Collect skill names from patterns
        skill_names: Set[str] = set()
        for pattern in patterns:
            if "skills" in pattern:
                skill_names.update(pattern["skills"])

        # Find matching skills
        matching_skills = []
        for skill_name in skill_names:
            if skill_name in self.cache:
                matching_skills.append(self.cache[skill_name])
            else:
                logger.warning(f"Pattern references unknown skill: {skill_name}")

        logger.info(f"Found {len(matching_skills)} skills from patterns")
        return matching_skills

    # ========================================================================
    # Skill Loading and Caching
    # ========================================================================

    def load_available_skills(self) -> List[SkillMetadata]:
        """
        Scan and load all available skills from ~/.claude/skills/.

        This method recursively searches for SKILL.md files, parses their
        YAML frontmatter, extracts metadata, and caches the results.

        Returns:
            List of SkillMetadata for all discovered skills

        Example:
            >>> skills = discovery.load_available_skills()
            >>> print(f"Loaded {len(skills)} skills")
        """
        logger.info(f"Scanning for skills in: {self.skills_dir}")

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return []

        skills: List[SkillMetadata] = []

        # Recursively find all SKILL.md files
        skill_files = list(self.skills_dir.rglob("SKILL.md"))
        logger.info(f"Found {len(skill_files)} SKILL.md files")

        for skill_file in skill_files:
            try:
                skill_meta = self._parse_skill_file(skill_file)
                if skill_meta:
                    skills.append(skill_meta)
                    self.cache[skill_meta.name] = skill_meta
            except Exception as e:
                logger.error(f"Failed to parse skill file {skill_file}: {e}")

        # Enrich with analytics data
        self._enrich_with_analytics(skills)

        logger.info(f"Loaded {len(skills)} skills into cache")
        return skills

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _parse_skill_file(self, skill_file: Path) -> Optional[SkillMetadata]:
        """
        Parse a SKILL.md file and extract metadata.

        Args:
            skill_file: Path to SKILL.md file

        Returns:
            SkillMetadata if parsing succeeds, None otherwise
        """
        try:
            content = skill_file.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not yaml_match:
                logger.warning(f"No YAML frontmatter in {skill_file}")
                # Use directory name as skill name
                skill_name = skill_file.parent.name
                return SkillMetadata(
                    name=skill_name,
                    path=skill_file,
                    description=f"Skill: {skill_name}",
                    triggers=[skill_name]
                )

            # Parse YAML
            yaml_str = yaml_match.group(1)
            yaml_data = yaml.safe_load(yaml_str)

            # Extract metadata
            name = yaml_data.get("name", skill_file.parent.name)
            description = yaml_data.get("description", "")

            # Extract triggers from various sources
            triggers = []

            # Add explicit triggers if present
            if "triggers" in yaml_data:
                triggers.extend(yaml_data["triggers"])

            # Add name as trigger
            triggers.append(name)

            # Extract from description
            triggers.extend(self._extract_triggers_from_description(description))

            # Extract dependencies
            dependencies = yaml_data.get("dependencies", [])
            if isinstance(dependencies, str):
                dependencies = [dep.strip() for dep in dependencies.split(",")]

            # Create metadata
            return SkillMetadata(
                name=name,
                path=skill_file,
                description=description,
                triggers=triggers,
                dependencies=dependencies,
                priority=yaml_data.get("priority", 50),
                usage_count=0,  # Will be enriched from analytics
                success_rate=1.0,
                last_used=None
            )

        except Exception as e:
            logger.error(f"Error parsing {skill_file}: {e}")
            return None

    def _extract_triggers_from_description(self, description: str) -> List[str]:
        """
        Extract potential trigger keywords from description.

        Looks for framework names, technology names, and key concepts.

        Args:
            description: Skill description text

        Returns:
            List of extracted trigger keywords
        """
        triggers = []
        description_lower = description.lower()

        # Check for known frameworks/technologies
        for framework, aliases in self.FRAMEWORK_ALIASES.items():
            for alias in aliases:
                if alias in description_lower:
                    triggers.append(framework)
                    break

        # Extract capitalized words (likely framework/library names)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\.[a-z]+)?\b', description)
        triggers.extend([word.lower() for word in capitalized])

        return list(set(triggers))  # Remove duplicates

    def _enrich_with_analytics(self, skills: List[SkillMetadata]) -> None:
        """
        Enrich skill metadata with analytics data.

        Updates usage_count, success_rate, and last_used from analytics.

        Args:
            skills: List of SkillMetadata to enrich
        """
        skill_usage = self.analytics.get("skill_usage", {})

        for skill in skills:
            if skill.name in skill_usage:
                usage_data = skill_usage[skill.name]
                skill.usage_count = usage_data.get("count", 0)
                skill.success_rate = usage_data.get("success_rate", 1.0)

                # Parse last_used timestamp
                last_used_str = usage_data.get("last_used")
                if last_used_str:
                    try:
                        skill.last_used = datetime.fromisoformat(last_used_str)
                    except ValueError:
                        pass

    def _discover_explicit_matches(self, intent: Intent) -> List[tuple[SkillMetadata, float]]:
        """
        Find skills explicitly mentioned in the intent.

        Returns list of (SkillMetadata, confidence) tuples.
        """
        matches = []

        # Check each entity
        for entity in intent.entities:
            skill = self.find_skill_for_entity(entity)
            if skill:
                # High confidence for explicit matches
                matches.append((skill, 1.0))

        return matches

    def _discover_pattern_matches(self, intent: Intent) -> List[tuple[SkillMetadata, float]]:
        """
        Find skills suggested by learned patterns.

        Returns list of (SkillMetadata, pattern_confidence) tuples.
        """
        matches = []

        # Get patterns from intent
        for pattern in intent.patterns:
            skills = pattern.get("skills", [])
            confidence = pattern.get("confidence", 0.5)

            for skill_name in skills:
                if skill_name in self.cache:
                    matches.append((self.cache[skill_name], confidence))

        # Also check learned patterns
        for pattern_name, pattern_data in self.patterns.items():
            # Simple matching - check if pattern keywords in intent
            pattern_keywords = pattern_data.get("keywords", [])
            if any(keyword.lower() in intent.text.lower() for keyword in pattern_keywords):
                skills = pattern_data.get("skills", [])
                confidence = pattern_data.get("confidence", 0.5)

                for skill_name in skills:
                    if skill_name in self.cache:
                        matches.append((self.cache[skill_name], confidence))

        return matches

    def _discover_domain_matches(self, intent: Intent) -> List[SkillMetadata]:
        """Find skills that match the intent's domain."""
        if not intent.domain:
            return []

        return self.get_domain_skills(intent.domain)

    def _discover_dependencies(self, discovered: List[DiscoveredSkill]) -> List[SkillMetadata]:
        """
        Find dependency skills for already discovered skills.

        Args:
            discovered: List of already discovered skills

        Returns:
            List of dependency SkillMetadata
        """
        dependencies = []

        for ds in discovered:
            for dep_name in ds.skill.dependencies:
                if dep_name in self.cache:
                    dependencies.append(self.cache[dep_name])

        return dependencies

    def _apply_user_preferences(self, discovered: List[DiscoveredSkill]) -> List[DiscoveredSkill]:
        """
        Filter and adjust skills based on user preferences.

        Args:
            discovered: List of discovered skills

        Returns:
            Filtered/adjusted list of discovered skills
        """
        # Get user preferences
        preferences = self.user_profile.get("preferences", {})

        # Check for disabled skills
        disabled_skills = preferences.get("disabled_skills", [])

        # Filter out disabled skills
        filtered = [
            ds for ds in discovered
            if ds.skill.name not in disabled_skills
        ]

        # Boost priority for preferred skills
        preferred_skills = preferences.get("preferred_skills", [])
        for ds in filtered:
            if ds.skill.name in preferred_skills:
                ds.priority = min(100, ds.priority + 10)  # Boost by 10

        return filtered

    def _get_entity_aliases(self, entity: str) -> List[str]:
        """
        Get all aliases for an entity.

        Args:
            entity: Entity name (normalized/lowercase)

        Returns:
            List of aliases including the entity itself
        """
        entity_lower = entity.lower()

        # Check if entity is in aliases
        for framework, aliases in self.FRAMEWORK_ALIASES.items():
            if entity_lower in aliases or entity_lower == framework:
                return aliases + [framework]

        # Return entity itself
        return [entity_lower]

    # Aliases for backward compatibility
    def discover_skills(
        self,
        intent,  # Can be Intent or dict
        sort_by_usage: bool = False,
        resolve_dependencies: bool = False,
        filter_by_profile: bool = False,
        max_token_budget: Optional[int] = None,
        **kwargs
    ) -> List[DiscoveredSkill]:
        """
        Alias for discover() method - for backward compatibility.

        Supports both Intent objects and dict inputs for flexibility.

        Args:
            intent: User intent (Intent object or dict with 'entities', 'domain', etc.)
            sort_by_usage: Whether to sort results by usage analytics (ignored for now)
            resolve_dependencies: Whether to include dependency skills (ignored for now)
            filter_by_profile: Whether to filter by user profile (ignored for now)
            max_token_budget: Maximum token budget (ignored for now)
            **kwargs: Additional arguments (ignored for backward compat)

        Returns:
            List of DiscoveredSkill objects, sorted by priority (descending)
        """
        # Handle dict input - convert to Intent-like object
        if isinstance(intent, dict):
            from skillforge.analyzers.intent_analyzer import Intent as IntentClass
            intent = IntentClass(
                entities=intent.get('entities', []),
                action=intent.get('action', ''),
                domain=intent.get('domain', ''),
                complexity=intent.get('complexity', ''),
                patterns=intent.get('patterns', []),
                confidence=intent.get('confidence', 0.0),
                raw_request=intent.get('text', intent.get('raw_request', '')),
                metadata=intent.get('metadata', {})
            )

        return self.discover(intent)

    def discover_by_explicit_mention(self, intent: Intent) -> List[DiscoveredSkill]:
        """
        Discover skills explicitly mentioned in the intent.

        Args:
            intent: User intent

        Returns:
            List of explicitly discovered skills
        """
        matches = self._discover_explicit_matches(intent)
        discovered = []
        for skill_meta, confidence in matches:
            discovered.append(DiscoveredSkill(
                skill=skill_meta,
                priority=100,
                reason="explicit",
                confidence=confidence
            ))
        return discovered

    def discover_by_pattern(self, intent: Intent) -> List[DiscoveredSkill]:
        """
        Discover skills based on learned patterns.

        Args:
            intent: User intent

        Returns:
            List of pattern-based discovered skills
        """
        matches = self._discover_pattern_matches(intent)
        discovered = []
        for skill_meta, pattern_confidence in matches:
            priority = int(70 + (pattern_confidence * 20))  # 70-90
            discovered.append(DiscoveredSkill(
                skill=skill_meta,
                priority=priority,
                reason="pattern",
                confidence=pattern_confidence
            ))
        return discovered

    def discover_by_domain(self, intent: Intent) -> List[DiscoveredSkill]:
        """
        Discover skills based on domain matching.

        Args:
            intent: User intent

        Returns:
            List of domain-based discovered skills
        """
        domain_skills = self._discover_domain_matches(intent)
        discovered = []
        for skill_meta in domain_skills:
            discovered.append(DiscoveredSkill(
                skill=skill_meta,
                priority=60,
                reason="domain",
                confidence=0.7
            ))
        return discovered

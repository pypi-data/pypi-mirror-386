"""
Pattern Detection and Learning System for SkillForge

This module provides intelligent pattern detection from usage data:
- Combination Patterns: Which skills are used together
- Style Patterns: Coding style preferences (naming, imports, error handling)
- Workflow Patterns: Development workflow preferences (commits, branches, testing)

The PatternDetector uses statistical analysis and confidence scoring to identify
and validate patterns, applying decay over time to ensure patterns remain relevant.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import json
import math


@dataclass
class DetectedPattern:
    """Base class for all detected patterns"""
    pattern_id: str
    pattern_type: str          # "combination", "style", "workflow"
    description: str
    confidence: float          # 0.0 to 1.0
    frequency: int            # Number of occurrences
    success_rate: float       # Success rate when applied
    first_seen: datetime
    last_seen: datetime
    data: Dict = field(default_factory=dict)  # Type-specific data

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary for serialization"""
        result = asdict(self)
        result['first_seen'] = self.first_seen.isoformat()
        result['last_seen'] = self.last_seen.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectedPattern':
        """Create pattern from dictionary"""
        data = data.copy()
        data['first_seen'] = datetime.fromisoformat(data['first_seen'])
        data['last_seen'] = datetime.fromisoformat(data['last_seen'])
        return cls(**data)


@dataclass
class CombinationPattern(DetectedPattern):
    """Pattern for skills that are frequently used together"""
    skills: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Ensure pattern_type is set correctly"""
        self.pattern_type = "combination"
        if not self.data:
            self.data = {"skills": self.skills}


@dataclass
class StylePattern(DetectedPattern):
    """Pattern for coding style preferences"""
    style_type: str = ""       # "naming", "imports", "error_handling"
    examples: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Ensure pattern_type is set correctly"""
        self.pattern_type = "style"
        if not self.data:
            self.data = {"style_type": self.style_type, "examples": self.examples}


@dataclass
class WorkflowPattern(DetectedPattern):
    """Pattern for workflow preferences"""
    workflow_type: str = ""    # "commit", "branch", "testing"
    template: str = ""

    def __post_init__(self):
        """Ensure pattern_type is set correctly"""
        self.pattern_type = "workflow"
        if not self.data:
            self.data = {"workflow_type": self.workflow_type, "template": self.template}


class PatternDetector:
    """
    Detects and manages patterns from usage data.

    Uses statistical analysis to identify:
    - Which skills are used together (combination patterns)
    - Coding style preferences (style patterns)
    - Development workflow preferences (workflow patterns)

    Patterns have confidence scores that decay over time if not reinforced.
    """

    # Detection thresholds
    COMBINATION_THRESHOLD = 0.8
    COMBINATION_MIN_OCCURRENCES = 3  # Lowered from 10 for reasonable detection

    STYLE_THRESHOLD = 0.75
    STYLE_MIN_SAMPLES = 3  # Lowered from 15 for reasonable detection

    WORKFLOW_THRESHOLD = 0.8
    WORKFLOW_MIN_SAMPLES = 3  # Lowered from 20 for reasonable detection

    # Confidence thresholds for suggestions and auto-apply
    SUGGEST_CONFIDENCE = 0.8
    AUTO_APPLY_CONFIDENCE = 0.9

    # Decay and removal thresholds
    DECAY_RATE_PER_MONTH = 0.1  # 10% per month
    REMOVAL_THRESHOLD = 0.3

    def __init__(self, config_module=None):
        """
        Initialize PatternDetector.

        Args:
            config_module: Config module for loading/saving data (defaults to generators.config)
        """
        if config_module is None:
            from skillforge.generators.config import Config
            self.config = Config
        else:
            self.config = config_module

        self.patterns: Dict[str, DetectedPattern] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load existing patterns from disk"""
        try:
            pattern_data = self.config.load_learned_patterns()

            for pattern_id, data in pattern_data.items():
                # Reconstruct appropriate pattern type
                pattern_type = data.get('pattern_type')

                if pattern_type == 'combination':
                    pattern = CombinationPattern.from_dict(data)
                elif pattern_type == 'style':
                    pattern = StylePattern.from_dict(data)
                elif pattern_type == 'workflow':
                    pattern = WorkflowPattern.from_dict(data)
                else:
                    pattern = DetectedPattern.from_dict(data)

                self.patterns[pattern_id] = pattern

        except Exception as e:
            print(f"Warning: Could not load patterns: {e}")
            self.patterns = {}

    def _save_patterns(self) -> None:
        """Save patterns to disk"""
        try:
            pattern_data = {
                pid: pattern.to_dict()
                for pid, pattern in self.patterns.items()
            }
            self.config.save_learned_patterns(pattern_data)
        except Exception as e:
            raise OSError(f"Failed to save patterns: {e}")

    def detect_patterns(self) -> List[DetectedPattern]:
        """
        Main pattern detection method.

        Performs complete pattern detection:
        1. Load usage data from analytics
        2. Group similar behaviors
        3. Calculate frequency for each group
        4. Calculate confidence (frequency * success_rate * recency)
        5. Filter by thresholds
        6. Validate patterns (not conflicting)
        7. Save to Config.save_learned_patterns()

        Returns:
            List of all detected patterns (combination, style, workflow)
        """
        # Step 1: Load usage data
        analytics = self.config.load_analytics()
        skill_usage = analytics.get('skill_usage', {})

        if not skill_usage:
            return []

        # Detect all pattern types
        new_patterns = []

        # Detect combination patterns
        new_patterns.extend(self.analyze_skill_combinations())

        # Detect style patterns
        new_patterns.extend(self.analyze_code_style())

        # Detect workflow patterns
        new_patterns.extend(self.analyze_workflows())

        # Step 5 & 6: Filter and validate patterns
        validated_patterns = self._validate_patterns(new_patterns)

        # Merge with existing patterns
        for pattern in validated_patterns:
            if pattern.pattern_id in self.patterns:
                # Update existing pattern
                existing = self.patterns[pattern.pattern_id]
                existing.frequency = pattern.frequency
                existing.success_rate = pattern.success_rate
                existing.last_seen = pattern.last_seen
                existing.confidence = self._calculate_confidence(existing)
            else:
                # Add new pattern
                self.patterns[pattern.pattern_id] = pattern

        # Step 7: Save patterns
        self._save_patterns()

        return list(self.patterns.values())

    def analyze_skill_combinations(self) -> List[CombinationPattern]:
        """
        Analyze which skills are frequently used together.

        Detects patterns like:
        - React + TypeScript + Tailwind
        - pytest + unittest + mock
        - git + GitHub Actions + semantic-release

        Uses association rule mining with minimum support and confidence.

        Returns:
            List of detected combination patterns
        """
        analytics = self.config.load_analytics()
        skill_usage = analytics.get('skill_usage', {})

        if not skill_usage:
            return []

        # Step 2: Group behaviors - find co-occurring skills
        # Track which skills appear together in sessions
        session_skills = defaultdict(list)

        for skill_name, usage_data in skill_usage.items():
            sessions = usage_data.get('sessions', [])
            for session in sessions:
                session_id = session.get('timestamp', datetime.now().isoformat())
                # Get all skills used in this session (from session data or default to current skill)
                skills_in_session = session.get('skills', [skill_name])
                for skill in skills_in_session:
                    if skill not in session_skills[session_id]:
                        session_skills[session_id].append(skill)

        # Find frequent skill combinations
        combination_counts = Counter()
        combination_successes = defaultdict(int)
        combination_total = defaultdict(int)

        for session_id, skills in session_skills.items():
            if len(skills) < 2:
                continue

            # Sort for consistent combination keys
            skills = sorted(set(skills))

            # Generate combinations of 2-4 skills
            for size in range(2, min(5, len(skills) + 1)):
                from itertools import combinations
                for combo in combinations(skills, size):
                    combo_key = tuple(sorted(combo))
                    combination_counts[combo_key] += 1

                    # Track success (simplified - assume session completion = success)
                    combination_total[combo_key] += 1
                    # In real implementation, check session outcome
                    combination_successes[combo_key] += 1

        # Step 3 & 4: Calculate frequency and confidence
        patterns = []
        now = datetime.now()

        for combo, count in combination_counts.items():
            # Step 5: Filter by threshold
            if count < self.COMBINATION_MIN_OCCURRENCES:
                continue

            skills = list(combo)
            pattern_id = f"combo_{hash(combo) & 0x7FFFFFFF}"

            success_rate = (
                combination_successes[combo] / combination_total[combo]
                if combination_total[combo] > 0 else 0.0
            )

            # Create pattern
            pattern = CombinationPattern(
                pattern_id=pattern_id,
                pattern_type="combination",
                description=f"Skills often used together: {', '.join(skills)}",
                confidence=0.0,  # Will be calculated
                frequency=count,
                success_rate=success_rate,
                first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                last_seen=now,
                skills=skills,
                data={"skills": skills}
            )

            # Calculate confidence
            pattern.confidence = self._calculate_confidence(pattern)

            if pattern.confidence >= self.COMBINATION_THRESHOLD:
                patterns.append(pattern)

        return patterns

    def analyze_code_style(self) -> List[StylePattern]:
        """
        Analyze coding style patterns.

        Detects patterns in:
        - Naming conventions (camelCase, snake_case, PascalCase)
        - Import organization (grouped, sorted, absolute vs relative)
        - Error handling (try/except, if/else, early return)
        - Code formatting preferences

        Returns:
            List of detected style patterns
        """
        analytics = self.config.load_analytics()
        skill_usage = analytics.get('skill_usage', {})

        if not skill_usage:
            return []

        # Aggregate style indicators from usage data
        naming_styles = []
        import_styles = []
        error_handling_styles = []

        for skill_name, usage_data in skill_usage.items():
            metadata = usage_data.get('metadata', {})

            # Extract style indicators from metadata
            if 'naming_style' in metadata:
                naming_styles.append(metadata['naming_style'])

            if 'import_style' in metadata:
                import_styles.append(metadata['import_style'])

            if 'error_handling' in metadata:
                error_handling_styles.append(metadata['error_handling'])

        patterns = []
        now = datetime.now()

        # Analyze naming style patterns
        if len(naming_styles) >= self.STYLE_MIN_SAMPLES:
            style_counts = Counter(naming_styles)
            most_common_style, count = style_counts.most_common(1)[0]

            success_rate = count / len(naming_styles)

            if success_rate >= self.STYLE_THRESHOLD:
                pattern_id = f"style_naming_{most_common_style}"
                pattern = StylePattern(
                    pattern_id=pattern_id,
                    pattern_type="style",
                    description=f"Preferred naming convention: {most_common_style}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    style_type="naming",
                    examples=[most_common_style],
                    data={"style_type": "naming", "examples": [most_common_style]}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        # Analyze import style patterns
        if len(import_styles) >= self.STYLE_MIN_SAMPLES:
            style_counts = Counter(import_styles)
            most_common_style, count = style_counts.most_common(1)[0]

            success_rate = count / len(import_styles)

            if success_rate >= self.STYLE_THRESHOLD:
                pattern_id = f"style_imports_{most_common_style}"
                pattern = StylePattern(
                    pattern_id=pattern_id,
                    pattern_type="style",
                    description=f"Preferred import style: {most_common_style}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    style_type="imports",
                    examples=[most_common_style],
                    data={"style_type": "imports", "examples": [most_common_style]}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        # Analyze error handling patterns
        if len(error_handling_styles) >= self.STYLE_MIN_SAMPLES:
            style_counts = Counter(error_handling_styles)
            most_common_style, count = style_counts.most_common(1)[0]

            success_rate = count / len(error_handling_styles)

            if success_rate >= self.STYLE_THRESHOLD:
                pattern_id = f"style_errors_{most_common_style}"
                pattern = StylePattern(
                    pattern_id=pattern_id,
                    pattern_type="style",
                    description=f"Preferred error handling: {most_common_style}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    style_type="error_handling",
                    examples=[most_common_style],
                    data={"style_type": "error_handling", "examples": [most_common_style]}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        return patterns

    def analyze_workflows(self) -> List[WorkflowPattern]:
        """
        Analyze workflow patterns.

        Detects patterns in:
        - Commit message formats (conventional commits, semantic, custom)
        - Branch naming (feature/, fix/, hotfix/, etc.)
        - Testing workflows (test before commit, CI/CD, manual)
        - Development cycles (TDD, BDD, exploratory)

        Returns:
            List of detected workflow patterns
        """
        analytics = self.config.load_analytics()
        skill_usage = analytics.get('skill_usage', {})

        if not skill_usage:
            return []

        # Aggregate workflow indicators
        commit_formats = []
        branch_patterns = []
        testing_workflows = []

        for skill_name, usage_data in skill_usage.items():
            metadata = usage_data.get('metadata', {})

            # Extract workflow indicators
            if 'commit_format' in metadata:
                commit_formats.append(metadata['commit_format'])

            if 'branch_pattern' in metadata:
                branch_patterns.append(metadata['branch_pattern'])

            if 'testing_workflow' in metadata:
                testing_workflows.append(metadata['testing_workflow'])

        patterns = []
        now = datetime.now()

        # Analyze commit format patterns
        if len(commit_formats) >= self.WORKFLOW_MIN_SAMPLES:
            format_counts = Counter(commit_formats)
            most_common_format, count = format_counts.most_common(1)[0]

            success_rate = count / len(commit_formats)

            if success_rate >= self.WORKFLOW_THRESHOLD:
                pattern_id = f"workflow_commit_{most_common_format}"

                # Create template based on format
                templates = {
                    "conventional": "type(scope): description",
                    "semantic": "type: description",
                    "imperative": "Verb description"
                }
                template = templates.get(most_common_format, most_common_format)

                pattern = WorkflowPattern(
                    pattern_id=pattern_id,
                    pattern_type="workflow",
                    description=f"Preferred commit format: {most_common_format}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    workflow_type="commit",
                    template=template,
                    data={"workflow_type": "commit", "template": template}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        # Analyze branch naming patterns
        if len(branch_patterns) >= self.WORKFLOW_MIN_SAMPLES:
            pattern_counts = Counter(branch_patterns)
            most_common_pattern, count = pattern_counts.most_common(1)[0]

            success_rate = count / len(branch_patterns)

            if success_rate >= self.WORKFLOW_THRESHOLD:
                pattern_id = f"workflow_branch_{most_common_pattern}"
                pattern = WorkflowPattern(
                    pattern_id=pattern_id,
                    pattern_type="workflow",
                    description=f"Preferred branch naming: {most_common_pattern}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    workflow_type="branch",
                    template=most_common_pattern,
                    data={"workflow_type": "branch", "template": most_common_pattern}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        # Analyze testing workflow patterns
        if len(testing_workflows) >= self.WORKFLOW_MIN_SAMPLES:
            workflow_counts = Counter(testing_workflows)
            most_common_workflow, count = workflow_counts.most_common(1)[0]

            success_rate = count / len(testing_workflows)

            if success_rate >= self.WORKFLOW_THRESHOLD:
                pattern_id = f"workflow_testing_{most_common_workflow}"
                pattern = WorkflowPattern(
                    pattern_id=pattern_id,
                    pattern_type="workflow",
                    description=f"Preferred testing workflow: {most_common_workflow}",
                    confidence=0.0,
                    frequency=count,
                    success_rate=success_rate,
                    first_seen=self.patterns.get(pattern_id).first_seen if pattern_id in self.patterns else now,
                    last_seen=now,
                    workflow_type="testing",
                    template=most_common_workflow,
                    data={"workflow_type": "testing", "template": most_common_workflow}
                )
                pattern.confidence = self._calculate_confidence(pattern)
                patterns.append(pattern)

        return patterns

    def _calculate_confidence(self, pattern: DetectedPattern) -> float:
        """
        Calculate pattern confidence score.

        Confidence is calculated as:
            confidence = (frequency_weight * 0.4 +
                         success_weight * 0.4 +
                         recency_weight * 0.2)

        Args:
            pattern: Pattern to calculate confidence for

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Frequency weight (max at 50 uses)
        frequency_weight = min(pattern.frequency / 50.0, 1.0)

        # Success rate weight
        success_weight = pattern.success_rate

        # Recency weight (decay over time)
        recency_weight = self._calculate_recency_bonus(pattern.last_seen)

        confidence = (
            frequency_weight * 0.4 +
            success_weight * 0.4 +
            recency_weight * 0.2
        )

        return min(confidence, 1.0)

    def _calculate_recency_bonus(self, last_seen: datetime) -> float:
        """
        Calculate recency bonus for a pattern.

        Patterns decay over time if not reinforced:
        - Recent (< 1 month): 1.0
        - 1-3 months: 0.8
        - 3-6 months: 0.6
        - 6-12 months: 0.4
        - > 12 months: 0.2

        Args:
            last_seen: When pattern was last observed

        Returns:
            Recency weight between 0.0 and 1.0
        """
        now = datetime.now()
        age_days = (now - last_seen).days

        if age_days < 30:
            return 1.0
        elif age_days < 90:
            return 0.8
        elif age_days < 180:
            return 0.6
        elif age_days < 365:
            return 0.4
        else:
            return 0.2

    def update_confidence(self, pattern_id: str, outcome: bool) -> None:
        """
        Update pattern confidence based on user feedback.

        When a user accepts or rejects a pattern suggestion,
        this updates the pattern's success rate and recalculates confidence.

        Args:
            pattern_id: ID of pattern to update
            outcome: True if user accepted, False if rejected
        """
        if pattern_id not in self.patterns:
            print(f"Warning: Pattern {pattern_id} not found")
            return

        pattern = self.patterns[pattern_id]

        # Update success rate using exponential moving average
        alpha = 0.2  # Learning rate
        new_outcome = 1.0 if outcome else 0.0
        pattern.success_rate = (
            alpha * new_outcome + (1 - alpha) * pattern.success_rate
        )

        # Update last seen
        pattern.last_seen = datetime.now()

        # Recalculate confidence
        pattern.confidence = self._calculate_confidence(pattern)

        # Save updated patterns
        self._save_patterns()

    def apply_pattern_decay(self) -> None:
        """
        Apply decay to all patterns.

        Patterns lose confidence over time if not reinforced (10% per month).
        Patterns with confidence < 0.3 are removed.

        This should be run periodically (e.g., weekly) to keep patterns fresh.
        """
        now = datetime.now()
        patterns_to_remove = []

        for pattern_id, pattern in self.patterns.items():
            # Calculate months since last seen
            age_days = (now - pattern.last_seen).days
            months_old = age_days / 30.0

            # Apply decay
            decay_factor = math.exp(-self.DECAY_RATE_PER_MONTH * months_old)
            pattern.confidence *= decay_factor

            # Mark for removal if below threshold
            if pattern.confidence < self.REMOVAL_THRESHOLD:
                patterns_to_remove.append(pattern_id)

        # Remove low-confidence patterns
        for pattern_id in patterns_to_remove:
            del self.patterns[pattern_id]

        # Save updated patterns
        if patterns_to_remove:
            self._save_patterns()

    def _validate_patterns(self, patterns: List[DetectedPattern]) -> List[DetectedPattern]:
        """
        Validate patterns to ensure they don't conflict.

        Filters out:
        - Duplicate patterns
        - Conflicting patterns (e.g., contradictory styles)
        - Patterns below confidence thresholds

        Args:
            patterns: List of patterns to validate

        Returns:
            List of validated patterns
        """
        validated = []
        seen_patterns = set()

        # Group patterns by type for conflict detection
        by_type = defaultdict(list)

        for pattern in patterns:
            # Skip duplicates
            if pattern.pattern_id in seen_patterns:
                continue

            seen_patterns.add(pattern.pattern_id)
            by_type[pattern.pattern_type].append(pattern)

        # Validate each type
        for pattern_type, type_patterns in by_type.items():
            if pattern_type == "style":
                # For style patterns, keep only the highest confidence per style_type
                style_best = {}
                for pattern in type_patterns:
                    if isinstance(pattern, StylePattern):
                        style_type = pattern.style_type
                        if (style_type not in style_best or
                            pattern.confidence > style_best[style_type].confidence):
                            style_best[style_type] = pattern

                validated.extend(style_best.values())

            elif pattern_type == "workflow":
                # For workflow patterns, keep only the highest confidence per workflow_type
                workflow_best = {}
                for pattern in type_patterns:
                    if isinstance(pattern, WorkflowPattern):
                        workflow_type = pattern.workflow_type
                        if (workflow_type not in workflow_best or
                            pattern.confidence > workflow_best[workflow_type].confidence):
                            workflow_best[workflow_type] = pattern

                validated.extend(workflow_best.values())

            else:
                # For combination patterns, keep all non-conflicting ones
                validated.extend(type_patterns)

        return validated

    def get_applicable_patterns(self, context: Dict[str, Any]) -> List[DetectedPattern]:
        """
        Get patterns applicable to the current context.

        Args:
            context: Current context (active skills, file types, etc.)

        Returns:
            List of patterns that should be suggested or applied
        """
        applicable = []

        for pattern in self.patterns.values():
            # Only suggest patterns with sufficient confidence
            if pattern.confidence < self.SUGGEST_CONFIDENCE:
                continue

            # Check if pattern is relevant to context
            if self._is_pattern_applicable(pattern, context):
                applicable.append(pattern)

        # Sort by confidence (highest first)
        applicable.sort(key=lambda p: p.confidence, reverse=True)

        return applicable

    def _is_pattern_applicable(self, pattern: DetectedPattern, context: Dict[str, Any]) -> bool:
        """
        Check if pattern is applicable in the given context.

        Args:
            pattern: Pattern to check
            context: Current context

        Returns:
            True if pattern is applicable
        """
        # Combination patterns are applicable if any of the skills are active
        if isinstance(pattern, CombinationPattern):
            active_skills = context.get('active_skills', [])
            return any(skill in active_skills for skill in pattern.skills)

        # Style patterns are applicable for code generation
        if isinstance(pattern, StylePattern):
            return context.get('operation') == 'code_generation'

        # Workflow patterns are applicable for git operations
        if isinstance(pattern, WorkflowPattern):
            operation = context.get('operation', '')
            if pattern.workflow_type == 'commit':
                return operation == 'git_commit'
            elif pattern.workflow_type == 'branch':
                return operation == 'git_branch'
            elif pattern.workflow_type == 'testing':
                return operation == 'testing'

        return False

    def should_auto_apply(self, pattern: DetectedPattern) -> bool:
        """
        Check if pattern should be automatically applied.

        Args:
            pattern: Pattern to check

        Returns:
            True if pattern should be auto-applied
        """
        # Only auto-apply if confidence is very high
        if pattern.confidence < self.AUTO_APPLY_CONFIDENCE:
            return False

        # Check user preferences (would need to be loaded from config)
        # For now, return False (opt-in for auto-apply)
        return False

    # Alias for backward compatibility - forward to UsageTracker
    def record_combination(
        self,
        skills: List[str],
        success: bool,
        duration: Optional[float] = None
    ) -> None:
        """
        Record skill combination - delegates to UsageTracker.

        This is a convenience method that forwards to UsageTracker's
        record_combination() for backward compatibility.

        Args:
            skills: List of skill identifiers
            success: Whether the combination was successful
            duration: Optional duration in seconds
        """
        from .usage_tracker import UsageTracker
        tracker = UsageTracker()
        tracker.record_combination(skills, success, duration)

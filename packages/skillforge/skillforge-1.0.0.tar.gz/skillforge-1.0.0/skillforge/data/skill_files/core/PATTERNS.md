# PATTERNS.md

## Overview

SkillForge's pattern detection system learns from user behavior to provide increasingly personalized and accurate assistance. This document defines how patterns are detected, stored, analyzed, and applied.

## 1. Pattern Detection

### What are Patterns?

Patterns are recurring behaviors, preferences, or structures in a user's work that can be detected, learned, and applied to improve future assistance. Patterns represent the "how" behind user preferences.

### Four Types of Patterns

#### 1.1 Usage Patterns
Frequency and timing of skill/tool usage.

```json
{
  "pattern_type": "usage",
  "pattern_id": "usage_pytest_preferred",
  "description": "User consistently chooses pytest over unittest",
  "metrics": {
    "pytest_usage_count": 47,
    "unittest_usage_count": 2,
    "preference_ratio": 0.96,
    "temporal_consistency": 0.89
  },
  "confidence": 0.92,
  "first_detected": "2025-01-15T10:30:00Z",
  "last_reinforced": "2025-01-22T14:20:00Z"
}
```

#### 1.2 Code Style Patterns
Preferences in code structure and formatting.

```json
{
  "pattern_type": "code_style",
  "pattern_id": "style_double_quotes",
  "description": "User prefers double quotes for strings",
  "metrics": {
    "double_quote_count": 156,
    "single_quote_count": 12,
    "preference_ratio": 0.93,
    "contexts": ["function_args", "dict_keys", "strings"]
  },
  "confidence": 0.88,
  "examples": [
    "print(\"Hello, world!\")",
    "config = {\"key\": \"value\"}"
  ]
}
```

#### 1.3 Workflow Patterns
Process and methodology preferences.

```json
{
  "pattern_type": "workflow",
  "pattern_id": "workflow_tdd",
  "description": "User follows test-driven development",
  "metrics": {
    "tests_before_impl_count": 23,
    "tests_after_impl_count": 3,
    "tdd_ratio": 0.88,
    "avg_test_first_time_delta": "-15m"
  },
  "confidence": 0.85,
  "sequence": ["write_test", "run_test", "implement", "refactor"]
}
```

#### 1.4 Combination Patterns
Complex patterns involving multiple dimensions.

```json
{
  "pattern_type": "combination",
  "pattern_id": "combo_api_testing",
  "description": "User uses FastAPI + pytest + httpx for API testing",
  "components": [
    "tool_fastapi",
    "tool_pytest",
    "tool_httpx"
  ],
  "co_occurrence_rate": 0.91,
  "confidence": 0.87,
  "contexts": ["web_development", "api_testing"]
}
```

### Detection Algorithms

#### Frequency-Based Detection

```python
def detect_frequency_pattern(events, threshold=0.75, min_samples=5):
    """
    Detect patterns based on frequency of occurrence.

    Args:
        events: List of events with timestamps and choices
        threshold: Minimum preference ratio to establish pattern
        min_samples: Minimum occurrences to consider

    Returns:
        Pattern object or None
    """
    if len(events) < min_samples:
        return None

    choice_counts = {}
    for event in events:
        choice = event['choice']
        choice_counts[choice] = choice_counts.get(choice, 0) + 1

    total = sum(choice_counts.values())
    max_choice = max(choice_counts.items(), key=lambda x: x[1])
    preference_ratio = max_choice[1] / total

    if preference_ratio >= threshold:
        return {
            'preferred_choice': max_choice[0],
            'preference_ratio': preference_ratio,
            'sample_size': total,
            'confidence': calculate_confidence(preference_ratio, total)
        }

    return None

def calculate_confidence(ratio, sample_size):
    """
    Calculate confidence score based on preference ratio and sample size.
    Uses Wilson score interval for binomial proportion.
    """
    import math

    z = 1.96  # 95% confidence
    p = ratio
    n = sample_size

    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2*n)) / denominator
    adjustment = z * math.sqrt((p*(1-p) + z**2/(4*n)) / n) / denominator

    lower_bound = centre - adjustment

    # Confidence is the lower bound of the interval
    return round(lower_bound, 3)
```

#### Temporal Consistency Detection

```python
from datetime import datetime, timedelta

def detect_temporal_consistency(events, time_window_days=30):
    """
    Detect if pattern is consistent over time.

    Args:
        events: List of events with timestamps
        time_window_days: Days to divide into windows

    Returns:
        Temporal consistency score (0-1)
    """
    if not events:
        return 0.0

    # Sort by timestamp
    sorted_events = sorted(events, key=lambda x: x['timestamp'])
    start = sorted_events[0]['timestamp']
    end = sorted_events[-1]['timestamp']

    # Divide into time windows
    window_size = timedelta(days=time_window_days)
    windows = []
    current = start

    while current < end:
        window_end = current + window_size
        window_events = [
            e for e in sorted_events
            if current <= e['timestamp'] < window_end
        ]
        if window_events:
            windows.append(window_events)
        current = window_end

    if len(windows) < 2:
        return 0.5  # Not enough time data

    # Calculate consistency across windows
    window_patterns = [detect_frequency_pattern(w) for w in windows]
    consistent_windows = sum(
        1 for p in window_patterns
        if p and p['preferred_choice'] == window_patterns[0]['preferred_choice']
    )

    return consistent_windows / len(windows)
```

#### Context-Aware Detection

```python
def detect_contextual_pattern(events, context_key):
    """
    Detect patterns within specific contexts.

    Args:
        events: List of events with context metadata
        context_key: Context dimension to analyze (e.g., 'project_type')

    Returns:
        Dict of context -> pattern mappings
    """
    context_groups = {}
    for event in events:
        context = event.get('context', {}).get(context_key, 'unknown')
        if context not in context_groups:
            context_groups[context] = []
        context_groups[context].append(event)

    patterns = {}
    for context, context_events in context_groups.items():
        pattern = detect_frequency_pattern(context_events)
        if pattern:
            patterns[context] = pattern

    return patterns
```

## 2. Data Collection

### What to Track

#### Skill Usage Events
```json
{
  "event_type": "skill_used",
  "timestamp": "2025-01-22T14:30:00Z",
  "skill_id": "python_write_test",
  "context": {
    "project_type": "web_api",
    "file_type": "test_*.py",
    "trigger": "explicit_request",
    "session_id": "sess_abc123"
  },
  "outcome": {
    "success": true,
    "user_modified": false,
    "execution_time_ms": 1250
  }
}
```

#### Code Generation Events
```json
{
  "event_type": "code_generated",
  "timestamp": "2025-01-22T14:31:00Z",
  "skill_id": "python_class_generator",
  "input": {
    "class_name": "UserRepository",
    "style_hints": ["dataclass", "type_hints"]
  },
  "output": {
    "code_length": 450,
    "style_markers": {
      "quote_style": "double",
      "import_style": "absolute",
      "typing_style": "full"
    }
  },
  "user_feedback": {
    "accepted": true,
    "modifications": []
  }
}
```

#### Tool Selection Events
```json
{
  "event_type": "tool_selected",
  "timestamp": "2025-01-22T14:32:00Z",
  "category": "testing_framework",
  "options_presented": ["pytest", "unittest", "nose2"],
  "user_choice": "pytest",
  "context": {
    "project_type": "web_api",
    "existing_tools": ["fastapi", "pydantic"]
  }
}
```

#### Workflow Events
```json
{
  "event_type": "workflow_step",
  "timestamp": "2025-01-22T14:35:00Z",
  "workflow": "feature_development",
  "step": "create_test",
  "sequence_position": 1,
  "session_id": "sess_abc123",
  "metadata": {
    "branch_created": true,
    "commit_before_test": false
  }
}
```

### When to Track

1. **Explicit Skill Invocation**: When user directly calls a skill
2. **Automatic Skill Selection**: When system chooses a skill based on context
3. **Code Acceptance**: When user accepts or modifies generated code
4. **Tool Installation/Usage**: When user installs or configures a tool
5. **Workflow Milestones**: Git commits, PR creation, test runs
6. **Configuration Changes**: When user modifies skill parameters

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SkillForge Event Schema",
  "type": "object",
  "required": ["event_id", "event_type", "timestamp", "user_id"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique event identifier"
    },
    "event_type": {
      "type": "string",
      "enum": [
        "skill_used",
        "code_generated",
        "tool_selected",
        "workflow_step",
        "configuration_changed",
        "feedback_provided"
      ]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "user_id": {
      "type": "string",
      "description": "Hashed user identifier"
    },
    "session_id": {
      "type": "string",
      "description": "Current session identifier"
    },
    "skill_id": {
      "type": "string",
      "description": "Skill identifier if applicable"
    },
    "context": {
      "type": "object",
      "properties": {
        "project_type": {"type": "string"},
        "file_type": {"type": "string"},
        "trigger": {"type": "string"},
        "language": {"type": "string"},
        "framework": {"type": "string"}
      }
    },
    "data": {
      "type": "object",
      "description": "Event-specific data"
    },
    "outcome": {
      "type": "object",
      "properties": {
        "success": {"type": "boolean"},
        "error_type": {"type": "string"},
        "user_modified": {"type": "boolean"}
      }
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata"
    }
  }
}
```

### Privacy Considerations

1. **No PII Collection**: Never collect names, emails, or identifiable information
2. **Code Privacy**: Only collect code patterns, not actual code content
3. **Hashed Identifiers**: User IDs are cryptographically hashed
4. **Local Storage**: All pattern data stored locally by default
5. **Opt-Out**: Users can disable pattern learning entirely
6. **Data Retention**: Configurable retention periods (default: 90 days)
7. **Anonymization**: Remove all identifying context before analysis

```python
import hashlib
from datetime import datetime, timedelta

class PrivacyFilter:
    """Ensure collected data respects privacy constraints."""

    SENSITIVE_FIELDS = ['user_name', 'email', 'ip_address', 'file_path']
    PII_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b'  # Credit card
    ]

    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """Create non-reversible hash of user identifier."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    @staticmethod
    def filter_event(event: dict) -> dict:
        """Remove sensitive information from event."""
        filtered = event.copy()

        # Remove sensitive fields
        for field in PrivacyFilter.SENSITIVE_FIELDS:
            filtered.pop(field, None)

        # Sanitize nested data
        if 'context' in filtered:
            filtered['context'] = PrivacyFilter._sanitize_context(
                filtered['context']
            )

        return filtered

    @staticmethod
    def _sanitize_context(context: dict) -> dict:
        """Remove identifying information from context."""
        sanitized = {}
        for key, value in context.items():
            if key == 'file_path':
                # Keep only file extension and type
                sanitized['file_type'] = value.split('.')[-1]
            elif key not in PrivacyFilter.SENSITIVE_FIELDS:
                sanitized[key] = value
        return sanitized
```

## 3. Pattern Analysis

### Statistical Methods

#### Chi-Square Test for Independence

```python
from scipy.stats import chi2_contingency
import numpy as np

def test_pattern_significance(observed_counts, expected_counts):
    """
    Test if observed pattern is statistically significant.

    Args:
        observed_counts: Dict of {choice: count}
        expected_counts: Dict of expected {choice: count} under null hypothesis

    Returns:
        (is_significant, p_value, chi2_statistic)
    """
    choices = list(observed_counts.keys())
    observed = [observed_counts[c] for c in choices]
    expected = [expected_counts.get(c, 0) for c in choices]

    if sum(expected) == 0:
        # Uniform distribution as null hypothesis
        total = sum(observed)
        expected = [total / len(choices)] * len(choices)

    # Create contingency table
    contingency = np.array([observed, expected])

    chi2, p_value, dof, expected_freq = chi2_contingency(contingency)

    # Significant at p < 0.05
    is_significant = p_value < 0.05

    return is_significant, p_value, chi2
```

#### Bayesian Confidence Updates

```python
class BayesianPatternLearner:
    """Update pattern confidence using Bayesian inference."""

    def __init__(self, prior_alpha=1, prior_beta=1):
        """
        Initialize with Beta distribution priors.

        Args:
            prior_alpha: Prior successes (default: 1 for uniform prior)
            prior_beta: Prior failures (default: 1 for uniform prior)
        """
        self.alpha = prior_alpha
        self.beta = prior_beta

    def update(self, successes, failures):
        """Update posterior distribution with new observations."""
        self.alpha += successes
        self.beta += failures

    def confidence(self):
        """Calculate expected value (mean of Beta distribution)."""
        return self.alpha / (self.alpha + self.beta)

    def credible_interval(self, confidence_level=0.95):
        """Calculate Bayesian credible interval."""
        from scipy.stats import beta
        dist = beta(self.alpha, self.beta)
        lower = dist.ppf((1 - confidence_level) / 2)
        upper = dist.ppf(1 - (1 - confidence_level) / 2)
        return lower, upper
```

### Confidence Thresholds

```python
class ConfidenceThresholds:
    """Define confidence levels for pattern application."""

    # Minimum confidence to consider pattern
    MIN_CONFIDENCE = 0.60

    # Confidence to auto-apply pattern
    AUTO_APPLY = 0.85

    # Confidence to suggest pattern
    SUGGEST = 0.70

    # Minimum sample size
    MIN_SAMPLES = 5

    # Temporal consistency threshold
    MIN_TEMPORAL_CONSISTENCY = 0.70

    @staticmethod
    def get_action(confidence, sample_size, temporal_consistency):
        """
        Determine action based on confidence metrics.

        Returns:
            'auto_apply', 'suggest', 'observe', or 'insufficient'
        """
        if sample_size < ConfidenceThresholds.MIN_SAMPLES:
            return 'insufficient'

        if confidence < ConfidenceThresholds.MIN_CONFIDENCE:
            return 'observe'

        if temporal_consistency < ConfidenceThresholds.MIN_TEMPORAL_CONSISTENCY:
            return 'observe'

        if confidence >= ConfidenceThresholds.AUTO_APPLY:
            return 'auto_apply'

        if confidence >= ConfidenceThresholds.SUGGEST:
            return 'suggest'

        return 'observe'
```

### Pattern Validation

```python
class PatternValidator:
    """Validate patterns before application."""

    @staticmethod
    def validate(pattern):
        """
        Comprehensive pattern validation.

        Returns:
            (is_valid, validation_errors)
        """
        errors = []

        # Check confidence
        if pattern.get('confidence', 0) < ConfidenceThresholds.MIN_CONFIDENCE:
            errors.append('Confidence below minimum threshold')

        # Check sample size
        sample_size = pattern.get('metrics', {}).get('sample_size', 0)
        if sample_size < ConfidenceThresholds.MIN_SAMPLES:
            errors.append(f'Insufficient samples: {sample_size}')

        # Check temporal validity
        last_reinforced = datetime.fromisoformat(
            pattern.get('last_reinforced', '1970-01-01T00:00:00Z')
        )
        days_since = (datetime.utcnow() - last_reinforced).days
        if days_since > 90:
            errors.append('Pattern is stale (>90 days)')

        # Check statistical significance
        if 'statistical_test' in pattern:
            if not pattern['statistical_test'].get('is_significant', False):
                errors.append('Pattern not statistically significant')

        return len(errors) == 0, errors

    @staticmethod
    def cross_validate(pattern, holdout_events):
        """
        Test pattern against holdout data.

        Returns:
            accuracy score (0-1)
        """
        if not holdout_events:
            return 0.0

        preferred_choice = pattern.get('preferred_choice')
        correct = sum(
            1 for event in holdout_events
            if event.get('choice') == preferred_choice
        )

        return correct / len(holdout_events)
```

### False Positive Handling

```python
class FalsePositiveDetector:
    """Detect and handle false positive patterns."""

    @staticmethod
    def detect_spurious_correlation(pattern, events):
        """
        Detect if pattern is spurious correlation.

        Checks:
        1. Sample size too small
        2. Recent change in behavior
        3. Context-dependent variance
        """
        issues = []

        # Check 1: Sample size
        if len(events) < 10:
            issues.append('small_sample')

        # Check 2: Recent change
        recent_events = [
            e for e in events
            if (datetime.utcnow() - e['timestamp']).days < 7
        ]
        if recent_events:
            recent_pattern = detect_frequency_pattern(recent_events)
            if recent_pattern and recent_pattern['preferred_choice'] != pattern.get('preferred_choice'):
                issues.append('recent_behavior_change')

        # Check 3: Context variance
        contexts = set(e.get('context', {}).get('project_type', 'unknown') for e in events)
        if len(contexts) > 1:
            context_patterns = detect_contextual_pattern(events, 'project_type')
            if len(set(p['preferred_choice'] for p in context_patterns.values())) > 1:
                issues.append('context_dependent')

        return issues

    @staticmethod
    def decay_pattern_confidence(pattern, decay_rate=0.05):
        """
        Decay confidence over time to handle changing preferences.

        Args:
            pattern: Pattern object
            decay_rate: Confidence reduction per day

        Returns:
            Updated confidence
        """
        last_reinforced = datetime.fromisoformat(pattern['last_reinforced'])
        days_since = (datetime.utcnow() - last_reinforced).days

        current_confidence = pattern['confidence']
        decayed_confidence = current_confidence * (1 - decay_rate) ** days_since

        return max(0.0, decayed_confidence)
```

## 4. Pattern Application

### How to Apply Learned Patterns

```python
class PatternApplicator:
    """Apply learned patterns to enhance skills."""

    def __init__(self, pattern_store):
        self.pattern_store = pattern_store

    def apply_to_skill(self, skill_id, context):
        """
        Apply relevant patterns to skill execution.

        Args:
            skill_id: Skill being executed
            context: Current execution context

        Returns:
            Modified skill parameters
        """
        patterns = self.pattern_store.get_patterns_for_skill(skill_id)
        modifications = {}

        for pattern in patterns:
            # Validate pattern
            is_valid, errors = PatternValidator.validate(pattern)
            if not is_valid:
                continue

            # Check if pattern applies to current context
            if not self._pattern_matches_context(pattern, context):
                continue

            # Determine application strategy
            action = ConfidenceThresholds.get_action(
                pattern['confidence'],
                pattern['metrics']['sample_size'],
                pattern.get('temporal_consistency', 1.0)
            )

            if action == 'auto_apply':
                modifications.update(self._extract_modifications(pattern))
            elif action == 'suggest':
                modifications['_suggestions'] = modifications.get('_suggestions', [])
                modifications['_suggestions'].append({
                    'pattern_id': pattern['pattern_id'],
                    'description': pattern['description'],
                    'confidence': pattern['confidence']
                })

        return modifications

    def _pattern_matches_context(self, pattern, context):
        """Check if pattern context matches current context."""
        pattern_context = pattern.get('context', {})

        for key, value in pattern_context.items():
            if key in context and context[key] != value:
                return False

        return True

    def _extract_modifications(self, pattern):
        """Extract parameter modifications from pattern."""
        mods = {}

        if pattern['pattern_type'] == 'code_style':
            mods['code_style'] = pattern.get('preferred_choice')
        elif pattern['pattern_type'] == 'usage':
            mods['preferred_tool'] = pattern.get('preferred_choice')
        elif pattern['pattern_type'] == 'workflow':
            mods['workflow_sequence'] = pattern.get('sequence', [])

        return mods
```

### Skill Updating Process

```python
class SkillUpdater:
    """Update skill definitions based on learned patterns."""

    def update_skill_with_patterns(self, skill, patterns):
        """
        Update skill configuration with learned patterns.

        Args:
            skill: Skill object to update
            patterns: List of applicable patterns

        Returns:
            Updated skill object
        """
        updated_skill = skill.copy()

        for pattern in patterns:
            if pattern['pattern_type'] == 'code_style':
                updated_skill.setdefault('defaults', {})
                updated_skill['defaults']['code_style'] = pattern.get('style_preferences', {})

            elif pattern['pattern_type'] == 'usage':
                updated_skill.setdefault('preferences', {})
                updated_skill['preferences']['preferred_tools'] = pattern.get('preferred_choice')

            elif pattern['pattern_type'] == 'workflow':
                updated_skill.setdefault('workflow', {})
                updated_skill['workflow']['steps'] = pattern.get('sequence', [])

        # Add metadata about pattern application
        updated_skill['_pattern_metadata'] = {
            'patterns_applied': len(patterns),
            'last_updated': datetime.utcnow().isoformat(),
            'confidence_avg': sum(p['confidence'] for p in patterns) / len(patterns)
        }

        return updated_skill
```

### User Notification

```python
class PatternNotifier:
    """Notify users about pattern learning and application."""

    @staticmethod
    def notify_pattern_learned(pattern):
        """Generate notification for newly learned pattern."""
        return {
            'type': 'pattern_learned',
            'message': f"Learned new pattern: {pattern['description']}",
            'pattern_id': pattern['pattern_id'],
            'confidence': pattern['confidence'],
            'action_required': False,
            'details': {
                'pattern_type': pattern['pattern_type'],
                'sample_size': pattern['metrics']['sample_size']
            }
        }

    @staticmethod
    def notify_pattern_applied(pattern, skill_id):
        """Generate notification for pattern application."""
        return {
            'type': 'pattern_applied',
            'message': f"Applied pattern '{pattern['description']}' to {skill_id}",
            'pattern_id': pattern['pattern_id'],
            'skill_id': skill_id,
            'confidence': pattern['confidence'],
            'action_required': False
        }

    @staticmethod
    def suggest_pattern(pattern):
        """Generate suggestion for pattern application."""
        return {
            'type': 'pattern_suggestion',
            'message': f"Would you like to apply: {pattern['description']}?",
            'pattern_id': pattern['pattern_id'],
            'confidence': pattern['confidence'],
            'action_required': True,
            'actions': ['accept', 'reject', 'always', 'never']
        }
```

### Opt-Out Mechanism

```python
class PatternOptOut:
    """Manage user preferences for pattern learning."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.preferences = self._load_preferences()

    def _load_preferences(self):
        """Load user pattern preferences."""
        import json
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'pattern_learning_enabled': True,
                'disabled_pattern_types': [],
                'disabled_patterns': [],
                'auto_apply_enabled': True
            }

    def is_pattern_learning_enabled(self):
        """Check if pattern learning is globally enabled."""
        return self.preferences.get('pattern_learning_enabled', True)

    def is_pattern_type_enabled(self, pattern_type):
        """Check if specific pattern type is enabled."""
        return pattern_type not in self.preferences.get('disabled_pattern_types', [])

    def is_pattern_enabled(self, pattern_id):
        """Check if specific pattern is enabled."""
        return pattern_id not in self.preferences.get('disabled_patterns', [])

    def disable_pattern(self, pattern_id):
        """Disable a specific pattern."""
        if pattern_id not in self.preferences.get('disabled_patterns', []):
            self.preferences.setdefault('disabled_patterns', []).append(pattern_id)
            self._save_preferences()

    def disable_pattern_type(self, pattern_type):
        """Disable an entire pattern type."""
        if pattern_type not in self.preferences.get('disabled_pattern_types', []):
            self.preferences.setdefault('disabled_pattern_types', []).append(pattern_type)
            self._save_preferences()

    def _save_preferences(self):
        """Save preferences to disk."""
        import json
        with open(self.config_path, 'w') as f:
            json.dump(self.preferences, f, indent=2)
```

## 5. Pattern Categories

### Code Style Patterns

#### Naming Conventions

```json
{
  "pattern_id": "style_naming_snake_case",
  "pattern_type": "code_style",
  "category": "naming",
  "description": "User prefers snake_case for variables and functions",
  "metrics": {
    "snake_case_count": 234,
    "camelCase_count": 12,
    "PascalCase_count": 45,
    "preference_ratio": 0.80
  },
  "style_rules": {
    "variables": "snake_case",
    "functions": "snake_case",
    "classes": "PascalCase",
    "constants": "UPPER_SNAKE_CASE"
  },
  "confidence": 0.88
}
```

#### Import Organization

```json
{
  "pattern_id": "style_imports_grouped",
  "pattern_type": "code_style",
  "category": "imports",
  "description": "User groups imports: stdlib, third-party, local",
  "import_order": [
    "standard_library",
    "third_party",
    "local"
  ],
  "style_rules": {
    "sort_within_groups": true,
    "blank_line_between_groups": true,
    "from_imports_after_direct": false
  },
  "confidence": 0.91
}
```

#### Error Handling

```json
{
  "pattern_id": "style_error_specific",
  "pattern_type": "code_style",
  "category": "error_handling",
  "description": "User prefers specific exception types over bare except",
  "metrics": {
    "specific_exception_count": 67,
    "bare_except_count": 2,
    "preference_ratio": 0.97
  },
  "preferred_exceptions": [
    "ValueError",
    "TypeError",
    "KeyError",
    "FileNotFoundError"
  ],
  "confidence": 0.93
}
```

#### Testing Style

```json
{
  "pattern_id": "style_testing_aaa",
  "pattern_type": "code_style",
  "category": "testing",
  "description": "User follows Arrange-Act-Assert pattern",
  "test_structure": {
    "pattern": "AAA",
    "uses_comments": true,
    "blank_lines_between": true
  },
  "naming_pattern": "test_{method}_{scenario}_{expected}",
  "confidence": 0.85
}
```

### Workflow Patterns

#### Commit Patterns

```json
{
  "pattern_id": "workflow_conventional_commits",
  "pattern_type": "workflow",
  "category": "commits",
  "description": "User follows Conventional Commits specification",
  "commit_format": {
    "type": ["feat", "fix", "docs", "refactor", "test", "chore"],
    "scope": "optional",
    "breaking_change_indicator": "!",
    "message_format": "{type}({scope}): {description}"
  },
  "metrics": {
    "conventional_commits": 89,
    "total_commits": 95,
    "compliance_ratio": 0.94
  },
  "confidence": 0.92
}
```

#### Branch Naming

```json
{
  "pattern_id": "workflow_branch_naming",
  "pattern_type": "workflow",
  "category": "branches",
  "description": "User follows feature/fix/chore branch naming",
  "branch_format": "{type}/{ticket}-{description}",
  "types": {
    "feature": 0.65,
    "fix": 0.25,
    "chore": 0.10
  },
  "includes_ticket_number": true,
  "confidence": 0.87
}
```

#### Pull Request Workflow

```json
{
  "pattern_id": "workflow_pr_process",
  "pattern_type": "workflow",
  "category": "pull_requests",
  "description": "User creates draft PRs, updates with commits, then marks ready",
  "sequence": [
    "create_draft_pr",
    "push_commits",
    "self_review",
    "mark_ready_for_review",
    "address_feedback",
    "merge"
  ],
  "pr_template_used": true,
  "auto_delete_branch": true,
  "confidence": 0.83
}
```

#### Code Review Pattern

```json
{
  "pattern_id": "workflow_code_review",
  "pattern_type": "workflow",
  "category": "review",
  "description": "User thoroughly reviews tests and docs first",
  "review_order": [
    "tests",
    "documentation",
    "implementation",
    "configuration"
  ],
  "uses_review_comments": true,
  "requests_changes_threshold": "medium_issues",
  "confidence": 0.79
}
```

### Tool Preferences

#### Preferred Libraries

```json
{
  "pattern_id": "tool_pref_pytest",
  "pattern_type": "usage",
  "category": "preferred_tools",
  "description": "User strongly prefers pytest over alternatives",
  "tool": "pytest",
  "category_name": "testing_framework",
  "alternatives_rejected": ["unittest", "nose2"],
  "usage_count": 47,
  "contexts": ["web_api", "cli_tool", "library"],
  "confidence": 0.95
}
```

#### Avoided Tools

```json
{
  "pattern_id": "tool_avoid_pylint",
  "pattern_type": "usage",
  "category": "avoided_tools",
  "description": "User avoids pylint, prefers ruff",
  "tool_avoided": "pylint",
  "preferred_alternative": "ruff",
  "rejection_count": 8,
  "last_rejected": "2025-01-20T10:30:00Z",
  "confidence": 0.82
}
```

#### Configuration Preferences

```json
{
  "pattern_id": "tool_config_pyproject",
  "pattern_type": "code_style",
  "category": "configuration",
  "description": "User centralizes config in pyproject.toml",
  "preferred_config_file": "pyproject.toml",
  "tools_configured": [
    "pytest",
    "ruff",
    "mypy",
    "black"
  ],
  "avoids_separate_configs": true,
  "confidence": 0.89
}
```

### Architecture Patterns

#### File Organization

```json
{
  "pattern_id": "arch_src_layout",
  "pattern_type": "code_style",
  "category": "file_organization",
  "description": "User prefers src/ layout for Python projects",
  "structure": {
    "uses_src_dir": true,
    "test_location": "tests/",
    "docs_location": "docs/",
    "config_location": "root"
  },
  "project_count": 8,
  "confidence": 0.91
}
```

#### Module Structure

```json
{
  "pattern_id": "arch_module_structure",
  "pattern_type": "code_style",
  "category": "module_structure",
  "description": "User organizes by feature, not by type",
  "organization_style": "feature_based",
  "structure_example": {
    "users": ["models.py", "services.py", "routes.py", "schemas.py"],
    "auth": ["models.py", "services.py", "routes.py", "schemas.py"]
  },
  "avoids_type_based": true,
  "confidence": 0.86
}
```

#### Separation of Concerns

```json
{
  "pattern_id": "arch_separation_concerns",
  "pattern_type": "code_style",
  "category": "architecture",
  "description": "User separates business logic from framework code",
  "layers": [
    "routes/controllers",
    "services/business_logic",
    "repositories/data_access",
    "models/entities"
  ],
  "framework_isolation": true,
  "dependency_direction": "inward",
  "confidence": 0.84
}
```

## 6. Learning Pipeline

### Five-Stage Learning Process

#### Stage 1: Observation (Confidence: 0.0-0.4)

```python
class ObservationStage:
    """Initial data collection stage."""

    def __init__(self):
        self.min_samples = 3
        self.observations = []

    def record(self, event):
        """Record observation without pattern formation."""
        self.observations.append(event)

    def should_advance(self):
        """Check if ready to advance to hypothesis stage."""
        return len(self.observations) >= self.min_samples

    def get_initial_stats(self):
        """Get preliminary statistics."""
        choices = {}
        for obs in self.observations:
            choice = obs['choice']
            choices[choice] = choices.get(choice, 0) + 1

        total = len(self.observations)
        return {
            'unique_choices': len(choices),
            'most_common': max(choices.items(), key=lambda x: x[1]),
            'total_observations': total
        }
```

#### Stage 2: Hypothesis (Confidence: 0.4-0.6)

```python
class HypothesisStage:
    """Form initial pattern hypothesis."""

    def __init__(self, observations):
        self.observations = observations
        self.hypothesis = None

    def form_hypothesis(self):
        """Create initial pattern hypothesis."""
        pattern = detect_frequency_pattern(
            self.observations,
            threshold=0.60,
            min_samples=3
        )

        if pattern:
            self.hypothesis = {
                'pattern_type': 'usage',
                'preferred_choice': pattern['preferred_choice'],
                'confidence': pattern['confidence'],
                'stage': 'hypothesis',
                'sample_size': pattern['sample_size']
            }

        return self.hypothesis

    def should_advance(self):
        """Check if hypothesis is strong enough for testing."""
        if not self.hypothesis:
            return False
        return self.hypothesis['confidence'] >= 0.55
```

#### Stage 3: Testing (Confidence: 0.6-0.75)

```python
class TestingStage:
    """Test hypothesis with new observations."""

    def __init__(self, hypothesis):
        self.hypothesis = hypothesis
        self.test_observations = []
        self.confirmations = 0
        self.violations = 0

    def test(self, new_event):
        """Test hypothesis against new observation."""
        self.test_observations.append(new_event)

        if new_event['choice'] == self.hypothesis['preferred_choice']:
            self.confirmations += 1
        else:
            self.violations += 1

        # Update confidence using Bayesian update
        learner = BayesianPatternLearner(
            prior_alpha=self.hypothesis['sample_size'] * self.hypothesis['confidence'],
            prior_beta=self.hypothesis['sample_size'] * (1 - self.hypothesis['confidence'])
        )
        learner.update(self.confirmations, self.violations)

        self.hypothesis['confidence'] = learner.confidence()
        self.hypothesis['sample_size'] += 1

    def should_advance(self):
        """Check if ready for validation stage."""
        return (
            len(self.test_observations) >= 5 and
            self.hypothesis['confidence'] >= 0.70
        )

    def should_regress(self):
        """Check if hypothesis should be abandoned."""
        return (
            len(self.test_observations) >= 5 and
            self.hypothesis['confidence'] < 0.50
        )
```

#### Stage 4: Validation (Confidence: 0.75-0.85)

```python
class ValidationStage:
    """Validate pattern across contexts and time."""

    def __init__(self, pattern):
        self.pattern = pattern
        self.validation_tests = []

    def validate_statistical_significance(self, all_events):
        """Test statistical significance."""
        observed_counts = {}
        for event in all_events:
            choice = event['choice']
            observed_counts[choice] = observed_counts.get(choice, 0) + 1

        # Uniform distribution as null hypothesis
        total = sum(observed_counts.values())
        expected_counts = {
            choice: total / len(observed_counts)
            for choice in observed_counts
        }

        is_sig, p_value, chi2 = test_pattern_significance(
            observed_counts,
            expected_counts
        )

        self.validation_tests.append({
            'test': 'statistical_significance',
            'passed': is_sig,
            'p_value': p_value
        })

        return is_sig

    def validate_temporal_consistency(self, all_events):
        """Test temporal consistency."""
        consistency = detect_temporal_consistency(all_events)

        passed = consistency >= ConfidenceThresholds.MIN_TEMPORAL_CONSISTENCY

        self.validation_tests.append({
            'test': 'temporal_consistency',
            'passed': passed,
            'score': consistency
        })

        return passed

    def validate_cross_context(self, events_by_context):
        """Test pattern holds across different contexts."""
        contexts_supporting = 0
        total_contexts = len(events_by_context)

        for context, events in events_by_context.items():
            pattern = detect_frequency_pattern(events)
            if pattern and pattern['preferred_choice'] == self.pattern['preferred_choice']:
                contexts_supporting += 1

        cross_context_ratio = contexts_supporting / total_contexts if total_contexts > 0 else 0
        passed = cross_context_ratio >= 0.70

        self.validation_tests.append({
            'test': 'cross_context',
            'passed': passed,
            'ratio': cross_context_ratio
        })

        return passed

    def should_advance(self):
        """Check if ready for application stage."""
        if len(self.validation_tests) < 2:
            return False

        passed_tests = sum(1 for test in self.validation_tests if test['passed'])
        return passed_tests >= 2 and self.pattern['confidence'] >= 0.80
```

#### Stage 5: Application (Confidence: 0.85+)

```python
class ApplicationStage:
    """Apply validated pattern and continue monitoring."""

    def __init__(self, pattern):
        self.pattern = pattern
        self.application_count = 0
        self.success_count = 0
        self.pattern['stage'] = 'application'

    def apply(self):
        """Mark pattern as applied."""
        self.application_count += 1
        self.pattern['last_applied'] = datetime.utcnow().isoformat()

    def record_feedback(self, success):
        """Record feedback on pattern application."""
        if success:
            self.success_count += 1

        # Update confidence based on application feedback
        success_rate = self.success_count / self.application_count

        # Blend with existing confidence (weighted average)
        alpha = 0.3  # Weight for new evidence
        self.pattern['confidence'] = (
            alpha * success_rate +
            (1 - alpha) * self.pattern['confidence']
        )

    def monitor_drift(self, recent_events):
        """Monitor for pattern drift."""
        if len(recent_events) < 5:
            return False

        recent_pattern = detect_frequency_pattern(recent_events)
        if not recent_pattern:
            return False

        # Check if recent behavior differs
        drift_detected = (
            recent_pattern['preferred_choice'] != self.pattern['preferred_choice'] and
            recent_pattern['confidence'] > 0.70
        )

        return drift_detected
```

### Confidence Building

```python
class ConfidenceBuilder:
    """Build pattern confidence over time."""

    def __init__(self):
        self.stages = {
            'observation': (0.0, 0.4),
            'hypothesis': (0.4, 0.6),
            'testing': (0.6, 0.75),
            'validation': (0.75, 0.85),
            'application': (0.85, 1.0)
        }

    def get_stage(self, confidence):
        """Determine stage based on confidence."""
        for stage, (min_conf, max_conf) in self.stages.items():
            if min_conf <= confidence < max_conf:
                return stage
        return 'application' if confidence >= 0.85 else 'observation'

    def calculate_progression(self, pattern, new_event):
        """Calculate how new event affects progression."""
        current_stage = pattern.get('stage', 'observation')
        current_confidence = pattern['confidence']

        # Simulate confidence update
        is_confirmation = new_event['choice'] == pattern.get('preferred_choice')

        if is_confirmation:
            confidence_delta = 0.05 * (1 - current_confidence)
        else:
            confidence_delta = -0.10 * current_confidence

        new_confidence = max(0.0, min(1.0, current_confidence + confidence_delta))
        new_stage = self.get_stage(new_confidence)

        return {
            'old_stage': current_stage,
            'new_stage': new_stage,
            'old_confidence': current_confidence,
            'new_confidence': new_confidence,
            'progressed': new_stage != current_stage
        }
```

### Pattern Reinforcement

```python
class PatternReinforcer:
    """Reinforce patterns with positive observations."""

    @staticmethod
    def reinforce(pattern, confirming_event):
        """Strengthen pattern with confirming observation."""
        # Update last reinforced timestamp
        pattern['last_reinforced'] = datetime.utcnow().isoformat()

        # Increment reinforcement count
        pattern['metrics']['reinforcement_count'] = (
            pattern['metrics'].get('reinforcement_count', 0) + 1
        )

        # Slightly boost confidence (diminishing returns)
        current_confidence = pattern['confidence']
        boost = 0.01 * (1 - current_confidence)
        pattern['confidence'] = min(0.99, current_confidence + boost)

        # Update sample size
        pattern['metrics']['sample_size'] += 1

        return pattern

    @staticmethod
    def weaken(pattern, violating_event):
        """Weaken pattern with contradicting observation."""
        # Update last modified timestamp
        pattern['last_modified'] = datetime.utcnow().isoformat()

        # Increment violation count
        pattern['metrics']['violation_count'] = (
            pattern['metrics'].get('violation_count', 0) + 1
        )

        # Reduce confidence
        current_confidence = pattern['confidence']
        reduction = 0.05
        pattern['confidence'] = max(0.0, current_confidence - reduction)

        # Update sample size
        pattern['metrics']['sample_size'] += 1

        # Check if pattern should be demoted
        if pattern['confidence'] < ConfidenceThresholds.MIN_CONFIDENCE:
            pattern['stage'] = 'observation'

        return pattern
```

### Pattern Decay

```python
class PatternDecay:
    """Handle pattern decay over time."""

    def __init__(self, decay_rate=0.01):
        """
        Initialize decay handler.

        Args:
            decay_rate: Confidence decay per day (default: 1% per day)
        """
        self.decay_rate = decay_rate

    def apply_decay(self, pattern):
        """Apply time-based decay to pattern confidence."""
        last_reinforced = datetime.fromisoformat(
            pattern.get('last_reinforced', pattern.get('first_detected'))
        )
        days_since = (datetime.utcnow() - last_reinforced).days

        if days_since == 0:
            return pattern

        # Exponential decay
        current_confidence = pattern['confidence']
        decayed_confidence = current_confidence * (1 - self.decay_rate) ** days_since

        pattern['confidence'] = max(0.0, decayed_confidence)

        # Update stage based on new confidence
        builder = ConfidenceBuilder()
        pattern['stage'] = builder.get_stage(pattern['confidence'])

        return pattern

    def decay_all_patterns(self, patterns):
        """Apply decay to all patterns."""
        return [self.apply_decay(p) for p in patterns]

    def remove_expired_patterns(self, patterns, expiry_days=180):
        """Remove patterns that haven't been reinforced in expiry_days."""
        active_patterns = []

        for pattern in patterns:
            last_activity = datetime.fromisoformat(
                pattern.get('last_reinforced', pattern.get('first_detected'))
            )
            days_since = (datetime.utcnow() - last_activity).days

            if days_since < expiry_days:
                active_patterns.append(pattern)

        return active_patterns
```

## 7. Pattern Storage

### File Format

Patterns are stored in JSON Lines format (one JSON object per line) for efficient append and streaming operations.

```jsonl
{"pattern_id":"usage_pytest_preferred","pattern_type":"usage","description":"User consistently chooses pytest over unittest","confidence":0.92,"first_detected":"2025-01-15T10:30:00Z","last_reinforced":"2025-01-22T14:20:00Z","stage":"application","metrics":{"pytest_usage_count":47,"unittest_usage_count":2,"preference_ratio":0.96,"sample_size":49}}
{"pattern_id":"style_double_quotes","pattern_type":"code_style","description":"User prefers double quotes for strings","confidence":0.88,"first_detected":"2025-01-16T09:15:00Z","last_reinforced":"2025-01-22T16:45:00Z","stage":"application","metrics":{"double_quote_count":156,"single_quote_count":12,"preference_ratio":0.93,"sample_size":168}}
```

### Schema Design

```python
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

@dataclass
class Pattern:
    """Schema for pattern storage."""

    pattern_id: str
    pattern_type: str  # usage, code_style, workflow, combination
    description: str
    confidence: float
    first_detected: str  # ISO 8601
    last_reinforced: str  # ISO 8601
    stage: str  # observation, hypothesis, testing, validation, application
    metrics: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None
    statistical_test: Optional[Dict[str, Any]] = None

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str):
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
```

### Query Capabilities

```python
class PatternStore:
    """Store and query patterns."""

    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.patterns = []
        self._load_patterns()

    def _load_patterns(self):
        """Load patterns from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                self.patterns = [
                    Pattern.from_json(line.strip())
                    for line in f
                    if line.strip()
                ]
        except FileNotFoundError:
            self.patterns = []

    def save(self):
        """Save all patterns to storage."""
        with open(self.storage_path, 'w') as f:
            for pattern in self.patterns:
                f.write(pattern.to_json() + '\n')

    def add_pattern(self, pattern):
        """Add new pattern."""
        self.patterns.append(pattern)
        # Append to file
        with open(self.storage_path, 'a') as f:
            f.write(pattern.to_json() + '\n')

    def query(self, **filters):
        """
        Query patterns with filters.

        Examples:
            query(pattern_type='usage')
            query(pattern_type='code_style', confidence_min=0.8)
            query(stage='application')
        """
        results = self.patterns

        for key, value in filters.items():
            if key.endswith('_min'):
                # Minimum threshold filter
                attr = key[:-4]
                results = [p for p in results if getattr(p, attr) >= value]
            elif key.endswith('_max'):
                # Maximum threshold filter
                attr = key[:-4]
                results = [p for p in results if getattr(p, attr) <= value]
            else:
                # Exact match filter
                results = [p for p in results if getattr(p, key) == value]

        return results

    def get_by_id(self, pattern_id):
        """Get pattern by ID."""
        for pattern in self.patterns:
            if pattern.pattern_id == pattern_id:
                return pattern
        return None

    def get_patterns_for_skill(self, skill_id):
        """Get patterns applicable to a skill."""
        # This would need context about which patterns apply to which skills
        # For now, return patterns that might be relevant
        return self.query(stage='application', confidence_min=0.70)

    def get_patterns_by_context(self, context):
        """Get patterns matching specific context."""
        matching = []
        for pattern in self.patterns:
            if pattern.context:
                match = all(
                    pattern.context.get(k) == v
                    for k, v in context.items()
                )
                if match:
                    matching.append(pattern)
        return matching

    def update_pattern(self, pattern_id, updates):
        """Update existing pattern."""
        pattern = self.get_by_id(pattern_id)
        if pattern:
            for key, value in updates.items():
                setattr(pattern, key, value)
            self.save()
            return pattern
        return None

    def delete_pattern(self, pattern_id):
        """Delete pattern by ID."""
        self.patterns = [p for p in self.patterns if p.pattern_id != pattern_id]
        self.save()
```

### Backup Strategy

```python
import shutil
from pathlib import Path

class PatternBackupManager:
    """Manage pattern backups."""

    def __init__(self, storage_path, backup_dir):
        self.storage_path = Path(storage_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self):
        """Create timestamped backup."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"patterns_{timestamp}.jsonl"

        shutil.copy2(self.storage_path, backup_path)

        return backup_path

    def rotate_backups(self, keep_count=10):
        """Keep only most recent backups."""
        backups = sorted(
            self.backup_dir.glob('patterns_*.jsonl'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[keep_count:]:
            old_backup.unlink()

    def restore_backup(self, backup_path):
        """Restore from backup."""
        shutil.copy2(backup_path, self.storage_path)

    def list_backups(self):
        """List available backups."""
        backups = sorted(
            self.backup_dir.glob('patterns_*.jsonl'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return [
            {
                'path': str(backup),
                'timestamp': datetime.fromtimestamp(backup.stat().st_mtime),
                'size': backup.stat().st_size
            }
            for backup in backups
        ]
```

## 8. Pattern Sharing

### Team Patterns

```python
class TeamPatternManager:
    """Manage shared patterns within a team."""

    def __init__(self, personal_store, team_store):
        self.personal_store = personal_store
        self.team_store = team_store

    def share_pattern(self, pattern_id, team_id):
        """Share personal pattern with team."""
        pattern = self.personal_store.get_by_id(pattern_id)
        if not pattern:
            return False

        # Anonymize pattern
        team_pattern = self._anonymize_pattern(pattern)
        team_pattern.context = team_pattern.context or {}
        team_pattern.context['team_id'] = team_id
        team_pattern.context['shared_by'] = 'anonymous'

        self.team_store.add_pattern(team_pattern)
        return True

    def get_team_patterns(self, team_id):
        """Get patterns shared by team."""
        return self.team_store.query(context_team_id=team_id)

    def merge_team_pattern(self, team_pattern_id):
        """Adopt team pattern into personal patterns."""
        team_pattern = self.team_store.get_by_id(team_pattern_id)
        if not team_pattern:
            return False

        # Create personal copy
        personal_pattern = Pattern(
            pattern_id=f"personal_{team_pattern.pattern_id}",
            pattern_type=team_pattern.pattern_type,
            description=f"Adopted from team: {team_pattern.description}",
            confidence=team_pattern.confidence * 0.8,  # Reduce confidence initially
            first_detected=datetime.utcnow().isoformat(),
            last_reinforced=datetime.utcnow().isoformat(),
            stage='testing',  # Start in testing stage
            metrics=team_pattern.metrics.copy(),
            context=team_pattern.context
        )

        self.personal_store.add_pattern(personal_pattern)
        return True

    def _anonymize_pattern(self, pattern):
        """Remove identifying information from pattern."""
        anonymized = Pattern(
            pattern_id=pattern.pattern_id,
            pattern_type=pattern.pattern_type,
            description=pattern.description,
            confidence=pattern.confidence,
            first_detected=pattern.first_detected,
            last_reinforced=pattern.last_reinforced,
            stage=pattern.stage,
            metrics=pattern.metrics.copy()
        )

        # Remove any potentially identifying context
        if pattern.context:
            safe_context = {
                k: v for k, v in pattern.context.items()
                if k not in ['user_id', 'project_name', 'file_path']
            }
            anonymized.context = safe_context

        return anonymized
```

### Community Patterns (Future Feature)

```python
class CommunityPatternRegistry:
    """
    Registry for community-contributed patterns.

    Future feature: Allow users to contribute anonymized patterns
    to a community registry for others to discover and adopt.
    """

    def __init__(self, registry_url):
        self.registry_url = registry_url

    def search_patterns(self, query, filters=None):
        """
        Search community patterns.

        Args:
            query: Search query (e.g., "python testing")
            filters: Additional filters (language, framework, etc.)

        Returns:
            List of matching community patterns
        """
        # Future implementation
        pass

    def submit_pattern(self, pattern, metadata):
        """
        Submit pattern to community registry.

        Args:
            pattern: Pattern to share
            metadata: Additional metadata (tags, description)

        Returns:
            Submission ID
        """
        # Future implementation
        pass

    def vote_pattern(self, pattern_id, helpful=True):
        """Vote on pattern helpfulness."""
        # Future implementation
        pass
```

### Privacy Preservation

```python
class PrivacyPreservingSharing:
    """Ensure privacy when sharing patterns."""

    @staticmethod
    def differential_privacy_noise(value, epsilon=1.0):
        """
        Add Laplace noise for differential privacy.

        Args:
            value: Original numeric value
            epsilon: Privacy parameter (smaller = more privacy)

        Returns:
            Noised value
        """
        import numpy as np

        scale = 1.0 / epsilon
        noise = np.random.laplace(0, scale)

        return value + noise

    @staticmethod
    def anonymize_for_sharing(pattern):
        """
        Prepare pattern for public sharing with privacy guarantees.
        """
        shared_pattern = {
            'pattern_type': pattern.pattern_type,
            'description': pattern.description,
            'confidence_range': PrivacyPreservingSharing._bucket_confidence(
                pattern.confidence
            ),
            'category': pattern.context.get('category', 'general') if pattern.context else 'general'
        }

        # Add noised metrics
        if pattern.metrics:
            shared_pattern['metrics'] = {
                'sample_size_range': PrivacyPreservingSharing._bucket_sample_size(
                    pattern.metrics.get('sample_size', 0)
                )
            }

        return shared_pattern

    @staticmethod
    def _bucket_confidence(confidence):
        """Bucket confidence into ranges."""
        if confidence < 0.6:
            return 'low'
        elif confidence < 0.8:
            return 'medium'
        else:
            return 'high'

    @staticmethod
    def _bucket_sample_size(size):
        """Bucket sample size into ranges."""
        if size < 10:
            return '< 10'
        elif size < 50:
            return '10-50'
        elif size < 100:
            return '50-100'
        else:
            return '100+'
```

## Summary

This pattern system enables SkillForge to:

1. **Learn from user behavior** through multiple detection algorithms
2. **Build confidence gradually** through a 5-stage pipeline
3. **Apply patterns intelligently** with appropriate confidence thresholds
4. **Respect user privacy** with comprehensive privacy controls
5. **Share knowledge** within teams while preserving anonymity
6. **Adapt over time** through reinforcement and decay mechanisms

The pattern detection system transforms SkillForge from a static tool into a learning assistant that becomes increasingly personalized and effective over time.

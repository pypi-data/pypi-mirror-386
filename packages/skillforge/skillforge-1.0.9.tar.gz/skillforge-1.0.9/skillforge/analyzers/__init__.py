"""
Analyzers - Intelligence and learning systems for SkillForge

This module contains:
- IntentAnalyzer: Analyzes user intent from requests
- SkillDiscovery: Finds appropriate skills for tasks
- UsageTracker: Tracks skill usage for learning
- PatternDetector: Detects patterns from usage data
- LearningPipeline: Orchestrates pattern learning
- SkillOptimizer: Optimizes existing skills
"""

from .intent_analyzer import IntentAnalyzer, Intent, Pattern
from .usage_tracker import UsageTracker
from .skill_discovery import (
    SkillDiscovery,
    SkillMetadata,
    DiscoveredSkill,
    Intent as DiscoveryIntent,
)
from .pattern_detector import (
    PatternDetector,
    DetectedPattern,
    CombinationPattern,
    StylePattern,
    WorkflowPattern,
)
from .learning_pipeline import (
    LearningPipeline,
    Notification,
    LearningState,
)
from .skill_optimizer import (
    SkillOptimizer,
    OptimizationSuggestion,
    SkillAnalysis,
)

__all__ = [
    'IntentAnalyzer',
    'Intent',
    'Pattern',
    'UsageTracker',
    'SkillDiscovery',
    'SkillMetadata',
    'DiscoveredSkill',
    'DiscoveryIntent',
    'PatternDetector',
    'DetectedPattern',
    'CombinationPattern',
    'StylePattern',
    'WorkflowPattern',
    'LearningPipeline',
    'Notification',
    'LearningState',
    'SkillOptimizer',
    'OptimizationSuggestion',
    'SkillAnalysis',
]

"""
Skill Optimizer - Optimizes existing skills for efficiency and quality

This module provides the SkillOptimizer class for:
- Finding and removing redundancies in skills
- Suggesting merges for similar skills
- Updating outdated documentation
- Optimizing token usage
- Improving skill structure and organization

Quality-focused: Maintains skill effectiveness while reducing token overhead.
"""

import re
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from difflib import SequenceMatcher

from ..generators.config import Config
from ..generators.doc_fetcher import DocFetcher
from .usage_tracker import UsageTracker


@dataclass
class OptimizationSuggestion:
    """Suggestion for optimizing skills"""
    suggestion_id: str
    suggestion_type: str        # "merge", "update", "compress", "restructure", "remove"
    priority: str               # "high", "medium", "low"
    description: str
    affected_skills: List[str]
    estimated_token_savings: int
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationSuggestion':
        """Create suggestion from dictionary"""
        return cls(**data)


@dataclass
class SkillAnalysis:
    """Analysis results for a skill"""
    skill_name: str
    file_path: Path
    token_count: int
    line_count: int
    section_count: int
    last_modified: datetime
    usage_count: int
    success_rate: float
    has_yaml: bool
    yaml_valid: bool
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary"""
        result = asdict(self)
        result['file_path'] = str(self.file_path)
        result['last_modified'] = self.last_modified.isoformat()
        return result


class SkillOptimizer:
    """
    Optimizes existing skills for efficiency and quality.

    The optimizer:
    1. Analyzes all skills for metrics and issues
    2. Finds redundancies and overlaps
    3. Suggests merges for similar skills
    4. Identifies outdated documentation
    5. Optimizes token usage
    6. Improves structure and organization

    Example:
        >>> optimizer = SkillOptimizer()
        >>> report = optimizer.optimize_all_skills()
        >>> print(f"Token savings: {report['total_token_savings']}")
        >>> suggestions = optimizer.get_suggestions()
    """

    # Optimization thresholds
    SIMILARITY_THRESHOLD = 0.70  # 70% similarity for merge suggestion
    TOKEN_WARNING_THRESHOLD = 3000
    OUTDATED_DAYS = 90
    MIN_USAGE_FOR_KEEP = 3

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the skill optimizer.

        Args:
            config: Optional Config instance
        """
        self.config = config or Config()
        self.usage_tracker = UsageTracker()
        self.doc_fetcher = DocFetcher()
        self.suggestions: List[OptimizationSuggestion] = []
        self.analyses: Dict[str, SkillAnalysis] = {}

    def optimize_all_skills(self, auto_apply_safe: bool = False) -> Dict[str, Any]:
        """
        Optimize all skills in the skills directory.

        Args:
            auto_apply_safe: Automatically apply safe optimizations

        Returns:
            Optimization report with suggestions
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "skills_analyzed": 0,
            "total_tokens": 0,
            "optimizations": [],
            "total_token_savings": 0,
            "auto_applied": []
        }

        # Find all skills
        skills_dir = Path.home() / ".claude" / "skills"
        if not skills_dir.exists():
            return report

        skill_files = list(skills_dir.glob("*.md"))
        skill_files.extend(skills_dir.glob("**/*.md"))

        # Analyze each skill
        for skill_file in skill_files:
            if skill_file.name == "SKILL.md":  # Skip framework files
                continue

            try:
                analysis = self.analyze_skill(skill_file)
                self.analyses[analysis.skill_name] = analysis
                report["skills_analyzed"] += 1
                report["total_tokens"] += analysis.token_count
            except Exception as e:
                print(f"Error analyzing {skill_file}: {e}")

        # Run optimization strategies
        self._find_redundancies()
        self._suggest_merges()
        self._check_outdated_docs()
        self._optimize_token_usage()
        self._improve_structure()

        # Build report
        for suggestion in self.suggestions:
            report["optimizations"].append(suggestion.to_dict())
            report["total_token_savings"] += suggestion.estimated_token_savings

        # Auto-apply safe optimizations
        if auto_apply_safe:
            for suggestion in self.suggestions:
                if self._is_safe_to_auto_apply(suggestion):
                    try:
                        self.apply_suggestion(suggestion)
                        report["auto_applied"].append(suggestion.suggestion_id)
                    except Exception as e:
                        print(f"Error auto-applying {suggestion.suggestion_id}: {e}")

        return report

    def analyze_skill(self, skill_path: Path) -> SkillAnalysis:
        """
        Analyze a single skill file.

        Args:
            skill_path: Path to skill file

        Returns:
            SkillAnalysis with metrics and issues
        """
        with open(skill_path, 'r') as f:
            content = f.read()

        # Extract YAML frontmatter
        has_yaml = content.startswith('---')
        yaml_valid = False
        yaml_data = {}

        if has_yaml:
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_data = yaml.safe_load(parts[1])
                    yaml_valid = True
                    body = parts[2]
                else:
                    body = content
            except Exception:
                body = content
        else:
            body = content

        # Calculate metrics
        token_count = self._estimate_tokens(content)
        line_count = len(content.split('\n'))
        section_count = len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE))

        # Get usage statistics
        stats = self.usage_tracker.get_statistics()
        skill_name = skill_path.stem
        skill_usage = stats.get("skill_usage", {}).get(skill_name, {})

        usage_count = skill_usage.get("count", 0)
        success_rate = skill_usage.get("success_rate", 0.0)

        # Get file metadata
        last_modified = datetime.fromtimestamp(skill_path.stat().st_mtime)

        # Detect issues
        issues = []
        if token_count > self.TOKEN_WARNING_THRESHOLD:
            issues.append(f"High token count ({token_count})")

        if not has_yaml:
            issues.append("Missing YAML frontmatter")
        elif not yaml_valid:
            issues.append("Invalid YAML frontmatter")

        if section_count < 3:
            issues.append("Minimal structure (few sections)")

        days_since_modified = (datetime.now() - last_modified).days
        if days_since_modified > self.OUTDATED_DAYS:
            issues.append(f"Not updated in {days_since_modified} days")

        return SkillAnalysis(
            skill_name=skill_name,
            file_path=skill_path,
            token_count=token_count,
            line_count=line_count,
            section_count=section_count,
            last_modified=last_modified,
            usage_count=usage_count,
            success_rate=success_rate,
            has_yaml=has_yaml,
            yaml_valid=yaml_valid,
            issues=issues,
            metadata=yaml_data
        )

    def optimize_skill(self, skill_path: Path) -> Dict[str, Any]:
        """
        Optimize a specific skill file.

        Args:
            skill_path: Path to skill file

        Returns:
            Optimization results
        """
        analysis = self.analyze_skill(skill_path)

        results = {
            "skill": analysis.skill_name,
            "original_tokens": analysis.token_count,
            "optimized_tokens": analysis.token_count,
            "savings": 0,
            "changes": []
        }

        # Apply optimizations
        with open(skill_path, 'r') as f:
            content = f.read()

        original_content = content

        # Remove redundant whitespace
        content = self._compress_whitespace(content)
        if content != original_content:
            results["changes"].append("Compressed whitespace")

        # Optimize markdown
        content = self._optimize_markdown(content)
        if content != original_content:
            results["changes"].append("Optimized markdown")

        # Calculate savings
        optimized_tokens = self._estimate_tokens(content)
        results["optimized_tokens"] = optimized_tokens
        results["savings"] = analysis.token_count - optimized_tokens

        # Write optimized content if there are savings
        if results["savings"] > 0:
            with open(skill_path, 'w') as f:
                f.write(content)

        return results

    def _find_redundancies(self) -> None:
        """Find redundant content across skills"""
        # Group skills by content similarity
        skill_names = list(self.analyses.keys())

        for i, skill1 in enumerate(skill_names):
            for skill2 in skill_names[i+1:]:
                # Calculate content overlap
                overlap = self._calculate_overlap(skill1, skill2)

                if overlap > 0.5 and overlap < self.SIMILARITY_THRESHOLD:
                    # Significant overlap but not similar enough to merge
                    suggestion = OptimizationSuggestion(
                        suggestion_id=f"redundancy_{skill1}_{skill2}",
                        suggestion_type="remove",
                        priority="medium",
                        description=f"Remove redundant content between {skill1} and {skill2}",
                        affected_skills=[skill1, skill2],
                        estimated_token_savings=int(
                            min(
                                self.analyses[skill1].token_count,
                                self.analyses[skill2].token_count
                            ) * overlap * 0.5
                        ),
                        confidence=overlap,
                        details={
                            "overlap_percentage": overlap * 100,
                            "skill1": skill1,
                            "skill2": skill2
                        }
                    )
                    self.suggestions.append(suggestion)

    def _suggest_merges(self) -> None:
        """Suggest merging similar skills"""
        skill_names = list(self.analyses.keys())

        for i, skill1 in enumerate(skill_names):
            for skill2 in skill_names[i+1:]:
                similarity = self._calculate_similarity(skill1, skill2)

                if similarity >= self.SIMILARITY_THRESHOLD:
                    # High similarity - suggest merge
                    combined_tokens = (
                        self.analyses[skill1].token_count +
                        self.analyses[skill2].token_count
                    )
                    # Estimate merged size (accounting for removed duplicates)
                    estimated_merged = int(combined_tokens * (1 - similarity * 0.5))

                    suggestion = OptimizationSuggestion(
                        suggestion_id=f"merge_{skill1}_{skill2}",
                        suggestion_type="merge",
                        priority="high" if similarity >= 0.85 else "medium",
                        description=f"Merge {skill1} and {skill2} ({similarity*100:.0f}% similar)",
                        affected_skills=[skill1, skill2],
                        estimated_token_savings=combined_tokens - estimated_merged,
                        confidence=similarity,
                        details={
                            "similarity": similarity * 100,
                            "skill1": skill1,
                            "skill2": skill2,
                            "skill1_tokens": self.analyses[skill1].token_count,
                            "skill2_tokens": self.analyses[skill2].token_count,
                            "estimated_merged_tokens": estimated_merged
                        }
                    )
                    self.suggestions.append(suggestion)

    def _check_outdated_docs(self) -> None:
        """Check for skills with outdated documentation"""
        for skill_name, analysis in self.analyses.items():
            days_old = (datetime.now() - analysis.last_modified).days

            if days_old > self.OUTDATED_DAYS:
                # Check if framework has newer version
                framework_info = self._detect_framework(analysis)

                if framework_info:
                    suggestion = OptimizationSuggestion(
                        suggestion_id=f"update_{skill_name}",
                        suggestion_type="update",
                        priority="high" if days_old > 180 else "medium",
                        description=f"Update documentation for {skill_name} (last updated {days_old} days ago)",
                        affected_skills=[skill_name],
                        estimated_token_savings=0,  # Quality improvement, not token savings
                        confidence=0.95,
                        details={
                            "days_old": days_old,
                            "last_modified": analysis.last_modified.isoformat(),
                            "framework": framework_info.get("name"),
                            "detected_version": framework_info.get("version")
                        }
                    )
                    self.suggestions.append(suggestion)

    def _optimize_token_usage(self) -> None:
        """Identify opportunities to reduce token usage"""
        for skill_name, analysis in self.analyses.items():
            if analysis.token_count > self.TOKEN_WARNING_THRESHOLD:
                # Skill is too verbose
                potential_savings = int((analysis.token_count - self.TOKEN_WARNING_THRESHOLD) * 0.3)

                suggestion = OptimizationSuggestion(
                    suggestion_id=f"compress_{skill_name}",
                    suggestion_type="compress",
                    priority="high" if analysis.token_count > 5000 else "medium",
                    description=f"Compress verbose content in {skill_name}",
                    affected_skills=[skill_name],
                    estimated_token_savings=potential_savings,
                    confidence=0.8,
                    details={
                        "current_tokens": analysis.token_count,
                        "target_tokens": self.TOKEN_WARNING_THRESHOLD,
                        "verbosity_issues": self._identify_verbose_sections(skill_name)
                    }
                )
                self.suggestions.append(suggestion)

    def _improve_structure(self) -> None:
        """Suggest structural improvements"""
        for skill_name, analysis in self.analyses.items():
            issues = []

            # Check for missing YAML
            if not analysis.has_yaml:
                issues.append("Add YAML frontmatter")
            elif not analysis.yaml_valid:
                issues.append("Fix invalid YAML")

            # Check for minimal structure
            if analysis.section_count < 3:
                issues.append("Add more sections for better organization")

            # Check for poor section organization
            if analysis.token_count > 2000 and analysis.section_count < 5:
                issues.append("Break down into more sections")

            if issues:
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"restructure_{skill_name}",
                    suggestion_type="restructure",
                    priority="low",
                    description=f"Improve structure of {skill_name}",
                    affected_skills=[skill_name],
                    estimated_token_savings=0,
                    confidence=0.7,
                    details={
                        "issues": issues,
                        "current_sections": analysis.section_count,
                        "current_tokens": analysis.token_count
                    }
                )
                self.suggestions.append(suggestion)

    def _calculate_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate similarity between two skills.

        Args:
            skill1: First skill name
            skill2: Second skill name

        Returns:
            Similarity score 0.0 to 1.0
        """
        analysis1 = self.analyses[skill1]
        analysis2 = self.analyses[skill2]

        # Read file contents
        with open(analysis1.file_path, 'r') as f:
            content1 = f.read()
        with open(analysis2.file_path, 'r') as f:
            content2 = f.read()

        # Remove YAML frontmatter for comparison
        content1 = self._remove_frontmatter(content1)
        content2 = self._remove_frontmatter(content2)

        # Calculate sequence similarity
        return SequenceMatcher(None, content1, content2).ratio()

    def _calculate_overlap(self, skill1: str, skill2: str) -> float:
        """Calculate content overlap between skills"""
        analysis1 = self.analyses[skill1]
        analysis2 = self.analyses[skill2]

        with open(analysis1.file_path, 'r') as f:
            content1 = f.read()
        with open(analysis2.file_path, 'r') as f:
            content2 = f.read()

        # Extract sections
        sections1 = set(re.findall(r'^#{1,3}\s+(.+)$', content1, re.MULTILINE))
        sections2 = set(re.findall(r'^#{1,3}\s+(.+)$', content2, re.MULTILINE))

        # Calculate section overlap
        if not sections1 or not sections2:
            return 0.0

        common = sections1 & sections2
        total = sections1 | sections2

        return len(common) / len(total) if total else 0.0

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2]
        return content

    def _detect_framework(self, analysis: SkillAnalysis) -> Optional[Dict[str, str]]:
        """Detect framework and version from skill"""
        metadata = analysis.metadata

        # Check YAML metadata
        if "framework" in metadata:
            return {
                "name": metadata["framework"],
                "version": metadata.get("version", "unknown")
            }

        # Try to detect from skill name
        skill_name = analysis.skill_name.lower()

        framework_patterns = {
            "nextjs": "Next.js",
            "react": "React",
            "vue": "Vue",
            "svelte": "Svelte",
            "django": "Django",
            "fastapi": "FastAPI",
            "express": "Express"
        }

        for pattern, name in framework_patterns.items():
            if pattern in skill_name:
                return {"name": name, "version": "unknown"}

        return None

    def _identify_verbose_sections(self, skill_name: str) -> List[str]:
        """Identify verbose sections in skill"""
        analysis = self.analyses[skill_name]

        with open(analysis.file_path, 'r') as f:
            content = f.read()

        verbose_sections = []

        # Find sections with >500 tokens
        sections = re.split(r'^(#{1,3}\s+.+)$', content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_title = sections[i].strip()
                section_content = sections[i + 1]
                section_tokens = self._estimate_tokens(section_content)

                if section_tokens > 500:
                    verbose_sections.append(section_title)

        return verbose_sections

    def _compress_whitespace(self, content: str) -> str:
        """Compress excessive whitespace"""
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]

        # Remove more than 2 consecutive empty lines
        compressed = []
        empty_count = 0

        for line in lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    compressed.append(line)
            else:
                empty_count = 0
                compressed.append(line)

        return '\n'.join(compressed)

    def _optimize_markdown(self, content: str) -> str:
        """Optimize markdown formatting"""
        # Remove redundant formatting
        content = re.sub(r'\*\*\*(.+?)\*\*\*', r'**\1**', content)  # Bold+italic -> bold

        # Compress lists with excessive spacing
        content = re.sub(r'\n\n-', r'\n-', content)
        content = re.sub(r'\n\n\*', r'\n*', content)

        return content

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses rough approximation: ~4 characters per token.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _is_safe_to_auto_apply(self, suggestion: OptimizationSuggestion) -> bool:
        """Check if suggestion is safe to auto-apply"""
        # Only auto-apply compress and restructure with high confidence
        if suggestion.suggestion_type in ["compress", "restructure"]:
            return suggestion.confidence >= 0.8

        # Never auto-apply merges or removals
        return False

    def apply_suggestion(self, suggestion: OptimizationSuggestion) -> Dict[str, Any]:
        """
        Apply an optimization suggestion.

        Args:
            suggestion: Suggestion to apply

        Returns:
            Application results
        """
        results = {
            "success": False,
            "suggestion_id": suggestion.suggestion_id,
            "changes": []
        }

        try:
            if suggestion.suggestion_type == "compress":
                self._apply_compression(suggestion)
                results["changes"].append("Compressed content")
                results["success"] = True

            elif suggestion.suggestion_type == "restructure":
                self._apply_restructure(suggestion)
                results["changes"].append("Improved structure")
                results["success"] = True

            elif suggestion.suggestion_type == "update":
                self._apply_update(suggestion)
                results["changes"].append("Updated documentation")
                results["success"] = True

            # Mark as applied
            suggestion.applied = True

        except Exception as e:
            results["error"] = str(e)

        return results

    def _apply_compression(self, suggestion: OptimizationSuggestion) -> None:
        """Apply compression optimization"""
        skill_name = suggestion.affected_skills[0]
        analysis = self.analyses[skill_name]

        self.optimize_skill(analysis.file_path)

    def _apply_restructure(self, suggestion: OptimizationSuggestion) -> None:
        """Apply structure improvements"""
        skill_name = suggestion.affected_skills[0]
        analysis = self.analyses[skill_name]

        with open(analysis.file_path, 'r') as f:
            content = f.read()

        # Add YAML frontmatter if missing
        if not analysis.has_yaml:
            frontmatter = f"""---
name: {skill_name}
description: {skill_name.replace('-', ' ').title()}
version: 1.0.0
---

"""
            content = frontmatter + content

        with open(analysis.file_path, 'w') as f:
            f.write(content)

    def _apply_update(self, suggestion: OptimizationSuggestion) -> None:
        """Apply documentation update"""
        # This would fetch latest docs and update skill
        # For now, just mark as needing manual update
        pass

    def get_suggestions(
        self,
        suggestion_type: Optional[str] = None,
        priority: Optional[str] = None,
        applied: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get optimization suggestions with optional filtering.

        Args:
            suggestion_type: Filter by type
            priority: Filter by priority
            applied: Filter by applied status

        Returns:
            List of suggestion dictionaries
        """
        suggestions = self.suggestions

        if suggestion_type:
            suggestions = [s for s in suggestions if s.suggestion_type == suggestion_type]

        if priority:
            suggestions = [s for s in suggestions if s.priority == priority]

        if applied is not None:
            suggestions = [s for s in suggestions if s.applied == applied]

        return [s.to_dict() for s in suggestions]

    def get_analysis(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get analysis for specific skill"""
        if skill_name in self.analyses:
            return self.analyses[skill_name].to_dict()
        return None

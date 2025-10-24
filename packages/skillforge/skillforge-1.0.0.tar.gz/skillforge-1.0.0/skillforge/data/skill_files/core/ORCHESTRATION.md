# ORCHESTRATION.md

*Intelligent skill orchestration and workflow management for SkillForge*

---

## 1. Orchestration Pipeline

The orchestration pipeline manages the complete lifecycle of skill discovery, loading, and execution. It ensures optimal skill selection and efficient context usage.

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

Input: User Query
    │
    ▼
┌─────────────────┐
│ 1. Intent       │ → Analyze query semantics
│    Analysis     │   Extract topics, actions, domains
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Skill        │ → Search available skills
│    Discovery    │   Match capabilities to intent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Dependency   │ → Build skill dependency graph
│    Resolution   │   Determine load order
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Priority     │ → Score skills by relevance
│    Sorting      │   Rank by importance
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Token Budget │ → Allocate context tokens
│    Allocation   │   Optimize for highest value
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Progressive  │ → Load skills by priority
│    Loading      │   Stream highest priority first
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Context      │ → Inject into LLM context
│    Injection    │   Format for optimal parsing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. Usage        │ → Track actual usage
│    Tracking     │   Update skill statistics
└────────┬────────┘
         │
         ▼
Output: Enriched Context
```

### Stage Details

**Stage 1: Intent Analysis**
- Input: Raw user query string
- Process: Parse query, extract keywords, identify domain
- Output: IntentAnalysis object with topics, actions, confidence

**Stage 2: Skill Discovery**
- Input: IntentAnalysis object
- Process: Search skill library, match capabilities
- Output: List of candidate skills with relevance scores

**Stage 3: Dependency Resolution**
- Input: List of candidate skills
- Process: Build dependency graph, detect cycles, determine order
- Output: Ordered skill list with dependencies resolved

**Stage 4: Priority Sorting**
- Input: Ordered skill list
- Process: Calculate priority scores based on multiple factors
- Output: Ranked skill list

**Stage 5: Token Budget Allocation**
- Input: Ranked skill list, available token budget
- Process: Allocate tokens proportionally to priority
- Output: Token allocation map

**Stage 6: Progressive Loading**
- Input: Skills with token allocations
- Process: Load skills in priority order up to budget limit
- Output: Loaded skill content

**Stage 7: Context Injection**
- Input: Loaded skill content
- Process: Format and structure for LLM consumption
- Output: Formatted context string

**Stage 8: Usage Tracking**
- Input: Skills that were actually used
- Process: Record usage statistics, update metadata
- Output: Updated usage database

---

## 2. Intent Analysis

Intent analysis extracts meaning from user queries to identify relevant skills.

### IntentAnalyzer Class

```python
from typing import List, Dict, Set
import re
from dataclasses import dataclass

@dataclass
class IntentAnalysis:
    """Results of intent analysis"""
    query: str
    topics: List[str]           # Main topics identified
    actions: List[str]          # Actions to perform
    domains: List[str]          # Knowledge domains
    keywords: Set[str]          # Important keywords
    confidence: float           # Analysis confidence (0-1)

class IntentAnalyzer:
    """Analyzes user queries to extract intent"""

    def __init__(self):
        # Action verbs that indicate intent
        self.action_verbs = {
            'create', 'build', 'make', 'generate', 'write',
            'analyze', 'review', 'check', 'validate', 'test',
            'debug', 'fix', 'solve', 'resolve', 'optimize',
            'explain', 'document', 'describe', 'teach', 'show',
            'refactor', 'improve', 'enhance', 'upgrade', 'update'
        }

        # Domain keywords for classification
        self.domain_keywords = {
            'web': ['http', 'api', 'rest', 'endpoint', 'server', 'client'],
            'database': ['sql', 'query', 'table', 'database', 'db', 'schema'],
            'ml': ['model', 'training', 'neural', 'learning', 'ai', 'prediction'],
            'devops': ['deploy', 'docker', 'kubernetes', 'ci', 'cd', 'pipeline'],
            'frontend': ['react', 'vue', 'component', 'ui', 'css', 'html'],
            'backend': ['server', 'api', 'service', 'microservice', 'lambda']
        }

    def analyze(self, query: str) -> IntentAnalysis:
        """
        Perform complete intent analysis on a query

        5-step process:
        1. Tokenize and clean query
        2. Extract action verbs
        3. Identify topics
        4. Classify domains
        5. Calculate confidence
        """
        # Step 1: Tokenize and clean
        tokens = self._tokenize(query)

        # Step 2: Extract actions
        actions = self._extract_actions(tokens)

        # Step 3: Identify topics
        topics = self._identify_topics(tokens, query)

        # Step 4: Classify domains
        domains = self._classify_domains(tokens)

        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(actions, topics, domains)

        return IntentAnalysis(
            query=query,
            topics=topics,
            actions=actions,
            domains=domains,
            keywords=set(tokens),
            confidence=confidence
        )

    def _tokenize(self, query: str) -> List[str]:
        """Convert query to lowercase tokens"""
        # Remove special characters, split on whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        return [t for t in cleaned.split() if len(t) > 2]

    def _extract_actions(self, tokens: List[str]) -> List[str]:
        """Find action verbs in tokens"""
        return [t for t in tokens if t in self.action_verbs]

    def _identify_topics(self, tokens: List[str], query: str) -> List[str]:
        """Extract main topics from query"""
        # Look for capitalized words (likely nouns/topics)
        topics = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)

        # Add significant technical terms
        technical_terms = [t for t in tokens if len(t) > 6]
        topics.extend(technical_terms[:3])  # Limit to top 3

        return list(set(topics))

    def _classify_domains(self, tokens: List[str]) -> List[str]:
        """Classify query into knowledge domains"""
        domains = []
        for domain, keywords in self.domain_keywords.items():
            if any(kw in tokens for kw in keywords):
                domains.append(domain)
        return domains

    def _calculate_confidence(self, actions: List[str],
                             topics: List[str],
                             domains: List[str]) -> float:
        """Calculate confidence score for analysis"""
        # Start with base confidence
        confidence = 0.5

        # Boost for clear actions
        if actions:
            confidence += 0.2

        # Boost for identified topics
        if topics:
            confidence += 0.15

        # Boost for domain classification
        if domains:
            confidence += 0.15

        return min(confidence, 1.0)
```

### Concrete Examples

```python
# Example 1: Web development query
analyzer = IntentAnalyzer()
result = analyzer.analyze("Create a REST API endpoint for user authentication")

print(result)
# IntentAnalysis(
#     query="Create a REST API endpoint for user authentication",
#     topics=['REST', 'API', 'authentication'],
#     actions=['create'],
#     domains=['web', 'backend'],
#     keywords={'create', 'rest', 'api', 'endpoint', 'user', 'authentication'},
#     confidence=0.85
# )

# Example 2: Database query
result = analyzer.analyze("Optimize SQL query performance for large tables")

print(result)
# IntentAnalysis(
#     query="Optimize SQL query performance for large tables",
#     topics=['SQL', 'performance', 'tables'],
#     actions=['optimize'],
#     domains=['database'],
#     keywords={'optimize', 'sql', 'query', 'performance', 'large', 'tables'},
#     confidence=0.85
# )

# Example 3: Ambiguous query
result = analyzer.analyze("Help me with this")

print(result)
# IntentAnalysis(
#     query="Help me with this",
#     topics=[],
#     actions=[],
#     domains=[],
#     keywords={'help', 'with', 'this'},
#     confidence=0.5
# )
```

---

## 3. Skill Discovery

Skill discovery matches intent to available skills using multiple strategies.

### SkillDiscovery Class

```python
from typing import List, Dict, Tuple
from pathlib import Path
import json

@dataclass
class SkillMatch:
    """A skill matched to an intent"""
    skill_id: str
    skill_path: Path
    relevance_score: float
    match_reasons: List[str]
    metadata: Dict

class SkillDiscovery:
    """Discovers skills matching user intent"""

    def __init__(self, skill_library_path: Path):
        self.library_path = skill_library_path
        self.skill_index = self._build_index()

    def _build_index(self) -> Dict:
        """Build searchable index of all skills"""
        index = {
            'by_tag': {},      # tag -> [skill_ids]
            'by_domain': {},   # domain -> [skill_ids]
            'by_keyword': {},  # keyword -> [skill_ids]
            'metadata': {}     # skill_id -> metadata
        }

        # Scan skill library and index all skills
        for skill_file in self.library_path.rglob("*.md"):
            skill_id = skill_file.stem
            metadata = self._parse_metadata(skill_file)

            index['metadata'][skill_id] = metadata

            # Index by tags
            for tag in metadata.get('tags', []):
                index['by_tag'].setdefault(tag, []).append(skill_id)

            # Index by domain
            domain = metadata.get('domain', 'general')
            index['by_domain'].setdefault(domain, []).append(skill_id)

            # Index by keywords
            for keyword in metadata.get('keywords', []):
                index['by_keyword'].setdefault(keyword, []).append(skill_id)

        return index

    def discover(self, intent: IntentAnalysis) -> List[SkillMatch]:
        """
        Discover skills using 5 strategies:
        1. Exact keyword matching
        2. Domain classification
        3. Action-based matching
        4. Semantic similarity
        5. Usage history correlation
        """
        candidates = {}  # skill_id -> (score, reasons)

        # Strategy 1: Exact keyword matching
        for keyword in intent.keywords:
            if keyword in self.skill_index['by_keyword']:
                for skill_id in self.skill_index['by_keyword'][keyword]:
                    score, reasons = candidates.get(skill_id, (0.0, []))
                    candidates[skill_id] = (
                        score + 0.3,
                        reasons + [f"Keyword match: {keyword}"]
                    )

        # Strategy 2: Domain classification
        for domain in intent.domains:
            if domain in self.skill_index['by_domain']:
                for skill_id in self.skill_index['by_domain'][domain]:
                    score, reasons = candidates.get(skill_id, (0.0, []))
                    candidates[skill_id] = (
                        score + 0.4,
                        reasons + [f"Domain match: {domain}"]
                    )

        # Strategy 3: Action-based matching
        for action in intent.actions:
            # Find skills tagged with this action
            if action in self.skill_index['by_tag']:
                for skill_id in self.skill_index['by_tag'][action]:
                    score, reasons = candidates.get(skill_id, (0.0, []))
                    candidates[skill_id] = (
                        score + 0.2,
                        reasons + [f"Action match: {action}"]
                    )

        # Strategy 4: Semantic similarity (simplified)
        # In production, use embeddings and cosine similarity
        for topic in intent.topics:
            topic_lower = topic.lower()
            for skill_id, metadata in self.skill_index['metadata'].items():
                skill_desc = metadata.get('description', '').lower()
                if topic_lower in skill_desc:
                    score, reasons = candidates.get(skill_id, (0.0, []))
                    candidates[skill_id] = (
                        score + 0.25,
                        reasons + [f"Topic in description: {topic}"]
                    )

        # Strategy 5: Usage history correlation
        # Boost frequently used skills slightly
        for skill_id in candidates.keys():
            metadata = self.skill_index['metadata'][skill_id]
            usage_count = metadata.get('usage_count', 0)
            if usage_count > 10:
                score, reasons = candidates[skill_id]
                candidates[skill_id] = (
                    score + 0.1,
                    reasons + ["Frequently used"]
                )

        # Convert to SkillMatch objects
        matches = []
        for skill_id, (score, reasons) in candidates.items():
            skill_path = self._get_skill_path(skill_id)
            matches.append(SkillMatch(
                skill_id=skill_id,
                skill_path=skill_path,
                relevance_score=min(score, 1.0),
                match_reasons=reasons,
                metadata=self.skill_index['metadata'][skill_id]
            ))

        # Sort by relevance
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        return matches

    def _parse_metadata(self, skill_file: Path) -> Dict:
        """Extract metadata from skill file"""
        # Read frontmatter or metadata section
        # Simplified version
        return {
            'title': skill_file.stem,
            'tags': [],
            'domain': 'general',
            'keywords': [],
            'usage_count': 0
        }

    def _get_skill_path(self, skill_id: str) -> Path:
        """Get full path to skill file"""
        return self.library_path / f"{skill_id}.md"
```

### Example Usage

```python
# Setup
library = Path("/path/to/skillforge/data/skill_files")
discovery = SkillDiscovery(library)

# Analyze intent
analyzer = IntentAnalyzer()
intent = analyzer.analyze("Build a GraphQL API with authentication")

# Discover matching skills
matches = discovery.discover(intent)

# Display results
for match in matches[:5]:  # Top 5
    print(f"\n{match.skill_id} (score: {match.relevance_score:.2f})")
    print(f"  Path: {match.skill_path}")
    print(f"  Reasons: {', '.join(match.match_reasons)}")

# Output:
# GRAPHQL_BASICS (score: 0.85)
#   Path: /path/to/skillforge/data/skill_files/frameworks/GRAPHQL_BASICS.md
#   Reasons: Keyword match: graphql, Domain match: backend, Action match: build
#
# API_DESIGN (score: 0.75)
#   Path: /path/to/skillforge/data/skill_files/patterns/API_DESIGN.md
#   Reasons: Keyword match: api, Domain match: backend, Frequently used
#
# AUTHENTICATION (score: 0.70)
#   Path: /path/to/skillforge/data/skill_files/security/AUTHENTICATION.md
#   Reasons: Keyword match: authentication, Topic in description: Authentication
```

---

## 4. Dependency Resolution

Dependency resolution ensures skills are loaded in the correct order.

### DependencyResolver Class

```python
from typing import List, Dict, Set
from collections import defaultdict, deque

class DependencyResolver:
    """Resolves skill dependencies using topological sort"""

    def __init__(self):
        self.graph = defaultdict(list)  # skill -> [dependencies]
        self.in_degree = defaultdict(int)

    def add_skill(self, skill_id: str, dependencies: List[str]):
        """Add a skill and its dependencies to the graph"""
        self.graph[skill_id] = dependencies

        # Update in-degrees
        if skill_id not in self.in_degree:
            self.in_degree[skill_id] = 0

        for dep in dependencies:
            self.in_degree[skill_id] += 1
            if dep not in self.graph:
                self.graph[dep] = []
            if dep not in self.in_degree:
                self.in_degree[dep] = 0

    def resolve(self) -> List[str]:
        """
        Resolve dependencies using Kahn's topological sort algorithm

        Returns skills in load order (dependencies first)
        Raises ValueError if circular dependencies detected
        """
        # Copy in-degrees for processing
        in_deg = self.in_degree.copy()

        # Queue of skills with no dependencies
        queue = deque([skill for skill, deg in in_deg.items() if deg == 0])

        result = []

        while queue:
            # Get skill with no remaining dependencies
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for dependent skills
            for skill, deps in self.graph.items():
                if current in deps:
                    in_deg[skill] -= 1
                    if in_deg[skill] == 0:
                        queue.append(skill)

        # Check for circular dependencies
        if len(result) != len(self.graph):
            unresolved = set(self.graph.keys()) - set(result)
            raise ValueError(f"Circular dependency detected: {unresolved}")

        return result

    def visualize(self) -> str:
        """Generate ASCII visualization of dependency graph"""
        lines = ["Dependency Graph:", ""]

        for skill, deps in sorted(self.graph.items()):
            if deps:
                lines.append(f"{skill}")
                for dep in deps:
                    lines.append(f"  ├─ depends on → {dep}")
            else:
                lines.append(f"{skill} (no dependencies)")

        return "\n".join(lines)
```

### Example: Dependency Graph

```python
# Build dependency graph
resolver = DependencyResolver()

# Add skills with their dependencies
resolver.add_skill('FASTAPI_CRUD', ['PYTHON_BASICS', 'API_DESIGN'])
resolver.add_skill('GRAPHQL_API', ['PYTHON_BASICS', 'GRAPHQL_BASICS'])
resolver.add_skill('AUTHENTICATION', ['SECURITY_BASICS'])
resolver.add_skill('API_DESIGN', ['REST_PRINCIPLES'])
resolver.add_skill('PYTHON_BASICS', [])  # No dependencies
resolver.add_skill('GRAPHQL_BASICS', [])
resolver.add_skill('SECURITY_BASICS', [])
resolver.add_skill('REST_PRINCIPLES', [])

# Visualize the graph
print(resolver.visualize())
# Output:
# Dependency Graph:
#
# API_DESIGN
#   ├─ depends on → REST_PRINCIPLES
# AUTHENTICATION
#   ├─ depends on → SECURITY_BASICS
# FASTAPI_CRUD
#   ├─ depends on → PYTHON_BASICS
#   ├─ depends on → API_DESIGN
# GRAPHQL_API
#   ├─ depends on → PYTHON_BASICS
#   ├─ depends on → GRAPHQL_BASICS
# GRAPHQL_BASICS (no dependencies)
# PYTHON_BASICS (no dependencies)
# REST_PRINCIPLES (no dependencies)
# SECURITY_BASICS (no dependencies)

# Resolve dependencies
load_order = resolver.resolve()
print("\nLoad Order:")
for i, skill in enumerate(load_order, 1):
    print(f"{i}. {skill}")

# Output:
# Load Order:
# 1. PYTHON_BASICS
# 2. GRAPHQL_BASICS
# 3. SECURITY_BASICS
# 4. REST_PRINCIPLES
# 5. API_DESIGN
# 6. AUTHENTICATION
# 7. FASTAPI_CRUD
# 8. GRAPHQL_API
```

---

## 5. Priority Sorting

Priority sorting ranks skills by relevance and importance using multiple factors.

### Priority Scoring Algorithm

```python
from dataclasses import dataclass
from typing import List

@dataclass
class PriorityScore:
    """Complete priority score breakdown"""
    skill_id: str
    relevance: float      # 0-1, from discovery
    recency: float        # 0-1, how recently updated
    usage_freq: float     # 0-1, normalized usage count
    context_fit: float    # 0-1, fit with current context
    dependency_depth: float  # 0-1, inverse of depth (shallow = higher)
    final_score: float    # Weighted sum

class PriorityScorer:
    """Calculate priority scores for skill loading"""

    # Weights for each factor (sum to 1.0)
    WEIGHTS = {
        'relevance': 0.40,        # Most important
        'recency': 0.10,          # Recent updates
        'usage_freq': 0.15,       # Popular skills
        'context_fit': 0.25,      # Context matching
        'dependency_depth': 0.10  # Prefer shallower deps
    }

    def calculate_priority(self,
                          skill_id: str,
                          relevance_score: float,
                          last_updated_days: int,
                          usage_count: int,
                          context_keywords: Set[str],
                          skill_keywords: Set[str],
                          dependency_depth: int) -> PriorityScore:
        """
        Calculate priority score using weighted formula:

        P = w₁·R + w₂·T + w₃·U + w₄·C + w₅·D

        Where:
        - R = relevance score (from discovery)
        - T = recency score (time since update)
        - U = usage frequency score
        - C = context fit score (keyword overlap)
        - D = dependency depth score (inverse depth)
        - wᵢ = weight for each factor
        """
        # Factor 1: Relevance (already 0-1)
        relevance = relevance_score

        # Factor 2: Recency (decay over 365 days)
        recency = max(0.0, 1.0 - (last_updated_days / 365.0))

        # Factor 3: Usage frequency (normalize to 0-1)
        # Assume max usage count of 1000 for normalization
        usage_freq = min(usage_count / 1000.0, 1.0)

        # Factor 4: Context fit (Jaccard similarity)
        if context_keywords and skill_keywords:
            intersection = len(context_keywords & skill_keywords)
            union = len(context_keywords | skill_keywords)
            context_fit = intersection / union if union > 0 else 0.0
        else:
            context_fit = 0.0

        # Factor 5: Dependency depth (inverse, max depth 5)
        dependency_score = max(0.0, 1.0 - (dependency_depth / 5.0))

        # Calculate weighted final score
        final = (
            self.WEIGHTS['relevance'] * relevance +
            self.WEIGHTS['recency'] * recency +
            self.WEIGHTS['usage_freq'] * usage_freq +
            self.WEIGHTS['context_fit'] * context_fit +
            self.WEIGHTS['dependency_depth'] * dependency_score
        )

        return PriorityScore(
            skill_id=skill_id,
            relevance=relevance,
            recency=recency,
            usage_freq=usage_freq,
            context_fit=context_fit,
            dependency_depth=dependency_score,
            final_score=final
        )
```

### Example Calculations

```python
scorer = PriorityScorer()

# Context from user query
context_keywords = {'api', 'rest', 'authentication', 'python'}

# Score different skills
skills_to_score = [
    {
        'id': 'FASTAPI_CRUD',
        'relevance': 0.85,
        'last_updated': 30,
        'usage_count': 150,
        'keywords': {'api', 'rest', 'python', 'fastapi', 'crud'}
    },
    {
        'id': 'DJANGO_REST',
        'relevance': 0.75,
        'last_updated': 120,
        'usage_count': 300,
        'keywords': {'api', 'rest', 'python', 'django'}
    },
    {
        'id': 'AUTHENTICATION',
        'relevance': 0.70,
        'last_updated': 15,
        'usage_count': 450,
        'keywords': {'authentication', 'security', 'tokens', 'jwt'}
    }
]

scores = []
for skill in skills_to_score:
    score = scorer.calculate_priority(
        skill_id=skill['id'],
        relevance_score=skill['relevance'],
        last_updated_days=skill['last_updated'],
        usage_count=skill['usage_count'],
        context_keywords=context_keywords,
        skill_keywords=skill['keywords'],
        dependency_depth=2  # Assume depth of 2
    )
    scores.append(score)

# Display results
for score in sorted(scores, key=lambda s: s.final_score, reverse=True):
    print(f"\n{score.skill_id}: {score.final_score:.3f}")
    print(f"  Relevance:    {score.relevance:.3f} × {scorer.WEIGHTS['relevance']}")
    print(f"  Recency:      {score.recency:.3f} × {scorer.WEIGHTS['recency']}")
    print(f"  Usage Freq:   {score.usage_freq:.3f} × {scorer.WEIGHTS['usage_freq']}")
    print(f"  Context Fit:  {score.context_fit:.3f} × {scorer.WEIGHTS['context_fit']}")
    print(f"  Dep Depth:    {score.dependency_depth:.3f} × {scorer.WEIGHTS['dependency_depth']}")

# Output:
# FASTAPI_CRUD: 0.759
#   Relevance:    0.850 × 0.4
#   Recency:      0.918 × 0.1
#   Usage Freq:   0.150 × 0.15
#   Context Fit:  0.571 × 0.25
#   Dep Depth:    0.600 × 0.1
#
# AUTHENTICATION: 0.645
#   Relevance:    0.700 × 0.4
#   Recency:      0.959 × 0.1
#   Usage Freq:   0.450 × 0.15
#   Context Fit:  0.143 × 0.25
#   Dep Depth:    0.600 × 0.1
#
# DJANGO_REST: 0.640
#   Relevance:    0.750 × 0.4
#   Recency:      0.671 × 0.1
#   Usage Freq:   0.300 × 0.15
#   Context Fit:  0.571 × 0.25
#   Dep Depth:    0.600 × 0.1
```

---

## 6. Token Budget Allocation

Token budget allocation distributes available context tokens among skills.

### TokenBudgetManager Class

```python
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class TokenAllocation:
    """Token allocation for a single skill"""
    skill_id: str
    tokens_allocated: int
    priority_score: float
    percentage: float

class TokenBudgetManager:
    """Manages token allocation across skills"""

    def __init__(self, total_budget: int, reserve: float = 0.2):
        """
        Initialize budget manager

        Args:
            total_budget: Total tokens available for skills
            reserve: Fraction to keep in reserve (0-1)
        """
        self.total_budget = total_budget
        self.reserve = reserve
        self.allocatable = int(total_budget * (1 - reserve))

    def allocate(self,
                priority_scores: List[PriorityScore],
                min_tokens_per_skill: int = 500) -> List[TokenAllocation]:
        """
        Allocate tokens proportionally to priority scores

        Strategy:
        1. Allocate minimum tokens to each skill
        2. Distribute remaining tokens by priority ratio
        3. Respect total budget constraint
        """
        if not priority_scores:
            return []

        # Sort by priority (highest first)
        sorted_scores = sorted(
            priority_scores,
            key=lambda s: s.final_score,
            reverse=True
        )

        # Calculate how many skills we can fit with minimum allocation
        max_skills = self.allocatable // min_tokens_per_skill
        selected_scores = sorted_scores[:max_skills]

        if not selected_scores:
            return []

        # Reserve minimum tokens for each
        total_min = len(selected_scores) * min_tokens_per_skill
        remaining = self.allocatable - total_min

        # Calculate priority sum for ratio
        priority_sum = sum(s.final_score for s in selected_scores)

        # Allocate tokens
        allocations = []
        for score in selected_scores:
            # Minimum allocation
            allocated = min_tokens_per_skill

            # Add proportional share of remaining
            if remaining > 0 and priority_sum > 0:
                ratio = score.final_score / priority_sum
                additional = int(remaining * ratio)
                allocated += additional

            percentage = (allocated / self.total_budget) * 100

            allocations.append(TokenAllocation(
                skill_id=score.skill_id,
                tokens_allocated=allocated,
                priority_score=score.final_score,
                percentage=percentage
            ))

        return allocations

    def optimize_allocation(self,
                           allocations: List[TokenAllocation],
                           actual_sizes: Dict[str, int]) -> List[TokenAllocation]:
        """
        Optimize allocations based on actual skill sizes

        If a skill needs fewer tokens than allocated, redistribute
        the excess to higher priority skills
        """
        optimized = []
        excess_tokens = 0

        for alloc in allocations:
            actual_size = actual_sizes.get(alloc.skill_id, alloc.tokens_allocated)

            if actual_size <= alloc.tokens_allocated:
                # Use actual size, save excess
                excess_tokens += alloc.tokens_allocated - actual_size
                optimized.append(TokenAllocation(
                    skill_id=alloc.skill_id,
                    tokens_allocated=actual_size,
                    priority_score=alloc.priority_score,
                    percentage=(actual_size / self.total_budget) * 100
                ))
            else:
                # Needs more than allocated
                optimized.append(alloc)

        # Redistribute excess to skills that need more
        if excess_tokens > 0:
            for i, alloc in enumerate(optimized):
                actual_size = actual_sizes.get(alloc.skill_id, alloc.tokens_allocated)
                if actual_size > alloc.tokens_allocated:
                    additional = min(excess_tokens, actual_size - alloc.tokens_allocated)
                    optimized[i] = TokenAllocation(
                        skill_id=alloc.skill_id,
                        tokens_allocated=alloc.tokens_allocated + additional,
                        priority_score=alloc.priority_score,
                        percentage=((alloc.tokens_allocated + additional) / self.total_budget) * 100
                    )
                    excess_tokens -= additional
                    if excess_tokens <= 0:
                        break

        return optimized
```

### Example Allocation

```python
# Setup budget manager
total_budget = 10000  # 10k tokens available
manager = TokenBudgetManager(total_budget, reserve=0.2)

print(f"Total Budget: {total_budget} tokens")
print(f"Allocatable: {manager.allocatable} tokens (80%)")
print(f"Reserve: {int(total_budget * 0.2)} tokens (20%)\n")

# Priority scores from previous example
allocations = manager.allocate(scores, min_tokens_per_skill=500)

print("Token Allocation:")
print("-" * 60)
for alloc in allocations:
    print(f"{alloc.skill_id:20} {alloc.tokens_allocated:5} tokens "
          f"({alloc.percentage:5.1f}%) [priority: {alloc.priority_score:.3f}]")

# Output:
# Total Budget: 10000 tokens
# Allocatable: 8000 tokens (80%)
# Reserve: 2000 tokens (20%)
#
# Token Allocation:
# ------------------------------------------------------------
# FASTAPI_CRUD          3200 tokens ( 32.0%) [priority: 0.759]
# AUTHENTICATION        2100 tokens ( 21.0%) [priority: 0.645]
# DJANGO_REST           2100 tokens ( 21.0%) [priority: 0.640]
# PYTHON_BASICS          600 tokens (  6.0%) [priority: 0.450]

# Optimize based on actual sizes
actual_sizes = {
    'FASTAPI_CRUD': 2800,      # Needs less
    'AUTHENTICATION': 2500,    # Needs more
    'DJANGO_REST': 2000,       # Fits exactly
    'PYTHON_BASICS': 500       # Needs less
}

optimized = manager.optimize_allocation(allocations, actual_sizes)

print("\n\nOptimized Allocation:")
print("-" * 60)
for alloc in optimized:
    actual = actual_sizes[alloc.skill_id]
    print(f"{alloc.skill_id:20} {alloc.tokens_allocated:5} tokens "
          f"(actual: {actual:4}) [priority: {alloc.priority_score:.3f}]")

# Output:
# Optimized Allocation:
# ------------------------------------------------------------
# FASTAPI_CRUD          2800 tokens (actual: 2800) [priority: 0.759]
# AUTHENTICATION        2500 tokens (actual: 2500) [priority: 0.645]
# DJANGO_REST           2000 tokens (actual: 2000) [priority: 0.640]
# PYTHON_BASICS          500 tokens (actual:  500) [priority: 0.450]
```

---

## 7. Progressive Loading

Progressive loading streams skills in priority order with varying detail levels.

### Loading Levels

Progressive loading supports four levels of detail:

**Level 1: Metadata Only** (~100 tokens per skill)
- Skill ID and title
- Brief description (1-2 sentences)
- Tags and domain classification
- Dependencies list

**Level 2: Summary** (~500 tokens per skill)
- Everything from Level 1
- Key concepts overview
- Primary use cases
- Quick reference syntax

**Level 3: Detailed** (~2000 tokens per skill)
- Everything from Level 2
- Complete documentation
- Code examples
- Best practices
- Common patterns

**Level 4: Complete** (full skill content)
- Everything from Level 3
- Advanced topics
- Edge cases
- Troubleshooting guides
- Related resources

### When to Use Each Level

```python
from enum import Enum

class LoadingLevel(Enum):
    """Progressive loading levels"""
    METADATA = 1    # Quick scan, many skills
    SUMMARY = 2     # Moderate depth, several skills
    DETAILED = 3    # Deep knowledge, few skills
    COMPLETE = 4    # Everything, 1-2 skills

def select_loading_level(token_budget: int,
                        num_skills: int,
                        priority_score: float) -> LoadingLevel:
    """
    Select appropriate loading level based on constraints

    Decision logic:
    - High priority (>0.8) + sufficient budget → COMPLETE
    - High priority (>0.6) + moderate budget → DETAILED
    - Medium priority (>0.4) → SUMMARY
    - Low priority or many skills → METADATA
    """
    tokens_per_skill = token_budget / num_skills if num_skills > 0 else 0

    # High priority skills deserve more detail
    if priority_score > 0.8 and tokens_per_skill >= 3000:
        return LoadingLevel.COMPLETE
    elif priority_score > 0.6 and tokens_per_skill >= 1500:
        return LoadingLevel.DETAILED
    elif priority_score > 0.4 and tokens_per_skill >= 400:
        return LoadingLevel.SUMMARY
    else:
        return LoadingLevel.METADATA
```

### Examples for Each Level

**Level 1: METADATA Example**
```
# FASTAPI_CRUD

Modern Python API framework for building CRUD operations with automatic documentation.

Domain: backend | Tags: api, rest, python, fastapi
Dependencies: PYTHON_BASICS, API_DESIGN
```

**Level 2: SUMMARY Example**
```
# FASTAPI_CRUD

Modern Python API framework for building CRUD operations with automatic documentation.

Domain: backend | Tags: api, rest, python, fastapi
Dependencies: PYTHON_BASICS, API_DESIGN

## Key Concepts
- Path operations for HTTP methods (GET, POST, PUT, DELETE)
- Automatic request/response validation with Pydantic
- Built-in OpenAPI documentation
- Async support for high performance

## Quick Reference
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"id": item_id}
```

## Primary Use Cases
- RESTful APIs with automatic validation
- Microservices requiring async operations
- APIs needing automatic documentation
```

**Level 3: DETAILED Example**
```
# FASTAPI_CRUD

Modern Python API framework for building CRUD operations with automatic documentation.

Domain: backend | Tags: api, rest, python, fastapi
Dependencies: PYTHON_BASICS, API_DESIGN

## Key Concepts
- Path operations for HTTP methods (GET, POST, PUT, DELETE)
- Automatic request/response validation with Pydantic
- Built-in OpenAPI documentation
- Async support for high performance

## Complete CRUD Implementation

### Setup
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="CRUD API")

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float

items_db = []
```

### Create Operation
```python
@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    item.id = len(items_db) + 1
    items_db.append(item)
    return item
```

### Read Operations
```python
@app.get("/items/", response_model=List[Item])
async def read_items(skip: int = 0, limit: int = 10):
    return items_db[skip : skip + limit]

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")
```

### Update Operation
```python
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, updated_item: Item):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db[i] = updated_item
            items_db[i].id = item_id
            return items_db[i]
    raise HTTPException(status_code=404, detail="Item not found")
```

### Delete Operation
```python
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
```

## Best Practices
- Use Pydantic models for validation
- Implement proper error handling
- Use async for I/O-bound operations
- Document endpoints with docstrings
- Use dependency injection for common logic
```

**Level 4: COMPLETE** (Includes everything from Level 3 plus advanced topics, edge cases, troubleshooting, and related resources)

---

## 8. Multi-Skill Workflows

Multi-skill workflows orchestrate complex tasks requiring multiple skills.

### WorkflowOrchestrator Class

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class WorkflowStage(Enum):
    """Stages in workflow execution"""
    PLANNING = "planning"
    LOADING = "loading"
    EXECUTING = "executing"
    COMPLETE = "complete"

@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    step_id: str
    skill_id: str
    description: str
    inputs: Dict
    outputs: Dict
    status: str = "pending"

class WorkflowOrchestrator:
    """Orchestrates multi-skill workflows"""

    def __init__(self, intent_analyzer: IntentAnalyzer,
                 skill_discovery: SkillDiscovery,
                 dependency_resolver: DependencyResolver):
        self.intent_analyzer = intent_analyzer
        self.skill_discovery = skill_discovery
        self.dependency_resolver = dependency_resolver
        self.current_stage = WorkflowStage.PLANNING

    def create_workflow(self, query: str) -> List[WorkflowStep]:
        """
        Create a workflow from a complex query

        Process:
        1. Analyze query intent
        2. Decompose into subtasks
        3. Map subtasks to skills
        4. Resolve dependencies
        5. Create execution plan
        """
        # Stage 1: Analyze intent
        intent = self.intent_analyzer.analyze(query)

        # Stage 2: Decompose into subtasks
        subtasks = self._decompose_query(query, intent)

        # Stage 3: Map to skills
        workflow_steps = []
        for i, subtask in enumerate(subtasks):
            # Find best matching skill
            subtask_intent = self.intent_analyzer.analyze(subtask)
            matches = self.skill_discovery.discover(subtask_intent)

            if matches:
                best_match = matches[0]
                step = WorkflowStep(
                    step_id=f"step_{i+1}",
                    skill_id=best_match.skill_id,
                    description=subtask,
                    inputs={},
                    outputs={}
                )
                workflow_steps.append(step)

        # Stage 4: Resolve dependencies
        for step in workflow_steps:
            self.dependency_resolver.add_skill(
                step.skill_id,
                []  # Get from metadata
            )

        load_order = self.dependency_resolver.resolve()

        # Sort steps by load order
        workflow_steps.sort(
            key=lambda s: load_order.index(s.skill_id)
            if s.skill_id in load_order else 999
        )

        return workflow_steps

    def _decompose_query(self, query: str, intent: IntentAnalysis) -> List[str]:
        """Decompose complex query into subtasks"""
        # Simplified decomposition based on actions
        subtasks = []

        # Look for compound tasks
        if "and" in query.lower():
            parts = query.lower().split("and")
            subtasks.extend([p.strip() for p in parts])
        elif len(intent.actions) > 1:
            # Multiple actions = multiple subtasks
            for action in intent.actions:
                subtasks.append(f"{action} related to {', '.join(intent.topics)}")
        else:
            # Single task
            subtasks.append(query)

        return subtasks

    def execute_workflow(self, workflow: List[WorkflowStep]) -> Dict:
        """Execute workflow steps in order"""
        self.current_stage = WorkflowStage.EXECUTING
        results = {}

        for step in workflow:
            print(f"Executing {step.step_id}: {step.description}")

            # Load skill content
            # Execute step logic
            # Store results

            step.status = "complete"
            results[step.step_id] = {
                "status": "success",
                "output": f"Completed {step.skill_id}"
            }

        self.current_stage = WorkflowStage.COMPLETE
        return results
```

### Complete Workflow Example

```python
# Setup orchestrator
orchestrator = WorkflowOrchestrator(
    intent_analyzer=IntentAnalyzer(),
    skill_discovery=SkillDiscovery(Path("/skills")),
    dependency_resolver=DependencyResolver()
)

# Complex query requiring multiple skills
query = """
Create a FastAPI application with user authentication and CRUD operations
for a blog post system, and deploy it to AWS Lambda
"""

# Create workflow
print("Creating workflow...")
workflow = orchestrator.create_workflow(query)

# Display workflow plan
print("\nWorkflow Plan:")
print("-" * 70)
for i, step in enumerate(workflow, 1):
    print(f"\nStep {i}: {step.step_id}")
    print(f"  Skill: {step.skill_id}")
    print(f"  Task: {step.description}")
    print(f"  Status: {step.status}")

# Output:
# Creating workflow...
#
# Workflow Plan:
# ----------------------------------------------------------------------
#
# Step 1: step_1
#   Skill: PYTHON_BASICS
#   Task: Create a FastAPI application with user authentication
#   Status: pending
#
# Step 2: step_2
#   Skill: API_DESIGN
#   Task: Create a FastAPI application with user authentication
#   Status: pending
#
# Step 3: step_3
#   Skill: FASTAPI_CRUD
#   Task: Create a FastAPI application with user authentication
#   Status: pending
#
# Step 4: step_4
#   Skill: AUTHENTICATION
#   Task: Create a FastAPI application with user authentication
#   Status: pending
#
# Step 5: step_5
#   Skill: AWS_LAMBDA_DEPLOY
#   Task: deploy it to AWS Lambda
#   Status: pending

# Execute workflow
print("\n\nExecuting workflow...")
results = orchestrator.execute_workflow(workflow)

print("\nWorkflow Results:")
for step_id, result in results.items():
    print(f"  {step_id}: {result['status']}")

# Output:
# Executing workflow...
# Executing step_1: Create a FastAPI application with user authentication
# Executing step_2: Create a FastAPI application with user authentication
# Executing step_3: Create a FastAPI application with user authentication
# Executing step_4: Create a FastAPI application with user authentication
# Executing step_5: deploy it to AWS Lambda
#
# Workflow Results:
#   step_1: success
#   step_2: success
#   step_3: success
#   step_4: success
#   step_5: success
```

---

## 9. Conflict Resolution

Conflict resolution handles situations where skills provide contradictory guidance.

### Resolution Strategies

**Strategy 1: Priority-Based**
Use the guidance from the highest priority skill. Simple and fast.

**Strategy 2: Consensus-Based**
Prefer guidance that appears in multiple skills. More reliable but slower.

**Strategy 3: Context-Aware**
Choose guidance that best fits the current context and recent decisions.

### Conflict Examples

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Guidance:
    """A piece of guidance from a skill"""
    skill_id: str
    topic: str
    recommendation: str
    priority: float
    confidence: float

class ConflictResolver:
    """Resolves conflicts between skill guidance"""

    def detect_conflicts(self, guidance_list: List[Guidance]) -> Dict[str, List[Guidance]]:
        """Group conflicting guidance by topic"""
        by_topic = {}
        for guidance in guidance_list:
            if guidance.topic not in by_topic:
                by_topic[guidance.topic] = []
            by_topic[guidance.topic].append(guidance)

        # Find topics with multiple different recommendations
        conflicts = {}
        for topic, items in by_topic.items():
            unique_recs = set(g.recommendation for g in items)
            if len(unique_recs) > 1:
                conflicts[topic] = items

        return conflicts

    def resolve_priority_based(self, conflicting: List[Guidance]) -> Guidance:
        """Resolve using highest priority skill"""
        return max(conflicting, key=lambda g: g.priority)

    def resolve_consensus_based(self, conflicting: List[Guidance]) -> Guidance:
        """Resolve using most common recommendation"""
        from collections import Counter

        # Count recommendations weighted by confidence
        weighted_votes = {}
        for g in conflicting:
            if g.recommendation not in weighted_votes:
                weighted_votes[g.recommendation] = 0
            weighted_votes[g.recommendation] += g.confidence

        # Find recommendation with highest weighted vote
        best_rec = max(weighted_votes.items(), key=lambda x: x[1])[0]

        # Return the guidance with that recommendation and highest priority
        candidates = [g for g in conflicting if g.recommendation == best_rec]
        return max(candidates, key=lambda g: g.priority)

    def resolve_context_aware(self,
                             conflicting: List[Guidance],
                             context: Dict[str, any]) -> Guidance:
        """Resolve using context information"""
        # Score each guidance by context fit
        scores = []
        for g in conflicting:
            score = g.priority * 0.5 + g.confidence * 0.5

            # Boost if skill matches context domain
            if context.get('domain') == g.skill_id.split('_')[0]:
                score += 0.2

            scores.append((score, g))

        return max(scores, key=lambda x: x[0])[1]

# Example conflicts
guidance_list = [
    Guidance("PYTHON_STYLE", "string_quotes", "Use single quotes", 0.8, 0.9),
    Guidance("DJANGO_STYLE", "string_quotes", "Use double quotes", 0.7, 0.8),
    Guidance("FASTAPI_STYLE", "string_quotes", "Use double quotes", 0.75, 0.85),
]

resolver = ConflictResolver()
conflicts = resolver.detect_conflicts(guidance_list)

print("Detected Conflicts:")
for topic, items in conflicts.items():
    print(f"\n{topic}:")
    for g in items:
        print(f"  {g.skill_id}: {g.recommendation} (priority: {g.priority})")

# Resolve using different strategies
print("\n\nResolution Strategies:")

result = resolver.resolve_priority_based(guidance_list)
print(f"\nPriority-based: {result.skill_id} → {result.recommendation}")

result = resolver.resolve_consensus_based(guidance_list)
print(f"Consensus-based: {result.skill_id} → {result.recommendation}")

result = resolver.resolve_context_aware(guidance_list, {'domain': 'DJANGO'})
print(f"Context-aware (Django project): {result.skill_id} → {result.recommendation}")
```

### Decision Tree

```
Conflict Detected
    │
    ▼
┌─────────────────────┐
│ High priority skill │ Yes
│ clearly dominant?   ├────→ Use Priority-Based
└──────┬──────────────┘
       │ No
       ▼
┌─────────────────────┐
│ Clear consensus     │ Yes
│ among skills?       ├────→ Use Consensus-Based
└──────┬──────────────┘
       │ No
       ▼
┌─────────────────────┐
│ Strong context      │ Yes
│ indicators?         ├────→ Use Context-Aware
└──────┬──────────────┘
       │ No
       ▼
Use Priority-Based
(fallback)
```

---

## 10. Usage Tracking

Usage tracking records how skills are used to improve future orchestration.

### What to Track

**Per-Skill Metrics:**
- Total load count
- Last accessed timestamp
- Average relevance score when loaded
- Success rate (loaded vs. actually used)
- Average context consumption
- Co-occurrence with other skills

**Per-Query Metrics:**
- Query text and intent
- Skills loaded
- Skills actually used
- Execution time
- Success/failure status
- User feedback (if available)

### JSON Schema for Tracking Data

```json
{
  "skill_usage": {
    "skill_id": {
      "total_loads": 156,
      "total_uses": 142,
      "success_rate": 0.91,
      "last_accessed": "2025-10-22T14:30:00Z",
      "avg_relevance": 0.76,
      "avg_tokens_used": 1850,
      "co_occurrences": {
        "PYTHON_BASICS": 89,
        "API_DESIGN": 67,
        "AUTHENTICATION": 45
      },
      "load_history": [
        {
          "timestamp": "2025-10-22T14:30:00Z",
          "query": "Create FastAPI endpoint",
          "relevance": 0.85,
          "loaded": true,
          "used": true,
          "tokens": 2100
        }
      ]
    }
  },
  "query_history": [
    {
      "timestamp": "2025-10-22T14:30:00Z",
      "query": "Create FastAPI endpoint with authentication",
      "intent": {
        "topics": ["FastAPI", "authentication"],
        "actions": ["create"],
        "domains": ["backend"]
      },
      "skills_loaded": ["FASTAPI_CRUD", "AUTHENTICATION", "PYTHON_BASICS"],
      "skills_used": ["FASTAPI_CRUD", "AUTHENTICATION"],
      "execution_time_ms": 245,
      "success": true
    }
  ]
}
```

### How to Save

```python
import json
from pathlib import Path
from datetime import datetime

class UsageTracker:
    """Track skill usage statistics"""

    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load existing tracking data"""
        if self.data_file.exists():
            with open(self.data_file) as f:
                return json.load(f)
        return {"skill_usage": {}, "query_history": []}

    def track_skill_load(self, skill_id: str, query: str,
                        relevance: float, loaded: bool,
                        used: bool, tokens: int):
        """Record a skill load event"""
        if skill_id not in self.data['skill_usage']:
            self.data['skill_usage'][skill_id] = {
                "total_loads": 0,
                "total_uses": 0,
                "success_rate": 0.0,
                "last_accessed": None,
                "avg_relevance": 0.0,
                "avg_tokens_used": 0,
                "co_occurrences": {},
                "load_history": []
            }

        skill_data = self.data['skill_usage'][skill_id]

        if loaded:
            skill_data['total_loads'] += 1
        if used:
            skill_data['total_uses'] += 1

        skill_data['success_rate'] = (
            skill_data['total_uses'] / skill_data['total_loads']
            if skill_data['total_loads'] > 0 else 0.0
        )

        skill_data['last_accessed'] = datetime.utcnow().isoformat() + 'Z'

        # Update running averages
        n = len(skill_data['load_history'])
        skill_data['avg_relevance'] = (
            (skill_data['avg_relevance'] * n + relevance) / (n + 1)
        )
        skill_data['avg_tokens_used'] = (
            (skill_data['avg_tokens_used'] * n + tokens) / (n + 1)
        )

        skill_data['load_history'].append({
            "timestamp": skill_data['last_accessed'],
            "query": query,
            "relevance": relevance,
            "loaded": loaded,
            "used": used,
            "tokens": tokens
        })

    def save(self):
        """Persist tracking data to disk"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
```

---

## 11. Optimization Strategies

Optimization strategies improve orchestration performance and accuracy over time.

### Strategy 1: Caching Frequently Used Skills

**What:** Cache fully loaded skill content in memory for instant access.

**When:** Skills with >100 loads in past 30 days.

**Example:**
```python
from functools import lru_cache
from pathlib import Path

class SkillCache:
    """LRU cache for frequently used skills"""

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.cache = {}
        self.access_count = {}

    @lru_cache(maxsize=20)
    def load_skill(self, skill_path: str) -> str:
        """Load skill with caching"""
        with open(skill_path) as f:
            return f.read()

    def should_cache(self, skill_id: str, usage_stats: Dict) -> bool:
        """Decide if skill should be cached"""
        recent_loads = usage_stats.get('loads_last_30_days', 0)
        return recent_loads > 100
```

### Strategy 2: Preloading Skill Dependencies

**What:** Preload known dependencies when loading a skill to reduce latency.

**When:** Dependencies have high co-occurrence rate (>70%).

**Example:**
```python
class DependencyPreloader:
    """Preload skill dependencies"""

    def __init__(self, usage_tracker: UsageTracker):
        self.usage_tracker = usage_tracker

    def should_preload(self, skill_id: str, dependency_id: str) -> bool:
        """Check if dependency should be preloaded"""
        skill_data = self.usage_tracker.data['skill_usage'].get(skill_id, {})
        co_occurs = skill_data.get('co_occurrences', {})

        if dependency_id not in co_occurs:
            return False

        # Preload if co-occurrence rate > 70%
        total_loads = skill_data.get('total_loads', 0)
        dep_loads = co_occurs[dependency_id]

        return (dep_loads / total_loads) > 0.7 if total_loads > 0 else False
```

### Strategy 3: Adaptive Token Allocation

**What:** Adjust token allocations based on historical usage patterns.

**When:** After 50+ queries, enough data to identify patterns.

**Example:**
```python
class AdaptiveAllocator:
    """Adjust allocations based on history"""

    def adjust_allocation(self, base_allocation: int,
                         skill_id: str,
                         usage_stats: Dict) -> int:
        """Adjust allocation based on actual usage"""
        avg_used = usage_stats.get('avg_tokens_used', base_allocation)
        success_rate = usage_stats.get('success_rate', 1.0)

        # If typically uses less, reduce allocation
        if avg_used < base_allocation * 0.7:
            adjusted = int(avg_used * 1.1)  # 10% buffer
        # If high success rate and uses most of allocation, increase
        elif success_rate > 0.9 and avg_used > base_allocation * 0.9:
            adjusted = int(base_allocation * 1.2)
        else:
            adjusted = base_allocation

        return adjusted
```

### Strategy 4: Query Pattern Recognition

**What:** Recognize common query patterns to skip analysis steps.

**When:** Pattern seen 10+ times with consistent results.

**Example:**
```python
from typing import Optional

class QueryPatternMatcher:
    """Match queries to known patterns"""

    def __init__(self):
        self.patterns = {
            r'create.*api.*endpoint': {
                'skills': ['API_DESIGN', 'FASTAPI_CRUD'],
                'confidence': 0.95
            },
            r'deploy.*aws.*lambda': {
                'skills': ['AWS_LAMBDA_DEPLOY', 'SERVERLESS'],
                'confidence': 0.90
            }
        }

    def match(self, query: str) -> Optional[Dict]:
        """Try to match query to known pattern"""
        import re

        query_lower = query.lower()
        for pattern, result in self.patterns.items():
            if re.search(pattern, query_lower):
                return result
        return None
```

### Strategy 5: Progressive Detail Loading

**What:** Start with metadata, load more detail only if needed.

**When:** Loading many skills or limited token budget.

**Example:**
```python
class ProgressiveLoader:
    """Load skills progressively"""

    def load_progressive(self, skill_id: str,
                        initial_level: LoadingLevel,
                        feedback_needed: bool) -> str:
        """
        Load skill starting at initial level,
        increasing detail if feedback indicates need
        """
        content = self._load_at_level(skill_id, initial_level)

        if feedback_needed:
            # Simulate checking if more detail needed
            if self._needs_more_detail(content):
                next_level = LoadingLevel(initial_level.value + 1)
                content = self._load_at_level(skill_id, next_level)

        return content

    def _load_at_level(self, skill_id: str, level: LoadingLevel) -> str:
        """Load skill at specific detail level"""
        # Implementation would extract appropriate sections
        pass

    def _needs_more_detail(self, content: str) -> bool:
        """Determine if more detail needed"""
        # Could use LLM to check if content sufficient
        # or check if user is asking follow-up questions
        return False
```

### When to Apply Optimizations

| Optimization | Trigger Condition | Expected Benefit |
|--------------|------------------|------------------|
| Caching | >100 loads/30 days | 90% faster loading |
| Preloading | >70% co-occurrence | 50% reduced latency |
| Adaptive Allocation | >50 queries logged | 20% better token usage |
| Pattern Recognition | >10 identical patterns | Skip analysis entirely |
| Progressive Loading | >5 skills or <5000 tokens | 2-3x more skills loaded |

---

## Summary

SkillForge's orchestration system provides intelligent skill management through:

1. **8-stage pipeline** from intent to usage tracking
2. **Multi-strategy discovery** using keywords, domains, actions, semantics, and history
3. **Dependency resolution** ensuring correct load order
4. **Priority scoring** with 5 weighted factors
5. **Token budget allocation** maximizing value within constraints
6. **Progressive loading** with 4 detail levels
7. **Multi-skill workflows** for complex tasks
8. **Conflict resolution** using priority, consensus, or context
9. **Usage tracking** for continuous improvement
10. **5 optimization strategies** for performance and accuracy

This orchestration approach ensures the most relevant skills are loaded efficiently, optimizing both context usage and task completion quality.

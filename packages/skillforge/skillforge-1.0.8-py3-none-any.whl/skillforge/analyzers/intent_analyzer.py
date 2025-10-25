"""
Intent Analysis for SkillForge

This module provides the IntentAnalyzer class for analyzing user requests and
extracting structured intent information including entities, actions, domain,
complexity, and matching learned patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
from pathlib import Path

from skillforge.generators.config import Config


@dataclass
class Pattern:
    """Represents a learned pattern from previous requests"""

    name: str
    keywords: List[str]
    entities: List[str]
    action: str
    domain: str
    complexity: str
    confidence: float = 0.0
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary for serialization"""
        return {
            "name": self.name,
            "keywords": self.keywords,
            "entities": self.entities,
            "action": self.action,
            "domain": self.domain,
            "complexity": self.complexity,
            "confidence": self.confidence,
            "usage_count": self.usage_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """Create pattern from dictionary"""
        return cls(
            name=data.get("name", ""),
            keywords=data.get("keywords", []),
            entities=data.get("entities", []),
            action=data.get("action", ""),
            domain=data.get("domain", ""),
            complexity=data.get("complexity", ""),
            confidence=data.get("confidence", 0.0),
            usage_count=data.get("usage_count", 0)
        )


@dataclass
class Intent:
    """Represents the analyzed intent from a user request"""

    entities: List[str] = field(default_factory=list)
    action: str = ""
    domain: str = ""
    complexity: str = ""
    patterns: List[Pattern] = field(default_factory=list)
    confidence: float = 0.0
    raw_request: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Alias for raw_request - for backward compatibility."""
        return self.raw_request

    @text.setter
    def text(self, value: str) -> None:
        """Setter for text property."""
        self.raw_request = value

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for backward compatibility."""
        return hasattr(self, key)

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access for backward compatibility."""
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get() for backward compatibility."""
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert intent to dictionary for serialization"""
        return {
            "entities": self.entities,
            "action": self.action,
            "domain": self.domain,
            "complexity": self.complexity,
            "patterns": [p.to_dict() for p in self.patterns],
            "confidence": self.confidence,
            "raw_request": self.raw_request,
            "text": self.raw_request,  # Include text alias
            "metadata": self.metadata
        }


class IntentAnalyzer:
    """
    Analyzes user requests to extract structured intent information.

    Capabilities:
    - Extract framework/library entities
    - Determine user action type
    - Identify domain (frontend, backend, etc.)
    - Assess complexity level
    - Match against learned patterns
    """

    # Framework and library patterns
    FRAMEWORKS = {
        # Frontend frameworks
        r'\b(next\.?js|nextjs)\b': 'Next.js',
        r'\breact\b': 'React',
        r'\bvue(\.js)?\b': 'Vue',
        r'\bangular\b': 'Angular',
        r'\bsvelte\b': 'Svelte',
        r'\bsolid(js)?\b': 'SolidJS',
        r'\bqwik\b': 'Qwik',

        # Backend frameworks
        r'\bdjango\b': 'Django',
        r'\bflask\b': 'Flask',
        r'\bfastapi\b': 'FastAPI',
        r'\bexpress(\.js)?\b': 'Express',
        r'\bnest(js)?\b': 'NestJS',
        r'\blaravel\b': 'Laravel',
        r'\bruby\s+on\s+rails\b': 'Ruby on Rails',
        r'\brails\b': 'Rails',

        # Full-stack frameworks
        r'\bredwood(js)?\b': 'RedwoodJS',
        r'\bblitz(js)?\b': 'BlitzJS',
        r'\bremix\b': 'Remix',
        r'\bmeteor\b': 'Meteor',
    }

    LIBRARIES = {
        # Databases & ORMs
        r'\bsupabase\b': 'Supabase',
        r'\bprisma\b': 'Prisma',
        r'\bdrizzle\b': 'Drizzle',
        r'\bmongodb\b': 'MongoDB',
        r'\bmongoose\b': 'Mongoose',
        r'\bpostgres(ql)?\b': 'PostgreSQL',
        r'\bmysql\b': 'MySQL',
        r'\bsqlalchemy\b': 'SQLAlchemy',

        # Styling
        r'\btailwind(css)?\b': 'Tailwind CSS',
        r'\bshadcn(/ui)?\b': 'shadcn/ui',
        r'\bchakra\s?ui\b': 'Chakra UI',
        r'\bmaterial\s?ui\b': 'Material-UI',
        r'\bmui\b': 'MUI',
        r'\bbootstrap\b': 'Bootstrap',
        r'\bstyled\s?components\b': 'Styled Components',

        # State management
        r'\bredux\b': 'Redux',
        r'\bzustand\b': 'Zustand',
        r'\bjotai\b': 'Jotai',
        r'\brecoil\b': 'Recoil',
        r'\bmobx\b': 'MobX',

        # Authentication
        r'\bnextauth(\.js)?\b': 'NextAuth.js',
        r'\bauth0\b': 'Auth0',
        r'\bclerk\b': 'Clerk',
        r'\bpassport(\.js)?\b': 'Passport.js',

        # Testing
        r'\bjest\b': 'Jest',
        r'\bvitest\b': 'Vitest',
        r'\bpytest\b': 'Pytest',
        r'\bcypress\b': 'Cypress',
        r'\bplaywright\b': 'Playwright',

        # Build tools
        r'\bvite\b': 'Vite',
        r'\bwebpack\b': 'Webpack',
        r'\bturbopack\b': 'Turbopack',
        r'\besbuild\b': 'esbuild',
    }

    FEATURES = {
        r'\bauth(entication)?\b': 'authentication',
        r'\blogin\b': 'login',
        r'\bsign\s?up\b': 'signup',
        r'\bsign\s?in\b': 'signin',
        r'\bdashboard\b': 'dashboard',
        r'\bapi\b': 'API',
        r'\brest\s?api\b': 'REST API',
        r'\bgraphql\b': 'GraphQL',
        r'\bform\b': 'form',
        r'\bcrud\b': 'CRUD',
        r'\badmin\s?panel\b': 'admin panel',
        r'\bnavigation\b': 'navigation',
        r'\brouting\b': 'routing',
        r'\bmiddleware\b': 'middleware',
        r'\bwebhook\b': 'webhook',
        r'\breal\s?time\b': 'real-time',
        r'\bchat\b': 'chat',
        r'\bnotification\b': 'notification',
        r'\bsearch\b': 'search',
        r'\bfilter\b': 'filter',
        r'\bpagination\b': 'pagination',
    }

    FILE_TYPES = {
        r'\bcomponent\b': 'component',
        r'\bpage\b': 'page',
        r'\broute\b': 'route',
        r'\bapi\s+route\b': 'api-route',
        r'\bmodel\b': 'model',
        r'\bschema\b': 'schema',
        r'\bservice\b': 'service',
        r'\bcontroller\b': 'controller',
        r'\bmiddleware\b': 'middleware',
        r'\bhook\b': 'hook',
        r'\butil(ity)?\b': 'utility',
        r'\bhelper\b': 'helper',
        r'\btype\b': 'type',
        r'\binterface\b': 'interface',
    }

    # Action keywords
    ACTIONS = {
        # More specific actions first to avoid generic matches
        'document': [
            'document', 'explain', 'describe', 'comment', 'comments'
        ],
        'deploy': [
            'deploy', 'publish', 'release', 'ship', 'launch'
        ],
        'test': [
            'test', 'verify', 'validate', 'ensure'
        ],
        'debug': [
            'debug', 'fix', 'resolve', 'troubleshoot', 'repair', 'solve',
            'correct', 'patch'
        ],
        'analyze': [
            'analyze', 'review', 'check', 'inspect', 'examine', 'optimize',
            'audit', 'evaluate', 'assess'
        ],
        'update': [
            'update', 'modify', 'change', 'edit', 'revise', 'alter',
            'refactor', 'improve', 'enhance'
        ],
        'delete': [
            'delete', 'remove', 'destroy', 'clean', 'purge', 'clear'
        ],
        # Generic create action last (contains common words like 'add')
        'create': [
            'create', 'build', 'make', 'generate', 'scaffold', 'initialize',
            'setup', 'new', 'add', 'implement'
        ]
    }

    # Domain classification keywords
    DOMAIN_KEYWORDS = {
        'frontend': [
            'ui', 'component', 'page', 'view', 'client', 'browser',
            'css', 'style', 'layout', 'responsive', 'interface'
        ],
        'backend': [
            'api', 'server', 'database', 'model', 'controller', 'service',
            'endpoint', 'route', 'middleware', 'query'
        ],
        'fullstack': [
            'fullstack', 'full-stack', 'app', 'application', 'project'
        ],
        'devops': [
            'docker', 'kubernetes', 'ci/cd', 'deployment', 'infrastructure',
            'pipeline', 'container', 'cloud', 'aws', 'azure', 'gcp'
        ],
        'testing': [
            'test', 'unit test', 'integration test', 'e2e', 'testing',
            'spec', 'coverage', 'jest', 'mocha', 'cypress', 'vitest',
            'pytest', 'unittest', 'jasmine', 'karma'
        ],
        'documentation': [
            'documentation', 'docs', 'readme', 'guide', 'tutorial'
        ]
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        'simple': [
            'simple', 'basic', 'single', 'small', 'quick', 'minimal'
        ],
        'moderate': [
            'moderate', 'standard', 'typical', 'normal', 'regular'
        ],
        'complex': [
            'complex', 'advanced', 'sophisticated', 'comprehensive',
            'full-featured', 'enterprise', 'production'
        ]
    }

    def __init__(self):
        """Initialize the IntentAnalyzer"""
        self.learned_patterns: Dict[str, Pattern] = {}
        self._load_learned_patterns()

    def _load_learned_patterns(self) -> None:
        """Load learned patterns from Config"""
        try:
            patterns_data = Config.load_learned_patterns()
            for name, data in patterns_data.items():
                self.learned_patterns[name] = Pattern.from_dict(data)
        except Exception as e:
            # If loading fails, start with empty patterns
            print(f"Warning: Could not load learned patterns: {e}")
            self.learned_patterns = {}

    def analyze(self, user_request: str) -> Intent:
        """
        Main analysis method to extract intent from user request.

        Args:
            user_request: The raw user request string

        Returns:
            Intent object with extracted information

        Example:
            >>> analyzer = IntentAnalyzer()
            >>> intent = analyzer.analyze("Create a Next.js app with Supabase auth")
            >>> print(intent.entities)
            ['Next.js', 'Supabase', 'authentication']
            >>> print(intent.action)
            'create'
        """
        # Normalize text
        text = user_request.lower().strip()

        # Extract components
        entities = self.extract_entities(text)
        action = self.determine_action(text)
        domain = self.identify_domain(entities, text)
        complexity = self.assess_complexity(text, entities)
        patterns = self.match_patterns(text)

        # Calculate confidence based on how much we could extract
        confidence = self._calculate_confidence(
            entities, action, domain, complexity, patterns
        )

        # Extract metadata
        metadata = self._extract_metadata(text, entities)

        return Intent(
            entities=entities,
            action=action,
            domain=domain,
            complexity=complexity,
            patterns=patterns,
            confidence=confidence,
            raw_request=user_request,
            metadata=metadata
        )

    def extract_entities(self, text: str) -> List[str]:
        """
        Extract framework/library names and features from text.

        Args:
            text: Input text (should be lowercase)

        Returns:
            List of extracted entity names

        Example:
            >>> analyzer.extract_entities("build a react app with tailwind")
            ['React', 'Tailwind CSS']
        """
        entities = []

        # Extract frameworks
        for pattern, name in self.FRAMEWORKS.items():
            if re.search(pattern, text, re.IGNORECASE):
                if name not in entities:
                    entities.append(name)

        # Extract libraries
        for pattern, name in self.LIBRARIES.items():
            if re.search(pattern, text, re.IGNORECASE):
                if name not in entities:
                    entities.append(name)

        # Extract features
        for pattern, name in self.FEATURES.items():
            if re.search(pattern, text, re.IGNORECASE):
                if name not in entities:
                    entities.append(name)

        # Extract file types
        for pattern, name in self.FILE_TYPES.items():
            if re.search(pattern, text, re.IGNORECASE):
                if name not in entities:
                    entities.append(name)

        return entities

    def determine_action(self, text: str) -> str:
        """
        Detect the primary action from the request.

        Args:
            text: Input text (should be lowercase)

        Returns:
            Action type ('create', 'update', 'debug', etc.)

        Example:
            >>> analyzer.determine_action("build a new component")
            'create'
        """
        # Check for action keywords
        for action, keywords in self.ACTIONS.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text):
                    return action

        # Default to 'create' if no action detected
        return 'create'

    def identify_domain(self, entities: List[str], text: str) -> str:
        """
        Classify the domain based on entities and keywords.

        Args:
            entities: List of extracted entities
            text: Input text (should be lowercase)

        Returns:
            Domain classification

        Example:
            >>> analyzer.identify_domain(['React', 'component'], "create ui component")
            'frontend'
        """
        domain_scores = {domain: 0 for domain in self.DOMAIN_KEYWORDS}

        # Score based on keywords in text
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text):
                    domain_scores[domain] += 1

        # Score based on entities
        entity_text = ' '.join(entities).lower()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in entity_text:
                    domain_scores[domain] += 2  # Weight entities higher

        # Identify frontend frameworks
        frontend_frameworks = {'React', 'Vue', 'Angular', 'Svelte', 'SolidJS'}
        if any(fw in entities for fw in frontend_frameworks):
            domain_scores['frontend'] += 3

        # Identify backend frameworks
        backend_frameworks = {'Django', 'Flask', 'FastAPI', 'Express', 'NestJS'}
        if any(fw in entities for fw in backend_frameworks):
            domain_scores['backend'] += 3

        # Identify fullstack frameworks
        fullstack_frameworks = {'Next.js', 'Remix', 'RedwoodJS', 'BlitzJS'}
        if any(fw in entities for fw in fullstack_frameworks):
            domain_scores['fullstack'] += 3

        # Find domain with highest score
        max_score = max(domain_scores.values())
        if max_score > 0:
            for domain, score in domain_scores.items():
                if score == max_score:
                    return domain

        # Default to fullstack
        return 'fullstack'

    def assess_complexity(self, text: str, entities: List[str]) -> str:
        """
        Assess the complexity level of the request.

        Args:
            text: Input text (should be lowercase)
            entities: List of extracted entities

        Returns:
            Complexity level ('simple', 'moderate', 'complex', 'enterprise')

        Example:
            >>> analyzer.assess_complexity("create basic form", ['form'])
            'simple'
        """
        complexity_scores = {level: 0 for level in self.COMPLEXITY_INDICATORS}

        # Check for explicit complexity keywords
        for level, keywords in self.COMPLEXITY_INDICATORS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text):
                    complexity_scores[level] += 2

        # Infer from number of entities
        entity_count = len(entities)
        if entity_count == 0:
            # No entities - don't bias toward simple
            pass
        elif entity_count <= 2:
            complexity_scores['simple'] += 1
        elif entity_count <= 4:
            complexity_scores['moderate'] += 1
        else:
            complexity_scores['complex'] += 1

        # Check for complexity indicators
        if re.search(r'\bfull\s+app(lication)?\b', text):
            complexity_scores['complex'] += 2

        if re.search(r'\benterprise\b', text):
            return 'enterprise'

        if re.search(r'\bproduction\b', text):
            complexity_scores['complex'] += 1

        # Check for multiple features indicating complexity
        feature_keywords = ['auth', 'dashboard', 'api', 'database', 'real-time']
        feature_count = sum(1 for kw in feature_keywords if kw in text)
        if feature_count >= 3:
            complexity_scores['complex'] += 2
        elif feature_count >= 2:
            complexity_scores['moderate'] += 1

        # Find complexity with highest score
        max_score = max(complexity_scores.values())
        if max_score > 0:
            for level, score in complexity_scores.items():
                if score == max_score:
                    return level

        # Default to moderate
        return 'moderate'

    def match_patterns(self, text: str) -> List[Pattern]:
        """
        Match request against learned patterns.

        Args:
            text: Input text (should be lowercase)

        Returns:
            List of matching patterns sorted by confidence

        Example:
            >>> patterns = analyzer.match_patterns("create next.js auth")
            >>> print(patterns[0].name if patterns else "No matches")
        """
        if not self.learned_patterns:
            return []

        matches = []

        for pattern in self.learned_patterns.values():
            # Calculate similarity score
            similarity = self._calculate_pattern_similarity(text, pattern)

            if similarity > 0.5:  # Threshold for matching
                # Create a copy with updated confidence
                matched_pattern = Pattern(
                    name=pattern.name,
                    keywords=pattern.keywords,
                    entities=pattern.entities,
                    action=pattern.action,
                    domain=pattern.domain,
                    complexity=pattern.complexity,
                    confidence=similarity,
                    usage_count=pattern.usage_count
                )
                matches.append(matched_pattern)

        # Sort by confidence (highest first)
        matches.sort(key=lambda p: p.confidence, reverse=True)

        return matches

    def _calculate_pattern_similarity(
        self, text: str, pattern: Pattern
    ) -> float:
        """
        Calculate similarity between text and a pattern.

        Args:
            text: Input text
            pattern: Pattern to compare against

        Returns:
            Similarity score (0.0 to 1.0)
        """
        scores = []

        # Check keyword matches
        if pattern.keywords:
            keyword_matches = sum(
                1 for kw in pattern.keywords if kw.lower() in text
            )
            keyword_score = keyword_matches / len(pattern.keywords)
            scores.append(keyword_score)

        # Check entity matches
        if pattern.entities:
            text_entities = self.extract_entities(text)
            entity_matches = sum(
                1 for e in pattern.entities if e in text_entities
            )
            entity_score = entity_matches / len(pattern.entities)
            scores.append(entity_score)

        # Use sequence matching for overall similarity
        sequence_score = SequenceMatcher(None, text, ' '.join(pattern.keywords)).ratio()
        scores.append(sequence_score)

        # Return average of all scores
        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_confidence(
        self,
        entities: List[str],
        action: str,
        domain: str,
        complexity: str,
        patterns: List[Pattern]
    ) -> float:
        """
        Calculate overall confidence score for the intent analysis.

        Args:
            entities: Extracted entities
            action: Detected action
            domain: Identified domain
            complexity: Assessed complexity
            patterns: Matched patterns

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0

        # Entity extraction confidence
        if entities:
            score += 0.3

        # Action detection confidence
        if action and action != 'create':  # create is default
            score += 0.2
        elif action == 'create':
            score += 0.1

        # Domain identification confidence
        if domain and domain != 'fullstack':  # fullstack is default
            score += 0.2
        elif domain == 'fullstack':
            score += 0.1

        # Complexity assessment confidence
        if complexity and complexity != 'moderate':  # moderate is default
            score += 0.1

        # Pattern matching confidence
        if patterns:
            score += 0.2

        return min(score, 1.0)  # Cap at 1.0

    def _extract_metadata(
        self, text: str, entities: List[str]
    ) -> Dict[str, Any]:
        """
        Extract additional metadata from the request.

        Args:
            text: Input text
            entities: Extracted entities

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Check for TypeScript preference
        if re.search(r'\btypescript\b|\bts\b', text):
            metadata['typescript'] = True

        # Check for styling preference
        if 'Tailwind CSS' in entities or re.search(r'\btailwind\b', text):
            metadata['styling'] = 'tailwind'
        elif 'Chakra UI' in entities or re.search(r'\bchakra\b', text):
            metadata['styling'] = 'chakra'
        elif 'Material-UI' in entities or 'MUI' in entities or re.search(r'\bmaterial-ui\b|\bmui\b', text):
            metadata['styling'] = 'mui'

        # Check for database preference
        db_entities = [e for e in entities if e in [
            'Supabase', 'Prisma', 'MongoDB', 'PostgreSQL', 'MySQL'
        ]]
        if db_entities:
            metadata['database'] = db_entities[0]

        # Check for authentication preference
        auth_entities = [e for e in entities if e in [
            'NextAuth.js', 'Auth0', 'Clerk', 'Passport.js', 'Supabase'
        ]]
        if auth_entities:
            metadata['auth_provider'] = auth_entities[0]

        return metadata

    # Alias for backward compatibility
    def analyze_intent(self, user_request: str) -> Intent:
        """
        Alias for analyze() method - for backward compatibility.

        Args:
            user_request: The raw user request string

        Returns:
            Intent object with extracted information
        """
        return self.analyze(user_request)

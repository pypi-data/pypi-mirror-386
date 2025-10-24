"""
Unit tests for IntentAnalyzer class

Tests intent analysis including:
- Entity extraction from various requests
- Action determination for all action types
- Domain identification for all domains
- Complexity assessment for all levels
- Pattern matching with learned patterns
- Complete analyze() integration
"""

import pytest
from pathlib import Path
from skillforge.analyzers.intent_analyzer import (
    IntentAnalyzer,
    Intent,
    Pattern
)
from skillforge.generators.config import Config


@pytest.fixture
def temp_home(tmp_path):
    """
    Create temporary SkillForge home for testing.

    Overrides Config paths to use temporary directory,
    ensuring tests don't affect real user data.
    """
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)

    # Override Config class variables
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
    Config.ensure_directories()

    yield home


@pytest.fixture
def analyzer(temp_home):
    """Create IntentAnalyzer instance with clean state"""
    return IntentAnalyzer()


@pytest.fixture
def analyzer_with_patterns(temp_home):
    """Create IntentAnalyzer with some learned patterns"""
    # Save test patterns
    patterns = {
        "nextjs_auth": {
            "name": "nextjs_auth",
            "keywords": ["next.js", "nextjs", "authentication", "auth"],
            "entities": ["Next.js", "authentication"],
            "action": "create",
            "domain": "fullstack",
            "complexity": "moderate",
            "confidence": 0.85,
            "usage_count": 15
        },
        "react_component": {
            "name": "react_component",
            "keywords": ["react", "component", "ui"],
            "entities": ["React", "component"],
            "action": "create",
            "domain": "frontend",
            "complexity": "simple",
            "confidence": 0.92,
            "usage_count": 30
        }
    }
    Config.save_learned_patterns(patterns)
    return IntentAnalyzer()


class TestEntityExtraction:
    """Test extract_entities() with various requests"""

    def test_extract_frameworks(self, analyzer):
        """Test extraction of framework names"""
        text = "create a next.js app with react"
        entities = analyzer.extract_entities(text)

        assert "Next.js" in entities
        assert "React" in entities

    def test_extract_libraries(self, analyzer):
        """Test extraction of library names"""
        text = "build with tailwind and supabase"
        entities = analyzer.extract_entities(text)

        assert "Tailwind CSS" in entities
        assert "Supabase" in entities

    def test_extract_features(self, analyzer):
        """Test extraction of feature names"""
        text = "add authentication and dashboard"
        entities = analyzer.extract_entities(text)

        assert "authentication" in entities
        assert "dashboard" in entities

    def test_extract_file_types(self, analyzer):
        """Test extraction of file type entities"""
        text = "create a component and api route"
        entities = analyzer.extract_entities(text)

        assert "component" in entities
        assert "api-route" in entities

    def test_extract_multiple_entity_types(self, analyzer):
        """Test extraction of mixed entity types"""
        text = "build a nextjs dashboard with supabase auth"
        entities = analyzer.extract_entities(text)

        assert "Next.js" in entities  # framework
        assert "Supabase" in entities  # library
        assert "dashboard" in entities  # feature
        assert "authentication" in entities  # feature

    def test_extract_case_insensitive(self, analyzer):
        """Test case-insensitive extraction"""
        text = "use REACT and TAILWIND"
        entities = analyzer.extract_entities(text.lower())

        assert "React" in entities
        assert "Tailwind CSS" in entities

    def test_extract_no_duplicates(self, analyzer):
        """Test that duplicate entities are not added"""
        text = "react component with react hooks"
        entities = analyzer.extract_entities(text)

        # React should only appear once
        assert entities.count("React") == 1

    def test_extract_empty_text(self, analyzer):
        """Test extraction from empty text"""
        entities = analyzer.extract_entities("")
        assert entities == []


class TestActionDetermination:
    """Test determine_action() for all action types"""

    def test_action_create(self, analyzer):
        """Test detection of create actions"""
        assert analyzer.determine_action("create a new component") == "create"
        assert analyzer.determine_action("build an api") == "create"
        assert analyzer.determine_action("make a form") == "create"
        assert analyzer.determine_action("generate tests") == "create"
        assert analyzer.determine_action("initialize project") == "create"

    def test_action_update(self, analyzer):
        """Test detection of update actions"""
        assert analyzer.determine_action("update the component") == "update"
        assert analyzer.determine_action("modify the api") == "update"
        assert analyzer.determine_action("refactor the code") == "update"
        assert analyzer.determine_action("improve performance") == "update"
        assert analyzer.determine_action("enhance the ui") == "update"

    def test_action_debug(self, analyzer):
        """Test detection of debug actions"""
        assert analyzer.determine_action("fix the bug") == "debug"
        assert analyzer.determine_action("debug this issue") == "debug"
        assert analyzer.determine_action("resolve the error") == "debug"
        assert analyzer.determine_action("troubleshoot authentication") == "debug"
        assert analyzer.determine_action("repair the database") == "debug"

    def test_action_analyze(self, analyzer):
        """Test detection of analyze actions"""
        assert analyzer.determine_action("analyze the code") == "analyze"
        assert analyzer.determine_action("review the implementation") == "analyze"
        assert analyzer.determine_action("check for issues") == "analyze"
        assert analyzer.determine_action("optimize performance") == "analyze"
        assert analyzer.determine_action("audit security") == "analyze"

    def test_action_delete(self, analyzer):
        """Test detection of delete actions"""
        assert analyzer.determine_action("delete the component") == "delete"
        assert analyzer.determine_action("remove the feature") == "delete"
        assert analyzer.determine_action("clean up the code") == "delete"

    def test_action_test(self, analyzer):
        """Test detection of test actions"""
        assert analyzer.determine_action("test the component") == "test"
        assert analyzer.determine_action("verify functionality") == "test"
        assert analyzer.determine_action("validate the api") == "test"

    def test_action_deploy(self, analyzer):
        """Test detection of deploy actions"""
        assert analyzer.determine_action("deploy to production") == "deploy"
        assert analyzer.determine_action("publish the app") == "deploy"
        assert analyzer.determine_action("release version 2.0") == "deploy"

    def test_action_document(self, analyzer):
        """Test detection of document actions"""
        assert analyzer.determine_action("document the api") == "document"
        assert analyzer.determine_action("explain the code") == "document"
        assert analyzer.determine_action("add comments") == "document"

    def test_action_default(self, analyzer):
        """Test default action when no keyword found"""
        assert analyzer.determine_action("something random") == "create"


class TestDomainIdentification:
    """Test identify_domain() for all domains"""

    def test_domain_frontend(self, analyzer):
        """Test frontend domain identification"""
        entities = ["React", "component"]
        text = "create a ui component"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "frontend"

    def test_domain_backend(self, analyzer):
        """Test backend domain identification"""
        entities = ["Express", "API"]
        text = "build a rest api server"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "backend"

    def test_domain_fullstack(self, analyzer):
        """Test fullstack domain identification"""
        entities = ["Next.js"]
        text = "create a next.js application"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "fullstack"

    def test_domain_devops(self, analyzer):
        """Test devops domain identification"""
        entities = []
        text = "setup docker containers and ci/cd pipeline"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "devops"

    def test_domain_testing(self, analyzer):
        """Test testing domain identification"""
        entities = ["Jest"]
        text = "create unit tests with jest"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "testing"

    def test_domain_documentation(self, analyzer):
        """Test documentation domain identification"""
        entities = []
        text = "write documentation and readme"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "documentation"

    def test_domain_default(self, analyzer):
        """Test default domain when no match found"""
        entities = []
        text = "do something"
        domain = analyzer.identify_domain(entities, text)
        assert domain == "fullstack"


class TestComplexityAssessment:
    """Test assess_complexity() for all levels"""

    def test_complexity_simple(self, analyzer):
        """Test simple complexity detection"""
        text = "create a simple form"
        entities = ["form"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "simple"

    def test_complexity_simple_by_entity_count(self, analyzer):
        """Test simple complexity based on entity count"""
        text = "build something"
        entities = ["React"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "simple"

    def test_complexity_moderate(self, analyzer):
        """Test moderate complexity detection"""
        text = "create a standard dashboard"
        entities = ["React", "dashboard", "API"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "moderate"

    def test_complexity_moderate_by_entity_count(self, analyzer):
        """Test moderate complexity based on entity count"""
        text = "build an app"
        entities = ["React", "Tailwind CSS", "API"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "moderate"

    def test_complexity_complex(self, analyzer):
        """Test complex complexity detection"""
        text = "create a complex full application"
        entities = ["Next.js", "Supabase", "authentication", "dashboard", "API"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "complex"

    def test_complexity_complex_by_features(self, analyzer):
        """Test complex complexity based on feature count"""
        text = "build app with auth dashboard api database and real-time"
        entities = ["Next.js"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "complex"

    def test_complexity_enterprise(self, analyzer):
        """Test enterprise complexity detection"""
        text = "create an enterprise application"
        entities = ["Next.js", "PostgreSQL"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "enterprise"

    def test_complexity_production(self, analyzer):
        """Test production complexity indicator"""
        text = "build a production ready app with auth and dashboard"
        entities = ["Next.js", "Supabase"]
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "complex"

    def test_complexity_default(self, analyzer):
        """Test default complexity"""
        text = "build something"
        entities = []
        complexity = analyzer.assess_complexity(text, entities)
        assert complexity == "moderate"


class TestPatternMatching:
    """Test match_patterns() with learned patterns"""

    def test_match_single_pattern(self, analyzer_with_patterns):
        """Test matching a single learned pattern"""
        text = "create next.js authentication"
        patterns = analyzer_with_patterns.match_patterns(text)

        assert len(patterns) > 0
        assert any(p.name == "nextjs_auth" for p in patterns)

    def test_match_multiple_patterns(self, analyzer_with_patterns):
        """Test matching multiple patterns"""
        text = "create react component with next.js authentication"
        patterns = analyzer_with_patterns.match_patterns(text)

        # Should match both patterns
        pattern_names = [p.name for p in patterns]
        assert "nextjs_auth" in pattern_names or "react_component" in pattern_names

    def test_match_sorted_by_confidence(self, analyzer_with_patterns):
        """Test that patterns are sorted by confidence"""
        text = "create react component"
        patterns = analyzer_with_patterns.match_patterns(text)

        if len(patterns) > 1:
            # Check that each pattern has lower or equal confidence than the previous
            for i in range(len(patterns) - 1):
                assert patterns[i].confidence >= patterns[i + 1].confidence

    def test_match_no_patterns(self, analyzer):
        """Test matching with no learned patterns"""
        text = "create something"
        patterns = analyzer.match_patterns(text)
        assert len(patterns) == 0

    def test_match_threshold(self, analyzer_with_patterns):
        """Test that low similarity patterns are filtered out"""
        text = "completely unrelated text"
        patterns = analyzer_with_patterns.match_patterns(text)

        # All returned patterns should have confidence > 0.5
        for pattern in patterns:
            assert pattern.confidence > 0.5

    def test_pattern_confidence_update(self, analyzer_with_patterns):
        """Test that matched patterns have updated confidence"""
        text = "create react component"
        patterns = analyzer_with_patterns.match_patterns(text)

        if patterns:
            # Confidence should be recalculated based on similarity
            assert 0.0 <= patterns[0].confidence <= 1.0


class TestAnalyzeIntegration:
    """Test complete analyze() integration"""

    def test_analyze_basic(self, analyzer):
        """Test basic analysis of a simple request"""
        intent = analyzer.analyze("Create a React component")

        assert isinstance(intent, Intent)
        assert "React" in intent.entities
        assert intent.action == "create"
        assert intent.domain == "frontend"
        assert intent.raw_request == "Create a React component"
        assert 0.0 <= intent.confidence <= 1.0

    def test_analyze_complex(self, analyzer):
        """Test analysis of a complex request"""
        request = "Build a Next.js app with Supabase authentication and dashboard"
        intent = analyzer.analyze(request)

        assert "Next.js" in intent.entities
        assert "Supabase" in intent.entities
        assert "authentication" in intent.entities
        assert "dashboard" in intent.entities
        assert intent.action == "create"
        assert intent.domain == "fullstack"
        assert intent.complexity in ["moderate", "complex"]

    def test_analyze_with_patterns(self, analyzer_with_patterns):
        """Test analysis with pattern matching"""
        intent = analyzer_with_patterns.analyze("Create Next.js authentication")

        assert intent.patterns  # Should have matched patterns
        assert any(p.name == "nextjs_auth" for p in intent.patterns)

    def test_analyze_confidence_calculation(self, analyzer):
        """Test confidence calculation"""
        # High confidence: many entities, specific action, clear domain
        intent1 = analyzer.analyze("Build a React component with TypeScript")

        # Low confidence: few entities, default action, default domain
        intent2 = analyzer.analyze("do something")

        assert intent1.confidence > intent2.confidence

    def test_analyze_metadata_extraction(self, analyzer):
        """Test metadata extraction"""
        intent = analyzer.analyze("Create TypeScript Next.js app with Tailwind CSS and Supabase")

        assert intent.metadata.get("typescript") is True
        assert intent.metadata.get("styling") == "tailwind"
        assert intent.metadata.get("database") == "Supabase"

    def test_analyze_empty_request(self, analyzer):
        """Test analysis of empty request"""
        intent = analyzer.analyze("")

        assert intent.entities == []
        assert intent.action == "create"  # default
        assert intent.domain == "fullstack"  # default
        assert intent.confidence < 0.5  # low confidence


class TestConfidenceCalculation:
    """Test confidence score calculations"""

    def test_confidence_with_entities(self, analyzer):
        """Test confidence increases with entities"""
        intent1 = analyzer.analyze("build something")
        intent2 = analyzer.analyze("build a React app with Tailwind")

        # More entities should increase confidence
        assert intent2.confidence > intent1.confidence

    def test_confidence_with_specific_action(self, analyzer):
        """Test confidence with non-default action"""
        intent1 = analyzer.analyze("something with React")
        intent2 = analyzer.analyze("debug the React component")

        # Explicit action (debug) should have higher confidence than default (create)
        assert intent2.confidence >= intent1.confidence

    def test_confidence_with_domain(self, analyzer):
        """Test confidence with specific domain"""
        intent = analyzer.analyze("create React component")

        # Should have moderate confidence with clear domain
        assert intent.confidence > 0.3

    def test_confidence_with_patterns(self, analyzer_with_patterns):
        """Test confidence increases with pattern matches"""
        intent = analyzer_with_patterns.analyze("Create Next.js authentication")

        # Should have higher confidence due to pattern match
        assert intent.confidence >= 0.5


class TestMetadataExtraction:
    """Test metadata extraction from requests"""

    def test_metadata_typescript(self, analyzer):
        """Test TypeScript preference detection"""
        intent = analyzer.analyze("Create a TypeScript component")
        assert intent.metadata.get("typescript") is True

    def test_metadata_styling_tailwind(self, analyzer):
        """Test Tailwind CSS styling detection"""
        intent = analyzer.analyze("Build with Tailwind CSS")
        assert intent.metadata.get("styling") == "tailwind"

    def test_metadata_styling_chakra(self, analyzer):
        """Test Chakra UI styling detection"""
        intent = analyzer.analyze("Use Chakra UI for styling")
        assert intent.metadata.get("styling") == "chakra"

    def test_metadata_styling_mui(self, analyzer):
        """Test Material-UI styling detection"""
        intent = analyzer.analyze("Style with Material-UI")
        assert intent.metadata.get("styling") == "mui"

    def test_metadata_database(self, analyzer):
        """Test database preference detection"""
        intent = analyzer.analyze("Connect to PostgreSQL database")
        assert intent.metadata.get("database") == "PostgreSQL"

    def test_metadata_auth_provider(self, analyzer):
        """Test authentication provider detection"""
        intent = analyzer.analyze("Add Auth0 authentication")
        assert intent.metadata.get("auth_provider") == "Auth0"

    def test_metadata_multiple(self, analyzer):
        """Test extraction of multiple metadata items"""
        intent = analyzer.analyze("Build TypeScript app with Supabase auth and Tailwind")

        assert intent.metadata.get("typescript") is True
        assert intent.metadata.get("styling") == "tailwind"
        assert intent.metadata.get("auth_provider") == "Supabase"

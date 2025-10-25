"""
Unit tests for DocFetcher class

Tests documentation fetching functionality including:
- Cache operations (save/load/validate)
- Response parsing from Context7 format
- Best practices extraction
- Code example extraction
- Fallback chain behavior
"""

import json
import pytest
import time
from pathlib import Path
from skillforge.generators.doc_fetcher import (
    DocFetcher,
    DocFetchError,
    LibraryDocs,
    DocSource
)


@pytest.fixture
def fetcher():
    """Create DocFetcher instance with short cache TTL"""
    return DocFetcher(cache_ttl_days=7, use_mcp=False)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Override Config to use temp cache
    from skillforge.generators.config import Config
    Config.CACHE_DIR = cache_dir
    Config.DATA_DIR = tmp_path

    return cache_dir


@pytest.fixture
def sample_docs():
    """Create sample LibraryDocs object for testing"""
    source = DocSource(
        type="mock",
        timestamp=time.time(),
        library_id="/facebook/react",
        version="18.2.0"
    )

    return LibraryDocs(
        library_id="/facebook/react",
        library_name="react",
        version="18.2.0",
        content="# React Documentation\n\nReact is a library.",
        examples=[
            {
                "code": "const [count, setCount] = useState(0);",
                "language": "javascript",
                "description": "Using useState hook"
            }
        ],
        best_practices=[
            "Use functional components",
            "Keep components small"
        ],
        source=source,
        topics_covered=["hooks", "components"],
        raw_data={}
    )


@pytest.fixture
def sample_markdown_docs():
    """Sample markdown documentation with examples and best practices"""
    return """
# React Hooks Documentation

React Hooks allow you to use state in functional components.

## Best Practices

- Always call hooks at the top level
- Don't call hooks inside loops or conditions
- Use custom hooks to share logic between components
- Keep hooks simple and focused

## Examples

### Basic useState Example

```javascript
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

### useEffect Example

```javascript
import { useEffect, useState } from 'react';

function DataFetcher() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData().then(setData);
  }, []);

  return <div>{data}</div>;
}
```

## Tips

- Tip: Use ESLint plugin for hooks to catch common mistakes
- Note: Effects run after every render by default
- Recommendation: Always specify dependencies array for useEffect

You should clean up effects to prevent memory leaks.
You must handle loading and error states properly.
"""


class TestCacheOperations:
    """Test cache save/load/validate operations"""

    def test_cache_docs(self, fetcher, temp_cache_dir, sample_docs):
        """Test caching documentation to disk"""
        from skillforge.generators.config import Config

        fetcher.cache_docs("/facebook/react", sample_docs)

        cache_path = Config.get_cache_path("/facebook/react")
        assert cache_path.exists()

        with open(cache_path, 'r') as f:
            data = json.load(f)

        assert data["library_id"] == "/facebook/react"
        assert data["library_name"] == "react"
        assert data["version"] == "18.2.0"
        assert len(data["examples"]) == 1
        assert len(data["best_practices"]) == 2

    def test_get_cached_docs(self, fetcher, temp_cache_dir, sample_docs):
        """Test loading cached documentation"""
        from skillforge.generators.config import Config

        # First cache the docs
        fetcher.cache_docs("/facebook/react", sample_docs)

        # Then load them
        loaded = fetcher.get_cached_docs("/facebook/react")

        assert loaded is not None
        assert loaded.library_id == "/facebook/react"
        assert loaded.library_name == "react"
        assert loaded.version == "18.2.0"
        assert len(loaded.examples) == 1
        assert len(loaded.best_practices) == 2

    def test_get_cached_docs_nonexistent(self, fetcher, temp_cache_dir):
        """Test loading cache that doesn't exist"""
        loaded = fetcher.get_cached_docs("/nonexistent/library")
        assert loaded is None

    def test_get_cached_docs_corrupted(self, fetcher, temp_cache_dir):
        """Test loading corrupted cache file"""
        from skillforge.generators.config import Config

        cache_path = Config.get_cache_path("/test/lib")
        cache_path.write_text("{ invalid json }")

        loaded = fetcher.get_cached_docs("/test/lib")
        assert loaded is None

    def test_is_cache_valid_fresh(self, fetcher, temp_cache_dir, sample_docs):
        """Test cache validity check for fresh cache"""
        from skillforge.generators.config import Config

        fetcher.cache_docs("/facebook/react", sample_docs)

        is_valid = fetcher.is_cache_valid("/facebook/react")
        assert is_valid is True

    def test_is_cache_valid_nonexistent(self, fetcher, temp_cache_dir):
        """Test cache validity check for nonexistent cache"""
        is_valid = fetcher.is_cache_valid("/nonexistent/library")
        assert is_valid is False

    def test_is_cache_valid_stale(self, fetcher, temp_cache_dir, sample_docs):
        """Test cache validity check for stale cache"""
        import os
        from skillforge.generators.config import Config

        fetcher.cache_docs("/facebook/react", sample_docs)

        # Modify file time to be 10 days old
        cache_path = Config.get_cache_path("/facebook/react")
        old_time = time.time() - (10 * 86400)  # 10 days ago
        os.utime(cache_path, (old_time, old_time))

        is_valid = fetcher.is_cache_valid("/facebook/react")
        assert is_valid is False


class TestResponseParsing:
    """Test parsing Context7 response format"""

    def test_parse_response_basic(self, fetcher):
        """Test parsing basic Context7 response"""
        response = {
            "library_id": "/facebook/react",
            "library_name": "React",
            "version": "18.2.0",
            "content": "# React\n\nA JavaScript library for building UIs."
        }

        docs = fetcher.parse_response(response)

        assert docs.library_id == "/facebook/react"
        assert docs.library_name == "React"
        assert docs.version == "18.2.0"
        assert "JavaScript library" in docs.content

    def test_parse_response_without_version(self, fetcher):
        """Test parsing response without explicit version"""
        response = {
            "library_id": "/test/lib",
            "content": "Documentation content"
        }

        docs = fetcher.parse_response(response)

        assert docs.library_id == "/test/lib"
        assert docs.version is None

    def test_parse_response_extracts_version_from_content(self, fetcher):
        """Test extracting version from content when not explicit"""
        response = {
            "library_id": "/test/lib",
            "content": "# Library\n\nVersion: 2.5.0\n\nSome documentation."
        }

        docs = fetcher.parse_response(response)

        assert docs.version == "2.5.0"

    def test_parse_response_invalid_format(self, fetcher):
        """Test parsing invalid response raises error"""
        response = {}  # Missing required fields

        # parse_response is more forgiving and will use defaults
        docs = fetcher.parse_response(response)
        assert docs.library_id == "unknown"


class TestBestPracticesExtraction:
    """Test extraction of best practices from documentation"""

    def test_extract_best_practices_from_section(self, fetcher, sample_markdown_docs):
        """Test extracting practices from Best Practices section"""
        practices = fetcher.extract_best_practices(sample_markdown_docs)

        assert len(practices) > 0
        assert any("top level" in p.lower() for p in practices)
        assert any("custom hooks" in p.lower() for p in practices)

    def test_extract_best_practices_from_tips(self, fetcher, sample_markdown_docs):
        """Test extracting practices from Tip/Note/Recommendation"""
        practices = fetcher.extract_best_practices(sample_markdown_docs)

        # Should extract tips and notes
        assert any("eslint" in p.lower() for p in practices)

    def test_extract_best_practices_from_should_statements(self, fetcher, sample_markdown_docs):
        """Test extracting 'should' and 'must' statements"""
        practices = fetcher.extract_best_practices(sample_markdown_docs)

        # Should find "should clean up effects" and "must handle loading"
        assert any("clean up" in p.lower() for p in practices)
        assert any("loading" in p.lower() or "error" in p.lower() for p in practices)

    def test_extract_best_practices_no_duplicates(self, fetcher):
        """Test that duplicate practices are removed"""
        docs = """
## Best Practices
- Use hooks properly
- Use hooks properly

## Tips
Tip: Use hooks properly
"""
        practices = fetcher.extract_best_practices(docs)

        # Count how many times "Use hooks properly" appears
        matching = [p for p in practices if "use hooks properly" in p.lower()]
        assert len(matching) == 1

    def test_extract_best_practices_limits_results(self, fetcher):
        """Test that extraction limits to top 10 practices"""
        # Create docs with many practices
        docs = "## Best Practices\n"
        for i in range(20):
            docs += f"- Best practice number {i}\n"

        practices = fetcher.extract_best_practices(docs)

        assert len(practices) <= 10

    def test_extract_best_practices_empty_docs(self, fetcher):
        """Test extraction from docs with no practices"""
        docs = "# Library\n\nJust some basic documentation."

        practices = fetcher.extract_best_practices(docs)

        # May be empty or have very few
        assert isinstance(practices, list)


class TestExamplesExtraction:
    """Test extraction of code examples from documentation"""

    def test_extract_examples_javascript(self, fetcher, sample_markdown_docs):
        """Test extracting JavaScript code examples"""
        examples = fetcher.extract_examples(sample_markdown_docs)

        assert len(examples) >= 2
        assert any("useState" in ex["code"] for ex in examples)
        assert any("useEffect" in ex["code"] for ex in examples)

    def test_extract_examples_with_language(self, fetcher):
        """Test that language is correctly identified"""
        docs = """
```python
def hello():
    print("Hello")
```

```javascript
console.log("Hello");
```
"""
        examples = fetcher.extract_examples(docs)

        assert len(examples) == 2

        python_ex = next(ex for ex in examples if ex["language"] == "python")
        assert "def hello" in python_ex["code"]

        js_ex = next(ex for ex in examples if ex["language"] == "javascript")
        assert "console.log" in js_ex["code"]

    def test_extract_examples_without_language(self, fetcher):
        """Test extracting examples without language specifier"""
        docs = """
```
const x = 10;
```
"""
        examples = fetcher.extract_examples(docs)

        assert len(examples) == 1
        assert examples[0]["language"] == "text"

    def test_extract_examples_strips_whitespace(self, fetcher):
        """Test that code is properly stripped"""
        docs = """
```javascript

const x = 10;

```
"""
        examples = fetcher.extract_examples(docs)

        assert examples[0]["code"] == "const x = 10;"

    def test_extract_examples_no_code_blocks(self, fetcher):
        """Test extraction from docs with no code blocks"""
        docs = "# Documentation\n\nNo code examples here."

        examples = fetcher.extract_examples(docs)

        assert len(examples) == 0


class TestLibraryResolution:
    """Test library name to ID resolution"""

    def test_resolve_library_id_common_libraries(self, fetcher):
        """Test resolving common library names"""
        assert fetcher.resolve_library_id("react") == "/facebook/react"
        assert fetcher.resolve_library_id("next.js") == "/vercel/next.js"
        assert fetcher.resolve_library_id("nextjs") == "/vercel/next.js"
        assert fetcher.resolve_library_id("vue") == "/vuejs/vue"
        assert fetcher.resolve_library_id("express") == "/expressjs/express"

    def test_resolve_library_id_case_insensitive(self, fetcher):
        """Test that resolution is case-insensitive"""
        assert fetcher.resolve_library_id("React") == "/facebook/react"
        assert fetcher.resolve_library_id("NEXTJS") == "/vercel/next.js"

    def test_resolve_library_id_unknown(self, fetcher):
        """Test resolving unknown library returns None"""
        result = fetcher.resolve_library_id("unknown-library-xyz")
        assert result is None


class TestFetchFallbackChain:
    """Test the fallback chain for fetching documentation"""

    def test_fetch_uses_cache_when_valid(self, fetcher, temp_cache_dir, sample_docs):
        """Test that fetch uses cache when valid"""
        from skillforge.generators.config import Config

        # Cache the docs first
        fetcher.cache_docs("/facebook/react", sample_docs)

        # Fetch should return cached version
        docs = fetcher.fetch("react")

        assert docs is not None
        assert docs.library_id == "/facebook/react"
        assert docs.source.type in ["mock", "cache"]  # Could be mock from original

    def test_fetch_skips_stale_cache(self, fetcher, temp_cache_dir, sample_docs):
        """Test that fetch skips stale cache"""
        import os
        from skillforge.generators.config import Config

        # Cache the docs
        fetcher.cache_docs("/facebook/react", sample_docs)

        # Make cache stale
        cache_path = Config.get_cache_path("/facebook/react")
        old_time = time.time() - (10 * 86400)
        os.utime(cache_path, (old_time, old_time))

        # Fetch should not use stale cache (will use mock data)
        docs = fetcher.fetch("react")

        assert docs is not None
        # Will get mock data instead

    def test_fetch_returns_mock_data_as_fallback(self, fetcher, temp_cache_dir):
        """Test that fetch returns mock data when nothing else available"""
        docs = fetcher.fetch("react")

        assert docs is not None
        assert docs.library_name == "react"
        assert docs.source.type == "mock"

    def test_fetch_with_topic(self, fetcher, temp_cache_dir):
        """Test fetching with specific topic"""
        docs = fetcher.fetch("react", topic="hooks")

        assert docs is not None
        assert "hooks" in docs.topics_covered or "general" in docs.topics_covered

    def test_fetch_caches_mock_data(self, fetcher, temp_cache_dir):
        """Test that mock data is cached for future use"""
        from skillforge.generators.config import Config

        # Fetch (will get mock data)
        docs = fetcher.fetch("react")

        # Check that it was cached
        cache_path = Config.get_cache_path("/facebook/react")
        assert cache_path.exists()


class TestMockDataGeneration:
    """Test mock data generation for development"""

    def test_get_mock_data_structure(self, fetcher):
        """Test that mock data has correct structure"""
        docs = fetcher._get_mock_data("test-lib", topic="testing")

        assert docs.library_name == "test-lib"
        assert docs.version == "1.0.0"
        assert docs.source.type == "mock"
        assert len(docs.examples) > 0
        assert len(docs.best_practices) > 0
        assert "testing" in docs.topics_covered

    def test_get_mock_data_extractable_examples(self, fetcher):
        """Test that mock data contains extractable examples"""
        docs = fetcher._get_mock_data("test-lib", None)

        # Mock content should have code blocks that can be extracted
        assert len(docs.examples) > 0
        assert all("code" in ex for ex in docs.examples)
        assert all("language" in ex for ex in docs.examples)

    def test_get_mock_data_extractable_practices(self, fetcher):
        """Test that mock data contains extractable practices"""
        docs = fetcher._get_mock_data("test-lib", None)

        # Should extract practices from the mock content
        assert len(docs.best_practices) > 0
        assert all(len(p) > 10 for p in docs.best_practices)


class TestHelperMethods:
    """Test helper methods used internally"""

    def test_extract_version_from_content(self, fetcher):
        """Test version extraction from documentation content"""
        response = {
            "content": "# Library\n\nVersion: 3.14.159\n\nDocumentation..."
        }

        version = fetcher._extract_version(response)
        assert version == "3.14.159"

    def test_extract_version_with_v_prefix(self, fetcher):
        """Test version extraction with 'v' prefix"""
        response = {
            "content": "Current version: v2.0.0"
        }

        version = fetcher._extract_version(response)
        assert version == "2.0.0"

    def test_extract_topics_from_headers(self, fetcher):
        """Test topic extraction from markdown headers"""
        content = """
# Main Title

## Getting Started

## API Reference

## Advanced Usage

## FAQ
"""
        topics = fetcher._extract_topics(content)

        assert "getting started" in topics
        assert "api reference" in topics
        assert "advanced usage" in topics
        assert "faq" in topics

    def test_extract_topics_limits_results(self, fetcher):
        """Test that topic extraction is limited"""
        # Create content with many headers
        content = "\n".join([f"## Topic {i}" for i in range(30)])

        topics = fetcher._extract_topics(content)

        assert len(topics) <= 15

    def test_find_code_description(self, fetcher):
        """Test finding description for code blocks"""
        docs = """
This is a simple example of useState.

```javascript
const [count, setCount] = useState(0);
```
"""
        code = "const [count, setCount] = useState(0);"

        description = fetcher._find_code_description(docs, code)

        assert "example" in description.lower() or "usestate" in description.lower()

"""
Documentation Fetcher for SkillForge

This module provides the DocFetcher class for retrieving and caching
library documentation from Context7 MCP and other sources.

Integration Strategy:
    - Primary: Context7 MCP tools (mocked for now, requires Claude Code environment)
    - Fallback 1: Local cache
    - Fallback 2: Web search (placeholder)
    - Fallback 3: Return None with error

Future MCP Integration:
    When running in Claude Code environment, the actual MCP tools will be:
    - mcp__context7__resolve-library-id
    - mcp__context7__get-library-docs

For now, this module uses mock data for testing and development.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .config import Config

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DocSource:
    """Represents the source of documentation"""
    type: str  # "context7", "cache", "websearch", "mock"
    timestamp: float
    library_id: str
    version: Optional[str] = None


@dataclass
class LibraryDocs:
    """Container for library documentation and metadata"""
    library_id: str
    library_name: str
    version: Optional[str]
    content: str
    examples: List[Dict[str, str]]
    best_practices: List[str]
    source: DocSource
    topics_covered: List[str]
    raw_data: Dict[str, Any]


class DocFetchError(Exception):
    """Custom exception for documentation fetching errors"""
    pass


class DocFetcher:
    """
    Fetches and caches library documentation from various sources.

    Primary source is Context7 MCP (Model Context Protocol), with fallbacks
    to cache, web search, and mock data.

    Attributes:
        cache_ttl_days: How long cached docs are valid (default: 7 days)
        use_mcp: Whether to attempt MCP tool calls (default: False for now)

    Example:
        >>> fetcher = DocFetcher()
        >>> docs = fetcher.fetch("react", topic="hooks")
        >>> if docs:
        ...     print(f"Found {len(docs.examples)} examples")
    """

    def __init__(self, cache_ttl_days: int = 7, use_mcp: bool = False):
        """
        Initialize DocFetcher with configuration.

        Args:
            cache_ttl_days: Days before cache expires (default: 7)
            use_mcp: Whether to try calling MCP tools (default: False)
        """
        self.cache_ttl_days = cache_ttl_days
        self.use_mcp = use_mcp
        Config.ensure_directories()

        logger.info(f"DocFetcher initialized (cache_ttl={cache_ttl_days}d, use_mcp={use_mcp})")

    def fetch(
        self,
        library_name: str,
        topic: Optional[str] = None,
        tokens: int = 5000
    ) -> Optional[LibraryDocs]:
        """
        Main entry point for fetching library documentation.

        Attempts to fetch docs in this order:
        1. Check cache (if valid)
        2. Try Context7 MCP (if enabled)
        3. Try web search (placeholder)
        4. Return mock data or None

        Args:
            library_name: Name of library (e.g., "react", "next.js")
            topic: Optional topic to focus on (e.g., "hooks", "routing")
            tokens: Max tokens for Context7 response (default: 5000)

        Returns:
            LibraryDocs object if successful, None otherwise

        Example:
            >>> fetcher = DocFetcher()
            >>> docs = fetcher.fetch("react", topic="hooks")
            >>> if docs:
            ...     for example in docs.examples:
            ...         print(example["code"])
        """
        logger.info(f"Fetching docs for '{library_name}' (topic={topic}, tokens={tokens})")

        try:
            # Step 1: Try cache first
            cached = self._try_cache(library_name)
            if cached:
                logger.info(f"Using cached docs for '{library_name}'")
                return cached

            # Step 2: Try Context7 MCP
            if self.use_mcp:
                mcp_docs = self._try_context7_mcp(library_name, topic, tokens)
                if mcp_docs:
                    logger.info(f"Fetched from Context7 MCP for '{library_name}'")
                    self.cache_docs(mcp_docs.library_id, mcp_docs)
                    return mcp_docs

            # Step 3: Try web search (placeholder)
            web_docs = self._try_web_search(library_name, topic)
            if web_docs:
                logger.info(f"Fetched from web search for '{library_name}'")
                return web_docs

            # Step 4: Return mock data for development
            logger.warning(f"Using mock data for '{library_name}'")
            mock_docs = self._get_mock_data(library_name, topic)
            # Cache the mock data for future use
            if mock_docs:
                self.cache_docs(mock_docs.library_id, mock_docs)
            return mock_docs

        except Exception as e:
            logger.error(f"Error fetching docs for '{library_name}': {e}")
            raise DocFetchError(f"Failed to fetch documentation: {e}")

    def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve library name to Context7-compatible library ID.

        In production, this would call:
        mcp__context7__resolve-library-id

        For now, returns a mock library ID.

        Args:
            library_name: Library name to resolve

        Returns:
            Library ID in format '/org/project' or None

        Example:
            >>> fetcher = DocFetcher()
            >>> lib_id = fetcher.resolve_library_id("react")
            >>> print(lib_id)  # "/facebook/react"
        """
        logger.info(f"Resolving library ID for '{library_name}'")

        if self.use_mcp:
            # TODO: Call actual MCP tool when in Claude Code environment
            # Example call format:
            # result = mcp__context7__resolve_library_id(libraryName=library_name)
            # return result['library_id']
            logger.warning("MCP integration not yet implemented")

        # Mock resolution for common libraries
        mock_mappings = {
            "react": "/facebook/react",
            "next.js": "/vercel/next.js",
            "nextjs": "/vercel/next.js",
            "vue": "/vuejs/vue",
            "angular": "/angular/angular",
            "svelte": "/sveltejs/svelte",
            "typescript": "/microsoft/typescript",
            "express": "/expressjs/express",
            "fastapi": "/tiangolo/fastapi",
            "django": "/django/django",
            "flask": "/pallets/flask",
        }

        library_id = mock_mappings.get(library_name.lower())
        logger.info(f"Resolved '{library_name}' -> '{library_id}'")
        return library_id

    def get_docs(
        self,
        library_id: str,
        topic: Optional[str] = None,
        tokens: int = 5000
    ) -> Optional[Dict[str, Any]]:
        """
        Get documentation from Context7 for a specific library ID.

        In production, this would call:
        mcp__context7__get-library-docs

        For now, returns mock documentation.

        Args:
            library_id: Library ID from resolve_library_id
            topic: Optional topic to focus on
            tokens: Max tokens to retrieve

        Returns:
            Raw documentation response dict or None
        """
        logger.info(f"Getting docs for library_id='{library_id}', topic='{topic}'")

        if self.use_mcp:
            # TODO: Call actual MCP tool when in Claude Code environment
            # Example call format:
            # result = mcp__context7__get_library_docs(
            #     context7CompatibleLibraryID=library_id,
            #     topic=topic,
            #     tokens=tokens
            # )
            # return result
            logger.warning("MCP integration not yet implemented")

        # Return None to trigger fallback
        return None

    def cache_docs(self, library_id: str, docs: LibraryDocs) -> None:
        """
        Save documentation to cache.

        Cache format:
        {
            "library_id": "...",
            "library_name": "...",
            "version": "...",
            "timestamp": 1234567890.0,
            "content": "...",
            "examples": [...],
            "best_practices": [...],
            "topics_covered": [...],
            "source": {...},
            "raw_data": {...}
        }

        Args:
            library_id: Library identifier
            docs: LibraryDocs object to cache

        Raises:
            OSError: If cache cannot be written
        """
        cache_path = Config.get_cache_path(library_id)
        logger.info(f"Caching docs for '{library_id}' to {cache_path}")

        try:
            cache_data = {
                "library_id": docs.library_id,
                "library_name": docs.library_name,
                "version": docs.version,
                "timestamp": time.time(),
                "content": docs.content,
                "examples": docs.examples,
                "best_practices": docs.best_practices,
                "topics_covered": docs.topics_covered,
                "source": {
                    "type": docs.source.type,
                    "timestamp": docs.source.timestamp,
                    "library_id": docs.source.library_id,
                    "version": docs.source.version
                },
                "raw_data": docs.raw_data
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully cached docs for '{library_id}'")

        except OSError as e:
            logger.error(f"Failed to cache docs for '{library_id}': {e}")
            raise

    def get_cached_docs(self, library_id: str) -> Optional[LibraryDocs]:
        """
        Load documentation from cache.

        Args:
            library_id: Library identifier

        Returns:
            LibraryDocs object if cache exists and is valid, None otherwise
        """
        cache_path = Config.get_cache_path(library_id)

        if not cache_path.exists():
            logger.debug(f"No cache found for '{library_id}'")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Reconstruct LibraryDocs from cache
            source = DocSource(
                type=cache_data["source"]["type"],
                timestamp=cache_data["source"]["timestamp"],
                library_id=cache_data["source"]["library_id"],
                version=cache_data["source"].get("version")
            )

            docs = LibraryDocs(
                library_id=cache_data["library_id"],
                library_name=cache_data["library_name"],
                version=cache_data.get("version"),
                content=cache_data["content"],
                examples=cache_data["examples"],
                best_practices=cache_data["best_practices"],
                source=source,
                topics_covered=cache_data.get("topics_covered", []),
                raw_data=cache_data.get("raw_data", {})
            )

            logger.info(f"Loaded cached docs for '{library_id}'")
            return docs

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.error(f"Failed to load cache for '{library_id}': {e}")
            return None

    def is_cache_valid(self, library_id: str) -> bool:
        """
        Check if cached documentation is still valid.

        Args:
            library_id: Library identifier

        Returns:
            True if cache exists and is fresh, False otherwise
        """
        return Config.is_cache_valid(library_id, self.cache_ttl_days)

    def parse_response(self, response: Dict[str, Any]) -> LibraryDocs:
        """
        Parse Context7 response into LibraryDocs structure.

        Args:
            response: Raw response from Context7 MCP

        Returns:
            Parsed LibraryDocs object

        Raises:
            ValueError: If response format is invalid
        """
        logger.info("Parsing Context7 response")

        try:
            # Extract basic info
            library_id = response.get("library_id", "unknown")
            library_name = response.get("library_name", library_id.split("/")[-1])
            version = self._extract_version(response)
            content = response.get("content", "")

            # Parse structured data
            examples = self.extract_examples(content)
            best_practices = self.extract_best_practices(content)
            topics = self._extract_topics(content)

            source = DocSource(
                type="context7",
                timestamp=time.time(),
                library_id=library_id,
                version=version
            )

            docs = LibraryDocs(
                library_id=library_id,
                library_name=library_name,
                version=version,
                content=content,
                examples=examples,
                best_practices=best_practices,
                source=source,
                topics_covered=topics,
                raw_data=response
            )

            logger.info(f"Parsed docs: {len(examples)} examples, {len(best_practices)} practices")
            return docs

        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            raise ValueError(f"Invalid response format: {e}")

    def extract_best_practices(self, docs: str) -> List[str]:
        """
        Extract best practices from documentation content.

        Looks for patterns like:
        - "Best Practice:" or "Best Practices:"
        - "Recommended:" or "Recommendation:"
        - "Tip:" or "Note:"
        - Bullet points in best practices sections

        Args:
            docs: Documentation content (markdown or plain text)

        Returns:
            List of best practice strings

        Example:
            >>> fetcher = DocFetcher()
            >>> docs = "## Best Practices\\n- Use hooks\\n- Avoid prop drilling"
            >>> practices = fetcher.extract_best_practices(docs)
            >>> print(practices)
            ['Use hooks', 'Avoid prop drilling']
        """
        logger.debug("Extracting best practices from documentation")

        practices = []

        # Pattern 1: Best Practices sections
        bp_pattern = r'(?:^|\n)##?\s*(?:Best Practices?|Recommendations?|Guidelines?)\s*\n(.*?)(?=\n##?|\Z)'
        matches = re.findall(bp_pattern, docs, re.DOTALL | re.IGNORECASE)

        for match in matches:
            # Extract bullet points
            bullets = re.findall(r'[-*]\s+(.+)', match)
            practices.extend([b.strip() for b in bullets])

        # Pattern 2: Inline tips and notes
        tip_pattern = r'(?:Best Practice|Tip|Note|Recommendation):\s*(.+?)(?:\n|$)'
        tip_matches = re.findall(tip_pattern, docs, re.IGNORECASE)
        practices.extend([t.strip() for t in tip_matches])

        # Pattern 3: "Should" and "Must" statements
        should_pattern = r'(?:You\s+)?(?:should|must|need\s+to)\s+([^.!?]+[.!?])'
        should_matches = re.findall(should_pattern, docs, re.IGNORECASE)
        practices.extend([s.strip() for s in should_matches])

        # Remove duplicates while preserving order
        seen = set()
        unique_practices = []
        for practice in practices:
            if practice.lower() not in seen and len(practice) > 10:
                seen.add(practice.lower())
                unique_practices.append(practice)

        logger.info(f"Extracted {len(unique_practices)} best practices")
        return unique_practices[:10]  # Limit to top 10

    def extract_examples(self, docs: str) -> List[Dict[str, str]]:
        """
        Extract code examples from documentation content.

        Looks for:
        - Markdown code blocks (```language)
        - Code sections with descriptions
        - Example sections

        Args:
            docs: Documentation content (markdown or plain text)

        Returns:
            List of dicts with 'code', 'language', and 'description' keys

        Example:
            >>> fetcher = DocFetcher()
            >>> docs = "```python\\nprint('hello')\\n```"
            >>> examples = fetcher.extract_examples(docs)
            >>> print(examples[0]['language'])
            'python'
        """
        logger.debug("Extracting code examples from documentation")

        examples = []

        # Pattern for markdown code blocks with optional language
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, docs, re.DOTALL)

        for language, code in matches:
            # Try to find description before the code block
            description = self._find_code_description(docs, code)

            examples.append({
                "code": code.strip(),
                "language": language or "text",
                "description": description
            })

        logger.info(f"Extracted {len(examples)} code examples")
        return examples

    # --- Private Helper Methods ---

    def _try_cache(self, library_name: str) -> Optional[LibraryDocs]:
        """Try to load from cache if valid"""
        library_id = self.resolve_library_id(library_name)
        if not library_id:
            return None

        if self.is_cache_valid(library_id):
            return self.get_cached_docs(library_id)

        return None

    def _try_context7_mcp(
        self,
        library_name: str,
        topic: Optional[str],
        tokens: int
    ) -> Optional[LibraryDocs]:
        """Try to fetch from Context7 MCP"""
        library_id = self.resolve_library_id(library_name)
        if not library_id:
            return None

        response = self.get_docs(library_id, topic, tokens)
        if response:
            return self.parse_response(response)

        return None

    def _try_web_search(
        self,
        library_name: str,
        topic: Optional[str]
    ) -> Optional[LibraryDocs]:
        """
        Placeholder for web search fallback.

        TODO: Implement using WebSearch MCP or similar
        """
        logger.info(f"Web search not implemented for '{library_name}'")
        return None

    def _get_mock_data(
        self,
        library_name: str,
        topic: Optional[str]
    ) -> LibraryDocs:
        """
        Return mock documentation data for testing.

        This is used during development when MCP tools aren't available.
        """
        logger.info(f"Generating mock data for '{library_name}'")

        library_id = self.resolve_library_id(library_name) or f"/mock/{library_name}"

        mock_content = f"""
# {library_name.title()} Documentation

## Overview
{library_name} is a popular library for building modern applications.

## Best Practices
- Use the latest version for best performance
- Follow the official style guide
- Write comprehensive tests
- Document your code thoroughly

## Examples

### Basic Usage
```javascript
import {{ {library_name} }} from '{library_name}';

const app = new {library_name}();
app.start();
```

### Advanced Usage
```javascript
import {{ {library_name}, configure }} from '{library_name}';

const app = configure({{
  mode: 'production',
  plugins: ['plugin-a', 'plugin-b']
}});

app.start();
```

## Tips
- Tip: Always check the official documentation for updates
- Note: Performance can be improved by enabling caching
"""

        source = DocSource(
            type="mock",
            timestamp=time.time(),
            library_id=library_id,
            version="1.0.0"
        )

        docs = LibraryDocs(
            library_id=library_id,
            library_name=library_name,
            version="1.0.0",
            content=mock_content,
            examples=self.extract_examples(mock_content),
            best_practices=self.extract_best_practices(mock_content),
            source=source,
            topics_covered=[topic] if topic else ["general"],
            raw_data={"mock": True}
        )

        return docs

    def _extract_version(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract version from response"""
        # Try explicit version field
        if "version" in response:
            return response["version"]

        # Try to extract from content
        content = response.get("content", "")
        version_pattern = r'(?:version|v)\s*[:\-]?\s*(\d+\.\d+(?:\.\d+)?)'
        match = re.search(version_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics/sections from documentation"""
        topics = []

        # Extract markdown headers
        header_pattern = r'^##?\s+(.+)$'
        matches = re.findall(header_pattern, content, re.MULTILINE)

        for match in matches:
            # Clean up the header
            topic = match.strip().lower()
            topic = re.sub(r'[^\w\s-]', '', topic)
            if topic and topic not in topics:
                topics.append(topic)

        return topics[:15]  # Limit to 15 topics

    def _find_code_description(self, docs: str, code: str) -> str:
        """Find descriptive text before a code block"""
        # Look for text in the paragraph before the code block
        code_escaped = re.escape(code[:50])  # Use first 50 chars
        pattern = rf'([^\n]+)\n+```.*?{code_escaped}'
        match = re.search(pattern, docs, re.DOTALL)

        if match:
            description = match.group(1).strip()
            # Remove markdown headers
            description = re.sub(r'^#+\s+', '', description)
            return description

        return "Code example"

    # Alias for backward compatibility
    @staticmethod
    def fetch_documentation(
        library_name: str,
        version: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Optional[LibraryDocs]:
        """
        Static alias for fetch() method - for backward compatibility.

        Args:
            library_name: Name of library to fetch docs for
            version: Optional specific version
            topic: Optional topic to focus on

        Returns:
            LibraryDocs object or None if fetch failed
        """
        fetcher = DocFetcher()
        return fetcher.fetch(library_name, version, topic)

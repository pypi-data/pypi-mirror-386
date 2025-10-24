# MCP Integration - SkillForge

**Complete guide to Model Context Protocol (MCP) integration for intelligent skill generation**

This document provides comprehensive specifications for integrating MCP servers into SkillForge, with primary focus on Context7 for documentation fetching, Sequential Thinking for complex reasoning, and extensible patterns for future integrations.

---

## 1. MCP Overview

### What is MCP?

**Model Context Protocol (MCP)** is Anthropic's standardized protocol that enables Large Language Models to communicate with external tools and services in a secure, consistent manner.

MCP provides:
- Standardized tool interfaces
- Secure execution contexts
- Type-safe parameter passing
- Error handling conventions
- Resource management

### Why SkillForge Uses MCP

SkillForge leverages MCP to solve critical challenges in skill generation:

**Problems Solved**:
- ❌ **Outdated Documentation**: Claude's training cutoff means framework examples can be months or years old
- ❌ **Hallucinated APIs**: LLMs sometimes invent non-existent functions or methods
- ❌ **Version Mismatches**: Using React 17 patterns when user has React 18+
- ❌ **Inefficient Reasoning**: Complex orchestration tasks need structured thinking
- ❌ **Limited Context**: Static skills can't access latest best practices

**Solutions Provided**:
- ✅ **Real-time Documentation**: Fetch current, version-specific docs via Context7
- ✅ **Verified APIs**: Use official documentation sources
- ✅ **Version Awareness**: Match documentation to user's installed versions
- ✅ **Structured Reasoning**: Break down complex problems with Sequential Thinking
- ✅ **Dynamic Skills**: Generate skills with latest patterns and practices

### MCP Architecture in SkillForge

```
┌─────────────────────────────────────────────────────────┐
│                    SkillForge System                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Generator   │  │ Orchestrator │  │  Optimizer   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │         │
└─────────┼─────────────────┼──────────────────┼─────────┘
          │                 │                  │
          ↓                 ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│                   MCP Layer (Claude)                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Context7   │  │  Sequential  │  │  Web Search  │ │
│  │     MCP      │  │   Thinking   │  │     MCP      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼─────────────────┼──────────────────┼─────────┘
          │                 │                  │
          ↓                 ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│               External Services & Data                  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Context7 DB │  │   Reasoning  │  │   Internet   │ │
│  │  (1000+ libs)│  │    Engine    │  │  (fallback)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Benefits

**For Skill Generation**:
1. **Accuracy**: Always use current, official documentation
2. **Consistency**: Same integration patterns across all skills
3. **Maintainability**: Single source of truth for documentation
4. **Flexibility**: Easy to add new MCP servers as needed
5. **Performance**: Efficient caching reduces redundant fetches

**For Users**:
1. **Trust**: Skills use verified, up-to-date information
2. **Transparency**: Know which docs were used to generate skills
3. **Customization**: Skills match user's specific versions
4. **Quality**: Reduced hallucinations and outdated patterns

---

## 2. Context7 Integration (PRIMARY)

Context7 is the **primary MCP server** for SkillForge, providing version-specific documentation for 1000+ libraries and frameworks.

### A. Setup & Configuration

#### Prerequisites

1. **Context7 MCP Server Installed**
   - Available through MCP marketplace
   - Or install manually: `npm install -g @upstash/context7-mcp`

2. **Claude Configuration**
   - Context7 must be enabled in Claude's MCP settings
   - Verify with: Check available MCP tools include `mcp__context7__*`

3. **SkillForge Configuration**

```python
# skillforge/generators/config.py

class Context7Config:
    """Configuration for Context7 integration"""

    # Enable/disable Context7
    ENABLED: bool = True

    # Default token limits for documentation fetching
    DEFAULT_TOKENS: int = 5000  # Balanced for skill generation
    MIN_TOKENS: int = 1000      # Minimal fetch
    MAX_TOKENS: int = 10000     # Comprehensive fetch

    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_DAYS: int = 7     # Cache documentation for 7 days
    CACHE_DIR: Path = Path.home() / ".claude" / "skills" / "skillforge" / "data" / "cache" / "context7"

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 2

    # Trust score threshold (0-10)
    MIN_TRUST_SCORE: int = 7    # Only use high-quality docs

    # Fallback settings
    FALLBACK_TO_WEB_SEARCH: bool = True
    FALLBACK_TO_CACHE: bool = True
    ALLOW_STALE_CACHE: bool = True  # Use old cache if nothing else works
```

#### Testing Connection

```python
# skillforge/generators/mcp/context7_test.py

def test_context7_connection() -> bool:
    """
    Test Context7 MCP connection

    Returns:
        True if Context7 is available and working
    """
    try:
        # Try resolving a known library
        result = mcp__context7__resolve_library_id(
            libraryName="react"
        )

        if result and 'matches' in result:
            print("✅ Context7 connection successful")
            return True
        else:
            print("⚠️  Context7 returned unexpected format")
            return False

    except Exception as e:
        print(f"❌ Context7 connection failed: {e}")
        return False

# Usage
if __name__ == "__main__":
    if test_context7_connection():
        print("Context7 is ready for use")
    else:
        print("Check Context7 MCP server configuration")
```

### B. Library ID Resolution

The first step in fetching documentation is resolving a human-readable library name to a Context7-compatible ID.

#### resolve-library-id Function

```python
# skillforge/generators/mcp/context7_resolver.py

from typing import Optional, List, Dict, Any
import json

class LibraryResolver:
    """Resolve library names to Context7-compatible IDs"""

    def __init__(self):
        self.cache = {}  # In-memory cache for resolved IDs

    def resolve(self, library_name: str) -> Optional[str]:
        """
        Resolve library name to Context7 ID

        Args:
            library_name: Human-readable name (e.g., "Next.js", "react", "FastAPI")

        Returns:
            Context7-compatible library ID (e.g., "/vercel/next.js")
            None if library not found

        Example:
            >>> resolver = LibraryResolver()
            >>> library_id = resolver.resolve("Next.js")
            >>> print(library_id)
            "/vercel/next.js"
        """
        # Check in-memory cache first
        if library_name in self.cache:
            return self.cache[library_name]

        try:
            # Call Context7 MCP tool
            response = mcp__context7__resolve_library_id(
                libraryName=library_name
            )

            # Parse response
            matches = response.get('matches', [])

            if not matches:
                print(f"⚠️  No matches found for: {library_name}")
                return None

            # Select best match
            best_match = self._select_best_match(matches)
            library_id = best_match['id']

            # Cache result
            self.cache[library_name] = library_id

            return library_id

        except Exception as e:
            print(f"❌ Error resolving {library_name}: {e}")
            return None

    def _select_best_match(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select best match from multiple results

        Selection criteria (in order):
        1. Highest trust_score (7-10 preferred)
        2. Most code_snippets (more examples = better)
        3. Most recent updated_at timestamp

        Args:
            matches: List of library matches from Context7

        Returns:
            Best matching library dictionary
        """
        if len(matches) == 1:
            return matches[0]

        # Sort by multiple criteria
        sorted_matches = sorted(
            matches,
            key=lambda m: (
                m.get('trust_score', 0),        # Primary: trust score
                m.get('code_snippets', 0),      # Secondary: examples count
                m.get('updated_at', '')         # Tertiary: recency
            ),
            reverse=True
        )

        best = sorted_matches[0]

        # Log selection decision
        print(f"Selected: {best['name']} (trust: {best.get('trust_score')}/10)")

        return best
```

#### Matching Algorithm

Context7's matching algorithm considers:

1. **Name Similarity**
   - Exact matches (highest priority)
   - Case-insensitive matches
   - Common aliases (e.g., "Next" → "Next.js")

2. **Trust Score** (0-10 scale)
   - 9-10: Official repositories
   - 7-8: Well-maintained, popular libraries
   - 5-6: Community libraries
   - < 5: Use with caution

3. **Documentation Coverage**
   - Number of code snippets
   - Completeness of API reference
   - Quality of examples

#### Fallback Strategies

```python
class LibraryResolver:
    # ... continued from above

    def resolve_with_fallback(self, library_name: str) -> Optional[str]:
        """
        Resolve with multiple fallback strategies

        Fallback chain:
        1. Context7 API call
        2. Local mappings (common libraries)
        3. Fuzzy search in cache
        4. None (trigger web search fallback)
        """
        # Strategy 1: Context7 API
        library_id = self.resolve(library_name)
        if library_id:
            return library_id

        # Strategy 2: Local mappings
        library_id = self._get_from_local_mappings(library_name)
        if library_id:
            print(f"ℹ️  Using local mapping for {library_name}")
            return library_id

        # Strategy 3: Fuzzy search
        library_id = self._fuzzy_search_cache(library_name)
        if library_id:
            print(f"ℹ️  Using fuzzy match for {library_name}")
            return library_id

        # Strategy 4: Failed - return None
        print(f"⚠️  Could not resolve {library_name}")
        return None

    def _get_from_local_mappings(self, library_name: str) -> Optional[str]:
        """Hardcoded mappings for common libraries"""
        mappings = {
            # Frontend frameworks
            "react": "/facebook/react",
            "nextjs": "/vercel/next.js",
            "next.js": "/vercel/next.js",
            "vue": "/vuejs/core",
            "vue.js": "/vuejs/core",
            "nuxt": "/nuxt/nuxt",
            "angular": "/angular/angular",
            "svelte": "/sveltejs/svelte",

            # Backend frameworks
            "express": "/expressjs/express",
            "fastapi": "/tiangolo/fastapi",
            "django": "/django/django",
            "flask": "/pallets/flask",
            "nestjs": "/nestjs/nest",

            # Libraries
            "typescript": "/microsoft/TypeScript",
            "tailwind": "/tailwindlabs/tailwindcss",
            "tailwindcss": "/tailwindlabs/tailwindcss",
            "prisma": "/prisma/prisma",
            "supabase": "/supabase/supabase",

            # Testing
            "jest": "/jestjs/jest",
            "vitest": "/vitest-dev/vitest",
            "pytest": "/pytest-dev/pytest",
            "playwright": "/microsoft/playwright",
        }

        return mappings.get(library_name.lower())

    def _fuzzy_search_cache(self, library_name: str) -> Optional[str]:
        """Search cache for similar names"""
        # Implementation of fuzzy search
        # Returns closest match if confidence > 0.8
        pass
```

#### Caching Strategy

```python
# Cache structure
# ~/.claude/skills/skillforge/data/cache/context7/
#   ├── _resolutions.json          # Library name → ID mappings
#   ├── facebook_react.json         # Documentation cache
#   ├── vercel_next_js.json
#   └── ...

class ResolutionCache:
    """Cache for library ID resolutions"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "_resolutions.json"
        self.resolutions = self._load()

    def _load(self) -> Dict[str, str]:
        """Load cached resolutions"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def get(self, library_name: str) -> Optional[str]:
        """Get cached resolution"""
        return self.resolutions.get(library_name.lower())

    def set(self, library_name: str, library_id: str):
        """Cache resolution"""
        self.resolutions[library_name.lower()] = library_id
        self._save()

    def _save(self):
        """Save cache to disk"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.resolutions, f, indent=2)
```

### C. Documentation Fetching

Once we have a library ID, we fetch its documentation using `get-library-docs`.

#### get-library-docs Function

```python
# skillforge/generators/mcp/context7_fetcher.py

from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

class DocumentationFetcher:
    """Fetch library documentation via Context7"""

    def __init__(self, cache_dir: Path, resolver: LibraryResolver):
        self.cache_dir = cache_dir
        self.resolver = resolver
        self.cache_ttl = timedelta(days=7)

    def fetch(
        self,
        library_name: str,
        topic: Optional[str] = None,
        tokens: int = 5000
    ) -> Optional[str]:
        """
        Fetch documentation for a library

        Args:
            library_name: Human-readable library name
            topic: Optional focus topic (e.g., "hooks", "routing")
            tokens: Token budget (default: 5000)

        Returns:
            Markdown-formatted documentation
            None if fetch fails

        Example:
            >>> fetcher = DocumentationFetcher(cache_dir, resolver)
            >>> docs = fetcher.fetch("Next.js", topic="App Router", tokens=3000)
            >>> print(len(docs))
            8542
        """
        # Step 1: Resolve library ID
        library_id = self.resolver.resolve(library_name)

        if not library_id:
            print(f"⚠️  Cannot fetch docs: {library_name} not resolved")
            return None

        # Step 2: Check cache
        cached_docs = self._get_cached_docs(library_id, topic)
        if cached_docs:
            print(f"✅ Using cached docs for {library_name}")
            return cached_docs

        # Step 3: Fetch from Context7
        try:
            docs = self._fetch_from_context7(library_id, topic, tokens)

            # Step 4: Cache result
            self._cache_docs(library_id, topic, docs)

            print(f"✅ Fetched {len(docs)} chars from Context7: {library_name}")
            return docs

        except Exception as e:
            print(f"❌ Failed to fetch docs for {library_name}: {e}")

            # Try stale cache as last resort
            stale_docs = self._get_cached_docs(library_id, topic, allow_stale=True)
            if stale_docs:
                print(f"⚠️  Using stale cache for {library_name}")
                return stale_docs

            return None

    def _fetch_from_context7(
        self,
        library_id: str,
        topic: Optional[str],
        tokens: int
    ) -> str:
        """Call Context7 MCP tool to fetch docs"""
        params = {
            "context7CompatibleLibraryID": library_id,
            "tokens": tokens
        }

        if topic:
            params["topic"] = topic

        # Call MCP tool
        docs = mcp__context7__get_library_docs(**params)

        return docs

    def _get_cached_docs(
        self,
        library_id: str,
        topic: Optional[str],
        allow_stale: bool = False
    ) -> Optional[str]:
        """Get documentation from cache"""
        cache_key = self._get_cache_key(library_id, topic)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check freshness
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            age = datetime.now() - cached_time

            if age <= self.cache_ttl or allow_stale:
                return cache_data['content']

            # Cache is stale and allow_stale=False
            return None

        except Exception as e:
            print(f"⚠️  Cache read error: {e}")
            return None

    def _cache_docs(self, library_id: str, topic: Optional[str], content: str):
        """Cache documentation to disk"""
        cache_key = self._get_cache_key(library_id, topic)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            'library_id': library_id,
            'topic': topic,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'expires_at': (datetime.now() + self.cache_ttl).isoformat()
        }

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def _get_cache_key(self, library_id: str, topic: Optional[str]) -> str:
        """Generate cache key"""
        # Sanitize library_id for filesystem
        safe_id = library_id.replace('/', '_').replace('@', '_').replace('.', '_')

        if topic:
            safe_topic = topic.lower().replace(' ', '_').replace('/', '_')
            return f"{safe_id}_{safe_topic}"

        return safe_id
```

#### Token Limits

**Token Budget Guidelines**:

```python
class TokenBudget:
    """Token budget recommendations for different scenarios"""

    # Overview generation - just the basics
    OVERVIEW = 1000

    # Quick reference - key patterns only
    QUICK_REFERENCE = 2000

    # Standard skill generation - balanced
    STANDARD = 5000  # RECOMMENDED

    # Comprehensive - everything
    COMPREHENSIVE = 8000

    # Maximum (use sparingly)
    MAXIMUM = 10000
```

**Token Usage by Section**:
- API Overview: ~500-800 tokens
- Best Practices: ~800-1200 tokens
- Code Examples: ~1000-2000 tokens
- Advanced Patterns: ~1500-2500 tokens
- Troubleshooting: ~500-1000 tokens

#### Topic Focusing

Using the `topic` parameter significantly improves relevance and reduces token waste.

```python
# Example: Topic focusing for Next.js

# ❌ Without topic (10,000 tokens for everything)
docs = fetcher.fetch("Next.js", tokens=10000)
# Returns: All Next.js docs (Pages Router, App Router, API Routes, etc.)

# ✅ With topic (3,000 tokens, focused)
docs = fetcher.fetch("Next.js", topic="App Router", tokens=3000)
# Returns: Only App Router documentation (exactly what we need)

# Topic examples by framework:
topics = {
    "Next.js": ["App Router", "API Routes", "Server Components", "Routing"],
    "React": ["Hooks", "Server Components", "Context", "Performance"],
    "FastAPI": ["Async", "Dependencies", "Database", "Authentication"],
    "Django": ["Models", "Views", "ORM", "Admin"],
    "Supabase": ["Auth", "Database", "Realtime", "Storage"]
}
```

#### Response Parsing

```python
def parse_documentation(docs: str) -> Dict[str, Any]:
    """
    Parse fetched documentation into structured sections

    Returns:
        {
            'best_practices': List[str],
            'code_examples': List[Dict],
            'api_reference': str,
            'version': str
        }
    """
    parsed = {
        'best_practices': [],
        'code_examples': [],
        'api_reference': '',
        'version': ''
    }

    # Extract version
    version_match = re.search(r'version[:\s]+([0-9.]+)', docs, re.IGNORECASE)
    if version_match:
        parsed['version'] = version_match.group(1)

    # Extract code examples
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', docs, re.DOTALL)
    for lang, code in code_blocks:
        parsed['code_examples'].append({
            'language': lang or 'plaintext',
            'code': code.strip()
        })

    # Extract best practices (sections starting with "Best" or "Recommended")
    sections = docs.split('\n##')
    for section in sections:
        if any(keyword in section.lower() for keyword in ['best', 'recommend', 'should', 'must']):
            parsed['best_practices'].append(section.strip())

    return parsed
```

### D. Best Practices

#### When to Fetch

```python
# ✅ ALWAYS fetch on skill generation
def generate_skill(profile, skill_type):
    # Fetch latest docs FIRST
    docs = fetch_documentation(profile['tech_stack'])
    # Then generate skill using fresh docs
    skill = create_skill_from_docs(docs, profile)
    return skill

# ✅ Fetch on skill updates
def update_skill(skill_path):
    skill = load_skill(skill_path)
    # Check if docs are outdated
    if is_outdated(skill.metadata['framework_version']):
        fresh_docs = fetch_documentation(skill.framework)
        skill.update_with_docs(fresh_docs)

# ❌ DON'T fetch at runtime (use generated skills)
def execute_task(task):
    # Skills are already loaded, don't fetch again
    selected_skills = discover_skills(task)
    execute_with_skills(selected_skills)
```

#### What to Cache

**CACHE** ✅:
- Documentation content (7 days)
- Library ID resolutions (30 days)
- Best practices (7 days)
- Code examples (7 days)

**DON'T CACHE** ❌:
- User-specific information
- Generated skill content
- API responses with errors
- Incomplete fetches

#### Cache Duration

```python
# Recommended TTL by content type
CACHE_TTL = {
    'documentation': timedelta(days=7),    # Weekly refresh
    'resolutions': timedelta(days=30),     # Monthly refresh
    'versions': timedelta(days=1),         # Daily check
    'examples': timedelta(days=7),         # Weekly refresh
}

# When to force refresh:
FORCE_REFRESH_IF = [
    'user_explicitly_requests',
    'generation_fails_with_cache',
    'cache_age > 30_days',
    'new_major_version_detected'
]
```

#### Rate Limiting

```python
class RateLimiter:
    """Prevent excessive Context7 API calls"""

    def __init__(self):
        self.calls = []
        self.max_calls_per_minute = 20
        self.max_calls_per_hour = 100

    def can_call(self) -> bool:
        """Check if we can make another call"""
        now = datetime.now()

        # Clean old calls
        self.calls = [t for t in self.calls if now - t < timedelta(hours=1)]

        # Check limits
        recent_minute = sum(1 for t in self.calls if now - t < timedelta(minutes=1))
        recent_hour = len(self.calls)

        return (recent_minute < self.max_calls_per_minute and
                recent_hour < self.max_calls_per_hour)

    def record_call(self):
        """Record that a call was made"""
        self.calls.append(datetime.now())
```

### E. Error Handling

#### Network Errors

```python
def fetch_with_retry(library_id: str, max_retries: int = 3) -> Optional[str]:
    """Fetch with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            docs = fetch_from_context7(library_id)
            return docs
        except NetworkError as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"⚠️  Network error, retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ Network error after {max_retries} attempts: {e}")
                return None
```

#### API Errors

```python
def handle_context7_error(error: Exception) -> Optional[str]:
    """
    Handle Context7-specific errors

    Error types:
    - LibraryNotFoundError: Library doesn't exist in Context7
    - RateLimitError: Too many requests
    - AuthenticationError: MCP authentication issue
    - TimeoutError: Request took too long
    """
    if isinstance(error, LibraryNotFoundError):
        print(f"⚠️  Library not in Context7, trying web search")
        return fallback_to_web_search()

    elif isinstance(error, RateLimitError):
        print(f"⚠️  Rate limit hit, using cache")
        return get_cached_docs(allow_stale=True)

    elif isinstance(error, AuthenticationError):
        print(f"❌ MCP authentication failed - check Context7 setup")
        return None

    elif isinstance(error, TimeoutError):
        print(f"⚠️  Request timeout, trying with lower token limit")
        return fetch_with_reduced_tokens()

    else:
        print(f"❌ Unknown error: {error}")
        return None
```

#### Stale Data Handling

```python
def get_documentation_with_freshness_check(
    library_name: str,
    max_age_days: int = 7
) -> Tuple[Optional[str], str]:
    """
    Get documentation with freshness indicator

    Returns:
        (docs, freshness_status)
        freshness_status: "fresh", "cached", "stale", "unavailable"
    """
    # Try fresh fetch
    try:
        docs = fetch_from_context7(library_name)
        return docs, "fresh"
    except Exception:
        pass

    # Try recent cache
    cached_docs = get_cached_docs(library_name, max_age=timedelta(days=max_age_days))
    if cached_docs:
        return cached_docs, "cached"

    # Try stale cache
    stale_docs = get_cached_docs(library_name, allow_stale=True)
    if stale_docs:
        return stale_docs, "stale"

    # No docs available
    return None, "unavailable"
```

#### Fallback to web_search

```python
def fetch_documentation_with_fallback(library_name: str) -> Tuple[str, str]:
    """
    Fetch documentation with multi-tier fallback

    Fallback chain:
    1. Context7 (fresh) ✅ PREFERRED
    2. Cache (< 7 days) ⚠️ ACCEPTABLE
    3. Cache (stale) ⚠️ LAST RESORT
    4. Web Search 🔍 FALLBACK

    Returns:
        (docs, source)
        source: "context7", "cache", "stale_cache", "web_search", "failed"
    """
    # Tier 1: Context7
    try:
        docs = fetch_from_context7(library_name)
        return docs, "context7"
    except Exception as e:
        print(f"⚠️  Context7 failed: {e}")

    # Tier 2: Fresh cache
    cached = get_cached_docs(library_name)
    if cached:
        return cached, "cache"

    # Tier 3: Stale cache
    stale = get_cached_docs(library_name, allow_stale=True)
    if stale:
        print(f"⚠️  Using stale cache for {library_name}")
        return stale, "stale_cache"

    # Tier 4: Web search
    try:
        docs = web_search_docs(library_name)
        return docs, "web_search"
    except Exception as e:
        print(f"❌ Web search failed: {e}")

    # All fallbacks exhausted
    return "", "failed"

def web_search_docs(library_name: str) -> str:
    """Fallback: Search web for documentation"""
    # Use MCP web search
    query = f"{library_name} official documentation latest"
    results = mcp__web_search(query=query)

    # Parse and extract relevant content
    docs = extract_docs_from_search(results)

    return docs
```

---

## 3. Sequential Thinking Integration (SECONDARY)

Sequential Thinking MCP is used for complex multi-step reasoning tasks.

### When to Use Sequential Thinking

**USE** ✅:
- Skill generation requires >5 decision points
- Complex orchestration logic
- Analyzing skill overlap and redundancy
- Optimizing skill combinations
- Architecture decisions

**DON'T USE** ❌:
- Simple skill generation
- Documentation fetching
- Cache management
- Linear workflows

### Integration Pattern

```python
def generate_complex_skill_with_reasoning(requirements: Dict) -> str:
    """
    Use Sequential Thinking for complex skill generation
    """
    # Invoke Sequential Thinking MCP
    reasoning_result = mcp__sequential_thinking__sequentialthinking(
        thought="User wants to generate a skill for a complex tech stack. "
               "I need to analyze: 1) Which frameworks work together, "
               "2) What documentation to fetch, 3) How to structure the skill, "
               "4) What patterns to include",
        nextThoughtNeeded=True,
        thoughtNumber=1,
        totalThoughts=8
    )

    # Continue reasoning chain
    # ... (Sequential Thinking handles the breakdown)

    # Once reasoning complete, generate skill
    return create_skill_from_reasoning(reasoning_result)
```

### Example: Skill Optimization

```python
def optimize_skills_with_reasoning(skills: List[Skill]) -> List[str]:
    """
    Use Sequential Thinking to optimize skill set

    Complex decisions:
    1. Which skills overlap?
    2. Should they be merged or kept separate?
    3. What's the optimal token budget allocation?
    4. Are there redundant patterns?
    """
    # Start reasoning chain
    # Thought 1: Analyze overlaps
    # Thought 2: Calculate redundancy scores
    # Thought 3: Determine merge candidates
    # Thought 4: Validate merged result
    # Thought 5: Final recommendations

    # Implementation uses Sequential Thinking MCP
    pass
```

---

## 4. Other MCP Servers

### Web Search/Fetch (Fallback)

```python
# Use when Context7 unavailable or library not found
def fallback_web_search(library_name: str) -> str:
    docs = mcp__web_search(
        query=f"{library_name} documentation latest version"
    )
    return extract_relevant_docs(docs)
```

### Filesystem Operations

```python
# For skill file management
def save_generated_skill(skill_content: str, path: Path):
    mcp__filesystem__write_file(
        path=str(path),
        content=skill_content
    )
```

### Custom User MCPs

Users can add their own MCP servers for specialized needs:

```python
# Example: Custom company-internal documentation MCP
def fetch_internal_docs(library: str) -> str:
    if mcp_available("company-docs"):
        return mcp__company_docs__get_docs(library=library)
    return ""
```

---

## 5. Integration Patterns

### Primary-Fallback Pattern

```python
def fetch_with_fallback_chain(library: str) -> Tuple[str, str]:
    """Primary: Context7, Fallback: Cache → Web Search"""

    # Primary
    try:
        return fetch_from_context7(library), "context7"
    except:
        pass

    # Fallback 1: Cache
    cached = get_cache(library)
    if cached:
        return cached, "cache"

    # Fallback 2: Web search
    try:
        return web_search(library), "web_search"
    except:
        pass

    # Failed
    return "", "failed"
```

### Parallel Queries

```python
async def fetch_multiple_docs(libraries: List[str]) -> Dict[str, str]:
    """Fetch docs for multiple libraries in parallel"""

    tasks = [
        fetch_documentation_async(lib)
        for lib in libraries
    ]

    results = await asyncio.gather(*tasks)

    return dict(zip(libraries, results))
```

### Sequential Chaining

```python
def generate_skill_with_chaining(requirements: Dict) -> str:
    """Chain multiple MCP calls in sequence"""

    # Step 1: Resolve libraries
    library_ids = [
        resolve_library_id(lib)
        for lib in requirements['libraries']
    ]

    # Step 2: Fetch docs (depends on step 1)
    docs = {
        lib_id: fetch_docs(lib_id)
        for lib_id in library_ids
    }

    # Step 3: Generate skill (depends on step 2)
    skill = generate_from_docs(docs, requirements)

    return skill
```

### Caching Layer

```python
class MCPCache:
    """Unified cache for all MCP operations"""

    def __init__(self):
        self.context7_cache = Context7Cache()
        self.search_cache = SearchCache()

    def get_or_fetch(self, key: str, fetcher: Callable) -> Any:
        """Get from cache or fetch and cache"""
        cached = self.get(key)
        if cached:
            return cached

        result = fetcher()
        self.set(key, result)
        return result
```

---

## 6. Testing Integration

### Mock MCP Server

```python
# tests/mocks/mock_context7.py

class MockContext7:
    """Mock Context7 MCP for testing"""

    def resolve_library_id(self, libraryName: str) -> Dict:
        """Mock library resolution"""
        mock_responses = {
            "react": {
                "matches": [{
                    "id": "/facebook/react",
                    "name": "React",
                    "trust_score": 10
                }]
            },
            "nextjs": {
                "matches": [{
                    "id": "/vercel/next.js",
                    "name": "Next.js",
                    "trust_score": 10
                }]
            }
        }
        return mock_responses.get(libraryName.lower(), {"matches": []})

    def get_library_docs(self, context7CompatibleLibraryID: str, **kwargs) -> str:
        """Mock documentation fetch"""
        return f"# Documentation for {context7CompatibleLibraryID}\n\nMock content..."
```

### Integration Tests

```python
# tests/integration/test_context7_integration.py

def test_fetch_react_docs():
    """Test fetching React documentation"""
    fetcher = DocumentationFetcher(cache_dir, resolver)
    docs = fetcher.fetch("react", tokens=2000)

    assert docs is not None
    assert len(docs) > 100
    assert "React" in docs

def test_cache_persistence():
    """Test that documentation is cached"""
    fetcher = DocumentationFetcher(cache_dir, resolver)

    # First fetch
    docs1 = fetcher.fetch("react")

    # Second fetch (should use cache)
    docs2 = fetcher.fetch("react")

    assert docs1 == docs2
```

### Error Scenario Tests

```python
def test_fallback_on_context7_failure():
    """Test fallback when Context7 fails"""
    with mock.patch('fetch_from_context7', side_effect=NetworkError):
        docs, source = fetch_documentation_with_fallback("react")

        assert source in ["cache", "web_search"]
        assert docs is not None
```

---

## 7. Future Integrations

### Planned MCPs

1. **GitHub MCP**: Fetch examples from real repositories
2. **StackOverflow MCP**: Common issues and solutions
3. **NPM/PyPI MCP**: Package metadata and usage stats
4. **Custom Company MCP**: Internal documentation

### Community MCPs

SkillForge is designed to support any MCP server:

```python
# User adds custom MCP in config
CUSTOM_MCPS = [
    "company-internal-docs",
    "team-conventions",
    "project-templates"
]
```

### Custom Integration Pattern

```python
def register_custom_mcp(mcp_name: str, mcp_functions: Dict):
    """Register a custom MCP server"""
    MCP_REGISTRY[mcp_name] = mcp_functions

# Usage
register_custom_mcp("my-docs", {
    "fetch_docs": my_docs_fetch_function,
    "search": my_docs_search_function
})
```

---

## Summary

SkillForge's MCP integration provides:

✅ **Context7 (Primary)**: Up-to-date documentation for 1000+ libraries
✅ **Sequential Thinking (Secondary)**: Complex reasoning for orchestration
✅ **Multi-tier Fallbacks**: Robust error handling with cache and web search
✅ **Intelligent Caching**: 7-day TTL with stale fallback
✅ **Extensible Design**: Easy to add new MCP servers
✅ **Testing Support**: Mock servers for reliable testing

**Key Principles**:
1. **Always** fetch fresh docs for skill generation
2. **Cache** aggressively (7 days)
3. **Fallback** gracefully (Context7 → Cache → Web Search)
4. **Monitor** source freshness
5. **Test** with mocks

This integration ensures SkillForge generates skills with accurate, up-to-date information while maintaining performance through intelligent caching.

---

*Last Updated: 2025-01-22*
*Version: 1.0.0*

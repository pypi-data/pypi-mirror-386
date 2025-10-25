# Context7 MCP Integration - Research Document

**Date**: 2025-10-22
**Sources**:
- https://github.com/upstash/context7
- https://lobehub.com/mcp/upstash-context7
- User's MCP_Context7.md documentation
**Purpose**: Plan Context7 integration for SkillForge skill generation

---

## Executive Summary

Context7 is an **MCP server** that provides **up-to-date, version-specific documentation** for libraries and frameworks. It's CRITICAL for SkillForge's Generator component.

**Key Value**: Eliminates outdated examples, hallucinated APIs, and ensures generated skills use latest best practices.

**Integration Points**:
1. **Generator**: Fetch docs when creating skills
2. **Optimizer**: Update docs when refreshing skills
3. **Caching**: Store fetched docs locally

---

## 1. Context7 Overview

### What It Solves

**Problems**:
- ❌ Outdated code examples (e.g., Next.js Pages Router when App Router is current)
- ❌ Hallucinated APIs (LLMs inventing non-existent functions)
- ❌ Version mismatches (using React 17 patterns in React 18)

**Solution**:
- ✅ Dynamic, version-specific documentation injection
- ✅ Real-time updates from official sources
- ✅ Curated, high-quality documentation

### Architecture

```
SkillForge Generator
    ↓
Context7 MCP Server
    ↓
Context7 Documentation Database
    - 1000+ libraries
    - Version-specific docs
    - Best practices
    - Code examples
```

---

## 2. Core Tools

### Tool 1: `resolve-library-id`

**Purpose**: Convert friendly library name → Context7-compatible ID

**Input**:
```json
{
  "libraryName": "Next.js"
}
```

**Output**:
```json
{
  "library_id": "/vercel/next.js",
  "matches": [
    {
      "id": "/vercel/next.js",
      "name": "Next.js",
      "description": "The React Framework for Production",
      "latest_version": "15.0.0",
      "trust_score": 10
    }
  ]
}
```

**Key Fields**:
- `id`: Use this for `get-library-docs`
- `trust_score`: 0-10 (prefer 7-10 for quality)
- `latest_version`: Current version available

### Tool 2: `get-library-docs`

**Purpose**: Fetch documentation for a specific library

**Input**:
```json
{
  "context7CompatibleLibraryID": "/vercel/next.js",
  "topic": "App Router",  // optional
  "tokens": 5000          // optional (default: 10000)
}
```

**Output**: Markdown-formatted documentation with:
- Best practices
- Code examples
- API reference
- Common patterns
- Version-specific info

**Token Limits**:
- Default: 10,000 tokens
- Max: Depends on plan
- Recommendation: 2000-5000 for skill generation

---

## 3. Usage Pattern

### Sequential Flow (REQUIRED)

```python
# Step 1: ALWAYS resolve library ID first
library_id = resolve_library_id("Next.js")
# Returns: "/vercel/next.js"

# Step 2: Fetch documentation
docs = get_library_docs(
    library_id="/vercel/next.js",
    topic="App Router",  # Focus on specific area
    tokens=3000          # Limit to reduce context
)

# Step 3: Parse and use
best_practices = extract_best_practices(docs)
code_examples = extract_code_examples(docs)
```

### IMPORTANT Rules

1. **MUST call resolve-library-id first**
   - Exception: User provides exact ID like `/vercel/next.js`
   - Otherwise: Always resolve

2. **Topic parameter is powerful**
   - Focuses documentation on specific area
   - Reduces irrelevant content
   - Examples: "App Router", "Server Components", "Authentication"

3. **Token budget management**
   - Default 10K is often too much
   - For skill generation: 2K-5K is ideal
   - Balance: comprehensive vs efficient

---

## 4. Integration with SkillForge

### Generator Component Integration

```python
# generators/doc_fetcher.py

class DocFetcher:
    """Fetches documentation via Context7 MCP"""

    def fetch(self, library_name: str, topic: Optional[str] = None) -> str:
        """
        Fetch documentation for a library

        Args:
            library_name: Human-readable name (e.g., "Next.js")
            topic: Optional focus area (e.g., "App Router")

        Returns:
            Markdown documentation
        """
        # Step 1: Resolve library ID
        library_id = self._resolve_library_id(library_name)

        # Step 2: Check cache
        cached = self._get_cached_docs(library_id)
        if cached and not self._is_stale(cached):
            return cached

        # Step 3: Fetch from Context7
        docs = self._fetch_from_context7(library_id, topic)

        # Step 4: Cache for future use
        self._cache_docs(library_id, docs)

        return docs

    def _resolve_library_id(self, library_name: str) -> str:
        """Call Context7 resolve-library-id tool"""
        response = mcp_call("resolve-library-id", {
            "libraryName": library_name
        })

        # Select best match (highest trust score)
        matches = response.get("matches", [])
        if not matches:
            raise LibraryNotFoundError(f"No match for {library_name}")

        best_match = max(matches, key=lambda m: m.get("trust_score", 0))
        return best_match["id"]

    def _fetch_from_context7(self,
                            library_id: str,
                            topic: Optional[str] = None) -> str:
        """Call Context7 get-library-docs tool"""
        params = {
            "context7CompatibleLibraryID": library_id,
            "tokens": 3000  # Optimized for skill generation
        }

        if topic:
            params["topic"] = topic

        docs = mcp_call("get-library-docs", params)
        return docs
```

### Caching Strategy

**Why Cache**:
- Reduce API calls
- Faster generation
- Offline capability (fallback)

**Cache Structure**:
```
data/cache/context7/
├── vercel-nextjs-15.0.0-app-router.json
├── facebook-react-18.2.0.json
└── supabase-supabase-js-2.38.0.json
```

**Cache Format**:
```json
{
  "library_id": "/vercel/next.js",
  "version": "15.0.0",
  "topic": "App Router",
  "fetched_at": "2025-10-22T10:00:00Z",
  "expires_at": "2025-10-29T10:00:00Z",  // 7 days
  "documentation": "... markdown content ..."
}
```

**Cache TTL**: 7 days (documentation doesn't change daily)

**Cache Invalidation**:
- Time-based: 7 days
- Version-based: When new version detected
- Manual: `/sf:update` command

---

## 5. Error Handling

### Common Errors

1. **Library Not Found**
   ```python
   try:
       library_id = resolve_library_id("NonExistentLib")
   except LibraryNotFoundError:
       # Fallback: use web_search
       docs = web_search(f"{library_name} documentation")
   ```

2. **Rate Limiting**
   ```python
   try:
       docs = get_library_docs(library_id)
   except RateLimitError:
       # Fallback: use cached docs (even if stale)
       docs = get_cached_docs(library_id, allow_stale=True)
   ```

3. **Network Errors**
   ```python
   try:
       docs = fetch_from_context7(library_id)
   except NetworkError:
       # Fallback: builtin knowledge or cached
       docs = get_cached_docs(library_id) or get_builtin_docs(library_name)
   ```

### Fallback Chain

```
1. Context7 (fresh docs) ✅ Preferred
    ↓ (if fails)
2. Cache (stale docs OK) ⚠️ Acceptable
    ↓ (if fails)
3. Web Search 🔍 Backup
    ↓ (if fails)
4. Builtin Knowledge 🤖 Last Resort
```

**Always Inform User**:
```
✅ "Using Context7 (Next.js 15.0.0 - latest)"
⚠️  "Using cached docs (Next.js 15.0.0 - 5 days old)"
🔍 "Context7 unavailable, using web search"
🤖 "Using builtin knowledge (may be outdated)"
```

---

## 6. Best Practices

### 1. Resolve First, Always

```python
# ❌ Wrong
docs = get_library_docs("Next.js")  # Won't work!

# ✅ Right
library_id = resolve_library_id("Next.js")
docs = get_library_docs(library_id)
```

### 2. Use Topic Parameter

```python
# ❌ Less Efficient (gets all Next.js docs)
docs = get_library_docs("/vercel/next.js", tokens=10000)

# ✅ More Efficient (focused on App Router)
docs = get_library_docs(
    "/vercel/next.js",
    topic="App Router",
    tokens=3000
)
```

### 3. Token Budget Wisely

**For Skill Generation**:
- Overview: 1000-2000 tokens
- Focused area: 2000-3000 tokens
- Comprehensive: 5000-8000 tokens

**Never**: Use default 10K blindly

### 4. Cache Aggressively

```python
# Check cache BEFORE calling Context7
if cached_docs := get_cached_docs(library_id):
    if not is_stale(cached_docs, days=7):
        return cached_docs

# Only fetch if cache miss or stale
return fetch_from_context7(library_id)
```

### 5. Select Best Match

```python
# When multiple matches, prefer:
matches = sorted(matches, key=lambda m: (
    m.get("trust_score", 0),      # Higher trust score
    m.get("code_snippets", 0),    # More examples
    m.get("updated_at", "")       # More recent
), reverse=True)

best_match = matches[0]
```

---

## 7. Context7 Limits & Constraints

### Known Constraints

1. **Coverage**
   - Not all libraries available
   - Newer/obscure libraries may not exist
   - Check trust_score < 7 → may be incomplete

2. **Version Lag**
   - Latest version may have 1-2 day delay
   - Breaking changes might not be immediate

3. **API Rate Limits**
   - Exact limits unknown (need testing)
   - Implement exponential backoff

4. **Token Costs**
   - Each fetch counts against context
   - Balance: comprehensive vs efficient

### Validation Strategy

**Before Production**:
```python
# Test Context7 with 10+ common libraries
test_libraries = [
    "Next.js",
    "React",
    "Vue",
    "Supabase",
    "Tailwind CSS",
    "TypeScript",
    "Express",
    "FastAPI",
    "Django",
    "PostgreSQL"
]

for lib in test_libraries:
    try:
        library_id = resolve_library_id(lib)
        docs = get_library_docs(library_id, tokens=1000)
        print(f"✅ {lib}: {len(docs)} chars")
    except Exception as e:
        print(f"❌ {lib}: {e}")
```

**Action**: Run this test in Week 1-2 (Fase 0)

---

## 8. SkillForge-Specific Patterns

### Pattern 1: Generation Time Fetching

```python
# generators/skill_generator.py

def generate_skill(profile, skill_type):
    """Generate a skill with fresh documentation"""

    # Get framework from profile
    framework = profile["tech_stack"].get("frontend")  # e.g., "Next.js"

    # Fetch latest docs
    docs = doc_fetcher.fetch(
        library_name=framework,
        topic=get_relevant_topic(skill_type)  # e.g., "App Router"
    )

    # Extract components
    best_practices = extract_best_practices(docs)
    code_examples = extract_code_examples(docs)
    version = extract_version(docs)

    # Generate SKILL.md
    skill_content = template_processor.process(
        template="nextjs-fullstack.template",
        variables={
            "framework_name": framework,
            "framework_version": version,
            "best_practices": best_practices,
            "code_examples": code_examples,
            "user_conventions": profile["conventions"]
        }
    )

    return skill_content
```

### Pattern 2: Update Time Refreshing

```python
# analyzers/skill_optimizer.py

def update_documentation(skill_path):
    """Refresh skill with latest docs"""

    # Parse existing skill
    skill = parse_skill(skill_path)
    framework = skill.metadata["framework_name"]
    current_version = skill.metadata["framework_version"]

    # Fetch latest docs
    docs = doc_fetcher.fetch(framework)
    latest_version = extract_version(docs)

    # Check if update needed
    if latest_version > current_version:
        # Regenerate relevant sections
        skill.update_section("best_practices", extract_best_practices(docs))
        skill.update_section("code_examples", extract_code_examples(docs))
        skill.metadata["framework_version"] = latest_version

        # Save updated skill
        skill.save()

        return True, f"Updated {framework} {current_version} → {latest_version}"

    return False, f"{framework} {current_version} is latest"
```

---

## 9. Testing Strategy

### Unit Tests

```python
# tests/unit/test_doc_fetcher.py

def test_resolve_library_id():
    """Test library ID resolution"""
    fetcher = DocFetcher()
    library_id = fetcher._resolve_library_id("Next.js")
    assert library_id == "/vercel/next.js"

def test_fetch_with_cache():
    """Test cache hit"""
    fetcher = DocFetcher()
    # First fetch (cache miss)
    docs1 = fetcher.fetch("Next.js")
    # Second fetch (cache hit)
    docs2 = fetcher.fetch("Next.js")
    assert docs1 == docs2  # Should be identical

def test_fallback_on_error():
    """Test fallback when Context7 fails"""
    with mock.patch('doc_fetcher._fetch_from_context7', side_effect=NetworkError):
        docs = fetcher.fetch("Next.js")
        # Should return cached or builtin
        assert docs is not None
```

### Integration Tests

```python
# tests/integration/test_context7_live.py

@pytest.mark.slow
def test_live_context7_fetch():
    """Test actual Context7 call (requires MCP server running)"""
    fetcher = DocFetcher()
    docs = fetcher.fetch("Next.js", topic="App Router")

    # Validate response
    assert "App Router" in docs
    assert len(docs) > 500  # Should have substantial content
    assert "Server Components" in docs  # Next.js 15 feature
```

---

## 10. Key Decisions for SkillForge

### Decision 1: When to Fetch

✅ **Generation time**: ALWAYS fetch fresh docs
✅ **Update time**: Fetch to check for new versions
❌ **Runtime**: Don't fetch (use generated skills)

**Rationale**: Generated skills should be static, not dynamic

### Decision 2: Cache Duration

✅ **7 days**: Good balance (docs don't change daily)
❌ **24 hours**: Too aggressive (unnecessary API calls)
❌ **30 days**: Too stale (miss updates)

### Decision 3: Token Budget

✅ **3000 tokens**: Optimal for skill generation
❌ **10000 tokens**: Too much (bloats context)
❌ **1000 tokens**: Too little (insufficient detail)

### Decision 4: Fallback Strategy

✅ **Multi-tier fallback**: Context7 → Cache → WebSearch → Builtin
❌ **Fail fast**: Don't fallback (blocks generation)
❌ **Single fallback**: Only cache (insufficient reliability)

---

## 11. Action Items for Implementation

**Fase 0** (Current):
- ✅ Document Context7 integration
- [ ] Test Context7 with 10+ common libraries
- [ ] Measure response times and token usage

**Fase 3** (Generation System):
- [ ] Implement DocFetcher class
- [ ] Implement caching layer
- [ ] Implement fallback chain
- [ ] Add error handling
- [ ] Write unit tests

**Fase 4** (Orchestration):
- [ ] Integrate DocFetcher with SkillGenerator
- [ ] Add topic selection logic
- [ ] Optimize token budgets

**Fase 8** (Testing):
- [ ] Integration tests with live Context7
- [ ] Cache performance tests
- [ ] Fallback scenario tests

---

## 12. References

- GitHub: https://github.com/upstash/context7
- Lobe Hub: https://lobehub.com/mcp/upstash-context7
- Tutorial: https://dev.to/mehmetakar/context7-mcp-tutorial-3he2
- User's MCP_Context7.md documentation

---

**Research Completed**: 2025-10-22
**Confidence Level**: High
**Next Step**: Validate with live testing in Week 1-2
**Status**: Ready for implementation planning

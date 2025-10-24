# GENERATOR.md - Skill Generation System

## Overview

The SkillForge generator is an intelligent system that creates customized SKILL.md files through an interactive wizard, automated documentation fetching, and template processing. It transforms user requirements into production-ready skills with comprehensive documentation and best practices.

---

## 1. Generation Pipeline

### 7-Step Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SKILL GENERATION PIPELINE                      │
└─────────────────────────────────────────────────────────────────────┘

Step 1: WIZARD INTERVIEW
┌──────────────────────┐
│  Interactive Q&A     │──→ user_requirements.json
│  - Role questions    │
│  - Tech stack        │
│  - Frameworks        │
│  - Tools & workflow  │
└──────────────────────┘
         │
         ↓
Step 2: REQUIREMENT VALIDATION
┌──────────────────────┐
│  Validate inputs     │──→ validated_requirements.json
│  - Check conflicts   │
│  - Verify versions   │
│  - Suggest additions │
└──────────────────────┘
         │
         ↓
Step 3: DOCUMENTATION FETCHING
┌──────────────────────┐
│  Context7 API        │──→ library_docs/
│  - Resolve lib IDs   │    ├── react.md
│  - Fetch docs        │    ├── nextjs.md
│  - Cache locally     │    └── ...
└──────────────────────┘
         │
         ↓
Step 4: TEMPLATE SELECTION
┌──────────────────────┐
│  Choose templates    │──→ selected_templates[]
│  - Role-based        │
│  - Framework-based   │
│  - Tool-based        │
└──────────────────────┘
         │
         ↓
Step 5: TEMPLATE PROCESSING
┌──────────────────────┐
│  Process templates   │──→ processed_content.md
│  - Variable subst.   │
│  - Conditionals      │
│  - Loops             │
│  - Doc injection     │
└──────────────────────┘
         │
         ↓
Step 6: CONTENT ASSEMBLY
┌──────────────────────┐
│  Assemble SKILL.md   │──→ draft_skill.md
│  - Frontmatter       │
│  - Core sections     │
│  - Best practices    │
│  - Examples          │
└──────────────────────┘
         │
         ↓
Step 7: POST-GENERATION VALIDATION
┌──────────────────────┐
│  Quality checks      │──→ final_skill.md
│  - Structure valid   │    + validation_report.json
│  - Links working     │
│  - Examples tested   │
│  - Completeness      │
└──────────────────────┘
```

### Input/Output Specification

**Step 1 Input:**
- User interaction via CLI
- Optional: existing project analysis

**Step 1 Output:**
```json
{
  "role": "fullstack_web_developer",
  "tech_stack": {
    "languages": ["typescript", "python"],
    "frontend": ["react", "nextjs"],
    "backend": ["fastapi", "nodejs"],
    "database": ["postgresql", "redis"],
    "tools": ["docker", "git", "vscode"]
  },
  "preferences": {
    "testing": "pytest_jest",
    "styling": "tailwindcss",
    "state_management": "zustand",
    "api_style": "rest"
  },
  "project_type": "web_application",
  "experience_level": "intermediate"
}
```

**Step 7 Output:**
```markdown
---
skill_name: "Fullstack Web Development - React & FastAPI"
version: "1.0.0"
generated_at: "2025-01-15T10:30:00Z"
...
---

# Fullstack Web Development Skill

[Complete SKILL.md content]
```

---

## 2. Wizard System

### Interactive Questionnaire Design

The wizard uses a multi-stage questionnaire that adapts based on user responses.

```python
# skillforge/generators/wizard.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    """Types of questions in the wizard"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    BOOLEAN = "boolean"
    VERSION_SELECT = "version_select"

@dataclass
class Question:
    """Represents a wizard question"""
    id: str
    category: str
    text: str
    type: QuestionType
    options: Optional[List[str]] = None
    default: Optional[Any] = None
    validation_rules: Optional[Dict] = None
    depends_on: Optional[Dict] = None  # Conditional display
    help_text: Optional[str] = None

class SkillWizard:
    """Interactive wizard for skill generation"""

    def __init__(self):
        self.questions = self._build_question_tree()
        self.answers = {}

    def _build_question_tree(self) -> List[Question]:
        """Build the complete question tree"""
        return [
            # CATEGORY: Role & Project Type
            Question(
                id="role",
                category="role",
                text="What is your primary development role?",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "Frontend Developer",
                    "Backend Developer",
                    "Fullstack Developer",
                    "DevOps Engineer",
                    "Data Scientist",
                    "Mobile Developer",
                    "ML Engineer",
                    "Custom (specify)"
                ],
                help_text="This determines the core skill template"
            ),

            Question(
                id="project_type",
                category="role",
                text="What type of projects do you work on?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Web Applications",
                    "Mobile Apps",
                    "APIs/Microservices",
                    "Data Processing",
                    "Machine Learning",
                    "DevOps/Infrastructure",
                    "Desktop Applications"
                ]
            ),

            Question(
                id="experience_level",
                category="role",
                text="What is your experience level?",
                type=QuestionType.SINGLE_CHOICE,
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                default="Intermediate",
                help_text="Affects detail level and best practices included"
            ),

            # CATEGORY: Tech Stack - Languages
            Question(
                id="primary_language",
                category="tech_stack",
                text="What is your primary programming language?",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "JavaScript/TypeScript",
                    "Python",
                    "Java",
                    "Go",
                    "Rust",
                    "C#/.NET",
                    "Ruby",
                    "PHP",
                    "Other"
                ]
            ),

            Question(
                id="additional_languages",
                category="tech_stack",
                text="What other languages do you use?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "JavaScript", "TypeScript", "Python", "Java",
                    "Go", "Rust", "C#", "Ruby", "PHP", "Kotlin",
                    "Swift", "Scala", "Elixir"
                ]
            ),

            # CATEGORY: Frameworks - Frontend
            Question(
                id="frontend_framework",
                category="frameworks",
                text="Which frontend framework(s) do you use?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "React", "Next.js", "Vue.js", "Nuxt.js",
                    "Angular", "Svelte", "SvelteKit", "Solid.js",
                    "None/Vanilla"
                ],
                depends_on={"role": ["Frontend Developer", "Fullstack Developer"]}
            ),

            Question(
                id="react_version",
                category="frameworks",
                text="Which React version?",
                type=QuestionType.VERSION_SELECT,
                options=["18.x (latest)", "17.x", "16.x"],
                default="18.x (latest)",
                depends_on={"frontend_framework": ["React"]}
            ),

            # CATEGORY: Frameworks - Backend
            Question(
                id="backend_framework",
                category="frameworks",
                text="Which backend framework(s) do you use?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Express.js", "Fastify", "NestJS", "Koa",
                    "FastAPI", "Django", "Flask", "Spring Boot",
                    "Gin", "Fiber", "Rails", "Laravel",
                    "ASP.NET Core"
                ],
                depends_on={"role": ["Backend Developer", "Fullstack Developer"]}
            ),

            # CATEGORY: Tools - Database
            Question(
                id="databases",
                category="tools",
                text="Which databases do you use?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "PostgreSQL", "MySQL", "MongoDB", "Redis",
                    "SQLite", "Elasticsearch", "DynamoDB",
                    "Cassandra", "Neo4j", "Supabase", "Firebase"
                ]
            ),

            # CATEGORY: Tools - Development
            Question(
                id="version_control",
                category="tools",
                text="Version control system?",
                type=QuestionType.SINGLE_CHOICE,
                options=["Git", "Git + GitHub", "Git + GitLab", "Git + Bitbucket"],
                default="Git + GitHub"
            ),

            Question(
                id="editor",
                category="tools",
                text="Primary code editor?",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "VS Code", "Cursor", "Neovim", "IntelliJ IDEA",
                    "PyCharm", "WebStorm", "Sublime Text", "Other"
                ],
                default="VS Code"
            ),

            Question(
                id="containerization",
                category="tools",
                text="Do you use containerization?",
                type=QuestionType.BOOLEAN,
                default=True
            ),

            Question(
                id="container_tool",
                category="tools",
                text="Which container tool?",
                type=QuestionType.SINGLE_CHOICE,
                options=["Docker", "Podman", "Docker + Kubernetes"],
                depends_on={"containerization": True}
            ),

            # CATEGORY: Workflow - Testing
            Question(
                id="testing_frameworks",
                category="workflow",
                text="Which testing frameworks do you use?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Jest", "Vitest", "Mocha", "Cypress", "Playwright",
                    "pytest", "unittest", "Robot Framework",
                    "JUnit", "TestNG", "Go testing"
                ]
            ),

            # CATEGORY: Workflow - CI/CD
            Question(
                id="cicd_platform",
                category="workflow",
                text="Which CI/CD platform?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "GitHub Actions", "GitLab CI", "CircleCI",
                    "Jenkins", "Travis CI", "Azure DevOps",
                    "None currently"
                ]
            ),

            # CATEGORY: Workflow - Styling (for frontend)
            Question(
                id="styling_approach",
                category="workflow",
                text="CSS/Styling approach?",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Tailwind CSS", "CSS Modules", "Styled Components",
                    "Emotion", "SASS/SCSS", "Plain CSS", "shadcn/ui",
                    "Material-UI", "Chakra UI"
                ],
                depends_on={"role": ["Frontend Developer", "Fullstack Developer"]}
            ),
        ]

    def run(self) -> Dict[str, Any]:
        """Run the wizard and collect answers"""
        print("╔═══════════════════════════════════════╗")
        print("║   SkillForge Skill Generator Wizard   ║")
        print("╚═══════════════════════════════════════╝\n")

        for question in self.questions:
            if self._should_ask_question(question):
                answer = self._ask_question(question)
                self.answers[question.id] = answer

        return self._process_answers()

    def _should_ask_question(self, question: Question) -> bool:
        """Check if question should be asked based on dependencies"""
        if not question.depends_on:
            return True

        for key, required_values in question.depends_on.items():
            user_answer = self.answers.get(key)

            # Handle boolean dependencies
            if isinstance(required_values, bool):
                if user_answer != required_values:
                    return False
            # Handle list dependencies
            elif isinstance(user_answer, list):
                if not any(val in user_answer for val in required_values):
                    return False
            # Handle single value dependencies
            else:
                if user_answer not in required_values:
                    return False

        return True

    def _ask_question(self, question: Question) -> Any:
        """Ask a single question and get validated answer"""
        print(f"\n[{question.category.upper()}]")
        print(f"❯ {question.text}")

        if question.help_text:
            print(f"  ℹ {question.help_text}")

        if question.type == QuestionType.SINGLE_CHOICE:
            return self._ask_single_choice(question)
        elif question.type == QuestionType.MULTIPLE_CHOICE:
            return self._ask_multiple_choice(question)
        elif question.type == QuestionType.BOOLEAN:
            return self._ask_boolean(question)
        elif question.type == QuestionType.TEXT_INPUT:
            return self._ask_text_input(question)
        elif question.type == QuestionType.VERSION_SELECT:
            return self._ask_single_choice(question)

    def _ask_single_choice(self, question: Question) -> str:
        """Ask single choice question"""
        for i, option in enumerate(question.options, 1):
            default_marker = " (default)" if option == question.default else ""
            print(f"  {i}. {option}{default_marker}")

        while True:
            response = input("\nEnter number (or press Enter for default): ").strip()

            if not response and question.default:
                return question.default

            try:
                choice_idx = int(response) - 1
                if 0 <= choice_idx < len(question.options):
                    return question.options[choice_idx]
                else:
                    print("❌ Invalid choice. Try again.")
            except ValueError:
                print("❌ Please enter a number.")

    def _ask_multiple_choice(self, question: Question) -> List[str]:
        """Ask multiple choice question"""
        for i, option in enumerate(question.options, 1):
            print(f"  {i}. {option}")

        print("\n  Enter numbers separated by commas (e.g., 1,3,5)")

        while True:
            response = input("Your choices: ").strip()

            if not response:
                print("❌ Please select at least one option.")
                continue

            try:
                indices = [int(x.strip()) - 1 for x in response.split(",")]
                choices = [question.options[i] for i in indices
                          if 0 <= i < len(question.options)]

                if choices:
                    return choices
                else:
                    print("❌ No valid choices selected.")
            except (ValueError, IndexError):
                print("❌ Invalid input. Use comma-separated numbers.")

    def _ask_boolean(self, question: Question) -> bool:
        """Ask yes/no question"""
        default_text = " [Y/n]" if question.default else " [y/N]"
        response = input(f"{default_text}: ").strip().lower()

        if not response:
            return question.default if question.default is not None else False

        return response in ['y', 'yes', 'true', '1']

    def _ask_text_input(self, question: Question) -> str:
        """Ask text input question"""
        response = input("Your answer: ").strip()

        if question.validation_rules:
            if not self._validate_input(response, question.validation_rules):
                print("❌ Invalid input. Try again.")
                return self._ask_text_input(question)

        return response

    def _validate_input(self, value: str, rules: Dict) -> bool:
        """Validate input against rules"""
        if 'min_length' in rules and len(value) < rules['min_length']:
            return False
        if 'max_length' in rules and len(value) > rules['max_length']:
            return False
        if 'pattern' in rules:
            import re
            if not re.match(rules['pattern'], value):
                return False
        return True

    def _process_answers(self) -> Dict[str, Any]:
        """Process and structure the collected answers"""
        return {
            "role": self.answers.get("role"),
            "project_type": self.answers.get("project_type"),
            "experience_level": self.answers.get("experience_level"),
            "tech_stack": {
                "primary_language": self.answers.get("primary_language"),
                "additional_languages": self.answers.get("additional_languages", []),
                "frontend": self.answers.get("frontend_framework", []),
                "backend": self.answers.get("backend_framework", []),
                "databases": self.answers.get("databases", []),
            },
            "tools": {
                "version_control": self.answers.get("version_control"),
                "editor": self.answers.get("editor"),
                "containerization": self.answers.get("containerization"),
                "container_tool": self.answers.get("container_tool"),
            },
            "workflow": {
                "testing": self.answers.get("testing_frameworks", []),
                "cicd": self.answers.get("cicd_platform", []),
                "styling": self.answers.get("styling_approach", []),
            },
            "versions": {
                "react": self.answers.get("react_version"),
            }
        }
```

---

## 3. Documentation Fetching

### Context7 Integration

The system uses Context7's MCP tools to fetch up-to-date documentation for specified libraries and frameworks.

```python
# skillforge/generators/doc_fetcher.py

from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime, timedelta

class DocumentationFetcher:
    """Fetches and caches library documentation via Context7"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(days=7)  # Cache for 7 days

    def fetch_documentation(
        self,
        libraries: List[str],
        topics: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Fetch documentation for multiple libraries

        Args:
            libraries: List of library names (e.g., ["react", "nextjs"])
            topics: Optional dict mapping library -> topic focus

        Returns:
            Dict mapping library name -> documentation content
        """
        docs = {}

        for library in libraries:
            topic = topics.get(library) if topics else None

            # Check cache first
            cached_doc = self._get_cached_doc(library, topic)
            if cached_doc:
                docs[library] = cached_doc
                continue

            # Fetch from Context7
            try:
                doc_content = self._fetch_from_context7(library, topic)
                docs[library] = doc_content

                # Cache the result
                self._cache_doc(library, topic, doc_content)

            except Exception as e:
                print(f"⚠️  Failed to fetch docs for {library}: {e}")
                # Use fallback
                docs[library] = self._get_fallback_doc(library)

        return docs

    def _fetch_from_context7(
        self,
        library: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Fetch documentation using Context7 MCP tools

        Process:
        1. Call mcp__context7__resolve-library-id to get library ID
        2. Call mcp__context7__get-library-docs with ID and optional topic
        """
        # Step 1: Resolve library ID
        library_id = self._resolve_library_id(library)

        if not library_id:
            raise ValueError(f"Could not resolve library ID for: {library}")

        # Step 2: Get documentation
        return self._get_library_docs(library_id, topic)

    def _resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve a library name to Context7-compatible ID

        This would actually call the MCP tool, but here's the logic:
        """
        # Map common names to Context7 format
        library_mappings = {
            "react": "facebook/react",
            "nextjs": "vercel/next.js",
            "next.js": "vercel/next.js",
            "vue": "vuejs/core",
            "fastapi": "tiangolo/fastapi",
            "django": "django/django",
            "express": "expressjs/express",
            "tailwind": "tailwindlabs/tailwindcss",
            "tailwindcss": "tailwindlabs/tailwindcss",
            "postgresql": "postgres/postgres",
            "mongodb": "mongodb/mongo",
        }

        # Try direct mapping first
        if library_name.lower() in library_mappings:
            return f"/{library_mappings[library_name.lower()]}"

        # Would call MCP tool here in real implementation:
        # result = mcp__context7__resolve_library_id(libraryName=library_name)
        # return result['library_id']

        return None

    def _get_library_docs(
        self,
        library_id: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Fetch library documentation

        In real implementation, would call:
        mcp__context7__get_library_docs(
            context7CompatibleLibraryID=library_id,
            topic=topic,
            tokens=5000
        )
        """
        # Placeholder - would use actual MCP tool
        return f"Documentation for {library_id}" + (f" (topic: {topic})" if topic else "")

    def _get_cached_doc(self, library: str, topic: Optional[str]) -> Optional[str]:
        """Get documentation from cache if available and fresh"""
        cache_key = self._get_cache_key(library, topic)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still fresh
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.cache_duration:
                return None

            return cache_data['content']

        except Exception:
            return None

    def _cache_doc(self, library: str, topic: Optional[str], content: str):
        """Cache documentation content"""
        cache_key = self._get_cache_key(library, topic)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            'library': library,
            'topic': topic,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def _get_cache_key(self, library: str, topic: Optional[str]) -> str:
        """Generate cache key"""
        base = library.lower().replace('/', '_').replace('.', '_')
        if topic:
            base += f"_{topic.lower().replace(' ', '_')}"
        return base

    def _get_fallback_doc(self, library: str) -> str:
        """Provide fallback documentation when fetch fails"""
        return f"""
# {library.title()} Documentation

> Note: Full documentation fetch failed. Using fallback information.

## Overview

{library} is a popular library/framework. For complete documentation, visit the official website.

## Basic Usage

```python
# Example placeholder
# Check official docs for {library}
```

## Resources

- Official Documentation: [Check official website]
- GitHub: [Search on GitHub]
"""
```

### Caching Strategy

```python
# Cache structure:
# .skillforge/
#   cache/
#     docs/
#       react.json
#       nextjs_routing.json
#       fastapi_async.json
#       ...

# Cache entry format:
{
  "library": "react",
  "topic": "hooks",
  "content": "# React Hooks Documentation\n...",
  "timestamp": "2025-01-15T10:30:00",
  "version": "18.x",
  "source": "context7"
}
```

---

## 4. Template Processing

### Template Format

Templates use Jinja2-style syntax with custom extensions for skill generation.

```markdown
<!-- templates/fullstack_web.md.j2 -->

# {{ skill_name }}

## Overview

This skill covers {{ role }} with focus on:
{% for area in focus_areas %}
- {{ area }}
{% endfor %}

## Technology Stack

### Frontend
{% if tech_stack.frontend %}
{% for framework in tech_stack.frontend %}
- **{{ framework }}**: {{ get_framework_description(framework) }}
{% endfor %}

{{ inject_docs('frontend_framework', tech_stack.frontend[0]) }}
{% else %}
- No frontend framework specified
{% endif %}

### Backend
{% if tech_stack.backend %}
{% for framework in tech_stack.backend %}
- **{{ framework }}**: {{ get_framework_description(framework) }}
{% endfor %}

{{ inject_docs('backend_framework', tech_stack.backend[0]) }}
{% endif %}

### Database
{% if tech_stack.databases %}
Databases used in this stack:
{% for db in tech_stack.databases %}
- {{ db }}
{% endfor %}
{% endif %}

## Development Workflow

### Version Control
{{ workflow.version_control }}

### Testing Strategy
{% if workflow.testing %}
Testing is implemented using:
{% for tool in workflow.testing %}
- {{ tool }}
{% endfor %}

{{ inject_best_practices('testing', workflow.testing[0]) }}
{% endif %}

### CI/CD
{% if workflow.cicd %}
Continuous Integration/Deployment using: {{ workflow.cicd | join(', ') }}
{% endif %}

## Best Practices

{{ inject_best_practices('role', role) }}

{% if experience_level == 'Advanced' or experience_level == 'Expert' %}
## Advanced Patterns

{{ inject_advanced_patterns(tech_stack) }}
{% endif %}

## Code Examples

### Full Stack Example
{% if 'React' in tech_stack.frontend and 'FastAPI' in tech_stack.backend %}
{{ inject_example('react_fastapi_integration') }}
{% elif 'Next.js' in tech_stack.frontend %}
{{ inject_example('nextjs_fullstack') }}
{% endif %}

## Troubleshooting

{{ inject_troubleshooting(tech_stack) }}

## Resources

{{ inject_resources(tech_stack, workflow) }}
```

### Template Processor

```python
# skillforge/generators/template_processor.py

from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any
from pathlib import Path

class TemplateProcessor:
    """Process templates with custom functions and filters"""

    def __init__(self, template_dir: Path, docs: Dict[str, str]):
        self.template_dir = template_dir
        self.docs = docs
        self.env = self._setup_environment()

    def _setup_environment(self) -> Environment:
        """Setup Jinja2 environment with custom functions"""
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom functions
        env.globals['inject_docs'] = self.inject_docs
        env.globals['inject_best_practices'] = self.inject_best_practices
        env.globals['inject_example'] = self.inject_example
        env.globals['inject_advanced_patterns'] = self.inject_advanced_patterns
        env.globals['inject_troubleshooting'] = self.inject_troubleshooting
        env.globals['inject_resources'] = self.inject_resources
        env.globals['get_framework_description'] = self.get_framework_description

        return env

    def process(self, template_name: str, context: Dict[str, Any]) -> str:
        """Process a template with given context"""
        template = self.env.get_template(template_name)
        return template.render(**context)

    def inject_docs(self, category: str, library: str) -> str:
        """Inject documentation from fetched docs"""
        doc_key = library.lower().replace(' ', '_').replace('.', '_')

        if doc_key in self.docs:
            return f"\n### {library} Documentation\n\n{self.docs[doc_key]}\n"

        return f"\n> Documentation for {library} not available\n"

    def inject_best_practices(self, category: str, technology: str) -> str:
        """Inject best practices for technology"""
        practices = {
            'testing': {
                'pytest': """
### Testing Best Practices

1. **Test Organization**: Group tests by feature/module
2. **Fixtures**: Use fixtures for common setup
3. **Parametrize**: Test multiple cases with @pytest.mark.parametrize
4. **Coverage**: Aim for 80%+ coverage on critical paths
5. **Mock External Dependencies**: Use pytest-mock for external services
""",
                'jest': """
### Testing Best Practices

1. **Test Organization**: Co-locate tests with components
2. **Test Utils**: Create custom render functions with providers
3. **Async Testing**: Use waitFor and findBy queries
4. **Coverage**: Aim for 80%+ coverage on components
5. **Mock API Calls**: Use MSW (Mock Service Worker)
"""
            },
            'role': {
                'Fullstack Developer': """
### Fullstack Development Best Practices

1. **API Design**: RESTful conventions or GraphQL schema-first
2. **Type Safety**: Share types between frontend and backend
3. **Error Handling**: Consistent error responses and client handling
4. **Authentication**: Secure token management (HttpOnly cookies)
5. **State Management**: Server state vs client state separation
6. **Performance**: Optimize database queries and implement caching
"""
            }
        }

        return practices.get(category, {}).get(technology, "")

    def inject_example(self, example_type: str) -> str:
        """Inject code examples"""
        examples = {
            'react_fastapi_integration': """
```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  async getUsers() {
    const response = await apiClient.get('/users');
    return response.data;
  },

  async createUser(userData: UserCreate) {
    const response = await apiClient.post('/users', userData);
    return response.data;
  },
};
```

```python
# backend/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/users")
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```
""",
            'nextjs_fullstack': """
```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  const users = await prisma.user.findMany();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const body = await request.json();
  const user = await prisma.user.create({
    data: body,
  });
  return NextResponse.json(user);
}
```

```typescript
// app/users/page.tsx
'use client';

import { useEffect, useState } from 'react';

export default function UsersPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(setUsers);
  }, []);

  return (
    <div>
      <h1>Users</h1>
      {users.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  );
}
```
"""
        }

        return examples.get(example_type, "")

    def inject_advanced_patterns(self, tech_stack: Dict) -> str:
        """Inject advanced patterns based on tech stack"""
        return """
### Advanced Architecture Patterns

1. **Clean Architecture**: Separate concerns (domain, application, infrastructure)
2. **Repository Pattern**: Abstract data access layer
3. **Factory Pattern**: Create complex objects
4. **Observer Pattern**: Event-driven updates
5. **Strategy Pattern**: Interchangeable algorithms
"""

    def inject_troubleshooting(self, tech_stack: Dict) -> str:
        """Inject common troubleshooting scenarios"""
        return """
### Common Issues

#### CORS Errors
- Ensure backend CORS middleware is configured correctly
- Check that frontend URL is in allowed origins

#### Authentication Issues
- Verify token storage (localStorage vs cookies)
- Check token expiration handling
- Ensure auth headers are sent with requests

#### Database Connection
- Verify connection string
- Check database server is running
- Ensure proper migrations are applied
"""

    def inject_resources(self, tech_stack: Dict, workflow: Dict) -> str:
        """Generate resource links"""
        resources = []

        # Add resources based on tech stack
        if 'React' in tech_stack.get('frontend', []):
            resources.append("- [React Documentation](https://react.dev)")

        if 'Next.js' in tech_stack.get('frontend', []):
            resources.append("- [Next.js Documentation](https://nextjs.org/docs)")

        if 'FastAPI' in tech_stack.get('backend', []):
            resources.append("- [FastAPI Documentation](https://fastapi.tiangolo.com)")

        return '\n'.join(resources)

    def get_framework_description(self, framework: str) -> str:
        """Get brief framework description"""
        descriptions = {
            'React': 'A JavaScript library for building user interfaces',
            'Next.js': 'The React framework for production',
            'FastAPI': 'Modern, fast web framework for building APIs with Python',
            'Django': 'High-level Python web framework',
            'Express.js': 'Minimal and flexible Node.js web framework',
            'PostgreSQL': 'Powerful, open source object-relational database',
            'MongoDB': 'Document-oriented NoSQL database',
        }

        return descriptions.get(framework, 'Popular framework/library')
```

---

## 5. SKILL.md Generation

### Required Sections

Every generated SKILL.md must include:

1. YAML Frontmatter
2. Overview
3. Technology Stack
4. Development Workflow
5. Best Practices
6. Code Examples
7. Troubleshooting
8. Resources

### YAML Frontmatter Generation

```python
# skillforge/generators/frontmatter.py

from typing import Dict, Any
from datetime import datetime
import yaml

def generate_frontmatter(context: Dict[str, Any]) -> str:
    """Generate YAML frontmatter for SKILL.md"""

    # Generate skill name
    role = context['role']
    primary_tech = context['tech_stack']['frontend'][0] if context['tech_stack'].get('frontend') else \
                   context['tech_stack']['backend'][0] if context['tech_stack'].get('backend') else \
                   context['tech_stack']['primary_language']

    skill_name = f"{role} - {primary_tech}"

    # Build tags
    tags = ['generated']
    tags.append(role.lower().replace(' ', '_'))
    tags.extend([t.lower().replace(' ', '_') for t in context['tech_stack'].get('frontend', [])])
    tags.extend([t.lower().replace(' ', '_') for t in context['tech_stack'].get('backend', [])])

    frontmatter = {
        'skill_name': skill_name,
        'version': '1.0.0',
        'generated_at': datetime.now().isoformat(),
        'role': role,
        'experience_level': context.get('experience_level', 'Intermediate'),
        'tech_stack': {
            'primary_language': context['tech_stack']['primary_language'],
            'frameworks': (context['tech_stack'].get('frontend', []) +
                         context['tech_stack'].get('backend', [])),
            'databases': context['tech_stack'].get('databases', []),
            'tools': list(context.get('tools', {}).values()),
        },
        'tags': tags,
        'auto_generated': True,
        'customizable': True,
    }

    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n"
```

### Complete Generation Example

```python
# skillforge/generators/skill_generator.py

from pathlib import Path
from typing import Dict, Any
import json

class SkillGenerator:
    """Main skill generator orchestrator"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.template_dir = Path(__file__).parent.parent / 'templates'
        self.cache_dir = Path.home() / '.skillforge' / 'cache' / 'docs'

    def generate(self, requirements: Dict[str, Any]) -> Path:
        """
        Generate a SKILL.md file from requirements

        Returns: Path to generated SKILL.md
        """
        print("🔧 Starting skill generation...")

        # 1. Validate requirements
        print("  ✓ Validating requirements...")
        validated = self._validate_requirements(requirements)

        # 2. Fetch documentation
        print("  ✓ Fetching library documentation...")
        libraries = self._extract_libraries(validated)
        doc_fetcher = DocumentationFetcher(self.cache_dir)
        docs = doc_fetcher.fetch_documentation(libraries)

        # 3. Select template
        print("  ✓ Selecting template...")
        template_name = self._select_template(validated)

        # 4. Process template
        print("  ✓ Processing template...")
        processor = TemplateProcessor(self.template_dir, docs)

        # Build context
        context = {
            **validated,
            'skill_name': self._generate_skill_name(validated),
            'focus_areas': self._determine_focus_areas(validated),
        }

        content = processor.process(template_name, context)

        # 5. Add frontmatter
        print("  ✓ Generating frontmatter...")
        frontmatter = generate_frontmatter(context)
        full_content = frontmatter + "\n" + content

        # 6. Write file
        output_file = self.output_dir / 'SKILL.md'
        output_file.write_text(full_content)

        print(f"✅ Generated: {output_file}")

        # 7. Validate generated file
        print("  ✓ Validating generated skill...")
        validation_result = self._validate_generated_skill(output_file)

        if validation_result['valid']:
            print("✅ Validation passed!")
        else:
            print("⚠️  Validation warnings:")
            for warning in validation_result['warnings']:
                print(f"    - {warning}")

        return output_file

    def _validate_requirements(self, requirements: Dict) -> Dict:
        """Validate and enhance requirements"""
        # Add validation logic
        return requirements

    def _extract_libraries(self, requirements: Dict) -> list:
        """Extract all libraries that need documentation"""
        libraries = []

        if 'frontend' in requirements['tech_stack']:
            libraries.extend(requirements['tech_stack']['frontend'])

        if 'backend' in requirements['tech_stack']:
            libraries.extend(requirements['tech_stack']['backend'])

        return libraries

    def _select_template(self, requirements: Dict) -> str:
        """Select appropriate template based on role"""
        role_templates = {
            'Frontend Developer': 'frontend_web.md.j2',
            'Backend Developer': 'backend_api.md.j2',
            'Fullstack Developer': 'fullstack_web.md.j2',
            'DevOps Engineer': 'devops.md.j2',
            'Data Scientist': 'data_science.md.j2',
        }

        return role_templates.get(
            requirements['role'],
            'generic.md.j2'
        )

    def _generate_skill_name(self, requirements: Dict) -> str:
        """Generate descriptive skill name"""
        role = requirements['role']
        tech = requirements['tech_stack']

        primary_tech = (tech.get('frontend', [None])[0] or
                       tech.get('backend', [None])[0] or
                       tech.get('primary_language'))

        return f"{role} - {primary_tech}"

    def _determine_focus_areas(self, requirements: Dict) -> list:
        """Determine key focus areas"""
        areas = []

        if requirements['tech_stack'].get('frontend'):
            areas.append("Frontend Development")

        if requirements['tech_stack'].get('backend'):
            areas.append("Backend Development")

        if requirements['workflow'].get('testing'):
            areas.append("Testing & Quality Assurance")

        if requirements['workflow'].get('cicd'):
            areas.append("CI/CD & DevOps")

        return areas

    def _validate_generated_skill(self, skill_file: Path) -> Dict:
        """Validate generated skill file"""
        from .validator import SkillValidator

        validator = SkillValidator()
        return validator.validate(skill_file)
```

---

## 6. Supporting Files

### Directory Structure

```
skillforge/
├── generators/
│   ├── __init__.py
│   ├── wizard.py              # Interactive wizard
│   ├── doc_fetcher.py         # Documentation fetching
│   ├── template_processor.py # Template processing
│   ├── skill_generator.py     # Main generator
│   ├── frontmatter.py         # Frontmatter generation
│   └── validator.py           # Validation logic
├── templates/
│   ├── frontend_web.md.j2
│   ├── backend_api.md.j2
│   ├── fullstack_web.md.j2
│   ├── devops.md.j2
│   ├── data_science.md.j2
│   ├── mobile.md.j2
│   └── generic.md.j2
├── scripts/
│   ├── generate_skill.py      # CLI entry point
│   └── validate_skill.py      # Standalone validator
└── data/
    ├── best_practices/
    │   ├── testing.json
    │   ├── security.json
    │   └── performance.json
    └── examples/
        ├── react_fastapi.md
        ├── nextjs_fullstack.md
        └── django_vue.md
```

---

## 7. Validation System

### Pre-Generation Validation

```python
# skillforge/generators/validator.py

from typing import Dict, List, Any
from pathlib import Path
import yaml
import re

class RequirementsValidator:
    """Validate requirements before generation"""

    def validate(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate requirements and return result

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'suggestions': List[str]
            }
        """
        errors = []
        warnings = []
        suggestions = []

        # Check required fields
        required_fields = ['role', 'tech_stack']
        for field in required_fields:
            if field not in requirements:
                errors.append(f"Missing required field: {field}")

        # Validate tech stack
        tech_stack = requirements.get('tech_stack', {})

        # Check for conflicting frameworks
        frontend = tech_stack.get('frontend', [])
        if len(frontend) > 3:
            warnings.append(
                f"Many frontend frameworks selected ({len(frontend)}). "
                "Consider focusing on 1-2 main frameworks."
            )

        # Check for missing testing tools
        if not requirements.get('workflow', {}).get('testing'):
            suggestions.append(
                "No testing framework specified. Consider adding pytest, jest, or similar."
            )

        # Check for missing CI/CD
        if not requirements.get('workflow', {}).get('cicd'):
            suggestions.append(
                "No CI/CD platform specified. Consider GitHub Actions, GitLab CI, etc."
            )

        # Validate compatibility
        if 'React' in frontend and 'Vue.js' in frontend:
            warnings.append(
                "Both React and Vue.js selected. These are typically not used together."
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
```

### Post-Generation Validation

```python
class SkillValidator:
    """Validate generated SKILL.md files"""

    REQUIRED_SECTIONS = [
        'Overview',
        'Technology Stack',
        'Development Workflow',
        'Best Practices',
        'Code Examples',
        'Resources'
    ]

    def validate(self, skill_file: Path) -> Dict[str, Any]:
        """
        Validate a generated SKILL.md file

        Returns validation result with details
        """
        content = skill_file.read_text()

        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }

        # 1. Check frontmatter
        frontmatter_check = self._check_frontmatter(content)
        results['checks']['frontmatter'] = frontmatter_check
        if not frontmatter_check['valid']:
            results['valid'] = False
            results['errors'].extend(frontmatter_check['errors'])

        # 2. Check required sections
        sections_check = self._check_sections(content)
        results['checks']['sections'] = sections_check
        if not sections_check['valid']:
            results['warnings'].extend(sections_check['warnings'])

        # 3. Check links
        links_check = self._check_links(content)
        results['checks']['links'] = links_check
        results['warnings'].extend(links_check['warnings'])

        # 4. Check code blocks
        code_check = self._check_code_blocks(content)
        results['checks']['code_blocks'] = code_check

        # 5. Check for placeholders
        placeholder_check = self._check_placeholders(content)
        results['checks']['placeholders'] = placeholder_check
        if not placeholder_check['valid']:
            results['warnings'].extend(placeholder_check['warnings'])

        return results

    def _check_frontmatter(self, content: str) -> Dict:
        """Check YAML frontmatter validity"""
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)

        if not match:
            return {
                'valid': False,
                'errors': ['No YAML frontmatter found']
            }

        try:
            frontmatter = yaml.safe_load(match.group(1))

            required_keys = ['skill_name', 'version', 'role']
            missing = [key for key in required_keys if key not in frontmatter]

            if missing:
                return {
                    'valid': False,
                    'errors': [f'Missing frontmatter keys: {", ".join(missing)}']
                }

            return {'valid': True, 'frontmatter': frontmatter}

        except yaml.YAMLError as e:
            return {
                'valid': False,
                'errors': [f'Invalid YAML: {e}']
            }

    def _check_sections(self, content: str) -> Dict:
        """Check for required sections"""
        warnings = []

        for section in self.REQUIRED_SECTIONS:
            # Look for h2 or h3 headers
            pattern = rf'^##+ {re.escape(section)}'
            if not re.search(pattern, content, re.MULTILINE):
                warnings.append(f'Missing section: {section}')

        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }

    def _check_links(self, content: str) -> Dict:
        """Check markdown links"""
        warnings = []

        # Find all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)

        for text, url in links:
            # Check for placeholder URLs
            if url in ['#', 'TODO', 'PLACEHOLDER']:
                warnings.append(f'Placeholder link: [{text}]({url})')

        return {'warnings': warnings}

    def _check_code_blocks(self, content: str) -> Dict:
        """Check code blocks for common issues"""
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)

        return {
            'count': len(code_blocks),
            'languages': list(set(lang for lang, _ in code_blocks if lang))
        }

    def _check_placeholders(self, content: str) -> Dict:
        """Check for unreplaced placeholders"""
        warnings = []

        # Common placeholder patterns
        patterns = [
            r'\{\{.*?\}\}',  # {{ variable }}
            r'\[TODO.*?\]',  # [TODO: ...]
            r'PLACEHOLDER',  # PLACEHOLDER text
            r'YOUR_.*?_HERE'  # YOUR_VALUE_HERE
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                warnings.append(
                    f'Found {len(matches)} placeholder(s): {pattern}'
                )

        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }
```

### Testing Generated Skills

```python
# scripts/test_generated_skill.py

import subprocess
from pathlib import Path

def test_skill_usability(skill_file: Path):
    """Test if generated skill can be used"""

    print(f"Testing skill: {skill_file}")

    # Test 1: Can skillforge load it?
    result = subprocess.run(
        ['python', '-m', 'skillforge', 'validate', str(skill_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Skill validation failed:\n{result.stderr}")
        return False

    print("✅ Skill validation passed")

    # Test 2: Check if it can be activated
    result = subprocess.run(
        ['python', '-m', 'skillforge', 'activate', '--dry-run', str(skill_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Skill activation test failed:\n{result.stderr}")
        return False

    print("✅ Skill activation test passed")

    return True
```

---

## 8. Version Management

### Versioning Strategy

Generated skills follow semantic versioning:

- **Major (1.x.x)**: Breaking changes (structure, required fields)
- **Minor (x.1.x)**: New sections, enhanced features
- **Patch (x.x.1)**: Bug fixes, doc updates

```python
# skillforge/generators/versioning.py

from typing import Dict
import re
from packaging import version as pkg_version

class SkillVersionManager:
    """Manage skill versions and updates"""

    def __init__(self):
        self.current_generator_version = "1.0.0"

    def detect_version(self, skill_content: str) -> str:
        """Detect version from skill frontmatter"""
        match = re.search(r'version:\s*["\']?([0-9.]+)["\']?', skill_content)
        if match:
            return match.group(1)
        return "0.0.0"

    def needs_update(self, skill_file: Path) -> bool:
        """Check if skill needs updating"""
        content = skill_file.read_text()
        current_version = self.detect_version(content)

        return pkg_version.parse(current_version) < \
               pkg_version.parse(self.current_generator_version)

    def suggest_update(self, skill_file: Path) -> Dict:
        """Suggest updates for outdated skill"""
        content = skill_file.read_text()
        current_version = self.detect_version(content)

        suggestions = []

        # Check for new sections
        if pkg_version.parse(current_version) < pkg_version.parse("1.1.0"):
            suggestions.append({
                'type': 'new_section',
                'section': 'Performance Optimization',
                'reason': 'Added in v1.1.0'
            })

        # Check for deprecated patterns
        if 'OLD_PATTERN' in content:
            suggestions.append({
                'type': 'deprecation',
                'pattern': 'OLD_PATTERN',
                'replacement': 'NEW_PATTERN'
            })

        return {
            'current_version': current_version,
            'latest_version': self.current_generator_version,
            'needs_update': len(suggestions) > 0,
            'suggestions': suggestions
        }

    def migrate(self, skill_file: Path) -> Path:
        """Migrate skill to latest version"""
        # Implementation for migrating old skills
        pass
```

### Update Detection

```bash
# CLI command to check for updates
$ skillforge check-updates

Checking for skill updates...
✓ SKILL.md (v1.0.0) - Up to date
⚠ frontend_skill.md (v0.9.0) - Update available (v1.0.0)

  Suggested changes:
  - Add "Performance Optimization" section
  - Update React examples to v18 syntax

  Run: skillforge migrate frontend_skill.md
```

---

## Usage Example

### Complete Generation Flow

```python
#!/usr/bin/env python3
# scripts/generate_skill.py

from pathlib import Path
from skillforge.generators.wizard import SkillWizard
from skillforge.generators.skill_generator import SkillGenerator

def main():
    """Main entry point for skill generation"""

    # 1. Run wizard
    wizard = SkillWizard()
    requirements = wizard.run()

    # 2. Confirm generation
    print("\n" + "="*50)
    print("GENERATION SUMMARY")
    print("="*50)
    print(f"Role: {requirements['role']}")
    print(f"Tech Stack: {requirements['tech_stack']}")
    print(f"Workflow: {requirements['workflow']}")

    confirm = input("\nGenerate skill with these settings? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("❌ Generation cancelled")
        return

    # 3. Generate skill
    output_dir = Path.cwd()
    generator = SkillGenerator(output_dir)

    skill_file = generator.generate(requirements)

    print("\n" + "="*50)
    print(f"✅ Skill generated successfully!")
    print(f"📄 Location: {skill_file}")
    print("="*50)

    # 4. Next steps
    print("\nNext steps:")
    print(f"  1. Review and customize: {skill_file}")
    print(f"  2. Activate skill: skillforge activate {skill_file}")
    print(f"  3. Test with Claude Code")

if __name__ == '__main__':
    main()
```

### Generated Output Example

```markdown
---
skill_name: "Fullstack Developer - React & FastAPI"
version: "1.0.0"
generated_at: "2025-01-15T10:30:00Z"
role: "Fullstack Developer"
experience_level: "Intermediate"
tech_stack:
  primary_language: "TypeScript"
  frameworks:
    - "React"
    - "Next.js"
    - "FastAPI"
  databases:
    - "PostgreSQL"
    - "Redis"
  tools:
    - "Git + GitHub"
    - "VS Code"
    - "Docker"
tags:
  - generated
  - fullstack_developer
  - react
  - nextjs
  - fastapi
auto_generated: true
customizable: true
---

# Fullstack Developer - React & FastAPI

## Overview

This skill covers Fullstack Developer with focus on:
- Frontend Development
- Backend Development
- Testing & Quality Assurance
- CI/CD & DevOps

[... rest of generated content ...]
```

---

## Technical Implementation Notes

### Performance Considerations

1. **Caching**: Documentation is cached for 7 days to minimize API calls
2. **Async Fetching**: Multiple libraries fetched concurrently
3. **Template Compilation**: Templates compiled once and reused
4. **Incremental Generation**: Only regenerate changed sections

### Error Handling

1. **Graceful Fallbacks**: Use local docs if Context7 fails
2. **Validation Warnings**: Non-blocking warnings for suggestions
3. **Rollback Support**: Keep previous version on update failures
4. **Detailed Logging**: Track generation steps for debugging

### Extensibility

1. **Plugin System**: Custom template functions can be registered
2. **Custom Templates**: Users can add their own templates
3. **Best Practices DB**: JSON files for easy updates
4. **Hook Points**: Pre/post generation hooks for customization

---

## Conclusion

The SkillForge generator provides a comprehensive, automated system for creating high-quality, customized SKILL.md files. Through its 7-step pipeline, interactive wizard, documentation fetching, and robust validation, it ensures that generated skills are production-ready and follow best practices while remaining fully customizable by users.

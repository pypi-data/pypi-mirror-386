# WizardEngine Documentation

## Overview

The `WizardEngine` is an interactive CLI wizard that guides users through SkillForge setup and configuration. It automatically detects technologies from project files and asks targeted questions to build a comprehensive user profile.

## Features

### 1. **Auto-Detection**
Scans project files to detect technologies:
- **package.json** - JavaScript/TypeScript projects
- **requirements.txt** - Python projects
- **go.mod** - Go projects
- **composer.json** - PHP projects

Detected technologies:
- Frontend frameworks (React, Vue, Angular, Svelte, Next.js, Nuxt.js)
- UI libraries (Material-UI, Tailwind, Chakra, Bootstrap, etc.)
- State management (Redux, Zustand, Recoil, MobX, Pinia)
- Backend frameworks (Express, NestJS, Django, FastAPI, Laravel, etc.)
- Databases (PostgreSQL, MySQL, MongoDB, Redis, etc.)
- Auth providers (NextAuth, Auth0, Clerk, Supabase Auth)
- Testing tools (Jest, Vitest, Playwright, Cypress, pytest)
- Build tools (Vite, Webpack, Turbopack, esbuild)

### 2. **Smart Question Flow**
- **12 comprehensive questions** covering:
  - Developer role
  - Frontend & backend preferences
  - Testing & deployment
  - Code style & workflow

- **Conditional logic**: Questions adapt based on previous answers
- **Skip logic**: Auto-detected technologies can be confirmed with Enter
- **Navigation**: Go back to previous questions

### 3. **Session Management**
- **Auto-save**: Progress saved after each question
- **Resume capability**: Continue from where you left off
- **Graceful interruption**: Ctrl+C saves progress automatically

### 4. **Rich Output**
- Colorful terminal interface with emojis
- Progress indicators
- Technology summary
- Next steps suggestions

## Usage

### Basic Usage

```python
from skillforge.generators import WizardEngine

# Create wizard instance
wizard = WizardEngine()

# Run interactive wizard
profile = wizard.run()

# Profile is automatically saved to:
# ~/.claude/skills/skillforge/data/user_profile.json
```

### Custom Directory

```python
from pathlib import Path
from skillforge.generators import WizardEngine

# Specify custom project directory for detection
wizard = WizardEngine(current_dir=Path("/path/to/project"))
profile = wizard.run()
```

### Detection Only

```python
from skillforge.generators import WizardEngine

wizard = WizardEngine()

# Just detect technologies
detected = wizard.detect_stack()

# Show detected technologies
wizard.show_detected()

# Access detected data
for category, technologies in detected.items():
    print(f"{category}: {technologies}")
```

## Architecture

### Class Structure

```
WizardEngine
├── __init__(current_dir)           # Initialize wizard
├── run()                            # Main entry point
├── detect_stack()                   # Auto-detect technologies
├── ask_question(question, detected) # Interactive Q&A
├── validate_answer(input, options)  # Input validation
├── save_profile()                   # Persist to disk
├── show_summary()                   # Display results
└── show_detected()                  # Show detected tech
```

### Data Flow

```
1. Initialize
   ↓
2. Load saved session (if exists)
   ↓
3. Detect tech stack from files
   ↓
4. Show detected technologies
   ↓
5. Ask questions (with skip/back logic)
   ↓
6. Build profile structure
   ↓
7. Save profile to disk
   ↓
8. Show summary & suggestions
   ↓
9. Clear session
```

## Profile Structure

Generated profile saved to `~/.claude/skills/skillforge/data/user_profile.json`:

```json
{
  "setup_completed": true,
  "role": "Full-Stack Developer",
  "frontend_framework": "Next.js",
  "ui_library": ["Tailwind CSS", "Material-UI (MUI)"],
  "state_management": ["Zustand"],
  "backend_framework": "Express.js (Node)",
  "database": ["PostgreSQL", "Redis"],
  "auth_provider": ["NextAuth.js"],
  "testing_tools": ["Jest", "Playwright"],
  "build_tools": ["Vite", "tsc (TypeScript)"],
  "deployment_platform": ["Vercel"],
  "code_style": ["TypeScript strict mode", "ESLint + Prettier"],
  "workflow_preferences": ["Git hooks (Husky)", "Conventional commits"],
  "tech_stack": {
    "frontend": "Next.js",
    "ui": ["Tailwind CSS", "Material-UI (MUI)"],
    "state": ["Zustand"],
    "backend": "Express.js (Node)",
    "database": ["PostgreSQL", "Redis"],
    "auth": ["NextAuth.js"],
    "testing": ["Jest", "Playwright"],
    "build": ["Vite", "tsc (TypeScript)"]
  },
  "preferences": {
    "role": "Full-Stack Developer",
    "deployment": ["Vercel"],
    "code_style": ["TypeScript strict mode", "ESLint + Prettier"],
    "workflow": ["Git hooks (Husky)", "Conventional commits"]
  },
  "conventions": {
    "typescript": true,
    "linting": true,
    "formatting": true,
    "paradigm": []
  }
}
```

## Question Reference

### 1. Role (👤)
**Options**: Full-Stack, Frontend, Backend, DevOps, Mobile, Data Engineer

### 2. Frontend Framework (⚛️)
**Options**: React, Vue.js, Angular, Svelte, Next.js, Nuxt.js, Vanilla JS, None
**Detectable**: Yes (package.json)
**Skip if**: Role is Backend Developer

### 3. UI Library (🎨)
**Options**: Material-UI, Ant Design, Chakra UI, Tailwind, Bootstrap, Styled Components, CSS Modules, None
**Detectable**: Yes (package.json)
**Multiple**: Yes
**Skip if**: Frontend framework is "None"

### 4. State Management (🔄)
**Options**: Redux, Redux Toolkit, Zustand, Recoil, MobX, Context API, Pinia, None
**Detectable**: Yes (package.json)
**Multiple**: Yes
**Skip if**: Frontend framework is "None"

### 5. Backend Framework (🔧)
**Options**: Express.js, Fastify, NestJS, Django, FastAPI, Flask, Rails, Laravel, Spring Boot, Go, None
**Detectable**: Yes (package.json, requirements.txt, go.mod, composer.json)
**Skip if**: Role is Frontend Developer

### 6. Database (💾)
**Options**: PostgreSQL, MySQL, MongoDB, Redis, SQLite, DynamoDB, Firestore, Supabase, PlanetScale, None
**Detectable**: Yes
**Multiple**: Yes

### 7. Auth Provider (🔐)
**Options**: NextAuth.js, Auth0, Clerk, Supabase Auth, Firebase Auth, JWT, Passport.js, OAuth2, None
**Detectable**: Yes
**Multiple**: Yes

### 8. Testing Tools (🧪)
**Options**: Jest, Vitest, Playwright, Cypress, Testing Library, pytest, unittest, Mocha/Chai, None
**Detectable**: Yes
**Multiple**: Yes

### 9. Build Tools (🏗️)
**Options**: Vite, Webpack, Turbopack, esbuild, Rollup, Parcel, tsc, Babel, None
**Detectable**: Yes (package.json)
**Multiple**: Yes

### 10. Deployment Platform (🚀)
**Options**: Vercel, Netlify, AWS, Google Cloud, Azure, Heroku, Railway, Render, DigitalOcean, Self-hosted
**Multiple**: Yes

### 11. Code Style (✨)
**Options**: TypeScript strict, ESLint+Prettier, Airbnb, Standard.js, Google, Black, Functional, OOP, Flexible
**Detectable**: Yes (linting tools)
**Multiple**: Yes

### 12. Workflow Preferences (⚙️)
**Options**: Git hooks, Pre-commit linting, Conventional commits, CI/CD, Code review automation, Automated testing, Docs generation, Performance monitoring
**Detectable**: Partial (husky)
**Multiple**: Yes

## Interactive Commands

During the wizard, users can:
- **Enter number(s)**: Select option(s)
- **Press Enter**: Accept auto-detected values
- **Type 'b'**: Go back to previous question
- **Type 's'**: Skip current question
- **Type 'q'**: Quit and save progress
- **Ctrl+C**: Save and exit

## Error Handling

### Invalid Input
```
❌ Invalid input. Please try again.
```
The wizard validates:
- Numeric input within valid range
- Proper format for multiple selections
- Non-empty required fields

### File System Errors
```python
try:
    wizard.save_profile()
except OSError as e:
    print(f"Failed to save profile: {e}")
```

### Interrupted Session
```
⚠️  Wizard interrupted!
💾 Saving your progress...
✅ Progress saved. Run the wizard again to resume.
```

## Testing

### Run Demo Tests
```bash
python3 test_wizard_demo.py
```

Tests include:
- Detection from package.json
- Input validation (single & multiple)
- Profile building logic
- Tech stack categorization

### Example Test
```python
from skillforge.generators import WizardEngine

wizard = WizardEngine()

# Test validation
result = wizard.validate_answer(
    "1,2,3",
    ["React", "Vue", "Angular"],
    allow_multiple=True
)
assert result == ["React", "Vue", "Angular"]
```

## Advanced Usage

### Extend Detection Patterns

Add new technologies to `TECH_PATTERNS`:

```python
TECH_PATTERNS = {
    "package.json": {
        "new-library": ["New Library Name"]
    }
}
```

### Add Custom Questions

Extend `QUESTIONS` list:

```python
QUESTIONS.append({
    "id": "custom_question",
    "question": "Your question?",
    "emoji": "🔥",
    "options": ["Option 1", "Option 2"],
    "allow_multiple": False,
    "detect_from": ["package.json"]
})
```

### Custom Profile Processing

```python
class CustomWizard(WizardEngine):
    def _build_tech_stack(self):
        # Custom logic
        stack = super()._build_tech_stack()
        stack['custom_field'] = self.profile.get('custom_question')
        return stack
```

## Logging

The wizard uses Python's logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

wizard = WizardEngine()
wizard.run()  # Will show debug information
```

## Files

| File | Purpose |
|------|---------|
| `wizard_engine.py` | Main wizard implementation (956 lines) |
| `~/.claude/skills/skillforge/data/user_profile.json` | Saved user profile |
| `~/.claude/skills/skillforge/data/wizard_session.json` | Temporary session state (for resume) |

## Dependencies

- Python 3.8+
- `skillforge.generators.config.Config` - Configuration management
- Standard library: `json`, `logging`, `pathlib`, `signal`, `sys`, `re`, `typing`

## Performance

- Detection: < 100ms for typical projects
- Question flow: Real-time user interaction
- Profile save: < 10ms
- Memory usage: ~5MB

## Future Enhancements

Planned features:
- [ ] More tech stack detections (Docker, Kubernetes, etc.)
- [ ] Machine learning from usage patterns
- [ ] Cloud integration detection
- [ ] Monorepo support
- [ ] Team sharing profiles
- [ ] Import from existing configs

## See Also

- [Config Documentation](./config.md)
- [Skill Generation Guide](./skill-generation.md)
- [SkillForge Architecture](./architecture.md)

# ❓ Frequently Asked Questions

**Common questions about SkillForge**

---

## General Questions

### What is SkillForge?

SkillForge is a meta-programming framework that extends Claude Code with personalized skills tailored to YOUR tech stack and coding conventions.

### Is SkillForge free?

Yes! SkillForge is open-source under the MIT license and completely free to use.

### Do I need Claude Code?

Yes. SkillForge is specifically designed to work with Claude Code's native skill system.

### Where is my data stored?

All data is stored locally on your machine in `~/.claude/skills/skillforge/`. Nothing is sent to external servers except when fetching public documentation via Context7.

---

## Installation & Setup

### How do I install SkillForge?

```bash
# Install package
pipx install skillforge

# Initialize
skillforge install

# Run setup wizard in Claude Code
/sf:wizard
```

### Do I need to run the wizard for each project?

No! Run the wizard once to set up YOUR preferences. These preferences are global and apply to all projects.

### Can I use SkillForge with different tech stacks?

Yes! Generate additional skills as needed:
```bash
/sf:generate vue-spa
/sf:generate python-fastapi
```

Your personal conventions (naming, imports, etc.) are applied to every skill.

---

## Usage Questions

### Does SkillForge slow down Claude Code?

No. Orchestration happens in milliseconds, and intelligent token optimization ensures optimal performance.

### How much disk space does SkillForge use?

Approximately 50-100MB depending on how many skills you generate.

### Can I modify generated skills?

Yes! Generated skills are standard SKILL.md files you can edit manually. However, be aware that `/sf:optimize` or `/sf:update` may overwrite changes.

### Can I share skills with my team?

Yes! You can export your profile and skills, and team members can import them. Team collaboration features are planned for v1.1.

---

## Pattern Learning

### How does pattern learning work?

SkillForge tracks your usage across all projects. When a pattern appears consistently with 80%+ confidence (typically after 10+ samples), it's automatically applied to your skills.

### Can I disable pattern learning?

Yes:
```bash
/sf:config set learning.enabled false
```

### How do I review learned patterns before they're applied?

```bash
/sf:analyze --patterns
/sf:introspect --learning
```

### Can I reject a learned pattern?

Yes. Before a pattern is applied, you're notified. You can reject it or opt-out of specific patterns.

---

## Skills & Generation

### What skill types are available?

25+ skill types including:
- Frontend: nextjs-fullstack, react-spa, vue-app, svelte-app
- Backend: fastapi-api, django-api, express-api, nestjs-api
- Integrations: supabase-integration, firebase-integration, mongodb-integration
- Workflow: git-workflow, testing-suite, deployment-pipeline

See full list: `/sf:generate` (without arguments)

### How often are skills updated?

Skills are generated with current documentation. You can update manually:
```bash
/sf:update nextjs-fullstack
/sf:update --all
```

### Can I create custom skills?

Yes! See [Templates Guide](TEMPLATES.md) for creating custom templates.

---

## Optimization

### When should I run /sf:optimize?

Run monthly or when `/sf:analyze` suggests optimizations. SkillForge will identify:
- Redundant skills to merge
- Outdated documentation
- Token optimization opportunities

### Will optimization delete my skills?

No. Optimization creates backups before any changes and requires confirmation for destructive operations.

---

## Troubleshooting

### "skillforge: command not found"

```bash
# Add pipx bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or reinstall
pip install --user skillforge
```

### Claude Code doesn't load my skills

```bash
# Verify installation
ls ~/.claude/skills/

# Restart Claude completely
killall claude
claude
```

### Generated code doesn't match my conventions

```bash
# Re-run wizard to update preferences
/sf:wizard --update

# Then regenerate skills
/sf:generate nextjs-fullstack --force
```

### Wizard fails during documentation fetch

```bash
# Generate without fetching (uses built-in)
/sf:generate nextjs-fullstack --no-docs

# Check Context7 MCP
claude --list-mcps  # Should show: context7
```

---

## Performance & Limits

### What's the token budget?

Default: 5000 tokens total across all skills. Configurable:
```bash
/sf:config set optimization.token_budget 7000
```

### How many skills can I have?

No hard limit, but recommended: 8-12 skills for optimal performance.

### Does SkillForge work offline?

Skill usage works offline. Documentation fetching requires internet (Context7 MCP).

---

## Technical Questions

### Which Python version is required?

Python 3.11 or higher.

### Can I use SkillForge with other AI assistants?

Not currently. SkillForge is built specifically for Claude Code's skill architecture.

### Is there an API?

Yes! See [API Documentation](API.md) for programmatic access.

### How do I contribute?

See [Contributing Guide](CONTRIBUTING.md) for guidelines.

---

## Workflow

### Do I need to manually load skills?

No! SkillForge orchestrates automatically. Just make requests naturally, and SkillForge loads relevant skills behind the scenes.

### Can I force-load a specific skill?

Yes, mention the skill name in your request:
```
"Create a component using my nextjs-fullstack skill"
```

### What if I disagree with SkillForge's decisions?

Use `/sf:introspect` to see why decisions were made, then adjust preferences via `/sf:config` or `/sf:wizard --update`.

---

## Data & Privacy

### What data does SkillForge collect?

SkillForge tracks:
- Skill usage statistics (which skills, success rates)
- Code patterns you use repeatedly
- Skill combinations

NOT tracked:
- Actual code content
- Project names
- Sensitive information

### Can I export my data?

Yes:
```bash
# Export analysis
/sf:analyze --export

# Data location
~/.claude/skills/skillforge/data/
```

### Can I delete my data?

Yes:
```bash
/sf:reset --all  # Complete reset
/sf:reset --analytics  # Just usage data
/sf:reset --patterns  # Just learned patterns
```

---

## Updates & Versions

### How do I update SkillForge?

```bash
pipx upgrade skillforge
# or
pip install --upgrade skillforge
```

### What version am I running?

```bash
skillforge --version
# or in Claude Code
/sf:status
```

### Do skills need updates when SkillForge updates?

Minor updates: No
Major updates: May require `/sf:update --all`

---

## Best Practices

### How long until patterns are learned?

Typically 10-20 uses of similar tasks. Patterns need 80%+ confidence to apply automatically.

### Should I generate all available skills?

No! Generate only what you use. Start with 3-5 skills for your current stack.

### When should I re-run the wizard?

- When switching to a new tech stack
- When your coding conventions change
- Every 3-6 months to review preferences

---

## Error Messages

### "No user profile found"

Run the setup wizard:
```bash
/sf:wizard
```

### "Context7 MCP not available"

Context7 is optional. Generate without docs:
```bash
/sf:generate <skill> --no-docs
```

### "Token budget exceeded"

Reduce token usage:
```bash
/sf:optimize  # Compress skills
/sf:config set optimization.token_budget 3000  # Reduce per-skill budget
```

---

## Advanced

### Can I use custom templates?

Yes! Place templates in:
```
~/.claude/skills/skillforge/templates/custom/
```

See [Templates Guide](TEMPLATES.md) for details.

### Can I modify the orchestration logic?

Not directly, but you can configure behavior:
```bash
/sf:config  # View all options
```

### Can I run SkillForge headless?

Yes! Use the Python API:
```python
from skillforge.generators import SkillGenerator

generator = SkillGenerator()
skill = generator.generate(profile, "nextjs-fullstack")
```

---

## Getting Help

**Still have questions?**

- 📖 Read the [full documentation](../README.md)
- 🔧 Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- 🐛 [Report an issue](https://github.com/omarpiosedev/SkillForge/issues)
- 💬 [Start a discussion](https://github.com/omarpiosedev/SkillForge/discussions)

---

**SkillForge**: Transforming Claude Code into YOUR personal pair programmer.

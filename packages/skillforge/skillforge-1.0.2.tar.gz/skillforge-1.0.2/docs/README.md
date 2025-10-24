# 🔨 SkillForge

**Meta-Programming Framework for Claude Code Skills**

---

## 🚧 Development Status

**Current Phase**: Fase 0 - Preparation & Setup
**Version**: 0.0.1-dev
**Status**: In Development

---

## 🎯 What is SkillForge?

SkillForge transforms Claude Code from a generic AI assistant into an expert team member specialized in YOUR tech stack, following YOUR conventions, and continuously improving from YOUR patterns.

**In one sentence**: SkillForge generates, orchestrates, and optimizes personalized Claude Code skills automatically.

---

## 💡 The Problem

Claude Code has powerful native skills but they are:
- Generic (don't know YOUR stack)
- Static (don't improve over time)
- Uncoordinated (no intelligent orchestration)
- Manual (hard to create custom skills)

**Result**: Generated code requires 15-30 minutes of adjustments to match your style.

---

## ✨ The Solution

SkillForge provides 4 core components:

1. **Generator** - Creates personalized skills for your tech stack
2. **Orchestrator** - Intelligently loads the right skills at the right time
3. **Learner** - Detects patterns and improves skills over time
4. **Optimizer** - Keeps skills updated and token-optimized

---

## 🏗️ Project Structure

```
SkillForge/                           # Repository root
├── skillforge/                       # Python package
│   ├── __init__.py
│   ├── generators/                   # Skill generation engine
│   ├── analyzers/                    # Intelligence & learning systems
│   ├── templates/                    # Skill templates
│   │   ├── tech-stack/              # Framework-specific templates
│   │   ├── workflow/                # Workflow templates
│   │   └── integration/             # Integration templates
│   └── data/
│       ├── cache/                    # Cached documentation
│       └── skill_files/              # SkillForge framework (deployed to ~/.claude/skills/)
│           ├── SKILL.md             # Entry point (Fase 1)
│           ├── core/                 # Behavioral files (Fase 2)
│           │   ├── SKILLFORGE.md
│           │   ├── ORCHESTRATION.md
│           │   ├── GENERATOR.md
│           │   └── ...
│           └── commands/sf/          # Slash commands (Fase 6)
│               ├── wizard.md
│               └── ...
├── tests/                            # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                             # Documentation & research
│   ├── research/                     # Technical research
│   ├── adr/                          # Architecture decisions
│   └── ...
├── scripts/                          # Development scripts
├── setup.py                          # Package setup (Fase 1)
├── pyproject.toml                    # Modern Python packaging (Fase 1)
└── README.md
```

**Note**: The `skillforge/data/skill_files/` directory contains the actual SkillForge framework files (SKILL.md, core/, commands/) that will be deployed to `~/.claude/skills/skillforge/` during installation.

---

## 🚀 Quick Start

**Not yet available - in development**

When ready:
```bash
pipx install skillforge
/sf:wizard  # In Claude Code
```

---

## 📖 Documentation

- [Complete Briefing](./docs/skillforge-briefing-completo.md)
- [Development Roadmap](./docs/skillforge-complete-roadmap.md)
- [Claude Code Briefing](./docs/CLAUDE_BRIEFING.md)
- [Research Documents](./docs/research/)
- [Architecture Decisions](./docs/adr/)

---

## 🧪 Development Setup

```bash
# Prerequisites
python3 --version  # >= 3.11 required
git --version
claude --version

# Clone and setup (if not already done)
cd SkillForge
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Run tests (when available)
pytest tests/ -v
```

---

## 📊 Development Progress

### Fase 0: Preparation & Setup ✅ COMPLETE
- [x] Verify prerequisites (Python 3.13.7, git, Claude Code)
- [x] Initialize git repository with .gitignore
- [x] Create virtual environment
- [x] Install base dependencies (pytest, pyyaml, requests, click)
- [x] Create directory structure
- [x] Create initial README.md
- [x] Research Claude Code native skills system
- [x] Research SuperClaude patterns
- [x] Research Context7 MCP integration
- [x] Create ADRs (001-003)
- [x] Reorganize project structure (Python package + framework separation)

### Fase 1: Base Structure (Next)
- [ ] Create SKILL.md entry point
- [ ] Create setup.py and pyproject.toml
- [ ] Create configuration management system
- [ ] Create CLI entry point (skillforge init)

---

## 🎯 Roadmap

**MVP Timeline**: 8 weeks

1. **Foundation** (Week 1-2)
2. **Generation System** (Week 3-4)
3. **Alpha Testing** (Week 5)
4. **Commands & Polish** (Week 6)
5. **Documentation** (Week 7)
6. **Release MVP v0.5** (Week 8)

See [complete roadmap](./skillforge-complete-roadmap.md) for details.

---

## 🤝 Contributing

Project is in early development. Contributions welcome after MVP release.

---

## 📄 License

MIT License (to be added)

---

## 👤 Author

Omar Pioselli

---

**Built with Claude Code** 🤖

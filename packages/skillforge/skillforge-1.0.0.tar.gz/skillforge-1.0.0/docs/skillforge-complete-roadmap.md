# 🗺️ SkillForge - Roadmap Completa di Sviluppo

**Framework di Meta-Programmazione Intelligente per Claude Code**

---

## 📋 Indice

- [Fase 0: Preparazione & Setup](#fase-0-preparazione--setup)
- [Fase 1: Struttura Base](#fase-1-struttura-base)
- [Fase 2: File Comportamentali Core](#fase-2-file-comportamentali-core)
- [Fase 3: Sistema di Generazione](#fase-3-sistema-di-generazione)
- [Fase 4: Sistema di Orchestrazione](#fase-4-sistema-di-orchestrazione)
- [Fase 5: Pattern Learning](#fase-5-pattern-learning)
- [Fase 6: Comandi Slash](#fase-6-comandi-slash)
- [Fase 7: Templates](#fase-7-templates)
- [Fase 8: Testing & Validation](#fase-8-testing--validation)
- [Fase 9: Documentation](#fase-9-documentation)
- [Fase 10: Release & Distribution](#fase-10-release--distribution)

---

## 🎯 Overview del Progetto

### Cosa Stiamo Costruendo
Un framework di meta-programmazione che trasforma Claude Code in un sistema intelligente di gestione skills, capace di:
- Generare skills personalizzate per lo stack tecnologico dell'utente
- Orchestrare intelligentemente skills multiple
- Imparare dai pattern d'uso
- Ottimizzare automaticamente le performance

### Stack Tecnologico
- **Linguaggio**: Python 3.11+ (per script e logica)
- **Formato Config**: YAML + Markdown
- **Storage**: JSON (per dati persistenti)
- **Integration**: MCP (Model Context Protocol) - Context7, Sequential
- **Testing**: pytest + pytest-cov
- **Docs**: Markdown + docstrings

### Ambiente di Sviluppo
- **Editor**: Claude Code (usato per sviluppare SkillForge stesso!)
- **Terminal**: Bash/Zsh
- **Git**: Version control
- **Python Environment**: venv o pipx

---

## Fase 0: Preparazione & Setup

### 0.1 Setup Ambiente di Sviluppo

#### Prerequisiti
```bash
# Verificare versione Python
python3 --version  # Deve essere >= 3.11

# Verificare Claude Code installato
claude --version

# Verificare git
git --version
```

#### Creare Progetto
```bash
# Creare directory progetto
mkdir skillforge-development
cd skillforge-development

# Inizializzare git
git init
git branch -m main

# Creare virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# Creare .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Data files (non committare dati utente)
data/user_profile.json
data/usage_analytics.json
data/learned_patterns.json
data/cache/

# Build
dist/
build/
EOF

# Installare dipendenze base
pip install --upgrade pip
pip install pytest pytest-cov pyyaml requests
```

#### Struttura Iniziale
```bash
# Creare struttura directory base
mkdir -p {core,commands/sf,commands/shared,generators,templates/{tech-stack,workflow,integration},analyzers,data/cache/context7,docs,tests}

# Creare README iniziale
cat > README.md << 'EOF'
# SkillForge

Meta-programming framework for Claude Code skills.

## Development Status
🚧 In Development

## Quick Start
Coming soon...
EOF

# Primo commit
git add .
git commit -m "chore: initial project structure"
```

### 0.2 Ricerca & Documentazione Preliminare

**IMPORTANTE: Usa Claude Code per questa fase!**

#### Ricerche da Fare con Claude Code

```
📝 PROMPT 1: Comprensione Sistema Skills Nativo
"Analizza in dettaglio come funziona il sistema di Skills nativo in Claude Code.
Leggi la documentazione ufficiale Anthropic e crea un documento che spiega:
- Come Claude carica le skills all'avvio
- Il formato del file SKILL.md (YAML frontmatter + Markdown)
- Progressive disclosure mechanism
- Come Claude decide quando usare una skill
- Struttura directory ~/.claude/skills/
- Come funzionano allowed-tools
- Best practices per creare skills

Salva tutto in: docs/research/native-skills-system.md"
```

```
📝 PROMPT 2: Studio SuperClaude
"Analizza il framework SuperClaude su GitHub (SuperClaude-Org/SuperClaude_Framework).
Studia in particolare:
- Come strutturano i file comportamentali (CLAUDE.md, RULES.md, etc)
- Sistema di @include references
- Come implementano comandi slash
- Sistema di personas/agents
- Pattern di orchestrazione

Crea un documento con i pattern riutilizzabili per SkillForge.
Salva in: docs/research/superclaude-patterns.md"
```

```
📝 PROMPT 3: MCP Context7 Integration
"Ricerca e documenta l'integrazione con Context7 MCP per fetching documentazione.
Include:
- Come funziona resolve-library-id
- Come funziona get-library-docs
- Best practices per caching
- Rate limiting
- Error handling

Salva in: docs/research/context7-integration.md"
```

```
📝 PROMPT 4: Tech Stack Analysis
"Analizza i tech stack più comuni per web development nel 2025:
- Frontend frameworks (Next.js, React, Vue, Svelte)
- Backend frameworks (Node.js, Python, Go)
- Databases (PostgreSQL, MongoDB, Supabase)
- UI libraries (Tailwind, Shadcn/ui, Material UI)
- State management (Zustand, Redux, Context)

Per ognuno, identifica:
- Versione corrente
- Best practices principali
- Pattern comuni
- Cosa includere in una skill

Salva in: docs/research/tech-stacks-analysis.md"
```

#### Creare Architecture Decision Records (ADR)

```bash
mkdir -p docs/adr

# ADR 1: Perché Python per i generator?
cat > docs/adr/001-python-generators.md << 'EOF'
# ADR 001: Python per Generator Scripts

## Status
Accepted

## Context
Dobbiamo scegliere il linguaggio per gli script di generazione.

## Decision
Usiamo Python 3.11+ per:
- Generator scripts
- Analyzers
- Utility functions

## Consequences
✅ Pro:
- Ottimo supporto per text processing
- Librerie per YAML/JSON
- Facile integrazione con bash
- Type hints per safety

❌ Cons:
- Dipendenza aggiuntiva (ma Python è già richiesto per Claude Code)
EOF
```

Creare ADR per tutte le decisioni architetturali principali.

---

## Fase 1: Struttura Base

### 1.1 Creare SKILL.md (Entry Point)

**PROMPT PER CLAUDE CODE:**
```
"Crea il file ~/.claude/skills/skillforge/SKILL.md seguendo questi requisiti:

1. YAML frontmatter con:
   - name: "SkillForge"
   - description chiara e dettagliata (quando usare questa skill)
   - version: "1.0.0"
   - allowed-tools: [bash_tool, view, create_file, str_replace, web_search, web_fetch, Context7 tools]

2. Sezione Core Identity che spiega:
   - Cos'è SkillForge (meta-programming framework)
   - Cosa NON è (non è una semplice skill)
   - I 4 pilastri principali

3. Sezione Configuration System con @include references a:
   - @core/SKILLFORGE.md
   - @core/ORCHESTRATION.md
   - @core/GENERATOR.md
   - @core/PATTERNS.md
   - @core/RULES.md
   - @core/WORKFLOWS.md
   - @core/MCP_INTEGRATION.md

4. Sezione Available Commands
   - Lista tutti i comandi /sf:*
   - Breve descrizione per ognuno

5. Sezione How Claude Should Use SkillForge
   - Automatic orchestration flow
   - Example flow concreto
   - Progressive disclosure strategy

6. Sezione Pattern Learning
   - Cosa tracciare
   - Come usare i dati

7. Sezioni Critical Behaviors
   - DO's
   - DON'Ts

8. Error Handling

Usa come riferimento:
- Il sistema di skills nativo (docs/research/native-skills-system.md)
- Pattern da SuperClaude (docs/research/superclaude-patterns.md)

Lunghezza: ~500 righe, ben strutturato, massima chiarezza."
```

**File da creare:** `~/.claude/skills/skillforge/SKILL.md`

**Validazione:**
```bash
# Dopo aver creato il file, validarlo
cd ~/.claude/skills/skillforge

# 1. Verificare YAML frontmatter è valido
python3 << 'EOF'
import yaml
with open('SKILL.md', 'r') as f:
    content = f.read()
    if content.startswith('---'):
        yaml_content = content.split('---')[1]
        try:
            data = yaml.safe_load(yaml_content)
            print("✅ YAML frontmatter valido")
            print(f"Name: {data.get('name')}")
            print(f"Description: {data.get('description')[:50]}...")
        except Exception as e:
            print(f"❌ Errore YAML: {e}")
EOF

# 2. Verificare @include references esistono (verranno creati dopo)
echo "📝 References da creare:"
grep "@core/" SKILL.md | sed 's/.*@/  - /'
```

### 1.2 Creare Package Structure

```bash
cd ~/skillforge-development

# Creare __init__.py files per rendere moduli importabili
touch generators/__init__.py
touch analyzers/__init__.py
touch tests/__init__.py

# Creare setup.py per installazione
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="skillforge",
    version="1.0.0",
    description="Meta-programming framework for Claude Code skills",
    author="SkillForge Team",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.11",
    entry_points={
        'console_scripts': [
            'skillforge=generators.cli:main',
        ],
    },
)
EOF

# Installare in modalità development
pip install -e .
```

### 1.3 Creare Configurazione Base

```python
# File: generators/config.py
"""
Configuration management for SkillForge
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Manages SkillForge configuration"""
    
    SKILLFORGE_HOME = Path.home() / ".claude" / "skills" / "skillforge"
    DATA_DIR = SKILLFORGE_HOME / "data"
    CACHE_DIR = DATA_DIR / "cache" / "context7"
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "user_profile": {
            "setup_completed": False,
            "tech_stack": {},
            "preferences": {},
            "conventions": {}
        },
        "learning": {
            "enabled": True,
            "min_samples_for_pattern": 10
        },
        "optimization": {
            "auto_optimize": True,
            "token_budget": 5000
        }
    }
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.SKILLFORGE_HOME.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_user_profile(cls) -> Dict[str, Any]:
        """Load user profile or create default"""
        cls.ensure_directories()
        profile_path = cls.DATA_DIR / "user_profile.json"
        
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                return json.load(f)
        else:
            return cls.DEFAULT_CONFIG["user_profile"]
    
    @classmethod
    def save_user_profile(cls, profile: Dict[str, Any]):
        """Save user profile"""
        cls.ensure_directories()
        profile_path = cls.DATA_DIR / "user_profile.json"
        
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
    
    @classmethod
    def load_analytics(cls) -> Dict[str, Any]:
        """Load usage analytics"""
        cls.ensure_directories()
        analytics_path = cls.DATA_DIR / "usage_analytics.json"
        
        if analytics_path.exists():
            with open(analytics_path, 'r') as f:
                return json.load(f)
        else:
            return {"skill_usage": {}, "patterns": {}}
    
    @classmethod
    def save_analytics(cls, analytics: Dict[str, Any]):
        """Save usage analytics"""
        cls.ensure_directories()
        analytics_path = cls.DATA_DIR / "usage_analytics.json"
        
        with open(analytics_path, 'w') as f:
            json.dump(analytics, f, indent=2)
```

**Test:**
```python
# File: tests/test_config.py
import pytest
from generators.config import Config

def test_ensure_directories():
    """Test directory creation"""
    Config.ensure_directories()
    assert Config.SKILLFORGE_HOME.exists()
    assert Config.DATA_DIR.exists()
    assert Config.CACHE_DIR.exists()

def test_user_profile():
    """Test user profile load/save"""
    profile = Config.load_user_profile()
    assert "setup_completed" in profile
    
    profile["setup_completed"] = True
    Config.save_user_profile(profile)
    
    loaded = Config.load_user_profile()
    assert loaded["setup_completed"] == True
```

```bash
# Eseguire test
pytest tests/test_config.py -v
```

---

## Fase 2: File Comportamentali Core

### 2.1 Creare SKILLFORGE.md (Core Configuration)

**PROMPT PER CLAUDE CODE:**
```
"Crea il file core/SKILLFORGE.md seguendo questa struttura:

# SkillForge Core Configuration

Sezioni obbligatorie:

1. Core Philosophy
   - 4 principi fondamentali con spiegazione dettagliata
   - Personalization Over Generalization
   - Intelligence Over Automation
   - Evolution Over Stasis
   - Efficiency Over Completeness

2. Operational Modes
   - Setup Mode (quando e come)
   - Orchestration Mode (DEFAULT - comportamento)
   - Learning Mode (background)
   - Optimization Mode (periodico)
   - Update Mode (weekly)
   
   Per ogni modo: triggers, behavior, output

3. Skill Discovery Algorithm
   - Pseudocode Python dettagliato
   - 8 step del processo
   - Esempio concreto

4. Token Economics
   - Budget allocation strategy
   - Token optimization techniques
   - Breakdown per categoria

5. Skill Generation Rules
   - Regole OBBLIGATORIE per generazione
   - Context7 integration
   - Structure requirements
   - User conventions integration
   - Composability rules

6. Pattern Learning System
   - JSON schema per tracked data
   - Learning process (5 steps)
   - Update triggers

7. MCP Integration Strategy
   - Quali MCP servers
   - Quando usarli
   - Priorità

8. Error Recovery
   - Scenari comuni
   - Recovery strategies
   - Fallback mechanisms

9. Quality Standards
   - Checklist per generated skills (✅ Must / ❌ Must Not)

Lunghezza: ~400 righe
Formato: Markdown con code blocks per esempi
Stile: Tecnico ma chiaro

Riferimenti:
- docs/research/native-skills-system.md
- docs/research/superclaude-patterns.md"
```

**File da creare:** `core/SKILLFORGE.md`

**Validazione:**
```bash
# Verificare sezioni obbligatorie
echo "Verificando sezioni in SKILLFORGE.md..."
required_sections=(
    "Core Philosophy"
    "Operational Modes"
    "Skill Discovery Algorithm"
    "Token Economics"
    "Pattern Learning System"
)

for section in "${required_sections[@]}"; do
    if grep -q "## $section" core/SKILLFORGE.md; then
        echo "✅ $section"
    else
        echo "❌ Manca: $section"
    fi
done
```

### 2.2 Creare ORCHESTRATION.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/ORCHESTRATION.md che definisce il sistema di orchestrazione intelligente.

Struttura:

1. Orchestration Pipeline
   - Diagramma ASCII flow
   - 8 stage del pipeline
   - Spiegazione di ogni stage

2. Intent Analysis
   - Classe IntentAnalyzer in Python
   - 5 step analysis
   - Esempi concreti

3. Skill Discovery
   - Classe SkillDiscovery in Python
   - 5 strategie di discovery
   - Esempio con output

4. Dependency Resolution
   - Classe DependencyResolver
   - Topological sort
   - Esempio dependency graph

5. Priority Sorting
   - Algoritmo di scoring
   - 5 fattori di priorità
   - Formula finale

6. Token Budget Allocation
   - TokenBudgetManager class
   - Allocation strategy per priority
   - Esempio allocation

7. Progressive Loading
   - 4 livelli di loading
   - Quando usare ogni livello
   - Esempi

8. Multi-Skill Workflows
   - WorkflowOrchestrator class
   - Esempio workflow completo
   - Step-by-step breakdown

9. Conflict Resolution
   - 3 strategie di risoluzione
   - Esempi di conflitti
   - Decision tree

10. Usage Tracking
    - Cosa tracciare
    - Come salvare
    - Schema dati

11. Optimization Strategies
    - 5 tecniche di ottimizzazione
    - Quando applicarle

Ogni sezione deve avere:
- Code examples in Python
- Concrete examples
- Clear comments

Lunghezza: ~600 righe"
```

**File da creare:** `core/ORCHESTRATION.md`

### 2.3 Creare GENERATOR.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/GENERATOR.md che documenta il sistema di generazione skills.

Struttura:

1. Generation Pipeline
   - Overview 7-step process
   - Input/Output per step
   - Diagramma flow

2. Wizard System
   - Interactive questionnaire design
   - Question categories:
     * Role identification
     * Tech stack detection
     * Framework preferences
     * Tool preferences
     * Workflow patterns
   - Branching logic
   - Validation rules

3. Documentation Fetching
   - Context7 integration dettagliata
   - resolve-library-id process
   - get-library-docs process
   - Caching strategy
   - Fallback mechanisms

4. Template Processing
   - Template format
   - Variable substitution
   - Conditional blocks
   - Loop constructs
   - Example template

5. SKILL.md Generation
   - Required sections
   - YAML frontmatter generation
   - Content structure
   - Best practices injection
   - Example generation

6. Supporting Files
   - Scripts generation
   - Template files creation
   - Documentation generation
   - Directory structure

7. Validation System
   - Pre-generation validation
   - Post-generation validation
   - Quality checks
   - Testing generated skills

8. Version Management
   - Versioning strategy
   - Update detection
   - Migration handling

Includi:
- Python code examples
- Template examples
- Generated output examples
- Validation scripts

Lunghezza: ~500 righe"
```

**File da creare:** `core/GENERATOR.md`

### 2.4 Creare PATTERNS.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/PATTERNS.md che definisce il sistema di pattern learning.

Struttura:

1. Pattern Detection
   - Cosa sono i patterns
   - Tipi di pattern:
     * Usage patterns
     * Code style patterns
     * Workflow patterns
     * Combination patterns
   - Detection algorithms

2. Data Collection
   - Cosa tracciare
   - Quando tracciare
   - Schema dati JSON completo
   - Privacy considerations

3. Pattern Analysis
   - Statistical methods
   - Confidence thresholds
   - Pattern validation
   - False positive handling

4. Pattern Application
   - Come applicare patterns appresi
   - Skill updating process
   - User notification
   - Opt-out mechanism

5. Pattern Categories
   
   A. Code Style Patterns:
      - Naming conventions
      - Import preferences
      - Error handling style
      - Testing approaches
   
   B. Workflow Patterns:
      - Commit message format
      - Branch naming
      - PR descriptions
      - Review checklist
   
   C. Tool Preferences:
      - Preferred libraries
      - Avoided libraries
      - Configuration patterns
   
   D. Architecture Patterns:
      - File organization
      - Module structure
      - Separation of concerns

6. Learning Pipeline
   - 5-stage learning process
   - Confidence building
   - Pattern reinforcement
   - Pattern decay

7. Pattern Storage
   - File format
   - Schema design
   - Query capabilities
   - Backup strategy

8. Pattern Sharing (Future)
   - Team patterns
   - Community patterns
   - Privacy preservation

Ogni sezione con:
- JSON examples
- Python algorithms
- Concrete scenarios

Lunghezza: ~450 righe"
```

**File da creare:** `core/PATTERNS.md`

### 2.5 Creare RULES.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/RULES.md - regole comportamentali per Claude quando usa SkillForge.

Ispirazione: SuperClaude RULES.md ma adattato per SkillForge.

Struttura:

1. Priority System
   🔴 CRITICAL: Security, data safety, must-follow
   🟡 IMPORTANT: Quality, best practices, strong preference
   🟢 RECOMMENDED: Optimization, style, apply when practical

2. Core Rules

   🔴 CRITICAL Rules:
   - ALWAYS fetch latest documentation via Context7 before generating
   - NEVER generate skills without user profile
   - ALWAYS validate generated SKILL.md YAML
   - NEVER modify user data without permission
   - ALWAYS use absolute paths
   - NEVER expose sensitive data in skills
   
   🟡 IMPORTANT Rules:
   - Think before generating (analyze user needs)
   - Follow user conventions consistently
   - Keep skills focused (one capability per skill)
   - Make skills composable
   - Document all assumptions
   - Test generated skills
   
   🟢 RECOMMENDED Rules:
   - Optimize for token efficiency
   - Cache frequently used docs
   - Suggest improvements proactively
   - Learn from patterns (when enabled)

3. Skill Generation Rules
   - Pre-generation checklist
   - Generation process rules
   - Post-generation validation
   - Naming conventions

4. Orchestration Rules
   - Skill loading priorities
   - Token budget enforcement
   - Conflict resolution hierarchy
   - Error handling protocol

5. File Organization Rules
   - Where to place generated skills
   - Directory structure enforcement
   - Naming conventions
   - No scattered files policy

6. Decision Trees
   - When to generate new skill?
   - When to update existing skill?
   - When to merge skills?
   - When to ask user?

7. Quality Gates
   - Validation checkpoints
   - Success criteria
   - Failure handling

8. Learning Rules
   - When to track data
   - When to apply patterns
   - Confidence thresholds
   - User notification requirements

Formato:
- Clear priority markers
- Actionable rules
- Decision trees in ASCII
- Examples for unclear cases

Lunghezza: ~350 righe"
```

**File da creare:** `core/RULES.md`

### 2.6 Creare WORKFLOWS.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/WORKFLOWS.md che definisce workflow automatizzati comuni.

Struttura:

1. Workflow Catalog
   - Lista di 10+ workflow predefiniti
   - Breve descrizione per ognuno
   - Quando usarli

2. Workflow Definition Format
   - YAML schema per workflow
   - Required fields
   - Optional fields
   - Example completo

3. Common Workflows

   A. New Project Setup
      - Steps dettagliati
      - Skills coinvolte
      - Validation checks
      - Example output
   
   B. Feature Development
      - Branch creation
      - Implementation
      - Testing
      - Documentation
      - PR creation
   
   C. Bug Fix
      - Investigation
      - Fix implementation
      - Test creation
      - Verification
   
   D. Code Review
      - Analysis steps
      - Checklist items
      - Feedback generation
   
   E. Deployment
      - Pre-deployment checks
      - Deployment steps
      - Post-deployment validation
   
   F. Refactoring
      - Analysis
      - Plan generation
      - Incremental changes
      - Validation
   
   G. Documentation Update
      - What to document
      - Format
      - Generation
      - Review
   
   H. Performance Optimization
      - Profiling
      - Analysis
      - Optimization
      - Benchmarking

4. Workflow Orchestration
   - Como concatenare workflows
   - Dependency management
   - Parallel execution
   - Error recovery

5. Custom Workflows
   - How users can define custom
   - Template structure
   - Variables
   - Conditionals

6. Workflow State Management
   - State tracking
   - Resume capability
   - Rollback mechanism

Ogni workflow con:
- Step-by-step breakdown
- Skills used
- Expected output
- Error scenarios

Lunghezza: ~500 righe"
```

**File da creare:** `core/WORKFLOWS.md`

### 2.7 Creare MCP_INTEGRATION.md

**PROMPT PER CLAUDE CODE:**
```
"Crea core/MCP_INTEGRATION.md per integrazioni MCP.

Struttura:

1. MCP Overview
   - Cosa è MCP
   - Perché SkillForge usa MCP
   - Benefits

2. Context7 Integration (PRIMARY)
   
   A. Setup & Configuration
      - How to enable Context7
      - Configuration options
      - Testing connection
   
   B. Library ID Resolution
      - resolve-library-id function
      - Matching algorithm
      - Fallback strategies
      - Caching
   
   C. Documentation Fetching
      - get-library-docs function
      - Token limits
      - Topic focusing
      - Response parsing
   
   D. Best Practices
      - When to fetch
      - What to cache
      - How long to cache
      - Rate limiting
   
   E. Error Handling
      - Network errors
      - API errors
      - Stale data handling
      - Fallback to web_search

3. Sequential Integration (SECONDARY)
   
   - When to use Sequential
   - Multi-step reasoning
   - Complex orchestration
   - Examples

4. Other MCP Servers
   
   - Web search/fetch
   - Filesystem operations
   - Custom user MCPs
   - How to extend

5. Integration Patterns
   
   - Primary-fallback pattern
   - Parallel queries
   - Sequential chaining
   - Caching layer

6. Testing Integration
   - Mock servers for testing
   - Integration tests
   - Error scenarios

7. Future Integrations
   - Planned MCPs
   - Community MCPs
   - Custom integrations

Includi:
- Code examples
- Configuration samples
- Error handling code
- Test examples

Lunghezza: ~400 righe"
```

**File da creare:** `core/MCP_INTEGRATION.md`

### 2.8 Validazione File Comportamentali

```bash
# Script di validazione
cat > scripts/validate-core-files.sh << 'EOF'
#!/bin/bash

echo "🔍 Validating SkillForge Core Files..."

CORE_FILES=(
    "core/SKILLFORGE.md"
    "core/ORCHESTRATION.md"
    "core/GENERATOR.md"
    "core/PATTERNS.md"
    "core/RULES.md"
    "core/WORKFLOWS.md"
    "core/MCP_INTEGRATION.md"
)

all_valid=true

for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Check file size (should be substantial)
        size=$(wc -l < "$file")
        if [ "$size" -gt 100 ]; then
            echo "✅ $file ($size lines)"
        else
            echo "⚠️  $file is too short ($size lines)"
            all_valid=false
        fi
        
        # Check for required sections (basic)
        if grep -q "^# " "$file"; then
            echo "   - Has main heading"
        else
            echo "   ❌ Missing main heading"
            all_valid=false
        fi
    else
        echo "❌ Missing: $file"
        all_valid=false
    fi
done

if [ "$all_valid" = true ]; then
    echo ""
    echo "✅ All core files validated successfully!"
else
    echo ""
    echo "❌ Validation failed. Fix the issues above."
    exit 1
fi
EOF

chmod +x scripts/validate-core-files.sh

# Eseguire validazione
./scripts/validate-core-files.sh
```

---

## Fase 3: Sistema di Generazione

### 3.1 Wizard Engine

**PROMPT PER CLAUDE CODE:**
```
"Crea generators/wizard_engine.py - motore per interactive wizard.

Requirements:

1. Classe WizardEngine con metodi:
   - run() - main entry point
   - ask_question() - chiede domanda con opzioni
   - detect_stack() - auto-detection stack (analizza directory corrente)
   - validate_answer() - valida risposta
   - save_profile() - salva profilo utente

2. Question Flow:
   Step 1: Role (Developer type)
   Step 2: Frontend Framework
   Step 3: UI Library (if applicable)
   Step 4: State Management
   Step 5: Backend Framework
   Step 6: Database
   Step 7: Auth Provider
   Step 8: Testing Tools
   Step 9: Build Tools
   Step 10: Deployment Platform
   Step 11: Code Style Preferences
   Step 12: Workflow Preferences

3. Features:
   - Auto-detection (analizza package.json, requirements.txt, etc)
   - Skip logic (se auto-detected, chiede conferma)
   - Branching (domande diverse based on answers)
   - Progress indicator
   - Can go back
   - Save and resume

4. Output:
   - Genera user_profile.json
   - Mostra summary
   - Suggerisce skills da generare

5. Error Handling:
   - Invalid input
   - Interrupted session
   - Resume from saved state

Usa:
- Type hints
- Docstrings
- Error handling
- Logging

Test: crea tests/test_wizard_engine.py

Lunghezza: ~400 righe + 100 righe test"
```

**File da creare:** `generators/wizard_engine.py`

**Example Structure:**
```python
# generators/wizard_engine.py

from typing import Dict, List, Any, Optional
import json
from pathlib import Path
from .config import Config

class WizardEngine:
    """Interactive wizard for skill generation setup"""
    
    def __init__(self):
        self.profile = Config.load_user_profile()
        self.answers = {}
    
    def run(self) -> Dict[str, Any]:
        """Run the interactive wizard"""
        print("🧙 SkillForge Setup Wizard")
        print("=" * 50)
        
        # Auto-detect existing stack
        detected = self.detect_stack()
        if detected:
            self.show_detected(detected)
        
        # Ask questions
        self.ask_role()
        self.ask_frontend()
        self.ask_backend()
        self.ask_database()
        # ... more questions
        
        # Generate summary
        self.show_summary()
        
        # Save profile
        self.save_profile()
        
        return self.profile
    
    def detect_stack(self) -> Dict[str, Any]:
        """Auto-detect tech stack from current directory"""
        detected = {}
        cwd = Path.cwd()
        
        # Check package.json
        if (cwd / "package.json").exists():
            with open(cwd / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), 
                        **pkg.get("devDependencies", {})}
                
                if "next" in deps:
                    detected["frontend"] = "Next.js"
                elif "react" in deps:
                    detected["frontend"] = "React"
                
                if "tailwindcss" in deps:
                    detected["ui"] = "Tailwind CSS"
        
        # Check requirements.txt
        if (cwd / "requirements.txt").exists():
            with open(cwd / "requirements.txt") as f:
                reqs = f.read()
                if "fastapi" in reqs:
                    detected["backend"] = "FastAPI"
                elif "django" in reqs:
                    detected["backend"] = "Django"
        
        return detected
    
    def ask_question(self, 
                     question: str, 
                     options: List[str],
                     allow_multiple: bool = False) -> Any:
        """Ask a question with multiple choice"""
        print(f"\n{question}")
        for i, option in enumerate(options, 1):
            print(f"  [{i}] {option}")
        
        if allow_multiple:
            print("  (Enter numbers separated by commas)")
        
        while True:
            answer = input("> ").strip()
            
            if allow_multiple:
                try:
                    indices = [int(x.strip()) for x in answer.split(",")]
                    return [options[i-1] for i in indices]
                except:
                    print("❌ Invalid input. Try again.")
            else:
                try:
                    idx = int(answer)
                    if 1 <= idx <= len(options):
                        return options[idx-1]
                except:
                    pass
                print("❌ Invalid input. Try again.")
    
    # ... more methods

# Example usage:
if __name__ == "__main__":
    wizard = WizardEngine()
    profile = wizard.run()
    print("\n✅ Profile saved!")
```

### 3.2 Skill Generator

**PROMPT PER CLAUDE CODE:**
```
"Crea generators/skill_generator.py - genera file SKILL.md.

Requirements:

1. Classe SkillGenerator:
   - generate_skill(profile, skill_type) -> Path
   - fetch_documentation(library_name) -> str
   - process_template(template_path, variables) -> str
   - validate_generated_skill(skill_path) -> bool

2. Generation Process:
   Step 1: Load template
   Step 2: Fetch latest docs (Context7)
   Step 3: Process template with variables
   Step 4: Generate SKILL.md content
   Step 5: Create supporting files
   Step 6: Validate output
   Step 7: Save to ~/.claude/skills/

3. Template Variables:
   - {{framework_name}}
   - {{framework_version}}
   - {{best_practices}}
   - {{code_examples}}
   - {{user_conventions}}
   - {{dependencies}}

4. Documentation Integration:
   - Use Context7 to fetch docs
   - Parse and extract relevant sections
   - Format for SKILL.md
   - Cache for future use

5. Validation:
   - YAML frontmatter valid
   - Required sections present
   - No placeholder text remaining
   - Examples are valid
   - Description is specific

Includi:
- Error handling
- Logging
- Progress indicators
- Rollback on failure

Test: tests/test_skill_generator.py

Lunghezza: ~500 righe + 150 righe test"
```

**File da creare:** `generators/skill_generator.py`

### 3.3 Template Processor

**PROMPT PER CLAUDE CODE:**
```
"Crea generators/template_processor.py - processa template con variabili.

Requirements:

1. Classe TemplateProcessor:
   - load_template(template_path) -> str
   - process(template, variables) -> str
   - process_conditionals(template, variables) -> str
   - process_loops(template, variables) -> str

2. Template Syntax:
   
   Variables:
   {{variable_name}}
   
   Conditionals:
   {{#if condition}}
   content
   {{/if}}
   
   Loops:
   {{#each items}}
   - {{name}}
   {{/each}}
   
   Includes:
   {{> partial_name}}

3. Features:
   - Variable substitution
   - Conditional blocks
   - Loop constructs
   - Partial templates
   - Escaping
   - Default values

4. Validation:
   - Check all variables provided
   - Warn about unused variables
   - Error on missing required variables

Example template usage:
```
---
name: "{{framework_name}}"
description: "{{description}}"
---

# {{framework_name}} Development

## Best Practices

{{#each best_practices}}
- {{this}}
{{/each}}

{{#if has_typescript}}
## TypeScript Configuration
...
{{/if}}
```

Test: tests/test_template_processor.py

Lunghezza: ~300 righe + 100 righe test"
```

**File da creare:** `generators/template_processor.py`

### 3.4 Documentation Fetcher

**PROMPT PER CLAUDE CODE:**
```
"Crea generators/doc_fetcher.py - fetches documentation via Context7.

Requirements:

1. Classe DocFetcher:
   - fetch(library_name, topic=None) -> str
   - resolve_library_id(library_name) -> str
   - get_docs(library_id, topic, tokens) -> str
   - cache_docs(library_id, docs)
   - get_cached_docs(library_id) -> Optional[str]

2. Context7 Integration:
   - Call resolve-library-id tool
   - Parse response
   - Select best match
   - Call get-library-docs
   - Parse documentation

3. Caching:
   - Cache in data/cache/context7/
   - Filename: {library_id}-{timestamp}.json
   - TTL: 7 days
   - Check cache before fetching

4. Fallback:
   - If Context7 fails → try web_search
   - If web_search fails → use builtin knowledge
   - Always inform user of source

5. Response Parsing:
   - Extract code examples
   - Extract best practices
   - Extract version info
   - Format for template

Error handling:
- Network errors
- API rate limits
- Invalid library names
- No documentation found

Test: tests/test_doc_fetcher.py

Lunghezza: ~350 righe + 100 righe test"
```

**File da creare:** `generators/doc_fetcher.py`

### 3.5 Validation Scripts

```bash
# Test generation pipeline
cat > scripts/test-generation.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Skill Generation Pipeline..."

# 1. Test wizard
echo "1. Testing Wizard Engine..."
python3 -c "
from generators.wizard_engine import WizardEngine
wizard = WizardEngine()
print('✅ Wizard initialized')
"

# 2. Test template processor
echo "2. Testing Template Processor..."
python3 -c "
from generators.template_processor import TemplateProcessor
processor = TemplateProcessor()
result = processor.process(
    '{{name}}',
    {'name': 'Test'}
)
assert result == 'Test'
print('✅ Template processor works')
"

# 3. Test doc fetcher (if Context7 available)
echo "3. Testing Doc Fetcher..."
python3 -c "
from generators.doc_fetcher import DocFetcher
fetcher = DocFetcher()
print('✅ Doc fetcher initialized')
# Note: actual fetch requires Context7 MCP
"

# 4. Test skill generator
echo "4. Testing Skill Generator..."
python3 -c "
from generators.skill_generator import SkillGenerator
generator = SkillGenerator()
print('✅ Skill generator initialized')
"

echo ""
echo "✅ All generation components initialized successfully!"
EOF

chmod +x scripts/test-generation.sh
./scripts/test-generation.sh
```

---

## Fase 4: Sistema di Orchestrazione

### 4.1 Intent Analyzer

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/intent_analyzer.py - analizza intent dalle richieste.

Requirements:

1. Classe IntentAnalyzer:
   - analyze(user_request: str) -> Intent
   - extract_entities(text: str) -> List[str]
   - determine_action(text: str) -> str
   - identify_domain(entities: List[str]) -> str
   - assess_complexity(text: str) -> str
   - match_patterns(text: str) -> List[Pattern]

2. Intent Data Class:
```python
@dataclass
class Intent:
    entities: List[str]           # ["Next.js", "Supabase", "auth"]
    action: str                   # "create", "build", "implement"
    domain: str                   # "fullstack", "frontend", "backend"
    complexity: str               # "simple", "moderate", "complex"
    patterns: List[Pattern]       # Matched learned patterns
    confidence: float             # 0.0 to 1.0
```

3. Entity Extraction:
   - Framework names (Next.js, React, etc)
   - Library names (Supabase, Prisma, etc)
   - Feature types (auth, dashboard, API)
   - File types (component, page, api route)

4. Action Detection:
   - create, build, implement, add
   - update, modify, refactor
   - debug, fix, troubleshoot
   - analyze, review, optimize

5. Domain Classification:
   - frontend
   - backend
   - fullstack
   - devops
   - testing
   - documentation

6. Complexity Assessment:
   - simple: single file, < 50 lines
   - moderate: multiple files, < 500 lines
   - complex: multiple features, > 500 lines
   - enterprise: full application

7. Pattern Matching:
   - Load learned patterns
   - Match against request
   - Return confidence scores

Test: tests/test_intent_analyzer.py con esempi:
- "Create a Next.js login component with Supabase" -> entities, action, domain
- "Fix the bug in my API route" -> debug action
- "Build a full dashboard" -> complex

Lunghezza: ~400 righe + 150 righe test"
```

**File da creare:** `analyzers/intent_analyzer.py`

### 4.2 Skill Discovery

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/skill_discovery.py - trova skills appropriate.

Requirements:

1. Classe SkillDiscovery:
   - discover(intent: Intent) -> List[Skill]
   - find_skill_for_entity(entity: str) -> Optional[Skill]
   - get_domain_skills(domain: str) -> List[Skill]
   - get_pattern_skills(patterns: List[Pattern]) -> List[Skill]
   - load_available_skills() -> List[Skill]

2. Skill Data Class:
```python
@dataclass
class Skill:
    name: str
    path: Path
    description: str
    triggers: List[str]
    dependencies: List[str]
    priority: int
    usage_count: int
    success_rate: float
    last_used: datetime
```

3. Discovery Strategies:
   
   A. Explicit Match:
      - User mentions framework name
      - Direct skill name match
      - Highest priority
   
   B. Pattern Match:
      - Learned patterns suggest skills
      - Based on historical usage
      - High priority
   
   C. Domain Match:
      - Domain requires certain skills
      - Standard combinations
      - Medium priority
   
   D. Dependency Match:
      - Other skills require this
      - Transitive dependencies
      - Low priority

4. Skill Loading:
   - Scan ~/.claude/skills/
   - Parse SKILL.md files
   - Extract metadata
   - Cache in memory

5. Filtering:
   - Remove irrelevant skills
   - Check applicability
   - Respect user preferences

Test: tests/test_skill_discovery.py

Lunghezza: ~350 righe + 100 righe test"
```

**File da creare:** `analyzers/skill_discovery.py`

### 4.3 Usage Tracker

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/usage_tracker.py - traccia uso skills per learning.

Requirements:

1. Classe UsageTracker:
   - track_usage(skills: List[Skill], success: bool)
   - record_combination(skills: List[Skill])
   - record_pattern(intent: Intent, skills: List[Skill])
   - get_statistics() -> Dict
   - analyze_trends() -> Dict

2. Data Schema:
```python
{
    "skill_usage": {
        "nextjs-fullstack": {
            "total_uses": 156,
            "successes": 147,
            "failures": 9,
            "last_used": "2025-10-22T10:00:00Z",
            "avg_duration_seconds": 45,
            "common_with": ["supabase-integration", "shadcn-ui"]
        }
    },
    "combinations": {
        "nextjs-fullstack+supabase-integration": {
            "count": 89,
            "success_rate": 0.96
        }
    },
    "patterns": {
        "create_auth_component": {
            "skills": ["nextjs-fullstack", "supabase-integration"],
            "frequency": 23,
            "confidence": 0.92
        }
    }
}
```

3. Tracking Events:
   - skill_loaded
   - skill_used
   - task_started
   - task_completed
   - task_failed

4. Statistics:
   - Success rates per skill
   - Common combinations
   - Execution times
   - Trend analysis

5. Privacy:
   - No sensitive data
   - Opt-out option
   - User can view/export data
   - User can delete data

6. Storage:
   - Save to data/usage_analytics.json
   - Atomic writes
   - Backup on update
   - Compression for large files

Test: tests/test_usage_tracker.py

Lunghezza: ~300 righe + 80 righe test"
```

**File da creare:** `analyzers/usage_tracker.py`

### 4.4 Pattern Detector

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/pattern_detector.py - rileva pattern da usage data.

Requirements:

1. Classe PatternDetector:
   - detect_patterns() -> List[Pattern]
   - analyze_skill_combinations() -> List[CombinationPattern]
   - analyze_code_style() -> List[StylePattern]
   - analyze_workflows() -> List[WorkflowPattern]
   - update_confidence(pattern: Pattern, outcome: bool)

2. Pattern Types:

   A. Combination Patterns:
      - Which skills are used together
      - Confidence threshold: 0.8
      - Min occurrences: 10
   
   B. Style Patterns:
      - Naming conventions
      - Import statements
      - Error handling
      - Min samples: 15
   
   C. Workflow Patterns:
      - Commit messages
      - Branch naming
      - Testing approach
      - Min samples: 20

3. Detection Algorithm:
   
   Step 1: Collect samples from usage data
   Step 2: Group by similarity
   Step 3: Calculate frequency
   Step 4: Calculate confidence (success_rate * frequency_weight)
   Step 5: Filter by thresholds
   Step 6: Validate patterns
   Step 7: Save learned patterns

4. Confidence Calculation:
```python
def calculate_confidence(pattern):
    frequency_weight = min(pattern.count / 50, 1.0)  # Max at 50 uses
    success_weight = pattern.success_rate
    recency_weight = calculate_recency_bonus(pattern.last_seen)
    
    confidence = (
        frequency_weight * 0.4 +
        success_weight * 0.4 +
        recency_weight * 0.2
    )
    return confidence
```

5. Pattern Application:
   - When to suggest patterns
   - How to apply to skills
   - User notification
   - Opt-out per pattern

6. Pattern Decay:
   - Confidence decreases over time
   - Removed if not reinforced
   - Decay rate: 10% per month

Test: tests/test_pattern_detector.py

Lunghezza: ~400 righe + 120 righe test"
```

**File da creare:** `analyzers/pattern_detector.py`

---

## Fase 5: Pattern Learning

### 5.1 Implementare Learning Pipeline

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/learning_pipeline.py - orchestrates pattern learning.

Requirements:

1. Classe LearningPipeline:
   - run_learning_cycle()
   - collect_data()
   - analyze_patterns()
   - apply_patterns()
   - notify_user()

2. Learning Cycle (Background):
   
   Trigger: After N uses (default: 10)
   
   Step 1: Collect usage data
   Step 2: Run pattern detection
   Step 3: Validate patterns
   Step 4: Check confidence thresholds
   Step 5: Apply high-confidence patterns
   Step 6: Update skills
   Step 7: Notify user of changes
   Step 8: Save state

3. Pattern Application:
   
   For each learned pattern:
   - Determine affected skills
   - Generate updates
   - Validate changes
   - Apply to SKILL.md
   - Track application

4. User Notification:
```python
notification = {
    "type": "pattern_learned",
    "timestamp": "2025-10-22T10:00:00Z",
    "pattern": {
        "name": "always_use_zod",
        "description": "Always use Zod for validation",
        "confidence": 0.92,
        "based_on": 23
    },
    "applied_to": ["nextjs-fullstack", "react-spa"],
    "action": "skill_updated"
}
```

5. Opt-Out:
   - User can disable learning
   - User can reject specific patterns
   - User can rollback changes

6. Safety:
   - Never apply patterns < 0.8 confidence
   - Always backup before changes
   - Validate after application
   - Rollback on error

Test: tests/test_learning_pipeline.py

Lunghezza: ~350 righe + 100 righe test"
```

**File da creare:** `analyzers/learning_pipeline.py`

### 5.2 Skill Optimizer

**PROMPT PER CLAUDE CODE:**
```
"Crea analyzers/skill_optimizer.py - ottimizza skills esistenti.

Requirements:

1. Classe SkillOptimizer:
   - optimize_all_skills()
   - optimize_skill(skill_path: Path)
   - find_redundancies()
   - suggest_merges()
   - update_documentation()

2. Optimization Strategies:
   
   A. Remove Redundancies:
      - Find duplicate content
      - Find overlapping instructions
      - Suggest consolidation
   
   B. Merge Similar Skills:
      - Find skills with >70% overlap
      - Suggest merging
      - Preserve unique content
   
   C. Update Documentation:
      - Check for outdated info
      - Fetch latest docs
      - Update examples
   
   D. Token Optimization:
      - Identify verbose sections
      - Compress without losing meaning
      - Prioritize critical content
   
   E. Structure Optimization:
      - Enforce consistent format
      - Improve progressive disclosure
      - Better section organization

3. Analysis Metrics:
   - Token count per skill
   - Overlap percentage
   - Usage frequency
   - Success rate
   - Last update date

4. Optimization Report:
```python
{
    "analyzed": 12,
    "optimizations": [
        {
            "type": "merge",
            "skills": ["react-spa", "react-vite"],
            "reason": "82% content overlap",
            "token_savings": 1200
        },
        {
            "type": "update",
            "skill": "nextjs-fullstack",
            "reason": "Documentation outdated (Next.js 14 → 15)",
            "confidence": 0.95
        }
    ],
    "total_token_savings": 2500
}
```

5. User Interaction:
   - Show optimization suggestions
   - Require confirmation for merges
   - Auto-apply safe updates
   - Provide preview

Test: tests/test_skill_optimizer.py

Lunghezza: ~400 righe + 100 righe test"
```

**File da creare:** `analyzers/skill_optimizer.py`

---

## Fase 6: Comandi Slash

### 6.1 Creare Struttura Comandi

```bash
mkdir -p commands/sf
cd commands/sf

# Creare file per ogni comando
touch wizard.md generate.md analyze.md optimize.md update.md \
      introspect.md list.md status.md config.md reset.md
```

### 6.2 Comando /sf:wizard

**PROMPT PER CLAUDE CODE:**
```
"Crea commands/sf/wizard.md - comando per wizard interattivo.

Formato comando slash per Claude Code:

```markdown
---
name: wizard
description: Launch interactive skill generation wizard. Analyzes your tech stack and generates personalized skills.
---

# /sf:wizard - Interactive Skill Generation Wizard

## Purpose
Interactive wizard that guides you through generating personalized skills for your tech stack.

## When to Use
- First time setup
- Adding new tech stack
- Onboarding new project
- User requests setup/configuration

## Behavior

### Step 1: Welcome & Auto-Detection
- Greet user
- Explain what wizard will do
- Auto-detect tech stack from current directory
- Show detected technologies
- Ask for confirmation

### Step 2: Interactive Questionnaire
Ask questions about:
1. Role (Developer type)
2. Frontend framework
3. UI library
4. State management
5. Backend framework
6. Database
7. Auth provider
8. Testing tools
9. Code style preferences
10. Workflow preferences

### Step 3: Generate Profile
- Show summary of answers
- Ask for confirmation
- Generate user_profile.json
- Save to data/

### Step 4: Generate Skills
For each tech in stack:
- Fetch latest documentation (Context7)
- Generate SKILL.md
- Create supporting files
- Save to ~/.claude/skills/

### Step 5: Completion
- Show list of generated skills
- Explain next steps
- Suggest restart Claude Code

## Implementation

When user runs `/sf:wizard`:

```python
# Pseudocode
wizard = WizardEngine()
profile = wizard.run()

if profile["setup_completed"]:
    skills_to_generate = wizard.determine_skills(profile)
    
    for skill_type in skills_to_generate:
        generator = SkillGenerator()
        skill_path = generator.generate(profile, skill_type)
        print(f"✅ Generated: {skill_path}")
    
    print("\n🎉 Setup complete! Restart Claude Code to activate skills.")
else:
    print("❌ Setup cancelled.")
```

## Error Handling
- User interrupts → Save state, allow resume
- Network error → Use cached docs
- Generation fails → Rollback, show error

## Example Usage

User: `/sf:wizard`

Output:
```
🧙 SkillForge Setup Wizard
═══════════════════════════════════════

I'll help you create personalized skills for your tech stack.

📍 Auto-detected in current directory:
  ✓ Next.js 15.0.0 (package.json)
  ✓ Tailwind CSS (tailwind.config.js)
  ✓ TypeScript (tsconfig.json)

Is this correct? [Y/n] 

...
```

## Related Commands
- `/sf:generate` - Generate specific skill
- `/sf:update` - Update existing skills
- `/sf:list` - List generated skills
```

Lunghezza: ~250 righe"
```

**File da creare:** `commands/sf/wizard.md`

### 6.3 Comando /sf:generate

**PROMPT PER CLAUDE CODE:**
```
"Crea commands/sf/generate.md - genera skill specifica.

Struttura:

---
name: generate
description: Generate a specific skill without running full wizard. Syntax: /sf:generate <skill-type> [options]
---

# /sf:generate - Generate Specific Skill

## Purpose
Generate a single skill without going through full wizard.

## Syntax
```
/sf:generate <skill-type> [--force] [--preview]
```

## Skill Types
- nextjs-fullstack
- react-spa
- python-api
- supabase-integration
- git-workflow
- testing-suite
- deployment-pipeline

## Options
- `--force` - Overwrite existing skill
- `--preview` - Show what would be generated without creating files
- `--no-docs` - Skip documentation fetching (use cached/builtin)

## Behavior

1. Validate skill type
2. Check if already exists
3. Load user profile
4. Fetch documentation (if needed)
5. Generate SKILL.md
6. Create supporting files
7. Validate output
8. Show summary

## Examples

Generate Next.js skill:
```
/sf:generate nextjs-fullstack
```

Preview without creating:
```
/sf:generate react-spa --preview
```

Force overwrite existing:
```
/sf:generate supabase-integration --force
```

## Error Handling
- Unknown skill type → Show available types
- Missing profile → Suggest /sf:wizard
- Already exists → Ask for confirmation or suggest --force

Lunghezza: ~200 righe"
```

**File da creare:** `commands/sf/generate.md`

### 6.4 Comando /sf:analyze

**PROMPT PER CLAUDE CODE:**
```
"Crea commands/sf/analyze.md - analizza skills e usage.

Struttura:

---
name: analyze
description: Analyze current skills, usage patterns, and optimization opportunities
---

# /sf:analyze - Analyze Skills & Usage

## Purpose
Comprehensive analysis of:
- Existing skills
- Usage patterns
- Optimization opportunities
- Pattern detection
- Health metrics

## Syntax
```
/sf:analyze [--detailed] [--patterns] [--health]
```

## Options
- `--detailed` - Show detailed analysis per skill
- `--patterns` - Focus on learned patterns
- `--health` - Health check for skills

## Output Sections

### 1. Skills Overview
- Total skills installed
- SkillForge-generated vs native
- Last update dates
- Token usage

### 2. Usage Statistics
- Most used skills
- Success rates
- Common combinations
- Trend analysis

### 3. Learned Patterns
- Detected patterns
- Confidence levels
- Application status

### 4. Optimization Opportunities
- Redundancies found
- Merge suggestions
- Update recommendations
- Token savings potential

### 5. Health Check
- Outdated documentation
- Broken links
- Invalid YAML
- Missing dependencies

## Example Output
```
📊 SkillForge Analysis Report
═══════════════════════════════════════

Skills Overview:
  Total Skills: 8
  SkillForge Generated: 5
  Native Anthropic: 3
  Total Token Usage: ~12,500 tokens

Usage Statistics (Last 30 days):
  Most Used:
    1. nextjs-fullstack (89 uses, 94% success)
    2. supabase-integration (67 uses, 96% success)
    3. git-workflow (45 uses, 100% success)

Learned Patterns (3):
  ✓ always_use_zod (confidence: 0.92, applied)
  ✓ error_boundary_pattern (confidence: 0.88, applied)
  ⏳ feature_colocation (confidence: 0.75, pending)

Optimization Opportunities:
  ⚡ Merge react-spa + react-vite (82% overlap, save 1200 tokens)
  📝 Update nextjs-fullstack (Next.js 14 → 15 available)
  🧹 Remove unused tailwind-setup skill (0 uses in 60 days)

Health: ✅ All skills healthy
```

Lunghezza: ~250 righe"
```

**File da creare:** `commands/sf/analyze.md`

### 6.5 Comandi Rimanenti

Creare gli altri comandi seguendo lo stesso pattern:

```bash
# /sf:optimize
commands/sf/optimize.md

# /sf:update  
commands/sf/update.md

# /sf:introspect
commands/sf/introspect.md

# /sf:list
commands/sf/list.md

# /sf:status
commands/sf/status.md

# /sf:config
commands/sf/config.md

# /sf:reset
commands/sf/reset.md
```

Per ognuno:
1. YAML frontmatter (name, description)
2. Purpose section
3. Syntax/Usage
4. Options
5. Behavior description
6. Examples
7. Error handling

---

## Fase 7: Templates

### 7.1 Template Structure

**PROMPT PER CLAUDE CODE:**
```
"Crea il template base per skills: templates/base-skill.template

Questo è il template master da cui derivano tutti gli altri.

Struttura:

```markdown
---
name: "{{skill_name}}"
description: >
  {{description}}
version: "{{version}}"
author: "SkillForge Auto-Generated"
generated_at: "{{timestamp}}"
based_on: "{{framework_name}} {{framework_version}}"
allowed-tools:
  - bash_tool
  - view
  - create_file
  - str_replace
{{#if additional_tools}}
{{#each additional_tools}}
  - {{this}}
{{/each}}
{{/if}}
---

# {{skill_name}}

## Overview

{{overview}}

## When to Use

Use this skill when:
{{#each use_cases}}
- {{this}}
{{/each}}

## Prerequisites

{{#each prerequisites}}
- {{this}}
{{/each}}

## Core Concepts

{{#each core_concepts}}
### {{name}}

{{description}}

{{#if code_example}}
```{{language}}
{{code_example}}
```
{{/if}}
{{/each}}

## Best Practices

{{#each best_practices}}
### {{category}}

{{#each items}}
- ✅ **DO**: {{do}}
- ❌ **DON'T**: {{dont}}
{{/each}}
{{/each}}

## Common Patterns

{{#each patterns}}
### {{name}}

**Use Case**: {{use_case}}

**Implementation**:
```{{language}}
{{code}}
```

**Explanation**: {{explanation}}
{{/each}}

## Anti-Patterns

{{#each anti_patterns}}
### {{name}}

❌ **Problem**: {{problem}}

```{{language}}
{{bad_code}}
```

✅ **Solution**: {{solution}}

```{{language}}
{{good_code}}
```
{{/each}}

## User Conventions

{{#if has_user_conventions}}
Based on your preferences:

{{#each user_conventions}}
- {{this}}
{{/each}}
{{/if}}

## Related Skills

{{#each related_skills}}
- `{{name}}` - {{description}}
{{/each}}

## Resources

{{#each resources}}
- [{{title}}]({{url}})
{{/each}}

## Version History

- {{version}} ({{timestamp}}): Initial generation
```

Variables esperadas:
- skill_name
- description
- framework_name
- framework_version
- overview
- use_cases (array)
- prerequisites (array)
- core_concepts (array of objects)
- best_practices (array)
- patterns (array)
- anti_patterns (array)
- user_conventions (array)
- related_skills (array)
- resources (array)

Lunghezza: ~200 righe template"
```

**File da creare:** `templates/base-skill.template`

### 7.2 Next.js Template

**PROMPT PER CLAUDE CODE:**
```
"Crea templates/tech-stack/nextjs-fullstack.template

Basato su base-skill.template ma con specifiche Next.js.

Include:

1. App Router patterns
2. Server Components
3. Client Components
4. Route Handlers
5. Metadata API
6. Image optimization
7. Font optimization
8. Middleware
9. Error handling
10. Loading states

Sections specifiche:

## Routing Patterns
- App Router structure
- Dynamic routes
- Route groups
- Parallel routes
- Intercepting routes

## Component Patterns
- Server Component (default)
- Client Component ('use client')
- When to use each
- Props passing
- Children pattern

## Data Fetching
- Server-side fetch
- Client-side (React Query)
- Caching strategies
- Revalidation
- Streaming

## State Management
- URL state (searchParams)
- Server state
- Client state ({{state_library}})  # User's preference

## Styling
- {{ui_library}} integration  # User's choice
- CSS Modules
- Tailwind CSS
- Global styles

## API Routes
- Route Handler pattern
- Request/Response
- Error handling
- Middleware
- Auth

## Best Practices Section
Deve includere:
- ✅ Use Server Components by default
- ✅ Mark 'use client' only when needed
- ✅ Colocate components with routes
- ❌ Don't use getServerSideProps (Pages Router)
- ❌ Don't fetch on client if not needed

## User Conventions
{{#if user_conventions.naming}}
- File naming: {{user_conventions.naming.files}}
- Component naming: {{user_conventions.naming.components}}
{{/if}}

{{#if user_conventions.structure}}
- Directory structure: {{user_conventions.structure}}
{{/if}}

Code examples devono essere COMPLETI e FUNZIONANTI.

Lunghezza: ~800 righe"
```

**File da creare:** `templates/tech-stack/nextjs-fullstack.template`

### 7.3 Altri Template Tech Stack

Creare template per:

1. **React SPA**: `templates/tech-stack/react-spa.template`
   - Vite setup
   - React Router
   - State management
   - Build optimization

2. **Python FastAPI**: `templates/tech-stack/python-api.template`
   - Project structure
   - Async patterns
   - Database integration
   - Authentication

3. **Supabase**: `templates/tech-stack/supabase-integration.template`
   - Auth
   - Database
   - Storage
   - Real-time

### 7.4 Workflow Templates

**PROMPT PER CLAUDE CODE:**
```
"Crea templates/workflow/git-workflow.template

Template per Git workflow personalized.

Include:

## Commit Message Format
{{commit_format}}

Examples:
- feat(auth): add Google OAuth integration
- fix(api): resolve CORS issue in production
- docs(readme): update installation instructions

## Branch Naming
{{branch_format}}

Examples:
- feature/user-authentication
- bugfix/api-cors-error
- hotfix/production-crash

## PR Description Template
```markdown
## Changes
- 

## Testing
- 

## Screenshots (if applicable)

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No console errors
```

## Code Review Checklist
{{#each review_checklist}}
- [ ] {{this}}
{{/each}}

Lunghezza: ~300 righe"
```

**File da creare:** `templates/workflow/git-workflow.template`

---

## Fase 8: Testing & Validation

### 8.1 Test Suite Setup

```bash
# Struttura test
mkdir -p tests/{unit,integration,e2e}

# Configurazione pytest
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=generators
    --cov=analyzers
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
EOF
```

### 8.2 Unit Tests

**PROMPT PER CLAUDE CODE:**
```
"Crea test suite completa in tests/unit/

Files da creare:

1. test_config.py
   - Test Config class
   - Directory creation
   - Profile load/save
   - Analytics load/save

2. test_wizard_engine.py
   - Test question flow
   - Test auto-detection
   - Test validation
   - Test profile generation

3. test_skill_generator.py
   - Test template loading
   - Test variable substitution
   - Test SKILL.md generation
   - Test validation

4. test_template_processor.py
   - Test variable processing
   - Test conditionals
   - Test loops
   - Test includes

5. test_intent_analyzer.py
   - Test entity extraction
   - Test action detection
   - Test domain classification
   - Test complexity assessment

6. test_skill_discovery.py
   - Test skill loading
   - Test discovery strategies
   - Test filtering
   - Test priority sorting

7. test_usage_tracker.py
   - Test usage recording
   - Test statistics
   - Test data persistence

8. test_pattern_detector.py
   - Test pattern detection
   - Test confidence calculation
   - Test pattern application

Ogni test file deve avere:
- Setup/teardown fixtures
- Test data fixtures
- Mock external dependencies
- Clear test names
- Assertions con messaggi
- Edge cases
- Error cases

Coverage target: >80%

Esempio struttura:
```python
import pytest
from unittest.mock import Mock, patch
from generators.skill_generator import SkillGenerator

@pytest.fixture
def sample_profile():
    return {
        "tech_stack": {
            "frontend": "Next.js",
            "ui": "Tailwind CSS"
        }
    }

@pytest.fixture
def generator():
    return SkillGenerator()

def test_generate_skill_success(generator, sample_profile):
    \"\"\"Test successful skill generation\"\"\"
    with patch('generators.doc_fetcher.DocFetcher.fetch') as mock_fetch:
        mock_fetch.return_value = "mock docs"
        
        result = generator.generate_skill(sample_profile, "nextjs")
        
        assert result.exists()
        assert result.name == "SKILL.md"

def test_generate_skill_invalid_type(generator, sample_profile):
    \"\"\"Test error handling for invalid skill type\"\"\"
    with pytest.raises(ValueError, match="Unknown skill type"):
        generator.generate_skill(sample_profile, "invalid")
```
"
```

### 8.3 Integration Tests

**PROMPT PER CLAUDE CODE:**
```
"Crea integration tests in tests/integration/

Test end-to-end flows:

1. test_wizard_to_generation.py
   - Run wizard
   - Generate skills
   - Validate output
   - Check file system

2. test_skill_lifecycle.py
   - Generate skill
   - Use skill
   - Track usage
   - Detect patterns
   - Update skill

3. test_orchestration_flow.py
   - Analyze intent
   - Discover skills
   - Load skills
   - Track usage

4. test_learning_cycle.py
   - Generate usage data
   - Detect patterns
   - Apply patterns
   - Validate updates

Use real file system (in temp dir):
```python
import tempfile
import pytest
from pathlib import Path

@pytest.fixture
def temp_skillforge_home(tmp_path):
    \"\"\"Create temporary SkillForge home\"\"\"
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)
    
    # Override Config paths
    from generators.config import Config
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache"
    Config.ensure_directories()
    
    yield home
    
    # Cleanup handled by tmp_path fixture

def test_full_generation_flow(temp_skillforge_home):
    \"\"\"Test complete flow from wizard to skill usage\"\"\"
    # ... test implementation
```
"
```

### 8.4 E2E Tests

**PROMPT PER CLAUDE CODE:**
```
"Crea e2e tests in tests/e2e/

Simulate real user scenarios:

1. test_first_time_setup.py
   - Fresh install
   - Run wizard
   - Generate skills
   - Verify Claude Code can load them

2. test_daily_usage.py
   - Use skills multiple times
   - Check tracking works
   - Verify pattern detection

3. test_skill_update.py
   - Skill becomes outdated
   - Run update command
   - Verify new version

4. test_optimization.py
   - Create redundant skills
   - Run optimize
   - Verify suggestions

Mark as slow:
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_first_time_setup():
    \"\"\"Complete first-time setup flow\"\"\"
    # This test takes 30+ seconds
    ...
```

Run separately:
```bash
pytest tests/e2e/ -m e2e -v
```
"
```

### 8.5 Test Utilities

```python
# File: tests/conftest.py
"""
Shared pytest fixtures and utilities
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

@pytest.fixture
def temp_home(tmp_path):
    """Create temporary SkillForge home"""
    home = tmp_path / ".claude" / "skills" / "skillforge"
    home.mkdir(parents=True)
    
    from generators.config import Config
    Config.SKILLFORGE_HOME = home
    Config.DATA_DIR = home / "data"
    Config.CACHE_DIR = Config.DATA_DIR / "cache"
    Config.ensure_directories()
    
    return home

@pytest.fixture
def sample_profile() -> Dict[str, Any]:
    """Sample user profile"""
    return {
        "setup_completed": True,
        "tech_stack": {
            "frontend": "Next.js",
            "ui": "Tailwind CSS",
            "state": "Zustand",
            "backend": "Next.js API Routes",
            "database": "Supabase"
        },
        "preferences": {
            "naming": "camelCase",
            "testing": "Vitest"
        }
    }

@pytest.fixture
def sample_usage_data() -> Dict[str, Any]:
    """Sample usage analytics"""
    return {
        "skill_usage": {
            "nextjs-fullstack": {
                "total_uses": 50,
                "successes": 47,
                "failures": 3,
                "common_with": ["supabase-integration"]
            }
        }
    }

def create_mock_skill(path: Path, name: str):
    """Create a mock SKILL.md file"""
    content = f"""---
name: "{name}"
description: "Mock skill for testing"
---

# {name}

Mock content.
"""
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(content)
```

### 8.6 Run All Tests

```bash
# Script per run tests
cat > scripts/run-tests.sh << 'EOF'
#!/bin/bash

echo "🧪 Running SkillForge Test Suite..."
echo ""

# Unit tests
echo "1️⃣ Running unit tests..."
pytest tests/unit/ -v --cov=generators --cov=analyzers --cov-report=html
unit_result=$?

# Integration tests
echo ""
echo "2️⃣ Running integration tests..."
pytest tests/integration/ -v
integration_result=$?

# E2E tests (optional, slow)
if [ "$1" == "--full" ]; then
    echo ""
    echo "3️⃣ Running E2E tests..."
    pytest tests/e2e/ -v -m e2e
    e2e_result=$?
else
    echo ""
    echo "⏭️  Skipping E2E tests (use --full to run)"
    e2e_result=0
fi

# Summary
echo ""
echo "📊 Test Summary:"
echo "  Unit Tests: $([ $unit_result -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "  Integration: $([ $integration_result -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
if [ "$1" == "--full" ]; then
    echo "  E2E Tests: $([ $e2e_result -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
fi

# Exit code
if [ $unit_result -eq 0 ] && [ $integration_result -eq 0 ] && [ $e2e_result -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    exit 0
else
    echo ""
    echo "❌ Some tests failed"
    exit 1
fi
EOF

chmod +x scripts/run-tests.sh

# Run
./scripts/run-tests.sh
```

---

## Fase 9: Documentation

### 9.1 README.md

**PROMPT PER CLAUDE CODE:**
```
"Crea README.md principale del progetto.

Sections:

# SkillForge

> Meta-programming framework for Claude Code skills

## 🎯 What is SkillForge?

SkillForge transforms Claude Code into an intelligent development partner by:
- Generating personalized skills for YOUR tech stack
- Orchestrating multiple skills intelligently  
- Learning from your patterns and preferences
- Keeping skills updated automatically

## ✨ Key Features

- 🧙 **Interactive Wizard** - Setup in 5 minutes
- 🎯 **Smart Orchestration** - Automatic skill coordination
- 🧠 **Pattern Learning** - Improves over time
- 📚 **Always Updated** - Fetches latest docs via Context7
- ⚡ **Token Optimized** - Progressive disclosure
- 🔧 **Customizable** - Adapts to your conventions

## 🚀 Quick Start

```bash
# Install SkillForge
pipx install skillforge

# Run setup wizard
skillforge install
/sf:wizard

# That's it! Restart Claude Code and your skills are active.
```

## 📖 How It Works

1. **Setup**: Run wizard, answer questions about your stack
2. **Generation**: SkillForge generates personalized skills
3. **Usage**: Claude Code uses skills automatically
4. **Learning**: SkillForge learns from your patterns
5. **Evolution**: Skills improve over time

## 🎓 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Command Reference](docs/COMMANDS.md)
- [Template Guide](docs/TEMPLATES.md)
- [API Documentation](docs/API.md)

## 🔧 Commands

- `/sf:wizard` - Setup wizard
- `/sf:generate <type>` - Generate specific skill
- `/sf:analyze` - Analyze skills and usage
- `/sf:optimize` - Optimize existing skills
- `/sf:update` - Update skills with latest docs

## 📊 Example

Before SkillForge:
```
You: "Create a Next.js login component"
Claude: Uses generic knowledge, may be outdated
```

After SkillForge:
```
You: "Create a Next.js login component"
Claude: 
  ✓ Loads nextjs-fullstack skill (your conventions)
  ✓ Loads supabase-integration skill
  ✓ Creates component with YOUR patterns
  ✓ Follows YOUR naming conventions
  ✓ Uses YOUR preferred libraries
  ✓ Result: Perfect, consistent code
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- Anthropic for Claude Code
- SuperClaude for inspiration
- Community contributors

Lunghezza: ~300 righe"
```

### 9.2 Documentation Files

Creare:

1. **docs/QUICKSTART.md** - Getting started guide
2. **docs/ARCHITECTURE.md** - Technical architecture
3. **docs/COMMANDS.md** - All commands reference
4. **docs/TEMPLATES.md** - Template creation guide
5. **docs/API.md** - Python API documentation
6. **docs/CONTRIBUTING.md** - Contribution guidelines
7. **docs/FAQ.md** - Frequently asked questions
8. **docs/TROUBLESHOOTING.md** - Common issues

Per ognuno, usare Claude Code con prompt specifici.

### 9.3 Code Documentation

```bash
# Generate API docs con pydoc o sphinx
pip install sphinx sphinx-rtd-theme

# Setup sphinx
sphinx-quickstart docs/api

# Configurare per auto-generate da docstrings
# ... configurazione ...

# Generate docs
cd docs/api
make html

# Docs disponibili in docs/api/_build/html/
```

---

## Fase 10: Release & Distribution

### 10.1 Package Preparation

```bash
# Verificare struttura finale
tree -L 2 ~/.claude/skills/skillforge/

# Output dovrebbe essere:
# skillforge/
# ├── SKILL.md
# ├── core/
# │   ├── SKILLFORGE.md
# │   ├── ORCHESTRATION.md
# │   ├── GENERATOR.md
# │   ├── PATTERNS.md
# │   ├── RULES.md
# │   ├── WORKFLOWS.md
# │   └── MCP_INTEGRATION.md
# ├── commands/
# │   └── sf/
# ├── generators/
# ├── templates/
# ├── analyzers/
# ├── data/
# └── docs/
```

### 10.2 Installer Script

**PROMPT PER CLAUDE CODE:**
```
"Crea install.sh - installer script per SkillForge.

Requirements:

1. Detect OS (Linux/Mac/Windows WSL)
2. Check prerequisites (Python, Claude Code)
3. Install Python package
4. Copy files to ~/.claude/skills/skillforge/
5. Create data directories
6. Run initial setup
7. Test installation
8. Show next steps

```bash
#!/bin/bash

set -e

echo "🔨 SkillForge Installer"
echo "======================="
echo ""

# 1. Check prerequisites
echo "Checking prerequisites..."

# Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"

# Claude Code
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude Code not found in PATH"
    echo "   Make sure Claude Code is installed"
fi

# 2. Install Python package
echo ""
echo "Installing SkillForge package..."
pipx install skillforge || pip install --user skillforge

# 3. Copy files
echo ""
echo "Installing skills to ~/.claude/skills/skillforge/..."
SKILL_DIR="$HOME/.claude/skills/skillforge"
mkdir -p "$SKILL_DIR"

# Copy all files
cp -r ./* "$SKILL_DIR/"

# 4. Create data directories
echo "Creating data directories..."
mkdir -p "$SKILL_DIR/data/cache/context7"

# 5. Test installation
echo ""
echo "Testing installation..."
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo "✅ SKILL.md installed"
else
    echo "❌ SKILL.md missing"
    exit 1
fi

# 6. Success
echo ""
echo "✅ SkillForge installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code"
echo "  2. Run: /sf:wizard"
echo "  3. Follow the setup wizard"
echo ""
echo "Documentation: https://github.com/your-org/skillforge"
```

Lunghezza: ~150 righe"
```

**File da creare:** `install.sh`

### 10.3 PyPI Package

```bash
# Setup for PyPI
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="skillforge",
    version="1.0.0",
    author="SkillForge Team",
    author_email="team@skillforge.dev",
    description="Meta-programming framework for Claude Code skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/skillforge",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/skillforge/issues",
        "Documentation": "https://skillforge.dev/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "skillforge=generators.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.template", "*.md", "*.yml"],
    },
)
EOF

# Build package
python setup.py sdist bdist_wheel

# Test locally
pip install dist/skillforge-1.0.0-py3-none-any.whl

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ skillforge

# If all good, upload to PyPI
twine upload dist/*
```

### 10.4 GitHub Repository

```bash
# Create .github/workflows/
mkdir -p .github/workflows

# CI/CD pipeline
cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=generators --cov=analyzers
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
EOF

# Release workflow
cat > .github/workflows/release.yml << 'EOF'
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Build package
      run: |
        pip install build twine
        python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
      run: |
        twine upload dist/*
    
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
EOF
```

### 10.5 Release Checklist

```markdown
# SkillForge v1.0.0 Release Checklist

## Pre-Release
- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] Documentation complete
- [ ] Examples working
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] LICENSE file present

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing on fresh install
- [ ] Testing on Linux
- [ ] Testing on macOS
- [ ] Testing on Windows WSL

## Documentation
- [ ] README.md complete
- [ ] QUICKSTART.md clear
- [ ] All commands documented
- [ ] API docs generated
- [ ] Examples validated

## Package
- [ ] setup.py correct
- [ ] MANIFEST.in includes all files
- [ ] Build succeeds
- [ ] Test install from wheel
- [ ] Test import in Python

## Distribution
- [ ] Upload to TestPyPI
- [ ] Test install from TestPyPI
- [ ] Upload to PyPI
- [ ] Test install from PyPI: `pipx install skillforge`
- [ ] GitHub release created
- [ ] Release notes published

## Announcement
- [ ] Blog post (if applicable)
- [ ] Social media announcement
- [ ] Community notification
- [ ] Claude Code community

## Post-Release
- [ ] Monitor for issues
- [ ] Respond to early feedback
- [ ] Update documentation based on questions
- [ ] Plan v1.1.0 features
```

---

## 📊 Timeline Estimation

### Week 1-2: Foundation
- Fase 0: Setup (2 days)
- Fase 1: Base structure (3 days)
- Fase 2: Core files (5 days)

### Week 3-4: Generation System
- Fase 3: Generation (7 days)

### Week 5-6: Intelligence
- Fase 4: Orchestration (5 days)
- Fase 5: Learning (5 days)

### Week 7: Commands & Templates
- Fase 6: Slash commands (3 days)
- Fase 7: Templates (4 days)

### Week 8: Quality
- Fase 8: Testing (5 days)

### Week 9: Polish
- Fase 9: Documentation (3 days)
- Fase 10: Release prep (2 days)

**Total**: ~9 weeks (2 mesi)

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ Test coverage > 80%
- ✅ All core files complete
- ✅ 10+ templates available
- ✅ All commands working
- ✅ Context7 integration working

### Quality Metrics
- ✅ Generated skills are valid
- ✅ Skills load in Claude Code
- ✅ Orchestration works correctly
- ✅ Pattern learning functional
- ✅ Documentation comprehensive

### User Metrics
- ✅ Setup takes < 10 minutes
- ✅ Generated code is high-quality
- ✅ Skills improve over time
- ✅ Token usage optimized
- ✅ Positive user feedback

---

## 🚀 Next Steps After v1.0

### v1.1 - Community
- Skill marketplace
- Share skills with team
- Import/export profiles

### v1.2 - AI Improvements
- Better pattern detection
- Auto-optimization
- Predictive loading

### v1.3 - Integrations
- More MCP servers
- IDE extensions
- CI/CD integration

---

## 📚 Additional Resources

### During Development

**Use Claude Code intensively!**

Every fase, usa questi pattern:

```
"Claude, read the research documents in docs/research/ and 
implement [component] following the patterns we've established.
Use the architecture in docs/ARCHITECTURE.md as reference."
```

```
"Claude, generate comprehensive tests for [module] covering:
- Happy paths
- Edge cases  
- Error scenarios
- Integration scenarios"
```

```
"Claude, review this code and suggest improvements based on:
- Python best practices
- Our project patterns
- Performance optimization
- Error handling"
```

### Learning Resources

- Claude Code Documentation
- SuperClaude GitHub
- Context7 MCP Documentation
- Python Best Practices
- Template Design Patterns

---

## 🎉 Conclusion

This roadmap provides a complete path from zero to a fully functional SkillForge v1.0. The key is to:

1. **Use Claude Code to build SkillForge** - meta! 
2. **Test continuously** - every component
3. **Document everything** - for users and developers
4. **Iterate based on feedback** - improve constantly

**Remember**: SkillForge is about making Claude Code better at understanding YOUR way of working. Every decision should optimize for that goal.

Good luck building! 🚀

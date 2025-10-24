# 🔨 SkillForge - Briefing Completo del Progetto

**Meta-Programming Framework per Claude Code Skills**

---

## 📌 Executive Summary

SkillForge è un framework di meta-programmazione intelligente che trasforma Claude Code da assistente AI generico in un membro esperto del team di sviluppo, specializzato nel TUO stack tecnologico, che segue le TUE convenzioni, e migliora continuamente imparando dai TUOI pattern di lavoro.

**In una frase**: SkillForge genera, orchestra e ottimizza automaticamente le skills di Claude Code per renderlo perfettamente allineato al tuo modo di lavorare.

---

## 🎯 Il Problema che Risolviamo

### Situazione Attuale con Claude Code

Claude Code ha un sistema di **Skills nativo** potente ma con limitazioni:

```
~/.claude/skills/
├── public/                    # Skills ufficiali Anthropic
│   ├── docx/                 # Creare Word docs
│   ├── pptx/                 # Creare presentazioni
│   ├── xlsx/                 # Creare Excel
│   └── pdf/                  # Manipolare PDF
│
└── user/                      # Skills personalizzate
    └── (vuoto o manuale)
```

**Problemi:**

1. **Skills Generiche**
   - Le skills ufficiali sono generiche per tutti
   - Non sanno nulla del TUO stack (Next.js? FastAPI? Supabase?)
   - Non conoscono le TUE convenzioni (naming, structure, patterns)

2. **Nessuna Orchestrazione Intelligente**
   - Claude deve indovinare quali skills usare
   - Può caricare troppe skills (spreco token)
   - Può caricare poche skills (risultato mediocre)
   - Nessuna coordinazione tra skills multiple

3. **Nessuna Memoria**
   - Ogni sessione Claude ricomincia da zero
   - Non ricorda cosa hai fatto ieri
   - Non impara dai tuoi pattern
   - Non sa le tue preferenze

4. **Skills Statiche**
   - Le skills non si aggiornano
   - Documentation può diventare obsoleta
   - Nessun miglioramento nel tempo

5. **Creazione Manuale**
   - Creare skills custom richiede expertise
   - Devi scrivere SKILL.md manualmente
   - Devi mantenere la documentazione aggiornata
   - Time-consuming e error-prone

### Esempio Concreto del Problema

**Scenario**: Vuoi creare un componente di login con Next.js e Supabase.

**Senza SkillForge:**
```
Tu: "Crea un componente login con Next.js e Supabase"

Claude Code:
├─ Usa conoscenza generica (forse obsoleta)
├─ Non sa se usi App Router o Pages Router
├─ Non sa se usi Tailwind o altra UI library
├─ Non sa se usi Zustand, Redux o Context
├─ Genera codice generico
└─ Risultato: OK ma non ottimale, non tuo stile

Devi poi:
├─ Correggere naming conventions
├─ Aggiustare import paths
├─ Modificare styling
├─ Adattare al tuo pattern
└─ Time wasted: 15-30 minuti
```

**Con SkillForge:**
```
Tu: "Crea un componente login con Next.js e Supabase"

SkillForge (invisibile):
├─ Analizza: "login component with Next.js and Supabase"
├─ Identifica skills: nextjs-fullstack + supabase-integration
├─ Carica skills (generate apposta per te)
├─ Claude Code usa skills personalizzate

Claude Code:
├─ Sa che usi Next.js 15 App Router
├─ Sa che usi Shadcn/ui + Tailwind
├─ Sa che usi Zustand per state
├─ Sa le tue naming conventions
├─ Sa la tua folder structure
├─ Genera codice PERFETTO per te
└─ Risultato: Pronto per produzione, 0 modifiche

Time wasted: 0 minuti ✅
```

---

## 💡 La Soluzione: SkillForge

### Cos'è SkillForge

SkillForge è composto da **4 componenti principali**:

```
┌─────────────────────────────────────────────────────────┐
│                     SkillForge                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │   1. Generator   │  │ 2. Orchestrator  │          │
│  │                  │  │                  │          │
│  │  Crea skills     │  │  Coordina skills │          │
│  │  personalizzate  │  │  intelligentemente│          │
│  │  per il tuo      │  │  quando servono   │          │
│  │  stack           │  │                  │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │  3. Learner      │  │  4. Optimizer    │          │
│  │                  │  │                  │          │
│  │  Impara pattern  │  │  Migliora skills │          │
│  │  dal tuo uso     │  │  nel tempo       │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↓                                    ↓
    ~/.claude/skills/              Claude Code usa skills
```

### 1. Generator (Generazione Skills)

**Cosa fa**: Genera skills personalizzate per il tuo stack tecnologico.

**Come funziona**:

```
1. Interactive Wizard
   ↓
   Tu rispondi domande sul tuo stack:
   - Che framework usi? (Next.js, React, Vue...)
   - Che UI library? (Tailwind, Shadcn, Material...)
   - Che state management? (Zustand, Redux...)
   - Che database? (Supabase, PostgreSQL...)
   - Che auth provider? (Supabase Auth, NextAuth...)
   - Ecc...
   
2. Documentation Fetching
   ↓
   Per ogni tecnologia che usi:
   - Fetcha latest documentation (via Context7 MCP)
   - Estrae best practices
   - Estrae esempi di codice
   - Identifica pattern comuni
   
3. Template Processing
   ↓
   Usa templates predefiniti:
   - nextjs-fullstack.template
   - supabase-integration.template
   - git-workflow.template
   - ecc...
   
4. SKILL.md Generation
   ↓
   Genera file SKILL.md completo:
   
   ~/.claude/skills/nextjs-fullstack/
   ├── SKILL.md                    # Skill principale
   │   ├── YAML frontmatter        # Metadata
   │   ├── Best Practices          # Specifici per Next.js 15
   │   ├── Code Examples           # Esempi TUOI pattern
   │   ├── Common Patterns         # Pattern comuni
   │   ├── Anti-Patterns           # Cosa evitare
   │   └── User Conventions        # TUE convenzioni
   │
   ├── scripts/                    # Python scripts helper
   │   ├── create_component.py
   │   └── setup_route.py
   │
   ├── templates/                  # Code templates
   │   ├── component.tsx.template
   │   ├── page.tsx.template
   │   └── api-route.ts.template
   │
   └── docs/                       # Reference docs
       └── nextjs-15-patterns.md

5. Validation
   ↓
   - Valida YAML frontmatter
   - Valida structure
   - Testa che skill funzioni
   - Salva in ~/.claude/skills/
```

**Risultato**: Hai skills personalizzate che Claude Code può usare automaticamente.

### 2. Orchestrator (Orchestrazione Intelligente)

**Cosa fa**: Coordina l'uso di multiple skills in modo intelligente.

**Come funziona**:

```
User Request
    ↓
┌─────────────────────────────────────────────┐
│     Intent Analysis                         │
│  ├─ Entities: [Next.js, Supabase, login]  │
│  ├─ Action: create                         │
│  ├─ Domain: fullstack                      │
│  └─ Complexity: moderate                   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Skill Discovery                         │
│  Trova skills rilevanti:                   │
│  ├─ nextjs-fullstack (direct match)       │
│  ├─ supabase-integration (direct match)   │
│  ├─ shadcn-ui (dependency)                │
│  └─ typescript-config (dependency)        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Priority Sorting                        │
│  Ordina per importanza:                    │
│  1. nextjs-fullstack (critical)           │
│  2. supabase-integration (high)           │
│  3. shadcn-ui (medium)                    │
│  4. typescript-config (low)               │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Token Budget Allocation                 │
│  Budget: 5000 tokens                       │
│  ├─ nextjs-fullstack: 2000 tokens (full)  │
│  ├─ supabase-integration: 1500 (full)     │
│  ├─ shadcn-ui: 800 tokens (core)          │
│  └─ typescript-config: 200 (summary)      │
│  Total: 4500 tokens (within budget)       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Progressive Loading                     │
│  Carica skills in 3 livelli:               │
│  Level 1 (Metadata): Tutte le skills       │
│  Level 2 (Core): Skills critiche           │
│  Level 3 (Full): Solo quando serve         │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Execution                               │
│  Claude Code esegue con skills caricate    │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Usage Tracking                          │
│  Traccia per learning:                     │
│  ├─ Skills usate                           │
│  ├─ Combinazioni                           │
│  ├─ Success/failure                        │
│  └─ Execution time                         │
└─────────────────────────────────────────────┘
```

**Vantaggi**:
- ✅ Carica solo skills necessarie (ottimizzazione token)
- ✅ Coordina multiple skills automaticamente
- ✅ Applica best practices automaticamente
- ✅ Risultato coerente e di alta qualità

### 3. Learner (Apprendimento Pattern)

**Cosa fa**: Impara dai tuoi pattern d'uso e adatta le skills di conseguenza.

**Come funziona**:

```
┌─────────────────────────────────────────────┐
│     Data Collection                         │
│  Dopo ogni uso, traccia:                   │
│  ├─ Quali skills usate                     │
│  ├─ Come usate insieme                     │
│  ├─ Risultato (success/failure)           │
│  └─ Tempo impiegato                        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Pattern Detection                       │
│  Dopo 10+ usi, analizza:                   │
│                                             │
│  Pattern trovato:                           │
│  "Sempre usi Zod per validation"           │
│  ├─ Frequenza: 23/25 volte (92%)          │
│  ├─ Consistenza: Alta                     │
│  └─ Confidence: 0.92                      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Pattern Application                     │
│  Se confidence > 0.8, applica:             │
│                                             │
│  Aggiorna nextjs-fullstack/SKILL.md:       │
│  ## User Conventions                       │
│  - ✅ ALWAYS use Zod for validation       │
│  - ✅ ALWAYS use React Query for fetching │
│  - ❌ NEVER use PropTypes                 │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     User Notification                       │
│  "🎉 Pattern learned!                      │
│   I've updated your skills to always use  │
│   Zod for validation (confidence: 92%)."  │
└─────────────────────────────────────────────┘
```

**Tipi di Pattern Appresi**:

1. **Code Style Patterns**
   ```javascript
   // Dopo 20+ usi, SkillForge nota:
   - Naming: camelCase per functions, PascalCase per components
   - Imports: sempre absolute paths con @/ alias
   - Error handling: sempre con Error Boundary
   - Async: sempre async/await, mai .then()
   ```

2. **Workflow Patterns**
   ```bash
   # Commit messages
   "type(scope): message"
   
   # Branch naming
   "feature/description"
   
   # File organization
   "Feature-based colocation"
   ```

3. **Tool Preferences**
   ```
   Sempre usa:
   - Zod (validation)
   - React Query (data fetching)
   - Vitest (testing)
   
   Mai usa:
   - PropTypes
   - fetch diretto
   - class components
   ```

4. **Combination Patterns**
   ```
   Quando usi nextjs-fullstack:
   - 89% delle volte usi anche supabase-integration
   - 67% delle volte usi anche shadcn-ui
   
   → Pre-load these skills together
   ```

**Risultato**: Le tue skills migliorano automaticamente riflettendo il TUO modo di lavorare.

### 4. Optimizer (Ottimizzazione Continua)

**Cosa fa**: Ottimizza skills esistenti per performance e qualità.

**Come funziona**:

```
┌─────────────────────────────────────────────┐
│     Analysis Phase                          │
│  Analizza tutte le skills:                 │
│  ├─ Token usage per skill                  │
│  ├─ Overlap tra skills                     │
│  ├─ Usage frequency                        │
│  ├─ Success rate                           │
│  └─ Last update date                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Optimization Opportunities              │
│                                             │
│  1. Redundancy Detected:                   │
│     react-spa + react-vite hanno 82%       │
│     contenuto uguale                       │
│     → Suggerisci merge (save 1200 tokens)  │
│                                             │
│  2. Outdated Documentation:                │
│     nextjs-fullstack usa Next.js 14        │
│     Latest: Next.js 15                     │
│     → Suggerisci update                    │
│                                             │
│  3. Unused Skills:                         │
│     tailwind-setup non usata da 60 giorni  │
│     → Suggerisci rimozione                 │
│                                             │
│  4. Token Optimization:                    │
│     supabase-integration: 3500 tokens      │
│     Sezioni verbose identificate           │
│     → Compress senza perdere informazioni  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     User Confirmation                       │
│  Mostra report:                            │
│  "Found 3 optimization opportunities       │
│   that could save 2500 tokens.             │
│   Review and apply? [Y/n]"                 │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│     Apply Optimizations                     │
│  ├─ Backup skills originali                │
│  ├─ Applica ottimizzazioni                 │
│  ├─ Valida nuove skills                    │
│  └─ Show results                           │
└─────────────────────────────────────────────┘
```

**Ottimizzazioni Applicate**:

1. **Token Reduction**
   - Rimuove verbosità
   - Comprime esempi ridondanti
   - Mantiene significato
   - Target: -30% tokens mantenendo qualità

2. **Documentation Updates**
   - Auto-fetch latest docs (Context7)
   - Update esempi
   - Update best practices
   - Frequency: settimanale

3. **Skill Merging**
   - Identifica overlap >70%
   - Merge preservando unique content
   - Reduce token budget
   - Improve maintenance

4. **Structure Optimization**
   - Progressive disclosure migliorato
   - Sezioni più chiare
   - Migliore organizzazione
   - Facilitate Claude discovery

---

## 🏗️ Architettura Tecnica

### File System Structure

```
~/.claude/skills/skillforge/
│
├── SKILL.md                           # Entry point (meta-skill)
│
├── core/                              # File comportamentali
│   ├── SKILLFORGE.md                 # Core configuration
│   ├── ORCHESTRATION.md              # Orchestration logic
│   ├── GENERATOR.md                  # Generation system
│   ├── PATTERNS.md                   # Pattern learning
│   ├── RULES.md                      # Behavioral rules
│   ├── WORKFLOWS.md                  # Automated workflows
│   └── MCP_INTEGRATION.md            # MCP integrations
│
├── commands/                          # Slash commands
│   └── sf/
│       ├── wizard.md                 # /sf:wizard
│       ├── generate.md               # /sf:generate
│       ├── analyze.md                # /sf:analyze
│       ├── optimize.md               # /sf:optimize
│       ├── update.md                 # /sf:update
│       └── ...
│
├── generators/                        # Python generators
│   ├── __init__.py
│   ├── config.py                     # Configuration
│   ├── wizard_engine.py              # Interactive wizard
│   ├── skill_generator.py            # Skill generator
│   ├── template_processor.py         # Template engine
│   └── doc_fetcher.py                # Context7 integration
│
├── analyzers/                         # Intelligence
│   ├── __init__.py
│   ├── intent_analyzer.py            # Analyze user requests
│   ├── skill_discovery.py            # Find relevant skills
│   ├── usage_tracker.py              # Track usage
│   ├── pattern_detector.py           # Detect patterns
│   ├── learning_pipeline.py          # Learning cycle
│   └── skill_optimizer.py            # Optimize skills
│
├── templates/                         # Skill templates
│   ├── base-skill.template           # Base template
│   ├── tech-stack/
│   │   ├── nextjs-fullstack.template
│   │   ├── react-spa.template
│   │   ├── python-api.template
│   │   └── supabase-integration.template
│   ├── workflow/
│   │   ├── git-workflow.template
│   │   └── testing-workflow.template
│   └── integration/
│       └── database.template
│
├── data/                              # Persistent data
│   ├── user_profile.json             # User setup
│   ├── usage_analytics.json          # Usage stats
│   ├── learned_patterns.json         # Learned patterns
│   ├── generated_skills.json         # Skills registry
│   └── cache/
│       └── context7/                 # Cached docs
│
└── docs/                              # Documentation
    ├── README.md
    ├── ARCHITECTURE.md
    └── EXAMPLES.md
```

### Sistema di File Comportamentali

SkillForge usa un sistema simile a SuperClaude:

**SKILL.md** (Entry Point)
```markdown
---
name: "SkillForge"
description: "Meta-programming framework..."
allowed-tools: [bash_tool, view, create_file, ...]
---

# SkillForge

Configuration System:
@core/SKILLFORGE.md       # Main config
@core/ORCHESTRATION.md    # How to orchestrate
@core/GENERATOR.md        # How to generate
@core/PATTERNS.md         # How to learn
@core/RULES.md            # Behavioral rules
@core/WORKFLOWS.md        # Workflows
@core/MCP_INTEGRATION.md  # MCP integration

Available Commands:
- /sf:wizard
- /sf:generate
- ...
```

Quando Claude Code carica SkillForge, legge SKILL.md e poi carica progressivamente gli altri file in base al contesto.

### Stack Tecnologico

```
Language:       Python 3.11+
Config Format:  YAML + Markdown
Storage:        JSON (user data)
Integration:    MCP (Context7, Sequential)
Testing:        pytest + pytest-cov
Documentation:  Markdown

Python Packages:
├── pyyaml      # YAML parsing
├── requests    # HTTP requests
├── click       # CLI interface
└── jinja2      # Template engine (optional)
```

### MCP Integration (Context7)

**Context7** è fondamentale per SkillForge:

```python
# Come SkillForge usa Context7

# 1. Resolve Library ID
library_id = context7_resolve_library_id("Next.js")
# Returns: "/vercel/next.js"

# 2. Fetch Documentation
docs = context7_get_library_docs(
    library_id="/vercel/next.js",
    topic="App Router",
    tokens=2000
)

# 3. Parse & Extract
best_practices = extract_best_practices(docs)
code_examples = extract_code_examples(docs)
patterns = extract_patterns(docs)

# 4. Use in Skill Generation
skill_content = generate_skill(
    template="nextjs-fullstack.template",
    documentation=docs,
    best_practices=best_practices,
    code_examples=code_examples,
    user_conventions=user_profile["conventions"]
)
```

---

## 🎯 User Journey Completo

### Primo Setup (Una volta)

```bash
# 1. Installa SkillForge
$ pipx install skillforge
$ skillforge install

# 2. Apri Claude Code
$ claude

# 3. Run wizard
/sf:wizard

═══════════════════════════════════════
🧙 SkillForge Setup Wizard
═══════════════════════════════════════

I'll help you create personalized skills.

📍 Auto-detected in current directory:
  ✓ Next.js 15.0.0 (package.json)
  ✓ Tailwind CSS (tailwind.config.js)
  ✓ TypeScript (tsconfig.json)

Is this correct? [Y/n] Y

Great! Let me ask a few more questions...

1️⃣ What UI library do you use?
   [1] Shadcn/ui
   [2] Material UI
   [3] Chakra UI
   [4] Other
> 1

2️⃣ State management?
   [1] Zustand
   [2] Redux
   [3] Context API
   [4] Jotai
> 1

3️⃣ Backend?
   [1] Next.js API Routes
   [2] Express.js
   [3] FastAPI
> 1

4️⃣ Database?
   [1] Supabase
   [2] PostgreSQL
   [3] MongoDB
> 1

5️⃣ Auth provider?
   [1] Supabase Auth
   [2] NextAuth.js
   [3] Auth0
> 1

... (10 more questions) ...

════════════════════════════════════════
📊 Setup Summary
════════════════════════════════════════

Tech Stack:
  Frontend:  Next.js 15 (App Router)
  UI:        Shadcn/ui + Tailwind CSS
  State:     Zustand
  Backend:   Next.js API Routes
  Database:  Supabase
  Auth:      Supabase Auth
  Testing:   Vitest + Testing Library
  Language:  TypeScript

Skills to generate:
  ✓ nextjs-fullstack
  ✓ supabase-integration
  ✓ shadcn-patterns
  ✓ git-workflow
  ✓ testing-suite

Proceed? [Y/n] Y

════════════════════════════════════════
⚙️  Generating Skills...
════════════════════════════════════════

[1/5] 📦 Fetching Next.js documentation...
      ├─ Context7: /vercel/next.js/latest
      ├─ Topics: App Router, Server Components
      └─ ✅ Documentation fetched

[2/5] 🔨 Generating nextjs-fullstack skill...
      ├─ Processing template
      ├─ Injecting documentation
      ├─ Adding user conventions
      ├─ Creating SKILL.md (2341 lines)
      ├─ Creating scripts/ (3 files)
      ├─ Creating templates/ (5 files)
      └─ ✅ Skill generated

[3/5] 📦 Fetching Supabase documentation...
      └─ ✅ Documentation fetched

[4/5] 🔨 Generating supabase-integration skill...
      └─ ✅ Skill generated

[5/5] 🔨 Generating additional skills...
      ├─ shadcn-patterns ✅
      ├─ git-workflow ✅
      └─ testing-suite ✅

════════════════════════════════════════
✅ Setup Complete!
════════════════════════════════════════

Skills installed:
  ~/.claude/skills/
  ├── nextjs-fullstack/
  ├── supabase-integration/
  ├── shadcn-patterns/
  ├── git-workflow/
  └── testing-suite/

Next steps:
  1. Restart Claude Code: Cmd+Q → claude
  2. Skills will activate automatically
  3. Try: "Create a login component"

Your skills will improve as you use them!
```

### Uso Quotidiano (Automatico)

**Tu non fai nulla di speciale** - SkillForge lavora in background.

```
Tu: "Create a login component with Supabase auth"

SkillForge (invisibile, in millisecondi):
├─ Analizza intent: "login component, Supabase, auth"
├─ Identifica skills: nextjs-fullstack + supabase-integration
├─ Carica skills (3500 tokens)
├─ Claude riceve context perfetto
└─ Traccia uso per learning

Claude Code:
├─ Legge nextjs-fullstack skill:
│   - App Router pattern
│   - Server Component
│   - 'use client' quando necessario
│   - Shadcn/ui components
│   - Zustand per state
│   - TUE naming conventions
│   - TUA folder structure
│
├─ Legge supabase-integration skill:
│   - Auth setup
│   - signIn / signOut methods
│   - Session management
│   - Error handling
│   - TypeScript types
│
└─ Genera componente:

File: app/(auth)/login/page.tsx
```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthStore } from '@/lib/store/auth'
import { supabase } from '@/lib/supabase/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const setUser = useAuthStore((state) => state.setUser)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsLoading(true)

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error
      
      setUser(data.user)
      router.push('/dashboard')
    } catch (error) {
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 rounded-lg border p-8">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Welcome back</h1>
          <p className="text-gray-500">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </div>
    </div>
  )
}
```

✅ 100% tuo stile
✅ Shadcn/ui components
✅ Zustand store
✅ Supabase auth
✅ Error handling
✅ Loading states
✅ TypeScript types
✅ Tailwind styling
✅ Folder structure corretta
✅ 0 modifiche necessarie
```

### Dopo 2 Settimane (Learning)

SkillForge ha tracciato il tuo uso:

```
📊 Usage Summary (14 giorni)

Skills Usage:
  nextjs-fullstack:       47 uses (96% success)
  supabase-integration:   38 uses (95% success)
  shadcn-patterns:        22 uses (100% success)

Patterns Detected:

✅ Code Style Pattern (confidence: 0.94)
   "Always use Zod for form validation"
   Detected in: 23/25 form components
   
   Action: Updated nextjs-fullstack skill
   Added: "✅ ALWAYS use Zod for validation"

✅ Workflow Pattern (confidence: 0.89)
   "Feature-based colocation"
   Detected in: 18/20 new features
   
   Action: Updated folder structure recommendations

⏳ Emerging Pattern (confidence: 0.72)
   "Prefer server actions over API routes"
   Detected in: 12/17 data mutations
   
   Action: Monitoring (need 3 more samples for 0.8 threshold)

Your skills have been updated to reflect your preferences! 🎉
```

### Dopo 1 Mese (Optimization)

```
/sf:analyze

📊 SkillForge Analysis Report
═══════════════════════════════════════

Skills Overview:
  Total: 8 skills
  SkillForge: 5
  Native: 3
  Token usage: ~11,200 tokens

Usage Stats (30 days):
  Most used:
    1. nextjs-fullstack (89 uses, 94% success)
    2. supabase-integration (67 uses, 96% success)
    3. git-workflow (45 uses, 100% success)

Learned Patterns (5):
  ✅ always_use_zod (applied)
  ✅ feature_colocation (applied)
  ✅ error_boundary_pattern (applied)
  ✅ server_actions_preferred (applied)
  ⏳ playwright_for_e2e (pending - 0.76 confidence)

Optimization Opportunities:

⚡ Token Optimization
   nextjs-fullstack can be compressed by 15%
   Save: ~350 tokens
   
📝 Documentation Update
   Next.js 15.0.0 → 15.1.0 available
   New features: Partial Prerendering stable
   
🔄 Skill Combination
   nextjs-fullstack + supabase-integration
   used together 67/89 times (75%)
   Consider: Pre-load together

Apply optimizations? [Y/n]
```

---

## 🎨 Comandi Disponibili

### /sf:wizard
Interactive wizard per setup iniziale.

```
Usage: /sf:wizard [--force]

Guida interattiva per:
- Rilevare tech stack
- Rispondere domande
- Generare skills personalizzate
- Setup completo

Flags:
  --force    Forza re-setup (cancella config esistente)
```

### /sf:generate
Genera skill specifica.

```
Usage: /sf:generate <skill-type> [--force] [--preview]

Skill Types:
  nextjs-fullstack       Next.js App Router full-stack
  react-spa             React SPA con Vite
  python-api            FastAPI backend
  supabase-integration  Supabase (auth, db, storage)
  git-workflow          Git workflow e conventions
  testing-suite         Testing setup
  deployment            Deployment configurations

Flags:
  --force       Sovrascrivi se esiste
  --preview     Mostra cosa verrà generato
  --no-docs     Usa cache/builtin (no Context7)

Examples:
  /sf:generate nextjs-fullstack
  /sf:generate supabase-integration --force
  /sf:generate testing-suite --preview
```

### /sf:analyze
Analizza skills e usage.

```
Usage: /sf:analyze [--detailed] [--patterns] [--health]

Flags:
  --detailed    Analisi dettagliata per skill
  --patterns    Focus su learned patterns
  --health      Health check skills

Output:
  - Skills overview
  - Usage statistics
  - Learned patterns
  - Optimization opportunities
  - Health status
```

### /sf:optimize
Ottimizza skills esistenti.

```
Usage: /sf:optimize [--auto] [--preview]

Actions:
  - Trova ridondanze
  - Suggerisci merge
  - Comprimi verbose content
  - Update outdated docs

Flags:
  --auto      Applica safe optimizations automaticamente
  --preview   Mostra cosa verrà ottimizzato
```

### /sf:update
Aggiorna skills con latest documentation.

```
Usage: /sf:update [skill-name] [--all] [--check]

Updates:
  - Fetch latest docs (Context7)
  - Update best practices
  - Update code examples
  - Update patterns

Flags:
  --all       Update tutte le skills
  --check     Solo check (no update)

Examples:
  /sf:update nextjs-fullstack
  /sf:update --all
  /sf:update --check
```

### /sf:list
Lista skills installate.

```
Usage: /sf:list [--generated] [--native]

Flags:
  --generated   Solo SkillForge generated
  --native      Solo native Anthropic

Output:
  Nome, Tipo, Last used, Success rate
```

### /sf:status
Status SkillForge.

```
Usage: /sf:status

Output:
  - Setup status
  - Skills count
  - Learning status
  - Last optimization
  - Pending updates
```

### /sf:introspect
Debug SkillForge behavior.

```
Usage: /sf:introspect [--orchestration] [--learning]

For debugging:
  - Orchestration decisions
  - Pattern detection
  - Skill loading
  - Token usage

Flags:
  --orchestration   Debug orchestration
  --learning        Debug pattern learning
```

---

## 🔬 Esempi Dettagliati

### Esempio 1: Setup Nuovo Progetto

```
Scenario: Stai iniziando nuovo progetto Next.js + Supabase

You: "Help me setup a new Next.js project with Supabase"

SkillForge (se già configurato):
├─ Carica: nextjs-fullstack + supabase-integration
├─ Segue TUE convenzioni
└─ Genera:

📁 Project Structure:
my-app/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   └── api/
├── components/
│   ├── ui/           # Shadcn components
│   └── features/     # Feature components
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── middleware.ts
│   ├── store/
│   │   └── auth.ts   # Zustand store
│   └── utils/
├── types/
└── middleware.ts

✅ Con setup completo:
   - Supabase client/server
   - Auth middleware
   - TypeScript types
   - Zustand store
   - Shadcn components configured
   - TUO stile everywhere
```

### Esempio 2: Feature Development

```
Scenario: Aggiungi feature "task management"

You: "Add task management feature with CRUD operations"

SkillForge:
├─ Carica: nextjs-fullstack + supabase-integration
├─ Identifica workflow: feature development
├─ Applica learned patterns:
│   - Feature-based colocation
│   - Server actions preferred
│   - Zod validation
│   - Error boundaries
│
└─ Genera:

📁 app/(dashboard)/tasks/
├── page.tsx                 # Task list (Server Component)
├── [id]/
│   └── page.tsx            # Task detail
├── actions.ts              # Server actions (TUO pattern)
├── components/
│   ├── task-list.tsx       # Client component
│   ├── task-form.tsx       # With Zod validation
│   └── task-item.tsx
├── lib/
│   ├── schemas.ts          # Zod schemas
│   └── queries.ts          # Database queries
└── types/
    └── task.ts             # TypeScript types

✅ Tutto segue TUE convenzioni
✅ Server actions (tuo pattern appreso)
✅ Zod validation (tuo pattern appreso)
✅ Error boundary (tuo pattern appreso)
✅ Feature colocation (tuo pattern appreso)
```

### Esempio 3: Bug Fix

```
Scenario: C'è un bug nell'auth flow

You: "There's a bug in the login - session not persisting"

SkillForge:
├─ Carica: supabase-integration (auth troubleshooting)
├─ Carica: nextjs-fullstack (middleware knowledge)
│
└─ Analizza:

Claude: "Let me check the common issues with Supabase auth 
in Next.js:

1. Middleware configuration
2. Cookie settings
3. Auth callback handling

Looking at your middleware.ts...

Found the issue! Your middleware is not configured to 
handle auth cookies properly for the dashboard route.

Current (buggy):
```typescript
export const config = {
  matcher: ['/dashboard/:path*']
}
```

Should be:
```typescript
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/auth/callback'  // Missing!
  ]
}
```

Fixed middleware.ts with proper Supabase auth handling.
The session will now persist correctly."

✅ SkillForge fornì context esatto per debugging
✅ Fix basato su TUO setup (Supabase + Next.js)
✅ Soluzione alignata alle TUE configurazioni
```

### Esempio 4: Code Review

```
Scenario: Vuoi review del nuovo codice

You: "Review this component for best practices"

SkillForge:
├─ Carica: nextjs-fullstack (Next.js best practices)
├─ Carica: TUE learned conventions
│
└─ Review basato su:
    - Next.js 15 best practices
    - TUE code style patterns
    - TUE naming conventions
    - Security best practices

Claude: "Code Review Results:

✅ Good:
- Server Component by default ✓
- Proper TypeScript types ✓
- Shadcn/ui components ✓
- Error handling present ✓

⚠️  Improvements:

1. Naming Convention (YOUR pattern):
   Current: `user_data`
   Should be: `userData` (you prefer camelCase)

2. Import Path (YOUR pattern):
   Current: `../../components/ui/button`
   Should be: `@/components/ui/button` (you use absolute)

3. Validation (YOUR learned pattern):
   Missing Zod validation for form
   You always use Zod - add schema:
   ```typescript
   const formSchema = z.object({
     // ...
   })
   ```

4. Error Handling (YOUR learned pattern):
   Should wrap in Error Boundary component
   You always use Error Boundaries

Fixed version following YOUR conventions..."

✅ Review basato su TUE convenzioni
✅ Suggerimenti allineati ai TUOI pattern
✅ Non solo "best practices" generiche
```

---

## 💎 Differenze Chiave con Sistema Nativo

### Sistema Nativo Claude Code

```
Skills Native:
├── Generiche per tutti
├── Statiche (no updates)
├── Nessuna orchestrazione
├── Nessun learning
├── Creazione manuale
└── Risultato: Buono ma generico

Example Output:
// Generic Next.js component
export default function Component() {
  // Generic patterns
  // May be outdated
  // Not your style
}
```

### Con SkillForge

```
SkillForge Skills:
├── Personalizzate per TE
├── Dinamiche (auto-update)
├── Orchestrazione intelligente
├── Learning continuo
├── Generazione automatica
└── Risultato: Perfetto per te

Example Output:
// YOUR Next.js component
// With YOUR naming
// With YOUR patterns
// With YOUR preferences
// Latest best practices
// 0 modifications needed
```

---

## 🎯 Filosofia & Principi

### 1. Personalization Over Generalization

```
❌ Bad: "Use React"
✅ Good: "Use React 18 with Hooks, following YOUR
         functional component pattern, with YOUR
         naming conventions (PascalCase), in YOUR
         project structure (feature-based)"
```

### 2. Intelligence Over Automation

```
❌ Bad: Automatically load all skills (waste tokens)
✅ Good: Intelligently select and load only relevant
         skills based on context, with optimal token
         allocation
```

### 3. Evolution Over Stasis

```
❌ Bad: Skills created once, never change
✅ Good: Skills improve continuously:
         - Learn from usage
         - Update documentation
         - Adapt to preferences
         - Optimize performance
```

### 4. Efficiency Over Completeness

```
❌ Bad: Load full documentation (10k tokens)
✅ Good: Progressive disclosure:
         - Level 1: Metadata (50 tokens)
         - Level 2: Core (2k tokens)
         - Level 3: Full (on demand)
```

---

## 🚀 Benefici Finali

### Per Developer

✅ **Setup una volta, funziona sempre**
   - 10 minuti di setup
   - Benefici per anni

✅ **Zero overhead cognitivo**
   - Non ricordare convenzioni
   - Non ricordare patterns
   - Claude lo sa già

✅ **Codice 100% consistente**
   - Stesso stile
   - Stesse convenzioni
   - Across tutto il team

✅ **Velocità 10x**
   - Su task ripetitivi
   - Su boilerplate
   - Su setup

✅ **Qualità sempre alta**
   - Latest best practices
   - Latest documentation
   - TUE best practices

### Per Claude Code

✅ **Context perfetto**
   - Sa esattamente il tuo stack
   - Sa le tue preferenze
   - Sa i tuoi pattern

✅ **Decisioni migliori**
   - Basate su TUO profilo
   - Basate su documentazione aggiornata
   - Basate su pattern appresi

✅ **Output ottimale**
   - Segue TUE convenzioni
   - Usa TUE libraries
   - Applica TUO stile

### Per Team

✅ **Onboarding istantaneo**
   - New member runs wizard
   - Gets team skills
   - Instant productivity

✅ **Consistency automatica**
   - Tutti seguono stesse conventions
   - Automaticamente
   - Senza enforcement manuale

✅ **Knowledge sharing**
   - Skills condivise via git
   - Pattern appresi condivisi
   - Miglioramento collettivo

---

## 📊 Metrics & Success

### Technical Metrics

- ✅ Token efficiency: -40% token usage vs naive approach
- ✅ Skill relevance: 95%+ correct skill selection
- ✅ Pattern accuracy: 90%+ pattern detection accuracy
- ✅ Update frequency: Weekly documentation updates

### Quality Metrics

- ✅ Code quality: Follows latest best practices
- ✅ Consistency: 100% consistent with user conventions
- ✅ Completeness: All edge cases handled
- ✅ Maintenance: Self-updating, low maintenance

### User Metrics

- ✅ Setup time: < 10 minutes
- ✅ Learning curve: Minimal (just answer questions)
- ✅ Time saved: 30-60% on common tasks
- ✅ Satisfaction: High (code matches expectations)

---

## 🔮 Future Vision (Post v1.0)

### v1.1 - Community & Sharing

```
- Skill Marketplace
- Share skills with team
- Import/export profiles
- Community patterns
```

### v1.2 - Advanced AI

```
- Better pattern detection
- Predictive skill loading
- Auto-optimization
- Anomaly detection
```

### v1.3 - Ecosystem

```
- More MCP integrations
- IDE extensions
- CI/CD integration
- Team dashboards
```

### v2.0 - Multi-Model

```
- Support other models
- Cross-model patterns
- Universal skills
- Model-agnostic framework
```

---

## 🎯 Summary: What to Tell Claude Code

Puoi copiare questa sezione come briefing completo:

---

**BRIEFING PER CLAUDE CODE:**

"Voglio costruire SkillForge - un framework di meta-programmazione per Claude Code.

**Problema**: Claude Code ha skills native potenti ma generiche. Non sanno nulla del MIO stack, delle MIE convenzioni, dei MIEI pattern. Ogni sessione ricomincia da zero.

**Soluzione**: SkillForge genera automaticamente skills personalizzate per il MIO stack tecnologico, orchestra intelligentemente multiple skills, impara dai miei pattern d'uso, e migliora continuamente.

**Componenti**:
1. **Generator**: Wizard interattivo che genera skills personalizzate usando templates e documentazione aggiornata (Context7)
2. **Orchestrator**: Sistema intelligente che seleziona e carica le skills giuste con token optimization
3. **Learner**: Analizza i pattern d'uso e aggiorna automaticamente le skills
4. **Optimizer**: Ottimizza skills per performance e qualità

**Architettura**:
- File comportamentali (SKILLFORGE.md, ORCHESTRATION.md, etc.) come SuperClaude
- Python generators per skill generation
- Templates per diversi tech stack
- Comandi slash (/sf:wizard, /sf:generate, etc.)
- MCP Context7 per documentazione sempre aggiornata
- JSON storage per dati persistenti

**Obiettivo**: Quando uso Claude Code, deve essere come avere un senior developer del mio team che conosce perfettamente il mio stack, le mie convenzioni, e il mio stile - automaticamente.

**Tech Stack**: Python 3.11+, YAML/Markdown, Context7 MCP, pytest

Seguiremo la roadmap in skillforge-complete-roadmap.md fase per fase."

---

## 📚 Risorse

- Roadmap Completa: `skillforge-complete-roadmap.md`
- Architecture: Da definire in Fase 1
- Examples: Da creare durante sviluppo
- Documentation: https://docs.claude.com/en/docs/claude-code/skills

---

**SkillForge**: Trasforma Claude Code da assistente AI in membro esperto del team. 🚀

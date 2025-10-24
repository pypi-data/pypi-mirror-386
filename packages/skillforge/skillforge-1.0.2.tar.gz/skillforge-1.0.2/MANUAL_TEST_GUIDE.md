# 🧪 Guida Test Manuale SkillForge (Produzione)

**Versione**: Pre-Release
**Data**: 2025-10-23
**Obiettivo**: Testare SkillForge come se fosse il prodotto finale pronto per gli utenti

---

## 📋 Overview

Questa guida ti permette di testare SkillForge simulando l'esperienza completa di un utente reale, dalla configurazione iniziale all'uso quotidiano.

---

## ✅ Pre-requisiti

Prima di iniziare, verifica:

```bash
# 1. Python installato (3.11+)
python3 --version

# 2. SkillForge installato
source venv/bin/activate
skillforge --version

# 3. Directory esistono
ls -la ~/.claude/skills/skillforge/

# 4. Test suite passa
python test_end_to_end_production.py
```

**Expected Output**:
- Python 3.11+
- SkillForge version 0.0.1-dev
- Directory esistono
- 4-6/6 test passano

---

## 🧪 Test Scenario 1: First-Time User Setup

**Obiettivo**: Simulare un nuovo utente che configura SkillForge per la prima volta

### Step 1.1: Check Status Iniziale

```bash
skillforge status
```

**Expected**: Mostra installazione ma no user profile

### Step 1.2: Visualizza Comandi Disponibili

```bash
skillforge --help
```

**Expected**: Lista di comandi (init, status, version)

### Step 1.3: Simula Setup Profile

```python
# Esegui in Python REPL
from skillforge.generators.config import Config

# Crea profilo utente
profile = {
    "setup_completed": True,
    "tech_stack": {
        "frontend": "Next.js 15",
        "ui": "Tailwind CSS",
        "backend": "Next.js API Routes",
        "database": "Supabase",
        "auth": "Supabase Auth"
    },
    "preferences": {
        "naming": "camelCase",
        "testing": "Vitest"
    }
}

Config.save_user_profile(profile)
print("✅ Profile saved!")

# Verifica
loaded = Config.load_user_profile()
print(f"Frontend: {loaded['tech_stack']['frontend']}")
```

**Expected**: Profile salvato in `~/.claude/skills/skillforge/data/user_profile.json`

### Step 1.4: Verifica Status Dopo Setup

```bash
skillforge status
```

**Expected**: Mostra "Setup completed"

---

## 🎯 Test Scenario 2: Intent Analysis & Skill Discovery

**Obiettivo**: Testare che il sistema comprende le richieste e trova le skills giuste

### Step 2.1: Test Intent Analyzer

```python
from skillforge.analyzers.intent_analyzer import IntentAnalyzer

analyzer = IntentAnalyzer()

# Test varie richieste
requests = [
    "Create a Next.js login page with Supabase authentication",
    "Build a dashboard with charts and tables",
    "Debug the API endpoint",
    "Add tests for the auth component"
]

for req in requests:
    intent = analyzer.analyze(req)
    print(f"\n📝 Request: {req}")
    print(f"   Action: {intent.action}")
    print(f"   Domain: {intent.domain}")
    print(f"   Complexity: {intent.complexity}")
    print(f"   Entities: {', '.join(intent.entities[:3])}")
```

**Expected**:
- Action correttamente identificata (create, build, debug, etc.)
- Domain corretto (frontend, backend, fullstack)
- Entities estratte (Next.js, Supabase, etc.)

### Step 2.2: Test Skill Discovery

```python
from skillforge.analyzers.skill_discovery import SkillDiscovery

discovery = SkillDiscovery()

# Analizza intent
intent = analyzer.analyze("Create a Next.js component with Supabase data")

# Trova skills
skills = discovery.discover_skills(intent)

print(f"\n🔍 Skills discovered: {len(skills)}")
for skill in skills:
    print(f"   - {skill.skill.name} (priority: {skill.priority}, reason: {skill.reason})")
```

**Expected**:
- Trova 2-3 skills relevanti
- nextjs-skill e supabase-skill hanno priority 100 (explicit match)
- Skills ordinate per priority

### Step 2.3: Verifica Skills Disponibili

```bash
# Lista skills disponibili
ls -la ~/.claude/skills/generated/

# Controlla una skill
cat ~/.claude/skills/generated/nextjs-skill/SKILL.md | head -50
```

**Expected**:
- Varie skills in `generated/`
- SKILL.md ha YAML frontmatter valido
- Contenuto strutturato e completo

---

## 📊 Test Scenario 3: Usage Tracking & Analytics

**Obiettivo**: Verificare che il sistema traccia l'uso e genera analytics

### Step 3.1: Simula Uso Skills

```python
from skillforge.analyzers.usage_tracker import UsageTracker

tracker = UsageTracker()

# Simula 10 usi
for i in range(10):
    tracker.record_usage(
        skills=["nextjs-skill"],
        success=True,
        duration=2.5,
        metadata={"task": f"Task {i+1}"}
    )

# Simula combinazioni
for i in range(5):
    tracker.record_usage(
        skills=["nextjs-skill", "supabase-skill"],
        success=True,
        duration=3.0
    )

print("✅ Usage recorded!")
```

**Expected**: Nessun errore

### Step 3.2: Verifica Analytics

```python
from skillforge.generators.config import Config

analytics = Config.load_analytics()
print(f"\n📊 Analytics:")
print(f"   Skills tracked: {len(analytics.get('skill_usage', {}))}")
print(f"   Total uses: {sum(s.get('total_uses', 0) for s in analytics.get('skill_usage', {}).values())}")
```

**Expected**: Dati salvati in `usage_analytics.json`

---

## 🧠 Test Scenario 4: Pattern Learning

**Obiettivo**: Verificare che il sistema apprende pattern dai dati

### Step 4.1: Record Pattern Data

```python
from skillforge.analyzers.pattern_detector import PatternDetector

detector = PatternDetector()

# Simula pattern ripetuti
combinations = [
    ["nextjs-skill", "supabase-skill"],
    ["nextjs-skill", "tailwind-skill"],
    ["supabase-skill", "auth-skill"]
]

# Ripeti per creare pattern
for _ in range(15):
    for combo in combinations:
        detector.record_combination(combo, success=True)

print("✅ Pattern data recorded!")
```

### Step 4.2: Analizza Pattern

```python
patterns = detector.analyze_skill_combinations()

print(f"\n🔍 Patterns detected: {len(patterns)}")
for pattern in patterns[:3]:
    print(f"\n   Combination: {' + '.join(pattern['skills'])}")
    print(f"   Frequency: {pattern['count']} times")
    print(f"   Success rate: {pattern['success_rate']:.1%}")
```

**Expected**:
- 3 pattern rilevati
- Count >= 15 per pattern
- Success rate 100%

---

## ⚡ Test Scenario 5: Production Performance

**Obiettivo**: Verificare performance in condizioni realistiche

### Step 5.1: Test Latency

```python
import time

# Test discovery speed
start = time.time()
for i in range(20):
    intent = analyzer.analyze("Create a Next.js component")
    skills = discovery.discover_skills(intent)
elapsed = time.time() - start

print(f"\n⚡ Performance:")
print(f"   20 discovery cycles: {elapsed:.2f}s")
print(f"   Average per cycle: {elapsed/20*1000:.0f}ms")
```

**Expected**:
- < 2 secondi totali
- < 100ms per ciclo

### Step 5.2: Test Memory Usage

```python
import sys

# Controlla dimensione dati
analytics_file = Config.DATA_DIR / "usage_analytics.json"
if analytics_file.exists():
    size_kb = analytics_file.stat().st_size / 1024
    print(f"\n💾 Data size: {size_kb:.1f} KB")
```

**Expected**: < 100 KB per dati analytics

---

## 🔄 Test Scenario 6: End-to-End Workflow

**Obiettivo**: Test completo workflow utente

### Step 6.1: Run Automated E2E Test

```bash
source venv/bin/activate
python test_end_to_end_production.py
```

**Expected**: 4-6/6 scenari passano

### Step 6.2: Manual Workflow Test

Esegui questi steps in sequenza:

1. **Setup**: Crea user profile
2. **Usage**: Simula 10 tasks
3. **Learning**: Analizza pattern
4. **Optimization**: Identifica opportunità
5. **Introspection**: Verifica stato sistema

**Expected**: Tutti completano senza errori

---

## 📝 Test Scenario 7: Error Handling

**Obiettivo**: Verificare che il sistema gestisce errori correttamente

### Step 7.1: Invalid Intent

```python
# Intent vuoto
intent = analyzer.analyze("")
print(f"Empty intent: {intent.action}")  # Should handle gracefully
```

### Step 7.2: Missing Profile

```python
# Backup profile
import shutil
profile_path = Config.DATA_DIR / "user_profile.json"
backup_path = Config.DATA_DIR / "user_profile.json.bak"

shutil.copy(profile_path, backup_path)
profile_path.unlink()

# Try to load
profile = Config.load_user_profile()
print(f"Missing profile handled: {profile.get('setup_completed', False)}")

# Restore
shutil.copy(backup_path, profile_path)
```

**Expected**: Nessun crash, fallback a default

---

## ✅ Test Checklist Finale

Prima di considerare "pronto per produzione", verifica:

### Core Functionality
- [ ] Intent analysis funziona per vari input
- [ ] Skill discovery trova skills relevanti
- [ ] Usage tracking salva dati correttamente
- [ ] Pattern detection identifica combinazioni comuni
- [ ] Config management persiste dati

### Performance
- [ ] Discovery < 100ms per richiesta
- [ ] File dati < 100KB dopo uso normale
- [ ] Memory usage stabile durante uso prolungato

### Reliability
- [ ] Gestisce input vuoti/malformati
- [ ] Non crasha mai
- [ ] Fallback a default quando necessario
- [ ] Dati persistono tra restart

### User Experience
- [ ] CLI commands rispondono velocemente
- [ ] Messaggi di errore chiari
- [ ] Status command mostra info utili
- [ ] Setup intuitivo

### Data Integrity
- [ ] JSON files validi
- [ ] Backup automatico prima di modifiche critiche
- [ ] No data loss su errori
- [ ] Profile versioning funziona

---

## 🐛 Problemi Noti

### Issue 1: Skills in /generated/ non in root
**Workaround**: Skills funzionano comunque, discovery le trova

### Issue 2: Alcuni logging molto verbose
**Workaround**: Normale per development, ridurre per production

---

## 📊 Report Template

Dopo i test, compila questo report:

```markdown
# SkillForge Test Report

**Data Test**: 2025-10-23
**Tester**: [Il tuo nome]
**Versione**: 0.0.1-dev

## Risultati

### Automated Tests
- [ ] test_end_to_end_production.py: X/6 passed

### Manual Tests
- [ ] Scenario 1 (Setup): PASS/FAIL
- [ ] Scenario 2 (Intent & Discovery): PASS/FAIL
- [ ] Scenario 3 (Usage Tracking): PASS/FAIL
- [ ] Scenario 4 (Pattern Learning): PASS/FAIL
- [ ] Scenario 5 (Performance): PASS/FAIL
- [ ] Scenario 6 (E2E Workflow): PASS/FAIL
- [ ] Scenario 7 (Error Handling): PASS/FAIL

### Issues Found
1. [Descrizione issue]
2. [Descrizione issue]

### Production Readiness
Overall: READY / MOSTLY READY / NOT READY

Giustificazione: [...]
```

---

## 🚀 Prossimi Passi

Se i test passano:

1. **Fase 10 - Distribution**:
   - Creare installer script
   - Preparare package PyPI
   - Setup GitHub repository
   - Scrivere release notes

2. **Beta Testing**:
   - Invitare 5-10 beta tester
   - Raccogliere feedback
   - Iterare basandosi su feedback reale

3. **Production Release**:
   - Publish to PyPI
   - Announce su community Claude Code
   - Setup support channels

---

## 📚 Risorse

- **Documentazione**: `docs/`
- **Test Suite**: `tests/`
- **Roadmap**: `docs/skillforge-complete-roadmap.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

## 💡 Tips per Test Efficaci

1. **Testa in ambiente pulito**: Usa `rm -rf ~/.claude/skills/skillforge/data/` per reset
2. **Varia gli scenari**: Non testare solo happy path
3. **Simula uso reale**: Pensa come un utente vero
4. **Documenta problemi**: Screenshot + steps to reproduce
5. **Testa edge cases**: Input vuoti, molto lunghi, speciali

---

## ✨ Conclusione

SkillForge è quasi pronto! I componenti core funzionano. Manca solo:

- Wizard interattivo completo
- Context7 integration live
- Slash commands in Claude Code
- Documentazione finale

Ma il **cuore del sistema** (analisi, discovery, tracking, learning) è **funzionante e testato**! 🎉

#!/bin/bash

# Script to test Skill Generation Pipeline components
# Tests all generator modules in isolation

set -e  # Exit on error

echo "🧪 Testing SkillForge Generation Pipeline..."
echo "==========================================="
echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
echo "   Python version: $python_version"
echo ""

# Test 1: Config Module
echo "1. Testing Config Module..."
python3 << 'EOF'
from skillforge.generators.config import Config
import tempfile
from pathlib import Path

# Override with temp directory for testing
temp_dir = Path(tempfile.mkdtemp())
Config.SKILLFORGE_HOME = temp_dir / ".claude" / "skills" / "skillforge"
Config.DATA_DIR = Config.SKILLFORGE_HOME / "data"
Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"

Config.ensure_directories()
assert Config.SKILLFORGE_HOME.exists(), "Failed to create SKILLFORGE_HOME"
assert Config.DATA_DIR.exists(), "Failed to create DATA_DIR"
assert Config.CACHE_DIR.exists(), "Failed to create CACHE_DIR"

print("   ✅ Config module works")
EOF

# Test 2: Wizard Engine
echo "2. Testing Wizard Engine..."
python3 << 'EOF'
from skillforge.generators.wizard_engine import WizardEngine
import tempfile
from pathlib import Path
import json

# Create test package.json
temp_dir = Path(tempfile.mkdtemp())
package_json = temp_dir / "package.json"
package_json.write_text(json.dumps({
    "dependencies": {
        "next": "^14.0.0",
        "react": "^18.0.0",
        "tailwindcss": "^3.0.0"
    }
}))

# Change to temp directory
import os
os.chdir(temp_dir)

wizard = WizardEngine()
detected = wizard.detect_stack()

assert "Next.js" in str(detected.get("frontend", "")), "Failed to detect Next.js"
assert "Tailwind CSS" in str(detected.get("ui", "")), "Failed to detect Tailwind"

print("   ✅ Wizard Engine initialized and detects stack")
EOF

# Test 3: Template Processor
echo "3. Testing Template Processor..."
python3 << 'EOF'
from skillforge.generators.template_processor import TemplateProcessor

processor = TemplateProcessor()

# Test variable substitution
result = processor.process(
    '{{name}} is {{age}} years old',
    {'name': 'Alice', 'age': 30}
)
assert result == 'Alice is 30 years old', "Variable substitution failed"

# Test conditionals
template = '''{{#if premium}}Premium{{else}}Free{{/if}}'''
result = processor.process(template, {'premium': True})
assert 'Premium' in result, "Conditional failed"

# Test loops
template = '''{{#each items}}{{name}},{{/each}}'''
result = processor.process(template, {
    'items': [{'name': 'A'}, {'name': 'B'}]
})
assert 'A,' in result and 'B,' in result, "Loop failed"

print("   ✅ Template Processor works (variables, conditionals, loops)")
EOF

# Test 4: Doc Fetcher
echo "4. Testing Doc Fetcher..."
python3 << 'EOF'
from skillforge.generators.doc_fetcher import DocFetcher
from skillforge.generators.config import Config
import tempfile
from pathlib import Path

# Override cache directory for testing
temp_dir = Path(tempfile.mkdtemp())
Config.SKILLFORGE_HOME = temp_dir / ".claude" / "skills" / "skillforge"
Config.DATA_DIR = Config.SKILLFORGE_HOME / "data"
Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
Config.ensure_directories()

fetcher = DocFetcher()

# Test library resolution
library_id = fetcher.resolve_library_id("next.js")
assert library_id is not None, "Library resolution failed"
assert "next" in library_id.lower(), "Library ID incorrect"

# Test mock data fetch
docs = fetcher.fetch("next.js", use_mcp=False)  # Use mock data
assert docs is not None, "Doc fetch failed"
assert "documentation" in docs or "docs" in docs.lower(), "Invalid docs format"

# Test cache
cache_path = Config.get_cache_path("next.js")
assert cache_path.exists(), "Cache not created"

print("   ✅ Doc Fetcher initialized and fetches mock data")
EOF

# Test 5: Skill Generator
echo "5. Testing Skill Generator..."
python3 << 'EOF'
from skillforge.generators.skill_generator import SkillGenerator
from skillforge.generators.config import Config
import tempfile
from pathlib import Path

# Override directories for testing
temp_dir = Path(tempfile.mkdtemp())
Config.SKILLFORGE_HOME = temp_dir / ".claude" / "skills" / "skillforge"
Config.DATA_DIR = Config.SKILLFORGE_HOME / "data"
Config.CACHE_DIR = Config.DATA_DIR / "cache" / "context7"
Config.ensure_directories()

generator = SkillGenerator()

# Test template path resolution
template_path = generator.get_template_path("nextjs")
# Template may not exist yet, but method should work
assert template_path is not None, "Template path resolution failed"

# Test variable preparation
profile = {
    "tech_stack": {
        "frontend": "Next.js",
        "ui": "Tailwind CSS"
    },
    "preferences": {
        "testing": "Jest"
    }
}

docs = {"version": "14.0", "examples": ["example1"], "best_practices": ["practice1"]}
variables = generator.prepare_variables("nextjs", profile, docs)

assert "framework_name" in variables, "Missing framework_name"
assert "user_conventions" in variables, "Missing user_conventions"
assert "best_practices" in variables, "Missing best_practices"

print("   ✅ Skill Generator initialized and prepares variables")
EOF

# Run full test suite
echo ""
echo "6. Running Full Test Suite..."
python3 -m pytest tests/unit/test_wizard_engine.py tests/unit/test_template_processor.py tests/unit/test_doc_fetcher.py tests/unit/test_skill_generator.py --tb=no -q

echo ""
echo "==========================================="
echo "✅ All Generation Components Validated!"
echo ""
echo "Summary:"
echo "  - Config: ✅ Working"
echo "  - Wizard Engine: ✅ Working"
echo "  - Template Processor: ✅ Working"
echo "  - Doc Fetcher: ✅ Working"
echo "  - Skill Generator: ✅ Working"
echo "  - Test Suite: ✅ Running"
echo ""
echo "Generation pipeline ready for use!"

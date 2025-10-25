# ADR 003: Distribution Strategy (PyPI + Post-Install Deployment)

## Status
**Accepted** - 2025-10-22

## Context
SkillForge has dual nature:
1. **Python package** (generators, analyzers)
2. **Claude Code skills** (Markdown files in `~/.claude/skills/skillforge/`)

We need a distribution strategy that handles both components elegantly.

**Options considered**:
1. npm package
2. PyPI package only (manual skill deployment)
3. PyPI + post-install hook (automatic)
4. GitHub releases only
5. Custom installer script

## Decision
Use **PyPI + Post-Install Hook** with automatic skill deployment.

**Primary Method**: `pipx install skillforge`
**Fallback**: `skillforge init` command for manual setup

## Rationale

### Why PyPI

**✅ Pros**:
1. **Standard Python Distribution**
   - Familiar to Python devs
   - Established ecosystem
   - Version management (pip handles updates)

2. **Dependency Management**
   - pip resolves dependencies automatically
   - Virtual environment support
   - Requirements clearly specified

3. **Discoverability**
   - PyPI.org for discovery
   - `pip search skillforge`
   - Standard installation experience

4. **CI/CD Integration**
   - GitHub Actions can auto-publish
   - Version bumping standard
   - Testing before release

### Why Post-Install Hook

**✅ Pros**:
1. **Automatic Deployment**
   - Skills deployed without manual steps
   - Reduced setup friction
   - Better user experience

2. **Single Command Install**
   ```bash
   pipx install skillforge
   # → Python package installed
   # → Skills auto-deployed to ~/.claude/skills/skillforge/
   # → Ready to use!
   ```

3. **Update Safety**
   - Preserves user data (data/ directory)
   - Only updates skill files
   - Clear upgrade path

### Why pipx (Recommended)

**✅ Pros**:
1. **Isolated Environment**
   - No dependency conflicts
   - Clean system
   - Easy to uninstall completely

2. **Global Command**
   - `skillforge` available in PATH
   - Works from any directory
   - Professional CLI experience

3. **Standard Practice**
   - Recommended by Python packaging authority
   - Used by other CLI tools
   - Familiar to developers

### Why NOT npm

**❌ Cons**:
1. JavaScript ecosystem (SkillForge is Python)
2. Would need Node.js dependency
3. npm can't easily deploy to `~/.claude/skills/`
4. Package.json doesn't fit Python codebase

### Why NOT Manual Deployment Only

**❌ Cons**:
1. Multi-step installation (bad UX)
2. Users might skip skill deployment
3. More support burden (where to put files?)
4. Friction reduces adoption

### Why NOT GitHub Only

**❌ Cons**:
1. No version management
2. Manual `git clone` + install
3. Updates require manual pull
4. Not discoverable via pip search

## Implementation

### Package Structure

```python
# setup.py
from setuptools import setup
from setuptools.command.install import install
import shutil
from pathlib import Path

class PostInstallCommand(install):
    """Deploy skills after package install"""

    def run(self):
        # Install Python package
        install.run(self)

        # Deploy skill files
        self.deploy_skills()

    def deploy_skills(self):
        """Copy skill files to ~/.claude/skills/skillforge/"""
        target = Path.home() / ".claude" / "skills" / "skillforge"
        target.mkdir(parents=True, exist_ok=True)

        # Copy from package data
        source = Path(__file__).parent / "skillforge" / "data" / "skill_files"

        for item in source.rglob("*"):
            if item.is_file():
                relative = item.relative_to(source)
                dest = target / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

        print(f"✅ Skills deployed to: {target}")
        print("   Restart Claude Code to activate")

setup(
    name="skillforge",
    version="1.0.0",
    cmdclass={'install': PostInstallCommand},
    # ... rest of setup
)
```

### Package Data Inclusion

```python
# setup.py
setup(
    # ...
    include_package_data=True,
    package_data={
        "skillforge": [
            "data/skill_files/**/*",
            "data/templates/**/*",
        ],
    },
)
```

### Fallback: Manual Init

```python
# skillforge/cli.py
@click.command()
def init():
    """Deploy skill files (fallback if post-install failed)"""
    target = Path.home() / ".claude" / "skills" / "skillforge"

    if target.exists() and (target / "SKILL.md").exists():
        click.echo("✅ Already initialized!")
        return

    # Deploy files
    deploy_skills(target)
    click.echo(f"✅ Skills deployed to: {target}")
```

## User Experience

### Happy Path (99% of users)

```bash
# Single command installation
$ pipx install skillforge

# Output:
Installing skillforge...
✅ SkillForge installed!
✅ Skills deployed to: ~/.claude/skills/skillforge/

Next steps:
  1. Restart Claude Code
  2. Run: /sf:wizard
```

### Fallback Path (if post-install fails)

```bash
$ pipx install skillforge
$ skillforge init  # Manual deployment

# Output:
✅ Skills deployed to: ~/.claude/skills/skillforge/

Next steps:
  1. Restart Claude Code
  2. Run: /sf:wizard
```

### Update Path

```bash
$ pipx upgrade skillforge

# Output:
Upgrading skillforge...
✅ SkillForge upgraded to 1.1.0
✅ Skills updated (user data preserved)

Changes:
  - Updated Next.js template (14 → 15)
  - Added Python FastAPI template
  - Fixed bug in pattern detection

Restart Claude Code to see changes.
```

## Consequences

### Positive
- ✅ **One-command install**: Minimal friction
- ✅ **Standard tooling**: pipx/pip familiar
- ✅ **Automatic deployment**: Skills just work
- ✅ **Easy updates**: `pipx upgrade skillforge`
- ✅ **Data preservation**: User data survives updates
- ✅ **Discoverable**: On PyPI.org

### Negative
- ⚠️ **Restart required**: Claude Code must restart to see skills
- ⚠️ **Post-install complexity**: More setup.py code
- ⚠️ **Testing burden**: Must test installation process

### Risks & Mitigation

**Risk 1**: Post-install fails (permissions, path issues)
- **Mitigation**: Fallback `skillforge init` command
- **Detection**: Check if SKILL.md exists after install

**Risk 2**: User doesn't restart Claude Code
- **Mitigation**: Clear messaging in output
- **Mitigation**: Add to README prominently

**Risk 3**: Update overwrites user customizations
- **Mitigation**: Only update skill files, not data/
- **Mitigation**: Backup before update (future enhancement)

## Distribution Channels

### Primary: PyPI
```bash
# Build
python -m build

# Upload to TestPyPI (first)
twine upload --repository testpypi dist/*

# Test
pipx install --pip-args="--index-url https://test.pypi.org/simple/" skillforge

# Upload to PyPI (production)
twine upload dist/*
```

### Alternative: GitHub Releases
- Provide as backup for users who prefer git
- Include in release notes
- Manual install instructions

### Future: Homebrew
- Consider after v1.0
- MacOS/Linux package manager
- Even easier install: `brew install skillforge`

## Testing Strategy

### Pre-Release Testing

```bash
# Test post-install hook
python setup.py install

# Verify deployment
ls -la ~/.claude/skills/skillforge/
test -f ~/.claude/skills/skillforge/SKILL.md && echo "✅ SKILL.md exists"

# Test fallback
rm -rf ~/.claude/skills/skillforge
skillforge init
test -f ~/.claude/skills/skillforge/SKILL.md && echo "✅ Fallback works"
```

### CI/CD Testing

```yaml
# .github/workflows/test-install.yml
name: Test Installation

on: [push, pull_request]

jobs:
  test-install:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}

      - name: Install package
        run: pip install .

      - name: Verify skills deployed
        run: |
          test -f ~/.claude/skills/skillforge/SKILL.md
          echo "✅ Skills deployed successfully"

      - name: Test CLI
        run: |
          skillforge --version
          skillforge status
```

## References
- Python Packaging: https://packaging.python.org/
- pipx Documentation: https://pypa.github.io/pipx/
- setuptools: https://setuptools.pypa.io/
- Post-install hooks: https://setuptools.pypa.io/en/latest/userguide/extension.html

## Review Criteria
Will reconsider if:
- Post-install hooks prove unreliable (>10% failure rate)
- PyPI policies change to restrict this pattern
- Better distribution method emerges
- User feedback indicates significant friction

## Timeline
- **Fase 1**: Setup basic package structure
- **Fase 3**: Implement post-install hook
- **Fase 9**: Test installation on multiple platforms
- **Fase 10**: Publish to PyPI

## Related ADRs
- ADR 001: Python for Generators (why Python package)
- ADR 002: Behavioral File Injection (what gets deployed)

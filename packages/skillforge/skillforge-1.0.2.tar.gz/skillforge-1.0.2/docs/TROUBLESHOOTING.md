# 🔧 Troubleshooting Guide

**Common issues and their solutions**

---

## Installation Issues

### Issue: "skillforge: command not found"

**Cause**: SkillForge CLI not in PATH

**Solution**:
```bash
# Check if pipx bin directory is in PATH
echo $PATH | grep ".local/bin"

# If not, add to shell config
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc

# Verify installation
which skillforge

# If still not found, reinstall
pipx uninstall skillforge
pipx install skillforge
```

### Issue: "Python version not supported"

**Cause**: Python version < 3.11

**Solution**:
```bash
# Check Python version
python3 --version

# If < 3.11, install newer Python
# macOS:
brew install python@3.11

# Linux:
sudo apt install python3.11

# Verify
python3.11 --version
```

### Issue: "pip install fails with dependencies error"

**Cause**: Missing system dependencies

**Solution**:
```bash
# Update pip
python3 -m pip install --upgrade pip

# Install with verbose output to see error
pip install skillforge -v

# If specific package fails, install separately
pip install pyyaml requests click

# Then retry
pip install skillforge
```

---

## Wizard Issues

### Issue: Wizard hangs during auto-detection

**Cause**: Large project directory

**Solution**:
```bash
# Run from root directory, not nested folder
cd ~/projects/my-project  # not ~/projects/my-project/src/

# Or skip auto-detection
/sf:wizard
# Answer "n" when asked about detected stack
```

### Issue: "No tech stack detected"

**Cause**: Not in a project directory

**Solution**:
```bash
# Navigate to project first
cd ~/projects/my-project

# Then run wizard
/sf:wizard

# Or manually specify stack in wizard questions
```

### Issue: Wizard crashes during documentation fetch

**Cause**: Context7 MCP not available or network issue

**Solution**:
```bash
# Check Context7 MCP
claude --list-mcps

# If not listed, generate without docs
/sf:generate <skill> --no-docs

# Or check network
ping anthropic.com
```

---

## Skill Generation Issues

### Issue: "Skill already exists"

**Cause**: Skill with same name already generated

**Solution**:
```bash
# Option 1: Force overwrite
/sf:generate nextjs-fullstack --force

# Option 2: Delete old skill first
rm -rf ~/.claude/skills/nextjs-fullstack/
/sf:generate nextjs-fullstack

# Option 3: Rename old skill
mv ~/.claude/skills/nextjs-fullstack/ ~/.claude/skills/nextjs-fullstack-old/
/sf:generate nextjs-fullstack
```

### Issue: "Invalid template"

**Cause**: Template file corrupted or missing

**Solution**:
```bash
# Reinstall SkillForge
pipx reinstall skillforge

# Or repair installation
skillforge install --repair

# Verify templates exist
ls ~/.claude/skills/skillforge/templates/
```

### Issue: Generated skill is empty or incomplete

**Cause**: Template processing error

**Solution**:
```bash
# Check logs
cat ~/.claude/skills/skillforge/data/logs/generation.log

# Regenerate with verbose output
/sf:generate <skill> --verbose

# If still fails, use built-in template
/sf:generate <skill> --no-docs --force
```

---

## Claude Code Integration Issues

### Issue: Skills not loading in Claude Code

**Cause**: Claude hasn't reloaded skills

**Solution**:
```bash
# Restart Claude Code completely
killall claude
claude

# Verify skills directory
ls ~/.claude/skills/
# Should show: skillforge/, nextjs-fullstack/, etc.

# Check SKILL.md exists
cat ~/.claude/skills/nextjs-fullstack/SKILL.md | head -20
```

### Issue: Claude uses wrong conventions

**Cause**: Skills not loading or profile outdated

**Solution**:
```bash
# Verify profile
cat ~/.claude/skills/skillforge/data/user_profile.json

# Update profile
/sf:wizard --update

# Regenerate skills with new profile
/sf:generate <skill> --force

# Restart Claude
killall claude && claude
```

### Issue: "Skill not found" error

**Cause**: Skill path incorrect

**Solution**:
```bash
# Check skill installation
/sf:list

# Reinstall skill
/sf:generate <skill-name> --force

# Verify directory structure
tree ~/.claude/skills/nextjs-fullstack/
# Should have SKILL.md at root
```

---

## Orchestration Issues

### Issue: Wrong skills loaded for task

**Cause**: Intent analysis misinterpretation

**Solution**:
```bash
# Debug orchestration
/sf:introspect --orchestration --last

# Be more explicit in request
# Instead of: "Create component"
# Use: "Create Next.js component with Supabase auth"

# Force specific skill
"Create component using my nextjs-fullstack skill"
```

### Issue: Too many skills loaded (token budget exceeded)

**Cause**: Too many skills discovered

**Solution**:
```bash
# Reduce token budget per skill
/sf:config set optimization.token_budget 2500

# Or optimize skills to reduce size
/sf:optimize

# Or be more specific in requests
# Instead of: "Build app"
# Use: "Create login component"
```

---

## Learning & Pattern Issues

### Issue: Patterns not learning

**Cause**: Not enough samples or learning disabled

**Solution**:
```bash
# Check learning status
/sf:introspect --learning

# Verify learning enabled
/sf:config get learning.enabled

# Enable if disabled
/sf:config set learning.enabled true

# Check sample count
/sf:analyze --patterns
# Patterns need 10+ samples
```

### Issue: Wrong patterns detected

**Cause**: False positives or low confidence

**Solution**:
```bash
# View pattern details
/sf:analyze --patterns

# Increase confidence threshold
/sf:config set learning.confidence_threshold 0.9

# Disable auto-application
/sf:config set learning.auto_apply false

# Manual review before applying
/sf:introspect --learning
```

### Issue: Pattern not applied to skill

**Cause**: Confidence below threshold

**Solution**:
```bash
# Check pattern confidence
/sf:analyze --patterns

# If close to threshold, use skill more
# Pattern will strengthen with more samples

# Or lower threshold (not recommended)
/sf:config set learning.confidence_threshold 0.75
```

---

## Performance Issues

### Issue: Slow skill generation

**Cause**: Documentation fetch is slow

**Solution**:
```bash
# Skip doc fetching (use cache)
/sf:generate <skill> --no-docs

# Or increase cache TTL
/sf:config set cache.ttl_days 14

# Check network
ping docs.anthropic.com
```

### Issue: Slow orchestration

**Cause**: Too many skills installed

**Solution**:
```bash
# Remove unused skills
/sf:optimize

# Or manually remove
rm -rf ~/.claude/skills/<unused-skill>/

# Check skill count (recommended: 8-12)
/sf:list
```

### Issue: High memory usage

**Cause**: Large skills or too many loaded

**Solution**:
```bash
# Compress skills
/sf:optimize

# Reduce token budget
/sf:config set optimization.token_budget 2500

# Remove unused skills
/sf:reset --cache
```

---

## Update Issues

### Issue: "No updates available" but docs are outdated

**Cause**: Cache is still valid

**Solution**:
```bash
# Force update
/sf:update <skill> --force

# Or clear cache first
/sf:reset --cache
/sf:update <skill>
```

### Issue: Update fails with validation error

**Cause**: New documentation incompatible with template

**Solution**:
```bash
# Check logs
cat ~/.claude/skills/skillforge/data/logs/update.log

# Rollback to previous version
/sf:config restore-backup

# Or regenerate completely
rm -rf ~/.claude/skills/<skill>/
/sf:generate <skill>
```

---

## Configuration Issues

### Issue: "Config key not found"

**Cause**: Invalid configuration key

**Solution**:
```bash
# List all config keys
/sf:config

# Use exact key name
/sf:config get learning.enabled  # Correct
/sf:config get learning_enabled  # Wrong
```

### Issue: Config changes not applying

**Cause**: Need to restart or regenerate

**Solution**:
```bash
# After config change, restart Claude
killall claude && claude

# For preference changes, regenerate skills
/sf:generate <skill> --force
```

### Issue: Can't reset configuration

**Cause**: Permission error or corrupted file

**Solution**:
```bash
# Check permissions
ls -la ~/.claude/skills/skillforge/data/

# Fix permissions
chmod 755 ~/.claude/skills/skillforge/data/

# Manually delete config
rm ~/.claude/skills/skillforge/data/config.json

# Regenerate
/sf:wizard
```

---

## Context7 MCP Issues

### Issue: "Context7 not available"

**Cause**: MCP server not running or configured

**Solution**:
```bash
# Check MCP servers
claude --list-mcps

# If Context7 not listed, install it
# (See Context7 documentation)

# Workaround: Generate without docs
/sf:generate <skill> --no-docs
```

### Issue: "Library not found" error

**Cause**: Context7 doesn't have docs for library

**Solution**:
```bash
# Check library ID
/sf:introspect --request "Library: <name>"

# Use alternative name
# e.g., "Next.js" instead of "nextjs"

# Or use --no-docs
/sf:generate <skill> --no-docs
```

---

## File System Issues

### Issue: "Permission denied" errors

**Cause**: Incorrect file permissions

**Solution**:
```bash
# Fix SkillForge directory permissions
chmod -R 755 ~/.claude/skills/skillforge/

# Fix data directory
chmod -R 755 ~/.claude/skills/skillforge/data/

# Verify
ls -la ~/.claude/skills/skillforge/
```

### Issue: "Disk full" or "No space left"

**Cause**: Too many cached files

**Solution**:
```bash
# Check cache size
du -sh ~/.claude/skills/skillforge/data/cache/

# Clear cache
/sf:reset --cache

# Or manually
rm -rf ~/.claude/skills/skillforge/data/cache/*
```

### Issue: Corrupted skill files

**Cause**: Incomplete write or system crash

**Solution**:
```bash
# Check YAML frontmatter
head -20 ~/.claude/skills/<skill>/SKILL.md

# If corrupted, regenerate
rm -rf ~/.claude/skills/<skill>/
/sf:generate <skill>

# Or restore from backup
cp ~/.claude/skills/skillforge/data/backups/<skill>-*.md \
   ~/.claude/skills/<skill>/SKILL.md
```

---

## Common Error Messages

### "ValueError: Invalid skill type"

**Solution**: Use valid skill type from `/sf:generate` list

### "FileNotFoundError: user_profile.json"

**Solution**: Run `/sf:wizard` to create profile

### "YAMLError: Invalid frontmatter"

**Solution**: Regenerate skill with `/sf:generate <skill> --force`

### "TokenBudgetExceeded"

**Solution**: Run `/sf:optimize` or reduce token budget

### "ValidationError: Missing required sections"

**Solution**: Regenerate skill (template may be incomplete)

---

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set log level
export SKILLFORGE_LOG_LEVEL=DEBUG

# Run command
/sf:generate nextjs-fullstack

# Check logs
tail -f ~/.claude/skills/skillforge/data/logs/skillforge.log
```

---

## Getting Help

If the issue persists:

1. **Collect diagnostics**:
   ```bash
   /sf:status --verbose > status.txt
   /sf:introspect --last > introspect.txt
   ```

2. **Check logs**:
   ```bash
   cat ~/.claude/skills/skillforge/data/logs/skillforge.log
   ```

3. **Create issue**:
   - Go to [GitHub Issues](https://github.com/omarpiosedev/SkillForge/issues)
   - Include: status.txt, introspect.txt, relevant logs
   - Describe: What you were doing, expected vs actual behavior

4. **Community**:
   - Join [Discord](https://discord.gg/skillforge)
   - Check [Discussions](https://github.com/omarpiosedev/SkillForge/discussions)

---

## Preventive Measures

### Regular Maintenance

```bash
# Weekly
/sf:analyze
/sf:update --check

# Monthly
/sf:optimize
/sf:update --all
```

### Backup Important Data

```bash
# Backup profile
cp ~/.claude/skills/skillforge/data/user_profile.json ~/backups/

# Backup skills
tar -czf ~/backups/skills-$(date +%Y%m%d).tar.gz ~/.claude/skills/
```

### Keep SkillForge Updated

```bash
# Check for updates
pipx list | grep skillforge

# Update
pipx upgrade skillforge

# Verify
skillforge --version
```

---

**Still stuck?** [Open an issue](https://github.com/omarpiosedev/SkillForge/issues) - we're here to help!

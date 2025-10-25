"""
SkillForge CLI - Command Line Interface

Main entry point for skillforge command.
Full implementation will be added in later phases.
"""

import os
import click
from skillforge import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """
    SkillForge - Meta-Programming Framework for Claude Code Skills

    Utility commands for managing SkillForge installation and configuration.

    Note: Skill generation and AI-powered features are available via Claude Code:
    - /sf:wizard - Interactive setup wizard
    - /sf:generate - Generate skills with latest docs
    - /sf:update - Update skills with new documentation
    - /sf:optimize - Optimize skills for performance
    - /sf:analyze - Analyze usage patterns
    """
    pass


@main.command()
@click.option('--local', is_flag=True, help='Install from local development environment')
def install(local):
    """Install SkillForge skill files to Claude Code"""
    import subprocess
    import sys
    from pathlib import Path

    try:
        # Find the install.sh script inside the package
        import skillforge
        package_dir = Path(skillforge.__file__).parent
        install_script = package_dir / "data" / "scripts" / "install.sh"

        # Check if script exists
        if not install_script.exists():
            click.echo(f"❌ Installation script not found: {install_script}")
            click.echo("\nFalling back to manual installation...")

            # Fallback to Python-based installation
            _manual_install()
            return

        # Make script executable
        install_script.chmod(0o755)

        # Run the beautiful bash installer
        cmd = [str(install_script)]
        if local:
            cmd.append("--local")

        # Execute the script
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)

    except Exception as e:
        click.echo(f"\n❌ Installation failed: {e}")
        click.echo("\nPlease report this issue at:")
        click.echo("https://github.com/omarpioselli/SkillForge/issues")
        sys.exit(1)


def _manual_install():
    """Manual fallback installation if bash script not found"""
    import shutil
    from pathlib import Path
    from skillforge.generators.config import Config

    click.echo("\n⚠️  Using Python-based fallback installer...")
    click.echo("")

    import skillforge
    package_dir = Path(skillforge.__file__).parent
    source_dir = package_dir / "data" / "skill_files"

    if not source_dir.exists():
        click.echo(f"❌ Source directory not found: {source_dir}")
        return

    # Install skill files
    skills_dest = Config.CLAUDE_SKILLS_DIR / "skillforge"
    skills_dest.mkdir(parents=True, exist_ok=True)

    # Copy SKILL.md
    skill_file = source_dir / "SKILL.md"
    if skill_file.exists():
        shutil.copy2(skill_file, skills_dest / "SKILL.md")
        click.echo(f"✅ SKILL.md")

    # Copy core/
    core_src = source_dir / "core"
    core_dest = skills_dest / "core"
    if core_src.exists():
        if core_dest.exists():
            shutil.rmtree(core_dest)
        shutil.copytree(core_src, core_dest)
        click.echo(f"✅ Core files")

    # Copy templates/
    templates_src = package_dir / "data" / "templates"
    templates_dest = Config.DATA_DIR / "templates"
    if templates_src.exists():
        if templates_dest.exists():
            shutil.rmtree(templates_dest)
        shutil.copytree(templates_src, templates_dest)
        click.echo(f"✅ Templates")

    # Create data directories
    Config.ensure_directories()

    # Install slash commands
    commands_root = Path.home() / ".claude" / "commands" / "sf"
    commands_root.mkdir(parents=True, exist_ok=True)

    commands_src = source_dir / "commands" / "sf"
    if commands_src.exists():
        for cmd_file in commands_src.glob("*.md"):
            shutil.copy2(str(cmd_file), str(commands_root / cmd_file.name))
        click.echo(f"✅ Slash commands")

    click.echo("\n✅ Installation complete!")
    click.echo("Restart Claude Code to activate SkillForge.")


@main.command()
def version():
    """Show SkillForge version"""
    click.echo(f"SkillForge version {__version__}")


@main.command()
def list():
    """List all installed SkillForge skills"""
    from skillforge.generators.config import Config

    try:
        click.echo("📚 Installed Skills")
        click.echo("=" * 60)

        skills = Config.get_installed_skills()

        if not skills:
            click.echo("\n⚠️  No skills installed yet.")
            click.echo("Use /sf:wizard in Claude Code to generate your first skills!")
            return

        click.echo(f"\nFound {len(skills)} skills:\n")

        for skill_name in sorted(skills):
            skill_path = Config.CLAUDE_SKILLS_DIR / skill_name
            if skill_path.exists():
                # Get skill metadata
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    size = skill_file.stat().st_size
                    click.echo(f"  ✅ {skill_name}")
                    click.echo(f"     Path: {skill_path}")
                    click.echo(f"     Size: {size:,} bytes")
                else:
                    click.echo(f"  ⚠️  {skill_name} (SKILL.md missing)")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(key, value):
    """View or edit SkillForge configuration"""
    from skillforge.generators.config import Config

    try:
        if not key:
            # Show all config
            click.echo("⚙️  SkillForge Configuration")
            click.echo("=" * 60)
            click.echo(f"\n📁 Paths:")
            click.echo(f"  • SkillForge Home: {Config.SKILLFORGE_HOME}")
            click.echo(f"  • Data Directory: {Config.DATA_DIR}")
            click.echo(f"  • Cache Directory: {Config.CACHE_DIR}")
            click.echo(f"  • Claude Skills: {Config.CLAUDE_SKILLS_DIR}")

            profile = Config.load_user_profile()
            if profile:
                click.echo(f"\n👤 User Profile:")
                click.echo(f"  • Setup completed: {profile.get('setup_completed', False)}")
                click.echo(f"  • Role: {profile.get('role', 'N/A')}")

        elif key and not value:
            # Show specific config value
            profile = Config.load_user_profile()
            if key in profile:
                click.echo(f"{key}: {profile[key]}")
            else:
                click.echo(f"⚠️  Config key '{key}' not found")

        elif key and value:
            # Set config value
            profile = Config.load_user_profile()
            profile[key] = value
            Config.save_user_profile(profile)
            click.echo(f"✅ Set {key} = {value}")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def reset(confirm):
    """Reset SkillForge to defaults"""
    from skillforge.generators.config import Config
    import shutil

    try:
        if not confirm:
            click.echo("⚠️  This will delete all SkillForge data:")
            click.echo("  • User profile")
            click.echo("  • Usage analytics")
            click.echo("  • Generated skills")
            click.echo("  • Cache")
            response = input("\nAre you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                click.echo("\n❌ Reset cancelled")
                return

        click.echo("\n🔄 Resetting SkillForge...")

        # Remove data directory
        if Config.DATA_DIR.exists():
            shutil.rmtree(Config.DATA_DIR)
            click.echo("  ✅ Removed data directory")

        # Recreate directories
        Config.ensure_directories()
        click.echo("  ✅ Recreated directory structure")

        click.echo("\n✅ SkillForge has been reset to defaults")
        click.echo("\n💡 Use /sf:wizard in Claude Code to set up again")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
def status():
    """Show SkillForge installation status"""
    from pathlib import Path
    from skillforge.generators.config import Config

    click.echo("📊 SkillForge Status")
    click.echo("=" * 50)
    click.echo("")

    # Check installation
    skillforge_home = Config.SKILLFORGE_HOME
    if skillforge_home.exists():
        click.echo(f"✅ Installation found: {skillforge_home}")
    else:
        click.echo(f"❌ Not installed: {skillforge_home}")

    # Check data directory
    if Config.DATA_DIR.exists():
        click.echo(f"✅ Data directory: {Config.DATA_DIR}")

        # Check for user profile
        profile_path = Config.DATA_DIR / "user_profile.json"
        if profile_path.exists():
            profile = Config.load_user_profile()
            if profile.get("setup_completed"):
                click.echo("✅ Setup completed")
            else:
                click.echo("⚠️  Setup not completed - run /sf:wizard in Claude Code")
        else:
            click.echo("⚠️  No user profile found")
    else:
        click.echo(f"❌ Data directory not found: {Config.DATA_DIR}")

    click.echo("")


if __name__ == "__main__":
    main()

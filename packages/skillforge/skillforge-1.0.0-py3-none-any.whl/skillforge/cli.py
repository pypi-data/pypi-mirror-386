"""
SkillForge CLI - Command Line Interface

Main entry point for skillforge command.
Full implementation will be added in later phases.
"""

import click
from skillforge import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """
    SkillForge - Meta-Programming Framework for Claude Code Skills

    Generate, orchestrate, and optimize personalized Claude Code skills automatically.
    """
    pass


@main.command()
def init():
    """Initialize SkillForge in the current directory"""
    click.echo("🔨 SkillForge Initialization")
    click.echo("=" * 50)
    click.echo("")
    click.echo("⚠️  This feature is not yet implemented.")
    click.echo("SkillForge is currently in development (Phase 1).")
    click.echo("")
    click.echo("For now, please use Claude Code directly with:")
    click.echo("  /sf:wizard")
    click.echo("")


@main.command()
def version():
    """Show SkillForge version"""
    click.echo(f"SkillForge version {__version__}")


@main.command()
def status():
    """Show SkillForge installation status"""
    import os
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

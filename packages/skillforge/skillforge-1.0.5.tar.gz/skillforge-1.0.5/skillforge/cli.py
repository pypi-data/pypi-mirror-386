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

    Generate, orchestrate, and optimize personalized Claude Code skills automatically.
    """
    pass


@main.command()
def wizard():
    """Launch interactive skill generation wizard"""
    from skillforge.generators.wizard_engine import WizardEngine
    from skillforge.generators.skill_generator import SkillGenerator
    from skillforge.generators.config import Config

    try:
        click.echo("🧙 SkillForge Setup Wizard")
        click.echo("=" * 60)
        click.echo("")

        # Initialize and run wizard
        wizard_engine = WizardEngine()
        profile = wizard_engine.run()

        # Check if user completed wizard
        if not profile.get("setup_completed"):
            click.echo("\n❌ Setup cancelled. Run 'skillforge wizard' again anytime.")
            return

        # Save profile
        Config.save_user_profile(profile)
        click.echo(f"\n✅ Profile saved to {Config.DATA_DIR / 'user_profile.json'}")

        # Determine which skills to generate
        skills_to_generate = wizard_engine.determine_skills(profile)

        if not skills_to_generate:
            click.echo("\n⚠️  No skills to generate based on your profile.")
            return

        click.echo(f"\n🚀 Generating {len(skills_to_generate)} skills...")
        click.echo("")

        # Generate each skill
        generator = SkillGenerator()
        success_count = 0
        failed_skills = []

        for skill_type in skills_to_generate:
            try:
                skill_path = generator.generate(skill_type, profile)
                click.echo(f"✅ Generated: {skill_path}")
                success_count += 1
            except Exception as e:
                click.echo(f"❌ Failed to generate {skill_type}: {e}")
                failed_skills.append(skill_type)

        # Show summary
        click.echo("\n" + "=" * 60)
        click.echo("🎉 Setup Complete!")
        click.echo("=" * 60)
        click.echo(f"\n📊 Summary:")
        click.echo(f"  • Skills generated: {success_count}/{len(skills_to_generate)}")
        if failed_skills:
            click.echo(f"  • Failed skills: {', '.join(failed_skills)}")
        click.echo(f"\n📚 Skills are ready to use in Claude Code!")
        click.echo(f"💡 Restart Claude Code to activate your new skills.")
        click.echo(f"\n📋 Next steps:")
        click.echo(f"  • skillforge list - View all your skills")
        click.echo(f"  • skillforge analyze - See usage patterns")
        click.echo(f"  • skillforge optimize - Optimize your skills")
        click.echo("")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Wizard interrupted. Progress has been saved.")
        click.echo("Run 'skillforge wizard' to resume.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        click.echo("\nPlease report this issue at:")
        click.echo("https://github.com/omarpioselli/SkillForge/issues")


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
def init():
    """Initialize SkillForge (alias for wizard)"""
    from skillforge.generators.config import Config

    # Check if already initialized
    profile_path = Config.DATA_DIR / "user_profile.json"
    if profile_path.exists():
        profile = Config.load_user_profile()
        if profile.get("setup_completed"):
            click.echo("✅ SkillForge is already initialized!")
            click.echo(f"\nProfile location: {profile_path}")
            click.echo(f"\nTo reconfigure, run: skillforge wizard")
            return

    # Not initialized, run wizard
    click.echo("🔨 Initializing SkillForge...")
    click.echo("")
    import sys
    from click.testing import CliRunner

    # Call wizard command
    runner = CliRunner()
    result = runner.invoke(wizard)
    sys.exit(result.exit_code)


@main.command()
def version():
    """Show SkillForge version"""
    click.echo(f"SkillForge version {__version__}")


@main.command()
@click.argument('skill_type')
@click.option('--force', is_flag=True, help='Regenerate even if skill exists')
@click.option('--preview', is_flag=True, help='Preview skill without saving')
@click.option('--no-docs', is_flag=True, help='Skip documentation fetching')
def generate(skill_type, force, preview, no_docs):
    """Generate a specific skill"""
    from skillforge.generators.skill_generator import SkillGenerator
    from skillforge.generators.config import Config

    try:
        # Check if profile exists
        profile = Config.load_user_profile()
        if not profile.get("setup_completed"):
            click.echo("⚠️  No user profile found. Please run 'skillforge wizard' first.")
            return

        click.echo(f"🎨 Generating skill: {skill_type}")
        click.echo("=" * 60)

        generator = SkillGenerator()
        skill_path = generator.generate(
            skill_type,
            profile,
            force=force,
            preview=preview,
            fetch_docs=not no_docs
        )

        if preview:
            click.echo("\n📄 Preview generated successfully!")
        else:
            click.echo(f"\n✅ Skill generated: {skill_path}")
            click.echo("\n💡 Restart Claude Code to activate the skill.")

    except FileExistsError:
        click.echo(f"\n⚠️  Skill '{skill_type}' already exists.")
        click.echo("Use --force to regenerate.")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
@click.option('--detailed', is_flag=True, help='Show detailed analytics')
@click.option('--days', default=30, help='Number of days to analyze (default: 30)')
def analyze(detailed, days):
    """Analyze skill usage patterns"""
    from skillforge.analyzers.usage_tracker import UsageTracker
    from skillforge.analyzers.pattern_detector import PatternDetector
    from skillforge.generators.config import Config

    try:
        click.echo("📊 SkillForge Analytics")
        click.echo("=" * 60)

        tracker = UsageTracker()
        usage_data = tracker.get_usage_summary(days=days)

        if not usage_data:
            click.echo("\n⚠️  No usage data found.")
            click.echo("Skills will be tracked as you use them in Claude Code.")
            return

        # Show usage summary
        click.echo(f"\n📈 Usage Summary (Last {days} Days)")
        click.echo(f"  • Total Sessions: {usage_data.get('total_sessions', 0)}")
        click.echo(f"  • Total Skills Used: {usage_data.get('total_skills', 0)}")
        click.echo(f"  • Success Rate: {usage_data.get('success_rate', 0):.1f}%")

        # Show most used skills
        if usage_data.get('most_used_skills'):
            click.echo("\n🏆 Most Used Skills:")
            for skill in usage_data['most_used_skills'][:5]:
                click.echo(f"  • {skill['name']}: {skill['count']} times")

        # Detect patterns
        if detailed:
            click.echo("\n🔍 Detected Patterns:")
            detector = PatternDetector()
            patterns = detector.detect_patterns()

            if patterns:
                for pattern in patterns:
                    confidence = pattern.get('confidence', 0) * 100
                    click.echo(f"\n  ✨ {pattern['description']}")
                    click.echo(f"     Confidence: {confidence:.0f}%")
                    if confidence >= 80:
                        click.echo("     → Recommended for auto-application")
            else:
                click.echo("  No significant patterns detected yet.")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
@click.option('--skill', help='Optimize specific skill')
@click.option('--all', 'all_skills', is_flag=True, help='Optimize all skills')
def optimize(skill, all_skills):
    """Optimize skills for better performance"""
    from skillforge.analyzers.skill_optimizer import SkillOptimizer

    try:
        click.echo("⚡ SkillForge Optimizer")
        click.echo("=" * 60)

        optimizer = SkillOptimizer()

        if skill:
            click.echo(f"\n🔍 Analyzing skill: {skill}")
            result = optimizer.optimize_skill(skill)
            click.echo(f"\n✅ Optimization complete:")
            click.echo(f"  • Original size: {result['original_size']} tokens")
            click.echo(f"  • Optimized size: {result['optimized_size']} tokens")
            click.echo(f"  • Reduction: {result['reduction_percent']}%")

        elif all_skills:
            click.echo("\n🔍 Analyzing all skills...")
            results = optimizer.optimize_all_skills()
            total_saved = sum(r['tokens_saved'] for r in results)
            click.echo(f"\n✅ Optimized {len(results)} skills")
            click.echo(f"  • Total tokens saved: {total_saved}")

        else:
            # Show optimization suggestions
            suggestions = optimizer.get_optimization_suggestions()
            if suggestions:
                click.echo("\n💡 Optimization Suggestions:")
                for suggestion in suggestions:
                    click.echo(f"\n  • {suggestion['skill']}")
                    click.echo(f"    Size: {suggestion['size']} tokens")
                    click.echo(f"    Potential savings: {suggestion['potential_savings']} tokens")
                click.echo(f"\n📋 Run 'skillforge optimize --all' to optimize all skills")
            else:
                click.echo("\n✅ All skills are already optimized!")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


@main.command()
@click.option('--skill', help='Update specific skill')
@click.option('--all', 'all_skills', is_flag=True, help='Update all skills')
def update(skill, all_skills):
    """Update skills with latest documentation"""
    from skillforge.generators.skill_generator import SkillGenerator
    from skillforge.generators.config import Config

    try:
        click.echo("🔄 SkillForge Updater")
        click.echo("=" * 60)

        profile = Config.load_user_profile()
        generator = SkillGenerator()

        if skill:
            click.echo(f"\n📥 Updating skill: {skill}")
            result = generator.update_skill(skill, profile)
            click.echo(f"\n✅ Updated successfully!")
            if result.get('changes'):
                click.echo(f"  • Changes: {result['changes']}")

        elif all_skills:
            click.echo("\n📥 Updating all skills with latest documentation...")
            skills = Config.get_installed_skills()
            updated = 0
            for skill_name in skills:
                try:
                    generator.update_skill(skill_name, profile)
                    click.echo(f"  ✅ {skill_name}")
                    updated += 1
                except Exception as e:
                    click.echo(f"  ❌ {skill_name}: {e}")
            click.echo(f"\n✅ Updated {updated}/{len(skills)} skills")

        else:
            click.echo("\n💡 Specify a skill to update:")
            click.echo("  skillforge update --skill nextjs-fullstack")
            click.echo("  skillforge update --all")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


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
            click.echo("Run 'skillforge wizard' to generate your first skills!")
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
@click.option('--project', help='Project directory to analyze (default: current)')
def introspect(project):
    """Analyze current project and suggest skills"""
    from skillforge.analyzers.skill_discovery import SkillDiscovery
    from skillforge.analyzers.intent_analyzer import IntentAnalyzer
    from pathlib import Path

    try:
        project_dir = Path(project) if project else Path.cwd()

        click.echo("🔍 SkillForge Introspection")
        click.echo("=" * 60)
        click.echo(f"\n📁 Analyzing project: {project_dir}")

        # Detect tech stack
        click.echo("\n🔎 Detecting technologies...")
        # This would use project scanning logic
        click.echo("  • This feature analyzes your project structure")
        click.echo("  • Detects frameworks and libraries")
        click.echo("  • Suggests relevant skills to generate")
        click.echo("\n⚠️  Full implementation coming soon!")

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
        click.echo("\n💡 Run 'skillforge wizard' to set up again")

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

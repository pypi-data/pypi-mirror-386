#!/usr/bin/env python3
"""
Script to update slash command .md files with CLI command implementations.
Adds implementation sections that tell Claude to call the CLI commands.
"""

from pathlib import Path

# Command mappings: slash command name -> CLI command
COMMANDS = {
    "wizard": {
        "cli": "skillforge wizard",
        "description": "Launch interactive skill generation wizard",
        "interactive": True
    },
    "generate": {
        "cli": "skillforge generate",
        "description": "Generate a specific skill",
        "interactive": False,
        "note": "Takes skill_type as argument and optional flags (--force, --preview, --no-docs)"
    },
    "analyze": {
        "cli": "skillforge analyze",
        "description": "Analyze skill usage patterns",
        "interactive": False,
        "note": "Optional flags: --detailed, --days N"
    },
    "optimize": {
        "cli": "skillforge optimize",
        "description": "Optimize skills for better performance",
        "interactive": False,
        "note": "Optional flags: --skill SKILL_NAME, --all"
    },
    "update": {
        "cli": "skillforge update",
        "description": "Update skills with latest documentation",
        "interactive": False,
        "note": "Optional flags: --skill SKILL_NAME, --all"
    },
    "list": {
        "cli": "skillforge list",
        "description": "List all installed SkillForge skills",
        "interactive": False
    },
    "introspect": {
        "cli": "skillforge introspect",
        "description": "Analyze current project and suggest skills",
        "interactive": False,
        "note": "Optional: --project /path/to/project"
    },
    "config": {
        "cli": "skillforge config",
        "description": "View or edit SkillForge configuration",
        "interactive": False,
        "note": "Usage: skillforge config [KEY] [VALUE]"
    },
    "reset": {
        "cli": "skillforge reset",
        "description": "Reset SkillForge to defaults",
        "interactive": True,
        "note": "Requires confirmation. Use --confirm to skip prompt."
    },
    "status": {
        "cli": "skillforge status",
        "description": "Show SkillForge installation status",
        "interactive": False
    }
}


def generate_implementation_section(cmd_name, cmd_info):
    """Generate the implementation section text"""
    cli_command = cmd_info["cli"]
    is_interactive = cmd_info.get("interactive", False)
    note = cmd_info.get("note", "")

    impl = f"""
## Implementation

When user runs `/sf:{cmd_name}`, Claude Code should execute:

```bash
{cli_command}
```
"""

    if note:
        impl += f"\n**Note**: {note}\n"

    if is_interactive:
        impl += """
**Important**: This command runs interactively in the terminal. Claude should:
1. Use the Bash tool to execute the command
2. Allow the user to interact with the command directly
3. Not interrupt or try to automate the interactive prompts
"""
    else:
        impl += """
**Usage**: Claude should use the Bash tool to execute this command and display the results to the user.
"""

    return impl


def update_command_file(cmd_path: Path, cmd_name: str, cmd_info: dict):
    """Update a single command file"""
    if not cmd_path.exists():
        print(f"  ⚠️  File not found: {cmd_path}")
        return False

    content = cmd_path.read_text()

    # Check if implementation section already exists
    if "## Implementation" in content:
        # Remove old implementation section
        lines = content.split("\n")
        new_lines = []
        skip_until_next_section = False

        for line in lines:
            if line.strip() == "## Implementation":
                skip_until_next_section = True
                continue
            elif skip_until_next_section and line.startswith("## "):
                skip_until_next_section = False

            if not skip_until_next_section:
                new_lines.append(line)

        content = "\n".join(new_lines).rstrip()

    # Add new implementation section at the end
    impl_section = generate_implementation_section(cmd_name, cmd_info)

    # Find the last ## section and add implementation before examples if they exist
    if "## Example" in content:
        # Insert before examples
        content = content.replace("## Example", impl_section + "\n## Example")
    else:
        # Append at end
        content += "\n" + impl_section

    cmd_path.write_text(content)
    print(f"  ✅ Updated: {cmd_name}.md")
    return True


def main():
    print("🔧 Updating Slash Command Files")
    print("=" * 60)

    # Get commands directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    commands_dir = repo_root / "skillforge" / "data" / "skill_files" / "commands" / "sf"

    if not commands_dir.exists():
        print(f"\n❌ Commands directory not found: {commands_dir}")
        return 1

    print(f"\n📁 Commands directory: {commands_dir}\n")

    updated = 0
    failed = 0

    for cmd_name, cmd_info in COMMANDS.items():
        cmd_file = commands_dir / f"{cmd_name}.md"

        if update_command_file(cmd_file, cmd_name, cmd_info):
            updated += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"✅ Updated {updated} command files")
    if failed > 0:
        print(f"❌ Failed {failed} command files")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

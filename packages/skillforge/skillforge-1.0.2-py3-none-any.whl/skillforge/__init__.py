"""
SkillForge - Meta-Programming Framework for Claude Code Skills

SkillForge transforms Claude Code into an intelligent development partner by:
- Generating personalized skills for your tech stack
- Orchestrating multiple skills intelligently
- Learning from your patterns and preferences
- Keeping skills updated automatically
"""

__version__ = "1.0.2"
__author__ = "Omar Pioselli"

# Make key components available at package level
from skillforge.generators.config import Config

__all__ = ["__version__", "Config"]

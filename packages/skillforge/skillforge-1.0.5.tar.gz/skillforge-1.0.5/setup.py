"""
SkillForge - Meta-Programming Framework for Claude Code Skills

Setup script for package installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="skillforge",
    version="0.0.1-dev",
    author="Omar Pioselli",
    author_email="",  # Add email if desired
    description="Meta-programming framework for Claude Code skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/omarpioselli/SkillForge",  # Update with actual URL
    project_urls={
        "Bug Tracker": "https://github.com/omarpioselli/SkillForge/issues",
        "Documentation": "https://github.com/omarpioselli/SkillForge/blob/main/docs/",
        "Source Code": "https://github.com/omarpioselli/SkillForge",
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    python_requires=">=3.11",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "click>=8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skillforge=skillforge.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "skillforge": [
            "data/skill_files/**/*",
            "templates/**/*.template",
            "templates/**/*.md",
        ],
    },
    zip_safe=False,
    keywords="claude-code skills meta-programming ai-development code-generation",
)

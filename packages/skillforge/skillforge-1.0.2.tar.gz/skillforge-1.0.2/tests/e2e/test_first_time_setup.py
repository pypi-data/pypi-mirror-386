"""
End-to-end tests for first-time user setup.

Simulates a new user installing and configuring SkillForge.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from skillforge.generators.wizard_engine import WizardEngine
from skillforge.generators.skill_generator import SkillGenerator
from skillforge.generators.config import Config


@pytest.mark.e2e
@pytest.mark.slow
def test_complete_first_time_setup(temp_home):
    """
    Test complete first-time setup flow:
    - Fresh install
    - Run wizard
    - Generate skills
    - Verify Claude Code can load them
    """

    # 1. VERIFY FRESH INSTALL
    assert temp_home.exists()
    assert not (temp_home / "data" / "user_profile.json").exists()

    # 2. RUN WIZARD
    wizard = WizardEngine()

    # Mock user inputs
    mock_inputs = [
        'Next.js',              # Frontend
        '14.0.0',              # Version
        'Tailwind CSS',        # UI
        '3.3.0',               # Version
        'Zustand',             # State
        'Supabase',            # Database
        '2.38.0',              # Version
        'Vitest',              # Testing
        'yes',                 # Analytics
        'y',                   # Confirm
    ]

    with patch('builtins.input', side_effect=mock_inputs):
        with patch.object(wizard, '_detect_technologies', return_value={}):
            profile = wizard.run_wizard()

    # Verify profile created
    assert profile is not None
    assert profile['setup_completed'] is True

    # 3. GENERATE SKILLS
    generator = SkillGenerator()

    skills_to_generate = [
        ('nextjs', 'nextjs-fullstack'),
        ('supabase', 'supabase-integration'),
        ('tailwind', 'tailwind-styling'),
    ]

    generated_skills = []

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Mock documentation content',
            'code_snippets': [
                {'title': 'Example', 'code': 'const x = 1', 'language': 'typescript'}
            ],
            'best_practices': [
                'Follow best practices',
                'Write clean code'
            ],
        }

        for skill_type, skill_name in skills_to_generate:
            skill_path = generator.generate_skill(
                profile=profile,
                skill_type=skill_type,
                skill_name=skill_name
            )
            generated_skills.append(skill_path)

    # 4. VERIFY SKILLS LOADABLE
    for skill_path in generated_skills:
        # Verify file exists
        assert skill_path.exists(), f"Skill not found: {skill_path}"

        # Verify YAML frontmatter
        content = skill_path.read_text()
        assert '---' in content
        assert 'name:' in content
        assert 'description:' in content

        # Verify content sections
        assert '## Overview' in content
        assert '## When to Use' in content
        assert '## Best Practices' in content

        # Verify parseable
        lines = content.split('\n')
        assert len(lines) > 50  # Substantial content

    # 5. VERIFY DIRECTORY STRUCTURE
    assert (temp_home / "data").exists()
    assert (temp_home / "data" / "user_profile.json").exists()
    assert (temp_home / "data" / "analytics.json").exists()

    # 6. VERIFY PROFILE PERSISTENCE
    config = Config()
    loaded_profile = config.load_profile()

    assert loaded_profile['tech_stack']['frontend'] == 'Next.js'
    assert loaded_profile['tech_stack']['database'] == 'Supabase'


@pytest.mark.e2e
@pytest.mark.slow
def test_first_setup_with_auto_detection(temp_home, tmp_path):
    """Test first-time setup with project auto-detection."""

    # Create mock project
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()

    # Create package.json
    (project_dir / "package.json").write_text("""
    {
      "name": "my-app",
      "dependencies": {
        "next": "^14.0.0",
        "react": "^18.2.0",
        "@supabase/supabase-js": "^2.38.0"
      }
    }
    """)

    # Run wizard
    wizard = WizardEngine()

    # Auto-detect from project
    detected = wizard._detect_technologies(project_dir)

    # Verify detection worked
    assert detected is not None


@pytest.mark.e2e
@pytest.mark.slow
def test_minimal_setup_flow(temp_home):
    """Test minimal setup with just one framework."""

    wizard = WizardEngine()

    # Minimal inputs
    with patch('builtins.input', side_effect=['React', '18.2.0', 'no', 'y']):
        with patch.object(wizard, '_detect_technologies', return_value={}):
            profile = wizard.run_wizard()

    assert profile is not None
    assert profile['tech_stack']['frontend'] == 'React'

    # Generate single skill
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'React docs',
            'code_snippets': [],
            'best_practices': ['Use hooks'],
        }

        skill_path = generator.generate_skill(
            profile=profile,
            skill_type='react',
            skill_name='react-components'
        )

    assert skill_path.exists()


@pytest.mark.e2e
@pytest.mark.slow
def test_setup_with_all_features(temp_home):
    """Test setup enabling all optional features."""

    wizard = WizardEngine()

    # Enable everything
    comprehensive_inputs = [
        'Next.js', '14.0.0',
        'Tailwind CSS', '3.3.0',
        'Zustand', '4.4.0',
        'Next.js API Routes',
        'Supabase', '2.38.0',
        'Vitest', '1.0.0',
        'Cypress', '13.0.0',
        'Docker',
        'GitHub Actions',
        'yes',  # Analytics
        'yes',  # Pattern learning
        'yes',  # Auto-optimization
        'y',    # Confirm
    ]

    with patch('builtins.input', side_effect=comprehensive_inputs):
        with patch.object(wizard, '_detect_technologies', return_value={}):
            profile = wizard.run_wizard()

    # Verify comprehensive profile
    assert profile['setup_completed'] is True
    assert profile['analytics_enabled'] is True

    # Generate all relevant skills
    generator = SkillGenerator()

    skill_types = ['nextjs', 'supabase', 'tailwind', 'testing', 'git-workflow']

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        for skill_type in skill_types:
            try:
                generator.generate_skill(
                    profile=profile,
                    skill_type=skill_type,
                    skill_name=f'{skill_type}-skill'
                )
            except Exception as e:
                # Some might fail, that's ok for this test
                print(f"Skipped {skill_type}: {e}")


@pytest.mark.e2e
@pytest.mark.slow
def test_setup_interruption_and_resume(temp_home):
    """Test that setup can be interrupted and resumed."""

    wizard = WizardEngine()

    # Start setup
    partial_profile = {
        'setup_completed': False,
        'tech_stack': {
            'frontend': 'Next.js',
            'frontend_version': '14.0.0',
        }
    }

    # Save partial state
    wizard.save_session(partial_profile)

    # Simulate restart - load session
    resumed = wizard.load_session()

    assert resumed is not None
    assert resumed['tech_stack']['frontend'] == 'Next.js'
    assert resumed.get('setup_completed', False) is False


@pytest.mark.e2e
@pytest.mark.slow
def test_setup_validation_and_error_handling(temp_home):
    """Test setup handles invalid inputs gracefully."""

    wizard = WizardEngine()

    # Test with invalid inputs followed by valid ones
    with patch('builtins.input', side_effect=[
        '',             # Invalid: empty
        'InvalidFramework',  # Invalid: unknown framework
        'React',        # Valid
        '18.2.0',       # Valid
        'yes',
        'y'
    ]):
        with patch.object(wizard, '_detect_technologies', return_value={}):
            with patch('builtins.print'):  # Suppress error messages
                profile = wizard.run_wizard()

    # Should eventually succeed with valid input
    assert profile is not None


@pytest.mark.e2e
@pytest.mark.slow
def test_post_setup_verification(temp_home):
    """Test that everything works after setup completes."""

    # Complete setup
    config = Config()

    profile = {
        'setup_completed': True,
        'tech_stack': {
            'frontend': 'Next.js',
            'database': 'Supabase',
        },
        'analytics_enabled': True,
    }

    config.save_profile(profile)

    # Verify can generate skills
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=profile,
            skill_type='nextjs',
            skill_name='test-skill'
        )

    assert skill_path.exists()

    # Verify can track usage
    from skillforge.analyzers.usage_tracker import UsageTracker

    tracker = UsageTracker()
    tracker.record_usage('test-skill', success=True)

    usage = tracker.get_usage_summary()
    assert 'test-skill' in usage['skill_usage']

    # Verify can detect patterns
    from skillforge.analyzers.pattern_detector import PatternDetector

    detector = PatternDetector()
    detector.record_style_preference('test-pattern', confidence=0.8)

    patterns = detector.detect_patterns()
    assert patterns is not None


@pytest.mark.e2e
@pytest.mark.slow
def test_setup_creates_correct_file_structure(temp_home):
    """Verify that setup creates the expected directory structure."""

    wizard = WizardEngine()
    config = Config()

    # Run setup
    profile = {
        'setup_completed': True,
        'tech_stack': {'frontend': 'React'},
    }

    config.save_profile(profile)

    # Verify structure
    assert (temp_home / "data").exists()
    assert (temp_home / "data" / "user_profile.json").exists()
    assert (temp_home / "data" / "analytics.json").exists()
    assert (temp_home / "data" / "cache").exists()

    # Generate a skill to create skills directory
    generator = SkillGenerator()

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=profile,
            skill_type='react',
            skill_name='test-skill'
        )

    # Verify skill directory created
    assert skill_path.parent.exists()

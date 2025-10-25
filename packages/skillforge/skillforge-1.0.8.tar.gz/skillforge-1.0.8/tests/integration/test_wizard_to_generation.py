"""
Integration tests for wizard to skill generation flow.

Tests the complete flow from running the wizard to generating skills.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from skillforge.generators.wizard_engine import WizardEngine
from skillforge.generators.skill_generator import SkillGenerator
from skillforge.generators.config import Config


@pytest.mark.integration
def test_wizard_to_single_skill_generation(temp_home, sample_profile, skill_templates):
    """Test complete flow: wizard -> profile -> single skill generation."""
    # Skip wizard - use pre-built profile (wizard is tested separately in unit tests)
    # This integration test focuses on profile -> skill generation flow

    # Save profile to simulate wizard completion
    Config.save_user_profile(sample_profile)

    # Verify profile was saved
    loaded_profile = Config.load_user_profile()
    assert loaded_profile is not None
    assert 'tech_stack' in loaded_profile

    # Generate skill from profile
    generator = SkillGenerator()
    generator.template_dir = skill_templates  # Use test templates

    with patch.object(generator.doc_fetcher, 'fetch') as mock_fetch:
        from skillforge.generators.doc_fetcher import LibraryDocs, DocSource
        import time
        mock_fetch.return_value = LibraryDocs(
            library_id='/vercel/next.js',
            library_name='Next.js',
            version='14.0.0',
            content='Mock Next.js documentation',
            examples=[],
            best_practices=['Use Server Components'],
            source=DocSource(type='cache', timestamp=time.time(), library_id='/vercel/next.js', version='14.0.0'),
            topics_covered=[],
            raw_data={}
        )

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-fullstack'
        )

    # Verify skill was generated
    assert skill_path.exists()
    assert skill_path.name == 'SKILL.md'

    # Verify skill content
    content = skill_path.read_text()
    assert 'nextjs-fullstack' in content.lower()


@pytest.mark.integration
def test_wizard_to_multiple_skills_generation(temp_home, sample_profile, skill_templates):
    """Test generating multiple skills from wizard profile."""
    # Save profile
    Config.save_user_profile(sample_profile)

    # Generate multiple skills
    generator = SkillGenerator()
    generator.template_dir = skill_templates  # Use test templates
    skill_types = ['nextjs', 'supabase', 'git-workflow']

    generated_skills = []

    with patch.object(generator.doc_fetcher, 'fetch') as mock_fetch:
        from skillforge.generators.doc_fetcher import LibraryDocs, DocSource
        import time
        mock_fetch.return_value = LibraryDocs(
            library_id='/mock/library',
            library_name='Mock Library',
            version='1.0.0',
            content='Mock documentation',
            examples=[],
            best_practices=[],
            source=DocSource(type='cache', timestamp=time.time(), library_id='/mock/library', version='1.0.0'),
            topics_covered=[],
            raw_data={}
        )

        for skill_type in skill_types:
            skill_path = generator.generate_skill(
                profile=sample_profile,
                skill_type=skill_type,
                skill_name=f'{skill_type}-skill'
            )
            generated_skills.append(skill_path)

    # Verify all skills were generated
    assert len(generated_skills) == len(skill_types)
    for skill_path in generated_skills:
        assert skill_path.exists()
        assert skill_path.name == 'SKILL.md'


@pytest.mark.integration
def test_wizard_profile_persistence(temp_home):
    """Test that wizard profile persists correctly."""
    wizard = WizardEngine()
    config = Config()

    # Create and save profile
    test_profile = {
        'setup_completed': True,
        'tech_stack': {
            'frontend': 'React',
            'backend': 'FastAPI',
        }
    }

    config.save_profile(test_profile)

    # Load profile
    loaded_profile = config.load_profile()

    # Verify loaded profile matches
    assert loaded_profile['setup_completed'] is True
    assert loaded_profile['tech_stack']['frontend'] == 'React'
    assert loaded_profile['tech_stack']['backend'] == 'FastAPI'


@pytest.mark.integration
def test_wizard_auto_detection_integration(temp_home, tmp_path):
    """Test wizard auto-detection with actual project files."""
    # Create mock project structure
    project_dir = tmp_path / "mock_project"
    project_dir.mkdir()

    # Create package.json
    package_json = project_dir / "package.json"
    package_json.write_text("""
    {
      "name": "test-app",
      "dependencies": {
        "next": "^14.0.0",
        "react": "^18.2.0",
        "@supabase/supabase-js": "^2.38.0",
        "tailwindcss": "^3.3.0"
      }
    }
    """)

    # Test auto-detection
    wizard = WizardEngine()
    detected = wizard._detect_technologies(project_dir)

    # Verify detection
    assert 'next' in str(detected).lower() or 'react' in str(detected).lower()


@pytest.mark.integration
def test_generation_with_templates(temp_home, sample_profile, skill_templates):
    """Test skill generation uses correct templates."""
    # Save profile first so SkillGenerator doesn't prompt
    Config.save_user_profile(sample_profile)

    generator = SkillGenerator()
    generator.template_dir = skill_templates  # Use test templates

    # Generate skill and verify template was used
    with patch.object(generator.doc_fetcher, 'fetch') as mock_fetch:
        from skillforge.generators.doc_fetcher import LibraryDocs, DocSource
        import time
        mock_fetch.return_value = LibraryDocs(
            library_id='/vercel/next.js',
            library_name='Next.js',
            version='14.0.0',
            content='Mock documentation',
            examples=[],
            best_practices=[],
            source=DocSource(type='cache', timestamp=time.time(), library_id='/vercel/next.js', version='14.0.0'),
            topics_covered=[],
            raw_data={}
        )

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='test-skill'
        )

        content = skill_path.read_text()

        # Verify template sections are present
        assert '## Overview' in content
        assert '## When to Use' in content or '## When to Use' in content
        assert '## Best Practices' in content or '## Usage' in content


@pytest.mark.integration
def test_generation_failure_rollback(temp_home, skill_templates):
    """Test that failed generation rolls back properly."""
    profile = {
        'tech_stack': {
            'frontend': 'Next.js',
        }
    }

    # Save profile to avoid stdin prompt
    Config.save_user_profile(profile)

    generator = SkillGenerator()
    generator.template_dir = skill_templates  # Use test templates

    # Force generation failure
    with patch('skillforge.generators.template_processor.TemplateProcessor.process') as mock_process:
        mock_process.side_effect = Exception("Template processing failed")

        with pytest.raises(Exception, match="Template processing failed"):
            generator.generate_skill(
                profile=profile,
                skill_type='nextjs',
                skill_name='test-skill'
            )

    # Verify no partial files left behind
    skill_dir = Config.SKILLFORGE_HOME / "skills" / "test-skill"
    assert not skill_dir.exists()


@pytest.mark.integration
def test_wizard_resume_functionality(temp_home):
    """Test wizard can resume from saved session."""
    wizard = WizardEngine()

    # Create partial session
    partial_answers = {
        'frontend': 'Next.js',
        'frontend_version': '14.0.0',
    }

    wizard.save_session(partial_answers)

    # Resume session
    resumed = wizard.load_session()

    assert resumed is not None
    assert resumed['frontend'] == 'Next.js'
    assert resumed['frontend_version'] == '14.0.0'


@pytest.mark.integration
def test_bulk_skill_generation(temp_home, sample_profile, skill_templates):
    """Test generating all skills for a tech stack at once."""
    config = Config()
    config.save_profile(sample_profile)

    generator = SkillGenerator()
    generator.template_dir = skill_templates  # Use test templates

    # Determine skills to generate from profile
    skills_to_generate = [
        'nextjs-fullstack',
        'supabase-integration',
        'tailwind-styling',
        'git-workflow',
    ]

    generated = []

    with patch.object(generator.doc_fetcher, 'fetch') as mock_fetch:
        from skillforge.generators.doc_fetcher import LibraryDocs, DocSource
        import time
        mock_fetch.return_value = LibraryDocs(
            library_id='/mock/library',
            library_name='Mock Library',
            version='1.0.0',
            content='Mock documentation',
            examples=[],
            best_practices=['Follow best practices'],
            source=DocSource(type='cache', timestamp=time.time(), library_id='/mock/library', version='1.0.0'),
            topics_covered=[],
            raw_data={}
        )

        for skill_name in skills_to_generate:
            try:
                skill_path = generator.generate_skill(
                    profile=sample_profile,
                    skill_type=skill_name.split('-')[0],
                    skill_name=skill_name
                )
                generated.append(skill_path)
            except Exception as e:
                # Log but continue
                print(f"Failed to generate {skill_name}: {e}")

    # Verify at least some skills were generated
    assert len(generated) > 0

    for skill_path in generated:
        assert skill_path.exists()

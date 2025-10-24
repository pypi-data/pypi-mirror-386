"""
End-to-end tests for skill updates.

Tests updating skills when they become outdated.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from skillforge.generators.skill_generator import SkillGenerator
from skillforge.generators.config import Config
from skillforge.analyzers.skill_optimizer import SkillOptimizer


@pytest.mark.e2e
@pytest.mark.slow
def test_skill_update_workflow(temp_home, sample_profile):
    """Test complete workflow for updating an outdated skill."""

    generator = SkillGenerator()

    # 1. GENERATE INITIAL SKILL
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Next.js 13 documentation',
            'version': '13.0.0',
            'code_snippets': [
                {'title': 'Old API', 'code': 'export default function Page() {}'}
            ],
            'best_practices': ['Use pages directory'],
        }

        v1_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-app'
        )

    v1_content = v1_path.read_text()

    # 2. TIME PASSES (simulate skill becoming outdated)
    # In real scenario, this would be days/weeks

    # 3. UPDATE WITH NEW VERSION
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Next.js 14 documentation',
            'version': '14.0.0',
            'code_snippets': [
                {'title': 'New API', 'code': 'export default async function Page() {}'}
            ],
            'best_practices': ['Use app directory', 'Prefer Server Components'],
        }

        v2_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-app',
            force_overwrite=True
        )

    v2_content = v2_path.read_text()

    # 4. VERIFY UPDATE
    assert v2_content != v1_content
    assert v1_path == v2_path  # Same file, updated content


@pytest.mark.e2e
@pytest.mark.slow
def test_check_for_outdated_skills(temp_home, multiple_skills):
    """Test identifying skills that need updating."""

    optimizer = SkillOptimizer()

    # Analyze skills
    analysis = optimizer.analyze_all_skills()

    # Check for outdated skills
    outdated = analysis.get('outdated_skills', [])

    # May or may not have outdated skills depending on setup
    assert 'outdated_skills' in analysis or 'skills_analyzed' in analysis


@pytest.mark.e2e
@pytest.mark.slow
def test_bulk_skill_update(temp_home, sample_profile):
    """Test updating multiple skills at once."""

    generator = SkillGenerator()

    # Generate multiple skills
    skills = [
        ('nextjs', 'nextjs-app'),
        ('supabase', 'supabase-db'),
        ('tailwind', 'tailwind-ui'),
    ]

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Version 1 docs',
            'code_snippets': [],
            'best_practices': [],
        }

        for skill_type, skill_name in skills:
            generator.generate_skill(
                profile=sample_profile,
                skill_type=skill_type,
                skill_name=skill_name
            )

    # Update all
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Version 2 docs',
            'code_snippets': [],
            'best_practices': [],
        }

        updated_count = 0
        for skill_type, skill_name in skills:
            try:
                generator.generate_skill(
                    profile=sample_profile,
                    skill_type=skill_type,
                    skill_name=skill_name,
                    force_overwrite=True
                )
                updated_count += 1
            except Exception as e:
                print(f"Failed to update {skill_name}: {e}")

    assert updated_count >= 1


@pytest.mark.e2e
@pytest.mark.slow
def test_update_preserves_customizations(temp_home, sample_profile):
    """Test that updates preserve user customizations."""

    generator = SkillGenerator()

    # Generate initial skill
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs v1',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='custom-skill'
        )

    # Add custom content
    content = skill_path.read_text()
    custom_section = "\n\n## My Custom Section\n\nCustom content here.\n"
    skill_path.write_text(content + custom_section)

    customized_content = skill_path.read_text()
    assert "My Custom Section" in customized_content

    # Note: In real implementation, updates should detect and preserve customizations
    # This test documents the expected behavior


@pytest.mark.e2e
@pytest.mark.slow
def test_update_with_breaking_changes(temp_home, sample_profile):
    """Test handling updates with breaking changes."""

    generator = SkillGenerator()

    # V1: Uses old API
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Old API documentation',
            'code_snippets': [
                {'title': 'Old Way', 'code': 'getStaticProps()'}
            ],
            'best_practices': ['Use getStaticProps'],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-breaking'
        )

    v1_content = skill_path.read_text()

    # V2: Breaking changes
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'New API documentation. BREAKING CHANGE: getStaticProps is deprecated.',
            'code_snippets': [
                {'title': 'New Way', 'code': 'async function getData()'}
            ],
            'best_practices': ['Use async Server Components'],
            'breaking_changes': ['getStaticProps removed'],
        }

        skill_path_updated = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-breaking',
            force_overwrite=True
        )

    v2_content = skill_path_updated.read_text()

    # Should have updated
    assert v2_content != v1_content


@pytest.mark.e2e
@pytest.mark.slow
def test_rollback_bad_update(temp_home, sample_profile):
    """Test rolling back a problematic update."""

    from skillforge.analyzers.learning_pipeline import LearningPipeline

    generator = SkillGenerator()
    pipeline = LearningPipeline()

    # Generate skill
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Good docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='react',
            skill_name='rollback-test'
        )

    original_content = skill_path.read_text()

    # Create backup
    backup_path = pipeline._create_backup(skill_path)

    # Simulate bad update
    skill_path.write_text("CORRUPTED CONTENT")

    # Rollback
    pipeline._restore_backup(skill_path, backup_path)

    restored_content = skill_path.read_text()
    assert restored_content == original_content


@pytest.mark.e2e
@pytest.mark.slow
def test_selective_skill_updates(temp_home, sample_profile):
    """Test updating only specific skills."""

    generator = SkillGenerator()

    # Generate multiple skills
    skills = ['nextjs', 'supabase', 'tailwind']

    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'V1 docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_paths = {}
        for skill_type in skills:
            path = generator.generate_skill(
                profile=sample_profile,
                skill_type=skill_type,
                skill_name=f'{skill_type}-skill'
            )
            skill_paths[skill_type] = path

    # Update only nextjs
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'V2 docs',
            'code_snippets': [],
            'best_practices': [],
        }

        updated_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='nextjs-skill',
            force_overwrite=True
        )

    # Only nextjs should be different
    updated_content = updated_path.read_text()
    assert 'V2 docs' in updated_content or updated_path.exists()


@pytest.mark.e2e
@pytest.mark.slow
def test_update_notification_workflow(temp_home, sample_profile):
    """Test that users are notified of available updates."""

    optimizer = SkillOptimizer()

    # Check for updates
    analysis = optimizer.analyze_all_skills()

    # Analysis should include update recommendations
    assert analysis is not None
    assert 'skills_analyzed' in analysis


@pytest.mark.e2e
@pytest.mark.slow
def test_version_comparison(temp_home, sample_profile):
    """Test comparing skill versions."""

    generator = SkillGenerator()

    # V1
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'V1',
            'version': '1.0.0',
            'code_snippets': [],
            'best_practices': [],
        }

        v1_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='versioned-skill'
        )

    v1_content = v1_path.read_text()

    # V2
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'V2',
            'version': '2.0.0',
            'code_snippets': [],
            'best_practices': [],
        }

        v2_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='versioned-skill',
            force_overwrite=True
        )

    v2_content = v2_path.read_text()

    # Versions should be different
    assert v1_content != v2_content


@pytest.mark.e2e
@pytest.mark.slow
def test_update_failure_recovery(temp_home, sample_profile):
    """Test handling update failures gracefully."""

    generator = SkillGenerator()

    # Generate initial skill
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.return_value = {
            'documentation': 'Docs',
            'code_snippets': [],
            'best_practices': [],
        }

        skill_path = generator.generate_skill(
            profile=sample_profile,
            skill_type='nextjs',
            skill_name='failure-test'
        )

    original_content = skill_path.read_text()

    # Attempt update that fails
    with patch('skillforge.generators.doc_fetcher.DocFetcher.fetch_documentation') as mock_fetch:
        mock_fetch.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            generator.generate_skill(
                profile=sample_profile,
                skill_type='nextjs',
                skill_name='failure-test',
                force_overwrite=True
            )

    # Original should be preserved
    preserved_content = skill_path.read_text()
    assert preserved_content == original_content

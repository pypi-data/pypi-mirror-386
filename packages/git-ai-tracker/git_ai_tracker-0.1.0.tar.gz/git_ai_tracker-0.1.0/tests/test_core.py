"""Tests for git-ai package"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from git_ai.core import GitAI
from git_ai.cli import main


class TestGitAI:
    """Test cases for the GitAI core functionality"""

    @pytest.fixture
    def git_repo(self):
        """Create a temporary git repository for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize git repository
            subprocess.run(['git', 'init'], cwd=repo_path, check=True)
            subprocess.run(
                ['git', 'config', 'user.email', 'test@example.com'],
                cwd=repo_path, check=True
            )
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)

            # Create initial commit
            test_file = repo_path / 'README.md'
            test_file.write_text('# Test Repository')
            subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True)

            # Change to repo directory for tests
            original_cwd = os.getcwd()
            os.chdir(repo_path)

            yield repo_path

            # Restore original directory
            os.chdir(original_cwd)

    def test_git_ai_initialization(self, git_repo):
        """Test that GitAI can be initialized"""
        git_ai = GitAI()
        assert git_ai.repo_root == str(git_repo)
        assert git_ai.ai_config_dir.endswith('/.git/ai')

    def test_init_command(self, git_repo):  # pylint: disable=unused-argument
        """Test the init command creates necessary configuration"""
        git_ai = GitAI()
        git_ai.init()

        # Check that config directory was created
        assert os.path.exists(git_ai.ai_config_dir)
        assert os.path.exists(git_ai.ai_config_file)

        # Check config content
        config = git_ai.load_config()
        assert config['version'] == '1.0'
        assert 'ai_systems' in config
        assert 'settings' in config

    def test_track_ai_system(self, git_repo):  # pylint: disable=unused-argument
        """Test tracking an AI system"""
        git_ai = GitAI()
        git_ai.init()

        git_ai.track("Test AI System")

        config = git_ai.load_config()
        assert len(config['ai_systems']) == 1
        assert 'current_session' in config

        ai_system = list(config['ai_systems'].values())[0]
        assert ai_system['name'] == "Test AI System"
        assert ai_system['active'] is True

    def test_find_git_root(self, git_repo):
        """Test finding git repository root"""
        # Create subdirectory and test from there
        subdir = git_repo / 'subdir'
        subdir.mkdir()
        os.chdir(subdir)

        git_ai = GitAI()
        assert git_ai.repo_root == str(git_repo)

    def test_git_command_execution(self, git_repo):  # pylint: disable=unused-argument
        """Test git command execution"""
        git_ai = GitAI()

        result = git_ai.run_git_command(['status', '--porcelain'])
        assert result.returncode == 0
        assert isinstance(result.stdout, str)


def test_main_help():
    """Test that main help works"""
    # This would normally require mocking sys.argv
    # For now, just test that the function exists
    assert callable(main)


if __name__ == '__main__':
    pytest.main([__file__])

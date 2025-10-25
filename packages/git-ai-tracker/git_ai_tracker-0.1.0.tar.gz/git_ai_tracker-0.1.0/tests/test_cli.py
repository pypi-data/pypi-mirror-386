"""Tests for the CLI module"""

import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest

from git_ai.cli import main, create_parser, execute_core_commands
from git_ai.core import GitAI


class TestCLI:
    """Test cases for the CLI functionality"""

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
            import os
            original_cwd = os.getcwd()
            os.chdir(repo_path)

            yield repo_path

            # Restore original directory
            os.chdir(original_cwd)

    def test_create_parser(self):
        """Test argument parser creation"""
        parser, subparsers = create_parser()
        assert parser is not None
        assert subparsers is not None

    def test_parser_init_command(self):
        """Test init command parsing"""
        parser, _ = create_parser()
        args = parser.parse_args(['init'])
        assert args.command == 'init'

    def test_parser_track_command(self):
        """Test track command parsing"""
        parser, _ = create_parser()
        args = parser.parse_args(['track', 'chatgpt'])
        assert args.command == 'track'
        assert args.ai_system == 'chatgpt'

    def test_parser_commit_command(self):
        """Test commit command parsing"""
        parser, _ = create_parser()
        args = parser.parse_args(['commit', '-m', 'Test message'])
        assert args.command == 'commit'
        assert args.message == 'Test message'

    def test_parser_commit_with_ai_metadata(self):
        """Test commit command with AI metadata"""
        parser, _ = create_parser()
        args = parser.parse_args([
            'commit', '-m', 'Test message',
            '--ai-prompt', 'Generate a test',
            '--ai-model', 'gpt-4'
        ])
        assert args.command == 'commit'
        assert args.message == 'Test message'
        assert args.ai_prompt == 'Generate a test'
        assert args.ai_model == 'gpt-4'

    def test_parser_log_command(self):
        """Test log command parsing"""
        parser, _ = create_parser()
        args = parser.parse_args(['log'])
        assert args.command == 'log'

    def test_parser_log_with_options(self):
        """Test log command with options"""
        parser, _ = create_parser()
        args = parser.parse_args(['log', '--ai-only', '-n', '5'])
        assert args.command == 'log'
        assert args.ai_only is True
        assert args.max_count == 5

    def test_parser_experiment_command(self):
        """Test experiment command parsing"""
        parser, _ = create_parser()
        args = parser.parse_args(['experiment', 'test-feature'])
        assert args.command == 'experiment'
        assert args.experiment_name == 'test-feature'

    def test_parser_experiment_with_commit(self):
        """Test experiment command with from-commit"""
        parser, _ = create_parser()
        args = parser.parse_args(['experiment', 'test-feature', '--from-commit', 'abc123'])
        assert args.command == 'experiment'
        assert args.experiment_name == 'test-feature'
        assert args.from_commit == 'abc123'

    @patch('git_ai.core.GitAI')
    def test_execute_core_commands_init(self, mock_git_ai_class):
        """Test execution of init command"""
        mock_git_ai = Mock()
        
        parser, _ = create_parser()
        args = parser.parse_args(['init'])
        
        result = execute_core_commands(mock_git_ai, args)
        assert result is True
        mock_git_ai.init.assert_called_once()

    @patch('git_ai.core.GitAI')
    def test_execute_core_commands_track(self, mock_git_ai_class):
        """Test execution of track command"""
        mock_git_ai = Mock()
        
        parser, _ = create_parser()
        args = parser.parse_args(['track', 'chatgpt'])
        
        result = execute_core_commands(mock_git_ai, args)
        assert result is True
        mock_git_ai.track.assert_called_once_with('chatgpt')

    @patch('git_ai.core.GitAI')
    def test_execute_core_commands_commit(self, mock_git_ai_class):
        """Test execution of commit command"""
        mock_git_ai = Mock()
        
        parser, _ = create_parser()
        args = parser.parse_args(['commit', '-m', 'Test message'])
        
        result = execute_core_commands(mock_git_ai, args)
        assert result is True
        mock_git_ai.commit.assert_called_once_with('Test message', None, None, None)

    @patch('git_ai.core.GitAI')
    def test_execute_core_commands_experiment(self, mock_git_ai_class):
        """Test execution of experiment command"""
        mock_git_ai = Mock()
        
        parser, _ = create_parser()
        args = parser.parse_args(['experiment', 'test-feature'])
        
        result = execute_core_commands(mock_git_ai, args)
        assert result is True
        mock_git_ai.create_experiment.assert_called_once_with('test-feature', None)

    @patch('git_ai.core.GitAI')
    def test_execute_core_commands_invalid(self, mock_git_ai_class):
        """Test execution with invalid command"""
        mock_git_ai = Mock()
        
        # Create args with invalid command
        args = Mock()
        args.command = 'invalid'
        
        result = execute_core_commands(mock_git_ai, args)
        assert result is False

    def test_main_functionality_exists(self):
        """Test that main function exists and can be imported"""
        from git_ai.cli import main
        assert main is not None

    @patch('git_ai.core.GitAI')
    @patch('sys.argv', ['git-ai', '--help'])
    def test_main_help(self, mock_git_ai_class):
        """Test main function with help"""
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):
                try:
                    main()
                except SystemExit:
                    pass

    @patch('git_ai.core.GitAI')
    @patch('sys.argv', ['git-ai', 'invalid-command'])
    def test_main_invalid_command(self, mock_git_ai_class):
        """Test main function with invalid command"""
        mock_git_ai = Mock()
        mock_git_ai_class.return_value = mock_git_ai
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):
                main()
                mock_exit.assert_called_with(2)  # argparse uses exit code 2 for invalid args
"""Tests for the remote module"""

import os
from unittest.mock import Mock, patch
import pytest

from git_ai.remote import RemoteSync


class TestRemoteSync:
    """Test cases for the RemoteSync functionality"""

    def test_remote_sync_init(self, mock_git_ai):
        """Test remote sync initialization"""
        sync = RemoteSync(mock_git_ai)
        assert sync is not None
        assert sync.git_ai == mock_git_ai

    @patch('subprocess.run')
    def test_setup_remote(self, mock_run, mock_git_ai):
        """Test remote setup"""
        sync = RemoteSync(mock_git_ai)
        
        # Mock successful git operations
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        
        # Setup remote
        sync.setup_remote_sync('origin')
        
        assert mock_run.called

    @patch('builtins.print')
    def test_show_remote_status(self, mock_print, mock_git_ai):
        """Test remote status display"""
        sync = RemoteSync(mock_git_ai)
        
        # Mock the GitAI run_git_command method
        mock_git_ai.run_git_command = Mock()
        mock_result = Mock()
        mock_result.stdout = "refs/notes/ai"
        mock_git_ai.run_git_command.return_value = mock_result
        
        # Show remote status (returns None but prints output)
        result = sync.show_remote_status('origin')
        
        # Should have called print
        assert mock_print.called
        # Method returns None
        assert result is None
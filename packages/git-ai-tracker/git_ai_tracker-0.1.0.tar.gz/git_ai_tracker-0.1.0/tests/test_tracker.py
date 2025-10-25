"""Tests for the tracker module"""

import os
from unittest.mock import Mock, patch
import pytest

from git_ai.tracker import AIChangeTracker


class TestAIChangeTracker:
    """Test cases for the AIChangeTracker functionality"""

    def test_tracker_init(self, mock_git_ai):
        """Test tracker initialization"""
        tracker = AIChangeTracker(mock_git_ai)
        assert tracker is not None
        assert tracker.git_ai == mock_git_ai

    def test_get_ai_status(self, mock_git_ai):
        """Test getting AI status"""
        tracker = AIChangeTracker(mock_git_ai)
        
        # Get AI status - should not raise exception
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "main\n"
            
            status = tracker.get_ai_status()
            assert isinstance(status, dict)

    def test_create_ai_commit_without_session(self, mock_git_ai):
        """Test AI commit creation without active session"""
        tracker = AIChangeTracker(mock_git_ai)
        
        # Mock the GitAI config loading to return empty config
        mock_git_ai.load_config = Mock(return_value={})
        
        # This should raise ValueError about no active session
        try:
            tracker.create_ai_commit('test message', 'test prompt', 'gpt-4')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No active AI session" in str(e)

    @patch('subprocess.run')
    def test_merge_ai_branch(self, mock_run, mock_git_ai):
        """Test AI branch merging"""
        tracker = AIChangeTracker(mock_git_ai)
        
        # Mock successful git operations
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        
        # Merge AI branch with target branch
        tracker.merge_ai_branch('ai/test-feature', 'main')
        
        # Should call git merge
        assert mock_run.called

    def test_get_ai_commit_metadata(self, mock_git_ai):
        """Test getting AI commit metadata"""
        tracker = AIChangeTracker(mock_git_ai)
        
        # Mock git notes show
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"ai_system": "test-ai"}'
            
            metadata = tracker.get_ai_commit_metadata('abc123')
            # Should return metadata or None
            assert metadata is None or isinstance(metadata, dict)
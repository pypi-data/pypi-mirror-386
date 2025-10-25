"""Tests for the visualizer module"""

import os
from unittest.mock import Mock, patch
import pytest

from git_ai.visualizer import TreeVisualizer


class TestTreeVisualizer:
    """Test cases for the TreeVisualizer functionality"""

    def test_visualizer_init(self, mock_git_ai):
        """Test visualizer initialization"""
        visualizer = TreeVisualizer(mock_git_ai)
        assert visualizer is not None
        assert visualizer.git_ai == mock_git_ai

    @patch('subprocess.run')
    def test_show_ai_tree(self, mock_run, mock_git_ai):
        """Test AI tree visualization"""
        visualizer = TreeVisualizer(mock_git_ai)
        
        # Mock git log output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "abc123 Initial commit\n"
        
        # Show tree - should not raise exception
        result = visualizer.show_ai_tree()
        
        assert isinstance(result, str)
        assert mock_run.called

    def test_show_ai_statistics_no_data(self, mock_git_ai):
        """Test AI statistics display with no data"""
        visualizer = TreeVisualizer(mock_git_ai)
        
        # Mock the GitAI config loading to return empty config
        mock_git_ai.load_config = Mock(return_value={})
        
        # Show stats - should return string for no data
        result = visualizer.show_ai_statistics()
        
        assert isinstance(result, str)
        assert "No AI tracking data available" in result
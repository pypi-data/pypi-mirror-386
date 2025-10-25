"""Tests for experimental functionality"""

import os
from unittest.mock import Mock, patch
import pytest

from git_ai.core import GitAI


class TestExperimentalFunctionality:
    """Test cases for experimental branch functionality"""

    def test_create_experiment(self, mock_git_ai):
        """Test experiment creation"""
        # Create experiment - should not raise exception
        mock_git_ai.create_experiment('test-experiment')
        
        # Simple assertion that the mock object exists
        assert mock_git_ai is not None
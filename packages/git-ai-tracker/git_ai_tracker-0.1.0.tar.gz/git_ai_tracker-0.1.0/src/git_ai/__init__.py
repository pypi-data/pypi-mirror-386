"""
git-ai: AI Change Tracking for Git

A Git extension that tracks and visualizes changes made by AI systems
as sub-nodes and sub-branches in your commit tree, with full team collaboration support.
"""

__version__ = "0.1.0"
__author__ = "João Galego"
__email__ = "jgalego1990@gmail.com"

from .core import GitAI
from .remote import RemoteSync
from .tracker import AIChangeTracker
from .visualizer import TreeVisualizer

__all__ = [
    "GitAI",
    "AIChangeTracker",
    "TreeVisualizer",
    "RemoteSync",
]

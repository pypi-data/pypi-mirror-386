#!/usr/bin/env python3
"""
Core GitAI class and functionality

This module contains the main GitAI class that orchestrates all git-ai functionality.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from .remote import RemoteSync
from .tracker import AIChangeTracker
from .visualizer import TreeVisualizer


class GitAI:
    """Main class for the git-ai extension"""

    def __init__(self):
        self.repo_root = self._find_git_root()
        self.ai_config_dir = os.path.join(self.repo_root, ".git", "ai")
        self.ai_config_file = os.path.join(self.ai_config_dir, "config.json")
        self.current_ai_session = None

        # Initialize tracking and visualization modules
        self.tracker = AIChangeTracker(self)
        self.visualizer = TreeVisualizer(self)
        self.remote = RemoteSync(self)

    def _find_git_root(self) -> str:
        """Find the root of the git repository"""
        current_dir = os.getcwd()
        while current_dir != "/":
            if os.path.exists(os.path.join(current_dir, ".git")):
                return current_dir
            current_dir = os.path.dirname(current_dir)
        raise ValueError("Not in a git repository")

    def run_git_command(
        self, command: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute a git command and return the result"""
        return self._run_git_command(command, capture_output)

    def _run_git_command(
        self, command: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute a git command and return the result"""
        try:
            result = subprocess.run(
                ["git"] + command,
                capture_output=capture_output,
                text=True,
                cwd=self.repo_root,
                check=False,
            )
            return result
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Error running git command: {e}")
            sys.exit(1)

    def _ensure_ai_config_dir(self):
        """Ensure the AI configuration directory exists"""
        os.makedirs(self.ai_config_dir, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load AI tracking configuration"""
        return self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load AI tracking configuration"""
        if not os.path.exists(self.ai_config_file):
            return {}

        with open(self.ai_config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config: Dict[str, Any]):
        """Save AI tracking configuration"""
        return self._save_config(config)

    def _save_config(self, config: Dict[str, Any]):
        """Save AI tracking configuration"""
        self._ensure_ai_config_dir()
        with open(self.ai_config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def get_ai_commit_metadata(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve AI metadata for a commit using git notes"""
        try:
            notes_result = self._run_git_command(
                ["notes", "--ref=ai", "show", commit_hash]
            )
            if notes_result.returncode == 0:
                return json.loads(notes_result.stdout)
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def init(self):
        """Initialize AI tracking for this repository"""
        print("Initializing git-ai tracking...")

        self._ensure_ai_config_dir()

        # Create initial configuration
        config = {
            "version": "1.0",
            "initialized": datetime.now().isoformat(),
            "ai_systems": {},
            "settings": {
                "auto_create_ai_branches": True,
                "ai_branch_prefix": "ai/",
                "require_ai_metadata": True,
            },
        }

        self._save_config(config)

        # Initialize git notes for AI metadata
        self._run_git_command(["config", "notes.rewriteRef", "refs/notes/ai"])

        print("✓ git-ai initialized successfully")
        print("  - AI configuration directory created")
        print("  - Git notes configured for AI metadata")
        print("  - Default settings applied")
        print("\nNext steps:")
        print("  1. Start tracking with: git ai track <ai-system-name>")
        print("  2. Make AI changes and commit with: git ai commit")

    def track(self, ai_system: str):
        """Start tracking changes for a specific AI system"""
        config = self._load_config()

        if not config:
            print("Error: git-ai not initialized. Run 'git ai init' first.")
            return

        # Create AI system entry
        if "ai_systems" not in config:
            config["ai_systems"] = {}

        ai_id = f"ai_{len(config['ai_systems']) + 1}"
        config["ai_systems"][ai_id] = {
            "name": ai_system,
            "created": datetime.now().isoformat(),
            "active": True,
            "branch_prefix": f"ai/{ai_system.lower().replace(' ', '-')}",
        }

        # Set current AI session
        config["current_session"] = ai_id
        self._save_config(config)

        print(f"✓ Now tracking AI system: {ai_system}")
        print(f"  - AI ID: {ai_id}")
        print(f"  - Branch prefix: {config['ai_systems'][ai_id]['branch_prefix']}")
        print("  - Use 'git ai commit' to commit AI changes")

    def create_experiment(self, experiment_name: str, from_commit: Optional[str] = None):
        """Create a new experimental AI branch"""
        config = self._load_config()

        if not config or "current_session" not in config:
            print("Error: No active AI session. Run 'git ai track <ai-system>' first.")
            return

        current_session = config["current_session"]
        ai_system = config["ai_systems"][current_session]

        # Get current branch
        current_branch_result = self._run_git_command(["branch", "--show-current"])
        current_branch = current_branch_result.stdout.strip()

        # Determine base branch (strip AI prefix if we're on an AI branch)
        if current_branch.startswith(ai_system["branch_prefix"]):
            base_branch = current_branch.replace(f"{ai_system['branch_prefix']}/", "").split("/")[0]
        else:
            base_branch = current_branch

        # Create experiment branch name - use underscore instead of nested path
        experiment_branch = (
            f"{ai_system['branch_prefix']}/{base_branch}_experiment_{experiment_name}"
        )

        # Determine starting point - for true branching, start from a common base
        if from_commit:
            start_point = from_commit
        else:
            # If we're on an AI branch, start the experiment from the original base branch
            # to create proper branching topology
            if current_branch.startswith(ai_system["branch_prefix"]):
                start_point = base_branch  # Start from the human branch
            else:
                start_point = current_branch

        # Create and switch to experiment branch
        create_result = self._run_git_command(["checkout", "-b", experiment_branch, start_point])

        if create_result.returncode == 0:
            print(f"✓ Created experimental branch: {experiment_branch}")
            print(f"  - Based on: {start_point}")
            print(f"  - AI System: {ai_system['name']}")
            print("  - Use 'git ai commit' to make experimental changes")

            # Update config to track this experiment
            if "experiments" not in config["ai_systems"][current_session]:
                config["ai_systems"][current_session]["experiments"] = {}

            config["ai_systems"][current_session]["experiments"][experiment_name] = {
                "branch": experiment_branch,
                "created": datetime.now().isoformat(),
                "base_commit": start_point,
                "active": True
            }

            self._save_config(config)
        else:
            print(f"Error creating experiment branch: {create_result.stderr}")

    def commit(
        self,
        message: str,
        ai_prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        files: Optional[List[str]] = None,
    ):
        """Create a commit with AI metadata"""
        if not message:
            print("Error: Commit message is required")
            return

        commit_hash = self.tracker.create_ai_commit(message, ai_prompt, ai_model, files)
        if commit_hash:
            print("Commit created successfully!")
            if ai_prompt:
                print(f"  - AI Prompt: {ai_prompt}")
            if ai_model:
                print(f"  - AI Model: {ai_model}")

    def show_log(self, ai_only: bool = False, max_count: Optional[int] = None):
        """Show commit history with AI annotations"""
        # Filter AI commits if requested
        if ai_only:
            ai_commits = self.tracker.list_ai_commits(limit=max_count)
            ai_commits = [commit for commit in ai_commits if commit.get('ai_metadata')]
        else:
            ai_commits = self.tracker.list_ai_commits(limit=max_count)

        if not ai_commits:
            print("No AI commits found.")
            return

        print("AI Commit History:")
        print("=" * 50)

        for commit in ai_commits:
            print(f"\nCommit: {commit['hash'][:8]}")
            print(f"Date: {commit['date']}")
            print(f"Author: {commit['author']}")
            print(f"Message: {commit['subject']}")

            ai_meta = commit["ai_metadata"]
            print(f"AI System: {ai_meta.get('ai_system', 'Unknown')}")

            if "ai_model" in ai_meta:
                print(f"AI Model: {ai_meta['ai_model']}")

            if "ai_prompt" in ai_meta:
                print(f"AI Prompt: {ai_meta['ai_prompt']}")

            if "ai_branch" in ai_meta:
                print(f"AI Branch: {ai_meta['ai_branch']}")

    def show_tree(
        self,
        format_type: str = "unicode",
        max_commits: int = 20,
        show_ai_only: bool = False,
    ):
        """Show commit tree with AI annotations"""
        tree_output = self.visualizer.show_ai_tree(
            format_type=format_type, max_commits=max_commits, show_ai_only=show_ai_only
        )
        print(tree_output)

    def show_status(self):
        """Show AI tracking status"""
        status = self.tracker.get_ai_status()

        if not status["initialized"]:
            print("git-ai is not initialized in this repository.")
            print("Run 'git ai init' to get started.")
            return

        print("AI Tracking Status:")
        print("=" * 30)
        print(f"Current Branch: {status['current_branch']}")

        if status["is_ai_branch"]:
            if status.get("is_experiment_branch"):
                print("🧪 Currently on an experimental AI branch")
            else:
                print("📍 Currently on an AI branch")
        else:
            print("📍 Currently on a human branch")

        if status["active_ai_system"]:
            ai_sys = status["active_ai_system"]
            print(f"\nActive AI System: {ai_sys['name']}")
            print(f"Session ID: {status['active_session']}")
            print(f"Branch Prefix: {ai_sys['branch_prefix']}")
        else:
            print("\nNo active AI session")
            print("Use 'git ai track <ai-system>' to start tracking")

        print(f"\nAI Systems: {status['ai_systems_count']}")
        print(f"AI Branches: {len(status['ai_branches'])}")

        if status["recent_ai_commits"]:
            print("\nRecent AI Commits:")
            for commit in status["recent_ai_commits"][:3]:
                ai_sys = commit["ai_metadata"].get("ai_system", "Unknown")
                print(f"  {commit['hash'][:8]} - {commit['subject']} [{ai_sys}]")

    def show_config(
        self,
        list_all: bool = False,
        set_key: Optional[str] = None,
        set_value: Optional[str] = None,
    ):
        """Configure AI tracking settings"""
        config = self._load_config()

        if not config:
            print("git-ai not initialized. Run 'git ai init' first.")
            return

        if list_all:
            print("AI Configuration:")
            print("=" * 30)
            print(json.dumps(config, indent=2))
        elif set_key and set_value:
            # Simple key setting (can be expanded)
            if set_key in [
                "ai_branch_prefix",
                "auto_create_ai_branches",
                "require_ai_metadata",
            ]:
                config["settings"][set_key] = set_value
                self._save_config(config)
                print(f"✓ Set {set_key} = {set_value}")
            else:
                print(f"Unknown configuration key: {set_key}")
        else:
            # Show key settings
            settings = config.get("settings", {})
            print("Key AI Settings:")
            print("=" * 30)
            for key, value in settings.items():
                print(f"{key}: {value}")

    def merge_ai_branch(
        self,
        ai_branch: str,
        target_branch: Optional[str] = None,
        strategy: str = "merge",
    ):
        """Merge an AI branch"""
        if not target_branch:
            # Get current branch as target
            current_branch_result = self._run_git_command(["branch", "--show-current"])
            target_branch = current_branch_result.stdout.strip()

        if not target_branch:
            print("Error: Could not determine target branch")
            return

        success = self.tracker.merge_ai_branch(ai_branch, target_branch, strategy)

        if success:
            print("AI branch merged successfully!")
            print("You may want to delete the AI branch if no longer needed:")
            print(f"  git branch -d {ai_branch}")
        else:
            print("Merge failed. Please resolve conflicts and try again.")

    def show_branches(self, format_type: str = "unicode"):
        """Show AI branches structure"""
        branches_output = self.visualizer.show_ai_branches(format_type)
        print(branches_output)

    def show_statistics(self):
        """Show AI contribution statistics"""
        stats_output = self.visualizer.show_ai_statistics()
        print(stats_output)

    def setup_remote(self, remote_name: str = "origin"):
        """Setup remote synchronization for AI data"""
        self.remote.setup_remote_sync(remote_name)

    def push_ai_data(self, remote_name: str = "origin", force: bool = False):
        """Push AI data to remote"""
        self.remote.push_ai_data(remote_name, force)

    def pull_ai_data(self, remote_name: str = "origin"):
        """Pull AI data from remote"""
        self.remote.pull_ai_data(remote_name)

    def sync_ai_data(self, remote_name: str = "origin"):
        """Sync AI data bidirectionally with remote"""
        self.remote.sync_ai_data(remote_name)

    def show_remote_status(self, remote_name: str = "origin"):
        """Show remote synchronization status"""
        self.remote.show_remote_status(remote_name)

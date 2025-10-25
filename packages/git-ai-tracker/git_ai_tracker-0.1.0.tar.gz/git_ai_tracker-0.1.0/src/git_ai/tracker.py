#!/usr/bin/env python3
"""
AI Change Tracking Module for git-ai

This module handles the core functionality for tracking AI-made changes,
including metadata storage, branch management, and integration with git workflow.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AIMetadataParams:
    """Parameters for creating AI metadata"""
    ai_system: Dict[str, Any]
    current_session: str
    current_branch: str
    ai_branch_name: str
    ai_prompt: Optional[str] = None
    ai_model: Optional[str] = None


class AIChangeTracker:
    """Handles tracking and management of AI-made changes"""

    def __init__(self, git_ai_instance):
        self.git_ai = git_ai_instance
        self.repo_root = git_ai_instance.repo_root
        self.ai_config_dir = git_ai_instance.ai_config_dir

    def _prepare_ai_commit_environment(self, ai_system: Dict[str, Any], files: Optional[List[str]]):
        """Prepare the environment for creating an AI commit"""
        # Get current branch
        current_branch_result = self.git_ai.run_git_command(["branch", "--show-current"])
        current_branch = current_branch_result.stdout.strip()

        # Determine the base branch and AI branch name
        if current_branch.startswith(ai_system['branch_prefix']):
            # We're already on an AI branch (including experimental branches)
            ai_branch_name = current_branch

            # Extract the original branch from the AI branch name
            if "_experiment_" in current_branch:
                # For experimental branches: ai/copilot/main_experiment_feature1 -> main
                branch_part = current_branch.replace(f"{ai_system['branch_prefix']}/", "")
                base_branch = branch_part.split("_experiment_")[0]
            else:
                # For regular AI branches: ai/copilot/main -> main
                base_branch = current_branch.replace(f"{ai_system['branch_prefix']}/", "")
        else:
            # We're on a human branch, create/switch to AI branch
            base_branch = current_branch
            ai_branch_name = f"{ai_system['branch_prefix']}/{current_branch}"
            self._ensure_ai_branch(ai_branch_name, current_branch)
            # Switch to AI branch
            self.git_ai.run_git_command(["checkout", ai_branch_name])

        # Add files if specified, otherwise add all changed files
        if files:
            for file in files:
                self.git_ai.run_git_command(["add", file])
        else:
            self.git_ai.run_git_command(["add", "."])

        return base_branch, ai_branch_name

    def _create_ai_metadata(self, params: AIMetadataParams) -> Dict[str, Any]:
        """Create AI metadata dictionary"""
        ai_metadata = {
            "ai_system": params.ai_system["name"],
            "ai_session_id": params.current_session,
            "timestamp": datetime.now().isoformat(),
            "commit_type": "ai_generated",
            "parent_branch": params.current_branch,
            "ai_branch": params.ai_branch_name,
        }

        if params.ai_prompt:
            ai_metadata["ai_prompt"] = params.ai_prompt
        if params.ai_model:
            ai_metadata["ai_model"] = params.ai_model

        return ai_metadata

    def create_ai_commit(
        self,
        message: str,
        ai_prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Create a commit with AI metadata"""
        config = self.git_ai.load_config()

        if "current_session" not in config:
            raise ValueError(
                "No active AI session. Use 'git ai track <ai-system>' first."
            )

        current_session = config["current_session"]
        ai_system = config["ai_systems"][current_session]

        # Prepare commit environment
        current_branch, ai_branch_name = self._prepare_ai_commit_environment(ai_system, files)

        # Create commit
        commit_result = self.git_ai.run_git_command(["commit", "-m", message])

        if commit_result.returncode != 0:
            print(f"Error creating commit: {commit_result.stderr}")
            return None

        # Get the commit hash
        commit_hash_result = self.git_ai.run_git_command(["rev-parse", "HEAD"])
        commit_hash = commit_hash_result.stdout.strip()

        # Create and store AI metadata
        metadata_params = AIMetadataParams(
            ai_system=ai_system,
            current_session=current_session,
            current_branch=current_branch,
            ai_branch_name=ai_branch_name,
            ai_prompt=ai_prompt,
            ai_model=ai_model
        )
        ai_metadata = self._create_ai_metadata(metadata_params)
        self._add_ai_notes(commit_hash, ai_metadata)

        # Update tracking statistics
        self._update_ai_stats(current_session, commit_hash)

        print(f"✓ AI commit created: {commit_hash[:8]}")
        print(f"  - Branch: {ai_branch_name}")
        print(f"  - AI System: {ai_system['name']}")
        print(f"  - Message: {message}")

        return commit_hash

    def _ensure_ai_branch(self, ai_branch_name: str, parent_branch: str):
        """Ensure an AI branch exists, create if necessary"""
        # Check if branch exists
        branch_check = self.git_ai.run_git_command(
            ["branch", "--list", ai_branch_name]
        )

        if not branch_check.stdout.strip():
            # Branch doesn't exist, create it from the parent branch (not current HEAD)
            print(f"Creating AI branch: {ai_branch_name}")
            self.git_ai.run_git_command(
                ["checkout", "-b", ai_branch_name, parent_branch]
            )
        else:
            print(f"Using existing AI branch: {ai_branch_name}")

    def _add_ai_notes(self, commit_hash: str, metadata: Dict[str, Any]):
        """Add AI metadata as git notes"""
        metadata_json = json.dumps(metadata, indent=2)

        # Use git notes to store AI metadata
        with subprocess.Popen(
            ["git", "notes", "--ref=ai", "add", "-m", metadata_json, commit_hash],
            cwd=self.repo_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as notes_process:
            _, stderr = notes_process.communicate()

            if notes_process.returncode != 0:
                print(f"Warning: Could not add AI notes: {stderr}")

    def _update_ai_stats(self, session_id: str, commit_hash: str):
        """Update AI session statistics"""
        config = self.git_ai.load_config()

        if "stats" not in config["ai_systems"][session_id]:
            config["ai_systems"][session_id]["stats"] = {
                "total_commits": 0,
                "commits": [],
            }

        config["ai_systems"][session_id]["stats"]["total_commits"] += 1
        config["ai_systems"][session_id]["stats"]["commits"].append(
            {"hash": commit_hash, "timestamp": datetime.now().isoformat()}
        )

        self.git_ai.save_config(config)

    def get_ai_commit_metadata(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve AI metadata for a commit"""
        return self.git_ai.get_ai_commit_metadata(commit_hash)

    def list_ai_commits(
        self, branch: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all AI commits with metadata"""
        # Build git log command
        log_cmd = ["log", "--format=%H|%s|%an|%ad", "--date=iso"]

        if branch:
            log_cmd.append(branch)

        if limit:
            log_cmd.extend(["-n", str(limit)])

        log_result = self.git_ai.run_git_command(log_cmd)

        if log_result.returncode != 0:
            return []

        ai_commits = []

        for line in log_result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < 4:
                continue

            commit_hash, subject, author, date = parts

            # Check if this commit has AI metadata
            ai_metadata = self.get_ai_commit_metadata(commit_hash)

            if ai_metadata:
                commit_info = {
                    "hash": commit_hash,
                    "subject": subject,
                    "author": author,
                    "date": date,
                    "ai_metadata": ai_metadata,
                }
                ai_commits.append(commit_info)

        return ai_commits

    def merge_ai_branch(
        self, ai_branch: str, target_branch: str, strategy: str = "merge"
    ) -> bool:
        """Merge an AI branch back to the target branch"""
        print(f"Merging AI branch '{ai_branch}' into '{target_branch}'...")

        # Verify that the AI branch exists
        branch_check = self.git_ai.run_git_command(["branch", "--list", ai_branch])
        if not branch_check.stdout.strip():
            print(f"Error: AI branch '{ai_branch}' does not exist")
            return False

        # Switch to target branch
        checkout_result = self.git_ai.run_git_command(["checkout", target_branch])
        if checkout_result.returncode != 0:
            print(
                f"Error: Could not checkout target branch '{target_branch}': "
                f"{checkout_result.stderr}"
            )
            return False

        merge_result = None
        if strategy == "merge":
            # Force a merge commit (no fast-forward) to show proper branching in graph
            merge_message = f"Merge AI changes from {ai_branch}"
            merge_result = self.git_ai.run_git_command(
                ["merge", "--no-ff", ai_branch, "-m", merge_message]
            )
        elif strategy == "squash":
            # Squash merge
            merge_result = self.git_ai.run_git_command(
                ["merge", "--squash", ai_branch]
            )
            if merge_result.returncode == 0:
                # Create squash commit
                squash_message = f"AI changes from {ai_branch} (squashed)"
                commit_result = self.git_ai.run_git_command(
                    ["commit", "-m", squash_message]
                )
                merge_result = commit_result

        if strategy not in ["merge", "squash"]:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        if merge_result and merge_result.returncode == 0:
            print(f"✓ Successfully merged {ai_branch} into {target_branch}")

            # Add merge metadata
            commit_hash_result = self.git_ai.run_git_command(["rev-parse", "HEAD"])
            commit_hash = commit_hash_result.stdout.strip()

            merge_metadata = {
                "merge_type": "ai_to_human",
                "ai_branch": ai_branch,
                "target_branch": target_branch,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat(),
            }

            self._add_ai_notes(commit_hash, merge_metadata)
            return True

        if merge_result:
            print(f"✗ Merge failed: {merge_result.stderr}")
            print("Please resolve conflicts manually and complete the merge.")
        else:
            print("✗ Merge failed: Unknown strategy")
        return False

    def get_ai_status(self) -> Dict[str, Any]:
        """Get current AI tracking status"""
        config = self.git_ai.load_config()

        if not config:
            return {"initialized": False}

        # Get current branch
        current_branch_result = self.git_ai.run_git_command(
            ["branch", "--show-current"]
        )
        current_branch = current_branch_result.stdout.strip()

        # Check if current branch is an AI branch
        is_ai_branch = current_branch.startswith("ai/")

        # Get active AI session
        active_session = config.get("current_session")
        active_ai_system = None

        if active_session and active_session in config.get("ai_systems", {}):
            active_ai_system = config["ai_systems"][active_session]

        # Count AI branches
        branches_result = self.git_ai.run_git_command(["branch", "-a"])
        ai_branches = [
            b.strip()
            for b in branches_result.stdout.split("\n")
            if b.strip().startswith("ai/") or "ai/" in b
        ]

        # Get recent AI commits
        recent_ai_commits = self.list_ai_commits(limit=5)

        return {
            "initialized": True,
            "current_branch": current_branch,
            "is_ai_branch": is_ai_branch,
            "is_experiment_branch": "_experiment_" in current_branch,
            "active_session": active_session,
            "active_ai_system": active_ai_system,
            "ai_branches": ai_branches,
            "ai_systems_count": len(config.get("ai_systems", {})),
            "recent_ai_commits": recent_ai_commits,
        }

#!/usr/bin/env python3
"""
Remote Synchronization Module for git-ai

This module handles synchronization of AI metadata and branches with remote repositories,
enabling team collaboration on AI-tracked projects.
"""

import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional


class RemoteSync:
    """Handles synchronization of AI data with remote repositories"""

    def __init__(self, git_ai_instance):
        self.git_ai = git_ai_instance
        self.repo_root = git_ai_instance.repo_root

    def setup_remote_sync(self, remote_name: str = "origin"):
        """Configure the repository for AI metadata synchronization with remote"""
        print(f"Setting up AI metadata synchronization with remote '{remote_name}'...")

        # Configure git to push/pull AI notes
        self.git_ai.run_git_command(
            ["config", f"remote.{remote_name}.push", "+refs/notes/ai:refs/notes/ai"]
        )

        # Configure git to fetch AI notes
        self.git_ai.run_git_command(
            [
                "config",
                f"remote.{remote_name}.fetch",
                f"+refs/notes/ai:refs/remotes/{remote_name}/notes/ai",
            ]
        )

        # Add AI branches to default push configuration
        config = self.git_ai.load_config()
        if config and "settings" in config:
            ai_branch_prefix = config["settings"].get("ai_branch_prefix", "ai/")

            # Configure push for AI branches
            self.git_ai.run_git_command(
                [
                    "config",
                    "--add",
                    f"remote.{remote_name}.push",
                    f"+refs/heads/{ai_branch_prefix}*:refs/heads/{ai_branch_prefix}*",
                ]
            )

        print("✓ Remote synchronization configured")
        print("  - AI notes will be synchronized")
        print("  - AI branches will be pushed/pulled")
        print("  - Use 'git ai push' and 'git ai pull' to sync AI data")

    def push_ai_data(self, remote_name: str = "origin", force: bool = False):
        """Push AI metadata and branches to remote"""
        print(f"Pushing AI data to remote '{remote_name}'...")

        # Push AI notes
        notes_cmd = ["push", remote_name, "refs/notes/ai"]
        if force:
            notes_cmd.insert(1, "--force")

        notes_result = self.git_ai.run_git_command(notes_cmd)

        if notes_result.returncode == 0:
            print("✓ AI notes pushed successfully")
        else:
            print(f"⚠ AI notes push failed: {notes_result.stderr}")

        # Push AI branches
        ai_branches = self._get_local_ai_branches()

        for branch in ai_branches:
            branch_cmd = ["push", remote_name, f"{branch}:{branch}"]
            if force:
                branch_cmd.insert(1, "--force")

            branch_result = self.git_ai.run_git_command(branch_cmd)

            if branch_result.returncode == 0:
                print(f"✓ AI branch '{branch}' pushed successfully")
            else:
                print(f"⚠ AI branch '{branch}' push failed: {branch_result.stderr}")

        # Push AI configuration as a special file
        self._push_ai_config(remote_name, force)

        print("AI data push completed!")

    def pull_ai_data(self, remote_name: str = "origin"):
        """Pull AI metadata and branches from remote"""
        print(f"Pulling AI data from remote '{remote_name}'...")

        # Fetch all references including AI notes
        fetch_result = self.git_ai.run_git_command(["fetch", remote_name])

        if fetch_result.returncode != 0:
            print(f"Error fetching from remote: {fetch_result.stderr}")
            return

        # Pull AI notes
        try:
            notes_result = self.git_ai.run_git_command(
                ["notes", "--ref=ai", "merge", f"refs/remotes/{remote_name}/notes/ai"]
            )

            if notes_result.returncode == 0:
                print("✓ AI notes merged successfully")
            else:
                print("ℹ No remote AI notes to merge")
        except (subprocess.SubprocessError, OSError):
            print("ℹ No remote AI notes to merge")

        # Pull remote AI branches
        remote_ai_branches = self._get_remote_ai_branches(remote_name)

        for remote_branch in remote_ai_branches:
            local_branch = remote_branch.replace(f"remotes/{remote_name}/", "")

            # Check if local branch exists
            local_check = self.git_ai.run_git_command(
                ["branch", "--list", local_branch]
            )

            if local_check.stdout.strip():
                # Branch exists locally, merge changes
                current_branch = self._get_current_branch()

                self.git_ai.run_git_command(["checkout", local_branch])
                merge_result = self.git_ai.run_git_command(["merge", remote_branch])

                if merge_result.returncode == 0:
                    print(f"✓ AI branch '{local_branch}' updated")
                else:
                    print(f"⚠ Merge conflict in AI branch '{local_branch}'")

                # Return to original branch
                if current_branch:
                    self.git_ai.run_git_command(["checkout", current_branch])
            else:
                # Create new local branch from remote
                create_result = self.git_ai.run_git_command(
                    ["checkout", "-b", local_branch, remote_branch]
                )

                if create_result.returncode == 0:
                    print(f"✓ New AI branch '{local_branch}' created from remote")

        # Pull AI configuration
        self._pull_ai_config(remote_name)

        print("AI data pull completed!")

    def sync_ai_data(self, remote_name: str = "origin"):
        """Bidirectional sync: pull then push AI data"""
        print("Performing bidirectional AI data sync...")

        # First pull to get latest changes
        self.pull_ai_data(remote_name)

        # Then push our changes
        self.push_ai_data(remote_name)

        print("✓ AI data synchronization completed!")

    def clone_with_ai_data(self, repo_url: str, directory: Optional[str] = None):
        """Clone a repository and set up AI data synchronization"""
        print(f"Cloning repository with AI data: {repo_url}")

        # Standard git clone
        clone_cmd = ["git", "clone", repo_url]
        if directory:
            clone_cmd.append(directory)

        clone_result = subprocess.run(clone_cmd, capture_output=True, text=True, check=False)

        if clone_result.returncode != 0:
            print(f"Error cloning repository: {clone_result.stderr}")
            return False

        # Change to the cloned directory
        if directory:
            target_dir = directory
        else:
            target_dir = repo_url.split("/")[-1].replace(".git", "")

        original_cwd = os.getcwd()
        os.chdir(target_dir)

        try:
            # Initialize git-ai and pull AI data
            temp_git_ai = type(self.git_ai)()  # Create new instance in cloned repo

            # Setup remote sync
            temp_sync = RemoteSync(temp_git_ai)
            temp_sync.setup_remote_sync()

            # Pull AI data
            temp_sync.pull_ai_data()

            print(f"✓ Repository cloned with AI data in '{target_dir}'")
            return True

        finally:
            os.chdir(original_cwd)

    def _get_local_ai_branches(self) -> List[str]:
        """Get list of local AI branches"""
        branches_result = self.git_ai.run_git_command(["branch"])

        ai_branches = []
        for line in branches_result.stdout.strip().split("\n"):
            branch = line.strip().replace("* ", "")
            if branch.startswith("ai/"):
                ai_branches.append(branch)

        return ai_branches

    def _get_remote_ai_branches(self, remote_name: str) -> List[str]:
        """Get list of remote AI branches"""
        branches_result = self.git_ai.run_git_command(["branch", "-r"])

        remote_ai_branches = []
        prefix = f"{remote_name}/ai/"

        for line in branches_result.stdout.strip().split("\n"):
            branch = line.strip()
            if prefix in branch:
                remote_ai_branches.append(branch)

        return remote_ai_branches

    def _get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        result = self.git_ai.run_git_command(["branch", "--show-current"])
        return result.stdout.strip() if result.returncode == 0 else None

    def _push_ai_config(self, remote_name: str, force: bool = False):
        """Push AI configuration to a special remote branch"""
        config = self.git_ai.load_config()

        if not config:
            return

        # Create a temporary commit with AI config in a special branch
        current_branch = self._get_current_branch()
        config_branch = "ai-config"

        try:
            # Create or checkout config branch
            self.git_ai.run_git_command(["checkout", "-B", config_branch])

            # Write config to a special file
            config_file = ".git-ai-config.json"
            with open(os.path.join(self.repo_root, config_file), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            # Commit the config
            self.git_ai.run_git_command(["add", config_file])
            self.git_ai.run_git_command(
                ["commit", "-m", f"AI config update: {datetime.now().isoformat()}"]
            )

            # Push config branch
            push_cmd = ["push", remote_name, f"{config_branch}:{config_branch}"]
            if force:
                push_cmd.insert(1, "--force")

            push_result = self.git_ai.run_git_command(push_cmd)

            if push_result.returncode == 0:
                print("✓ AI configuration pushed successfully")

        except (subprocess.SubprocessError, OSError, IOError) as e:
            print(f"⚠ Failed to push AI configuration: {e}")

        finally:
            # Return to original branch
            if current_branch:
                self.git_ai.run_git_command(["checkout", current_branch])

            # Clean up config file
            config_file_path = os.path.join(self.repo_root, ".git-ai-config.json")
            if os.path.exists(config_file_path):
                os.remove(config_file_path)

    def _pull_ai_config(self, remote_name: str):
        """Pull AI configuration from remote"""
        current_branch = self._get_current_branch()
        config_branch = "ai-config"

        try:
            # Check if remote config branch exists
            remote_branches = self.git_ai.run_git_command(["branch", "-r"])
            remote_config_branch = f"{remote_name}/{config_branch}"

            if remote_config_branch not in remote_branches.stdout:
                return  # No remote config to pull

            # Checkout remote config branch
            self.git_ai.run_git_command(
                ["checkout", "-B", config_branch, f"{remote_name}/{config_branch}"]
            )

            # Read remote config
            config_file_path = os.path.join(self.repo_root, ".git-ai-config.json")
            if os.path.exists(config_file_path):
                with open(config_file_path, "r", encoding="utf-8") as f:
                    remote_config = json.load(f)

                # Merge with local config
                local_config = self.git_ai.load_config()
                merged_config = self._merge_ai_configs(local_config, remote_config)

                self.git_ai.save_config(merged_config)
                print("✓ AI configuration merged from remote")

        except (subprocess.SubprocessError, OSError, IOError, json.JSONDecodeError) as e:
            print(f"⚠ Failed to pull AI configuration: {e}")

        finally:
            # Return to original branch
            if current_branch:
                self.git_ai.run_git_command(["checkout", current_branch])

    def _merge_ai_configs(
        self, local_config: Dict[str, Any], remote_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge local and remote AI configurations"""
        # Start with local config
        merged = local_config.copy()

        # Merge AI systems (add new ones, don't overwrite existing)
        if "ai_systems" in remote_config:
            if "ai_systems" not in merged:
                merged["ai_systems"] = {}

            for system_id, system_data in remote_config["ai_systems"].items():
                if system_id not in merged["ai_systems"]:
                    merged["ai_systems"][system_id] = system_data

        # Update version if remote is newer
        remote_version = remote_config.get("version", "1.0")
        local_version = merged.get("version", "1.0")

        if remote_version > local_version:
            merged["version"] = remote_version

        return merged

    def show_remote_status(self, remote_name: str = "origin"):
        """Show status of AI data synchronization with remote"""
        print(f"AI Remote Synchronization Status ({remote_name}):")
        print("=" * 50)

        # Check if remote sync is configured
        try:
            config_check = self.git_ai.run_git_command(
                ["config", f"remote.{remote_name}.push"]
            )

            if "refs/notes/ai" in config_check.stdout:
                print("✓ Remote sync configured for AI notes")
            else:
                print("✗ Remote sync not configured")
                print(f"  Run: git ai remote setup {remote_name}")
        except (subprocess.SubprocessError, OSError):
            print("✗ Remote sync not configured")

        # Check local vs remote AI branches
        local_ai_branches = self._get_local_ai_branches()
        remote_ai_branches = self._get_remote_ai_branches(remote_name)

        print(f"\nLocal AI branches: {len(local_ai_branches)}")
        for branch in local_ai_branches:
            print(f"  {branch}")

        print(f"\nRemote AI branches: {len(remote_ai_branches)}")
        for branch in remote_ai_branches:
            print(f"  {branch}")

        # Check for unpushed AI commits
        unpushed_commits = self._get_unpushed_ai_commits(remote_name)
        if unpushed_commits:
            print(f"\nUnpushed AI commits: {len(unpushed_commits)}")
            for commit in unpushed_commits[:5]:  # Show first 5
                print(f"  {commit[:8]} (on {self._get_branch_for_commit(commit)})")

        # Check AI notes status
        self._check_ai_notes_status(remote_name)

    def _get_unpushed_ai_commits(self, remote_name: str) -> List[str]:
        """Get list of local AI commits not yet pushed to remote"""
        unpushed = []

        for branch in self._get_local_ai_branches():
            try:
                # Get commits ahead of remote
                ahead_result = self.git_ai.run_git_command(
                    ["rev-list", f"{remote_name}/{branch}..{branch}"]
                )

                if ahead_result.returncode == 0:
                    ahead_commits = ahead_result.stdout.strip().split("\n")
                    unpushed.extend([c for c in ahead_commits if c])
            except (subprocess.SubprocessError, OSError):
                # Branch might not exist on remote yet
                all_commits = self.git_ai.run_git_command(["rev-list", branch])

                if all_commits.returncode == 0:
                    branch_commits = all_commits.stdout.strip().split("\n")
                    unpushed.extend([c for c in branch_commits if c])

        return unpushed

    def _get_branch_for_commit(self, commit_hash: str) -> str:
        """Get branch name containing a specific commit"""
        result = self.git_ai.run_git_command(["branch", "--contains", commit_hash])

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                branch = line.strip().replace("* ", "")
                if branch.startswith("ai/"):
                    return branch

        return "unknown"

    def _check_ai_notes_status(self, remote_name: str):
        """Check synchronization status of AI notes"""
        try:
            # Check if remote AI notes exist
            remote_notes_result = self.git_ai.run_git_command(
                ["ls-remote", remote_name, "refs/notes/ai"]
            )

            if remote_notes_result.stdout.strip():
                print("\n✓ Remote AI notes found")

                # Check if local notes are up to date
                local_notes_result = self.git_ai.run_git_command(
                    ["rev-parse", "refs/notes/ai"]
                )

                if local_notes_result.returncode == 0:
                    local_hash = local_notes_result.stdout.strip()
                    remote_hash = remote_notes_result.stdout.split()[0]

                    if local_hash == remote_hash:
                        print("✓ AI notes are synchronized")
                    else:
                        print("⚠ AI notes out of sync - run 'git ai pull'")
                else:
                    print("ℹ No local AI notes - run 'git ai pull'")
            else:
                print("\nℹ No remote AI notes found")

        except (subprocess.SubprocessError, OSError) as e:
            print(f"\n⚠ Could not check AI notes status: {e}")

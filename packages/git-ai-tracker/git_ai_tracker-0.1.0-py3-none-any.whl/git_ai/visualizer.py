#!/usr/bin/env python3
"""
Tree Visualization Module for git-ai

This module provides enhanced visualization of commit trees showing AI contributions
as sub-nodes and sub-branches alongside human-made commits.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CommitInfo:
    """Container for commit information"""
    graph_part: str
    commit_hash: str
    subject: str
    author: str
    date: str
    ai_metadata: Optional[Dict[str, Any]]
    parents: List[str]


class TreeVisualizer:
    """Handles visualization of commit trees with AI annotations"""

    def __init__(self, git_ai_instance):
        self.git_ai = git_ai_instance
        self.repo_root = git_ai_instance.repo_root

        # Unicode characters for tree visualization
        self.tree_chars = {
            "unicode": {
                "branch": "├─",
                "last_branch": "└─",
                "vertical": "│ ",
                "space": "  ",
                "ai_marker": "🤖",
                "human_marker": "👤",
                "merge_marker": "🔀",
                "ai_branch_marker": "🌿",
            },
            "ascii": {
                "branch": "|-",
                "last_branch": "\\-",
                "vertical": "| ",
                "space": "  ",
                "ai_marker": "[AI]",
                "human_marker": "[H]",
                "merge_marker": "[M]",
                "ai_branch_marker": "[AB]",
            },
        }

    def _build_log_command(self, branch: Optional[str], max_commits: int) -> List[str]:
        """Build git log command for tree visualization"""
        log_cmd = [
            "log",
            "--graph",
            "--format=%H|%s|%an|%ad|%P",
            "--date=short",
            f"-n{max_commits}",
        ]

        if branch:
            log_cmd.append(branch)
        else:
            log_cmd.append("--all")

        return log_cmd

    def _process_commit_line(
        self, line: str, chars: Dict[str, str], show_ai_only: bool
    ) -> Optional[str]:
        """Process a single commit line from git log output"""
        if not line.strip():
            return None

        # Extract git graph characters and commit info
        graph_part, commit_part = self._split_graph_and_commit(line)

        if not commit_part:
            return None

        commit_info_parts = commit_part.split("|")
        if len(commit_info_parts) < 4:
            return None

        commit_hash, subject, author, date = commit_info_parts[:4]
        parents = commit_info_parts[4].split() if len(commit_info_parts) > 4 else []

        # Check for AI metadata
        ai_metadata = self._get_ai_metadata(commit_hash)

        # Skip non-AI commits if show_ai_only is True
        if show_ai_only and not ai_metadata:
            return None

        # Format the line with AI annotations
        commit_info = CommitInfo(
            graph_part=graph_part,
            commit_hash=commit_hash,
            subject=subject,
            author=author,
            date=date,
            ai_metadata=ai_metadata,
            parents=parents,
        )
        return self._format_commit_line(commit_info, chars)

    def _process_tree_lines(
        self, lines: List[str], chars: Dict[str, str], show_ai_only: bool
    ) -> List[str]:
        """Process all lines from git log output to build tree"""
        tree_output = []

        for line in lines:
            formatted_line = self._process_commit_line(line, chars, show_ai_only)
            if formatted_line:
                tree_output.append(formatted_line)

                # Add AI sub-branches if this commit has AI children
                commit_hash = self._extract_commit_hash(line)
                if commit_hash:
                    ai_children = self._get_ai_children(commit_hash)
                    if ai_children:
                        graph_part, _ = self._split_graph_and_commit(line)
                        for child in ai_children:
                            child_line = self._format_ai_child_line(child, chars, graph_part)
                            tree_output.append(child_line)

        return tree_output

    def show_ai_tree(
        self,
        branch: Optional[str] = None,
        format_type: str = "unicode",
        max_commits: int = 20,
        show_ai_only: bool = False,
    ) -> str:
        """Display commit tree with AI annotations - clean git log style"""

        # Build git log command for a clean tree view
        log_cmd = [
            "log",
            "--graph",
            "--format=%H|%s|%an|%ad",
            "--date=short",
            f"-n{max_commits}",
        ]

        if branch:
            log_cmd.append(branch)
        else:
            log_cmd.append("--all")

        log_result = self.git_ai.run_git_command(log_cmd)


        if log_result.returncode != 0:
            return "Error retrieving commit history"

        lines = log_result.stdout.strip().split("\n")
        tree_output = []

        for line in lines:
            if not line.strip():
                continue

            # Parse the line to separate graph from commit info
            formatted_line = self._format_clean_commit_line(line, format_type, show_ai_only)
            if formatted_line:
                tree_output.append(formatted_line)

        return "\n".join(tree_output)

    def _format_clean_commit_line(
        self, line: str, format_type: str, show_ai_only: bool
    ) -> Optional[str]:
        """Format a commit line in clean git log style with AI markers"""

        # Handle pure graph lines (branches/merges)
        if re.match(r"^[\s\|\*/\\]+$", line):
            return line

        # Parse commit information
        commit_info = self._parse_commit_line(line)
        if not commit_info:
            return None

        # Skip non-AI commits if requested
        if show_ai_only and not commit_info["ai_metadata"]:
            return None

        # Format the commit line
        return self._build_formatted_line(commit_info, format_type)

    def _parse_commit_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a git log line into its components"""
        # Find the commit hash
        match = re.search(r"([a-f0-9]{40})", line)
        if not match:
            return None

        # Split into graph part and commit info
        graph_part = line[:match.start()]
        commit_part = line[match.start():]

        # Parse commit information
        commit_info_parts = commit_part.split("|")
        if len(commit_info_parts) < 4:
            return None

        commit_hash, subject, author, date = commit_info_parts[:4]
        ai_metadata = self._get_ai_metadata(commit_hash)

        return {
            "graph_part": graph_part,
            "commit_hash": commit_hash,
            "subject": subject,
            "author": author,
            "date": date,
            "ai_metadata": ai_metadata
        }

    def _build_formatted_line(self, commit_info: Dict[str, Any], format_type: str) -> str:
        """Build the formatted commit line with colors and metadata"""
        # Choose marker and color
        marker, color_code = self._get_commit_marker_and_color(
            commit_info["ai_metadata"], format_type
        )

        # Build base line
        short_hash = commit_info["commit_hash"][:8]
        formatted_line = (
            f"{commit_info['graph_part']}{color_code}{marker} {short_hash}\033[0m "
            f"{commit_info['subject']}"
        )

        # Add author and date
        formatted_line += (
            f" \033[90m({commit_info['author']}, {commit_info['date']})\033[0m"
        )

        # Add AI metadata if available
        if commit_info["ai_metadata"]:
            ai_info = self._format_ai_metadata(commit_info["ai_metadata"])
            if ai_info:
                formatted_line += f" \033[33m[{ai_info}]\033[0m"

        return formatted_line

    def _get_commit_marker_and_color(
        self, ai_metadata: Optional[Dict[str, Any]], format_type: str
    ) -> Tuple[str, str]:
        """Get the appropriate marker and color for a commit"""
        if ai_metadata:
            marker = "🤖" if format_type == "unicode" else "[AI]"
            color_code = "\033[36m"  # Cyan for AI commits
        else:
            marker = "👤" if format_type == "unicode" else "[H]"
            color_code = "\033[32m"  # Green for human commits
        return marker, color_code

    def _format_ai_metadata(self, ai_metadata: Dict[str, Any]) -> str:
        """Format AI metadata into a concise string"""
        ai_info_parts = []
        if "ai_system" in ai_metadata:
            ai_info_parts.append(f"AI: {ai_metadata['ai_system']}")
        if "ai_model" in ai_metadata:
            ai_info_parts.append(f"Model: {ai_metadata['ai_model']}")
        if "ai_prompt" in ai_metadata:
            # Truncate long prompts
            prompt = ai_metadata['ai_prompt']
            if len(prompt) > 30:
                prompt = prompt[:27] + "..."
            ai_info_parts.append(f"Prompt: {prompt}")

        return ', '.join(ai_info_parts)

    def _extract_commit_hash(self, line: str) -> Optional[str]:
        """Extract commit hash from git log line"""
        match = re.search(r"([a-f0-9]{40})", line)
        return match.group(1) if match else None

    def _split_graph_and_commit(self, line: str) -> Tuple[str, str]:
        """Split git log line into graph part and commit info"""
        # Find where the commit hash starts (after graph characters)
        match = re.search(r"([a-f0-9]{40})", line)
        if match:
            graph_part = line[: match.start()]
            commit_part = line[match.start() :]
            return graph_part, commit_part
        return line, ""

    def _get_ai_metadata(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Get AI metadata for a commit"""
        return self.git_ai.get_ai_commit_metadata(commit_hash)

    def _get_ai_children(self, commit_hash: str) -> List[Dict[str, Any]]:
        """Get AI commits that are direct children of this commit"""
        # Find commits that have this commit as parent
        children_result = self.git_ai.run_git_command(
            ["log", "--format=%H|%P", "--all"]
        )

        ai_children = []

        for line in children_result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < 2:
                continue

            child_hash, parents = parts[0], parts[1]

            if commit_hash in parents.split():
                # This is a child commit, check if it's an AI commit
                ai_metadata = self._get_ai_metadata(child_hash)
                if ai_metadata:
                    # Get commit details
                    commit_result = self.git_ai.run_git_command(
                        ["log", "-1", "--format=%s|%an|%ad", "--date=short", child_hash]
                    )
                    if commit_result.returncode == 0:
                        commit_details = commit_result.stdout.strip().split("|")
                        if len(commit_details) >= 3:
                            ai_children.append(
                                {
                                    "hash": child_hash,
                                    "subject": commit_details[0],
                                    "author": commit_details[1],
                                    "date": commit_details[2],
                                    "ai_metadata": ai_metadata,
                                }
                            )

        return ai_children

    def _format_commit_line(
        self,
        commit_info: CommitInfo,
        chars: Dict[str, str],
    ) -> str:
        """Format a single commit line with AI annotations"""
        # Note: parents parameter not currently used but kept for future enhancements
        _ = commit_info.parents  # Suppress unused variable warning

        # Determine commit type
        if commit_info.ai_metadata:
            if commit_info.ai_metadata.get("commit_type") == "ai_generated":
                marker = chars["ai_marker"]
                color_code = "\033[94m"  # Blue for AI commits
            elif commit_info.ai_metadata.get("merge_type") == "ai_to_human":
                marker = chars["merge_marker"]
                color_code = "\033[95m"  # Magenta for AI merges
            else:
                marker = chars["ai_marker"]
                color_code = "\033[94m"
        else:
            marker = chars["human_marker"]
            color_code = "\033[92m"  # Green for human commits

        reset_color = "\033[0m"

        # Format hash (short version)
        short_hash = commit_info.commit_hash[:8]

        # Build the formatted line
        formatted_line = (
            f"{commit_info.graph_part}{marker} {color_code}{short_hash}{reset_color} "
            f"{commit_info.subject}"
        )

        # Add author and date
        formatted_line += f" \033[90m({commit_info.author}, {commit_info.date})\033[0m"

        # Add AI-specific information
        if commit_info.ai_metadata:
            ai_info = []
            if "ai_system" in commit_info.ai_metadata:
                ai_info.append(f"AI: {commit_info.ai_metadata['ai_system']}")
            if "ai_model" in commit_info.ai_metadata:
                ai_info.append(f"Model: {commit_info.ai_metadata['ai_model']}")
            if "ai_branch" in commit_info.ai_metadata:
                ai_info.append(f"Branch: {commit_info.ai_metadata['ai_branch']}")

            if ai_info:
                formatted_line += f" \033[93m[{', '.join(ai_info)}]\033[0m"

        return formatted_line

    def _format_ai_child_line(
        self, child_info: Dict[str, Any], chars: Dict[str, str], parent_graph: str
    ) -> str:
        """Format an AI child commit as a sub-branch"""

        # Create indented sub-branch visualization
        indent = len(parent_graph.replace("\t", "    ")) + 2
        sub_branch_prefix = " " * indent + chars["branch"] + chars["ai_branch_marker"]

        color_code = "\033[96m"  # Cyan for AI sub-branches
        reset_color = "\033[0m"

        short_hash = child_info["hash"][:8]
        subject = child_info["subject"]
        ai_system = child_info["ai_metadata"].get("ai_system", "Unknown AI")

        return (
            f"{sub_branch_prefix} {color_code}{short_hash}{reset_color} "
            f"{subject} \033[93m[{ai_system}]\033[0m"
        )

    def _categorize_branches(self, branches_result) -> Tuple[List[str], List[str]]:
        """Categorize branches into AI and human branches"""
        ai_branches = []
        human_branches = []

        for line in branches_result.stdout.strip().split("\n"):
            branch = line.strip().replace("* ", "").replace("  ", "")
            if branch.startswith("ai/"):
                ai_branches.append(branch)
            elif not branch.startswith("remotes/") and branch:
                human_branches.append(branch)

        return ai_branches, human_branches

    def _format_human_branches(
        self, human_branches: List[str], ai_branches: List[str], chars: Dict[str, str]
    ) -> List[str]:
        """Format human branches with their related AI branches"""
        output = []

        for i, branch in enumerate(human_branches):
            is_last = i == len(human_branches) - 1 and not ai_branches
            prefix = chars["last_branch"] if is_last else chars["branch"]
            output.append(f"{prefix} {chars['human_marker']} {branch}")

            # Show AI branches that belong to this human branch
            related_ai_branches = [ai_br for ai_br in ai_branches if branch in ai_br]
            for j, ai_branch in enumerate(related_ai_branches):
                is_last_ai = j == len(related_ai_branches) - 1
                ai_prefix = chars["space"] + (
                    chars["last_branch"] if is_last_ai else chars["branch"]
                )
                output.append(f"{ai_prefix} {chars['ai_marker']} {ai_branch}")

        return output

    def show_ai_branches(self, format_type: str = "unicode") -> str:
        """Show all AI branches and their relationships"""
        chars = self.tree_chars[format_type]

        # Get all branches
        branches_result = self.git_ai.run_git_command(["branch", "-a"])

        if branches_result.returncode != 0:
            return "Error retrieving branches"

        ai_branches, human_branches = self._categorize_branches(branches_result)

        output = []
        output.append("Branch Structure:")
        output.append("")

        # Show human branches with their AI branches
        human_output = self._format_human_branches(human_branches, ai_branches, chars)
        output.extend(human_output)

        # Show orphaned AI branches
        orphaned_ai = [
            ai_br
            for ai_br in ai_branches
            if not any(human_br in ai_br for human_br in human_branches)
        ]

        if orphaned_ai:
            output.append("")
            output.append("Orphaned AI Branches:")
            for i, ai_branch in enumerate(orphaned_ai):
                is_last = i == len(orphaned_ai) - 1
                prefix = chars["last_branch"] if is_last else chars["branch"]
                output.append(f"{prefix} {chars['ai_marker']} {ai_branch}")

        return "\n".join(output)

    def _format_ai_system_stats(
        self, session_id: str, ai_system: Dict[str, Any]
    ) -> Tuple[List[str], int]:
        """Format statistics for a single AI system"""
        output = []
        output.append(f"AI System: {ai_system['name']}")
        output.append(f"  Session ID: {session_id}")
        output.append(f"  Created: {ai_system['created'][:10]}")

        stats = ai_system.get("stats", {})
        commit_count = stats.get("total_commits", 0)
        output.append(f"  Total Commits: {commit_count}")

        if commit_count > 0:
            recent_commits = stats.get("commits", [])[-3:]  # Show last 3
            output.append("  Recent Commits:")
            for commit in recent_commits:
                short_hash = commit["hash"][:8]
                timestamp = commit["timestamp"][:10]
                output.append(f"    {short_hash} ({timestamp})")

        output.append("")
        return output, commit_count

    def _calculate_overall_stats(self, actual_ai_commits: int) -> List[str]:
        """Calculate and format overall repository statistics"""
        output = []

        # Get total regular commits for comparison
        total_commits_result = self.git_ai.run_git_command(
            ["rev-list", "--count", "HEAD"]
        )

        if total_commits_result.returncode == 0:
            total_commits = int(total_commits_result.stdout.strip())

            human_commits = total_commits - actual_ai_commits
            ai_percentage = (
                (actual_ai_commits / total_commits * 100) if total_commits > 0 else 0
            )

            output.append(f"Total Human Commits: {human_commits}")
            output.append(f"AI Contribution: {ai_percentage:.1f}%")

        return output

    def show_ai_statistics(self) -> str:
        """Show statistics about AI contributions"""
        config = self.git_ai.load_config()

        if not config or "ai_systems" not in config:
            return "No AI tracking data available"

        output = []
        output.append("AI Contribution Statistics:")
        output.append("=" * 30)
        output.append("")

        total_ai_commits = 0

        for session_id, ai_system in config["ai_systems"].items():
            system_output, commit_count = self._format_ai_system_stats(session_id, ai_system)
            output.extend(system_output)
            total_ai_commits += commit_count

        # Overall statistics
        actual_ai_commits = len(self.git_ai.tracker.list_ai_commits())
        output.append(f"Total AI Systems: {len(config['ai_systems'])}")
        output.append(f"Total AI Commits: {actual_ai_commits}")

        # Calculate real statistics
        overall_stats = self._calculate_overall_stats(actual_ai_commits)
        output.extend(overall_stats)

        return "\n".join(output)

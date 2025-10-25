#!/usr/bin/env python3
"""
Command-line interface for git-ai

This module provides the command-line interface entry point for the git-ai extension.
"""

import argparse
import subprocess
import sys

from .core import GitAI


def show_detailed_help():
    """Show detailed help information for git-ai"""
    help_text = """
git-ai: A Git extension for tracking AI-made changes

DESCRIPTION:
    git-ai extends Git with the ability to track changes made by AI systems,
    creating a detailed record of AI contributions in your repository. Each AI
    system can have its own branch structure and metadata.

BASIC WORKFLOW:
    1. Initialize:    git ai init
    2. Track AI:      git ai track "GitHub Copilot"
    3. Commit:        git ai commit -m "Add authentication"
    4. Visualize:     git ai tree

CORE COMMANDS:
    init                    Initialize AI tracking in repository
    track <ai-system>       Start tracking an AI system
    commit -m <message>     Commit with AI metadata
    status                  Show AI tracking status

VISUALIZATION COMMANDS:
    tree                    Show commit tree with AI branches
    log                     Show commit history with AI annotations
    branches                Show AI branches structure
    stats                   Show AI contribution statistics

MANAGEMENT COMMANDS:
    config                  Configure AI tracking settings
    merge <ai-branch>       Merge AI branch with conflict resolution

REMOTE COMMANDS:
    setup [remote]          Setup remote synchronization
    push [remote]           Push AI data to remote
    pull [remote]           Pull AI data from remote
    sync [remote]           Bidirectional sync with remote
    remote-status [remote]  Show remote sync status

OPTIONS:
    Use 'git ai <command> --help' for detailed help on specific commands.

EXAMPLES:
    git ai init
    git ai track "GitHub Copilot"
    git ai commit -m "Added user authentication" --ai-prompt "Create login system"
    git ai tree --format unicode
    git ai merge ai/copilot/main

For more information, visit: https://github.com/jgalego/git-ai
"""
    print(help_text.strip())


def create_parser():
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Git extension for tracking AI-made changes", prog="git-ai"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    subparsers.add_parser("init", help="Initialize AI tracking")

    # Track command
    track_parser = subparsers.add_parser("track", help="Start tracking an AI system")
    track_parser.add_argument("ai_system", help="Name of the AI system to track")

    # Experiment command for creating experimental AI branches
    experiment_parser = subparsers.add_parser(
        "experiment", help="Create or switch to experimental AI branch"
    )
    experiment_parser.add_argument("experiment_name", help="Name of the experiment")
    experiment_parser.add_argument(
        "--from-commit", help="Start experiment from specific commit hash"
    )

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit with AI metadata")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    commit_parser.add_argument(
        "--ai-prompt", help="AI prompt that generated the changes"
    )
    commit_parser.add_argument("--ai-model", help="AI model used")
    commit_parser.add_argument("--files", nargs="*", help="Specific files to commit")

    # Log command
    log_parser = subparsers.add_parser(
        "log", help="Show commit history with AI annotations"
    )
    log_parser.add_argument(
        "--ai-only", action="store_true", help="Show only AI commits"
    )
    log_parser.add_argument(
        "-n", "--max-count", type=int, help="Limit number of commits"
    )

    return parser, subparsers


def add_visualization_commands(subparsers):
    """Add visualization-related commands to the parser"""
    # Tree command
    tree_parser = subparsers.add_parser(
        "tree", help="Show commit tree with AI sub-branches"
    )
    tree_parser.add_argument(
        "--format", choices=["ascii", "unicode"], default="unicode", help="Tree format"
    )
    tree_parser.add_argument(
        "-n", "--max-commits", type=int, default=20, help="Maximum commits to show"
    )
    tree_parser.add_argument(
        "--ai-only", action="store_true", help="Show only AI commits"
    )

    # Status command
    subparsers.add_parser("status", help="Show AI tracking status")

    # Branches command
    branches_parser = subparsers.add_parser(
        "branches", help="Show AI branches structure"
    )
    branches_parser.add_argument(
        "--format",
        choices=["ascii", "unicode"],
        default="unicode",
        help="Display format",
    )

    # Stats command
    subparsers.add_parser("stats", help="Show AI contribution statistics")


def add_management_commands(subparsers):
    """Add management-related commands to the parser"""
    # Config command
    config_parser = subparsers.add_parser("config", help="Configure AI tracking")
    config_parser.add_argument(
        "--list", action="store_true", help="List all configuration"
    )
    config_parser.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value"
    )

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge AI branch")
    merge_parser.add_argument("ai_branch", help="AI branch to merge")
    merge_parser.add_argument(
        "--target", help="Target branch (default: current branch)"
    )
    merge_parser.add_argument(
        "--strategy",
        choices=["merge", "squash"],
        default="merge",
        help="Merge strategy",
    )

    # Help command
    subparsers.add_parser("help", help="Show detailed help information")


def add_remote_commands(subparsers):
    """Add remote synchronization commands to the parser"""
    # Remote commands
    setup_parser = subparsers.add_parser("setup", help="Setup remote sync")
    setup_parser.add_argument("remote", nargs="?", default="origin", help="Remote name")

    push_parser = subparsers.add_parser("push", help="Push AI data to remote")
    push_parser.add_argument("remote", nargs="?", default="origin", help="Remote name")
    push_parser.add_argument("--force", action="store_true", help="Force push")

    pull_parser = subparsers.add_parser("pull", help="Pull AI data from remote")
    pull_parser.add_argument("remote", nargs="?", default="origin", help="Remote name")

    sync_parser = subparsers.add_parser("sync", help="Sync AI data bidirectionally")
    sync_parser.add_argument("remote", nargs="?", default="origin", help="Remote name")

    remote_status_parser = subparsers.add_parser(
        "remote-status", help="Show remote sync status"
    )
    remote_status_parser.add_argument(
        "remote", nargs="?", default="origin", help="Remote name"
    )


def execute_core_commands(git_ai, args):
    """Execute core git-ai commands"""
    if args.command == "init":
        git_ai.init()
    elif args.command == "track":
        git_ai.track(args.ai_system)
    elif args.command == "experiment":
        git_ai.create_experiment(args.experiment_name, args.from_commit)
    elif args.command == "commit":
        git_ai.commit(args.message, args.ai_prompt, args.ai_model, args.files)
    elif args.command == "status":
        git_ai.show_status()
    else:
        return False
    return True


def execute_visualization_commands(git_ai, args):
    """Execute visualization commands"""
    if args.command == "log":
        git_ai.show_log(args.ai_only, args.max_count)
    elif args.command == "tree":
        git_ai.show_tree(args.format, args.max_commits, args.ai_only)
    elif args.command == "branches":
        git_ai.show_branches(args.format)
    elif args.command == "stats":
        git_ai.show_statistics()
    else:
        return False
    return True


def execute_management_commands(git_ai, args):
    """Execute management commands"""
    if args.command == "config":
        set_key, set_value = (
            (args.set[0], args.set[1]) if args.set else (None, None)
        )
        git_ai.show_config(args.list, set_key, set_value)
    elif args.command == "merge":
        git_ai.merge_ai_branch(args.ai_branch, args.target, args.strategy)
    elif args.command == "help":
        show_detailed_help()
    else:
        return False
    return True


def execute_remote_commands(git_ai, args):
    """Execute remote synchronization commands"""
    if args.command == "setup":
        git_ai.setup_remote(args.remote)
    elif args.command == "push":
        git_ai.push_ai_data(args.remote, args.force)
    elif args.command == "pull":
        git_ai.pull_ai_data(args.remote)
    elif args.command == "sync":
        git_ai.sync_ai_data(args.remote)
    elif args.command == "remote-status":
        git_ai.show_remote_status(args.remote)
    else:
        return False
    return True


def main():
    """Main entry point for the git-ai command"""
    parser, subparsers = create_parser()

    # Add command groups
    add_visualization_commands(subparsers)
    add_management_commands(subparsers)
    add_remote_commands(subparsers)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        git_ai = GitAI()

        # Execute commands by category
        if execute_core_commands(git_ai, args):
            return
        if execute_visualization_commands(git_ai, args):
            return
        if execute_management_commands(git_ai, args):
            return
        if execute_remote_commands(git_ai, args):
            return

        # Unknown command
        print(f"Unknown command: {args.command}")
        parser.print_help()

    except (subprocess.SubprocessError, OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

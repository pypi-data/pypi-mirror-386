# Git AI

A Git extension that tracks and visualizes changes made by AI systems as separate nodes and branches in your commit tree, with full team collaboration support.

> *Because sometimes you need to track who's doing the **actual** thinking in your codebase.*

<img src="https://github.com/JGalego/git-ai/blob/main/git-ai.jpg?raw=true" alt="Git AI Visualization" title="&#34;It's like comparing apples and oranges; they're both delicious&#34; - Cyd Charisse" width="50%"/>

## Warning ⚠️

**This extension is highly experimental and under active development.** The developers take no responsibility for any damages, data loss, or repository corruption that may occur when using this software on real-life repositories.

**Use at your own risk** and always test thoroughly on non-critical repositories first.

## Features

- 🤖 **AI Change Tracking**: Mark and track commits made by AI systems
- 🌳 **Visual Commit Tree**: Enhanced git log with AI annotations and sub-branches  
- 📊 **AI Statistics**: View contribution statistics and AI system usage
- 🔀 **Smart Merging**: Merge AI branches with proper conflict resolution
- 📝 **Metadata Storage**: Store AI prompts, models, and context with commits
- 🎨 **Beautiful Visualization**: Unicode and ASCII tree formats with colors
- 🌐 **Remote Collaboration**: Full team synchronization of AI metadata and branches
- ⚙️ **Conflict Resolution**: Handle AI metadata and branch conflicts intelligently

## Installation

### From PyPI (recommended)

```bash
pip install git-ai-tracker
```

### From Source

```bash
git clone https://github.com/jgalego/git-ai.git
cd git-ai
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/jgalego/git-ai.git
cd git-ai
pip install -e ".[dev]"
```

## Quick Start

```bash
# Get help
git ai help

# Initialize AI tracking
git ai init

# Start tracking an AI system
git ai track "GitHub Copilot"

# Make AI changes and commit them
git ai commit -m "Add user authentication" --ai-prompt "Create a login system" --ai-model "gpt-4"

# Visualize your AI contributions
git ai tree
git ai stats
```

## Commands

### Core Commands

- `git ai init` - Initialize AI tracking for this repository
- `git ai track <ai-system>` - Start tracking changes for an AI system
- `git ai commit -m <message>` - Commit with AI metadata
- `git ai status` - Show current AI tracking status
- `git ai help` - Show detailed help information

### Visualization Commands

- `git ai tree` - Show commit tree with AI sub-branches
- `git ai log` - Show commit history with AI annotations
- `git ai branches` - Show AI branches structure
- `git ai stats` - Show AI contribution statistics

### Management Commands

- `git ai merge <ai-branch>` - Merge AI branch with conflict resolution
- `git ai experiment <name>` - Create experimental branch for testing AI ideas
- `git ai config` - Configure AI tracking settings

### Remote Commands

- `git ai setup <remote>` - Setup remote synchronization
- `git ai push <remote>` - Push AI data to remote
- `git ai remote-status <remote>` - Show remote synchronization status

## Team Collaboration

### Setup for Team

```bash
# Repository owner
git ai init
git ai track "GitHub Copilot"
git ai commit -m "Add auth" --ai-prompt "Create login system"
git ai setup origin
git ai push origin

# Team member
git clone <repo>
git ai init                    # Initialize on cloned repo
git fetch origin refs/notes/ai:refs/notes/ai  # Get AI metadata
git ai track "Claude"          # Track their AI system
git ai commit -m "Add dashboard"
git ai push origin             # Share with team
```

### Daily Workflow

```bash
git pull                       # Get latest changes
git fetch origin refs/notes/ai:refs/notes/ai  # Get AI metadata
# Make AI-assisted changes
git ai commit -m "..." --ai-prompt "..." --ai-model "..."
git ai push origin             # Share changes and AI metadata
```

### Experimental Workflow

```bash
# Try experimental AI ideas
git ai experiment "feature-x"
git ai commit -m "Experimental feature" --ai-prompt "Try new approach"

# If experiment fails, switch back to main AI branch
git checkout ai/copilot/main

# If experiment succeeds, merge it
git checkout main
git ai merge ai/copilot/main_experiment_feature-x
```

## How It Works

`git-ai` extends Git's functionality by:

1. **Metadata Storage**: Uses Git notes to store AI-specific metadata (prompts, models, timestamps)
2. **Branch Management**: Creates lightweight AI branches prefixed with `ai/`
3. **Commit Annotation**: Marks commits with AI system information
4. **Visual Enhancement**: Provides enhanced log and tree views showing AI contributions
5. **Remote Synchronization**: Syncs AI notes, branches, and configuration across team

### Architecture

```
your-repo/
├── .git/
│   ├── ai/                  # AI configuration
│   │   └── config.json      # AI systems and settings
│   └── notes/
│       └── ai               # AI metadata for commits
├── main                     # Your main branch
├── feature/auth             # Human feature branch
├── ai/copilot/main          # AI sub-branch of main
└── ai/copilot/feature/auth  # AI sub-branch of feature
```

### Remote Synchronization

The extension synchronizes:
- **AI Notes**: All metadata about AI contributions
- **AI Branches**: Complete AI branch structure  
- **AI Configuration**: Team-wide AI system settings

## Tree Visualization

git-ai provides enhanced commit visualization:

```
*   🤖 e1f2g3h4 Merge AI changes from ai/copilot/main (alice, 2024-01-15) [AI: merge]
|\
| * 🤖 c3d4e5f6 AI addition: error handling (alice, 2024-01-15) [AI: GitHub Copilot, Model: gpt-4, Prompt: Add error handling]
| * 🤖 b2c3d4e5 AI rewrite: improved validation (alice, 2024-01-15) [AI: GitHub Copilot, Model: gpt-4, Prompt: Make validation more robust]
| * 🤖 a1b2c3d4 AI: Add user authentication (alice, 2024-01-15) [AI: GitHub Copilot, Model: gpt-4, Prompt: Create a login system]
|/
* 👤 d4e5f6g7 Update documentation (bob, 2024-01-14)
* 👤 f5g6h7i8 Initial commit (alice, 2024-01-13)
```

**Legend**: 🤖 AI-generated • 👤 Human-made

## Advanced Usage

### Multiple AI Systems

```bash
git ai track "GitHub Copilot"
git ai track "Claude"
git ai track "Custom AI"

# View contribution breakdown
git ai stats
```

### Code Review Integration

```bash
# Review only AI contributions
git ai log --ai-only

git ai merge ai/copilot/feature --strategy squash
```

### CI/CD Integration

```bash
git ai track "CI Bot"
git ai commit -m "Auto-format code" --ai-model "prettier"
```

## Troubleshooting

### Remote Issues

```bash
# Sync AI metadata with remote
git ai setup origin
git ai push origin

# Manual sync if needed
git fetch origin refs/notes/ai:refs/notes/ai
git push origin refs/notes/ai

# Check remote status
git ai remote-status origin
```

### Common Issues

- **"git-ai command not found"**: Check if package is installed (`pip list | grep git-ai-tracker`)
- **"No active AI session"**: Run `git ai track "Your AI System"`
- **"Not a git repository"**: Run commands from within a Git repository
- **Remote sync not working**: Use standard `git` commands for notes and branches

### Development

```bash
# Run tests
pytest

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## Requirements

- Git 2.0+
- Python 3.8+
- Unix-like system (Linux, macOS) or WSL on Windows

## License

[MIT](LICENSE)

---

**Track your AI contributions and collaborate seamlessly with your team!** 🤖✨
# Simpleminded Shell MCP Server

An MCP (Model Context Protocol) server that provides AI assistants with complete understanding of your simpleminded-shell environment.

## What It Does

This MCP server exposes your shell configuration, aliases, installed tools, and usage examples to AI assistants like Claude Code, enabling them to:

- **Understand your environment** - Know that `cat` actually runs `bat`, `grep` runs `ripgrep`, etc.
- **Translate commands** - Convert traditional Unix commands to modern equivalents
- **Check tool installation** - Verify which tools are installed and their versions
- **Provide relevant examples** - Get context-aware usage examples
- **Recommend tools** - Suggest the right tool for any task

## Prerequisites

Before using this MCP server, you should have simpleminded-shell configured:

```bash
# Clone the main repository
git clone https://github.com/yourusername/simpleminded-shell.git
cd simpleminded-shell

# Run the interactive installer
bash install.sh
```

This sets up your shell with modern CLI tools and aliases that the MCP server will expose to AI assistants.

## Quick Start

### Install with uvx (Recommended)

```bash
# Run directly with uvx (no installation needed!)
uvx --from git+https://github.com/yourusername/simpleminded-shell simpleminded-mcp
```

### Install with pip

```bash
# From PyPI (once published)
pip install simplemindedshellmcp

# Or from source
cd simpleminded-shell/mcp-server
pip install -e .
```

### Configure Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "simpleminded-shell": {
      "command": "uvx",
      "args": [
        "--from",
        "simplemindedshellmcp",
        "simpleminded-mcp"
      ]
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "simpleminded-shell": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

## Features

### Resources

Read-only resources that provide information about your environment:

- `simpleminded://config/info` - Configuration file location and details
- `simpleminded://aliases/all` - All your shell aliases
- `simpleminded://aliases/category/{category}` - Aliases by category (git, file, docker, etc.)
- `simpleminded://tools/status` - Installation status of all tools
- `simpleminded://tools/summary` - Summary of installed vs missing tools
- `simpleminded://examples/all` - Usage examples for all tools
- `simpleminded://workflows/all` - Common multi-step workflows

### Tools

Interactive tools that AI can invoke:

- **translate_command** - Convert traditional command to modern equivalent
  ```
  Input: grep -r "pattern" .
  Output: rg "pattern"
  ```

- **check_tool** - Check if tool is installed and get version
  ```
  Input: bat
  Output: {installed: true, version: "0.24.0", path: "/opt/homebrew/bin/bat"}
  ```

- **get_examples** - Get usage examples for a tool
  ```
  Input: tool=fd, use_case=find_by_extension
  Output: [{command: "fd -e py", description: "Find all Python files"}]
  ```

- **explain_alias** - Explain what an alias actually does
  ```
  Input: cat
  Output: Runs 'bat --paging=never' - provides syntax highlighting
  ```

- **search_examples** - Search examples by keyword
  ```
  Input: "find python files"
  Output: Examples from fd, rg showing how to find Python files
  ```

- **get_tool_benefits** - Why use modern tool over traditional
  ```
  Input: rg
  Output: [Faster than grep, respects .gitignore, Unicode support, ...]
  ```

- **recommend_tools** - Get tool recommendations for a task
  ```
  Input: "search for text in files"
  Output: Recommends rg with relevant examples
  ```

## Architecture

```
mcp-server/
├── src/
│   ├── server.py              # Main MCP server
│   ├── config_parser.py       # Auto-detect shell config
│   ├── alias_detector.py      # Parse aliases from config
│   ├── command_translator.py  # Translate commands
│   ├── tool_checker.py        # Check tool installation
│   └── example_provider.py    # Provide examples
├── tests/
│   └── (test files)
├── pyproject.toml
└── README.md
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/simpleminded-shell.git
cd simpleminded-shell/mcp-server

# Install in development mode
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Locally

```bash
# Run the server
python -m src.server

# Or use the entry point
simpleminded-mcp
```

## Configuration

The server automatically detects your shell configuration by checking:

1. `~/.zshrc`
2. `~/.bashrc`
3. `~/.config/zsh/.zshrc`
4. `~/.bash_profile`
5. `~/.profile`

It looks for:
- The `SIMPLEMINDED-SHELL-CONFIG` marker
- Characteristic aliases like `alias cat='bat'`

## Publishing to PyPI

### Build

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build
```

### Test Upload (TestPyPI)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ simplemindedshellmcp
```

### Production Upload

```bash
# Upload to PyPI
python -m twine upload dist/*
```

## Requirements

- Python 3.10+
- `mcp` Python package
- Simpleminded-shell configured in your shell (optional but recommended)

## License

MIT License - See LICENSE file for details

## Contributing

Issues and pull requests welcome!

## See Also

- [Main Simpleminded Shell Documentation](../README.md)
- [MCP Server User Guide](../docs/MCP-SERVER.md)
- [AI Setup Guide](../docs/AI-SETUP.md)

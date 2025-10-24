"""Provide context-aware usage examples for tools and aliases."""

from typing import List, Dict, Optional


class ExampleProvider:
    """Provide usage examples for simpleminded-shell tools."""

    EXAMPLES = {
        "bat": [
            {
                "use_case": "view_file",
                "command": "bat script.py",
                "description": "View file with syntax highlighting"
            },
            {
                "use_case": "with_paging",
                "command": "bat long-file.log",
                "description": "View long file with automatic paging"
            },
            {
                "use_case": "plain",
                "command": "bat --style=plain config.txt",
                "description": "View without line numbers and decorations"
            },
            {
                "use_case": "show_changes",
                "command": "bat --diff modified.py",
                "description": "Show git changes with syntax highlighting"
            },
        ],
        "fd": [
            {
                "use_case": "find_by_name",
                "command": 'fd "config"',
                "description": "Find files named config"
            },
            {
                "use_case": "find_by_extension",
                "command": "fd -e py",
                "description": "Find all Python files"
            },
            {
                "use_case": "include_hidden",
                "command": "fd -H .env",
                "description": "Find including hidden files"
            },
            {
                "use_case": "directories_only",
                "command": "fd -t d node_modules",
                "description": "Find directories only"
            },
            {
                "use_case": "execute_on_results",
                "command": 'fd -e js -x wc -l',
                "description": "Count lines in all JavaScript files"
            },
        ],
        "rg": [
            {
                "use_case": "basic_search",
                "command": 'rg "TODO"',
                "description": "Search for TODO in all files"
            },
            {
                "use_case": "case_insensitive",
                "command": 'rg -i "error"',
                "description": "Case-insensitive search"
            },
            {
                "use_case": "by_type",
                "command": 'rg --type py "import"',
                "description": "Search only Python files"
            },
            {
                "use_case": "count_matches",
                "command": 'rg --count "FIXME"',
                "description": "Count matches per file"
            },
            {
                "use_case": "list_files",
                "command": 'rg -l "class"',
                "description": "List files containing matches"
            },
        ],
        "eza": [
            {
                "use_case": "basic_list",
                "command": "eza",
                "description": "List files with colors and icons"
            },
            {
                "use_case": "detailed",
                "command": "ll",
                "description": "Detailed list with git status"
            },
            {
                "use_case": "tree_view",
                "command": "lt",
                "description": "Tree view (2 levels deep)"
            },
            {
                "use_case": "directories_only",
                "command": "eza -D",
                "description": "List directories only"
            },
        ],
        "fzf": [
            {
                "use_case": "find_file",
                "command": "ff",
                "description": "Fuzzy find and edit files"
            },
            {
                "use_case": "search_history",
                "command": "Ctrl+R",
                "description": "Search command history"
            },
            {
                "use_case": "change_directory",
                "command": "cdf",
                "description": "Change directory with preview"
            },
        ],
        "lazygit": [
            {
                "use_case": "visual_git",
                "command": "lg",
                "description": "Visual Git interface for all operations"
            },
        ],
        "mise": [
            {
                "use_case": "show_versions",
                "command": "mise current",
                "description": "Show current tool versions"
            },
            {
                "use_case": "install_tool",
                "command": "mise install python@3.12",
                "description": "Install Python 3.12"
            },
            {
                "use_case": "use_version",
                "command": "mise use python@3.12",
                "description": "Use Python 3.12 in current project"
            },
        ],
        "jq": [
            {
                "use_case": "pretty_print",
                "command": "cat data.json | jq",
                "description": "Pretty print JSON"
            },
            {
                "use_case": "extract_field",
                "command": "jq '.users[].name' data.json",
                "description": "Extract specific field"
            },
            {
                "use_case": "show_keys",
                "command": "jq 'keys' data.json",
                "description": "Show all keys"
            },
        ],
    }

    WORKFLOWS = {
        "search_and_edit": {
            "description": "Search for pattern and edit matching files",
            "steps": [
                'rg "TODO" -l  # List files with TODOs',
                'ff  # Fuzzy find and open in editor',
            ],
        },
        "find_and_view": {
            "description": "Find files and view with syntax highlighting",
            "steps": [
                'fd -e py  # Find Python files',
                'bat $(fd -e py | fzf)  # Preview and select to view',
            ],
        },
        "git_workflow": {
            "description": "Quick git workflow",
            "steps": [
                'lg  # Open lazygit',
                '# Or use commands:',
                'gs  # Check status',
                'ga .  # Stage all',
                'gc -m "message"  # Commit',
                'gp  # Push',
            ],
        },
        "search_replace": {
            "description": "Search and replace across files",
            "steps": [
                'rg "old_function" -l  # Find files',
                'fd -e py | xargs sed -i "" "s/old_function/new_function/g"',
            ],
        },
    }

    def get_examples(self, tool: str, use_case: Optional[str] = None) -> List[Dict]:
        """Get examples for a tool."""
        tool_examples = self.EXAMPLES.get(tool, [])

        if use_case:
            return [ex for ex in tool_examples if ex["use_case"] == use_case]

        return tool_examples

    def get_workflow(self, workflow_name: str) -> Optional[Dict]:
        """Get a specific workflow."""
        return self.WORKFLOWS.get(workflow_name)

    def get_all_workflows(self) -> Dict[str, Dict]:
        """Get all available workflows."""
        return self.WORKFLOWS

    def search_examples(self, query: str) -> List[Dict]:
        """Search examples by description or command."""
        query_lower = query.lower()
        results = []

        for tool, examples in self.EXAMPLES.items():
            for example in examples:
                if (query_lower in example["command"].lower() or
                    query_lower in example["description"].lower() or
                    query_lower in tool.lower()):
                    results.append({
                        "tool": tool,
                        **example
                    })

        return results

    def get_use_cases(self, tool: str) -> List[str]:
        """Get available use cases for a tool."""
        tool_examples = self.EXAMPLES.get(tool, [])
        return [ex["use_case"] for ex in tool_examples]

    def get_all_tools(self) -> List[str]:
        """Get list of tools with examples."""
        return list(self.EXAMPLES.keys())

    def get_recommendations(self, task_description: str) -> List[Dict]:
        """Get tool recommendations based on task description."""
        task_lower = task_description.lower()

        recommendations = []

        # File viewing
        if any(word in task_lower for word in ["view", "read", "see", "show", "display"]):
            if any(word in task_lower for word in ["file", "code", "script"]):
                recommendations.append({
                    "tool": "bat",
                    "reason": "View files with syntax highlighting",
                    "examples": self.get_examples("bat")[:2]
                })

        # Searching
        if any(word in task_lower for word in ["search", "find text", "grep", "look for"]):
            recommendations.append({
                "tool": "rg",
                "reason": "Fast text search across files",
                "examples": self.get_examples("rg")[:3]
            })

        # Finding files
        if any(word in task_lower for word in ["find file", "locate", "where is"]):
            recommendations.append({
                "tool": "fd",
                "reason": "Fast file finding with simple syntax",
                "examples": self.get_examples("fd")[:3]
            })

        # Git operations
        if any(word in task_lower for word in ["git", "commit", "push", "branch", "repository"]):
            recommendations.append({
                "tool": "lazygit",
                "reason": "Visual Git interface for all operations",
                "examples": self.get_examples("lazygit")
            })

        # JSON processing
        if any(word in task_lower for word in ["json", "api", "parse"]):
            recommendations.append({
                "tool": "jq",
                "reason": "Process and query JSON data",
                "examples": self.get_examples("jq")
            })

        return recommendations

"""Detect and parse shell aliases from configuration."""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Alias:
    """Represents a shell alias."""
    name: str
    command: str
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ShellFunction:
    """Represents a shell function."""
    name: str
    body: str
    description: Optional[str] = None


class AliasDetector:
    """Detect and categorize aliases from shell configuration."""

    # Alias categories based on command patterns
    CATEGORIES = {
        "file": ["cat", "bat", "ls", "ll", "lt", "eza", "tree", "find", "fd"],
        "search": ["grep", "rg", "search", "ff"],
        "git": ["git", "g", "gs", "ga", "gc", "gp", "gl", "lg", "gcb", "gd", "glog"],
        "docker": ["docker", "ld", "dps", "dimg", "dexec"],
        "navigation": ["cd", "z", "cdf", "mkcd"],
        "version": ["mise", "mc", "mls", "mi", "mu"],
        "docs": ["tldr", "tl", "md", "glow", "cheat"],
        "json": ["jq", "jqp", "jqr", "jqc", "jqs", "jqk"],
        "ai": ["ollama", "ol", "olls", "olrun", "olpull"],
        "system": ["ps", "top", "ports", "fkill"],
        "utility": ["extract", "backup", "sizeof", "trash", "rm"],
    }

    def __init__(self, config_content: str):
        """Initialize with configuration content."""
        self.config_content = config_content
        self._aliases: Optional[Dict[str, Alias]] = None
        self._functions: Optional[Dict[str, ShellFunction]] = None

    def parse_aliases(self) -> Dict[str, Alias]:
        """Parse all aliases from configuration."""
        if self._aliases is not None:
            return self._aliases

        aliases = {}

        # Match: alias name='command' or alias name="command"
        pattern = r"^alias\s+([a-zA-Z0-9_\-\.]+)=['\"](.+?)['\"]"

        for line in self.config_content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            match = re.match(pattern, line)
            if match:
                name, command = match.groups()
                category = self._categorize_alias(name, command)
                aliases[name] = Alias(
                    name=name,
                    command=command,
                    category=category
                )

        self._aliases = aliases
        return aliases

    def parse_functions(self) -> Dict[str, ShellFunction]:
        """Parse shell functions from configuration."""
        if self._functions is not None:
            return self._functions

        functions = {}
        lines = self.config_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Match function definition: function_name() { or function function_name {
            func_match = re.match(r"^(?:function\s+)?([a-zA-Z0-9_\-]+)\s*\(\)\s*\{?", line)

            if func_match:
                name = func_match.group(1)
                body_lines = [line]
                brace_count = line.count("{") - line.count("}")
                i += 1

                # Collect function body until closing brace
                while i < len(lines) and brace_count > 0:
                    body_line = lines[i]
                    body_lines.append(body_line)
                    brace_count += body_line.count("{") - body_line.count("}")
                    i += 1

                functions[name] = ShellFunction(
                    name=name,
                    body="\n".join(body_lines)
                )
            else:
                i += 1

        self._functions = functions
        return functions

    def _categorize_alias(self, name: str, command: str) -> str:
        """Categorize an alias based on its name and command."""
        name_lower = name.lower()
        command_lower = command.lower()

        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in name_lower or keyword in command_lower:
                    return category

        return "other"

    def get_aliases_by_category(self, category: str) -> Dict[str, Alias]:
        """Get all aliases in a specific category."""
        all_aliases = self.parse_aliases()
        return {
            name: alias
            for name, alias in all_aliases.items()
            if alias.category == category
        }

    def get_all_categories(self) -> List[str]:
        """Get list of all categories with aliases."""
        all_aliases = self.parse_aliases()
        categories = set(alias.category for alias in all_aliases.values())
        return sorted(categories)

    def get_alias(self, name: str) -> Optional[Alias]:
        """Get a specific alias by name."""
        aliases = self.parse_aliases()
        return aliases.get(name)

    def get_function(self, name: str) -> Optional[ShellFunction]:
        """Get a specific function by name."""
        functions = self.parse_functions()
        return functions.get(name)

    def search_aliases(self, query: str) -> Dict[str, Alias]:
        """Search aliases by name or command."""
        all_aliases = self.parse_aliases()
        query_lower = query.lower()

        return {
            name: alias
            for name, alias in all_aliases.items()
            if query_lower in name.lower() or query_lower in alias.command.lower()
        }

    def to_dict(self) -> Dict:
        """Convert all parsed data to dictionary format."""
        return {
            "aliases": {
                name: {
                    "name": alias.name,
                    "command": alias.command,
                    "category": alias.category,
                }
                for name, alias in self.parse_aliases().items()
            },
            "functions": {
                name: {
                    "name": func.name,
                    "body": func.body,
                }
                for name, func in self.parse_functions().items()
            },
            "categories": self.get_all_categories(),
        }

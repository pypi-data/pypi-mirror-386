"""Translate traditional Unix commands to modern simpleminded-shell equivalents."""

import re
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class Translation:
    """Represents a command translation."""
    original: str
    modern: str
    explanation: str
    tool: str


class CommandTranslator:
    """Translate traditional commands to modern tool equivalents."""

    # Direct command replacements
    REPLACEMENTS = {
        "cat": "bat",
        "find": "fd",
        "grep": "rg",
        "ls": "eza",
    }

    # Flag translations for common patterns
    FLAG_TRANSLATIONS = {
        "cat": {
            "-n": "--number",  # bat uses --number for line numbers
        },
        "grep": {
            "-r": "",  # rg is recursive by default
            "-i": "-i",  # case insensitive
            "-v": "-v",  # invert match
            "-c": "--count",
            "-l": "--files-with-matches",
            "-n": "-n",  # line numbers (default in rg)
            "-w": "-w",  # word regexp
            "-E": "",  # rg uses regex by default
            "--include": "--type",  # Different syntax
        },
        "find": {
            "-name": "",  # fd doesn't need -name
            "-type f": "-t f",
            "-type d": "-t d",
            "-iname": "-i",  # case insensitive
        },
        "ls": {
            "-la": "ll",  # Common alias
            "-l": "-l",
            "-a": "-a",
            "-h": "-h",
        }
    }

    COMMON_PATTERNS = [
        # grep patterns
        (
            r"grep\s+-r\s+['\"](.+?)['\"]",
            r'rg "\1"',
            "ripgrep is recursive by default",
            "ripgrep"
        ),
        (
            r"grep\s+-ri\s+['\"](.+?)['\"]",
            r'rg -i "\1"',
            "Case-insensitive ripgrep search",
            "ripgrep"
        ),
        (
            r"grep\s+--include=['\"]?\*\.(\w+)['\"]?\s+['\"](.+?)['\"]",
            r'rg --type \1 "\2"',
            "Filter by file type",
            "ripgrep"
        ),

        # find patterns
        (
            r"find\s+\.\s+-name\s+['\"](.+?)['\"]",
            r'fd "\1"',
            "fd doesn't need -name flag",
            "fd"
        ),
        (
            r"find\s+\.\s+-type\s+f\s+-name\s+['\"]?\*\.(\w+)['\"]?",
            r'fd -e \1',
            "Use -e for extension search",
            "fd"
        ),
        (
            r"find\s+\.\s+-name\s+['\"](.+?)['\"].*-type\s+f",
            r'fd -t f "\1"',
            "Specify file type with -t",
            "fd"
        ),

        # cat patterns
        (
            r"cat\s+(.+?)\s+\|\s+grep",
            r'bat \1 | rg',
            "Use bat for syntax highlighting",
            "bat"
        ),

        # ls patterns
        (
            r"ls\s+-la",
            r'll',
            "Use ll alias for detailed listing",
            "eza"
        ),
        (
            r"ls\s+-lah",
            r'll',
            "ll provides human-readable sizes by default",
            "eza"
        ),
    ]

    def translate(self, command: str) -> Optional[Translation]:
        """Translate a traditional command to modern equivalent."""
        command = command.strip()

        # Try pattern matching first
        for pattern, replacement, explanation, tool in self.COMMON_PATTERNS:
            match = re.match(pattern, command)
            if match:
                modern_cmd = re.sub(pattern, replacement, command)
                return Translation(
                    original=command,
                    modern=modern_cmd,
                    explanation=explanation,
                    tool=tool
                )

        # Try simple command replacement
        parts = command.split(maxsplit=1)
        if parts:
            cmd = parts[0]
            if cmd in self.REPLACEMENTS:
                modern_cmd = command.replace(cmd, self.REPLACEMENTS[cmd], 1)
                return Translation(
                    original=command,
                    modern=modern_cmd,
                    explanation=f"Use {self.REPLACEMENTS[cmd]} instead of {cmd}",
                    tool=self.REPLACEMENTS[cmd]
                )

        return None

    def get_examples(self) -> List[Dict[str, str]]:
        """Get translation examples."""
        examples = [
            {
                "traditional": 'grep -r "pattern" .',
                "modern": 'rg "pattern"',
                "explanation": "ripgrep is recursive by default, much faster",
            },
            {
                "traditional": 'find . -name "*.py"',
                "modern": 'fd -e py',
                "explanation": "fd has simpler syntax, respects .gitignore",
            },
            {
                "traditional": 'grep -ri "error" --include="*.log"',
                "modern": 'rg -i --type log "error"',
                "explanation": "Use file type filters instead of glob patterns",
            },
            {
                "traditional": "cat file.py | grep 'def'",
                "modern": "bat file.py | rg 'def'",
                "explanation": "bat adds syntax highlighting, rg is faster",
            },
            {
                "traditional": "ls -la",
                "modern": "ll",
                "explanation": "ll alias provides detailed list with icons and git status",
            },
            {
                "traditional": 'find . -type f -name "*.js" -exec grep -l "TODO" {} \\;',
                "modern": 'fd -e js | xargs rg -l "TODO"',
                "explanation": "Simpler syntax, much faster execution",
            },
            {
                "traditional": "find . -type d -name node_modules",
                "modern": "fd -t d node_modules",
                "explanation": "Use -t for type, simpler syntax",
            },
        ]
        return examples

    def explain_alias(self, alias_name: str, alias_command: str) -> str:
        """Explain what an alias actually does."""
        explanations = {
            "cat": f"Runs '{alias_command}' - provides syntax highlighting and Git integration",
            "grep": f"Runs '{alias_command}' - much faster, respects .gitignore by default",
            "find": f"Runs '{alias_command}' - faster, simpler syntax, smart defaults",
            "ls": f"Runs '{alias_command}' - modern output with icons and Git status",
        }

        for cmd, explanation in explanations.items():
            if cmd in alias_name.lower():
                return explanation

        return f"Runs: {alias_command}"

    def get_tool_benefits(self, tool: str) -> List[str]:
        """Get benefits of using modern tool over traditional."""
        benefits = {
            "bat": [
                "Syntax highlighting for 200+ languages",
                "Git integration shows file changes",
                "Automatic paging for long files",
                "Line numbers and decorations",
                "Works as MANPAGER for colored man pages",
            ],
            "fd": [
                "10x faster than find",
                "Intuitive syntax - no -name flag needed",
                "Respects .gitignore by default",
                "Colored output",
                "Parallel directory traversal",
                "Smart case matching",
            ],
            "rg": [
                "Blazingly fast - faster than grep, ag, ack",
                "Respects .gitignore by default",
                "Full Unicode support",
                "Multiline search",
                "Smart case (lowercase = case-insensitive)",
                "Search inside compressed files",
            ],
            "eza": [
                "Beautiful icons for file types",
                "Git integration shows file status",
                "Tree view built in",
                "Colors and formatting",
                "Faster than ls",
            ],
        }
        return benefits.get(tool, [])

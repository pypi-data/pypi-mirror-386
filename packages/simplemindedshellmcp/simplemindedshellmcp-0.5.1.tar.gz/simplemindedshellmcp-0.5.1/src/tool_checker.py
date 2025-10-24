"""Check for installed tools and their versions."""

import subprocess
import re
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ToolInfo:
    """Information about an installed tool."""
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    brew_package: Optional[str] = None


class ToolChecker:
    """Check installation status and versions of simpleminded-shell tools."""

    SIMPLEMINDED_TOOLS = {
        "bat": {"brew": "bat", "version_flag": "--version", "version_pattern": r"bat (\d+\.\d+\.\d+)"},
        "fd": {"brew": "fd", "version_flag": "--version", "version_pattern": r"fd (\d+\.\d+\.\d+)"},
        "rg": {"brew": "ripgrep", "version_flag": "--version", "version_pattern": r"ripgrep (\d+\.\d+\.\d+)"},
        "eza": {"brew": "eza", "version_flag": "--version", "version_pattern": r"v(\d+\.\d+\.\d+)"},
        "lazygit": {"brew": "lazygit", "version_flag": "--version", "version_pattern": r"version=(\d+\.\d+\.\d+)"},
        "lazydocker": {"brew": "lazydocker", "version_flag": "--version", "version_pattern": r"Version: (\d+\.\d+\.\d+)"},
        "zellij": {"brew": "zellij", "version_flag": "--version", "version_pattern": r"zellij (\d+\.\d+\.\d+)"},
        "mise": {"brew": "mise", "version_flag": "--version", "version_pattern": r"(\d+\.\d+\.\d+)"},
        "tldr": {"brew": "tealdeer", "version_flag": "--version", "version_pattern": r"tealdeer (\d+\.\d+\.\d+)"},
        "glow": {"brew": "glow", "version_flag": "--version", "version_pattern": r"glow version (\d+\.\d+\.\d+)"},
        "fzf": {"brew": "fzf", "version_flag": "--version", "version_pattern": r"(\d+\.\d+\.\d+)"},
        "zoxide": {"brew": "zoxide", "version_flag": "--version", "version_pattern": r"zoxide (\d+\.\d+\.\d+)"},
        "jq": {"brew": "jq", "version_flag": "--version", "version_pattern": r"jq-(\d+\.\d+)"},
        "ollama": {"brew": "ollama", "version_flag": "--version", "version_pattern": r"ollama version is (\d+\.\d+\.\d+)"},
    }

    def __init__(self):
        """Initialize tool checker."""
        self._cache: Dict[str, ToolInfo] = {}

    def check_tool(self, tool_name: str) -> ToolInfo:
        """Check if a tool is installed and get its version."""
        if tool_name in self._cache:
            return self._cache[tool_name]

        tool_config = self.SIMPLEMINDED_TOOLS.get(tool_name)
        if not tool_config:
            return ToolInfo(name=tool_name, installed=False)

        # Check if command exists
        path = self._get_command_path(tool_name)
        if not path:
            info = ToolInfo(
                name=tool_name,
                installed=False,
                brew_package=tool_config["brew"]
            )
            self._cache[tool_name] = info
            return info

        # Get version
        version = self._get_version(tool_name, tool_config)

        info = ToolInfo(
            name=tool_name,
            installed=True,
            version=version,
            path=path,
            brew_package=tool_config["brew"]
        )
        self._cache[tool_name] = info
        return info

    def _get_command_path(self, command: str) -> Optional[str]:
        """Get the full path to a command."""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Try with 'command -v' as fallback
        try:
            result = subprocess.run(
                ["sh", "-c", f"command -v {command}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _get_version(self, tool_name: str, tool_config: Dict) -> Optional[str]:
        """Get version of a tool."""
        try:
            version_flag = tool_config.get("version_flag", "--version")
            result = subprocess.run(
                [tool_name, version_flag],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                output = result.stdout + result.stderr
                pattern = tool_config.get("version_pattern")
                if pattern:
                    match = re.search(pattern, output)
                    if match:
                        return match.group(1)

                # Fallback: return first line
                return output.split("\n")[0].strip()

        except Exception:
            pass

        return None

    def check_all_tools(self) -> Dict[str, ToolInfo]:
        """Check all simpleminded-shell tools."""
        results = {}
        for tool_name in self.SIMPLEMINDED_TOOLS.keys():
            results[tool_name] = self.check_tool(tool_name)
        return results

    def get_installed_tools(self) -> List[ToolInfo]:
        """Get list of installed tools only."""
        all_tools = self.check_all_tools()
        return [info for info in all_tools.values() if info.installed]

    def get_missing_tools(self) -> List[ToolInfo]:
        """Get list of tools not installed."""
        all_tools = self.check_all_tools()
        return [info for info in all_tools.values() if not info.installed]

    def get_installation_command(self, tool_name: str) -> Optional[str]:
        """Get brew installation command for a tool."""
        tool_config = self.SIMPLEMINDED_TOOLS.get(tool_name)
        if not tool_config:
            return None

        brew_package = tool_config["brew"]
        return f"brew install {brew_package}"

    def get_summary(self) -> Dict:
        """Get summary of tool installation status."""
        all_tools = self.check_all_tools()
        installed = [t for t in all_tools.values() if t.installed]
        missing = [t for t in all_tools.values() if not t.installed]

        return {
            "total_tools": len(all_tools),
            "installed_count": len(installed),
            "missing_count": len(missing),
            "installed": [
                {
                    "name": t.name,
                    "version": t.version,
                    "path": t.path
                }
                for t in installed
            ],
            "missing": [
                {
                    "name": t.name,
                    "install_command": self.get_installation_command(t.name)
                }
                for t in missing
            ]
        }

    def clear_cache(self) -> None:
        """Clear the tool information cache."""
        self._cache.clear()

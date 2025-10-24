"""Shell configuration parser with auto-detection."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import re


class ShellConfigParser:
    """Parse shell configuration files to extract simpleminded-shell setup."""

    MARKER = "SIMPLEMINDED-SHELL-CONFIG"

    CONFIG_PATHS = [
        "~/.zshrc",
        "~/.bashrc",
        "~/.config/zsh/.zshrc",
        "~/.bash_profile",
        "~/.profile",
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize parser with optional config path."""
        self.config_path = self._detect_config(config_path)
        self.config_content = self._read_config()

    def _detect_config(self, provided_path: Optional[str]) -> Optional[Path]:
        """Auto-detect shell config file."""
        if provided_path:
            path = Path(provided_path).expanduser()
            if path.exists():
                return path
            return None

        # Try each known config path
        for config_path in self.CONFIG_PATHS:
            path = Path(config_path).expanduser()
            if path.exists():
                # Check if it has simpleminded-shell config
                try:
                    content = path.read_text()
                    if self.MARKER in content or self._has_simpleminded_aliases(content):
                        return path
                except Exception:
                    continue

        return None

    def _has_simpleminded_aliases(self, content: str) -> bool:
        """Check if content has characteristic simpleminded-shell aliases."""
        indicators = [
            "alias cat='bat",
            "alias find='fd",
            "alias grep='rg",
            "alias ls='eza",
        ]
        return any(indicator in content for indicator in indicators)

    def _read_config(self) -> str:
        """Read configuration file content."""
        if not self.config_path:
            return ""
        try:
            return self.config_path.read_text()
        except Exception:
            return ""

    def get_aliases_output(self) -> Optional[str]:
        """Get output from the 'aliases' command if available."""
        try:
            result = subprocess.run(
                ["aliases"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return None

    def get_raw_config(self) -> str:
        """Get raw configuration content."""
        return self.config_content

    def extract_section(self, start_marker: str, end_marker: Optional[str] = None) -> str:
        """Extract a section between markers."""
        if not self.config_content:
            return ""

        start_idx = self.config_content.find(start_marker)
        if start_idx == -1:
            return ""

        if end_marker:
            end_idx = self.config_content.find(end_marker, start_idx)
            if end_idx == -1:
                return self.config_content[start_idx:]
            return self.config_content[start_idx:end_idx]

        return self.config_content[start_idx:]

    def get_simpleminded_section(self) -> str:
        """Get the simpleminded-shell configuration section."""
        return self.extract_section(f"# {self.MARKER}")

    def is_simpleminded_shell(self) -> bool:
        """Check if this is a simpleminded-shell configuration."""
        return bool(self.config_path and (
            self.MARKER in self.config_content or
            self._has_simpleminded_aliases(self.config_content)
        ))

    def get_config_info(self) -> Dict[str, any]:
        """Get information about the configuration."""
        return {
            "config_path": str(self.config_path) if self.config_path else None,
            "is_simpleminded": self.is_simpleminded_shell(),
            "has_marker": self.MARKER in self.config_content,
            "config_size": len(self.config_content),
        }

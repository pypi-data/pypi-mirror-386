"""Tests for alias detector."""

import pytest
from src.alias_detector import AliasDetector, Alias


SAMPLE_CONFIG = """
# Sample shell config
alias cat='bat --paging=never'
alias grep='rg'
alias find='fd'
alias ls='eza --color=always'
alias ll='eza -la --icons'

# Git aliases
alias g='git'
alias gs='git status'
alias ga='git add'

# Function example
search() {
    rg "$1" | fzf
}
"""


def test_parse_aliases():
    """Test parsing aliases from config."""
    detector = AliasDetector(SAMPLE_CONFIG)
    aliases = detector.parse_aliases()

    assert len(aliases) > 0
    assert "cat" in aliases
    assert aliases["cat"].command == "bat --paging=never"


def test_categorize_aliases():
    """Test alias categorization."""
    detector = AliasDetector(SAMPLE_CONFIG)
    aliases = detector.parse_aliases()

    # File-related aliases
    assert aliases["cat"].category in ["file", "other"]
    assert aliases["ls"].category in ["file", "other"]

    # Git aliases
    assert aliases["gs"].category in ["git", "other"]


def test_get_aliases_by_category():
    """Test getting aliases by category."""
    detector = AliasDetector(SAMPLE_CONFIG)
    git_aliases = detector.get_aliases_by_category("git")

    git_names = [name for name in git_aliases.keys()]
    assert "gs" in git_names or "ga" in git_names


def test_parse_functions():
    """Test parsing shell functions."""
    detector = AliasDetector(SAMPLE_CONFIG)
    functions = detector.parse_functions()

    assert "search" in functions
    assert "rg" in functions["search"].body


def test_get_alias():
    """Test getting specific alias."""
    detector = AliasDetector(SAMPLE_CONFIG)
    alias = detector.get_alias("cat")

    assert alias is not None
    assert alias.name == "cat"
    assert "bat" in alias.command


def test_search_aliases():
    """Test searching aliases."""
    detector = AliasDetector(SAMPLE_CONFIG)
    results = detector.search_aliases("git")

    assert len(results) > 0
    assert any("git" in alias.command for alias in results.values())


def test_to_dict():
    """Test converting to dictionary."""
    detector = AliasDetector(SAMPLE_CONFIG)
    data = detector.to_dict()

    assert "aliases" in data
    assert "functions" in data
    assert "categories" in data
    assert len(data["aliases"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

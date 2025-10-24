"""Tests for command translator."""

import pytest
from src.command_translator import CommandTranslator, Translation


def test_translate_grep_basic():
    """Test basic grep translation."""
    translator = CommandTranslator()
    result = translator.translate('grep -r "pattern" .')

    assert result is not None
    assert result.modern == 'rg "pattern"'
    assert result.tool == "ripgrep"


def test_translate_find_basic():
    """Test basic find translation."""
    translator = CommandTranslator()
    result = translator.translate('find . -name "*.py"')

    assert result is not None
    assert "fd" in result.modern
    assert result.tool == "fd"


def test_translate_find_extension():
    """Test find by extension translation."""
    translator = CommandTranslator()
    result = translator.translate('find . -type f -name "*.js"')

    assert result is not None
    assert "fd -e js" in result.modern or "fd" in result.modern
    assert result.tool == "fd"


def test_translate_ls():
    """Test ls translation."""
    translator = CommandTranslator()
    result = translator.translate('ls -la')

    assert result is not None
    assert result.modern == 'll'
    assert result.tool == "eza"


def test_translate_unknown_command():
    """Test that unknown commands return None."""
    translator = CommandTranslator()
    result = translator.translate('unknown command')

    assert result is None


def test_get_examples():
    """Test getting translation examples."""
    translator = CommandTranslator()
    examples = translator.get_examples()

    assert len(examples) > 0
    assert any("grep" in ex["traditional"] for ex in examples)
    assert any("find" in ex["traditional"] for ex in examples)


def test_explain_alias():
    """Test alias explanation."""
    translator = CommandTranslator()
    explanation = translator.explain_alias("cat", "bat --paging=never")

    assert "bat" in explanation
    assert "syntax highlighting" in explanation.lower()


def test_get_tool_benefits():
    """Test getting tool benefits."""
    translator = CommandTranslator()
    benefits = translator.get_tool_benefits("rg")

    assert len(benefits) > 0
    assert any("fast" in b.lower() for b in benefits)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

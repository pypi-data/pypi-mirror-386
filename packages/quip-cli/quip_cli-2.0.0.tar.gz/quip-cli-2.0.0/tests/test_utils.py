"""Unit tests for utility functions in quip/__init__.py"""
import pytest
from quip import (
    cprint,
    color_text,
    yes_or_no,
    choose_one,
    resolve_quiet_mode,
    set_quiet_mode,
)


class TestColorPrint:
    """Tests for color printing utilities."""
    
    def test_cprint_basic(self, capsys):
        """Test basic color printing."""
        cprint("Test message", "red")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
    
    def test_cprint_empty_string(self, capsys):
        """Test that empty strings don't print."""
        cprint("", "red")
        cprint("   ", "blue")
        captured = capsys.readouterr()
        assert captured.out == ""
    
    def test_color_text(self):
        """Test color text formatting."""
        result = color_text("Test", "red")
        assert "Test" in result
        assert len(result) > 4  # Should include ANSI codes


class TestYesOrNo:
    """Tests for yes_or_no function."""
    
    def test_yes_input(self, monkeypatch):
        """Test 'yes' input."""
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        result = yes_or_no("Test question?")
        assert result is True
    
    def test_no_input(self, monkeypatch):
        """Test 'no' input."""
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        result = yes_or_no("Test question?")
        assert result is False
    
    def test_yes_full_word(self, monkeypatch):
        """Test 'yes' full word input."""
        monkeypatch.setattr('builtins.input', lambda _: 'yes')
        result = yes_or_no("Test question?")
        assert result is True
    
    def test_no_full_word(self, monkeypatch):
        """Test 'no' full word input."""
        monkeypatch.setattr('builtins.input', lambda _: 'no')
        result = yes_or_no("Test question?")
        assert result is False
    
    def test_default_true(self, monkeypatch):
        """Test default=True with empty input."""
        monkeypatch.setattr('builtins.input', lambda _: '')
        result = yes_or_no("Test question?", default=True)
        assert result is True
    
    def test_default_false(self, monkeypatch):
        """Test default=False with empty input."""
        monkeypatch.setattr('builtins.input', lambda _: '')
        result = yes_or_no("Test question?", default=False)
        assert result is False
    
    def test_invalid_then_valid(self, monkeypatch):
        """Test invalid input followed by valid input."""
        inputs = iter(['invalid', 'y'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = yes_or_no("Test question?")
        assert result is True
    
    def test_with_color(self, monkeypatch):
        """Test with color parameter."""
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        result = yes_or_no("Test question?", color="red")
        assert result is True


class TestChooseOne:
    """Tests for choose_one function."""
    
    def test_choose_first_option(self, monkeypatch):
        """Test choosing the first option."""
        values = [("Option 1", 1), ("Option 2", 2), ("Option 3", 3)]
        monkeypatch.setattr('builtins.input', lambda _: '1')
        result = choose_one(values)
        assert result == ("Option 1", 1)
    
    def test_choose_last_option(self, monkeypatch):
        """Test choosing the last option."""
        values = [("Option 1", 1), ("Option 2", 2), ("Option 3", 3)]
        monkeypatch.setattr('builtins.input', lambda _: '3')
        result = choose_one(values)
        assert result == ("Option 3", 3)
    
    def test_with_default(self, monkeypatch):
        """Test with default value."""
        values = [("Option 1", 1), ("Option 2", 2), ("Option 3", 3)]
        monkeypatch.setattr('builtins.input', lambda _: '')
        result = choose_one(values, default="Option 2")
        assert result == ("Option 2", 2)
    
    def test_invalid_then_valid(self, monkeypatch):
        """Test invalid input followed by valid input."""
        values = [("Option 1", 1), ("Option 2", 2)]
        inputs = iter(['5', '1'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = choose_one(values)
        assert result == ("Option 1", 1)
    
    def test_with_title(self, monkeypatch, capsys):
        """Test with title parameter."""
        values = [("Option 1", 1), ("Option 2", 2)]
        monkeypatch.setattr('builtins.input', lambda _: '1')
        result = choose_one(values, title="Select an option")
        captured = capsys.readouterr()
        assert "Select an option" in captured.out
        assert result == ("Option 1", 1)
    
    def test_sorting(self, monkeypatch):
        """Test that options are sorted."""
        values = [("Zebra", 3), ("Alpha", 1), ("Beta", 2)]
        monkeypatch.setattr('builtins.input', lambda _: '1')
        result = choose_one(values, sort=True)
        # First sorted option should be Alpha
        assert result == ("Alpha", 1)


class TestResolveQuietMode:
    """Tests for resolve_quiet_mode helper."""

    def teardown_method(self):
        set_quiet_mode(False)

    def test_cli_flag_wins(self):
        assert resolve_quiet_mode(cli_quiet=True) is True

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("QUIP_QUIET", "1")
        assert resolve_quiet_mode(cli_quiet=False) is True

    def test_env_disables_even_with_config(self, monkeypatch, tmp_path):
        config = tmp_path / ".uip_config.yml"
        config.write_text("defaults:\n  quiet: true\n")
        monkeypatch.setenv("QUIP_QUIET", "0")
        assert resolve_quiet_mode(cli_quiet=False, config_path=str(config)) is False

    def test_config_sets_quiet(self, tmp_path):
        config = tmp_path / ".uip_config.yml"
        config.write_text("defaults:\n  quiet: yes\n")
        assert resolve_quiet_mode(cli_quiet=False, config_path=str(config)) is True

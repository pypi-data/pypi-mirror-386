"""
Unit tests for utils module.
"""

import os
from pathlib import Path
from datetime import datetime
import pytest

from obsidian_base_logger.utils import (
    is_binary,
    extract_iteration,
    get_next_iteration,
    get_output_path,
    resolve_vault_path,
    sanitize_command_name,
)


class TestIsBinary:
    """Tests for binary content detection."""

    def test_null_bytes_is_binary(self):
        """Null bytes indicate binary content."""
        data = b'hello\x00world'
        assert is_binary(data) is True

    def test_high_nonprintable_ratio_is_binary(self):
        """High ratio of non-printable characters indicates binary."""
        # Create data with >30% non-printable
        data = b'\x01\x02\x03\x04\x05' * 200 + b'text'
        assert is_binary(data) is True

    def test_printable_text_not_binary(self):
        """Normal printable text is not binary."""
        data = b'This is normal text\nWith newlines\tand tabs'
        assert is_binary(data) is False

    def test_empty_data_not_binary(self):
        """Empty data is not considered binary."""
        assert is_binary(b'') is False

    def test_whitespace_allowed(self):
        """Common whitespace (tab, newline, CR) not counted as non-printable."""
        data = b'Line 1\nLine 2\nLine 3\n'
        assert is_binary(data) is False


class TestExtractIteration:
    """Tests for iteration number extraction."""

    def test_extract_valid_iteration(self):
        """Extract iteration from valid filename."""
        assert extract_iteration('2025-10-24-npm-3.md') == 3
        assert extract_iteration('2025-10-24-python-1.md') == 1
        assert extract_iteration('2025-10-24-bash-42.md') == 42

    def test_no_iteration_returns_zero(self):
        """Missing iteration returns 0."""
        assert extract_iteration('2025-10-24-npm.md') == 0
        assert extract_iteration('random.md') == 0

    def test_malformed_filename_returns_zero(self):
        """Malformed filename returns 0."""
        assert extract_iteration('not-a-match.txt') == 0
        assert extract_iteration('') == 0


class TestGetNextIteration:
    """Tests for iteration counter logic."""

    def test_no_existing_files(self, tmp_path):
        """With no existing files, returns 1."""
        vault = tmp_path / "vault"
        vault.mkdir()
        iteration = get_next_iteration(vault, "testhost", "2025-10-24", "npm")
        assert iteration == 1

    def test_with_existing_files(self, tmp_path):
        """With existing files, returns max + 1."""
        vault = tmp_path / "vault"
        log_dir = vault / "logs" / "testhost"
        log_dir.mkdir(parents=True)

        # Create existing files
        (log_dir / "2025-10-24-npm-1.md").touch()
        (log_dir / "2025-10-24-npm-2.md").touch()
        (log_dir / "2025-10-24-npm-3.md").touch()

        iteration = get_next_iteration(vault, "testhost", "2025-10-24", "npm")
        assert iteration == 4

    def test_non_sequential_iterations(self, tmp_path):
        """With gaps in iterations, returns max + 1."""
        vault = tmp_path / "vault"
        log_dir = vault / "logs" / "testhost"
        log_dir.mkdir(parents=True)

        # Create files with gaps
        (log_dir / "2025-10-24-npm-1.md").touch()
        (log_dir / "2025-10-24-npm-5.md").touch()
        (log_dir / "2025-10-24-npm-3.md").touch()

        iteration = get_next_iteration(vault, "testhost", "2025-10-24", "npm")
        assert iteration == 6

    def test_different_commands_separate(self, tmp_path):
        """Different commands have separate iteration counters."""
        vault = tmp_path / "vault"
        log_dir = vault / "logs" / "testhost"
        log_dir.mkdir(parents=True)

        # Create files for different commands
        (log_dir / "2025-10-24-npm-1.md").touch()
        (log_dir / "2025-10-24-npm-2.md").touch()
        (log_dir / "2025-10-24-python-1.md").touch()

        npm_iteration = get_next_iteration(vault, "testhost", "2025-10-24", "npm")
        python_iteration = get_next_iteration(vault, "testhost", "2025-10-24", "python")

        assert npm_iteration == 3
        assert python_iteration == 2


class TestGetOutputPath:
    """Tests for output path construction."""

    def test_path_format(self, tmp_path):
        """Verify correct path format."""
        vault = tmp_path / "vault"
        timestamp = datetime(2025, 10, 24, 10, 30, 0)

        path = get_output_path(vault, "myhost", timestamp, "npm")

        expected = vault / "logs" / "myhost" / "2025-10-24-npm-1.md"
        assert path == expected

    def test_creates_directory(self, tmp_path):
        """Ensure directory is created."""
        vault = tmp_path / "vault"
        timestamp = datetime(2025, 10, 24, 10, 30, 0)

        path = get_output_path(vault, "myhost", timestamp, "npm")

        assert path.parent.exists()
        assert path.parent.is_dir()

    def test_iteration_increments(self, tmp_path):
        """Multiple calls increment iteration."""
        vault = tmp_path / "vault"
        timestamp = datetime(2025, 10, 24, 10, 30, 0)

        path1 = get_output_path(vault, "myhost", timestamp, "npm")
        path1.touch()  # Create the file

        path2 = get_output_path(vault, "myhost", timestamp, "npm")

        assert path1.name == "2025-10-24-npm-1.md"
        assert path2.name == "2025-10-24-npm-2.md"


class TestResolveVaultPath:
    """Tests for vault path resolution."""

    def test_cli_option_takes_precedence(self, tmp_path, monkeypatch):
        """CLI option has highest priority."""
        cli_path = tmp_path / "cli_vault"
        env_path = tmp_path / "env_vault"

        monkeypatch.setenv('OBSIDIAN_VAULT', str(env_path))

        result = resolve_vault_path(str(cli_path))
        assert result == cli_path

    def test_environment_variable_second(self, tmp_path, monkeypatch):
        """Environment variable used if no CLI option."""
        env_path = tmp_path / "env_vault"
        monkeypatch.setenv('OBSIDIAN_VAULT', str(env_path))

        result = resolve_vault_path(None)
        assert result == env_path

    def test_default_fallback(self, monkeypatch):
        """Default path used if no CLI option or env var."""
        monkeypatch.delenv('OBSIDIAN_VAULT', raising=False)

        result = resolve_vault_path(None)
        expected = Path.home() / ".local" / "obsidian" / "vault"
        assert result == expected

    def test_expands_home_directory(self, monkeypatch):
        """Tilde is expanded to home directory."""
        result = resolve_vault_path("~/my_vault")
        assert str(result).startswith(str(Path.home()))
        assert "~" not in str(result)


class TestSanitizeCommandName:
    """Tests for command name sanitization."""

    def test_simple_command(self):
        """Simple command unchanged."""
        assert sanitize_command_name("npm") == "npm"
        assert sanitize_command_name("python") == "python"

    def test_removes_path(self):
        """Path components removed."""
        assert sanitize_command_name("/usr/bin/python") == "python"
        assert sanitize_command_name("./my-script.sh") == "my-script_sh"

    def test_replaces_special_chars(self):
        """Special characters replaced with underscore."""
        assert sanitize_command_name("my script") == "my_script"
        assert sanitize_command_name("test@v1.0") == "test_v1_0"

    def test_preserves_allowed_chars(self):
        """Alphanumeric, dash, underscore preserved."""
        assert sanitize_command_name("my-command_v2") == "my-command_v2"

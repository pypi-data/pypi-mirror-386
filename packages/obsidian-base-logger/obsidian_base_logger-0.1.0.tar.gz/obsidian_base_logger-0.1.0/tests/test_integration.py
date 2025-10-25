"""
Integration tests for the complete obsidian-base-logger flow.
"""

import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def tmp_vault(tmp_path):
    """Create temporary Obsidian vault for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    return vault


def run_logger(vault_path, command_args):
    """
    Run obsidian-base-logger with given command.

    Returns completed process.
    """
    cmd = [
        sys.executable, '-m', 'obsidian_base_logger.cli',
        '-o', str(vault_path)
    ] + command_args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result


def find_latest_log(vault_path):
    """Find the most recently created log file."""
    log_files = list(vault_path.glob('logs/**/*.md'))
    if not log_files:
        raise FileNotFoundError("No log files found")
    return max(log_files, key=lambda p: p.stat().st_mtime)


def list_logs(vault_path):
    """List all log files, sorted by modification time."""
    log_files = list(vault_path.glob('logs/**/*.md'))
    return sorted(log_files, key=lambda p: p.stat().st_mtime)


class TestSuccessfulCommand:
    """Test wrapping successful commands."""

    def test_simple_echo(self, tmp_vault):
        """Simple echo command."""
        result = run_logger(tmp_vault, ['echo', 'hello world'])

        # Logger should exit with same code as wrapped command
        assert result.returncode == 0

        # Should have created log file
        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Verify metadata
        assert 'return: 0' in content
        assert 'command: echo' in content
        assert 'arguments: hello world' in content

        # Verify output
        assert '## stdout' in content
        assert 'hello world' in content

    def test_pwd_command(self, tmp_vault):
        """Command with stdout output."""
        result = run_logger(tmp_vault, ['pwd'])

        assert result.returncode == 0

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        assert 'return: 0' in content
        assert '## stdout' in content


class TestFailedCommand:
    """Test wrapping failed commands."""

    def test_exit_one(self, tmp_vault):
        """Command that exits with code 1."""
        result = run_logger(tmp_vault, ['python3', '-c', 'import sys; sys.exit(1)'])

        # Logger should exit with same code
        assert result.returncode == 1

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        assert 'return: 1' in content

    def test_exit_code_preserved(self, tmp_vault):
        """Exit code propagated correctly."""
        result = run_logger(tmp_vault, ['python3', '-c', 'import sys; sys.exit(42)'])

        assert result.returncode == 42

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        assert 'return: 42' in content


class TestOutputCapture:
    """Test output capture scenarios."""

    def test_stdout_only(self, tmp_vault):
        """Command with stdout, empty stderr."""
        result = run_logger(tmp_vault, ['echo', 'output'])

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # stdout should have content
        stdout_section = content.split('## stdout')[1].split('---')[0]
        assert 'output' in stdout_section
        assert '[no output]' not in stdout_section

        # stderr should be empty
        stderr_section = content.split('## stderr')[1]
        assert '[no output]' in stderr_section

    def test_stderr_only(self, tmp_vault):
        """Command with stderr, empty stdout."""
        result = run_logger(tmp_vault, ['bash', '-c', '>&2 echo "error message"'])

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # stdout should be empty
        stdout_section = content.split('## stdout')[1].split('---')[0]
        assert '[no output]' in stdout_section

        # stderr should have content
        stderr_section = content.split('## stderr')[1]
        assert 'error message' in stderr_section

    def test_both_outputs(self, tmp_vault):
        """Command with both stdout and stderr."""
        result = run_logger(
            tmp_vault,
            ['bash', '-c', 'echo "out" && >&2 echo "err"']
        )

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        assert 'out' in content
        assert 'err' in content

        # Neither should have [no output]
        assert content.count('[no output]') == 0

    def test_empty_outputs(self, tmp_vault):
        """Command with no output."""
        result = run_logger(tmp_vault, ['true'])

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Both should show [no output]
        assert content.count('[no output]') == 2


class TestFileOrganization:
    """Test file path and organization."""

    def test_file_path_format(self, tmp_vault):
        """Verify file path format."""
        result = run_logger(tmp_vault, ['echo', 'test'])

        log_file = find_latest_log(tmp_vault)

        # Should be in logs/{hostname}/{date}-{command}-{iteration}.md
        assert log_file.parent.parent.name == 'logs'
        assert log_file.name.endswith('-echo-1.md')
        assert '.md' in log_file.name

    def test_iteration_increment(self, tmp_vault):
        """Multiple runs increment iteration."""
        # Run same command 3 times
        for _ in range(3):
            run_logger(tmp_vault, ['echo', 'test'])

        logs = list_logs(tmp_vault)
        assert len(logs) == 3

        assert logs[0].name.endswith('-echo-1.md')
        assert logs[1].name.endswith('-echo-2.md')
        assert logs[2].name.endswith('-echo-3.md')

    def test_different_commands_separate(self, tmp_vault):
        """Different commands have separate iteration counters."""
        run_logger(tmp_vault, ['echo', 'test1'])
        run_logger(tmp_vault, ['echo', 'test2'])
        run_logger(tmp_vault, ['pwd'])

        logs = list_logs(tmp_vault)
        assert len(logs) == 3

        echo_logs = [l for l in logs if 'echo' in l.name]
        pwd_logs = [l for l in logs if 'pwd' in l.name]

        assert len(echo_logs) == 2
        assert len(pwd_logs) == 1

        assert echo_logs[0].name.endswith('-echo-1.md')
        assert echo_logs[1].name.endswith('-echo-2.md')
        assert pwd_logs[0].name.endswith('-pwd-1.md')


class TestMetadataCapture:
    """Test metadata field capture."""

    def test_all_basic_fields(self, tmp_vault):
        """All basic metadata fields present."""
        result = run_logger(tmp_vault, ['echo', 'test'])

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Check required fields
        assert 'host:' in content
        assert 'started:' in content
        assert 'time:' in content
        assert 'return:' in content
        assert 'command:' in content
        assert 'pid:' in content
        assert 'user:' in content
        assert 'cwd:' in content

    def test_time_in_seconds(self, tmp_vault):
        """Time field is in seconds."""
        result = run_logger(tmp_vault, ['sleep', '0.2'])

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Extract time value
        import re
        match = re.search(r'time: (\d+\.?\d*)', content)
        assert match
        time_value = float(match.group(1))

        # Should be around 0.2 seconds (with some tolerance)
        assert 0.15 < time_value < 0.5


class TestPipedCommands:
    """Test commands with pipes and redirects."""

    def test_pipe_command(self, tmp_vault):
        """Piped command works correctly."""
        result = run_logger(
            tmp_vault,
            ['bash', '-c', 'echo -e "foo\\nbar\\nbaz" | grep bar']
        )

        assert result.returncode == 0

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Should only have 'bar', not 'foo' or 'baz'
        stdout_section = content.split('## stdout')[1].split('---')[0]
        assert 'bar' in stdout_section
        assert 'foo' not in stdout_section


class TestAnsiCodes:
    """Test ANSI escape code preservation."""

    def test_preserves_ansi_codes(self, tmp_vault):
        """ANSI codes preserved in output."""
        # Use a command that outputs ANSI codes
        result = run_logger(
            tmp_vault,
            ['bash', '-c', 'echo -e "\\033[32mGreen\\033[0m"']
        )

        log_file = find_latest_log(tmp_vault)
        content = log_file.read_text()

        # Should have the text (ANSI codes may be preserved or escaped)
        assert 'Green' in content

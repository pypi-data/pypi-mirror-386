"""
Unit tests for executor module.
"""

import os
import pytest
from obsidian_base_logger.executor import execute_command, ExecutionResult


class TestExecuteCommand:
    """Tests for command execution."""

    def test_successful_command(self):
        """Execute simple successful command."""
        result = execute_command(['echo', 'hello'])

        assert result.return_code == 0
        assert b'hello' in result.stdout_bytes
        assert result.metadata['return'] == 0
        assert result.metadata['command'] == 'echo'

    def test_failed_command(self):
        """Execute command that exits with error."""
        result = execute_command(['python3', '-c', 'import sys; sys.exit(1)'])

        assert result.return_code == 1
        assert result.metadata['return'] == 1

    def test_captures_stdout(self):
        """Stdout captured correctly."""
        result = execute_command(['echo', 'test output'])

        assert b'test output' in result.stdout_bytes

    def test_captures_stderr(self):
        """Stderr captured correctly."""
        result = execute_command(['bash', '-c', '>&2 echo "error message"'])

        assert b'error message' in result.stderr_bytes

    def test_both_outputs(self):
        """Both stdout and stderr captured."""
        result = execute_command(['bash', '-c', 'echo "out" && >&2 echo "err"'])

        assert b'out' in result.stdout_bytes
        assert b'err' in result.stderr_bytes

    def test_metadata_host(self):
        """Hostname captured in metadata."""
        result = execute_command(['echo', 'test'])

        assert 'host' in result.metadata
        assert isinstance(result.metadata['host'], str)
        assert len(result.metadata['host']) > 0

    def test_metadata_timestamps(self):
        """Start time captured."""
        result = execute_command(['echo', 'test'])

        assert 'started' in result.metadata
        assert result.metadata['started'] is not None

    def test_metadata_execution_time(self):
        """Execution time calculated in seconds."""
        result = execute_command(['sleep', '0.1'])

        assert 'time' in result.metadata
        assert result.metadata['time'] >= 0.1
        # Should be in seconds
        assert result.metadata['time'] < 10

    def test_metadata_command_and_args(self):
        """Command and arguments separated."""
        result = execute_command(['npm', 'test', '--verbose'])

        assert result.metadata['command'] == 'npm'
        assert result.metadata['arguments'] == 'test --verbose'

    def test_metadata_single_command_no_args(self):
        """Single command with no arguments."""
        result = execute_command(['pwd'])

        assert result.metadata['command'] == 'pwd'
        assert result.metadata['arguments'] == ''

    def test_metadata_pid(self):
        """Process ID captured."""
        result = execute_command(['echo', 'test'])

        assert 'pid' in result.metadata
        assert isinstance(result.metadata['pid'], int)
        assert result.metadata['pid'] > 0

    def test_metadata_user(self):
        """Username captured."""
        result = execute_command(['echo', 'test'])

        assert 'user' in result.metadata
        assert isinstance(result.metadata['user'], str)
        # Should not be empty or 'unknown' in normal circumstances
        assert len(result.metadata['user']) > 0

    def test_metadata_cwd(self):
        """Working directory captured."""
        result = execute_command(['echo', 'test'])

        assert 'cwd' in result.metadata
        assert result.metadata['cwd'] == os.getcwd()

    def test_cpu_times_if_available(self):
        """CPU times captured if available."""
        # Run a command that uses some CPU
        result = execute_command(['python3', '-c', 'sum(range(1000))'])

        # CPU times might not be available on all platforms
        # Just check they're present and reasonable if they exist
        if 'cpu_time_user_ms' in result.metadata:
            assert isinstance(result.metadata['cpu_time_user_ms'], int)
            assert result.metadata['cpu_time_user_ms'] >= 0

        if 'cpu_time_system_ms' in result.metadata:
            assert isinstance(result.metadata['cpu_time_system_ms'], int)
            assert result.metadata['cpu_time_system_ms'] >= 0

    def test_memory_if_available(self):
        """Memory usage captured if available."""
        result = execute_command(['echo', 'test'])

        # Memory metrics might not be available on all platforms
        if 'memory_peak_mb' in result.metadata:
            assert isinstance(result.metadata['memory_peak_mb'], (int, float))
            assert result.metadata['memory_peak_mb'] > 0

    def test_piped_command(self):
        """Commands with pipes work."""
        result = execute_command(['bash', '-c', 'echo -e "foo\\nbar\\nbaz" | grep bar'])

        assert b'bar' in result.stdout_bytes
        assert b'foo' not in result.stdout_bytes
        assert result.return_code == 0

    def test_empty_output(self):
        """Commands with no output."""
        result = execute_command(['true'])

        assert result.stdout_bytes == b''
        assert result.stderr_bytes == b''
        assert result.return_code == 0


class TestExecutionResult:
    """Tests for ExecutionResult class."""

    def test_initialization(self):
        """ExecutionResult initializes correctly."""
        result = ExecutionResult()

        assert isinstance(result.metadata, dict)
        assert result.stdout_bytes == b''
        assert result.stderr_bytes == b''
        assert result.return_code == 0

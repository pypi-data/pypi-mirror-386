"""
Unit tests for formatter module.
"""

from datetime import datetime, timezone
import pytest

from obsidian_base_logger.formatter import (
    format_yaml_value,
    format_properties,
    truncate_output,
    format_output_section,
    format_markdown_document,
)


class TestFormatYamlValue:
    """Tests for YAML value formatting."""

    def test_format_none(self):
        """None formatted as null."""
        assert format_yaml_value(None) == "null"

    def test_format_bool(self):
        """Boolean values formatted correctly."""
        assert format_yaml_value(True) == "true"
        assert format_yaml_value(False) == "false"

    def test_format_numbers(self):
        """Numbers formatted as strings."""
        assert format_yaml_value(42) == "42"
        assert format_yaml_value(3.14) == "3.14"

    def test_format_datetime(self):
        """Datetime formatted as ISO 8601."""
        dt = datetime(2025, 10, 24, 10, 30, 15, tzinfo=timezone.utc)
        result = format_yaml_value(dt)
        assert "2025-10-24" in result
        assert "10:30:15" in result

    def test_format_simple_string(self):
        """Simple strings pass through."""
        assert format_yaml_value("hello") == "hello"

    def test_format_complex_string(self):
        """Complex strings are quoted."""
        assert format_yaml_value("hello: world") == '"hello: world"'
        assert format_yaml_value("multi\nline") == '"multi\\nline"'


class TestFormatProperties:
    """Tests for YAML frontmatter formatting."""

    def test_basic_metadata(self):
        """Basic metadata formatted correctly."""
        metadata = {
            'host': 'testhost',
            'started': datetime(2025, 10, 24, 10, 30, 0, tzinfo=timezone.utc),
            'time': 2.456,
            'return': 0,
            'command': 'npm',
            'arguments': 'test',
        }

        result = format_properties(metadata)

        assert result.startswith('---')
        assert result.endswith('---')
        assert 'host: testhost' in result
        assert 'time: 2.456' in result
        assert 'return: 0' in result
        assert 'command: npm' in result
        assert 'arguments: test' in result

    def test_complete_metadata(self):
        """All metadata fields formatted."""
        metadata = {
            'host': 'myserver',
            'started': datetime(2025, 10, 24, 10, 30, 0, tzinfo=timezone.utc),
            'time': 1.234,
            'return': 0,
            'command': 'python',
            'arguments': 'test.py',
            'pid': 12345,
            'user': 'alice',
            'cwd': '/home/alice',
            'cpu_time_user_ms': 850,
            'cpu_time_system_ms': 150,
            'memory_peak_mb': 45.2,
            'io_read_bytes': 1024,
            'io_write_bytes': 512,
        }

        result = format_properties(metadata)

        assert 'pid: 12345' in result
        assert 'user: alice' in result
        assert 'cpu_time_user_ms: 850' in result
        assert 'cpu_time_system_ms: 150' in result
        assert 'memory_peak_mb: 45.2' in result

    def test_property_order(self):
        """Properties appear in defined order."""
        metadata = {
            'return': 0,
            'host': 'testhost',
            'time': 1.0,
            'command': 'test',
        }

        result = format_properties(metadata)
        lines = result.split('\n')

        # host should come before time, time before return, return before command
        host_idx = next(i for i, l in enumerate(lines) if l.startswith('host:'))
        time_idx = next(i for i, l in enumerate(lines) if l.startswith('time:'))
        return_idx = next(i for i, l in enumerate(lines) if l.startswith('return:'))
        command_idx = next(i for i, l in enumerate(lines) if l.startswith('command:'))

        assert host_idx < time_idx < return_idx < command_idx


class TestTruncateOutput:
    """Tests for output truncation."""

    def test_short_output_unchanged(self):
        """Output under limit unchanged."""
        output = '\n'.join([f"Line {i}" for i in range(100)])
        result = truncate_output(output, max_lines=10000)
        assert result == output

    def test_truncate_long_output(self):
        """Long output truncated at limit."""
        lines = [f"Line {i}" for i in range(15000)]
        output = '\n'.join(lines)

        result = truncate_output(output, max_lines=10000)

        # Should have truncation message
        assert "Output truncated" in result
        assert "15,000 total lines" in result or "15000 total lines" in result
        assert "showing first 10,000" in result or "showing first 10000" in result

        # Should only have first 10000 lines
        result_lines = result.split('\n')
        # +1 for empty line, +1 for truncation message
        assert len(result_lines) <= 10002

    def test_exact_limit(self):
        """Output at exact limit not truncated."""
        output = '\n'.join([f"Line {i}" for i in range(10000)])
        result = truncate_output(output, max_lines=10000)
        assert "truncated" not in result.lower()


class TestFormatOutputSection:
    """Tests for output section formatting."""

    def test_empty_output(self):
        """Empty output shows [no output]."""
        result = format_output_section(b'', 'stdout')
        assert '## stdout' in result
        assert '[no output]' in result

    def test_whitespace_only_output(self):
        """Whitespace-only output treated as empty."""
        result = format_output_section(b'   \n  \n  ', 'stderr')
        assert '[no output]' in result

    def test_binary_output(self):
        """Binary output shows [binary output]."""
        result = format_output_section(b'\x00\x01\x02', 'stdout', is_binary=True)
        assert '[binary output]' in result

    def test_normal_output(self):
        """Normal output included directly."""
        output = b'Test output\nLine 2'
        result = format_output_section(output, 'stdout')

        assert '## stdout' in result
        assert 'Test output' in result
        assert 'Line 2' in result

    def test_preserves_ansi_codes(self):
        """ANSI escape codes preserved."""
        output = b'\x1b[32mGreen text\x1b[0m'
        result = format_output_section(output, 'stdout')

        # ANSI codes should be preserved (may show as unicode or escaped)
        assert 'Green text' in result


class TestFormatMarkdownDocument:
    """Tests for complete document formatting."""

    def test_complete_document_structure(self):
        """Document has all required sections."""
        metadata = {
            'host': 'testhost',
            'started': datetime(2025, 10, 24, 10, 30, 0, tzinfo=timezone.utc),
            'time': 1.5,
            'return': 0,
            'command': 'echo',
            'arguments': 'hello',
        }
        stdout = b'hello\n'
        stderr = b''

        result = format_markdown_document(metadata, stdout, stderr)

        # Should have frontmatter
        assert result.startswith('---')
        assert 'host: testhost' in result

        # Should have stdout section
        assert '## stdout' in result
        assert 'hello' in result

        # Should have separator
        assert '\n---\n' in result

        # Should have stderr section
        assert '## stderr' in result

    def test_both_empty_outputs(self):
        """Both empty outputs handled."""
        metadata = {
            'host': 'test',
            'started': datetime.now(timezone.utc),
            'time': 0.1,
            'return': 0,
            'command': 'true',
            'arguments': '',
        }

        result = format_markdown_document(metadata, b'', b'')

        assert result.count('[no output]') == 2

    def test_binary_outputs(self):
        """Binary outputs marked correctly."""
        metadata = {
            'host': 'test',
            'started': datetime.now(timezone.utc),
            'time': 0.1,
            'return': 0,
            'command': 'cat',
            'arguments': '/bin/ls',
        }

        result = format_markdown_document(
            metadata,
            b'\x00\x01\x02',
            b'',
            stdout_is_binary=True,
            stderr_is_binary=False
        )

        assert result.count('[binary output]') == 1
        assert result.count('[no output]') == 1

    def test_section_order(self):
        """Sections appear in correct order."""
        metadata = {
            'host': 'test',
            'started': datetime.now(timezone.utc),
            'time': 0.5,
            'return': 0,
            'command': 'test',
            'arguments': '',
        }
        stdout = b'stdout content'
        stderr = b'stderr content'

        result = format_markdown_document(metadata, stdout, stderr)

        # Find positions
        frontmatter_start = result.find('---')
        frontmatter_end = result.find('---', frontmatter_start + 3)
        stdout_pos = result.find('## stdout')
        separator_pos = result.find('\n---\n', frontmatter_end + 3)
        stderr_pos = result.find('## stderr')

        # Verify order
        assert frontmatter_start < frontmatter_end
        assert frontmatter_end < stdout_pos
        assert stdout_pos < separator_pos
        assert separator_pos < stderr_pos

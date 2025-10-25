"""
Markdown and YAML formatting for Obsidian output.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def format_yaml_value(value: Any) -> str:
    """
    Format a value for YAML output.

    Args:
        value: Value to format

    Returns:
        YAML-formatted string
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        # ISO 8601 format with timezone
        return value.isoformat()
    elif isinstance(value, str):
        # Check if string needs quoting (contains special chars, newlines, etc.)
        if '\n' in value or ':' in value or value.startswith(('-', '[', '{', '>', '|')):
            # Escape special characters and quote the string
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            return f'"{escaped}"'
        return value
    else:
        return str(value)


def format_properties(metadata: Dict[str, Any]) -> str:
    """
    Format metadata dictionary as YAML frontmatter (Obsidian properties).

    Args:
        metadata: Dictionary of metadata fields

    Returns:
        YAML frontmatter string with --- delimiters
    """
    lines = ["---"]

    # Define property order for consistent output
    property_order = [
        "host",
        "started",
        "time",
        "return",
        "command",
        "arguments",
        "pid",
        "user",
        "cwd",
        "cpu_time_user_ms",
        "cpu_time_system_ms",
        "memory_peak_mb",
        "io_read_bytes",
        "io_write_bytes",
    ]

    # Add properties in order (skip missing ones)
    for key in property_order:
        if key in metadata:
            value = format_yaml_value(metadata[key])
            lines.append(f"{key}: {value}")

    # Add any additional properties not in the standard order
    for key, value in metadata.items():
        if key not in property_order:
            formatted_value = format_yaml_value(value)
            lines.append(f"{key}: {formatted_value}")

    lines.append("---")
    return "\n".join(lines)


def truncate_output(output: str, max_lines: int = 10000) -> str:
    """
    Truncate output if it exceeds maximum line count.

    Args:
        output: Output string
        max_lines: Maximum number of lines to keep

    Returns:
        Truncated output with informative message if truncated
    """
    lines = output.splitlines()

    if len(lines) <= max_lines:
        return output

    # Keep first max_lines
    truncated_lines = lines[:max_lines]
    truncated = '\n'.join(truncated_lines)

    # Add truncation message
    total_lines = len(lines)
    truncated += f"\n\n[Output truncated: {total_lines:,} total lines, showing first {max_lines:,}]"

    return truncated


def format_output_section(
    output_bytes: bytes,
    section_name: str,
    is_binary: bool = False
) -> str:
    """
    Format output section (stdout or stderr) for Markdown.

    Args:
        output_bytes: Raw output bytes
        section_name: Section name (e.g., "stdout", "stderr")
        is_binary: Whether output is binary

    Returns:
        Formatted Markdown section
    """
    lines = [f"## {section_name}", ""]

    if is_binary:
        # Binary output - don't include actual content
        lines.append("[binary output]")
    elif not output_bytes or len(output_bytes.strip()) == 0:
        # Empty output
        lines.append("[no output]")
    else:
        # Normal output - decode and preserve ANSI codes
        try:
            output_text = output_bytes.decode('utf-8', errors='replace')
        except Exception:
            output_text = "[decoding error]"

        # Truncate if needed
        output_text = truncate_output(output_text)

        lines.append(output_text)

    return "\n".join(lines)


def format_markdown_document(
    metadata: Dict[str, Any],
    stdout_bytes: bytes,
    stderr_bytes: bytes,
    stdout_is_binary: bool = False,
    stderr_is_binary: bool = False
) -> str:
    """
    Format complete Markdown document with YAML frontmatter and output sections.

    Args:
        metadata: Execution metadata
        stdout_bytes: Standard output bytes
        stderr_bytes: Standard error bytes
        stdout_is_binary: Whether stdout is binary
        stderr_is_binary: Whether stderr is binary

    Returns:
        Complete Markdown document as string
    """
    sections = []

    # YAML frontmatter
    sections.append(format_properties(metadata))

    # Empty line after frontmatter
    sections.append("")

    # stdout section
    sections.append(format_output_section(stdout_bytes, "stdout", stdout_is_binary))

    # Horizontal rule separator
    sections.append("")
    sections.append("---")
    sections.append("")

    # stderr section
    sections.append(format_output_section(stderr_bytes, "stderr", stderr_is_binary))

    return "\n".join(sections)

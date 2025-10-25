"""
CLI entry point for obsidian-base-logger.
"""

import argparse
import sys
from pathlib import Path

from .executor import execute_command
from .formatter import format_markdown_document
from .utils import (
    is_binary,
    get_output_path,
    resolve_vault_path,
    sanitize_command_name,
)


def parse_args(args=None):
    """
    Parse command line arguments.

    Args:
        args: Optional list of arguments (for testing)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog='obsidian-base-logger',
        description='Wrap a shell process and log execution metadata to Obsidian-compatible Markdown',
        epilog='Example: obsidian-base-logger npm test'
    )

    parser.add_argument(
        '-o', '--vault',
        dest='vault_path',
        type=str,
        help='Obsidian vault path (default: $OBSIDIAN_VAULT or ~/.local/obsidian/vault)'
    )

    parser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
        help='Command and arguments to execute'
    )

    parsed = parser.parse_args(args)

    # Ensure command is not empty
    if not parsed.command:
        parser.error("the following arguments are required: command")

    return parsed


def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Resolve vault path
    vault_path = resolve_vault_path(args.vault_path)

    # Execute the command
    try:
        result = execute_command(args.command)
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine if outputs are binary
    stdout_is_binary = is_binary(result.stdout_bytes)
    stderr_is_binary = is_binary(result.stderr_bytes)

    # Format as Markdown
    markdown_content = format_markdown_document(
        metadata=result.metadata,
        stdout_bytes=result.stdout_bytes,
        stderr_bytes=result.stderr_bytes,
        stdout_is_binary=stdout_is_binary,
        stderr_is_binary=stderr_is_binary
    )

    # Determine output file path
    command_name = sanitize_command_name(args.command[0])
    output_path = get_output_path(
        vault_path=vault_path,
        hostname=result.metadata['host'],
        timestamp=result.metadata['started'],
        command=command_name
    )

    # Write to file
    try:
        output_path.write_text(markdown_content, encoding='utf-8')
        print(f"Log written to: {output_path}")
    except Exception as e:
        print(f"Error writing log file: {e}", file=sys.stderr)
        sys.exit(1)

    # Exit with same code as wrapped process
    sys.exit(result.return_code)


if __name__ == '__main__':
    main()

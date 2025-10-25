"""
Utility functions for file operations and helpers.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


def is_binary(data: bytes, sample_size: int = 8192) -> bool:
    """
    Check if data appears to be binary.

    Binary indicators:
    - Contains null bytes (definitive binary indicator)
    - High ratio of non-printable characters (>30%)

    Args:
        data: Bytes to check
        sample_size: Number of bytes to sample from the beginning

    Returns:
        True if data appears to be binary, False otherwise
    """
    if not data:
        return False

    sample = data[:sample_size]

    # Check for null bytes (definitive binary indicator)
    if b'\x00' in sample:
        return True

    # Count non-printable characters (excluding tab=9, newline=10, carriage return=13)
    non_printable = sum(
        1 for b in sample
        if b < 32 and b not in (9, 10, 13)
    )

    # If >30% non-printable, likely binary
    if len(sample) > 0:
        return (non_printable / len(sample)) > 0.3

    return False


def extract_iteration(filename: str) -> int:
    """
    Extract iteration number from filename.

    Expected format: {date}-{command}-{iteration}.md
    Example: 2025-10-24-npm-3.md -> 3

    Args:
        filename: Filename to parse

    Returns:
        Iteration number, or 0 if not found or malformed
    """
    try:
        # Pattern: ends with -{number}.md
        match = re.search(r'-(\d+)\.md$', filename)
        return int(match.group(1)) if match else 0
    except (AttributeError, ValueError):
        return 0


def get_next_iteration(vault_path: Path, hostname: str, date_str: str, command: str) -> int:
    """
    Scan directory and find next available iteration number.

    Args:
        vault_path: Root vault directory
        hostname: System hostname
        date_str: Date string in YYYY-MM-DD format
        command: Command name

    Returns:
        Next iteration number (starts at 1)
    """
    log_dir = vault_path / "logs" / hostname

    if not log_dir.exists():
        return 1

    # Find existing files matching pattern: {date}-{command}-*.md
    pattern = f"{date_str}-{command}-*.md"
    existing = list(log_dir.glob(pattern))

    if not existing:
        return 1

    # Extract iteration numbers and return max + 1
    iterations = [extract_iteration(f.name) for f in existing]
    return max(iterations) + 1


def get_output_path(
    vault_path: Path,
    hostname: str,
    timestamp: datetime,
    command: str
) -> Path:
    """
    Construct output file path and ensure directory exists.

    Format: ${vault}/logs/${host}/{date}-{command}-{iteration}.md

    Args:
        vault_path: Root vault directory
        hostname: System hostname
        timestamp: Execution start timestamp
        command: Command name

    Returns:
        Path object for output file
    """
    date_str = timestamp.strftime("%Y-%m-%d")
    log_dir = vault_path / "logs" / hostname

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get next iteration
    iteration = get_next_iteration(vault_path, hostname, date_str, command)

    # Construct filename
    filename = f"{date_str}-{command}-{iteration}.md"

    return log_dir / filename


def resolve_vault_path(cli_option: Optional[str] = None) -> Path:
    """
    Resolve vault path from CLI option, environment variable, or default.

    Priority:
    1. CLI option (-o)
    2. Environment variable (OBSIDIAN_VAULT)
    3. Default: ~/.local/obsidian/vault

    Args:
        cli_option: Optional vault path from CLI argument

    Returns:
        Resolved Path object with expanded home directory
    """
    if cli_option:
        return Path(cli_option).expanduser()

    env_vault = os.environ.get('OBSIDIAN_VAULT')
    if env_vault:
        return Path(env_vault).expanduser()

    # Default location
    return Path.home() / ".local" / "obsidian" / "vault"


def sanitize_command_name(command: str) -> str:
    """
    Sanitize command name for use in filename.

    Removes path components and special characters.

    Args:
        command: Command string

    Returns:
        Sanitized command name suitable for filename
    """
    # Get base name (remove path)
    base = Path(command).name

    # Remove or replace special characters that are problematic in filenames
    # Keep alphanumeric, dash, underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', base)

    return sanitized

# Obsidian Base Logger - Overview

## Purpose

`obsidian-base-logger` is a command-line tool that wraps arbitrary shell processes and captures their execution metadata and output in Obsidian-compatible Markdown format.

## Key Features

- **Process Wrapping**: Execute any command and capture its behavior
- **Rich Metadata**: Captures execution time, resource usage, and system information
- **Obsidian Integration**: Outputs formatted Markdown with YAML frontmatter (properties)
- **Organized Storage**: Automatically organizes logs by host and date with iteration tracking
- **Edge Case Handling**: Gracefully handles binary output, large outputs, and empty results
- **ANSI Preservation**: Retains terminal color codes for rich viewing

## Quick Start

```bash
# Basic usage
obsidian-base-logger npm test

# Custom vault location
obsidian-base-logger -o ~/Documents/MyVault npm test

# Complex commands with pipes
obsidian-base-logger bash -c "cat file.txt | grep error"
```

## Output Location

Logs are saved to: `${OBSIDIAN_VAULT}/logs/${host}/{date}-{command}-{iteration}.md`

**Vault Location Priority:**
1. CLI option: `-o <path>`
2. Environment variable: `$OBSIDIAN_VAULT`
3. Default: `~/.local/obsidian/vault`

## Technology Stack

- **Language**: Python 3.10+
- **Package Manager**: uv
- **Key Dependencies**:
  - `psutil` - System and process metrics
  - Standard library: `subprocess`, `argparse`, `datetime`, `pathlib`

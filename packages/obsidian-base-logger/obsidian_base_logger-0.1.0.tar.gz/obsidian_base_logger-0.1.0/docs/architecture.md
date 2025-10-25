# Architecture

## Project Structure

```
obsidian-base-logger/
├── src/
│   └── obsidian_base_logger/
│       ├── __init__.py
│       ├── cli.py           # CLI argument parsing and main entry point
│       ├── executor.py      # Process execution and metrics collection
│       ├── formatter.py     # Markdown and YAML formatting
│       └── utils.py         # File handling, iteration logic, helpers
├── tests/
│   ├── test_executor.py
│   ├── test_formatter.py
│   ├── test_utils.py
│   └── fixtures/
├── docs/
│   ├── overview.md
│   ├── architecture.md
│   ├── file-format.md
│   ├── edge-cases.md
│   └── testing.md
├── pyproject.toml           # uv/Python project configuration
├── README.md
├── CLAUDE.md                # Instructions for AI agents
└── .python-version
```

## Module Responsibilities

### `cli.py`
- Parse command-line arguments
- Determine vault location (CLI option > env var > default)
- Coordinate execution flow
- Handle errors and user feedback

### `executor.py`
- Execute wrapped process with `subprocess`
- Capture stdout and stderr separately
- Collect process metrics using `psutil`:
  - Start/end timestamps
  - CPU time (user/system)
  - Memory usage (peak RSS)
  - Disk I/O (read/write bytes)
  - Process ID, user, working directory
- Calculate execution time
- Return execution results and metadata

### `formatter.py`
- Format metadata as YAML frontmatter (Obsidian properties)
- Format stdout/stderr in Markdown sections
- Handle edge cases:
  - Empty output → `[no output]`
  - Binary output → `[binary output]`
  - Large output → Truncate at 10,000 lines
- Preserve ANSI escape codes in code blocks
- Generate final Markdown document

### `utils.py`
- Determine output file path
- Calculate iteration number by scanning existing files
- Create necessary directories
- Binary content detection
- Helper functions for file operations

## Data Flow

```
User Command
    ↓
cli.py (parse args, determine vault path)
    ↓
executor.py (run process, collect metrics)
    ↓
formatter.py (create Markdown with YAML frontmatter)
    ↓
utils.py (determine file path with iteration)
    ↓
Write to: ${VAULT}/logs/${host}/{date}-{command}-{iteration}.md
```

## Key Design Decisions

### Language Choice: Python
- Excellent process management (`subprocess`)
- Rich ecosystem for system metrics (`psutil`)
- Fast development and testing cycle
- Cross-platform support
- `uv` provides modern dependency management

### Shell Execution
Commands are executed with `shell=True` to support:
- Pipes and redirects
- Variable expansion
- Complex shell syntax

**Security Note**: This is intentional as the tool wraps arbitrary commands.

### ANSI Code Preservation
Terminal color codes (ANSI escape sequences) are preserved as-is in the output. This allows:
- No data loss
- Potential rendering by Obsidian plugins or external tools
- Graceful fallback to visible codes if no rendering available

### Iteration Tracking
Files are automatically numbered to prevent overwrites:
- Scans existing files matching `{date}-{command}-*.md`
- Extracts iteration numbers
- Uses max(iterations) + 1 for new file
- Starts at 1 if no existing files

### Metrics Collection
Using `psutil` to wrap the process allows collection of:
- CPU time (user and system)
- Memory usage (peak resident set size)
- Disk I/O (bytes read/written)

**Note**: Network I/O is not collected as it requires root privileges or platform-specific APIs.

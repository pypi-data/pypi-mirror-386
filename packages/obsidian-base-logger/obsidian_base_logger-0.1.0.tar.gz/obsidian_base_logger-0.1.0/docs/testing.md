# Testing Strategy

## Test Pyramid

```
    ┌─────────────┐
    │ Integration │  (10-15 tests)
    │   Tests     │
    ├─────────────┤
    │    Unit     │  (30-40 tests)
    │   Tests     │
    └─────────────┘
```

## Unit Tests

### `test_formatter.py`

**Metadata Formatting:**
- ✓ Format complete metadata to YAML frontmatter
- ✓ Handle missing optional fields
- ✓ Correct property types (string, number, datetime)
- ✓ ISO 8601 datetime formatting
- ✓ Time in seconds (not milliseconds)
- ✓ CPU times in milliseconds

**Markdown Body Formatting:**
- ✓ Wrap output in ansi code blocks
- ✓ Separate stdout and stderr with horizontal rule
- ✓ Handle empty output → `[no output]`
- ✓ Handle binary output → `[binary output]`
- ✓ Truncate large output at 10,000 lines
- ✓ Preserve ANSI escape codes

**Edge Cases:**
- ✓ Empty stdout, populated stderr
- ✓ Populated stdout, empty stderr
- ✓ Both empty
- ✓ Unicode characters
- ✓ Special characters in command/arguments

### `test_utils.py`

**Binary Detection:**
- ✓ Detect null bytes → binary
- ✓ Detect high ratio of non-printable chars → binary
- ✓ Allow printable text → not binary
- ✓ Allow common whitespace (tab, newline) → not binary
- ✓ Handle empty input

**Iteration Calculation:**
- ✓ No existing files → iteration 1
- ✓ Files exist (1, 2, 3) → return 4
- ✓ Files exist (1, 3, 5) → return 6 (max + 1)
- ✓ Malformed filenames → ignore and continue
- ✓ Directory doesn't exist → iteration 1

**Path Construction:**
- ✓ Correct path format: `{vault}/logs/{host}/{date}-{command}-{iteration}.md`
- ✓ Handle special characters in hostname
- ✓ Expand user home directory (`~`)
- ✓ Create missing directories

**Vault Location Resolution:**
- ✓ CLI option takes precedence
- ✓ Environment variable second priority
- ✓ Default fallback: `~/.local/obsidian/vault`

### `test_executor.py`

**Process Execution:**
- ✓ Capture stdout correctly
- ✓ Capture stderr correctly
- ✓ Capture return code (0 for success)
- ✓ Capture return code (non-zero for failure)
- ✓ Calculate execution time in seconds
- ✓ Record start timestamp (ISO 8601)

**Metrics Collection:**
- ✓ Capture PID
- ✓ Capture username
- ✓ Capture working directory
- ✓ Capture CPU time (user)
- ✓ Capture CPU time (system)
- ✓ Capture peak memory usage
- ✓ Capture I/O counters (read/write bytes)

**Error Handling:**
- ✓ Command not found
- ✓ Permission denied
- ✓ Process timeout (if implemented)

## Integration Tests

### `test_integration.py`

**Successful Command:**
```python
def test_successful_command(tmp_vault):
    """Test wrapping a successful command."""
    result = run_logger(
        tmp_vault,
        ["echo", "hello world"]
    )
    assert result.returncode == 0

    log_file = find_latest_log(tmp_vault)
    content = log_file.read_text()

    assert "return: 0" in content
    assert "hello world" in content
    assert "## stdout" in content
```

**Failed Command:**
```python
def test_failed_command(tmp_vault):
    """Test wrapping a command that exits with error."""
    result = run_logger(
        tmp_vault,
        ["python", "-c", "import sys; sys.exit(1)"]
    )
    assert result.returncode == 1

    log_file = find_latest_log(tmp_vault)
    content = log_file.read_text()

    assert "return: 1" in content
```

**Stdout Only:**
```python
def test_stdout_only(tmp_vault):
    """Command with stdout, empty stderr."""
    run_logger(tmp_vault, ["echo", "output"])

    log = find_latest_log(tmp_vault).read_text()
    assert "output" in log
    assert "[no output]" in log  # stderr section
```

**Stderr Only:**
```python
def test_stderr_only(tmp_vault):
    """Command with stderr, empty stdout."""
    run_logger(
        tmp_vault,
        ["bash", "-c", ">&2 echo 'error message'"]
    )

    log = find_latest_log(tmp_vault).read_text()
    assert "error message" in log
    assert "[no output]" in log  # stdout section
```

**Both Outputs:**
```python
def test_both_outputs(tmp_vault):
    """Command with both stdout and stderr."""
    run_logger(
        tmp_vault,
        ["bash", "-c", "echo 'out' && >&2 echo 'err'"]
    )

    log = find_latest_log(tmp_vault).read_text()
    assert "out" in log
    assert "err" in log
    assert log.index("out") < log.index("err")  # Order preserved
```

**Empty Outputs:**
```python
def test_empty_output(tmp_vault):
    """Command that produces no output."""
    run_logger(tmp_vault, ["true"])

    log = find_latest_log(tmp_vault).read_text()
    assert log.count("[no output]") == 2  # Both stdout and stderr
```

**Binary Output:**
```python
def test_binary_output(tmp_vault):
    """Command that outputs binary data."""
    run_logger(tmp_vault, ["cat", "/bin/ls"])

    log = find_latest_log(tmp_vault).read_text()
    assert "[binary output]" in log
```

**ANSI Colors:**
```python
def test_ansi_colors(tmp_vault):
    """Preserve ANSI escape codes."""
    run_logger(tmp_vault, ["ls", "--color=always"])

    log = find_latest_log(tmp_vault).read_text()
    # Check for ANSI escape sequences (ESC character)
    assert "\x1b[" in log or "\\x1b[" in log
```

**Large Output:**
```python
def test_large_output(tmp_vault):
    """Truncate output over 10,000 lines."""
    # Generate 15,000 lines
    run_logger(
        tmp_vault,
        ["bash", "-c", "for i in {1..15000}; do echo $i; done"]
    )

    log = find_latest_log(tmp_vault).read_text()
    assert "Output truncated" in log
    assert "15,000 total lines" in log or "15000 total lines" in log
```

**Command with Pipes:**
```python
def test_piped_command(tmp_vault):
    """Execute command with pipes."""
    run_logger(
        tmp_vault,
        ["bash", "-c", "echo -e 'foo\\nbar\\nbaz' | grep bar"]
    )

    log = find_latest_log(tmp_vault).read_text()
    assert "bar" in log
    assert "foo" not in log  # Filtered by grep
```

**Iteration Increment:**
```python
def test_iteration_increment(tmp_vault):
    """Multiple runs increment iteration."""
    # Run same command 3 times
    for _ in range(3):
        run_logger(tmp_vault, ["echo", "test"])

    logs = list_logs(tmp_vault)
    assert len(logs) == 3
    assert "echo-1.md" in logs[0].name
    assert "echo-2.md" in logs[1].name
    assert "echo-3.md" in logs[2].name
```

## Test Fixtures

### Commands for Testing

```python
# tests/fixtures/commands.py

# Simple stdout
ECHO_HELLO = ["echo", "hello"]

# Exit code 1
EXIT_ONE = ["python", "-c", "import sys; sys.exit(1)"]

# Stderr only
STDERR_ONLY = ["bash", "-c", ">&2 echo 'error'"]

# Both outputs
BOTH_OUTPUTS = ["bash", "-c", "echo 'out' && >&2 echo 'err'"]

# ANSI colors
COLORED_LS = ["ls", "--color=always"]

# Binary output
BINARY_CAT = ["cat", "/bin/ls"]

# Large output
LARGE_OUTPUT = ["bash", "-c", "seq 1 15000"]

# Piped command
PIPED_CMD = ["bash", "-c", "echo -e 'a\\nb\\nc' | grep b"]
```

### Temporary Vault

```python
import pytest
from pathlib import Path

@pytest.fixture
def tmp_vault(tmp_path):
    """Create temporary Obsidian vault for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    return vault
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=obsidian_base_logger --cov-report=html

# Run specific test file
uv run pytest tests/test_executor.py

# Run specific test
uv run pytest tests/test_formatter.py::test_empty_output

# Verbose output
uv run pytest -v

# Show print statements
uv run pytest -s
```

## Continuous Integration

Consider adding GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Run tests
        run: uv run pytest --cov
```

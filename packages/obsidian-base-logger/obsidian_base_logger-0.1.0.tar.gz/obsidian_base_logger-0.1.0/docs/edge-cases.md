# Edge Cases and Special Handling

## Empty Output

When stdout or stderr has no content:

```markdown
## stdout

[no output]
```

**Implementation:**
```python
if not stdout_data or len(stdout_data.strip()) == 0:
    stdout_content = "[no output]"
```

## Very Large Output

Truncate after 10,000 lines with informative message:

```markdown
## stdout

<first 10,000 lines>

[Output truncated: 15,243 total lines, showing first 10,000]
```

**Implementation:**
```python
lines = output.splitlines()
if len(lines) > 10000:
    truncated = '\n'.join(lines[:10000])
    truncated += f"\n\n[Output truncated: {len(lines):,} total lines, showing first 10,000]"
    return truncated
return output
```

## Binary Output

Detect and replace binary content:

```markdown
## stdout

[binary output]
```

**Detection Algorithm:**
```python
def is_binary(data: bytes, sample_size: int = 8192) -> bool:
    """
    Check if data appears to be binary.

    Binary indicators:
    - Contains null bytes
    - High ratio of non-printable characters
    """
    if not data:
        return False

    sample = data[:sample_size]

    # Check for null bytes (definitive binary indicator)
    if b'\x00' in sample:
        return True

    # Count non-printable characters (excluding tab, newline, carriage return)
    non_printable = sum(
        1 for b in sample
        if b < 32 and b not in (9, 10, 13)
    )

    # If >30% non-printable, likely binary
    if len(sample) > 0:
        return (non_printable / len(sample)) > 0.3

    return False
```

## Commands with Pipes and Redirects

### Problem
```bash
# This doesn't work as expected:
obsidian-base-logger ls | grep foo
# The pipe operates on obsidian-base-logger's output, not ls
```

### Solution
Accept full command as arguments and execute in shell:

```bash
# Recommended approach:
obsidian-base-logger bash -c "ls | grep foo"

# Or pass the full pipeline:
obsidian-base-logger "ls | grep foo"
```

**Implementation:**
```python
import subprocess
import shlex

# Join all arguments as command
full_command = ' '.join(args.command)

# Execute with shell=True to support pipes, redirects, etc.
process = subprocess.Popen(
    full_command,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    # ... other options
)
```

**Security Note:** This executes arbitrary shell commands, which is the intended behavior for a process wrapper.

## ANSI Escape Codes (Terminal Colors)

### Approach
Preserve ANSI escape codes as-is in the output.

**Example Raw Output:**
```
\x1b[32m✓\x1b[0m Tests passed
```

**Stored in Markdown:**
```markdown
[32m✓[0m Tests passed
```

**Rationale:**
- No data loss
- Can be post-processed or rendered by external tools
- Gracefully degrades to visible escape codes if unrendered
- No known Obsidian plugin currently renders ANSI codes, but content is preserved for future use

### Implementation
```python
# No special handling needed - just preserve as-is
stdout_content = stdout_bytes.decode('utf-8', errors='replace')
```

## Unicode and Encoding Issues

Handle non-UTF-8 output gracefully:

```python
# Decode with error handling
output_text = output_bytes.decode('utf-8', errors='replace')
```

The `errors='replace'` parameter replaces invalid bytes with `�` (replacement character) instead of raising an exception.

## Process Termination

### Normal Termination
- Return code available via `process.returncode`
- Captured in `return` property

### Signal Termination
```yaml
return: -9  # Killed by SIGKILL
return: -15 # Killed by SIGTERM
```

### Timeout (if implemented)
Could add optional timeout with:
```python
process.wait(timeout=300)  # 5 minute timeout
```

## Missing Metrics

If `psutil` cannot collect certain metrics:

```python
try:
    proc_info = psutil.Process(process.pid)
    io_counters = proc_info.io_counters()
except (psutil.NoSuchProcess, AttributeError):
    io_counters = None

# In YAML output, omit missing fields or use null
if io_counters:
    metadata['io_read_bytes'] = io_counters.read_bytes
    metadata['io_write_bytes'] = io_counters.write_bytes
```

## Iteration Counter Edge Cases

### Concurrent Execution
Race condition if two processes run simultaneously:

```python
# Mitigation: Use file locking or accept occasional collision
# For v1: Accept potential collision (low probability)
# For v2: Implement file locking with fcntl
```

### Malformed Filenames
If existing files don't match expected pattern:

```python
def extract_iteration(filename: str) -> int:
    """Extract iteration number from filename."""
    try:
        # Pattern: {date}-{command}-{iteration}.md
        match = re.search(r'-(\d+)\.md$', filename)
        return int(match.group(1)) if match else 0
    except (AttributeError, ValueError):
        return 0  # Treat malformed files as iteration 0
```

## Directory Creation

Ensure log directories exist:

```python
from pathlib import Path

log_dir = Path(vault_path) / "logs" / hostname
log_dir.mkdir(parents=True, exist_ok=True)
```

The `parents=True` creates intermediate directories, and `exist_ok=True` prevents errors if directory already exists.

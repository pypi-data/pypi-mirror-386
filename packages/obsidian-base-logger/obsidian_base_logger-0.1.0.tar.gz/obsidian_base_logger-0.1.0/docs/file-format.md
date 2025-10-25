# File Format Specification

## File Path Format

```
${OBSIDIAN_VAULT}/logs/${host}/{date}-{command}-{iteration}.md
```

**Components:**
- `${OBSIDIAN_VAULT}`: Vault root directory
- `${host}`: System hostname
- `{date}`: ISO date format `YYYY-MM-DD`
- `{command}`: Base command name (e.g., `npm`, `python`, `bash`)
- `{iteration}`: Auto-incrementing number starting from 1

**Examples:**
```
~/.local/obsidian/vault/logs/myserver/2025-10-24-npm-1.md
~/.local/obsidian/vault/logs/myserver/2025-10-24-npm-2.md
~/.local/obsidian/vault/logs/myserver/2025-10-24-python-1.md
```

## Markdown Document Structure

### YAML Frontmatter (Obsidian Properties)

```yaml
---
host: <string>              # Hostname where process ran
started: <datetime>          # ISO 8601 format with timezone
time: <number>              # Execution time in SECONDS
return: <number>            # Exit code (0 = success)
command: <string>           # Base command name
arguments: <text>           # Full arguments string
pid: <number>               # Process ID
user: <string>              # Username that ran the process
cwd: <text>                 # Working directory path
cpu_time_user_ms: <number>  # User CPU time in milliseconds
cpu_time_system_ms: <number> # System CPU time in milliseconds
memory_peak_mb: <number>    # Peak memory usage in megabytes
io_read_bytes: <number>     # Bytes read from disk
io_write_bytes: <number>    # Bytes written to disk
---
```

### Property Types

Obsidian will infer these types:
- `host`, `command`, `user`: Text
- `started`: Date & Time
- `time`, `return`, `pid`, `cpu_time_user_ms`, `cpu_time_system_ms`, `memory_peak_mb`, `io_read_bytes`, `io_write_bytes`: Number
- `arguments`, `cwd`: Text (multi-line)

### Markdown Body

```markdown
## stdout

<stdout content here>

---

## stderr

<stderr content here>
```

**Notes:**
- Output included directly (no code blocks)
- ANSI escape codes preserved as-is
- Horizontal rule (`---`) separates stdout and stderr sections

## Complete Example

```markdown
---
host: myserver
started: 2025-10-24T10:30:15.123Z
time: 2.456
return: 0
command: npm
arguments: test --verbose
pid: 12345
user: alice
cwd: /home/alice/projects/myapp
cpu_time_user_ms: 1850
cpu_time_system_ms: 320
memory_peak_mb: 145.2
io_read_bytes: 5242880
io_write_bytes: 1048576
---

## stdout

[32m✓[0m All tests passed
[90m  Duration: 2.3s[0m

---

## stderr

[no output]
```

## Data Types Reference

### Time Formats

- **`started`**: ISO 8601 with timezone (e.g., `2025-10-24T10:30:15.123Z`)
- **`time`**: Decimal seconds (e.g., `2.456` for 2.456 seconds)
- **`cpu_time_user_ms`**: Integer milliseconds (e.g., `1850`)
- **`cpu_time_system_ms`**: Integer milliseconds (e.g., `320`)

### Size Formats

- **`memory_peak_mb`**: Decimal megabytes (e.g., `145.2`)
- **`io_read_bytes`**: Integer bytes (e.g., `5242880`)
- **`io_write_bytes`**: Integer bytes (e.g., `1048576`)

### Return Codes

- **`0`**: Success
- **Non-zero**: Error (standard Unix convention)
- **Negative**: Signal termination (e.g., `-9` for SIGKILL)

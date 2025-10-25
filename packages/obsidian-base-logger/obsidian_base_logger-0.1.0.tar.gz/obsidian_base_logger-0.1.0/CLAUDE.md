# Instructions for AI Agents (Claude Code)

This document provides guidance for AI agents (like Claude Code) working on the `obsidian-base-logger` project.

## Project Overview

`obsidian-base-logger` is a Python CLI tool that wraps shell processes and logs execution metadata and output to Obsidian-compatible Markdown files.

**Key Technologies:**
- Python 3.10+
- `uv` for package management
- `psutil` for process metrics
- Standard library: `subprocess`, `argparse`, `pathlib`

## Quick Reference

### Documentation Structure

All design documentation is in `docs/`:
- `overview.md` - Project purpose and quick start
- `architecture.md` - Code structure and design decisions
- `file-format.md` - Output file specification
- `edge-cases.md` - Special handling and edge cases
- `testing.md` - Test strategy and examples

**READ THESE FIRST** before making changes.

### Project Structure

```
src/obsidian_base_logger/
├── cli.py          # Entry point, argument parsing
├── executor.py     # Process execution and metrics
├── formatter.py    # Markdown/YAML formatting
└── utils.py        # File operations, iteration logic
```

### Key Design Constraints

1. **Time Units:**
   - `time` property: **seconds** (decimal)
   - `cpu_time_user_ms` / `cpu_time_system_ms`: **milliseconds** (integer)

2. **Properties (YAML frontmatter):**
   ```yaml
   host, started, time, return, command, arguments,
   pid, user, cwd, cpu_time_user_ms, cpu_time_system_ms,
   memory_peak_mb, io_read_bytes, io_write_bytes
   ```

3. **File Path Format:**
   ```
   ${OBSIDIAN_VAULT}/logs/${host}/{date}-{command}-{iteration}.md
   ```

4. **Vault Location Priority:**
   - CLI `-o` option
   - `$OBSIDIAN_VAULT` env var
   - Default: `~/.local/obsidian/vault`

5. **Edge Cases:**
   - Empty output → `[no output]`
   - Binary output → `[binary output]` (detect null bytes or >30% non-printable)
   - Large output → Truncate at 10,000 lines
   - ANSI codes → Preserve as-is (no stripping)

6. **No Tags:** Do not include tags in properties

## Development Workflow

### Setup Environment

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=obsidian_base_logger
```

### Running the Tool

```bash
# Basic usage
uv run obsidian-base-logger echo "hello"

# Custom vault
uv run obsidian-base-logger -o ~/MyVault echo "hello"

# Complex command
uv run obsidian-base-logger bash -c "ls | grep test"
```

### Adding Features

1. **Read relevant docs** in `docs/` first
2. **Update tests** before implementing
3. **Follow existing patterns** in module structure
4. **Update docs** if behavior changes
5. **Run full test suite** before committing

### Testing Guidelines

- Unit tests in `tests/test_*.py`
- Use `tmp_vault` fixture for integration tests
- Test commands available in `tests/fixtures/commands.py`
- Aim for >80% code coverage
- Test all edge cases from `docs/edge-cases.md`

## Common Tasks

### Add New Metadata Field

1. Update `executor.py` to collect the metric
2. Update `formatter.py` to include in YAML
3. Update `docs/file-format.md` with field description
4. Add tests in `test_formatter.py` and `test_executor.py`

### Modify Output Format

1. Check `docs/file-format.md` for current spec
2. Update `formatter.py`
3. Update format examples in docs
4. Update integration tests to verify new format

### Handle New Edge Case

1. Document in `docs/edge-cases.md`
2. Implement handling in appropriate module
3. Add test case in `test_integration.py`

## Code Style

- Follow PEP 8
- Use type hints
- Docstrings for public functions
- Keep functions focused and small
- Prefer `pathlib.Path` over `os.path`

## Debugging

```bash
# Run specific test with output
uv run pytest tests/test_executor.py::test_capture_stdout -s

# Run tool with Python debugger
uv run python -m pdb -m obsidian_base_logger echo test

# Check created files
ls -la ~/.local/obsidian/vault/logs/$(hostname)/
cat ~/.local/obsidian/vault/logs/$(hostname)/<latest-file>
```

## Important Notes for AI Agents

### What NOT to Do

- ❌ Don't add tags to properties
- ❌ Don't change time units without updating ALL references
- ❌ Don't strip ANSI codes
- ❌ Don't create new docs files without updating this list
- ❌ Don't skip tests when adding features

### What TO Do

- ✅ Read `docs/` before making changes
- ✅ Write tests first (TDD approach)
- ✅ Preserve all existing functionality
- ✅ Update docs when behavior changes
- ✅ Check edge cases from `docs/edge-cases.md`
- ✅ Use type hints
- ✅ Follow the existing code patterns

### When Uncertain

1. Check `docs/` for specification
2. Look at existing tests for examples
3. Review similar functionality in codebase
4. Ask for clarification if spec is ambiguous

## Dependencies

Core dependencies (see `pyproject.toml`):
- `psutil` - Process and system metrics
- Standard library only otherwise

Dev dependencies:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting

## File Naming Conventions

- Source files: `snake_case.py`
- Test files: `test_*.py`
- Docs: `kebab-case.md`
- Log output: `{date}-{command}-{iteration}.md`

## Commit Messages

Follow conventional commits:
```
feat: add network metrics collection
fix: handle unicode in command arguments
docs: update edge-cases.md with binary detection
test: add integration test for piped commands
refactor: simplify iteration counter logic
```

## Questions to Consider

When modifying the code, ask:

1. **Does this change the output format?** → Update `docs/file-format.md`
2. **Does this handle a new edge case?** → Update `docs/edge-cases.md`
3. **Does this change architecture?** → Update `docs/architecture.md`
4. **Are there tests?** → Add them
5. **Will this work on all platforms?** → Consider Linux, macOS, Windows
6. **Does this preserve existing behavior?** → Run full test suite

## Resources

- Python subprocess: https://docs.python.org/3/library/subprocess.html
- psutil documentation: https://psutil.readthedocs.io/
- Obsidian properties: https://help.obsidian.md/properties
- uv documentation: https://docs.astral.sh/uv/

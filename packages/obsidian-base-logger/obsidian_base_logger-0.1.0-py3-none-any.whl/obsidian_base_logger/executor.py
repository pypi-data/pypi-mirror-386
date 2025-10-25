"""
Process execution and metrics collection.
"""

import os
import shlex
import socket
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import psutil


class ExecutionResult:
    """Container for process execution results and metrics."""

    def __init__(self):
        self.metadata: Dict[str, Any] = {}
        self.stdout_bytes: bytes = b''
        self.stderr_bytes: bytes = b''
        self.return_code: int = 0


def execute_command(command_args: List[str]) -> ExecutionResult:
    """
    Execute a command and collect execution metadata and output.

    Args:
        command_args: List of command arguments (e.g., ['npm', 'test'])

    Returns:
        ExecutionResult containing metadata, stdout, stderr, and return code
    """
    result = ExecutionResult()

    # Record start time
    start_time = datetime.now(timezone.utc)

    # Join command args for shell execution with proper quoting
    # This allows pipes, redirects, and other shell features
    full_command = shlex.join(command_args)

    # Get current working directory
    cwd = os.getcwd()

    # Start process with psutil wrapper for metrics
    process = subprocess.Popen(
        full_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )

    # Wrap with psutil for metrics collection
    try:
        proc_info = psutil.Process(process.pid)
    except psutil.NoSuchProcess:
        proc_info = None

    # Wait for process to complete and get output
    stdout_bytes, stderr_bytes = process.communicate()

    # Record end time
    end_time = datetime.now(timezone.utc)

    # Calculate execution time in seconds
    execution_time_seconds = (end_time - start_time).total_seconds()

    # Collect basic metadata
    result.metadata = {
        'host': socket.gethostname(),
        'started': start_time,
        'time': round(execution_time_seconds, 3),  # seconds with 3 decimal places
        'return': process.returncode,
        'command': command_args[0] if command_args else '',
        'arguments': ' '.join(command_args[1:]) if len(command_args) > 1 else '',
        'pid': process.pid,
        'user': os.getenv('USER') or os.getenv('USERNAME') or 'unknown',
        'cwd': cwd,
    }

    # Collect process metrics if available
    if proc_info:
        try:
            # CPU times (in milliseconds)
            cpu_times = proc_info.cpu_times()
            result.metadata['cpu_time_user_ms'] = int(cpu_times.user * 1000)
            result.metadata['cpu_time_system_ms'] = int(cpu_times.system * 1000)
        except (psutil.NoSuchProcess, AttributeError):
            pass

        try:
            # Memory info (convert to MB)
            mem_info = proc_info.memory_info()
            result.metadata['memory_peak_mb'] = round(mem_info.rss / (1024 * 1024), 2)
        except (psutil.NoSuchProcess, AttributeError):
            pass

        try:
            # I/O counters (bytes read/written)
            io_counters = proc_info.io_counters()
            result.metadata['io_read_bytes'] = io_counters.read_bytes
            result.metadata['io_write_bytes'] = io_counters.write_bytes
        except (psutil.NoSuchProcess, AttributeError, NotImplementedError):
            # io_counters() not available on all platforms
            pass

    # Store output and return code
    result.stdout_bytes = stdout_bytes
    result.stderr_bytes = stderr_bytes
    result.return_code = process.returncode

    return result

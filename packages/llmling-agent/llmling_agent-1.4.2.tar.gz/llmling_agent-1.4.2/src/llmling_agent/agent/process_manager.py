"""Process management for background command execution."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
from typing import Any
import uuid

from llmling_agent.log import get_logger


logger = get_logger(__name__)


@dataclass
class ProcessOutput:
    """Output from a running process."""

    stdout: str
    stderr: str
    combined: str
    truncated: bool = False
    exit_code: int | None = None
    signal: str | None = None


@dataclass
class RunningProcess:
    """Represents a running background process."""

    process_id: str
    command: str
    args: list[str]
    cwd: Path | None
    env: dict[str, str]
    process: asyncio.subprocess.Process
    created_at: datetime = field(default_factory=datetime.now)
    output_limit: int | None = None
    _stdout_buffer: list[str] = field(default_factory=list)
    _stderr_buffer: list[str] = field(default_factory=list)
    _output_size: int = 0
    _truncated: bool = False

    def add_output(self, stdout: str = "", stderr: str = "") -> None:
        """Add output to buffers, applying size limits."""
        if stdout:
            self._stdout_buffer.append(stdout)
            self._output_size += len(stdout.encode())
        if stderr:
            self._stderr_buffer.append(stderr)
            self._output_size += len(stderr.encode())

        # Apply truncation if limit exceeded
        if self.output_limit and self._output_size > self.output_limit:
            self._truncate_output()
            self._truncated = True

    def _truncate_output(self) -> None:
        """Truncate output from beginning to stay within limit."""
        if not self.output_limit:
            return

        # Combine all output to measure total size
        all_stdout = "".join(self._stdout_buffer)
        all_stderr = "".join(self._stderr_buffer)

        # Calculate how much to keep
        target_size = int(self.output_limit * 0.9)  # Keep 90% of limit

        # Truncate stdout first, then stderr if needed
        if len(all_stdout.encode()) > target_size:
            # Find character boundary for truncation
            truncated_stdout = all_stdout[-target_size:].lstrip()
            self._stdout_buffer = [truncated_stdout]
            self._stderr_buffer = [all_stderr]
        else:
            remaining = target_size - len(all_stdout.encode())
            truncated_stderr = all_stderr[-remaining:].lstrip()
            self._stdout_buffer = [all_stdout]
            self._stderr_buffer = [truncated_stderr]

        # Update size counter
        self._output_size = sum(
            len(chunk.encode()) for chunk in self._stdout_buffer + self._stderr_buffer
        )

    def get_output(self) -> ProcessOutput:
        """Get current process output."""
        stdout = "".join(self._stdout_buffer)
        stderr = "".join(self._stderr_buffer)
        combined = stdout + stderr

        # Check if process has exited
        exit_code = self.process.returncode
        signal = None  # TODO: Extract signal info if available

        return ProcessOutput(
            stdout=stdout,
            stderr=stderr,
            combined=combined,
            truncated=self._truncated,
            exit_code=exit_code,
            signal=signal,
        )

    async def is_running(self) -> bool:
        """Check if process is still running."""
        return self.process.returncode is None

    async def wait(self) -> int:
        """Wait for process to complete and return exit code."""
        return await self.process.wait()

    async def kill(self) -> None:
        """Terminate the process."""
        if await self.is_running():
            try:
                self.process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except TimeoutError:
                    # Force kill if it doesn't terminate
                    self.process.kill()
                    await self.process.wait()
            except ProcessLookupError:
                # Process already dead
                pass


class ProcessManager:
    """Manages background processes for an agent pool."""

    def __init__(self):
        """Initialize process manager."""
        self._processes: dict[str, RunningProcess] = {}
        self._output_tasks: dict[str, asyncio.Task[None]] = {}

    async def start_process(
        self,
        command: str,
        args: list[str] | None = None,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        output_limit: int | None = None,
    ) -> str:
        """Start a background process.

        Args:
            command: Command to execute
            args: Command arguments
            cwd: Working directory
            env: Environment variables (added to current env)
            output_limit: Maximum bytes of output to retain

        Returns:
            Process ID for tracking

        Raises:
            OSError: If process creation fails
        """
        process_id = f"proc_{uuid.uuid4().hex[:8]}"
        args = args or []

        # Prepare environment
        proc_env = dict(os.environ)
        if env:
            proc_env.update(env)

        # Convert cwd to Path if provided
        work_dir = Path(cwd) if cwd else None

        try:
            # Start process
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                cwd=work_dir,
                env=proc_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Create tracking object
            running_proc = RunningProcess(
                process_id=process_id,
                command=command,
                args=args,
                cwd=work_dir,
                env=env or {},
                process=process,
                output_limit=output_limit,
            )

            self._processes[process_id] = running_proc

            # Start output collection task
            self._output_tasks[process_id] = asyncio.create_task(
                self._collect_output(running_proc)
            )

            logger.info("Started process %s: %s %s", process_id, command, " ".join(args))
        except Exception as e:
            msg = f"Failed to start process: {command} {' '.join(args)}"
            logger.exception(msg, exc_info=e)
            raise OSError(msg) from e
        else:
            return process_id

    async def _collect_output(self, proc: RunningProcess) -> None:
        """Collect output from process in background."""
        try:
            # Read output streams concurrently
            stdout_task = asyncio.create_task(self._read_stream(proc.process.stdout))
            stderr_task = asyncio.create_task(self._read_stream(proc.process.stderr))

            stdout_chunks = []
            stderr_chunks = []

            # Collect output until both streams close
            stdout_done = False
            stderr_done = False

            while not (stdout_done and stderr_done):
                done, pending = await asyncio.wait(
                    [stdout_task, stderr_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=0.1,  # Check every 100ms
                )

                for task in done:
                    if task == stdout_task and not stdout_done:
                        chunk = task.result()
                        if chunk is None:
                            stdout_done = True
                        else:
                            stdout_chunks.append(chunk)
                            proc.add_output(stdout=chunk)
                            # Restart task for next chunk
                            stdout_task = asyncio.create_task(
                                self._read_stream(proc.process.stdout)
                            )

                    elif task == stderr_task and not stderr_done:
                        chunk = task.result()
                        if chunk is None:
                            stderr_done = True
                        else:
                            stderr_chunks.append(chunk)
                            proc.add_output(stderr=chunk)
                            # Restart task for next chunk
                            stderr_task = asyncio.create_task(
                                self._read_stream(proc.process.stderr)
                            )

            # Cancel any remaining tasks
            for task in pending:
                task.cancel()

        except Exception:
            logger.exception("Error collecting output for %s", proc.process_id)

    async def _read_stream(self, stream: asyncio.StreamReader | None) -> str | None:
        """Read a chunk from a stream."""
        if not stream:
            return None
        try:
            data = await stream.read(8192)  # Read in 8KB chunks
            return data.decode("utf-8", errors="replace") if data else None
        except Exception:  # noqa: BLE001
            return None

    async def get_output(self, process_id: str) -> ProcessOutput:
        """Get current output from a process.

        Args:
            process_id: Process identifier

        Returns:
            Current process output

        Raises:
            ValueError: If process not found
        """
        if process_id not in self._processes:
            msg = f"Process {process_id} not found"
            raise ValueError(msg)

        proc = self._processes[process_id]
        return proc.get_output()

    async def wait_for_exit(self, process_id: str) -> int:
        """Wait for process to complete.

        Args:
            process_id: Process identifier

        Returns:
            Exit code

        Raises:
            ValueError: If process not found
        """
        if process_id not in self._processes:
            msg = f"Process {process_id} not found"
            raise ValueError(msg)

        proc = self._processes[process_id]
        exit_code = await proc.wait()

        # Wait for output collection to finish
        if process_id in self._output_tasks:
            await self._output_tasks[process_id]

        return exit_code

    async def kill_process(self, process_id: str) -> None:
        """Kill a running process.

        Args:
            process_id: Process identifier

        Raises:
            ValueError: If process not found
        """
        if process_id not in self._processes:
            msg = f"Process {process_id} not found"
            raise ValueError(msg)

        proc = self._processes[process_id]
        await proc.kill()

        # Cancel output collection task
        if process_id in self._output_tasks:
            self._output_tasks[process_id].cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._output_tasks[process_id]

        logger.info("Killed process %s", process_id)

    async def release_process(self, process_id: str) -> None:
        """Release resources for a process.

        Args:
            process_id: Process identifier

        Raises:
            ValueError: If process not found
        """
        if process_id not in self._processes:
            msg = f"Process {process_id} not found"
            raise ValueError(msg)

        # Kill if still running
        proc = self._processes[process_id]
        if await proc.is_running():
            await proc.kill()

        # Clean up tasks
        if process_id in self._output_tasks:
            self._output_tasks[process_id].cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._output_tasks[process_id]
            del self._output_tasks[process_id]

        # Remove from tracking
        del self._processes[process_id]
        logger.info("Released process %s", process_id)

    def list_processes(self) -> list[str]:
        """List all tracked process IDs."""
        return list(self._processes.keys())

    async def get_process_info(self, process_id: str) -> dict[str, Any]:
        """Get information about a process.

        Args:
            process_id: Process identifier

        Returns:
            Process information dict

        Raises:
            ValueError: If process not found
        """
        if process_id not in self._processes:
            msg = f"Process {process_id} not found"
            raise ValueError(msg)

        proc = self._processes[process_id]
        return {
            "process_id": process_id,
            "command": proc.command,
            "args": proc.args,
            "cwd": str(proc.cwd) if proc.cwd else None,
            "created_at": proc.created_at.isoformat(),
            "is_running": await proc.is_running(),
            "exit_code": proc.process.returncode,
            "output_limit": proc.output_limit,
        }

    async def cleanup(self) -> None:
        """Clean up all processes."""
        logger.info("Cleaning up %s processes", len(self._processes))

        # Try graceful termination first
        termination_tasks = []
        for proc in self._processes.values():
            if await proc.is_running():
                proc.process.terminate()
                termination_tasks.append(proc.wait())

        if termination_tasks:
            try:
                future = asyncio.gather(*termination_tasks, return_exceptions=True)
                await asyncio.wait_for(future, timeout=5.0)  # Wait up to 5 seconds
            except TimeoutError:
                msg = "Some processes didn't terminate gracefully, force killing"
                logger.warning(msg)
                # Force kill remaining processes
                for proc in self._processes.values():
                    if await proc.is_running():
                        proc.process.kill()

        if self._output_tasks:
            for task in self._output_tasks.values():
                task.cancel()
            await asyncio.gather(*self._output_tasks.values(), return_exceptions=True)

        # Clear all tracking
        self._processes.clear()
        self._output_tasks.clear()

        logger.info("Process cleanup completed")

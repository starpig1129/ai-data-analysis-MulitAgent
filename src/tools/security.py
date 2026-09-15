"""Security scanning and resource limiting for code execution.

This module provides:
- SecurityScanner: Static analysis to detect dangerous code patterns
- ResourceLimiter: Execute code with timeout/memory limits
"""

import ast
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from queue import Empty, Queue

from ..logger import setup_logger
from .tool_config import TOOL_CONFIG

logger = setup_logger()

# Constants
DEFAULT_POLL_INTERVAL_SECONDS = 0.1


@dataclass
class ScanResult:
    """Result of security scan.

    Attributes:
        is_safe: Whether the code passed security checks.
        violations: List of security violations found.
        warnings: Non-blocking warnings (e.g., risky imports).
    """

    is_safe: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SecurityScanner:
    """Static analysis for dangerous code patterns.

    Uses both regex pattern matching and AST analysis to detect
    potentially dangerous code before execution.
    """

    # Dangerous builtins that should never be called (immutable)
    DANGEROUS_BUILTINS: frozenset = frozenset({"eval", "exec", "compile", "__import__"})

    # Risky modules that warrant warnings (immutable)
    RISKY_MODULES: frozenset = frozenset(
        {"os", "subprocess", "shutil", "socket", "ctypes"}
    )

    # Pre-compiled pattern for faster matching (built on first use)
    _compiled_pattern: re.Pattern | None = None

    @classmethod
    def _get_blocked_pattern(cls) -> re.Pattern:
        """Get or create compiled regex for blocked patterns."""
        if cls._compiled_pattern is None:
            patterns = TOOL_CONFIG.execution.blocked_patterns
            # Escape special regex chars and join with |
            escaped = [re.escape(p) for p in patterns]
            cls._compiled_pattern = re.compile("|".join(escaped))
        return cls._compiled_pattern

    @classmethod
    def scan_code(cls, code: str) -> ScanResult:
        """Scan code for security violations.

        Args:
            code: Python source code to scan.

        Returns:
            ScanResult with safety status and any violations/warnings.
        """
        violations = []
        warnings = []

        # Pattern-based detection (fast, using pre-compiled regex)
        pattern = cls._get_blocked_pattern()
        matches = pattern.findall(code)
        for match in matches:
            violations.append(f"Blocked pattern detected: '{match}'")

        # AST-based detection (more accurate, catches actual usage)
        try:
            tree = ast.parse(code)
            ast_violations, ast_warnings = cls._analyze_ast(tree)
            violations.extend(ast_violations)
            warnings.extend(ast_warnings)
        except SyntaxError as e:
            # Don't block on syntax errors - let runtime handle them
            warnings.append(f"Syntax error during scan: {e}")

        return ScanResult(
            is_safe=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    @classmethod
    def _analyze_ast(cls, tree: ast.AST) -> tuple:
        """Analyze AST for dangerous patterns (single-pass).

        Args:
            tree: Parsed AST tree.

        Returns:
            Tuple of (violations, warnings).
        """
        violations = []
        warnings = []

        for node in ast.walk(tree):
            # Check for dangerous builtins
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.DANGEROUS_BUILTINS:
                    violations.append(f"Dangerous builtin call: {func_name}()")

            # Check for risky imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in cls.RISKY_MODULES:
                        warnings.append(f"Risky module import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in cls.RISKY_MODULES:
                    warnings.append(f"Risky module import: {node.module}")

            # Check for attribute access on risky patterns
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "os" and node.attr == "system":
                    violations.append("os.system() is blocked")
                elif node.value.id == "shutil" and node.attr == "rmtree":
                    violations.append("shutil.rmtree() is blocked")

        return violations, warnings


def _enqueue_output(pipe, queue: Queue, stop_event: threading.Event) -> None:
    """Read lines from pipe and put them in queue (runs in thread).

    Args:
        pipe: stdout or stderr pipe from subprocess.
        queue: Queue to put lines into.
        stop_event: Event to signal thread to stop.
    """
    try:
        for line in iter(pipe.readline, ""):
            if stop_event.is_set():
                break
            if line:
                queue.put(line)
        pipe.close()
    except (ValueError, OSError):
        # Pipe closed
        pass


class ResourceLimiter:
    """Execute code with user-controlled resource limits.

    Supports:
    - Fixed timeout: Kill after N seconds
    - Progress-based timeout: Kill only if no stdout for N seconds
    - Memory limit: Set via resource.setrlimit (Linux only)

    Uses threading for cross-platform non-blocking stdout reading.
    """

    def __init__(
        self,
        timeout: int | None = None,
        memory_mb: int | None = None,
        max_output_chars: int | None = None,
        progress_timeout: int | None = None,
    ):
        """Initialize resource limiter.

        Args:
            timeout: Fixed timeout in seconds. None = no limit.
            memory_mb: Memory limit in MB (Linux only). None = no limit.
            max_output_chars: Truncate output if exceeds. None = use config default.
            progress_timeout: Timeout only if no stdout for N seconds.
        """
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.max_output_chars = (
            max_output_chars or TOOL_CONFIG.execution.max_output_chars
        )
        self.progress_timeout = progress_timeout

    def execute(
        self,
        command: list[str],
        cwd: str,
        shell: bool = False,
        executable: str | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute command with resource limits.

        Args:
            command: Command to execute (list or string if shell=True).
            cwd: Working directory.
            shell: Whether to use shell execution.
            executable: Shell executable (e.g., /bin/bash).

        Returns:
            CompletedProcess with stdout/stderr.

        Raises:
            TimeoutError: If execution exceeds timeout limits.
        """
        # Apply memory limit if specified (Linux only)
        preexec_fn = None
        if self.memory_mb is not None:
            preexec_fn = self._create_preexec_fn()

        # No timeout - run directly
        if self.timeout is None and self.progress_timeout is None:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=shell,
                executable=executable,
                capture_output=True,
                text=True,
                preexec_fn=preexec_fn,
            )
            return self._truncate_output(result)

        # Use Popen with threading for cross-platform timeout monitoring
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            executable=executable,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec_fn,
        )

        # Set up threaded output reading
        stdout_queue: Queue = Queue()
        stderr_queue: Queue = Queue()
        stop_event = threading.Event()

        stdout_thread = threading.Thread(
            target=_enqueue_output,
            args=(process.stdout, stdout_queue, stop_event),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_enqueue_output,
            args=(process.stderr, stderr_queue, stop_event),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        start_time = time.time()
        last_output_time = start_time
        stdout_lines = []
        stderr_lines = []

        try:
            while True:
                elapsed = time.time() - start_time
                idle_time = time.time() - last_output_time

                # Check if process finished
                return_code = process.poll()
                if return_code is not None:
                    # Process completed - drain remaining output
                    stop_event.set()
                    stdout_thread.join(timeout=1.0)
                    stderr_thread.join(timeout=1.0)

                    while not stdout_queue.empty():
                        try:
                            stdout_lines.append(stdout_queue.get_nowait())
                        except Empty:
                            break
                    while not stderr_queue.empty():
                        try:
                            stderr_lines.append(stderr_queue.get_nowait())
                        except Empty:
                            break
                    break

                # Read available output from queue
                try:
                    line = stdout_queue.get(timeout=DEFAULT_POLL_INTERVAL_SECONDS)
                    stdout_lines.append(line)
                    last_output_time = time.time()
                except Empty:
                    pass

                # Drain stderr without blocking
                while not stderr_queue.empty():
                    try:
                        stderr_lines.append(stderr_queue.get_nowait())
                    except Empty:
                        break

                # Timeout logic
                if self.progress_timeout is not None:
                    if idle_time > self.progress_timeout:
                        process.kill()
                        raise TimeoutError(
                            f"No output for {self.progress_timeout}s "
                            f"(total elapsed: {elapsed:.1f}s)"
                        )
                elif self.timeout is not None:
                    if elapsed > self.timeout:
                        process.kill()
                        raise TimeoutError(
                            f"Execution exceeded {self.timeout}s timeout"
                        )

        except TimeoutError:
            stop_event.set()
            process.kill()
            process.wait()
            raise

        result = subprocess.CompletedProcess(
            args=command,
            returncode=return_code,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
        )

        return self._truncate_output(result)

    def _create_preexec_fn(self):
        """Create preexec function for memory limiting (Linux only)."""
        memory_mb = self.memory_mb

        def set_limits():
            try:
                import resource

                memory_bytes = memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            except (ImportError, ValueError, OSError):
                pass  # Not available on this platform

        return set_limits

    def _truncate_output(
        self, result: subprocess.CompletedProcess
    ) -> subprocess.CompletedProcess:
        """Truncate output if it exceeds max_output_chars."""
        if self.max_output_chars and len(result.stdout) > self.max_output_chars:
            result.stdout = (
                result.stdout[: self.max_output_chars]
                + f"\n\n... [OUTPUT TRUNCATED at {self.max_output_chars} chars]"
            )
        return result

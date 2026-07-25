"""
Grounded Compiler Arbitrage (GCA) for Goby Framework.
Executes code snippets or scripts in isolated subprocesses to gather empirical proof.
"""

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    is_success: bool


class GroundedCompilerArbitrage:
    """
    Executes commands or code scripts safely in a subprocess environment,
    providing empirical evidence before making claims.
    """

    def __init__(self, default_timeout: float = 30.0, cwd: Optional[str] = None):
        self.default_timeout = default_timeout
        self.cwd = cwd or os.getcwd()

    def run_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """Runs a shell command synchronously and returns the execution result."""
        timeout_sec = timeout if timeout is not None else self.default_timeout
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        import time
        start_time = time.time()

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.cwd,
                env=current_env
            )
            stdout, stderr = process.communicate(timeout=timeout_sec)
            exit_code = process.returncode
            duration = time.time() - start_time

            return ExecutionResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout or "",
                stderr=stderr or "",
                duration_seconds=round(duration, 3),
                is_success=(exit_code == 0)
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            duration = time.time() - start_time
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout=stdout or "",
                stderr=f"Execution timed out after {timeout_sec} seconds.\n" + (stderr or ""),
                duration_seconds=round(duration, 3),
                is_success=False
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                command=command,
                exit_code=-2,
                stdout="",
                stderr=f"Execution failed with exception: {str(e)}",
                duration_seconds=round(duration, 3),
                is_success=False
            )

    def run_python_snippet(self, code_snippet: str, timeout: Optional[float] = None) -> ExecutionResult:
        """
        Creates a temporary python file with the snippet, executes it using current python interpreter,
        and cleans up afterwards.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code_snippet)
            temp_path = temp_file.name

        try:
            cmd = f'"{sys.executable}" "{temp_path}"'
            result = self.run_command(cmd, timeout=timeout)
            return result
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    # -------------------------------------------------------------------
    # Polyglot Extensions (v1.2.0)
    # -------------------------------------------------------------------

    def is_node_available(self) -> bool:
        """Check if Node.js is available in PATH."""
        node_path = getattr(self, "_node_path", "node")
        try:
            result = subprocess.run(
                [node_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def run_js_snippet(self, code_snippet: str, timeout: Optional[float] = None) -> ExecutionResult:
        """
        Creates a temporary .js file, executes it using Node.js,
        and cleans up afterwards. Returns graceful fallback if Node is unavailable.
        """
        node_path = getattr(self, "_node_path", "node")
        if not self.is_node_available():
            return ExecutionResult(
                command=f"{node_path} <snippet>",
                exit_code=-3,
                stdout="",
                stderr=f"Node.js is not available at '{node_path}'. Install Node.js or set _node_path.",
                duration_seconds=0.0,
                is_success=False,
            )

        with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code_snippet)
            temp_path = temp_file.name

        try:
            cmd = f'"{node_path}" "{temp_path}"'
            result = self.run_command(cmd, timeout=timeout)
            return result
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def run_test_suite(self, command: str, runner: str = "auto"):
        """
        Execute a test command and return structured, parsed results.
        Auto-detects the test runner from the command string if runner='auto'.

        Returns:
            StructuredTestResult from core.output_parsers
        """
        from .output_parsers import detect_runner, get_parser

        if runner == "auto":
            runner = detect_runner(command)

        raw_result = self.run_command(command)
        parser = get_parser(runner)
        structured = parser.parse(raw_result.stdout, raw_result.stderr, raw_result.exit_code)
        return structured

"""
Test command implementation for wl tool.
"""

import subprocess
import sys
from typing import Any

from .. import Command, register_command


@register_command("test")
class TestCommand(Command):
    """Command to run tests for the project."""

    # Tell pytest not to collect this class as a test class
    __test__ = False

    @property
    def name(self) -> str:
        """Get the command name."""
        return "test"

    @property
    def help(self) -> str:
        """Get the command help text."""
        return "Run project tests"

    def add_arguments(self, parser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            "--report",
            action="store_true",
            help="Show detailed test report including verbose output and coverage",
        )

    def _build_command_args(self, report_mode: bool, args) -> list[str]:
        """Build the command arguments for pytest."""
        cmd_args: list[str] = [sys.executable, "-m", "pytest", "tests/"]

        # Add verbose flag only in report mode
        if report_mode:
            cmd_args.append("-v")
        else:
            # Quiet mode - only show summary and errors
            cmd_args.append("--tb=short")  # Show shorter tracebacks
            cmd_args.append("-q")  # Quiet mode
            cmd_args.append("--no-header")  # Don't show pytest header
            cmd_args.append("--no-summary")  # Don't show summary at the end

        # Parse args to check if user provided their own --cov option
        has_user_cov = any(arg.startswith("--cov") for arg in args)

        # Only add default coverage if no user-defined cov and plugin is available
        if not has_user_cov and report_mode:
            has_pytest_cov = self._check_pytest_cov()
            if has_pytest_cov:
                cmd_args.extend(["--cov=py_wlcommands", "--cov-report=term-missing"])

        # Add any additional user arguments
        if args:
            filtered_args = [
                arg for arg in args if not arg.startswith("tests/")
            ]  # Avoid duplicate test paths
            cmd_args.extend(filtered_args)

        return cmd_args

    def _run_report_mode(self, cmd_args: list[str]) -> subprocess.CompletedProcess:
        """Run tests in report mode with direct stdout/stderr passthrough."""
        import os

        return subprocess.run(
            cmd_args,
            cwd=self._get_project_root(),
            check=False,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    def _run_quiet_mode(self, cmd_args: list[str]) -> subprocess.CompletedProcess:
        """Run tests in quiet mode with captured output."""
        import os

        return subprocess.run(
            cmd_args,
            cwd=self._get_project_root(),
            check=False,
            capture_output=True,
            text=True,
        )

    def _handle_test_result(
        self, result: subprocess.CompletedProcess, report_mode: bool
    ) -> None:
        """Handle the test result and print appropriate output."""
        # Only print output if there are errors
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"Tests failed with return code {result.returncode}")
            sys.exit(result.returncode)
        else:
            if not report_mode:
                print("All tests passed successfully!")
            else:
                print("All tests passed successfully! (Detailed report above)")

    def execute(self, *args: Any, **kwargs: Any) -> None:
        """
        Execute the test command.

        Args:
            *args: Positional arguments (can include pytest arguments like --cov)
            **kwargs: Keyword arguments
        """
        # Check if report mode is enabled
        report_mode = kwargs.get("report", False)

        # Run pytest to execute tests
        try:
            cmd_args = self._build_command_args(report_mode, args)

            # For report mode, directly pass through stdout/stderr to preserve colors
            if report_mode:
                result = self._run_report_mode(cmd_args)
            else:
                # For quiet mode, capture output and only show on failure
                result = self._run_quiet_mode(cmd_args)
                self._handle_test_result(result, report_mode)

            if result.returncode != 0:
                print(f"Tests failed with return code {result.returncode}")
                sys.exit(result.returncode)
            else:
                if not report_mode:
                    print("All tests passed successfully!")
                else:
                    print("All tests passed successfully! (Detailed report above)")
        except FileNotFoundError:
            print(
                "Error: pytest not found. Please install it using 'pip install pytest'"
            )
            sys.exit(1)
        except Exception as e:
            print(f"Error running tests: {e}")
            sys.exit(1)

    def _check_pytest_cov(self) -> bool:
        """
        Check if pytest-cov plugin is available.

        Returns:
            bool: True if pytest-cov is available, False otherwise
        """
        try:
            import pytest_cov

            return True
        except ImportError:
            return False

    def _get_project_root(self) -> str:
        """
        Get the project root directory.

        Returns:
            str: Path to the project root directory
        """
        import os

        # For now, assume the project root is the current working directory
        return os.getcwd()

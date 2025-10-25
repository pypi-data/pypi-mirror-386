"""
Python code formatting utilities for WL Commands.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from ...utils.logging import log_info


def format_with_python_tools(
    target: str, env: dict, quiet: bool, unsafe: bool = False
) -> None:
    """Format code with ruff only."""
    # Check if target exists
    target_path = Path(target)
    if not target_path.exists():
        if not quiet:
            print(f"Target {target} does not exist, skipping...")
        return

    try:
        ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix"]
        if unsafe:
            ruff_check_cmd.append("--unsafe-fixes")
        ruff_check_cmd.append(target)

        _run_format_command(ruff_check_cmd, env, quiet, passthrough=not quiet)
    except Exception as e:
        if not quiet:
            print(f"Warning: ruff check failed: {e}")
        else:
            print(f"Warning: ruff check failed: {e}")

    try:
        _run_format_command(
            ["uv", "run", "ruff", "format", target], env, quiet, passthrough=not quiet
        )
    except Exception as e:
        if not quiet:
            print(f"Warning: ruff format failed: {e}")
        else:
            print(f"Warning: ruff format failed: {e}")


def format_tools_scripts(
    tools_dir: str, env: dict, quiet: bool, unsafe: bool = False
) -> None:
    """Format Python files in tools directory with ruff."""
    tools_path = Path(tools_dir)
    if not tools_path.exists():
        if not quiet:
            print(f"Tools directory {tools_dir} does not exist, skipping...")
        else:
            print(f"Tools directory {tools_dir} does not exist, skipping...")
        return

    # Find all Python files in tools directory
    python_files = list(tools_path.glob("**/*.py"))
    if python_files:
        # Fix issues in tools Python files with ruff check
        try:
            ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix"]
            if unsafe:
                ruff_check_cmd.append("--unsafe-fixes")
            ruff_check_cmd.extend([str(f) for f in python_files])

            _run_format_command(ruff_check_cmd, env, quiet, passthrough=not quiet)
        except Exception as e:
            if not quiet:
                print(f"Warning: ruff check failed for tools scripts: {e}")
            else:
                print(f"Warning: ruff check failed for tools scripts: {e}")

        # Format tools Python files with ruff format
        try:
            _run_format_command(
                ["uv", "run", "ruff", "format"] + [str(f) for f in python_files],
                env,
                quiet,
                passthrough=not quiet,
            )
        except Exception as e:
            if not quiet:
                print(f"Warning: ruff format failed for tools scripts: {e}")
            else:
                print(f"Warning: ruff format failed for tools scripts: {e}")
    else:
        if not quiet:
            print("No Python files found in tools directory")
        else:
            print("No Python files found in tools directory")


def format_examples(
    examples_dir: str, env: dict, quiet: bool, unsafe: bool = False
) -> None:
    """Format examples directory with ruff."""
    examples_path = Path(examples_dir)
    if not examples_path.exists():
        if not quiet:
            print(f"Examples directory {examples_dir} does not exist, skipping...")
        else:
            print(f"Examples directory {examples_dir} does not exist, skipping...")
        return

    # Fix issues in examples with ruff check
    try:
        ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix"]
        if unsafe:
            ruff_check_cmd.append("--unsafe-fixes")
        ruff_check_cmd.append(examples_dir)

        _run_format_command(ruff_check_cmd, env, quiet, passthrough=not quiet)
    except Exception as e:
        if not quiet:
            print(f"Warning: ruff check failed for examples: {e}")
        else:
            print(f"Warning: ruff check failed for examples: {e}")

    # Format examples with ruff format
    try:
        _run_format_command(
            ["uv", "run", "ruff", "format", examples_dir],
            env,
            quiet,
            passthrough=not quiet,
        )
    except Exception as e:
        if not quiet:
            print(f"Warning: ruff format failed for examples: {e}")
        else:
            print(f"Warning: ruff format failed for examples: {e}")


def generate_type_stubs(src_dir: str, typings_dir: str, env: dict, quiet: bool) -> None:
    """Generate type stubs."""
    if not quiet:
        print(f"Generating type stubs for {src_dir}...")

    # Ensure typings directory exists
    typings_path = Path(typings_dir)
    typings_path.mkdir(parents=True, exist_ok=True)

    try:
        # Try to run stubgen through uv
        _run_format_command(
            ["uv", "run", "stubgen", src_dir, "-o", typings_dir],
            env,
            quiet,
            passthrough=False,
        )
    except Exception:
        # If that fails, try direct execution as fallback
        try:
            # First check if stubgen is available
            result = subprocess.run(
                ["python", "-c", "import mypy.stubgen"],
                capture_output=True,
                text=True,
                shell=False,
            )

            if result.returncode == 0:
                # stubgen is available, use it directly
                _run_format_command(
                    ["python", "-m", "mypy.stubgen", src_dir, "-o", typings_dir],
                    env,
                    quiet,
                    passthrough=False,
                )
            else:
                # Try to find stubgen executable
                stubgen_path = shutil.which("stubgen")
                if stubgen_path:
                    _run_format_command(
                        [stubgen_path, src_dir, "-o", typings_dir],
                        env,
                        quiet,
                        passthrough=False,
                    )
                else:
                    if not quiet:
                        print(
                            "Warning: stubgen not found, skipping type stub generation"
                        )
                    else:
                        print(
                            "Warning: stubgen not found, skipping type stub generation"
                        )
        except Exception as fallback_e:
            if not quiet:
                print(f"Warning: Failed to generate type stubs: {fallback_e}")
            else:
                print(f"Warning: Failed to generate type stubs: {fallback_e}")


def _is_running_in_uv_tool() -> bool:
    """Check if we are running in a uv tool environment."""
    # Check if we're in a uv tool environment by looking for uv specific paths
    import sys

    # Get the current executable path
    executable_path = sys.executable.lower()

    # Check if we're in a uv tool environment
    # UV tool environments typically have paths like:
    # Windows: C:\Users\{user}\AppData\Roaming\uv\tools\{tool_name}\...
    # Unix: ~/.local/share/uv/tools/{tool_name}/...
    return "uv\\tools\\" in executable_path or "uv/tools/" in executable_path


def _run_format_command(
    command: list, env: dict, quiet: bool, passthrough: bool = False
) -> None:
    """Run a formatting command with proper output handling."""
    # Prepare environment variables
    environment = env.copy() if env else {}

    # Fix encoding issues on Windows
    if sys.platform.startswith("win"):
        # Set environment variables to ensure proper UTF-8 handling
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONLEGACYWINDOWSFSENCODING"] = "1"

    # Special handling for uv run commands when running in uv tool environment
    if (
        len(command) >= 2
        and command[0] == "uv"
        and command[1] == "run"
        and _is_running_in_uv_tool()
    ):
        # When running in uv tool environment, try to run tools directly
        # instead of using uv run to avoid file locking issues
        direct_command = command[2:]  # Remove "uv run" from the command
        try:
            # Try running the command directly first
            _run_command_with_fallback(direct_command, environment, quiet, passthrough)
            return
        except Exception:
            # If direct execution fails, fall back to uv run
            pass

    # Check for execution of untrusted input - not applicable here as we're running
    # trusted formatting tools with trusted paths
    _run_command_with_fallback(command, environment, quiet, passthrough)


def _run_command_with_fallback(
    command: list, env: dict, quiet: bool, passthrough: bool = False
) -> None:
    """Run command with fallback handling."""
    if quiet and not passthrough:
        # In quiet mode, capture output to suppress it
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            shell=False,
            # Explicitly set encoding for Windows systems
            encoding="utf-8" if sys.platform.startswith("win") else None,
        )  # nosec B603
        # Even if the command fails, we continue execution to make formatting more robust
        if result.returncode != 0:
            # Log the error but don't raise exception to avoid stopping the whole formatting process
            error_msg = f"Command failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr.strip()}"
            raise Exception(error_msg)
    else:
        # In normal mode, let the command output directly to stdout/stderr
        result = subprocess.run(
            command,
            env=env,
            shell=False,
            # Explicitly set encoding for Windows systems
            encoding="utf-8" if sys.platform.startswith("win") else None,
        )  # nosec B603
        # Even if the command fails, we continue execution to make formatting more robust
        if result.returncode != 0:
            # Log the error but don't raise exception to avoid stopping the whole formatting process
            raise Exception(f"Command failed with return code {result.returncode}")

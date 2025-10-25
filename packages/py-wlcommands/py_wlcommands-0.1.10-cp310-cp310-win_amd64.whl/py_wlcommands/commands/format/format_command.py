"""
Format code command.
"""

from ...commands import Command, register_command, validate_command_args
from .python_formatter import (
    _run_format_command,
    format_examples,
    format_tools_scripts,
    format_with_python_tools,
    generate_type_stubs,
)
from .rust_formatter import format_rust_code


@register_command("format")
class FormatCommand(Command):
    """Command to format code."""

    @property
    def name(self) -> str:
        return "format"

    @property
    def help(self) -> str:
        return "Format code with ruff and cargo fmt"

    @classmethod
    def add_arguments(cls, parser):
        """Add command-specific arguments."""
        parser.add_argument(
            "-q", "--quiet", action="store_true", help="Suppress detailed output"
        )
        parser.add_argument(
            "--unsafe", action="store_true", help="Enable ruff's unsafe fixes"
        )
        parser.add_argument(
            "paths",
            nargs="*",
            help="Paths to format (default: src, tools, examples, rust)",
        )

    def _format_specified_paths(self, paths, env, quiet, unsafe=False):
        """Format specified paths."""
        import os
        from pathlib import Path

        from ...utils.logging import log_info

        for path in paths:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_file() and path_obj.suffix == ".py":
                    # Format individual Python file with ruff only
                    try:
                        ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix"]
                        if unsafe:
                            ruff_check_cmd.append("--unsafe-fixes")
                        ruff_check_cmd.append(str(path_obj))

                        _run_format_command(
                            ruff_check_cmd, env, quiet, passthrough=not quiet
                        )

                        # Also run ruff format for code formatting
                        _run_format_command(
                            [
                                "uv",
                                "run",
                                "ruff",
                                "format",
                                str(path_obj),
                            ],
                            env,
                            quiet,
                            passthrough=not quiet,
                        )
                    except Exception as e:
                        if not quiet:
                            print(f"Warning: Failed to format {path}: {e}")
                        else:
                            print(f"Warning: Failed to format {path}: {e}")
                elif path_obj.is_dir():
                    # Format directory with ruff only
                    format_with_python_tools(str(path_obj), env, quiet, unsafe)
            else:
                if not quiet:
                    print(f"Warning: Path {path} does not exist")
                else:
                    print(f"Warning: Path {path} does not exist")

    def _format_python_directory(
        self, directory: str, env: dict, quiet: bool, unsafe: bool = False
    ) -> None:
        """Format Python directory with ruff only."""
        from pathlib import Path

        from ...utils.logging import log_info

        # Check if directory exists before attempting to format
        dir_path = Path(directory)
        if not dir_path.exists():
            if not quiet:
                print(f"Directory {directory} does not exist, skipping...")
            else:
                print(f"Directory {directory} does not exist, skipping...")
            return

        format_with_python_tools(directory, env, quiet, unsafe)

    def _format_default_paths(self, project_root, env, quiet, unsafe=False):
        """Format default paths."""
        from pathlib import Path

        # Format source code with ruff only
        format_with_python_tools(str(project_root / "src"), env, quiet, unsafe)

        # Format tools scripts if directory exists
        tools_dir = project_root / "tools"
        if tools_dir.exists():
            format_with_python_tools(str(tools_dir), env, quiet, unsafe)

        # Format examples if directory exists
        examples_dir = project_root / "examples"
        if examples_dir.exists():
            format_with_python_tools(str(examples_dir), env, quiet, unsafe)

        # Generate type stubs
        generate_type_stubs(
            str(project_root / "src"), str(project_root / "typings"), env, quiet
        )

    @validate_command_args()
    def execute(
        self, quiet: bool = False, unsafe: bool = False, paths: list = None
    ) -> None:
        """
        Format code - equivalent to make format
        格式化代码 - 等效于 make format
        """
        import os
        import sys
        from pathlib import Path

        from ...utils.logging import log_info

        if not quiet:
            print("Formatting code...")

        try:
            # Set environment variables to handle encoding issues
            # 设置环境变量以处理编码问题
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Get project root directory
            project_root = Path(__file__).parent.parent.parent.parent.parent

            if paths:
                # Format specified paths
                self._format_specified_paths(paths, env, quiet, unsafe)
            else:
                # Format default paths
                self._format_default_paths(project_root, env, quiet, unsafe)

            # Format Rust code (only if no custom paths or rust path is specified)
            # 格式化 Rust 代码
            if not paths or any("rust" in path for path in paths):
                if not quiet:
                    print("Formatting Rust code with cargo fmt...")
                format_rust_code(str(project_root / "rust"), env, quiet)

            if not quiet:
                print("Code formatting completed successfully!")
            else:
                print("Code formatting completed successfully!")
        except Exception as e:
            if not quiet:
                print(f"Error formatting code: {e}")
            else:
                print(f"Error formatting code: {e}")
            sys.exit(1)

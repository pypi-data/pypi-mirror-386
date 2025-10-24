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
        return "Format code with isort, black, ruff and cargo fmt"

    @classmethod
    def add_arguments(cls, parser):
        """Add command-specific arguments."""
        parser.add_argument(
            "-q", "--quiet", action="store_true", help="Suppress detailed output"
        )
        parser.add_argument(
            "paths",
            nargs="*",
            help="Paths to format (default: src, tools, examples, rust)",
        )

    def _format_specified_paths(self, paths, env, quiet):
        """Format specified paths."""
        import os
        from pathlib import Path

        from ...utils.logging import log_info

        for path in paths:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_file() and path_obj.suffix == ".py":
                    # Format individual Python file
                    try:
                        _run_format_command(
                            ["uv", "run", "isort", str(path_obj)], env, quiet
                        )
                        _run_format_command(
                            ["uv", "run", "black", str(path_obj)], env, quiet
                        )
                        _run_format_command(
                            [
                                "uv",
                                "run",
                                "ruff",
                                "check",
                                "--fix",
                                str(path_obj),
                            ],
                            env,
                            quiet,
                        )
                    except Exception as e:
                        if not quiet:
                            log_info(f"Warning: Failed to format {path}: {e}")
                            log_info(f"警告：格式化 {path} 失败: {e}", lang="zh")
                        else:
                            print(f"Warning: Failed to format {path}: {e}")
                elif path_obj.is_dir():
                    # Format directory
                    format_with_python_tools(str(path_obj), env, quiet)
            else:
                if not quiet:
                    log_info(f"Warning: Path {path} does not exist")
                    log_info(f"警告：路径 {path} 不存在", lang="zh")
                else:
                    print(f"Warning: Path {path} does not exist")

    def _format_default_paths(self, project_root, env, quiet):
        """Format default paths."""
        # Format source code with isort and black
        # 使用 isort 和 black 格式化源代码
        format_with_python_tools(str(project_root / "src"), env, quiet)

        # Format tools scripts
        # 格式化工具脚本
        format_tools_scripts(str(project_root / "tools"), env, quiet)

        # Format examples
        # 格式化示例代码
        if (project_root / "examples").exists():
            format_examples(str(project_root / "examples"), env, quiet)

        # Generate type stubs
        # 生成类型提示文件
        generate_type_stubs(
            str(project_root / "src"), str(project_root / "typings"), env, quiet
        )

    @validate_command_args()
    def execute(self, quiet: bool = False, paths: list = None) -> None:
        """
        Format code - equivalent to make format
        格式化代码 - 等效于 make format
        """
        import os
        import sys
        from pathlib import Path

        from ...utils.logging import log_info

        if not quiet:
            log_info("Formatting code...")
            log_info("正在格式化代码...", lang="zh")

        try:
            # Set environment variables to handle encoding issues
            # 设置环境变量以处理编码问题
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Get project root directory
            project_root = Path(__file__).parent.parent.parent.parent.parent

            if paths:
                # Format specified paths
                self._format_specified_paths(paths, env, quiet)
            else:
                # Format default paths
                self._format_default_paths(project_root, env, quiet)

            # Format Rust code (only if no custom paths or rust path is specified)
            # 格式化 Rust 代码
            if not paths or any("rust" in path for path in paths):
                format_rust_code(str(project_root / "rust"), env, quiet)

            # Use simple logging for user-facing messages
            if not quiet:
                log_info("Code formatting completed successfully!")
                log_info("代码格式化成功完成！", lang="zh")
            else:
                print("Code formatting completed successfully!")
        except Exception as e:
            if not quiet:
                log_info(f"Error formatting code: {e}", lang="en")
                log_info(f"错误：格式化代码失败: {e}", lang="zh")
            else:
                print(f"Error formatting code: {e}")
            sys.exit(1)

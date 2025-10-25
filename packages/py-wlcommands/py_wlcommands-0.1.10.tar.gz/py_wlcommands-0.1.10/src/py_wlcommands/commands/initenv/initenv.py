"""Initialize project command."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

from ...exceptions import CommandError
from ...utils.logging import log_error, log_info
from .. import Command, register_command
from .utils.exceptions import InitEnvError
from .utils.git_initializer import GitInitializer
from .utils.initializer import Initializer
from .utils.platform_adapter import PlatformAdapter


@register_command("init")
class InitCommand(Command):
    """Command to initialize project environment."""

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        """Return the command name."""
        return "init"

    @property
    def help(self) -> str:
        """Return the command help text."""
        return "Initialize project environment or project structure"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "type",
            nargs="?",
            choices=["env", "project"],
            default="env",
            help="Type of initialization: env (default) or project",
        )

    def execute(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize project - equivalent to make init
        初始化项目 - 等效于 make init
        """
        init_type = kwargs.get("type", "env")

        if init_type == "project":
            self._init_project_structure()
        else:
            self._init_environment()

    def _init_environment(self) -> None:
        """Initialize full project environment."""
        log_info("=== Starting initialization of project environment ===")
        log_info("=== 开始初始化项目环境 ===", lang="zh")

        try:
            # Detect platform
            is_windows = PlatformAdapter.is_windows()
            env = PlatformAdapter.get_env()

            # Create initializer
            initializer = Initializer(env)

            # Check if uv is installed
            initializer.check_uv_installed()

            # Initialize Git repository
            initializer.init_git()

            # Setup project structure
            initializer.setup_project_structure()

            # Initialize Rust if needed
            initializer.init_rust()

            # Generate pyproject.toml if needed
            # Moved after init_rust to correctly detect Rust environment
            initializer.generate_pyproject()

            # Sync Cargo.toml with pyproject.toml
            initializer.sync_cargo_toml()

            # Create virtual environment
            initializer.create_venv(is_windows)

            # Platform-specific finalization
            if is_windows:
                self._finalize_windows()
            else:
                self._finalize_unix()

            log_info("Project environment initialization completed!")
            log_info("项目环境初始化完成!", lang="zh")
        except InitEnvError as e:
            log_error(f"Initialization error: {e}")
            log_error(f"初始化错误: {e}", lang="zh")
            raise CommandError(f"Project initialization failed: {e}")
        except Exception as e:
            log_error(f"Error initializing project: {e}")
            log_error(f"错误：初始化项目失败: {e}", lang="zh")
            raise CommandError(f"Project initialization failed: {e}")

    def _init_project_structure(self) -> None:
        """Initialize project structure with apps and packages folders."""
        log_info("=== Starting initialization of project structure ===")
        log_info("=== 开始初始化项目结构 ===", lang="zh")

        try:
            # Create apps and packages directories
            Path("apps").mkdir(exist_ok=True)
            Path("packages").mkdir(exist_ok=True)
            log_info("✓ Created apps and packages directories")
            log_info("✓ 创建 apps 和 packages 目录", lang="zh")

            # Get vendor template directory
            current_file = Path(__file__)
            vendor_project_dir = (
                current_file.parent
                / "utils"
                / ".."
                / ".."
                / ".."
                / "vendors"
                / "project"
            )
            vendor_project_dir = vendor_project_dir.resolve()

            template_files = [
                ".gitignore",
                ".python-version",
                "README.md",
                "pyproject.toml",
            ]

            for file_name in template_files:
                source_file = vendor_project_dir / file_name
                target_file = Path(file_name)

                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    log_info(f"✓ Copied {file_name} from template")
                    log_info(f"✓ 从模板复制 {file_name}", lang="zh")
                else:
                    log_error(f"Template file {file_name} not found")
                    log_error(f"未找到模板文件 {file_name}", lang="zh")

            # Initialize Git repository
            env = PlatformAdapter.get_env()
            git_initializer = GitInitializer(env)
            git_initializer.initialize()

            # Setup uv environment using 'uv run' to trigger initialization
            try:
                subprocess.run(
                    ["uv", "run", "python", "--version"],
                    check=True,
                    capture_output=True,
                    env=env,
                )
                log_info("✓ UV environment initialized")
                log_info("✓ UV 环境已初始化", lang="zh")
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to initialize UV environment: {e}")
                log_error(f"初始化 UV 环境失败: {e}", lang="zh")

            log_info("Project structure initialization completed!")
            log_info("项目结构初始化完成!", lang="zh")
        except Exception as e:
            log_error(f"Error initializing project structure: {e}")
            log_error(f"初始化项目结构时出错: {e}", lang="zh")
            raise CommandError(f"Project structure initialization failed: {e}")

    def _finalize_windows(self) -> None:
        """Finalize Windows-specific steps."""
        log_info("Environment initialization completed!")
        log_info("环境初始化完成!", lang="zh")
        log_info("To activate the environment, please run:")
        log_info("要激活环境，请运行:", lang="zh")
        log_info("  .venv\\Scripts\\Activate.ps1")
        log_info(
            "After activating the environment, please run 'uv pip install -e .' to install project dependencies."
        )
        log_info(
            "激活环境后，请运行 'uv pip install -e .' 来安装项目依赖包。", lang="zh"
        )

    def _finalize_unix(self) -> None:
        """Finalize Unix-specific steps."""
        log_info("Project environment initialization completed!")
        log_info("项目环境初始化完成!", lang="zh")

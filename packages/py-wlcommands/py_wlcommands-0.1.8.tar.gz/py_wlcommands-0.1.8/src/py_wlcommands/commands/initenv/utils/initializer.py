"""Project initializer coordinator."""

import subprocess
from pathlib import Path

from ....utils.logging import log_info
from .cargo_sync import sync_toml_files
from .config_manager import ConfigManager
from .git_initializer import GitInitializer
from .i18n_manager import I18nManager
from .log_manager import LogManager
from .project_structure import ProjectStructureSetup
from .pyproject_generator import PyProjectGenerator
from .rust_initializer import RustInitializer
from .venv_manager import VenvManager


class Initializer:
    """Coordinator for project initialization."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = env
        self.project_name = Path.cwd().name
        self.config_manager = ConfigManager()
        self.i18n_manager = I18nManager()
        self.log_manager = LogManager()

        # Initialize sub-components
        self.git_initializer = GitInitializer(env)
        self.project_structure_setup = ProjectStructureSetup()
        self.rust_initializer = RustInitializer()
        self.venv_manager = VenvManager(env)

    def check_uv_installed(self) -> None:
        """Check if uv is installed."""
        try:
            subprocess.run(
                ["uv", "--version"], check=True, capture_output=True, env=self.env
            )
            log_info("✓ uv command found.")
            log_info("✓ 找到 uv 命令。", lang="zh")
        except Exception:
            from ....exceptions import CommandError

            raise CommandError(
                "uv command not found. Please install uv first (e.g., pip install uv) and try again."
            )

    def init_git(self) -> None:
        """Initialize Git repository."""
        self.git_initializer.initialize()

    def generate_pyproject(self) -> None:
        """Generate pyproject.toml if it doesn't exist."""
        if not Path("pyproject.toml").exists():
            log_info("pyproject.toml not found, generating...")
            log_info("未找到 pyproject.toml，正在生成...", lang="zh")

            try:
                # Create PyProjectGenerator instance and generate pyproject.toml
                generator = PyProjectGenerator(self.project_name)
                generator.set_project_info()
                generator.set_build_system(is_rust=Path("rust").exists())
                generator.set_development_tools()
                generator.generate()

                log_info("✓ pyproject.toml generated successfully")
                log_info("✓ pyproject.toml 生成成功", lang="zh")
            except Exception as e:
                log_info(f"Warning: Failed to generate pyproject.toml: {e}")
                log_info(f"警告: 生成 pyproject.toml 失败: {e}", lang="zh")

    def setup_project_structure(self) -> None:
        """Setup project structure."""
        log_info("Setting up project structure...")
        log_info("设置项目结构...", lang="zh")

        try:
            self.project_structure_setup.setup(self.project_name)
        except Exception as e:
            log_info(f"Warning: Failed to setup project structure: {e}")
            log_info(f"警告: 设置项目结构失败: {e}", lang="zh")

    def init_rust(self) -> None:
        """Initialize Rust environment."""
        log_info("Initializing Rust environment...")
        log_info("初始化Rust环境...", lang="zh")

        try:
            self.rust_initializer.initialize()
        except Exception as e:
            log_info(f"Warning: Failed to initialize Rust environment: {e}")
            log_info(f"警告: 初始化Rust环境失败: {e}", lang="zh")

    def sync_cargo_toml(self) -> None:
        """Sync Cargo.toml with pyproject.toml."""
        try:
            sync_toml_files(Path("pyproject.toml"), Path("rust/Cargo.toml"))
            log_info("✓ rust/Cargo.toml 已成功同步和更新。")
        except Exception as e:
            log_info(f"Warning: Failed to sync Cargo.toml: {e}")
            log_info(f"警告: 同步 Cargo.toml 失败: {e}", lang="zh")

    def create_venv(self, is_windows: bool) -> None:
        """Create virtual environment."""
        if is_windows:
            self._create_venv_windows()
        else:
            self._create_venv_unix()

    def _detect_uv_workspace(self) -> bool:
        """Detect if we are in a uv workspace."""
        try:
            # Method 1: Check for uv.lock file which indicates a workspace
            if Path("uv.lock").exists():
                log_info("Debug: uv.lock file found, workspace detected")
                return True

            # Method 2: Use uv tree command to check for multiple root packages
            result = subprocess.run(
                ["uv", "tree"],
                capture_output=True,
                text=True,
                env=self.env,
                encoding="utf-8",
            )
            # Check for a workspace by counting root packages
            # In a workspace, there would be multiple top-level packages
            lines = result.stdout.split("\n")
            root_packages = []
            for line in lines:
                # Root package lines:
                # 1. Are not indented (don't start with space)
                # 2. Are not "Resolved" lines
                # 3. Are not "(*)" lines
                if (
                    not line.startswith(" ")
                    and line.strip()
                    and not line.startswith("Resolved")
                    and not line.startswith("(*)")
                ):
                    # Check if this is a root package - either without version or with version
                    # Root packages with versions look like "package-name v1.2.3"
                    if " v" in line and not line.startswith("v"):
                        # Check if it's a root package with version by verifying the format
                        parts = line.split(" v", 1)  # Split only on first occurrence
                        if len(parts) == 2:
                            package_name = parts[0]
                            version = parts[1]
                            # Verify that package name doesn't start with special chars and version is valid
                            if (
                                package_name
                                and not package_name.startswith(("├", "└", "│"))
                                and version.replace(".", "").replace("-", "").isalnum()
                            ):
                                root_packages.append(line)
                    elif line and not line.startswith(
                        ("├", "└", "│")
                    ):  # Plain root package without version
                        root_packages.append(line)

            log_info(f"Debug: uv tree root packages: {root_packages}")
            log_info(f"Debug: root packages count: {len(root_packages)}")

            # There should be more than one root package in a workspace
            if len(root_packages) > 1:
                log_info("Debug: Multiple root packages found, workspace detected")
                return True

        except Exception as e:
            log_info(f"Debug: Workspace detection error: {e}")
            pass  # Ignore errors in workspace detection

        log_info("Debug: No workspace detected")
        return False

    def _create_venv_windows(self) -> None:
        """Create virtual environment on Windows."""
        # Check uv workspace status and create venv if needed
        log_info(
            "Checking uv workspace status to determine if virtual environment should be created..."
        )
        log_info("检查uv workspace状态以决定是否创建虚拟环境...", lang="zh")

        if self._detect_uv_workspace():
            log_info(
                "✓ uv workspace environment detected, skipping local .venv creation"
            )
            log_info("✓ 检测到uv workspace环境，跳过创建本地.venv", lang="zh")
        else:
            log_info("Ensuring virtual environment exists...")
            log_info("确保虚拟环境存在...", lang="zh")
            # Create virtual environment directly instead of calling external script
            venv_path = self.config_manager.get("venv_path", ".venv")
            python_version = self.config_manager.get("python_version", "3.10")
            if not self.venv_manager.create_venv_windows(venv_path, python_version):
                log_info("Warning: Failed to create virtual environment")
                log_info("警告: 创建虚拟环境失败", lang="zh")

    def _create_venv_unix(self) -> None:
        """Create virtual environment on Unix-like systems."""
        # Check uv workspace status and create venv if needed
        log_info(
            "Checking uv workspace status to determine if virtual environment should be created..."
        )
        log_info("检查uv workspace状态以决定是否创建虚拟环境...", lang="zh")

        is_workspace = self._detect_uv_workspace()
        log_info(f"Debug: is_workspace = {is_workspace}")

        if is_workspace:
            log_info(
                "✓ uv workspace environment detected, skipping local .venv creation"
            )
            log_info("✓ 检测到uv workspace环境，跳过创建本地.venv", lang="zh")
        else:
            log_info("Creating basic virtual environment...")
            log_info("创建基础虚拟环境...", lang="zh")
            venv_path = self.config_manager.get("venv_path", ".venv")
            python_version = self.config_manager.get("python_version", "3.12")
            if not self.venv_manager.create_venv_unix(
                venv_path, python_version, self.env
            ):
                log_info("Warning: Failed to create virtual environment")
                log_info("警告: 创建虚拟环境失败", lang="zh")

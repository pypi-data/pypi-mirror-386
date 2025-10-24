"""Publish command for WL Commands."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..commands import Command, register_command
from ..exceptions import CommandError
from ..utils.logging import log_error, log_info
from .buildcommands.build_utils import is_rust_enabled


@register_command("publish")
class PublishCommand(Command):
    """Command to publish the project to PyPI."""

    @property
    def name(self) -> str:
        """Return the command name."""
        return "publish"

    @property
    def help(self) -> str:
        """Return the command help text."""
        return "Publish the project to PyPI"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add arguments to the parser."""
        parser.add_argument(
            "--repository",
            "-r",
            default="pypi",
            help="Repository to upload to (default: pypi)",
        )
        parser.add_argument(
            "--skip-build",
            action="store_true",
            help="Skip building the package, use existing dist files",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without actually uploading",
        )
        parser.add_argument(
            "--username",
            help="Username for uploading to PyPI",
        )
        parser.add_argument(
            "--password",
            help="Password or API token for uploading to PyPI",
        )
        parser.add_argument(
            "--no-auto-increment",
            action="store_true",
            help="Do not automatically increment the patch version before publishing",
        )

    def execute(self, *args: Any, **kwargs: Any) -> None:
        """Execute the publish command."""
        repository = kwargs.get("repository", "pypi")
        skip_build = kwargs.get("skip_build", False)
        dry_run = kwargs.get("dry_run", False)
        username = kwargs.get("username")
        password = kwargs.get("password")
        no_auto_increment = kwargs.get("no_auto_increment", False)

        try:
            # Auto increment version unless explicitly disabled
            if not no_auto_increment:
                self._increment_version()

            # Build the project if not skipped
            if not skip_build:
                self._build_distribution_packages()

            # Check that we have files to upload
            dist_files = self._get_dist_files()
            if not dist_files:
                raise CommandError("No distribution files found in dist/ directory")

            log_info(f"Found {len(dist_files)} distribution files to upload")
            for f in dist_files:
                log_info(f"  - {f.name}")

            # Upload to PyPI
            if dry_run:
                log_info("Dry run mode: skipping actual upload")
                log_info("Would run: twine upload --repository pypi dist/*")
            else:
                self._upload_to_pypi(repository, dist_files, username, password)

            log_info("✓ Package published successfully!")
            log_info("✓ 包发布成功！", lang="zh")

        except Exception as e:
            log_error(f"Publish failed: {e}")
            log_error(f"发布失败: {e}", lang="zh")
            raise CommandError(f"Publish failed: {e}")

    def _increment_version(self) -> None:
        """Increment the patch version in both Python and Rust files."""
        log_info("Incrementing patch version...")
        log_info("正在递增补丁版本号...", lang="zh")

        # Increment Python version
        python_version_file = Path("src/py_wlcommands/__init__.py")
        python_version = None
        if python_version_file.exists():
            content = python_version_file.read_text(encoding="utf-8")
            # Find version pattern and increment patch version
            version_pattern = r'__version__\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']'
            match = re.search(version_pattern, content)
            if match:
                major, minor, patch = match.groups()
                new_patch = str(int(patch) + 1)
                new_version = f"{major}.{minor}.{new_patch}"
                new_content = re.sub(
                    version_pattern, f'__version__ = "{new_version}"', content
                )
                python_version_file.write_text(new_content, encoding="utf-8")
                log_info(
                    f"Updated Python version from {major}.{minor}.{patch} to {new_version}"
                )
                python_version = new_version
            else:
                raise CommandError("Could not find version in __init__.py")

        # Increment Rust version
        rust_version_file = Path("rust/Cargo.toml")
        rust_version = None
        if rust_version_file.exists():
            content = rust_version_file.read_text(encoding="utf-8")
            # Find version pattern in the package section only and increment patch version
            # This pattern specifically looks for the version under the [package] section
            package_section_pattern = (
                r'(\[package\][^\[]*version\s*=\s*["\'])(\d+\.\d+\.\d+)(["\'])'
            )
            match = re.search(package_section_pattern, content, re.DOTALL)
            if match:
                full_match, current_version, end_quote = match.groups()
                # Parse the current version
                version_parts = current_version.split(".")
                if len(version_parts) == 3:
                    major, minor, patch = version_parts
                    new_patch = str(int(patch) + 1)
                    new_version = f"{major}.{minor}.{new_patch}"

                    # Replace only the version in the [package] section
                    def replace_version(match):
                        return f"{match.group(1)}{new_version}{match.group(3)}"

                    new_content = re.sub(
                        package_section_pattern,
                        replace_version,
                        content,
                        flags=re.DOTALL,
                    )
                    rust_version_file.write_text(new_content, encoding="utf-8")
                    log_info(
                        f"Updated Rust version from {current_version} to {new_version}"
                    )
                    rust_version = new_version
                else:
                    raise CommandError("Invalid version format in Cargo.toml")
            else:
                raise CommandError(
                    "Could not find version in Cargo.toml [package] section"
                )

        # Check version consistency
        if python_version and rust_version and python_version != rust_version:
            log_error(
                f"Version mismatch: Python version is {python_version}, Rust version is {rust_version}"
            )
            raise CommandError("Version mismatch between Python and Rust components")

        # Update template files to keep them in sync
        self._update_template_versions(python_version, rust_version)

    def _update_template_versions(self, python_version: str = None, rust_version: str = None) -> None:
        """Update template files with new version numbers."""
        # Update Rust template version
        if rust_version:
            rust_template_file = Path("src/py_wlcommands/vendors/rust/Cargo.toml")
            if rust_template_file.exists():
                content = rust_template_file.read_text(encoding="utf-8")
                package_section_pattern = (
                    r'(\[package\][^\[]*version\s*=\s*["\'])(\d+\.\d+\.\d+)(["\'])'
                )
                match = re.search(package_section_pattern, content, re.DOTALL)
                if match:
                    def replace_version(match):
                        return f"{match.group(1)}{rust_version}{match.group(3)}"

                    new_content = re.sub(
                        package_section_pattern,
                        replace_version,
                        content,
                        flags=re.DOTALL,
                    )
                    rust_template_file.write_text(new_content, encoding="utf-8")
                    log_info(f"Updated Rust template version to {rust_version}")

    def _build_distribution_packages(self) -> None:
        """Build distribution packages."""
        log_info("Building distribution packages...")
        log_info("构建分发包...", lang="zh")

        # Clean previous builds
        dist_dir = Path("dist")
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
            dist_dir.mkdir(exist_ok=True)

        # Build with maturin
        rust_enabled = is_rust_enabled()
        try:
            if rust_enabled:
                log_info("Building mixed Python/Rust project with maturin...")
                log_info("使用 maturin 构建混合 Python/Rust 项目...", lang="zh")

                # Check if we are in a uv workspace
                is_workspace = self._detect_uv_workspace()
                python_executable = None
                if is_workspace:
                    log_info("✓ uv workspace environment detected")
                    # In a workspace, check if .venv exists
                    if not Path(".venv").exists():
                        log_info("No .venv found, creating virtual environment...")
                        # Create virtual environment
                        self._create_venv()

                    # Set python executable path for maturin
                    if sys.platform.startswith("win"):
                        python_executable = ".venv\\Scripts\\python.exe"
                    else:
                        python_executable = ".venv/bin/python"
                else:
                    log_info("Not in uv workspace environment")

                # Build both wheel and sdist for maximum compatibility
                command = ["maturin", "build", "--release", "--out", "dist", "--sdist"]
                # If we have a python executable, use it for the build
                if python_executable:
                    command.extend(["-i", python_executable])

                log_info(f"Trying to build with: {' '.join(command)}")
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.stdout:
                    log_info(f"Build output: {result.stdout}")

                # If in workspace, remove the .venv directory
                if is_workspace and Path(".venv").exists():
                    log_info("In uv workspace, removing .venv directory...")
                    shutil.rmtree(".venv")
                    log_info("✓ .venv directory removed")
            else:
                log_info("Building pure Python project with uv...")
                log_info("使用 uv 构建纯 Python 项目...", lang="zh")
                subprocess.run(
                    ["uv", "build", "--sdist", "--wheel", "--out-dir", "dist"],
                    check=True,
                    capture_output=False,
                )
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Build failed: {e}")

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

    def _create_venv(self) -> None:
        """Create virtual environment using uv."""
        try:
            # Use uv to create virtual environment
            cmd = ["uv", "venv"]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            log_info("✓ Virtual environment created successfully")
            if result.stdout:
                log_info(f"uv venv output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create virtual environment: {e}"
            if e.stdout:
                error_msg += f"\nstdout: {e.stdout}"
            if e.stderr:
                error_msg += f"\nstderr: {e.stderr}"
            log_error(error_msg)
            raise CommandError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating virtual environment: {e}"
            log_error(error_msg)
            raise CommandError(error_msg)

    def _get_dist_files(self) -> list[Path]:
        """Get list of distribution files."""
        dist_dir = Path("dist")
        if not dist_dir.exists():
            return []

        dist_files = []
        for file_path in dist_dir.iterdir():
            if file_path.is_file() and (
                file_path.suffix == ".whl"
                or (file_path.suffix == ".gz" and "tar" in file_path.name)
            ):
                dist_files.append(file_path)

        return dist_files

    def _upload_to_pypi(
        self,
        repository: str,
        dist_files: list[Path],
        username: str = None,
        password: str = None,
    ) -> None:
        """Upload distribution files to PyPI."""
        log_info(f"Uploading to {repository}...")
        log_info(f"上传到 {repository}...", lang="zh")

        # Check if twine is available
        try:
            subprocess.run(["twine", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise CommandError(
                "twine is not installed. Please install it with: pip install twine"
            )

        # Prepare twine command
        cmd = ["twine", "upload", "--repository", repository]

        # Add credentials from command line arguments, environment variables, or let twine prompt
        if username and password:
            # Use provided credentials
            cmd.extend(["--username", username, "--password", password])
            log_info("Using credentials from command line arguments")
            log_info("使用命令行参数中的凭证", lang="zh")
        elif os.environ.get("TWINE_USERNAME") and os.environ.get("TWINE_PASSWORD"):
            # Use environment variables
            log_info("Using credentials from environment variables")
            log_info("使用环境变量中的凭证", lang="zh")
        else:
            # Let twine prompt for credentials
            log_info("No credentials provided, twine will prompt for them")
            log_info("未提供凭证，twine 将提示输入", lang="zh")

        # Add file paths
        for file_path in dist_files:
            cmd.append(str(file_path))

        # Execute upload
        try:
            subprocess.run(cmd, check=True, capture_output=False)
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Upload failed: {e}")

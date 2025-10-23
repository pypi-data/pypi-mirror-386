"""
Utilities for clean command.
"""

import glob
import os
import shutil
from pathlib import Path

import pathspec

from py_wlcommands.utils.logging import log_info


def clean_build_artifacts() -> None:
    """
    Clean build artifacts and temporary files
    清理构建产物和临时文件
    """

    # List of directories to remove
    # 需要删除的目录列表
    dirs_to_remove = [
        "build",
        "dist",
        "results",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "logs",
        "todos",
    ]

    # List of files to remove
    # 需要删除的文件列表
    files_to_remove = [".coverage"]

    # Remove specific directories
    # 删除指定目录
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                log_info(f"Removed directory: {dir_name}", lang="en")
                log_info(f"已删除目录: {dir_name}", lang="zh")
            except Exception as e:
                log_info(f"Failed to remove directory {dir_name}: {e}", lang="en")
                log_info(f"删除目录 {dir_name} 失败: {e}", lang="zh")

    # Remove specific files
    # 删除指定文件
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                log_info(f"Removed file: {file_name}", lang="en")
                log_info(f"已删除文件: {file_name}", lang="zh")
            except Exception as e:
                log_info(f"Failed to remove file {file_name}: {e}", lang="en")
                log_info(f"删除文件 {file_name} 失败: {e}", lang="zh")

    # Remove log files
    # 删除日志文件
    try:
        for log_file in glob.glob("*.log"):
            os.remove(log_file)
            log_info(f"Removed log file: {log_file}", lang="en")
            log_info(f"已删除日志文件: {log_file}", lang="zh")
    except Exception as e:
        log_info(f"Failed to remove log files: {e}", lang="en")
        log_info(f"删除日志文件失败: {e}", lang="zh")

    # Remove __pycache__ directories only in project directory (not in venv)
    # 只删除项目目录中的__pycache__目录（不删除虚拟环境中的）
    try:
        project_root = Path(".").resolve()
        for pycache_dir in project_root.rglob("__pycache__"):
            # Skip pycache directories in virtual environments
            # 跳过虚拟环境中的pycache目录
            if ".venv" in str(pycache_dir) or "venv" in str(pycache_dir):
                continue

            if pycache_dir.is_dir():
                shutil.rmtree(pycache_dir)
                log_info(f"Removed pycache directory: {pycache_dir}", lang="en")
                log_info(f"已删除pycache目录: {pycache_dir}", lang="zh")
    except Exception as e:
        log_info(f"Failed to remove pycache directories: {e}", lang="en")
        log_info(f"删除pycache目录失败: {e}", lang="zh")

    # Remove egg-info directories only in project directory
    # 只删除项目目录中的egg-info目录
    try:
        project_root = Path(".").resolve()
        for egg_info_dir in project_root.rglob("*.egg-info"):
            # Skip egg-info directories in virtual environments
            # 跳过虚拟环境中的egg-info目录
            if ".venv" in str(egg_info_dir) or "venv" in str(egg_info_dir):
                continue

            if egg_info_dir.is_dir():
                shutil.rmtree(egg_info_dir)
                log_info(f"Removed egg-info directory: {egg_info_dir}", lang="en")
                log_info(f"已删除egg-info目录: {egg_info_dir}", lang="zh")
    except Exception as e:
        log_info(f"Failed to remove egg-info directories: {e}", lang="en")
        log_info(f"删除egg-info目录失败: {e}", lang="zh")


def clean_all_artifacts() -> None:
    """
    Clean all artifacts including virtual environment
    清理所有产物，包括虚拟环境
    """

    # First do regular cleaning
    # 首先执行常规清理
    clean_build_artifacts()

    # Clean Rust artifacts
    # 清理Rust构建产物
    clean_rust_artifacts()

    # Remove virtual environment
    # 删除虚拟环境
    venv_dirs = [".venv", "venv"]
    for venv_dir in venv_dirs:
        if os.path.exists(venv_dir):
            try:
                shutil.rmtree(venv_dir)
                log_info(f"Removed virtual environment: {venv_dir}", lang="en")
                log_info(f"已删除虚拟环境: {venv_dir}", lang="zh")
            except Exception as e:
                log_info(
                    f"Failed to remove virtual environment {venv_dir}: {e}", lang="en"
                )
                log_info(f"删除虚拟环境 {venv_dir} 失败: {e}", lang="zh")

    # Remove auto-activation scripts
    # 删除自动激活脚本
    auto_activate_scripts = ["auto_activate_venv.bat", "auto_activate_venv.sh"]
    for script in auto_activate_scripts:
        if os.path.exists(script):
            try:
                os.remove(script)
                log_info(f"Removed auto-activation script: {script}", lang="en")
                log_info(f"已删除自动激活脚本: {script}", lang="zh")
            except Exception as e:
                log_info(
                    f"Failed to remove auto-activation script {script}: {e}", lang="en"
                )
                log_info(f"删除自动激活脚本 {script} 失败: {e}", lang="zh")

    # Remove files and directories that match .gitignore patterns
    # 删除匹配.gitignore模式的文件和目录
    try:
        if os.path.exists(".gitignore"):
            with open(".gitignore", encoding="utf-8") as f:
                gitignore_patterns = f.read().splitlines()

            # Filter out comments and empty lines
            # 过滤掉注释和空行
            patterns = [
                pattern.strip()
                for pattern in gitignore_patterns
                if pattern.strip() and not pattern.startswith("#")
            ]

            # Create pathspec matcher
            # 创建pathspec匹配器
            spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

            # Get all files and directories in the project
            # 获取项目中的所有文件和目录
            project_root = Path(".").resolve()
            all_paths = []

            # Walk through all files and directories
            for root, dirs, files in os.walk(".", topdown=True):
                # Modify dirs in-place to skip unwanted directories
                dirs[:] = [d for d in dirs if d not in (".git", ".venv", "venv")]

                # Handle files
                for file in files:
                    file_path = os.path.relpath(os.path.join(root, file), ".")
                    # Normalize path separators for cross-platform compatibility
                    normalized_path = file_path.replace("\\", "/")
                    all_paths.append(normalized_path)

                # Handle directories
                for dir in dirs:
                    dir_path = os.path.relpath(os.path.join(root, dir), ".")
                    # Normalize path separators for cross-platform compatibility and add trailing slash for directories
                    normalized_path = dir_path.replace("\\", "/") + "/"
                    all_paths.append(normalized_path)

            # Sort paths by depth (process files first, then directories)
            # This prevents trying to delete files in directories that have already been deleted
            all_paths.sort(key=lambda x: (x.count("/"), x))

            # Track deleted directories to avoid trying to delete files in them
            deleted_dirs = set()

            # Remove files and directories that match .gitignore patterns
            # 删除匹配.gitignore模式的文件和目录
            for path in all_paths:
                # Check if this path is inside a deleted directory
                skip = False
                for deleted_dir in deleted_dirs:
                    # For files in deleted directories
                    if path.startswith(deleted_dir) and not path == deleted_dir:
                        skip = True
                        break

                if skip:
                    continue

                if spec.match_file(path):
                    # Convert normalized path back to system path for file operations
                    system_path = path.rstrip(
                        "/"
                    )  # Remove trailing slash for file operations
                    system_path = system_path.replace("/", os.sep)
                    full_path = project_root / system_path
                    if full_path.exists():
                        try:
                            if full_path.is_dir():
                                shutil.rmtree(full_path)
                                deleted_dirs.add(path)
                                log_info(
                                    f"Removed directory matching .gitignore: {path}",
                                    lang="en",
                                )
                                log_info(
                                    f"已删除匹配.gitignore的目录: {path}", lang="zh"
                                )
                            else:
                                os.remove(full_path)
                                log_info(
                                    f"Removed file matching .gitignore: {path}",
                                    lang="en",
                                )
                                log_info(
                                    f"已删除匹配.gitignore的文件: {path}", lang="zh"
                                )
                        except Exception as e:
                            log_info(f"Failed to remove {path}: {e}", lang="en")
                            log_info(f"删除 {path} 失败: {e}", lang="zh")
    except Exception as e:
        log_info(f"Failed to clean files matching .gitignore patterns: {e}", lang="en")
        log_info(f"清理匹配.gitignore模式的文件失败: {e}", lang="zh")


def clean_rust_artifacts() -> None:
    """
    Clean Rust build artifacts
    清理Rust构建产物
    """

    # Check if Rust is enabled and directory exists
    # 检查是否启用了Rust且目录存在
    rust_dir = "rust"
    if os.path.exists(rust_dir):
        rust_target_dir = os.path.join(rust_dir, "target")
        if os.path.exists(rust_target_dir):
            try:
                shutil.rmtree(rust_target_dir)
                log_info(f"Removed Rust target directory: {rust_target_dir}", lang="en")
                log_info(f"已删除Rust target目录: {rust_target_dir}", lang="zh")
            except Exception as e:
                log_info(
                    f"Failed to remove Rust target directory {rust_target_dir}: {e}",
                    lang="en",
                )
                log_info(f"删除Rust target目录 {rust_target_dir} 失败: {e}", lang="zh")
        else:
            log_info("Rust target directory does not exist, skipping...", lang="en")
            log_info("Rust target目录不存在，跳过...", lang="zh")
    else:
        log_info("Rust directory does not exist, skipping...", lang="en")
        log_info("Rust目录不存在，跳过...", lang="zh")

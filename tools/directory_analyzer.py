# tools/directory_analyzer.py
import os
from typing import Dict, List, Optional, Set
from pathlib import Path


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def _calculate_summary(tree: Dict) -> Dict:
    """计算目录树的统计信息"""
    total_files = 0
    total_dirs = 0
    files_by_ext = {}

    def traverse(node):
        nonlocal total_files, total_dirs

        children = node.get("children", {})

        # 统计文件
        for file in children.get("files", []):
            total_files += 1
            ext = file.get("extension", "无扩展名")
            files_by_ext[ext] = files_by_ext.get(ext, 0) + 1

        # 递归统计子目录
        for directory in children.get("directories", []):
            total_dirs += 1
            if "children" in directory:
                traverse(directory)

    traverse(tree)

    return {
        "total_files": total_files,
        "total_directories": total_dirs,
        "files_by_extension": files_by_ext
    }


def list_directory(
        dirpath: str,
        max_depth: int = 1,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        show_hidden: bool = False
) -> Dict:
    """
    列出目录下的文件和子目录结构
    """
    dirpath = os.path.abspath(dirpath)

    if not os.path.exists(dirpath):
        return {
            "error": f"目录不存在: {dirpath}",
            "status": "error"
        }

    if not os.path.isdir(dirpath):
        return {
            "error": f"不是目录: {dirpath}",
            "status": "error"
        }

    # 默认排除常见的无关目录
    default_excludes = {
        '__pycache__', '.git', '.svn', '.hg',
        'node_modules', '.idea', '.vscode',
        'target', 'build', 'dist', '.gradle'
    }

    if exclude_patterns:
        exclude_set = set(exclude_patterns) | default_excludes
    else:
        exclude_set = default_excludes

    def should_exclude(path: str) -> bool:
        """判断是否应该排除此路径"""
        basename = os.path.basename(path)

        # 排除隐藏文件
        if not show_hidden and basename.startswith('.'):
            return True

        # 排除匹配的模式
        for pattern in exclude_set:
            if pattern in path or basename == pattern:
                return True

        return False

    def scan_directory(path: str, current_depth: int = 0) -> Dict:
        """递归扫描目录"""
        if current_depth > max_depth:
            return None

        try:
            entries = os.listdir(path)
        except PermissionError:
            return {
                "error": "权限不足",
                "type": "error"
            }

        directories = []
        files = []

        for entry in sorted(entries):
            entry_path = os.path.join(path, entry)

            if should_exclude(entry_path):
                continue

            if os.path.isdir(entry_path):
                dir_info = {
                    "name": entry,
                    "path": entry_path,
                    "type": "directory"
                }

                # 递归扫描子目录
                if current_depth < max_depth:
                    subdir = scan_directory(entry_path, current_depth + 1)
                    if subdir:
                        dir_info["children"] = subdir.get("children")
                        dir_info["summary"] = subdir.get("summary")

                directories.append(dir_info)

            elif os.path.isfile(entry_path):
                _, ext = os.path.splitext(entry)

                # 扩展名过滤
                if include_extensions and ext.lower() not in include_extensions:
                    continue

                file_size = os.path.getsize(entry_path)
                files.append({
                    "name": entry,
                    "path": entry_path,
                    "type": "file",
                    "extension": ext,
                    "size": file_size,
                    "size_human": _format_size(file_size)
                })

        return {
            "children": {
                "directories": directories,
                "files": files
            }
        }

    result = scan_directory(dirpath, 0)

    # 计算统计信息
    summary = _calculate_summary(result)

    return {
        "path": dirpath,
        "type": "directory",
        "children": result.get("children"),
        "summary": summary,
        "filters": {
            "max_depth": max_depth,
            "include_extensions": include_extensions,
            "exclude_patterns": list(exclude_set),
            "show_hidden": show_hidden
        },
        "status": "success"
    }


def get_project_structure(
        dirpath: str,
        language: Optional[str] = None
) -> Dict:
    """获取项目的智能结构概览"""
    language_configs = {
        'python': {
            'extensions': ['.py'],
            'exclude': ['__pycache__', '.pytest_cache', 'venv', 'env', '.venv', 'dist', 'build', '*.egg-info']
        },
        'java': {
            'extensions': ['.java'],
            'exclude': ['target', 'build', '.gradle', 'out']
        },
        'javascript': {
            'extensions': ['.js', '.jsx', '.ts', '.tsx'],
            'exclude': ['node_modules', 'dist', 'build', '.next']
        },
        'all': {
            'extensions': None,
            'exclude': []
        }
    }

    config = language_configs.get(language or 'all', language_configs['all'])

    return list_directory(
        dirpath=dirpath,
        max_depth=2,
        include_extensions=config['extensions'],
        exclude_patterns=config['exclude'],
        show_hidden=False
    )


def find_entry_files(
        dirpath: str,
        patterns: Optional[List[str]] = None
) -> Dict:
    """查找项目的入口文件"""
    if patterns is None:
        patterns = [
            'main.py', '__main__.py', 'app.py', 'run.py',
            'Main.java', 'Application.java',
            'index.js', 'app.js', 'server.js'
        ]

    dirpath = os.path.abspath(dirpath)
    entry_files = []

    for root, dirs, files in os.walk(dirpath):
        # 排除常见的无关目录
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv', 'target'
        }]

        for file in files:
            if file in patterns or any(file.endswith(p) for p in patterns):
                filepath = os.path.join(root, file)
                entry_files.append({
                    "name": file,
                    "path": filepath,
                    "relative_path": os.path.relpath(filepath, dirpath)
                })

    return {
        "project_root": dirpath,
        "entry_files": entry_files,
        "total": len(entry_files),
        "status": "success"
    }
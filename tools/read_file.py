import ast
import os
import sys


def find_project_root(start_path):
    """
    向上查找项目根目录
    策略：找到包含主包名的目录的父目录
    例如：/path/to/project/mmdet/datasets/ -> /path/to/project/
    """
    current = os.path.abspath(start_path)

    # 向上遍历，找到包含 __init__.py 的最顶层目录
    while True:
        parent = os.path.dirname(current)
        if parent == current:  # 已到达根目录
            return start_path

        # 检查父目录是否还是 Python 包
        parent_init = os.path.join(parent, "__init__.py")
        if not os.path.exists(parent_init):
            # 父目录不是包，当前目录是顶层包
            return parent

        current = parent

    return start_path


def recursive_read(filepath, base_path=None, visited=None, project_root=None):
    """
    递归读取 Python 文件及其本地依赖
    """
    if visited is None:
        visited = set()

    # 入口时确定 base_path 和 project_root
    if base_path is None:
        abspath = os.path.abspath(filepath)
        base_path = os.path.dirname(abspath)
        # 智能检测项目根目录
        project_root = find_project_root(base_path)
        print(f"检测到项目根目录: {project_root}")
    else:
        abspath = os.path.abspath(os.path.join(base_path, filepath))

    abspath = os.path.normcase(abspath)
    print(f"读取文件: {abspath}")

    if abspath in visited:
        return {}

    if not os.path.exists(abspath):
        print(f"文件不存在: {abspath}")
        return {}

    visited.add(abspath)
    result = {}

    try:
        with open(abspath, "r", encoding="utf-8") as f:
            content = f.read()
        result[abspath] = content
    except Exception as e:
        print(f"读取文件失败: {abspath}, 错误: {e}")
        return result

    # 解析 AST
    try:
        tree = ast.parse(content, filename=abspath)
    except Exception as e:
        print(f"解析AST失败: {abspath}, 错误: {e}")
        return result

    current_dir = os.path.dirname(abspath)

    def resolve_module_path(module_parts, level=0):
        """解析模块路径为文件路径"""
        # 计算相对导入的起始目录
        if level > 0:
            # 相对导入
            parent_dir = current_dir
            for _ in range(level - 1):
                parent_dir = os.path.dirname(parent_dir)
        else:
            # 绝对导入，从 project_root 开始
            parent_dir = project_root

        # 构建模块路径
        module_path = os.path.join(parent_dir, *module_parts)

        # 尝试 module.py
        py_file = module_path + ".py"
        if os.path.exists(py_file):
            return os.path.normcase(os.path.abspath(py_file))

        # 尝试 module/__init__.py
        init_file = os.path.join(module_path, "__init__.py")
        if os.path.exists(init_file):
            return os.path.normcase(os.path.abspath(init_file))

        return None

    def is_local_file(path):
        """判断是否为本地项目文件"""
        if path is None:
            return False
        try:
            norm_path = os.path.normcase(os.path.abspath(path))
            norm_root = os.path.normcase(os.path.abspath(project_root))
            return norm_path.startswith(norm_root)
        except (ValueError, OSError):
            return False

    for node in ast.walk(tree):
        # 处理 from ... import ...
        if isinstance(node, ast.ImportFrom):
            level = node.level or 0

            if node.module:
                # from .module import name 或 from package.module import name
                module_parts = node.module.split(".")
                dep_path = resolve_module_path(module_parts, level)

                if is_local_file(dep_path):
                    print(f"  -> 发现依赖: {node.module} (level={level}) -> {dep_path}")
                    result.update(recursive_read(
                        dep_path,
                        base_path=base_path,
                        visited=visited,
                        project_root=project_root
                    ))
                else:
                    if dep_path:
                        print(f"  -> 跳过非本地模块: {node.module}")
                    else:
                        print(f"  -> 无法解析模块: {node.module}")
            else:
                # from . import name
                if level > 0 and node.names:
                    for alias in node.names:
                        if alias.name != "*":
                            dep_path = resolve_module_path([alias.name], level)
                            if is_local_file(dep_path):
                                print(f"  -> 发现依赖: from {'.' * level} import {alias.name} -> {dep_path}")
                                result.update(recursive_read(
                                    dep_path,
                                    base_path=base_path,
                                    visited=visited,
                                    project_root=project_root
                                ))

        # 处理 import ...
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_parts = alias.name.split(".")
                dep_path = resolve_module_path(module_parts, level=0)

                if is_local_file(dep_path):
                    print(f"  -> 发现依赖: import {alias.name} -> {dep_path}")
                    result.update(recursive_read(
                        dep_path,
                        base_path=base_path,
                        visited=visited,
                        project_root=project_root
                    ))

    return result


def recursive_read_with_logging(filepath, base_path=None, project_root=None):
    """
    封装的函数，用于调用 recursive_read 并打印 visited 集合
    """
    visited = set()
    result = recursive_read(filepath, base_path=base_path, visited=visited, project_root=project_root)

    # 打印 visited 集合
    print("Visited files:")
    for path in visited:
        print(path)

    return result
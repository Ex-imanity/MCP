import ast
import os
from typing import List, Dict, Optional


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

def get_file_content(filepath: str) -> Dict[str, str]:
    """
    读取单个文件的内容

    Args:
        filepath: 文件的绝对路径或相对路径

    Returns:
        {"filepath": 绝对路径, "content": 文件内容}
    """
    try:
        abspath = os.path.abspath(filepath)
        with open(abspath, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "filepath": abspath,
            "content": content,
            "status": "success"
        }
    except Exception as e:
        return {
            "filepath": filepath,
            "error": str(e),
            "status": "error"
        }


def get_file_imports(filepath: str, project_root: Optional[str] = None) -> Dict:
    """
    分析文件的导入语句，返回本地依赖的文件路径列表

    Args:
        filepath: 要分析的文件路径
        project_root: 项目根目录（可选，自动检测）

    Returns:
        {
            "filepath": 文件绝对路径,
            "project_root": 项目根目录,
            "local_imports": [本地依赖文件的绝对路径列表],
            "external_imports": [外部模块名称列表],
            "import_details": [详细的导入信息]
        }
    """
    abspath = os.path.abspath(filepath)

    if not os.path.exists(abspath):
        return {"error": f"文件不存在: {abspath}", "status": "error"}

    # 自动检测项目根目录
    if project_root is None:
        project_root = find_project_root(os.path.dirname(abspath))

    try:
        with open(abspath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=abspath)
    except Exception as e:
        return {"error": f"解析失败: {str(e)}", "status": "error"}

    current_dir = os.path.dirname(abspath)
    local_imports = []
    external_imports = []
    import_details = []

    def resolve_module_path(module_parts, level=0):
        """解析模块路径为文件路径"""
        if level > 0:
            parent_dir = current_dir
            for _ in range(level - 1):
                parent_dir = os.path.dirname(parent_dir)
        else:
            parent_dir = project_root

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
        if isinstance(node, ast.ImportFrom):
            level = node.level or 0
            module_name = node.module or ""
            imported_names = [alias.name for alias in node.names]

            if node.module:
                module_parts = node.module.split(".")
                dep_path = resolve_module_path(module_parts, level)

                import_info = {
                    "type": "from_import",
                    "module": node.module,
                    "names": imported_names,
                    "level": level,
                    "is_local": is_local_file(dep_path),
                    "resolved_path": dep_path
                }

                if is_local_file(dep_path):
                    local_imports.append(dep_path)
                else:
                    external_imports.append(node.module)

                import_details.append(import_info)

            else:
                # from . import name
                if level > 0 and node.names:
                    for alias in node.names:
                        if alias.name != "*":
                            dep_path = resolve_module_path([alias.name], level)
                            import_info = {
                                "type": "relative_import",
                                "names": [alias.name],
                                "level": level,
                                "is_local": is_local_file(dep_path),
                                "resolved_path": dep_path
                            }

                            if is_local_file(dep_path):
                                local_imports.append(dep_path)

                            import_details.append(import_info)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_parts = alias.name.split(".")
                dep_path = resolve_module_path(module_parts, level=0)

                import_info = {
                    "type": "import",
                    "module": alias.name,
                    "is_local": is_local_file(dep_path),
                    "resolved_path": dep_path
                }

                if is_local_file(dep_path):
                    local_imports.append(dep_path)
                else:
                    external_imports.append(alias.name)

                import_details.append(import_info)

    return {
        "filepath": abspath,
        "project_root": project_root,
        "local_imports": list(set(local_imports)),  # 去重
        "external_imports": list(set(external_imports)),  # 去重
        "import_details": import_details,
        "status": "success"
    }


def get_dependency_tree(filepath: str, max_depth: int = 3, project_root: Optional[str] = None) -> Dict:
    """
    获取依赖树结构（不包含文件内容，仅路径）

    Args:
        filepath: 起始文件路径
        max_depth: 最大递归深度
        project_root: 项目根目录

    Returns:
        依赖树结构
    """
    if project_root is None:
        abspath = os.path.abspath(filepath)
        project_root = find_project_root(os.path.dirname(abspath))

    visited = set()

    def build_tree(path, depth=0):
        if depth > max_depth:
            return {"truncated": True, "reason": "max_depth_reached"}

        abspath = os.path.abspath(path)
        if abspath in visited:
            return {"circular": True}

        visited.add(abspath)

        imports_result = get_file_imports(abspath, project_root)
        if imports_result.get("status") == "error":
            return imports_result

        dependencies = {}
        for dep_path in imports_result.get("local_imports", []):
            dependencies[dep_path] = build_tree(dep_path, depth + 1)

        return {
            "filepath": abspath,
            "local_imports": imports_result.get("local_imports", []),
            "external_imports": imports_result.get("external_imports", []),
            "dependencies": dependencies
        }

    return {
        "root": filepath,
        "project_root": project_root,
        "tree": build_tree(filepath),
        "total_files": len(visited)
    }
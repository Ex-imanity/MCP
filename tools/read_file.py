import ast
import os

def recursive_read(filepath, base_path=None, visited=None):
    if visited is None:
        visited = set()
    # 入口时确定base_path
    if base_path is None:
        abspath = os.path.abspath(filepath)
        base_path = os.path.dirname(abspath)
    else:
        abspath = os.path.abspath(os.path.join(base_path, filepath))
    abspath = os.path.normcase(abspath)  # 兼容windows路径
    print(f"读取文件: {abspath}")
    if abspath in visited or not os.path.exists(abspath):
        return {}
    visited.add(abspath)
    result = {}
    with open(abspath, "r", encoding="utf-8") as f:
        content = f.read()
    result[abspath] = content
    # 解析import
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"解析AST失败: {abspath}, 错误: {e}")
        return result
    current_dir = os.path.dirname(abspath)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level > 0:
            # level=1: 当前目录，level=2: 上一级，依此类推
            parent_dir = current_dir
            for _ in range(node.level - 1):
                parent_dir = os.path.dirname(parent_dir)
            dep_relative_path = node.module.replace(".", os.sep) + ".py"
            dep_path = os.path.normcase(os.path.abspath(os.path.join(parent_dir, dep_relative_path)))
            if os.path.exists(dep_path):
                result.update(recursive_read(dep_path, visited=visited))
    return result
import ast
import os
from typing import List, Optional
from .base import LanguageParser, ImportInfo


class PythonParser(LanguageParser):
    """Python 语言解析器"""

    def get_file_extensions(self) -> List[str]:
        return ['.py']

    def find_project_root(self, start_path: str) -> str:
        """
        向上查找包含 __init__.py 的最顶层目录
        """
        current = os.path.abspath(start_path)

        while True:
            parent = os.path.dirname(current)
            if parent == current:
                return start_path

            parent_init = os.path.join(parent, "__init__.py")
            if not os.path.exists(parent_init):
                return parent

            current = parent

        return start_path

    def parse_imports(self, filepath: str) -> List[ImportInfo]:
        """解析 Python 文件的 import 语句"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        import_infos = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                level = node.level or 0
                module = node.module or ""
                names = [alias.name for alias in node.names]

                if node.module:
                    import_infos.append(ImportInfo(
                        type="from_import",
                        module=module,
                        names=names,
                        is_local=False,  # 稍后解析
                        resolved_path=None,
                        level=level
                    ))
                else:
                    # from . import name
                    for alias in node.names:
                        if alias.name != "*":
                            import_infos.append(ImportInfo(
                                type="relative_import",
                                module=alias.name,
                                names=[alias.name],
                                is_local=False,
                                resolved_path=None,
                                level=level
                            ))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_infos.append(ImportInfo(
                        type="import",
                        module=alias.name,
                        names=[alias.name],
                        is_local=False,
                        resolved_path=None,
                        level=0
                    ))

        return import_infos

    def resolve_import_path(
            self,
            import_info: ImportInfo,
            current_file: str
    ) -> Optional[str]:
        """解析 Python 模块路径为文件路径"""
        current_dir = os.path.dirname(current_file)
        level = import_info.level

        # 计算起始目录
        if level > 0:
            # 相对导入
            parent_dir = current_dir
            for _ in range(level - 1):
                parent_dir = os.path.dirname(parent_dir)
        else:
            # 绝对导入
            parent_dir = self.project_root

        # 构建模块路径
        module_parts = import_info.module.split(".")
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
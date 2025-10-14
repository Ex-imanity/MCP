import os
from typing import Dict, Optional
from .parsers.factory import ParserFactory
from .parsers.base import FileAnalysisResult


def get_file_content(filepath: str) -> Dict[str, str]:
    """读取单个文件的内容（语言无关）"""
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


def analyze_file_imports(
        filepath: str,
        project_root: Optional[str] = None
) -> Dict:
    """
    分析文件的导入语句（自动检测语言）
    """
    parser = ParserFactory.get_parser(filepath, project_root)

    if parser is None:
        _, ext = os.path.splitext(filepath)
        supported = ParserFactory.get_supported_extensions()
        return {
            "error": f"不支持的文件类型: {ext}。支持的类型: {supported}",
            "status": "error"
        }

    result = parser.analyze_file(filepath)

    # 转换为字典
    return {
        "filepath": result.filepath,
        "project_root": result.project_root,
        "local_imports": result.local_imports,
        "external_imports": result.external_imports,
        "import_details": [
            {
                "type": imp.type,
                "module": imp.module,
                "names": imp.names,
                "is_local": imp.is_local,
                "resolved_path": imp.resolved_path,
                "level": imp.level
            }
            for imp in result.import_details
        ],
        "status": result.status,
        "error": result.error,
        "language": result.language
    }


def get_dependency_tree(
        filepath: str,
        max_depth: int = 3,
        project_root: Optional[str] = None
) -> Dict:
    """获取依赖树结构（支持多语言）"""
    parser = ParserFactory.get_parser(filepath, project_root)

    if parser is None:
        _, ext = os.path.splitext(filepath)
        return {
            "error": f"不支持的文件类型: {ext}",
            "status": "error"
        }

    visited = set()

    def build_tree(path, depth=0):
        if depth > max_depth:
            return {"truncated": True, "reason": "max_depth_reached"}

        abspath = os.path.abspath(path)
        if abspath in visited:
            return {"circular": True}

        visited.add(abspath)

        analysis = analyze_file_imports(abspath, project_root)
        if analysis.get("status") == "error":
            return analysis

        dependencies = {}
        for dep_path in analysis.get("local_imports", []):
            dependencies[dep_path] = build_tree(dep_path, depth + 1)

        return {
            "filepath": abspath,
            "language": analysis.get("language"),
            "local_imports": analysis.get("local_imports", []),
            "external_imports": analysis.get("external_imports", []),
            "dependencies": dependencies
        }

    return {
        "root": filepath,
        "project_root": parser.project_root,
        "tree": build_tree(filepath),
        "total_files": len(visited)
    }
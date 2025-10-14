from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ImportInfo:
    """导入信息的统一数据结构"""
    type: str  # 'import', 'from_import', 'relative_import'
    module: str  # 模块名
    names: List[str]  # 导入的名称
    is_local: bool  # 是否为本地文件
    resolved_path: Optional[str]  # 解析后的文件路径
    level: int = 0  # 相对导入层级（Python特有）


@dataclass
class FileAnalysisResult:
    """文件分析结果的统一数据结构"""
    filepath: str
    project_root: str
    local_imports: List[str]
    external_imports: List[str]
    import_details: List[ImportInfo]
    status: str
    error: Optional[str] = None
    language: Optional[str] = None


class LanguageParser(ABC):
    """
    语言解析器的抽象基类
    遵循开放封闭原则：对扩展开放，对修改封闭
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        pass

    @abstractmethod
    def find_project_root(self, start_path: str) -> str:
        """
        查找项目根目录
        不同语言有不同的项目结构标识
        """
        pass

    @abstractmethod
    def parse_imports(self, filepath: str) -> List[ImportInfo]:
        """
        解析文件中的导入语句
        返回统一的 ImportInfo 列表
        """
        pass

    @abstractmethod
    def resolve_import_path(
            self,
            import_info: ImportInfo,
            current_file: str
    ) -> Optional[str]:
        """
        将导入语句解析为实际文件路径
        不同语言有不同的模块解析规则
        """
        pass

    def is_local_file(self, path: Optional[str]) -> bool:
        """判断文件是否属于本地项目"""
        if path is None:
            return False
        try:
            import os
            norm_path = os.path.normcase(os.path.abspath(path))
            norm_root = os.path.normcase(os.path.abspath(self.project_root))
            return norm_path.startswith(norm_root)
        except (ValueError, OSError):
            return False

    def analyze_file(self, filepath: str) -> FileAnalysisResult:
        """
        分析文件的模板方法
        定义了分析流程，具体步骤由子类实现
        """
        import os

        abspath = os.path.abspath(filepath)

        if not os.path.exists(abspath):
            return FileAnalysisResult(
                filepath=abspath,
                project_root="",
                local_imports=[],
                external_imports=[],
                import_details=[],
                status="error",
                error=f"文件不存在: {abspath}"
            )

        # 自动检测项目根目录
        if self.project_root is None:
            self.project_root = self.find_project_root(os.path.dirname(abspath))

        try:
            # 解析导入语句
            import_infos = self.parse_imports(abspath)

            local_imports = []
            external_imports = []

            # 解析每个导入的实际路径
            for import_info in import_infos:
                resolved_path = self.resolve_import_path(import_info, abspath)
                import_info.resolved_path = resolved_path
                import_info.is_local = self.is_local_file(resolved_path)

                if import_info.is_local:
                    local_imports.append(resolved_path)
                else:
                    external_imports.append(import_info.module)

            return FileAnalysisResult(
                filepath=abspath,
                project_root=self.project_root,
                local_imports=list(set(local_imports)),
                external_imports=list(set(external_imports)),
                import_details=import_infos,
                status="success",
                language=self.__class__.__name__.replace("Parser", "").lower()
            )

        except Exception as e:
            return FileAnalysisResult(
                filepath=abspath,
                project_root=self.project_root or "",
                local_imports=[],
                external_imports=[],
                import_details=[],
                status="error",
                error=str(e)
            )
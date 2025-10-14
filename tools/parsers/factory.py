import os
from typing import Optional, Dict, Type
from .base import LanguageParser
from .python_parser import PythonParser
from .java_parser import JavaParser


class ParserFactory:
    """
    解析器工厂
    遵循开放封闭原则：通过注册机制添加新解析器，无需修改工厂代码
    """

    _parsers: Dict[str, Type[LanguageParser]] = {}

    @classmethod
    def register_parser(cls, parser_class: Type[LanguageParser]):
        """注册新的解析器"""
        parser_instance = parser_class()
        for ext in parser_instance.get_file_extensions():
            cls._parsers[ext.lower()] = parser_class

    @classmethod
    def get_parser(
            cls,
            filepath: str,
            project_root: Optional[str] = None
    ) -> Optional[LanguageParser]:
        """根据文件扩展名获取对应的解析器"""
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        parser_class = cls._parsers.get(ext)
        if parser_class:
            return parser_class(project_root)

        return None

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """获取所有支持的文件扩展名"""
        return list(cls._parsers.keys())


# 注册所有解析器
ParserFactory.register_parser(PythonParser)
ParserFactory.register_parser(JavaParser)
import os
import re
from typing import List, Optional
from .base import LanguageParser, ImportInfo


class JavaParser(LanguageParser):
    """Java 语言解析器"""

    def get_file_extensions(self) -> List[str]:
        return ['.java']

    def find_project_root(self, start_path: str) -> str:
        """
        查找 Java 项目根目录
        标识：pom.xml (Maven) 或 build.gradle (Gradle) 或 src/ 目录
        """
        current = os.path.abspath(start_path)

        while True:
            parent = os.path.dirname(current)
            if parent == current:
                return start_path

            # 检查 Maven 项目
            if os.path.exists(os.path.join(current, "pom.xml")):
                return current

            # 检查 Gradle 项目
            if os.path.exists(os.path.join(current, "build.gradle")) or \
                    os.path.exists(os.path.join(current, "build.gradle.kts")):
                return current

            # 检查 src 目录
            if os.path.basename(current) == "src" and os.path.isdir(current):
                return parent

            current = parent

        return start_path

    def parse_imports(self, filepath: str) -> List[ImportInfo]:
        """解析 Java 文件的 import 语句"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        import_infos = []

        # 正则匹配 import 语句
        # import com.example.MyClass;
        # import static com.example.Utils.*;
        import_pattern = r'import\s+(?:static\s+)?([a-zA-Z0-9_.]+)(?:\.\*)?;'

        for match in re.finditer(import_pattern, content):
            full_import = match.group(1)

            # 分离包名和类名
            parts = full_import.split('.')
            if len(parts) > 0:
                class_name = parts[-1]
                package = '.'.join(parts[:-1]) if len(parts) > 1 else ''

                import_infos.append(ImportInfo(
                    type="import",
                    module=full_import,
                    names=[class_name],
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
        """解析 Java 包路径为文件路径"""
        # Java 的包名对应目录结构
        # com.example.MyClass -> src/main/java/com/example/MyClass.java

        # 查找 src 目录
        src_dirs = self._find_src_directories()

        # 将包名转换为路径
        package_path = import_info.module.replace('.', os.sep) + '.java'

        # 在各个 src 目录中查找
        for src_dir in src_dirs:
            possible_path = os.path.join(src_dir, package_path)
            if os.path.exists(possible_path):
                return os.path.normcase(os.path.abspath(possible_path))

        return None

    def _find_src_directories(self) -> List[str]:
        """查找项目中的 src 目录"""
        src_dirs = []

        # Maven 标准结构
        maven_src = os.path.join(self.project_root, "src", "main", "java")
        if os.path.exists(maven_src):
            src_dirs.append(maven_src)

        maven_test = os.path.join(self.project_root, "src", "test", "java")
        if os.path.exists(maven_test):
            src_dirs.append(maven_test)

        # Gradle 可能的结构
        gradle_src = os.path.join(self.project_root, "src")
        if os.path.exists(gradle_src):
            for root, dirs, files in os.walk(gradle_src):
                if "java" in dirs:
                    src_dirs.append(os.path.join(root, "java"))

        return src_dirs
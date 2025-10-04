import os
import tempfile
from tools.read_file import find_project_root, get_file_content, get_file_imports, get_dependency_tree

def test_recursive_read():
    # # 创建临时目录和文件
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     # 创建主文件
    #     main_file_path = os.path.join(temp_dir, "main.py")
    #     with open(main_file_path, "w", encoding="utf-8") as f:
    #         f.write("from .subdir.module import func\n")
    #
    #     # 创建子目录和模块文件
    #     subdir_path = os.path.join(temp_dir, "subdir")
    #     os.makedirs(subdir_path)
    #     module_file_path = os.path.join(subdir_path, "module.py")
    #     with open(module_file_path, "w", encoding="utf-8") as f:
    #         f.write("def func():\n    pass\n")

    # 调用函数
    main_file_path = r"D:\dev\PythonProjects\MMDetection-C2Former\mmdet\datasets\drone_vehicle.py"
    project_root = find_project_root(main_file_path)
    print(f"Project root: {project_root}")
    content = get_file_content(main_file_path)
    print(f"File content: {content['content'][:100]}...")  # 只打印前100个字符
    imports = get_file_imports(main_file_path, project_root)
    print(f"File imports: {imports}")


# 执行测试
test_recursive_read()
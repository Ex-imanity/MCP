import os
import tempfile
from tools.read_file import recursive_read, recursive_read_with_logging

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
        main_file_path = r"D:\Imanity\dev\PythonProjects\MMDetection-C2Former\mmdet\datasets\drone_vehicle.py"
        result = recursive_read_with_logging(main_file_path)

        # 输出结果
        for path, content in result.items():
            print(f"文件路径: {path}\n内容预览:\n{content[:100]}...\n")

# 执行测试
test_recursive_read()
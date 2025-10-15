# MCP-demo

一个基于 Starlette 和 SSE 的多功能服务端项目，支持递归读取 Python 和 Java 项目文件及其依赖，并支持对整个文件夹进行递归分析。

## 目录结构

- `conf/` 配置文件目录
  - `mcp_recursive_server.json` 递归服务配置
- `server/` 服务端相关代码
  - `__init__.py`
  - `read_file_server.py` 主服务端启动文件
- `tools/` 工具函数目录
  - `__init__.py`
  - `directory_analyzer.py` 文件夹递归分析工具
  - `file_analyzer.py` 文件分析工具
  - `read_file.py` 递归读取文件工具
  - `parsers/` 语言解析器目录
    - `__init__.py`
    - `base.py` 解析器基类
    - `factory.py` 解析器工厂
    - `java_parser.py` Java 解析器
    - `python_parser.py` Python 解析器
- `tmp/` 临时和测试目录
  - `__init__.py`
  - `test_read_file.py` 相关测试
- `README.md` 项目说明文档

## 依赖

- Python 3.11+
- starlette
- uvicorn

## 安装依赖

```bash
pip install starlette uvicorn mcp
```

## 功能说明

- 支持递归读取 Python 文件及其通过 import 导入的依赖模块
- 支持递归读取 Java 文件及其 import 的依赖类（需在同一项目目录下）
- 支持对整个文件夹进行递归分析，自动识别并处理其中的 Python/Java 文件及其依赖
- 自动识别文件类型，分析依赖关系，生成依赖树结构
- 提供基于 Starlette 的 HTTP/SSE 服务端接口，便于集成和自动化调用

## 启动服务示例

`server/read_file_server.py` 提供了基于 Starlette 的服务端，支持通过 HTTP 接口递归读取 Python/Java 文件及其依赖，也支持对文件夹的递归分析。

启动服务：
```bash
python server/read_file_server.py --host 0.0.0.0 --port 8081
```

## 注册 mcp 插件
URL: **http://<host>:<port>/sse**
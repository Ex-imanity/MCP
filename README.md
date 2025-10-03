# MCP-demo

一个基于 Starlette 和 SSE 的多功能 Python 服务端项目，支持递归读取文件功能。

## 目录结构

- `conf/` 配置文件目录
- `server/` 服务端相关代码
  - `read_file_server.py` 主服务端启动文件
- `tools/` 工具函数目录
  - `read_file.py` 递归读取文件工具

## 依赖

- Python 3.11+
- starlette
- uvicorn

## 安装依赖

```bash
pip install starlette uvicorn
```

## 启动服务示例
```bash
python server/read_file_server.py --host 0.0.0.0 --port 8080
```

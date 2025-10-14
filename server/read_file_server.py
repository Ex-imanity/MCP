from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from tools.file_analyzer import (
    get_file_content,
    analyze_file_imports,
    get_dependency_tree
)
from tools.parsers.factory import ParserFactory

mcp = FastMCP("Multi-language File Analyzer")


@mcp.tool()
def read_file(filepath: str) -> dict:
    """
    读取单个文件的完整内容（支持多种语言）

    支持的语言：Python (.py), Java (.java)

    Args:
        filepath: 文件路径

    Returns:
        文件内容和元数据
    """
    return get_file_content(filepath)


@mcp.tool()
def analyze_imports(filepath: str, project_root: str = None) -> dict:
    """
    分析文件的导入依赖（自动识别语言）

    支持的语言：
    - Python: import, from...import 语句
    - Java: import 语句（包括 static import）

    Args:
        filepath: 文件路径
        project_root: 项目根目录（可选，自动检测）

    Returns:
        {
            "language": "检测到的语言",
            "local_imports": ["本地依赖列表"],
            "external_imports": ["外部库列表"]
        }
    """
    return analyze_file_imports(filepath, project_root)


@mcp.tool()
def get_deps_tree(filepath: str, max_depth: int = 2, project_root: str = None) -> dict:
    """
    获取多语言项目的依赖树结构

    Args:
        filepath: 起始文件
        max_depth: 最大深度
        project_root: 项目根目录

    Returns:
        完整依赖树
    """
    return get_dependency_tree(filepath, max_depth, project_root)


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        print("收到SSE请求")
        try:
            async with sse.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,
            ) as (read_stream, write_stream):
                print("开始运行mcp_server")
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
        except Exception as e:
            print(f"SSE连接异常: {e}")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    import argparse

    parser = argparse.ArgumentParser(description='运行多语言文件分析MCP服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机地址')
    parser.add_argument('--port', type=int, default=8080, help='监听的端口号')
    args = parser.parse_args()

    starlette_app = create_starlette_app(mcp_server, debug=True)
    print(f"支持的文件类型: {ParserFactory.get_supported_extensions()}")
    uvicorn.run(starlette_app, host=args.host, port=args.port)
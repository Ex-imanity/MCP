from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from tools.read_file import get_file_content, get_file_imports, get_dependency_tree

mcp = FastMCP("read file recursively")


# 注册多个独立的工具
@mcp.tool()
def read_file(filepath: str) -> dict:
    """
    读取单个文件的完整内容

    Args:
        filepath: 文件的绝对路径或相对路径

    Returns:
        包含文件路径、内容和状态的字典
    """
    return get_file_content(filepath)


@mcp.tool()
def analyze_file_imports(filepath: str, project_root: str = None) -> dict:
    """
    分析Python文件的导入语句，返回依赖信息。

    这个工具只返回文件路径列表，不返回文件内容，非常节省token。
    建议先用这个工具了解依赖结构，再决定是否需要读取具体文件。

    Args:
        filepath: 要分析的Python文件路径
        project_root: 项目根目录（可选，会自动检测）

    Returns:
        {
            "filepath": "文件绝对路径",
            "project_root": "项目根目录",
            "local_imports": ["本地依赖文件路径列表"],
            "external_imports": ["外部库名称列表"],
            "import_details": [详细的导入信息],
            "status": "success" | "error"
        }

    使用建议：
    - 先调用此工具查看依赖列表
    - 根据需要再调用 read_file 读取具体文件内容
    """
    return get_file_imports(filepath, project_root)


@mcp.tool()
def get_dependency_tree_structure(filepath: str, max_depth: int = 3, project_root: str = None) -> dict:
    """
    获取文件的完整依赖树结构（仅包含路径，不包含文件内容）

    Args:
        filepath: 起始文件路径
        max_depth: 最大递归深度，默认为3
        project_root: 项目根目录（可选，会自动检测）

    Returns:
        依赖树结构，包含所有依赖文件的路径关系
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

    parser = argparse.ArgumentParser(description='运行基于SSE的MCP服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机地址')
    parser.add_argument('--port', type=int, default=8080, help='监听的端口号')
    args = parser.parse_args()

    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
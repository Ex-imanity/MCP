from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# 导入文件分析工具
from tools.file_analyzer import (
    get_file_content,
    analyze_file_imports,
    get_dependency_tree
)

# 导入目录分析工具（新增）
from tools.directory_analyzer import (
    list_directory,
    get_project_structure,
    find_entry_files
)

mcp = FastMCP("Multi-language File Analyzer")


# ========== 文件操作工具 ==========

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

    Args:
        filepath: 文件路径
        project_root: 项目根目录（可选，自动检测）

    Returns:
        依赖分析结果
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


# ========== 目录操作工具（新增）==========

@mcp.tool()
def browse_directory(
        dirpath: str,
        max_depth: int = 1,
        file_extensions: str = None,
        show_hidden: bool = False
) -> dict:
    """
    浏览目录结构，查看文件和子目录

    Args:
        dirpath: 目录路径
        max_depth: 递归深度（1=仅当前层，2=包含子目录一层）
        file_extensions: 仅显示特定类型文件，如 ".py,.java"（逗号分隔）
        show_hidden: 是否显示隐藏文件

    Returns:
        目录结构信息
    """
    extensions = None
    if file_extensions:
        extensions = [ext.strip() for ext in file_extensions.split(',')]

    return list_directory(
        dirpath=dirpath,
        max_depth=max_depth,
        include_extensions=extensions,
        show_hidden=show_hidden
    )


@mcp.tool()
def explore_project(dirpath: str, language: str = "all") -> dict:
    """
    智能探索项目结构（自动过滤常见无关文件）

    Args:
        dirpath: 项目根目录
        language: 项目语言类型 ("python", "java", "javascript", "all")

    Returns:
        项目结构概览
    """
    return get_project_structure(dirpath, language)


@mcp.tool()
def find_main_files(dirpath: str) -> dict:
    """
    查找项目的入口文件

    Args:
        dirpath: 项目根目录

    Returns:
        入口文件列表
    """
    return find_entry_files(dirpath)


# ========== Server 配置 ==========

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
    parser.add_argument('--port', type=int, default=8081, help='监听的端口号')
    args = parser.parse_args()

    starlette_app = create_starlette_app(mcp_server, debug=True)

    print("=" * 50)
    print("MCP Server 已启动")
    print("=" * 50)
    print("已注册的工具:")
    print("  📄 文件操作:")
    print("     - read_file: 读取文件内容")
    print("     - analyze_imports: 分析文件依赖")
    print("     - get_deps_tree: 获取依赖树")
    print("  📁 目录操作:")
    print("     - browse_directory: 浏览目录结构")
    print("     - explore_project: 智能探索项目")
    print("     - find_main_files: 查找入口文件")
    print("=" * 50)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
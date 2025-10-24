"""FastMCP服务器主逻辑"""

import argparse
import asyncio

from fastmcp import FastMCP

from .tools import register_all_tools


def create_server(name: str = "protein-mcp", version: str = "0.1.0") -> FastMCP:
    """创建并配置FastMCP服务器实例"""
    mcp = FastMCP(name=name, version=version)

    # 注册所有工具
    register_all_tools(mcp)

    return mcp


def main() -> None:
    """主入口点，支持命令行参数"""
    parser = argparse.ArgumentParser(description="Protein MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="传输协议 (默认: stdio)",
    )
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机 (默认: 0.0.0.0)")
    parser.add_argument("--name", default="protein-mcp", help="服务器名称 (默认: protein-mcp)")
    parser.add_argument("--version", default="0.1.0", help="服务器版本 (默认: 0.1.0)")

    args = parser.parse_args()

    # 创建服务器
    mcp = create_server(args.name, args.version)

    print("🧬 启动 Protein MCP Server")
    print(f"📦 版本: {args.version}")
    print(f"🌐 传输协议: {args.transport}")

    try:
        if args.transport == "stdio":
            print("🔌 STDIO模式启动")
            mcp.run()
        elif args.transport == "http":
            print(f"🌐 HTTP模式启动: http://{args.host}:{args.port}")
            asyncio.run(mcp.run_http_async(host=args.host, port=args.port))
        elif args.transport == "sse":
            print(f"📡 SSE模式启动: http://{args.host}:{args.port}")
            asyncio.run(mcp.run_sse_async(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()

import sys
from .tools import mcp


def print_help():
    """打印帮助信息"""
    help_text = """
Tushare Docs MCP Server - 提供 Tushare 接口文档查询功能

用法:
  tushare-docs-mcp [选项] [端口]

选项:
  stdio                     使用标准输入输出传输（适用于 Claude 等工具）
  http                      使用 HTTP 传输（默认）
  -h, --help               显示此帮助信息
  -v, --version            显示版本信息

参数:
  端口                      HTTP 模式下的端口号（可选，默认 8888）

示例:
  tushare-docs-mcp stdio                    # 使用 stdio 模式
  tushare-docs-mcp                          # 使用 HTTP 模式，端口 8888
  tushare-docs-mcp 8080                     # 使用 HTTP 模式，端口 8080
  tushare-docs-mcp http 8080                # 使用 HTTP 模式，端口 8080

Claude Desktop 配置:
  {
    "mcpServers": {
      "tushare-docs": {
        "command": "uvx",
        "args": ["tushare-docs-mcp", "stdio"]
      }
    }
  }
"""
    print(help_text.strip())


def print_version():
    """打印版本信息"""
    print("Tushare Docs MCP Server v0.0.1")


def main():
    """
    启动 Tushare Docs MCP 服务器
    支持不同的传输方式:
    - 不带参数或指定 http: 使用 HTTP 传输
    - 指定 stdio: 使用标准输入输出传输
    """
    # 处理帮助和版本选项
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print_help()
            return
        elif sys.argv[1] in ["-v", "--version"]:
            print_version()
            return

    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        # 使用 stdio 传输，适用于 Claude 等工具
        mcp.run(transport="stdio")
    else:
        # 默认使用 HTTP 传输，支持指定端口
        port = 8888  # 默认端口

        # 解析端口参数
        for arg in sys.argv[1:]:
            if arg.isdigit():
                port = int(arg)
                break

        mcp.settings.port = port
        print(f"Starting Tushare Docs MCP Server on port {port}...")
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
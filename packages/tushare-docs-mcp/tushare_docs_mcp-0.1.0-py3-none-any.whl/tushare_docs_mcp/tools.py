from importlib import resources

from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP("tushare-docs-mcp")

@mcp.tool()
def tushare_basic() -> str:
    """
    获取tushare库的基础用法说明
    Returns:
        str: markdown格式的说明文档
    """
    ref = (
        resources.files("tushare_docs_mcp")
        / "docs"
        / "tushare_basic.md"
    )
    return ref.read_text(encoding="utf-8")

@mcp.tool()
def tushare_docs_catalog() -> str:
    """
    获取tushare库的接口文档目录
    Returns:
        str: markdown格式的目录
    """
    ref = (
        resources.files("tushare_docs_mcp")
        / "docs"
        / "non-official"
        / "catalog.md"
    )
    return ref.read_text(encoding="utf-8")


@mcp.tool()
def tushare_docs(docs_path: str) -> str:
    """
    获取tushare库特定接口的文档
    Args:
        docs_path (str): 文档路径，目录间使用空格分隔，从 tushare_docs_catalog 获取。例子： "01_股票数据 01_基础数据 01_股票列表"
    Returns:
        str: markdown格式的接口文档
    """
    docs_arr = docs_path.split(" ")
    docs_arr[-1] = f'{docs_arr[-1]}.md'

    ref = (
        resources.files("tushare_docs_mcp")
        / "docs"
        / "non-official"
    )
    for docs_sub_path in docs_arr:
        ref = ref / docs_sub_path

    if not ref.is_file():
        return f"{docs_path} not found"
    else:
        return ref.read_text(encoding="utf-8")


from mcp.server.fastmcp import FastMCP

# 生成一个 MCP server
mcp = FastMCP("Demo")


# 添加一个 tool
@mcp.tool()
def price(a: int) -> int:
    """计算土豆的价格，输入a是几斤，每一斤7元，返回价格"""
    return a *7

  



def main() -> None:
    mcp.run(transport='stdio')  

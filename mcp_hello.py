from fastmcp import FastMCP

mcp = FastMCP(name="HelloWorldServer")

@mcp.tool()
def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run() 
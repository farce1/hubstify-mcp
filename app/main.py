from logging import INFO, basicConfig

from fastmcp import FastMCP

from app.config import settings
from app.mcp import mcp_router

basicConfig(level=INFO, format="[%(asctime)s - %(name)s] (%(levelname)s) %(message)s")


mcp = FastMCP(name=settings.mcp_server_name)


mcp.mount(mcp_router)


def run() -> None:
    if settings.mcp_transport == "http":
        mcp.run(transport="http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run()


if __name__ == "__main__":
    run()

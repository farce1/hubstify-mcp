from logging import INFO, basicConfig

from fastmcp import FastMCP

from app.config import settings
from app.mcp import mcp_router

basicConfig(level=INFO, format="[%(asctime)s - %(name)s] (%(levelname)s) %(message)s")


mcp = FastMCP(name=settings.mcp_server_name)


mcp.mount(mcp_router)


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()

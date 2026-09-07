from logging import INFO, basicConfig

from fastmcp import FastMCP

from app.config import settings
from app.mcp.tools import identity, people, projects, raw, time, writes

basicConfig(level=INFO, format="[%(asctime)s - %(name)s] (%(levelname)s) %(message)s")


mcp = FastMCP(name=settings.mcp_server_name)

for router in (
    identity.identity_router,
    projects.projects_router,
    people.people_router,
    time.time_router,
    writes.writes_router,
    raw.raw_router,
):
    mcp.mount(router)


def run() -> None:
    if settings.mcp_transport == "http":
        mcp.run(transport="http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run()


if __name__ == "__main__":
    run()

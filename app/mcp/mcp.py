from fastmcp import FastMCP

from app.mcp.tools import identity, people, projects, time, writes

mcp_router = FastMCP(name="Main MCP")

mcp_router.mount(identity.identity_router)
mcp_router.mount(projects.projects_router)
mcp_router.mount(people.people_router)
mcp_router.mount(time.time_router)
mcp_router.mount(writes.writes_router)

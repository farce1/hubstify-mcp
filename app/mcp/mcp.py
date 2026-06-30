from fastmcp import FastMCP

from app.mcp.tools import identity, people, projects

mcp_router = FastMCP(name="Main MCP")

mcp_router.mount(identity.identity_router)
mcp_router.mount(projects.projects_router)
mcp_router.mount(people.people_router)

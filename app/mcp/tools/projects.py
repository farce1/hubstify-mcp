from fastmcp import FastMCP

from app.domain.project import Project
from app.mcp.context import get_context
from app.mcp.support import bullet_list, safe

projects_router = FastMCP(name="Projects")


@projects_router.tool
@safe
async def get_projects(organization_id: int | None = None, status: str | None = None) -> str:
    """List projects in an organization (defaults to your default org). Optional status: active, archived, or all."""
    ctx = get_context()
    org_id = organization_id if organization_id is not None else await ctx.default_organization_id()
    projects = await ctx.projects.list_projects(org_id, status)
    lines = [_project_line(project) for project in projects]
    return bullet_list(f"Projects in organization {org_id}:", lines, "No projects found.")


@projects_router.tool
@safe
async def get_tasks(project_id: int, status: str | None = None) -> str:
    """List tasks in a project. Optional status: active or completed."""
    tasks = await get_context().tasks.list_tasks(project_id, status)
    lines = [f"{task.summary} (id {task.id}{f', {task.status}' if task.status else ''})" for task in tasks]
    return bullet_list(f"Tasks in project {project_id}:", lines, "No tasks found.")


def _project_line(project: Project) -> str:
    flags = [flag for flag in (project.status, "billable" if project.billable else None) if flag]
    suffix = f" [{', '.join(flags)}]" if flags else ""
    return f"{project.name} (id {project.id}){suffix}"

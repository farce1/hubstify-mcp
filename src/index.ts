#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { HubstaffClient, HubstaffError } from "./hubstaff.js";

const refreshToken = process.env.HUBSTAFF_REFRESH_TOKEN;
if (!refreshToken) {
  console.error(
    "[hubstify-mcp] Missing HUBSTAFF_REFRESH_TOKEN environment variable.\n" +
      "Generate a Personal Access Token at https://developer.hubstaff.com/personal_access_tokens"
  );
  process.exit(1);
}

const client = new HubstaffClient({
  refreshToken,
  tokenStorePath: process.env.HUBSTAFF_TOKEN_STORE,
});

const server = new McpServer({
  name: "hubstify-mcp",
  version: "0.1.0",
});

/** Wrap a Hubstaff call so every tool returns MCP-shaped content + clean errors. */
async function run(fn: () => Promise<unknown>) {
  try {
    const data = await fn();
    return {
      content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
    };
  } catch (err) {
    const message =
      err instanceof HubstaffError
        ? `${err.message}\n${JSON.stringify(err.body, null, 2)}`
        : err instanceof Error
          ? err.message
          : String(err);
    return {
      content: [{ type: "text" as const, text: `Error: ${message}` }],
      isError: true,
    };
  }
}

const pagination = {
  page_start_id: z
    .number()
    .optional()
    .describe("Cursor id to start the page from (for pagination)."),
  page_limit: z
    .number()
    .min(1)
    .max(500)
    .optional()
    .describe("Number of records per page (max 500)."),
};

// ── Account / identity ────────────────────────────────────────────────────────

server.registerTool(
  "hubstaff_get_current_user",
  {
    title: "Get current user",
    description:
      "Get the authenticated Hubstaff user (the owner of the access token).",
    inputSchema: {},
  },
  () => run(() => client.request("/users/me"))
);

server.registerTool(
  "hubstaff_list_organizations",
  {
    title: "List organizations",
    description:
      "List Hubstaff organizations the authenticated user has access to. Use the returned organization id for project, member and activity tools.",
    inputSchema: { ...pagination },
  },
  ({ page_start_id, page_limit }) =>
    run(() =>
      client.request("/organizations", { query: { page_start_id, page_limit } })
    )
);

// ── Projects ──────────────────────────────────────────────────────────────────

server.registerTool(
  "hubstaff_list_projects",
  {
    title: "List projects",
    description: "List projects within an organization.",
    inputSchema: {
      organization_id: z.number().describe("Organization id."),
      status: z
        .enum(["active", "archived"])
        .optional()
        .describe("Filter by project status."),
      ...pagination,
    },
  },
  ({ organization_id, status, page_start_id, page_limit }) =>
    run(() =>
      client.request(`/organizations/${organization_id}/projects`, {
        query: { status, page_start_id, page_limit },
      })
    )
);

server.registerTool(
  "hubstaff_get_project",
  {
    title: "Get project",
    description: "Get a single project by id.",
    inputSchema: { project_id: z.number().describe("Project id.") },
  },
  ({ project_id }) => run(() => client.request(`/projects/${project_id}`))
);

// ── Members ───────────────────────────────────────────────────────────────────

server.registerTool(
  "hubstaff_list_members",
  {
    title: "List organization members",
    description: "List members (users) of an organization.",
    inputSchema: {
      organization_id: z.number().describe("Organization id."),
      ...pagination,
    },
  },
  ({ organization_id, page_start_id, page_limit }) =>
    run(() =>
      client.request(`/organizations/${organization_id}/members`, {
        query: { page_start_id, page_limit },
      })
    )
);

// ── Tasks ─────────────────────────────────────────────────────────────────────

server.registerTool(
  "hubstaff_list_tasks",
  {
    title: "List project tasks",
    description: "List tasks belonging to a project.",
    inputSchema: {
      project_id: z.number().describe("Project id."),
      status: z
        .enum(["active", "completed"])
        .optional()
        .describe("Filter by task status."),
      ...pagination,
    },
  },
  ({ project_id, status, page_start_id, page_limit }) =>
    run(() =>
      client.request(`/projects/${project_id}/tasks`, {
        query: { status, page_start_id, page_limit },
      })
    )
);

server.registerTool(
  "hubstaff_create_task",
  {
    title: "Create task",
    description: "Create a new task within a project.",
    inputSchema: {
      project_id: z.number().describe("Project id the task belongs to."),
      summary: z.string().describe("Task summary / title."),
      details: z.string().optional().describe("Optional task details."),
      assignee_ids: z
        .array(z.number())
        .optional()
        .describe("User ids to assign the task to."),
    },
  },
  ({ project_id, summary, details, assignee_ids }) =>
    run(() =>
      client.request(`/projects/${project_id}/tasks`, {
        method: "POST",
        body: {
          task: {
            summary,
            ...(details ? { details } : {}),
            ...(assignee_ids ? { assignee_ids } : {}),
          },
        },
      })
    )
);

// ── Time tracking / activities ────────────────────────────────────────────────

server.registerTool(
  "hubstaff_list_activities",
  {
    title: "List activities",
    description:
      "List tracked time activities for an organization within a time range. Times are ISO 8601 (e.g. 2024-01-01T00:00:00Z).",
    inputSchema: {
      organization_id: z.number().describe("Organization id."),
      time_slot_start: z
        .string()
        .describe("Start of the range, ISO 8601 timestamp."),
      time_slot_stop: z
        .string()
        .describe("End of the range, ISO 8601 timestamp."),
      user_ids: z.array(z.number()).optional().describe("Filter by user ids."),
      project_ids: z
        .array(z.number())
        .optional()
        .describe("Filter by project ids."),
      ...pagination,
    },
  },
  ({
    organization_id,
    time_slot_start,
    time_slot_stop,
    user_ids,
    project_ids,
    page_start_id,
    page_limit,
  }) =>
    run(() =>
      client.request(`/organizations/${organization_id}/activities`, {
        query: {
          "time_slot[start]": time_slot_start,
          "time_slot[stop]": time_slot_stop,
          user_ids,
          project_ids,
          page_start_id,
          page_limit,
        },
      })
    )
);

server.registerTool(
  "hubstaff_daily_activities",
  {
    title: "Daily activities summary",
    description:
      "Get per-day aggregated tracked-time activities for an organization over a date range (dates are YYYY-MM-DD).",
    inputSchema: {
      organization_id: z.number().describe("Organization id."),
      date_start: z.string().describe("Start date, YYYY-MM-DD."),
      date_stop: z.string().describe("End date, YYYY-MM-DD."),
      user_ids: z.array(z.number()).optional().describe("Filter by user ids."),
      project_ids: z
        .array(z.number())
        .optional()
        .describe("Filter by project ids."),
      ...pagination,
    },
  },
  ({
    organization_id,
    date_start,
    date_stop,
    user_ids,
    project_ids,
    page_start_id,
    page_limit,
  }) =>
    run(() =>
      client.request(`/organizations/${organization_id}/activities/daily`, {
        query: {
          "date[start]": date_start,
          "date[stop]": date_stop,
          user_ids,
          project_ids,
          page_start_id,
          page_limit,
        },
      })
    )
);

// ── Escape hatch: raw request ─────────────────────────────────────────────────

server.registerTool(
  "hubstaff_raw_request",
  {
    title: "Raw Hubstaff API request",
    description:
      "Perform an arbitrary authenticated request against the Hubstaff v2 API. Use this for endpoints not covered by a dedicated tool. Path is relative to https://api.hubstaff.com/v2 (e.g. '/organizations').",
    inputSchema: {
      method: z
        .enum(["GET", "POST", "PUT", "PATCH", "DELETE"])
        .default("GET")
        .describe("HTTP method."),
      path: z.string().describe("API path relative to the v2 base URL."),
      query: z
        .record(z.any())
        .optional()
        .describe("Query parameters as a key/value object."),
      body: z.any().optional().describe("JSON request body (for writes)."),
    },
  },
  ({ method, path, query, body }) =>
    run(() => client.request(path, { method, query, body }))
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[hubstify-mcp] Hubstaff MCP server running on stdio");
}

main().catch((err) => {
  console.error("[hubstify-mcp] Fatal error:", err);
  process.exit(1);
});

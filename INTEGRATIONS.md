# Integrations

Connect `hubstaff-mcp` to your MCP client. The server runs over **stdio** and is
launched with `uv`, so every client uses the same command:

```
uv --directory /absolute/path/to/hubstify-mcp run hubstaff-mcp
```

Replace `/absolute/path/to/hubstify-mcp` with the real path to your clone, and set
`HUBSTAFF_PERSONAL_ACCESS_TOKEN` to your Personal Access Token
([create one here](https://developer.hubstaff.com/account/personal-access-tokens)).

Prerequisites: [`uv`](https://docs.astral.sh/uv/) installed and `uv sync` run once
in the project directory.

---

## Claude Code

Add the server from the CLI (run from anywhere):

```bash
claude mcp add hubstaff \
  -e HUBSTAFF_PERSONAL_ACCESS_TOKEN=your_pat_here \
  -- uv --directory /absolute/path/to/hubstify-mcp run hubstaff-mcp
```

Then `claude mcp list` should show `hubstaff` connected. Use `-s user` to make it
available across all your projects.

---

## Claude Desktop / Claude Cowork

Claude Desktop (and Cowork, which shares the desktop app's local-MCP
configuration) reads `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hubstaff": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/hubstify-mcp", "run", "hubstaff-mcp"],
      "env": { "HUBSTAFF_PERSONAL_ACCESS_TOKEN": "your_pat_here" }
    }
  }
}
```

Restart Claude Desktop afterward. A ready-to-edit copy is in
[`claude_desktop_config.example.json`](./claude_desktop_config.example.json).

---

## Cursor

Create `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` for all projects):

```json
{
  "mcpServers": {
    "hubstaff": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/hubstify-mcp", "run", "hubstaff-mcp"],
      "env": { "HUBSTAFF_PERSONAL_ACCESS_TOKEN": "your_pat_here" }
    }
  }
}
```

Enable the server in Cursor's MCP settings if prompted.

---

## Codex

Codex CLI reads `~/.codex/config.toml`. Add an `mcp_servers` entry:

```toml
[mcp_servers.hubstaff]
command = "uv"
args = ["--directory", "/absolute/path/to/hubstify-mcp", "run", "hubstaff-mcp"]
env = { HUBSTAFF_PERSONAL_ACCESS_TOKEN = "your_pat_here" }
```

---

## Verifying

Once connected, try:

- *"Who am I on Hubstaff?"* → `get_current_user`
- *"Show my time entries for this week."* → `get_time_entries`
- *"Give me my timesheet summary for last month."* → `get_timesheet`
- *"What projects and tasks am I assigned to?"* → `get_projects` + `get_tasks`
- *"Log 2 hours to project Acme today with note 'API integration'."* → `log_time`

> Editing or deleting a tracked-time entry is not supported by the Hubstaff v2 API;
> do that in the Hubstaff web app.

## Troubleshooting

- **`HUBSTAFF_PERSONAL_ACCESS_TOKEN is not set`** — the env var didn't reach the server;
  check the `env` block in your client config.
- **Auth errors after it worked before** — the refresh token may have been revoked
  or rotated out of band. Update `HUBSTAFF_PERSONAL_ACCESS_TOKEN` and delete
  `~/.hubstaff-mcp/tokens.json`.
- **Wrong day for "today"/"this week"** — set `DEFAULT_TIMEZONE` (e.g.
  `Europe/Warsaw`) in the `env` block; Hubstaff buckets daily activity by timezone.

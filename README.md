# hubstaff-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for
[Hubstaff](https://hubstaff.com). Operate your Hubstaff organizations, projects,
tasks, members, tracked-time activities and timesheets through any MCP-compatible
LLM client — read your timesheet, log time, and inspect your team in natural
language.

Built on [FastMCP](https://gofastmcp.com) and scaffolded from
[`the-momentum/python-ai-kit`](https://github.com/the-momentum/python-ai-kit).

## Connect it to your LLM

You need two things: a Hubstaff Personal Access Token, and one config entry in your
client. **No clone required** — [`uv`](https://docs.astral.sh/uv/) runs the server
straight from GitHub.

**1. Get a Personal Access Token** at
[developer.hubstaff.com/account/personal-access-tokens](https://developer.hubstaff.com/account/personal-access-tokens).
That's the value of `HUBSTAFF_PERSONAL_ACCESS_TOKEN` in the steps below.

**2. Add the server to your client:**

### Claude Code

```bash
claude mcp add hubstaff \
  -e HUBSTAFF_PERSONAL_ACCESS_TOKEN=your_pat_here \
  -- uvx --from git+https://github.com/farce1/hubstify-mcp.git hubstaff-mcp
```

`claude mcp list` should then show `hubstaff` connected. Add `-s user` to enable it
across all your projects.

### Claude Desktop / Claude Cowork

Edit `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`,
Windows: `%APPDATA%\Claude\`). Cowork shares the same desktop MCP configuration:

```json
{
  "mcpServers": {
    "hubstaff": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/farce1/hubstify-mcp.git", "hubstaff-mcp"],
      "env": { "HUBSTAFF_PERSONAL_ACCESS_TOKEN": "your_pat_here" }
    }
  }
}
```

Restart the app afterward. A ready-to-edit copy is in
[`claude_desktop_config.example.json`](./claude_desktop_config.example.json).

### Cursor

Create `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` for all projects)
with the **same `mcpServers` block** shown above for Claude Desktop.

### Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.hubstaff]
command = "uvx"
args = ["--from", "git+https://github.com/farce1/hubstify-mcp.git", "hubstaff-mcp"]
env = { HUBSTAFF_PERSONAL_ACCESS_TOKEN = "your_pat_here" }
```

> **Prefer a local clone?** After `git clone … && uv sync`, replace the launch
> command everywhere above with
> `uv --directory /absolute/path/to/hubstify-mcp run hubstaff-mcp`.

**3. Try it** — ask your assistant:

- *"Who am I on Hubstaff?"* → `get_current_user`
- *"Show my tracked time this week."* → `get_time_entries`
- *"Give me my timesheet summary for last month."* → `get_timesheet`
- *"What projects and tasks am I assigned to?"* → `get_projects` + `get_tasks`
- *"Log 2 hours to project Acme today with note 'API integration'."* → `log_time`

## Tools

| Tool | Kind | Description |
| --- | --- | --- |
| `get_current_user` | read | The authenticated user (you) |
| `get_organizations` | read | Organizations you belong to |
| `get_projects` | read | Projects in an organization (defaults to your default org) |
| `get_tasks` | read | Tasks in a project |
| `get_members` | read | Members of an organization |
| `get_teams` | read | Teams in an organization |
| `get_time_entries` | read | Your tracked time per day for a period (optional project filter) |
| `get_timesheet` | read | Your tracked time summarised per project for a period |
| `log_time` | create | Create a manual time entry for yourself |
| `create_task` | create | Create a task in a project |
| `hubstaff_get` | read | Guarded raw GET for `organizations/*`, `users/*`, `projects/*` |

> **Hubstaff v2 limitation:** time entries are **create-only**. The v2 API has no
> endpoint to edit or delete a tracked-time entry, so this server intentionally does
> not expose update/delete tools — do that in the Hubstaff web app. Tracked time is
> read via daily activities.

## Highlights

- 🔑 PAT auth with automatic access-token refresh **and rotation handling** (the
  rotated refresh token is persisted; the token endpoint's 5/hour limit is respected)
- ⏱️ Read tracked time and per-project timesheets over natural periods
  ("this week", "last month", …)
- ✍️ Log manual time entries and create tasks
- 🛡️ Rate-limit aware (honors `Retry-After`, backs off on 5xx) with cursor pagination
- 🧰 A guarded read-only escape hatch for endpoints without a dedicated tool

## Other ways to install

The config above needs no clone, but the same `hubstaff-mcp` command is available via:

```bash
uv tool install git+https://github.com/farce1/hubstify-mcp.git   # persistent, on PATH
pipx run --spec git+https://github.com/farce1/hubstify-mcp.git hubstaff-mcp   # pipx
pip install git+https://github.com/farce1/hubstify-mcp.git       # into a venv

# From source (development):
git clone https://github.com/farce1/hubstify-mcp.git && cd hubstify-mcp && uv sync
```

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HUBSTAFF_PERSONAL_ACCESS_TOKEN` | ✅ | — | Your Hubstaff Personal Access Token |
| `HUBSTAFF_TOKEN_STORE` | — | `~/.hubstaff-mcp/tokens.json` | Where the rotated token cache is persisted |
| `HUBSTAFF_DEFAULT_ORGANIZATION_ID` | — | first org | Organization id used when a tool isn't given one |
| `DEFAULT_TIMEZONE` | — | `UTC` | IANA timezone for resolving "today"/"this week" and localizing naive start times |
| `MCP_TRANSPORT` | — | `stdio` | `stdio` for local clients, or `http` to self-host (see below) |
| `MCP_HOST` | — | `127.0.0.1` | Bind address when `MCP_TRANSPORT=http` |
| `MCP_PORT` | — | `8000` | Port when `MCP_TRANSPORT=http` |

> Hubstaff rotates the refresh token on every exchange; this server persists the
> newest token (mode `0600`) so it survives restarts. If you revoke the token,
> update `HUBSTAFF_PERSONAL_ACCESS_TOKEN` and delete the token store file.

## Troubleshooting

- **`HUBSTAFF_PERSONAL_ACCESS_TOKEN is not set`** — the env var didn't reach the
  server; check the `env` block in your client config.
- **Auth errors after it worked before** — the token may have been revoked or
  rotated out of band. Update `HUBSTAFF_PERSONAL_ACCESS_TOKEN` and delete
  `~/.hubstaff-mcp/tokens.json`.
- **Wrong day for "today"/"this week"** — set `DEFAULT_TIMEZONE` (e.g.
  `Europe/Warsaw`); Hubstaff buckets daily activity by timezone.

## Self-hosting over HTTP

By default the server talks **stdio** (the client spawns it as a subprocess). To run
it as a long-lived HTTP service instead, set `MCP_TRANSPORT=http`:

```bash
HUBSTAFF_PERSONAL_ACCESS_TOKEN=your_pat MCP_TRANSPORT=http MCP_PORT=8000 \
  uvx --from git+https://github.com/farce1/hubstify-mcp.git hubstaff-mcp
```

The endpoint is then `http://<host>:<port>/mcp`, which any HTTP-capable MCP client
can connect to.

> ⚠️ **Single-user only.** The server acts as the *one* identity behind
> `HUBSTAFF_PERSONAL_ACCESS_TOKEN` — every request reads and writes that account's
> Hubstaff data. Do **not** expose this endpoint to other people or the public
> internet; keep it bound to localhost or your private network and put your own
> authentication in front of it. Multi-tenant hosting (each user with their own
> Hubstaff token) is not yet supported.

## Development

```bash
make install     # uv sync --all-groups
make test        # pytest
make lint        # ruff check
make typecheck   # ty check
make check       # lint + typecheck + tests + format check
```

## Architecture

A thin, layered design (each layer has one responsibility):

```
app/
├── domain/        # Pydantic models + value objects (Duration, DateRange)
├── hubstaff/      # auth (token rotation) + HTTP client (retry, pagination)
├── repositories/  # one per aggregate: endpoints + envelope -> domain models
├── services/      # use-case logic (date normalization, timesheet projection)
└── mcp/           # FastMCP tools (thin adapters) + composition root
```

## License

MIT — see [LICENSE](./LICENSE).

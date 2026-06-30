# hubstaff-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for
[Hubstaff](https://hubstaff.com). Operate your Hubstaff organizations, projects,
tasks, members, tracked-time activities and timesheets through any MCP-compatible
LLM client — read your timesheet, log time, and inspect your team in natural
language.

Built on [FastMCP](https://gofastmcp.com) and scaffolded from
[`the-momentum/python-ai-kit`](https://github.com/the-momentum/python-ai-kit).

## Features

- 🔑 PAT auth with automatic access-token refresh **and rotation handling** (the
  rotated refresh token is persisted; the token endpoint's 5/hour limit is respected)
- ⏱️ Read your tracked time and per-project timesheets over natural periods
  ("this week", "last month", …)
- ✍️ Log manual time entries and create tasks
- 🛡️ Rate-limit aware (honors `Retry-After`, backs off on 5xx) with cursor pagination
- 🧰 A guarded read-only escape hatch for endpoints without a dedicated tool

## Tools

| Tool | Kind | Description |
| --- | --- | --- |
| `get_current_user` | read | The authenticated user (you) |
| `get_organizations` | read | Organizations you belong to |
| `get_projects` | read | Projects in an organization (defaults to your primary) |
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

## Setup

### 1. Install [`uv`](https://docs.astral.sh/uv/) and build

```bash
git clone https://github.com/farce1/hubstify-mcp.git
cd hubstify-mcp
uv sync
```

### 2. Get a Hubstaff Personal Access Token

Create one at
[developer.hubstaff.com/account/personal-access-tokens](https://developer.hubstaff.com/account/personal-access-tokens).
The token is a long-lived refresh token; set it as `HUBSTAFF_REFRESH_TOKEN`.

### 3. Run

```bash
HUBSTAFF_REFRESH_TOKEN=your_pat uv run hubstaff-mcp
```

The server speaks MCP over **stdio**. To connect it to Claude Code, Claude
Desktop/Cowork, Cursor or Codex, see **[INTEGRATIONS.md](./INTEGRATIONS.md)**.

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HUBSTAFF_REFRESH_TOKEN` | ✅ | — | Personal Access Token (refresh token) |
| `HUBSTAFF_TOKEN_STORE` | — | `~/.hubstaff-mcp/tokens.json` | Where the rotated token cache is persisted |
| `DEFAULT_TIMEZONE` | — | `UTC` | IANA timezone for resolving "today"/"this week" and localizing naive start times |

> Hubstaff rotates the refresh token on every exchange; this server persists the
> newest token (mode `0600`) so it survives restarts. If you revoke the token,
> update `HUBSTAFF_REFRESH_TOKEN` and delete the token store file.

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

# hubstify-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for
[Hubstaff](https://hubstaff.com). It lets any MCP-compatible LLM client (Claude
Desktop, Claude Code, Cursor, etc.) read and operate Hubstaff data — organizations,
projects, members, tasks and tracked-time activities — through natural language.

## Features

- 🔑 OAuth2 refresh-token auth with automatic token refresh **and rotation handling**
- 🏢 List organizations, projects and members
- ✅ List and create tasks
- ⏱️ Query tracked-time activities (raw and daily-aggregated)
- 🧰 `hubstaff_raw_request` escape hatch for any other Hubstaff v2 endpoint

## Tools

| Tool | Description |
| --- | --- |
| `hubstaff_get_current_user` | Get the authenticated user |
| `hubstaff_list_organizations` | List organizations |
| `hubstaff_list_projects` | List projects in an organization |
| `hubstaff_get_project` | Get a project by id |
| `hubstaff_list_members` | List members of an organization |
| `hubstaff_list_tasks` | List tasks in a project |
| `hubstaff_create_task` | Create a task in a project |
| `hubstaff_list_activities` | List tracked-time activities in a time range |
| `hubstaff_daily_activities` | Per-day aggregated activities over a date range |
| `hubstaff_raw_request` | Arbitrary authenticated Hubstaff v2 request |

## Setup

### 1. Get a Hubstaff Personal Access Token

Create one at
[developer.hubstaff.com/personal_access_tokens](https://developer.hubstaff.com/personal_access_tokens).
This is a long-lived refresh token used to mint short-lived access tokens.

### 2. Install & build

```bash
git clone https://github.com/farce1/hubstify-mcp.git
cd hubstify-mcp
npm install
npm run build
```

### 3. Configure your MCP client

Add the server to your client config (example for Claude Desktop /
`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hubstaff": {
      "command": "node",
      "args": ["/absolute/path/to/hubstify-mcp/dist/index.js"],
      "env": {
        "HUBSTAFF_REFRESH_TOKEN": "your_personal_access_token_here"
      }
    }
  }
}
```

For Claude Code:

```bash
claude mcp add hubstaff -e HUBSTAFF_REFRESH_TOKEN=your_token -- node /absolute/path/to/hubstify-mcp/dist/index.js
```

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `HUBSTAFF_REFRESH_TOKEN` | ✅ | Personal Access Token (refresh token) |
| `HUBSTAFF_TOKEN_STORE` | — | Path for the persisted token cache (default `~/.hubstify-mcp/token.json`) |

> **Note on token rotation:** Hubstaff rotates the refresh token every time it is
> exchanged for an access token. This server persists the newest token to the token
> store so it survives restarts. If you rotate or revoke the token in Hubstaff,
> update `HUBSTAFF_REFRESH_TOKEN` and delete the token store file.

## Development

```bash
npm run dev    # tsc --watch
npm run build  # compile to dist/
npm start      # run the built server
```

## License

MIT — see [LICENSE](./LICENSE).

# hubstaff-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server for
[Hubstaff](https://hubstaff.com). Operate your Hubstaff organizations, projects,
tasks, members, tracked-time activities and timesheets through any MCP-compatible
LLM client (Claude Code, Claude Desktop/Cowork, Cursor, Codex).

Built on [FastMCP](https://gofastmcp.com) and scaffolded from
[`the-momentum/python-ai-kit`](https://github.com/the-momentum/python-ai-kit).

> 🚧 Under construction. See `docs/` for the design spec.

## Quick start

```bash
uv sync
HUBSTAFF_REFRESH_TOKEN=your_pat uv run hubstaff-mcp
```

Get a Personal Access Token at
<https://developer.hubstaff.com/account/personal-access-tokens>.

## License

MIT — see [LICENSE](./LICENSE).

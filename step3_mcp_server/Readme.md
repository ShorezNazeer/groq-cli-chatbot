# MCP Filesystem Server

A sandboxed [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that exposes filesystem and shell tools to any MCP-compatible AI client — Claude Desktop, Claude Code, or a custom-built assistant.

Unlike hardcoding tool logic directly into a chatbot script, this server runs standalone. Any MCP client can connect to it and immediately gain the ability to browse files, read them, and run shell commands — without that client needing its own implementation of any of it.

## Tools

| Tool | Description |
|---|---|
| `list_directory(path)` | Lists files and folders inside the sandbox |
| `read_file(path)` | Reads and returns a file's text contents |
| `run_shell_command(command)` | Runs a shell command and returns its output |

## Safety model

Filesystem and shell access is powerful and needs real guardrails, not just correct-looking code. This server enforces two:

- **Sandbox confinement** — every tool call is restricted to one base directory. Any path that resolves outside it (e.g. `../../etc/passwd`) is rejected before anything is read or written.
- **Command denylist** — `run_shell_command` refuses any command containing a destructive or network-facing pattern (`rm`, `sudo`, `curl`, `wget`, `mv`, `dd`, `>`) before execution.

Both were manually tested against real escape attempts (path traversal, `rm -rf`) via the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and confirmed to block them, not just theoretically prevent them.

## Setup

```bash
python -m venv venv# MCP Filesystem Server

A sandboxed [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that exposes filesystem and shell tools to any MCP-compatible AI client — Claude Desktop, Claude Code, or a custom-built assistant.

Unlike hardcoding tool logic directly into a chatbot script, this server runs standalone. Any MCP client can connect to it and immediately gain the ability to browse files, read them, and run shell commands — without that client needing its own implementation of any of it.

## Tools

| Tool | Description |
|---|---|
| `list_directory(path)` | Lists files and folders inside the sandbox |
| `read_file(path)` | Reads and returns a file's text contents |
| `run_shell_command(command)` | Runs a shell command and returns its output |

## Safety model

Filesystem and shell access is powerful and needs real guardrails, not just correct-looking code. This server enforces two:

- **Sandbox confinement** — every tool call is restricted to one base directory. Any path that resolves outside it (e.g. `../../etc/passwd`) is rejected before anything is read or written.
- **Command denylist** — `run_shell_command` refuses any command containing a destructive or network-facing pattern (`rm`, `sudo`, `curl`, `wget`, `mv`, `dd`, `>`) before execution.

Both were manually tested against real escape attempts (path traversal, `rm -rf`) via the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and confirmed to block them, not just theoretically prevent them.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install "mcp[cli]<2"
```

## Running it

Test interactively with the MCP Inspector:

```bash
mcp dev mcp_server.py
```

This opens a local web UI where you can call each tool by hand and inspect the results.

To run the server directly (for a real MCP client to connect to):

```bash
python mcp_server.py
```

## Notes

- Requires Node.js/npm (for the Inspector's web UI) and [`uv`](https://github.com/astral-sh/uv) (used to launch the server process).
- Currently pinned to `mcp<2` for compatibility with the `FastMCP` API; the SDK's v2 release renamed this to `MCPServer`.

## Part of a larger project

This is Step 3 of a roadmap to learn agentic AI architecture, building toward a Claude-API-powered rebuild of an [n8n calendar-booking agent](https://github.com/ShorezNazeer). See [groq-cli-chatbot](https://github.com/ShorezNazeer/groq-cli-chatbot) for Steps 1–2 (a CLI chatbot with tool-use/function-calling).
source venv/bin/activate
pip install "mcp[cli]<2"
```

## Running it

Test interactively with the MCP Inspector:

```bash
mcp dev mcp_server.py
```

This opens a local web UI where you can call each tool by hand 

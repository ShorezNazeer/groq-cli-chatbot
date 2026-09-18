# Mini Claude Code

A small agentic coding CLI built with Groq, made as a hands-on alternative to Anthropic's
Claude Code — built to understand the architecture rather than pay for the product.

## Why this exists

Claude Code requires a paid Anthropic subscription or metered API billing. Rather than
spend money just to *use* an agent, this reimplements its core architecture — plan, act,
observe, repeat — on top of the tools already built in Step 3 (`mcp_server.py`), using
Groq's free tier.

## Architecture

- **Plan → act → observe loop**: the model is asked to lay out a short plan before
  touching any tools, then executes it step by step, seeing each tool's result before
  deciding its next move.
- **Human-in-the-loop confirmation**: any file write or shell command pauses and shows
  exactly what's about to happen, waiting for explicit `y`/`n` before proceeding.
- **Sandboxing**: every file operation is resolved and checked against a sandbox folder
  (`_safe_path`), blocking path-escape attempts like `../../etc/passwd`.
- **Command denylist**: shell commands are checked against a blocklist (`rm `, `sudo`,
  `curl`, `>`, etc.) before they're even offered for confirmation.
- **Persistent session memory**: conversation history carries across multiple tasks in
  one run, so a declined action is remembered on the next request instead of being
  retried blind.

## Tools available to the agent

| Tool | Description | Confirmation required |
|---|---|---|
| `list_directory` | Lists files/folders in the sandbox | No |
| `read_file` | Reads a file's contents | No |
| `write_file` | Creates/overwrites a file | Yes |
| `run_shell_command` | Runs a shell command in the sandbox | Yes (and denylist-checked) |

## Usage

```bash
python mini_claude_code.py
```

Then type a task, e.g.:
- `create a file called notes.txt with 3 todo items`
- `read notes.txt and summarize it into summary.txt`

Type `quit` to exit.

## Bugs found and fixed during testing

Two real agent bugs surfaced through hands-on testing (not just written and assumed
correct):

1. **Conversation history was rebuilt from scratch on every task**, so a declined
   write had no memory on the next request. Fixed by persisting `messages` across the
   whole session instead of inside a single `run_agent()` call.
2. **Completion detection assumed the model always plans on its very first response**
   (checked `iteration == 0`). In practice the model sometimes explores with tools
   first and plans afterward, which caused the agent to silently stop without ever
   acting. Fixed by tracking a `took_action` flag instead of relying on iteration
   position.

## What this isn't

This is a deliberately minimal teaching version, not a production tool: no context
compression for long sessions, no multi-file awareness, no git integration, and model
behavior is non-deterministic between runs (order of actions can vary on identical
prompts).

# Agentic AI Roadmap: building a Claude-Code-style agent from scratch

A hands-on project that builds an AI agent step by step on Groq's free tier, from a basic chatbot up to a small agentic coding CLI. Each step adds one idea and has working, tested code.

## The steps

| Step | What it adds | Where |
|---|---|---|
| 1 | CLI chatbot using the Groq SDK | [`main.py`](main.py) |
| 2 | Tool use: Weather and Calculator tools; the model keeps calling tools until it no longer asks for any | [`tool_agent.py`](tool_agent.py) |
| 3 | MCP server exposing sandboxed `list_directory`, `read_file` and `run_shell_command`, with a command denylist | [`step3_mcp_server/`](step3_mcp_server/) |
| 4 | Agentic coding CLI: plan → act → observe loop, `write_file`, human confirmation before writes and shell commands, history kept across tasks | [`mini_claude_code.py`](mini_claude_code.py), [notes](README_mini_claude_code.md) |
| 5 | Robustness patterns: retry-with-backoff, reflection on tool results, context compression | [`agent_patterns.py`](agent_patterns.py), [`test_backoff.py`](test_backoff.py) |
| 6 | *Planned:* rebuild a Google Calendar booking agent directly on the API | not started |

## Setup

```bash
git clone https://github.com/ShorezNazeer/groq-cli-chatbot.git
cd groq-cli-chatbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GROQ_API_KEY="your-key-here"   
```

Get a free API key from the [Groq console](https://console.groq.com).

## Running

```bash
python main.py              # step 1
python tool_agent.py        # step 2
python mini_claude_code.py  # steps 4-5 (works inside ./sandbox)
python test_backoff.py      # tests the retry logic with a fake client
```

For the MCP server, see [`step3_mcp_server/README.md`](step3_mcp_server/README.md).

## Design notes

- **Layered safety.** The coding agent has a command denylist, a path sandbox, and a confirmation prompt before every write or shell command. Testing showed the model also refused a "delete everything" request on its own, independent of the denylist.
- **Don't assume the happy path.** Model output order isn't deterministic, so completion is detected by tracking whether the agent actually acted rather than by turn position.
- **No exception ≠ success.** A shell command can fail without raising a Python error. Tool results return structured `success` / `exit_code` / `stderr`, and a reflection message makes failures impossible for the model to miss. Writes are read back and compared.
- **Transient failures.** API calls retry with exponential backoff and jitter on rate limits, timeouts and 5xx errors, and fail fast on errors like a bad API key.
- **Long sessions.** Older turns are summarized once the history grows, and the system prompt is always kept.

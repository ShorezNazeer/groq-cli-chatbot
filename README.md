# Groq CLI Chatbot

A command-line chatbot built using Claude/agentic AI architecture 

## Why Groq instead of Claude?

This project was originally built against the Anthropic API, but was switched to Groq's free tier to allow building and testing the full roadmap (chatbot → tool use → MCP → agentic patterns) at zero cost. The flagship project later in the roadmap will swap back to the Claude API directly.

Since Groq's API is OpenAI-compatible, the core patterns here (message history, chat completions, model calls) transfer directly to Claude and other LLM APIs with minimal changes.

## What it does

A simple, multi-turn CLI chatbot:
- Maintains conversation history across turns (not just single-shot Q&A)
- Streams user input from the terminal and prints model responses
- Runs on Groq's `openai/gpt-oss-120b` model via their free, fast LPU-based inference

## Setup

1. Clone this repo and create a virtual environment:
```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install groq
```

2. Get a free API key from [console.groq.com](https://console.groq.com/keys) (no credit card required).

3. Export it in your shell config:
```bash
   export GROQ_API_KEY="your-key-here"
```

4. Run it:
```bash
   python main.py
```
## Step 2: Tool Use / Function Calling — `tool_agent.py`

Extends the base chatbot with tool use (function calling). The model can request
that a real function be run — instead of guessing an answer — then uses the
actual result to respond.

**Tools implemented:**
- `get_weather(city)` — fetches live weather data from [wttr.in](https://wttr.in)
- `calculate(expression)` — evaluates a math expression

**How it works:**
1. Send the user's message to the model along with a schema describing the
   available tools.
2. If the model requests a tool call, run the real Python function and send
   the result back to the model.
3. The model uses that real data to generate its final natural-language reply.

This demonstrates the two-call tool-use pattern used by most LLM agent frameworks —
the model decides *what* to call, the code executes it, and the result is fed
back for a grounded final answer.

Run it with:
\```bash
python tool_agent.py
\```



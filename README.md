# Groq CLI Chatbot

A command-line chatbot built as Step 1 of a hands-on roadmap to learn Claude/agentic AI architecture — starting with API fundamentals before moving into tool use, MCP, and multi-step agent design.

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

## Notes / lessons learned

- Groq deprecated `llama-3.3-70b-versatile` for free-tier use partway through this build, which surfaced a real lesson in model-lifecycle management for anyone building on third-party LLM APIs — model IDs aren't permanent, and production code should treat them as configurable rather than hardcoded.

## Roadmap this fits into

1. **Claude API fundamentals (this project)** — CLI chatbot
2. Tool use / function calling — Weather + Calculator agent
3. MCP (Model Context Protocol) — small MCP server
4. Claude Code hands-on — practicing on own repos
5. Agentic design patterns — verify-loop mini-project
6. Flagship project — rebuild an n8n calendar-booking agent using the Claude API directly with real tool use
7. Documentation for GitHub/LinkedIn

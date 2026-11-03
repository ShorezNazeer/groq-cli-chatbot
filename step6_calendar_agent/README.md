# Step 6: Calendar Agent

A command-line assistant that manages Google Calendar in plain English ("is tomorrow 5pm free?", "book a call on Friday at 3pm"). I first built this as an n8n workflow, then rebuilt it in Python to understand what the platform was hiding: the tool loop, error handling, and safety gates.

## How it works

1. You type a request.
2. The model (Groq, `openai/gpt-oss-120b`) decides which calendar tool to call.
3. The tool runs against the real Google Calendar API and returns a structured result.
4. The model reads the result and answers, or calls another tool.

Tools: `list_events`, `check_availability`, `create_event`, `delete_event`.

## Setup

1. Create a Google Cloud project, enable the Google Calendar API, configure the OAuth consent screen (External, Testing mode) and add yourself as a test user.
2. Create an OAuth client ID of type **Desktop app**, download it, and save it as `step6_calendar_agent/credentials.json`.
3. Install dependencies and set your Groq key:
   ```bash
   pip install -r requirements.txt
   export GROQ_API_KEY="your_key"
   ```
4. Run from the repo root:
   ```bash
   python step6_calendar_agent/calendar_agent.py
   ```
   The first run opens a browser to sign in and creates `token.json`.

`credentials.json` and `token.json` are gitignored. Never commit them.

## Design decisions

- **Narrowest OAuth scope.** The agent only requests `calendar.events`. My first availability check used Google's `freeBusy` endpoint and got a 403, because that needs a broader scope. Instead of widening permissions, `check_availability` lists events in the time window using the scope I already had.
- **Current date injected on every task.** The system prompt is rebuilt with today's date, time and timezone (Asia/Kolkata) so "tomorrow" and "next Friday" resolve correctly.
- **Confirmation gate on writes.** `create_event` and `delete_event` ask `[y/N]` before touching the calendar. If I decline, the tool result tells the model not to retry the same action.
- **Tools never raise to the model.** Every tool returns `{success, detail, ...}`, including for bad dates, past start times, and Google API errors, so failures are reported honestly instead of crashing the loop.
- **Check before booking.** The system prompt requires `check_availability` before `create_event`, and `list_events` before any delete, so the model never guesses an event id.

## Reliability patterns (from Step 5)

- Retry with exponential backoff and jitter on transient API errors (`agent_patterns.py`)
- A reflection line after each tool result, so a failure is hard to miss
- Context compression when the conversation gets long

## What's verified

- All four tools were tested against a real calendar (create, list, availability, delete).
- The agent ran end to end on real requests.
- Backoff and compression are unit-tested with fake clients. I haven't seen a real retry or compression run live.

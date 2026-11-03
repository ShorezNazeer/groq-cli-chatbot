import os
import sys
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from groq import Groq

# agent_patterns.py lives one folder up, in the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_patterns import call_groq_with_backoff, reflect_on_result, compress_if_needed

from calendar_tools import list_events, check_availability, create_event, delete_event, TZ

MODEL = "openai/gpt-oss-120b"
MAX_ITERATIONS = 8

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

TOOL_IMPL = {
    "list_events": list_events,
    "check_availability": check_availability,
    "create_event": create_event,
    "delete_event": delete_event,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "List calendar events between two times. Use this to see what is scheduled and to find event ids.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "ISO 8601 start, e.g. 2026-11-03T00:00:00"},
                    "end": {"type": "string", "description": "ISO 8601 end, e.g. 2026-11-04T00:00:00"},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check whether a time slot is free. Returns any conflicting events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "ISO 8601 start"},
                    "end": {"type": "string", "description": "ISO 8601 end"},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a calendar event. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start": {"type": "string", "description": "ISO 8601 start"},
                    "end": {"type": "string", "description": "ISO 8601 end"},
                },
                "required": ["title", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": "Delete an event by its id (get ids from list_events). Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {"event_id": {"type": "string"}},
                "required": ["event_id"],
            },
        },
    },
]


def build_system_prompt():
    now = datetime.now(ZoneInfo(TZ))
    return f"""You are a calendar assistant that manages the user's Google Calendar.

Current date and time: {now:%A, %d %B %Y, %H:%M} (timezone: {TZ}).
Use this to resolve words like "today", "tomorrow" and "next Friday".
All datetimes you pass to tools must be ISO 8601 without a timezone,
for example 2026-11-03T15:00:00. They are interpreted as {TZ}.

Rules:
1. To book something, first call check_availability for that slot. If it is busy,
   tell the user what conflicts and ask what to do. Do not create the event anyway.
2. If the user gives a start time but no end time or duration, assume 30 minutes
   and say so in your summary.
3. To delete an event, first call list_events to find its id. Never guess an id.
4. create_event and delete_event ask the user for confirmation. If the user
   declines, do not retry the same action; ask what to change instead.
5. If a tool returns success false, tell the user plainly what failed and why.
6. Do not call tools for simple chat. When a task is done, give a short summary.
"""


def run_agent(messages: list, task: str) -> list:
    # Refresh the date/time on every task so "tomorrow" is always correct
    messages[0] = {"role": "system", "content": build_system_prompt()}
    messages.append({"role": "user", "content": task})

    for iteration in range(MAX_ITERATIONS):
        messages = compress_if_needed(messages, client, MODEL)
        response = call_groq_with_backoff(
            client, model=MODEL, messages=messages, tools=TOOL_SCHEMAS, tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            print(f"\n--- agent (iteration {iteration + 1}) ---")
            print(msg.content)

        if not msg.tool_calls:
            break

        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"\n[tool call] {name}({args})")

            impl = TOOL_IMPL.get(name)
            if impl is None:
                result = {"success": False, "detail": f"unknown tool '{name}'"}
            else:
                try:
                    result = impl(**args)
                except TypeError as err:
                    result = {"success": False, "detail": f"bad arguments: {err}"}

            print(f"[tool result] {str(result)[:300]}")
            reflection = reflect_on_result(name, result)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": f"{reflection}\n\n{json.dumps(result)}",
            })
    else:
        print("\n[stopped: reached MAX_ITERATIONS without the agent finishing]")

    return messages


if __name__ == "__main__":
    messages = [{"role": "system", "content": build_system_prompt()}]
    while True:
        task = input("\nWhat should I do with your calendar? (or 'quit')\n> ")
        if task.strip().lower() in ("quit", "exit"):
            break
        if not task.strip():
            continue
        messages = run_agent(messages, task)

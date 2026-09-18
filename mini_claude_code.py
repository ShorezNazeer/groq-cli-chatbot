import os
import json
import subprocess
from pathlib import Path
from groq import Groq


MODEL = "openai/gpt-oss-120b"       
SANDBOX = Path.home() / "projects" / "claude-cli-bot" / "sandbox"
MAX_ITERATIONS = 8                      

DENYLIST = ["rm ", "sudo", "curl", "wget", ">", ">>", "mkfs", ":(){", "dd "]

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Safety layer 

def _safe_path(user_path: str) -> Path:
    """Resolve a path and refuse anything that escapes the sandbox."""
    SANDBOX.mkdir(parents=True, exist_ok=True)
    resolved = (SANDBOX / user_path).resolve()
    if SANDBOX.resolve() not in resolved.parents and resolved != SANDBOX.resolve():
        raise ValueError(f"Refused: '{user_path}' escapes the sandbox.")
    return resolved


def _is_denied(command: str) -> bool:
    return any(bad in command for bad in DENYLIST)


def _confirm(action_description: str) -> bool:
    """The permission gate. Real Claude Code does this before file/shell
    actions — this is that same checkpoint, made explicit."""
    print(f"\n[CONFIRM NEEDED] {action_description}")
    answer = input("Proceed? [y/N]: ").strip().lower()
    return answer == "y"

# Tools

def list_directory(path: str = ".") -> str:
    target = _safe_path(path)
    if not target.exists():
        return f"Error: {path} does not exist."
    entries = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
    return "\n".join(entries) if entries else "(empty directory)"


def read_file(path: str) -> str:
    target = _safe_path(path)
    if not target.exists():
        return f"Error: {path} does not exist."
    return target.read_text(errors="replace")


def write_file(path: str, content: str) -> str:
    target = _safe_path(path)
    preview = content if len(content) < 400 else content[:400] + "\n...(truncated)"
    if not _confirm(f"Write to '{path}':\n---\n{preview}\n---"):
        return "User declined this write. Do not retry the same write; ask what to do differently."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"Wrote {len(content)} chars to {path}."


def run_shell_command(command: str) -> str:
    if _is_denied(command):
        return f"Error: command blocked by denylist: {command}"
    if not _confirm(f"Run shell command: {command}"):
        return "User declined this command. Do not retry the same command."
    try:
        result = subprocess.run(
            command, shell=True, cwd=SANDBOX, capture_output=True,
            text=True, timeout=15,
        )
        output = result.stdout + result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."


TOOL_IMPL = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "run_shell_command": run_shell_command,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path inside sandbox, default '.'"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's text contents from the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in the sandbox with given content. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Run a shell command inside the sandbox. Requires user confirmation. Destructive commands are blocked.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a small coding agent operating only inside a sandbox folder.

For every task:
1. First, respond with a short numbered PLAN (2-5 steps) of what you intend to do.
   Do not call any tools in this first message — plan only.
2. After the plan, execute it step by step using the available tools.
3. After each tool result, check whether it matches what you expected.
   If a step failed or was declined by the user, explain what you'll try instead
   rather than blindly repeating it.
4. When the task is fully done, stop calling tools and give a short summary
   of what changed.
"""

# Agent loop

def run_agent(messages: list, task: str) -> list:
    messages.append({"role": "user", "content": task})
    took_action = False

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS, tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            print(f"\n--- agent (iteration {iteration + 1}) ---")
            print(msg.content)

        if not msg.tool_calls:
            if not took_action:
                messages.append({"role": "user", "content": "Continue — use the tools to actually complete the task."})
                continue
            break

        took_action = True
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"\n[tool call] {name}({args})")
            result = TOOL_IMPL[name](**args)
            print(f"[tool result] {result[:300]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "name": name, "content": result})
    else:
        print("\n[stopped: reached MAX_ITERATIONS without the agent finishing]")

    return messages


if __name__ == "__main__":
    print(f"Sandbox: {SANDBOX}")
    # The conversation starts once, here, and lives for the whole session --
    # every task after this appends to the same history instead of starting fresh.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        task = input("\nWhat should the agent do? (or 'quit' to exit)\n> ")
        if task.strip().lower() in ("quit", "exit"):
            break
        messages = run_agent(messages, task)
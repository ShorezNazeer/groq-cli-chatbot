import os
import subprocess
from mcp.server.fastmcp import FastMCP

BASE_DIR = os.path.abspath(os.path.expanduser("~/projects/claude-cli-bot/sandbox"))
os.makedirs(BASE_DIR, exist_ok=True)

mcp = FastMCP("filesystem-tools")

def _safe_path(user_path: str) -> str:
    """Resolve user_path relative to BASE_DIR and refuse to leave it."""
    candidate = os.path.abspath(os.path.join(BASE_DIR, user_path))

    if not candidate.startswith(BASE_DIR):
        raise ValueError("Path escapes the sandbox directory - not allowed.")
    return candidate

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List files and folders inside the sandbox directiry.

    Args:
        path: Relative path inside the sandbox (default: sandbox root).
    """

    target = _safe_path(path)
    if not os.path.isdir(target):
        return f"Error: '{path}' is not a directory."

    entries = os.listdir(target)
    if not entries:
        return "(empty directory)"

    return "\n".join(sorted(entries))

@mcp.tool()
def read_file(path: str) -> str:
    target = _safe_path(path)
    if not os.path.isfile(target):
        return f"Error: '{path}' is not a file."

    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return "Error: File is not readable as text (binary file?)."

DENYLIST = ["rm", "sudo", ">", "curl", "wget", "mv", "dd"]
@mcp.tool()
def run_shell_command(command: str) -> str:
    """Run a shell command inside the sandbox directory and return its output.

    Args:
        command: The shell command to execute. Destructive or network
            commands (rm, sudo, curl, etc.) are blocked.
    """
    lowered = command.lower()
    if any(bad in lowered for bad in DENYLIST):
        return "Error: command blocked by safety denylist."

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=10,

        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr.strip()}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."

if __name__ == "__main__":
    mcp.run()


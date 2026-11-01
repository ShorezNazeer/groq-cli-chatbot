import time
import random
from groq import RateLimitError, APIConnectionError, APITimeoutError, InternalServerError

RETRYABLE_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)

def call_groq_with_backoff(client, max_retries=5, base_delay=1.0, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RETRYABLE_ERRORS as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            print(f"[retry] {type(e).__name__}: waiting {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)

import subprocess

def run_shell_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
    return {
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    with open(path, "r") as f:          # read back what actually landed on disk
        written = f.read()
    return {"success": written == content, "path": path, "bytes_written": len(written)}

def reflect_on_result(tool_name, result):
    if result["success"]:
        return f"[reflection] {tool_name} succeeded."
    detail = result.get("stderr") or result.get("detail") or "no further detail available"
    return f"[reflection] {tool_name} FAILED. detail: {detail[:200]}"

def compress_if_needed(messages, max_messages=30, keep_recent=10):
    if len(messages) <= max_messages:
        return messages
    old, recent = messages[:-keep_recent], messages[-keep_recent:]
    summary = summarize(old)   # a Groq call: "summarize this conversation so far"
    return [{"role": "system", "content": f"[earlier context, summarized] {summary}"}] + recent
# test_backoff.py -- forces a fake rate limit, no real Groq calls or waiting on quota
import httpx
from groq import RateLimitError
from agent_patterns import call_groq_with_backoff

calls = {"n": 0}
fake_request = httpx.Request("POST", "https://api.groq.com/fake")

class FakeCompletions:
    def create(self, **kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            fake_response = httpx.Response(429, request=fake_request)
            raise RateLimitError("rate limited", response=fake_response, body=None)
        return "SUCCESS"

class FakeChat:
    completions = FakeCompletions()

class FakeClient:
    chat = FakeChat()

result = call_groq_with_backoff(FakeClient(), messages=[])
print("result:", result, "| total attempts:", calls["n"])
assert result == "SUCCESS" and calls["n"] == 3
print("PASS")

# --- second scenario: a non-retryable error should raise immediately ---
from groq import AuthenticationError

auth_calls = {"n": 0}

class FakeAuthCompletions:
    def create(self, **kwargs):
        auth_calls["n"] += 1
        fake_response = httpx.Response(401, request=fake_request)
        raise AuthenticationError("bad key", response=fake_response, body=None)

class FakeAuthChat:
    completions = FakeAuthCompletions()

class FakeAuthClient:
    chat = FakeAuthChat()

try:
    call_groq_with_backoff(FakeAuthClient(), messages=[])
    print("FAIL: should have raised")
except AuthenticationError:
    assert auth_calls["n"] == 1
    print("PASS: raised immediately, zero retries")
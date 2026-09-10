import os
import json
import requests
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------------------------------------
# 1. The actual Python functions that DO the work.
#    These are just normal functions — nothing Groq-specific.
# ---------------------------------------------------------

def get_weather(city: str) -> str:
    """Fetch current weather for a city using wttr.in (no API key needed)."""
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return response.text.strip()
    except Exception as e:
        return f"Could not fetch weather: {e}"


def calculate(expression: str) -> str:
    """Evaluate a basic math expression safely-ish."""
    try:
        # eval() is risky on arbitrary input in production code —
        # fine here since it's just us testing locally.
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# A lookup table so we can call the right Python function
# once we know which tool name the model picked.
available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
}

# ---------------------------------------------------------
# 2. Tool schemas — this is what we SEND to the model so it
#    knows these tools exist, what they're called, and what
#    arguments each one needs. The model never runs these
#    itself — it just tells us "please call this one".
# ---------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'Lucknow' or 'Delhi'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a math expression, e.g. '12 * (3 + 4)'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A valid Python math expression as a string",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# ---------------------------------------------------------
# 3. The conversation loop
# ---------------------------------------------------------

messages = [
    {"role": "system", "content": "You are a helpful assistant with access to weather and calculator tools."}
]

print("Tool-use agent ready. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    # First call: give the model the tools list. It will either
    # answer directly, or ask to call one/more tools.
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools,
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        # The model wants to call one or more functions before answering.
        # We must append its request as an assistant message first —
        # the API needs this in history so it knows what it asked for.
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Look up and actually run the real Python function
            function_to_call = available_functions[function_name]
            function_result = function_to_call(**function_args)

            # Feed the result back as a "tool" role message,
            # tagged with tool_call_id so the model knows which
            # request this result answers.
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_result,
            })

        # Second call: now the model has real data and can
        # give a normal natural-language answer.
        second_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
        )
        final_message = second_response.choices[0].message.content
        print(f"Bot: {final_message}\n")
        messages.append({"role": "assistant", "content": final_message})

    else:
        # No tool needed — model answered directly.
        print(f"Bot: {response_message.content}\n")
        messages.append({"role": "assistant", "content": response_message.content})
        





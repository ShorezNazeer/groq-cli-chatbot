import os
import json
import requests
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


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
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
}


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


messages = [
    {"role": "system", "content": "You are a helpful assistant with access to weather and calculator tools."}
]

print("Tool-use agent ready. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})


    while True:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if not tool_calls:
            print(f"Bot: {response_message.content}\n")
            messages.append({"role": "assistant", "content": response_message.content})
            break  

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            function_to_call = available_functions[function_name]
            function_result = function_to_call(**function_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_result,
            })

        





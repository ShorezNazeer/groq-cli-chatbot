import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def chat():
    print("Groq CLI Chatbot - type 'exit' to quit\n")
    messages = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
        )

        reply = response.choices[0].message.content
        print(f"Bot: {reply}\n")

        messages.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    chat()

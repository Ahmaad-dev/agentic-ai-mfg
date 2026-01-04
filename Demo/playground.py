from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
api_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

messages = []

print("Chat gestartet! Geben Sie 'exit' ein, um zu beenden.\n")

while True:
    user_input = input("Sie: ")

    if user_input.lower() in ["exit", "quit", "beenden"]:
        print("Chat beendet.")
        break

    messages.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model=deployment_name,
        messages=messages
    )

    assistant_message = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_message})

    print(f"\nAssistent: {assistant_message}\n")

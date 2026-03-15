"""Test HF Inference API using OpenAI-compatible endpoint"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

token = os.getenv("HF_TOKEN")
print(f"Token loaded: {token[:10]}..." if token else "NO TOKEN FOUND")

# Use HF's OpenAI-compatible endpoint
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=token,
)

# Try with a model
print("\nTesting with Mistral...")
try:
    completion = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        messages=[
            {"role": "user", "content": "What is AI? One sentence."}
        ],
        max_tokens=100,
    )
    print(f"Success: {completion.choices[0].message.content}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:300]}")

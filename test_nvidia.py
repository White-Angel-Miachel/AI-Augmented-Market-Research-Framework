import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY", "").replace("Bearer ", "")

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=api_key
)

try:
    print("Calling Nvidia NIM API with OpenAI Client for MINIMAX M2.5 with system prompt...")
    
    # Simulate a full pipeline request with system prompt
    completion = client.chat.completions.create(
        model="minimaxai/minimax-m2.5",
        messages=[
            {"role": "system", "content": "You are a market parsing bot."},
            {"role": "user", "content": "Here is a 30,000 token request to test latency... Just say hello."}
        ],
        temperature=0.7,
        max_tokens=8000
    )
    print("Success:", completion.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Error:", e)

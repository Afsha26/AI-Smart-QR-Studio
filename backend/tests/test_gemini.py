import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

print("✅ API Key Loaded Successfully")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Send a simple prompt
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say Hello in one sentence."
)

print("\nGemini Response:")
print(response.text)
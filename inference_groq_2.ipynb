import os
from groq import Groq

# Get the Groq API key from environment variable set by GitHub Actions
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise EnvironmentError("Missing GROQ_API_KEY. Make sure it's set in GitHub Secrets.")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Run prompt
response = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {"role": "user", "content": "Write a user requirement for password reset."}
    ],
    temperature=0.7,
)

# Print the result
print(response.choices[0].message.content)

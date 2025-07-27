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

# Extract the response text
output_text = response.choices[0].message.content

# Print to console
print("Groq response:\n", output_text)

# Save to file
output_file = "groq_output.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(output_text)

print(f"\nOutput written to: {output_file}")

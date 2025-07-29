import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Load Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

LLM_MODEL = "llama3-8b-8192"

def ask_llm(prompt, system_prompt="You are a helpful IT support assistant. Be natural and concise."):
    """Generic LLM call using Groq-hosted LLaMA."""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def extract_ids(message):
    """Use LLM to extract order ID and/or container ID from user message."""
    prompt = f"""
You are a support agent. Extract Order ID or Container ID from this message:
"{message}"

Return JSON with the format: {{
  "order_id": "ORD-1234" or null,
  "container_id": "CONT-5678" or null
}}. 
Only extract if present.
"""
    try:
        import json
        result = ask_llm(prompt, system_prompt="You are an expert data extractor.")
        parsed = json.loads(result)
        return {
            "order_id": parsed.get("order_id"),
            "container_id": parsed.get("container_id")
        }
    except Exception as e:
        return {"order_id": None, "container_id": None}


def request_missing_id(order_id, container_id):
    """Ask user for missing order/container ID using LLM phrasing."""
    if not order_id and not container_id:
        prompt = "The user hasn't provided any Order ID or Container ID. Ask politely for one of them to proceed."
    elif not order_id:
        prompt = "The user didn't provide the Order ID. Ask naturally for the Order ID."
    elif not container_id:
        prompt = "The user didn't provide the Container ID. Ask naturally for the Container ID."
    else:
        return None  # Nothing missing

    return ask_llm(prompt)


def phrase_workaround(issue_label, workaround_text):
    """Phrase a known workaround using LLM for a more natural response."""
    prompt = f"""
We identified this issue: "{issue_label}".

The workaround is: "{workaround_text}".

Write a helpful, polite sentence suggesting this workaround to the user, as if you're a friendly IT support chatbot.
"""
    return ask_llm(prompt)


def draft_email_content(issue_summary, order_id=None, container_id=None):
    """Generate escalation email using LLM."""
    id_lines = []
    if order_id:
        id_lines.append(f"Order ID: {order_id}")
    if container_id:
        id_lines.append(f"Container ID: {container_id}")
    ids = "\n".join(id_lines) if id_lines else "No ID provided."

    prompt = f"""
You're an IT support agent. Draft a professional escalation email.

Issue summary:
{issue_summary}

Identifiers:
{ids}

Keep it short, formal, and clear. End with a request for IT to investigate and resolve.
"""
    return ask_llm(prompt)


def interpret_user_confirmation(reply_text):
    """
    Use LLM to interpret whether user's reply means success, failure, or ambiguous
    """
    prompt = f"""
You are an IT service assistant. A workaround was suggested to a user. They replied with:

"{reply_text}"

Classify this response into one of the following categories:

- success: if the user confirms the workaround helped
- failure: if the user says it didn’t work
- unclear: if the response is ambiguous, neutral, or not clear

Respond with only one word: success, failure, or unclear.
"""
    return ask_llm(prompt).strip().lower()

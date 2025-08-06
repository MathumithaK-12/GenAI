import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Load Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

LLM_MODEL = "llama3-8b-8192"


def ask_llm(prompt, system_prompt="You are a helpful IT assistant at Warehouse. Be natural and concise. Reduce ambiguity. Always address back or greet back only when it is greeting"):
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

def detect_intent(user_input: str) -> str:
    """
    Uses the LLM to classify the user input into:
    - greeting
    - thanks
    - end_of_convo
    - new_issue
    - normal (default)
    """
    prompt = (
        "Classify the following message into one of these intents: "
        "'greeting', 'thanks', 'end_of_convo', 'new_issue', or 'normal'.\n\n"
        f"Message: \"{user_input}\"\n"
        "Respond with only one word: greeting, thanks, end_of_convo, new_issue, or normal."
    )

    response = ask_llm(prompt)
    intent = response.strip().lower()

    if intent in ["greeting", "thanks", "new_issue", "end_of_convo"]:
        return intent
    return "normal"


def handle_greeting():
    prompt = "The user greeted you. Respond with a warm greeting and ask how you can help."
    return ask_llm(prompt)

def handle_thanks():
    prompt = "The user thanked you. Respond with a warm and polite message like 'Glad I could help!'"
    return ask_llm(prompt)

def extract_ids(message):
    """
    Use LLM to extract order ID and/or container ID from user message.
    Fallback to regex if LLM fails or returns bad format.
    """
    prompt = f"""
You are a support agent. Extract Order ID and/or Container ID from this message:
"{message}"

Return a JSON like:
{{
  "order_id": "ORD123" or null,
  "container_id": "CONT456" or null
}}. 
Only include fields if the ID is actually present.
If neither is found, return: {{}}
"""

    try:
        response = ask_llm(prompt, system_prompt="You are an expert data extractor. Respond ONLY with JSON.")
        json_str = re.search(r'\{.*\}', response)
        if json_str:
            parsed = json.loads(json_str.group())
            return {
                "order_id": parsed.get("order_id"),
                "container_id": parsed.get("container_id")
            }
    except Exception as e:
        print("⚠️ LLM ID extraction failed, trying regex...")

    # Fallback to regex extraction
    order_match = re.search(r'\bORD[-]?\d+\b', message, re.IGNORECASE)
    container_match = re.search(r'\bCONT[-]?\d+\b', message, re.IGNORECASE)

    return {
        "order_id": order_match.group().upper() if order_match else None,
        "container_id": container_match.group().upper() if container_match else None
    }


def request_missing_id(order_id, container_id):
    """Ask user for missing order/container ID using LLM phrasing. Greet only if greeted here"""
    if not order_id and not container_id:
        prompt = "The user hasn't provided any Order ID or Container ID. Ask them politely to share either one so we can assist."
    elif not order_id:
        prompt = "The user didn't provide an Order ID. Ask them kindly to share it."
    elif not container_id:
        prompt = "The user didn't provide a Container ID. Ask them kindly to share it."
    else:
        return None  # Nothing missing

    return ask_llm(prompt, system_prompt="You are a polite support assistant. Ask in a concise and short manner. Like in a chat")


def phrase_workaround(workaround_text):
    """Phrase a known workaround using LLM for a more natural response."""
    prompt = f"""

No need to say Hi or do any greeting here.     
We identified an issue with the provided order or container.

The workaround is: "{workaround_text}".

Write a helpful, polite message suggesting this workaround to the user as if you're a friendly support chatbot. Keep is short and precise. Reply with workaround deterministically as it is a known issue. Be polite. Also ask to check if the workaround worked.
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

Keep it short, simple, formal, and clear. End with a request for IT to investigate and resolve. Just add Best Regards, IT Support Agent at end.
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



def classify_issue_intent(message: str) -> str:
    """
    Use LLM to classify the message and map to one of the agent types.
    """
    prompt = f"""Classify the user's issue into one of the following categories:
- pack_itsm: Only Packing or label or postcode related issues.
- location: Location-related issues
- health_check: Health check or system monitoring
- user_account: User account creation or access issues or user related issues or user account issues
- hsn_code: HSN code-related issues
- design: Design or workflow queries

If the message is unclear or not enough to classify, respond ONLY with: unknown

User message: "{message}" 

Respond with only one keyword: pack_itsm, location, health_check, user_account, hsn_code, or design.

Answer:""".strip()

    response = ask_llm(prompt)  # Use your LLM calling function
    classification = response.strip().lower()

    allowed = {"pack_itsm", "location", "health_check", "user_account", "hsn_code", "design"}
    return classification if classification in allowed else "unknown"


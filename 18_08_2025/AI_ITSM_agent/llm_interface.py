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


def ask_llm(prompt, system_prompt="You are a helpful IT assistant at a Warehouse. Be natural and concise. Reduce ambiguity. Always address back or greet back only when it is greeting. Respond in a human like format. Respond casually and empathetically. Start with phrases like Hey, gotchu, Apologies or similar words based on the context before the main message. But be formal when composing a mail"):
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
    - greeting: user greets
    - thanks: user expresses gratitude
    - end_of_convo: user wants to end the conversation
    - new_issue: user explicitly wants to log a new issue/incident
    - summary: user asks for summary/status/details of an order/container/incident
    - normal (default): user directly reports an issue (e.g., 'issue with packing', 'label not printing')
    """
    prompt = (
        "Classify the following message into one of these intents: "
        "'greeting', 'thanks', 'end_of_convo', 'new_issue', 'summary', or 'normal'.\n\n"
        f"Message: \"{user_input}\"\n"
        "Respond with only one word: greeting, thanks, end_of_convo, new_issue, summary or normal."
    )

    response = ask_llm(prompt)
    intent = response.strip().lower()

    if intent in ["greeting", "thanks", "new_issue", "end_of_convo", "summary"]:
        return intent
    return "normal"


def handle_greeting():
    prompt = "The user greeted you. Respond with a warm greeting.  Introduce yourself as Pack assist and ask how you can help. Do not tell anything beyond this"
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
You are a support agent. Extract **full IDs** from this message:
"{message}"

ID formats:
- Order ID: starts with 'ORD' followed by digits, e.g., ORD69021
- Container ID: starts with 'CONT' followed by digits, e.g., CONT12345
- Incident ID: starts with 'INC' followed by a date (YYYYMMDD) and a 6-digit sequence, e.g., INC-20250819-001143


Return a **valid JSON only**, like this:
{{
  "order_id": "ORD12345" or null,
  "container_id": "CONT67890" or null,
  "incident_id": "INC-YYYYMMDD-######" or null
}}

**Important**:
- Return full IDs exactly as they appear in the message.
- Do not truncate or shorten any IDs.
- Only include fields if they are present; if none are found, return {{}}.
"""

    try:
        response = ask_llm(prompt, system_prompt="You are an expert data extractor. Respond ONLY with JSON.")
        json_str = re.search(r'\{.*\}', response)
        if json_str:
            parsed = json.loads(json_str.group())
            return {
                "order_id": parsed.get("order_id"),
                "container_id": parsed.get("container_id"),
                "incident_id": parsed.get("incident_id")
            }
    except Exception as e:
        print("⚠️ LLM ID extraction failed, trying regex...")

    # Fallback to regex extraction
    order_match = re.search(r'\bORD[-]?\d+\b', message, re.IGNORECASE)
    container_match = re.search(r'\bCONT[-]?\d+\b', message, re.IGNORECASE)
    incident_match = re.search(r'\bINC-\d{8}-\d{6}\b', message, re.IGNORECASE)


    return {
        "order_id": order_match.group().upper() if order_match else None,
        "container_id": container_match.group().upper() if container_match else None,
        "incident_id": incident_match.group().upper() if incident_match else None
    }


def request_missing_id(order_id, container_id):
    """Ask user for missing order/container ID using LLM phrasing. Greet only if greeted here"""
    if not order_id and not container_id:
        prompt = "Do not greet here. The user hasn't provided any Order ID or Container ID. Be casual and ask them politely to share either one so we can assist, in a humanly format"
    elif not order_id:
        prompt = "The user didn't provide an Order ID. Ask them kindly to share it."
    elif not container_id:
        prompt = "The user didn't provide a Container ID. Ask them kindly to share it."
    else:
        return None  # Nothing missing

    return ask_llm(prompt, system_prompt="You are a polite support assistant. Ask in a concise and short manner. Like in a chat")


def phrase_workaround(workaround_text, issue_type):
    """Phrase a known workaround using LLM for a more natural response."""
    prompt =  (
        "No need to say Hi or do any greeting here.\n\n"
        "We identified an issue with the provided order or container.\n\n"
        f'The workaround is: "{workaround_text}".\n\n'
        "Write a helpful, polite message suggesting this workaround to the user as if you're a friendly support chatbot. "
        "Keep it short and precise. Reply deterministically as it is a known issue. Be polite.\n\n"
    )

    if issue_type == "Hazmat Issue":
        prompt += "Please check the SKU table for details related to this hazmat SKU issue.\n\n"
    elif issue_type == "Invalid Postcode":
        prompt += "Please verify the postcode in the order table for the affected order.\n\n"
    
    prompt += (
        "Also check with the user if the workaround suggested has worked, so that we can bring the incident to closure.\n\n"
        "**Format requirement:**\n"
        "- Each sentence must be on its own line.\n"
        "- Add a blank line between the introduction, the workaround steps, and the closing request.\n"
        "- Do not combine sentences into a single paragraph."
    )

    return ask_llm(prompt)


def draft_email_content(issue_summary):
    """Generate escalation email using LLM."""

    prompt = f"""
You're an IT support agent. Draft a professional escalation email.

Issue summary:
{issue_summary}


No need to include any subject. Do not place any generic placeholders and do not say that this is a drafted mail or something similar. Keep it short, simple, formal, and clear. End with a request for IT team to investigate and resolve. Do ask IT team to reach out to the flow room/user for further details related to the issue. Just add Best Regards, IT Support Agent at end.
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

def user_confirmation(reply_text):
    text = reply_text.strip().lower()

    # Directly handle simple yes/no without LLM
    if text in ["no", "nope", "nah"]:
        return "issue_resolved"
    if text in ["yes", "yeah", "yep", "still", "yes it persists"]:
        return "issue_persists"

    
    prompt = f"""
You are an IT service assistant. You asked the user whether they still notice an issue with their order.
They replied with:

"{reply_text}"

Classify this response into one of the following categories:

- issue_persists: user says YES or confirms the issue continues (e.g., "yes", "still happening")
- issue_resolved: user says NO or confirms the issue is gone (e.g., "no", "it's fixed", "not happening anymore")
- unclear: if the reply is ambiguous

Respond with only one word: issue_persists, issue_resolved, or unclear.
"""
    result = ask_llm(prompt).strip().lower()
    if result in ["issue_persists", "issue_resolved", "unclear"]:
        return result
    else:
        return "unclear"

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


def request_missing_summary_ids() -> str:
    """
    LLM phrases a short, friendly ask for any of the 3 IDs.
    """
    prompt = """
The user asked for a summary but didn't provide identifiers.
Write a single short sentence asking them to share ANY of: Incident ID, Order ID, or Container ID.
Be friendly and clear. No greeting.
"""
    return ask_llm(prompt)


def draft_summary_message(facts: dict) -> str:
    """
    LLM composes a concise summary from structured facts.
    facts keys (any may be None): 
      incident_id, incident_status, incident_created_at, issue_summary,
      order_id, container_id, 
      cms_last_status, cms_last_time
    """
    prompt = f"""
Compose a concise, human-friendly summary from this JSON.
Prefer Incident info if available; otherwise summarize latest CMS log.
If there is no incident, mention that briefly but still state the latest CMS status if present.

JSON:
{json.dumps(facts, default=str)}

Constraints:
- No greeting.
- 3 to 6 short lines max.
- If a field is null/missing, don't mention it.
"""
    return ask_llm(prompt)


def phrase_mismatch_or_notfound(context: dict) -> str:
    """
    LLM phrasing for mismatch/notfound messages.
    context: 
      { "type": "notfound"|"mismatch", 
        "incident_id":..., "incident_order_id":..., "incident_container_id":...,
        "provided_order_id":..., "provided_container_id":... }
    """
    prompt = f"""
Write a single, polite message for the user based on this JSON context:
{json.dumps(context)}

Rules:
- If type is "notfound": clearly say the incident/order/container wasn't found and ask them to recheck or share another ID.
- If type is "mismatch": explain the mismatch (e.g., Incident belongs to a different order/container) and ask which one to use.
- No greeting; one or two sentences only.
"""
    return ask_llm(prompt)    

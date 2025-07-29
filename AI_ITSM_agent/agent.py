import os
from dotenv import load_dotenv
from incident_handler import (
    handle_user_message,
    handle_user_confirmation
)

load_dotenv()

print("🤖 Agent: IT Support Assistant is now online. How can I help you today?")

conversation_active = True
session_state = {
    "order_id": None,
    "container_id": None,
    "incident_id": None,
    "awaiting_user_confirmation": False,
    "last_log": None,
    "matched_label": None,
    "known_workaround": None,
    "escalated": False
}

while conversation_active:
    user_input = input("You: ")

    # Exit condition
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("🤖 Agent: Thank you! If you need further assistance, just let me know.")
        break

    if session_state.get("awaiting_user_confirmation"):
        response, session_state = handle_user_confirmation(user_input, session_state)
    else:
        response, session_state = handle_user_message(user_input, session_state)

    print("🤖 Agent: ", response)

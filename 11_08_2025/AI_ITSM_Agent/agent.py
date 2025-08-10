# backend/agent.py

import os
from dotenv import load_dotenv
from incident_handler import (
    handle_user_message,
    handle_user_confirmation
)

load_dotenv()

# In-memory session storage for UI/API access
session_store = {}

def run_itsm_agent(user_input: str, session_id: str) -> str:
    # Initialize session if not present
    if session_id not in session_store:
        session_store[session_id] = {
            "order_id": None,
            "container_id": None,
            "incident_id": None,
            "awaiting_user_confirmation": False,
            "last_log": None,
            "matched_label": None,
            "known_workaround": None,
            "escalated": False
        }

    session_state = session_store[session_id]

    if session_state.get("awaiting_user_confirmation"):
        response, updated_state = handle_user_confirmation(user_input, session_state)
    else:
        response, updated_state = handle_user_message(user_input, session_state)

    session_store[session_id] = updated_state
    return response


# CLI Mode
def main():
    print("🤖 Agent: IT Support Assistant is now online. How can I help you today?")
    session_id = "cli_session"  # fixed session ID for CLI
    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("🤖 Agent: Thank you! If you need further assistance, just let me know.")
            break

        response = run_itsm_agent(user_input, session_id)
        print("🤖 Agent:", response)


if __name__ == "__main__":
    main()

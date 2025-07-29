import os
from dotenv import load_dotenv

from incident_handler import (
    handle_user_message,
    handle_user_confirmation
)

# Load environment variables
load_dotenv()

# Initialize session state
session_state = {
    "order_id": None,
    "container_id": None,
    "incident_id": None,
    "last_log": None,
    "matched_label": None,
    "known_workaround": None,
    "awaiting_user_confirmation": False,
    "escalated": False
}


def main():
    print("🤖 ITSM Assistant is now active. Describe your issue below:")

    while True:
        try:
            user_input = input("\nYou: ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Bye! Have a great day.")
                break

            if session_state.get("awaiting_user_confirmation"):
                response, updated_state = handle_user_confirmation(user_input, session_state)
            else:
                response, updated_state = handle_user_message(user_input, session_state)

            session_state.update(updated_state)
            print("\nAgent:", response)

        except KeyboardInterrupt:
            print("\n👋 Exiting agent.")
            break
        except Exception as e:
            print(f"⚠️ An error occurred: {e}")


if __name__ == "__main__":
    main()

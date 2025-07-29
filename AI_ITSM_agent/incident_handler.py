from llm_interface import (
    ask_llm,
    extract_ids,
    request_missing_id,
    phrase_workaround,
    draft_email_content,
    interpret_user_confirmation
)

from db_interface import (
    get_latest_log,
    find_known_failure_match,
    log_incident,
    update_incident_status
)

from email_utils import send_email_to_it


def handle_user_message(user_input, session_state):
    # Initialize session state if not present
    if not session_state:
        session_state = {
            "incident_id": None,
            "order_id": None,
            "container_id": None,
            "status": None
        }

    # Extract IDs if not already set
    if not session_state["order_id"] and not session_state["container_id"]:
        extracted = extract_ids(user_input)
        session_state["order_id"] = extracted.get("order_id")
        session_state["container_id"] = extracted.get("container_id")

    # If still missing, ask the user naturally

    order_id = session_state["order_id"]
    container_id = session_state["container_id"]

    if not order_id and not container_id:
        prompt = request_missing_id(order_id, container_id)
        return prompt, session_state

    # Check if logs exist
    latest_log = get_latest_log(order_id=order_id, container_id=container_id)
    if not latest_log:
        return (
            f"I couldn't find any recent activity for the given "
            f"{'order ID' if order_id else 'container ID'}. "
            f"Could you double-check the ID and try again?",
            session_state
        )

    # Log the incident if not already logged
    if not session_state["incident_id"]:
        summary = f"Issue with Order {order_id}" if order_id else f"Issue with Container {container_id}"
        incident_id = log_incident(order_id, container_id, summary)
        session_state["incident_id"] = incident_id
        session_state["status"] = "In Progress"

    update_incident_status(session_state["incident_id"], "In Progress")

    # Match against known failure
    response_payload = latest_log["response_xml"]
    match = find_known_failure_match(response_payload)

    if match:
        # Use LLM to phrase workaround naturally
        phrased_response = phrase_workaround(match["workaround"])
        session_state["awaiting_user_confirmation"] = True
        return phrased_response, session_state

    else:
        # Unknown issue – escalate
        summary = (
            f"Issue reported for Order {order_id or ''} / Container {container_id or ''}. "
            "No known pattern matched."
        )
        email_body = draft_email_content(summary, response_payload)
        session_state["status"] = "EscalatedToIT"
        return (
            "I'm unable to resolve this with known workarounds. I've escalated the issue to our IT team. "
            "They’ll look into it shortly.\n\n" + email_body,
            session_state
        )


def handle_user_confirmation(user_input, session_state):
    result = interpret_user_confirmation(user_input)

    if result == "success":
        update_incident_status(session_state["incident_id"], "Resolved")
        session_state["status"] = "Resolved"
        session_state["awaiting_user_confirmation"] = False
        return (
            "Great! I'm glad that resolved your issue. Let me know if you need help with anything else.",
            session_state
        )

    elif result == "failure":
        update_incident_status(session_state["incident_id"], "Open")
        summary = (
            f"User confirmed workaround failed for Order {session_state['order_id'] or ''} / "
            f"Container {session_state['container_id'] or ''}."
        )
        email_body = draft_email_content(summary)
        send_email_to_it(
        subject="Escalation: Order/Container Issue",
        body=email_body
        )
        session_state["status"] = "EscalatedToIT"
        session_state["awaiting_user_confirmation"] = False
        return (
            "Thanks for confirming. I've escalated this to our IT team for further investigation.\n\n" + email_body,
            session_state
        )

    else:
        return "Just to confirm, did the workaround resolve the issue? Please reply with yes or no.", session_state

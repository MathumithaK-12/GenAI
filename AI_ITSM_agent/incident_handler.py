from db_interface import (
    get_latest_log,
    log_incident,
    update_incident_status,
    find_known_failure_match
)
from llm_interface import (
    ask_llm,
    extract_ids,
    request_missing_id,
    phrase_workaround,
    draft_email_content,
    interpret_user_confirmation
)
from email_utils import send_email_to_it


def handle_user_message(user_message, session_state):
    # Step 1: Extract order_id or container_id from user input (if not already present)
    if not session_state.get("order_id") and not session_state.get("container_id"):
        ids = extract_ids(user_message)
        session_state.update(ids)

    # Step 2: Prompt if still missing ID
    if not session_state.get("order_id") and not session_state.get("container_id"):
        return request_missing_id(
            order_id=session_state.get("order_id"),
            container_id=session_state.get("container_id")
        ), session_state

    # Step 3: Raise incident (move to In Progress)
    if not session_state.get("incident_id"):
        session_state["incident_id"] = log_incident(
            session_state.get("order_id"),
            session_state.get("container_id"),
            "Auto-detected failure, pending root cause"
        )
        update_incident_status(session_state["incident_id"], "In Progress")

    # Step 4: Fetch latest log for that ID
    log = get_latest_log(
        order_id=session_state.get("order_id"),
        container_id=session_state.get("container_id")
    )

    if not log:
        return "I couldn't find any related logs for the provided ID. Please double-check and try again.", session_state

    session_state["last_log"] = log

    # Step 5: If status is success, no action needed
    if log["status"].lower() == "success":
        return "The operation seems to have completed successfully. You may try again or let me know if you're still facing issues.", session_state

    # Step 6: Check for known failure match
    known_issue = find_known_failure_match(log["response_payload"])
    if known_issue:
        session_state["matched_label"] = known_issue["label"]
        session_state["known_workaround"] = known_issue["workaround"]
        workaround = phrase_workaround(known_issue["workaround"])
        session_state["awaiting_user_confirmation"] = True
        return workaround + "\n\nCan you please try that and let me know if it works?", session_state

    # Step 7: Unknown failure — escalate to IT
    update_incident_status(session_state["incident_id"], "Open")
    email_body = draft_email_content(user_message, session_state)
    send_email_to_it(
        subject=f"Incident Escalation - Issue with Order {session_state.get('order_id') or session_state.get('container_id')}",
        body=email_body
    )
    session_state["escalated"] = True
    return (
        "I couldn't resolve this issue automatically. I've escalated it to the IT team and logged an incident for tracking.\n\n"
        "They’ll reach out to you shortly.",
        session_state
    )


def handle_user_confirmation(user_reply, session_state):
    # Interpret LLM-based user confirmation reply
    outcome = interpret_user_confirmation(user_reply)

    if outcome == "success":
        update_incident_status(session_state["incident_id"], "Resolved")
        session_state["awaiting_user_confirmation"] = False
        return (
            "Awesome! I've marked the incident as resolved. Glad we could help. Let me know if you need anything else!",
            session_state
        )

    elif outcome == "failure":
        update_incident_status(session_state["incident_id"], "Open")
        email_body = draft_email_content(
            "User confirmed that the suggested workaround didn’t help. " + user_reply,
            session_state
        )
        send_email_to_it(
            subject=f"Follow-up Escalation - Workaround Failed for {session_state.get('order_id') or session_state.get('container_id')}",
            body=email_body
        )
        session_state["escalated"] = True
        session_state["awaiting_user_confirmation"] = False
        return (
            "Thanks for trying. Since that didn’t work, I’ve escalated the issue to the IT team. They’ll investigate and follow up with you soon.",
            session_state
        )

    else:
        return (
            "Just to clarify — did the workaround help resolve the issue? Please let me know with a quick 'yes' or 'no'.",
            session_state
        )

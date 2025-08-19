from typing import Dict, Tuple, Optional, Any

from llm_interface import (
    ask_llm,
    extract_ids,
    request_missing_id,
    phrase_workaround,
    draft_email_content,
    interpret_user_confirmation,
    detect_intent,
    handle_greeting,
    handle_thanks,
    user_confirmation,
    request_missing_summary_ids,
    draft_summary_message,
    phrase_mismatch_or_notfound
)

from db_interface import (
    get_latest_log,
    find_known_failure_match,
    log_incident,
    update_incident_status,
    get_incident_by_id,
    order_exists,
    container_exists,
    get_latest_incident_by_order_or_container
)

from email_utils import send_email_to_it


def _handle_summary_request(session_state: Dict[str, Any], incident_id: Optional[str], order_id: Optional[str], container_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """
    Handles user's request for an incident summary.
    Supports incident_id, order_id, container_id combinations with improved mismatch handling.
    """
    # Case 1: No IDs at all
    if not incident_id and not order_id and not container_id:
        msg = request_missing_summary_ids()
        return msg, session_state

    # Case 2: Incident ID is provided
    incident_row = None
    if incident_id:
        incident_row = get_incident_by_id(incident_id)
        if not incident_row:
            msg = phrase_mismatch_or_notfound({"type": "notfound", "incident_id": incident_id})
            return msg, session_state

        mismatches = []
        if order_id and incident_row.get("order_id") and incident_row["order_id"] != order_id:
            mismatches.append(
                f"Order ID mismatch: incident {incident_id} has {incident_row['order_id']} but you gave {order_id}"
            )
        if container_id and incident_row.get("container_id") and incident_row["container_id"] != container_id:
            mismatches.append(
                f"Container ID mismatch: incident {incident_id} has {incident_row['container_id']} but you gave {container_id}"
            )

        if mismatches:
            msg = phrase_mismatch_or_notfound({"type": "mismatch", "incident_id": incident_id, "details": mismatches})
            return msg, session_state

        # Use IDs from incident
        order_id = incident_row.get("order_id")
        container_id = incident_row.get("container_id")

    # Case 3: No incident, but order/container given
    else:
        if order_id and not order_exists(order_id):
            msg = phrase_mismatch_or_notfound({"type": "notfound", "provided_order_id": order_id})
            return msg, session_state
        if container_id and not container_exists(container_id):
            msg = phrase_mismatch_or_notfound({"type": "notfound", "provided_container_id": container_id})
            return msg, session_state

        incident_row = get_latest_incident_by_order_or_container(order_id, container_id)
        if not incident_row:
            msg = phrase_mismatch_or_notfound({"type": "notfound", "provided_order_id": order_id, "provided_container_id": container_id})
            return msg, session_state

        incident_id = incident_row["incident_id"]

    # Build summary facts
    facts = {
        "incident_id": incident_id,
        "incident_status": incident_row.get("status") if incident_row else "Unknown",
        "order_id": order_id,
        "container_id": container_id,
    }

    session_state["incident_id"] = incident_id

    summary_msg = draft_summary_message(facts)
    return summary_msg, session_state


def handle_user_message(user_input, session_state):
    if session_state is None:
        session_state = {"incident_id": None, "order_id": None, "container_id": None, "status": None}

    # ---- Centralized ID extraction ----
    extracted = extract_ids(user_input)
    incident_id = extracted.get("incident_id")
    order_id = extracted.get("order_id")
    container_id = extracted.get("container_id")

    # Merge with existing session
    session_state["incident_id"] = session_state.get("incident_id") or incident_id
    session_state["order_id"] = session_state.get("order_id") or order_id
    session_state["container_id"] = session_state.get("container_id") or container_id

    # LLM detects intent
    intent = detect_intent(user_input)
    print(f"[DEBUG] Detected intent: {intent}")

    # --- Greeting / Thanks / End ---

    if intent == "greeting" and not session_state.get("incident_id"):
        return handle_greeting(), session_state

    if intent in ["thanks", "end_of_convo"]:
        return handle_thanks(), session_state

     # --- SESSION-AWARE SUMMARY HANDLING ---
    if session_state.get("last_summary_request") or intent == "summary":
        # Update last_summary_request with latest IDs
        session_state["last_summary_request"] = {
            "incident_id": session_state.get("incident_id"),
            "order_id": session_state.get("order_id"),
            "container_id": session_state.get("container_id")
        }
        summary_msg, session_state = _handle_summary_request(
            session_state,
            session_state.get("incident_id"),
            session_state.get("order_id"),
            session_state.get("container_id")
        )
        return summary_msg, session_state



    # --- New issue handling ---
    issue_resolved_or_escalated = session_state.get("status") in ["Resolved", "EscalatedToIT", "Open"]
    if intent == "new_issue" and issue_resolved_or_escalated:
        session_state.clear()
        session_state = {"incident_id": None, "order_id": None, "container_id": None, "status": None}
        extracted = extract_ids(user_input)
        order_id = extracted.get("order_id")
        container_id = extracted.get("container_id")
        if not order_id and not container_id:
            return "Sure, let’s take a look at your new issue. Could you please share the Order ID or Container ID?", session_state
        session_state["order_id"] = order_id
        session_state["container_id"] = container_id

    # --- Ensure IDs are set ---
    order_id = session_state.get("order_id")
    container_id = session_state.get("container_id")
    if not order_id and not container_id:
        prompt = request_missing_id(order_id, container_id)
        return prompt, session_state

    # --- Check logs ---
    latest_log = get_latest_log(order_id=order_id, container_id=container_id)
    if not latest_log:
        return f"I couldn't find any recent activity for the given {'order ID' if order_id else 'container ID'}. Could you double-check the ID and try again?", session_state

    # --- Log incident if new ---
    if not session_state.get("incident_id"):
        summary = f"Issue with Order {order_id}" if order_id else f"Issue with Container {container_id}"
        incident_id = log_incident(order_id, container_id, summary)
        session_state["incident_id"] = incident_id
        session_state["status"] = "In Progress"

    update_incident_status(session_state["incident_id"], "In Progress")

    # --- Handle success confirmation ---
    log_status = latest_log.get("status", "").lower()
    if log_status == "success" and not session_state.get("awaiting_success_confirmation"):
        session_state["awaiting_success_confirmation"] = True
        return f"I checked the CMS logs for {order_id or container_id}, and everything looks fine on our side. Do you still notice an issue with your order?", session_state

    if session_state.get("awaiting_success_confirmation"):
        incident_id = session_state.get("incident_id")
        confirmation = user_confirmation(user_input)
        if confirmation == "issue_persists":
            if not incident_id:
                incident_id = log_incident(order_id, container_id, "User confirmed issue despite success status")
                session_state["incident_id"] = incident_id
            update_incident_status(incident_id, "Open")
            subject = f"Escalation Request: Issue despite success response {order_id or container_id}"
            summary = f"The incident with order/container ({order_id or container_id}) has successful response from CMS, but the user still faces issue.\n\nIncident ID: {incident_id}\nPlease investigate potential underlying issues."
            email_body = draft_email_content(summary)
            send_email_to_it(subject, body=email_body)
            session_state["awaiting_success_confirmation"] = False
            session_state["status"] = "EscalatedToIT"
            return "I've escalated this to IT and sent them an email.\n\n" + email_body, session_state
        elif confirmation == "issue_resolved":
            session_state["awaiting_success_confirmation"] = False
            update_incident_status(incident_id, "Closed")
            session_state["status"] = "Resolved"
            return "Okay, I will close this incident.", session_state
        else:
            return "Please confirm if you still see an issue with the order. Reply with yes or no.", session_state

    # --- Known failure handling ---
    response_payload = latest_log.get("response_xml", "")
    match = find_known_failure_match(response_payload)
    if match:
        issue_type = match.get("failure_type")
        phrased_response = phrase_workaround(match["workaround"], issue_type)
        session_state["awaiting_user_confirmation"] = True
        return phrased_response, session_state

    # --- Unknown failure ---
    summary = f"Issue reported for Order {order_id or ''} / Container {container_id or ''}. No known pattern matched."
    email_body = draft_email_content(summary)
    session_state["status"] = "EscalatedToIT"
    return "I'm unable to resolve this with known workarounds. I've escalated the issue to our IT team. They’ll look into it shortly.\n\n" + email_body, session_state


def handle_user_confirmation(user_input, session_state):
    result = interpret_user_confirmation(user_input)

    if result == "success":
        update_incident_status(session_state["incident_id"], "Resolved")
        session_state["status"] = "Resolved"
        session_state["awaiting_user_confirmation"] = False
        return "Great! I'm glad that resolved your issue. Let me know if you need help with anything else.", session_state

    elif result == "failure":
        update_incident_status(session_state["incident_id"], "Open")
        subject = f"Escalation Request: Workaround failed for {session_state['order_id'] or session_state['container_id']}"
        summary = f"User confirmed workaround failed for Order / Container - {session_state['order_id'] or session_state['container_id']}. Incident ID: {session_state['incident_id']}"
        email_body = draft_email_content(summary)
        send_email_to_it(subject, body=email_body)
        session_state["status"] = "EscalatedToIT"
        session_state["awaiting_user_confirmation"] = False
        return "Thanks for confirming. I've escalated this to our IT team for further investigation.\n\n" + email_body, session_state

    else:
        return "Just to confirm, did the workaround resolve the issue? Please reply with yes or no.", session_state

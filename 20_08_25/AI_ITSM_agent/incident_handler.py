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
    get_latest_incident_by_order_or_container,
    get_all_incidents_by_order_or_container
)

from email_utils import send_email_to_it


def _handle_summary_request(session_state: Dict[str, Any],
                            incident_id: Optional[str],
                            order_id: Optional[str],
                            container_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """
    Handles a user's request for an incident summary.
    Fully stateless: ignores any session pending incidents or statuses.
    Fetches incident by provided IDs or asks for missing ones.
    Handles multiple incidents by asking user to pick one.
    """

    explicit_id_provided = bool(incident_id or order_id or container_id)

    if not explicit_id_provided:
        msg = request_missing_summary_ids()
        return msg, session_state

    incident_row = None

    # Incident ID provided
    if incident_id:
        incident_row = get_incident_by_id(incident_id)
        if not incident_row:
            msg = phrase_mismatch_or_notfound({"type": "notfound", "incident_id": incident_id})
            return msg, session_state

        # Check mismatches if order/container IDs are provided
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

        order_id = incident_row.get("order_id")
        container_id = incident_row.get("container_id")

    # Only order/container provided
    else:
        if order_id and not order_exists(order_id):
            msg = phrase_mismatch_or_notfound({"type": "notfound", "provided_order_id": order_id})
            return msg, session_state
        if container_id and not container_exists(container_id):
            msg = phrase_mismatch_or_notfound({"type": "notfound", "provided_container_id": container_id})
            return msg, session_state

        all_incidents = get_all_incidents_by_order_or_container(order_id, container_id)
        if not all_incidents:
            msg = phrase_mismatch_or_notfound({
                "type": "notfound",
                "provided_order_id": order_id,
                "provided_container_id": container_id
            })
            return msg, session_state

        if len(all_incidents) > 1:
            choices = "\n".join([
                f"- Incident {row['incident_id']} (Status: {row['status']}, Created: {row.get('created_at','N/A')})"
                for row in all_incidents
            ])
            msg = (
                f"I found multiple incidents linked to Order {order_id or ''} / Container {container_id or ''}:\n\n"
                f"{choices}\n\n"
                f"Could you please specify which incident ID you'd like details for?"
            )
            session_state["pending_incident_choice_for_summary"] = [row["incident_id"] for row in all_incidents]
            return msg, session_state

        incident_row = all_incidents[0]
        incident_id = incident_row["incident_id"]

    # --- NEW PART: enrich with cms + failure ---
    cms_log = get_latest_log(order_id=order_id, container_id=container_id)
    issue_summary, workaround = None, None
    if cms_log:
        failure = find_known_failure_match(cms_log["response_xml"])
        if failure:
            issue_summary = failure["failure_type"]
            workaround = failure["workaround"]    

    facts = {
        "incident_id": incident_id,
        "incident_status": incident_row.get("status") if incident_row else "Unknown",
        "order_id": order_id,
        "container_id": container_id,
        "incident_created_at": incident_row.get("created_at") if incident_row else None,
        "issue_summary": issue_summary,
        "workaround": workaround
    }

    session_state["last_summary_incident_id"] = incident_id
    summary_msg = draft_summary_message(facts)
    return summary_msg, session_state


def handle_user_message(user_input, session_state):
    if session_state is None:
        session_state = {"incident_id": None, "order_id": None, "container_id": None, "status": None}

    session_state["last_user_message"] = user_input
    extracted = extract_ids(user_input)
    incident_id = extracted.get("incident_id")
    order_id = extracted.get("order_id")
    container_id = extracted.get("container_id")

    # Update session IDs if present
    if incident_id:
        session_state["incident_id"] = incident_id
    if order_id:
        session_state["order_id"] = order_id
    if container_id:
        session_state["container_id"] = container_id

    # --- NEW: Check if message is only IDs ---
    only_ids_provided = all([
        user_input.strip().lower() in 
        [str(incident_id or "").lower(), str(order_id or "").lower(), str(container_id or "").lower()]
    ])

    # If only IDs provided, skip detection and continue with last intent
    if not only_ids_provided:
        intent = detect_intent(user_input)
        print(f"[DEBUG] Detected intent: {intent}")
        if intent:
            session_state["last_intent"] = intent
    else:
        # Carry forward the previous intent
        intent = session_state.get("last_intent")
        print(f"[DEBUG] Continuing with last intent: {intent}")


    # --- Greeting / Thanks ---
    if intent == "greeting" and not session_state.get("incident_id"):
        return handle_greeting(), session_state
    if intent in ["thanks", "end_of_convo"]:
        return handle_thanks(), session_state

    # --- Handle summary flow ---
    if session_state.get("pending_incident_choice_for_summary"):
        if incident_id and incident_id in session_state["pending_incident_choice_for_summary"]:
            session_state.pop("pending_incident_choice_for_summary", None)
            summary_msg, session_state = _handle_summary_request(
                session_state, incident_id, None, None
            )
            return summary_msg, session_state
        else:
            return f"Please reply with one of the valid incident IDs: {', '.join(session_state['pending_incident_choice_for_summary'])}", session_state

    if intent == "summary":
        summary_msg, session_state = _handle_summary_request(
            session_state,
            incident_id,
            order_id,
            container_id
        )
        return summary_msg, session_state

    # --- New issue flow ---
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

    # Ensure IDs are set
    order_id = session_state.get("order_id")
    container_id = session_state.get("container_id")
    if not order_id and not container_id:
        prompt = request_missing_id(order_id, container_id)
        return prompt, session_state

    # Check latest log
    latest_log = get_latest_log(order_id=order_id, container_id=container_id)
    if not latest_log:
        return f"I couldn't find any recent activity for the given {'order ID' if order_id else 'container ID'}. Could you double-check the ID and try again?", session_state

    # Log incident if new
    if not session_state.get("incident_id"):
        summary = f"Issue with Order {order_id}" if order_id else f"Issue with Container {container_id}"
        incident_id = log_incident(order_id, container_id, summary)
        session_state["incident_id"] = incident_id
        session_state["status"] = "In Progress"

    update_incident_status(session_state["incident_id"], "In Progress")

    # Handle success confirmation
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

    # Known failure handling
    response_payload = latest_log.get("response_xml", "")
    match = find_known_failure_match(response_payload)
    if match:
        issue_type = match.get("failure_type")
        phrased_response = phrase_workaround(match["workaround"], issue_type)
        session_state["awaiting_user_confirmation"] = True
        return phrased_response, session_state

    # Unknown failure
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

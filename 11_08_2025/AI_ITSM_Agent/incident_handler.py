from llm_interface import (
    ask_llm,
    extract_ids,
    request_missing_id,
    phrase_workaround,
    draft_email_content,
    interpret_user_confirmation,
    detect_intent,
    handle_greeting,
    handle_thanks

)

from db_interface import (
    get_latest_log,
    find_known_failure_match,
    log_incident,
    update_incident_status
)

from email_utils import send_email_to_it

def handle_user_message(user_input, session_state):
    # LLM detects intent of the message
    intent = detect_intent(user_input)

    # Greet the user if greeting
    if intent == "greeting" and not session_state.get("incident_id"):
        return handle_greeting(), session_state

    # Respond politely if it's a thank you
    if intent == "thanks" or intent == "end_of_convo":
        return handle_thanks(), session_state

    # Handle 'new_issue' only if the previous one is resolved or escalated
    issue_resolved_or_escalated = session_state.get("status") in ["Resolved", "EscalatedToIT", "Open"]


    # If new issue is being reported — reset session
    if intent == "new_issue" and issue_resolved_or_escalated:
        session_state.clear()

        # Step 1: Try extracting order/container ID from user message
        extracted = extract_ids(user_input)
        order_id = extracted.get("order_id")
        container_id = extracted.get("container_id")
        if not order_id and not container_id:
            return (
            "Sure, let’s take a look at your new issue. Could you please share the Order ID or Container ID?",
            {
                "incident_id": None,
                "order_id": None,
                "container_id": None,
                "status": None
            }
        )

    # ------- Continue your regular flow below ----------

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

    
    log_status = latest_log["status"]
    if log_status.lower() == "success" and not session_state.get("awaiting_success_confirmation"):
        # Ask user for confirmation and set flag
        session_state["awaiting_success_confirmation"] = True
        return (
            f"I checked the CMS logs for {order_id or container_id}, and everything looks fine on our side. "
            "Do you still notice an issue with your order?",
            session_state
        )

    # Later, when user replies and confirmation expected:
    if session_state.get("awaiting_success_confirmation"):
        incident_id = session_state.get("incident_id") 
        confirmation = interpret_user_confirmation(user_input)  # This must return True/False

        if confirmation == "success":
            if not incident_id:
                incident_id = log_incident(order_id, container_id, "User confirmed issue despite success status")
                session_state["incident_id"] = incident_id
        # Update incident before escalation
            update_incident_status(incident_id, "Open")
        
        # Always send escalation email after confirmation
            subject = f"Escalation Request: Issue despite success response {order_id or container_id}"
            summary = (
                f"The incident with order/container ({order_id or container_id}) has successful response from CMS, "
                "but the user still faces issue with process the order / container and has requested escalation for further review.\n\n"
                f"Incident ID: {incident_id}\n"
                "Please investigate potential underlying issues."
            )
            email_body = draft_email_content(summary)
            send_email_to_it(subject, body = email_body)

            session_state["awaiting_success_confirmation"] = False
            session_state["status"] = "EscalatedToIT"

            return "I've escalated this to IT and sent them an email.\n\n" + email_body, session_state

        elif confirmation == "failure":
            # No escalation
            session_state["awaiting_success_confirmation"] = False
            update_incident_status(incident_id, "Closed")
            return "Okay, I will close this incident."

        else:
            # unclear, ask again politely
            return ("Please confirm if you still see an issue with the order. Reply with yes or no.", session_state)

    else:
        response_payload = latest_log["response_xml"]
        match = find_known_failure_match(response_payload)

        # Match against known failure
        if match:
            # Use LLM to phrase workaround naturally
            issue_type = match.get("failure_type")
            phrased_response = phrase_workaround(match["workaround"], issue_type)
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
        subject = f"Escalation Request: Workaround failed for {session_state['order_id'] or session_state['container_id']}"
        summary = (
            f"User confirmed workaround failed for Order / Container - {session_state['order_id'] or session_state['container_id']}."
            f"The incident is been tracked under Incident ID: {session_state['incident_id']}"
        )
        email_body = draft_email_content(summary)
        send_email_to_it(subject,body=email_body)
        session_state["status"] = "EscalatedToIT"
        session_state["awaiting_user_confirmation"] = False
        return (
            "Thanks for confirming. I've escalated this to our IT team for further investigation.\n\n" + email_body,
            session_state
        )

    else:
        return "Just to confirm, did the workaround resolve the issue? Please reply with yes or no.", session_state

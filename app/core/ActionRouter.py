import requests  # optional if you want to simulate external POSTs

def RouteAction(agent_output: dict):
    action = agent_output.get("suggested_action", "")
    result = {"action": action, "status": "unknown", "route": None}

    if action == "escalate":
        # Simulate POST to CRM
        print(f"[Action Router] Escalating to CRM: {agent_output.get('sender')}")
        # response = requests.post("http://localhost:8000/crm/escalate", json=agent_output) # optional
        result["status"] = "success"
        result["route"] = "/crm/escalate"

    elif action == "log_and_close":
        print("[Action Router] Logging and closing the ticket.")
        result["status"] = "success"
        result["route"] = "log_only"

    elif action == "trigger_alert":
        print("[Action Router] Alerting compliance team.")
        result["status"] = "success"
        result["route"] = "/risk_alert"

    else:
        print(f"[Action Router] Unknown action: {action}")
        result["status"] = "failed"

    return result

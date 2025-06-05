import requests 
import logging
from memory.MemoryStore import update_action_status
import config


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def RouteAction(agent_output: dict):
    action = agent_output.get("suggested_action", "")
    result = {"action": action, "status": "unknown", "route": None}
    
    logger.debug(f"RouteAction received agent_output: {agent_output}")
    
    if action == "escalate":
        logger.info(f"[Action Router] Escalating to CRM: {agent_output.get('sender')}")
        # Simulate POST to CRM
        # response = requests.post("http://localhost:8000/crm/escalate", json=agent_output) # optional
        result["status"] = "success"
        result["route"] = "/crm/escalate"

    elif action == "log_and_close":
        logger.info("[Action Router] Logging and closing the ticket.")
        result["status"] = "success"
        result["route"] = "log_only"

    elif action == "trigger_alert":
        logger.info("[Action Router] Alerting compliance team.")
        result["status"] = "success"
        result["route"] = "/risk_alert"

    else:
        logger.warning(f"[Action Router] Unknown action: {action}")
        result["status"] = "failed"
    
    run_id = config.CURRENT_RUN_ID  # Ensure you have the run_id set in your config
    # RouteAction returns a result including a status (e.g., "success" or "failed")
    update_action_status(run_id, result["status"])
    logger.info("### Memory Update")
    logger.info(f"Action status updated in memory for run_id: {run_id}")

    logger.debug(f"RouteAction result: {result}")
    return result
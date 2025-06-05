import sqlite3
import json
from datetime import datetime

DB_PATH = "memory1.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Creates the `workflow_run` table if it doesn’t exist.
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS workflow_run (
        run_id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        file_path TEXT NOT NULL,
        original_ext TEXT NOT NULL,
        received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        detected_format TEXT,
        intent TEXT,
        llm_classification TEXT,
        email_agent_output TEXT,
        pdf_agent_output TEXT,
        json_agent_output TEXT,
        routed_to_agent TEXT,
        action_taken TEXT,
        action_payload TEXT,
        action_status TEXT,
        current_status TEXT,
        last_updated DATETIME,
        history TEXT
    );
    """
    with get_conn() as conn:
        conn.execute(create_sql)
        conn.commit()

def append_history(history_json: str, event: str, details: dict) -> str:
    """
    Given the existing history_json (or None), append a new event.
    Returns updated JSON string.
    """
    now = datetime.now().isoformat()
    entry = {"timestamp": now, "event": event, "details": details}

    if not history_json:
        new_history = {"log": [entry]}
    else:
        hist = json.loads(history_json)
        hist["log"].append(entry)
        new_history = hist

    return json.dumps(new_history)

def insert_run(run_id: str, source: str, file_path: str, original_ext: str):
    """
    Called by File Processor when a new file arrives.
    """
    event_details = {
        "source": source,
        "original_ext": original_ext,
        "file_path": file_path
    }
    history = append_history(None, "file_received", event_details)

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO workflow_run (
                run_id, source, file_path, original_ext, current_status, last_updated, history
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, source, file_path, original_ext, "received",
              datetime.now().isoformat(), history))
        conn.commit()

def update_after_classification(run_id: str, detected_format: str, intent: str, llm_output: str, routed_to: str):
    """
    Called by Classifier Agent.
    """
    with get_conn() as conn:
        row = conn.execute("SELECT history FROM workflow_run WHERE run_id = ?", (run_id,)).fetchone()
        history = append_history(row["history"],
                                 "classified",
                                 {"detected_format": detected_format,
                                  "intent": intent,
                                  "llm_output": llm_output,
                                  "routed_to_agent": routed_to})

        conn.execute("""
            UPDATE workflow_run
            SET detected_format = ?, intent = ?, llm_classification = ?,
                routed_to_agent = ?, current_status = ?, last_updated = ?, history = ?
            WHERE run_id = ?
        """, (detected_format, intent, llm_output, routed_to,
              "classified", datetime.now().isoformat(), history, run_id))
        conn.commit()

def update_pdf_agent(run_id: str, pdf_output: dict, action_taken: str, action_payload: dict):
    """
    Called by PDF Agent.
    pdf_output: Python dict (will be converted to JSON string)
    action_payload: Python dict
    """
    pdf_json = json.dumps(pdf_output)
    payload_json = json.dumps(action_payload)

    with get_conn() as conn:
        row = conn.execute("SELECT history FROM workflow_run WHERE run_id = ?", (run_id,)).fetchone()
        history = append_history(row["history"],
                                 "pdf_processed",
                                 {
                                     "pdf_agent_output": pdf_output,
                                     "action_taken": action_taken,
                                     "action_payload": action_payload
                                 })

        conn.execute("""
            UPDATE workflow_run
            SET pdf_agent_output = ?, action_taken = ?, action_payload = ?,
                current_status = ?, last_updated = ?, history = ?
            WHERE run_id = ?
        """, (pdf_json, action_taken, payload_json,
              "processed", datetime.now().isoformat(), history, run_id))
        conn.commit()

def update_json_agent(run_id: str, json_output: dict, action_taken: str, action_payload: dict):
    json_str = json.dumps(json_output)
    payload_str = json.dumps(action_payload)

    with get_conn() as conn:
        row = conn.execute("SELECT history FROM workflow_run WHERE run_id = ?", (run_id,)).fetchone()
        history = append_history(row["history"],
                                 "json_processed",
                                 {
                                     "json_agent_output": json_output,
                                     "action_taken": action_taken,
                                     "action_payload": action_payload
                                 })

        conn.execute("""
            UPDATE workflow_run
            SET json_agent_output = ?, action_taken = ?, action_payload = ?,
                current_status = ?, last_updated = ?, history = ?
            WHERE run_id = ?
        """, (json_str, action_taken, payload_str,
              "processed", datetime.now().isoformat(), history, run_id))
        conn.commit()

def update_email_agent(run_id: str, email_output: dict, action_taken: str, action_payload: dict):
    email_str = json.dumps(email_output)
    payload_str = json.dumps(action_payload)

    with get_conn() as conn:
        row = conn.execute("SELECT history FROM workflow_run WHERE run_id = ?", (run_id,)).fetchone()
        history = append_history(row["history"],
                                 "email_processed",
                                 {
                                     "email_agent_output": email_output,
                                     "action_taken": action_taken,
                                     "action_payload": action_payload
                                 })

        conn.execute("""
            UPDATE workflow_run
            SET email_agent_output = ?, action_taken = ?, action_payload = ?,
                current_status = ?, last_updated = ?, history = ?
            WHERE run_id = ?
        """, (email_str, action_taken, payload_str,
              "processed", datetime.now().isoformat(), history, run_id))
        conn.commit()

def update_action_status(run_id: str, action_status: str):
    with get_conn() as conn:
        row = conn.execute("SELECT action_taken, action_payload, history FROM workflow_run WHERE run_id = ?", (run_id,)).fetchone()
        event_details = {
            "action_taken": row["action_taken"],
            "action_payload": json.loads(row["action_payload"]) if row["action_payload"] else None,
            "action_status": action_status
        }
        history = append_history(row["history"], "action_routed", event_details)

        new_status = "complete" if action_status == "success" else "error"
        conn.execute("""
            UPDATE workflow_run
            SET action_status = ?, current_status = ?, last_updated = ?, history = ?
            WHERE run_id = ?
        """, (action_status, new_status, datetime.now().isoformat(), history, run_id))
        conn.commit()
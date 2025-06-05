import os
import re
import json
import logging

from langchain.prompts import PromptTemplate
from .llm import llm  # Reuse the shared LLM instance
from memory.MemoryStore import update_json_agent
import config

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Define the JSON validation prompt
json_validation_prompt = PromptTemplate(
    input_variables=["payload"],
    template="""
You are a JSON Validation Agent responsible for validating structured JSON payloads received via webhook in a financial services context. Your job is to detect any schema violations or real-time business logic anomalies in the payload and classify their severity.

The types of documents you will receive are typically:
- Invoices
- Payslips
- Quotations

🎯 Your Task:
Validate Schema:
- Ensure required fields are present.
- Validate data types (e.g., string, number, date).
- Accept extra fields but flag them as minor anomalies.

Check Business Rules (Real-Time Anomalies):
- Dates should be realistic (no future issue_date, pay_period).
- due_date should not be before issue_date.
- net_pay should not exceed gross salary.
- Sum of line items should match the total_amount.
- Currency should be consistent across line items and summary.
- Detect duplicate invoice_id, quote_id, etc.

Classify Each Anomaly:
- critical: Requires immediate escalation (e.g., future-dated invoice, mismatched totals, duplicate ID).
- minor: Log-only, doesn't require immediate action (e.g., extra fields, date formatting, unused optional fields).

Response Format (on each payload):
Respond strictly in valid JSON with the following format:
{{
  "status": "valid" | "invalid",
  "anomalies": [
    {{
      "field": "due_date",
      "description": "Due date is before issue date.",
      "severity": "critical"
    }},
    {{
      "field": "note",
      "description": "Extra field not in schema.",
      "severity": "minor"
    }}
  ],
  "suggested_action": "log_and_close" | "trigger_alert"
}}

If no critical anomalies are found, set "status": "valid" and "action": "log_and_close".
If one or more critical anomalies are found, set "status": "invalid" and "action": "trigger_alert".

Here is the JSON payload to validate:
{payload}
"""
)

# Build the chain by chaining the prompt and the shared LLM
json_agent_chain = json_validation_prompt | llm

def extract_json_from_text(raw_text: str) -> dict:
    """
    Extracts the substring between the first '{' and the last '}' in the text.
    Attempts to parse it as JSON and return the object.
    If parsing fails, returns an empty dictionary.
    """
    logger.debug("Extracting JSON from JSON agent output.")
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_str = raw_text[start:end + 1]
        try:
            parsed = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
    else:
        logger.warning("No JSON brackets found in the output.")
    
    return {}

def processJson(payload_text: str) -> dict:
    """
    Processes the JSON payload using the JSON agent chain.
    Returns a dictionary with the validation result.
    """
    logger.info("Processing JSON payload through JsonAgent chain.")

    try:
        llm_output = json_agent_chain.invoke({"payload": payload_text})
        logger.debug("JsonAgent chain invoked successfully.")
        logger.debug(f"LLM output: {llm_output}")
    except Exception as e:
        logger.error("Error invoking JSON agent chain.", exc_info=True)
        raise e

    try:
        output_str = llm_output.content.strip()
        logger.debug(f"LLM output after stripping: {output_str[:200]}...")  # Log first 200 chars
    except Exception as e:
        logger.error("Error processing LLM output for JSON payload.", exc_info=True)
        raise e

    try:
        extracted = extract_json_from_text(output_str)
        if not extracted:
            logger.error("No valid JSON extracted from JSON agent output.")
            raise ValueError("No valid JSON found in LLM output.")
        logger.info(f"JSON validation successful: {extracted}")

        run_id = config.CURRENT_RUN_ID
        json_output = extracted
        action_taken = extracted.get("suggested_action" , "unknown")  # if anomalies exist, for example
        action_payload = {  }         # additional info
        update_json_agent(run_id, json_output, action_taken, action_payload)
        logger.info("#### Memory Update")
        logger.info(f"JSON agent run_id: {run_id}, action taken: {action_taken}, payload: {action_payload}")


        return extracted
    except Exception as e:
        logger.error("Error extracting JSON validation result.", exc_info=True)
        raise ValueError(f"Error extracting JSON validation result: {e}")

# For testing purposes, you can run this script directly.
if __name__ == "__main__":
    test_payload = """
{
  "id": "fa4da2ff-dcda-4367-a97d-0c9445147b73",
  "items": [
    {
      "name": "Canvas Slip Ons",
      "code": "CVG-096732",
      "description": "Shoes",
      "quantity": "1",
      "amount": {
        "value": 1000
      },
      "totalAmount": {
        "value": 1000
      }
    }
  ],
  "requestReferenceNumber": "5fc10b93-bdbd-4f31-b31d-4575a3785009",
  "receiptNumber": "7fa0ff6fa5a6",
  "createdAt": "2021-07-13T15:25:45.000Z",
  "updatedAt": "2021-07-13T15:26:49.000Z",
  "paymentScheme": "master-card",
  "expressCheckout": true,
  "refundedAmount": "0",
  "canPayPal": false,
  "expiredAt": "2021-07-13T16:25:45.000Z",
  "status": "COMPLETED",
  "paymentStatus": "PAYMENT_SUCCESS"
}
"""
    result = processJson(test_payload)
    logger.info("JSON Validation Result:")
    logger.info(result)
    print(result)
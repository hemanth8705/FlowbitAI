import os
import re
import json
import logging

from langchain.prompts import PromptTemplate
from .llm import llm  # Reuse the shared LLM instance

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Define the email extraction prompt
email_extraction_prompt = PromptTemplate(
    input_variables=["email"],
    template="""
You are an intelligent email processing agent.

Your task is to extract the following fields from the email text:
- Sender
- Urgency (High, Medium, Low)
- Issue or Request
- Tone (Escalation, Polite, Threatening)
- suggested_action (escalate, log_and_close, alert_risk)

Here is the email:
{email}

I will directly use json.loads(response) on your output so please respond in valid JSON format only.
Respond in the following JSON format:
{{
  "sender": "...",
  "urgency": "...",
  "CotentSummary": "...",
  "tone": "...",
  "suggested_action": "..."
}}
"""
)

# Build the chain by chaining the prompt and LLM
email_agent_chain = email_extraction_prompt | llm

def extract_json_from_text(raw_text: str) -> dict:
    """
    Extracts the substring between the first '{' and the last '}' in the text.
    Attempts to parse it as JSON and return the object.
    If parsing fails, returns an empty dictionary.
    """
    logger.debug("Extracting JSON from email LLM output.")
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

def processEmail(email_text: str) -> dict:
    """
    Processes the email text using the email agent chain.
    Returns a dictionary with the extracted fields.
    """
    logger.info("Processing email text through EmailAgent chain.")
    logger.debug(f"Email text: {email_text[:100]}...")  # Log first 100 chars

    try:
        llm_output = email_agent_chain.invoke({"email": email_text})
        logger.debug("Email agent chain invoked successfully.")
    except Exception as e:
        logger.error("Error invoking email agent chain.", exc_info=True)
        raise e

    try:
        output_str = llm_output.content.strip()
        logger.debug(f"LLM output after stripping: {output_str[:200]}...")  # Log first 200 chars
    except Exception as e:
        logger.error("Error processing LLM output for email.", exc_info=True)
        raise e

    try:
        extracted = extract_json_from_text(output_str)
        if not extracted:
            logger.error("No valid JSON extracted from email LLM output.")
            raise ValueError("No valid JSON found in LLM output.")
        logger.info(f"Email processing successful: {extracted}")
        return extracted
    except Exception as e:
        logger.error("Error extracting email fields.", exc_info=True)
        raise ValueError(f"Error extracting email fields: {e}")

# For testing purposes
if __name__ == "__main__":
    sample_email = """
Subject: Immediate Attention Required: Overcharged on Last Invoice

Dear Support Team,

I am writing to express my frustration regarding an issue with my recent invoice (Invoice #12345). I noticed that I was charged an amount higher than what was initially quoted to me during the sales call. This discrepancy is significant and I request an immediate resolution to this problem.

On March 15th, 2025, I had a call with one of your sales representatives, and we discussed the pricing. The quoted price was $1200, but the invoice I received lists the total as $1500. This $300 overcharge is unacceptable.

I expect prompt attention to adjust the invoice accordingly.

Sincerely,
John Doe
8121812181
example@gmail.com
"""
    result = processEmail(sample_email)
    logger.info("Extracted Email Fields:")
    logger.info(result)
    print(result)


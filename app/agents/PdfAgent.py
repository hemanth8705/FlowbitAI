import os
import re
import json
import logging

from langchain.prompts import PromptTemplate
from .llm import llm  # Reuse the shared LLM instance

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.getLogger("pdfminer").setLevel(logging.WARNING)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Define the PDF extraction and validation prompt
pdf_extraction_prompt = PromptTemplate(
    input_variables=["pdf_text"],
    template="""
You are a PDF Data Extraction and Validation Agent. Your job is to analyze text extracted from PDF documents and:

Identify the document type: either an Invoice or a Policy Document.

For Invoices:
- Extract key fields including:
  - Invoice Number/ID
  - Issue Date
  - Due Date
  - Customer Name
  - Line items (each with: description, quantity, unit price, tax, amount)
  - Currency
  - Total Amount
- Validate that the total amount matches the sum of line items.
- Flag a critical anomaly if the invoice total exceeds 10,000 (in any currency).

For Policy Documents:
- Identify mentions of specific regulatory keywords such as "GDPR", "FDA", "HIPAA", or "SOX".
- If any of these keywords are found, flag a critical anomaly indicating compliance relevance.

Respond in the following JSON format:
{{
  "document_type": "invoice" | "policy",
  "extracted_data": {{
    // key-value pairs depending on document type
  }},
  "anomalies": [
    {{
      "field": "total_amount",
      "description": "Invoice total exceeds threshold of 10,000.",
      "severity": "critical"
    }}
  ],
  "suggested_action": "log_and_close" | "trigger_alert"
}}

If no anomalies are found, set "anomalies": [] and "action": "log_and_close".

Here is the extracted PDF text:
{pdf_text}
"""
)

# Build the chain by chaining the prompt with the shared LLM
pdf_agent_chain = pdf_extraction_prompt | llm

def extract_json_from_text(raw_text: str) -> dict:
    """
    Extracts the substring between the first '{' and the last '}' in the text.
    Attempts to parse it as JSON and return the object.
    If parsing fails, returns an empty dictionary.
    """
    logger.debug("Extracting JSON from Pdf agent output.")
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

def processPdf(pdf_text: str) -> dict:
    """
    Processes extracted PDF text using the PDF agent chain.
    Returns a dictionary containing documents type, extracted data, anomalies, and suggested action.
    """
    logger.info("Processing PDF text through PDF agent chain.")
    logger.debug(f"PDF text received for processing: {pdf_text[:100]}...")  # Log first 100 characters
    
    try:
        llm_output = pdf_agent_chain.invoke({"pdf_text": pdf_text})
        logger.debug("PDF agent chain invoked successfully.")
    except Exception as e:
        logger.error("Error invoking PDF agent chain.", exc_info=True)
        raise e

    try:
        # Ensure we have a string output and strip whitespace
        output_str = str(llm_output.content).strip()
        logger.debug(f"LLM output after stripping: {output_str[:100]}...")  # Log first 100 characters
    except Exception as e:
        logger.error("Error processing LLM output.", exc_info=True)
        raise e

    try:
        extracted = extract_json_from_text(output_str)
        if not extracted:
            logger.error("No valid JSON extracted from LLM output.")
            raise ValueError("No valid JSON found in LLM output.")
        logger.info(f"PDF processing successful, extracted data: {extracted}")
        return extracted
    except Exception as e:
        logger.error("Error extracting PDF data.", exc_info=True)
        raise ValueError(f"Error extracting PDF validation result: {e}")

# For testing purposes
if __name__ == "__main__":
    test_pdf_text = """
Invoice Document

Invoice Number: INV-98765
Issue Date: 2025-06-01
Due Date: 2025-06-15
Customer Name: XYZ Corporation
Line Items:
  - Description: Consulting Service, Quantity: 2, Unit Price: 3000, Tax: 300, Amount: 6300
Currency: USD
Total Amount: 6300

This is a sample invoice extracted from a PDF.
"""
    result = processPdf(test_pdf_text)
    logger.info("PDF Agent Result:")
    logger.info(result)
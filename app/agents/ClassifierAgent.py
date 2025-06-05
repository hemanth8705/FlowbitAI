import os
import pickle
import re
import json

from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from .llm import llm
import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Only want application logs on console/file; set noisy external libraries to WARNING.
logging.getLogger("groq._base_client").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


from memory.MemoryStore import update_after_classification



# Optionally add console handler if not configured elsewhere:
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)



# Load external examples from JSON file
examples_file = os.path.join(os.path.dirname(__file__), "FewShotExamples", "ClassifierAgentExamples.pkl")
logger.info(f"Loading Few Shot examples from {examples_file}")
try:
    with open(examples_file, "rb") as f:
        examples = pickle.load(f)
    logger.info("Examples loaded successfully.")
except Exception as e:
    logger.error("Failed to load examples file.", exc_info=True)
    raise e


example_prompt = PromptTemplate(
    input_variables=["text", "format", "intent"],
    template="Input: {text}\nFormat: {format}\nIntent: {intent}\n"
)

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix="""
     You are given the shot examples to learn how to format and extract the intent from the given input.
     Act as a classifier agent that classifies the input text into:
       Format (email, json, pdf)
       Intent (complaint, invoice, rfq, fraud risk, regulation)
     Give the output in the following JSON format:
     {{ "format": "<format>", "intent": "<intent>" }}
     dont give any other information or explanation.
    """,
    suffix="Input: {input}\nFormat:",
    input_variables=["input"]
)

classifier_chain = prompt | llm

def extract_json_from_text(raw_text: str) -> dict:
    """
    Extracts the substring between the first '{' and the last '}' in the text.
    Attempts to parse it as JSON and return the object.
    If parsing fails, returns an empty dictionary.
    """
    logger.debug("Extracting JSON from Classifier LLM output.")
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



def classifyInput(input_text: str) -> dict:
    """
    Classifies the input text into a format and intent using the LLMChain.
    Returns a dictionary with 'format' and 'intent'.
    """
    logger.info("Classifying input text.")
    logger.info(">>>"*30)
    logger.debug(f"Input text: {input_text}")
    logger.info("<<<"*30)
    try:
        llm_output = classifier_chain.invoke({"input": input_text})
        logger.debug("LLM chain invoked successfully.")
        logger.debug(f"LLM output: {llm_output}")
    except Exception as e:
        logger.error("Error invoking classifier chain.", exc_info=True)
        raise e

    try:
        llm_output = llm_output.content.strip()
        logger.debug(f"LLM output after stripping: {llm_output}")
    except Exception as e:
        logger.error("Error processing LLM output.", exc_info=True)
        raise e

    try:
        classification = extract_json_from_text(llm_output)
        if not classification:
            logger.error("Extracted classification is empty. No valid JSON found.")
            raise ValueError("No valid JSON found in LLM output.")
        logger.info(f"Classification successful: {classification}")

        run_id = ...           # obtain the proper run_id for this file
        detected_format = classification.get("format", "")
        intent = classification.get("intent", "")
        routed_to = classification.get("format", "unknown")
        update_after_classification(config.CURRENT_RUN_ID, detected_format, intent, llm_output, routed_to)
        logger.info("### Memory Update")
        logger.info(f"Run ID: {config.CURRENT_RUN_ID}, Detected Format: {detected_format}, Intent: {intent}, Routed To: {routed_to}")
        return classification
    except Exception as e:
        logger.error("Error extracting classification.", exc_info=True)
        raise ValueError(f"Error extracting classification: {e}")
    

# For testing purposes, you can use this code:
if __name__ == "__main__":
    input_text = """
    - Item 1:
      Page_number: 1
      Text: Statement
    Statement Number 123
    Issue Date March 25, 2024
    Period February 24, 2024 - March 25, 2024
    Example, LLC Bill To
    123 Fake Street Customer
    New York City, NY 10012 Address
    (555) 867-5309 City, State Zipcode
    support@example.com customer@example.org
    Item Unit Cost Quantity Amount
    Subscription $19.00 1 $19.00
    Subtotal $19.00
    Tax Rate 0%
    Total $19.00
    For questions, contact us anytime at support@example.com.
      Tables:
    
      Ocr_text:
    """
    classification = classifyInput(input_text)
    print("Classification Result:")
    print(classification)
    # Example output:
    # Classification Result:
    # {'format': 'email', 'intent': 'invoice'}


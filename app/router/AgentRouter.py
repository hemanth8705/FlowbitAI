from agents.EmailAgent import processEmail
from agents.JsonAgent import processJson
from agents.PdfAgent import processPdf

def route_to_agent(file_path: str, classification: dict, extracted_text: str):
    """Routes the file to the appropriate agent based on its format and intent.
    Args:
        file_path (str): The path to the file being processed.
        classification (dict): A dictionary containing the classification results with keys 'format' and 'intent'.
        extracted_text (str): The text extracted from the file.
    Returns:
        dict: The result from the appropriate agent, or a message indicating an unknown format.
    """
    file_format = classification["format"].lower()

    if file_format == "email":
        return processEmail( extracted_text)
    elif file_format == "json":
        return processJson( extracted_text)
    elif file_format == "pdf":
        return processPdf(extracted_text)
    else:
        print("❌ Unknown format. No agent triggered.")
        return {"status": "skipped", "reason": "Unknown format"}

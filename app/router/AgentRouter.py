from agents.EmailAgent import processEmail
from agents.JsonAgent import processJson
from agents.PdfAgent import processPdf

def route_to_agent(file_path: str, classification: dict, extracted_text: str):
    file_format = classification["format"]

    if file_format == "Email":
        return processEmail(file_path, extracted_text)
    elif file_format == "JSON":
        return processJson(file_path, extracted_text)
    elif file_format == "PDF":
        return processPdf(file_path, extracted_text)
    else:
        print("❌ Unknown format. No agent triggered.")
        return {"status": "skipped", "reason": "Unknown format"}

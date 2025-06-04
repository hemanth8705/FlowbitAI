import random

def classifyInput(text: str) -> dict:
    """
    Randomized classifier agent for file format and business intent.
    """
    text_lower = text.lower()

    # --- Format detection --- 
    formats = ["Email", "PDF", "JSON", "Unknown"]
    file_format = random.choice(formats)

    # --- Intent detection ---
    intents = ["Complaint", "RFQ", "Invoice", "Regulation", "Fraud Risk", "Unknown"]
    intent = random.choice(intents)

        
    # Output the classification randomly chosen
    return {
        "format": file_format,
        "business_intent": intent
    }


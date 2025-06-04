
import random
import re

def detect_urgency(text: str) -> str:
    """
    Randomly select an urgency level based on certain keywords in the text.
    """
    urgency_levels = ["high", "medium", "low"]
    
    # Randomly select an urgency based on the presence of specific words
    if any(word in text.lower() for word in ["urgent", "asap", "immediately", "now", "priority"]):
        return random.choice(urgency_levels)  # Randomly return any urgency level
    else:
        return random.choice(urgency_levels)

def detect_tone(text: str) -> str:
    """
    Randomly select a tone based on certain keywords in the text.
    """
    tones = ["angry", "polite", "threatening", "neutral"]

    # Randomly select a tone from predefined options
    if any(word in text.lower() for word in ["angry", "frustrated", "disappointed", "complain"]):
        return random.choice(tones)  # Randomly return any tone
    elif any(word in text.lower() for word in ["please", "kindly", "appreciate"]):
        return random.choice(tones)
    elif any(word in text.lower() for word in ["legal", "lawsuit", "threat", "sue"]):
        return random.choice(tones)
    
    return random.choice(tones)  # Randomly choose tone if no keywords found

def extract_sender(text: str) -> str:
    """
    Extracts the sender from the text, but returns randomly if the sender is found.
    """
    match = re.search(r"From:\s*(.*)", text)
    if match:
        return random.choice([match.group(1).strip(), "unknown"])  # Randomly choose between found sender or unknown
    return "unknown"

def extract_issue(text: str) -> str:
    """
    Randomly extracts 1-2 lines of the issue from the text.
    """
    lines = text.strip().split("\n")
    return random.choice([lines[:2], lines])  # Randomly choose either first 2 lines or all lines as the issue

def processEmail(file_path: str, extracted_text: str) -> dict:
    """
    Processes the email text and generates a dictionary with details.
    The values are randomized based on keyword matching.
    """
    sender = extract_sender(extracted_text)
    urgency = detect_urgency(extracted_text)
    tone = detect_tone(extracted_text)
    issue = extract_issue(extracted_text)

    # Randomly decide action based on tone and urgency
    actions = ["escalate", "log_and_close"]
    if tone in ["angry", "threatening"] or urgency == "high":
        action = random.choice(actions)
    else:
        action = random.choice(actions)

    return {
        "agent": "email_agent",
        "sender": sender,
        "urgency": urgency,
        "tone": tone,
        "issue_summary": "\n".join(issue),  # Ensuring the issue is properly formatted
        "suggested_action": action
    }


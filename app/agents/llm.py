import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from .env file
load_dotenv()

# Read GROQ_API_KEY from the environment
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the ChatGroq LLM
llm = ChatGroq(model="Gemma2-9b-It", groq_api_key=groq_api_key)

# Main entry point
if __name__ == "__main__":
    print("groq_api_key:", groq_api_key)
    print("llm:", llm)

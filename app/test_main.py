import os
import logging
import logging.config


from processor.fileProcessor import process_file
from agents.ClassifierAgent import classifyInput
from router.AgentRouter import route_to_agent
from core.ActionRouter import RouteAction
from memory.MemoryStore import init_db

lineLen = 60

# Configure logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",  # Use DEBUG for development, INFO or WARNING for production
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(os.getcwd(), "app.log"),
            "formatter": "detailed",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def main():

    logger.info("\n"*5)
    logger.info("=" * 30 + " NEW SECTION " + "=" * 30)
    logger.info("Application starting up...")
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\pdfs\wordpress-pdf-invoice-plugin-sample.pdf"
    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\txt\sample4.txt"
    file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\sampleFiles\txt\sample3.txt"
    if not os.path.exists(file_path):
        print("file_path = " , file_path)
        print("File does not exist. Please check the path.")
        return

    try:
            extractedText = process_file(file_path)

            print("\n📄 Extracted Text:")
            print(extractedText)
            logger.info("Extracted text from file: ")
            logger.info(extractedText) 
            logger.info("_"*30)



            classification = classifyInput(extractedText)

            print("\n📂 File Classification:")
            print(classification)
            logger.info("_"*30)


            agent_result = route_to_agent(file_path, classification, extractedText)

            print("\n🧠 Agent Output:")
            print(agent_result)
            logger.info("_"*30)



            action_response = RouteAction(agent_result)

            print("\n✅ Action Router Response:")
            print(action_response)
            logger.info("_"*30)

            logger.info("Application finished!")
            
    except ValueError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

import os
import logging
import logging.config


from processor.fileProcessor import process_file
from agents.ClassifierAgent import classifyInput
from router.AgentRouter import route_to_agent
from core.ActionRouter import RouteAction
from memory.MemoryStore import init_db, log_trace , get_all_traces


init_db()
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
    logger.info("=" * 30 + " NEW SECTION " + "=" * 30)
    logger.info("Application starting up...")

    file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\pdfs\invoice.pdf"
    file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\txt\sample4.txt"
    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\json\sample1.json"
    if not os.path.exists(file_path):
        print("file_path = " , file_path)
        print("File does not exist. Please check the path.")
        return

    try:
            extractedText = process_file(file_path)

            print("\n📄 Extracted Text:")
            print(extractedText)

            classification = classifyInput(extractedText)

            print("\n📂 File Classification:")
            print(classification)

            agent_result = route_to_agent(file_path, classification, extractedText)

            print("\n🧠 Agent Output:")
            print(agent_result)

            action_response = RouteAction(agent_result)

            print("\n✅ Action Router Response:")
            print(action_response)

            # log_trace(
            #     filename=os.path.basename(file_path),
            #     file_type=agent_result.get("format", "unknown"),
            #     intent=classification.get("intent", "unknown"),
            #     agent="email_agent",  # or json/pdf
            #     extracted_fields=agent_result,
            #     action=action_response.get("action ", "unknown")
            # )


            # print("\n🗃️ All Traces:")
            # traces = get_all_traces()
            # for trace in traces:
            #     print(trace)
            logger.info("Application finished!")
            
    except ValueError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

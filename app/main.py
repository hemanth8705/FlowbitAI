import os
from processor.fileProcessor import process_file
from agents.ClassifierAgent import classifyInput
from router.AgentRouter import route_to_agent
from core.ActionRouter import RouteAction
from memory.MemoryStore import init_db, log_trace , get_all_traces


init_db()

def main():
    file_path = "E:\langflow_directory\gitRepos\AgenticAI\sampleFiles\pdfs\invoice.pdf"
    file_path = r"E:\langflow_directory\gitRepos\AgenticAI\sampleFiles\txt\sample2.txt"
    # file_path = "E:\langflow_directory\gitRepos\AgenticAI\sampleFiles\json\sample1.json"
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

            log_trace(
                filename=os.path.basename(file_path),
                file_type=agent_result.get("format", "unknown"),
                intent=classification.get("intent", "unknown"),
                agent="email_agent",  # or json/pdf
                extracted_fields=agent_result,
                action=action_response.get("action ", "unknown")
            )


            print("\n🗃️ All Traces:")
            traces = get_all_traces()
            for trace in traces:
                print(trace)
            
    except ValueError as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

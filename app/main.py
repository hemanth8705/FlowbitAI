import os
import logging
import logging.config

from processor.fileProcessor import process_file
from agents.ClassifierAgent import classifyInput
from router.AgentRouter import route_to_agent
from core.ActionRouter import RouteAction
from memory.MemoryStore import init_db
import config

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import shutil

import sys
import os
import sqlite3
# Instead of adding the parent directory,
# add the current directory (i.e. the "app" folder) to sys.path.
sys.path.insert(0, os.path.dirname(__file__))
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
logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)

app = FastAPI(title="FlowbitAI Multi-Agent System")

origins = [
    "http://localhost:5173",  # your React front end URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    logger.info("\n"*5)
    logger.info("=" * 30 + " NEW SECTION " + "=" * 30)
    logger.info("Application starting up...")
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")

# Define the path to your SQLite DB (or use your config variable)
DB_PATH = os.getenv("DB_PATH", "memory.db")

@app.get("/history")
async def get_history():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            run_id = config.CURRENT_RUN_ID 
            if not run_id:
                raise HTTPException(status_code=400, detail="No run_id found in config")
            cursor = conn.cursor()
            cursor.execute("SELECT history FROM workflow_run WHERE run_id=?", (run_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Run id not found")
            # The history field is a JSON string
            history = row[0]
            return {"run_id": run_id, "routing_history": history}
    except Exception as e:
        logger.exception("Error fetching history")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_input(file: UploadFile = File(...)):

    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\pdfs\wordpress-pdf-invoice-plugin-sample.pdf"
    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\txt\sample4.txt"
    # file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\json\sample3.json"
    # Save the file to a local sample directory
    upload_dir = os.path.join(os.getcwd(), "sampleFiles")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
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

        # Return a response including the classification and agent output info
        return JSONResponse(
            content={
                "run_id": config.CURRENT_RUN_ID,
                "classification": classification,
                "agent_result": agent_result,
                "action_response": action_response,
                "extracted_text": extractedText
            }
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

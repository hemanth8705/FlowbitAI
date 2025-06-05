import os
import json
import pdfplumber
import pytesseract
from PIL import Image
import logging
from memory.MemoryStore import insert_run
import uuid

run_id = str(uuid.uuid4())   # ensure you import uuid
import config
config.CURRENT_RUN_ID = run_id


# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# --- PDF text extraction and OCR ---
def extract_text_and_tables(pdf_path):
    logger.info(f"Starting extraction from PDF: {pdf_path}")
    all_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.debug(f"PDF opened successfully with {len(pdf.pages)} pages.")
            for i, page in enumerate(pdf.pages):
                logger.debug(f"Processing page {i+1}.")
                page_data = {
                    "page_number": i + 1,
                    "text": page.extract_text() or "",
                    "tables": [],
                    "ocr_text": ""
                }

                # Extract tables and store as list of rows
                tables = page.extract_tables()
                logger.debug(f"Found {len(tables)} table(s) on page {i+1}.")
                for table in tables:
                    cleaned_table = [row for row in table if any(cell is not None for cell in row)]
                    if cleaned_table:
                        page_data["tables"].append(cleaned_table)

                # If no text and tables found, apply OCR
                if not page_data["text"].strip() and not page_data["tables"]:
                    logger.info(f"No text or tables detected on page {i+1}, applying OCR.")
                    img = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(img)
                    page_data["ocr_text"] = ocr_text.strip()
                    
                all_data.append(page_data)
            logger.info("Completed extraction from PDF in Json format.")
            logger.info(">>>"*30)
            logger.debug(f"Extracted data: {json.dumps(all_data, indent=2)}")
            logger.info("<<<"*30)
    except Exception as e:
        logger.error(f"Error during PDF extraction for {pdf_path}", exc_info=True)
        raise e
    return all_data

# --- Convert JSON data into human-readable text ---
def json_to_llm_text(data: dict, indent=0) -> str:
    logger.debug("Converting JSON data into human-readable text for LLM input.")
    output_lines = []
    indent_str = '  ' * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                output_lines.append(f"{indent_str}{key.capitalize()}:")
                output_lines.append(json_to_llm_text(value, indent + 1))
            else:
                output_lines.append(f"{indent_str}{key.capitalize()}: {value}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            output_lines.append(f"{indent_str}- Item {idx + 1}:")
            output_lines.append(json_to_llm_text(item, indent + 1))
    else:
        output_lines.append(f"{indent_str}{data}")

    result = "\n".join(output_lines)
    logger.debug("Conversion completed.")
    return result

# --- File type detection and processing ---
def process_file(file_path):
    logger.info(f"Processing file: {file_path}")
    file_extension = file_path.split('.')[-1].lower()

    insert_run(config.CURRENT_RUN_ID, "upload", file_path, file_extension)
    logger.info("#### Memory Update")
    logger.info(f"insert_run called with run_id: {run_id}, source: 'upload', file_path: {file_path}, original_ext: {file_extension}")

    if file_extension == "txt":
        try:
            logger.info("Detected text file.")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info("Text file processed successfully.")
            return text
        except Exception as e:
            logger.error(f"Error processing text file: {file_path}", exc_info=True)
            raise e

    elif file_extension == "json":
        try:
            logger.info("Detected JSON file.")
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info("JSON file processed successfully.")
            return data
        except Exception as e:
            logger.error(f"Error processing JSON file: {file_path}", exc_info=True)
            raise e

    elif file_extension == "pdf":
        try:
            logger.info("Detected PDF file.")
            extracted_data = extract_text_and_tables(file_path)
            # converted_text = json_to_llm_text(extracted_data)
            logger.info("PDF file processed successfully.")
            return extracted_data
        except Exception as e:
            logger.error(f"Error processing PDF file: {file_path}", exc_info=True)
            raise e

    else:
        logger.error(f"Unsupported file format: {file_extension}")
        raise ValueError("Unsupported file format. Please provide a .txt, .json, or .pdf file.")

# --- Main entry point for testing ---
if __name__ == "__main__":
    file_path = r"E:\langflow_directory\gitRepos\FlowbitAI\app\sampleFiles\pdfs\statement.pdf"  # Change to your test file path
    file_path = os.path.abspath(file_path)  # Ensure absolute path
    logger.info("File Processing started with __name__ = '__main__'")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        exit(1)
    try:
        processed_data = process_file(file_path)
        logger.info("Processed Data:")
        logger.info(processed_data)
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
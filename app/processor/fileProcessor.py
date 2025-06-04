import os
import json
import pdfplumber
import pytesseract
from PIL import Image

# --- PDF text extraction and OCR ---
def extract_text_and_tables(pdf_path):
    all_data = []

    # Use pdfplumber for text + table extraction
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_data = {
                "page_number": i + 1,
                "text": page.extract_text() or "",
                "tables": [],
                "ocr_text": ""
            }

            # Extract tables and store as list of rows
            tables = page.extract_tables()
            for table in tables:
                cleaned_table = [row for row in table if any(cell is not None for cell in row)]
                if cleaned_table:
                    page_data["tables"].append(cleaned_table)

            # If no text and tables found → apply OCR
            if not page_data["text"].strip() and not page_data["tables"]:
                img = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(img)
                page_data["ocr_text"] = ocr_text.strip()

            all_data.append(page_data)

    return all_data

# --- Convert JSON data into human-readable text ---
def json_to_llm_text(data: dict, indent=0) -> str:
    """
    Converts JSON/dictionary into human-readable, structured text
    suitable as an LLM input prompt.
    """
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

    return "\n".join(output_lines)

# --- File type detection and processing ---
def process_file(file_path):
    file_extension = file_path.split('.')[-1].lower()


    if file_extension == "txt":
        # Read and return plain text from a .txt file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text

    elif file_extension == "json":
        # Read and parse JSON data from a .json file
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return json_to_llm_text(data)

    elif file_extension == "pdf":
        # Process the PDF file (extract text, tables, and OCR)
        extracted_data = extract_text_and_tables(file_path)
        return json_to_llm_text(extracted_data)

    else:
        raise ValueError("Unsupported file format. Please provide a .txt, .json, or .pdf file.")

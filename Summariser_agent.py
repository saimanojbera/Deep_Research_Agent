import fitz  # PyMuPDF
import pdfplumber
import re
import os
import json
import shutil
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=gemini_api_key)

# Define folder paths
PDF_FOLDER = "./related_papers"   # Folder containing PDFs
OUTPUT_FOLDER = "./extracted_images"  # Folder for extracted images
SUMMARY_FOLDER = "./structured_summaries"  # Folder for summaries

def refresh_output_folders():
    """Deletes and recreates output folders **only once** before processing the first PDF."""
    for folder in [OUTPUT_FOLDER, SUMMARY_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)  # Delete the entire folder
        os.makedirs(folder)  # Recreate empty folder

def extract_metadata_from_pdf(pdf_path):
    """Extracts title, authors, and DOI from the first page of a PDF."""
    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text("text")

    # Extract Title (First Large Text Line)
    title = first_page_text.split("\n")[0].strip()

    # Extract Authors (Lines after title but before Abstract)
    author_lines = []
    for line in first_page_text.split("\n")[1:]:
        if "abstract" in line.lower():
            break
        author_lines.append(line.strip())

    authors = ", ".join(author_lines)

    # Extract DOI
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", first_page_text, re.I)
    doi = doi_match.group(0) if doi_match else "DOI not found"

    return title, authors, doi

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF."""
    doc = fitz.open(pdf_path)
    return "\n\n".join(page.get_text("text") for page in doc).strip()

def extract_images_from_pdf(pdf_path):
    """Extracts images from a PDF and saves them."""
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_filename = f"{OUTPUT_FOLDER}/{os.path.basename(pdf_path).replace('.pdf', '')}_page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
            with open(image_filename, "wb") as f:
                f.write(image_bytes)
            image_paths.append(image_filename)

    return image_paths

def extract_tables_from_pdf(pdf_path):
    """Extracts tables from a PDF using pdfplumber."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            table = page.extract_table()
            if table:
                tables.append({"page": page_num + 1, "table_data": table})
    return tables

def summarize_with_gemini(text, figures, tables):
    """Summarizes extracted text while referencing figures and tables."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        structured_prompt = f"""
        You are an AI researcher summarizing an academic paper. The extracted text is provided below.
        Include references to figures and tables in the summary where applicable.

        --- Paper Content ---
        {text[:2000]}  # Limit input to avoid API constraints

        --- Figures & Tables ---
        Figures: {len(figures)} extracted
        Tables: {len(tables)} extracted

        Summarize this paper in a structured format:
        1. Introduction
        2. Key Findings
        3. Important Figures & Tables (mention their relevance)
        4. Conclusion
        """

        response = model.generate_content(structured_prompt)
        return response.text if response.text else "Summary not available."
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return "Summary not available due to API error."

def format_summary(title, authors, doi, text_summary, figures, tables):
    """Formats the extracted information into a structured summary JSON."""
    return {
        "title": title,
        "authors": authors,
        "doi": doi,
        "summary": text_summary,
        "figures": [{"image_path": img} for img in figures],
        "tables": [{"page": table["page"], "table_data": table["table_data"]} for table in tables]
    }

def generate_summary_report(pdf_path):
    """Full pipeline: Extract metadata, summarize, and format the research paper content."""
    print(f"📄 Processing: {os.path.basename(pdf_path)}")

    title, authors, doi = extract_metadata_from_pdf(pdf_path)
    extracted_text = extract_text_from_pdf(pdf_path)
    extracted_images = extract_images_from_pdf(pdf_path)
    extracted_tables = extract_tables_from_pdf(pdf_path)
    text_summary = summarize_with_gemini(extracted_text, extracted_images, extracted_tables)

    final_summary = format_summary(title, authors, doi, text_summary, extracted_images, extracted_tables)

    output_filename = os.path.join(SUMMARY_FOLDER, os.path.basename(pdf_path).replace(".pdf", ".json"))
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_summary, f, indent=4, ensure_ascii=False)

    print(f"✅ Summary saved: {output_filename}")

def process_all_pdfs_in_folder(pdf_folder):
    """Iterates through all PDFs in the folder and processes them."""
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

    if not pdf_files:
        print("⚠️ No PDF files found in the folder.")
        return

    # **Refresh folders once before processing the first PDF**
    refresh_output_folders()

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        generate_summary_report(pdf_path)

# Run for all PDFs in the folder
#if __name__ == "__main__":
#   process_all_pdfs_in_folder(PDF_FOLDER)

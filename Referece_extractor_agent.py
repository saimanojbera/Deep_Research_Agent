from crewai import Agent, Task, Crew
import fitz  # PyMuPDF for PDF text extraction
import re
import requests
import time
import json
import os
import concurrent.futures

class ReferenceExtractor:
    """
    Extracts references from research paper PDFs using PyMuPDF and regex,
    then validates them using CrossRef API.
    """
    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """Extracts text from a PDF file."""
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return text

    @staticmethod
    def extract_references_section(text):
        """Finds and extracts only the References section."""
        match = re.search(r'\b(?:References|Bibliography)\b(.+)', text, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else text

    @staticmethod
    def extract_references(text):
        """Extracts references from a structured numbered reference section."""
        reference_pattern = re.compile(r'\d+\.\s+([^\n]+(?:\n(?!\d+\.).*)*)', re.MULTILINE)
        references = reference_pattern.findall(text)
        return [' '.join(ref.splitlines()) for ref in references]

    @staticmethod
    def validate_reference(reference):
      """Validates references using CrossRef API with better error handling."""
      base_url = "https://api.crossref.org/works?query="
      query_url = f"{base_url}{reference}"

      try:
          response = requests.get(query_url, timeout=5)  # Reduce timeout
          if response.status_code == 200:
              data = response.json()
              if "message" in data and "items" in data["message"] and data["message"]["items"]:
                  return data["message"]["items"][0].get("DOI", "No DOI found")
      except requests.exceptions.Timeout:
          return "Not Found (Timeout)"
      except requests.RequestException as e:
          return f"Error: {str(e)}"

      return "Not Found"

    @staticmethod
    def validate_references_parallel(references, max_workers=10):
        """Validates references using multi-threading to speed up processing."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(ReferenceExtractor.validate_reference, references))
        return results

    @staticmethod
    def save_to_json(data, folder="/content/references", filename="references.json"):
        """Saves extracted references to a JSON file in a specific folder."""
        os.makedirs(folder, exist_ok=True)  # Ensure the folder exists
        file_path = os.path.join(folder, filename)
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"References saved to {file_path}")

# Define CrewAI Agents
extractor_agent = Agent(
    role="Reference Extractor",
    goal="Extract references from research papers.",
    backstory="A research assistant specialized in document parsing.",
    allow_delegation=False,
    function=ReferenceExtractor.extract_text_from_pdf
)

parser_agent = Agent(
    role="Reference Parser",
    goal="Identify and extract structured references from the extracted text.",
    backstory="A linguistic expert trained to identify citation formats.",
    allow_delegation=False,
    function=ReferenceExtractor.extract_references
)

validator_agent = Agent(
    role="Reference Validator",
    goal="Validate extracted references against online databases like CrossRef.",
    backstory="A digital librarian verifying the authenticity of research references.",
    allow_delegation=False,
    function=ReferenceExtractor.validate_reference
)

# Define Tasks with `expected_output`
extract_task = Task(
    description="Extract text from a given PDF and retrieve raw references.",
    agent=extractor_agent,
    expected_output="A raw text string extracted from the PDF document."
)

parse_task = Task(
    description="Parse extracted text and identify structured references.",
    agent=parser_agent,
    context=[extract_task],
    expected_output="A list of extracted references in text format."
)

validate_task = Task(
    description="Validate references against CrossRef and fetch metadata.",
    agent=validator_agent,
    context=[parse_task],
    expected_output="A list of validated references with DOI numbers."
)

# Create Crew
reference_extraction_crew = Crew(
    agents=[extractor_agent, parser_agent, validator_agent],
    tasks=[extract_task, parse_task, validate_task]
)

# Function to run Crew for a single PDF
def extract_references_from_pdf(pdf_path, output_folder="/content/references", output_json=True):
    """Runs the CrewAI pipeline to extract and validate references from a PDF and save to JSON in a specific folder."""
    text = ReferenceExtractor.extract_text_from_pdf(pdf_path)
    references_section = ReferenceExtractor.extract_references_section(text)
    references = ReferenceExtractor.extract_references(references_section)
    validated_references = [{"reference": ref, "DOI": ReferenceExtractor.validate_reference(ref)} for ref in references]

    if output_json:
        filename = os.path.splitext(os.path.basename(pdf_path))[0] + "_references.json"
        ReferenceExtractor.save_to_json(validated_references, folder=output_folder, filename=filename)

    return validated_references

# Function to process multiple PDFs in a folder
def process_pdfs_in_folder(folder_path="/content/research_papers", output_folder="/content/references"):
    """Processes all PDFs in a given folder and extracts references from each after refreshing output folder once."""
    if os.path.exists(output_folder):
        for file in os.listdir(output_folder):
            file_path = os.path.join(output_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Output folder {output_folder} cleared.")
    else:
        os.makedirs(output_folder, exist_ok=True)

    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return

    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in the folder.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Processing: {pdf_file}")
        extract_references_from_pdf(pdf_path, output_folder=output_folder)

# Example Usage:
# process_pdfs_in_folder("/content/research_papers", "/content/references")

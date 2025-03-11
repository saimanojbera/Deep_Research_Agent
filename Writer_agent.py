import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("❌ GEMINI_API_KEY is not set in the .env file.")

# Configure API Key
genai.configure(api_key=gemini_api_key)

def generate_literature_review():
    """Generates a literature review using Gemini AI from extracted research summaries."""
    
    # Path to JSON files folder
    json_folder = "./structured_summaries"
    
    if not os.path.exists(json_folder) or not os.listdir(json_folder):
        print("⚠️ No structured summaries found. Skipping literature review.")
        return

    # Load and preprocess JSON files
    all_papers = []
    for file_name in os.listdir(json_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(json_folder, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    all_papers.append(data)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping '{file_name}' due to JSON parsing error.")

    if not all_papers:
        print("⚠️ No valid research papers found in JSON files. Exiting process.")
        return

    # Extract relevant fields
    processed_papers = [
        {
            "title": paper.get("title", "No Title"),
            "authors": paper.get("authors", "Unknown Author"),
            "year": paper.get("year", "Unknown Year"),
            "doi": paper.get("doi", "No DOI"),
            "summary": paper.get("summary", "No summary available."),
        }
        for paper in all_papers[:10]
    ]

    context_data = json.dumps(processed_papers, indent=2)

    # Construct AI prompt
    structured_prompt = f"""
    ### **Research Task: Generate a High-Quality, Multi-Page Literature Review**
    Generate a **3-4 page literature review** based on structured data extracted from research papers.

    --- **Extracted Research Papers:** ---
    {context_data}

    --- **Follow this structure:** ---
    1. **Introduction**
    2. **Key Themes & Findings**
    3. **Research Gaps & Future Directions**
    4. **Conclusion**
    5. **References (formatted citations)**

    Only use the provided data.
    """

    # Generate response using Gemini API
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(structured_prompt)

        # Save output
        output_file = "generated_literature_review.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(response.text)

        print(f"✅ Literature review saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error generating literature review: {e}")

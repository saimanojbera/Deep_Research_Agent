import streamlit as st
from crewai import Agent, Task, Crew
import requests
import json
import os
import shutil
import re
from dotenv import load_dotenv
from copy_files import copy_files
from Referece_extractor_agent import process_pdfs_in_folder
from Paper_downloader_Agent import download_papers_from_dois
from Summariser_agent import process_all_pdfs_in_folder
import Writer_agent

# Load API key from .env file
load_dotenv()
SERPERDEV_API_KEY = os.getenv('SERPERDEV_API_KEY')
if not SERPERDEV_API_KEY:
    st.error("Please set the SERPERDEV_API_KEY in the .env file.")
    st.stop()

pdf_folder = "selected_papers"
if os.path.exists(pdf_folder):
    shutil.rmtree(pdf_folder)
os.makedirs(pdf_folder, exist_ok=True)

# Folder to save Total collected Papers
target_folder = "./Collected_Papers"
if os.path.exists(target_folder):
    shutil.rmtree(target_folder)  # Refresh folder on every run
os.makedirs(target_folder, exist_ok=True)

# Function to sanitize filenames
def sanitize_filename(filename):
    filename = filename.replace(" “", "").replace("”", "").replace("‘", "").replace("’", "")  # Normalize quotes
    filename = re.sub(r'[^a-zA-Z0-9_. -]', '', filename)  # Remove invalid characters
    return filename[:150]  # Limit filename length

# Define functions

def search_papers(query):
    url = "https://google.serper.dev/scholar"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': SERPERDEV_API_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("organic", [])[:10]  # Limit to top 10 results

def select_papers(search_results):
    selected_papers = []
    st.subheader("Select papers to download:")
    checkboxes = {}
    
    for i, paper in enumerate(search_results):
        details = f"**{paper['title']}**\n\n"
        details += f"📅 Year: {paper.get('year', 'Unknown Year')}  |  🔗 [Source Link]({paper.get('link', '#')})\n\n"
        details += f"📄 PDF: {'[Download](' + paper['pdfUrl'] + ')' if paper.get('pdfUrl') else 'Not Available'}\n"
        checkboxes[i] = st.checkbox(details, key=f"paper_{i}")
    
    for index, checked in checkboxes.items():
        if checked:
            selected_papers.append(search_results[index])
    
    return selected_papers

def download_pdf(selected_papers):
    failed_downloads = []
    for paper in selected_papers:
        pdf_url = paper.get("pdfUrl")
        if pdf_url:
            title_cleaned = sanitize_filename(paper["title"]).replace(" ", "_").replace("/", "-")
            filename = os.path.join(pdf_folder, f"{title_cleaned}.pdf")
            try:
                response = requests.head(pdf_url, allow_redirects=True, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type or pdf_url.endswith('.pdf'):
                    response = requests.get(pdf_url, stream=True, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                    response.raise_for_status()
                    with open(filename, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                    st.success(f"✅ Downloaded: {filename}")
                else:
                    raise ValueError("Not a direct PDF link")
            except (requests.exceptions.RequestException, ValueError) as e:
                st.error(f"❌ Failed to download {filename}: {e}")
                failed_downloads.append(pdf_url)
    return failed_downloads

# Define Agents without LLM dependencies
search_agent = Agent(
    name="Search Agent",
    role="Researcher",
    goal="Finds relevant academic papers from Google Scholar.",
    backstory="An expert in academic research, dedicated to discovering valuable sources."
)

selection_agent = Agent(
    name="Selection Agent",
    role="Evaluator",
    goal="Helps users manually select the most relevant papers.",
    backstory="A meticulous reviewer who ensures only the best papers are chosen."
)

download_agent = Agent(
    name="Download Agent",
    role="Downloader",
    goal="Ensures selected papers are downloaded and organized properly.",
    backstory="A diligent archivist focused on preserving academic papers."
)

# Streamlit UI
st.title("Deep Research Agentic Bot")
query = st.text_input("Enter your research topic:")
if st.button("Search"):
    search_results = search_papers(query)
    if search_results:
        st.session_state["search_results"] = search_results
        st.success("Search completed! Select papers below.")
    else:
        st.error("No results found.")

if "search_results" in st.session_state:
    selected_papers = select_papers(st.session_state["search_results"])
    if st.button("Download Selected Papers"):
        failed_downloads = download_pdf(selected_papers)
        if failed_downloads:
            #st.warning("❌ Some PDFs could not be downloaded:")
            for url in failed_downloads:
                st.write(f"🔗 {url}")
        st.success("📂 All available PDFs have been downloaded.")
        
        # Copy Selected intial papers to Collected_Papers
        copy_files("./selected_papers", "./Collected_Papers")
        st.success("📂 Intially Selected Papers successfully moved to Collected_Papers(root) folder.")

        #if no files in selected_papers folder then the next steps will not be executed
        if os.listdir("./selected_papers") == []:
            st.error("❌ No PDFs found in the selected_papers folder. Please select papers and try again or the papers you have selected are behind the pay wall.")
        else:
        
            # Level 1: Calling Reference Extractor
            process_pdfs_in_folder("./selected_papers", "./references_json")
            st.success("📄 Level 1: References extracted and saved in references_json folder.")
            
            # Level 1: Calling to download all the PDFs
            download_papers_from_dois("./references_json", "./downloaded_papers")
            st.success("📄 Level 1: Papers downloaded using extracted DOIs and saved in downloaded_papers folder.")

            # Level 1: Copy downloaded papers to Collected_Papers
            copy_files("./downloaded_papers", "./Collected_Papers")
            st.success("📂 Level 1: Extracted Papers successfully moved to Collected_Papers(root) folder.")

            # Level 2: Calling Reference Extractor
            process_pdfs_in_folder("./downloaded_papers", "./references_json")
            st.success("📄 Level 2: References extracted and saved in references_json folder.")
            
            # Level 2: Calling to download all the PDFs
            download_papers_from_dois("./references_json", "./downloaded_papers")
            st.success("📄 Level 2: Papers downloaded using extracted DOIs and saved in downloaded_papers folder.")

            # Level 2: Copy downloaded papers to Collected_Papers
            copy_files("./downloaded_papers", "./Collected_Papers")
            st.success("📂 Level 2: Extracted Papers successfully moved to Collected_Papers(root) folder.")

            # Level 3: Calling Reference Extractor
            process_pdfs_in_folder("./downloaded_papers", "./references_json")
            st.success("📄 Level 3: References extracted and saved in references_json folder.")
            
            # Level 3: Calling to download all the PDFs
            download_papers_from_dois("./references_json", "./downloaded_papers")
            st.success("📄 Level 3: Papers downloaded using extracted DOIs and saved in downloaded_papers folder.")

            # Level 3: Copy downloaded papers to Collected_Papers
            copy_files("./downloaded_papers", "./Collected_Papers")
            st.success("📂 Level 3: Extracted Papers successfully moved to Collected_Papers(root) folder.")

            # Summarize all the papers
            process_all_pdfs_in_folder("./Collected_Papers")
            st.success("📄 Papers summarized and saved in summary folder.")

            # Generate Literature Review
            Writer_agent.generate_literature_review()
            st.success("📄 Literature review generated and saved in the root folder.")

            # Display the generated literature review in Streamlit
            output_file = "generated_literature_review.txt"
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as file:
                    literature_review_content = file.read()
                
                st.subheader("📜 Generated Literature Review")
                st.markdown(literature_review_content, unsafe_allow_html=True)  # Display formatted text
            else:
                st.error("❌ Literature review file not found. Please check the generation process.")

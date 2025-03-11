from crewai import Agent, Task, Crew
import requests
import json
import os
import shutil
from google.colab import userdata

# Load API key
SERPERDEV_API_KEY = userdata.get('SERPER_DEV')
if not SERPERDEV_API_KEY:
    raise Exception("Please set the SERPERDEV_API_KEY environment variable in your Google Colab environment.")

pdf_folder = "/content/drive/MyDrive/Deep-Research-Agentic-Bot/selected_papers"
if os.path.exists(pdf_folder):
    shutil.rmtree(pdf_folder)
os.makedirs(pdf_folder, exist_ok=True)

# Define functions

def search_papers(query):
    url = "https://google.serper.dev/scholar"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': SERPERDEV_API_KEY, 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("organic", [])[:10]  # Limit to top 10 results

def select_papers(search_results):
    selected_papers = []
    print("\nTop 10 search results:")
    for i, result in enumerate(search_results, 1):
        title = result.get("title", "No Title")
        year = result.get("year", "Unknown Year")
        cited_by = result.get("citedBy", "Unknown Citations")
        link = result.get("link", "No Link")
        pdf_url = result.get("pdfUrl", "No PDF Available")

        print(f"{i}. {title} ({year})")
        print(f"   Cited by: {cited_by}")
        print(f"   Link: {link}")
        print(f"   PDF: {pdf_url}\n")
    
    choices = input("Enter the numbers of the papers you want to select (comma-separated): ")
    selected_indices = [int(x.strip()) - 1 for x in choices.split(",") if x.strip().isdigit()]
    for index in selected_indices:
        if 0 <= index < len(search_results):
            selected_papers.append(search_results[index])
    return selected_papers

def download_pdf(selected_papers):
    failed_downloads = []
    for paper in selected_papers:
        pdf_url = paper.get("pdfUrl")
        if pdf_url:
            title_cleaned = paper["title"].replace(" ", "_").replace("/", "-")
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
                    print(f"✅ Downloaded: {filename}")
                else:
                    raise ValueError("Not a direct PDF link")
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"❌ Failed to download {filename}: {e}")
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

# Create the Crew
crew = Crew(
    agents=[search_agent, selection_agent, download_agent]
)

# Manually execute tasks instead of `crew.kickoff()`
query = input("Enter your research topic: ")
search_results = search_papers(query)
selected_papers = select_papers(search_results)
failed_downloads = download_pdf(selected_papers)

# Log failed downloads
if failed_downloads:
    print("\n❌ The following PDFs could not be downloaded:")
    for url in failed_downloads:
        print(f"🔗 {url}")

print("\n📂 All available PDFs have been downloaded.")
print(f"📁 PDFs are saved in the folder: {pdf_folder}")
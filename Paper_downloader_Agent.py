from crewai import Agent, Task, Crew
import json
import os
import requests
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PaperDownloader:
    """
    Extracts DOIs from JSON files, searches open-access repositories,
    and downloads papers. Falls back to Sci-Hub if needed.
    """

    @staticmethod
    def clean_doi(doi):
        """Cleans DOI by removing invalid characters or extra parts (e.g., table references)."""
        return doi.split("/table")[0].strip()

    @staticmethod
    def read_dois_from_json(folder_path):
        """Reads all JSON files in a folder and extracts valid DOIs."""
        dois = []
        for file in os.listdir(folder_path):
            if file.endswith(".json"):
                file_path = os.path.join(folder_path, file)
                with open(file_path, "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    for entry in data:
                        doi = entry.get("DOI")
                        if doi and doi.lower() not in ["no doi found", "not found"]:
                            cleaned_doi = PaperDownloader.clean_doi(doi)
                            dois.append(cleaned_doi)
        return dois

    @staticmethod
    def search_open_access(doi):
        """Searches for a paper in open-access repositories (Semantic Scholar, OpenAlex, arXiv)."""
        sources = [
            f"https://api.semanticscholar.org/v1/paper/{doi}",
            f"https://api.openalex.org/works/https://doi.org/{doi}",
        ]

        # Special handling for arXiv
        if "10.48550" in doi or "arxiv" in doi.lower():
            arxiv_id = doi.split("/")[-1]  # Extract arXiv ID
            sources.append(f"https://export.arxiv.org/api/query?id_list={arxiv_id}")

        for url in sources:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"Warning: Failed request ({response.status_code}) for {url}")
                    continue

                # Handle JSON-based sources (Semantic Scholar & OpenAlex)
                if "semanticscholar.org" in url or "openalex.org" in url:
                    try:
                        data = response.json()
                        pdf_url = data.get("pdf_url") or data.get("open_access_pdf")
                        if pdf_url:
                            return pdf_url  # Return first found PDF URL
                    except json.JSONDecodeError:
                        print(f"Error: Could not parse JSON from {url}. Skipping.")

                # Handle arXiv (which returns XML)
                elif "arxiv.org" in url:
                    root = ET.fromstring(response.text)
                    pdf_links = [entry.find("link[@title='pdf']") for entry in root.findall("entry")]
                    pdf_urls = [link.attrib["href"] for link in pdf_links if link is not None]

                    if pdf_urls:
                        return pdf_urls[0]

            except requests.exceptions.RequestException as e:
                print(f"Error contacting {url}: {e}")

        return None  # No PDF found

    @staticmethod
    def download_paper(doi, pdf_url, output_folder):
        """Downloads a paper from a given URL."""
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, f"{doi.replace('/', '_')}.pdf")

        # Avoid duplicate downloads
        if os.path.exists(file_path):
            print(f"File already exists, skipping: {file_path}")
            return True

        try:
            response = requests.get(pdf_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(file_path, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=1024):
                        pdf_file.write(chunk)
                print(f"Downloaded: {file_path}")
                return True
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {doi} from {pdf_url}: {e}")

        return False

    @staticmethod
    def fallback_to_scihub(doi, output_folder):
        """Attempts to download a paper from Sci-Hub if other sources fail."""
        sci_hub_url = f"https://sci-hub.se/{doi}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        file_path = os.path.join(output_folder, f"{doi.replace('/', '_')}_scihub.pdf")

        # Avoid duplicate downloads
        if os.path.exists(file_path):
            print(f"File already exists, skipping Sci-Hub download: {file_path}")
            return True

        try:
            response = requests.get(sci_hub_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            embed_tag = soup.find("embed") or soup.find("iframe")

            if embed_tag and embed_tag.has_attr("src"):
                pdf_url = embed_tag["src"]
                if pdf_url.startswith("//"):
                    pdf_url = "https:" + pdf_url
                full_pdf_url = urljoin(sci_hub_url, pdf_url)

                pdf_response = requests.get(full_pdf_url, headers=headers, timeout=10)
                if pdf_response.status_code == 200:
                    with open(file_path, "wb") as pdf_file:
                        pdf_file.write(pdf_response.content)
                    print(f"Downloaded via Sci-Hub: {file_path}")
                    return True
                else:
                    print(f"Failed to download PDF for DOI {doi}")
            else:
                print(f"PDF not found for DOI {doi}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {doi} from Sci-Hub: {e}")

        return False

# Function to run Crew
def download_papers_from_dois(references_folder="/content/references", output_folder="/content/downloaded_papers"):
    """Runs the CrewAI pipeline to extract DOIs, search open-access papers, and download them."""

    # Refresh output folder before starting
    if os.path.exists(output_folder):
        for file in os.listdir(output_folder):
            file_path = os.path.join(output_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Output folder {output_folder} cleared.")
    else:
        os.makedirs(output_folder, exist_ok=True)

    dois = PaperDownloader.read_dois_from_json(references_folder)

    for doi in dois:
        pdf_url = PaperDownloader.search_open_access(doi)
        if pdf_url:
            success = PaperDownloader.download_paper(doi, pdf_url, output_folder)
            if not success:
                PaperDownloader.fallback_to_scihub(doi, output_folder)
        else:
            PaperDownloader.fallback_to_scihub(doi, output_folder)

# Example Usage:
# download_papers_from_dois("/content/references", "/content/downloaded_papers")

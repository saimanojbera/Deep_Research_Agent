### **Deep Research Agentic Bot - Project Overview**  

The **Deep Research Agentic Bot** is an AI-powered research assistant designed to **automate academic research** by searching for papers, extracting references, analyzing citations, summarizing content, and generating structured literature reviews.  

---

## **🔹 Project Purpose**
The project aims to **reduce the manual effort** in research by:
1. **Finding relevant papers** on a given topic from Google Scholar.
2. **Extracting and analyzing references** to identify key citations.
3. **Downloading open-access papers** automatically using DOIs.
4. **Summarizing research papers** using AI (Google Gemini).
5. **Building a knowledge graph** to represent relationships between papers.
6. **Generating a structured literature review** with AI assistance.

---

## **🔹 Key Components**
The system consists of multiple agents, each responsible for a specific research task:

### **1️⃣ Search & Selection Agent**
- Queries **Google Scholar** for relevant papers.
- Displays a **selection interface** for users to choose papers.

### **2️⃣ Paper Downloader Agent**
- Extracts **DOIs** from selected papers.
- Searches for full-text PDFs in **Semantic Scholar, OpenAlex, and arXiv**.
- Falls back to **Sci-Hub** if needed.

### **3️⃣ Reference Extractor Agent**
- Reads **references** from research papers.
- Uses **CrossRef API** to validate citations and retrieve more DOIs.

### **4️⃣ Knowledge Graph Builder**
- Uses **Natural Language Processing (NLP)** to extract **key topics** from papers.
- Constructs a **graph** of related research using **network analysis**.

### **5️⃣ Summarization Agent**
- Extracts **key findings, figures, and tables** from papers.
- Uses **Google Gemini AI** to summarize research papers in a structured format.

### **6️⃣ Literature Review Generator**
- Compiles research insights into a **formatted literature review**.
- Identifies **key themes, gaps, and conclusions**.

---

## **🔹 How It Works**
1. **User inputs a research topic** (e.g., "AI in Healthcare").
2. **System fetches relevant papers** from Google Scholar.
3. **User selects papers**, and PDFs are automatically downloaded.
4. **References are extracted**, and additional cited papers are retrieved.
5. **A knowledge graph is built**, connecting related papers.
6. **Summaries are generated** for all collected papers.
7. **A literature review is compiled** and formatted for use in research.

---

## **🔹 Why This Project is Useful**
✅ **Saves time** by automating the tedious research process.  
✅ **Expands knowledge** by recursively finding cited papers.  
✅ **Enhances understanding** through structured AI-generated summaries.  
✅ **Helps researchers & students** by auto-generating literature reviews.  

This tool is especially useful for **researchers, students, and professionals** who need to quickly explore academic topics and generate reports efficiently. 🚀

## **📌 Features**
- **Search & Select Papers** 📚: Finds relevant academic papers from Google Scholar.  
- **Multi-Level Reference Mining** 🔍: Extracts references from papers and recursively downloads cited works.  
- **Paper Download Automation** 📄: Retrieves open-access PDFs from multiple sources (Semantic Scholar, OpenAlex, arXiv, Sci-Hub fallback).  
- **Knowledge Graph Creation** 🧠: Builds a graph of related research papers based on keyword similarity.  
- **AI-Powered Summarization** 🤖: Uses **Google Gemini AI** to generate structured summaries of research papers.  
- **Automated Literature Review** 📑: Generates a formatted literature review from extracted research papers.  
- **Streamlit UI** 🎛️: Provides an intuitive web-based interface for easy interaction.  

---

## **🛠️ Tech Stack**
- **Backend**: Python  
- **Frontend**: Streamlit  
- **AI Models**: Google Gemini, SentenceTransformers  
- **Data Extraction**: PyMuPDF, pdfplumber  
- **Knowledge Graph**: NetworkX  
- **API Integration**: Semantic Scholar, OpenAlex, CrossRef  
- **Cloud Deployment**: GCP Cloud Run (or other options)  

---

## **🚀 Setup & Installation**
### **🔹 1. Clone the Repository**
```bash
git clone https://github.com/saimanojbera/Deep_Research_Agent.git
cd deep-research-bot
```

### **🔹 2. Create a Virtual Environment (Optional)**
```bash
python -m venv venv
source venv/bin/activate   # For macOS/Linux
venv\Scripts\activate      # For Windows
```

### **🔹 3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **🔹 4. Set Up API Keys**
Create a `.env` file and add the required API keys:
```plaintext
SERPERDEV_API_KEY=your_serper_api_key
GEMINI_API_KEY=your_gemini_api_key
```

---

## **🖥️ Running the Application Locally**
```bash
streamlit run app.py
```
- Open **http://localhost:8501/** in your browser.

---

## **📂 Project Structure**
```
📦 deep-research-bot
├── 📜 app.py                      # Main Streamlit app
├── 📜 copy_files.py                # Handles file movement
├── 📜 Knowledge_Graph.py           # Creates research knowledge graph
├── 📜 Paper_downloader_Agent.py    # Downloads papers using DOIs
├── 📜 Referece_extractor_agent.py   # Extracts references from papers
├── 📜 Summariser_agent.py          # AI-based summarization
├── 📜 Writer_agent.py              # Generates literature review
├── 📂 Collected_Papers/            # Stores all downloaded papers
├── 📂 references_json/             # Extracted references in JSON format
├── 📂 structured_summaries/        # AI-generated summaries
├── 📜 requirements.txt             # Python dependencies
├── 📜 Dockerfile                   # Deployment container config
├── 📜 README.md                    # This file
```
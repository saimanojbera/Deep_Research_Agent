import os
import fitz  # PyMuPDF
import networkx as nx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer, util
import shutil
from collections import Counter

# Download necessary NLTK resources
nltk.download("punkt")
nltk.download("stopwords")

class KnowledgeGraph:
    def __init__(self, pdf_folder, related_papers_folder):
        self.pdf_folder = pdf_folder
        self.related_papers_folder = related_papers_folder
        os.makedirs(self.related_papers_folder, exist_ok=True)  # Ensure folder exists

        # Initialize model and knowledge graph
        self.bert_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.kg = nx.Graph()
        self.papers = {}

    def extract_text_from_pdf(self, pdf_path, char_limit=4000):
        """Extracts text from a PDF with an optional character limit."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text("text")
                if len(text) >= char_limit:
                    break
            return text[:char_limit] if text else None
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return None

    def extract_keywords(self, text, top_n=10):
        """Extracts important keywords from the given text."""
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words("english"))
        keywords = [word for word in words if word.isalnum() and word not in stop_words]

        # Use frequency-based filtering
        freq_dist = Counter(keywords)
        return [word for word, _ in freq_dist.most_common(top_n)]

    def build_graph(self):
        """Builds a knowledge graph from PDFs in the specified folder."""
        for filename in os.listdir(self.pdf_folder):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(self.pdf_folder, filename)
                text = self.extract_text_from_pdf(pdf_path)

                if text:  # Only process if text is extracted
                    keywords = self.extract_keywords(text)
                    embedding = self.bert_model.encode(text, convert_to_tensor=True)

                    # Add paper node
                    self.kg.add_node(filename, type="paper", keywords=keywords)
                    self.papers[filename] = {"text": text, "embedding": embedding, "path": pdf_path}

                    # Add keyword nodes with frequency info
                    for kw in keywords:
                        if not self.kg.has_node(kw):
                            self.kg.add_node(kw, type="keyword", frequency=1)
                        else:
                            self.kg.nodes[kw]["frequency"] += 1
                        self.kg.add_edge(filename, kw)

        print(f"Knowledge graph built with {len(self.papers)} papers.")

    def query_papers(self, query, top_k=5):
        """Finds top-k related papers based on the query and saves them."""
        query_embedding = self.bert_model.encode(query, convert_to_tensor=True)
        similarities = []

        for paper, data in self.papers.items():
            score = util.pytorch_cos_sim(query_embedding, data["embedding"]).item()
            similarities.append((paper, score, data["path"]))

        # Sort papers by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Save top-k related papers in the related_papers folder
        for paper, _, path in similarities[:top_k]:
            shutil.copy(path, os.path.join(self.related_papers_folder, paper))

        return similarities[:top_k]

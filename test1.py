from test import KnowledgeGraph

# Define folders
PDF_FOLDER = "./Collected_Papers"
RELATED_PAPERS_FOLDER = "./related_papers"

# Initialize and build the knowledge graph
kg = KnowledgeGraph(PDF_FOLDER, RELATED_PAPERS_FOLDER)
kg.build_graph()

# Query the knowledge graph
query_text = input("Enter your research query:")
related_papers = kg.query_papers(query_text, top_k=5)

# Print results
print("Top related papers:")
for paper, score, _ in related_papers:
    print(f"{paper} - Similarity Score: {score:.4f}")

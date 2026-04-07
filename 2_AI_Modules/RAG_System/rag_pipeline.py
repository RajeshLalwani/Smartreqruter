import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class LocalRAGPipeline:
    """
    Lightning-fast, dependency-light RAG pipeline using TF-IDF.
    Reads all text files from the knowledge_base directory to act as the 'Brain'.
    """
    def __init__(self, kb_dir=None):
        if kb_dir is None:
            # Default to the same directory as this script > knowledge_base
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.kb_dir = os.path.join(base_dir, "knowledge_base")
        else:
            self.kb_dir = kb_dir

        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.vectors = None
        self._load_and_index()

    def _load_and_index(self):
        """Reads all txt files in the knowledge base and chunks them."""
        if not os.path.exists(self.kb_dir):
            os.makedirs(self.kb_dir, exist_ok=True)
            print(f"[RAG] Warning: Created empty knowledge base at {self.kb_dir}")
            return

        raw_text = ""
        for filename in os.listdir(self.kb_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.kb_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_text += f.read() + "\n\n"

        if not raw_text.strip():
            print("[RAG] Knowledge base is empty.")
            return

        # Simple chunking by paragraph
        paragraphs = [p.strip() for p in raw_text.split('\n\n') if len(p.strip()) > 50]
        self.chunks = paragraphs

        if self.chunks:
            self.vectors = self.encoder.encode(self.chunks)
            print(f"[RAG] Indexed {len(self.chunks)} knowledge chunks with Dense Vectors.")

    def query_knowledge(self, question, top_k=2):
        """Retrieves the most contextually relevant chunks for a given question."""
        if self.vectors is None or not self.chunks:
            return ""

        query_vec = self.encoder.encode([question])
        similarities = cosine_similarity(query_vec, self.vectors).flatten()
        
        # Get indices of top_k highest similarities
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Filter out low confidence matches
        relevant_chunks = [self.chunks[i] for i in top_indices if similarities[i] > 0.05]
        
        return "\n".join(relevant_chunks)

class CandidateRAGPipeline:
    """
    Dynamic RAG pipeline for searching candidates' resumes via natural language.
    Does not rely on static files, but instead ingests a dictionary of {candidate_id: resume_text}.
    """
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.candidate_ids = []
        self.documents = [] 
        self.vectors = None

    def load_candidates(self, candidates_dict):
        """
        Ingests the candidate data.
        candidates_dict: dict of {candidate_id: resume_text}
        """
        # Filter out empty resumes
        valid_candidates = {k: v for k, v in candidates_dict.items() if v and isinstance(v, str) and len(v.strip()) > 10}
        
        self.candidate_ids = list(valid_candidates.keys())
        self.documents = list(valid_candidates.values())
        
        if self.documents:
            self.vectors = self.encoder.encode(self.documents)
            print(f"[RAG] Indexed {len(self.documents)} candidate resumes with Dense Vectors.")
        else:
            self.vectors = None

    def search_candidates(self, query, top_k=10, threshold=0.15):
        """
        Searches the resumes and returns matching candidate IDs and scores.
        Threshold adjusted for dense vector cosine similarities.
        """
        if self.vectors is None or not self.documents:
            return []

        query_vec = self.encoder.encode([query])
        similarities = cosine_similarity(query_vec, self.vectors).flatten()
        
        # Sort indices by highest similarity
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for i in top_indices:
            if similarities[i] >= threshold:
                results.append({
                    "candidate_id": self.candidate_ids[i],
                    "score": float(similarities[i])
                })
        
        return results

if __name__ == "__main__":
    # Test the pipeline
    rag = LocalRAGPipeline()
    context = rag.query_knowledge("What is the company policy on remote work?")
    print("Retrieved Context:", context)

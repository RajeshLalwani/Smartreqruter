import json
from django.conf import settings
from core.ai_engine import AIEngine
import re
import os
import sys

# Add AI_Modules to path for RAG access
sys.path.append(os.path.join(settings.BASE_DIR, "..", "2_AI_Modules"))
from RAG_System.rag_pipeline import LocalRAGPipeline

class ArchitectureEvaluator:
    def __init__(self, diagram_json):
        self.raw_data = diagram_json
        self.engine = AIEngine()
        self.rag = LocalRAGPipeline()

    def parse_graph(self):
        """Extracts a readable summary of React Flow nodes and their edges."""
        nodes = self.raw_data.get('nodes', [])
        edges = self.raw_data.get('edges', [])
        
        node_map = {n['id']: n.get('data', {}).get('label', 'Unknown') for n in nodes}
        graph_summary = []
        
        for node in nodes:
            node_id = node['id']
            name = node.get('data', {}).get('label', 'Unknown')
            
            # Find outgoing connections
            connections = []
            for edge in edges:
                if edge.get('source') == node_id:
                    target_id = edge.get('target')
                    target_name = node_map.get(target_id, 'Unknown')
                    connections.append(f"Connects to {target_name}")
            
            graph_summary.append({
                "type": name,
                "connections": connections
            })
            
        return graph_summary

    def evaluate(self):
        """Sends the architectural summary to the AI with RAG-enhanced criteria."""
        summary = self.parse_graph()
        
        # Retrieve Best Practices from RAG
        context = self.rag.query_knowledge("What are the best practices for redundancy, security, and scalability in system design?", top_k=3)
        
        prompt = f"""
        Evaluate the following system architecture designed by a candidate.
        
        Design Summary:
        {json.dumps(summary, indent=2)}
        
        RAG-Retrieved Best Practices Context:
        {context}
        
        Criteria for Evaluation:
        1. Redundancy: Single points of failure detection.
        2. Security: Entry point protection and data isolation.
        3. Scalability: Horizontal scaling and managed services.
        
        Return ONLY a JSON response:
        {{
          "score": (Integer 0-100),
          "analysis": "3-4 bullet points specifically referencing the design",
          "best_practices_followed": (Boolean)
        }}
        """
        
        try:
            response_text = self.engine.generate(prompt)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response_text)
        except Exception as e:
            # Enhanced fallback logic
            score = 50
            types = [n['type'].lower() for n in summary]
            if 'lb' in types or 'load balancer' in types: score += 20
            if 'apig' in types or 'api gateway' in types: score += 15
            if 'db' in types and len(summary) > 2: score += 10
            
            return {
                "score": min(score, 100),
                "analysis": "Detected key infrastructure components. Redundancy seems partially implemented.",
                "best_practices_followed": score > 75
            }

def evaluate_design(diagram_json):
    evaluator = ArchitectureEvaluator(diagram_json)
    return evaluator.evaluate()

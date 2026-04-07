import json
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Candidate, CandidateEmbedding
from .views_advanced import _recruiter_required
from .skill_graph_service import get_expanded_concepts

try:
    from google import genai
    from django.conf import settings
    _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception:
    _genai_client = None

def _get_embedding(text):
    """Utility to fetch embeddings from Gemini (text-embedding-004)."""
    if not _genai_client:
        return [0.0] * 768
    try:
        # If text is too short, pad it
        if not text or len(text) < 2: text = "candidate profile empty info"
        
        result = _genai_client.models.embed_content(
            model="text-embedding-004",
            contents=text[:8000], # New limit is higher
            config={'task_type': 'RETRIEVAL_DOCUMENT'}
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding failed: {e}")
        return [0.0] * 768

@login_required
def semantic_hunter(request):
    """Advanced AI Search that matches 'Concepts' between Query and Candidates using Vector Similarity."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # 🕸️ KNOWLEDGE GRAPH EXPANSION
        expanded_query = get_expanded_concepts(query)
        
        # 1. Embed the expanded query
        query_vec = np.array(_get_embedding(expanded_query))
        
        # 2. Vector space search over candidate database
        embeddings = CandidateEmbedding.objects.all().select_related('candidate')
        
        candidates_to_score = []
        for emb in embeddings:
            try:
                vec = np.array(json.loads(emb.vector_json))
                # 3. Vector Similarity (Cosine)
                similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
                if similarity > 0.4: # Only show relevant-ish matches
                    candidates_to_score.append({
                        'candidate': emb.candidate,
                        'score': round(float(similarity) * 100, 2)
                    })
            except: continue
            
        # 4. Rank by conceptual relevance
        results = sorted(candidates_to_score, key=lambda x: x['score'], reverse=True)[:15]

    return render(request, 'jobs/semantic_hunter.html', {
        'results': results,
        'query': query,
        'has_vectors': CandidateEmbedding.objects.exists()
    })

@login_required
def rebuild_vector_index(request):
    """Enterprise-level re-indexing of the entire talent pool."""
    if not _recruiter_required(request): return redirect('dashboard')
    
    # We clear and rebuild to ensure vector alignment
    candidates = Candidate.objects.all()
    count = 0
    for cand in candidates:
        # Synthesize a 'Knowledge Node' for this candidate
        knowledge_text = f"""
        Name: {cand.full_name}
        Skills: {cand.technical_skills}
        Experience: {cand.experience_summary}
        Education: {cand.education}
        """
        vector = _get_embedding(knowledge_text)
        
        CandidateEmbedding.objects.update_or_create(
            candidate=cand,
            defaults={'vector_json': json.dumps(vector)}
        )
        count += 1
        
    return render(request, 'jobs/vector_index_status.html', {'count': count})
@login_required
def talent_galaxy(request):
    """Entry point for the 3D Talent Universe."""
    if not _recruiter_required(request): return redirect('dashboard')
    
    count = Candidate.objects.count()
    return render(request, 'jobs/talent_galaxy.html', {
        'candidate_count': count
    })

@login_required
def talent_galaxy_api(request):
    """Returns 3D coordinates for the entire talent pool using vector projection."""
    if not _recruiter_required(request):
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    embeddings = CandidateEmbedding.objects.all().select_related('candidate')
    nodes = []
    
    for emb in embeddings:
        try:
            # Deterministic projection from high-dim (768) to 3D
            # We use specific indices to ensure a stable 'Galaxy' shape
            vec = json.loads(emb.vector_json)
            
            # Use three different spans of the vector to determine X, Y, Z
            # Apply a spiral transformation for aesthetic 'Galaxy' look
            raw_x = sum(vec[0:256]) * 10 
            raw_y = sum(vec[256:512]) * 5
            raw_z = sum(vec[512:768]) * 10
            
            # Map to spiral (Aesthetic projection)
            dist = np.sqrt(raw_x**2 + raw_z**2)
            angle = np.arctan2(raw_z, raw_x) + (dist * 0.01) # Add slight twist
            
            x = np.cos(angle) * dist
            y = raw_y
            z = np.sin(angle) * dist

            nodes.append({
                'id': emb.candidate.id,
                'name': emb.candidate.full_name,
                'role': getattr(emb.candidate, 'current_role', 'Specialist'),
                'x': float(x),
                'y': float(y),
                'z': float(z),
                'score': 100 # Default for galaxy view
            })
        except: continue
        
    from django.http import JsonResponse
    return JsonResponse({'nodes': nodes})

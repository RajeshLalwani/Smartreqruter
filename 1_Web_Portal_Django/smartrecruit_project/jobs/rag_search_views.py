import json
import os
import sys
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Application

# Import CandidateRAGPipeline
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    ai_modules_dir = os.path.join(parent_dir, '2_AI_Modules')
    sys.path.append(ai_modules_dir)
    from RAG_System.rag_pipeline import CandidateRAGPipeline
except ImportError as e:
    CandidateRAGPipeline = None
    print(f"[RAG Search] Error importing CandidateRAGPipeline: {e}")

@csrf_exempt
@login_required
def api_rag_search(request):
    """
    API endpoint for 'Talk to Resume' feature.
    Accepts a natural language query and returns matching candidate IDs.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    if not CandidateRAGPipeline:
        return JsonResponse({'error': 'RAG Pipeline module not found.'}, status=500)

    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)

        # 1. Fetch all applications (You might want to filter by specific Job ID later)
        applications = Application.objects.select_related('candidate').all()
        
        # 2. Build the ingest dictionary {application_id: resume_text}
        # We index by Application ID so the frontend can easily hide/show rows
        candidates_dict = {}
        for app in applications:
            if app.candidate and app.candidate.resume_text:
                candidates_dict[app.id] = app.candidate.resume_text
                
        if not candidates_dict:
            return JsonResponse({'matches': []})

        # 3. Instantiate and run RAG
        rag = CandidateRAGPipeline()
        rag.load_candidates(candidates_dict)
        results = rag.search_candidates(query, top_k=20, threshold=0.01)

        # Map results back to application_ids
        # results looks like: [{"candidate_id": <app_id>, "score": 0.15}, ...]
        matched_app_ids = [result['candidate_id'] for result in results]

        return JsonResponse({
            'matches': matched_app_ids,
            'details': results
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

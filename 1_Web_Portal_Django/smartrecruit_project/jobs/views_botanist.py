from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import logging
from .models import Interview, SentimentLog
from core.ai_engine import AIEngine
from core.utils.vocal_analyzer import VocalAnalyzer
from django.utils import timezone

logger = logging.getLogger(__name__)

@require_POST
def botanist_chat_view(request):
    """
    Handles real-time voice transcripts, generates Bot responses, 
    and logs behavioral fitment.
    """
    try:
        data = json.loads(request.body)
        user_text = data.get('text', '')
        interview_id = data.get('interview_id')
        
        if not user_text or not interview_id:
            return JsonResponse({'error': 'Missing data'}, status=400)
            
        interview = Interview.objects.get(id=interview_id)
        ai = AIEngine()
        
        # 1. Get Botanist Follow-up question
        # We can pass context via session or DB history if needed, for now simple interaction
        bot_reply = ai.get_botanist_response(user_text)
        
        # 2. Perform Vocal/Behavioral Analysis
        # Duration is estimated for now since we don't have start/end per phrase easily
        # Let's assume average phrase duration for metric scaling
        metrics = VocalAnalyzer.calculate_metrics(user_text, duration_seconds=max(5, len(user_text.split()) / 2))
        
        # 3. Log to SentimentLog
        SentimentLog.objects.create(
            interview=interview,
            emotion='neutral',
            score=0.9,
            voice_transcript=user_text,
            vocal_metrics=metrics,
            behavioral_score=metrics.get('confidence_impact', 0) + 50,
            vocal_confidence_score=metrics.get('confidence_impact', 0) + 70, # Scaled for UI
            speech_rate=metrics.get('wpm', 0),
            hesitation_count=metrics.get('pauses', 0),
            volume_consistency=metrics.get('stability', 0),
            behavioral_fitment_summary=bot_reply # Use current reply as a snippet
        )
        
        return JsonResponse({
            'reply': bot_reply,
            'metrics': metrics
        })
        
    except Interview.DoesNotExist:
        return JsonResponse({'error': 'Interview not found'}, status=404)
    except Exception as e:
        logger.error(f"Botanist Chat Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
def finalize_behavioral_round(request):
    """
    Summarizes the entire session's voice transcripts for the recruiter.
    """
    try:
        data = json.loads(request.body)
        interview_id = data.get('interview_id')
        interview = Interview.objects.get(id=interview_id)
        
        logs = SentimentLog.objects.filter(interview=interview).exclude(voice_transcript__isnull=True)
        full_transcript = " ".join([log.voice_transcript for log in logs])
        
        ai = AIEngine()
        summary = ai.evaluate_behavioral_fitment(full_transcript)
        
        # Update interview or application with summary if needed
        # For now, we return it to be displayed.
        return JsonResponse({'summary': summary})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

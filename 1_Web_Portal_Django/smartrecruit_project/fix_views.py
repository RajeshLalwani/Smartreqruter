import urllib.request
import os

views_path = r'C:/Users/ASUS/Documents/Tech Elecon Pvt. Ltd/Project/SmartRecruit/1_Web_Portal_Django/smartrecruit_project/jobs/views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '# BOTANIST INTERACTIVE VOICE AI VIEWS' in line:
        new_lines.append(line)
        break
    new_lines.append(line)

code = '''
@login_required
def botanist_interview_view(request, application_id):
    """
    Renders the Botanist voice interview interface.
    """
    from django.shortcuts import get_object_or_404, render
    from .models import Application, Interview
    application = get_object_or_404(Application, id=application_id)
    interview, created = Interview.objects.get_or_create(
        application=application,
        interview_type='BOTANIST',
        defaults={'status': 'SCHEDULED'}
    )
    
    return render(request, 'jobs/botanist_interview.html', {'interview': interview, 'application': application})

from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from core.ai_engine import AIEngine

@login_required
@require_POST
def botanist_process_view(request):
    """
    Real-time AI processor for Botanist voice responses.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(request.body)
        user_text = data.get('text', '')
        history = data.get('history', '')
        
        ai = AIEngine()
        bot_reply = ai.get_botanist_response(user_text, context_history=history)
        
        return JsonResponse({'reply': bot_reply})
    except Exception as e:
        logger.error(f"Botanist Process Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def botanist_finalize_view(request):
    """
    Finalizes the voice session, evaluates fitment, and calculates vocal metrics.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(request.body)
        interview_id = data.get('interview_id')
        full_transcript = data.get('full_transcript', '')
        
        from django.shortcuts import get_object_or_404
        from .models import Interview
        from .models import VoiceInterviewLog
        interview = get_object_or_404(Interview, id=interview_id)
        
        # 1. AI Behavioral Evaluation
        ai = AIEngine()
        fitment_summary = ai.evaluate_behavioral_fitment(full_transcript)
        
        # 2. Vocal Analytics
        duration = data.get('duration', len(full_transcript) / 10) # rough estimate
        from core.utils.voice_analytics import VoiceAnalytics
        analytics = VoiceAnalytics.analyze_voice_metadata(full_transcript, duration)
        
        # 3. Log the session
        VoiceInterviewLog.objects.create(
            interview=interview,
            transcript=full_transcript,
            ai_evaluation=fitment_summary,
            behavioral_fitment_summary=fitment_summary,
            vocal_confidence_score=analytics['vocal_confidence_score'],
            speech_rate=analytics['speech_rate'],
            hesitation_count=analytics['hesitation_count'],
            volume_consistency=analytics['volume_consistency']
        )
        
        # 4. Update Application Status
        application = interview.application
        application.status = 'ROUND_3_PASSED' if analytics['vocal_confidence_score'] > 60 else 'ROUND_3_FAILED'
        application.save()
        
        interview.status = 'COMPLETED'
        interview.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Botanist Finalize Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def interview_complete_view(request, interview_id):
    """
    Renders the interview complete view.
    """
    from django.shortcuts import get_object_or_404, render
    from .models import Interview
    interview = get_object_or_404(Interview, id=interview_id)
    return render(request, 'jobs/interview_complete.html', {'interview': interview})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def process_sentiment_stream(request, application_id):
    """
    API endpoint for real-time camera sentiment analysis.
    """
    import json
    import os
    import tempfile
    import base64
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import Application, Interview, SentimentLog

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        application = get_object_or_404(Application, id=application_id)
        interview = Interview.objects.filter(application=application).last()
        if not interview:
            return JsonResponse({'status': 'error', 'message': 'No interview found'}, status=404)

        score = 0.85
        emotion = 'neutral'

        if image_data:
            try:
                from deepface import DeepFace
                header, encoded = image_data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(img_bytes)
                    temp_img_path = tmp.name

                try:
                    analysis = DeepFace.analyze(img_path=temp_img_path, actions=['emotion'], enforce_detection=False)
                    if isinstance(analysis, list):
                        analysis = analysis[0]
                        
                    emotion = analysis.get('dominant_emotion', 'neutral')
                    emotions_dict = analysis.get('emotion', {})
                    score = (emotions_dict.get(emotion, 0.0) / 100.0) if emotions_dict else 0.85
                finally:
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
            except Exception as e:
                import logging
                logging.getLogger('jobs').error(f"DeepFace processing error: {e}")

        emotion = emotion.lower()
        if hasattr(SentimentLog, 'EMOTION_CHOICES') and emotion not in [c[0] for c in SentimentLog.EMOTION_CHOICES]:
            emotion = 'neutral'
            
        SentimentLog.objects.create(
            interview=interview,
            emotion=emotion,
            score=score
        )
        
        return JsonResponse({
            'status': 'success', 
            'emotion': emotion, 
            'score': round(score * 100, 2)
        })
        
    except Exception as e:
        import logging
        logging.getLogger('jobs').error(f"Sentiment Stream Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
'''

with open(views_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(code)

print('Done.')

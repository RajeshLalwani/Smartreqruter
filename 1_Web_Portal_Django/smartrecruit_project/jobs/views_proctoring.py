from django.shortcuts import render, get_object_or_404
from .security import get_authorized_application
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Application, ProctoringLog, ProctoringAnalysis
from django.core.files.base import ContentFile
import base64
import json
from datetime import datetime

@csrf_exempt
@login_required
@require_POST
def log_violation(request, application_id):
    """
    Receives proctoring logs (violations or periodic screenshots) from client JS.
    Enhanced for SecureSight (Vision).
    """
    try:
        application = get_authorized_application(request, application_id)
        
        log_type = request.POST.get('log_type', 'VIOLATION')
        details = request.POST.get('details', '')
        image_data = request.POST.get('image', None)
        
        # New: Machine Vision granular data
        face_count = int(request.POST.get('face_count', 1))
        pose_stability = float(request.POST.get('pose_stability', 1.0))
        
        log = ProctoringLog(
            application=application,
            log_type=log_type,
            details=details
        )
        
        if image_data and 'base64,' in image_data:
            format, imgstr = image_data.split(';base64,') 
            ext = format.split('/')[-1]
            filename = f"{log_type}_{application_id}_{datetime.now().strftime('%H%M%S')}.{ext}"
            log.image.save(filename, ContentFile(base64.b64decode(imgstr)), save=False)
            
        log.save()

        # If it's a vision-related violation, log to ProctoringAnalysis too
        if log_type in ['MULTI_FACE', 'PERSON_SWITCH', 'VIOLATION']:
            ProctoringAnalysis.objects.create(
                application=application,
                face_count=face_count,
                pose_stability=pose_stability,
                eye_status=request.POST.get('eye_status', 'LOOKING_CENTER'),
                is_impersonation_risk=(face_count > 1 or log_type == 'PERSON_SWITCH'),
                vision_confidence=0.95 # Simulated high confidence
            )
        
        return JsonResponse({'status': 'success', 'log_id': log.id})
        
    except Exception as e:
        print(f"Proctoring Log Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@login_required
@require_POST
def vision_heartbeat(request, application_id):
    """
    Periodic heartbeat from front-end Machine Vision (SecureSight).
    Doesn't necessarily create a 'Violation' but updates the analysis table.
    """
    try:
        application = get_authorized_application(request, application_id)
        data = json.loads(request.body)
        
        analysis = ProctoringAnalysis.objects.create(
            application=application,
            face_count=data.get('face_count', 1),
            pose_stability=data.get('pose_stability', 1.0),
            eye_status=data.get('eye_status', 'LOOKING_CENTER'),
            is_impersonation_risk=data.get('face_count', 1) > 1,
            vision_confidence=data.get('confidence', 0.9)
        )
        
        return JsonResponse({'status': 'success', 'analysis_id': analysis.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
@login_required
def interview_deep_vision(request, application_id):
    """DeepVision HUD: Monitoring interface for recruiters."""
    if not request.user.is_recruiter and not request.user.is_staff:
        from django.shortcuts import redirect
        return redirect('dashboard')
        
    application = get_authorized_application(request, application_id)
    return render(request, 'jobs/interview_deep_vision.html', {
        'application': application
    })

@csrf_exempt
@require_POST
def log_proctoring_violation_api(request):
    """
    Stand-alone API for logging tab switches, gaze deviations.
    """
    try:
        data = json.loads(request.body)
        interview_id = data.get('interview_id')
        violation_type = data.get('violation_type')
        details = data.get('details', '')
        
        from jobs.models import Interview, SentimentLog
        interview = get_object_or_404(Interview, id=interview_id)
        
        # Log to SentimentLog (since proctoring flags go there now)
        flags = {violation_type: True}
        SentimentLog.objects.create(
            interview=interview,
            emotion='neutral',
            score=0,
            proctoring_flags=flags
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

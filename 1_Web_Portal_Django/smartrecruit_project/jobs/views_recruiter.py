import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from core.utils.docker_engine import get_system_load
from core.utils.bias_auditor import run_bias_audit
from jobs.models import AuditLog
from .models import Application, SystemDesignAssessment
from Interview_Bot.interviewer import AIInterviewer

@login_required
def save_system_design(request, application_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            diagram = data.get('diagram')
            analysis_schema = data.get('analysis_schema')
            
            app = Application.objects.get(id=application_id)
            
            # Trigger AI Evaluation
            bot = AIInterviewer()
            ai_eval = bot.evaluate_architecture(analysis_schema)
            
            assessment, created = SystemDesignAssessment.objects.update_or_create(
                application=app,
                defaults={
                    'diagram_json': diagram,
                    'ai_score': ai_eval.get('score', 70),
                    'ai_analysis': ai_eval.get('critique', 'Architecture preserved.')
                }
            )
            
            return JsonResponse({
                'status': 'success', 
                'score': assessment.ai_score,
                'analysis': assessment.ai_analysis
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@login_required
def system_load_api(request):
    """
    Returns real-time Docker sandbox and Host CPU stats.
    Only accessible to recruiters/admins.
    """
    if not request.user.is_recruiter:
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    stats = get_system_load()
    return JsonResponse(stats)

@login_required
def ethics_audit_api(request, job_id):
    """
    Runs a fresh bias audit for a job and returns the latest metrics.
    """
    if not request.user.is_recruiter:
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    # Trigger fresh audit
    log = run_bias_audit(job_id)
    
    return JsonResponse({
        'fairness_score': log.fairness_score,
        'dir_ratio': log.disparate_impact_ratio,
        'has_risk': log.has_risk,
        'risk_details': log.risk_details,
        'demographics': log.demographics_json
    })

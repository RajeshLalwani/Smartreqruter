import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ATSSyncLog, ATSSyncConfig, Application, ExternalATSMapping
from core.api.ats_sync import ATSSyncManager

@csrf_exempt
def ats_webhook_listener(request):
    """
    Ingests status changes from external ATS platforms.
    Endpoint: /api/v1/ats-sync/
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body)
        # Use the new ATSSyncManager for pull logic
        success = ATSSyncManager.pull_candidate_status(payload)
        
        if success:
            return JsonResponse({"status": "success", "message": "Internal stage updated"}, status=200)
        else:
            return JsonResponse({"status": "error", "message": "Update failed or mapping missing"}, status=400)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@login_required
def ats_sync_monitor(request):
    """
    Recruiter Dashboard: ATS Synchronization Logs & Connectivity Status.
    """
    if not request.user.is_recruiter:
        return HttpResponse("Unauthorized", status=403)

    logs = ATSSyncLog.objects.all().select_related('application', 'application__candidate')[:50]
    configs = ATSSyncConfig.objects.all()
    
    # Check connectivity via env status
    api_status = "ONLINE" if os.environ.get("WORKDAY_API_KEY") or os.environ.get("GREENHOUSE_API_KEY") else "OFFLINE"

    context = {
        "logs": logs,
        "configs": configs,
        "api_status": api_status,
        "platform": "Multi-Provider (Enterprise)"
    }
    return render(request, 'jobs/ats_sync_monitor.html', context)

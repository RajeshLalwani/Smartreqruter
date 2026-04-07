import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WebhookConfig, Candidate, Application, JobPosting
from django.contrib.auth import get_user_model
User = get_user_model()
from .views_advanced import _recruiter_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

@login_required
def automation_hub(request):
    """UI for managing external AI Orchestration (n8n/Zapier)."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    webhooks = WebhookConfig.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')
        event_type = request.POST.get('event_type')
        
        if name and url and event_type:
            WebhookConfig.objects.create(name=name, url=url, event_type=event_type)
            messages.success(request, f"Successfully connected '{name}' to our AI Pipeline!")
            return redirect('automation_hub')

    return render(request, 'jobs/automation_hub.html', {
        'webhooks': webhooks,
        'event_choices': WebhookConfig.EVENT_CHOICES
    })

@login_required
def delete_webhook(request, webhook_id):
    if not _recruiter_required(request): return redirect('dashboard')
    webhook = get_object_or_404(WebhookConfig, pk=webhook_id)
    webhook.delete()
    messages.warning(request, "Automation hook disconnected.")
    return redirect('automation_hub')

def dispatch_webhook_event(event_type, payload):
    """
    Sends a JSON payload to all active webhooks listening for a specific event.
    Designed for n8n/Zapier integration.
    """
    active_hooks = WebhookConfig.objects.filter(event_type=event_type, is_active=True)
    
    for hook in active_hooks:
        try:
            # We use a timeout to ensure the recruitment portal isn't bogged down by external tools
            response = requests.post(hook.url, json={
                'event': event_type,
                'source': 'SmartRecruit_AI_Portal',
                'timestamp': str(json.dumps(payload)), # Wrapping in string for n8n safety if needed
                'data': payload
            }, timeout=3)
            print(f"Automation triggered: {hook.name} - Status: {response.status_code}")
        except Exception as e:
            print(f"FAILED to trigger automation {hook.name}: {str(e)}")

@csrf_exempt
def receive_sourced_candidate(request):
    """
    Inbound webhook receiver for n8n/Zapier.
    Creates a passive candidate and an application in the SOURCED column.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
        
    # Simple token auth check (in production this would be a real secret)
    auth_header = request.headers.get('Authorization')
    if auth_header != 'Bearer SMARTRECRUIT_N8N_SECRET_TOKEN':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        data = json.loads(request.body)
        
        # 1. Parse Payload
        name = data.get('name', 'Unknown Candidate')
        email = data.get('email', f"sourced_{name.replace(' ', '').lower()}_{int(timezone.now().timestamp())}@example.com")
        linkedin_url = data.get('linkedin_url', '')
        skills = data.get('skills', '')
        job_id = data.get('target_job_id')
        
        if not job_id:
            return JsonResponse({'error': 'target_job_id is required'}, status=400)
            
        job = get_object_or_404(JobPosting, pk=job_id)
        
        # 2. Create User (mock account)
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        user = User.objects.create(
            username=username,
            email=email,
            first_name=name.split()[0] if ' ' in name else name,
            last_name=' '.join(name.split()[1:]) if ' ' in name else ''
        )
        user.set_unusable_password()
        user.save()
        
        # 3. Create Candidate Profile
        candidate = Candidate.objects.create(
            user=user,
            full_name=name,
            email=email,
            portfolio_url=linkedin_url,
            skills_extracted=skills,
            is_passive_sourced=True
        )
        
        # 4. Create Application in "SOURCED" column
        application = Application.objects.create(
            job=job,
            candidate=candidate,
            source_of_hire='AI_HUNTER',
            status='SOURCED'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Candidate {name} sourced and added to {job.title}',
            'application_id': application.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

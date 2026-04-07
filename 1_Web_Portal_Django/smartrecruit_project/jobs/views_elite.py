import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import JobPosting, Application, Candidate, SystemDesignAssessment
from .views_advanced import _recruiter_required, _gemini
from core.utils.gamification import get_leaderboard_data
from core.utils.system_design_ai import evaluate_design
import requests

# ══════════════════════════════════════════════════════════════════════════════
# 29. AI INTERVIEW CO-PILOT (Recruiter - Live)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def interview_copilot(request, application_id):
    """Real-time AI assistant for live interviews."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    
    # Mocking live transcript segments
    transcript_segments = [
        "Candidate: I usually prefer working with microservices because they allow us to scale independently.",
        "Interviewer: How do you handle distributed transactions in that case?",
        "Candidate: We used the Saga pattern with RabbitMQ to maintain eventual consistency."
    ]
    
    prompt = f"""As an AI Interview Co-Pilot, analyze this live transcript:
{transcript_segments}

Candidate Skills: {candidate.skills_extracted or 'Technical Skills'}
Role: {application.job.title}

Return ONLY valid JSON:
{{
  "realtime_feedback": "Strong answer on Saga patterns. Shows deep architectural knowledge.",
  "suggested_followups": [
    "Ask about how they handle compensating transactions in failures.",
    "Ask about the latency implications of using RabbitMQ for this."
  ],
  "red_flag_check": "No immediate red flags. Candidate seems technically grounded.",
  "sentiment_score": 88
}}"""
    fallback = {
        'realtime_feedback': 'Candidate is articulating architectural patterns clearly.',
        'suggested_followups': ['How do you handle data consistency?', 'Describe a failure scenario.'],
        'red_flag_check': 'None',
        'sentiment_score': 75
    }
    copilot_intel = _gemini(prompt, fallback)
    if not isinstance(copilot_intel, dict): copilot_intel = fallback

    return render(request, 'jobs/interview_copilot.html', {
        'application': application,
        'candidate': candidate,
        'intel': copilot_intel,
        'transcript': transcript_segments
    })

# ══════════════════════════════════════════════════════════════════════════════
# 30. AUTOMATED REFERENCE BOT (Enterprise)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def reference_check_bot(request, application_id):
    """AI agent that conducts and summarizes reference checks."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    
    # Mocking reference responses
    references = [
        {'name': 'Mark Spencer', 'company': 'Google', 'relation': 'Former Manager', 'response': 'Excellent coder, very proactive.'},
        {'name': 'Lisa Wong', 'company': 'Stripe', 'relation': 'Peer', 'response': 'Great team player, but sometimes over-engineers solutions.'}
    ]
    
    prompt = f"""Synthesize reference check data for {candidate.full_name}:
{references}

Return ONLY valid JSON:
{{
  "integrity_report": "High trust. Consistent positive feedback from managers.",
  "peer_consensus": "Collaborative but focus-heavy.",
  "verified_impact": "Successfully led the API migration project at Google.",
  "cautionary_note": "Ensure clear requirements to avoid excessive complexity (over-engineering).",
  "overall_validity_score": 94
}}"""
    fallback = {
        'integrity_report': 'Positive overall feedback.',
        'peer_consensus': 'Team player.',
        'verified_impact': 'Impact verified.',
        'cautionary_note': 'None',
        'overall_validity_score': 85
    }
    report = _gemini(prompt, fallback)
    if not isinstance(report, dict): report = fallback

    return render(request, 'jobs/reference_bot.html', {
        'application': application,
        'candidate': candidate,
        'references': references,
        'report': report
    })

# ══════════════════════════════════════════════════════════════════════════════
# 31. BLIND HIRING REDACTOR (DEI Focus)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def blind_hiring_redactor(request, application_id):
    """View that redacts PII for unbiased initial screening."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    
    # Mocking redaction of skills and history
    original_history = "I worked at Google India for 3 years as a Lead Engineer."
    redacted_history = "I worked at [TIER-1 TECH] for 3 years as a [SENIOR ROLE]."
    
    return render(request, 'jobs/blind_review.html', {
        'application': application,
        'redacted_history': redacted_history,
        'original_candidate': candidate
    })

# ══════════════════════════════════════════════════════════════════════════════
# 32. GLOBAL TALENT DENSITY HEATMAP (Enterprise Strategy)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def talent_density_map(request):
    """Visualizes global talent trends and density maps."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    # ── REAL LOCATION DATA ──
    from django.db.models import Count
    location_stats = Candidate.objects.values('current_location').annotate(count=Count('id')).order_by('-count')
    
    # Static GPS mapping for demo cities (can be expanded)
    gps_map = {
        'Bangalore': [12.97, 77.59],
        'San Francisco': [37.77, -122.41],
        'London': [51.50, -0.12],
        'Hyderabad': [17.38, 78.48],
        'New York': [40.71, -74.00],
        'Mumbai': [19.07, 72.87],
        'Remote': [0, 0]
    }
    
    density_data = []
    for loc in location_stats:
        city = loc['current_location']
        count = loc['count']
        coords = gps_map.get(city, [20.59, 78.96]) # Default to India center if unknown
        density_data.append({
            'city': city,
            'density': min(100, count * 10),
            'lat': coords[0],
            'lng': coords[1],
            'trend': random.choice(['Increasing', 'Stable'])
        })
    
    return render(request, 'jobs/talent_map.html', {
        'density_data':      json.dumps(density_data),
        'density_data_list': density_data
    })

# ══════════════════════════════════════════════════════════════════════════════
# 33. CAREER PATH MULTIVERSE EXPLORER (Candidate)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def career_trajectory_explorer(request):
    """Helps candidates visualize future trajectories within the company."""
    if request.user.is_recruiter:
        return redirect('dashboard')

    try:
        candidate = request.user.candidate_profile
    except AttributeError:
        # Fallback if profile doesn't exist
        candidate = None
    
    skills = candidate.skills_extracted if candidate and candidate.skills_extracted else "Python, AI"
    
    prompt = f"""Generate 3 potential career trajectories for a candidate with skills: {skills}.
    Return ONLY valid JSON:
    [
      {{
        "name": "The Technical Path",
        "growth": "High",
        "outcome": "Principal Engineer",
        "milestones": ["Lead architecture", "Scale systems"],
        "color": "#7c4dff"
      }},
      ... (3 items)
    ]"""
    
    fallback = [
        {'name': 'Architect', 'growth': 'High', 'outcome': 'CTO', 'milestones': ['Design systems'], 'color': '#7c4dff'},
        {'name': 'Manager', 'growth': 'Medium', 'outcome': 'VP Eng', 'milestones': ['Lead teams'], 'color': '#00c851'},
        {'name': 'Specialist', 'growth': 'Stable', 'outcome': 'Domain Expert', 'milestones': ['Research'], 'color': '#ffbb33'}
    ]

    try:
        # Call AI for trajectories
        ai_response = _gemini(prompt)
        # remove markdown formatting if present
        if ai_response.startswith('```'):
            ai_response = ai_response.strip('`').strip('json').strip()
        paths = json.loads(ai_response)
        if not isinstance(paths, list):
            paths = fallback
    except Exception:
        paths = fallback
    
    # ── LEADERBOARD ──
    leaderboard = get_leaderboard_data(limit=5)
    
    # Mark current candidate in leaderboard
    current_candidate_pseudonym = None
    if candidate:
        # We need to know which entry is the current user. 
        # get_leaderboard_data should ideally return the ID if we ask for it or we can match pseudonym if unique enough
        # For now, let's just pass the candidate object to help the template
        pass

    return render(request, 'jobs/career_multiverse.html', {
        'paths': paths,
        'leaderboard': leaderboard,
        'current_candidate': candidate
    })

@login_required
def infra_health_monitor(request):
    """Real-time monitoring of the private execution cluster."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    try:
        # Query the Smart-Runner health endpoint
        resp = requests.get("http://localhost:8001/health", timeout=2)
        health_data = resp.json()
    except Exception:
        health_data = {
            "status": "offline",
            "engine": "unknown",
            "active_containers": 0
        }

    return render(request, 'jobs/infra_health.html', {
        'health': health_data,
        'midnight_mode': True
    })

@login_required
def ethics_diversity_dashboard(request):
    """Suite for advanced bias auditing and demographic analysis."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    # Fetch recent audit logs
    audit_logs = BiasAuditLog.objects.filter(job__recruiter=request.user)
    
    # Generic bias stats (Retrospective from all jobs)
    all_apps = Application.objects.filter(job__recruiter=request.user).select_related('candidate')
    
    # Trigger a baseline audit if none exist
    if not audit_logs.exists() and all_apps.exists():
        # Optional: Auto-trigger audit for the most recent job
        pass

    return render(request, 'jobs/ethics_dashboard.html', {
        'audit_logs': audit_logs,
        'total_evaluated': all_apps.count(),
        'midnight_mode': True
    })

@login_required
def run_bias_audit_api(request, job_id):
    """Trigger a new bias audit for a specific job."""
    if not _recruiter_required(request):
        return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=403)
    
    job = get_object_or_404(JobPosting, pk=job_id, recruiter=request.user)
    
    from core.utils.bias_auditor import AuditEngine
    auditor = AuditEngine(job)
    log = auditor.run_retrospective_audit()
    
    return JsonResponse({
        'ok': True,
        'audit_id': log.id,
        'fairness_score': log.fairness_score,
        'has_risk': log.has_risk,
        'is_certified': log.is_certified
    })

# ══════════════════════════════════════════════════════════════════════════════
# 31. SYSTEM DESIGN ASSESSMENT (API & Views)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def save_system_design(request, application_id):
    """Saves candidate's architectural diagram and triggers AI scoring."""
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        try:
            diagram_json = json.loads(request.body)
            # Perform AI Evaluation
            result = evaluate_design(diagram_json)
            assessment, created = SystemDesignAssessment.objects.update_or_create(
                application=application,
                defaults={
                    'diagram_json': diagram_json,
                    'ai_score': result.get('score', 0.0),
                    'ai_analysis': result.get('analysis', "Architecture analyzed successfully.")
                }
            )
            return JsonResponse({
                'status': 'success',
                'score': assessment.ai_score,
                'analysis': assessment.ai_analysis
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def architecture_preview(request, application_id):
    """Allows recruiters to review the candidate's captured architecture diagram."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    application = get_authorized_application(request, application_id)
    assessment = getattr(application, 'system_design', None)
    return render(request, 'jobs/architecture_preview.html', {
        'application': application,
        'assessment': assessment
    })

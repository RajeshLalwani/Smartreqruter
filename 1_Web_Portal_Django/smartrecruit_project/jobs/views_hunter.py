import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .views_advanced import _gemini, _recruiter_required

@login_required
def hunter_outreach_terminal(request):
    """
    The Hunter: Autonomous outreach and lead engagement.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
        
    from .models import SourcingMatch
    # Fetch real scouted leads from the Matchmaker results
    scouted_matches = SourcingMatch.objects.filter(job__recruiter=request.user).select_related('candidate', 'job')[:20]
    
    scouted_leads = []
    for m in scouted_matches:
        scouted_leads.append({
            "name": m.candidate.full_name,
            "profile": f"portal.ai/candidate/{m.candidate.id}",
            "status": "Ready for Outreach",
            "match_score": m.match_score
        })
    
    # Fallback to demo data only if database is empty
    if not scouted_leads:
        scouted_leads = [
            {"name": "Arjun Mehta (Demo)", "profile": "github.com/arjun-dev", "status": "Ready for Outreach", "match_score": 92},
            {"name": "Sara Khan (Demo)", "profile": "linkedin.com/in/sara-ai", "status": "Ready for Outreach", "match_score": 88}
        ]
    
    return render(request, 'jobs/hunter_terminal.html', {
        'leads': scouted_leads
    })

@login_required
def initiate_autonomous_engagement(request):
    """
    AI Agent starts a multi-step outreach sequence.
    """
    if request.method != 'POST': return JsonResponse({'error': 'Invalid'}, status=400)
    
    data = json.loads(request.body)
    lead_name = data.get('lead_name')
    lead_profile = data.get('lead_profile')
    
    prompt = f"""
    Role: Autonomous Talent Hunter (AI Agent).
    Task: Write a highly personalized, non-spammy outreach email to {lead_name} ({lead_profile}).
    Context: We are looking for high-velocity talent for a Top Tech Role.
    
    Sequence Step: 1 (The Hook).
    
    Return JSON:
    {{
      "subject": "Unique insight regarding your {lead_profile} project",
      "body": "...",
      "agent_thought": "I noticed their contribution to X repo, using that as the ice-breaker."
    }}
    """
    
    engagement = _gemini(prompt, {
        "subject": "Opportunity Inquiry",
        "body": "Hi, I saw your profile and liked it.",
        "agent_thought": "Standard outreach."
    })
    
    return JsonResponse({
        'lead_name': lead_name,
        'subject': engagement.get('subject'),
        'body': engagement.get('body'),
        'thought': engagement.get('agent_thought')
    })

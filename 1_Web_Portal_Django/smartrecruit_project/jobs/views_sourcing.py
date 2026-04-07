import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .views_advanced import _gemini, _recruiter_required

@login_required
def talent_scout_dashboard(request):
    """
    Main Hub for Passive Talent Sourcing.
    Allows recruiters to 'Crawl' potential leads before they apply.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    # Track 'Scouted' leads in session for demonstration (in production, use a Model)
    scouted_leads = request.session.get('scouted_leads', [])
    
    url_input = request.POST.get('profile_url', '').strip()
    analysis = None
    
    if request.method == 'POST' and url_input:
        # 🛰️ AGENTIC CRAWL & ANALYSIS (Simulated via Scout-X)
        scout_prompt = f"""
        Role: Scout-X (Technical Talent Hunter).
        Task: Evaluate a potential passive candidate based on their Public Footprint (URL: {url_input}).
        
        Since this is a simulation, synthesize a HIGH-FIDELITY evaluation of a hypothetical top-tier developer.
        Include:
        1. Primary Tech Stack.
        2. 'Open Source Weight' (impact in community).
        3. Potential 'Churn Risk' (how likely they are to leave their current role).
        4. Comparison to our internal 'Elite' benchmarks.
        
        Return ONLY valid JSON:
        {{
          "full_name": "Synthesized Name",
          "headline": "Senior Cloud Architect @ Fortune 500",
          "stack": ["Golang", "AWS", "gRPC", "K8s"],
          "scout_score": 94,
          "oss_weight": "High (Core Contributor to Kubernetes)",
          "churn_risk": "Low (Recently started new role)",
          "pitch_strategy": "Highlight our autonomous agentic infrastructure to pique their curiosity."
        }}
        """
        fallback = {
            'full_name': 'Passive Lead (Analysing...)',
            'headline': 'Software Engineer',
            'stack': ['Python', 'Django'],
            'scout_score': 75,
            'oss_weight': 'Medium',
            'churn_risk': 'Medium',
            'pitch_strategy': 'Direct reach out via LinkedIn.'
        }
        analysis = _gemini(scout_prompt, fallback)
        if not isinstance(analysis, dict): analysis = fallback
        
        # Save to session (Simulation only)
        analysis['url'] = url_input
        scouted_leads.insert(0, analysis)
        request.session['scouted_leads'] = scouted_leads[:10] # Keep last 10
        request.session.modified = True

    return render(request, 'jobs/sourcing_dashboard.html', {
        'scouted_leads': scouted_leads,
        'analysis': analysis,
        'url_input': url_input
    })

@login_required
def delete_scouted_lead(request, index):
    """Simple session-based lead removal."""
    scouted_leads = request.session.get('scouted_leads', [])
    if 0 <= index < len(scouted_leads):
        scouted_leads.pop(index)
        request.session['scouted_leads'] = scouted_leads
        request.session.modified = True
    return redirect('sourcing_dashboard')

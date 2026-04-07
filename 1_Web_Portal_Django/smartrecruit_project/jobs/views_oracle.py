import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .views_advanced import _gemini, _recruiter_required
from .matchmaker import MatchmakerAgent
from .models import SourcingMatch, Application, JobPosting

@login_required
def refresh_talent_pool(request):
    """Trigger the Matchmaker sourcing cycle."""
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    agent = MatchmakerAgent()
    count = agent.run_sourcing_cycle()
    
    from django.contrib import messages
    messages.success(request, f"The Matchmaker discovered {count} new high-potential candidates!")
    return redirect('oracle_intelligence_dashboard')

@login_required
def oracle_intelligence_dashboard(request):
    """
    The Oracle: Multi-agent Market Intelligence for Recruiters.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    # Simulate Market Data for the Oracle to Analyze
    market_context = {
        "sector": "Tech / FinTech",
        "hot_skills": ["Rust", "GenAI", "Solana", "Next.js"],
        "competitor_activity": [
            {"company": "Competitor X", "hiring_status": "Laying off", "sentiment": "Negative", "locations": ["Bangalore", "Mumbai"]},
            {"company": "Competitor Y", "hiring_status": "Aggressive Growth", "sentiment": "Positive", "locations": ["Pune", "Hyderabad"]},
            {"company": "Competitor Z", "hiring_status": "Steady", "sentiment": "Neutral", "locations": ["Gurgaon"]}
        ]
    }
    
    prompt = f"""
    Role: Market Intelligence Oracle (AI Agent).
    Context: Analyze the following tech market snapshot: {json.dumps(market_context)}
    
    Task: Generate a 'Strategic Intelligence Briefing'.
    1. Identify 'Talent Opportunities' (Where should we hunt?).
    2. Salary Volatility (Is the market over-paying?).
    3. Competitor Weakness (Who is losing talent?).
    
    Return ONLY JSON:
    {{
      "opportunity_score": 88,
      "briefing_text": "...",
      "recommendations": ["Hunt at Competitor X", "Focus on Node.js talent in Mumbai"],
      "salary_trend": "Rising +12%",
      "heatmap_data": [
          {{"city": "Bangalore", "density": 85, "growth": 12}},
          {{"city": "Mumbai", "density": 60, "growth": -5}}
      ]
    }}
    """
    
    intelligence = _gemini(prompt, {
        "opportunity_score": 50,
        "briefing_text": "Market data currently stabilizing.",
        "recommendations": ["Expand talent pool"],
        "salary_trend": "Neutral",
        "heatmap_data": []
    })

    # Fetch Top Matches from The Matchmaker
    agent = MatchmakerAgent()
    top_matches = SourcingMatch.objects.filter(job__recruiter=request.user).select_related('candidate', 'job')[:10]

    return render(request, 'jobs/oracle_dashboard.html', {
        'intel': intelligence,
        'market': market_context,
        'top_matches': top_matches
    })

@login_required
def recruiter_decision_matrix(request, job_id):
    """
    Elite Decision Suite: Compares candidates for a job side-by-side.
    """
    if not _recruiter_required(request): # Changed from request.user.is_recruiter to _recruiter_required(request) for consistency
        return redirect('dashboard')
        
    job = get_object_or_404(JobPosting, pk=job_id, recruiter=request.user)
    matrix = DecisionMatrixAgent.generate_matrix(job_id)
    
    # Enrich matrix with application objects for template access
    if matrix and 'rankings' in matrix:
        for r in matrix['rankings']:
            app_id = r.get('application_id')
            if app_id:
                r['application'] = Application.objects.get(pk=app_id)

    return render(request, 'jobs/decision_matrix.html', {
        'job': job,
        'matrix': matrix,
        'rankings': matrix.get('rankings', []) if matrix else [],
        'recommendation': matrix.get('hiring_recommendation', '') if matrix else ''
    })
@login_required
def roi_oracle_view(request):
    """High-level Strategic ROI Dashboard."""
    if not _recruiter_required(request): return redirect('dashboard')
    
    # Simulate ROI data for top candidates
    from .models import Candidate
    candidates = Candidate.objects.all()[:5]
    top_candidates = []
    for cand in candidates:
        top_candidates.append({
            'name': cand.full_name,
            'role': getattr(cand, 'current_role', 'Specialist'),
            'value': "12,40,000"
        })
        
    return render(request, 'jobs/roi_oracle.html', {
        'top_candidates': top_candidates
    })

import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from .models import JobPosting, Application, Candidate
from django.utils import timezone
from datetime import timedelta
from .views_advanced import _recruiter_required, _gemini

# ══════════════════════════════════════════════════════════════════════════════
# 34. AI NEGOTIATION SPARRER (Agentic AI - Candidate)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def negotiation_sparring(request, application_id):
    """Agentic AI that simulates a tough salary negotiation."""
    if request.user.is_recruiter:
        return redirect('dashboard')

    application = get_authorized_application(request, application_id)
    
    # ── REAL BUDGET DATA ──
    salary_range = application.job.salary_range or "$140,000"
    market_benchmark = salary_range.split('-')[-1].strip() if '-' in salary_range else salary_range
    
    # Mocking a conversation turn
    candidate_message = request.POST.get('message', 'I am looking for a fair market adjustment based on my technical contributions.')
    
    prompt = f"""Act as an Agentic AI Recruiter 'Sparrow'.
    Target Role: {application.job.title}
    Market Benchmark (Budget): {market_benchmark}
    Candidate's Opening: "{candidate_message}"
    
    Think like a data scientist. Calculate:
    1. Anchor strength (0-100)
    2. Compromise probability (0-100)
    
    Return ONLY valid JSON:
    {{
      "agent_response": "I see you've done your research. While we value niche expertise, $168k is at the 95th percentile for this level. How would you feel about $155k with a performance-based equity kicker?",
      "tactical_critique": "Your opening was bold but lacked a specific data-driven anchor. Try referencing a recent industry report.",
      "closing_strength": 72,
      "ai_counter_strategy": "Anchoring high to see how candidate reacts to equity vs salary."
    }}"""
    
    fallback = {
        'agent_response': 'That is a significant jump. Let us discuss the total compensation package.',
        'tactical_critique': 'Good confidence, needs more data support.',
        'closing_strength': 50,
        'ai_counter_strategy': 'Neutral'
    }
    sparring_result = _gemini(prompt, fallback)
    # Determine agent status perception
    closing_score = sparring_result.get('closing_strength', 50)
    agent_status = "Tough" if closing_score > 70 else ("Flexible" if closing_score < 40 else "Professional")

    return render(request, 'jobs/negotiation_sparring.html', {
        'application': application,
        'result': sparring_result,
        'agent_status': agent_status,
        'history': [{'role': 'Candidate', 'text': candidate_message}, {'role': 'AI Recruiter', 'text': sparring_result['agent_response']}]
    })

# ══════════════════════════════════════════════════════════════════════════════
# 35. PREDICTIVE TALENT CHURN SENTINEL (Data Science/ML - Enterprise)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def talent_churn_sentinel(request):
    """ML-driven dashboard predicting employee retention risk."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    from .models import ActivityLog, CandidateXP
    
    # Analyze candidates with high XP or activity as "employees"
    employees = Candidate.objects.all()[:15]
    sentinel_data = []
    
    for emp in employees:
        # ── REAL RISK ANALYSIS ──
        xp = CandidateXP.objects.filter(user=emp.user).first()
        activity_count = ActivityLog.objects.filter(user=emp.user, timestamp__gte=timezone.now() - timedelta(days=30)).count()
        
        # Risk factors: high XP + low recent activity = likely to leave or bored
        risk_score = 50
        if xp and xp.total_xp > 1000 and activity_count < 5:
            risk_score = 80
        elif activity_count > 20:
            risk_score = 20
        
        drivers = ["Stagnant compensation" if risk_score > 70 else "High engagement"]
        recommendation = "Suggest a growth-tier review." if risk_score > 50 else "Stable - no action needed."
        
        sentinel_data.append({
            'name': emp.full_name,
            'risk': risk_score,
            'status': 'High Risk' if risk_score > 70 else ('Moderate' if risk_score > 30 else 'Stable'),
            'drivers': drivers,
            'action': recommendation
        })
        
    return render(request, 'jobs/churn_sentinel.html', {
        'sentinel_data': sentinel_data
    })

# ══════════════════════════════════════════════════════════════════════════════
# 36. 30-60-90 DAY AI SUCCESS BLUEPRINT (Generative AI - Post-Hire)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def success_blueprint(request, application_id):
    """Generative AI creates a custom onboarding roadmap."""
    application = get_authorized_application(request, application_id)
    candidate   = application.candidate

    prompt = f"""Generate a high-performance 30-60-90 day Success Blueprint for {candidate.full_name} in the role of {application.job.title}.
    Candidate's Skill Gaps: {candidate.technical_skills or 'N/A'}
    Role Complexity: High (Enterprise)
    
    Return ONLY valid JSON:
    {{
      "month_1": {{"focus": "Integration", "milestones": ["Master CI/CD Pipeline", "Complete Security Training"]}},
      "month_2": {{"focus": "Execution", "milestones": ["Lead 1 minor release", "Refactor core module"]}},
      "month_3": {{"focus": "Innovation", "milestones": ["Propose architectural optimization", "Mentor 1 junior"]}},
      "growth_stack": ["System Design", "Cloud FinOps", "Agentic Frameworks"]
    }}"""
    
    fallback = {
        'month_1': {'focus': 'Onboarding', 'milestones': ['Setup Dev Env']},
        'month_2': {'focus': 'Core Tasks', 'milestones': ['Ticket completion']},
        'month_3': {'focus': 'Impact', 'milestones': ['Feature ownership']},
        'growth_stack': ['Internal Tooling']
    }
    blueprint = _gemini(prompt, fallback)
    if not isinstance(blueprint, dict): blueprint = fallback

    return render(request, 'jobs/success_blueprint.html', {
        'application': application,
        'blueprint': blueprint,
        'candidate': candidate
    })

# ══════════════════════════════════════════════════════════════════════════════
# 37. GLOBAL RELOCATION & LIFESTYLE AI (Data Science - Candidate)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def relocation_lifestyle_ai(request):
    """Data science comparison of relocation impact."""
    if request.user.is_recruiter:
        return redirect('dashboard')

    job_loc = "Bengaluru, India" # Default or pull from a session/last job
    
    prompt = f"""Suggest 3 global relocation destinations for a candidate currently looking at {job_loc}.
    Include Rent Index (1-100), Quality of Life (1-100), and Tech Scene summary.
    Return ONLY valid JSON:
    [
      {{"city": "Austin, TX", "rent_index": 72, "quality_of_life": 88, "tech_scene": "Explosive"}},
      ...
    ]"""
    
    fallback = [
        {'city': 'Austin, TX', 'rent_index': 72, 'quality_of_life': 88, 'tech_scene': 'Explosive'},
        {'city': 'Berlin, Germany', 'rent_index': 65, 'quality_of_life': 94, 'tech_scene': 'Vibrant/Artistic'},
        {'city': 'Dubai, UAE', 'rent_index': 85, 'quality_of_life': 82, 'tech_scene': 'Hyper-Growth'}
    ]
    
    destinations = _gemini(prompt, fallback)
    if not isinstance(destinations, list): destinations = fallback
    
    return render(request, 'jobs/relocation_ai.html', {
        'destinations': destinations
    })

# ══════════════════════════════════════════════════════════════════════════════
# 38. CULTURE-FIT DIGITAL TWIN SIMULATOR (Agentic AI - Candidate)
# ════════════════════════════════════════──────────────────────────────────────
@login_required
def culture_fit_simulator(request, application_id):
    """Simulates agentic personalities of future teammates."""
    if request.user.is_recruiter:
        return redirect('dashboard')

    application = get_authorized_application(request, application_id)
    
    # ── REAL CONTEXT SEEDING ──
    prompt = f"""Generate 3 'Digital Twin' personas for future teammates for a {application.job.title} role.
    Return ONLY valid JSON:
    [
      {{"name": "Alex (Lead)", "trait": "Direct", "intro": "..."}},
      ...
    ]"""
    
    fallback = [
        {'name': 'Alex (Lead Engineer)', 'trait': 'Direct & Technical', 'intro': "I value clean code and 'No BS' standups. Ready for a deep-dive challenge?"},
        {'name': 'Sarah (Product Manager)', 'trait': 'Empathetic & Strategic', 'intro': "I focus on user impact and cross-team alignment. How do you handle scope creep?"},
        {'name': 'Agent V (Team Bot)', 'trait': 'Optimizing', 'intro': "I monitor team velocity and distribute coffee credits."}
    ]
    
    twins = _gemini(prompt, fallback)
    if not isinstance(twins, list): twins = fallback
    
    return render(request, 'jobs/culture_simulator.html', {
        'application': application,
        'twins': twins
    })

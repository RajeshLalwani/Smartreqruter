import json
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Application, NegotiationSession, Offer
from .views_advanced import _gemini

@login_required
def negotiation_war_room(request, application_id):
    """
    Candidate portal for autonomous salary negotiation.
    """
    application = get_object_or_404(Application, pk=application_id, candidate__user=request.user)
    
    # Ensure negotiation session exists
    session, created = NegotiationSession.objects.get_or_create(
        application=application,
        defaults={
            'initial_salary_offer': 800000, # Mock initial
            'current_salary_offer': 800000,
            'max_budget': 1200000,          # Mock ceiling
            'chat_history': [{"role": "agent", "text": f"Congratulations {application.candidate.full_name}! We're excited to offer you the {application.job.title} role with an initial salary of ₹8,00,000. How do you feel about this?"}]
        }
    )

    return render(request, 'jobs/negotiation_room.html', {
        'application': application,
        'session': session
    })

@login_required
def process_negotiation_msg(request, application_id):
    """
    AI Logic for the 'Closer' agent.
    """
    if request.method != 'POST': return JsonResponse({'error': 'Invalid'}, status=400)
    
    application = get_object_or_404(Application, pk=application_id, candidate__user=request.user)
    session = get_object_or_404(NegotiationSession, application=application)
    
    data = json.loads(request.body)
    user_msg = data.get('message', '').strip()
    
    if not user_msg: return JsonResponse({'error': 'Empty message'}, status=400)
    
    # 1. Update History
    session.chat_history.append({"role": "candidate", "text": user_msg})
    
    # 2. AI Reasoning
    # Fetch candidate performance context
    avg_score = (application.ai_score + 70) / 2 # Simple mock avg
    
    prompt = f"""
    Role: Senior Talent Closer (AI Agent).
    Context: Negotiating with {application.candidate.full_name} for {application.job.title}.
    Candidate Value Score: {avg_score}/100.
    Current Offer: ₹{session.current_salary_offer}
    Max Budget Ceiling: ₹{session.max_budget}
    
    Negotiation History:
    {json.dumps(session.chat_history[-5:])}
    
    Rules:
    1. Be professional, warm, but firm on company value.
    2. If the candidate asks for more, you can increase the offer by 5-10% ONLY IF their Value Score > 75.
    3. NEVER exceed the Max Budget Ceiling.
    4. If you reach the ceiling, offer "Non-monetary perks" (Remote work, 4-day week, Learning budget).
    
    Return JSON:
    {{
      "agent_response": "...",
      "new_offer_amount": 850000,
      "status": "OPEN/ACCEPTED/STALLED"
    }}
    """
    
    response_data = _gemini(prompt, {
        "agent_response": "I hear your concerns. Let me check what's possible.",
        "new_offer_amount": session.current_salary_offer,
        "status": "OPEN"
    })
    
    # 3. Update Session
    session.current_salary_offer = response_data.get('new_offer_amount', session.current_salary_offer)
    session.status = response_data.get('status', 'OPEN')
    session.chat_history.append({"role": "agent", "text": response_data.get('agent_response')})
    session.save()
    
    return JsonResponse({
        'agent_response': response_data.get('agent_response'),
        'current_offer': session.current_salary_offer,
        'status': session.status
    })
@login_required
def negotiation_sparring_practice(request, application_id):
    """Recruiter practice mode to spar against an AI candidate."""
    if not _recruiter_required(request): return redirect('dashboard')
    
    application = get_authorized_application(request, application_id)
    return render(request, 'jobs/negotiation_war_room.html', {
        'application': application
    })

@login_required
def process_sparring_msg(request, application_id):
    """AI Logic for the 'Practice Candidate' agent."""
    if not _recruiter_required(request): return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method != 'POST': return JsonResponse({'error': 'Invalid'}, status=400)
    
    application = get_authorized_application(request, application_id)
    data = json.loads(request.body)
    user_msg = data.get('message', '').strip()
    
    # 1. AI Reasoning for the Candidate Persona
    prompt = f"""
    Role: A highly talented but firm Software Engineer negotiating a job offer.
    Current Recruiter Message: "{user_msg}"
    Candidate Persona: {application.candidate.full_name}, specialized in {application.candidate.technical_skills}.
    
    Objective: 
    - Negotiate for a higher salary (target ₹28LPA).
    - React to the recruiter's persuasion tactics.
    - Provide a 'Persuasion Score' (0-100) for the recruiter's current message.
    
    Return JSON:
    {{
      "candidate_response": "...",
      "persuasion_increase": 15,
      "sentiment": "Skeptical/Interested/Annoyed",
      "insight": "Explain why the recruiter's tactic worked or failed."
    }}
    """
    
    response_data = _gemini(prompt, {
        "candidate_response": "I'm not sure that's enough.",
        "persuasion_increase": 5,
        "sentiment": "Skeptical",
        "insight": "The offer lacks a competitive edge."
    })
    
    return JsonResponse(response_data)

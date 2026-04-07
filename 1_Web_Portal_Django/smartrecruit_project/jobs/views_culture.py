import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Application
from .culture_sim_service import get_next_scenario, calculate_vibe_score

@login_required
def culture_fit_simulator(request, application_id):
    """
    Virtual Office Simulator: A behavioral assessment using branching narratives.
    """
    application = get_object_or_404(Application, id=application_id, candidate__user=request.user)
    
    # Store game state in session
    session_key = f'culture_sim_{application_id}'
    if 'reset' in request.GET or session_key not in request.session:
        request.session[session_key] = {'current_index': 0, 'responses': []}
        request.session.modified = True
    
    state = request.session[session_key]
    scenario = get_next_scenario(state['current_index'])
    
    if not scenario:
        # End of simulation -> Calculate final vibe
        vibe_score = calculate_vibe_score(state['responses'])
        # Save to application insights (hypothetically)
        return render(request, 'jobs/culture_sim_result.html', {
            'application': application,
            'vibe_score': vibe_score
        })

    return render(request, 'jobs/culture_simulator.html', {
        'application': application,
        'scenario': scenario,
        'progress': int((state['current_index'] / 2) * 100) # Assuming 2 scenarios for now
    })

@login_required
def submit_sim_response(request, application_id):
    if request.method == 'POST':
        session_key = f'culture_sim_{application_id}'
        state = request.session.get(session_key)
        
        data = json.loads(request.body)
        scenario_id = data.get('scenario_id')
        option_id = data.get('option_id')
        
        state['responses'].append({'scenario_id': scenario_id, 'option_id': option_id})
        state['current_index'] += 1
        request.session.modified = True
        
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid'}, status=400)
@login_required
def virtual_office_sim(request, application_id):
    """The Elite Project Singularity Virtual Office Simulator."""
    application = get_object_or_404(Application, id=application_id, candidate__user=request.user)
    return render(request, 'jobs/virtual_office_sim.html', {
        'application': application
    })

from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from .models import Application
from .views_advanced import _recruiter_required
from .velocity_service import calculate_performance_velocity

@login_required
def performance_velocity_report(request, application_id):
    """
    Recruiter tool for visualizing AI-predicted performance growth.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
        
    application = get_authorized_application(request, application_id)
    velocity_data = calculate_performance_velocity(application)
    
    return render(request, 'jobs/velocity_report.html', {
        'application': application,
        'velocity': velocity_data
    })

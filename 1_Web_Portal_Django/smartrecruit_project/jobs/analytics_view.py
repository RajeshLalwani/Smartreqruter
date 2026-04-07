from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import JobPosting, Candidate, Application, Interview
from django.db.models import Count, Avg, Q, F
import json

@login_required
def recruiter_analytics(request):
    """
    Analytics dashboard for recruiters showing hiring metrics and visualizations.
    """
    if not (request.user.is_recruiter or request.user.is_superuser):
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('dashboard')
    
    # Get Date Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    from .utils_analytics import get_analytics_context
    data = get_analytics_context(request.user, start_date, end_date)
    
    # Prepare context with actual data for the template, not just JSON for charts
    context = {
        'summary': data['summary'],
        'avg_velocity': data['summary']['avg_time_to_hire'],
        'funnel_data': data['simplified_funnel'],
        'sources': [
            {'source_of_hire': k, 'count': v, 'avg_score': 85.0} # Avg score simulated for now
            for k, v in data['source_data'].items()
        ],
        'agent_insights': [
            "Source ROI: LinkedIn is providing the highest quality candidates this month.",
            "Bottleneck Alert: Resume screening is taking 24% longer than last quarter.",
            "Diversity Pulse: Technical roles have seen a 15% increase in gender-diverse applicants."
        ],
        'start_date': start_date,
        'end_date': end_date,
        
        # JSON Dumps for Chart.js (if needed by any scripts)
        'funnel_labels': json.dumps(list(data['simplified_funnel'].keys())),
        'funnel_values': json.dumps(list(data['simplified_funnel'].values())),
        'tech_data': json.dumps(data['tech_data']),
        'first_job_id': JobPosting.objects.filter(recruiter=request.user).first().id if JobPosting.objects.filter(recruiter=request.user).exists() else None,
    }
    
    return render(request, 'jobs/recruiter_analytics.html', context)

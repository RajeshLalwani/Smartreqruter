from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Application, JobPosting, Assessment

# ============ ANALYTICS DASHBOARD ============
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
    
    # Get all applications for this recruiter's jobs
    applications = Application.objects.filter(job__recruiter=request.user)
    
    # 1. FUNNEL DATA - Count at each stage
    funnel_stages = {
        'APPLIED': 'Applied',
        'RESUME_SCREENING': 'Resume Screening',
        'RESUME_SELECTED': 'Resume Selected',
        'RESUME_REJECTED': 'Resume Rejected',
        'ROUND_1_PASSED': 'Round 1 Passed',
        'ROUND_1_FAILED': 'Round 1 Failed',
        'ROUND_2_PASSED': 'Round 2 Passed',
        'ROUND_2_FAILED': 'Round 2 Failed',
        'ROUND_3_PASSED': 'Round 3 Passed',
        'ROUND_3_FAILED': 'Round 3 Failed',
        'HR_ROUND_PENDING': 'HR Round Pending',
        'OFFER_GENERATED': 'Offer Generated',
        'OFFER_ACCEPTED': 'Hired',
        'OFFER_REJECTED': 'Offer Rejected',
        'REJECTED': 'Rejected',
    }
    
    funnel_data = applications.values('status').annotate(count=Count('id'))
    funnel_counts = {stage: 0 for stage in funnel_stages.keys()}
    for item in funnel_data:
        if item['status'] in funnel_counts:
            funnel_counts[item['status']] = item['count']
    
    # Simplified funnel for visualization (main stages only)
    simplified_funnel = {
        'Total Applications': applications.count(),
        'Resume Selected': funnel_counts.get('RESUME_SELECTED', 0),
        'Round 1 Passed': funnel_counts.get('ROUND_1_PASSED', 0),
        'Round 2 Passed': funnel_counts.get('ROUND_2_PASSED', 0),
        'Round 3 Passed': funnel_counts.get('ROUND_3_PASSED', 0),
        'Offer Generated': funnel_counts.get('OFFER_GENERATED', 0),
        'Hired': funnel_counts.get('OFFER_ACCEPTED', 0),
    }
    
    # 2. PASS RATES - Calculate percentage passing each round
    total_apps = applications.count()
    pass_rates = {}
    
    if total_apps > 0:
        # Resume pass rate
        resume_selected = funnel_counts.get('RESUME_SELECTED', 0)
        pass_rates['Resume Screening'] = round((resume_selected / total_apps) * 100, 1) if total_apps > 0 else 0
        
        # Round 1 pass rate (of those who took it)
        round1_total = funnel_counts.get('ROUND_1_PASSED', 0) + funnel_counts.get('ROUND_1_FAILED', 0)
        pass_rates['Round 1'] = round((funnel_counts.get('ROUND_1_PASSED', 0) / round1_total) * 100, 1) if round1_total > 0 else 0
        
        # Round 2 pass rate
        round2_total = funnel_counts.get('ROUND_2_PASSED', 0) + funnel_counts.get('ROUND_2_FAILED', 0)
        pass_rates['Round 2'] = round((funnel_counts.get('ROUND_2_PASSED', 0) / round2_total) * 100, 1) if round2_total > 0 else 0
        
        # Round 3 pass rate
        round3_total = funnel_counts.get('ROUND_3_PASSED', 0) + funnel_counts.get('ROUND_3_FAILED', 0)
        pass_rates['Round 3'] = round((funnel_counts.get('ROUND_3_PASSED', 0) / round3_total) * 100, 1) if round3_total > 0 else 0
        
        # HR/Offer rate
        offer_total = funnel_counts.get('OFFER_GENERATED', 0) + funnel_counts.get('REJECTED', 0)
        pass_rates['HR Round'] = round((funnel_counts.get('OFFER_GENERATED', 0) / offer_total) * 100, 1) if offer_total > 0 else 0
    
    # 3. AVERAGE SCORES - From Assessment model
    assessments = Assessment.objects.filter(application__job__recruiter=request.user)
    
    avg_scores = {
        'Aptitude': assessments.filter(test_type='APTITUDE').aggregate(avg=Avg('score'))['avg'] or 0,
        'Practical': assessments.filter(test_type='PRACTICAL').aggregate(avg=Avg('score'))['avg'] or 0,
    }
    avg_scores = {k: round(v, 1) for k, v in avg_scores.items()}
    
    # 4. TECHNOLOGY BREAKDOWN - Applications by tech stack
    tech_breakdown = applications.values('job__technology_stack').annotate(count=Count('id'))
    tech_data = {}
    for item in tech_breakdown:
        tech = item['job__technology_stack'] or 'GENERAL'
        tech_data[tech] = item['count']
    
    # 5. SUMMARY CARDS
    summary = {
        'total_applications': total_apps,
        'active_jobs': JobPosting.objects.filter(recruiter=request.user, status='OPEN').count(),
        'pending_reviews': applications.filter(status__in=['RESUME_SCREENING', 'ROUND_1_PASSED', 'ROUND_2_PASSED', 'ROUND_3_PASSED']).count(),
        'total_hired': funnel_counts.get('OFFER_ACCEPTED', 0),
    }
    
    context = {
        'summary': summary,
        'funnel_data': json.dumps(simplified_funnel),
        'pass_rates': json.dumps(pass_rates),
        'avg_scores': json.dumps(avg_scores),
        'tech_data': json.dumps(tech_data),
        'funnel_labels': json.dumps(list(simplified_funnel.keys())),
        'funnel_values': json.dumps(list(simplified_funnel.values())),
        'pass_rate_labels': json.dumps(list(pass_rates.keys())),
        'pass_rate_values': json.dumps(list(pass_rates.values())),
    }
    
    return render(request, 'jobs/recruiter_analytics.html', context)

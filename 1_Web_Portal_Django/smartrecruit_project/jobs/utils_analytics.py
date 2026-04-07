from django.db.models import Count, Avg, Q
from django.utils.dateparse import parse_date
from .models import JobPosting, Application, Assessment

def get_analytics_context(recruiter_user, start_date_str=None, end_date_str=None):
    """
    Aggregates analytics data for a recruiter, optionally filtering by date range.
    Returns a dictionary suitable for context or export.
    """
    # Base Queryset
    applications = Application.objects.filter(job__recruiter=recruiter_user)
    
    # Date Filtering
    if start_date_str:
        start_date = parse_date(start_date_str)
        if start_date:
            applications = applications.filter(applied_at__date__gte=start_date)
            
    if end_date_str:
        end_date = parse_date(end_date_str)
        if end_date:
            applications = applications.filter(applied_at__date__lte=end_date)

    # 1. FUNNEL DATA
    funnel_stages = [
        'RESUME_SELECTED', 'ROUND_1_PASSED', 'ROUND_2_PASSED',
        'ROUND_3_PASSED', 'OFFER_GENERATED', 'OFFER_ACCEPTED'
    ]
    funnel_counts = {stage: 0 for stage in funnel_stages}
    
    # Aggregate counts for all statuses
    status_counts = applications.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in status_counts}
    
    for stage in funnel_stages:
        funnel_counts[stage] = status_map.get(stage, 0)
        
    simplified_funnel = {
        'Total Applications': applications.count(),
        'Resume Selected': funnel_counts['RESUME_SELECTED'],
        'Round 1 Passed': funnel_counts['ROUND_1_PASSED'],
        'Round 2 Passed': funnel_counts['ROUND_2_PASSED'],
        'Round 3 Passed': funnel_counts['ROUND_3_PASSED'],
        'Offer Generated': funnel_counts['OFFER_GENERATED'],
        'Hired': status_map.get('OFFER_ACCEPTED', 0) + status_map.get('HIRED', 0),
    }

    # 2. PASS RATES
    total_apps = applications.count()
    pass_rates = {}
    if total_apps > 0:
        pass_rates['Resume Screening'] = round((funnel_counts['RESUME_SELECTED'] / total_apps) * 100, 1)
        
        # Round 1
        r1_total = funnel_counts['ROUND_1_PASSED'] + status_map.get('ROUND_1_FAILED', 0)
        pass_rates['Round 1'] = round((funnel_counts['ROUND_1_PASSED'] / r1_total) * 100, 1) if r1_total > 0 else 0
        
        # Round 2
        r2_total = funnel_counts['ROUND_2_PASSED'] + status_map.get('ROUND_2_FAILED', 0)
        pass_rates['Round 2'] = round((funnel_counts['ROUND_2_PASSED'] / r2_total) * 100, 1) if r2_total > 0 else 0
        
        # Round 3
        r3_total = funnel_counts['ROUND_3_PASSED'] + status_map.get('ROUND_3_FAILED', 0)
        pass_rates['Round 3'] = round((funnel_counts['ROUND_3_PASSED'] / r3_total) * 100, 1) if r3_total > 0 else 0
        
        # Offer
        offer_total = funnel_counts['OFFER_GENERATED'] + status_map.get('REJECTED', 0) # Approximation
        pass_rates['HR Round'] = round((funnel_counts['OFFER_GENERATED'] / offer_total) * 100, 1) if offer_total > 0 else 0

    # 3. AVERAGE SCORES
    assessments = Assessment.objects.filter(application__in=applications)
    avg_scores = {
        'Aptitude': assessments.filter(test_type='APTITUDE').aggregate(avg=Avg('score'))['avg'] or 0,
        'Practical': assessments.filter(test_type='PRACTICAL').aggregate(avg=Avg('score'))['avg'] or 0,
    }
    avg_scores = {k: round(v, 1) for k, v in avg_scores.items()}

    # 4. TECH BREAKDOWN
    tech_breakdown = applications.values('job__technology_stack').annotate(count=Count('id'))
    tech_data = {
        (item['job__technology_stack'] or 'GENERAL'): item['count'] 
        for item in tech_breakdown
    }

    # 5. TIME TO HIRE
    hired_apps = applications.filter(status__in=['OFFER_ACCEPTED', 'HIRED'])
    time_to_hire_days = []
    tth_dist = {'< 7 Days': 0, '1-2 Weeks': 0, '2-4 Weeks': 0, '1+ Month': 0}
    
    for app in hired_apps:
        delta = app.updated_at - app.applied_at
        days = delta.days
        time_to_hire_days.append(days)
        if days < 7: tth_dist['< 7 Days'] += 1
        elif days < 14: tth_dist['1-2 Weeks'] += 1
        elif days < 30: tth_dist['2-4 Weeks'] += 1
        else: tth_dist['1+ Month'] += 1
            
    avg_time_to_hire = round(sum(time_to_hire_days) / len(time_to_hire_days), 1) if time_to_hire_days else 0

    # 6. SOURCE & DEMOGRAPHICS
    source_data = {
        dict(Application.SOURCE_CHOICES).get(item['source_of_hire'], 'Other'): item['count']
        for item in applications.values('source_of_hire').annotate(count=Count('id'))
    }
    
    location_data = {
        item['candidate__current_location']: item['count']
        for item in applications.values('candidate__current_location').annotate(count=Count('id')).order_by('-count')[:5]
    }
    
    exp_dist = {'Entry (0-2y)': 0, 'Mid (3-5y)': 0, 'Senior (5-8y)': 0, 'Lead (8y+)': 0}
    for app in applications:
        exp = app.candidate.experience_years
        if exp <= 2: exp_dist['Entry (0-2y)'] += 1
        elif exp <= 5: exp_dist['Mid (3-5y)'] += 1
        elif exp <= 8: exp_dist['Senior (5-8y)'] += 1
        else: exp_dist['Lead (8y+)'] += 1

    # 7. AI PERFORMANCE
    from .models import ProctoringLog, Interview
    ai_metrics = {
        'total_violations': ProctoringLog.objects.filter(application__in=applications, log_type='VIOLATION').count(),
        'ai_audited_count': ProctoringLog.objects.filter(application__in=applications, details__contains='[DeepVision]').count(),
        'avg_interview_confidence': Interview.objects.filter(application__in=applications, interview_type='AI_BOT').aggregate(avg=Avg('ai_confidence_score'))['avg'] or 0
    }

    # SUMMARY
    summary = {
        'total_applications': total_apps,
        'active_jobs': JobPosting.objects.filter(recruiter=recruiter_user, status='OPEN').count(),
        'pending_reviews': applications.filter(status__in=['RESUME_SCREENING', 'ROUND_1_PASSED']).count(),
        'total_hired': simplified_funnel['Hired'],
        'avg_time_to_hire': avg_time_to_hire,
        'ai_efficiency': round(ai_metrics['avg_interview_confidence'], 1)
    }

    return {
        'summary': summary,
        'simplified_funnel': simplified_funnel,
        'pass_rates': pass_rates,
        'avg_scores': avg_scores,
        'tech_data': tech_data,
        'tth_dist': tth_dist,
        'source_data': source_data,
        'location_data': location_data,
        'exp_dist': exp_dist,
        'ai_metrics': ai_metrics,
        'filtered_count': total_apps
    }

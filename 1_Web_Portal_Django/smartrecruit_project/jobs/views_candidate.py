from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Candidate, Badge, Application
from core.utils.gamification import get_leaderboard_data

@login_required
def leaderboard_api(request):
    """
    API endpoint for the competitive leaderboard.
    """
    data = get_leaderboard_data()
    return JsonResponse({'leaderboard': data})

@login_required
def achievements_view(request):
    """
    Renders the candidate's personal 'Trophy Case'.
    """
    candidate = getattr(request.user, 'candidate_profile', None)
    if not candidate:
        return render(request, 'error.html', {'message': 'Candidate profile not found'})
    
    earned_badges = candidate.earned_badges.all()
    all_badges = Badge.objects.all()
    
    # Group by rarity for UI
    badges_by_rarity = {
        'LEGENDARY': earned_badges.filter(rarity='LEGENDARY'),
        'EPIC': earned_badges.filter(rarity='EPIC'),
        'RARE': earned_badges.filter(rarity='RARE'),
        'COMMON': earned_badges.filter(rarity='COMMON'),
    }
    
    context = {
        'candidate': candidate,
        'earned_badges': earned_badges,
        'badges_by_rarity': badges_by_rarity,
        'total_badges': all_badges.count(),
        'earned_count': earned_badges.count(),
    }
    return render(request, 'jobs/achievements.html', context)

@login_required
def candidate_profile_view(request):
    """
    Renders the candidate's professional profile / settings.
    """
    candidate, created = Candidate.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email
        }
    )
    
    if request.method == 'POST':
        pseudonym = request.POST.get('pseudonym')
        if pseudonym:
            candidate.pseudonym = pseudonym
            candidate.save()
            messages.success(request, f"Identity updated to {pseudonym}!")
            
    return render(request, 'jobs/candidate_profile.html', {'profile': candidate})

@login_required
def candidate_applications_view(request):
    """
    Shows all applications for the current candidate.
    """
    candidate = getattr(request.user, 'candidate_profile', None)
    applications = []
    if candidate:
        applications = Application.objects.filter(candidate=candidate).order_by('-applied_at')
    return render(request, 'jobs/my_applications.html', {'applications': applications})

@login_required
def candidate_skills_api(request):
    """
    Returns candidate skills as JSON.
    """
    candidate = getattr(request.user, 'candidate_profile', None)
    skills = candidate.skills_list if candidate else []
    return JsonResponse({'skills': skills})

@login_required
def candidate_statistics_api(request):
    """
    Returns candidate activity stats.
    """
    candidate = getattr(request.user, 'candidate_profile', None)
    stats = {
        'badges': candidate.earned_badges.count() if candidate else 0,
        'apps': Application.objects.filter(candidate=candidate).count() if candidate else 0
    }
    return JsonResponse(stats)

@login_required
def take_mock_test(request):
    """
    Redirects to practice arena.
    """
    return redirect('coding_arena')

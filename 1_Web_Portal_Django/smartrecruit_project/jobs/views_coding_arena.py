"""
Coding Practice Arena Views — SmartRecruit
──────────────────────────────────────────────────────
Features:
  - Challenge list with filters (category, difficulty, status)
  - Challenge solve page with Monaco code editor
  - Code execution via Piston API (free, no auth required)
  - AI hint generation via Gemini
  - XP and gamification tracking
  - Leaderboard
"""

import json
import time
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Q

from .models import CodingChallenge, CodingSubmission, CandidateXP, Candidate

import logging
logger = logging.getLogger(__name__)


PISTON_API  = 'https://emkc.org/api/v2/piston/execute'
PISTON_LANGS = {
    'python':     {'language': 'python',  'version': '3.10.0'},
    'javascript': {'language': 'js',      'version': '18.15.0'},
    'java':       {'language': 'java',    'version': '15.0.2'},
    'cpp':        {'language': 'cpp',     'version': '10.2.0'},
    'sql':        {'language': 'sqlite3', 'version': '3.36.0'},
}


def _get_or_create_xp(user):
    xp, _ = CandidateXP.objects.get_or_create(user=user)
    return xp


def _award_xp(user, challenge, status, hints_used):
    """Award XP based on solve outcome."""
    xp_obj = _get_or_create_xp(user)
    earned = 0

    if status == 'ACCEPTED':
        base = challenge.xp_reward
        hint_penalty = hints_used * 10
        earned = max(base - hint_penalty, base // 4)  # Min 25% of base XP
        xp_obj.total_xp += earned
        xp_obj.problems_solved += 1

        # Streak logic
        today = timezone.now().date()
        if xp_obj.last_active:
            delta = (today - xp_obj.last_active).days
            if delta == 1:
                xp_obj.streak_days += 1
            elif delta > 1:
                xp_obj.streak_days = 1
        else:
            xp_obj.streak_days = 1
        xp_obj.last_active = today

        # Badges
        badges = xp_obj.badges or []
        if xp_obj.problems_solved == 1 and 'first_solve' not in badges:
            badges.append('first_solve')
        if xp_obj.streak_days >= 3 and 'streak_3' not in badges:
            badges.append('streak_3')
        if xp_obj.total_xp >= 300 and 'learner' not in badges:
            badges.append('learner')
        if challenge.difficulty == 'hard' and 'hard_solver' not in badges:
            badges.append('hard_solver')
        xp_obj.badges = badges

    elif status == 'PARTIAL':
        earned = challenge.xp_reward // 4

    xp_obj.save()

    # 🔗 Trigger Advanced Badge Logic
    try:
        from core.utils.gamification import award_badge
        candidate = user.candidate_profile
        if status == 'ACCEPTED':
            # Speed Demon (Under 100ms runtime for practice, or simple logic)
            # In actual assessments, we track total completion time
            if challenge.difficulty == 'hard' and 'hard_solver' not in (xp_obj.badges or []):
                award_badge(candidate, "Logic Master")
    except Exception as e:
        logger.error(f"[Gamification] Badge awarding failed: {e}")

    return earned


# ─── Views ──────────────────────────────────────────────────────

@login_required
def coding_arena(request):
    """Main coding challenge list/lobby page."""
    challenges = CodingChallenge.objects.filter(is_active=True)

    # Filters
    category   = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    search     = request.GET.get('q', '')

    if category:
        challenges = challenges.filter(category=category)
    if difficulty:
        challenges = challenges.filter(difficulty=difficulty)
    if search:
        challenges = challenges.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Which have the user already solved?
    solved_slugs = set(
        CodingSubmission.objects.filter(
            user=request.user, status='ACCEPTED'
        ).values_list('challenge__slug', flat=True)
    )

    # XP profile
    xp_obj = _get_or_create_xp(request.user)

    # Category counts
    category_counts = CodingChallenge.objects.filter(is_active=True).values(
        'category'
    ).annotate(count=Count('id'))

    # Stats
    total      = CodingChallenge.objects.filter(is_active=True).count()
    easy_count = CodingChallenge.objects.filter(is_active=True, difficulty='easy').count()
    med_count  = CodingChallenge.objects.filter(is_active=True, difficulty='medium').count()
    hard_count = CodingChallenge.objects.filter(is_active=True, difficulty='hard').count()

    context = {
        'challenges':      challenges,
        'solved_slugs':    solved_slugs,
        'xp':              xp_obj,
        'xp_level':        xp_obj.level,
        'category_counts': {c['category']: c['count'] for c in category_counts},
        'categories':      CodingChallenge.CATEGORY_CHOICES,
        'selected_cat':    category,
        'selected_diff':   difficulty,
        'search':          search,
        'stats': {
            'total': total, 'easy': easy_count,
            'medium': med_count, 'hard': hard_count,
            'solved': len(solved_slugs),
        },
    }
    return render(request, 'jobs/coding_arena.html', context)


@login_required
def coding_challenge_solve(request, slug):
    """Individual challenge solve page with Monaco editor."""
    challenge = get_object_or_404(CodingChallenge, slug=slug, is_active=True)

    # Previous submissions by this user
    my_submissions_full = CodingSubmission.objects.filter(
        user=request.user, challenge=challenge
    ).order_by('-submitted_at')
    
    is_solved = my_submissions_full.filter(status='ACCEPTED').exists()
    my_submissions = my_submissions_full[:10]

    # Default language
    lang = request.GET.get('lang', 'python')
    
    # Robust starter code extraction
    starter_codes = challenge.starter_code
    if isinstance(starter_codes, str):
        try:
            starter_codes = json.loads(starter_codes)
        except json.JSONDecodeError:
            starter_codes = {}
            
    starter = starter_codes.get(lang, '# Write your solution here\n') if isinstance(starter_codes, dict) else '# Write your solution here\n'

    xp_obj = _get_or_create_xp(request.user)

    # All challenges for navigation
    all_challenges = list(CodingChallenge.objects.filter(is_active=True).values('slug', 'title', 'difficulty'))
    current_idx = next((i for i, c in enumerate(all_challenges) if c['slug'] == slug), 0)
    prev_ch = all_challenges[current_idx - 1] if current_idx > 0 else None
    next_ch = all_challenges[current_idx + 1] if current_idx < len(all_challenges) - 1 else None

    context = {
        'challenge':      challenge,
        'starter_code':   json.dumps(starter_codes),
        'my_submissions': my_submissions,
        'is_solved':      is_solved,
        'selected_lang':  lang,
        'xp':             xp_obj,
        'xp_level':       xp_obj.level,
        'prev_challenge': prev_ch,
        'next_challenge': next_ch,
        'hints_json':     json.dumps(challenge.hints or []),
        'examples_json':  json.dumps(challenge.examples or []),
    }
    return render(request, 'jobs/coding_solve.html', context)


@login_required
def execute_code(request):
    """
    API endpoint: executes user code via Piston API and returns results.
    POST body: { code, language, challenge_slug, hints_used }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    code     = body.get('code', '')
    language = body.get('language', 'python')
    slug     = body.get('challenge_slug', '')
    try:
        hints_used = int(body.get('hints_used', 0) or 0)
    except (ValueError, TypeError):
        hints_used = 0

    if not code.strip():
        return JsonResponse({'error': 'No code provided'}, status=400)

    challenge = get_object_or_404(CodingChallenge, slug=slug) if slug else None

    # ── Execute via Modular Sandbox ──────────────────────────────
    from core.utils.code_runner import execute_code as run_sandbox_code
    start_ms = int(time.time() * 1000)

    exec_result = run_sandbox_code(source_code=code, language=language)
    
    stdout = exec_result.get('stdout', '')
    stderr = exec_result.get('stderr', '')
    base_status = exec_result.get('status', 'ERROR')
    
    # Adapt to view's expected format
    if base_status == 'TIMEOUT':
        return JsonResponse({
            'status': 'TIMEOUT',
            'stdout': stdout,
            'stderr': stderr or 'Code execution timed out',
            'runtime_ms': 5000,
        })
    elif base_status == 'ERROR':
        return JsonResponse({
            'status': 'ERROR',
            'stdout': stdout,
            'stderr': stderr or 'Execution service error',
            'runtime_ms': 0,
        })
    
    exit_code = 0 if base_status in ['ACCEPTED', 'WRONG_ANSWER'] else 1

    runtime_ms = int(time.time() * 1000) - start_ms

    # ── Determine Status ─────────────────────────────────────────
    if exit_code != 0 or stderr:
        status = 'ERROR'
    elif challenge:
        # Run basic test case checks (compare output with expected)
        test_results = []
        passed = 0
        for tc in (challenge.test_cases or []):
            expected = str(tc.get('expected', '') or '').strip().lower()
            actual   = str(stdout or '').lower()
            ok = expected in actual or actual == expected
            test_results.append({'passed': ok, 'expected': expected})
            if ok: passed += 1
        total_tests = len(test_results)
        if total_tests == 0:
            status = 'ACCEPTED'
        elif passed == total_tests:
            status = 'ACCEPTED'
        elif passed > 0:
            status = 'PARTIAL'
        else:
            status = 'WRONG'
    else:
        status = 'ACCEPTED' if exit_code == 0 else 'ERROR'
        test_results = []
        passed = 0
        total_tests = 0

    # ── Save Submission ──────────────────────────────────────────
    xp_earned = 0
    if challenge:
        submission = CodingSubmission.objects.create(
            user=request.user,
            challenge=challenge,
            language=language,
            code=code,
            status=status,
            runtime_ms=runtime_ms,
            test_results=test_results,
            hints_used=hints_used,
            xp_earned=0,
        )
        xp_earned = _award_xp(request.user, challenge, status, hints_used)
        submission.xp_earned = xp_earned
        submission.save()

    return JsonResponse({
        'status':      status,
        'stdout':      stdout[:3000],
        'stderr':      stderr[:2000],
        'runtime_ms':  runtime_ms,
        'xp_earned':   xp_earned,
        'passed':      passed if challenge else None,
        'total_tests': total_tests if challenge else None,
    })


@login_required
def get_ai_hint(request):
    """Generate an AI hint using Gemini for the current challenge."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    slug  = body.get('slug', '')
    level = int(body.get('hint_level', 0))
    code  = body.get('code', '')

    challenge = get_object_or_404(CodingChallenge, slug=slug)

    # Use pre-defined hints first (3 levels), then generate with Gemini
    builtin_hints = challenge.hints or []
    if level < len(builtin_hints):
        return JsonResponse({'hint': builtin_hints[level], 'source': 'builtin'})

    # Generate via AIEngine
    try:
        from core.ai_engine import AIEngine
        ai = AIEngine()

        prompt = f"""You are a coding tutor helping a student solve this problem:

Problem: {challenge.title}
Description: {challenge.description[:500]}

The student's current code:
```
{code[:800] if code else 'Not started yet'}
```

Give a helpful but non-spoiling hint. Keep it to 2-3 sentences maximum. Don't give the full solution."""

        hint = ai.generate(prompt=prompt).strip()
    except Exception as e:
        hint = "Think about breaking the problem into smaller sub-problems and solving each one step by step."

    return JsonResponse({'hint': hint, 'source': 'ai'})


@login_required
def coding_leaderboard(request):
    """Global leaderboard of top coders by XP (Pseudonymized)."""
    top_xp = CandidateXP.objects.select_related('user', 'user__candidate_profile').order_by('-total_xp')[:20]

    # My rank
    all_ids = list(CandidateXP.objects.order_by('-total_xp').values_list('user_id', flat=True))
    my_rank = (all_ids.index(request.user.id) + 1) if request.user.id in all_ids else None
    my_xp = _get_or_create_xp(request.user)

    # Pseudonymization helper (e.g. CodeNinja_42)
    leaderboard_data = []
    for entry in top_xp:
        pseudo = f"Lvl.{entry.level} Coder-{entry.user.id}"
        if entry.user == request.user:
            pseudo = "You"
            
        leaderboard_data.append({
            'rank': all_ids.index(entry.user_id) + 1,
            'name': pseudo,
            'xp': entry.total_xp,
            'badges_count': entry.user.candidate_profile.earned_badges.count() if hasattr(entry.user, 'candidate_profile') else 0,
            'is_me': entry.user == request.user
        })

    context = {
        'leaderboard': leaderboard_data,
        'my_rank':   my_rank,
        'my_xp':     my_xp,
        'xp_level':  my_xp.level,
    }
    return render(request, 'jobs/coding_leaderboard.html', context)

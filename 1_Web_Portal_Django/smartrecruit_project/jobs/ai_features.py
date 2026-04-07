"""
AI Features Module for SmartRecruit
────────────────────────────────────────────────────────
1. Skill Gap Analysis Engine
2. Predictive Hiring Score (Composite ML-style weighted model)
3. Candidate Intelligence Report Builder
4. Trend Analysis & Insights Generator
"""

import json
import re


# ─────────────────────────────────────────────────────────────────
# 1. SKILL GAP ANALYSIS ENGINE
# ─────────────────────────────────────────────────────────────────

SKILL_SYNONYMS = {
    'ml': ['machine learning', 'ml', 'scikit-learn', 'sklearn'],
    'dl': ['deep learning', 'dl', 'neural network', 'tensorflow', 'pytorch', 'keras'],
    'python': ['python', 'python3', 'py'],
    'sql': ['sql', 'mysql', 'postgresql', 'sqlite', 'database', 'rdbms'],
    'nlp': ['nlp', 'natural language processing', 'bert', 'gpt', 'transformer', 'huggingface'],
    'cv': ['computer vision', 'opencv', 'image processing', 'cnn', 'yolo'],
    'data': ['data analysis', 'data science', 'pandas', 'numpy', 'matplotlib', 'seaborn'],
    'docker': ['docker', 'containerization', 'kubernetes', 'k8s'],
    'cloud': ['aws', 'azure', 'gcp', 'cloud computing', 'cloud'],
    'api': ['api', 'rest api', 'restful', 'fastapi', 'django rest', 'drf'],
    'js': ['javascript', 'js', 'node.js', 'nodejs', 'typescript'],
    'react': ['react', 'reactjs', 'react.js'],
    'django': ['django', 'django rest framework', 'drf'],
    'git': ['git', 'github', 'gitlab', 'version control'],
}

SKILL_CATEGORIES = {
    'Programming Languages': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'kotlin', 'swift'],
    'Data Science & ML': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'nlp', 'computer vision', 'data analysis', 'pandas', 'numpy'],
    'Databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra'],
    'Cloud & DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd', 'terraform', 'jenkins'],
    'Web Frameworks': ['django', 'flask', 'fastapi', 'react', 'angular', 'vue', 'node.js', 'spring'],
    'Tools & Version Control': ['git', 'github', 'jira', 'agile', 'scrum'],
}

SKILL_IMPORTANCE = {
    'machine learning': 9,
    'deep learning': 9,
    'python': 8,
    'tensorflow': 8.5,
    'pytorch': 8.5,
    'sql': 7,
    'docker': 7.5,
    'aws': 7.5,
    'nlp': 9,
    'computer vision': 8,
    'data analysis': 8,
    'react': 7,
    'django': 7,
    'git': 6,
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill string to lowercase, stripped."""
    return skill.strip().lower()


def expand_skill_synonyms(skills: list) -> set:
    """Expand a list of skills using synonyms for fuzzy matching."""
    expanded = set()
    for skill in skills:
        norm = normalize_skill(skill)
        expanded.add(norm)
        for key, synonyms in SKILL_SYNONYMS.items():
            if norm in synonyms:
                expanded.update(synonyms)
    return expanded


def get_skill_gap_analysis(job, candidate_skills_raw: str) -> dict:
    """
    Full skill gap analysis between a job posting and a candidate.
    
    Returns:
        {
            matched_skills: [...],
            missing_skills: [...],
            extra_skills: [...],
            match_percentage: float,
            skill_breakdown: {category: {matched, missing}},
            recommendations: [...],
            importance_weighted_score: float,
        }
    """
    # Parse skills
    job_skills = [normalize_skill(s) for s in job.required_skills.split(',') if s.strip()]
    candidate_skills = [normalize_skill(s) for s in candidate_skills_raw.split(',') if s.strip()]
    
    # Expand synonyms
    job_skills_expanded = expand_skill_synonyms(job_skills)
    candidate_skills_expanded = expand_skill_synonyms(candidate_skills)
    
    # Match calculation
    matched = []
    missing = []
    
    for skill in job_skills:
        # Check exact or synonym match
        skill_synonyms = set([skill])
        for key, synonyms in SKILL_SYNONYMS.items():
            if skill in synonyms:
                skill_synonyms.update(synonyms)
        
        if skill_synonyms & candidate_skills_expanded:
            matched.append(skill)
        else:
            missing.append(skill)
    
    # Extra skills (candidate has but job doesn't require)
    extra = []
    for skill in candidate_skills:
        is_required = False
        for js in job_skills:
            job_syns = set([js])
            for key, synonyms in SKILL_SYNONYMS.items():
                if js in synonyms:
                    job_syns.update(synonyms)
            if skill in job_syns or js in expand_skill_synonyms([skill]):
                is_required = True
                break
        if not is_required:
            extra.append(skill)
    
    # Match percentage
    total_required = len(job_skills)
    match_pct = round((len(matched) / max(total_required, 1)) * 100, 1)
    
    # Importance-weighted score
    total_importance = 0
    matched_importance = 0
    for skill in job_skills:
        importance = SKILL_IMPORTANCE.get(skill, 5)
        total_importance += importance
        if skill in matched:
            matched_importance += importance
    
    importance_score = round((matched_importance / max(total_importance, 1)) * 100, 1) if total_importance > 0 else match_pct
    
    # Category breakdown
    skill_breakdown = {}
    for category, cat_skills in SKILL_CATEGORIES.items():
        cat_matched = [s for s in matched if any(cs in s or s in cs for cs in cat_skills)]
        cat_missing = [s for s in missing if any(cs in s or s in cs for cs in cat_skills)]
        if cat_matched or cat_missing:
            skill_breakdown[category] = {
                'matched': cat_matched,
                'missing': cat_missing,
                'match_rate': round(len(cat_matched) / max(len(cat_matched) + len(cat_missing), 1) * 100)
            }
    
    # Recommendations
    recommendations = []
    if len(missing) > 0:
        top_missing = missing[:3]
        recommendations.append(f"Focus on developing: {', '.join(top_missing)}")
    if match_pct >= 80:
        recommendations.append("Strong candidate — consider prioritizing for interviews.")
    elif match_pct >= 60:
        recommendations.append("Decent match — verify key skills during interview.")
    else:
        recommendations.append("Significant skill gaps — may need training or is a stretch hire.")
    
    # Add DS/AI specific recommendations
    ml_skills = ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn']
    missing_ml = [s for s in missing if any(ml in s for ml in ml_skills)]
    if missing_ml:
        recommendations.append(f"Critical AI/ML skills missing: {', '.join(missing_ml)}")
    
    return {
        'matched_skills': matched,
        'missing_skills': missing,
        'extra_skills': extra[:10],  # Limit to 10 extras
        'match_percentage': match_pct,
        'importance_weighted_score': importance_score,
        'skill_breakdown': skill_breakdown,
        'recommendations': recommendations,
        'total_required': total_required,
        'total_matched': len(matched),
    }


# ─────────────────────────────────────────────────────────────────
# 2. PREDICTIVE HIRING SCORE (Composite Weighted Model)
# ─────────────────────────────────────────────────────────────────

STAGE_WEIGHTS = {
    'resume_match':       0.20,  # AI resume score
    'aptitude_score':     0.20,  # Round 1
    'practical_score':    0.25,  # Round 2
    'ai_interview_score': 0.25,  # Round 3
    'skill_gap_score':    0.10,  # Skill gap analysis
}

HIRING_STAGES_ORDER = [
    'APPLIED', 'RESUME_SCREENING', 'RESUME_SELECTED',
    'ROUND_1_PENDING', 'ROUND_1_PASSED',
    'ROUND_2_PENDING', 'ROUND_2_PASSED',
    'ROUND_3_PENDING', 'ROUND_3_PASSED',
    'HR_ROUND_PENDING', 'OFFER_GENERATED', 'OFFER_ACCEPTED', 'HIRED'
]


def calculate_predictive_hiring_score(application) -> dict:
    """
    Composite "Likelihood to be Hired" score (0–100) based on:
    - Resume AI Match (20%)
    - Aptitude Score (20%)
    - Practical/Coding Score (25%)
    - AI Interview Confidence (25%)
    - Skill Gap Match (10%)
    
    Returns augmented score details.
    """
    from .models import Assessment, Interview

    scores = {}
    raw_components = {}

    # Resume Match Score
    resume_score = float(application.ai_score or 0)
    scores['resume_match'] = resume_score
    raw_components['Resume AI Match'] = {'score': resume_score, 'weight': '20%', 'out_of': 100}

    # Round 1: Aptitude
    aptitude = Assessment.objects.filter(application=application, test_type='APTITUDE').last()
    apt_score = float(aptitude.score) if aptitude else None
    scores['aptitude_score'] = apt_score or 0
    raw_components['Aptitude Test (R1)'] = {
        'score': apt_score,
        'weight': '20%',
        'out_of': 100,
        'passed': aptitude.passed if aptitude else None
    }

    # Round 2: Practical
    practical = Assessment.objects.filter(application=application, test_type='PRACTICAL').last()
    prac_score = float(practical.score) if practical else None
    scores['practical_score'] = prac_score or 0
    raw_components['Coding Test (R2)'] = {
        'score': prac_score,
        'weight': '25%',
        'out_of': 100,
        'passed': practical.passed if practical else None
    }

    # Round 3: AI Interview
    ai_interview = Interview.objects.filter(application=application, interview_type='AI_BOT', status='COMPLETED').last()
    ai_score = float(ai_interview.ai_confidence_score) if ai_interview else None
    scores['ai_interview_score'] = ai_score or 0
    raw_components['AI Interview (R3)'] = {
        'score': ai_score,
        'weight': '25%',
        'out_of': 100
    }

    # Skill Gap Score
    candidate_skills = application.candidate.skills_extracted or ''
    skill_data = get_skill_gap_analysis(application.job, candidate_skills)
    gap_score = skill_data['importance_weighted_score']
    scores['skill_gap_score'] = gap_score
    raw_components['Skill Gap Match'] = {
        'score': round(gap_score),
        'weight': '10%',
        'out_of': 100,
        'details': f"{skill_data['total_matched']}/{skill_data['total_required']} skills matched"
    }

    # Compute weighted score (only from available stages)
    available_weight = 0
    weighted_sum = 0
    for key, weight in STAGE_WEIGHTS.items():
        val = scores.get(key, 0)
        if val > 0 or key == 'resume_match':  # Always include resume
            weighted_sum += val * weight
            available_weight += weight

    composite_score = round(weighted_sum / max(available_weight, 0.01), 1)

    # Stage progress bonus (+2 per stage beyond APPLIED)
    try:
        stage_idx = HIRING_STAGES_ORDER.index(application.status)
    except ValueError:
        stage_idx = 0
    stage_bonus = min(stage_idx * 2, 10)  # Cap at 10 bonus points
    composite_score = min(composite_score + stage_bonus, 99)  # Never show 100% unless hired

    # Hiring likelihood label
    if composite_score >= 80:
        likelihood = 'Very High'
        likelihood_color = 'success'
        likelihood_icon = 'fas fa-star'
    elif composite_score >= 65:
        likelihood = 'High'
        likelihood_color = 'info'
        likelihood_icon = 'fas fa-thumbs-up'
    elif composite_score >= 50:
        likelihood = 'Moderate'
        likelihood_color = 'warning'
        likelihood_icon = 'fas fa-balance-scale'
    elif composite_score >= 35:
        likelihood = 'Low'
        likelihood_color = 'warning text-dark'
        likelihood_icon = 'fas fa-exclamation-triangle'
    else:
        likelihood = 'Very Low'
        likelihood_color = 'danger'
        likelihood_icon = 'fas fa-times-circle'

    return {
        'composite_score': composite_score,
        'likelihood': likelihood,
        'likelihood_color': likelihood_color,
        'likelihood_icon': likelihood_icon,
        'components': raw_components,
        'skill_analysis': skill_data,
        'stage_bonus': stage_bonus,
    }


# ─────────────────────────────────────────────────────────────────
# 3. TREND ANALYSIS: APPLICATIONS OVER TIME
# ─────────────────────────────────────────────────────────────────

def get_application_trend(applications, days: int = 30) -> dict:
    """
    Returns application count grouped by day for the last `days` days.
    Used for line/area charts in analytics.
    """
    from django.utils import timezone
    from collections import defaultdict

    now = timezone.now()
    start = now - __import__('datetime').timedelta(days=days)
    recent = applications.filter(applied_at__gte=start)

    daily = defaultdict(int)
    for app in recent:
        date_key = app.applied_at.strftime('%b %d')
        daily[date_key] += 1

    # Build sequential list for last `days` days
    labels = []
    values = []
    for i in range(days - 1, -1, -1):
        d = now - __import__('datetime').timedelta(days=i)
        label = d.strftime('%b %d')
        labels.append(label)
        values.append(daily.get(label, 0))

    return {'labels': labels, 'values': values}


def get_score_distribution(applications) -> dict:
    """
    Get distribution of AI resume scores (histogram bins).
    """
    bins = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for app in applications:
        score = float(app.ai_score or 0)
        if score <= 20:
            bins['0-20'] += 1
        elif score <= 40:
            bins['21-40'] += 1
        elif score <= 60:
            bins['41-60'] += 1
        elif score <= 80:
            bins['61-80'] += 1
        else:
            bins['81-100'] += 1
    return bins


def get_top_candidates_ranking(job, applications, limit=10) -> list:
    """
    Rank candidates by composite predictive score.
    Returns sorted list with score details.
    """
    rankings = []
    for app in applications:
        try:
            score_data = calculate_predictive_hiring_score(app)
            rankings.append({
                'application': app,
                'composite_score': score_data['composite_score'],
                'likelihood': score_data['likelihood'],
                'likelihood_color': score_data['likelihood_color'],
            })
        except Exception:
            continue

    return sorted(rankings, key=lambda x: x['composite_score'], reverse=True)[:limit]

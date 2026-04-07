"""
Custom template tags and filters for SmartRecruit
"""

from django import template
import ast

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary in templates
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def percentage(value):
    """
    Convert a decimal to percentage
    Usage: {{ 0.75|percentage }} -> 75%
    """
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter
def match_color(score):
    """
    Return Bootstrap color class based on match score
    Usage: {{ score|match_color }}
    """
    try:
        score = float(score)
        if score >= 70:
            return "success"
        elif score >= 50:
            return "warning"
        else:
            return "danger"
    except (ValueError, TypeError):
        return "secondary"


@register.filter
def status_badge(status):
    """
    Return Bootstrap badge class for application status
    """
    status_map = {
        'APPLIED': 'info',
        'RESUME_SCREENING': 'secondary',
        'RESUME_SELECTED': 'info',
        'RESUME_REJECTED': 'danger',
        'ROUND_1_PENDING': 'warning',
        'ROUND_1_PASSED': 'primary',
        'ROUND_1_FAILED': 'danger',
        'ROUND_2_PENDING': 'warning',
        'ROUND_2_PASSED': 'primary',
        'ROUND_2_FAILED': 'danger',
        'ROUND_3_PENDING': 'warning',
        'ROUND_3_PASSED': 'success',
        'ROUND_3_FAILED': 'danger',
        'HR_ROUND_PENDING': 'warning',
        'OFFER_GENERATED': 'success',
        'OFFER_ACCEPTED': 'success',
        'OFFER_REJECTED': 'danger',
        'HIRED': 'success',
        'REJECTED': 'danger',
    }
    return status_map.get(status, 'secondary')


@register.filter
def truncate_words_custom(value, arg):
    """
    Truncate text to specified number of words
    Usage: {{ text|truncate_words_custom:20 }}
    """
    try:
        words = value.split()
        if len(words) > int(arg):
            return ' '.join(words[:int(arg)]) + '...'
        return value
    except (ValueError, TypeError, AttributeError):
        return value


@register.simple_tag
def query_transform(request, **kwargs):
    """
    Update query parameters while preserving existing ones
    Usage: {% query_transform page=2 %}
    """
    updated = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, None)
    return updated.urlencode()


@register.filter
def get_progress_step(status):
    """
    Maps application status to a progress step (1-7)
    """
    steps = {
        'APPLIED': 1,
        'RESUME_SCREENING': 2, 'RESUME_SELECTED': 2, 'RESUME_REJECTED': 2,
        'ROUND_1_PENDING': 3, 'ROUND_1_PASSED': 3, 'ROUND_1_FAILED': 3,
        'ROUND_2_PENDING': 4, 'ROUND_2_PASSED': 4, 'ROUND_2_FAILED': 4,
        'ROUND_3_PENDING': 5, 'ROUND_3_PASSED': 5, 'ROUND_3_FAILED': 5,
        'HR_ROUND_PENDING': 6, 'HR_ROUND_PASSED': 6,
        'OFFER_GENERATED': 7, 'OFFER_ACCEPTED': 7, 'OFFER_REJECTED': 7, 'HIRED': 7,
        'REJECTED': 0 # Special case
    }
    return steps.get(status, 1)


@register.filter
def get_skill_analysis(application):
    """
    Analyzes skills match between candidate and job.
    Returns a dict: {'matched': [], 'missing': []}
    """
    try:
        # Job skills
        if not application.job.required_skills:
            return {'matched': [], 'missing': []}
            
        job_skills = [s.strip().lower() for s in application.job.required_skills.split(',') if s.strip()]
        
        # Candidate skills
        candidate_skills_raw = application.candidate.skills_extracted
        candidate_skills = []
        
        try:
            # Try parsing as list string ['Skill']
            parsed = ast.literal_eval(candidate_skills_raw)
            if isinstance(parsed, list):
                candidate_skills = [str(s).lower().strip() for s in parsed]
            else:
                 candidate_skills = [s.lower().strip() for s in str(candidate_skills_raw).split(',')]
        except Exception:
             # Fallback
             candidate_skills = [s.lower().strip() for s in candidate_skills_raw.split(',') if s.strip()]

        candidate_skills_norm = set(candidate_skills)
        
        img_matched = []
        img_missing = []
        
        for skill in job_skills:
            if skill in candidate_skills_norm:
                img_matched.append(skill.title())
            else:
                img_missing.append(skill.title())
                
        return {
            'matched': img_matched,
            'missing': img_missing
        }
    except Exception as e:
        return {'matched': [], 'missing': [], 'error': str(e)}

@register.simple_tag(takes_context=True)
def setvar(context, key, val):
    """
    Sets a variable in the template context statically.
    Usage: {% setvar 'glow_class' 'border-purple' %}
    """
    context[key] = val
    return ''
@register.filter
def replace(value, arg):
    """
    Replace characters in a string
    Usage: {{ value|replace:"_, " }}
    """
    if value is None:
        return ""
    try:
        old, new = arg.split(',')
        return str(value).replace(old, new)
    except (ValueError, TypeError):
        return value

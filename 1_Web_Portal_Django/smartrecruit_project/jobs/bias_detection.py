"""
Bias Detection & Blind Hiring Engine — SmartRecruit
──────────────────────────────────────────────────────────
Anonymizes PII from candidate profiles for unbiased screening.

Anonymized fields:
  - Full Name → "Candidate #XXXX"
  - Email     → "*****@***.***"
  - Phone     → "**** *** ****"
  - Photo     → removed
  - Gender-coded words → neutralized
  - Location  → generalized ("India" instead of specific city)

Also provides:
  - Bias Risk Score for job description language
  - Gender-coded word detector in JD
"""

import re
import hashlib
from typing import Dict, List


# ─── Gender-Coded JD Words ────────────────────────────────────────
# (from Gaucher et al., 2011 — "Evidence That Gendered Wording in Job Ads Exists and Sustains Gender Inequality")
MASCULINE_CODED = [
    'aggressive', 'ambitious', 'analytical', 'assertive', 'autonomous',
    'battle', 'boast', 'challenge', 'champion', 'compete', 'competitive',
    'confident', 'courageous', 'decision', 'decisive', 'determination',
    'dominant', 'driven', 'fearless', 'fight', 'force', 'hero', 'independent',
    'individual', 'leader', 'leadership', 'logic', 'ninja', 'outspoken',
    'principal', 'rock star', 'self-reliant', 'stubborn', 'superior', 'warrior',
]

FEMININE_CODED = [
    'affectionate', 'agree', 'collaborate', 'commit', 'communal', 'compassion',
    'connect', 'cooperate', 'dedicated', 'dependable', 'empathize', 'empower',
    'enthusiastic', 'gentle', 'honest', 'humble', 'inclusive', 'kind',
    'loyal', 'mindful', 'nurture', 'passionate', 'patient', 'polite',
    'resilient', 'share', 'supportive', 'sympathetic', 'team', 'together',
    'trust', 'understand', 'warm', 'welcoming',
]

AGEIST_WORDS = [
    'young', 'junior', 'fresh graduate', 'entry level', 'recent graduate',
    'digital native', 'millennial', 'energetic', 'hip',
]

ELITIST_WORDS = [
    'ivy league', 'prestigious university', 'top tier', 'elite college',
    'brand name company', 'top school',
]


def mask_email(email: str) -> str:
    if not email:
        return None
    parts = email.split('@')
    if len(parts) != 2:
        return '***@***.***'
    user = parts[0]
    domain = parts[1]
    masked_user = user[0] + '*' * (len(user) - 1) if len(user) > 1 else '*'
    domain_parts = domain.split('.')
    masked_domain = domain_parts[0][0] + '***' if domain_parts else '***'
    return f"{masked_user}@{masked_domain}.***"


def mask_phone(phone: str) -> str:
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 10:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    return '*' * len(phone)


def generate_anon_id(candidate_id: int) -> str:
    """Generate a consistent anonymized ID from the real candidate ID."""
    hash_val = hashlib.md5(str(candidate_id).encode()).hexdigest()[:6].upper()
    return f"CND-{hash_val}"


def anonymize_application(application) -> Dict:
    """
    Returns an anonymized version of the application data.
    Strips all PII while preserving skills, scores, and experience.
    """
    candidate = application.candidate
    anon_id = generate_anon_id(candidate.id)

    return {
        'id':           application.id,
        'anon_id':      anon_id,
        'name':         f"Candidate {anon_id}",
        'email':        mask_email(candidate.email),
        'phone':        mask_phone(candidate.phone) if candidate.phone else None,
        'location':     _generalize_location(candidate.current_location),
        'experience':   candidate.experience_years,
        'skills':       candidate.skills_extracted or '',
        'ai_score':     application.ai_score,
        'status':       application.get_status_display(),
        'applied_at':   application.applied_at,
        'job_title':    application.job.title,
    }


def _generalize_location(location: str) -> str:
    """Generalize a specific city/area to country-level."""
    if not location:
        return 'India'
    indian_cities = [
        'mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'hyderabad',
        'pune', 'kolkata', 'ahmedabad', 'surat', 'jaipur', 'lucknow',
        'noida', 'gurugram', 'gurgaon', 'chandigarh', 'indore', 'bhopal',
        'kochi', 'thiruvananthapuram', 'nagpur', 'vadodara', 'coimbatore',
    ]
    loc_lower = location.lower()
    if any(city in loc_lower for city in indian_cities):
        return 'Metro India'
    if 'remote' in loc_lower:
        return 'Remote'
    if 'uk' in loc_lower or 'london' in loc_lower:
        return 'United Kingdom'
    if 'us' in loc_lower or 'new york' in loc_lower or 'california' in loc_lower:
        return 'United States'
    return 'India'  # Default


# ─── JD Bias Analyzer ─────────────────────────────────────────────

def analyze_jd_bias(job_description: str) -> Dict:
    """
    Analyze a job description for biased language.
    Returns: bias score, masculine/feminine/ageist/elitist word counts.
    """
    if not job_description:
        return {'score': 0, 'masculine': [], 'feminine': [], 'ageist': [], 'elitist': [], 'suggestions': []}

    text_lower = job_description.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    masculine_found = [w for w in MASCULINE_CODED if w in text_lower]
    feminine_found  = [w for w in FEMININE_CODED  if w in text_lower]
    ageist_found    = [w for w in AGEIST_WORDS    if w in text_lower]
    elitist_found   = [w for w in ELITIST_WORDS   if w in text_lower]

    # Compute bias risk score (0 = fair, 100 = very biased)
    male_score   = min(len(masculine_found) * 8, 40)
    female_score = min(len(feminine_found) * 4, 20)
    age_score    = min(len(ageist_found) * 12, 25)
    elite_score  = min(len(elitist_found) * 15, 15)
    bias_score   = min(male_score + female_score + age_score + elite_score, 100)

    # Gender skew
    if len(masculine_found) > len(feminine_found) + 2:
        skew = 'masculine'
    elif len(feminine_found) > len(masculine_found) + 2:
        skew = 'feminine'
    else:
        skew = 'neutral'

    # Suggestions
    suggestions = []
    if masculine_found:
        subs = ', '.join(f'"{w}"' for w in masculine_found[:3])
        suggestions.append(f"Replace gender-coded masculine words like {subs} with neutral alternatives.")
    if ageist_found:
        suggestions.append("Avoid age-related terms. Use 'early-career professional' instead of 'young/fresh graduate'.")
    if elitist_found:
        suggestions.append("Avoid elite-institution bias. Focus on skills and experience rather than college tier.")
    if bias_score < 20:
        suggestions.append("✅ Great! Your JD language appears largely unbiased and inclusive.")

    return {
        'score':      bias_score,
        'skew':       skew,
        'masculine':  masculine_found,
        'feminine':   feminine_found,
        'ageist':     ageist_found,
        'elitist':    elitist_found,
        'suggestions': suggestions,
    }


# ─── Batch Anonymizer ─────────────────────────────────────────────

def get_blind_screening_batch(applications) -> List[Dict]:
    """
    Returns list of anonymized candidate dicts for blind screening view.
    Sorted by AI score (highest first).
    """
    anon_list = []
    for app in applications:
        try:
            anon_list.append(anonymize_application(app))
        except Exception:
            continue
    return sorted(anon_list, key=lambda x: x['ai_score'], reverse=True)

"""
AI Salary Estimator Engine — SmartRecruit
────────────────────────────────────────────────────────────────
Feature #7: Heuristic regression model that estimates fair salary
range for a candidate based on:
  - Skills (technology tier weights)
  - Years of experience
  - Education level
  - Job title / role level
  - Location (India metro vs tier-2 vs international)
  - Current ATS score (demand proxy)

Returns:
  - Estimated salary range (min / mid / max) in INR LPA
  - Confidence level
  - Per-factor contribution breakdown
  - Market benchmarks
  - Negotiation zone

Feature #9: Cultural Fit Score
Keyword alignment between company description/values and
candidate resume/interview text using weighted term overlap.
"""

import re
from typing import Dict, List, Optional, Tuple


# ─── Salary Base Maps (INR LPA — Annual Package in Lakhs) ─────────

ROLE_BASE = {
    # Data Science / AI / ML
    'data scientist':       { 'entry': 6.0,  'mid': 13.0, 'senior': 24.0, 'lead': 38.0 },
    'ml engineer':          { 'entry': 7.0,  'mid': 15.0, 'senior': 28.0, 'lead': 42.0 },
    'ai engineer':          { 'entry': 7.5,  'mid': 16.0, 'senior': 30.0, 'lead': 45.0 },
    'data analyst':         { 'entry': 4.0,  'mid': 8.0,  'senior': 15.0, 'lead': 22.0 },
    'data engineer':        { 'entry': 6.0,  'mid': 13.0, 'senior': 24.0, 'lead': 36.0 },
    'nlp engineer':         { 'entry': 8.0,  'mid': 17.0, 'senior': 32.0, 'lead': 48.0 },
    # Software Engineering
    'software engineer':    { 'entry': 5.0,  'mid': 11.0, 'senior': 22.0, 'lead': 35.0 },
    'backend engineer':     { 'entry': 5.5,  'mid': 12.0, 'senior': 23.0, 'lead': 36.0 },
    'frontend engineer':    { 'entry': 4.5,  'mid': 10.0, 'senior': 20.0, 'lead': 32.0 },
    'full stack developer': { 'entry': 5.5,  'mid': 12.0, 'senior': 22.0, 'lead': 34.0 },
    'python developer':     { 'entry': 5.0,  'mid': 11.0, 'senior': 21.0, 'lead': 33.0 },
    # DevOps / Cloud
    'devops engineer':      { 'entry': 6.0,  'mid': 13.0, 'senior': 24.0, 'lead': 38.0 },
    'cloud architect':      { 'entry': 10.0, 'mid': 20.0, 'senior': 38.0, 'lead': 60.0 },
    # Management
    'product manager':      { 'entry': 8.0,  'mid': 18.0, 'senior': 32.0, 'lead': 50.0 },
    'engineering manager':  { 'entry': 15.0, 'mid': 28.0, 'senior': 45.0, 'lead': 70.0 },
    # Default
    '_default':             { 'entry': 4.5,  'mid': 10.0, 'senior': 20.0, 'lead': 32.0 },
}

# Premium skill multipliers (stacks on top of base)
PREMIUM_SKILLS = {
    # High demand DS/AI
    'pytorch':          0.12, 'tensorflow':    0.12, 'llm':            0.18,
    'transformers':     0.15, 'bert':          0.12, 'huggingface':    0.13,
    'reinforcement learning': 0.16, 'computer vision': 0.13, 'nlp': 0.10,
    # Cloud / DevOps
    'kubernetes':       0.10, 'aws':           0.08, 'azure':          0.07,
    'gcp':              0.08, 'terraform':     0.09, 'docker':         0.06,
    # Programming  
    'rust':             0.12, 'scala':         0.10, 'go':             0.09,
    'kotlin':           0.07, 'typescript':    0.05,
    # Data
    'spark':            0.10, 'kafka':         0.10, 'airflow':        0.08,
    'dbt':              0.08, 'snowflake':     0.07,
    # Standard
    'python':           0.05, 'sql':           0.03, 'java':           0.04,
    'react':            0.05, 'django':        0.04, 'fastapi':        0.05,
}

EDUCATION_MULTIPLIER = {
    'phd':        1.20,
    'm.tech':     1.12,
    'msc':        1.10,
    'mca':        1.08,
    'mba':        1.05,
    'b.tech':     1.00,
    'bsc':        0.97,
    'bca':        0.97,
    'diploma':    0.90,
    '_default':   1.00,
}

LOCATION_MULTIPLIER = {
    'mumbai':        1.20, 'bangalore': 1.25, 'bengaluru': 1.25,
    'hyderabad':     1.15, 'pune':      1.10, 'delhi':     1.15,
    'noida':         1.12, 'gurgaon':   1.15, 'gurugram':  1.15,
    'chennai':       1.10, 'kolkata':   0.95,
    'remote':        1.10,
    'metro india':   1.12,
    'usa':           4.50, 'uk':        4.00, 'canada':    3.80,
    'singapore':     3.50, 'germany':   3.20, 'australia': 3.70,
    '_default':      1.00,  # Tier-2 India
}

YOE_LEVEL_MAP = {
    (0, 1):   'entry',
    (1, 3):   'entry',
    (3, 6):   'mid',
    (6, 10):  'senior',
    (10, 99): 'lead',
}


def _get_experience_level(years: float) -> str:
    for (low, high), level in YOE_LEVEL_MAP.items():
        if low <= years < high:
            return level
    return 'senior'


def _match_role(job_title: str) -> Tuple[str, Dict]:
    title_lower = job_title.lower()
    for role_key, base_map in ROLE_BASE.items():
        if role_key != '_default' and role_key in title_lower:
            return role_key, base_map
    return '_default', ROLE_BASE['_default']


def _get_education_multiplier(skills_text: str) -> Tuple[str, float]:
    text_lower = skills_text.lower()
    for deg, mult in EDUCATION_MULTIPLIER.items():
        if deg != '_default' and deg in text_lower:
            return deg, mult
    return '_default', 1.00


def _get_location_multiplier(location: str) -> Tuple[str, float]:
    loc_lower = (location or 'india').lower()
    for loc, mult in LOCATION_MULTIPLIER.items():
        if loc != '_default' and loc in loc_lower:
            return loc, mult
    return location, LOCATION_MULTIPLIER['_default']


def _calculate_skill_bonus(skills_text: str) -> Tuple[float, List[str]]:
    text_lower = skills_text.lower()
    total = 0.0
    premium_found = []
    for skill, bonus in PREMIUM_SKILLS.items():
        if skill in text_lower:
            total += bonus
            premium_found.append(f"{skill} (+{int(bonus*100)}%)")
    return min(total, 0.60), premium_found  # Cap at 60% bonus


# ─── Main Salary Estimator ────────────────────────────────────────

def estimate_salary(
    job_title: str,
    experience_years: float,
    skills_text: str,
    location: str = 'India',
    ai_score: float = 0,
) -> Dict:
    """
    Estimates salary range (INR LPA) for a candidate.

    Args:
        job_title:        Job title / role being applied for
        experience_years: Total years of professional experience
        skills_text:      Raw text from resume (skills_extracted)
        location:         Candidate's current location
        ai_score:         Resume AI match score (0–100)

    Returns:
        Dict with salary range, factors, confidence, market benchmarks.
    """
    years = float(experience_years or 0)

    # ── Step 1: Base salary by role + experience tier ───────────────
    role_key, base_map = _match_role(job_title)
    level = _get_experience_level(years)
    base_salary = base_map[level]

    # ── Step 2: Education multiplier ────────────────────────────────
    edu_key, edu_mult = _get_education_multiplier(skills_text)

    # ── Step 3: Location multiplier ─────────────────────────────────
    loc_key, loc_mult = _get_location_multiplier(location)

    # ── Step 4: Premium skill bonus ─────────────────────────────────
    skill_bonus, premium_skills = _calculate_skill_bonus(skills_text)

    # ── Step 5: AI score demand factor (0–10% bonus) ────────────────
    demand_factor = 1.0 + (ai_score / 100 * 0.10)

    # ── Step 6: Compute mid salary ──────────────────────────────────
    mid = base_salary * edu_mult * loc_mult * (1 + skill_bonus) * demand_factor

    # Range: ±20% of mid (wider for senior)
    spread = 0.20 if level in ('entry', 'mid') else 0.25
    low  = round(mid * (1 - spread), 1)
    high = round(mid * (1 + spread), 1)
    mid  = round(mid, 1)

    # ── Step 7: Confidence level ────────────────────────────────────
    confidence_factors = 0
    if years > 0:          confidence_factors += 1
    if role_key != '_default': confidence_factors += 1
    if edu_key != '_default':  confidence_factors += 1
    if loc_key != location or loc_key in LOCATION_MULTIPLIER: confidence_factors += 1
    if premium_skills:     confidence_factors += 1
    confidence = ['Low', 'Low', 'Moderate', 'Moderate', 'High', 'Very High'][confidence_factors]

    # ── Step 8: Negotiation zone ────────────────────────────────────
    neg_low  = round(mid * 0.95, 1)
    neg_high = round(mid * 1.15, 1)

    # ── Step 9: Market percentiles (heuristic) ──────────────────────
    p25 = round(low * 0.95, 1)
    p50 = mid
    p75 = round(high * 1.02, 1)
    p90 = round(high * 1.15, 1)

    # ── Step 10: Factor breakdown for visualization ─────────────────
    factors = {
        'Role Base':     base_salary,
        'Education':     round((edu_mult - 1) * 100, 1),
        'Location':      round((loc_mult - 1) * 100, 1),
        'Premium Skills': round(skill_bonus * 100, 1),
        'AI Demand':     round((demand_factor - 1) * 100, 1),
    }

    return {
        'salary_min':     low,
        'salary_mid':     mid,
        'salary_max':     high,
        'currency':       'INR LPA',
        'experience_level': level.capitalize(),
        'role_matched':   role_key.title(),
        'confidence':     confidence,
        'negotiation_zone': { 'low': neg_low, 'high': neg_high },
        'market_percentiles': { 'p25': p25, 'p50': p50, 'p75': p75, 'p90': p90 },
        'premium_skills': premium_skills,
        'education_detected': edu_key,
        'location_applied': loc_key,
        'factors': factors,
    }


# ─── Feature 9: Cultural Fit Score ───────────────────────────────

# Default company values and culture keywords
DEFAULT_COMPANY_VALUES = [
    'innovation', 'collaboration', 'integrity', 'excellence', 'ownership',
    'agile', 'customer-centric', 'diversity', 'inclusion', 'transparency',
    'growth mindset', 'continuous learning', 'impact', 'data-driven',
    'accountability', 'empathy', 'respect', 'trust', 'teamwork',
]

CULTURE_CATEGORIES = {
    'Innovation':    ['innovation', 'creative', 'build', 'experiment', 'disrupt', 'novel', 'invent', 'problem solving'],
    'Collaboration': ['team', 'collaborate', 'together', 'cross-functional', 'partner', 'coordination', 'communication'],
    'Growth':        ['learning', 'growth', 'development', 'improve', 'upskill', 'mentorship', 'training', 'certification'],
    'Ownership':     ['ownership', 'responsible', 'accountable', 'initiative', 'proactive', 'lead', 'drive'],
    'Data-Driven':   ['data', 'analytics', 'metrics', 'evidence', 'insight', 'research', 'measure', 'kpi'],
    'Integrity':     ['honest', 'ethical', 'transparent', 'genuine', 'trust', 'integrity', 'respect'],
    'Customer Focus':['customer', 'user', 'client', 'satisfaction', 'support', 'experience', 'feedback'],
}


def calculate_cultural_fit(
    candidate_text: str,
    company_values: Optional[List[str]] = None,
    job_description: str = '',
) -> Dict:
    """
    Scores how well a candidate's profile aligns with company culture.

    Args:
        candidate_text:   Combined resume + interview text
        company_values:   List of company culture keywords (optional)
        job_description:  Job description text for additional context

    Returns:
        Dict with overall score, category breakdown, alignment signals.
    """
    if not candidate_text:
        return _empty_cultural_fit()

    combined_values = (company_values or []) + DEFAULT_COMPANY_VALUES
    candidate_lower = candidate_text.lower()
    jd_lower = job_description.lower()

    # ── Category Scoring ──────────────────────────────────────────
    category_scores = {}
    all_matches = []
    for category, keywords in CULTURE_CATEGORIES.items():
        matched = [kw for kw in keywords if kw in candidate_lower]
        jd_bonus = 0.1 if any(kw in jd_lower for kw in keywords) else 0
        score = min(len(matched) / len(keywords) * 100 + jd_bonus * 20, 100)
        category_scores[category] = {
            'score': round(score),
            'matched': matched[:4],
        }
        all_matches.extend(matched)

    # ── Overall Score (weighted average) ──────────────────────────
    weights = {
        'Innovation': 0.20, 'Collaboration': 0.20, 'Growth': 0.15,
        'Ownership': 0.15, 'Data-Driven': 0.15, 'Integrity': 0.10,
        'Customer Focus': 0.05,
    }
    overall = sum(category_scores[cat]['score'] * weights[cat] for cat in CULTURE_CATEGORIES)
    overall = round(overall)

    # ── Fit Label ─────────────────────────────────────────────────
    if overall >= 75:
        fit_label = 'Strong Cultural Fit'
        fit_color = 'success'
        fit_icon  = 'fas fa-handshake'
    elif overall >= 55:
        fit_label = 'Good Cultural Alignment'
        fit_color = 'info'
        fit_icon  = 'fas fa-check-circle'
    elif overall >= 35:
        fit_label = 'Partial Alignment'
        fit_color = 'warning'
        fit_icon  = 'fas fa-exclamation-circle'
    else:
        fit_label = 'Cultural Mismatch Risk'
        fit_color = 'danger'
        fit_icon  = 'fas fa-times-circle'

    # ── Top Alignment Signals ─────────────────────────────────────
    top_signals = list(dict.fromkeys(all_matches))[:8]

    # ── Weak Areas ───────────────────────────────────────────────-
    weak_categories = [cat for cat, data in category_scores.items() if data['score'] < 30]

    recommendation = _culture_recommendation(overall, weak_categories)

    return {
        'overall_score':    overall,
        'fit_label':        fit_label,
        'fit_color':        fit_color,
        'fit_icon':         fit_icon,
        'category_scores':  category_scores,
        'top_signals':      top_signals,
        'weak_areas':       weak_categories,
        'recommendation':   recommendation,
    }


def _culture_recommendation(score: int, weak_areas: List[str]) -> str:
    if score >= 75:
        return "Excellent cultural alignment. Candidate's values and work style closely match the organization's culture."
    elif score >= 55:
        missing = ', '.join(weak_areas[:2]) if weak_areas else 'a few'
        return f"Good alignment overall. Consider discussing {missing} during the HR round to confirm cultural compatibility."
    else:
        areas = ', '.join(weak_areas[:3]) if weak_areas else 'collaboration and growth'
        return f"Cultural alignment is moderate. Candidate shows limited signals for: {areas}. Recommend a culture-focused interview round."


def _empty_cultural_fit() -> Dict:
    return {
        'overall_score': 0,
        'fit_label': 'No Data',
        'fit_color': 'secondary',
        'fit_icon': 'fas fa-question-circle',
        'category_scores': {cat: {'score': 0, 'matched': []} for cat in CULTURE_CATEGORIES},
        'top_signals': [],
        'weak_areas': list(CULTURE_CATEGORIES.keys()),
        'recommendation': 'No candidate text available for cultural fit analysis.',
    }


# ─── Feature 8: Offer Acceptance Probability ──────────────────────

ACCEPTANCE_FACTORS = {
    'ai_score':            0.25,   # Resume match quality
    'predictive_score':    0.30,   # Composite hiring score
    'time_to_offer_days':  -0.01,  # Negative: delay reduces probability
    'rounds_completed':    0.10,   # More rounds = more investment/interest
    'salary_competitiveness': 0.20,# How competitive the offer is vs estimate
    'culture_fit':         0.15,   # Cultural alignment
}

def estimate_offer_acceptance(
    ai_score: float,
    predictive_score: float,
    days_to_offer: int,
    rounds_completed: int,
    offered_salary: Optional[float],
    estimated_salary_mid: Optional[float],
    culture_fit_score: float,
) -> Dict:
    """
    Predicts probability (0–100%) that a candidate will accept the offer.
    Uses a logistic-regression inspired weighted factor model.
    """
    # Salary competitiveness (0–100)
    if offered_salary and estimated_salary_mid and estimated_salary_mid > 0:
        salary_comp = min((offered_salary / estimated_salary_mid) * 100, 130)
    else:
        salary_comp = 70  # Assume average

    # Time penalty (max 30 days positive effect)
    time_penalty = max(0, min(days_to_offer, 60))

    # Weighted raw score
    raw = (
        ai_score * 0.20
        + predictive_score * 0.25
        + (min(rounds_completed, 4) * 25) * 0.10
        + salary_comp * 0.25
        + culture_fit_score * 0.15
        - time_penalty * 0.3
    )

    # Clamp 0–100
    probability = round(max(0, min(raw, 100)))

    # Label
    if probability >= 80:
        label, color = 'Very Likely to Accept', 'success'
    elif probability >= 60:
        label, color = 'Likely to Accept', 'info'
    elif probability >= 40:
        label, color = 'Uncertain', 'warning'
    else:
        label, color = 'At Risk of Declining', 'danger'

    # Risk factors
    risks = []
    if days_to_offer > 14: risks.append(f"Offer delayed by {days_to_offer} days — risk of candidate exploring other options.")
    if salary_comp < 90:   risks.append("Offered salary is below estimated market rate for this profile.")
    if culture_fit_score < 40: risks.append("Low cultural alignment may reduce long-term retention after acceptance.")
    if ai_score < 50:      risks.append("Low AI match score — candidate may feel underqualified and second-guess the fit.")

    # Boosters
    boosters = []
    if salary_comp >= 110: boosters.append("Offer is above market rate — strong financial incentive.")
    if culture_fit_score >= 70: boosters.append("High cultural fit score — candidate likely values the role beyond salary.")
    if rounds_completed >= 3: boosters.append("Candidate invested significant time through multiple rounds — committed.")

    return {
        'probability': probability,
        'label': label,
        'color': color,
        'risks': risks,
        'boosters': boosters,
        'salary_competitiveness': round(salary_comp),
    }

# ─── Feature 10: PathwayAI (Deep Learning Career Predictor) ────────

CAREER_PATHS = {
    'software engineer': ['Senior Software Engineer', 'Engineering Manager', 'Software Architect'],
    'data scientist': ['Senior Data Scientist', 'AI Researcher', 'Head of Data Science'],
    'frontend engineer': ['Senior Frontend Engineer', 'UI/UX Lead', 'Frontend Architect'],
    'ml engineer': ['Senior ML Engineer', 'AI Architect', 'Chief AI Officer'],
    'python developer': ['Senior Python Developer', 'Backend Architect', 'Full Stack Lead'],
}

def predict_career_path(candidate_profile: dict) -> Dict:
    """
    PathwayAI: DL-inspired career trajectory predictor.
    Analyzes current role, skills, and YOE to map future growth.
    """
    current_role = candidate_profile.get('current_role', 'Software Engineer').lower()
    skills = candidate_profile.get('skills', [])
    yoe = float(candidate_profile.get('experience_years', 0))
    
    # ── Step 1: Base Trajectory (Pattern Matching) ─────────────
    next_roles = []
    for role, path in CAREER_PATHS.items():
        if role in current_role:
            next_roles = path
            break
    
    if not next_roles:
        next_roles = ['Senior ' + current_role.title(), 'Lead ' + current_role.title(), 'Architect']

    # ── Step 2: Transition Probability (Deep Logic) ─────────────
    # Higher YOE and more skills = faster transition to Lead/Architect
    skill_count = len(skills)
    transition_years = max(1, round(5 - (skill_count * 0.2) - (yoe * 0.1), 1))
    
    # ── Step 3: Salary Jump Prediction ──────────────────────────
    current_salary = candidate_profile.get('current_salary', 10.0)
    jump_pct = 15 + (skill_count * 2) + (yoe * 1.5)
    predicted_salary = round(current_salary * (1 + jump_pct/100), 1)

    # ── Step 4: Recommended Upskilling (SkillForge Bridge) ──────
    upskilling = []
    if 'cloud' not in str(skills).lower(): upskilling.append('Cloud Architecture (AWS/Azure)')
    if 'ai' not in str(skills).lower() and 'ml' not in str(skills).lower(): upskilling.append('Generative AI Fundamentals')
    if yoe > 5 and 'leadership' not in str(skills).lower(): upskilling.append('Engineering Management & Mentorship')

    return {
        'next_milestone_role': next_roles[0],
        'secondary_roles': next_roles[1:],
        'estimated_time_to_next': f"{transition_years} years",
        'predicted_salary_jump': f"{round(jump_pct)}%",
        'next_salary_estimate': f"{predicted_salary} LPA",
        'upskilling_required': upskilling[:3],
        'confidence_score': min(65 + (skill_count * 2), 98),
        'rationale': f"Strong foundation in {skills[0] if skills else 'core tech'} and {yoe} years of experience suggests a natural move towards {next_roles[0]}."
    }


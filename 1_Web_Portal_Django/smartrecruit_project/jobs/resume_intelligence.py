"""
Resume Intelligence Engine — SmartRecruit
──────────────────────────────────────────────────────────────────
NLP-powered entity extraction from resume text.
No external NLP library dependency (pure regex + heuristics).

Extracts:
  1. Contact Info (email, phone, LinkedIn, GitHub)
  2. Education (degree, institution, year)
  3. Work Experience (company, role, years)
  4. Skills (technical & soft)
  5. Certifications
  6. Projects
  7. Total Experience Years
  8. ATS Readability Score
"""

import re
from typing import Dict, List, Optional


# ─── Patterns ────────────────────────────────────────────────────

EMAIL_RE    = re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', re.I)
PHONE_RE    = re.compile(r'(?:\+91[\s-]?)?(?:\(?\d{3,5}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4,6}')
LINKEDIN_RE = re.compile(r'linkedin\.com/in/[\w-]+', re.I)
GITHUB_RE   = re.compile(r'github\.com/[\w-]+', re.I)

DEGREE_PATTERNS = [
    r'\b(B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|B\.?Sc\.?|M\.?Sc\.?|BCA|MCA|B\.?Com|MBA|Ph\.?D|Bachelor|Master|Diploma|Associate)\b',
    r'\b(Computer Science|Information Technology|Electronics|Electrical|Mechanical|Civil|Data Science|AI|ML)\b',
]

CERT_KEYWORDS = [
    'certified', 'certification', 'certificate', 'aws certified', 'google cloud',
    'azure', 'pmp', 'scrum', 'agile', 'coursera', 'udemy', 'edx', 'nptel',
    'cisco', 'comptia', 'oracle', 'salesforce', 'tensorflow developer',
    'deep learning specialization', 'machine learning', 'data science',
]

PROJECT_INDICATORS = [
    'project', 'developed', 'built', 'implemented', 'created', 'designed',
    'deployed', 'launched', 'architected', 'engineered',
]

SECTION_HEADERS = {
    'education':      r'\b(education|academic|qualification|degree|university|college)\b',
    'experience':     r'\b(experience|work history|employment|career|professional)\b',
    'skills':         r'\b(skills|technical skills|competencies|technologies|expertise)\b',
    'certifications': r'\b(certification|certificates|credentials|courses|training)\b',
    'projects':       r'\b(projects|portfolio|work samples|personal projects)\b',
    'summary':        r'\b(summary|profile|objective|about me|overview)\b',
}

TECH_SKILLS = [
    # Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
    'ruby', 'php', 'kotlin', 'swift', 'r', 'scala', 'dart', 'perl',
    # Web
    'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
    'fastapi', 'spring', 'laravel', 'rails', 'html', 'css', 'bootstrap',
    # Data / ML
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
    'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy',
    'nlp', 'computer vision', 'opencv', 'bert', 'transformers', 'huggingface',
    'xgboost', 'random forest', 'neural network', 'cnn', 'rnn', 'lstm',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
    'jenkins', 'github actions', 'ci/cd', 'devops',
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'sqlite', 'oracle', 'cassandra', 'dynamodb',
    # Tools
    'git', 'github', 'gitlab', 'jira', 'confluence', 'linux', 'bash',
    'postman', 'swagger', 'rest api', 'graphql', 'microservices',
    # Mobile
    'android', 'ios', 'flutter', 'react native', 'xamarin',
]

SOFT_SKILLS = [
    'communication', 'leadership', 'teamwork', 'problem solving', 'analytical',
    'critical thinking', 'time management', 'project management', 'agile',
    'scrum', 'collaboration', 'adaptability', 'creativity', 'attention to detail',
]

YEAR_RE      = re.compile(r'\b(19|20)\d{2}\b')
YOE_RE       = re.compile(r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)', re.I)
COMPANY_SIZE = re.compile(r'\b(startup|mnc|product|service|enterprise|sme)\b', re.I)


# ─── Main Extractor ───────────────────────────────────────────────

def extract_resume_entities(text: str, candidate=None) -> Dict:
    """
    Main entry point. Accepts raw resume text string.
    Returns structured dict with all extracted entities.
    """
    text = text or ''
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    contact    = _extract_contact(text)
    education  = _extract_education(text, lines)
    skills     = _extract_skills(text)
    certs      = _extract_certifications(text, lines)
    projects   = _extract_projects(text, lines)
    experience = _extract_experience(text, lines, candidate)
    summary    = _extract_summary(text, lines)
    ats_score  = _calculate_ats_score(text, contact, skills, education, experience)

    return {
        'contact':       contact,
        'education':     education,
        'skills':        skills,
        'certifications': certs,
        'projects':      projects,
        'experience':    experience,
        'summary':       summary,
        'ats_score':     ats_score,
        'word_count':    len(text.split()),
        'line_count':    len(lines),
    }


def _extract_contact(text: str) -> Dict:
    email   = EMAIL_RE.search(text)
    phone   = PHONE_RE.search(text)
    linkedin= LINKEDIN_RE.search(text)
    github  = GITHUB_RE.search(text)
    return {
        'email':    email.group()    if email    else None,
        'phone':    phone.group()    if phone    else None,
        'linkedin': linkedin.group() if linkedin else None,
        'github':   github.group()   if github   else None,
    }


def _extract_education(text: str, lines: List[str]) -> List[Dict]:
    """Extract degree, institution, year."""
    results = []
    edu_re  = re.compile('|'.join(DEGREE_PATTERNS), re.I)
    years   = YEAR_RE.findall(text)

    for i, line in enumerate(lines):
        if edu_re.search(line):
            context = ' '.join(lines[max(0, i-1): i+3])
            yr_match = YEAR_RE.search(context)
            results.append({
                'raw':  line,
                'year': yr_match.group() if yr_match else None,
            })

    return results[:5]  # Cap to 5 entries


def _extract_skills(text: str) -> Dict:
    """Match technical and soft skills from the resume text."""
    text_lower = text.lower()
    matched_tech = [s for s in TECH_SKILLS if s in text_lower]
    matched_soft = [s for s in SOFT_SKILLS if s in text_lower]

    # Deduplicate while preserving order
    seen = set()
    unique_tech = []
    for s in matched_tech:
        if s not in seen:
            seen.add(s)
            unique_tech.append(s)

    return {
        'technical': unique_tech,
        'soft':      list(set(matched_soft)),
        'total':     len(unique_tech) + len(matched_soft),
    }


def _extract_certifications(text: str, lines: List[str]) -> List[str]:
    """Find certification mentions."""
    certs = []
    text_lower = text.lower()
    for line in lines:
        ll = line.lower()
        if any(kw in ll for kw in CERT_KEYWORDS):
            if len(line) > 10:  # Skip noise
                certs.append(line.strip())
    # Deduplicate
    seen = set()
    unique = []
    for c in certs:
        key = c[:40].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:8]


def _extract_projects(text: str, lines: List[str]) -> List[str]:
    """Detect project mentions."""
    projects = []
    in_project_section = False

    for line in lines:
        ll = line.lower()
        if re.search(SECTION_HEADERS['projects'], ll):
            in_project_section = True
            continue
        if in_project_section:
            if re.search(r'\b(education|experience|skills|certif)\b', ll):
                in_project_section = False
            elif len(line) > 15 and any(kw in ll for kw in PROJECT_INDICATORS):
                projects.append(line.strip()[:120])

    # Fallback: detect project-like lines anywhere
    if not projects:
        for line in lines:
            ll = line.lower()
            if any(kw in ll for kw in ['project:', 'built:', 'developed:']) and len(line) > 10:
                projects.append(line.strip()[:120])

    return projects[:6]


def _extract_experience(text: str, lines: List[str], candidate=None) -> Dict:
    """
    Extract years of experience and work entries.
    Uses: explicit "X years experience" mentions, date ranges in text,
    and candidate.experience_years as fallback.
    """
    # Try explicit YOE match
    yoe_match = YOE_RE.search(text)
    total_years = float(yoe_match.group(1)) if yoe_match else None

    # Fallback to model field
    if total_years is None and candidate and hasattr(candidate, 'experience_years'):
        total_years = candidate.experience_years

    # Extract years from text to compute range
    all_years = [int(y) for y in YEAR_RE.findall(text)]
    year_range = None
    if len(all_years) >= 2:
        year_range = f"{min(all_years)} – {max(all_years)}"

    # Detect work entries (lines that might be job titles or company names)
    work_entries = []
    for line in lines:
        ll = line.lower()
        if any(kw in ll for kw in ['engineer', 'developer', 'analyst', 'intern', 'manager', 'lead', 'architect', 'scientist']):
            if 5 < len(line) < 100:
                work_entries.append(line.strip())

    return {
        'total_years':   total_years,
        'year_range':    year_range,
        'work_entries':  work_entries[:6],
    }


def _extract_summary(text: str, lines: List[str]) -> Optional[str]:
    """Find the summary/objective section."""
    in_summary = False
    summary_lines = []
    for line in lines:
        ll = line.lower()
        if re.search(r'\b(summary|profile|objective|about me)\b', ll) and len(line) < 40:
            in_summary = True
            continue
        if in_summary:
            if re.search(r'\b(education|experience|skills|certif|project)\b', ll) and len(line) < 40:
                break
            if len(line) > 10:
                summary_lines.append(line)
            if len(summary_lines) >= 4:
                break

    return ' '.join(summary_lines) if summary_lines else None


def _calculate_ats_score(text: str, contact: Dict, skills: Dict, education: List, experience: Dict) -> Dict:
    """
    Heuristic ATS readability score (0–100).
    Checks: completeness, skill density, keyword presence, length.
    """
    score = 0
    issues = []
    suggestions = []

    # Contact completeness (20 pts)
    if contact.get('email'):   score += 8
    else: issues.append("Missing email address")
    if contact.get('phone'):   score += 6
    else: issues.append("Missing phone number")
    if contact.get('linkedin'):score += 4
    else: suggestions.append("Add LinkedIn URL for better visibility")
    if contact.get('github'):  score += 2
    else: suggestions.append("Add GitHub profile for technical roles")

    # Skills (30 pts)
    tech_count = len(skills.get('technical', []))
    if tech_count >= 10:   score += 30
    elif tech_count >= 6:  score += 20
    elif tech_count >= 3:  score += 10
    else:
        issues.append("Very few technical skills detected")

    # Education (15 pts)
    if education:
        score += 12
        if any(e.get('year') for e in education):
            score += 3
    else:
        issues.append("Education section not clearly detected")

    # Experience (20 pts)
    if experience.get('total_years'):
        score += 10
        if experience['total_years'] >= 2:
            score += 5
        if experience['work_entries']:
            score += 5
    else:
        suggestions.append("Explicitly mention total years of experience")

    # Length & Completeness (15 pts)
    word_count = len(text.split())
    if 300 <= word_count <= 800:
        score += 10
    elif word_count > 800:
        score += 7
        suggestions.append("Resume may be too long for ATS parsers (>800 words)")
    else:
        score += 3
        issues.append("Resume is too short — add more detail")
    if '\n' in text and len(text.splitlines()) > 10:
        score += 5

    grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 50 else 'D'

    return {
        'score':       min(score, 100),
        'grade':       grade,
        'issues':      issues,
        'suggestions': suggestions,
    }

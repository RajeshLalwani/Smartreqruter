from .models import JobPosting, Application, Candidate
from django.db.models import Q

def get_candidate_skills(user):
    if not hasattr(user, 'candidate_profile'): return []
    try:
        raw_skills = user.candidate_profile.skills_extracted
        if raw_skills:
            if '[' in raw_skills:
                import ast
                return [s.strip().lower() for s in ast.literal_eval(raw_skills)]
            else:
                return [s.strip().lower() for s in raw_skills.split(',')]
    except Exception:
        return []
    return []

def get_match_details(user, job):
    candidate_skills = get_candidate_skills(user)
    job_skills = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
    
    matched = []
    missing = []
    
    for skill in job_skills:
        if skill in candidate_skills:
            matched.append(skill)
        else:
            missing.append(skill)
            
    # Base Keyword Score
    keyword_score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0
    
    # Semantic Score Calculation
    semantic_score = 0
    try:
        # Attempt to use Spacy for semantic similarity
        import spacy
        import en_core_web_sm
        nlp = en_core_web_sm.load()
        
        # Create docs
        # Join skills into a mock sentence for context
        resume_text = ""
        if hasattr(user, 'candidate_profile'):
            resume_text = user.candidate_profile.resume_text if hasattr(user.candidate_profile, 'resume_text') else ''
            
        job_text = f"{job.title} requires {', '.join(job_skills)}"
        candidate_text = f"{resume_text} skills: {', '.join(candidate_skills)}"
        
        doc1 = nlp(job_text)
        doc2 = nlp(candidate_text)
        semantic_score = int(doc1.similarity(doc2) * 100)
    except Exception:
        # Fallback: Boosted keyword score
        # precise matching + partial matching on skills
        partial_matches = 0
        for j_skill in missing:
            for c_skill in candidate_skills:
                # If there's a significant substring match (e.g. "react" in "react.js")
                if j_skill in c_skill or c_skill in j_skill:
                    partial_matches += 0.5
                    break
        
        semantic_score = min(keyword_score + int((partial_matches / len(job_skills)) * 100), 100) if job_skills else 0

    # Tech Stack Boost (10% boost if stack matches)
    if job.technology_stack != 'GENERAL' and hasattr(user, 'candidate_profile'):
        # Simple heuristic: if job tech stack name is in candidate skills
        if job.technology_stack.lower().replace('_', ' ') in candidate_skills:
            keyword_score = min(keyword_score + 10, 100)
            semantic_score = min(semantic_score + 10, 100)
            
    return {
        'score': semantic_score, # Use semantic score as the primary 'Match Score'
        'keyword_score': keyword_score,
        'matched': [s.title() for s in matched],
        'missing': [s.title() for s in missing]
    }

def get_job_recommendations(user, limit=5):
    """
    Recommend jobs based on skill overlap.
    """
    if not hasattr(user, 'candidate_profile'):
        jobs = JobPosting.objects.filter(status='OPEN').order_by('-created_at')[:limit]
        return [{'job': job, 'match_score': 0, 'matched': [], 'missing': [], 'reasons': ['Latest Job']} for job in jobs]

    jobs = JobPosting.objects.filter(status='OPEN').exclude(applications__candidate=user.candidate_profile)
    scored_jobs = []

    for job in jobs:
        details = get_match_details(user, job)
        if details['score'] > 0:
            reasons = []
            if details['matched']:
                reasons.append(f"Matches {len(details['matched'])} skills")
            
            scored_jobs.append({
                'job': job, 
                'match_score': details['score'], 
                'keyword_score': details.get('keyword_score', 0),
                'matched': details['matched'],
                'missing': details['missing'],
                'reasons': reasons
            })

    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return scored_jobs[:limit]

def advanced_job_search(params):
    """
    Filter jobs based on various parameters.
    """
    jobs = JobPosting.objects.filter(status='OPEN')
    
    query = params.get('q')
    location = params.get('location')
    job_type = params.get('job_type')
    
    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(technology_stack__icontains=query) | Q(description__icontains=query))
    
    if location:
        jobs = jobs.filter(location__icontains=location)
        
    if job_type:
        jobs = jobs.filter(job_type=job_type)
        
    return jobs.order_by('-created_at')

def get_job_match_score(user, job):
    """
    Calculate simple match score for UI display
    """
    return get_match_details(user, job)['score']

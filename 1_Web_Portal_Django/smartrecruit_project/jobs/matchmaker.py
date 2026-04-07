import os
import json
import logging
from django.db.models import Q
from .models import JobPosting, Candidate, SourcingMatch
from .recommendations import get_match_details

logger = logging.getLogger(__name__)

class MatchmakerAgent:
    """
    The Matchmaker: An autonomous agent that proactively discovers talent
    for open requisitions by scanning the candidate database.
    """
    
    def run_sourcing_cycle(self, job_instance=None):
        """
        Runs a complete sourcing cycle.
        If job_instance is provided, sources only for that job.
        Otherwise, sources for all OPEN jobs.
        """
        jobs = [job_instance] if job_instance else JobPosting.objects.filter(status='OPEN')
        candidates = Candidate.objects.all()
        
        total_matches = 0
        
        for job in jobs:
            logger.info(f"Matchmaker sourcing for: {job.title}")
            for candidate in candidates:
                # Skip if already matched recently (e.g. within 24 hours)
                # For Phase 5, we'll re-calculate if requested or new candidate
                
                match_data = get_match_details(candidate.user, job)
                score = match_data.get('score', 0)
                
                if score >= 65: # Elite threshold for "Auto-Shortlist"
                    rationale = f"Detected strong {job.technology_stack} alignment. "
                    rationale += f"Matches {len(match_data.get('matched', []))} core skills: "
                    rationale += ", ".join(match_data.get('matched', [])[:3])
                    
                    match, created = SourcingMatch.objects.update_or_create(
                        job=job,
                        candidate=candidate,
                        defaults={
                            'match_score': score,
                            'fit_rationale': rationale,
                            'is_shortlisted': score >= 85 # Auto-shortlist for very high scores
                        }
                    )
                    if created: total_matches += 1
                    
        return total_matches

    def get_top_matches(self, job_id, limit=10):
        """Helper to fetch matches for a specific job."""
        return SourcingMatch.objects.filter(job_id=job_id).order_by('-match_score')[:limit]

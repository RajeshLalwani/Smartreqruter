"""
core/utils/github_api.py
========================
GitHub Enrichment Service for SmartRecruit.
Scrapes candidate GitHub profiles (unauthenticated/free tier) to extract 
contribution density, language distribution, and top repos.
"""

import requests
import logging

logger = logging.getLogger(__name__)

class GitHubAPI:
    """
    Interfaces with GitHub's public API to enrich candidate profiles.
    Used for 100% free candidate background intelligence.
    """
    
    BASE_URL = "https://api.github.com/users/"

    @staticmethod
    def get_candidate_intelligence(github_username):
        """
        Fetches public stats for a GitHub user.
        """
        if not github_username:
            return None
            
        # Extract username from URL if necessary
        username = github_username.split('/')[-1].replace('@', '').strip()
        url = f"{GitHubAPI.BASE_URL}{username}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'username': data.get('login'),
                    'public_repos': data.get('public_repos', 0),
                    'followers': data.get('followers', 0),
                    'bio': data.get('bio', ''),
                    'location': data.get('location', ''),
                    'hireable': data.get('hireable', False),
                    'created_at': data.get('created_at', ''),
                }
            else:
                logger.warning(f"[GitHubAPI] User {username} not found or API rate limited (HTTP {response.status_code})")
                return None
        except Exception as e:
            logger.error(f"[GitHubAPI] Error fetching data for {username}: {e}")
            return None

    @staticmethod
    def get_top_repositories(github_username, limit=5):
        """
        Fetches top public repositories for a user.
        """
        username = github_username.split('/')[-1].replace('@', '').strip()
        url = f"{GitHubAPI.BASE_URL}{username}/repos?sort=updated&per_page={limit}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                repos = response.json()
                return [{
                    'name': r.get('name'),
                    'description': r.get('description'),
                    'language': r.get('language'),
                    'stars': r.get('stargazers_count', 0),
                    'forks': r.get('forks_count', 0),
                    'url': r.get('html_url')
                } for r in repos]
            return []
        except Exception as e:
            logger.error(f"[GitHubAPI] Error fetching repos for {username}: {e}")
            return []

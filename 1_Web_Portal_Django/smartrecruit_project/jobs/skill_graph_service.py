# 🕸️ SMARTRECRUIT KNOWLEDGE GRAPH SERVICE
# Moving from Simple Keywords to Ontological Reasoning

TECH_ONTOLOGY = {
    "Cloud Native": ["Kubernetes", "Docker", "Helm", "Service Mesh", "Istio", "Terraform", "CloudFormation"],
    "Frontend Mastery": ["React", "Vue", "Angular", "Next.js", "TypeScript", "Tailwind CSS", "Redux", "Web Performance"],
    "AI/ML Engineering": ["PyTorch", "TensorFlow", "Scikit-Learn", "Transformer", "LLM", "NLP", "Computer Vision", "MLOps"],
    "Backend Scale": ["Golang", "Rust", "Node.js", "Distributed Systems", "Microservices", "gRPC", "Message Queues", "Kafka"],
    "DevOps Automation": ["CI/CD", "Jenkins", "GitHub Actions", "Ansible", "Prometheus", "Grafana", "Site Reliability Engineering"],
    "Data Engineering": ["Spark", "Hadoop", "Airflow", "ETL", "Snowflake", "BigQuery", "Data Lake", "Vector DB"],
}

def get_expanded_concepts(query_text):
    """
    Expands a search query by identifying 'Core Domains' and injecting related concepts.
    This ensures that vector embeddings capture the full 'Contextual Cloud' of the query.
    """
    expanded_terms = []
    query_lower = query_text.lower()
    
    # 1. Ontological Mapping
    for domain, skills in TECH_ONTOLOGY.items():
        # Check if the query matches the domain or any skill within it
        if domain.lower() in query_lower or any(s.lower() in query_lower for s in skills):
            expanded_terms.extend(skills)
            expanded_terms.append(domain)
            
    # 2. Deduplicate and return
    unique_terms = list(set(expanded_terms))
    
    # We return the original query + the 'Conceptual Cloud'
    if unique_terms:
        # We only take a subset to avoid bloating the embedding space too much
        expansion_string = ", ".join(unique_terms[:15])
        return f"{query_text} (Contextual Cluster: {expansion_string})"
    
    return query_text

def get_skill_distance(skill_a, skill_b):
    """
    Calculates conceptual distance between two skills.
    In a full Knowledge Graph implementation, this would use Graph Traversal.
    """
    for domain, skills in TECH_ONTOLOGY.items():
        if skill_a in skills and skill_b in skills:
            return 0.1 # Very close (same domain)
            
    return 1.0 # Distant

def get_learning_roadmap(missing_skills: list) -> list:
    """
    SkillForge: Maps missing skills to curated learning resources.
    Returns a list of dictionaries with skill, resource, and difficulty.
    """
    from .models import SkillLearningResource
    
    roadmap = []
    for skill in missing_skills:
        # Search for resources for this skill
        resources = SkillLearningResource.objects.filter(skill_name__icontains=skill)
        if resources.exists():
            for res in resources[:2]: # Top 2 resources
                roadmap.append({
                    'skill': skill,
                    'title': res.resource_title,
                    'url': res.url,
                    'difficulty': res.difficulty,
                    'platform': res.platform
                })
        else:
            # Fallback for common tech
            roadmap.append({
                'skill': skill,
                'title': f"Mastering {skill} for Professionals",
                'url': f"https://www.coursera.org/search?query={skill}",
                'difficulty': 'Intermediate',
                'platform': 'Coursera'
            })
            
    return roadmap

def seed_learning_resources():
    """Utility to seed some initial resources for SkillForge."""
    from .models import SkillLearningResource
    
    defaults = [
        ('Python', 'Modern Python Bootcamp', 'https://www.udemy.com/topic/python/', 'Beginner'),
        ('Machine Learning', 'Machine Learning Specialization', 'https://www.coursera.org/specializations/machine-learning-introduction', 'Intermediate'),
        ('AWS', 'AWS Certified Solutions Architect', 'https://explore.skillbuilder.aws/', 'Advanced'),
        ('React', 'React - The Complete Guide', 'https://react.dev/learn', 'Beginner'),
        ('Docker', 'Docker Mastery', 'https://www.docker.com/products/docker-desktop/', 'Intermediate'),
        ('Generative AI', 'DeepLearning.AI: Generative AI for Everyone', 'https://www.deeplearning.ai/courses/generative-ai-for-everyone/', 'Beginner'),
    ]
    
    for skill, title, url, diff in defaults:
        SkillLearningResource.objects.get_or_create(
            skill_name=skill,
            resource_title=title,
            defaults={'url': url, 'difficulty': diff}
        )

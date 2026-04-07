import os
import sys
import django

sys.path.append(r"c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartrecruit_project.settings")
django.setup()

from jobs.utils import parse_resume
from Resume_Matcher.ai_matcher import ResumeMatcher
from RAG_System.rag_pipeline import CandidateRAGPipeline

print("Testing Dense Vectors...")
rag = CandidateRAGPipeline()
docs = {"cand1": "I am a Python Backend Developer using Django and AWS", "cand2": "I hate Python, I only do UI UX Design."}
rag.load_candidates(docs)
results = rag.search_candidates("Need a Django developer")
print("RAG Results:", results)

print("Testing Resume Matcher baseline...")
matcher = ResumeMatcher()
score = matcher.calculate_match("I am a Python Django developer.", "Need a Django developer")
print("Match Score:", score)

print("Testing Skills JSON Extractor...")
resume_path = r"c:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit\1_Web_Portal_Django\smartrecruit_project\media\resumes\sample.txt"
# Create sample text
with open(resume_path, "w") as f:
    f.write("I am an expert in Python and Django. I have 5 years of experience. I am also familiar with Kubernetes and AWS but only used them once. Core skills include React.")

with open(resume_path, "rb") as f:
    res = parse_resume(f)
print("Extracted Skills JSON:", res.get('skills'))

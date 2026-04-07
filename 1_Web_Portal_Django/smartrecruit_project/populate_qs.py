import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '2_AI_Modules'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import Question
from django.contrib.auth import get_user_model
from jobs.utils import fetch_questions, generate_ai_mcqs

def populate_questions():
    User = get_user_model()
    # Find a recruiter to own the questions
    recruiter = User.objects.filter(is_recruiter=True).first()
    if not recruiter:
        recruiter = User.objects.first()

    domains = ['PYTHON', 'GENERAL', 'APTITUDE']
    difficulties = ['easy', 'medium', 'hard']

    for domain in domains:
        for diff in difficulties:
            count = Question.objects.filter(category__iexact=domain, difficulty=diff).count()
            needed = 50 - count
            if needed > 0:
                print(f"Fetching {needed} questions for {domain} - {diff}...")
                try:
                    if domain == 'APTITUDE':
                        # category 18 is Science: Computers in OpenTriviaDB, let's use it for Aptitude or 9 (General Knowledge)
                        # OpenTrivia DB has category=9 for General Knowledge, let's use 9 for aptitude if needed, or 18 as it was.
                        fetched = fetch_questions(amount=min(needed, 50), category=9, difficulty=diff)
                    else:
                        fetched = generate_ai_mcqs(amount=needed, domain=domain, difficulty=diff)
                        
                    if not fetched:
                        print(f"Fallback: Trying smaller batch for {domain} {diff}")
                        fetched = generate_ai_mcqs(amount=10, domain=domain, difficulty=diff)
                        
                    saved = 0
                    for q in fetched:
                        Question.objects.create(
                            recruiter=recruiter,
                            text=q['question'],
                            options=q['options'],
                            correct_answer=q['correct'],
                            category=domain,
                            difficulty=diff
                        )
                        saved += 1
                    print(f"Saved {saved} questions for {domain} - {diff}")
                except Exception as e:
                    print(f"Error fetching {domain} {diff}: {e}")
            else:
                print(f"{domain} - {diff} already has {count} questions.")

if __name__ == "__main__":
    populate_questions()

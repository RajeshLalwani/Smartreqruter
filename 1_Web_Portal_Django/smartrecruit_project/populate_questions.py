import os
import sys
import django
import time

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from jobs.models import Question
from django.contrib.auth import get_user_model
from jobs.utils import generate_ai_mcqs

User = get_user_model()

def populate_questions():
    print("Starting AI Question Generation...")
    
    # Get the admin user to assign questions to
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.first()
        if not admin_user:
            print("No users found. Please create a superuser first.")
            return

    domains = ['Python', 'Java', 'JavaScript', 'SQL', 'Aptitude', 'HR/Behavioral']
    difficulties = ['easy', 'medium', 'hard']
    target_per_combo = 100
    batch_size = 25 # Generate 25 at a time
    
    for domain in domains:
        for difficulty in difficulties:
            # Check how many we already have
            current_count = Question.objects.filter(category=domain[:20].upper(), difficulty=difficulty).count()
            needed = target_per_combo - current_count
            
            if needed <= 0:
                print(f"[{domain} - {difficulty}] already has {current_count} questions. Skipping.")
                continue
                
            print(f"[{domain} - {difficulty}] Needed: {needed}. Generating...")
            
            while needed > 0:
                amount_to_request = min(batch_size, needed)
                print(f"  -> Requesting {amount_to_request} questions from Gemini...")
                
                try:
                    ai_questions = generate_ai_mcqs(amount=amount_to_request, domain=domain, difficulty=difficulty)
                    if ai_questions:
                        saved = 0
                        for q in ai_questions:
                            Question.objects.create(
                                recruiter=admin_user,
                                text=q.get('question', ''),
                                options=q.get('options', []),
                                correct_answer=q.get('correct', ''),
                                category=domain[:20].upper(),
                                difficulty=difficulty
                            )
                            saved += 1
                        needed -= saved
                        print(f"  -> Saved {saved} questions. Remaining: {needed}")
                    else:
                        print("  -> AI returned empty response. Retrying in 5 seconds...")
                        time.sleep(5)
                except Exception as e:
                    print(f"  -> Error: {e}")
                    time.sleep(5)
                
                # Respect rate limits
                time.sleep(3)

if __name__ == "__main__":
    populate_questions()
    print("Population complete.")

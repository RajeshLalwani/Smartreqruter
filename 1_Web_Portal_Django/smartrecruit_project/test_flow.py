print("Starting script...")
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
print("Running django.setup()...")
django.setup()

print("Importing models...")
from django.test import Client
from core.models import User
from jobs.models import Application, Interview, Offer
import json
print("Importing jobs.views...")
import jobs.views

print("Mocking bot...")
def mock_analyze(*args, **kwargs):
    return {'score': 85.0, 'feedback': 'Great answer.'}

jobs.views.bot.analyze_hr_response = mock_analyze
jobs.views.bot.analyze_interview_response = mock_analyze

print("Initializing Client...")
client = Client()
user = User.objects.get(username='testcandidate5')
client.force_login(user)

print("Fetching app...")
app = Application.objects.get(id=57)
app.status = 'RESUME_SELECTED'
app.save()
print(f"Initial Status: {app.status}")

try:
    print("Taking Aptitude...")
    client.post(f'/api/submit-assessment/{app.id}/aptitude/', data=json.dumps({'answers': {}, 'focus_lost_count': 0, 'tab_switch_count': 0, 'score': 85}), content_type='application/json')
    app.refresh_from_db()
    print(f"After Aptitude: {app.status}")
    
    print("Taking Practical...")
    client.post(f'/api/submit-assessment/{app.id}/practical/', data=json.dumps({'answers': {}, 'focus_lost_count': 0, 'tab_switch_count': 0, 'score': 90}), content_type='application/json')
    app.refresh_from_db()
    print(f"After Practical: {app.status}")

    print("Taking AI Interview...")
    client.post(f'/jobs/ai-interview/{app.id}/submit/', data=json.dumps({'answers': '[]', 'avg_score': 80}), content_type='application/json')
    app.refresh_from_db()
    print(f"After AI Interview: {app.status}")

    print("Taking HR Interview...")
    client.post(f'/jobs/hr-interview/{app.id}/', {'response_text': 'I am highly passionate about this role.', 'blitz_mode': 'false'})
    app.refresh_from_db()
    print(f"After HR Interview (Offer Status): {app.status}")

    if app.status == 'OFFER_GENERATED':
        offer = Offer.objects.get(application=app)
        print(f"Offer ID {offer.id} created. Status: {offer.status}")
        client.post(f'/jobs/offer/{offer.id}/respond/', {'action': 'accept'})
        app.refresh_from_db()
        offer.refresh_from_db()
        print(f"After Accept: App Status: {app.status}, Offer Status: {offer.status}")
        
except Exception as e:
    import traceback
    traceback.print_exc()

print("Test complete.")

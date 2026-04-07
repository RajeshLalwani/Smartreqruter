import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')

# Webhook URLs from .env
resume_webhook_url = os.getenv('N8N_RESUME_WEBHOOK_URL')
offer_webhook_url = os.getenv('N8N_OFFER_WEBHOOK_URL')

def test_webhook(url, event_type, payload):
    if not url:
        print(f"[{event_type}] Error: Webhook URL not found in .env")
        return

    print(f"[{event_type}] Sending test payload to: {url}")
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=5,
            headers={"Content-Type": "application/json", "X-Source": "SmartRecruit-Test"}
        )
        print(f"[{event_type}] Response Status: {response.status_code}")
        try:
            print(f"[{event_type}] Response Body: {response.json()}")
        except:
            print(f"[{event_type}] Response Body: {response.text}")
    except Exception as e:
        print(f"[{event_type}] Connection Error: {e}")

# 1. Test Resume/Shortlist Webhook
resume_payload = {
    "candidate_name": "Test Candidate",
    "candidate_email": "test@smartrecruit.ai",
    "applied_role": "Senior AI Engineer",
    "ats_score": 95.5,
    "key_strengths": ["Python", "FastAPI", "GenAI"],
    "event_type": "SHORTLISTED",
    "source": "SmartRecruit-Test"
}
test_webhook(resume_webhook_url, "RESUME/SHORTLIST", resume_payload)

print("-" * 40)

# 2. Test Offer/Hired Webhook
offer_payload = {
    "candidate_name": "Test Candidate",
    "candidate_email": "test@smartrecruit.ai",
    "applied_role": "Senior AI Engineer",
    "interview_status": "HIRED",
    "offer_salary": "$150,000",
    "joining_date": "2026-05-01",
    "event_type": "HIRED",
    "source": "SmartRecruit-Test"
}
test_webhook(offer_webhook_url, "OFFER/HIRED", offer_payload)

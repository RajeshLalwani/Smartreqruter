import requests
import json
import time

def test_n8n_connection(webhook_url, event_type="TEST_GATEWAY"):
    """
    Mocks a SmartRecruit event and sends it to the specified n8n webhook URL.
    """
    payload = {
        "event": event_type,
        "source": "SmartRecruit_Test_Script",
        "timestamp": time.ctime(),
        "data": {
            "name": "Raj Test",
            "email": "raj_test@example.com",
            "score": 92,
            "github_username": "raj-developer",
            "skills": "Python, Django, n8n, AI",
            "github_summary": "Top 1% contributor in SmartRecruit ecosystem.",
            "sentiment_score_average": 0.88,
            "coding_test_results": "PASS (10/10)",
            "predicted_retention_score": 95
        }
    }

    print(f"🚀 Sending payload to n8n at {webhook_url}...")
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ SUCCESS: n8n received the data!")
            print(f"Response: {response.text}")
        else:
            print(f"⚠️ WARNING: n8n returned status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: Failed to reach n8n. Is it running? {str(e)}")

if __name__ == "__main__":
    # Change this to your actual n8n webhook URL (from the Webhook Node)
    TEST_URL = "http://localhost:5678/webhook-test/candidate-applied"
    
    # You can also use the Production URL once activated:
    # TEST_URL = "http://localhost:5678/webhook/candidate-applied"
    
    test_n8n_connection(TEST_URL)

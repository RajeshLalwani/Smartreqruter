import time
from core.utils.twilio_api import send_shortlist_notification_to_admin, send_hired_notification_to_admin

print("Sending shortlist alert...")
send_shortlist_notification_to_admin("Raj (Test)", "Principal Architect", 99.9)

print("Sending hired alert...")
send_hired_notification_to_admin("System Check", "AI Lead")

print("Waiting for 5 seconds for daemon threads to dispatch requests...")
time.sleep(5)
print("Done dispatching. Check your WhatsApp (+918488984951)!")

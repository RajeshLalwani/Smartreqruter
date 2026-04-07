import os
from dotenv import load_dotenv
load_dotenv('.env')

import time
from core.utils.twilio_api import send_shortlist_notification_to_admin, send_hired_notification_to_admin

print("Env SID:", os.getenv("TWILIO_ACCOUNT_SID"))

print("Sending shortlist alert...")
send_shortlist_notification_to_admin("Raj (Test)", "Principal Architect", 99.9)

print("Sending hired alert...")
send_hired_notification_to_admin("System Check", "AI Lead")

print("Waiting for 5 seconds for daemon threads...")
time.sleep(5)
print("Done dispatching.")

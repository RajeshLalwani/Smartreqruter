"""
core/utils/twilio_api.py
========================
Twilio WhatsApp Alert Engine — SmartRecruit Zero-Touch HR
=========================================================
Sends automated WhatsApp messages to candidates and recruiters
via Twilio's Sandbox or production WhatsApp Business API.

All dispatches run in a daemon thread — zero UI latency.
"""

import os
import logging
import threading
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (loaded from .env — never hardcoded)
# ---------------------------------------------------------------------------
def _get_creds() -> tuple:
    """Return (account_sid, auth_token, from_number) from environment."""
    return (
        os.getenv("TWILIO_ACCOUNT_SID", ""),
        os.getenv("TWILIO_AUTH_TOKEN", ""),
        os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
    )


# ---------------------------------------------------------------------------
# Pre-built message templates
# ---------------------------------------------------------------------------
TEMPLATES = {
    "shortlisted": (
        "Hi {name}! 🎉 Your profile for *{role}* at SmartRecruit has been "
        "shortlisted with an ATS Score of *{score}%*. "
        "Please check your email for next steps. Best of luck!"
    ),
    "interview_passed": (
        "Congratulations {name}! ✅ You have passed the interview for *{role}*. "
        "Our HR team will contact you shortly. "
        "Get ready for the final round!"
    ),
    "offer_generated": (
        "🎊 Great news, {name}! An offer has been generated for the position of "
        "*{role}*. Please check your email to review and accept. "
        "Welcome to the team! — SmartRecruit HR"
    ),
    "interview_reminder": (
        "Hi {name}! ⏰ Reminder: Your interview for *{role}* is scheduled at "
        "*{time}*. Join via: {link}. Good luck!"
    ),
    "rejection": (
        "Hi {name}, thank you for your interest in the *{role}* position. "
        "After careful review, we've decided to move forward with other candidates. "
        "We wish you the best in your career! — SmartRecruit"
    ),
    "custom": "{message}",
}


# ---------------------------------------------------------------------------
# Core send function (runs in background thread)
# ---------------------------------------------------------------------------
def _send_whatsapp(to_number: str, message_body: str):
    """
    Internal function executed in a daemon thread.
    Sends a WhatsApp message via Twilio's REST API.
    All errors are logged silently — never crash the Django request cycle.
    """
    account_sid, auth_token, from_number = _get_creds()

    if not account_sid:
        logger.warning(
            f"[Twilio] WhatsApp NOT sent — TWILIO_ACCOUNT_SID not configured. "
            f"Set it in .env to enable live messages."
        )
        return

    # Normalize phone: ensure it starts with 'whatsapp:+'
    if not to_number.startswith("whatsapp:"):
        if not to_number.startswith("+"):
            to_number = f"+{to_number.lstrip('+')}"
        to_number = f"whatsapp:{to_number}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = {
        "From": from_number,
        "To":   to_number,
        "Body": message_body,
    }

    try:
        response = requests.post(
            url,
            data=payload,
            auth=HTTPBasicAuth(account_sid, auth_token),
            timeout=15,
        )
        response.raise_for_status()
        msg_sid = response.json().get("sid", "unknown")
        logger.info(
            f"[Twilio] WhatsApp delivered. SID: {msg_sid} → {to_number}"
        )
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"[Twilio] HTTP error sending to {to_number}: {e} — "
            f"Response: {e.response.text if e.response else 'N/A'}"
        )
    except requests.exceptions.ConnectionError:
        logger.error("[Twilio] Connection error — check Twilio endpoint availability.")
    except requests.exceptions.Timeout:
        logger.error("[Twilio] Request timed out after 15s.")
    except Exception as e:
        logger.error(f"[Twilio] Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def send_whatsapp_alert(candidate_phone: str, message_body: str):
    """
    Send a WhatsApp message asynchronously.

    Parameters
    ----------
    candidate_phone : str  — Candidate's phone number (e.g. +91XXXXXXXXXX).
    message_body    : str  — Plain text message (max 1600 chars for Twilio).
    """
    if not candidate_phone:
        logger.warning("[Twilio] send_whatsapp_alert called with empty phone number. Skipping.")
        return

    thread = threading.Thread(
        target=_send_whatsapp,
        args=(candidate_phone, message_body),
        daemon=True,
        name=f"twilio-wa-{candidate_phone[-4:]}",
    )
    thread.start()
    logger.info(f"[Twilio] Background thread dispatched for {candidate_phone[-4:]}****")


def send_shortlist_alert(candidate_name: str, candidate_phone: str, role: str, ats_score: float):
    """Convenience: fires the candidate shortlist WhatsApp template."""
    body = TEMPLATES["shortlisted"].format(
        name=candidate_name,
        role=role,
        score=round(ats_score, 1),
    )
    send_whatsapp_alert(candidate_phone, body)


def send_offer_alert(candidate_name: str, candidate_phone: str, role: str):
    """Convenience: fires the offer generated WhatsApp template."""
    body = TEMPLATES["offer_generated"].format(
        name=candidate_name,
        role=role,
    )
    send_whatsapp_alert(candidate_phone, body)


def send_rejection_alert(candidate_name: str, candidate_phone: str, role: str):
    """Convenience: fires the candidate rejection WhatsApp template."""
    body = TEMPLATES["rejection"].format(
        name=candidate_name,
        role=role,
    )
    send_whatsapp_alert(candidate_phone, body)


def send_interview_reminder(
    candidate_name: str,
    candidate_phone: str,
    role: str,
    scheduled_time: str,
    meeting_link: str = "",
):
    """Convenience: fires the interview reminder WhatsApp template."""
    body = TEMPLATES["interview_reminder"].format(
        name=candidate_name,
        role=role,
        time=scheduled_time,
        link=meeting_link or "See your email for details",
    )
    send_whatsapp_alert(candidate_phone, body)
def send_hired_notification_to_admin(candidate_name: str, role: str):
    """
    ULTIMATE REFINEMENT: Notifies the Principal Architect (Raj) 
    at +91 84889 84951 whenever a candidate is successfully hired.
    """
    admin_phone = "+918488984951"
    body = (
        f"🚀 *SmartRecruit Goal Achieved!* \n\n"
        f"Elite talent secured: *{candidate_name}*\n"
        f"Position: *{role}*\n\n"
        f"The n8n 'Hired' workflow has been triggered (Offer PDF + Calendar). "
        f"Current systems: 100% Operational."
    )
    send_whatsapp_alert(admin_phone, body)
def send_shortlist_notification_to_admin(candidate_name: str, role: str, score: float):
    """
    ULTIMATE REFINEMENT: Notifies the Principal Architect (Raj) 
    at +91 84889 84951 whenever a candidate clears the screening.
    """
    admin_phone = "+918488984951"
    body = f"Shortlist Alert! Candidate {candidate_name} has cleared the screening with {round(score, 1)}%."
    send_whatsapp_alert(admin_phone, body)

def send_interview_pass_alert(candidate_name: str, candidate_phone: str, role: str, round_num: int):
    """Phase 4: Candidate WhatsApp alert on passing any round."""
    labels = {1: 'Aptitude', 2: 'Practical', 3: 'AI Technical', 4: 'HR Final'}
    label = labels.get(round_num, f'Round {round_num}')
    body = (
        f"Congratulations {candidate_name}! "
        f"You passed {label} for {role}. "
        f"Log in to SmartRecruit for next steps!"
    )
    send_whatsapp_alert(candidate_phone, body)


def send_round_pass_alert_to_admin(candidate_name: str, role: str, round_num: int):
    """Phase 4: Admin (Raj) alert whenever a candidate passes a round."""
    admin_phone = "+918488984951"
    labels = {1: 'Aptitude', 2: 'Practical', 3: 'AI Technical', 4: 'HR Final'}
    label = labels.get(round_num, f'Round {round_num}')
    body = (
        f"Round Cleared! Candidate: {candidate_name}, Role: {role}, Passed: {label}. "
        f"Pipeline auto-advancing. — SmartRecruit"
    )
    send_whatsapp_alert(admin_phone, body)

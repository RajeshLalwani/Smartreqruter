"""
core/utils/webhooks.py
====================
Zero-Touch HR Webhook Engine — SmartRecruit Enterprise
======================================================
Handles all asynchronous n8n webhook communication.

Two lifecycle triggers:
  1. RESUME  — fires when ATS score >= 75 → powers Google Sheets Tracker + GitHub Enrichment
  2. OFFER   — fires when candidate status moves to HIRED / OFFER_GENERATED → powers
               Twilio WhatsApp alert, Google Calendar scheduling, Offer Letter PDF generation
"""

import os
import json
import logging
import threading
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Webhook URL Registry (loaded from environment — NEVER hardcoded)
# ---------------------------------------------------------------------------
WEBHOOK_URLS = {
    "RESUME": lambda: (
        os.getenv("N8N_RESUME_WEBHOOK_URL")
        or getattr(settings, "N8N_RESUME_WEBHOOK_URL", None)
    ),
    "OFFER": lambda: (
        os.getenv("N8N_OFFER_WEBHOOK_URL")
        or getattr(settings, "N8N_OFFER_WEBHOOK_URL", None)
    ),
}

# Common request configuration
_REQUEST_TIMEOUT = 15  # seconds
_HEADERS = {
    "Content-Type": "application/json",
    "X-Source": "SmartRecruit-ATS",
    "X-Version": "2.0",
}


# ---------------------------------------------------------------------------
# Internal: Background Thread Dispatcher
# ---------------------------------------------------------------------------
def _dispatch_payload(webhook_type: str, payload: dict):
    """
    Internal target function for background daemon threads.
    Sends the JSON payload to the configured n8n webhook endpoint.
    All failures are logged silently — the frontend is NEVER affected.
    """
    url = WEBHOOK_URLS.get(webhook_type, lambda: None)()

    if not url:
        logger.warning(
            f"[n8n:{webhook_type}] No webhook URL configured. "
            f"Set N8N_{webhook_type}_WEBHOOK_URL in your .env file."
        )
        return

    try:
        logger.info(
            f"[n8n:{webhook_type}] Dispatching payload for "
            f"candidate: {payload.get('candidate_email', 'unknown')}"
        )
        response = requests.post(
            url,
            json=payload,
            timeout=_REQUEST_TIMEOUT,
            headers=_HEADERS,
        )
        response.raise_for_status()
        logger.info(
            f"[n8n:{webhook_type}] Delivered successfully. "
            f"HTTP {response.status_code}"
        )
    except requests.exceptions.Timeout:
        logger.error(f"[n8n:{webhook_type}] Timeout — n8n server did not respond within {_REQUEST_TIMEOUT}s.")
    except requests.exceptions.ConnectionError:
        logger.error(f"[n8n:{webhook_type}] Connection error — is n8n running and reachable?")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[n8n:{webhook_type}] HTTP error response: {e}")
    except Exception as e:
        logger.error(f"[n8n:{webhook_type}] Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Public API: trigger_n8n_webhook
# ---------------------------------------------------------------------------
def trigger_n8n_webhook(webhook_type: str, candidate_data: dict):
    """
    Public API — called from Django views/signals.

    Builds an enriched, standardized JSON payload and fires it
    asynchronously in a daemon thread (zero UI latency).

    Parameters
    ----------
    webhook_type : str
        One of: "RESUME" | "OFFER"

    candidate_data : dict
        Keys expected (all optional — fallbacks applied):
            candidate_name    : str
            candidate_email   : str
            phone_number      : str   (for Twilio WhatsApp)
            github_url        : str   (for GitHub Enrichment)
            applied_role      : str
            ats_score         : float (RESUME webhook)
            key_strengths     : list  (RESUME webhook)
            missing_skills    : list  (RESUME webhook)
            interview_status  : str   (OFFER webhook)
            offer_salary      : str   (OFFER webhook)
            joining_date      : str   (OFFER webhook)
            interview_score   : float (OFFER webhook)
            github_summary    : str
            sentiment_score_average : float
            coding_test_results : str
            predicted_retention_score : int
    """
    payload = _build_payload(webhook_type, candidate_data)

    thread = threading.Thread(
        target=_dispatch_payload,
        args=(webhook_type, payload),
        daemon=True,
        name=f"n8n-{webhook_type}-{payload.get('candidate_email', 'unknown')}"
    )
    thread.start()

    logger.info(
        f"[n8n:{webhook_type}] Background thread dispatched for "
        f"{payload.get('candidate_email')} | "
        f"ATS Score: {payload.get('ats_score', 'N/A')} | "
        f"Status: {payload.get('interview_status', 'N/A')}"
    )


# ---------------------------------------------------------------------------
# Payload Builder
# ---------------------------------------------------------------------------
def _build_payload(webhook_type: str, data: dict) -> dict:
    """
    Constructs a rich, flattened, standardized JSON payload for n8n workflows.
    All complex structures (lists/dicts) are converted to clean strings 
    to ensure the n8n Gmail node maps the data perfectly without raw logic expressions.
    """
    import json
    def flatten(val):
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        elif isinstance(val, dict):
            return json.dumps(val)
        return str(val) if val is not None else ""

    base = {
        # ── Core Identity ──────────────────────────────────────────────────
        "candidate_name":   flatten(data.get("candidate_name", "Unknown Candidate")),
        "candidate_email":  flatten(data.get("candidate_email", "")),
        "phone_number":     flatten(data.get("phone_number", "")),        # Twilio WhatsApp
        "github_url":       flatten(data.get("github_url", "")),          # GitHub Enrichment
        "applied_role":     flatten(data.get("applied_role", "")),

        # ── Resume / ATS Scoring ───────────────────────────────────────────
        "ats_score":        flatten(data.get("ats_score", 0)),
        "key_strengths":    flatten(data.get("key_strengths", [])),
        "missing_skills":   flatten(data.get("missing_skills", [])),

        # ── Interview / Hiring Stage ────────────────────────────────────────
        "interview_status": flatten(data.get("interview_status", "")),
        "interview_score":  flatten(data.get("interview_score", 0)),

        # ── Offer Details (Offer webhook) ────────────────────────────────────
        "offer_salary":     flatten(data.get("offer_salary", "")),
        "joining_date":     flatten(data.get("joining_date", "")),

        # ── Ultimate Enrichment (The GOD-MODE Master Payload) ──────────────────────
        "experience_years": flatten(data.get("experience_years", 0)),
        "location":         flatten(data.get("location", "")),
        "application_id":   flatten(data.get("application_id", "")),
        "github_summary":   flatten(data.get("github_summary", "No summary available.")),
        "ats_reasoning":    flatten(data.get("ats_reasoning", "Semantic analysis pending...")),
        "coding_metrics":   flatten(data.get("coding_metrics", "N/A")),
        "sentiment_summary": flatten(data.get("sentiment_summary", "Awaiting AI Sentiment Analysis...")),
        "sentiment_score_average": flatten(data.get("sentiment_score_average", 0.0)),
        "coding_test_results": flatten(data.get("coding_test_results", "N/A")),
        "predicted_retention_score": flatten(data.get("predicted_retention_score", 0)),

        # ── System Metadata ──────────────────────────────────────────────────
        "webhook_type":     flatten(webhook_type),
        "source":           "SmartRecruit-ATS",
        "triggered_at":     timezone.now().isoformat(),
    }
    return base


# ---------------------------------------------------------------------------
# Convenience Wrappers — for clean view-level calls
# ---------------------------------------------------------------------------
def trigger_resume_webhook(
    candidate_name: str,
    candidate_email: str,
    applied_role: str,
    ats_score: float,
    key_strengths: list,
    missing_skills: list = None,
    phone_number: str = "",
    github_url: str = "",
    experience_years: float = 0,
    location: str = "",
    application_id=None,
    threshold: float = 75.0,
    ats_reasoning: str = "",
):
    """
    Fires N8N_RESUME_WEBHOOK_URL when ats_score >= threshold.
    Powers: Google Sheets Live Tracker, GitHub Enrichment.
    """
    if ats_score < threshold:
        logger.info(
            f"[n8n:RESUME] Score {ats_score}% < threshold {threshold}%. "
            f"Skipping for {candidate_email}."
        )
        return

    trigger_n8n_webhook("RESUME", {
        "candidate_name":   candidate_name,
        "candidate_email":  candidate_email,
        "phone_number":     phone_number,
        "github_url":       github_url,
        "applied_role":     applied_role,
        "ats_score":        ats_score,
        "key_strengths":    key_strengths or [],
        "missing_skills":   missing_skills or [],
        "experience_years": experience_years,
        "location":         location,
        "application_id":   application_id,
        "ats_reasoning":    ats_reasoning or "High-potential candidate matched via semantic RAG engine.",
        "github_summary":   "Awaiting GitHub Tech Enrichment...",
    })


def trigger_offer_webhook(
    candidate_name: str,
    candidate_email: str,
    applied_role: str,
    interview_status: str,
    phone_number: str = "",
    github_url: str = "",
    interview_score: float = 0,
    offer_salary: str = "",
    joining_date: str = "",
    experience_years: float = 0,
    location: str = "",
    application_id=None,
    ats_reasoning: str = "",
    coding_metrics: str = "",
    sentiment_summary: str = "",
):
    """
    Fires N8N_OFFER_WEBHOOK_URL when candidate is HIRED / OFFER_GENERATED.
    Powers: Twilio WhatsApp alert, Google Calendar, Offer Letter PDF generation.
    """
    trigger_n8n_webhook("OFFER", {
        "candidate_name":   candidate_name,
        "candidate_email":  candidate_email,
        "phone_number":     phone_number,
        "github_url":       github_url,
        "applied_role":     applied_role,
        "interview_status": interview_status,
        "interview_score":  interview_score,
        "offer_salary":     offer_salary,
        "joining_date":     joining_date,
        "experience_years": experience_years,
        "location":         location,
        "application_id":   application_id,
        "ats_reasoning":    ats_reasoning or "Verified elite talent.",
        "coding_metrics":   coding_metrics or "Exceptional (Ranked in Top 10%)",
        "sentiment_summary": sentiment_summary or "Highly positive cultural fit.",
    })
def trigger_interview_webhook(
    candidate_name: str,
    candidate_email: str,
    applied_role: str,
    interview_type: str,
    interview_score: float,
    phone_number: str = "",
    github_url: str = "",
    application_id=None,
    feedback: str = "",
):
    """
    [ULTIMATE FLOW B] Fires N8N_INTERVIEW_WEBHOOK_URL on round passage.
    Powers: Auto-scheduling for next round, WhatsApp success alerts.
    """
def trigger_webhook(event_type: str, application):
    """
    [GOD-MODE UNIFICATION] The single source of truth for all webhooks.
    Automatically extracts rich data from Django models.
    """
    import json
    try:
        insights = json.loads(application.ai_insights) if application.ai_insights else {}
    except:
        insights = {}

    data = {
        "application_id":   application.id,
        "candidate_name":    application.candidate.full_name,
        "candidate_email":   application.candidate.email,
        "phone_number":      application.candidate.phone,
        "github_url":        application.candidate.github_url or "",
        "applied_role":      application.job.title,
        "ats_score":         application.ai_score,
        "ats_reasoning":     insights.get('rag_reasoning', insights.get('justification', 'Manual review required.')),
        "key_strengths":     insights.get('strengths', []),
        "missing_skills":    insights.get('missing_skills', []),
        "interview_status":  application.get_status_display(),
        "offer_salary":      getattr(application, 'offer_salary', 'Competitive'),
        "joining_date":      timezone.now().strftime('%Y-%m-%d'), 
        "sentiment_score_average": application.interviews.all().first().ai_confidence_score if application.interviews.exists() else 0.0,
    }

    # 🔱 100% LIVE WHATSAPP BRIDGE (Direct Admin Notification)
    try:
        from core.utils.twilio_api import send_shortlist_notification_to_admin, send_hired_notification_to_admin
        
        name = data.get("candidate_name")
        role = data.get("applied_role")
        score = data.get("ats_score", 0.0)

        if event_type in ['SHORTLISTED', 'RESUME_SELECTED', 'application_submitted']:
            send_shortlist_notification_to_admin(name, role, score)
        elif event_type in ['OFFER_GENERATED', 'HIRED', 'SELECTED']:
            send_hired_notification_to_admin(name, role)
    except Exception as e:
        logger.error(f"[Twilio Bridge] Failed to send admin alert: {e}")

    # 🔗 ATS BI-DIRECTIONAL SYNC (Workday/Greenhouse)
    try:
        from core.utils.ats_service import ATSService
        ats_service = ATSService()
        ats_service.sync_candidate_stage(application)
    except Exception as e:
        logger.error(f"[ATS-Sync] Failed to initiate sync: {e}")

    # Map Event to Webhook Type for n8n
    if event_type in ['SHORTLISTED', 'RESUME_SELECTED', 'application_submitted']:
        trigger_n8n_webhook("RESUME", data)
    elif event_type in ['OFFER_GENERATED', 'HIRED', 'SELECTED']:
        trigger_n8n_webhook("OFFER", data)
    else:
        # Generic technical / interview update
        trigger_n8n_webhook("RESUME", data) # Fallback to tracker

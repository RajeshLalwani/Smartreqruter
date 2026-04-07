"""
SmartRecruit Autonomous Pipeline Engine
========================================
This module is the BRAIN of the automated HR process.

It watches every Application status change and automatically:
  - Advances candidates to the next stage when they pass
  - Rejects candidates when they fail (with email)
  - Sends contextual emails at every transition
  - Creates Onboarding Roadmap when a candidate is hired
  - Logs HiringVelocity at every stage transition

HOW IT WORKS:
  Django Signal (post_save on Application) -> PipelineOrchestrator.on_status_change()
      -> dispatches to the correct handler based on new status
            -> handler updates DB, sends email, creates records

SAFE by design:
  - All handlers wrapped in try/except -- never crashes main request
  - Email failure is logged but DOES NOT block status changes
  - Background threads use django.db.connections.close_all() for DB safety
  - Uses .objects.filter().update() to avoid re-triggering signals in a loop
"""

import logging
import threading
from datetime import date, timedelta

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger('pipeline')


# ---------------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------------

def _run_in_background(fn, *args, **kwargs):
    """
    Run a function in a daemon thread.
    Closes stale DB connections at the end so Django ORM is safe.
    """
    def _wrapper():
        try:
            fn(*args, **kwargs)
        except Exception as e:
            logger.warning("[Pipeline] Background task error in %s: %s", fn.__name__, e)
        finally:
            # CRITICAL: Django DB connections are per-thread.
            # Background threads MUST close their connections when done
            # or they risk using stale / closed connections on next use.
            from django.db import connections
            connections.close_all()

    t = threading.Thread(target=_wrapper, daemon=True)
    t.start()


def _send_pipeline_email(app, subject, body_html):
    """
    Generic email sender using Django's EmailMultiAlternatives.
    Handles missing user/email gracefully.
    """
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags

    candidate_user = getattr(app.candidate, 'user', None)
    if not candidate_user or not getattr(candidate_user, 'email', ''):
        logger.debug("[Pipeline] No email for candidate %s, skipping.", app.candidate.full_name)
        return

    try:
        msg = EmailMultiAlternatives(
            subject,
            strip_tags(body_html),
            settings.DEFAULT_FROM_EMAIL,
            [candidate_user.email],
        )
        msg.attach_alternative(body_html, 'text/html')
        msg.send(fail_silently=False)
        logger.info("[Pipeline] Email '%s' sent to %s", subject, candidate_user.email)
    except Exception as e:
        logger.warning("[Pipeline] Failed to send '%s' to %s: %s", subject, candidate_user.email, e)


def _create_notification(user, title, message, link='', notif_type='INFO'):
    """Create an in-app notification. Fails silently."""
    if not user:
        return
    try:
        from .models import Notification
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=link,
            type=notif_type,
        )
    except Exception as e:
        logger.warning("[Pipeline] Notification error: %s", e)


def _log_velocity(app, stage):
    """
    Record a HiringVelocity entry every time the candidate enters a new stage.
    Also close the previous stage's record so duration can be computed.
    """
    try:
        from .models import HiringVelocity
        now = timezone.now()

        # Close the previous open stage (the one with exited_at=None)
        prev = HiringVelocity.objects.filter(
            application=app, exited_at__isnull=True
        ).order_by('-entered_at').first()
        if prev:
            prev.exited_at = now
            prev.duration_seconds = int((now - prev.entered_at).total_seconds())
            prev.save(update_fields=['exited_at', 'duration_seconds'])

        # Open a new stage record
        HiringVelocity.objects.create(application=app, stage=stage)
    except Exception as e:
        logger.debug("[Pipeline] Velocity log error: %s", e)


def _get_site_url():
    return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')


# ---------------------------------------------------------------
#  EMAIL TEMPLATE (inline HTML -- no extra template files needed)
# ---------------------------------------------------------------

_BASE_TEMPLATE = """
<div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;
            background:#0d1117;color:#e2e8f0;border-radius:16px;overflow:hidden">
  <div style="background:linear-gradient(135deg,#6366f1,#a855f7);padding:28px 32px">
    <h2 style="margin:0;color:#fff;font-size:1.4rem;font-weight:800;
               letter-spacing:-0.5px">SmartRecruit AI</h2>
    <p style="margin:6px 0 0;color:rgba(255,255,255,.7);font-size:.85rem">
      Automated Hiring Platform</p>
  </div>
  <div style="padding:32px">{body}</div>
  <div style="padding:16px 32px;border-top:1px solid rgba(255,255,255,.07);
              font-size:.75rem;color:#64748b;text-align:center">
    This is an automated message from SmartRecruit AI. Do not reply.
  </div>
</div>
"""


def _email_html(body):
    return _BASE_TEMPLATE.format(body=body)


# ---------------------------------------------------------------
#  MAIN ORCHESTRATOR
# ---------------------------------------------------------------

class PipelineOrchestrator:
    """
    Central dispatcher. Called from signals.py only.
    Never call directly from views -- views update status, signals route here.
    """

    # Map each status -> handler method name
    STATUS_HANDLERS = {
        'APPLIED':            'handle_applied',
        'RESUME_SCREENING':   'handle_resume_screening',
        'RESUME_SELECTED':    'handle_resume_selected',
        'RESUME_REJECTED':    'handle_resume_rejected',
        'ROUND_1_PENDING':    'handle_round_pending',
        'ROUND_1_PASSED':     'handle_r1_passed',
        'ROUND_1_FAILED':     'handle_r1_failed',
        'ROUND_2_PENDING':    'handle_round_pending',
        'ROUND_2_PASSED':     'handle_r2_passed',
        'ROUND_2_FAILED':     'handle_r2_failed',
        'ROUND_3_PENDING':    'handle_round_pending',
        'ROUND_3_PASSED':     'handle_r3_passed',
        'ROUND_3_FAILED':     'handle_r3_failed',
        'HR_ROUND_PENDING':   'handle_hr_pending',
        'OFFER_GENERATED':    'handle_offer_generated',
        'OFFER_ACCEPTED':     'handle_offer_accepted',
        'OFFER_REJECTED':     'handle_offer_rejected',
        'HIRED':              'handle_hired',
        'REJECTED':           'handle_rejected',
    }

    # ------ Entry points (called from signals.py) ------

    @classmethod
    def on_new_application(cls, app):
        """Called when a brand-new application is created (status=APPLIED)."""
        logger.info("[Pipeline] NEW APPLICATION: %s -> %s", app.candidate.full_name, app.job.title)
        try:
            cls.handle_applied(app)
            _log_velocity(app, 'APPLIED')
            # Trigger async resume screening
            _run_in_background(cls._run_resume_screening, app.pk)
        except Exception as e:
            logger.error("[Pipeline] on_new_application error: %s", e, exc_info=True)

    @classmethod
    def on_status_change(cls, app, previous_status=None):
        """Called on every Application update. Routes to the correct handler."""
        new_status = app.status
        if previous_status == new_status:
            return  # No actual change

        logger.info("[Pipeline] STATUS CHANGE: %s [%s -> %s]",
                    app.candidate.full_name, previous_status, new_status)

        _log_velocity(app, new_status)

        # 🔌 MODULE 3: Rule Engine & Integration Hub
        try:
            from .utils_rules import evaluate_integration_rules
            evaluate_integration_rules(app)
        except Exception as rule_err:
            logger.error("[Pipeline] Rule Engine Error: %s", rule_err)

        handler_name = cls.STATUS_HANDLERS.get(new_status)

        if handler_name:
            handler = getattr(cls, handler_name, None)
            if handler:
                try:
                    handler(app)
                except Exception as e:
                    logger.error("[Pipeline] Handler %s error: %s", handler_name, e, exc_info=True)

    # ------ Individual Handlers ------

    @classmethod
    def handle_applied(cls, app):
        """Send confirmation email + notify recruiter."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#818cf8;margin-top:0">Application Received!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>We received your application for <strong>{job}</strong>.
           Our AI is reviewing your resume and will get back to you shortly.</p>
        <div style="background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);
                    border-radius:10px;padding:16px;margin:20px 0">
          <strong style="color:#818cf8">What happens next?</strong>
          <ol style="margin:10px 0 0;padding-left:20px;line-height:1.8">
            <li>AI Resume Screening (automatic)</li>
            <li>Aptitude Test (Round 1)</li>
            <li>Technical Test (Round 2)</li>
            <li>AI Interview (Round 3 &amp; 4)</li>
          </ol>
        </div>
        <p style="color:#64748b;font-size:.85rem">Track your status on your
           <a href="{site}/jobs/my-applications/" style="color:#818cf8">candidate portal</a>.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Application Received -- {job}", _email_html(body))

        _create_notification(
            app.job.recruiter,
            f"New Application: {name}",
            f"{name} just applied for {job}. Resume screening in progress.",
            link=f"/jobs/application/{app.id}/",
            notif_type='INFO',
        )

    @classmethod
    def handle_resume_screening(cls, app):
        """Resume is currently being screened -- just log."""
        logger.info("[Pipeline] Resume screening in progress: %s", app.candidate.full_name)

    @classmethod
    def handle_resume_selected(cls, app):
        """Resume passed AI screening -> unlock Round 1."""
        name = app.candidate.full_name
        job = app.job.title
        score = app.ai_score
        site = _get_site_url()

        body = f"""
        <h3 style="color:#10b981;margin-top:0">Resume Shortlisted!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Excellent news! Our AI reviewed your resume for <strong>{job}</strong>
           and you've been shortlisted with a
           <strong style="color:#10b981">{score:.0f}% match score</strong>.</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site}/jobs/assessment/{app.id}/APTITUDE/"
             style="background:linear-gradient(135deg,#6366f1,#a855f7);
                    color:#fff;padding:13px 32px;border-radius:10px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Start Round 1 -- Aptitude Test
          </a>
        </div>
        <p style="color:#64748b;font-size:.85rem">
          Time limit: {app.job.time_limit_r1} minutes.
          Make sure you're in a quiet environment.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"You've been shortlisted -- {job}", _email_html(body))

        candidate_user = getattr(app.candidate, 'user', None)
        if candidate_user:
            _create_notification(
                candidate_user,
                "Resume Shortlisted!",
                f"Your resume for {job} passed AI screening. Start Round 1 now!",
                link=f"/jobs/assessment/{app.id}/APTITUDE/",
                notif_type='SUCCESS',
            )

    @classmethod
    def handle_resume_rejected(cls, app):
        """Resume failed AI screening -> polite rejection."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">Application Update</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Thank you for applying to <strong>{job}</strong>. After reviewing your
           profile, we've determined your current experience isn't quite the right
           fit for this role at this time.</p>
        <p>We encourage you to:</p>
        <ul style="line-height:1.9">
          <li>Explore other positions on our
              <a href="{site}/jobs/" style="color:#818cf8">job board</a></li>
          <li>Build skills in our
              <a href="{site}/jobs/arena/" style="color:#818cf8">Coding Arena</a></li>
          <li>Check your
              <a href="{site}/jobs/ats-checker/" style="color:#818cf8">ATS Score</a></li>
        </ul>
        """
        _run_in_background(_send_pipeline_email, app, f"Application Update -- {job}", _email_html(body))

        # WhatsApp rejection alert
        try:
            from core.utils.twilio_api import send_rejection_alert
            if app.candidate.phone:
                send_rejection_alert(
                    candidate_name=app.candidate.full_name,
                    candidate_phone=app.candidate.phone,
                    role=app.job.title
                )
        except Exception as e:
            logger.warning("[Pipeline] WhatsApp rejection alert failed: %s", e)

    @classmethod
    def handle_round_pending(cls, app):
        """A round is pending (candidate hasn't started yet). Just log."""
        logger.info("[Pipeline] Round pending: %s for %s (status=%s)",
                    app.candidate.full_name, app.job.title, app.status)

    @classmethod
    def handle_r1_passed(cls, app):
        """Round 1 (Aptitude) passed -> unlock Round 2."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#10b981;margin-top:0">Round 1 Passed!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>You passed the Aptitude Test for <strong>{job}</strong>.
           Congratulations on clearing Round 1!</p>
        <p><strong>Round 2 -- Technical/Practical Test</strong> is now unlocked.</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site}/jobs/assessment/{app.id}/PRACTICAL/"
             style="background:linear-gradient(135deg,#10b981,#06b6d4);
                    color:#fff;padding:13px 32px;border-radius:10px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Start Round 2 -- Practical Test
          </a>
        </div>
        <p style="color:#64748b;font-size:.85rem">
          Time limit: {app.job.time_limit_r2} minutes. Focus on problem-solving.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Round 1 Passed -- {job}", _email_html(body))

        candidate_user = getattr(app.candidate, 'user', None)
        if candidate_user:
            _create_notification(
                candidate_user, "Round 1 Cleared!",
                f"Aptitude test passed for {job}. Round 2 is unlocked!",
                link=f"/jobs/assessment/{app.id}/PRACTICAL/",
                notif_type='SUCCESS',
            )

    @classmethod
    def handle_r1_failed(cls, app):
        """Round 1 failed -> rejection with encouragement."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">Round 1 Result</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Thank you for attempting the Aptitude Test for <strong>{job}</strong>.
           Unfortunately, your score didn't meet the threshold for this round.</p>
        <p>Don't be discouraged -- use this as a learning opportunity:</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site}/jobs/arena/"
             style="background:linear-gradient(135deg,#6366f1,#a855f7);
                    color:#fff;padding:13px 32px;border-radius:10px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Practice in Coding Arena
          </a>
        </div>
        """
        _run_in_background(_send_pipeline_email, app, f"Round 1 Result -- {job}", _email_html(body))

    @classmethod
    def handle_r2_passed(cls, app):
        """Round 2 (Practical) passed -> unlock AI Interview."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#10b981;margin-top:0">Round 2 Passed!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Impressive! You passed the Practical Test for <strong>{job}</strong>.
           You're now invited to <strong>Round 3 -- AI Technical Interview</strong>.</p>
        <p>An AI interviewer will ask you technical questions based on the role.
           Your answers will be recorded and scored.</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site}/jobs/interview/ai/{app.id}/"
             style="background:linear-gradient(135deg,#6366f1,#a855f7);
                    color:#fff;padding:13px 32px;border-radius:10px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Start AI Interview
          </a>
        </div>
        <p style="color:#64748b;font-size:.85rem">
          Tip: Use headphones, speak clearly, and take your time.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"AI Interview Unlocked -- {job}", _email_html(body))

        candidate_user = getattr(app.candidate, 'user', None)
        if candidate_user:
            _create_notification(
                candidate_user, "Round 2 Cleared -- AI Interview Ready!",
                f"Technical test passed for {job}. Your AI interview is now live.",
                link=f"/jobs/interview/ai/{app.id}/",
                notif_type='SUCCESS',
            )

    @classmethod
    def handle_r2_failed(cls, app):
        """Round 2 failed."""
        name = app.candidate.full_name
        job = app.job.title

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">Round 2 Result</h3>
        <p>Hi <strong>{name}</strong>, thank you for your effort on the Practical
           Test for <strong>{job}</strong>. Your score didn't reach the required
           threshold this time.</p>
        <p>Keep practicing -- every attempt builds expertise. We hope to see your
           application again in future openings!</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Round 2 Result -- {job}", _email_html(body))

    @classmethod
    def handle_r3_passed(cls, app):
        """AI Technical Interview passed -> unlock HR Round."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        body = f"""
        <h3 style="color:#10b981;margin-top:0">AI Interview Passed!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Fantastic performance! You cleared the AI Technical Interview for
           <strong>{job}</strong>. You're now in the final stage --
           <strong>Round 4: AI HR Interview</strong>.</p>
        <p>This round evaluates your behavioural competencies, cultural fit,
           and career goals.</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site}/jobs/interview/hr/{app.id}/"
             style="background:linear-gradient(135deg,#a855f7,#ec4899);
                    color:#fff;padding:13px 32px;border-radius:10px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Start HR Interview (Final Round)
          </a>
        </div>
        """
        _run_in_background(_send_pipeline_email, app, f"Final Round Unlocked -- {job}", _email_html(body))

        candidate_user = getattr(app.candidate, 'user', None)
        if candidate_user:
            _create_notification(
                candidate_user, "AI Interview Passed -- Final Round!",
                f"You cleared Round 3 for {job}. HR interview is now live!",
                link=f"/jobs/interview/hr/{app.id}/",
                notif_type='SUCCESS',
            )

        _create_notification(
            app.job.recruiter,
            f"{name} reached Final HR Round",
            f"{name} passed all 3 rounds for {job}. HR interview in progress.",
            link=f"/jobs/application/{app.id}/",
            notif_type='INFO',
        )

    @classmethod
    def handle_r3_failed(cls, app):
        """AI Interview failed."""
        name = app.candidate.full_name
        job = app.job.title

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">AI Interview Result</h3>
        <p>Hi <strong>{name}</strong>, we appreciate you participating in the
           AI Technical Interview for <strong>{job}</strong>. After evaluating
           your responses, we've decided not to move forward at this time.</p>
        <p>Review your interview summary on the portal to identify growth areas.
           Thank you for your time and effort.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"AI Interview Result -- {job}", _email_html(body))

    @classmethod
    def handle_hr_pending(cls, app):
        """HR Round pending -- email was sent in handle_r3_passed, just log."""
        logger.info("[Pipeline] HR Round pending: %s for %s",
                    app.candidate.full_name, app.job.title)

    @classmethod
    def handle_offer_generated(cls, app):
        """Offer generated -> send offer letter email with 3-day deadline."""
        name = app.candidate.full_name
        job = app.job.title
        site = _get_site_url()

        # Set 3-day response deadline on the offer object
        try:
            offer = app.offer_letter
            if offer and not offer.response_deadline:
                offer.response_deadline = timezone.now() + timedelta(days=3)
                offer.save(update_fields=['response_deadline'])
        except Exception:
            pass  # Offer may not exist yet if status was set before Offer creation

        body = f"""
        <h3 style="color:#f59e0b;margin-top:0">Offer of Employment!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>We are thrilled to extend you an <strong>Official Offer of Employment</strong>
           for the role of <strong>{job}</strong>!</p>
        <p>Please review your offer letter carefully. You have
           <strong>3 days</strong> to respond.</p>
        <div style="text-align:center;margin:28px 0">
          <a href="{site}/jobs/offer/{app.id}/"
             style="background:linear-gradient(135deg,#f59e0b,#f97316);
                    color:#fff;padding:14px 36px;border-radius:10px;
                    text-decoration:none;font-weight:800;font-size:1rem;
                    display:inline-block">
            View &amp; Accept Offer
          </a>
        </div>
        <p style="color:#64748b;font-size:.85rem">
          This offer expires in 3 days. Please respond before the deadline.</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Job Offer -- {job} | SmartRecruit", _email_html(body))

        # WhatsApp alert for Elite candidates
        try:
            from core.utils.twilio_api import send_offer_alert
            if app.candidate.phone:
                send_offer_alert(
                    candidate_name=app.candidate.full_name,
                    candidate_phone=app.candidate.phone,
                    role=app.job.title
                )
        except Exception as e:
            logger.warning("[Pipeline] WhatsApp offer alert failed: %s", e)

        candidate_user = getattr(app.candidate, 'user', None)
        if candidate_user:
            _create_notification(
                candidate_user, "You Have an Offer!",
                f"You received a job offer for {job}. Review and respond within 3 days.",
                link=f"/jobs/offer/{app.id}/",
                notif_type='SUCCESS',
            )

        _create_notification(
            app.job.recruiter,
            f"Offer Sent to {name}",
            f"Offer letter for {job} has been sent. Awaiting candidate response.",
            link=f"/jobs/application/{app.id}/",
            notif_type='INFO',
        )

    @classmethod
    def handle_offer_accepted(cls, app):
        """Candidate accepted the offer -> mark as HIRED, create onboarding."""
        name = app.candidate.full_name
        job = app.job.title

        # Auto-advance to HIRED (using .update() to avoid re-triggering signals)
        try:
            from .models import Application as AppModel
            AppModel.objects.filter(pk=app.pk).update(status='HIRED')
            app.status = 'HIRED'
            _log_velocity(app, 'HIRED')
            logger.info("[Pipeline] Auto-advanced %s to HIRED.", name)
        except Exception as e:
            logger.warning("[Pipeline] Could not auto-advance to HIRED: %s", e)

        body = f"""
        <h3 style="color:#10b981;margin-top:0">Welcome to the Team!</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>Congratulations and welcome aboard! We're excited to have you join us
           as <strong>{job}</strong>.</p>
        <p>Our onboarding team will be in touch shortly with your first-day
           details, equipment setup, and 30-day roadmap.</p>
        <p style="color:#64748b;font-size:.85rem">
          Check your <strong>Onboarding Portal</strong> once it's ready.
          Welcome to SmartRecruit!</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Welcome to the Team -- {job}!", _email_html(body))

        # Create onboarding roadmap automatically
        cls._create_onboarding(app)

        _create_notification(
            app.job.recruiter,
            f"{name} Accepted the Offer!",
            f"{name} accepted the offer for {job}. Onboarding roadmap created.",
            link=f"/jobs/application/{app.id}/onboarding/",
            notif_type='SUCCESS',
        )

    @classmethod
    def handle_offer_rejected(cls, app):
        """Candidate rejected the offer."""
        name = app.candidate.full_name
        job = app.job.title

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">Offer Response Received</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>We're sorry to hear you've decided not to accept the offer for
           <strong>{job}</strong> at this time. We respect your decision and
           appreciate the time you invested in our process.</p>
        <p>Should your circumstances change, we'd love to stay connected.
           Best of luck on your journey!</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Offer Update -- {job}", _email_html(body))

        _create_notification(
            app.job.recruiter,
            f"{name} Declined the Offer",
            f"{name} has declined the offer for {job}. Consider the next candidate.",
            link=f"/jobs/application/{app.id}/",
            notif_type='WARNING',
        )

    @classmethod
    def handle_hired(cls, app):
        """Final HIRED state -- ensure onboarding exists."""
        logger.info("[Pipeline] HIRED: %s for %s", app.candidate.full_name, app.job.title)
        cls._create_onboarding(app)

    @classmethod
    def handle_rejected(cls, app):
        """General rejection (e.g., manual recruiter action)."""
        name = app.candidate.full_name
        job = app.job.title

        body = f"""
        <h3 style="color:#e2e8f0;margin-top:0">Application Update</h3>
        <p>Hi <strong>{name}</strong>,</p>
        <p>After careful consideration, we've decided not to proceed with your
           application for <strong>{job}</strong> at this time.</p>
        <p>We valued your interest and encourage you to apply for future
           opportunities. Thank you for your time!</p>
        """
        _run_in_background(_send_pipeline_email, app, f"Application Update -- {job}", _email_html(body))

        # WhatsApp rejection alert
        try:
            from core.utils.twilio_api import send_rejection_alert
            if app.candidate.phone:
                send_rejection_alert(
                    candidate_name=app.candidate.full_name,
                    candidate_phone=app.candidate.phone,
                    role=app.job.title
                )
        except Exception as e:
            logger.warning("[Pipeline] WhatsApp rejection alert failed: %s", e)

    # ------ Supporting Actions ------

    @classmethod
    def _run_resume_screening(cls, app_pk):
        """
        Auto-score the resume and advance/reject.
        Accepts app_pk (not app instance) because this runs in a background thread
        and needs a fresh DB read to be safe.
        """
        from .models import Application as AppModel

        try:
            app = AppModel.objects.select_related(
                'candidate', 'candidate__user', 'job'
            ).get(pk=app_pk)
        except AppModel.DoesNotExist:
            logger.warning("[Pipeline] Resume screening: Application %s not found.", app_pk)
            return

        try:
            from .utils import match_resume_with_ai

            # If score already set (e.g., from apply_job view), use it
            if app.ai_score > 0:
                score = app.ai_score
            else:
                score = match_resume_with_ai(app.candidate, app.job)
                AppModel.objects.filter(pk=app.pk).update(ai_score=score)
                app.ai_score = score

            threshold = app.job.passing_score_r1
            new_status = 'RESUME_SELECTED' if score >= threshold else 'RESUME_REJECTED'

            # Update status via .update() to avoid signal loops
            AppModel.objects.filter(pk=app.pk).update(status=new_status)
            app.status = new_status

            # Manually call handlers (update() doesn't fire signals)
            _log_velocity(app, new_status)
            if new_status == 'RESUME_SELECTED':
                cls.handle_resume_selected(app)
            else:
                cls.handle_resume_rejected(app)

            logger.info("[Pipeline] Resume screened: %s -> %s (score=%.1f)",
                        app.candidate.full_name, new_status, score)

        except Exception as e:
            logger.error("[Pipeline] Resume screening error for app %s: %s", app_pk, e, exc_info=True)

    @classmethod
    def _create_onboarding(cls, app):
        """Auto-create an OnboardingRoadmap for a hired candidate."""
        try:
            from .models import OnboardingRoadmap

            # Check for existing roadmap (OneToOneField -> use try/except, not hasattr)
            try:
                existing = app.onboarding_roadmap
                if existing:
                    return  # Already exists, skip
            except OnboardingRoadmap.DoesNotExist:
                pass  # Doesn't exist yet, create it

            default_tasks = [
                {"title": "Complete HR Paperwork & Documentation", "status": "PENDING", "day": 1},
                {"title": "IT Setup -- Laptop, Accounts & Tools", "status": "PENDING", "day": 1},
                {"title": "Meet the Team & Introduction Sessions", "status": "PENDING", "day": 2},
                {"title": "Role Briefing & 30-Day Goal Setting", "status": "PENDING", "day": 3},
                {"title": "Product/Service Deep Dive Training", "status": "PENDING", "day": 5},
                {"title": "First Project Assignment", "status": "PENDING", "day": 7},
                {"title": "1-Month Performance Check-in", "status": "PENDING", "day": 30},
                {"title": "3-Month Performance Review", "status": "PENDING", "day": 90},
            ]

            # Try to enhance with AI
            ai_notes = f"Standard onboarding plan for {app.job.title} role. Focus on technical ramp-up and team integration in the first 30 days."
            try:
                import os
                from google import genai as gai
                api_key = os.environ.get("GEMINI_API_KEY")
                if api_key:
                    client = gai.Client(api_key=api_key)
                    prompt = (
                        f"Create a brief onboarding plan summary (2-3 sentences) for:\n"
                        f"- Role: {app.job.title}\n"
                        f"- Candidate: {app.candidate.full_name}\n"
                        f"- Key Skills: {app.candidate.skills_extracted or 'General'}\n"
                        f"Focus on what a manager should prioritize in the first 30 days."
                    )
                    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                    ai_notes = resp.text.strip()
            except Exception as ai_err:
                logger.debug("[Pipeline] AI onboarding notes failed (non-critical): %s", ai_err)

            OnboardingRoadmap.objects.create(
                application=app,
                tasks=default_tasks,
                start_date=date.today(),
                status='ACTIVE',
                ai_generated_notes=ai_notes,
            )
            logger.info("[Pipeline] Onboarding roadmap created for %s", app.candidate.full_name)

        except Exception as e:
            logger.error("[Pipeline] Onboarding creation error: %s", e, exc_info=True)


# ---------------------------------------------------------------
#  SCHEDULED TASKS (called via management command or Celery Beat)
# ---------------------------------------------------------------

class PipelineScheduler:
    """
    Tasks that run on a schedule (every 30 mins / daily).
    Wire these to 'python manage.py run_pipeline_scheduler --task all'.
    """

    @classmethod
    def expire_offer_deadlines(cls):
        """Auto-reject offers that have passed their 3-day response deadline."""
        from .models import Offer, Application

        expired = Offer.objects.filter(
            status='GENERATED',
            response_deadline__lt=timezone.now(),
        ).select_related('application__candidate', 'application__job')

        count = 0
        for offer in expired:
            try:
                app = offer.application
                # Update offer status (use update_fields to avoid cascading)
                offer.status = 'REJECTED'
                offer.save(update_fields=['status'])
                # Update application (use .update() to avoid signal loops)
                Application.objects.filter(pk=app.pk).update(status='REJECTED')
                app.status = 'REJECTED'
                _log_velocity(app, 'REJECTED')
                PipelineOrchestrator.handle_rejected(app)
                count += 1
                logger.info("[Scheduler] Offer expired: %s", app.candidate.full_name)
            except Exception as e:
                logger.warning("[Scheduler] Offer expiry error: %s", e)

        logger.info("[Scheduler] Expired %d offer(s).", count)
        return count

    @classmethod
    def send_ghosting_nudges(cls):
        """
        Detect candidates stuck in a PENDING stage for >48h
        and send a gentle reminder email.
        """
        from .models import Application

        threshold = timezone.now() - timedelta(hours=48)
        stuck = Application.objects.filter(
            updated_at__lt=threshold,
            status__in=[
                'ROUND_1_PENDING', 'ROUND_2_PENDING',
                'ROUND_3_PENDING', 'HR_ROUND_PENDING',
            ],
        ).select_related('candidate__user', 'job')

        count = 0
        for app in stuck:
            try:
                name = app.candidate.full_name
                status_display = app.get_status_display()
                site = _get_site_url()

                body = f"""
                <h3 style="color:#f59e0b;margin-top:0">
                  Don't forget -- your next round awaits!</h3>
                <p>Hi <strong>{name}</strong>,</p>
                <p>We noticed you haven't completed your
                   <strong>{status_display}</strong>
                   for <strong>{app.job.title}</strong>.</p>
                <p>Your application is still active and we'd love to see
                   you continue!</p>
                <div style="text-align:center;margin:24px 0">
                  <a href="{site}/jobs/my-applications/"
                     style="background:linear-gradient(135deg,#6366f1,#a855f7);
                            color:#fff;padding:13px 32px;border-radius:10px;
                            text-decoration:none;font-weight:700;
                            display:inline-block">
                    Continue Application
                  </a>
                </div>
                """
                _send_pipeline_email(app, f"Reminder -- {app.job.title} awaits you!", _email_html(body))
                count += 1
            except Exception as e:
                logger.warning("[Scheduler] Nudge error: %s", e)

        logger.info("[Scheduler] Sent %d ghosting nudge(s).", count)
        return count

    @classmethod
    def offer_reminder_3day(cls):
        """Send a reminder 1 day before offer expiry."""
        from .models import Offer

        tomorrow = timezone.now() + timedelta(days=1)
        expiring_soon = Offer.objects.filter(
            status='GENERATED',
            response_deadline__date=tomorrow.date(),
        ).select_related('application__candidate__user', 'application__job')

        count = 0
        for offer in expiring_soon:
            try:
                app = offer.application
                name = app.candidate.full_name
                job = app.job.title
                site = _get_site_url()

                body = f"""
                <h3 style="color:#f59e0b;margin-top:0">
                  Offer Expires Tomorrow!</h3>
                <p>Hi <strong>{name}</strong>,</p>
                <p>Your job offer for <strong>{job}</strong> expires in
                   <strong>24 hours</strong>. Please review and respond to
                   avoid missing this opportunity!</p>
                <div style="text-align:center;margin:24px 0">
                  <a href="{site}/jobs/offer/{app.id}/"
                     style="background:linear-gradient(135deg,#f59e0b,#f97316);
                            color:#fff;padding:13px 32px;border-radius:10px;
                            text-decoration:none;font-weight:700;
                            display:inline-block">
                    View Offer Now
                  </a>
                </div>
                """
                _send_pipeline_email(app, f"Offer expires in 24h -- {job}", _email_html(body))
                count += 1
            except Exception as e:
                logger.warning("[Scheduler] Reminder error: %s", e)

        logger.info("[Scheduler] Sent %d offer reminder(s).", count)
        return count

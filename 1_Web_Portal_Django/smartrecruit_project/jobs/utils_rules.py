import logging
from .models import ATSSyncConfig, TriggerRule, ATSSyncLog
from core.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)

def evaluate_integration_rules(app):
    """
    Orchestrator for Module 3: Integrations & Webhooks.
    Called whenever an application's status or score changes.
    """
    logger.info(f"[RuleEngine] Evaluating rules for {app.candidate.full_name} (Status: {app.status}, Score: {app.ai_score})")

    # 1. ATS STATUS SYNC (Mapping)
    sync_configs = ATSSyncConfig.objects.filter(internal_stage=app.status, is_active=True)
    for config in sync_configs:
        _push_to_external_ats(app, config)

    # 2. CUSTOM TRIGGERS (Rule Engine)
    active_rules = TriggerRule.objects.filter(is_active=True)
    for rule in active_rules:
        triggered = False
        
        if rule.condition_type == 'SCORE_ABOVE' and app.ai_score >= (rule.threshold or 0):
            triggered = True
        elif rule.condition_type == 'STAGE_REACHED' and app.status == rule.target_stage:
            triggered = True
        
        if triggered:
            _execute_rule_action(app, rule)

def _push_to_external_ats(app, config):
    """
    Simulates a push to external ATS (Workday/SAP).
    In production, this would use EncryptedAPIKey to authenticate.
    """
    logger.info(f"[ATS_SYNC] Pushing {app.status} to {config.provider} as '{config.external_ats_stage}'")
    
    # Log the attempt
    ATSSyncLog.objects.create(
        application=app,
        sync_type='PUSH',
        payload=f"Status: {config.external_ats_stage}",
        response="HTTP 200 OK (Simulated)",
        status_code=200,
        is_success=True
    )

def _execute_rule_action(app, rule):
    """
    Executes the action defined in the TriggerRule.
    """
    logger.info(f"[RuleEngine] Executing {rule.action} for rule: {rule.name}")
    
    if rule.action == 'SEND_WHATSAPP':
        # Mock WhatsApp via Twilio logic
        phone = getattr(app.candidate, 'phone', 'Unknown')
        _log_action(f"WhatsApp Alert sent to Admin for {app.candidate.full_name} ({phone})")
        
    elif rule.action == 'SEND_EMAIL':
        from .email_utils import send_status_email
        send_status_email(app.job.recruiter, f"Rule Triggered: {rule.name}", 
                          f"Candidate {app.candidate.full_name} has met the criteria: {rule.name}")
        
    elif rule.action == 'TRIGGER_WEBHOOK':
        # Post to rule.webhook_url
        _log_action(f"Webhook fired to {rule.webhook_url}")

def _log_action(message):
    logger.info(f"[RuleEngine_ACTION] {message}")

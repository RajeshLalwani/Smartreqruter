import os
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from jobs.models import Application, ATSSyncConfig, ATSSyncLog, ExternalATSMapping

logger = logging.getLogger(__name__)

class ATSSyncManager:
    """
    Enterprise Integration Middleware.
    Handles secure handshakes and data mapping between SmartRecruit and Legacy ATS.
    """

    def get_oauth_token(self, provider):
        """
        Retrieves a valid OAuth 2.0 token for the specified provider.
        In a real scenario, this would handle token expiration and refreshing.
        """
        config = ATSSyncConfig.objects.filter(provider=provider, is_active=True).first()
        if not config or not config.api_key:
            return None
        
        # Simulation: In production, we'd use requests.post(config.auth_url, data=...)
        # For now, we return the stored API Key as a Bearer token.
        return config.api_key

    def push_candidate_milestone(self, application, milestone_name):
        """
        Push local milestones to External ATS.
        Triggered when an interview tier or application status changes.
        """
        # Check if we have an external mapping
        mapping = getattr(application, 'ats_mapping', None)
        if not mapping:
            logger.warning(f"[Sync] No external mapping found for application {application.id}. Skipping PUSH.")
            return False

        # Find active sync config for this application's current status
        config = ATSSyncConfig.objects.filter(internal_stage=milestone_name, is_active=True).first()
        if not config:
            logger.warning(f"[Sync] No active sync config found for internal stage '{milestone_name}'. Skipping PUSH.")
            return False

        token = self.get_oauth_token(config.provider)
        if not token:
            logger.error(f"[ATSSync] No valid OAuth token for provider {config.provider}")
            return False

        payload = {
            "external_candidate_id": mapping.external_candidate_id, # Assuming external_id in instruction meant external_candidate_id
            "external_application_id": mapping.external_application_id,
            "status": config.external_ats_stage,
            "milestone": milestone_name,
            "score": application.ai_score,
            "timestamp": timezone.now().isoformat()
        }

        try:
            # Simulation of external API call with OAuth header
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            # In production, this would be:
            # response = requests.post(f"{config.base_url}/api/v1/sync", json=payload, headers=headers)
            # For now, simulate success
            
            # Log success
            ATSSyncLog.objects.create(
                application=application,
                sync_type='PUSH',
                is_success=True, # Changed from 'status' to 'is_success' to match model
                payload=json.dumps(payload), # Payload should be JSON string
                response=json.dumps({"status": "Synced via OAuth 2.0"}) # Changed from 'response_data' to 'response'
            )
            logger.info(f"[Sync] PUSH Successful: {application.candidate.full_name} -> {config.provider} for milestone {milestone_name}")
            return True
        except Exception as e:
            logger.error(f"[ATSSync] Push failed for App {application.id}: {e}")
            ATSSyncLog.objects.create(
                application=application,
                sync_type='PUSH',
                is_success=False,
                payload=json.dumps(payload),
                response=str(e)
            )
            return False

    @staticmethod
    def pull_candidate_status(external_payload):
        """
        Process incoming webhooks from external ATS.
        Updates internal SmartRecruit state based on external changes.
        """
        ext_app_id = external_payload.get('external_application_id')
        ext_status = external_payload.get('external_status')

        try:
            mapping = ExternalATSMapping.objects.get(external_application_id=ext_app_id)
            application = mapping.application

            # Correlate external status back to internal stage
            config = ATSSyncConfig.objects.filter(external_ats_stage=ext_status, is_active=True).first()
            
            if config:
                application.status = config.internal_stage
                application.save()
                
                ATSSyncLog.objects.create(
                    application=application,
                    sync_type='PULL',
                    payload=json.dumps(external_payload),
                    is_success=True,
                    response=f"Mapped status: {config.internal_stage}"
                )
                logger.info(f"[Sync] PULL Successful: {application.id} updated to {application.status}")
                return True
            else:
                logger.warning(f"[Sync] PULL Warning: No mapping found for external status '{ext_status}'")
                return False

        except ExternalATSMapping.DoesNotExist:
            logger.error(f"[Sync] PULL Error: External App ID {ext_app_id} not mapped.")
            return False
        except Exception as e:
            logger.error(f"[Sync] PULL Error: {e}")
            return False

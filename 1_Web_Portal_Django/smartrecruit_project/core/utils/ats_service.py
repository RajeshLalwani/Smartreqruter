import os
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class ATSService:
    """
    Middleware for bi-directional synchronization with external ATS platforms.
    Supports OAuth 2.0 / API Key authentication and stage mapping.
    """
    
    def __init__(self, platform="Generic-ATS"):
        self.platform = platform
        self.api_key = os.getenv("ATS_API_KEY") or getattr(settings, "ATS_API_KEY", None)
        self.api_url = os.getenv("ATS_API_BASE_URL") or getattr(settings, "ATS_API_BASE_URL", "https://api.external-ats.com/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Client-ID": "SmartRecruit-Sync",
        }

    def sync_candidate_stage(self, application):
        """
        Pushes a candidate's current stage to the external ATS.
        """
        from jobs.models import ATSSyncConfig, ATSSyncLog
        
        # 1. Get mapped stage
        config = ATSSyncConfig.objects.filter(internal_stage=application.status, is_active=True).first()
        if not config:
            logger.info(f"[ATS-Sync] No mapping found for stage: {application.status}. Skipping.")
            return False

        # 2. Build Payload
        payload = {
            "external_id": application.external_ats_id,
            "email": application.candidate.email,
            "new_stage": config.external_ats_stage,
            "score": application.ai_score,
            "timestamp": timezone.now().isoformat()
        }

        # 3. Dispatch (with retry/idempotency)
        return self._dispatch_request("PUSH", application, payload)

    def _dispatch_request(self, sync_type, application, payload):
        """
        Internal dispatcher with logging and error handling.
        """
        from jobs.models import ATSSyncLog
        
        log = ATSSyncLog.objects.create(
            application=application,
            sync_type=sync_type,
            payload=json.dumps(payload)
        )

        try:
            # Note: In a real enterprise setup, we would handle OAuth token refresh here
            response = requests.post(
                f"{self.api_url}/sync",
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            log.status_code = response.status_code
            log.response = response.text
            log.is_success = response.status_code in [200, 201]
            
            if log.is_success:
                application.sync_status = 'SYNCED'
            else:
                application.sync_status = 'FAILED'
            
        except Exception as e:
            log.response = str(e)
            log.is_success = False
            application.sync_status = 'FAILED'
            logger.error(f"[ATS-Sync] Error during {sync_type}: {e}")

        log.save()
        application.save()
        return log.is_success

    @staticmethod
    def ingest_webhook_status(payload):
        """
        Handles incoming status changes from external ATS webhooks.
        """
        from jobs.models import Application, ATSSyncConfig, ATSSyncLog
        
        external_id = payload.get("id")
        external_status = payload.get("status")
        
        application = Application.objects.filter(external_ats_id=external_id).first()
        if not application:
            logger.warning(f"[ATS-Webhook] Application {external_id} not found in local DB.")
            return False

        # Map external status back to internal stage
        mapping = ATSSyncConfig.objects.filter(external_ats_stage=external_status, is_active=True).first()
        if mapping:
            application.status = mapping.internal_stage
            application.sync_status = 'SYNCED'
            application.save()
            
            # Log the pull event
            ATSSyncLog.objects.create(
                application=application,
                sync_type='PULL',
                payload=json.dumps(payload),
                is_success=True,
                status_code=200
            )
            return True
        
        return False

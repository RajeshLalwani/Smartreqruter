from jobs.models import SentimentLog
import logging

logger = logging.getLogger(__name__)

def fetch_interview_frames(interview_id):
    """
    Fetches all proctoring frames and violations for a specific interview.
    Sorted chronologically.
    """
    try:
        logs = SentimentLog.objects.filter(
            interview_id=interview_id,
            frame__isnull=False
        ).order_by('timestamp')

        sequence = []
        for log in logs:
            sequence.append({
                'frame': log.frame,
                'timestamp': log.timestamp.strftime("%H:%M:%S"),
                'violations': log.proctoring_flags.get('violations', []),
                'flags_count': log.proctoring_flags.get('total_session_flags', 0)
            })
        
        return sequence
    except Exception as e:
        logger.error(f"Error fetching interview frames: {e}")
        return []

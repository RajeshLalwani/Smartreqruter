from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import JobPosting, Candidate, Application, Interview
from .serializers import JobPostingSerializer, CandidateSerializer, ApplicationSerializer, InterviewSerializer

class CandidateDashboardAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'candidate_profile'):
            return Response({"error": "User is not a candidate"}, status=status.HTTP_400_BAD_REQUEST)
        
        candidate = request.user.candidate_profile
        applications = Application.objects.filter(candidate=candidate)
        interviews = Interview.objects.filter(application__candidate=candidate)
        
        return Response({
            "profile": CandidateSerializer(candidate).data,
            "applications": ApplicationSerializer(applications, many=True).data,
            "interviews": InterviewSerializer(interviews, many=True).data
        })

class JobPostingListAPI(generics.ListAPIView):
    queryset = JobPosting.objects.filter(status='OPEN')
    serializer_class = JobPostingSerializer
    permission_classes = [permissions.AllowAny]

class InterviewStateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, interview_id):
        try:
            interview = Interview.objects.get(id=interview_id)
            # Ensure the user has access
            if request.user != interview.application.candidate.user and not request.user.is_staff:
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
            return Response(InterviewSerializer(interview).data)
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, interview_id):
        # Trigger Gemini/HuggingFace to analyze the recorded audio/text and populate sentiment data
        try:
            interview = Interview.objects.get(id=interview_id)
            transcript = request.data.get('transcript', '')

            if transcript:
                from core.ai_engine import AIEngine
                from .models import SentimentLog
                ai = AIEngine()
                
                # Direct call to Gemini Engine
                prompt = (
                    "Analyze the following transcript. Return STRICTLY a JSON object with no markdown and no pre-amble. "
                    "Schema required: {\"sentiment_label\": \"Positive/Neutral/Negative\", \"confidence_score\": 0.8, \"stress_level\": 0.2}\n\n"
                    f"Transcript: {transcript}"
                )
                
                raw_response = ai.get_chat_response(prompt)
                
                # Parse and Sync
                import json
                try:
                    cleaned_json = raw_response.replace('```json', '').replace('```', '').strip()
                    data = json.loads(cleaned_json)
                    
                    SentimentLog.objects.create(
                        interview=interview,
                        emotion=data.get('sentiment_label', 'Neutral').lower(),
                        sentiment_label=data.get('sentiment_label', 'Neutral'),
                        confidence_score=float(data.get('confidence_score', 0.5)),
                        stress_level=float(data.get('stress_level', 0.0)),
                        voice_transcript=transcript
                    )
                except Exception as e:
                    # Fallback to standard tagging
                    SentimentLog.objects.create(
                        interview=interview,
                        sentiment_label="Neutral",
                        confidence_score=0.5,
                        stress_level=0.5,
                        voice_transcript=transcript,
                        raw_expressions={"error": str(e), "raw": raw_response}
                    )

            return Response({"status": "Sentiment Analysis complete and synced to Log"})
        except Interview.DoesNotExist:
            return Response({"error": "Interview not found"}, status=status.HTTP_404_NOT_FOUND)

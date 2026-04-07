from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# This is a crucial import to link our Django app with the AI module.
# The path has been configured in settings.py to allow this.
from Interview_Bot.interviewer import AIInterviewer

# Initialize the AI Interviewer once when the server starts.
# This is more efficient than creating a new instance for every request.
# We'll add a check for the API key as well.
try:
    interviewer_bot = AIInterviewer()
    print("[INFO] AIInterviewer initialized successfully.")
except Exception as e:
    interviewer_bot = None
    print(f"[ERROR] Failed to initialize AIInterviewer: {e}")

def interview_view(request):
    """
    Renders the main interview page.
    This page will contain the chat interface and the voice interaction logic.
    """
    # We can pass initial data to the template if needed, for example, the job role.
    job_role = request.GET.get('job', 'Software Engineer') # Get job from URL parameter
    return render(request, 'interview/interview_page.html', {'job_title': job_role})

@csrf_exempt
def chat_api_view(request):
    """
    API endpoint to handle the chat logic for the interview bot.
    Receives user messages, gets a response from the AI, and returns it.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    if not interviewer_bot:
        return JsonResponse({'error': 'AI Interviewer not available'}, status=503)

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        job_title = data.get('job_title', 'Software Engineer')
        conversation_history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        # Phase 10: Multi-Language Awareness
        candidate_language = getattr(request, 'LANGUAGE_CODE', 'en')

        # Let's decide which AI function to call.
        # If the conversation has just started, generate a standard question.
        # If there's history, generate a dynamic follow-up.
        if not conversation_history:
             # Let's create a welcome message and the first question
            bot_response = f"Excellent. We're starting your interview for the {job_title} position. Good luck! "
            bot_response += interviewer_bot.generate_question(job_title=job_title, candidate_language=candidate_language)
        else:
            # Generate a dynamic follow-up based on the last answer
            bot_response = interviewer_bot.generate_dynamic_question(job_title=job_title, conversation_history=conversation_history, candidate_language=candidate_language)
        
        # We could also add logic here to evaluate the user's previous answer
        # For now, we'll just get the next question.

        return JsonResponse({'response': bot_response})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        # Log the error for debugging
        print(f"[ERROR] Chat API failed: {e}")
        # Provide a graceful fallback response to the user
        fallback_response = "I'm having a little trouble connecting right now. Can you tell me more about your previous experience?"
        return JsonResponse({'response': fallback_response}, status=500)

import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger('ai_email_generator')

# Configure Gemini Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    client = None
    logger.error(f"Failed to initialize Gemini Client for Email Generator: {e}")

def generate_personalized_email(candidate_name, job_title, action_type, feedback_data):
    """
    Generates a hyper-personalized HTML email body using Gemini.
    action_type: 'shortlist' or 'reject'
    feedback_data: Dictionary containing AI Insights or Interview Feedback
    """
    if not client or not GEMINI_API_KEY:
        logger.warning("Gemini Client not available. Falling back to standard template.")
        return _fallback_email(candidate_name, job_title, action_type)

    if action_type == 'shortlist':
        prompt_goal = f"""
        You are a warm, professional Senior Recruiter at a top-tier tech company.
        You are writing an email to {candidate_name} to inform them that they have been SHORTLISTED for the {job_title} position!
        
        Write a highly empathetic and personalized email acknowledging specific strengths they demonstrated in their profile/interview.
        Use the following feedback data to personalize the email: {json.dumps(feedback_data)}
        
        Requirements:
        1. Keep it under 150 words.
        2. Format the response ONLY in clean HTML (e.g., <p>, <strong>, <br>). Do not use markdown ```html blocks.
        3. Do not include the <html>, <head>, or <body> tags. Just the internal HTML content.
        4. Do not include a subject line, just the body.
        5. The tone must be exciting, professional, and highly personalized!
        """
    else:
        # Rejection
        prompt_goal = f"""
        You are a highly empathetic and professional Senior Recruiter at a top-tier tech company.
        You are writing an email to {candidate_name} to inform them that they have unfortunately NOT been selected for the {job_title} position.
        
        Instead of a standard generic rejection, give them a "Hyper-Personalized" rejection. 
        Acknowledge 1 or 2 specific things they did well, but gently point out the specific area where they fell short compared to other candidates.
        Provide a 1-sentence actionable tip on how they can improve that specific skill.
        
        Use the following feedback data to personalize the email: {json.dumps(feedback_data)}
        
        Requirements:
        1. Keep it under 150 words.
        2. Format the response ONLY in clean HTML (e.g., <p>, <strong>, <br>). Do not use markdown ```html blocks.
        3. Do not include the <html>, <head>, or <body> tags. Just the internal HTML content.
        4. Do not include a subject line, just the body.
        5. The tone must be kind, encouraging, constructive, and highly personalized!
        """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_goal,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
            )
        )
        # Clean up any potential markdown formatting the AI might still try to add
        html_content = response.text.replace("```html", "").replace("```", "").strip()
        return html_content
        
    except Exception as e:
        logger.error(f"Error generating personalized email via Gemini: {e}")
        return _fallback_email(candidate_name, job_title, action_type)


def _fallback_email(candidate_name, job_title, action_type):
    """Fallback standard emails if AI generation fails."""
    if action_type == 'shortlist':
        return f"<p>Hi {candidate_name},</p><p>Congratulations! Your profile has been selected for the next round of interviews for the <strong>{job_title}</strong> role. We were very impressed with your background and are excited to learn more about you.</p><p>Our team will be in touch shortly with the next steps.</p>"
    else:
        return f"<p>Hi {candidate_name},</p><p>Thank you for taking the time to apply for the <strong>{job_title}</strong> role. We appreciate your interest in our company.</p><p>Unfortunately, we have decided to move forward with other candidates who more closely align with our current needs for this specific role.</p><p>We wish you the best of luck in your job search.</p>"

import json
import io
import logging
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.core.files.base import ContentFile
try:
    from core.ai_engine import AIEngine
except ImportError:
    AIEngine = None

logger = logging.getLogger(__name__)

def generate_interview_summary(application):
    """
    Generate HR Summary and Candidate Feedback using Gemini, then save to application.
    Also calculates dimensional scores.
    """
    if not AIEngine:
        logger.warning("AIEngine not available. Cannot generate summary.")
        return False
        
    ai = AIEngine()
    
    # Collect data points
    interviews = application.interviews.all()
    transcript = ""
    flags = []
    sentiment_data = []
    
    for iv in interviews:
        transcript += iv.code_final + " "
        flags.append(f"Flags detected: {iv.flag_count}")
        for log in iv.sentiment_logs.all()[:100]: # Sample up to 100 logs
            if log.emotion:
                sentiment_data.append(log.emotion)
            if hasattr(log, 'voice_transcript') and log.voice_transcript:
                transcript += log.voice_transcript + " "

    prompt = f"""
    Analyze the following candidate data for the role of {application.job.title}.
    Transcript snippet: {transcript[:1500]}
    Proctoring Flags: {', '.join(flags)}
    Emotions: {', '.join(sentiment_data[:50])}
    
    Return ONLY valid JSON with this exact structure:
    {{
      "hr_summary": "<ul><li>Point 1</li><li>Point 2</li><li>Point 3</li></ul>",
      "candidate_feedback": "<b>Strengths:</b>...<br/><b>Areas for Improvement:</b>...",
      "technical_score": 85,
      "communication_score": 75,
      "confidence_score": 80,
      "integrity_score": 90,
      "problem_solving_score": 85
    }}
    
    Rules:
    - hr_summary should be a 3-bullet "Bottom Line" in HTML format.
    - candidate_feedback should be a "Growth Mindset" report in HTML.
    - Scores must be integers out of 100.
    """
    
    system_prompt = "You are a professional AI Assistant for HR and Candidate feedback."
    
    try:
        text = ai.generate(system_prompt=system_prompt, user_prompt=prompt, json_response=True)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
                
        data = json.loads(text.strip())
        
        application.hr_summary = data.get("hr_summary", "Summary unavailable.")
        application.candidate_feedback = data.get("candidate_feedback", "Feedback unavailable.")
        application.technical_score = float(data.get("technical_score", 0))
        application.communication_score = float(data.get("communication_score", 0))
        application.confidence_score = float(data.get("confidence_score", 0))
        application.integrity_score = float(data.get("integrity_score", 0))
        application.problem_solving_score = float(data.get("problem_solving_score", 0))
        
        application.save()
        return True
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return False

def generate_pdf_report(application):
    """
    Generates a PDF report using ReportLab for HR records and returns passing it as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        textColor=colors.HexColor("#00d2ff"),
        fontSize=18,
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        textColor=colors.HexColor("#333333"),
        spaceBefore=15,
        spaceAfter=10
    )
    normal_style = styles['Normal']
    
    story = []
    
    # Header
    story.append(Paragraph(f"SmartRecruit AI Interview Report", title_style))
    story.append(Paragraph(f"<b>Candidate:</b> {application.candidate.full_name}", normal_style))
    story.append(Paragraph(f"<b>Role:</b> {application.job.title}", normal_style))
    story.append(Paragraph(f"<b>Date:</b> {timezone.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    story.append(Spacer(1, 20))
    
    # HR Summary
    story.append(Paragraph("Executive Summary (HR)", heading_style))
    
    # Clean up simple HTML tags for ReportLab (ReportLab supports b, i, u, sub, super, font)
    # Removing ul, li, br for standard Paragraph if needed, or keeping them within supported subsets.
    clean_hr_summary = application.hr_summary or "No summary generated."
    clean_hr_summary = clean_hr_summary.replace("<ul>", "").replace("</ul>", "")
    clean_hr_summary = clean_hr_summary.replace("<li>", "<bullet>&bull;</bullet> ").replace("</li>", "<br/>")
    story.append(Paragraph(clean_hr_summary, normal_style))
    
    story.append(Spacer(1, 20))
    
    # Scores
    story.append(Paragraph("Dimensional Scores", heading_style))
    story.append(Paragraph(f"Technical Score: {application.technical_score}/100", normal_style))
    story.append(Paragraph(f"Communication Score: {application.communication_score}/100", normal_style))
    story.append(Paragraph(f"Confidence Score: {application.confidence_score}/100", normal_style))
    story.append(Paragraph(f"Integrity Score: {application.integrity_score}/100", normal_style))
    story.append(Paragraph(f"Problem Solving Score: {application.problem_solving_score}/100", normal_style))
    
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

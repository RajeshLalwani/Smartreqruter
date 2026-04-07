import os
import sys
import requests
import html
import random
import asyncio
import edge_tts
import json
from google import genai
from google.genai import types
from django.conf import settings
from django.utils import timezone
from uuid import uuid4

# AI Modules are added to sys.path in settings.py

def generate_ai_mcqs(amount=5, domain='general', difficulty='medium'):
    """
    Generates MCQs using Gemini API based on domain and difficulty.
    Expected to return a list of dicts.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Returning mocked array of AI MCQs.")
        return [{'question': f'Mock Evaluation Question {i+1} for {domain} ({difficulty})?', 'correct': 'Correct Answer A', 'options': ['Correct Answer A', 'Wrong Option B', 'Wrong Option C', 'Wrong Option D']} for i in range(amount)]
    
    client = genai.Client(api_key=api_key)
    try:
        prompt = f'''
        Generate {amount} multiple-choice questions about '{domain}' at a '{difficulty}' difficulty level.
        Return ONLY a raw JSON array of objects.
        Each object MUST have exactly these keys:
        - "question": The question text.
        - "correct_answer": The correct answer.
        - "incorrect_answers": An array of exactly 3 incorrect answers.
        '''
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            config=types.GenerateContentConfig(response_mime_type='application/json'),
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Clean up potential markdown formatting from the response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        raw_questions = json.loads(response_text)
        return format_questions(raw_questions)
        
    except Exception as e:
        print(f"Error generating MCQs from Gemini: {e}")
        return []

def fetch_questions(amount=50, category=18, difficulty=None):
    """
    Fetches questions fully automatically from external APIs.
    If category is a string, it uses Gemini AI to generate domain-specific questions.
    If category is an integer (like 18 for OpenTriviaDB), it fetches from OpenTriviaDB.
    No manual admin questions are required.
    """
    try:
        if isinstance(category, str):
            diff = difficulty if difficulty else 'medium'
            return generate_ai_mcqs(amount=amount, domain=category, difficulty=diff)
            
        # OpenTriviaDB limits to 50 questions per request
        fetch_amount = min(amount, 50)
        url = f"https://opentdb.com/api.php?amount={fetch_amount}&category={category}&type=multiple"
        if difficulty:
            url += f"&difficulty={difficulty}"
            
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['response_code'] == 0:
            return format_questions(data['results'])
            
        return []
    except Exception as e:
        print(f"Error fetching questions from OpenTriviaDB: {e}")
        return []

def format_questions(raw_questions):
    formatted = []
    from uuid import uuid4
    for q in raw_questions:
        import html
        
        # Check if it is already formatted like our required dictionary
        if isinstance(q, dict) and 'correct' in q and 'options' in q:
            if 'id' not in q:
                q['id'] = str(uuid4())
            
            # Ensure options are lists, not strings, to fix rendering bug
            if isinstance(q['options'], str):
                try:
                    import ast
                    q['options'] = ast.literal_eval(q['options'])
                except:
                    q['options'] = [q['correct'], 'Option B', 'Option C', 'Option D']

            formatted.append(q)
            continue
            
        # Otherwise, assume it's OpenTriviaDB raw output
        options = [html.unescape(opt) for opt in q.get('incorrect_answers', [])]
        correct_answer = html.unescape(q.get('correct_answer', ''))
        options.append(correct_answer)
        
        import random
        random.shuffle(options)
        
        formatted.append({
            'id': str(uuid4()),
            'question': html.unescape(q.get('question', '')),
            'options': options,
            'correct': correct_answer
        })
    return formatted


try:
    from Resume_Parser.parser import ResumeParser
except ImportError as e:
    print(f"Error importing ResumeParser: {e}")
    ResumeParser = None

def parse_resume(resume_file, required_skills=None):
    """
    Parses the resume using the AI Resume Parser module.
    Calculates ATS score based on skill matching if required_skills provided.
    """
    import tempfile
    
    if not ResumeParser:
        return {
            'score': 0,
            'skills': ['Parser Not Loaded'],
            'email': '',
            'phone': '',
            'matched_skills': [],
            'missing_skills': []
        }

    try:
        ext = os.path.splitext(resume_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='wb') as temp_file:
            for chunk in resume_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        parser = ResumeParser()
        data = parser.parse(temp_file_path)
        
        # Real ATS Scoring Algorithm
        score = 0
        matched_skills = []
        missing_skills = []
        
        if required_skills and len(required_skills) > 0:
            # Normalize skills (lowercase, strip whitespace)
            resume_skills_normalized = [s.lower().strip() for s in data['skills']]
            required_skills_normalized = [s.lower().strip() for s in required_skills]
            
            # Find matches
            for req_skill in required_skills_normalized:
                if req_skill in resume_skills_normalized:
                    matched_skills.append(req_skill)
                else:
                    missing_skills.append(req_skill)
            
            # Calculate score: (Matched / Total Required) * 100
            if len(required_skills_normalized) > 0:
                score = (len(matched_skills) / len(required_skills_normalized)) * 100
            else:
                score = 70  # Default if no required skills
                
            # Bonus for extra skills
            extra_skills = len(resume_skills_normalized) - len(matched_skills)
            if extra_skills > 0:
                score = min(score + (extra_skills * 2), 100)
        else:
            # Fallback: Use skill count as proxy
            score = min(len(data['skills']) * 10 + 40, 85)
        
        score = round(score, 2)
        
        os.unlink(temp_file_path)
        
        return {
            'score': score, 
            'skills': data['skills'],
            'email': data.get('email'),
            'phone': data.get('phone'),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills
        }
        
    except Exception as e:
        print(f"Parsing Error: {e}")
        return {
            'score': 0,
            'skills': [],
            'error': str(e),
            'matched_skills': [],
            'missing_skills': []
        }

def match_resume_with_ai(resume_file, job_description):
    """
    Uses TF-IDF Vectorization to match resume content with job description.
    """
    try:
        from Resume_Matcher.ai_matcher import ResumeMatcher
        import tempfile
        
        matcher = ResumeMatcher()
        
        # Save temp file for extraction
        ext = os.path.splitext(resume_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='wb') as temp_file:
            for chunk in resume_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
            
        resume_text = matcher.extract_text(temp_file_path)
        os.unlink(temp_file_path) # Cleanup
        
        score = matcher.calculate_match(resume_text, job_description)
        insights = matcher.extract_keywords(resume_text, job_description)
        
        return {
            'score': score,
            'insights': insights
        }
    except Exception as e:
        print(f"AI Match Error: {e}")
        return 0.0

def advanced_ai_candidate_ranking(resume_text, job_description):
    """
    Advanced candidate evaluation using Gemini to return score, strengths, weaknesses, and a summary.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Returning mocked AI Candidate Ranking to allow application progression.")
        return {'score': 85, 'strengths': ['Strong foundational skills', 'Good experience match'], 'weaknesses': ['Needs domain specific training'], 'summary': 'Candidate shows strong potential and matches job requirements well based on keywords.', 'dimensions': {'Technical': 85, 'Communication': 80, 'Leadership': 70, 'Cultural': 80}}
    
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f'''
        Act as an expert technical recruiter and evaluate the following candidate's resume against the provided job description.
        Return ONLY a strictly valid JSON object. Do not format with markdown blocks like ```json.
        Use exactly these keys:
        - "score": An integer from 0 to 100 representing the match percentage.
        - "strengths": An array of strings highlighting up to 3 strong points or matched skills.
        - "weaknesses": An array of strings highlighting up to 3 weak points or missing skills.
        - "summary": A short, 2-sentence professional summary of the candidate's fit.
        - "dimensions": An object with exactly 4 keys mapping to integer scores out of 100: "Technical", "Communication", "Leadership", "Cultural".
        
        --- JOB DESCRIPTION ---
        {job_description}
        
        --- CANDIDATE RESUME ---
        {resume_text}
        '''
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up potential markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text)
    except Exception as e:
        print(f"Error in Advanced AI match: {e}")
        return {'score': 0, 'strengths': [], 'weaknesses': [], 'summary': str(e), 'dimensions': {'Technical': 0, 'Communication': 0, 'Leadership': 0, 'Cultural': 0}}

async def _generate_voice_async(text, output_file):
    """Async helper for edge_tts"""
    try:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(output_file)
    except Exception as e:
        print(f"EdgeTTS Error: {e}")
        raise e

def generate_voice_file(text):
    """
    Generates an MP3 file from text using Edge TTS.
    Returns the relative path to the file.
    """
    try:
        filename = f"voice_{uuid4()}.mp3"
        # Ensure media directory exists
        media_root = getattr(settings, 'MEDIA_ROOT', 'media')
        voice_dir = os.path.join(media_root, 'voice_questions')
        os.makedirs(voice_dir, exist_ok=True)
        
        output_path = os.path.join(voice_dir, filename)
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we are already in an event loop (e.g. some servers), use create_task or similar? 
                # Ideally unrelated in standard Django sync view.
                # Use a new loop if possible or run_coroutine_threadsafe
                 asyncio.run(_generate_voice_async(text, output_path))
            else:
                 asyncio.run(_generate_voice_async(text, output_path))
        except RuntimeError:
             # Fallback for "There is no current event loop" or similar
             asyncio.run(_generate_voice_async(text, output_path))

        return os.path.join('voice_questions', filename)
    except Exception as e:
        print(f"Error generating voice file: {e}")
        return None


def generate_ai_job_description(title, skills, tone='professional'):
    """
    Generates a professional job description using a stochastic template system.
    Supports 'professional', 'modern', and 'dynamic' tones.
    """
    import random
    
    # Tone-based Templates
    intros = {
        'professional': [
            f"We are seeking a highly qualified {title} to join our engineering team. The ideal candidate will have strong technical skills and a passion for excellence.",
            f"An established company is looking for a {title} to contribute to our core products. You will work in a collaborative environment to deliver high-quality software.",
        ],
        'modern': [
            f"We are looking for a talented {title} to join our collaborative team. If you are passionate about building high-quality products and learning new technologies, we would love to meet you.",
            f"Join a forward-thinking team as a {title}. We value innovation, creativity, and a commitment to building user-centric solutions.",
        ],
        'dynamic': [
            f"We are scaling rapidly and looking for a visionary {title} to help us define the future. This is a high-impact role for someone ready to take ownership and drive results.",
            f"Join our fast-paced environment as a {title}. We are looking for driven individuals who thrive on challenges and want to make a tangible impact.",
        ]
    }
    
    # Skill-Specific Responsibilities
    skill_map = {
        'python': [
            "- Write efficient, scalable, and testable Python code.",
            "- Integrate user-facing elements with server-side logic.",
            "- Implement security and data protection solutions."
        ],
        'django': [
            "- Architect and develop RESTful APIs using Django Rest Framework.",
            "- Optimize database schemas and ORM queries for maximum performance.",
            "- Manage background tasks with Celery and Redis."
        ],
        'react': [
            "- Build reusable components and front-end libraries for future use.",
            "- Translate designs and wireframes into high-quality code.",
            "- Optimize components for maximum performance across a vast array of web-capable devices and browsers."
        ],
        'javascript': [
            "- Develop functional and sustainable web applications with clean codes.",
            "- Ensure the technical feasibility of UI/UX designs."
        ],
        'aws': [
            "- Deploy and manage applications on AWS infrastructure.",
            "- Implement CI/CD pipelines for automated deployment."
        ],
        'docker': [
            "- Containerize applications for consistent environments.",
            "- Orchestrate services using Docker Compose or Kubernetes."
        ],
        'machine learning': [
            "- Design and implement machine learning models.",
            "- Perform statistical analysis and fine-tuning using test results."
        ]
    }
    
    # Default Responsibilities
    default_responsibilities = [
        "- Collaborate with cross-functional teams to define, design, and ship new features.",
        "- Identify and correct bottlenecks and fix bugs.",
        "- Help maintain code quality, organization, and automatization.",
        f"- Stay up-to-date with new technology trends regarding {skills[0] if skills else 'our stack'}."
    ]

    # Build Responsibilities
    responsibilities = []
    # Mix generic and specific
    responsibilities.extend(default_responsibilities[:2]) 
    
    for skill in skills:
        s_lower = skill.lower().strip()
        # Check direct match or substring
        for key, lines in skill_map.items():
            if key in s_lower:
                responsibilities.extend(lines)
                break
                
    # Deduplicate and shuffle slightly
    responsibilities = list(set(responsibilities))
    random.shuffle(responsibilities)
    
    # Requirements
    requirements = [
        f"- Proven experience as a {title} or similar role.",
        f"- Strong proficiency in {', '.join(skills)}.",
        "- Familiarity with RESTful APIs and modern frontend build pipelines.",
        "- Ability to understand business requirements and translate them into technical requirements.",
        "- Degree in Computer Science, Engineering, or relevant field."
    ]
    
    # Benefits (Tone dependent)
    if tone == 'professional':
        benefits = [
            "- Competitive salary and comprehensive health benefits.",
            "- 401(k) matching and retirement planning.",
            "- Professional development opportunities."
        ]
    elif tone == 'modern':
        benefits = [
            "- Competitive salary and flexible work environment.",
            "- Modern office space and remote work options.",
            "- Collaborative culture and team events."
        ]
    else: # Dynamic
        benefits = [
            "- Top-tier compensation and equity packages.",
            "- Work on cutting-edge technology that matters.",
            "- Rapid career growth and unlimited potential."
        ]

    # Assemble
    intro_candidates = intros.get(tone, intros['professional'])
    
    jd = f"""**Job Overview**
{random.choice(intro_candidates)}

**Key Responsibilities**
{chr(10).join(responsibilities)}

**Requirements**
{chr(10).join(requirements)}

**What We Offer**
{chr(10).join(benefits)}
"""
    return jd


def generate_ics_content(interview):
    """
    Generates a VCALENDAR string for the given interview.
    """
    from datetime import timedelta
    
    # Format dates for ICS (UTC)
    # ICS format: YYYYMMDDTHHMMSSZ
    start_time = interview.scheduled_time
    end_time = start_time + timedelta(hours=1) # Assume 1 hour duration
    
    def format_dt(dt):
        return dt.strftime('%Y%m%dT%H%M%SZ')
    
    uid = f"{interview.id}-{uuid4()}@smartrecruit.com"
    dtstamp = format_dt(timezone.now())
    dtstart = format_dt(start_time)
    dtend = format_dt(end_time)
    
    summary = f"Interview: {interview.application.job.title} ({interview.get_interview_type_display()})"
    description = f"SmartRecruit Interview\\nRound: {interview.get_interview_type_display()}\\nLink: {interview.meeting_link}"
    location = interview.meeting_link
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SmartRecruit//Interview Scheduler//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR"""
    
    return ics_content


def render_to_pdf(template_src, context_dict={}):
    """
    Helper to render HTML template to PDF buffer using xhtml2pdf.
    """
    from io import BytesIO
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # PDF rendering
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    return None

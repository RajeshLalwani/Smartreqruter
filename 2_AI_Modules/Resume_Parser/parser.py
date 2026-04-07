import os
import json
import logging
import re
import PyPDF2
import docx
from core.ai_engine import AIEngine

# Suppress debug logs
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Advanced Resume Scanner & RAG Pipeline.
    Uses native Python libraries to extract document text (avoids Spacy/Pydantic V1 bugs) 
    and delegates AI analysis to the Centralized AIEngine for zero-downtime ATS matching.
    """

    def __init__(self):
        self.ai_engine = AIEngine()

    def split_text(self, text, chunk_size=2000, overlap=200):
        if not text:
            return []
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i + chunk_size])
            i += chunk_size - overlap
        return chunks

    def extract_text(self, file_path):
        """
        Extracts text natively from various document formats (PDF, DOCX, TXT).
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                text = ""
                try:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text += extracted + "\n"
                    
                    if len(text.strip()) < 50:
                        raise ValueError("PyPDF2 returned insufficient text.")
                except Exception as e:
                    logger.warning(f"PyPDF2 failed ({e}), falling back to pdfplumber...")
                    try:
                        import pdfplumber
                        text = ""
                        with pdfplumber.open(file_path) as pdf:
                            for page in pdf.pages:
                                text += (page.extract_text() or "") + "\n"
                    except ImportError:
                        logger.error("pdfplumber not installed for fallback.")
                return text
            elif ext in ['.docx', '.doc']:
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Text Extraction Failed for {file_path}: {e}")
            return ""

    def parse(self, file_path, job_description=None):
        """
        Main entry point: Extracts text -> Chunks (RAG) -> Analyzes via AIEngine.
        Returns a structured dictionary compatible with the Django application.
        """
        # 1. Extract raw text natively
        raw_text = self.extract_text(file_path)
        if not raw_text:
            logger.error("No text extracted from resume.")
            return None

        # 1.2 Language Detection
        detected_lang = "en"
        try:
            from langdetect import detect
            detected_lang = detect(raw_text)
            logger.info(f"Detected Language: {detected_lang}")
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")

        # 2. RAG Chunking
        # Even if we don't use a vector DB for a single resume, 
        # chunking ensures we stay within token limits for all engines.
        chunks = self.split_text(raw_text)
        # For analysis, we typically use the first few major chunks or the full text if it's manageable.
        # Gemini-1.5 handles huge context, but our fallback (Groq/Llama) has smaller windows.
        # We'll pass the consolidated text (up to a limit) to the AIEngine.
        processed_text = "\n---\n".join(chunks[:5]) # Limit to ~10k tokens for stability

        # 3. Analyze via Central AI Engine
        if not job_description:
            job_description = "General professional role evaluation based on skills and experience."

        analysis_json_str = self.ai_engine.analyze_resume(processed_text, job_description)
        
        # 4. Parse Structured JSON Output (CRITICAL)
        try:
            analysis_data = json.loads(analysis_json_str)
        except json.JSONDecodeError:
            logger.error("AIEngine returned invalid JSON for resume analysis.")
            # Graceful recovery with schema-compliant fallback
            analysis_data = {
                "ats_score": 50,
                "strengths": ["Experience extracted but analysis was non-JSON"],
                "missing_skills": ["Unable to determine precisely"],
                "recommendation": "Manual Review Required"
            }

        # 5. Build final response object
        return {
            'text': raw_text,
            'ats_score': analysis_data.get('ats_score', 0),
            'strengths': analysis_data.get('strengths', []),
            'missing_skills': analysis_data.get('missing_skills', []),
            'recommendation': analysis_data.get('recommendation', 'Reject'),
            # Extract basic metadata via regex fallback for legacy DB support if needed
            'email': self._extract_email_fallback(raw_text),
            'phone': self._extract_phone_fallback(raw_text),
            'detected_language': detected_lang
        }

    def _extract_email_fallback(self, text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    def _extract_phone_fallback(self, text):
        phone_pattern = r'\b\d{10}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        return phones[0] if phones else None

if __name__ == "__main__":
    # Test stub
    parser = ResumeParser()
    print("[SUCCESS] LangChain RAG Resume Parser Initialized.")

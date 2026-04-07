from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
import json
from .utils.media_processing import fetch_interview_frames
from .utils.report_generator import generate_proctoring_pdf
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test

# --- SmartRecruit Models ---
# Import moved here to ensure availability across admin views
# from jobs.models import ActivityLog, Candidate, Application (imported inside views to avoid circularity if needed, but standard is fine)


# --- SmartRecruit Central Brain ---
from .chatbot import bot
from core.ai_engine import AIEngine
from core.utils.proctor_engine import ProctorEngine
from core.utils.email_service import send_async_email
from core.utils.media_processing import fetch_interview_frames
from core.utils.blockchain_engine import verify_hash_on_chain
from core.utils.boilerplates import get_boilerplate

logger = logging.getLogger(__name__)

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def _get_safe_redirect(request, default='dashboard'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return next_url
    return reverse(default)

@login_required
def chatbot_api(request):
    """
    Standard Text Chat API.
    Delegates to SmartBot (which uses AIEngine).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Neural transmission empty.'}, status=400)
            
            # Use the global SmartBot instance
            ai_response = bot.get_response(user_message, user=request.user)
            return JsonResponse({'response': ai_response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method Not Allowed'}, status=405)

@login_required
def voice_assistant_api(request):
    """
    Dedicated Voice Assistant API.
    Routes directly to Centralized AIEngine (Groq preferred for speed)
    and forcefully strips markdown for clean TTS playback.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transcript = data.get('transcript', '').strip()
            
            if not transcript:
                return JsonResponse({'error': 'No auditory data received.'}, status=400)
            
            # --- 1. Call Central AIEngine (Step 2 Implementation) ---
            ai = AIEngine()
            raw_response = ai.get_voice_response(user_audio_text=transcript)
            
            # --- 2. Voice-Specific Data Cleansing (CRITICAL for TTS) ---
            # TTS engines choke on Markdown symbols like **, #, etc.
            clean_response = raw_response.replace("*", "").replace("#", "").replace("`", "").strip()
            
            voice_pref = getattr(request.user, 'voice_preference', 'female')
            
            return JsonResponse({
                'response': clean_response,
                'voice_preference': voice_pref
            })
        except Exception as e:
            logger.error(f"[VoiceAssistant] AIEngine call failed: {e}")
            return JsonResponse({'error': "Voice engine temporarily offline."}, status=500)
            
    return JsonResponse({'error': 'Method Not Allowed'}, status=405)


# =========================================
# CRITICAL FIX: Correct Model Imports
# =========================================
from .models import User
from jobs.models import JobPosting  # Imported from the correct app
from .forms import CustomUserCreationForm  # Use the custom form

# =========================================
# AUTHENTICATION VIEWS
# =========================================
from django.views.decorators.cache import never_cache

@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Your account is ready. Welcome to SmartRecruit.")
            return redirect(_get_safe_redirect(request))
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

from django.views.decorators.csrf import csrf_protect

@never_cache
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        remember_me = request.POST.get('remember') == 'on'
        lookup_identifier = identifier

        if '@' in identifier:
            existing_user = User.objects.filter(email__iexact=identifier).first()
            if existing_user:
                lookup_identifier = existing_user.username

        user = authenticate(request, username=lookup_identifier, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(60 * 60 * 24 * 14)
            
            # Core Fix: Inject JWT creation
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}.")
            
            # RBAC Redirection: Route each role to its dedicated workspace
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and next_url.startswith('/'):
                redirect_url = next_url
            elif user.is_superuser:
                redirect_url = reverse('admin_dashboard')
            elif getattr(user, 'is_recruiter', False):
                redirect_url = reverse('dashboard')
            else:
                # Candidate → Career Multiverse (job feed)
                redirect_url = reverse('job_list')
            
            response = redirect(redirect_url)
            response.set_cookie('access_token', str(refresh.access_token), httponly=True)
            response.set_cookie('refresh_token', str(refresh), httponly=True)
            return response
        else:
            messages.error(request, "Invalid credentials. Use your username/email and password.")
    return render(request, 'login.html', {'next': request.GET.get('next', '')})

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_POST
def logout_view(request):
    """
    Performs a global logout. Requires POST for CSRF protection (Django 5.x standard).
    The logout form in base.html includes {% csrf_token %}.
    """
    logout(request)
    if hasattr(request, 'session'):
        request.session.flush()
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    response.delete_cookie('jwt')
    response.delete_cookie('sessionid')
    return response

def forgot_password_view(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            try:
                token_generator = PasswordResetTokenGenerator()
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token = token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('reset_password_confirm', kwargs={'uidb64': uidb64, 'token': token})
                )
                subject = 'Password Reset Request - SmartRecruit'
                message = (
                    f"Hello {user.get_full_name() or user.username},\n\n"
                    "We received a request to reset your SmartRecruit password.\n"
                    f"Reset it here: {reset_url}\n\n"
                    "If you did not request this, you can ignore this email."
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER, ['rajlalwani511@gmail.com'], fail_silently=False)
            except Exception as e:
                logger.warning(f"Error sending password reset email: {e}")

        messages.success(
            request,
            "If an account exists for that email address, a password reset link has been sent."
        )
        return redirect('forgot_password')
        
    return render(request, 'forgot_password.html')

def reset_password_confirm_view(request, uidb64, token):
    token_generator = PasswordResetTokenGenerator()
    user = None
    valid_link = False

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        valid_link = token_generator.check_token(user, token)
    except Exception:
        user = None
        valid_link = False

    if not valid_link:
        messages.error(request, "This password reset link is invalid or has expired.")
        return render(request, 'reset_password_confirm.html', {
            'token': token,
            'uidb64': uidb64,
            'valid_link': False,
            'token_val': token,
            'uidb64_val': uidb64,
        })

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password or new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                validate_password(new_password, user=user)
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully. You can now sign in.")
                return redirect('login')
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
             
    return render(request, 'reset_password_confirm.html', {
        'token': token,
        'uidb64': uidb64,
        'valid_link': True,
    })

def offline_view(request):
    """
    Renders the PWA offline fallback page.
    """
    return render(request, 'offline.html')

def service_worker(request):
    response = render(request, 'js/service-worker.js', content_type='application/javascript')
    return response

def manifest(request):
    response = render(request, 'manifest.json', content_type='application/json')
    return response

# =========================================
# DASHBOARD VIEW
# =========================================
@login_required
def dashboard(request):
    from .services import DashboardService
    
    # 1. CANDIDATE DASHBOARD
    if hasattr(request.user, 'is_candidate') and request.user.is_candidate:
        context = DashboardService.get_candidate_context(request.user)
        return render(request, 'candidate_dashboard.html', context)
    
    # 2. ADMIN DASHBOARD
    elif getattr(request.user, 'is_superuser', False):
        return redirect('admin_dashboard')
        
    # 3. RECRUITER DASHBOARD
    else:
        # Trigger Autonomous Housekeeping (Flow B & C)
        from jobs.utils import run_system_housekeeping
        run_system_housekeeping()

        context = DashboardService.get_recruiter_context(request.user)
        return render(request, 'recruiter_dashboard.html', context)

# =========================================
# SETTINGS VIEW
# =========================================
@login_required
def settings_view(request):
    """
    Advanced Settings View (Phase 6)
    Handles: Profile, Appearance, Security, Hiring, AI Hub, Notifications, Performance
    """
    from jobs.models import UserUIProfile, AIUsageLog, AuditLog # Lazy imports
    
    # Ensure UI Profile exists
    ui_profile, created = UserUIProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. PROFILE UPDATE
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.professional_title = request.POST.get('professional_title', '')
            request.user.save()
            
            # Log action
            AuditLog.objects.create(user=request.user, action="Profile Update", ip_address=request.META.get('REMOTE_ADDR'))
            messages.success(request, "Neural profile synchronized successfully.")

        # SYSTEM ALERTS (Telemetry)
        elif action == 'update_telemetry':
            ui_profile.smtp_alerts_enabled = request.POST.get('smtp_alerts') == 'on'
            ui_profile.high_value_ping_enabled = request.POST.get('high_value_ping') == 'on'
            ui_profile.save()
            AuditLog.objects.create(user=request.user, action="Notification Preferences Updated", status="SUCCESS")
            messages.success(request, 'System telemetry protocols synchronized successfully.')

        # 2. PASSWORD CHANGE
        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                AuditLog.objects.create(user=request.user, action="Password Change", status="SUCCESS")
                messages.success(request, 'Security protocols updated. Password changed successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Security Error: {error}")

        # Blind Hiring Toggle
        elif action == 'toggle_blind_hiring':
            blind_status = request.POST.get('blind_hiring') == 'on'
            request.user.blind_hiring = blind_status
            request.user.save()
            messages.success(request, f"Blind Hiring Mode {'Enabled' if blind_status else 'Disabled'}.")
            
        # Voice Preference Setup
        elif action == 'update_voice_preference':
            voice = request.POST.get('voice_preference', 'female')
            if voice in ['female', 'male']:
                request.user.voice_preference = voice
                request.user.save()
                messages.success(request, "Voice Assistant preference updated!")
        
        # Model Selection
        elif action == 'update_model_preference':
            model = request.POST.get('model_preference', 'gemini-2.0-flash')
            if model in ['gemini-2.0-flash', 'gemini-1.5-pro']:
                request.user.model_preference = model
                request.user.save()
                messages.success(request, f"AI Model Preference set to {model}!")
        
        # ATS Sync Mapping (Phase 12)
        elif action == 'update_ats_config' and request.user.is_recruiter:
            from jobs.models import ATSSyncConfig
            internal_stage = request.POST.get('internal_stage')
            external_ats_stage = request.POST.get('external_ats_stage')
            
            if internal_stage and external_ats_stage:
                config, created = ATSSyncConfig.objects.update_or_create(
                    internal_stage=internal_stage,
                    defaults={'external_ats_stage': external_ats_stage, 'is_active': True}
                )
                AuditLog.objects.create(user=request.user, action="ATS Mapping Updated", details=f"{internal_stage} -> {external_ats_stage}")
                messages.success(request, f"ATS Bridge updated: {internal_stage} is now mapped to '{external_ats_stage}'.")

        return redirect('settings')
    
    # Pre-fetch ATS configs for the UI
    from jobs.models import ATSSyncConfig
    ats_configs = ATSSyncConfig.objects.filter(is_active=True)
    
    return render(request, 'settings.html', {
        'user': request.user,
        'ats_configs': ats_configs
    })


# =========================================
# SESSION TERMINATION
# =========================================
@login_required
def terminate_session(request):
    """
    Terminates an active interview session.
    Clears session data, marks the Interview as TERMINATED, and redirects.
    """
    from jobs.models import Interview
    
    interview_id = request.POST.get('interview_id') or request.session.get('active_interview_id')
    
    if interview_id:
        try:
            interview = Interview.objects.get(id=interview_id)
            interview.status = 'TERMINATED'
            interview.feedback = (interview.feedback or '') + '\n[Session terminated by user]'
            interview.save()
            logger.info(f"[TerminateSession] Interview #{interview_id} terminated by {request.user.username}")
        except Interview.DoesNotExist:
            logger.warning(f"[TerminateSession] Interview #{interview_id} not found")
    
    # Clear all interview-related session keys
    session_keys_to_clear = [
        'active_interview_id', 'interview_questions', 'interview_answers',
        'interview_context', 'current_question_index', 'interview_start_time',
    ]
    for key in session_keys_to_clear:
        request.session.pop(key, None)
    
    messages.info(request, "Interview session terminated. Your progress has been saved.")
    return redirect('dashboard')


# =========================================
# SENTIMENT DATA COLLECTION API (with Server-Side AI)
# =========================================
@login_required
def save_sentiment_data(request):
    """
    Receives webcam frames from the sentiment widget, runs FER-based
    facial expression analysis on the server, saves the result to
    SentimentLog, and returns the detected emotion to the frontend.

    POST payload: { frame: str (base64 JPEG), context: str, interview_id: int (optional) }
    Returns: { ok, emotion, display_label, score }
    """
    from jobs.models import Interview, SentimentLog
    from core.utils.ai_logic import analyze_frame

    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    try:
        data = json.loads(request.body)
        frame_data = data.get('frame', '')
        interview_id = data.get('interview_id')

        # ── Run server-side FER analysis on the frame ──
        if frame_data:
            from Sentiment_Analyzer.sentiment_engine import SentimentEngine
            engine = SentimentEngine()
            result = engine.process_frame(frame_data)
        else:
            # Fallback: accept a client-provided label (legacy support)
            client_label = data.get('label', 'neutral').lower()
            label_map = {
                'confident': 'happy', 'focused': 'neutral',
                'nervous': 'fearful', 'high stress': 'angry',
            }
            emotion = label_map.get(client_label, client_label)
            valid_emotions = ['happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised', 'neutral']
            if emotion not in valid_emotions:
                emotion = 'neutral'
            result = {
                'emotion': emotion,
                'display_label': client_label.title(),
                'score': float(data.get('score', 0.0)),
                'all_emotions': {},
            }

        # ── Resolve interview link ──
        interview = None
        if interview_id:
            try:
                interview = Interview.objects.get(id=interview_id)
            except Interview.DoesNotExist:
                pass

        # ── Persist to SentimentLog ──
        SentimentLog.objects.create(
            interview=interview,
            emotion=result['emotion'],
            score=min(max(result['score'], 0.0), 1.0),
            raw_expressions={
                'display_label': result['display_label'],
                'risk_level': result.get('risk_level', 'Low'),
                'flags': result.get('flags', []),
                'face_count': result.get('face_count', 0),
                'all_emotions': result.get('all_emotions', {}),
                'context': data.get('context', ''),
                'is_proctoring': data.get('proctoring', False),
            },
        )

        return JsonResponse({
            'ok': True,
            'emotion': result['emotion'],
            'display_label': result['display_label'],
            'score': result['score'],
            'risk_level': result.get('risk_level', 'Low'),
            'flags': result.get('flags', []),
        })
    except Exception as e:
        logger.error(f"[SaveSentiment] Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def get_live_proctoring(request):
    """
    Returns the latest 10 proctoring logs for active interviews.
    """
    from jobs.models import SentimentLog
    from django.db.models import Q
    logs = SentimentLog.objects.filter(
        Q(raw_expressions__is_proctoring=True) | Q(proctoring_flags__isnull=False)
    ).order_by('-timestamp')[:10]
    
    data = []
    for log in logs:
        interview = log.interview
        candidate_name = "Unknown"
        is_flagged = False
        if interview:
            is_flagged = getattr(interview, 'is_flagged', False)
            if interview.application and interview.application.candidate:
                candidate_name = interview.application.candidate.full_name
            
        # Extract flags from either old or new field
        flags = log.proctoring_flags.get('violations', []) if log.proctoring_flags else log.raw_expressions.get('flags', [])
        risk_level = "High" if is_flagged else ("Medium" if flags else "Low")
        
        data.append({
            'id': log.id,
            'candidate': candidate_name,
            'timestamp': log.timestamp.strftime("%H:%M:%S"),
            'risk_level': risk_level,
            'flags': flags,
            'is_flagged': is_flagged,
            'interview_id': interview.id if interview else None,
            'application_id': interview.application.id if (interview and interview.application) else None
        })
    
    return JsonResponse({'ok': True, 'logs': data})

@login_required
def get_session_frames(request, interview_id):
    """Returns chronologically sorted frames for replay."""
    frames = fetch_interview_frames(interview_id)
    return JsonResponse({'ok': True, 'frames': frames})

@login_required
def download_proctoring_report(request, interview_id):
    """Generates and downloads a PDF evidence report."""
    try:
        interview = Interview.objects.get(id=interview_id)
        frames = fetch_interview_frames(interview_id)
        flagged_frames = [f for f in frames if f['violations']]
        
        pdf_data = generate_proctoring_pdf(
            interview.application.candidate.full_name,
            interview.application.job.title,
            flagged_frames if flagged_frames else frames[:10] # Fallback to first 10 if no violations
        )
        
        fname = f"ProctorReport_{interview.application.candidate.full_name.replace(' ', '_')}.pdf"
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        return response
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return HttpResponse("Error generating report", status=500)


# =========================================
# AI CONTENT REGENERATION API
# =========================================
@login_required
def regenerate_content(request):
    """
    Generic AI content regeneration endpoint.
    Accepts content_type ('resume_summary', 'interview_question', 'cover_letter')
    and context data, returns freshly AI-generated content.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        content_type = data.get('content_type', 'resume_summary')
        context = data.get('context', '')
        current_text = data.get('current_text', '')
        
        ai = AIEngine()
        
        prompts = {
            'resume_summary': f"Regenerate and improve this professional resume summary. Make it more impactful, concise, and ATS-optimized. Current summary: {current_text}. Context: {context}",
            'interview_question': f"Generate a fresh, challenging interview question for this context: {context}. The previous question was: {current_text}. Generate something different.",
            'cover_letter': f"Regenerate this cover letter paragraph to be more compelling and specific. Current text: {current_text}. Job context: {context}",
            'job_description': f"Refine and enhance this job description to attract top talent. Current JD: {current_text}. Make it more engaging while keeping technical accuracy.",
        }
        
        prompt = prompts.get(content_type, f"Improve and regenerate this text: {current_text}")
        
        new_content = ai.get_chat_response(prompt)
        
        return JsonResponse({
            'ok': True,
            'content': new_content,
            'content_type': content_type,
        })
    except Exception as e:
        logger.error(f"[RegenerateContent] Error: {e}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
def proctoring_analysis_api(request):
    """
    Real-time video proctoring API.
    Processes frames for face count and eye gaze.
    """
    from jobs.models import Interview, SentimentLog
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    try:
        data = json.loads(request.body)
        frame_b64 = data.get('frame', '')
        interview_id = data.get('interview_id')

        engine = ProctorEngine()
        result = engine.analyze_frame(frame_b64)

        if "error" in result:
            return JsonResponse({'ok': False, 'error': result["error"]}, status=400)

        # Log violation if face_count != 1 or wandering
        if result["face_count"] != 1 or result["eye_gaze"] == "WANDERING":
            # 1. Resolve interview
            interview = None
            if interview_id:
                try:
                    interview = Interview.objects.get(id=interview_id)
                except Interview.DoesNotExist:
                    pass
            
        # 2. Track threshold in Interview model
        session_key = f"proctor_flags_{interview_id}" if interview_id else "proctor_flags_generic"
        current_flags = request.session.get(session_key, 0) + 1
        request.session[session_key] = current_flags

        if interview:
            interview.flag_count = current_flags
            # Use dynamic threshold for is_flagged
            from jobs.models import PlatformSetting
            flags_max = int(PlatformSetting.get('PROCTOR_FLAGS_MAX', 5))
            if current_flags >= flags_max:
                interview.is_flagged = True
                interview.proctoring_status = 'PENDING'
            interview.save()

        # 3. Log to SentimentLog
            SentimentLog.objects.create(
                interview=interview,
                emotion='neutral',
                score=0.0,
                frame=frame_b64,
                proctoring_flags={
                    'face_count': result["face_count"],
                    'eye_gaze': result["eye_gaze"],
                    'violations': result["violations"],
                    'total_session_flags': current_flags
                }
            )

            # 4. Trigger Alert if Threshold Hit (Rule: >= 3)
            if current_flags == 3: 
                if interview:
                    interview.is_flagged = True
                    interview.save()
                    
                    # Send Asynchronous Email Alert
                    recipient = getattr(settings, 'HR_EMAIL', "hr@smartrecruit.ai")
                    if interview.application.job.recruiter.email:
                        recipient = interview.application.job.recruiter.email

                    subject = f"🚨 INTEGRITY ALERT: {interview.application.candidate.full_name}"
                    context = {
                        'candidate_name': interview.application.candidate.full_name,
                        'job_title': interview.application.job.title,
                        'violation_count': current_flags,
                        'violation_type': ", ".join(result["violations"]) if result["violations"] else "Suspicious Behavior",
                        'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'log_url': request.build_absolute_uri(reverse('dashboard'))
                    }
                    send_async_email(subject, 'emails/proctoring_alert.html', context, [recipient])

        return JsonResponse({
            'ok': True,
            'face_count': result["face_count"],
            'eye_gaze': result["eye_gaze"],
            'violations': result["violations"],
            'flags_count': current_flags if ('current_flags' in locals()) else 0
        })
    except Exception as e:
        logger.error(f"[ProctoringAPI] Error: {e}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
def get_interview_replay_api(request, interview_id):
    """
    Returns a sequential list of frames and violations for replay.
    """
    try:
        sequence = fetch_interview_frames(interview_id)
        return JsonResponse({
            'ok': True, 
            'interview_id': interview_id,
            'frames': sequence
        })
    except Exception as e:
        logger.error(f"[ReplayAPI] Error: {e}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
def blockchain_verify_api(request, candidate_id):
    """
    Triggers a simulated blockchain verification for a candidate's credentials.
    """
    from jobs.models import Candidate
    try:
        candidate = Candidate.objects.get(id=candidate_id)
        # Using the existing hash stored in the model for simulation
        success, tx_id = verify_hash_on_chain(candidate.blockchain_hash)
        
        if success:
            candidate.is_verified_on_chain = True
            candidate.blockchain_tx_id = tx_id
            candidate.save()
            return JsonResponse({'ok': True, 'tx_id': tx_id})
        else:
            return JsonResponse({'ok': False, 'error': 'Hash not found on decentralized ledger'})
            
    except Candidate.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Candidate not found'}, status=404)
    except Exception as e:
        logger.error(f"[BlockchainAPI] Error: {e}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
def get_boilerplate_api(request):
    """
    Returns the starter code for a specific language.
    """
    lang = request.GET.get('lang', 'python')
    code = get_boilerplate(lang)
    return JsonResponse({'ok': True, 'language': lang, 'code': code})

def verify_credential(request):
    """
    Public-facing portal to verify an interview credential hash.
    """
    context = {}
    cert_hash = request.POST.get('cert_hash', '').strip() or request.GET.get('hash', '').strip()
    
    if cert_hash:
        from core.utils.blockchain_sync import verify_certificate
        verification_result = verify_certificate(cert_hash)
        context['cert_hash'] = cert_hash
        context['result'] = verification_result

    return render(request, 'verify_credential.html', context)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def analyze_vocal_confidence(request):
    """
    API endpoint for Web Audio API chunks.
    Phase 13: Vocal Confidence & Stress Analyzer
    Bridge to Gemini/HuggingFace engines.
    """
    if request.method == 'POST':
        try:
            audio_bytes = request.body
            interview_id = request.headers.get('X-Interview-Id')
            transcript = request.headers.get('X-Transcript', '')
            
            # AI Engine Bridge (Centralized)
            from core.ai_engine import AIEngine
            from jobs.models import Interview, SentimentLog
            ai = AIEngine()
            
            # Advanced Prompt for Granular Metrics
            ai_prompt = f"""
            Analyze the vocal confidence and emotional state from this interview segment.
            TRANSCRIPT: '{transcript}'
            
            Return ONLY a JSON object with:
            {{
                "sentiment": "positive|neutral|negative",
                "confidence_score": 0-100,
                "stress_level": 0-100,
                "energy": 0-100,
                "insight": "1-sentence tip for the recruiter"
            }}
            """
            
            try:
                raw_response = ai.generate(user_prompt=ai_prompt, system_prompt="You are a professional behavioral psychologist.")
                import json
                analysis = json.loads(raw_response)
            except:
                # Fallback for parsing errors
                analysis = {
                    "sentiment": "neutral",
                    "confidence_score": 75,
                    "stress_level": 20,
                    "energy": 80,
                    "insight": "Maintaining steady pace."
                }
            
            sentiment = analysis.get('sentiment', 'neutral')
            conf_score = analysis.get('confidence_score', 80)
            
            from core.utils.audio_processor import audio_processor
            result = audio_processor.process_audio_chunk_sync(audio_bytes, transcript, sentiment, interview_id=interview_id)
            
            interview_obj = None
            if interview_id:
                try:
                    interview_obj = Interview.objects.get(id=interview_id)
                except:
                    pass
                    
            SentimentLog.objects.create(
                interview=interview_obj,
                emotion=sentiment,
                score=conf_score / 100.0,
                raw_expressions={
                    'transcript': transcript, 
                    'analysis': analysis,
                    'engine': 'Advanced Neural Suite'
                }
            )
            
            return JsonResponse({
                'status': 'success', 
                'sentiment': sentiment,
                'vocal_confidence': conf_score,
                'stress_level': analysis.get('stress_level', 20),
                'energy': analysis.get('energy', 80),
                'insight': analysis.get('insight', 'Stable')
            })
        except Exception as e:
            logger.error(f"[AnalyzeVocal] Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST required'}, status=405)

# =========================================
# ADMIN / SUPERUSER VIEWS  (Professional Suite)
# =========================================
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.http import HttpResponse
from django.core.paginator import Paginator
import csv, json
from datetime import timedelta

def is_admin_check(user):
    return user.is_active and user.is_superuser

# ─── Helpers ───────────────────────────────────────────────────────────────

def _admin_context(title, section):
    """Inject sidebar meta-data into every admin page context."""
    return {'page_title': title, 'active_section': section}

# ─── Dashboard ─────────────────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_dashboard(request):
    from jobs.models import JobPosting, Interview, Application
    from django.utils import timezone as tz

    total_users       = User.objects.count()
    total_candidates  = User.objects.filter(is_candidate=True).count()
    total_recruiters  = User.objects.filter(is_recruiter=True).count()
    active_jobs       = JobPosting.objects.filter(status='OPEN').count()
    closed_jobs       = JobPosting.objects.filter(status='CLOSED').count()
    total_applications = Application.objects.count()
    hired_count        = Application.objects.filter(status='HIRED').count()
    total_interviews   = Interview.objects.count()
    flagged_interviews = Interview.objects.filter(is_flagged=True).count()

    # Proctoring Statistics
    total_flags_count = sum(i.flag_count for i in Interview.objects.all())
    violation_rate = (flagged_interviews / total_interviews * 100) if total_interviews > 0 else 0
    
    # AI Engine Telemetry
    from jobs.models import PlatformSetting
    active_llm = PlatformSetting.get('ACTIVE_LLM', 'gemini-2.0-flash')
    
    # Calculate simulated token usage (1000 tokens per interview round as baseline)
    estimated_tokens = total_interviews * 3 * 1050 
    
    # System Health (Simulated Pings)
    system_health = {
        'database': 'ONLINE',
        'ai_engine': 'ONLINE',
        'media_vault': 'ONLINE',
        'webhooks': 'STABLE',
    }

    # --- Telemetry & Analytics (Zenith Phase 9.2) ---
    from django.utils import timezone as tz
    seven_days_ago = tz.now() - tz.timedelta(days=7)
    new_users      = User.objects.filter(date_joined__gte=seven_days_ago).count()
    recent_users   = User.objects.all().order_by('-date_joined')[:5]
    recent_flags   = Interview.objects.filter(is_flagged=True).select_related('application', 'application__candidate', 'application__job').order_by('-created_at')[:5]

    # Pipeline Funnel Metrics
    funnel = {
        'Applied': Application.objects.filter(status='APPLIED').count(),
        'Resume Selected': Application.objects.filter(status='RESUME_SELECTED').count(),
        'Technical Passed': Application.objects.filter(status='ROUND_1_PASSED').count(),
        'Practical Passed': Application.objects.filter(status='ROUND_2_PASSED').count(),
        'Offered': Application.objects.filter(status='OFFER_GENERATED').count(),
        'Hired': Application.objects.filter(status='HIRED').count(),
    }

    ctx = _admin_context('Command Center', 'dashboard')
    ctx.update({
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_recruiters': total_recruiters,
        'active_jobs': active_jobs,
        'closed_jobs': closed_jobs,
        'total_applications': total_applications,
        'hired_count': hired_count,
        'total_interviews': total_interviews,
        'flagged_interviews': flagged_interviews,
        'total_flags_count': total_flags_count,
        'violation_rate': round(violation_rate, 1),
        'active_llm': active_llm.upper(),
        'estimated_tokens': f"{estimated_tokens:,}",
        'system_health': system_health,
        'new_users': new_users,
        'recent_flags': recent_flags,
        'recent_users': recent_users,
        'funnel_json': json.dumps(funnel),
    })
    return render(request, 'core/admin_dashboard.html', ctx)

# ─── User Directory ────────────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_users(request):
    role_filter = request.GET.get('role', 'all')
    search_q    = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-date_joined')

    if role_filter == 'candidate':
        users = users.filter(is_candidate=True)
    elif role_filter == 'recruiter':
        users = users.filter(is_recruiter=True)
    elif role_filter == 'admin':
        users = users.filter(is_superuser=True)

    if search_q:
        users = users.filter(
            Q(username__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(first_name__icontains=search_q) |
            Q(last_name__icontains=search_q)
        )

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('User Directory', 'users')
    ctx.update({
        'users_list': page_obj,
        'page_obj': page_obj,
        'current_filter': role_filter,
        'search_q': search_q,
        'total_shown': paginator.count,
    })
    return render(request, 'core/admin_users.html', ctx)

@user_passes_test(is_admin_check)
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role     = request.POST.get('role', 'candidate')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                if role == 'admin':
                    user.is_superuser = True
                    user.is_staff = True
                elif role == 'recruiter':
                    user.is_recruiter = True
                else:
                    user.is_candidate = True
                user.save()
                messages.success(request, f"✓ User '{username}' created as {role.capitalize()}.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    return redirect('admin_users')

@user_passes_test(is_admin_check)
def admin_export_users(request):
    """Export all users to a CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="smartrecruit_users.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Status', 'Joined'])
    for u in User.objects.all().order_by('-date_joined'):
        if u.is_superuser:
            role = 'Admin'
        elif u.is_recruiter:
            role = 'Recruiter'
        else:
            role = 'Candidate'
        writer.writerow([
            u.id, u.username, u.email, u.first_name, u.last_name,
            role, 'Active' if u.is_active else 'Suspended',
            u.date_joined.strftime('%Y-%m-%d')
        ])
    return response

@user_passes_test(is_admin_check)
def admin_toggle_user_status(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if not user.is_superuser:
                user.is_active = not user.is_active
                user.save()
                action = "activated" if user.is_active else "suspended"
                messages.success(request, f"User '{user.username}' has been {action}.")
            else:
                messages.error(request, "Cannot suspend a fellow Administrator.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('admin_users')

@user_passes_test(is_admin_check)
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if not user.is_superuser:
                uname = user.username
                user.delete()
                messages.success(request, f"User '{uname}' permanently deleted.")
            else:
                messages.error(request, "Superusers cannot be deleted from the portal.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('admin_users')

# ─── Job Moderation ────────────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_jobs(request):
    from jobs.models import JobPosting
    status_f = request.GET.get('status', 'all')
    jobs = JobPosting.objects.all().order_by('-created_at')
    if status_f == 'open':
        jobs = jobs.filter(status='OPEN')
    elif status_f == 'closed':
        jobs = jobs.filter(status='CLOSED')
    elif status_f == 'pending':
        jobs = jobs.filter(status='PENDING')
    elif status_f == 'rejected':
        jobs = jobs.filter(status='REJECTED')

    jobs = jobs.annotate(app_count=Count('applications'))

    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('Job Moderation', 'jobs')
    ctx.update({
        'jobs_list': page_obj, 
        'page_obj': page_obj,
        'status_filter': status_f
    })
    return render(request, 'core/admin_jobs.html', ctx)

@user_passes_test(lambda u: u.is_superuser)
def system_health_dashboard(request):
    """Render the glassmorphism War Room dashboard."""
    return render(request, 'core/health_dashboard.html')

@user_passes_test(lambda u: u.is_superuser)
def system_health_api(request):
    """Execute background checks and return JSON status for the War Room."""
    from django.http import JsonResponse
    from jobs.models import Assessment, SentimentLog
    status = {"round1": False, "round2": False, "round3": False, "round4": False, "sentiment_logs": []}
    
    # Round 1: Gemini & PDF
    try:
        import PyPDF2
        from django.conf import settings
        if getattr(settings, 'GEMINI_API_KEY', None):
            status["round1"] = True
    except ImportError:
        pass
        
    # Round 2: Assessment Engine / DB
    try:
        count = Assessment.objects.count()
        status["round2"] = True
    except Exception:
        pass
        
    # Round 3: Live Sentiment Feed
    try:
        logs = SentimentLog.objects.order_by('-timestamp')[:5]
        status["sentiment_logs"] = [
            {"emotion": log.emotion, "score": float(log.confidence)*100 if hasattr(log, 'confidence') else 99.9, "time": log.timestamp.strftime("%H:%M:%S")}
            for log in logs
        ]
        status["round3"] = True
    except Exception:
        pass
        
    # Round 4: Email SMTP Ping
    try:
        from django.core.mail import get_connection
        connection = get_connection()
        connection.open()
        connection.close()
        status["round4"] = True
    except Exception:
        pass
        
    return JsonResponse(status)

@user_passes_test(is_admin_check)
def admin_toggle_job_status(request, job_id):
    if request.method == 'POST':
        from jobs.models import JobPosting
        try:
            job = JobPosting.objects.get(id=job_id)
            job.status = 'CLOSED' if job.status == 'OPEN' else 'OPEN'
            job.save()
            messages.success(request, f"Job '{job.title}' is now {job.status}.")
        except JobPosting.DoesNotExist:
            messages.error(request, "Job not found.")
    return redirect('admin_jobs')

@user_passes_test(is_admin_check)
def admin_approve_job(request, job_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        from jobs.models import JobPosting
        from jobs.utils_notifications import send_notification
        try:
            job = JobPosting.objects.get(id=job_id)
            if action == 'approve':
                job.status = 'OPEN'
                job.save()
                messages.success(request, f"Job '{job.title}' approved successfully.")
                send_notification(
                    user=job.recruiter,
                    title="Job Posting Approved",
                    message=f"Your job posting '{job.title}' has been approved and is now live.",
                    link=f"/jobs/{job.id}/",
                    type="SUCCESS"
                )
            elif action == 'reject':
                job.status = 'REJECTED'
                job.save()
                messages.error(request, f"Job '{job.title}' rejected.")
                send_notification(
                    user=job.recruiter,
                    title="Job Posting Rejected",
                    message=f"Your job posting '{job.title}' has been rejected by administration.",
                    link=f"#",
                    type="ERROR"
                )
        except JobPosting.DoesNotExist:
            messages.error(request, "Job not found.")
    return redirect('admin_jobs')

# ─── Application Oversight ─────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_applications(request):
    from jobs.models import Application
    stage_f  = request.GET.get('stage', 'all')
    search_q = request.GET.get('q', '').strip()

    apps = Application.objects.all().select_related(
        'job', 'candidate'
    ).order_by('-applied_at')

    if stage_f != 'all':
        apps = apps.filter(status=stage_f)
    if search_q:
        apps = apps.filter(
            Q(candidate__full_name__icontains=search_q) |
            Q(job__title__icontains=search_q)
        )

    from jobs.models import Application as App
    stage_choices = App.STATUS_CHOICES

    paginator = Paginator(apps, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('Application Oversight', 'applications')
    ctx.update({
        'apps_list': page_obj,
        'page_obj': page_obj,
        'stage_filter': stage_f,
        'search_q': search_q,
        'stage_choices': stage_choices,
        'total_shown': paginator.count,
    })
    return render(request, 'core/admin_applications.html', ctx)

# ─── Interview Oversight ───────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_interviews(request):
    from jobs.models import Interview
    flag_f = request.GET.get('flag', 'all')

    interviews = Interview.objects.all().select_related(
        'application__candidate', 'application__job'
    ).order_by('-created_at')

    if flag_f == 'flagged':
        interviews = interviews.filter(is_flagged=True)
    elif flag_f == 'clean':
        interviews = interviews.filter(is_flagged=False)

    paginator = Paginator(interviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('Interview Oversight', 'interviews')
    ctx.update({
        'interviews_list': page_obj,
        'page_obj': page_obj,
        'flag_filter': flag_f,
        'total_flagged': Interview.objects.filter(is_flagged=True).count(),
    })
    return render(request, 'core/admin_interviews.html', ctx)

# ─── System / Audit Log ────────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_system_log(request):
    from jobs.models import BlockchainAuditLog
    logs = BlockchainAuditLog.objects.all().order_by('-timestamp')
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('System Audit Log', 'system_log')
    ctx.update({'logs': page_obj, 'page_obj': page_obj})
    return render(request, 'core/admin_system_log.html', ctx)

# ─── Analytics & Reports ───────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_analytics(request):
    from jobs.models import JobPosting, Application, Interview
    from django.utils import timezone as tz
    from datetime import timedelta
    import json as _json

    # Applications per last 14 days
    today = tz.now().date()
    labels, app_counts = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%b %d'))
        app_counts.append(Application.objects.filter(applied_at__date=d).count())

    # Status breakdown for donut chart
    status_map = {
        'Applied': Application.objects.filter(status='APPLIED').count(),
        'Screening': Application.objects.filter(status__in=['RESUME_SCREENING', 'RESUME_SELECTED']).count(),
        'Round 1': Application.objects.filter(status__icontains='ROUND_1').count(),
        'Round 2': Application.objects.filter(status__icontains='ROUND_2').count(),
        'Interview': Application.objects.filter(status__icontains='ROUND_3').count(),
        'HR Round': Application.objects.filter(status='HR_ROUND_PENDING').count(),
        'Hired': Application.objects.filter(status='HIRED').count(),
        'Rejected': Application.objects.filter(status__icontains='REJECTED').count(),
    }

    # Top recruiters by hires
    top_recruiters = (
        User.objects.filter(is_recruiter=True)
        .annotate(
            job_count=Count('posted_jobs', distinct=True),
            hire_count=Count('posted_jobs__applications', filter=Q(posted_jobs__applications__status='HIRED'), distinct=True),
            applicant_count=Count('posted_jobs__applications', distinct=True),
        )
        .order_by('-hire_count')[:10]
    )

    # Interview flags by type
    total_interviews = Interview.objects.count()
    flagged_count   = Interview.objects.filter(is_flagged=True).count()
    clean_count     = total_interviews - flagged_count

    ctx = _admin_context('Analytics & Reports', 'analytics')
    ctx.update({
        'chart_labels': _json.dumps(labels),
        'chart_apps': _json.dumps(app_counts),
        'status_labels': _json.dumps(list(status_map.keys())),
        'status_data': _json.dumps(list(status_map.values())),
        'top_recruiters': top_recruiters,
        'total_interviews': total_interviews,
        'flagged_count': flagged_count,
        'clean_count': clean_count,
    })
    return render(request, 'core/admin_analytics.html', ctx)

# ─── Platform Settings ─────────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_platform_settings(request):
    from jobs.models import PlatformSetting

    DEFAULTS = [
        {'key': 'passing_score_r1',     'label': 'Round 1 Default Passing Score (%)',   'group': 'assessments', 'value': '70'},
        {'key': 'passing_score_r2',     'label': 'Round 2 Default Passing Score (%)',   'group': 'assessments', 'value': '70'},
        {'key': 'time_limit_r1',        'label': 'Round 1 Default Time Limit (mins)',   'group': 'assessments', 'value': '45'},
        {'key': 'time_limit_r2',        'label': 'Round 2 Default Time Limit (mins)',   'group': 'assessments', 'value': '60'},
        {'key': 'blind_hiring_global',  'label': 'Enforce Blind Hiring Platform-Wide',  'group': 'hiring',      'value': 'false'},
        {'key': 'maintenance_notice',   'label': 'Platform Maintenance Notice (shown to all users)', 'group': 'platform', 'value': ''},
        {'key': 'allow_self_register',  'label': 'Allow Public Self-Registration',      'group': 'platform',    'value': 'true'},
        {'key': 'max_applications_per_candidate', 'label': 'Max Open Applications per Candidate', 'group': 'platform', 'value': '10'},
    ]
    # Seed defaults if not present
    for d in DEFAULTS:
        PlatformSetting.objects.get_or_create(
            key=d['key'],
            defaults={'value': d['value'], 'label': d['label'], 'group': d['group']}
        )

    if request.method == 'POST':
        for d in DEFAULTS:
            new_val = request.POST.get(d['key'], '').strip()
            PlatformSetting.set(d['key'], new_val, label=d['label'], group=d['group'])
        messages.success(request, '✓ Platform settings saved successfully.')
        return redirect('admin_platform_settings')

    settings_all = PlatformSetting.objects.all()
    ctx = _admin_context('Platform Settings', 'settings')
    ctx.update({'settings_all': settings_all, 'defaults': DEFAULTS})
    return render(request, 'core/admin_settings.html', ctx)

# ─── Broadcast Notifications ───────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_broadcast(request):
    from jobs.models import Notification

    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        body     = request.POST.get('body', '').strip()
        audience = request.POST.get('audience', 'all')
        notif_type = request.POST.get('type', 'INFO')

        if not title or not body:
            messages.error(request, 'Title and message body are required.')
        else:
            if audience == 'candidates':
                recipients = User.objects.filter(is_candidate=True, is_active=True)
            elif audience == 'recruiters':
                recipients = User.objects.filter(is_recruiter=True, is_active=True)
            else:
                recipients = User.objects.filter(is_active=True)

            notifs = [
                Notification(user=u, title=title, message=body, type=notif_type)
                for u in recipients
            ]
            Notification.objects.bulk_create(notifs)
            messages.success(request, f'✓ Broadcast sent to {len(notifs)} user{("s" if len(notifs) != 1 else "")}.')
            return redirect('admin_broadcast')

    recent_broadcasts = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    ctx = _admin_context('Broadcast Notifications', 'broadcast')
    ctx.update({'recent_broadcasts': recent_broadcasts})
    return render(request, 'core/admin_broadcast.html', ctx)

# ─── Recruiter Performance ─────────────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_recruiter_performance(request):
    from jobs.models import Application

    recruiters = (
        User.objects.filter(is_recruiter=True)
        .annotate(
            job_count=Count('posted_jobs', distinct=True),
            applicant_count=Count('posted_jobs__applications', distinct=True),
            hire_count=Count(
                'posted_jobs__applications',
                filter=Q(posted_jobs__applications__status='HIRED'),
                distinct=True
            ),
        )
        .order_by('-hire_count', '-applicant_count')
    )

    paginator = Paginator(recruiters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = _admin_context('Recruiter Performance', 'recruiters')
    ctx.update({'recruiters': page_obj, 'page_obj': page_obj})
    return render(request, 'core/admin_recruiter_performance.html', ctx)

# ─── AI Engine Configuration Hub ──────────────────────────────────────────

@user_passes_test(is_admin_check)
def admin_ai_hub(request):
    from jobs.models import PlatformSetting
    
    if request.method == 'POST':
        active_llm = request.POST.get('active_llm', 'gemini-2.0-flash')
        prompt_raj = request.POST.get('prompt_raj', '')
        prompt_botanist = request.POST.get('prompt_botanist', '')
        
        PlatformSetting.set('ACTIVE_LLM', active_llm, label='Active LLM Engine', group='ai_config')
        PlatformSetting.set('PROMPT_RAJ', prompt_raj, label='Raj Interviewer Persona', group='ai_config')
        PlatformSetting.set('PROMPT_BOTANIST', prompt_botanist, label='Botanist Persona', group='ai_config')
        
        messages.success(request, f"AI Hub constraints updated successfully. Active Engine: {active_llm.upper()}")
        return redirect('admin_ai_hub')
        
    current_llm = PlatformSetting.get('ACTIVE_LLM', 'gemini-2.0-flash')
    current_raj = PlatformSetting.get('PROMPT_RAJ', '')
    current_botanist = PlatformSetting.get('PROMPT_BOTANIST', '')
    
    if not current_raj:
        current_raj = "You are Raj, an elite AI Technical Interviewer for SmartRecruit..."
    if not current_botanist:
        current_botanist = "You are 'The Botanist', a highly sophisticated AI Behavioral Interviewer..."
    
    ctx = _admin_context('AI Engine Hub', 'ai_hub')
    ctx.update({
        'active_llm': current_llm,
        'prompt_raj': current_raj,
        'prompt_botanist': current_botanist,
    })
    return render(request, 'core/admin_ai_hub.html', ctx)

@login_required
@user_passes_test(is_admin_check)
def admin_compliance_vault(request):
    """
    Master Compliance Dashboard: Audit Logs, Data Retention Trigger, and Privacy Stats.
    """
    from jobs.models import ActivityLog, Candidate, Application
    from django.utils import timezone
    from datetime import timedelta
    
    audit_logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    
    # Stats
    total_candidates = Candidate.objects.count()
    total_applications = Application.objects.count()
    
    # 6-Month Retention Stats (Forecast)
    threshold = timezone.now() - timedelta(days=180)
    expired_count = Application.objects.filter(applied_at__lt=threshold).count()

    ctx = _admin_context('Compliance Vault', 'compliance')
    ctx.update({
        'audit_logs': audit_logs,
        'total_candidates': total_candidates,
        'total_applications': total_applications,
        'expired_count': expired_count,
        'retention_threshold': threshold.date(),
    })
    return render(request, 'core/admin_compliance_vault.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_integration_center(request):
    """
    ATS Sync Mapping Hub: Manage Workday/SAP stage mappings and Rule Triggers.
    """
    from jobs.models import ATSSyncConfig, TriggerRule, Application
    
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        
        if action_type == 'add_mapping':
            provider = request.POST.get('provider')
            internal_stage = request.POST.get('internal_stage')
            external_stage = request.POST.get('external_stage')
            ATSSyncConfig.objects.update_or_create(
                internal_stage=internal_stage,
                defaults={'provider': provider, 'external_ats_stage': external_stage}
            )
            messages.success(request, f"ATS Mapping for '{internal_stage}' updated.")
            
        elif action_type == 'add_trigger':
            name = request.POST.get('name')
            condition = request.POST.get('condition_type')
            threshold = request.POST.get('threshold')
            action = request.POST.get('action')
            TriggerRule.objects.create(
                name=name, condition_type=condition, 
                threshold=float(threshold) if threshold else None,
                action=action
            )
            messages.success(request, f"Trigger rule '{name}' activated.")

        return redirect('admin_integration_center')

    mappings = ATSSyncConfig.objects.all()
    triggers = TriggerRule.objects.all()
    
    ctx = _admin_context('Integration Hub', 'integrations')
    ctx.update({
        'mappings': mappings,
        'triggers': triggers,
        'internal_stages': [c[0] for c in Application.STATUS_CHOICES]
    })
    return render(request, 'core/admin_integration_center.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_api_keys(request):
    """
    Secure Vault: Rotate and manage encrypted API keys for external services.
    """
    from jobs.models import EncryptedAPIKey
    from core.utils.encryption import encrypt_value, decrypt_value
    
    if request.method == 'POST':
        service = request.POST.get('service_name')
        raw_key = request.POST.get('api_key')
        desc = request.POST.get('description', '')
        
        # Store encrypted
        encrypted = encrypt_value(raw_key)
        EncryptedAPIKey.objects.update_or_create(
            service_name=service,
            defaults={'encrypted_value': encrypted, 'description': desc}
        )
        messages.success(request, f"Encrypted key for {service} rotated successfully.")
        return redirect('admin_api_keys')

    keys = EncryptedAPIKey.objects.all()
    # For UI, we don't show the full decrypted key, just a hint or masked version
    vault_items = []
    for k in keys:
        vault_items.append({
            'service': k.service_name,
            'desc': k.description,
            'last_rotated': k.last_rotated,
            'masked_key': '••••••••' + decrypt_value(k.encrypted_value)[-4:] if k.encrypted_value else "EMPTY"
        })

    ctx = _admin_context('API Key Vault', 'api_vault')
    ctx.update({'vault_items': vault_items})
    return render(request, 'core/admin_api_keys.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_question_bank(request):
    """
    Master Repository & Governance for the Global Question Bank.
    Supports bulk import, bias detection (failure rates), and moderation.
    """
    from jobs.models import QuestionBank
    import csv
    
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        
        if action_type == 'bulk_import':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, "No neural data (CSV) detected for upload.")
            else:
                try:
                    decoded_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    
                    # Expected columns: round, category, question_text, options(JSON), correct_answer, explanation
                    count = 0
                    for row in reader:
                        try:
                            # Parse options from JSON string if provided, else empty list
                            raw_options = row.get('options', '[]').replace("'", '"') # Fix single quotes
                            options_list = json.loads(raw_options) if raw_options else []
                            
                            QuestionBank.objects.create(
                                round=row['round'],
                                category=row.get('category', 'LOGICAL'),
                                difficulty=row.get('difficulty', 'medium'),
                                question_text=row['question_text'],
                                options=options_list,
                                correct_answer=row['correct_answer'],
                                explanation=row.get('explanation', ''),
                                is_coding=row.get('is_coding', 'False').lower() == 'true',
                                moderation_status='APPROVED', # Admin imports are auto-approved
                                submitted_by=request.user
                            )
                            count += 1
                        except Exception as e:
                            logger.error(f"Import error at row {count+1}: {e}")
                            
                    messages.success(request, f"✓ Neural upload successful. {count} questions integrated into the bank.")
                except Exception as e:
                    messages.error(request, f"Encryption/Format error: {str(e)}")
            return redirect('admin_question_bank')

    # Filters
    q_round = request.GET.get('round', 'all')
    q_status = request.GET.get('status', 'all')
    
    questions = QuestionBank.objects.all().select_related('submitted_by').order_by('-created_at')
    
    if q_round != 'all':
        questions = questions.filter(round=q_round)
    if q_status != 'all':
        questions = questions.filter(moderation_status=q_status)

    # Bias Detection (Analytics)
    # Questions with high failure rates (attempted > 5 times)
    high_failure_questions = []
    candidates_for_review = QuestionBank.objects.filter(attempt_count__gt=5)
    for q in candidates_for_review:
        fail_rate = (q.failure_count / q.attempt_count) * 100
        if fail_rate > 60: # Threshold for 'Hard/Biased'
            high_failure_questions.append({
                'id': q.id,
                'text': q.question_text[:60] + "...",
                'fail_rate': round(fail_rate, 1),
                'attempts': q.attempt_count
            })
    
    high_failure_questions = sorted(high_failure_questions, key=lambda x: x['fail_rate'], reverse=True)[:5]

    ctx = _admin_context('Question Governance', 'question_bank')
    ctx.update({
        'questions': questions[:100], 
        'high_failure_questions': high_failure_questions,
        'round_choices': QuestionBank.ROUND_CHOICES,
        'status_choices': QuestionBank.MODERATION_CHOICES,
        'q_round': q_round,
        'q_status': q_status,
        'total_questions': QuestionBank.objects.count(),
        'pending_count': QuestionBank.objects.filter(moderation_status='PENDING').count(),
        'approved_count': QuestionBank.objects.filter(moderation_status='APPROVED').count(),
    })
    return render(request, 'core/admin_question_bank.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_question_moderate(request, q_id):
    """
    Approve or Reject a question submitted by a local recruiter.
    """
    from jobs.models import QuestionBank
    from django.shortcuts import get_object_or_404
    if request.method == 'POST':
        question = get_object_or_404(QuestionBank, id=q_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            question.moderation_status = 'APPROVED'
            question.is_active = True
        elif action == 'reject':
            question.moderation_status = 'REJECTED'
            question.is_active = False
            
        question.save()
        messages.success(request, f"Question ID {q_id} marked as {question.moderation_status}.")
        
    return redirect('admin_question_bank')


@login_required
@user_passes_test(is_admin_check)
def admin_proctoring_config(request):
    """
    Advanced Proctoring Control Panel: Sensitivity & Strictness.
    """
    from jobs.models import PlatformSetting
    
    if request.method == 'POST':
        min_conf = request.POST.get('min_confidence', '0.5')
        eye_low = request.POST.get('eye_low', '0.35')
        eye_high = request.POST.get('eye_high', '0.65')
        flags_max = request.POST.get('flags_max', '5')
        
        PlatformSetting.set('PROCTOR_MIN_CONFIDENCE', min_conf, 'Minimum Face Detection Confidence', 'proctoring')
        PlatformSetting.set('PROCTOR_EYE_RATIO_LOW', eye_low, 'Eye Gaze Low Threshold', 'proctoring')
        PlatformSetting.set('PROCTOR_EYE_RATIO_HIGH', eye_high, 'Eye Gaze High Threshold', 'proctoring')
        PlatformSetting.set('PROCTOR_FLAGS_MAX', flags_max, 'Max flags before auto-flag', 'proctoring')
        
        messages.success(request, "Proctoring thresholds updated successfully (Neural Sync Complete).")
        return redirect('admin_proctoring_config')

    ctx = _admin_context('Proctoring Control', 'proctoring_config')
    ctx.update({
        'min_conf': PlatformSetting.get('PROCTOR_MIN_CONFIDENCE', '0.5'),
        'eye_low': PlatformSetting.get('PROCTOR_EYE_RATIO_LOW', '0.35'),
        'eye_high': PlatformSetting.get('PROCTOR_EYE_RATIO_HIGH', '0.65'),
        'flags_max': PlatformSetting.get('PROCTOR_FLAGS_MAX', '5'),
    })
    return render(request, 'core/admin_proctoring_config.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_proctoring_review(request):
    """
    Master list of flagged 'Cheating' or suspicious sessions.
    """
    from jobs.models import Interview
    status_filter = request.GET.get('status', 'PENDING')
    
    interviews = Interview.objects.filter(flag_count__gt=0).order_by('-flag_count')
    if status_filter != 'ALL':
        interviews = interviews.filter(proctoring_status=status_filter)

    ctx = _admin_context('Evidence Review', 'proctoring_review')
    ctx.update({
        'interviews': interviews,
        'status_filter': status_filter,
    })
    return render(request, 'core/admin_proctoring_review.html', ctx)


@login_required
@user_passes_test(is_admin_check)
def admin_proctoring_detail(request, interview_id):
    """
    Detailed evidence view for a specific flagged interview.
    Shows timestamped violation frames.
    """
    from jobs.models import Interview, SentimentLog
    from django.shortcuts import get_object_or_404
    
    interview = get_object_or_404(Interview, id=interview_id)
    # Only show logs with proctoring flags and non-empty frame
    logs = SentimentLog.objects.filter(interview=interview).exclude(proctoring_flags={}).order_by('timestamp')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'verify':
            interview.proctoring_status = 'VERIFIED'
            interview.is_flagged = True
        elif action == 'dismiss':
            interview.proctoring_status = 'FALSE_POSITIVE'
            interview.is_flagged = False
            
        interview.proctoring_notes = notes
        interview.save()
        messages.success(request, f"Review completed for {interview.application.candidate.full_name}.")
        return redirect('admin_proctoring_review')

    ctx = _admin_context('Violation Evidence', 'proctoring_review')
    ctx.update({
        'interview': interview,
        'logs': logs,
    })
    return render(request, 'core/admin_proctoring_detail.html', ctx)
# ─── Question Bank Governance (Module 4) ───────────────────────────────────

@user_passes_test(is_admin_check)
def admin_question_bank(request):
    from jobs.models import QuestionBank
    
    q_round = request.GET.get('round', 'all')
    q_status = request.GET.get('status', 'all')
    
    questions = QuestionBank.objects.all()
    if q_round != 'all':
        questions = questions.filter(round=q_round)
    if q_status != 'all':
        questions = questions.filter(moderation_status=q_status)
        
    total_questions = QuestionBank.objects.count()
    pending_count = QuestionBank.objects.filter(moderation_status='PENDING').count()
    approved_count = QuestionBank.objects.filter(moderation_status='APPROVED').count()
    
    # Simple bias detection: high failure rate flag (>70% fails after 10 attempts)
    high_failure_questions = []
    for q in QuestionBank.objects.filter(attempt_count__gte=5):
        fail_rate = (q.failure_count / q.attempt_count) * 100
        if fail_rate > 70:
            high_failure_questions.append({
                'id': q.id,
                'fail_rate': round(fail_rate, 1),
                'text': q.question_text
            })

    ctx = _admin_context('Question Governance', 'question_bank')
    ctx.update({
        'questions': questions.order_by('-created_at'),
        'total_questions': total_questions,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'high_failure_questions': high_failure_questions,
        'round_choices': QuestionBank.ROUND_CHOICES,
        'status_choices': QuestionBank.MODERATION_CHOICES,
        'q_round': q_round,
        'q_status': q_status,
    })
    return render(request, 'core/admin_question_bank.html', ctx)

@user_passes_test(is_admin_check)
def admin_question_moderate(request, q_id):
    from jobs.models import QuestionBank
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    
    if request.method == 'POST':
        action = request.POST.get('action')
        question = get_object_or_404(QuestionBank, id=q_id)
        if action == 'approve':
            question.moderation_status = 'APPROVED'
        elif action == 'reject':
            question.moderation_status = 'REJECTED'
        question.save()
        messages.success(request, f"Question #{q_id} status updated to {question.moderation_status}")
    return redirect('admin_question_bank')

@csrf_exempt
@user_passes_test(is_admin_check)
def admin_question_gen_api(request):
    """
    AI Assistant Endpoint: Generates questions using AIEngine (Gemini/Groq)
    """
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        from .ai_engine import AIEngine
        
        try:
            data = json.loads(request.body)
            round_type = data.get('round')
            category = data.get('category')
            difficulty = data.get('difficulty')
            count = int(data.get('count', 5))
            
            engine = AIEngine()
            questions = engine.generate_questions(round_type, category, difficulty, count)
            
            return JsonResponse({'status': 'success', 'questions': questions})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
@user_passes_test(is_admin_check)
def admin_question_bulk_save(request):
    """
    Saves AI-generated (and potentially edited) questions to the database.
    """
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        from jobs.models import QuestionBank
        
        try:
            data = json.loads(request.body)
            questions_payload = data.get('questions', [])
            round_type = data.get('round')
            category = data.get('category')
            difficulty = data.get('difficulty')
            
            saved_count = 0
            for q_data in questions_payload:
                QuestionBank.objects.create(
                    round=round_type,
                    category=category,
                    difficulty=difficulty,
                    question_text=q_data.get('question_text'),
                    options=q_data.get('options'),
                    correct_answer=q_data.get('correct_answer'),
                    explanation=q_data.get('explanation'),
                    moderation_status='PENDING', # Needs final verification by admin
                    submitted_by=request.user
                )
                saved_count += 1
                
            return JsonResponse({'status': 'success', 'message': f"Injected {saved_count} questions into the bank pipeline."})
        except Exception as e:
             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ─── Data Portability & Audit (Module 6) ───────────────────────────────────

@user_passes_test(is_admin_check)
def admin_export_data(request):
    """
    Universal CSV Export for major datatables.
    """
    import csv
    from django.http import HttpResponse
    from jobs.models import Candidate, Interview, JobApplication
    
    table = request.GET.get('table', 'candidates')
    filename = f"smartrecruit_{table}_export.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    if table == 'candidates':
        writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Created At'])
        for c in Candidate.objects.all():
            writer.writerow([c.id, c.full_name, c.email, c.phone, c.created_at])
    elif table == 'applications':
        writer.writerow(['ID', 'Candidate', 'Job', 'Status', 'Applied At'])
        for a in JobApplication.objects.all():
            writer.writerow([a.id, a.candidate.full_name, a.job.title, a.status, a.created_at])
    elif table == 'interviews':
        writer.writerow(['ID', 'Candidate', 'Score', 'Status', 'Date'])
        for i in Interview.objects.all():
            writer.writerow([i.id, i.application.candidate.full_name, i.total_score, i.proctoring_status, i.interview_date])
            
    return response

@user_passes_test(is_admin_check)
def admin_activity_feed_api(request):
    """
    Returns recent ActivityLog entries as JSON for the dashboard feed.
    """
    from jobs.models import ActivityLog
    logs = ActivityLog.objects.all().order_by('-timestamp')[:15]
    data = []
    for l in logs:
        data.append({
            'user': l.user.username if l.user else 'System',
            'action': l.action,
            'details': l.details[:50],
            'time': l.timestamp.strftime("%H:%M"),
            'date': l.timestamp.strftime("%d %b")
        })
    return JsonResponse({'status': 'success', 'logs': data})

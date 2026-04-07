from django.shortcuts import redirect
from django.contrib import messages
from .models import Assessment
from .email_utils import send_status_email, send_html_email

class AssessmentService:
    @staticmethod
    def handle_proctoring_violation(request, application, reason):
        """
        Handles cheating detection: updates status, sends email, and alerts user.
        """
        application.status = 'REJECTED'
        application.save()
        
        # Email Notification
        send_html_email(
            subject="Application Status Update - SmartRecruit",
            template_name='assessment_result.html', # Fallback needed if template doesn't support this context fully, but using existing pattern
            context={
                'candidate_name': request.user.get_full_name(),
                'job_title': application.job.title,
                'test_type': 'Assessment',
                'passed': False,
                'score': 0,
                'passing_score': 0,
                'next_steps': f"Terminated due to: {reason}"
            },
            recipient_email=request.user.email
        )
        return f"Assessment Terminated: {reason}"

    @staticmethod
    def calculate_aptitude_score(session_answers, post_data):
        """
        Calculates score for Aptitude (MCQ).
        """
        correct_count = 0
        total_questions = len(session_answers)
        if total_questions == 0:
            return 0.0
            
        points_per_question = 100.0 / total_questions
        
        for q_id, correct_ans in session_answers.items():
            user_ans = post_data.get(q_id)
            if user_ans == correct_ans:
                correct_count += 1
        
        score = correct_count * points_per_question
        return round(float(score), 2)

    @staticmethod
    def calculate_practical_score(session_answers, post_data, bot):
        """
        Calculates score for Practical (MCQ + Code Execution via Piston).
        """
        import logging
        logger = logging.getLogger(__name__)

        # A. MCQs (50%)
        mcq_score = 0.0
        total_mcqs = len(session_answers)
        points_per_mcq = 50.0 / total_mcqs if total_mcqs > 0 else 0
        
        for q_id, correct_ans in session_answers.items():
            user_ans = post_data.get(q_id)
            if user_ans == correct_ans:
                mcq_score += float(points_per_mcq)

        # B. Code Execution (50%) - Powered by Piston API
        user_code = post_data.get('code_submission', '')
        language = post_data.get('language', 'python')
        challenge_id = post_data.get('question_id')
        
        code_score = 0
        if not user_code or len(user_code) < 10:
            return mcq_score

        # ⚡ EXECUTION UNIT: Piston API (100% Free)
        from core.utils.code_runner import execute_code as run_piston
        
        try:
            from core.ai_engine import AIEngine
            
            # 1. Run in Sandbox
            exec_result = run_piston(source_code=user_code, language=language)
            status = exec_result.get('status')
            output = exec_result.get('stdout', '')
            stderr = exec_result.get('stderr', '')
            
            if status in ['COMPILE_ERROR', 'RUNTIME_ERROR']:
                # Syntax error or crash: Minimal points for effort
                code_score = 15
            else:
                # 2. Functional code! Use AIEngine for semantic grading
                ai = AIEngine()
                judge_prompt = f"""
                Analyze this polyglot code submission for a Technical Assessment.
                
                Context: Challenge "{challenge_id}"
                Target Language: {language}
                Submission Source:
                ```{language}
                {user_code}
                ```
                
                Runtime Execution Status: {status}
                Captured Output: {output}
                
                GRADING CRITERIA:
                1. Algorithmic Correctness: Does the logic solve the underlying problem?
                2. Time/Space Complexity: Is the approach efficient?
                3. Idiomatic Usage: Does it follow {language} best practices?
                4. Robustness: Are edge cases handled?
                
                Score the solution from 0 to 50. 
                Return ONLY the numeric score (e.g., 42).
                """
                ai_judge = ai.generate(prompt=judge_prompt)
                try:
                    score_val = "".join(filter(str.isdigit, ai_judge))
                    code_score = int(score_val) if score_val else 30
                except:
                    code_score = 35 # High-confidence fallback
            
            # Documentation Bonus
            if any(comment in user_code for comment in ['#', '//', '/*', '"""', "'''"]):
                code_score += 5
                
        except Exception as e:
            logger.error(f"[PolyglotGrading] Bridge Failed: {e}")
            code_score = 25 # Static fallback
            
        return mcq_score + min(code_score, 50)

    @staticmethod
    def finalize_assessment(request, application, test_type, score, details=None):
        """
        Saves result, updates application status, and sends notifications.
        """
        from django.utils import timezone
        from datetime import datetime
        import json

        details = details or {}
        time_taken = None
        start_time_str = details.get('start_time')
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
                time_taken = timezone.now() - start_time
            except:
                pass

        # Blitz Mode Bonus points
        if details and details.get('blitz_mode') and time_taken:
            test_duration = details.get('test_duration', 1200) # Default 20 mins
            if isinstance(test_duration, (int, float)):
                time_saved = max(0.0, float(test_duration) - time_taken.total_seconds())
                time_saved_pct = (time_saved / test_duration) * 100
                
                # Dynamic bonus: 0.2 points per 1% time saved, max 20
                speed_bonus = min(20, int(time_saved_pct * 0.2))
                score = min(float(score) + speed_bonus, 100.0)
                if isinstance(details, dict):
                    details['speed_bonus'] = speed_bonus
                    details['time_saved_pct'] = round(float(time_saved_pct), 1)
        is_passed = False
        passing_score = 0.0
        
        # Determine Passing Criteria
        if test_type == 'aptitude':
            passing_score = application.job.passing_score_r1
            is_passed = score >= passing_score
        elif test_type == 'practical':
            passing_score = application.job.passing_score_r2
            is_passed = score >= passing_score

        # Create Record
        assessment = Assessment.objects.create(
            application=application,
            test_type=test_type.upper(),
            score=score,
            max_score=100.0,
            passed=is_passed,
            time_taken=time_taken,
            details=details
        )
        
        # 🏅 Gamification: Milestone Check
        try:
            from core.utils.gamification import check_assessment_milestones
            check_assessment_milestones(application.candidate, assessment, request=request)
        except Exception as ge:
            import logging
            logging.getLogger(__name__).error(f"[Gamification] Milestone Check Failed: {ge}")
        
        # Update State & Notify
        if is_passed:
            if test_type == 'aptitude':
                application.status = 'ROUND_1_PASSED'
                msg = f"Congrats! You passed Round 1 with {score}%. Qualified for Round 2."
                email_sub = "Round 1 Cleared - SmartRecruit"
                email_body = f"Congratulations! You passed the Aptitude Test with {score}%. You are now eligible for Round 2 (Practical)."
            
            elif test_type == 'practical':
                application.status = 'ROUND_2_PASSED'
                msg = f"Excellent! You passed Round 2 with {score}%. Qualified for AI Interview."
                email_sub = "Round 2 Cleared - SmartRecruit"
                email_body = f"Congratulations! You passed the Practical Test with {score}%. You are now qualified for the AI Interview (Round 3)."
            
            messages.success(request, msg)
            send_status_email(request.user, email_sub, email_body)

            # 📱 Twilio WhatsApp Alerts (Candidate & Admin)
            try:
                from core.utils.twilio_api import send_interview_pass_alert, send_round_pass_alert_to_admin
                candidate_phone = getattr(application.candidate, 'phone', '')
                round_num = 1 if test_type == 'aptitude' else 2
                
                # Notify Candidate
                if candidate_phone:
                    send_interview_pass_alert(
                        candidate_name=request.user.get_full_name(),
                        candidate_phone=candidate_phone,
                        role=application.job.title,
                        round_num=round_num
                    )
                
                # Notify Admin (Raj)
                send_round_pass_alert_to_admin(
                    candidate_name=request.user.get_full_name(),
                    role=application.job.title,
                    round_num=round_num
                )
            except Exception as _tw_err:
                import logging
                logging.getLogger(__name__).warning(f"[Twilio:ROUND_PASS] Alert failed: {_tw_err}")

            # 🔱 ULTIMATE FLOW B: n8n Auto-Scheduling & WhatsApp Notification
            from core.utils.webhooks import trigger_interview_webhook
            trigger_interview_webhook(
                candidate_name=request.user.get_full_name(),
                candidate_email=request.user.email,
                applied_role=application.job.title,
                interview_type=test_type.upper(),
                interview_score=score,
                application_id=application.id,
                phone_number=getattr(application.candidate, 'phone', ''),
                github_url=getattr(application.candidate, 'github_url', ''),
                feedback=msg
            )
            
        else:
            if test_type == 'aptitude':
                application.status = 'ROUND_1_FAILED'
                error_msg = f"Sorry, you scored {score}%. The cutoff was {passing_score}%."
            elif test_type == 'practical':
                application.status = 'ROUND_2_FAILED'
                error_msg = f"Sorry, you scored {score}%. The cutoff was {passing_score}%."
            
            messages.error(request, error_msg)
            # Send specific rejection/result email with score
            send_status_email(
                 request.user, 
                 "Assessment Result - SmartRecruit", 
                 f"You scored {score}%. Unfortunately, the cutoff was {passing_score}%."
            )

        application.save()

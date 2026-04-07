from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import Question
from .forms import QuestionForm
from .utils import generate_ai_mcqs

@login_required
def question_list(request):
    if not (request.user.is_recruiter or request.user.is_superuser):
        messages.error(request, "Access Denied. Recruiters only.")
        return redirect('dashboard')
        
    questions = Question.objects.filter(recruiter=request.user).order_by('-created_at')
    return render(request, 'jobs/question_list.html', {'questions': questions})

@login_required
def add_question(request):
    if not (request.user.is_recruiter or request.user.is_superuser):
        messages.error(request, "Access Denied. Recruiters only.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.recruiter = request.user
            question.save()
            messages.success(request, "Question added successfully!")
            return redirect('question_list')
    else:
        form = QuestionForm()
    
    return render(request, 'jobs/add_question.html', {'form': form})

@login_required
def edit_question(request, question_id):
    if not (request.user.is_recruiter or request.user.is_superuser):
        messages.error(request, "Access Denied. Recruiters only.")
        return redirect('dashboard')
        
    question = get_object_or_404(Question, id=question_id, recruiter=request.user)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully!")
            return redirect('question_list')
    else:
        form = QuestionForm(instance=question)
        
    return render(request, 'jobs/edit_question.html', {'form': form, 'question': question})

@login_required
def delete_question(request, question_id):
    if not (request.user.is_recruiter or request.user.is_superuser):
        return redirect('dashboard')
        
    question = get_object_or_404(Question, id=question_id, recruiter=request.user)
    question.delete()
    messages.success(request, "Question deleted.")
    return redirect('question_list')

@login_required
def preview_assessment(request, job_id, test_type):
    from .models import JobPosting, Question
    from .utils import generate_ai_mcqs
    
    if not (request.user.is_recruiter or request.user.is_superuser):
        messages.error(request, "Access Denied.")
        return redirect('dashboard')
        
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    
    # 🔗 Industry Standard Domain Mapping
    if test_type == 'aptitude':
        domains = ['Logical Reasoning', 'Quantitative Aptitude', 'Verbal Ability']
    else: # practical
        domains = []
        if job.technology_stack and job.technology_stack != 'GENERAL':
            domains.append(job.technology_stack.title())
        else:
            domains.append("General Software Engineering")
        
        # Add sub-domains for variety
        domains.append("System Design & Architecture")
        domains.append("Modern Best Practices")

    difficulties = ['easy', 'medium', 'hard']
    grouped_questions = {}
    
    force_regen = request.GET.get('regen') == '1'
    target_domain = request.GET.get('domain', '').upper()

    for domain in domains:
        domain_key = domain.upper()[:20]
        grouped_questions[domain] = {}
        for diff in difficulties:
            db_qs = Question.objects.filter(category__iexact=domain_key, difficulty=diff)
            
            # Auto-generate if empty or forced
            should_gen = not db_qs.exists()
            if force_regen and (not target_domain or target_domain == domain_key):
                should_gen = True

            if should_gen:
                gen_amount = 50 if diff == 'hard' else 25 # Phase 2 Upgrade: More questions
                ai_qs = generate_ai_mcqs(amount=gen_amount, domain=domain, difficulty=diff)
                for q in ai_qs:
                    Question.objects.get_or_create(
                        recruiter=request.user,
                        text=q.get('question'),
                        defaults={
                            'options': q.get('options'),
                            'correct_answer': q.get('correct'),
                            'category': domain_key,
                            'difficulty': diff
                        }
                    )
                db_qs = Question.objects.filter(category__iexact=domain_key, difficulty=diff)

            preview_qs = list(db_qs.order_by('?')[:25])
            grouped_questions[domain][diff] = [{'question': q.text, 'options': q.options, 'correct': q.correct_answer} for q in preview_qs]
        
    context = {
        'job': job,
        'test_type': test_type,
        'grouped_questions': grouped_questions,
        'domains': domains
    }
    return render(request, 'jobs/preview_assessment.html', context)

@login_required
def generate_questions_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
        
    if not (request.user.is_recruiter or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        domain = data.get('domain', 'general')
        difficulty = data.get('difficulty', 'medium')
        amount = int(data.get('amount', 5))
        
        # Call Gemini API wrapper
        ai_questions = generate_ai_mcqs(amount=amount, domain=domain, difficulty=difficulty)
        
        if not ai_questions:
            return JsonResponse({'success': False, 'error': 'Failed to generate questions. Check API key or try again.'})
            
        # Parse and save directly
        saved_count = 0
        for q in ai_questions:
            Question.objects.create(
                recruiter=request.user,
                text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('correct', ''),
                category=domain[:20].upper(), # Mapping dynamically
                difficulty=difficulty
            )
            saved_count += 1
            
        return JsonResponse({'success': True, 'message': f'Successfully generated and saved {saved_count} questions!'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

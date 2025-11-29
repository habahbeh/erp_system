# apps/hr/views/performance_views.py
"""
واجهات التقييم والأداء
Performance & Evaluation Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal

from apps.hr.models import (
    PerformancePeriod,
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationDetail,
    PerformanceGoal,
    PerformanceNote,
    Employee,
    Department,
)
from apps.hr.forms import (
    PerformancePeriodForm,
    PerformanceCriteriaForm,
    PerformanceEvaluationForm,
    PerformanceGoalForm,
    PerformanceNoteForm,
    SelfEvaluationForm,
    ManagerEvaluationForm,
    GoalProgressUpdateForm,
    EvaluationApprovalForm,
    BulkEvaluationForm,
)


# ==================== Performance Period Views ====================

@login_required
def period_list(request):
    """قائمة فترات التقييم"""
    company = request.current_company
    periods = PerformancePeriod.objects.filter(company=company).order_by('-year', '-start_date')

    # Filters
    status = request.GET.get('status')
    year = request.GET.get('year')

    if status:
        periods = periods.filter(status=status)
    if year:
        periods = periods.filter(year=year)

    # Pagination
    paginator = Paginator(periods, 20)
    page = request.GET.get('page')
    periods = paginator.get_page(page)

    # Get available years for filter
    years = PerformancePeriod.objects.filter(company=company).values_list('year', flat=True).distinct()

    context = {
        'periods': periods,
        'years': sorted(set(years), reverse=True),
        'selected_status': status,
        'selected_year': year,
        'title': _('فترات التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فترات التقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/period_list.html', context)


@login_required
def period_create(request):
    """إنشاء فترة تقييم جديدة"""
    company = request.current_company

    if request.method == 'POST':
        form = PerformancePeriodForm(request.POST)
        if form.is_valid():
            period = form.save(commit=False)
            period.company = company
            period.created_by = request.user
            period.save()
            messages.success(request, _('تم إنشاء فترة التقييم بنجاح'))
            return redirect('hr:period_list')
    else:
        form = PerformancePeriodForm()

    context = {
        'form': form,
        'title': _('إنشاء فترة تقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فترات التقييم'), 'url': '/hr/performance/periods/'},
            {'title': _('إنشاء فترة تقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/period_form.html', context)


@login_required
def period_edit(request, pk):
    """تعديل فترة تقييم"""
    company = request.current_company
    period = get_object_or_404(PerformancePeriod, pk=pk, company=company)

    if request.method == 'POST':
        form = PerformancePeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث فترة التقييم بنجاح'))
            return redirect('hr:period_list')
    else:
        form = PerformancePeriodForm(instance=period)

    context = {
        'form': form,
        'period': period,
        'title': _('تعديل فترة التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فترات التقييم'), 'url': '/hr/performance/periods/'},
            {'title': _('تعديل فترة التقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/period_form.html', context)


@login_required
def period_delete(request, pk):
    """حذف فترة تقييم"""
    company = request.current_company
    period = get_object_or_404(PerformancePeriod, pk=pk, company=company)

    if request.method == 'POST':
        # Check if there are evaluations
        if PerformanceEvaluation.objects.filter(period=period).exists():
            messages.error(request, _('لا يمكن حذف الفترة لوجود تقييمات مرتبطة بها'))
        else:
            period.delete()
            messages.success(request, _('تم حذف فترة التقييم بنجاح'))
        return redirect('hr:period_list')

    context = {
        'period': period,
        'title': _('حذف فترة التقييم'),
    }
    return render(request, 'hr/performance/period_confirm_delete.html', context)


# ==================== Performance Criteria Views ====================

@login_required
def criteria_list(request):
    """قائمة معايير التقييم"""
    company = request.current_company
    criteria = PerformanceCriteria.objects.filter(company=company).order_by('display_order', 'name')

    # Filters
    criteria_type = request.GET.get('type')
    if criteria_type:
        criteria = criteria.filter(criteria_type=criteria_type)

    context = {
        'criteria_list': criteria,
        'selected_type': criteria_type,
        'title': _('معايير التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('معايير التقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/criteria_list.html', context)


@login_required
def criteria_create(request):
    """إنشاء معيار تقييم جديد"""
    company = request.current_company

    if request.method == 'POST':
        form = PerformanceCriteriaForm(request.POST, company=company)
        if form.is_valid():
            criteria = form.save(commit=False)
            criteria.company = company
            criteria.created_by = request.user
            criteria.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, _('تم إنشاء معيار التقييم بنجاح'))
            return redirect('hr:criteria_list')
    else:
        form = PerformanceCriteriaForm(company=company)

    context = {
        'form': form,
        'title': _('إنشاء معيار تقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('معايير التقييم'), 'url': '/hr/performance/criteria/'},
            {'title': _('إنشاء معيار'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/criteria_form.html', context)


@login_required
def criteria_edit(request, pk):
    """تعديل معيار تقييم"""
    company = request.current_company
    criteria = get_object_or_404(PerformanceCriteria, pk=pk, company=company)

    if request.method == 'POST':
        form = PerformanceCriteriaForm(request.POST, instance=criteria, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث معيار التقييم بنجاح'))
            return redirect('hr:criteria_list')
    else:
        form = PerformanceCriteriaForm(instance=criteria, company=company)

    context = {
        'form': form,
        'criteria': criteria,
        'title': _('تعديل معيار التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('معايير التقييم'), 'url': '/hr/performance/criteria/'},
            {'title': _('تعديل معيار'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/criteria_form.html', context)


@login_required
def criteria_delete(request, pk):
    """حذف معيار تقييم"""
    company = request.current_company
    criteria = get_object_or_404(PerformanceCriteria, pk=pk, company=company)

    if request.method == 'POST':
        # Check if there are evaluation details using this criteria
        if PerformanceEvaluationDetail.objects.filter(criteria=criteria).exists():
            messages.error(request, _('لا يمكن حذف المعيار لوجود تقييمات تستخدمه'))
        else:
            criteria.delete()
            messages.success(request, _('تم حذف معيار التقييم بنجاح'))
        return redirect('hr:criteria_list')

    context = {
        'criteria': criteria,
        'title': _('حذف معيار التقييم'),
    }
    return render(request, 'hr/performance/criteria_confirm_delete.html', context)


# ==================== Performance Evaluation Views ====================

@login_required
def evaluation_list(request):
    """قائمة التقييمات"""
    company = request.current_company
    evaluations = PerformanceEvaluation.objects.filter(
        company=company
    ).select_related('employee', 'period', 'evaluator').order_by('-created_at')

    # Filters
    period_id = request.GET.get('period')
    status = request.GET.get('status')
    department_id = request.GET.get('department')

    if period_id:
        evaluations = evaluations.filter(period_id=period_id)
    if status:
        evaluations = evaluations.filter(status=status)
    if department_id:
        evaluations = evaluations.filter(employee__department_id=department_id)

    # Pagination
    paginator = Paginator(evaluations, 20)
    page = request.GET.get('page')
    evaluations = paginator.get_page(page)

    # Get filter options
    periods = PerformancePeriod.objects.filter(company=company, is_active=True)
    departments = Department.objects.filter(company=company, is_active=True)

    context = {
        'evaluations': evaluations,
        'periods': periods,
        'departments': departments,
        'selected_period': period_id,
        'selected_status': status,
        'selected_department': department_id,
        'title': _('تقييمات الأداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/evaluation_list.html', context)


@login_required
def evaluation_create(request):
    """إنشاء تقييم أداء جديد"""
    company = request.current_company

    if request.method == 'POST':
        form = PerformanceEvaluationForm(request.POST, company=company)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.company = company
            evaluation.evaluator = request.user
            evaluation.created_by = request.user
            evaluation.save()

            # Create evaluation details for each applicable criteria
            employee = evaluation.employee
            criteria_list = PerformanceCriteria.objects.filter(
                company=company, is_active=True
            ).filter(
                Q(applies_to_all=True) | Q(departments=employee.department)
            ).distinct()

            for criteria in criteria_list:
                PerformanceEvaluationDetail.objects.create(
                    evaluation=evaluation,
                    criteria=criteria
                )

            messages.success(request, _('تم إنشاء التقييم بنجاح'))
            return redirect('hr:evaluation_detail', pk=evaluation.pk)
    else:
        form = PerformanceEvaluationForm(company=company)

    context = {
        'form': form,
        'title': _('إنشاء تقييم أداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('إنشاء تقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/evaluation_form.html', context)


@login_required
def evaluation_detail(request, pk):
    """تفاصيل تقييم الأداء"""
    company = request.current_company
    evaluation = get_object_or_404(
        PerformanceEvaluation.objects.select_related('employee', 'period', 'evaluator'),
        pk=pk, company=company
    )

    details = PerformanceEvaluationDetail.objects.filter(
        evaluation=evaluation
    ).select_related('criteria').order_by('criteria__display_order')

    context = {
        'evaluation': evaluation,
        'details': details,
        'title': _('تفاصيل التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('تفاصيل التقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/evaluation_detail.html', context)


@login_required
def self_evaluation(request, pk):
    """التقييم الذاتي"""
    company = request.current_company
    evaluation = get_object_or_404(
        PerformanceEvaluation,
        pk=pk, company=company, status__in=['draft', 'self_evaluation']
    )

    details = PerformanceEvaluationDetail.objects.filter(
        evaluation=evaluation
    ).select_related('criteria').order_by('criteria__display_order')

    criteria_list = [d.criteria for d in details]

    if request.method == 'POST':
        form = SelfEvaluationForm(request.POST, criteria_list=criteria_list)
        if form.is_valid():
            for detail in details:
                score_key = f'score_{detail.criteria.id}'
                comment_key = f'comment_{detail.criteria.id}'

                if score_key in form.cleaned_data:
                    detail.self_score = form.cleaned_data[score_key]
                if comment_key in form.cleaned_data:
                    detail.employee_comments = form.cleaned_data[comment_key]
                detail.save()

            # Update evaluation status
            evaluation.status = 'manager_evaluation'
            evaluation.self_evaluation_date = timezone.now().date()
            evaluation.save()

            messages.success(request, _('تم حفظ التقييم الذاتي بنجاح'))
            return redirect('hr:evaluation_detail', pk=evaluation.pk)
    else:
        initial = {}
        for detail in details:
            if detail.self_score:
                initial[f'score_{detail.criteria.id}'] = detail.self_score
            if detail.employee_comments:
                initial[f'comment_{detail.criteria.id}'] = detail.employee_comments
        form = SelfEvaluationForm(initial=initial, criteria_list=criteria_list)

    context = {
        'form': form,
        'evaluation': evaluation,
        'details': details,
        'title': _('التقييم الذاتي'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('التقييم الذاتي'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/self_evaluation.html', context)


@login_required
def manager_evaluation(request, pk):
    """تقييم المدير"""
    company = request.current_company
    evaluation = get_object_or_404(
        PerformanceEvaluation,
        pk=pk, company=company, status='manager_evaluation'
    )

    details = PerformanceEvaluationDetail.objects.filter(
        evaluation=evaluation
    ).select_related('criteria').order_by('criteria__display_order')

    criteria_list = [d.criteria for d in details]

    if request.method == 'POST':
        form = ManagerEvaluationForm(request.POST, criteria_list=criteria_list)
        if form.is_valid():
            for detail in details:
                score_key = f'score_{detail.criteria.id}'
                comment_key = f'comment_{detail.criteria.id}'

                if score_key in form.cleaned_data:
                    detail.manager_score = form.cleaned_data[score_key]
                if comment_key in form.cleaned_data:
                    detail.manager_comments = form.cleaned_data[comment_key]

                # Calculate final score (70% manager, 30% self)
                if detail.manager_score:
                    self_score = detail.self_score or detail.manager_score
                    detail.final_score = (detail.manager_score * Decimal('0.7')) + (self_score * Decimal('0.3'))
                detail.save()

            # Calculate overall final score
            evaluation.calculate_final_score()
            evaluation.status = 'pending_approval'
            evaluation.manager_evaluation_date = timezone.now().date()
            evaluation.save()

            messages.success(request, _('تم حفظ تقييم المدير بنجاح'))
            return redirect('hr:evaluation_detail', pk=evaluation.pk)
    else:
        initial = {}
        for detail in details:
            if detail.manager_score:
                initial[f'score_{detail.criteria.id}'] = detail.manager_score
            if detail.manager_comments:
                initial[f'comment_{detail.criteria.id}'] = detail.manager_comments
        form = ManagerEvaluationForm(initial=initial, criteria_list=criteria_list)

    context = {
        'form': form,
        'evaluation': evaluation,
        'details': details,
        'title': _('تقييم المدير'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('تقييم المدير'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/manager_evaluation.html', context)


@login_required
def evaluation_approve(request, pk):
    """اعتماد أو رفض التقييم"""
    company = request.current_company
    evaluation = get_object_or_404(
        PerformanceEvaluation,
        pk=pk, company=company, status='pending_approval'
    )

    if request.method == 'POST':
        form = EvaluationApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            comments = form.cleaned_data['comments']

            if action == 'approve':
                evaluation.status = 'approved'
                evaluation.approval_date = timezone.now().date()
                evaluation.approved_by = request.user
                messages.success(request, _('تم اعتماد التقييم بنجاح'))
            else:
                evaluation.status = 'rejected'
                messages.warning(request, _('تم رفض التقييم'))

            if comments:
                evaluation.overall_comments = (evaluation.overall_comments or '') + f'\n\n{_("ملاحظات المعتمد")}: {comments}'
            evaluation.save()

            return redirect('hr:evaluation_list')
    else:
        form = EvaluationApprovalForm()

    context = {
        'form': form,
        'evaluation': evaluation,
        'title': _('اعتماد التقييم'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('اعتماد التقييم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/evaluation_approve.html', context)


@login_required
def bulk_evaluation_create(request):
    """إنشاء تقييمات جماعية"""
    company = request.current_company

    if request.method == 'POST':
        form = BulkEvaluationForm(request.POST, company=company)
        if form.is_valid():
            period = form.cleaned_data['period']
            department = form.cleaned_data.get('department')
            employees = form.cleaned_data.get('employees')

            if not employees:
                if department:
                    employees = Employee.objects.filter(
                        company=company, department=department, is_active=True
                    )
                else:
                    employees = Employee.objects.filter(company=company, is_active=True)

            created_count = 0
            skipped_count = 0

            for employee in employees:
                # Check if evaluation already exists
                if PerformanceEvaluation.objects.filter(employee=employee, period=period).exists():
                    skipped_count += 1
                    continue

                evaluation = PerformanceEvaluation.objects.create(
                    company=company,
                    employee=employee,
                    period=period,
                    evaluator=request.user,
                    status='draft',
                    created_by=request.user
                )

                # Create evaluation details
                criteria_list = PerformanceCriteria.objects.filter(
                    company=company, is_active=True
                ).filter(
                    Q(applies_to_all=True) | Q(departments=employee.department)
                ).distinct()

                for criteria in criteria_list:
                    PerformanceEvaluationDetail.objects.create(
                        evaluation=evaluation,
                        criteria=criteria
                    )

                created_count += 1

            messages.success(
                request,
                _('تم إنشاء %(count)d تقييم جديد. تم تخطي %(skipped)d موظف (تقييمات موجودة)') % {
                    'count': created_count,
                    'skipped': skipped_count
                }
            )
            return redirect('hr:evaluation_list')
    else:
        form = BulkEvaluationForm(company=company)

    context = {
        'form': form,
        'title': _('إنشاء تقييمات جماعية'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تقييمات الأداء'), 'url': '/hr/performance/evaluations/'},
            {'title': _('إنشاء تقييمات جماعية'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/bulk_evaluation_form.html', context)


# ==================== Performance Goals Views ====================

@login_required
def goal_list(request):
    """قائمة الأهداف"""
    company = request.current_company
    goals = PerformanceGoal.objects.filter(
        company=company
    ).select_related('employee', 'period').order_by('-created_at')

    # Filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    employee_id = request.GET.get('employee')

    if status:
        goals = goals.filter(status=status)
    if priority:
        goals = goals.filter(priority=priority)
    if employee_id:
        goals = goals.filter(employee_id=employee_id)

    # Pagination
    paginator = Paginator(goals, 20)
    page = request.GET.get('page')
    goals = paginator.get_page(page)

    employees = Employee.objects.filter(company=company, is_active=True)

    context = {
        'goals': goals,
        'employees': employees,
        'selected_status': status,
        'selected_priority': priority,
        'selected_employee': employee_id,
        'title': _('أهداف الأداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أهداف الأداء'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/goal_list.html', context)


@login_required
def goal_create(request):
    """إنشاء هدف جديد"""
    company = request.current_company

    if request.method == 'POST':
        form = PerformanceGoalForm(request.POST, company=company)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.company = company
            goal.created_by = request.user
            goal.save()
            messages.success(request, _('تم إنشاء الهدف بنجاح'))
            return redirect('hr:goal_list')
    else:
        form = PerformanceGoalForm(company=company)

    context = {
        'form': form,
        'title': _('إنشاء هدف أداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أهداف الأداء'), 'url': '/hr/performance/goals/'},
            {'title': _('إنشاء هدف'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/goal_form.html', context)


@login_required
def goal_edit(request, pk):
    """تعديل هدف"""
    company = request.current_company
    goal = get_object_or_404(PerformanceGoal, pk=pk, company=company)

    if request.method == 'POST':
        form = PerformanceGoalForm(request.POST, instance=goal, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الهدف بنجاح'))
            return redirect('hr:goal_list')
    else:
        form = PerformanceGoalForm(instance=goal, company=company)

    context = {
        'form': form,
        'goal': goal,
        'title': _('تعديل هدف الأداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أهداف الأداء'), 'url': '/hr/performance/goals/'},
            {'title': _('تعديل هدف'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/goal_form.html', context)


@login_required
def goal_detail(request, pk):
    """تفاصيل الهدف"""
    company = request.current_company
    goal = get_object_or_404(
        PerformanceGoal.objects.select_related('employee', 'period'),
        pk=pk, company=company
    )

    context = {
        'goal': goal,
        'title': _('تفاصيل الهدف'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أهداف الأداء'), 'url': '/hr/performance/goals/'},
            {'title': _('تفاصيل الهدف'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/goal_detail.html', context)


@login_required
def goal_update_progress(request, pk):
    """تحديث تقدم الهدف"""
    company = request.current_company
    goal = get_object_or_404(PerformanceGoal, pk=pk, company=company)

    if request.method == 'POST':
        form = GoalProgressUpdateForm(request.POST)
        if form.is_valid():
            goal.achieved_value = form.cleaned_data['achieved_value']
            goal.status = form.cleaned_data['status']

            # Calculate progress percentage
            if goal.target_value and goal.target_value > 0:
                goal.progress_percentage = (goal.achieved_value / goal.target_value) * 100

            # Add note if provided
            note_text = form.cleaned_data.get('progress_note')
            if note_text:
                goal.notes = (goal.notes or '') + f'\n[{timezone.now().date()}]: {note_text}'

            goal.save()
            messages.success(request, _('تم تحديث تقدم الهدف بنجاح'))
            return redirect('hr:goal_detail', pk=goal.pk)
    else:
        form = GoalProgressUpdateForm(initial={
            'achieved_value': goal.achieved_value,
            'status': goal.status
        })

    context = {
        'form': form,
        'goal': goal,
        'title': _('تحديث تقدم الهدف'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('أهداف الأداء'), 'url': '/hr/performance/goals/'},
            {'title': _('تحديث التقدم'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/goal_progress_form.html', context)


@login_required
def goal_delete(request, pk):
    """حذف هدف"""
    company = request.current_company
    goal = get_object_or_404(PerformanceGoal, pk=pk, company=company)

    if request.method == 'POST':
        goal.delete()
        messages.success(request, _('تم حذف الهدف بنجاح'))
        return redirect('hr:goal_list')

    context = {
        'goal': goal,
        'title': _('حذف الهدف'),
    }
    return render(request, 'hr/performance/goal_confirm_delete.html', context)


# ==================== Performance Notes Views ====================

@login_required
def note_list(request):
    """قائمة ملاحظات الأداء"""
    company = request.current_company
    notes = PerformanceNote.objects.filter(
        company=company
    ).select_related('employee', 'noted_by').order_by('-date', '-created_at')

    # Filters
    note_type = request.GET.get('type')
    employee_id = request.GET.get('employee')

    if note_type:
        notes = notes.filter(note_type=note_type)
    if employee_id:
        notes = notes.filter(employee_id=employee_id)

    # Pagination
    paginator = Paginator(notes, 20)
    page = request.GET.get('page')
    notes = paginator.get_page(page)

    employees = Employee.objects.filter(company=company, is_active=True)

    context = {
        'notes': notes,
        'employees': employees,
        'selected_type': note_type,
        'selected_employee': employee_id,
        'title': _('ملاحظات الأداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('ملاحظات الأداء'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/note_list.html', context)


@login_required
def note_create(request):
    """إنشاء ملاحظة جديدة"""
    company = request.current_company

    if request.method == 'POST':
        form = PerformanceNoteForm(request.POST, company=company)
        if form.is_valid():
            note = form.save(commit=False)
            note.company = company
            note.noted_by = request.user
            note.created_by = request.user
            note.save()
            messages.success(request, _('تم إنشاء الملاحظة بنجاح'))
            return redirect('hr:note_list')
    else:
        form = PerformanceNoteForm(company=company)

    context = {
        'form': form,
        'title': _('إنشاء ملاحظة أداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('ملاحظات الأداء'), 'url': '/hr/performance/notes/'},
            {'title': _('إنشاء ملاحظة'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/note_form.html', context)


@login_required
def note_edit(request, pk):
    """تعديل ملاحظة"""
    company = request.current_company
    note = get_object_or_404(PerformanceNote, pk=pk, company=company)

    if request.method == 'POST':
        form = PerformanceNoteForm(request.POST, instance=note, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الملاحظة بنجاح'))
            return redirect('hr:note_list')
    else:
        form = PerformanceNoteForm(instance=note, company=company)

    context = {
        'form': form,
        'note': note,
        'title': _('تعديل ملاحظة الأداء'),
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('ملاحظات الأداء'), 'url': '/hr/performance/notes/'},
            {'title': _('تعديل ملاحظة'), 'url': None},
        ]
    }
    return render(request, 'hr/performance/note_form.html', context)


@login_required
def note_delete(request, pk):
    """حذف ملاحظة"""
    company = request.current_company
    note = get_object_or_404(PerformanceNote, pk=pk, company=company)

    if request.method == 'POST':
        note.delete()
        messages.success(request, _('تم حذف الملاحظة بنجاح'))
        return redirect('hr:note_list')

    context = {
        'note': note,
        'title': _('حذف الملاحظة'),
    }
    return render(request, 'hr/performance/note_confirm_delete.html', context)


# ==================== AJAX Views ====================

@login_required
def get_employees_by_department(request):
    """جلب الموظفين حسب القسم (AJAX)"""
    department_id = request.GET.get('department_id')
    company = request.current_company

    employees = Employee.objects.filter(company=company, is_active=True)
    if department_id:
        employees = employees.filter(department_id=department_id)

    data = [{'id': e.id, 'name': f'{e.first_name} {e.last_name}'} for e in employees]
    return JsonResponse(data, safe=False)


@login_required
def get_employee_goals(request, employee_id):
    """جلب أهداف الموظف (AJAX)"""
    company = request.current_company
    goals = PerformanceGoal.objects.filter(
        company=company, employee_id=employee_id
    ).values('id', 'title', 'status', 'progress_percentage')

    return JsonResponse(list(goals), safe=False)


@login_required
def get_evaluation_stats(request):
    """إحصائيات التقييمات (AJAX)"""
    company = request.current_company
    period_id = request.GET.get('period_id')

    evaluations = PerformanceEvaluation.objects.filter(company=company)
    if period_id:
        evaluations = evaluations.filter(period_id=period_id)

    stats = {
        'total': evaluations.count(),
        'draft': evaluations.filter(status='draft').count(),
        'self_evaluation': evaluations.filter(status='self_evaluation').count(),
        'manager_evaluation': evaluations.filter(status='manager_evaluation').count(),
        'pending_approval': evaluations.filter(status='pending_approval').count(),
        'approved': evaluations.filter(status='approved').count(),
        'rejected': evaluations.filter(status='rejected').count(),
        'avg_score': evaluations.filter(final_score__isnull=False).aggregate(Avg('final_score'))['final_score__avg'] or 0,
    }

    return JsonResponse(stats)

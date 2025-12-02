# apps/hr/views/training_views.py
"""
واجهات التدريب والتطوير - المرحلة 6
Training & Development Views - Phase 6
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.hr.models import (
    TrainingCategory,
    TrainingProvider,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRequest,
    TrainingPlan,
    TrainingPlanItem,
    TrainingFeedback,
    Employee,
    Department,
)
from apps.hr.forms import (
    TrainingCategoryForm,
    TrainingProviderForm,
    TrainingCourseForm,
    TrainingEnrollmentForm,
    BulkEnrollmentForm,
    TrainingRequestForm,
    TrainingRequestApprovalForm,
    TrainingPlanForm,
    TrainingPlanItemForm,
    TrainingFeedbackForm,
    CourseFilterForm,
    EnrollmentUpdateForm,
)


# ============================================
# Training Category Views
# ============================================

@login_required
def category_list(request):
    """قائمة فئات التدريب"""
    company = request.current_company
    categories = TrainingCategory.objects.filter(company=company).order_by('name')

    context = {
        'title': _('فئات التدريب'),
        'categories': categories,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فئات التدريب')},
        ]
    }
    return render(request, 'hr/training/categories/category_list.html', context)


@login_required
def category_create(request):
    """إنشاء فئة تدريب"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingCategoryForm(request.POST, company=company)
        if form.is_valid():
            category = form.save(commit=False)
            category.company = company
            category.save()
            messages.success(request, _('تم إنشاء فئة التدريب بنجاح'))
            return redirect('hr:training_category_list')
    else:
        form = TrainingCategoryForm(company=company)

    context = {
        'title': _('إضافة فئة تدريب'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فئات التدريب'), 'url': '/hr/training/categories/'},
            {'title': _('إضافة فئة')},
        ]
    }
    return render(request, 'hr/training/categories/category_form.html', context)


@login_required
def category_edit(request, pk):
    """تعديل فئة تدريب"""
    company = request.current_company
    category = get_object_or_404(TrainingCategory, pk=pk, company=company)

    if request.method == 'POST':
        form = TrainingCategoryForm(request.POST, instance=category, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث فئة التدريب بنجاح'))
            return redirect('hr:training_category_list')
    else:
        form = TrainingCategoryForm(instance=category, company=company)

    context = {
        'title': _('تعديل فئة التدريب'),
        'form': form,
        'category': category,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فئات التدريب'), 'url': '/hr/training/categories/'},
            {'title': _('تعديل')},
        ]
    }
    return render(request, 'hr/training/categories/category_form.html', context)


@login_required
def category_delete(request, pk):
    """حذف فئة تدريب"""
    company = request.current_company
    category = get_object_or_404(TrainingCategory, pk=pk, company=company)

    if request.method == 'POST':
        category.delete()
        messages.success(request, _('تم حذف فئة التدريب بنجاح'))
        return redirect('hr:training_category_list')

    context = {
        'title': _('حذف فئة التدريب'),
        'category': category,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('فئات التدريب'), 'url': '/hr/training/categories/'},
            {'title': _('حذف')},
        ]
    }
    return render(request, 'hr/training/categories/category_confirm_delete.html', context)


# ============================================
# Training Provider Views
# ============================================

@login_required
def provider_list(request):
    """قائمة مزودي التدريب"""
    company = request.current_company
    providers = TrainingProvider.objects.filter(company=company).order_by('name')

    # Filters
    provider_type = request.GET.get('type', '')
    if provider_type:
        providers = providers.filter(provider_type=provider_type)

    context = {
        'title': _('مزودي التدريب'),
        'providers': providers,
        'selected_type': provider_type,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('مزودي التدريب')},
        ]
    }
    return render(request, 'hr/training/providers/provider_list.html', context)


@login_required
def provider_create(request):
    """إنشاء مزود تدريب"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingProviderForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.company = company
            provider.save()
            messages.success(request, _('تم إنشاء مزود التدريب بنجاح'))
            return redirect('hr:training_provider_list')
    else:
        form = TrainingProviderForm()

    context = {
        'title': _('إضافة مزود تدريب'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('مزودي التدريب'), 'url': '/hr/training/providers/'},
            {'title': _('إضافة مزود')},
        ]
    }
    return render(request, 'hr/training/providers/provider_form.html', context)


@login_required
def provider_edit(request, pk):
    """تعديل مزود تدريب"""
    company = request.current_company
    provider = get_object_or_404(TrainingProvider, pk=pk, company=company)

    if request.method == 'POST':
        form = TrainingProviderForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث مزود التدريب بنجاح'))
            return redirect('hr:training_provider_list')
    else:
        form = TrainingProviderForm(instance=provider)

    context = {
        'title': _('تعديل مزود التدريب'),
        'form': form,
        'provider': provider,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('مزودي التدريب'), 'url': '/hr/training/providers/'},
            {'title': _('تعديل')},
        ]
    }
    return render(request, 'hr/training/providers/provider_form.html', context)


@login_required
def provider_delete(request, pk):
    """حذف مزود تدريب"""
    company = request.current_company
    provider = get_object_or_404(TrainingProvider, pk=pk, company=company)

    if request.method == 'POST':
        provider.delete()
        messages.success(request, _('تم حذف مزود التدريب بنجاح'))
        return redirect('hr:training_provider_list')

    context = {
        'title': _('حذف مزود التدريب'),
        'provider': provider,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('مزودي التدريب'), 'url': '/hr/training/providers/'},
            {'title': _('حذف')},
        ]
    }
    return render(request, 'hr/training/providers/provider_confirm_delete.html', context)


# ============================================
# Training Course Views
# ============================================

@login_required
def course_list(request):
    """قائمة الدورات التدريبية"""
    company = request.current_company
    courses = TrainingCourse.objects.filter(company=company).select_related(
        'category', 'provider'
    ).order_by('-start_date', 'name')

    # Filters
    filter_form = CourseFilterForm(request.GET, company=company)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        provider = filter_form.cleaned_data.get('provider')
        course_type = filter_form.cleaned_data.get('course_type')
        status = filter_form.cleaned_data.get('status')

        if category:
            courses = courses.filter(category=category)
        if provider:
            courses = courses.filter(provider=provider)
        if course_type:
            courses = courses.filter(course_type=course_type)
        if status:
            courses = courses.filter(status=status)

    paginator = Paginator(courses, 12)
    page = request.GET.get('page', 1)
    courses = paginator.get_page(page)

    context = {
        'title': _('الدورات التدريبية'),
        'courses': courses,
        'filter_form': filter_form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('الدورات التدريبية')},
        ]
    }
    return render(request, 'hr/training/courses/course_list.html', context)


@login_required
def course_create(request):
    """إنشاء دورة تدريبية"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, company=company)
        if form.is_valid():
            course = form.save(commit=False)
            course.company = company
            course.created_by = request.user
            course.save()
            form.save_m2m()  # Save ManyToMany fields
            messages.success(request, _('تم إنشاء الدورة التدريبية بنجاح'))
            return redirect('hr:training_course_list')
    else:
        form = TrainingCourseForm(company=company)

    context = {
        'title': _('إضافة دورة تدريبية'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('الدورات التدريبية'), 'url': '/hr/training/courses/'},
            {'title': _('إضافة دورة')},
        ]
    }
    return render(request, 'hr/training/courses/course_form.html', context)


@login_required
def course_edit(request, pk):
    """تعديل دورة تدريبية"""
    company = request.current_company
    course = get_object_or_404(TrainingCourse, pk=pk, company=company)

    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, instance=course, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الدورة التدريبية بنجاح'))
            return redirect('hr:training_course_detail', pk=pk)
    else:
        form = TrainingCourseForm(instance=course, company=company)

    context = {
        'title': _('تعديل الدورة التدريبية'),
        'form': form,
        'course': course,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('الدورات التدريبية'), 'url': '/hr/training/courses/'},
            {'title': course.name, 'url': f'/hr/training/courses/{pk}/'},
            {'title': _('تعديل')},
        ]
    }
    return render(request, 'hr/training/courses/course_form.html', context)


@login_required
def course_detail(request, pk):
    """تفاصيل الدورة التدريبية"""
    company = request.current_company
    course = get_object_or_404(
        TrainingCourse.objects.select_related('category', 'provider', 'trainer_employee'),
        pk=pk, company=company
    )

    enrollments = course.enrollments.select_related('employee', 'employee__department').order_by('status')

    # Statistics
    stats = {
        'total_enrolled': enrollments.count(),
        'completed': enrollments.filter(status='completed').count(),
        'attending': enrollments.filter(status='attending').count(),
        'pending': enrollments.filter(status__in=['nominated', 'pending_approval', 'approved']).count(),
    }

    context = {
        'title': course.name,
        'course': course,
        'enrollments': enrollments,
        'stats': stats,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('الدورات التدريبية'), 'url': '/hr/training/courses/'},
            {'title': course.name},
        ]
    }
    return render(request, 'hr/training/courses/course_detail.html', context)


@login_required
def course_delete(request, pk):
    """حذف دورة تدريبية"""
    company = request.current_company
    course = get_object_or_404(TrainingCourse, pk=pk, company=company)

    if request.method == 'POST':
        course.delete()
        messages.success(request, _('تم حذف الدورة التدريبية بنجاح'))
        return redirect('hr:training_course_list')

    context = {
        'title': _('حذف الدورة التدريبية'),
        'course': course,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('الدورات التدريبية'), 'url': '/hr/training/courses/'},
            {'title': _('حذف')},
        ]
    }
    return render(request, 'hr/training/courses/course_confirm_delete.html', context)


# ============================================
# Enrollment Views
# ============================================

@login_required
def enrollment_list(request):
    """قائمة التسجيلات"""
    company = request.current_company
    enrollments = TrainingEnrollment.objects.filter(company=company).select_related(
        'course', 'employee', 'employee__department'
    ).order_by('-created_at')

    # Filters
    course_id = request.GET.get('course', '')
    employee_id = request.GET.get('employee', '')
    status = request.GET.get('status', '')

    if course_id:
        enrollments = enrollments.filter(course_id=course_id)
    if employee_id:
        enrollments = enrollments.filter(employee_id=employee_id)
    if status:
        enrollments = enrollments.filter(status=status)

    paginator = Paginator(enrollments, 20)
    page = request.GET.get('page', 1)
    enrollments = paginator.get_page(page)

    courses = TrainingCourse.objects.filter(company=company, is_active=True)
    employees = Employee.objects.filter(company=company, is_active=True)

    context = {
        'title': _('تسجيلات التدريب'),
        'enrollments': enrollments,
        'courses': courses,
        'employees': employees,
        'selected_course': course_id,
        'selected_employee': employee_id,
        'selected_status': status,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تسجيلات التدريب')},
        ]
    }
    return render(request, 'hr/training/enrollments/enrollment_list.html', context)


@login_required
def enrollment_create(request):
    """إنشاء تسجيل في دورة"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingEnrollmentForm(request.POST, company=company)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.company = company
            enrollment.save()
            messages.success(request, _('تم تسجيل الموظف في الدورة بنجاح'))
            return redirect('hr:training_enrollment_list')
    else:
        form = TrainingEnrollmentForm(company=company)
        # Pre-fill course if provided
        course_id = request.GET.get('course')
        if course_id:
            form.fields['course'].initial = course_id

    context = {
        'title': _('تسجيل في دورة'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تسجيلات التدريب'), 'url': '/hr/training/enrollments/'},
            {'title': _('تسجيل جديد')},
        ]
    }
    return render(request, 'hr/training/enrollments/enrollment_form.html', context)


@login_required
def bulk_enrollment(request):
    """تسجيل جماعي"""
    company = request.current_company

    if request.method == 'POST':
        form = BulkEnrollmentForm(request.POST, company=company)
        if form.is_valid():
            course = form.cleaned_data['course']
            employees = form.cleaned_data.get('employees')
            department = form.cleaned_data.get('department')

            # If department selected, get all its employees
            if department and not employees:
                employees = Employee.objects.filter(
                    company=company,
                    department=department,
                    is_active=True
                )

            created_count = 0
            for employee in employees:
                # Check if already enrolled
                if not TrainingEnrollment.objects.filter(course=course, employee=employee).exists():
                    TrainingEnrollment.objects.create(
                        company=company,
                        course=course,
                        employee=employee,
                        status='nominated'
                    )
                    created_count += 1

            messages.success(request, _('تم تسجيل {} موظف في الدورة').format(created_count))
            return redirect('hr:training_course_detail', pk=course.pk)
    else:
        form = BulkEnrollmentForm(company=company)

    context = {
        'title': _('تسجيل جماعي'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تسجيلات التدريب'), 'url': '/hr/training/enrollments/'},
            {'title': _('تسجيل جماعي')},
        ]
    }
    return render(request, 'hr/training/enrollments/bulk_enrollment_form.html', context)


@login_required
def enrollment_update(request, pk):
    """تحديث حالة التسجيل"""
    company = request.current_company
    enrollment = get_object_or_404(TrainingEnrollment, pk=pk, company=company)

    if request.method == 'POST':
        form = EnrollmentUpdateForm(request.POST)
        if form.is_valid():
            enrollment.status = form.cleaned_data['status']
            if form.cleaned_data.get('attendance_percentage'):
                enrollment.attendance_percentage = form.cleaned_data['attendance_percentage']
            if form.cleaned_data.get('score'):
                enrollment.score = form.cleaned_data['score']
            if form.cleaned_data.get('notes'):
                enrollment.notes = form.cleaned_data['notes']

            # Auto-set dates based on status
            if enrollment.status == 'completed' and not enrollment.completion_date:
                enrollment.completion_date = timezone.now().date()
            elif enrollment.status == 'enrolled' and not enrollment.enrollment_date:
                enrollment.enrollment_date = timezone.now().date()
            elif enrollment.status == 'approved' and not enrollment.approval_date:
                enrollment.approval_date = timezone.now().date()
                enrollment.approved_by = request.user

            enrollment.save()
            messages.success(request, _('تم تحديث حالة التسجيل'))
            return redirect('hr:training_course_detail', pk=enrollment.course.pk)
    else:
        form = EnrollmentUpdateForm(initial={
            'status': enrollment.status,
            'attendance_percentage': enrollment.attendance_percentage,
            'score': enrollment.score,
            'notes': enrollment.notes,
        })

    context = {
        'title': _('تحديث التسجيل'),
        'form': form,
        'enrollment': enrollment,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تسجيلات التدريب'), 'url': '/hr/training/enrollments/'},
            {'title': _('تحديث')},
        ]
    }
    return render(request, 'hr/training/enrollments/enrollment_update.html', context)


@login_required
def enrollment_delete(request, pk):
    """حذف تسجيل"""
    company = request.current_company
    enrollment = get_object_or_404(TrainingEnrollment, pk=pk, company=company)
    course_pk = enrollment.course.pk

    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, _('تم حذف التسجيل بنجاح'))
        return redirect('hr:training_course_detail', pk=course_pk)

    context = {
        'title': _('حذف التسجيل'),
        'enrollment': enrollment,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('تسجيلات التدريب'), 'url': '/hr/training/enrollments/'},
            {'title': _('حذف')},
        ]
    }
    return render(request, 'hr/training/enrollments/enrollment_confirm_delete.html', context)


# ============================================
# Training Request Views
# ============================================

@login_required
def request_list(request):
    """قائمة طلبات التدريب"""
    company = request.current_company
    requests = TrainingRequest.objects.filter(company=company).select_related(
        'employee', 'employee__department', 'course', 'training_category'
    ).order_by('-created_at')

    # Filters
    status = request.GET.get('status', '')
    if status:
        requests = requests.filter(status=status)

    paginator = Paginator(requests, 15)
    page = request.GET.get('page', 1)
    requests = paginator.get_page(page)

    context = {
        'title': _('طلبات التدريب'),
        'requests': requests,
        'selected_status': status,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('طلبات التدريب')},
        ]
    }
    return render(request, 'hr/training/requests/request_list.html', context)


@login_required
def request_create(request):
    """إنشاء طلب تدريب"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingRequestForm(request.POST, company=company)
        if form.is_valid():
            training_request = form.save(commit=False)
            training_request.company = company
            training_request.created_by = request.user
            training_request.status = 'pending'
            training_request.save()
            messages.success(request, _('تم إنشاء طلب التدريب بنجاح'))
            return redirect('hr:training_request_list')
    else:
        form = TrainingRequestForm(company=company)

    context = {
        'title': _('طلب تدريب جديد'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('طلبات التدريب'), 'url': '/hr/training/requests/'},
            {'title': _('طلب جديد')},
        ]
    }
    return render(request, 'hr/training/requests/request_form.html', context)


@login_required
def request_detail(request, pk):
    """تفاصيل طلب التدريب"""
    company = request.current_company
    training_request = get_object_or_404(
        TrainingRequest.objects.select_related(
            'employee', 'employee__department', 'course', 'training_category'
        ),
        pk=pk, company=company
    )

    context = {
        'title': _('تفاصيل طلب التدريب'),
        'training_request': training_request,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('طلبات التدريب'), 'url': '/hr/training/requests/'},
            {'title': _('تفاصيل الطلب')},
        ]
    }
    return render(request, 'hr/training/requests/request_detail.html', context)


@login_required
def request_approve(request, pk):
    """موافقة/رفض طلب التدريب"""
    company = request.current_company
    training_request = get_object_or_404(TrainingRequest, pk=pk, company=company)

    if request.method == 'POST':
        form = TrainingRequestApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            comments = form.cleaned_data.get('comments', '')

            if action == 'approve':
                # Check if it needs manager or HR approval
                if training_request.status == 'pending':
                    training_request.status = 'manager_approved'
                    training_request.manager_approved_by = request.user
                    training_request.manager_approved_date = timezone.now().date()
                    training_request.manager_comments = comments
                elif training_request.status == 'manager_approved':
                    training_request.status = 'approved'
                    training_request.hr_approved_by = request.user
                    training_request.hr_approved_date = timezone.now().date()
                    training_request.hr_comments = comments
                messages.success(request, _('تمت الموافقة على الطلب'))
            else:
                training_request.status = 'rejected'
                training_request.rejection_reason = form.cleaned_data.get('rejection_reason', '')
                messages.warning(request, _('تم رفض الطلب'))

            training_request.save()
            return redirect('hr:training_request_list')
    else:
        form = TrainingRequestApprovalForm()

    context = {
        'title': _('معالجة طلب التدريب'),
        'form': form,
        'training_request': training_request,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('طلبات التدريب'), 'url': '/hr/training/requests/'},
            {'title': _('معالجة الطلب')},
        ]
    }
    return render(request, 'hr/training/requests/request_approve.html', context)


# ============================================
# Training Plan Views
# ============================================

@login_required
def plan_list(request):
    """قائمة خطط التدريب"""
    company = request.current_company
    plans = TrainingPlan.objects.filter(company=company).select_related(
        'department'
    ).order_by('-year', 'name')

    context = {
        'title': _('خطط التدريب'),
        'plans': plans,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('خطط التدريب')},
        ]
    }
    return render(request, 'hr/training/plans/plan_list.html', context)


@login_required
def plan_create(request):
    """إنشاء خطة تدريب"""
    company = request.current_company

    if request.method == 'POST':
        form = TrainingPlanForm(request.POST, company=company)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.company = company
            plan.created_by = request.user
            plan.save()
            messages.success(request, _('تم إنشاء خطة التدريب بنجاح'))
            return redirect('hr:training_plan_detail', pk=plan.pk)
    else:
        form = TrainingPlanForm(company=company)
        form.fields['year'].initial = timezone.now().year

    context = {
        'title': _('إنشاء خطة تدريب'),
        'form': form,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('خطط التدريب'), 'url': '/hr/training/plans/'},
            {'title': _('خطة جديدة')},
        ]
    }
    return render(request, 'hr/training/plans/plan_form.html', context)


@login_required
def plan_edit(request, pk):
    """تعديل خطة تدريب"""
    company = request.current_company
    plan = get_object_or_404(TrainingPlan, pk=pk, company=company)

    if request.method == 'POST':
        form = TrainingPlanForm(request.POST, instance=plan, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث خطة التدريب بنجاح'))
            return redirect('hr:training_plan_detail', pk=pk)
    else:
        form = TrainingPlanForm(instance=plan, company=company)

    context = {
        'title': _('تعديل خطة التدريب'),
        'form': form,
        'plan': plan,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('خطط التدريب'), 'url': '/hr/training/plans/'},
            {'title': plan.name, 'url': f'/hr/training/plans/{pk}/'},
            {'title': _('تعديل')},
        ]
    }
    return render(request, 'hr/training/plans/plan_form.html', context)


@login_required
def plan_detail(request, pk):
    """تفاصيل خطة التدريب"""
    company = request.current_company
    plan = get_object_or_404(
        TrainingPlan.objects.select_related('department'),
        pk=pk, company=company
    )

    items = plan.items.select_related('course', 'category').order_by('planned_quarter', '-priority')

    # Statistics
    stats = {
        'total_items': items.count(),
        'completed_items': items.filter(is_completed=True).count(),
        'total_budget': items.aggregate(Sum('planned_budget'))['planned_budget__sum'] or 0,
        'actual_budget': items.aggregate(Sum('actual_budget'))['actual_budget__sum'] or 0,
    }

    context = {
        'title': plan.name,
        'plan': plan,
        'items': items,
        'stats': stats,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('خطط التدريب'), 'url': '/hr/training/plans/'},
            {'title': plan.name},
        ]
    }
    return render(request, 'hr/training/plans/plan_detail.html', context)


@login_required
def plan_item_add(request, plan_pk):
    """إضافة بند لخطة التدريب"""
    company = request.current_company
    plan = get_object_or_404(TrainingPlan, pk=plan_pk, company=company)

    if request.method == 'POST':
        form = TrainingPlanItemForm(request.POST, company=company)
        if form.is_valid():
            item = form.save(commit=False)
            item.plan = plan
            item.save()
            form.save_m2m()
            messages.success(request, _('تم إضافة البند بنجاح'))
            return redirect('hr:training_plan_detail', pk=plan_pk)
    else:
        form = TrainingPlanItemForm(company=company)

    context = {
        'title': _('إضافة بند للخطة'),
        'form': form,
        'plan': plan,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': _('خطط التدريب'), 'url': '/hr/training/plans/'},
            {'title': plan.name, 'url': f'/hr/training/plans/{plan_pk}/'},
            {'title': _('إضافة بند')},
        ]
    }
    return render(request, 'hr/training/plans/plan_item_form.html', context)


# ============================================
# Training Feedback Views
# ============================================

@login_required
def feedback_create(request, enrollment_pk):
    """إنشاء تقييم للتدريب"""
    company = request.current_company
    enrollment = get_object_or_404(TrainingEnrollment, pk=enrollment_pk, company=company)

    # Check if feedback already exists
    if hasattr(enrollment, 'feedback'):
        messages.warning(request, _('تم تقديم التقييم سابقاً'))
        return redirect('hr:training_course_detail', pk=enrollment.course.pk)

    if request.method == 'POST':
        form = TrainingFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.enrollment = enrollment
            feedback.save()
            messages.success(request, _('تم تقديم التقييم بنجاح'))
            return redirect('hr:training_course_detail', pk=enrollment.course.pk)
    else:
        form = TrainingFeedbackForm()

    context = {
        'title': _('تقييم الدورة التدريبية'),
        'form': form,
        'enrollment': enrollment,
        'breadcrumbs': [
            {'title': _('الموارد البشرية'), 'url': '/hr/'},
            {'title': enrollment.course.name},
            {'title': _('تقييم')},
        ]
    }
    return render(request, 'hr/training/feedback/feedback_form.html', context)


# ============================================
# AJAX Views
# ============================================

@login_required
def get_employees_for_enrollment(request):
    """الحصول على الموظفين المتاحين للتسجيل في دورة"""
    company = request.current_company
    course_id = request.GET.get('course_id')

    if not course_id:
        return JsonResponse({'employees': []})

    # Get already enrolled employees
    enrolled_ids = TrainingEnrollment.objects.filter(
        course_id=course_id
    ).values_list('employee_id', flat=True)

    # Get available employees
    employees = Employee.objects.filter(
        company=company, is_active=True
    ).exclude(id__in=enrolled_ids).select_related('department')

    data = {
        'employees': [
            {
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}",
                'department': emp.department.name if emp.department else ''
            }
            for emp in employees
        ]
    }
    return JsonResponse(data)


@login_required
def get_training_stats(request):
    """إحصائيات التدريب"""
    company = request.current_company

    stats = {
        'total_courses': TrainingCourse.objects.filter(company=company).count(),
        'active_courses': TrainingCourse.objects.filter(company=company, status='in_progress').count(),
        'total_enrollments': TrainingEnrollment.objects.filter(company=company).count(),
        'completed_trainings': TrainingEnrollment.objects.filter(company=company, status='completed').count(),
        'pending_requests': TrainingRequest.objects.filter(company=company, status__in=['pending', 'manager_approved']).count(),
    }
    return JsonResponse(stats)

# apps/hr/views/ajax_views.py
"""
Ajax Views for HR Module - DataTables and API endpoints
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db.models import Q, Count, Sum
from django.utils.translation import gettext_lazy as _

from ..models import (
    Department, JobGrade, JobTitle, Employee,
    EmployeeContract, SalaryIncrement, LeaveType,
    Attendance, LeaveRequest, LeaveBalance, Advance, Overtime, EarlyLeave,
    Payroll, PayrollDetail
)


# ============================================
# Department Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def department_datatable_ajax(request):
    """Ajax endpoint لجدول الأقسام"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    is_active = request.GET.get('is_active', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = Department.objects.filter(
            company=request.current_company
        ).select_related('parent', 'manager').annotate(
            employees_count=Count('employees'),
            children_count=Count('children')
        )

        # تطبيق الفلاتر
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(code__icontains=search_term) |
                Q(name__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['code', 'name', 'parent__name', 'manager__first_name', 'employees_count', 'is_active']
            if int(order_column) < len(columns):
                order_field = columns[int(order_column)]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('code')

        # العد الإجمالي
        total_records = Department.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_department')
        can_delete = request.user.has_perm('hr.delete_department')

        for dept in queryset:
            # حالة القسم
            if dept.is_active:
                status_badge = '<span class="badge bg-success">نشط</span>'
            else:
                status_badge = '<span class="badge bg-danger">غير نشط</span>'

            # القسم الأب
            parent_display = dept.parent.name if dept.parent else '-'

            # المدير
            manager_display = dept.manager.get_full_name() if dept.manager else '-'

            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:department_update', args=[dept.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and dept.employees_count == 0 and dept.children_count == 0:
                actions.append(f'''
                    <a href="{reverse('hr:department_delete', args=[dept.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                dept.code,
                f'{dept.name} <span class="badge bg-info">{dept.employees_count} موظف</span>',
                parent_display,
                manager_display,
                dept.employees_count,
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Job Grade Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def job_grade_datatable_ajax(request):
    """Ajax endpoint لجدول الدرجات الوظيفية"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = JobGrade.objects.filter(
            company=request.current_company
        ).annotate(employees_count=Count('employees'))

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(code__icontains=search_term) |
                Q(name__icontains=search_term)
            )

        # الترتيب
        queryset = queryset.order_by('level', 'code')

        # العد الإجمالي
        total_records = JobGrade.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_jobgrade')
        can_delete = request.user.has_perm('hr.delete_jobgrade')

        for grade in queryset:
            # حالة الدرجة
            if grade.is_active:
                status_badge = '<span class="badge bg-success">نشط</span>'
            else:
                status_badge = '<span class="badge bg-danger">غير نشط</span>'

            # نطاق الراتب
            salary_range = f'{grade.min_salary:,.2f} - {grade.max_salary:,.2f}' if grade.min_salary and grade.max_salary else '-'

            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:job_grade_update', args=[grade.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and grade.employees_count == 0:
                actions.append(f'''
                    <a href="{reverse('hr:job_grade_delete', args=[grade.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                grade.code,
                grade.name,
                grade.level,
                salary_range,
                grade.employees_count,
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Job Title Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def job_title_datatable_ajax(request):
    """Ajax endpoint لجدول المسميات الوظيفية"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    department_id = request.GET.get('department', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = JobTitle.objects.filter(
            company=request.current_company
        ).select_related('department', 'job_grade').annotate(
            employees_count=Count('employees')
        )

        # تطبيق الفلاتر
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(code__icontains=search_term) |
                Q(name__icontains=search_term)
            )

        # الترتيب
        queryset = queryset.order_by('code')

        # العد الإجمالي
        total_records = JobTitle.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_jobtitle')
        can_delete = request.user.has_perm('hr.delete_jobtitle')

        for title in queryset:
            # حالة المسمى
            if title.is_active:
                status_badge = '<span class="badge bg-success">نشط</span>'
            else:
                status_badge = '<span class="badge bg-danger">غير نشط</span>'

            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:job_title_update', args=[title.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and title.employees_count == 0:
                actions.append(f'''
                    <a href="{reverse('hr:job_title_delete', args=[title.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                title.code,
                title.name,
                title.department.name if title.department else '-',
                title.job_grade.name if title.job_grade else '-',
                title.employees_count,
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Employee Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def employee_datatable_ajax(request):
    """Ajax endpoint لجدول الموظفين"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = Employee.objects.filter(
            company=request.current_company
        ).select_related('department', 'job_title', 'job_grade')

        # تطبيق الفلاتر
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        if status:
            queryset = queryset.filter(status=status)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(employee_number__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(national_id__icontains=search_term) |
                Q(mobile__icontains=search_term)
            )

        # الترتيب
        order_column = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]')

        if order_column:
            columns = ['employee_number', 'first_name', 'department__name', 'job_title__name', 'basic_salary', 'status']
            if int(order_column) < len(columns):
                order_field = columns[int(order_column)]
                if order_dir == 'desc':
                    order_field = '-' + order_field
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-created_at')

        # العد الإجمالي
        total_records = Employee.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_view = request.user.has_perm('hr.view_employee')
        can_edit = request.user.has_perm('hr.change_employee')
        can_delete = request.user.has_perm('hr.delete_employee')

        for emp in queryset:
            # حالة الموظف
            status_classes = {
                'active': 'bg-success',
                'inactive': 'bg-secondary',
                'on_leave': 'bg-warning',
                'terminated': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(emp.status, "bg-secondary")}">{emp.get_status_display()}</span>'

            # أزرار الإجراءات
            actions = []

            if can_view:
                actions.append(f'''
                    <a href="{reverse('hr:employee_detail', args=[emp.pk])}"
                       class="btn btn-outline-info btn-sm" title="عرض" data-bs-toggle="tooltip">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:employee_update', args=[emp.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('hr:employee_delete', args=[emp.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                emp.employee_number,
                emp.get_full_name(),
                emp.department.name if emp.department else '-',
                emp.job_title.name if emp.job_title else '-',
                f'{emp.basic_salary:,.2f}' if emp.basic_salary else '-',
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Contract Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def contract_datatable_ajax(request):
    """Ajax endpoint لجدول العقود"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    status = request.GET.get('status', '')
    contract_type = request.GET.get('contract_type', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = EmployeeContract.objects.filter(
            company=request.current_company
        ).select_related('employee')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(contract_number__icontains=search_term) |
                Q(employee__first_name__icontains=search_term) |
                Q(employee__last_name__icontains=search_term)
            )

        # الترتيب
        queryset = queryset.order_by('-start_date')

        # العد الإجمالي
        total_records = EmployeeContract.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_employeecontract')
        can_delete = request.user.has_perm('hr.delete_employeecontract')

        for contract in queryset:
            # حالة العقد
            status_classes = {
                'draft': 'bg-secondary',
                'active': 'bg-success',
                'expired': 'bg-warning',
                'terminated': 'bg-danger',
                'renewed': 'bg-info',
            }
            status_badge = f'<span class="badge {status_classes.get(contract.status, "bg-secondary")}">{contract.get_status_display()}</span>'

            # راتب العقد
            salary_display = f'{contract.contract_salary:,.2f}' if contract.contract_salary else '-'

            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:contract_update', args=[contract.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('hr:contract_delete', args=[contract.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                contract.contract_number or f'#{contract.pk}',
                contract.employee.get_full_name(),
                contract.get_contract_type_display(),
                contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '-',
                contract.end_date.strftime('%Y-%m-%d') if contract.end_date else 'غير محدد',
                salary_display,
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Increment Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def increment_datatable_ajax(request):
    """Ajax endpoint لجدول العلاوات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    status = request.GET.get('status', '')
    increment_type = request.GET.get('increment_type', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = SalaryIncrement.objects.filter(
            company=request.current_company
        ).select_related('employee')

        # تطبيق الفلاتر
        if status:
            queryset = queryset.filter(status=status)

        if increment_type:
            queryset = queryset.filter(increment_type=increment_type)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_term) |
                Q(employee__last_name__icontains=search_term) |
                Q(employee__employee_number__icontains=search_term)
            )

        # الترتيب
        queryset = queryset.order_by('-effective_date')

        # العد الإجمالي
        total_records = SalaryIncrement.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_salaryincrement')
        can_delete = request.user.has_perm('hr.delete_salaryincrement')

        for inc in queryset:
            # حالة العلاوة
            status_classes = {
                'pending': 'bg-warning',
                'approved': 'bg-info',
                'applied': 'bg-success',
                'rejected': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(inc.status, "bg-secondary")}">{inc.get_status_display()}</span>'

            # الراتب القديم
            old_salary_display = f'{inc.old_salary:,.2f}' if inc.old_salary else '-'

            # قيمة الزيادة
            amount_display = f'{inc.increment_amount:,.2f}'
            if inc.is_percentage:
                amount_display += '%'

            # الراتب الجديد
            new_salary_display = f'{inc.new_salary:,.2f}' if inc.new_salary else '-'

            # أزرار الإجراءات
            actions = []

            if can_edit and inc.status != 'applied':
                actions.append(f'''
                    <a href="{reverse('hr:increment_update', args=[inc.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete and inc.status != 'applied':
                actions.append(f'''
                    <a href="{reverse('hr:increment_delete', args=[inc.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                inc.employee.get_full_name(),
                inc.get_increment_type_display(),
                old_salary_display,
                amount_display,
                new_salary_display,
                inc.effective_date.strftime('%Y-%m-%d') if inc.effective_date else '-',
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Leave Type Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def leave_type_datatable_ajax(request):
    """Ajax endpoint لجدول أنواع الإجازات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    search_filter = request.GET.get('search_filter', '')

    # الفلاتر المخصصة
    is_active = request.GET.get('is_active', '')
    is_paid = request.GET.get('is_paid', '')

    try:
        queryset = LeaveType.objects.filter(
            company=request.current_company
        )

        # تطبيق الفلاتر
        if is_active == '1':
            queryset = queryset.filter(is_active=True)
        elif is_active == '0':
            queryset = queryset.filter(is_active=False)

        if is_paid == '1':
            queryset = queryset.filter(is_paid=True)
        elif is_paid == '0':
            queryset = queryset.filter(is_paid=False)

        # البحث العام
        if search_value or search_filter:
            search_term = search_value or search_filter
            queryset = queryset.filter(
                Q(code__icontains=search_term) |
                Q(name__icontains=search_term)
            )

        # الترتيب
        queryset = queryset.order_by('code')

        # العد الإجمالي
        total_records = LeaveType.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()

        # الصفحات
        queryset = queryset[start:start + length]

        # إعداد البيانات
        data = []
        can_edit = request.user.has_perm('hr.change_leavetype')
        can_delete = request.user.has_perm('hr.delete_leavetype')

        for leave_type in queryset:
            # حالة النوع
            if leave_type.is_active:
                status_badge = '<span class="badge bg-success">نشط</span>'
            else:
                status_badge = '<span class="badge bg-danger">غير نشط</span>'

            # مدفوعة
            if leave_type.is_paid:
                paid_icon = '<i class="fas fa-check text-success"></i>'
            else:
                paid_icon = '<i class="fas fa-times text-danger"></i>'

            # تؤثر على الراتب
            if leave_type.affects_salary:
                affects_salary_icon = '<i class="fas fa-check text-warning"></i>'
            else:
                affects_salary_icon = '<i class="fas fa-times text-muted"></i>'

            # تتطلب موافقة
            if leave_type.requires_approval:
                requires_approval_icon = '<i class="fas fa-check text-info"></i>'
            else:
                requires_approval_icon = '<i class="fas fa-times text-muted"></i>'

            # قابلة للترحيل
            if leave_type.carry_forward:
                carry_forward_icon = '<i class="fas fa-check text-success"></i>'
            else:
                carry_forward_icon = '<i class="fas fa-times text-muted"></i>'

            # أزرار الإجراءات
            actions = []

            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:leave_type_update', args=[leave_type.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل" data-bs-toggle="tooltip">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            if can_delete:
                actions.append(f'''
                    <a href="{reverse('hr:leave_type_delete', args=[leave_type.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف" data-bs-toggle="tooltip">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            actions_html = ' '.join(actions) if actions else '-'

            data.append([
                leave_type.code,
                leave_type.name,
                paid_icon,
                affects_salary_icon,
                f'{leave_type.default_days} يوم' if leave_type.default_days else '-',
                requires_approval_icon,
                carry_forward_icon,
                status_badge,
                actions_html
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Search Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def employee_search_ajax(request):
    """البحث السريع في الموظفين للـ autocomplete"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse([], safe=False)

    query = request.GET.get('term', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    employees = Employee.objects.filter(
        company=request.current_company,
        status='active'
    ).filter(
        Q(employee_number__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).select_related('department', 'job_title')[:20]

    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'text': f"{emp.employee_number} - {emp.get_full_name()}",
            'employee_number': emp.employee_number,
            'name': emp.get_full_name(),
            'department': emp.department.name if emp.department else '',
            'job_title': emp.job_title.name if emp.job_title else '',
            'basic_salary': float(emp.basic_salary) if emp.basic_salary else 0,
        })

    return JsonResponse(results, safe=False)


@login_required
@require_http_methods(["GET"])
def department_search_ajax(request):
    """البحث السريع في الأقسام للـ autocomplete"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse([], safe=False)

    query = request.GET.get('term', '').strip()
    if len(query) < 1:
        # إرجاع جميع الأقسام النشطة
        departments = Department.objects.filter(
            company=request.current_company,
            is_active=True
        )[:20]
    else:
        departments = Department.objects.filter(
            company=request.current_company,
            is_active=True
        ).filter(
            Q(code__icontains=query) |
            Q(name__icontains=query)
        )[:20]

    results = []
    for dept in departments:
        results.append({
            'id': dept.id,
            'text': f"{dept.code} - {dept.name}",
            'code': dept.code,
            'name': dept.name,
        })

    return JsonResponse(results, safe=False)


# ============================================
# Phase 2 - Attendance Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def attendance_datatable_ajax(request):
    """Ajax endpoint لجدول الحضور والانصراف"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    # الفلاتر
    employee_id = request.GET.get('employee', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    try:
        queryset = Attendance.objects.filter(
            company=request.current_company
        ).select_related('employee')

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if status:
            queryset = queryset.filter(status=status)
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        queryset = queryset.order_by('-date')

        total_records = Attendance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('hr.change_attendance')
        can_delete = request.user.has_perm('hr.delete_attendance')

        for att in queryset:
            status_classes = {
                'present': 'bg-success',
                'absent': 'bg-danger',
                'late': 'bg-warning',
                'leave': 'bg-info',
                'holiday': 'bg-secondary',
            }
            status_badge = f'<span class="badge {status_classes.get(att.status, "bg-secondary")}">{att.get_status_display()}</span>'

            actions = []
            if can_edit and att.status not in ['holiday']:
                actions.append(f'''
                    <a href="{reverse('hr:attendance_update', args=[att.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')
            if can_delete:
                actions.append(f'''
                    <a href="{reverse('hr:attendance_delete', args=[att.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                att.date.strftime('%Y-%m-%d'),
                att.employee.full_name,
                att.check_in.strftime('%H:%M') if att.check_in else '-',
                att.check_out.strftime('%H:%M') if att.check_out else '-',
                f'{att.working_hours:.1f}' if att.working_hours else '-',
                status_badge,
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 2 - Leave Request Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def leave_request_datatable_ajax(request):
    """Ajax endpoint لجدول طلبات الإجازات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    status = request.GET.get('status', '')
    leave_type = request.GET.get('leave_type', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = LeaveRequest.objects.filter(
            company=request.current_company
        ).select_related('employee', 'leave_type')

        if status:
            queryset = queryset.filter(status=status)
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
        if search_filter:
            queryset = queryset.filter(
                Q(request_number__icontains=search_filter) |
                Q(employee__first_name__icontains=search_filter) |
                Q(employee__last_name__icontains=search_filter)
            )

        queryset = queryset.order_by('-created_at')

        total_records = LeaveRequest.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('hr.change_leaverequest')
        can_delete = request.user.has_perm('hr.delete_leaverequest')

        for req in queryset:
            status_classes = {
                'draft': 'bg-secondary',
                'pending': 'bg-warning',
                'approved': 'bg-success',
                'rejected': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(req.status, "bg-secondary")}">{req.get_status_display()}</span>'

            actions = [f'''
                <a href="{reverse('hr:leave_request_detail', args=[req.pk])}"
                   class="btn btn-outline-info btn-sm" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
            ''']

            if can_edit and req.status in ['draft', 'pending']:
                actions.append(f'''
                    <a href="{reverse('hr:leave_request_update', args=[req.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')
            if can_delete and req.status in ['draft', 'pending']:
                actions.append(f'''
                    <a href="{reverse('hr:leave_request_delete', args=[req.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                req.request_number or f'#{req.pk}',
                req.employee.full_name,
                req.leave_type.name if req.leave_type else '-',
                req.start_date.strftime('%Y-%m-%d'),
                req.end_date.strftime('%Y-%m-%d'),
                req.days,
                status_badge,
                ' '.join(actions)
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 2 - Leave Balance Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def leave_balance_datatable_ajax(request):
    """Ajax endpoint لجدول أرصدة الإجازات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    year = request.GET.get('year', '')
    leave_type = request.GET.get('leave_type', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = LeaveBalance.objects.filter(
            company=request.current_company
        ).select_related('employee', 'leave_type')

        if year:
            queryset = queryset.filter(year=year)
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
        if search_filter:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_filter) |
                Q(employee__last_name__icontains=search_filter) |
                Q(employee__employee_number__icontains=search_filter)
            )

        queryset = queryset.order_by('employee__first_name', 'leave_type__name')

        total_records = LeaveBalance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('hr.change_leavebalance')

        for bal in queryset:
            remaining = bal.remaining
            remaining_class = 'text-success' if remaining > 5 else ('text-warning' if remaining > 0 else 'text-danger')

            actions = []
            if can_edit:
                actions.append(f'''
                    <a href="{reverse('hr:leave_balance_update', args=[bal.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')

            data.append([
                bal.employee.full_name,
                bal.leave_type.name if bal.leave_type else '-',
                bal.year,
                bal.opening_balance,
                bal.carried_forward or 0,
                bal.used,
                f'<span class="{remaining_class} fw-bold">{remaining}</span>',
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 2 - Advance Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def advance_datatable_ajax(request):
    """Ajax endpoint لجدول السلف"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    status = request.GET.get('status', '')
    search_filter = request.GET.get('search_filter', '')

    try:
        queryset = Advance.objects.filter(
            company=request.current_company
        ).select_related('employee')

        if status:
            queryset = queryset.filter(status=status)
        if search_filter:
            queryset = queryset.filter(
                Q(advance_number__icontains=search_filter) |
                Q(employee__first_name__icontains=search_filter) |
                Q(employee__last_name__icontains=search_filter)
            )

        queryset = queryset.order_by('-created_at')

        total_records = Advance.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_view = request.user.has_perm('hr.view_advance')

        for adv in queryset:
            status_classes = {
                'pending': 'bg-warning',
                'approved': 'bg-info',
                'rejected': 'bg-danger',
                'disbursed': 'bg-primary',
                'partially_paid': 'bg-secondary',
                'paid': 'bg-success',
            }
            status_badge = f'<span class="badge {status_classes.get(adv.status, "bg-secondary")}">{adv.get_status_display()}</span>'

            actions = []
            if can_view:
                actions.append(f'''
                    <a href="{reverse('hr:advance_detail', args=[adv.pk])}"
                       class="btn btn-outline-info btn-sm" title="عرض">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            data.append([
                adv.advance_number or f'#{adv.pk}',
                adv.employee.full_name,
                f'{adv.amount:,.2f}',
                adv.installments,
                f'{adv.installment_amount:,.2f}',
                f'{adv.remaining_amount:,.2f}',
                status_badge,
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 2 - Overtime Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def overtime_datatable_ajax(request):
    """Ajax endpoint لجدول العمل الإضافي"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    try:
        queryset = Overtime.objects.filter(
            company=request.current_company
        ).select_related('employee').order_by('-date')

        total_records = queryset.count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('hr.change_overtime')
        can_delete = request.user.has_perm('hr.delete_overtime')

        for ot in queryset:
            status_classes = {
                'pending': 'bg-warning',
                'approved': 'bg-success',
                'rejected': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(ot.status, "bg-secondary")}">{ot.get_status_display()}</span>'

            actions = []
            if can_edit and ot.status == 'pending':
                actions.append(f'''
                    <a href="{reverse('hr:overtime_update', args=[ot.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')
            if can_delete and ot.status == 'pending':
                actions.append(f'''
                    <a href="{reverse('hr:overtime_delete', args=[ot.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                ot.date.strftime('%Y-%m-%d'),
                ot.employee.full_name,
                f'{ot.hours:.1f}',
                f'{ot.rate}x',
                f'{ot.amount:,.2f}' if ot.amount else '-',
                status_badge,
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 2 - Early Leave Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def early_leave_datatable_ajax(request):
    """Ajax endpoint لجدول المغادرات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    try:
        queryset = EarlyLeave.objects.filter(
            company=request.current_company
        ).select_related('employee').order_by('-date')

        total_records = queryset.count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_edit = request.user.has_perm('hr.change_earlyleave')
        can_delete = request.user.has_perm('hr.delete_earlyleave')

        for el in queryset:
            status_classes = {
                'pending': 'bg-warning',
                'approved': 'bg-success',
                'rejected': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(el.status, "bg-secondary")}">{el.get_status_display()}</span>'

            actions = []
            if can_edit and el.status == 'pending':
                actions.append(f'''
                    <a href="{reverse('hr:early_leave_update', args=[el.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')
            if can_delete and el.status == 'pending':
                actions.append(f'''
                    <a href="{reverse('hr:early_leave_delete', args=[el.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                el.date.strftime('%Y-%m-%d'),
                el.employee.full_name,
                el.leave_time.strftime('%H:%M') if el.leave_time else '-',
                el.minutes,
                el.reason[:50] + '...' if len(el.reason) > 50 else el.reason,
                status_badge,
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })


# ============================================
# Phase 3 - Payroll Ajax Views
# ============================================

@login_required
@require_http_methods(["GET"])
def payroll_datatable_ajax(request):
    """Ajax endpoint لجدول مسيرات الرواتب"""

    if not hasattr(request, 'current_company') or not request.current_company:
        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': 'لا توجد شركة محددة'
        })

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    # الفلاتر
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    status = request.GET.get('status', '')

    try:
        queryset = Payroll.objects.filter(
            company=request.current_company
        ).select_related('branch')

        if year:
            queryset = queryset.filter(period_year=year)
        if month:
            queryset = queryset.filter(period_month=month)
        if status:
            queryset = queryset.filter(status=status)

        queryset = queryset.order_by('-period_year', '-period_month')

        total_records = Payroll.objects.filter(company=request.current_company).count()
        filtered_records = queryset.count()
        queryset = queryset[start:start + length]

        data = []
        can_view = request.user.has_perm('hr.view_payroll')
        can_edit = request.user.has_perm('hr.change_payroll')
        can_delete = request.user.has_perm('hr.delete_payroll')

        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        for payroll in queryset:
            status_classes = {
                'draft': 'bg-secondary',
                'processing': 'bg-warning',
                'calculated': 'bg-info',
                'approved': 'bg-success',
                'paid': 'bg-primary',
                'cancelled': 'bg-danger',
            }
            status_badge = f'<span class="badge {status_classes.get(payroll.status, "bg-secondary")}">{payroll.get_status_display()}</span>'

            # الفترة
            period = f'{month_names.get(payroll.period_month, payroll.period_month)} {payroll.period_year}'

            actions = []
            if can_view:
                actions.append(f'''
                    <a href="{reverse('hr:payroll_detail', args=[payroll.pk])}"
                       class="btn btn-outline-info btn-sm" title="عرض">
                        <i class="fas fa-eye"></i>
                    </a>
                ''')

            if can_edit and payroll.status == 'draft':
                actions.append(f'''
                    <a href="{reverse('hr:payroll_update', args=[payroll.pk])}"
                       class="btn btn-outline-primary btn-sm" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                ''')
            if can_delete and payroll.status == 'draft':
                actions.append(f'''
                    <a href="{reverse('hr:payroll_delete', args=[payroll.pk])}"
                       class="btn btn-outline-danger btn-sm" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                ''')

            data.append([
                payroll.number,
                period,
                payroll.branch.name if payroll.branch else 'جميع الفروع',
                payroll.employee_count or 0,
                f'{payroll.total_net or 0:,.2f}',
                status_badge,
                ' '.join(actions) if actions else '-'
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })

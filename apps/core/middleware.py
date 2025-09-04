"""
Middleware مخصص
لتتبع الفرع الحالي والشركة
"""

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from .models import Company, Branch

class CurrentBranchMiddleware(MiddlewareMixin):
    """تتبع الفرع الحالي للمستخدم"""

    def process_request(self, request):
        """إضافة الفرع الحالي للـ request"""
        if request.user.is_authenticated:
            # الفرع من الجلسة أو الافتراضي
            branch_id = request.session.get('current_branch')

            if branch_id:
                try:
                    branch = Branch.objects.get(id=branch_id)
                    if request.user.can_access_branch(branch):
                        request.current_branch = branch
                    else:
                        request.current_branch = request.user.branch
                except Branch.DoesNotExist:
                    request.current_branch = request.user.branch
            else:
                request.current_branch = request.user.branch
                if request.current_branch:
                    request.session['current_branch'] = request.current_branch.id

            # الشركة دائماً من الفرع
            if request.current_branch:
                request.current_company = request.current_branch.company
            else:
                request.current_company = request.user.company
        else:
            request.current_branch = None
            request.current_company = None


class CompanyBranchMiddleware(MiddlewareMixin):
    """
    Middleware لإضافة الشركة والفرع الحالي للطلب
    """

    def process_request(self, request):
        """معالجة الطلب وإضافة الشركة والفرع"""

        # إضافة الشركة الحالية
        if request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                # للتطبيقات التي تحتاج شركة افتراضية
                request.current_company = Company.objects.filter(is_active=True).first()
        else:
            request.current_company = None

        # إضافة الفرع الحالي
        if request.user.is_authenticated:
            # التحقق من الفرع المحفوظ في الجلسة
            branch_id = request.session.get('current_branch')

            if branch_id:
                try:
                    branch = Branch.objects.get(
                        id=branch_id,
                        company=request.current_company,
                        is_active=True
                    )
                    request.current_branch = branch
                except Branch.DoesNotExist:
                    request.current_branch = None
                    # إزالة الفرع غير الصالح من الجلسة
                    if 'current_branch' in request.session:
                        del request.session['current_branch']
            else:
                # استخدام الفرع الافتراضي للمستخدم
                if hasattr(request.user, 'branch') and request.user.branch:
                    request.current_branch = request.user.branch
                    request.session['current_branch'] = request.user.branch.id
                else:
                    # استخدام الفرع الرئيسي للشركة
                    if request.current_company:
                        main_branch = Branch.objects.filter(
                            company=request.current_company,
                            is_main=True,
                            is_active=True
                        ).first()

                        if main_branch:
                            request.current_branch = main_branch
                            request.session['current_branch'] = main_branch.id
                        else:
                            request.current_branch = None
                    else:
                        request.current_branch = None
        else:
            request.current_branch = None

        return None


class UserPermissionMiddleware(MiddlewareMixin):
    """
    Middleware لإضافة صلاحيات المستخدم المخصصة
    """

    def process_request(self, request):
        """إضافة الصلاحيات المخصصة للمستخدم"""

        if request.user.is_authenticated:
            # إضافة الصلاحيات المخصصة كخاصية للمستخدم
            if hasattr(request.user, 'custom_permissions'):
                custom_perms = request.user.custom_permissions.all()
                request.user._custom_permission_codes = [
                    perm.code for perm in custom_perms
                ]
            else:
                request.user._custom_permission_codes = []

        return None
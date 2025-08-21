"""
Middleware مخصص
لتتبع الفرع الحالي والشركة
"""

from django.utils.deprecation import MiddlewareMixin
from .models import Branch


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
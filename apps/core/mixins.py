# apps/core/mixins.py
"""
Mixins لإعادة الاستخدام
توفر وظائف مشتركة للـ Views
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import AuditLog
import json


class AuditLogMixin:
    """تسجيل العمليات تلقائياً"""

    def get_client_ip(self):
        """الحصول على IP العميل"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def log_action(self, action, obj, old_values=None, new_values=None):
        """تسجيل العملية"""
        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj),
            old_values=old_values,
            new_values=new_values,
            ip_address=self.get_client_ip(),
            # user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def form_valid(self, form):
        """تسجيل عند حفظ النموذج"""
        import datetime
        from decimal import Decimal

        # حفظ القيم القديمة قبل التعديل
        if self.object and self.object.pk:
            old_values = {}
            for field in self.object._meta.fields:
                value = getattr(self.object, field.name)
                # تحويل الـ objects إلى أرقام هوية
                if hasattr(value, 'pk'):
                    old_values[field.name] = value.pk
                elif isinstance(value, (datetime.datetime, datetime.date)):
                    old_values[field.name] = str(value)
                elif isinstance(value, Decimal):
                    old_values[field.name] = float(value)
                else:
                    old_values[field.name] = value
            action = 'UPDATE'
        else:
            old_values = None
            action = 'CREATE'

        response = super().form_valid(form)

        # حفظ القيم الجديدة
        new_values = {}
        for field in self.object._meta.fields:
            value = getattr(self.object, field.name)
            # تحويل الـ objects إلى أرقام هوية
            if hasattr(value, 'pk'):
                new_values[field.name] = value.pk
            elif isinstance(value, (datetime.datetime, datetime.date)):
                new_values[field.name] = str(value)
            elif isinstance(value, Decimal):
                new_values[field.name] = float(value)
            else:
                new_values[field.name] = value

        # تسجيل العملية
        self.log_action(action, self.object, old_values, new_values)

        return response


class CompanyBranchMixin:
    """فلترة حسب الشركة والفرع"""

    def get_queryset(self):
        """فلترة القائمة حسب شركة وفرع المستخدم"""
        queryset = super().get_queryset()
        user = self.request.user

        # فلترة حسب الشركة
        if hasattr(queryset.model, 'company') and user.company:
            queryset = queryset.filter(company=user.company)

        # فلترة حسب الفرع
        if hasattr(queryset.model, 'branch') and user.branch:
            # إذا لم يكن لديه صلاحية عرض كل الفروع
            if not user.custom_permissions.filter(
                    code='view_all_branches'
            ).exists():
                queryset = queryset.filter(branch=user.branch)

        return queryset

    def form_valid(self, form):
        """إضافة الشركة والفرع تلقائياً"""
        if hasattr(form.instance, 'company') and not form.instance.company:
            form.instance.company = self.request.user.company

        if hasattr(form.instance, 'branch') and not form.instance.branch:
            form.instance.branch = self.request.user.branch

        return super().form_valid(form)


class CompanyMixin(CompanyBranchMixin):
    """مايكسين لفلترة البيانات حسب الشركة فقط"""

    def get_queryset(self):
        """فلترة حسب الشركة فقط"""
        queryset = super().get_queryset()
        user = self.request.user

        # فلترة حسب الشركة فقط
        if hasattr(queryset.model, 'company') and user.company:
            return queryset.filter(company=user.company)

        return queryset

    def form_valid(self, form):
        """إضافة الشركة تلقائياً"""
        if hasattr(form.instance, 'company') and not form.instance.company:
            form.instance.company = self.request.user.company

        return super().form_valid(form)


class AjaxResponseMixin:
    """مايكسين للاستجابة AJAX"""

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
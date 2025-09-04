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
from django.forms import ModelForm


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
                # التعامل مع ملفات Django (ImageField, FileField)
                elif hasattr(value, 'name') and hasattr(value, '_file'):
                    try:
                        old_values[field.name] = value.name if value else None
                    except ValueError:
                        # الملف غير موجود
                        old_values[field.name] = None
                # التعامل مع القيم التي لا يمكن تحويلها إلى JSON
                else:
                    try:
                        import json
                        json.dumps(value)  # اختبار إمكانية التحويل
                        old_values[field.name] = value
                    except (TypeError, ValueError):
                        old_values[field.name] = str(value)  # تحويل إلى نص
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
            # التعامل مع ملفات Django (ImageField, FileField)
            elif hasattr(value, 'name') and hasattr(value, '_file'):
                try:
                    new_values[field.name] = value.name if value else None
                except ValueError:
                    # الملف غير موجود
                    new_values[field.name] = None
            # التعامل مع القيم التي لا يمكن تحويلها إلى JSON
            else:
                try:
                    import json
                    json.dumps(value)  # اختبار إمكانية التحويل
                    new_values[field.name] = value
                except (TypeError, ValueError):
                    new_values[field.name] = str(value)  # تحويل إلى نص

        # تسجيل العملية
        self.log_action(action, self.object, old_values, new_values)

        return response


class CompanyMixin:
    """مايكسين للموديلات التي تحتاج company فقط (مثل الأصناف)"""

    def get_queryset(self):
        """فلترة حسب الشركة فقط"""
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(queryset.model, 'company'):
            if hasattr(user, 'company') and user.company:
                return queryset.filter(company=user.company)
            else:
                # استخدام أول شركة متاحة
                from .models import Company
                company = Company.objects.first()
                if company:
                    return queryset.filter(company=company)

        return queryset

    def form_valid(self, form):
        """إضافة الشركة تلقائياً - بدون branch"""
        # التحقق من أن الـ form هو ModelForm
        if (isinstance(form, ModelForm) and
            hasattr(form._meta.model, 'company') and
            not getattr(form.instance, 'company', None)):
            from .models import Company
            company = Company.objects.first()
            form.instance.company = company

        return super().form_valid(form)


class CompanyBranchMixin:
    """فلترة حسب الشركة والفرع - للمستندات فقط"""

    def get_queryset(self):
        """فلترة القائمة حسب شركة وفرع المستخدم"""
        queryset = super().get_queryset()
        user = self.request.user

        # فلترة حسب الشركة
        if hasattr(queryset.model, 'company') and user.company:
            queryset = queryset.filter(company=user.company)

        # فلترة حسب الفرع - فقط للموديلات التي لها branch
        if hasattr(queryset.model, 'branch') and user.branch:
            if not user.custom_permissions.filter(code='view_all_branches').exists():
                queryset = queryset.filter(branch=user.branch)

        return queryset

    def form_valid(self, form):
        """إضافة الشركة والفرع للمستندات"""
        # التحقق من أن الـ form هو ModelForm قبل الوصول إلى _meta
        if isinstance(form, ModelForm):
            # الشركة
            if hasattr(form._meta.model, 'company') and not getattr(form.instance, 'company', None):
                from .models import Company
                company = Company.objects.first()
                form.instance.company = company

            # الفرع - فقط للموديلات التي تحتاجه
            if hasattr(form._meta.model, 'branch') and not getattr(form.instance, 'branch', None):
                current_branch = getattr(self.request, 'current_branch', None)
                if current_branch:
                    form.instance.branch = current_branch

        return super().form_valid(form)


class AjaxResponseMixin:
    """مايكسين للاستجابة AJAX"""

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
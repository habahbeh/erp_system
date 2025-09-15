# apps/core/forms/user_profile_forms.py
"""
نماذج ملفات المستخدمين
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models import UserProfile, Branch, Warehouse

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """نموذج إدارة ملف المستخدم"""

    class Meta:
        model = UserProfile
        fields = [
            'max_discount_percentage', 'max_credit_limit',
            'allowed_branches', 'allowed_warehouses'
        ]
        widgets = {
            'max_discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': _('نسبة الخصم المسموحة %')
            }),
            'max_credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': _('حد الائتمان المسموح')
            }),
            'allowed_branches': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'allowed_warehouses': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة الفروع والمستودعات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            self.fields['allowed_branches'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['allowed_warehouses'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')
        elif self.instance and self.instance.user and self.instance.user.company:
            company = self.instance.user.company

            self.fields['allowed_branches'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['allowed_warehouses'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')
        else:
            self.fields['allowed_branches'].queryset = Branch.objects.none()
            self.fields['allowed_warehouses'].queryset = Warehouse.objects.none()

        # إضافة نص مساعد
        self.fields['allowed_branches'].help_text = _('اتركه فارغاً للسماح بالوصول لكل الفروع')
        self.fields['allowed_warehouses'].help_text = _('اتركه فارغاً للسماح بالوصول لكل المستودعات')

    def clean_max_discount_percentage(self):
        """التحقق من نسبة الخصم"""
        value = self.cleaned_data.get('max_discount_percentage')
        if value and value > 100:
            raise ValidationError(_('نسبة الخصم لا يمكن أن تزيد عن 100%'))
        if value and value < 0:
            raise ValidationError(_('نسبة الخصم لا يمكن أن تكون سالبة'))
        return value

    def clean_max_credit_limit(self):
        """التحقق من حد الائتمان"""
        value = self.cleaned_data.get('max_credit_limit')
        if value and value < 0:
            raise ValidationError(_('حد الائتمان لا يمكن أن يكون سالباً'))
        return value


class BulkUserProfileForm(forms.Form):
    """نموذج تحديث ملفات متعددة للمستخدمين"""

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '8'
        }),
        label=_('المستخدمين'),
        help_text=_('اختر المستخدمين لتحديث ملفاتهم')
    )

    max_discount_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.01',
            'placeholder': _('نسبة الخصم الجديدة %')
        }),
        label=_('نسبة الخصم المسموحة %'),
        help_text=_('اتركه فارغاً لعدم التغيير')
    )

    max_credit_limit = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.01',
            'placeholder': _('حد الائتمان الجديد')
        }),
        label=_('حد الائتمان المسموح'),
        help_text=_('اتركه فارغاً لعدم التغيير')
    )

    allowed_branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5'
        }),
        label=_('الفروع المسموحة'),
        help_text=_('اتركه فارغاً لعدم التغيير')
    )

    allowed_warehouses = forms.ModelMultipleChoiceField(
        queryset=Warehouse.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5'
        }),
        label=_('المستودعات المسموحة'),
        help_text=_('اتركه فارغاً لعدم التغيير')
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة المستخدمين حسب الشركة
            self.fields['users'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name', 'username')

            # فلترة الفروع والمستودعات
            self.fields['allowed_branches'].queryset = Branch.objects.filter(
                company=company, is_active=True
            ).order_by('name')

            self.fields['allowed_warehouses'].queryset = Warehouse.objects.filter(
                company=company, is_active=True
            ).order_by('name')


class UserPermissionsForm(forms.Form):
    """نموذج إدارة صلاحيات المستخدم"""

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # إضافة صلاحيات Django
        self._add_django_permissions()

        # إضافة الصلاحيات المخصصة
        self._add_custom_permissions()

    def _add_django_permissions(self):
        """إضافة صلاحيات Django"""
        from django.contrib.auth.models import Permission

        # Core permissions
        core_permissions = Permission.objects.filter(
            content_type__app_label='core'
        ).select_related('content_type').order_by('content_type__model', 'name')

        if core_permissions.exists():
            user_current_core_perms = self.user.user_permissions.filter(
                content_type__app_label='core'
            ).values_list('id', flat=True)

            self.fields['django_core_permissions'] = forms.ModelMultipleChoiceField(
                queryset=core_permissions,
                required=False,
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                label='صلاحيات النظام الأساسي (Core)',
                initial=list(user_current_core_perms)  # ✅ التأكد من التحويل لـ list
            )

        # Auth permissions
        auth_permissions = Permission.objects.filter(
            content_type__app_label='auth'
        ).select_related('content_type').order_by('content_type__model', 'name')

        if auth_permissions.exists():
            user_current_auth_perms = self.user.user_permissions.filter(
                content_type__app_label='auth'
            ).values_list('id', flat=True)

            self.fields['django_auth_permissions'] = forms.ModelMultipleChoiceField(
                queryset=auth_permissions,
                required=False,
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                label='صلاحيات إدارة المستخدمين (Auth)',
                initial=list(user_current_auth_perms)  # ✅ التأكد من التحويل لـ list
            )

    def _add_custom_permissions(self):
        """إضافة الصلاحيات المخصصة"""
        try:
            from ..models import CustomPermission
            categories = CustomPermission.objects.filter(is_active=True).values_list('category', flat=True).distinct()

            for category in categories:
                permissions = CustomPermission.objects.filter(category=category, is_active=True).order_by('name')

                if permissions.exists():
                    user_custom_perms = []
                    if hasattr(self.user, 'custom_permissions'):
                        user_custom_perms = self.user.custom_permissions.filter(
                            category=category
                        ).values_list('id', flat=True)

                    field_name = f'permissions_{category}'
                    self.fields[field_name] = forms.ModelMultipleChoiceField(
                        queryset=permissions,
                        required=False,
                        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                        label=f'الصلاحيات المخصصة - {category}',
                        initial=list(user_custom_perms)
                    )
        except ImportError:
            pass

    def save(self):
        """حفظ الصلاحيات"""
        # حفظ صلاحيات Django
        for field_name, field_obj in self.fields.items():
            if field_name.startswith('django_'):
                app_label = field_name.replace('django_', '').replace('_permissions', '')

                # مسح الصلاحيات الحالية لهذا التطبيق
                current_perms = self.user.user_permissions.filter(content_type__app_label=app_label)
                self.user.user_permissions.remove(*current_perms)

                # إضافة الصلاحيات المحددة
                selected_perms = self.cleaned_data.get(field_name, [])
                if selected_perms:
                    self.user.user_permissions.add(*selected_perms)

        # حفظ الصلاحيات المخصصة
        try:
            if hasattr(self.user, 'custom_permissions'):
                self.user.custom_permissions.clear()

                for field_name, field_obj in self.fields.items():
                    if field_name.startswith('permissions_'):
                        selected_permissions = self.cleaned_data.get(field_name, [])
                        for permission in selected_permissions:
                            self.user.custom_permissions.add(permission)
        except AttributeError:
            pass
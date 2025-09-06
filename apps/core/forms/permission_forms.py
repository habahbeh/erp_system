# apps/core/forms/permission_forms.py
"""
نماذج إدارة الصلاحيات المخصصة
"""

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from ..models import CustomPermission, PermissionGroup, Company, UserProfile

User = get_user_model()


class CustomPermissionForm(forms.ModelForm):
    """نموذج إضافة/تعديل الصلاحية المخصصة"""

    class Meta:
        model = CustomPermission
        fields = [
            'name', 'code', 'description', 'category', 'permission_type',
            'is_active', 'requires_approval', 'max_amount', 'users', 'groups'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم وصفي للصلاحية')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رمز_الصلاحية_باللغة_الانجليزية')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف تفصيلي لما تفعله هذه الصلاحية')
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'permission_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('الحد الأقصى للمبلغ')
            }),
            'users': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '6'
            }),
            'groups': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '6'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة المستخدمين والمجموعات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company
            self.fields['users'].queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name', 'username')

        # إضافة نص مساعد
        self.fields['code'].help_text = _('رمز فريد بالإنجليزية، سيتم تحويل المسافات إلى _')
        self.fields['max_amount'].help_text = _('اتركه فارغاً إذا لم يكن هناك حد للمبلغ')

    def clean_code(self):
        """تنظيف رمز الصلاحية"""
        code = self.cleaned_data.get('code')
        if code:
            # تحويل إلى lowercase وتبديل المسافات بـ _
            code = code.lower().replace(' ', '_').replace('-', '_')

            # التحقق من عدم وجود رموز غير مسموحة
            import re
            if not re.match(r'^[a-z0-9_]+$', code):
                raise ValidationError(_('الرمز يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط'))

        return code

    def clean_max_amount(self):
        """التحقق من المبلغ"""
        max_amount = self.cleaned_data.get('max_amount')
        if max_amount is not None and max_amount < 0:
            raise ValidationError(_('الحد الأقصى للمبلغ لا يمكن أن يكون سالباً'))
        return max_amount


class PermissionGroupForm(forms.ModelForm):
    """نموذج إضافة/تعديل مجموعة الصلاحيات"""

    class Meta:
        model = PermissionGroup
        fields = [
            'name', 'description', 'permissions', 'django_permissions',
            'is_active', 'company'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم مجموعة الصلاحيات')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('وصف مجموعة الصلاحيات وما تشمله')
            }),
            'permissions': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8'
            }),
            'django_permissions': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '8'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # فلترة الصلاحيات المخصصة النشطة
        self.fields['permissions'].queryset = CustomPermission.objects.filter(
            is_active=True
        ).order_by('category', 'name')

        # فلترة صلاحيات Django للتطبيقات المهمة
        important_apps = ['core', 'auth', 'accounting', 'sales', 'purchases', 'inventory']
        self.fields['django_permissions'].queryset = Permission.objects.filter(
            content_type__app_label__in=important_apps
        ).select_related('content_type').order_by('content_type__app_label', 'name')

        # فلترة الشركات
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company
            self.fields['company'].queryset = Company.objects.filter(
                id=company.id
            ) if company else Company.objects.filter(is_active=True)
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)

        # إضافة نصوص مساعدة
        self.fields['permissions'].help_text = _('الصلاحيات المخصصة التجارية')
        self.fields['django_permissions'].help_text = _('صلاحيات Django الأساسية (CRUD)')
        self.fields['company'].help_text = _('اتركها فارغة للمجموعات العامة')


class BulkPermissionAssignForm(forms.Form):
    """نموذج تعيين صلاحيات متعددة"""

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '8'
        }),
        label=_('المستخدمين'),
        help_text=_('اختر المستخدمين لتعيين الصلاحيات لهم')
    )

    permission_groups = forms.ModelMultipleChoiceField(
        queryset=PermissionGroup.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '6'
        }),
        label=_('مجموعات الصلاحيات'),
        help_text=_('مجموعات الصلاحيات المراد تعيينها')
    )

    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=CustomPermission.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '8'
        }),
        label=_('صلاحيات مخصصة إضافية'),
        help_text=_('صلاحيات مخصصة إضافية غير المجموعات')
    )

    action_type = forms.ChoiceField(
        choices=[
            ('add', _('إضافة الصلاحيات')),
            ('replace', _('استبدال الصلاحيات')),
            ('remove', _('إزالة الصلاحيات')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('نوع العملية'),
        initial='add'
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

            # فلترة مجموعات الصلاحيات
            self.fields['permission_groups'].queryset = PermissionGroup.objects.filter(
                Q(company=company) | Q(company__isnull=True),
                is_active=True
            ).order_by('name')

            # فلترة الصلاحيات المخصصة
            self.fields['custom_permissions'].queryset = CustomPermission.objects.filter(
                is_active=True
            ).order_by('category', 'name')


class CopyUserPermissionsForm(forms.Form):
    """نموذج نسخ صلاحيات بين المستخدمين"""

    source_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('المستخدم المصدر'),
        help_text=_('المستخدم الذي ستُنسخ صلاحياته')
    )

    target_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '8'
        }),
        label=_('المستخدمين الهدف'),
        help_text=_('المستخدمين الذين ستُنسخ إليهم الصلاحيات')
    )

    copy_options = forms.MultipleChoiceField(
        choices=[
            ('custom_permissions', _('الصلاحيات المخصصة المباشرة')),
            ('permission_groups', _('مجموعات الصلاحيات')),
            ('django_groups', _('مجموعات Django')),
            ('user_permissions', _('صلاحيات Django المباشرة')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('ما المراد نسخه؟'),
        initial=['permission_groups']
    )

    replace_existing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('استبدال الصلاحيات الموجودة'),
        help_text=_('إذا تم التحديد، ستُستبدل جميع الصلاحيات الموجودة')
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة المستخدمين حسب الشركة
            users_queryset = User.objects.filter(
                company=company, is_active=True
            ).order_by('first_name', 'last_name', 'username')

            self.fields['source_user'].queryset = users_queryset
            self.fields['target_users'].queryset = users_queryset

    def clean(self):
        cleaned_data = super().clean()
        source_user = cleaned_data.get('source_user')
        target_users = cleaned_data.get('target_users')

        if source_user and target_users:
            if source_user in target_users:
                raise ValidationError(_('لا يمكن أن يكون المستخدم المصدر ضمن المستخدمين الهدف'))

        return cleaned_data
# apps/core/forms/user_forms.py
"""
نماذج إدارة المستخدمين
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models import Company, Branch, Warehouse

User = get_user_model()


class UserForm(UserCreationForm):
    """نموذج إضافة مستخدم جديد"""

    password1 = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل كلمة المرور')
        })
    )

    password2 = forms.CharField(
        label=_('تأكيد كلمة المرور'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أعد إدخال كلمة المرور')
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'emp_number',
            'company', 'branch', 'default_warehouse', 'max_discount_percentage',
            'ui_language', 'theme', 'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم'),
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الأول'),
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العائلة'),
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'emp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموظف')
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'ui_language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'theme': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['phone'].required = False
        self.fields['emp_number'].required = False
        self.fields['branch'].required = False
        self.fields['default_warehouse'].required = False

        # فلترة الشركات
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company
            self.fields['company'].initial = company
            self.fields['company'].queryset = Company.objects.filter(is_active=True)

            # فلترة الفروع حسب الشركة
            if company:
                self.fields['branch'].queryset = Branch.objects.filter(
                    company=company, is_active=True
                ).order_by('name')

                # فلترة المستودعات حسب الشركة
                self.fields['default_warehouse'].queryset = Warehouse.objects.filter(
                    company=company, is_active=True
                ).order_by('name')
            else:
                self.fields['branch'].queryset = Branch.objects.none()
                self.fields['default_warehouse'].queryset = Warehouse.objects.none()
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)
            self.fields['branch'].queryset = Branch.objects.none()
            self.fields['default_warehouse'].queryset = Warehouse.objects.none()

        # إضافة خيارات فارغة
        self.fields['company'].empty_label = _('اختر الشركة')
        self.fields['branch'].empty_label = _('اختر الفرع')
        self.fields['default_warehouse'].empty_label = _('اختر المستودع الافتراضي')

    def clean_username(self):
        """التحقق من عدم تكرار اسم المستخدم"""
        username = self.cleaned_data.get('username')
        if username:
            queryset = User.objects.filter(username=username)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('اسم المستخدم مستخدم مسبقاً'))
        return username

    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            queryset = User.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('البريد الإلكتروني مستخدم مسبقاً'))
        return email

    def clean_emp_number(self):
        """التحقق من عدم تكرار رقم الموظف"""
        emp_number = self.cleaned_data.get('emp_number')
        if emp_number:
            queryset = User.objects.filter(emp_number=emp_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('رقم الموظف مستخدم مسبقاً'))
        return emp_number


class UserUpdateForm(UserChangeForm):
    """نموذج تعديل المستخدم"""

    password = None  # إخفاء حقل كلمة المرور

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'emp_number',
            'company', 'branch', 'default_warehouse', 'max_discount_percentage',
            'ui_language', 'theme', 'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم المستخدم'),
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('البريد الإلكتروني'),
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('الاسم الأول'),
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العائلة'),
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الهاتف')
            }),
            'emp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('رقم الموظف')
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_warehouse': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'ui_language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'theme': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['phone'].required = False
        self.fields['emp_number'].required = False
        self.fields['branch'].required = False
        self.fields['default_warehouse'].required = False

        # فلترة الشركات والفروع والمستودعات
        self.fields['company'].queryset = Company.objects.filter(is_active=True)

        if self.instance.company:
            self.fields['branch'].queryset = Branch.objects.filter(
                company=self.instance.company, is_active=True
            ).order_by('name')

            self.fields['default_warehouse'].queryset = Warehouse.objects.filter(
                company=self.instance.company, is_active=True
            ).order_by('name')
        else:
            self.fields['branch'].queryset = Branch.objects.none()
            self.fields['default_warehouse'].queryset = Warehouse.objects.none()

        # إضافة خيارات فارغة
        self.fields['company'].empty_label = _('اختر الشركة')
        self.fields['branch'].empty_label = _('اختر الفرع')
        self.fields['default_warehouse'].empty_label = _('اختر المستودع الافتراضي')

    def clean_username(self):
        """التحقق من عدم تكرار اسم المستخدم"""
        username = self.cleaned_data.get('username')
        if username:
            queryset = User.objects.filter(username=username)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('اسم المستخدم مستخدم مسبقاً'))
        return username

    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if email:
            queryset = User.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('البريد الإلكتروني مستخدم مسبقاً'))
        return email

    def clean_emp_number(self):
        """التحقق من عدم تكرار رقم الموظف"""
        emp_number = self.cleaned_data.get('emp_number')
        if emp_number:
            queryset = User.objects.filter(emp_number=emp_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('رقم الموظف مستخدم مسبقاً'))
        return emp_number


class ChangePasswordForm(forms.Form):
    """نموذج تغيير كلمة المرور"""

    old_password = forms.CharField(
        label=_('كلمة المرور الحالية'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل كلمة المرور الحالية')
        })
    )

    new_password1 = forms.CharField(
        label=_('كلمة المرور الجديدة'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل كلمة المرور الجديدة')
        })
    )

    new_password2 = forms.CharField(
        label=_('تأكيد كلمة المرور الجديدة'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أعد إدخال كلمة المرور الجديدة')
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """التحقق من كلمة المرور الحالية"""
        old_password = self.cleaned_data.get('old_password')
        if old_password and not self.user.check_password(old_password):
            raise ValidationError(_('كلمة المرور الحالية غير صحيحة'))
        return old_password

    def clean(self):
        """التحقق من تطابق كلمات المرور الجديدة"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError(_('كلمات المرور الجديدة غير متطابقة'))

        return cleaned_data

    def save(self):
        """حفظ كلمة المرور الجديدة"""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
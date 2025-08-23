# apps/base_data/forms/warehouse_forms.py
"""
نماذج المستودعات ووحدات القياس
يتضمن: المستودعات، وحدات القياس، التحويلات بين المستودعات
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ..models import Warehouse, UnitOfMeasure
from core.models import User, Branch


class UnitOfMeasureForm(forms.ModelForm):
    """نموذج وحدة القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', 'name_en']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: KG, M, PC, BOX'),
                'maxlength': '10',
                'required': True,
                'autofocus': True,
                'style': 'text-transform: uppercase;',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: كيلوغرام، متر، قطعة، كرتون'),
                'required': True,
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Example: Kilogram, Meter, Piece, Box'),
                'dir': 'ltr',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # تطبيق الصلاحيات
        if self.user and not self.user.has_perm('base_data.change_unitofmeasure'):
            for field in self.fields:
                self.fields[field].disabled = True

    def clean_code(self):
        """التحقق من عدم تكرار الرمز وتحويله لأحرف كبيرة"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # التحقق من التكرار
            qs = UnitOfMeasure.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الرمز مستخدم بالفعل'))
        return code

    def clean_name(self):
        """التحقق من عدم تكرار الاسم"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            # التحقق من التكرار
            qs = UnitOfMeasure.objects.filter(
                name=name,
                company=self.instance.company if self.instance.pk else None
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('هذا الاسم مستخدم بالفعل'))
        return name


class WarehouseForm(forms.ModelForm):
    """نموذج المستودع"""

    class Meta:
        model = Warehouse
        fields = [
            'code', 'name', 'branch',
            'location', 'keeper', 'warehouse_type'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: WH01, MAIN, BR01'),
                'required': True,
                'autofocus': True,
                'maxlength': '20',
                'style': 'text-transform: uppercase;',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: المستودع الرئيسي، مستودع الفرع الأول'),
                'required': True,
            }),
            'branch': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر الفرع'),
            }),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('العنوان التفصيلي للمستودع'),
                'rows': 2,
            }),
            'keeper': forms.Select(attrs={
                'class': 'form-control form-select',
                'data-control': 'select2',
                'data-placeholder': _('اختر أمين المستودع'),
                'data-allow-clear': 'true',
            }),
            'warehouse_type': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فلترة البيانات حسب الشركة
        if hasattr(self.instance, 'company') and self.instance.company:
            company = self.instance.company

            # الفروع
            branches_qs = Branch.objects.filter(
                company=company,
                is_active=True
            ).order_by('name')

            # فلترة الفروع حسب صلاحيات المستخدم
            if self.user and not self.user.is_superuser:
                if hasattr(self.user, 'profile'):
                    allowed_branches = self.user.profile.allowed_branches.all()
                    if allowed_branches.exists():
                        branches_qs = branches_qs.filter(
                            id__in=allowed_branches.values_list('id', flat=True)
                        )
                else:
                    # فقط فرع المستخدم
                    if self.user.branch:
                        branches_qs = branches_qs.filter(id=self.user.branch.id)

            self.fields['branch'].queryset = branches_qs

            # تعيين الفرع الافتراضي
            if not self.instance.pk and self.user and self.user.branch:
                self.fields['branch'].initial = self.user.branch

            # أمناء المستودعات
            keepers_qs = User.objects.filter(
                company=company,
                is_active=True
            ).order_by('first_name', 'last_name')

            # فلترة حسب الصلاحية
            if self.user and not self.user.is_superuser:
                keepers_qs = keepers_qs.filter(
                    groups__permissions__codename='can_manage_warehouse'
                ).distinct()

            self.fields['keeper'].queryset = keepers_qs

        # تطبيق الصلاحيات
        self._apply_permissions()

    def _apply_permissions(self):
        """تطبيق الصلاحيات على الحقول"""
        if not self.user:
            return

        # تعطيل جميع الحقول لمن ليس لديه صلاحية التعديل
        if not self.user.has_perm('base_data.change_warehouse'):
            for field in self.fields:
                self.fields[field].disabled = True

        # منع تغيير الفرع لغير المدراء
        if not self.user.has_perm('base_data.change_warehouse_branch'):
            self.fields['branch'].disabled = True

    def clean_code(self):
        """التحقق من عدم تكرار الرمز"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # التحقق من التكرار على مستوى الشركة والفرع
            branch = self.cleaned_data.get('branch') or self.instance.branch
            qs = Warehouse.objects.filter(
                code=code,
                company=self.instance.company if self.instance.pk else None,
                branch=branch
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _('هذا الرمز مستخدم بالفعل في نفس الفرع')
                )
        return code

    def clean(self):
        """التحقق من منطقية البيانات"""
        cleaned_data = super().clean()
        warehouse_type = cleaned_data.get('warehouse_type')
        branch = cleaned_data.get('branch')

        # التحقق من وجود مستودع رئيسي واحد فقط لكل فرع
        if warehouse_type == 'main' and branch:
            qs = Warehouse.objects.filter(
                branch=branch,
                warehouse_type='main',
                is_active=True
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({
                    'warehouse_type': _('يوجد مستودع رئيسي بالفعل في هذا الفرع')
                })

        return cleaned_data


class WarehouseTransferForm(forms.Form):
    """نموذج التحويل بين المستودعات - للاستخدام في العمليات"""

    from_warehouse = forms.ModelChoiceField(
        label=_('من مستودع'),
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'data-control': 'select2',
            'data-placeholder': _('اختر المستودع المصدر'),
            'required': True,
        })
    )

    to_warehouse = forms.ModelChoiceField(
        label=_('إلى مستودع'),
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'data-control': 'select2',
            'data-placeholder': _('اختر المستودع الهدف'),
            'required': True,
        })
    )

    transfer_date = forms.DateField(
        label=_('تاريخ التحويل'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True,
        })
    )

    notes = forms.CharField(
        label=_('ملاحظات'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('ملاحظات حول التحويل'),
        })
    )

    def __init__(self, company, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.user = user

        # فلترة المستودعات
        warehouses = Warehouse.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        # فلترة حسب صلاحيات المستخدم
        if user and not user.is_superuser:
            if hasattr(user, 'profile'):
                allowed_warehouses = user.profile.allowed_warehouses.all()
                if allowed_warehouses.exists():
                    warehouses = warehouses.filter(
                        id__in=allowed_warehouses.values_list('id', flat=True)
                    )

        self.fields['from_warehouse'].queryset = warehouses
        self.fields['to_warehouse'].queryset = warehouses

        # تعيين التاريخ الافتراضي
        from django.utils import timezone
        self.fields['transfer_date'].initial = timezone.now().date()

    def clean(self):
        """التحقق من صحة التحويل"""
        cleaned_data = super().clean()
        from_warehouse = cleaned_data.get('from_warehouse')
        to_warehouse = cleaned_data.get('to_warehouse')

        # التحقق من عدم التحويل لنفس المستودع
        if from_warehouse and to_warehouse and from_warehouse == to_warehouse:
            raise ValidationError({
                'to_warehouse': _('لا يمكن التحويل إلى نفس المستودع')
            })

        # التحقق من صلاحية التحويل بين الفروع
        if from_warehouse and to_warehouse:
            if from_warehouse.branch != to_warehouse.branch:
                if self.user and not self.user.has_perm('inventory.transfer_between_branches'):
                    raise ValidationError(
                        _('ليس لديك صلاحية التحويل بين الفروع المختلفة')
                    )

        return cleaned_data


# نماذج إضافية للاستيراد والتصدير
class WarehouseImportForm(forms.Form):
    """نموذج استيراد المستودعات من ملف"""

    import_file = forms.FileField(
        label=_('ملف الاستيراد'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv',
            'required': True,
        }),
        help_text=_('ملف Excel أو CSV يحتوي على: رمز المستودع، الاسم، الفرع، النوع')
    )

    update_existing = forms.BooleanField(
        label=_('تحديث المستودعات الموجودة'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch',
        })
    )

    def clean_import_file(self):
        """التحقق من صحة الملف"""
        file = self.cleaned_data.get('import_file')
        if file:
            # التحقق من حجم الملف
            if file.size > 2 * 1024 * 1024:  # 2 ميجا
                raise ValidationError(
                    _('حجم الملف كبير جداً. الحد الأقصى 2 ميجابايت')
                )

            # التحقق من نوع الملف
            ext = file.name.split('.')[-1].lower()
            if ext not in ['xlsx', 'xls', 'csv']:
                raise ValidationError(
                    _('صيغة الملف غير مدعومة. يرجى استخدام Excel أو CSV')
                )

        return file


class UnitConversionImportForm(forms.Form):
    """نموذج استيراد معدلات التحويل بين الوحدات"""

    import_file = forms.FileField(
        label=_('ملف معدلات التحويل'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv',
            'required': True,
        }),
        help_text=_('ملف يحتوي على: رمز المادة، من وحدة، إلى وحدة، المعامل')
    )

    def clean_import_file(self):
        """التحقق من صحة الملف"""
        file = self.cleaned_data.get('import_file')
        if file:
            if file.size > 1 * 1024 * 1024:  # 1 ميجا
                raise ValidationError(
                    _('حجم الملف كبير جداً. الحد الأقصى 1 ميجابايت')
                )
        return file
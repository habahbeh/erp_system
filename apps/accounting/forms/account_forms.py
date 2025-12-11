# apps/accounting/forms/account_forms.py
"""
Account Forms - نماذج الحسابات ودليل الحسابات (محسن)
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Account, AccountType, CostCenter
from apps.core.models import Currency


class AccountForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الحسابات - محسن"""

    class Meta:
        model = Account
        fields = [
            'code', 'name', 'name_en', 'account_type', 'parent',
            'currency', 'nature', 'notes', 'is_suspended',
            'is_cash_account', 'is_bank_account', 'accept_entries',
            'opening_balance', 'opening_balance_date'
        ]

        widgets = {
            'opening_balance_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # تخصيص الحقول الأساسية
        self.fields['code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'رمز الحساب (مثال: 1111)',
            'maxlength': '20',
            'pattern': '[0-9A-Za-z-_]+',
            'title': 'يمكن استخدام الأرقام والحروف والشرطة فقط'
        })

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'اسم الحساب بالعربية',
            'maxlength': '200'
        })

        self.fields['name_en'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'اسم الحساب بالإنجليزية (اختياري)',
            'maxlength': '200'
        })

        # قوائم منسدلة محسنة
        self.fields['account_type'].widget.attrs.update({
            'class': 'form-select',
        })

        # الحساب الأب - قائمة منسدلة
        self.fields['parent'].widget.attrs.update({
            'class': 'form-select',
        })
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "لا يوجد (حساب رئيسي)"

        self.fields['currency'].widget.attrs.update({
            'class': 'form-select',
        })

        self.fields['nature'].widget.attrs.update({'class': 'form-select'})

        # حقول نصية
        self.fields['notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'ملاحظات إضافية (اختياري)'
        })

        # حقول رقمية
        self.fields['opening_balance'].widget.attrs.update({
            'class': 'form-control text-end',
            'step': '0.001',
            'placeholder': '0.000'
        })

        self.fields['opening_balance_date'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })

        # checkboxes محسنة
        checkbox_fields = ['is_suspended', 'is_cash_account', 'is_bank_account', 'accept_entries']
        for field in checkbox_fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-check-input',
                'role': 'switch'
            })

        # تحديد التسميات والمساعدات
        self.fields['code'].label = 'رمز الحساب'
        self.fields['name'].label = 'اسم الحساب'
        self.fields['name_en'].label = 'الاسم الإنجليزي'
        self.fields['account_type'].label = 'نوع الحساب'
        self.fields['parent'].label = 'الحساب الأب'
        self.fields['currency'].label = 'العملة الافتراضية'
        self.fields['nature'].label = 'طبيعة الحساب'
        self.fields['notes'].label = 'ملاحظات'
        self.fields['is_suspended'].label = 'حساب موقوف'
        self.fields['is_cash_account'].label = 'حساب نقدي'
        self.fields['is_bank_account'].label = 'حساب بنكي'
        self.fields['accept_entries'].label = 'يقبل قيود مباشرة'
        self.fields['opening_balance'].label = 'الرصيد الافتتاحي'
        self.fields['opening_balance_date'].label = 'تاريخ الرصيد الافتتاحي'

        # نصوص المساعدة
        self.fields['code'].help_text = 'رمز فريد للحساب (أرقام وحروف فقط)'
        self.fields['nature'].help_text = 'مدين = يزيد بالمدين، دائن = يزيد بالدائن'
        self.fields['is_cash_account'].help_text = 'للحسابات النقدية (صندوق، خزينة)'
        self.fields['is_bank_account'].help_text = 'للحسابات البنكية'
        self.fields['accept_entries'].help_text = 'هل يمكن إدخال قيود مباشرة على هذا الحساب'
        self.fields['parent'].help_text = 'اختياري - للحسابات الفرعية فقط'

        # فلترة البيانات حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            company = self.request.current_company

            # فلترة أنواع الحسابات
            self.fields['account_type'].queryset = AccountType.objects.all()

            # فلترة الحسابات الأب - فقط الحسابات التي يمكن أن تكون آباء
            parent_queryset = Account.objects.filter(
                company=company,
                level__lte=5  # حتى المستوى 5 يمكن أن يكون أب
            ).select_related('account_type').order_by('code')

            # استبعاد الحساب نفسه إذا كان تعديل
            if self.instance and self.instance.pk:
                parent_queryset = parent_queryset.exclude(pk=self.instance.pk)

                # استبعاد الحسابات الفرعية للحساب الحالي
                descendants = self.get_descendants(self.instance)
                if descendants:
                    parent_queryset = parent_queryset.exclude(pk__in=descendants)

            self.fields['parent'].queryset = parent_queryset

            # فلترة العملات
            try:
                # محاولة استخدام العلاقة companies (ManyToMany)
                self.fields['currency'].queryset = Currency.objects.filter(
                    Q(companies=company) | Q(is_base=True)
                ).filter(is_active=True).distinct()
            except Exception:
                # في حالة فشل المحاولة الأولى، استخدم جميع العملات النشطة
                self.fields['currency'].queryset = Currency.objects.filter(
                    is_active=True
                )

            # تعيين العملة الافتراضية
            if not self.instance.pk:
                try:
                    # البحث عن العملة الأساسية للشركة
                    default_currency = Currency.objects.filter(
                        companies=company, is_base=True
                    ).first()

                    # إذا لم توجد، ابحث عن أي عملة أساسية
                    if not default_currency:
                        default_currency = Currency.objects.filter(
                            is_base=True, is_active=True
                        ).first()

                    if default_currency:
                        self.fields['currency'].initial = default_currency

                except Exception:
                    # في حالة حدوث خطأ، اترك الحقل فارغاً
                    pass

        # إذا كان للحساب أطفال، منع تفعيل "يقبل قيود"
        if self.instance and self.instance.pk:
            if self.instance.children.exists():
                self.fields['accept_entries'].widget.attrs.update({
                    'disabled': 'disabled'
                })
                self.fields['accept_entries'].help_text = 'لا يمكن تفعيله للحسابات الأب'

    def get_descendants(self, account):
        """الحصول على جميع الحسابات الفرعية"""
        descendants = []

        def get_children(acc):
            children = Account.objects.filter(parent=acc)
            for child in children:
                descendants.append(child.pk)
                get_children(child)

        get_children(account)
        return descendants

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()

        if not self.request or not hasattr(self.request, 'current_company'):
            raise ValidationError('لا توجد شركة محددة')

        # التحقق من طول الرمز
        if len(code) < 2:
            raise ValidationError('رمز الحساب يجب أن يكون حرفين على الأقل')

        # التحقق من الرمز (أرقام وحروف فقط)
        if not code.replace('-', '').replace('_', '').isalnum():
            raise ValidationError('رمز الحساب يجب أن يحتوي على أرقام وحروف فقط')

        # التحقق من عدم تكرار الرمز في نفس الشركة
        existing = Account.objects.filter(
            code=code,
            company=self.request.current_company
        ).exclude(pk=self.instance.pk if self.instance else None)

        if existing.exists():
            raise ValidationError('رمز الحساب موجود مسبقاً في هذه الشركة')

        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if len(name) < 3:
            raise ValidationError('يجب أن يكون اسم الحساب 3 أحرف على الأقل')

        # التحقق من عدم تكرار الاسم في نفس الشركة
        if self.request and hasattr(self.request, 'current_company'):
            existing = Account.objects.filter(
                name=name,
                company=self.request.current_company
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('اسم الحساب موجود مسبقاً في هذه الشركة')

        return name

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')

        if parent:
            # التحقق من عدم إنشاء دورة
            if self.instance and parent == self.instance:
                raise ValidationError('لا يمكن أن يكون الحساب أب لنفسه')

            # التحقق من أن الأب في نفس الشركة
            if self.request and hasattr(self.request, 'current_company'):
                if parent.company != self.request.current_company:
                    raise ValidationError('الحساب الأب يجب أن يكون في نفس الشركة')

            # التحقق من العمق الهرمي
            level = 1
            current_parent = parent
            while current_parent:
                level += 1
                if level > 10:  # زيادة الحد الأقصى للمستويات
                    raise ValidationError('لا يمكن تجاوز 10 مستويات في التسلسل الهرمي')
                current_parent = current_parent.parent

                # التحقق من عدم إنشاء دورة
                if current_parent == self.instance:
                    raise ValidationError('هذا الاختيار سيؤدي إلى دورة في التسلسل الهرمي')

        return parent

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        accept_entries = cleaned_data.get('accept_entries')
        is_cash_account = cleaned_data.get('is_cash_account')
        is_bank_account = cleaned_data.get('is_bank_account')
        account_type = cleaned_data.get('account_type')

        # لا يمكن أن يكون الحساب نقدي وبنكي معاً
        if is_cash_account and is_bank_account:
            raise ValidationError('لا يمكن أن يكون الحساب نقدي وبنكي في نفس الوقت')

        # منع تحديد حساب أب يقبل قيود مباشرة
        if parent and parent.accept_entries:
            self.add_error('parent',
                           'لا يمكن اختيار حساب أب يقبل قيود مباشرة. يجب تعديل الحساب الأب أولاً.')

        # التحقق من أن الحساب الحالي إذا كان له أطفال لا يمكنه قبول قيود
        if self.instance and self.instance.pk:
            if self.instance.children.exists() and accept_entries:
                self.add_error('accept_entries',
                               'الحسابات الأب لا يمكنها قبول قيود مباشرة. احذف الحسابات الفرعية أولاً.')

        # التحقق من تطابق نوع الحساب مع الأب
        if parent and account_type and parent.account_type != account_type:
            self.add_error('account_type',
                           'نوع الحساب يجب أن يطابق نوع الحساب الأب')

        return cleaned_data


class AccountImportForm(forms.Form):
    """نموذج استيراد الحسابات من ملف Excel/CSV"""

    file = forms.FileField(
        label='ملف الاستيراد',
        help_text='يدعم ملفات Excel (.xlsx, .xls) و CSV (.csv)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    update_existing = forms.BooleanField(
        label='تحديث الحسابات الموجودة',
        help_text='في حالة وجود حساب بنفس الرمز، سيتم تحديث بياناته',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )

    validate_hierarchy = forms.BooleanField(
        label='التحقق من التسلسل الهرمي',
        help_text='التحقق من صحة الهيكل الهرمي للحسابات',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )

    def clean_file(self):
        file = self.cleaned_data['file']

        # التحقق من نوع الملف
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError('نوع الملف غير مدعوم. يرجى رفع ملف Excel أو CSV')

        # التحقق من حجم الملف (10MB max)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError('حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت')

        return file


class AccountFilterForm(forms.Form):
    """نموذج فلترة الحسابات - محسن"""

    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        required=False,
        empty_label="جميع الأنواع",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-live-search': 'true'
        })
    )

    parent = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="جميع الحسابات",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-live-search': 'true'
        })
    )

    is_active = forms.ChoiceField(
        choices=[
            ('', 'جميع الحالات'),
            ('1', 'نشط'),
            ('0', 'موقوف')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    has_children = forms.ChoiceField(
        choices=[
            ('', 'الكل'),
            ('1', 'حسابات أب'),
            ('0', 'حسابات فرعية')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    accept_entries = forms.ChoiceField(
        choices=[
            ('', 'الكل'),
            ('1', 'يقبل قيود'),
            ('0', 'لا يقبل قيود')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في الرمز أو الاسم',
            'autocomplete': 'off'
        })
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if request and hasattr(request, 'current_company'):
            self.fields['parent'].queryset = Account.objects.filter(
                company=request.current_company,
                level__lt=4,
                children__isnull=False
            ).distinct()


class AccountBulkActionForm(forms.Form):
    """نموذج الإجراءات المجمعة على الحسابات"""

    ACTION_CHOICES = [
        ('', 'اختر إجراء...'),
        ('suspend', 'إيقاف الحسابات'),
        ('activate', 'تنشيط الحسابات'),
        ('change_type', 'تغيير نوع الحساب'),
        ('export', 'تصدير الحسابات المحددة'),
        ('delete', 'حذف الحسابات'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleActionOptions(this.value)'
        }),
        label='الإجراء'
    )

    account_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    # خيارات إضافية لتغيير النوع
    new_account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'display: none;'
        }),
        label='النوع الجديد'
    )

    # تأكيد العمليات الخطيرة
    confirm_action = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'style': 'display: none;'
        }),
        label='أتأكد من تنفيذ هذا الإجراء'
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        account_ids = cleaned_data.get('account_ids', '')

        if not action:
            raise ValidationError('يجب اختيار إجراء')

        if not account_ids:
            raise ValidationError('يجب اختيار حساب واحد على الأقل')

        # التحقق من تأكيد العمليات الخطيرة
        if action in ['delete'] and not cleaned_data.get('confirm_action'):
            raise ValidationError('يجب تأكيد تنفيذ هذا الإجراء')

        if action == 'change_type' and not cleaned_data.get('new_account_type'):
            raise ValidationError('يجب اختيار النوع الجديد')

        # تحويل IDs إلى list
        try:
            cleaned_data['account_ids'] = [int(id) for id in account_ids.split(',') if id.strip()]
        except ValueError:
            raise ValidationError('معرفات الحسابات غير صحيحة')

        return cleaned_data


class AccountMoveForm(forms.Form):
    """نموذج نقل الحسابات إلى حساب أب آخر"""

    account_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

    new_parent = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="نقل إلى المستوى الأول (بدون أب)",
        widget=forms.Select(attrs={
            'class': 'form-select account-select',
            'data-live-search': 'true'
        }),
        label='الحساب الأب الجديد'
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        exclude_ids = kwargs.pop('exclude_ids', [])
        super().__init__(*args, **kwargs)

        if request and hasattr(request, 'current_company'):
            # الحسابات المسموح نقلها إليها (لا تشمل الحسابات المحددة)
            self.fields['new_parent'].queryset = Account.objects.filter(
                company=request.current_company,
                can_have_children=True,
                level__lt=4
            ).exclude(pk__in=exclude_ids)

    def clean_account_ids(self):
        account_ids = self.cleaned_data['account_ids']

        try:
            return [int(id) for id in account_ids.split(',') if id.strip()]
        except ValueError:
            raise ValidationError('معرفات الحسابات غير صحيحة')


class CostCenterForm(forms.ModelForm):
    """نموذج مركز التكلفة"""

    class Meta:
        model = CostCenter
        fields = ['name', 'code', 'description', 'parent', 'cost_center_type', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'cost_center_type': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CostCenterFilterForm(forms.Form):
    """نموذج فلترة مراكز التكلفة"""

    cost_center_type = forms.ChoiceField(
        choices=[('', 'جميع الأنواع')] + CostCenter.COST_CENTER_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_active = forms.ChoiceField(
        choices=[('', 'الكل'), ('1', 'نشط'), ('0', 'غير نشط')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'البحث في الرمز أو الاسم'
        })
    )
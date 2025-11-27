# ERP System - Project Context for HR Module Development

> هذا الملف مرجع شامل لمساعدة Claude Code في بناء نظام HR بنفس أسلوب المشروع

---

## 1. بنية المشروع الكاملة

```
erp_system/
├── config/                          # إعدادات Django
│   ├── settings.py                  # الإعدادات الرئيسية
│   ├── urls.py                      # URLs الرئيسية
│   └── wsgi.py
├── apps/                            # تطبيقات النظام
│   ├── core/                        # النواة - النماذج والوظائف المشتركة
│   │   ├── models/                  # النماذج (مجزأة)
│   │   │   ├── __init__.py          # تصدير كل النماذج
│   │   │   ├── base_models.py       # BaseModel, DocumentBaseModel
│   │   │   ├── company_models.py    # Company, Branch, Warehouse
│   │   │   ├── user_models.py       # User, UserProfile, CustomPermission
│   │   │   ├── item_models.py       # Item, ItemCategory, Variant...
│   │   │   ├── partner_models.py    # BusinessPartner
│   │   │   ├── uom_models.py        # UnitOfMeasure, UoMConversion
│   │   │   ├── pricing_models.py    # PriceList, PriceListItem
│   │   │   ├── audit_models.py      # AuditLog
│   │   │   └── system_models.py     # NumberingSequence, SystemSettings
│   │   ├── views/                   # Views (مجزأة)
│   │   ├── forms/                   # Forms (مجزأة)
│   │   ├── mixins.py                # CompanyMixin, AuditLogMixin
│   │   ├── middleware.py            # CurrentBranchMiddleware
│   │   ├── decorators.py            # permission_required_with_message
│   │   └── templatetags/            # Template tags مخصصة
│   │
│   ├── accounting/                  # المحاسبة - المرجع الرئيسي للأسلوب
│   │   ├── models/                  # 5 ملفات نماذج
│   │   │   ├── account_models.py    # AccountType, Account, CostCenter
│   │   │   ├── fiscal_models.py     # FiscalYear, AccountingPeriod
│   │   │   ├── journal_models.py    # JournalEntry, JournalEntryLine
│   │   │   ├── voucher_models.py    # PaymentVoucher, ReceiptVoucher
│   │   │   └── balance_models.py    # AccountBalance, AccountBalanceHistory
│   │   ├── views/                   # 8 ملفات views
│   │   ├── forms/                   # 6 ملفات forms
│   │   ├── templates/accounting/    # القوالب
│   │   └── urls.py
│   │
│   ├── hr/                          # الموارد البشرية (للبناء)
│   ├── sales/                       # المبيعات
│   ├── purchases/                   # المشتريات
│   ├── inventory/                   # المخزون
│   ├── assets/                      # الأصول الثابتة
│   └── reports/                     # التقارير
├── templates/                       # القوالب العامة
│   └── base/
│       └── base.html                # القالب الأساسي
└── static/                          # الملفات الثابتة
```

---

## 2. النماذج الأساسية (Base Models)

### 2.1 BaseModel - للبيانات الأساسية (Master Data)

```python
# apps/core/models/base_models.py

class BaseModel(models.Model):
    """النموذج الأساسي الموحد - للبيانات الأساسية"""

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        verbose_name=_('الشركة')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التعديل')
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        verbose_name=_('أنشأ بواسطة')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    class Meta:
        abstract = True
```

**استخدم BaseModel لـ:**
- الموظفين (Employees)
- الأقسام (Departments)
- المسميات الوظيفية (JobTitles)
- أي بيانات أساسية تابعة للشركة

---

### 2.2 DocumentBaseModel - للمستندات والعمليات

```python
class DocumentBaseModel(BaseModel):
    """النموذج الأساسي للمستندات والفواتير - يحتاج فرع"""

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.PROTECT,
        verbose_name=_('الفرع')
    )

    class Meta:
        abstract = True
```

**استخدم DocumentBaseModel لـ:**
- طلبات الإجازة (LeaveRequests)
- سجلات الحضور (AttendanceRecords)
- مسيرات الرواتب (PayrollRuns)
- أي مستند يحتاج تتبع الفرع

---

## 3. نماذج المحاسبة - مرجع الأسلوب

### 3.1 نمط النموذج مع الحالات (Status)

```python
# من apps/accounting/models/journal_models.py

class JournalEntry(DocumentBaseModel):
    """القيود اليومية - مثال للمستند مع حالات"""

    # === الثوابت (CHOICES) ===
    ENTRY_TYPES = [
        ('manual', _('قيد يدوي')),
        ('auto', _('قيد تلقائي')),
        ('opening', _('قيد افتتاحي')),
        ('closing', _('قيد إقفال')),
        ('adjustment', _('قيد تسوية')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('posted', _('مرحل')),
        ('cancelled', _('ملغي')),
    ]

    # === الحقول الأساسية ===
    number = models.CharField(
        _('رقم القيد'),
        max_length=50,
        editable=False  # ⚡ توليد تلقائي
    )
    entry_date = models.DateField(
        _('تاريخ القيد'),
        default=date.today
    )
    entry_type = models.CharField(
        _('نوع القيد'),
        max_length=20,
        choices=ENTRY_TYPES,
        default='manual'
    )
    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # === الحقول المحسوبة ===
    total_debit = models.DecimalField(
        _('إجمالي المدين'),
        max_digits=15,
        decimal_places=4,
        default=0,
        editable=False  # ⚡ محسوب تلقائياً
    )

    # === الترحيل ===
    posted_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posted_journal_entries',
        verbose_name=_('رحل بواسطة')
    )
    posted_date = models.DateTimeField(
        _('تاريخ الترحيل'),
        null=True, blank=True
    )

    # === الربط بمصادر أخرى ===
    source_document = models.CharField(
        _('المستند المصدر'),
        max_length=100,
        blank=True
    )
    source_id = models.PositiveIntegerField(
        _('معرف المصدر'),
        null=True, blank=True
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('قيد يومية')
        verbose_name_plural = _('القيود اليومية')
        unique_together = [['company', 'number']]  # ⚡ فريد بالشركة
        ordering = ['-entry_date', '-number']
        indexes = [
            models.Index(fields=['entry_date', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['number']),
        ]

    # === دوال التحقق من الصلاحيات ===
    def can_edit(self):
        """هل يمكن تعديل المستند"""
        return self.status == 'draft'

    def can_post(self):
        """هل يمكن ترحيل المستند"""
        return self.status == 'draft' and self.is_balanced and self.lines.exists()

    def can_unpost(self):
        """هل يمكن إلغاء ترحيل المستند"""
        return self.status == 'posted'

    def can_delete(self):
        """هل يمكن حذف المستند"""
        return self.status == 'draft'

    # === دالة الحفظ المخصصة ===
    def save(self, *args, **kwargs):
        self.full_clean()

        is_new = self.pk is None

        if is_new and not self.number:
            self.number = self.generate_number()
            if not self.fiscal_year_id:
                self.auto_set_fiscal_period()

        super().save(*args, **kwargs)

        if self.pk:
            self.calculate_totals()

    # === توليد الرقم التسلسلي ===
    def generate_number(self):
        """توليد رقم القيد بناءً على التسلسل"""
        from apps.core.models import NumberingSequence
        # ... منطق التوليد

    # === العمليات (Actions) ===
    @transaction.atomic
    def post(self, user=None):
        """ترحيل القيد وتحديث الأرصدة"""
        if self.status == 'posted':
            raise ValidationError(_('القيد مرحل مسبقاً'))

        self.calculate_totals()

        if not self.is_balanced:
            raise ValidationError(_('القيد غير متوازن'))

        self.status = 'posted'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()

        self.update_account_balances()

    @transaction.atomic
    def unpost(self):
        """إلغاء ترحيل القيد"""
        if self.status != 'posted':
            raise ValidationError(_('القيد غير مرحل'))

        self.status = 'draft'
        self.posted_by = None
        self.posted_date = None
        self.save()

        self.update_account_balances()
```

---

### 3.2 نمط السطور (Detail Lines)

```python
class JournalEntryLine(models.Model):
    """سطر القيد اليومي"""

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines',  # ⚡ مهم: للوصول من الأب
        verbose_name=_('القيد')
    )

    line_number = models.PositiveIntegerField(
        _('رقم السطر'),
        default=1
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,  # ⚡ PROTECT لمنع الحذف
        verbose_name=_('الحساب')
    )
    description = models.CharField(
        _('البيان'),
        max_length=255
    )
    debit_amount = models.DecimalField(
        _('مدين'),
        max_digits=15,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)]
    )
    credit_amount = models.DecimalField(
        _('دائن'),
        max_digits=15,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _('سطر قيد يومية')
        verbose_name_plural = _('سطور قيود اليومية')
        ordering = ['line_number']
        unique_together = [['journal_entry', 'line_number']]  # ⚡ ترقيم فريد

    def clean(self):
        """التحقق من صحة السطر"""
        if self.debit_amount and self.credit_amount:
            raise ValidationError(_('لا يمكن إدخال مبلغ في المدين والدائن معاً'))

        if not self.debit_amount and not self.credit_amount:
            raise ValidationError(_('يجب إدخال مبلغ في المدين أو الدائن'))

    def save(self, *args, **kwargs):
        # تعيين رقم السطر تلقائياً
        if not self.line_number:
            max_line = self.journal_entry.lines.aggregate(
                max_line=models.Max('line_number')
            )['max_line']
            self.line_number = (max_line or 0) + 1

        super().save(*args, **kwargs)

        # إعادة حساب إجماليات القيد
        self.journal_entry.calculate_totals()
```

---

### 3.3 نمط الربط مع المحاسبة (Integration)

```python
# من apps/accounting/models/voucher_models.py

class PaymentVoucher(DocumentBaseModel):
    """سند الصرف - مثال للمستند المرتبط بالمحاسبة"""

    # === الحقول الأساسية ===
    number = models.CharField(_('رقم السند'), max_length=50, editable=False)
    date = models.DateField(_('التاريخ'))
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')

    # === بيانات المستفيد ===
    beneficiary_name = models.CharField(_('اسم المستفيد'), max_length=200)
    beneficiary_type = models.CharField(
        _('نوع المستفيد'),
        max_length=20,
        choices=[
            ('supplier', _('مورد')),
            ('employee', _('موظف')),  # ⚡ مهم للرواتب
            ('other', _('أخرى'))
        ]
    )
    beneficiary_id = models.IntegerField(_('معرف المستفيد'), null=True, blank=True)

    # === التفاصيل المالية ===
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=3)
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)

    # === الحسابات ===
    cash_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='payment_vouchers',
        verbose_name=_('حساب الصندوق/البنك')
    )
    expense_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='expense_vouchers',
        verbose_name=_('حساب المصروف'),
        null=True, blank=True
    )

    # === القيد المحاسبي ===
    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    @transaction.atomic
    def post(self, user=None):
        """ترحيل السند وإنشاء القيد المحاسبي"""

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            fiscal_year=fiscal_year,
            period=period,
            entry_date=self.date,
            entry_type='auto',  # ⚡ تلقائي
            description=f"سند صرف رقم {self.number} - {self.description}",
            reference=self.number,
            source_document='payment_voucher',  # ⚡ ربط المصدر
            source_id=self.pk,
            created_by=user or self.created_by
        )

        # إنشاء سطور القيد
        # سطر المصروف (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=expense_account,
            description=f"{self.description} - {self.beneficiary_name}",
            debit_amount=self.amount,
            credit_amount=0,
            currency=self.currency,
        )

        # سطر الصندوق (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=self.cash_account,
            description=f"سند صرف - {self.beneficiary_name}",
            debit_amount=0,
            credit_amount=self.amount,
            currency=self.currency,
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث السند
        self.journal_entry = journal_entry
        self.status = 'posted'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()
```

---

## 4. أنماط Views

### 4.1 نمط ListView مع DataTable Ajax

```python
# apps/accounting/views/journal_views.py

class JournalEntryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة القيود اليومية"""

    model = JournalEntry
    template_name = 'accounting/journal/journal_entry_list.html'
    context_object_name = 'journal_entries'
    permission_required = 'accounting.view_journalentry'  # ⚡ صلاحية Django
    paginate_by = 25

    def get_queryset(self):
        queryset = JournalEntry.objects.filter(
            company=self.request.current_company  # ⚡ من Middleware
        ).select_related(
            'fiscal_year', 'period', 'created_by', 'posted_by'
        ).prefetch_related('lines')

        # الفلترة من GET parameters
        status = self.request.GET.get('status')
        entry_type = self.request.GET.get('entry_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(description__icontains=search) |
                Q(reference__icontains=search)
            )

        return queryset.order_by('-entry_date', '-number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('القيود اليومية'),
            'can_add': self.request.user.has_perm('accounting.add_journalentry'),
            'can_edit': self.request.user.has_perm('accounting.change_journalentry'),
            'can_delete': self.request.user.has_perm('accounting.delete_journalentry'),
            'status_choices': JournalEntry.STATUS_CHOICES,
            'entry_type_choices': JournalEntry.ENTRY_TYPES,
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': ''},
            ]
        })
        return context
```

---

### 4.2 نمط CreateView مع معالجة السطور

```python
class JournalEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إنشاء قيد يومية جديد"""

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journal/journal_entry_form.html'
    permission_required = 'accounting.add_journalentry'
    success_url = reverse_lazy('accounting:journal_entry_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # ⚡ تمرير request للفلترة
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        # تعيين الشركة والفرع
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        # معالجة السطور من JSON
        lines_data = self.request.POST.get('lines_data')
        if lines_data:
            try:
                lines = json.loads(lines_data)
                line_number = 1

                for line_data in lines:
                    account_id = line_data.get('account')
                    if not account_id:
                        continue

                    account = Account.objects.get(
                        id=account_id,
                        company=self.request.current_company
                    )

                    debit = float(line_data.get('debit_amount', 0) or 0)
                    credit = float(line_data.get('credit_amount', 0) or 0)

                    if debit == 0 and credit == 0:
                        continue

                    JournalEntryLine.objects.create(
                        journal_entry=self.object,
                        line_number=line_number,
                        account=account,
                        description=line_data.get('description', self.object.description),
                        debit_amount=debit,
                        credit_amount=credit,
                        currency=account.currency,
                    )
                    line_number += 1

                self.object.calculate_totals()
                messages.success(self.request, f'تم إنشاء القيد {self.object.number} بنجاح')

            except json.JSONDecodeError as e:
                messages.error(self.request, f'خطأ في بيانات السطور: {str(e)}')
                self.object.delete()
                return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إنشاء قيد يومية جديد'),
            'breadcrumbs': [
                {'title': _('المحاسبة'), 'url': reverse('accounting:dashboard')},
                {'title': _('القيود اليومية'), 'url': reverse('accounting:journal_entry_list')},
                {'title': _('إنشاء قيد جديد'), 'url': ''},
            ],
        })
        return context
```

---

### 4.3 نمط UpdateView

```python
class JournalEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل قيد يومية"""

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journal/journal_entry_form.html'
    permission_required = 'accounting.change_journalentry'

    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.current_company)

    @transaction.atomic
    def form_valid(self, form):
        # التحقق من إمكانية التعديل
        if not self.object.can_edit():
            messages.error(self.request, _('لا يمكن تعديل قيد مرحل'))
            return redirect('accounting:journal_entry_detail', pk=self.object.pk)

        self.object = form.save()

        # حذف السطور القديمة وإنشاء الجديدة
        self.object.lines.all().delete()
        # ... نفس منطق CreateView
```

---

### 4.4 نمط Ajax Views

```python
# DataTable Ajax
@login_required
@permission_required_with_message('accounting.view_journalentry')
@require_http_methods(["GET"])
def journal_entry_datatable_ajax(request):
    """Ajax endpoint لجدول القيود"""

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # الفلاتر المخصصة
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    queryset = JournalEntry.objects.filter(
        company=request.current_company
    ).select_related('created_by', 'posted_by')

    # تطبيق الفلاتر
    if status:
        queryset = queryset.filter(status=status)
    if date_from:
        queryset = queryset.filter(entry_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(entry_date__lte=date_to)
    if search_value:
        queryset = queryset.filter(
            Q(number__icontains=search_value) |
            Q(description__icontains=search_value)
        )

    # العد والصفحات
    total_records = JournalEntry.objects.filter(company=request.current_company).count()
    filtered_records = queryset.count()
    queryset = queryset[start:start + length]

    # بناء البيانات
    data = []
    for entry in queryset:
        # بناء badges و actions HTML
        # ...
        data.append([
            entry.number,
            entry.entry_date.strftime('%Y-%m-%d'),
            entry.description[:50],
            f"{entry.total_debit:,.2f}",
            status_badge,
            actions_html
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })


# Autocomplete Ajax
@login_required
def account_autocomplete(request):
    """Autocomplete للحسابات"""

    term = request.GET.get('term', '').strip()

    if len(term) < 2:
        return JsonResponse([], safe=False)

    accounts = Account.objects.filter(
        company=request.current_company,
        is_suspended=False,
        accept_entries=True
    ).filter(
        Q(code__icontains=term) |
        Q(name__icontains=term)
    )[:20]

    results = [{
        'id': account.id,
        'text': f"{account.code} - {account.name}",
        'code': account.code,
        'name': account.name,
    } for account in accounts]

    return JsonResponse(results, safe=False)


# Action Ajax (Post/Unpost)
@login_required
@permission_required_with_message('accounting.change_journalentry')
@require_http_methods(["POST"])
def post_journal_entry(request, pk):
    """ترحيل القيد"""

    try:
        journal_entry = get_object_or_404(
            JournalEntry,
            pk=pk,
            company=request.current_company
        )

        if not journal_entry.can_post():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكن ترحيل هذا القيد'
            })

        journal_entry.post(user=request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم ترحيل القيد {journal_entry.number} بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في ترحيل القيد: {str(e)}'
        })
```

---

## 5. أنماط Forms

### 5.1 BaseForm الأساسي

```python
# apps/core/forms/__init__.py

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة CSS classes تلقائياً
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
```

---

### 5.2 نمط Form مع فلترة الشركة

```python
# apps/accounting/forms/journal_forms.py

class JournalEntryForm(BaseForm):
    """نموذج القيد اليومي"""

    class Meta:
        model = JournalEntry
        fields = [
            'entry_date', 'entry_type', 'description', 'reference',
            'template', 'notes'
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'اكتب بيان القيد هنا...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # ⚡ استلام request
        super().__init__(*args, **kwargs)

        # فلترة حسب الشركة
        if self.request and hasattr(self.request, 'current_company'):
            self.fields['template'].queryset = JournalEntryTemplate.objects.filter(
                company=self.request.current_company,
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('entry_date')

        if entry_date and entry_date > date.today():
            raise ValidationError({
                'entry_date': _('لا يمكن أن يكون تاريخ القيد في المستقبل')
            })

        return cleaned_data
```

---

### 5.3 نمط Form للـ Autocomplete

```python
class QuickJournalEntryForm(forms.Form):
    """نموذج سريع مع حقول Hidden للـ Autocomplete"""

    entry_date = forms.DateField(
        label="التاريخ",
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    description = forms.CharField(
        label="البيان",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
        })
    )

    # ⚡ Hidden field - يملأ من Select2/Autocomplete
    debit_account = forms.IntegerField(
        label="الحساب المدين",
        widget=forms.HiddenInput(attrs={'id': 'id_debit_account'})
    )

    credit_account = forms.IntegerField(
        label="الحساب الدائن",
        widget=forms.HiddenInput(attrs={'id': 'id_credit_account'})
    )

    amount = forms.DecimalField(
        label="المبلغ",
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-end',
            'step': '0.01',
            'min': '0.01',
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        kwargs.pop('instance', None)  # ⚡ إزالة instance للـ Form العادي
        super().__init__(*args, **kwargs)

    def clean_debit_account(self):
        account_id = self.cleaned_data.get('debit_account')
        if not account_id:
            raise forms.ValidationError('يجب اختيار الحساب المدين')

        try:
            account = Account.objects.get(
                id=account_id,
                company=self.request.current_company,
                accept_entries=True,
                is_suspended=False
            )
            return account
        except Account.DoesNotExist:
            raise forms.ValidationError('الحساب المدين غير موجود أو غير صالح')
```

---

## 6. أنماط URLs

```python
# apps/accounting/urls.py

app_name = 'accounting'

urlpatterns = [
    # ========== DASHBOARD ==========
    path('', dashboard.AccountingDashboardView.as_view(), name='dashboard'),

    # Dashboard APIs
    path('api/dashboard-stats/', dashboard.dashboard_stats_api, name='dashboard_stats_api'),

    # ========== CRUD PATTERN ==========
    # List
    path('journal-entries/',
         journal_views.JournalEntryListView.as_view(),
         name='journal_entry_list'),

    # Create
    path('journal-entries/create/',
         journal_views.JournalEntryCreateView.as_view(),
         name='journal_entry_create'),

    # Detail
    path('journal-entries/<int:pk>/',
         journal_views.JournalEntryDetailView.as_view(),
         name='journal_entry_detail'),

    # Update
    path('journal-entries/<int:pk>/update/',
         journal_views.JournalEntryUpdateView.as_view(),
         name='journal_entry_update'),

    # Delete
    path('journal-entries/<int:pk>/delete/',
         journal_views.JournalEntryDeleteView.as_view(),
         name='journal_entry_delete'),

    # ========== AJAX ENDPOINTS ==========
    # DataTables
    path('ajax/journal-entries/',
         journal_views.journal_entry_datatable_ajax,
         name='journal_entry_datatable_ajax'),

    # Autocomplete
    path('ajax/accounts/autocomplete/',
         journal_views.account_autocomplete,
         name='account_autocomplete'),

    # ========== ACTIONS ==========
    path('ajax/journal-entries/<int:pk>/post/',
         journal_views.post_journal_entry,
         name='post_journal_entry'),

    path('ajax/journal-entries/<int:pk>/unpost/',
         journal_views.unpost_journal_entry,
         name='unpost_journal_entry'),

    # ========== EXPORT ==========
    path('journal-entries/export/',
         report_views.export_journal_entries,
         name='export_journal_entries'),
]
```

---

## 7. Mixins المستخدمة

### 7.1 CompanyMixin

```python
# apps/core/mixins.py

class CompanyMixin:
    """فلترة حسب الشركة"""

    @property
    def current_company(self):
        user = self.request.user
        if hasattr(user, 'company') and user.company:
            return user.company
        else:
            from .models import Company
            return Company.objects.first()

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'company'):
            return queryset.filter(company=self.current_company)
        return queryset

    def form_valid(self, form):
        if hasattr(form._meta.model, 'company') and not getattr(form.instance, 'company', None):
            form.instance.company = self.current_company
        return super().form_valid(form)
```

---

### 7.2 AuditLogMixin

```python
class AuditLogMixin:
    """تسجيل العمليات تلقائياً"""

    def form_valid(self, form):
        # حفظ القيم القديمة
        if self.object and self.object.pk:
            old_values = {field.name: getattr(self.object, field.name)
                         for field in self.object._meta.fields}
            action = 'UPDATE'
        else:
            old_values = None
            action = 'CREATE'

        response = super().form_valid(form)

        # حفظ القيم الجديدة وتسجيل العملية
        new_values = {field.name: getattr(self.object, field.name)
                     for field in self.object._meta.fields}

        self.log_action(action, self.object, old_values, new_values)

        return response
```

---

## 8. نمط Template List

```html
<!-- apps/accounting/templates/accounting/vouchers/payment_voucher_list.html -->
{% extends 'base/base.html' %}
{% load i18n static %}

{% block title %}{{ title }}{% endblock %}

{% block extra_css %}
<!-- DataTables CSS -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css">
<!-- Select2 CSS للفلاتر -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb">
            {% for breadcrumb in breadcrumbs %}
                {% if forloop.last %}
                    <li class="breadcrumb-item active">{{ breadcrumb.title }}</li>
                {% else %}
                    <li class="breadcrumb-item">
                        <a href="{{ breadcrumb.url }}">{{ breadcrumb.title }}</a>
                    </li>
                {% endif %}
            {% endfor %}
        </ol>
    </nav>

    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h3 mb-1">{{ title }}</h1>
            <p class="text-muted mb-0">{% trans "وصف الصفحة" %}</p>
        </div>
        {% if can_add %}
        <a href="{% url 'accounting:payment_voucher_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> {% trans "إضافة جديد" %}
        </a>
        {% endif %}
    </div>

    <!-- Stats Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h6>{% trans "الإجمالي" %}</h6>
                    <h2>{{ stats.total|default:0 }}</h2>
                </div>
            </div>
        </div>
        <!-- ... المزيد من الإحصائيات -->
    </div>

    <!-- Filters Card -->
    <div class="card mb-4">
        <div class="card-header">
            <i class="fas fa-filter"></i> {% trans "البحث والفلترة" %}
        </div>
        <div class="card-body">
            <div class="row g-3">
                <div class="col-md-2">
                    <select class="form-select" id="statusFilter">
                        <option value="">{% trans "جميع الحالات" %}</option>
                        <option value="draft">{% trans "مسودة" %}</option>
                        <option value="posted">{% trans "مرحل" %}</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <input type="date" class="form-control" id="dateFromFilter">
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control" id="searchFilter"
                           placeholder="{% trans 'بحث...' %}">
                </div>
                <div class="col-md-1">
                    <button class="btn btn-outline-secondary" id="clearFilters">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- DataTable -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover" id="dataTable">
                <thead class="table-dark">
                    <tr>
                        <th>{% trans "الرقم" %}</th>
                        <th>{% trans "التاريخ" %}</th>
                        <th>{% trans "المبلغ" %}</th>
                        <th>{% trans "الحالة" %}</th>
                        <th>{% trans "الإجراءات" %}</th>
                    </tr>
                </thead>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<script>
$(document).ready(function() {
    // Initialize DataTable
    var table = $('#dataTable').DataTable({
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "{% url 'accounting:payment_voucher_datatable_ajax' %}",
            "type": "GET",
            "data": function(d) {
                d.status = $('#statusFilter').val();
                d.date_from = $('#dateFromFilter').val();
                d.search_filter = $('#searchFilter').val();
            }
        },
        "columns": [
            {"data": 0},
            {"data": 1},
            {"data": 2, "className": "text-end"},
            {"data": 3, "className": "text-center"},
            {"data": 4, "orderable": false}
        ],
        "language": {
            "url": "https://cdn.datatables.net/plug-ins/1.13.7/i18n/ar.json"
        }
    });

    // Filter Events
    $('#statusFilter, #dateFromFilter').on('change', function() {
        table.ajax.reload();
    });

    $('#searchFilter').on('keyup', function() {
        clearTimeout(window.searchTimeout);
        window.searchTimeout = setTimeout(function() {
            table.ajax.reload();
        }, 500);
    });

    $('#clearFilters').on('click', function() {
        $('#statusFilter').val('');
        $('#dateFromFilter, #searchFilter').val('');
        table.ajax.reload();
    });

    // Action Functions
    window.postItem = function(id) {
        Swal.fire({
            title: 'تأكيد الترحيل',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'نعم',
            cancelButtonText: 'إلغاء'
        }).then((result) => {
            if (result.isConfirmed) {
                $.post('{% url "accounting:post_payment_voucher" 0 %}'.replace('0', id), {
                    'csrfmiddlewaretoken': '{{ csrf_token }}'
                }).done(function(data) {
                    if (data.success) {
                        Swal.fire('تم!', data.message, 'success');
                        table.ajax.reload();
                    } else {
                        Swal.fire('خطأ!', data.message, 'error');
                    }
                });
            }
        });
    };
});
</script>
{% endblock %}
```

---

## 9. نمط Template Form

```html
<!-- apps/accounting/templates/accounting/vouchers/payment_voucher_form.html -->
{% extends 'base/base.html' %}
{% load i18n static widget_tweaks %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-3">...</nav>

    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3">{{ title }}</h1>
        <a href="{% url 'accounting:payment_voucher_list' %}" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-right"></i> {% trans "العودة" %}
        </a>
    </div>

    <div class="row">
        <!-- Form Section (8 columns) -->
        <div class="col-lg-8">
            <div class="card">
                <div class="card-body">
                    <form method="post" novalidate id="mainForm">
                        {% csrf_token %}

                        <!-- Section: المعلومات الأساسية -->
                        <div class="mb-4">
                            <h6 class="text-primary border-bottom pb-2">
                                <i class="fas fa-info-circle"></i> المعلومات الأساسية
                            </h6>
                            <div class="row g-3">
                                <div class="col-md-4">
                                    <label class="form-label required-field">{{ form.date.label }}</label>
                                    {{ form.date|add_class:"form-control" }}
                                    {% if form.date.errors %}
                                        <div class="text-danger small">{{ form.date.errors.0 }}</div>
                                    {% endif %}
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label required-field">{{ form.amount.label }}</label>
                                    {{ form.amount|add_class:"form-control text-end" }}
                                </div>
                            </div>
                        </div>

                        <!-- Section: الحسابات (with Select2) -->
                        <div class="mb-4">
                            <h6 class="text-primary border-bottom pb-2">
                                <i class="fas fa-sitemap"></i> الحسابات
                            </h6>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label">{{ form.cash_account.label }}</label>
                                    {{ form.cash_account|add_class:"form-select account-select" }}
                                </div>
                            </div>
                        </div>

                        <!-- Form Actions -->
                        <div class="d-flex justify-content-between pt-3 border-top">
                            <a href="{% url 'accounting:payment_voucher_list' %}" class="btn btn-light">
                                إلغاء
                            </a>
                            <button type="submit" class="btn btn-primary" id="submitBtn">
                                <i class="fas fa-save"></i> حفظ
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Sidebar (4 columns) -->
        <div class="col-lg-4">
            <!-- Help Card -->
            <div class="card mb-3" style="border-left: 4px solid #0d6efd;">
                <div class="card-body">
                    <h6><i class="fas fa-lightbulb"></i> معلومات مهمة</h6>
                    <ul class="small mb-0">
                        <li>نقطة 1</li>
                        <li>نقطة 2</li>
                    </ul>
                </div>
            </div>

            <!-- Stats Card (for edit) -->
            {% if object %}
            <div class="card">
                <div class="card-header">معلومات السجل</div>
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <span>الرقم:</span>
                        <span class="badge bg-primary">{{ object.number }}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>الحالة:</span>
                        {% if object.status == 'draft' %}
                            <span class="badge bg-warning">مسودة</span>
                        {% elif object.status == 'posted' %}
                            <span class="badge bg-success">مرحل</span>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    // Select2 for account fields
    $('.account-select').select2({
        theme: 'bootstrap-5',
        dir: "rtl",
        placeholder: 'ابحث عن الحساب...',
        minimumInputLength: 1,
        ajax: {
            url: '{% url "accounting:account_autocomplete" %}',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    term: params.term,
                    only_leaf: '1',
                    only_active: '1'
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(item) {
                        return { id: item.id, text: item.text };
                    })
                };
            }
        }
    });

    // Form submission with loading state
    $('#mainForm').on('submit', function() {
        $('#submitBtn').prop('disabled', true).html(
            '<i class="fas fa-spinner fa-spin"></i> جاري الحفظ...'
        );
    });
});
</script>
{% endblock %}
```

---

## 10. بنية HR المقترحة

### 10.1 هيكل الملفات

```
apps/hr/
├── __init__.py
├── apps.py
├── admin.py
├── urls.py
├── models/
│   ├── __init__.py
│   ├── employee_models.py       # Employee, EmployeeDocument
│   ├── organization_models.py   # Department, JobTitle, JobGrade
│   ├── attendance_models.py     # AttendanceRecord, WorkShift
│   ├── leave_models.py          # LeaveType, LeaveRequest, LeaveBalance
│   ├── payroll_models.py        # SalaryStructure, PayrollRun, Payslip
│   └── evaluation_models.py     # PerformanceReview, KPI
├── views/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── employee_views.py
│   ├── attendance_views.py
│   ├── leave_views.py
│   ├── payroll_views.py
│   └── ajax_views.py
├── forms/
│   ├── __init__.py
│   ├── employee_forms.py
│   ├── attendance_forms.py
│   ├── leave_forms.py
│   └── payroll_forms.py
├── templates/hr/
│   ├── dashboard.html
│   ├── employees/
│   │   ├── employee_list.html
│   │   ├── employee_form.html
│   │   └── employee_detail.html
│   ├── attendance/
│   ├── leaves/
│   └── payroll/
└── templatetags/
    └── hr_tags.py
```

---

### 10.2 النماذج المقترحة

```python
# apps/hr/models/employee_models.py

class Employee(BaseModel):
    """نموذج الموظف"""

    GENDER_CHOICES = [
        ('male', _('ذكر')),
        ('female', _('أنثى')),
    ]

    MARITAL_STATUS = [
        ('single', _('أعزب')),
        ('married', _('متزوج')),
        ('divorced', _('مطلق')),
        ('widowed', _('أرمل')),
    ]

    EMPLOYMENT_STATUS = [
        ('active', _('نشط')),
        ('on_leave', _('في إجازة')),
        ('suspended', _('موقوف')),
        ('terminated', _('منتهي الخدمة')),
    ]

    # رقم الموظف
    employee_number = models.CharField(
        _('رقم الموظف'),
        max_length=20,
        editable=False
    )

    # ربط بالمستخدم (اختياري)
    user = models.OneToOneField(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employee_profile',
        verbose_name=_('حساب المستخدم')
    )

    # البيانات الشخصية
    first_name = models.CharField(_('الاسم الأول'), max_length=50)
    middle_name = models.CharField(_('اسم الأب'), max_length=50, blank=True)
    last_name = models.CharField(_('اسم العائلة'), max_length=50)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=150, blank=True)

    national_id = models.CharField(_('رقم الهوية'), max_length=20, unique=True)
    date_of_birth = models.DateField(_('تاريخ الميلاد'))
    gender = models.CharField(_('الجنس'), max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(
        _('الحالة الاجتماعية'),
        max_length=20,
        choices=MARITAL_STATUS,
        default='single'
    )

    # معلومات الاتصال
    email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    phone = models.CharField(_('الهاتف'), max_length=20)
    mobile = models.CharField(_('الجوال'), max_length=20, blank=True)
    address = models.TextField(_('العنوان'), blank=True)

    # البيانات الوظيفية
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('القسم')
    )
    job_title = models.ForeignKey(
        'JobTitle',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('المسمى الوظيفي')
    )
    job_grade = models.ForeignKey(
        'JobGrade',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('الدرجة الوظيفية')
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subordinates',
        verbose_name=_('المدير المباشر')
    )

    # تواريخ العمل
    hire_date = models.DateField(_('تاريخ التعيين'))
    contract_end_date = models.DateField(_('تاريخ انتهاء العقد'), null=True, blank=True)
    termination_date = models.DateField(_('تاريخ إنهاء الخدمة'), null=True, blank=True)

    # الراتب
    basic_salary = models.DecimalField(
        _('الراتب الأساسي'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    currency = models.ForeignKey(
        'core.Currency',
        on_delete=models.PROTECT,
        verbose_name=_('العملة')
    )

    # البنك
    bank_name = models.CharField(_('اسم البنك'), max_length=100, blank=True)
    bank_account = models.CharField(_('رقم الحساب البنكي'), max_length=50, blank=True)
    iban = models.CharField(_('رقم IBAN'), max_length=50, blank=True)

    # الحالة
    employment_status = models.CharField(
        _('حالة التوظيف'),
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='active'
    )

    # الصورة
    photo = models.ImageField(
        _('الصورة الشخصية'),
        upload_to='employees/photos/',
        blank=True
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('موظف')
        verbose_name_plural = _('الموظفين')
        unique_together = [['company', 'employee_number']]
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['employee_number']),
            models.Index(fields=['national_id']),
            models.Index(fields=['department', 'employment_status']),
        ]

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def years_of_service(self):
        from datetime import date
        end_date = self.termination_date or date.today()
        delta = end_date - self.hire_date
        return delta.days / 365.25

    def save(self, *args, **kwargs):
        if not self.employee_number:
            self.employee_number = self.generate_employee_number()
        super().save(*args, **kwargs)

    def generate_employee_number(self):
        from apps.core.models import NumberingSequence
        try:
            sequence = NumberingSequence.objects.get(
                company=self.company,
                document_type='employee'
            )
            return sequence.get_next_number()
        except NumberingSequence.DoesNotExist:
            # Fallback
            last = Employee.objects.filter(company=self.company).order_by('-id').first()
            num = (last.id + 1) if last else 1
            return f"EMP{num:06d}"

    def __str__(self):
        return f"{self.employee_number} - {self.full_name}"


class Department(BaseModel):
    """الأقسام"""

    code = models.CharField(_('رمز القسم'), max_length=20)
    name = models.CharField(_('اسم القسم'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('القسم الأب')
    )

    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managed_departments',
        verbose_name=_('مدير القسم')
    )

    # ربط بمركز التكلفة
    cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('مركز التكلفة')
    )

    level = models.PositiveSmallIntegerField(_('المستوى'), default=1)

    class Meta:
        verbose_name = _('قسم')
        verbose_name_plural = _('الأقسام')
        unique_together = [['company', 'code']]
        ordering = ['code']

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class JobTitle(BaseModel):
    """المسميات الوظيفية"""

    code = models.CharField(_('الرمز'), max_length=20)
    name = models.CharField(_('المسمى الوظيفي'), max_length=100)
    name_en = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    description = models.TextField(_('الوصف الوظيفي'), blank=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='job_titles',
        verbose_name=_('القسم'),
        null=True, blank=True
    )

    min_salary = models.DecimalField(
        _('الحد الأدنى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True, blank=True
    )
    max_salary = models.DecimalField(
        _('الحد الأعلى للراتب'),
        max_digits=10,
        decimal_places=2,
        null=True, blank=True
    )

    class Meta:
        verbose_name = _('مسمى وظيفي')
        verbose_name_plural = _('المسميات الوظيفية')
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name
```

---

### 10.3 مثال على تكامل الرواتب مع المحاسبة

```python
# apps/hr/models/payroll_models.py

class PayrollRun(DocumentBaseModel):
    """مسير الرواتب"""

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('calculated', _('محسوب')),
        ('approved', _('معتمد')),
        ('posted', _('مرحل')),
        ('paid', _('مدفوع')),
    ]

    number = models.CharField(_('رقم المسير'), max_length=50, editable=False)
    period_month = models.PositiveSmallIntegerField(_('الشهر'))
    period_year = models.PositiveSmallIntegerField(_('السنة'))

    status = models.CharField(
        _('الحالة'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # الإجماليات
    total_gross = models.DecimalField(
        _('إجمالي الرواتب'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_deductions = models.DecimalField(
        _('إجمالي الخصومات'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_net = models.DecimalField(
        _('صافي الرواتب'),
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # ربط القيد المحاسبي
    journal_entry = models.OneToOneField(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('القيد المحاسبي')
    )

    # ربط سند الصرف
    payment_voucher = models.OneToOneField(
        'accounting.PaymentVoucher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('سند الصرف')
    )

    posted_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posted_payroll_runs'
    )
    posted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('مسير رواتب')
        verbose_name_plural = _('مسيرات الرواتب')
        unique_together = [['company', 'number'], ['company', 'period_month', 'period_year']]

    @transaction.atomic
    def post_to_accounting(self, user=None):
        """ترحيل الرواتب للمحاسبة"""
        from apps.accounting.models import JournalEntry, JournalEntryLine, Account

        # البحث عن الحسابات
        salary_expense_account = Account.objects.get(
            company=self.company,
            code='510100'  # مصروف الرواتب
        )
        salary_payable_account = Account.objects.get(
            company=self.company,
            code='210200'  # رواتب مستحقة
        )

        # إنشاء القيد المحاسبي
        journal_entry = JournalEntry.objects.create(
            company=self.company,
            branch=self.branch,
            entry_date=date(self.period_year, self.period_month, 28),
            entry_type='auto',
            description=f"رواتب شهر {self.period_month}/{self.period_year}",
            reference=self.number,
            source_document='payroll_run',
            source_id=self.pk,
            created_by=user
        )

        # سطر المصروف (مدين)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=1,
            account=salary_expense_account,
            description=f"رواتب الموظفين - {self.period_month}/{self.period_year}",
            debit_amount=self.total_gross,
            credit_amount=0,
            currency=self.company.base_currency,
        )

        # سطر المستحقات (دائن)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            line_number=2,
            account=salary_payable_account,
            description=f"رواتب مستحقة - {self.period_month}/{self.period_year}",
            debit_amount=0,
            credit_amount=self.total_net,
            currency=self.company.base_currency,
        )

        # ترحيل القيد
        journal_entry.post(user=user)

        # تحديث المسير
        self.journal_entry = journal_entry
        self.status = 'posted'
        self.posted_by = user
        self.posted_date = timezone.now()
        self.save()
```

---

## 11. ملخص القواعد والأنماط

### 11.1 قواعد النماذج
- ✅ استخدم `BaseModel` للبيانات الأساسية
- ✅ استخدم `DocumentBaseModel` للمستندات
- ✅ أضف `unique_together = [['company', 'field']]` للحقول الفريدة
- ✅ استخدم `PROTECT` للعلاقات المهمة
- ✅ أضف `indexes` للحقول المستخدمة في البحث
- ✅ أنشئ دوال `can_edit()`, `can_post()`, `can_delete()`

### 11.2 قواعد Views
- ✅ استخدم `LoginRequiredMixin` و `PermissionRequiredMixin`
- ✅ استخدم `CompanyMixin` للفلترة التلقائية
- ✅ استخدم `AuditLogMixin` للتسجيل
- ✅ مرر `request` للـ Forms
- ✅ استخدم `transaction.atomic` للعمليات المعقدة

### 11.3 قواعد Forms
- ✅ فلتر الـ querysets حسب `request.current_company`
- ✅ استخدم `widget_tweaks` للـ CSS classes
- ✅ أضف validation في `clean()` methods

### 11.4 قواعد Templates
- ✅ استخدم DataTables مع Server-side processing
- ✅ استخدم Select2 للـ autocomplete
- ✅ أضف Breadcrumbs
- ✅ أضف Stats Cards
- ✅ أضف Sidebar للمعلومات والمساعدة

### 11.5 قواعد URLs
- ✅ استخدم `app_name` للـ namespace
- ✅ اتبع نمط CRUD: `list`, `create`, `<pk>/`, `<pk>/update/`, `<pk>/delete/`
- ✅ ضع Ajax endpoints تحت `ajax/`
- ✅ ضع Actions تحت `ajax/.../action/`

---

## 12. أوامر مفيدة

```bash
# إنشاء migrations
python manage.py makemigrations hr

# تطبيق migrations
python manage.py migrate

# إنشاء superuser
python manage.py createsuperuser

# تشغيل السيرفر
python manage.py runserver

# Django shell
python manage.py shell
```

---

> **ملاحظة:** هذا الملف يُستخدم كمرجع لـ Claude Code لضمان التناسق في بناء نظام HR مع باقي النظام.

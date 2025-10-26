# خطة إعادة بناء Assets Views
## بناءً على أسلوب Accounting Module

---

## 🎯 الهدف الرئيسي
إعادة بناء `apps/assets/views/` بحيث يكون:
1. **متكامل محاسبياً** - إنشاء قيود تلقائية لكل عملية
2. **متناسق مع Accounting Views** - نفس البنية والأسلوب
3. **يستخدم Core Models بشكل صحيح** - Company, Branch, User, NumberingSequence
4. **منظم وقابل للصيانة** - كود نظيف ومقروء

---

## 📋 المبادئ الأساسية المستخرجة من Accounting Module

### 1. هيكلة الملفات
```
apps/assets/views/
├── __init__.py                    # تصدير كل الـ views
├── dashboard.py                   # لوحة التحكم + إحصائيات
├── asset_views.py                 # CRUD الأصول الأساسية
├── category_views.py              # إدارة الفئات
├── transaction_views.py           # العمليات (شراء، بيع، استبعاد، تحويل)
├── depreciation_views.py          # الإهلاك
├── maintenance_views.py           # الصيانة
├── insurance_views.py             # التأمين
├── lease_views.py                 # الإيجار
├── physical_count_views.py        # الجرد الفعلي
├── valuation_views.py             # إعادة التقييم
├── workflow_views.py              # الموافقات
├── report_views.py                # التقارير
└── api_views.py                   # API endpoints
```

### 2. النمط الموحد لكل Model
```python
# مثال: asset_views.py
class AssetListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView)
class AssetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView)
class AssetDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView)
class AssetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView)
class AssetDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView)
```

### 3. القواعد الإلزامية في كل View

#### أ) List Views
```python
def get_queryset(self):
    queryset = Asset.objects.filter(
        company=self.request.current_company
    ).select_related(...).prefetch_related(...)

    # فلترة متقدمة من GET parameters
    status = self.request.GET.get('status')
    category = self.request.GET.get('category')
    date_from = self.request.GET.get('date_from')
    date_to = self.request.GET.get('date_to')
    search = self.request.GET.get('search')

    # تطبيق الفلاتر...
    return queryset.order_by('-created_at')

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
        'title': _('...'),
        'can_add': self.request.user.has_perm('...'),
        'can_edit': self.request.user.has_perm('...'),
        'can_delete': self.request.user.has_perm('...'),
        'breadcrumbs': [...],
        'stats': {...}  # إحصائيات سريعة
    })
    return context
```

#### ب) Create Views
```python
def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    kwargs['request'] = self.request  # تمرير request للـ form
    return kwargs

def form_valid(self, form):
    form.instance.company = self.request.current_company
    form.instance.branch = self.request.current_branch
    form.instance.created_by = self.request.user
    response = super().form_valid(form)
    messages.success(self.request, f'تم الإنشاء بنجاح')
    return response

def get_success_url(self):
    return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})
```

#### ج) Update Views
```python
def get_queryset(self):
    return Asset.objects.filter(company=self.request.current_company)

def form_valid(self, form):
    # التحقق من إمكانية التعديل
    if not self.object.can_edit():
        messages.error(self.request, _('لا يمكن التعديل'))
        return redirect('assets:asset_detail', pk=self.object.pk)

    response = super().form_valid(form)
    messages.success(self.request, f'تم التحديث بنجاح')
    return response
```

#### د) Delete Views
```python
def delete(self, request, *args, **kwargs):
    self.object = self.get_object()

    if not self.object.can_delete():
        messages.error(request, _('لا يمكن الحذف'))
        return redirect('assets:asset_detail', pk=self.object.pk)

    object_name = str(self.object)
    messages.success(request, f'تم حذف {object_name} بنجاح')
    return super().delete(request, *args, **kwargs)
```

---

## 🔥 التكامل المحاسبي - النقطة الأهم

### المبدأ: القيود تُنشأ في الـ Models وليس الـ Views

#### 1. إضافة Methods في Models
```python
# في apps/assets/models/asset_models.py (class Asset)

def create_purchase_journal_entry(self):
    """إنشاء قيد شراء الأصل"""
    from apps.accounting.models import JournalEntry, JournalEntryLine

    # التحقق من الإعدادات المحاسبية
    if not self.category.asset_account:
        raise ValidationError('لم يتم تحديد حساب الأصول للفئة')

    # إنشاء القيد
    journal_entry = JournalEntry.objects.create(
        company=self.company,
        branch=self.branch,
        entry_date=self.purchase_date,
        entry_type='asset_purchase',
        description=f'شراء أصل ثابت: {self.name}',
        reference=self.asset_number,
        source_model='asset',
        source_id=self.id,
        status='draft'
    )

    # سطور القيد
    # مدين: حساب الأصول
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=1,
        account=self.category.asset_account,
        description=f'شراء {self.name}',
        debit_amount=self.purchase_price,
        credit_amount=0,
        currency=self.currency
    )

    # دائن: حساب الموردين أو النقدية
    payment_account = self.get_payment_account()
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=2,
        account=payment_account,
        description=f'دفع ثمن {self.name}',
        debit_amount=0,
        credit_amount=self.purchase_price,
        currency=self.currency
    )

    journal_entry.calculate_totals()

    # حفظ رابط القيد
    self.purchase_journal_entry = journal_entry
    self.save(update_fields=['purchase_journal_entry'])

    return journal_entry
```

#### 2. Methods أخرى مطلوبة في Asset Model
```python
def create_sale_journal_entry(self, sale_price, sale_date):
    """قيد بيع الأصل (مع حساب الربح/الخسارة)"""
    pass

def create_disposal_journal_entry(self, disposal_reason):
    """قيد استبعاد الأصل (خسارة كاملة)"""
    pass

def create_transfer_journal_entry(self, to_branch, to_cost_center):
    """قيد تحويل الأصل (إن لزم)"""
    pass
```

#### 3. Methods في AssetDepreciation Model
```python
# في apps/assets/models/asset_models.py (class AssetDepreciation)

def create_depreciation_journal_entry(self):
    """إنشاء قيد الإهلاك"""
    journal_entry = JournalEntry.objects.create(
        company=self.asset.company,
        branch=self.asset.branch,
        entry_date=self.depreciation_date,
        entry_type='depreciation',
        description=f'إهلاك {self.asset.name} - {self.period_year}/{self.period_month}',
        reference=self.asset.asset_number,
        source_model='assetdepreciation',
        source_id=self.id,
        status='draft'
    )

    # مدين: مصروف الإهلاك
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=1,
        account=self.asset.category.depreciation_expense_account,
        description=f'مصروف إهلاك {self.asset.name}',
        debit_amount=self.depreciation_amount,
        credit_amount=0,
        cost_center=self.asset.cost_center
    )

    # دائن: مجمع الإهلاك
    JournalEntryLine.objects.create(
        journal_entry=journal_entry,
        line_number=2,
        account=self.asset.category.accumulated_depreciation_account,
        description=f'مجمع إهلاك {self.asset.name}',
        debit_amount=0,
        credit_amount=self.depreciation_amount
    )

    journal_entry.calculate_totals()
    self.journal_entry = journal_entry
    self.save(update_fields=['journal_entry'])

    return journal_entry
```

#### 4. Methods في AssetMaintenance Model
```python
def create_maintenance_journal_entry(self):
    """إنشاء قيد الصيانة"""

    if self.maintenance_type == 'preventive':
        # صيانة وقائية = مصروف
        expense_account = self.asset.category.maintenance_expense_account
    else:
        # صيانة تحسينية = إضافة لقيمة الأصل
        expense_account = self.asset.category.asset_account

    # إنشاء القيد...
```

#### 5. Methods في AssetTransaction Model
```python
def create_transaction_journal_entry(self):
    """إنشاء قيد حسب نوع العملية"""

    if self.transaction_type == 'purchase':
        return self.asset.create_purchase_journal_entry()
    elif self.transaction_type == 'sale':
        return self.create_sale_entry()
    elif self.transaction_type == 'disposal':
        return self.create_disposal_entry()
    # ... إلخ
```

---

## 📝 خطة التنفيذ خطوة بخطوة

### Phase 1: تجهيز Models (الأهم)
**الهدف**: إضافة جميع الـ methods المحاسبية في Models

#### الملفات المطلوب تعديلها:
1. **apps/assets/models/asset_models.py**
   - [ ] `Asset.create_purchase_journal_entry()`
   - [ ] `Asset.create_sale_journal_entry(sale_price, sale_date)`
   - [ ] `Asset.create_disposal_journal_entry(disposal_reason)`
   - [ ] `Asset.create_transfer_journal_entry(to_branch, to_cost_center)`
   - [ ] `Asset.can_edit()` - قواعد التعديل
   - [ ] `Asset.can_delete()` - قواعد الحذف
   - [ ] `Asset.get_payment_account()` - حساب الدفع (مورد أو نقدية)
   - [ ] `AssetDepreciation.create_depreciation_journal_entry()`
   - [ ] `AssetDepreciation.post()` - ترحيل الإهلاك
   - [ ] `AssetDepreciation.unpost()` - إلغاء الترحيل

2. **apps/assets/models/transaction_models.py**
   - [ ] `AssetTransaction.create_journal_entry()`
   - [ ] `AssetTransaction.post()` - اعتماد العملية
   - [ ] `AssetTransaction.unpost()` - إلغاء الاعتماد
   - [ ] `AssetTransaction.can_edit()`
   - [ ] `AssetTransaction.can_delete()`
   - [ ] `AssetTransfer.create_transfer_entry()`

3. **apps/assets/models/maintenance_models.py**
   - [ ] `AssetMaintenance.create_journal_entry()`
   - [ ] `AssetMaintenance.complete()` - إتمام الصيانة
   - [ ] `AssetMaintenance.post()` - ترحيل محاسبياً

4. **apps/assets/models/insurance_models.py**
   - [ ] `AssetInsurance.create_payment_entry()` - قيد دفع قسط التأمين
   - [ ] `InsuranceClaim.create_claim_entry()` - قيد التعويض

5. **apps/assets/models/physical_count_models.py**
   - [ ] `PhysicalCountAdjustment.create_adjustment_entry()` - قيد الفروقات

---

### Phase 2: إعادة بناء Views الأساسية

#### 1. Dashboard (dashboard.py) ✅ موجود
- [ ] مراجعة وتحسين الإحصائيات
- [ ] إضافة Quick Actions
- [ ] إضافة Recent Activities
- [ ] إضافة Charts/Graphs

#### 2. Asset CRUD (asset_views.py)
**الحالة**: موجود لكن يحتاج تعديل

**التعديلات المطلوبة**:
```python
class AssetCreateView:
    @transaction.atomic
    def form_valid(self, form):
        # حفظ الأصل
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'active'

        self.object = form.save()

        # ✅ إنشاء القيد المحاسبي
        if self.request.POST.get('create_journal_entry') == 'on':
            try:
                journal_entry = self.object.create_purchase_journal_entry()
                messages.success(
                    self.request,
                    f'تم إنشاء الأصل والقيد المحاسبي {journal_entry.number}'
                )
            except ValidationError as e:
                messages.warning(
                    self.request,
                    f'تم إنشاء الأصل لكن فشل القيد: {str(e)}'
                )
        else:
            messages.success(self.request, f'تم إنشاء الأصل {self.object.asset_number}')

        return redirect(self.get_success_url())
```

#### 3. Category Views (category_views.py) - جديد
```python
class AssetCategoryListView(...)
class AssetCategoryCreateView(...)
class AssetCategoryUpdateView(...)
class AssetCategoryDetailView(...)
class AssetCategoryDeleteView(...)

# AJAX
@login_required
def category_hierarchy_ajax(request):
    """شجرة الفئات الهرمية"""
    pass

@login_required
def category_accounts_ajax(request, pk):
    """عرض الحسابات المرتبطة بالفئة"""
    pass
```

#### 4. Transaction Views (transaction_views.py)
**الحالة**: موجود لكن لا ينشئ قيود

**التعديلات الجذرية**:
```python
class AssetTransactionCreateView:
    @transaction.atomic
    def form_valid(self, form):
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'

        self.object = form.save()

        # ✅ إنشاء القيد حسب نوع العملية
        try:
            journal_entry = self.object.create_journal_entry()
            messages.success(
                self.request,
                f'تم إنشاء العملية {self.object.transaction_number} والقيد {journal_entry.number}'
            )
        except ValidationError as e:
            # رجوع عن العملية
            raise

        return redirect(self.get_success_url())

# إضافة AJAX Actions
@login_required
@require_http_methods(['POST'])
def post_transaction(request, pk):
    """اعتماد العملية وترحيل القيد"""
    transaction_obj = get_object_or_404(
        AssetTransaction,
        pk=pk,
        company=request.current_company
    )

    if not transaction_obj.can_post():
        return JsonResponse({'success': False, 'error': 'لا يمكن الاعتماد'})

    try:
        with transaction.atomic():
            transaction_obj.post()
            if transaction_obj.journal_entry:
                transaction_obj.journal_entry.post(request.user)

        return JsonResponse({
            'success': True,
            'message': f'تم اعتماد العملية {transaction_obj.transaction_number}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
```

#### 5. Depreciation Views (depreciation_views.py)
**أهم التعديلات**:
```python
@login_required
@permission_required('assets.add_assetdepreciation')
def calculate_monthly_depreciation(request):
    """حساب الإهلاك الشهري لجميع الأصول"""

    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        create_entries = request.POST.get('create_journal_entries') == 'on'

        # جلب الأصول النشطة
        assets = Asset.objects.filter(
            company=request.current_company,
            status='active',
            depreciation_method__isnull=False
        )

        created_count = 0
        with transaction.atomic():
            for asset in assets:
                # حساب الإهلاك
                depreciation = asset.calculate_monthly_depreciation(year, month)

                if depreciation and create_entries:
                    # ✅ إنشاء القيد المحاسبي
                    depreciation.create_depreciation_journal_entry()
                    depreciation.journal_entry.post(request.user)

                created_count += 1

        messages.success(
            request,
            f'تم حساب الإهلاك لـ {created_count} أصل وإنشاء القيود المحاسبية'
        )
        return redirect('assets:depreciation_list')
```

#### 6. Maintenance Views (maintenance_views.py)
```python
class AssetMaintenanceCreateView:
    @transaction.atomic
    def form_valid(self, form):
        # حفظ الصيانة
        form.instance.company = self.request.current_company
        form.instance.branch = self.request.current_branch
        form.instance.created_by = self.request.user
        form.instance.status = 'scheduled'

        self.object = form.save()
        messages.success(self.request, 'تم جدولة الصيانة')
        return redirect(self.get_success_url())

@login_required
@require_http_methods(['POST'])
def complete_maintenance(request, pk):
    """إتمام الصيانة وإنشاء القيد"""
    maintenance = get_object_or_404(
        AssetMaintenance,
        pk=pk,
        company=request.current_company
    )

    actual_cost = Decimal(request.POST.get('actual_cost', 0))

    with transaction.atomic():
        maintenance.actual_cost = actual_cost
        maintenance.actual_end_date = timezone.now().date()
        maintenance.status = 'completed'
        maintenance.save()

        # ✅ إنشاء القيد المحاسبي
        journal_entry = maintenance.create_journal_entry()
        journal_entry.post(request.user)

    return JsonResponse({
        'success': True,
        'journal_entry': journal_entry.number
    })
```

#### 7. Insurance Views (insurance_views.py)
```python
class AssetInsuranceCreateView:
    """تسجيل بوليصة تأمين جديدة"""
    # عند الحفظ، إنشاء قيد دفع قسط التأمين الأول
    pass

class InsuranceClaimCreateView:
    """تسجيل مطالبة تأمين"""
    @transaction.atomic
    def form_valid(self, form):
        # حفظ المطالبة
        self.object = form.save()

        # إنشاء قيد استلام التعويض (إن وُجد)
        if self.object.approved_amount > 0:
            journal_entry = self.object.create_claim_entry()

        return redirect(self.get_success_url())
```

#### 8. Physical Count Views (physical_count_views.py)
```python
class PhysicalCountCompleteView:
    """إتمام الجرد وإنشاء قيود التسوية"""

    @transaction.atomic
    def post(self, request, pk):
        count = get_object_or_404(PhysicalCount, pk=pk)

        # مقارنة الفعلي مع الدفتري
        adjustments = []
        for line in count.lines.all():
            if line.actual_condition != line.book_condition:
                # إنشاء تسوية
                adjustment = PhysicalCountAdjustment.objects.create(
                    physical_count=count,
                    asset=line.asset,
                    old_condition=line.book_condition,
                    new_condition=line.actual_condition,
                    adjustment_reason='من الجرد الفعلي'
                )

                # ✅ إنشاء قيد التسوية
                journal_entry = adjustment.create_adjustment_entry()
                journal_entry.post(request.user)

                adjustments.append(adjustment)

        count.status = 'completed'
        count.save()

        messages.success(
            request,
            f'تم إتمام الجرد وإنشاء {len(adjustments)} قيد تسوية'
        )
        return redirect('assets:physical_count_detail', pk=pk)
```

---

### Phase 3: التحسينات والإضافات

#### 1. إضافة Bulk Operations
```python
# في asset_views.py
@login_required
@permission_required('assets.change_asset')
def bulk_depreciation(request):
    """حساب إهلاك جماعي"""
    pass

@login_required
@permission_required('assets.change_asset')
def bulk_transfer(request):
    """تحويل جماعي للأصول"""
    pass

@login_required
@permission_required('assets.change_asset')
def bulk_status_change(request):
    """تغيير حالة جماعية"""
    pass
```

#### 2. تحسين Reports
```python
# في report_views.py
class AssetRegisterReport(LoginRequiredMixin, TemplateView):
    """سجل الأصول الثابتة"""

    def get_context_data(self):
        # تقرير شامل بكل الأصول مع الإهلاك والصيانة
        pass

class DepreciationScheduleReport(LoginRequiredMixin, TemplateView):
    """جدول الإهلاك المستقبلي"""
    pass

class AssetMovementReport(LoginRequiredMixin, TemplateView):
    """تقرير حركة الأصول"""
    pass

class MaintenanceHistoryReport(LoginRequiredMixin, TemplateView):
    """سجل الصيانة"""
    pass
```

#### 3. إضافة API Views
```python
# في api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def asset_summary_api(request, pk):
    """ملخص الأصل (للـ Dashboard)"""
    asset = get_object_or_404(Asset, pk=pk, company=request.current_company)

    return Response({
        'asset_number': asset.asset_number,
        'name': asset.name,
        'purchase_price': asset.purchase_price,
        'book_value': asset.get_current_book_value(),
        'accumulated_depreciation': asset.get_total_depreciation(),
        'maintenance_count': asset.maintenances.count(),
        'last_maintenance': asset.get_last_maintenance(),
        # ... إلخ
    })
```

---

## 🔄 الـ Workflow المقترح

### 1. إنشاء أصل جديد
```
User Submit Form
    ↓
AssetCreateView.form_valid()
    ↓
Save Asset (with company, branch, created_by)
    ↓
[Optional] Asset.create_purchase_journal_entry()
    ↓
JournalEntry created (status=draft)
    ↓
Redirect to AssetDetailView
    ↓
User can review and post the entry
```

### 2. إهلاك شهري
```
User clicks "حساب الإهلاك الشهري"
    ↓
calculate_monthly_depreciation(month, year)
    ↓
Loop through active assets
    ↓
For each asset:
    - Calculate depreciation amount
    - Create AssetDepreciation record
    - AssetDepreciation.create_depreciation_journal_entry()
    - Auto-post entry if requested
    ↓
Show summary report
```

### 3. صيانة
```
Schedule Maintenance → Save as 'scheduled'
    ↓
Start Maintenance → Change to 'in_progress'
    ↓
Complete Maintenance → Enter actual_cost
    ↓
AssetMaintenance.create_journal_entry()
    ↓
Post entry automatically
    ↓
Status = 'completed'
```

---

## ✅ Checklist التنفيذ

### المرحلة 1: Models (أسبوع 1)
- [ ] إضافة methods محاسبية في Asset
- [ ] إضافة methods محاسبية في AssetDepreciation
- [ ] إضافة methods محاسبية في AssetTransaction
- [ ] إضافة methods محاسبية في AssetMaintenance
- [ ] إضافة methods محاسبية في AssetInsurance
- [ ] إضافة methods محاسبية في PhysicalCountAdjustment
- [ ] إضافة validation methods (can_edit, can_delete, can_post)
- [ ] Testing للـ methods

### المرحلة 2: Core Views (أسبوع 2)
- [ ] إعادة كتابة asset_views.py
- [ ] إنشاء category_views.py
- [ ] تحديث dashboard.py
- [ ] تحديث transaction_views.py مع التكامل المحاسبي
- [ ] Testing للـ CRUD operations

### المرحلة 3: Specialized Views (أسبوع 3)
- [ ] تحديث depreciation_views.py
- [ ] تحديث maintenance_views.py
- [ ] تحديث insurance_views.py
- [ ] تحديث lease_views.py
- [ ] تحديث physical_count_views.py
- [ ] Testing للعمليات المحاسبية

### المرحلة 4: Reports & Polish (أسبوع 4)
- [ ] تحسين report_views.py
- [ ] إضافة bulk operations
- [ ] تحسين api_views.py
- [ ] إضافة export/import
- [ ] UI/UX improvements
- [ ] Documentation
- [ ] Full system testing

---

## 📊 Metrics للنجاح

1. ✅ كل عملية أصول تنشئ قيد محاسبي تلقائياً
2. ✅ لا يوجد hard-coded accounts في views
3. ✅ كل view يستخدم CompanyMixin و AuditLogMixin
4. ✅ Permissions محددة بدقة
5. ✅ Messages واضحة للمستخدم
6. ✅ Breadcrumbs موحدة
7. ✅ Error handling شامل
8. ✅ Transaction.atomic لكل عملية حساسة

---

## 🎓 أمثلة كود جاهزة

سأقوم بكتابة ملفات كاملة كأمثلة في المراحل القادمة:

1. `asset_views_NEW.py` - مثال كامل للـ Asset CRUD
2. `transaction_views_NEW.py` - مع التكامل المحاسبي الكامل
3. `depreciation_views_NEW.py` - مع حساب وترحيل تلقائي
4. `asset_models_UPDATED.py` - مع كل الـ methods المحاسبية

---

## 💡 ملاحظات هامة

1. **لا تحذف الـ views القديمة** - احتفظ بها في backup
2. **اختبر كل method في Models قبل استخدامه في Views**
3. **استخدم fixtures للبيانات التجريبية**
4. **راجع الـ permissions** - تأكد من وجود custom permissions إن لزم
5. **التوثيق** - اكتب docstrings واضحة
6. **الأداء** - استخدم select_related و prefetch_related دائماً

---

**هل تريد أن أبدأ بكتابة أي من الملفات المذكورة؟**

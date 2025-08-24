# apps/base_data/views/item_views.py
"""
Views الخاصة بالأصناف والمواد
يشمل: الأصناف، التصنيفات، معدلات التحويل، المكونات
"""

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse, HttpResponse
from django.views import View
from django_datatables_view.base_datatable_view import BaseDatatableView

from ..models import Item, ItemCategory, ItemConversion, ItemComponent
from ..forms import (
    ItemForm, ItemCategoryForm, ItemConversionForm, ItemComponentForm,
    ItemQuickAddForm, ItemImportForm, ItemFilterForm
)


class BaseItemMixin:
    """Mixin أساسي للأصناف - يحتوي على الإعدادات المشتركة"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة معلومات الشركة والفرع
        context['current_company'] = self.request.user.company
        context['current_branch'] = self.request.user.branch

        # Breadcrumbs
        context['breadcrumbs'] = self.get_breadcrumbs()

        return context

    def get_breadcrumbs(self):
        """بناء breadcrumbs للصفحة"""
        return [
            {'title': _('الرئيسية'), 'url': reverse_lazy('core:dashboard')},
            {'title': _('البيانات الأساسية'), 'url': '#'},
        ]

    def get_queryset(self):
        """فلترة البيانات حسب الشركة"""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.company)


# ============== Views الأصناف ==============

class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, ListView):
    """عرض قائمة الأصناف"""
    model = Item
    template_name = 'base_data/item/item_list.html'
    context_object_name = 'items'
    permission_required = 'base_data.view_item'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الأصناف')
        context['filter_form'] = ItemFilterForm(
            company=self.request.user.company,
            data=self.request.GET or None
        )

        # إحصائيات سريعة
        context['stats'] = {
            'total_items': self.get_queryset().count(),
            'active_items': self.get_queryset().filter(is_inactive=False).count(),
            'categories_count': ItemCategory.objects.filter(
                company=self.request.user.company,
                is_active=True
            ).count(),
            'out_of_stock': self.get_queryset().filter(
                itemstock__quantity__lte=F('minimum_quantity')
            ).distinct().count()
        }

        # breadcrumbs
        context['breadcrumbs'].append({'title': _('الأصناف'), 'active': True})

        return context

    def get_queryset(self):
        """تطبيق الفلاتر"""
        queryset = super().get_queryset()

        # استخدام FilterForm
        filter_form = ItemFilterForm(
            company=self.request.user.company,
            data=self.request.GET or None
        )

        if filter_form.is_valid():
            queryset = filter_form.get_queryset(queryset)

        return queryset.select_related(
            'category', 'unit', 'created_by', 'updated_by'
        ).prefetch_related('substitute_items')


class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, DetailView):
    """عرض تفاصيل الصنف"""
    model = Item
    template_name = 'base_data/item/item_detail.html'
    context_object_name = 'item'
    permission_required = 'base_data.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = str(self.object)

        # معلومات المخزون
        context['stock_info'] = self.object.itemstock_set.select_related(
            'warehouse'
        ).order_by('warehouse__name')

        # معدلات التحويل
        context['conversions'] = self.object.conversions.select_related(
            'from_unit', 'to_unit'
        )

        # المكونات (إن وجدت)
        context['components'] = self.object.components.select_related(
            'component_item', 'unit'
        )

        # المواد البديلة
        context['substitutes'] = self.object.substitute_items.all()

        # آخر الحركات
        context['recent_movements'] = self.object.stockmovement_set.select_related(
            'warehouse', 'created_by'
        ).order_by('-date')[:10]

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': str(self.object), 'active': True}
        ])

        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                     BaseItemMixin, CreateView):
    """إضافة صنف جديد"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/item/item_form.html'
    permission_required = 'base_data.add_item'
    success_url = reverse_lazy('base_data:item_list')
    success_message = _('تم إضافة الصنف %(name)s بنجاح')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة صنف جديد')
        context['action'] = _('إضافة')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('إضافة صنف جديد'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                     BaseItemMixin, UpdateView):
    """تعديل صنف"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/item/item_form.html'
    permission_required = 'base_data.change_item'
    success_url = reverse_lazy('base_data:item_list')
    success_message = _('تم تعديل الصنف %(name)s بنجاح')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل صنف: %s') % self.object
        context['action'] = _('تعديل')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': str(self.object), 'url': self.object.get_absolute_url()},
            {'title': _('تعديل'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, DeleteView):
    """حذف صنف"""
    model = Item
    template_name = 'base_data/confirm_delete.html'
    permission_required = 'base_data.delete_item'
    success_url = reverse_lazy('base_data:item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف صنف')
        context['message'] = _('هل أنت متأكد من حذف الصنف "%s"؟') % self.object
        context['cancel_url'] = reverse_lazy('base_data:item_list')

        # التحقق من وجود حركات
        if self.object.stockmovement_set.exists():
            context['warning'] = _('تحذير: هذا الصنف له حركات مخزنية مسجلة!')

        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, _('تم حذف الصنف %s بنجاح') % obj)
        return super().delete(request, *args, **kwargs)


class ItemDataTableView(LoginRequiredMixin, PermissionRequiredMixin, BaseDatatableView):
    """DataTable AJAX للأصناف"""
    model = Item
    columns = [
        'code', 'name', 'barcode', 'category__name', 'unit__name',
        'sale_price', 'purchase_price', 'is_inactive', 'id'
    ]
    order_columns = [
        'code', 'name', 'barcode', 'category__name', 'unit__name',
        'sale_price', 'purchase_price', 'is_inactive', ''
    ]
    permission_required = 'base_data.view_item'
    max_display_length = 100

    def get_initial_queryset(self):
        return Item.objects.filter(
            company=self.request.user.company
        ).select_related('category', 'unit')

    def filter_queryset(self, qs):
        """تطبيق فلاتر DataTables"""
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(barcode__icontains=search) |
                Q(category__name__icontains=search)
            )

        # فلترة حسب التصنيف
        category_id = self.request.GET.get('category', None)
        if category_id:
            qs = qs.filter(category_id=category_id)

        # فلترة حسب الحالة
        status = self.request.GET.get('status', None)
        if status == 'active':
            qs = qs.filter(is_inactive=False)
        elif status == 'inactive':
            qs = qs.filter(is_inactive=True)

        return qs

    def prepare_results(self, qs):
        """تحضير البيانات للعرض"""
        json_data = []
        for item in qs:
            json_data.append([
                item.code,
                item.name,
                item.barcode or '-',
                item.category.name if item.category else '-',
                item.unit.name if item.unit else '-',
                f'{item.sale_price:,.2f}',
                f'{item.purchase_price:,.2f}',
                self.render_status(item.is_inactive),
                self.render_actions(item)
            ])
        return json_data

    def render_status(self, is_inactive):
        """عرض حالة الصنف"""
        if is_inactive:
            return '<span class="badge bg-danger">غير نشط</span>'
        return '<span class="badge bg-success">نشط</span>'

    def render_actions(self, obj):
        """أزرار الإجراءات"""
        actions = []

        # عرض
        if self.request.user.has_perm('base_data.view_item'):
            actions.append(
                f'<a href="{obj.get_absolute_url()}" '
                f'class="btn btn-sm btn-info" title="{_("عرض")}">'
                f'<i class="fas fa-eye"></i></a>'
            )

        # تعديل
        if self.request.user.has_perm('base_data.change_item'):
            actions.append(
                f'<a href="{obj.get_edit_url()}" '
                f'class="btn btn-sm btn-warning" title="{_("تعديل")}">'
                f'<i class="fas fa-edit"></i></a>'
            )

        # حذف
        if self.request.user.has_perm('base_data.delete_item'):
            actions.append(
                f'<button type="button" class="btn btn-sm btn-danger" '
                f'onclick="confirmDelete({obj.pk}, \'{obj}\')" title="{_("حذف")}">'
                f'<i class="fas fa-trash"></i></button>'
            )

        return ' '.join(actions)


class ItemQuickAddView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إضافة صنف سريعة (للنوافذ المنبثقة)"""
    model = Item
    form_class = ItemQuickAddForm
    template_name = 'base_data/item/item_quick_add.html'
    permission_required = 'base_data.add_item'

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.branch = self.request.user.branch
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        self.object = form.save()

        # إرجاع JSON response
        return JsonResponse({
            'success': True,
            'id': self.object.id,
            'name': str(self.object),
            'code': self.object.code,
            'message': _('تم إضافة الصنف بنجاح')
        })

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


class ItemImportView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, View):
    """استيراد الأصناف من ملف Excel/CSV"""
    permission_required = 'base_data.add_item'
    template_name = 'base_data/item/item_import.html'

    def get(self, request):
        context = {
            'title': _('استيراد الأصناف'),
            'form': ItemImportForm(),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse_lazy('core:dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
                {'title': _('استيراد'), 'active': True}
            ]
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = ItemImportForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # معالجة الملف
                result = self.process_import(
                    form.cleaned_data['import_file'],
                    form.cleaned_data['file_format'],
                    form.cleaned_data['update_existing']
                )

                messages.success(
                    request,
                    _('تم استيراد %(count)d صنف بنجاح') % {'count': result['success']}
                )

                if result['errors']:
                    messages.warning(
                        request,
                        _('فشل استيراد %(count)d صنف') % {'count': len(result['errors'])}
                    )

                return redirect('base_data:item_list')

            except Exception as e:
                messages.error(request, _('خطأ في الاستيراد: %s') % str(e))

        context = {
            'title': _('استيراد الأصناف'),
            'form': form,
            'breadcrumbs': self.get_breadcrumbs()
        }
        return render(request, self.template_name, context)

    def process_import(self, file, file_format, update_existing):
        """معالجة ملف الاستيراد"""
        # سيتم تطويرها لاحقاً
        # هنا يتم قراءة الملف ومعالجة البيانات
        return {'success': 0, 'errors': []}


class ItemExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """تصدير الأصناف"""
    permission_required = 'base_data.view_item'

    def get(self, request):
        # الحصول على البيانات المفلترة
        queryset = Item.objects.filter(company=request.user.company)

        # تطبيق الفلاتر من GET parameters
        filter_form = ItemFilterForm(
            company=request.user.company,
            data=request.GET or None
        )

        if filter_form.is_valid():
            queryset = filter_form.get_queryset(queryset)

        # تحديد صيغة التصدير
        export_format = request.GET.get('format', 'xlsx')

        if export_format == 'xlsx':
            return self.export_excel(queryset)
        elif export_format == 'csv':
            return self.export_csv(queryset)
        else:
            return self.export_pdf(queryset)

    def export_excel(self, queryset):
        """تصدير Excel"""
        # سيتم تطويرها مع openpyxl
        pass

    def export_csv(self, queryset):
        """تصدير CSV"""
        import csv

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="items.csv"'
        response.write('\ufeff')  # BOM for UTF-8

        writer = csv.writer(response)
        # كتابة العناوين
        writer.writerow([
            _('الرمز'), _('الاسم'), _('الباركود'),
            _('التصنيف'), _('الوحدة'), _('سعر البيع'),
            _('سعر الشراء'), _('الحالة')
        ])

        # كتابة البيانات
        for item in queryset:
            writer.writerow([
                item.code,
                item.name,
                item.barcode or '',
                item.category.name if item.category else '',
                item.unit.name if item.unit else '',
                item.sale_price,
                item.purchase_price,
                _('غير نشط') if item.is_inactive else _('نشط')
            ])

        return response


# ============== Views التصنيفات ==============

class ItemCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, ListView):
    """عرض قائمة التصنيفات"""
    model = ItemCategory
    template_name = 'base_data/item/category_list.html'
    context_object_name = 'categories'
    permission_required = 'base_data.view_itemcategory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تصنيفات الأصناف')

        # بناء شجرة التصنيفات
        context['category_tree'] = self.build_category_tree()

        # إحصائيات
        context['stats'] = {
            'total_categories': self.get_queryset().count(),
            'total_items': Item.objects.filter(
                company=self.request.user.company
            ).count()
        }

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('التصنيفات'), 'active': True}
        ])

        return context

    def build_category_tree(self):
        """بناء شجرة التصنيفات"""
        categories = self.get_queryset().select_related('parent')

        # تنظيم حسب المستوى
        tree = {}
        for cat in categories:
            if not cat.parent:
                tree[cat] = self.get_children(cat, categories)

        return tree

    def get_children(self, parent, all_categories):
        """الحصول على الأبناء"""
        children = {}
        for cat in all_categories:
            if cat.parent == parent:
                children[cat] = self.get_children(cat, all_categories)
        return children


class ItemCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                             BaseItemMixin, CreateView):
    """إضافة تصنيف جديد"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/item/category_form.html'
    permission_required = 'base_data.add_itemcategory'
    success_url = reverse_lazy('base_data:category_list')
    success_message = _('تم إضافة التصنيف %(name)s بنجاح')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة تصنيف جديد')
        context['action'] = _('إضافة')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('التصنيفات'), 'url': reverse_lazy('base_data:category_list')},
            {'title': _('إضافة تصنيف'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                             BaseItemMixin, UpdateView):
    """تعديل تصنيف"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/item/category_form.html'
    permission_required = 'base_data.change_itemcategory'
    success_url = reverse_lazy('base_data:category_list')
    success_message = _('تم تعديل التصنيف %(name)s بنجاح')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل تصنيف: %s') % self.object
        context['action'] = _('تعديل')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('التصنيفات'), 'url': reverse_lazy('base_data:category_list')},
            {'title': str(self.object), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, DeleteView):
    """حذف تصنيف"""
    model = ItemCategory
    template_name = 'base_data/confirm_delete.html'
    permission_required = 'base_data.delete_itemcategory'
    success_url = reverse_lazy('base_data:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف تصنيف')
        context['message'] = _('هل أنت متأكد من حذف التصنيف "%s"؟') % self.object
        context['cancel_url'] = reverse_lazy('base_data:category_list')

        # التحقق من وجود أصناف
        items_count = self.object.item_set.count()
        if items_count > 0:
            context['error'] = _('لا يمكن حذف هذا التصنيف لوجود %d صنف مرتبط به') % items_count
            context['can_delete'] = False

        # التحقق من وجود تصنيفات فرعية
        children_count = self.object.children.count()
        if children_count > 0:
            context['error'] = _('لا يمكن حذف هذا التصنيف لوجود %d تصنيف فرعي') % children_count
            context['can_delete'] = False

        return context


class ItemCategoryDataTableView(LoginRequiredMixin, PermissionRequiredMixin, BaseDatatableView):
    """DataTable AJAX للتصنيفات"""
    model = ItemCategory
    columns = ['code', 'name', 'parent__name', 'level', 'id']
    order_columns = ['code', 'name', 'parent__name', 'level', '']
    permission_required = 'base_data.view_itemcategory'

    def get_initial_queryset(self):
        return ItemCategory.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('parent')

    def prepare_results(self, qs):
        json_data = []
        for cat in qs:
            json_data.append([
                cat.code,
                '—' * (cat.level - 1) + ' ' + cat.name,
                cat.parent.name if cat.parent else '-',
                cat.level,
                self.render_actions(cat)
            ])
        return json_data

    def render_actions(self, obj):
        """أزرار الإجراءات"""
        actions = []

        # عدد الأصناف
        items_count = obj.item_set.count()
        actions.append(
            f'<span class="badge bg-info">{items_count} {_("صنف")}</span>'
        )

        # تعديل
        if self.request.user.has_perm('base_data.change_itemcategory'):
            actions.append(
                f'<a href="{reverse_lazy("base_data:category_update", args=[obj.pk])}" '
                f'class="btn btn-sm btn-warning" title="{_("تعديل")}">'
                f'<i class="fas fa-edit"></i></a>'
            )

        # حذف
        if self.request.user.has_perm('base_data.delete_itemcategory'):
            if items_count == 0 and not obj.children.exists():
                actions.append(
                    f'<button type="button" class="btn btn-sm btn-danger" '
                    f'onclick="confirmDelete({obj.pk}, \'{obj}\')" title="{_("حذف")}">'
                    f'<i class="fas fa-trash"></i></button>'
                )

        return ' '.join(actions)


# ============== Views معدلات التحويل ==============

class ItemConversionListView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, ListView):
    """عرض معدلات التحويل"""
    model = ItemConversion
    template_name = 'base_data/item/conversion_list.html'
    context_object_name = 'conversions'
    permission_required = 'base_data.view_itemconversion'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('معدلات تحويل الوحدات')

        # فلترة حسب الصنف إن وجد
        item_id = self.request.GET.get('item')
        if item_id:
            context['item'] = get_object_or_404(Item, pk=item_id, company=self.request.user.company)

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('معدلات التحويل'), 'active': True}
        ])

        return context

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'item', 'from_unit', 'to_unit'
        )

        # فلترة حسب الصنف
        item_id = self.request.GET.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset


class ItemConversionCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                               BaseItemMixin, CreateView):
    """إضافة معدل تحويل"""
    model = ItemConversion
    form_class = ItemConversionForm
    template_name = 'base_data/item/conversion_form.html'
    permission_required = 'base_data.add_itemconversion'
    success_message = _('تم إضافة معدل التحويل بنجاح')

    def get_success_url(self):
        if 'item' in self.request.GET:
            return reverse_lazy('base_data:conversion_list') + f'?item={self.request.GET["item"]}'
        return reverse_lazy('base_data:conversion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة معدل تحويل')
        context['action'] = _('إضافة')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('معدلات التحويل'), 'url': reverse_lazy('base_data:conversion_list')},
            {'title': _('إضافة'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # إذا كان من صفحة صنف معين
        item_id = self.request.GET.get('item')
        if item_id:
            initial['item'] = item_id
        return initial

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemConversionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                               BaseItemMixin, UpdateView):
    """تعديل معدل تحويل"""
    model = ItemConversion
    form_class = ItemConversionForm
    template_name = 'base_data/item/conversion_form.html'
    permission_required = 'base_data.change_itemconversion'
    success_message = _('تم تعديل معدل التحويل بنجاح')

    def get_success_url(self):
        return reverse_lazy('base_data:conversion_list') + f'?item={self.object.item.pk}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل معدل تحويل')
        context['action'] = _('تعديل')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('معدلات التحويل'), 'url': reverse_lazy('base_data:conversion_list')},
            {'title': _('تعديل'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemConversionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, DeleteView):
    """حذف معدل تحويل"""
    model = ItemConversion
    template_name = 'base_data/confirm_delete.html'
    permission_required = 'base_data.delete_itemconversion'

    def get_success_url(self):
        return reverse_lazy('base_data:conversion_list') + f'?item={self.object.item.pk}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف معدل تحويل')
        context['message'] = _('هل أنت متأكد من حذف معدل التحويل: %s؟') % self.object
        context['cancel_url'] = self.get_success_url()
        return context


# ============== Views مكونات المواد ==============

class ItemComponentListView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, ListView):
    """عرض مكونات المواد"""
    model = ItemComponent
    template_name = 'base_data/item/component_list.html'
    context_object_name = 'components'
    permission_required = 'base_data.view_itemcomponent'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('مكونات المواد')

        # فلترة حسب المنتج
        item_id = self.request.GET.get('parent_item')
        if item_id:
            context['parent_item'] = get_object_or_404(
                Item, pk=item_id, company=self.request.user.company
            )

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('مكونات المواد'), 'active': True}
        ])

        return context

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'parent_item', 'component_item', 'unit'
        )

        # فلترة حسب المنتج
        item_id = self.request.GET.get('parent_item')
        if item_id:
            queryset = queryset.filter(parent_item_id=item_id)

        return queryset


class ItemComponentCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                              BaseItemMixin, CreateView):
    """إضافة مكون"""
    model = ItemComponent
    form_class = ItemComponentForm
    template_name = 'base_data/item/component_form.html'
    permission_required = 'base_data.add_itemcomponent'
    success_message = _('تم إضافة المكون بنجاح')

    def get_success_url(self):
        if self.object.parent_item:
            return reverse_lazy('base_data:component_list') + f'?parent_item={self.object.parent_item.pk}'
        return reverse_lazy('base_data:component_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة مكون')
        context['action'] = _('إضافة')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('مكونات المواد'), 'url': reverse_lazy('base_data:component_list')},
            {'title': _('إضافة'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # إذا كان من صفحة منتج معين
        item_id = self.request.GET.get('parent_item')
        if item_id:
            initial['parent_item'] = item_id
        return initial

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemComponentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin,
                              BaseItemMixin, UpdateView):
    """تعديل مكون"""
    model = ItemComponent
    form_class = ItemComponentForm
    template_name = 'base_data/item/component_form.html'
    permission_required = 'base_data.change_itemcomponent'
    success_message = _('تم تعديل المكون بنجاح')

    def get_success_url(self):
        return reverse_lazy('base_data:component_list') + f'?parent_item={self.object.parent_item.pk}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل مكون')
        context['action'] = _('تعديل')

        # breadcrumbs
        context['breadcrumbs'].extend([
            {'title': _('الأصناف'), 'url': reverse_lazy('base_data:item_list')},
            {'title': _('مكونات المواد'), 'url': reverse_lazy('base_data:component_list')},
            {'title': _('تعديل'), 'active': True}
        ])

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ItemComponentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, BaseItemMixin, DeleteView):
    """حذف مكون"""
    model = ItemComponent
    template_name = 'base_data/confirm_delete.html'
    permission_required = 'base_data.delete_itemcomponent'

    def get_success_url(self):
        return reverse_lazy('base_data:component_list') + f'?parent_item={self.object.parent_item.pk}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف مكون')
        context['message'] = _('هل أنت متأكد من حذف هذا المكون؟')
        context['cancel_url'] = self.get_success_url()
        return context
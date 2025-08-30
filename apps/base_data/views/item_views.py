# apps/base_data/views/item_views.py
"""
Views الأصناف - CRUD + معدلات التحويل + مكونات المواد
Class-based views + Bootstrap 5 + RTL + DataTables server-side
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.db.models import Q, Count, Sum, F
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from django.forms import inlineformset_factory
from django.views import View

from ..models import Item, ItemCategory, ItemConversion, ItemComponent, WarehouseItem
from ..forms import (
    ItemForm, ItemFilterForm, ItemQuickAddForm, ItemConversionFormSet,
    ItemComponentFormSet, ItemImportForm
)
from apps.core.mixins import CompanyMixin, AjaxResponseMixin
from apps.core.utils import generate_code


class ItemListView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض قائمة الأصناف مع فلترة وبحث"""
    model = Item
    template_name = 'base_data/items/list.html'
    context_object_name = 'items'
    paginate_by = 25

    def get_queryset(self):
        queryset = Item.objects.filter(
            company=self.request.user.company
        ).select_related('category', 'unit').prefetch_related('warehouse_items')

        # تطبيق الفلاتر
        self.filter_form = ItemFilterForm(
            data=self.request.GET or None,
            company=self.request.user.company
        )

        if self.filter_form.is_valid():
            queryset = self.filter_form.get_queryset(queryset)

        # الترتيب الافتراضي
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': self.filter_form,
            'page_title': _('الأصناف'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('الأصناف'), 'active': True}
            ],
            'can_add': self.request.user.has_perm('base_data.add_item'),
            'can_change': self.request.user.has_perm('base_data.change_item'),
            'can_delete': self.request.user.has_perm('base_data.delete_item'),
            'total_items': self.get_queryset().count(),
            'active_items': self.get_queryset().filter(is_active=True, is_inactive=False).count(),
        })
        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء صنف جديد"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/items/form.html'
    permission_required = 'base_data.add_item'
    success_url = reverse_lazy('base_data:item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة FormSets للمعدلات والمكونات
        if self.request.POST:
            context['conversion_formset'] = ItemConversionFormSet(
                self.request.POST,
                instance=self.object,
                prefix='conversions'
            )
            context['component_formset'] = ItemComponentFormSet(
                self.request.POST,
                instance=self.object,
                prefix='components'
            )
        else:
            context['conversion_formset'] = ItemConversionFormSet(
                instance=self.object,
                prefix='conversions'
            )
            context['component_formset'] = ItemComponentFormSet(
                instance=self.object,
                prefix='components'
            )

        context.update({
            'page_title': _('إضافة صنف جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ الصنف'),
            'cancel_url': reverse('base_data:item_list'),
        })
        return context

    def form_valid(self, form):
        # تعيين الشركة والمستخدم
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        # توليد الكود إذا لم يتم إدخاله
        if not form.instance.code:
            form.instance.code = generate_code('ITEM', self.request.user.company)

        # التحقق من صحة FormSets
        context = self.get_context_data()
        conversion_formset = context['conversion_formset']
        component_formset = context['component_formset']

        with transaction.atomic():
            if form.is_valid() and conversion_formset.is_valid() and component_formset.is_valid():
                self.object = form.save()

                conversion_formset.instance = self.object
                conversion_formset.save()

                component_formset.instance = self.object
                component_formset.save()

                messages.success(
                    self.request,
                    _('تم إنشاء الصنف "%(name)s" بنجاح') % {'name': self.object.name}
                )
                return super().form_valid(form)
            else:
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل صنف موجود"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/items/form.html'
    permission_required = 'base_data.change_item'
    context_object_name = 'item'

    def get_queryset(self):
        return Item.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['conversion_formset'] = ItemConversionFormSet(
                self.request.POST,
                instance=self.object,
                prefix='conversions'
            )
            context['component_formset'] = ItemComponentFormSet(
                self.request.POST,
                instance=self.object,
                prefix='components'
            )
        else:
            context['conversion_formset'] = ItemConversionFormSet(
                instance=self.object,
                prefix='conversions'
            )
            context['component_formset'] = ItemComponentFormSet(
                instance=self.object,
                prefix='components'
            )

        context.update({
            'page_title': _('تعديل الصنف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': self.object.name, 'active': True}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('base_data:item_detail', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:item_delete', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        context = self.get_context_data()
        conversion_formset = context['conversion_formset']
        component_formset = context['component_formset']

        with transaction.atomic():
            if form.is_valid() and conversion_formset.is_valid() and component_formset.is_valid():
                self.object = form.save()

                conversion_formset.instance = self.object
                conversion_formset.save()

                component_formset.instance = self.object
                component_formset.save()

                messages.success(
                    self.request,
                    _('تم تحديث الصنف "%(name)s" بنجاح') % {'name': self.object.name}
                )
                return redirect('base_data:item_detail', pk=self.object.pk)
            else:
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemDetailView(LoginRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل الصنف"""
    model = Item
    template_name = 'base_data/items/detail.html'
    context_object_name = 'item'

    def get_queryset(self):
        return Item.objects.filter(
            company=self.request.user.company
        ).select_related('category', 'unit', 'created_by', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # جلب المعدلات والمكونات
        conversions = self.object.conversions.select_related('from_unit', 'to_unit')
        components = self.object.components.select_related('component_item', 'unit')
        warehouse_items = self.object.warehouse_items.select_related('warehouse')

        # حساب إجمالي المخزون
        total_stock = warehouse_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        context.update({
            'page_title': self.object.name,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': self.object.name, 'active': True}
            ],
            'conversions': conversions,
            'components': components,
            'warehouse_items': warehouse_items,
            'total_stock': total_stock,
            'can_change': self.request.user.has_perm('base_data.change_item'),
            'can_delete': self.request.user.has_perm('base_data.delete_item'),
            'edit_url': reverse('base_data:item_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:item_delete', kwargs={'pk': self.object.pk}),
        })
        return context


class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف صنف"""
    model = Item
    template_name = 'base_data/items/delete.html'
    permission_required = 'base_data.delete_item'
    success_url = reverse_lazy('base_data:item_list')
    context_object_name = 'item'

    def get_queryset(self):
        return Item.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # فحص الاستخدامات
        usage_count = {
            'sales_lines': 0,  # من نظام المبيعات
            'purchase_lines': 0,  # من نظام المشتريات
            'warehouse_items': self.object.warehouse_items.count(),
            'components': self.object.components.count(),
        }

        context.update({
            'page_title': _('حذف الصنف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': self.object.name, 'url': reverse('base_data:item_detail', kwargs={'pk': self.object.pk})},
                {'title': _('حذف'), 'active': True}
            ],
            'usage_count': usage_count,
            'can_delete': sum(usage_count.values()) == 0,
            'cancel_url': reverse('base_data:item_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # فحص إمكانية الحذف
        if self.object.warehouse_items.exists() or self.object.components.exists():
            messages.error(
                request,
                _('لا يمكن حذف الصنف "%(name)s" لأنه مستخدم في معاملات أخرى') % {
                    'name': self.object.name
                }
            )
            return redirect('base_data:item_detail', pk=self.object.pk)

        name = self.object.name
        self.object.delete()

        messages.success(
            request,
            _('تم حذف الصنف "%(name)s" بنجاح') % {'name': name}
        )
        return redirect(self.success_url)


class ItemQuickAddView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, CreateView):
    """إضافة سريعة للصنف عبر AJAX"""
    model = Item
    form_class = ItemQuickAddForm
    template_name = 'base_data/items/quick_add.html'
    permission_required = 'base_data.add_item'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            form.instance.code = generate_code('ITEM', self.request.user.company)

        self.object = form.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('تم إنشاء الصنف بنجاح'),
                'item': {
                    'id': self.object.pk,
                    'code': self.object.code,
                    'name': self.object.name,
                    'category': self.object.category.name if self.object.category else '',
                    'unit': self.object.unit.name if self.object.unit else '',
                }
            })

        messages.success(self.request, _('تم إنشاء الصنف بنجاح'))
        return redirect('base_data:item_list')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('يرجى تصحيح الأخطاء'),
                'errors': form.errors
            })
        return super().form_invalid(form)


class ItemDuplicateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """تكرار صنف موجود"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/items/form.html'
    permission_required = 'base_data.add_item'

    def get_initial(self):
        original_item = get_object_or_404(
            Item,
            pk=self.kwargs['pk'],
            company=self.request.user.company
        )

        initial = {
            'name': f"{original_item.name} - {_('نسخة')}",
            'category': original_item.category,
            'unit': original_item.unit,
            'purchase_price': original_item.purchase_price,
            'sale_price': original_item.sale_price,
            'tax_rate': original_item.tax_rate,
            'manufacturer': original_item.manufacturer,
            'specifications': original_item.specifications,
            'weight': original_item.weight,
            'minimum_quantity': original_item.minimum_quantity,
            'maximum_quantity': original_item.maximum_quantity,
        }
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        original_item = get_object_or_404(
            Item,
            pk=self.kwargs['pk'],
            company=self.request.user.company
        )

        context.update({
            'page_title': _('تكرار الصنف: %(name)s') % {'name': original_item.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': original_item.name, 'url': reverse('base_data:item_detail', kwargs={'pk': original_item.pk})},
                {'title': _('تكرار'), 'active': True}
            ],
            'submit_text': _('إنشاء نسخة'),
            'cancel_url': reverse('base_data:item_detail', kwargs={'pk': original_item.pk}),
            'is_duplicate': True,
        })
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.code = generate_code('ITEM', self.request.user.company)

        self.object = form.save()
        messages.success(
            self.request,
            _('تم تكرار الصنف بنجاح باسم "%(name)s"') % {'name': self.object.name}
        )
        return redirect('base_data:item_detail', pk=self.object.pk)


class ItemToggleActiveView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """تفعيل/إلغاء تفعيل الصنف"""
    permission_required = 'base_data.change_item'

    def post(self, request, pk):
        item = get_object_or_404(Item, pk=pk, company=request.user.company)

        item.is_active = not item.is_active
        item.updated_by = request.user
        item.save()

        status_text = _('نشط') if item.is_active else _('غير نشط')
        message = _('تم تغيير حالة الصنف "%(name)s" إلى %(status)s') % {
            'name': item.name,
            'status': status_text
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'is_active': item.is_active,
                'status_text': status_text
            })

        messages.success(request, message)
        return redirect('base_data:item_list')


# AJAX Views للـ DataTables
# تحديث ItemDataTableView في item_views.py

class ItemDataTableView(LoginRequiredMixin, CompanyMixin, View):
    """بيانات الأصناف لـ DataTables - إصلاح 403 error"""

    def dispatch(self, request, *args, **kwargs):
        # التأكد من Authentication أولاً
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # التحقق من الصلاحيات
        if not request.user.has_perm('base_data.view_item'):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            # معاملات DataTable
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 25))
            search_value = request.GET.get('search[value]', '').strip()

            # معاملات الترتيب
            order_column = int(request.GET.get('order[0][column]', 1))
            order_dir = request.GET.get('order[0][dir]', 'asc')

            # الأعمدة (تطابق template)
            columns = ['', 'code', 'name', 'category__name', 'unit__name', 'sale_price', '', 'is_active', '']

            # تحديد عمود الترتيب
            if 1 <= order_column < len(columns) and columns[order_column]:
                order_field = columns[order_column]
                if order_dir == 'desc':
                    order_field = f'-{order_field}'
            else:
                order_field = '-created_at'

            # الاستعلام الأساسي
            queryset = Item.objects.filter(
                company=request.user.company
            ).select_related('category', 'unit')

            # تطبيق الفلاتر من النموذج
            search = request.GET.get('search', '')
            category = request.GET.get('category', '')
            unit = request.GET.get('unit', '')
            is_active = request.GET.get('is_active', '')
            stock_status = request.GET.get('stock_status', '')

            if search:
                queryset = queryset.filter(
                    Q(code__icontains=search) |
                    Q(name__icontains=search) |
                    Q(barcode__icontains=search)
                )

            if category:
                queryset = queryset.filter(category_id=category)

            if unit:
                queryset = queryset.filter(unit_id=unit)

            if is_active:
                if is_active == '1':
                    queryset = queryset.filter(is_active=True, is_inactive=False)
                elif is_active == '0':
                    queryset = queryset.filter(Q(is_active=False) | Q(is_inactive=True))

            # البحث العام
            if search_value:
                queryset = queryset.filter(
                    Q(code__icontains=search_value) |
                    Q(name__icontains=search_value) |
                    Q(category__name__icontains=search_value) |
                    Q(unit__name__icontains=search_value)
                )

            # العد قبل التقسيم
            total_count = Item.objects.filter(company=request.user.company).count()
            filtered_count = queryset.count()

            # الترتيب والتقسيم
            queryset = queryset.order_by(order_field)[start:start + length]

            # تحضير البيانات
            data = []
            for item in queryset:
                # حساب المخزون
                stock_total = item.warehouse_items.aggregate(
                    total=Sum('quantity')
                ).get('total') or 0

                data.append({
                    'id': item.pk,
                    'checkbox': '',  # سيتم ملؤه بـ JavaScript
                    'code': item.code or '',
                    'name': item.name,
                    'category': item.category.name if item.category else '',
                    'unit': item.unit.name if item.unit else '',
                    'sale_price': str(item.sale_price) if item.sale_price else '0.00',
                    'stock': str(stock_total),
                    'is_active': item.is_active and not item.is_inactive,
                    'actions': self._get_action_buttons(item, request)
                })

            return JsonResponse({
                'draw': draw,
                'recordsTotal': total_count,
                'recordsFiltered': filtered_count,
                'data': data
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'ItemDataTableView error: {str(e)}', exc_info=True)

            return JsonResponse({
                'draw': int(request.GET.get('draw', 1)),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': str(e)
            }, status=500)

    def _get_action_buttons(self, item, request):
        """إنشاء أزرار الإجراءات"""
        buttons = []

        # عرض
        if request.user.has_perm('base_data.view_item'):
            buttons.append(f'''
                <a href="{reverse('base_data:item_detail', kwargs={'pk': item.pk})}" 
                   class="btn btn-sm btn-outline-primary" title="عرض">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

        # تعديل
        if request.user.has_perm('base_data.change_item'):
            buttons.append(f'''
                <a href="{reverse('base_data:item_update', kwargs={'pk': item.pk})}" 
                   class="btn btn-sm btn-outline-warning" title="تعديل">
                    <i class="fas fa-edit"></i>
                </a>
            ''')

            # تفعيل/إلغاء تفعيل
            is_active = item.is_active and not item.is_inactive
            toggle_class = 'success' if is_active else 'secondary'
            toggle_title = 'إلغاء التفعيل' if is_active else 'تفعيل'

            buttons.append(f'''
                <button onclick="toggleItemStatus({item.pk})" 
                        class="btn btn-sm btn-outline-{toggle_class}" title="{toggle_title}">
                    <i class="fas fa-toggle-{'on' if is_active else 'off'}"></i>
                </button>
            ''')

        # حذف
        if request.user.has_perm('base_data.delete_item'):
            buttons.append(f'''
                <a href="{reverse('base_data:item_delete', kwargs={'pk': item.pk})}" 
                   class="btn btn-sm btn-outline-danger" title="حذف"
                   onclick="return confirm('هل أنت متأكد من الحذف؟')">
                    <i class="fas fa-trash"></i>
                </a>
            ''')

        return ' '.join(buttons)

# Views للبحث والتحديد
class ItemSelectView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """بحث الأصناف للـ Select2"""

    def get(self, request):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        page_size = 20

        queryset = Item.objects.filter(
            company=request.user.company,
            is_active=True,
            is_inactive=False
        ).select_related('category', 'unit')

        if term:
            queryset = queryset.filter(
                Q(code__icontains=term) |
                Q(name__icontains=term) |
                Q(barcode__icontains=term)
            )

        total_count = queryset.count()
        start = (page - 1) * page_size
        items = queryset[start:start + page_size]

        results = []
        for item in items:
            results.append({
                'id': item.pk,
                'text': f"{item.code} - {item.name}",
                'category': item.category.name if item.category else '',
                'unit': item.unit.name if item.unit else '',
                'sale_price': float(item.sale_price) if item.sale_price else 0,
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': start + page_size < total_count
            }
        })


class ItemStockView(LoginRequiredMixin, CompanyMixin, DetailView):
    """عرض مخزون الصنف في جميع المستودعات"""
    model = Item
    template_name = 'base_data/items/stock.html'
    context_object_name = 'item'

    def get_queryset(self):
        return Item.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        warehouse_items = WarehouseItem.objects.filter(
            item=self.object,
            warehouse__company=self.request.user.company,
            warehouse__is_active=True
        ).select_related('warehouse').order_by('warehouse__name')

        total_stock = sum(wi.quantity for wi in warehouse_items)
        total_value = sum(wi.quantity * wi.average_cost for wi in warehouse_items)

        context.update({
            'page_title': _('مخزون الصنف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('base_data:item_list')},
                {'title': self.object.name, 'url': reverse('base_data:item_detail', kwargs={'pk': self.object.pk})},
                {'title': _('المخزون'), 'active': True}
            ],
            'warehouse_items': warehouse_items,
            'total_stock': total_stock,
            'total_value': total_value,
            'low_stock_alert': total_stock <= self.object.minimum_quantity if self.object.minimum_quantity else False,
        })
        return context
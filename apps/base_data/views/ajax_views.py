# apps/base_data/views/ajax_views.py
"""
AJAX Views - DataTables server-side + Select2 + Quick actions
Bootstrap 5 + RTL + JSON responses
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.db.models import Q, Count, Sum, F, Case, When, Value, CharField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib import messages

from ..models import Item, BusinessPartner, Warehouse, ItemCategory, UnitOfMeasure, WarehouseItem
from apps.core.mixins import CompanyMixin, AjaxResponseMixin


class BaseDataTableView(LoginRequiredMixin, CompanyMixin, View):
    """Base class لجميع DataTables AJAX views"""
    model = None
    columns = []
    searchable_fields = []
    default_order = '-created_at'

    def get(self, request):
        draw = int(request.GET.get('draw', 0))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '')
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        # بناء الاستعلام الأساسي
        queryset = self.get_base_queryset()

        # تطبيق الفلاتر الإضافية
        queryset = self.apply_filters(queryset)

        # البحث
        if search_value and self.searchable_fields:
            search_q = Q()
            for field in self.searchable_fields:
                search_q |= Q(**{f'{field}__icontains': search_value})
            queryset = queryset.filter(search_q)

        # العدد الكلي
        total_count = self.get_base_queryset().count()
        filtered_count = queryset.count()

        # الترتيب
        order_column_name = self.get_order_column(order_column, order_dir)
        queryset = queryset.order_by(order_column_name)

        # التقسيم
        queryset = queryset[start:start + length]

        # تحضير البيانات
        data = []
        for obj in queryset:
            row_data = self.prepare_row_data(obj)
            data.append(row_data)

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data
        })

    def get_base_queryset(self):
        """الاستعلام الأساسي"""
        return self.model.objects.filter(company=self.request.user.company)

    def apply_filters(self, queryset):
        """تطبيق فلاتر إضافية"""
        return queryset

    def get_order_column(self, order_column, order_dir):
        """تحديد عمود الترتيب"""
        if order_column < len(self.columns):
            column_name = self.columns[order_column]
        else:
            column_name = self.default_order.lstrip('-')

        if order_dir == 'desc':
            column_name = f'-{column_name}'

        return column_name

    def prepare_row_data(self, obj):
        """تحضير بيانات الصف"""
        raise NotImplementedError


class DashboardStatsView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """إحصائيات Dashboard"""

    def get(self, request):
        company = request.user.company

        # إحصائيات الأصناف
        items_stats = Item.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True, is_inactive=False)),
            inactive=Count('id', filter=Q(is_inactive=True)),
            with_stock=Count('id', filter=Q(warehouse_items__quantity__gt=0))
        )

        # إحصائيات الشركاء
        partners_stats = BusinessPartner.objects.filter(company=company).aggregate(
            total=Count('id'),
            customers=Count('id', filter=Q(partner_type__in=['customer', 'both'])),
            suppliers=Count('id', filter=Q(partner_type__in=['supplier', 'both'])),
            active=Count('id', filter=Q(is_active=True))
        )

        # إحصائيات المستودعات
        warehouses_stats = Warehouse.objects.filter(company=company).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            main=Count('id', filter=Q(warehouse_type='main')),
            branch=Count('id', filter=Q(warehouse_type='branch'))
        )

        # إحصائيات المخزون
        stock_stats = WarehouseItem.objects.filter(
            warehouse__company=company
        ).aggregate(
            total_items=Count('item', distinct=True),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('average_cost')),
            low_stock_items=Count(
                'item',
                filter=Q(quantity__lte=F('item__minimum_quantity')),
                distinct=True
            )
        )

        return JsonResponse({
            'items': items_stats,
            'partners': partners_stats,
            'warehouses': warehouses_stats,
            'stock': stock_stats or {
                'total_items': 0,
                'total_quantity': 0,
                'total_value': 0,
                'low_stock_items': 0
            }
        })


class QuickSearchView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """البحث السريع العام"""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        results = []

        # البحث في الأصناف
        items = Item.objects.filter(
            company=request.user.company,
            is_active=True
        ).filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(barcode__icontains=query)
        )[:5]

        for item in items:
            results.append({
                'type': 'item',
                'id': item.pk,
                'title': item.name,
                'subtitle': f'{item.code} - {item.category.name if item.category else ""}',
                'url': reverse('base_data:item_detail', kwargs={'pk': item.pk}),
                'icon': 'fas fa-box text-primary'
            })

        # البحث في الشركاء
        partners = BusinessPartner.objects.filter(
            company=request.user.company,
            is_active=True
        ).filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:5]

        for partner in partners:
            results.append({
                'type': 'partner',
                'id': partner.pk,
                'title': partner.name,
                'subtitle': f'{partner.code} - {partner.get_partner_type_display()}',
                'url': reverse('base_data:partner_detail', kwargs={'pk': partner.pk}),
                'icon': 'fas fa-user-tie text-info'
            })

        # البحث في المستودعات
        warehouses = Warehouse.objects.filter(
            company=request.user.company,
            is_active=True
        ).filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(location__icontains=query)
        )[:3]

        for warehouse in warehouses:
            results.append({
                'type': 'warehouse',
                'id': warehouse.pk,
                'title': warehouse.name,
                'subtitle': f'{warehouse.code} - {warehouse.get_warehouse_type_display()}',
                'url': reverse('base_data:warehouse_detail', kwargs={'pk': warehouse.pk}),
                'icon': 'fas fa-warehouse text-success'
            })

        return JsonResponse({
            'results': results,
            'has_more': len(results) >= 10
        })


class BulkActionView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """الإجراءات المجمعة"""
    model = None
    permission_required = None

    def post(self, request):
        action = request.POST.get('action')
        ids = request.POST.getlist('ids[]')

        if not action or not ids:
            return JsonResponse({
                'success': False,
                'message': _('يرجى اختيار عنصر واحد على الأقل')
            })

        queryset = self.model.objects.filter(
            id__in=ids,
            company=request.user.company
        )

        if not queryset.exists():
            return JsonResponse({
                'success': False,
                'message': _('لم يتم العثور على عناصر')
            })

        try:
            if action == 'activate':
                count = queryset.update(is_active=True, updated_by=request.user)
                message = _('تم تفعيل %(count)d عنصر') % {'count': count}

            elif action == 'deactivate':
                count = queryset.update(is_active=False, updated_by=request.user)
                message = _('تم إلغاء تفعيل %(count)d عنصر') % {'count': count}

            elif action == 'delete':
                # فحص إمكانية الحذف
                can_delete, error_message = self.can_delete(queryset)
                if not can_delete:
                    return JsonResponse({
                        'success': False,
                        'message': error_message
                    })

                count = queryset.count()
                queryset.delete()
                message = _('تم حذف %(count)d عنصر') % {'count': count}

            else:
                return JsonResponse({
                    'success': False,
                    'message': _('إجراء غير مدعوم')
                })

            return JsonResponse({
                'success': True,
                'message': message,
                'count': count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    def can_delete(self, queryset):
        """فحص إمكانية الحذف المجمع"""
        return True, None


class ItemBulkActionView(BulkActionView):
    """الإجراءات المجمعة للأصناف"""
    model = Item
    permission_required = 'base_data.change_item'

    def can_delete(self, queryset):
        # فحص وجود مخزون أو معاملات
        has_stock = WarehouseItem.objects.filter(
            item__in=queryset,
            quantity__gt=0
        ).exists()

        if has_stock:
            return False, _('لا يمكن حذف أصناف لها مخزون')

        return True, None


class PartnerBulkActionView(BulkActionView):
    """الإجراءات المجمعة للشركاء"""
    model = BusinessPartner
    permission_required = 'base_data.change_businesspartner'


class WarehouseBulkActionView(BulkActionView):
    """الإجراءات المجمعة للمستودعات"""
    model = Warehouse
    permission_required = 'base_data.change_warehouse'

    def can_delete(self, queryset):
        # فحص وجود مخزون
        has_items = WarehouseItem.objects.filter(
            warehouse__in=queryset,
            quantity__gt=0
        ).exists()

        if has_items:
            return False, _('لا يمكن حذف مستودعات تحتوي على مخزون')

        return True, None


class ValidationView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """التحقق من صحة البيانات"""

    def get(self, request):
        field = request.GET.get('field')
        value = request.GET.get('value')
        model_name = request.GET.get('model')
        exclude_id = request.GET.get('exclude_id')

        if not all([field, value, model_name]):
            return JsonResponse({'valid': False})

        # تحديد النموذج
        model_map = {
            'item': Item,
            'partner': BusinessPartner,
            'warehouse': Warehouse,
            'category': ItemCategory,
            'unit': UnitOfMeasure
        }

        model = model_map.get(model_name)
        if not model:
            return JsonResponse({'valid': False})

        # بناء الاستعلام
        kwargs = {
            field: value,
            'company': request.user.company
        }

        queryset = model.objects.filter(**kwargs)

        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)

        is_valid = not queryset.exists()

        return JsonResponse({
            'valid': is_valid,
            'message': _('هذه القيمة مستخدمة من قبل') if not is_valid else ''
        })


class ItemStockCheckView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """فحص مخزون الصنف"""

    def get(self, request, item_id):
        try:
            item = Item.objects.get(
                pk=item_id,
                company=request.user.company
            )

            warehouse_items = WarehouseItem.objects.filter(
                item=item,
                warehouse__is_active=True
            ).select_related('warehouse')

            stock_data = []
            total_stock = 0

            for wi in warehouse_items:
                stock_data.append({
                    'warehouse_id': wi.warehouse.pk,
                    'warehouse_name': wi.warehouse.name,
                    'quantity': float(wi.quantity),
                    'average_cost': float(wi.average_cost),
                    'value': float(wi.quantity * wi.average_cost)
                })
                total_stock += wi.quantity

            return JsonResponse({
                'success': True,
                'item': {
                    'id': item.pk,
                    'name': item.name,
                    'code': item.code,
                    'unit': item.unit.name if item.unit else '',
                    'minimum_quantity': float(item.minimum_quantity)
                },
                'stock_data': stock_data,
                'total_stock': float(total_stock),
                'is_low_stock': total_stock <= item.minimum_quantity if item.minimum_quantity else False
            })

        except Item.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('الصنف غير موجود')
            })


class PartnerBalanceView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """رصيد الشريك"""

    def get(self, request, partner_id):
        try:
            partner = BusinessPartner.objects.get(
                pk=partner_id,
                company=request.user.company
            )

            # هنا يمكن حساب الرصيد من النظام المحاسبي
            balance_data = {
                'opening_balance': 0,
                'total_debit': 0,
                'total_credit': 0,
                'current_balance': 0,
                'credit_limit': float(partner.credit_limit) if partner.credit_limit else 0,
                'available_credit': float(partner.credit_limit) if partner.credit_limit else 0,
                'is_over_limit': False
            }

            return JsonResponse({
                'success': True,
                'partner': {
                    'id': partner.pk,
                    'name': partner.name,
                    'code': partner.code,
                    'partner_type': partner.get_partner_type_display()
                },
                'balance': balance_data
            })

        except BusinessPartner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('الشريك غير موجود')
            })


class NotificationsView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """إشعارات البيانات الأساسية"""

    def get(self, request):
        notifications = []

        # أصناف منخفضة المخزون
        low_stock_items = WarehouseItem.objects.filter(
            warehouse__company=request.user.company,
            warehouse__is_active=True,
            quantity__lte=F('item__minimum_quantity'),
            item__minimum_quantity__gt=0
        ).select_related('item', 'warehouse')[:10]

        for wi in low_stock_items:
            notifications.append({
                'type': 'low_stock',
                'title': _('مخزون منخفض'),
                'message': _('الصنف %(item)s في %(warehouse)s: %(qty)s %(unit)s') % {
                    'item': wi.item.name,
                    'warehouse': wi.warehouse.name,
                    'qty': wi.quantity,
                    'unit': wi.item.unit.name if wi.item.unit else ''
                },
                'url': reverse('base_data:item_detail', kwargs={'pk': wi.item.pk}),
                'icon': 'fas fa-exclamation-triangle',
                'class': 'text-warning',
                'created_at': wi.updated_at.isoformat() if wi.updated_at else None
            })

        # أصناف بدون مخزون
        zero_stock_count = Item.objects.filter(
            company=request.user.company,
            is_active=True,
            is_inactive=False
        ).exclude(
            warehouse_items__quantity__gt=0
        ).count()

        if zero_stock_count > 0:
            notifications.append({
                'type': 'zero_stock',
                'title': _('أصناف بدون مخزون'),
                'message': _('%(count)d صنف بدون مخزون') % {'count': zero_stock_count},
                'url': reverse('base_data:item_list') + '?stock_status=out_of_stock',
                'icon': 'fas fa-times-circle',
                'class': 'text-danger',
                'created_at': None
            })

        return JsonResponse({
            'notifications': notifications,
            'count': len(notifications)
        })
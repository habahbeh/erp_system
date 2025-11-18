# apps/core/views/datatables_views.py
"""
DataTables Server-Side Processing Views
Provides AJAX endpoints for DataTables with server-side processing
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from decimal import Decimal

from apps.core.models import (
    PricingRule, PriceList, PriceListItem, Item
)
from apps.core.utils.datatables_helper import (
    DataTablesServerSide, DataTablesColumnBuilder, DataTablesExporter
)


class PricingRuleDatatableView(LoginRequiredMixin, View):
    """
    Server-side DataTables endpoint for pricing rules
    """

    def get(self, request, *args, **kwargs):
        """
        Handle DataTables AJAX request for pricing rules
        """
        # Base queryset
        queryset = PricingRule.objects.filter(
            company=request.current_company
        ).select_related('company')

        # Define columns
        columns = [
            DataTablesColumnBuilder.text_column('code', 'الرمز'),
            DataTablesColumnBuilder.text_column('name', 'الاسم'),
            DataTablesColumnBuilder.text_column('rule_type', 'النوع', orderable=True),
            DataTablesColumnBuilder.number_column('priority', 'الأولوية'),
            DataTablesColumnBuilder.boolean_column('is_active', 'نشط'),
            DataTablesColumnBuilder.date_column('created_at', 'تاريخ الإنشاء'),
            DataTablesColumnBuilder.actions_column(),
        ]

        # Create processor
        dt_processor = DataTablesServerSide(request, queryset, columns)

        # Row callback
        def row_callback(rule):
            # Get rule type display
            rule_type_display = {
                'DISCOUNT_PERCENTAGE': 'خصم نسبة مئوية',
                'DISCOUNT_AMOUNT': 'خصم مبلغ ثابت',
                'MARKUP_PERCENTAGE': 'هامش ربح نسبي',
                'MARKUP_AMOUNT': 'هامش ربح ثابت',
                'BULK_DISCOUNT': 'خصم الكميات',
                'CUSTOM_FORMULA': 'معادلة مخصصة',
            }.get(rule.rule_type, rule.rule_type)

            # Build action buttons
            actions = f'''
                <div class="btn-group btn-group-sm">
                    <a href="{reverse('core:pricing_rule_detail', args=[rule.pk])}"
                       class="btn btn-info" title="عرض">
                        <i class="fas fa-eye"></i>
                    </a>
                    <a href="{reverse('core:pricing_rule_update', args=[rule.pk])}"
                       class="btn btn-warning" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                    <a href="{reverse('core:pricing_rule_test', args=[rule.pk])}"
                       class="btn btn-success" title="اختبار">
                        <i class="fas fa-flask"></i>
                    </a>
                    <a href="{reverse('core:pricing_rule_delete', args=[rule.pk])}"
                       class="btn btn-danger" title="حذف">
                        <i class="fas fa-trash"></i>
                    </a>
                </div>
            '''

            return {
                'code': rule.code,
                'name': rule.name,
                'rule_type': rule_type_display,
                'priority': rule.priority,
                'is_active': '<span class="badge bg-success">نعم</span>' if rule.is_active else '<span class="badge bg-secondary">لا</span>',
                'created_at': rule.created_at.strftime('%Y-%m-%d') if rule.created_at else '',
                'actions': actions
            }

        # Process and return response
        return dt_processor.process(row_callback)


class PriceListItemDatatableView(LoginRequiredMixin, View):
    """
    Server-side DataTables endpoint for price list items
    """

    def get(self, request, *args, **kwargs):
        """
        Handle DataTables AJAX request for price list items
        """
        price_list_id = request.GET.get('price_list_id')

        # Base queryset
        queryset = PriceListItem.objects.filter(
            item__company=request.current_company
        ).select_related('item', 'price_list', 'uom', 'item__category')

        if price_list_id:
            queryset = queryset.filter(price_list_id=price_list_id)

        # Define columns
        columns = [
            DataTablesColumnBuilder.text_column('item__code', 'رمز الصنف', search_fields=['item__code', 'item__name']),
            DataTablesColumnBuilder.text_column('item__name', 'اسم الصنف'),
            DataTablesColumnBuilder.text_column('item__category__name', 'التصنيف'),
            DataTablesColumnBuilder.text_column('price_list__name', 'قائمة الأسعار'),
            DataTablesColumnBuilder.text_column('uom__name', 'الوحدة'),
            DataTablesColumnBuilder.number_column('price', 'السعر'),
            DataTablesColumnBuilder.date_column('updated_at', 'آخر تحديث'),
            DataTablesColumnBuilder.actions_column(),
        ]

        # Create processor
        dt_processor = DataTablesServerSide(request, queryset, columns)

        # Row callback
        def row_callback(price_item):
            currency_symbol = request.current_company.currency.symbol if request.current_company.currency else ''

            actions = f'''
                <div class="btn-group btn-group-sm">
                    <a href="{reverse('core:item_detail', args=[price_item.item.pk])}"
                       class="btn btn-info" title="عرض الصنف">
                        <i class="fas fa-eye"></i>
                    </a>
                    <button class="btn btn-warning edit-price-btn"
                            data-id="{price_item.pk}"
                            data-price="{price_item.price}"
                            title="تعديل السعر">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            '''

            return {
                'item__code': price_item.item.code,
                'item__name': price_item.item.name,
                'item__category__name': price_item.item.category.name if price_item.item.category else '-',
                'price_list__name': price_item.price_list.name,
                'uom__name': price_item.uom.name,
                'price': f'{price_item.price:,.2f} {currency_symbol}',
                'updated_at': price_item.updated_at.strftime('%Y-%m-%d %H:%M') if hasattr(price_item, 'updated_at') and price_item.updated_at else '',
                'actions': actions
            }

        # Process and return response
        return dt_processor.process(row_callback)


class ItemPricesDatatableView(LoginRequiredMixin, View):
    """
    Server-side DataTables endpoint for items with prices
    """

    def get(self, request, *args, **kwargs):
        """
        Handle DataTables AJAX request for items with price information
        """
        category_id = request.GET.get('category_id')

        # Base queryset
        queryset = Item.objects.filter(
            company=request.current_company,
            is_active=True
        ).select_related('category', 'base_uom', 'currency')

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Define columns
        columns = [
            DataTablesColumnBuilder.text_column('code', 'الرمز'),
            DataTablesColumnBuilder.text_column('name', 'الاسم'),
            DataTablesColumnBuilder.text_column('category__name', 'التصنيف'),
            DataTablesColumnBuilder.text_column('base_uom__name', 'الوحدة'),
            DataTablesColumnBuilder.number_column('price_lists_count', 'عدد الأسعار', orderable=False),
            DataTablesColumnBuilder.actions_column(),
        ]

        # Create processor
        dt_processor = DataTablesServerSide(request, queryset, columns)

        # Row callback
        def row_callback(item):
            # Count price lists for this item
            price_lists_count = PriceListItem.objects.filter(item=item).count()

            actions = f'''
                <div class="btn-group btn-group-sm">
                    <a href="{reverse('core:item_detail', args=[item.pk])}"
                       class="btn btn-info" title="عرض">
                        <i class="fas fa-eye"></i>
                    </a>
                    <a href="{reverse('core:item_prices', args=[item.pk])}"
                       class="btn btn-success" title="الأسعار">
                        <i class="fas fa-tags"></i>
                    </a>
                    <a href="{reverse('core:item_price_calculator', args=[item.pk])}"
                       class="btn btn-warning" title="حاسبة الأسعار">
                        <i class="fas fa-calculator"></i>
                    </a>
                </div>
            '''

            return {
                'code': item.code,
                'name': item.name,
                'category__name': item.category.name if item.category else '-',
                'base_uom__name': item.base_uom.name if item.base_uom else '-',
                'price_lists_count': f'<span class="badge bg-primary">{price_lists_count}</span>',
                'actions': actions
            }

        # Process and return response
        return dt_processor.process(row_callback)


class ExportPricingRulesView(LoginRequiredMixin, View):
    """
    Export pricing rules to Excel/CSV
    """

    def get(self, request, *args, **kwargs):
        """
        Export pricing rules
        """
        format_type = request.GET.get('format', 'excel')

        # Get queryset
        queryset = PricingRule.objects.filter(
            company=request.current_company
        ).order_by('priority', 'code')

        # Define columns
        columns = [
            {'name': 'code', 'label': 'الرمز'},
            {'name': 'name', 'label': 'الاسم'},
            {'name': 'rule_type', 'label': 'النوع'},
            {'name': 'priority', 'label': 'الأولوية'},
            {'name': 'is_active', 'label': 'نشط'},
            {'name': 'created_at', 'label': 'تاريخ الإنشاء'},
        ]

        # Export based on format
        if format_type == 'csv':
            return DataTablesExporter.to_csv(
                queryset, columns, 'pricing_rules.csv'
            )
        else:
            return DataTablesExporter.to_excel(
                queryset, columns, 'pricing_rules.xlsx'
            )


class ExportPriceListItemsView(LoginRequiredMixin, View):
    """
    Export price list items to Excel/CSV
    """

    def get(self, request, *args, **kwargs):
        """
        Export price list items
        """
        format_type = request.GET.get('format', 'excel')
        price_list_id = request.GET.get('price_list_id')

        # Get queryset
        queryset = PriceListItem.objects.filter(
            item__company=request.current_company
        ).select_related('item', 'price_list', 'uom')

        if price_list_id:
            queryset = queryset.filter(price_list_id=price_list_id)

        queryset = queryset.order_by('item__code')

        # Define columns
        columns = [
            {'name': 'item__code', 'label': 'رمز الصنف'},
            {'name': 'item__name', 'label': 'اسم الصنف'},
            {'name': 'price_list__name', 'label': 'قائمة الأسعار'},
            {'name': 'uom__name', 'label': 'الوحدة'},
            {'name': 'price', 'label': 'السعر'},
        ]

        # Export based on format
        if format_type == 'csv':
            return DataTablesExporter.to_csv(
                queryset, columns, 'price_list_items.csv'
            )
        else:
            return DataTablesExporter.to_excel(
                queryset, columns, 'price_list_items.xlsx'
            )

# apps/base_data/views/api_views.py
"""
API Views للبيانات الأساسية - كامل ومطابق للمتطلبات
يشمل: الأصناف، العملاء، الموردين، المستودعات، وحدات القياس، التصنيفات
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg, F, Prefetch
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.http import JsonResponse
from decimal import Decimal
import json

from ..models import (
    Item, ItemCategory, ItemConversion, ItemComponent, BusinessPartner,
    Customer, Supplier, ContactInfo, Warehouse, WarehouseItem,
    UnitOfMeasure, SalesRepresentative, Account, Branch
)
from ..serializers import (
    ItemSerializer, ItemDetailSerializer, ItemCategorySerializer,
    ItemConversionSerializer, ItemComponentSerializer,
    BusinessPartnerSerializer, BusinessPartnerDetailSerializer,
    CustomerSerializer, SupplierSerializer, ContactInfoSerializer,
    WarehouseSerializer, WarehouseDetailSerializer, WarehouseItemSerializer,
    UnitOfMeasureSerializer, SalesRepresentativeSerializer
)
from ..filters import ItemFilter, BusinessPartnerFilter, WarehouseFilter


class BaseDataPermission(permissions.BasePermission):
    """صلاحيات مخصصة للبيانات الأساسية"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # التحقق من الصلاحيات حسب نوع العملية
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm(f'base_data.view_{view.model._meta.model_name}')
        elif request.method == 'POST':
            return request.user.has_perm(f'base_data.add_{view.model._meta.model_name}')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_perm(f'base_data.change_{view.model._meta.model_name}')
        elif request.method == 'DELETE':
            return request.user.has_perm(f'base_data.delete_{view.model._meta.model_name}')

        return False


class BaseDataViewSetMixin:
    """Base Mixin للـ ViewSets للبيانات الأساسية"""
    permission_classes = [BaseDataPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        """تقييد البيانات حسب الشركة"""
        queryset = super().get_queryset()
        if hasattr(self.model, 'company'):
            queryset = queryset.filter(company=self.request.user.company)
        return queryset

    def perform_create(self, serializer):
        """إضافة الشركة والمستخدم عند الإنشاء"""
        data = {}
        if hasattr(self.model, 'company'):
            data['company'] = self.request.user.company
        if hasattr(self.model, 'branch') and self.request.user.branch:
            data['branch'] = self.request.user.branch
        if hasattr(self.model, 'created_by'):
            data['created_by'] = self.request.user

        serializer.save(**data)

    def perform_update(self, serializer):
        """إضافة المستخدم المحدث"""
        data = {}
        if hasattr(self.model, 'updated_by'):
            data['updated_by'] = self.request.user

        serializer.save(**data)

    @property
    def model(self):
        """الحصول على النموذج من الـ queryset"""
        return self.get_queryset().model


# ============== API التصنيفات ==============

class ItemCategoryViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API لتصنيفات الأصناف - 4 مستويات"""
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    search_fields = ['name', 'name_en', 'code']
    ordering_fields = ['code', 'name', 'level']
    ordering = ['code']

    def get_queryset(self):
        queryset = super().get_queryset()

        # فلترة حسب المستوى
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        # فلترة حسب الأب
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        elif parent_id == '':  # الحصول على المستوى الأول فقط
            queryset = queryset.filter(parent__isnull=True)

        # فلترة الحالة
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.select_related('parent').prefetch_related('children')

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """الحصول على التصنيفات الفرعية"""
        category = self.get_object()
        children = category.children.filter(is_active=True).order_by('code')
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """الحصول على الأصناف في التصنيف"""
        category = self.get_object()
        items = category.items.filter(
            company=request.user.company,
            is_inactive=False
        ).select_related('unit_of_measure')

        # تطبيق pagination
        page = request.query_params.get('page', 1)
        paginator = Paginator(items, 20)
        items_page = paginator.get_page(page)

        serializer = ItemSerializer(items_page, many=True, context={'request': request})
        return Response({
            'items': serializer.data,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': int(page)
        })

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """الحصول على شجرة التصنيفات الكاملة"""

        def build_tree(category):
            data = self.get_serializer(category).data
            children = category.children.filter(is_active=True).order_by('code')
            if children.exists():
                data['children'] = [build_tree(child) for child in children]
            data['items_count'] = category.items.filter(
                company=request.user.company,
                is_inactive=False
            ).count()
            return data

        root_categories = self.get_queryset().filter(
            parent__isnull=True,
            is_active=True
        ).order_by('code')

        tree_data = [build_tree(category) for category in root_categories]
        return Response(tree_data)

    @action(detail=False, methods=['get'])
    def levels(self, request):
        """الحصول على التصنيفات حسب المستوى"""
        level = request.query_params.get('level', 1)
        categories = self.get_queryset().filter(
            level=level,
            is_active=True
        ).order_by('code')

        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


# ============== API الأصناف ==============

class ItemViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API للأصناف مع جميع العلاقات"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    search_fields = ['name', 'name_en', 'code', 'barcode']
    ordering_fields = ['code', 'name', 'sale_price', 'purchase_price', 'created_at']
    ordering = ['code']
    filterset_class = ItemFilter

    def get_serializer_class(self):
        """اختيار الـ serializer حسب العملية"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ItemDetailSerializer
        return ItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'category', 'unit_of_measure', 'purchase_unit', 'sale_unit'
        ).prefetch_related(
            'conversions__from_unit', 'conversions__to_unit',
            'components__component_item', 'substitute_items'
        )

        # فلترة حسب التصنيف
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # فلترة حسب نوع الصنف
        item_type = self.request.query_params.get('item_type')
        if item_type:
            queryset = queryset.filter(item_type=item_type)

        # فلترة الحالة
        is_inactive = self.request.query_params.get('is_inactive')
        if is_inactive is not None:
            queryset = queryset.filter(is_inactive=is_inactive.lower() == 'true')

        # فلترة الأصناف ذات المخزون
        has_stock = self.request.query_params.get('has_stock')
        if has_stock == 'true':
            queryset = queryset.filter(warehouse_items__quantity__gt=0).distinct()

        return queryset

    @action(detail=True, methods=['get'])
    def conversions(self, request, pk=None):
        """معدلات تحويل الصنف"""
        item = self.get_object()
        conversions = item.conversions.filter(
            company=request.user.company
        ).select_related('from_unit', 'to_unit')

        serializer = ItemConversionSerializer(conversions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_conversion(self, request, pk=None):
        """إضافة معدل تحويل جديد"""
        item = self.get_object()
        serializer = ItemConversionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                item=item,
                company=request.user.company,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def components(self, request, pk=None):
        """مكونات الصنف"""
        item = self.get_object()
        components = item.components.filter(
            company=request.user.company
        ).select_related('component_item', 'unit')

        serializer = ItemComponentSerializer(components, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_component(self, request, pk=None):
        """إضافة مكون جديد"""
        item = self.get_object()
        serializer = ItemComponentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                parent_item=item,
                company=request.user.company,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def substitutes(self, request, pk=None):
        """المواد البديلة للصنف"""
        item = self.get_object()
        substitutes = item.substitute_items.filter(
            company=request.user.company,
            is_inactive=False
        )

        serializer = ItemSerializer(substitutes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_substitute(self, request, pk=None):
        """إضافة مادة بديلة"""
        item = self.get_object()
        substitute_id = request.data.get('substitute_id')

        try:
            substitute = Item.objects.get(
                id=substitute_id,
                company=request.user.company
            )
            item.substitute_items.add(substitute)
            return Response({'message': _('تم إضافة المادة البديلة بنجاح')})
        except Item.DoesNotExist:
            return Response(
                {'error': _('المادة البديلة غير موجودة')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def stock_summary(self, request, pk=None):
        """ملخص مخزون الصنف في جميع المستودعات"""
        item = self.get_object()
        warehouse_items = WarehouseItem.objects.filter(
            item=item,
            warehouse__company=request.user.company
        ).select_related('warehouse')

        total_quantity = sum(wi.quantity for wi in warehouse_items)
        total_value = sum(wi.quantity * wi.average_cost for wi in warehouse_items)

        warehouses_data = []
        for wi in warehouse_items:
            warehouses_data.append({
                'warehouse_id': wi.warehouse.id,
                'warehouse_name': wi.warehouse.name,
                'warehouse_code': wi.warehouse.code,
                'quantity': wi.quantity,
                'average_cost': wi.average_cost,
                'total_value': wi.quantity * wi.average_cost,
                'last_updated': wi.updated_at
            })

        return Response({
            'item_id': item.id,
            'item_code': item.code,
            'item_name': item.name,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'reorder_level': item.reorder_level,
            'max_level': item.max_level,
            'warehouses': warehouses_data
        })

    @action(detail=False, methods=['get'])
    def barcode_search(self, request):
        """البحث بالباركود"""
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response(
                {'error': _('الباركود مطلوب')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = self.get_queryset().get(barcode=barcode)
            serializer = ItemDetailSerializer(item, context={'request': request})
            return Response(serializer.data)
        except Item.DoesNotExist:
            return Response(
                {'error': _('الصنف غير موجود')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """الأصناف ذات المخزون المنخفض"""
        items = self.get_queryset().filter(
            reorder_level__gt=0
        ).annotate(
            total_stock=Sum('warehouse_items__quantity')
        ).filter(
            total_stock__lte=F('reorder_level')
        )

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """الأصناف المنتهية الصلاحية"""
        items = self.get_queryset().annotate(
            total_stock=Sum('warehouse_items__quantity')
        ).filter(
            Q(total_stock=0) | Q(total_stock__isnull=True)
        )

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


# ============== API الشركاء التجاريين ==============

class BusinessPartnerViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API للشركاء التجاريين"""
    queryset = BusinessPartner.objects.all()
    serializer_class = BusinessPartnerSerializer
    search_fields = ['name', 'name_en', 'code', 'phone', 'mobile', 'email']
    ordering_fields = ['code', 'name', 'partner_type', 'created_at']
    ordering = ['code']
    filterset_class = BusinessPartnerFilter

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return BusinessPartnerDetailSerializer
        return BusinessPartnerSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'account', 'sales_representative', 'branch'
        ).prefetch_related('contact_info')

        # فلترة نوع الشريك
        partner_type = self.request.query_params.get('partner_type')
        if partner_type:
            queryset = queryset.filter(partner_type=partner_type)

        # فلترة نوع الحساب
        account_type = self.request.query_params.get('account_type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)

        # فلترة الحالة الضريبية
        tax_status = self.request.query_params.get('tax_status')
        if tax_status:
            queryset = queryset.filter(tax_status=tax_status)

        return queryset

    @action(detail=False, methods=['get'])
    def customers(self, request):
        """العملاء فقط"""
        customers = self.get_queryset().filter(
            partner_type__in=['customer', 'both']
        )
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suppliers(self, request):
        """الموردين فقط"""
        suppliers = self.get_queryset().filter(
            partner_type__in=['supplier', 'both']
        )
        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def contact_info(self, request, pk=None):
        """معلومات الاتصال للشريك"""
        partner = self.get_object()
        contacts = partner.contact_info.all().order_by('contact_type')
        serializer = ContactInfoSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_contact(self, request, pk=None):
        """إضافة معلومة اتصال جديدة"""
        partner = self.get_object()
        serializer = ContactInfoSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                partner=partner,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """رصيد الشريك"""
        partner = self.get_object()
        # TODO: حساب الرصيد من الحركات المحاسبية
        balance_data = {
            'partner_id': partner.id,
            'partner_name': partner.name,
            'current_balance': 0,  # سيتم حسابه من الحركات
            'credit_limit': partner.credit_limit if hasattr(partner, 'credit_limit') else 0,
            'available_credit': 0,  # credit_limit - current_balance
            'last_transaction_date': None
        }
        return Response(balance_data)

    @action(detail=True, methods=['get'])
    def transactions_summary(self, request, pk=None):
        """ملخص معاملات الشريك"""
        partner = self.get_object()
        # TODO: إحصائيات من المبيعات/المشتريات
        summary = {
            'partner_id': partner.id,
            'total_transactions': 0,
            'total_amount': 0,
            'last_transaction_date': None,
            'average_transaction_value': 0
        }
        return Response(summary)


class CustomerViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API للعملاء"""
    serializer_class = CustomerSerializer
    search_fields = ['name', 'name_en', 'code', 'phone', 'email']
    ordering = ['code']

    def get_queryset(self):
        return Customer.customers.filter(
            company=self.request.user.company
        ).select_related('account', 'sales_representative')

    @action(detail=True, methods=['get'])
    def sales_summary(self, request, pk=None):
        """ملخص مبيعات العميل"""
        customer = self.get_object()
        # TODO: إحصائيات من المبيعات
        summary = {
            'customer_id': customer.id,
            'total_sales': 0,
            'total_invoices': 0,
            'average_invoice_value': 0,
            'last_sale_date': None,
            'outstanding_balance': 0
        }
        return Response(summary)


class SupplierViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API للموردين"""
    serializer_class = SupplierSerializer
    search_fields = ['name', 'name_en', 'code', 'phone', 'email']
    ordering = ['code']

    def get_queryset(self):
        return Supplier.suppliers.filter(
            company=self.request.user.company
        ).select_related('account', 'sales_representative')

    @action(detail=True, methods=['get'])
    def purchases_summary(self, request, pk=None):
        """ملخص مشتريات المورد"""
        supplier = self.get_object()
        # TODO: إحصائيات من المشتريات
        summary = {
            'supplier_id': supplier.id,
            'total_purchases': 0,
            'total_bills': 0,
            'average_bill_value': 0,
            'last_purchase_date': None,
            'outstanding_balance': 0
        }
        return Response(summary)


# ============== API المستودعات ==============

class WarehouseViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API للمستودعات"""
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    search_fields = ['name', 'name_en', 'code', 'location']
    ordering_fields = ['code', 'name', 'warehouse_type']
    ordering = ['code']
    filterset_class = WarehouseFilter

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return WarehouseDetailSerializer
        return WarehouseSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'branch', 'keeper'
        ).prefetch_related('warehouse_items__item')

        # فلترة حسب الفرع
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # فلترة حسب نوع المستودع
        warehouse_type = self.request.query_params.get('warehouse_type')
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)

        return queryset

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """أرصدة المستودع"""
        warehouse = self.get_object()
        warehouse_items = warehouse.warehouse_items.select_related(
            'item', 'item__unit_of_measure'
        ).order_by('item__name')

        # فلترة الأرصدة
        filter_type = request.query_params.get('filter', 'all')
        if filter_type == 'in_stock':
            warehouse_items = warehouse_items.filter(quantity__gt=0)
        elif filter_type == 'out_of_stock':
            warehouse_items = warehouse_items.filter(quantity=0)
        elif filter_type == 'low_stock':
            warehouse_items = warehouse_items.filter(
                quantity__lte=F('item__reorder_level'),
                item__reorder_level__gt=0
            )

        # تطبيق pagination
        page = request.query_params.get('page', 1)
        paginator = Paginator(warehouse_items, 50)
        items_page = paginator.get_page(page)

        serializer = WarehouseItemSerializer(items_page, many=True)
        return Response({
            'inventory': serializer.data,
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': int(page)
        })

    @action(detail=True, methods=['get'])
    def stock_summary(self, request, pk=None):
        """ملخص مخزون المستودع"""
        warehouse = self.get_object()
        warehouse_items = warehouse.warehouse_items.select_related('item')

        total_items = warehouse_items.count()
        items_in_stock = warehouse_items.filter(quantity__gt=0).count()
        items_out_of_stock = warehouse_items.filter(quantity=0).count()
        low_stock_items = warehouse_items.filter(
            quantity__lte=F('item__reorder_level'),
            item__reorder_level__gt=0
        ).count()

        total_value = sum(
            wi.quantity * wi.average_cost
            for wi in warehouse_items
        )

        return Response({
            'warehouse_id': warehouse.id,
            'warehouse_name': warehouse.name,
            'total_items': total_items,
            'items_in_stock': items_in_stock,
            'items_out_of_stock': items_out_of_stock,
            'low_stock_items': low_stock_items,
            'total_value': total_value
        })

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        """المستودعات حسب الفرع"""
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response(
                {'error': _('معرف الفرع مطلوب')},
                status=status.HTTP_400_BAD_REQUEST
            )

        warehouses = self.get_queryset().filter(
            branch_id=branch_id,
            is_active=True
        )
        serializer = self.get_serializer(warehouses, many=True)
        return Response(serializer.data)


# ============== API وحدات القياس ==============

class UnitOfMeasureViewSet(BaseDataViewSetMixin, viewsets.ModelViewSet):
    """API لوحدات القياس"""
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    search_fields = ['name', 'name_en', 'code']
    ordering_fields = ['code', 'name']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # فلترة الحالة
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.filter(is_active=True)


# ============== API Views البحث ==============

class ItemSearchAPIView(APIView):
    """API للبحث السريع في الأصناف"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        category_id = request.GET.get('category')

        if not query:
            return Response({'results': []})

        items_qs = Item.objects.filter(
            company=request.user.company,
            is_inactive=False
        ).filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(code__icontains=query) |
            Q(barcode__icontains=query)
        )

        if category_id:
            items_qs = items_qs.filter(category_id=category_id)

        items = items_qs.select_related(
            'unit_of_measure', 'category'
        )[:limit]

        results = []
        for item in items:
            results.append({
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'name_en': item.name_en,
                'barcode': item.barcode,
                'sale_price': float(item.sale_price or 0),
                'purchase_price': float(item.purchase_price or 0),
                'unit': str(item.unit_of_measure) if item.unit_of_measure else '',
                'category': str(item.category) if item.category else '',
                'text': f"{item.code} - {item.name}"
            })

        return Response({'results': results})


class PartnerSearchAPIView(APIView):
    """API للبحث السريع في الشركاء"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        partner_type = request.GET.get('type', '')
        limit = int(request.GET.get('limit', 10))

        if not query:
            return Response({'results': []})

        partners_qs = BusinessPartner.objects.filter(
            company=request.user.company,
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(code__icontains=query) |
            Q(phone__icontains=query) |
            Q(mobile__icontains=query) |
            Q(email__icontains=query)
        )

        if partner_type:
            if partner_type in ['customer', 'supplier']:
                partners_qs = partners_qs.filter(
                    Q(partner_type=partner_type) | Q(partner_type='both')
                )
            else:
                partners_qs = partners_qs.filter(partner_type=partner_type)

        partners = partners_qs[:limit]

        results = []
        for partner in partners:
            results.append({
                'id': partner.id,
                'code': partner.code,
                'name': partner.name,
                'name_en': partner.name_en,
                'partner_type': partner.partner_type,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'email': partner.email,
                'text': f"{partner.code} - {partner.name}"
            })

        return Response({'results': results})


class WarehouseSearchAPIView(APIView):
    """API للبحث السريع في المستودعات"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        branch_id = request.GET.get('branch')
        warehouse_type = request.GET.get('type')
        limit = int(request.GET.get('limit', 10))

        if not query:
            return Response({'results': []})

        warehouses_qs = Warehouse.objects.filter(
            company=request.user.company,
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(code__icontains=query) |
            Q(location__icontains=query)
        )

        if branch_id:
            warehouses_qs = warehouses_qs.filter(branch_id=branch_id)

        if warehouse_type:
            warehouses_qs = warehouses_qs.filter(warehouse_type=warehouse_type)

        warehouses = warehouses_qs.select_related('branch')[:limit]

        results = []
        for warehouse in warehouses:
            results.append({
                'id': warehouse.id,
                'code': warehouse.code,
                'name': warehouse.name,
                'warehouse_type': warehouse.warehouse_type,
                'location': warehouse.location,
                'branch_name': str(warehouse.branch) if warehouse.branch else '',
                'text': f"{warehouse.code} - {warehouse.name}"
            })

        return Response({'results': results})


# ============== API Views التحقق من البيانات ==============

class CheckBarcodeAPIView(APIView):
    """API للتحقق من تفرد الباركود"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        barcode = request.GET.get('barcode', '').strip()
        item_id = request.GET.get('exclude_id')  # استبعاد صنف معين من التحقق

        if not barcode:
            return Response({'exists': False, 'valid': True})

        items_qs = Item.objects.filter(
            barcode=barcode,
            company=request.user.company
        )

        if item_id:
            items_qs = items_qs.exclude(id=item_id)

        exists = items_qs.exists()

        if exists:
            item = items_qs.first()
            return Response({
                'exists': True,
                'valid': False,
                'item': {
                    'id': item.id,
                    'code': item.code,
                    'name': item.name
                }
            })

        return Response({'exists': False, 'valid': True})


class CheckCodeAPIView(APIView):
    """API للتحقق من تفرد الكود"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.GET.get('code', '').strip()
        model_name = request.GET.get('model', '')
        exclude_id = request.GET.get('exclude_id')

        if not code or not model_name:
            return Response({'exists': False, 'valid': True})

        model_map = {
            'item': Item,
            'partner': BusinessPartner,
            'customer': BusinessPartner,
            'supplier': BusinessPartner,
            'warehouse': Warehouse,
            'unit': UnitOfMeasure,
            'category': ItemCategory
        }

        model = model_map.get(model_name)
        if not model:
            return Response({'exists': False, 'valid': True})

        objects_qs = model.objects.filter(
            code=code,
            company=request.user.company
        )

        if exclude_id:
            objects_qs = objects_qs.exclude(id=exclude_id)

        exists = objects_qs.exists()

        if exists:
            obj = objects_qs.first()
            return Response({
                'exists': True,
                'valid': False,
                'object': {
                    'id': obj.id,
                    'code': obj.code,
                    'name': getattr(obj, 'name', str(obj))
                }
            })

        return Response({'exists': False, 'valid': True})


# ============== API Views الإحصائيات ==============

class StatsAPIView(APIView):
    """API للإحصائيات العامة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company

        # إحصائيات الأصناف
        items_stats = {
            'total_items': Item.objects.filter(company=company).count(),
            'active_items': Item.objects.filter(company=company, is_inactive=False).count(),
            'items_with_stock': WarehouseItem.objects.filter(
                warehouse__company=company,
                quantity__gt=0
            ).values('item').distinct().count(),
            'low_stock_items': Item.objects.filter(
                company=company,
                reorder_level__gt=0
            ).annotate(
                total_stock=Sum('warehouse_items__quantity')
            ).filter(
                total_stock__lte=F('reorder_level')
            ).count()
        }

        # إحصائيات الشركاء
        partners_stats = {
            'total_partners': BusinessPartner.objects.filter(company=company).count(),
            'customers': BusinessPartner.objects.filter(
                company=company,
                partner_type__in=['customer', 'both']
            ).count(),
            'suppliers': BusinessPartner.objects.filter(
                company=company,
                partner_type__in=['supplier', 'both']
            ).count()
        }

        # إحصائيات المستودعات
        warehouses_stats = {
            'total_warehouses': Warehouse.objects.filter(company=company).count(),
            'active_warehouses': Warehouse.objects.filter(
                company=company,
                is_active=True
            ).count(),
            'total_inventory_value': WarehouseItem.objects.filter(
                warehouse__company=company
            ).aggregate(
                total=Sum(F('quantity') * F('average_cost'))
            )['total'] or 0
        }

        return Response({
            'items': items_stats,
            'partners': partners_stats,
            'warehouses': warehouses_stats
        })


# ============== Function-based API Views ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_item_by_barcode(request):
    """الحصول على الصنف بالباركود"""
    barcode = request.GET.get('barcode')
    if not barcode:
        return Response({'error': 'الباركود مطلوب'}, status=400)

    try:
        item = Item.objects.select_related(
            'category', 'unit_of_measure'
        ).get(
            barcode=barcode,
            company=request.user.company
        )

        # الحصول على الرصيد الحالي
        current_stock = WarehouseItem.objects.filter(
            item=item,
            warehouse__company=request.user.company
        ).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        data = {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'barcode': item.barcode,
            'sale_price': float(item.sale_price or 0),
            'purchase_price': float(item.purchase_price or 0),
            'unit': str(item.unit_of_measure) if item.unit_of_measure else '',
            'category': str(item.category) if item.category else '',
            'current_stock': float(current_stock),
            'reorder_level': float(item.reorder_level or 0)
        }

        return Response(data)

    except Item.DoesNotExist:
        return Response({'error': 'الصنف غير موجود'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_warehouses_by_branch(request):
    """الحصول على المستودعات حسب الفرع"""
    branch_id = request.GET.get('branch_id')
    if not branch_id:
        return Response({'warehouses': []})

    warehouses = Warehouse.objects.filter(
        company=request.user.company,
        branch_id=branch_id,
        is_active=True
    ).values(
        'id', 'code', 'name', 'warehouse_type', 'location'
    ).order_by('name')

    return Response({'warehouses': list(warehouses)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_item_stock_by_warehouse(request):
    """الحصول على رصيد صنف في مستودع معين"""
    item_id = request.GET.get('item_id')
    warehouse_id = request.GET.get('warehouse_id')

    if not item_id or not warehouse_id:
        return Response({'error': 'معرف الصنف والمستودع مطلوبان'}, status=400)

    try:
        warehouse_item = WarehouseItem.objects.get(
            item_id=item_id,
            warehouse_id=warehouse_id,
            warehouse__company=request.user.company
        )

        return Response({
            'quantity': float(warehouse_item.quantity),
            'average_cost': float(warehouse_item.average_cost),
            'total_value': float(warehouse_item.quantity * warehouse_item.average_cost),
            'last_updated': warehouse_item.updated_at
        })

    except WarehouseItem.DoesNotExist:
        return Response({
            'quantity': 0,
            'average_cost': 0,
            'total_value': 0,
            'last_updated': None
        })
# apps/base_data/views/api_views.py
"""
API Views للبيانات الأساسية
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ..models import Item, ItemCategory, BusinessPartner, Customer, Supplier, Warehouse, UnitOfMeasure
from ..serializers import (
    ItemSerializer, ItemCategorySerializer, BusinessPartnerSerializer,
    CustomerSerializer, SupplierSerializer, WarehouseSerializer,
    UnitOfMeasureSerializer
)


class BaseDataViewSet:
    """Base ViewSet للبيانات الأساسية"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """تقييد البيانات حسب الشركة"""
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        """إضافة الشركة والمستخدم عند الإنشاء"""
        serializer.save(
            company=self.request.user.company,
            branch=self.request.user.branch,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        """إضافة المستخدم المحدث"""
        serializer.save(updated_by=self.request.user)


class ItemCategoryViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API لتصنيفات الأصناف"""
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """الحصول على التصنيفات الفرعية"""
        category = self.get_object()
        children = category.children.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """الحصول على شجرة التصنيفات"""
        categories = self.get_queryset().filter(parent=None, is_active=True)

        def build_tree(category):
            data = self.get_serializer(category).data
            children = category.children.filter(is_active=True)
            if children:
                data['children'] = [build_tree(child) for child in children]
            return data

        tree_data = [build_tree(category) for category in categories]
        return Response(tree_data)


class ItemViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API للأصناف"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # فلترة حسب التصنيف
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # فلترة حسب الحالة
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # البحث
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(barcode__icontains=search)
            )

        return queryset.select_related('category', 'unit')

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """الحصول على رصيد الصنف في المستودعات"""
        item = self.get_object()
        # TODO: سيتم تنفيذه عند إنشاء نموذج المخزون
        return Response({'message': 'سيتم تنفيذه قريباً'})

    @action(detail=False, methods=['get'])
    def barcode_search(self, request):
        """البحث بالباركود"""
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response({'error': 'الباركود مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = self.get_queryset().get(barcode=barcode)
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except Item.DoesNotExist:
            return Response({'error': 'الصنف غير موجود'}, status=status.HTTP_404_NOT_FOUND)


class BusinessPartnerViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API للشركاء التجاريين"""
    queryset = BusinessPartner.objects.all()
    serializer_class = BusinessPartnerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # فلترة حسب نوع الشريك
        partner_type = self.request.query_params.get('partner_type', None)
        if partner_type:
            queryset = queryset.filter(partner_type=partner_type)

        # البحث
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def customers(self, request):
        """الحصول على العملاء فقط"""
        customers = self.get_queryset().filter(
            partner_type__in=['customer', 'both']
        )
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suppliers(self, request):
        """الحصول على الموردين فقط"""
        suppliers = self.get_queryset().filter(
            partner_type__in=['supplier', 'both']
        )
        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data)


class CustomerViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API للعملاء"""
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.customers.filter(company=self.request.user.company)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """الحصول على رصيد العميل"""
        customer = self.get_object()
        # TODO: سيتم حساب الرصيد عند إنشاء نموذج المحاسبة
        return Response({'balance': 0, 'credit_limit': customer.credit_limit})


class SupplierViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API للموردين"""
    serializer_class = SupplierSerializer

    def get_queryset(self):
        return Supplier.suppliers.filter(company=self.request.user.company)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """الحصول على رصيد المورد"""
        supplier = self.get_object()
        # TODO: سيتم حساب الرصيد عند إنشاء نموذج المحاسبة
        return Response({'balance': 0})


class WarehouseViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API للمستودعات"""
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # فلترة حسب الفرع
        branch_id = self.request.query_params.get('branch', None)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # فلترة حسب نوع المستودع
        warehouse_type = self.request.query_params.get('type', None)
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)

        return queryset.select_related('branch', 'keeper')

    @action(detail=True, methods=['get'])
    def stock_summary(self, request, pk=None):
        """ملخص مخزون المستودع"""
        warehouse = self.get_object()
        # TODO: سيتم تنفيذه عند إنشاء نموذج المخزون
        return Response({
            'total_items': 0,
            'total_value': 0,
            'low_stock_items': 0
        })

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        """المستودعات حسب الفرع"""
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({'error': 'معرف الفرع مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

        warehouses = self.get_queryset().filter(branch_id=branch_id, is_active=True)
        serializer = self.get_serializer(warehouses, many=True)
        return Response(serializer.data)


class UnitOfMeasureViewSet(BaseDataViewSet, viewsets.ModelViewSet):
    """API لوحدات القياس"""
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)

        # البحث
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        return queryset
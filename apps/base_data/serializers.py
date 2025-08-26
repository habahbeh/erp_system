# apps/base_data/serializers.py
"""
Serializers لتطبيق البيانات الأساسية
للاستخدام مع Django REST Framework APIs
"""

from rest_framework import serializers
from .models import Item, ItemCategory, BusinessPartner, Warehouse, UnitOfMeasure


class ItemSerializer(serializers.ModelSerializer):
    """Serializer للأصناف"""

    class Meta:
        model = Item
        fields = ['id', 'code', 'name', 'name_en', 'barcode', 'is_active']


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer لتصنيفات الأصناف"""

    class Meta:
        model = ItemCategory
        fields = ['id', 'code', 'name', 'name_en', 'is_active']


class BusinessPartnerSerializer(serializers.ModelSerializer):
    """Serializer للشركاء التجاريين"""

    class Meta:
        model = BusinessPartner
        fields = ['id', 'code', 'name', 'name_en', 'partner_type', 'is_active']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer للعملاء (نفس BusinessPartner لكن مفلتر للعملاء)"""

    class Meta:
        model = BusinessPartner
        fields = ['id', 'code', 'name', 'name_en', 'partner_type', 'is_active']

    def get_queryset(self):
        return BusinessPartner.objects.filter(partner_type='customer')


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer للموردين (نفس BusinessPartner لكن مفلتر للموردين)"""

    class Meta:
        model = BusinessPartner
        fields = ['id', 'code', 'name', 'name_en', 'partner_type', 'is_active']

    def get_queryset(self):
        return BusinessPartner.objects.filter(partner_type='supplier')


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer للمستودعات"""

    class Meta:
        model = Warehouse
        fields = ['id', 'code', 'name', 'name_en', 'is_active']


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    """Serializer لوحدات القياس"""

    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name', 'name_en', 'is_active']
# apps/assets/forms/__init__.py
"""
نماذج تطبيق إدارة الأصول الثابتة
"""

from .asset_forms import (
    AssetCategoryForm,
    DepreciationMethodForm,
    AssetConditionForm,
    AssetForm,
    AssetAttachmentForm,
    AssetValuationForm,
    AssetFilterForm,
    AssetDepreciationCalculationForm,
)

from .transaction_forms import (
    AssetTransactionForm,
    AssetPurchaseForm,
    AssetSaleForm,
    AssetDisposalForm,
    AssetTransferForm,
)

from .maintenance_forms import (
    MaintenanceTypeForm,
    MaintenanceScheduleForm,
    AssetMaintenanceForm,
    MaintenanceFilterForm,
)

__all__ = [
    # نماذج الأصول
    'AssetCategoryForm',
    'DepreciationMethodForm',
    'AssetConditionForm',
    'AssetForm',
    'AssetAttachmentForm',
    'AssetValuationForm',
    'AssetFilterForm',
    'AssetDepreciationCalculationForm',

    # نماذج العمليات
    'AssetTransactionForm',
    'AssetPurchaseForm',
    'AssetSaleForm',
    'AssetDisposalForm',
    'AssetTransferForm',

    # نماذج الصيانة
    'MaintenanceTypeForm',
    'MaintenanceScheduleForm',
    'AssetMaintenanceForm',
    'MaintenanceFilterForm',
]
# apps/assets/models/__init__.py
"""
نماذج تطبيق إدارة الأصول الثابتة
"""

from .asset_models import (
    AssetCategory,
    DepreciationMethod,
    AssetCondition,
    Asset,
    AssetDepreciation,
    AssetAttachment,
    AssetValuation,
)

from .transaction_models import (
    AssetTransaction,
    AssetTransfer,
)

from .maintenance_models import (
    MaintenanceType,
    MaintenanceSchedule,
    AssetMaintenance,
)

__all__ = [
    # النماذج الأساسية
    'AssetCategory',
    'DepreciationMethod',
    'AssetCondition',
    'Asset',
    'AssetDepreciation',
    'AssetAttachment',
    'AssetValuation',

    # العمليات
    'AssetTransaction',
    'AssetTransfer',

    # الصيانة
    'MaintenanceType',
    'MaintenanceSchedule',
    'AssetMaintenance',
]
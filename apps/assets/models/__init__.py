# apps/assets/models/__init__.py

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
    AssetLease,
    LeasePayment,
)

from .maintenance_models import (
    MaintenanceType,
    MaintenanceSchedule,
    AssetMaintenance,
)

from .physical_count_models import (
    PhysicalCountCycle,
    PhysicalCount,
    PhysicalCountLine,
    PhysicalCountAdjustment,
)

from .insurance_models import (
    InsuranceCompany,
    AssetInsurance,
    InsuranceClaim,
)

from .notification_models import (
    NotificationTemplate,
    AssetNotification,
    NotificationSettings,
)

from .workflow_models import (
    ApprovalWorkflow,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalHistory,
)

# ✅ إضافة جديدة
from .accounting_config import AssetAccountingConfiguration

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
    'AssetLease',
    'LeasePayment',

    # الصيانة
    'MaintenanceType',
    'MaintenanceSchedule',
    'AssetMaintenance',

    # الجرد الفعلي
    'PhysicalCountCycle',
    'PhysicalCount',
    'PhysicalCountLine',
    'PhysicalCountAdjustment',

    # التأمين
    'InsuranceCompany',
    'AssetInsurance',
    'InsuranceClaim',

    # الإشعارات
    'NotificationTemplate',
    'AssetNotification',
    'NotificationSettings',

    # سير العمل
    'ApprovalWorkflow',
    'ApprovalLevel',
    'ApprovalRequest',
    'ApprovalHistory',

    # ✅ الإعدادات المحاسبية
    'AssetAccountingConfiguration',
]
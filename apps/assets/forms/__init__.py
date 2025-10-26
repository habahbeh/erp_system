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

from .depreciation_forms import (
    AssetDepreciationForm,
    BulkDepreciationCalculationForm,
    SingleAssetDepreciationCalculationForm,
    ReverseDepreciationForm,
    DepreciationFilterForm,
)

from .insurance_forms import (
    InsuranceCompanyForm,
    AssetInsuranceForm,
    InsuranceClaimForm,
    ClaimApprovalForm,
    ClaimRejectionForm,
    ClaimPaymentForm,
    InsuranceFilterForm,
    ClaimFilterForm,
)

from .physical_count_forms import (
    PhysicalCountCycleForm,
    PhysicalCountForm,
    PhysicalCountLineForm,
    BarcodeCountForm,
    PhysicalCountAdjustmentForm,
    CountFilterForm,
    AdjustmentFilterForm,
    BulkCountLineUpdateForm,
)

from .lease_forms import (
    AssetLeaseForm,
    LeasePaymentForm,
    LeaseTerminationForm,
    LeaseRenewalForm,
    PurchaseOptionForm,
    BulkPaymentProcessingForm,
    LeaseFilterForm,
    PaymentFilterForm,
)

from .workflow_forms import (
    ApprovalWorkflowForm,
    ApprovalLevelForm,
    ApprovalLevelFormSet,
    ApprovalRequestForm,
    ApprovalActionForm,
    ApprovalRequestFilterForm,
    QuickApprovalForm,
    BulkApprovalForm,
    DelegateApprovalForm,
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

    # نماذج الإهلاك
    'AssetDepreciationForm',
    'BulkDepreciationCalculationForm',
    'SingleAssetDepreciationCalculationForm',
    'ReverseDepreciationForm',
    'DepreciationFilterForm',

    # نماذج التأمين
    'InsuranceCompanyForm',
    'AssetInsuranceForm',
    'InsuranceClaimForm',
    'ClaimApprovalForm',
    'ClaimRejectionForm',
    'ClaimPaymentForm',
    'InsuranceFilterForm',
    'ClaimFilterForm',

    # نماذج الجرد الفعلي
    'PhysicalCountCycleForm',
    'PhysicalCountForm',
    'PhysicalCountLineForm',
    'BarcodeCountForm',
    'PhysicalCountAdjustmentForm',
    'CountFilterForm',
    'AdjustmentFilterForm',
    'BulkCountLineUpdateForm',

    # نماذج الإيجار
    'AssetLeaseForm',
    'LeasePaymentForm',
    'LeaseTerminationForm',
    'LeaseRenewalForm',
    'PurchaseOptionForm',
    'BulkPaymentProcessingForm',
    'LeaseFilterForm',
    'PaymentFilterForm',

    # نماذج سير العمل
    'ApprovalWorkflowForm',
    'ApprovalLevelForm',
    'ApprovalLevelFormSet',
    'ApprovalRequestForm',
    'ApprovalActionForm',
    'ApprovalRequestFilterForm',
    'QuickApprovalForm',
    'BulkApprovalForm',
    'DelegateApprovalForm',
]
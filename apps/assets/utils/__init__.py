# apps/assets/utils/__init__.py
"""
استيراد جميع الدوال المساعدة من الملفات المختلفة
"""

# استيراد دوال الإهلاك والقيود
from .depreciation import (
    DepreciationCalculator,
    generate_asset_purchase_journal_entry,
    generate_asset_sale_journal_entry,
    generate_depreciation_journal_entry,
    generate_maintenance_journal_entry,
    calculate_asset_metrics,
)

# استيراد دوال التصدير
try:
    from .export_utils import (
        ExcelExporter,
        PDFExporter,
        format_currency,
        format_date,
    )
except ImportError:
    # إذا لم تكن المكتبات متوفرة
    ExcelExporter = None
    PDFExporter = None
    format_currency = None
    format_date = None

# تصدير كل شيء
__all__ = [
    # دوال الإهلاك
    'DepreciationCalculator',
    'generate_asset_purchase_journal_entry',
    'generate_asset_sale_journal_entry',
    'generate_depreciation_journal_entry',
    'generate_maintenance_journal_entry',
    'calculate_asset_metrics',

    # دوال التصدير
    'ExcelExporter',
    'PDFExporter',
    'format_currency',
    'format_date',
]
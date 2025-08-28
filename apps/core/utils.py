# apps/core/utils.py
"""
Utility functions للمشروع
"""

import string
import random
from django.utils import timezone


def generate_code(prefix='', company=None, length=6):
    """توليد كود فريد"""

    # إنشاء رقم عشوائي
    chars = string.digits + string.ascii_uppercase
    random_part = ''.join(random.choices(chars, k=length))

    # إنشاء الكود النهائي
    if prefix:
        code = f"{prefix}-{random_part}"
    else:
        code = random_part

    return code


def export_to_excel(data, filename='export'):
    """تصدير البيانات إلى Excel"""
    pass  # سيتم تطويره لاحقاً


def export_to_pdf(data, filename='export'):
    """تصدير البيانات إلى PDF"""
    pass  # سيتم تطويره لاحقاً


def export_to_csv(data, filename='export'):
    """تصدير البيانات إلى CSV"""
    pass  # سيتم تطويره لاحقاً
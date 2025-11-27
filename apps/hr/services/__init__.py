# apps/hr/services/__init__.py
"""
خدمات الموارد البشرية
HR Services Package
"""

from .notification_service import HRNotificationService

__all__ = [
    'HRNotificationService',
]

# tests/hr/conftest.py
"""
Shared test fixtures for HR module tests
تهيئة مشتركة لاختبارات وحدة الموارد البشرية
"""

import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model

from apps.core.models import Company, Branch, Currency
from apps.hr.models import (
    Department, JobGrade, JobTitle, Employee,
    HRSettings, SocialSecuritySettings,
)

User = get_user_model()


@pytest.fixture
def test_password():
    """Standard test password"""
    return 'testpass123'

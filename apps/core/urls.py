# apps/core/urls.py
"""
URLs لتطبيق النواة
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('switch-branch/<int:branch_id>/', views.switch_branch, name='switch_branch'),
]
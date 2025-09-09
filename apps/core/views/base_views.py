# إضافة في أعلى الملف
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from ..models import Company, CustomPermission, PermissionGroup

User = get_user_model()


def dashboard(request):
    """لوحة التحكم الرئيسية مع KPIs وإحصائيات"""
    context = {
        'title': _('لوحة التحكم'),
        'today': timezone.now(),

        # إحصائيات أساسية
        'total_users': User.objects.count(),
        'total_companies': Company.objects.filter(is_active=True).count(),
        'active_companies': Company.objects.filter(is_active=True).count(),
        'total_permissions': CustomPermission.objects.filter(is_active=True).count(),
        'permission_groups_count': PermissionGroup.objects.filter(is_active=True).count(),

        # إحصائيات شهرية
        'new_users_this_month': User.objects.filter(
            date_joined__gte=timezone.now().replace(day=1)
        ).count(),

        # بيانات للـ Charts
        'activity_labels': json.dumps(_get_activity_labels()),
        'login_data': json.dumps(_get_login_data()),
        'active_users_data': json.dumps(_get_active_users_data()),
        'permission_categories': json.dumps(_get_permission_categories()),
        'permission_counts': json.dumps(_get_permission_counts()),

        # الأنشطة الأخيرة
        'recent_activities': _get_recent_activities(request.user),
    }

    return render(request, 'core/dashboard.html', context)


def _get_activity_labels():
    """الحصول على تسميات آخر 7 أيام"""
    labels = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        labels.append(date.strftime('%d/%m'))
    return labels


def _get_login_data():
    """بيانات تسجيل الدخول لآخر 7 أيام"""
    # بيانات وهمية للآن - سنستبدلها بالحقيقية لاحقاً
    return [12, 19, 15, 25, 22, 18, 30]


def _get_active_users_data():
    """بيانات المستخدمين النشطين لآخر 7 أيام"""
    data = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        count = User.objects.filter(
            last_login__date=date.date(),
            is_active=True
        ).count()
        data.append(count)
    return data


# def _get_permission_categories():
#     """تصنيفات الصلاحيات"""
#     categories = CustomPermission.objects.values_list('category', flat=True).distinct()
#     return [dict(CustomPermission.CATEGORY_CHOICES).get(cat, cat) for cat in categories]

def _get_permission_categories():
    """تصنيفات الصلاحيات"""
    categories = CustomPermission.objects.values_list('category', flat=True).distinct()
    category_choices = {
        'sales': 'المبيعات',
        'purchases': 'المشتريات',
        'inventory': 'المخازن',
        'accounting': 'المحاسبة',
        'hr': 'الموارد البشرية',
        'reports': 'التقارير',
        'system': 'النظام'
    }
    return [category_choices.get(cat, cat) for cat in categories]


def _get_permission_counts():
    """عدد الصلاحيات لكل تصنيف"""
    categories = CustomPermission.objects.values('category').annotate(
        count=Count('id')
    ).order_by('category')
    return [item['count'] for item in categories]


def _get_recent_activities(user):
    """الأنشطة الأخيرة للمستخدم"""
    activities = []

    # المستخدمين الجدد
    recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).order_by('-date_joined')[:3]

    for u in recent_users:
        activities.append({
            'description': f'انضم المستخدم {u.get_full_name() or u.username} للنظام',
            'icon': 'user-plus',
            'color': 'success',
            'created_at': u.date_joined
        })

    # الشركات الجديدة
    recent_companies = Company.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:2]

    for c in recent_companies:
        activities.append({
            'description': f'تم إضافة شركة {c.name}',
            'icon': 'building',
            'color': 'primary',
            'created_at': c.created_at
        })

    # ترتيب حسب التاريخ
    activities.sort(key=lambda x: x['created_at'], reverse=True)

    return activities[:5]


# Ajax endpoint للتحديث المباشر
@login_required
def dashboard_ajax(request):
    """إرجاع بيانات Dashboard للتحديث المباشر"""
    data = {
        'total_users': User.objects.count(),
        'total_companies': Company.objects.filter(is_active=True).count(),
        'total_permissions': CustomPermission.objects.filter(is_active=True).count(),
        'today_activities': User.objects.filter(
            last_login__date=timezone.now().date()
        ).count(),
    }
    return JsonResponse(data)
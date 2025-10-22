# apps/assets/views/notification_views.py
"""
Views الإشعارات والتنبيهات
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta

from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetDepreciation, AssetMaintenance, MaintenanceSchedule,
    AssetInsurance, AssetLease, LeasePayment
)


@login_required
@permission_required_with_message('assets.view_asset')
def notifications_dashboard(request):
    """لوحة الإشعارات"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    # الصيانة المتأخرة
    overdue_maintenance = MaintenanceSchedule.objects.filter(
        company=request.current_company,
        is_active=True,
        next_maintenance_date__lt=date.today()
    ).select_related('asset').count()

    # الصيانة القريبة (خلال 7 أيام)
    upcoming_maintenance = MaintenanceSchedule.objects.filter(
        company=request.current_company,
        is_active=True,
        next_maintenance_date__gte=date.today(),
        next_maintenance_date__lte=date.today() + timedelta(days=7)
    ).select_related('asset').count()

    # التأمين المنتهي قريباً (خلال 30 يوم)
    expiring_insurance = AssetInsurance.objects.filter(
        company=request.current_company,
        status='active',
        end_date__gte=date.today(),
        end_date__lte=date.today() + timedelta(days=30)
    ).select_related('asset').count()

    # دفعات الإيجار المستحقة
    overdue_lease_payments = LeasePayment.objects.filter(
        lease__company=request.current_company,
        is_paid=False,
        payment_date__lt=date.today()
    ).count()

    # الأصول المتوقفة عن العمل
    inactive_assets = Asset.objects.filter(
        company=request.current_company,
        status='inactive'
    ).count()

    # الأصول تحت الصيانة
    under_maintenance = Asset.objects.filter(
        company=request.current_company,
        status='under_maintenance'
    ).count()

    context = {
        'title': _('الإشعارات والتنبيهات'),
        'overdue_maintenance': overdue_maintenance,
        'upcoming_maintenance': upcoming_maintenance,
        'expiring_insurance': expiring_insurance,
        'overdue_lease_payments': overdue_lease_payments,
        'inactive_assets': inactive_assets,
        'under_maintenance': under_maintenance,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('الإشعارات'), 'url': ''},
        ]
    }

    return render(request, 'assets/notifications/dashboard.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def overdue_maintenance_list(request):
    """قائمة الصيانة المتأخرة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    schedules = MaintenanceSchedule.objects.filter(
        company=request.current_company,
        is_active=True,
        next_maintenance_date__lt=date.today()
    ).select_related('asset', 'maintenance_type').order_by('next_maintenance_date')

    context = {
        'title': _('الصيانة المتأخرة'),
        'schedules': schedules,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('الإشعارات'), 'url': reverse('assets:notifications_dashboard')},
            {'title': _('الصيانة المتأخرة'), 'url': ''},
        ]
    }

    return render(request, 'assets/notifications/overdue_maintenance.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def upcoming_maintenance_list(request):
    """قائمة الصيانة القريبة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    days = int(request.GET.get('days', 30))

    schedules = MaintenanceSchedule.objects.filter(
        company=request.current_company,
        is_active=True,
        next_maintenance_date__gte=date.today(),
        next_maintenance_date__lte=date.today() + timedelta(days=days)
    ).select_related('asset', 'maintenance_type').order_by('next_maintenance_date')

    context = {
        'title': _('الصيانة القريبة'),
        'schedules': schedules,
        'days': days,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('الإشعارات'), 'url': reverse('assets:notifications_dashboard')},
            {'title': _('الصيانة القريبة'), 'url': ''},
        ]
    }

    return render(request, 'assets/notifications/upcoming_maintenance.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def expiring_insurance_list(request):
    """قائمة التأمين المنتهي قريباً"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    days = int(request.GET.get('days', 60))

    insurances = AssetInsurance.objects.filter(
        company=request.current_company,
        status='active',
        end_date__gte=date.today(),
        end_date__lte=date.today() + timedelta(days=days)
    ).select_related('asset', 'insurance_company').order_by('end_date')

    context = {
        'title': _('التأمين المنتهي قريباً'),
        'insurances': insurances,
        'days': days,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('الإشعارات'), 'url': reverse('assets:notifications_dashboard')},
            {'title': _('التأمين المنتهي'), 'url': ''},
        ]
    }

    return render(request, 'assets/notifications/expiring_insurance.html', context)


@login_required
@permission_required_with_message('assets.view_asset')
def overdue_lease_payments_list(request):
    """قائمة دفعات الإيجار المتأخرة"""

    if not hasattr(request, 'current_company') or not request.current_company:
        messages.error(request, 'لا توجد شركة محددة')
        return redirect('assets:dashboard')

    payments = LeasePayment.objects.filter(
        lease__company=request.current_company,
        is_paid=False,
        payment_date__lt=date.today()
    ).select_related('lease', 'lease__asset').order_by('payment_date')

    context = {
        'title': _('دفعات الإيجار المتأخرة'),
        'payments': payments,
        'breadcrumbs': [
            {'title': _('الأصول الثابتة'), 'url': reverse('assets:dashboard')},
            {'title': _('الإشعارات'), 'url': reverse('assets:notifications_dashboard')},
            {'title': _('دفعات متأخرة'), 'url': ''},
        ]
    }

    return render(request, 'assets/notifications/overdue_payments.html', context)


# ==================== Ajax Views ====================

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def notification_count_ajax(request):
    """عدد الإشعارات الجديدة"""

    try:
        # الصيانة المتأخرة
        overdue_maintenance = MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lt=date.today()
        ).count()

        # التأمين المنتهي قريباً
        expiring_insurance = AssetInsurance.objects.filter(
            company=request.current_company,
            status='active',
            end_date__gte=date.today(),
            end_date__lte=date.today() + timedelta(days=30)
        ).count()

        # دفعات الإيجار المتأخرة
        overdue_payments = LeasePayment.objects.filter(
            lease__company=request.current_company,
            is_paid=False,
            payment_date__lt=date.today()
        ).count()

        total = overdue_maintenance + expiring_insurance + overdue_payments

        return JsonResponse({
            'success': True,
            'total': total,
            'overdue_maintenance': overdue_maintenance,
            'expiring_insurance': expiring_insurance,
            'overdue_payments': overdue_payments
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def notification_details_ajax(request):
    """تفاصيل الإشعارات"""

    try:
        # الصيانة المتأخرة
        overdue_maintenance = MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lt=date.today()
        ).select_related('asset')[:5]

        # التأمين المنتهي قريباً
        expiring_insurance = AssetInsurance.objects.filter(
            company=request.current_company,
            status='active',
            end_date__gte=date.today(),
            end_date__lte=date.today() + timedelta(days=30)
        ).select_related('asset')[:5]

        # دفعات الإيجار المتأخرة
        overdue_payments = LeasePayment.objects.filter(
            lease__company=request.current_company,
            is_paid=False,
            payment_date__lt=date.today()
        ).select_related('lease__asset')[:5]

        notifications = []

        # إضافة الصيانة المتأخرة
        for schedule in overdue_maintenance:
            days_overdue = (date.today() - schedule.next_maintenance_date).days
            notifications.append({
                'type': 'maintenance',
                'priority': 'high',
                'title': f'صيانة متأخرة: {schedule.asset.name}',
                'description': f'متأخرة {days_overdue} يوم',
                'url': reverse('assets:schedule_detail', args=[schedule.pk])
            })

        # إضافة التأمين المنتهي
        for insurance in expiring_insurance:
            days_remaining = (insurance.end_date - date.today()).days
            notifications.append({
                'type': 'insurance',
                'priority': 'medium',
                'title': f'تأمين ينتهي: {insurance.asset.name}',
                'description': f'ينتهي بعد {days_remaining} يوم',
                'url': reverse('assets:insurance_detail', args=[insurance.pk])
            })

        # إضافة دفعات الإيجار المتأخرة
        for payment in overdue_payments:
            days_overdue = (date.today() - payment.payment_date).days
            notifications.append({
                'type': 'payment',
                'priority': 'high',
                'title': f'دفعة إيجار متأخرة: {payment.lease.asset.name}',
                'description': f'متأخرة {days_overdue} يوم - المبلغ: {payment.amount:,.2f}',
                'url': reverse('assets:lease_detail', args=[payment.lease.pk])
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
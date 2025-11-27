# apps/hr/views/notification_views.py
"""
واجهات الإشعارات للموارد البشرية
HR Notification Views
"""

from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q

from ..models import HRNotification, NotificationSetting
from ..services import HRNotificationService


class NotificationListView(LoginRequiredMixin, ListView):
    """عرض قائمة الإشعارات"""
    model = HRNotification
    template_name = 'hr/notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        queryset = HRNotification.objects.filter(
            company=self.request.current_company,
            recipient=self.request.user,
            is_active=True
        ).select_related('employee')

        # فلترة حسب الحالة
        status = self.request.GET.get('status', 'all')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'read':
            queryset = queryset.filter(is_read=True)

        # فلترة حسب النوع
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # فلترة حسب الأولوية
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'الإشعارات'
        context['breadcrumbs'] = [
            {'title': 'الموارد البشرية', 'url': '/hr/'},
            {'title': 'الإشعارات', 'url': None}
        ]

        # إحصائيات
        all_notifications = HRNotification.objects.filter(
            company=self.request.current_company,
            recipient=self.request.user,
            is_active=True
        )
        context['stats'] = {
            'total': all_notifications.count(),
            'unread': all_notifications.filter(is_read=False).count(),
            'urgent': all_notifications.filter(priority='urgent', is_read=False).count(),
            'high': all_notifications.filter(priority='high', is_read=False).count(),
        }

        # أنواع الإشعارات للفلترة
        context['notification_types'] = HRNotification.NOTIFICATION_TYPES
        context['priority_choices'] = HRNotification.PRIORITY_CHOICES

        # الفلاتر الحالية
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_priority'] = self.request.GET.get('priority', '')

        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    """تحديد إشعار كمقروء (AJAX)"""

    def post(self, request, pk):
        notification = get_object_or_404(
            HRNotification,
            pk=pk,
            company=request.current_company,
            recipient=request.user
        )
        notification.mark_as_read()
        return JsonResponse({
            'success': True,
            'message': 'تم تحديد الإشعار كمقروء'
        })


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """تحديد جميع الإشعارات كمقروءة (AJAX)"""

    def post(self, request):
        HRNotificationService.mark_all_read(request.user, request.current_company)
        return JsonResponse({
            'success': True,
            'message': 'تم تحديد جميع الإشعارات كمقروءة'
        })


class NotificationDeleteView(LoginRequiredMixin, View):
    """حذف إشعار (AJAX)"""

    def post(self, request, pk):
        notification = get_object_or_404(
            HRNotification,
            pk=pk,
            company=request.current_company,
            recipient=request.user
        )
        notification.is_active = False
        notification.save()
        return JsonResponse({
            'success': True,
            'message': 'تم حذف الإشعار'
        })


class NotificationCountView(LoginRequiredMixin, View):
    """الحصول على عدد الإشعارات غير المقروءة (AJAX)"""

    def get(self, request):
        count = HRNotification.get_unread_count(request.user, request.current_company)
        return JsonResponse({
            'count': count
        })


class NotificationDropdownView(LoginRequiredMixin, View):
    """الحصول على أحدث الإشعارات للقائمة المنسدلة (AJAX)"""

    def get(self, request):
        notifications = HRNotification.get_unread_notifications(
            request.user,
            request.current_company,
            limit=5
        )

        data = [{
            'id': n.id,
            'type': n.notification_type,
            'type_display': n.get_notification_type_display(),
            'title': n.title,
            'message': n.message[:100] + '...' if len(n.message) > 100 else n.message,
            'priority': n.priority,
            'priority_display': n.get_priority_display(),
            'action_url': n.action_url or '#',
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
            'employee': str(n.employee) if n.employee else None,
        } for n in notifications]

        return JsonResponse({
            'notifications': data,
            'total_unread': HRNotification.get_unread_count(request.user, request.current_company)
        })


class GenerateNotificationsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """توليد الإشعارات التلقائية"""
    permission_required = 'hr.can_manage_hr'

    def post(self, request):
        service = HRNotificationService(request.current_company)
        service.generate_all_notifications()
        return JsonResponse({
            'success': True,
            'message': 'تم توليد الإشعارات بنجاح'
        })


class NotificationSettingsView(LoginRequiredMixin, View):
    """إعدادات الإشعارات"""
    template_name = 'hr/notifications/notification_settings.html'

    def get(self, request):
        from django.shortcuts import render
        settings, created = NotificationSetting.objects.get_or_create(
            user=request.user,
            company=request.current_company
        )
        context = {
            'title': 'إعدادات الإشعارات',
            'settings': settings,
            'breadcrumbs': [
                {'title': 'الموارد البشرية', 'url': '/hr/'},
                {'title': 'الإشعارات', 'url': '/hr/notifications/'},
                {'title': 'الإعدادات', 'url': None}
            ]
        }
        return render(request, self.template_name, context)

    def post(self, request):
        settings, created = NotificationSetting.objects.get_or_create(
            user=request.user,
            company=request.current_company
        )

        # تحديث الإعدادات
        settings.notify_contract_expiry = request.POST.get('notify_contract_expiry') == 'on'
        settings.contract_expiry_days = int(request.POST.get('contract_expiry_days', 30))
        settings.notify_leave_balance = request.POST.get('notify_leave_balance') == 'on'
        settings.leave_balance_threshold = int(request.POST.get('leave_balance_threshold', 5))
        settings.notify_leave_requests = request.POST.get('notify_leave_requests') == 'on'
        settings.notify_advance_dues = request.POST.get('notify_advance_dues') == 'on'
        settings.notify_attendance = request.POST.get('notify_attendance') == 'on'
        settings.notify_documents = request.POST.get('notify_documents') == 'on'
        settings.document_expiry_days = int(request.POST.get('document_expiry_days', 30))
        settings.email_notifications = request.POST.get('email_notifications') == 'on'
        settings.save()

        return JsonResponse({
            'success': True,
            'message': 'تم حفظ الإعدادات بنجاح'
        })


__all__ = [
    'NotificationListView',
    'NotificationMarkReadView',
    'NotificationMarkAllReadView',
    'NotificationDeleteView',
    'NotificationCountView',
    'NotificationDropdownView',
    'GenerateNotificationsView',
    'NotificationSettingsView',
]

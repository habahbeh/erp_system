# apps/hr/services/notification_service.py
"""
خدمة إدارة الإشعارات للموارد البشرية
HR Notification Service
"""

from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from django.contrib.auth import get_user_model

from ..models import (
    HRNotification, EmployeeContract, Employee,
    LeaveBalance, Advance, AdvanceInstallment
)

User = get_user_model()


class HRNotificationService:
    """خدمة إنشاء وإدارة إشعارات الموارد البشرية"""

    def __init__(self, company):
        self.company = company

    def generate_all_notifications(self):
        """توليد جميع الإشعارات"""
        self.generate_contract_expiry_notifications()
        self.generate_leave_balance_notifications()
        self.generate_advance_due_notifications()
        self.generate_probation_end_notifications()

    def generate_contract_expiry_notifications(self, days_ahead=30):
        """توليد إشعارات انتهاء العقود"""
        today = timezone.now().date()
        expiry_date = today + timedelta(days=days_ahead)

        # العقود التي ستنتهي قريباً
        expiring_contracts = EmployeeContract.objects.filter(
            company=self.company,
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('employee')

        notifications_created = []
        hr_managers = self._get_hr_managers()

        for contract in expiring_contracts:
            days_remaining = (contract.end_date - today).days

            # تحديد الأولوية
            if days_remaining <= 7:
                priority = 'urgent'
            elif days_remaining <= 14:
                priority = 'high'
            elif days_remaining <= 30:
                priority = 'medium'
            else:
                priority = 'low'

            title = f"عقد الموظف {contract.employee} سينتهي قريباً"
            message = f"عقد الموظف {contract.employee.first_name} {contract.employee.last_name} سينتهي خلال {days_remaining} يوم (تاريخ الانتهاء: {contract.end_date})."

            # إنشاء إشعار لكل مدير HR
            for manager in hr_managers:
                # تجنب التكرار
                existing = HRNotification.objects.filter(
                    company=self.company,
                    notification_type='contract_expiry',
                    recipient=manager,
                    related_object_type='EmployeeContract',
                    related_object_id=contract.id,
                    is_read=False
                ).exists()

                if not existing:
                    notification = HRNotification.objects.create(
                        company=self.company,
                        notification_type='contract_expiry',
                        title=title,
                        message=message,
                        priority=priority,
                        recipient=manager,
                        employee=contract.employee,
                        related_object_type='EmployeeContract',
                        related_object_id=contract.id,
                        action_url=f'/hr/contracts/{contract.id}/'
                    )
                    notifications_created.append(notification)

        return notifications_created

    def generate_leave_balance_notifications(self, threshold=5):
        """توليد إشعارات رصيد الإجازات المنخفض"""
        today = timezone.now().date()
        current_year = today.year

        # أرصدة الإجازات المنخفضة
        low_balances = LeaveBalance.objects.filter(
            employee__company=self.company,
            year=current_year,
            employee__is_active=True,
            employee__status='active'
        ).select_related('employee', 'leave_type')

        notifications_created = []
        hr_managers = self._get_hr_managers()

        for balance in low_balances:
            # حساب الرصيد المتبقي
            total = (balance.opening_balance or 0) + (balance.carried_forward or 0) + (balance.adjustment or 0)
            remaining = total - (balance.used or 0)

            if remaining <= threshold and remaining >= 0:
                title = f"رصيد إجازات منخفض - {balance.employee}"
                message = f"رصيد إجازات {balance.leave_type.name} للموظف {balance.employee.first_name} {balance.employee.last_name} منخفض ({remaining} يوم متبقي)."

                for manager in hr_managers:
                    existing = HRNotification.objects.filter(
                        company=self.company,
                        notification_type='leave_balance_low',
                        recipient=manager,
                        related_object_type='LeaveBalance',
                        related_object_id=balance.id,
                        is_read=False
                    ).exists()

                    if not existing:
                        notification = HRNotification.objects.create(
                            company=self.company,
                            notification_type='leave_balance_low',
                            title=title,
                            message=message,
                            priority='low',
                            recipient=manager,
                            employee=balance.employee,
                            related_object_type='LeaveBalance',
                            related_object_id=balance.id,
                            action_url=f'/hr/leave-balances/?employee={balance.employee.id}'
                        )
                        notifications_created.append(notification)

        return notifications_created

    def generate_advance_due_notifications(self):
        """توليد إشعارات أقساط السلف المستحقة"""
        today = timezone.now().date()
        next_week = today + timedelta(days=7)

        # الأقساط المستحقة خلال أسبوع
        due_installments = AdvanceInstallment.objects.filter(
            advance__employee__company=self.company,
            status='pending',
            due_date__lte=next_week
        ).select_related('advance', 'advance__employee')

        notifications_created = []
        hr_managers = self._get_hr_managers()

        for installment in due_installments:
            days_until_due = (installment.due_date - today).days

            if days_until_due < 0:
                priority = 'urgent'
                title = f"قسط سلفة متأخر - {installment.advance.employee}"
                message = f"قسط سلفة الموظف {installment.advance.employee} متأخر بـ {abs(days_until_due)} يوم. المبلغ: {installment.amount}"
            else:
                priority = 'medium'
                title = f"قسط سلفة مستحق قريباً - {installment.advance.employee}"
                message = f"قسط سلفة الموظف {installment.advance.employee} مستحق خلال {days_until_due} يوم. المبلغ: {installment.amount}"

            for manager in hr_managers:
                existing = HRNotification.objects.filter(
                    company=self.company,
                    notification_type='advance_due',
                    recipient=manager,
                    related_object_type='AdvanceInstallment',
                    related_object_id=installment.id,
                    is_read=False
                ).exists()

                if not existing:
                    notification = HRNotification.objects.create(
                        company=self.company,
                        notification_type='advance_due',
                        title=title,
                        message=message,
                        priority=priority,
                        recipient=manager,
                        employee=installment.advance.employee,
                        related_object_type='AdvanceInstallment',
                        related_object_id=installment.id,
                        action_url=f'/hr/advances/{installment.advance.id}/'
                    )
                    notifications_created.append(notification)

        return notifications_created

    def generate_probation_end_notifications(self, days_ahead=7):
        """توليد إشعارات انتهاء فترة التجربة"""
        today = timezone.now().date()
        end_date = today + timedelta(days=days_ahead)

        # الموظفين الذين ستنتهي فترة تجربتهم
        employees = Employee.objects.filter(
            company=self.company,
            is_active=True,
            status='active',
            probation_end_date__lte=end_date,
            probation_end_date__gte=today
        )

        notifications_created = []
        hr_managers = self._get_hr_managers()

        for employee in employees:
            days_remaining = (employee.probation_end_date - today).days

            title = f"انتهاء فترة التجربة - {employee}"
            message = f"فترة التجربة للموظف {employee.first_name} {employee.last_name} ستنتهي خلال {days_remaining} يوم (تاريخ الانتهاء: {employee.probation_end_date})."

            priority = 'high' if days_remaining <= 3 else 'medium'

            for manager in hr_managers:
                existing = HRNotification.objects.filter(
                    company=self.company,
                    notification_type='probation_end',
                    recipient=manager,
                    employee=employee,
                    is_read=False
                ).exists()

                if not existing:
                    notification = HRNotification.objects.create(
                        company=self.company,
                        notification_type='probation_end',
                        title=title,
                        message=message,
                        priority=priority,
                        recipient=manager,
                        employee=employee,
                        action_url=f'/hr/employees/{employee.id}/'
                    )
                    notifications_created.append(notification)

        return notifications_created

    def create_leave_request_notification(self, leave_request):
        """إنشاء إشعار عند تقديم طلب إجازة"""
        hr_managers = self._get_hr_managers()
        notifications = []

        for manager in hr_managers:
            notification = HRNotification.objects.create(
                company=self.company,
                notification_type='leave_request',
                title=f"طلب إجازة جديد - {leave_request.employee}",
                message=f"قدم الموظف {leave_request.employee.first_name} {leave_request.employee.last_name} طلب إجازة ({leave_request.leave_type.name}) من {leave_request.start_date} إلى {leave_request.end_date}",
                priority='medium',
                recipient=manager,
                employee=leave_request.employee,
                related_object_type='LeaveRequest',
                related_object_id=leave_request.id,
                action_url=f'/hr/leave-requests/{leave_request.id}/'
            )
            notifications.append(notification)

        return notifications

    def _get_hr_managers(self):
        """الحصول على مديري الموارد البشرية"""
        # البحث عن المستخدمين الذين لديهم صلاحيات HR
        return User.objects.filter(
            is_active=True,
            is_staff=True
        ).filter(
            Q(groups__permissions__codename__contains='hr') |
            Q(user_permissions__codename__contains='hr') |
            Q(is_superuser=True)
        ).distinct()[:10]  # الحد الأقصى 10 مستلمين

    @staticmethod
    def mark_notification_read(notification_id, user):
        """تحديد إشعار كمقروء"""
        try:
            notification = HRNotification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.mark_as_read()
            return True
        except HRNotification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_read(user, company):
        """تحديد جميع الإشعارات كمقروءة"""
        HRNotification.objects.filter(
            company=company,
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @staticmethod
    def delete_old_notifications(days=90):
        """حذف الإشعارات القديمة"""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted, _ = HRNotification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()
        return deleted

# apps/sales/views/campaign_views.py
"""
Views لحملات الخصومات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction, models
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime

from apps.sales.models import DiscountCampaign, SalesInvoice
from apps.sales.forms import DiscountCampaignForm


class CampaignListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """عرض قائمة حملات الخصومات"""
    model = DiscountCampaign
    template_name = 'sales/campaigns/campaign_list.html'
    context_object_name = 'campaigns'
    permission_required = 'sales.view_discountcampaign'
    paginate_by = 50

    def get_queryset(self):
        """الحصول على الحملات للشركة الحالية"""
        queryset = DiscountCampaign.objects.filter(
            company=self.request.current_company
        ).prefetch_related('items', 'categories', 'customers')

        # الفلاتر
        campaign_type = self.request.GET.get('campaign_type')
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)

        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')

        status = self.request.GET.get('status')
        if status == 'active':
            # حملات نشطة وضمن الفترة
            now = timezone.now()
            queryset = queryset.filter(
                is_active=True,
                start_date__lte=now.date(),
                end_date__gte=now.date()
            )
        elif status == 'upcoming':
            # حملات قادمة
            queryset = queryset.filter(start_date__gt=date.today())
        elif status == 'expired':
            # حملات منتهية
            queryset = queryset.filter(end_date__lt=date.today())

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search) |
                models.Q(description__icontains=search)
            )

        return queryset.order_by('-priority', '-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حملات الخصومات')

        # إحصائيات
        campaigns = self.get_queryset()
        now = timezone.now()
        today = now.date()

        context['total_campaigns'] = campaigns.count()
        context['active_campaigns'] = campaigns.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).count()
        context['upcoming_campaigns'] = campaigns.filter(start_date__gt=today).count()
        context['expired_campaigns'] = campaigns.filter(end_date__lt=today).count()

        return context


class CampaignCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """إنشاء حملة خصم جديدة"""
    model = DiscountCampaign
    form_class = DiscountCampaignForm
    template_name = 'sales/campaigns/campaign_form.html'
    permission_required = 'sales.add_discountcampaign'
    success_url = reverse_lazy('sales:campaign_list')

    def get_form_kwargs(self):
        """إضافة company للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة حملة خصم جديدة')
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ الحملة"""
        self.object = form.save(commit=False)
        self.object.company = self.request.current_company
        self.object.created_by = self.request.user
        self.object.save()
        form.save_m2m()

        messages.success(
            self.request,
            _('تم إنشاء حملة الخصم "{}" بنجاح').format(self.object.name)
        )
        return redirect(self.success_url)


class CampaignUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل حملة خصم"""
    model = DiscountCampaign
    form_class = DiscountCampaignForm
    template_name = 'sales/campaigns/campaign_form.html'
    permission_required = 'sales.change_discountcampaign'
    success_url = reverse_lazy('sales:campaign_list')

    def get_queryset(self):
        """الحصول على الحملات للشركة الحالية فقط"""
        return DiscountCampaign.objects.filter(company=self.request.current_company)

    def get_form_kwargs(self):
        """إضافة company للـ form"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل حملة الخصم: {}').format(self.object.name)
        return context

    @transaction.atomic
    def form_valid(self, form):
        """حفظ التعديلات"""
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تعديل حملة الخصم "{}" بنجاح').format(self.object.name)
        )
        return redirect(self.success_url)


class CampaignDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """عرض تفاصيل حملة الخصم"""
    model = DiscountCampaign
    template_name = 'sales/campaigns/campaign_detail.html'
    context_object_name = 'campaign'
    permission_required = 'sales.view_discountcampaign'

    def get_queryset(self):
        """الحصول على الحملات للشركة الحالية فقط"""
        return DiscountCampaign.objects.filter(
            company=self.request.current_company
        ).prefetch_related('items', 'categories', 'customers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حملة الخصم: {}').format(self.object.name)

        # حساب الإحصائيات
        now = timezone.now()
        today = now.date()

        # هل الحملة نشطة حالياً؟
        context['is_currently_active'] = (
            self.object.is_active and
            self.object.start_date <= today <= self.object.end_date
        )

        # هل الحملة قادمة؟
        context['is_upcoming'] = self.object.start_date > today

        # هل الحملة منتهية؟
        context['is_expired'] = self.object.end_date < today

        # الأيام المتبقية
        if context['is_currently_active']:
            context['days_remaining'] = (self.object.end_date - today).days
        elif context['is_upcoming']:
            context['days_until_start'] = (self.object.start_date - today).days

        # نسبة الاستخدام
        if self.object.max_uses:
            context['usage_percentage'] = (
                self.object.current_uses / self.object.max_uses * 100
            )
        else:
            context['usage_percentage'] = 0

        # الفواتير المرتبطة بالحملة
        context['related_invoices'] = SalesInvoice.objects.filter(
            company=self.request.current_company,
            discount_campaign=self.object
        ).select_related('customer').order_by('-date')[:10]

        context['related_invoices_count'] = SalesInvoice.objects.filter(
            company=self.request.current_company,
            discount_campaign=self.object
        ).count()

        return context


class CampaignDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف حملة خصم"""
    model = DiscountCampaign
    template_name = 'sales/campaigns/campaign_confirm_delete.html'
    permission_required = 'sales.delete_discountcampaign'
    success_url = reverse_lazy('sales:campaign_list')

    def get_queryset(self):
        """الحصول على الحملات للشركة الحالية فقط"""
        return DiscountCampaign.objects.filter(company=self.request.current_company)

    def delete(self, request, *args, **kwargs):
        """التحقق قبل الحذف"""
        self.object = self.get_object()

        # التحقق من وجود فواتير مرتبطة
        related_invoices = SalesInvoice.objects.filter(
            company=request.current_company,
            discount_campaign=self.object
        ).count()

        if related_invoices > 0:
            messages.warning(
                request,
                _('تحذير: يوجد {} فاتورة مرتبطة بهذه الحملة. يمكنك إلغاء تفعيلها بدلاً من حذفها.').format(
                    related_invoices
                )
            )

        messages.success(
            request,
            _('تم حذف حملة الخصم "{}" بنجاح').format(self.object.name)
        )
        return super().delete(request, *args, **kwargs)


class ToggleCampaignStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """تفعيل/إلغاء تفعيل حملة"""
    permission_required = 'sales.change_discountcampaign'

    def post(self, request, pk):
        """تبديل حالة الحملة"""
        campaign = get_object_or_404(
            DiscountCampaign,
            pk=pk,
            company=request.current_company
        )

        campaign.is_active = not campaign.is_active
        campaign.save()

        status_text = _('تم تفعيل') if campaign.is_active else _('تم إلغاء تفعيل')
        messages.success(
            request,
            _('{}  حملة الخصم "{}" بنجاح').format(status_text, campaign.name)
        )

        return redirect('sales:campaign_detail', pk=campaign.pk)


class GetActiveCampaignsAjax(LoginRequiredMixin, View):
    """الحصول على الحملات النشطة عبر AJAX"""

    def get(self, request):
        """إرجاع الحملات النشطة كـ JSON"""
        customer_id = request.GET.get('customer_id')
        invoice_total = request.GET.get('invoice_total', 0)

        try:
            invoice_total = Decimal(invoice_total)
        except:
            invoice_total = Decimal('0')

        # الحصول على الحملات النشطة
        now = timezone.now()
        today = now.date()

        campaigns = DiscountCampaign.objects.filter(
            company=request.current_company,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).order_by('-priority')

        # فلترة حسب العميل
        if customer_id:
            campaigns = campaigns.filter(
                models.Q(customers__isnull=True) |
                models.Q(customers__id=customer_id)
            ).distinct()

        # فلترة حسب قيمة الفاتورة
        campaigns = campaigns.filter(
            models.Q(min_purchase_amount__isnull=True) |
            models.Q(min_purchase_amount__lte=invoice_total)
        ).filter(
            models.Q(max_purchase_amount__isnull=True) |
            models.Q(max_purchase_amount__gte=invoice_total)
        )

        # فلترة حسب عدد الاستخدامات
        campaigns = campaigns.filter(
            models.Q(max_uses__isnull=True) |
            models.Q(max_uses__gt=models.F('current_uses'))
        )

        # تحويل لـ JSON
        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append({
                'id': campaign.id,
                'code': campaign.code,
                'name': campaign.name,
                'campaign_type': campaign.campaign_type,
                'discount_percentage': str(campaign.discount_percentage),
                'discount_amount': str(campaign.discount_amount),
                'description': campaign.description,
            })

        return JsonResponse({
            'success': True,
            'campaigns': campaigns_data
        })

# apps/assets/views/attachment_views.py
"""
Attachment Views - إدارة مرفقات الأصول
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from datetime import date, datetime
import json
import os

from apps.core.mixins import CompanyMixin, AuditLogMixin
from apps.core.decorators import permission_required_with_message, company_required
from ..models import Asset, AssetAttachment
from ..forms import AssetAttachmentForm


class AssetAttachmentListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ListView):
    """قائمة مرفقات أصل معين"""

    model = AssetAttachment
    template_name = 'assets/attachment/attachment_list.html'
    context_object_name = 'attachments'
    permission_required = 'assets.view_asset'
    paginate_by = 20

    def get_queryset(self):
        self.asset = get_object_or_404(
            Asset,
            pk=self.kwargs['asset_pk'],
            company=self.request.current_company
        )
        return AssetAttachment.objects.filter(
            asset=self.asset
        ).select_related('uploaded_by').order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_attachments = self.get_queryset().count()
        by_type = self.get_queryset().values('attachment_type').annotate(
            count=Count('id')
        )

        context.update({
            'title': f'مرفقات {self.asset.name}',
            'asset': self.asset,
            'can_add': self.request.user.has_perm('assets.change_asset'),
            'can_delete': self.request.user.has_perm('assets.change_asset'),
            'total_attachments': total_attachments,
            'by_type': by_type,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': self.asset.asset_number, 'url': reverse('assets:asset_detail', args=[self.asset.pk])},
                {'title': _('المرفقات'), 'url': ''}
            ],
        })
        return context


class AssetAttachmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """رفع مرفق جديد"""

    model = AssetAttachment
    form_class = AssetAttachmentForm
    template_name = 'assets/attachment/attachment_form.html'
    permission_required = 'assets.change_asset'

    def dispatch(self, request, *args, **kwargs):
        self.asset = get_object_or_404(
            Asset,
            pk=self.kwargs['asset_pk'],
            company=request.current_company
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['asset'] = self.asset
        return kwargs

    def form_valid(self, form):
        form.instance.asset = self.asset
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم رفع المرفق بنجاح')
        return response

    def get_success_url(self):
        return reverse('assets:attachment_list', kwargs={'asset_pk': self.asset.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'رفع مرفق - {self.asset.name}',
            'asset': self.asset,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': self.asset.asset_number, 'url': reverse('assets:asset_detail', args=[self.asset.pk])},
                {'title': _('المرفقات'), 'url': reverse('assets:attachment_list', args=[self.asset.pk])},
                {'title': _('رفع مرفق'), 'url': ''}
            ],
        })
        return context


class AssetAttachmentDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل مرفق"""

    model = AssetAttachment
    template_name = 'assets/attachment/attachment_detail.html'
    context_object_name = 'attachment'
    permission_required = 'assets.view_asset'

    def get_queryset(self):
        return AssetAttachment.objects.filter(
            asset__company=self.request.current_company
        ).select_related('asset', 'uploaded_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # معلومات الملف
        file_size = None
        file_extension = None
        if self.object.file:
            try:
                file_size = self.object.file.size
                file_extension = os.path.splitext(self.object.file.name)[1]
            except:
                pass

        context.update({
            'title': f'مرفق: {self.object.title}',
            'can_delete': self.request.user.has_perm('assets.change_asset'),
            'file_size': file_size,
            'file_extension': file_extension,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('إدارة الأصول'), 'url': reverse('assets:dashboard')},
                {'title': _('الأصول'), 'url': reverse('assets:asset_list')},
                {'title': self.object.asset.asset_number,
                 'url': reverse('assets:asset_detail', args=[self.object.asset.pk])},
                {'title': _('المرفقات'), 'url': reverse('assets:attachment_list', args=[self.object.asset.pk])},
                {'title': self.object.title, 'url': ''}
            ],
        })
        return context


class AssetAttachmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف مرفق"""

    model = AssetAttachment
    template_name = 'assets/attachment/attachment_confirm_delete.html'
    permission_required = 'assets.change_asset'

    def get_queryset(self):
        return AssetAttachment.objects.filter(asset__company=self.request.current_company)

    def get_success_url(self):
        return reverse('assets:attachment_list', kwargs={'asset_pk': self.object.asset.pk})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        title = self.object.title

        # حذف الملف من التخزين
        if self.object.file:
            try:
                self.object.file.delete()
            except:
                pass

        messages.success(request, f'تم حذف المرفق "{title}" بنجاح')
        return super().delete(request, *args, **kwargs)


# Ajax Views

@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def download_attachment(request, pk):
    """تحميل مرفق"""

    try:
        attachment = get_object_or_404(
            AssetAttachment,
            pk=pk,
            asset__company=request.current_company
        )

        if not attachment.file:
            messages.error(request, 'الملف غير موجود')
            return redirect('assets:attachment_list', asset_pk=attachment.asset.pk)

        # تحميل الملف
        response = FileResponse(
            attachment.file.open('rb'),
            as_attachment=True,
            filename=os.path.basename(attachment.file.name)
        )

        return response

    except Exception as e:
        messages.error(request, f'خطأ في تحميل الملف: {str(e)}')
        return redirect('assets:asset_list')


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def view_attachment(request, pk):
    """عرض مرفق في المتصفح"""

    try:
        attachment = get_object_or_404(
            AssetAttachment,
            pk=pk,
            asset__company=request.current_company
        )

        if not attachment.file:
            return HttpResponse('الملف غير موجود', status=404)

        # عرض الملف
        response = FileResponse(
            attachment.file.open('rb'),
            content_type='application/pdf'  # أو حسب نوع الملف
        )

        return response

    except Exception as e:
        return HttpResponse(f'خطأ: {str(e)}', status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_attachments_ajax(request, asset_pk):
    """الحصول على مرفقات أصل - Ajax"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=asset_pk,
            company=request.current_company
        )

        attachments = AssetAttachment.objects.filter(
            asset=asset
        ).select_related('uploaded_by').order_by('-uploaded_at')

        data = []
        for attachment in attachments:
            # معلومات الملف
            file_size = None
            if attachment.file:
                try:
                    file_size = attachment.file.size
                except:
                    pass

            # التنبيه للصلاحية
            is_expired = attachment.is_expired() if attachment.expiry_date else False

            data.append({
                'id': attachment.id,
                'title': attachment.title,
                'attachment_type': attachment.get_attachment_type_display(),
                'file_name': os.path.basename(attachment.file.name) if attachment.file else None,
                'file_size': file_size,
                'issue_date': attachment.issue_date.strftime('%Y-%m-%d') if attachment.issue_date else None,
                'expiry_date': attachment.expiry_date.strftime('%Y-%m-%d') if attachment.expiry_date else None,
                'is_expired': is_expired,
                'uploaded_by': attachment.uploaded_by.get_full_name() if attachment.uploaded_by else None,
                'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'download_url': reverse('assets:download_attachment', args=[attachment.pk]),
                'view_url': reverse('assets:view_attachment', args=[attachment.pk]),
                'detail_url': reverse('assets:attachment_detail', args=[attachment.pk]),
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'total': len(data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.change_asset')
@require_http_methods(["POST"])
def upload_attachment_ajax(request, asset_pk):
    """رفع مرفق - Ajax"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=asset_pk,
            company=request.current_company
        )

        # التحقق من البيانات
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'لم يتم رفع أي ملف'
            })

        file = request.FILES['file']
        title = request.POST.get('title', file.name)
        attachment_type = request.POST.get('attachment_type', 'other')
        description = request.POST.get('description', '')

        # التحقق من حجم الملف (مثلاً 10 MB)
        max_size = 10 * 1024 * 1024  # 10 MB
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'حجم الملف يتجاوز الحد المسموح (10 ميجابايت)'
            })

        # إنشاء المرفق
        attachment = AssetAttachment.objects.create(
            asset=asset,
            title=title,
            attachment_type=attachment_type,
            file=file,
            description=description,
            uploaded_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'تم رفع المرفق بنجاح',
            'data': {
                'id': attachment.id,
                'title': attachment.title,
                'file_name': os.path.basename(attachment.file.name),
                'download_url': reverse('assets:download_attachment', args=[attachment.pk])
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'خطأ في رفع المرفق: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.change_asset')
@require_http_methods(["POST"])
def delete_attachment_ajax(request, pk):
    """حذف مرفق - Ajax"""

    try:
        attachment = get_object_or_404(
            AssetAttachment,
            pk=pk,
            asset__company=request.current_company
        )

        title = attachment.title

        # حذف الملف
        if attachment.file:
            try:
                attachment.file.delete()
            except:
                pass

        attachment.delete()

        return JsonResponse({
            'success': True,
            'message': f'تم حذف المرفق "{title}" بنجاح'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في حذف المرفق: {str(e)}'
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def expired_attachments_ajax(request):
    """المرفقات منتهية الصلاحية"""

    try:
        today = date.today()

        expired_attachments = AssetAttachment.objects.filter(
            asset__company=request.current_company,
            expiry_date__lt=today
        ).select_related('asset', 'uploaded_by').order_by('expiry_date')

        data = []
        for attachment in expired_attachments:
            days_expired = (today - attachment.expiry_date).days

            data.append({
                'id': attachment.id,
                'title': attachment.title,
                'asset_number': attachment.asset.asset_number,
                'asset_name': attachment.asset.name,
                'attachment_type': attachment.get_attachment_type_display(),
                'expiry_date': attachment.expiry_date.strftime('%Y-%m-%d'),
                'days_expired': days_expired,
                'detail_url': reverse('assets:attachment_detail', args=[attachment.pk])
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'total': len(data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def expiring_soon_attachments_ajax(request):
    """المرفقات التي ستنتهي صلاحيتها قريباً (خلال 30 يوم)"""

    try:
        from datetime import timedelta
        today = date.today()
        future_date = today + timedelta(days=30)

        expiring_attachments = AssetAttachment.objects.filter(
            asset__company=request.current_company,
            expiry_date__gte=today,
            expiry_date__lte=future_date
        ).select_related('asset', 'uploaded_by').order_by('expiry_date')

        data = []
        for attachment in expiring_attachments:
            days_remaining = (attachment.expiry_date - today).days

            data.append({
                'id': attachment.id,
                'title': attachment.title,
                'asset_number': attachment.asset.asset_number,
                'asset_name': attachment.asset.name,
                'attachment_type': attachment.get_attachment_type_display(),
                'expiry_date': attachment.expiry_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'detail_url': reverse('assets:attachment_detail', args=[attachment.pk])
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'total': len(data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
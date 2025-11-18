# apps/core/views/uom_import_export_views.py
"""
Views for UoM Import/Export

⭐ NEW Week 2 Day 4
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django import forms

from apps.core.models import UoMGroup, Company
from apps.core.utils.uom_import_export import (
    export_conversions_to_excel,
    import_conversions_from_excel,
    OPENPYXL_AVAILABLE
)


class ExportConversionsView(LoginRequiredMixin, TemplateView):
    """
    Export UoM Conversions to Excel

    ⭐ NEW Week 2 Day 4

    URL: /core/uom-conversions/export/
    """
    template_name = 'core/uom_conversions/export.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all groups for company
        groups = UoMGroup.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context['groups'] = groups
        context['openpyxl_available'] = OPENPYXL_AVAILABLE

        return context

    def post(self, request, *args, **kwargs):
        """Handle export request"""

        if not OPENPYXL_AVAILABLE:
            messages.error(request, _('مكتبة openpyxl غير متوفرة'))
            return self.get(request, *args, **kwargs)

        # Get selected group (optional)
        group_id = request.POST.get('group_id')
        group = None

        if group_id:
            try:
                group = UoMGroup.objects.get(
                    id=group_id,
                    company=request.current_company
                )
            except UoMGroup.DoesNotExist:
                messages.error(request, _('المجموعة غير موجودة'))
                return self.get(request, *args, **kwargs)

        # Export
        try:
            excel_data = export_conversions_to_excel(
                request.current_company,
                group
            )

            # Create response
            filename = f'uom_conversions_{group.code if group else "all"}.xlsx'
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            messages.error(request, f'خطأ في التصدير: {str(e)}')
            return self.get(request, *args, **kwargs)


class ImportConversionsForm(forms.Form):
    """Form for importing conversions"""

    excel_file = forms.FileField(
        label=_('ملف Excel'),
        help_text=_('ارفع ملف Excel يحتوي على التحويلات'),
        required=True
    )

    skip_duplicates = forms.BooleanField(
        label=_('تخطي التحويلات المكررة'),
        help_text=_('إذا كان التحويل موجوداً مسبقاً، تخطيه بدلاً من تحديثه'),
        required=False,
        initial=True
    )


class ImportConversionsView(LoginRequiredMixin, FormView):
    """
    Import UoM Conversions from Excel

    ⭐ NEW Week 2 Day 4

    URL: /core/uom-conversions/import/
    """
    template_name = 'core/uom_conversions/import.html'
    form_class = ImportConversionsForm
    success_url = reverse_lazy('core:uom_conversion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['openpyxl_available'] = OPENPYXL_AVAILABLE
        return context

    def form_valid(self, form):
        """Handle file upload and import"""

        if not OPENPYXL_AVAILABLE:
            messages.error(self.request, _('مكتبة openpyxl غير متوفرة'))
            return self.form_invalid(form)

        excel_file = form.cleaned_data['excel_file']
        skip_duplicates = form.cleaned_data['skip_duplicates']

        try:
            # Read file
            file_data = excel_file.read()

            # Import
            result = import_conversions_from_excel(
                self.request.current_company,
                file_data,
                skip_duplicates
            )

            # Show results
            if result['success']:
                messages.success(
                    self.request,
                    _(f'تم استيراد {result["created"]} تحويل بنجاح')
                )

                if result['skipped'] > 0:
                    messages.info(
                        self.request,
                        _(f'تم تخطي {result["skipped"]} تحويل مكرر')
                    )

                if result['warnings']:
                    for warning in result['warnings'][:5]:  # Show first 5
                        messages.warning(
                            self.request,
                            f"صف {warning.get('row', '?')}: {warning['warning']}"
                        )

            else:
                messages.error(
                    self.request,
                    _(f'فشل الاستيراد. عدد الأخطاء: {len(result["errors"])}')
                )

                # Show errors
                for error in result['errors'][:10]:  # Show first 10
                    messages.error(
                        self.request,
                        f"صف {error.get('row', '?')}: {error['error']}"
                    )

            # Store full results in session for detail view
            self.request.session['import_results'] = result

            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f'خطأ في الاستيراد: {str(e)}')
            return self.form_invalid(form)


class DownloadTemplateView(LoginRequiredMixin, TemplateView):
    """
    Download empty Excel template for importing conversions

    ⭐ NEW Week 2 Day 4

    URL: /core/uom-conversions/download-template/
    """

    def get(self, request, *args, **kwargs):
        """Generate and return template file"""

        if not OPENPYXL_AVAILABLE:
            messages.error(request, _('مكتبة openpyxl غير متوفرة'))
            return HttpResponse('openpyxl not available', status=500)

        try:
            from apps.core.utils.uom_import_export import UoMConversionExporter

            exporter = UoMConversionExporter(request.current_company)

            # Create workbook with template
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Template"

            exporter._create_template_sheet(ws)

            # Save to bytes
            excel_data = exporter.save_to_bytes(wb)

            # Create response
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="uom_conversions_template.xlsx"'

            return response

        except Exception as e:
            messages.error(request, f'خطأ في إنشاء القالب: {str(e)}')
            return HttpResponse(str(e), status=500)


class ImportResultsView(LoginRequiredMixin, TemplateView):
    """
    Show detailed import results

    ⭐ NEW Week 2 Day 4

    URL: /core/uom-conversions/import-results/
    """
    template_name = 'core/uom_conversions/import_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get results from session
        results = self.request.session.get('import_results', {})

        context['results'] = results
        context['has_errors'] = len(results.get('errors', [])) > 0
        context['has_warnings'] = len(results.get('warnings', [])) > 0

        return context

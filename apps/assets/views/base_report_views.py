# apps/assets/views/base_report_views.py
"""
Base Classes للتقارير
- BaseReportView: الفئة الأساسية لكل التقارير
- ExportMixin: دعم التصدير لـ Excel و PDF
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, date
from decimal import Decimal

from apps.core.mixins import CompanyMixin
from apps.assets.utils import ExcelExporter, PDFExporter, format_currency, format_date


class ExportMixin:
    """
    Mixin لدعم التصدير إلى Excel و PDF
    """

    def get_export_filename(self, format='excel'):
        """توليد اسم الملف للتصدير"""
        report_name = getattr(self, 'report_name', 'report')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format == 'excel':
            return f"{report_name}_{timestamp}.xlsx"
        elif format == 'pdf':
            return f"{report_name}_{timestamp}.pdf"
        else:
            return f"{report_name}_{timestamp}.txt"

    def export_to_excel(self, data, headers, title, filename=None):
        """تصدير البيانات إلى Excel"""
        if filename is None:
            filename = self.get_export_filename('excel')

        # إنشاء الـ Exporter
        exporter = ExcelExporter(company_name=self.request.user.company.name)

        # إضافة العنوان
        exporter.add_title(title)
        exporter.add_empty_row()

        # إضافة معلومات التقرير
        exporter.add_info_row('الشركة', self.request.user.company.name)
        exporter.add_info_row('تاريخ التقرير', datetime.now().strftime('%Y-%m-%d %H:%M'))
        exporter.add_info_row('المستخدم', self.request.user.get_full_name())
        exporter.add_empty_row()

        # إضافة فلاتر التقرير
        filters = self.get_report_filters()
        if filters:
            for key, value in filters.items():
                exporter.add_info_row(key, value)
            exporter.add_empty_row()

        # إضافة الرؤوس
        exporter.add_headers(headers)

        # إضافة البيانات
        exporter.add_data_rows(data)

        # إضافة الإجماليات
        summary = self.get_report_summary()
        if summary:
            exporter.add_empty_row()
            exporter.add_summary_row(summary)

        return exporter.get_response(filename)

    def export_to_pdf(self, data, headers, title, filename=None, orientation='portrait'):
        """تصدير البيانات إلى PDF"""
        if filename is None:
            filename = self.get_export_filename('pdf')

        # إنشاء الـ Exporter
        exporter = PDFExporter(
            company_name=self.request.user.company.name,
            orientation=orientation
        )

        # إضافة العنوان
        exporter.add_title(title)

        # إضافة معلومات رأس التقرير
        header_info = {
            'الشركة': self.request.user.company.name,
            'تاريخ التقرير': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'المستخدم': self.request.user.get_full_name(),
        }

        # إضافة الفلاتر
        filters = self.get_report_filters()
        if filters:
            header_info.update(filters)

        exporter.add_header_info(header_info)

        # إضافة الجدول
        table_data = [headers] + data

        # إضافة الإجماليات
        summary = self.get_report_summary()
        if summary:
            table_data.append(summary)

        exporter.add_table(table_data)

        return exporter.get_response(filename)

    def get_report_filters(self):
        """الحصول على الفلاتر المطبقة - يتم تجاوزها في كل تقرير"""
        return {}

    def get_report_summary(self):
        """الحصول على صف الإجماليات - يتم تجاوزها في كل تقرير"""
        return None


class BaseReportView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, ExportMixin, TemplateView):
    """الفئة الأساسية لجميع التقارير"""

    template_name = 'assets/reports/base_report.html'
    permission_required = 'assets.view_asset'
    report_name = 'asset_report'
    report_title = 'تقرير الأصول'

    def get_context_data(self, **kwargs):
        """بناء سياق الصفحة"""
        context = super().get_context_data(**kwargs)

        # معلومات التقرير
        context.update({
            'title': self.report_title,
            'report_name': self.report_name,
            'breadcrumbs': self.get_breadcrumbs(),
            'can_export': self.request.user.has_perm('assets.view_asset'),
        })

        # الفلاتر
        filters = self.get_filters_from_request()
        context['filters'] = filters

        # البيانات
        queryset = self.get_report_queryset(filters)
        context['report_data'] = self.prepare_report_data(queryset)

        # الإحصائيات
        context['report_stats'] = self.get_report_statistics(queryset)

        return context

    def get(self, request, *args, **kwargs):
        """معالجة GET request"""
        # التحقق من طلب التصدير
        export_format = request.GET.get('export')

        if export_format in ['excel', 'pdf']:
            return self.handle_export(export_format)

        # عرض الصفحة عادي
        return super().get(request, *args, **kwargs)

    def handle_export(self, format):
        """معالجة طلب التصدير"""
        # الحصول على الفلاتر
        filters = self.get_filters_from_request()

        # الحصول على البيانات
        queryset = self.get_report_queryset(filters)

        # تحضير البيانات للتصدير
        headers = self.get_export_headers()
        data = self.prepare_export_data(queryset)

        # التصدير
        if format == 'excel':
            return self.export_to_excel(
                data=data,
                headers=headers,
                title=self.report_title
            )
        elif format == 'pdf':
            orientation = getattr(self, 'pdf_orientation', 'portrait')
            return self.export_to_pdf(
                data=data,
                headers=headers,
                title=self.report_title,
                orientation=orientation
            )

    def get_breadcrumbs(self):
        """بناء مسار التنقل"""
        from django.urls import reverse

        return [
            {'title': 'الرئيسية', 'url': reverse('core:dashboard')},
            {'title': 'الأصول', 'url': reverse('assets:dashboard')},
            {'title': 'التقارير', 'url': '#'},
            {'title': self.report_title, 'url': ''},
        ]

    def get_filters_from_request(self):
        """استخراج الفلاتر من الـ Request"""
        filters = {}

        # فلاتر مشتركة
        if self.request.GET.get('date_from'):
            filters['date_from'] = self.request.GET.get('date_from')

        if self.request.GET.get('date_to'):
            filters['date_to'] = self.request.GET.get('date_to')

        if self.request.GET.get('category'):
            filters['category_id'] = self.request.GET.get('category')

        if self.request.GET.get('branch'):
            filters['branch_id'] = self.request.GET.get('branch')

        return filters

    def get_report_queryset(self, filters):
        """الحصول على QuerySet - يجب تجاوزها في كل تقرير"""
        raise NotImplementedError('يجب تنفيذ get_report_queryset في التقرير')

    def prepare_report_data(self, queryset):
        """تحضير بيانات التقرير للعرض"""
        return list(queryset)

    def get_report_statistics(self, queryset):
        """حساب الإحصائيات"""
        return {}

    def get_export_headers(self):
        """رؤوس الأعمدة للتصدير - يجب تجاوزها"""
        raise NotImplementedError('يجب تنفيذ get_export_headers في التقرير')

    def prepare_export_data(self, queryset):
        """تحضير البيانات للتصدير - يجب تجاوزها"""
        raise NotImplementedError('يجب تنفيذ prepare_export_data في التقرير')
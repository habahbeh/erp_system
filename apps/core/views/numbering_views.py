# apps/core/views/numbering_views.py
"""
Views لتسلسل الترقيم
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView, TemplateView
from django.shortcuts import get_object_or_404

from ..models import NumberingSequence
from ..forms.numbering_forms import NumberingSequenceForm
from ..mixins import CompanyMixin, AuditLogMixin


class NumberingSequenceListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """عرض جميع تسلسلات الترقيم للشركة"""
    template_name = 'core/numbering/numbering_list.html'
    permission_required = 'core.view_numberingsequence'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على الشركة الحالية
        if hasattr(self.request, 'current_company') and self.request.current_company:
            company = self.request.current_company
        elif hasattr(self.request.user, 'company') and self.request.user.company:
            company = self.request.user.company
        else:
            from ..models import Company
            company = Company.objects.first()

        # الحصول على جميع التسلسلات للشركة
        sequences = NumberingSequence.objects.filter(company=company).order_by('document_type')

        # تجميع التسلسلات حسب النوع
        sequence_dict = {seq.document_type: seq for seq in sequences}

        # إنشاء قائمة بجميع أنواع المستندات مع التسلسلات الموجودة
        all_sequences = []
        for doc_type, doc_name in NumberingSequence.DOCUMENT_TYPES:
            sequence = sequence_dict.get(doc_type)
            all_sequences.append({
                'type': doc_type,
                'name': doc_name,
                'sequence': sequence,
                'has_sequence': sequence is not None,
                'preview': sequence.get_next_number() if sequence else _('غير محدد'),
            })

        context.update({
            'title': _('إدارة تسلسل الترقيم'),
            'sequences': all_sequences,
            'can_change': self.request.user.has_perm('core.change_numberingsequence'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تسلسل الترقيم'), 'url': ''}
            ],
            'company': company,
        })
        return context


class NumberingSequenceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل تسلسل ترقيم أو إنشاء جديد"""
    model = NumberingSequence
    form_class = NumberingSequenceForm
    template_name = 'core/numbering/numbering_form.html'
    permission_required = 'core.change_numberingsequence'
    success_url = reverse_lazy('core:numbering_list')

    def get_object(self):
        """الحصول على التسلسل أو إنشاء جديد"""
        document_type = self.kwargs.get('document_type')

        if hasattr(self.request, 'current_company') and self.request.current_company:
            company = self.request.current_company
        elif hasattr(self.request.user, 'company') and self.request.user.company:
            company = self.request.user.company
        else:
            from ..models import Company
            company = Company.objects.first()

        # البحث عن التسلسل الموجود أو إنشاء جديد
        sequence, created = NumberingSequence.objects.get_or_create(
            company=company,
            document_type=document_type,
            defaults={
                'prefix': self.get_default_prefix(document_type),
                'next_number': 1,
                'padding': 6,
                'yearly_reset': True,
                'include_year': True,
                'include_month': False,
                'separator': '/',
                'created_by': self.request.user
            }
        )

        return sequence

    def get_default_prefix(self, document_type):
        """الحصول على البادئة الافتراضية حسب نوع المستند"""
        prefixes = {
            'sales_invoice': 'INV',
            'sales_return': 'SR',
            'sales_quotation': 'QUO',
            'sales_order': 'SO',
            'purchase_invoice': 'PI',
            'purchase_return': 'PR',
            'purchase_order': 'PO',
            'purchase_request': 'REQ',
            'stock_in': 'SI',
            'stock_out': 'SO',
            'stock_transfer': 'ST',
            'stock_count': 'SC',
            'journal_entry': 'JE',
            'payment_voucher': 'PV',
            'receipt_voucher': 'RV',
        }
        return prefixes.get(document_type, 'DOC')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['document_type'] = self.kwargs.get('document_type')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_type = self.kwargs.get('document_type')

        # الحصول على اسم نوع المستند
        doc_name = dict(NumberingSequence.DOCUMENT_TYPES).get(document_type, document_type)

        context.update({
            'title': _('إعداد ترقيم: %(doc_name)s') % {'doc_name': doc_name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تسلسل الترقيم'), 'url': reverse('core:numbering_list')},
                {'title': _('إعداد'), 'url': ''}
            ],
            'submit_text': _('حفظ الإعدادات'),
            'cancel_url': reverse('core:numbering_list'),
            'document_type': document_type,
            'document_name': doc_name,
            'is_new': getattr(self.object, '_created', False),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        doc_name = dict(NumberingSequence.DOCUMENT_TYPES).get(self.kwargs.get('document_type'))
        messages.success(
            self.request,
            _('تم حفظ إعدادات ترقيم "%(doc_name)s" بنجاح') % {'doc_name': doc_name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)
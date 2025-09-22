# في apps/accounting/views/advanced_search.py - ملف جديد

class AdvancedAccountSearchView(LoginRequiredMixin, CompanyMixin, TemplateView):
    """البحث المتقدم في الحسابات"""
    template_name = 'accounting/search/advanced_account_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # معاملات البحث
        search_params = {
            'code': self.request.GET.get('code', ''),
            'name': self.request.GET.get('name', ''),
            'account_type': self.request.GET.get('account_type', ''),
            'parent': self.request.GET.get('parent', ''),
            'level': self.request.GET.get('level', ''),
            'has_balance': self.request.GET.get('has_balance', ''),
            'balance_range_min': self.request.GET.get('balance_range_min', ''),
            'balance_range_max': self.request.GET.get('balance_range_max', ''),
        }

        # بناء الاستعلام
        queryset = Account.objects.filter(company=self.request.current_company)

        if search_params['code']:
            queryset = queryset.filter(code__icontains=search_params['code'])

        if search_params['name']:
            queryset = queryset.filter(name__icontains=search_params['name'])

        if search_params['account_type']:
            queryset = queryset.filter(account_type_id=search_params['account_type'])

        if search_params['level']:
            queryset = queryset.filter(level=search_params['level'])

        if search_params['has_balance'] == '1':
            queryset = queryset.exclude(opening_balance=0)
        elif search_params['has_balance'] == '0':
            queryset = queryset.filter(opening_balance=0)

        # نطاق الرصيد
        if search_params['balance_range_min']:
            queryset = queryset.filter(
                opening_balance__gte=Decimal(search_params['balance_range_min'])
            )
        if search_params['balance_range_max']:
            queryset = queryset.filter(
                opening_balance__lte=Decimal(search_params['balance_range_max'])
            )

        # النتائج مع التحسين
        results = queryset.select_related(
            'account_type', 'parent', 'currency'
        ).order_by('code')[:100]  # حد أقصى 100 نتيجة

        context.update({
            'search_params': search_params,
            'results': results,
            'results_count': results.count(),
            'account_types': AccountType.objects.all(),
        })

        return context
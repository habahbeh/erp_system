# apps/core/views/ajax_views.py
"""
Ajax Views للاستجابة السريعة
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _

from ..models import Item, BusinessPartner, ItemCategory, Brand
from ..decorators import permission_required_with_message


@login_required
@permission_required_with_message('core.view_item')
@require_http_methods(["GET"])
def item_datatable_ajax(request):
    """Ajax endpoint للـ DataTable مع تشخيص المشاكل"""
    try:
        # تشخيص المشاكل
        debug_info = {
            'user': str(request.user),
            'is_authenticated': request.user.is_authenticated,
            'current_company': str(getattr(request, 'current_company', 'None')),
            'has_permission': request.user.has_perm('core.view_item'),
        }

        # إذا لم يكن هناك شركة حالية، استخدم شركة المستخدم
        if not hasattr(request, 'current_company') or not request.current_company:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                # استخدم أول شركة متاحة للتجريب
                from apps.core.models import Company
                request.current_company = Company.objects.first()

        # معالجة طلبات تحميل خيارات الفلاتر
        if request.GET.get('get_categories'):
            categories = ItemCategory.objects.filter(
                company=request.current_company,
                is_active=True
            ).values('id', 'name').order_by('name')
            return JsonResponse({'categories': list(categories)})

        if request.GET.get('get_brands'):
            brands = Brand.objects.filter(
                company=request.current_company,
                is_active=True
            ).values('id', 'name').order_by('name')
            return JsonResponse({'brands': list(brands)})

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        category_filter = request.GET.get('category', '')
        brand_filter = request.GET.get('brand', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات - تجريب بدون فلترة الشركة أولاً
        if request.current_company:
            queryset = Item.objects.filter(company=request.current_company)
        else:
            # للتجريب - جلب جميع الأصناف
            queryset = Item.objects.all()

        queryset = queryset.select_related('category', 'brand', 'unit_of_measure', 'currency')

        debug_info['queryset_count'] = queryset.count()
        debug_info['company_filter'] = str(request.current_company)

        # تطبيق الفلاتر المخصصة
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        if brand_filter:
            queryset = queryset.filter(brand_id=brand_filter)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(sku__icontains=search_value) |
                Q(barcode__icontains=search_value) |
                Q(short_description__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = Item.objects.filter(company=request.current_company).count()
        else:
            records_total = Item.objects.count()

        records_filtered = queryset.count()

        debug_info['records_total'] = records_total
        debug_info['records_filtered'] = records_filtered

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'category__name', 'brand__name', 'unit_of_measure__name', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        items = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for item in items:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_item')
            can_delete = request.user.has_perm('core.delete_item')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:item_detail', kwargs={'pk': item.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:item_update', kwargs={'pk': item.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:item_delete', kwargs={'pk': item.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا الصنف؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود والباركود
                f'<div><code class="text-primary fw-bold">{item.code}</code>' +
                (
                    f'<br><small class="text-muted"><i class="fas fa-barcode"></i> {item.barcode}</small>' if item.barcode else '') + '</div>',

                # اسم الصنف
                f'<div><strong class="text-dark">{item.name}</strong>' +
                (f'<br><small class="text-muted">{item.name_en}</small>' if item.name_en else '') + '</div>',

                # التصنيف
                f'<span class="badge bg-secondary fs-6">{item.category.name}</span>' if item.category
                else '<span class="text-muted">-</span>',

                # العلامة التجارية
                f'<span class="text-dark">{item.brand.name}</span>' if item.brand
                else '<span class="text-muted">-</span>',

                # وحدة القياس
                f'<span class="badge bg-light text-dark">{item.unit_of_measure.name}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if item.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        # الاستجابة مع معلومات التشخيص
        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'debug': debug_info  # إضافة معلومات التشخيص
        }

        return JsonResponse(response)

    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'draw': draw if 'draw' in locals() else 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        }, status=500)


@login_required
def partner_autocomplete(request):
    """البحث السريع في الشركاء التجاريين"""
    term = request.GET.get('term', '').strip()

    if len(term) < 2:
        return JsonResponse([])

    partners = BusinessPartner.objects.filter(
        company=request.current_company,
        is_active=True
    ).filter(
        Q(name__icontains=term) |
        Q(name_en__icontains=term) |
        Q(code__icontains=term)
    )[:10]

    results = []
    for partner in partners:
        results.append({
            'id': partner.id,
            'text': f"{partner.code} - {partner.name}",
            'type': partner.get_partner_type_display()
        })

    return JsonResponse(results, safe=False)


@login_required
def item_autocomplete(request):
    """البحث السريع في الأصناف"""
    term = request.GET.get('term', '').strip()

    if len(term) < 2:
        return JsonResponse([])

    items = Item.objects.filter(
        company=request.current_company,
        is_active=True
    ).filter(
        Q(name__icontains=term) |
        Q(name_en__icontains=term) |
        Q(code__icontains=term) |
        Q(barcode__icontains=term) |
        Q(sku__icontains=term)
    ).select_related('unit_of_measure', 'currency')[:10]

    results = []
    for item in items:
        results.append({
            'id': item.id,
            'text': f"{item.code} - {item.name}",
            'price': float(item.sale_price),
            'unit': item.unit_of_measure.name,
            'currency': item.currency.symbol
        })

    return JsonResponse(results, safe=False)


@login_required
def get_item_details(request, item_id):
    """الحصول على تفاصيل صنف معين"""
    try:
        item = Item.objects.select_related(
            'category', 'brand', 'unit_of_measure', 'currency'
        ).get(
            id=item_id,
            company=request.current_company
        )

        data = {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'name_en': item.name_en,
            'barcode': item.barcode,
            'sku': item.sku,
            'tax_rate': float(item.tax_rate),
            'unit': item.unit_of_measure.name,
            'currency_symbol': item.currency.symbol,
            'category': item.category.name if item.category else None,
            'brand': item.brand.name if item.brand else None,
            'has_variants': item.has_variants,
            'is_active': item.is_active,
        }

        return JsonResponse(data)

    except Item.DoesNotExist:
        return JsonResponse({'error': _('الصنف غير موجود')}, status=404)

@login_required
def check_barcode(request):
    """التحقق من تفرد الباركود"""
    barcode = request.GET.get('barcode', '').strip()
    item_id = request.GET.get('item_id')

    if not barcode:
        return JsonResponse({'available': True})

    queryset = Item.objects.filter(
        company=request.current_company,
        barcode=barcode
    )

    # استثناء الصنف الحالي في حالة التعديل
    if item_id:
        try:
            queryset = queryset.exclude(id=int(item_id))
        except (ValueError, TypeError):
            pass

    is_available = not queryset.exists()

    return JsonResponse({
        'available': is_available,
        'message': _('الباركود متاح') if is_available else _('الباركود مستخدم مسبقاً')
    })
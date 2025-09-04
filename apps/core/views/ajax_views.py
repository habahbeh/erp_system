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

from ..models import Item, BusinessPartner, ItemCategory, Brand, Warehouse, UnitOfMeasure, Currency
from ..decorators import permission_required_with_message
from django.contrib.auth import get_user_model

User = get_user_model()

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
            # 'price': float(item.sale_price),
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




"""
Ajax Views للشركاء التجاريين
"""

@login_required
@permission_required_with_message('core.view_businesspartner')
@require_http_methods(["GET"])
def partner_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للشركاء التجاريين"""
    try:
        # إذا لم يكن هناك شركة حالية، استخدم شركة المستخدم
        if not hasattr(request, 'current_company') or not request.current_company:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                from apps.core.models import Company
                request.current_company = Company.objects.first()

        # معالجة طلبات تحميل خيارات الفلاتر
        if request.GET.get('get_representatives'):
            representatives = User.objects.filter(
                company=request.current_company,
                is_active=True
            ).values('id', 'first_name', 'last_name').order_by('first_name', 'last_name')

            # تنسيق البيانات
            reps_data = []
            for rep in representatives:
                full_name = f"{rep['first_name']} {rep['last_name']}".strip()
                if not full_name:
                    full_name = f"مستخدم {rep['id']}"
                reps_data.append({
                    'id': rep['id'],
                    'name': full_name
                })

            return JsonResponse({'representatives': reps_data})

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        partner_type_filter = request.GET.get('partner_type', '')
        account_type_filter = request.GET.get('account_type', '')
        representative_filter = request.GET.get('representative', '')
        tax_status_filter = request.GET.get('tax_status', '')
        city_filter = request.GET.get('city', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = BusinessPartner.objects.filter(company=request.current_company)
        else:
            queryset = BusinessPartner.objects.all()

        queryset = queryset.select_related('sales_representative')

        # تطبيق الفلاتر المخصصة
        if partner_type_filter:
            queryset = queryset.filter(partner_type=partner_type_filter)

        if account_type_filter:
            queryset = queryset.filter(account_type=account_type_filter)

        if representative_filter:
            queryset = queryset.filter(sales_representative_id=representative_filter)

        if tax_status_filter:
            queryset = queryset.filter(tax_status=tax_status_filter)

        if city_filter:
            queryset = queryset.filter(city__icontains=city_filter)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(contact_person__icontains=search_value) |
                Q(phone__icontains=search_value) |
                Q(mobile__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(tax_number__icontains=search_value) |
                Q(address__icontains=search_value) |
                Q(city__icontains=search_value) |
                Q(region__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = BusinessPartner.objects.filter(company=request.current_company).count()
        else:
            records_total = BusinessPartner.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'partner_type', 'account_type', 'sales_representative__first_name', 'phone',
                   'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        partners = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for partner in partners:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_businesspartner')
            can_delete = request.user.has_perm('core.delete_businesspartner')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:partner_detail', kwargs={'pk': partner.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:partner_update', kwargs={'pk': partner.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:partner_delete', kwargs={'pk': partner.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا الشريك؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود
                f'<code class="text-primary fw-bold">{partner.code}</code>',

                # اسم الشريك
                f'<div><strong class="text-dark">{partner.name}</strong>' +
                (f'<br><small class="text-muted">{partner.name_en}</small>' if partner.name_en else '') + '</div>',

                # نوع الشريك
                f'<span class="badge bg-primary fs-6">{partner.get_partner_type_display()}</span>',

                # نوع الحساب
                f'<span class="badge bg-secondary fs-6">{partner.get_account_type_display()}</span>',

                # المندوب
                f'<span class="text-dark">{partner.sales_representative.get_full_name()}</span>' if partner.sales_representative
                else '<span class="text-muted">-</span>',

                # الهاتف
                f'<div>' +
                (f'<div><i class="fas fa-phone"></i> {partner.phone}</div>' if partner.phone else '') +
                (f'<div><i class="fas fa-mobile-alt"></i> {partner.mobile}</div>' if partner.mobile else '') +
                '</div>' if partner.phone or partner.mobile else '<span class="text-muted">-</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if partner.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
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



# أضف هذا في نهاية ملف apps/core/views/ajax_views.py

@login_required
@permission_required_with_message('core.view_warehouse')
@require_http_methods(["GET"])
def warehouse_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للمستودعات"""
    try:
        # إذا لم يكن هناك شركة حالية، استخدم شركة المستخدم
        if not hasattr(request, 'current_company') or not request.current_company:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                from apps.core.models import Company
                request.current_company = Company.objects.first()

        # معالجة طلبات تحميل خيارات الفلاتر
        if request.GET.get('get_managers'):
            managers = User.objects.filter(
                company=request.current_company,
                is_active=True
            ).values('id', 'first_name', 'last_name').order_by('first_name', 'last_name')

            # تنسيق البيانات
            managers_data = []
            for manager in managers:
                full_name = f"{manager['first_name']} {manager['last_name']}".strip()
                if not full_name:
                    full_name = f"مستخدم {manager['id']}"
                managers_data.append({
                    'id': manager['id'],
                    'name': full_name
                })

            return JsonResponse({'managers': managers_data})

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        manager_filter = request.GET.get('manager', '')
        is_main_filter = request.GET.get('is_main', '')
        allow_negative_filter = request.GET.get('allow_negative', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = Warehouse.objects.filter(company=request.current_company)
        else:
            queryset = Warehouse.objects.all()

        queryset = queryset.select_related('manager')

        # تطبيق الفلاتر المخصصة
        if manager_filter:
            queryset = queryset.filter(manager_id=manager_filter)

        if is_main_filter:
            is_main = is_main_filter == '1'
            queryset = queryset.filter(is_main=is_main)

        if allow_negative_filter:
            allow_negative = allow_negative_filter == '1'
            queryset = queryset.filter(allow_negative_stock=allow_negative)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(address__icontains=search_value) |
                Q(phone__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = Warehouse.objects.filter(company=request.current_company).count()
        else:
            records_total = Warehouse.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'manager__first_name', 'is_main', 'allow_negative_stock', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        warehouses = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for warehouse in warehouses:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_warehouse')
            can_delete = request.user.has_perm('core.delete_warehouse')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:warehouse_detail', kwargs={'pk': warehouse.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:warehouse_update', kwargs={'pk': warehouse.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:warehouse_delete', kwargs={'pk': warehouse.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا المستودع؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود
                f'<code class="text-primary fw-bold">{warehouse.code}</code>',

                # اسم المستودع
                f'<div><strong class="text-dark">{warehouse.name}</strong>' +
                (f'<br><small class="text-muted">{warehouse.name_en}</small>' if warehouse.name_en else '') + '</div>',

                # المدير
                f'<span class="text-dark">{warehouse.manager.get_full_name()}</span>' if warehouse.manager
                else '<span class="text-muted">-</span>',

                # مستودع رئيسي
                f'<span class="badge bg-warning"><i class="fas fa-star"></i> {_("رئيسي")}</span>' if warehouse.is_main
                else f'<span class="badge bg-secondary">{_("فرعي")}</span>',

                # السماح بالسالب
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نعم")}</span>' if warehouse.allow_negative_stock
                else f'<span class="badge bg-danger"><i class="fas fa-times"></i> {_("لا")}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if warehouse.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
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
@permission_required_with_message('core.view_brand')
@require_http_methods(["GET"])
def brand_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للعلامات التجارية"""
    try:
        # إذا لم يكن هناك شركة حالية، استخدم شركة المستخدم
        if not hasattr(request, 'current_company') or not request.current_company:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                from apps.core.models import Company
                request.current_company = Company.objects.first()

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        country_filter = request.GET.get('country', '')
        has_logo_filter = request.GET.get('has_logo', '')
        has_website_filter = request.GET.get('has_website', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = Brand.objects.filter(company=request.current_company)
        else:
            queryset = Brand.objects.all()

        # تطبيق الفلاتر المخصصة
        if country_filter:
            queryset = queryset.filter(country__icontains=country_filter)

        if has_logo_filter:
            if has_logo_filter == '1':
                queryset = queryset.exclude(logo__exact='')
            elif has_logo_filter == '0':
                queryset = queryset.filter(logo__exact='')

        if has_website_filter:
            if has_website_filter == '1':
                queryset = queryset.exclude(website__exact='')
            elif has_website_filter == '0':
                queryset = queryset.filter(website__exact='')

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(description__icontains=search_value) |
                Q(country__icontains=search_value) |
                Q(website__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = Brand.objects.filter(company=request.current_company).count()
        else:
            records_total = Brand.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['name', 'name_en', 'country', 'website', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        brands = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for brand in brands:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_brand')
            can_delete = request.user.has_perm('core.delete_brand')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:brand_detail', kwargs={'pk': brand.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:brand_update', kwargs={'pk': brand.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:brand_delete', kwargs={'pk': brand.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه العلامة التجارية؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # اسم العلامة التجارية
                f'<div><strong class="text-dark">{brand.name}</strong>' +
                (f'<br><small class="text-muted">{brand.name_en}</small>' if brand.name_en else '') + '</div>',

                # بلد المنشأ
                f'<span class="text-dark">{brand.country}</span>' if brand.country
                else '<span class="text-muted">-</span>',

                # الشعار
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نعم")}</span>' if brand.logo
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("لا")}</span>',

                # الموقع الإلكتروني
                f'<a href="{brand.website}" target="_blank" class="text-decoration-none"><i class="fas fa-external-link-alt"></i> {_("زيارة")}</a>' if brand.website
                else '<span class="text-muted">-</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if brand.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
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
@permission_required_with_message('core.view_unitofmeasure')
@require_http_methods(["GET"])
def unit_datatable_ajax(request):
    """Ajax endpoint للـ DataTable لوحدات القياس"""
    try:
        # إذا لم يكن هناك شركة حالية، استخدم شركة المستخدم
        if not hasattr(request, 'current_company') or not request.current_company:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
            else:
                from apps.core.models import Company
                request.current_company = Company.objects.first()

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = UnitOfMeasure.objects.filter(company=request.current_company)
        else:
            queryset = UnitOfMeasure.objects.all()

        # تطبيق الفلاتر المخصصة
        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(code__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = UnitOfMeasure.objects.filter(company=request.current_company).count()
        else:
            records_total = UnitOfMeasure.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'name_en', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        units = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for unit in units:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_unitofmeasure')
            can_delete = request.user.has_perm('core.delete_unitofmeasure')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:unit_detail', kwargs={'pk': unit.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:unit_update', kwargs={'pk': unit.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:unit_delete', kwargs={'pk': unit.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه الوحدة؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الرمز
                f'<code class="bg-light text-primary fw-bold px-2 py-1 rounded">{unit.code}</code>',

                # اسم الوحدة
                f'<div><strong class="text-dark">{unit.name}</strong>' +
                (f'<br><small class="text-muted">{unit.name_en}</small>' if unit.name_en else '') + '</div>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if unit.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
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
@permission_required_with_message('core.view_currency')
@require_http_methods(["GET"])
def currency_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للعملات"""
    try:
        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        is_base_filter = request.GET.get('is_base', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        queryset = Currency.objects.all()

        # تطبيق الفلاتر المخصصة
        if is_base_filter:
            is_base = is_base_filter == '1'
            queryset = queryset.filter(is_base=is_base)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(symbol__icontains=search_value)
            )

        # العدد الكلي
        records_total = Currency.objects.count()
        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'symbol', 'exchange_rate', 'is_base', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        currencies = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for currency in currencies:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_currency')
            can_delete = request.user.has_perm('core.delete_currency')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:currency_detail', kwargs={'pk': currency.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:currency_update', kwargs={'pk': currency.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف (ممنوع للعملة الأساسية)
            if can_delete and not currency.is_base:
                actions += f'''
                    <a href="{reverse('core:currency_delete', kwargs={'pk': currency.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه العملة؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الرمز
                f'<code class="bg-light text-primary fw-bold px-2 py-1 rounded">{currency.code}</code>',

                # اسم العملة
                f'<div><strong class="text-dark">{currency.name}</strong>' +
                (f'<br><small class="text-muted">{currency.name_en}</small>' if currency.name_en else '') + '</div>',

                # الرمز
                f'<span class="badge bg-info fs-6">{currency.symbol}</span>',

                # سعر الصرف
                f'<span class="text-dark">{currency.exchange_rate:,.4f}</span>',

                # العملة الأساسية
                f'<span class="badge bg-success"><i class="fas fa-star"></i> {_("أساسية")}</span>' if currency.is_base
                else f'<span class="badge bg-secondary">{_("عادية")}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if currency.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # الإجراءات
                actions
            ]

            data.append(row)

        response = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
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
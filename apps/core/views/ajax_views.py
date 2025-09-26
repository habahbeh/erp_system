# apps/core/views/ajax_views.py
"""
Ajax Views للاستجابة السريعة
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.urls import reverse
from django.utils.translation import gettext as _

from ..models import Item, BusinessPartner, ItemCategory, Brand, Warehouse, UnitOfMeasure, Currency, Branch, VariantAttribute, UserProfile, PermissionGroup, CustomPermission
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
            # للتجريب - جلب جميع المواد
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
                Q(item_code__icontains=search_value) |
                Q(catalog_number__icontains=search_value) |
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

        columns = ['item_code', 'name', 'category__name', 'brand__name', 'unit_of_measure__name', 'is_active']

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
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا المادة؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود - عرض item_code إذا كان متوفر، وإلا code
                f'<div>' +
                (f'<code class="text-primary fw-bold">{item.item_code}</code>' if item.item_code
                 else f'<code class="text-muted">{item.code}</code>') +
                (
                    f'<br><small class="text-success"><i class="fas fa-bookmark"></i> {item.catalog_number}</small>' if item.catalog_number else '') +
                (
                    f'<br><small class="text-muted"><i class="fas fa-barcode"></i> {item.barcode}</small>' if item.barcode else '') +
                '</div>',

                # اسم المادة - لا تغيير
                f'<div><strong class="text-dark">{item.name}</strong>' +
                (f'<br><small class="text-muted">{item.name_en}</small>' if item.name_en else '') + '</div>',

                # باقي الأعمدة كما هي...
                f'<span class="badge bg-secondary fs-6">{item.category.name}</span>' if item.category
                else '<span class="text-muted">-</span>',

                f'<span class="text-dark">{item.brand.name}</span>' if item.brand
                else '<span class="text-muted">-</span>',

                f'<span class="badge bg-light text-dark">{item.unit_of_measure.name}</span>',

                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if item.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

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
    """البحث السريع في العملاء"""
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
    """البحث السريع في المواد"""
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
        Q(catalog_number__icontains=term)
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
    """الحصول على تفاصيل مادة معين"""
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
            'catalog_number': item.catalog_number,
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
        return JsonResponse({'error': _('المادة غير موجود')}, status=404)

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

    # استثناء المادة الحالي في حالة التعديل
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
Ajax Views للعملاء
"""

@login_required
@permission_required_with_message('core.view_businesspartner')
@require_http_methods(["GET"])
def partner_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للعملاء"""
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
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا العميل؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود
                f'<code class="text-primary fw-bold">{partner.code}</code>',

                # اسم العميل
                f'<div><strong class="text-dark">{partner.name}</strong>' +
                (f'<br><small class="text-muted">{partner.name_en}</small>' if partner.name_en else '') + '</div>',

                # نوع العميل
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



@login_required
@permission_required_with_message('core.view_branch')
@require_http_methods(["GET"])
def branch_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للفروع"""
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
        is_main_filter = request.GET.get('is_main', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = Branch.objects.filter(company=request.current_company)
        else:
            queryset = Branch.objects.all()

        queryset = queryset.select_related('default_warehouse')

        # تطبيق الفلاتر المخصصة
        if is_main_filter:
            is_main = is_main_filter == '1'
            queryset = queryset.filter(is_main=is_main)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(phone__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(address__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = Branch.objects.filter(company=request.current_company).count()
        else:
            records_total = Branch.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['code', 'name', 'phone', 'default_warehouse__name', 'is_main', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        branches = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for branch in branches:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_branch')
            can_delete = request.user.has_perm('core.delete_branch')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:branch_detail', kwargs={'pk': branch.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:branch_update', kwargs={'pk': branch.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف (ممنوع للفرع الرئيسي)
            if can_delete and not branch.is_main:
                actions += f'''
                    <a href="{reverse('core:branch_delete', kwargs={'pk': branch.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا الفرع؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # الكود
                f'<code class="text-primary fw-bold">{branch.code}</code>',

                # اسم الفرع
                f'<div><strong class="text-dark">{branch.name}</strong></div>',

                # الهاتف
                f'<span class="text-dark">{branch.phone}</span>' if branch.phone
                else '<span class="text-muted">-</span>',

                # المستودع الافتراضي
                f'<span class="text-dark">{branch.default_warehouse.name}</span>' if branch.default_warehouse
                else '<span class="text-muted">-</span>',

                # فرع رئيسي
                f'<span class="badge bg-warning"><i class="fas fa-star"></i> {_("رئيسي")}</span>' if branch.is_main
                else f'<span class="badge bg-secondary">{_("فرعي")}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if branch.is_active
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
@permission_required_with_message('core.view_variantattribute')
@require_http_methods(["GET"])
def variant_attribute_datatable_ajax(request):
    """Ajax endpoint للـ DataTable لخصائص المتغيرات"""
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
        is_required_filter = request.GET.get('is_required', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات
        if request.current_company:
            queryset = VariantAttribute.objects.filter(company=request.current_company)
        else:
            queryset = VariantAttribute.objects.all()

        # تطبيق الفلاتر المخصصة
        if is_required_filter:
            is_required = is_required_filter == '1'
            queryset = queryset.filter(is_required=is_required)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(name_en__icontains=search_value) |
                Q(display_name__icontains=search_value)
            )

        # العدد الكلي
        if request.current_company:
            records_total = VariantAttribute.objects.filter(company=request.current_company).count()
        else:
            records_total = VariantAttribute.objects.count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['name', 'display_name', 'values_count', 'is_required', 'sort_order', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field

            # معالجة خاصة لعدد القيم
            if order_field == 'values_count' or order_field == '-values_count':
                from django.db.models import Count
                queryset = queryset.annotate(values_count=Count('values'))
                queryset = queryset.order_by(order_field)
            else:
                queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('sort_order', 'name')

        # إضافة عدد القيم لكل خاصية
        from django.db.models import Count
        queryset = queryset.annotate(values_count=Count('values'))

        # التقسيم للصفحات
        attributes = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for attribute in attributes:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_variantattribute')
            can_delete = request.user.has_perm('core.delete_variantattribute')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:variant_attribute_detail', kwargs={'pk': attribute.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:variant_attribute_update', kwargs={'pk': attribute.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:variant_attribute_delete', kwargs={'pk': attribute.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه الخاصية؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تجميع صف البيانات
            row = [
                # اسم الخاصية
                f'<div><strong class="text-dark">{attribute.name}</strong>' +
                (f'<br><small class="text-muted">{attribute.name_en}</small>' if attribute.name_en else '') + '</div>',

                # اسم العرض
                f'<span class="text-dark">{attribute.display_name or attribute.name}</span>',

                # عدد القيم
                f'<span class="badge bg-primary fs-6">{attribute.values_count} {_("قيم")}</span>',

                # إجباري
                f'<span class="badge bg-danger"><i class="fas fa-exclamation"></i> {_("إجباري")}</span>' if attribute.is_required
                else f'<span class="badge bg-secondary">{_("اختياري")}</span>',

                # ترتيب العرض
                f'<span class="badge bg-light text-dark">{attribute.sort_order}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if attribute.is_active
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
@permission_required_with_message('auth.view_user')
@require_http_methods(["GET"])
def user_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للمستخدمين"""
    try:
        # معالجة طلبات تحميل خيارات الفلاتر
        if request.GET.get('get_companies'):
            companies = Company.objects.filter(is_active=True).values('id', 'name').order_by('name')
            return JsonResponse({'companies': list(companies)})

        if request.GET.get('get_branches'):
            company_id = request.GET.get('company_id')
            if company_id:
                branches = Branch.objects.filter(
                    company_id=company_id, is_active=True
                ).values('id', 'name').order_by('name')
                return JsonResponse({'branches': list(branches)})
            return JsonResponse({'branches': []})

        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # فلاتر مخصصة
        company_filter = request.GET.get('company', '')
        branch_filter = request.GET.get('branch', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')

        # الحصول على البيانات مع فلترة حسب الصلاحيات
        if request.user.is_superuser:
            # مديرو النظام يرون جميع المستخدمين
            queryset = User.objects.all()
        elif hasattr(request.user, 'company') and request.user.company:
            # المستخدمون العاديون يرون فقط مستخدمي شركتهم
            queryset = User.objects.filter(company=request.user.company)
        else:
            # إذا لم تكن هناك شركة، المستخدم يرى نفسه فقط
            queryset = User.objects.filter(pk=request.user.pk)

        queryset = queryset.select_related('company', 'branch')

        # تطبيق الفلاتر المخصصة
        if company_filter:
            queryset = queryset.filter(company_id=company_filter)

        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        if role_filter:
            if role_filter == 'superuser':
                queryset = queryset.filter(is_superuser=True)
            elif role_filter == 'staff':
                queryset = queryset.filter(is_staff=True, is_superuser=False)
            elif role_filter == 'user':
                queryset = queryset.filter(is_staff=False, is_superuser=False)

        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(username__icontains=search_value) |
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(emp_number__icontains=search_value) |
                Q(phone__icontains=search_value)
            )

        # العدد الكلي (حسب الصلاحيات)
        if request.user.is_superuser:
            records_total = User.objects.count()
        elif hasattr(request.user, 'company') and request.user.company:
            records_total = User.objects.filter(company=request.user.company).count()
        else:
            records_total = 1  # المستخدم نفسه فقط

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['username', 'first_name', 'email', 'company__name', 'branch__name', 'role', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('username')

        # التقسيم للصفحات
        users = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for user_obj in users:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('auth.change_user')
            can_delete = request.user.has_perm('auth.delete_user')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:user_detail', kwargs={'pk': user_obj.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:user_update', kwargs={'pk': user_obj.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر تغيير كلمة المرور
            if can_change or request.user == user_obj:
                actions += f'''
                    <a href="{reverse('core:user_change_password', kwargs={'pk': user_obj.pk})}" 
                       class="btn btn-outline-secondary btn-sm" title="{_('تغيير كلمة المرور')}">
                        <i class="fas fa-key"></i>
                    </a>
                '''

            # زر الحذف (ممنوع للمستخدم نفسه)
            if can_delete and user_obj != request.user:
                actions += f'''
                    <a href="{reverse('core:user_delete', kwargs={'pk': user_obj.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذا المستخدم؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # تحديد دور المستخدم
            if user_obj.is_superuser:
                role_badge = f'<span class="badge bg-danger"><i class="fas fa-crown"></i> {_("مدير نظام")}</span>'
            elif user_obj.is_staff:
                role_badge = f'<span class="badge bg-warning"><i class="fas fa-user-tie"></i> {_("طاقم الإدارة")}</span>'
            else:
                role_badge = f'<span class="badge bg-secondary"><i class="fas fa-user"></i> {_("مستخدم عادي")}</span>'

            # تجميع صف البيانات
            row = [
                # اسم المستخدم
                f'<div><strong class="text-dark">{user_obj.username}</strong></div>',

                # الاسم الكامل
                f'<div><strong class="text-dark">{user_obj.get_full_name() or "—"}</strong>' +
                (f'<br><small class="text-muted">{user_obj.emp_number}</small>' if user_obj.emp_number else '') + '</div>',

                # البريد الإلكتروني
                f'<div><span class="text-dark">{user_obj.email}</span>' +
                (f'<br><small class="text-muted"><i class="fas fa-phone"></i> {user_obj.phone}</small>' if user_obj.phone else '') + '</div>',

                # الشركة
                f'<span class="text-dark">{user_obj.company.name}</span>' if user_obj.company
                else '<span class="text-muted">-</span>',

                # الفرع
                f'<span class="text-dark">{user_obj.branch.name}</span>' if user_obj.branch
                else '<span class="text-muted">-</span>',

                # الصلاحيات
                role_badge,

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if user_obj.is_active
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
@permission_required_with_message('core.view_userprofile')
@require_http_methods(["GET"])
def profile_datatable_ajax(request):
    """Ajax endpoint للـ DataTable لملفات المستخدمين"""
    try:
        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # الحصول على البيانات مع فلترة حسب الصلاحيات
        if request.user.is_superuser:
            # مديرو النظام يرون جميع الملفات
            queryset = UserProfile.objects.all()
        elif hasattr(request.user, 'company') and request.user.company:
            # المستخدمون العاديون يرون فقط ملفات مستخدمي شركتهم
            queryset = UserProfile.objects.filter(user__company=request.user.company)
        else:
            # إذا لم تكن هناك شركة، المستخدم يرى ملفه فقط
            queryset = UserProfile.objects.filter(user=request.user)

        queryset = queryset.select_related('user', 'user__company', 'user__branch')
        queryset = queryset.prefetch_related('allowed_branches', 'allowed_warehouses')

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(user__username__icontains=search_value) |
                Q(user__first_name__icontains=search_value) |
                Q(user__last_name__icontains=search_value) |
                Q(user__email__icontains=search_value) |
                Q(user__company__name__icontains=search_value)
            )

        # العدد الكلي (حسب الصلاحيات)
        if request.user.is_superuser:
            records_total = UserProfile.objects.count()
        elif hasattr(request.user, 'company') and request.user.company:
            records_total = UserProfile.objects.filter(user__company=request.user.company).count()
        else:
            records_total = UserProfile.objects.filter(user=request.user).count()

        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = [
            'user__username', 'user__company__name', 'max_discount_percentage',
            'max_credit_limit', 'allowed_branches', 'allowed_warehouses'
        ]

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('user__username')

        # التقسيم للصفحات
        profiles = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for profile in profiles:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_userprofile')
            can_delete = request.user.has_perm('core.delete_userprofile')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:profile_detail', kwargs={'pk': profile.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:profile_update', kwargs={'pk': profile.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                            <a href="{reverse('core:profile_delete', kwargs={'pk': profile.pk})}" 
                               class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                               onclick="return confirm('{_('هل أنت متأكد من حذف ملف هذا المستخدم؟')}')">
                                <i class="fas fa-trash"></i>
                            </a>
                        '''

            # زر الصلاحيات
            if request.user.has_perm('core.change_custompermission'):
                actions += f'''
                    <a href="{reverse('core:user_permissions', kwargs={'user_id': profile.user.pk})}" 
                       class="btn btn-outline-secondary btn-sm" title="{_('إدارة الصلاحيات')}">
                        <i class="fas fa-key"></i>
                    </a>
                '''

            actions += '</div>'

            # الفروع المسموحة
            if profile.allowed_branches.exists():
                branches_text = ', '.join([b.name for b in profile.allowed_branches.all()[:3]])
                if profile.allowed_branches.count() > 3:
                    branches_text += f' +{profile.allowed_branches.count() - 3}'
                branches_badge = f'<span class="badge bg-info">{branches_text}</span>'
            else:
                branches_badge = f'<span class="badge bg-success">{_("جميع الفروع")}</span>'

            # المستودعات المسموحة
            if profile.allowed_warehouses.exists():
                warehouses_text = ', '.join([w.name for w in profile.allowed_warehouses.all()[:3]])
                if profile.allowed_warehouses.count() > 3:
                    warehouses_text += f' +{profile.allowed_warehouses.count() - 3}'
                warehouses_badge = f'<span class="badge bg-warning">{warehouses_text}</span>'
            else:
                warehouses_badge = f'<span class="badge bg-success">{_("جميع المستودعات")}</span>'

            # تجميع صف البيانات
            row = [
                # المستخدم
                f'<div><strong class="text-dark">{profile.user.get_full_name() or profile.user.username}</strong>' +
                f'<br><small class="text-muted">@{profile.user.username}</small>' +
                (f'<br><small class="text-muted">{profile.user.email}</small>' if profile.user.email else '') + '</div>',

                # الشركة
                f'<span class="text-dark">{profile.user.company.name}</span>' if profile.user.company
                else '<span class="text-muted">-</span>',

                # نسبة الخصم
                f'<span class="badge bg-primary fs-6">{profile.max_discount_percentage}%</span>',

                # حد الائتمان
                f'<span class="badge bg-success fs-6">{profile.max_credit_limit:,.2f} د.أ</span>',

                # الفروع المسموحة
                branches_badge,

                # المستودعات المسموحة
                warehouses_badge,

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


# إضافة هذا في نهاية ملف apps/core/views/ajax_views.py

@login_required
@permission_required_with_message('core.view_custompermission')
@require_http_methods(["GET"])
def permission_datatable_ajax(request):
    """Ajax endpoint للـ DataTable للصلاحيات المخصصة"""
    try:
        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # الحصول على البيانات
        queryset = CustomPermission.objects.all()

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(code__icontains=search_value) |
                Q(description__icontains=search_value) |
                Q(category__icontains=search_value)
            )

        # فلترة حسب التصنيف
        category_filter = request.GET.get('category', '')
        if category_filter:
            queryset = queryset.filter(category=category_filter)

        # فلترة حسب النوع
        type_filter = request.GET.get('permission_type', '')
        if type_filter:
            queryset = queryset.filter(permission_type=type_filter)

        # فلترة حسب الحالة
        status_filter = request.GET.get('is_active', '')
        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # العدد الكلي
        records_total = CustomPermission.objects.count()
        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['name', 'code', 'category', 'permission_type', 'is_active', 'users_count']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('category', 'name')

        # التقسيم للصفحات
        permissions = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for permission in permissions:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_custompermission')
            can_delete = request.user.has_perm('core.delete_custompermission')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:permission_detail', kwargs={'pk': permission.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:permission_update', kwargs={'pk': permission.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:permission_delete', kwargs={'pk': permission.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه الصلاحية؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # عدد المستخدمين
            users_count = permission.users.count()
            groups_count = permission.groups.count()

            # تجميع صف البيانات
            row = [
                # اسم الصلاحية
                f'<div><strong class="text-dark">{permission.name}</strong>' +
                (f'<br><small class="text-muted">{permission.description[:50]}...</small>' if permission.description else '') + '</div>',

                # الرمز
                f'<code class="bg-light text-primary">{permission.code}</code>',

                # التصنيف
                f'<span class="badge bg-primary">{permission.get_category_display()}</span>',

                # نوع الصلاحية
                f'<span class="badge bg-secondary">{permission.get_permission_type_display()}</span>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if permission.is_active
                else f'<span class="badge bg-secondary"><i class="fas fa-times"></i> {_("غير نشط")}</span>',

                # عدد المستخدمين
                f'<div class="text-center">' +
                f'<span class="badge bg-info">{users_count} {_("مستخدم")}</span>' +
                (f'<br><span class="badge bg-warning">{groups_count} {_("مجموعة")}</span>' if groups_count > 0 else '') +
                '</div>',

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
@permission_required_with_message('core.view_permissiongroup')
@require_http_methods(["GET"])
def group_datatable_ajax(request):
    """Ajax endpoint للـ DataTable لمجموعات الصلاحيات"""
    try:
        # معاملات DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '').strip()

        # الحصول على البيانات
        queryset = PermissionGroup.objects.all()
        queryset = queryset.prefetch_related('permissions', 'django_permissions')

        # البحث العام
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(description__icontains=search_value)
            )

        # فلترة حسب الحالة
        status_filter = request.GET.get('is_active', '')
        if status_filter:
            is_active = status_filter == '1'
            queryset = queryset.filter(is_active=is_active)

        # العدد الكلي
        records_total = PermissionGroup.objects.count()
        records_filtered = queryset.count()

        # الترتيب
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')

        columns = ['name', 'description', 'permissions_count', 'users_count', 'is_active']

        if 0 <= order_column < len(columns):
            order_field = columns[order_column]
            if order_dir == 'desc':
                order_field = '-' + order_field
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('name')

        # التقسيم للصفحات
        groups = queryset[start:start + length]

        # تجهيز البيانات للإرسال
        data = []
        for group in groups:
            # التحقق من الصلاحيات
            can_change = request.user.has_perm('core.change_permissiongroup')
            can_delete = request.user.has_perm('core.delete_permissiongroup')

            # تكوين أزرار الإجراءات
            actions = '<div class="btn-group btn-group-sm" role="group">'

            # زر العرض
            actions += f'''
                <a href="{reverse('core:group_detail', kwargs={'pk': group.pk})}" 
                   class="btn btn-outline-info btn-sm" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            '''

            # زر التعديل
            if can_change:
                actions += f'''
                    <a href="{reverse('core:group_update', kwargs={'pk': group.pk})}" 
                       class="btn btn-outline-warning btn-sm" title="{_('تعديل')}">
                        <i class="fas fa-edit"></i>
                    </a>
                '''

            # زر الحذف
            if can_delete:
                actions += f'''
                    <a href="{reverse('core:group_delete', kwargs={'pk': group.pk})}" 
                       class="btn btn-outline-danger btn-sm" title="{_('حذف')}"
                       onclick="return confirm('{_('هل أنت متأكد من حذف هذه المجموعة؟')}')">
                        <i class="fas fa-trash"></i>
                    </a>
                '''

            actions += '</div>'

            # إحصائيات
            permissions_count = group.get_total_permissions_count()
            users_count = UserProfile.objects.filter(permission_groups=group).count()

            # تجميع صف البيانات
            row = [
                # اسم المجموعة
                f'<div><strong class="text-dark">{group.name}</strong></div>',

                # الوصف
                f'<div class="text-muted">{group.description[:100]}...</div>' if group.description else '<span class="text-muted">-</span>',

                # عدد الصلاحيات
                f'<div class="text-center">' +
                f'<span class="badge bg-primary">{permissions_count} {_("صلاحية")}</span>' +
                '</div>',

                # عدد المستخدمين
                f'<div class="text-center">' +
                f'<span class="badge bg-info">{users_count} {_("مستخدم")}</span>' +
                '</div>',

                # الحالة
                f'<span class="badge bg-success"><i class="fas fa-check"></i> {_("نشط")}</span>' if group.is_active
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
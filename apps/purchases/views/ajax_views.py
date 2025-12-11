# apps/purchases/views/ajax_views.py
"""
AJAX Views for Invoice Advanced Features
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg, Sum, Max
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from apps.core.models import Item, ItemVariant, BusinessPartner
from ..models import PurchaseInvoice, PurchaseInvoiceItem, PurchaseOrder, PurchaseOrderItem


@login_required
@require_http_methods(["GET"])
def ajax_items_search(request):
    """
    البحث السريع للمواد - Quick Item Search
    يدعم البحث بالأحرف الأولى في الكود، الاسم، الاسم اللاتيني، والباركود
    """
    query = request.GET.get('q', '').strip()
    quick = request.GET.get('quick', '0') == '1'  # البحث المختصر
    limit = int(request.GET.get('limit', 10))

    if not query or len(query) < 1:
        return JsonResponse({'results': []})

    # البحث في المواد النشطة فقط
    items = Item.objects.filter(
        company=request.current_company,
        is_active=True,
        is_purchasable=True
    )

    # البحث المتقدم
    search_conditions = Q()

    # البحث بالأحرف الأولى في الاسم العربي
    if quick:
        # البحث في بداية الكلمات
        words = query.split()
        for word in words:
            search_conditions |= Q(name__icontains=word)
            search_conditions |= Q(name_english__icontains=word)
    else:
        # البحث العادي
        search_conditions = (
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(name_english__icontains=query) |
            Q(barcode__icontains=query)
        )

    items = items.filter(search_conditions).select_related('category', 'unit')[:limit]

    # تحضير النتائج
    results = []
    for item in items:
        # الحصول على آخر سعر شراء
        last_purchase = PurchaseInvoiceItem.objects.filter(
            invoice__company=request.current_company,
            invoice__is_posted=True,
            item=item
        ).order_by('-invoice__date').first()

        last_price = last_purchase.unit_price if last_purchase else item.purchase_price or Decimal('0')

        # ✅ الملاحظة 1: حساب السعر مع الضريبة
        tax_rate = item.tax_rate or Decimal('0')
        price_with_tax = last_price
        if not item.is_tax_exempt and tax_rate > 0:
            price_with_tax = last_price * (Decimal('1') + (tax_rate / Decimal('100')))

        result = {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'name_english': item.name_english or '',
            'barcode': item.barcode or '',
            'unit': item.unit.name if item.unit else '',
            'unit_id': item.unit.id if item.unit else None,
            'purchase_price': str(price_with_tax),  # ✅ الملاحظة 1: السعر مع الضريبة
            'purchase_price_before_tax': str(last_price),  # السعر الأصلي بدون ضريبة
            'tax_rate': str(tax_rate),
            'is_tax_exempt': item.is_tax_exempt,
            'category': item.category.name if item.category else '',
            # معلومات إضافية
            'has_variants': item.has_variants,
            'track_inventory': item.track_inventory,
        }

        # إذا كانت المادة لها متغيرات
        if item.has_variants:
            variants = ItemVariant.objects.filter(
                item=item,
                is_active=True
            ).select_related('item')[:5]

            variant_list = []
            for v in variants:
                v_price = v.purchase_price or last_price
                # ✅ الملاحظة 1: حساب سعر المتغير مع الضريبة
                v_price_with_tax = v_price
                if not item.is_tax_exempt and tax_rate > 0:
                    v_price_with_tax = v_price * (Decimal('1') + (tax_rate / Decimal('100')))

                variant_list.append({
                    'id': v.id,
                    'code': v.code,
                    'name': v.get_variant_display(),
                    'barcode': v.barcode or '',
                    'purchase_price': str(v_price_with_tax),  # ✅ الملاحظة 1: السعر مع الضريبة
                })

            result['variants'] = variant_list

        results.append(result)

    return JsonResponse({
        'results': results,
        'count': len(results)
    })


@login_required
@require_http_methods(["POST"])
def ajax_request_credit_approval(request):
    """
    طلب موافقة على الدفع الآجل (ذمم)
    Request approval for credit payment
    """
    try:
        data = json.loads(request.body)
        supplier_id = data.get('supplier_id')
        amount = Decimal(str(data.get('amount', 0)))
        invoice_id = data.get('invoice_id')  # اختياري في حالة التعديل

        if not supplier_id:
            return JsonResponse({
                'success': False,
                'error': _('يجب تحديد المورد')
            }, status=400)

        # التحقق من وجود المورد
        try:
            supplier = BusinessPartner.objects.get(
                id=supplier_id,
                company=request.current_company,
                partner_type__in=['supplier', 'both']
            )
        except BusinessPartner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': _('المورد غير موجود')
            }, status=404)

        # التحقق من حد الائتمان
        if supplier.credit_limit:
            # حساب الرصيد الحالي للمورد
            current_balance = PurchaseInvoice.objects.filter(
                company=request.current_company,
                supplier=supplier,
                is_posted=True,
                payment_status__in=['unpaid', 'partial']
            ).exclude(
                id=invoice_id  # استبعاد الفاتورة الحالية إذا كانت تعديل
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0')

            # التحقق من تجاوز الحد الائتماني
            if (current_balance + amount) > supplier.credit_limit:
                return JsonResponse({
                    'success': False,
                    'requires_approval': True,
                    'message': _('المبلغ يتجاوز الحد الائتماني للمورد'),
                    'current_balance': str(current_balance),
                    'credit_limit': str(supplier.credit_limit),
                    'available_credit': str(supplier.credit_limit - current_balance),
                    'requested_amount': str(amount),
                    'excess_amount': str((current_balance + amount) - supplier.credit_limit)
                })

        # إذا لم يكن هناك تجاوز، يمكن الموافقة مباشرة
        return JsonResponse({
            'success': True,
            'requires_approval': False,
            'message': _('المبلغ ضمن الحد الائتماني المسموح')
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': _('بيانات غير صحيحة')
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_purchase_orders_search(request):
    """
    البحث عن أوامر الشراء - Search Purchase Orders
    """
    query = request.GET.get('q', '').strip()
    supplier_id = request.GET.get('supplier_id', '')

    # البحث في أوامر الشراء المعتمدة فقط
    orders = PurchaseOrder.objects.filter(
        company=request.current_company,
        is_active=True,
        status='approved'  # فقط الأوامر المعتمدة
    ).select_related('supplier')

    # تصفية حسب المورد إذا تم تحديده
    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    # البحث بالنص
    if query:
        orders = orders.filter(
            Q(number__icontains=query) |
            Q(supplier__name__icontains=query)
        )

    orders = orders.order_by('-date')[:20]

    results = []
    for order in orders:
        results.append({
            'id': order.number,
            'text': f"{order.number} - {order.supplier.name} - {order.date}",
            'number': order.number,
            'supplier_id': order.supplier.id,
            'supplier_name': order.supplier.name,
            'date': str(order.date),
            'total': str(order.total_amount)
        })

    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def ajax_documents_search(request):
    """
    البحث عن كل المستندات (أوامر شراء + فواتير سابقة) - Search All Documents
    """
    query = request.GET.get('q', '').strip()
    supplier_id = request.GET.get('supplier_id', '')

    results = []

    # 1. البحث في أوامر الشراء المعتمدة
    orders = PurchaseOrder.objects.filter(
        company=request.current_company,
        is_active=True,
        status='approved'
    ).select_related('supplier')

    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    if query:
        orders = orders.filter(
            Q(number__icontains=query) |
            Q(supplier__name__icontains=query)
        )

    for order in orders.order_by('-date')[:10]:
        results.append({
            'id': order.number,
            'type': 'order',
            'type_label': 'أمر شراء',
            'number': order.number,
            'supplier_id': order.supplier.id,
            'supplier_name': order.supplier.name,
            'date': str(order.date),
            'total': str(order.total_amount),
            'icon': 'fa-file-alt',
            'color': 'primary'
        })

    # 2. البحث في فواتير المشتريات المرحّلة
    invoices = PurchaseInvoice.objects.filter(
        company=request.current_company,
        is_active=True,
        is_posted=True
    ).select_related('supplier')

    if supplier_id:
        invoices = invoices.filter(supplier_id=supplier_id)

    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(supplier__name__icontains=query)
        )

    for inv in invoices.order_by('-date')[:10]:
        results.append({
            'id': inv.number,
            'type': 'invoice',
            'type_label': 'فاتورة مشتريات',
            'number': inv.number,
            'supplier_id': inv.supplier.id,
            'supplier_name': inv.supplier.name,
            'date': str(inv.date),
            'total': str(inv.total_amount),
            'icon': 'fa-file-invoice',
            'color': 'success'
        })

    # ترتيب حسب التاريخ
    results.sort(key=lambda x: x['date'], reverse=True)

    return JsonResponse({'results': results[:20]})


@login_required
@require_http_methods(["GET"])
def ajax_get_document_details(request, doc_type, doc_number):
    """
    جلب تفاصيل أي مستند - Get Document Details
    """
    try:
        if doc_type == 'order':
            # جلب أمر شراء
            order = PurchaseOrder.objects.get(
                company=request.current_company,
                number=doc_number,
                status='approved'
            )

            items = []
            for item in order.items.all().select_related('item', 'item_variant', 'unit'):
                items.append({
                    'item_id': item.item.id,
                    'item_name': item.item.name,
                    'item_code': item.item.code,
                    'variant_id': item.item_variant.id if item.item_variant else None,
                    'variant_name': str(item.item_variant) if item.item_variant else '',
                    'quantity': str(item.quantity),
                    'unit': item.unit.name if item.unit else item.item.unit.name,
                    'unit_id': item.unit.id if item.unit else item.item.unit.id,
                    'unit_price': str(item.unit_price),
                    'tax_rate': str(item.tax_rate),
                    'discount_percentage': str(item.discount_percentage),
                    'subtotal': str(item.subtotal)
                })

            return JsonResponse({
                'success': True,
                'document': {
                    'type': 'order',
                    'number': order.number,
                    'date': str(order.date),
                    'supplier_id': order.supplier.id,
                    'supplier_name': order.supplier.name,
                    'warehouse_id': order.warehouse.id if hasattr(order, 'warehouse') and order.warehouse else None,
                    'notes': order.notes or '',
                    'items': items
                }
            })

        elif doc_type == 'invoice':
            # جلب فاتورة
            invoice = PurchaseInvoice.objects.get(
                company=request.current_company,
                number=doc_number,
                is_posted=True
            )

            items = []
            for item in invoice.items.all().select_related('item', 'item_variant', 'unit'):
                items.append({
                    'item_id': item.item.id,
                    'item_name': item.item.name,
                    'item_code': item.item.code,
                    'variant_id': item.item_variant.id if item.item_variant else None,
                    'variant_name': str(item.item_variant) if item.item_variant else '',
                    'quantity': str(item.quantity),
                    'unit': item.unit.name if item.unit else item.item.unit.name,
                    'unit_id': item.unit.id if item.unit else item.item.unit.id,
                    'unit_price': str(item.unit_price),
                    'tax_rate': str(item.tax_rate),
                    'discount_percentage': str(item.discount_percentage),
                    'subtotal': str(item.subtotal)
                })

            return JsonResponse({
                'success': True,
                'document': {
                    'type': 'invoice',
                    'number': invoice.number,
                    'date': str(invoice.date),
                    'supplier_id': invoice.supplier.id,
                    'supplier_name': invoice.supplier.name,
                    'warehouse_id': invoice.warehouse.id,
                    'notes': invoice.notes or '',
                    'items': items
                }
            })

        else:
            return JsonResponse({
                'success': False,
                'error': _('نوع المستند غير معروف')
            }, status=400)

    except (PurchaseOrder.DoesNotExist, PurchaseInvoice.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': _('المستند غير موجود')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_get_purchase_order_details(request, order_number):
    """
    جلب تفاصيل أمر الشراء - Get Purchase Order Details
    """
    try:
        order = PurchaseOrder.objects.get(
            company=request.current_company,
            number=order_number,
            status='approved'
        )

        items = []
        for item in order.items.all().select_related('item', 'item_variant', 'unit'):
            items.append({
                'item_id': item.item.id,
                'item_name': item.item.name,
                'item_code': item.item.code,
                'variant_id': item.item_variant.id if item.item_variant else None,
                'variant_name': str(item.item_variant) if item.item_variant else '',
                'quantity': str(item.quantity),
                'unit': item.unit.name if item.unit else item.item.unit.name,
                'unit_id': item.unit.id if item.unit else item.item.unit.id,
                'unit_price': str(item.unit_price),
                'tax_rate': str(item.tax_rate),
                'discount_percentage': str(item.discount_percentage),
                'subtotal': str(item.subtotal)
            })

        return JsonResponse({
            'success': True,
            'order': {
                'number': order.number,
                'date': str(order.date),
                'supplier_id': order.supplier.id,
                'supplier_name': order.supplier.name,
                'warehouse_id': order.warehouse.id if hasattr(order, 'warehouse') and order.warehouse else None,
                'notes': order.notes or '',
                'items': items
            }
        })

    except PurchaseOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('أمر الشراء غير موجود أو غير معتمد')
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_price_history(request):
    """
    عرض سجل الأسعار وحركات الشراء للمادة
    Show price history and purchase movements for an item
    """
    item_id = request.GET.get('item')
    variant_id = request.GET.get('variant')
    supplier_id = request.GET.get('supplier')
    limit = int(request.GET.get('limit', 20))

    if not item_id:
        return JsonResponse({
            'success': False,
            'error': _('يجب تحديد المادة')
        }, status=400)

    # التحقق من وجود المادة
    try:
        item = Item.objects.get(
            id=item_id,
            company=request.current_company
        )
    except Item.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('المادة غير موجودة')
        }, status=404)

    # بناء الاستعلام
    lines = PurchaseInvoiceItem.objects.filter(
        invoice__company=request.current_company,
        invoice__is_posted=True,
        item=item
    ).select_related(
        'invoice',
        'invoice__supplier',
        'invoice__branch',
        'item_variant'
    )

    # تصفية حسب المتغير إذا تم تحديده
    if variant_id:
        lines = lines.filter(item_variant_id=variant_id)

    # تصفية حسب المورد إذا تم تحديده
    if supplier_id:
        lines = lines.filter(invoice__supplier_id=supplier_id)

    # ترتيب حسب التاريخ (الأحدث أولاً)
    lines = lines.order_by('-invoice__date', '-invoice__number')[:limit]

    # تحضير البيانات
    history = []
    for line in lines:
        history.append({
            'date': line.invoice.date.strftime('%Y-%m-%d'),
            'invoice_number': line.invoice.number,
            'supplier': line.invoice.supplier.name if line.invoice.supplier else '',
            'branch': line.invoice.branch.name if line.invoice.branch else '',
            'quantity': str(line.quantity),
            'unit_price': str(line.unit_price),
            'discount': str(line.discount_amount or Decimal('0')),
            'discount_percentage': str(line.discount_percentage or Decimal('0')),
            'tax_amount': str(line.tax_amount or Decimal('0')),
            'total': str(line.total_amount),
            'variant': line.item_variant.get_variant_display() if line.item_variant else '',
            'notes': line.notes or ''
        })

    # حساب الإحصائيات
    stats = lines.aggregate(
        avg_price=Avg('unit_price'),
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_amount'),
        last_price=Max('unit_price')
    )

    # آخر سعر للمورد المحدد
    last_price_for_supplier = None
    last_date_for_supplier = None
    if supplier_id:
        last_for_supplier = lines.first()
        if last_for_supplier:
            last_price_for_supplier = str(last_for_supplier.unit_price)
            last_date_for_supplier = last_for_supplier.invoice.date.strftime('%Y-%m-%d')

    return JsonResponse({
        'success': True,
        'item': {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'name_english': item.name_english or ''
        },
        'history': history,
        'stats': {
            'avg_price': str(stats['avg_price'] or Decimal('0')),
            'total_quantity': str(stats['total_quantity'] or Decimal('0')),
            'total_amount': str(stats['total_amount'] or Decimal('0')),
            'last_price': str(stats['last_price'] or Decimal('0')),
            'count': len(history)
        },
        'supplier_info': {
            'last_price': last_price_for_supplier,
            'last_date': last_date_for_supplier
        } if supplier_id else None
    })


@login_required
@require_http_methods(["GET"])
def ajax_supplier_info(request):
    """
    الحصول على معلومات المورد (الرصيد، الحد الائتماني، إلخ)
    Get supplier information (balance, credit limit, etc.)
    """
    supplier_id = request.GET.get('supplier_id')

    if not supplier_id:
        return JsonResponse({
            'success': False,
            'error': _('يجب تحديد المورد')
        }, status=400)

    try:
        supplier = BusinessPartner.objects.get(
            id=supplier_id,
            company=request.current_company,
            partner_type__in=['supplier', 'both']
        )
    except BusinessPartner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('المورد غير موجود')
        }, status=404)

    # حساب الرصيد الحالي
    balance_info = PurchaseInvoice.objects.filter(
        company=request.current_company,
        supplier=supplier,
        is_posted=True
    ).aggregate(
        total_unpaid=Sum('total_amount', filter=Q(payment_status='unpaid')),
        total_partial=Sum('total_amount', filter=Q(payment_status='partial')),
        total_invoices=Sum('total_amount')
    )

    unpaid = balance_info['total_unpaid'] or Decimal('0')
    partial = balance_info['total_partial'] or Decimal('0')
    current_balance = unpaid + partial

    available_credit = None
    if supplier.credit_limit:
        available_credit = supplier.credit_limit - current_balance

    return JsonResponse({
        'success': True,
        'supplier': {
            'id': supplier.id,
            'code': supplier.code,
            'name': supplier.name,
            'name_english': supplier.name_english or '',
            'credit_limit': str(supplier.credit_limit) if supplier.credit_limit else None,
            'payment_terms': supplier.payment_terms,
            'current_balance': str(current_balance),
            'available_credit': str(available_credit) if available_credit else None,
            'is_active': supplier.is_active
        }
    })


@login_required
@require_http_methods(["GET"])
def ajax_get_item_price_by_uom(request):
    """
    الحصول على سعر المادة حسب الوحدة
    Get item price based on unit of measure
    """
    try:
        from apps.core.models import UnitOfMeasure, UoMConversion

        item_id = request.GET.get('item_id')
        variant_id = request.GET.get('variant_id')
        uom_id = request.GET.get('uom_id')
        supplier_id = request.GET.get('supplier_id')

        if not item_id or not uom_id:
            return JsonResponse({
                'success': False,
                'error': 'يجب تحديد المادة والوحدة'
            }, status=400)
        # Get item
        item = Item.objects.get(id=item_id, company=request.current_company)

        # Get UOM
        uom = UnitOfMeasure.objects.get(id=uom_id, company=request.current_company)

        # Get variant if provided
        variant = None
        if variant_id:
            variant = ItemVariant.objects.get(id=variant_id, item=item)

        # Get price from price list
        from apps.core.models import PriceList, PriceListItem

        price = None
        price_source = None

        # Try to get price from default price list
        price_list = PriceList.objects.filter(
            company=request.current_company,
            is_default=True,
            is_active=True
        ).first()

        if price_list:
            price_item = PriceListItem.objects.filter(
                price_list=price_list,
                item=item,
                variant=variant,
                uom=uom,
                is_active=True
            ).order_by('min_quantity').first()

            if price_item:
                price = price_item.price
                price_source = 'price_list'

        # If no price found, try to get last purchase price
        if not price:
            last_purchase = PurchaseInvoiceItem.objects.filter(
                invoice__company=request.current_company,
                invoice__is_posted=True,
                item=item,
                unit_id=uom_id
            ).order_by('-invoice__date').first()

            if last_purchase:
                price = last_purchase.unit_price
                price_source = 'last_purchase'

        return JsonResponse({
            'success': True,
            'price': str(price) if price else None,
            'price_source': price_source,
            'uom': {
                'id': uom.id,
                'code': uom.code,
                'name': uom.name,
                'name_english': getattr(uom, 'name_english', '') or ''
            },
            'conversion_factor': None,
            'last_purchase': None
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


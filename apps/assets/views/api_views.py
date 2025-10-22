# apps/assets/views/api_views.py
"""
API Views للأصول الثابتة
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from datetime import date, timedelta
from decimal import Decimal

from apps.core.decorators import permission_required_with_message
from ..models import (
    Asset, AssetCategory, AssetCondition, DepreciationMethod,
    MaintenanceSchedule, AssetInsurance, AssetLease
)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_search_api(request):
    """البحث عن الأصول - API"""

    search_term = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 20))

    if len(search_term) < 2:
        return JsonResponse({'results': []})

    try:
        assets = Asset.objects.filter(
            company=request.current_company
        ).filter(
            Q(asset_number__icontains=search_term) |
            Q(name__icontains=search_term) |
            Q(barcode__icontains=search_term) |
            Q(serial_number__icontains=search_term)
        ).select_related('category')[:limit]

        results = []
        for asset in assets:
            results.append({
                'id': asset.id,
                'asset_number': asset.asset_number,
                'name': asset.name,
                'category': asset.category.name,
                'status': asset.get_status_display(),
                'book_value': float(asset.book_value),
                'text': f"{asset.asset_number} - {asset.name}"  # للـ Select2
            })

        return JsonResponse({'results': results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_details_api(request, pk):
    """تفاصيل أصل معين - API"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=pk,
            company=request.current_company
        )

        data = {
            'id': asset.id,
            'asset_number': asset.asset_number,
            'name': asset.name,
            'category': {
                'id': asset.category.id,
                'name': asset.category.name
            },
            'status': asset.status,
            'status_display': asset.get_status_display(),
            'acquisition_date': asset.acquisition_date.strftime('%Y-%m-%d') if asset.acquisition_date else None,
            'acquisition_cost': float(asset.acquisition_cost),
            'accumulated_depreciation': float(asset.accumulated_depreciation),
            'book_value': float(asset.book_value),
            'depreciation_method': asset.depreciation_method.name if asset.depreciation_method else None,
            'useful_life_months': asset.useful_life_months,
            'salvage_value': float(asset.salvage_value),
            'branch': asset.branch.name if asset.branch else None,
            'location': asset.physical_location or '',
            'barcode': asset.barcode or '',
            'serial_number': asset.serial_number or '',
        }

        return JsonResponse({'success': True, 'asset': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def category_assets_api(request, pk):
    """أصول فئة معينة - API"""

    try:
        category = get_object_or_404(AssetCategory, pk=pk)

        assets = Asset.objects.filter(
            company=request.current_company,
            category=category
        ).values(
            'id', 'asset_number', 'name', 'status',
            'acquisition_cost', 'book_value'
        )[:100]

        return JsonResponse({
            'success': True,
            'category': category.name,
            'assets': list(assets)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_stats_api(request):
    """إحصائيات الأصول - API"""

    try:
        # الإحصائيات العامة
        stats = Asset.objects.filter(
            company=request.current_company
        ).aggregate(
            total_count=Count('id'),
            active_count=Count('id', filter=Q(status='active')),
            total_cost=Sum('acquisition_cost'),
            total_book_value=Sum('book_value')
        )

        # حسب الفئة
        by_category = list(Asset.objects.filter(
            company=request.current_company
        ).values('category__name').annotate(
            count=Count('id'),
            total_cost=Sum('acquisition_cost')
        ).order_by('-total_cost')[:10])

        # حسب الحالة
        by_status = list(Asset.objects.filter(
            company=request.current_company
        ).values('status').annotate(
            count=Count('id')
        ))

        return JsonResponse({
            'success': True,
            'stats': stats,
            'by_category': by_category,
            'by_status': by_status
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_schedule_api(request, pk):
    """جدول إهلاك أصل - API"""

    try:
        asset = get_object_or_404(
            Asset,
            pk=pk,
            company=request.current_company
        )

        # حساب جدول الإهلاك المستقبلي
        schedule = []
        remaining_months = asset.get_remaining_months()

        if asset.depreciation_method and asset.depreciation_method.method_type == 'straight_line':
            depreciable_amount = asset.get_depreciable_amount()
            monthly_depreciation = depreciable_amount / asset.useful_life_months if asset.useful_life_months else 0

            current_accumulated = asset.accumulated_depreciation
            current_book_value = asset.book_value

            from dateutil.relativedelta import relativedelta
            current_date = date.today()

            for i in range(min(remaining_months, 12)):  # أول 12 شهر
                month_date = current_date + relativedelta(months=i)

                remaining = depreciable_amount - current_accumulated
                if monthly_depreciation > remaining:
                    monthly_depreciation = remaining

                if monthly_depreciation <= 0:
                    break

                current_accumulated += monthly_depreciation
                current_book_value -= monthly_depreciation

                schedule.append({
                    'month': month_date.strftime('%Y-%m'),
                    'depreciation_amount': float(monthly_depreciation),
                    'accumulated_depreciation': float(current_accumulated),
                    'book_value': float(current_book_value)
                })

        return JsonResponse({
            'success': True,
            'asset': {
                'asset_number': asset.asset_number,
                'name': asset.name
            },
            'schedule': schedule
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def maintenance_alerts_api(request):
    """تنبيهات الصيانة - API"""

    try:
        days = int(request.GET.get('days', 30))

        # الصيانة المتأخرة
        overdue = MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lt=date.today()
        ).select_related('asset').count()

        # الصيانة القريبة
        upcoming = MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__gte=date.today(),
            next_maintenance_date__lte=date.today() + timedelta(days=days)
        ).select_related('asset').count()

        # قائمة الصيانة المتأخرة
        overdue_list = list(MaintenanceSchedule.objects.filter(
            company=request.current_company,
            is_active=True,
            next_maintenance_date__lt=date.today()
        ).select_related('asset', 'maintenance_type').values(
            'id',
            'asset__asset_number',
            'asset__name',
            'maintenance_type__name',
            'next_maintenance_date'
        )[:10])

        return JsonResponse({
            'success': True,
            'overdue_count': overdue,
            'upcoming_count': upcoming,
            'overdue_list': overdue_list
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def insurance_alerts_api(request):
    """تنبيهات التأمين - API"""

    try:
        days = int(request.GET.get('days', 60))

        # التأمين المنتهي قريباً
        expiring = AssetInsurance.objects.filter(
            company=request.current_company,
            status='active',
            end_date__gte=date.today(),
            end_date__lte=date.today() + timedelta(days=days)
        ).select_related('asset', 'insurance_company').count()

        # قائمة التأمين المنتهي
        expiring_list = list(AssetInsurance.objects.filter(
            company=request.current_company,
            status='active',
            end_date__gte=date.today(),
            end_date__lte=date.today() + timedelta(days=days)
        ).select_related('asset', 'insurance_company').values(
            'id',
            'policy_number',
            'asset__asset_number',
            'asset__name',
            'insurance_company__name',
            'end_date',
            'coverage_amount'
        ).order_by('end_date')[:10])

        return JsonResponse({
            'success': True,
            'expiring_count': expiring,
            'expiring_list': expiring_list
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def barcode_scan_api(request):
    """البحث بالباركود - API"""

    barcode = request.GET.get('barcode', '').strip()

    if not barcode:
        return JsonResponse({'success': False, 'error': 'يجب إدخال الباركود'}, status=400)

    try:
        asset = Asset.objects.filter(
            company=request.current_company,
            barcode=barcode
        ).select_related('category', 'condition', 'branch').first()

        if not asset:
            return JsonResponse({
                'success': False,
                'error': 'لم يتم العثور على الأصل'
            })

        data = {
            'id': asset.id,
            'asset_number': asset.asset_number,
            'name': asset.name,
            'category': asset.category.name,
            'status': asset.get_status_display(),
            'condition': asset.condition.name if asset.condition else '',
            'location': asset.physical_location or '',
            'branch': asset.branch.name if asset.branch else '',
            'responsible': asset.responsible_employee.get_full_name() if asset.responsible_employee else '',
            'book_value': float(asset.book_value)
        }

        return JsonResponse({'success': True, 'asset': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_condition_list_api(request):
    """قائمة حالات الأصول - API"""

    try:
        conditions = AssetCondition.objects.filter(
            is_active=True
        ).values('id', 'code', 'name', 'name_en').order_by('name')

        return JsonResponse({
            'success': True,
            'conditions': list(conditions)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def depreciation_method_list_api(request):
    """قائمة طرق الإهلاك - API"""

    try:
        methods = DepreciationMethod.objects.filter(
            is_active=True
        ).values(
            'id', 'code', 'name', 'method_type',
            'rate_percentage', 'description'
        ).order_by('name')

        return JsonResponse({
            'success': True,
            'methods': list(methods)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def category_list_api(request):
    """قائمة فئات الأصول - API"""

    try:
        categories = AssetCategory.objects.filter(
            is_active=True
        ).values(
            'id', 'code', 'name', 'name_en',
            'parent__name'
        ).order_by('name')

        return JsonResponse({
            'success': True,
            'categories': list(categories)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["POST"])
def validate_asset_number_api(request):
    """التحقق من رقم الأصل - API"""

    import json

    try:
        data = json.loads(request.body)
        asset_number = data.get('asset_number', '').strip()
        asset_id = data.get('asset_id')  # للتحديث

        if not asset_number:
            return JsonResponse({
                'valid': False,
                'message': 'يجب إدخال رقم الأصل'
            })

        # التحقق من التكرار
        query = Asset.objects.filter(
            company=request.current_company,
            asset_number=asset_number
        )

        if asset_id:
            query = query.exclude(pk=asset_id)

        if query.exists():
            return JsonResponse({
                'valid': False,
                'message': 'رقم الأصل موجود مسبقاً'
            })

        return JsonResponse({
            'valid': True,
            'message': 'رقم الأصل متاح'
        })

    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': f'خطأ: {str(e)}'
        }, status=500)


@login_required
@permission_required_with_message('assets.view_asset')
@require_http_methods(["GET"])
def asset_qr_code_api(request, pk):
    """رمز QR للأصل - API"""

    try:
        import qrcode
        from io import BytesIO
        import base64

        asset = get_object_or_404(
            Asset,
            pk=pk,
            company=request.current_company
        )

        # إنشاء رمز QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_data = f"ASSET:{asset.asset_number}|{asset.name}|{asset.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # تحويل إلى base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return JsonResponse({
            'success': True,
            'qr_code': f"data:image/png;base64,{img_str}",
            'asset_number': asset.asset_number,
            'asset_name': asset.name
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

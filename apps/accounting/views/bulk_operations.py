# في apps/accounting/views/bulk_operations.py - ملف جديد

@login_required
@permission_required_with_message('accounting.change_account')
@require_http_methods(["POST"])
def bulk_suspend_accounts(request):
    """تعليق عدة حسابات مرة واحدة"""
    account_ids = request.POST.getlist('account_ids')

    if not account_ids:
        return JsonResponse({'success': False, 'message': 'لم يتم تحديد أي حساب'})

    try:
        updated = Account.objects.filter(
            id__in=account_ids,
            company=request.current_company
        ).update(is_suspended=True)

        return JsonResponse({
            'success': True,
            'message': f'تم تعليق {updated} حساب بنجاح'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@permission_required_with_message('accounting.change_journalentry')
@require_http_methods(["POST"])
def bulk_post_journal_entries(request):
    """ترحيل عدة قيود مرة واحدة"""
    entry_ids = request.POST.getlist('entry_ids')

    if not entry_ids:
        return JsonResponse({'success': False, 'message': 'لم يتم تحديد أي قيد'})

    success_count = 0
    error_count = 0
    errors = []

    for entry_id in entry_ids:
        try:
            entry = JournalEntry.objects.get(
                id=entry_id,
                company=request.current_company
            )

            if entry.can_post():
                entry.post(user=request.user)
                success_count += 1
            else:
                error_count += 1
                errors.append(f'القيد {entry.number}: لا يمكن ترحيله')

        except Exception as e:
            error_count += 1
            errors.append(f'القيد {entry_id}: {str(e)}')

    return JsonResponse({
        'success': True,
        'message': f'تم ترحيل {success_count} قيد، فشل في {error_count}',
        'errors': errors
    })
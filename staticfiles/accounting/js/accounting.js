/**
 * accounting.js - JavaScript functions for Accounting App
 * Functions for DataTables, Ajax operations, and UI interactions
 */

// ========== Global Configuration ==========
$(document).ready(function() {
    // تفعيل tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // تفعيل popovers
    $('[data-bs-toggle="popover"]').popover();

    // إعداد CSRF للـ Ajax
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            }
        }
    });
});

// ========== Utility Functions ==========

/**
 * الحصول على CSRF Token
 */
function getCSRFToken() {
    const token = $('[name=csrfmiddlewaretoken]').val() ||
                  $('meta[name="csrf-token"]').attr('content') ||
                  document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    return token;
}

/**
 * التحقق من CSRF Safe Methods
 */
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

/**
 * عرض رسائل Toast
 */
function showToast(type, message, duration = 5000) {
    // إذا كان toastr موجود
    if (typeof toastr !== 'undefined') {
        toastr.options = {
            "closeButton": true,
            "progressBar": true,
            "timeOut": duration,
            "positionClass": "toast-top-right",
            "rtl": true
        };
        toastr[type](message);
    }
    // إذا كان Bootstrap toast موجود
    else if (typeof bootstrap !== 'undefined') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }
    // fallback
    else {
        alert(message);
    }
}

/**
 * تأكيد العملية
 */
function confirmAction(message, callback) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'تأكيد العملية',
            text: message,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'نعم، متابعة',
            cancelButtonText: 'إلغاء',
            reverseButtons: true
        }).then((result) => {
            if (result.isConfirmed) {
                callback();
            }
        });
    } else {
        if (confirm(message)) {
            callback();
        }
    }
}

// ========== Journal Entries Functions ==========

/**
 * ترحيل قيد يومية
 */
function postJournalEntry(entryId) {
    confirmAction('هل أنت متأكد من ترحيل هذا القيد؟\nلن تتمكن من تعديله بعد الترحيل.', function() {
        $.ajax({
            url: `/accounting/ajax/journal-entries/${entryId}/post/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    // إعادة تحميل الجدول أو الصفحة
                    if ($.fn.DataTable.isDataTable('#journal-entries-table')) {
                        $('#journal-entries-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function(xhr) {
                let message = 'حدث خطأ في ترحيل القيد';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showToast('error', message);
            }
        });
    });
}

/**
 * إلغاء ترحيل قيد يومية
 */
function unpostJournalEntry(entryId) {
    confirmAction('هل أنت متأكد من إلغاء ترحيل هذا القيد؟', function() {
        $.ajax({
            url: `/accounting/ajax/journal-entries/${entryId}/unpost/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#journal-entries-table')) {
                        $('#journal-entries-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في إلغاء ترحيل القيد');
            }
        });
    });
}

/**
 * حذف قيد يومية
 */
function deleteJournalEntry(entryId) {
    confirmAction('هل أنت متأكد من حذف هذا القيد نهائياً؟\nلن تتمكن من استرداده.', function() {
        $.ajax({
            url: `/accounting/journal-entries/${entryId}/delete/`,
            type: 'POST',
            success: function(response) {
                showToast('success', 'تم حذف القيد بنجاح');
                if ($.fn.DataTable.isDataTable('#journal-entries-table')) {
                    $('#journal-entries-table').DataTable().ajax.reload();
                } else {
                    window.location.href = '/accounting/journal-entries/';
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في حذف القيد');
            }
        });
    });
}

// ========== Voucher Functions ==========

/**
 * ترحيل سند صرف
 */
function postPaymentVoucher(voucherId) {
    confirmAction('هل أنت متأكد من ترحيل سند الصرف؟\nسيتم إنشاء قيد محاسبي تلقائياً.', function() {
        $.ajax({
            url: `/accounting/ajax/payment-vouchers/${voucherId}/post/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#payment-vouchers-table')) {
                        $('#payment-vouchers-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في ترحيل سند الصرف');
            }
        });
    });
}

/**
 * إلغاء ترحيل سند صرف
 */
function unpostPaymentVoucher(voucherId) {
    confirmAction('هل أنت متأكد من إلغاء ترحيل سند الصرف؟\nسيتم حذف القيد المحاسبي المرتبط.', function() {
        $.ajax({
            url: `/accounting/ajax/payment-vouchers/${voucherId}/unpost/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#payment-vouchers-table')) {
                        $('#payment-vouchers-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في إلغاء ترحيل سند الصرف');
            }
        });
    });
}

/**
 * ترحيل سند قبض
 */
function postReceiptVoucher(voucherId) {
    confirmAction('هل أنت متأكد من ترحيل سند القبض؟\nسيتم إنشاء قيد محاسبي تلقائياً.', function() {
        $.ajax({
            url: `/accounting/ajax/receipt-vouchers/${voucherId}/post/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#receipt-vouchers-table')) {
                        $('#receipt-vouchers-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في ترحيل سند القبض');
            }
        });
    });
}

/**
 * إلغاء ترحيل سند قبض
 */
function unpostReceiptVoucher(voucherId) {
    confirmAction('هل أنت متأكد من إلغاء ترحيل سند القبض؟\nسيتم حذف القيد المحاسبي المرتبط.', function() {
        $.ajax({
            url: `/accounting/ajax/receipt-vouchers/${voucherId}/unpost/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#receipt-vouchers-table')) {
                        $('#receipt-vouchers-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في إلغاء ترحيل سند القبض');
            }
        });
    });
}

// ========== Fiscal Period Functions ==========

/**
 * إقفال الفترة المحاسبية
 */
function closePeriod(periodId) {
    confirmAction('هل أنت متأكد من إقفال هذه الفترة المحاسبية؟\nلن تتمكن من إنشاء قيود جديدة فيها بعد الإقفال.', function() {
        $.ajax({
            url: `/accounting/ajax/periods/${periodId}/close/`,
            type: 'POST',
            data: {
                'closing_notes': 'إقفال تلقائي'
            },
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#periods-table')) {
                        $('#periods-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في إقفال الفترة');
            }
        });
    });
}

/**
 * إعادة فتح الفترة المحاسبية
 */
function reopenPeriod(periodId) {
    confirmAction('هل أنت متأكد من إعادة فتح هذه الفترة المحاسبية؟', function() {
        $.ajax({
            url: `/accounting/ajax/periods/${periodId}/reopen/`,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#periods-table')) {
                        $('#periods-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في إعادة فتح الفترة');
            }
        });
    });
}

// ========== Cost Center Functions ==========

/**
 * تفعيل/إلغاء تفعيل مركز التكلفة
 */
function toggleCostCenterStatus(costCenterId, newStatus) {
    const action = newStatus ? 'تفعيل' : 'إلغاء تفعيل';

    confirmAction(`هل أنت متأكد من ${action} مركز التكلفة؟`, function() {
        $.ajax({
            url: `/accounting/ajax/cost-centers/${costCenterId}/toggle-status/`,
            type: 'POST',
            data: {
                'status': newStatus
            },
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#cost-centers-table')) {
                        $('#cost-centers-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', `حدث خطأ في ${action} مركز التكلفة`);
            }
        });
    });
}

// ========== Account Functions ==========

/**
 * تعليق/إلغاء تعليق حساب
 */
function toggleAccountStatus(accountId, suspend) {
    const action = suspend ? 'تعليق' : 'إلغاء تعليق';

    confirmAction(`هل أنت متأكد من ${action} الحساب؟`, function() {
        $.ajax({
            url: `/accounting/ajax/accounts/${accountId}/toggle-suspend/`,
            type: 'POST',
            data: {
                'suspend': suspend
            },
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if ($.fn.DataTable.isDataTable('#accounts-table')) {
                        $('#accounts-table').DataTable().ajax.reload();
                    } else {
                        location.reload();
                    }
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', `حدث خطأ في ${action} الحساب`);
            }
        });
    });
}

// ========== Bulk Operations ==========

/**
 * العمليات المجمعة - ترحيل عدة قيود
 */
function bulkPostJournalEntries() {
    const selectedEntries = [];
    $('input[name="entry_ids"]:checked').each(function() {
        selectedEntries.push($(this).val());
    });

    if (selectedEntries.length === 0) {
        showToast('warning', 'يرجى اختيار قيد واحد على الأقل');
        return;
    }

    confirmAction(`هل أنت متأكد من ترحيل ${selectedEntries.length} قيد؟`, function() {
        $.ajax({
            url: '/accounting/ajax/journal-entries/bulk-post/',
            type: 'POST',
            data: {
                'entry_ids': selectedEntries
            },
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    if (response.errors && response.errors.length > 0) {
                        showToast('warning', 'بعض القيود لم يتم ترحيلها: ' + response.errors.join(', '));
                    }
                    $('#journal-entries-table').DataTable().ajax.reload();
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في ترحيل القيود');
            }
        });
    });
}

/**
 * العمليات المجمعة - تعليق عدة حسابات
 */
function bulkSuspendAccounts() {
    const selectedAccounts = [];
    $('input[name="account_ids"]:checked').each(function() {
        selectedAccounts.push($(this).val());
    });

    if (selectedAccounts.length === 0) {
        showToast('warning', 'يرجى اختيار حساب واحد على الأقل');
        return;
    }

    confirmAction(`هل أنت متأكد من تعليق ${selectedAccounts.length} حساب؟`, function() {
        $.ajax({
            url: '/accounting/ajax/accounts/bulk-suspend/',
            type: 'POST',
            data: {
                'account_ids': selectedAccounts
            },
            success: function(response) {
                if (response.success) {
                    showToast('success', response.message);
                    $('#accounts-table').DataTable().ajax.reload();
                } else {
                    showToast('error', response.message);
                }
            },
            error: function() {
                showToast('error', 'حدث خطأ في تعليق الحسابات');
            }
        });
    });
}

// ========== Select All/None Functions ==========

/**
 * تحديد الكل/إلغاء تحديد الكل
 */
function toggleSelectAll(checkbox) {
    const isChecked = $(checkbox).is(':checked');
    const targetName = $(checkbox).data('target');

    $(`input[name="${targetName}"]`).prop('checked', isChecked);

    // تحديث عدد المحدد
    updateSelectedCount(targetName);
}

/**
 * تحديث عدد العناصر المحددة
 */
function updateSelectedCount(targetName) {
    const count = $(`input[name="${targetName}"]:checked`).length;
    $(`.selected-count[data-target="${targetName}"]`).text(count);

    // إظهار/إخفاء أزرار العمليات المجمعة
    if (count > 0) {
        $(`.bulk-actions[data-target="${targetName}"]`).show();
    } else {
        $(`.bulk-actions[data-target="${targetName}"]`).hide();
    }
}

// ========== DataTable Common Configuration ==========

/**
 * إعدادات DataTable المشتركة
 */
function getCommonDataTableConfig() {
    return {
        processing: true,
        serverSide: true,
        language: {
            url: '/static/plugins/datatables/ar.json', // ملف الترجمة العربية
            processing: "جاري التحميل...",
            search: "بحث:",
            lengthMenu: "إظهار _MENU_ عنصر",
            info: "عرض _START_ إلى _END_ من أصل _TOTAL_ عنصر",
            infoEmpty: "لا توجد عناصر للعرض",
            infoFiltered: "(مفلتر من _MAX_ عنصر إجمالي)",
            paginate: {
                first: "الأول",
                last: "الأخير",
                next: "التالي",
                previous: "السابق"
            }
        },
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        responsive: true,
        autoWidth: false,
        drawCallback: function() {
            // إعادة تفعيل tooltips بعد كل رسم
            $('[data-bs-toggle="tooltip"]').tooltip();
        }
    };
}

// ========== Form Enhancement Functions ==========

/**
 * تحسين نماذج الإدخال
 */
$(document).ready(function() {
    // تفعيل Select2 للحقول المحددة
    $('.select2').select2({
        theme: 'bootstrap4',
        width: '100%',
        language: "ar"
    });

    // تفعيل Datepicker
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd',
        language: 'ar',
        rtl: true,
        autoclose: true,
        todayHighlight: true
    });

    // تفعيل Number formatting
    $('.number-format').on('blur', function() {
        let value = parseFloat($(this).val());
        if (!isNaN(value)) {
            $(this).val(value.toFixed(2));
        }
    });
});

// ========== Print Functions ==========

/**
 * طباعة القيد
 */
function printJournalEntry(entryId) {
    window.open(`/accounting/journal-entries/${entryId}/print/`, '_blank');
}

/**
 * طباعة السند
 */
function printVoucher(voucherId, type) {
    window.open(`/accounting/${type}-vouchers/${voucherId}/print/`, '_blank');
}

// ========== Export Functions ==========

/**
 * تصدير الجدول الحالي
 */
function exportCurrentTable(format) {
    const table = $('.datatable').DataTable();
    if (format === 'excel') {
        table.button('.buttons-excel').trigger();
    } else if (format === 'pdf') {
        table.button('.buttons-pdf').trigger();
    }
}

// ========== Search Enhancement ==========

/**
 * البحث المتقدم
 */
function toggleAdvancedSearch() {
    $('#advanced-search-panel').toggle();
}

/**
 * مسح فلاتر البحث
 */
function clearSearchFilters() {
    $('#advanced-search-form')[0].reset();
    $('.datatable').DataTable().search('').columns().search('').draw();
}

// ========== Auto-save Draft ==========

/**
 * حفظ تلقائي للمسودات
 */
let autoSaveTimer;
function enableAutoSave(formSelector, saveUrl) {
    $(formSelector + ' input, ' + formSelector + ' textarea, ' + formSelector + ' select').on('input change', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            const formData = new FormData($(formSelector)[0]);

            $.ajax({
                url: saveUrl,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        showToast('info', 'تم الحفظ تلقائياً', 2000);
                    }
                }
            });
        }, 5000); // حفظ كل 5 ثواني
    });
}
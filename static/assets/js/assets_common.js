/**
 * ====================================================================
 * Assets Management System - Common JavaScript
 * ====================================================================
 * Version: 1.0
 * Description: Unified JavaScript for all assets module pages
 * ====================================================================
 */

(function($) {
    'use strict';

    // ====================================================================
    // 1. SELECT2 INITIALIZATION
    // ====================================================================

    /**
     * Initialize Select2 with RTL support and common options
     * @param {string} selector - jQuery selector for select elements
     * @param {object} customOptions - Additional Select2 options
     */
    window.initSelect2 = function(selector, customOptions) {
        selector = selector || '.select2-dropdown';
        customOptions = customOptions || {};

        const defaultOptions = {
            theme: 'bootstrap-5',
            width: '100%',
            dir: 'rtl',
            language: 'ar',
            placeholder: function() {
                return $(this).data('placeholder') || $(this).find('option:first').text() || 'اختر...';
            },
            allowClear: true,
            minimumResultsForSearch: 5
        };

        const options = $.extend({}, defaultOptions, customOptions);

        $(selector).each(function() {
            if (!$(this).hasClass('select2-hidden-accessible')) {
                $(this).select2(options);
            }
        });
    };

    /**
     * Initialize Select2 with AJAX support
     * @param {string} selector - jQuery selector
     * @param {string} url - AJAX URL for data
     * @param {function} processResults - Function to process results
     */
    window.initSelect2Ajax = function(selector, url, processResults) {
        $(selector).select2({
            theme: 'bootstrap-5',
            width: '100%',
            dir: 'rtl',
            language: 'ar',
            allowClear: true,
            ajax: {
                url: url,
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        q: params.term,
                        page: params.page || 1
                    };
                },
                processResults: processResults || function(data) {
                    return {
                        results: data.results,
                        pagination: {
                            more: data.pagination && data.pagination.more
                        }
                    };
                },
                cache: true
            },
            minimumInputLength: 1
        });
    };

    // ====================================================================
    // 2. DATATABLES INITIALIZATION
    // ====================================================================

    /**
     * Initialize DataTable with common settings
     * @param {string} tableId - Table element ID
     * @param {string} ajaxUrl - URL for server-side processing
     * @param {array} columns - Column definitions
     * @param {object} additionalOptions - Additional DataTable options
     */
    window.initDataTable = function(tableId, ajaxUrl, columns, additionalOptions) {
        additionalOptions = additionalOptions || {};

        const defaultOptions = {
            processing: true,
            serverSide: true,
            ajax: {
                url: ajaxUrl,
                type: 'GET',
                data: function(d) {
                    // Add filter parameters
                    $('.filter-input').each(function() {
                        const name = $(this).attr('name');
                        const value = $(this).val();
                        if (name && value) {
                            d[name] = value;
                        }
                    });
                }
            },
            columns: columns,
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/ar.json',
                processing: '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">جاري التحميل...</span></div>'
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
            order: [[0, 'desc']],
            responsive: true,
            autoWidth: false,
            drawCallback: function() {
                // Re-initialize tooltips after table draw
                $('[data-bs-toggle="tooltip"]').tooltip();
            }
        };

        const options = $.extend(true, {}, defaultOptions, additionalOptions);

        return $(tableId).DataTable(options);
    };

    /**
     * Reload DataTable with current filters
     * @param {object} table - DataTable instance
     */
    window.reloadDataTable = function(table) {
        if (table) {
            table.ajax.reload(null, false);
        }
    };

    /**
     * Export DataTable to Excel
     * @param {string} tableId - Table element ID
     * @param {string} filename - Export filename
     */
    window.exportTableToExcel = function(tableId, filename) {
        const table = $(tableId).DataTable();
        const data = table.buttons.exportData();

        // Create workbook and worksheet
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet([data.header, ...data.body]);

        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(wb, ws, "Sheet1");

        // Save file
        XLSX.writeFile(wb, filename + '.xlsx');
    };

    // ====================================================================
    // 3. SWEETALERT2 DIALOGS
    // ====================================================================

    /**
     * Show success message
     * @param {string} message - Success message
     * @param {string} title - Dialog title
     */
    window.showSuccess = function(message, title) {
        Swal.fire({
            icon: 'success',
            title: title || 'نجح!',
            text: message,
            confirmButtonText: 'حسناً',
            confirmButtonColor: '#4caf50',
            timer: 3000,
            timerProgressBar: true
        });
    };

    /**
     * Show error message
     * @param {string} message - Error message
     * @param {string} title - Dialog title
     */
    window.showError = function(message, title) {
        Swal.fire({
            icon: 'error',
            title: title || 'خطأ!',
            text: message,
            confirmButtonText: 'حسناً',
            confirmButtonColor: '#f44336'
        });
    };

    /**
     * Show warning message
     * @param {string} message - Warning message
     * @param {string} title - Dialog title
     */
    window.showWarning = function(message, title) {
        Swal.fire({
            icon: 'warning',
            title: title || 'تحذير!',
            text: message,
            confirmButtonText: 'حسناً',
            confirmButtonColor: '#ff9800'
        });
    };

    /**
     * Show confirmation dialog
     * @param {string} title - Dialog title
     * @param {string} message - Confirmation message (can contain HTML)
     * @param {string} confirmText - Confirm button text
     * @param {string} cancelText - Cancel button text
     * @param {string} confirmColor - Confirm button color (optional)
     * @returns {Promise} - Swal promise
     */
    window.showConfirm = function(title, message, confirmText, cancelText, confirmColor) {
        return Swal.fire({
            icon: 'question',
            title: title || 'تأكيد',
            html: message || '',
            showCancelButton: true,
            confirmButtonText: confirmText || 'نعم، متأكد',
            cancelButtonText: cancelText || 'إلغاء',
            confirmButtonColor: confirmColor || '#2196f3',
            cancelButtonColor: '#9e9e9e',
            reverseButtons: true
        });
    };

    /**
     * Show delete confirmation dialog
     * @param {string} itemName - Name of item to delete
     * @param {string} deleteUrl - URL for delete action
     * @param {function} onSuccess - Callback on successful delete
     */
    window.confirmDelete = function(itemName, deleteUrl, onSuccess) {
        Swal.fire({
            icon: 'warning',
            title: 'تأكيد الحذف',
            html: `هل أنت متأكد من حذف <strong>${itemName}</strong>؟<br><small class="text-danger">لا يمكن التراجع عن هذا الإجراء!</small>`,
            showCancelButton: true,
            confirmButtonText: 'نعم، احذف',
            cancelButtonText: 'إلغاء',
            confirmButtonColor: '#f44336',
            cancelButtonColor: '#9e9e9e',
            reverseButtons: true,
            input: 'checkbox',
            inputPlaceholder: 'أنا متأكد من الحذف',
            inputValidator: (result) => {
                return !result && 'يجب تأكيد الحذف';
            }
        }).then((result) => {
            if (result.isConfirmed) {
                // Show loading
                Swal.fire({
                    title: 'جاري الحذف...',
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    showConfirmButton: false,
                    willOpen: () => {
                        Swal.showLoading();
                    }
                });

                // Send delete request
                $.ajax({
                    url: deleteUrl,
                    type: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    },
                    success: function(response) {
                        Swal.close();
                        if (response.success) {
                            showSuccess(response.message || 'تم الحذف بنجاح');
                            if (typeof onSuccess === 'function') {
                                onSuccess(response);
                            }
                        } else {
                            showError(response.error || 'فشل الحذف');
                        }
                    },
                    error: function(xhr) {
                        Swal.close();
                        const message = xhr.responseJSON?.error || 'حدث خطأ أثناء الحذف';
                        showError(message);
                    }
                });
            }
        });
    };

    /**
     * Show loading dialog
     * @param {string} message - Loading message
     */
    window.showLoading = function(message) {
        Swal.fire({
            title: message || 'جاري التحميل...',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            willOpen: () => {
                Swal.showLoading();
            }
        });
    };

    /**
     * Close all Swal dialogs
     */
    window.closeLoading = function() {
        Swal.close();
    };

    // ====================================================================
    // 4. FORM UTILITIES
    // ====================================================================

    /**
     * Initialize form change tracking
     * @param {string} formId - Form element ID
     */
    window.initFormChangeTracking = function(formId) {
        let formChanged = false;

        $(`${formId} :input`).on('change input', function() {
            formChanged = true;
        });

        $(formId).on('submit', function() {
            formChanged = false;
            $(this).data('submitting', true);
        });

        $(window).on('beforeunload', function() {
            if (formChanged && !$(formId).data('submitting')) {
                return 'لديك تغييرات غير محفوظة. هل تريد المغادرة؟';
            }
        });
    };

    /**
     * Validate form before submission
     * @param {string} formId - Form element ID
     * @returns {boolean} - Validation result
     */
    window.validateForm = function(formId) {
        const form = $(formId)[0];
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return false;
        }
        return true;
    };

    /**
     * Reset form validation
     * @param {string} formId - Form element ID
     */
    window.resetFormValidation = function(formId) {
        $(formId)[0].classList.remove('was-validated');
        $(formId).find('.is-invalid').removeClass('is-invalid');
        $(formId).find('.invalid-feedback').remove();
    };

    /**
     * Show field error
     * @param {string} fieldName - Field name
     * @param {string} errorMessage - Error message
     */
    window.showFieldError = function(fieldName, errorMessage) {
        const field = $(`[name="${fieldName}"]`);
        field.addClass('is-invalid');

        // Remove existing error
        field.next('.invalid-feedback').remove();

        // Add new error
        field.after(`<div class="invalid-feedback d-block">${errorMessage}</div>`);
    };

    /**
     * Clear all field errors
     */
    window.clearFieldErrors = function() {
        $('.is-invalid').removeClass('is-invalid');
        $('.invalid-feedback').remove();
    };

    /**
     * Serialize form to JSON
     * @param {string} formId - Form element ID
     * @returns {object} - Form data as JSON
     */
    window.serializeFormJSON = function(formId) {
        const formData = $(formId).serializeArray();
        const json = {};

        $.each(formData, function() {
            if (json[this.name]) {
                if (!json[this.name].push) {
                    json[this.name] = [json[this.name]];
                }
                json[this.name].push(this.value || '');
            } else {
                json[this.name] = this.value || '';
            }
        });

        return json;
    };

    // ====================================================================
    // 5. KEYBOARD SHORTCUTS
    // ====================================================================

    /**
     * Initialize global keyboard shortcuts
     * @param {object} shortcuts - Shortcut definitions
     */
    window.initKeyboardShortcuts = function(shortcuts) {
        shortcuts = shortcuts || {};

        // Default shortcuts
        const defaultShortcuts = {
            'ctrl+s': function(e) {
                e.preventDefault();
                $('form').first().submit();
            },
            'esc': function(e) {
                const cancelBtn = $('.btn-cancel, .btn-back').first();
                if (cancelBtn.length) {
                    window.location.href = cancelBtn.attr('href');
                }
            },
            'ctrl+p': function(e) {
                e.preventDefault();
                window.print();
            }
        };

        const allShortcuts = $.extend({}, defaultShortcuts, shortcuts);

        $(document).on('keydown', function(e) {
            const key = [];

            if (e.ctrlKey) key.push('ctrl');
            if (e.shiftKey) key.push('shift');
            if (e.altKey) key.push('alt');

            const specialKeys = {
                27: 'esc',
                13: 'enter',
                32: 'space',
                9: 'tab'
            };

            if (specialKeys[e.which]) {
                key.push(specialKeys[e.which]);
            } else if (e.which >= 65 && e.which <= 90) {
                key.push(String.fromCharCode(e.which).toLowerCase());
            }

            const shortcut = key.join('+');

            if (allShortcuts[shortcut]) {
                allShortcuts[shortcut](e);
            }
        });
    };

    // ====================================================================
    // 6. AJAX UTILITIES
    // ====================================================================

    /**
     * Get CSRF token
     * @returns {string} - CSRF token
     */
    window.getCsrfToken = function() {
        return $('[name=csrfmiddlewaretoken]').val() ||
               $('meta[name="csrf-token"]').attr('content') ||
               Cookies.get('csrftoken');
    };

    /**
     * Setup AJAX CSRF token
     */
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
            }
        }
    });

    /**
     * Make AJAX request with loading indicator
     * @param {object} options - AJAX options
     */
    window.ajaxRequest = function(options) {
        const defaults = {
            showLoading: true,
            loadingMessage: 'جاري التحميل...',
            successMessage: null,
            errorMessage: 'حدث خطأ أثناء العملية'
        };

        const settings = $.extend({}, defaults, options);

        if (settings.showLoading) {
            showLoading(settings.loadingMessage);
        }

        const ajaxOptions = {
            type: settings.type || 'GET',
            url: settings.url,
            data: settings.data,
            dataType: settings.dataType || 'json',
            success: function(response) {
                if (settings.showLoading) {
                    closeLoading();
                }

                if (settings.successMessage) {
                    showSuccess(settings.successMessage);
                }

                if (typeof settings.success === 'function') {
                    settings.success(response);
                }
            },
            error: function(xhr) {
                if (settings.showLoading) {
                    closeLoading();
                }

                const message = xhr.responseJSON?.error || settings.errorMessage;
                showError(message);

                if (typeof settings.error === 'function') {
                    settings.error(xhr);
                }
            }
        };

        $.ajax(ajaxOptions);
    };

    // ====================================================================
    // 7. STATISTICS CARD ANIMATIONS
    // ====================================================================

    /**
     * Animate number counting in stat cards
     * @param {string} selector - Element selector
     * @param {number} endValue - Target value
     * @param {number} duration - Animation duration in ms
     */
    window.animateCounter = function(selector, endValue, duration) {
        duration = duration || 1000;
        const element = $(selector);
        const startValue = 0;
        const startTime = Date.now();

        function update() {
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const currentValue = Math.floor(startValue + (endValue - startValue) * progress);
            element.text(currentValue.toLocaleString('ar-SA'));

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.text(endValue.toLocaleString('ar-SA'));
            }
        }

        requestAnimationFrame(update);
    };

    /**
     * Load and animate statistics
     * @param {string} ajaxUrl - URL to fetch stats
     * @param {object} selectors - Mapping of stat keys to selectors
     */
    window.loadStatistics = function(ajaxUrl, selectors) {
        $.ajax({
            url: ajaxUrl,
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                if (response.success && response.stats) {
                    $.each(response.stats, function(key, value) {
                        if (selectors[key]) {
                            if (typeof value === 'number') {
                                animateCounter(selectors[key], value);
                            } else {
                                $(selectors[key]).text(value);
                            }
                        }
                    });
                }
            },
            error: function() {
                console.error('Failed to load statistics');
            }
        });
    };

    // ====================================================================
    // 8. FILE UPLOAD UTILITIES
    // ====================================================================

    /**
     * Initialize file input with preview
     * @param {string} inputSelector - File input selector
     * @param {string} previewSelector - Preview container selector
     */
    window.initFileUpload = function(inputSelector, previewSelector) {
        $(inputSelector).on('change', function(e) {
            const files = e.target.files;
            const preview = $(previewSelector);
            preview.empty();

            $.each(files, function(index, file) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    if (file.type.startsWith('image/')) {
                        preview.append(`
                            <div class="file-preview-item">
                                <img src="${e.target.result}" alt="${file.name}">
                                <span class="file-name">${file.name}</span>
                            </div>
                        `);
                    } else {
                        preview.append(`
                            <div class="file-preview-item">
                                <i class="fas fa-file fa-3x"></i>
                                <span class="file-name">${file.name}</span>
                            </div>
                        `);
                    }
                };

                reader.readAsDataURL(file);
            });
        });
    };

    /**
     * Upload file via AJAX
     * @param {string} url - Upload URL
     * @param {FormData} formData - Form data with file
     * @param {function} onSuccess - Success callback
     * @param {function} onProgress - Progress callback
     */
    window.uploadFile = function(url, formData, onSuccess, onProgress) {
        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                const xhr = new window.XMLHttpRequest();

                if (typeof onProgress === 'function') {
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            const percent = Math.round((e.loaded / e.total) * 100);
                            onProgress(percent);
                        }
                    });
                }

                return xhr;
            },
            success: function(response) {
                if (typeof onSuccess === 'function') {
                    onSuccess(response);
                }
            },
            error: function(xhr) {
                const message = xhr.responseJSON?.error || 'فشل رفع الملف';
                showError(message);
            }
        });
    };

    // ====================================================================
    // 9. DATE & TIME UTILITIES
    // ====================================================================

    /**
     * Initialize date pickers
     * @param {string} selector - Date input selector
     */
    window.initDatePicker = function(selector) {
        selector = selector || '.datepicker';

        $(selector).each(function() {
            if (!$(this).data('datepicker-initialized')) {
                $(this).datepicker({
                    format: 'yyyy-mm-dd',
                    language: 'ar',
                    orientation: 'bottom auto',
                    autoclose: true,
                    todayHighlight: true,
                    rtl: true
                });

                $(this).data('datepicker-initialized', true);
            }
        });
    };

    /**
     * Format date to Arabic
     * @param {string} dateString - Date string
     * @returns {string} - Formatted date
     */
    window.formatDateArabic = function(dateString) {
        if (!dateString) return '-';

        const date = new Date(dateString);
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('ar-SA', options);
    };

    /**
     * Calculate date difference in days
     * @param {string} date1 - First date
     * @param {string} date2 - Second date
     * @returns {number} - Difference in days
     */
    window.dateDiffInDays = function(date1, date2) {
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        const diffTime = Math.abs(d2 - d1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    };

    // ====================================================================
    // 10. PRINT UTILITIES
    // ====================================================================

    /**
     * Print element content
     * @param {string} selector - Element selector to print
     * @param {string} title - Print title
     */
    window.printElement = function(selector, title) {
        const content = $(selector).html();
        const printWindow = window.open('', '_blank');

        printWindow.document.write(`
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <title>${title || 'طباعة'}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
                <style>
                    @media print {
                        @page { margin: 1cm; }
                        body { font-family: 'Arial', sans-serif; }
                        .no-print { display: none !important; }
                    }
                </style>
            </head>
            <body>
                ${content}
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
            </html>
        `);

        printWindow.document.close();
    };

    // ====================================================================
    // 11. NOTIFICATION UTILITIES
    // ====================================================================

    /**
     * Show toast notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, warning, info)
     */
    window.showToast = function(message, type) {
        type = type || 'info';

        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });

        Toast.fire({
            icon: type,
            title: message
        });
    };

    // ====================================================================
    // 12. RESPONSIVE TABLE UTILITIES
    // ====================================================================

    /**
     * Make table responsive by wrapping in scrollable div
     * @param {string} selector - Table selector
     */
    window.makeTableResponsive = function(selector) {
        $(selector).each(function() {
            if (!$(this).parent().hasClass('table-responsive')) {
                $(this).wrap('<div class="table-responsive"></div>');
            }
        });
    };

    // ====================================================================
    // 13. CLIPBOARD UTILITIES
    // ====================================================================

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     */
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('تم النسخ إلى الحافظة', 'success');
            }).catch(function() {
                showToast('فشل النسخ', 'error');
            });
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = 0;
            document.body.appendChild(textarea);
            textarea.select();

            try {
                document.execCommand('copy');
                showToast('تم النسخ إلى الحافظة', 'success');
            } catch (err) {
                showToast('فشل النسخ', 'error');
            }

            document.body.removeChild(textarea);
        }
    };

    // ====================================================================
    // 14. AUTO-INITIALIZATION ON DOCUMENT READY
    // ====================================================================

    $(document).ready(function() {
        // Initialize tooltips
        $('[data-bs-toggle="tooltip"]').tooltip();

        // Initialize popovers
        $('[data-bs-toggle="popover"]').popover();

        // Initialize Select2 dropdowns
        if (typeof $.fn.select2 !== 'undefined') {
            initSelect2('.select2-dropdown');
        }

        // Initialize date pickers
        if (typeof $.fn.datepicker !== 'undefined') {
            initDatePicker('.datepicker');
        }

        // Make tables responsive
        makeTableResponsive('table:not(.no-responsive)');

        // Initialize copy buttons
        $('.btn-copy').on('click', function() {
            const text = $(this).data('copy-text');
            copyToClipboard(text);
        });

        // Initialize print buttons
        $('.btn-print').on('click', function(e) {
            e.preventDefault();
            window.print();
        });

        // Smooth scroll to top button
        $(window).scroll(function() {
            if ($(this).scrollTop() > 200) {
                $('.scroll-to-top').fadeIn();
            } else {
                $('.scroll-to-top').fadeOut();
            }
        });

        $('.scroll-to-top').click(function() {
            $('html, body').animate({scrollTop: 0}, 600);
            return false;
        });
    });

})(jQuery);

// ====================================================================
// END OF COMMON JAVASCRIPT
// ====================================================================

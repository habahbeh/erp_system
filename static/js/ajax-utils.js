/**
 * AJAX Utilities for Dynamic Operations
 * Provides reusable AJAX functions and helpers
 */

// Toast notification system
class ToastNotifier {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            this.container = container;
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 3000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });

        bsToast.show();

        // Remove from DOM after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white border-0';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        // Set background color based on type
        const bgColors = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning',
            info: 'bg-info'
        };
        toast.classList.add(bgColors[type] || bgColors.info);

        // Set icon based on type
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        const icon = icons[type] || icons.info;

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        return toast;
    }

    success(message, duration = 3000) {
        this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        this.show(message, 'info', duration);
    }
}

// Global toast instance
const toast = new ToastNotifier();

// AJAX Helper Class
class AjaxHelper {
    /**
     * Get CSRF token from cookies
     */
    static getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Make AJAX POST request
     */
    static async post(url, data, options = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    ...options.headers
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'حدث خطأ في الطلب');
            }

            return result;
        } catch (error) {
            console.error('AJAX Error:', error);
            throw error;
        }
    }

    /**
     * Make AJAX GET request
     */
    static async get(url, params = {}, options = {}) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const fullUrl = queryString ? `${url}?${queryString}` : url;

            const response = await fetch(fullUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'حدث خطأ في الطلب');
            }

            return result;
        } catch (error) {
            console.error('AJAX Error:', error);
            throw error;
        }
    }

    /**
     * Show loading indicator
     */
    static showLoading(element) {
        if (element) {
            element.disabled = true;
            element.dataset.originalHtml = element.innerHTML;
            element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحميل...';
        }
    }

    /**
     * Hide loading indicator
     */
    static hideLoading(element) {
        if (element && element.dataset.originalHtml) {
            element.disabled = false;
            element.innerHTML = element.dataset.originalHtml;
            delete element.dataset.originalHtml;
        }
    }

    /**
     * Display form validation errors
     */
    static displayFormErrors(formElement, errors) {
        // Clear previous errors
        formElement.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        formElement.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });

        // Display new errors
        for (const [field, messages] of Object.entries(errors)) {
            const input = formElement.querySelector(`[name="${field}"]`);
            if (input) {
                input.classList.add('is-invalid');

                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = messages.join(', ');

                input.parentNode.appendChild(feedback);
            }
        }
    }

    /**
     * Clear form validation errors
     */
    static clearFormErrors(formElement) {
        formElement.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        formElement.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
    }
}

// Price Operations
class PriceOperations {
    /**
     * Update single price
     */
    static async updatePrice(priceItemId, newPrice) {
        try {
            const result = await AjaxHelper.post('/datatables/update-price/', {
                price_item_id: priceItemId,
                new_price: newPrice
            });

            if (result.success) {
                toast.success(result.message);
                return result.data;
            } else {
                toast.error(result.message);
                return null;
            }
        } catch (error) {
            toast.error('حدث خطأ في تحديث السعر');
            return null;
        }
    }

    /**
     * Bulk update prices
     */
    static async bulkUpdatePrices(updates) {
        try {
            const result = await AjaxHelper.post('/datatables/bulk-update-prices/', {
                updates: updates
            });

            if (result.success) {
                toast.success(result.message);
                if (result.data.errors.length > 0) {
                    toast.warning(`تحذير: ${result.data.errors.length} أخطاء`);
                }
                return result.data;
            } else {
                toast.error(result.message);
                return null;
            }
        } catch (error) {
            toast.error('حدث خطأ في التحديث الجماعي');
            return null;
        }
    }

    /**
     * Calculate price with rules
     */
    static async calculatePrice(itemId, quantity = 1, priceListId = null, applyRules = true) {
        try {
            const result = await AjaxHelper.post('/datatables/calculate-price/', {
                item_id: itemId,
                quantity: quantity,
                price_list_id: priceListId,
                apply_rules: applyRules
            });

            if (result.success) {
                return result.data;
            } else {
                toast.error(result.message);
                return null;
            }
        } catch (error) {
            toast.error('حدث خطأ في حساب السعر');
            return null;
        }
    }

    /**
     * Toggle pricing rule status
     */
    static async togglePricingRule(ruleId) {
        try {
            const result = await AjaxHelper.post('/datatables/toggle-rule/', {
                rule_id: ruleId
            });

            if (result.success) {
                toast.success(result.message);
                return result.data;
            } else {
                toast.error(result.message);
                return null;
            }
        } catch (error) {
            toast.error('حدث خطأ في تحديث القاعدة');
            return null;
        }
    }

    /**
     * Get item prices
     */
    static async getItemPrices(itemId) {
        try {
            const result = await AjaxHelper.get('/datatables/get-item-prices/', {
                item_id: itemId
            });

            if (result.success) {
                return result.data;
            } else {
                toast.error(result.message);
                return null;
            }
        } catch (error) {
            toast.error('حدث خطأ في جلب الأسعار');
            return null;
        }
    }
}

// Form Utilities
class FormUtils {
    /**
     * Serialize form to JSON
     */
    static serializeToJSON(formElement) {
        const formData = new FormData(formElement);
        const data = {};

        for (const [key, value] of formData.entries()) {
            // Handle multiple values (checkboxes, multi-select)
            if (data[key]) {
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        return data;
    }

    /**
     * Reset form and clear errors
     */
    static reset(formElement) {
        formElement.reset();
        AjaxHelper.clearFormErrors(formElement);
    }

    /**
     * Disable form
     */
    static disable(formElement) {
        formElement.querySelectorAll('input, select, textarea, button').forEach(el => {
            el.disabled = true;
        });
    }

    /**
     * Enable form
     */
    static enable(formElement) {
        formElement.querySelectorAll('input, select, textarea, button').forEach(el => {
            el.disabled = false;
        });
    }
}

// Dynamic Field Updates
class DynamicFields {
    /**
     * Show/hide fields based on condition
     */
    static toggleFieldVisibility(fieldElement, show) {
        if (show) {
            fieldElement.style.display = '';
            fieldElement.closest('.mb-3, .form-group')?.style.setProperty('display', '', 'important');
        } else {
            fieldElement.style.display = 'none';
            fieldElement.closest('.mb-3, .form-group')?.style.setProperty('display', 'none', 'important');
        }
    }

    /**
     * Update field options dynamically
     */
    static updateSelectOptions(selectElement, options) {
        selectElement.innerHTML = '';

        options.forEach(option => {
            const optElement = document.createElement('option');
            optElement.value = option.value;
            optElement.textContent = option.label;
            if (option.selected) {
                optElement.selected = true;
            }
            selectElement.appendChild(optElement);
        });

        // Trigger change event
        selectElement.dispatchEvent(new Event('change'));
    }

    /**
     * Populate form from data
     */
    static populateForm(formElement, data) {
        for (const [key, value] of Object.entries(data)) {
            const input = formElement.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = !!value;
                } else if (input.type === 'radio') {
                    const radio = formElement.querySelector(`[name="${key}"][value="${value}"]`);
                    if (radio) radio.checked = true;
                } else {
                    input.value = value;
                }
            }
        }
    }
}

// Confirmation Dialog
class ConfirmDialog {
    static async show(message, title = 'تأكيد') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                            <button type="button" class="btn btn-primary confirm-btn">تأكيد</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            modal.querySelector('.confirm-btn').addEventListener('click', () => {
                bsModal.hide();
                resolve(true);
            });

            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });
        });
    }
}

// Export for global use
window.toast = toast;
window.AjaxHelper = AjaxHelper;
window.PriceOperations = PriceOperations;
window.FormUtils = FormUtils;
window.DynamicFields = DynamicFields;
window.ConfirmDialog = ConfirmDialog;

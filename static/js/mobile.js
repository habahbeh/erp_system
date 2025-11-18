/**
 * Mobile Utilities
 * JavaScript utilities for mobile optimization
 */

// ==================== Mobile Detection ====================
const MobileDetector = {
    /**
     * Check if device is mobile
     */
    isMobile() {
        return window.matchMedia('(max-width: 767.98px)').matches;
    },

    /**
     * Check if device is tablet
     */
    isTablet() {
        return window.matchMedia('(min-width: 768px) and (max-width: 991.98px)').matches;
    },

    /**
     * Check if device is touch-enabled
     */
    isTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    },

    /**
     * Get device type
     */
    getDeviceType() {
        if (this.isMobile()) return 'mobile';
        if (this.isTablet()) return 'tablet';
        return 'desktop';
    },

    /**
     * Check if landscape orientation
     */
    isLandscape() {
        return window.matchMedia('(orientation: landscape)').matches;
    }
};

// ==================== Mobile Sidebar ====================
class MobileSidebar {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.overlay = null;
        this.toggleBtn = null;
        this.isOpen = false;

        this.init();
    }

    init() {
        if (!MobileDetector.isMobile()) return;

        // Create overlay
        this.createOverlay();

        // Create toggle button
        this.createToggleButton();

        // Add event listeners
        this.addEventListeners();
    }

    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'sidebar-overlay';
        document.body.appendChild(this.overlay);
    }

    createToggleButton() {
        // Check if button already exists
        if (document.querySelector('.mobile-menu-toggle')) return;

        this.toggleBtn = document.createElement('button');
        this.toggleBtn.className = 'mobile-menu-toggle';
        this.toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        this.toggleBtn.setAttribute('aria-label', 'فتح القائمة');

        // Insert in navbar
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.insertBefore(this.toggleBtn, navbar.firstChild);
        }
    }

    addEventListeners() {
        // Toggle button click
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Overlay click
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.close());
        }

        // Close on sidebar link click
        if (this.sidebar) {
            const links = this.sidebar.querySelectorAll('a');
            links.forEach(link => {
                link.addEventListener('click', () => {
                    if (MobileDetector.isMobile()) {
                        this.close();
                    }
                });
            });
        }

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            if (this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        if (this.sidebar) {
            this.sidebar.classList.add('show');
        }
        if (this.overlay) {
            this.overlay.classList.add('show');
        }
        this.isOpen = true;
        document.body.style.overflow = 'hidden';
    }

    close() {
        if (this.sidebar) {
            this.sidebar.classList.remove('show');
        }
        if (this.overlay) {
            this.overlay.classList.remove('show');
        }
        this.isOpen = false;
        document.body.style.overflow = '';
    }
}

// ==================== Touch Gestures ====================
class TouchGestures {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            swipeThreshold: 50,
            tapTimeout: 300,
            ...options
        };

        this.startX = 0;
        this.startY = 0;
        this.startTime = 0;

        this.init();
    }

    init() {
        if (!this.element) return;

        this.element.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.element.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
    }

    handleTouchStart(e) {
        this.startX = e.touches[0].clientX;
        this.startY = e.touches[0].clientY;
        this.startTime = Date.now();
    }

    handleTouchEnd(e) {
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        const endTime = Date.now();

        const deltaX = endX - this.startX;
        const deltaY = endY - this.startY;
        const deltaTime = endTime - this.startTime;

        // Detect swipe
        if (Math.abs(deltaX) > this.options.swipeThreshold || Math.abs(deltaY) > this.options.swipeThreshold) {
            const direction = this.getSwipeDirection(deltaX, deltaY);
            this.triggerEvent('swipe', { direction, deltaX, deltaY });
        }

        // Detect tap
        if (deltaTime < this.options.tapTimeout && Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10) {
            this.triggerEvent('tap', { x: endX, y: endY });
        }
    }

    getSwipeDirection(deltaX, deltaY) {
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            return deltaX > 0 ? 'right' : 'left';
        } else {
            return deltaY > 0 ? 'down' : 'up';
        }
    }

    triggerEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        this.element.dispatchEvent(event);
    }

    on(eventName, callback) {
        this.element.addEventListener(eventName, callback);
        return this;
    }
}

// ==================== Mobile Table Optimizer ====================
class MobileTableOptimizer {
    constructor() {
        this.tables = document.querySelectorAll('.table-responsive table');
        this.init();
    }

    init() {
        if (!MobileDetector.isMobile()) return;

        this.tables.forEach(table => {
            this.optimizeTable(table);
        });
    }

    optimizeTable(table) {
        // Add mobile-compact class if specified
        if (table.dataset.mobileCompact === 'true') {
            table.classList.add('table-mobile-compact');
            this.addDataLabels(table);
        }

        // Optimize action buttons
        this.optimizeActionButtons(table);
    }

    addDataLabels(table) {
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (headers[index]) {
                    cell.setAttribute('data-label', headers[index]);
                }
            });
        });
    }

    optimizeActionButtons(table) {
        const actionCells = table.querySelectorAll('td .btn-group, td .table-actions');
        actionCells.forEach(group => {
            group.classList.add('btn-group-vertical', 'btn-group-sm');
        });
    }
}

// ==================== Mobile Form Optimizer ====================
class MobileFormOptimizer {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }

    init() {
        if (!MobileDetector.isMobile()) return;

        this.forms.forEach(form => {
            this.optimizeForm(form);
        });
    }

    optimizeForm(form) {
        // Add sticky form actions
        this.addStickyActions(form);

        // Optimize select fields
        this.optimizeSelects(form);

        // Add input validation feedback
        this.addValidationFeedback(form);
    }

    addStickyActions(form) {
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');

        if (submitButtons.length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'form-actions';

            submitButtons.forEach(btn => {
                actionsDiv.appendChild(btn.cloneNode(true));
                btn.style.display = 'none';
            });

            form.appendChild(actionsDiv);
        }
    }

    optimizeSelects(form) {
        const selects = form.querySelectorAll('select');
        selects.forEach(select => {
            // Add size attribute for better mobile display
            if (!select.hasAttribute('size')) {
                select.style.fontSize = '16px'; // Prevent zoom on iOS
            }
        });
    }

    addValidationFeedback(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                e.preventDefault();
                input.classList.add('is-invalid');

                // Scroll to first invalid field
                if (input === form.querySelector('.is-invalid')) {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });

            input.addEventListener('input', () => {
                input.classList.remove('is-invalid');
            });
        });
    }
}

// ==================== Mobile Chart Optimizer ====================
class MobileChartOptimizer {
    constructor() {
        this.charts = [];
        this.init();
    }

    init() {
        if (!MobileDetector.isMobile()) return;

        // Optimize existing charts
        if (window.Chart) {
            this.optimizeChartDefaults();
        }

        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    optimizeChartDefaults() {
        // Set mobile-friendly defaults for Chart.js
        if (window.Chart) {
            Chart.defaults.font.size = 11;
            Chart.defaults.plugins.legend.labels.padding = 10;
            Chart.defaults.plugins.legend.labels.boxWidth = 12;
        }
    }

    handleResize() {
        // Charts auto-resize, but we can add custom logic here
        if (MobileDetector.isMobile()) {
            this.optimizeChartDefaults();
        }
    }

    registerChart(chart) {
        this.charts.push(chart);
    }
}

// ==================== Performance Monitor ====================
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            loadTime: 0,
            renderTime: 0,
            interactionTime: 0
        };

        this.init();
    }

    init() {
        // Measure page load time
        window.addEventListener('load', () => {
            this.metrics.loadTime = performance.now();
            console.log(`Page loaded in ${this.metrics.loadTime.toFixed(2)}ms`);
        });

        // Measure first interaction
        const events = ['click', 'touchstart', 'keydown'];
        events.forEach(event => {
            document.addEventListener(event, () => {
                if (this.metrics.interactionTime === 0) {
                    this.metrics.interactionTime = performance.now();
                    console.log(`First interaction at ${this.metrics.interactionTime.toFixed(2)}ms`);
                }
            }, { once: true });
        });
    }

    getMetrics() {
        return this.metrics;
    }
}

// ==================== Lazy Loading ====================
class LazyLoader {
    constructor() {
        this.images = document.querySelectorAll('img[data-src]');
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.observeImages();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }
    }

    observeImages() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px'
        });

        this.images.forEach(img => observer.observe(img));
    }

    loadImage(img) {
        const src = img.getAttribute('data-src');
        if (src) {
            img.src = src;
            img.removeAttribute('data-src');
        }
    }

    loadAllImages() {
        this.images.forEach(img => this.loadImage(img));
    }
}

// ==================== Orientation Handler ====================
class OrientationHandler {
    constructor() {
        this.currentOrientation = this.getOrientation();
        this.init();
    }

    init() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // Also listen to resize as fallback
        window.addEventListener('resize', () => {
            const newOrientation = this.getOrientation();
            if (newOrientation !== this.currentOrientation) {
                this.currentOrientation = newOrientation;
                this.handleOrientationChange();
            }
        });
    }

    getOrientation() {
        return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    }

    handleOrientationChange() {
        // Add class to body
        document.body.classList.remove('orientation-portrait', 'orientation-landscape');
        document.body.classList.add(`orientation-${this.currentOrientation}`);

        // Trigger custom event
        const event = new CustomEvent('orientationchange', {
            detail: { orientation: this.currentOrientation }
        });
        document.dispatchEvent(event);

        console.log(`Orientation changed to ${this.currentOrientation}`);
    }
}

// ==================== Mobile Utilities Helper ====================
const MobileUtils = {
    /**
     * Disable zoom on input focus (iOS)
     */
    disableInputZoom() {
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (parseFloat(window.getComputedStyle(input).fontSize) < 16) {
                input.style.fontSize = '16px';
            }
        });
    },

    /**
     * Add touch ripple effect
     */
    addRippleEffect(element) {
        element.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);

            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            setTimeout(() => ripple.remove(), 600);
        });
    },

    /**
     * Smooth scroll to element
     */
    smoothScroll(target, offset = 0) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (element) {
            const top = element.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    },

    /**
     * Vibrate device (if supported)
     */
    vibrate(pattern = 50) {
        if ('vibrate' in navigator) {
            navigator.vibrate(pattern);
        }
    },

    /**
     * Check if online
     */
    isOnline() {
        return navigator.onLine;
    },

    /**
     * Get connection type
     */
    getConnectionType() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        return connection ? connection.effectiveType : 'unknown';
    }
};

// ==================== Initialize on DOM Ready ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile sidebar
    if (MobileDetector.isMobile()) {
        new MobileSidebar();
        new MobileTableOptimizer();
        new MobileFormOptimizer();
        new MobileChartOptimizer();
        new LazyLoader();
        new OrientationHandler();
        new PerformanceMonitor();

        // Disable input zoom
        MobileUtils.disableInputZoom();

        // Add mobile class to body
        document.body.classList.add('is-mobile');

        console.log('Mobile optimizations initialized');
    }

    // Add device type class to body
    document.body.classList.add(`device-${MobileDetector.getDeviceType()}`);

    // Add touch class if touch-enabled
    if (MobileDetector.isTouch()) {
        document.body.classList.add('is-touch');
    }
});

// ==================== Export for external use ====================
window.MobileDetector = MobileDetector;
window.MobileSidebar = MobileSidebar;
window.TouchGestures = TouchGestures;
window.MobileUtils = MobileUtils;

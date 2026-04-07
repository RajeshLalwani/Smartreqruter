/**
 * SmartRecruit UI Enhancements
 * Dark mode, loading states, and utility functions
 */

// ========================================
// DARK MODE TOGGLE
// ========================================

// Check for saved theme preference or default to 'light'
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);

// ========================================
// BG THEME + FONT SCALE PERSISTENCE
// ========================================
(function applyPersistedSettings() {
    const BG_THEMES = {
        'midnight-nebula': 'linear-gradient(135deg,#0a081a 0%,#1a1635 50%,#0f0f1a 100%)',
        'ocean-abyss': 'linear-gradient(135deg,#020c1b 0%,#0a2349 50%,#051024 100%)',
        'volcanic-night': 'linear-gradient(135deg,#1a0505 0%,#2d0a0a 50%,#1a0a05 100%)',
        'forest-dark': 'linear-gradient(135deg,#030a03 0%,#0a1f0a 50%,#050f05 100%)',
        'cosmic-slate': 'linear-gradient(135deg,#0d0d0d 0%,#1a1a2e 50%,#0d0d0d 100%)',
        'neon-cyberpunk': 'linear-gradient(135deg,#1a0b2e 0%,#0b1f38 100%)',
        'crimson-eclipse': 'linear-gradient(135deg,#2e0808 0%,#1a0505 100%)',
        'emerald-matrix': 'linear-gradient(135deg,#051a0f 0%,#030d07 100%)',
        'corporate-calm': 'linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%)',
        'sakura-dawn': 'linear-gradient(135deg,#ffecd2 0%,#fcb69f 100%)',
        'mint-fresh': 'linear-gradient(135deg,#e0f7fa 0%,#b2ebf2 50%,#e8f5e9 100%)',
        'sunset-glow': 'linear-gradient(135deg,#f6d365 0%,#fda085 100%)',
        'glacier-breeze': 'linear-gradient(135deg,#e0c3fc 0%,#8ec5fc 100%)',
        'lavender-frost': 'linear-gradient(135deg,#f3e7e9 0%,#e3eeff 100%)',
    };
    // Restore bg theme
    const savedBg = localStorage.getItem('bgTheme');
    if (savedBg && BG_THEMES[savedBg]) {
        document.documentElement.style.setProperty('--bg-gradient', BG_THEMES[savedBg]);
        document.body && (document.body.style.backgroundImage = BG_THEMES[savedBg]);
    }
    // Restore font scale
    const savedScale = parseFloat(localStorage.getItem('fontScale') || '1.0');
    if (savedScale !== 1.0) {
        document.documentElement.style.fontSize = (savedScale * 16) + 'px';
    }
})();

function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update toggle button icon
    const toggleBtn = document.getElementById('darkModeToggle');
    if (toggleBtn) {
        toggleBtn.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
    }
}

// ========================================
// LOADING OVERLAY
// ========================================

function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');

    if (overlay) {
        if (loadingText) loadingText.textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ========================================
// TOAST NOTIFICATIONS
// ========================================

function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toastContainer.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function getToastIcon(type) {
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || icons.info;
}

// ========================================
// FORM VALIDATION HELPERS
// ========================================

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
            showFieldError(input, 'This field is required');
        } else {
            input.classList.remove('is-invalid');
            hideFieldError(input);
        }
    });

    return isValid;
}

function showFieldError(input, message) {
    let errorDiv = input.nextElementSibling;
    if (!errorDiv || !errorDiv.classList.contains('field-error')) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    errorDiv.textContent = message;
}

function hideFieldError(input) {
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('field-error')) {
        errorDiv.remove();
    }
}

// ========================================
// SMOOTH SCROLL
// ========================================

function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ========================================
// COPY TO CLIPBOARD
// ========================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success', 2000);
    }).catch(() => {
        showToast('Failed to copy', 'error', 2000);
    });
}

// ========================================
// DEBOUNCE UTILITY
// ========================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========================================
// INITIALIZE ON DOM READY
// ========================================

document.addEventListener('DOMContentLoaded', function () {
    // Add dark mode toggle button if it doesn't exist
    const nav = document.querySelector('.navbar');
    if (nav && !document.getElementById('darkModeToggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'darkModeToggle';
        toggleBtn.className = 'btn-dark-mode';
        toggleBtn.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
        toggleBtn.onclick = toggleDarkMode;
        toggleBtn.setAttribute('aria-label', 'Toggle dark mode');
        nav.appendChild(toggleBtn);
    }

    // Add loading overlay if it doesn't exist
    if (!document.getElementById('loadingOverlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <p id="loadingText">Loading...</p>
        `;
        document.body.appendChild(overlay);
    }

    // Add toast container if it doesn't exist
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Add smooth scroll to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            smoothScrollTo(targetId);
        });
    });

    // Auto-hide Django messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        });
    }, 5000);
});

// ========================================
// FORM SUBMISSION WITH LOADING
// ========================================

document.addEventListener('submit', function (e) {
    const form = e.target;
    if (form.classList.contains('ajax-form')) {
        e.preventDefault();
        showLoading('Submitting...');
        // Handle AJAX submission here
    } else if (form.classList.contains('validate-form')) {
        if (!validateForm(form.id)) {
            e.preventDefault();
            showToast('Please fill in all required fields', 'error');
        } else {
            showLoading('Processing...');
        }
    }
});

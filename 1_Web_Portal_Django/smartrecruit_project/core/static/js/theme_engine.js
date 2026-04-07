/**
 * Theme Engine — SmartRecruit
 * Developer: Rajesh Lalwani
 * Bridges the #theme-toggle UI button to the Thunder dual-theme system.
 * Works with data-theme="midnight" | "clean" on <html>.
 */

(function () {
    'use strict';

    var STORAGE_KEY = 'smartrecruit-theme';

    function getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'midnight';
    }

    function applyTheme(theme) {
        var root   = document.documentElement;
        var btn    = document.getElementById('theme-toggle');
        var state  = btn && btn.querySelector('.theme-toggle__state');
        var ariaLabel;

        root.setAttribute('data-theme', theme);
        // Keep Bootstrap in sync — fixes all BS components site-wide
        root.setAttribute('data-bs-theme', theme === 'clean' ? 'light' : 'dark');

        try { window.localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}

        // Update meta theme-color
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'clean' ? '#f0f2f5' : '#0a0b10');

        // Update toggle button state
        if (btn) {
            var isLight = (theme === 'clean');
            btn.setAttribute('aria-pressed', String(isLight));
            ariaLabel = isLight ? 'Switch to Midnight Dark mode' : 'Switch to Pristine Light mode';
            btn.setAttribute('aria-label', ariaLabel);
            btn.classList.toggle('is-light', isLight);
        }

        if (state) {
            state.textContent = (theme === 'clean') ? 'Pristine Light' : 'Midnight Dark';
        }

        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('thunder:themechange', { detail: { theme: theme } }));
    }

    function toggleTheme() {
        var next = getCurrentTheme() === 'midnight' ? 'clean' : 'midnight';
        applyTheme(next);
    }

    // Wire the toggle button on DOM ready
    document.addEventListener('DOMContentLoaded', function () {
        // Re-apply persisted theme state so button reflects reality
        var saved;
        try { saved = window.localStorage.getItem(STORAGE_KEY); } catch (e) {}
        if (!saved || (saved !== 'midnight' && saved !== 'clean')) {
            saved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'clean' : 'midnight';
        }
        applyTheme(saved);

        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', toggleTheme);
        }

        // Eye-protection toggle
        var eyeBtn = document.getElementById('eye-protection-toggle');
        if (eyeBtn) {
            var EYEKEY = 'smartrecruit-eye-protection';
            var eyeState;
            try { eyeState = window.localStorage.getItem(EYEKEY); } catch (e) {}

            if (eyeState === 'on') {
                document.documentElement.setAttribute('data-eye-protection', 'on');
            }

            eyeBtn.addEventListener('click', function () {
                var cur;
                try { cur = window.localStorage.getItem(EYEKEY); } catch (e) {}
                var next = (cur === 'on') ? 'off' : 'on';
                try { window.localStorage.setItem(EYEKEY, next); } catch (e) {}
                document.documentElement.setAttribute('data-eye-protection', next);
            });
        }
    });

    // Expose on window so preloader.js and other modules can call it
    window.Thunder = window.Thunder || {};
    window.Thunder.applyTheme  = applyTheme;
    window.Thunder.toggleTheme = toggleTheme;
    window.thunderToggleTheme  = toggleTheme; // legacy alias

}());

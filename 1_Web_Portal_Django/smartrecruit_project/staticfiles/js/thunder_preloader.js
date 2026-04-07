/**
 * Thunder Preloader — SmartRecruit
 * Developer: Rajesh Lalwani
 * Drives the SVG lightning bolt strike on every page transition.
 * Syncs with the dual-theme (midnight / clean) system.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'smartrecruit-theme';
    const PRELOADER_EL_ID = 'thunder-preloader';
    const PROGRESS_EL_ID  = 'thunder-progress-bar';
    const VALUE_EL_ID     = 'thunder-progress-value';

    /* ── 1. Detect & apply saved theme immediately (before first paint) ── */
    var root = document.documentElement;
    var savedTheme = 'midnight';
    try {
        savedTheme = window.localStorage.getItem(STORAGE_KEY) || 'midnight';
    } catch (e) {}

    if (savedTheme !== 'midnight' && savedTheme !== 'clean') {
        savedTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'clean' : 'midnight';
    }
    root.setAttribute('data-theme', savedTheme);

    /* ── 2. Theme toggle helper (called by the toggle button in base.html) ── */
    window.thunderToggleTheme = function () {
        var current = root.getAttribute('data-theme') || 'midnight';
        var next    = current === 'midnight' ? 'clean' : 'midnight';
        root.setAttribute('data-theme', next);
        try { window.localStorage.setItem(STORAGE_KEY, next); } catch (e) {}

        // Update the meta theme-color tag
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', next === 'clean' ? '#f0f2f5' : '#0a0b10');

        // Emit a custom event so other UI components can react
        document.dispatchEvent(new CustomEvent('thunder:themechange', { detail: { theme: next } }));
    };

    /* ── 3. Animate the progress bar during preloader display ── */
    function animateProgressBar(bar, valueEl) {
        if (!bar) return;
        var pct = 0;
        var statusMessages = [
            'Charging recruiter telemetry…',
            'Warming AI engines…',
            'Bootstrapping neural nodes…',
            'Ready — Strike!'
        ];
        var statusEl = document.getElementById('preloader-status');

        var interval = setInterval(function () {
            pct += Math.random() * 18 + 4;
            if (pct >= 100) { pct = 100; clearInterval(interval); }

            bar.style.width = pct.toFixed(1) + '%';
            if (valueEl) valueEl.textContent = Math.round(pct) + '%';

            // Cycle status messages
            if (statusEl) {
                var msgIdx = Math.min(Math.floor(pct / 26), statusMessages.length - 1);
                statusEl.textContent = statusMessages[msgIdx];
            }
        }, 90);
    }

    /* ── 4. Hide the preloader with a bolt-strike fade-out ── */
    function hidePreloader() {
        var preloader = document.getElementById(PRELOADER_EL_ID);
        if (!preloader) return;

        var bar     = document.getElementById(PROGRESS_EL_ID);
        var valEl   = document.getElementById(VALUE_EL_ID);

        // Force bar to 100% before hiding
        if (bar)   { bar.style.width = '100%'; bar.style.transition = 'width 0.2s ease'; }
        if (valEl) valEl.textContent = '100%';

        setTimeout(function () {
            preloader.classList.add('is-hidden');

            // Use GSAP if available for a polished exit
            if (typeof gsap !== 'undefined') {
                gsap.to(preloader, {
                    opacity: 0,
                    scale:   0.98,
                    duration: 0.5,
                    ease:    'power2.in',
                    onComplete: function () {
                        preloader.style.display = 'none';
                        root.classList.remove('preloader-active');
                    }
                });
            } else {
                preloader.style.opacity = '0';
                preloader.style.transition = 'opacity 0.45s ease';
                setTimeout(function () {
                    preloader.style.display = 'none';
                    root.classList.remove('preloader-active');
                }, 460);
            }
        }, 220);
    }

    /* ── 5. Show the preloader on internal navigations ── */
    function showPreloader() {
        var preloader = document.getElementById(PRELOADER_EL_ID);
        if (!preloader) return;

        preloader.style.display  = '';
        preloader.style.opacity  = '1';
        preloader.classList.remove('is-hidden');
        root.classList.add('preloader-active');

        var bar   = document.getElementById(PROGRESS_EL_ID);
        var valEl = document.getElementById(VALUE_EL_ID);
        if (bar) { bar.style.width = '0%'; bar.style.transition = 'none'; }

        animateProgressBar(bar, valEl);

        // GSAP bolt-strike entrance
        if (typeof gsap !== 'undefined') {
            var bolt = preloader.querySelector('.thunder-preloader__bolt');
            if (bolt) {
                gsap.fromTo(bolt,
                    { scaleY: 0, opacity: 0, transformOrigin: 'top center' },
                    { scaleY: 1, opacity: 1, duration: 0.55, ease: 'elastic.out(1, 0.5)' }
                );
            }
        }
    }

    /* ── 6. Wire up events ── */
    window.addEventListener('load', function () {
        // Run progress bar animation while page is loading
        var bar   = document.getElementById(PROGRESS_EL_ID);
        var valEl = document.getElementById(VALUE_EL_ID);
        animateProgressBar(bar, valEl);

        // Hide after a minimal strike delay
        setTimeout(hidePreloader, 1100);
        // Fallback safety: always hide within 3.5 s regardless
        setTimeout(function () {
            var el = document.getElementById(PRELOADER_EL_ID);
            if (el && el.style.display !== 'none') hidePreloader();
        }, 3500);
    });

    // Show preloader when navigating away
    window.addEventListener('beforeunload', function () {
        showPreloader();
    });

    // Also intercept internal link clicks for smoother transitions
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('a[href]').forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript') ||
                href.startsWith('mailto') || href.startsWith('tel') ||
                link.getAttribute('target') || link.getAttribute('data-bs-toggle')) {
                return;
            }
            link.addEventListener('click', function (e) {
                if (e.ctrlKey || e.metaKey || e.shiftKey) return;
                showPreloader();
            });
        });
    });

    /* ── 7. Expose public API ── */
    window.Thunder = window.Thunder || {};
    window.Thunder.showPreloader = showPreloader;
    window.Thunder.hidePreloader = hidePreloader;
    window.Thunder.toggleTheme  = window.thunderToggleTheme;

}());

/**
 * proctoring.js — SmartRecruit Elite Proctoring Suite
 * =====================================================
 * Developer: Rajesh Lalwani
 *
 * Defines the ProctoringSystem class used in take_assessment.html.
 * Responsibilities:
 *   1. Webcam initialization and stream management
 *   2. visibilitychange + window.blur tab-switch detection
 *   3. Thunder Toast warnings via SweetAlert2
 *   4. Violation logging via AJAX (logUrl)
 *   5. Periodic heartbeat pings (heartbeatUrl)
 *   6. Auto-submit on exceeded violation limit
 *   7. Context-menu / copy-paste shield reactivation safety
 */

(function (window) {
    'use strict';

    /**
     * @param {Object} opts Configuration options
     * @param {number}  opts.maxWarnings      Max tab-switch violations before auto-submit (default: 3)
     * @param {string}  opts.applicationId    Django Application PK (string)
     * @param {string}  opts.logUrl           URL for POST violation logs
     * @param {string}  opts.heartbeatUrl     URL for periodic heartbeat pings
     * @param {number}  opts.heartbeatMs      Interval in ms between heartbeats (default: 30000)
     */
    function ProctoringSystem(opts) {
        opts = opts || {};
        this.maxWarnings    = opts.maxWarnings   || 3;
        this.applicationId  = opts.applicationId || '';
        this.logUrl         = opts.logUrl         || '';
        this.heartbeatUrl   = opts.heartbeatUrl   || '';
        this.heartbeatMs    = opts.heartbeatMs    || 30000;

        // Internal state
        this._violations    = 0;
        this._heartbeatTmr  = null;
        this._stream        = null;
        this._started       = false;

        // Bind methods
        this._onVisibilityChange = this._onVisibilityChange.bind(this);
        this._onWindowBlur       = this._onWindowBlur.bind(this);

        this._init();
    }

    // ── Private: Initialization ──────────────────────────────────────────────

    ProctoringSystem.prototype._init = function () {
        this._initWebcam();
        this._bindEvents();
        this._startHeartbeat();
    };

    ProctoringSystem.prototype._initWebcam = function () {
        var self       = this;
        var videoEl    = document.getElementById('webcam');
        var statusEl   = document.getElementById('status-indicator');

        if (!videoEl) return;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            if (statusEl) {
                statusEl.textContent  = 'Camera N/A';
                statusEl.className    = 'badge bg-secondary flex-grow-1';
            }
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function (stream) {
                self._stream   = stream;
                videoEl.srcObject = stream;

                if (statusEl) {
                    statusEl.textContent = '⚡ Proctoring On';
                    statusEl.className   = 'badge bg-success text-dark flex-grow-1';
                }

                self._started = true;
                console.log('[Proctor] Webcam stream initialized.');
            })
            .catch(function (err) {
                console.warn('[Proctor] Webcam permission denied or unavailable:', err);
                if (statusEl) {
                    statusEl.textContent = '⚠ Camera Off';
                    statusEl.className   = 'badge bg-warning text-dark flex-grow-1';
                }
            });
    };

    ProctoringSystem.prototype._bindEvents = function () {
        document.addEventListener('visibilitychange', this._onVisibilityChange);
        window.addEventListener('blur', this._onWindowBlur);
    };

    // ── Private: Tab-switch / Visibility handlers ─────────────────────────────

    ProctoringSystem.prototype._onVisibilityChange = function () {
        if (document.visibilityState === 'hidden') {
            this._handleTabSwitch('Tab Hidden (visibilitychange)');
        }
    };

    ProctoringSystem.prototype._onWindowBlur = function () {
        // The template already handles window.blur for Swal — but we still log here
        // to ensure the violation counter is server-side logged even if Swal is blocked.
        var overlayEl = document.getElementById('fullscreen-overlay');
        var hiddenStyle = overlayEl && (overlayEl.style.display === 'none' || overlayEl.style.display === '');
        if (!hiddenStyle) return; // test hasn't started yet — ignore

        this.logViolation('Window Blur / Tab Switch');
    };

    ProctoringSystem.prototype._handleTabSwitch = function (reason) {
        // Update the hidden form field counter
        var tcField = document.getElementById('tab_switch_count');
        if (tcField) {
            var cur = parseInt(tcField.value || '0', 10);
            tcField.value = cur + 1;
        }

        this._violations++;
        this.logViolation(reason || 'Tab Switch');

        if (this._violations >= this.maxWarnings) {
            this._triggerAutoSubmit();
        } else {
            this._showThunderToast(this._violations, this.maxWarnings);
        }
    };

    // ── Private: Thunder Toast Warning ───────────────────────────────────────

    ProctoringSystem.prototype._showThunderToast = function (count, max) {
        if (typeof Swal === 'undefined') {
            console.warn('[Proctor] SweetAlert2 not loaded — using native alert fallback.');
            alert('⚠ Thunder Warning: Tab switching detected! ' + count + '/' + max + ' violations used.');
            return;
        }

        Swal.fire({
            icon: 'warning',
            title: '⚡ Thunder System Warning!',
            html: [
                '<p style="color:#fff; margin-bottom:8px;">Tab switching detected by the Proctoring Suite.</p>',
                '<p style="color:#ff4646; font-weight:800; font-size:1.1rem; margin-bottom:4px;">',
                count + ' / ' + max + ' violations used.',
                '</p>',
                '<small style="color:rgba(255,255,255,0.45);">This incident has been logged and reported.</small>'
            ].join(''),
            background:         'rgba(10, 11, 16, 0.97)',
            color:              '#ffffff',
            confirmButtonColor: '#00f2ff',
            confirmButtonText:  'Return to Test ⚡',
            timer:              7000,
            timerProgressBar:   true,
            customClass: {
                popup: 'thunder-swal-popup'
            }
        });
    };

    ProctoringSystem.prototype._triggerAutoSubmit = function () {
        this.logViolation('Max Violations — Auto Submit');

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon:               'error',
                title:              '🚨 Violation Limit Reached!',
                text:               'Maximum tab switches exceeded. Your assessment is being auto-submitted.',
                background:         'rgba(10,11,16,0.97)',
                color:              '#fff',
                timer:              4000,
                timerProgressBar:   true,
                showConfirmButton:  false
            }).then(function () {
                _doSubmit();
            });
        } else {
            _doSubmit();
        }

        function _doSubmit() {
            var form = document.getElementById('assessmentForm');
            if (form) {
                var fd = document.getElementById('cheating_detected_field');
                if (!fd) {
                    fd = document.createElement('input');
                    fd.type  = 'hidden';
                    fd.name  = 'cheating_detected';
                    fd.id    = 'cheating_detected_field';
                    form.appendChild(fd);
                }
                fd.value = 'true';
                form.submit();
            }
        }
    };

    // ── Public: Manual violation logger ──────────────────────────────────────

    /**
     * Log a violation to the server. Called externally from the template.
     * @param {string} reason Human-readable violation description
     */
    ProctoringSystem.prototype.logViolation = function (reason) {
        if (!this.logUrl) return;

        var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        var csrf      = csrfInput ? csrfInput.value : '';

        fetch(this.logUrl, {
            method:  'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  csrf
            },
            body: JSON.stringify({
                application_id: this.applicationId,
                reason:         reason || 'Unknown Violation',
                violations:     this._violations,
                timestamp:      new Date().toISOString()
            }),
            keepalive: true
        }).catch(function (e) {
            console.warn('[Proctor] Violation log failed (non-critical):', e);
        });
    };

    // ── Private: Heartbeat ────────────────────────────────────────────────────

    ProctoringSystem.prototype._startHeartbeat = function () {
        if (!this.heartbeatUrl) return;
        var self = this;

        this._heartbeatTmr = setInterval(function () {
            var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            var csrf      = csrfInput ? csrfInput.value : '';

            fetch(self.heartbeatUrl, {
                method:  'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken':  csrf
                },
                body: JSON.stringify({
                    application_id: self.applicationId,
                    heartbeat:      true,
                    violations:     self._violations,
                    timestamp:      new Date().toISOString()
                }),
                keepalive: true
            }).catch(function () {
                // Heartbeat failures are silent — test should never break
            });
        }, self.heartbeatMs);
    };

    ProctoringSystem.prototype.destroy = function () {
        clearInterval(this._heartbeatTmr);
        document.removeEventListener('visibilitychange', this._onVisibilityChange);
        window.removeEventListener('blur', this._onWindowBlur);

        if (this._stream) {
            this._stream.getTracks().forEach(function (t) { t.stop(); });
            this._stream = null;
        }
    };

    // ── Expose globally ───────────────────────────────────────────────────────
    window.ProctoringSystem = ProctoringSystem;

}(window));

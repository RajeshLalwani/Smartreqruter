/**
 * SmartRecruit Proctoring System
 * Monitors tab switching, window blur, and fullscreen status.
 */

class ProctoringSystem {
    constructor(config) {
        this.config = {
            maxWarnings: 3,
            ...config
        };
        this.warnings = 0;
        this.isTerminated = false;

        this.init();
    }

    init() {
        console.log("Proctoring System Initialized");

        // 1. Tab Switching / Visibility Change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handleViolation("Tab Switch Detected!");
            }
        });

        // 2. Window Blur (Alt+Tab or clicking outside)
        window.addEventListener('blur', () => {
            this.handleViolation("Focus Lost! Please stay on this window.");
        });

        // 3. Prevent Copy/Paste
        document.addEventListener('copy', (e) => e.preventDefault());
        document.addEventListener('paste', (e) => e.preventDefault());
        document.addEventListener('contextmenu', (e) => e.preventDefault());

        // 4. Fullscreen Enforcement (Optional - triggers on first interaction)
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && !this.isTerminated) {
                this.handleViolation("Fullscreen Exit Detected");
            }
        });
    }

    handleViolation(message) {
        if (this.isTerminated) return;

        this.warnings++;

        // UI Warning
        alert(`WARNING (${this.warnings}/${this.config.maxWarnings}): ${message}\nDo not switch tabs or windows during the assessment.`);

        // Log violation (in real app, send AJAX to server)
        console.warn(`Violation: ${message} - Count: ${this.warnings}`);

        if (this.warnings >= this.config.maxWarnings) {
            this.terminateTest("Maximum Violations Reached");
        }
    }

    terminateTest(reason) {
        this.isTerminated = true;
        alert("MAXIMUM VIOLATIONS REACHED. Your test is being submitted automatically.");

        // Find and submit the form
        const form = document.querySelector('form');
        if (form) {
            // Append a hidden field to indicate forced submission
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'cheating_detected';
            input.value = 'true';
            form.appendChild(input);

            const reasonInput = document.createElement('input');
            reasonInput.type = 'hidden';
            reasonInput.name = 'violation_reason';
            reasonInput.value = reason;
            form.appendChild(reasonInput);

            form.submit();
        } else {
            console.error("No form found to submit!");
            window.location.href = '/dashboard/';
        }
    }
}

// Global instance for inline script access if needed
window.ProctoringSystem = ProctoringSystem;

/**
 * SmartRecruit Proctoring System
 * Monitors tab switching, window blur, and fullscreen status.
 */
class ProctoringSystem {
    constructor(config) {
        this.config = {
            maxWarnings: 3,
            screenshotInterval: 120000, // 2 minutes
            ...config
        };
        this.warnings = 0;
        this.isTerminated = false;
        if (!this.config.logUrl || !this.config.applicationId) {
        }
        this.init();
    }
    init() {
        // 1. Tab Switching / Visibility Change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handleViolation("Tab Switch Detected!");
            }
        });
        // 2. Window Blur (Alt+Tab or clicking outside)
        window.addEventListener('blur', () => {
            // Optional: Debounce this if it triggers too easily
            this.handleViolation("Focus Lost! Please stay on this window.");
        });
        // 3. Prevent Copy/Paste
        document.addEventListener('copy', (e) => e.preventDefault());
        document.addEventListener('paste', (e) => e.preventDefault());
        document.addEventListener('contextmenu', (e) => e.preventDefault());
        // 4. Initialize Camera & Mic
        this.initCamera();
        // 5. Periodic Screenshots
        if (this.config.logUrl) {
            setInterval(() => this.captureScreenshot('SCREENSHOT', 'Periodic Check'), this.config.screenshotInterval);
        }
    }
    async initCamera() {
        const videoElement = document.getElementById('webcam');
        const statusIndicator = document.getElementById('status-indicator');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            if (videoElement) {
                videoElement.srcObject = stream;
            }
            if (statusIndicator) {
                statusIndicator.textContent = "Monitoring Active";
                statusIndicator.className = "badge bg-success";
            }
            // Load AI Model
            this.loadAIModel(videoElement);
            // Periodically check if tracks are active
            setInterval(() => {
                stream.getTracks().forEach(track => {
                    if (track.readyState !== 'live') {
                        this.handleViolation("Camera/Microphone disabled!");
                    }
                });
            }, 5000);
        } catch (err) {
            if (statusIndicator) {
                statusIndicator.textContent = "Access Denied";
                statusIndicator.className = "badge bg-danger";
            }
            alert("CRITICAL: Camera and Microphone access is REQUIRED for this assessment.\n\nPlease allow permissions and refresh the page.");
            // Disable form submission or redirect
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;
        }
    }
    async loadAIModel(videoElement) {
        try {
            const statusIndicator = document.getElementById('status-indicator');
            if (statusIndicator) statusIndicator.textContent = "Loading AI Models...";
            this.cocoModel = await cocoSsd.load();
            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
            await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
            if (statusIndicator) {
                statusIndicator.textContent = "AI Active & Proctoring";
                statusIndicator.className = "badge bg-success";
            }
            // Start Detection Loop
            setInterval(() => {
                if (!this.isTerminated && videoElement && videoElement.readyState === 4) {
                    this.detectObjects(videoElement);
                    this.detectFaces(videoElement);
                }
            }, 3000);
            // Start SecureSight Vision Heartbeat (Phase 5 add-on)
            if (this.config.heartbeatUrl) {
                this.startVisionHeartbeat();
            }
        } catch (err) {
            const statusIndicator = document.getElementById('status-indicator');
            if (statusIndicator) {
                statusIndicator.textContent = "AI Model Failed";
                statusIndicator.className = "badge bg-danger";
            }
        }
    }
    startVisionHeartbeat() {
        this.lastFacePosition = null;
        this.poseStability = 100;
        setInterval(async () => {
            if (this.isTerminated) return;
            const video = document.getElementById('webcam');
            if (!video || video.readyState !== 4) return;
            try {
                const faces = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions());
                const faceCount = faces.length;
                // Calculate pose stability based on movement of the first face found
                if (faceCount > 0) {
                    const currentPos = faces[0].box;
                    if (this.lastFacePosition) {
                        const dx = Math.abs(currentPos.x - this.lastFacePosition.x);
                        const dy = Math.abs(currentPos.y - this.lastFacePosition.y);
                        const movement = dx + dy;
                        // Heuristic: If movement > 50px, stability drops
                        this.poseStability = Math.max(0, Math.min(100, 100 - (movement * 0.5)));
                    }
                    this.lastFacePosition = currentPos;
                } else {
                    this.poseStability = 0;
                }
                this.sendHeartbeat(faceCount, this.poseStability);
            } catch (e) {
            }
        }, 10000); // Every 10 seconds
    }
    async sendHeartbeat(faceCount, stability) {
        try {
            const response = await fetch(this.config.heartbeatUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Assuming CSRF token is available on the window or as a cookie
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    face_count: faceCount,
                    pose_stability: stability,
                    impersonation_risk: faceCount > 1 ? 95 : (faceCount === 0 ? 50 : 5)
                })
            });
            const data = await response.json();
            if (data.status === 'error') {
                this.triggerSuspicion(data.message);
            }
        } catch (err) {
        }
    }
    getCsrfToken() {
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
    async detectObjects(videoElement) {
        if (!this.cocoModel) return;
        try {
            const predictions = await this.cocoModel.detect(videoElement);
            for (let i = 0; i < predictions.length; i++) {
                if (predictions[i].class === 'cell phone' || predictions[i].class === 'remote' || predictions[i].class === 'laptop' && predictions[i].score > 0.6) {
                    if (predictions[i].class !== 'laptop') { // Typically you wouldn't flag laptop if they are mostly looking at webcam, but keeping it flexible. Let's just flag phones.
                        this.handleViolation("Unauthorized device (" + predictions[i].class + ") detected!");
                    }
                }
            }
        } catch (e) {
        }
    }
    async detectFaces(videoElement) {
        try {
            const faces = await faceapi.detectAllFaces(videoElement, new faceapi.TinyFaceDetectorOptions());
            if (faces.length === 0) {
                this.triggerSuspicion("No face detected! Please stay in front of the camera.");
            } else if (faces.length > 1) {
                this.handleViolation("Multiple faces detected! You must be alone.");
            }
        } catch (e) {
        }
    }
    triggerSuspicion(reason) {
        if (this.isTerminated) return;
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) {
            statusIndicator.textContent = 'Suspicion: ' + reason;
            statusIndicator.className = 'badge bg-warning text-dark';
            setTimeout(() => {
                if (!this.isTerminated) {
                    statusIndicator.textContent = "AI Active & Proctoring";
                    statusIndicator.className = 'badge bg-success';
                }
            }, 4000);
        }
        // Capture evidence of suspicion without immediately counting as a full violation
        this.captureScreenshot('SUSPICION', reason);
    }
    handleViolation(message) {
        if (this.isTerminated) return;
        this.warnings++;
        // Capture evidence
        this.captureScreenshot('VIOLATION', message);
        // UI Warning
        alert(`WARNING (${this.warnings}/${this.config.maxWarnings}): ${message}\nDo not switch tabs, use phones, or have others in the room.`);
        // 360 Scan Prompt Logic
        if (this.warnings === 2) {
            alert("⚠️ SUSPICIOUS ACTIVITY DETECTED ⚠️\n\nPlease rotate your laptop 360 degrees immediately to show your surroundings.\n\nFailure to do so may lead to disqualification.");
            this.captureScreenshot('SUSPICION', '360 Scan Requested');
        }
        // Log violation (in real app, send AJAX to server)
        if (this.warnings >= this.config.maxWarnings) {
            this.terminateTest();
        }
    }
    captureScreenshot(type, details) {
        if (!this.config.logUrl) return;
        const video = document.getElementById('webcam');
        if (!video || !video.srcObject) return;
        try {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            this.sendLog(type, details, dataUrl);
        } catch (e) {
        }
    }
    sendLog(type, details, image) {
        const formData = new FormData();
        formData.append('log_type', type);
        formData.append('details', details);
        if (image) formData.append('image', image);
        fetch(this.config.logUrl, {
            method: 'POST',
            body: formData,
            headers: {
                // CSRF handled by cookies usually, but we might need to add it if checking headers
                // 'X-CSRFToken': getCookie('csrftoken') 
            }
        }).catch(err => );
    }
    terminateTest() {
        this.isTerminated = true;
        // Capture final evidence
        this.captureScreenshot('VIOLATION', 'Test Terminated');
        alert("MAXIMUM VIOLATIONS REACHED. Your test is being submitted automatically and you will be DISQUALIFIED.");
        // Find and submit the form
        const form = document.querySelector('form');
        if (form) {
            // Append a hidden field to indicate cheating/forced submission
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'cheating_detected';
            input.value = 'true';
            form.appendChild(input);
            form.submit();
        } else {
            window.location.href = '/dashboard/';
        }
    }
}
// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    const proctor = new ProctoringSystem({ maxWarnings: 3 });
});

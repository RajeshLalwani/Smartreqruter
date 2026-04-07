class ProctorReplay {
    constructor(containerId, interviewId) {
        this.container = document.getElementById(containerId);
        this.interviewId = interviewId;
        this.frames = [];
        this.currentIndex = 0;
        this.isPlaying = false;
        this.playbackInterval = null;
        this.init();
    }

    async init() {
        this.container.innerHTML = `<div class="text-center p-5"><div class="spinner-border text-cyan"></div><p class="mt-2">Connecting to Neural Archive...</p></div>`;
        try {
            const resp = await fetch(`/api/proctor/session/${this.interviewId}/frames/`);
            const data = await resp.json();
            if (data.ok) {
                this.frames = data.frames;
                this.render();
            }
        } catch (e) {
            this.container.innerHTML = `<div class="alert alert-danger">Failed to sync with Evidence Matrix.</div>`;
        }
    }

    render() {
        if (this.frames.length === 0) {
            this.container.innerHTML = `<div class="alert alert-info">No proctoring frames found for this session.</div>`;
            return;
        }

        this.container.innerHTML = `
            <div class="replay-player smart-glass p-3 rounded-4" style="border: 1px solid rgba(0, 210, 255, 0.3);">
                <!-- Screen Area -->
                <div class="screen-area position-relative bg-black rounded-3 overflow-hidden" style="aspect-ratio: 16/9; box-shadow: 0 0 20px rgba(0, 210, 255, 0.1);">
                    <img id="replay-frame" src="${this.frames[0].frame}" class="w-100 h-100 object-fit-contain">
                    <!-- Overlay Info -->
                    <div class="position-absolute top-0 start-0 p-3 w-100 d-flex justify-content-between" style="background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);">
                        <span class="badge bg-dark border border-cyan text-cyan">REC ● LIVE REPLAY</span>
                        <span id="replay-timestamp" class="text-white-50 small">${this.frames[0].timestamp}</span>
                    </div>
                    <!-- Violation HUD -->
                    <div id="violation-hud" class="position-absolute bottom-0 start-0 p-3 w-100" style="background: linear-gradient(to top, rgba(255,51,102,0.4), transparent); opacity: 0;">
                        <span class="badge bg-danger text-uppercase" id="violation-text">INTEGRITY BREACH</span>
                    </div>
                </div>

                <!-- Controls -->
                <div class="controls-area mt-3">
                    <div class="d-flex align-items-center gap-3">
                        <button id="play-pause-btn" class="btn btn-outline-cyan rounded-circle p-2" style="width: 45px; height: 45px;">
                            <i class="bi bi-play-fill fs-4"></i>
                        </button>
                        
                        <div class="flex-grow-1 position-relative">
                            <input type="range" id="seek-bar" class="form-range custom-range" min="0" max="${this.frames.length - 1}" value="0">
                            <!-- Violation Markers -->
                            <div id="violation-markers" class="position-absolute top-50 start-0 w-100 translate-middle-y" style="pointer-events: none; height: 10px;">
                                ${this.renderMarkers()}
                            </div>
                        </div>

                        <div class="text-white-50 small" style="min-width: 60px;">
                            <span id="current-idx">1</span> / ${this.frames.length}
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div class="d-flex justify-content-between mt-3">
                    <button class="btn btn-sm btn-outline-secondary" onclick="window.location.reload()">
                        <i class="bi bi-arrow-clockwise"></i> Reset
                    </button>
                    <a href="/api/proctor/session/${this.interviewId}/report/" class="btn btn-sm btn-cyan">
                        <i class="bi bi-file-earmark-pdf"></i> Download Evidence PDF
                    </a>
                </div>
            </div>
        `;

        this.attachEvents();
        this.updateFrame(0);
    }

    renderMarkers() {
        return this.frames.map((f, i) => {
            if (f.violations && f.violations.length > 0) {
                const pos = (i / (this.frames.length - 1)) * 100;
                return `<div class="violation-dot" style="left: ${pos}%" title="${f.violations.join(', ')}"></div>`;
            }
            return '';
        }).join('');
    }

    attachEvents() {
        const playBtn = this.container.querySelector('#play-pause-btn');
        const seekBar = this.container.querySelector('#seek-bar');
        const frameImg = this.container.querySelector('#replay-frame');

        playBtn.addEventListener('click', () => this.togglePlayback());
        seekBar.addEventListener('input', (e) => this.updateFrame(parseInt(e.target.value)));
    }

    togglePlayback() {
        this.isPlaying = !this.isPlaying;
        const btn = this.container.querySelector('#play-pause-btn i');
        
        if (this.isPlaying) {
            btn.className = 'bi bi-pause-fill fs-4';
            this.playbackInterval = setInterval(() => {
                if (this.currentIndex < this.frames.length - 1) {
                    this.updateFrame(this.currentIndex + 1);
                } else {
                    this.togglePlayback();
                }
            }, 500); // 2 FPS roughly
        } else {
            btn.className = 'bi bi-play-fill fs-4';
            clearInterval(this.playbackInterval);
        }
    }

    updateFrame(index) {
        this.currentIndex = index;
        const frame = this.frames[index];
        
        const frameImg = this.container.querySelector('#replay-frame');
        const tsText = this.container.querySelector('#replay-timestamp');
        const seekBar = this.container.querySelector('#seek-bar');
        const idxText = this.container.querySelector('#current-idx');
        const hud = this.container.querySelector('#violation-hud');
        const vText = this.container.querySelector('#violation-text');

        frameImg.src = frame.frame;
        tsText.innerText = frame.timestamp;
        seekBar.value = index;
        idxText.innerText = index + 1;

        if (frame.violations && frame.violations.length > 0) {
            hud.style.opacity = '1';
            vText.innerText = `BREACH: ${frame.violations.join(' | ')}`;
        } else {
            hud.style.opacity = '0';
        }
    }
}

// Global Launcher
window.openProctorReplay = (interviewId) => {
    const modal = new bootstrap.Modal(document.getElementById('replayModal'));
    modal.show();
    new ProctorReplay('replay-viewer-body', interviewId);
};

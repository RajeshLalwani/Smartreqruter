/**
 * Neural Hub (Project Zenith Phase 10)
 * Manages the global voice interaction loop.
 */

class NeuralHub {
    constructor() {
        this.btn = document.getElementById('neural-mic-btn');
        this.container = document.getElementById('neural-assistant-hub');
        this.canvas = document.getElementById('neural-waveform');
        this.ctx = this.canvas.getContext('2d');
        this.isListening = false;
        this.isSpeaking = false;
        
        this.init();
    }

    init() {
        if (!this.btn) return;
        
        this.btn.addEventListener('click', () => this.toggleVoiceLink());
        
        // Setup Waveform sizes
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Start animation loop
        this.animateWave();
    }

    resizeCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    toggleVoiceLink() {
        if (this.isListening || this.isSpeaking) {
            this.stopAll();
        } else {
            this.startListening();
        }
    }

    stopAll() {
        this.isListening = false;
        this.isSpeaking = false;
        this.btn.classList.remove('is-listening');
        this.container.classList.remove('active-comms');
        
        if (window.aiVoice) {
            window.aiVoice.synth.cancel();
        }
    }

    startListening() {
        if (!window.aiVoice) return;
        
        this.isListening = true;
        this.btn.classList.add('is-listening');
        this.container.classList.add('active-comms');
        
        window.aiVoice.listen(
            (transcript) => this.handleVoiceResult(transcript),
            () => console.log('Neural Link Established...'),
            () => {
                if (this.isListening) this.stopAll();
            }
        );
    }

    async handleVoiceResult(transcript) {
        this.isListening = false;
        this.btn.classList.remove('is-listening');
        
        // Show "thinking" state on the pulse
        this.container.classList.add('processing');
        
        try {
            const response = await fetch('/core/voice-assistant-api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ transcript: transcript })
            });
            
            const data = await response.json();
            
            if (data.response) {
                this.startSpeaking(data.response, data.voice_preference);
            } else {
                this.stopAll();
            }
        } catch (err) {
            console.error('Neural Hub API Error:', err);
            this.stopAll();
        } finally {
            this.container.classList.remove('processing');
        }
    }

    startSpeaking(text, voicePref) {
        this.isSpeaking = true;
        this.container.classList.add('active-comms');
        
        if (window.aiVoice) {
            window.aiVoice.speak(text, voicePref || 'female');
            
            // Check for end of speech
            const checkEnd = setInterval(() => {
                if (!window.aiVoice.synth.speaking) {
                    clearInterval(checkEnd);
                    this.stopAll();
                }
            }, 500);
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    animateWave() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.isListening || this.isSpeaking) {
            const time = Date.now() / 1000;
            const amplitude = this.isListening ? 15 : 25;
            const frequency = this.isListening ? 10 : 15;
            
            this.ctx.beginPath();
            this.ctx.lineWidth = 2;
            this.ctx.strokeStyle = '#00e5ff';
            
            for (let x = 0; x < this.canvas.width; x++) {
                const y = this.canvas.height / 2 + Math.sin(x / frequency + time * 5) * amplitude * Math.sin(x / 50);
                if (x === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            
            this.ctx.stroke();
            
            // Subtle glow
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = '#00e5ff';
        }
        
        requestAnimationFrame(() => this.animateWave());
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.neuralHub = new NeuralHub();
});

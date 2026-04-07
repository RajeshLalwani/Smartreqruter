/**
 * SmartRecruit AI Voice Agent
 * Handles Text-to-Speech (TTS) for AI Interviewers.
 */

class VoiceAgent {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voices = [];
        this.voiceName = localStorage.getItem('voiceName') || '';
        this.pitch = parseFloat(localStorage.getItem('voicePitch') || '1.0');
        this.rate = parseFloat(localStorage.getItem('voiceSpeed') || '1.0');

        // Load voices
        const loadVoices = () => {
            this.voices = this.synth.getVoices();
        };

        loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    updateSettings() {
        this.voiceName = localStorage.getItem('voiceName') || '';
        this.pitch = parseFloat(localStorage.getItem('voicePitch') || '1.0');
        this.rate = parseFloat(localStorage.getItem('voiceSpeed') || '1.0');
    }

    speakTest(text, voiceName, pitch, rate) {
        if (this.synth.speaking) {
            this.synth.cancel();
        }
        if (text !== '') {
            const utterThis = new SpeechSynthesisUtterance(text);
            let selectedVoice = this.voices.find(v => v.name === voiceName);
            if (selectedVoice) {
                utterThis.voice = selectedVoice;
            }
            utterThis.pitch = pitch;
            utterThis.rate = rate;
            this.synth.speak(utterThis);
        }
    }

    speak(text, gender = 'female') {
        if (this.synth.speaking) {
            this.synth.cancel(); // Cancel current speech to jump to newest
        }

        if (text !== '') {
            const utterThis = new SpeechSynthesisUtterance(text);
            let selectedVoice = null;

            if (this.voiceName) {
                // Use explicit user preference
                selectedVoice = this.voices.find(v => v.name === this.voiceName);
                if (selectedVoice) {
                    utterThis.voice = selectedVoice;
                }
                utterThis.pitch = this.pitch;
                utterThis.rate = this.rate;
            } else {
                // Fallback to Gender auto-select
                if (gender === 'female') {
                    selectedVoice = this.voices.find(v => v.name.toLowerCase().includes('google us english') || v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('female'));
                    if (!selectedVoice) selectedVoice = this.voices[0];
                    utterThis.pitch = 1.3;
                    utterThis.rate = 1.05;
                } else {
                    selectedVoice = this.voices.find(v => v.name.toLowerCase().includes('google uk english male') || v.name.toLowerCase().includes('david') || v.name.toLowerCase().includes('male'));
                    if (!selectedVoice) selectedVoice = this.voices[0];
                    utterThis.pitch = 0.9;
                    utterThis.rate = 1.0;
                }
                if (selectedVoice) utterThis.voice = selectedVoice;
            }

            utterThis.onend = function (event) {
                console.log('SpeechSynthesisUtterance.onend');
            };

            utterThis.onerror = function (event) {
                console.error('SpeechSynthesisUtterance.onerror');
            };

            this.synth.speak(utterThis);
        }
    }

    /**
     * Starts listening to user speech.
     * @param {Function} onResult - Callback with transcribed text.
     * @param {Function} onStart - Callback when listening starts.
     * @param {Function} onEnd - Callback when listening ends.
     */
    listen(onResult, onStart, onEnd) {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Speech recognition is not supported in this browser. Please use Chrome.");
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            console.log('Voice recognition activated. Try speaking into the microphone.');
            if (onStart) onStart();
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('You said: ', transcript);
            if (onResult) onResult(transcript);
        };

        recognition.onspeechend = () => {
            console.log('Speech ended.');
            recognition.stop();
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            if (onEnd) onEnd();
        };

        recognition.onend = () => {
            console.log('Voice recognition disconnected.');
            if (onEnd) onEnd();
        };

        recognition.start();
    }
}

const aiVoice = new VoiceAgent();

// Helper function to be called from HTML
function speakAI(text, gender) {
    // Small delay to ensure voices are loaded
    setTimeout(() => {
        aiVoice.speak(text, gender);
    }, 1000); // 1-second delay for smoother UX on load
}

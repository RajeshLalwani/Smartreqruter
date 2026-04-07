/**
 * SmartRecruit AI Voice Agent
 * Handles Text-to-Speech (TTS) for AI Interviewers.
 */

class VoiceAgent {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voices = [];

        // Load voices
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => {
                this.voices = this.synth.getVoices();
            };
        }
    }

    speak(text, gender = 'female') {
        if (this.synth.speaking) {
            console.error('speechSynthesis.speaking');
            return;
        }

        if (text !== '') {
            const utterThis = new SpeechSynthesisUtterance(text);

            // Select Voice based on Gender
            // Note: Voice availability depends on OS/Browser. 
            // We search for common English voices.
            let selectedVoice = null;

            if (gender === 'female') {
                // Try to find a female voice (Google US English, Microsoft Zira, etc.)
                selectedVoice = this.voices.find(v => v.name.includes('Google US English') || v.name.includes('Zira') || v.name.includes('Female'));
                if (!selectedVoice) selectedVoice = this.voices[0]; // Fallback

                utterThis.pitch = 1.3;
                utterThis.rate = 1.05;
            } else {
                // Male (Google UK English Male, Microsoft David, etc.)
                selectedVoice = this.voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('David') || v.name.includes('Male'));
                if (!selectedVoice) selectedVoice = this.voices[0]; // Fallback

                utterThis.pitch = 0.9; // Lower pitch for male
                utterThis.rate = 1.0;
            }

            utterThis.voice = selectedVoice;

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

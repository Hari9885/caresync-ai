/**
 * CareSync AI – Client-Side JavaScript
 * Handles voice synthesis, quick-fill chips, form validation, and UI interactions.
 */

// ─── Voice Synthesis ────────────────────────────────────────────────────

const synth = window.speechSynthesis;
let currentUtterance = null;
let isSpeaking = false;

/**
 * Speak the given text using Web Speech API.
 * @param {string} text - Text to speak
 * @param {string} lang - Language code (default: 'en-US')
 */
function speak(text, lang = 'en-US') {
    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 0.85; // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to find a good voice
    const voices = synth.getVoices();
    const preferredVoice = voices.find(v =>
        v.lang.startsWith(lang.split('-')[0]) && v.localService
    ) || voices.find(v =>
        v.lang.startsWith(lang.split('-')[0])
    );

    if (preferredVoice) {
        utterance.voice = preferredVoice;
    }

    currentUtterance = utterance;
    synth.speak(utterance);

    return utterance;
}

/**
 * Speak a single medicine's instructions.
 * @param {number} index - Index in the medicineData array
 */
function speakMedicine(index) {
    if (typeof medicineData === 'undefined' || !medicineData[index]) return;

    const med = medicineData[index];
    const btn = document.getElementById(`voice-btn-${index + 1}`);

    // Stop if already speaking this one
    if (isSpeaking && btn && btn.classList.contains('speaking')) {
        stopSpeech();
        return;
    }

    stopSpeech(); // Cancel any other speech

    const utterance = speak(med.voiceText);
    isSpeaking = true;

    // Visual feedback
    if (btn) {
        btn.classList.add('speaking');
        const label = btn.querySelector('.voice-label');
        if (label) label.textContent = 'Speaking...';
    }

    utterance.onend = () => {
        isSpeaking = false;
        if (btn) {
            btn.classList.remove('speaking');
            const label = btn.querySelector('.voice-label');
            if (label) label.textContent = 'Listen';
        }
    };

    utterance.onerror = () => {
        isSpeaking = false;
        if (btn) {
            btn.classList.remove('speaking');
            const label = btn.querySelector('.voice-label');
            if (label) label.textContent = 'Listen';
        }
    };
}

/**
 * Read all medicine instructions sequentially.
 */
function speakAll() {
    if (typeof medicineData === 'undefined' || medicineData.length === 0) return;

    const listenAllBtn = document.getElementById('listen-all-btn');
    const stopBtn = document.getElementById('stop-btn');

    // Show stop button, hide listen all
    if (listenAllBtn) {
        listenAllBtn.style.display = 'none';
    }
    if (stopBtn) {
        stopBtn.style.display = 'inline-flex';
    }

    isSpeaking = true;

    // Build a combined text with pauses
    let fullText = 'Here are your medicine instructions. ';
    medicineData.forEach((med, i) => {
        fullText += `Medicine ${i + 1}. ${med.voiceText} `;
        if (i < medicineData.length - 1) {
            fullText += '... Next medicine. ';
        }
    });
    fullText += '... That is all. Follow your doctor\'s advice and take your medicines on time.';

    const utterance = speak(fullText);

    // Highlight cards as they're being read
    utterance.onend = () => {
        isSpeaking = false;
        resetSpeechUI();
    };

    utterance.onerror = () => {
        isSpeaking = false;
        resetSpeechUI();
    };
}

/**
 * Stop all speech synthesis.
 */
function stopSpeech() {
    synth.cancel();
    isSpeaking = false;
    resetSpeechUI();
}

/**
 * Reset all speech-related UI elements.
 */
function resetSpeechUI() {
    // Reset listen all / stop buttons
    const listenAllBtn = document.getElementById('listen-all-btn');
    const stopBtn = document.getElementById('stop-btn');

    if (listenAllBtn) {
        listenAllBtn.style.display = 'inline-flex';
        listenAllBtn.classList.remove('speaking');
    }
    if (stopBtn) {
        stopBtn.style.display = 'none';
    }

    // Reset all individual voice buttons
    document.querySelectorAll('.voice-btn').forEach(btn => {
        btn.classList.remove('speaking');
        const label = btn.querySelector('.voice-label');
        if (label) label.textContent = 'Listen';
    });
}

// Load voices (they load asynchronously in some browsers)
if (synth) {
    synth.getVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => synth.getVoices();
    }
}


// ─── Quick-Fill Chips ───────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const chipGroup = document.getElementById('chip-group');
    const textarea = document.getElementById('prescription-input');

    if (chipGroup && textarea) {
        chipGroup.addEventListener('click', (e) => {
            const chip = e.target.closest('.chip');
            if (!chip) return;

            const text = chip.getAttribute('data-text');
            if (text) {
                // Replace escaped newlines with actual newlines
                textarea.value = text.replace(/\\n/g, '\n');
                textarea.focus();

                // Visual feedback
                chip.style.transform = 'scale(0.95)';
                chip.style.background = 'var(--primary-200)';
                setTimeout(() => {
                    chip.style.transform = '';
                    chip.style.background = '';
                }, 200);

                // Auto-grow textarea
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            }
        });
    }

    // ─── Form Submission ────────────────────────────────────────────────

    const form = document.getElementById('prescription-form');
    const submitBtn = document.getElementById('submit-btn');

    if (form && submitBtn) {
        form.addEventListener('submit', (e) => {
            const value = textarea ? textarea.value.trim() : '';
            if (!value) {
                e.preventDefault();
                textarea.focus();
                return;
            }

            // Show loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        });
    }

    // ─── Textarea Auto-Resize ───────────────────────────────────────────

    if (textarea) {
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 400) + 'px';
        });
    }

    // ─── Smooth Scroll for Section Visibility ───────────────────────────

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observe cards for entrance animation
    document.querySelectorAll('.medicine-card, .step-card, .feature-item').forEach(el => {
        observer.observe(el);
    });

    // ─── Keyboard Accessibility ─────────────────────────────────────────

    // Allow Enter key on chips
    document.querySelectorAll('.chip').forEach(chip => {
        chip.setAttribute('tabindex', '0');
        chip.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                chip.click();
            }
        });
    });

    // Allow Enter key on voice buttons
    document.querySelectorAll('.voice-btn').forEach(btn => {
        btn.setAttribute('tabindex', '0');
    });
});

// ─── Print Function (explicit for button) ───────────────────────────────

function printResults() {
    window.print();
}

// ─── Copy Guide (share as plain text) ───────────────────────────────────

function copyGuide() {
    if (typeof medicineData === 'undefined' || medicineData.length === 0) return;

    const text = 'My Medicine Guide (CareSync AI)\n\n' +
        medicineData.map((m, i) => `${i + 1}. ${m.voiceText}`).join('\n\n');

    navigator.clipboard.writeText(text).then(() => {
        const label = document.querySelector('#copy-btn .copy-label');
        if (label) {
            label.textContent = 'Copied!';
            setTimeout(() => { label.textContent = 'Copy Guide'; }, 2000);
        }
    });
}

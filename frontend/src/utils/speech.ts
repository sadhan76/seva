/**
 * Bilingual Text-to-Speech (TTS) and Speech-to-Text (STT) Utilities
 * Features:
 * - Tamil ('ta-IN') and English ('en-IN' / 'en-US') speech synthesis
 * - Play, Pause, Resume, and Stop speech controls
 * - Speech recognition with transcript preview
 * - Sanitization to ensure passwords, auth tokens, and secrets are NEVER read aloud
 */

import type { Language } from '../types';

/**
 * Strips Markdown formatting, URLs, emojis, and sensitive tokens before speaking.
 * TASK 3 & PHASE 19: "Never show or speak passwords, OTPs, tokens, or private authentication details using text-to-speech."
 */
export function cleanTextForSpeech(text: string): string {
  if (!text) return '';

  let cleaned = text
    // Remove Markdown headers, bold, italics, bullets, code fences
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[#*_~>•]/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [link text](url) -> link text
    .replace(/https?:\/\/\S+/g, ' ')
    // Remove emojis and special agricultural icons
    .replace(/[\u{1F300}-\u{1F9FF}]/gu, ' ')
    // Censor sensitive security patterns (tokens, JWT, passwords, Telegram OTPs)
    .replace(/eyJ[a-zA-Z0-9_\-.]+/g, '[security token hidden]')
    .replace(/NV-[a-zA-Z0-9_\-]+/g, '[token code hidden]')
    .replace(/password[:=]\s*\S+/gi, 'password hidden')
    .replace(/(?:otp|verification code|security code)[:=]\s*\d+/gi, '[code hidden]')
    .replace(/\b\d{6}\b/g, '[code hidden]') // Censor any 6-digit OTP codes
    .replace(/t\.me\/\S+/gi, '[telegram link hidden]')
    // Condense extra spaces and newlines
    .replace(/\s+/g, ' ')
    .trim();

  return cleaned;
}

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

export function isSpeechRecognitionSupported(): boolean {
  if (typeof window === 'undefined') return false;
  return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
}

/**
 * Finds the most suitable voice for the selected regional language.
 */
export function getBestVoice(language: Language): SpeechSynthesisVoice | null {
  if (!isSpeechSynthesisSupported()) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const targetPrefix = language.toLowerCase();

  // Try exact match or language prefix (e.g. 'ta-IN', 'hi-IN', 'te-IN')
  const matchedVoice = voices.find(
    (v) => v.lang.toLowerCase().startsWith(targetPrefix) || v.name.toLowerCase().includes(targetPrefix)
  );
  if (matchedVoice) return matchedVoice;

  // Look for Indian English voice fallback
  const indianEng = voices.find((v) => v.lang.toLowerCase() === 'en-in');
  if (indianEng) return indianEng;

  // Standard English fallback
  const engVoice = voices.find((v) => v.lang.toLowerCase().startsWith('en'));
  return engVoice || voices[0] || null;
}

export interface SpeechPlaybackController {
  speak: (
    text: string,
    language: Language,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (errorMsg: string) => void
  ) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  isSpeaking: () => boolean;
  isPaused: () => boolean;
}


export function createSpeechPlaybackController(): SpeechPlaybackController {
  let activeUtterance: SpeechSynthesisUtterance | null = null;

  return {
    speak: (text, language, onStart, onEnd, onError) => {
      if (!isSpeechSynthesisSupported()) {
        onError?.('Text-to-speech is not supported by your browser.');
        return;
      }

      window.speechSynthesis.cancel();

      const sanitizedText = cleanTextForSpeech(text);
      if (!sanitizedText) return;

      const utterance = new SpeechSynthesisUtterance(sanitizedText);
      activeUtterance = utterance;

      utterance.lang = language === 'ta' ? 'ta-IN' : 'en-IN';
      utterance.rate = language === 'ta' ? 0.95 : 1.0; // Slightly measured pace for clarity
      utterance.pitch = 1.0;

      const voice = getBestVoice(language);
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onstart = () => {
        onStart?.();
      };

      utterance.onend = () => {
        activeUtterance = null;
        onEnd?.();
      };

      utterance.onerror = (e) => {
        activeUtterance = null;
        // Ignore interrupted errors triggered by user pressing stop
        if (e.error !== 'interrupted' && e.error !== 'canceled') {
          onError?.(`Speech synthesis error: ${e.error}`);
        } else {
          onEnd?.();
        }
      };

      window.speechSynthesis.speak(utterance);
    },

    pause: () => {
      if (isSpeechSynthesisSupported() && window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
      }
    },

    resume: () => {
      if (isSpeechSynthesisSupported() && window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    },

    stop: () => {
      if (isSpeechSynthesisSupported()) {
        window.speechSynthesis.cancel();
        activeUtterance = null;
      }
    },

    isSpeaking: () => {
      return isSpeechSynthesisSupported() && (window.speechSynthesis.speaking || activeUtterance !== null);
    },

    isPaused: () => {
      return isSpeechSynthesisSupported() && window.speechSynthesis.paused;
    },
  };
}

/**
 * Speech Recognition Listener Controller.
 * TASK 4: Web speech recognition with language selection (Tamil / English).
 */
export interface SpeechRecognitionListener {
  start: () => void;
  stop: () => void;
}

export function createSpeechRecognizer(
  language: 'en' | 'ta',
  onResult: (transcription: string, isFinal: boolean) => void,
  onError: (errorText: string) => void,
  onEnd: () => void
): SpeechRecognitionListener | null {
  if (!isSpeechRecognitionSupported()) {
    return null;
  }

  const SpeechRecognitionClass =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  if (!SpeechRecognitionClass) return null;

  try {
    const recognition = new SpeechRecognitionClass();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = language === 'ta' ? 'ta-IN' : 'en-IN';

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const text = finalTranscript || interimTranscript;
      onResult(text, Boolean(finalTranscript));
    };

    recognition.onerror = (event: any) => {
      let msg = event.error || 'Speech recognition error.';
      if (event.error === 'not-allowed') {
        msg = 'Microphone permission denied. Please allow microphone access in your browser settings.';
      } else if (event.error === 'no-speech') {
        msg = 'No speech detected. Please speak into your microphone.';
      } else if (event.error === 'network') {
        msg = 'Network connection required for speech recognition service.';
      }
      onError(msg);
    };

    recognition.onend = () => {
      onEnd();
    };

    return {
      start: () => {
        try {
          recognition.start();
        } catch {
          // Already active
        }
      },
      stop: () => {
        try {
          recognition.stop();
        } catch {
          // Already stopped
        }
      },
    };
  } catch (err: any) {
    onError(err.message || 'Speech recognition initialization failed.');
    return null;
  }
}

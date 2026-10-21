/**
 * Multilingual Text-to-Speech (TTS) and Speech-to-Text (STT) Utilities
 * Supports all 22 Eighth Schedule languages of India plus English.
 * Features:
 * - Exact BCP-47 speech locale mappings via central locale registry
 * - Play, Pause, Resume, and Stop controls
 * - Honest browser/device capability detection with helpful fallback messages
 * - Sanitization to ensure passwords, auth tokens, OTPs, and secrets are NEVER read aloud
 */

import type { Language } from '../types';
import { getLocaleMetadata } from '../i18n/localeRegistry';

/**
 * Strips Markdown formatting, URLs, emojis, and sensitive security tokens before speaking.
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
    // Censor sensitive security patterns (tokens, JWT, passwords, OTPs)
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
 * Checks whether the browser has a voice for the requested regional language.
 */
export function getBestVoice(language: Language): { voice: SpeechSynthesisVoice | null; isSupported: boolean } {
  if (!isSpeechSynthesisSupported()) {
    return { voice: null, isSupported: false };
  }

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) {
    return { voice: null, isSupported: false };
  }

  const meta = getLocaleMetadata(language);
  const targetCode = language.toLowerCase();
  const targetLocale = (meta.speechSynthesisLocale || '').toLowerCase();

  // 1. Exact match on BCP-47 locale (e.g. 'hi-in', 'ta-in', 'te-in')
  let matched = voices.find((v) => v.lang.toLowerCase() === targetLocale);
  if (matched) return { voice: matched, isSupported: true };

  // 2. Prefix match (e.g. starts with 'hi-', 'ta-', 'ur-')
  matched = voices.find((v) => v.lang.toLowerCase().startsWith(`${targetCode}-`));
  if (matched) return { voice: matched, isSupported: true };

  // 3. Name match containing language name
  matched = voices.find((v) => v.name.toLowerCase().includes(meta.name.toLowerCase()));
  if (matched) return { voice: matched, isSupported: true };

  // 4. If target is English, accept standard English voice
  if (targetCode === 'en') {
    const eng = voices.find((v) => v.lang.toLowerCase().startsWith('en'));
    return { voice: eng || voices[0] || null, isSupported: Boolean(eng || voices[0]) };
  }

  // Language voice pack not installed on this browser/device
  return { voice: null, isSupported: false };
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

      const meta = getLocaleMetadata(language);
      const { voice, isSupported } = getBestVoice(language);

      // Honest feedback if browser lacks voice support for this regional language
      if (!isSupported && language !== 'en') {
        const errorMsg = `Speech audio in ${meta.name} (${meta.nativeName}) is not supported by this browser/device. Please install an Indian language voice pack in your device settings or use Chrome on Android.`;
        onError?.(errorMsg);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(sanitizedText);
      activeUtterance = utterance;

      utterance.lang = meta.speechSynthesisLocale || 'en-IN';
      utterance.rate = language === 'ta' || language === 'ur' ? 0.95 : 1.0;
      utterance.pitch = 1.0;

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

export interface SpeechRecognitionListener {
  start: () => void;
  stop: () => void;
}

export function createSpeechRecognizer(
  language: Language,
  onResult: (transcription: string, isFinal: boolean) => void,
  onError: (errorText: string) => void,
  onEnd: () => void
): SpeechRecognitionListener | null {
  if (!isSpeechRecognitionSupported()) {
    onError('Speech recognition is not supported by this browser.');
    return null;
  }

  const SpeechRecognitionClass =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  if (!SpeechRecognitionClass) {
    onError('Speech recognition is not supported by this browser.');
    return null;
  }

  const meta = getLocaleMetadata(language);

  try {
    const recognition = new SpeechRecognitionClass();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = meta.speechRecognitionLocale || 'en-IN';

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
      } else if (event.error === 'language-not-supported') {
        msg = `Voice recognition in ${meta.name} (${meta.nativeName}) is not supported by this browser/device. Please type your query or try Chrome.`;
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
    onError(err.message || `Speech recognition failed for ${meta.name}.`);
    return null;
  }
}

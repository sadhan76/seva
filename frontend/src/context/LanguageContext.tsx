import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Language } from '../types';
import {
  type TranslationSchema,
  getTranslationsForLanguage,
  CENTRAL_LOCALE_REGISTRY,
  getLocaleMetadata,
} from '../i18n/translations';
import type { LocaleMetadata, TextDirection, TranslationTier } from '../i18n/localeRegistry';
import { updateUserLanguageApi } from '../services/api';

const LANG_STORAGE_KEY = 'namma_vivasayi_lang';
const TOKEN_STORAGE_KEY = 'namma_vivasayi_auth_token';
const USER_STORAGE_KEY = 'namma_vivasayi_auth_user';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: TranslationSchema;
  isFullyTranslated: boolean;
  tier: TranslationTier;
  coveragePercent: number;
  activeLanguageName: string;
  nativeLanguageName: string;
  direction: TextDirection;
  isRTL: boolean;
  localeMetadata: LocaleMetadata;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    // 1. Check local storage preference
    const saved = localStorage.getItem(LANG_STORAGE_KEY);
    if (saved && (saved in CENTRAL_LOCALE_REGISTRY)) {
      return saved as Language;
    }
    // 2. Check saved user profile
    const savedUserStr = localStorage.getItem(USER_STORAGE_KEY);
    if (savedUserStr) {
      try {
        const u = JSON.parse(savedUserStr);
        if (u?.preferredLanguage && (u.preferredLanguage in CENTRAL_LOCALE_REGISTRY)) {
          return u.preferredLanguage as Language;
        }
      } catch {
        // ignore parse error
      }
    }
    return 'en';
  });

  const metadata = getLocaleMetadata(language);
  const isRTL = metadata.direction === 'rtl';

  // Apply HTML attributes, direction, and fonts on language change
  useEffect(() => {
    const docEl = document.documentElement;
    docEl.lang = language;
    docEl.dir = metadata.direction;
    document.body.dir = metadata.direction;

    if (isRTL) {
      docEl.classList.add('dir-rtl');
      docEl.classList.remove('dir-ltr');
    } else {
      docEl.classList.add('dir-ltr');
      docEl.classList.remove('dir-rtl');
    }

    docEl.style.setProperty('--app-font-family', metadata.fontFamily);
  }, [language, metadata, isRTL]);

  // Sync language with authenticated backend profile
  const setLanguage = useCallback((lang: Language) => {
    if (!(lang in CENTRAL_LOCALE_REGISTRY)) return;
    setLanguageState(lang);
    localStorage.setItem(LANG_STORAGE_KEY, lang);

    // If authenticated, persist to database
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      updateUserLanguageApi(lang, token).then((res) => {
        if (res && res.user) {
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(res.user));
        }
      }).catch((err) => {
        console.warn('Could not persist preferred language to profile:', err);
      });
    }
  }, []);

  // Listen for login/profile updates in localStorage
  useEffect(() => {
    const handleStorageChange = () => {
      const savedUserStr = localStorage.getItem(USER_STORAGE_KEY);
      if (savedUserStr) {
        try {
          const u = JSON.parse(savedUserStr);
          if (u?.preferredLanguage && u.preferredLanguage !== language && (u.preferredLanguage in CENTRAL_LOCALE_REGISTRY)) {
            setLanguageState(u.preferredLanguage as Language);
            localStorage.setItem(LANG_STORAGE_KEY, u.preferredLanguage);
          }
        } catch {
          // ignore
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [language]);

  const toggleLanguage = () => {
    const nextLang = language === 'en' ? 'ta' : 'en';
    setLanguage(nextLang);
  };

  const isFullyTranslated = metadata.tier === 'full';
  const activeLanguageName = `${metadata.name} (${metadata.nativeName})`;
  const nativeLanguageName = metadata.nativeName;

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        toggleLanguage,
        t: getTranslationsForLanguage(language),
        isFullyTranslated,
        tier: metadata.tier,
        coveragePercent: metadata.coveragePercent,
        activeLanguageName,
        nativeLanguageName,
        direction: metadata.direction,
        isRTL,
        localeMetadata: metadata,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Language } from '../types';
import {
  type TranslationSchema,
  getTranslationsForLanguage,
  REGIONAL_LANGUAGE_OPTIONS,
} from '../i18n/translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: TranslationSchema;
  isFullyTranslated: boolean;
  activeLanguageName: string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('namma_vivasayi_lang');
    if (saved && REGIONAL_LANGUAGE_OPTIONS.some((o) => o.code === saved)) {
      return saved as Language;
    }
    return 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('namma_vivasayi_lang', lang);
  };

  const toggleLanguage = () => {
    const nextLang = language === 'en' ? 'ta' : 'en';
    setLanguage(nextLang);
  };

  const currentOption = REGIONAL_LANGUAGE_OPTIONS.find((o) => o.code === language);
  const isFullyTranslated = currentOption ? currentOption.isFullyTranslated : false;
  const activeLanguageName = currentOption ? `${currentOption.name} (${currentOption.nativeName})` : language;

  useEffect(() => {
    document.documentElement.lang = language === 'ta' ? 'ta' : 'en';
  }, [language]);

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        toggleLanguage,
        t: getTranslationsForLanguage(language),
        isFullyTranslated,
        activeLanguageName,
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

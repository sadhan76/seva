import React from 'react';
import { Languages } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export const LanguageToggle: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center bg-emerald-950/10 dark:bg-emerald-900/20 p-1 rounded-xl border border-emerald-200">
      <button
        type="button"
        onClick={() => setLanguage('en')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
          language === 'en'
            ? 'bg-emerald-600 text-white shadow-sm'
            : 'text-emerald-900 hover:text-emerald-950 hover:bg-emerald-100/50'
        }`}
        title="Switch to English"
      >
        <Languages className="w-3.5 h-3.5" />
        English
      </button>
      <button
        type="button"
        onClick={() => setLanguage('ta')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
          language === 'ta'
            ? 'bg-emerald-600 text-white shadow-sm'
            : 'text-emerald-900 hover:text-emerald-950 hover:bg-emerald-100/50'
        }`}
        title="தமிழுக்கு மாற்றுக"
      >
        தமிழ்
      </button>
    </div>
  );
};

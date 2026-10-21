import React, { useState, useRef, useEffect } from 'react';
import { Languages, Check, Search, Globe, ChevronDown, Sparkles } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { REGIONAL_LANGUAGE_OPTIONS, type LanguageOption } from '../../i18n/translations';
import type { Language } from '../../types';

export const LanguageToggle: React.FC = () => {
  const { language, setLanguage, localeMetadata, isRTL } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const filteredLanguages = REGIONAL_LANGUAGE_OPTIONS.filter((opt: LanguageOption) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      opt.name.toLowerCase().includes(q) ||
      opt.nativeName.toLowerCase().includes(q) ||
      opt.code.toLowerCase().includes(q)
    );
  });

  const handleSelectLanguage = (code: Language) => {
    setLanguage(code);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/10 hover:bg-emerald-950/15 border border-emerald-200 text-emerald-900 transition-all font-semibold text-xs shadow-xs focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        title="Select Language / மொழி தேர்வு"
      >
        <Globe className="w-3.5 h-3.5 text-emerald-700" />
        <span className="font-bold">{localeMetadata.nativeName}</span>
        <span className="text-[11px] opacity-75 hidden sm:inline">({localeMetadata.name})</span>
        {localeMetadata.direction === 'rtl' && (
          <span className="text-[10px] bg-emerald-200/80 text-emerald-900 px-1 py-0.2 rounded font-mono">
            RTL
          </span>
        )}
        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={`absolute ${isRTL ? 'left-0' : 'right-0'} mt-2 w-80 sm:w-96 rounded-2xl bg-white shadow-2xl border border-slate-200/90 z-50 p-3 max-h-[85vh] flex flex-col text-slate-800 animate-in fade-in zoom-in-95 duration-150`}
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Languages className="w-4 h-4 text-emerald-600" />
              <div>
                <h3 className="text-xs font-bold text-slate-900">
                  Regional Languages / பிராந்திய மொழிகள்
                </h3>
                <p className="text-[10px] text-slate-500">
                  22 Eighth Schedule Languages + English
                </p>
              </div>
            </div>
            <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
              23 Languages
            </span>
          </div>

          {/* Search Box */}
          <div className="relative my-2">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search language / ভাষা / भाषा खोजें..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-hidden focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 bg-slate-50 placeholder:text-slate-400"
              autoFocus
            />
          </div>

          {/* Languages List */}
          <div className="overflow-y-auto space-y-1 max-h-72 pr-1 custom-scrollbar">
            {filteredLanguages.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-500">
                No matching language found.
              </div>
            ) : (
              filteredLanguages.map((opt) => {
                const isSelected = opt.code === language;
                return (
                  <button
                    key={opt.code}
                    type="button"
                    onClick={() => handleSelectLanguage(opt.code)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition-colors ${
                      isSelected
                        ? 'bg-emerald-600 text-white font-bold shadow-xs'
                        : 'hover:bg-emerald-50/80 text-slate-800 hover:text-emerald-950'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">{opt.nativeName}</span>
                          <span className={`text-[11px] ${isSelected ? 'text-emerald-100' : 'text-slate-500'}`}>
                            ({opt.name})
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {opt.direction === 'rtl' && (
                            <span
                              className={`text-[9px] font-mono px-1 py-0.2 rounded ${
                                isSelected ? 'bg-emerald-700 text-white' : 'bg-amber-100 text-amber-900'
                              }`}
                            >
                              RTL
                            </span>
                          )}
                          <span
                            className={`text-[9px] px-1.5 py-0.2 rounded font-medium ${
                              isSelected
                                ? 'bg-emerald-700 text-emerald-100'
                                : opt.tier === 'full'
                                ? 'bg-emerald-100 text-emerald-800'
                                : opt.tier === 'core'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {opt.tier === 'full' ? 'Full UI (100%)' : opt.tier === 'core' ? `Core UI (${opt.coveragePercent}%)` : `Essential (${opt.coveragePercent}%)`}
                          </span>
                        </div>
                      </div>
                    </div>

                    {isSelected && <Check className="w-4 h-4 text-white shrink-0 ml-2" />}
                  </button>
                );
              })
            )}
          </div>

          {/* Footer Note */}
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              Persists across login sessions
            </span>
            <span>Eighth Schedule</span>
          </div>
        </div>
      )}
    </div>
  );
};

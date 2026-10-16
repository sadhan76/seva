import React from 'react';
import { Bot, Bug, CalendarPlus, TrendingUp, Sparkles, type LucideIcon } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import type { NavTab } from '../../types';

interface QuickActionsProps {
  onNavigate: (tab: NavTab) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onNavigate }) => {
  const { t, language } = useLanguage();

  const actions: Array<{
    tab: NavTab;
    titleEn: string;
    titleTa: string;
    descEn: string;
    descTa: string;
    icon: LucideIcon;
    color: string;
    bgColor: string;
  }> = [
    {
      tab: 'assistant',
      titleEn: 'AI Farming Assistant',
      titleTa: 'விவசாய AI வழிகாட்டி',
      descEn: 'Ask questions in Tamil or English',
      descTa: 'பயிர் மற்றும் உரம் குறித்த சந்தேகங்கள்',
      icon: Bot,
      color: 'text-emerald-700',
      bgColor: 'bg-emerald-50 hover:bg-emerald-100/80 border-emerald-200',
    },
    {
      tab: 'disease',
      titleEn: 'Scan Plant Disease',
      titleTa: 'நோய் கண்டறிதல்',
      descEn: 'AI photo diagnosis & remedies',
      descTa: 'இலை படம் மூலம் பூச்சி/நோய் அறிய',
      icon: Bug,
      color: 'text-rose-700',
      bgColor: 'bg-rose-50 hover:bg-rose-100/80 border-rose-200',
    },
    {
      tab: 'procurement',
      titleEn: 'Book Mandi Slot',
      titleTa: 'கொள்முதல் முன்பதிவு',
      descEn: 'Reserve direct DPC time window',
      descTa: 'நெல் மூட்டை விற்பனைக்கான அனுமதி',
      icon: CalendarPlus,
      color: 'text-blue-700',
      bgColor: 'bg-blue-50 hover:bg-blue-100/80 border-blue-200',
    },
    {
      tab: 'market',
      titleEn: 'Market Prices',
      titleTa: 'சந்தை விலை விபரம்',
      descEn: 'Daily mandi rates across TN',
      descTa: 'இன்றைய விலை நிலவரம் மற்றும் போக்கு',
      icon: TrendingUp,
      color: 'text-amber-700',
      bgColor: 'bg-amber-50 hover:bg-amber-100/80 border-amber-200',
    },
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-emerald-600" />
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
          {t.dashboard.quickActionsTitle}
        </h3>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {actions.map((act) => {
          const Icon = act.icon;
          return (
            <button
              key={act.tab}
              type="button"
              onClick={() => onNavigate(act.tab)}
              className={`flex flex-col text-left p-3.5 rounded-2xl border transition-all duration-200 shadow-sm hover:shadow active:scale-[0.98] ${act.bgColor}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-xl bg-white shadow-xs ${act.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-xs text-slate-400 font-bold">→</span>
              </div>
              <p className="text-xs md:text-sm font-bold text-slate-800 leading-snug">
                {language === 'ta' ? act.titleTa : act.titleEn}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                {language === 'ta' ? act.descTa : act.descEn}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};

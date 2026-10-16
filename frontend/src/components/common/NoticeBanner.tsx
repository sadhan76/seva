import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

export const NoticeBanner: React.FC = () => {
  const { language } = useLanguage();
  const { user } = useAuth();

  return (
    <div className="mb-6 rounded-2xl bg-emerald-50/90 border border-emerald-200 p-3.5 text-emerald-950 shadow-xs transition-all">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-emerald-100 p-2 text-emerald-800 shrink-0">
          <ShieldCheck className="w-5 h-5 text-emerald-700" />
        </div>
        <div className="flex-1 text-xs md:text-sm leading-relaxed">
          <span className="font-extrabold tracking-wide uppercase text-[10px] bg-emerald-200/90 text-emerald-900 px-2 py-0.5 rounded-full mr-2">
            {language === 'ta' ? 'அங்கீகரிக்கப்பட்ட அமர்வு' : 'AUTHENTICATED SESSION'}
          </span>
          <span className="text-slate-700 font-medium">
            {language === 'ta'
              ? `${user?.name || 'விவசாயி'} அவர்களின் நேரடி சுயவிவரம் மற்றும் தமிழ்நாடு கொள்முதல் மையம் இணைக்கப்பட்டுள்ளது.`
              : `Operating with live authenticated database for ${user?.name || 'Farmer'} and verified Tamil Nadu direct procurement centre records.`}
          </span>
        </div>
      </div>
    </div>
  );
};

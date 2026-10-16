import React from 'react';
import { Sprout, MapPin, Calendar, CheckCircle2, Bot, CalendarPlus, Sparkles, Droplets, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import type { NavTab, FarmerProfile } from '../../types';

interface FarmerWelcomeHeroProps {
  onNavigate: (tab: NavTab) => void;
  farmer?: FarmerProfile | null;
}

export const FarmerWelcomeHero: React.FC<FarmerWelcomeHeroProps> = ({ onNavigate, farmer }) => {
  const { t, language } = useLanguage();
  const { user } = useAuth();

  const farmerName = user?.fullName || user?.name || farmer?.name || (language === 'ta' ? 'விவசாயி' : 'Farmer');
  const farmerLocation = user?.village
    ? `${user.village}, ${user.district || 'Tamil Nadu'}`
    : (user?.district ? `${user.district}, Tamil Nadu` : (farmer?.location || 'Tamil Nadu'));
  
  const primaryCrop = user?.primaryCrop || farmer?.primaryCrop || (language === 'ta' ? 'குறிப்பிடப்படவில்லை' : 'Not provided');
  const landArea = user?.totalLandAcres || farmer?.totalLandAcres;
  const soilType = user?.soilType || farmer?.soilType || (language === 'ta' ? 'விவரம் தேவை' : 'Profile incomplete');

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900 via-emerald-800 to-green-900 text-white shadow-xl shadow-emerald-950/10 mb-8 border border-emerald-700/40">
      {/* Decorative background glows */}
      <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 rounded-full bg-emerald-500/20 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 -mb-16 w-80 h-80 rounded-full bg-green-400/15 blur-2xl pointer-events-none" />

      <div className="relative p-6 sm:p-8 lg:p-10">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* Left Greeting & Summary */}
          <div className="max-w-2xl space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-700/80 text-emerald-200 border border-emerald-500/40 backdrop-blur-xs">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                {t.welcome.todayBadge}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-emerald-100 bg-white/10 border border-white/15 backdrop-blur-xs">
                <MapPin className="w-3.5 h-3.5 text-emerald-300" />
                {farmerLocation}
              </span>
              {user?.isAadhaarVerified ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-emerald-200 bg-emerald-950/60 border border-emerald-600/40">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Aadhaar Verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-emerald-200 bg-emerald-950/60 border border-emerald-600/40">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  {language === 'ta' ? 'அங்கீகரிக்கப்பட்ட விவசாயி' : 'Authenticated Farmer'}
                </span>
              )}
            </div>

            <div>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
                {t.welcome.greeting}{' '}
                <span className="text-emerald-300 font-black">
                  {farmerName}
                </span>
              </h2>
              <p className="text-xs sm:text-sm text-emerald-100/90 font-medium leading-relaxed mt-2 max-w-xl">
                {language === 'ta'
                  ? 'உங்கள் பண்ணைக்கான நேரடி நுண்ணறிவு, வானிலை முன்னறிவிப்பு மற்றும் நேரடி நெல் கொள்முதல் முன்பதிவு.'
                  : 'Real-time microclimate advisory, data-driven irrigation advice, and regulated procurement tracking for your farm.'}
              </p>
            </div>
          </div>

          {/* Right Action Shortcuts */}
          <div className="flex flex-wrap sm:flex-nowrap lg:flex-col gap-2.5 shrink-0 justify-start">
            <button
              onClick={() => onNavigate('assistant')}
              className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white text-emerald-950 hover:bg-emerald-50 font-bold text-xs sm:text-sm shadow-md transition-all active:scale-[0.98]"
            >
              <div className="p-1 rounded-lg bg-emerald-100 text-emerald-800">
                <Bot className="w-4 h-4" />
              </div>
              <span>{t.welcome.quickAssistantBtn}</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-700 ml-auto" />
            </button>

            <button
              onClick={() => onNavigate('procurement')}
              className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-emerald-700/80 hover:bg-emerald-600 text-white font-bold text-xs sm:text-sm border border-emerald-500/40 shadow-sm transition-all active:scale-[0.98]"
            >
              <div className="p-1 rounded-lg bg-emerald-800/80 text-emerald-200">
                <CalendarPlus className="w-4 h-4" />
              </div>
              <span>{t.welcome.quickMandiBtn}</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-300 ml-auto" />
            </button>
          </div>
        </div>

        {/* 4 Personalized Telemetry Quick Chips */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8 pt-6 border-t border-emerald-700/50">
          <div className="rounded-2xl bg-white/10 backdrop-blur-md p-3.5 border border-white/10 hover:border-emerald-400/30 transition-all">
            <div className="flex items-center gap-2 text-emerald-300 text-[11px] font-bold uppercase tracking-wider mb-1">
              <Sprout className="w-3.5 h-3.5 text-emerald-400" />
              {language === 'ta' ? 'முக்கிய பயிர்' : 'Primary Crop'}
            </div>
            <p className="text-xs sm:text-sm font-extrabold text-white truncate">
              {primaryCrop}
            </p>
            <p className="text-[11px] text-emerald-200/80 font-medium mt-0.5">
              {landArea ? `${landArea} Acres` : (language === 'ta' ? 'பரப்பளவு தேவை' : 'Holding not set')}
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 backdrop-blur-md p-3.5 border border-white/10 hover:border-emerald-400/30 transition-all">
            <div className="flex items-center gap-2 text-emerald-300 text-[11px] font-bold uppercase tracking-wider mb-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              {language === 'ta' ? 'மண் வகை' : 'Soil Profile'}
            </div>
            <p className="text-xs sm:text-sm font-extrabold text-white truncate">
              {soilType}
            </p>
            <p className="text-[11px] text-emerald-200/80 font-medium mt-0.5">
              {user?.district || 'Tamil Nadu'} Zone
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 backdrop-blur-md p-3.5 border border-white/10 hover:border-emerald-400/30 transition-all">
            <div className="flex items-center gap-2 text-emerald-300 text-[11px] font-bold uppercase tracking-wider mb-1">
              <Droplets className="w-3.5 h-3.5 text-blue-300" />
              {language === 'ta' ? 'பாசன முறை' : 'Irrigation Source'}
            </div>
            <p className="text-xs sm:text-sm font-extrabold text-white truncate">
              {user?.irrigationSource || farmer?.irrigationSource || (language === 'ta' ? 'கால்வாய் / ஆழ்துளை' : 'Canal / Borewell')}
            </p>
            <p className="text-[11px] text-emerald-200/80 font-medium mt-0.5">
              {language === 'ta' ? 'பரிந்துரை: காலை 6:30' : 'Cycle: Early Morning'}
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 backdrop-blur-md p-3.5 border border-white/10 hover:border-emerald-400/30 transition-all">
            <div className="flex items-center gap-2 text-emerald-300 text-[11px] font-bold uppercase tracking-wider mb-1">
              <Calendar className="w-3.5 h-3.5 text-emerald-300" />
              {language === 'ta' ? 'கொள்முதல் மையம்' : 'Procurement Mandi'}
            </div>
            <p className="text-xs sm:text-sm font-extrabold text-white truncate">
              {user?.district ? `${user.district} DPC` : 'Regulated Mandi'}
            </p>
            <p className="text-[11px] text-emerald-200/80 font-medium mt-0.5">
              {user?.farmerId || 'Direct Purchase Centre'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

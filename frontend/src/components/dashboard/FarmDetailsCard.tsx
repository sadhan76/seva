import React from 'react';
import { Sprout, ShieldAlert, CheckCircle2, Edit3 } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import type { FarmerProfile } from '../../types';

interface FarmDetailsCardProps {
  farmer: FarmerProfile;
  onViewProfile?: () => void;
}

export const FarmDetailsCard: React.FC<FarmDetailsCardProps> = ({
  farmer,
  onViewProfile,
}) => {
  const { t, language } = useLanguage();

  return (
    <Card
      title={t.dashboard.farmDetailsTitle}
      subtitle={farmer.location || (language === 'ta' ? 'தமிழ்நாடு' : 'Tamil Nadu')}
      icon={<Sprout className="w-5 h-5 text-emerald-600" />}
      headerAction={
        <div className="flex items-center gap-1.5">
          <Badge variant={farmer.isFromDb ? 'emerald' : 'slate'} dot>
            {farmer.isFromDb
              ? (language === 'ta' ? 'சரிபார்க்கப்பட்ட சுயவிவரம்' : 'Live Profile')
              : (language === 'ta' ? 'முழுமையற்றது' : 'Profile Pending')}
          </Badge>
          {onViewProfile && (
            <button
              onClick={onViewProfile}
              className="p-1 rounded-lg text-emerald-700 hover:bg-emerald-50 transition-colors"
              title={t.common.editProfile || 'Edit Profile'}
              aria-label={t.common.editProfile || 'Edit Profile'}
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      }
      footer={
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1.5 font-medium text-emerald-700">
            {farmer.aadhaarMasked ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Aadhaar ({farmer.aadhaarMasked})</span>
              </>
            ) : (
              <>
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                <span className="text-slate-500">
                  {language === 'ta' ? 'ஆதார்: இணைக்கப்படவில்லை' : 'Aadhaar: Not Linked'}
                </span>
              </>
            )}
          </span>
          {onViewProfile && (
            <button
              onClick={onViewProfile}
              className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 hover:text-emerald-800 hover:underline"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>{t.common.editProfile || 'Edit Profile'} →</span>
            </button>
          )}
        </div>
      }
    >
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <div className="rounded-xl bg-slate-50/80 p-3 border border-slate-100">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {t.dashboard.labels.farmerName}
          </p>
          <p className="text-sm font-bold text-slate-800 mt-0.5 truncate">
            {farmer.name || (language === 'ta' ? 'வழங்கப்படவில்லை' : 'Not provided')}
          </p>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
            {farmer.farmerId || (language === 'ta' ? 'ஒதுக்கீடு செய்யப்படுகிறது' : 'Pending Allocation')}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50/80 p-3 border border-slate-100">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {t.dashboard.labels.landSize}
          </p>
          <p className="text-sm font-bold text-slate-800 mt-0.5">
            {farmer.totalLandAcres
              ? `${farmer.totalLandAcres} ${t.dashboard.labels.acres}`
              : (language === 'ta' ? 'வழங்கப்படவில்லை' : 'Not provided')}
          </p>
          <p className="text-[11px] text-emerald-600 font-medium mt-0.5">
            {farmer.totalLandAcres ? 'Wetland / நஞ்சை' : (language === 'ta' ? 'பரப்பளவை சேர்க்கவும்' : 'Set land area')}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50/80 p-3 border border-slate-100">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {t.dashboard.labels.primaryCrop}
          </p>
          <p className="text-sm font-bold text-slate-800 mt-0.5 truncate">
            {farmer.primaryCrop || (language === 'ta' ? 'வழங்கப்படவில்லை' : 'Not provided')}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {farmer.primaryCrop ? 'Kharif / Samba' : (language === 'ta' ? 'பயிரை தேர்வு செய்க' : 'Specify crop')}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50/80 p-3 border border-slate-100">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {t.dashboard.labels.soilType}
          </p>
          <p className="text-sm font-bold text-slate-800 mt-0.5 truncate">
            {farmer.soilType || (language === 'ta' ? 'வழங்கப்படவில்லை' : 'Not provided')}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5 truncate">
            {farmer.soilType ? 'pH: 6.8 (Neutral)' : (language === 'ta' ? 'மண் பரிசோதனை தேவை' : 'Soil test pending')}
          </p>
        </div>
      </div>
    </Card>
  );
};

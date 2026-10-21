import React, { useState } from 'react';
import {
  UserPlus,
  AlertCircle,
  Loader2,
  X,
  Lock,
  Phone,
  User,
  Globe2,
  Sprout,
  Droplets,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { REGIONAL_LANGUAGE_OPTIONS, IRRIGATION_OPTIONS } from '../../i18n/translations';
import type { Language } from '../../types';
import { GeoLocationSelect, type GeoLocationValue } from '../common/GeoLocationSelect';

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

export const RegisterModal: React.FC<RegisterModalProps> = ({
  isOpen,
  onClose,
  onSwitchToLogin,
}) => {
  const { t, language, setLanguage } = useLanguage();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [geoLoc, setGeoLoc] = useState<GeoLocationValue>({
    country: 'India',
    state: '',
    stateCode: '',
    district: '',
    districtCode: '',
    village: '',
    taluk: '',
  });
  const [prefLang, setPrefLang] = useState<Language>(language);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Phase 19: Positive whole integer land acres & multi-select irrigation
  const [landAcres, setLandAcres] = useState<string>('3');
  const [primaryCrop, setPrimaryCrop] = useState('Paddy (Ponni Samba)');
  const [soilType, setSoilType] = useState('Alluvial Clay Loam');
  const [irrigationSources, setIrrigationSources] = useState<string[]>([
    'Borewell / Tube Well',
    'Canal',
  ]);
  const [otherIrrigationDetail, setOtherIrrigationDetail] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggleIrrigation = (source: string) => {
    setIrrigationSources((prev) => {
      if (prev.includes(source)) {
        const next = prev.filter((s) => s !== source);
        return next.length > 0 ? next : [source];
      } else {
        return [...prev, source];
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    // Frontend validation
    if (!fullName.trim()) {
      setErrorMessage('Please enter your full name.');
      return;
    }

    const phoneClean = phone.trim().replace(/\D/g, '');
    if (!/^[6-9]\d{9}$/.test(phoneClean)) {
      setErrorMessage('Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.');
      return;
    }

    if (!geoLoc.state.trim() || !geoLoc.district.trim() || !(geoLoc.village?.trim() || geoLoc.taluk?.trim())) {
      setErrorMessage('Please select your State/UT, District, and enter your Village/Taluk.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify both password fields.');
      return;
    }

    // Strict Integer Land Area Validation
    const acresStr = landAcres.trim();
    if (!acresStr || !/^\d+$/.test(acresStr)) {
      setErrorMessage('Total land area must be a positive whole number (e.g., 1, 2, 5 acres). Decimals or fractions are not permitted.');
      return;
    }
    const acresNum = parseInt(acresStr, 10);
    if (acresNum <= 0) {
      setErrorMessage('Total land area must be at least 1 acre.');
      return;
    }

    // Irrigation Validation
    if (irrigationSources.length === 0) {
      setErrorMessage('Please select at least one irrigation source.');
      return;
    }
    if (irrigationSources.includes('Other') && !otherIrrigationDetail.trim()) {
      setErrorMessage('Please specify your custom irrigation detail for "Other".');
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        name: fullName.trim(),
        phone: phoneClean,
        country: geoLoc.country || 'India',
        village: geoLoc.village?.trim() || geoLoc.taluk?.trim() || '',
        taluk: geoLoc.taluk?.trim(),
        district: geoLoc.district.trim(),
        districtCode: geoLoc.districtCode,
        state: geoLoc.state.trim(),
        stateCode: geoLoc.stateCode,
        preferredLanguage: prefLang,
        password,
        confirmPassword,
        totalLandAcres: acresNum,
        primaryCrop: primaryCrop.trim() || 'Paddy (Ponni)',
        soilType: soilType.trim() || 'Alluvial Clay Loam',
        irrigationSources,
        otherIrrigationDetail: irrigationSources.includes('Other') ? otherIrrigationDetail.trim() : undefined,
      });

      // Synchronize language toggle if preferred language differs
      if (prefLang !== language) {
        setLanguage(prefLang);
      }

      setSuccessMessage(t.auth.registerSuccess);
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err: any) {
      const msg = err.message || '';
      if (msg.includes('fetch') || msg.includes('Unable to connect') || msg.includes('NetworkError')) {
        setErrorMessage('Unable to connect to AgriBharat server. Please ensure the backend is running at http://127.0.0.1:8000.');
      } else {
        setErrorMessage(err.message || 'Registration failed. Please verify details.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedLang = REGIONAL_LANGUAGE_OPTIONS.find((l) => l.code === prefLang);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center mb-3 shadow-xs">
            <UserPlus className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">
            {t.auth.registerTitle}
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            {t.auth.registerSubtitle}
          </p>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-emerald-600" />
            <span className="flex-1 font-semibold">{successMessage}</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 p-3.5 rounded-xl bg-rose-50 border border-rose-300 text-rose-900 text-xs flex items-start gap-2.5 animate-shake">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span className="flex-1 font-medium">{errorMessage}</span>
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Full Name */}
          <div>
            <label className="block font-bold text-slate-700 mb-1">
              {t.auth.fullNameLabel} <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Murugesan K."
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Mobile Number */}
          <div>
            <label className="block font-bold text-slate-700 mb-1">
              {t.auth.mobileLabel} (10 Digits) <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="tel"
                required
                maxLength={10}
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                placeholder="e.g. 9876543210"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Complete India-wide Location Selection */}
          <GeoLocationSelect
            value={geoLoc}
            onChange={setGeoLoc}
            required
            showAttribution
            compact
          />

          {/* Preferred Language (16 Options) */}
          <div>
            <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Globe2 className="w-3.5 h-3.5 text-emerald-600" />
                Preferred Regional Language (16 Languages) *
              </span>
              {selectedLang && !selectedLang.isFullyTranslated && (
                <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  AI & Voice
                </span>
              )}
            </label>
            <select
              value={prefLang}
              onChange={(e) => setPrefLang(e.target.value as Language)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            >
              {REGIONAL_LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.code} value={opt.code}>
                  {opt.name} ({opt.nativeName}) {opt.isFullyTranslated ? '• Full UI' : '• AI & Voice'}
                </option>
              ))}
            </select>
          </div>

          {/* Land Area (Whole Integer) & Primary Crop & Soil */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Total Land (Whole Acres) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="1"
                min="1"
                required
                value={landAcres}
                onChange={(e) => setLandAcres(e.target.value)}
                placeholder="e.g. 3"
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500/20"
              />
              <p className="text-[9px] text-slate-500 mt-0.5">Whole numbers only</p>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Primary Crop <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Sprout className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  value={primaryCrop}
                  onChange={(e) => setPrimaryCrop(e.target.value)}
                  placeholder="Paddy / Cotton"
                  className="w-full pl-8 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Soil Type
              </label>
              <input
                type="text"
                value={soilType}
                onChange={(e) => setSoilType(e.target.value)}
                placeholder="Alluvial Clay Loam"
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
          </div>

          {/* Irrigation Sources Checkbox Group */}
          <div className="space-y-2 p-3 bg-slate-50 rounded-2xl border border-slate-200">
            <div className="flex items-center justify-between">
              <label className="block text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                <Droplets className="w-3.5 h-3.5 text-blue-600" />
                <span>Irrigation Sources (Multi-select) *</span>
              </label>
              <span className="text-[10px] text-slate-500 font-semibold">
                {irrigationSources.length} selected
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-40 overflow-y-auto pr-1">
              {IRRIGATION_OPTIONS.map((opt) => {
                const isChecked = irrigationSources.includes(opt);
                return (
                  <label
                    key={opt}
                    className={`flex items-center gap-2 p-1.5 rounded-lg border text-xs cursor-pointer transition-all ${
                      isChecked
                        ? 'bg-blue-50/70 border-blue-300 text-blue-900 font-bold'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleIrrigation(opt)}
                      className="rounded text-blue-600 focus:ring-blue-500 w-3.5 h-3.5 border-slate-300"
                    />
                    <span className="select-none text-[11px]">{opt}</span>
                  </label>
                );
              })}
            </div>

            {irrigationSources.includes('Other') && (
              <div className="pt-2 animate-fade-in">
                <label className="block text-[10px] font-bold text-blue-900 mb-1">
                  Specify Custom Irrigation Source *:
                </label>
                <input
                  type="text"
                  required
                  value={otherIrrigationDetail}
                  onChange={(e) => setOtherIrrigationDetail(e.target.value)}
                  placeholder="e.g. Solar Lift Pump from stream"
                  className="w-full px-3 py-1.5 bg-white border border-blue-300 rounded-xl text-xs font-medium"
                />
              </div>
            )}
          </div>

          {/* Account Security & Phone Ownership Disclosure */}
          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 flex items-center gap-1.5 text-xs">
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              Account Security Notice
            </span>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Your farmer profile is secured by your chosen password. Phone ownership is not verified as no SMS provider is currently active.
            </p>
          </div>

          {/* Password & Confirm Password */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">
                {t.auth.passwordLabel} <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 6 chars"
                  className="w-full pl-8 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                {t.auth.confirmPasswordLabel} <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat password"
                  className="w-full pl-8 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50 mt-4"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating Farmer Account...
              </>
            ) : (
              t.auth.registerBtn
            )}
          </button>
        </form>

        {/* Footer switch to login */}
        <div className="mt-5 pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
          <p>{t.auth.alreadyHaveAccount}</p>
          <button
            type="button"
            onClick={() => {
              onClose();
              onSwitchToLogin();
            }}
            className="mt-1 font-bold text-emerald-700 hover:text-emerald-800 hover:underline"
          >
            {t.auth.signIn} →
          </button>
        </div>
      </div>
    </div>
  );
};

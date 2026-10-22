import React, { useState } from 'react';
import {
  Sprout,
  LogIn,
  UserPlus,
  UserCheck,
  Building2,
  AlertCircle,
  Loader2,
  Lock,
  Phone,
  Eye,
  EyeOff,
  User,
  Sparkles,
  CheckCircle2,
  ShieldAlert,
  Globe2,
  Droplets,
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { LanguageToggle } from '../common/LanguageToggle';
import { REGIONAL_LANGUAGE_OPTIONS, IRRIGATION_OPTIONS } from '../../i18n/translations';
import type { Language } from '../../types';
import { GeoLocationSelect, type GeoLocationValue } from '../common/GeoLocationSelect';

interface LoginPageProps {
  initialMode?: 'signin' | 'register';
}

export const LoginPage: React.FC<LoginPageProps> = ({ initialMode = 'signin' }) => {
  const { t, language, setLanguage } = useLanguage();
  const { login, register } = useAuth();

  const [mode, setMode] = useState<'signin' | 'register'>(initialMode);

  // Sign-in state
  const [role, setRole] = useState<'farmer' | 'staff'>('farmer');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Registration state
  const [regName, setRegName] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regLoc, setRegLoc] = useState<GeoLocationValue>({
    country: 'India',
    state: '',
    stateCode: '',
    district: '',
    districtCode: '',
    village: '',
    taluk: '',
  });
  const [regPrefLang, setRegPrefLang] = useState<Language>(language);
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  
  // Phase 19: Integer Land Area & Multi-select Irrigation
  const [regLandAcres, setRegLandAcres] = useState<string>('3');
  const [regPrimaryCrop, setRegPrimaryCrop] = useState('Samba Paddy (CR 1009 Sub 1)');
  const [regSoilType, setRegSoilType] = useState('Alluvial Clay Loam');
  const [regIrrigationSources, setRegIrrigationSources] = useState<string[]>([
    'Borewell / Tube Well',
    'Canal'
  ]);
  const [regOtherIrrigationDetail, setRegOtherIrrigationDetail] = useState('');

  // Loading & error state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Handle Role Selection without injecting credentials
  const handleSelectRole = (targetRole: 'farmer' | 'staff') => {
    setRole(targetRole);
    setErrorMessage(null);
  };

  // Handle Quick Demo Fill (Local Development Helper Only)
  const handleQuickDemo = (demoRole: 'farmer' | 'staff') => {
    setRole(demoRole);
    setErrorMessage(null);
    if (demoRole === 'farmer') {
      setPhone('9876543299');
      setPassword('FarmerPassword@123');
    } else {
      setPhone('9842012345');
      setPassword('MandiStaff@2026');
    }
  };

  // Toggle irrigation source checkbox
  const handleToggleIrrigation = (source: string) => {
    setRegIrrigationSources((prev) => {
      if (prev.includes(source)) {
        const next = prev.filter((s) => s !== source);
        return next.length > 0 ? next : [source]; // Ensure at least 1 remains
      } else {
        return [...prev, source];
      }
    });
  };

  // Sign In Handler
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanPhone = phone.trim().replace(/\D/g, '');
    if (!cleanPhone || cleanPhone.length !== 10) {
      setErrorMessage(
        language === 'ta'
          ? 'சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்.'
          : 'Please enter a valid 10-digit mobile number.'
      );
      return;
    }

    if (!password.trim()) {
      setErrorMessage(
        language === 'ta'
          ? 'கடவுச்சொல்லை உள்ளிடவும்.'
          : 'Please enter your password.'
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        phone: cleanPhone,
        password: password.trim(),
        role,
      });
    } catch (err: any) {
      const msg = err.message || '';
      if (msg.includes('fetch') || msg.includes('Unable to connect') || msg.includes('NetworkError')) {
        setErrorMessage(
          language === 'ta'
            ? 'அக்ரிபாரத் சேவையகத்துடன் இணைக்க முடியவில்லை. பின்தள சேவையகம் இயங்குவதை உறுதிசெய்யவும்.'
            : 'Unable to connect to AgriBharat backend server. Please ensure the backend service is running.'
        );
      } else {
        setErrorMessage(
          err.message || (language === 'ta' ? 'உள்நுழைவு தோல்வியடைந்தது. விவரங்களை சரிபார்க்கவும்.' : 'Authentication failed. Please verify credentials.')
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Registration Handler
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!regName.trim()) {
      setErrorMessage(language === 'ta' ? 'விவசாயி பெயரை உள்ளிடவும்.' : 'Please enter your full name.');
      return;
    }

    const cleanPhone = regPhone.trim().replace(/\D/g, '');
    if (!/^[6-9]\d{9}$/.test(cleanPhone)) {
      setErrorMessage(
        language === 'ta'
          ? '6, 7, 8 அல்லது 9 இல் தொடங்கும் சரியான 10 இலக்க இந்திய மொபைல் எண்ணை உள்ளிடவும்.'
          : 'Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.'
      );
      return;
    }

    if (!regLoc.state.trim() || !regLoc.district.trim() || !(regLoc.village?.trim() || regLoc.taluk?.trim())) {
      setErrorMessage(
        language === 'ta'
          ? 'உங்கள் மாநிலம், மாவட்டம் மற்றும் கிராமத்தை உள்ளிடவும்/தேர்ந்தெடுக்கவும்.'
          : 'Please select your State/UT, District, and enter your Village/Taluk.'
      );
      return;
    }

    if (regPassword.length < 6) {
      setErrorMessage(
        language === 'ta'
          ? 'கடவுச்சொல் குறைந்தது 6 எழுத்துகள் கொண்டிருக்க வேண்டும்.'
          : 'Password must be at least 6 characters long.'
      );
      return;
    }

    if (regPassword !== regConfirmPassword) {
      setErrorMessage(
        language === 'ta'
          ? 'கடவுச்சொற்கள் பொருந்தவில்லை.'
          : 'Passwords do not match. Please verify both fields.'
      );
      return;
    }

    // Phase 19: Strict Positive Integer Validation for Land Area
    const acresStr = regLandAcres.trim();
    if (!acresStr || !/^\d+$/.test(acresStr)) {
      setErrorMessage(
        language === 'ta'
          ? 'நிலப்பரப்பு நேர்மறை முழு எண்ணாக மட்டுமே இருக்க வேண்டும் (எ.கா: 1, 2, 5). தசமங்கள் அனுமதிக்கப்படாது.'
          : 'Total land area must be a positive whole integer (e.g., 1, 2, 5 acres). Decimals, negatives, or non-numeric values are not permitted.'
      );
      return;
    }
    const acresNum = parseInt(acresStr, 10);
    if (acresNum <= 0) {
      setErrorMessage(
        language === 'ta'
          ? 'நிலப்பரப்பு 1 ஏக்கர் அல்லது அதற்கு மேல் இருக்க வேண்டும்.'
          : 'Total land area must be at least 1 acre.'
      );
      return;
    }

    // Irrigation validation
    if (regIrrigationSources.length === 0) {
      setErrorMessage(
        language === 'ta'
          ? 'குறைந்தது ஒரு பாசன ஆதாரத்தைத் தேர்ந்தெடுக்கவும்.'
          : 'Please select at least one irrigation source.'
      );
      return;
    }

    if (regIrrigationSources.includes('Other') && !regOtherIrrigationDetail.trim()) {
      setErrorMessage(
        language === 'ta'
          ? '"மற்றவை" பாசன வகையைத் தேர்ந்தெடுத்தால், விவரத்தைக் குறிப்பிடவும்.'
          : 'Please specify the custom irrigation source detail for "Other".'
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        name: regName.trim(),
        phone: cleanPhone,
        country: regLoc.country || 'India',
        village: regLoc.village?.trim() || regLoc.taluk?.trim() || '',
        taluk: regLoc.taluk?.trim(),
        district: regLoc.district.trim(),
        districtCode: regLoc.districtCode,
        state: regLoc.state.trim(),
        stateCode: regLoc.stateCode,
        preferredLanguage: regPrefLang,
        password: regPassword,
        confirmPassword: regConfirmPassword,
        totalLandAcres: acresNum,
        primaryCrop: regPrimaryCrop.trim() || 'Paddy (Samba)',
        soilType: regSoilType.trim() || 'Alluvial Clay Loam',
        irrigationSources: regIrrigationSources,
        otherIrrigationDetail: regIrrigationSources.includes('Other') ? regOtherIrrigationDetail.trim() : undefined,
      });

      // Synchronize language state if user selected a different regional language
      if (regPrefLang !== language) {
        setLanguage(regPrefLang);
      }

      setSuccessMessage(
        language === 'ta'
          ? 'விவசாயி கணக்கு வெற்றிகரமாக உருவாக்கப்பட்டது! உங்கள் டாஷ்போர்டு திறக்கப்படுகிறது...'
          : 'Farmer account registered successfully! Opening your dashboard...'
      );
    } catch (err: any) {
      const msg = err.message || '';
      if (msg.includes('fetch') || msg.includes('Unable to connect') || msg.includes('NetworkError')) {
        setErrorMessage(
          language === 'ta'
            ? 'அக்ரிபாரத் சேவையகத்துடன் இணைக்க முடியவில்லை. பின்தள சேவையகம் இயங்குவதை உறுதிசெய்யவும்.'
            : 'Unable to connect to AgriBharat backend server. Please ensure the backend service is running.'
        );
      } else {
        setErrorMessage(
          err.message || (language === 'ta' ? 'பதிவு தோல்வியடைந்தது. மீண்டும் முயற்சிக்கவும்.' : 'Registration failed. Please check your inputs.')
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedLangOption = REGIONAL_LANGUAGE_OPTIONS.find((l) => l.code === regPrefLang);

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50/60 via-slate-50 to-emerald-50/40 flex flex-col antialiased text-slate-800">
      {/* Top Navigation Bar */}
      <nav className="w-full bg-white/90 backdrop-blur-md border-b border-emerald-100 px-4 md:px-8 py-3.5 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-700 to-green-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/20">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-slate-900 text-base sm:text-lg tracking-tight">
                {t.appName}
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                Tamil Nadu Agri
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium hidden sm:block">
              {language === 'ta'
                ? 'நேரடி நெல் கொள்முதல் மற்றும் நுண்ணறிவு வேளாண் தளம்'
                : 'Smart Farming Intelligence & Mandi Procurement Platform'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <LanguageToggle />
        </div>
      </nav>

      {/* Main Authentication Card Container */}
      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:py-12">
        <div className="w-full max-w-xl bg-white rounded-3xl shadow-xl shadow-emerald-950/5 border border-slate-200/90 p-6 sm:p-10 space-y-6 animate-fade-in">
          {/* Header & Logo */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 mx-auto rounded-3xl bg-emerald-100/80 text-emerald-800 flex items-center justify-center shadow-xs border border-emerald-200">
              {mode === 'signin' ? <LogIn className="w-7 h-7" /> : <UserPlus className="w-7 h-7" />}
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              {mode === 'signin'
                ? (language === 'ta' ? 'கணக்கில் உள்நுழைக' : 'Sign In to Your Account')
                : (language === 'ta' ? 'விவசாயியாக பதிவு செய்க' : 'Register as a Farmer')}
            </h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              {mode === 'signin'
                ? (language === 'ta'
                    ? 'உங்கள் பதிவுசெய்யப்பட்ட மொபைல் எண் மற்றும் கடவுச்சொல்லைப் பயன்படுத்தி தொடரவும்.'
                    : 'Access your personalized farm advisory, live weather, and mandi procurement slots with your mobile number and password.')
                : (language === 'ta'
                    ? 'தமிழ்நாடு உழவர் அட்டை மற்றும் கொள்முதல் முன்பதிவுகளுக்கான புதிய பதிவு.'
                    : 'Create your digital farmer profile with multi-source irrigation and 16 regional languages.')}
            </p>
          </div>

          {/* Mode Switcher Tabs: Sign In vs Register as Farmer */}
          <div className="grid grid-cols-2 p-1.5 bg-slate-100 rounded-2xl border border-slate-200 text-xs font-bold">
            <button
              type="button"
              id="switch-to-signin-tab"
              onClick={() => {
                setMode('signin');
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2.5 px-3 rounded-xl transition-all flex items-center justify-center gap-2 ${
                mode === 'signin'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LogIn className="w-4 h-4" />
              <span>{language === 'ta' ? 'உள்நுழைக' : 'Sign In'}</span>
            </button>
            <button
              type="button"
              id="switch-to-register-tab"
              onClick={() => {
                setMode('register');
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2.5 px-3 rounded-xl transition-all flex items-center justify-center gap-2 ${
                mode === 'register'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              <span>{language === 'ta' ? 'விவசாயி பதிவு' : 'Register as Farmer'}</span>
            </button>
          </div>

          {/* Alerts: Error & Success */}
          {errorMessage && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 text-xs flex items-start gap-2.5 animate-shake">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1 font-semibold">{errorMessage}</div>
            </div>
          )}

          {successMessage && (
            <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div className="flex-1 font-semibold">{successMessage}</div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 1: SIGN IN FORM */}
          {/* ========================================================================= */}
          {mode === 'signin' ? (
            <form onSubmit={handleSignIn} className="space-y-4 text-xs">
              {/* Role Selection */}
              <div>
                <label className="block font-bold text-slate-700 mb-1.5">
                  {language === 'ta' ? 'பயனர் பங்கு:' : 'Select Account Role:'}
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-50 rounded-2xl border border-slate-200">
                  <button
                    type="button"
                    onClick={() => handleSelectRole('farmer')}
                    className={`py-2 px-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                      role === 'farmer'
                        ? 'bg-white text-emerald-800 border border-emerald-300 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <UserCheck className="w-4 h-4 text-emerald-600" />
                    <span>{t.auth.farmerRole}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSelectRole('staff')}
                    className={`py-2 px-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                      role === 'staff'
                        ? 'bg-white text-purple-800 border border-purple-300 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Building2 className="w-4 h-4 text-purple-600" />
                    <span>{t.auth.staffRole}</span>
                  </button>
                </div>
              </div>

              {/* Demo Credentials Helper (Local Development Only) */}
              {import.meta.env.DEV && (
                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    LOCAL DEV FILL:
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleQuickDemo('farmer')}
                      className={`text-[11px] px-2.5 py-1 rounded-lg border font-bold transition-all ${
                        role === 'farmer'
                          ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      Farmer (Murugesan)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleQuickDemo('staff')}
                      className={`text-[11px] px-2.5 py-1 rounded-lg border font-bold transition-all ${
                        role === 'staff'
                          ? 'bg-purple-100 text-purple-900 border-purple-300'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      Staff Inspector (Ramesh)
                    </button>
                  </div>
                </div>
              )}

              {/* Mobile Number Input */}
              <div>
                <label htmlFor="login-phone" className="block font-bold text-slate-700 mb-1">
                  {language === 'ta' ? 'மொபைல் எண்:' : 'Mobile Number:'}
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    id="login-phone"
                    type="tel"
                    required
                    maxLength={10}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    placeholder="e.g. 9876543210"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-slate-900"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <label htmlFor="login-password" className="block font-bold text-slate-700 mb-1">
                  {language === 'ta' ? 'கடவுச்சொல்:' : 'Password:'}
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-slate-900"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                id="login-submit-button"
                disabled={isSubmitting}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50 mt-3"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{language === 'ta' ? 'சரிபார்க்கப்படுகிறது...' : 'Verifying Credentials...'}</span>
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    <span>
                      {language === 'ta' ? 'உள்நுழைக' : 'Sign In to Dashboard'}
                    </span>
                  </>
                )}
              </button>

              <div className="text-center pt-3 border-t border-slate-100">
                <p className="text-slate-500">
                  {language === 'ta' ? 'புதிய விவசாயியா?' : "Don't have a farmer account yet?"}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register');
                      setErrorMessage(null);
                    }}
                    className="font-bold text-emerald-700 hover:underline"
                  >
                    {language === 'ta' ? 'இப்போதே பதிவு செய்க' : 'Register as Farmer'} →
                  </button>
                </p>
              </div>
            </form>
          ) : (
            /* ========================================================================= */
            /* TAB 2: REGISTER AS FARMER FORM */
            /* ========================================================================= */
            <form onSubmit={handleRegister} className="space-y-4 text-xs">
              {/* Notice that public registration is farmer-only */}
              <div className="p-3 rounded-2xl bg-emerald-50/70 border border-emerald-200 text-emerald-900 flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  {language === 'ta'
                    ? 'பொது பதிவு விவசாயிகளுக்கானது மட்டுமே. கொள்முதல் நிலைய ஊழியர் கணக்குகள் நிர்வாகத்தால் மட்டுமே ஒதுக்கப்படும்.'
                    : 'Public registration is exclusively for farmers across all Indian States & Union Territories. Staff accounts are assigned directly by the Mandi Procurement Administration.'}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Full Name */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    {language === 'ta' ? 'விவசாயி முழுப் பெயர் *' : 'Farmer Full Name *'}
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={regName}
                      onChange={(e) => setRegName(e.target.value)}
                      placeholder="e.g. Murugesan K."
                      className="w-full pl-10 pr-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                </div>

                {/* Mobile Number */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    {language === 'ta' ? '10 இலக்க மொபைல் எண் *' : '10-Digit Mobile Number *'}
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="tel"
                      required
                      maxLength={10}
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value.replace(/\D/g, ''))}
                      placeholder="9876543210"
                      className="w-full pl-10 pr-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                </div>

                {/* Complete India-wide Location Selection */}
                <div className="sm:col-span-2">
                  <GeoLocationSelect
                    value={regLoc}
                    onChange={setRegLoc}
                    required
                    showAttribution
                  />
                </div>

                {/* Preferred Regional Language (16 Languages) */}
                <div className="sm:col-span-2">
                  <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Globe2 className="w-3.5 h-3.5 text-emerald-600" />
                      {language === 'ta' ? 'விருப்பமான பிராந்திய மொழி (22 அட்டவணை மொழிகள் + ஆங்கிலம்) *' : 'Preferred Regional Language (22 Eighth Schedule + English) *'}
                    </span>
                    {selectedLangOption && (
                      <span className="text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        {selectedLangOption.tier === 'full' ? 'Full UI (100%)' : selectedLangOption.tier === 'core' ? `Core UI (${selectedLangOption.coveragePercent}%)` : `Essential (${selectedLangOption.coveragePercent}%)`}
                        {selectedLangOption.direction === 'rtl' ? ' • RTL' : ''}
                      </span>
                    )}
                  </label>
                  <select
                    id="preferred-language-select"
                    value={regPrefLang}
                    onChange={(e) => setRegPrefLang(e.target.value as Language)}
                    className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  >
                    {REGIONAL_LANGUAGE_OPTIONS.map((opt) => (
                      <option key={opt.code} value={opt.code}>
                        {opt.nativeName} — {opt.name} {opt.direction === 'rtl' ? '(RTL)' : ''} ({opt.tier === 'full' ? 'Full UI' : opt.tier === 'core' ? `Core UI ${opt.coveragePercent}%` : `Essential ${opt.coveragePercent}%`})
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-slate-500 mt-1">
                    AgriBharat AI assistant, weather alerts, and application screens will personalize to your selected language.
                  </p>
                </div>

                {/* Password with toggle */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    {language === 'ta' ? 'கடவுச்சொல் (குறைந்தது 6) *' : 'Password (min 6 characters) *'}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      minLength={6}
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-10 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      className="absolute right-3.5 top-2 text-slate-400 hover:text-slate-600"
                    >
                      {showRegPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    {language === 'ta' ? 'கடவுச்சொல்லை உறுதிப்படுத்துக *' : 'Confirm Password *'}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      minLength={6}
                      value={regConfirmPassword}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                </div>
              </div>

              {/* Phase 19: Farm Profile Inputs (Integer Acres & Multi-select Irrigation) */}
              <div className="pt-3 border-t border-slate-100 space-y-3">
                <p className="text-[11px] font-bold text-slate-700">
                  {language === 'ta' ? 'விவசாய விவரங்கள் (உழவர் அட்டை விவரங்கள்):' : 'Farm Profile Details:'}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Total Land Acres (STRICT WHOLE NUMBER) */}
                  <div>
                    <label htmlFor="reg-land-acres" className="block text-[11px] font-bold text-slate-700 mb-1">
                      {language === 'ta' ? 'நிலப்பரப்பு (முழு ஏக்கர்) *' : 'Total Land (Whole Acres) *'}
                    </label>
                    <input
                      id="reg-land-acres"
                      type="number"
                      step="1"
                      min="1"
                      required
                      value={regLandAcres}
                      onChange={(e) => setRegLandAcres(e.target.value)}
                      placeholder="e.g. 3"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500/20"
                    />
                    <p className="text-[9px] text-slate-500 mt-0.5">Whole numbers only (e.g. 1, 3, 5)</p>
                  </div>

                  {/* Primary Crop */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">
                      {language === 'ta' ? 'முக்கிய பயிர் *' : 'Primary Crop *'}
                    </label>
                    <input
                      type="text"
                      required
                      value={regPrimaryCrop}
                      onChange={(e) => setRegPrimaryCrop(e.target.value)}
                      placeholder="e.g. Samba Paddy"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-emerald-500/20"
                    />
                  </div>

                  {/* Soil Type */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">
                      {language === 'ta' ? 'மண் வகை' : 'Soil Type'}
                    </label>
                    <input
                      type="text"
                      value={regSoilType}
                      onChange={(e) => setRegSoilType(e.target.value)}
                      placeholder="e.g. Alluvial Clay Loam"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-emerald-500/20"
                    />
                  </div>
                </div>

                {/* Irrigation Source Checkbox Group (14 Options) */}
                <div className="space-y-2 p-3 bg-slate-50 rounded-2xl border border-slate-200">
                  <div className="flex items-center justify-between">
                    <label className="block text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                      <Droplets className="w-3.5 h-3.5 text-blue-600" />
                      <span>{language === 'ta' ? 'பாசன ஆதாரங்கள் (பல தெரிவுகள் அனுமதிக்கப்படும்) *' : 'Irrigation Sources (Multiple Selections Allowed) *'}</span>
                    </label>
                    <span className="text-[10px] text-slate-500 font-semibold">
                      {regIrrigationSources.length} selected
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 max-h-48 overflow-y-auto pr-1">
                    {IRRIGATION_OPTIONS.map((opt) => {
                      const isChecked = regIrrigationSources.includes(opt);
                      return (
                        <label
                          key={opt}
                          className={`flex items-center gap-2 p-2 rounded-xl border text-xs cursor-pointer transition-all ${
                            isChecked
                              ? 'bg-blue-50/70 border-blue-300 text-blue-900 font-bold'
                              : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleIrrigation(opt)}
                            className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 border-slate-300"
                          />
                          <span className="select-none">{opt}</span>
                        </label>
                      );
                    })}
                  </div>

                  {/* Conditional "Other" text input */}
                  {regIrrigationSources.includes('Other') && (
                    <div className="pt-2 animate-fade-in">
                      <label className="block text-[10px] font-bold text-blue-900 mb-1">
                        Specify Custom Irrigation Source *:
                      </label>
                      <input
                        type="text"
                        required
                        value={regOtherIrrigationDetail}
                        onChange={(e) => setRegOtherIrrigationDetail(e.target.value)}
                        placeholder="e.g. Solar Lift Pump from Vennar River"
                        className="w-full px-3 py-1.5 bg-white border border-blue-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-blue-500/20"
                      />
                    </div>
                  )}
                </div>

                {/* Account Security & Phone Ownership Disclosure */}
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-emerald-600 text-white flex items-center justify-center">
                      <Lock className="w-3.5 h-3.5" />
                    </div>
                    <span className="font-bold text-slate-800 text-xs">
                      {language === 'ta' ? 'கடவுச்சொல் பாதுகாப்பு மற்றும் சரிபார்ப்பு அறிவிப்பு' : 'Account Security & Phone Ownership Notice'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    {language === 'ta'
                      ? 'உங்கள் விவசாயி கணக்கு நீங்கள் தேர்ந்தெடுத்த கடவுச்சொல்லால் பாதுகாக்கப்படுகிறது. SMS சரிபார்ப்பு சேவை செயலில் இல்லை என்பதால் மொபைல் எண் சரிபார்க்கப்படாத நிலையில் உள்ளது.'
                      : 'Your farmer profile is secured by your chosen password. Phone ownership is not verified as no SMS provider is currently active.'}
                  </p>
                </div>
              </div>

              {/* Submit Registration */}
              <button
                type="submit"
                id="register-submit-button"
                disabled={isSubmitting}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50 mt-3"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{language === 'ta' ? 'பதிவு செய்யப்படுகிறது...' : 'Registering Account...'}</span>
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    <span>{language === 'ta' ? 'விவசாயி கணக்கை பதிவு செய்க' : 'Register & Enter Dashboard'}</span>
                  </>
                )}
              </button>

              <div className="text-center pt-3 border-t border-slate-100">
                <p className="text-slate-500">
                  {language === 'ta' ? 'ஏற்கனவே கணக்கு உள்ளதா?' : 'Already have an account?'}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('signin');
                      setErrorMessage(null);
                    }}
                    className="font-bold text-emerald-700 hover:underline"
                  >
                    {language === 'ta' ? 'உள்நுழைக' : 'Sign In here'} →
                  </button>
                </p>
              </div>
            </form>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 text-center text-xs text-slate-400 border-t border-slate-200/60 bg-white/60">
        <p>AgriBharat • Secure Authentication & Role Isolation • Smart Farming Intelligence & Agricultural Marketplace</p>
      </footer>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  User,
  Phone,
  FileText,
  ShieldCheck,
  Plus,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Database,
  Globe2,
  Droplets,
  Send,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import type { FarmerProfile, Language } from '../../types';
import {
  getFarmers,
  createFarmer,
  updateFarmerProfileApi,
  type FarmerProfileEntity,
  type FarmerProfileInput,
} from '../../services/api';
import { REGIONAL_LANGUAGE_OPTIONS, IRRIGATION_OPTIONS } from '../../i18n/translations';

interface ProfileViewProps {
  farmer: FarmerProfile;
  onFarmerUpdated?: (updated: FarmerProfile) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ farmer, onFarmerUpdated }) => {
  const { t, language, setLanguage } = useLanguage();
  const [activeFarmer, setActiveFarmer] = useState<FarmerProfile>(farmer);
  const [dbFarmers, setDbFarmers] = useState<FarmerProfileEntity[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { user, token, updateUser } = useAuth();
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form state initialized from authenticated user
  const [formData, setFormData] = useState<FarmerProfileInput>({
    name: user?.fullName || user?.name || farmer.name || '',
    phone: user?.phone || farmer.phone || '',
    location: user?.village ? `${user.village}, ${user.district || 'Tamil Nadu'}` : farmer.location,
    district: user?.district || farmer.district || 'Thanjavur',
    state: user?.state || farmer.state || 'Tamil Nadu',
    totalLandAcres: typeof user?.totalLandAcres === 'number' ? Math.round(user.totalLandAcres) : (farmer.totalLandAcres ? Math.round(farmer.totalLandAcres) : 2),
    primaryCrop: user?.primaryCrop || farmer.primaryCrop || 'Paddy (Samba)',
    soilType: user?.soilType || farmer.soilType || 'Alluvial Clay Loam',
    irrigationSource: user?.irrigationSource || farmer.irrigationSource || 'Borewell / Tube Well',
    irrigationSources: user?.irrigationSources || (farmer.irrigationSources && farmer.irrigationSources.length > 0 ? farmer.irrigationSources : ['Borewell / Tube Well']),
    otherIrrigationDetail: user?.otherIrrigationDetail || '',
    preferredLanguage: user?.preferredLanguage || language,
    aadhaarMasked: user?.aadhaarMasked || farmer.aadhaarMasked || undefined,
  });

  const [selectedIrrigationSources, setSelectedIrrigationSources] = useState<string[]>(() => {
    if (user?.irrigationSources && user.irrigationSources.length > 0) return user.irrigationSources;
    if (farmer.irrigationSources && farmer.irrigationSources.length > 0) return farmer.irrigationSources;
    return ['Borewell / Tube Well'];
  });

  const [otherIrrigationDetail, setOtherIrrigationDetail] = useState(user?.otherIrrigationDetail || '');
  const [landAcresInput, setLandAcresInput] = useState<string>(() => {
    const val = user?.totalLandAcres ?? farmer.totalLandAcres ?? 3;
    return String(Math.round(Number(val)) || 3);
  });
  const [preferredLang, setPreferredLang] = useState<string>(user?.preferredLanguage || language);

  // Sync active farmer when user changes
  useEffect(() => {
    if (user) {
      const updated: FarmerProfile = {
        name: user.fullName || user.name,
        phone: user.phone,
        location: user.village ? `${user.village}, ${user.district || 'Tamil Nadu'}` : (user.district || 'Tamil Nadu'),
        district: user.district || 'Thanjavur',
        state: user.state || 'Tamil Nadu',
        totalLandAcres: user.totalLandAcres || farmer.totalLandAcres,
        primaryCrop: user.primaryCrop || farmer.primaryCrop,
        soilType: user.soilType || farmer.soilType,
        irrigationSource: user.irrigationSource || farmer.irrigationSource,
        irrigationSources: user.irrigationSources || farmer.irrigationSources,
        preferredLanguage: (user.preferredLanguage as Language) || undefined,
        telegramLinked: user.telegramLinked,
        telegramUsername: user.telegramUsername,
        aadhaarMasked: user.aadhaarMasked,
        farmerId: user.farmerId || farmer.farmerId,
        isFromDb: true,
      };
      setActiveFarmer(updated);
      setFormData((prev) => ({
        ...prev,
        name: updated.name,
        phone: updated.phone,
        location: updated.location,
        district: updated.district,
        totalLandAcres: Math.round(Number(updated.totalLandAcres)) || 2,
        primaryCrop: updated.primaryCrop || 'Paddy (Samba)',
        soilType: updated.soilType || 'Alluvial Clay Loam',
        irrigationSource: updated.irrigationSource || 'Borewell / Tube Well',
        irrigationSources: updated.irrigationSources || ['Borewell / Tube Well'],
        preferredLanguage: updated.preferredLanguage || language,
      }));
      if (updated.irrigationSources && updated.irrigationSources.length > 0) {
        setSelectedIrrigationSources(updated.irrigationSources);
      }
      if (updated.totalLandAcres) {
        setLandAcresInput(String(Math.round(Number(updated.totalLandAcres))));
      }
      if (updated.preferredLanguage) {
        setPreferredLang(updated.preferredLanguage);
      }
    }
  }, [user]);

  // Fetch farmers list for directory
  const loadDbFarmers = async () => {
    setIsLoadingList(true);
    try {
      const records = await getFarmers();
      setDbFarmers(records);
    } catch {
      // Backend not running or DB empty - graceful
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    loadDbFarmers();
  }, []);

  const handleToggleIrrigation = (source: string) => {
    setSelectedIrrigationSources((prev) => {
      if (prev.includes(source)) {
        const next = prev.filter((s) => s !== source);
        return next.length > 0 ? next : [source];
      } else {
        return [...prev, source];
      }
    });
  };

  const handleRegisterOrUpdateFarmer = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);

    // Validate whole number integer acres
    const acresStr = landAcresInput.trim();
    if (!acresStr || !/^\d+$/.test(acresStr)) {
      setStatusMessage({
        type: 'error',
        text: 'Total cultivable land area must be a positive whole integer (e.g. 1, 2, 5). Decimals are not permitted.',
      });
      setIsSubmitting(false);
      return;
    }
    const acresNum = parseInt(acresStr, 10);
    if (acresNum <= 0) {
      setStatusMessage({
        type: 'error',
        text: 'Land area must be at least 1 acre.',
      });
      setIsSubmitting(false);
      return;
    }

    if (selectedIrrigationSources.length === 0) {
      setStatusMessage({
        type: 'error',
        text: 'Please select at least one irrigation source.',
      });
      setIsSubmitting(false);
      return;
    }

    if (selectedIrrigationSources.includes('Other') && !otherIrrigationDetail.trim()) {
      setStatusMessage({
        type: 'error',
        text: 'Please specify the custom irrigation source detail for "Other".',
      });
      setIsSubmitting(false);
      return;
    }

    const payload: FarmerProfileInput = {
      ...formData,
      totalLandAcres: acresNum,
      irrigationSources: selectedIrrigationSources,
      irrigationSource: selectedIrrigationSources.join(', '),
      otherIrrigationDetail: selectedIrrigationSources.includes('Other') ? otherIrrigationDetail.trim() : undefined,
      preferredLanguage: preferredLang,
    };

    try {
      if (token) {
        // Authenticated farmer updating their profile via PUT /api/farmers/me
        const updatedUser = await updateFarmerProfileApi(payload, token);
        updateUser(updatedUser);

        if (payload.preferredLanguage && payload.preferredLanguage !== language) {
          setLanguage(payload.preferredLanguage as Language);
        }

        const profileMapped: FarmerProfile = {
          name: updatedUser.name || updatedUser.fullName || payload.name,
          phone: updatedUser.phone || payload.phone,
          location: updatedUser.village ? `${updatedUser.village}, ${updatedUser.district || 'Tamil Nadu'}` : payload.location,
          district: updatedUser.district || payload.district || 'Thanjavur',
          state: updatedUser.state || 'Tamil Nadu',
          totalLandAcres: updatedUser.totalLandAcres || acresNum,
          primaryCrop: updatedUser.primaryCrop || payload.primaryCrop,
          soilType: updatedUser.soilType || payload.soilType,
          irrigationSource: updatedUser.irrigationSource || payload.irrigationSource,
          irrigationSources: updatedUser.irrigationSources || selectedIrrigationSources,
          preferredLanguage: (updatedUser.preferredLanguage as Language) || (preferredLang as Language),
          telegramLinked: updatedUser.telegramLinked,
          telegramUsername: updatedUser.telegramUsername,
          aadhaarMasked: updatedUser.aadhaarMasked || payload.aadhaarMasked,
          farmerId: updatedUser.farmerId || activeFarmer.farmerId,
          isFromDb: true,
        };

        setActiveFarmer(profileMapped);
        if (onFarmerUpdated) {
          onFarmerUpdated(profileMapped);
        }

        setStatusMessage({
          type: 'success',
          text: 'Farm profile, multi-select irrigation sources, and language preference updated successfully in MongoDB!',
        });
      } else {
        // Fallback: create new record
        const created = await createFarmer(payload, token);
        setStatusMessage({
          type: 'success',
          text: `Farmer profile registered successfully! Assigned ID: ${created.farmerId}`,
        });
        const profileMapped: FarmerProfile = {
          name: created.name,
          phone: created.phone,
          location: created.location,
          district: created.district || payload.district || 'Thanjavur',
          state: created.state || 'Tamil Nadu',
          totalLandAcres: created.totalLandAcres,
          primaryCrop: created.primaryCrop,
          soilType: created.soilType || 'Alluvial Clay Loam',
          irrigationSource: created.irrigationSource || 'Borewell / Tube Well',
          irrigationSources: created.irrigationSources || selectedIrrigationSources,
          preferredLanguage: (created.preferredLanguage as Language) || (preferredLang as Language),
          aadhaarMasked: created.aadhaarMasked,
          farmerId: created.farmerId,
          isFromDb: true,
        };
        setActiveFarmer(profileMapped);
        if (onFarmerUpdated) onFarmerUpdated(profileMapped);
      }

      setIsModalOpen(false);
      await loadDbFarmers();
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Failed to save farmer profile to backend MongoDB.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentLangObj = REGIONAL_LANGUAGE_OPTIONS.find(
    (l) => l.code === (activeFarmer.preferredLanguage || language)
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Status Alert Banner */}
      {statusMessage && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 transition-all ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-rose-50 border-rose-300 text-rose-900'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div className="text-xs sm:text-sm font-medium flex-1">
            {statusMessage.text}
          </div>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-xs font-bold opacity-60 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Profile Card */}
      <Card
        title={t.nav.profile}
        subtitle="Uzhavar e-Identity & Land Revenue Record (தமிழ்நாடு உழவர் அட்டை)"
        icon={<User className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <div className="flex items-center gap-2">
            {activeFarmer.isFromDb ? (
              <Badge variant="emerald" dot>
                Verified Profile
              </Badge>
            ) : null}
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Update Farm Details
            </button>
          </div>
        }
      >
        <div className="space-y-6">
          {/* Identity Header */}
          <div className="flex flex-col sm:flex-row items-center gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-16 h-16 rounded-full bg-emerald-700 text-white flex items-center justify-center font-extrabold text-xl shadow-md">
              {activeFarmer.name.substring(0, 2).toUpperCase()}
            </div>
            <div className="text-center sm:text-left flex-1">
              <h3 className="text-lg font-bold text-slate-900">{activeFarmer.name}</h3>
              <p className="text-xs font-mono text-emerald-800 font-bold">{activeFarmer.farmerId}</p>
              <p className="text-xs text-slate-500 mt-0.5">{activeFarmer.location}</p>
            </div>
            <div className="flex flex-col sm:items-end gap-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-100/70 px-3 py-1.5 rounded-full">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                e-KYC Completed
              </div>
              {activeFarmer.telegramLinked ? (
                <div className="flex items-center gap-1 text-[11px] font-semibold text-sky-800 bg-sky-100 px-2.5 py-1 rounded-full border border-sky-200">
                  <Send className="w-3 h-3 text-sky-600" />
                  <span>Telegram Linked: @{activeFarmer.telegramUsername || 'Verified'}</span>
                </div>
              ) : (
                <div className="text-[10px] text-slate-500">
                  Telegram OTP Login Available
                </div>
              )}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-100 bg-white space-y-2.5">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-600" />
                Land Revenue Records (Patta / Chitta)
              </h4>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Patta Number:</span>
                <span className="font-semibold text-slate-800">Patta #1294 (Kabisthalam)</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Total Cultivable Area:</span>
                <span className="font-bold text-emerald-800">{activeFarmer.totalLandAcres} Whole Acres</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Primary Crop:</span>
                <span className="font-semibold text-slate-800">{activeFarmer.primaryCrop}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Soil Type:</span>
                <span className="font-semibold text-slate-800">{activeFarmer.soilType}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Regional Language:</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1">
                  <Globe2 className="w-3.5 h-3.5" />
                  {currentLangObj ? `${currentLangObj.name} (${currentLangObj.nativeName})` : activeFarmer.preferredLanguage || 'English'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block mb-1.5">Irrigation Sources:</span>
                <div className="flex flex-wrap gap-1">
                  {activeFarmer.irrigationSources && activeFarmer.irrigationSources.length > 0 ? (
                    activeFarmer.irrigationSources.map((src, i) => (
                      <span
                        key={i}
                        className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200"
                      >
                        {src}
                      </span>
                    ))
                  ) : (
                    <span className="font-semibold text-slate-800">{activeFarmer.irrigationSource}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-100 bg-white space-y-2.5">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-blue-600" />
                Contact & Banking Direct Transfer (DBT)
              </h4>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Linked Mobile:</span>
                <span className="font-semibold text-slate-800 font-mono">{activeFarmer.phone}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Aadhaar (Masked):</span>
                <span className="font-semibold text-slate-800 font-mono">{activeFarmer.aadhaarMasked || '•••• •••• 9182'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">DBT Bank Account:</span>
                <span className="font-semibold text-slate-800 font-mono">Canara Bank (*****3198)</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">IFSC Code:</span>
                <span className="font-semibold text-slate-800 font-mono">CNRB0001042</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Telegram Status:</span>
                <span className="font-semibold text-sky-800">
                  {activeFarmer.telegramLinked ? `Linked (@${activeFarmer.telegramUsername || 'Verified'})` : 'Not Linked'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* MongoDB Farmer Records Directory */}
      <Card
        title="MongoDB Registered Farmer Directory"
        subtitle="Live records retrieved directly from MongoDB 'farmers' collection"
        icon={<Database className="w-5 h-5 text-emerald-600" />}
        headerAction={
          <button
            onClick={loadDbFarmers}
            className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold inline-flex items-center gap-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingList ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      >
        {dbFarmers.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500">
            No farmer records stored in MongoDB yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold">
                  <th className="py-2.5 px-3">Farmer ID</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Location</th>
                  <th className="py-2.5 px-3">Land Size</th>
                  <th className="py-2.5 px-3">Primary Crop</th>
                  <th className="py-2.5 px-3">Language</th>
                  <th className="py-2.5 px-3">Irrigation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dbFarmers.map((f) => (
                  <tr key={f.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-700">{f.farmerId}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-800">{f.name}</td>
                    <td className="py-2.5 px-3 text-slate-600">{f.location}</td>
                    <td className="py-2.5 px-3 font-bold text-slate-900">{f.totalLandAcres} Acres</td>
                    <td className="py-2.5 px-3 text-slate-700">{f.primaryCrop}</td>
                    <td className="py-2.5 px-3 text-slate-600 uppercase font-semibold">{f.preferredLanguage || 'ta'}</td>
                    <td className="py-2.5 px-3 text-slate-600 truncate max-w-xs">{f.irrigationSource}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal Dialog for Farmer Profile Update */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              ✕
            </button>

            <div className="flex items-center gap-3 mb-5 border-b border-slate-100 pb-3">
              <div className="p-2.5 rounded-2xl bg-emerald-100 text-emerald-800">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900">
                  Update Farm Profile & Preferences
                </h4>
                <p className="text-xs text-slate-500">
                  Persists changes to MongoDB with server-side whole-integer land validation
                </p>
              </div>
            </div>

            <form onSubmit={handleRegisterOrUpdateFarmer} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Farmer Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Phone Number *</label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>
                {/* Total Land Area: Positive Whole Number Integer */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Land Holding (Whole Acres Only) *
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    value={landAcresInput}
                    onChange={(e) => setLandAcresInput(e.target.value)}
                    placeholder="e.g. 5"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <p className="text-[10px] text-slate-500 mt-0.5">Whole integers only (e.g., 1, 3, 8)</p>
                </div>
              </div>

              {/* Preferred Regional Language */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Globe2 className="w-3.5 h-3.5 text-emerald-600" />
                    Preferred Regional Language (16 Languages) *
                  </span>
                </label>
                <select
                  value={preferredLang}
                  onChange={(e) => setPreferredLang(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                >
                  {REGIONAL_LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.code} value={opt.code}>
                      {opt.name} ({opt.nativeName}) {opt.isFullyTranslated ? '• Full UI' : '• AI & Voice'}
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  AI assistant responses, weather advisory, and voice recognition will converse in this dialect.
                </p>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Village & Block / Location *</label>
                <input
                  type="text"
                  required
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Primary Crop *</label>
                  <input
                    type="text"
                    required
                    value={formData.primaryCrop}
                    onChange={(e) => setFormData({ ...formData, primaryCrop: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Soil Type</label>
                  <input
                    type="text"
                    value={formData.soilType}
                    onChange={(e) => setFormData({ ...formData, soilType: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Multi-Select Irrigation Checkboxes */}
              <div className="space-y-2 p-3 bg-slate-50 rounded-2xl border border-slate-200">
                <div className="flex items-center justify-between">
                  <label className="block text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Droplets className="w-3.5 h-3.5 text-blue-600" />
                    <span>Irrigation Sources (Check all that apply) *</span>
                  </label>
                  <span className="text-[10px] text-slate-500 font-semibold">
                    {selectedIrrigationSources.length} selected
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-40 overflow-y-auto pr-1">
                  {IRRIGATION_OPTIONS.map((opt) => {
                    const isChecked = selectedIrrigationSources.includes(opt);
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

                {selectedIrrigationSources.includes('Other') && (
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

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-sm transition-all inline-flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving to MongoDB...
                    </>
                  ) : (
                    'Save to MongoDB'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

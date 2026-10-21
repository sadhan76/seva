import React, { useState, useEffect, useRef } from 'react';
import {
  User,
  Phone,
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Database,
  Globe2,
  Droplets,
  Lock,
  Camera,
  Trash2,
  Edit3,
  MapPin,
  Info,
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
  uploadProfilePhotoApi,
  type FarmerProfileEntity,
  type FarmerProfileInput,
} from '../../services/api';
import { REGIONAL_LANGUAGE_OPTIONS, IRRIGATION_OPTIONS } from '../../i18n/translations';
import { GeoLocationSelect, type GeoLocationValue } from '../common/GeoLocationSelect';

interface ProfileViewProps {
  farmer: FarmerProfile;
  onFarmerUpdated?: (updated: FarmerProfile) => void;
}

const COMMON_CROPS = [
  'Paddy (Samba)',
  'Paddy (Kuruvai)',
  'Paddy (Thaladi)',
  'Wheat',
  'Sugarcane',
  'Cotton',
  'Maize',
  'Groundnut',
  'Banana',
  'Turmeric',
  'Millets',
  'Black Gram / Urad',
];

const COMMON_SOILS = [
  'Alluvial Clay Loam',
  'Black Cotton Soil',
  'Red Sandy Loam',
  'Laterite Soil',
  'Clay Loam',
  'Coastal Sandy Soil',
  'Saline / Alkaline Soil',
];

const LAND_UNITS = ['Acres', 'Hectares', 'Cents', 'Bigha', 'Guntha'];

export const ProfileView: React.FC<ProfileViewProps> = ({ farmer, onFarmerUpdated }) => {
  const { t, language, setLanguage } = useLanguage();
  const { user, token, updateUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeFarmer, setActiveFarmer] = useState<FarmerProfile>(farmer);
  const [dbFarmers, setDbFarmers] = useState<FarmerProfileEntity[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form Fields - Loaded strictly from authenticated user / active farmer
  const [name, setName] = useState(user?.fullName || user?.name || farmer.name || '');
  const [phone, setPhone] = useState(user?.phone || farmer.phone || '');
  const [profilePhoto, setProfilePhoto] = useState<string | null>(user?.profilePhoto || farmer.profilePhoto || null);
  const [landAcresInput, setLandAcresInput] = useState<string>(() => {
    const val = user?.totalLandAcres ?? farmer.totalLandAcres ?? 3;
    return String(Math.round(Number(val)) || 3);
  });
  const [landUnit, setLandUnit] = useState<string>(user?.landUnit || farmer.landUnit || 'Acres');
  const [primaryCrop, setPrimaryCrop] = useState(user?.primaryCrop || farmer.primaryCrop || 'Paddy (Samba)');
  const [soilType, setSoilType] = useState(user?.soilType || farmer.soilType || 'Alluvial Clay Loam');
  const [preferredLang, setPreferredLang] = useState<string>(user?.preferredLanguage || farmer.preferredLanguage || language);

  const [profileGeoLoc, setProfileGeoLoc] = useState<GeoLocationValue>({
    country: user?.country || farmer.country || 'India',
    state: user?.state || farmer.state || 'Tamil Nadu',
    stateCode: user?.stateCode || farmer.stateCode || 'IN-TN',
    district: user?.district || farmer.district || 'Thanjavur',
    districtCode: user?.districtCode || farmer.districtCode || 'IN-TN-THAN',
    village: user?.village || farmer.location || 'Kabisthalam',
    taluk: user?.taluk || farmer.taluk || 'Papanasam',
  });

  const [selectedIrrigationSources, setSelectedIrrigationSources] = useState<string[]>(() => {
    if (user?.irrigationSources && user.irrigationSources.length > 0) return user.irrigationSources;
    if (farmer.irrigationSources && farmer.irrigationSources.length > 0) return farmer.irrigationSources;
    return ['Borewell / Tube Well'];
  });
  const [otherIrrigationDetail, setOtherIrrigationDetail] = useState(user?.otherIrrigationDetail || '');

  // Reset all edit fields back to saved user state
  const resetFormToSaved = () => {
    const targetUser = user;
    setName(targetUser?.fullName || targetUser?.name || farmer.name || '');
    setPhone(targetUser?.phone || farmer.phone || '');
    setProfilePhoto(targetUser?.profilePhoto || farmer.profilePhoto || null);
    setLandAcresInput(String(Math.round(Number(targetUser?.totalLandAcres ?? farmer.totalLandAcres ?? 3)) || 3));
    setLandUnit(targetUser?.landUnit || farmer.landUnit || 'Acres');
    setPrimaryCrop(targetUser?.primaryCrop || farmer.primaryCrop || 'Paddy (Samba)');
    setSoilType(targetUser?.soilType || farmer.soilType || 'Alluvial Clay Loam');
    setPreferredLang(targetUser?.preferredLanguage || farmer.preferredLanguage || language);

    setProfileGeoLoc({
      country: targetUser?.country || farmer.country || 'India',
      state: targetUser?.state || farmer.state || 'Tamil Nadu',
      stateCode: targetUser?.stateCode || farmer.stateCode || 'IN-TN',
      district: targetUser?.district || farmer.district || 'Thanjavur',
      districtCode: targetUser?.districtCode || farmer.districtCode || 'IN-TN-THAN',
      village: targetUser?.village || farmer.location || '',
      taluk: targetUser?.taluk || farmer.taluk || '',
    });

    if (targetUser?.irrigationSources && targetUser.irrigationSources.length > 0) {
      setSelectedIrrigationSources(targetUser.irrigationSources);
    } else if (farmer.irrigationSources && farmer.irrigationSources.length > 0) {
      setSelectedIrrigationSources(farmer.irrigationSources);
    } else {
      setSelectedIrrigationSources(['Borewell / Tube Well']);
    }
    setOtherIrrigationDetail(targetUser?.otherIrrigationDetail || '');
  };

  // Sync activeFarmer when user updates
  useEffect(() => {
    if (user) {
      const updated: FarmerProfile = {
        name: user.fullName || user.name,
        phone: user.phone,
        location: user.village ? `${user.village}, ${user.district || ''}` : (user.district || ''),
        village: user.village,
        country: user.country || farmer.country || 'India',
        district: user.district || farmer.district || '',
        districtCode: user.districtCode || farmer.districtCode,
        state: user.state || farmer.state || '',
        stateCode: user.stateCode || farmer.stateCode,
        taluk: user.taluk || farmer.taluk,
        totalLandAcres: user.totalLandAcres || farmer.totalLandAcres,
        landUnit: user.landUnit || farmer.landUnit || 'Acres',
        primaryCrop: user.primaryCrop || farmer.primaryCrop,
        soilType: user.soilType || farmer.soilType,
        irrigationSource: user.irrigationSource || farmer.irrigationSource,
        irrigationSources: user.irrigationSources || farmer.irrigationSources,
        preferredLanguage: (user.preferredLanguage as Language) || undefined,
        profilePhoto: user.profilePhoto || farmer.profilePhoto,
        telegramLinked: user.telegramLinked,
        telegramUsername: user.telegramUsername,
        aadhaarMasked: user.aadhaarMasked,
        farmerId: user.farmerId || farmer.farmerId,
        isPhoneVerified: user.isPhoneVerified,
        isFromDb: true,
      };
      setActiveFarmer(updated);
      resetFormToSaved();
    }
  }, [user]);

  // Fetch farmers directory
  const loadDbFarmers = async () => {
    setIsLoadingList(true);
    try {
      const records = await getFarmers();
      setDbFarmers(records);
    } catch {
      // Graceful fallback
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

  // Safe file upload handler
  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.match(/^image\/(jpeg|png|webp)$/)) {
      setStatusMessage({
        type: 'error',
        text: 'Unsupported image format. Please select a valid JPG, PNG, or WEBP photo.',
      });
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setStatusMessage({
        type: 'error',
        text: 'Image exceeds 2MB limit. Please upload a smaller photo.',
      });
      return;
    }

    setIsUploadingPhoto(true);
    try {
      if (token) {
        const uploadRes = await uploadProfilePhotoApi(file, token);
        setProfilePhoto(uploadRes.profilePhoto);
        setStatusMessage({
          type: 'success',
          text: 'Profile photo updated successfully!',
        });
      } else {
        // Local preview via FileReader
        const reader = new FileReader();
        reader.onload = (uploadEvent) => {
          setProfilePhoto(uploadEvent.target?.result as string);
        };
        reader.readAsDataURL(file);
      }
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Failed to upload photo.',
      });
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  const handleRemovePhoto = () => {
    setProfilePhoto(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);

    // 1. Validate full name
    const cleanName = name.trim();
    if (cleanName.length < 2) {
      setStatusMessage({
        type: 'error',
        text: 'Farmer full name must be at least 2 characters long.',
      });
      setIsSubmitting(false);
      return;
    }

    // 2. Validate mobile number (10 digits starting with 6-9)
    const cleanPhone = phone.replace(/[^\d]/g, '');
    const normalizedPhone = cleanPhone.length === 12 && cleanPhone.startsWith('91') ? cleanPhone.slice(2) : cleanPhone;
    if (!/^[6-9]\d{9}$/.test(normalizedPhone)) {
      setStatusMessage({
        type: 'error',
        text: 'Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.',
      });
      setIsSubmitting(false);
      return;
    }

    // 3. Validate land holding (positive whole integer)
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
        text: 'Land holding must be at least 1.',
      });
      setIsSubmitting(false);
      return;
    }

    // 4. Validate irrigation sources
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

    // 5. Validate geographic location
    if (!profileGeoLoc.state || !profileGeoLoc.district) {
      setStatusMessage({
        type: 'error',
        text: 'Please select a valid State / UT and District from the official directory.',
      });
      setIsSubmitting(false);
      return;
    }

    const payload: FarmerProfileInput = {
      name: cleanName,
      phone: normalizedPhone,
      country: profileGeoLoc.country || 'India',
      state: profileGeoLoc.state,
      stateCode: profileGeoLoc.stateCode,
      district: profileGeoLoc.district,
      districtCode: profileGeoLoc.districtCode,
      taluk: profileGeoLoc.taluk,
      village: profileGeoLoc.village,
      location: profileGeoLoc.village ? `${profileGeoLoc.village}, ${profileGeoLoc.district}` : profileGeoLoc.district,
      totalLandAcres: acresNum,
      landUnit: landUnit || 'Acres',
      primaryCrop: primaryCrop.trim() || 'Paddy (Samba)',
      soilType: soilType.trim() || 'Alluvial Clay Loam',
      irrigationSources: selectedIrrigationSources,
      irrigationSource: selectedIrrigationSources.join(', '),
      otherIrrigationDetail: selectedIrrigationSources.includes('Other') ? otherIrrigationDetail.trim() : undefined,
      preferredLanguage: preferredLang,
      profilePhoto: profilePhoto || undefined,
    };

    try {
      if (token) {
        // Authenticated farmer updating their profile via PUT /api/farmers/me
        const updatedUser = await updateFarmerProfileApi(payload, token);
        updateUser(updatedUser);

        // Immediate application-wide language switch
        if (payload.preferredLanguage && payload.preferredLanguage !== language) {
          setLanguage(payload.preferredLanguage as Language);
        }

        const profileMapped: FarmerProfile = {
          name: updatedUser.name || updatedUser.fullName || payload.name,
          phone: updatedUser.phone || payload.phone,
          location: updatedUser.village ? `${updatedUser.village}, ${updatedUser.district || ''}` : payload.location,
          village: updatedUser.village || payload.village,
          country: updatedUser.country || payload.country || 'India',
          district: updatedUser.district || payload.district || '',
          districtCode: updatedUser.districtCode || payload.districtCode,
          state: updatedUser.state || payload.state || '',
          stateCode: updatedUser.stateCode || payload.stateCode,
          taluk: updatedUser.taluk || payload.taluk,
          totalLandAcres: updatedUser.totalLandAcres || acresNum,
          landUnit: updatedUser.landUnit || payload.landUnit || 'Acres',
          primaryCrop: updatedUser.primaryCrop || payload.primaryCrop,
          soilType: updatedUser.soilType || payload.soilType,
          irrigationSource: updatedUser.irrigationSource || payload.irrigationSource,
          irrigationSources: updatedUser.irrigationSources || selectedIrrigationSources,
          preferredLanguage: (updatedUser.preferredLanguage as Language) || (preferredLang as Language),
          profilePhoto: updatedUser.profilePhoto || profilePhoto || undefined,
          telegramLinked: updatedUser.telegramLinked,
          telegramUsername: updatedUser.telegramUsername,
          aadhaarMasked: updatedUser.aadhaarMasked || activeFarmer.aadhaarMasked,
          farmerId: updatedUser.farmerId || activeFarmer.farmerId,
          isPhoneVerified: updatedUser.isPhoneVerified,
          isFromDb: true,
        };

        setActiveFarmer(profileMapped);
        if (onFarmerUpdated) {
          onFarmerUpdated(profileMapped);
        }

        setStatusMessage({
          type: 'success',
          text: 'Farmer profile and regional preferences updated successfully in MongoDB!',
        });
      } else {
        // Unauthenticated demo fallback: create new record
        const created = await createFarmer(payload, token);
        setStatusMessage({
          type: 'success',
          text: `Farmer profile created successfully! Assigned ID: ${created.farmerId}`,
        });
        const profileMapped: FarmerProfile = {
          name: created.name,
          phone: created.phone,
          location: created.location,
          village: created.village || payload.village,
          district: created.district || payload.district || 'Thanjavur',
          state: created.state || 'Tamil Nadu',
          totalLandAcres: created.totalLandAcres,
          landUnit: created.landUnit || 'Acres',
          primaryCrop: created.primaryCrop,
          soilType: created.soilType || 'Alluvial Clay Loam',
          irrigationSource: created.irrigationSource || 'Borewell / Tube Well',
          irrigationSources: created.irrigationSources || selectedIrrigationSources,
          preferredLanguage: (created.preferredLanguage as Language) || (preferredLang as Language),
          profilePhoto: profilePhoto || undefined,
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
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Status Alert Banner */}
      {statusMessage && (
        <div
          className={`p-4 rounded-2xl border flex items-start gap-3 transition-all ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-950 shadow-xs'
              : 'bg-rose-50 border-rose-300 text-rose-950 shadow-xs'
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
            className="text-xs font-bold opacity-60 hover:opacity-100 p-1"
            aria-label="Dismiss alert"
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
              onClick={() => {
                resetFormToSaved();
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>{t.common.editProfile || 'Edit Profile'}</span>
            </button>
          </div>
        }
      >
        <div className="space-y-6">
          {/* Identity Header */}
          <div className="flex flex-col sm:flex-row items-center gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-50 via-emerald-50/20 to-slate-50 border border-slate-200 shadow-xs">
            {activeFarmer.profilePhoto ? (
              <img
                src={activeFarmer.profilePhoto}
                alt={activeFarmer.name}
                className="w-16 h-16 rounded-full object-cover border-2 border-emerald-400 shadow-md shrink-0"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-emerald-700 text-white flex items-center justify-center font-extrabold text-xl shadow-md shrink-0">
                {activeFarmer.name ? activeFarmer.name.substring(0, 2).toUpperCase() : 'AG'}
              </div>
            )}
            <div className="text-center sm:text-left flex-1 min-w-0">
              <h3 className="text-lg font-bold text-slate-900 truncate">{activeFarmer.name}</h3>
              <p className="text-xs font-mono text-emerald-800 font-bold truncate">{activeFarmer.farmerId}</p>
              <p className="text-xs text-slate-500 mt-0.5 flex items-center justify-center sm:justify-start gap-1">
                <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                <span>{activeFarmer.location || activeFarmer.district || 'India'}</span>
                {activeFarmer.state && <span className="text-slate-400">({activeFarmer.state})</span>}
              </p>
            </div>
            <div className="flex flex-col sm:items-end gap-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-100/70 px-3 py-1.5 rounded-full border border-emerald-200">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>e-KYC Verified</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
                <Lock className="w-3.5 h-3.5 text-slate-500" />
                <span>Role: Farmer (Protected)</span>
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-100 bg-white space-y-2.5">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-600" />
                Agricultural & Holding Records
              </h4>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Total Cultivable Area:</span>
                <span className="font-bold text-emerald-800">
                  {activeFarmer.totalLandAcres} {activeFarmer.landUnit || 'Acres'}
                </span>
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
                    <span className="font-semibold text-slate-800">{activeFarmer.irrigationSource || 'Borewell'}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-100 bg-white space-y-2.5">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-blue-600" />
                Contact & Account Details
              </h4>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Registered Mobile:</span>
                <span className="font-semibold text-slate-800 font-mono">{activeFarmer.phone}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Aadhaar (Masked):</span>
                <span className="font-semibold text-slate-800 font-mono">{activeFarmer.aadhaarMasked || '•••• •••• 9182'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">State / Region:</span>
                <span className="font-semibold text-slate-800">{activeFarmer.state || 'Tamil Nadu'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">District:</span>
                <span className="font-semibold text-slate-800">{activeFarmer.district || 'Thanjavur'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Phone Verification:</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                  activeFarmer.isPhoneVerified
                    ? 'text-emerald-800 bg-emerald-50 border-emerald-200'
                    : 'text-amber-800 bg-amber-50 border-amber-200'
                }`}>
                  {activeFarmer.isPhoneVerified ? 'Verified via SMS' : 'Unverified (No SMS Gateway)'}
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
            <span>Refresh</span>
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
                    <td className="py-2.5 px-3 font-bold text-slate-900">{f.totalLandAcres} {f.landUnit || 'Acres'}</td>
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

      {/* Edit Profile Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 relative max-h-[92vh] overflow-y-auto">
            <button
              onClick={() => {
                resetFormToSaved();
                setIsModalOpen(false);
              }}
              className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label="Close modal"
            >
              ✕
            </button>

            <div className="flex items-center gap-3 mb-5 border-b border-slate-100 pb-3">
              <div className="p-2.5 rounded-2xl bg-emerald-100 text-emerald-800">
                <Edit3 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900">
                  {t.common.editProfile || 'Edit Farmer Profile'}
                </h4>
                <p className="text-xs text-slate-500">
                  Updates your saved agricultural profile, location, and regional language in MongoDB
                </p>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
              {/* Profile Photo Uploader */}
              <div className="flex items-center gap-4 p-3 bg-slate-50 rounded-2xl border border-slate-200">
                <div className="relative">
                  {profilePhoto ? (
                    <img
                      src={profilePhoto}
                      alt="Profile preview"
                      className="w-16 h-16 rounded-full object-cover border-2 border-emerald-500 shadow-sm"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-xl shadow-sm">
                      {name ? name.substring(0, 2).toUpperCase() : 'AG'}
                    </div>
                  )}
                  {isUploadingPhoto && (
                    <div className="absolute inset-0 rounded-full bg-slate-900/50 flex items-center justify-center">
                      <Loader2 className="w-5 h-5 text-white animate-spin" />
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  <p className="font-bold text-slate-800">Profile Photo (Optional)</p>
                  <p className="text-[11px] text-slate-500">Supports JPG, PNG, WEBP (Max 2MB)</p>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 text-[11px] font-bold shadow-2xs transition-colors"
                    >
                      <Camera className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{profilePhoto ? 'Change Photo' : 'Upload Photo'}</span>
                    </button>
                    {profilePhoto && (
                      <button
                        type="button"
                        onClick={handleRemovePhoto}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 text-[11px] font-bold transition-colors"
                      >
                        <Trash2 className="w-3 h-3 text-rose-600" />
                        <span>Remove</span>
                      </button>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={handlePhotoUpload}
                  />
                </div>
              </div>

              {/* Protected Read-Only Identity Row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded-xl bg-amber-50/70 border border-amber-200 text-[11px]">
                <div>
                  <span className="text-amber-800/80 block">Farmer ID (Protected):</span>
                  <span className="font-mono font-bold text-amber-950">{activeFarmer.farmerId || 'Auto-allocated'}</span>
                </div>
                <div>
                  <span className="text-amber-800/80 block">Account Role:</span>
                  <span className="font-bold text-amber-950">Farmer</span>
                </div>
                <div>
                  <span className="text-amber-800/80 block">Ownership Status:</span>
                  <span className="font-bold text-emerald-700">Authenticated</span>
                </div>
              </div>

              {/* Full Name & Mobile Number */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Farmer Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                    <span>Mobile Number *</span>
                    {phone !== (user?.phone || '') && (
                      <span className="text-[10px] text-amber-700 font-semibold">Number changed</span>
                    )}
                  </label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="10-digit mobile number"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-mono font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  {phone !== (user?.phone || '') ? (
                    <p className="text-[10px] text-amber-700 mt-0.5 flex items-center gap-1">
                      <Info className="w-3 h-3 shrink-0" />
                      <span>Changing mobile number will reset SMS verification status.</span>
                    </p>
                  ) : (
                    <p className="text-[10px] text-slate-400 mt-0.5">10-digit Indian number starting with 6-9</p>
                  )}
                </div>
              </div>

              {/* Preferred Regional Language */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Globe2 className="w-3.5 h-3.5 text-emerald-600" />
                    Preferred Regional Language (22 Eighth Schedule + English) *
                  </span>
                </label>
                <select
                  value={preferredLang}
                  onChange={(e) => setPreferredLang(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                >
                  {REGIONAL_LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.code} value={opt.code}>
                      {opt.name} ({opt.nativeName}) {opt.isFullyTranslated ? '• Full UI' : '• Core Translation'} {opt.direction === 'rtl' ? '[RTL]' : ''}
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Saving updates your preferred language application-wide, including voice and AI assistant.
                </p>
              </div>

              {/* Geographic Location Selection (State, District, Taluk, Village) */}
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <p className="font-bold text-slate-800 text-[11px] flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Geographic Location (State / Union Territory & District) *</span>
                </p>
                <GeoLocationSelect
                  value={profileGeoLoc}
                  onChange={setProfileGeoLoc}
                  required
                  compact
                  showAttribution
                />
              </div>

              {/* Farm Area & Unit + Primary Crop */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Land Area and Unit */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Land Holding Area & Unit *
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      step="1"
                      min="1"
                      required
                      value={landAcresInput}
                      onChange={(e) => setLandAcresInput(e.target.value)}
                      placeholder="e.g. 5"
                      className="w-2/3 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                    <select
                      value={landUnit}
                      onChange={(e) => setLandUnit(e.target.value)}
                      className="w-1/3 bg-slate-50 border border-slate-200 rounded-xl px-2 py-2 font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    >
                      {LAND_UNITS.map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                    </select>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">Whole integers only (e.g., 1, 3, 5)</p>
                </div>

                {/* Primary Crop */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Primary Crop *
                  </label>
                  <input
                    type="text"
                    required
                    value={primaryCrop}
                    onChange={(e) => setPrimaryCrop(e.target.value)}
                    placeholder="e.g. Paddy (Samba)"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <div className="flex flex-wrap gap-1 mt-1">
                    {COMMON_CROPS.slice(0, 4).map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setPrimaryCrop(c)}
                        className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 hover:bg-emerald-100 font-semibold"
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Soil Type */}
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Soil Type
                </label>
                <input
                  type="text"
                  value={soilType}
                  onChange={(e) => setSoilType(e.target.value)}
                  placeholder="e.g. Alluvial Clay Loam"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
                <div className="flex flex-wrap gap-1 mt-1">
                  {COMMON_SOILS.slice(0, 4).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSoilType(s)}
                      className="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 hover:bg-amber-100 font-semibold"
                    >
                      {s}
                    </button>
                  ))}
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
                      placeholder="e.g. Solar Lift Pump from canal"
                      className="w-full px-3 py-1.5 bg-white border border-blue-300 rounded-xl text-xs font-medium"
                    />
                  </div>
                )}
              </div>

              {/* Form Actions: Cancel & Save */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    resetFormToSaved();
                    setIsModalOpen(false);
                  }}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold transition-colors"
                >
                  {t.common.cancel || 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-sm transition-all inline-flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving to MongoDB...</span>
                    </>
                  ) : (
                    <span>{t.common.saveChanges || 'Save Changes'}</span>
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

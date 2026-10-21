import React, { useState, useEffect, useCallback } from 'react';
import {
  Droplets,
  Sprout,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Info,
  Loader2,
  ArrowRight,
  ShieldAlert,
  MapPin,
  RefreshCw,
  Compass,
  Check,
  Save,
  WifiOff,
  Sun,
  Clock,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  calculateIrrigationApi,
  getIrrigationWeatherApi,
  updateFarmLocationApi,
  type IrrigationCalculateResponse,
  type IrrigationWeatherResponse,
} from '../../services/api';

const CROPS = [
  'Paddy / Rice (சம்பா நெல்)',
  'Hybrid Maize (மக்காச்சோளம்)',
  'Sugarcane (கரும்பு)',
  'Cotton (பருத்தி)',
  'Black Gram (உளுந்து)',
  'Groundnut (நிலக்கடலை)',
  'Banana (வாழை)',
];

const GROWTH_STAGES = [
  'Initial / Sowing (விதைப்பு / நாற்று நிலை)',
  'Vegetative / Active Tillering (தழைப்பருவம் / கிளைத்தல்)',
  'Flowering / Panicle Initiation (பூக்கும் பருவம் / கதிர் உருவாக்கம்)',
  'Grain Filling / Pod Development (பால் மற்றும் காய் பிடிக்கும் பருவம்)',
  'Maturity / Ripening (முதிர்ச்சி நிலை)',
];

const SOIL_TYPES = [
  'Alluvial Clay Loam (வண்டல் களிமண்)',
  'Clay Loam (களிமண்)',
  'Red Loam (செம்மண்)',
  'Sandy Loam (மணல் கலந்த செம்மண்)',
  'Black Cotton Soil (கரிசல் மண்)',
];

const IRRIGATION_METHODS = [
  'Controlled Basin Flooding (பாத்தி முறை / நீர் கட்டுதல்)',
  'Precision Drip Irrigation (சொட்டு நீர் பாசனம்)',
  'Overhead Sprinkler (தெளிப்பு நீர் பாசனம்)',
  'Furrow Irrigation (பார் / சால் பாசனம்)',
];

// Tamil Nadu Agricultural District Reference Coordinates
export const TN_DISTRICT_LOCATIONS: Record<
  string,
  { name: string; nameTa: string; lat: number; lon: number; zone: string }
> = {
  thanjavur: { name: 'Thanjavur', nameTa: 'தஞ்சாவூர்', lat: 10.787, lon: 79.1378, zone: 'Cauvery Delta' },
  tiruvarur: { name: 'Tiruvarur', nameTa: 'திருவாரூர்', lat: 10.7725, lon: 79.6365, zone: 'Cauvery Delta' },
  nagapattinam: { name: 'Nagapattinam', nameTa: 'நாகப்பட்டினம்', lat: 10.7672, lon: 79.8449, zone: 'Cauvery Delta' },
  mayiladuthurai: { name: 'Mayiladuthurai', nameTa: 'மயிலாடுதுறை', lat: 11.1018, lon: 79.6522, zone: 'Cauvery Delta' },
  tiruchirappalli: { name: 'Tiruchirappalli', nameTa: 'திருச்சிராப்பள்ளி', lat: 10.7905, lon: 78.7047, zone: 'Cauvery Delta' },
  pudukkottai: { name: 'Pudukkottai', nameTa: 'புதுக்கோட்டை', lat: 10.3833, lon: 78.8001, zone: 'Cauvery Delta' },
  madurai: { name: 'Madurai', nameTa: 'மதுரை', lat: 9.9252, lon: 78.1198, zone: 'Southern' },
  coimbatore: { name: 'Coimbatore', nameTa: 'கோயம்புத்தூர்', lat: 11.0168, lon: 76.9558, zone: 'Western' },
  salem: { name: 'Salem', nameTa: 'சேலம்', lat: 11.6643, lon: 78.146, zone: 'North-Western' },
  erode: { name: 'Erode', nameTa: 'ஈரோடு', lat: 11.341, lon: 77.7172, zone: 'Western' },
  cuddalore: { name: 'Cuddalore', nameTa: 'கடலூர்', lat: 11.748, lon: 79.7714, zone: 'North-Eastern' },
  tirunelveli: { name: 'Tirunelveli', nameTa: 'திருநெல்வேலி', lat: 8.7139, lon: 77.7567, zone: 'Southern' },
  dindigul: { name: 'Dindigul', nameTa: 'திண்டுக்கல்', lat: 10.3673, lon: 77.9803, zone: 'Southern' },
  theni: { name: 'Theni', nameTa: 'தேனி', lat: 10.0104, lon: 77.4768, zone: 'Southern' },
  virudhunagar: { name: 'Virudhunagar', nameTa: 'விருதுநகர்', lat: 9.568, lon: 77.9624, zone: 'Southern' },
  ramanathapuram: { name: 'Ramanathapuram', nameTa: 'ராமநாதபுரம்', lat: 9.3639, lon: 78.8395, zone: 'Southern' },
  sivaganga: { name: 'Sivaganga', nameTa: 'சிவகங்கை', lat: 9.8433, lon: 78.4809, zone: 'Southern' },
  tenkasi: { name: 'Tenkasi', nameTa: 'தென்காசி', lat: 8.9594, lon: 77.315, zone: 'Southern' },
  thoothukudi: { name: 'Thoothukudi', nameTa: 'தூத்துக்குடி', lat: 8.7642, lon: 78.1348, zone: 'Southern' },
  kanniyakumari: { name: 'Kanniyakumari', nameTa: 'கன்னியாகுமரி', lat: 8.0883, lon: 77.5385, zone: 'Southern' },
  karur: { name: 'Karur', nameTa: 'கரூர்', lat: 10.9601, lon: 78.0766, zone: 'Western' },
  perambalur: { name: 'Perambalur', nameTa: 'பெரம்பலூர்', lat: 11.2333, lon: 78.8833, zone: 'Cauvery Delta' },
  ariyalur: { name: 'Ariyalur', nameTa: 'அரியலூர்', lat: 11.1401, lon: 79.0786, zone: 'Cauvery Delta' },
  namakkal: { name: 'Namakkal', nameTa: 'நாமக்கல்', lat: 11.2189, lon: 78.1674, zone: 'North-Western' },
  dharmapuri: { name: 'Dharmapuri', nameTa: 'தர்மபுரி', lat: 12.1211, lon: 78.1582, zone: 'North-Western' },
  krishnagiri: { name: 'Krishnagiri', nameTa: 'கிருஷ்ணகிரி', lat: 12.5186, lon: 78.2137, zone: 'North-Western' },
  tirupathur: { name: 'Tirupathur', nameTa: 'திருப்பத்தூர்', lat: 12.4958, lon: 78.5678, zone: 'North-Eastern' },
  vellore: { name: 'Vellore', nameTa: 'வேலூர்', lat: 12.9165, lon: 79.1325, zone: 'North-Eastern' },
  ranipet: { name: 'Ranipet', nameTa: 'ராணிப்பேட்டை', lat: 12.9299, lon: 79.333, zone: 'North-Eastern' },
  tiruvannamalai: { name: 'Tiruvannamalai', nameTa: 'திருவண்ணாமலை', lat: 12.2253, lon: 79.0747, zone: 'North-Eastern' },
  villupuram: { name: 'Villupuram', nameTa: 'விழுப்புரம்', lat: 11.9401, lon: 79.4861, zone: 'North-Eastern' },
  kallakurichi: { name: 'Kallakurichi', nameTa: 'கள்ளக்குறிச்சி', lat: 11.7383, lon: 78.9639, zone: 'North-Eastern' },
  kancheepuram: { name: 'Kancheepuram', nameTa: 'காஞ்சிபுரம்', lat: 12.8342, lon: 79.7036, zone: 'North-Eastern' },
  chengalpattu: { name: 'Chengalpattu', nameTa: 'செங்கல்பட்டு', lat: 12.6841, lon: 79.9836, zone: 'North-Eastern' },
  tiruvallur: { name: 'Tiruvallur', nameTa: 'திருவள்ளூர்', lat: 13.1432, lon: 79.9082, zone: 'Coastal' },
  chennai: { name: 'Chennai', nameTa: 'சென்னை', lat: 13.0827, lon: 80.2707, zone: 'Coastal' },
  nilgiris: { name: 'Nilgiris', nameTa: 'நீலகிரி', lat: 11.4102, lon: 76.695, zone: 'Hilly / High Rainfall' },
  tiruppur: { name: 'Tiruppur', nameTa: 'திருப்பூர்', lat: 11.1085, lon: 77.3411, zone: 'Western' },
};

export const IrrigationView: React.FC = () => {
  const { t, language } = useLanguage();
  const { user, token, updateUser } = useAuth();
  const pageT = t.irrigationPage;

  // Farm Location State
  const [lat, setLat] = useState<number | null>(() => {
    if (user?.farmCoordinates?.latitude) return user.farmCoordinates.latitude;
    const distKey = (user?.district || '').trim().toLowerCase();
    return TN_DISTRICT_LOCATIONS[distKey]?.lat ?? null;
  });

  const [lon, setLon] = useState<number | null>(() => {
    if (user?.farmCoordinates?.longitude) return user.farmCoordinates.longitude;
    const distKey = (user?.district || '').trim().toLowerCase();
    return TN_DISTRICT_LOCATIONS[distKey]?.lon ?? null;
  });

  const [locationName, setLocationName] = useState<string>(() => {
    if (user?.farmCoordinates?.locationName) return user.farmCoordinates.locationName;
    const distKey = (user?.district || '').trim().toLowerCase();
    return TN_DISTRICT_LOCATIONS[distKey]?.name || 'Tamil Nadu Farm';
  });

  const [selectedDistrict, setSelectedDistrict] = useState<string>(() => {
    const distKey = (user?.district || '').trim().toLowerCase();
    return TN_DISTRICT_LOCATIONS[distKey] ? distKey : 'thanjavur';
  });

  const [isEditingLocation, setIsEditingLocation] = useState<boolean>(false);
  const [manualLat, setManualLat] = useState<string>('');
  const [manualLon, setManualLon] = useState<string>('');
  const [consentChecked, setConsentChecked] = useState<boolean>(false);
  const [isDetectingGps, setIsDetectingGps] = useState<boolean>(false);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [isSavingLocation, setIsSavingLocation] = useState<boolean>(false);
  const [saveLocationSuccess, setSaveLocationSuccess] = useState<string | null>(null);

  // Weather Feed State
  const [weather, setWeather] = useState<IrrigationWeatherResponse | null>(null);
  const [weatherLoading, setWeatherLoading] = useState<boolean>(false);
  const [weatherRefreshing, setWeatherRefreshing] = useState<boolean>(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);

  // Irrigation Form State (Strictly user-selectable crop & agronomic fields)
  const [crop, setCrop] = useState<string>(CROPS[0]);
  const [growthStage, setGrowthStage] = useState<string>(GROWTH_STAGES[1]);
  const [soilType, setSoilType] = useState<string>(SOIL_TYPES[0]);
  const [irrigationMethod, setIrrigationMethod] = useState<string>(IRRIGATION_METHODS[0]);
  const [fieldArea, setFieldArea] = useState<string>(() => {
    return user?.totalLandAcres ? user.totalLandAcres.toString() : '1.0';
  });

  // Calculation Results
  const [calculating, setCalculating] = useState<boolean>(false);
  const [result, setResult] = useState<IrrigationCalculateResponse | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);

  // Monitor online / offline status
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch Agrometeorological Weather
  const fetchWeather = useCallback(async (latitude: number, longitude: number, isRefresh = false) => {
    if (!navigator.onLine) {
      setIsOffline(true);
      return;
    }
    if (isRefresh) {
      setWeatherRefreshing(true);
    } else {
      setWeatherLoading(true);
    }
    setWeatherError(null);

    try {
      const data = await getIrrigationWeatherApi(latitude, longitude, isRefresh);
      setWeather(data);
      if (data.error && !data.isLive && !data.isCached) {
        setWeatherError(data.error);
      }
    } catch (err: any) {
      setWeatherError(
        err.message || 'Live weather feed is temporarily unreachable. Please retry.'
      );
    } finally {
      setWeatherLoading(false);
      setWeatherRefreshing(false);
    }
  }, []);

  // Initial Weather Load on Mount or Coordinate Change
  useEffect(() => {
    if (lat !== null && lon !== null) {
      fetchWeather(lat, lon, false);
    }
  }, [lat, lon, fetchWeather]);

  // Handle Browser Geolocation Fix with User Confirmation
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.');
      return;
    }
    setGpsError(null);
    setIsDetectingGps(true);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const detectedLat = parseFloat(pos.coords.latitude.toFixed(4));
        const detectedLon = parseFloat(pos.coords.longitude.toFixed(4));
        setLat(detectedLat);
        setLon(detectedLon);
        setLocationName('Detected Farm Location (GPS)');
        setManualLat(detectedLat.toString());
        setManualLon(detectedLon.toString());
        setIsDetectingGps(false);
        setIsEditingLocation(true);
        fetchWeather(detectedLat, detectedLon, true);
      },
      (err) => {
        setIsDetectingGps(false);
        setGpsError(err.message || 'Location access permission was denied or timed out.');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  // Handle District Selection Dropdown
  const handleSelectDistrictChange = (distKey: string) => {
    setSelectedDistrict(distKey);
    const d = TN_DISTRICT_LOCATIONS[distKey];
    if (d) {
      setLat(d.lat);
      setLon(d.lon);
      setLocationName(language === 'ta' ? d.nameTa : d.name);
      setManualLat(d.lat.toString());
      setManualLon(d.lon.toString());
      fetchWeather(d.lat, d.lon, false);
    }
  };

  // Handle Saving Location to Farmer Profile with Consent
  const handleSaveFarmLocation = async () => {
    if (!consentChecked) {
      setGpsError('Please check the consent box to save your farm coordinates.');
      return;
    }
    if (lat === null || lon === null) {
      setGpsError('Valid latitude and longitude are required.');
      return;
    }

    setIsSavingLocation(true);
    setGpsError(null);
    setSaveLocationSuccess(null);

    try {
      const updatedUser = await updateFarmLocationApi(
        {
          latitude: lat,
          longitude: lon,
          locationName,
          consent: true,
        },
        token
      );
      updateUser(updatedUser);
      setSaveLocationSuccess(pageT.locationSavedSuccess);
      setIsEditingLocation(false);
      setTimeout(() => setSaveLocationSuccess(null), 4000);
    } catch (err: any) {
      setGpsError(err.message || 'Failed to save farm coordinates.');
    } finally {
      setIsSavingLocation(false);
    }
  };

  // Handle Irrigation Advisory Calculation
  const handleCalculate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (lat === null || lon === null) {
      setCalcError(pageT.locationRequiredWarning);
      return;
    }

    setCalculating(true);
    setCalcError(null);

    const parsedArea = parseFloat(fieldArea);
    const validArea = !isNaN(parsedArea) && parsedArea > 0 ? parsedArea : 1.0;

    try {
      const res = await calculateIrrigationApi({
        crop,
        growthStage,
        soilType,
        irrigationMethod,
        fieldAreaAcres: validArea,
        latitude: lat,
        longitude: lon,
      });
      setResult(res);
      // If calculate returned an updated weatherSummary, keep weather synced
      if (res.weatherSummary) {
        setWeather(res.weatherSummary);
      }
    } catch (err: any) {
      setCalcError(err.message || 'Failed to compute irrigation advisory.');
    } finally {
      setCalculating(false);
    }
  };

  // Handle Refreshing Advisory with fresh weather
  const handleRefreshAdvisory = async () => {
    if (lat === null || lon === null) return;
    setCalculating(true);
    setCalcError(null);
    try {
      if (fetchWeather) {
        await fetchWeather(lat, lon, true);
      }
      const parsedArea = parseFloat(fieldArea);
      const validArea = !isNaN(parsedArea) && parsedArea > 0 ? parsedArea : 1.0;
      const res = await calculateIrrigationApi({
        crop,
        growthStage,
        soilType,
        irrigationMethod,
        fieldAreaAcres: validArea,
        latitude: lat,
        longitude: lon,
      });
      setResult(res);
      if (res.weatherSummary) {
        setWeather(res.weatherSummary);
      }
    } catch (err: any) {
      setCalcError(err.message || 'Failed to refresh irrigation advisory.');
    } finally {
      setCalculating(false);
    }
  };

  const hasSavedFarmCoords = Boolean(user?.farmCoordinates?.latitude && user?.farmCoordinates?.longitude);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
      {/* 1. Header Card */}
      <Card
        title={t.nav.irrigation}
        subtitle={pageT.subtitle}
        icon={<Droplets className="w-5 h-5 text-blue-600" />}
        headerAction={
          <Badge variant="blue" dot>
            FAO-56 Water Budgeting
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Transparent Advisory Framework Notice */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-800">
                {language === 'ta'
                  ? 'நேரடி வானிலை & வெளிப்படையான வேளாண் வழிகாட்டுதல்'
                  : 'Live Meteorological Integration & Agronomic Advisory Framework'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? 'மழை வாய்ப்பு, பெய்த மழை மற்றும் ஆவியாதல் (ET₀) ஆகியவை Open-Meteo வானிலை மாதிரிகள் மூலம் தானாகவே கணக்கிடப்படுகின்றன. மாதிரி மண் ஈரப்பதம் ஒரு கணித உருவகப்படுத்துதலாகும் (நேரடி IoT சென்சார் அல்ல). வயல் நிலையை சரிபார்த்து நீர் பாய்ச்சவும்.'
                  : 'Rain probability, precipitation, and reference evapotranspiration (ET₀) are fetched live via Open-Meteo agrometeorological models. Modelled soil moisture is a numerical land-surface estimate (not an in-situ IoT probe). Always check field crumb condition before pumping.'}
              </p>
            </div>
          </div>

          {/* 2. Farm Location & Weather Station Card */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
                <h3 className="text-xs sm:text-sm font-bold text-slate-800">
                  {pageT.locationCardTitle}
                </h3>
                {hasSavedFarmCoords && (
                  <Badge variant="emerald" size="sm">
                    {pageT.savedLocation}
                  </Badge>
                )}
              </div>
              <button
                type="button"
                onClick={() => setIsEditingLocation((prev) => !prev)}
                className="text-[11px] font-bold text-blue-600 hover:text-blue-700 underline"
              >
                {isEditingLocation
                  ? language === 'ta'
                    ? 'சுருக்கவும்'
                    : 'Done'
                  : language === 'ta'
                  ? 'இருப்பிடத்தை மாற்று / GPS'
                  : 'Change Location / GPS'}
              </button>
            </div>

            {/* Current Selected Location Indicator */}
            <div className="flex flex-wrap items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-700">{locationName}</span>
                {lat !== null && lon !== null && (
                  <span className="text-[11px] font-mono text-slate-500">
                    ({lat.toFixed(4)}°N, {lon.toFixed(4)}°E)
                  </span>
                )}
              </div>
              {hasSavedFarmCoords && (
                <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1">
                  <Check className="w-3 h-3" />
                  {language === 'ta' ? 'சுயவிவரத்தில் சேமிக்கப்பட்டது' : 'Saved in profile'}
                </span>
              )}
            </div>

            {/* Location Editing Panel */}
            {isEditingLocation && (
              <div className="p-3.5 bg-blue-50/50 rounded-xl border border-blue-200/60 space-y-3 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Option A: Browser Geolocation */}
                  <div className="space-y-1.5">
                    <span className="font-bold text-slate-700 block">
                      {language === 'ta' ? 'விருப்பம் 1: உலாவி GPS கண்டறிதல்' : 'Option 1: Browser GPS Fix'}
                    </span>
                    <button
                      type="button"
                      disabled={isDetectingGps}
                      onClick={handleDetectLocation}
                      className="w-full py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold flex items-center justify-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
                    >
                      {isDetectingGps ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          {pageT.detectingGps}
                        </>
                      ) : (
                        <>
                          <Compass className="w-3.5 h-3.5" />
                          {pageT.detectGpsBtn}
                        </>
                      )}
                    </button>
                    <span className="text-[10px] text-slate-500 block">
                      {language === 'ta'
                        ? 'உங்கள் அனுமதியுடன் மட்டுமே தற்போதைய GPS ஆயத்தொலைவுகள் பெறப்படும்.'
                        : 'Requires browser location permission. Never used silently.'}
                    </span>
                  </div>

                  {/* Option B: District Selection */}
                  <div className="space-y-1.5">
                    <span className="font-bold text-slate-700 block">
                      {language === 'ta' ? 'விருப்பம் 2: வேளாண் மாவட்டம்' : 'Option 2: Agricultural District'}
                    </span>
                    <select
                      value={selectedDistrict}
                      onChange={(e) => handleSelectDistrictChange(e.target.value)}
                      className="w-full py-2 px-3 bg-white border border-slate-300 rounded-lg font-medium text-slate-800 focus:ring-2 focus:ring-blue-500"
                    >
                      {Object.entries(TN_DISTRICT_LOCATIONS).map(([k, d]) => (
                        <option key={k} value={k}>
                          {language === 'ta' ? d.nameTa : d.name} ({d.zone})
                        </option>
                      ))}
                    </select>
                    <span className="text-[10px] text-slate-500 block">
                      {language === 'ta'
                        ? 'மாவட்ட மைய ஆயத்தொலைவுகள் தானாக அமைக்கப்படும்.'
                        : 'Sets official district centroid coordinates.'}
                    </span>
                  </div>
                </div>

                {/* Option C: Manual Coordinate Input */}
                <div className="pt-2 border-t border-blue-200/60">
                  <span className="font-bold text-slate-700 block mb-1">
                    {pageT.manualCoordsLabel}
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">{pageT.latLabel}</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={manualLat}
                        onChange={(e) => {
                          setManualLat(e.target.value);
                          const val = parseFloat(e.target.value);
                          if (!isNaN(val) && val >= -90 && val <= 90) {
                            setLat(val);
                            setLocationName('Custom GPS Coordinates');
                            fetchWeather(val, lon ?? 79.1378, false);
                          }
                        }}
                        placeholder="e.g. 10.7870"
                        className="w-full px-2 py-1 text-xs border border-slate-300 rounded-lg bg-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">{pageT.lonLabel}</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={manualLon}
                        onChange={(e) => {
                          setManualLon(e.target.value);
                          const val = parseFloat(e.target.value);
                          if (!isNaN(val) && val >= -180 && val <= 180) {
                            setLon(val);
                            setLocationName('Custom GPS Coordinates');
                            fetchWeather(lat ?? 10.7870, val, false);
                          }
                        }}
                        placeholder="e.g. 79.1378"
                        className="w-full px-2 py-1 text-xs border border-slate-300 rounded-lg bg-white font-mono"
                      />
                    </div>
                  </div>
                </div>

                {/* Consent & Save to Profile */}
                <div className="pt-2 border-t border-blue-200/60 space-y-2">
                  <label className="flex items-start gap-2 cursor-pointer text-[11px] text-slate-700">
                    <input
                      type="checkbox"
                      checked={consentChecked}
                      onChange={(e) => setConsentChecked(e.target.checked)}
                      className="mt-0.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                    />
                    <span>{pageT.savePrimaryConsent}</span>
                  </label>

                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="button"
                      disabled={!consentChecked || isSavingLocation || lat === null || lon === null}
                      onClick={handleSaveFarmLocation}
                      className="py-1.5 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-40"
                    >
                      {isSavingLocation ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          {pageT.savingLocation}
                        </>
                      ) : (
                        <>
                          <Save className="w-3.5 h-3.5" />
                          {pageT.saveLocationBtn}
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {gpsError && (
                  <div className="p-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-[11px]">
                    {gpsError}
                  </div>
                )}
                {saveLocationSuccess && (
                  <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    {saveLocationSuccess}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 3. Read-Only Live Agrometeorological Weather Summary Card */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-blue-50/30 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Sun className="w-4 h-4 text-amber-500" />
                <h3 className="text-xs sm:text-sm font-bold text-slate-800">
                  {pageT.liveWeatherCardTitle}
                </h3>
                {weather?.isLive && (
                  <Badge variant="blue" size="sm" dot>
                    Live Open-Meteo
                  </Badge>
                )}
                {weather?.isCached && !weather?.isStale && (
                  <Badge variant="gray" size="sm">
                    Cached 15m
                  </Badge>
                )}
              </div>

              {/* Refresh Action Button */}
              <button
                type="button"
                disabled={weatherLoading || weatherRefreshing || lat === null || lon === null}
                onClick={() => lat !== null && lon !== null && fetchWeather(lat, lon, true)}
                className="py-1 px-2.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-bold shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 text-blue-600 ${
                    weatherRefreshing ? 'animate-spin' : ''
                  }`}
                />
                <span>
                  {weatherRefreshing ? pageT.refreshing : pageT.refreshWeather}
                </span>
              </button>
            </div>

            {/* UI State Banners */}
            {isOffline && (
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-center gap-2">
                <WifiOff className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{pageT.offlineWarning}</span>
              </div>
            )}

            {weather?.isStale && (
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{pageT.staleDataWarning}</span>
              </div>
            )}

            {weatherError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-300 text-rose-800 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">{pageT.providerError}</p>
                  <p className="text-[11px] text-rose-700 mt-0.5">{weatherError}</p>
                </div>
              </div>
            )}

            {/* Loading State Skeleton */}
            {weatherLoading && !weather && (
              <div className="py-8 flex flex-col items-center justify-center gap-2 text-slate-500 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span>{pageT.loadingWeather}</span>
              </div>
            )}

            {/* Live Weather Metrics Grid */}
            {weather && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                  {/* Metric 1: Temp & Condition */}
                  <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      {pageT.temp}
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-lg font-extrabold text-slate-800">
                        {weather.current?.temperatureC !== null
                          ? `${weather.current?.temperatureC}°C`
                          : '—'}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-500 mt-1 block truncate">
                      {language === 'ta'
                        ? weather.current?.conditionTa || 'பகுதி மேகமூட்டம்'
                        : weather.current?.condition || 'Partly Cloudy'}
                    </span>
                  </div>

                  {/* Metric 2: Relative Humidity */}
                  <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      {pageT.humidity}
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-lg font-extrabold text-slate-800">
                        {weather.current?.humidity !== null ? `${weather.current?.humidity}%` : '—'}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      RH @ 2m height
                    </span>
                  </div>

                  {/* Metric 3: Rain Probability & Precipitation */}
                  <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      {pageT.rainProbability}
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-lg font-extrabold text-indigo-700">
                        {weather.precipitationProbability !== null
                          ? `${weather.precipitationProbability}%`
                          : '—'}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-500 mt-1 block">
                      {weather.precipitationSumMm !== null
                        ? `~${weather.precipitationSumMm} mm rain`
                        : 'No rain forecast'}
                    </span>
                  </div>

                  {/* Metric 4: Reference Evapotranspiration ET0 */}
                  <div className="bg-white p-3 rounded-xl border border-blue-200/80 shadow-2xs bg-blue-50/20">
                    <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">
                      {pageT.et0Title}
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-lg font-extrabold text-blue-700">
                        {weather.et0EstimateMmDay !== null
                          ? `${weather.et0EstimateMmDay} mm`
                          : '5.0 mm'}
                      </span>
                      <span className="text-[10px] text-blue-500">/day</span>
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      FAO-56 PM model
                    </span>
                  </div>
                </div>

                {/* Modelled Soil Moisture Card */}
                <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-amber-700" />
                      <span className="text-xs font-bold text-slate-800">
                        {pageT.soilMoistureTitle}:
                      </span>
                      <span className="text-xs font-extrabold text-emerald-700">
                        {weather.soilMoisture.available && weather.soilMoisture.rootZonePercent !== null
                          ? `${weather.soilMoisture.rootZonePercent}%`
                          : pageT.soilMoistureUnavailable}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400">
                      Layer depth: 0 to 28 cm
                    </span>
                  </div>

                  {/* Multi-depth Soil Moisture Breakdown */}
                  {weather.soilMoisture.available && (
                    <div className="grid grid-cols-3 gap-2 text-[11px] pt-1">
                      <div className="bg-slate-50 p-2 rounded-lg border border-slate-200 text-center">
                        <span className="text-[10px] text-slate-400 block font-semibold">
                          {pageT.depth0_7}
                        </span>
                        <span className="font-bold text-slate-800">
                          {weather.soilMoisture.depth0To7cmPercent !== null
                            ? `${weather.soilMoisture.depth0To7cmPercent}%`
                            : '—'}
                        </span>
                      </div>
                      <div className="bg-slate-50 p-2 rounded-lg border border-slate-200 text-center">
                        <span className="text-[10px] text-slate-400 block font-semibold">
                          {pageT.depth7_28}
                        </span>
                        <span className="font-bold text-slate-800">
                          {weather.soilMoisture.depth7To28cmPercent !== null
                            ? `${weather.soilMoisture.depth7To28cmPercent}%`
                            : '—'}
                        </span>
                      </div>
                      <div className="bg-slate-50 p-2 rounded-lg border border-slate-200 text-center">
                        <span className="text-[10px] text-slate-400 block font-semibold">
                          {pageT.depth28_100}
                        </span>
                        <span className="font-bold text-slate-800">
                          {weather.soilMoisture.depth28To100cmPercent !== null
                            ? `${weather.soilMoisture.depth28To100cmPercent}%`
                            : '—'}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Truthfulness Notice */}
                  <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-100">
                    <span>
                      {language === 'ta'
                        ? weather.soilMoisture.disclaimerTa || pageT.soilMoistureDisclaimer
                        : weather.soilMoisture.disclaimer || pageT.soilMoistureDisclaimer}
                    </span>
                    <span className="font-mono text-slate-400 shrink-0 ml-2">
                      {weather.lastUpdated}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 4. Agronomic Crop Input Form (Manual weather fields completely removed) */}
          <form onSubmit={handleCalculate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
              {/* 1. Crop Selection */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  {pageT.cropSelection}
                </label>
                <select
                  value={crop}
                  onChange={(e) => setCrop(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                >
                  {CROPS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* 2. Growth Stage */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  {pageT.growthStage}
                </label>
                <select
                  value={growthStage}
                  onChange={(e) => setGrowthStage(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                >
                  {GROWTH_STAGES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* 3. Soil Type */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-600" />
                  {pageT.soilType}
                </label>
                <select
                  value={soilType}
                  onChange={(e) => setSoilType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                >
                  {SOIL_TYPES.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              {/* 4. Irrigation Method */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Droplets className="w-3.5 h-3.5 text-teal-600" />
                  {pageT.irrigationMethod}
                </label>
                <select
                  value={irrigationMethod}
                  onChange={(e) => setIrrigationMethod(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                >
                  {IRRIGATION_METHODS.map((im) => (
                    <option key={im} value={im}>
                      {im}
                    </option>
                  ))}
                </select>
              </div>

              {/* 5. Cultivated Field Area (Acres) - Separate field section */}
              <div className="sm:col-span-2 lg:col-span-2">
                <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-blue-600" />
                    {pageT.fieldAreaLabel}
                  </span>
                  <span className="text-[10px] text-slate-400 font-normal">
                    1 Acre ≈ 4,047 m²
                  </span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="500"
                    value={fieldArea}
                    onChange={(e) => setFieldArea(e.target.value)}
                    placeholder="1.0"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                  />
                  <span className="absolute right-3 top-2.5 text-slate-400 font-semibold text-xs">
                    Acres
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">{pageT.fieldAreaHelp}</p>
              </div>
            </div>

            {/* Calculate Button */}
            <button
              type="submit"
              disabled={calculating || lat === null || lon === null}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {calculating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {pageT.calculating}
                </>
              ) : (
                <>
                  <span>{pageT.calculateBtn}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Calc Error Banner */}
          {calcError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              {calcError}
            </div>
          )}

          {/* 5. Advisory Results Display */}
          {result && (
            <div className="space-y-5 pt-4 border-t border-slate-200/80">
              {/* Recommendation Banner with Distinct Outcome Themes */}
              <div
                className={`p-5 rounded-2xl border shadow-sm ${
                  result.recommendation === 'delay_reassess' || result.status === 'delay'
                    ? 'bg-amber-50/90 border-amber-300 text-amber-950'
                    : result.recommendation === 'monitor_conditions' || result.status === 'adequate'
                    ? 'bg-sky-50/90 border-sky-300 text-sky-950'
                    : 'bg-emerald-50/90 border-emerald-300 text-emerald-950'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    {result.recommendation === 'delay_reassess' || result.status === 'delay' ? (
                      <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                    ) : result.recommendation === 'monitor_conditions' || result.status === 'adequate' ? (
                      <CheckCircle2 className="w-6 h-6 text-sky-600 shrink-0 mt-0.5" />
                    ) : (
                      <Droplets className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[11px] font-extrabold uppercase tracking-wider ${
                            result.recommendation === 'delay_reassess' || result.status === 'delay'
                              ? 'bg-amber-200/70 text-amber-900 border border-amber-300'
                              : result.recommendation === 'monitor_conditions' || result.status === 'adequate'
                              ? 'bg-sky-200/70 text-sky-900 border border-sky-300'
                              : 'bg-emerald-200/70 text-emerald-900 border border-emerald-300'
                          }`}
                        >
                          {language === 'ta'
                            ? result.recommendationTitleTa || (result.recommendation === 'delay_reassess' ? pageT.recDelayReassess : result.recommendation === 'monitor_conditions' ? pageT.recMonitorConditions : pageT.recIrrigateNow)
                            : result.recommendationTitleEn || (result.recommendation === 'delay_reassess' ? pageT.recDelayReassess : result.recommendation === 'monitor_conditions' ? pageT.recMonitorConditions : pageT.recIrrigateNow)}
                        </span>
                        {result.confidenceLevel && (
                          <span className="text-[10px] font-bold text-slate-500">
                            {pageT.confidenceLabel}: {result.confidenceLevel}
                          </span>
                        )}
                      </div>
                      <h4 className="text-base font-extrabold tracking-tight mt-1">
                        {language === 'ta' ? result.recommendationTa : result.recommendationEn}
                      </h4>
                    </div>
                  </div>

                  {/* Refresh Advisory Action */}
                  <button
                    type="button"
                    disabled={calculating || lat === null || lon === null}
                    onClick={handleRefreshAdvisory}
                    className="py-1 px-3 bg-white/90 hover:bg-white text-slate-700 border border-slate-300/80 rounded-lg text-xs font-bold shadow-xs transition-all flex items-center gap-1.5 disabled:opacity-50 shrink-0"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 text-blue-600 ${calculating ? 'animate-spin' : ''}`} />
                    <span>{pageT.refreshAdvisoryBtn}</span>
                  </button>
                </div>

                {/* Local Irrigation Window Banner */}
                <div className="mt-4 p-3 rounded-xl bg-white/90 border border-black/5 flex items-start gap-2.5">
                  <Clock className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <div className="text-xs">
                    <span className="font-bold text-slate-800 block">
                      {pageT.irrigationWindowLabel}:
                    </span>
                    <span className="text-sm font-extrabold text-indigo-900 block mt-0.5">
                      {language === 'ta'
                        ? result.irrigationWindowTa || '06:00 AM – 09:00 AM IST'
                        : result.irrigationWindowEn || '06:00 AM – 09:00 AM IST'}
                    </span>
                  </div>
                </div>

                {/* Agronomic Parameter Badges */}
                {result.isWaterVolumeEstimated !== false ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3 text-xs bg-white/80 p-3 rounded-xl border border-black/5">
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        {pageT.cropFactorLabel}
                      </span>
                      <span className="font-extrabold text-slate-800 text-sm">
                        {result.cropFactorKc}
                      </span>
                      <span className="text-[10px] text-slate-400 block">FAO-56 / TNAU</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        {pageT.waterDemandLabel}
                      </span>
                      <span className="font-extrabold text-slate-800 text-sm">
                        {result.cropWaterDemandMm} mm/day
                      </span>
                      <span className="text-[10px] text-slate-400 block">ETc = ET₀ × Kc</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        ET₀ Reference
                      </span>
                      <span className="font-extrabold text-blue-700 text-sm">
                        {result.referenceEtoMmDay ?? 5.0} mm/day
                      </span>
                      <span className="text-[10px] text-slate-400 block">Open-Meteo Penman</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        {pageT.totalVolumeLabel}
                      </span>
                      <span className="font-extrabold text-emerald-800 text-sm">
                        ~{(result.totalEstimatedLiters ?? result.estimatedLitersPerAcre).toLocaleString()} Litres
                      </span>
                      <span className="text-[10px] text-slate-500 block">
                        for {result.fieldAreaAcres ?? fieldArea} Acres (~{result.estimatedLitersPerAcre.toLocaleString()} L/Acre)
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 p-3 rounded-xl bg-amber-100/70 border border-amber-300 text-xs text-amber-900">
                    <p className="font-bold">
                      {language === 'ta'
                        ? 'தரவு முழுமையடையாததால் துல்லியமான பாசன அளவு தவிர்க்கப்பட்டுள்ளது.'
                        : 'Precise irrigation volume was omitted because critical agronomic parameters were missing.'}
                    </p>
                  </div>
                )}

                {/* Structured Reasoning & Observations */}
                <div className="mt-4 pt-3 border-t border-black/10 text-xs">
                  <h5 className="font-bold text-slate-800 mb-1.5">{pageT.rationaleTitle}</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed">
                    {(language === 'ta' ? result.reasonsTa : result.reasonsEn).map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* TNAU Paddy Water Protocol Card (Rendered for Paddy crops) */}
              {result.paddySpecificNotesEn && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-xs shadow-xs space-y-1.5">
                  <div className="flex items-center gap-2 text-emerald-900 font-bold">
                    <Sprout className="w-4 h-4 text-emerald-600" />
                    <span>{pageT.paddyWaterProtocolTitle}</span>
                  </div>
                  <p className="text-emerald-950 leading-relaxed">
                    {language === 'ta' ? result.paddySpecificNotesTa : result.paddySpecificNotesEn}
                  </p>
                  <p className="text-[10px] text-emerald-700 font-medium">
                    {language === 'ta'
                      ? 'பாத்தி முறை நீர்ப்பாசனம் பராமரிக்கப்படுகிறது. TNAU மாற்று நனைத்தல் & காயவைத்தல் (AWD) முறை 25% நீரை சேமிக்கும்.'
                      : 'Preserves selected Controlled Basin Flooding. TNAU Alternate Wetting & Drying (AWD) reduces water use by 25%.'}
                  </p>
                </div>
              )}

              {/* Units Explanation Card (1 mm * 1 m² = 1 L; 1 mm * 1 acre = 4,047 L) */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1">
                <div className="font-bold text-slate-800 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-blue-600" />
                  <span>{pageT.unitExplanationTitle}</span>
                </div>
                <p className="leading-relaxed">
                  {language === 'ta'
                    ? result.unitExplanationTa || '1 சதுர மீட்டர் பரப்பில் 1 மிமீ நீர் ஆழம் என்பது 1 லிட்டர் ஆகும் (1 மிமீ × 1 ச.மீ = 1 லிட்டர்). 1 ஏக்கர் பயிர் நிலத்திற்கு (4,047 ச.மீ), 1 மிமீ ஆழம் 4,047 லிட்டர் நீருக்கு சமம்.'
                    : result.unitExplanationEn || '1 mm depth of water over 1 square metre equals 1 litre (1 mm × 1 m² = 1 L). Across 1 cultivated acre (4,047 m²), 1 mm depth equals 4,047 litres.'}
                </p>
              </div>

              {/* Confidence, Limitations & Assumptions Notice */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-bold text-slate-800 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-600" />
                    {pageT.limitationsTitle}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {result.weatherTimestamp || weather?.lastUpdated || 'Current Observation'}
                  </span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-600 leading-relaxed">
                  {(language === 'ta' ? (result.limitationsTa || []) : (result.limitationsEn || [])).map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              </div>

              {/* Mandatory Advisory & No Physical Control Notice */}
              <div className="p-3.5 rounded-xl bg-slate-100 border border-slate-300 text-[11px] text-slate-600 leading-relaxed space-y-1">
                <p className="font-bold text-slate-800 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{pageT.noHardwareControlBanner}</span>
                </p>
                <p className="text-slate-500">
                  {language === 'ta' ? result.disclaimerTa : result.disclaimerEn}
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

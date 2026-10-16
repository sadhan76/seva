import React, { useState, useEffect, useRef } from 'react';
import {
  CloudSun,
  Sun,
  Cloud,
  CloudDrizzle,
  CloudRain,
  CloudLightning,
  CloudFog,
  MapPin,
  RefreshCw,
  Droplets,
  Wind,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Sparkles,
  Loader2,
  Info,
  AlertCircle,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getWeatherApi,
  getWeatherDistrictsApi,
  type WeatherApiResponse,
  type WeatherDistrict,
} from '../../services/api';

const DEFAULT_DISTRICTS: WeatherDistrict[] = [
  { key: 'thanjavur', name: 'Thanjavur', nameTa: 'தஞ்சாவூர்', zone: 'Cauvery Delta' },
  { key: 'tiruvarur', name: 'Tiruvarur', nameTa: 'திருவாரூர்', zone: 'Cauvery Delta' },
  { key: 'nagapattinam', name: 'Nagapattinam', nameTa: 'நாகப்பட்டினம்', zone: 'Cauvery Delta' },
  { key: 'tiruchirappalli', name: 'Tiruchirappalli', nameTa: 'திருச்சிராப்பள்ளி', zone: 'Cauvery Delta' },
  { key: 'madurai', name: 'Madurai', nameTa: 'மதுரை', zone: 'Southern' },
  { key: 'coimbatore', name: 'Coimbatore', nameTa: 'கோயம்புத்தூர்', zone: 'Western' },
  { key: 'erode', name: 'Erode', nameTa: 'ஈரோடு', zone: 'Western' },
  { key: 'salem', name: 'Salem', nameTa: 'சேலம்', zone: 'North-Western' },
  { key: 'cuddalore', name: 'Cuddalore', nameTa: 'கடலூர்', zone: 'North-Eastern' },
  { key: 'tirunelveli', name: 'Tirunelveli', nameTa: 'திருநெல்வேலி', zone: 'Southern' },
  { key: 'dharmapuri', name: 'Dharmapuri', nameTa: 'தர்மபுரி', zone: 'North-Western' },
  { key: 'chennai', name: 'Chennai', nameTa: 'சென்னை', zone: 'Coastal' },
];

interface WeatherViewProps {
  registeredDistrict?: string;
  onNavigateToProfile?: () => void;
}

export const WeatherView: React.FC<WeatherViewProps> = ({
  registeredDistrict: propDistrict,
  onNavigateToProfile,
}) => {
  const { t, language } = useLanguage();
  const { user } = useAuth();

  // Load the authenticated farmer's registered district
  const registeredDistrictRaw = propDistrict || user?.district || '';
  const registeredDistrictKey = registeredDistrictRaw.trim().toLowerCase();

  const [districts, setDistricts] = useState<WeatherDistrict[]>(DEFAULT_DISTRICTS);
  // Default Target District to registered district. If no district, do not silently select Thanjavur
  const [selectedDistrict, setSelectedDistrict] = useState<string>(() => registeredDistrictKey || '');
  const [weatherData, setWeatherData] = useState<WeatherApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent overlapping in-flight requests
  const isFetchingRef = useRef<boolean>(false);

  // Load districts list from backend
  useEffect(() => {
    let isMounted = true;
    async function loadDistricts() {
      try {
        const list = await getWeatherDistrictsApi();
        if (isMounted && list && list.length > 0) {
          setDistricts(list);
        }
      } catch {
        // Keep DEFAULT_DISTRICTS fallback
      }
    }
    loadDistricts();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch weather for district with overlapping request lock
  const fetchWeather = async (dist: string, isRefresh: boolean = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const res = await getWeatherApi(dist);
      setWeatherData(res);
      if (res.error && !res.isLive && !res.isCached) {
        setError(res.error);
      }
    } catch (err: any) {
      const msg = err.message || 'Failed to fetch weather data from Open-Meteo.';
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
      isFetchingRef.current = false;
    }
  };

  // Synchronize default district when farmer profile updates or user switches
  useEffect(() => {
    if (registeredDistrictKey) {
      setSelectedDistrict(registeredDistrictKey);
    } else {
      setSelectedDistrict('');
    }
  }, [registeredDistrictKey]);

  useEffect(() => {
    if (selectedDistrict) {
      fetchWeather(selectedDistrict, false);
    } else {
      setWeatherData(null);
      setLoading(false);
    }
  }, [selectedDistrict]);

  const handleRefresh = () => {
    if (!refreshing && !loading && selectedDistrict) {
      fetchWeather(selectedDistrict, true);
    }
  };

  const currentDistObj = districts.find((d) => d.key === selectedDistrict);
  const registeredDistObj = districts.find((d) => d.key === registeredDistrictKey);
  const isTemporarySelection = Boolean(
    registeredDistrictKey &&
    selectedDistrict &&
    selectedDistrict !== registeredDistrictKey
  );

  // Dynamic WMO Weather Icon helper
  const renderWeatherIcon = (iconKey?: string, className: string = 'w-10 h-10') => {
    switch (iconKey) {
      case 'sun':
        return <Sun className={`${className} text-amber-500`} />;
      case 'cloud-sun':
        return <CloudSun className={`${className} text-amber-500`} />;
      case 'cloud':
        return <Cloud className={`${className} text-slate-500`} />;
      case 'cloud-drizzle':
        return <CloudDrizzle className={`${className} text-blue-400`} />;
      case 'cloud-rain':
        return <CloudRain className={`${className} text-blue-600`} />;
      case 'cloud-lightning':
        return <CloudLightning className={`${className} text-purple-600`} />;
      case 'cloud-fog':
        return <CloudFog className={`${className} text-slate-400`} />;
      default:
        return <CloudSun className={`${className} text-amber-500`} />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.weather}
        subtitle={
          language === 'ta'
            ? 'தமிழ்நாடு மாவட்ட வாரியான நேரடி வேளாண் காலநிலை மற்றும் தெளிப்பு ஆலோசனை'
            : 'Localized Microclimate & Spraying Advisory for Tamil Nadu Agro-Climatic Zones'
        }
        icon={<CloudSun className="w-5 h-5 text-amber-500" />}
        headerAction={
          weatherData?.isCached ? (
            <Badge variant="amber" dot>
              {language === 'ta' ? 'சேமிக்கப்பட்ட தரவு' : 'Cached Data'}
            </Badge>
          ) : error ? (
            <Badge variant="rose" dot>
              {language === 'ta' ? 'இணைப்பு பிழை' : 'Service Offline'}
            </Badge>
          ) : null
        }
      >
        <div className="space-y-6">
          {/* Missing District Alert if farmer has not set district */}
          {!registeredDistrictKey && (
            <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">
                    {language === 'ta' ? 'பண்ணை மாவட்டம் அமைக்கப்படவில்லை' : 'Registered Farm District Not Set'}
                  </p>
                  <p className="mt-0.5 text-amber-800">
                    {language === 'ta'
                      ? 'உங்கள் சுயவிவரத்தில் பண்ணை மாவட்டம் பதிவு செய்யப்படவில்லை. நேரடி வானிலையைக் காண கீழே ஒரு மாவட்டத்தைத் தேர்ந்தெடுக்கவும் அல்லது உங்கள் சுயவிவரத்தில் மாவட்டத்தை அமைக்கவும்.'
                      : 'Your farm profile does not have a registered district yet. Please select a district below or complete your farm profile to set your home district.'}
                  </p>
                </div>
              </div>
              {onNavigateToProfile && (
                <button
                  type="button"
                  onClick={onNavigateToProfile}
                  className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-xs shrink-0 shadow-2xs"
                >
                  {language === 'ta' ? 'சுயவிவரத்தை நிரப்புக' : 'Complete Profile'}
                </button>
              )}
            </div>
          )}

          {/* Distinguish registered district vs temporary selection */}
          {isTemporarySelection ? (
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 p-3 rounded-2xl bg-amber-50/90 border border-amber-200/90 text-xs text-amber-900">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-amber-600 shrink-0" />
                <span>
                  <strong>{language === 'ta' ? 'தற்காலிக வானிலை தேர்வு: ' : 'Temporary Weather Selection: '}</strong>
                  <span className="font-bold text-slate-800">{currentDistObj?.name || selectedDistrict}</span>
                  <span className="text-slate-500 ml-2">
                    ({language === 'ta' ? 'உங்கள் பதிவு செய்யப்பட்ட மாவட்டம்: ' : 'Registered Farm District: '}
                    <strong className="text-emerald-800">{registeredDistObj?.name || registeredDistrictRaw}</strong>)
                  </span>
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDistrict(registeredDistrictKey)}
                className="px-2.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-2xs transition-all active:scale-95 shrink-0"
              >
                {language === 'ta' ? 'என் மாவட்டத்திற்கு திரும்பு ↺' : 'Reset to My District ↺'}
              </button>
            </div>
          ) : registeredDistrictKey && selectedDistrict === registeredDistrictKey ? (
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 px-3.5 py-2 rounded-2xl border border-emerald-200/80">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                {language === 'ta'
                  ? `உங்கள் பதிவு செய்யப்பட்ட மாவட்டம்: ${currentDistObj?.nameTa || registeredDistrictRaw} (${currentDistObj?.zone || 'வேளாண் மண்டலம்'})`
                  : `Your Registered Farm District: ${currentDistObj?.name || registeredDistrictRaw} (${currentDistObj?.zone || 'Agro Zone'})`}
              </span>
            </div>
          ) : null}

          {/* District Selection Bar & Live Status */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-200/90 rounded-2xl">
            <div className="flex items-center gap-2 flex-1">
              <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
              <label htmlFor="district-select" className="text-xs font-bold text-slate-700 shrink-0">
                {language === 'ta' ? 'மாவட்டம்:' : 'Target District:'}
              </label>
              <select
                id="district-select"
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                disabled={loading || refreshing}
                className="w-full sm:w-64 px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-60"
              >
                {!registeredDistrictKey && (
                  <option value="">
                    {language === 'ta' ? '-- மாவட்டத்தைத் தேர்ந்தெடுக்கவும் --' : '-- Select a District --'}
                  </option>
                )}
                {districts.map((d) => (
                  <option key={d.key} value={d.key}>
                    {d.name} ({d.nameTa}) • {d.zone}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 justify-end">
              <button
                type="button"
                id="weather-refresh-button"
                onClick={handleRefresh}
                disabled={refreshing || loading || !selectedDistrict}
                className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 flex items-center gap-1.5 shadow-2xs transition-all active:scale-95 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                <span>{language === 'ta' ? 'புதுப்பி' : 'Refresh'}</span>
              </button>
            </div>
          </div>

          {/* Cached Warning Banner if showing offline cache */}
          {weatherData?.isCached && (
            <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 flex items-center gap-2.5 text-xs text-amber-900">
              <Info className="w-4 h-4 text-amber-600 shrink-0" />
              <p className="flex-1">
                <strong>{language === 'ta' ? 'சேமிக்கப்பட்ட தரவு அறிவிப்பு: ' : 'Cached Data Notice: '}</strong>
                {weatherData.cacheNotice ||
                  (language === 'ta'
                    ? 'முந்தைய வானிலை தரவு காட்டப்படுகிறது. நேரடி மீட்டோ இணைப்பு கிடைத்ததும் தானாக புதுப்பிக்கப்படும்.'
                    : 'Displaying recently cached observation. Live feed will resume as soon as the network reconnects.')}
              </p>
            </div>
          )}

          {/* Empty Prompt if no district selected */}
          {!selectedDistrict && (
            <div className="p-8 text-center text-slate-500 bg-slate-50 border border-dashed border-slate-200 rounded-3xl space-y-2">
              <CloudSun className="w-10 h-10 text-emerald-600/70 mx-auto" />
              <p className="font-bold text-sm text-slate-700">
                {language === 'ta' ? 'வானிலை பார்க்க மாவட்டத்தைத் தேர்ந்தெடுக்கவும்' : 'Select a District to View Weather'}
              </p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                {language === 'ta'
                  ? 'மேலே உள்ள பட்டியலில் இருந்து உங்கள் மாவட்டத்தைத் தேர்ந்தெடுக்கவும். வேளாண் வானிலை தானாக காட்டப்படும்.'
                  : 'Please choose your target district from the dropdown above to load live local agro-meteorological observations.'}
              </p>
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold">
                {language === 'ta'
                  ? 'நேரடி வேளாண் வானிலைத் தகவல்கள் பெறப்படுகின்றன...'
                  : 'Retrieving live agro-meteorological metrics...'}
              </p>
            </div>
          ) : error && !weatherData ? (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center space-y-2">
              <AlertCircle className="w-7 h-7 mx-auto text-rose-600" />
              <p className="font-bold text-sm">
                {language === 'ta' ? 'வானிலை தரவை பெற முடியவில்லை' : 'Unable to Load Live Weather'}
              </p>
              <p className="text-slate-600">{error}</p>
              <p className="text-[11px] text-slate-500">
                {language === 'ta'
                  ? 'போலி மதிப்புகள் காட்டப்படாது. இணைய இணைப்பை சரிபார்த்து மீண்டும் முயற்சிக்கவும்.'
                  : 'Fabricated values are never shown. Please verify network access and tap Refresh.'}
              </p>
              <button
                type="button"
                onClick={handleRefresh}
                className="mt-2 px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-xs"
              >
                {language === 'ta' ? 'மீண்டும் முயற்சி செய்' : 'Retry'}
              </button>
            </div>
          ) : weatherData ? (
            <>
              {/* Primary Current Weather Banner */}
              <div className="flex flex-col md:flex-row items-center justify-between p-6 rounded-3xl bg-gradient-to-br from-emerald-500/10 via-amber-500/10 to-teal-500/10 border border-emerald-200/80 gap-6 shadow-xs">
                <div className="flex items-center gap-5 w-full md:w-auto">
                  <div className="w-18 h-18 rounded-3xl bg-white shadow-md border border-amber-100 flex items-center justify-center shrink-0">
                    {renderWeatherIcon(weatherData.weatherIcon, 'w-11 h-11')}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight">
                        {weatherData.temperatureC}°C
                      </span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">
                        {currentDistObj?.zone || weatherData.zone || 'Delta Zone'}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-slate-800 mt-1">
                      {language === 'ta' ? weatherData.condition_ta : weatherData.condition}
                    </p>
                    <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                      <span>
                        {weatherData.district} ({weatherData.district_ta})
                      </span>
                      {weatherData.coordinates && (
                        <span className="text-[11px] text-slate-400">
                          • {weatherData.coordinates.lat.toFixed(2)}°N, {weatherData.coordinates.lon.toFixed(2)}°E
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* 3 Metrics: Humidity, Rain Prob, Wind */}
                <div className="grid grid-cols-3 gap-2 sm:gap-3 w-full md:w-auto">
                  <div className="bg-white/90 backdrop-blur-xs p-3 rounded-2xl border border-slate-200/80 text-center shadow-xs">
                    <Droplets className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      {language === 'ta' ? 'ஈரப்பதம்' : 'Humidity'}
                    </p>
                    <p className="text-sm sm:text-base font-extrabold text-slate-800 mt-0.5">
                      {weatherData.humidity}%
                    </p>
                  </div>
                  <div className="bg-white/90 backdrop-blur-xs p-3 rounded-2xl border border-slate-200/80 text-center shadow-xs">
                    <CloudRain className="w-4 h-4 text-indigo-500 mx-auto mb-1" />
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      {language === 'ta' ? 'மழை வாய்ப்பு' : 'Rain Prob'}
                    </p>
                    <p className="text-sm sm:text-base font-extrabold text-slate-800 mt-0.5">
                      {weatherData.rainfallChance}%
                    </p>
                  </div>
                  <div className="bg-white/90 backdrop-blur-xs p-3 rounded-2xl border border-slate-200/80 text-center shadow-xs">
                    <Wind className="w-4 h-4 text-teal-600 mx-auto mb-1" />
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      {language === 'ta' ? 'காற்று வேகம்' : 'Wind Speed'}
                    </p>
                    <p className="text-sm sm:text-base font-extrabold text-slate-800 mt-0.5">
                      {weatherData.windSpeedKmh} <span className="text-[10px] font-normal">km/h</span>
                    </p>
                  </div>
                </div>
              </div>

              {/* Weather Observation & Last Updated Timestamps */}
              <div className="px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-slate-700">
                    {language === 'ta' ? 'கணிப்பு நேரம் (IST): ' : 'Observation Time (IST): '}
                  </span>
                  <span className="font-semibold text-slate-900">
                    {weatherData.observationTime || 'Unavailable'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 sm:text-right">
                  <span className="font-bold text-slate-700">
                    {language === 'ta' ? 'கடைசி புதுப்பிப்பு: ' : 'Last Updated: '}
                  </span>
                  <span className="font-semibold text-slate-900">
                    {weatherData.lastUpdated || weatherData.updatedAt || 'Unavailable'}
                  </span>
                </div>
              </div>

              {/* Agricultural Spraying Advisory */}
              {weatherData.sprayingAdvisory && (
                <div
                  className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                    weatherData.sprayingAdvisory.status === 'optimal'
                      ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
                      : weatherData.sprayingAdvisory.status === 'not_recommended'
                      ? 'bg-rose-50/70 border-rose-300 text-rose-950'
                      : 'bg-amber-50/70 border-amber-300 text-amber-950'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    {weatherData.sprayingAdvisory.status === 'optimal' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                    )}
                    <h4 className="text-sm font-bold">
                      {language === 'ta'
                        ? weatherData.sprayingAdvisory.title_ta
                        : weatherData.sprayingAdvisory.title_en}
                    </h4>
                    <span
                      className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase ml-auto ${
                        weatherData.sprayingAdvisory.status === 'optimal'
                          ? 'bg-emerald-200 text-emerald-900'
                          : weatherData.sprayingAdvisory.status === 'not_recommended'
                          ? 'bg-rose-200 text-rose-900'
                          : 'bg-amber-200 text-amber-900'
                      }`}
                    >
                      {weatherData.sprayingAdvisory.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed mt-1">
                    {language === 'ta'
                      ? weatherData.sprayingAdvisory.reason_ta
                      : weatherData.sprayingAdvisory.reason_en}
                  </p>
                  <div className="mt-2.5 pt-2 border-t border-slate-200/60 text-xs font-semibold flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                    <span>
                      {language === 'ta' ? 'பரிந்துரைக்கப்படும் நேரம்: ' : 'Favorable Window: '}
                      <strong className="font-extrabold">{weatherData.sprayingAdvisory.favorable_window}</strong>
                    </span>
                  </div>
                  {/* Official Agricultural Advisory Disclaimer */}
                  <div className="mt-2 text-[10px] text-slate-500 italic border-t border-slate-200/50 pt-1.5">
                    {language === 'ta'
                      ? weatherData.sprayingAdvisory.disclaimer_ta ||
                        'அறிவிப்பு: இது வானிலை அடிப்படையிலான வழிகாட்டல் மட்டுமே. மருந்து லேபிள் வழிமுறைகளையும் தமிழ்நாடு வேளாண் பல்கலைக்கழக (TNAU) பரிந்துரைகளையும் பின்பற்றவும்.'
                      : weatherData.sprayingAdvisory.disclaimer_en ||
                        'Notice: Microclimate forecast advisory only. Always follow pesticide/fungicide label instructions and official TNAU/KVK agricultural extension recommendations.'}
                  </div>
                </div>
              )}

              {/* 5-Day Microclimate Forecast */}
              {weatherData.forecast && weatherData.forecast.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    {language === 'ta' ? '5 நாள் வானிலை முன்னறிவிப்பு' : '5-Day Agro-Weather Forecast'}
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                    {weatherData.forecast.map((day, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-white border border-slate-200/90 text-center shadow-xs hover:border-emerald-300 transition-all flex flex-col justify-between"
                      >
                        <div>
                          <p className="text-xs font-bold text-slate-800 truncate">
                            {language === 'ta' && day.day_ta ? day.day_ta : day.day}
                          </p>
                          {day.date && (
                            <p className="text-[10px] text-slate-400 font-medium">{day.date}</p>
                          )}
                          <div className="my-1.5 flex justify-center">
                            {renderWeatherIcon(day.weatherIcon, 'w-7 h-7')}
                          </div>
                          <div className="text-sm font-black text-slate-900 tracking-tight">
                            {day.temp}
                          </div>
                          <p className="text-[10px] text-slate-500 truncate mt-0.5">
                            {language === 'ta' && day.condition_ta ? day.condition_ta : day.condition}
                          </p>
                        </div>
                        <div className="mt-2 space-y-1">
                          <div className="text-[10px] font-bold text-indigo-700 bg-indigo-50 py-0.5 px-1 rounded-md border border-indigo-100 flex items-center justify-center gap-1">
                            <CloudRain className="w-3 h-3 text-indigo-500 shrink-0" />
                            <span>{day.rainProb}% rain</span>
                          </div>
                          {day.precipMm !== undefined && day.precipMm > 0 && (
                            <p className="text-[9px] text-slate-400 font-medium">
                              {day.precipMm} mm expected
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </Card>
    </div>
  );
};

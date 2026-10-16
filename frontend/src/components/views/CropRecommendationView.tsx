import React, { useState, useEffect } from 'react';
import {
  Sprout,
  MapPin,
  Layers,
  Calendar,
  Droplet,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  recommendCropsApi,
  type CropRecommendResponse,
} from '../../services/api';

const DISTRICTS = [
  'Thanjavur',
  'Tiruvarur',
  'Nagapattinam',
  'Tiruchirappalli',
  'Madurai',
  'Coimbatore',
  'Erode',
  'Salem',
  'Cuddalore',
  'Tirunelveli',
  'Dharmapuri',
];

const SOILS = [
  'Alluvial Clay Loam',
  'Clay Loam',
  'Red Loam',
  'Sandy Loam',
  'Black Cotton Soil',
];

const SEASONS = [
  'Samba (Aug - Jan)',
  'Thaladi (Sep - Feb)',
  'Kuruvai / Kharif (Jun - Sep)',
  'Rice Fallow (Jan - Apr)',
  'Summer / Chithirai Pattam (Feb - May)',
];

const WATER_LEVELS = [
  'High (Assured Canal / River)',
  'Medium (Borewell / Open Well)',
  'Low (Rainfed / Limited Moisture)',
];

export const CropRecommendationView: React.FC = () => {
  const { t, language } = useLanguage();

  const [district, setDistrict] = useState<string>('Thanjavur');
  const [soilType, setSoilType] = useState<string>('Alluvial Clay Loam');
  const [season, setSeason] = useState<string>('Samba (Aug - Jan)');
  const [waterAvailability, setWaterAvailability] = useState<string>('High');
  const [cropPreference, setCropPreference] = useState<string>('All');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CropRecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await recommendCropsApi({
        district,
        soilType,
        season,
        waterAvailability: waterAvailability.split(' ')[0], // 'High', 'Medium', 'Low'
        cropPreference: cropPreference === 'All' ? undefined : cropPreference,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve crop recommendations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRecommendations();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.recommendations}
        subtitle={
          language === 'ta'
            ? 'மண் வளம், பருவகாலம் மற்றும் நீர் இருப்பு அடிப்படையிலான பயிர் சுழற்சி ஆலோசனை'
            : 'Agro-Climatic Crop Rotation & Variety Advisory (Cauvery Delta & Tamil Nadu Zones)'
        }
        icon={<Sprout className="w-5 h-5 text-emerald-600" />}
        headerAction={
          <Badge variant="emerald" dot>
            Tamil Nadu Agro-Climatic Matrix
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Input Configuration Form */}
          <form
            onSubmit={handleSubmit}
            className="p-4 sm:p-5 bg-slate-50 border border-slate-200/90 rounded-2xl space-y-4 text-xs"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* District */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  {language === 'ta' ? 'மாவட்டம்' : 'District'}
                </label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
                >
                  {DISTRICTS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Soil Type */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-600" />
                  {language === 'ta' ? 'மண் வகை' : 'Soil Type'}
                </label>
                <select
                  value={soilType}
                  onChange={(e) => setSoilType(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
                >
                  {SOILS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Season */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  {language === 'ta' ? 'பருவகாலம்' : 'Season'}
                </label>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
                >
                  {SEASONS.map((sn) => (
                    <option key={sn} value={sn}>
                      {sn}
                    </option>
                  ))}
                </select>
              </div>

              {/* Water Availability */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Droplet className="w-3.5 h-3.5 text-teal-600" />
                  {language === 'ta' ? 'நீர் வசதி' : 'Water Availability'}
                </label>
                <select
                  value={waterAvailability}
                  onChange={(e) => setWaterAvailability(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-emerald-500/20"
                >
                  {WATER_LEVELS.map((w) => (
                    <option key={w} value={w.split(' ')[0]}>
                      {w}
                    </option>
                  ))}
                </select>
              </div>

              {/* Crop Preferences */}
              <div className="sm:col-span-2 lg:col-span-2">
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Filter className="w-3.5 h-3.5 text-slate-500" />
                  {language === 'ta' ? 'விருப்பப் பயிர் பிரிவு' : 'Crop Category Preference'}
                </label>
                <div className="flex flex-wrap items-center gap-2">
                  {['All', 'Cereals', 'Pulses', 'Oilseeds'].map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setCropPreference(cat)}
                      className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                        cropPreference === cat
                          ? 'bg-emerald-600 text-white shadow-2xs'
                          : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                  <button
                    type="submit"
                    disabled={loading}
                    className="ml-auto px-4 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold rounded-xl shadow-xs flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="w-3.5 h-3.5" />
                    )}
                    <span>{language === 'ta' ? 'பரிந்துரைக்க' : 'Find Best Crops'}</span>
                  </button>
                </div>
              </div>
            </div>
          </form>

          {/* Error Banner */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              {error}
            </div>
          )}

          {/* Missing Information Notice Box */}
          {result?.missingInformationNotice && (
            <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Missing Laboratory Parameters: </span>
                <span>{result.missingInformationNotice}</span>
              </div>
            </div>
          )}

          {/* Results List */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold">
                Computing agronomic suitability and rotation patterns...
              </p>
            </div>
          ) : result && result.recommendations.length > 0 ? (
            <div className="space-y-4">
              {result.recommendations.map((rec, i) => (
                <div
                  key={i}
                  className={`p-5 rounded-2xl border transition-all ${
                    rec.isTopPick
                      ? 'bg-emerald-50/40 border-emerald-300 ring-2 ring-emerald-400/20'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-base font-extrabold text-slate-900">
                          {language === 'ta' ? rec.cropTa : rec.crop}
                        </h4>
                        {rec.isTopPick && (
                          <span className="text-[10px] font-extrabold uppercase tracking-wider bg-emerald-600 text-white px-2 py-0.5 rounded-full">
                            Top Agro-Climatic Match
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Category: <strong className="text-slate-700">{rec.category}</strong> • Duration: {rec.durationDays} Days • Water Need: {rec.waterNeed}
                      </p>
                    </div>

                    <div className="text-left sm:text-right">
                      <span className="text-xs font-extrabold text-emerald-800 bg-emerald-100 border border-emerald-200 px-2.5 py-1 rounded-lg">
                        {rec.matchScore} Agro Match
                      </span>
                    </div>
                  </div>

                  {/* Yield range (strictly non-guaranteed) */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-3 text-xs bg-white/90 p-3 rounded-xl border border-slate-100">
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        Indicative Yield Range
                      </span>
                      <span className="font-bold text-slate-800">{rec.expectedYieldRange}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        Water Demand
                      </span>
                      <span className="font-bold text-slate-700">{rec.waterNeed}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] font-bold uppercase">
                        Duration
                      </span>
                      <span className="font-bold text-slate-700">{rec.durationDays} Days</span>
                    </div>
                  </div>

                  {/* Why Suitable Explanation */}
                  <div className="mt-3 text-xs text-slate-700 leading-relaxed">
                    <p className="font-bold text-slate-900 flex items-center gap-1.5 mb-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      {language === 'ta' ? 'பொருத்தத்திற்கான காரணங்கள்:' : 'Agronomic Suitability Rationale:'}
                    </p>
                    <p className="pl-5 text-slate-600">
                      {language === 'ta' ? rec.whySuitableTa : rec.whySuitableEn}
                    </p>
                  </div>

                  {/* Management Tips */}
                  <div className="mt-2.5 pt-2.5 border-t border-slate-100 text-xs text-slate-600">
                    <span className="font-bold text-emerald-900">Key Management Tip: </span>
                    <span>{language === 'ta' ? rec.managementTipTa : rec.managementTipEn}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400">
              <p className="text-sm font-semibold">No crop recommendations matching current criteria.</p>
              <p className="text-xs text-slate-400 mt-1">Try adjusting the water availability or crop category filter.</p>
            </div>
          )}

          {/* Assumptions & Non-Guaranteed Disclaimer */}
          {result && (
            <div className="space-y-2 pt-2 border-t border-slate-200">
              {result.assumptions && result.assumptions.length > 0 && (
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
                  <h5 className="font-bold text-slate-800 mb-1 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-slate-500" />
                    Model Assumptions:
                  </h5>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-slate-500">
                    {result.assumptions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500 leading-relaxed flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p>{result.disclaimer}</p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

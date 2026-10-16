import React, { useState } from 'react';
import {
  Droplets,
  Sprout,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  CloudRain,
  Info,
  Loader2,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  calculateIrrigationApi,
  type IrrigationCalculateResponse,
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

export const IrrigationView: React.FC = () => {
  const { t, language } = useLanguage();

  const [crop, setCrop] = useState<string>(CROPS[0]);
  const [growthStage, setGrowthStage] = useState<string>(GROWTH_STAGES[1]);
  const [soilType, setSoilType] = useState<string>(SOIL_TYPES[0]);
  const [irrigationMethod, setIrrigationMethod] = useState<string>(IRRIGATION_METHODS[0]);
  const [soilMoisture, setSoilMoisture] = useState<string>('52');
  const [recentRain, setRecentRain] = useState<string>('0');
  const [forecastRain, setForecastRain] = useState<string>('20');

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<IrrigationCalculateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await calculateIrrigationApi({
        crop,
        growthStage,
        soilType,
        irrigationMethod,
        soilMoisturePercent: soilMoisture ? parseFloat(soilMoisture) : undefined,
        recentRainMm: recentRain ? parseFloat(recentRain) : 0,
        forecastRainChance: forecastRain ? parseFloat(forecastRain) : 20,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compute irrigation advisory.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.irrigation}
        subtitle={
          language === 'ta'
            ? 'மண் ஈரப்பதம் மற்றும் பயிர் காரணி (Kc) அடிப்படையிலான நீர்ப்பாசன வழிகாட்டுதல்'
            : 'Evapotranspiration & Soil Moisture Advisory (FAO-56 & TNAU Water Budgeting)'
        }
        icon={<Droplets className="w-5 h-5 text-blue-600" />}
        headerAction={
          <Badge variant="blue" dot>
            Agronomic Advisory
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Platform Truthfulness Notice */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-800">
                {language === 'ta'
                  ? 'வெளிப்படையான ஆலோசனை அறிவிப்பு'
                  : 'Transparent Advisory Framework (Non-Hardware Notice)'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? 'இந்த பரிந்துரைகள் பயிர் வகை, வளர்ச்சி நிலை, மண் வளம் மற்றும் வானிலை சமன்பாடுகளின் அடிப்படையில் கணக்கிடப்படுகிறது. களத்தில் உடல் ரீதியாக இணைக்கப்பட்ட மோட்டார் சுவிட்சுகள் அல்லது சென்சார் இணைப்புகள் எதுவும் கற்பனையாக காட்டப்படவில்லை.'
                  : 'Guidance is computed from physiological crop coefficients (Kc), soil retention properties, and weather forecast inputs. We do not invent simulated sensor readings or claim physical motor actuators are attached.'}
              </p>
            </div>
          </div>

          {/* Input Form */}
          <form onSubmit={handleCalculate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {/* 1. Crop Selection */}
              <div>
                <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  {language === 'ta' ? 'பயிர் வகை' : 'Crop Type'}
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
                  {language === 'ta' ? 'வளர்ச்சி நிலை' : 'Growth Stage'}
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
                  {language === 'ta' ? 'மண் வகை' : 'Soil Type'}
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
                  {language === 'ta' ? 'பாசன முறை' : 'Irrigation Method'}
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

              {/* 5. Soil Moisture % (Optional input) */}
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  {language === 'ta' ? 'மண் ஈரப்பதம் % (கிடைத்தால்)' : 'Available Soil Moisture % (If Measured)'}
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={soilMoisture}
                  onChange={(e) => setSoilMoisture(e.target.value)}
                  placeholder="e.g. 52 (Leave blank if unknown)"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                />
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Field gauge reading or ball-squeeze tactile test percentage.
                </span>
              </div>

              {/* 6. Forecast Rain Chance & Recent Rainfall */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-bold text-slate-700 mb-1 flex items-center gap-1">
                    <CloudRain className="w-3.5 h-3.5 text-indigo-500" />
                    {language === 'ta' ? 'மழை வாய்ப்பு (%)' : 'Rain Forecast (%)'}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={forecastRain}
                    onChange={(e) => setForecastRain(e.target.value)}
                    placeholder="e.g. 25"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    {language === 'ta' ? 'பெய்த மழை (மிமீ)' : 'Recent Rain (mm)'}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="500"
                    value={recentRain}
                    onChange={(e) => setRecentRain(e.target.value)}
                    placeholder="e.g. 0"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Calculating Water Requirement...
                </>
              ) : (
                <>
                  <span>
                    {language === 'ta' ? 'பாசன ஆலோசனையை பெறவும்' : 'Compute Irrigation Advisory'}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Error Banner */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
              {error}
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-4 pt-4 border-t border-slate-200/80">
              {/* Recommendation Banner */}
              <div
                className={`p-5 rounded-2xl border ${
                  result.status === 'delay'
                    ? 'bg-amber-50/80 border-amber-300 text-amber-950'
                    : result.status === 'adequate'
                    ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
                    : result.status === 'urgent'
                    ? 'bg-rose-50/80 border-rose-300 text-rose-950'
                    : 'bg-blue-50/80 border-blue-300 text-blue-950'
                }`}
              >
                <div className="flex items-center gap-2.5 mb-2">
                  {result.status === 'adequate' ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                  ) : result.status === 'delay' ? (
                    <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0" />
                  ) : (
                    <Droplets className="w-6 h-6 text-blue-600 shrink-0" />
                  )}
                  <div>
                    <h4 className="text-base font-extrabold tracking-tight">
                      {language === 'ta' ? result.recommendationTa : result.recommendationEn}
                    </h4>
                    <span className="text-[10px] font-bold uppercase tracking-wider opacity-75">
                      Status: {result.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* 3 Metric Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mt-4 text-xs bg-white/80 p-3 rounded-xl border border-black/5">
                  <div>
                    <span className="text-slate-400 block text-[10px] font-bold uppercase">
                      Crop Factor (Kc)
                    </span>
                    <span className="font-extrabold text-slate-800 text-sm">
                      {result.cropFactorKc}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] font-bold uppercase">
                      Daily Water Demand
                    </span>
                    <span className="font-extrabold text-slate-800 text-sm">
                      {result.cropWaterDemandMm} mm/day
                    </span>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <span className="text-slate-400 block text-[10px] font-bold uppercase">
                      Est. Volume / Acre
                    </span>
                    <span className="font-extrabold text-blue-700 text-sm">
                      ~{result.estimatedLitersPerAcre.toLocaleString()} Liters
                    </span>
                  </div>
                </div>

                {/* Structured Reasoning */}
                <div className="mt-4 pt-3 border-t border-black/10 text-xs">
                  <h5 className="font-bold text-slate-800 mb-1.5">
                    {language === 'ta' ? 'பரிந்துரைக்கான காரணங்கள்:' : 'Agronomic Rationale & Observations:'}
                  </h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed">
                    {(language === 'ta' ? result.reasonsTa : result.reasonsEn).map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Mandatory Advisory Notice */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500 leading-relaxed flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p>{language === 'ta' ? result.disclaimerTa : result.disclaimerEn}</p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

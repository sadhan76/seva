import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Briefcase,
  Leaf,
  Layers,
  Building,
  Package,
  Search,
  ExternalLink,
  Phone,
  Mail,
  ShieldCheck,
  Calendar,
  MapPin,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  ArrowRight,
  Info,
  Droplets,
  Sprout,
  X,
  DollarSign,
  TrendingUp,
  ShieldAlert,
  FileText,
  Hammer,
  Award,
  Store,
  Scale,
  CheckSquare,
  Compass
} from 'lucide-react';
import type { NavTab, FarmerSupportContent } from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { getFarmerSupportContent, getCropMasterGuide } from '../../services/api';

interface FarmerSupportHubViewProps {
  onNavigate?: (tab: NavTab) => void;
}

type SupportCategory = 
  | 'all'
  | 'training'
  | 'entrepreneurship'
  | 'organic'
  | 'special_operation'
  | 'protected_cultivation'
  | 'value_addition'
  | 'direct_market';

export const FarmerSupportHubView: React.FC<FarmerSupportHubViewProps> = ({ onNavigate }) => {
  const { language } = useLanguage();
  const isTa = language === 'ta';

  // State
  const [selectedCategory, setSelectedCategory] = useState<SupportCategory>('all');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [selectedState, setSelectedState] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [items, setItems] = useState<FarmerSupportContent[]>([]);
  const [districtsList, setDistrictsList] = useState<string[]>(['All']);
  const [statesList, setStatesList] = useState<string[]>(['All', 'Tamil Nadu', 'All-India']);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);
  const [hasStaleNotice, setHasStaleNotice] = useState<boolean>(false);

  // Detail Modal State
  const [selectedItemForDetail, setSelectedItemForDetail] = useState<FarmerSupportContent | null>(null);

  // Special Operation Crop Guide State
  const [selectedCropGuide, setSelectedCropGuide] = useState<'paddy' | 'groundnut' | 'tomato'>('paddy');
  const [activeCropGuideData, setActiveCropGuideData] = useState<FarmerSupportContent | null>(null);
  const [expandedStage, setExpandedStage] = useState<number | null>(1);

  // Fetch support items
  const loadContent = async () => {
    setIsLoading(true);
    setHasError(false);
    try {
      const data = await getFarmerSupportContent({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        district: selectedDistrict === 'All' ? undefined : selectedDistrict,
        state: selectedState === 'All' ? undefined : selectedState,
        search: searchQuery.trim() || undefined,
        activeOnly: true,
      });
      setItems(data.items || []);
      if (data.districts && data.districts.length > 0) {
        setDistrictsList(data.districts);
      }
      if (data.states && data.states.length > 0) {
        setStatesList(data.states);
      }
      setHasStaleNotice(data.hasStaleNotice || false);
    } catch (err) {
      console.error('Failed to load farmer support content:', err);
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadContent();
  }, [selectedCategory, selectedDistrict, selectedState]);

  // Load Special Operation crop guide when tab is active or crop selection changes
  useEffect(() => {
    if (selectedCategory === 'special_operation' || selectedCategory === 'all') {
      getCropMasterGuide(selectedCropGuide)
        .then((res) => setActiveCropGuideData(res))
        .catch((err) => console.warn('Could not fetch crop master guide:', err));
    }
  }, [selectedCategory, selectedCropGuide]);

  // Category Tabs Configuration (All 7 Sections)
  const categoryTabs: Array<{ id: SupportCategory; labelEn: string; labelTa: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'all', labelEn: 'All Resources', labelTa: 'அனைத்து சேவைகள்', icon: Layers },
    { id: 'training', labelEn: 'Farmer Training', labelTa: 'விவசாயிகள் களப்பயிற்சி', icon: GraduationCap },
    { id: 'entrepreneurship', labelEn: 'Agri Entrepreneurship', labelTa: 'வேளாண் தொழில்முனைவு', icon: Briefcase },
    { id: 'organic', labelEn: 'Organic Farming', labelTa: 'இயற்கை வேளாண்மை', icon: Leaf },
    { id: 'special_operation', labelEn: 'Special Operation', labelTa: 'முழு பயிர் வழிகாட்டல்', icon: Sprout },
    { id: 'protected_cultivation', labelEn: 'Protected Cultivation', labelTa: 'பசுமைக் குடில் & நிழல்வலை', icon: Building },
    { id: 'value_addition', labelEn: 'Value-Added Products', labelTa: 'மதிப்புக் கூட்டப்பட்ட பொருட்கள்', icon: Package },
    { id: 'direct_market', labelEn: 'Direct Market & e-NAM', labelTa: 'நேரடி சந்தை & e-NAM', icon: Store },
  ];

  // Helper to check if a date is older than 180 days
  const isDateOlderThan180Days = (dateStr?: string) => {
    if (!dateStr) return false;
    const itemDate = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((now.getTime() - itemDate.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays > 180;
  };

  // Helper to format days until date
  const getDaysUntil = (dateStr?: string) => {
    if (!dateStr) return null;
    const target = new Date(dateStr);
    const today = new Date();
    const diff = Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Card */}
      <div className="bg-gradient-to-r from-emerald-800 via-emerald-700 to-teal-800 text-white rounded-2xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 w-64 h-64 bg-white/5 rounded-full blur-2xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 text-xs font-semibold mb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-300" />
            {isTa ? '100% அதிகாரப்பூர்வ தமிழ்நாடு அரசு & TNAU அங்கீகாரம்' : '100% Verified Tamil Nadu Govt & TNAU Provenance'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            {isTa ? 'உழவர் வழிகாட்டல் மற்றும் ஆதரவு மையம்' : 'Farmer Support & Development Hub'}
          </h1>
          <p className="text-emerald-100 text-sm sm:text-base leading-relaxed">
            {isTa
              ? 'TNAU, ICAR-KVK, தமிழ்நாடு கரிமச் சான்றளிப்புத் துறை (TNOCD), TANHODA, NIFTEM-T, e-NAM மற்றும் NABARD ஆகியவற்றின் அதிகாரப்பூர்வ பயிற்சி, மானியம், நேரடி சந்தை மற்றும் தொழில் முனைவு வழிகாட்டுதல்கள்.'
              : 'Institutional practical training, agri-entrepreneurship models, organic farming certification, stage-by-stage crop journeys, protected polyhouse specs, value-addition blueprints, and e-NAM / direct market workflows.'}
          </p>
        </div>
      </div>

      {/* Stale Contact Review Advisory Banner */}
      {hasStaleNotice && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <p className="font-semibold">
              {isTa ? 'அதிகாரப்பூர்வ மறுஆய்வு எச்சரிக்கை' : 'Institutional Content Review Advisory'}
            </p>
            <p className="text-xs text-amber-700 mt-0.5">
              {isTa
                ? 'சில அரசு தொடர்பு மற்றும் அறிவிப்பு விவரங்கள் 180 நாட்களுக்கு முந்தையவை. சமீபத்திய தகவலை உறுதிசெய்ய அரசு உதவி மையத்தை (1800-425-1661) தொடர்பு கொள்ளவும்.'
                : 'Some institutional desk contacts were last verified over 180 days ago. Check the official source link or call the Kisan Call Centre at 1800-425-1661 for live confirmation.'}
            </p>
          </div>
        </div>
      )}

      {/* Category Pills Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {categoryTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = selectedCategory === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setSelectedCategory(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all whitespace-nowrap shrink-0 ${
                isActive
                  ? 'bg-emerald-700 text-white shadow-md shadow-emerald-700/20'
                  : 'bg-white text-slate-700 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-emerald-600'}`} />
              <span>{isTa ? tab.labelTa : tab.labelEn}</span>
            </button>
          );
        })}
      </div>

      {/* Search, State & District Filter Controls */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadContent()}
            placeholder={isTa ? 'பயிற்சி, தொழில் அல்லது சந்தையை தேடுக...' : 'Search course, idea, market or crop...'}
            className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full md:w-auto justify-end">
          {/* State Filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-semibold text-slate-600 flex items-center gap-1 shrink-0">
              <Building className="w-3.5 h-3.5 text-emerald-600" />
              {isTa ? 'மாநிலம்:' : 'State:'}
            </label>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
            >
              {statesList.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? (isTa ? 'அனைத்து மாநிலங்கள் (All)' : 'All States') : s}
                </option>
              ))}
            </select>
          </div>

          {/* District Filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-semibold text-slate-600 flex items-center gap-1 shrink-0">
              <MapPin className="w-3.5 h-3.5 text-emerald-600" />
              {isTa ? 'மாவட்டம்:' : 'District:'}
            </label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
            >
              {districtsList.map((d) => (
                <option key={d} value={d}>
                  {d === 'All' ? (isTa ? 'அனைத்து மாவட்டங்கள் (All)' : 'All Districts') : d}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadContent}
            title={isTa ? 'புதுப்பி' : 'Refresh'}
            className="p-2 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 border border-slate-200 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* SPECIAL OPERATION DEEP-DIVE SECTION */}
      {selectedCategory === 'special_operation' && (
        <div className="bg-white rounded-2xl border border-emerald-200 shadow-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                  {isTa ? 'சிறப்பு வழிகாட்டல்' : 'Special Operation'}
                </span>
                <span className="text-xs text-slate-500">TRRI Aduthurai & TNAU Master Blueprints</span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 mt-1">
                {isTa
                  ? 'விதைப்பு முதல் அறுவடை விற்பனை வரை — முழுமையான பயிர் சாகுபடி வழிகாட்டல்'
                  : 'Beginner-Friendly Crop Cultivation Journeys (Farm Prep to Harvest Selling)'}
              </h2>
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => onNavigate?.('special_operation')}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-700 to-teal-700 hover:from-emerald-800 hover:to-teal-800 text-white text-xs font-bold shadow-md flex items-center gap-2 transition-all"
                >
                  <Compass className="w-4 h-4 text-amber-300" />
                  <span>
                    {isTa
                      ? '10-படி ஊடாடும் கற்றல் பயணத்தைத் தொடங்கு (படிவங்கள், காலவரிசை & சான்றிதழ்)'
                      : 'Launch 10-Step Interactive Guided Journey (Checklists, Timeline & Certificate)'}
                  </span>
                  <ArrowRight className="w-4 h-4 text-emerald-200" />
                </button>
              </div>
            </div>

            {/* Crop Selector Switcher */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto gap-1">
              <button
                onClick={() => setSelectedCropGuide('paddy')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedCropGuide === 'paddy'
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'text-slate-600 hover:text-emerald-700'
                }`}
              >
                🌾 {isTa ? 'சம்பா நெல்' : 'Samba Paddy'}
              </button>
              <button
                onClick={() => setSelectedCropGuide('groundnut')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedCropGuide === 'groundnut'
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'text-slate-600 hover:text-emerald-700'
                }`}
              >
                🥜 {isTa ? 'நிலக்கடலை' : 'Rainfed Groundnut'}
              </button>
              <button
                onClick={() => setSelectedCropGuide('tomato')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedCropGuide === 'tomato'
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'text-slate-600 hover:text-emerald-700'
                }`}
              >
                🍅 {isTa ? 'தக்காளி' : 'Commercial Tomato'}
              </button>
            </div>
          </div>

          {activeCropGuideData && activeCropGuideData.cropGuideMeta && (
            <div className="space-y-6">
              {/* Meta Summary Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-emerald-50/70 border border-emerald-100">
                <div>
                  <div className="text-xs text-emerald-800 font-medium">{isTa ? 'பயிர் & ரகம்' : 'Crop & Season'}</div>
                  <div className="text-sm font-bold text-emerald-950">
                    {isTa ? activeCropGuideData.cropGuideMeta.cropNameTa : activeCropGuideData.cropGuideMeta.cropName}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-emerald-800 font-medium">{isTa ? 'சாகுபடி காலம்' : 'Duration'}</div>
                  <div className="text-sm font-bold text-emerald-950">
                    {activeCropGuideData.cropGuideMeta.durationDays} {isTa ? 'நாட்கள்' : 'Days'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-emerald-800 font-medium">{isTa ? 'பருவம்' : 'Optimal Season'}</div>
                  <div className="text-sm font-bold text-emerald-950">
                    {activeCropGuideData.cropGuideMeta.season || 'Samba / Rabi'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-emerald-800 font-medium">{isTa ? 'விற்பனை இணைப்பு' : 'Market Connect'}</div>
                  <div className="text-sm font-bold text-emerald-950 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    TNCSC DPC / Direct Market
                  </div>
                </div>
              </div>

              {/* Stage-by-Stage Accordion */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                  {isTa ? '5 தொடர் வளர்ச்சி நிலைகள் & களப் பணிகள்' : 'Sequential 5-Stage Crop Management Lifecycle'}
                </h3>
                {activeCropGuideData.cropGuideMeta.stages.map((stage) => {
                  const isExpanded = expandedStage === stage.stageNumber;
                  return (
                    <div
                      key={stage.stageNumber}
                      className="border border-slate-200 rounded-xl overflow-hidden transition-all bg-white"
                    >
                      <button
                        onClick={() => setExpandedStage(isExpanded ? null : stage.stageNumber)}
                        className={`w-full flex items-center justify-between p-4 text-left font-semibold text-sm transition-colors ${
                          isExpanded ? 'bg-emerald-50/80 text-emerald-900 border-b border-emerald-100' : 'hover:bg-slate-50 text-slate-800'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="w-7 h-7 rounded-full bg-emerald-700 text-white text-xs font-bold flex items-center justify-center shrink-0">
                            {stage.stageNumber}
                          </span>
                          <div>
                            <span className="font-bold text-slate-900">
                              {isTa ? stage.stageNameTa || stage.stageName : stage.stageName}
                            </span>
                            <span className="ml-2 text-xs text-emerald-700 font-medium bg-emerald-100 px-2 py-0.5 rounded-full">
                              {stage.daysRange}
                            </span>
                          </div>
                        </div>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-emerald-700" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </button>

                      {isExpanded && (
                        <div className="p-4 space-y-4 text-xs sm:text-sm text-slate-700">
                          {/* Key Activities Checklist */}
                          <div>
                            <div className="font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              {isTa ? 'முக்கிய களப் பணிகள்:' : 'Key Operational Activities:'}
                            </div>
                            <ul className="space-y-1.5 pl-6 list-disc text-slate-600">
                              {stage.keyActivities.map((act, i) => (
                                <li key={i}>{act}</li>
                              ))}
                            </ul>
                          </div>

                          {/* Water & Nutrient Grid */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                            {stage.waterManagement && (
                              <div className="p-3 rounded-lg bg-sky-50 border border-sky-100">
                                <div className="font-semibold text-sky-900 flex items-center gap-1 mb-1">
                                  <Droplets className="w-3.5 h-3.5 text-sky-600" />
                                  {isTa ? 'பாசன மேலாண்மை (AWD)' : 'Water Management (AWD)'}
                                </div>
                                <div className="text-sky-800 text-xs leading-relaxed">{stage.waterManagement}</div>
                              </div>
                            )}

                            {stage.nutrientRegime && (
                              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                                <div className="font-semibold text-emerald-900 flex items-center gap-1 mb-1">
                                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                                  {isTa ? 'உர மேலாண்மை' : 'Nutrient Protocol'}
                                </div>
                                <div className="text-emerald-800 text-xs leading-relaxed">{stage.nutrientRegime}</div>
                              </div>
                            )}
                          </div>

                          {/* Critical Pest Alert */}
                          {stage.criticalAlert && (
                            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
                              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                              <div>
                                <span className="font-bold">{isTa ? 'முக்கிய எச்சரிக்கை: ' : 'Critical Advisory: '}</span>
                                {stage.criticalAlert}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Direct Market / Procurement Linkage */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-700 to-teal-800 text-white flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <div className="font-bold text-base flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-300" />
                    {isTa ? 'அறுவடை சந்தை இணைப்பு' : 'Harvest Market Linkage Ready'}
                  </div>
                  <div className="text-xs text-emerald-100 mt-1 max-w-xl">
                    {isTa
                      ? 'அறுவடைக்கு பின் நெல்லை TNCSC DPC நேரடி கொள்முதல் மையத்தில் விற்க டோக்கன் பெறவும், அல்லது காய்கறிகளை நமது நேரடி சந்தையில் பட்டியலிடவும்.'
                      : 'Connect your harvest directly to government DPC procurement yards or list fresh produce for buyers on AgriBharat Direct Marketplace.'}
                  </div>
                </div>
                {onNavigate && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onNavigate('procurement')}
                      className="px-4 py-2 rounded-xl bg-white text-emerald-800 font-bold text-xs hover:bg-emerald-50 shadow-md transition-all shrink-0 flex items-center gap-1.5"
                    >
                      <span>{isTa ? 'DPC முன்பதிவு' : 'DPC Booking'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onNavigate('marketplace')}
                      className="px-4 py-2 rounded-xl bg-emerald-900/60 text-white border border-emerald-400/40 font-bold text-xs hover:bg-emerald-900 transition-all shrink-0"
                    >
                      <span>{isTa ? 'சந்தையில் விற்க' : 'Direct Market'}</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Support Items Grid (Sections 1-6) */}
      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-700">
            {isTa ? 'அதிகாரப்பூர்வ தகவல்கள் சேகரிக்கப்படுகின்றன...' : 'Loading verified government & university guidance...'}
          </p>
        </div>
      ) : hasError ? (
        <div className="bg-white rounded-2xl border border-red-200 p-8 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
          <p className="text-sm font-bold text-slate-800">
            {isTa ? 'தகவல்களை ஏற்றுவதில் பிழை ஏற்பட்டது' : 'Unable to connect to support records.'}
          </p>
          <button
            onClick={loadContent}
            className="px-4 py-2 bg-emerald-700 text-white rounded-lg text-xs font-semibold hover:bg-emerald-800"
          >
            {isTa ? 'மீண்டும் முயற்சி செய்' : 'Retry'}
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-2">
          <Info className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-sm font-bold text-slate-700">
            {isTa ? 'பொருத்தமான பதிவுகள் எதுவும் இல்லை' : 'No records match your filter criteria.'}
          </p>
          <p className="text-xs text-slate-500">
            {isTa ? 'மாவட்டம் அல்லது தேடல் வார்த்தையை மாற்றி பார்க்கவும்.' : 'Try changing the district filter or search query.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => {
            const isStale = item.verificationStatus === 'stale_review_needed' || isDateOlderThan180Days(item.lastCheckedDate);
            const daysLeft = item.trainingMeta ? getDaysUntil(item.trainingMeta.registrationDeadline || item.trainingMeta.startDate) : null;
            return (
              <div
                key={item.contentId}
                className="bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
              >
                {/* Card Header & Badges */}
                <div className="p-5 space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                      {item.category.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      {item.district || 'Statewide'}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-2">
                    {isTa ? item.title.ta : item.title.en}
                  </h3>

                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {isTa ? item.description.ta : item.description.en}
                  </p>

                  {/* Stale Warning Badge on Card if older than 180 days */}
                  {isStale && (
                    <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-center gap-1.5 font-medium">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>{isTa ? 'மறுஆய்வு தேவை (>180 நாட்கள்)' : 'Verification review advised (>180d)'}</span>
                    </div>
                  )}

                  {/* Training-specific Meta Box */}
                  {item.trainingMeta && (
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-2 text-xs">
                      <div className="flex items-center justify-between font-semibold text-slate-800">
                        <span className="flex items-center gap-1.5 text-emerald-700">
                          <Calendar className="w-3.5 h-3.5" />
                          {item.trainingMeta.startDate}
                        </span>
                        <div className="flex items-center gap-1">
                          {item.trainingMeta.scheduleStatus === 'recurring_monthly' && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                              🔁 {isTa ? 'சுழற்சி' : 'Recurring'}
                            </span>
                          )}
                          {item.trainingMeta.scheduleStatus === 'historical_reference' && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                              📜 {isTa ? 'வரலாறு' : 'Ref Only'}
                            </span>
                          )}
                          {item.trainingMeta.scheduleStatus === 'unverified_schedule' && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                              ⚠️ {isTa ? 'அழைக்கவும்' : 'Call Desk'}
                            </span>
                          )}
                          <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">
                            {item.trainingMeta.mode}
                          </span>
                        </div>
                      </div>
                      <div className="text-slate-600 flex items-center justify-between">
                        <span>{isTa ? 'கட்டணம்:' : 'Fees:'} <strong className="text-slate-800">{item.trainingMeta.fees || 'Free'}</strong></span>
                        {daysLeft !== null && daysLeft >= 0 && (
                          <span className="text-amber-700 font-bold bg-amber-50 px-2 py-0.5 rounded-md">
                            {daysLeft === 0 ? 'Last Day!' : `${daysLeft} days left`}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Entrepreneurship snippet */}
                  {item.entrepreneurshipMeta && (
                    <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 space-y-1 text-xs">
                      <div className="font-bold text-emerald-950">
                        💡 {isTa ? item.entrepreneurshipMeta.businessIdea.ta : item.entrepreneurshipMeta.businessIdea.en}
                      </div>
                      <div className="text-emerald-800 text-[11px]">
                        <strong>{isTa ? 'மூலதனம்:' : 'Capital:'}</strong> {item.entrepreneurshipMeta.estimatedCapitalCost}
                      </div>
                    </div>
                  )}

                  {/* Protected Cultivation snippet */}
                  {item.protectedCultivationMeta && (
                    <div className="p-3 rounded-xl bg-sky-50/60 border border-sky-100 space-y-1 text-xs">
                      <div className="font-bold text-sky-950">
                        🏛️ {item.protectedCultivationMeta.structureType}
                      </div>
                      {item.protectedCultivationMeta.suitableCrops && item.protectedCultivationMeta.suitableCrops.length > 0 && (
                        <div className="text-sky-800 text-[11px]">
                          {item.protectedCultivationMeta.suitableCrops.slice(0, 3).join(', ')}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Value Addition snippet */}
                  {item.valueAdditionMeta && (
                    <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-100 space-y-1 text-xs">
                      <div className="font-bold text-amber-950">
                        📦 {item.valueAdditionMeta.processingIdea ? (isTa ? item.valueAdditionMeta.processingIdea.ta : item.valueAdditionMeta.processingIdea.en) : item.valueAdditionMeta.produceCategory}
                      </div>
                      {item.valueAdditionMeta.shelfLifeExtensionDays && (
                        <div className="text-amber-800 text-[11px]">
                          <strong>{isTa ? 'ஆயுட்காலம்:' : 'Shelf-life:'}</strong> {item.valueAdditionMeta.shelfLifeExtensionDays}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Direct Market & e-NAM snippet */}
                  {item.directMarketMeta && (
                    <div className="p-3 rounded-xl bg-purple-50/70 border border-purple-100 space-y-1 text-xs">
                      <div className="font-bold text-purple-950 flex items-center justify-between">
                        <span>🏪 {item.directMarketMeta.channelType || item.directMarketMeta.marketType || (isTa ? 'நேரடி சந்தை' : 'Direct Market')}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-200/80 text-purple-900 font-semibold">
                          {item.state || 'TN'}
                        </span>
                      </div>
                      <div className="text-purple-800 text-[11px]">
                        <strong>{isTa ? 'முறை / விலை:' : 'Mode / Pricing:'}</strong> {item.directMarketMeta.pricingMechanism || (isTa ? 'மின்னணு வெளிப்படையான ஏலம்' : 'Electronic Bidding / Fair Price')}
                      </div>
                      {((item.directMarketMeta.suitableProduce && item.directMarketMeta.suitableProduce.length > 0) ||
                        (item.directMarketMeta.buyerLinkageChannels && item.directMarketMeta.buyerLinkageChannels.length > 0) ||
                        (item.highlights && item.highlights.length > 0)) && (
                        <div className="text-purple-700 text-[10px] truncate">
                          {(item.directMarketMeta.suitableProduce || item.directMarketMeta.buyerLinkageChannels || item.highlights || []).slice(0, 3).join(', ')}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Subsidy-specific Meta Box */}
                  {item.subsidyMeta && (
                    <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 space-y-1 text-xs">
                      <div className="font-bold text-emerald-900 flex items-center justify-between">
                        <span>{item.subsidyMeta.schemeName}</span>
                        {item.subsidyMeta.subsidyPercent && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900 font-extrabold">
                            {item.subsidyMeta.subsidyPercent}% {isTa ? 'மானியம்' : 'Subsidy'}
                          </span>
                        )}
                      </div>
                      <div className="text-emerald-800 text-xs">
                        <strong>{isTa ? 'வரம்பு:' : 'Norm:'}</strong> {item.subsidyMeta.costNorm}
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Footer: Verified Contact Desk & Interactive Details Button */}
                <div className="p-4 bg-slate-50/80 border-t border-slate-100 space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700 truncate max-w-[170px]" title={item.institution}>
                      🏛️ {item.institution}
                    </span>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.contact?.contactType === 'institutional_office' && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-200/80 text-slate-700">
                          {isTa ? 'அலுவலகம்' : 'Office Desk'}
                        </span>
                      )}
                      {item.contact?.contactType === 'helpline' && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-100 text-emerald-800">
                          {isTa ? 'ஹெல்ப்லைன்' : 'Helpline'}
                        </span>
                      )}
                      <span className="text-[10px] text-slate-400">
                        {item.lastCheckedDate}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-1">
                    {/* View Full Details Modal Trigger */}
                    <button
                      onClick={() => setSelectedItemForDetail(item)}
                      className="w-full flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold transition-all shadow-2xs"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>{isTa ? 'முழு விவரங்கள்' : 'View Details'}</span>
                    </button>

                    {/* Official Portal Source Link */}
                    <a
                      href={item.officialSourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-all shadow-2xs"
                    >
                      <span>{isTa ? 'அரசு தளம்' : 'Govt Link'}</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* FULL DEEP-DIVE MODAL FOR CHOSEN SUPPORT ITEM */}
      {selectedItemForDetail && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-100 animate-in fade-in duration-200">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                  {selectedItemForDetail.category.replace('_', ' ')}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  {selectedItemForDetail.district || 'All Districts (Statewide)'}
                </span>
              </div>
              <button
                onClick={() => setSelectedItemForDetail(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 text-slate-800">
              {/* Title & Description */}
              <div>
                <h2 className="text-xl font-extrabold text-slate-900 mb-1 leading-snug">
                  {isTa ? selectedItemForDetail.title.ta : selectedItemForDetail.title.en}
                </h2>
                <div className="text-xs text-slate-500 font-semibold mb-3">
                  🏛️ {selectedItemForDetail.institution}
                </div>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {isTa ? selectedItemForDetail.description.ta : selectedItemForDetail.description.en}
                </p>
              </div>

              {/* Provenance & Stale Advisory Notice */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-emerald-800 font-semibold">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'அதிகாரப்பூர்வ சரிபார்க்கப்பட்ட பதிவு' : 'Verified Institutional Content'}</span>
                  </div>
                  <div className="text-slate-500">
                    {isTa ? 'கடைசியாக சரிபார்க்கப்பட்ட தேதி:' : 'Last Verified:'} <strong>{selectedItemForDetail.lastCheckedDate}</strong>
                  </div>
                </div>

                {(selectedItemForDetail.verificationStatus === 'stale_review_needed' ||
                  isDateOlderThan180Days(selectedItemForDetail.lastCheckedDate)) && (
                  <div className="p-2.5 rounded-lg bg-amber-100/70 border border-amber-300 text-amber-900 text-xs flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <strong>{isTa ? 'மறுஆய்வு எச்சரிக்கை:' : 'Stale Review Warning:'} </strong>
                      {isTa
                        ? 'இந்த தகவல் 180 நாட்களுக்கு முன்பு சரிபார்க்கப்பட்டது. சமீபத்திய கட்டணங்கள் மற்றும் கால அட்டவணையை அதிகாரப்பூர்வ போர்டலில் உறுதி செய்யவும்.'
                        : 'This official content has not been re-verified within the last 180 days. Please verify published dates and norms on the official portal.'}
                    </div>
                  </div>
                )}
              </div>

              {/* 1. TRAINING SPECIFICS */}
              {selectedItemForDetail.trainingMeta && (
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <GraduationCap className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'பயிற்சி விபரங்கள் & அட்டவணை' : 'Practical Course Schedule & Venue'}</span>
                  </h3>

                  {(selectedItemForDetail.trainingMeta.scheduleStatus === 'historical_reference' ||
                    selectedItemForDetail.trainingMeta.scheduleStatus === 'unverified_schedule') && (
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <strong>{isTa ? 'அட்டவணை உறுதிப்படுத்தல் எச்சரிக்கை:' : 'Schedule & Batch Advisory:'} </strong>
                        {isTa
                          ? 'இந்த பயிற்சி அறிவிப்பு சுழற்சி/வரலாற்று அட்டவணையாக பதிவு செய்யப்பட்டுள்ளது. நேரில் செல்வதற்கு முன் அல்லது கட்டணம் செலுத்துவதற்கு முன், தொலைபேசி மூலம் நடப்பு பயிற்சி தேதியை உறுதி செய்யவும்.'
                          : 'This training course is published from an institutional schedule or historical calendar. Batch dates and seat availability are subject to re-scheduling. Please contact the institution office desk before traveling or remitting fees.'}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block mb-0.5">{isTa ? 'பயிற்சி மையம் & இடம்:' : 'Provider & Venue:'}</span>
                      <strong className="text-slate-900">{selectedItemForDetail.trainingMeta.venue}</strong>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block mb-0.5">{isTa ? 'பயிற்சி காலம் & முறை:' : 'Schedule & Mode:'}</span>
                      <strong className="text-slate-900">
                        {selectedItemForDetail.trainingMeta.startDate} to {selectedItemForDetail.trainingMeta.endDate} ({selectedItemForDetail.trainingMeta.mode})
                      </strong>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block mb-0.5">{isTa ? 'அதிகாரப்பூர்வ கட்டணம்:' : 'Official Published Fees:'}</span>
                      <strong className="text-emerald-800">{selectedItemForDetail.trainingMeta.fees || 'Free (இலவசம்)'}</strong>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 block mb-0.5">{isTa ? 'தகுதி வரம்பு:' : 'Eligibility Criteria:'}</span>
                      <strong className="text-slate-900">{selectedItemForDetail.trainingMeta.eligibility}</strong>
                    </div>
                  </div>

                  {selectedItemForDetail.registrationInstructions && (
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 space-y-1">
                      <strong className="font-bold flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-emerald-700" />
                        {isTa ? 'விண்ணப்பிக்கும் நடைமுறை (Registration Steps):' : 'Official Registration Instructions:'}
                      </strong>
                      <p className="leading-relaxed">
                        {isTa ? selectedItemForDetail.registrationInstructions.ta : selectedItemForDetail.registrationInstructions.en}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* 2. ENTREPRENEURSHIP SPECIFICS */}
              {selectedItemForDetail.entrepreneurshipMeta && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <Briefcase className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'வணிக மாதிரி & நிதி மதிப்பீடுகள்' : 'Agri-Business Blueprint & Financial Feasibility'}</span>
                  </h3>
                  
                  {/* Financials & Revenue Box */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                      <span className="text-emerald-800 font-medium block mb-0.5">{isTa ? 'ஆரம்ப மூலதனம்:' : 'Estimated Capital Cost:'}</span>
                      <strong className="text-emerald-950 text-sm">{selectedItemForDetail.entrepreneurshipMeta.estimatedCapitalCost}</strong>
                    </div>
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                      <span className="text-emerald-800 font-medium block mb-0.5">{isTa ? 'மாத இயக்கச் செலவு:' : 'Monthly Operating Cost:'}</span>
                      <strong className="text-emerald-950 text-sm">{selectedItemForDetail.entrepreneurshipMeta.estimatedMonthlyOperatingCost}</strong>
                    </div>
                  </div>

                  {/* Revenue Assumptions */}
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
                    <strong className="text-slate-800 flex items-center gap-1.5 font-bold">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                      {isTa ? 'வருவாய் மற்றும் லாப விகித மதிப்பீடு:' : 'Revenue Assumptions & Margins:'}
                    </strong>
                    <p className="text-slate-600 leading-relaxed">
                      {selectedItemForDetail.entrepreneurshipMeta.revenueAssumptions}
                    </p>
                  </div>

                  {/* Target Customers */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'இலக்கு வாடிக்கையாளர்கள் (Target Customers):' : 'Target Customers:'}</strong>
                    <div className="flex flex-wrap gap-1.5">
                      {(selectedItemForDetail.entrepreneurshipMeta.targetCustomers || []).map((cust, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 text-xs font-medium">
                          {cust}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Machinery & Equipment */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 flex items-center gap-1">
                      <Hammer className="w-3.5 h-3.5 text-slate-500" />
                      {isTa ? 'தேவைப்படும் இயந்திரங்கள் (Required Equipment):' : 'Required Equipment & Machinery:'}
                    </strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.entrepreneurshipMeta.requiredEquipment || []).map((eq, i) => (
                        <li key={i}>{eq}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Startup Planning Roadmap */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'தொடக்கக் காலப் பணிகள் (Startup Planning Steps):' : 'Startup Implementation Roadmap:'}</strong>
                    <ol className="list-decimal pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.entrepreneurshipMeta.startupPlanningSteps || []).map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>

                  {/* Risk Analysis */}
                  <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-200 text-xs space-y-1.5">
                    <strong className="text-amber-900 font-bold flex items-center gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
                      {isTa ? 'இடர் பகுப்பாய்வு & பாதுகாப்பு வழிகள் (Risk Analysis):' : 'Risk Analysis & Mitigation Strategies:'}
                    </strong>
                    <ul className="list-disc pl-5 space-y-1 text-amber-800">
                      {(selectedItemForDetail.entrepreneurshipMeta.riskAnalysis || []).map((rk, i) => (
                        <li key={i}>{rk}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Official Support Resources */}
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs space-y-1.5">
                    <strong className="text-emerald-900 font-bold flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-emerald-700" />
                      {isTa ? 'அதிகாரப்பூர்வ அரசு மற்றும் நபார்டு ஆதரவு:' : 'Relevant Official Support Resources:'}
                    </strong>
                    <ul className="list-disc pl-5 space-y-1 text-emerald-800">
                      {(selectedItemForDetail.entrepreneurshipMeta.officialSupportResources || []).map((res, i) => (
                        <li key={i}>{res}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* 3. ORGANIC FARMING SPECIFICS */}
              {selectedItemForDetail.organicMeta && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <Leaf className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'இயற்கை வேளாண்மை & சான்றளிப்பு நெறிமுறைகள்' : 'Organic Soil Health, Bio-Inputs & Certification'}</span>
                  </h3>

                  {/* Soil Health Practices */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'மண்வள மேம்பாட்டு முறைகள்:' : 'Soil Health & Carbon Enrichment:'}</strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.organicMeta.soilHealthPractices || []).map((sh, i) => (
                        <li key={i}>{sh}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Composting Methods */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'மக்கிய உர தயாரிப்பு (Composting Methods):' : 'Composting Methods (NADEP / Vermicomposting):'}</strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.organicMeta.compostingMethods || []).map((cm, i) => (
                        <li key={i}>{cm}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Bio-Inputs Recipes */}
                  {selectedItemForDetail.organicMeta.bioInputsRecipes && selectedItemForDetail.organicMeta.bioInputsRecipes.length > 0 && (
                    <div className="space-y-2">
                      <strong className="text-xs text-slate-800 block">{isTa ? 'பாரம்பரிய உயிரி இடுபொருட்கள் செய்முறை:' : 'Standard Bio-Inputs Preparation Recipes:'}</strong>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {selectedItemForDetail.organicMeta.bioInputsRecipes.map((recipe, i) => (
                          <div key={i} className="p-3 rounded-lg bg-emerald-50/70 border border-emerald-100 text-xs space-y-1.5">
                            <div className="font-bold text-emerald-950 flex items-center justify-between">
                              <span>{isTa && recipe.nameTa ? recipe.nameTa : recipe.name}</span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-200 text-emerald-900">
                                {recipe.preparationDays} {isTa ? 'நாட்கள்' : 'days'}
                              </span>
                            </div>
                            <div className="text-emerald-900 text-[11px]">
                              <strong>{isTa ? 'அளவு:' : 'Dosage:'}</strong> {recipe.dosage}
                            </div>
                            <div className="text-slate-600 text-[11px]">
                              <strong>{isTa ? 'மூலப்பொருட்கள்:' : 'Ingredients:'}</strong> {(recipe.ingredients || []).join(', ')}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 3-Year Certification Guidance */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <strong className="text-slate-900 font-bold flex items-center gap-1.5">
                        <Award className="w-4 h-4 text-emerald-700" />
                        {isTa ? 'TNOCD கரிமச் சான்றளிப்பு நடைமுறைகள்' : 'TNOCD / NPOP Organic Certification Process'}
                      </strong>
                      <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 font-bold">
                        {selectedItemForDetail.organicMeta.transitionTimelineYears} {isTa ? 'ஆண்டுகள் மாற்றம்' : 'Years Conversion'}
                      </span>
                    </div>
                    <ol className="list-decimal pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.organicMeta.certificationSteps || []).map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}

              {/* 4. PROTECTED CULTIVATION SPECIFICS */}
              {selectedItemForDetail.protectedCultivationMeta && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <Building className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'பசுமைக் குடில் & நிழல்வலை விபரங்கள்' : 'Protected Cultivation Setup & Regimes'}</span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-sky-50 border border-sky-100">
                      <span className="text-sky-800 font-medium block mb-0.5">{isTa ? 'கட்டமைப்பு வகை:' : 'Structure Type:'}</span>
                      <strong className="text-sky-950">{selectedItemForDetail.protectedCultivationMeta.structureType}</strong>
                    </div>
                    <div className="p-3 rounded-lg bg-sky-50 border border-sky-100">
                      <span className="text-sky-800 font-medium block mb-0.5">{isTa ? 'பொருத்தமான பயிர்கள்:' : 'Suitable Crops:'}</span>
                      <strong className="text-sky-950">{(selectedItemForDetail.protectedCultivationMeta.suitableCrops || []).join(', ')}</strong>
                    </div>
                  </div>

                  {/* Irrigation & Fertigation */}
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
                    <strong className="text-slate-800 flex items-center gap-1.5 font-bold">
                      <Droplets className="w-3.5 h-3.5 text-sky-600" />
                      {isTa ? 'நுண்ணீர் பாசனம் & உர மேலாண்மை (Fertigation):' : 'Irrigation & Fertigation Regime:'}
                    </strong>
                    <p className="text-slate-600 leading-relaxed">
                      {selectedItemForDetail.protectedCultivationMeta.irrigationFertigationRegime}
                    </p>
                  </div>

                  {/* Pest & Disease Management */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'பூச்சி மற்றும் நோய் கட்டுப்பாடு:' : 'Pest & Disease Management under Netting:'}</strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.protectedCultivationMeta.pestDiseaseManagement || []).map((pdm, i) => (
                        <li key={i}>{pdm}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Setup & Annual Maintenance */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <strong className="text-slate-800 block mb-1">{isTa ? 'அமைக்கும் தேவைகள்:' : 'Setup Requirements:'}</strong>
                      <ul className="list-disc pl-4 space-y-1 text-slate-600">
                        {(selectedItemForDetail.protectedCultivationMeta.setupRequirements || []).map((sr, i) => (
                          <li key={i}>{sr}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <strong className="text-slate-800 block mb-1">{isTa ? 'வருடாந்திர பராமரிப்பு:' : 'Annual Maintenance Tips:'}</strong>
                      <ul className="list-disc pl-4 space-y-1 text-slate-600">
                        {(selectedItemForDetail.protectedCultivationMeta.annualMaintenanceTips || []).map((tip, i) => (
                          <li key={i}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Applicable Schemes */}
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs space-y-1">
                    <strong className="text-emerald-950 font-bold flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-emerald-700" />
                      {isTa ? 'அரசு மானியத் திட்டங்கள் (Applicable Official Schemes):' : 'Applicable Government Subsidies:'}
                    </strong>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {(selectedItemForDetail.protectedCultivationMeta.applicableSchemes || []).map((sch, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-md bg-white border border-emerald-300 text-emerald-900 font-semibold text-xs">
                          {sch}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* 5. VALUE ADDITION SPECIFICS */}
              {selectedItemForDetail.valueAdditionMeta && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <Package className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'மதிப்புக் கூட்டுப் பொருள் தயாரிப்பு & சந்தைப்படுத்தல்' : 'Processing Technology, Shelf Life & Costing'}</span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-100">
                      <span className="text-amber-800 font-medium block mb-0.5">{isTa ? 'விளைபொருள் வகை:' : 'Produce Category:'}</span>
                      <strong className="text-amber-950">{selectedItemForDetail.valueAdditionMeta.produceCategory}</strong>
                    </div>
                    <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-100">
                      <span className="text-amber-800 font-medium block mb-0.5">{isTa ? 'நீட்டிக்கப்பட்ட ஆயுட்காலம்:' : 'Shelf-Life Extension:'}</span>
                      <strong className="text-amber-950">{selectedItemForDetail.valueAdditionMeta.shelfLifeExtensionDays}</strong>
                    </div>
                  </div>

                  {/* Costing Breakdown */}
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100 text-xs space-y-1">
                    <strong className="text-emerald-950 font-bold flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-emerald-700" />
                      {isTa ? 'செலவு மற்றும் லாப மதிப்பீடு (Costing Breakdown):' : 'Estimated Costing & Profit Margin Breakdown:'}
                    </strong>
                    <p className="text-emerald-900 leading-relaxed">
                      {selectedItemForDetail.valueAdditionMeta.estimatedCostingBreakdown}
                    </p>
                  </div>

                  {/* Hygiene Standards */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'சுகாதாரத் தரநிலைகள் (Hygiene & FSSAI Standards):' : 'Hygiene & FSSAI Sanitary Standards:'}</strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.valueAdditionMeta.hygieneStandards || []).map((hs, i) => (
                        <li key={i}>{hs}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Packaging Options */}
                  <div className="text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'பேக்கேஜிங் தேர்வுகள் (Packaging Options):' : 'Packaging & Preservation Solutions:'}</strong>
                    <ul className="list-disc pl-5 space-y-1 text-slate-600">
                      {(selectedItemForDetail.valueAdditionMeta.packagingOptions || []).map((po, i) => (
                        <li key={i}>{po}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Marketing Channels */}
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                    <strong className="text-slate-800 block">{isTa ? 'விற்பனை வாய்ப்புகள் (Marketing Channels):' : 'Direct Marketing & Distribution Channels:'}</strong>
                    <div className="flex flex-wrap gap-1.5">
                      {(selectedItemForDetail.valueAdditionMeta.marketingChannels || []).map((mc, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-slate-700 text-xs font-medium">
                          {mc}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* 6. DIRECT MARKET & e-NAM SPECIFICS */}
              {selectedItemForDetail.directMarketMeta && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b pb-1.5">
                    <Store className="w-4 h-4 text-emerald-600" />
                    <span>{isTa ? 'நேரடி சந்தை & e-NAM வர்த்தக வழிமுறை' : 'Direct Market & e-NAM Trading Framework'}</span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-purple-50/70 border border-purple-100">
                      <span className="text-purple-800 font-medium block mb-0.5">{isTa ? 'சந்தை வழிமுறை:' : 'Market Channel:'}</span>
                      <strong className="text-purple-950 text-sm">
                        {selectedItemForDetail.directMarketMeta.channelType || selectedItemForDetail.directMarketMeta.marketType || (isTa ? 'நேரடி விவசாய சந்தை' : 'Direct Agricultural Market')}
                      </strong>
                    </div>
                    <div className="p-3 rounded-lg bg-purple-50/70 border border-purple-100">
                      <span className="text-purple-800 font-medium block mb-0.5">{isTa ? 'விலை நிர்ணய முறை:' : 'Pricing Mechanism:'}</span>
                      <strong className="text-purple-950 text-sm">
                        {selectedItemForDetail.directMarketMeta.pricingMechanism || (isTa ? 'மின்னணு வெளிப்படையான ஏலம் / நியாய விலை' : 'Electronic Bidding / Transparent Discovery')}
                      </strong>
                    </div>
                  </div>

                  {/* Portal & Helpline Badges if available */}
                  {(selectedItemForDetail.directMarketMeta.platformPortal || selectedItemForDetail.directMarketMeta.helplinePhone) && (
                    <div className="p-3 rounded-lg bg-purple-50/50 border border-purple-200 text-xs flex flex-wrap items-center justify-between gap-2">
                      {selectedItemForDetail.directMarketMeta.platformPortal && (
                        <a
                          href={selectedItemForDetail.directMarketMeta.platformPortal}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-purple-700 hover:text-purple-900 font-bold hover:underline"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>{isTa ? 'அதிகாரப்பூர்வ வர்த்தக போர்டல்' : 'Official Trading Portal'}</span>
                        </a>
                      )}
                      {selectedItemForDetail.directMarketMeta.helplinePhone && (
                        <span className="text-purple-900 font-medium flex items-center gap-1">
                          <Phone className="w-3.5 h-3.5 text-purple-600" />
                          <span>{selectedItemForDetail.directMarketMeta.helplinePhone}</span>
                        </span>
                      )}
                    </div>
                  )}

                  {/* Trading Workflow Stages */}
                  {((isTa && selectedItemForDetail.directMarketMeta.tradingWorkflowTa && selectedItemForDetail.directMarketMeta.tradingWorkflowTa.length > 0) ||
                    (selectedItemForDetail.directMarketMeta.tradingWorkflow && selectedItemForDetail.directMarketMeta.tradingWorkflow.length > 0) ||
                    (selectedItemForDetail.directMarketMeta.tradingWorkflowStages && selectedItemForDetail.directMarketMeta.tradingWorkflowStages.length > 0)) && (
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                      <strong className="text-slate-800 flex items-center gap-1.5 font-bold">
                        <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                        {isTa ? 'வர்த்தக படிநிலைகள் (Workflow Stages):' : 'Trading Workflow Stages:'}
                      </strong>
                      <ol className="list-decimal pl-4 space-y-1.5 text-slate-700">
                        {(isTa && selectedItemForDetail.directMarketMeta.tradingWorkflowTa && selectedItemForDetail.directMarketMeta.tradingWorkflowTa.length > 0
                          ? selectedItemForDetail.directMarketMeta.tradingWorkflowTa
                          : (selectedItemForDetail.directMarketMeta.tradingWorkflow || selectedItemForDetail.directMarketMeta.tradingWorkflowStages || [])
                        ).map((stage, i) => (
                          <li key={i} className="leading-relaxed">
                            {stage}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Quality Assaying & Required Documents */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <strong className="text-slate-800 flex items-center gap-1.5 font-bold mb-1.5">
                        <Scale className="w-3.5 h-3.5 text-purple-600" />
                        {isTa ? 'தர பரிசோதனை காரணிகள் (Assaying):' : 'Quality Assaying Parameters:'}
                      </strong>
                      <ul className="list-disc pl-4 space-y-1 text-slate-600">
                        {(selectedItemForDetail.directMarketMeta.qualityAssayingParameters || [
                          isTa ? 'ஈரப்பத அளவு தர நிர்ணயம்' : 'Moisture content tolerance',
                          isTa ? 'வெளிப்புற கழிவுப் பொருட்கள் நீக்கம் (<1%)' : 'Foreign matter removal (<1%)',
                          isTa ? 'முழுமையான தரம் வாரியான பிரித்தல்' : 'Grade A/B/C quality sorting'
                        ]).map((param, i) => (
                          <li key={i}>{param}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <strong className="text-slate-800 flex items-center gap-1.5 font-bold mb-1.5">
                        <FileText className="w-3.5 h-3.5 text-emerald-600" />
                        {isTa ? 'தேவைப்படும் ஆவணங்கள்:' : 'Required Documents:'}
                      </strong>
                      <ul className="list-disc pl-4 space-y-1 text-slate-600">
                        {(selectedItemForDetail.directMarketMeta.requiredDocuments || [
                          isTa ? 'விவசாயி ஆதார் அட்டை' : 'Farmer Aadhaar Card',
                          isTa ? 'வங்கி கணக்கு புத்தகம் / விவரம்' : 'Bank Passbook / Verified Account',
                          isTa ? 'நில உரிமை / அடங்கல் / உழவர் அடையாள எண்' : 'Land Record / Farmer ID'
                        ]).map((doc, i) => (
                          <li key={i}>{doc}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Buyer Channels & Charges */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 font-semibold block mb-1">{isTa ? 'கொள்முதல் வாங்குபவர்கள்:' : 'Target Buyers:'}</span>
                      <div className="flex flex-wrap gap-1">
                        {(selectedItemForDetail.directMarketMeta.buyerTypes || selectedItemForDetail.directMarketMeta.buyerLinkageChannels || [
                          isTa ? 'மொத்த வியாபாரிகள்' : 'Wholesale Traders',
                          isTa ? 'உணவு பதப்படுத்தும் நிறுவனங்கள்' : 'Food Processors',
                          isTa ? 'உழவர் உற்பத்தியாளர் நிறுவனங்கள் (FPOs)' : 'FPOs & Retailers'
                        ]).map((buyer, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 text-[11px]">
                            {buyer}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-500 font-semibold block mb-0.5">{isTa ? 'கட்டணம் & வரிகள்:' : 'Market Charges & Levies:'}</span>
                      <strong className="text-slate-900 leading-relaxed block">
                        {selectedItemForDetail.directMarketMeta.chargesOrLevies || (isTa ? 'விவசாயிகளுக்கு எவ்வித கமிஷனும் இல்லை (0% கட்டணம்)' : 'Zero commission on farmer produce')}
                      </strong>
                    </div>
                  </div>

                  {/* Dispute Desk & Digital Payments */}
                  <div className="p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 text-xs space-y-1">
                    <div className="flex items-center justify-between text-emerald-950 font-semibold">
                      <span>⚖️ {isTa ? 'தீர்வு மையம்:' : 'Dispute Desk:'} {selectedItemForDetail.directMarketMeta.disputeResolutionDesk || (isTa ? 'ஒழுங்குமுறை விற்பனைக் குழு குறைதீர் பிரிவு' : 'Mandi Grievance Committee')}</span>
                    </div>
                    <div className="text-emerald-800 text-[11px] pt-1">
                      <strong>{isTa ? 'பணப்பரிவர்த்தனை:' : 'Payment Modes:'}</strong> {(selectedItemForDetail.directMarketMeta.digitalPaymentModes || [
                        'Direct Bank Transfer (DBT)',
                        'RTGS / NEFT / UPI',
                        'Instant Mandi Settlement'
                      ]).join(', ')}
                    </div>
                  </div>
                </div>
              )}

              {/* Source Excerpt Quote */}
              {selectedItemForDetail.sourceExcerpt && (
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                  <span className="text-slate-500 font-bold block flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    {isTa ? 'அரசு மூலக் குறிப்பு (Official Portal Excerpt):' : 'Official Portal Source Excerpt:'}
                  </span>
                  <blockquote className="italic text-slate-700 border-l-2 border-emerald-600 pl-3 leading-relaxed">
                    "{selectedItemForDetail.sourceExcerpt}"
                  </blockquote>
                </div>
              )}

              {/* Verified Institutional Contact Desk */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5 text-emerald-600" />
                    {isTa ? 'அதிகாரப்பூர்வ உதவி மையம் & தொடர்பு முகவரி' : 'Institutional Contact Desk'}
                  </div>
                  {selectedItemForDetail.contact.contactType && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-200/80 text-slate-700">
                      {selectedItemForDetail.contact.contactType.replace('_', ' ')}
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-600 space-y-1">
                  {selectedItemForDetail.contact.address && (
                    <p>📍 {selectedItemForDetail.contact.address}</p>
                  )}
                  {selectedItemForDetail.contact.officePhone && (
                    <p className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{isTa ? 'அலுவலக தொலைபேசி:' : 'Office Phone:'}</span>{' '}
                      <a href={`tel:${selectedItemForDetail.contact.officePhone}`} className="text-emerald-700 font-semibold hover:underline">
                        {selectedItemForDetail.contact.officePhone}
                      </a>
                    </p>
                  )}
                  {selectedItemForDetail.contact.helplinePhone && (
                    <p className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{isTa ? 'இலவச உதவி எண்:' : 'Helpline:'}</span>{' '}
                      <a href={`tel:${selectedItemForDetail.contact.helplinePhone}`} className="text-emerald-700 font-semibold hover:underline">
                        {selectedItemForDetail.contact.helplinePhone}
                      </a>
                    </p>
                  )}
                  {selectedItemForDetail.contact.email && (
                    <p className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      <span>{isTa ? 'மின்னஞ்சல்:' : 'Email:'}</span>{' '}
                      <a href={`mailto:${selectedItemForDetail.contact.email}`} className="text-emerald-700 font-semibold hover:underline">
                        {selectedItemForDetail.contact.email}
                      </a>
                    </p>
                  )}
                  {selectedItemForDetail.contact.verificationNote && (
                    <p className="text-[11px] text-slate-500 italic pt-1.5 border-t border-slate-200/80">
                      ℹ️ {selectedItemForDetail.contact.verificationNote}
                    </p>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2 border-t">
                <button
                  onClick={() => setSelectedItemForDetail(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  {isTa ? 'மூடுக' : 'Close'}
                </button>
                <a
                  href={selectedItemForDetail.officialSourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-5 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2"
                >
                  <span>{isTa ? 'அரசு தளத்தில் காண்க' : 'Open Official Govt Source'}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

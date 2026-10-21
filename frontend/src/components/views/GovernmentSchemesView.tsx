import React, { useState, useEffect } from 'react';
import {
  Landmark,
  ExternalLink,
  FileText,
  CheckCircle2,
  Filter,
  ShieldAlert,
  Loader2,
  Building,
  PawPrint,
  Search,
  X,
  Info,
  Calendar,
  ChevronRight,
  ShieldCheck,
  Layers,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  getGovernmentSchemesApi,
  type GovernmentSchemesResponse,
  type GovernmentSchemeItem,
} from '../../services/api';

const CATEGORIES = [
  'All',
  'State',
  'Central',
  'Insurance',
  'Irrigation',
  'Machinery',
  'Animals & Livestock',
] as const;

type CategoryType = typeof CATEGORIES[number];

const LIVESTOCK_FILTER_OPTIONS = [
  { value: 'All', labelEn: 'All Animals', labelTa: 'அனைத்து கால்நடைகளும்' },
  { value: 'Cattle', labelEn: 'Cattle & Dairy', labelTa: 'மாடுகள் & பால்வளம்' },
  { value: 'Buffalo', labelEn: 'Buffalo', labelTa: 'எருமை மாடுகள்' },
  { value: 'Sheep', labelEn: 'Sheep', labelTa: 'செம்மறி ஆடுகள்' },
  { value: 'Goat', labelEn: 'Goat', labelTa: 'வெள்ளாடுகள்' },
  { value: 'Poultry', labelEn: 'Poultry', labelTa: 'கோழிப்பண்ணை' },
  { value: 'Pig', labelEn: 'Pig', labelTa: 'பன்றி வளர்ப்பு' },
];

export const GovernmentSchemesView: React.FC = () => {
  const { t, language } = useLanguage();

  const [category, setCategory] = useState<CategoryType>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [governmentLevel, setGovernmentLevel] = useState<string>('All');
  const [livestockType, setLivestockType] = useState<string>('All');
  const [selectedScheme, setSelectedScheme] = useState<GovernmentSchemeItem | null>(null);

  const [data, setData] = useState<GovernmentSchemesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSchemes() {
      setLoading(true);
      setError(null);
      try {
        const res = await getGovernmentSchemesApi({
          category: category === 'All' ? undefined : category,
          search: searchQuery.trim() || undefined,
          governmentLevel: governmentLevel === 'All' ? undefined : governmentLevel,
          livestockType: livestockType === 'All' ? undefined : livestockType,
        });
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load government welfare schemes.');
      } finally {
        setLoading(false);
      }
    }
    loadSchemes();
  }, [category, searchQuery, governmentLevel, livestockType]);

  const categoryLabel = (cat: CategoryType) => {
    if (language === 'ta') {
      switch (cat) {
        case 'All':
          return t.schemesPage?.allCategories || 'அனைத்தும்';
        case 'State':
          return t.schemesPage?.stateCategory || 'மாநில அரசு';
        case 'Central':
          return t.schemesPage?.centralCategory || 'மத்திய அரசு';
        case 'Insurance':
          return t.schemesPage?.insuranceCategory || 'காப்பீடு';
        case 'Irrigation':
          return t.schemesPage?.irrigationCategory || 'பாசனம்';
        case 'Machinery':
          return t.schemesPage?.machineryCategory || 'இயந்திரங்கள்';
        case 'Animals & Livestock':
          return t.schemesPage?.animalsCategory || 'கால்நடைகள் & வளர்ப்பு';
        default:
          return cat;
      }
    }
    return cat;
  };

  const getStatusBadgeVariant = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'emerald';
      case 'closed':
        return 'rose';
      case 'application window unknown':
        return 'amber';
      default:
        return 'slate';
    }
  };

  const formatStatus = (status?: string) => {
    if (!status) return language === 'ta' ? 'அறியப்படவில்லை' : 'Unknown';
    if (language === 'ta') {
      switch (status.toLowerCase()) {
        case 'active':
          return t.schemesPage?.statusActive || 'செயலில் உள்ளது';
        case 'application window unknown':
          return t.schemesPage?.statusUnknown || 'விண்ணப்ப காலம் அறியப்படவில்லை';
        case 'closed':
          return t.schemesPage?.statusClosed || 'முடிவடைந்தது';
        case 'unverified':
          return t.schemesPage?.statusUnverified || 'சரிபார்க்கப்படாதது';
        default:
          return status;
      }
    }
    return status;
  };

  const clearAllFilters = () => {
    setCategory('All');
    setSearchQuery('');
    setGovernmentLevel('All');
    setLivestockType('All');
  };

  const hasActiveFilters =
    category !== 'All' ||
    searchQuery.trim() !== '' ||
    governmentLevel !== 'All' ||
    livestockType !== 'All';

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in pb-12">
      <Card
        title={t.schemesPage?.title || t.nav.schemes}
        subtitle={
          language === 'ta'
            ? t.schemesPage?.subtitle ||
              'மத்திய மற்றும் தமிழ்நாடு மாநில அரசு உழவர் & கால்நடை நலத்திட்டங்கள் மற்றும் நேரடி மானியங்கள்'
            : t.schemesPage?.subtitle ||
              'Central & Tamil Nadu State Agricultural & Livestock Welfare Schemes & Official Portals'
        }
        icon={<Landmark className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <Badge variant="emerald" dot>
            {t.schemesPage?.verifiedNotice || 'Verified Official Portals'}
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Statutory Verification Policy Disclaimer */}
          <div className="p-3.5 rounded-2xl bg-emerald-50/60 border border-emerald-200/80 text-xs text-slate-700 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-emerald-950">
                {language === 'ta'
                  ? 'அதிகாரப்பூர்வ அரசு வழிகாட்டுதல் மற்றும் சரிபார்ப்பு கொள்கை'
                  : 'Official Government Portal Verification Policy'}
              </p>
              <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? data?.disclaimerTa ||
                    'திட்ட மானியங்கள் மற்றும் நலத்திட்ட ஒப்புதல்கள் அனைத்தும் அரசு துறை அலுவலர்களின் கள ஆய்வுக்கு உட்பட்டவை. விவசாயிகள் அதிகாரப்பூர்வ அரசு இணையதளங்கள் மூலமாக மட்டுமே விண்ணப்பிக்க வேண்டும்.'
                  : data?.disclaimerEn ||
                    'Scheme sanctions and DBT subsidy transfers are subject to revenue land/animal records and field verification by competent government officers. AgriBharat does not guarantee application approval. Always apply directly through the verified official government portals provided below.'}
              </p>
            </div>
          </div>

          {/* Search Bar & Multi-Filters Container */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={
                  t.schemesPage?.searchPlaceholder ||
                  'Search schemes by name, department, animal (cattle, goat, poultry) or keywords...'
                }
                className="w-full pl-9 pr-9 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Filter Dropdowns Row */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex flex-wrap items-center gap-3">
                {/* Government Level Dropdown */}
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="font-semibold text-slate-600 flex items-center gap-1">
                    <Layers className="w-3 h-3 text-slate-400" />
                    {t.schemesPage?.filterLevel || 'Level'}:
                  </span>
                  <select
                    value={governmentLevel}
                    onChange={(e) => setGovernmentLevel(e.target.value)}
                    className="py-1 px-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="All">{t.schemesPage?.allLevels || 'All Levels'}</option>
                    <option value="Central">
                      {language === 'ta' ? 'மத்திய அரசு (Central)' : 'Central Government'}
                    </option>
                    <option value="State">
                      {language === 'ta' ? 'மாநில அரசு (Tamil Nadu)' : 'Tamil Nadu State'}
                    </option>
                  </select>
                </div>

                {/* Livestock Animal Type Dropdown (Useful especially for Animals & Livestock category) */}
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="font-semibold text-slate-600 flex items-center gap-1">
                    <PawPrint className="w-3 h-3 text-emerald-600" />
                    {t.schemesPage?.filterLivestock || 'Animal'}:
                  </span>
                  <select
                    value={livestockType}
                    onChange={(e) => setLivestockType(e.target.value)}
                    className="py-1 px-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    {LIVESTOCK_FILTER_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {language === 'ta' ? opt.labelTa : opt.labelEn}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Active Filters Clear Button */}
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={clearAllFilters}
                  className="text-xs text-rose-600 hover:text-rose-700 font-bold flex items-center gap-1 hover:underline"
                >
                  <X className="w-3 h-3" />
                  {language === 'ta' ? 'வடிகட்டிகளை நீக்குக' : 'Reset Filters'}
                </button>
              )}
            </div>
          </div>

          {/* Primary Category Filter Pills */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 font-semibold px-0.5">
              <span className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5" />
                {language === 'ta' ? 'பிரிவுகள்:' : 'Categories:'}
              </span>
              {data?.schemes && (
                <span className="text-[11px] font-medium text-slate-500">
                  {language === 'ta'
                    ? `${data.schemes.length} திட்டங்கள் காட்டப்படுகின்றன`
                    : `Showing ${data.schemes.length} schemes`}
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {CATEGORIES.map((cat) => {
                const isSelected = category === cat;
                const isAnimals = cat === 'Animals & Livestock';
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                      isSelected
                        ? 'bg-emerald-600 text-white shadow-2xs'
                        : isAnimals
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {isAnimals && <PawPrint className="w-3.5 h-3.5 shrink-0" />}
                    <span>{categoryLabel(cat)}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Schemes List */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold">
                {language === 'ta'
                  ? 'சரிபார்க்கப்பட்ட அரசு நலத்திட்டங்கள் ஏற்றப்படுகின்றன...'
                  : 'Loading verified agricultural & livestock schemes...'}
              </p>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center space-y-2">
              <p className="font-bold">{error}</p>
              <button
                type="button"
                onClick={clearAllFilters}
                className="px-3 py-1 bg-white border border-rose-300 rounded-lg text-rose-700 font-bold hover:bg-rose-100"
              >
                {language === 'ta' ? 'வடிகட்டிகளை மீட்டமை' : 'Reset Filters'}
              </button>
            </div>
          ) : data?.schemes && data.schemes.length > 0 ? (
            <div className="space-y-4">
              {data.schemes.map((s: GovernmentSchemeItem) => {
                const displayName =
                  language === 'ta' ? s.nameTa || s.titleTa : s.name || s.titleEn;
                const displayDept = s.department || s.dept;
                const isAnimalRelated =
                  s.category === 'Animals & Livestock' ||
                  (s.livestockTypes && s.livestockTypes.length > 0);

                return (
                  <div
                    key={s.id}
                    className="p-5 rounded-2xl border border-slate-200 bg-white hover:border-emerald-300 hover:shadow-xs transition-all space-y-3.5"
                  >
                    {/* Header Row: Badges, Title, Department, Portal Button */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {/* Category Badge */}
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                              isAnimalRelated
                                ? 'bg-amber-100 text-amber-900 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-900'
                            }`}
                          >
                            {isAnimalRelated && <PawPrint className="w-2.5 h-2.5" />}
                            {s.category}
                          </span>

                          {/* Government Level Badge */}
                          {s.governmentLevel && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                              {s.governmentLevel === 'State'
                                ? language === 'ta'
                                  ? 'தமிழ்நாடு அரசு'
                                  : 'State Govt'
                                : language === 'ta'
                                ? 'மத்திய அரசு'
                                : 'Central Govt'}
                            </span>
                          )}

                          {/* Application Status Badge */}
                          {s.applicationStatus && (
                            <Badge variant={getStatusBadgeVariant(s.applicationStatus)}>
                              {formatStatus(s.applicationStatus)}
                            </Badge>
                          )}
                        </div>

                        {/* Title */}
                        <h4 className="text-sm sm:text-base font-extrabold text-slate-900 leading-snug">
                          {displayName}
                        </h4>

                        {/* Department */}
                        <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                          <Building className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{displayDept}</span>
                        </p>
                      </div>

                      {/* Action Buttons Top-Right */}
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          type="button"
                          onClick={() => setSelectedScheme(s)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-all"
                        >
                          <Info className="w-3 h-3" />
                          <span>{t.schemesPage?.viewDetails || 'View Details'}</span>
                        </button>

                        <a
                          href={s.applicationUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 hover:bg-emerald-600 hover:text-white border border-emerald-200 text-xs font-bold transition-all shrink-0"
                        >
                          <span>{s.portalName || (language === 'ta' ? 'அரசு தளம்' : 'Official Portal')}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>

                    {/* Short Description */}
                    {s.description && (
                      <p className="text-xs text-slate-600 leading-relaxed bg-slate-50/50 p-2.5 rounded-xl border border-slate-100">
                        {s.description}
                      </p>
                    )}

                    {/* Livestock Type Tags (If applicable) */}
                    {s.livestockTypes && s.livestockTypes.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 text-xs pt-0.5">
                        <span className="text-[11px] font-bold text-slate-500 flex items-center gap-1 mr-1">
                          <PawPrint className="w-3 h-3 text-emerald-600" />
                          {language === 'ta' ? 'பொருந்தும் கால்நடைகள்:' : 'Livestock Types:'}
                        </span>
                        {s.livestockTypes.map((type, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-50 border border-amber-200/80 text-amber-900 text-[11px] font-medium"
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Benefits and Eligibility Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                      <div>
                        <span className="font-extrabold text-emerald-950 block mb-0.5">
                          🎁 {t.schemesPage?.benefitsLabel || 'Subsidy / Financial Benefit'}:
                        </span>
                        {Array.isArray(s.benefits) && s.benefits.length > 0 ? (
                          <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed">
                            {s.benefits.slice(0, 2).map((b, bIdx) => (
                              <li key={bIdx}>{b}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-slate-700 leading-relaxed">{s.benefit}</p>
                        )}
                      </div>
                      <div>
                        <span className="font-extrabold text-slate-900 block mb-0.5">
                          👥 {t.schemesPage?.eligibilityLabel || 'Eligibility Criteria'}:
                        </span>
                        {Array.isArray(s.eligibility) ? (
                          <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed">
                            {s.eligibility.slice(0, 2).map((e, eIdx) => (
                              <li key={eIdx}>{e}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-slate-700 leading-relaxed">{s.eligibility}</p>
                        )}
                      </div>
                    </div>

                    {/* Required Documents Checklist */}
                    {s.requiredDocuments && s.requiredDocuments.length > 0 && (
                      <div className="text-xs pt-0.5">
                        <span className="font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5 text-slate-400" />
                          {t.schemesPage?.documentsLabel || 'Required Application Documents'}:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {s.requiredDocuments.map((doc, dIdx) => (
                            <span
                              key={dIdx}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-600 text-[11px]"
                            >
                              <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                              {doc}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Card Footer: Verification Date & Official Source Link */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                      <div className="flex items-center gap-3">
                        {s.verificationDate && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            {t.schemesPage?.verificationDate || 'Verified'}: {s.verificationDate}
                          </span>
                        )}
                        {s.sourceUrl && (
                          <a
                            href={s.sourceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-emerald-700 hover:text-emerald-900 font-medium hover:underline flex items-center gap-0.5"
                          >
                            <span>{t.schemesPage?.viewSource || 'Official Source'}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>

                      <button
                        type="button"
                        onClick={() => setSelectedScheme(s)}
                        className="text-emerald-700 hover:text-emerald-900 font-bold flex items-center gap-0.5 hover:underline"
                      >
                        <span>{language === 'ta' ? 'முழு விவரங்கள்' : 'Full Specifications'}</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <Info className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-600">
                {language === 'ta'
                  ? 'தேர்ந்தெடுக்கப்பட்ட வடிகட்டிகளுக்கு திட்டங்கள் எதுவும் கிடைக்கவில்லை.'
                  : 'No schemes found matching the selected filters.'}
              </p>
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={clearAllFilters}
                  className="px-3.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold hover:bg-emerald-100"
                >
                  {language === 'ta' ? 'அனைத்து வடிகட்டிகளையும் மீட்டமை' : 'Clear All Filters'}
                </button>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Detail Modal Component */}
      {selectedScheme && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-5 animate-scale-up">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 uppercase">
                    {selectedScheme.category}
                  </span>
                  {selectedScheme.governmentLevel && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {selectedScheme.governmentLevel} Govt
                    </span>
                  )}
                  {selectedScheme.applicationStatus && (
                    <Badge variant={getStatusBadgeVariant(selectedScheme.applicationStatus)}>
                      {formatStatus(selectedScheme.applicationStatus)}
                    </Badge>
                  )}
                </div>
                <h3 className="text-lg font-extrabold text-slate-900 leading-snug">
                  {language === 'ta'
                    ? selectedScheme.nameTa || selectedScheme.titleTa
                    : selectedScheme.name || selectedScheme.titleEn}
                </h3>
                <p className="text-xs text-slate-500 font-medium flex items-center gap-1">
                  <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>{selectedScheme.department || selectedScheme.dept}</span>
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedScheme(null)}
                className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="space-y-4 text-xs">
              {/* Description */}
              {selectedScheme.description && (
                <div>
                  <span className="font-extrabold text-slate-800 block mb-1">
                    {language === 'ta' ? 'திட்டத்தின் நோக்கம் / விளக்கம்:' : 'Scheme Summary & Objective:'}
                  </span>
                  <p className="text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {selectedScheme.description}
                  </p>
                </div>
              )}

              {/* Livestock Types */}
              {selectedScheme.livestockTypes && selectedScheme.livestockTypes.length > 0 && (
                <div>
                  <span className="font-extrabold text-slate-800 block mb-1">
                    🐾 {language === 'ta' ? 'பொருந்தும் கால்நடை வகைகள்:' : 'Target Livestock Types:'}
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedScheme.livestockTypes.map((type, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 font-semibold"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Benefits */}
              <div>
                <span className="font-extrabold text-emerald-950 block mb-1">
                  🎁 {t.schemesPage?.benefitsLabel || 'Benefits & Financial Assistance'}:
                </span>
                {Array.isArray(selectedScheme.benefits) && selectedScheme.benefits.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1.5 bg-emerald-50/50 p-3 rounded-xl border border-emerald-100 text-slate-700 leading-relaxed">
                    {selectedScheme.benefits.map((b, idx) => (
                      <li key={idx}>{b}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="bg-emerald-50/50 p-3 rounded-xl border border-emerald-100 text-slate-700 leading-relaxed">
                    {selectedScheme.benefit}
                  </p>
                )}
              </div>

              {/* Eligibility */}
              <div>
                <span className="font-extrabold text-slate-900 block mb-1">
                  👥 {t.schemesPage?.eligibilityLabel || 'Beneficiary Eligibility Criteria'}:
                </span>
                {Array.isArray(selectedScheme.eligibility) ? (
                  <ul className="list-disc list-inside space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-700 leading-relaxed">
                    {selectedScheme.eligibility.map((e, idx) => (
                      <li key={idx}>{e}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-700 leading-relaxed">
                    {selectedScheme.eligibility}
                  </p>
                )}
              </div>

              {/* Required Documents */}
              {selectedScheme.requiredDocuments && selectedScheme.requiredDocuments.length > 0 && (
                <div>
                  <span className="font-extrabold text-slate-900 block mb-1">
                    📄 {t.schemesPage?.documentsLabel || 'Required Documents'}:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {selectedScheme.requiredDocuments.map((doc, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 text-slate-700 text-[11px]"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Operational Notes */}
              {selectedScheme.notes && (
                <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/80 text-amber-950">
                  <span className="font-bold block mb-0.5">
                    📌 {language === 'ta' ? 'முக்கிய குறிப்பு:' : 'Application Guidance & Department Notes:'}
                  </span>
                  <p className="text-[11px] leading-relaxed text-amber-900">
                    {selectedScheme.notes}
                  </p>
                </div>
              )}

              {/* Verification & Source */}
              <div className="p-3 rounded-xl bg-slate-100 text-slate-600 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
                <span className="flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  {t.schemesPage?.verificationDate || 'Verified On'}:{' '}
                  <strong className="text-slate-800">{selectedScheme.verificationDate || '2026-10-20'}</strong>
                </span>

                {selectedScheme.sourceUrl && (
                  <a
                    href={selectedScheme.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-emerald-700 font-bold hover:underline"
                  >
                    <span>{t.schemesPage?.viewSource || 'View Official Department Source'}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {/* Statutory Disclaimer */}
              <p className="text-[10px] text-slate-500 leading-relaxed italic border-t border-slate-100 pt-2">
                {t.schemesPage?.disclaimerModal ||
                  'Official Statutory Notice: Final eligibility, subsidy sanctions, and fund allocations are determined solely by the competent officers of the respective government department. Always apply directly through the verified official government portals provided.'}
              </p>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedScheme(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
              >
                {t.schemesPage?.closeModal || 'Close'}
              </button>

              <a
                href={selectedScheme.applicationUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm"
              >
                <span>{t.schemesPage?.visitPortal || 'Visit Official Application Portal'}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

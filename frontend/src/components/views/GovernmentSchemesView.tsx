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
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  getGovernmentSchemesApi,
  type GovernmentSchemesResponse,
  type GovernmentSchemeItem,
} from '../../services/api';

const CATEGORIES = ['All', 'State', 'Central', 'Insurance', 'Irrigation', 'Machinery'];

export const GovernmentSchemesView: React.FC = () => {
  const { t, language } = useLanguage();

  const [category, setCategory] = useState<string>('All');
  const [data, setData] = useState<GovernmentSchemesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSchemes() {
      setLoading(true);
      setError(null);
      try {
        const res = await getGovernmentSchemesApi(category === 'All' ? undefined : category);
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load government welfare schemes.');
      } finally {
        setLoading(false);
      }
    }
    loadSchemes();
  }, [category]);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.schemes}
        subtitle={
          language === 'ta'
            ? 'மத்திய மற்றும் தமிழ்நாடு மாநில அரசு உழவர் நலத்திட்டங்கள் மற்றும் நேரடி மானியங்கள்'
            : 'Central & Tamil Nadu State Agricultural Welfare Schemes & Verified Portals'
        }
        icon={<Landmark className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <Badge variant="emerald" dot>
            Verified Official Portals
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Statutory Verification Notice */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-800">
                {language === 'ta'
                  ? 'அதிகாரப்பூர்வ அரசு வழிகாட்டுதல் மற்றும் சரிபார்ப்பு குறிப்பு'
                  : 'Official Government Portal Verification Policy'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? data?.disclaimerTa ||
                    'திட்ட மானியங்கள் மற்றும் நலத்திட்ட ஒப்புதல்கள் அனைத்தும் கிராம நிர்வாக அலுவலர் (VAO) மற்றும் வேளாண் துறை அலுவலர்களின் கள ஆய்வுக்கு உட்பட்டவை. நலம் பெறும் பொருட்டு விவசாயிகள் அதிகாரப்பூர்வ அரசு இணையதளங்கள் மூலமாக மட்டுமே விண்ணப்பிக்க வேண்டும்.'
                  : data?.disclaimerEn ||
                    'Scheme sanctions and DBT subsidy transfers are subject to revenue land records (Patta/Chitta) and field verification by competent agricultural officers. Antigravity/Namma Vivasayi does not guarantee application approval. Always apply directly through the verified official government portals provided below.'}
              </p>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1.5 mr-1">
              <Filter className="w-3.5 h-3.5" />
              Category:
            </span>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  category === cat
                    ? 'bg-emerald-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Schemes List */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold">Loading verified agricultural schemes...</p>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center">
              {error}
            </div>
          ) : data?.schemes && data.schemes.length > 0 ? (
            <div className="space-y-4">
              {data.schemes.map((s: GovernmentSchemeItem) => (
                <div
                  key={s.id}
                  className="p-5 rounded-2xl border border-slate-200 bg-white hover:border-emerald-300 hover:shadow-xs transition-all space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 uppercase">
                          {s.category}
                        </span>
                        <h4 className="text-sm sm:text-base font-extrabold text-slate-900 leading-snug">
                          {language === 'ta' ? s.titleTa : s.titleEn}
                        </h4>
                      </div>
                      <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1 mt-1">
                        <Building className="w-3 h-3 text-slate-400" />
                        {s.dept}
                      </p>
                    </div>

                    <a
                      href={s.applicationUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 hover:bg-emerald-600 hover:text-white border border-emerald-200 text-xs font-bold transition-all shrink-0 w-fit"
                    >
                      <span>{s.portalName}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  {/* Benefits and Eligibility Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                    <div>
                      <span className="font-extrabold text-emerald-950 block mb-0.5">
                        🎁 Subsidy / Financial Benefit:
                      </span>
                      <p className="text-slate-700 leading-relaxed">{s.benefit}</p>
                    </div>
                    <div>
                      <span className="font-extrabold text-slate-900 block mb-0.5">
                        👥 Eligibility Criteria:
                      </span>
                      <p className="text-slate-700 leading-relaxed">{s.eligibility}</p>
                    </div>
                  </div>

                  {/* Required Documents Checklist */}
                  {s.requiredDocuments && s.requiredDocuments.length > 0 && (
                    <div className="text-xs pt-1">
                      <span className="font-bold text-slate-700 block mb-1.5 flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        Required Application Documents:
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
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400">
              <p className="text-sm font-semibold">No schemes found in this category.</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

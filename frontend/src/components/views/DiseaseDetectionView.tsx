import React, { useState, useEffect, useRef } from 'react';
import {
  Bug,
  Camera,
  Upload,
  AlertTriangle,
  Info,
  CheckCircle2,
  FileText,
  ShieldAlert,
  Loader2,
  PhoneCall,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  analyzeDiseaseImageApi,
  getDiseaseCatalogApi,
  type DiseaseAnalysisResponse,
  type DiseaseCatalogItem,
} from '../../services/api';

export const DiseaseDetectionView: React.FC = () => {
  const { t, language } = useLanguage();

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<DiseaseAnalysisResponse | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // TNAU Reference Catalog
  const [catalog, setCatalog] = useState<DiseaseCatalogItem[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>('rice_blast');

  useEffect(() => {
    async function loadCatalog() {
      try {
        const res = await getDiseaseCatalogApi();
        if (res && res.catalog) {
          setCatalog(res.catalog);
        }
      } catch {
        // Fallback
      }
    }
    loadCatalog();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValidationError(null);
    setAnalysisResult(null);

    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setValidationError('Please select a valid image file (JPEG, PNG, or WEBP).');
      return;
    }

    // Validate size (< 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setValidationError('File size exceeds 5MB limit. Please upload a smaller compressed photo.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleSubmitAnalysis = async () => {
    if (!selectedFile) return;

    setAnalyzing(true);
    setValidationError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await analyzeDiseaseImageApi(formData);
      setAnalysisResult(res);
      if (res.referenceCatalog && res.referenceCatalog.length > 0) {
        setCatalog(res.referenceCatalog);
      }
    } catch (err: any) {
      setValidationError(err.message || 'Error uploading image to pathology service.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setAnalysisResult(null);
    setValidationError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Upload Interface */}
      <Card
        title={t.nav.disease}
        subtitle={
          language === 'ta'
            ? 'தாவர இலை நோய் மற்றும் பூச்சி தாக்குதல் புகைப்பட ஆய்வு மையம்'
            : 'Plant Pathology & Pest Diagnostics (Honest AI Status & TNAU Clinical Reference)'
        }
        icon={<Bug className="w-5 h-5 text-rose-600" />}
        headerAction={
          <Badge variant="red" dot>
            Pathology Verification
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Diagnostic Integrity Notice */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
            <Info className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-800">
                {language === 'ta'
                  ? 'கள நேர்மை கொள்கை (உண்மை அறிக்கை)'
                  : 'Diagnostic Integrity & Scientific Accuracy Policy'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? 'விவசாயிகளுக்கு தவறான அல்லது போலி நோய் அறிக்கைகள் வழங்கப்படாது. சரிபார்க்கப்பட்ட விஷன் மாடல் சேவையகத்தில் நிறுவப்படாத போது, சேவையகம் வெளிப்படையாக "ஆய்வு கட்டமைக்கப்படவில்லை" என்று தெரிவிக்கும்.'
                  : 'We strictly follow clinical integrity guidelines. The system never invents synthetic confidence scores or diagnoses when an inference engine is not configured. Instead, we connect farmers with verified TNAU visual symptom keys and government extension helplines.'}
              </p>
            </div>
          </div>

          {/* Upload Area */}
          <div className="border-2 border-dashed border-emerald-300 rounded-3xl p-6 sm:p-8 text-center bg-emerald-50/20">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />

            {previewUrl ? (
              <div className="space-y-4 max-w-sm mx-auto">
                <div className="relative rounded-2xl overflow-hidden border-2 border-emerald-500 shadow-md">
                  <img
                    src={previewUrl}
                    alt="Uploaded leaf specimen"
                    className="w-full h-56 object-cover"
                  />
                  <div className="absolute bottom-0 inset-x-0 bg-slate-900/70 backdrop-blur-xs text-white p-2 text-[11px] font-mono truncate">
                    {selectedFile?.name} ({(selectedFile?.size ? selectedFile.size / 1024 : 0).toFixed(1)} KB)
                  </div>
                </div>

                <div className="flex items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={handleSubmitAnalysis}
                    disabled={analyzing}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md flex items-center gap-2 disabled:opacity-50 transition-all active:scale-95"
                  >
                    {analyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Transmitting to Pathology Engine...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        {language === 'ta' ? 'ஆய்வுக்கு சமர்ப்பிக்கவும்' : 'Submit for Backend Analysis'}
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all"
                  >
                    Clear
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div className="w-16 h-16 mx-auto rounded-3xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3 shadow-xs">
                  <Camera className="w-8 h-8" />
                </div>
                <h4 className="text-sm sm:text-base font-bold text-slate-800">
                  {language === 'ta'
                    ? 'பாதிக்கப்பட்ட பயிர் இலையின் புகைப்படத்தை பதிவேற்றவும்'
                    : 'Upload photo of affected crop leaf or stem'}
                </h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  Supported formats: JPG, PNG, WEBP (Max size: 5MB). Ensure good natural lighting and close focus on leaf lesions.
                </p>

                <div className="mt-5">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-all active:scale-95"
                  >
                    <Upload className="w-4 h-4" />
                    <span>{language === 'ta' ? 'புகைப்படத்தை தேர்ந்தெடுக்க' : 'Select Leaf Image'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {/* Backend Response State */}
          {analysisResult && (
            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-300 text-amber-950">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-extrabold text-slate-900">
                        {language === 'ta'
                          ? 'சேவையக ஆய்வு நிலை: தானியங்கி AI மாடல் கட்டமைக்கப்படவில்லை'
                          : 'Backend Analysis Status: AI Vision Pathology Model Not Configured'}
                      </h4>
                      <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-amber-200 text-amber-900">
                        Truthful Status
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                      {language === 'ta' ? analysisResult.messageTa : analysisResult.messageEn}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-1 italic">
                      {analysisResult.truthfulnessNotice}
                    </p>
                  </div>
                </div>

                {/* Safe Next Steps */}
                {analysisResult.safeNextSteps && (
                  <div className="mt-4 pt-3 border-t border-amber-200/60 text-xs">
                    <h5 className="font-bold text-slate-900 mb-1.5 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Recommended Safe Next Steps for the Farmer:
                    </h5>
                    <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed">
                      {analysisResult.safeNextSteps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TNAU Visual Symptom Reference Guide */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  {language === 'ta'
                    ? 'TNAU அதிகாரப்பூர்வ பயிர் நோய் அடையாள வழிகாட்டி'
                    : 'TNAU Clinical Crop Disease Reference Keys (Visual Comparison)'}
                </h4>
                <p className="text-[11px] text-slate-400">
                  Compare your physical leaf specimen against verified pathology keys from Tamil Nadu Agricultural University.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {catalog.map((item) => {
                const isExpanded = expandedId === item.disease_id;
                return (
                  <div
                    key={item.disease_id}
                    className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-2xs"
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedId(isExpanded ? null : item.disease_id)}
                      className="w-full p-4 flex items-center justify-between gap-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs sm:text-sm text-slate-900">
                            {language === 'ta' ? item.name_ta : item.name_en}
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                            {item.crop}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                          Pathogen: {item.pathogen}
                        </p>
                      </div>
                      <div className="text-slate-400">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-1 border-t border-slate-100 space-y-3 text-xs">
                        {/* Symptoms */}
                        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="font-bold text-slate-700 block mb-1">
                            🔍 Key Visual Symptoms:
                          </span>
                          <p className="text-slate-600 leading-relaxed">
                            {language === 'ta' ? item.symptoms_ta : item.symptoms_en}
                          </p>
                        </div>

                        {/* Weather & Management */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                          <div className="p-3 rounded-xl bg-blue-50/50 border border-blue-100">
                            <span className="font-bold text-blue-900 block mb-1">
                              ☁️ Favorable Microclimate:
                            </span>
                            <p className="text-slate-600 text-[11px]">{item.favorable_weather}</p>
                          </div>
                          <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-100">
                            <span className="font-bold text-emerald-900 block mb-1">
                              🛡️ Recommended Management:
                            </span>
                            <p className="text-slate-600 text-[11px]">
                              {language === 'ta' ? item.recommended_management_ta : item.recommended_management_en}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Government Helpline Footer */}
          <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5">
              <PhoneCall className="w-5 h-5 text-emerald-700 shrink-0" />
              <div>
                <p className="font-bold text-emerald-950">
                  TNAU Kisan Call Centre (உழவன் உதவி மையம்)
                </p>
                <p className="text-[11px] text-emerald-800">
                  Toll-Free Agricultural Support: <strong>1800-425-1661</strong> (06:00 AM - 10:00 PM)
                </p>
              </div>
            </div>
            <a
              href="https://agritech.tnau.ac.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3.5 py-1.5 rounded-xl bg-white text-emerald-800 font-bold border border-emerald-300 hover:bg-emerald-100 flex items-center gap-1.5 transition-all text-[11px] shrink-0"
            >
              <span>TNAU Agritech Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
};

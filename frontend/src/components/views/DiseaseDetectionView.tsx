import React, { useState, useEffect, useRef } from 'react';
import {
  Bug,
  Activity,
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
  RefreshCw,
  Trash2,
  X,
  ShieldCheck,
  Sparkles,
  AlertCircle,
  Eye,
  Droplets,
  Leaf,
  FlaskConical,
  Layers,
  HelpCircle,
  RotateCcw,
  Clock,
  Shield,
  History,
  Calendar,
  BookmarkCheck,
  Lock,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  analyzeDiseaseImageApi,
  getDiseaseCatalogApi,
  listDiagnosisReportsApi,
  deleteDiagnosisReportApi,
  type DiseaseAnalysisResponse,
  type DiseaseCatalogItem,
  type DiagnosisCategory,
  type VerifiedTreatmentGuidance,
  type DiagnosisReportEntity,
} from '../../services/api';

const COMMON_CROPS = [
  { value: '', labelEn: 'Auto-detect Crop (தானாக கண்டறி)', labelTa: 'தானாக கண்டறி (பரிந்துரை)' },
  { value: 'Paddy / Rice (நெல்)', labelEn: 'Paddy / Rice', labelTa: 'நெல்' },
  { value: 'Groundnut (நிலக்கடலை)', labelEn: 'Groundnut', labelTa: 'நிலக்கடலை' },
  { value: 'Cotton (பருத்தி)', labelEn: 'Cotton', labelTa: 'பருத்தி' },
  { value: 'Sugarcane (கரும்பு)', labelEn: 'Sugarcane', labelTa: 'கரும்பு' },
  { value: 'Banana (வாழை)', labelEn: 'Banana', labelTa: 'வாழை' },
  { value: 'Blackgram / Pulses (பயறு)', labelEn: 'Pulses / Blackgram', labelTa: 'பயறு வகைகள்' },
  { value: 'Tomato / Vegetables (தக்காளி/காய்கறி)', labelEn: 'Tomato / Vegetables', labelTa: 'தக்காளி / காய்கறிகள்' },
  { value: 'Chilli (மிளகாய்)', labelEn: 'Chilli', labelTa: 'மிளகாய்' },
  { value: 'Maize / Corn (மக்காச்சோளம்)', labelEn: 'Maize / Corn', labelTa: 'மக்காச்சோளம்' },
  { value: 'Other', labelEn: 'Other Crop', labelTa: 'இதர பயிர்' },
];

const PLANT_PARTS = [
  { value: 'leaf', labelEn: 'Leaf (இலை)', labelTa: 'இலை' },
  { value: 'stem', labelEn: 'Stem / Tiller (தண்டு/குருத்து)', labelTa: 'தண்டு / குருத்து' },
  { value: 'panicle', labelEn: 'Panicle / Grain (கதிர்/மணி)', labelTa: 'கதிர் / தானியம்' },
  { value: 'fruit', labelEn: 'Fruit / Pod (காய்/கனி)', labelTa: 'காய் / கனி' },
  { value: 'root', labelEn: 'Root / Collar (வேர்/அடிப்பகுதி)', labelTa: 'வேர் / அடிப்பகுதி' },
  { value: 'whole_plant', labelEn: 'Whole Plant (முழு செடி)', labelTa: 'முழு செடி' },
];

export const DiseaseDetectionView: React.FC = () => {
  const { t, language } = useLanguage();

  // File upload state
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Authenticated farmer state & diagnosis history
  const { token, user, isAuthenticated } = useAuth();

  // Optional contextual hints from farmer
  const [selectedCrop, setSelectedCrop] = useState<string>('');
  const [selectedPlantPart, setSelectedPlantPart] = useState<string>('leaf');
  const [selectedDistrict, setSelectedDistrict] = useState<string>(user?.district || '');
  const [symptomNotes, setSymptomNotes] = useState<string>('');
  const [showContextOptions, setShowContextOptions] = useState<boolean>(false);

  // Live Camera state
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraLoading, setCameraLoading] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedSnapshotUrl, setCapturedSnapshotUrl] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);

  // Analysis state
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<DiseaseAnalysisResponse | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // TNAU Reference Catalog
  const [catalog, setCatalog] = useState<DiseaseCatalogItem[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>('rice_blast');

  // Authenticated farmer state & diagnosis history
  const [activeTab, setActiveTab] = useState<'scanner' | 'history'>('scanner');
  const [historyReports, setHistoryReports] = useState<DiagnosisReportEntity[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);

  // Fetch farmer's saved diagnosis reports
  const fetchHistory = async () => {
    if (!token) return;
    setLoadingHistory(true);
    setHistoryError(null);
    try {
      const data = await listDiagnosisReportsApi(token);
      setHistoryReports(data.reports || []);
    } catch (err: any) {
      setHistoryError(err.message || 'Failed to load diagnosis history');
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    if (!token) return;
    const confirmMsg = language === 'ta'
      ? 'இந்த ஆய்வு அறிக்கையை நிச்சயமாக நீக்க விரும்புகிறீர்களா?'
      : 'Are you sure you want to delete this diagnosis report? This action cannot be undone.';
    if (!window.confirm(confirmMsg)) return;

    setDeletingId(reportId);
    try {
      await deleteDiagnosisReportApi(reportId, token);
      setHistoryReports((prev) => prev.filter((r) => r.id !== reportId));
    } catch (err: any) {
      alert(err.message || 'Failed to delete report');
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewHistoricalReport = (report: DiagnosisReportEntity) => {
    const historicalAnalysis: DiseaseAnalysisResponse = {
      status: report.status || 'diagnosed',
      testedModelPresent: true,
      modelName: 'Gemini Vision (Archived Report)',
      filename: report.imageMetadata?.filename || 'historical_scan.jpg',
      fileSizeBytes: report.imageMetadata?.fileSizeBytes || 0,
      contentType: report.imageMetadata?.contentType || 'image/jpeg',
      messageEn: `Historical diagnostic report archived on ${new Date(report.createdAt).toLocaleDateString()}.`,
      messageTa: `${new Date(report.createdAt).toLocaleDateString()} அன்று சேமிக்கப்பட்ட வரலாற்று ஆய்வு அறிக்கை.`,
      truthfulnessNotice: 'This is an archived diagnostic finding saved from your past field evaluation.',
      safeNextSteps: report.recommendedNextSteps || [],
      diagnosis: {
        isCropLeaf: true,
        category: (report.category as any) || 'plant_disease',
        categoryLabelEn: report.categoryLabelEn || report.category,
        categoryLabelTa: report.categoryLabelTa || report.category,
        suspectedCondition: report.suspectedCondition,
        suspectedConditionTa: report.suspectedConditionTa,
        affectedCrop: report.crop,
        affectedCropTa: report.cropTa,
        plantPart: report.plantPart || 'leaf',
        pathogenOrCausalAgent: report.pathogenOrCausalAgent,
        confidencePercent: report.confidencePercent || 0,
        severityOrUrgency: (report.severityOrUrgency as any) || 'moderate',
        visualSymptoms: report.visualSymptoms || '',
        visualSymptomsTa: report.visualSymptomsTa,
        possibleCauses: report.possibleCauses || [],
        alternativeExplanations: report.alternativeExplanations || [],
        diagnosticLimitations: report.diagnosticLimitations || [],
        recommendedNextSteps: report.recommendedNextSteps || [],
        biologicalManagement: report.biologicalManagement || [],
        chemicalTreatment: report.chemicalTreatment,
        chemicalPrecautions: report.chemicalPrecautions,
        preventionTips: [],
        whenToConsultExpert: [],
        verifiedGuidanceReferences: report.verifiedGuidanceReferences || [],
        verifiedTreatment: report.verifiedTreatment,
        crop: report.crop,
        cropTa: report.cropTa,
        diseaseName: report.suspectedCondition,
        diseaseNameTa: report.suspectedConditionTa,
        pathogen: report.pathogenOrCausalAgent,
        severity: report.severityOrUrgency,
      },
      verifiedTreatment: report.verifiedTreatment,
      reportId: report.id,
      saved: true,
    };

    setAnalysisResult(historicalAnalysis);
    setActiveTab('scanner');
    window.scrollTo({ top: 300, behavior: 'smooth' });
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchHistory();
    }
  }, [isAuthenticated, token]);

  // Load verified TNAU reference catalog on mount
  useEffect(() => {
    let isMounted = true;
    async function loadCatalog() {
      try {
        const res = await getDiseaseCatalogApi();
        if (isMounted && res && res.catalog) {
          setCatalog(res.catalog);
        }
      } catch {
        // Graceful fallback
      }
    }
    loadCatalog();
    return () => {
      isMounted = false;
    };
  }, []);

  // ============================================================================
  // CAMERA CONTROLS
  // ============================================================================

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore track stop error
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    setCameraLoading(false);
  };

  // Cleanup camera tracks and object URLs on unmount
  useEffect(() => {
    return () => {
      stopCamera();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (capturedSnapshotUrl) URL.revokeObjectURL(capturedSnapshotUrl);
    };
  }, [previewUrl, capturedSnapshotUrl]);

  const startCamera = async () => {
    setCameraError(null);
    setValidationError(null);
    setCapturedSnapshotUrl(null);
    setCapturedBlob(null);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError(
        language === 'ta'
          ? 'உங்கள் உலாவியில் நேரடி கேமரா ஆதரிக்கப்படவில்லை. புகைப்பட பதிவேற்றத்தைப் பயன்படுத்தவும்.'
          : 'Live camera capture is not supported by your browser. Please use the image upload option.'
      );
      return;
    }

    setCameraLoading(true);
    setIsCameraActive(true);

    try {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      };

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setCameraLoading(false);
    } catch (err: any) {
      stopCamera();
      let errorMsg = language === 'ta'
        ? 'கேமராவைத் திறக்க முடியவில்லை.'
        : 'Unable to access camera.';

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMsg = language === 'ta'
          ? 'கேமரா அனுமதி மறுக்கப்பட்டது. உங்கள் உலாவி அமைப்பில் கேமரா அனுமதியை இயக்கவும்.'
          : 'Camera permission denied. Please allow camera access in your browser settings to take live leaf photos.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMsg = language === 'ta'
          ? 'உங்கள் சாதனத்தில் கேமரா எதுவும் கண்டறியப்படவில்லை. புகைப்பட பதிவேற்றத்தைப் பயன்படுத்தவும்.'
          : 'No camera hardware found on this device. Please select an image file from storage.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMsg = language === 'ta'
          ? 'கேமரா மற்றொரு செயலியில் பயன்பாட்டில் உள்ளது. தயவுசெய்து மற்ற செயலிகளை மூடவும்.'
          : 'Camera is currently locked or in use by another application.';
      }
      setCameraError(errorMsg);
    }
  };

  const handleCaptureSnapshot = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        setCapturedBlob(blob);
        if (capturedSnapshotUrl) URL.revokeObjectURL(capturedSnapshotUrl);
        const snapshotUrl = URL.createObjectURL(blob);
        setCapturedSnapshotUrl(snapshotUrl);
      },
      'image/jpeg',
      0.92
    );
  };

  const handleRetakeSnapshot = () => {
    if (capturedSnapshotUrl) {
      URL.revokeObjectURL(capturedSnapshotUrl);
      setCapturedSnapshotUrl(null);
    }
    setCapturedBlob(null);
  };

  const handleConfirmCapturedPhoto = () => {
    if (!capturedBlob) return;

    const filename = `leaf_specimen_${Date.now()}.jpg`;
    const file = new File([capturedBlob], filename, { type: 'image/jpeg' });

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setAnalysisResult(null);
    setValidationError(null);

    stopCamera();
    if (capturedSnapshotUrl) {
      URL.revokeObjectURL(capturedSnapshotUrl);
      setCapturedSnapshotUrl(null);
    }
    setCapturedBlob(null);
  };

  const handleCancelCamera = () => {
    stopCamera();
    if (capturedSnapshotUrl) {
      URL.revokeObjectURL(capturedSnapshotUrl);
      setCapturedSnapshotUrl(null);
    }
    setCapturedBlob(null);
    setCameraError(null);
  };

  // ============================================================================
  // FILE UPLOAD CONTROLS
  // ============================================================================

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValidationError(null);
    setAnalysisResult(null);

    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setValidationError(
        language === 'ta'
          ? 'சரியான புகைப்பட கோப்பைத் தேர்ந்தெடுக்கவும் (JPG, JPEG, PNG, அல்லது WEBP).'
          : 'Please select a valid image file format (JPG, JPEG, PNG, or WEBP).'
      );
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setValidationError(
        language === 'ta'
          ? 'கோப்பு அளவு 5MB வரம்பை மீறுகிறது. தயவுசெய்து சிறிய புகைப்படத்தை பதிவேற்றவும்.'
          : 'File size exceeds 5MB limit. Please upload a compressed photo under 5MB.'
      );
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleRemoveImage = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setAnalysisResult(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleReplaceImage = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // ============================================================================
  // SUBMISSION TO MULTI-CATEGORY BACKEND PIPELINE
  // ============================================================================

  const handleSubmitAnalysis = async () => {
    if (!selectedFile || analyzing) return;

    setAnalyzing(true);
    setValidationError(null);
    setSaveNotice(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (selectedCrop && selectedCrop.trim()) formData.append('crop_name', selectedCrop.trim());
    if (selectedPlantPart && selectedPlantPart.trim()) formData.append('plant_part', selectedPlantPart.trim());
    const districtToSend = selectedDistrict.trim() || user?.district || '';
    if (districtToSend) formData.append('district', districtToSend);
    if (symptomNotes.trim()) formData.append('symptom_description', symptomNotes.trim());

    try {
      const res = await analyzeDiseaseImageApi(formData, language, token);
      setAnalysisResult(res);
      if (res.referenceCatalog && res.referenceCatalog.length > 0) {
        setCatalog(res.referenceCatalog);
      }
      if (res.saved && res.reportId) {
        setSaveNotice(
          language === 'ta'
            ? `அறிக்கை உங்கள் பாதுகாப்பான வரலாற்றில் சேமிக்கப்பட்டது (அறிக்கை எண்: ${res.reportId.slice(-6)})`
            : `Report saved to your secure history (Report ID: ${res.reportId.slice(-6)})`
        );
        if (token) fetchHistory();
      }
    } catch (err: any) {
      setValidationError(
        err.message ||
          (language === 'ta'
            ? 'நோய் ஆய்வு சேவையகத்துடன் இணைக்க முடியவில்லை.'
            : 'Error transmitting specimen to pathology service. Please check your connection.')
      );
    } finally {
      setAnalyzing(false);
    }
  };



  // Category Badge Helper
  const renderCategoryBadge = (category: DiagnosisCategory) => {
    switch (category) {
      case 'pest_damage':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
            <Bug className="w-3.5 h-3.5 text-amber-700" />
            {language === 'ta' ? 'வகை 1: பூச்சி தாக்குதல்' : 'Category 1: Pest & Insect Damage'}
          </span>
        );
      case 'plant_disease':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-300">
            <Activity className="w-3.5 h-3.5 text-rose-700" />
            {language === 'ta' ? 'வகை 2: பயிர் நோய்' : 'Category 2: Plant Disease'}
          </span>
        );
      case 'abiotic_disorder':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-sky-100 text-sky-900 border border-sky-300">
            <Droplets className="w-3.5 h-3.5 text-sky-700" />
            {language === 'ta' ? 'வகை 3: உடலியல் / ஊட்டச்சத்து குறைபாடு' : 'Category 3: Abiotic & Physiological Disorder'}
          </span>
        );
      case 'healthy':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
            {language === 'ta' ? 'ஆரோக்கியமான பயிர்' : 'Healthy Crop Foliage'}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-300">
            <HelpCircle className="w-3.5 h-3.5 text-slate-600" />
            {language === 'ta' ? 'தெளிவற்ற நிலை' : 'Inconclusive Specimen'}
          </span>
        );
    }
  };

  const renderSeverityBadge = (severity: string) => {
    const sev = severity.toLowerCase();
    let bg = 'bg-slate-100 text-slate-700';
    if (sev === 'critical') bg = 'bg-rose-600 text-white animate-pulse';
    else if (sev === 'high') bg = 'bg-rose-100 text-rose-800 border border-rose-300';
    else if (sev === 'moderate') bg = 'bg-amber-100 text-amber-800 border border-amber-300';
    else if (sev === 'low') bg = 'bg-emerald-100 text-emerald-800 border border-emerald-300';

    return (
      <span className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${bg}`}>
        {severity}
      </span>
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,image/webp,image/jpg"
        className="hidden"
      />
      <canvas ref={canvasRef} className="hidden" />

      {/* Main Container Card */}
      <Card
        title={t.nav.disease}
        subtitle={
          language === 'ta'
            ? 'விரிவான பயிர் நலம் & நோய் ஆய்வு மையம் (பூச்சிகள், நோய்கள், ஊட்டச்சத்து குறைபாடுகள்)'
            : 'Comprehensive Crop Health Diagnostics (Pests, Diseases & Abiotic Disorders)'
        }
        icon={<Bug className="w-5 h-5 text-rose-600" />}
        headerAction={
          <Badge variant="emerald" dot>
            {language === 'ta' ? '3-வகை AI ஆய்வு' : '3-Category AI Pipeline'}
          </Badge>
        }
      >
        <div className="space-y-6">
          {/* Save notification banner */}
          {saveNotice && (
            <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-950 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs animate-fade-in">
              <div className="flex items-center gap-2.5">
                <BookmarkCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="font-medium">{saveNotice}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActiveTab('history');
                  fetchHistory();
                }}
                className="text-xs font-bold text-emerald-700 hover:text-emerald-900 underline shrink-0 cursor-pointer"
              >
                {language === 'ta' ? 'வரலாற்றில் காண்க →' : 'View in History →'}
              </button>
            </div>
          )}

          {/* Tab Selector: Diagnostic Scanner vs Diagnosis History */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            <button
              type="button"
              onClick={() => setActiveTab('scanner')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeTab === 'scanner'
                  ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Camera className="w-4 h-4" />
              <span>{language === 'ta' ? 'புதிய பயிர் ஆய்வு' : 'Crop Diagnostic Scanner'}</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveTab('history');
                fetchHistory();
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeTab === 'history'
                  ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <History className="w-4 h-4" />
              <span>{language === 'ta' ? 'என் ஆய்வு வரலாறு' : 'My Diagnosis History'}</span>
              {isAuthenticated && historyReports.length > 0 && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-black ${
                    activeTab === 'history' ? 'bg-white text-emerald-800' : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {historyReports.length}
                </span>
              )}
            </button>
          </div>

          {/* SCANNER TAB CONTENT */}
          {activeTab === 'scanner' && (
            <div className="space-y-6">
              {/* Integrity & Tri-Category Notice */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
            <Info className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-bold text-slate-800">
                {language === 'ta'
                  ? '3-வகை கள ஆய்வு & அறிவியல் நேர்மை கொள்கை'
                  : 'Three-Category Clinical Pathology & Scientific Integrity Policy'}
              </p>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                {language === 'ta'
                  ? 'இந்த அமைப்பு 1) பூச்சி தாக்குதல், 2) பூஞ்சை/பாக்டீரியா/வைரஸ் நோய்கள், மற்றும் 3) ஊட்டச்சத்து/நீர்/வெப்ப உடலியல் குறைபாடுகளை துல்லியமாக வேறுபடுத்தி பகுப்பாய்வு செய்கிறது. தெளிவற்ற மாதிரிகளுக்கு போலி அறிக்கைகள் வழங்கப்படாது.'
                  : 'The system distinguishes strictly between 1) Pest & insect damage, 2) Infectious diseases (fungal, bacterial, viral), and 3) Abiotic & nutrient disorders (NPK, drought, waterlogging, salinity). Evidence-based caution is exercised, and inconclusive specimens are flagged honestly without fabricating diagnoses.'}
              </p>
            </div>
          </div>

          {/* ================================================================= */}
          {/* LIVE CAMERA OVERLAY VIEWFINDER                                    */}
          {/* ================================================================= */}
          {isCameraActive && (
            <div className="rounded-3xl border-2 border-emerald-500 bg-slate-950 p-4 sm:p-6 text-white shadow-xl space-y-4 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  <span className="text-xs sm:text-sm font-bold tracking-wide">
                    {language === 'ta' ? 'நேரடி கேமரா பார்வை' : 'Live Camera Viewfinder'}
                  </span>
                  <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">
                    {language === 'ta' ? 'பின்புற லென்ஸ் பரிந்துரை' : 'Rear Lens Preferred'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleCancelCamera}
                  className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                  aria-label="Close Camera"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {cameraLoading ? (
                <div className="h-64 sm:h-80 flex flex-col items-center justify-center gap-3 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                  <p className="text-xs">
                    {language === 'ta' ? 'கேமரா தொடங்குகிறது...' : 'Initializing camera stream...'}
                  </p>
                </div>
              ) : capturedSnapshotUrl ? (
                <div className="space-y-4">
                  <div className="relative rounded-2xl overflow-hidden border border-slate-700 max-h-80 flex items-center justify-center bg-black">
                    <img
                      src={capturedSnapshotUrl}
                      alt="Captured leaf snapshot"
                      className="max-h-80 w-auto object-contain"
                    />
                    <div className="absolute top-2 left-2 px-2.5 py-1 rounded-lg bg-slate-900/80 backdrop-blur-xs text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {language === 'ta' ? 'படம் எடுக்கப்பட்டது' : 'Photo Captured'}
                    </div>
                  </div>

                  <p className="text-center text-xs text-slate-400">
                    {language === 'ta'
                      ? 'இலையின் நோய் அறிகுறிகள் தெளிவாக உள்ளனவா என்பதை சரிபார்க்கவும்.'
                      : 'Verify that leaf lesions, pest damage, or chlorotic patterns are clearly focused in natural daylight.'}
                  </p>

                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleRetakeSnapshot}
                      className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-2 transition-all active:scale-95"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>{language === 'ta' ? 'மறுபடியும் படம் எடு' : 'Retake'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmCapturedPhoto}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-900/30 transition-all active:scale-95"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{language === 'ta' ? 'இந்த படத்தை பயன்படுத்தவும்' : 'Use This Photo'}</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-black aspect-4/3 max-h-80 mx-auto flex items-center justify-center">
                    <video
                      ref={videoRef}
                      playsInline
                      muted
                      autoPlay
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-6 sm:inset-10 border-2 border-dashed border-emerald-400/70 rounded-2xl pointer-events-none flex items-center justify-center">
                      <span className="text-[11px] text-emerald-300 font-bold bg-slate-900/70 px-3 py-1 rounded-full backdrop-blur-xs">
                        {language === 'ta'
                          ? 'பாதிக்கப்பட்ட தாவர பகுதியை இந்த சட்டகத்தில் வைக்கவும்'
                          : 'Position affected plant part within this frame'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-center gap-3">
                    <button
                      type="button"
                      onClick={handleCaptureSnapshot}
                      className="px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-bold shadow-lg shadow-emerald-900/40 flex items-center gap-2 transition-all active:scale-95"
                    >
                      <Camera className="w-4 h-4" />
                      <span>{language === 'ta' ? 'புகைப்படம் எடு' : 'Capture Photo'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelCamera}
                      className="px-4 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-all"
                    >
                      {language === 'ta' ? 'ரத்து செய்' : 'Cancel'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Camera Error Banner */}
          {cameraError && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-2 animate-fade-in">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{cameraError}</span>
              </div>
              <button
                type="button"
                onClick={() => setCameraError(null)}
                className="text-rose-600 hover:text-rose-800 text-xs font-bold"
              >
                ✕
              </button>
            </div>
          )}

          {/* ================================================================= */}
          {/* UPLOAD & PREVIEW AREA                                             */}
          {/* ================================================================= */}
          {!isCameraActive && (
            <div className="border-2 border-dashed border-emerald-300 rounded-3xl p-6 sm:p-8 text-center bg-emerald-50/20 space-y-4">
              {previewUrl ? (
                /* Selected / Captured Image Preview */
                <div className="space-y-4 max-w-md mx-auto">
                  <div className="relative rounded-2xl overflow-hidden border-2 border-emerald-500 shadow-md bg-slate-900">
                    <img
                      src={previewUrl}
                      alt="Uploaded leaf specimen"
                      className="w-full h-64 object-contain"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-slate-900/80 backdrop-blur-xs text-white p-2.5 text-[11px] font-mono flex items-center justify-between">
                      <span className="truncate max-w-[220px]">{selectedFile?.name}</span>
                      <span>
                        {(selectedFile?.size ? selectedFile.size / 1024 : 0).toFixed(1)} KB
                      </span>
                    </div>
                  </div>

                  {/* Optional Contextual Helpers Drawer */}
                  <div className="border border-emerald-200 rounded-2xl p-3 bg-white text-left space-y-2 text-xs">
                    <button
                      type="button"
                      onClick={() => setShowContextOptions(!showContextOptions)}
                      className="w-full flex items-center justify-between text-slate-700 font-bold text-[11px]"
                    >
                      <span className="flex items-center gap-1.5 text-emerald-800">
                        <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                        {language === 'ta'
                          ? 'பயிர் விவரங்கள் (துல்லியத்தை மேம்படுத்த விருப்பத்தேர்வு)'
                          : 'Crop Details (Optional for enhanced precision)'}
                      </span>
                      {showContextOptions ? (
                        <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </button>

                    {showContextOptions && (
                      <div className="space-y-2.5 pt-2 border-t border-slate-100 animate-fade-in text-xs">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                          <div>
                            <label className="text-[10px] font-bold text-slate-600 block mb-1">
                              {language === 'ta' ? 'பயிர் வகை:' : 'Crop Type:'}
                            </label>
                            <select
                              value={selectedCrop}
                              onChange={(e) => setSelectedCrop(e.target.value)}
                              className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-emerald-500"
                            >
                              {COMMON_CROPS.map((c) => (
                                <option key={c.value} value={c.value}>
                                  {language === 'ta' ? c.labelTa : c.labelEn}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-slate-600 block mb-1">
                              {language === 'ta' ? 'தாவர பகுதி:' : 'Plant Part:'}
                            </label>
                            <select
                              value={selectedPlantPart}
                              onChange={(e) => setSelectedPlantPart(e.target.value)}
                              className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-emerald-500"
                            >
                              {PLANT_PARTS.map((p) => (
                                <option key={p.value} value={p.value}>
                                  {language === 'ta' ? p.labelTa : p.labelEn}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-slate-600 block mb-1">
                              {language === 'ta' ? 'மாவட்டம் (விருப்பம்):' : 'District (Optional):'}
                            </label>
                            <input
                              type="text"
                              value={selectedDistrict}
                              onChange={(e) => setSelectedDistrict(e.target.value)}
                              placeholder={language === 'ta' ? 'எ.கா: தஞ்சாவூர், சேலம்' : 'e.g., Thanjavur, Salem'}
                              className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-emerald-500"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="text-[10px] font-bold text-slate-600 block mb-1">
                            {language === 'ta'
                              ? 'கள அறிகுறிகள் / குறிப்புகள் (விருப்பம்):'
                              : 'Field Observations / Notes (Optional):'}
                          </label>
                          <input
                            type="text"
                            value={symptomNotes}
                            onChange={(e) => setSymptomNotes(e.target.value)}
                            placeholder={
                              language === 'ta'
                                ? 'எ.கா: மழைக்கு பின் இலை ஓரங்களில் மஞ்சள் நிற புள்ளிகள்'
                                : 'e.g., yellow spots on leaf margins after heavy rain'
                            }
                            className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-emerald-500"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Primary & Auxiliary Actions */}
                  <div className="flex flex-wrap items-center justify-center gap-2.5 pt-1">
                    <button
                      type="button"
                      onClick={handleSubmitAnalysis}
                      disabled={analyzing}
                      className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-700/20 flex items-center gap-2 disabled:opacity-50 transition-all active:scale-95"
                    >
                      {analyzing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>
                            {language === 'ta'
                              ? '3-வகை AI ஆய்வுக்கு அனுப்பப்படுகிறது...'
                              : 'Transmitting to Diagnostic Engine...'}
                          </span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          <span>
                            {language === 'ta'
                              ? 'பயிர் நலம் ஆய்வு செய்'
                              : 'Run Crop Health Diagnosis'}
                          </span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={handleReplaceImage}
                      disabled={analyzing}
                      className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>{language === 'ta' ? 'மாற்றவும்' : 'Replace'}</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleRemoveImage}
                      disabled={analyzing}
                      className="px-3.5 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>{language === 'ta' ? 'அகற்றவும்' : 'Remove'}</span>
                    </button>
                  </div>
                </div>
              ) : (
                /* Unselected State */
                <div className="space-y-4 max-w-lg mx-auto">
                  <div className="w-16 h-16 mx-auto rounded-3xl bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-xs">
                    <Camera className="w-8 h-8" />
                  </div>

                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-slate-800">
                      {language === 'ta'
                        ? 'பாதிக்கப்பட்ட பயிர் இலையின் புகைப்படத்தை வழங்கவும்'
                        : 'Provide photo of affected crop leaf or stem'}
                    </h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                      {language === 'ta'
                        ? 'நேரடி கேமரா மூலம் படம் எடுக்கவும் அல்லது உங்கள் சாதனத்திலிருந்து பதிவேற்றவும் (JPG, PNG, WEBP, அதிகபட்சம் 5MB).'
                        : 'Take a live photograph or select an image file (JPG, PNG, WEBP, max 5MB). Covers pests, infectious diseases, and nutrient deficiencies.'}
                    </p>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={startCamera}
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-700/20 transition-all active:scale-95"
                    >
                      <Camera className="w-4 h-4" />
                      <span>{language === 'ta' ? 'நேரடி படம் எடு' : 'Take Live Photo'}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold border border-slate-300 shadow-xs transition-all active:scale-95"
                    >
                      <Upload className="w-4 h-4 text-emerald-600" />
                      <span>{language === 'ta' ? 'படத்தை பதிவேற்றவும்' : 'Upload Image'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Validation Error Banner */}
          {validationError && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-2 animate-fade-in">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{validationError}</span>
              </div>
              <button
                type="button"
                onClick={() => setValidationError(null)}
                className="text-rose-600 hover:text-rose-800 text-xs font-bold"
              >
                ✕
              </button>
            </div>
          )}

          {/* ================================================================= */}
          {/* SEVEN-SECTION DIAGNOSIS WORKFLOW PRESENTATION                      */}
          {/* ================================================================= */}
          {analysisResult && (
            <div className="space-y-6 pt-2 border-t border-slate-200 animate-fade-in">
              {/* IMAGE QUALITY & RETAKE FEEDBACK */}
              {analysisResult.imageQuality && analysisResult.imageQuality.warnings && analysisResult.imageQuality.warnings.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 space-y-2 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <span className="font-bold flex items-center gap-1.5 text-amber-800">
                      <Camera className="w-4 h-4 text-amber-600" />
                      {language === 'ta' ? 'படத் தர பகுப்பாய்வு & குறிப்புகள்' : 'Image Quality Assessment'}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold">
                      Score: {analysisResult.imageQuality.qualityScore}/100
                    </span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-800/90 pl-1">
                    {analysisResult.imageQuality.warnings.map((w, idx) => (
                      <li key={idx}><strong>Notice:</strong> {w}</li>
                    ))}
                  </ul>
                  {((language === 'ta' ? analysisResult.imageQuality.retakeGuidanceTa : analysisResult.imageQuality.retakeGuidanceEn) || []).length > 0 && (
                    <div className="pt-1 border-t border-amber-200/60 text-[11px]">
                      <span className="font-bold text-amber-950 block mb-0.5">
                        {language === 'ta' ? 'மறுபடம் எடுக்கும் வழிகாட்டல்:' : 'Retake Guidance for Higher Accuracy:'}
                      </span>
                      <ul className="list-disc list-inside space-y-0.5 text-amber-900 pl-1">
                        {(language === 'ta' ? analysisResult.imageQuality.retakeGuidanceTa : analysisResult.imageQuality.retakeGuidanceEn).map((g, idx) => (
                          <li key={idx}>{g}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* CASE 1: REAL DIAGNOSIS PRODUCED (ALL 7 SECTIONS) */}
              {(analysisResult.status === 'diagnosed' || analysisResult.status === 'suspected') && analysisResult.diagnosis ? (
                <div className="space-y-4">
                  {/* ========================================================= */}
                  {/* SECTION 1: DIAGNOSIS SUMMARY                              */}
                  {/* ========================================================= */}
                  <div className="rounded-3xl border-2 border-emerald-500 bg-linear-to-b from-emerald-50/70 to-white p-5 sm:p-6 shadow-sm space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-emerald-100 pb-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          {renderCategoryBadge(analysisResult.diagnosis.category)}
                          <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                            {language === 'ta'
                              ? analysisResult.diagnosis.affectedCropTa || analysisResult.diagnosis.affectedCrop
                              : analysisResult.diagnosis.affectedCrop}
                          </span>
                          {analysisResult.diagnosis.plantPart && (
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                              Part: {analysisResult.diagnosis.plantPart}
                            </span>
                          )}
                          {analysisResult.status === 'suspected' && (
                            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                              {language === 'ta'
                                ? 'சந்தேகிக்கப்படும் நிலை (சரிபார்ப்பு தேவை)'
                                : 'Suspected Condition (Verification Advised)'}
                            </span>
                          )}
                        </div>

                        <h3 className="text-base sm:text-lg font-black text-slate-900 mt-2">
                          {language === 'ta'
                            ? analysisResult.diagnosis.suspectedConditionTa || analysisResult.diagnosis.suspectedCondition
                            : analysisResult.diagnosis.suspectedCondition}
                        </h3>

                        {analysisResult.diagnosis.pathogenOrCausalAgent && (
                          <p className="text-xs text-slate-500 font-mono mt-0.5">
                            Causal Agent: {analysisResult.diagnosis.pathogenOrCausalAgent}
                          </p>
                        )}
                      </div>

                      <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2 bg-white p-3 rounded-2xl border border-emerald-100 shadow-2xs shrink-0">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          {language === 'ta' ? 'அவசர நிலை' : 'Urgency / Severity'}
                        </span>
                        <div>{renderSeverityBadge(analysisResult.diagnosis.severityOrUrgency)}</div>
                        <span className="text-[10px] font-mono text-slate-400">
                          Confidence: {analysisResult.diagnosis.confidencePercent}%
                        </span>
                      </div>
                    </div>

                    {/* Diagnostic Limitations Notice */}
                    {analysisResult.diagnosis.diagnosticLimitations && analysisResult.diagnosis.diagnosticLimitations.length > 0 && (
                      <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-950 text-xs flex items-start gap-2.5">
                        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                        <div className="space-y-0.5">
                          <span className="font-bold block text-[11px]">
                            {language === 'ta' ? 'ஆய்வு வரம்புகள்:' : 'Diagnostic Limitations:'}
                          </span>
                          <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-900">
                            {analysisResult.diagnosis.diagnosticLimitations.map((lim, idx) => (
                              <li key={idx}>{lim}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ========================================================= */}
                  {/* SECTION 2: SYMPTOMS DETECTED                              */}
                  {/* ========================================================= */}
                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <Eye className="w-4 h-4 text-emerald-600" />
                      {language === 'ta' ? '2. கண்டறியப்பட்ட புல அறிகுறிகள்' : '2. Symptoms Detected on Specimen'}
                    </h4>
                    <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                      {language === 'ta'
                        ? analysisResult.diagnosis.visualSymptomsTa || analysisResult.diagnosis.visualSymptoms
                        : analysisResult.diagnosis.visualSymptoms}
                    </p>
                  </div>

                  {/* ========================================================= */}
                  {/* SECTION 3: WHY THIS MIGHT HAVE HAPPENED                    */}
                  {/* ========================================================= */}
                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-blue-600" />
                      {language === 'ta' ? '3. இது ஏன் ஏற்பட்டிருக்கலாம்?' : '3. Why This Might Have Happened'}
                    </h4>

                    {analysisResult.diagnosis.possibleCauses && analysisResult.diagnosis.possibleCauses.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[11px] font-bold text-slate-700 block">
                          {language === 'ta' ? 'முதன்மை காரணங்கள் & சூழல் தூண்டல்கள்:' : 'Primary Environmental & Cultural Triggers:'}
                        </span>
                        <ul className="list-disc list-inside space-y-1 text-xs text-slate-600 bg-blue-50/40 p-3 rounded-xl border border-blue-100">
                          {analysisResult.diagnosis.possibleCauses.map((cause, idx) => (
                            <li key={idx}>{cause}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {analysisResult.diagnosis.alternativeExplanations && analysisResult.diagnosis.alternativeExplanations.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <span className="text-[11px] font-bold text-slate-700 block">
                          {language === 'ta' ? 'மாற்று சாத்தியக்கூறுகள் (வேறுபட்ட நோயறிதல்):' : 'Alternative Possibilities (Differential Diagnoses):'}
                        </span>
                        <ul className="list-disc list-inside space-y-1 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                          {analysisResult.diagnosis.alternativeExplanations.map((alt, idx) => (
                            <li key={idx}>{alt}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* ========================================================= */}
                  {/* SECTION 4 & 5: DUAL MANAGEMENT PROTOCOLS                  */}
                  {/* ========================================================= */}
                  {(() => {
                    const verifiedTreatment: VerifiedTreatmentGuidance | undefined =
                      (analysisResult as any).verifiedTreatment || analysisResult.diagnosis.verifiedTreatment;
                    const isAbiotic = analysisResult.diagnosis.category === 'abiotic_disorder';
                    const hasVerifiedChemical = verifiedTreatment?.chemicalManagement?.isApplicable;

                    return (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* SECTION 4: Biological and Non-Chemical Management */}
                        <div className="p-5 rounded-2xl bg-emerald-50/70 border border-emerald-200 shadow-xs space-y-3">
                          <div className="flex items-center justify-between gap-2 border-b border-emerald-200/70 pb-2">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-950 flex items-center gap-1.5">
                              <Leaf className="w-4 h-4 text-emerald-700" />
                              {language === 'ta' ? '4. இயற்கை & உயிரியல் மேலாண்மை' : '4. Biological & Cultural Management'}
                            </h4>
                            <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100/90 px-2 py-0.5 rounded-full border border-emerald-300">
                              TNAU / ICAR Verified
                            </span>
                          </div>

                          {verifiedTreatment?.biologicalManagement ? (
                            <div className="space-y-3 text-xs text-emerald-950">
                              {/* Cultural & Preventive Practices */}
                              {verifiedTreatment.biologicalManagement.culturalPractices?.length > 0 && (
                                <div className="space-y-1">
                                  <span className="text-[11px] font-bold text-emerald-900 block">
                                    {language === 'ta' ? 'பயிர்க்கிரியை & உழவியல் முறைகள்:' : 'Cultural & Preventive Practices:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-1 text-emerald-900/90 leading-relaxed pl-1">
                                    {verifiedTreatment.biologicalManagement.culturalPractices.map((c: string, idx: number) => (
                                      <li key={idx}>{c}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Field Sanitation */}
                              {verifiedTreatment.biologicalManagement.fieldSanitation?.length > 0 && (
                                <div className="space-y-1">
                                  <span className="text-[11px] font-bold text-emerald-900 block">
                                    {language === 'ta' ? 'வயல் தூய்மை & நோய் எச்சங்கள் நீக்குதல்:' : 'Field Sanitation & Debris Disposal:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-1 text-emerald-900/90 leading-relaxed pl-1">
                                    {verifiedTreatment.biologicalManagement.fieldSanitation.map((f: string, idx: number) => (
                                      <li key={idx}>{f}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Resistant Varieties & Rotation */}
                              {verifiedTreatment.biologicalManagement.cropRotationAndVarieties?.length > 0 && (
                                <div className="space-y-1">
                                  <span className="text-[11px] font-bold text-emerald-900 block">
                                    {language === 'ta' ? 'நோய் எதிர்ப்பு ரகங்கள் & பயிர் சுழற்சி:' : 'Resistant Varieties & Crop Rotation:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-1 text-emerald-900/90 leading-relaxed pl-1">
                                    {verifiedTreatment.biologicalManagement.cropRotationAndVarieties.map((v: string, idx: number) => (
                                      <li key={idx}>{v}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Biocontrol Agents */}
                              {verifiedTreatment.biologicalManagement.biologicalControlAgents?.length > 0 && (
                                <div className="space-y-1 bg-white/70 p-2.5 rounded-xl border border-emerald-200">
                                  <span className="text-[11px] font-bold text-emerald-900 block">
                                    {language === 'ta' ? 'உயிரியல் கட்டுப்பாட்டு முகவர்கள் (Bio-Control):' : 'Biological Control Agents & Biopesticides:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-1 text-emerald-900 leading-relaxed pl-1">
                                    {verifiedTreatment.biologicalManagement.biologicalControlAgents.map((b: string, idx: number) => (
                                      <li key={idx}>{b}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Soil and Nutrient Management (for abiotic/physiological) */}
                              {Boolean(verifiedTreatment.biologicalManagement.soilAndNutrientManagement && verifiedTreatment.biologicalManagement.soilAndNutrientManagement.length > 0) && (
                                <div className="space-y-1 bg-emerald-100/60 p-2.5 rounded-xl border border-emerald-300">
                                  <span className="text-[11px] font-bold text-emerald-950 block">
                                    {language === 'ta' ? 'மண் & ஊட்டச்சத்து மேலாண்மை:' : 'Soil, Moisture & Nutrient Management:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-1 text-emerald-950 leading-relaxed pl-1">
                                    {verifiedTreatment.biologicalManagement.soilAndNutrientManagement!.map((s: string, idx: number) => (
                                      <li key={idx}>{s}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          ) : (
                            <ul className="list-disc list-inside space-y-1.5 text-xs text-emerald-900 leading-relaxed">
                              {analysisResult.diagnosis.biologicalManagement?.map((b, idx) => (
                                <li key={idx}>{b}</li>
                              ))}
                            </ul>
                          )}
                        </div>

                        {/* SECTION 5: Chemical Treatment */}
                        <div className="p-5 rounded-2xl bg-amber-50/70 border border-amber-200 shadow-xs space-y-3">
                          <div className="flex items-center justify-between gap-2 border-b border-amber-200/70 pb-2">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-950 flex items-center gap-1.5">
                              <FlaskConical className="w-4 h-4 text-amber-700" />
                              {language === 'ta' ? '5. அங்கீகரிக்கப்பட்ட ரசாயன மேலாண்மை' : '5. Chemical Treatment (When Verified)'}
                            </h4>
                            <span className="text-[10px] font-bold text-amber-900 bg-amber-100/90 px-2 py-0.5 rounded-full border border-amber-300">
                              CIBRC / TNAU Regulated
                            </span>
                          </div>

                          {/* CASE A: Abiotic / Physiological Disorder -> Strictly No Chemical */}
                          {isAbiotic || verifiedTreatment?.chemicalManagement?.isApplicable === false ? (
                            <div className="p-3.5 rounded-xl bg-amber-100/80 border-2 border-amber-300 text-xs text-amber-950 space-y-2">
                              <div className="flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4 text-amber-800 shrink-0" />
                                <span className="font-bold text-xs text-amber-900 uppercase tracking-wide">
                                  {language === 'ta'
                                    ? 'ரசாயன பூச்சிக்கொல்லிகள் இதற்கு பொருந்தாது!'
                                    : 'Chemical Pesticides Are Strictly NOT Applicable'}
                                </span>
                              </div>
                              <p className="text-[11px] text-amber-900 leading-relaxed">
                                {verifiedTreatment?.chemicalManagement?.inapplicableReason ||
                                  (language === 'ta'
                                    ? 'இது ஒரு உடலியல் அல்லது ஊட்டச்சத்து குறைபாடு. ரசாயன பூச்சிக்கொல்லிகளை தெளிப்பது பயிரை சேதப்படுத்தும் (பைட்டோடாக்சிசிட்டி) மற்றும் விவசாயிக்கு வீண் செலவை ஏற்படுத்தும்.'
                                    : 'This is a non-infectious physiological or nutrient disorder. Chemical pesticides provide zero benefit, waste farmer expenditure, and risk foliar phytotoxicity.')}
                              </p>
                              <div className="pt-2 border-t border-amber-200 text-[11px] text-amber-950 font-medium">
                                <strong>{language === 'ta' ? 'பாதுகாப்பான மாற்று:' : 'Safe Corrective Action: '}</strong>
                                {language === 'ta'
                                  ? 'மண் பரிசோதனை அட்டை (SHC) பரிந்துரைகளின்படி மட்டுமே உரங்களை இடவும் அல்லது தகுந்த இலைவழி நுண்ணூட்ட கரைசலை தெளிக்கவும்.'
                                  : 'Apply balanced soil amendments based on Soil Health Card recommendations or spray approved foliar micro-nutrient salts.'}
                              </div>
                            </div>
                          ) : hasVerifiedChemical ? (
                            /* CASE B: Verified Chemical Treatment */
                            <div className="space-y-3 text-xs text-amber-950">
                              {/* Active Ingredient & Dosage Box */}
                              <div className="p-3 rounded-xl bg-white border border-amber-200 shadow-2xs space-y-1.5">
                                <div className="flex items-center justify-between gap-1 flex-wrap">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                    Approved Active Ingredient
                                  </span>
                                  <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                                    CIBRC Approved
                                  </span>
                                </div>
                                <p className="text-xs font-bold text-slate-900 font-mono">
                                  {verifiedTreatment.chemicalManagement.activeIngredient}
                                </p>
                                {verifiedTreatment.chemicalManagement.dosageAndApplication && (
                                  <div className="pt-1 text-[11px] text-slate-700">
                                    <strong>Verified Dosage: </strong>
                                    <span className="font-mono text-amber-900 font-bold">
                                      {verifiedTreatment.chemicalManagement.dosageAndApplication}
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* Safety Intervals: PHI & REI */}
                              <div className="grid grid-cols-2 gap-2 text-center">
                                <div className="p-2 rounded-xl bg-amber-100/50 border border-amber-200">
                                  <span className="text-[9px] uppercase font-bold text-amber-800 block flex items-center justify-center gap-1">
                                    <Clock className="w-3 h-3 text-amber-700" />
                                    Pre-Harvest Interval (PHI)
                                  </span>
                                  <span className="text-xs font-bold text-amber-950 font-mono">
                                    {verifiedTreatment.chemicalManagement.preHarvestIntervalDays
                                      ? `${verifiedTreatment.chemicalManagement.preHarvestIntervalDays} Days`
                                      : 'Adhere to Label'}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-amber-100/50 border border-amber-200">
                                  <span className="text-[9px] uppercase font-bold text-amber-800 block flex items-center justify-center gap-1">
                                    <Shield className="w-3 h-3 text-amber-700" />
                                    Re-Entry Interval (REI)
                                  </span>
                                  <span className="text-xs font-bold text-amber-950 font-mono">
                                    {verifiedTreatment.chemicalManagement.reEntryIntervalHours
                                      ? `${verifiedTreatment.chemicalManagement.reEntryIntervalHours} Hours`
                                      : '24 Hours'}
                                  </span>
                                </div>
                              </div>

                              {/* Personal Protective Equipment (PPE) */}
                              {verifiedTreatment.chemicalManagement.personalProtectiveEquipment?.length > 0 && (
                                <div className="space-y-1">
                                  <span className="text-[11px] font-bold text-amber-900 block flex items-center gap-1">
                                    <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                                    {language === 'ta' ? 'கட்டாய பாதுகாப்பு உபகரணங்கள் (PPE):' : 'Mandatory Protective Equipment (PPE):'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-900/90 pl-1">
                                    {verifiedTreatment.chemicalManagement.personalProtectiveEquipment.map((ppe: string, idx: number) => (
                                      <li key={idx}>{ppe}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Safety & Environmental Precautions */}
                              {verifiedTreatment.chemicalManagement.safetyPrecautions?.length > 0 && (
                                <div className="space-y-1 pt-1 border-t border-amber-200/80">
                                  <span className="text-[11px] font-bold text-amber-900 block">
                                    {language === 'ta' ? 'சுற்றுச்சூழல் & தெளிப்பு முன்னெச்சரிக்கைகள்:' : 'Environmental & Spray Precautions:'}
                                  </span>
                                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-800 pl-1">
                                    {verifiedTreatment.chemicalManagement.safetyPrecautions.map((safe: string, idx: number) => (
                                      <li key={idx}>{safe}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          ) : (
                            /* CASE C: Fallback / Model notes */
                            <div className="space-y-2 text-xs text-amber-950">
                              <p className="text-[11px] text-amber-900 italic">
                                {language === 'ta'
                                  ? 'அங்கீகரிக்கப்பட்ட ரசாயன அட்டவணை கிடைக்கவில்லை. வேளாண்மை அலுவலரின் வழிகாட்டுதல் இன்றி ரசாயனங்களை தெளிக்க வேண்டாம்.'
                                  : 'Specific chemical prescription withheld. Avoid applying unverified commercial formulations without field confirmation by an extension officer.'}
                              </p>
                              {analysisResult.diagnosis.chemicalTreatment && analysisResult.diagnosis.chemicalTreatment.length > 0 && (
                                <ul className="list-disc list-inside space-y-1 text-xs text-amber-900">
                                  {analysisResult.diagnosis.chemicalTreatment.map((chem, idx) => (
                                    <li key={idx}>{chem}</li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          )}

                          {/* Authoritative Reference Link Footer */}
                          {verifiedTreatment?.references && verifiedTreatment.references.length > 0 && (
                            <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between text-[10px] text-amber-800">
                              <span className="font-bold">Source: {verifiedTreatment.references[0].organization}</span>
                              {verifiedTreatment.references[0].url && (
                                <a
                                  href={verifiedTreatment.references[0].url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-emerald-800 hover:text-emerald-950 font-bold underline"
                                >
                                  <span>View Official Guide</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}

                  {/* ========================================================= */}
                  {/* SECTION 6: PREVENTION                                     */}
                  {/* ========================================================= */}
                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      {language === 'ta' ? '6. எதிர்கால தடுப்பு நடவடிக்கைகள்' : '6. Prevention & Proactive Crop Care'}
                    </h4>
                    {analysisResult.diagnosis.preventionTips && analysisResult.diagnosis.preventionTips.length > 0 ? (
                      <ul className="list-disc list-inside space-y-1 text-xs text-slate-600 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                        {analysisResult.diagnosis.preventionTips.map((tip, idx) => (
                          <li key={idx}>{tip}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-600">
                        Use certified seeds, balanced NPK based on soil health cards, and maintain aeration alleyways.
                      </p>
                    )}
                  </div>

                  {/* ========================================================= */}
                  {/* SECTION 7: WHEN TO CONSULT AN AGRICULTURAL EXPERT         */}
                  {/* ========================================================= */}
                  <div className="p-5 rounded-2xl bg-linear-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-300 shadow-xs space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-950 flex items-center gap-1.5">
                          <PhoneCall className="w-4 h-4 text-emerald-700" />
                          {language === 'ta' ? '7. எப்போது வேளாண் வல்லுநரை அணுக வேண்டும்?' : '7. When to Consult an Agricultural Expert'}
                        </h4>
                        <p className="text-[11px] text-emerald-800 mt-0.5">
                          Field conditions require physical verification before large-scale spray investment.
                        </p>
                      </div>

                      <a
                        href="tel:18004251661"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-md transition-all active:scale-95 shrink-0"
                      >
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>Call Toll-Free: 1800-425-1661</span>
                      </a>
                    </div>

                    {analysisResult.diagnosis.whenToConsultExpert && analysisResult.diagnosis.whenToConsultExpert.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 text-xs text-emerald-900 bg-white/70 p-3 rounded-xl border border-emerald-200">
                        {analysisResult.diagnosis.whenToConsultExpert.map((trig, idx) => (
                          <li key={idx}>{trig}</li>
                        ))}
                      </ul>
                    )}

                    {analysisResult.diagnosis.verifiedGuidanceReferences && (
                      <div className="text-[10px] text-emerald-800 flex flex-wrap items-center gap-2 pt-1 border-t border-emerald-200/60">
                        <span className="font-bold">Verified References:</span>
                        {analysisResult.diagnosis.verifiedGuidanceReferences.map((ref, idx) => (
                          <span key={idx} className="bg-emerald-100 text-emerald-900 px-2 py-0.5 rounded-md font-mono">
                            {ref}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : (analysisResult.status === 'inconclusive' || analysisResult.status === 'quality_failure') ? (
                /* INCONCLUSIVE / QUALITY FAILURE STATE */
                <div className="p-6 rounded-3xl bg-amber-50/90 border-2 border-amber-300 text-amber-950 space-y-4 shadow-sm animate-fade-in">
                  <div className="flex items-start gap-3">
                    <RotateCcw className="w-6 h-6 text-amber-700 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-extrabold text-slate-900">
                          {language === 'ta'
                            ? (analysisResult.status === 'quality_failure'
                                ? 'புகைப்பட தர எச்சரிக்கை: மீண்டும் படம் எடுக்கவும்'
                                : 'கூடுதல் ஆதாரம் தேவைப்படுகிறது: படம் தெளிவற்றது')
                            : (analysisResult.status === 'quality_failure'
                                ? 'Photo Quality Failure: Retake Recommended'
                                : 'Additional Evidence Required: Diagnosis Inconclusive')}
                        </h4>
                        <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-amber-200 text-amber-900">
                          Honest Notice
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {language === 'ta' ? analysisResult.messageTa : analysisResult.messageEn}
                      </p>
                      <p className="text-[11px] text-slate-500 italic">
                        {analysisResult.truthfulnessNotice}
                      </p>
                    </div>
                  </div>

                  {/* Photography Tips Card */}
                  <div className="bg-white/80 p-4 rounded-2xl border border-amber-200 space-y-2 text-xs">
                    <span className="font-bold text-slate-800 flex items-center gap-1.5">
                      <Camera className="w-4 h-4 text-emerald-600" />
                      {language === 'ta'
                        ? 'துல்லியமான AI ஆய்வுக்கு சிறந்த படம் எடுப்பது எப்படி:'
                        : 'Tips for Taking a Diagnosable Crop Photo:'}
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-600 text-[11px] leading-relaxed">
                      <li>
                        <strong>Natural Daylight:</strong> Avoid shadows or direct camera flash reflection.
                      </li>
                      <li>
                        <strong>Focus on Lesions:</strong> Capture the boundary between green healthy tissue and diseased tissue.
                      </li>
                      <li>
                        <strong>Camera Distance:</strong> Keep camera 15-25 cm from the leaf so leaf veins and spots are sharp.
                      </li>
                      <li>
                        <strong>Single Problem:</strong> If the crop has multiple stresses, capture individual affected parts separately.
                      </li>
                    </ul>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pt-1">
                    <button
                      type="button"
                      onClick={startCamera}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-2 shadow-sm transition-all active:scale-95"
                    >
                      <Camera className="w-4 h-4" />
                      <span>{language === 'ta' ? 'புதிய படம் எடுக்கவும்' : 'Retake with Live Camera'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleReplaceImage}
                      className="px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-bold transition-all active:scale-95"
                    >
                      {language === 'ta' ? 'வேறு படத்தை தேர்ந்தெடுக்கவும்' : 'Upload Different File'}
                    </button>
                  </div>
                </div>
              ) : (
                /* UNAVAILABLE / NOT CONFIGURED STATE */
                <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-300 text-amber-950 space-y-3">
                  <div className="flex items-start gap-3">
                    <ShieldAlert className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-extrabold text-slate-900">
                          {language === 'ta'
                            ? 'சேவையக ஆய்வு நிலை: நேரடி AI சேவை தற்போது கிடைக்கவில்லை'
                            : 'Backend Status: Live Machine Vision Service Currently Unavailable'}
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

                  {analysisResult.safeNextSteps && (
                    <div className="mt-3 pt-3 border-t border-amber-200 text-xs">
                      <h5 className="font-bold text-slate-900 mb-1.5 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        {language === 'ta' ? 'விவசாயிகளுக்கான பரிந்துரைக்கப்பட்ட படிகள்:' : 'Recommended Safe Next Steps for Farmer:'}
                      </h5>
                      <ul className="list-disc list-inside space-y-1 text-slate-700 leading-relaxed text-[11px]">
                        {analysisResult.safeNextSteps.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ================================================================= */}
          {/* TNAU VISUAL SYMPTOM REFERENCE GUIDE ACCORDION                     */}
          {/* ================================================================= */}
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
                        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="font-bold text-slate-700 block mb-1">
                            🔍 Key Visual Symptoms:
                          </span>
                          <p className="text-slate-600 leading-relaxed">
                            {language === 'ta' ? item.symptoms_ta : item.symptoms_en}
                          </p>
                        </div>

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
        </div>
      )}

      {/* HISTORY TAB CONTENT */}
      {activeTab === 'history' && (
        <div className="space-y-6 animate-fade-in">
          {/* Authentication Guard */}
          {!isAuthenticated ? (
            <div className="p-8 rounded-3xl bg-slate-50 border border-slate-200 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center">
                <Lock className="w-6 h-6" />
              </div>
              <div className="space-y-1.5 max-w-md mx-auto">
                <h3 className="font-bold text-slate-800 text-base">
                  {language === 'ta' ? 'உழவர் உள்நுழைவு தேவை' : 'Farmer Authentication Required'}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {language === 'ta'
                    ? 'பாதுகாப்பான பயிர் ஆய்வு அறிக்கைகள் உங்கள் உழவர் அடையாள எண்ணுடன் மட்டுமே பாதுகாக்கப்படுகின்றன. உங்கள் முந்தைய பரிசோதனைகளைக் காண தயவுசெய்து உள்நுழையவும்.'
                    : 'Personal diagnosis reports and TNAU management histories are strictly protected under your farmer account. Log in with your registered Farmer ID or phone number to access your records.'}
                </p>
              </div>
              <div className="inline-flex items-center gap-2 text-xs font-bold text-emerald-700 bg-emerald-50 px-3.5 py-1.5 rounded-full border border-emerald-200">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>
                  {language === 'ta' ? 'பூஜ்ஜிய கசிவு • உழவர் தனியுரிமை பாதுகாப்பு' : 'Strict Farmer Ownership & Data Privacy'}
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {/* Header & Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-white border border-emerald-200">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-emerald-950 text-sm sm:text-base">
                      {language === 'ta' ? 'பாதுகாக்கப்பட்ட கள ஆய்வு வரலாறு' : 'Secure Diagnostic Medical History'}
                    </h3>
                    <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900">
                      {historyReports.length} {language === 'ta' ? 'அறிக்கைகள்' : 'Reports'}
                    </span>
                  </div>
                  <p className="text-xs text-emerald-800">
                    {language === 'ta'
                      ? `உழவர்: ${user?.name || 'மதிப்பிற்குரிய உழவர்'} | எண்: ${user?.farmerId || user?.phone || 'உள்நுழைவு செயலில் உள்ளது'}`
                      : `Farmer: ${user?.name || 'Registered Farmer'} | ID: ${user?.farmerId || user?.phone || 'Active Session'}`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={fetchHistory}
                  disabled={loadingHistory}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-100 text-xs font-bold transition-all shadow-2xs self-start sm:self-auto cursor-pointer disabled:opacity-60"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
                  <span>{language === 'ta' ? 'புதுப்பி' : 'Refresh'}</span>
                </button>
              </div>

              {/* Data Protection Notice */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 flex items-start gap-2.5">
                <Shield className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <p>
                  {language === 'ta'
                    ? '🛡️ தனியுரிமை கொள்கை: விவசாயிகளின் தரவு சேமிப்பு கொள்கையின்படி, மாதிரி புகைப்படங்கள் நிகழ்நேர ஆய்வுக்குப் பின் அழிக்கப்படுகின்றன; ஆய்வு முடிவுகள், TNAU பரிந்துரைகள் மற்றும் சிகிச்சை குறிப்புகள் மட்டுமே உங்கள் கணக்கில் பாதுகாப்பாக சேமிக்கப்படுகின்றன.'
                    : '🛡️ Privacy & Controlled Retention: To protect farmer data and minimize digital footprint, raw uploaded images are evaluated in real-time and discarded. Diagnostic clinical summaries, confidence indicators, and authoritative TNAU treatment plans are permanently archived.'}
                </p>
              </div>

              {/* Error State */}
              {historyError && (
                <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 text-xs flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>{historyError}</span>
                  </div>
                  <button
                    type="button"
                    onClick={fetchHistory}
                    className="underline font-bold text-rose-700 hover:text-rose-900 cursor-pointer"
                  >
                    {language === 'ta' ? 'மீண்டும் முயற்சிக்கவும்' : 'Retry'}
                  </button>
                </div>
              )}

              {/* Loading State */}
              {loadingHistory && (
                <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-500">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                  <p className="text-xs">
                    {language === 'ta' ? 'ஆய்வு அறிக்கைகளை மீட்டெடுக்கிறது...' : 'Retrieving encrypted diagnosis records...'}
                  </p>
                </div>
              )}

              {/* Empty State */}
              {!loadingHistory && historyReports.length === 0 && !historyError && (
                <div className="p-10 rounded-3xl bg-slate-50 border border-dashed border-slate-300 text-center space-y-3">
                  <div className="w-12 h-12 mx-auto rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Leaf className="w-6 h-6" />
                  </div>
                  <h4 className="font-bold text-slate-800 text-sm">
                    {language === 'ta' ? 'சேமிக்கப்பட்ட ஆய்வு எதுவும் இல்லை' : 'No Diagnosis Records Yet'}
                  </h4>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    {language === 'ta'
                      ? 'நீங்கள் கேமரா அல்லது பட பதிவேற்றம் மூலம் பயிர்களை ஆய்வு செய்யும்போது, அந்த அறிக்கைகள் தானாகவே உங்கள் கணக்கில் பாதுகாக்கப்படும்.'
                      : 'When you diagnose a plant specimen via upload or live camera, full pathology reports and TNAU treatments will automatically be preserved here.'}
                  </p>
                  <button
                    type="button"
                    onClick={() => setActiveTab('scanner')}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm cursor-pointer"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>{language === 'ta' ? 'புதிய பயிர் பரிசோதனை செய்ய' : 'Perform a Diagnosis Now'}</span>
                  </button>
                </div>
              )}

              {/* Reports List */}
              {!loadingHistory && historyReports.length > 0 && (
                <div className="space-y-4">
                  {historyReports.map((report) => {
                    const formattedDate = new Date(report.createdAt).toLocaleDateString(
                      language === 'ta' ? 'ta-IN' : 'en-US',
                      {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      }
                    );
                    const isDeleting = deletingId === report.id;

                    return (
                      <div
                        key={report.id}
                        className="p-5 rounded-2xl border border-slate-200 bg-white hover:border-emerald-300 hover:shadow-md transition-all space-y-3.5 group"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-slate-100">
                          <div className="flex flex-wrap items-center gap-2">
                            {renderCategoryBadge(report.category as DiagnosisCategory)}
                            {renderSeverityBadge(report.severityOrUrgency || 'moderate')}
                            <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                              <Leaf className="w-3 h-3 text-emerald-600" />
                              {report.crop || 'Field Crop'}
                            </span>
                            {report.plantPart && (
                              <span className="text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200">
                                {report.plantPart}
                              </span>
                            )}
                            {report.district && (
                              <span className="text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200">
                                📍 {report.district}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 text-[11px] text-slate-500">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            <span>{formattedDate}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                          <div className="md:col-span-2 space-y-1">
                            <h4 className="font-extrabold text-slate-900 text-sm sm:text-base flex items-center gap-2">
                              <span>{report.suspectedCondition}</span>
                            </h4>
                            {(report.suspectedConditionTa || report.visualSymptomsTa) && (
                              <p className="text-xs text-slate-600 font-medium line-clamp-2">
                                {report.suspectedConditionTa || report.visualSymptomsTa}
                              </p>
                            )}
                            <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-500">
                              <span>
                                {language === 'ta' ? 'நம்பகத்தன்மை:' : 'Confidence:'}{' '}
                                <strong className="text-emerald-700">
                                  {report.confidencePercent || 0}%
                                </strong>
                              </span>
                              <span>•</span>
                              <span>
                                {language === 'ta' ? 'நிலை:' : 'Status:'}{' '}
                                <span className="font-semibold capitalize text-slate-700">
                                  {report.status || 'Completed'}
                                </span>
                              </span>
                              <span>•</span>
                              <span className="text-[10px] text-slate-400">
                                {report.imageMetadata?.filename || 'Image Analyzed'} (Raw discarded)
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-end gap-2 pt-2 md:pt-0">
                            <button
                              type="button"
                              onClick={() => handleViewHistoricalReport(report)}
                              className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>{language === 'ta' ? 'அறிக்கையைக் காண்க' : 'View Full Report'}</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDeleteReport(report.id)}
                              disabled={isDeleting}
                              className="p-2 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 border border-slate-200 hover:border-rose-300 transition-all cursor-pointer disabled:opacity-50"
                              title={language === 'ta' ? 'அறிக்கையை நீக்கு' : 'Delete Report'}
                              aria-label="Delete Report"
                            >
                              {isDeleting ? (
                                <Loader2 className="w-4 h-4 animate-spin text-rose-600" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ================================================================= */}
      {/* GOVERNMENT HELPLINE FOOTER                                        */}
          {/* ================================================================= */}
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

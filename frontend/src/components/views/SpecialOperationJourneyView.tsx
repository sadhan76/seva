import React, { useState, useEffect } from 'react';
import {
  Compass,
  CheckCircle2,
  Calendar,
  Layers,
  Sprout,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Clock,
  HelpCircle,
  ExternalLink,
  RefreshCw,
  Save,
  RotateCcw,
  ArrowRight,
  ArrowLeft,
  Info,
  Droplet,
  CloudSun,
  Bug,
  ShieldCheck,
  Award,
  Printer,
  Camera,
  Plus,
  Check,
  Users,
  ShoppingBag
} from 'lucide-react';
import type {
  NavTab,
  SpecialOperationJourney,
  SpecialOperationProfileInput,
  SpecialOperationCropRecommendation,
  SpecialOperationCropGuide,
  SpecialOperationTimeline,
  JourneyObservation,
  JourneyCostsWorksheet,
  JourneySalePlan,
  JourneyCompletionRecord,
  SpecialOperationLandUnit,
  SpecialOperationWater,
  SpecialOperationSoil,
  SpecialOperationSeason,
  SpecialOperationBudget,
  SpecialOperationGoal,
} from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getSpecialOperationJourney,
  updateSpecialOperationStep,
  getSpecialOperationCrops,
  getSpecialOperationCropGuide,
  getSpecialOperationTimeline,
  addSpecialOperationObservation,
  triggerSpecialOperationReminder,
  resetSpecialOperationJourney,
  getMarketPricesApi,
  getDistrictsApi,
} from '../../services/api';

interface SpecialOperationJourneyViewProps {
  onNavigate?: (tab: NavTab) => void;
}

const STEP_TITLES = [
  { step: 1, en: 'Understand the Farmer', ta: 'விவசாயி சுயவிவரம்', icon: Users },
  { step: 2, en: 'Select a Crop', ta: 'பொருத்தமான பயிர் தேர்வு', icon: Sprout },
  { step: 3, en: 'Prepare the Farm', ta: 'பண்ணை தயாரிப்பு', icon: Layers },
  { step: 4, en: 'Planting Guidance', ta: 'விதைப்பு மற்றும் நடவு', icon: Compass },
  { step: 5, en: 'Daily & Weekly Care', ta: 'பயிர் பராமரிப்பு', icon: Droplet },
  { step: 6, en: 'Growth Tracker', ta: 'வளர்ச்சி கண்காணிப்பு', icon: Clock },
  { step: 7, en: 'Harvest Readiness', ta: 'அறுவடை தயாரிப்பு', icon: CheckCircle2 },
  { step: 8, en: 'Estimate Costs', ta: 'செலவு கணக்கீடு', icon: DollarSign },
  { step: 9, en: 'Plan the Sale', ta: 'விற்பனை திட்டமிடல்', icon: TrendingUp },
  { step: 10, en: 'Complete Journey', ta: 'பயணம் நிறைவு & சான்றிதழ்', icon: Award },
];

export const SpecialOperationJourneyView: React.FC<SpecialOperationJourneyViewProps> = ({ onNavigate }) => {
  const { language } = useLanguage();
  const { token, user } = useAuth();
  const isTa = language === 'ta';

  // Core State
  const [journey, setJourney] = useState<SpecialOperationJourney | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveToast, setSaveToast] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState<boolean>(false);
  const [showResetModal, setShowResetModal] = useState<boolean>(false);

  // Step 1: Profile State
  const [profile, setProfile] = useState<SpecialOperationProfileInput>({
    district: user?.district || '',
    landArea: 1.0,
    landUnit: 'acres',
    waterAvailability: 'ample_borewell',
    soilType: 'unknown',
    season: 'unknown',
    budgetRange: 'low_15k_35k',
    availableLabour: 'family_only_1_2',
    farmingGoal: 'commercial_income',
  });

  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function fetchDistricts() {
      const stateToQuery = user?.state || 'Tamil Nadu';
      const dList = await getDistrictsApi(stateToQuery);
      if (isMounted) {
        const names = dList.map((d) => d.name);
        if (user?.district && !names.includes(user.district)) {
          names.unshift(user.district);
        }
        setAvailableDistricts(names);
        if (!profile.district && names.length > 0) {
          setProfile((p) => ({ ...p, district: user?.district || names[0] }));
        }
      }
    }
    fetchDistricts();
    return () => {
      isMounted = false;
    };
  }, [user?.state, user?.district]);

  // Step 2: Recommendations State
  const [candidateCrops, setCandidateCrops] = useState<SpecialOperationCropRecommendation[]>([]);
  const [cropsDisclaimer, setCropsDisclaimer] = useState<string>('');
  const [isLoadingCrops, setIsLoadingCrops] = useState<boolean>(false);
  const [selectedCropId, setSelectedCropId] = useState<string>('tomato');

  // Step 3 & 4: Crop Guide State
  const [cropGuide, setCropGuide] = useState<SpecialOperationCropGuide | null>(null);
  const [checklists, setChecklists] = useState<Record<string, boolean>>({});

  // Step 4: Planting Date
  const [plantingDate, setPlantingDate] = useState<string>('');

  // Step 6: Observations & Dynamic Timeline
  const [timeline, setTimeline] = useState<SpecialOperationTimeline | null>(null);
  const [newObsNote, setNewObsNote] = useState<string>('');
  const [newObsStage, setNewObsStage] = useState<number>(1);
  const [newObsIsDeviation, setNewObsIsDeviation] = useState<boolean>(false);
  const [newObsReason, setNewObsReason] = useState<string>('');
  const [newObsPhoto, setNewObsPhoto] = useState<string>('');
  const [isLoggingObs, setIsLoggingObs] = useState<boolean>(false);

  // Step 8: Cost Worksheet
  const [costsWorksheet, setCostsWorksheet] = useState<JourneyCostsWorksheet>({
    entries: [],
    totalOperatingCost: 0,
    costPerUnitArea: 0,
    disclaimer: 'Estimates are illustrative guidelines based on TNAU benchmarks.',
  });

  // Step 9: Market Plan & Mandi Snapshot
  const [salePlan, setSalePlan] = useState<JourneySalePlan>({
    targetChannels: ['Uzhavar Sandhai', 'Direct Farm Gate'],
    gradingPackagingDetails: ['Grade A clean crates', 'Grade B bulk local'],
    transportConsiderations: 'Coordinate shared mini-truck with neighbouring farmers',
    disclaimer: 'Quoted mandi prices are modal auction rates, not guaranteed contracts.',
  });
  const [mandiPriceData, setMandiPriceData] = useState<any>(null);

  // Step 10: Harvest Completion Record
  const [completionRecord, setCompletionRecord] = useState<JourneyCompletionRecord>({
    harvestDate: new Date().toISOString().split('T')[0],
    harvestedQuantity: 3500,
    harvestUnit: 'kg',
    gradeBreakdown: { GradeA: 80, GradeB: 20 },
    buyerNameOrChannel: 'Salem Uzhavar Sandhai',
    achievedPricePerUnit: 25.0,
    grossRevenue: 87500,
    totalOperatingCost: 28500,
    netProfitOrLoss: 59000,
    farmerReflection: 'Direct selling at Uzhavar Sandhai yielded 30% higher return than local brokers.',
    completedAt: '',
  });

  // Load journey data
  const fetchJourney = async () => {
    setIsLoading(true);
    try {
      if (token) {
        const data = await getSpecialOperationJourney(token);
        setJourney(data);
        setCurrentStep(data.currentStep || 1);
        if (data.profileInput) setProfile(data.profileInput);
        if (data.selectedCropId) setSelectedCropId(data.selectedCropId);
        if (data.checklists) setChecklists(data.checklists);
        if (data.plantingDate) setPlantingDate(data.plantingDate);
        if (data.costsWorksheet && data.costsWorksheet.entries?.length > 0) {
          setCostsWorksheet(data.costsWorksheet);
        }
        if (data.salePlan) setSalePlan(data.salePlan);
        if (data.completionRecord) setCompletionRecord(data.completionRecord);
        if (data.timeline) setTimeline(data.timeline);
      } else {
        // Fallback for unauthenticated exploration
        const defaultCrop = 'tomato';
        setSelectedCropId(defaultCrop);
      }
    } catch (err) {
      console.error('Failed to load Special Operation journey:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJourney();
  }, [token]);

  // Load candidate crops when profile changes or on Step 2
  useEffect(() => {
    const fetchCrops = async () => {
      setIsLoadingCrops(true);
      try {
        const res = await getSpecialOperationCrops({
          district: profile.district,
          water_availability: profile.waterAvailability,
          soil_type: profile.soilType,
          season: profile.season,
          budget_range: profile.budgetRange,
          available_labour: profile.availableLabour,
          farming_goal: profile.farmingGoal,
        });
        setCandidateCrops(res.crops || []);
        setCropsDisclaimer(res.disclaimer || '');
      } catch (e) {
        console.error('Failed to fetch candidate crops:', e);
      } finally {
        setIsLoadingCrops(false);
      }
    };

    if (currentStep >= 1) {
      fetchCrops();
    }
  }, [profile, currentStep]);

  // Load crop guide whenever selectedCropId changes
  useEffect(() => {
    const fetchGuide = async () => {
      if (!selectedCropId) return;
      try {
        const guide = await getSpecialOperationCropGuide(selectedCropId);
        setCropGuide(guide);
      } catch (e) {
        console.error('Failed to fetch crop guide:', e);
      }
    };
    fetchGuide();
  }, [selectedCropId]);

  // Load timeline whenever planting date or crop changes
  useEffect(() => {
    const fetchTimeline = async () => {
      if (!selectedCropId) return;
      try {
        const tl = await getSpecialOperationTimeline(selectedCropId, plantingDate || undefined);
        setTimeline(tl);
      } catch (e) {
        console.error('Failed to fetch timeline:', e);
      }
    };
    fetchTimeline();
  }, [selectedCropId, plantingDate]);

  // Load Mandi Price snapshot for Step 9
  useEffect(() => {
    const fetchMandi = async () => {
      try {
        const res = await getMarketPricesApi({
          district: profile.district !== 'All' ? profile.district : undefined,
        });
        const items = (res as any)?.items || (Array.isArray(res) ? res : []);
        if (items && items.length > 0) {
          const matched = items.find((m: any) =>
            m.commodity?.toLowerCase().includes(selectedCropId.toLowerCase()) ||
            m.commodityName?.toLowerCase().includes(selectedCropId.toLowerCase())
          );
          setMandiPriceData(matched || items[0]);
        }
      } catch (e) {
        console.error('Failed to load mandi prices for sale plan:', e);
      }
    };
    if (currentStep >= 8) {
      fetchMandi();
    }
  }, [currentStep, selectedCropId, profile.district]);

  // Helper to show temporary toast
  const triggerToast = (msg: string) => {
    setSaveToast(msg);
    setTimeout(() => setSaveToast(null), 3500);
  };

  // Persist Step Update to Backend
  const saveProgress = async (stepToSave: number, extraData?: any) => {
    if (!token) {
      setCurrentStep(stepToSave);
      triggerToast(isTa ? 'முன்னேற்றம் சேமிக்கப்பட்டது (Demo)' : 'Progress saved (Demo Mode)');
      return;
    }

    setIsSaving(true);
    try {
      const payload: any = {
        currentStep: stepToSave,
        profileInput: profile,
        selectedCropId: selectedCropId,
        plantingDate: plantingDate || undefined,
        checklists: checklists,
        costsWorksheet: costsWorksheet,
        salePlan: salePlan,
        completionRecord: extraData?.completionRecord || completionRecord,
        ...(extraData || {}),
      };

      const updated = await updateSpecialOperationStep(payload, token);
      setJourney(updated);
      if (updated.timeline) setTimeline(updated.timeline);
      setCurrentStep(stepToSave);
      triggerToast(isTa ? 'முன்னேற்றம் வெற்றிகரமாக சேமிக்கப்பட்டது!' : 'Progress saved successfully!');
    } catch (err: any) {
      console.error('Save step failed:', err);
      triggerToast(isTa ? 'சேமிப்பதில் பிழை ஏற்பட்டது.' : 'Failed to save progress.');
    } finally {
      setIsSaving(false);
    }
  };

  // Safe Reset Journey
  const handleResetJourney = async () => {
    if (!token) {
      setCurrentStep(1);
      setSelectedCropId('tomato');
      setChecklists({});
      setPlantingDate('');
      setShowResetModal(false);
      triggerToast(isTa ? 'பயணம் ஆரம்ப நிலைக்கு மாற்றப்பட்டது.' : 'Journey reset to Step 1.');
      return;
    }

    try {
      setIsLoading(true);
      const res = await resetSpecialOperationJourney(token);
      setJourney(res.journey);
      setCurrentStep(1);
      setSelectedCropId('tomato');
      setChecklists({});
      setPlantingDate('');
      setShowResetModal(false);
      triggerToast(isTa ? 'பயணம் வெற்றிகரமாக மீட்டமைக்கப்பட்டது.' : 'Journey reset successfully.');
    } catch (e) {
      console.error('Reset failed:', e);
      triggerToast(isTa ? 'மீட்டமைப்பதில் பிழை ஏற்பட்டது.' : 'Reset failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // Checklist Toggle
  const toggleChecklist = (id: string) => {
    const next = { ...checklists, [id]: !checklists[id] };
    setChecklists(next);
    // Background autosave checklist state
    if (token) {
      updateSpecialOperationStep({ currentStep, checklists: next }, token).catch(console.error);
    }
  };

  // Cost Worksheet Cell Change
  const handleCostEntryChange = (index: number, field: 'userQuantity' | 'userUnitPrice', val: number) => {
    const updatedEntries = [...costsWorksheet.entries];
    const current = updatedEntries[index];
    if (!current) return;

    updatedEntries[index] = {
      ...current,
      [field]: val,
      isUserEdited: true,
    };

    const newTotal = updatedEntries.reduce(
      (sum, entry) => sum + (entry.userQuantity * entry.userUnitPrice),
      0
    );

    const updatedWorksheet: JourneyCostsWorksheet = {
      ...costsWorksheet,
      entries: updatedEntries,
      totalOperatingCost: Math.round(newTotal * 100) / 100,
    };

    setCostsWorksheet(updatedWorksheet);
  };

  // Step 6: Add Observation Log
  const handleAddObservation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newObsNote.trim()) return;

    setIsLoggingObs(true);
    try {
      if (token) {
        const res = await addSpecialOperationObservation(
          {
            note: newObsNote.trim(),
            stageNumber: newObsStage,
            photoUrl: newObsPhoto.trim() || undefined,
            isDeviation: newObsIsDeviation,
            deviationReason: newObsIsDeviation ? newObsReason.trim() : undefined,
          },
          token
        );
        if (journey) {
          setJourney({
            ...journey,
            observations: [res.observation, ...(journey.observations || [])],
          });
        }
      } else {
        const mockObs: JourneyObservation = {
          id: `obs_${Date.now()}`,
          date: new Date().toISOString().split('T')[0],
          stageNumber: newObsStage,
          note: newObsNote.trim(),
          photoUrl: newObsPhoto.trim() || undefined,
          isDeviation: newObsIsDeviation,
          deviationReason: newObsIsDeviation ? newObsReason.trim() : undefined,
          createdAt: new Date().toISOString(),
        };
        if (journey) {
          setJourney({
            ...journey,
            observations: [mockObs, ...(journey.observations || [])],
          });
        }
      }

      setNewObsNote('');
      setNewObsReason('');
      setNewObsIsDeviation(false);
      setNewObsPhoto('');
      triggerToast(isTa ? 'கண்காணிப்பு பதிவு செய்யப்பட்டது!' : 'Observation recorded!');
    } catch (err) {
      console.error('Failed to log observation:', err);
      triggerToast(isTa ? 'பதிவு செய்வதில் பிழை.' : 'Failed to record observation.');
    } finally {
      setIsLoggingObs(false);
    }
  };

  // Send Test In-App Notification Reminder
  const handleSendReminder = async () => {
    if (!token) {
      triggerToast(isTa ? 'உள்நுழைந்த பயனர்களுக்கு மட்டும் அறிவிப்பு அனுப்பப்படும்.' : 'Login required to dispatch push/in-app notification.');
      return;
    }
    try {
      await triggerSpecialOperationReminder(
        {
          title: isTa ? 'பயிர் பராமரிப்பு நினைவூட்டல்' : 'Special Operation Care Reminder',
          message: isTa
            ? `${selectedCropId.toUpperCase()} பயிருக்கு 2-ம் கட்ட மேலுரமிடுதல் மற்றும் பாசன சரிபார்ப்பு செய்ய வேண்டிய நேரம்.`
            : `Time to verify stage top-dressing and irrigation for your ${selectedCropId.toUpperCase()} crop.`,
        },
        token
      );
      triggerToast(isTa ? 'அறிவிப்பு அனுப்பப்பட்டது! (அறிவிப்புகள் பக்கத்தை பார்க்கவும்)' : 'Reminder sent to notification center!');
    } catch (e) {
      console.error(e);
      triggerToast(isTa ? 'அறிவிப்பு அனுப்புவதில் பிழை.' : 'Failed to dispatch reminder.');
    }
  };

  // Completion calculation updates
  const handleCompletionChange = (field: keyof JourneyCompletionRecord, val: any) => {
    const updated = { ...completionRecord, [field]: val };
    const qty = field === 'harvestedQuantity' ? Number(val) : updated.harvestedQuantity;
    const price = field === 'achievedPricePerUnit' ? Number(val) : updated.achievedPricePerUnit;
    const gross = Math.round(qty * price);
    const cost = costsWorksheet.totalOperatingCost || updated.totalOperatingCost;
    const net = Math.round(gross - cost);

    setCompletionRecord({
      ...updated,
      grossRevenue: gross,
      totalOperatingCost: cost,
      netProfitOrLoss: net,
    });
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-500 space-y-3 bg-white rounded-2xl border border-slate-200 shadow-xs">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600" />
        <p className="text-sm font-semibold text-slate-700">
          {isTa ? 'உங்கள் சிறப்பு வழிகாட்டல் பயணம் ஏற்றப்படுகிறது...' : 'Loading Special Operation Journey...'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Toast Notification */}
      {saveToast && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl flex items-center gap-3 border border-slate-700 animate-in fade-in slide-in-from-bottom-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span className="text-sm font-medium">{saveToast}</span>
        </div>
      )}

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <RotateCcw className="w-6 h-6" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-bold text-slate-900">
                {isTa ? 'பயணத்தை மீண்டும் தொடங்குவதா?' : 'Restart Beginner Journey?'}
              </h3>
              <p className="text-xs text-slate-600 mt-2">
                {isTa
                  ? 'உங்கள் தற்போதைய பயிர் வழிகாட்டல் மற்றும் படிகள் ஆரம்ப நிலைக்கு மாற்றப்படும். உங்கள் சுயவிவரம், உழவர் சந்தை பட்டியல்கள் மற்றும் முன்பதிவுகள் பாதுகாப்பாக இருக்கும்.'
                  : 'This will reset your Special Operation progress back to Step 1 so you can choose a new crop. Your mandi bookings, profile, and marketplace records will NOT be deleted.'}
              </p>
            </div>
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowResetModal(false)}
                className="flex-1 px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl"
              >
                {isTa ? 'ரத்து செய்க' : 'Cancel'}
              </button>
              <button
                type="button"
                onClick={handleResetJourney}
                className="flex-1 px-4 py-2 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl"
              >
                {isTa ? 'ஆம், மீட்டமை' : 'Yes, Restart'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HERO BANNER & STATUS */}
      <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-amber-950 flex items-center gap-1.5 shadow-xs">
                <Compass className="w-3.5 h-3.5" />
                {isTa ? 'சிறப்பு வழிகாட்டல் திட்டம்' : 'Special Operation'}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-700/80 text-emerald-100 border border-emerald-600">
                {isTa ? 'முழுமையான தொடக்க விவசாய வழிகாட்டி' : 'Beginner Farmer Blueprint'}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-800/80 text-teal-200">
                TNAU & ICAR Verified
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {isTa
                ? 'முதல் படி முதல் முதல் விற்பனை வரை'
                : 'From First Step to First Sale'}
            </h1>
            <p className="text-sm text-emerald-100 max-w-2xl leading-relaxed">
              {isTa
                ? 'விவசாய அனுபவம் இல்லாத புதியவர்களுக்கான 10-படி நேரடி செயல்முறை வழிகாட்டி. நில ஆய்வு, பயிர் தேர்வு, விதைப்பு, பராமரிப்பு முதல் உழவர் சந்தை விற்பனை வரை.'
                : 'A guided 10-step interactive journey designed for complete beginners who do not know how to farm. Real verified agronomy, transparent costs, and market connections.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap md:flex-col items-end gap-2 self-start md:self-auto shrink-0">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowHelp(!showHelp)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-700/60 hover:bg-emerald-600 text-white flex items-center gap-1.5 border border-emerald-500/40"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                {isTa ? (showHelp ? 'உதவி மறை' : 'ஏன் இது முக்கியம்?') : (showHelp ? 'Hide Explanations' : 'Why This Matters')}
              </button>

              <button
                type="button"
                onClick={() => saveProgress(currentStep)}
                disabled={isSaving}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-emerald-950 flex items-center gap-1.5 shadow-xs transition-all font-bold"
              >
                {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                {isTa ? 'சேமி & தொடர்க' : 'Save & Resume'}
              </button>
            </div>

            <button
              type="button"
              onClick={() => setShowResetModal(true)}
              className="text-xs text-emerald-300 hover:text-white flex items-center gap-1 underline underline-offset-2 transition-colors pt-1"
            >
              <RotateCcw className="w-3 h-3" />
              {isTa ? 'புதிய பயிர் தொடங்க / மீட்டமை' : 'Switch Crop / Restart Journey'}
            </button>
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="mt-6 pt-4 border-t border-emerald-700/60 space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-emerald-200">
            <span>
              {isTa ? 'பயண முன்னேற்றம்' : 'Journey Progress'}: <strong className="text-white">Step {currentStep} of 10</strong> ({STEP_TITLES[currentStep - 1]?.[isTa ? 'ta' : 'en']})
            </span>
            <span>{Math.round((currentStep / 10) * 100)}% {isTa ? 'நிறைவு' : 'Completed'}</span>
          </div>
          <div className="w-full bg-emerald-950/60 rounded-full h-2.5 overflow-hidden border border-emerald-700/50">
            <div
              className="bg-gradient-to-r from-amber-400 to-emerald-400 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${(currentStep / 10) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* EDUCATIONAL DISCLAIMER BANNER */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex items-start gap-3 text-amber-900 text-xs">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-semibold">
            {isTa ? 'அரசு கல்வி வழிகாட்டுதல் அறிவிப்பு (Educational Disclaimer):' : 'Educational Agricultural Guidance:'}
          </p>
          <p className="text-amber-800 leading-relaxed">
            {isTa
              ? 'இந்த வழிகாட்டி தமிழ்நாடு வேளாண்மைப் பல்கலைக்கழகம் (TNAU) மற்றும் ICAR தரவுகளை அடிப்படையாகக் கொண்டது. தட்பவெப்பநிலை, மண் வளம் மற்றும் பூச்சி தாக்குதலுக்கு ஏற்ப கள நிலைமைகள் மாறுபடலாம். மகசூல், சந்தை விலை அல்லது லாபம் உத்தரவாதம் செய்யப்படாது. தீவிர இடர்பாடுகளுக்கு உங்கள் வட்டார வேளாண்மை அலுவலரை (AO / KVK) அணுகவும்.'
              : 'This journey is an educational guide synthesized from validated TNAU & ICAR crop production protocols. Real farm outcomes vary by weather, soil ecology, and management. Yield, price, or profit are never guaranteed. Consult your local block Agricultural Officer (AO) or KVK scientist for field-specific anomalies.'}
          </p>
        </div>
      </div>

      {/* 10-STEP PROGRESS NAVIGATION BAR */}
      <div className="bg-white rounded-xl border border-slate-200 p-2 shadow-xs overflow-x-auto scrollbar-thin">
        <div className="flex items-center min-w-max gap-1">
          {STEP_TITLES.map((st) => {
            const Icon = st.icon;
            const isCompleted = currentStep > st.step;
            const isActive = currentStep === st.step;

            return (
              <button
                key={st.step}
                type="button"
                onClick={() => {
                  saveProgress(st.step);
                }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : isCompleted
                    ? 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isActive
                      ? 'bg-amber-400 text-amber-950'
                      : isCompleted
                      ? 'bg-emerald-200 text-emerald-900'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {isCompleted ? <Check className="w-3 h-3 text-emerald-800" /> : st.step}
                </div>
                <Icon className="w-3.5 h-3.5 opacity-80" />
                <span>{st[isTa ? 'ta' : 'en']}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* STEP 1: UNDERSTAND THE FARMER */}
      {/* ==================================================================== */}
      {currentStep === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                1
              </span>
              <h2 className="text-xl font-bold text-slate-900">
                {isTa ? 'படி 1: உங்கள் பண்ணை விவரங்களை அறிக' : 'Step 1: Understand Your Farm & Goals'}
              </h2>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              {isTa
                ? 'கடினமான வேளாண் சொற்கள் தேவையில்லை. உங்களுக்குத் தெரியாதவற்றுக்கு "எனக்குத் தெரியாது" என்று தேர்ந்தெடுக்கலாம்.'
                : 'No complex agricultural terminology required. Choose "I don\'t know" for any unfamiliar term. We explain why each factor matters.'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* District */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'மாவட்டம்' : 'District'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? உள்ளூர் தட்பவெப்பம் மற்றும் சந்தை தூரத்தை நிர்ணயிக்கிறது.' : 'Why? Dictates local rainfall & nearby wholesale mandi.'}
                  </span>
                )}
              </label>
              <select
                value={profile.district}
                onChange={(e) => setProfile({ ...profile, district: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {(availableDistricts.length > 0 ? availableDistricts : ['Thanjavur', 'Salem', 'Coimbatore', 'Madurai']).map(
                  (d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  )
                )}
              </select>
            </div>

            {/* Land Area & Unit */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'நில அளவு மற்றும் அலகு' : 'Land Area & Unit'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? விதை அளவு மற்றும் செலவுகளை துல்லியமாக கணக்கிட உதவுகிறது.' : 'Why? Scales seed quantity and budget accurately.'}
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={profile.landArea}
                  onChange={(e) => setProfile({ ...profile, landArea: parseFloat(e.target.value) || 1 })}
                  className="w-1/2 text-sm border border-slate-300 rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-emerald-500"
                  placeholder="e.g. 1"
                />
                <select
                  value={profile.landUnit}
                  onChange={(e) => setProfile({ ...profile, landUnit: e.target.value as SpecialOperationLandUnit })}
                  className="w-1/2 text-sm border border-slate-300 rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-emerald-500 bg-white"
                >
                  <option value="acres">{isTa ? 'ஏக்கர் (Acres)' : 'Acres'}</option>
                  <option value="cents">{isTa ? 'சென்ட் (Cents - 100 cents = 1 acre)' : 'Cents'}</option>
                  <option value="guntas">{isTa ? 'குண்டா (Guntas - 40 guntas = 1 acre)' : 'Guntas'}</option>
                  <option value="sq_ft">{isTa ? 'சதுர அடி (Sq. Ft)' : 'Square Feet'}</option>
                </select>
              </div>
            </div>

            {/* Water Availability */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'நீர் வசதி' : 'Water Availability'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? நெல் போன்ற பயிர்களுக்கு அதிக நீர் தேவை; நிலக்கடலைக்கு குறைந்த நீர் போதும்.' : 'Why? Paddy needs standing water; pulses/groundnut need minimal.'}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'ample_borewell', en: 'Ample Borewell / Well', ta: 'கிணறு / ஆழ்துளை (போதுமானது)' },
                  { id: 'canal_seasonal', en: 'Canal (Seasonal)', ta: 'வாய்க்கால் பாசனம் (பருவக்காலம்)' },
                  { id: 'rainfed_only', en: 'Rainfed Only', ta: 'வானம் பார்த்த பூமி (மழை மட்டும்)' },
                  { id: 'unknown', en: "I don't know yet", ta: 'சரியாகத் தெரியாது' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setProfile({ ...profile, waterAvailability: opt.id as SpecialOperationWater })}
                    className={`p-2.5 rounded-xl border text-left text-xs font-semibold transition-all ${
                      profile.waterAvailability === opt.id
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt[isTa ? 'ta' : 'en']}
                  </button>
                ))}
              </div>
            </div>

            {/* Soil Type */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'மண் வகை (தெரிந்தால்)' : 'Soil Type (If Known)'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? வடிகால் வசதி மற்றும் வேர் வளர்ச்சி மண்ணைப் பொறுத்தது.' : 'Why? Affects root aeration and water drainage.'}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'red_sandy_loam', en: 'Red Sandy Loam', ta: 'செம்மண் / மணல் கலந்த மண்' },
                  { id: 'clay_loam', en: 'Clay / Heavy Loam', ta: 'களிமண்' },
                  { id: 'alluvial', en: 'Alluvial (River Basin)', ta: 'வண்டல் மண்' },
                  { id: 'unknown', en: "I don't know (Soil Test)", ta: 'எனக்குத் தெரியாது (பரிசோதனை தேவை)' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setProfile({ ...profile, soilType: opt.id as SpecialOperationSoil })}
                    className={`p-2.5 rounded-xl border text-left text-xs font-semibold transition-all ${
                      profile.soilType === opt.id
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt[isTa ? 'ta' : 'en']}
                  </button>
                ))}
              </div>
            </div>

            {/* Season */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'சாகுபடி பருவம்' : 'Season'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? பூக்கும் கால தட்பவெப்பம் மகசூலை தீர்மானிக்கிறது.' : 'Why? Day length and temperature govern flowering.'}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'samba_thaladi', en: 'Samba/Thaladi (Sep-Jan)', ta: 'சம்பா / தாளடி (செப்-ஜன)' },
                  { id: 'kuruvai', en: 'Kuruvai (Jun-Sep)', ta: 'குறுவை (ஜூன்-செப்)' },
                  { id: 'navarai_summer', en: 'Navarai / Summer (Jan-May)', ta: 'நவரை / கோடை (ஜன-மே)' },
                  { id: 'unknown', en: 'Year-Round / Flexible', ta: 'எப்போது வேண்டுமானாலும்' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setProfile({ ...profile, season: opt.id as SpecialOperationSeason })}
                    className={`p-2.5 rounded-xl border text-left text-xs font-semibold transition-all ${
                      profile.season === opt.id
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt[isTa ? 'ta' : 'en']}
                  </button>
                ))}
              </div>
            </div>

            {/* Budget Range */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'முதலீட்டு வரம்பு (Budget Range)' : 'Available Budget Range'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? ஆரம்ப மூலதனத்திற்குள் செலவு கட்டுக்குள் இருக்க வேண்டும்.' : 'Why? Keeps initial inputs within your comfort zone.'}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'micro_under_15k', en: 'Under ₹15,000 (Micro)', ta: '₹15,000க்கு கீழ் (குறைந்த செலவு)' },
                  { id: 'low_15k_35k', en: '₹15,000 - ₹35,000', ta: '₹15,000 முதல் ₹35,000 வரை' },
                  { id: 'medium_35k_75k', en: '₹35,000 - ₹75,000', ta: '₹35,000 முதல் ₹75,000 வரை' },
                  { id: 'flexible_above_75k', en: 'Flexible (Above ₹75k)', ta: 'தேவைக்கேற்ப முதலீடு' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setProfile({ ...profile, budgetRange: opt.id as SpecialOperationBudget })}
                    className={`p-2.5 rounded-xl border text-left text-xs font-semibold transition-all ${
                      profile.budgetRange === opt.id
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt[isTa ? 'ta' : 'en']}
                  </button>
                ))}
              </div>
            </div>

            {/* Farming Goal */}
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                <span>{isTa ? 'விவசாயத்தின் நோக்கம்' : 'Primary Farming Goal'}</span>
                {showHelp && (
                  <span className="text-[11px] text-emerald-700 font-normal">
                    {isTa ? 'ஏன்? உங்கள் உண்மையான தேவையை நோக்கி வழிநடத்துகிறது.' : 'Why? Tailors crop selection and market strategy.'}
                  </span>
                )}
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { id: 'commercial_income', en: 'Commercial Income', ta: 'வணிக வருமானம் (Cash flow)' },
                  { id: 'household_consumption', en: 'Home Food Security', ta: 'குடும்ப உணவுத் தேவை' },
                  { id: 'low_risk_learning', en: 'Low-Risk Learning', ta: 'முதல் முறை கற்றல் (குறைந்த ஆபத்து)' },
                  { id: 'organic_lifestyle', en: 'Organic Lifestyle', ta: 'இயற்கை முறை வேளாண்மை' },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setProfile({ ...profile, farmingGoal: opt.id as SpecialOperationGoal })}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      profile.farmingGoal === opt.id
                        ? 'border-emerald-600 bg-emerald-50 text-emerald-900 shadow-xs'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {opt[isTa ? 'ta' : 'en']}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(2)}
              className="px-6 py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-sm font-bold flex items-center gap-2 shadow-md transition-all"
            >
              <span>{isTa ? 'பொருத்தமான பயிர்களை பரிந்துரைக்க' : 'Find Matching Beginner Crops'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 2: SELECT A SUITABLE CROP */}
      {/* ==================================================================== */}
      {currentStep === 2 && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                    2
                  </span>
                  <h2 className="text-xl font-bold text-slate-900">
                    {isTa ? 'படி 2: உங்களுக்கான பொருத்தமான பயிரைத் தேர்ந்தெடுக்கவும்' : 'Step 2: Recommended Beginner Crops'}
                  </h2>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  {isTa
                    ? 'உங்கள் மாவட்டம், மண் மற்றும் நீர் நிலைக்கு ஏற்ப TNAU வேளாண்மை வழிகாட்டுதலின்படி வரிசைப்படுத்தப்பட்டுள்ளது.'
                    : 'Ranked according to verified TNAU agro-climatic advisories for your conditions. Trade-offs and risks clearly explained.'}
                </p>
              </div>

              <button
                type="button"
                onClick={() => saveProgress(1)}
                className="text-xs text-slate-600 hover:text-emerald-700 font-semibold flex items-center gap-1 self-start sm:self-auto"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                {isTa ? 'சுயவிவரத்தை திருத்த' : 'Edit Farm Profile'}
              </button>
            </div>

            {isLoadingCrops ? (
              <div className="p-12 text-center text-slate-500 space-y-3">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600" />
                <p className="text-sm font-medium">{isTa ? 'பயிர்கள் பகுப்பாய்வு செய்யப்படுகின்றன...' : 'Evaluating agronomic suitability...'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {candidateCrops.map((crop) => {
                  const isSelected = selectedCropId === crop.cropId;

                  return (
                    <div
                      key={crop.cropId}
                      className={`rounded-2xl border p-5 transition-all space-y-4 ${
                        isSelected
                          ? 'border-emerald-600 bg-emerald-50/40 ring-2 ring-emerald-500 shadow-md'
                          : 'border-slate-200 bg-white hover:border-emerald-300'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-base font-bold text-slate-900">
                              {crop.cropName[isTa ? 'ta' : 'en']}
                            </h3>
                            <span className="px-2 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800">
                              {crop.suitabilityScore}% {isTa ? 'பொருத்தம்' : 'Match'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {crop.varietySuggestions?.join(', ')}
                          </p>
                        </div>

                        <div className="text-right shrink-0">
                          <span className="text-xs font-bold text-slate-700 block">
                            ⏱️ {crop.durationDays} {isTa ? 'நாட்கள்' : 'Days'}
                          </span>
                          <span className="text-[11px] text-slate-500 block">
                            {crop.budgetEstimatePerAcre}
                          </span>
                        </div>
                      </div>

                      {/* Suitability Reason */}
                      <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                        {crop.suitabilityReason[isTa ? 'ta' : 'en']}
                      </p>

                      {/* Trade-offs & Risks (Mandatory beginner education) */}
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[11px] font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                          {isTa ? 'இடர்பாடுகள் & கவனிக்க வேண்டியவை (Risks & Trade-offs):' : 'Key Trade-offs & Operational Risks:'}
                        </span>
                        <ul className="text-xs text-slate-600 space-y-1 pl-4 list-disc">
                          {crop.tradeOffsAndRisks?.slice(0, 2).map((risk, idx) => (
                            <li key={idx}>{risk[isTa ? 'ta' : 'en']}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Reference Badge */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                        <span className="flex items-center gap-1">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                          {crop.verifiedReference?.institution}
                        </span>
                        <a
                          href={crop.verifiedReference?.sourceUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-700 hover:underline flex items-center gap-0.5"
                        >
                          <span>{isTa ? 'சான்று காண்க' : 'View Source'}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>

                      {/* Select Button */}
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCropId(crop.cropId);
                          saveProgress(3, { selectedCropId: crop.cropId });
                        }}
                        className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                          isSelected
                            ? 'bg-emerald-700 text-white shadow-xs'
                            : 'bg-slate-100 text-slate-700 hover:bg-emerald-600 hover:text-white'
                        }`}
                      >
                        {isSelected ? (
                          <>
                            <Check className="w-4 h-4" />
                            {isTa ? 'தேர்வு செய்யப்பட்டது — அடுத்த படிக்குச் செல்' : 'Selected — Continue to Farm Prep'}
                          </>
                        ) : (
                          <>
                            <Sprout className="w-4 h-4" />
                            {isTa ? 'இந்த பயிரைத் தேர்ந்தெடு' : 'Select this Crop'}
                          </>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {cropsDisclaimer && (
              <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-3 text-xs text-amber-900 flex items-start gap-2">
                <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{cropsDisclaimer}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 3: PREPARE THE FARM */}
      {/* ==================================================================== */}
      {currentStep === 3 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  3
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 3: பண்ணை மற்றும் நில தயாரிப்பு சரிபார்ப்பு' : 'Step 3: Farm & Soil Preparation Checklist'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'விதைப்பதற்கு முன் செய்ய வேண்டிய அத்தியாவசிய பணிகள். நிறைவு செய்தவற்றை டிக் செய்யவும்.'
                  : 'Critical pre-sowing actions. Check off each action as you complete it on your land.'}
              </p>
            </div>

            <div className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 self-start sm:self-auto">
              {cropGuide?.cropName?.[isTa ? 'ta' : 'en'] || selectedCropId.toUpperCase()}
            </div>
          </div>

          {/* SOIL TESTING PROTOCOL CARD (Highlight feature) */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
              <Compass className="w-4 h-4 text-amber-700" />
              <span>{isTa ? 'மண் பரிசோதனை வழிகாட்டுதல் (8-புள்ளி மாதிரி எடுக்கும் முறை)' : 'Soil Testing Protocol (8-Point Zigzag Sampling)'}</span>
            </div>
            <p className="text-xs text-amber-950 leading-relaxed">
              {isTa
                ? 'உங்கள் நிலத்தில் ‘Z’ வடிவில் 8 இடங்களில் 15 செ.மீ ஆழத்தில் ‘V’ வடிவ பள்ளம் தோண்டி ஒரு பிடி மண் எடுக்கவும். அனைத்தையும் பிளாஸ்டிக் வாளியில் கலந்து, நிழலில் உலர்த்தி, 500 கிராம் மண்ணை அருகில் உள்ள வேளாண்மை விரிவாக்க மையம் அல்லது KVK மண் பரிசோதனை கூடத்திற்கு அனுப்பவும்.'
                : 'Walk across the field in a zigzag ‘Z’ pattern. Dig a 15 cm V-shaped cut at 8 spots, scrape 1 cm from the slice into a clean bucket. Mix thoroughly, shade dry, and send 500g in a cloth bag to your nearest Agricultural Department Soil Testing Lab (STL) or Salem KVK.'}
            </p>
            <div className="flex items-center gap-3 text-[11px] text-amber-800 pt-1 font-medium">
              <span>⚠️ {isTa ? 'உரமிட்ட உடனோ அல்லது ஈரமான போதோ மண் எடுக்கக் கூடாது.' : 'Never sample immediately after fertilizer application or when waterlogged.'}</span>
            </div>
          </div>

          {/* CHECKLIST ITEMS */}
          <div className="space-y-3">
            {cropGuide?.landPreparation?.steps?.map((step) => {
              const checked = !!checklists[step.id];

              return (
                <div
                  key={step.id}
                  onClick={() => toggleChecklist(step.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition-all flex items-start gap-3.5 ${
                    checked
                      ? 'border-emerald-500 bg-emerald-50/50 shadow-xs'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div
                    className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-colors ${
                      checked
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'border-slate-300 bg-white'
                    }`}
                  >
                    {checked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>

                  <div className="space-y-1 flex-1">
                    <h4 className={`text-sm font-bold ${checked ? 'text-emerald-950 line-through' : 'text-slate-900'}`}>
                      {step.title[isTa ? 'ta' : 'en']}
                    </h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {step.description[isTa ? 'ta' : 'en']}
                    </p>

                    {step.kvkContactAlert && (
                      <div className="mt-2 text-[11px] text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg p-2 font-medium">
                        📞 {step.kvkContactAlert[isTa ? 'ta' : 'en']}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(2)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(4)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'விதைப்பு மற்றும் நடவு படிக்குச் செல்' : 'Proceed to Planting Step'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 4: PLANTING (SPACING & DEPTH) */}
      {/* ==================================================================== */}
      {currentStep === 4 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  4
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 4: விதைப்பு மற்றும் நடவு முறை' : 'Step 4: Seed Selection, Spacing & Planting Date'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'பயிர் இடைவெளி, ஆழம் மற்றும் நடவு நேரத்தை சரியாக பின்பற்றவும்.'
                  : 'Accurate spacing prevents crop overcrowding and fungal build-up.'}
              </p>
            </div>

            <div className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 self-start sm:self-auto">
              {cropGuide?.cropName?.[isTa ? 'ta' : 'en']}
            </div>
          </div>

          {/* SPACING & FIELD LAYOUT DIAGRAM / ILLUSTRATION */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 relative overflow-hidden space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Compass className="w-4 h-4" />
                {isTa ? 'வயல் இடைவெளி மாதிரி (Field Spacing Diagram)' : 'Interactive Spacing Blueprint'}
              </span>
              <span className="text-xs text-slate-400">TNAU Production Manual</span>
            </div>

            {/* Visual Row & Plant Diagram */}
            <div className="bg-slate-800/80 rounded-xl p-6 border border-slate-700 flex flex-col items-center justify-center space-y-4">
              <div className="w-full max-w-md flex justify-between items-center text-xs text-emerald-300 font-mono border-b border-dashed border-emerald-500/50 pb-2">
                <span>Row A (வரிசை 1)</span>
                <span>↔ {cropGuide?.plantingInstructions?.spacing?.rowToRowCm || 60} cm (பார் இடைவெளி)</span>
                <span>Row B (வரிசை 2)</span>
              </div>

              <div className="w-full max-w-md flex justify-around py-3">
                {[1, 2, 3].map((plantIdx) => (
                  <div key={plantIdx} className="flex flex-col items-center space-y-1">
                    <span className="text-2xl">🌱</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {plantIdx < 3 ? `↔ ${cropGuide?.plantingInstructions?.spacing?.plantToPlantCm || 45} cm` : 'Plant'}
                    </span>
                  </div>
                ))}
              </div>

              <div className="text-xs text-slate-300 text-center max-w-lg leading-relaxed">
                {cropGuide?.plantingInstructions?.spacing?.diagramText?.[isTa ? 'ta' : 'en'] ||
                  'Maintain proper spacing for air circulation and easy weeding.'}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
              <div className="bg-slate-800 p-3 rounded-xl border border-slate-700">
                <span className="text-slate-400 block text-[11px]">{isTa ? 'விதை / நாற்று அளவு' : 'Seed Rate / Acre'}</span>
                <strong className="text-white text-xs mt-0.5 block">
                  {cropGuide?.plantingInstructions?.seedRatePerAcre?.[isTa ? 'ta' : 'en'] || 'Standard rate'}
                </strong>
              </div>
              <div className="bg-slate-800 p-3 rounded-xl border border-slate-700">
                <span className="text-slate-400 block text-[11px]">{isTa ? 'விதைக்கும் ஆழம்' : 'Planting Depth'}</span>
                <strong className="text-white text-xs mt-0.5 block">
                  {cropGuide?.plantingInstructions?.plantingDepthCm || 2} cm
                </strong>
              </div>
              <div className="bg-slate-800 p-3 rounded-xl border border-slate-700">
                <span className="text-slate-400 block text-[11px]">{isTa ? 'உகந்த நேரம்' : 'Ideal Time of Day'}</span>
                <strong className="text-white text-xs mt-0.5 block">
                  {cropGuide?.plantingInstructions?.idealTimingOfDay?.[isTa ? 'ta' : 'en'] || 'Late afternoon'}
                </strong>
              </div>
            </div>
          </div>

          {/* Sowing / Nursery Method Explanation */}
          <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4 text-xs text-slate-700 space-y-1">
            <h4 className="font-bold text-emerald-950">
              {isTa ? 'விதைப்பு மற்றும் நாற்று நடும் முறை:' : 'Transplanting / Sowing Method:'}
            </h4>
            <p className="leading-relaxed">
              {cropGuide?.plantingInstructions?.nurseryAndSowingMethod?.[isTa ? 'ta' : 'en']}
            </p>
          </div>

          {/* ACTUAL PLANTING DATE INPUT (Powers dynamic timeline in Step 6) */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-700" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                {isTa ? 'உண்மையான நடவு / விதைப்பு தேதி' : 'Record Actual Sowing / Planting Date'}
              </h4>
            </div>
            <p className="text-xs text-slate-600">
              {isTa
                ? 'இந்தத் தேதியை அடிப்படையாகக் கொண்டு தினசரி பாசனம், உரமிடுதல் மற்றும் அறுவடை நாள் கணக்கிடப்படும்.'
                : 'This actual planting date dynamically generates your crop-stage calendar and automated task reminders.'}
            </p>
            <div className="max-w-xs">
              <input
                type="date"
                value={plantingDate}
                onChange={(e) => setPlantingDate(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-xl px-3.5 py-2.5 focus:ring-2 focus:ring-emerald-500 bg-white font-medium"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(3)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(5)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'தினசரி பராமரிப்புக்குச் செல்' : 'Save & Unlock Crop Care'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 5: DAILY & WEEKLY CROP CARE */}
      {/* ==================================================================== */}
      {currentStep === 5 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  5
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 5: தினசரி & வாராந்திர பயிர் பராமரிப்பு' : 'Step 5: Daily & Weekly Crop Care Plan'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'பாசனம், மேலுரமிடுதல், களை எடுத்தல் மற்றும் பூச்சி கட்டுப்பாடு வழிகாட்டல்.'
                  : 'Stage-by-stage agronomic actions with integrated smart weather, irrigation, and disease tools.'}
              </p>
            </div>

            {/* Smart Tools Shortcuts */}
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => onNavigate?.('weather')}
                className="px-3 py-1.5 rounded-lg bg-sky-50 text-sky-800 hover:bg-sky-100 text-xs font-bold flex items-center gap-1 border border-sky-200"
              >
                <CloudSun className="w-3.5 h-3.5 text-sky-600" />
                {isTa ? 'வானிலை' : 'Weather'}
              </button>
              <button
                type="button"
                onClick={() => onNavigate?.('irrigation')}
                className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-800 hover:bg-blue-100 text-xs font-bold flex items-center gap-1 border border-blue-200"
              >
                <Droplet className="w-3.5 h-3.5 text-blue-600" />
                {isTa ? 'பாசனம்' : 'Smart Irrigation'}
              </button>
              <button
                type="button"
                onClick={() => onNavigate?.('disease')}
                className="px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-xs font-bold flex items-center gap-1 border border-emerald-200"
              >
                <Bug className="w-3.5 h-3.5 text-emerald-600" />
                {isTa ? 'நோய் கண்டறி' : 'Leaf Scanner'}
              </button>
            </div>
          </div>

          {/* STAGES LIST */}
          <div className="space-y-4">
            {cropGuide?.cropCareStages?.map((stage) => (
              <div key={stage.stageNumber} className="border border-slate-200 rounded-2xl p-5 space-y-3 bg-slate-50/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-emerald-700 text-white text-xs font-bold flex items-center justify-center">
                      {stage.stageNumber}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900">
                      {stage.stageName[isTa ? 'ta' : 'en']}
                    </h3>
                  </div>
                  <span className="text-xs text-slate-500 font-medium">
                    {stage.durationDays} {isTa ? 'நாட்கள்' : 'days duration'}
                  </span>
                </div>

                <div className="space-y-2">
                  {stage.tasks?.map((t, idx) => (
                    <div
                      key={idx}
                      className="bg-white rounded-xl border border-slate-200 p-3 text-xs flex items-start gap-2.5 shadow-2xs"
                    >
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase shrink-0 mt-0.5 bg-slate-100 text-slate-700">
                        {t.category}
                      </span>
                      <span className="text-slate-700 leading-relaxed flex-1">
                        {t.task[isTa ? 'ta' : 'en']}
                      </span>
                      {t.criticality === 'critical' && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 shrink-0">
                          CRITICAL
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                {stage.smartFeaturesPrompt && (
                  <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 text-xs text-sky-900 flex items-center justify-between gap-3">
                    <span className="leading-relaxed">
                      💡 {stage.smartFeaturesPrompt.message[isTa ? 'ta' : 'en']}
                    </span>
                    <button
                      type="button"
                      onClick={() => onNavigate?.(stage.smartFeaturesPrompt?.feature as NavTab)}
                      className="px-3 py-1 bg-sky-700 hover:bg-sky-800 text-white rounded-lg text-xs font-bold shrink-0"
                    >
                      {isTa ? 'திறக்க' : 'Open Tool'}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(4)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(6)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'வளர்ச்சி கண்காணிப்புக்குச் செல்' : 'Go to Growth Tracker'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 6: TRACK GROWTH (TIMELINE & OBSERVATIONS) */}
      {/* ==================================================================== */}
      {currentStep === 6 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  6
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 6: வளர்ச்சி காலவரிசை & களக் குறிப்புகள்' : 'Step 6: Growth Tracker & Farmer Observation Log'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'நடவு தேதியிலிருந்து தற்போதைய பயிர் பருவம் மற்றும் அடுத்த கட்ட பணிகளை அறியலாம்.'
                  : 'Dynamic timeline calculated from your actual planting date with deviation alerts.'}
              </p>
            </div>

            <button
              type="button"
              onClick={handleSendReminder}
              className="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-900 hover:bg-amber-100 text-xs font-bold border border-amber-200 flex items-center gap-1.5 self-start sm:self-auto"
            >
              <span>🔔 {isTa ? 'நினைவூட்டல் அனுப்பு' : 'Test Reminder Notification'}</span>
            </button>
          </div>

          {/* DYNAMIC TIMELINE STATUS CARD */}
          {timeline && (
            <div className="bg-gradient-to-br from-emerald-900 to-teal-900 text-white rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-emerald-300 font-bold uppercase tracking-wider block">
                    {isTa ? 'தற்போதைய பயிர் நிலை' : 'Active Growth Stage'}
                  </span>
                  <h3 className="text-xl font-extrabold mt-0.5">
                    {timeline.stages?.find((s) => s.isActive)?.stageName?.[isTa ? 'ta' : 'en'] || 'Vegetative Stage'}
                  </h3>
                </div>

                <div className="text-right">
                  <span className="text-2xl font-black text-amber-400">
                    Day {timeline.daysElapsed}
                  </span>
                  <span className="text-xs text-emerald-200 block">
                    of {timeline.totalDurationDays} {isTa ? 'நாட்கள்' : 'Days'}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-emerald-200">
                  <span>{timeline.plantingDate ? `Planted: ${timeline.plantingDate}` : 'Relative Schedule'}</span>
                  <span>{timeline.percentComplete}% {isTa ? 'முடிந்தது' : 'Complete'}</span>
                </div>
                <div className="w-full bg-emerald-950 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-amber-400 h-2 rounded-full transition-all"
                    style={{ width: `${timeline.percentComplete}%` }}
                  />
                </div>
              </div>

              {/* Stages Pill Carousel */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
                {timeline.stages?.map((st) => (
                  <div
                    key={st.stageNumber}
                    className={`p-2.5 rounded-xl border text-xs text-center space-y-1 ${
                      st.isActive
                        ? 'bg-amber-400 text-amber-950 font-bold border-amber-300 shadow-xs'
                        : st.isCompleted
                        ? 'bg-emerald-800/80 text-emerald-200 border-emerald-700'
                        : 'bg-emerald-950/40 text-slate-400 border-emerald-900'
                    }`}
                  >
                    <span className="block text-[10px]">Stage {st.stageNumber}</span>
                    <span className="block truncate">{st.stageName[isTa ? 'ta' : 'en']}</span>
                    <span className="block text-[9px] opacity-80">
                      Day {st.startDay}-{st.endDay}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* OBSERVATION LOGGER */}
          <div className="border border-slate-200 rounded-2xl p-5 space-y-4 bg-slate-50">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Camera className="w-4 h-4 text-emerald-700" />
              {isTa ? 'கள அவதானிப்பு மற்றும் மாறுபாடுகளை பதிவு செய்க' : 'Record Growth Observations & Deviations'}
            </h4>

            <form onSubmit={handleAddObservation} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">
                    {isTa ? 'பருவம் (Stage)' : 'Crop Stage'}
                  </label>
                  <select
                    value={newObsStage}
                    onChange={(e) => setNewObsStage(parseInt(e.target.value) || 1)}
                    className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white"
                  >
                    {[1, 2, 3, 4, 5].map((s) => (
                      <option key={s} value={s}>
                        Stage {s}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">
                    {isTa ? 'புகைப்பட முகவரி (விரும்பினால்)' : 'Photo URL / Evidence Preview (Optional)'}
                  </label>
                  <input
                    type="url"
                    value={newObsPhoto}
                    onChange={(e) => setNewObsPhoto(e.target.value)}
                    placeholder="https://... or sample photo link"
                    className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'களக் குறிப்பு (Observations / Leaf condition / Pests noticed)' : 'Farmer Field Notes'}
                </label>
                <textarea
                  rows={2}
                  value={newObsNote}
                  onChange={(e) => setNewObsNote(e.target.value)}
                  placeholder={
                    isTa
                      ? 'இலைகளில் மஞ்சள் புள்ளிகள் தென்படுகின்றன அல்லது முதல் பூ மொட்டுகள் தோன்றியுள்ளன...'
                      : 'Noticed uniform flowering; leaf canopy covering row spacing; no whiteflies seen...'
                  }
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              {/* Deviation toggle */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newObsIsDeviation}
                    onChange={(e) => setNewObsIsDeviation(e.target.checked)}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="text-xs font-bold text-amber-900">
                    ⚠️ {isTa ? 'இது வழக்கமான வளர்ச்சியிலிருந்து மாறுபட்டதா? (Record Deviation)' : 'Is this a deviation from normal growth?'}
                  </span>
                </label>

                {newObsIsDeviation && (
                  <input
                    type="text"
                    value={newObsReason}
                    onChange={(e) => setNewObsReason(e.target.value)}
                    placeholder={isTa ? 'மாறுபாட்டுக்கான காரணம் (எ.கா: தொடர் மழை காரணமாக வளர்ச்சி தாமதம்)' : 'Reason (e.g. unexpected cold snap delayed flower set by 5 days)'}
                    className="w-full text-xs border border-amber-300 rounded-lg p-2 bg-amber-50/50"
                  />
                )}
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoggingObs || !newObsNote.trim()}
                  className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{isTa ? 'குறிப்பை பதிவு செய்க' : 'Save Observation'}</span>
                </button>
              </div>
            </form>

            {/* List of logged observations */}
            {journey?.observations && journey.observations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-200">
                <span className="text-[11px] font-bold text-slate-500 block uppercase">
                  {isTa ? 'பதிவு செய்யப்பட்ட குறிப்புகள்' : 'Previous Observation Logs'}
                </span>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {journey.observations.map((obs) => (
                    <div
                      key={obs.id}
                      className={`p-3 rounded-xl border text-xs space-y-1 ${
                        obs.isDeviation
                          ? 'border-amber-300 bg-amber-50/60'
                          : 'border-slate-200 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="font-bold text-slate-700">Stage {obs.stageNumber} • {obs.date}</span>
                        {obs.isDeviation && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-200 text-amber-900 font-bold">
                            DEVIATION
                          </span>
                        )}
                      </div>
                      <p className="text-slate-800 leading-relaxed">{obs.note}</p>
                      {obs.deviationReason && (
                        <p className="text-[11px] text-amber-900 font-medium">
                          <strong>Reason:</strong> {obs.deviationReason}
                        </p>
                      )}
                      {obs.photoUrl && (
                        <a
                          href={obs.photoUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-emerald-700 underline flex items-center gap-1"
                        >
                          <Camera className="w-3 h-3" /> View Photo Preview
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(5)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(7)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'அறுவடை தயாரிப்புக்குச் செல்' : 'Proceed to Harvest Readiness'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 7: HARVEST READINESS */}
      {/* ==================================================================== */}
      {currentStep === 7 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  7
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 7: அறுவடை முதிர்ச்சி அறிகுறிகள் & தரம் பிரித்தல்' : 'Step 7: Harvest Readiness, Handling & Grading'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'பயிரை எப்போது, எப்படி அறுவடை செய்வது மற்றும் தரம் பிரிக்கும் வழிமுறைகள்.'
                  : 'Crop-specific maturity indicators, shade cooling, and grading standards.'}
              </p>
            </div>

            <div className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 self-start sm:self-auto">
              {cropGuide?.cropName?.[isTa ? 'ta' : 'en']}
            </div>
          </div>

          {/* MATURITY INDICATORS */}
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl p-5 space-y-3">
            <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              {isTa ? 'முதிர்ச்சி அறிகுறிகள் (Maturity Indicators):' : 'Visual & Tactile Maturity Indicators:'}
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {cropGuide?.harvestReadiness?.maturityIndicators?.map((ind, idx) => (
                <div key={idx} className="bg-white rounded-xl p-3 border border-emerald-100 text-xs text-slate-800 leading-relaxed shadow-2xs">
                  {ind[isTa ? 'ta' : 'en']}
                </div>
              ))}
            </div>
          </div>

          {/* HARVESTING METHOD & POST-HARVEST CARE */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border border-slate-200 rounded-xl p-4 space-y-2 bg-slate-50">
              <h4 className="text-xs font-bold text-slate-900 uppercase">
                {isTa ? 'அறுவடை செய்யும் முறை' : 'Harvesting Technique'}
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed">
                {cropGuide?.harvestReadiness?.harvestingMethod?.[isTa ? 'ta' : 'en']}
              </p>
            </div>

            <div className="border border-slate-200 rounded-xl p-4 space-y-2 bg-slate-50">
              <h4 className="text-xs font-bold text-slate-900 uppercase">
                {isTa ? 'சேமிப்பு ஆலோசனை' : 'Storage Advisory'}
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed">
                {cropGuide?.harvestReadiness?.storageAdvisory?.[isTa ? 'ta' : 'en']}
              </p>
            </div>
          </div>

          {/* GRADING STANDARDS TABLE */}
          <div className="border border-slate-200 rounded-2xl p-5 space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {isTa ? 'தரம் பிரிக்கும் அளவுகோல் (Grading Specifications)' : 'Grading Specifications (Grade A vs Grade B)'}
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {cropGuide?.harvestReadiness?.gradingStandards?.map((g, idx) => (
                <div key={idx} className="border border-slate-200 rounded-xl p-3.5 space-y-1 bg-white">
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-emerald-100 text-emerald-800">
                    {g.grade}
                  </span>
                  <p className="text-xs text-slate-700 leading-relaxed pt-1">
                    {g.description[isTa ? 'ta' : 'en']}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* SAFETY CAUTION */}
          {cropGuide?.harvestReadiness?.safetyCaution && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 text-xs text-rose-950 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-700 shrink-0 mt-0.5" />
              <span>{cropGuide.harvestReadiness.safetyCaution[isTa ? 'ta' : 'en']}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(6)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(8)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'செலவு கணக்கீட்டுக்குச் செல்' : 'Proceed to Cost Worksheet'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 8: ESTIMATE COSTS (TRANSPARENT WORKSHEET) */}
      {/* ==================================================================== */}
      {currentStep === 8 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  8
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 8: வெளிப்படையான சாகுபடி செலவு கணக்கீடு' : 'Step 8: Transparent Input-Cost Worksheet'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'TNAU நிலையான மாதிரி மதிப்பீடு vs உங்கள் நேரடி செலவு. அளவுகளையும் விலையையும் நீங்கள் திருத்தலாம்.'
                  : 'Compare institutional benchmark rates with your actual expenses. Fully editable lines.'}
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-500 block">{isTa ? 'மொத்த செயல்பாட்டு செலவு' : 'Total Operating Cost'}</span>
              <span className="text-xl font-black text-emerald-800">
                ₹{costsWorksheet.totalOperatingCost?.toLocaleString('en-IN') || 0}
              </span>
            </div>
          </div>

          {/* EDITABLE COST WORKSHEET TABLE */}
          <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 uppercase font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">{isTa ? 'செலவு இனம்' : 'Expense Item'}</th>
                    <th className="px-4 py-3">{isTa ? 'அரசு மாதிரி விகிதம்' : 'Govt Benchmark'}</th>
                    <th className="px-4 py-3">{isTa ? 'உங்கள் அளவு' : 'Quantity'}</th>
                    <th className="px-4 py-3">{isTa ? 'அலகு விலை (₹)' : 'Unit Price (₹)'}</th>
                    <th className="px-4 py-3">{isTa ? 'மொத்தம் (₹)' : 'Line Total (₹)'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {costsWorksheet.entries?.map((entry, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-900">
                        <div>{entry.itemName[isTa ? 'ta' : 'en']}</div>
                        <span className="text-[10px] text-slate-400 capitalize">{entry.category}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 font-mono">
                        ₹{entry.benchmarkRatePerAcre}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          min="0"
                          step="0.5"
                          value={entry.userQuantity}
                          onChange={(e) => handleCostEntryChange(idx, 'userQuantity', parseFloat(e.target.value) || 0)}
                          className="w-20 text-xs border border-slate-300 rounded-lg px-2 py-1 bg-white font-mono"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          min="0"
                          step="10"
                          value={entry.userUnitPrice}
                          onChange={(e) => handleCostEntryChange(idx, 'userUnitPrice', parseFloat(e.target.value) || 0)}
                          className="w-24 text-xs border border-slate-300 rounded-lg px-2 py-1 bg-white font-mono"
                        />
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900 font-mono">
                        ₹{Math.round(entry.userQuantity * entry.userUnitPrice).toLocaleString('en-IN')}
                        {entry.isUserEdited && (
                          <span className="ml-1.5 text-[9px] text-amber-700 bg-amber-100 px-1 py-0.5 rounded">
                            CUSTOM
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* VALUE-ADDITION EXPLORATION BANNER */}
          <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-green-50 border border-emerald-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-1">
              <span className="font-bold text-emerald-950 flex items-center gap-1.5 text-sm">
                <Layers className="w-4 h-4 text-emerald-700" />
                {isTa ? 'மதிப்புக்கூட்டல் மூலம் கூடுதல் லாபம் ஈட்டுங்கள்' : 'Multiply Farm Value with Processed Products'}
              </span>
              <p className="text-emerald-800 text-[11px] leading-relaxed">
                {isTa
                  ? 'விளைச்சலில் தரம் குறைந்த அல்லது உபரி காய்கறிகளை பதப்படுத்தி ப்யூரி, எண்ணெய், மசாலாப் பொடிகளாக மாற்றி கூடுதல் லாபம் ஈட்டுங்கள் (TNAU SOP வழிகாட்டிகள் & லாபக் கணக்கீட்டாளர்).'
                  : 'Turn surplus or off-grade harvest into shelf-stable tomato puree, cold-pressed oil, or turmeric powder using verified TNAU recipes & costing calculators.'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate?.('value_addition')}
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl font-bold text-xs shrink-0 shadow-xs flex items-center gap-1.5"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>{isTa ? 'மதிப்புக்கூட்டல் மையம்' : 'Explore Value Addition'}</span>
            </button>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] text-slate-600">
            ℹ️ {costsWorksheet.disclaimer}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(7)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(9)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'விற்பனை திட்டமிடலுக்குச் செல்' : 'Proceed to Sale Plan'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 9: PLAN THE SALE */}
      {/* ==================================================================== */}
      {currentStep === 9 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                  9
                </span>
                <h2 className="text-xl font-bold text-slate-900">
                  {isTa ? 'படி 9: முதல் விற்பனையை திட்டமிடுதல்' : 'Step 9: Plan Your First Sale & Channels'}
                </h2>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isTa
                  ? 'உழவர் சந்தை, ஒழுங்குமுறை விற்பனைக்கூடம் மற்றும் நேரடி வாடிக்கையாளர் விற்பனை வாய்ப்புகள்.'
                  : 'Distinguish quoted modal prices from confirmed offers. Maximize farmer margins.'}
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
              <button
                type="button"
                onClick={() => onNavigate?.('marketplace')}
                className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-xs font-bold flex items-center gap-1.5 border border-emerald-200"
              >
                <ShoppingBag className="w-3.5 h-3.5" />
                <span>{isTa ? 'உழவர் நேரடி சந்தை' : 'Direct Marketplace'}</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigate?.('agri_entrepreneurship')}
                className="px-3 py-1.5 rounded-xl bg-teal-50 text-teal-800 hover:bg-teal-100 text-xs font-bold flex items-center gap-1.5 border border-teal-200"
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <span>{isTa ? 'தொழில்முனைவு மையம்' : 'Agri Entrepreneurship'}</span>
              </button>
            </div>
          </div>

          {/* SOURCED MANDI SNAPSHOT CARD */}
          <div className="border border-slate-200 rounded-2xl p-5 space-y-3 bg-gradient-to-br from-slate-900 to-slate-800 text-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4" />
                {isTa ? 'சந்தை நிலவரம் (Market Mandi Snapshot)' : 'Live Market Mandi Benchmark'}
              </span>
              <span className="text-[11px] text-slate-400">Modal Auction Rate</span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
              <div>
                <span className="text-xs text-slate-300 block">{mandiPriceData?.market || 'Salem Market Committee'}</span>
                <h3 className="text-xl font-bold text-white mt-0.5">
                  {mandiPriceData?.commodity || selectedCropId.toUpperCase()}
                </h3>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-2xl font-black text-emerald-400">
                  ₹{mandiPriceData?.modalPrice || 2400} / {isTa ? 'குவிண்டால்' : 'Quintal'}
                </span>
                <span className="text-xs text-slate-400 block">
                  (Approx. ₹{Math.round((mandiPriceData?.modalPrice || 2400) / 100)} / kg)
                </span>
              </div>
            </div>

            <div className="text-[11px] text-slate-400 border-t border-slate-700 pt-2 flex items-center justify-between">
              <span>⚠️ {salePlan.disclaimer}</span>
              <button
                type="button"
                onClick={() => onNavigate?.('market')}
                className="text-emerald-400 hover:underline flex items-center gap-1"
              >
                <span>{isTa ? 'அனைத்து சந்தைகள்' : 'View All Mandis'}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* CHANNELS COMPARISON */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-slate-200 rounded-2xl p-4 space-y-2 bg-emerald-50/50">
              <span className="text-xs font-bold text-emerald-950 uppercase flex items-center gap-1">
                🏪 {isTa ? 'உழவர் சந்தை (Zero Commission)' : 'Uzhavar Sandhai'}
              </span>
              <p className="text-xs text-slate-600 leading-relaxed">
                {isTa
                  ? 'இடைத்தரகர் இல்லாத நேரடி பண விற்பனை. எடை மேடை மற்றும் இலவச கடைகள் அரசு மூலம் வழங்கப்படுகிறது.'
                  : 'Direct-to-consumer cash sales with zero middleman fee. Daily morning demand.'}
              </p>
            </div>

            <div className="border border-slate-200 rounded-2xl p-4 space-y-2 bg-sky-50/50">
              <span className="text-xs font-bold text-sky-950 uppercase flex items-center gap-1">
                ⚖️ {isTa ? 'e-NAM ஒழுங்குமுறை விற்பனைக்கூடம்' : 'e-NAM Regulated Mandi'}
              </span>
              <p className="text-xs text-slate-600 leading-relaxed">
                {isTa
                  ? 'மின்னணு ஏலம் மூலம் வெளிப்படையான போட்டி விலை. எடை மேடை ரசீது மற்றும் வங்கி கணக்கில் உடனடி பணம்.'
                  : 'Electronic bidding across wholesale buyers. Proper weighment receipt and DBT payment.'}
              </p>
            </div>

            <div className="border border-slate-200 rounded-2xl p-4 space-y-2 bg-purple-50/50">
              <span className="text-xs font-bold text-purple-950 uppercase flex items-center gap-1">
                📱 {isTa ? 'அக்ரிபாரத் நேரடி வாடிக்கையாளர்' : 'Direct Consumer Orders'}
              </span>
              <p className="text-xs text-slate-600 leading-relaxed">
                {isTa
                  ? 'ஹோட்டல்கள், விடுதிகள் மற்றும் அப்பார்ட்மெண்ட்களுக்கு WhatsApp மூலம் மொத்தமாக முன்பதிவு செய்தல்.'
                  : 'List harvested batches in AgriBharat marketplace for nearby restaurants & groups.'}
              </p>
            </div>
          </div>

          {/* AGRI ENTREPRENEURSHIP & ENTERPRISE OPPORTUNITIES */}
          <div className="bg-gradient-to-r from-teal-900 to-emerald-900 text-white rounded-2xl p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-xs font-bold text-teal-300 uppercase tracking-wider block">
                  {isTa ? 'அடுத்த கட்ட வளர்ச்சி: உழவர் முதல் தொழில்முனைவர் வரை' : 'Next Step: From Harvest to Rural Enterprise'}
                </span>
                <h4 className="text-base font-bold text-white mt-0.5">
                  {isTa ? 'பண்ணை உபகரண வாடகை மையம் அல்லது சூரிய உலர்த்தி ஆலை' : 'Scale Up with Custom Hiring or Agro-Processing'}
                </h4>
                <p className="text-xs text-teal-100 mt-1 max-w-xl leading-relaxed">
                  {isTa
                    ? 'உங்கள் அறுவடைக்கு அப்பால் கிராமப்புற தொழில் வாய்ப்புகள், அரசு மானியங்கள் (PMFME, ACABC, AIF) மற்றும் 8-படி தொழில் திட்டமிடல் வழிகாட்டியை ஆராயுங்கள்.'
                    : 'Turn your farm experience into a year-round rural enterprise with capex equipment models, 35% PMFME subsidies, and TNAU incubation support.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigate?.('agri_entrepreneurship')}
                className="px-4 py-2 bg-white text-emerald-950 font-bold rounded-xl text-xs hover:bg-emerald-50 shrink-0 shadow-md flex items-center gap-1.5"
              >
                <span>{isTa ? 'தொழில் திட்டமிடல் மையம்' : 'Agri-Business Planner'}</span>
                <ArrowRight className="w-3.5 h-3.5 text-emerald-800" />
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => saveProgress(8)}
              className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-xl"
            >
              {isTa ? 'முந்தைய படி' : 'Previous Step'}
            </button>
            <button
              type="button"
              onClick={() => saveProgress(10)}
              className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs"
            >
              <span>{isTa ? 'பயணத்தை நிறைவு செய்க' : 'Proceed to Journey Completion'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 10: COMPLETE THE JOURNEY (RECONCILIATION & CERTIFICATE) */}
      {/* ==================================================================== */}
      {currentStep === 10 && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
                    10
                  </span>
                  <h2 className="text-xl font-bold text-slate-900">
                    {isTa ? 'படி 10: இறுதி அறுவடை கணக்கு & நிறைவு சான்றிதழ்' : 'Step 10: Harvest Reconciliation & Achievement Card'}
                  </h2>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  {isTa
                    ? 'அறுவடை அளவு, விற்பனை விலை மற்றும் நிகர லாப கணக்கீட்டை பூர்த்தி செய்து உங்கள் சான்றிதழைப் பெறுங்கள்.'
                    : 'Record final harvest yield, actual sale price, and compute net financial outcome.'}
                </p>
              </div>

              <button
                type="button"
                onClick={() => window.print()}
                className="px-3.5 py-2 rounded-xl bg-slate-900 text-white hover:bg-slate-800 text-xs font-bold flex items-center gap-1.5 self-start sm:self-auto shadow-xs"
              >
                <Printer className="w-4 h-4" />
                <span>{isTa ? 'சான்றிதழை அச்சிடுக' : 'Print / Save Certificate'}</span>
              </button>
            </div>

            {/* HARVEST RECONCILIATION FORM */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'அறுவடை தேதி' : 'Harvest Date'}
                </label>
                <input
                  type="date"
                  value={completionRecord.harvestDate}
                  onChange={(e) => handleCompletionChange('harvestDate', e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white font-medium"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'அறுவடை செய்யப்பட்ட மொத்த அளவு' : 'Total Harvested Quantity (kg/bags)'}
                </label>
                <input
                  type="number"
                  min="1"
                  step="10"
                  value={completionRecord.harvestedQuantity}
                  onChange={(e) => handleCompletionChange('harvestedQuantity', parseFloat(e.target.value) || 0)}
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'பெறப்பட்ட விற்பனை விலை (₹/அலகு)' : 'Achieved Selling Price (₹/unit)'}
                </label>
                <input
                  type="number"
                  min="1"
                  step="0.5"
                  value={completionRecord.achievedPricePerUnit}
                  onChange={(e) => handleCompletionChange('achievedPricePerUnit', parseFloat(e.target.value) || 0)}
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white font-mono"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'கொள்முதல் செய்தவர் அல்லது சந்தை மையம்' : 'Buyer Name or Channel'}
                </label>
                <input
                  type="text"
                  value={completionRecord.buyerNameOrChannel}
                  onChange={(e) => handleCompletionChange('buyerNameOrChannel', e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white"
                  placeholder="e.g. Salem Uzhavar Sandhai Stalls #14-15"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'முதல் தரம் (Grade A %)' : 'Grade A Share (%)'}
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={completionRecord.gradeBreakdown?.GradeA || 80}
                  onChange={(e) =>
                    setCompletionRecord({
                      ...completionRecord,
                      gradeBreakdown: { GradeA: parseFloat(e.target.value) || 0, GradeB: 100 - (parseFloat(e.target.value) || 0) },
                    })
                  }
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white font-mono"
                />
              </div>

              <div className="md:col-span-3">
                <label className="text-[11px] font-bold text-slate-600 block mb-1">
                  {isTa ? 'விவசாயியின் அனுபவ பகிர்வு & அடுத்த பருவ திட்டம்' : 'Farmer Reflections & Next Season Plan'}
                </label>
                <textarea
                  rows={2}
                  value={completionRecord.farmerReflection || ''}
                  onChange={(e) => handleCompletionChange('farmerReflection', e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-xl p-2.5 bg-white"
                />
              </div>
            </div>

            {/* FINANCIAL SUMMARY BOX */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[11px] text-slate-500 uppercase font-bold block">{isTa ? 'மொத்த வருமானம்' : 'Gross Revenue'}</span>
                <span className="text-xl font-bold text-slate-900 block mt-1 font-mono">
                  ₹{completionRecord.grossRevenue?.toLocaleString('en-IN') || 0}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[11px] text-slate-500 uppercase font-bold block">{isTa ? 'மொத்த செலவு' : 'Operating Cost'}</span>
                <span className="text-xl font-bold text-slate-900 block mt-1 font-mono">
                  ₹{costsWorksheet.totalOperatingCost?.toLocaleString('en-IN') || 0}
                </span>
              </div>

              <div className={`p-4 rounded-xl border ${
                completionRecord.netProfitOrLoss >= 0
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                  : 'bg-rose-50 border-rose-200 text-rose-950'
              }`}>
                <span className="text-[11px] uppercase font-bold block">
                  {completionRecord.netProfitOrLoss >= 0
                    ? isTa ? 'நிகர லாபம் (Net Profit)' : 'Net Profit'
                    : isTa ? 'நிகர நஷ்டம் (Net Loss)' : 'Net Loss'}
                </span>
                <span className="text-xl font-black block mt-1 font-mono">
                  ₹{Math.abs(completionRecord.netProfitOrLoss)?.toLocaleString('en-IN')}
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() =>
                  saveProgress(10, {
                    status: 'completed',
                    completionRecord: {
                      ...completionRecord,
                      completedAt: new Date().toISOString(),
                    },
                  })
                }
                className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-md"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{isTa ? 'பயணத்தை நிறைவு செய்து சேமி' : 'Finalize & Lock Journey'}</span>
              </button>
            </div>
          </div>

          {/* ================================================================ */}
          {/* PRINTABLE ACHIEVEMENT CERTIFICATE CARD */}
          {/* ================================================================ */}
          <div className="border-4 border-double border-emerald-800 rounded-3xl p-8 bg-gradient-to-br from-amber-50/70 via-white to-emerald-50/70 shadow-xl space-y-6 relative overflow-hidden print:m-0 print:border-2">
            <div className="text-center space-y-2">
              <div className="w-16 h-16 rounded-full bg-emerald-800 text-amber-300 flex items-center justify-center mx-auto shadow-md">
                <Award className="w-8 h-8" />
              </div>
              <span className="text-xs font-bold text-emerald-900 tracking-widest uppercase block">
                AgriBharat • Special Operation
              </span>
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-slate-900">
                {isTa
                  ? 'தொடக்க விவசாயி சாதனைச் சான்றிதழ்'
                  : 'First Step to First Sale Achievement Card'}
              </h2>
              <p className="text-xs text-slate-600 max-w-lg mx-auto">
                {isTa
                  ? 'விதைப்பு முதல் அறுவடை விற்பனை வரை 10 படி செயல்முறை வழிகாட்டலை வெற்றிகரமாக முடித்தமைக்காக வழங்கப்படுகிறது.'
                  : 'Awarded for successfully executing verified agronomy from land preparation to first marketplace sale.'}
              </p>
            </div>

            <div className="border-y border-emerald-700/30 py-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <span className="text-[11px] text-slate-500 uppercase block">{isTa ? 'விவசாயி பெயர்' : 'Farmer Name'}</span>
                <strong className="text-sm text-slate-900 block mt-0.5">
                  {user?.fullName || user?.name || 'Thiru. Selvakumar R.'}
                </strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase block">{isTa ? 'மாவட்டம்' : 'District'}</span>
                <strong className="text-sm text-slate-900 block mt-0.5">{profile.district}</strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase block">{isTa ? 'பயிர்' : 'Crop Cultivated'}</span>
                <strong className="text-sm text-emerald-800 block mt-0.5">
                  {cropGuide?.cropName?.[isTa ? 'ta' : 'en'] || selectedCropId.toUpperCase()}
                </strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase block">{isTa ? 'அறுவடை அளவு' : 'Total Yield'}</span>
                <strong className="text-sm text-slate-900 block mt-0.5">
                  {completionRecord.harvestedQuantity} {completionRecord.harvestUnit}
                </strong>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 pt-2 gap-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-700" />
                <span>Verified by TNAU & TRRI Institutional Blueprints</span>
              </div>

              <div className="text-center sm:text-right text-[11px]">
                <span>Completed on: {new Date().toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

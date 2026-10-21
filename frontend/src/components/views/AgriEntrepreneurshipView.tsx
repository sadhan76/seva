import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  TrendingUp,
  Sparkles,
  Calculator,
  Building2,
  FileText,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Plus,
  Trash2,
  RefreshCw,
  Phone,
  Mail,
  ShieldCheck,
  Check,
  ArrowRight,
  Compass,
  Bookmark
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  matchBusinessIdeas,
  calculateBusinessPlan,
  createFarmerBusinessPlan,
  getFarmerBusinessPlans,
  deleteFarmerBusinessPlan,
  getDistrictsApi,
} from '../../services/api';
import type {
  BusinessIdeaItem,
  BusinessIdeaMatchRequest,
  BusinessPlanWizardData,
  BusinessPlanCalculationResult,
  BusinessPlanModel,
  NavTab
} from '../../types';

interface AgriEntrepreneurshipViewProps {
  onNavigate?: (tab: NavTab) => void;
  initialProduceFilter?: string;
}

export const AgriEntrepreneurshipView: React.FC<AgriEntrepreneurshipViewProps> = ({
  onNavigate: _onNavigate,
  initialProduceFilter
}) => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const isTa = language === 'ta';
  const isFarmer = user?.role === 'farmer';

  // Navigation sub-tabs
  const [activeTab, setActiveTab] = useState<'match' | 'wizard' | 'saved'>('match');

  // Matcher State
  const [interests, setInterests] = useState<string[]>([
    'value_addition',
    'solar_drying',
    'organic_inputs'
  ]);
  const [skills, setSkills] = useState<string[]>([
    'farming_experience',
    'packaging'
  ]);
  const [district, setDistrict] = useState<string>(user?.district || '');
  const [budget, setBudget] = useState<number>(150000);
  const [selectedProduce, setSelectedProduce] = useState<string[]>(
    initialProduceFilter ? [initialProduceFilter] : ['Tomato', 'Groundnut']
  );
  const [space, setSpace] = useState<string>('shed_200sqft');

  const [matchedIdeas, setMatchedIdeas] = useState<BusinessIdeaItem[]>([]);
  const [isMatching, setIsMatching] = useState<boolean>(false);
  const [matchDisclaimer, setMatchDisclaimer] = useState<string>('');
  const [selectedIdeaForModal, setSelectedIdeaForModal] = useState<BusinessIdeaItem | null>(null);

  // Saved Plans State
  const [savedPlans, setSavedPlans] = useState<BusinessPlanModel[]>([]);
  const [isLoadingPlans, setIsLoadingPlans] = useState<boolean>(false);

  // Wizard State
  const [wizardStep, setWizardStep] = useState<number>(1);
  const [planBusinessName, setPlanBusinessName] = useState<string>(
    user?.district ? `${user.district} Bio-Inputs Lab` : 'Bio-Inputs Enterprise'
  );
  const [selectedIdeaId, setSelectedIdeaId] = useState<string>('bio_inputs_lab');
  const [dynamicDistricts, setDynamicDistricts] = useState<string[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function loadDistricts() {
      const stateToQuery = user?.state || 'Tamil Nadu';
      const dList = await getDistrictsApi(stateToQuery);
      if (isMounted) {
        const names = dList.map((d) => d.name);
        if (user?.district && !names.includes(user.district)) {
          names.unshift(user.district);
        }
        setDynamicDistricts(names);
        if (!district && names.length > 0) {
          setDistrict(user?.district || names[0]);
        }
      }
    }
    loadDistricts();
    return () => {
      isMounted = false;
    };
  }, [user?.state, user?.district]);

  const [equipmentList, setEquipmentList] = useState<Array<{ name: string; quantity: number; unitCost: number }>>([
    { name: 'Autoclave & Laminar Airflow (Mini)', quantity: 1, unitCost: 65000 },
    { name: 'HDPE Fermentation Drums (10 x 200L)', quantity: 1, unitCost: 18000 },
    { name: 'Shade Net Shed (300 sq.ft)', quantity: 1, unitCost: 35000 }
  ]);

  const [rawMaterialsList, setRawMaterialsList] = useState<Array<{ name: string; monthlyQuantity: number; unitCost: number }>>([
    { name: 'Mother Culture Media & Agar', monthlyQuantity: 5, unitCost: 1200 },
    { name: 'Cow Dung & Local Organic Residues', monthlyQuantity: 1000, unitCost: 12 }
  ]);

  const [operatingCosts, setOperatingCosts] = useState<Record<string, number>>({
    labour: 12000,
    electricity: 3500,
    packaging: 6000,
    logistics: 3000,
    marketing: 2000,
    maintenance: 1500
  });

  const [pricingStrategy, setPricingStrategy] = useState<{
    productUnit: string;
    unitProductionCost: number;
    targetSellingPrice: number;
    expectedMonthlySalesUnits: number;
  }>({
    productUnit: '1 Litre Bottle',
    unitProductionCost: 45,
    targetSellingPrice: 95,
    expectedMonthlySalesUnits: 600
  });

  const [distributionChannels, setDistributionChannels] = useState<string[]>([
    'Direct to Local Farmers',
    'Uzhavar Sandhai Stalls',
    'AgriBharat Marketplace'
  ]);

  const [customerSegments, setCustomerSegments] = useState<string[]>([
    'Organic Farmers within 25 km',
    'Local Horticulture Nurseries'
  ]);

  const [regulatoryChecklist, setRegulatoryChecklist] = useState<Record<string, boolean>>({
    udyam: true,
    fssai: false,
    bankCurrentAccount: true,
    fcoLicense: false
  });

  const [liveCalculations, setLiveCalculations] = useState<BusinessPlanCalculationResult | null>(null);
  const [isSavingPlan, setIsSavingPlan] = useState<boolean>(false);
  const [planSaveSuccess, setPlanSaveSuccess] = useState<boolean>(false);

  // Available options
  const interestOptions = [
    { id: 'organic_inputs', en: 'Organic Bio-Inputs & Vermicompost', ta: 'இயற்கை உரம் & மண்புழு உரம்' },
    { id: 'value_addition', en: 'Food Processing & Value Addition', ta: 'மதிப்புக் கூட்டப்பட்ட உணவுப் பொருட்கள்' },
    { id: 'solar_drying', en: 'Solar Dehydration & Drying', ta: 'சூரிய கூடார உலர்த்தி தொழில்' },
    { id: 'machinery_rental', en: 'Custom Hiring & Machinery Rental', ta: 'பண்ணை இயந்திரங்கள் வாடகை மையம்' },
    { id: 'cattle_feed', en: 'Cattle Feed & Mineral Mixture Mill', ta: 'மாட்டுத் தீவனம் & தாது உப்பு தயாரிப்பு' },
    { id: 'nursery', en: 'Hi-Tech Seedling & Shade Net Nursery', ta: 'நிழல்வலை நாற்றங்கால் தொழில்' }
  ];

  const skillOptions = [
    { id: 'farming_experience', en: 'Practical Farming Experience', ta: 'விவசாய கள அனுபவம்' },
    { id: 'technical_operations', en: 'Machinery & Technical Handling', ta: 'இயந்திரங்கள் இயக்கும் திறன்' },
    { id: 'packaging', en: 'Hygienic Packaging & Sorting', ta: 'சுகாதார பேக்கிங் மற்றும் தரம் பிரித்தல்' },
    { id: 'marketing_sales', en: 'Local Sales & Market Connect', ta: 'சந்தைப்படுத்தல் மற்றும் விற்பனை' },
    { id: 'mechanical', en: 'Tractor / Motor Maintenance', ta: 'இயந்திர பழுது நீக்கும் பயிற்சி' }
  ];

  const produceOptions = [
    'Tomato', 'Groundnut', 'Paddy', 'Tapioca', 'Turmeric', 'Millets', 'Banana', 'Coconut', 'Chillies', 'Dairy / Cow Dung'
  ];

  const districtList = dynamicDistricts.length > 0
    ? dynamicDistricts
    : ['Thanjavur', 'Salem', 'Coimbatore', 'Erode', 'Madurai', 'Dindigul', 'Tiruppur', 'Dharmapuri', 'Villupuram', 'Tirunelveli'];

  // Perform live matching
  const handleRunMatch = async () => {
    setIsMatching(true);
    try {
      const req: BusinessIdeaMatchRequest = {
        interests,
        skills,
        locationDistrict: district,
        investmentBudget: budget,
        availableProduce: selectedProduce,
        landOrSpaceAvailable: space
      };
      const res = await matchBusinessIdeas(req);
      setMatchedIdeas(res.matchedIdeas || []);
      setMatchDisclaimer(res.disclaimer || '');
    } catch (err) {
      console.error('Failed to match business ideas:', err);
    } finally {
      setIsMatching(false);
    }
  };

  useEffect(() => {
    handleRunMatch();
  }, [district]);

  // Load saved plans if farmer
  const loadSavedPlans = async () => {
    if (!token || !isFarmer) return;
    setIsLoadingPlans(true);
    try {
      const res = await getFarmerBusinessPlans(token);
      setSavedPlans(res.items || []);
    } catch (err) {
      console.error('Failed to load saved plans:', err);
    } finally {
      setIsLoadingPlans(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'saved') {
      loadSavedPlans();
    }
  }, [activeTab]);

  // Calculate live wizard finances
  useEffect(() => {
    const runCalc = async () => {
      try {
        const res = await calculateBusinessPlan({
          equipmentAndInfrastructure: equipmentList,
          rawMaterialInputs: rawMaterialsList,
          operatingCosts,
          pricingStrategy
        });
        setLiveCalculations(res);
      } catch (err) {
        console.error('Calculation error:', err);
      }
    };
    runCalc();
  }, [equipmentList, rawMaterialsList, operatingCosts, pricingStrategy]);

  // Adopt idea into wizard
  const handleAdoptIdea = (idea: BusinessIdeaItem) => {
    setSelectedIdeaId(idea.ideaId);
    setPlanBusinessName(`${district} ${idea.title.en}`);
    
    // Convert estimated capex to equipment items
    const newEquip = Object.entries(idea.estimatedStartupCapex).map(([k, v]) => ({
      name: k,
      quantity: 1,
      unitCost: v
    }));
    setEquipmentList(newEquip);

    // Convert estimated opex
    const newOpex: Record<string, number> = {};
    Object.entries(idea.estimatedMonthlyOpex).forEach(([k, v]) => {
      const cleanKey = k.toLowerCase().includes('labour') ? 'labour' :
                       k.toLowerCase().includes('electricity') ? 'electricity' :
                       k.toLowerCase().includes('pack') ? 'packaging' :
                       k.toLowerCase().includes('deliv') ? 'logistics' : 'maintenance';
      newOpex[cleanKey] = (newOpex[cleanKey] || 0) + v;
    });
    setOperatingCosts(newOpex);

    setActiveTab('wizard');
    setWizardStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Save wizard plan
  const handleSavePlan = async () => {
    if (!token) {
      alert(isTa ? 'திட்டத்தை சேமிக்க உள்நுழையவும்.' : 'Please sign in as a farmer to save your business plan.');
      return;
    }
    setIsSavingPlan(true);
    setPlanSaveSuccess(false);
    try {
      const wizardData: BusinessPlanWizardData = {
        productOrService: planBusinessName,
        customerSegment: customerSegments,
        equipmentAndInfrastructure: equipmentList,
        rawMaterialInputs: rawMaterialsList,
        operatingCosts,
        pricingStrategy,
        distributionChannels,
        risksAndMitigations: [
          { risk: 'Raw material price surge', mitigation: 'Long-term forward contracts with local farmers' }
        ],
        regulatoryChecklist,
        nextStepsRoadmap: [
          { stepNumber: 1, title: 'Obtain Udyam MSME Registration Certificate', timeline: 'Week 1', resourceLink: 'https://udyamregistration.gov.in/' },
          { stepNumber: 2, title: 'Apply for FSSAI / FCO Trade License', timeline: 'Week 2', resourceLink: 'https://foscos.fssai.gov.in/' },
          { stepNumber: 3, title: 'Submit DPR to Bank under PMFME / AIF Subsidy Scheme', timeline: 'Month 1', resourceLink: 'https://pmfme.mofpi.gov.in/' }
        ]
      };

      await createFarmerBusinessPlan({
        businessName: planBusinessName,
        ideaId: selectedIdeaId,
        wizardData
      }, token);

      setPlanSaveSuccess(true);
      setTimeout(() => {
        setPlanSaveSuccess(false);
        setActiveTab('saved');
      }, 1500);
    } catch (err) {
      console.error('Failed to save business plan:', err);
      alert(isTa ? 'திட்டத்தை சேமிக்க முடியவில்லை.' : 'Failed to save business plan.');
    } finally {
      setIsSavingPlan(false);
    }
  };

  const handleDeletePlan = async (planId: string) => {
    if (!token || !window.confirm(isTa ? 'இந்த திட்டத்தை நிச்சயமாக நீக்க விரும்புகிறீர்களா?' : 'Are you sure you want to delete this business plan?')) return;
    try {
      await deleteFarmerBusinessPlan(planId, token);
      loadSavedPlans();
    } catch (err) {
      console.error('Failed to delete plan:', err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner Header */}
      <div className="rounded-3xl bg-linear-to-r from-emerald-900 via-emerald-850 to-teal-900 text-white p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-200 text-xs font-bold border border-emerald-400/30">
            <Sparkles className="w-3.5 h-3.5 text-emerald-300" />
            <span>{isTa ? 'வேளாண் தொழில்முனைவோர் வழிகாட்டி' : 'Agri-Entrepreneurship Development Hub'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            {isTa ? 'விவசாயத்திலிருந்து வேளாண் தொழில்முனைவோராக மாறுங்கள்' : 'From Farm Producer to Agri-Business Owner'}
          </h1>
          <p className="text-emerald-100 text-xs sm:text-sm leading-relaxed">
            {isTa
              ? 'உங்கள் நிலம், மூலப்பொருட்கள், முதலீடு மற்றும் திறனுக்கு ஏற்ற தொழில்களை கண்டறிந்து, செலவு கணக்கீடுகள், இயந்திரங்கள் மற்றும் அரசு ஆதரவுடன் வணிகத் திட்டத்தை உருவாக்குங்கள்.'
              : 'Discover viable rural enterprises matched to your budget, farm produce, and skills. Build comprehensive 8-step business plans with verified capex/opex benchmarks, FSSAI compliance, and official incubation support.'}
          </p>

          {/* Institutional Integrity Alert */}
          <div className="pt-2">
            <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-700/50 text-[11px] text-emerald-200 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong>{isTa ? 'அதிகாரப்பூர்வ நிறுவன தரவுகள்:' : 'Official Institutional Benchmarks:'} </strong>
                {isTa
                  ? 'திட்டங்கள் TNAU DABD, EDII-TN, மற்றும் ACABC வழிகாட்டுதல்களை அடிப்படையாகக் கொண்டவை. அரசு கடன் மற்றும் மானியங்கள் தகுதிக்கு உட்பட்டவை; லாபம் உறுதி செய்யப்படவில்லை.'
                  : 'Blueprints cite TNAU Directorate of Agri-Business Development (DABD), EDII-TN, and ACABC standards. Loan sanction and subsidy eligibility are subject to official guidelines; profit is never guaranteed.'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('match')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'match'
              ? 'bg-emerald-700 text-white shadow-md'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>{isTa ? '1. தொழில் வாய்ப்பு பொருத்தம்' : '1. Idea Matcher'}</span>
        </button>

        <button
          onClick={() => setActiveTab('wizard')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'wizard'
              ? 'bg-emerald-700 text-white shadow-md'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Calculator className="w-4 h-4" />
          <span>{isTa ? '2. தொழில் திட்ட வழிகாட்டி (8 படிகள்)' : '2. Business Planning Wizard'}</span>
        </button>

        {isFarmer && (
          <button
            onClick={() => setActiveTab('saved')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'saved'
                ? 'bg-emerald-700 text-white shadow-md'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <Bookmark className="w-4 h-4" />
            <span>{isTa ? 'என் வணிகத் திட்டங்கள்' : 'My Business Plans'} ({savedPlans.length})</span>
          </button>
        )}
      </div>

      {/* TAB 1: BUSINESS IDEA MATCHER */}
      {activeTab === 'match' && (
        <div className="space-y-6">
          {/* Filter / Inputs Form Card */}
          <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200 shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-emerald-700" />
                <span>{isTa ? 'உங்கள் பண்ணை விபரங்களை குறிப்பிடவும்' : 'Enter Your Farm & Enterprise Preferences'}</span>
              </h2>
              <button
                onClick={handleRunMatch}
                disabled={isMatching}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-200 transition-all"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isMatching ? 'animate-spin' : ''}`} />
                <span>{isTa ? 'பொருத்தங்களை புதுப்பி' : 'Refresh Matches'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* District & Location */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  {isTa ? 'மாவட்டம் (District)' : 'Location District'}
                </label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
                >
                  {districtList.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-500 mt-1">
                  {isTa ? 'மாவட்ட விவசாயக் கொத்துகளுக்கு முன்னுரிமை அளிக்கப்படும்.' : 'Matches regional industrial and crop clusters.'}
                </p>
              </div>

              {/* Investment Budget */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    {isTa ? 'தொடக்க முதலீடு (Budget)' : 'Available Budget'}
                  </label>
                  <span className="text-xs font-black text-emerald-800 font-mono">
                    ₹{budget.toLocaleString('en-IN')}
                  </span>
                </div>
                <input
                  type="range"
                  min="30000"
                  max="1000000"
                  step="10000"
                  value={budget}
                  onChange={(e) => setBudget(parseFloat(e.target.value))}
                  className="w-full accent-emerald-700"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                  <span>₹30K (Micro)</span>
                  <span>₹2.5L</span>
                  <span>₹10L+ (Commercial)</span>
                </div>
              </div>

              {/* Space Available */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  {isTa ? 'கிடைக்கும் இடம் (Available Space)' : 'Available Infrastructure'}
                </label>
                <select
                  value={space}
                  onChange={(e) => setSpace(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
                >
                  <option value="shed_200sqft">Tiled / Metal Shed (200 - 500 sq.ft)</option>
                  <option value="open_land_1acre">Open Farm Land (0.5 to 2 Acres)</option>
                  <option value="backyard">Farm House Backyard (100 sq.ft)</option>
                  <option value="village_rental">Rented Village Commercial Space</option>
                </select>
              </div>
            </div>

            {/* Produce Synergies Pills */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700">
                {isTa ? 'உங்களிடம் உள்ள விளைபொருட்கள் / மூலப்பொருட்கள்' : 'Available Farm Produce / Raw Materials'}
              </label>
              <div className="flex flex-wrap gap-2">
                {produceOptions.map((prod) => {
                  const isSelected = selectedProduce.includes(prod);
                  return (
                    <button
                      key={prod}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setSelectedProduce(selectedProduce.filter((p) => p !== prod));
                        } else {
                          setSelectedProduce([...selectedProduce, prod]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        isSelected
                          ? 'bg-emerald-700 text-white shadow-2xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {prod} {isSelected ? '✓' : '+'}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Interest Areas Pills */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700">
                {isTa ? 'உங்கள் விருப்பப் பிரிவுகள்' : 'Enterprise Interest Areas'}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {interestOptions.map((opt) => {
                  const isSelected = interests.includes(opt.id);
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setInterests(interests.filter((i) => i !== opt.id));
                        } else {
                          setInterests([...interests, opt.id]);
                        }
                      }}
                      className={`p-2.5 rounded-xl text-left border text-xs font-semibold transition-all flex items-start gap-2 ${
                        isSelected
                          ? 'bg-emerald-50 border-emerald-500 text-emerald-950 font-bold'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <div className={`w-4 h-4 rounded-sm mt-0.5 shrink-0 flex items-center justify-center text-[10px] ${
                        isSelected ? 'bg-emerald-700 text-white' : 'border border-slate-300'
                      }`}>
                        {isSelected ? '✓' : ''}
                      </div>
                      <div>
                        <div>{isTa ? opt.ta : opt.en}</div>
                        <div className="text-[10px] text-slate-500 font-normal">{isTa ? opt.en : opt.ta}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Skills Pills */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700">
                {isTa ? 'உங்களிடம் உள்ள திறன்கள்' : 'Skills & Operational Capabilities'}
              </label>
              <div className="flex flex-wrap gap-2">
                {skillOptions.map((sk) => {
                  const isSelected = skills.includes(sk.id);
                  return (
                    <button
                      key={sk.id}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setSkills(skills.filter((s) => s !== sk.id));
                        } else {
                          setSkills([...skills, sk.id]);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        isSelected
                          ? 'bg-teal-700 text-white font-bold'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {isTa ? sk.ta : sk.en}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Matched Ideas Grid */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-black text-slate-900">
                  {isTa ? 'பரிந்துரைக்கப்பட்ட வணிக யோசனைகள்' : 'Matched Enterprise Opportunities'} ({matchedIdeas.length})
                </h3>
                <p className="text-xs text-slate-500">
                  {isTa ? 'உங்கள் முதலீடு மற்றும் மூலப்பொருட்களுக்கு அதிக பொருத்தம் கொண்ட தொழில்கள்.' : 'Ranked by suitability score against your budget, inputs, and regional clusters.'}
                </p>
              </div>
            </div>

            {matchDisclaimer && (
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs">
                ⚠️ {matchDisclaimer}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {matchedIdeas.map((idea) => {
                const totalCapex = Object.values(idea.estimatedStartupCapex).reduce((a, b) => a + b, 0);
                const totalOpex = Object.values(idea.estimatedMonthlyOpex).reduce((a, b) => a + b, 0);

                return (
                  <div
                    key={idea.ideaId}
                    className="bg-white rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
                  >
                    <div className="p-5 space-y-4">
                      {/* Top Badges */}
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                          <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
                          <span>{idea.matchScore}% {isTa ? 'பொருத்தம்' : 'Match Score'}</span>
                        </span>
                        <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                          {idea.category}
                        </span>
                      </div>

                      {/* Title & Description */}
                      <div>
                        <h4 className="text-base font-extrabold text-slate-900 leading-snug">
                          {isTa ? idea.title.ta : idea.title.en}
                        </h4>
                        <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                          {isTa ? idea.suitabilitySummary.ta : idea.suitabilitySummary.en}
                        </p>
                      </div>

                      {/* Match Reasons */}
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                        <div className="text-[11px] font-bold text-slate-700">{isTa ? 'ஏன் இந்த தொழில் சிறந்தது:' : 'Match Rationales:'}</div>
                        <ul className="space-y-1">
                          {idea.matchReasons.map((r, i) => (
                            <li key={i} className="text-xs text-emerald-900 flex items-start gap-1.5">
                              <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                              <span>{isTa ? r.ta : r.en}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Capex / Opex Snapshot */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-100">
                          <div className="text-[10px] font-bold text-emerald-800 uppercase">{isTa ? 'தொடக்க முதலீடு (Capex)' : 'Startup Capex'}</div>
                          <div className="text-base font-black text-emerald-950 font-mono mt-0.5">
                            ₹{totalCapex.toLocaleString('en-IN')}
                          </div>
                          <div className="text-[10px] text-emerald-700 mt-0.5">
                            {Object.keys(idea.estimatedStartupCapex).length} {isTa ? 'இயந்திரங்கள் / கூடம்' : 'equipment items'}
                          </div>
                        </div>

                        <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-100">
                          <div className="text-[10px] font-bold text-teal-800 uppercase">{isTa ? 'மாத செலவு (Opex)' : 'Monthly Opex'}</div>
                          <div className="text-base font-black text-teal-950 font-mono mt-0.5">
                            ₹{totalOpex.toLocaleString('en-IN')}
                          </div>
                          <div className="text-[10px] text-teal-700 mt-0.5">
                            {isTa ? 'முதலீடு திரும்ப:' : 'Breakeven:'} {idea.typicalBreakevenMonths}
                          </div>
                        </div>
                      </div>

                      {/* Target Customers */}
                      <div className="space-y-1 text-xs text-slate-600">
                        <div className="font-bold text-slate-700">{isTa ? 'வாடிக்கையாளர்கள்:' : 'Target Customers:'}</div>
                        <div className="flex flex-wrap gap-1.5">
                          {idea.targetCustomers.map((c, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px]">
                              {isTa ? c.ta : c.en}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Card Footer Actions */}
                    <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-3">
                      <button
                        onClick={() => setSelectedIdeaForModal(idea)}
                        className="text-xs font-bold text-slate-700 hover:text-emerald-800 hover:underline flex items-center gap-1"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>{isTa ? 'முழு விபரம் & மானியங்கள்' : 'View Full Details'}</span>
                      </button>

                      <button
                        onClick={() => handleAdoptIdea(idea)}
                        className="px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-xs transition-all flex items-center gap-1.5"
                      >
                        <span>{isTa ? 'திட்டம் உருவாக்கவும்' : 'Build Plan'}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: 8-STEP BUSINESS PLANNING WIZARD */}
      {activeTab === 'wizard' && (
        <div className="space-y-6">
          {/* Wizard Progress Stepper */}
          <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between overflow-x-auto pb-2 gap-2">
              {[
                { step: 1, title: isTa ? '1. தொழில் விபரம்' : '1. Concept' },
                { step: 2, title: isTa ? '2. வாடிக்கையாளர்' : '2. Customers' },
                { step: 3, title: isTa ? '3. இயந்திரங்கள்' : '3. Equipment (Capex)' },
                { step: 4, title: isTa ? '4. மூலப்பொருள்' : '4. Raw Materials' },
                { step: 5, title: isTa ? '5. மாதச் செலவு' : '5. Monthly Opex' },
                { step: 6, title: isTa ? '6. விலை & வரவு' : '6. Pricing & Sales' },
                { step: 7, title: isTa ? '7. சந்தை வழி' : '7. Channels' },
                { step: 8, title: isTa ? '8. சட்டம் & சேமி' : '8. Statutory & Save' }
              ].map((s) => (
                <button
                  key={s.step}
                  onClick={() => setWizardStep(s.step)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                    wizardStep === s.step
                      ? 'bg-emerald-700 text-white shadow-2xs'
                      : wizardStep > s.step
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  <span>{s.title}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Step Content */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-5">
                {/* STEP 1: CONCEPT */}
                {wizardStep === 1 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 1: உங்கள் வேளாண் தொழிலின் பெயர் மற்றும் நோக்கம்' : 'Step 1: Enterprise Name & Concept'}
                    </h3>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        {isTa ? 'தொழில் / நிறுவனத்தின் பெயர்' : 'Enterprise / Business Name'}
                      </label>
                      <input
                        type="text"
                        value={planBusinessName}
                        onChange={(e) => setPlanBusinessName(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-800"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        {isTa ? 'அடிப்படை தொழில் யோசனை' : 'Selected Business Model Template'}
                      </label>
                      <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-950 font-semibold">
                        Template ID: {selectedIdeaId} • District: {district}
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 2: CUSTOMER SEGMENTS */}
                {wizardStep === 2 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 2: இலக்கு வாடிக்கையாளர்கள் (Customer Segments)' : 'Step 2: Target Customer Segments'}
                    </h3>
                    <p className="text-xs text-slate-600">
                      {isTa ? 'உங்கள் தயாரிப்பு அல்லது சேவையை யாரிடம் விற்கப் போகிறீர்கள்?' : 'Select all customer channels that you will serve:'}
                    </p>
                    <div className="space-y-2">
                      {[
                        'Organic & Progressive Farmers within 25 km',
                        'Local Farmer Producer Companies (FPOs)',
                        'Urban Direct Consumers via Weekly Sandhai',
                        'Bakeries, Snack & Food Processing Outlets',
                        'Hostels, Hospitals & Canteens'
                      ].map((seg) => {
                        const isChecked = customerSegments.includes(seg);
                        return (
                          <label key={seg} className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 text-xs font-semibold text-slate-800">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) setCustomerSegments([...customerSegments, seg]);
                                else setCustomerSegments(customerSegments.filter((s) => s !== seg));
                              }}
                              className="rounded-sm text-emerald-700"
                            />
                            <span>{seg}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* STEP 3: EQUIPMENT & INFRASTRUCTURE */}
                {wizardStep === 3 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                      <h3 className="text-base font-extrabold text-slate-900">
                        {isTa ? 'படி 3: உபகரணங்கள் மற்றும் தொடக்க முதலீடு (Capex)' : 'Step 3: Equipment & Infrastructure (Capex)'}
                      </h3>
                      <button
                        type="button"
                        onClick={() => setEquipmentList([...equipmentList, { name: 'New Machine / Tool', quantity: 1, unitCost: 10000 }])}
                        className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-xs font-bold flex items-center gap-1 border border-emerald-200"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>{isTa ? 'சேர்' : 'Add Item'}</span>
                      </button>
                    </div>

                    <div className="space-y-2">
                      {equipmentList.map((eq, i) => (
                        <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-12 gap-2 items-center text-xs">
                          <div className="col-span-6">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'இயந்திரம் / சாதனம்' : 'Equipment Name'}</label>
                            <input
                              type="text"
                              value={eq.name}
                              onChange={(e) => {
                                const copy = [...equipmentList];
                                copy[i].name = e.target.value;
                                setEquipmentList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold"
                            />
                          </div>
                          <div className="col-span-2">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'எண்ணிக்கை' : 'Qty'}</label>
                            <input
                              type="number"
                              min="1"
                              value={eq.quantity}
                              onChange={(e) => {
                                const copy = [...equipmentList];
                                copy[i].quantity = parseFloat(e.target.value) || 1;
                                setEquipmentList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-center"
                            />
                          </div>
                          <div className="col-span-3">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'விலை (₹)' : 'Rate (₹)'}</label>
                            <input
                              type="number"
                              min="0"
                              value={eq.unitCost}
                              onChange={(e) => {
                                const copy = [...equipmentList];
                                copy[i].unitCost = parseFloat(e.target.value) || 0;
                                setEquipmentList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg font-mono font-bold"
                            />
                          </div>
                          <div className="col-span-1 text-right pt-4">
                            <button
                              type="button"
                              onClick={() => setEquipmentList(equipmentList.filter((_, idx) => idx !== i))}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* STEP 4: RAW MATERIALS */}
                {wizardStep === 4 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                      <h3 className="text-base font-extrabold text-slate-900">
                        {isTa ? 'படி 4: மாதாந்திர மூலப்பொருட்கள் தேவை' : 'Step 4: Monthly Raw Material Inputs'}
                      </h3>
                      <button
                        type="button"
                        onClick={() => setRawMaterialsList([...rawMaterialsList, { name: 'Additional Ingredient', monthlyQuantity: 100, unitCost: 15 }])}
                        className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-xs font-bold flex items-center gap-1 border border-emerald-200"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>{isTa ? 'சேர்' : 'Add Input'}</span>
                      </button>
                    </div>

                    <div className="space-y-2">
                      {rawMaterialsList.map((rm, i) => (
                        <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-12 gap-2 items-center text-xs">
                          <div className="col-span-5">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'மூலப்பொருள்' : 'Raw Input Item'}</label>
                            <input
                              type="text"
                              value={rm.name}
                              onChange={(e) => {
                                const copy = [...rawMaterialsList];
                                copy[i].name = e.target.value;
                                setRawMaterialsList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold"
                            />
                          </div>
                          <div className="col-span-3">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'மாத அளவு (kg/L)' : 'Monthly Qty'}</label>
                            <input
                              type="number"
                              min="1"
                              value={rm.monthlyQuantity}
                              onChange={(e) => {
                                const copy = [...rawMaterialsList];
                                copy[i].monthlyQuantity = parseFloat(e.target.value) || 0;
                                setRawMaterialsList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-center"
                            />
                          </div>
                          <div className="col-span-3">
                            <label className="text-[10px] text-slate-500 font-bold block mb-0.5">{isTa ? 'விலை/அலகு (₹)' : 'Rate / Unit (₹)'}</label>
                            <input
                              type="number"
                              min="0"
                              value={rm.unitCost}
                              onChange={(e) => {
                                const copy = [...rawMaterialsList];
                                copy[i].unitCost = parseFloat(e.target.value) || 0;
                                setRawMaterialsList(copy);
                              }}
                              className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-lg font-mono font-bold"
                            />
                          </div>
                          <div className="col-span-1 text-right pt-4">
                            <button
                              type="button"
                              onClick={() => setRawMaterialsList(rawMaterialsList.filter((_, idx) => idx !== i))}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* STEP 5: OPERATING COSTS */}
                {wizardStep === 5 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 5: மாதாந்திர இயக்கச் செலவுகள் (Monthly Opex)' : 'Step 5: Monthly Operating Costs (Opex)'}
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      {Object.entries(operatingCosts).map(([k, v]) => (
                        <div key={k} className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                          <label className="text-[11px] font-bold text-slate-700 uppercase block mb-1">
                            {k} (₹ / month)
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={v}
                            onChange={(e) => {
                              setOperatingCosts({
                                ...operatingCosts,
                                [k]: parseFloat(e.target.value) || 0
                              });
                            }}
                            className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-mono font-bold text-slate-800"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* STEP 6: PRICING & PROJECTIONS */}
                {wizardStep === 6 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 6: விலை நிர்ணயம் & விற்பனை திட்டம்' : 'Step 6: Pricing & Unit Economics'}
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          {isTa ? 'விற்பனை அலகு (Unit)' : 'Product Unit Package'}
                        </label>
                        <input
                          type="text"
                          value={pricingStrategy.productUnit}
                          onChange={(e) => setPricingStrategy({ ...pricingStrategy, productUnit: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                        />
                      </div>

                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          {isTa ? 'விற்பனை விலை (₹ / அலகு)' : 'Target Selling Price (₹ / unit)'}
                        </label>
                        <input
                          type="number"
                          min="1"
                          value={pricingStrategy.targetSellingPrice}
                          onChange={(e) => setPricingStrategy({ ...pricingStrategy, targetSellingPrice: parseFloat(e.target.value) || 0 })}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono font-bold text-emerald-800"
                        />
                      </div>

                      <div>
                        <label className="text-xs font-bold text-slate-700 block mb-1">
                          {isTa ? 'எதிர்பார்க்கும் மாத விற்பனை (அளவுகள்)' : 'Expected Monthly Sales Volume (Units)'}
                        </label>
                        <input
                          type="number"
                          min="1"
                          value={pricingStrategy.expectedMonthlySalesUnits}
                          onChange={(e) => setPricingStrategy({ ...pricingStrategy, expectedMonthlySalesUnits: parseFloat(e.target.value) || 0 })}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono font-bold"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 7: CHANNELS */}
                {wizardStep === 7 && (
                  <div className="space-y-4">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 7: விற்பனை மற்றும் விநியோக வழிகள்' : 'Step 7: Sales & Distribution Channels'}
                    </h3>
                    <div className="space-y-2">
                      {[
                        'Uzhavar Sandhai Direct Stall',
                        'AgriBharat Direct Marketplace',
                        'Weekly Village Shandy / Haat',
                        'Supply to Local Retail Kirana Stores',
                        'Direct Delivery to Registered Farm Gate Buyers'
                      ].map((ch) => {
                        const isChecked = distributionChannels.includes(ch);
                        return (
                          <label key={ch} className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 text-xs font-semibold text-slate-800">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) setDistributionChannels([...distributionChannels, ch]);
                                else setDistributionChannels(distributionChannels.filter((c) => c !== ch));
                              }}
                              className="rounded-sm text-emerald-700"
                            />
                            <span>{ch}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* STEP 8: STATUTORY & SAVE */}
                {wizardStep === 8 && (
                  <div className="space-y-5">
                    <h3 className="text-base font-extrabold text-slate-900 border-b border-slate-100 pb-2">
                      {isTa ? 'படி 8: சட்டப்பூர்வ பதிவுகள் மற்றும் திட்ட சேமிப்பு' : 'Step 8: Statutory Compliance & Final Save'}
                    </h3>
                    <div className="space-y-2 text-xs">
                      <div className="font-bold text-slate-700 mb-1">{isTa ? 'சட்டப்பூர்வ சான்றிதழ் நிலை:' : 'Regulatory Status:'}</div>
                      {Object.entries(regulatoryChecklist).map(([k, v]) => (
                        <label key={k} className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 cursor-pointer text-slate-800">
                          <input
                            type="checkbox"
                            checked={v}
                            onChange={(e) => setRegulatoryChecklist({ ...regulatoryChecklist, [k]: e.target.checked })}
                            className="rounded-sm text-emerald-700"
                          />
                          <span className="font-semibold uppercase text-[11px]">{k}</span>
                        </label>
                      ))}
                    </div>

                    {/* Official Incubation Links */}
                    <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2 text-xs">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <Building2 className="w-4 h-4 text-emerald-700" />
                        <span>{isTa ? 'இணைக்கப்பட்ட அரசு ஆதரவு & மானியங்கள்:' : 'Linked Government Incubation & Financing:'}</span>
                      </div>
                      <p className="text-[11px] text-emerald-800 leading-relaxed">
                        {isTa
                          ? 'இத்திட்டத்தை TNAU DABD அல்லது EDII-TN வழியாக தொழில்முனைவோர் பயிற்சி பெற்று PMFME 35% மூலதன மானியத்திற்கு சமர்ப்பிக்கலாம்.'
                          : 'You can submit this plan for 35% capital subsidy under PMFME or interest subvention under Agriculture Infrastructure Fund (AIF).'}
                      </p>
                      <div className="pt-1 flex flex-wrap gap-2 text-[11px]">
                        <a href="https://pmfme.mofpi.gov.in/" target="_blank" rel="noreferrer" className="text-emerald-700 font-bold hover:underline inline-flex items-center gap-0.5">
                          PMFME Portal <ExternalLink className="w-3 h-3" />
                        </a>
                        <span>•</span>
                        <a href="https://agriinfra.dac.gov.in/" target="_blank" rel="noreferrer" className="text-emerald-700 font-bold hover:underline inline-flex items-center gap-0.5">
                          AIF Scheme <ExternalLink className="w-3 h-3" />
                        </a>
                        <span>•</span>
                        <a href="https://agritech.tnau.ac.in/dabd/" target="_blank" rel="noreferrer" className="text-emerald-700 font-bold hover:underline inline-flex items-center gap-0.5">
                          TNAU DABD <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>

                    {planSaveSuccess && (
                      <div className="p-3 rounded-xl bg-emerald-100 text-emerald-900 text-xs font-bold flex items-center gap-2 border border-emerald-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                        <span>{isTa ? 'வணிகத் திட்டம் வெற்றிகரமாக சேமிக்கப்பட்டது!' : 'Business plan saved successfully to your farmer profile!'}</span>
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={handleSavePlan}
                      disabled={isSavingPlan}
                      className="w-full py-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-black text-sm shadow-md transition-all flex items-center justify-center gap-2"
                    >
                      {isSavingPlan ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Bookmark className="w-4 h-4" />}
                      <span>{isTa ? 'வணிகத் திட்டத்தை சேமிக்கவும்' : 'Save Business Plan to Profile'}</span>
                    </button>
                  </div>
                )}

                {/* Stepper Navigation Buttons */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                  <button
                    type="button"
                    disabled={wizardStep === 1}
                    onClick={() => setWizardStep(Math.max(1, wizardStep - 1))}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-40"
                  >
                    {isTa ? 'முந்தைய படி' : 'Previous Step'}
                  </button>

                  <button
                    type="button"
                    disabled={wizardStep === 8}
                    onClick={() => setWizardStep(Math.min(8, wizardStep + 1))}
                    className="px-5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold shadow-xs flex items-center gap-1.5 disabled:opacity-40"
                  >
                    <span>{isTa ? 'அடுத்த படி' : 'Next Step'}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Right 1 Col: Live Financial Projections & Breakeven Card */}
            <div className="space-y-4">
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-4 sticky top-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                    <Calculator className="w-4 h-4 text-emerald-700" />
                    <span>{isTa ? 'நிதி கணக்கீடு சுருக்கம்' : 'Live Financial Projections'}</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    Auto-Update
                  </span>
                </div>

                {liveCalculations && (
                  <div className="space-y-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-slate-500">{isTa ? 'தொடக்க முதலீடு (Capex):' : 'Startup Capex:'}</span>
                        <strong className="font-mono text-slate-900">₹{liveCalculations.totalStartupCapex.toLocaleString('en-IN')}</strong>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">{isTa ? 'மாத இயக்கச் செலவு (Opex):' : 'Monthly Opex:'}</span>
                        <strong className="font-mono text-slate-900">₹{liveCalculations.totalMonthlyOpex.toLocaleString('en-IN')}</strong>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">{isTa ? 'மாத வரவு (Gross Revenue):' : 'Monthly Gross Revenue:'}</span>
                        <strong className="font-mono text-emerald-700 font-bold">₹{liveCalculations.monthlyGrossRevenue.toLocaleString('en-IN')}</strong>
                      </div>
                      <div className="flex justify-between pt-1 border-t border-slate-200">
                        <span className="font-bold text-slate-700">{isTa ? 'மாத நிகர உபரி (Operating Surplus):' : 'Net Operating Surplus:'}</span>
                        <strong className={`font-mono font-black ${liveCalculations.monthlyNetOperatingSurplus >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                          ₹{liveCalculations.monthlyNetOperatingSurplus.toLocaleString('en-IN')}
                        </strong>
                      </div>
                    </div>

                    {/* Breakeven Timeline */}
                    <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 space-y-1">
                      <div className="text-[11px] font-bold text-emerald-950">{isTa ? 'முதலீடு மீட்பு & பிரேக்-ஈவன்:' : 'Breakeven Payback:'}</div>
                      <div className="text-lg font-black text-emerald-900 font-mono">
                        {liveCalculations.breakevenMonths > 0 ? `${liveCalculations.breakevenMonths} Months` : 'N/A'}
                      </div>
                      <div className="text-[10px] text-emerald-700">
                        {isTa ? 'குறைந்தபட்ச விற்பனை அளவு:' : 'Breakeven Volume:'} <strong>{liveCalculations.breakevenMonthlyUnits} units/month</strong>
                      </div>
                    </div>

                    {/* Assumptions Notes */}
                    <div className="space-y-1 text-[11px] text-slate-500 italic">
                      <p>"{liveCalculations.disclaimer}"</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: MY SAVED PLANS */}
      {activeTab === 'saved' && isFarmer && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-black text-slate-900">
                {isTa ? 'என் சேமிக்கப்பட்ட வணிகத் திட்டங்கள்' : 'My Saved Business Plans'} ({savedPlans.length})
              </h3>
              <p className="text-xs text-slate-500">
                {isTa ? 'உங்கள் சுயவிவரத்தில் பதிவு செய்யப்பட்ட திட்டங்கள்.' : 'Plans saved to your profile for bank loan and subsidy applications.'}
              </p>
            </div>
          </div>

          {isLoadingPlans ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-700" />
              <span>{isTa ? 'திட்டங்கள் ஏற்றப்படுகின்றன...' : 'Loading saved business plans...'}</span>
            </div>
          ) : savedPlans.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
              <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-700">{isTa ? 'சேமிக்கப்பட்ட திட்டங்கள் இல்லை' : 'No saved business plans yet'}</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                {isTa ? 'தொழில் வழிகாட்டியைப் பயன்படுத்தி உங்கள் முதல் வணிகத் திட்டத்தை உருவாக்கவும்.' : 'Use the 8-step planning wizard to create and save your first bankable agricultural project.'}
              </p>
              <button
                onClick={() => { setActiveTab('wizard'); setWizardStep(1); }}
                className="mt-4 px-4 py-2 bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-emerald-800"
              >
                {isTa ? 'புதிய திட்டம் உருவாக்குக' : 'Start New Plan'}
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedPlans.map((p) => (
                <div key={p.planId} className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      ID: {p.planId}
                    </span>
                    <button
                      onClick={() => handleDeletePlan(p.planId)}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="Delete Plan"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div>
                    <h4 className="text-base font-extrabold text-slate-900">{p.businessName}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {isTa ? 'உருவாக்கப்பட்ட தேதி:' : 'Created:'} {new Date(p.createdAt).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50 rounded-xl text-center text-xs">
                    <div>
                      <div className="text-[10px] text-slate-500 font-bold">{isTa ? 'முதலீடு' : 'Capex'}</div>
                      <div className="font-mono font-bold text-slate-800 mt-0.5">₹{p.financialCalculations.totalStartupCapex.toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-bold">{isTa ? 'மாத வரவு' : 'Monthly Rev'}</div>
                      <div className="font-mono font-bold text-emerald-700 mt-0.5">₹{p.financialCalculations.monthlyGrossRevenue.toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-bold">{isTa ? 'மீட்பு' : 'Payback'}</div>
                      <div className="font-mono font-bold text-teal-800 mt-0.5">{p.financialCalculations.breakevenMonths}m</div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-500">
                      Status: <strong className="text-slate-800 uppercase">{p.status}</strong>
                    </span>
                    <button
                      onClick={() => {
                        setSelectedIdeaId(p.ideaId || 'bio_inputs_lab');
                        setPlanBusinessName(p.businessName);
                        setEquipmentList(p.wizardData.equipmentAndInfrastructure || []);
                        setRawMaterialsList(p.wizardData.rawMaterialInputs || []);
                        setOperatingCosts(p.wizardData.operatingCosts || {});
                        setPricingStrategy({
                          productUnit: p.wizardData.pricingStrategy?.productUnit || '1 Unit',
                          unitProductionCost: p.wizardData.pricingStrategy?.unitProductionCost || 0,
                          targetSellingPrice: p.wizardData.pricingStrategy?.targetSellingPrice || 0,
                          expectedMonthlySalesUnits: p.wizardData.pricingStrategy?.expectedMonthlySalesUnits || 0
                        });
                        setActiveTab('wizard');
                        setWizardStep(1);
                      }}
                      className="text-emerald-700 font-bold hover:underline flex items-center gap-1"
                    >
                      <span>{isTa ? 'திறக்கவும் / மாற்றவும்' : 'Open in Wizard'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL: FULL IDEA DETAILS & SCHEMES */}
      {selectedIdeaForModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl relative my-8 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  {selectedIdeaForModal.category}
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-1">
                  {isTa ? selectedIdeaForModal.title.ta : selectedIdeaForModal.title.en}
                </h3>
              </div>
              <button
                onClick={() => setSelectedIdeaForModal(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {/* Statutory Compliance Checklist */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                {isTa ? 'சட்டப்பூர்வ பதிவுகள் & விதிமுறைகள்:' : 'Statutory & Regulatory Requirements:'}
              </h4>
              <div className="space-y-1.5">
                {selectedIdeaForModal.statutoryRequirements.map((st, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700 flex items-start gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                    <span>{isTa ? st.ta : st.en}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Official Training & Incubation Providers */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                {isTa ? 'அங்கீகரிக்கப்பட்ட பயிற்சி & மானிய நிறுவனங்கள்:' : 'Official Training, Incubation & Support Resources:'}
              </h4>
              <div className="space-y-2">
                {selectedIdeaForModal.officialResources.map((res, i) => (
                  <div key={i} className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <strong className="text-emerald-950 font-bold">{res.title}</strong>
                      <a href={res.link} target="_blank" rel="noreferrer" className="text-emerald-700 hover:underline inline-flex items-center gap-0.5 text-[11px] font-bold">
                        Website <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <p className="text-[11px] text-emerald-800">{res.department} • {res.eligibilityNote}</p>
                    <div className="flex items-center gap-3 text-[11px] text-emerald-900 pt-1 border-t border-emerald-200">
                      {res.phone && (
                        <span className="flex items-center gap-1 font-semibold">
                          <Phone className="w-3 h-3 text-emerald-700" /> {res.phone}
                        </span>
                      )}
                      {res.email && (
                        <span className="flex items-center gap-1 font-semibold">
                          <Mail className="w-3 h-3 text-emerald-700" /> {res.email}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Disclaimer */}
            <p className="text-[11px] text-slate-500 italic p-3 bg-slate-50 rounded-xl border border-slate-100">
              "{selectedIdeaForModal.nonGuaranteeDisclaimer}"
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setSelectedIdeaForModal(null)}
                className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 text-xs font-semibold"
              >
                {isTa ? 'மூடு' : 'Close'}
              </button>
              <button
                onClick={() => {
                  const idea = selectedIdeaForModal;
                  setSelectedIdeaForModal(null);
                  handleAdoptIdea(idea);
                }}
                className="px-5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-md"
              >
                {isTa ? 'இந்த யோசனைக்கு திட்டம் உருவாக்கவும்' : 'Adopt and Build Plan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

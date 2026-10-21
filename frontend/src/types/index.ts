export type Language =
  | 'as'  // Assamese
  | 'bn'  // Bengali
  | 'brx' // Bodo
  | 'doi' // Dogri
  | 'en'  // English
  | 'gu'  // Gujarati
  | 'hi'  // Hindi
  | 'kn'  // Kannada
  | 'ks'  // Kashmiri
  | 'kok' // Konkani
  | 'mai' // Maithili
  | 'ml'  // Malayalam
  | 'mni' // Manipuri (Meitei)
  | 'mr'  // Marathi
  | 'ne'  // Nepali
  | 'or'  // Odia
  | 'pa'  // Punjabi
  | 'sa'  // Sanskrit
  | 'sat' // Santali
  | 'sd'  // Sindhi
  | 'ta'  // Tamil
  | 'te'  // Telugu
  | 'ur'  // Urdu
  | 'other';

export type NavTab = 
  | 'dashboard'
  | 'assistant'
  | 'weather'
  | 'irrigation'
  | 'disease'
  | 'recommendations'
  | 'market'
  | 'schemes'
  | 'support_hub'
  | 'special_operation'
  | 'marketplace'
  | 'agri_entrepreneurship'
  | 'value_addition'
  | 'procurement'
  | 'queue'
  | 'notifications'
  | 'profile'
  | 'staff_portal';

export type ViewState = 'normal' | 'loading' | 'empty' | 'error';

export interface GeoDistrictItem {
  id: string;
  code: string;
  name: string;
  localNames?: Record<string, string>;
}

export interface GeoStateItem {
  id: string;
  code: string;
  name: string;
  type: 'state' | 'union_territory';
  localNames?: Record<string, string>;
  districtsCount: number;
  districts?: GeoDistrictItem[];
}

export interface GeoMetaResponse {
  version: string;
  lastUpdated: string;
  source: string;
  license: string;
  totalRegions: number;
  statesCount: number;
  unionTerritoriesCount: number;
  totalDistricts: number;
  notes: string;
}

export interface FarmerProfile {
  name: string;
  phone: string;
  location: string;
  district: string;
  state: string;
  country?: string;
  stateCode?: string;
  districtCode?: string;
  taluk?: string;
  village?: string;
  totalLandAcres?: number;
  landUnit?: string;
  primaryCrop?: string;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  preferredLanguage?: Language;
  profilePhoto?: string;
  aadhaarMasked?: string;
  farmerId?: string;
  isFromDb?: boolean;
  isPhoneVerified?: boolean;
  telegramLinked?: boolean;
  telegramUsername?: string;
}

export interface WeatherData {
  temperatureC: number;
  condition: string;
  humidity: number;
  rainfallChance: number;
  windSpeedKmh: number;
  updatedAt: string;
  isSample: boolean;
  forecast: Array<{
    day: string;
    temp: string;
    condition: string;
    rainProb: number;
  }>;
}

export interface IrrigationAdvice {
  soilMoisturePercent: number;
  status: 'optimal' | 'dry' | 'excess';
  nextScheduledTime: string;
  waterSavedLiters: number;
  recommendation: string;
  isSample: boolean;
}

export interface CropHealth {
  cropName: string;
  stage: string;
  healthScorePercent: number;
  status: 'healthy' | 'attention' | 'critical';
  lastScannedDate: string;
  notes: string;
  isSample: boolean;
}

export interface QualityInspectionRecord {
  qualityStatus: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
  qualityGrade: string;
  moisturePercent: number;
  declaredWeightKg: number;
  acceptedWeightKg: number;
  rejectedWeightKg: number;
  rejectionReason?: string;
  notes?: string;
  inspectedAt: string;
  inspectedByStaff: string;
}

export interface ProcurementSlot {
  bookingId: string;
  mandiName: string;
  crop: string;
  cropVariety?: string;
  harvestDate?: string;
  quantityBags: number;
  estimatedWeightQuintals: number;
  slotDate: string;
  timeWindow: string;
  tokenNumber: string;
  status: 'confirmed' | 'pending' | 'weighed' | 'completed' | 'booked' | 'quality_checked' | 'no_show' | 'rejected' | string;
  isSample: boolean;
  isFromDb?: boolean;
  qualityInspection?: QualityInspectionRecord;
  noShowDetails?: {
    markedAt: string;
    markedByStaff: string;
    reason: string;
  };
  isNowServing?: boolean;
  rateSourceLabel?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  time: string;
  language?: Language;
  provider?: string;
  isRealAI?: boolean;
  providerNotice?: string;
  followUpQuestion?: string;
}

export interface InAppNotification {
  id: string;
  title: string;
  titleTa?: string;
  message: string;
  messageTa?: string;
  type: 'booking' | 'queue' | 'weighing' | 'bill' | 'payment' | 'weather' | 'irrigation' | 'market' | string;
  eventType?: string;
  sourceDataTime?: string;
  relatedFarmId?: string;
  coordinates?: { latitude?: number; longitude?: number };
  crop?: string;
  growthStage?: string;
  recommendation?: string;
  // Mandi Market Fields
  market?: string;
  district?: string;
  commodity?: string;
  commodityTa?: string;
  variety?: string;
  grade?: string;
  oldPrice?: number | null;
  newPrice?: number | null;
  priceDiff?: number | null;
  priceChangePercent?: number | null;
  sourceReportingDate?: string;
  dedupKey?: string;
  isRead: boolean;
  createdAt: string;
  isoTimestamp?: string;
  bookingId?: string;
  farmerId?: string;
  userId?: string;
}

export interface NotificationPreferences {
  userId: string;
  farmerId?: string | null;
  rainAlerts: boolean;
  irrigationDemandAlerts: boolean;
  heatDemandAlerts: boolean;
  staleWeatherAlerts: boolean;
  adviceChangeAlerts: boolean;
  pushEnabled: boolean;
  pushConfigured: boolean;
  // Mandi Price Alerts
  mandiPriceAlerts?: boolean;
  mandiPriceSurgeAlerts?: boolean;
  mandiPriceDropAlerts?: boolean;
  mandiStaleFeedAlerts?: boolean;
  mandiSelectedCommodities?: string[];
  mandiSelectedMarkets?: string[];
  mandiPriceThresholdPercent?: number;
  updatedAt?: string | null;
}

export interface PushStatusInfo {
  pushConfigured: boolean;
  inAppActive: boolean;
  vapidPublicKey?: string | null;
  subscribed: boolean;
  note: string;
}

export interface IrrigationAlertCheckSummary {
  checkedFarmers: number;
  generatedAlerts: number;
  skippedDeduplicated: number;
  skippedByPreferences: number;
  rateLimited: number;
  workerId: string;
  timestamp: string;
  leaseAcquired: boolean;
  note?: string | null;
}

export interface SMSStatusInfo {
  configured: boolean;
  provider: string;
  senderId?: string;
  message: string;
  note: string;
}

export type {
  CounterInfo,
  NowServingResponse,
  CropReportSummary,
  CounterThroughputSummary,
  DailyProcurementReportResponse,
  SlotClosureEntity,
  FarmerQuotaCheckResponse,
  ProcurementCentreItem
} from '../services/api';

// ============================================================================
// FARMER SUPPORT HUB & DIRECT MARKETPLACE TYPES
// ============================================================================

export interface BilingualText {
  en: string;
  ta: string;
}

export interface SupportContactInfo {
  name?: string;
  designation?: string;
  contactType?: 'institutional_office' | 'individual_officer' | 'helpline' | 'unverified';
  officePhone?: string;
  helplinePhone?: string;
  mobile?: string;
  email?: string;
  address?: string;
  deskName?: string;
  contactVerificationStatus: 'verified_official' | 'pending_verification' | 'unverified';
  verificationNote?: string;
}

export interface TrainingMeta {
  startDate: string;
  endDate: string;
  registrationDeadline?: string;
  mode: 'In-Person' | 'Classroom' | 'Hands-on Workshop' | 'Online Webinar' | 'Hybrid';
  scheduleStatus?: 'current_active' | 'recurring_monthly' | 'historical_reference' | 'unverified_schedule';
  venue?: string;
  fees?: string;
  capacity?: number;
  eligibility?: string;
  curriculumHighlights?: string[];
  organizingBody?: string;
  verificationNote?: string;
}

export interface CropStageGuidance {
  stageNumber: number;
  stageName: string;
  stageNameTa?: string;
  daysRange: string;
  keyActivities: string[];
  waterManagement?: string;
  nutrientRegime?: string;
  pestMonitoring?: string;
  criticalAlert?: string;
}

export interface CropGuideMeta {
  cropName: string;
  cropNameTa?: string;
  season?: string;
  durationDays?: number;
  stages: CropStageGuidance[];
  harvestIndices?: string[];
  marketChannels?: string[];
  procurementCenterIntegration?: string;
}

export interface SupportSubsidyMeta {
  schemeName: string;
  costNorm?: string;
  subsidyPercent?: number;
  maxEligibleArea?: string;
  applicationPortal?: string;
  applicableSectors?: string[];
}

export interface EntrepreneurshipMeta {
  businessIdea: BilingualText;
  targetCustomers: string[];
  requiredEquipment: string[];
  inputsRequired: string[];
  startupPlanningSteps: string[];
  estimatedCapitalCost: string;
  estimatedMonthlyOperatingCost: string;
  revenueAssumptions: string;
  riskAnalysis: string[];
  officialSupportResources: string[];
}

export interface OrganicMeta {
  soilHealthPractices: string[];
  compostingMethods: string[];
  bioInputsRecipes: Array<{ name: string; nameTa?: string; ingredients: string[]; dosage: string; preparationDays: number }>;
  cropRotationPlanning: string[];
  organicPestManagement: string[];
  transitionTimelineYears: number;
  certificationSteps: string[];
}

export interface ProtectedCultivationMeta {
  structureType: string;
  suitableCrops: string[];
  irrigationFertigationRegime: string;
  pestDiseaseManagement: string[];
  setupRequirements: string[];
  annualMaintenanceTips: string[];
  applicableSchemes: string[];
}

export interface ValueAdditionMeta {
  produceCategory: string;
  processingIdea: BilingualText;
  hygieneStandards: string[];
  packagingOptions: string[];
  shelfLifeExtensionDays: string;
  estimatedCostingBreakdown: string;
  marketingChannels: string[];
}

export interface DirectMarketMeta {
  channelType?: string;
  marketType?: string;
  platformPortal?: string;
  helplinePhone?: string;
  suitableProduce?: string[];
  registrationProcess?: string[];
  requiredDocuments?: string[];
  qualityAssayingParameters?: string[];
  tradingWorkflowStages?: string[];
  tradingWorkflow?: string[];
  tradingWorkflowTa?: string[];
  buyerTypes?: string[];
  buyerLinkageChannels?: string[];
  pricingMechanism?: string;
  disputeResolutionDesk?: string;
  chargesOrLevies?: string;
  digitalPaymentModes?: string[];
}

export interface FarmerSupportContent {
  contentId: string;
  category: 'training' | 'entrepreneurship' | 'organic' | 'special_operation' | 'protected_cultivation' | 'value_addition' | 'direct_market';
  subCategory?: string;
  contentType: 'guidance_package' | 'static_educational' | 'training_announcement' | 'scheme_sop' | 'contact_directory';
  title: BilingualText;
  description: BilingualText;
  district?: string;
  state?: string;
  language?: string;
  institution: string;
  officialSourceUrl: string;
  sourcePublicationDate?: string;
  lastCheckedDate: string;
  sourceExcerpt?: string;
  adminReviewed?: boolean;
  verificationStatus: 'verified_official' | 'pending_review' | 'stale_review_needed';
  activeStatus: 'active' | 'expired' | 'archived';
  contact: SupportContactInfo;
  trainingMeta?: TrainingMeta;
  cropGuideMeta?: CropGuideMeta;
  subsidyMeta?: SupportSubsidyMeta;
  entrepreneurshipMeta?: EntrepreneurshipMeta;
  organicMeta?: OrganicMeta;
  protectedCultivationMeta?: ProtectedCultivationMeta;
  valueAdditionMeta?: ValueAdditionMeta;
  directMarketMeta?: DirectMarketMeta;
  registrationInstructions?: BilingualText;
  highlights?: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface FarmerSupportResponse {
  items: FarmerSupportContent[];
  total: number;
  categories: string[];
  districts: string[];
  states?: string[];
  hasStaleNotice: boolean;
}

export interface MarketplaceListing {
  listingId: string;
  farmerId: string;
  farmerName: string;
  farmerPhone: string;
  crop: string;
  variety?: string;
  category: string;
  district: string;
  village?: string;
  quantity: number;
  unit: string;
  pricePerUnit: number;
  isOrganicCertified: boolean;
  certificationBody?: string;
  harvestDate?: string;
  availableUntil?: string;
  fulfillmentModes: string[];
  serviceArea?: string;
  photoUrls?: string[];
  showContactToBuyers?: boolean;
  description?: string;
  listingStatus: 'active' | 'sold_out' | 'out_of_stock' | 'paused' | 'expired' | 'flagged';
  viewCount: number;
  inquiryCount: number;
  reportCount?: number;
  adminFlagged: boolean;
  flagReason?: string;
  isDemoData?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MarketplaceResponse {
  items: MarketplaceListing[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  categories: string[];
  districts: string[];
}

export interface MarketplaceListingCreate {
  crop: string;
  variety?: string;
  category: string;
  district: string;
  village?: string;
  quantity: number;
  unit: string;
  pricePerUnit: number;
  isOrganicCertified?: boolean;
  certificationBody?: string;
  harvestDate?: string;
  availableUntil?: string;
  fulfillmentModes?: string[];
  serviceArea?: string;
  photoUrls?: string[];
  showContactToBuyers?: boolean;
  description?: string;
  isDemoData?: boolean;
}

export interface MarketplaceListingReportRequest {
  reasonCategory: 'spam' | 'fake_price' | 'misleading_claims' | 'expired_produce' | 'other';
  details?: string;
  reporterPhone?: string;
}

export interface MarketplaceOrderRequestCreate {
  buyerName: string;
  buyerPhone: string;
  requestedQuantity: number;
  fulfillmentPreference?: string;
  deliveryAddress?: string;
  message?: string;
}

export interface MarketplaceOrderRequest {
  orderId: string;
  listingId: string;
  farmerId: string;
  crop: string;
  unit: string;
  pricePerUnit: number;
  totalEstimatedPrice: number;
  buyerName: string;
  buyerPhone: string;
  requestedQuantity: number;
  fulfillmentPreference: string;
  deliveryAddress?: string;
  message?: string;
  status: 'pending' | 'confirmed' | 'rejected' | 'completed';
  createdAt: string;
  updatedAt?: string;
}

// ============================================================================
// SPECIAL OPERATION — FROM FIRST STEP TO FIRST SALE
// ============================================================================

export interface BilingualText {
  en: string;
  ta: string;
}

export type SpecialOperationLandUnit = 'acres' | 'cents' | 'guntas' | 'sq_ft' | 'unknown';
export type SpecialOperationWater = 'ample_borewell' | 'canal_seasonal' | 'rainfed_only' | 'tank_limited' | 'unknown';
export type SpecialOperationSoil = 'red_sandy_loam' | 'clay_loam' | 'alluvial' | 'black_cotton' | 'unknown';
export type SpecialOperationSeason = 'samba_thaladi' | 'kuruvai' | 'navarai_summer' | 'rainfed_monsoon' | 'year_round' | 'unknown';
export type SpecialOperationBudget = 'micro_under_15k' | 'low_15k_35k' | 'medium_35k_75k' | 'flexible_above_75k' | 'unknown';
export type SpecialOperationLabour = 'family_only_1_2' | 'hired_occasional' | 'abundant' | 'unknown';
export type SpecialOperationGoal = 'commercial_income' | 'household_consumption' | 'low_risk_learning' | 'organic_lifestyle';

export interface SpecialOperationProfileInput {
  district: string;
  landArea: number;
  landUnit: SpecialOperationLandUnit;
  waterAvailability: SpecialOperationWater;
  soilType: SpecialOperationSoil;
  season: SpecialOperationSeason;
  budgetRange: SpecialOperationBudget;
  availableLabour: SpecialOperationLabour;
  farmingGoal: SpecialOperationGoal;
}

export interface SpecialOperationCropRecommendation {
  cropId: string;
  cropName: BilingualText;
  varietySuggestions: string[];
  durationDays: number;
  suitabilityScore: number;
  suitabilityReason: BilingualText;
  waterNeedLevel: string;
  waterNeedText: BilingualText;
  budgetEstimatePerAcre: string;
  tradeOffsAndRisks: BilingualText[];
  marketChannels: string[];
  verifiedReference: {
    institution: string;
    sourceTitle: string;
    sourceUrl: string;
    reviewDate: string;
  };
}

export interface JourneyObservation {
  id: string;
  date: string;
  stageNumber: number;
  note: string;
  photoUrl?: string;
  isDeviation: boolean;
  deviationReason?: string;
  createdAt: string;
}

export interface CostItemEntry {
  category: string;
  itemName: BilingualText;
  benchmarkRatePerAcre: number;
  userQuantity: number;
  userUnitPrice: number;
  isUserEdited: boolean;
  notes?: string;
}

export interface JourneyCostsWorksheet {
  entries: CostItemEntry[];
  totalOperatingCost: number;
  costPerUnitArea: number;
  disclaimer: string;
}

export interface JourneySalePlan {
  targetChannels: string[];
  mandiPriceSnapshot?: {
    crop: string;
    modalPricePerQuintal?: number;
    modalPricePerKg?: number;
    mandiName?: string;
    lastUpdated?: string;
  };
  gradingPackagingDetails: string[];
  transportConsiderations: string;
  disclaimer: string;
}

export interface JourneyCompletionRecord {
  harvestDate: string;
  harvestedQuantity: number;
  harvestUnit: string;
  gradeBreakdown: Record<string, number>;
  buyerNameOrChannel: string;
  achievedPricePerUnit: number;
  grossRevenue: number;
  totalOperatingCost: number;
  netProfitOrLoss: number;
  farmerReflection?: string;
  completedAt: string;
}

export interface SpecialOperationTimelineStage {
  stageNumber: number;
  stageName: BilingualText;
  startDay: number;
  endDay: number;
  calendarStartDate?: string;
  calendarEndDate?: string;
  isCompleted: boolean;
  isActive: boolean;
  isUpcoming: boolean;
  tasks: Array<{
    task: BilingualText;
    criticality: 'critical' | 'high' | 'recommended' | 'optional';
    category: string;
  }>;
}

export interface SpecialOperationTimeline {
  cropId: string;
  cropName: BilingualText;
  totalDurationDays: number;
  plantingDate?: string;
  daysElapsed: number;
  currentActiveStageNumber: number;
  percentComplete: number;
  stages: SpecialOperationTimelineStage[];
}

export interface SpecialOperationJourney {
  journeyId: string;
  farmerId: string;
  farmerName: string;
  farmerPhone: string;
  status: 'in_progress' | 'paused' | 'completed' | 'abandoned';
  currentStep: number;
  profileInput: SpecialOperationProfileInput;
  selectedCropId?: string;
  selectedCropName?: BilingualText;
  plantingDate?: string;
  landAreaNormalizedAcres: number;
  checklists: Record<string, boolean>;
  observations: JourneyObservation[];
  costsWorksheet: JourneyCostsWorksheet;
  salePlan: JourneySalePlan;
  completionRecord?: JourneyCompletionRecord;
  remindersActive: boolean;
  createdAt: string;
  updatedAt: string;
  timeline?: SpecialOperationTimeline;
}

export interface SpecialOperationStepUpdateRequest {
  currentStep: number;
  status?: 'in_progress' | 'paused' | 'completed' | 'abandoned';
  profileInput?: SpecialOperationProfileInput;
  selectedCropId?: string;
  plantingDate?: string;
  checklists?: Record<string, boolean>;
  costsWorksheet?: JourneyCostsWorksheet;
  salePlan?: JourneySalePlan;
  completionRecord?: JourneyCompletionRecord;
  remindersActive?: boolean;
}

export interface SpecialOperationCropGuide {
  cropId: string;
  cropName: BilingualText;
  varietySuggestions: string[];
  durationDays: number;
  landPreparation: {
    steps: Array<{
      id: string;
      title: BilingualText;
      description: BilingualText;
      soilTestAlert?: BilingualText;
      kvkContactAlert?: BilingualText;
    }>;
  };
  plantingInstructions: {
    seedRatePerAcre: BilingualText;
    spacing: {
      rowToRowCm: number;
      plantToPlantCm: number;
      diagramText: BilingualText;
    };
    plantingDepthCm: number;
    nurseryAndSowingMethod: BilingualText;
    idealTimingOfDay: BilingualText;
  };
  cropCareStages: Array<{
    stageNumber: number;
    stageName: BilingualText;
    durationDays: number;
    tasks: Array<{
      category: 'irrigation' | 'nutrients' | 'weeds' | 'ipm' | 'monitoring';
      task: BilingualText;
      criticality: 'critical' | 'high' | 'recommended' | 'optional';
    }>;
    smartFeaturesPrompt?: {
      feature: 'weather' | 'irrigation' | 'disease';
      message: BilingualText;
    };
  }>;
  harvestReadiness: {
    maturityIndicators: BilingualText[];
    harvestingMethod: BilingualText;
    postHarvestCare: BilingualText[];
    gradingStandards: Array<{
      grade: string;
      description: BilingualText;
    }>;
    storageAdvisory: BilingualText;
    safetyCaution: BilingualText;
  };
  references: {
    institution: string;
    sourceTitle: string;
    sourceUrl: string;
    reviewDate: string;
  };
}

// ============================================================================
// AGRI ENTREPRENEURSHIP & VALUE ADDED PRODUCTS TYPES
// ============================================================================

export interface BusinessIdeaItem {
  ideaId: string;
  title: BilingualText;
  category: string;
  matchScore: number;
  matchReasons: BilingualText[];
  suitabilitySummary: BilingualText;
  estimatedStartupCapex: Record<string, number>;
  estimatedMonthlyOpex: Record<string, number>;
  typicalBreakevenMonths: string;
  targetCustomers: BilingualText[];
  requiredSkillsAndEquipment: BilingualText[];
  officialResources: Array<{
    title: string;
    department: string;
    phone: string;
    email: string;
    link: string;
    eligibilityNote: string;
  }>;
  statutoryRequirements: BilingualText[];
  nonGuaranteeDisclaimer: string;
}

export interface BusinessIdeaMatchRequest {
  interests: string[];
  skills: string[];
  locationDistrict: string;
  investmentBudget: number;
  availableProduce: string[];
  landOrSpaceAvailable?: string;
}

export interface BusinessIdeaMatchResponse {
  matchedIdeas: BusinessIdeaItem[];
  farmerContextSummary: Record<string, any>;
  disclaimer: string;
}

export interface BusinessPlanWizardData {
  productOrService: string;
  customerSegment: string[];
  equipmentAndInfrastructure: Array<{
    name: string;
    quantity: number;
    unitCost: number;
    totalCost?: number;
  }>;
  rawMaterialInputs: Array<{
    name: string;
    monthlyQuantity: number;
    unitCost: number;
    totalCost?: number;
  }>;
  operatingCosts: Record<string, number>;
  pricingStrategy: {
    productUnit?: string;
    unitProductionCost?: number;
    targetSellingPrice?: number;
    expectedMonthlySalesUnits?: number;
  };
  distributionChannels: string[];
  risksAndMitigations: Array<{
    risk: string;
    mitigation: string;
  }>;
  regulatoryChecklist: Record<string, boolean>;
  nextStepsRoadmap: Array<{
    stepNumber: number | string;
    title: string;
    timeline: string;
    resourceLink?: string;
  }>;
}

export interface BusinessPlanCalculationResult {
  totalStartupCapex: number;
  totalMonthlyOpex: number;
  monthlyGrossRevenue: number;
  monthlyNetOperatingSurplus: number;
  breakevenMonthlyUnits: number;
  breakevenMonths: number;
  itemizedAssumptions: string[];
  disclaimer: string;
}

export interface BusinessPlanModel {
  planId: string;
  farmerId: string;
  farmerName: string;
  businessName: string;
  ideaId?: string;
  wizardData: BusinessPlanWizardData;
  financialCalculations: BusinessPlanCalculationResult;
  linkedSchemes: Array<{
    name: string;
    link: string;
    subsidyType: string;
  }>;
  status: 'draft' | 'in_review' | 'finalized';
  createdAt: string;
  updatedAt: string;
}

export interface BusinessPlanCreateRequest {
  businessName: string;
  ideaId?: string;
  wizardData: BusinessPlanWizardData;
}

export interface BusinessPlanUpdateRequest {
  businessName?: string;
  wizardData?: BusinessPlanWizardData;
  status?: 'draft' | 'in_review' | 'finalized';
}

export interface BusinessPlanCalculationRequest {
  equipmentAndInfrastructure: Array<{
    name: string;
    quantity: number;
    unitCost: number;
    totalCost?: number;
  }>;
  rawMaterialInputs: Array<{
    name: string;
    monthlyQuantity: number;
    unitCost: number;
    totalCost?: number;
  }>;
  operatingCosts: Record<string, number>;
  pricingStrategy: Record<string, any>;
}

export interface ValueAdditionProductBlueprint {
  productId: string;
  productName: BilingualText;
  rawMaterial: string;
  processingMethod: string;
  processingMethodCategory: 'thermal_processing' | 'cold_extraction' | 'milling_pulverizing' | 'dehydration_drying' | 'fermentation_pickling';
  fssaiCategory: string;
  rawMaterialToFinishedRatio: number;
  typicalByproducts: Array<{
    name: string;
    yieldRatio: number;
    typicalValuePerKg: number;
    purpose?: string;
  }>;
  shelfLifeAndStorage: BilingualText;
  storageTemperature: string;
  requiredEquipment: Array<{
    machineName: string;
    capacity: string;
    approxCostInr: number;
    purpose: string;
  }>;
  ingredientsAndRecipe: Array<{
    ingredientName: string;
    proportionPercentage: number;
    purpose: string;
    foodGradeGrade: string;
  }>;
  standardOperatingProcedure: Array<{
    stepNumber: number;
    stepTitle: string;
    details: string;
    hygieneStandard: string;
    criticalControlPoint: string;
  }>;
  foodSafetyAndHygiene: BilingualText[];
  packagingGuidance: BilingualText;
  authoritativeReference: {
    institute?: string;
    document?: string;
    verificationUrl?: string;
  };
  potentialSalesChannels: string[];
  trainingProviders: Array<{
    institute: string;
    location: string;
    contact: string;
    email: string;
    courseName: string;
  }>;
}

export interface ValueAdditionCalculationRequest {
  productId: string;
  rawMaterialQuantityKg: number;
  rawMaterialCostPerKg: number;
  yieldLossPercentage?: number;
  processingCostPerKgOrBatch?: number;
  packagingCostPerFinishedUnit?: number;
  finishedUnitSize?: number;
  labourCostTotal?: number;
  transportAndMarketingCost?: number;
  expectedSellingPricePerFinishedUnit: number;
  includeByproductRecovery?: boolean;
  byproductSellingPricePerKg?: number;
}

export interface ValueAdditionCalculationResponse {
  productId: string;
  productName: BilingualText;
  rawMaterialQuantityKg: number;
  effectiveYieldPercent: number;
  yieldLossQuantityKg: number;
  finishedProductQuantity: number;
  finishedUnitsCount: number;
  unitSize: number;
  byproductQuantityKg: number;
  byproductRevenue: number;
  totalExpenses: {
    rawMaterial: number;
    processing: number;
    packaging: number;
    labour: number;
    transport: number;
    total: number;
  };
  finishedProductRevenue: number;
  totalGrossRevenue: number;
  estimatedGrossProfit: number;
  estimatedProfitMarginPercent: number;
  costPerFinishedUnit: number;
  netProfitPerFinishedUnit: number;
  breakevenSellingPricePerUnit: number;
  itemizedAssumptions: string[];
  authoritativeReference: {
    institute?: string;
    document?: string;
    verificationUrl?: string;
  };
  disclaimer: string;
}




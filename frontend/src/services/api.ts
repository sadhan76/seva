import type { 
  InAppNotification, 
  SMSStatusInfo, 
  NotificationPreferences, 
  PushStatusInfo, 
  IrrigationAlertCheckSummary,
  FarmerSupportContent,
  FarmerSupportResponse,
  MarketplaceListing,
  MarketplaceResponse,
  MarketplaceListingCreate,
  MarketplaceListingReportRequest,
  MarketplaceOrderRequestCreate,
  MarketplaceOrderRequest,
  SpecialOperationJourney,
  SpecialOperationStepUpdateRequest,
  SpecialOperationCropRecommendation,
  SpecialOperationCropGuide,
  SpecialOperationTimeline,
  JourneyObservation,
  BusinessIdeaMatchRequest,
  BusinessIdeaMatchResponse,
  BusinessPlanWizardData,
  BusinessPlanCalculationResult,
  BusinessPlanCalculationRequest,
  BusinessPlanModel,
  BusinessPlanCreateRequest,
  BusinessPlanUpdateRequest,
  ValueAdditionProductBlueprint,
  ValueAdditionCalculationRequest,
  ValueAdditionCalculationResponse,
  GeoDistrictItem,
  GeoStateItem,
  GeoMetaResponse,
  Language,
} from '../types';

export type { 
  GeoDistrictItem,
  GeoStateItem,
  GeoMetaResponse,
};

export type { 
  InAppNotification, 
  SMSStatusInfo, 
  NotificationPreferences, 
  PushStatusInfo, 
  IrrigationAlertCheckSummary,
  FarmerSupportContent,
  FarmerSupportResponse,
  MarketplaceListing,
  MarketplaceResponse,
  MarketplaceListingCreate,
  MarketplaceListingReportRequest,
  MarketplaceOrderRequestCreate,
  MarketplaceOrderRequest,
  SpecialOperationJourney,
  SpecialOperationStepUpdateRequest,
  SpecialOperationCropRecommendation,
  SpecialOperationCropGuide,
  SpecialOperationTimeline,
  JourneyObservation,
  BusinessIdeaMatchRequest,
  BusinessIdeaMatchResponse,
  BusinessPlanWizardData,
  BusinessPlanCalculationResult,
  BusinessPlanCalculationRequest,
  BusinessPlanModel,
  BusinessPlanCreateRequest,
  BusinessPlanUpdateRequest,
  ValueAdditionProductBlueprint,
  ValueAdditionCalculationRequest,
  ValueAdditionCalculationResponse,
};

import localGeoDirectory from '../data/indiaGeographicDirectory.json';

const getDefaultApiUrl = (): string => {
  if (typeof window !== 'undefined') {
    // When running inside Vite dev server or browser preview, prefer relative /api proxy
    if (window.location.port === '5173' || window.location.port === '5174') {
      return '/api';
    }
  }
  return 'http://127.0.0.1:8000/api';
};

const rawApiUrl =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  getDefaultApiUrl();
const cleanApiUrl = rawApiUrl.replace(/\/+$/, '');
const API_BASE_URL = cleanApiUrl.endsWith('/api') ? cleanApiUrl : `${cleanApiUrl}/api`;

export interface BackendHealthResponse {
  status: string;
  environment: string;
  timestamp: string;
  database: {
    connected: boolean;
    database_name: string;
    message: string;
  };
}

export interface UserSummary {
  id: string;
  name: string;
  fullName?: string;
  phone: string;
  role: 'farmer' | 'staff';
  preferredLanguage: string;
  country?: string;
  village?: string;
  taluk?: string;
  district?: string;
  districtCode?: string;
  state?: string;
  stateCode?: string;
  mandiName?: string;
  mandiAssigned?: string;
  centreCode?: string;
  farmerId?: string;
  primaryCrop?: string;
  totalLandAcres?: number;
  landUnit?: string;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  aadhaarMasked?: string;
  isAadhaarVerified?: boolean;
  isPhoneVerified?: boolean;
  profilePhoto?: string;
  createdAt: string;
  telegramLinked?: boolean;
  telegramUsername?: string;
  farmCoordinates?: {
    latitude: number;
    longitude: number;
    locationName?: string;
    consentGiven?: boolean;
    updatedAt?: string;
  };
}

export interface AuthTokenResponse {
  accessToken: string;
  tokenType: string;
  expiresInMinutes: number;
  user: UserSummary;
}

export interface FarmerRegisterPayload {
  name: string;
  phone: string;
  country?: string;
  village: string;
  taluk?: string;
  district: string;
  districtCode?: string;
  state: string;
  stateCode?: string;
  preferredLanguage: string;
  password: string;
  confirmPassword: string;
  totalLandAcres: number;
  primaryCrop?: string;
  soilType?: string;
  irrigationSources?: string[];
  irrigationSource?: string;
  otherIrrigationDetail?: string;
}

export interface LoginPayload {
  phone: string;
  password: string;
  role: 'farmer' | 'staff';
}

export interface FarmerProfileInput {
  name: string;
  phone: string;
  country?: string;
  village?: string;
  location: string;
  taluk?: string;
  district?: string;
  districtCode?: string;
  state?: string;
  stateCode?: string;
  totalLandAcres: number;
  landUnit?: string;
  primaryCrop: string;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  preferredLanguage?: string;
  profilePhoto?: string;
  aadhaarMasked?: string;
}

export interface FarmerProfileEntity extends FarmerProfileInput {
  id: string;
  farmerId: string;
  createdAt: string;
}

export interface ProcurementBookingInput {
  farmerName: string;
  farmerId?: string;
  mandiName: string;
  crop: string;
  cropVariety?: string;
  harvestDate: string;
  quantityBags: number;
  preferredDate: string;
  slotDate?: string;
  timeWindow?: string;
}

export interface ProcurementCentreInfo {
  id: string;
  centreCode: string;
  name: string;
  nameTa: string;
  district: string;
  taluk: string;
  locationAddress: string;
  supportedCrops: string[];
  operatingHours: string;
  dailyCapacityBags: number;
  slotCapacityBags: number;
  slotWindows: string[];
  isDemoData: boolean;
  dataSourceLabel: string;
}

export interface SlotStatusInfo {
  timeWindow: string;
  maxCapacityBags: number;
  bookedBags: number;
  availableBags: number;
  status: 'available' | 'filling_fast' | 'full' | 'closed';
  isClosed?: boolean;
  closureReason?: string | null;
}

export interface CentreSlotsResponse {
  centreCode: string;
  centreName: string;
  date: string;
  totalDailyCapacityBags: number;
  slots: SlotStatusInfo[];
}

export interface TokenVerifyResponse {
  isValid: boolean;
  status: string;
  bookingId: string;
  tokenNumber: string;
  farmerName: string;
  farmerId: string;
  mandiName: string;
  crop: string;
  quantityBags: number;
  estimatedWeightQuintals: number;
  slotDate: string;
  timeWindow: string;
  canCheckIn: boolean;
  canWeigh: boolean;
  message: string;
  disclaimer: string;
}

export interface AuditLogEntry {
  action: string;
  by: string;
  role: string;
  timestamp: string;
  notes?: string;
}

export interface WeighingTransactionDetails {
  actualNetWeightQuintals: number;
  pricePerQuintal: number;
  moisturePercent: number;
  moistureDeductionAmount: number;
  otherDeductionsAmount: number;
  totalDeductionsAmount: number;
  grossAmount: number;
  netPayableAmount: number;
  paymentStatus: 'PENDING' | 'PROCESSING' | 'PAID';
  paymentMethod: string;
  disclaimer: string;
  weighedAt: string;
  weighedByStaff: string;
  notes?: string;
}

export interface QueueStageDetail {
  stageNumber: number;
  code: string;
  name: string;
  nameTa: string;
  state: 'done' | 'current' | 'pending' | 'cancelled';
}

export interface QueueTrackingResponse {
  bookingId: string;
  tokenNumber: string;
  status: string;
  mandiName: string;
  centreCode?: string;
  slotDate: string;
  timeWindow: string;
  farmerName: string;
  crop: string;
  cropVariety?: string;
  harvestDate?: string;
  quantityBags?: number;
  vehiclesAhead: number | null;
  queuePosition: number | null;
  estimatedWaitMinutes: number | null;
  hasSufficientDataForEstimate: boolean;
  waitingTimeDisplay?: string;
  isInActiveQueue?: boolean;
  currentStageNumber: number;
  stages: QueueStageDetail[];
  transaction?: WeighingTransactionDetails | null;
  auditHistory: AuditLogEntry[];
  lastPolledAt: string;
  isDemoData: boolean;
  qualityInspection?: {
    qualityStatus?: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
    status?: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
    qualityGrade: string;
    moisturePercent: number;
    declaredWeightKg?: number;
    acceptedWeightKg: number;
    rejectedWeightKg: number;
    rejectionReason?: string;
    notes?: string;
    inspectedAt?: string;
    inspectedByStaff?: string;
  };
  isNowServing?: boolean;
  nowServingToken?: string;
  counterId?: string | null;
  counterName?: string | null;
  counters?: CounterInfo[];
}

export interface StaffTransactionPayload {
  actualNetWeightQuintals?: number;
  acceptedWeightKg?: number;
  pricePerQuintal?: number;
  pricePerKg?: number;
  moisturePercent?: number;
  qualityGrade?: string;
  qualityDeductionsAmount?: number;
  otherDeductionsAmount?: number;
  customDeductionsAmount?: number;
  paymentStatus?: 'PENDING' | 'PROCESSING' | 'PAID';
  notes?: string;
}

export interface StaffWeighingPayload {
  acceptedWeightKg: number;
  pricePerKg: number;
  qualityDeductionsAmount?: number;
  otherDeductionsAmount?: number;
  qualityGrade?: string;
  paymentStatus?: 'PENDING' | 'PROCESSING' | 'PAID';
  notes?: string;
}

export interface WeighingCalculationPreview {
  acceptedWeightKg: number;
  pricePerKg: number;
  grossAmount: number;
  qualityDeductionsAmount: number;
  otherDeductionsAmount: number;
  totalDeductionsAmount: number;
  netAmount: number;
  isValid: boolean;
  validationError?: string;
}

export interface DigitalBillEntity {
  id?: string;
  billNumber: string;
  bookingId: string;
  tokenNumber?: string;
  farmerName: string;
  farmerId: string;
  mandiName: string;
  crop: string;
  acceptedWeightKg: number;
  actualNetWeightQuintals: number;
  pricePerKg: number;
  pricePerQuintal: number;
  grossAmount: number;
  qualityDeductionsAmount: number;
  otherDeductionsAmount: number;
  totalDeductionsAmount: number;
  netAmount: number;
  netPayableAmount?: number;
  paymentStatus: 'PENDING' | 'PROCESSING' | 'PAID';
  paymentMethod: string;
  transactionDate: string;
  weighedAt?: string;
  weighedByStaff: string;
  notes?: string;
  paymentHistory?: Array<{
    status: string;
    updatedBy: string;
    role: string;
    timestamp: string;
    notes?: string;
    transactionReference?: string;
  }>;
  auditHistory?: Array<{
    action: string;
    by: string;
    role: string;
    timestamp: string;
    notes?: string;
  }>;
  disclaimer?: string;
  createdAt?: string;
  acceptedWeightQuintals?: number;
  totalDeductions?: number;
}

export interface ProcurementBookingEntity {
  id: string;
  bookingId: string;
  tokenNumber: string;
  opaqueToken?: string;
  qrVerificationUrl?: string;
  farmerName: string;
  farmerId: string;
  mandiName: string;
  crop: string;
  cropVariety?: string;
  harvestDate?: string;
  quantityBags: number;
  estimatedWeightQuintals: number;
  slotDate: string;
  timeWindow: string;
  status: string;
  moisturePercent?: number;
  actualNetWeightQuintals?: number;
  acceptedWeightKg?: number;
  qualityNotes?: string;
  qualityInspection?: {
    qualityStatus: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
    status?: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
    qualityGrade: string;
    moisturePercent: number;
    declaredWeightKg: number;
    acceptedWeightKg: number;
    rejectedWeightKg: number;
    rejectionReason?: string;
    notes?: string;
    inspectedAt: string;
    inspectedByStaff: string;
  };
  noShowDetails?: {
    markedAt: string;
    markedByStaff: string;
    markedByStaffName?: string;
    reason: string;
  };
  isNowServing?: boolean;
  rateSourceLabel?: string;
  billNumber?: string;
  bill?: DigitalBillEntity | null;
  transaction?: WeighingTransactionDetails | null;
  auditHistory?: AuditLogEntry[];
  createdAt: string;
}

export interface QualityInspectionPayload {
  qualityStatus: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED';
  qualityGrade?: string;
  moisturePercent: number;
  declaredWeightKg?: number;
  acceptedWeightKg?: number;
  rejectedWeightKg?: number;
  rejectionReason?: string;
  notes?: string;
}

export interface ProcurementRateItem {
  id?: string;
  crop: string;
  cropVariety: string;
  centreCode: string;
  ratePerKg: number;
  ratePerQuintal: number;
  effectiveDate: string;
  isActive: boolean;
  sourceLabel: string;
  rateSourceLabel?: string;
  notes?: string;
  createdAt?: string;
}

export interface CounterInfo {
  counterId: string;
  name: string;
  isActive: boolean;
  isNowServing: boolean;
  currentBookingId?: string | null;
  currentToken?: string | null;
  farmerName?: string | null;
  crop?: string | null;
  lastCalledAt?: string | null;
}

export interface NowServingResponse {
  centreCode: string;
  centreName: string;
  date: string;
  counterId: string;
  counterName?: string;
  counters?: CounterInfo[];
  currentServing?: {
    bookingId: string;
    tokenNumber: string;
    farmerName: string;
    crop: string;
    cropVariety?: string;
    quantityBags: number;
    status: string;
    timeWindow?: string;
    nowServingCalledAt?: string;
  } | null;
  currentToken?: {
    bookingId: string;
    tokenNumber: string;
    farmerName: string;
    crop: string;
    cropVariety?: string;
    quantityBags: number;
    status: string;
    timeWindow?: string;
    nowServingCalledAt?: string;
  } | null;
  nextEligible?: {
    bookingId: string;
    tokenNumber: string;
    farmerName: string;
    crop: string;
    cropVariety?: string;
    quantityBags: number;
    status: string;
    timeWindow?: string;
  } | null;
  nextEligibleToken?: {
    bookingId: string;
    tokenNumber: string;
    farmerName: string;
    crop: string;
    cropVariety?: string;
    quantityBags: number;
    status: string;
    timeWindow?: string;
  } | null;
  calledToken?: {
    bookingId: string;
    tokenNumber: string;
    farmerName: string;
    crop: string;
    cropVariety?: string;
    quantityBags: number;
    status: string;
    timeWindow?: string;
  };
  activeWaitingCount: number;
  lastCalledAt?: string | null;
}

export interface StaffQueueOverviewResponse {
  staffName: string;
  mandiName: string;
  centreCode?: string;
  selectedDate?: string;
  selectedTimeWindow?: string;
  totalBookings: number;
  totalBagsRegistered: number;
  queueStatus: {
    vehiclesWaiting: number;
    vehiclesProcessing: number;
    weighedCompleted: number;
    weighbridgeOperational: boolean;
  };
  checkedIn?: ProcurementBookingEntity[];
  inQueue?: ProcurementBookingEntity[];
  processing?: ProcurementBookingEntity[];
  completed?: ProcurementBookingEntity[];
  booked?: ProcurementBookingEntity[];
  cancelled?: ProcurementBookingEntity[];
  activeQueue?: ProcurementBookingEntity[];
  bookings: ProcurementBookingEntity[];
  lastUpdated?: string;
}

export interface StaffBookingStatusUpdatePayload {
  status: 'confirmed' | 'quality_checked' | 'weighed' | 'dbt_completed' | 'cancelled';
  moisturePercent?: number;
  actualNetWeightQuintals?: number;
  qualityNotes?: string;
}


export async function safeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (err: any) {
    if (
      err.name === 'TypeError' ||
      err.message?.includes('fetch') ||
      err.message?.includes('NetworkError') ||
      err.message?.includes('Failed to fetch')
    ) {
      throw new Error(
        'Unable to connect to AgriBharat server. Please ensure the backend is running on http://127.0.0.1:8000.'
      );
    }
    throw err;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

/**
 * Check backend API health and real MongoDB connectivity status
 */
export async function checkBackendHealth(): Promise<BackendHealthResponse> {
  const res = await safeFetch(`${API_BASE_URL}/health`);
  return handleResponse<BackendHealthResponse>(res);
}

// ============================================================================
// GEOGRAPHIC DIRECTORY APIS (ALL 36 REGIONS, 788 DISTRICTS)
// ============================================================================

export async function getGeoMetaApi(): Promise<GeoMetaResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/geo/meta`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Network fallback
  }
  const geo = localGeoDirectory as any;
  return {
    version: geo.version,
    lastUpdated: geo.lastUpdated,
    source: geo.source,
    license: geo.license,
    totalRegions: geo.totalRegions,
    statesCount: geo.statesCount,
    unionTerritoriesCount: geo.unionTerritoriesCount,
    totalDistricts: geo.totalDistricts,
    notes: geo.notes,
  };
}

export async function getStatesApi(): Promise<GeoStateItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/geo/states`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.states) && data.states.length > 0) {
        return data.states;
      }
    }
  } catch {
    // Network fallback
  }
  return (localGeoDirectory.states as any[]).map((s) => ({
    id: s.id,
    code: s.code,
    name: s.name,
    type: s.type,
    localNames: s.localNames || {},
    districtsCount: s.districtsCount || (s.districts ? s.districts.length : 0),
  }));
}

export async function getDistrictsApi(stateQuery: string): Promise<GeoDistrictItem[]> {
  if (!stateQuery || !stateQuery.trim()) return [];
  try {
    const res = await fetch(`${API_BASE_URL}/geo/districts?state=${encodeURIComponent(stateQuery.trim())}`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.districts)) {
        return data.districts;
      }
    }
  } catch {
    // Network fallback
  }
  const clean = stateQuery.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  const matched = (localGeoDirectory.states as any[]).find((s) => {
    const sId = (s.id || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    const sCode = (s.code || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    const sName = (s.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    return clean === sId || clean === sCode || clean === sName;
  });
  return (matched?.districts as GeoDistrictItem[]) || [];
}

export async function searchGeoLocationsApi(
  query: string,
  stateQuery?: string
): Promise<{ states: GeoStateItem[]; districts: GeoDistrictItem[] }> {
  try {
    let url = `${API_BASE_URL}/geo/search?q=${encodeURIComponent(query)}`;
    if (stateQuery) {
      url += `&state=${encodeURIComponent(stateQuery)}`;
    }
    const res = await fetch(url);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Network fallback
  }
  const qClean = query.trim().toLowerCase();
  const matchedStates = (localGeoDirectory.states as any[])
    .filter((s) => s.name.toLowerCase().includes(qClean) || (s.code && s.code.toLowerCase().includes(qClean)))
    .map((s) => ({
      id: s.id,
      code: s.code,
      name: s.name,
      type: s.type,
      localNames: s.localNames || {},
      districtsCount: s.districtsCount || (s.districts ? s.districts.length : 0),
    }));

  let poolDistricts: GeoDistrictItem[] = [];
  if (stateQuery) {
    const cleanState = stateQuery.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const st = (localGeoDirectory.states as any[]).find((s) => {
      const sId = (s.id || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const sCode = (s.code || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const sName = (s.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      return cleanState === sId || cleanState === sCode || cleanState === sName;
    });
    if (st && st.districts) poolDistricts = st.districts;
  } else {
    for (const st of localGeoDirectory.states as any[]) {
      if (st.districts) poolDistricts.push(...st.districts);
    }
  }
  const matchedDistricts = poolDistricts.filter(
    (d) => d.name.toLowerCase().includes(qClean) || (d.code && d.code.toLowerCase().includes(qClean))
  );
  return { states: matchedStates, districts: matchedDistricts.slice(0, 50) };
}

// ============================================================================
// AUTHENTICATION APIS (PHASE 3)
// ============================================================================

function normalizeUser(u: UserSummary): UserSummary {
  return {
    ...u,
    fullName: u.name || u.fullName || '',
    mandiAssigned: u.mandiName || u.mandiAssigned || '',
    landUnit: u.landUnit || 'Acres',
  };
}

/**
 * Register a new farmer account
 */
export async function registerFarmerApi(data: FarmerRegisterPayload): Promise<AuthTokenResponse> {
  const res = await safeFetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const dataRes = await handleResponse<AuthTokenResponse>(res);
  return {
    ...dataRes,
    user: normalizeUser(dataRes.user),
  };
}

/**
 * Login with mobile, password, and role
 */
export async function loginApi(data: LoginPayload): Promise<AuthTokenResponse> {
  const res = await safeFetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const dataRes = await handleResponse<AuthTokenResponse>(res);
  return {
    ...dataRes,
    user: normalizeUser(dataRes.user),
  };
}

/**
 * Fetch current authenticated user's profile using JWT
 */
export async function getMeApi(token: string): Promise<UserSummary> {
  const res = await safeFetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  const u = await handleResponse<UserSummary>(res);
  return normalizeUser(u);
}

// ============================================================================
// AGRICULTURAL & BOOKING APIS
// ============================================================================

export async function getFarmers(): Promise<FarmerProfileEntity[]> {
  const res = await fetch(`${API_BASE_URL}/farmers`);
  return handleResponse<FarmerProfileEntity[]>(res);
}

export async function createFarmer(data: FarmerProfileInput, token?: string | null): Promise<FarmerProfileEntity> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/farmers`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  return handleResponse<FarmerProfileEntity>(res);
}

export async function updateFarmerProfileApi(
  data: FarmerProfileInput,
  token?: string | null
): Promise<UserSummary> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/farmers/me`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });
  const u = await handleResponse<UserSummary>(res);
  return normalizeUser(u);
}

export async function getMyFarmerProfileApi(token: string): Promise<UserSummary> {
  const res = await fetch(`${API_BASE_URL}/farmers/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  const u = await handleResponse<UserSummary>(res);
  return normalizeUser(u);
}

export async function uploadProfilePhotoApi(
  file: File,
  token?: string | null
): Promise<{ status: string; message: string; profilePhoto: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/users/me/avatar`, {
    method: 'POST',
    headers,
    body: formData,
  });
  return handleResponse<{ status: string; message: string; profilePhoto: string }>(res);
}

export async function updateUserLanguageApi(
  language: string,
  token?: string | null
): Promise<{ status: string; preferredLanguage: string; user: UserSummary }> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/users/me/language`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ preferredLanguage: language }),
  });
  return handleResponse<{ status: string; preferredLanguage: string; user: UserSummary }>(res);
}

export async function getProcurementBookings(token?: string | null): Promise<ProcurementBookingEntity[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/procurement/bookings`, { headers });
  return handleResponse<ProcurementBookingEntity[]>(res);
}

export async function createProcurementBooking(
  data: ProcurementBookingInput,
  token?: string | null
): Promise<ProcurementBookingEntity> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/procurement/bookings`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

// ============================================================================
// PHASE 5: SMART PROCUREMENT TRACKING APIS
// ============================================================================

export async function getProcurementCentres(): Promise<ProcurementCentreInfo[]> {
  const res = await fetch(`${API_BASE_URL}/procurement/centres`);
  return handleResponse<ProcurementCentreInfo[]>(res);
}

export async function getProcurementSlots(centreId: string, date: string): Promise<CentreSlotsResponse> {
  const res = await fetch(`${API_BASE_URL}/procurement/centres/${encodeURIComponent(centreId)}/slots?date=${encodeURIComponent(date)}`);
  return handleResponse<CentreSlotsResponse>(res);
}

export async function getQueueTracking(bookingId: string, token?: string): Promise<QueueTrackingResponse> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/procurement/queue/${encodeURIComponent(bookingId)}`, {
    headers,
  });
  return handleResponse<QueueTrackingResponse>(res);
}

export async function verifyStaffTokenApi(
  payload: { token?: string; bookingId?: string },
  staffToken: string
): Promise<TokenVerifyResponse> {
  const res = await fetch(`${API_BASE_URL}/staff/verify-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<TokenVerifyResponse>(res);
}

export async function staffCheckInApi(
  bookingId: string,
  notes: string | undefined,
  staffToken: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/checkin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({ notes }),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

export async function staffRecordTransactionApi(
  bookingId: string,
  payload: StaffTransactionPayload,
  staffToken: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/transaction`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

export async function previewWeighingCalculationApi(payload: {
  acceptedWeightKg: number;
  pricePerKg: number;
  qualityDeductionsAmount?: number;
  otherDeductionsAmount?: number;
}): Promise<WeighingCalculationPreview> {
  const res = await fetch(`${API_BASE_URL}/staff/weighing/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<WeighingCalculationPreview>(res);
}

export async function staffRecordWeighingApi(
  bookingId: string,
  payload: StaffWeighingPayload,
  staffToken: string
): Promise<DigitalBillEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/weighing`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<DigitalBillEntity>(res);
}

export async function getDigitalBillApi(
  billId: string,
  token: string
): Promise<DigitalBillEntity> {
  const res = await fetch(`${API_BASE_URL}/procurement/bills/${encodeURIComponent(billId)}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<DigitalBillEntity>(res);
}

export async function getFarmerBillsApi(
  token: string
): Promise<{ total: number; bills: DigitalBillEntity[] }> {
  const res = await fetch(`${API_BASE_URL}/procurement/my-bills`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ total: number; bills: DigitalBillEntity[] }>(res);
}

export async function getStaffBillsApi(
  token: string,
  filters?: { date?: string; statusFilter?: string }
): Promise<{ total: number; bills: DigitalBillEntity[] }> {
  const params = new URLSearchParams();
  if (filters?.date) params.set('date', filters.date);
  if (filters?.statusFilter && filters.statusFilter !== 'all') params.set('statusFilter', filters.statusFilter);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/staff/bills${qs}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ total: number; bills: DigitalBillEntity[] }>(res);
}

export async function staffUpdatePaymentStatusApi(
  billNumberOrBookingId: string,
  payload: { newStatus: 'PENDING' | 'PROCESSING' | 'PAID'; notes?: string; transactionReference?: string },
  token: string
): Promise<DigitalBillEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bills/${encodeURIComponent(billNumberOrBookingId)}/payment-status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<DigitalBillEntity>(res);
}


export async function getNotificationsApi(token?: string | null, unreadOnly?: boolean): Promise<InAppNotification[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const url = unreadOnly ? `${API_BASE_URL}/notifications?unread_only=true` : `${API_BASE_URL}/notifications`;
  const res = await fetch(url, { headers });
  return handleResponse<InAppNotification[]>(res);
}

export async function markNotificationReadApi(notificationId: string, token?: string | null): Promise<{ success: boolean; notificationId: string }> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/notifications/${encodeURIComponent(notificationId)}/read`, {
    method: 'PATCH',
    headers,
  });
  return handleResponse<{ success: boolean; notificationId: string }>(res);
}

export async function markAllNotificationsReadApi(token: string): Promise<{ success: boolean; markedCount: number; message: string }> {
  const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<{ success: boolean; markedCount: number; message: string }>(res);
}

export async function getUnreadNotificationsCountApi(token: string): Promise<{ unreadCount: number }> {
  const res = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<{ unreadCount: number }>(res);
}

export async function getSmsGatewayStatusApi(token: string): Promise<SMSStatusInfo> {
  const res = await fetch(`${API_BASE_URL}/notifications/sms-status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<SMSStatusInfo>(res);
}

export async function getNotificationPreferencesApi(token: string): Promise<NotificationPreferences> {
  const res = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<NotificationPreferences>(res);
}

export async function updateNotificationPreferencesApi(
  token: string,
  updates: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  const res = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  return handleResponse<NotificationPreferences>(res);
}

export async function getPushStatusApi(token: string): Promise<PushStatusInfo> {
  const res = await fetch(`${API_BASE_URL}/notifications/push-status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<PushStatusInfo>(res);
}

export async function savePushSubscriptionApi(
  token: string,
  subscriptionPayload: { endpoint: string; keys: Record<string, string>; expirationTime?: number | null }
): Promise<{ success: boolean; message: string; data?: any }> {
  const res = await fetch(`${API_BASE_URL}/notifications/push-subscription`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(subscriptionPayload),
  });
  return handleResponse<{ success: boolean; message: string; data?: any }>(res);
}

export async function deletePushSubscriptionApi(token: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/notifications/push-subscription`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

export async function triggerIrrigationCheckApi(token: string): Promise<IrrigationAlertCheckSummary> {
  const res = await fetch(`${API_BASE_URL}/notifications/irrigation-check`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<IrrigationAlertCheckSummary>(res);
}

export async function triggerMandiCheckApi(token: string): Promise<{ success: boolean; syncResult?: any; notificationSummary?: any }> {
  const res = await fetch(`${API_BASE_URL}/notifications/mandi-check`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse<{ success: boolean; syncResult?: any; notificationSummary?: any }>(res);
}


// ============================================================================
// STAFF PROCUREMENT CENTRE OPERATIONS
// ============================================================================

export async function getStaffQueueApi(
  token: string,
  filters?: { centreCode?: string; mandiName?: string; date?: string; timeWindow?: string; statusFilter?: string }
): Promise<StaffQueueOverviewResponse> {
  const params = new URLSearchParams();
  if (filters?.centreCode) params.set('centreCode', filters.centreCode);
  if (filters?.mandiName) params.set('mandiName', filters.mandiName);
  if (filters?.date) params.set('date', filters.date);
  if (filters?.timeWindow && filters.timeWindow !== 'all') params.set('timeWindow', filters.timeWindow);
  if (filters?.statusFilter && filters.statusFilter !== 'all') params.set('statusFilter', filters.statusFilter);

  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/staff/queue${qs}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<StaffQueueOverviewResponse>(res);
}

export async function staffUpdateStatusApi(
  bookingId: string,
  payload: { newStatus: string; notes?: string },
  token: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

export async function updateBookingStatusByStaffApi(
  bookingId: string,
  payload: StaffBookingStatusUpdatePayload,
  token: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${bookingId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * FEATURE 6: Farmer's own booking history (strict ownership enforced on backend)
 */
export interface FarmerBookingHistoryResponse {
  farmerId: string;
  farmerName: string;
  totalBookings: number;
  bookings: ProcurementBookingEntity[];
}

export async function getMyBookingsApi(token: string): Promise<FarmerBookingHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/procurement/my-bookings`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return handleResponse<FarmerBookingHistoryResponse>(res);
}

/**
 * FEATURE 4: Staff moves booking to IN_QUEUE (yard queue assigned)
 */
export async function staffMoveToQueueApi(bookingId: string, staffToken: string): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/queue`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({}),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * FEATURE 4: Staff moves booking to PROCESSING (on the weighbridge)
 */
export async function staffMoveToProcessingApi(bookingId: string, staffToken: string): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/processing`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({}),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * FEATURE 4: Staff cancels a booking with audit trail
 */
export async function staffCancelBookingApi(bookingId: string, staffToken: string): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/cancel`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({}),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * PHASE 3: Staff records physical quality inspection
 */
export async function staffQualityInspectionApi(
  bookingId: string,
  payload: QualityInspectionPayload,
  staffToken: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/quality-inspection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * PHASE 3: Staff marks an unadmitted booking as NO_SHOW
 */
export async function staffNoShowApi(
  bookingId: string,
  reason: string | undefined,
  staffToken: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/bookings/${encodeURIComponent(bookingId)}/no-show`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({ reason }),
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

/**
 * PHASE 3: Fetch active configured procurement rates
 */
export async function getProcurementRatesApi(
  crop?: string,
  centreCode?: string
): Promise<ProcurementRateItem[]> {
  const params = new URLSearchParams();
  if (crop) params.set('crop', crop);
  if (centreCode && centreCode !== 'ALL') params.set('centreCode', centreCode);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/procurement/rates${qs}`);
  return handleResponse<ProcurementRateItem[]>(res);
}

/**
 * PHASE 3: Staff creates or updates rate configuration
 */
export async function createProcurementRateApi(
  payload: Partial<ProcurementRateItem>,
  staffToken: string
): Promise<ProcurementRateItem> {
  const res = await fetch(`${API_BASE_URL}/staff/rates`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProcurementRateItem>(res);
}

/**
 * PHASE 3: Get live Now Serving token and next eligible waiting vehicle
 */
export interface CropReportSummary {
  crop: string;
  totalBags?: number;
  totalBookings?: number;
  acceptedWeightKg: number;
  acceptedWeightQuintals: number;
  rejectedWeightKg: number;
  totalTransactions?: number;
  completedCount?: number;
  grossAmount?: number;
  grossValue?: number;
  netPayable?: number;
  netAmount?: number;
}

export interface CounterThroughputSummary {
  counterId: string;
  counterName: string;
  tokensServed?: number;
  completedCount?: number;
  completedBookings?: number;
  totalAcceptedWeightKg?: number;
  totalWeightKg: number;
  grossAmount?: number;
}

export interface DailyProcurementReportResponse {
  centreCode: string;
  centreName: string;
  date?: string;
  reportDate?: string;
  filterCrop?: string | null;
  filterPaymentStatus?: string | null;
  totalBookings: number;
  cancelledBookings?: number;
  cancelledCount?: number;
  noShowBookings?: number;
  noShowCount?: number;
  cancelledAndNoShowBookings?: number;
  completedTransactions?: number;
  completedCount?: number;
  totalEstimatedBags?: number;
  totalAcceptedWeightKg: number;
  totalAcceptedWeightQuintals: number;
  totalRejectedWeightKg: number;
  totalGrossAmount?: number;
  totalGrossTransactionValue?: number;
  totalDeductions?: number;
  totalDeductionsAmount?: number;
  totalNetPayable?: number;
  totalNetAmount?: number;
  amountPending: number;
  amountProcessing: number;
  amountPaid: number;
  paymentBreakdown?: {
    pendingAmount: number;
    pendingCount: number;
    processingAmount: number;
    processingCount: number;
    paidAmount: number;
    paidCount: number;
  };
  cropBreakdown: CropReportSummary[];
  counterThroughput: CounterThroughputSummary[];
  generatedAt: string;
  generatedByStaff?: string;
}

export interface SlotClosureEntity {
  id?: string;
  centreCode: string;
  slotDate: string;
  timeWindow: string;
  isClosed?: boolean;
  isActive?: boolean;
  closureReason: string;
  reason?: string;
  closedByStaffName?: string;
  closedByStaff?: string;
  closedBy?: string;
  closedAt?: string;
  reopenedByStaffName?: string;
  reopenedByStaff?: string;
  reopenedAt?: string;
}

export interface FarmerQuotaCheckResponse {
  farmerId: string;
  date: string;
  timeWindow?: string | null;
  maxBagsPerSlot: number;
  maxBagsPerDay: number;
  bookedBagsToday: number;
  bookedBagsSlot: number;
  remainingBagsToday: number;
  remainingBagsSlot: number;
  canBook: boolean;
  reason?: string | null;
}

export interface ProcurementCentreItem {
  id?: string;
  centreCode: string;
  name: string;
  nameTa?: string;
  district: string;
  taluk?: string;
  locationAddress?: string;
  address?: string;
  contactNumber?: string;
  operatingHours?: string;
  dailyCapacityBags: number;
  slotCapacityBags?: number;
  supportedCrops: string[];
  slotWindows?: string[];
  counters?: CounterInfo[];
  isActive: boolean;
  statusChangeReason?: string;
  deactivationReason?: string | null;
}

/**
 * PHASE 3 & 4: Get live Now Serving token and next eligible waiting vehicle per counter
 */
export async function getNowServingApi(
  centreCode: string,
  date?: string,
  counterId?: string
): Promise<NowServingResponse> {
  const params = new URLSearchParams({ centreCode });
  if (date) params.set('date', date);
  if (counterId) params.set('counterId', counterId);
  const res = await fetch(`${API_BASE_URL}/procurement/now-serving?${params.toString()}`);
  return handleResponse<NowServingResponse>(res);
}

/**
 * PHASE 3 & 4: Staff calls next eligible token from FIFO queue with atomic concurrency
 */
export async function staffCallNextTokenApi(
  payload: { centreCode: string; date?: string; counterId?: string },
  staffToken: string
): Promise<NowServingResponse> {
  const res = await fetch(`${API_BASE_URL}/staff/queue/call-next`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<NowServingResponse>(res);
}

/**
 * PHASE 4: Staff Daily Procurement Report
 */
export async function getDailyProcurementReportApi(
  params: { centreCode: string; date?: string; crop?: string; paymentStatus?: string },
  staffToken: string
): Promise<DailyProcurementReportResponse> {
  const search = new URLSearchParams({ centreCode: params.centreCode });
  if (params.date) search.set('date', params.date);
  if (params.crop) search.set('crop', params.crop);
  if (params.paymentStatus) search.set('paymentStatus', params.paymentStatus);
  const res = await fetch(`${API_BASE_URL}/staff/reports/daily?${search.toString()}`, {
    headers: { Authorization: `Bearer ${staffToken}` }
  });
  return handleResponse<DailyProcurementReportResponse>(res);
}

/**
 * PHASE 4: Slot Closure Management
 */
export async function closeSlotApi(
  payload: { centreCode: string; slotDate: string; timeWindow: string; reason: string },
  staffToken: string
): Promise<SlotClosureEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/slots/close`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<SlotClosureEntity>(res);
}

export async function reopenSlotApi(
  payload: { centreCode: string; slotDate: string; timeWindow: string },
  staffToken: string
): Promise<SlotClosureEntity> {
  const res = await fetch(`${API_BASE_URL}/staff/slots/reopen`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<SlotClosureEntity>(res);
}

export async function getSlotClosuresApi(
  centreCode: string,
  date?: string,
  staffToken?: string
): Promise<{ centreCode: string; closures: SlotClosureEntity[] }> {
  const search = new URLSearchParams({ centreCode });
  if (date) search.set('date', date);
  const headers: Record<string, string> = {};
  if (staffToken) headers['Authorization'] = `Bearer ${staffToken}`;
  const res = await fetch(`${API_BASE_URL}/staff/slots/closures?${search.toString()}`, { headers });
  return handleResponse<{ centreCode: string; closures: SlotClosureEntity[] }>(res);
}

/**
 * PHASE 4: Farmer Quota / Quantity Limit Check
 */
export async function getFarmerQuotaApi(
  farmerId: string,
  date: string,
  timeWindow?: string
): Promise<FarmerQuotaCheckResponse> {
  const search = new URLSearchParams({ farmerId, date });
  if (timeWindow) search.set('timeWindow', timeWindow);
  const res = await fetch(`${API_BASE_URL}/procurement/farmer-quota?${search.toString()}`);
  return handleResponse<FarmerQuotaCheckResponse>(res);
}

/**
 * PHASE 4: Procurement Centre Master Data Management
 */
export async function createProcurementCentreApi(
  data: Partial<ProcurementCentreItem>,
  staffToken: string
): Promise<ProcurementCentreItem> {
  const res = await fetch(`${API_BASE_URL}/staff/centres`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(data),
  });
  return handleResponse<ProcurementCentreItem>(res);
}

export async function updateProcurementCentreApi(
  centreCode: string,
  data: Partial<ProcurementCentreItem>,
  staffToken: string
): Promise<ProcurementCentreItem> {
  const res = await fetch(`${API_BASE_URL}/staff/centres/${encodeURIComponent(centreCode)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify(data),
  });
  return handleResponse<ProcurementCentreItem>(res);
}

export async function setProcurementCentreStatusApi(
  centreCode: string,
  isActive: boolean,
  reason: string,
  staffToken: string
): Promise<ProcurementCentreItem> {
  const res = await fetch(`${API_BASE_URL}/staff/centres/${encodeURIComponent(centreCode)}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${staffToken}`,
    },
    body: JSON.stringify({ isActive, reason }),
  });
  return handleResponse<ProcurementCentreItem>(res);
}


// ============================================================================
// PHASE 4: SMART FARMING INTELLIGENCE APIS
// ============================================================================

export interface WeatherDistrict {
  key: string;
  name: string;
  nameTa: string;
  zone: string;
}

export interface WeatherForecastDay {
  day: string;
  day_ta?: string;
  date?: string;
  fullDate?: string;
  temp: string;
  tempMax?: number;
  tempMin?: number;
  condition: string;
  condition_ta?: string;
  weatherCode?: number;
  weatherIcon?: string;
  rainProb: number;
  precipMm?: number;
}

export interface SprayingAdvisory {
  status: 'optimal' | 'caution' | 'warning' | 'not_recommended';
  title_en: string;
  title_ta: string;
  reason_en: string;
  reason_ta: string;
  favorable_window: string;
  disclaimer_en?: string;
  disclaimer_ta?: string;
}

export interface WeatherApiResponse {
  district: string;
  district_ta: string;
  zone: string;
  coordinates?: { lat: number; lon: number };
  temperatureC: number;
  condition: string;
  condition_ta: string;
  weatherCode?: number;
  weatherIcon?: string;
  humidity: number;
  rainfallChance: number;
  windSpeedKmh: number;
  observationTime?: string;
  lastUpdated?: string;
  updatedAt: string;
  isLive: boolean;
  isCached?: boolean;
  cacheNotice?: string;
  source: string;
  sprayingAdvisory: SprayingAdvisory;
  forecast: WeatherForecastDay[];
  error?: string;
}

export interface IrrigationWeatherResponse {
  coordinates: { lat: number; lon: number };
  timezone: string;
  source: string;
  forecastHorizon: string;
  units: {
    temperature: string;
    humidity: string;
    precipitation: string;
    rain: string;
    et0: string;
    soilMoisture: string;
  };
  current: {
    temperatureC: number | null;
    humidity: number | null;
    precipitationMm: number | null;
    rainMm: number | null;
    weatherCode: number;
    condition: string;
    conditionTa: string;
    weatherIcon: string;
    observationTime: string;
  } | null;
  precipitationProbability: number | null;
  precipitationSumMm: number | null;
  et0EstimateMmDay: number | null;
  soilMoisture: {
    available: boolean;
    rootZonePercent: number | null;
    displayLabel: string;
    depth0To7cmPercent: number | null;
    depth7To28cmPercent: number | null;
    depth28To100cmPercent: number | null;
    disclaimer: string;
    disclaimerTa: string;
  };
  lastUpdated: string;
  lastUpdatedIso: string;
  isLive: boolean;
  isCached: boolean;
  isStale: boolean;
  cacheAgeSeconds?: number;
  warning?: string;
  error?: string;
}

export interface FarmLocationInput {
  latitude: number;
  longitude: number;
  locationName?: string;
  consent: boolean;
}

export interface IrrigationCalculateInput {
  crop: string;
  growthStage: string;
  soilType: string;
  irrigationMethod: string;
  fieldAreaAcres?: number;
  latitude?: number;
  longitude?: number;
  soilMoisturePercent?: number;
  recentRainMm?: number;
  forecastRainChance?: number;
}

export interface IrrigationCalculateResponse {
  crop: string;
  growthStage: string;
  soilType: string;
  irrigationMethod: string;
  recommendation?: 'irrigate_now' | 'delay_reassess' | 'monitor_conditions';
  status: 'delay' | 'adequate' | 'urgent' | 'moderate';
  recommendationTitleEn?: string;
  recommendationTitleTa?: string;
  recommendationEn: string;
  recommendationTa: string;
  irrigationWindowEn?: string;
  irrigationWindowTa?: string;
  referenceEtoMmDay?: number;
  cropWaterDemandMm: number;
  cropFactorKc: number;
  fieldAreaAcres?: number;
  effectiveRainfallMm?: number;
  netIrrigationRequirementMm?: number;
  grossIrrigationRequirementMm?: number | null;
  estimatedLitersPerAcre: number;
  totalEstimatedLiters?: number | null;
  isWaterVolumeEstimated?: boolean;
  unitExplanationEn?: string;
  unitExplanationTa?: string;
  soilMoistureUsedPercent?: number | null;
  forecastRainChancePercent?: number | null;
  recentRainMm?: number | null;
  reasonsEn: string[];
  reasonsTa: string[];
  confidenceLevel?: 'High' | 'Medium' | 'Low';
  limitationsEn?: string[];
  limitationsTa?: string[];
  paddySpecificNotesEn?: string | null;
  paddySpecificNotesTa?: string | null;
  isLiveWeatherUsed?: boolean;
  weatherSummary?: IrrigationWeatherResponse | null;
  weatherTimestamp?: string | null;
  isAdvisoryOnly: boolean;
  noHardwareControlNotice?: string;
  disclaimerEn: string;
  disclaimerTa: string;
}

export interface CropRecommendInput {
  district: string;
  soilType: string;
  season: string;
  waterAvailability: string;
  cropPreference?: string;
}

export interface CropRecommendationItem {
  crop: string;
  cropTa: string;
  category: string;
  matchScore: string;
  durationDays: string;
  expectedYieldRange: string;
  waterNeed: string;
  whySuitableEn: string;
  whySuitableTa: string;
  managementTipEn: string;
  managementTipTa: string;
  isTopPick: boolean;
}

export interface CropRecommendResponse {
  district: string;
  soilType: string;
  season: string;
  waterAvailability: string;
  recommendations: CropRecommendationItem[];
  assumptions: string[];
  missingInformationNotice: string;
  disclaimer: string;
}

export type DiagnosisCategory = 'pest_damage' | 'plant_disease' | 'abiotic_disorder' | 'healthy' | 'inconclusive';

export interface CropHealthDiagnosisDetails {
  isCropLeaf: boolean;
  category: DiagnosisCategory;
  categoryLabelEn: string;
  categoryLabelTa: string;
  suspectedCondition: string;
  suspectedConditionTa?: string;
  affectedCrop: string;
  affectedCropTa?: string;
  plantPart?: string;
  pathogenOrCausalAgent?: string;
  confidencePercent: number;
  severityOrUrgency: 'low' | 'moderate' | 'high' | 'critical' | 'unknown';
  visualSymptoms: string;
  visualSymptomsTa?: string;
  possibleCauses: string[];
  alternativeExplanations: string[];
  diagnosticLimitations: string[];
  recommendedNextSteps: string[];
  biologicalManagement: string[];
  chemicalTreatment?: string[];
  chemicalPrecautions?: string;
  preventionTips: string[];
  whenToConsultExpert: string[];
  verifiedGuidanceReferences: string[];

  // Legacy fields for backward compatibility
  crop?: string;
  cropTa?: string;
  diseaseName?: string;
  diseaseNameTa?: string;
  pathogen?: string;
  severity?: string;
  organicManagement?: string;
  organicManagementTa?: string;
  chemicalManagement?: string;
  chemicalManagementTa?: string;
  extensionAdvisory?: string;
  extensionAdvisoryTa?: string;
  verifiedTreatment?: VerifiedTreatmentGuidance;
}

export interface AuthoritativeReference {
  organization: string;
  sourceTitle: string;
  url?: string;
  publicationType?: string;
}

export interface BiologicalManagementGuidance {
  culturalPractices: string[];
  fieldSanitation: string[];
  cropRotationAndVarieties: string[];
  biologicalControlAgents: string[];
  soilAndNutrientManagement?: string[];
}

export interface ChemicalTreatmentGuidance {
  isApplicable: boolean;
  inapplicableReason?: string | null;
  activeIngredient?: string | null;
  approvedTarget?: string | null;
  dosageAndApplication?: string | null;
  cibrcRegistrationStatus?: string | null;
  preHarvestIntervalDays?: number | null;
  reEntryIntervalHours?: number | null;
  personalProtectiveEquipment: string[];
  safetyPrecautions: string[];
}

export interface VerifiedTreatmentGuidance {
  crop: string;
  cropTa?: string | null;
  conditionKey: string;
  conditionNameEn: string;
  conditionNameTa?: string | null;
  category: 'pest_damage' | 'plant_disease' | 'abiotic_disorder' | 'healthy' | 'inconclusive' | string;
  categoryLabelEn: string;
  categoryLabelTa: string;
  biologicalManagement: BiologicalManagementGuidance;
  chemicalManagement: ChemicalTreatmentGuidance;
  ipmStrategySummaryEn: string;
  ipmStrategySummaryTa: string;
  whenToConsultOfficer: string[];
  isUncertainOrInconclusive: boolean;
  safetyNoticeEn: string;
  safetyNoticeTa: string;
  references: AuthoritativeReference[];
}

export type DiseaseDiagnosisDetails = CropHealthDiagnosisDetails;

export interface ImageQualityAssessment {
  isAcceptable: boolean;
  qualityScore: number;
  luminance: number;
  edgeVariance: number;
  plantPixelFraction: number;
  warnings: string[];
  retakeGuidanceEn: string[];
  retakeGuidanceTa: string[];
}

export interface DiseaseAnalysisResponse {
  status: 'diagnosed' | 'suspected' | 'inconclusive' | 'quality_failure' | 'unavailable' | 'not_configured' | 'invalid_image' | string;
  diagnosticStatus?: string;
  testedModelPresent: boolean;
  modelName?: string;
  filename: string;
  fileSizeBytes?: number;
  contentType?: string;
  messageEn: string;
  messageTa: string;
  truthfulnessNotice: string;
  safeNextSteps: string[];
  diagnosis?: CropHealthDiagnosisDetails;
  verifiedTreatment?: VerifiedTreatmentGuidance;
  referenceCatalog?: DiseaseCatalogItem[];
  imageQuality?: ImageQualityAssessment;
  reportId?: string;
  saved?: boolean;
}

export interface DiagnosisReportEntity {
  id: string;
  userId: string;
  farmerId?: string;
  farmerName?: string;
  crop: string;
  cropTa?: string;
  plantPart?: string;
  district?: string;
  symptomDescription?: string;
  category: 'pest_damage' | 'plant_disease' | 'abiotic_disorder' | 'healthy' | 'inconclusive' | string;
  categoryLabelEn: string;
  categoryLabelTa: string;
  suspectedCondition: string;
  suspectedConditionTa?: string;
  pathogenOrCausalAgent?: string;
  status: string;
  confidencePercent: number;
  severityOrUrgency: string;
  isUncertainOrInconclusive: boolean;
  uncertaintyReason?: string;
  visualSymptoms: string;
  visualSymptomsTa?: string;
  possibleCauses: string[];
  alternativeExplanations: string[];
  diagnosticLimitations: string[];
  recommendedNextSteps: string[];
  biologicalManagement: string[];
  chemicalTreatment?: string[];
  chemicalPrecautions?: string;
  verifiedTreatment?: VerifiedTreatmentGuidance;
  verifiedGuidanceReferences: string[];
  imageMetadata?: {
    filename?: string;
    fileSizeBytes?: number;
    contentType?: string;
    retainedRawImage?: boolean;
    storagePolicy?: string;
  };
  createdAt: string;
  updatedAt?: string | null;
}

export interface DiagnosisReportListResponse {
  reports: DiagnosisReportEntity[];
  total: number;
  farmerId?: string;
  farmerName?: string;
}

export interface DiseaseCatalogItem {
  disease_id: string;
  crop: string;
  pathogen: string;
  name_en: string;
  name_ta: string;
  symptoms_en: string;
  symptoms_ta: string;
  favorable_weather: string;
  recommended_management_en: string;
  recommended_management_ta: string;
}

export interface MarketCommodityItem {
  id: string;
  crop: string;
  cropTa: string;
  commodity?: string;
  commodityTa?: string;
  variety?: string;
  grade?: string;
  district: string;
  mandi: string;
  market?: string;
  state?: string;
  arrivalDate?: string;
  arrivalDateHuman?: string;
  minPrice: number;
  maxPrice: number;
  modalPrice: number;
  unit: string;
  trend: 'up' | 'down' | 'steady';
  change: string;
  date: string;
}

export interface MarketPricesPagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface MarketPricesResponse {
  timestamp: string;
  dataSource: string;
  sourceUrl?: string;
  resourceId?: string;
  sourceStatus?: string;
  sourceConfigured?: boolean;
  isLive: boolean;
  isStale?: boolean;
  sourceArrivalDate?: string;
  lastSuccessfulFetchTime?: string;
  lastCheckedTime?: string;
  commodities: MarketCommodityItem[];
  pagination?: MarketPricesPagination;
  availableDistricts?: string[];
  availableCommodities?: string[];
  staleNoticeEn?: string;
  staleNoticeTa?: string;
  error?: string | null;
  demoNoticeEn?: string;
  demoNoticeTa?: string;
  hasNewData?: boolean;
  syncStatus?: string;
  syncMessageEn?: string;
  syncMessageTa?: string;
  refreshIntervalMinutes?: number;
  nextScheduledRefreshTime?: string;
}

export interface GovernmentSchemeItem {
  id: string;
  name?: string;
  nameTa?: string;
  titleEn: string;
  titleTa: string;
  dept: string;
  department?: string;
  category: string;
  governmentLevel?: 'Central' | 'State' | string;
  description?: string;
  benefit: string;
  benefits?: string[];
  eligibility: string | string[];
  requiredDocuments: string[];
  livestockTypes?: string[];
  applicationUrl: string;
  sourceUrl?: string;
  verificationDate?: string;
  applicationStatus?: 'Active' | 'Application Window Unknown' | 'Closed' | 'Unverified' | string;
  notes?: string;
  isVerifiedLink: boolean;
  portalName: string;
}

export interface GovernmentSchemesResponse {
  schemes: GovernmentSchemeItem[];
  totalCount?: number;
  disclaimerEn: string;
  disclaimerTa: string;
}

export async function getWeatherApi(district: string = 'thanjavur'): Promise<WeatherApiResponse> {
  const res = await fetch(`${API_BASE_URL}/weather?district=${encodeURIComponent(district)}`);
  return handleResponse<WeatherApiResponse>(res);
}

export async function getWeatherDistrictsApi(): Promise<WeatherDistrict[]> {
  const res = await fetch(`${API_BASE_URL}/weather/districts`);
  return handleResponse<WeatherDistrict[]>(res);
}

export async function getIrrigationWeatherApi(
  lat: number,
  lon: number,
  forceRefresh?: boolean
): Promise<IrrigationWeatherResponse> {
  const query = new URLSearchParams({
    lat: lat.toString(),
    lon: lon.toString(),
  });
  if (forceRefresh) {
    query.set('forceRefresh', 'true');
  }
  const res = await fetch(`${API_BASE_URL}/weather/irrigation?${query.toString()}`);
  return handleResponse<IrrigationWeatherResponse>(res);
}

export async function updateFarmLocationApi(
  data: FarmLocationInput,
  token?: string | null
): Promise<UserSummary> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/farmer/farm-location`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  return handleResponse<UserSummary>(res);
}

export async function calculateIrrigationApi(data: IrrigationCalculateInput): Promise<IrrigationCalculateResponse> {
  const res = await fetch(`${API_BASE_URL}/irrigation/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<IrrigationCalculateResponse>(res);
}

export async function recommendCropsApi(data: CropRecommendInput): Promise<CropRecommendResponse> {
  const res = await fetch(`${API_BASE_URL}/crops/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<CropRecommendResponse>(res);
}

export async function analyzeDiseaseImageApi(
  formData: FormData,
  language: string = 'en',
  token?: string | null
): Promise<DiseaseAnalysisResponse> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/disease/analyze?language=${encodeURIComponent(language)}`, {
    method: 'POST',
    headers,
    body: formData,
  });
  return handleResponse<DiseaseAnalysisResponse>(res);
}

export async function getDiseaseCatalogApi(): Promise<{ catalog: DiseaseCatalogItem[]; source: string }> {
  const res = await fetch(`${API_BASE_URL}/disease/catalog`);
  return handleResponse<{ catalog: DiseaseCatalogItem[]; source: string }>(res);
}

export async function getDiseaseTreatmentApi(params: {
  crop?: string;
  condition?: string;
  category?: string;
  confidence?: number;
  language?: string;
}): Promise<VerifiedTreatmentGuidance> {
  const q = new URLSearchParams();
  if (params.crop) q.append('crop', params.crop);
  if (params.condition) q.append('condition', params.condition);
  if (params.category) q.append('category', params.category);
  if (params.confidence !== undefined) q.append('confidence', params.confidence.toString());
  if (params.language) q.append('language', params.language);
  const res = await fetch(`${API_BASE_URL}/disease/treatment?${q.toString()}`);
  return handleResponse<VerifiedTreatmentGuidance>(res);
}

export async function listDiagnosisReportsApi(token: string): Promise<DiagnosisReportListResponse> {
  const res = await fetch(`${API_BASE_URL}/disease/reports`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<DiagnosisReportListResponse>(res);
}

export async function getDiagnosisReportByIdApi(reportId: string, token: string): Promise<DiagnosisReportEntity> {
  const res = await fetch(`${API_BASE_URL}/disease/reports/${reportId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<DiagnosisReportEntity>(res);
}

export async function deleteDiagnosisReportApi(reportId: string, token: string): Promise<{ success: boolean; message: string; deletedId: string }> {
  const res = await fetch(`${API_BASE_URL}/disease/reports/${reportId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<{ success: boolean; message: string; deletedId: string }>(res);
}

export interface GetMarketPricesParams {
  district?: string;
  commodity?: string;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  forceRefresh?: boolean;
}

export async function getMarketPricesApi(
  districtOrParams?: string | GetMarketPricesParams,
  search?: string
): Promise<MarketPricesResponse> {
  const query = new URLSearchParams();

  if (typeof districtOrParams === 'object' && districtOrParams !== null) {
    if (districtOrParams.district && districtOrParams.district !== 'All') {
      query.append('district', districtOrParams.district);
    }
    if (districtOrParams.commodity && districtOrParams.commodity !== 'All') {
      query.append('commodity', districtOrParams.commodity);
    }
    if (districtOrParams.search && districtOrParams.search.trim()) {
      query.append('search', districtOrParams.search.trim());
    }
    if (districtOrParams.page) {
      query.append('page', String(districtOrParams.page));
    }
    if (districtOrParams.limit) {
      query.append('limit', String(districtOrParams.limit));
    }
    if (districtOrParams.sortBy) {
      query.append('sort_by', districtOrParams.sortBy);
    }
    if (districtOrParams.sortOrder) {
      query.append('sort_order', districtOrParams.sortOrder);
    }
    if (districtOrParams.forceRefresh) {
      query.append('force_refresh', 'true');
    }
  } else {
    if (districtOrParams && districtOrParams !== 'All') {
      query.append('district', districtOrParams);
    }
    if (search && search.trim()) {
      query.append('search', search.trim());
    }
  }

  const queryString = query.toString();
  const url = queryString ? `${API_BASE_URL}/market/prices?${queryString}` : `${API_BASE_URL}/market/prices`;
  const res = await fetch(url);
  return handleResponse<MarketPricesResponse>(res);
}

export interface GetGovernmentSchemesParams {
  category?: string;
  search?: string;
  governmentLevel?: string;
  livestockType?: string;
}

export async function getGovernmentSchemesApi(
  paramsOrCategory?: string | GetGovernmentSchemesParams
): Promise<GovernmentSchemesResponse> {
  const queryParams = new URLSearchParams();

  if (typeof paramsOrCategory === 'string') {
    if (paramsOrCategory && paramsOrCategory !== 'All') {
      queryParams.set('category', paramsOrCategory);
    }
  } else if (paramsOrCategory) {
    if (paramsOrCategory.category && paramsOrCategory.category !== 'All') {
      queryParams.set('category', paramsOrCategory.category);
    }
    if (paramsOrCategory.search && paramsOrCategory.search.trim()) {
      queryParams.set('search', paramsOrCategory.search.trim());
    }
    if (paramsOrCategory.governmentLevel && paramsOrCategory.governmentLevel !== 'All') {
      queryParams.set('governmentLevel', paramsOrCategory.governmentLevel);
    }
    if (paramsOrCategory.livestockType && paramsOrCategory.livestockType !== 'All') {
      queryParams.set('livestockType', paramsOrCategory.livestockType);
    }
  }

  const queryString = queryParams.toString();
  const res = await fetch(`${API_BASE_URL}/schemes${queryString ? `?${queryString}` : ''}`);
  return handleResponse<GovernmentSchemesResponse>(res);
}

// ============================================================================
// PHASE 6: AI FARMER ASSISTANT & CHAT
// ============================================================================

export interface ChatMessagePayload {
  message: string;
  language: Language;
  conversationId?: string;
  includeFarmContext?: boolean;
  confirmedAction?: Record<string, any>;
}

export interface ChatAction {
  intent: string;
  actionType?: 'NAVIGATE' | 'SHOW_DATA' | 'REQUEST_CONFIRMATION' | 'EXECUTE_ACTION' | 'UNSUPPORTED' | 'ERROR' | string;
  targetTab?: string | null;
  actionName?: string;
  parameters?: Record<string, any>;
  data?: Record<string, any>;
  requiresConfirmation?: boolean;
  confirmationPrompt?: string;
  confirmedActionPayload?: Record<string, any>;
}

export interface ChatMessageApiResponse {
  id: string;
  reply: string;
  language: Language;
  provider: string;
  isRealAI: boolean;
  providerNotice: string;
  contextUsed: {
    farmerName?: string;
    district?: string;
    crop?: string;
    activeBookingsCount?: number;
    weatherSummary?: string;
  };
  followUpQuestion?: string;
  timestamp: string;
  conversationId: string;
  action?: ChatAction | null;
}

export async function sendChatMessageApi(
  payload: ChatMessagePayload,
  token?: string | null
): Promise<ChatMessageApiResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}/chat/message`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  return handleResponse<ChatMessageApiResponse>(res);
}

export async function getChatHistoryApi(
  token: string
): Promise<{ messages: Array<{
  id: string;
  conversationId: string;
  userMessage: string;
  assistantReply: string;
  followUpQuestion?: string;
  language: 'en' | 'ta';
  provider: string;
  isRealAI: boolean;
  timestamp: string;
}> }> {
  const res = await fetch(`${API_BASE_URL}/chat/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function clearChatHistoryApi(token: string): Promise<{ deletedCount: number; message: string }> {
  const res = await fetch(`${API_BASE_URL}/chat/history`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export interface ChatStatusApiResponse {
  geminiConfigured: boolean;
  model: string;
  supportedLanguages: string[];
  mode: string;
}

export async function getChatStatusApi(): Promise<ChatStatusApiResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/status`);
  return handleResponse<ChatStatusApiResponse>(res);
}

export async function cancelProcurementBookingApi(
  bookingId: string,
  token: string
): Promise<ProcurementBookingEntity> {
  const res = await fetch(`${API_BASE_URL}/procurement/bookings/${encodeURIComponent(bookingId)}/cancel`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<ProcurementBookingEntity>(res);
}

// ============================================================================
// PLATFORM CONFIGURATION METADATA API
// ============================================================================

export interface ConfigMetaResponse {
  irrigationOptions: string[];
  languages: string[];
  languageCodes: Record<string, string>;
  phoneVerification?: {
    configured: boolean;
    provider?: string | null;
    notice: string;
  };
}

export async function getConfigMetaApi(): Promise<ConfigMetaResponse> {
  const res = await fetch(`${API_BASE_URL}/config/meta`);
  return handleResponse<ConfigMetaResponse>(res);
}

// ============================================================================
// FARMER SUPPORT HUB (SECTIONS 1-6) APIS
// ============================================================================

export async function getFarmerSupportContent(params?: {
  category?: string;
  district?: string;
  state?: string;
  search?: string;
  contentType?: string;
  activeOnly?: boolean;
}): Promise<FarmerSupportResponse> {
  const q = new URLSearchParams();
  if (params?.category && params.category !== 'all') q.set('category', params.category);
  if (params?.district && params.district !== 'All') q.set('district', params.district);
  if (params?.state && params.state !== 'All') q.set('state', params.state);
  if (params?.search) q.set('search', params.search);
  if (params?.contentType) q.set('content_type', params.contentType);
  if (params?.activeOnly !== undefined) q.set('active_only', String(params.activeOnly));

  const url = `${API_BASE_URL}/support/content${q.toString() ? `?${q.toString()}` : ''}`;
  const res = await fetch(url);
  return handleResponse<FarmerSupportResponse>(res);
}

export async function getSupportContentById(contentId: string): Promise<FarmerSupportContent> {
  const res = await fetch(`${API_BASE_URL}/support/content/${encodeURIComponent(contentId)}`);
  return handleResponse<FarmerSupportContent>(res);
}

export async function getTrainingCalendar(params?: {
  district?: string;
  mode?: string;
  upcomingOnly?: boolean;
}): Promise<{ items: FarmerSupportContent[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.district && params.district !== 'All') q.set('district', params.district);
  if (params?.mode && params.mode !== 'All') q.set('mode', params.mode);
  if (params?.upcomingOnly !== undefined) q.set('upcoming_only', String(params.upcomingOnly));

  const url = `${API_BASE_URL}/support/training/calendar${q.toString() ? `?${q.toString()}` : ''}`;
  const res = await fetch(url);
  return handleResponse<{ items: FarmerSupportContent[]; total: number }>(res);
}

export async function getCropMasterGuide(cropId: string): Promise<FarmerSupportContent> {
  const res = await fetch(`${API_BASE_URL}/support/crops/guide/${encodeURIComponent(cropId)}`);
  return handleResponse<FarmerSupportContent>(res);
}

// ============================================================================
// FARMER DIRECT MARKETPLACE (SECTION 7) APIS
// ============================================================================

export async function getMarketplaceListings(params?: {
  district?: string;
  category?: string;
  search?: string;
  organicOnly?: boolean;
  page?: number;
  limit?: number;
}): Promise<MarketplaceResponse> {
  const q = new URLSearchParams();
  if (params?.district && params.district !== 'All') q.set('district', params.district);
  if (params?.category && params.category !== 'All') q.set('category', params.category);
  if (params?.search) q.set('search', params.search);
  if (params?.organicOnly) q.set('organic_only', 'true');
  if (params?.page) q.set('page', String(params.page));
  if (params?.limit) q.set('limit', String(params.limit));

  const url = `${API_BASE_URL}/marketplace/listings${q.toString() ? `?${q.toString()}` : ''}`;
  const res = await fetch(url);
  return handleResponse<MarketplaceResponse>(res);
}

export async function getMarketplaceListingById(listingId: string): Promise<MarketplaceListing> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}`);
  return handleResponse<MarketplaceListing>(res);
}

export async function recordMarketplaceInquiry(listingId: string): Promise<{ success: boolean; listingId: string }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}/inquiry`, {
    method: 'POST',
  });
  return handleResponse<{ success: boolean; listingId: string }>(res);
}

export async function getFarmerMyListings(token: string): Promise<{ items: MarketplaceListing[]; total: number }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/my-listings`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ items: MarketplaceListing[]; total: number }>(res);
}

export async function createFarmerMarketplaceListing(
  data: MarketplaceListingCreate,
  token: string
): Promise<{ success: boolean; message: string; listing: MarketplaceListing }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return handleResponse<{ success: boolean; message: string; listing: MarketplaceListing }>(res);
}

export async function updateFarmerMarketplaceListing(
  listingId: string,
  data: Partial<MarketplaceListingCreate> & { listingStatus?: string },
  token: string
): Promise<{ success: boolean; message: string; listing: MarketplaceListing }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return handleResponse<{ success: boolean; message: string; listing: MarketplaceListing }>(res);
}

export async function deleteFarmerMarketplaceListing(
  listingId: string,
  token: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

export async function createMarketplaceOrderRequest(
  listingId: string,
  data: MarketplaceOrderRequestCreate
): Promise<MarketplaceOrderRequest> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<MarketplaceOrderRequest>(res);
}

export async function getFarmerMyOrders(
  token: string,
  listingId?: string
): Promise<{ items: MarketplaceOrderRequest[]; total: number }> {
  const q = listingId ? `?listing_id=${encodeURIComponent(listingId)}` : '';
  const res = await fetch(`${API_BASE_URL}/marketplace/my-orders${q}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ items: MarketplaceOrderRequest[]; total: number }>(res);
}

export async function updateFarmerOrderStatus(
  orderId: string,
  status: string,
  token: string
): Promise<{ success: boolean; order: MarketplaceOrderRequest }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/orders/${encodeURIComponent(orderId)}/status?status=${encodeURIComponent(status)}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ success: boolean; order: MarketplaceOrderRequest }>(res);
}

// ============================================================================
// SPECIAL OPERATION — FROM FIRST STEP TO FIRST SALE API CLIENT
// ============================================================================

export async function getSpecialOperationJourney(token: string): Promise<SpecialOperationJourney> {
  const res = await fetch(`${API_BASE_URL}/special-operation/journey`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<SpecialOperationJourney>(res);
}

export async function updateSpecialOperationStep(
  payload: SpecialOperationStepUpdateRequest,
  token: string
): Promise<SpecialOperationJourney> {
  const res = await fetch(`${API_BASE_URL}/special-operation/journey/step`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<SpecialOperationJourney>(res);
}

export async function getSpecialOperationCrops(
  filters?: Record<string, string>
): Promise<{ crops: SpecialOperationCropRecommendation[]; total: number; disclaimer: string }> {
  const params = new URLSearchParams(filters || {});
  const res = await fetch(`${API_BASE_URL}/special-operation/crops?${params.toString()}`);
  return handleResponse<{ crops: SpecialOperationCropRecommendation[]; total: number; disclaimer: string }>(res);
}

export async function getSpecialOperationCropGuide(cropId: string): Promise<SpecialOperationCropGuide> {
  const res = await fetch(`${API_BASE_URL}/special-operation/crops/${encodeURIComponent(cropId)}/guide`);
  return handleResponse<SpecialOperationCropGuide>(res);
}

export async function getSpecialOperationTimeline(
  cropId: string,
  plantingDate?: string
): Promise<SpecialOperationTimeline> {
  const q = plantingDate ? `?planting_date=${encodeURIComponent(plantingDate)}` : '';
  const res = await fetch(`${API_BASE_URL}/special-operation/crops/${encodeURIComponent(cropId)}/timeline${q}`);
  return handleResponse<SpecialOperationTimeline>(res);
}

export async function addSpecialOperationObservation(
  payload: {
    note: string;
    stageNumber?: number;
    photoUrl?: string;
    isDeviation?: boolean;
    deviationReason?: string;
  },
  token: string
): Promise<{ success: boolean; observation: JourneyObservation }> {
  const res = await fetch(`${API_BASE_URL}/special-operation/journey/observation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ success: boolean; observation: JourneyObservation }>(res);
}

export async function triggerSpecialOperationReminder(
  payload: { title: string; message: string },
  token: string
): Promise<{ success: boolean; notification: any }> {
  const res = await fetch(`${API_BASE_URL}/special-operation/journey/reminders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ success: boolean; notification: any }>(res);
}

export async function resetSpecialOperationJourney(
  token: string
): Promise<{ success: boolean; message: string; journey: SpecialOperationJourney }> {
  const res = await fetch(`${API_BASE_URL}/special-operation/journey/reset`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ success: boolean; message: string; journey: SpecialOperationJourney }>(res);
}

// ============================================================================
// MARKETPLACE REPORTING API
// ============================================================================

export async function reportMarketplaceListing(
  listingId: string,
  payload: MarketplaceListingReportRequest
): Promise<{ listingId: string; reportCount: number; flagged: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/marketplace/listings/${encodeURIComponent(listingId)}/report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ listingId: string; reportCount: number; flagged: boolean; message: string }>(res);
}

// ============================================================================
// AGRI ENTREPRENEURSHIP APIS
// ============================================================================

export async function matchBusinessIdeas(
  payload: BusinessIdeaMatchRequest
): Promise<BusinessIdeaMatchResponse> {
  const res = await fetch(`${API_BASE_URL}/business/ideas/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<BusinessIdeaMatchResponse>(res);
}

export async function calculateBusinessPlan(
  payload: BusinessPlanCalculationRequest
): Promise<BusinessPlanCalculationResult> {
  const res = await fetch(`${API_BASE_URL}/business/plans/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<BusinessPlanCalculationResult>(res);
}

export async function createFarmerBusinessPlan(
  payload: BusinessPlanCreateRequest,
  token: string
): Promise<BusinessPlanModel> {
  const res = await fetch(`${API_BASE_URL}/business/plans`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<BusinessPlanModel>(res);
}

export async function getFarmerBusinessPlans(
  token: string
): Promise<{ items: BusinessPlanModel[]; total: number }> {
  const res = await fetch(`${API_BASE_URL}/business/plans`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ items: BusinessPlanModel[]; total: number }>(res);
}

export async function getFarmerBusinessPlanById(
  planId: string,
  token: string
): Promise<BusinessPlanModel> {
  const res = await fetch(`${API_BASE_URL}/business/plans/${encodeURIComponent(planId)}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<BusinessPlanModel>(res);
}

export async function updateFarmerBusinessPlan(
  planId: string,
  payload: BusinessPlanUpdateRequest,
  token: string
): Promise<BusinessPlanModel> {
  const res = await fetch(`${API_BASE_URL}/business/plans/${encodeURIComponent(planId)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<BusinessPlanModel>(res);
}

export async function deleteFarmerBusinessPlan(
  planId: string,
  token: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/business/plans/${encodeURIComponent(planId)}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

// ============================================================================
// VALUE-ADDED PRODUCTS APIS
// ============================================================================

export async function getValueAdditionProducts(params?: {
  raw_material?: string;
  method_category?: string;
}): Promise<{ items: ValueAdditionProductBlueprint[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.raw_material) q.set('raw_material', params.raw_material);
  if (params?.method_category) q.set('method_category', params.method_category);
  const url = `${API_BASE_URL}/value-addition/products${q.toString() ? `?${q.toString()}` : ''}`;
  const res = await fetch(url);
  return handleResponse<{ items: ValueAdditionProductBlueprint[]; total: number }>(res);
}

export async function getValueAdditionProductDetail(
  productId: string
): Promise<ValueAdditionProductBlueprint> {
  const res = await fetch(`${API_BASE_URL}/value-addition/products/${encodeURIComponent(productId)}`);
  return handleResponse<ValueAdditionProductBlueprint>(res);
}

export async function calculateValueAddition(
  payload: ValueAdditionCalculationRequest
): Promise<ValueAdditionCalculationResponse> {
  const res = await fetch(`${API_BASE_URL}/value-addition/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ValueAdditionCalculationResponse>(res);
}



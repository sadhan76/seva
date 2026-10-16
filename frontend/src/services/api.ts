import type { InAppNotification, SMSStatusInfo } from '../types';

export type { InAppNotification, SMSStatusInfo };

const rawApiUrl =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000/api';
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
  village?: string;
  district?: string;
  state?: string;
  mandiName?: string;
  mandiAssigned?: string;
  farmerId?: string;
  primaryCrop?: string;
  totalLandAcres?: number;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  aadhaarMasked?: string;
  isAadhaarVerified?: boolean;
  createdAt: string;
  telegramLinked?: boolean;
  telegramUsername?: string;
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
  village: string;
  district?: string;
  state?: string;
  preferredLanguage: string;
  password: string;
  confirmPassword: string;
  totalLandAcres: number;
  primaryCrop?: string;
  soilType?: string;
  irrigationSources?: string[];
  irrigationSource?: string;
  otherIrrigationDetail?: string;
  telegramVerifiedToken?: string;
}

export interface LoginPayload {
  phone: string;
  password?: string;
  role: 'farmer' | 'staff';
  authMethod?: 'password' | 'telegram_otp';
  telegramOtp?: string;
}

export interface FarmerProfileInput {
  name: string;
  phone: string;
  location: string;
  district?: string;
  state?: string;
  totalLandAcres: number;
  primaryCrop: string;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  preferredLanguage?: string;
  aadhaarMasked?: string;
}

export interface TelegramStatusResponse {
  configured: boolean;
  botUsername?: string;
  message: string;
}

export interface TelegramLinkTokenResponse {
  linkToken: string;
  deepLink: string;
  botUsername: string;
  expiresInSeconds: number;
  configured: boolean;
  notice: string;
}

export interface TelegramLinkStatusResponse {
  linked: boolean;
  verified: boolean;
  telegramUsername?: string;
  telegramFirstName?: string;
  phone?: string;
  message: string;
}

export interface TelegramSendOtpResponse {
  success: boolean;
  message: string;
  maskedChat: string;
  cooldownSeconds: number;
  expiresInSeconds: number;
}

export interface TelegramVerifyOtpResponse {
  success: boolean;
  message: string;
  phone: string;
  verifiedToken?: string;
  authToken?: AuthTokenResponse;
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
  quantityBags: number;
  preferredDate: string;
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
  status: 'available' | 'filling_fast' | 'full';
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
  slotDate: string;
  timeWindow: string;
  farmerName: string;
  crop: string;
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
  quantityBags: number;
  estimatedWeightQuintals: number;
  slotDate: string;
  timeWindow: string;
  status: string;
  moisturePercent?: number;
  actualNetWeightQuintals?: number;
  acceptedWeightKg?: number;
  qualityNotes?: string;
  billNumber?: string;
  bill?: DigitalBillEntity | null;
  transaction?: WeighingTransactionDetails | null;
  auditHistory?: AuditLogEntry[];
  createdAt: string;
}

export interface StaffQueueOverviewResponse {
  staffName: string;
  mandiName: string;
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
  const res = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<BackendHealthResponse>(res);
}

// ============================================================================
// AUTHENTICATION APIS (PHASE 3)
// ============================================================================

function normalizeUser(u: UserSummary): UserSummary {
  return {
    ...u,
    fullName: u.name || u.fullName || '',
    mandiAssigned: u.mandiName || u.mandiAssigned || '',
  };
}

/**
 * Register a new farmer account
 */
export async function registerFarmerApi(data: FarmerRegisterPayload): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
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
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
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
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
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
  return handleResponse<UserSummary>(res);
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

export interface IrrigationCalculateInput {
  crop: string;
  growthStage: string;
  soilType: string;
  irrigationMethod: string;
  soilMoisturePercent?: number;
  recentRainMm?: number;
  forecastRainChance?: number;
}

export interface IrrigationCalculateResponse {
  crop: string;
  growthStage: string;
  soilType: string;
  irrigationMethod: string;
  status: 'delay' | 'adequate' | 'urgent' | 'moderate';
  recommendationEn: string;
  recommendationTa: string;
  cropWaterDemandMm: number;
  cropFactorKc: number;
  estimatedLitersPerAcre: number;
  reasonsEn: string[];
  reasonsTa: string[];
  isAdvisoryOnly: boolean;
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

export interface DiseaseAnalysisResponse {
  status: string;
  testedModelPresent: boolean;
  filename: string;
  fileSizeBytes?: number;
  contentType?: string;
  messageEn: string;
  messageTa: string;
  truthfulnessNotice: string;
  safeNextSteps: string[];
  referenceCatalog?: DiseaseCatalogItem[];
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
  district: string;
  mandi: string;
  minPrice: number;
  maxPrice: number;
  modalPrice: number;
  unit: string;
  trend: 'up' | 'down' | 'steady';
  change: string;
  date: string;
}

export interface MarketPricesResponse {
  timestamp: string;
  dataSource: string;
  isLive: boolean;
  demoNoticeEn: string;
  demoNoticeTa: string;
  commodities: MarketCommodityItem[];
}

export interface GovernmentSchemeItem {
  id: string;
  titleEn: string;
  titleTa: string;
  dept: string;
  category: string;
  benefit: string;
  eligibility: string;
  requiredDocuments: string[];
  applicationUrl: string;
  isVerifiedLink: boolean;
  portalName: string;
}

export interface GovernmentSchemesResponse {
  schemes: GovernmentSchemeItem[];
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

export async function analyzeDiseaseImageApi(formData: FormData): Promise<DiseaseAnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/disease/analyze`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<DiseaseAnalysisResponse>(res);
}

export async function getDiseaseCatalogApi(): Promise<{ catalog: DiseaseCatalogItem[]; source: string }> {
  const res = await fetch(`${API_BASE_URL}/disease/catalog`);
  return handleResponse<{ catalog: DiseaseCatalogItem[]; source: string }>(res);
}

export async function getMarketPricesApi(district?: string, search?: string): Promise<MarketPricesResponse> {
  const params = new URLSearchParams();
  if (district) params.append('district', district);
  if (search) params.append('search', search);
  const res = await fetch(`${API_BASE_URL}/market/prices?${params.toString()}`);
  return handleResponse<MarketPricesResponse>(res);
}

export async function getGovernmentSchemesApi(category?: string): Promise<GovernmentSchemesResponse> {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  const res = await fetch(`${API_BASE_URL}/schemes?${params.toString()}`);
  return handleResponse<GovernmentSchemesResponse>(res);
}

// ============================================================================
// PHASE 6: AI FARMER ASSISTANT & CHAT
// ============================================================================

export interface ChatMessagePayload {
  message: string;
  language: 'en' | 'ta';
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
  language: 'en' | 'ta';
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
// PHASE 19: CONFIGURATION METADATA & TELEGRAM AUTH APIS
// ============================================================================

export interface ConfigMetaResponse {
  irrigationOptions: string[];
  languages: string[];
  languageCodes: Record<string, string>;
  telegram: {
    configured: boolean;
    botUsername: string;
  };
}

export async function getConfigMetaApi(): Promise<ConfigMetaResponse> {
  const res = await fetch(`${API_BASE_URL}/config/meta`);
  return handleResponse<ConfigMetaResponse>(res);
}

export async function getTelegramStatusApi(): Promise<TelegramStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/telegram/status`);
  return handleResponse<TelegramStatusResponse>(res);
}

export async function createTelegramLinkTokenApi(phone?: string, purpose?: string): Promise<TelegramLinkTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/telegram/link-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, purpose }),
  });
  return handleResponse<TelegramLinkTokenResponse>(res);
}

export async function getTelegramLinkStatusApi(token: string): Promise<TelegramLinkStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/telegram/link-status?token=${encodeURIComponent(token)}`);
  return handleResponse<TelegramLinkStatusResponse>(res);
}

export async function sendTelegramOtpApi(phone: string, purpose?: string): Promise<TelegramSendOtpResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/telegram/send-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, purpose }),
  });
  return handleResponse<TelegramSendOtpResponse>(res);
}

export async function verifyTelegramOtpApi(phone: string, otp: string, purpose?: string): Promise<TelegramVerifyOtpResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/telegram/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, otp, purpose }),
  });
  const data = await handleResponse<TelegramVerifyOtpResponse>(res);
  if (data.authToken && data.authToken.user) {
    data.authToken.user = normalizeUser(data.authToken.user);
  }
  return data;
}





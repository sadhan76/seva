export type Language =
  | 'en'
  | 'ta'
  | 'hi'
  | 'te'
  | 'kn'
  | 'ml'
  | 'mr'
  | 'bn'
  | 'gu'
  | 'pa'
  | 'or'
  | 'as'
  | 'ur'
  | 'ne'
  | 'sa'
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
  | 'procurement'
  | 'queue'
  | 'notifications'
  | 'profile'
  | 'staff_portal';

export type ViewState = 'normal' | 'loading' | 'empty' | 'error';

export interface FarmerProfile {
  name: string;
  phone: string;
  location: string;
  district: string;
  state: string;
  totalLandAcres?: number;
  primaryCrop?: string;
  soilType?: string;
  irrigationSource?: string;
  irrigationSources?: string[];
  otherIrrigationDetail?: string;
  preferredLanguage?: Language;
  aadhaarMasked?: string;
  farmerId?: string;
  isFromDb?: boolean;
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

export interface ProcurementSlot {
  bookingId: string;
  mandiName: string;
  crop: string;
  quantityBags: number;
  estimatedWeightQuintals: number;
  slotDate: string;
  timeWindow: string;
  tokenNumber: string;
  status: 'confirmed' | 'pending' | 'weighed' | 'completed' | 'booked' | string;
  isSample: boolean;
  isFromDb?: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  time: string;
  language?: 'en' | 'ta';
  provider?: string;
  isRealAI?: boolean;
  providerNotice?: string;
  followUpQuestion?: string;
}

export interface InAppNotification {
  id: string;
  title: string;
  message: string;
  type: 'booking' | 'queue' | 'weighing' | 'bill' | 'payment' | 'weather' | string;
  isRead: boolean;
  createdAt: string;
  isoTimestamp?: string;
  bookingId?: string;
  farmerId?: string;
  userId?: string;
}

export interface SMSStatusInfo {
  configured: boolean;
  provider: string;
  senderId?: string;
  message: string;
  note: string;
}


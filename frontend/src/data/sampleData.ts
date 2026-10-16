import type { FarmerProfile, WeatherData, IrrigationAdvice, CropHealth, ProcurementSlot } from '../types';

/**
 * SAMPLE AGRICULTURAL DATA FOR DEMO PURPOSES ONLY
 * Note: These values are mocked for hackathon development and local testing.
 * They are not connected to official live government or meteorological sources yet.
 */

export const sampleFarmerProfile: FarmerProfile = {
  name: 'Selvakumar R.',
  phone: '+91 98XXX-XX120',
  farmerId: 'TN-AGRI-2026-8841',
  location: 'Kabisthalam, Thanjavur District',
  district: 'Thanjavur',
  state: 'Tamil Nadu',
  totalLandAcres: 3.5,
  primaryCrop: 'Samba Paddy (CR 1009 Sub 1)',
  soilType: 'Alluvial Clay Loam',
  irrigationSource: 'Borewell & Vennar Canal',
  aadhaarMasked: 'XXXX-XXXX-4921',
};

export const sampleWeather: WeatherData = {
  temperatureC: 31,
  condition: 'Partly Cloudy',
  humidity: 68,
  rainfallChance: 20,
  windSpeedKmh: 14,
  updatedAt: 'Today, 02:30 PM (Simulated)',
  isSample: true,
  forecast: [
    { day: 'Today', temp: '31°C / 24°C', condition: 'Partly Cloudy', rainProb: 20 },
    { day: 'Tomorrow', temp: '32°C / 23°C', condition: 'Sunny & Dry', rainProb: 10 },
    { day: 'Friday', temp: '29°C / 22°C', condition: 'Light Showers', rainProb: 45 },
  ],
};

export const sampleIrrigation: IrrigationAdvice = {
  soilMoisturePercent: 64,
  status: 'optimal',
  nextScheduledTime: 'Tomorrow at 06:30 AM',
  waterSavedLiters: 1450,
  recommendation: 'Soil moisture is in the optimal 60-70% zone for tillering stage paddy. Delay watering until tomorrow morning to conserve electricity and water.',
  isSample: true,
};

export const sampleCropHealth: CropHealth = {
  cropName: 'Samba Paddy (CR 1009)',
  stage: 'Active Tillering (Day 38)',
  healthScorePercent: 92,
  status: 'healthy',
  lastScannedDate: '13 Oct 2026 (Field Inspection)',
  notes: 'Canopy greenness index is high. No bacterial leaf blight or brown planthopper infestation symptoms identified.',
  isSample: true,
};

export const sampleProcurement: ProcurementSlot = {
  bookingId: 'PROC-TNJ-2026-0941',
  mandiName: 'Thanjavur Regulated Market (DPC Centre #3)',
  crop: 'Paddy Grade A (CR 1009)',
  quantityBags: 120,
  estimatedWeightQuintals: 48.0,
  slotDate: '18 Oct 2026',
  timeWindow: '08:30 AM - 11:30 AM',
  tokenNumber: 'TN-DPC-042',
  status: 'confirmed',
  isSample: true,
};

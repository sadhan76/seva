import React, { useState, useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import {
  CalendarCheck,
  CheckCircle2,
  ShieldCheck,
  Loader2,
  AlertCircle,
  Database,
  RefreshCw,
  Building2,
  Clock,
  Scale,
  ArrowRight,
  FileText,
  Printer,
} from 'lucide-react';

import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { DigitalBillModal } from '../common/DigitalBillModal';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getProcurementBookings,
  createProcurementBooking,
  getProcurementCentres,
  getProcurementSlots,
  getFarmerBillsApi,
  getDigitalBillApi,
  type ProcurementBookingEntity,
  type ProcurementCentreInfo,
  type CentreSlotsResponse,
  type DigitalBillEntity,
} from '../../services/api';
import type { ProcurementSlot } from '../../types';

interface ProcurementBookingViewProps {
  onBookingCreated?: (booking: ProcurementSlot) => void;
  onNavigateToQueue?: (bookingId?: string) => void;
}

export const ProcurementBookingView: React.FC<ProcurementBookingViewProps> = ({
  onBookingCreated,
  onNavigateToQueue,
}) => {
  const { t, language } = useLanguage();
  const { user, token } = useAuth();

  // Centres Master Data
  const [centres, setCentres] = useState<ProcurementCentreInfo[]>([]);
  const [selectedCentre, setSelectedCentre] = useState<ProcurementCentreInfo | null>(null);
  const [isLoadingCentres, setIsLoadingCentres] = useState(true);

  // Form Fields
  const [crop, setCrop] = useState('Paddy Grade A (சம்பா நெல் CR 1009)');
  const [bags, setBags] = useState<number>(100);
  const [slotDate, setSlotDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return d.toISOString().split('T')[0];
  });
  const [slotTime, setSlotTime] = useState<string>('08:30 AM - 11:30 AM');

  // Slots availability data for selected centre & date
  const [slotsAvailability, setSlotsAvailability] = useState<CentreSlotsResponse | null>(null);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [submittedSlot, setSubmittedSlot] = useState<ProcurementBookingEntity | null>(null);

  // Past farmer bookings
  const [dbBookings, setDbBookings] = useState<ProcurementBookingEntity[]>([]);
  const [isLoadingBookings, setIsLoadingBookings] = useState(false);

  // Digital Bills State
  const [farmerBills, setFarmerBills] = useState<DigitalBillEntity[]>([]);
  const [isLoadingBills, setIsLoadingBills] = useState(false);
  const [selectedBillForModal, setSelectedBillForModal] = useState<DigitalBillEntity | null>(null);
  const [isBillModalOpen, setIsBillModalOpen] = useState(false);

  // QR Code canvas reference
  const qrCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Auto-calculated quintals: standard 40 kg per bag / 100
  const estimatedQuintals = Number(((bags * 40) / 100).toFixed(2));

  // 1. Fetch available procurement centres on load
  useEffect(() => {
    const fetchCentres = async () => {
      setIsLoadingCentres(true);
      try {
        const data = await getProcurementCentres();
        setCentres(data);
        if (data.length > 0) {
          setSelectedCentre(data[0]);
          if (data[0].supportedCrops.length > 0) {
            setCrop(data[0].supportedCrops[0]);
          }
          if (data[0].slotWindows.length > 0) {
            setSlotTime(data[0].slotWindows[0]);
          }
        }
      } catch (err: any) {
        console.error('Failed to load centres:', err);
      } finally {
        setIsLoadingCentres(false);
      }
    };
    fetchCentres();
  }, []);

  // 2. Fetch live slot availability whenever centre or date changes
  useEffect(() => {
    if (!selectedCentre || !slotDate) return;

    const fetchSlots = async () => {
      setIsLoadingSlots(true);
      try {
        const slotsData = await getProcurementSlots(selectedCentre.centreCode, slotDate);
        setSlotsAvailability(slotsData);
      } catch (err) {
        console.error('Failed to load slot capacity:', err);
      } finally {
        setIsLoadingSlots(false);
      }
    };
    fetchSlots();
  }, [selectedCentre, slotDate]);

  // 3. Load user's bookings from MongoDB
  const loadBookings = async () => {
    setIsLoadingBookings(true);
    try {
      const records = await getProcurementBookings(token);
      setDbBookings(records);
    } catch {
      // Graceful fallback
    } finally {
      setIsLoadingBookings(false);
    }
  };

  const loadFarmerBills = async () => {
    if (!token) return;
    setIsLoadingBills(true);
    try {
      const data = await getFarmerBillsApi(token);
      setFarmerBills(data.bills || []);
    } catch (err: any) {
      console.error('Failed to load farmer bills:', err);
    } finally {
      setIsLoadingBills(false);
    }
  };

  useEffect(() => {
    loadBookings();
    loadFarmerBills();
  }, [token]);

  // 4. Render QR code upon successful slot submission
  useEffect(() => {
    if (submittedSlot && qrCanvasRef.current) {
      // Privacy-first QR encoding: Encode ONLY opaque token and official URL, strictly no PII
      const qrPayload = submittedSlot.qrVerificationUrl ||
        `https://nammavivasayi.gov.in/verify?token=${submittedSlot.opaqueToken || submittedSlot.tokenNumber}&id=${submittedSlot.bookingId}`;

      QRCode.toCanvas(
        qrCanvasRef.current,
        qrPayload,
        {
          width: 220,
          margin: 2,
          color: {
            dark: '#064e3b',
            light: '#ffffff',
          },
        },
        (error) => {
          if (error) console.error('QR Render error:', error);
        }
      );
    }
  }, [submittedSlot]);

  // Handle centre selection change
  const handleCentreChange = (centreId: string) => {
    const c = centres.find((item) => item.id === centreId || item.centreCode === centreId);
    if (c) {
      setSelectedCentre(c);
      if (c.supportedCrops.length > 0 && !c.supportedCrops.includes(crop)) {
        setCrop(c.supportedCrops[0]);
      }
      if (c.slotWindows.length > 0) {
        setSlotTime(c.slotWindows[0]);
      }
    }
  };

  // Submit Booking
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCentre) return;

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const farmerName = user?.name || user?.fullName || 'Selvakumar R.';
      const farmerId = user?.farmerId || 'TN-AGRI-2026-8841';

      const bookingPayload = {
        farmerName,
        farmerId,
        mandiName: selectedCentre.name,
        crop,
        quantityBags: bags,
        preferredDate: slotDate,
        timeWindow: slotTime,
      };

      const result = await createProcurementBooking(bookingPayload, token);
      setSubmittedSlot(result);

      if (onBookingCreated) {
        onBookingCreated({
          bookingId: result.bookingId,
          mandiName: result.mandiName,
          crop: result.crop,
          quantityBags: result.quantityBags,
          estimatedWeightQuintals: result.estimatedWeightQuintals,
          slotDate: result.slotDate,
          timeWindow: result.timeWindow,
          tokenNumber: result.tokenNumber,
          status: 'confirmed',
          isSample: false,
          isFromDb: true,
        });
      }

      await loadBookings();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit booking. Capacity might be exceeded.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Find capacity status for current selected window
  const currentSlotInfo = slotsAvailability?.slots?.find((s) => s.timeWindow === slotTime);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Error alert if backend call failed */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 flex items-start gap-3 animate-fade-in shadow-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm font-medium flex-1">
            <strong>{language === 'ta' ? 'முன்பதிவு தோல்வியுற்றது:' : 'Booking Submission Error:'}</strong>{' '}
            {errorMsg}
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-xs font-bold text-rose-700 hover:text-rose-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Confirmation View with Privacy-Safe QR Code */}
      {submittedSlot ? (
        <Card
          title={language === 'ta' ? 'முன்பதிவு உறுதி செய்யப்பட்டது' : 'Procurement Slot Confirmed!'}
          subtitle={submittedSlot.mandiName}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-700" />}
          headerAction={
            <Badge variant="emerald" dot>
              MongoDB Verified
            </Badge>
          }
        >
          <div className="p-6 rounded-3xl bg-gradient-to-b from-emerald-50/80 to-white border border-emerald-200 text-center space-y-6">
            <div className="w-16 h-16 mx-auto rounded-3xl bg-emerald-100 text-emerald-800 flex items-center justify-center shadow-inner">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div>
              <span className="text-[11px] font-mono uppercase tracking-widest text-emerald-800 font-bold block">
                {language === 'ta' ? 'அதிகாரப்பூர்வ டோக்கன் எண்' : 'Official Mandi Queue Token'}
              </span>
              <span className="text-4xl font-extrabold font-mono text-emerald-800 tracking-tight my-1 block">
                {submittedSlot.tokenNumber}
              </span>
              <p className="text-xs text-slate-500 font-medium">
                Booking ID: <code className="bg-emerald-100/70 text-emerald-950 px-2 py-0.5 rounded font-bold font-mono">{submittedSlot.bookingId}</code>
              </p>
            </div>

            {/* Privacy-Preserving QR Code Display */}
            <div className="inline-block p-4 bg-white rounded-2xl border-2 border-dashed border-emerald-300 shadow-sm">
              <canvas ref={qrCanvasRef} className="mx-auto rounded-xl" />
              <div className="flex items-center justify-center gap-1.5 mt-2 text-[11px] text-slate-500 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>
                  {language === 'ta'
                    ? 'பாதுகாப்பான QR டோக்கன் (தனிநபர் விவரங்கள் இல்லை)'
                    : 'Encodes opaque token URL only • No PII encoded'}
                </span>
              </div>
            </div>

            {/* Slot Details Summary Table */}
            <div className="max-w-md mx-auto grid grid-cols-2 gap-3 text-left text-xs bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">{language === 'ta' ? 'விவசாயி' : 'Farmer'}</span>
                <span className="font-semibold text-slate-800">{submittedSlot.farmerName}</span>
                <span className="text-[10px] text-slate-500 block font-mono">{submittedSlot.farmerId}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">{language === 'ta' ? 'விளைபொருள்' : 'Commodity'}</span>
                <span className="font-semibold text-slate-800">{submittedSlot.crop}</span>
                <span className="text-[11px] font-bold text-emerald-700 block">
                  {submittedSlot.quantityBags} Bags (~{submittedSlot.estimatedWeightQuintals} Qtl)
                </span>
              </div>
              <div className="col-span-2 pt-2 border-t border-emerald-200/50">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">{language === 'ta' ? 'அறிக்கையிடல் நேரம்' : 'Reporting Window'}</span>
                <span className="font-bold text-slate-800">
                  {submittedSlot.slotDate} • {submittedSlot.timeWindow}
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
              {onNavigateToQueue && (
                <button
                  type="button"
                  onClick={() => onNavigateToQueue(submittedSlot.bookingId)}
                  className="px-6 py-3 rounded-2xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-emerald-700/20 transition-all"
                >
                  <ArrowRight className="w-4 h-4" />
                  {language === 'ta' ? 'வரிசையை நேரடியாகக் காண்க' : 'Track in Live Yard Queue'}
                </button>
              )}
              <button
                type="button"
                onClick={() => setSubmittedSlot(null)}
                className="px-6 py-3 rounded-2xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs transition-colors"
              >
                {language === 'ta' ? 'மற்றொரு முன்பதிவு செய்க' : 'Book Another Slot'}
              </button>
            </div>
          </div>
        </Card>
      ) : (
        /* Booking Reservation Form */
        <Card
          title={t.nav.procurement}
          subtitle="Smart Direct Mandi & DPC Slot Reservation (நேரடி கொள்முதல் முன்பதிவு)"
          icon={<CalendarCheck className="w-5 h-5 text-emerald-700" />}
          headerAction={
            <Badge variant="emerald" dot>
              Phase 5 Live Capacity
            </Badge>
          }
        >
          <p className="text-xs md:text-sm text-slate-600 mb-6">
            {language === 'ta'
              ? 'தமிழ்நாடு நேரடி நெல் கொள்முதல் நிலையங்களில் (DPC) உங்கள் விளைபொருளை இடைத்தரகர் இன்றி MSP விலையில் விற்க முன்பதிவு செய்யுங்கள். நேரம் மற்றும் கொள்ளளவு தரவுத்தளத்தில் நேரடியாகச் சரிபார்க்கப்படுகிறது.'
              : 'Reserve your delivery time window in advance to avoid yard traffic congestion and receive MSP payment directly via DBT. Capacity is validated live in MongoDB.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* FEATURE 1: PROCUREMENT CENTRE SELECTION */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-emerald-700" />
                  {language === 'ta' ? 'கொள்முதல் நிலையம் தேர்வு' : 'Select Procurement Centre'}
                </label>
                <span className="text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                  {selectedCentre?.dataSourceLabel || 'Verified Demo Centre'}
                </span>
              </div>

              {isLoadingCentres ? (
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center gap-2 text-xs text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                  Loading procurement centres...
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {centres.map((c) => {
                    const isSelected = selectedCentre?.id === c.id;
                    return (
                      <div
                        key={c.id}
                        onClick={() => handleCentreChange(c.id)}
                        className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-emerald-50/90 border-emerald-500 ring-2 ring-emerald-500/20'
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <h4 className="text-xs font-bold text-slate-900 leading-snug">
                            {language === 'ta' ? c.nameTa : c.name}
                          </h4>
                          <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded ml-2 shrink-0">
                            {c.centreCode}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
                          <span>📍</span> {c.locationAddress}
                        </p>
                        <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-600 font-medium">
                          <span>🕒 {c.operatingHours}</span>
                          <span>📦 Max {c.dailyCapacityBags} Bags/day</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* FEATURE 2: SLOT BOOKING INPUTS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
              {/* Authenticated Farmer Profile (Read-only / Auto-filled) */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  {language === 'ta' ? 'விவசாயி பெயர் & ஐடி' : 'Farmer Name & ID'}
                </label>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-800 flex items-center justify-between">
                  <span className="font-semibold">{user?.name || user?.fullName || 'Selvakumar R.'}</span>
                  <span className="font-mono text-[11px] bg-white px-2 py-0.5 rounded border border-slate-200 font-bold text-emerald-800">
                    {user?.farmerId || 'TN-AGRI-2026-8841'}
                  </span>
                </div>
              </div>

              {/* Crop Selection */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  {language === 'ta' ? 'பயிர் வகை' : 'Crop Type'}
                </label>
                <select
                  value={crop}
                  onChange={(e) => setCrop(e.target.value)}
                  className="w-full text-xs p-3 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  {selectedCentre?.supportedCrops.map((cr) => (
                    <option key={cr} value={cr}>
                      {cr}
                    </option>
                  )) || (
                    <option value="Paddy Grade A">Paddy Grade A (சம்பா நெல் CR 1009)</option>
                  )}
                </select>
              </div>

              {/* Quantity in Bags with Estimated Weight */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  {language === 'ta' ? 'மூட்டைகள் எண்ணிக்கை (40 கிலோ/மூட்டை)' : 'Estimated Quantity (Bags)'}
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min={1}
                    max={currentSlotInfo?.availableBags || 500}
                    value={bags}
                    onChange={(e) => setBags(Math.max(1, parseInt(e.target.value) || 0))}
                    className="w-full text-xs p-3 pr-20 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 font-bold"
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-400">
                    Bags
                  </div>
                </div>
                <p className="text-[11px] text-emerald-700 font-medium mt-1 flex items-center gap-1">
                  <Scale className="w-3.5 h-3.5" />
                  Estimated: <strong>~{estimatedQuintals} Quintals</strong> (40 kg standard moisture dockage basis)
                </p>
              </div>

              {/* Date Selection */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  {language === 'ta' ? 'விற்பனைத் தேதி' : 'Preferred Date'}
                </label>
                <input
                  type="date"
                  value={slotDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setSlotDate(e.target.value)}
                  className="w-full text-xs p-3 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              {/* Time Window with Live Capacity Badges */}
              <div className="sm:col-span-2">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-emerald-700" />
                    {language === 'ta' ? 'அறிக்கையிடல் நேர இடைவெளி (நேரடி கொள்ளளவு)' : 'Reporting Time Window (Live Slot Capacity)'}
                  </label>
                  {isLoadingSlots && (
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin text-emerald-600" />
                      Checking capacity...
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {(selectedCentre?.slotWindows || ['08:30 AM - 11:30 AM', '11:30 AM - 02:30 PM', '02:30 PM - 05:30 PM']).map((win) => {
                    const isSelected = slotTime === win;
                    const slotData = slotsAvailability?.slots?.find((s) => s.timeWindow === win);
                    const isFull = slotData?.status === 'full' || (slotData && slotData.availableBags <= 0);
                    const isFillingFast = slotData?.status === 'filling_fast';

                    return (
                      <div
                        key={win}
                        onClick={() => {
                          if (!isFull) setSlotTime(win);
                        }}
                        className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                          isFull
                            ? 'opacity-60 bg-slate-100 border-slate-200 cursor-not-allowed'
                            : isSelected
                            ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-500/20 font-bold text-emerald-950'
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{win}</span>
                          {isFull ? (
                            <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded">
                              Full
                            </span>
                          ) : isFillingFast ? (
                            <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                              Fast filling
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                              Available
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1">
                          {slotData ? (
                            <span>
                              {slotData.availableBags} / {slotData.maxCapacityBags} Bags left
                            </span>
                          ) : (
                            <span>Capacity: 250 Bags</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  {language === 'ta'
                    ? 'முன்பதிவு சமர்ப்பித்த பிறகு MongoDB-யில் டோக்கன் உருவாக்கப்படும்'
                    : 'Tokens are issued only after verified MongoDB database confirmation.'}
                </span>
              </div>

              <button
                type="submit"
                disabled={isSubmitting || (currentSlotInfo && currentSlotInfo.availableBags <= 0)}
                className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-700/20 transition-all"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Reserving in MongoDB...</span>
                  </>
                ) : (
                  <>
                    <CalendarCheck className="w-4 h-4" />
                    <span>{language === 'ta' ? 'முன்பதிவை உறுதி செய்' : 'Confirm & Reserve Slot'}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* Booking History Table */}
      <Card
        title={language === 'ta' ? 'உங்கள் கொள்முதல் முன்பதிவுகள்' : 'Your Mandi Slot Reservations'}
        subtitle="Live records retrieved directly from MongoDB"
        icon={<Database className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <button
            onClick={loadBookings}
            disabled={isLoadingBookings}
            className="flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingBookings ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      >
        {isLoadingBookings ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
            Loading reservations...
          </div>
        ) : dbBookings.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No bookings registered yet for this account. Create your first slot above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold">
                  <th className="py-2.5 px-3">Token #</th>
                  <th className="py-2.5 px-3">Centre & Date</th>
                  <th className="py-2.5 px-3">Crop / Bags</th>
                  <th className="py-2.5 px-3">Est. Weight</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dbBookings.map((b) => (
                  <tr key={b.bookingId || b.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-3 font-mono font-bold text-emerald-700">
                      {b.tokenNumber}
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-semibold text-slate-800">{b.mandiName}</p>
                      <p className="text-[11px] text-slate-500 font-mono">
                        {b.slotDate} ({b.timeWindow})
                      </p>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-slate-800">{b.crop}</span>
                      <span className="block text-slate-500 text-[11px]">{b.quantityBags} Bags</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-700 font-medium">
                      ~{b.estimatedWeightQuintals} Qtl
                    </td>
                    <td className="py-3 px-3">
                      <Badge
                        variant={
                          b.status === 'COMPLETED'
                            ? 'emerald'
                            : b.status === 'CHECKED_IN' || b.status === 'IN_QUEUE'
                            ? 'blue'
                            : b.status === 'CANCELLED'
                            ? 'rose'
                            : 'amber'
                        }
                        size="sm"
                      >
                        {b.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5 flex-wrap">
                        {b.billNumber && (
                          <button
                            onClick={async () => {
                              try {
                                const bill = await getDigitalBillApi(b.billNumber!, token!);
                                setSelectedBillForModal(bill);
                                setIsBillModalOpen(true);
                              } catch (err: any) {
                                console.error('Failed to load bill', err);
                              }
                            }}
                            className="px-2.5 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-bold shadow-sm flex items-center gap-1"
                          >
                            <FileText className="w-3 h-3" />
                            {language === 'ta' ? 'ரசீது' : 'Bill'}
                          </button>
                        )}
                        {onNavigateToQueue && (
                          <button
                            onClick={() => onNavigateToQueue(b.bookingId)}
                            className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-[11px] font-bold transition-colors"
                          >
                            {language === 'ta' ? 'வரிசை' : 'Queue'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* TASK 3 & 4: Farmer Digital Bills & Payment Receipts */}
      <Card
        title={language === 'ta' ? 'எனது கொள்முதல் ரசீதுகள் & வங்கி பணம் நிலை' : 'My Digital Procurement Bills & Payment Tracking'}
        subtitle={
          language === 'ta'
            ? 'அரசு நேரடி கொள்முதல் நிலைய எடை ரசீதுகள் மற்றும் நேரடி பணப் பரிமாற்றம் (DBT)'
            : 'Verified electronic weighment receipts, deductions breakdown & PFMS DBT status'
        }
        icon={<FileText className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <button
            onClick={loadFarmerBills}
            disabled={isLoadingBills}
            className="flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingBills ? 'animate-spin' : ''}`} />
            {language === 'ta' ? 'புதுப்பி' : 'Refresh Bills'}
          </button>
        }
      >
        {isLoadingBills ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
            {language === 'ta' ? 'ரசீதுகள் ஏற்றப்படுகின்றன...' : 'Loading verified bills from database...'}
          </div>
        ) : farmerBills.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            {language === 'ta'
              ? 'இதுவரை ரசீதுகள் எதுவும் உருவாக்கப்படவில்லை. மண்டி மையத்தில் பயிர் எடையிடப்பட்டதும் உங்கள் ரசீது இங்கு தோன்றும்.'
              : 'No digital bills issued yet. Your bill will be generated automatically when your produce is weighed at the Mandi centre.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold">
                  <th className="py-2.5 px-3">{language === 'ta' ? 'ரசீது எண்' : 'Bill #'}</th>
                  <th className="py-2.5 px-3">{language === 'ta' ? 'மையம் & தேதி' : 'Centre & Date'}</th>
                  <th className="py-2.5 px-3">{language === 'ta' ? 'பயிர் / எடை' : 'Crop & Weight'}</th>
                  <th className="py-2.5 px-3">{language === 'ta' ? 'விலை / கழிவு' : 'Rate & Deductions'}</th>
                  <th className="py-2.5 px-3">{language === 'ta' ? 'நிகர தொகை' : 'Net Amount'}</th>
                  <th className="py-2.5 px-3">{language === 'ta' ? 'வங்கி நிலை' : 'Payment Status'}</th>
                  <th className="py-2.5 px-3 text-right">{language === 'ta' ? 'நடவடிக்கை' : 'Action'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {farmerBills.map((bill) => (
                  <tr key={bill.billNumber} className="hover:bg-slate-50/50">
                    <td className="py-3 px-3 font-mono font-bold text-emerald-800">
                      {bill.billNumber}
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-800 block">{bill.mandiName}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(bill.createdAt || bill.transactionDate || Date.now()).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-slate-800 block">{bill.crop}</span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {(bill.acceptedWeightKg ?? 0).toLocaleString()} kg (~{(bill.actualNetWeightQuintals ?? bill.acceptedWeightQuintals) ?? 0} Qtl)
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-slate-800 block">₹{(bill.pricePerKg ?? 0).toFixed(2)}/kg</span>
                      <span className="text-[10px] text-rose-600 block">
                        -₹{((bill.totalDeductionsAmount ?? bill.totalDeductions) ?? 0).toLocaleString()} {language === 'ta' ? 'கழிவு' : 'ded.'}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-black text-emerald-800 text-sm">
                      ₹{(bill.netAmount ?? 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          bill.paymentStatus === 'PAID'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : bill.paymentStatus === 'PROCESSING'
                            ? 'bg-blue-100 text-blue-800 border border-blue-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}
                      >
                        {bill.paymentStatus}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => {
                          setSelectedBillForModal(bill);
                          setIsBillModalOpen(true);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[11px] font-bold shadow-sm inline-flex items-center gap-1"
                      >
                        <Printer className="w-3 h-3" />
                        {language === 'ta' ? 'ரசீது பார்க்க' : 'View & Print'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* TASK 3: Print-friendly Farmer Digital Bill Modal */}
      <DigitalBillModal
        isOpen={isBillModalOpen}
        onClose={() => setIsBillModalOpen(false)}
        bill={selectedBillForModal}
        isStaff={false}
      />
    </div>
  );
};

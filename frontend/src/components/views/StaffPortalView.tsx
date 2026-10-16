import React, { useState, useEffect } from 'react';
import {
  Building2,
  ShieldAlert,
  Search,
  RefreshCw,
  CheckCircle2,
  Scale,
  Loader2,
  AlertCircle,
  QrCode,
  Check,
  FileText,
  Printer,
} from 'lucide-react';

import { useAuth } from '../../context/AuthContext';
import { DigitalBillModal } from '../common/DigitalBillModal';
import {
  getStaffQueueApi,
  verifyStaffTokenApi,
  staffCheckInApi,
  staffRecordWeighingApi,
  getStaffBillsApi,
  getDigitalBillApi,
  staffMoveToQueueApi,
  staffMoveToProcessingApi,
  staffCancelBookingApi,
  type ProcurementBookingEntity,
  type TokenVerifyResponse,
  type StaffQueueOverviewResponse,
  type DigitalBillEntity,
  type StaffWeighingPayload,
} from '../../services/api';

export const StaffPortalView: React.FC = () => {
  const { user, token } = useAuth();

  const [queue, setQueue] = useState<ProcurementBookingEntity[]>([]);
  const [overviewData, setOverviewData] = useState<StaffQueueOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedTimeSlot, setSelectedTimeSlot] = useState<string>('all');

  // FEATURE 3: Token Verification Form / Scanner State
  const [inputToken, setInputToken] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedTokenResult, setVerifiedTokenResult] = useState<TokenVerifyResponse | null>(null);

  // Gate Check-in State
  const [checkInNotes, setCheckInNotes] = useState('');
  const [isCheckingIn, setIsCheckingIn] = useState(false);

  // FEATURE 5: Weighing & Digital Bill Form State
  const [activeBookingForWeighing, setActiveBookingForWeighing] = useState<ProcurementBookingEntity | null>(null);
  const [acceptedWeightKg, setAcceptedWeightKg] = useState<number>(1500.0);
  const [actualNetWeight, setActualNetWeight] = useState<number>(15.0);
  const [pricePerKg, setPricePerKg] = useState<number>(23.20);
  const [pricePerQuintal, setPricePerQuintal] = useState<number>(2320.0); // Paddy Grade A MSP
  const [qualityDeductions, setQualityDeductions] = useState<number>(0.0);
  const [otherDeductions, setOtherDeductions] = useState<number>(0.0);
  const [moisturePercent, setMoisturePercent] = useState<number>(14.0);
  const [qualityGrade, setQualityGrade] = useState<string>('FAQ Grade A');
  const [paymentStatus, setPaymentStatus] = useState<'PENDING' | 'PROCESSING' | 'PAID'>('PENDING');
  const [transactionNotes, setTransactionNotes] = useState<string>('Electronic weighbridge gross & tare certified.');
  const [isSavingTx, setIsSavingTx] = useState(false);

  // Digital Bill Modal State & Centre Bills State
  const [activeBillForModal, setActiveBillForModal] = useState<DigitalBillEntity | null>(null);
  const [isBillModalOpen, setIsBillModalOpen] = useState(false);
  const [staffBills, setStaffBills] = useState<DigitalBillEntity[]>([]);
  const [isLoadingBills, setIsLoadingBills] = useState(false);

  // Live Math calculations:
  // Gross = acceptedWeightKg * pricePerKg
  const grossAmount = Math.max(0, Number((acceptedWeightKg * pricePerKg).toFixed(2)));
  const totalDeductions = Number((Number(qualityDeductions || 0) + Number(otherDeductions || 0)).toFixed(2));
  const isDeductionsExceeding = totalDeductions > grossAmount;
  const netPayable = Math.max(0, Number((grossAmount - totalDeductions).toFixed(2)));

  // 1. Fetch queue for staff's permitted centre
  const fetchQueue = async () => {
    if (!token) return;
    try {
      setErrorMsg(null);
      const res = await getStaffQueueApi(token, {
        date: selectedDate || undefined,
        timeWindow: selectedTimeSlot !== 'all' ? selectedTimeSlot : undefined,
        statusFilter: statusFilter !== 'all' && statusFilter !== 'active' ? statusFilter : undefined,
      });
      if (res) {
        setOverviewData(res);
        if (statusFilter === 'active' && res.activeQueue) {
          setQueue(res.activeQueue);
        } else if (res.bookings) {
          setQueue(res.bookings);
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch staff queue.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch Centre Digital Bills
  const fetchStaffBills = async () => {
    if (!token) return;
    setIsLoadingBills(true);
    try {
      const res = await getStaffBillsApi(token);
      setStaffBills(res.bills || []);
    } catch (err: any) {
      console.error('Failed to load bills:', err);
    } finally {
      setIsLoadingBills(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    fetchStaffBills();
    const interval = setInterval(() => {
      fetchQueue();
      fetchStaffBills();
    }, 15000);
    return () => clearInterval(interval);
  }, [token, selectedDate, selectedTimeSlot, statusFilter]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchQueue();
    fetchStaffBills();
  };

  // 2. FEATURE 3: Token Verification (Manual entry or QR payload)
  const handleVerifyToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputToken.trim() || !token) return;

    setIsVerifying(true);
    setVerifiedTokenResult(null);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      let cleanInput = inputToken.trim();
      // If a full QR verification URL was pasted or scanned, parse query parameters
      if (cleanInput.includes('token=')) {
        try {
          const urlObj = new URL(cleanInput);
          const tVal = urlObj.searchParams.get('token');
          if (tVal) cleanInput = tVal;
        } catch {
          // Keep clean input as is
        }
      }

      const res = await verifyStaffTokenApi({ token: cleanInput }, token);
      setVerifiedTokenResult(res);
      if (res.isValid) {
        setSuccessMsg(`Token verified: ${res.tokenNumber} (${res.farmerName})`);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Token verification failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  // 3. FEATURE 5: Gate Check-In Action
  const handleCheckIn = async (bookingId: string) => {
    if (!token) return;
    setIsCheckingIn(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await staffCheckInApi(bookingId, checkInNotes || 'Gate arrival & QR verified', token);
      setSuccessMsg(`Gate check-in recorded for booking ${bookingId}`);
      setCheckInNotes('');
      // Refresh verified result and queue
      if (verifiedTokenResult && verifiedTokenResult.bookingId === bookingId) {
        setVerifiedTokenResult({
          ...verifiedTokenResult,
          status: 'CHECKED_IN',
          canCheckIn: false,
          canWeigh: true,
          message: 'Vehicle admitted to yard queue.',
        });
      }
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to check in vehicle.');
    } finally {
      setIsCheckingIn(false);
    }
  };

  // FEATURE 4: Move booking to IN_QUEUE (yard queue)
  const handleMoveToQueue = async (bookingId: string) => {
    if (!token) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await staffMoveToQueueApi(bookingId, token);
      setSuccessMsg(`Booking ${bookingId} assigned to yard weighbridge queue.`);
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to assign to queue.');
    }
  };

  // FEATURE 4: Move booking to PROCESSING (on weighbridge)
  const handleMoveToProcessing = async (bookingId: string) => {
    if (!token) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await staffMoveToProcessingApi(bookingId, token);
      setSuccessMsg(`Booking ${bookingId} moved to PROCESSING — weighbridge active.`);
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to move to processing.');
    }
  };

  // FEATURE 4: Cancel booking with audit trail
  const handleCancelBooking = async (bookingId: string) => {
    if (!token) return;
    if (!window.confirm(`Cancel booking ${bookingId}? This action will be logged in the audit trail.`)) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await staffCancelBookingApi(bookingId, token);
      setSuccessMsg(`Booking ${bookingId} cancelled and recorded in audit trail.`);
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to cancel booking.');
    }
  };

  // 4. Open Weighing Modal
  const openWeighingModal = (booking: ProcurementBookingEntity) => {
    setActiveBookingForWeighing(booking);
    // Standard initial kg: from acceptedWeightKg, or quintals * 100, or bags * 40
    const initialKg = booking.acceptedWeightKg ||
      (booking.actualNetWeightQuintals ? booking.actualNetWeightQuintals * 100 : (booking.estimatedWeightQuintals ? booking.estimatedWeightQuintals * 100 : (booking.quantityBags ? booking.quantityBags * 40 : 1500)));
    setAcceptedWeightKg(initialKg);
    setPricePerKg(23.20); // Default TN Paddy Grade A MSP rate: ₹23.20/kg
    setQualityDeductions(0.0);
    setOtherDeductions(0.0);
    setPaymentStatus('PENDING'); // Task 4: Do not mark as PAID merely because bill was generated
    setTransactionNotes('Standard electronic weighbridge certification.');
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  // 5. Submit Weighing & Issue Digital Bill
  const handleSaveWeighingTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBookingForWeighing || !token) return;

    if (acceptedWeightKg <= 0 || pricePerKg <= 0) {
      setErrorMsg('Accepted weight and price per kg must be positive values greater than zero.');
      return;
    }
    if (qualityDeductions < 0 || otherDeductions < 0) {
      setErrorMsg('Deductions cannot be negative.');
      return;
    }
    if (isDeductionsExceeding) {
      setErrorMsg(`Total deductions (₹${totalDeductions.toFixed(2)}) cannot exceed gross amount (₹${grossAmount.toFixed(2)}).`);
      return;
    }

    setIsSavingTx(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const payload: StaffWeighingPayload = {
        acceptedWeightKg: Number(acceptedWeightKg),
        pricePerKg: Number(pricePerKg),
        qualityDeductionsAmount: Number(qualityDeductions || 0),
        otherDeductionsAmount: Number(otherDeductions || 0),
        paymentStatus: paymentStatus,
        notes: transactionNotes,
      };

      const bill = await staffRecordWeighingApi(activeBookingForWeighing.bookingId, payload, token);
      setSuccessMsg(
        `Weighment and Digital Bill #${bill.billNumber} created successfully! Gross: ₹${bill.grossAmount.toLocaleString()}, Net: ₹${bill.netAmount.toLocaleString()}`
      );
      setActiveBookingForWeighing(null);
      // Immediately display digital bill modal
      setActiveBillForModal(bill);
      setIsBillModalOpen(true);

      await fetchQueue();
      await fetchStaffBills();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to record weighing and generate digital bill.');
    } finally {
      setIsSavingTx(false);
    }
  };

  // If user is not staff, show warning
  if (user?.role !== 'staff') {
    return (
      <div className="bg-white rounded-3xl p-8 border border-amber-200 shadow-sm text-center max-w-xl mx-auto my-12">
        <div className="w-16 h-16 rounded-3xl bg-amber-100 text-amber-800 flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">Access Restricted to Procurement Staff</h3>
        <p className="text-sm text-slate-600 mb-6">
          This dashboard is reserved for authorized Direct Purchase Centre (DPC) officers, weighbridge operators, and mandi staff.
        </p>
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
          <p className="font-semibold text-slate-700 mb-1">Demo Staff Credentials:</p>
          <p>
            Mobile: <code className="bg-white px-2 py-0.5 rounded border font-mono font-bold text-emerald-700">9842012345</code> | Password: <code className="bg-white px-2 py-0.5 rounded border font-mono font-bold text-emerald-700">MandiStaff@2026</code>
          </p>
        </div>
      </div>
    );
  }

  // Filtered queue items
  const filteredQueue = queue.filter((item) => {
    const matchesSearch =
      item.farmerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.farmerId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.bookingId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.tokenNumber.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' ||
      item.status.toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Staff Identity & Mandi Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 p-6 md:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shrink-0">
              <Building2 className="w-7 h-7 text-emerald-300" />
            </div>
            <div>
              <span className="text-[11px] font-mono tracking-wider uppercase text-emerald-300 font-bold">
                Mandi Operational Portal • Authorized Staff Role
              </span>
              <h2 className="text-2xl font-black mt-0.5">{user.name}</h2>
              <p className="text-xs text-emerald-100/90 mt-1 flex items-center gap-1.5">
                <span>📍 Permitted Centre:</span>
                <strong className="underline underline-offset-2">
                  {user.mandiName || user.mandiAssigned || 'Thanjavur DPC Centre #3'}
                </strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Sync Yard Records
            </button>
          </div>
        </div>
      </div>

      {/* Global Alerts */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm font-medium flex-1">
            <strong>Error:</strong> {errorMsg}
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-xs font-bold text-rose-700">✕</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-900 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm font-medium flex-1">
            <strong>Success:</strong> {successMsg}
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-xs font-bold text-emerald-700">✕</button>
        </div>
      )}

      {/* FEATURE 3: TOKEN VERIFICATION CARD */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <QrCode className="w-4 h-4 text-emerald-700" />
            Gate Token Verification & QR Scanner
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">
            Direct MongoDB Verification
          </span>
        </div>

        <form onSubmit={handleVerifyToken} className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Scan QR or enter Token (e.g. TN-DPC-851 or NV-...) or Booking ID"
              value={inputToken}
              onChange={(e) => setInputToken(e.target.value)}
              className="w-full text-xs p-3 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={isVerifying || !inputToken.trim()}
            className="px-6 py-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            {isVerifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Verify Token</span>}
          </button>
        </form>

        {/* Verification Result Card */}
        {verifiedTokenResult && (
          <div
            className={`p-4 rounded-2xl border transition-all text-xs ${
              verifiedTokenResult.isValid
                ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
                : 'bg-rose-50 border-rose-300 text-rose-950'
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-base font-extrabold font-mono text-emerald-800">
                    {verifiedTokenResult.tokenNumber || 'Invalid'}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      verifiedTokenResult.isValid ? 'bg-emerald-200 text-emerald-900' : 'bg-rose-200 text-rose-900'
                    }`}
                  >
                    {verifiedTokenResult.status}
                  </span>
                </div>
                <p className="font-medium text-slate-700">{verifiedTokenResult.message}</p>
                {verifiedTokenResult.isValid && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] text-slate-600">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Farmer</span>
                      <span className="font-semibold">{verifiedTokenResult.farmerName}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Crop / Bags</span>
                      <span className="font-semibold">{verifiedTokenResult.crop} ({verifiedTokenResult.quantityBags} Bags)</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Scheduled Window</span>
                      <span className="font-semibold">{verifiedTokenResult.slotDate} ({verifiedTokenResult.timeWindow})</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Centre</span>
                      <span className="font-semibold">{verifiedTokenResult.mandiName}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Actions available based on status */}
              <div className="flex flex-col gap-2 shrink-0">
                {verifiedTokenResult.canCheckIn && (
                  <button
                    onClick={() => handleCheckIn(verifiedTokenResult.bookingId)}
                    disabled={isCheckingIn}
                    className="px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm"
                  >
                    {isCheckingIn ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    Check In Vehicle
                  </button>
                )}

                {verifiedTokenResult.canWeigh && (
                  <button
                    onClick={() => {
                      const match = queue.find((q) => q.bookingId === verifiedTokenResult.bookingId);
                      if (match) openWeighingModal(match);
                    }}
                    className="px-4 py-2 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    Record Weighing
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* FEATURE 5: WEIGHING MODAL */}
      {activeBookingForWeighing && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 md:p-8 max-w-xl w-full shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-5 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-800 font-bold block">
                  Weighbridge Slip & DBT Ledger
                </span>
                <h3 className="text-lg font-bold text-slate-900">
                  {activeBookingForWeighing.tokenNumber} • {activeBookingForWeighing.farmerName}
                </h3>
              </div>
              <button
                onClick={() => setActiveBookingForWeighing(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 font-bold flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveWeighingTransaction} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Net Weight */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Actual Net Weight (Quintals) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.1"
                    value={actualNetWeight}
                    onChange={(e) => setActualNetWeight(Math.max(0.01, parseFloat(e.target.value) || 0))}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-bold text-slate-900 font-mono"
                    required
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Gross weight minus vehicle tare weight
                  </span>
                </div>

                {/* Price Per Quintal (MSP) */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    MSP Rate (₹ per Quintal) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    value={pricePerQuintal}
                    onChange={(e) => setPricePerQuintal(Math.max(1, parseFloat(e.target.value) || 0))}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-bold text-slate-900 font-mono"
                    required
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Govt Paddy Grade A MSP: ₹2,320/Qtl
                  </span>
                </div>

                {/* Moisture % */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Moisture Meter Reading (%) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="5"
                    max="35"
                    value={moisturePercent}
                    onChange={(e) => setMoisturePercent(parseFloat(e.target.value) || 14.0)}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-bold text-slate-900 font-mono"
                    required
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Standard FAQ tolerance: max 17.0%
                  </span>
                </div>

                {/* Quality Grade */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Quality Standard
                  </label>
                  <select
                    value={qualityGrade}
                    onChange={(e) => setQualityGrade(e.target.value)}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-semibold text-slate-900"
                  >
                    <option value="FAQ Grade A (Standard)">FAQ Grade A (Standard)</option>
                    <option value="Common Paddy Standard">Common Paddy Standard</option>
                    <option value="Super Fine Variety">Super Fine Variety</option>
                  </select>
                </div>

                {/* Custom Deductions */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Additional Cess / Fee Deductions (₹)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={otherDeductions}
                    onChange={(e) => setOtherDeductions(Math.max(0, parseFloat(e.target.value) || 0))}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-bold text-slate-900 font-mono"
                  />
                </div>

                {/* Payment Status */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    DBT Ledger Payment Status
                  </label>
                  <select
                    value={paymentStatus}
                    onChange={(e) => setPaymentStatus(e.target.value as any)}
                    className="w-full p-3 bg-white rounded-xl border border-slate-300 font-semibold text-slate-900"
                  >
                    <option value="PROCESSING">PROCESSING (Queued for PFMS)</option>
                    <option value="PENDING">PENDING (Awaiting Verification)</option>
                    <option value="PAID">PAID (DBT Cleared)</option>
                  </select>
                </div>
              </div>

              {/* Transaction Notes */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  Weighbridge Operator Notes & Remarks
                </label>
                <input
                  type="text"
                  value={transactionNotes}
                  onChange={(e) => setTransactionNotes(e.target.value)}
                  placeholder="e.g. Weigh slip #9012, truck tare checked"
                  className="w-full p-3 bg-white rounded-xl border border-slate-300 text-xs text-slate-800"
                />
              </div>

              {/* Automatic Math Verification Box */}
              <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 space-y-1.5 font-medium">
                <div className="flex justify-between text-slate-700">
                  <span>Gross Amount ({actualNetWeight} Qtl × ₹{pricePerQuintal}):</span>
                  <span className="font-mono font-bold">₹{grossAmount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-rose-700">
                  <span>
                    Moisture Deduction ({moisturePercent > 17 ? `${(moisturePercent - 17).toFixed(1)}% dockage` : '0% within FAQ limit'}):
                  </span>
                  <span className="font-mono font-bold">-₹{qualityDeductions.toLocaleString()}</span>
                </div>
                {otherDeductions > 0 && (
                  <div className="flex justify-between text-rose-700">
                    <span>Other Cess / Fees:</span>
                    <span className="font-mono font-bold">-₹{otherDeductions.toLocaleString()}</span>
                  </div>
                )}
                <div className="pt-2 border-t border-emerald-200 flex justify-between items-center text-sm font-black text-emerald-950">
                  <span>Net Recorded Amount:</span>
                  <span className="text-base font-mono text-emerald-800">₹{netPayable.toLocaleString()}</span>
                </div>
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveBookingForWeighing(null)}
                  className="px-5 py-2.5 rounded-xl border border-slate-300 text-slate-600 hover:bg-slate-50 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingTx}
                  className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold flex items-center gap-2 shadow-md"
                >
                  {isSavingTx ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  Save Transaction Ledger
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FEATURE 5: QUEUE LISTING TABLE */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Procurement Centre Queue & Booking Management
            </h3>
            <p className="text-xs text-slate-500">
              Active yard intake records for {user.mandiName || 'Thanjavur Direct Procurement Centre #3'}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-2 flex-wrap">
            <div className="relative">
              <input
                type="text"
                placeholder="Search token, farmer or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="text-xs p-2.5 pl-8 bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-emerald-500 w-44 sm:w-48"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            </div>

            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-xl font-semibold text-slate-700"
              title="Filter by Booking Date"
            />

            <select
              value={selectedTimeSlot}
              onChange={(e) => setSelectedTimeSlot(e.target.value)}
              className="text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-xl font-semibold text-slate-700"
            >
              <option value="all">All Time Slots</option>
              <option value="08:30 AM - 11:30 AM">08:30 AM - 11:30 AM</option>
              <option value="11:30 AM - 02:30 PM">11:30 AM - 02:30 PM</option>
              <option value="02:30 PM - 05:30 PM">02:30 PM - 05:30 PM</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-xl font-semibold text-slate-700"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Queue (Arrived)</option>
              <option value="BOOKED">BOOKED</option>
              <option value="CHECKED_IN">CHECKED_IN</option>
              <option value="IN_QUEUE">IN_QUEUE</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>
        </div>

        {/* TASK 3: Category filter chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'all'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Bookings ({overviewData?.totalBookings ?? queue.length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('active')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'active'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
            }`}
          >
            Active Queue ({overviewData?.activeQueue?.length ?? queue.filter(q => ['CHECKED_IN', 'IN_QUEUE', 'PROCESSING'].includes(q.status)).length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('CHECKED_IN')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'CHECKED_IN'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-blue-50 text-blue-800 hover:bg-blue-100'
            }`}
          >
            Checked-In ({overviewData?.checkedIn?.length ?? queue.filter(q => q.status === 'CHECKED_IN').length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('IN_QUEUE')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'IN_QUEUE'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-indigo-50 text-indigo-800 hover:bg-indigo-100'
            }`}
          >
            In Yard Queue ({overviewData?.inQueue?.length ?? queue.filter(q => q.status === 'IN_QUEUE').length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('PROCESSING')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'PROCESSING'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'bg-purple-50 text-purple-800 hover:bg-purple-100'
            }`}
          >
            Weighbridge ({overviewData?.processing?.length ?? queue.filter(q => q.status === 'PROCESSING').length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('COMPLETED')}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold transition-all ${
              statusFilter === 'COMPLETED'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
            }`}
          >
            Completed ({overviewData?.completed?.length ?? queue.filter(q => q.status === 'COMPLETED').length})
          </button>
          {overviewData?.lastUpdated && (
            <span className="text-[10px] text-slate-400 font-mono ml-auto">
              Last synced: {overviewData.lastUpdated}
            </span>
          )}
        </div>

        {/* Table */}
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
            Loading yard queue...
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No bookings found matching the filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold">
                  <th className="py-3 px-3">Token #</th>
                  <th className="py-3 px-3">Farmer Details</th>
                  <th className="py-3 px-3">Crop / Bags</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Weighment & Net DBT</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredQueue.map((item) => {
                  const isCompleted = item.status === 'COMPLETED' || item.status === 'dbt_completed';
                  const isCheckedIn = item.status === 'CHECKED_IN' || item.status === 'IN_QUEUE' || item.status === 'quality_checked';
                  const isBooked = item.status === 'BOOKED' || item.status === 'confirmed';

                  return (
                    <tr key={item.bookingId || item.id} className="hover:bg-slate-50/60">
                      <td className="py-3 px-3">
                        <span className="font-mono font-bold text-emerald-800 block">
                          {item.tokenNumber}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {item.bookingId}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span className="font-semibold text-slate-800 block">
                          {item.farmerName}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {item.farmerId} • {item.slotDate}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span className="font-medium text-slate-800 block">{item.crop}</span>
                        <span className="text-slate-500 text-[11px] block">
                          {item.quantityBags} Bags (~{item.estimatedWeightQuintals} Qtl)
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isCompleted
                              ? 'bg-emerald-100 text-emerald-800'
                              : isCheckedIn
                              ? 'bg-blue-100 text-blue-800'
                              : item.status === 'CANCELLED'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        {item.transaction ? (
                          <div>
                            <span className="font-bold text-emerald-800 font-mono block">
                              ₹{item.transaction.netPayableAmount.toLocaleString()}
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {item.transaction.actualNetWeightQuintals} Qtl ({item.transaction.paymentStatus})
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Pending weighment</span>
                        )}
                      </td>

                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5 flex-wrap">
                          {/* BOOKED → CHECKED_IN */}
                          {isBooked && (
                            <button
                              onClick={() => handleCheckIn(item.bookingId)}
                              className="px-2 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-bold shadow-sm"
                            >
                              Check In
                            </button>
                          )}

                          {/* CHECKED_IN → IN_QUEUE */}
                          {item.status === 'CHECKED_IN' && (
                            <button
                              onClick={() => handleMoveToQueue(item.bookingId)}
                              className="px-2 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-bold shadow-sm"
                            >
                              → Queue
                            </button>
                          )}

                          {/* IN_QUEUE → PROCESSING */}
                          {item.status === 'IN_QUEUE' && (
                            <button
                              onClick={() => handleMoveToProcessing(item.bookingId)}
                              className="px-2 py-1 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-[10px] font-bold shadow-sm"
                            >
                              → Process
                            </button>
                          )}

                          {/* Weigh & Price (for any non-completed, non-cancelled) */}
                          {/* Weigh & Generate Bill (for any non-completed, non-cancelled) */}
                          {!isCompleted && item.status !== 'CANCELLED' && (
                            <button
                              onClick={() => openWeighingModal(item)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-bold shadow-sm flex items-center gap-1"
                            >
                              <Scale className="w-3 h-3" />
                              Weigh & Bill
                            </button>
                          )}

                          {/* View Bill (if completed) */}
                          {isCompleted && (item.billNumber || item.bill?.billNumber) && (
                            <button
                              onClick={async () => {
                                const bNum = item.billNumber || item.bill?.billNumber;
                                if (!bNum || !token) return;
                                try {
                                  const b = await getDigitalBillApi(bNum, token);
                                  setActiveBillForModal(b);
                                  setIsBillModalOpen(true);
                                } catch (e: any) {
                                  setErrorMsg(e.message || 'Failed to open bill');
                                }
                              }}
                              className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 text-[10px] font-bold flex items-center gap-1 shadow-sm"
                            >
                              <FileText className="w-3 h-3 text-emerald-700" />
                              View Bill
                            </button>
                          )}

                          {/* Cancel (for any non-completed) */}
                          {!isCompleted && item.status !== 'CANCELLED' && (
                            <button
                              onClick={() => handleCancelBooking(item.bookingId)}
                              className="px-2 py-1 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-800 text-[10px] font-bold"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Centre Digital Bills & Payment Tracking Section */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Centre Digital Bills & Payment Tracking</h3>
              <p className="text-xs text-slate-500">Official procurement bills & PFMS Direct Benefit Transfer status</p>
            </div>
          </div>
          <button
            onClick={fetchStaffBills}
            disabled={isLoadingBills}
            className="self-start sm:self-auto px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingBills ? 'animate-spin' : ''}`} />
            Refresh Bills
          </button>
        </div>

        {isLoadingBills ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
            Loading bills from MongoDB...
          </div>
        ) : staffBills.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No bills issued yet for this centre. Completed weighments will appear here automatically.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold">
                  <th className="py-2.5 px-3">Bill Number</th>
                  <th className="py-2.5 px-3">Booking ID</th>
                  <th className="py-2.5 px-3">Farmer Details</th>
                  <th className="py-2.5 px-3">Crop / Weight</th>
                  <th className="py-2.5 px-3">Gross & Deductions</th>
                  <th className="py-2.5 px-3">Net Disbursed</th>
                  <th className="py-2.5 px-3">Payment Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {staffBills.map((b) => (
                  <tr key={b.billNumber} className="hover:bg-slate-50/50">
                    <td className="py-3 px-3 font-mono font-bold text-emerald-800">
                      {b.billNumber}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600">
                      {b.bookingId}
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-800 block">{b.farmerName}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{b.farmerId}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-slate-800 block">{b.crop}</span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {(b.acceptedWeightKg ?? 0).toLocaleString()} kg (~{(b.actualNetWeightQuintals ?? b.acceptedWeightQuintals) ?? 0} Qtl)
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-slate-800 block">₹{(b.grossAmount ?? 0).toLocaleString()}</span>
                      <span className="text-[10px] text-rose-600 block">
                        -₹{((b.totalDeductionsAmount ?? b.totalDeductions) ?? 0).toLocaleString()} ded.
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-black text-emerald-800">
                      ₹{(b.netAmount ?? 0).toLocaleString()}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          b.paymentStatus === 'PAID'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : b.paymentStatus === 'PROCESSING'
                            ? 'bg-blue-100 text-blue-800 border border-blue-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}
                      >
                        {b.paymentStatus}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => {
                          setActiveBillForModal(b);
                          setIsBillModalOpen(true);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-bold shadow-sm inline-flex items-center gap-1"
                      >
                        <Printer className="w-3 h-3" />
                        View & Update
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* TASK 1 & 2: STAFF WEIGHING & BILLING MODAL */}
      {activeBookingForWeighing && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 my-8">
            <div className="flex items-start justify-between border-b border-slate-100 pb-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                  <Scale className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">
                    Staff Weighment & Billing Form
                  </h3>
                  <p className="text-xs text-slate-500">
                    Official Mandi Crop Weighing, Deductions & Bill Generation
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveBookingForWeighing(null)}
                className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            {/* Booking Details Summary */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs mb-4">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Booking ID</span>
                <span className="font-mono font-bold text-slate-800">{activeBookingForWeighing.bookingId}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Token Number</span>
                <span className="font-mono font-bold text-emerald-800">{activeBookingForWeighing.tokenNumber}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Farmer Name</span>
                <span className="font-semibold text-slate-800">{activeBookingForWeighing.farmerName}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Crop (From Booking)</span>
                <span className="font-semibold text-emerald-800">{activeBookingForWeighing.crop}</span>
              </div>
            </div>

            <form onSubmit={handleSaveWeighingTransaction} className="space-y-4">
              {/* Field 1: Accepted Crop Weight in kg */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Accepted Crop Weight (kg) *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={acceptedWeightKg}
                      onChange={(e) => setAcceptedWeightKg(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">kg</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    = {(acceptedWeightKg / 100).toFixed(2)} Quintals
                  </span>
                </div>

                {/* Field 2: Configured Price per kg */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Configured Price (₹/kg) *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={pricePerKg}
                      onChange={(e) => setPricePerKg(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">₹/kg</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    = ₹{(pricePerKg * 100).toFixed(2)} / Quintal MSP
                  </span>
                </div>
              </div>

              {/* Deductions: Quality & Other */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Quality Deductions (₹)
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={qualityDeductions}
                      onChange={(e) => setQualityDeductions(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">₹</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    Moisture & foreign matter deductions
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Other Deductions (₹)
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={otherDeductions}
                      onChange={(e) => setOtherDeductions(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono text-sm text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">₹</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    Authorized handling / gunny charges
                  </span>
                </div>
              </div>

              {/* Initial Payment Status Assignment & Notes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Initial Payment Status
                  </label>
                  <select
                    value={paymentStatus}
                    onChange={(e) => setPaymentStatus(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-900 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="PENDING">PENDING (Direct Benefit Transfer Queued)</option>
                    <option value="PROCESSING">PROCESSING (Under Bank PFMS Review)</option>
                  </select>
                  <span className="text-[10px] text-amber-700 mt-0.5 block">
                    * Status cannot be set to PAID until verified bank transfer.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Notes / Observations
                  </label>
                  <input
                    type="text"
                    value={transactionNotes}
                    onChange={(e) => setTransactionNotes(e.target.value)}
                    placeholder="E.g. Certified on weighbridge #2"
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* TASK 2: LIVE AMOUNT CALCULATION CARD */}
              <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 space-y-2">
                <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                  Amount Calculation Summary (Decimal Precision)
                </span>
                <div className="flex justify-between text-xs text-slate-700">
                  <span>Gross Amount ({acceptedWeightKg.toLocaleString()} kg × ₹{pricePerKg.toFixed(2)}):</span>
                  <span className="font-mono font-bold">₹{grossAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-xs text-rose-700">
                  <span>Total Deductions (Quality + Other):</span>
                  <span className="font-mono font-bold">-₹{totalDeductions.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <div className="border-t border-emerald-200/80 pt-2 flex justify-between text-sm font-black text-emerald-950">
                  <span>Net Payable Amount:</span>
                  <span className="font-mono text-base text-emerald-700">₹{netPayable.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>

                {isDeductionsExceeding && (
                  <div className="p-2.5 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-xs font-bold flex items-center gap-2 mt-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>Deductions exceed gross amount. Please adjust deductions to proceed.</span>
                  </div>
                )}

                <p className="text-[10px] text-slate-500 italic pt-1">
                  * All amounts are recalculated and verified independently on the backend; amounts sent by the frontend are strictly validated.
                </p>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveBookingForWeighing(null)}
                  className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingTx || isDeductionsExceeding || acceptedWeightKg <= 0 || pricePerKg <= 0}
                  className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white text-xs font-bold shadow-md shadow-emerald-700/20 flex items-center gap-2"
                >
                  {isSavingTx ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving & Generating Bill...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Confirm Weighment & Issue Bill</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TASK 3 & 4: DIGITAL BILL MODAL */}
      <DigitalBillModal
        isOpen={isBillModalOpen}
        onClose={() => setIsBillModalOpen(false)}
        bill={activeBillForModal}
        isStaff={true}
        onPaymentUpdated={(updatedBill: DigitalBillEntity) => {
          setActiveBillForModal(updatedBill);
          fetchQueue();
          fetchStaffBills();
          setSuccessMsg(`Payment status updated to ${updatedBill.paymentStatus} for Bill #${updatedBill.billNumber}`);
        }}
      />
    </div>
  );
};

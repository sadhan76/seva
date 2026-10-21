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
  Megaphone,
  UserX,
  ClipboardCheck,
  BarChart3,
  Lock,
  Unlock,
  Layers,
  Power,
  Clock,
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
  staffQualityInspectionApi,
  staffNoShowApi,
  getProcurementRatesApi,
  getNowServingApi,
  staffCallNextTokenApi,
  getDailyProcurementReportApi,
  closeSlotApi,
  reopenSlotApi,
  getSlotClosuresApi,
  getProcurementCentres,
  setProcurementCentreStatusApi,
  type ProcurementBookingEntity,
  type TokenVerifyResponse,
  type StaffQueueOverviewResponse,
  type DigitalBillEntity,
  type StaffWeighingPayload,
  type QualityInspectionPayload,
  type ProcurementRateItem,
  type NowServingResponse,
  type DailyProcurementReportResponse,
  type SlotClosureEntity,
  type ProcurementCentreItem,
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

  // PHASE 3 — Quality Inspection State
  const [activeBookingForQI, setActiveBookingForQI] = useState<ProcurementBookingEntity | null>(null);
  const [qiAcceptedWeightKg, setQiAcceptedWeightKg] = useState<number>(0);
  const [qiRejectedWeightKg, setQiRejectedWeightKg] = useState<number>(0);
  const [qiMoisturePercent, setQiMoisturePercent] = useState<number>(14.0);
  const [qiQualityGrade, setQiQualityGrade] = useState<string>('FAQ Grade A (Standard)');
  const [qiRejectionReason, setQiRejectionReason] = useState<string>('');
  const [qiNotes, setQiNotes] = useState<string>('');
  const [isSubmittingQI, setIsSubmittingQI] = useState(false);

  // PHASE 3 — No-Show Handling State
  const [bookingForNoShow, setBookingForNoShow] = useState<ProcurementBookingEntity | null>(null);
  const [noShowReason, setNoShowReason] = useState<string>('Farmer did not arrive during designated slot window');
  const [isSubmittingNoShow, setIsSubmittingNoShow] = useState(false);

  // PHASE 3 — Dynamic Procurement Rates State
  const [procurementRates, setProcurementRates] = useState<ProcurementRateItem[]>([]);
  const [rateSourceLabel, setRateSourceLabel] = useState<string>('Configured Rate');

  // PHASE 3 — "Now Serving" State
  const [nowServing, setNowServing] = useState<NowServingResponse | null>(null);
  const [isCallingNext, setIsCallingNext] = useState(false);

  // PHASE 4 — Active Sub-navigation Tabs
  const [activeSection, setActiveSection] = useState<'queue' | 'reports' | 'closures' | 'centres'>('queue');

  // PHASE 4 — Multi-Counter Weighbridge State
  const [selectedCounterId, setSelectedCounterId] = useState<string>('Counter-1');

  // PHASE 4 — Daily Procurement Reports State
  const [reportDate, setReportDate] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [reportCrop, setReportCrop] = useState<string>('all');
  const [reportPaymentStatus, setReportPaymentStatus] = useState<string>('all');
  const [dailyReport, setDailyReport] = useState<DailyProcurementReportResponse | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState<boolean>(false);

  // PHASE 4 — Slot Closures State
  const [closuresList, setClosuresList] = useState<SlotClosureEntity[]>([]);
  const [closureDate, setClosureDate] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [closureSlotWindow, setClosureSlotWindow] = useState<string>('08:30 AM - 11:30 AM');
  const [closureReasonInput, setClosureReasonInput] = useState<string>('Weighbridge Calibration & Yard Maintenance');
  const [isLoadingClosures, setIsLoadingClosures] = useState<boolean>(false);
  const [isClosingSlot, setIsClosingSlot] = useState<boolean>(false);

  // PHASE 4 — Procurement Centre Master Management State
  const [centresList, setCentresList] = useState<ProcurementCentreItem[]>([]);
  const [isLoadingCentresList, setIsLoadingCentresList] = useState<boolean>(false);
  const [centreStatusReasonInput, setCentreStatusReasonInput] = useState<string>('Seasonal facility renovation');
  const [isUpdatingCentreStatus, setIsUpdatingCentreStatus] = useState<boolean>(false);

  // FEATURE 5: Weighing & Digital Bill Form State
  const [activeBookingForWeighing, setActiveBookingForWeighing] = useState<ProcurementBookingEntity | null>(null);
  const [acceptedWeightKg, setAcceptedWeightKg] = useState<number>(1500.0);
  const [pricePerKg, setPricePerKg] = useState<number>(23.20);
  const [qualityDeductions, setQualityDeductions] = useState<number>(0.0);
  const [otherDeductions, setOtherDeductions] = useState<number>(0.0);
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

  // Fetch queue for staff's permitted centre
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

  // Fetch dynamic rates
  const fetchRates = async () => {
    try {
      const rates = await getProcurementRatesApi();
      setProcurementRates(rates);
    } catch (err: any) {
      console.error('Failed to load rates:', err);
    }
  };

  // Fetch Now Serving token (multi-counter aware)
  const fetchNowServing = async () => {
    const centre = overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01';
    try {
      const ns = await getNowServingApi(centre, selectedDate || undefined, selectedCounterId);
      setNowServing(ns);
      if (ns?.counters && ns.counters.length > 0 && !ns.counters.some((c) => c.counterId === selectedCounterId)) {
        setSelectedCounterId(ns.counters[0].counterId);
      }
    } catch {
      // Graceful fallback
    }
  };

  // PHASE 4: Fetch Daily Procurement Report
  const fetchDailyReport = async () => {
    if (!token) return;
    const centre = overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01';
    setIsLoadingReport(true);
    setErrorMsg(null);
    try {
      const rep = await getDailyProcurementReportApi(
        {
          centreCode: centre,
          date: reportDate || undefined,
          crop: reportCrop !== 'all' ? reportCrop : undefined,
          paymentStatus: reportPaymentStatus !== 'all' ? reportPaymentStatus : undefined,
        },
        token
      );
      setDailyReport(rep);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate daily procurement report.');
    } finally {
      setIsLoadingReport(false);
    }
  };

  // PHASE 4: Slot Closures Management
  const fetchClosures = async () => {
    if (!token) return;
    const centre = overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01';
    setIsLoadingClosures(true);
    try {
      const res = await getSlotClosuresApi(centre, closureDate || undefined, token);
      setClosuresList(res.closures || []);
    } catch (err: any) {
      console.error('Failed to load closures:', err);
    } finally {
      setIsLoadingClosures(false);
    }
  };

  const handleCloseSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    const centre = overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01';
    if (!closureReasonInput.trim()) {
      setErrorMsg('Please enter a specific reason for closing this slot.');
      return;
    }
    setIsClosingSlot(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await closeSlotApi(
        {
          centreCode: centre,
          slotDate: closureDate,
          timeWindow: closureSlotWindow,
          reason: closureReasonInput,
        },
        token
      );
      setSuccessMsg(`Slot window (${closureSlotWindow}) on ${closureDate} marked CLOSED.`);
      await fetchClosures();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to close slot window.');
    } finally {
      setIsClosingSlot(false);
    }
  };

  const handleReopenSlot = async (closure: SlotClosureEntity) => {
    if (!token) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await reopenSlotApi(
        {
          centreCode: closure.centreCode,
          slotDate: closure.slotDate,
          timeWindow: closure.timeWindow,
        },
        token
      );
      setSuccessMsg(`Slot window (${closure.timeWindow}) on ${closure.slotDate} successfully reopened.`);
      await fetchClosures();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to reopen slot window.');
    }
  };

  // PHASE 4: Centre Master Directory
  const fetchCentresList = async () => {
    setIsLoadingCentresList(true);
    try {
      const list = await getProcurementCentres();
      setCentresList(list as any);
    } catch (err: any) {
      console.error('Failed to load centres:', err);
    } finally {
      setIsLoadingCentresList(false);
    }
  };

  const handleToggleCentreStatus = async (centre: ProcurementCentreItem) => {
    if (!token) return;
    setIsUpdatingCentreStatus(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const nextStatus = !centre.isActive;
      await setProcurementCentreStatusApi(
        centre.centreCode,
        nextStatus,
        centreStatusReasonInput || (nextStatus ? 'Facility resumed normal operations' : 'Facility seasonal maintenance'),
        token
      );
      setSuccessMsg(`Centre ${centre.centreCode} status changed to ${nextStatus ? 'ACTIVE' : 'DEACTIVATED'}.`);
      await fetchCentresList();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update centre status.');
    } finally {
      setIsUpdatingCentreStatus(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    fetchStaffBills();
    fetchRates();
    fetchNowServing();
    const interval = setInterval(() => {
      fetchQueue();
      fetchStaffBills();
      fetchNowServing();
    }, 15000);
    return () => clearInterval(interval);
  }, [token, selectedDate, selectedTimeSlot, statusFilter, selectedCounterId]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchQueue();
    fetchStaffBills();
    fetchNowServing();
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

  // Open Quality Modal
  const openQualityModal = (booking: ProcurementBookingEntity) => {
    setActiveBookingForQI(booking);
    const declaredWeight = booking.acceptedWeightKg ||
      (booking.actualNetWeightQuintals ? booking.actualNetWeightQuintals * 100 : (booking.estimatedWeightQuintals ? booking.estimatedWeightQuintals * 100 : (booking.quantityBags ? booking.quantityBags * 40 : 1500)));
    setQiAcceptedWeightKg(declaredWeight);
    setQiRejectedWeightKg(0);
    setQiMoisturePercent(14.0);
    setQiQualityGrade('FAQ Grade A (Standard)');
    setQiRejectionReason('');
    setQiNotes('Standard moisture and dockage sampling.');
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  // Submit Quality Inspection
  const handleSaveQualityInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBookingForQI || !token) return;

    if (qiAcceptedWeightKg < 0 || qiRejectedWeightKg < 0) {
      setErrorMsg('Accepted and rejected quantities cannot be negative.');
      return;
    }
    if (qiAcceptedWeightKg === 0 && qiRejectedWeightKg === 0) {
      setErrorMsg('Total inspected quantity must be greater than zero.');
      return;
    }
    if (qiRejectedWeightKg > 0 && !qiRejectionReason.trim()) {
      setErrorMsg('Rejection reason is required whenever produce is rejected.');
      return;
    }

    setIsSubmittingQI(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const qualityStatus: 'ACCEPTED' | 'PARTIALLY_ACCEPTED' | 'REJECTED' =
        qiAcceptedWeightKg > 0 && qiRejectedWeightKg === 0
          ? 'ACCEPTED'
          : qiAcceptedWeightKg > 0 && qiRejectedWeightKg > 0
          ? 'PARTIALLY_ACCEPTED'
          : 'REJECTED';

      const payload: QualityInspectionPayload = {
        qualityStatus,
        acceptedWeightKg: Number(qiAcceptedWeightKg),
        rejectedWeightKg: Number(qiRejectedWeightKg),
        moisturePercent: Number(qiMoisturePercent),
        qualityGrade: qiQualityGrade,
        rejectionReason: qiRejectionReason.trim() || undefined,
        notes: qiNotes,
      };

      await staffQualityInspectionApi(activeBookingForQI.bookingId, payload, token);
      setSuccessMsg(
        `Quality inspection recorded for ${activeBookingForQI.bookingId}: ${qiAcceptedWeightKg} kg accepted, ${qiRejectedWeightKg} kg rejected.`
      );
      setActiveBookingForQI(null);
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit quality inspection.');
    } finally {
      setIsSubmittingQI(false);
    }
  };

  // Confirm No-Show
  const handleConfirmNoShow = async () => {
    if (!bookingForNoShow || !token) return;
    setIsSubmittingNoShow(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await staffNoShowApi(bookingForNoShow.bookingId, noShowReason, token);
      setSuccessMsg(`Booking ${bookingForNoShow.bookingId} marked as NO-SHOW. Capacity released and farmer notified.`);
      setBookingForNoShow(null);
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to mark as no-show.');
    } finally {
      setIsSubmittingNoShow(false);
    }
  };

  // Call Next Token (Multi-Counter FIFO)
  const handleCallNextToken = async () => {
    if (!token) return;
    const centre = overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01';
    setIsCallingNext(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await staffCallNextTokenApi(
        {
          centreCode: centre,
          date: selectedDate || undefined,
          counterId: selectedCounterId,
        },
        token
      );
      const called = res.calledToken || res.currentServing || res.currentToken;
      setSuccessMsg(
        `Called next token #${called?.tokenNumber || ''} (${called?.farmerName || ''}) to ${res.counterName || selectedCounterId}.`
      );
      await fetchNowServing();
      await fetchQueue();
    } catch (err: any) {
      setErrorMsg(err.message || 'No eligible tokens waiting in queue for this counter.');
    } finally {
      setIsCallingNext(false);
    }
  };

  // 4. Open Weighing Modal
  const openWeighingModal = (booking: ProcurementBookingEntity) => {
    // Quality check guard
    if (booking.status !== 'QUALITY_CHECKED' && !booking.qualityInspection) {
      setErrorMsg(`Booking ${booking.tokenNumber} must undergo Quality Inspection before weighing! Opening inspection.`);
      openQualityModal(booking);
      return;
    }

    setActiveBookingForWeighing(booking);
    
    // Initial kg: from qualityInspection acceptedWeightKg if present
    const initialKg = booking.qualityInspection?.acceptedWeightKg ?? (
      booking.acceptedWeightKg ||
      (booking.actualNetWeightQuintals ? booking.actualNetWeightQuintals * 100 : (booking.estimatedWeightQuintals ? booking.estimatedWeightQuintals * 100 : (booking.quantityBags ? booking.quantityBags * 40 : 1500)))
    );
    setAcceptedWeightKg(initialKg);

    // Resolve dynamic configured rate
    const matchingRate = procurementRates.find(
      (r) => r.isActive && r.crop.toLowerCase().trim() === booking.crop.toLowerCase().trim()
    );
    if (matchingRate) {
      setPricePerKg(matchingRate.ratePerKg);
      setRateSourceLabel(`${matchingRate.rateSourceLabel || matchingRate.sourceLabel} (Effective: ${matchingRate.effectiveDate})`);
    } else {
      setPricePerKg(23.20);
      setRateSourceLabel('Demo / Unconfigured Fallback Rate (₹23.20/kg)');
    }

    setQualityDeductions(0.0);
    setOtherDeductions(0.0);
    setPaymentStatus('PENDING');
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
          <p className="font-semibold text-slate-700 mb-1">Official Procurement Staff Notice:</p>
          <p>
            Please sign in using your government-assigned procurement portal credentials. Contact your district Agricultural Marketing Officer (DPC Admin) for account provisioning or password assistance.
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

      {/* PHASE 4: Sub-Navigation Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveSection('queue')}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
            activeSection === 'queue'
              ? 'bg-emerald-700 text-white shadow-sm'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Queue & Weighbridge Operations
        </button>
        <button
          onClick={() => {
            setActiveSection('reports');
            fetchDailyReport();
          }}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
            activeSection === 'reports'
              ? 'bg-emerald-700 text-white shadow-sm'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Daily Procurement Reports
        </button>
        <button
          onClick={() => {
            setActiveSection('closures');
            fetchClosures();
          }}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
            activeSection === 'closures'
              ? 'bg-emerald-700 text-white shadow-sm'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Lock className="w-4 h-4" />
          Slot Closure Management
        </button>
        <button
          onClick={() => {
            setActiveSection('centres');
            fetchCentresList();
          }}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
            activeSection === 'centres'
              ? 'bg-emerald-700 text-white shadow-sm'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Layers className="w-4 h-4" />
          Centre Master Directory
        </button>
      </div>

      {activeSection === 'queue' && (
        <>
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

          {/* PHASE 3 & 4: Multi-Counter Weighbridge Queue Caller Bar */}
          <div className="bg-gradient-to-r from-emerald-800 to-teal-900 rounded-3xl p-5 text-white shadow-lg space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center shrink-0">
                  <Megaphone className="w-6 h-6 text-amber-300" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-200 font-bold">
                      Live Intake Yard • Weighbridge Counters
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-400 text-slate-950 uppercase">
                      Now Serving
                    </span>
                  </div>
                  {nowServing?.currentToken ? (
                    <div className="mt-0.5">
                      <span className="text-xl md:text-2xl font-black font-mono tracking-tight text-white">
                        {nowServing.currentToken.tokenNumber}
                      </span>
                      <span className="text-xs text-emerald-100 font-medium ml-2">
                        — {nowServing.currentToken.farmerName} ({nowServing.currentToken.crop}) • {nowServing.counterName || selectedCounterId}
                      </span>
                    </div>
                  ) : (
                    <p className="text-sm font-semibold text-emerald-100 mt-0.5">
                      {selectedCounterId} Idle — Click "Call Next Token" to admit next arrival
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                {nowServing?.nextEligibleToken && (
                  <div className="text-right hidden sm:block">
                    <span className="text-[10px] text-emerald-200 uppercase font-bold block">Next in FIFO Queue</span>
                    <span className="text-xs font-mono font-bold text-white">
                      {nowServing.nextEligibleToken.tokenNumber} ({nowServing.nextEligibleToken.farmerName})
                    </span>
                  </div>
                )}
                <button
                  onClick={handleCallNextToken}
                  disabled={isCallingNext}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-300 disabled:bg-slate-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-all"
                >
                  {isCallingNext ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Calling next...</span>
                    </>
                  ) : (
                    <>
                      <Megaphone className="w-4 h-4" />
                      <span>Call Next to {selectedCounterId}</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Counter Selection Pills */}
            <div className="pt-2 border-t border-white/10 flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold text-emerald-200 uppercase tracking-wider mr-1">
                Active Weighbridge Counter:
              </span>
              {(nowServing?.counters && nowServing.counters.length > 0
                ? nowServing.counters
                : [
                    { counterId: 'Counter-1', name: 'Weighbridge Counter #1', isActive: true, isNowServing: false },
                    { counterId: 'Counter-2', name: 'Weighbridge Counter #2', isActive: true, isNowServing: false },
                  ]
              ).map((c) => {
                const isSelected = selectedCounterId === c.counterId;
                return (
                  <button
                    key={c.counterId}
                    type="button"
                    onClick={() => setSelectedCounterId(c.counterId)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                      isSelected
                        ? 'bg-white text-emerald-950 shadow-md ring-2 ring-white/50'
                        : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>{c.name}</span>
                    {c.currentToken ? (
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold ${isSelected ? 'bg-amber-400 text-slate-950' : 'bg-emerald-700 text-white'}`}>
                        #{c.currentToken}
                      </span>
                    ) : (
                      <span className="text-[9px] opacity-75">(Idle)</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

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
                  const isCheckedIn = ['CHECKED_IN', 'IN_QUEUE', 'PROCESSING', 'QUALITY_CHECKED', 'quality_checked'].includes(item.status);
                  const isBooked = item.status === 'BOOKED' || item.status === 'confirmed';
                  const isQualityChecked = item.status === 'QUALITY_CHECKED' || !!item.qualityInspection;
                  const isRejected = item.status === 'REJECTED';
                  const isNoShow = item.status === 'NO_SHOW';

                  return (
                    <tr key={item.bookingId || item.id} className="hover:bg-slate-50/60">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono font-bold text-emerald-800">
                            {item.tokenNumber}
                          </span>
                          {item.isNowServing && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500 text-white animate-pulse">
                              Serving
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono block">
                          {item.bookingId}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span className="font-semibold text-slate-800 block">
                          {item.farmerName}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono block">
                          {item.farmerId} • {item.slotDate}
                        </span>
                        {item.harvestDate && (
                          <span className="text-[10px] text-emerald-800 font-medium block">
                            🌾 Harvest: {item.harvestDate}
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <span className="font-medium text-slate-800 block">{item.crop}</span>
                        {item.cropVariety && (
                          <span className="text-[10px] text-emerald-700 font-semibold block">
                            Var: {item.cropVariety}
                          </span>
                        )}
                        <span className="text-slate-500 text-[11px] block">
                          {item.quantityBags} Bags (~{item.estimatedWeightQuintals} Qtl)
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isCompleted
                              ? 'bg-emerald-100 text-emerald-800'
                              : item.status === 'QUALITY_CHECKED'
                              ? 'bg-teal-100 text-teal-800'
                              : isCheckedIn
                              ? 'bg-blue-100 text-blue-800'
                              : item.status === 'CANCELLED' || isRejected || isNoShow
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {item.status}
                        </span>
                        {item.qualityInspection && (
                          <div className="text-[10px] mt-1 space-y-0.5 font-medium">
                            <span className={(item.qualityInspection.status || item.qualityInspection.qualityStatus) === 'REJECTED' ? 'text-rose-600' : 'text-teal-700'}>
                              Quality: {item.qualityInspection.status || item.qualityInspection.qualityStatus}
                            </span>
                            {item.qualityInspection.acceptedWeightKg !== undefined && (
                              <span className="text-slate-500 block text-[9px]">
                                Acc: {item.qualityInspection.acceptedWeightKg} kg | Rej: {item.qualityInspection.rejectedWeightKg} kg
                              </span>
                            )}
                          </div>
                        )}
                        {item.noShowDetails && (
                          <div className="text-[9px] text-slate-500 italic mt-0.5">
                            Marked No-Show by {item.noShowDetails.markedByStaffName || item.noShowDetails.markedByStaff || 'Staff'}
                          </div>
                        )}
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
                            <>
                              <button
                                onClick={() => handleCheckIn(item.bookingId)}
                                className="px-2 py-1 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-bold shadow-sm"
                              >
                                Check In
                              </button>
                              <button
                                onClick={() => setBookingForNoShow(item)}
                                className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-bold"
                              >
                                No-Show
                              </button>
                            </>
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

                          {/* QUALITY INSPECTION (for checked in / queue / processing without inspection) */}
                          {isCheckedIn && !isCompleted && !isRejected && (
                            <button
                              onClick={() => openQualityModal(item)}
                              className={`px-2 py-1 rounded-lg text-white text-[10px] font-bold shadow-sm flex items-center gap-1 ${
                                isQualityChecked
                                  ? 'bg-teal-700 hover:bg-teal-800'
                                  : 'bg-amber-600 hover:bg-amber-700'
                              }`}
                            >
                              <ClipboardCheck className="w-3 h-3" />
                              {isQualityChecked ? 'Re-Inspect' : 'Inspect Quality'}
                            </button>
                          )}

                          {/* Weigh & Generate Bill (for any non-completed, non-cancelled, non-rejected) */}
                          {!isCompleted && !['CANCELLED', 'NO_SHOW', 'REJECTED'].includes(item.status) && (
                            <button
                              onClick={() => openWeighingModal(item)}
                              className={`px-2.5 py-1 rounded-lg text-white text-[10px] font-bold shadow-sm flex items-center gap-1 ${
                                isQualityChecked
                                  ? 'bg-emerald-700 hover:bg-emerald-800'
                                  : 'bg-slate-500 hover:bg-slate-600'
                              }`}
                              title={isQualityChecked ? 'Record Weighing & Issue Bill' : 'Quality Inspection Required First'}
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
        </>
      )}

      {/* PHASE 4: DAILY PROCUREMENT REPORTS SECTION */}
      {activeSection === 'reports' && (
        <div className="space-y-6">
          {/* Report Filters */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-emerald-700" />
                  Daily Procurement & Financial Audit Reports
                </h3>
                <p className="text-xs text-slate-500">
                  Accurate centre-level accounting derived from persisted mandi gate weighing and digital bills.
                </p>
              </div>
              <button
                onClick={fetchDailyReport}
                disabled={isLoadingReport}
                className="px-4 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shrink-0 shadow-sm disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingReport ? 'animate-spin' : ''}`} />
                {isLoadingReport ? 'Calculating Report...' : 'Generate Report'}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Procurement Date
                </label>
                <input
                  type="date"
                  value={reportDate}
                  onChange={(e) => setReportDate(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Crop Filter
                </label>
                <select
                  value={reportCrop}
                  onChange={(e) => setReportCrop(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="all">All Crops</option>
                  <option value="Paddy (Common)">Paddy (Common)</option>
                  <option value="Paddy (Grade A)">Paddy (Grade A)</option>
                  <option value="Maize">Maize</option>
                  <option value="Ragi">Ragi</option>
                  <option value="Black Gram">Black Gram</option>
                  <option value="Green Gram">Green Gram</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Payment Settlement Status
                </label>
                <select
                  value={reportPaymentStatus}
                  onChange={(e) => setReportPaymentStatus(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="all">All Payment States</option>
                  <option value="PENDING">Pending Approval</option>
                  <option value="PROCESSING">Bank Processing (Treasury)</option>
                  <option value="PAID">Paid / Disbursed (DBT)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Report Loading State */}
          {isLoadingReport && (
            <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-sm text-center">
              <Loader2 className="w-8 h-8 text-emerald-700 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Compiling official audit figures from MongoDB...</p>
              <p className="text-xs text-slate-400">Aggregating weighbridge entries, deductions and disbursement records.</p>
            </div>
          )}

          {/* Report Results */}
          {!isLoadingReport && dailyReport && (
            <div className="space-y-6">
              {/* Centre Banner Summary */}
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-200 text-emerald-900 flex items-center justify-center font-bold">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-black text-emerald-950">
                      {dailyReport.centreName} ({dailyReport.centreCode})
                    </h4>
                    <p className="text-xs text-emerald-800">
                      Procurement Date: <strong className="font-mono">{dailyReport.reportDate}</strong> • Generated on {new Date(dailyReport.generatedAt).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-white text-emerald-800 border border-emerald-200">
                    Official Government Audit Report
                  </span>
                </div>
              </div>

              {/* 8-Card Key Metrics Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Bookings Handled
                  </div>
                  <div className="text-2xl font-black text-slate-900">
                    {dailyReport.totalBookings}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-2">
                    <span className="text-emerald-700 font-semibold">{dailyReport.completedTransactions} Weighed</span>
                    <span>•</span>
                    <span className="text-rose-600">{dailyReport.cancelledAndNoShowBookings} Void/No-show</span>
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Accepted Procurement
                  </div>
                  <div className="text-2xl font-black text-emerald-800">
                    {(dailyReport.totalAcceptedWeightQuintals).toFixed(2)} <span className="text-xs font-semibold text-emerald-600">Qtl</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    {dailyReport.totalAcceptedWeightKg.toLocaleString()} kg net accepted
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Total Gross Value
                  </div>
                  <div className="text-2xl font-black text-slate-900">
                    ₹{(dailyReport.totalGrossTransactionValue || dailyReport.totalGrossAmount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    At official MSP & mandi procurement rates
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Net Farmer Payable
                  </div>
                  <div className="text-2xl font-black text-teal-800">
                    ₹{(dailyReport.totalNetPayable || dailyReport.totalNetAmount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    Deductions: ₹{(dailyReport.totalDeductions || dailyReport.totalDeductionsAmount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-1">
                    Paid / Disbursed (DBT)
                  </div>
                  <div className="text-xl font-black text-emerald-700">
                    ₹{dailyReport.amountPaid.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Directly transferred to bank accounts
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-blue-600 uppercase tracking-wider mb-1">
                    In Bank Processing
                  </div>
                  <div className="text-xl font-black text-blue-700">
                    ₹{dailyReport.amountProcessing.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Treasury clearing in progress
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-amber-600 uppercase tracking-wider mb-1">
                    Pending Approval
                  </div>
                  <div className="text-xl font-black text-amber-700">
                    ₹{dailyReport.amountPending.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Awaiting final weighment sign-off
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-bold text-rose-500 uppercase tracking-wider mb-1">
                    Rejected Quantity
                  </div>
                  <div className="text-xl font-black text-rose-600">
                    {dailyReport.totalRejectedWeightKg} <span className="text-xs font-semibold text-rose-400">kg</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Failed moisture / FAQ quality checks
                  </div>
                </div>
              </div>

              {/* Crop-Wise Breakdown Table */}
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-emerald-700" />
                    Crop-Wise Quantity & Financial Distribution
                  </h4>
                  <span className="text-xs text-slate-500">
                    {dailyReport.cropBreakdown.length} crop categories
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                      <tr>
                        <th className="p-3 pl-4">Crop Name</th>
                        <th className="p-3">Bookings</th>
                        <th className="p-3">Accepted (Kg)</th>
                        <th className="p-3">Accepted (Qtl)</th>
                        <th className="p-3">Rejected (Kg)</th>
                        <th className="p-3">Gross Value</th>
                        <th className="p-3">Net Payable</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {dailyReport.cropBreakdown.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="p-6 text-center text-slate-400">
                            No crop transactions recorded matching the selected filter.
                          </td>
                        </tr>
                      ) : (
                        dailyReport.cropBreakdown.map((cr, idx) => (
                          <tr key={idx} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3 pl-4 font-bold text-slate-900">{cr.crop}</td>
                            <td className="p-3">{cr.totalBookings}</td>
                            <td className="p-3 font-mono font-semibold text-emerald-800">
                              {cr.acceptedWeightKg.toLocaleString()} kg
                            </td>
                            <td className="p-3 font-mono font-semibold text-slate-700">
                              {cr.acceptedWeightQuintals.toFixed(2)} Qtl
                            </td>
                            <td className="p-3 font-mono text-rose-600">
                              {cr.rejectedWeightKg} kg
                            </td>
                            <td className="p-3 font-mono">
                              ₹{(cr.grossValue || cr.grossAmount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </td>
                            <td className="p-3 font-mono font-bold text-teal-800">
                              ₹{(cr.netPayable || cr.netAmount || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Counter Throughput Summary */}
              {dailyReport.counterThroughput && dailyReport.counterThroughput.length > 0 && (
                <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Scale className="w-4 h-4 text-emerald-700" />
                    Weighbridge Counter Operational Throughput
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {dailyReport.counterThroughput.map((ct) => (
                      <div key={ct.counterId} className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-xs text-slate-900">{ct.counterName}</span>
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800">
                            {ct.counterId}
                          </span>
                        </div>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between text-slate-600">
                            <span>Completed Weighings:</span>
                            <strong className="text-slate-900">{ct.completedBookings}</strong>
                          </div>
                          <div className="flex justify-between text-slate-600">
                            <span>Total Net Weight:</span>
                            <strong className="text-emerald-800 font-mono">{ct.totalWeightKg.toLocaleString()} kg</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!isLoadingReport && !dailyReport && (
            <div className="bg-white rounded-3xl p-12 border border-slate-200 text-center">
              <BarChart3 className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">No report generated yet</p>
              <p className="text-xs text-slate-400">Click &quot;Generate Report&quot; to compile official procurement records for this centre.</p>
            </div>
          )}
        </div>
      )}

      {/* PHASE 4: SLOT CLOSURE MANAGEMENT SECTION */}
      {activeSection === 'closures' && (
        <div className="space-y-6">
          {/* Slot Closure Control Card */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-rose-600" />
                  Direct Purchase Centre Slot Closure Controls
                </h3>
                <p className="text-xs text-slate-500">
                  Halt booking acceptance for specific dates and time windows due to weighbridge calibration, maintenance, or yard congestion.
                </p>
              </div>
              <button
                onClick={fetchClosures}
                disabled={isLoadingClosures}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center gap-2 transition-all shrink-0"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingClosures ? 'animate-spin' : ''}`} />
                Refresh Closures
              </button>
            </div>

            <form onSubmit={handleCloseSlot} className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 items-end">
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Target Slot Date
                </label>
                <input
                  type="date"
                  value={closureDate}
                  onChange={(e) => setClosureDate(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Time Window
                </label>
                <select
                  value={closureSlotWindow}
                  onChange={(e) => setClosureSlotWindow(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="08:30 AM - 11:30 AM">08:30 AM - 11:30 AM (Morning)</option>
                  <option value="11:30 AM - 02:30 PM">11:30 AM - 02:30 PM (Midday)</option>
                  <option value="02:30 PM - 05:30 PM">02:30 PM - 05:30 PM (Afternoon)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Closure Justification
                </label>
                <input
                  type="text"
                  placeholder="e.g. Weighbridge load-cell recalibration"
                  value={closureReasonInput}
                  onChange={(e) => setClosureReasonInput(e.target.value)}
                  className="w-full text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isClosingSlot}
                  className="w-full py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-sm disabled:opacity-50"
                >
                  {isClosingSlot ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Lock className="w-4 h-4" />
                  )}
                  {isClosingSlot ? 'Closing...' : 'Mark Slot CLOSED'}
                </button>
              </div>
            </form>
          </div>

          {/* Active Closures Table */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-700" />
                Active Slot Closures for Centre {overviewData?.centreCode || user?.centreCode || 'TNJ-DPC-01'}
              </h4>
              <span className="text-xs text-slate-500">
                {closuresList.length} closures recorded
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="p-3 pl-4">Date</th>
                    <th className="p-3">Time Window</th>
                    <th className="p-3">Reason / Justification</th>
                    <th className="p-3">Closed By</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right pr-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {isLoadingClosures ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-400">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-400" />
                        Loading slot closure records...
                      </td>
                    </tr>
                  ) : closuresList.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-400">
                        No active slot closures recorded for this centre. All regular slots are open for farmer booking.
                      </td>
                    </tr>
                  ) : (
                    closuresList.map((cl, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 transition-colors">
                        <td className="p-3 pl-4 font-mono font-bold text-slate-900">{cl.slotDate}</td>
                        <td className="p-3 font-semibold text-slate-800">{cl.timeWindow}</td>
                        <td className="p-3 text-slate-600 max-w-xs">{cl.reason}</td>
                        <td className="p-3 font-mono text-[11px] text-slate-500">{cl.closedBy}</td>
                        <td className="p-3">
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 flex items-center gap-1 w-fit">
                            <Lock className="w-3 h-3" />
                            CLOSED
                          </span>
                        </td>
                        <td className="p-3 text-right pr-4">
                          <button
                            onClick={() => handleReopenSlot(cl)}
                            className="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold text-xs flex items-center gap-1.5 ml-auto border border-emerald-200 transition-all"
                          >
                            <Unlock className="w-3.5 h-3.5" />
                            Reopen Slot
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* PHASE 4: CENTRE MASTER DIRECTORY SECTION */}
      {activeSection === 'centres' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-emerald-700" />
                Procurement Centre Master Network
              </h3>
              <p className="text-xs text-slate-500">
                Official Direct Purchase Centres (DPCs) and Regulated Market Committees across Tamil Nadu.
              </p>
            </div>
            <button
              onClick={fetchCentresList}
              disabled={isLoadingCentresList}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center gap-2 transition-all shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingCentresList ? 'animate-spin' : ''}`} />
              Refresh Directory
            </button>
          </div>

          {/* Status Change Reason Input */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center gap-3">
            <label className="text-xs font-bold text-slate-700 shrink-0">
              Centre Deactivation / Reactivation Reason:
            </label>
            <input
              type="text"
              value={centreStatusReasonInput}
              onChange={(e) => setCentreStatusReasonInput(e.target.value)}
              placeholder="e.g. Seasonal facility maintenance, weighing sensor upgrade"
              className="w-full text-xs p-2.5 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Centres Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoadingCentresList ? (
              <div className="col-span-2 bg-white rounded-3xl p-12 text-center border border-slate-200">
                <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-700 mb-2" />
                <p className="text-xs text-slate-500">Loading procurement centre directory...</p>
              </div>
            ) : centresList.length === 0 ? (
              <div className="col-span-2 bg-white rounded-3xl p-12 text-center border border-slate-200">
                <Building2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs text-slate-500">No centres found in directory. Click refresh to load.</p>
              </div>
            ) : (
              centresList.map((c) => (
                <div
                  key={c.centreCode}
                  className={`bg-white rounded-3xl p-5 border transition-all shadow-sm ${
                    c.isActive ? 'border-slate-200' : 'border-rose-200 bg-rose-50/20'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                          {c.centreCode}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            c.isActive
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {c.isActive ? 'ACTIVE' : 'DEACTIVATED'}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-900 mt-1">{c.name}</h4>
                      <p className="text-xs text-slate-500">{c.district} District • {c.address}</p>
                    </div>

                    <button
                      onClick={() => handleToggleCentreStatus(c)}
                      disabled={isUpdatingCentreStatus}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shrink-0 ${
                        c.isActive
                          ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200'
                          : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      <Power className="w-3.5 h-3.5" />
                      {c.isActive ? 'Deactivate' : 'Reactivate'}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 p-3 rounded-2xl bg-slate-50 text-xs mb-3">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Daily Yard Capacity</span>
                      <span className="font-semibold text-slate-800">{c.dailyCapacityBags} Bags / Day</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Operating Hours</span>
                      <span className="font-semibold text-slate-800">{c.operatingHours || '08:30 AM - 05:30 PM'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Active Counters</span>
                      <span className="font-semibold text-emerald-800">
                        {c.counters ? c.counters.length : 1} Weighbridge Counter(s)
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Slot Granularity</span>
                      <span className="font-semibold text-slate-800">3 Windows / Day</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Supported Crops</span>
                    <div className="flex flex-wrap gap-1">
                      {c.supportedCrops && c.supportedCrops.map((crp, ci) => (
                        <span key={ci} className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-medium">
                          {crp}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
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
                    = ₹{(pricePerKg * 100).toFixed(2)} / Quintal • Source: <strong className="text-emerald-800">{rateSourceLabel}</strong>
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

      {/* PHASE 3: QUALITY INSPECTION MODAL */}
      {activeBookingForQI && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 my-8 space-y-4">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-teal-100 text-teal-800 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">
                    Mandatory Quality Inspection
                  </h3>
                  <p className="text-xs text-slate-500">
                    Moisture dockage, grade analysis & produce acceptance gate
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveBookingForQI(null)}
                className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            {/* Booking Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 p-3 rounded-2xl bg-teal-50/70 border border-teal-200 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Token</span>
                <span className="font-mono font-bold text-teal-900">{activeBookingForQI.tokenNumber}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Farmer</span>
                <span className="font-semibold text-slate-800">{activeBookingForQI.farmerName}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Crop & Var</span>
                <span className="font-semibold text-slate-800">
                  {activeBookingForQI.crop} {activeBookingForQI.cropVariety ? `(${activeBookingForQI.cropVariety})` : ''}
                </span>
              </div>
            </div>

            <form onSubmit={handleSaveQualityInspection} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                    required
                    value={qiMoisturePercent}
                    onChange={(e) => setQiMoisturePercent(parseFloat(e.target.value) || 0)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 font-bold font-mono text-slate-900"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Standard FAQ tolerance: max 17.0%
                  </span>
                </div>

                {/* Quality Grade */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Inspected Quality Standard *
                  </label>
                  <select
                    value={qiQualityGrade}
                    onChange={(e) => setQiQualityGrade(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 font-semibold text-slate-900"
                  >
                    <option value="FAQ Grade A (Standard)">FAQ Grade A (Standard)</option>
                    <option value="Common Paddy Standard">Common Paddy Standard</option>
                    <option value="Super Fine Variety">Super Fine Variety</option>
                    <option value="Below FAQ (Sub-standard)">Below FAQ (Sub-standard)</option>
                  </select>
                </div>

                {/* Accepted Weight */}
                <div>
                  <label className="font-bold text-emerald-800 block mb-1">
                    Accepted Quantity (kg) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={qiAcceptedWeightKg}
                    onChange={(e) => setQiAcceptedWeightKg(Math.max(0, parseFloat(e.target.value) || 0))}
                    className="w-full p-2.5 rounded-xl border border-emerald-300 font-bold font-mono text-slate-900 bg-emerald-50/30"
                  />
                  <span className="text-[10px] text-emerald-700 mt-0.5 block">
                    = {(qiAcceptedWeightKg / 100).toFixed(2)} Quintals eligible for weighing
                  </span>
                </div>

                {/* Rejected Weight */}
                <div>
                  <label className="font-bold text-rose-800 block mb-1">
                    Rejected Quantity (kg)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={qiRejectedWeightKg}
                    onChange={(e) => setQiRejectedWeightKg(Math.max(0, parseFloat(e.target.value) || 0))}
                    className="w-full p-2.5 rounded-xl border border-rose-300 font-bold font-mono text-slate-900 bg-rose-50/30"
                  />
                  <span className="text-[10px] text-rose-600 mt-0.5 block">
                    Disqualified due to high moisture or foreign dockage
                  </span>
                </div>
              </div>

              {/* Rejection Reason (Mandatory if rejected > 0) */}
              {qiRejectedWeightKg > 0 && (
                <div>
                  <label className="font-bold text-rose-800 block mb-1">
                    Specific Rejection Reason * (Required by TN Govt Procurement Rules)
                  </label>
                  <input
                    type="text"
                    required
                    value={qiRejectionReason}
                    onChange={(e) => setQiRejectionReason(e.target.value)}
                    placeholder="e.g. Moisture exceeds 21%, excessive foreign seeds and dockage"
                    className="w-full p-2.5 rounded-xl border border-rose-300 bg-rose-50/50 text-slate-900 font-medium"
                  />
                </div>
              )}

              {/* Inspector Notes */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  Quality Inspector Notes
                </label>
                <input
                  type="text"
                  value={qiNotes}
                  onChange={(e) => setQiNotes(e.target.value)}
                  placeholder="e.g. Moisture sampled from 5 random bags, visual dockage normal"
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-slate-800"
                />
              </div>

              {/* Outcome Badge Preview */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <span className="text-slate-600 font-medium">Outcome Preview:</span>
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase ${
                    qiAcceptedWeightKg > 0 && qiRejectedWeightKg === 0
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : qiAcceptedWeightKg > 0 && qiRejectedWeightKg > 0
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : 'bg-rose-100 text-rose-800 border border-rose-300'
                  }`}
                >
                  {qiAcceptedWeightKg > 0 && qiRejectedWeightKg === 0
                    ? 'FULL ACCEPTANCE'
                    : qiAcceptedWeightKg > 0 && qiRejectedWeightKg > 0
                    ? 'PARTIAL ACCEPTANCE'
                    : 'FULL REJECTION'}
                </span>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  disabled={isSubmittingQI}
                  onClick={() => setActiveBookingForQI(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingQI}
                  className="px-6 py-2 rounded-xl bg-teal-700 hover:bg-teal-800 disabled:bg-slate-300 text-white font-bold flex items-center gap-1.5 shadow-md shadow-teal-700/20"
                >
                  {isSubmittingQI ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving Inspection...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Save Quality Record</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PHASE 3: NO-SHOW CONFIRMATION MODAL */}
      {bookingForNoShow && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scale-up">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
                <UserX className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Mark as NO-SHOW?
                </h3>
                <p className="text-xs text-slate-500 font-mono">Booking ID: {bookingForNoShow.bookingId}</p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Token Number:</span>
                <span className="font-mono font-bold text-emerald-800">{bookingForNoShow.tokenNumber}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Farmer:</span>
                <span className="font-semibold text-slate-800">{bookingForNoShow.farmerName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Slot Window:</span>
                <span className="font-semibold text-slate-800">{bookingForNoShow.slotDate} ({bookingForNoShow.timeWindow})</span>
              </div>
            </div>

            <div>
              <label className="font-bold text-slate-700 block text-xs mb-1">
                Reason for marking No-Show:
              </label>
              <input
                type="text"
                value={noShowReason}
                onChange={(e) => setNoShowReason(e.target.value)}
                placeholder="e.g. Farmer did not arrive during designated time window"
                className="w-full text-xs p-2.5 rounded-xl border border-slate-300"
              />
            </div>

            <p className="text-xs text-slate-600">
              Marking this booking as NO-SHOW will release the reserved capacity back to other farmers and notify the farmer in-app.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                disabled={isSubmittingNoShow}
                onClick={() => setBookingForNoShow(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingNoShow}
                onClick={handleConfirmNoShow}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-md shadow-amber-600/20 flex items-center gap-1.5"
              >
                {isSubmittingNoShow ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>Confirm No-Show</span>
                )}
              </button>
            </div>
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

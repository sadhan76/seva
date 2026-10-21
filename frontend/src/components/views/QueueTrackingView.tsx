import React, { useState, useEffect } from 'react';
import {
  ListOrdered,
  Clock,
  Scale,
  RefreshCw,
  Search,
  AlertCircle,
  Loader2,
  Info,
  Check,
  Megaphone,
  ClipboardCheck,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getQueueTracking,
  getProcurementBookings,
  getNowServingApi,
  type QueueTrackingResponse,
  type ProcurementBookingEntity,
  type NowServingResponse,
} from '../../services/api';

interface QueueTrackingViewProps {
  initialBookingId?: string | null;
}

export const QueueTrackingView: React.FC<QueueTrackingViewProps> = ({ initialBookingId }) => {
  const { t, language } = useLanguage();
  const { token } = useAuth();

  const [bookingIdInput, setBookingIdInput] = useState<string>(initialBookingId || '');
  const [activeBookings, setActiveBookings] = useState<ProcurementBookingEntity[]>([]);
  const [selectedBookingId, setSelectedBookingId] = useState<string>(initialBookingId || '');
  const [queueData, setQueueData] = useState<QueueTrackingResponse | null>(null);
  const [nowServing, setNowServing] = useState<NowServingResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [autoPoll, setAutoPoll] = useState<boolean>(true);

  // 1. Load user's bookings to populate quick selector
  useEffect(() => {
    const fetchMyBookings = async () => {
      try {
        const records = await getProcurementBookings(token);
        setActiveBookings(records);
        if (!selectedBookingId && records.length > 0) {
          setSelectedBookingId(records[0].bookingId);
          setBookingIdInput(records[0].bookingId);
        }
      } catch {
        // Fallback gracefully
      }
    };
    fetchMyBookings();
  }, [token]);

  // Update selected booking if initialBookingId prop changes
  useEffect(() => {
    if (initialBookingId) {
      setSelectedBookingId(initialBookingId);
      setBookingIdInput(initialBookingId);
    }
  }, [initialBookingId]);

  // 2. Fetch live queue tracking data from backend
  const fetchQueueInfo = async (idToFetch: string, isManual = false) => {
    if (!idToFetch) return;
    if (isManual) setIsLoading(true);
    setErrorMsg(null);

    try {
      const data = await getQueueTracking(idToFetch, token || undefined);
      setQueueData(data);
      if (data.centreCode) {
        try {
          const ns = await getNowServingApi(data.centreCode);
          setNowServing(ns);
        } catch {
          // Graceful fallback
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch queue information for this booking.');
      setQueueData(null);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Trigger fetch when selected booking changes
  useEffect(() => {
    if (selectedBookingId) {
      fetchQueueInfo(selectedBookingId, true);
    }
  }, [selectedBookingId]);

  // Auto-polling interval every 15 seconds
  useEffect(() => {
    if (!autoPoll || !selectedBookingId) return;

    const interval = setInterval(() => {
      fetchQueueInfo(selectedBookingId, false);
    }, 15000);

    return () => clearInterval(interval);
  }, [autoPoll, selectedBookingId]);

  const handleManualSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (bookingIdInput.trim()) {
      setSelectedBookingId(bookingIdInput.trim());
      fetchQueueInfo(bookingIdInput.trim(), true);
    }
  };

  const handleRefresh = () => {
    if (selectedBookingId) {
      setIsRefreshing(true);
      fetchQueueInfo(selectedBookingId, false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Booking Selector & Search Bar */}
      <Card
        title={t.nav.queue}
        subtitle="Live Procurement Yard Queue & DBT Ledger Tracking"
        icon={<ListOrdered className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <Badge variant={queueData ? 'emerald' : 'slate'} dot>
            Backend Polling ({autoPoll ? 'Active 15s' : 'Paused'})
          </Badge>
        }
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            {language === 'ta'
              ? 'உங்கள் முன்பதிவு எண் அல்லது டோக்கனைத் தேர்ந்தெடுத்து, நேரடி யார்டு வரிசை நிலை, நுழைவு வாயில் சரிபார்ப்பு மற்றும் எடைப் பதிவுகளை கண்காணிக்கவும்.'
              : 'Select your booking or enter your token number to monitor your live truck queue position, electronic weighbridge slip, and DBT bank ledger.'}
          </p>

          <form onSubmit={handleManualSearch} className="flex flex-col sm:flex-row gap-2">
            {activeBookings.length > 0 && (
              <select
                value={selectedBookingId}
                onChange={(e) => {
                  setSelectedBookingId(e.target.value);
                  setBookingIdInput(e.target.value);
                }}
                className="text-xs p-3 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-semibold"
              >
                {activeBookings.map((b) => (
                  <option key={b.bookingId} value={b.bookingId}>
                    {b.tokenNumber} — {b.mandiName} ({b.slotDate})
                  </option>
                ))}
              </select>
            )}

            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Enter Booking ID (e.g. PROC-TNJ-2026-...) or Token Number"
                value={bookingIdInput}
                onChange={(e) => setBookingIdInput(e.target.value)}
                className="w-full text-xs p-3 pl-10 bg-white rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            </div>

            <button
              type="submit"
              disabled={isLoading || !bookingIdInput.trim()}
              className="px-6 py-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-sm"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Search</span>}
            </button>
          </form>
        </div>
      </Card>

      {/* Error state */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm font-medium flex-1">
            <strong>Queue Tracking Notice:</strong> {errorMsg}
          </div>
        </div>
      )}

      {/* Main Queue Progress Card */}
      {isLoading ? (
        <div className="py-16 text-center text-xs text-slate-500 flex flex-col items-center justify-center gap-3 bg-white rounded-3xl border border-slate-200">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
          <p className="font-semibold text-slate-700">Connecting to Mandi Yard Backend...</p>
        </div>
      ) : queueData ? (
        <>
          {/* PHASE 3: Live "Now Serving" Alert for this Farmer */}
          {queueData.isNowServing && (
            <div className="p-4 rounded-3xl bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg animate-pulse flex items-center justify-between gap-3">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center shrink-0">
                  <Megaphone className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h4 className="font-extrabold text-sm uppercase tracking-wide">
                    🎉 Your Token Is Now Being Served!
                  </h4>
                  <p className="text-xs text-amber-100 font-medium">
                    Please drive your vehicle directly onto {queueData.counterName || queueData.counterId || nowServing?.counterName || 'Weighbridge Counter #1'}.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 bg-white text-slate-900 font-black text-xs rounded-xl shrink-0 shadow-sm">
                {queueData.counterName || queueData.counterId || nowServing?.counterName || 'Counter-1'} Calling
              </span>
            </div>
          )}

          {/* Multi-Counter & Now Serving Notice */}
          {nowServing?.counters && nowServing.counters.length > 1 ? (
            <div className="p-3.5 rounded-2xl bg-slate-900 text-white space-y-2 text-xs shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping shrink-0" />
                  Active Weighbridge Counters ({nowServing.counters.length})
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Multi-Weighbridge Live Status</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {nowServing.counters.map((c) => (
                  <div key={c.counterId} className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between">
                    <div>
                      <span className="text-slate-400 text-[10px] font-bold block">{c.name}</span>
                      {c.currentToken ? (
                        <span className="font-mono font-bold text-amber-300 text-xs">
                          Serving #{c.currentToken} {c.farmerName ? `(${c.farmerName})` : ''}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-xs italic">Idle / Waiting</span>
                      )}
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${c.isNowServing ? 'bg-amber-400 text-slate-950' : 'bg-slate-700 text-slate-300'}`}>
                      {c.isNowServing ? 'Active' : 'Idle'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : nowServing?.currentToken && !queueData.isNowServing && (
            <div className="p-3.5 rounded-2xl bg-slate-900 text-white flex items-center justify-between text-xs shadow-sm">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping shrink-0" />
                <span className="text-slate-400 font-bold uppercase text-[10px]">Now Serving at {nowServing.counterName || 'Counter-1'}:</span>
                <span className="font-mono font-black text-amber-300 text-sm">#{nowServing.currentToken.tokenNumber}</span>
                <span className="text-slate-300 hidden sm:inline">({nowServing.currentToken.farmerName})</span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Single Weighbridge Queue</span>
            </div>
          )}

          <Card
            title={`Token #${queueData.tokenNumber}`}
            subtitle={`${queueData.mandiName} • ${queueData.slotDate} (${queueData.timeWindow})${
              queueData.cropVariety ? ` • Var: ${queueData.cropVariety}` : ''
            }${queueData.harvestDate ? ` • Harvest: ${queueData.harvestDate}` : ''}`}
            icon={<Clock className="w-5 h-5 text-emerald-700" />}
            headerAction={
              <Badge
                variant={
                  queueData.status === 'COMPLETED'
                    ? 'emerald'
                    : queueData.status === 'QUALITY_CHECKED'
                    ? 'emerald'
                    : queueData.status === 'CHECKED_IN' || queueData.status === 'IN_QUEUE' || queueData.status === 'PROCESSING'
                    ? 'blue'
                    : queueData.status === 'CANCELLED' || queueData.status === 'REJECTED' || queueData.status === 'NO_SHOW'
                    ? 'rose'
                    : 'amber'
                }
                dot
              >
                {queueData.status}
              </Badge>
            }
          footer={
            <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
              <span className="font-mono text-[11px]">
                Last backend poll: {queueData.lastPolledAt} (Real MongoDB check)
              </span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setAutoPoll(!autoPoll)}
                  className="text-xs text-slate-500 hover:text-slate-800"
                >
                  {autoPoll ? 'Pause Auto-Poll' : 'Resume Auto-Poll'}
                </button>
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="flex items-center gap-1 font-bold text-emerald-700 hover:text-emerald-800"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                  Refresh Queue
                </button>
              </div>
            </div>
          }
        >
          <div className="space-y-6">
            {/* FEATURE 4: 3-BOX COUNTERS */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
              {/* Centre Status */}
              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  {language === 'ta' ? 'கொள்முதல் நிலை' : 'Procurement State'}
                </span>
                <span className="text-xl font-extrabold text-slate-800 mt-1 block">
                  {queueData.status}
                </span>
                <span className="text-xs text-slate-500 mt-0.5 block">
                  {queueData.crop} • {queueData.quantityBags} Bags
                </span>
              </div>

              {/* Queue Position */}
              <div className="rounded-2xl bg-emerald-50/80 p-4 border border-emerald-200">
                <span className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider block">
                  {language === 'ta' ? 'யார்டு வரிசை எண்' : 'Yard Queue Position'}
                </span>
                <span className="text-2xl font-mono font-extrabold text-emerald-800 mt-1 block">
                  {queueData.isInActiveQueue && queueData.queuePosition !== null
                    ? `#${queueData.queuePosition}`
                    : queueData.status === 'COMPLETED'
                    ? 'Finished'
                    : queueData.status === 'CANCELLED'
                    ? 'Cancelled'
                    : 'Not Assigned'}
                </span>
                <span className="text-xs text-emerald-700 font-bold mt-0.5 block">
                  {queueData.isInActiveQueue && queueData.vehiclesAhead !== null
                    ? `${queueData.vehiclesAhead} Farmers Ahead`
                    : queueData.status === 'COMPLETED'
                    ? 'Transaction Closed'
                    : queueData.status === 'CANCELLED'
                    ? 'Booking Cancelled'
                    : 'Report to gate upon arrival'}
                </span>
              </div>

              {/* Estimated Waiting Time */}
              <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  {language === 'ta' ? 'தோராயக் காத்திருப்பு நேரம்' : 'Estimated Waiting Time'}
                </span>
                <span className="text-xl font-extrabold text-slate-800 mt-1 block">
                  {queueData.hasSufficientDataForEstimate && queueData.estimatedWaitMinutes !== null
                    ? `~${queueData.estimatedWaitMinutes} Mins`
                    : queueData.waitingTimeDisplay || 'Waiting time unavailable'}
                </span>
                <span className="text-xs text-slate-500 mt-0.5 block">
                  {queueData.hasSufficientDataForEstimate
                    ? 'Average weighbridge rate: ~15 min/truck'
                    : 'Requires gate check-in & active yard data'}
                </span>
              </div>
            </div>

            {/* FEATURE 4: 5-STAGE PROGRESSION STEPPER */}
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                {language === 'ta' ? 'கொள்முதல் வாழ்க்கைச் சுழற்சி' : 'Procurement & Weighment Lifecycle'}
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5">
                {queueData.stages.map((st) => (
                  <div
                    key={st.stageNumber}
                    className={`p-3 rounded-2xl border text-xs transition-all relative ${
                      st.state === 'done'
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-medium'
                        : st.state === 'current'
                        ? 'bg-amber-50 border-amber-400 text-amber-950 ring-2 ring-amber-400/30 font-bold shadow-sm'
                        : 'bg-slate-50/70 border-slate-200 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-[10px] font-bold">Step {st.stageNumber}</span>
                      {st.state === 'done' && <Check className="w-4 h-4 text-emerald-600 stroke-[3]" />}
                      {st.state === 'current' && <Clock className="w-4 h-4 text-amber-600 animate-pulse" />}
                    </div>
                    <p className="leading-snug">
                      {language === 'ta' ? st.nameTa : st.name}
                    </p>
                    <span className="text-[10px] uppercase font-bold tracking-wider mt-1 block text-slate-400">
                      {st.code}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* PHASE 3: QUALITY INSPECTION OUTCOME CARD */}
            {queueData.qualityInspection && (
              <div className="rounded-3xl bg-teal-50/70 border border-teal-200 p-5 space-y-3 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-teal-200 pb-2.5">
                  <div className="flex items-center gap-2">
                    <ClipboardCheck className="w-5 h-5 text-teal-700" />
                    <div>
                      <h4 className="text-sm font-bold text-teal-950">
                        Official Mandi Quality Inspection Results
                      </h4>
                      <p className="text-[11px] text-teal-700">
                        Inspected by {queueData.qualityInspection.inspectedByStaff || 'Officer'}
                        {queueData.qualityInspection.inspectedAt ? ` on ${queueData.qualityInspection.inspectedAt}` : ''}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={
                      queueData.qualityInspection.status === 'ACCEPTED'
                        ? 'emerald'
                        : queueData.qualityInspection.status === 'PARTIALLY_ACCEPTED'
                        ? 'amber'
                        : 'rose'
                    }
                    size="sm"
                  >
                    {queueData.qualityInspection.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="bg-white p-3 rounded-2xl border border-teal-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Accepted Weight</span>
                    <span className="text-sm font-extrabold font-mono text-emerald-800">
                      {queueData.qualityInspection.acceptedWeightKg} kg
                    </span>
                    <span className="text-[10px] text-slate-500 block">
                      ~{(queueData.qualityInspection.acceptedWeightKg / 100).toFixed(2)} Qtl
                    </span>
                  </div>

                  <div className="bg-white p-3 rounded-2xl border border-teal-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Rejected Weight</span>
                    <span className="text-sm font-extrabold font-mono text-rose-700">
                      {queueData.qualityInspection.rejectedWeightKg} kg
                    </span>
                    <span className="text-[10px] text-slate-500 block">Dockage / sub-grade</span>
                  </div>

                  <div className="bg-white p-3 rounded-2xl border border-teal-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Moisture Content</span>
                    <span className="text-sm font-extrabold font-mono text-teal-900">
                      {queueData.qualityInspection.moisturePercent}%
                    </span>
                    <span className="text-[10px] text-slate-500 block">FAQ standard ≤ 17%</span>
                  </div>

                  <div className="bg-white p-3 rounded-2xl border border-teal-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Quality Standard</span>
                    <span className="text-xs font-bold text-slate-800 block truncate">
                      {queueData.qualityInspection.qualityGrade}
                    </span>
                  </div>
                </div>

                {queueData.qualityInspection.rejectionReason && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 text-xs flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-rose-800 font-bold">Rejection Justification:</strong>
                      <span>{queueData.qualityInspection.rejectionReason}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* FEATURE 6: TRANSACTION & PAYMENT TRACKING */}
            {queueData.transaction ? (
              <div className="rounded-3xl bg-slate-50 border border-slate-200 p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Scale className="w-4 h-4 text-emerald-700" />
                      Electronic Weighbridge & DBT Ledger Record
                    </h4>
                    <p className="text-xs text-slate-500">
                      Recorded by Officer {queueData.transaction.weighedByStaff} on {queueData.transaction.weighedAt}
                    </p>
                  </div>
                  <Badge
                    variant={
                      queueData.transaction.paymentStatus === 'PAID'
                        ? 'emerald'
                        : 'amber'
                    }
                    size="sm"
                  >
                    DBT Status: {queueData.transaction.paymentStatus}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="bg-white p-3 rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Actual Net Weight</span>
                    <span className="text-sm font-extrabold font-mono text-slate-800">
                      {queueData.transaction.actualNetWeightQuintals} Qtl
                    </span>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">MSP Unit Rate</span>
                    <span className="text-sm font-extrabold font-mono text-slate-800">
                      ₹{queueData.transaction.pricePerQuintal.toLocaleString()}/Qtl
                    </span>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Moisture Tested</span>
                    <span className="text-sm font-extrabold font-mono text-slate-800">
                      {queueData.transaction.moisturePercent}%
                    </span>
                    <span className="text-[10px] text-slate-400 block">FAQ limit: 17%</span>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Deductions</span>
                    <span className="text-sm font-extrabold font-mono text-rose-700">
                      -₹{queueData.transaction.totalDeductionsAmount.toLocaleString()}
                    </span>
                    <span className="text-[10px] text-slate-400 block">Moisture dockage + cess</span>
                  </div>
                </div>

                {/* Amount Ledger Breakdown */}
                <div className="p-4 rounded-2xl bg-white border border-emerald-200 space-y-2 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>Gross Recorded Amount (Weight × MSP Rate):</span>
                    <span className="font-mono font-bold text-slate-800">
                      ₹{queueData.transaction.grossAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex justify-between text-rose-600">
                    <span>Moisture & Dockage Deductions:</span>
                    <span className="font-mono font-bold">
                      -₹{queueData.transaction.totalDeductionsAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-slate-100 flex justify-between items-center text-sm font-extrabold text-emerald-950">
                    <span>Net Payable Amount:</span>
                    <span className="text-lg font-mono text-emerald-700">
                      ₹{queueData.transaction.netPayableAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {/* Explicit Non-Monetary Disclaimer */}
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
                  <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] leading-relaxed">
                    <strong>Payment Disclaimer:</strong> {queueData.transaction.disclaimer} Real bank credit occurs via Canara Bank/PFMS treasury disbursement and does not claim instant automated wire.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
                <Scale className="w-6 h-6 text-slate-300 mx-auto mb-1" />
                <p className="font-semibold text-slate-700">Weighbridge slip has not been generated yet.</p>
                <p className="text-[11px] mt-0.5">
                  Once your vehicle passes through gate check-in and weighbridge inspection, electronic weight slips and DBT payment vouchers will automatically display here.
                </p>
              </div>
            )}

            {/* Audit History Trail */}
            {queueData.auditHistory && queueData.auditHistory.length > 0 && (
              <div className="pt-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Audit History (Database Timeline)
                </h4>
                <div className="space-y-2">
                  {queueData.auditHistory.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-xl border border-slate-200 text-xs flex items-start justify-between"
                    >
                      <div>
                        <span className="font-bold text-slate-800">{item.action}</span>
                        <span className="text-slate-500 block text-[11px] mt-0.5">
                          {item.notes || 'Recorded action'}
                        </span>
                      </div>
                      <div className="text-right text-[11px] text-slate-400 font-mono">
                        <span className="block font-medium text-slate-600">{item.by} ({item.role})</span>
                        <span>{item.timestamp}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </>
      ) : (
        <div className="p-12 text-center text-xs text-slate-400 bg-white rounded-3xl border border-slate-200">
          Search for a booking ID or select one of your reservations above to view its live status.
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import {
  X,
  Printer,
  ShieldCheck,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Building2,
  CreditCard,
  User,
  Calendar,
  Loader2,
} from 'lucide-react';
import type { DigitalBillEntity } from '../../services/api';
import { staffUpdatePaymentStatusApi } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

interface DigitalBillModalProps {
  bill: DigitalBillEntity | null;
  isOpen: boolean;
  onClose: () => void;
  onPaymentUpdated?: (updatedBill: DigitalBillEntity) => void;
  isStaff?: boolean;
}

export const DigitalBillModal: React.FC<DigitalBillModalProps> = ({
  bill,
  isOpen,
  onClose,
  onPaymentUpdated,
  isStaff = false,
}) => {
  const { language } = useLanguage();
  const { token } = useAuth();

  const [newStatus, setNewStatus] = useState<'PENDING' | 'PROCESSING' | 'PAID'>('PROCESSING');
  const [txRef, setTxRef] = useState('');
  const [updateNotes, setUpdateNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  if (!isOpen || !bill) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleUpdatePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !bill) return;

    setIsUpdating(true);
    setUpdateError(null);
    setUpdateSuccess(null);

    try {
      const updated = await staffUpdatePaymentStatusApi(
        bill.billNumber || bill.bookingId,
        {
          newStatus,
          notes: updateNotes || `Payment status marked as ${newStatus}`,
          transactionReference: txRef || undefined,
        },
        token
      );
      setUpdateSuccess(`Payment status successfully updated to ${newStatus}!`);
      if (onPaymentUpdated) {
        onPaymentUpdated(updated);
      }
    } catch (err: any) {
      setUpdateError(err.message || 'Failed to update payment status.');
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'PAID') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {language === 'ta' ? 'வங்கி கணக்கில் செலுத்தப்பட்டது (PAID)' : 'DISBURSED / PAID'}
        </span>
      );
    }
    if (s === 'PROCESSING') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300">
          <Clock className="w-3.5 h-3.5 animate-pulse" />
          {language === 'ta' ? 'வங்கி அனுமதி பரிசீலனையில் (PROCESSING)' : 'TREASURY DBT PROCESSING'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
        <AlertCircle className="w-3.5 h-3.5" />
        {language === 'ta' ? 'பட்டுவாடா நிலுவையில் (PENDING)' : 'PAYMENT PENDING'}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/70 backdrop-blur-sm overflow-y-auto print:p-0 print:bg-white print:static">
      <div className="relative w-full max-w-3xl my-6 bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden print:border-none print:shadow-none print:rounded-none">
        {/* Modal Controls (Hidden in Print) */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-50 border-b border-slate-200 print:hidden">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-700" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              {language === 'ta' ? 'அதிகாரப்பூர்வ டிஜிட்டல் கொள்முதல் ரசீது' : 'Official Electronic Procurement Bill'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold shadow-sm transition-colors"
            >
              <Printer className="w-4 h-4" />
              <span>{language === 'ta' ? 'அச்சிடு / PDF சேமி' : 'Print / Save PDF'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Bill Paper Content */}
        <div className="p-6 sm:p-8 space-y-6 text-slate-800 text-xs">
          {/* Government / Mandi Header */}
          <div className="text-center border-b-2 border-emerald-800/30 pb-5">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 mb-2">
              <Building2 className="w-6 h-6" />
            </div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">
              Government of Tamil Nadu • Department of Agricultural Marketing & Agri Business
            </p>
            <h1 className="text-lg sm:text-xl font-black text-slate-900 mt-0.5">
              {language === 'ta' ? 'தமிழ்நாடு நுகர்பொருள் வாணிபக் கழகம் - மின்னணு கொள்முதல் பட்டியல்' : 'DIRECT PURCHASE CENTRE (DPC) WEIGHMENT BILL & DBT VOUCHER'}
            </h1>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5">
              Tamil Nadu Civil Supplies Corporation & Regulated Mandi Platform
            </p>

            <div className="mt-3 flex items-center justify-center gap-3 flex-wrap">
              <span className="px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 font-mono font-bold text-emerald-800 text-xs">
                Bill #: {bill.billNumber}
              </span>
              <span className="px-3 py-1 rounded-lg bg-slate-100 border border-slate-200 font-mono font-semibold text-slate-700 text-xs">
                Token #: {bill.tokenNumber || 'TN-DPC'}
              </span>
              {getStatusBadge(bill.paymentStatus)}
            </div>
          </div>

          {/* Farmer & Procurement Centre Meta Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50/70 p-4 rounded-2xl border border-slate-200">
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-slate-500 font-semibold text-[11px]">
                <User className="w-3.5 h-3.5 text-emerald-700" />
                <span>{language === 'ta' ? 'விவசாயி விவரம்' : 'Farmer Beneficiary'}</span>
              </div>
              <p className="font-bold text-sm text-slate-900">{bill.farmerName}</p>
              <p className="font-mono text-slate-600 text-[11px]">ID: {bill.farmerId}</p>
              <p className="font-mono text-slate-500 text-[10px]">Booking Ref: {bill.bookingId}</p>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-slate-500 font-semibold text-[11px]">
                <Building2 className="w-3.5 h-3.5 text-emerald-700" />
                <span>{language === 'ta' ? 'கொள்முதல் மையம்' : 'Procurement Centre & Date'}</span>
              </div>
              <p className="font-bold text-sm text-slate-900">{bill.mandiName}</p>
              <p className="flex items-center gap-1 text-slate-600 font-mono text-[11px]">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>{bill.transactionDate || bill.weighedAt}</span>
              </p>
              <p className="text-[10px] text-slate-500">Weighed By: Officer {bill.weighedByStaff}</p>
            </div>
          </div>

          {/* Weighment & Crop Specifications */}
          <div className="rounded-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-100/70 px-4 py-2.5 font-bold text-slate-700 text-xs flex items-center justify-between">
              <span>{language === 'ta' ? 'தானிய எடை மற்றும் தர விவரங்கள்' : 'Crop & Weighbridge Specifications'}</span>
              <span className="font-mono text-emerald-700">ISO 9001:2015 Metric Weighment</span>
            </div>
            <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white text-center">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block uppercase font-bold">Crop Variety</span>
                <span className="font-bold text-slate-800 text-xs block truncate">{bill.crop}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-emerald-50/70 border border-emerald-100">
                <span className="text-[10px] text-emerald-700 block uppercase font-bold">Accepted Net Weight</span>
                <span className="font-bold text-emerald-900 text-sm font-mono block">
                  {bill.acceptedWeightKg.toLocaleString()} kg
                </span>
                <span className="text-[10px] text-emerald-600 font-mono">
                  ({bill.actualNetWeightQuintals} Quintals)
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block uppercase font-bold">MSP Rate / Kg</span>
                <span className="font-bold text-slate-800 text-sm font-mono block">
                  ₹{bill.pricePerKg.toFixed(2)}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  (₹{bill.pricePerQuintal.toFixed(2)}/Qtl)
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block uppercase font-bold">Moisture / Grade</span>
                <span className="font-bold text-slate-800 text-xs block">
                  Grade A FAQ
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  Standard Verified
                </span>
              </div>
            </div>
          </div>

          {/* Financial Calculation Table */}
          <div className="rounded-2xl border border-slate-200 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100/70 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Financial Ledger Component</th>
                  <th className="py-2.5 px-4 text-center">Calculation Basis</th>
                  <th className="py-2.5 px-4 text-right">Amount (INR)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                <tr>
                  <td className="py-3 px-4 font-sans font-semibold text-slate-800">
                    Gross Crop Value
                    <span className="block text-[10px] text-slate-400 font-normal">
                      Accepted weight multiplied by MSP rate per kg
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center text-slate-600">
                    {bill.acceptedWeightKg} kg × ₹{bill.pricePerKg.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-slate-900">
                    ₹{bill.grossAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                <tr>
                  <td className="py-2.5 px-4 font-sans text-slate-600">
                    Quality / Moisture Dockage Deductions
                    <span className="block text-[10px] text-slate-400 font-normal">
                      Excess moisture tolerance docking (Standard max 17%)
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-center text-slate-500">Standard FAQ</td>
                  <td className="py-2.5 px-4 text-right text-rose-600">
                    - ₹{bill.qualityDeductionsAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                <tr>
                  <td className="py-2.5 px-4 font-sans text-slate-600">
                    Authorized Handling & Mandi Cess Deductions
                    <span className="block text-[10px] text-slate-400 font-normal">
                      Statutory regulatory market deductions
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-center text-slate-500">Government Cess</td>
                  <td className="py-2.5 px-4 text-right text-rose-600">
                    - ₹{bill.otherDeductionsAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                <tr className="bg-slate-50 font-semibold text-slate-700">
                  <td className="py-2.5 px-4 font-sans">Total Validated Deductions</td>
                  <td className="py-2.5 px-4 text-center text-slate-500">Sum of deductions</td>
                  <td className="py-2.5 px-4 text-right text-rose-700 font-bold">
                    - ₹{bill.totalDeductionsAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>

                {/* Net Payable Highlight */}
                <tr className="bg-emerald-50/90 text-emerald-950 font-bold text-sm">
                  <td className="py-4 px-4 font-sans">
                    <span className="block text-emerald-900 font-black">NET BENEFICIARY PAYABLE AMOUNT</span>
                    <span className="text-[10px] text-emerald-700 font-normal font-sans">
                      Gross amount minus validated deductions
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center text-emerald-800 text-xs font-sans">
                    PFMS / e-Kuber Ledger
                  </td>
                  <td className="py-4 px-4 text-right text-base text-emerald-800 font-black">
                    ₹{bill.netAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Payment & DBT Settlement Notice */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-700 shrink-0" />
                <span className="font-bold text-slate-800">
                  {language === 'ta' ? 'வங்கி கணக்கில் செலுத்தும் முறை (DBT)' : 'Disbursement Route: Direct Benefit Transfer (PFMS / e-Kuber)'}
                </span>
              </div>
              <span className="font-mono text-slate-500 text-[11px]">
                Status: <strong>{bill.paymentStatus}</strong>
              </span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              {bill.disclaimer ||
                'This electronic procurement receipt is registered in the state civil supplies ledger. Actual bank fund transfer requires state treasury gateway clearance and Aadhaar-seeded bank account authorization.'}
            </p>
          </div>

          {/* Payment History Timeline */}
          {bill.paymentHistory && bill.paymentHistory.length > 0 && (
            <div className="border border-slate-200 rounded-2xl p-4 bg-white">
              <span className="font-bold text-slate-700 text-xs block mb-2">
                {language === 'ta' ? 'பட்டுவாடா பரிவர்த்தனை வரலாறு' : 'Payment Status & Audit Trail'}
              </span>
              <div className="space-y-2 font-mono text-[11px]">
                {bill.paymentHistory.map((h, idx) => (
                  <div key={idx} className="flex items-start justify-between border-b border-slate-100 pb-1.5 last:border-b-0">
                    <div>
                      <span className="font-bold text-slate-800 mr-2">{h.status}</span>
                      <span className="text-slate-500">{h.notes}</span>
                      {h.transactionReference && (
                        <span className="block text-emerald-700 font-semibold text-[10px]">
                          Ref: {h.transactionReference}
                        </span>
                      )}
                    </div>
                    <div className="text-right text-slate-400 text-[10px] shrink-0 ml-2">
                      <span>{h.updatedBy}</span>
                      <span className="block">{h.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Staff Payment Update Action Form (Only visible to Authorized Staff, hidden in Print) */}
          {isStaff && (
            <div className="mt-6 p-4 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3 print:hidden">
              <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                <ShieldCheck className="w-4 h-4 text-amber-700" />
                <span>Authorized Staff Action: Update Payment Status</span>
              </div>

              {updateError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
                  {updateError}
                </div>
              )}
              {updateSuccess && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
                  {updateSuccess}
                </div>
              )}

              <form onSubmit={handleUpdatePayment} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    New Payment Status *
                  </label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as any)}
                    className="w-full p-2 bg-white rounded-xl border border-slate-300 font-bold text-xs text-slate-800"
                  >
                    <option value="PENDING">PENDING</option>
                    <option value="PROCESSING">PROCESSING (Treasury Sent)</option>
                    <option value="PAID">PAID (Bank Credit Confirmed)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    Bank / PFMS Reference (UTR)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. UTR-SBI-2026-991"
                    value={txRef}
                    onChange={(e) => setTxRef(e.target.value)}
                    className="w-full p-2 bg-white rounded-xl border border-slate-300 text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    Remarks / Bank Notes
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Account verified"
                    value={updateNotes}
                    onChange={(e) => setUpdateNotes(e.target.value)}
                    className="w-full p-2 bg-white rounded-xl border border-slate-300 text-xs"
                  />
                </div>

                <div className="sm:col-span-3 flex justify-end">
                  <button
                    type="submit"
                    disabled={isUpdating}
                    className="px-5 py-2 rounded-xl bg-amber-700 hover:bg-amber-800 disabled:bg-slate-300 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition-colors"
                  >
                    {isUpdating ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Updating...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Confirm Payment Status Update</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Official Signatures */}
          <div className="pt-8 border-t border-slate-200 grid grid-cols-2 text-center text-[10px] text-slate-500">
            <div>
              <div className="w-32 h-0.5 bg-slate-300 mx-auto mb-1"></div>
              <p className="font-semibold text-slate-700">Procurement Officer / Operator</p>
              <p>{bill.weighedByStaff} ({bill.mandiName})</p>
            </div>
            <div>
              <div className="w-32 h-0.5 bg-slate-300 mx-auto mb-1"></div>
              <p className="font-semibold text-slate-700">Beneficiary Farmer Acknowledgement</p>
              <p>{bill.farmerName} ({bill.farmerId})</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

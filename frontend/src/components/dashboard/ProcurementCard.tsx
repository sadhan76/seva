import React, { useState } from 'react';
import { Building2, QrCode, Calendar, Clock, PackageCheck, Scale, CheckCircle2, X, PlusCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import type { ProcurementSlot } from '../../types';

interface ProcurementCardProps {
  slot?: ProcurementSlot | null;
  onTrackQueue?: () => void;
  onBookNew?: () => void;
}

export const ProcurementCard: React.FC<ProcurementCardProps> = ({
  slot,
  onTrackQueue,
  onBookNew,
}) => {
  const { t, language } = useLanguage();
  const [showQrModal, setShowQrModal] = useState(false);

  // If farmer has no active booking
  if (!slot || !slot.bookingId) {
    return (
      <Card
        title={t.dashboard.procurementTitle}
        subtitle={language === 'ta' ? 'தமிழ்நாடு நுகர்பொருள் வாணிபக் கழகம்' : 'TN Civil Supplies Department (TNCSC)'}
        icon={<Building2 className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <Badge variant="slate" dot>
            {language === 'ta' ? 'முன்பதிவு இல்லை' : 'No Active Slot'}
          </Badge>
        }
        footer={
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>{language === 'ta' ? 'நேரடி நெல் கொள்முதல்' : 'Direct Paddy Procurement'}</span>
            {onBookNew && (
              <button
                onClick={onBookNew}
                className="text-xs font-bold text-emerald-700 hover:text-emerald-800 hover:underline flex items-center gap-1"
              >
                <span>{language === 'ta' ? 'முன்பதிவு செய்க' : 'Book a Slot'} →</span>
              </button>
            )}
          </div>
        }
      >
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-center space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-800">
              {language === 'ta'
                ? 'தற்போது தீவிர முன்பதிவு எதுவும் இல்லை'
                : 'No Active Mandi Procurement Slot'}
            </p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-xs mx-auto">
              {language === 'ta'
                ? 'கொள்முதல் மையங்களில் காத்திருப்பதை தவிர்க்க உங்கள் அறுவடை நெல்லை முன்கூட்டியே பதிவு செய்யுங்கள்.'
                : 'Book a direct procurement centre delivery slot in advance to avoid mandi gate lines.'}
            </p>
          </div>
          {onBookNew && (
            <button
              type="button"
              onClick={onBookNew}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition-all active:scale-95"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>{language === 'ta' ? 'புதிய முன்பதிவு தொடங்குக' : 'Schedule Mandi Delivery'}</span>
            </button>
          )}
        </div>
      </Card>
    );
  }

  // Active Booking Card
  return (
    <>
      <Card
        title={t.dashboard.procurementTitle}
        subtitle={slot.mandiName}
        icon={<Building2 className="w-5 h-5 text-emerald-700" />}
        headerAction={
          <Badge variant={slot.isFromDb ? 'emerald' : 'amber'} dot>
            {slot.isFromDb
              ? (language === 'ta' ? 'உறுதி செய்யப்பட்டது' : 'Live Booking')
              : 'DEMO'}
          </Badge>
        }
        footer={
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5 font-medium text-emerald-700">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {t.dashboard.labels.confirmed}
            </span>
            <div className="flex items-center gap-3">
              {onBookNew && (
                <button
                  onClick={onBookNew}
                  className="text-xs font-semibold text-slate-600 hover:text-emerald-700 hover:underline"
                >
                  + New Booking
                </button>
              )}
              {onTrackQueue && (
                <button
                  onClick={onTrackQueue}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline"
                >
                  Live Queue →
                </button>
              )}
            </div>
          </div>
        }
      >
        <div className="flex flex-col gap-4">
          {/* Top Token and Status Bar */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-gradient-to-r from-emerald-500/10 via-emerald-600/5 to-transparent border border-emerald-200">
            <div>
              <span className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider block">
                {t.dashboard.labels.tokenNo}
              </span>
              <span className="text-xl font-mono font-extrabold text-emerald-800 tracking-tight">
                {slot.tokenNumber}
              </span>
              <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                {slot.bookingId}
              </p>
            </div>

            <button
              onClick={() => setShowQrModal(true)}
              className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
              title="View QR Entry Pass"
            >
              <QrCode className="w-4 h-4" />
              QR Token
            </button>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
              <div className="flex items-center gap-1 text-slate-400 mb-1">
                <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-[11px] font-medium text-slate-500 uppercase">{t.common.date}</span>
              </div>
              <p className="text-xs font-bold text-slate-800">{slot.slotDate}</p>
            </div>

            <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
              <div className="flex items-center gap-1 text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-blue-600" />
                <span className="text-[11px] font-medium text-slate-500 uppercase">{t.dashboard.labels.slotTime}</span>
              </div>
              <p className="text-xs font-bold text-slate-800">{slot.timeWindow}</p>
            </div>

            <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
              <div className="flex items-center gap-1 text-slate-400 mb-1">
                <PackageCheck className="w-3.5 h-3.5 text-indigo-600" />
                <span className="text-[11px] font-medium text-slate-500 uppercase">{t.dashboard.labels.quantity}</span>
              </div>
              <p className="text-xs font-bold text-slate-800">
                {slot.quantityBags} {t.dashboard.labels.bags}
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
              <div className="flex items-center gap-1 text-slate-400 mb-1">
                <Scale className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-[11px] font-medium text-slate-500 uppercase">{language === 'ta' ? 'எடை (குவிண்டால்)' : 'Est. Weight'}</span>
              </div>
              <p className="text-xs font-bold text-slate-800">
                {slot.estimatedWeightQuintals} Qtl
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* QR Token Modal */}
      {showQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 text-center relative">
            <button
              onClick={() => setShowQrModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-base font-bold text-slate-900 mb-1">
              Official Entry Pass
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Present this token to the gate inspector at the Mandi entrance.
            </p>

            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 inline-block mb-4">
              <div className="w-40 h-40 bg-white border border-slate-300 rounded-xl flex items-center justify-center mx-auto shadow-inner">
                <div className="text-center p-2">
                  <QrCode className="w-24 h-24 text-emerald-800 mx-auto" />
                  <span className="text-[11px] font-mono font-bold text-slate-700 block mt-1">
                    {slot.tokenNumber}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-xs text-slate-600 space-y-1 mb-5">
              <p><strong>Booking ID:</strong> {slot.bookingId}</p>
              <p><strong>Slot:</strong> {slot.slotDate} ({slot.timeWindow})</p>
              <p><strong>Centre:</strong> {slot.mandiName}</p>
            </div>

            <button
              onClick={() => setShowQrModal(false)}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs"
            >
              Close Pass
            </button>
          </div>
        </div>
      )}
    </>
  );
};

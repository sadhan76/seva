import React from 'react';
import { Droplet, Clock, Waves, Sparkles } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import type { IrrigationAdvice } from '../../types';

interface IrrigationAdviceCardProps {
  advice: IrrigationAdvice;
  onOpenSchedule?: () => void;
}

export const IrrigationAdviceCard: React.FC<IrrigationAdviceCardProps> = ({
  advice,
  onOpenSchedule,
}) => {
  const { t } = useLanguage();

  return (
    <Card
      title={t.dashboard.irrigationTitle}
      subtitle="AI Soil Moisture & Drip Optimizer"
      icon={<Droplet className="w-5 h-5 text-blue-600" />}
      headerAction={
        <Badge variant="blue" dot>
          {t.sampleBadge}
        </Badge>
      }
      footer={
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1.5 text-blue-700 font-medium">
            <Waves className="w-3.5 h-3.5" />
            Sensor Node #TN-04 (Mock Active)
          </span>
          {onOpenSchedule && (
            <button
              onClick={onOpenSchedule}
              className="text-xs font-semibold text-blue-700 hover:text-blue-800 hover:underline"
            >
              Adjust Timer →
            </button>
          )}
        </div>
      }
    >
      <div className="flex flex-col gap-4">
        {/* Moisture Level Meter */}
        <div className="rounded-xl bg-blue-50/50 border border-blue-100 p-3.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Droplet className="w-4 h-4 text-blue-500 fill-blue-500" />
              {t.dashboard.labels.soilMoisture}
            </span>
            <span className="text-xs font-bold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-full">
              {advice.soilMoisturePercent}% ({t.dashboard.labels.optimal})
            </span>
          </div>

          <div className="w-full h-3 bg-blue-100/70 rounded-full overflow-hidden relative">
            <div
              className="h-full bg-gradient-to-r from-blue-400 to-emerald-500 rounded-full transition-all duration-700"
              style={{ width: `${advice.soilMoisturePercent}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
            <span>0% (Dry)</span>
            <span>Target: 60-70%</span>
            <span>100% (Saturated)</span>
          </div>
        </div>

        {/* Schedule & Savings */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Clock className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-[11px] font-semibold uppercase">{t.dashboard.labels.nextIrrigation}</span>
            </div>
            <p className="text-xs font-bold text-slate-800">
              {advice.nextScheduledTime}
            </p>
          </div>

          <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-[11px] font-semibold uppercase">{t.dashboard.labels.waterSaved}</span>
            </div>
            <p className="text-xs font-bold text-emerald-700">
              ~{advice.waterSavedLiters.toLocaleString()} Liters
            </p>
          </div>
        </div>

        {/* AI Recommendation Quote */}
        <div className="rounded-xl bg-emerald-50/60 border border-emerald-200/60 p-3 text-xs leading-relaxed text-emerald-900">
          <span className="font-bold text-emerald-800 block mb-1">
            💡 {t.dashboard.labels.advice}:
          </span>
          {advice.recommendation}
        </div>
      </div>
    </Card>
  );
};

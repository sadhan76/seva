import React from 'react';
import { Activity, ShieldCheck, Camera, Calendar } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import type { CropHealth } from '../../types';

interface CropHealthCardProps {
  health: CropHealth;
  onScanLeaf?: () => void;
}

export const CropHealthCard: React.FC<CropHealthCardProps> = ({
  health,
  onScanLeaf,
}) => {
  const { t } = useLanguage();

  return (
    <Card
      title={t.dashboard.cropHealthTitle}
      subtitle={health.cropName}
      icon={<Activity className="w-5 h-5 text-emerald-600" />}
      headerAction={
        <Badge variant="emerald" dot>
          {t.sampleBadge}
        </Badge>
      }
      footer={
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1.5 text-slate-500">
            <Calendar className="w-3.5 h-3.5" />
            {t.dashboard.labels.lastScanned}: {health.lastScannedDate}
          </span>
          {onScanLeaf && (
            <button
              onClick={onScanLeaf}
              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline"
            >
              <Camera className="w-3.5 h-3.5" />
              New Scan →
            </button>
          )}
        </div>
      }
    >
      <div className="flex flex-col gap-4">
        {/* Score and Stage Header */}
        <div className="flex items-center justify-between bg-emerald-50/70 border border-emerald-100 p-3.5 rounded-xl">
          <div>
            <span className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider block">
              {t.dashboard.labels.healthScore}
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-3xl font-extrabold text-emerald-700">
                {health.healthScorePercent}%
              </span>
              <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                {t.dashboard.labels.healthy}
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              {t.dashboard.labels.cropStage}
            </span>
            <span className="text-xs font-bold text-slate-800 block mt-0.5">
              {health.stage}
            </span>
          </div>
        </div>

        {/* Diagnosis Note */}
        <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
          <div className="flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-600 leading-relaxed">
              <span className="font-semibold text-slate-800">Field Health Notes: </span>
              {health.notes}
            </div>
          </div>
        </div>

        {/* Disease Risk Index */}
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium">Blast Risk</p>
            <p className="text-xs font-bold text-emerald-600 mt-0.5">Low (5%)</p>
          </div>
          <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium">Stem Borer</p>
            <p className="text-xs font-bold text-emerald-600 mt-0.5">Low (2%)</p>
          </div>
          <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] text-slate-400 font-medium">Leaf Scald</p>
            <p className="text-xs font-bold text-emerald-600 mt-0.5">Negligible</p>
          </div>
        </div>
      </div>
    </Card>
  );
};

import React from 'react';
import { TrendingUp, ArrowUpRight, ArrowDownRight, Building2 } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';

interface MarketPricesCardProps {
  onViewMarket?: () => void;
}

export const MarketPricesCard: React.FC<MarketPricesCardProps> = ({ onViewMarket }) => {
  const { t } = useLanguage();

  const keyRates = [
    {
      cropEn: 'Paddy Grade A (சம்பா நெல்)',
      mandi: 'Thanjavur DPC',
      price: 2320,
      trend: 'up',
      change: '+₹25',
      unit: 'Qtl',
    },
    {
      cropEn: 'Black Gram (உளுந்து ADT 5)',
      mandi: 'Madurai Mandi',
      price: 8200,
      trend: 'down',
      change: '-₹40',
      unit: 'Qtl',
    },
    {
      cropEn: 'Paddy Common (பொன்னி நெல்)',
      mandi: 'Kumbakonam Yard',
      price: 2300,
      trend: 'up',
      change: '+₹10',
      unit: 'Qtl',
    },
    {
      cropEn: 'Groundnut (நிலக்கடலை)',
      mandi: 'Erode Regulated Market',
      price: 6900,
      trend: 'up',
      change: '+₹80',
      unit: 'Qtl',
    },
  ];

  return (
    <Card
      title={t.dashboard.marketPricesTitle}
      subtitle="Regulated Market Committee Modal Rates"
      icon={<TrendingUp className="w-5 h-5 text-amber-600" />}
      headerAction={
        <Badge variant="amber" dot>
          {t.sampleBadge}
        </Badge>
      }
      footer={
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="text-[11px] text-slate-400">
            Simulated Agmarknet Feed
          </span>
          {onViewMarket && (
            <button
              onClick={onViewMarket}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline inline-flex items-center gap-1"
            >
              {t.dashboard.labels.viewAllMandis}
            </button>
          )}
        </div>
      }
    >
      <div className="space-y-2.5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {keyRates.map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-50/80 border border-slate-200/80 hover:border-emerald-200 hover:bg-emerald-50/20 transition-all flex items-center justify-between"
            >
              <div className="min-w-0 pr-2">
                <p className="text-xs font-bold text-slate-800 truncate">
                  {item.cropEn}
                </p>
                <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-0.5 truncate">
                  <Building2 className="w-3 h-3 text-slate-400 shrink-0" />
                  <span className="truncate">{item.mandi}</span>
                </div>
              </div>

              <div className="text-right shrink-0">
                <p className="text-sm font-black text-slate-900">
                  ₹{item.price.toLocaleString()}
                  <span className="text-[10px] text-slate-400 font-normal">/{item.unit}</span>
                </p>
                <span
                  className={`inline-flex items-center text-[10px] font-bold ${
                    item.trend === 'up' ? 'text-emerald-600' : 'text-rose-600'
                  }`}
                >
                  {item.trend === 'up' ? (
                    <ArrowUpRight className="w-3 h-3" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3" />
                  )}
                  {item.change}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

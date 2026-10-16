import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Search,
  MapPin,
  RefreshCw,
  Calendar,
  Building2,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import {
  getMarketPricesApi,
  type MarketPricesResponse,
} from '../../services/api';

const DISTRICT_FILTERS = [
  'All',
  'Thanjavur',
  'Madurai',
  'Tiruchirappalli',
  'Erode',
  'Tiruppur',
  'Salem',
];

export const MarketPricesView: React.FC = () => {
  const { t, language } = useLanguage();

  const [filter, setFilter] = useState('');
  const [districtFilter, setDistrictFilter] = useState('All');
  const [marketData, setMarketData] = useState<MarketPricesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrices = async () => {
    try {
      setError(null);
      const res = await getMarketPricesApi(
        districtFilter === 'All' ? undefined : districtFilter,
        filter ? filter : undefined
      );
      setMarketData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load market prices.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchPrices();
  }, [districtFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPrices();
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPrices();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.market}
        subtitle={
          language === 'ta'
            ? 'ஒழுங்குமுறை விற்பனைக் கூடங்கள் மற்றும் நேரடி நெல் கொள்முதல் நிலைய தினசரி சந்தை நிலவரம்'
            : 'Tamil Nadu Regulated Market Yards & DPC Procurement Daily Commodity Rates'
        }
        icon={<TrendingUp className="w-5 h-5 text-amber-600" />}
        headerAction={
          <Badge variant="amber" dot>
            Agmarknet Benchmark Data
          </Badge>
        }
      >
        <div className="space-y-5">
          {/* Transparent Source & Demonstration Notice */}
          <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">
                {language === 'ta'
                  ? 'மாதிரி குறிப்பு கட்டண அறிவிப்பு (அதிகாரப்பூர்வ விலை உத்தரவாதமில்லை)'
                  : 'Demonstration Benchmark Notice (Non-Official Guarantee Notice)'}
              </p>
              <p className="text-[11px] text-amber-800/90 mt-0.5 leading-relaxed">
                {language === 'ta'
                  ? marketData?.demoNoticeTa ||
                    'கீழே குறிப்பிடப்பட்டுள்ள விலைகள் திட்டமிடல் மற்றும் கல்வி நோக்கங்களுக்கான மாதிரி குறிப்பு விகிதங்கள் மட்டுமே. அறுவடை செய்த விளைபொருட்களை ஏற்றிச் செல்வதற்கு முன் உங்கள் பகுதி ஒழுங்குமுறை விற்பனைக்கூட செயலாளரிடம் அன்றைய நேரடி ஏல விலையை உறுதிப்படுத்தவும்.'
                  : marketData?.demoNoticeEn ||
                    "Displayed rates are curated demonstration benchmark datasets for agricultural planning and price transparency. Never represent these as today's guaranteed official auction price. Confirm live daily mandi arrivals and quality grade cuts with your local market secretary."}
              </p>
            </div>
          </div>

          {/* Search & District Filter Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200/90 rounded-2xl">
            <form onSubmit={handleSearchSubmit} className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder={
                  language === 'ta'
                    ? 'பயிர் அல்லது ஒழுங்குமுறை கூடத்தை தேடுக...'
                    : 'Search commodity, crop, or mandi yard name...'
                }
                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </form>

            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-slate-400 shrink-0 hidden sm:inline" />
              <select
                value={districtFilter}
                onChange={(e) => setDistrictFilter(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 focus:ring-2 focus:ring-emerald-500/20"
              >
                {DISTRICT_FILTERS.map((d) => (
                  <option key={d} value={d}>
                    {d === 'All' ? (language === 'ta' ? 'அனைத்து மாவட்டங்கள்' : 'All Districts') : d}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing || loading}
                className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 shadow-2xs transition-all disabled:opacity-50"
                title="Refresh Market Rates"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Data Source & Timestamp Banner */}
          {marketData && (
            <div className="px-4 py-2 bg-white rounded-xl border border-slate-200 text-[11px] text-slate-500 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1">
              <span className="flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                <strong className="text-slate-700">Source: </strong> {marketData.dataSource}
              </span>
              <span className="flex items-center gap-1.5 font-mono text-[10px]">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {marketData.timestamp}
              </span>
            </div>
          )}

          {/* Table */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold">Loading market pricing matrix...</p>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center">
              {error}
            </div>
          ) : marketData?.commodities && marketData.commodities.length > 0 ? (
            <div className="overflow-x-auto rounded-2xl border border-slate-200/90 shadow-2xs">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-600 uppercase font-bold tracking-wider text-[10px]">
                    <th className="py-3 px-4">Crop / Commodity</th>
                    <th className="py-3 px-4">Market Yard & District</th>
                    <th className="py-3 px-4">Modal Price</th>
                    <th className="py-3 px-4">Min - Max Range</th>
                    <th className="py-3 px-4">24h Movement</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {marketData.commodities.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4">
                        <p className="font-bold text-slate-900">{item.crop}</p>
                        <p className="text-[11px] text-slate-400 font-normal">{item.cropTa}</p>
                      </td>
                      <td className="py-3 px-4">
                        <p className="font-semibold text-slate-800">{item.mandi}</p>
                        <p className="text-[11px] text-slate-400">{item.district} District</p>
                      </td>
                      <td className="py-3 px-4 font-black text-slate-900 text-sm">
                        ₹{item.modalPrice.toLocaleString()}{' '}
                        <span className="text-[10px] text-slate-400 font-normal">/{item.unit}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        ₹{item.minPrice.toLocaleString()} - ₹{item.maxPrice.toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 font-bold text-[11px] px-2 py-0.5 rounded-md ${
                            item.trend === 'up'
                              ? 'text-emerald-700 bg-emerald-50 border border-emerald-200'
                              : item.trend === 'down'
                              ? 'text-rose-700 bg-rose-50 border border-rose-200'
                              : 'text-slate-600 bg-slate-100'
                          }`}
                        >
                          {item.trend === 'up' && <ArrowUpRight className="w-3.5 h-3.5" />}
                          {item.trend === 'down' && <ArrowDownRight className="w-3.5 h-3.5" />}
                          {item.change}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400">
              <p className="text-sm font-semibold">No commodities found matching current filter.</p>
              <p className="text-xs text-slate-400 mt-1">Try resetting the district or search keyword.</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

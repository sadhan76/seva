import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Search,
  MapPin,
  RefreshCw,
  Calendar,
  Building2,
  Loader2,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Filter,
  ExternalLink,
  Clock,
  CheckCircle2,
  Timer,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getMarketPricesApi,
  getDistrictsApi,
  type MarketPricesResponse,
  type MarketCommodityItem,
} from '../../services/api';

const DEFAULT_DISTRICTS = [
  'All',
  'Coimbatore',
  'Cuddalore',
  'Dindigul',
  'Erode',
  'Madurai',
  'Salem',
  'Thanjavur',
  'Tiruchirappalli',
  'Tirunelveli',
  'Tiruppur',
  'Vellore',
];

export const MarketPricesView: React.FC = () => {
  const { t, language } = useLanguage();
  const { user } = useAuth();

  const [searchInput, setSearchInput] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [districtFilter, setDistrictFilter] = useState(user?.district || 'All');
  const [commodityFilter, setCommodityFilter] = useState('All');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  const [marketData, setMarketData] = useState<MarketPricesResponse | null>(null);
  const [dynamicDistricts, setDynamicDistricts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchDistrictOptions() {
      const stateToQuery = user?.state || 'Tamil Nadu';
      const dList = await getDistrictsApi(stateToQuery);
      if (isMounted) {
        const names = dList.map((d) => d.name);
        if (user?.district && !names.includes(user.district)) {
          names.unshift(user.district);
        }
        setDynamicDistricts(names);
      }
    }
    fetchDistrictOptions();
    return () => {
      isMounted = false;
    };
  }, [user?.state, user?.district]);

  // Reference to track whether component is actively mounted and whether initial fetch completed
  const isMountedRef = useRef(true);
  const initialLoadDoneRef = useRef(false);

  const fetchPrices = useCallback(
    async (forceRefresh = false, isSilent = false) => {
      try {
        setError(null);
        if (forceRefresh) {
          setRefreshing(true);
        } else if (!isSilent && !initialLoadDoneRef.current) {
          setLoading(true);
        }

        const res = await getMarketPricesApi({
          district: districtFilter === 'All' ? undefined : districtFilter,
          commodity: commodityFilter === 'All' ? undefined : commodityFilter,
          search: activeSearch ? activeSearch : undefined,
          page: currentPage,
          limit: pageSize,
          sortBy: 'arrival_date',
          sortOrder: 'desc',
          forceRefresh: forceRefresh,
        });

        if (isMountedRef.current) {
          setMarketData(res);
          initialLoadDoneRef.current = true;
        }
      } catch (err: any) {
        if (isMountedRef.current) {
          setError(err.message || 'Failed to load regulated mandi market rates.');
        }
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [districtFilter, commodityFilter, activeSearch, currentPage, pageSize]
  );

  // Initial fetch and automatic 60-second polling while page is active
  useEffect(() => {
    isMountedRef.current = true;
    fetchPrices(false, false);

    // 60-second periodic background refresh
    const pollInterval = window.setInterval(() => {
      // Avoid unnecessary requests when browser tab or view is not visible
      if (!document.hidden && isMountedRef.current) {
        fetchPrices(false, true); // silent background poll
      }
    }, 60000);

    // Visibility change handler: resume check when user returns to active tab
    const handleVisibilityChange = () => {
      if (!document.hidden && isMountedRef.current) {
        fetchPrices(false, true);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      isMountedRef.current = false;
      window.clearInterval(pollInterval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchPrices]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    setActiveSearch(searchInput.trim());
  };

  const handleSearchClear = () => {
    setSearchInput('');
    setActiveSearch('');
    setCurrentPage(1);
  };

  const handleDistrictChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDistrictFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleCommodityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCommodityFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleManualRefresh = () => {
    fetchPrices(true, false);
  };

  // Compile available districts dynamically
  const availableDistricts = useMemo(() => {
    const list = new Set<string>(['All']);
    if (dynamicDistricts && dynamicDistricts.length > 0) {
      dynamicDistricts.forEach((d) => list.add(d));
    }
    DEFAULT_DISTRICTS.forEach((d) => list.add(d));
    if (marketData?.availableDistricts) {
      marketData.availableDistricts.forEach((d) => list.add(d));
    }
    return Array.from(list);
  }, [marketData?.availableDistricts, dynamicDistricts]);

  // Compile available commodities dynamically
  const availableCommodities = useMemo(() => {
    const list = new Set<string>(['All']);
    if (marketData?.availableCommodities) {
      marketData.availableCommodities.forEach((c) => list.add(c));
    }
    return Array.from(list);
  }, [marketData?.availableCommodities]);

  const pagination = marketData?.pagination;
  const isLive = Boolean(marketData?.isLive);
  const isStale = Boolean(marketData?.isStale || !marketData?.sourceConfigured);
  const hasNewData = marketData?.hasNewData;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <Card
        title={t.nav.market}
        subtitle={
          language === 'ta'
            ? 'ஒழுங்குமுறை விற்பனைக் கூடங்கள் மற்றும் நேரடி நெல் கொள்முதல் நிலைய தினசரி சந்தை நிலவரம்'
            : 'Tamil Nadu Regulated Market Yards & DPC Procurement Daily Commodity Rates'
        }
        icon={<TrendingUp className="w-5 h-5 text-amber-600" />}
        headerAction={
          isLive ? (
            <Badge variant="emerald" dot>
              {language === 'ta' ? 'அரசு நேரடித் தரவு (AGMARKNET)' : 'Government Data (AGMARKNET Live)'}
            </Badge>
          ) : (
            <Badge variant="amber" dot>
              {language === 'ta' ? 'அரசு தரவு (ஆவணக் காப்பகம்)' : 'Government Data (AGMARKNET Archive)'}
            </Badge>
          )
        }
      >
        <div className="space-y-5">
          {/* Transparent Government Source & Non-Live / Stale Notice */}
          {isStale && (
            <div className="p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <p className="font-bold">
                    {language === 'ta'
                      ? 'அரசு ஆவணக் காப்பகத் தரவு அறிவிப்பு (நேரடித் தரவு அல்ல)'
                      : 'Official Government Cached Mandi Records (Non-Live Notice)'}
                  </p>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-200/70 text-amber-900 font-semibold">
                    {marketData?.sourceStatus || 'STALE_CACHE'}
                  </span>
                </div>
                <p className="text-[11px] text-amber-800/90 mt-1 leading-relaxed">
                  {language === 'ta'
                    ? marketData?.staleNoticeTa ||
                      `data.gov.in தளத்திலிருந்து பெறப்பட்ட அரசு ஆவணக் குறிப்புகள் காட்டப்படுகின்றன (சந்தை வரத்து தேதி: ${marketData?.sourceArrivalDate || '18 Oct 2026'}). நேரடி அரசு சேவையகம் தற்காலிகமாக தாமதமாகிறது.`
                    : marketData?.staleNoticeEn ||
                      `Displaying authenticated cached government records from data.gov.in (Source Arrival Date: ${marketData?.sourceArrivalDate || '18 Oct 2026'}). Live sync is operating in cached mode.`}
                </p>
                {marketData?.error && (
                  <p className="text-[10px] text-amber-950 font-mono mt-1 bg-amber-100/70 px-2 py-1 rounded-md">
                    <span className="font-semibold">{language === 'ta' ? 'சேவை நிலை:' : 'Gateway note:'}</span>{' '}
                    {marketData.error}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Sync Status / "No New Market Data" Notice */}
          {marketData && isLive && (
            <div className="flex items-center justify-between gap-3 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs flex-wrap">
              <div className="flex items-center gap-2">
                <CheckCircle2 className={`w-4 h-4 ${hasNewData ? 'text-emerald-600' : 'text-slate-500'}`} />
                <span className="font-semibold text-slate-800">
                  {hasNewData
                    ? language === 'ta'
                      ? 'அரசு தளத்திலிருந்து புதிய சந்தை நிலவரம் புதுப்பிக்கப்பட்டது'
                      : 'Updated with newly published market records'
                    : language === 'ta'
                    ? 'புதிய சந்தை வரத்து இல்லை (அரசு பதிவுகள் புதுப்பிக்கப்பட்டுள்ளன)'
                    : 'No new market data (Government records are up to date)'}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                <span className="flex items-center gap-1">
                  <Timer className="w-3 h-3 text-slate-400" />
                  {language === 'ta'
                    ? `அரசு சரிபார்ப்பு: ${marketData.refreshIntervalMinutes || 15} நிமிடங்களுக்கு ஒருமுறை`
                    : `Govt sync cycle: Every ${marketData.refreshIntervalMinutes || 15}m`}
                </span>
                <span className="hidden sm:inline text-slate-300">|</span>
                <span className="hidden sm:inline">
                  {language === 'ta' ? 'பக்க புதுப்பிப்பு: 60 விநாடிகள்' : 'Page auto-refresh: 60s'}
                </span>
              </div>
            </div>
          )}

          {/* Search & Dynamic Filter Controls */}
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200/90 rounded-2xl">
            {/* Search Input Form */}
            <form onSubmit={handleSearchSubmit} className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder={
                  language === 'ta'
                    ? 'பயிர், வகை அல்லது விற்பனைக் கூடத்தை தேடுக...'
                    : 'Search commodity, variety, or mandi yard...'
                }
                className="w-full pl-10 pr-16 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
              {searchInput && (
                <button
                  type="button"
                  onClick={handleSearchClear}
                  className="absolute right-3 top-2.5 text-[11px] font-bold text-slate-400 hover:text-slate-600"
                >
                  {language === 'ta' ? 'அழி' : 'Clear'}
                </button>
              )}
            </form>

            {/* Filter Dropdowns and Refresh Button */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Commodity Filter */}
              <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-2.5 py-1">
                <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <select
                  value={commodityFilter}
                  onChange={handleCommodityChange}
                  className="bg-transparent border-none text-xs font-bold text-slate-700 focus:ring-0 focus:outline-none cursor-pointer max-w-[150px] truncate"
                  title="Filter by Commodity"
                >
                  {availableCommodities.map((c) => (
                    <option key={c} value={c}>
                      {c === 'All' ? (language === 'ta' ? 'அனைத்து பயிர்கள்' : 'All Crops') : c}
                    </option>
                  ))}
                </select>
              </div>

              {/* District Filter */}
              <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-2.5 py-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <select
                  value={districtFilter}
                  onChange={handleDistrictChange}
                  className="bg-transparent border-none text-xs font-bold text-slate-700 focus:ring-0 focus:outline-none cursor-pointer max-w-[140px] truncate"
                  title="Filter by District"
                >
                  {availableDistricts.map((d) => (
                    <option key={d} value={d}>
                      {d === 'All' ? (language === 'ta' ? 'அனைத்து மாவட்டங்கள்' : 'All Districts') : d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Refresh Button */}
              <button
                type="button"
                onClick={handleManualRefresh}
                disabled={refreshing || loading}
                className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 shadow-2xs transition-all disabled:opacity-50 flex items-center gap-1 text-xs font-bold"
                title="Force check data.gov.in for updates"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-emerald-600' : ''}`} />
                <span className="hidden sm:inline">
                  {refreshing ? (language === 'ta' ? 'சரிபார்க்கிறது...' : 'Checking...') : language === 'ta' ? 'புதுப்பி' : 'Refresh'}
                </span>
              </button>
            </div>
          </div>

          {/* Official Source & Distinct Timestamps Banner */}
          {marketData && (
            <div className="px-4 py-2.5 bg-white rounded-xl border border-slate-200/90 text-[11px] text-slate-600 flex flex-col md:flex-row items-start md:items-center justify-between gap-2 shadow-2xs">
              {/* Left: Source Attribution */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <Building2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span className="font-bold text-slate-800">
                  {language === 'ta' ? 'அரசு மூலம்:' : 'Government Source:'}
                </span>
                <span className="text-slate-600 font-medium">
                  {marketData.dataSource}
                </span>
                {marketData.sourceUrl && (
                  <a
                    href={marketData.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 text-emerald-700 hover:text-emerald-800 font-semibold underline ml-1"
                    title="View official portal dataset"
                  >
                    data.gov.in
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {/* Right: Distinct Arrival Date & Last Checked Timestamps */}
              <div className="flex items-center gap-3 font-mono text-[10px] text-slate-500 flex-wrap">
                <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                  <Calendar className="w-3 h-3 text-emerald-600" />
                  <strong className="text-slate-700">
                    {language === 'ta' ? 'சந்தை வரத்து:' : 'Source Arrival:'}
                  </strong>{' '}
                  {marketData.sourceArrivalDate || '18 Oct 2026'}
                </span>
                <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <strong className="text-slate-700">
                    {language === 'ta' ? 'சரிபார்க்கப்பட்டது:' : 'Last Checked:'}
                  </strong>{' '}
                  {marketData.lastCheckedTime || 'IST'}
                </span>
              </div>
            </div>
          )}

          {/* Table Container */}
          {loading ? (
            <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-2" />
              <p className="text-xs font-semibold text-slate-700">
                {language === 'ta'
                  ? 'அரசு சந்தை நிலவரத் தரவுகள் பெறப்படுகின்றன...'
                  : 'Fetching authenticated government mandi records...'}
              </p>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center space-y-2">
              <p className="font-bold">{error}</p>
              <button
                type="button"
                onClick={() => fetchPrices(false, false)}
                className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700 transition-colors"
              >
                {language === 'ta' ? 'மீண்டும் முயற்சி செய்க' : 'Try Again'}
              </button>
            </div>
          ) : marketData?.commodities && marketData.commodities.length > 0 ? (
            <div className="space-y-3">
              <div className="overflow-x-auto rounded-2xl border border-slate-200/90 shadow-2xs bg-white">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/90 text-slate-600 uppercase font-bold tracking-wider text-[10px]">
                      <th className="py-3 px-4">{language === 'ta' ? 'பயிர் / விளைபொருள்' : 'Crop / Commodity'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'வகை / தரம்' : 'Variety & Grade'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'விற்பனைக் கூடம் & மாவட்டம்' : 'Mandi Yard & District'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'வரத்து தேதி' : 'Arrival Date'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'மாதிரி விலை (Modal)' : 'Modal Price'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'குறைந்த - அதிக வரம்பு' : 'Min - Max Range'}</th>
                      <th className="py-3 px-4">{language === 'ta' ? 'போக்கு' : 'Movement'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {marketData.commodities.map((item: MarketCommodityItem) => (
                      <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                        {/* Commodity / Crop */}
                        <td className="py-3 px-4">
                          <p className="font-bold text-slate-900">{item.crop || item.commodity}</p>
                          <p className="text-[11px] text-slate-500 font-normal">
                            {item.cropTa || item.commodityTa || ''}
                          </p>
                        </td>

                        {/* Variety & Grade */}
                        <td className="py-3 px-4">
                          <p className="font-semibold text-slate-800">{item.variety || 'Common'}</p>
                          <span className="inline-block mt-0.5 text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {item.grade || 'FAQ'}
                          </span>
                        </td>

                        {/* Mandi Yard & District */}
                        <td className="py-3 px-4">
                          <p className="font-semibold text-slate-800">{item.mandi || item.market}</p>
                          <p className="text-[11px] text-slate-500">{item.district} District</p>
                        </td>

                        {/* Arrival Date (Actual source date) */}
                        <td className="py-3 px-4 whitespace-nowrap">
                          <div className="flex items-center gap-1 text-slate-700 font-medium">
                            <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span>{item.arrivalDateHuman || item.date || item.arrivalDate}</span>
                          </div>
                        </td>

                        {/* Modal Price */}
                        <td className="py-3 px-4 font-black text-slate-900 text-sm whitespace-nowrap">
                          ₹{item.modalPrice.toLocaleString()}{' '}
                          <span className="text-[10px] text-slate-400 font-normal">/{item.unit || 'Quintal'}</span>
                        </td>

                        {/* Min - Max Range */}
                        <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                          ₹{item.minPrice.toLocaleString()} - ₹{item.maxPrice.toLocaleString()}
                        </td>

                        {/* Movement / Trend */}
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 font-bold text-[11px] px-2 py-0.5 rounded-md ${
                              item.trend === 'up'
                                ? 'text-emerald-700 bg-emerald-50 border border-emerald-200'
                                : item.trend === 'down'
                                ? 'text-rose-700 bg-rose-50 border border-rose-200'
                                : 'text-slate-600 bg-slate-100 border border-slate-200'
                            }`}
                          >
                            {item.trend === 'up' && <ArrowUpRight className="w-3.5 h-3.5" />}
                            {item.trend === 'down' && <ArrowDownRight className="w-3.5 h-3.5" />}
                            {item.trend === 'steady' && <Minus className="w-3.5 h-3.5 text-slate-400" />}
                            {item.change || '₹0'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {pagination && pagination.totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-3 py-2 bg-slate-50 border border-slate-200/90 rounded-xl text-xs text-slate-600">
                  <div className="text-slate-500 font-medium">
                    {language === 'ta'
                      ? `மொத்தம் ${pagination.total} பதிவுகளில் ${
                          (pagination.page - 1) * pagination.limit + 1
                        }-${Math.min(pagination.page * pagination.limit, pagination.total)} காட்டப்படுகிறது`
                      : `Showing ${(pagination.page - 1) * pagination.limit + 1} to ${Math.min(
                          pagination.page * pagination.limit,
                          pagination.total
                        )} of ${pagination.total} government records`}
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage <= 1 || loading}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      {language === 'ta' ? 'முந்தையது' : 'Previous'}
                    </button>

                    <span className="px-2.5 py-1 font-mono text-[11px] font-bold text-slate-700 bg-white border border-slate-200 rounded-lg">
                      {currentPage} / {pagination.totalPages}
                    </span>

                    <button
                      type="button"
                      onClick={() => setCurrentPage((p) => Math.min(pagination.totalPages, p + 1))}
                      disabled={currentPage >= pagination.totalPages || loading}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      {language === 'ta' ? 'அடுத்தது' : 'Next'}
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
              <p className="text-sm font-semibold text-slate-700">
                {language === 'ta'
                  ? 'தேர்ந்தெடுக்கப்பட்ட வடிகட்டிகளுக்கு விளைபொருட்கள் ஏதும் காணப்படவில்லை.'
                  : 'No market commodities found matching current filter.'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                {language === 'ta'
                  ? 'மாவட்ட அல்லது பயிர் வடிகட்டியை மாற்றி மீண்டும் பார்க்கவும்.'
                  : 'Try selecting "All Districts" or clearing the search query.'}
              </p>
              <button
                type="button"
                onClick={() => {
                  setDistrictFilter('All');
                  setCommodityFilter('All');
                  setSearchInput('');
                  setActiveSearch('');
                  setCurrentPage(1);
                }}
                className="mt-3 px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 font-bold hover:bg-slate-200 text-xs transition-colors"
              >
                {language === 'ta' ? 'வடிகட்டிகளை மீட்டமை' : 'Reset All Filters'}
              </button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

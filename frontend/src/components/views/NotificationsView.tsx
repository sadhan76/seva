import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCircle2,
  CalendarCheck,
  Scale,
  CreditCard,
  CloudRain,
  RefreshCw,
  Loader2,
  CheckCheck,
  Smartphone,
  Clock,
  Droplets,
  Sun,
  AlertTriangle,
  Sliders,
  ShieldCheck,
  Sparkles,
  Info,
  Check,
  Radio,
  MapPin,
  Sprout,
  TrendingUp,
  TrendingDown,
  Store,
  Calendar,
  X,
  Plus,
  Percent,
} from 'lucide-react';

import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getNotificationsApi,
  markNotificationReadApi,
  markAllNotificationsReadApi,
  getSmsGatewayStatusApi,
  getNotificationPreferencesApi,
  updateNotificationPreferencesApi,
  getPushStatusApi,
  savePushSubscriptionApi,
  deletePushSubscriptionApi,
  triggerIrrigationCheckApi,
  triggerMandiCheckApi,
  type InAppNotification,
  type SMSStatusInfo,
  type NotificationPreferences,
  type PushStatusInfo,
} from '../../services/api';

export const NotificationsView: React.FC = () => {
  const { language } = useLanguage();
  const { token, user } = useAuth();

  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread' | 'irrigation' | 'market'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [smsStatus, setSmsStatus] = useState<SMSStatusInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Notification Preferences State
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    userId: '',
    rainAlerts: true,
    irrigationDemandAlerts: true,
    heatDemandAlerts: true,
    staleWeatherAlerts: true,
    adviceChangeAlerts: true,
    pushEnabled: false,
    pushConfigured: false,
    mandiPriceAlerts: true,
    mandiPriceSurgeAlerts: true,
    mandiPriceDropAlerts: true,
    mandiStaleFeedAlerts: true,
    mandiSelectedCommodities: [],
    mandiSelectedMarkets: [],
    mandiPriceThresholdPercent: 5.0,
  });
  const [isSavingPrefs, setIsSavingPrefs] = useState(false);
  const [showPreferencesCard, setShowPreferencesCard] = useState(false);
  const [prefTab, setPrefTab] = useState<'irrigation' | 'mandi'>('mandi');
  const [newCommodityInput, setNewCommodityInput] = useState('');
  const [newMarketInput, setNewMarketInput] = useState('');

  // Browser Web Push State
  const [pushStatus, setPushStatus] = useState<PushStatusInfo | null>(null);
  const [browserPermission, setBrowserPermission] = useState<NotificationPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );
  const [isRequestingPush, setIsRequestingPush] = useState(false);
  const [isTriggeringCheck, setIsTriggeringCheck] = useState(false);
  const [isTriggeringMandiCheck, setIsTriggeringMandiCheck] = useState(false);

  const popularCommodities = [
    'Paddy',
    'Tomato',
    'Onion',
    'Cotton',
    'Maize',
    'Groundnut',
    'Turmeric',
    'Chilli Red',
    'Banana',
    'Tapioca'
  ];

  const popularMarkets = Array.from(
    new Set(
      [
        user?.district,
        'Thanjavur',
        'Madurai',
        'Tiruchirappalli',
        'Coimbatore',
        'Salem',
        'Tirunelveli',
        'Erode',
        'Dindigul'
      ].filter(Boolean) as string[]
    )
  );

  const fetchAllData = async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      setErrorMsg(null);
      const items = await getNotificationsApi(token, filter === 'unread');
      setNotifications(items || []);

      // Fetch Preferences
      try {
        const prefs = await getNotificationPreferencesApi(token);
        setPreferences(prefs);
      } catch (e) {
        console.warn('Could not load preferences:', e);
      }

      // Fetch Push Status
      try {
        const ps = await getPushStatusApi(token);
        setPushStatus(ps);
      } catch (e) {
        console.warn('Could not load push status:', e);
      }

      // Fetch SMS Gateway Status
      try {
        const sms = await getSmsGatewayStatusApi(token);
        setSmsStatus(sms);
      } catch {
        // Graceful fallback
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load notifications from database.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [token, filter]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchAllData();
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationReadApi(id, token);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
      );
    } catch (err: any) {
      console.warn('Could not mark as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    if (!token) return;
    setIsMarkingAll(true);
    try {
      await markAllNotificationsReadApi(token);
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
      setSuccessMsg(language === 'ta' ? 'அனைத்து அறிவிப்புகளும் படித்ததாகக் குறிக்கப்பட்டது.' : 'All notifications marked as read.');
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to mark all notifications as read.');
    } finally {
      setIsMarkingAll(false);
    }
  };

  // Update arbitrary notification preference fields
  const handleUpdatePreferences = async (updates: Partial<NotificationPreferences>) => {
    if (!token) return;
    const merged = { ...preferences, ...updates };
    setPreferences(merged);

    setIsSavingPrefs(true);
    try {
      const saved = await updateNotificationPreferencesApi(token, updates);
      setPreferences(saved);
      setSuccessMsg(
        language === 'ta'
          ? 'அறிவிப்பு விருப்பத்தேர்வுகள் புதுப்பிக்கப்பட்டன.'
          : 'Notification preferences updated.'
      );
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update preferences.');
      // Revert from server
      fetchAllData();
    } finally {
      setIsSavingPrefs(false);
    }
  };

  // Toggle boolean preference
  const handleTogglePreference = async (key: keyof NotificationPreferences) => {
    const newVal = !preferences[key];
    await handleUpdatePreferences({ [key]: newVal });
  };

  // Commodity Chip Management
  const handleToggleCommodity = (comm: string) => {
    const current = preferences.mandiSelectedCommodities || [];
    const exists = current.some((c) => c.toLowerCase() === comm.toLowerCase());
    const updated = exists
      ? current.filter((c) => c.toLowerCase() !== comm.toLowerCase())
      : [...current, comm];
    handleUpdatePreferences({ mandiSelectedCommodities: updated });
  };

  const handleAddCustomCommodity = () => {
    if (!newCommodityInput.trim()) return;
    const comm = newCommodityInput.trim();
    const current = preferences.mandiSelectedCommodities || [];
    if (!current.some((c) => c.toLowerCase() === comm.toLowerCase())) {
      handleUpdatePreferences({ mandiSelectedCommodities: [...current, comm] });
    }
    setNewCommodityInput('');
  };

  // Market Chip Management
  const handleToggleMarket = (mkt: string) => {
    const current = preferences.mandiSelectedMarkets || [];
    const exists = current.some((m) => m.toLowerCase() === mkt.toLowerCase());
    const updated = exists
      ? current.filter((m) => m.toLowerCase() !== mkt.toLowerCase())
      : [...current, mkt];
    handleUpdatePreferences({ mandiSelectedMarkets: updated });
  };

  const handleAddCustomMarket = () => {
    if (!newMarketInput.trim()) return;
    const mkt = newMarketInput.trim();
    const current = preferences.mandiSelectedMarkets || [];
    if (!current.some((m) => m.toLowerCase() === mkt.toLowerCase())) {
      handleUpdatePreferences({ mandiSelectedMarkets: [...current, mkt] });
    }
    setNewMarketInput('');
  };

  // Explicit user-triggered permission request for browser notifications
  const handleEnableBrowserNotifications = async () => {
    if (!token) return;
    if (typeof window === 'undefined' || !('Notification' in window)) {
      setErrorMsg(
        language === 'ta'
          ? 'உங்கள் உலாவி புஷ் அறிவிப்புகளை ஆதரிக்கவில்லை.'
          : 'This browser does not support Web Push notifications.'
      );
      return;
    }

    setIsRequestingPush(true);
    setErrorMsg(null);

    try {
      // 1. Request permission strictly upon explicit user click
      const perm = await Notification.requestPermission();
      setBrowserPermission(perm);

      if (perm === 'granted') {
        // 2. Register Service Worker if supported
        if ('serviceWorker' in navigator) {
          try {
            const reg = await navigator.serviceWorker.register('/sw.js');
            await navigator.serviceWorker.ready;

            // 3. If VAPID configured, subscribe to PushManager
            if (pushStatus?.vapidPublicKey) {
              const sub = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: pushStatus.vapidPublicKey,
              });

              // Send subscription to backend
              const subJson = sub.toJSON();
              await savePushSubscriptionApi(token, {
                endpoint: sub.endpoint,
                keys: {
                  p256dh: subJson.keys?.p256dh || '',
                  auth: subJson.keys?.auth || '',
                },
                expirationTime: sub.expirationTime,
              });
            } else {
              // VAPID unconfigured in backend: persist enabled toggle
              await updateNotificationPreferencesApi(token, { pushEnabled: true });
            }
          } catch (swErr) {
            console.warn('Service worker registration note:', swErr);
          }
        }

        setPreferences((prev) => ({ ...prev, pushEnabled: true }));
        setSuccessMsg(
          language === 'ta'
            ? 'உலாவி அறிவிப்புகள் வெற்றிகரமாக இயக்கப்பட்டன!'
            : 'Browser notifications successfully enabled!'
        );
        setTimeout(() => setSuccessMsg(null), 4000);
      } else if (perm === 'denied') {
        setErrorMsg(
          language === 'ta'
            ? 'அறிவிப்பு அனுமதி மறுக்கப்பட்டது. உலாவி அமைப்புகளில் அனுமதியை மாற்றவும்.'
            : 'Notification permission was denied. Please allow notifications in browser settings.'
        );
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Error enabling notifications.');
    } finally {
      setIsRequestingPush(false);
    }
  };

  // Disable browser notifications
  const handleDisableBrowserNotifications = async () => {
    if (!token) return;
    try {
      await deletePushSubscriptionApi(token);
      setPreferences((prev) => ({ ...prev, pushEnabled: false }));
      setSuccessMsg(
        language === 'ta'
          ? 'புஷ் அறிவிப்புகள் முடக்கப்பட்டன.'
          : 'Push notifications disabled.'
      );
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to disable notifications.');
    }
  };

  // Trigger automated irrigation check on demand
  const handleTriggerIrrigationCheck = async () => {
    if (!token) return;
    setIsTriggeringCheck(true);
    try {
      const summary = await triggerIrrigationCheckApi(token);
      setSuccessMsg(
        language === 'ta'
          ? `பாசன சோதனை முடிந்தது. விவசாயிகள்: ${summary.checkedFarmers}, புதிய எச்சரிக்கைகள்: ${summary.generatedAlerts}`
          : `Irrigation check complete. Farmers checked: ${summary.checkedFarmers}, New alerts generated: ${summary.generatedAlerts}`
      );
      setTimeout(() => setSuccessMsg(null), 5000);
      fetchAllData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error triggering irrigation check.');
    } finally {
      setIsTriggeringCheck(false);
    }
  };

  // Trigger mandi price check on demand
  const handleTriggerMandiCheck = async () => {
    if (!token) return;
    setIsTriggeringMandiCheck(true);
    try {
      const res = await triggerMandiCheckApi(token);
      const summary = res.notificationSummary;
      setSuccessMsg(
        language === 'ta'
          ? `மண்டி விலை மதிப்பீடு முடிந்தது. விவசாயிகள்: ${summary?.checkedFarmers || 0}, புதிய அறிவிப்புகள்: ${summary?.generatedAlerts || 0}`
          : `Mandi price check complete. Farmers checked: ${summary?.checkedFarmers || 0}, New alerts generated: ${summary?.generatedAlerts || 0}`
      );
      setTimeout(() => setSuccessMsg(null), 5000);
      fetchAllData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error triggering mandi check.');
    } finally {
      setIsTriggeringMandiCheck(false);
    }
  };

  // Helper for notification icons and styling by category
  const getNotificationIcon = (item: InAppNotification) => {
    const eventType = item.eventType || '';
    if (eventType === 'irrigation_rain_expected') {
      return <CloudRain className="w-5 h-5 text-amber-600" />;
    }
    if (eventType === 'irrigation_needed') {
      return <Droplets className="w-5 h-5 text-blue-600" />;
    }
    if (eventType === 'irrigation_high_heat') {
      return <Sun className="w-5 h-5 text-rose-600" />;
    }
    if (eventType === 'irrigation_weather_stale') {
      return <AlertTriangle className="w-5 h-5 text-slate-600" />;
    }
    if (eventType === 'irrigation_advice_updated') {
      return <Sparkles className="w-5 h-5 text-indigo-600" />;
    }

    // Mandi Market Price Event Types
    if (eventType === 'market_price_surge') {
      return <TrendingUp className="w-5 h-5 text-emerald-600" />;
    }
    if (eventType === 'market_price_drop') {
      return <TrendingDown className="w-5 h-5 text-rose-600" />;
    }
    if (eventType === 'market_new_price') {
      return <Store className="w-5 h-5 text-blue-600" />;
    }
    if (eventType === 'market_feed_stale') {
      return <AlertTriangle className="w-5 h-5 text-amber-600" />;
    }

    switch (item.type.toLowerCase()) {
      case 'booking':
        return <CalendarCheck className="w-5 h-5 text-emerald-700" />;
      case 'queue':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'weighing':
      case 'bill':
        return <Scale className="w-5 h-5 text-purple-600" />;
      case 'payment':
        return <CreditCard className="w-5 h-5 text-emerald-600" />;
      case 'weather':
      case 'irrigation':
        return <Droplets className="w-5 h-5 text-teal-600" />;
      case 'market':
        return <Store className="w-5 h-5 text-emerald-700" />;
      default:
        return <Bell className="w-5 h-5 text-slate-600" />;
    }
  };

  const getNotificationBadge = (item: InAppNotification) => {
    const eventType = item.eventType || '';
    if (eventType === 'irrigation_rain_expected') {
      return {
        label: language === 'ta' ? 'மழை எச்சரிக்கை' : 'Rain Expected',
        color: 'bg-amber-100 text-amber-900 border border-amber-300',
      };
    }
    if (eventType === 'irrigation_needed') {
      return {
        label: language === 'ta' ? 'பாசனம் தேவை' : 'Irrigation Required',
        color: 'bg-blue-100 text-blue-900 border border-blue-300',
      };
    }
    if (eventType === 'irrigation_high_heat') {
      return {
        label: language === 'ta' ? 'அதிக வெப்ப அழுத்தம்' : 'High Heat Demand',
        color: 'bg-rose-100 text-rose-900 border border-rose-300',
      };
    }
    if (eventType === 'irrigation_weather_stale') {
      return {
        label: language === 'ta' ? 'வானிலை சேவை நிலை' : 'Weather Feed Notice',
        color: 'bg-slate-100 text-slate-800 border border-slate-300',
      };
    }
    if (eventType === 'irrigation_advice_updated') {
      return {
        label: language === 'ta' ? 'ஆலோசனை மாற்றம்' : 'Advice Transition',
        color: 'bg-indigo-100 text-indigo-900 border border-indigo-300',
      };
    }

    // Mandi Badges
    if (eventType === 'market_price_surge') {
      return {
        label: language === 'ta' ? 'மண்டி விலை உயர்வு' : 'Mandi Price Surge',
        color: 'bg-emerald-100 text-emerald-900 border border-emerald-300',
      };
    }
    if (eventType === 'market_price_drop') {
      return {
        label: language === 'ta' ? 'மண்டி விலை சரிவு' : 'Mandi Price Drop',
        color: 'bg-rose-100 text-rose-900 border border-rose-300',
      };
    }
    if (eventType === 'market_new_price') {
      return {
        label: language === 'ta' ? 'புதிய மண்டி விலை' : 'New Mandi Price',
        color: 'bg-blue-100 text-blue-900 border border-blue-300',
      };
    }
    if (eventType === 'market_feed_stale') {
      return {
        label: language === 'ta' ? 'மண்டி சேவை நிலை' : 'Mandi Feed Notice',
        color: 'bg-amber-100 text-amber-900 border border-amber-300',
      };
    }

    switch (item.type.toLowerCase()) {
      case 'booking':
        return { label: language === 'ta' ? 'முன்பதிவு' : 'Booking', color: 'bg-emerald-100 text-emerald-800' };
      case 'queue':
        return { label: language === 'ta' ? 'வரிசை' : 'Queue', color: 'bg-blue-100 text-blue-800' };
      case 'weighing':
      case 'bill':
        return { label: language === 'ta' ? 'எடையிடல் / பில்' : 'Weighment & Bill', color: 'bg-purple-100 text-purple-800' };
      case 'payment':
        return { label: language === 'ta' ? 'வங்கி DBT' : 'PFMS Payment', color: 'bg-emerald-100 text-emerald-800' };
      case 'irrigation':
        return { label: language === 'ta' ? 'பாசன எச்சரிக்கை' : 'Irrigation Alert', color: 'bg-teal-100 text-teal-800' };
      case 'market':
        return { label: language === 'ta' ? 'மண்டி விலை' : 'Mandi Price', color: 'bg-emerald-100 text-emerald-800' };
      default:
        return { label: language === 'ta' ? 'அறிவிப்பு' : 'General', color: 'bg-slate-100 text-slate-700' };
    }
  };

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread') return !n.isRead;
    if (filter === 'irrigation') return n.type === 'irrigation' || (n.eventType && n.eventType.startsWith('irrigation_'));
    if (filter === 'market') return n.type === 'market' || (n.eventType && n.eventType.startsWith('market_'));
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.isRead).length;
  const irrigationAlertsCount = notifications.filter(
    (n) => n.type === 'irrigation' || (n.eventType && n.eventType.startsWith('irrigation_'))
  ).length;
  const marketAlertsCount = notifications.filter(
    (n) => n.type === 'market' || (n.eventType && n.eventType.startsWith('market_'))
  ).length;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shrink-0">
              <Bell className="w-7 h-7 text-emerald-300" />
            </div>
            <div>
              <span className="text-[11px] font-mono tracking-wider uppercase text-emerald-300 font-bold">
                {language === 'ta' ? 'அதிகாரப்பூர்வ அறிவிப்புகள் மையம்' : 'Official Notifications Center'}
              </span>
              <h2 className="text-2xl font-black mt-0.5">
                {language === 'ta' ? 'பாசன எச்சரிக்கைகள் & அறிவிப்புகள்' : 'Smart Irrigation & Mandi Alerts'}
              </h2>
              <p className="text-xs text-emerald-100/90 mt-1">
                {language === 'ta'
                  ? 'மழை எச்சரிக்கை, மண் ஈரப்பதம் குறைவு, தீவிர வெப்பம் மற்றும் நெல் கொள்முதல் நிலை'
                  : 'Agronomic water-balance advisories, rain forecasts, heat stress alerts, and mandi status'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            <button
              onClick={() => setShowPreferencesCard(!showPreferencesCard)}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5 text-emerald-300" />
              {language === 'ta' ? 'விருப்பத்தேர்வுகள்' : 'Preferences'}
            </button>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              {language === 'ta' ? 'புதுப்பி' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {/* Success / Error Messages */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-2xl flex items-center gap-2 shadow-xs">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-2xl flex items-center gap-2 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Browser Notification & Push Settings Card */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center shrink-0">
              <Radio className="w-5 h-5 text-teal-700" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">
                {language === 'ta' ? 'உலாவி புஷ் அறிவிப்புகள்' : 'Browser Push Notifications'}
              </h3>
              <p className="text-[11px] text-slate-500">
                {language === 'ta'
                  ? 'பக்கம் மூடப்பட்டிருக்கும் போது எச்சரிக்கைகளைப் பெறவும்'
                  : 'Receive real-time irrigation and rain alerts directly on your device'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {preferences.pushEnabled ? (
              <button
                onClick={handleDisableBrowserNotifications}
                className="px-3.5 py-1.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold transition-colors"
              >
                {language === 'ta' ? 'முடக்கு' : 'Disable Push'}
              </button>
            ) : (
              <button
                onClick={handleEnableBrowserNotifications}
                disabled={isRequestingPush}
                className="px-4 py-2 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold flex items-center gap-1.5 transition-colors shadow-sm"
              >
                {isRequestingPush ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Bell className="w-3.5 h-3.5" />
                )}
                {language === 'ta' ? 'அறிவிப்புகளை இயக்கு' : 'Enable Notifications'}
              </button>
            )}

            <button
              onClick={handleTriggerIrrigationCheck}
              disabled={isTriggeringCheck}
              title={language === 'ta' ? 'உடனடி பாசன சோதனை' : 'Test Scheduled Irrigation Check'}
              className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              {isTriggeringCheck ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              )}
              {language === 'ta' ? 'பாசன சோதனை' : 'Test Irrigation'}
            </button>

            <button
              onClick={handleTriggerMandiCheck}
              disabled={isTriggeringMandiCheck}
              title={language === 'ta' ? 'உடனடி மண்டி விலை மதிப்பீடு' : 'Test Mandi Price Evaluation'}
              className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              {isTriggeringMandiCheck ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600" />
              ) : (
                <Store className="w-3.5 h-3.5 text-teal-600" />
              )}
              {language === 'ta' ? 'மண்டி சோதனை' : 'Check Mandi'}
            </button>
          </div>
        </div>

        {/* Honest Push Status Banner */}
        <div
          className={`p-4 rounded-2xl text-xs space-y-1.5 border ${
            pushStatus?.pushConfigured
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
              : 'bg-amber-50/70 border-amber-200 text-amber-900'
          }`}
        >
          <div className="flex items-center gap-2 font-bold text-xs">
            <ShieldCheck
              className={`w-4 h-4 ${
                pushStatus?.pushConfigured ? 'text-emerald-700' : 'text-amber-700'
              }`}
            />
            <span>
              {pushStatus?.pushConfigured
                ? language === 'ta'
                  ? 'Web Push சேவை இயங்குகிறது (பின்னணி அறிவிப்புகள் தயார்)'
                  : 'Web Push Gateway Operational (Background Alerts Active)'
                : language === 'ta'
                ? 'நேரடி ஆப் அறிவிப்புகள் இயக்கத்தில் உள்ளன (இன்-ஆப் பயன்முறை)'
                : 'In-App Alerts Active (Web Push in Offline/Local Mode)'}
            </span>
          </div>

          <p className="text-[11px] leading-relaxed text-slate-700">
            {pushStatus?.note ||
              (language === 'ta'
                ? 'அனைத்து பாசன மற்றும் நெல் கொள்முதல் அறிவிப்புகளும் தரவுத்தளத்தில் சேமிக்கப்பட்டு ஆப் மூலம் உடனடியாக வழங்கப்படுகின்றன.'
                : 'All agricultural advisories and procurement notifications are persisted in MongoDB and updated in real-time in your app and notification bell.')}
          </p>

          <div className="flex items-center gap-4 text-[10px] text-slate-500 font-mono pt-1">
            <span>
              Permission: <strong>{browserPermission}</strong>
            </span>
            <span>
              In-App: <strong>ACTIVE</strong>
            </span>
            <span>
              Background Web Push:{' '}
              <strong>{pushStatus?.pushConfigured ? 'CONFIGURED' : 'UNCONFIGURED (SAFE)'}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Notification Preferences Drawer / Accordion */}
      {showPreferencesCard && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4 animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-emerald-700" />
              <div>
                <h3 className="text-sm font-bold text-slate-800">
                  {language === 'ta'
                    ? 'விவசாய & பாசன எச்சரிக்கை விருப்பத்தேர்வுகள்'
                    : 'Smart Irrigation Notification Preferences'}
                </h3>
                <p className="text-[11px] text-slate-500">
                  {language === 'ta'
                    ? 'தேவையான எச்சரிக்கை வகைகளை ஆன்/ஆஃப் செய்யவும் (24 மணி நேரத்தில் அதிகபட்சம் 4)'
                    : 'Configure which agronomic notifications you wish to receive (Rate limit: max 4/day)'}
                </p>
              </div>
            </div>

            {isSavingPrefs && (
              <span className="text-xs text-emerald-700 flex items-center gap-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {language === 'ta' ? 'சேமிக்கிறது...' : 'Saving...'}
              </span>
            )}
          </div>

          {/* Preference Tabs: Irrigation vs Mandi Market */}
          <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
            <button
              onClick={() => setPrefTab('mandi')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                prefTab === 'mandi'
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Store className="w-3.5 h-3.5" />
              {language === 'ta' ? 'மண்டி விலை எச்சரிக்கைகள்' : 'Mandi Market Prices'}
            </button>
            <button
              onClick={() => setPrefTab('irrigation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                prefTab === 'irrigation'
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Droplets className="w-3.5 h-3.5" />
              {language === 'ta' ? 'பாசனம் & வானிலை' : 'Irrigation & Weather'}
            </button>
          </div>

          {/* TAB 1: MANDI MARKET PRICE PREFERENCES */}
          {prefTab === 'mandi' && (
            <div className="space-y-4 pt-1">
              {/* Master Mandi Toggle */}
              <div
                onClick={() => handleTogglePreference('mandiPriceAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                  preferences.mandiPriceAlerts !== false
                    ? 'bg-emerald-50/80 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                    <Store className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">
                      {language === 'ta' ? 'மண்டி விலை எச்சரிக்கைகள் (முதன்மை)' : 'Mandi Market Price Alerts (Master)'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'அரசு AGMARKNET மண்டி விலை மாற்றங்கள் மற்றும் புதிய வரத்து தகவல்கள்'
                        : 'Enable verified price movement and arrival alerts from official AGMARKNET mandis'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.mandiPriceAlerts !== false ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>

              {/* Sub Toggles Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Surge Toggle */}
                <div
                  onClick={() => handleTogglePreference('mandiPriceSurgeAlerts')}
                  className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                    preferences.mandiPriceSurgeAlerts !== false
                      ? 'bg-emerald-50/60 border-emerald-300'
                      : 'bg-slate-50 border-slate-200 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-[11px] font-bold text-slate-800">
                        {language === 'ta' ? 'விலை உயர்வு' : 'Price Surge'}
                      </h5>
                      <p className="text-[9px] text-slate-500">
                        {language === 'ta' ? `+${preferences.mandiPriceThresholdPercent || 5}% மேல்` : `Increases ≥ ${preferences.mandiPriceThresholdPercent || 5}%`}
                      </p>
                    </div>
                  </div>
                  <div
                    className={`w-8 h-5 rounded-full transition-colors flex items-center p-0.5 ${
                      preferences.mandiPriceSurgeAlerts !== false ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow-xs" />
                  </div>
                </div>

                {/* Drop Toggle */}
                <div
                  onClick={() => handleTogglePreference('mandiPriceDropAlerts')}
                  className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                    preferences.mandiPriceDropAlerts !== false
                      ? 'bg-emerald-50/60 border-emerald-300'
                      : 'bg-slate-50 border-slate-200 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                      <TrendingDown className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-[11px] font-bold text-slate-800">
                        {language === 'ta' ? 'விலை சரிவு' : 'Price Drop'}
                      </h5>
                      <p className="text-[9px] text-slate-500">
                        {language === 'ta' ? `-${preferences.mandiPriceThresholdPercent || 5}% மேல்` : `Decreases ≥ ${preferences.mandiPriceThresholdPercent || 5}%`}
                      </p>
                    </div>
                  </div>
                  <div
                    className={`w-8 h-5 rounded-full transition-colors flex items-center p-0.5 ${
                      preferences.mandiPriceDropAlerts !== false ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow-xs" />
                  </div>
                </div>

                {/* Stale Feed Toggle */}
                <div
                  onClick={() => handleTogglePreference('mandiStaleFeedAlerts')}
                  className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                    preferences.mandiStaleFeedAlerts !== false
                      ? 'bg-emerald-50/60 border-emerald-300'
                      : 'bg-slate-50 border-slate-200 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-[11px] font-bold text-slate-800">
                        {language === 'ta' ? 'சேவை நிலை' : 'Feed Notice'}
                      </h5>
                      <p className="text-[9px] text-slate-500">
                        {language === 'ta' ? 'தரவு தாமதமானால்' : 'When feed is delayed'}
                      </p>
                    </div>
                  </div>
                  <div
                    className={`w-8 h-5 rounded-full transition-colors flex items-center p-0.5 ${
                      preferences.mandiStaleFeedAlerts !== false ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow-xs" />
                  </div>
                </div>
              </div>

              {/* Threshold Slider / Input */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Percent className="w-4 h-4 text-emerald-700" />
                    <span className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'விலை மாற்ற வரம்பு சதவீதம் (%)' : 'Price Change Alert Threshold (%)'}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    ±{preferences.mandiPriceThresholdPercent || 5.0}%
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="1"
                    max="25"
                    step="0.5"
                    value={preferences.mandiPriceThresholdPercent || 5.0}
                    onChange={(e) => handleUpdatePreferences({ mandiPriceThresholdPercent: parseFloat(e.target.value) })}
                    className="flex-1 accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                  />
                  <span className="text-[10px] text-slate-400 font-mono">1% - 25%</span>
                </div>
                <p className="text-[10px] text-slate-500">
                  {language === 'ta'
                    ? 'இந்த சதவீதத்திற்கு மேல் விலை கூடும்போதோ அல்லது குறையும்போதோ மட்டும் எச்சரிக்கப்படும் (வீண் எச்சரிக்கைகளைத் தவிர்க்க).'
                    : 'Alerts trigger only when modal auction price changes by at least this percentage to avoid alert fatigue.'}
                </p>
              </div>

              {/* Selected Crops (Commodities) Filter */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Sprout className="w-4 h-4 text-emerald-700" />
                    <span className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'கண்காணிக்கப்படும் பயிர்கள்' : 'Selected Crops (Commodities)'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {(preferences.mandiSelectedCommodities?.length || 0) === 0
                      ? language === 'ta' ? '(அனைத்து பயிர்களும்)' : '(All crops in district)'
                      : `${preferences.mandiSelectedCommodities?.length} selected`}
                  </span>
                </div>

                {/* Selected Chips */}
                {(preferences.mandiSelectedCommodities?.length || 0) > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {preferences.mandiSelectedCommodities?.map((comm) => (
                      <span
                        key={comm}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-900 border border-emerald-300 text-[11px] font-bold"
                      >
                        {comm}
                        <button
                          onClick={() => handleToggleCommodity(comm)}
                          className="hover:text-rose-700"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Quick Add Popular Crops */}
                <div className="space-y-1.5">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                    {language === 'ta' ? 'விரைவு தேர்வு:' : 'Quick Select:'}
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {popularCommodities.map((comm) => {
                      const isSelected = preferences.mandiSelectedCommodities?.some(
                        (c) => c.toLowerCase() === comm.toLowerCase()
                      );
                      return (
                        <button
                          key={comm}
                          onClick={() => handleToggleCommodity(comm)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-medium border transition-all ${
                            isSelected
                              ? 'bg-emerald-700 text-white border-emerald-700 shadow-2xs'
                              : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          {isSelected ? '✓ ' : '+ '}
                          {comm}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Commodity Input */}
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newCommodityInput}
                    onChange={(e) => setNewCommodityInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCustomCommodity()}
                    placeholder={language === 'ta' ? 'வேறு பயிரைச் சேர்க்கவும்...' : 'Add other crop (e.g. Ginger)...'}
                    className="flex-1 px-3 py-1.5 rounded-xl border border-slate-200 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                  <button
                    onClick={handleAddCustomCommodity}
                    disabled={!newCommodityInput.trim()}
                    className="px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    {language === 'ta' ? 'சேர்' : 'Add'}
                  </button>
                </div>
              </div>

              {/* Selected Markets Filter */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-700" />
                    <span className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'கண்காணிக்கப்படும் மண்டிகள் / சந்தைகள்' : 'Selected Regulated Mandis'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {(preferences.mandiSelectedMarkets?.length || 0) === 0
                      ? language === 'ta' ? '(அனைத்து மண்டிகளும்)' : '(All regulated mandis in TN)'
                      : `${preferences.mandiSelectedMarkets?.length} selected`}
                  </span>
                </div>

                {/* Selected Markets Chips */}
                {(preferences.mandiSelectedMarkets?.length || 0) > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {preferences.mandiSelectedMarkets?.map((mkt) => (
                      <span
                        key={mkt}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-teal-100 text-teal-900 border border-teal-300 text-[11px] font-bold"
                      >
                        {mkt}
                        <button
                          onClick={() => handleToggleMarket(mkt)}
                          className="hover:text-rose-700"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Quick Add Popular Markets */}
                <div className="space-y-1.5">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                    {language === 'ta' ? 'விரைவு தேர்வு:' : 'Quick Select:'}
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {popularMarkets.map((mkt) => {
                      const isSelected = preferences.mandiSelectedMarkets?.some(
                        (m) => m.toLowerCase() === mkt.toLowerCase()
                      );
                      return (
                        <button
                          key={mkt}
                          onClick={() => handleToggleMarket(mkt)}
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-medium border transition-all ${
                            isSelected
                              ? 'bg-teal-700 text-white border-teal-700 shadow-2xs'
                              : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          {isSelected ? '✓ ' : '+ '}
                          {mkt}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Market Input */}
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newMarketInput}
                    onChange={(e) => setNewMarketInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCustomMarket()}
                    placeholder={language === 'ta' ? 'வேறு மண்டியைச் சேர்க்கவும்...' : 'Add other market (e.g. Pollachi)...'}
                    className="flex-1 px-3 py-1.5 rounded-xl border border-slate-200 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                  <button
                    onClick={handleAddCustomMarket}
                    disabled={!newMarketInput.trim()}
                    className="px-3 py-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    {language === 'ta' ? 'சேர்' : 'Add'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: IRRIGATION & AGRONOMIC PREFERENCES */}
          {prefTab === 'irrigation' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              {/* Preference Item 1: Rain */}
              <div
                onClick={() => handleTogglePreference('rainAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                  preferences.rainAlerts
                    ? 'bg-emerald-50/60 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                    <CloudRain className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'மழை எச்சரிக்கை' : 'Rain Expected Soon'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'மழை எதிர்பார்க்கப்படும் போது பாசனத்தை தள்ளிப்போட'
                        : 'Reassess irrigation when rain chance ≥ 60%'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.rainAlerts ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>

              {/* Preference Item 2: Deficit */}
              <div
                onClick={() => handleTogglePreference('irrigationDemandAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                  preferences.irrigationDemandAlerts
                    ? 'bg-emerald-50/60 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                    <Droplets className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'பாசன தேவை எச்சரிக்கை' : 'Irrigation Required Alert'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'மண் ஈரப்பதம் குறைவாக உள்ளபோது எச்சரிக்க'
                        : 'When root-zone moisture drops below threshold'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.irrigationDemandAlerts ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>

              {/* Preference Item 3: Heat */}
              <div
                onClick={() => handleTogglePreference('heatDemandAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                  preferences.heatDemandAlerts
                    ? 'bg-emerald-50/60 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                    <Sun className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'அதிக வெப்ப அழுத்தம்' : 'High Heat & Transpiration'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'வெப்பம் ≥ 38°C அல்லது ஆவியாதல் அதிகம் உள்ளபோது'
                        : 'Triggered when temp ≥ 38°C or ET₀ ≥ 6.5 mm/day'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.heatDemandAlerts ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>

              {/* Preference Item 4: Stale */}
              <div
                onClick={() => handleTogglePreference('staleWeatherAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                  preferences.staleWeatherAlerts
                    ? 'bg-emerald-50/60 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                    <Info className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'வானிலை சேவை நிலை' : 'Weather Feed Status'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'வானிலை சேவை கிடைக்காத போது தகவல் அறிவிப்பு'
                        : 'Non-alarming notice when satellite feed is stale'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.staleWeatherAlerts ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>

              {/* Preference Item 5: Advice Transition */}
              <div
                onClick={() => handleTogglePreference('adviceChangeAlerts')}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 md:col-span-2 ${
                  preferences.adviceChangeAlerts
                    ? 'bg-emerald-50/60 border-emerald-300'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">
                      {language === 'ta' ? 'பாசன ஆலோசனை மாற்றங்கள்' : 'Updated Irrigation Advice'}
                    </h4>
                    <p className="text-[10px] text-slate-500">
                      {language === 'ta'
                        ? 'பரிந்துரை அர்த்தமுள்ள வகையில் மாறும்போது மட்டும் (உதா: தள்ளிப்போடு ➔ பாசனம் செய்)'
                        : 'Generated ONLY when recommendation meaningfully transitions (e.g. Delay ➔ Irrigate Now)'}
                    </p>
                  </div>
                </div>
                <div
                  className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 ${
                    preferences.adviceChangeAlerts ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Notifications Card */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        {/* Filters and Mark all as read */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                filter === 'all'
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {language === 'ta' ? 'அனைத்தும்' : 'All Alerts'} ({notifications.length})
            </button>
            <button
              onClick={() => setFilter('market')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 ${
                filter === 'market'
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Store className="w-3 h-3" />
              {language === 'ta' ? 'மண்டி விலைகள்' : 'Mandi Prices'} ({marketAlertsCount})
            </button>
            <button
              onClick={() => setFilter('irrigation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 ${
                filter === 'irrigation'
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Droplets className="w-3 h-3" />
              {language === 'ta' ? 'பாசனம்' : 'Irrigation'} ({irrigationAlertsCount})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                filter === 'unread'
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {language === 'ta' ? 'படிக்காதவை' : 'Unread'} ({unreadCount})
            </button>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              disabled={isMarkingAll}
              className="self-start sm:self-auto px-3.5 py-1.5 rounded-xl border border-slate-200 hover:bg-emerald-50 text-emerald-800 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              {isMarkingAll ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <CheckCheck className="w-3.5 h-3.5 text-emerald-700" />
              )}
              {language === 'ta' ? 'அனைத்தையும் படித்ததாகக் குறி' : 'Mark All as Read'}
            </button>
          )}
        </div>

        {/* Notifications List */}
        {isLoading ? (
          <div className="py-16 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
            {language === 'ta'
              ? 'அறிவிப்புகள் தரவுத்தளத்திலிருந்து பெறப்படுகின்றன...'
              : 'Loading live notifications from database...'}
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-400 space-y-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <Bell className="w-6 h-6" />
            </div>
            <p className="font-semibold text-slate-700">
              {language === 'ta' ? 'அறிவிப்புகள் எதுவும் இல்லை' : 'No notifications found in this view'}
            </p>
            <p className="text-[11px] max-w-md mx-auto">
              {language === 'ta'
                ? 'பாசன வானிலை மாற்றங்கள் மற்றும் நெல் கொள்முதல் நிலை மாற்றங்களின் போது இங்கு எச்சரிக்கைகள் தானாகவே தோன்றும்.'
                : 'Alerts appear here automatically when agricultural weather triggers an advisory or when mandi staff updates your queue.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredNotifications.map((item) => {
              const badge = getNotificationBadge(item);
              const title = language === 'ta' && item.titleTa ? item.titleTa : item.title;
              const message = language === 'ta' && item.messageTa ? item.messageTa : item.message;

              return (
                <div
                  key={item.id}
                  onClick={() => !item.isRead && handleMarkAsRead(item.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start gap-4 ${
                    item.isRead
                      ? 'bg-white border-slate-200 hover:bg-slate-50/70'
                      : 'bg-emerald-50/40 border-emerald-300 shadow-xs ring-1 ring-emerald-500/10'
                  }`}
                >
                  {/* Icon Avatar */}
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      item.isRead ? 'bg-slate-100' : 'bg-emerald-100'
                    }`}
                  >
                    {getNotificationIcon(item)}
                  </div>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${badge.color}`}>
                          {badge.label}
                        </span>
                        {!item.isRead && (
                          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                        )}
                        <h4
                          className={`text-xs sm:text-sm font-bold ${
                            item.isRead ? 'text-slate-800' : 'text-emerald-950 font-black'
                          }`}
                        >
                          {title}
                        </h4>
                      </div>

                      <span className="text-[10px] text-slate-400 font-mono">
                        {item.createdAt}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {message}
                    </p>

                    {/* Rich Agronomic / Mandi Details Footer */}
                    <div className="flex items-center gap-3 flex-wrap mt-2 pt-2 border-t border-slate-100/80 text-[11px] text-slate-500">
                      {/* Mandi Yard & District */}
                      {item.market && (
                        <div className="flex items-center gap-1 text-[10px] text-slate-700 bg-slate-100 px-2 py-0.5 rounded font-medium">
                          <MapPin className="w-3 h-3 text-emerald-600" />
                          <span>{item.market} {item.district ? `(${item.district})` : ''}</span>
                        </div>
                      )}

                      {/* Mandi Commodity & Variety */}
                      {item.commodity && (
                        <div className="flex items-center gap-1 text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-medium">
                          <Sprout className="w-3 h-3 text-emerald-600" />
                          <span>
                            {language === 'ta' && item.commodityTa ? item.commodityTa : item.commodity}
                            {item.variety ? ` • ${item.variety}` : ''}
                          </span>
                        </div>
                      )}

                      {/* Price badges */}
                      {item.newPrice !== undefined && item.newPrice !== null && (
                        <div className="flex items-center gap-1.5 text-[10px] bg-slate-50 border border-slate-200 px-2 py-0.5 rounded font-mono font-bold text-slate-800">
                          {item.oldPrice !== null && item.oldPrice !== undefined ? (
                            <>
                              <span className="line-through text-slate-400 font-normal">₹{item.oldPrice}</span>
                              {' ➔ '}
                              <span className="text-emerald-700">₹{item.newPrice}</span>
                              <span className="text-slate-500 font-normal">/Qtl</span>
                            </>
                          ) : (
                            <>
                              <span className="text-emerald-700">₹{item.newPrice}</span>
                              <span className="text-slate-500 font-normal">/Quintal</span>
                            </>
                          )}

                          {item.priceChangePercent !== null && item.priceChangePercent !== undefined && item.priceDiff !== 0 && (
                            <span
                              className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                                (item.priceDiff || 0) > 0
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {(item.priceDiff || 0) > 0 ? `+${item.priceChangePercent}%` : `${item.priceChangePercent}%`}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Source Reporting Date */}
                      {item.sourceReportingDate && (
                        <div className="flex items-center gap-1 font-mono text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>
                            {language === 'ta' ? 'அரசு வரத்து தேதி:' : 'Agmarknet Arrival:'} {item.sourceReportingDate}
                          </span>
                        </div>
                      )}

                      {item.sourceDataTime && (
                        <div className="flex items-center gap-1 font-mono text-[10px] text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                          <Clock className="w-3 h-3 text-teal-600" />
                          <span>
                            {language === 'ta' ? 'வானிலை தரவு நேரம்:' : 'Weather Observed:'}{' '}
                            {item.sourceDataTime}
                          </span>
                        </div>
                      )}

                      {item.relatedFarmId && (
                        <div className="flex items-center gap-1 text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          <span>{item.relatedFarmId}</span>
                        </div>
                      )}

                      {item.crop && !item.commodity && (
                        <div className="flex items-center gap-1 text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          <Sprout className="w-3 h-3 text-emerald-600" />
                          <span>
                            {item.crop} {item.growthStage ? `(${item.growthStage})` : ''}
                          </span>
                        </div>
                      )}

                      {item.bookingId && (
                        <span className="text-[10px] text-emerald-800 font-mono font-bold bg-white px-2 py-0.5 rounded border border-emerald-200">
                          Booking #{item.bookingId}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Mark as read button if unread */}
                  {!item.isRead && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMarkAsRead(item.id);
                      }}
                      className="shrink-0 p-1.5 rounded-lg text-slate-400 hover:text-emerald-700 hover:bg-emerald-100/50 transition-colors"
                      title={language === 'ta' ? 'படித்ததாகக் குறி' : 'Mark as read'}
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Transparent SMS Gateway Adapter Notice Card */}
      <div className="p-5 rounded-3xl bg-slate-50 border border-slate-200 text-xs space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-slate-800">
            <Smartphone className="w-4 h-4 text-emerald-700" />
            <span>{language === 'ta' ? 'தொலைத்தொடர்பு SMS சேவை நிலை' : 'Telecom SMS Gateway Adapter Status'}</span>
          </div>

          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
              smsStatus?.configured
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-amber-100 text-amber-800 border border-amber-300'
            }`}
          >
            {smsStatus?.configured
              ? `Connected (${smsStatus.provider})`
              : 'Unconfigured (In-App Active)'}
          </span>
        </div>

        <p className="text-slate-600 leading-relaxed text-[11px]">
          {smsStatus?.note ||
            'Government procurement notifications are securely persisted in MongoDB and delivered via in-app alerts. SMS dispatch interface is extensible for CDAC / Twilio telecom gateway keys.'}
        </p>

        <p className="text-[10px] text-slate-400 italic">
          * Strictly honest compliance: Telecom SMS is not claimed as physically delivered unless genuine CDAC/telecom API keys are configured in backend environment variables.
        </p>
      </div>
    </div>
  );
};

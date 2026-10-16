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
} from 'lucide-react';

import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getNotificationsApi,
  markNotificationReadApi,
  markAllNotificationsReadApi,
  getSmsGatewayStatusApi,
  type InAppNotification,
  type SMSStatusInfo,
} from '../../services/api';

export const NotificationsView: React.FC = () => {
  const { language } = useLanguage();
  const { token } = useAuth();

  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [smsStatus, setSmsStatus] = useState<SMSStatusInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchNotifications = async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      setErrorMsg(null);
      const items = await getNotificationsApi(token, filter === 'unread');
      setNotifications(items || []);

      // Also load SMS gateway configuration status
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
    fetchNotifications();
  }, [token, filter]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchNotifications();
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
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to mark all notifications as read.');
    } finally {
      setIsMarkingAll(false);
    }
  };

  // Helper for notification icons and styling by category
  const getNotificationIcon = (type: string) => {
    switch (type.toLowerCase()) {
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
        return <CloudRain className="w-5 h-5 text-teal-600" />;
      default:
        return <Bell className="w-5 h-5 text-slate-600" />;
    }
  };

  const getNotificationBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case 'booking':
        return { label: language === 'ta' ? 'முன்பதிவு' : 'Booking', color: 'bg-emerald-100 text-emerald-800' };
      case 'queue':
        return { label: language === 'ta' ? 'வரிசை' : 'Queue', color: 'bg-blue-100 text-blue-800' };
      case 'weighing':
      case 'bill':
        return { label: language === 'ta' ? 'எடையிடல் / பில்' : 'Weighment & Bill', color: 'bg-purple-100 text-purple-800' };
      case 'payment':
        return { label: language === 'ta' ? 'வங்கி DBT' : 'PFMS Payment', color: 'bg-emerald-100 text-emerald-800' };
      default:
        return { label: language === 'ta' ? 'அறிவிப்பு' : 'General', color: 'bg-slate-100 text-slate-700' };
    }
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

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
                {language === 'ta' ? 'அதிகாரப்பூர்வ அறிவிப்புகள்' : 'Official Notifications Center'}
              </span>
              <h2 className="text-2xl font-black mt-0.5">
                {language === 'ta' ? 'விவசாயி எச்சரிக்கைகள் & தகவல்கள்' : 'Farmer Alerts & Status Updates'}
              </h2>
              <p className="text-xs text-emerald-100/90 mt-1">
                {language === 'ta'
                  ? 'கொள்முதல் முன்பதிவு, வாகன வரிசை, எடை ரசீது மற்றும் வங்கி பணம் நிலை'
                  : 'Real-time alerts for mandi slot bookings, weighbridge queue, and DBT disbursements'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
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

      {/* Main Notifications Card */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl">
            {errorMsg}
          </div>
        )}
        {/* Filters and Mark all as read */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
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
        ) : notifications.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-400 space-y-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <Bell className="w-6 h-6" />
            </div>
            <p className="font-semibold text-slate-700">
              {language === 'ta' ? 'அறிவிப்புகள் எதுவும் இல்லை' : 'No notifications found'}
            </p>
            <p className="text-[11px]">
              {language === 'ta'
                ? 'கொள்முதல் முன்பதிவு மற்றும் எடை நிலை மாற்றங்களின் போது இங்கு எச்சரிக்கைகள் தோன்றும்.'
                : 'Alerts appear here automatically when you create mandi bookings or when staff updates your queue and weighing status.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((item) => {
              const badge = getNotificationBadge(item.type);

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
                    {getNotificationIcon(item.type)}
                  </div>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${badge.color}`}>
                          {badge.label}
                        </span>
                        {!item.isRead && (
                          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                        )}
                        <h4 className={`text-xs sm:text-sm font-bold ${item.isRead ? 'text-slate-800' : 'text-emerald-950 font-black'}`}>
                          {item.title}
                        </h4>
                      </div>

                      <span className="text-[10px] text-slate-400 font-mono">
                        {item.createdAt}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {item.message}
                    </p>

                    {item.bookingId && (
                      <span className="inline-block text-[10px] text-emerald-800 font-mono font-bold mt-1 bg-white px-2 py-0.5 rounded border border-emerald-200">
                        Booking #{item.bookingId}
                      </span>
                    )}
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

      {/* TASK 6: Transparent SMS Gateway Adapter Notice Card */}
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

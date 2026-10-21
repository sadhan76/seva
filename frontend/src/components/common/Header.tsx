import React, { useState, useEffect } from 'react';
import { Menu, LogIn, LogOut, UserPlus, Bell, UserCog } from 'lucide-react';
import { LanguageToggle } from './LanguageToggle';
import type { ViewState, NavTab } from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { getNotificationsApi, markNotificationReadApi, type InAppNotification } from '../../services/api';

interface HeaderProps {
  currentTab: NavTab;
  viewState?: ViewState;
  onSetViewState?: (state: ViewState) => void;
  onOpenMobileMenu: () => void;
  onOpenLogin: () => void;
  onOpenRegister: () => void;
  onNavigate?: (tab: NavTab) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  viewState: _viewState,
  onSetViewState: _onSetViewState,
  onOpenMobileMenu,
  onOpenLogin,
  onOpenRegister,
  onNavigate,
}) => {
  const { t, language } = useLanguage();
  const { user, token, isAuthenticated, logout } = useAuth();
  // Notification State
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const [isLoadingNotifs, setIsLoadingNotifs] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);

  const fetchNotifs = async () => {
    if (!token) return;
    setIsLoadingNotifs(true);
    try {
      const items = await getNotificationsApi(token);
      setNotifications(items);
    } catch {
      // Graceful
    } finally {
      setIsLoadingNotifs(false);
    }
  };


  useEffect(() => {
    if (isAuthenticated && token) {
      fetchNotifs();
      const interval = setInterval(fetchNotifs, 20000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, token]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationReadApi(id, token);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
      );
    } catch {
      // Graceful
    }
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const userName = user?.fullName || user?.name || 'User';

  return (
    <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-slate-200/90 px-4 md:px-6 py-3 transition-all">
      <div className="flex items-center justify-between gap-3">
        {/* Left: Mobile hamburger & Active Title */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 lg:hidden focus:outline-none"
            aria-label="Open mobile menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base md:text-lg font-bold text-slate-900 tracking-tight">
                {t.nav[currentTab] || currentTab}
              </h1>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              {t.appTagline}
            </p>
          </div>
        </div>

        {/* Right: Language Toggle + Notification + Profile / Auth */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Bilingual Language Selector */}
          <LanguageToggle />

          {/* FEATURE 7: In-App Notification Bell */}
          {isAuthenticated && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifs(!showNotifs)}
                className="relative p-2 rounded-xl text-slate-600 hover:text-emerald-800 hover:bg-emerald-50 transition-colors"
                aria-label="View notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-emerald-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Popover Dropdown */}
              {showNotifs && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 p-4 space-y-3 animate-fade-in">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div className="flex items-center gap-1.5">
                      <Bell className="w-4 h-4 text-emerald-700" />
                      <h4 className="text-xs font-bold text-slate-800">In-App Notifications</h4>
                    </div>
                    {unreadCount > 0 && (
                      <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                        {unreadCount} unread
                      </span>
                    )}
                  </div>

                  <div className="max-h-64 overflow-y-auto space-y-2 divide-y divide-slate-50">
                    {isLoadingNotifs ? (
                      <p className="text-xs text-slate-400 py-4 text-center">Loading notifications...</p>
                    ) : notifications.length === 0 ? (
                      <p className="text-xs text-slate-400 py-4 text-center">No notifications yet.</p>
                    ) : (
                      notifications.map((n) => {
                        const title = language === 'ta' && n.titleTa ? n.titleTa : n.title;
                        const message = language === 'ta' && n.messageTa ? n.messageTa : n.message;
                        return (
                          <div
                            key={n.id}
                            onClick={() => handleMarkAsRead(n.id)}
                            className={`pt-2 cursor-pointer transition-colors p-2 rounded-xl text-left ${
                              n.isRead ? 'opacity-70 bg-transparent' : 'bg-emerald-50/60 font-medium'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 line-clamp-1">{title}</span>
                              <span className="text-[10px] text-slate-400 font-mono shrink-0 ml-1">{n.createdAt}</span>
                            </div>
                            <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-2">{message}</p>
                            {n.sourceDataTime && (
                              <span className="text-[9px] text-teal-700 block font-mono mt-0.5">
                                {language === 'ta' ? `வானிலை நேரம்: ${n.sourceDataTime}` : `Weather observed: ${n.sourceDataTime}`}
                              </span>
                            )}
                            <span className="text-[9px] uppercase font-bold text-emerald-700 tracking-wider mt-1 block">
                              Type: {n.eventType || n.type}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-100 text-center space-y-1.5">
                    {onNavigate && (
                      <button
                        type="button"
                        onClick={() => {
                          setShowNotifs(false);
                          onNavigate('notifications');
                        }}
                        className="w-full py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold transition-colors shadow-xs"
                      >
                        View Full Notifications Page →
                      </button>
                    )}
                    <p className="text-[10px] text-slate-400">
                      In-app alerts are live. SMS integration can be connected via telecom gateway.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Authentication Badge / Account Menu */}
          {isAuthenticated && user ? (
            <div className="relative pl-2 border-l border-slate-200">
              <button
                type="button"
                onClick={() => setShowAccountMenu(!showAccountMenu)}
                className="flex items-center gap-2 p-1.5 rounded-2xl hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                aria-label="Open account menu"
              >
                {user.profilePhoto ? (
                  <img
                    src={user.profilePhoto}
                    alt={userName}
                    className="w-8 h-8 rounded-full object-cover border border-emerald-300 shadow-xs"
                  />
                ) : (
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shadow-xs ${
                      user.role === 'staff'
                        ? 'bg-purple-100 text-purple-800 border border-purple-200'
                        : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    {userName.substring(0, 2).toUpperCase()}
                  </div>
                )}
                <div className="hidden md:block text-left">
                  <div className="flex items-center gap-1.5">
                    <p className="text-xs font-bold text-slate-800 leading-tight">
                      {userName}
                    </p>
                    <span
                      className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded-full uppercase tracking-wider ${
                        user.role === 'staff'
                          ? 'bg-purple-100 text-purple-700 border border-purple-200'
                          : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {user.role === 'staff' ? 'Staff' : 'Farmer'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-none mt-0.5 truncate max-w-[140px]">
                    {user.role === 'staff'
                      ? (user.mandiAssigned || user.mandiName || 'Direct Purchase Centre')
                      : (user.village ? `${user.village}, ${user.district || ''}` : (user.district || 'India'))}
                  </p>
                </div>
              </button>

              {/* Farmer Account Dropdown Menu */}
              {showAccountMenu && (
                <div className="absolute right-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 p-4 space-y-3 animate-fade-in text-left">
                  <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
                    {user.profilePhoto ? (
                      <img
                        src={user.profilePhoto}
                        alt={userName}
                        className="w-12 h-12 rounded-full object-cover border border-emerald-300 shadow-sm"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-base shadow-sm">
                        {userName.substring(0, 2).toUpperCase()}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-slate-900 truncate">{userName}</p>
                      <p className="text-[11px] font-mono font-bold text-emerald-700 truncate">
                        {user.farmerId || 'Farmer Account'}
                      </p>
                      <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {user.phone}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Location:</span>
                      <span className="font-semibold text-slate-800 text-right truncate max-w-[160px]">
                        {user.village ? `${user.village}, ${user.district || ''}` : (user.district || 'India')}
                      </span>
                    </div>
                    {user.state && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">State:</span>
                        <span className="font-semibold text-slate-800">{user.state}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-slate-400">Language:</span>
                      <span className="font-bold text-emerald-700 uppercase">{user.preferredLanguage || 'en'}</span>
                    </div>
                    {user.totalLandAcres && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">Land Holding:</span>
                        <span className="font-semibold text-slate-800">
                          {user.totalLandAcres} {user.landUnit || 'Acres'}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-1 pt-1">
                    {onNavigate && (
                      <button
                        type="button"
                        onClick={() => {
                          setShowAccountMenu(false);
                          onNavigate('profile');
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-emerald-900 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                      >
                        <UserCog className="w-4 h-4 text-emerald-700" />
                        <span>{t.common.editProfile || 'Edit Profile'}</span>
                        <span className="ml-auto text-[10px] text-emerald-600">→</span>
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => {
                        setShowAccountMenu(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-rose-700 hover:bg-rose-50 transition-colors"
                    >
                      <LogOut className="w-4 h-4 text-rose-500" />
                      <span>{t.auth.signOut || 'Log Out'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
              <button
                type="button"
                onClick={onOpenLogin}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center gap-1.5"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>{t.auth.signIn}</span>
              </button>
              <button
                type="button"
                onClick={onOpenRegister}
                className="hidden sm:inline-flex px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all items-center gap-1.5"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>{t.auth.signUp}</span>
              </button>
            </div>
          )}

        </div>
      </div>
    </header>
  );
};


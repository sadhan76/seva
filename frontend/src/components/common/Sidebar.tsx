import React from 'react';
import {
  LayoutDashboard,
  Bot,
  CloudSun,
  Droplet,
  Bug,
  Sprout,
  TrendingUp,
  Landmark,
  CalendarCheck,
  ListOrdered,
  User,
  X,
  Building2,
  Bell,
  LogOut,
  GraduationCap,
  Store,
  Compass,
  Briefcase,
  Layers,
} from 'lucide-react';
import type { NavTab } from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isOpenMobile,
  onCloseMobile,
}) => {
  const { t, language } = useLanguage();
  const { user, logout } = useAuth();

  const isStaff = user?.role === 'staff';

  // Strict role-based navigation item segregation
  const navItems: Array<{
    id: NavTab;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    category?: 'core' | 'agri' | 'mandi' | 'account' | 'staff';
  }> = isStaff
    ? [
        {
          id: 'staff_portal' as NavTab,
          label: language === 'ta' ? 'பணியாளர் மையம்' : 'Staff Mandi Portal',
          icon: Building2,
          category: 'staff',
        },
        {
          id: 'market' as NavTab,
          label: t.nav.market,
          icon: TrendingUp,
          category: 'mandi',
        },
        {
          id: 'weather' as NavTab,
          label: t.nav.weather,
          icon: CloudSun,
          category: 'agri',
        },
        {
          id: 'support_hub' as NavTab,
          label: t.nav.support_hub,
          icon: GraduationCap,
          category: 'agri',
        },
        {
          id: 'notifications' as NavTab,
          label: t.nav.notifications,
          icon: Bell,
          category: 'account',
        },
      ]
    : [
        { id: 'dashboard', label: t.nav.dashboard, icon: LayoutDashboard, category: 'core' },
        { id: 'assistant', label: t.nav.assistant, icon: Bot, category: 'agri' },
        { id: 'weather', label: t.nav.weather, icon: CloudSun, category: 'agri' },
        { id: 'irrigation', label: t.nav.irrigation, icon: Droplet, category: 'agri' },
        { id: 'disease', label: t.nav.disease, icon: Bug, category: 'agri' },
        { id: 'recommendations', label: t.nav.recommendations, icon: Sprout, category: 'agri' },
        { id: 'market', label: t.nav.market, icon: TrendingUp, category: 'mandi' },
        { id: 'marketplace', label: t.nav.marketplace, icon: Store, category: 'mandi' },
        { id: 'agri_entrepreneurship', label: t.nav.agri_entrepreneurship, icon: Briefcase, category: 'mandi' },
        { id: 'value_addition', label: t.nav.value_addition, icon: Layers, category: 'mandi' },
        { id: 'schemes', label: t.nav.schemes, icon: Landmark, category: 'mandi' },
        { id: 'support_hub', label: t.nav.support_hub, icon: GraduationCap, category: 'agri' },
        { id: 'special_operation', label: t.nav.special_operation, icon: Compass, category: 'agri' },
        { id: 'procurement', label: t.nav.procurement, icon: CalendarCheck, category: 'mandi' },
        { id: 'queue', label: t.nav.queue, icon: ListOrdered, category: 'mandi' },
        { id: 'notifications', label: t.nav.notifications, icon: Bell, category: 'account' },
        { id: 'profile', label: t.nav.profile, icon: User, category: 'account' },
      ];

  const handleItemClick = (tab: NavTab) => {
    onSelectTab(tab);
    onCloseMobile();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-white border-r border-slate-200/90 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:z-30 ${
          isOpenMobile ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-emerald-50/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-700 to-green-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/20">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-slate-900 text-sm tracking-tight">
                  {t.appName}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">
                  {isStaff ? 'STAFF' : 'FARMER'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium truncate max-w-[155px]">
                {isStaff ? (user?.mandiAssigned || user?.mandiName || 'DPC Centre') : (user?.village || t.appTagline)}
              </p>
            </div>
          </div>
          <button
            onClick={onCloseMobile}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation List */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleItemClick(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-2xl text-xs font-bold transition-all text-left ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-xs shadow-emerald-600/20'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* User Identity & Logout Footer */}
        {user && (
          <div className="p-3 border-t border-slate-100 bg-slate-50/60">
            <div className="flex items-center justify-between gap-2 p-2 rounded-2xl bg-white border border-slate-200/80 shadow-2xs">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shrink-0 ${
                    isStaff
                      ? 'bg-purple-100 text-purple-800 border border-purple-200'
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}
                >
                  {(user.name || 'U').slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-slate-800 truncate">
                    {user.name}
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono truncate">
                    {user.phone}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={logout}
                title={language === 'ta' ? 'வெளியேறு' : 'Log Out'}
                className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors shrink-0"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};

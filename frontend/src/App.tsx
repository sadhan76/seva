import React, { useState, useEffect } from 'react';
import { Sprout, Loader2 } from 'lucide-react';
import type { NavTab, ViewState, FarmerProfile, ProcurementSlot, WeatherData } from './types';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { NoticeBanner } from './components/common/NoticeBanner';
import { LoadingState, EmptyState, ErrorState } from './components/common/StateViews';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { FarmerWelcomeHero } from './components/dashboard/FarmerWelcomeHero';
import { FarmDetailsCard } from './components/dashboard/FarmDetailsCard';
import { WeatherCard } from './components/dashboard/WeatherCard';
import { IrrigationAdviceCard } from './components/dashboard/IrrigationAdviceCard';
import { CropHealthCard } from './components/dashboard/CropHealthCard';
import { MarketPricesCard } from './components/dashboard/MarketPricesCard';
import { ProcurementCard } from './components/dashboard/ProcurementCard';
import { QuickActions } from './components/dashboard/QuickActions';

// Login Page Component (First Screen for Visitors)
import { LoginPage } from './components/auth/LoginPage';
import { LoginModal } from './components/auth/LoginModal';
import { RegisterModal } from './components/auth/RegisterModal';
import { GlobalChatWidget } from './components/chat/GlobalChatWidget';

// Tab Views
import { FarmingAssistantView } from './components/views/FarmingAssistantView';
import { WeatherView } from './components/views/WeatherView';
import { IrrigationView } from './components/views/IrrigationView';
import { DiseaseDetectionView } from './components/views/DiseaseDetectionView';
import { CropRecommendationView } from './components/views/CropRecommendationView';
import { MarketPricesView } from './components/views/MarketPricesView';
import { GovernmentSchemesView } from './components/views/GovernmentSchemesView';
import { ProcurementBookingView } from './components/views/ProcurementBookingView';
import { QueueTrackingView } from './components/views/QueueTrackingView';
import { ProfileView } from './components/views/ProfileView';
import { StaffPortalView } from './components/views/StaffPortalView';
import { NotificationsView } from './components/views/NotificationsView';
import { FarmerSupportHubView } from './components/views/FarmerSupportHubView';
import { MarketplaceView } from './components/views/MarketplaceView';
import { SpecialOperationJourneyView } from './components/views/SpecialOperationJourneyView';
import { AgriEntrepreneurshipView } from './components/views/AgriEntrepreneurshipView';
import { ValueAddedProductsView } from './components/views/ValueAddedProductsView';

// Sample Mock Data Fallbacks (Only used when no live data exists)
import {
  sampleWeather,
  sampleIrrigation,
  sampleCropHealth,
} from './data/sampleData';

import { getProcurementBookings, getWeatherApi } from './services/api';

const MainDashboardContent: React.FC<{
  currentTab: NavTab;
  onNavigate: (tab: NavTab, bookingId?: string) => void;
  viewState: ViewState;
  onSetViewState: (st: ViewState) => void;
  farmer: FarmerProfile;
  procurement: ProcurementSlot | null;
  liveWeather: WeatherData | null;
  onFarmerUpdated: (f: FarmerProfile) => void;
  onBookingCreated: (b: ProcurementSlot) => void;
  activeBookingId?: string | null;
}> = ({
  currentTab,
  onNavigate,
  viewState,
  onSetViewState,
  farmer,
  procurement,
  liveWeather,
  onFarmerUpdated,
  onBookingCreated,
  activeBookingId,
}) => {
  const { t } = useLanguage();

  if (viewState === 'loading') {
    return <LoadingState />;
  }

  if (viewState === 'empty') {
    return (
      <EmptyState
        title={t.common.emptyTitle}
        description={t.common.emptyDesc}
        actionText="Load Sample Data"
        onAction={() => onSetViewState('normal')}
      />
    );
  }

  if (viewState === 'error') {
    return (
      <ErrorState
        title={t.common.errorTitle}
        description={t.common.errorDesc}
        onRetry={() => onSetViewState('normal')}
      />
    );
  }

  // Render view corresponding to current active tab
  switch (currentTab) {
    case 'assistant':
      return <FarmingAssistantView />;
    case 'weather':
      return (
        <WeatherView
          registeredDistrict={farmer.district}
          onNavigateToProfile={() => onNavigate('profile')}
        />
      );
    case 'irrigation':
      return <IrrigationView />;
    case 'disease':
      return <DiseaseDetectionView />;
    case 'recommendations':
      return <CropRecommendationView />;
    case 'market':
      return <MarketPricesView />;
    case 'marketplace':
      return <MarketplaceView onNavigate={onNavigate} />;
    case 'agri_entrepreneurship':
      return <AgriEntrepreneurshipView onNavigate={onNavigate} />;
    case 'value_addition':
      return <ValueAddedProductsView onNavigate={onNavigate} />;
    case 'schemes':
      return <GovernmentSchemesView />;
    case 'support_hub':
      return <FarmerSupportHubView onNavigate={onNavigate} />;
    case 'special_operation':
      return <SpecialOperationJourneyView onNavigate={onNavigate} />;
    case 'procurement':
      return (
        <ProcurementBookingView
          onBookingCreated={onBookingCreated}
          onNavigateToQueue={(id) => onNavigate('queue', id)}
        />
      );
    case 'queue':
      return <QueueTrackingView initialBookingId={activeBookingId} />;
    case 'profile':
      return <ProfileView farmer={farmer} onFarmerUpdated={onFarmerUpdated} />;
    case 'notifications':
      return <NotificationsView />;
    case 'staff_portal':
      return <StaffPortalView />;
    case 'dashboard':
    default:
      return (
        <div className="space-y-6">
          {/* Status Notice Banner */}
          <NoticeBanner />

          {/* Welcome Section for the Authenticated Farmer */}
          <FarmerWelcomeHero onNavigate={onNavigate} farmer={farmer} />

          {/* Quick Action Shortcuts */}
          <QuickActions onNavigate={onNavigate} />

          {/* 6 Core Dashboard Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 1. Real Farm Profile Details */}
            <FarmDetailsCard
              farmer={farmer}
              onViewProfile={() => onNavigate('profile')}
            />

            {/* 2. Weather Advisory (Live Open-Meteo for Farmer's District) */}
            <WeatherCard
              weather={liveWeather || sampleWeather}
              onViewForecast={() => onNavigate('weather')}
            />

            {/* 3. Irrigation Advice */}
            <IrrigationAdviceCard
              advice={sampleIrrigation}
              onOpenSchedule={() => onNavigate('irrigation')}
            />

            {/* 4. Crop Health Monitor */}
            <CropHealthCard
              health={sampleCropHealth}
              onScanLeaf={() => onNavigate('disease')}
            />

            {/* 5. Market Mandi Prices */}
            <MarketPricesCard
              onViewMarket={() => onNavigate('market')}
            />

            {/* 6. Procurement Booking & Queue */}
            <ProcurementCard
              slot={procurement}
              onTrackQueue={() => onNavigate('queue')}
              onBookNew={() => onNavigate('procurement')}
            />
          </div>
        </div>
      );
  }
};

export const AppContent: React.FC = () => {
  const { user, token, isAuthenticated, isLoadingAuth } = useAuth();

  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [viewState, setViewState] = useState<ViewState>('normal');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeBookingId, setActiveBookingId] = useState<string | null>(null);

  // Fallback modal states for in-app popups if needed
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  // Authenticated farmer state
  const [farmer, setFarmer] = useState<FarmerProfile>({
    name: user?.fullName || user?.name || '',
    phone: user?.phone || '',
    location: user?.village ? `${user.village}, ${user.district || 'Tamil Nadu'}` : (user?.district || 'Tamil Nadu'),
    district: user?.district || 'Thanjavur',
    state: user?.state || 'Tamil Nadu',
    totalLandAcres: user?.totalLandAcres,
    primaryCrop: user?.primaryCrop,
    soilType: user?.soilType,
    irrigationSource: user?.irrigationSource,
    aadhaarMasked: user?.aadhaarMasked,
    farmerId: user?.farmerId,
    isFromDb: true,
  });

  // Real procurement booking for authenticated farmer
  const [procurement, setProcurement] = useState<ProcurementSlot | null>(null);

  // Real live weather for farmer's district
  const [liveWeather, setLiveWeather] = useState<WeatherData | null>(null);

  // Synchronize authenticated user profile
  useEffect(() => {
    if (user && user.role === 'farmer') {
      setFarmer({
        name: user.fullName || user.name,
        phone: user.phone,
        location: user.village ? `${user.village}, ${user.district || 'Tamil Nadu'}` : (user.district || 'Tamil Nadu'),
        district: user.district || 'Thanjavur',
        state: user.state || 'Tamil Nadu',
        farmerId: user.farmerId,
        totalLandAcres: user.totalLandAcres,
        primaryCrop: user.primaryCrop,
        soilType: user.soilType,
        irrigationSource: user.irrigationSource,
        aadhaarMasked: user.aadhaarMasked,
        isFromDb: true,
      });
    }
  }, [user]);

  // Load authenticated farmer's real bookings from MongoDB
  useEffect(() => {
    let isMounted = true;
    async function loadFarmerBookings() {
      if (!token || user?.role !== 'farmer') {
        if (isMounted) setProcurement(null);
        return;
      }
      try {
        const bookingsList = await getProcurementBookings(token);
        if (isMounted) {
          if (bookingsList && bookingsList.length > 0) {
            const latest = bookingsList[0];
            setProcurement({
              bookingId: latest.bookingId,
              mandiName: latest.mandiName,
              crop: latest.crop,
              quantityBags: latest.quantityBags,
              estimatedWeightQuintals: latest.estimatedWeightQuintals,
              slotDate: latest.slotDate,
              timeWindow: latest.timeWindow,
              tokenNumber: latest.tokenNumber,
              status: latest.status?.toLowerCase() === 'booked' ? 'confirmed' : (latest.status || 'confirmed'),
              isSample: false,
              isFromDb: true,
            });
          } else {
            setProcurement(null);
          }
        }
      } catch {
        if (isMounted) setProcurement(null);
      }
    }
    loadFarmerBookings();
    return () => {
      isMounted = false;
    };
  }, [token, user?.id]);

  // Load real localized weather for farmer's registered district
  useEffect(() => {
    let isMounted = true;
    async function loadLocalizedWeather() {
      if (!isAuthenticated) return;
      try {
        const targetDistrict = farmer.district || user?.district;
        if (!targetDistrict) {
          if (isMounted) setLiveWeather(null);
          return;
        }
        const dist = targetDistrict.trim().toLowerCase();
        const wRes = await getWeatherApi(dist);
        if (isMounted && wRes && wRes.temperatureC !== null && wRes.temperatureC !== undefined) {
          setLiveWeather({
            temperatureC: Math.round(wRes.temperatureC),
            condition: wRes.condition,
            humidity: wRes.humidity,
            rainfallChance: wRes.rainfallChance,
            windSpeedKmh: Math.round(wRes.windSpeedKmh),
            updatedAt: wRes.observationTime || wRes.lastUpdated || 'Live Feed',
            isSample: false,
            forecast: (wRes.forecast || []).slice(0, 3).map((f) => ({
              day: f.day,
              temp: f.temp || `${f.tempMax}° / ${f.tempMin}°C`,
              condition: f.condition,
              rainProb: f.rainProb,
            })),
          });
        }
      } catch {
        // Graceful fallback
      }
    }
    loadLocalizedWeather();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, user?.district, farmer.district]);

  // Role-based route protection
  useEffect(() => {
    if (!isAuthenticated) return;

    if (user?.role === 'staff') {
      const staffAllowed: NavTab[] = ['staff_portal', 'market', 'weather', 'notifications'];
      if (!staffAllowed.includes(currentTab)) {
        setCurrentTab('staff_portal');
      }
    } else if (user?.role === 'farmer') {
      if (currentTab === 'staff_portal') {
        setCurrentTab('dashboard');
      }
    }
  }, [user?.role, currentTab, isAuthenticated]);

  // Safe navigation handler with role checks
  const handleNavigate = (tab: NavTab, bookingId?: string) => {
    if (bookingId) {
      setActiveBookingId(bookingId);
    }
    // Block farmer from opening staff portal
    if (user?.role === 'farmer' && tab === 'staff_portal') {
      setCurrentTab('dashboard');
      return;
    }
    // Block staff from opening farmer dashboard
    if (user?.role === 'staff' && tab === 'dashboard') {
      setCurrentTab('staff_portal');
      return;
    }
    setCurrentTab(tab);
  };

  // 1. Loading Session Screen
  if (isLoadingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-slate-50 to-emerald-50/50 flex flex-col items-center justify-center p-4">
        <div className="w-16 h-16 rounded-3xl bg-emerald-600 text-white flex items-center justify-center shadow-lg shadow-emerald-600/20 mb-4 animate-bounce">
          <Sprout className="w-9 h-9" />
        </div>
        <h2 className="text-lg font-black text-slate-800 tracking-tight">AgriBharat</h2>
        <div className="flex items-center gap-2 mt-2 text-xs font-semibold text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
          <span>Verifying authenticated session...</span>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated: Display Dedicated Login Page as First Screen
  if (!isAuthenticated) {
    return <LoginPage initialMode="signin" />;
  }

  // 3. Authenticated: Render Role-Based Application
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col antialiased text-slate-800">
      <div className="flex flex-1">
        {/* Responsive Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={handleNavigate}
          isOpenMobile={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Header
            currentTab={currentTab}
            viewState={viewState}
            onSetViewState={setViewState}
            onOpenMobileMenu={() => setMobileMenuOpen(true)}
            onOpenLogin={() => setIsLoginOpen(true)}
            onOpenRegister={() => setIsRegisterOpen(true)}
            onNavigate={handleNavigate}
          />

          <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            <MainDashboardContent
              currentTab={currentTab}
              onNavigate={handleNavigate}
              viewState={viewState}
              onSetViewState={setViewState}
              farmer={farmer}
              procurement={procurement}
              liveWeather={liveWeather}
              onFarmerUpdated={setFarmer}
              onBookingCreated={setProcurement}
              activeBookingId={activeBookingId}
            />
          </main>

          {/* Footer */}
          <footer className="border-t border-slate-200/80 bg-white/70 backdrop-blur-xs py-4 px-6 text-center text-xs text-slate-500">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
              <p>
                <strong>AgriBharat (அக்ரிபாரத்)</strong> — Smart Farming Intelligence & Agricultural Marketplace
              </p>
              <p className="text-[11px] text-slate-400">
                Logged in as <strong>{user?.name}</strong> ({user?.role?.toUpperCase()}) • Tamil Nadu Agriculture & Mandi Procurement System
              </p>
            </div>
          </footer>
        </div>
      </div>

      {/* Auxiliary Modals for In-Session Changes if Needed */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onSwitchToRegister={() => {
          setIsLoginOpen(false);
          setIsRegisterOpen(true);
        }}
      />
      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSwitchToLogin={() => {
          setIsRegisterOpen(false);
          setIsLoginOpen(true);
        }}
      />

      {/* Global AI Assistant Floating Widget with Voice & App Actions (Phase 17) */}
      <GlobalChatWidget
        currentTab={currentTab}
        onNavigate={handleNavigate}
        farmer={farmer}
      />
    </div>
  );
};

export function App() {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </LanguageProvider>
    </ErrorBoundary>
  );
}

export default App;

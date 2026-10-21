import React, { useState, useEffect } from 'react';
import {
  Store,
  PlusCircle,
  Phone,
  MessageCircle,
  Search,
  MapPin,
  Calendar,
  Truck,
  Leaf,
  Package,
  Eye,
  Trash2,
  Edit,
  X,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ShoppingBag,
  AlertTriangle,
  CheckCircle2,
  Send,
  Check,
  UserCheck,
  Flag,
  Shield,
  Image as ImageIcon
} from 'lucide-react';
import type {
  NavTab,
  MarketplaceListing,
  MarketplaceListingCreate,
  MarketplaceOrderRequest,
  MarketplaceOrderRequestCreate
} from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  getMarketplaceListings,
  getFarmerMyListings,
  createFarmerMarketplaceListing,
  updateFarmerMarketplaceListing,
  deleteFarmerMarketplaceListing,
  recordMarketplaceInquiry,
  createMarketplaceOrderRequest,
  getFarmerMyOrders,
  updateFarmerOrderStatus,
  reportMarketplaceListing
} from '../../services/api';

interface MarketplaceViewProps {
  onNavigate?: (tab: NavTab) => void;
}

export const MarketplaceView: React.FC<MarketplaceViewProps> = ({ onNavigate: _onNavigate }) => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const isTa = language === 'ta';
  const isFarmer = user?.role === 'farmer';

  // Navigation tabs within Marketplace
  const [activeTab, setActiveTab] = useState<'browse' | 'my_listings'>('browse');
  const [farmerSubTab, setFarmerSubTab] = useState<'listings' | 'orders'>('listings');

  // Browse state
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [totalListings, setTotalListings] = useState<number>(0);
  const [categories, setCategories] = useState<string[]>(['All']);
  const [districts, setDistricts] = useState<string[]>(['All']);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [organicOnly, setOrganicOnly] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);

  // Farmer's personal listings & incoming orders
  const [myListings, setMyListings] = useState<MarketplaceListing[]>([]);
  const [isLoadingMyListings, setIsLoadingMyListings] = useState<boolean>(false);
  const [farmerOrders, setFarmerOrders] = useState<MarketplaceOrderRequest[]>([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState<boolean>(false);

  // Listing Create / Edit Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [editingListing, setEditingListing] = useState<MarketplaceListing | null>(null);

  // Customer Order Request Modal State
  const [orderModalListing, setOrderModalListing] = useState<MarketplaceListing | null>(null);
  const [orderForm, setOrderForm] = useState<MarketplaceOrderRequestCreate>({
    buyerName: user?.name || '',
    buyerPhone: user?.phone || '',
    requestedQuantity: 1,
    fulfillmentPreference: 'Farm Gate Pickup',
    deliveryAddress: '',
    message: ''
  });
  const [isSubmittingOrder, setIsSubmittingOrder] = useState<boolean>(false);
  const [orderSubmitError, setOrderSubmitError] = useState<string | null>(null);
  const [completedOrder, setCompletedOrder] = useState<MarketplaceOrderRequest | null>(null);

  // Reporting Modal State
  const [reportingListing, setReportingListing] = useState<MarketplaceListing | null>(null);
  const [reportReason, setReportReason] = useState<'spam' | 'fake_price' | 'misleading_claims' | 'expired_produce' | 'other'>('spam');
  const [reportDetails, setReportDetails] = useState<string>('');
  const [isSubmittingReport, setIsSubmittingReport] = useState<boolean>(false);
  const [reportSuccessMessage, setReportSuccessMessage] = useState<string | null>(null);

  // Produce Listing Form State
  const initialForm: MarketplaceListingCreate = {
    crop: '',
    variety: '',
    category: 'Cereals',
    district: user?.district || 'Thanjavur',
    village: user?.village || '',
    quantity: 10,
    unit: 'Quintal',
    pricePerUnit: 2500,
    isOrganicCertified: false,
    certificationBody: '',
    harvestDate: new Date().toISOString().split('T')[0],
    availableUntil: '',
    fulfillmentModes: ['Farm Gate Pickup'],
    serviceArea: '',
    photoUrls: [],
    showContactToBuyers: false,
    description: '',
  };
  const [formData, setFormData] = useState<MarketplaceListingCreate>(initialForm);

  // Load public listings
  const loadPublicListings = async () => {
    setIsLoading(true);
    setHasError(false);
    try {
      const res = await getMarketplaceListings({
        category: selectedCategory === 'All' ? undefined : selectedCategory,
        district: selectedDistrict === 'All' ? undefined : selectedDistrict,
        search: searchQuery.trim() || undefined,
        organicOnly,
        limit: 30,
      });
      setListings(res.items || []);
      setTotalListings(res.total || 0);
      if (res.categories && res.categories.length > 0) setCategories(res.categories);
      if (res.districts && res.districts.length > 0) setDistricts(res.districts);
    } catch (err) {
      console.error('Failed to load marketplace listings:', err);
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Load farmer's personal listings
  const loadMyListings = async () => {
    if (!token || !isFarmer) return;
    setIsLoadingMyListings(true);
    try {
      const res = await getFarmerMyListings(token);
      setMyListings(res.items || []);
    } catch (err) {
      console.error('Failed to load farmer listings:', err);
    } finally {
      setIsLoadingMyListings(false);
    }
  };

  // Load farmer's incoming buyer orders
  const loadFarmerOrders = async () => {
    if (!token || !isFarmer) return;
    setIsLoadingOrders(true);
    try {
      const res = await getFarmerMyOrders(token);
      setFarmerOrders(res.items || []);
    } catch (err) {
      console.error('Failed to load farmer orders:', err);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  useEffect(() => {
    loadPublicListings();
  }, [selectedCategory, selectedDistrict, organicOnly]);

  useEffect(() => {
    if (activeTab === 'my_listings') {
      loadMyListings();
      loadFarmerOrders();
    }
  }, [activeTab]);

  // Handle buyer contact click (Calls inquiry tracker API)
  const handleBuyerContact = async (listing: MarketplaceListing, type: 'call' | 'whatsapp') => {
    try {
      recordMarketplaceInquiry(listing.listingId);
    } catch (e) {
      // Non-blocking telemetry
    }

    if (type === 'call') {
      window.open(`tel:${listing.farmerPhone}`, '_self');
    } else {
      const cleanPhone = listing.farmerPhone.replace(/\D/g, '');
      const fullPhone = cleanPhone.startsWith('91') ? cleanPhone : `91${cleanPhone}`;
      const msg = encodeURIComponent(
        `Vanakkam ${listing.farmerName}, I saw your listing for ${listing.crop} (${listing.listingId}) on AgriBharat platform. Is it available for purchase?`
      );
      window.open(`https://wa.me/${fullPhone}?text=${msg}`, '_blank');
    }
  };

  // Handle Produce Form Submission (Create or Edit)
  const handleSubmitProduce = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setSubmitError('Authentication token expired. Please re-login.');
      return;
    }
    if (!formData.crop.trim()) {
      setSubmitError('Produce name is required.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      if (editingListing) {
        await updateFarmerMarketplaceListing(editingListing.listingId, formData, token);
      } else {
        await createFarmerMarketplaceListing(formData, token);
      }
      setIsCreateModalOpen(false);
      setEditingListing(null);
      setFormData(initialForm);
      loadPublicListings();
      loadMyListings();
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to save listing. Please check inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Order Request Submission by Buyer
  const handleSubmitOrderRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderModalListing) return;

    if (!orderForm.buyerName.trim() || !orderForm.buyerPhone.trim()) {
      setOrderSubmitError(isTa ? 'பெயர் மற்றும் தொடர்பு எண் அவசியம்' : 'Name and phone number are required.');
      return;
    }

    if (orderForm.requestedQuantity <= 0) {
      setOrderSubmitError(isTa ? 'சரியான அளவை உள்ளிடவும்' : 'Please enter a valid requested quantity.');
      return;
    }

    setIsSubmittingOrder(true);
    setOrderSubmitError(null);

    try {
      const res = await createMarketplaceOrderRequest(orderModalListing.listingId, orderForm);
      setCompletedOrder(res);
      loadPublicListings();
    } catch (err: any) {
      setOrderSubmitError(err.message || 'Failed to submit order request. Please try again.');
    } finally {
      setIsSubmittingOrder(false);
    }
  };

  // Farmer Order Status Update Handler
  const handleUpdateOrderStatus = async (orderId: string, newStatus: string) => {
    if (!token) return;
    try {
      await updateFarmerOrderStatus(orderId, newStatus, token);
      loadFarmerOrders();
    } catch (err) {
      alert(isTa ? 'ஆர்டர் நிலையை புதுப்பிக்க முடியவில்லை.' : 'Failed to update order status.');
    }
  };

  // Delete Listing
  const handleDeleteListing = async (listingId: string) => {
    if (!token) return;
    const confirmDelete = window.confirm(
      isTa
        ? 'இந்த விளைபொருள் பதிவை நிச்சயமாக நீக்க விரும்புகிறீர்களா?'
        : 'Are you sure you want to remove this produce listing?'
    );
    if (!confirmDelete) return;

    try {
      await deleteFarmerMarketplaceListing(listingId, token);
      loadMyListings();
      loadPublicListings();
    } catch (err) {
      alert('Failed to remove listing.');
    }
  };

  // Handle Report Submission
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportingListing) return;
    setIsSubmittingReport(true);
    try {
      await reportMarketplaceListing(reportingListing.listingId, {
        reasonCategory: reportReason,
        details: reportDetails
      });
      setReportSuccessMessage(
        isTa
          ? 'புகார் வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது. நிர்வாகி குழுவால் மதிப்பாய்வு செய்யப்படும்.'
          : 'Report submitted successfully. Our moderation team will review this listing.'
      );
      setTimeout(() => {
        setReportingListing(null);
        setReportSuccessMessage(null);
        setReportDetails('');
        loadPublicListings();
      }, 1800);
    } catch (err: any) {
      alert(err.message || 'Failed to submit report.');
    } finally {
      setIsSubmittingReport(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Hero Banner */}
      <div className="bg-gradient-to-r from-emerald-800 via-teal-800 to-emerald-900 text-white rounded-2xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 text-xs font-semibold mb-3">
            <Sparkles className="w-4 h-4 text-emerald-300" />
            {isTa ? 'இடைத்தரகர்கள் இல்லாத நேரடி பண்ணை சந்தை • 0% கமிஷன்' : 'Direct Farm Gate Discovery • 0% Commission'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            {isTa ? 'உழவர் - நுகர்வோர் நேரடி விற்பனை தளம்' : 'Farmer-to-Customer Direct Marketplace'}
          </h1>
          <p className="text-emerald-100 text-sm sm:text-base leading-relaxed">
            {isTa
              ? 'தமிழக விவசாயிகள் விளைவித்த பாரம்பரிய அரிசி, இயற்கை மஞ்சள், மரச்செக்கு எண்ணெய், காய்கறிகள் மற்றும் பழங்களை இடைத்தரகர்கள் இன்றி நேரடியாக பண்ணை வாசலில் வாங்குங்கள். நேரடி முன்பதிவு மற்றும் வாட்ஸ்அப் தொடர்பு.'
              : 'Discover farm-fresh heritage paddy, cold-pressed virgin oils, organic spices, and vegetables directly from verified Tamil Nadu farmers. Place direct order requests and connect via phone or WhatsApp.'}
          </p>

          {/* Action Bar for Logged-in Farmers */}
          <div className="mt-6 flex flex-wrap items-center gap-3">
            {isFarmer ? (
              <button
                onClick={() => {
                  setEditingListing(null);
                  setFormData(initialForm);
                  setIsCreateModalOpen(true);
                }}
                className="px-5 py-2.5 rounded-xl bg-white text-emerald-900 font-bold text-sm hover:bg-emerald-50 shadow-md transition-all flex items-center gap-2"
              >
                <PlusCircle className="w-4 h-4 text-emerald-700" />
                <span>{isTa ? 'என் விளைபொருளை பதிவேற்று' : 'List My Produce'}</span>
              </button>
            ) : (
              <div className="text-xs text-emerald-200 bg-white/10 px-3 py-1.5 rounded-lg border border-white/20">
                💡 {isTa ? 'விவசாயியாக உள்நுழைந்து உங்கள் விளைபொருட்களை பட்டியலிடலாம்.' : 'Log in as a registered farmer to list produce and receive orders.'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Mode Switcher: Browse Marketplace vs My Inventory */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab('browse')}
            className={`pb-2 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'browse'
                ? 'border-emerald-600 text-emerald-800'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <ShoppingBag className="w-4 h-4" />
            <span>{isTa ? 'சந்தை விளைபொருட்கள்' : 'Explore Produce'}</span>
            <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold">
              {totalListings}
            </span>
          </button>

          {isFarmer && (
            <button
              onClick={() => setActiveTab('my_listings')}
              className={`pb-2 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
                activeTab === 'my_listings'
                  ? 'border-emerald-600 text-emerald-800'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Package className="w-4 h-4" />
              <span>{isTa ? 'விவசாயி கட்டுப்பாட்டு பலகை' : 'Farmer Dashboard'}</span>
              <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                {myListings.length}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* BROWSE PUBLIC MARKETPLACE VIEW */}
      {activeTab === 'browse' && (
        <div className="space-y-6">
          {/* Filter and Search Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
              {/* Search */}
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadPublicListings()}
                  placeholder={isTa ? 'பயிர், ரகம், கிராமத்தை தேடுக...' : 'Search crop, variety, village...'}
                  className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white"
                />
              </div>

              {/* District & Organic Filter */}
              <div className="flex items-center gap-3 w-full sm:w-auto justify-end flex-wrap">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  <select
                    value={selectedDistrict}
                    onChange={(e) => setSelectedDistrict(e.target.value)}
                    className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
                  >
                    {districts.map((d) => (
                      <option key={d} value={d}>
                        {d === 'All' ? (isTa ? 'அனைத்து மாவட்டங்கள்' : 'All Districts') : d}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Organic certified toggle */}
                <button
                  onClick={() => setOrganicOnly(!organicOnly)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 border ${
                    organicOnly
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:border-emerald-300'
                  }`}
                >
                  <Leaf className={`w-3.5 h-3.5 ${organicOnly ? 'text-white' : 'text-emerald-600'}`} />
                  <span>{isTa ? 'இயற்கை சான்றிதழ் மட்டும்' : 'Organic Only'}</span>
                </button>

                <button
                  onClick={loadPublicListings}
                  title={isTa ? 'புதுப்பி' : 'Refresh'}
                  className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 border border-slate-200 rounded-lg transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Category Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pt-2 border-t border-slate-100 scrollbar-none">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                    selectedCategory === cat
                      ? 'bg-emerald-700 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-emerald-50 hover:text-emerald-700'
                  }`}
                >
                  {cat === 'All' ? (isTa ? 'அனைத்து பிரிவுகள்' : 'All Categories') : cat}
                </button>
              ))}
            </div>
          </div>

          {/* Produce Grid */}
          {isLoading ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
              <p className="text-sm font-semibold text-slate-700">
                {isTa ? 'விளைபொருட்கள் பட்டியலிடப்படுகின்றன...' : 'Loading farm gate produce...'}
              </p>
            </div>
          ) : hasError ? (
            <div className="bg-white rounded-2xl border border-red-200 p-8 text-center space-y-3">
              <AlertCircle className="w-8 h-8 text-red-500 mx-auto" />
              <p className="text-sm font-bold text-slate-800">
                {isTa ? 'சந்தை தகவல்களை ஏற்றுவதில் பிழை' : 'Unable to connect to marketplace.'}
              </p>
              <button
                onClick={loadPublicListings}
                className="px-4 py-2 bg-emerald-700 text-white rounded-lg text-xs font-semibold"
              >
                {isTa ? 'மீண்டும் முயற்சி செய்' : 'Retry'}
              </button>
            </div>
          ) : listings.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
              <Package className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-base font-bold text-slate-800">
                {isTa ? 'தற்போது பொருத்தமான விளைபொருட்கள் இல்லை' : 'No produce found matching your filters.'}
              </p>
              <p className="text-xs text-slate-500">
                {isTa
                  ? 'வடிகட்டிகளை மாற்றி பார்க்கவும் அல்லது புதிய விளைபொருட்களை பதிவு செய்யவும்.'
                  : 'Try selecting All Districts or resetting the organic filter.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {listings.map((item) => (
                <div
                  key={item.listingId}
                  className="bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden relative"
                >
                  {/* Photo Preview if Available */}
                  {item.photoUrls && item.photoUrls.length > 0 && (
                    <div className="h-44 w-full overflow-hidden bg-slate-100 relative">
                      <img
                        src={item.photoUrls[0]}
                        alt={item.crop}
                        className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                      <div className="absolute top-2 right-2">
                        <button
                          onClick={() => {
                            setReportingListing(item);
                            setReportSuccessMessage(null);
                          }}
                          className="p-1.5 rounded-full bg-slate-900/60 hover:bg-slate-900 text-white backdrop-blur-xs transition-all shadow-xs"
                          title={isTa ? 'இப்பதிவை புகாரளி' : 'Report this listing'}
                        >
                          <Flag className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="p-5 space-y-3">
                    {/* Header Row: Category, Demo Badge, Status & Organic Seal */}
                    <div className="flex items-center justify-between gap-1.5 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                          {item.category}
                        </span>

                        {/* Inventory status badge */}
                        {item.quantity <= 0 || item.listingStatus === 'out_of_stock' ? (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-800 border border-red-200">
                            {isTa ? 'கையிருப்பு தீர்ந்தது' : 'Out of Stock'}
                          </span>
                        ) : item.listingStatus === 'expired' ? (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                            {isTa ? 'காலாவதியானது' : 'Expired'}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            {isTa ? 'விற்பனைக்கு உள்ளது' : 'Active'}
                          </span>
                        )}
                      </div>

                      {/* Report button if no image */}
                      {(!item.photoUrls || item.photoUrls.length === 0) && (
                        <button
                          onClick={() => {
                            setReportingListing(item);
                            setReportSuccessMessage(null);
                          }}
                          className="p-1 text-slate-400 hover:text-red-600 rounded-md transition-colors"
                          title={isTa ? 'இப்பதிவை புகாரளி' : 'Report this listing'}
                        >
                          <Flag className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    {/* Produce Name & Variety */}
                    <div>
                      <h3 className="text-lg font-extrabold text-slate-900 leading-snug">
                        {item.crop}
                      </h3>
                      {item.variety && (
                        <p className="text-xs text-emerald-700 font-semibold">{item.variety}</p>
                      )}
                    </div>

                    {/* Price and Stock Box */}
                    <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-100 flex items-center justify-between">
                      <div>
                        <div className="text-[11px] text-emerald-800 font-medium">{isTa ? 'நேரடி பண்ணை விலை' : 'Farm Gate Price'}</div>
                        <div className="text-xl font-black text-emerald-950">
                          ₹{item.pricePerUnit.toLocaleString('en-IN')}{' '}
                          <span className="text-xs font-semibold text-emerald-800">/ {item.unit}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[11px] text-emerald-800 font-medium">{isTa ? 'கையிருப்பு' : 'Available Stock'}</div>
                        <div className="text-sm font-bold text-emerald-900">
                          {item.quantity} {item.unit}
                        </div>
                      </div>
                    </div>

                    {/* Location, Service Area & Delivery */}
                    <div className="space-y-1.5 text-xs text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>
                          {item.village ? `${item.village}, ` : ''}
                          <strong className="text-slate-800">{item.district}</strong>
                        </span>
                      </div>
                      {item.serviceArea && (
                        <div className="flex items-center gap-1.5 text-emerald-800">
                          <Truck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          <span>{isTa ? 'விநியோக பகுதி:' : 'Service Area:'} <strong>{item.serviceArea}</strong></span>
                        </div>
                      )}
                      <div className="flex items-center gap-1.5">
                        <Package className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{item.fulfillmentModes.join(' • ')}</span>
                      </div>
                      {item.harvestDate && (
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span>{isTa ? 'அறுவடை:' : 'Harvested:'} {item.harvestDate}</span>
                        </div>
                      )}
                    </div>

                    {/* Description */}
                    {item.description && (
                      <p className="text-xs text-slate-600 line-clamp-2 italic pt-1 border-t border-slate-100">
                        "{item.description}"
                      </p>
                    )}
                  </div>

                  {/* Card Footer: Order Request Action & Farmer Direct Contacts */}
                  <div className="p-4 bg-slate-50/80 border-t border-slate-100 space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <div>
                        <span className="text-slate-500">{isTa ? 'உழவர்:' : 'Farmer:'} </span>
                        <strong className="text-slate-800">{item.farmerName}</strong>
                      </div>
                      {item.inquiryCount > 0 && (
                        <span className="text-[11px] text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          💬 {item.inquiryCount} {isTa ? 'விசாரணைகள்' : 'orders/inquiries'}
                        </span>
                      )}
                    </div>

                    {/* Primary Order Request Action */}
                    <button
                      disabled={item.quantity <= 0 || item.listingStatus === 'out_of_stock'}
                      onClick={() => {
                        setOrderModalListing(item);
                        setCompletedOrder(null);
                        setOrderSubmitError(null);
                        setOrderForm({
                          buyerName: user?.name || '',
                          buyerPhone: user?.phone || '',
                          requestedQuantity: Math.min(1, Math.max(1, item.quantity)),
                          fulfillmentPreference: item.fulfillmentModes[0] || 'Farm Gate Pickup',
                          deliveryAddress: '',
                          message: ''
                        });
                      }}
                      className="w-full flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold text-xs shadow-md transition-all"
                    >
                      <ShoppingBag className="w-4 h-4" />
                      <span>
                        {item.quantity <= 0
                          ? isTa ? 'கையிருப்பு இல்லை' : 'Out of Stock'
                          : isTa ? 'முன்பதிவு / விசாரணை செய்க' : 'Place Order Request'}
                      </span>
                    </button>

                    {/* Direct Connect Buttons (Only if Farmer Granted Explicit Consent) */}
                    {item.showContactToBuyers ? (
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => handleBuyerContact(item, 'whatsapp')}
                          className="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-2xs"
                        >
                          <MessageCircle className="w-3.5 h-3.5" />
                          <span>WhatsApp</span>
                        </button>
                        <button
                          onClick={() => handleBuyerContact(item, 'call')}
                          className="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-300 text-slate-800 font-bold text-xs transition-all shadow-2xs"
                        >
                          <Phone className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{isTa ? 'நேரடி அழைப்பு' : 'Direct Call'}</span>
                        </button>
                      </div>
                    ) : (
                      <div className="p-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 flex items-center justify-center gap-1.5 text-[11px] font-semibold">
                        <Shield className="w-3.5 h-3.5 text-emerald-700" />
                        <span>{isTa ? 'தொலைபேசி எண் பாதுகாக்கப்பட்டுள்ளது' : 'Contact Protected (Send In-App Enquiry)'}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* FARMER DASHBOARD (My Produce Listings & Incoming Buyer Orders) */}
      {activeTab === 'my_listings' && (
        <div className="space-y-6">
          {/* Sub Navigation Bar for Farmer Dashboard */}
          <div className="flex items-center justify-between flex-wrap gap-3 pb-3 border-b border-slate-200">
            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl">
              <button
                onClick={() => setFarmerSubTab('listings')}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  farmerSubTab === 'listings'
                    ? 'bg-white text-emerald-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Package className="w-3.5 h-3.5" />
                <span>{isTa ? 'என் விளைபொருட்கள்' : 'My Produce Listings'} ({myListings.length})</span>
              </button>
              <button
                onClick={() => setFarmerSubTab('orders')}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                  farmerSubTab === 'orders'
                    ? 'bg-white text-emerald-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ShoppingBag className="w-3.5 h-3.5" />
                <span>{isTa ? 'வந்த ஆர்டர்கள்' : 'Received Orders'} ({farmerOrders.length})</span>
              </button>
            </div>

            {farmerSubTab === 'listings' && (
              <button
                onClick={() => {
                  setEditingListing(null);
                  setFormData(initialForm);
                  setIsCreateModalOpen(true);
                }}
                className="px-4 py-2 rounded-xl bg-emerald-700 text-white font-bold text-xs hover:bg-emerald-800 shadow-xs flex items-center gap-1.5"
              >
                <PlusCircle className="w-4 h-4" />
                <span>{isTa ? 'புதிய விளைபொருள்' : 'New Listing'}</span>
              </button>
            )}
          </div>

          {/* SUB-VIEW 1: MY PRODUCE LISTINGS */}
          {farmerSubTab === 'listings' && (
            <div>
              {isLoadingMyListings ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-slate-700">Loading your produce...</p>
                </div>
              ) : myListings.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
                  <Package className="w-10 h-10 text-slate-300 mx-auto" />
                  <p className="text-base font-bold text-slate-800">
                    {isTa ? 'நீங்கள் இதுவரை எந்த விளைபொருளையும் பதிவேற்றவில்லை' : 'You have not listed any produce yet.'}
                  </p>
                  <button
                    onClick={() => {
                      setEditingListing(null);
                      setFormData(initialForm);
                      setIsCreateModalOpen(true);
                    }}
                    className="px-4 py-2 rounded-xl bg-emerald-700 text-white font-bold text-xs"
                  >
                    {isTa ? 'முதல் விளைபொருளை பதிவேற்றுக' : 'Create First Listing'}
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {myListings.map((l) => (
                    <div
                      key={l.listingId}
                      className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4"
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${
                            l.listingStatus === 'active'
                              ? 'bg-emerald-100 text-emerald-800'
                              : l.listingStatus === 'sold_out'
                              ? 'bg-slate-100 text-slate-600'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {l.listingStatus.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">{l.listingId}</span>
                      </div>

                      <div>
                        <h3 className="text-base font-bold text-slate-900">{l.crop}</h3>
                        {l.variety && <p className="text-xs text-emerald-700">{l.variety}</p>}
                      </div>

                      <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-slate-50 text-xs">
                        <div>
                          <span className="text-slate-500">Stock:</span>
                          <div className="font-bold text-slate-800">{l.quantity} {l.unit}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">Price:</span>
                          <div className="font-bold text-slate-800">₹{l.pricePerUnit} / {l.unit}</div>
                        </div>
                      </div>

                      {/* Metrics */}
                      <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5 text-slate-400" />
                          {l.viewCount} views
                        </span>
                        <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                          <MessageCircle className="w-3.5 h-3.5" />
                          {l.inquiryCount} buyer inquiries
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="grid grid-cols-2 gap-2 pt-2">
                        <button
                          onClick={() => {
                            setEditingListing(l);
                            setFormData({
                              crop: l.crop,
                              variety: l.variety || '',
                              category: l.category,
                              district: l.district,
                              village: l.village || '',
                              quantity: l.quantity,
                              unit: l.unit,
                              pricePerUnit: l.pricePerUnit,
                              isOrganicCertified: l.isOrganicCertified,
                              certificationBody: l.certificationBody || '',
                              harvestDate: l.harvestDate || '',
                              availableUntil: l.availableUntil || '',
                              fulfillmentModes: l.fulfillmentModes || ['Farm Gate Pickup'],
                              serviceArea: l.serviceArea || '',
                              photoUrls: l.photoUrls || [],
                              showContactToBuyers: l.showContactToBuyers || false,
                              description: l.description || '',
                            });
                            setIsCreateModalOpen(true);
                          }}
                          className="py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center gap-1"
                        >
                          <Edit className="w-3.5 h-3.5" />
                          <span>{isTa ? 'திருத்து' : 'Edit'}</span>
                        </button>
                        <button
                          onClick={() => handleDeleteListing(l.listingId)}
                          className="py-2 px-3 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs flex items-center justify-center gap-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>{isTa ? 'நீக்கு' : 'Delete'}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* SUB-VIEW 2: RECEIVED BUYER ORDERS & ENQUIRIES */}
          {farmerSubTab === 'orders' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    {isTa ? 'நுகர்வோரிடமிருந்து பெறப்பட்ட முன்பதிவுகள்' : 'Incoming Buyer Order Requests'}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {isTa
                      ? 'வாங்குபவர் விவரங்களை சரிபார்த்து ஆர்டரை ஏற்கவும் அல்லது தொடர்புகொள்ளவும்.'
                      : 'Review customer orders, phone contacts, delivery preferences, and confirm availability.'}
                  </p>
                </div>
                <button
                  onClick={loadFarmerOrders}
                  className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 border border-slate-200 rounded-lg transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoadingOrders ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {isLoadingOrders ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-slate-700">Loading incoming orders...</p>
                </div>
              ) : farmerOrders.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-2">
                  <ShoppingBag className="w-10 h-10 text-slate-300 mx-auto" />
                  <p className="text-base font-bold text-slate-800">
                    {isTa ? 'இதுவரை ஆர்டர் கோரிக்கைகள் எதுவும் பெறப்படவில்லை' : 'No order requests received yet.'}
                  </p>
                  <p className="text-xs text-slate-500">
                    {isTa ? 'வாங்குபவர்கள் உங்கள் விளைபொருளை முன்பதிவு செய்யும் போது இங்கே தோன்றும்.' : 'Buyer order requests on your listings will appear here.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {farmerOrders.map((ord) => (
                    <div
                      key={ord.orderId}
                      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3 hover:border-emerald-300 transition-all"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700">
                            {ord.orderId}
                          </span>
                          <span className="text-xs text-slate-400">
                            {new Date(ord.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                        <div>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                              ord.status === 'confirmed'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : ord.status === 'rejected'
                                ? 'bg-red-100 text-red-800 border border-red-300'
                                : ord.status === 'completed'
                                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                : 'bg-amber-100 text-amber-900 border border-amber-300'
                            }`}
                          >
                            {ord.status}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                        {/* Produce & Quantity */}
                        <div className="space-y-1">
                          <span className="text-slate-500 block">{isTa ? 'விளைபொருள் & அளவு:' : 'Produce & Qty:'}</span>
                          <div className="text-sm font-bold text-slate-900">{ord.crop}</div>
                          <div className="text-emerald-800 font-semibold">
                            {ord.requestedQuantity} {ord.unit} @ ₹{ord.pricePerUnit}/{ord.unit}
                          </div>
                          <div className="text-sm font-black text-slate-900">
                            Total: ₹{ord.totalEstimatedPrice.toLocaleString('en-IN')}
                          </div>
                        </div>

                        {/* Customer Info */}
                        <div className="space-y-1">
                          <span className="text-slate-500 block">{isTa ? 'வாங்குபவர் விபரம்:' : 'Buyer Contact:'}</span>
                          <div className="font-bold text-slate-900 flex items-center gap-1.5">
                            <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                            {ord.buyerName}
                          </div>
                          <div>
                            <a
                              href={`tel:${ord.buyerPhone}`}
                              className="text-emerald-700 font-semibold flex items-center gap-1 hover:underline"
                            >
                              <Phone className="w-3 h-3" />
                              {ord.buyerPhone}
                            </a>
                          </div>
                          {ord.fulfillmentPreference && (
                            <div className="text-slate-600 flex items-center gap-1">
                              <Truck className="w-3 h-3 text-slate-400" />
                              <span>{ord.fulfillmentPreference}</span>
                            </div>
                          )}
                        </div>

                        {/* Delivery address & Notes */}
                        <div className="space-y-1">
                          <span className="text-slate-500 block">{isTa ? 'குறிப்புகள் / முகவரி:' : 'Notes / Address:'}</span>
                          {ord.deliveryAddress && (
                            <p className="text-slate-700">📍 {ord.deliveryAddress}</p>
                          )}
                          {ord.message && (
                            <p className="text-slate-600 italic">"{ord.message}"</p>
                          )}
                        </div>
                      </div>

                      {/* Status Action Buttons */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-end gap-2">
                        {ord.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleUpdateOrderStatus(ord.orderId, 'rejected')}
                              className="px-3 py-1.5 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 text-xs font-semibold"
                            >
                              {isTa ? 'நிராகரி' : 'Decline'}
                            </button>
                            <button
                              onClick={() => handleUpdateOrderStatus(ord.orderId, 'confirmed')}
                              className="px-4 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold shadow-xs flex items-center gap-1.5"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>{isTa ? 'ஏற்கவும் (Confirm)' : 'Accept Order'}</span>
                            </button>
                          </>
                        )}
                        {ord.status === 'confirmed' && (
                          <button
                            onClick={() => handleUpdateOrderStatus(ord.orderId, 'completed')}
                            className="px-4 py-1.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold shadow-xs"
                          >
                            {isTa ? 'நிறைவு செய்யப்பட்டது (Completed)' : 'Mark as Completed'}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* CUSTOMER PLACE ORDER REQUEST MODAL */}
      {orderModalListing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative my-8 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-emerald-700" />
                <h3 className="text-lg font-bold text-slate-900">
                  {isTa ? 'விளைபொருள் முன்பதிவு / விசாரணை' : 'Place Produce Order Request'}
                </h3>
              </div>
              <button
                onClick={() => setOrderModalListing(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {completedOrder ? (
              <div className="space-y-4 py-2 text-center">
                <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-7 h-7" />
                </div>
                <h4 className="text-lg font-extrabold text-slate-900">
                  {isTa ? 'முன்பதிவு கோரிக்கை அனுப்பப்பட்டது!' : 'Order Request Submitted!'}
                </h4>
                <p className="text-xs text-slate-600 max-w-sm mx-auto leading-relaxed">
                  {isTa
                    ? `உங்கள் ஆர்டர் கோரிக்கை எண் #${completedOrder.orderId} விவசாயி ${orderModalListing.farmerName} அவர்களுக்கு வெற்றிகரமாக அனுப்பப்பட்டது.`
                    : `Your order request #${completedOrder.orderId} was sent directly to farmer ${orderModalListing.farmerName}.`}
                </p>
                <div className="p-3 bg-emerald-50 rounded-xl text-xs font-mono text-emerald-900 font-bold border border-emerald-200">
                  Order ID: {completedOrder.orderId} • Total: ₹{completedOrder.totalEstimatedPrice.toLocaleString('en-IN')}
                </div>
                <div className="flex items-center justify-center gap-3 pt-2">
                  <button
                    onClick={() => {
                      const cleanPhone = orderModalListing.farmerPhone.replace(/\D/g, '');
                      const fullPhone = cleanPhone.startsWith('91') ? cleanPhone : `91${cleanPhone}`;
                      const msg = encodeURIComponent(
                        `Vanakkam ${orderModalListing.farmerName}, I placed an order request (#${completedOrder.orderId}) for ${completedOrder.requestedQuantity} ${completedOrder.unit} of ${completedOrder.crop} on AgriBharat. Total: ₹${completedOrder.totalEstimatedPrice}. Please confirm availability.`
                      );
                      window.open(`https://wa.me/${fullPhone}?text=${msg}`, '_blank');
                    }}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs"
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span>WhatsApp Farmer</span>
                  </button>
                  <button
                    onClick={() => setOrderModalListing(null)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                  >
                    {isTa ? 'மூடுக' : 'Close'}
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmitOrderRequest} className="space-y-4 text-xs sm:text-sm">
                {/* Purchase Enquiry & Direct Reservation Notice */}
                <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 flex items-start gap-2.5 text-xs text-amber-950">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <strong className="font-bold text-amber-900 block">
                      {isTa ? 'கவனத்திற்கு: நேரடி விசாரணை அறிவிப்பு' : 'Notice: Direct Purchase Enquiry Only'}
                    </strong>
                    <p className="text-[11px] text-amber-800 leading-relaxed">
                      {isTa
                        ? 'இந்த பதிவு விவசாயிக்கான கொள்முதல் விருப்ப விசாரணை மட்டுமே. இது உறுதிப்படுத்தப்பட்ட ஆர்டரோ, உத்தரவாத விநியோகமோ அல்லது ஆன்லைன் பணப் பரிவர்த்தனையோ அல்ல. விவசாயி இருப்பு மற்றும் விநியோகத்தை சரிபார்த்து உங்களை தொடர்புகொள்வார். தளத்தில் எந்தவித ஆன்லைன் கட்டணமும் வசூலிக்கப்படாது.'
                        : 'This submission is a purchase enquiry and direct reservation request to the farmer. It is NOT a confirmed order, completed payment, or guaranteed delivery. The farmer will review stock availability and contact you directly. No online payment is collected on this platform.'}
                    </p>
                  </div>
                </div>

                {/* Produce Summary Header */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] text-slate-500 block">Produce:</span>
                    <strong className="text-slate-900 font-bold">{orderModalListing.crop}</strong>
                    <div className="text-xs text-slate-600">Farmer: {orderModalListing.farmerName}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-slate-500 block">Price:</span>
                    <strong className="text-emerald-800 font-black text-sm">
                      ₹{orderModalListing.pricePerUnit} / {orderModalListing.unit}
                    </strong>
                    <div className="text-[11px] text-slate-500">Max stock: {orderModalListing.quantity} {orderModalListing.unit}</div>
                  </div>
                </div>

                {orderSubmitError && (
                  <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                    <span>{orderSubmitError}</span>
                  </div>
                )}

                {/* Buyer Name & Phone */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">
                      {isTa ? 'உங்கள் பெயர் *' : 'Your Name *'}
                    </label>
                    <input
                      type="text"
                      required
                      value={orderForm.buyerName}
                      onChange={(e) => setOrderForm({ ...orderForm, buyerName: e.target.value })}
                      placeholder="e.g. Ramesh Kumar"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">
                      {isTa ? 'கைபேசி எண் *' : 'Contact Phone *'}
                    </label>
                    <input
                      type="tel"
                      required
                      value={orderForm.buyerPhone}
                      onChange={(e) => setOrderForm({ ...orderForm, buyerPhone: e.target.value })}
                      placeholder="e.g. 9876543210"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                {/* Requested Quantity & Live Total Calculation */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">
                      {isTa ? `தேவைப்படும் அளவு (${orderModalListing.unit}) *` : `Quantity (${orderModalListing.unit}) *`}
                    </label>
                    <input
                      type="number"
                      min="1"
                      max={orderModalListing.quantity}
                      required
                      value={orderForm.requestedQuantity}
                      onChange={(e) => setOrderForm({ ...orderForm, requestedQuantity: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-bold text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">
                      {isTa ? 'மொத்த மதிப்பீடு' : 'Estimated Total'}
                    </label>
                    <div className="px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-950 font-black text-sm">
                      ₹{((orderForm.requestedQuantity || 0) * orderModalListing.pricePerUnit).toLocaleString('en-IN')}
                    </div>
                  </div>
                </div>

                {/* Fulfillment Preference */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'பெறும் முறை (Fulfillment Mode)' : 'Fulfillment Preference'}
                  </label>
                  <select
                    value={orderForm.fulfillmentPreference}
                    onChange={(e) => setOrderForm({ ...orderForm, fulfillmentPreference: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  >
                    {orderModalListing.fulfillmentModes.map((fm) => (
                      <option key={fm} value={fm}>{fm}</option>
                    ))}
                  </select>
                </div>

                {/* Delivery Address */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'டெலிவரி முகவரி / தாலுகா' : 'Delivery Address / Area'}
                  </label>
                  <input
                    type="text"
                    value={orderForm.deliveryAddress || ''}
                    onChange={(e) => setOrderForm({ ...orderForm, deliveryAddress: e.target.value })}
                    placeholder="e.g. Kumbakonam Town / Farm Gate visit"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>

                {/* Message to Farmer */}
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'விவசாயிக்கான செய்தி' : 'Message to Farmer (Optional)'}
                  </label>
                  <textarea
                    rows={2}
                    value={orderForm.message || ''}
                    onChange={(e) => setOrderForm({ ...orderForm, message: e.target.value })}
                    placeholder="e.g. Looking to collect this weekend; please confirm grain condition..."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setOrderModalListing(null)}
                    className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold text-xs"
                  >
                    {isTa ? 'ரத்து செய்' : 'Cancel'}
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingOrder}
                    className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
                  >
                    {isSubmittingOrder ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    <span>{isTa ? 'ஆர்டர் கோரிக்கை அனுப்புக' : 'Send Order Request'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* CREATE / EDIT PRODUCE MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl my-8 relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Store className="w-5 h-5 text-emerald-700" />
                <h3 className="text-lg font-bold text-slate-900">
                  {editingListing
                    ? isTa ? 'விளைபொருள் விபரங்களை மாற்று' : 'Edit Produce Listing'
                    : isTa ? 'புதிய விளைபொருள் விற்பனை பதிவு' : 'List Farm Produce for Direct Sale'}
                </h3>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {submitError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{submitError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitProduce} className="space-y-4 text-xs sm:text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'விளைபொருள் பெயர் *' : 'Produce Name *'}
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.crop}
                    onChange={(e) => setFormData({ ...formData, crop: e.target.value })}
                    placeholder="e.g. Traditional Black Rice / Karuppu Kavuni"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'பிரிவு (Category) *' : 'Category *'}
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  >
                    <option value="Cereals">Cereals (தானியங்கள்)</option>
                    <option value="Pulses">Pulses (பயறு வகைகள்)</option>
                    <option value="Vegetables">Vegetables (காய்கறிகள்)</option>
                    <option value="Fruits">Fruits (பழங்கள்)</option>
                    <option value="Spices">Spices (மசாலாப் பொருட்கள்)</option>
                    <option value="Oilseeds">Oilseeds (எண்ணெய் வித்துக்கள்)</option>
                    <option value="Value Added">Value Added Products</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'ரகம் (Variety)' : 'Variety / Breed'}
                  </label>
                  <input
                    type="text"
                    value={formData.variety || ''}
                    onChange={(e) => setFormData({ ...formData, variety: e.target.value })}
                    placeholder="e.g. Mappillai Samba / Salem Organic"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'கிராமம் / இருப்பிடம்' : 'Village / Taluk'}
                  </label>
                  <input
                    type="text"
                    value={formData.village || ''}
                    onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                    placeholder="e.g. Pillaiyarpatti"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              {/* Quantity, Unit & Price */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'அளவு (Qty) *' : 'Quantity *'}
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'அளவீடு *' : 'Unit *'}
                  </label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  >
                    <option value="Quintal">Quintal</option>
                    <option value="Bags (50kg)">Bags (50kg)</option>
                    <option value="kg">kg</option>
                    <option value="Tonnes">Tonnes</option>
                    <option value="Litres">Litres</option>
                    <option value="Dozen">Dozen</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'விலை (₹/Unit) *' : 'Price (₹) *'}
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.pricePerUnit}
                    onChange={(e) => setFormData({ ...formData, pricePerUnit: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-bold text-emerald-800"
                  />
                </div>
              </div>

              {/* Organic Checkbox */}
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-emerald-950">
                  <input
                    type="checkbox"
                    checked={formData.isOrganicCertified}
                    onChange={(e) => setFormData({ ...formData, isOrganicCertified: e.target.checked })}
                    className="rounded-sm text-emerald-700 focus:ring-emerald-500 w-4 h-4"
                  />
                  <span>{isTa ? 'இயற்கை சான்றளிக்கப்பட்ட விளைபொருள் (Certified Organic)' : 'Certified Organic Produce'}</span>
                </label>

                {formData.isOrganicCertified && (
                  <div>
                    <input
                      type="text"
                      value={formData.certificationBody || ''}
                      onChange={(e) => setFormData({ ...formData, certificationBody: e.target.value })}
                      placeholder="e.g. TNOCD Scope Certificate / PGS-India Green"
                      className="w-full px-3 py-1.5 bg-white border border-emerald-200 rounded-lg text-xs"
                    />
                  </div>
                )}
              </div>

              {/* Service Area */}
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  {isTa ? 'விநியோக பகுதி (Service / Delivery Area)' : 'Service / Delivery Area'}
                </label>
                <input
                  type="text"
                  value={formData.serviceArea || ''}
                  onChange={(e) => setFormData({ ...formData, serviceArea: e.target.value })}
                  placeholder={isTa ? 'எ.கா: ஆத்தூர் / சேலம் 25 கி.மீ சுற்றளவில் அல்லது தமிழ்நாடு முழுவதும் பார்சல்' : 'e.g. Within 25 km of Attur / Salem or Tamil Nadu courier'}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                />
              </div>

              {/* Photo URL */}
              <div>
                <label className="font-semibold text-slate-700 block mb-1 flex items-center gap-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-slate-500" />
                  <span>{isTa ? 'விளைபொருள் புகைப்பட URL' : 'Produce Photo URL'}</span>
                </label>
                <input
                  type="url"
                  value={(formData.photoUrls && formData.photoUrls[0]) || ''}
                  onChange={(e) => setFormData({ ...formData, photoUrls: e.target.value.trim() ? [e.target.value.trim()] : [] })}
                  placeholder="https://images.unsplash.com/photo-..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                />
                <div className="flex items-center gap-2 mt-1.5 text-[11px] text-slate-500">
                  <span>{isTa ? 'மாதிரி படங்கள்:' : 'Quick samples:'}</span>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, photoUrls: ['https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=800&q=80'] })}
                    className="text-emerald-700 hover:underline font-medium"
                  >
                    Rice
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, photoUrls: ['https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=800&q=80'] })}
                    className="text-emerald-700 hover:underline font-medium"
                  >
                    Tomato
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, photoUrls: ['https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80'] })}
                    className="text-emerald-700 hover:underline font-medium"
                  >
                    Turmeric
                  </button>
                </div>
              </div>

              {/* Direct Contact Privacy Consent Checkbox */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <label className="flex items-start gap-2.5 cursor-pointer font-semibold text-slate-900 text-xs">
                  <input
                    type="checkbox"
                    checked={formData.showContactToBuyers || false}
                    onChange={(e) => setFormData({ ...formData, showContactToBuyers: e.target.checked })}
                    className="rounded-sm text-emerald-700 focus:ring-emerald-500 w-4 h-4 mt-0.5"
                  />
                  <div>
                    <span>
                      {isTa
                        ? 'நேரடி தொடர்பு அனுமதி (Explicit Consent): எனது தொலைபேசி / வாட்ஸ்அப் எண்ணை வாடிக்கையாளர்களுக்கு நேரடியாக காட்ட ஒப்புதல் அளிக்கிறேன்.'
                        : 'Explicit Consent: Allow prospective buyers to see my direct phone & WhatsApp number publicly.'}
                    </span>
                    <p className="text-[11px] text-slate-500 font-normal mt-0.5">
                      {isTa
                        ? '🛡️ இதனை தேர்வு செய்யாவிட்டால் உங்கள் கைபேசி எண் பொது பார்வையில் இருந்து பாதுகாக்கப்படும்; வாடிக்கையாளர்கள் தளம் வழியான விசாரணைக் கோரிக்கைகள் மட்டுமே அனுப்ப முடியும்.'
                        : '🛡️ If unchecked, your direct phone number remains protected from public display, and buyers will reach you securely through in-app enquiries.'}
                    </p>
                  </div>
                </label>
              </div>

              {/* Description */}
              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  {isTa ? 'விளைபொருள் தரம் மற்றும் விபரங்கள்' : 'Produce Quality & Description'}
                </label>
                <textarea
                  rows={3}
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="e.g. Sun-dried to 14% moisture, direct from farm gate, ready for delivery or pickup..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold text-xs"
                >
                  {isTa ? 'ரத்து செய்' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
                >
                  {isSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>
                    {editingListing
                      ? isTa ? 'விபரங்களை சேமி' : 'Save Changes'
                      : isTa ? 'விளைபொருளை வெளியிடவும்' : 'Publish Listing'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* REPORT LISTING MODAL */}
      {reportingListing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 text-red-600">
                <Flag className="w-5 h-5" />
                <h3 className="text-base font-bold text-slate-900">
                  {isTa ? 'விளைபொருள் பதிவை புகாரளி' : 'Report Marketplace Listing'}
                </h3>
              </div>
              <button
                onClick={() => {
                  setReportingListing(null);
                  setReportSuccessMessage(null);
                }}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {reportSuccessMessage ? (
              <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 text-xs text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <p className="font-bold">{reportSuccessMessage}</p>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4 text-xs sm:text-sm">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <span className="text-slate-500 block">{isTa ? 'பட்டியல்:' : 'Listing:'}</span>
                  <strong className="text-slate-900 font-bold">{reportingListing.crop}</strong>
                  <span className="text-slate-500 ml-2">({reportingListing.farmerName} • {reportingListing.district})</span>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'புகாருக்கான காரணம் *' : 'Reason for Report *'}
                  </label>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value as any)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                  >
                    <option value="spam">{isTa ? 'தேவையற்ற பதிவு / ஸ்பேம் (Spam)' : 'Spam or Duplicate Listing'}</option>
                    <option value="fake_price">{isTa ? 'தவறான / போலி விலை (Fake Price)' : 'Unrealistic or Fake Price'}</option>
                    <option value="misleading_claims">{isTa ? 'தவறான இயற்கை சான்றிதழ் உரிமைகோரல்' : 'Misleading Claims / Fake Organic Claims'}</option>
                    <option value="expired_produce">{isTa ? 'காலாவதியான / சேதமடைந்த விளைபொருள்' : 'Expired / Spoiled Produce'}</option>
                    <option value="other">{isTa ? 'பிற காரணங்கள் (Other)' : 'Other Concerns'}</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">
                    {isTa ? 'விளக்கம் (விரும்பினால்)' : 'Details / Remarks (Optional)'}
                  </label>
                  <textarea
                    rows={3}
                    value={reportDetails}
                    onChange={(e) => setReportDetails(e.target.value)}
                    placeholder={isTa ? 'சிக்கல் பற்றிய கூடுதல் தகவல்களை பகிரவும்...' : 'Describe why this listing should be reviewed by moderation...'}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                  />
                </div>

                <p className="text-[11px] text-slate-500 italic">
                  🛡️ {isTa
                    ? '3 முறைக்கு மேல் புகாரளிக்கப்பட்ட பதிவுகள் தானாகவே மதிப்பாய்வு நிலைக்கு மாற்றப்பட்டு மறைக்கப்படும்.'
                    : 'Listings receiving 3 or more verified reports are automatically flagged for admin review.'}
                </p>

                <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setReportingListing(null)}
                    className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold text-xs"
                  >
                    {isTa ? 'ரத்து' : 'Cancel'}
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingReport}
                    className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
                  >
                    {isSubmittingReport && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    <span>{isTa ? 'புகார் அனுப்பு' : 'Submit Report'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

import type { Language, NavTab } from '../types';
import {
  CENTRAL_LOCALE_REGISTRY,
  getLocaleMetadata,
  isRTL,
} from './localeRegistry';
import { hiTranslations } from './locales/hi';
import {
  teTranslations,
  knTranslations,
  mlTranslations,
  mrTranslations,
  bnTranslations,
  guTranslations,
  paTranslations,
  orTranslations,
  asTranslations,
  urTranslations,
} from './locales/regionalCore';
import {
  ksTranslations,
  sdTranslations,
  neTranslations,
  saTranslations,
  brxTranslations,
  doiTranslations,
  kokTranslations,
  maiTranslations,
  mniTranslations,
  satTranslations,
} from './locales/scheduledEssential';

export interface TranslationSchema {
  appName: string;
  appTagline: string;
  sampleDataNotice: string;
  sampleBadge: string;
  liveBadge: string;
  nav: Record<NavTab, string>;
  common: {
    loading: string;
    loadingDesc: string;
    emptyTitle: string;
    emptyDesc: string;
    errorTitle: string;
    errorDesc: string;
    retry: string;
    viewDetails: string;
    bookSlot: string;
    askAi: string;
    refresh: string;
    status: string;
    date: string;
    time: string;
    location: string;
    switchState: string;
    editProfile?: string;
    saveChanges?: string;
    cancel?: string;
  };
  auth: {
    signIn: string;
    signUp: string;
    signOut: string;
    loginTitle: string;
    loginSubtitle: string;
    registerTitle: string;
    registerSubtitle: string;
    mobileLabel: string;
    passwordLabel: string;
    confirmPasswordLabel: string;
    fullNameLabel: string;
    villageLabel: string;
    districtLabel: string;
    stateLabel: string;
    prefLangLabel: string;
    selectRole: string;
    farmerRole: string;
    staffRole: string;
    farmerRoleDesc: string;
    staffRoleDesc: string;
    dontHaveAccount: string;
    alreadyHaveAccount: string;
    loginBtn: string;
    registerBtn: string;
    loginSuccess: string;
    registerSuccess: string;
    demoFillFarmer: string;
    demoFillStaff: string;
    staffPortalTitle: string;
    staffPortalSubtitle: string;
    roleBadgeFarmer: string;
    roleBadgeStaff: string;
  };
  welcome: {
    greeting: string;
    farmerName: string;
    todayBadge: string;
    tagline: string;
    statCrop: string;
    statSoil: string;
    statIrrigation: string;
    statMandi: string;
    quickAssistantBtn: string;
    quickDiseaseBtn: string;
    quickMandiBtn: string;
  };
  dashboard: {
    title: string;
    subtitle: string;
    farmDetailsTitle: string;
    weatherTitle: string;
    irrigationTitle: string;
    cropHealthTitle: string;
    procurementTitle: string;
    marketPricesTitle: string;
    quickActionsTitle: string;
    labels: {
      farmerName: string;
      farmerId: string;
      landSize: string;
      soilType: string;
      primaryCrop: string;
      irrigationSource: string;
      acres: string;
      temperature: string;
      humidity: string;
      rainfallChance: string;
      windSpeed: string;
      soilMoisture: string;
      nextIrrigation: string;
      waterSaved: string;
      advice: string;
      healthScore: string;
      cropStage: string;
      lastScanned: string;
      bookingId: string;
      procurementCenter: string;
      quantity: string;
      bags: string;
      tokenNo: string;
      slotTime: string;
      confirmed: string;
      optimal: string;
      healthy: string;
      viewAllMandis: string;
      modalPrice: string;
      marketTrends: string;
    };
  };
  schemesPage: {
    title: string;
    subtitle: string;
    allCategories: string;
    stateCategory: string;
    centralCategory: string;
    insuranceCategory: string;
    irrigationCategory: string;
    machineryCategory: string;
    animalsCategory: string;
    searchPlaceholder: string;
    filterLevel: string;
    allLevels: string;
    filterLivestock: string;
    allAnimals: string;
    benefitsLabel: string;
    eligibilityLabel: string;
    documentsLabel: string;
    viewDetails: string;
    visitPortal: string;
    viewSource: string;
    verifiedNotice: string;
    verificationDate: string;
    statusActive: string;
    statusUnknown: string;
    statusClosed: string;
    statusUnverified: string;
    disclaimerModal: string;
    closeModal: string;
  };
  irrigationPage: {
    title: string;
    subtitle: string;
    locationCardTitle: string;
    savedLocation: string;
    noSavedLocation: string;
    detectGpsBtn: string;
    detectingGps: string;
    selectDistrictLabel: string;
    manualCoordsLabel: string;
    latLabel: string;
    lonLabel: string;
    savePrimaryConsent: string;
    saveLocationBtn: string;
    savingLocation: string;
    locationSavedSuccess: string;
    liveWeatherCardTitle: string;
    weatherSource: string;
    lastUpdated: string;
    temp: string;
    humidity: string;
    rainProbability: string;
    forecastPrecipitation: string;
    et0Title: string;
    et0Desc: string;
    soilMoistureTitle: string;
    soilMoistureDisclaimer: string;
    soilMoistureUnavailable: string;
    depth0_7: string;
    depth7_28: string;
    depth28_100: string;
    refreshWeather: string;
    refreshing: string;
    loadingWeather: string;
    staleDataWarning: string;
    locationRequiredWarning: string;
    providerError: string;
    offlineWarning: string;
    cropSelection: string;
    growthStage: string;
    soilType: string;
    irrigationMethod: string;
    calculateBtn: string;
    calculating: string;
    rationaleTitle: string;
    waterDemandLabel: string;
    cropFactorLabel: string;
    estVolumeLabel: string;
    fieldAreaLabel: string;
    fieldAreaHelp: string;
    recIrrigateNow: string;
    recDelayReassess: string;
    recMonitorConditions: string;
    irrigationWindowLabel: string;
    grossDepthLabel: string;
    totalVolumeLabel: string;
    paddyWaterProtocolTitle: string;
    unitExplanationTitle: string;
    confidenceLabel: string;
    limitationsTitle: string;
    refreshAdvisoryBtn: string;
    noHardwareControlBanner: string;
    advisoryDisclaimer: string;
  };
}

export const translations: Record<'en' | 'ta', TranslationSchema> = {
  en: {
    appName: 'AgriBharat',
    appTagline: 'Smart Farming Intelligence & Agricultural Marketplace',
    sampleDataNotice: '⚠️ NOTICE: Information shown below is sample simulation data for demonstration during development. It does not represent live government/mandi records.',
    sampleBadge: 'DEMO DATA',
    liveBadge: 'SIMULATED',
    nav: {
      dashboard: 'Dashboard',
      assistant: 'Farming Assistant',
      weather: 'Weather Forecast',
      irrigation: 'Smart Irrigation',
      disease: 'Disease Detection',
      recommendations: 'Crop Recommendations',
      market: 'Market Mandi Prices',
      schemes: 'Govt Schemes',
      support_hub: 'Farmer Support Hub',
      special_operation: 'Special Operation: First Step to First Sale',
      marketplace: 'Direct Marketplace',
      agri_entrepreneurship: 'Agri Entrepreneurship',
      value_addition: 'Value-Added Products',
      procurement: 'Procurement Booking',
      queue: 'Queue Tracking',
      notifications: 'Notifications',
      profile: 'Farmer Profile',
      staff_portal: 'Staff Operations Portal',
    },
    common: {
      loading: 'Loading information...',
      loadingDesc: 'Fetching simulated agricultural records from the local system.',
      emptyTitle: 'No Records Found',
      emptyDesc: 'There are currently no active entries in this section.',
      errorTitle: 'Unable to Load Data',
      errorDesc: 'A temporary simulation error occurred. Please test the retry action.',
      retry: 'Try Again',
      viewDetails: 'View Details',
      bookSlot: 'Book Mandi Slot',
      askAi: 'Ask AI Assistant',
      refresh: 'Refresh',
      status: 'Status',
      date: 'Date',
      time: 'Time',
      location: 'Location',
      switchState: 'Simulate State:',
      editProfile: 'Edit Profile',
      saveChanges: 'Save Changes',
      cancel: 'Cancel',
    },
    auth: {
      signIn: 'Sign In',
      signUp: 'Register as Farmer',
      signOut: 'Log Out',
      loginTitle: 'Sign In to AgriBharat',
      loginSubtitle: 'Choose your role to access your farming tools or procurement staff operations.',
      registerTitle: 'Farmer Account Registration',
      registerSubtitle: 'Register with your verified mobile number to manage farm telemetry and mandi bookings.',
      mobileLabel: '10-Digit Mobile Number',
      passwordLabel: 'Password',
      confirmPasswordLabel: 'Confirm Password',
      fullNameLabel: 'Farmer Full Name',
      villageLabel: 'Village / Taluk',
      districtLabel: 'District',
      stateLabel: 'State',
      prefLangLabel: 'Preferred Language',
      selectRole: 'Select Your System Role',
      farmerRole: 'Farmer (உழவர்)',
      staffRole: 'Procurement Staff (அலுவலர்)',
      farmerRoleDesc: 'Access farm telemetry, crop advice, and direct mandi slot booking.',
      staffRoleDesc: 'Authorized staff for queue verification, weighbridge records & DBT approvals.',
      dontHaveAccount: "Don't have a farmer account yet?",
      alreadyHaveAccount: 'Already registered? Sign in here',
      loginBtn: 'Log In to Platform',
      registerBtn: 'Create Farmer Account',
      loginSuccess: 'Authentication successful! Welcome to the platform.',
      registerSuccess: 'Registration successful! Your Farmer ID has been created.',
      demoFillFarmer: 'Demo: Auto-fill Farmer',
      demoFillStaff: 'Demo: Auto-fill Staff (Admin)',
      staffPortalTitle: 'Mandi Procurement Centre Control Room',
      staffPortalSubtitle: 'Manage vehicle queues, grain moisture quality, weighbridge telemetry & direct DBT transfers.',
      roleBadgeFarmer: 'Farmer Account',
      roleBadgeStaff: 'Procurement Staff',
    },
    welcome: {
      greeting: 'Welcome back,',
      farmerName: 'Thiru. Selvakumar R.',
      todayBadge: 'Samba Season 2026 Active',
      tagline: 'Real-time agronomic telemetry, soil moisture status, and regulated procurement tracking for your field in Thanjavur.',
      statCrop: 'Samba Paddy (CR 1009 Sub 1)',
      statSoil: 'Clay Loam (pH 6.8 Optimal)',
      statIrrigation: 'Moisture 64% - Water Sparing',
      statMandi: 'Token #TN-DPC-042 (18 Oct)',
      quickAssistantBtn: 'Ask AI Agronomist',
      quickDiseaseBtn: 'Scan Leaf Disease',
      quickMandiBtn: 'Book Mandi Window',
    },
    dashboard: {
      title: 'Farmer Dashboard',
      subtitle: 'Overview of your field conditions, crop status, and mandi appointments.',
      farmDetailsTitle: 'Farm Profile',
      weatherTitle: 'Agri-Weather Forecast',
      irrigationTitle: 'Irrigation Advisory',
      cropHealthTitle: 'Crop Health Monitor',
      procurementTitle: 'Mandi Procurement Slot',
      marketPricesTitle: 'Live Mandi Market Prices',
      quickActionsTitle: 'Quick Farmer Actions',
      labels: {
        farmerName: 'Farmer Name',
        farmerId: 'Farmer ID',
        landSize: 'Land Holding',
        soilType: 'Soil Type',
        primaryCrop: 'Primary Crop',
        irrigationSource: 'Irrigation Source',
        acres: 'Acres',
        temperature: 'Temperature',
        humidity: 'Humidity',
        rainfallChance: 'Rain Probability',
        windSpeed: 'Wind Speed',
        soilMoisture: 'Soil Moisture',
        nextIrrigation: 'Next Scheduled Cycle',
        waterSaved: 'Water Saved This Week',
        advice: 'Advisory',
        healthScore: 'Health Score',
        cropStage: 'Growth Stage',
        lastScanned: 'Last Checked',
        bookingId: 'Token / Booking ID',
        procurementCenter: 'Regulated Mandi',
        quantity: 'Registered Crop',
        bags: 'Bags',
        tokenNo: 'Queue Token #',
        slotTime: 'Reporting Window',
        confirmed: 'Slot Confirmed',
        optimal: 'Moisture Adequate',
        healthy: 'Crop Healthy',
        viewAllMandis: 'Full Mandi Price Board →',
        modalPrice: 'Modal Price',
        marketTrends: 'Today’s Trend',
      },
    },
    schemesPage: {
      title: 'Govt Welfare Schemes',
      subtitle: 'Central & Tamil Nadu State Agricultural & Livestock Welfare Schemes & Official Portals',
      allCategories: 'All',
      stateCategory: 'State',
      centralCategory: 'Central',
      insuranceCategory: 'Insurance',
      irrigationCategory: 'Irrigation',
      machineryCategory: 'Machinery',
      animalsCategory: 'Animals & Livestock',
      searchPlaceholder: 'Search schemes by name, department, animal (cattle, goat, poultry) or keywords...',
      filterLevel: 'Govt Level',
      allLevels: 'All Levels',
      filterLivestock: 'Livestock / Animal',
      allAnimals: 'All Animals',
      benefitsLabel: 'Key Benefits & Subsidies',
      eligibilityLabel: 'Eligibility Criteria',
      documentsLabel: 'Required Documents',
      viewDetails: 'View Details',
      visitPortal: 'Visit Official Portal',
      viewSource: 'View Official Source',
      verifiedNotice: 'Verified Official Portal',
      verificationDate: 'Verified On',
      statusActive: 'Active',
      statusUnknown: 'Application Window Unknown',
      statusClosed: 'Closed',
      statusUnverified: 'Unverified',
      disclaimerModal: 'Official Statutory Notice: Final eligibility, subsidy sanctions, and fund allocations are determined solely by the competent officers of the respective government department. Always apply directly through the verified official government portals provided.',
      closeModal: 'Close Details',
    },
    irrigationPage: {
      title: 'Smart Irrigation Advisory',
      subtitle: 'Microclimate Evapotranspiration (ET₀) & Modelled Soil Physics (FAO-56 / TNAU)',
      locationCardTitle: 'Farm Location & Weather Station',
      savedLocation: 'Registered Primary Farm Location',
      noSavedLocation: 'No farm GPS location saved yet. Detect via browser or select your agricultural district.',
      detectGpsBtn: 'Detect Current Location (GPS)',
      detectingGps: 'Acquiring GPS fix...',
      selectDistrictLabel: 'Or Select Agricultural District',
      manualCoordsLabel: 'Enter Exact Farm GPS Coordinates',
      latLabel: 'Latitude (°N)',
      lonLabel: 'Longitude (°E)',
      savePrimaryConsent: 'I consent to save these coordinates as my primary farm location for automated agro-meteorological advisories.',
      saveLocationBtn: 'Save Farm Coordinates',
      savingLocation: 'Saving with consent...',
      locationSavedSuccess: 'Farm coordinates successfully saved to profile!',
      liveWeatherCardTitle: 'Live Agrometeorological Weather',
      weatherSource: 'Provider Source',
      lastUpdated: 'Observation Time',
      temp: 'Temperature',
      humidity: 'Relative Humidity',
      rainProbability: 'Rain Probability',
      forecastPrecipitation: 'Forecast Rain (24h)',
      et0Title: 'Reference Evapotranspiration (ET₀)',
      et0Desc: 'Atmospheric evaporative demand computed via FAO Penman-Monteith method.',
      soilMoistureTitle: 'Modelled Root-Zone Moisture (0-28cm)',
      soilMoistureDisclaimer: 'Numerical land-surface simulation (Open-Meteo). Not an in-situ physical sensor reading.',
      soilMoistureUnavailable: 'Soil moisture estimate unavailable',
      depth0_7: 'Surface (0-7 cm)',
      depth7_28: 'Root Zone (7-28 cm)',
      depth28_100: 'Deep Soil (28-100 cm)',
      refreshWeather: 'Refresh Weather',
      refreshing: 'Updating meteorological feed...',
      loadingWeather: 'Connecting to Open-Meteo satellite & meteorological models...',
      staleDataWarning: 'Notice: Displaying cached meteorological data due to network timeout.',
      locationRequiredWarning: 'Please configure or detect your farm coordinates below to fetch live meteorological data.',
      providerError: 'Live meteorological feed is temporarily unreachable. Please check connection and click Refresh.',
      offlineWarning: 'Your browser is currently offline. Real-time weather cannot be retrieved.',
      cropSelection: 'Crop Type',
      growthStage: 'Crop Phenological Stage',
      soilType: 'Soil Texture Class',
      irrigationMethod: 'Irrigation Delivery Method',
      calculateBtn: 'Compute Irrigation Advisory',
      calculating: 'Calculating Soil-Water Balance...',
      rationaleTitle: 'Agronomic Rationale & Observations:',
      waterDemandLabel: 'Daily Crop Water Demand',
      cropFactorLabel: 'Crop Factor (Kc)',
      estVolumeLabel: 'Est. Application Volume',
      fieldAreaLabel: 'Cultivated Field Area (Acres)',
      fieldAreaHelp: 'Enter cultivated land in acres to calculate total volumetric water requirement in litres (1 mm × 1 acre = 4,047 L).',
      recIrrigateNow: 'Irrigate Now',
      recDelayReassess: 'Delay and Reassess',
      recMonitorConditions: 'Monitor Conditions',
      irrigationWindowLabel: 'Recommended Irrigation Window (Local Time)',
      grossDepthLabel: 'Gross Application Depth',
      totalVolumeLabel: 'Total Application Volume',
      paddyWaterProtocolTitle: 'TNAU Lowland Basin Paddy Water Protocol',
      unitExplanationTitle: 'Agronomic Water Balance Principles',
      confidenceLabel: 'Calculation Confidence',
      limitationsTitle: 'Agronomic Limitations & Assumptions:',
      refreshAdvisoryBtn: 'Refresh Advisory',
      noHardwareControlBanner: 'Agronomic decision-support advisory tool. Does not physically operate valves, pumps, or electrical starters.',
      advisoryDisclaimer: 'Advisory Notice: Computed from agronomic water-balance rules (TNAU / FAO-56 Penman-Monteith). Modelled soil moisture is an agrometeorological estimate, not an in-situ IoT probe. Always verify soil crumb condition in the field before pumping.',
    },
  },
  ta: {
    appName: 'அக்ரிபாரத் (AgriBharat)',
    appTagline: 'ஸ்மார்ட் வேளாண் நுண்ணறிவு மற்றும் நேரடி வேளாண் சந்தை',
    sampleDataNotice: '⚠️ அறிவிப்பு: கீழே காட்டப்பட்டுள்ள தகவல்கள் வளர்ச்சி மற்றும் மாதிரி சோதனைகளுக்கானவை. இவை நேரடி அதிகாரப்பூர்வ அரசு அல்லது ஒழுங்குமுறை விற்பனைக்கூட பதிவுகள் அல்ல.',
    sampleBadge: 'மாதிரி தரவு',
    liveBadge: 'மாதிரி வடிவம்',
    nav: {
      dashboard: 'முகப்பு பலகை',
      assistant: 'விவசாய AI உதவியாளர்',
      weather: 'வானிலை முன்னறிவிப்பு',
      irrigation: 'நுண்ணீர் பாசன ஆலோசனை',
      disease: 'பயிர் நோய் கண்டறிதல்',
      recommendations: 'பயிர் பரிந்துரைகள்',
      market: 'சந்தை விலை நிலவரம்',
      schemes: 'அரசு நலத்திட்டங்கள்',
      support_hub: 'விவசாயிகள் உதவி மையம்',
      special_operation: 'சிறப்புத் திட்டம் (முதல் படி முதல் விற்பனை)',
      marketplace: 'உழவர் நேரடி சந்தை',
      agri_entrepreneurship: 'வேளாண் தொழில்முனைவு',
      value_addition: 'மதிப்புக்கூட்டப்பட்ட பொருட்கள்',
      procurement: 'கொள்முதல் முன்பதிவு',
      queue: 'வரிசை நிலை கண்காணிப்பு',
      notifications: 'அறிவிப்புகள்',
      profile: 'விவசாயி சுயவிவரம்',
      staff_portal: 'கொள்முதல் அலுவலர் தளம்',
    },
    common: {
      loading: 'தகவல் ஏற்றப்படுகிறது...',
      loadingDesc: 'வேளாண் மாதிரித் தகவல்கள் சேகரிக்கப்படுகின்றன.',
      emptyTitle: 'பதிவுகள் எதுவும் இல்லை',
      emptyDesc: 'இப்பிரிவில் தற்போது பதிவுகள் எதுவும் காணப்படவில்லை.',
      errorTitle: 'தகவல் பெற முடியவில்லை',
      errorDesc: 'மாதிரித் தரவை ஏற்றுவதில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.',
      retry: 'மீண்டும் முயற்சி செய்',
      viewDetails: 'விவரங்களை காண்க',
      bookSlot: 'கொள்முதல் நேரம் பதிவு செய்',
      askAi: 'AI உதவியாளரிடம் கேள்',
      refresh: 'புதுப்பி',
      status: 'நிலை',
      date: 'தேதி',
      time: 'நேரம்',
      location: 'இடம்',
      switchState: 'நிலை சோதனை:',
      editProfile: 'சுயவிவரம் திருத்து',
      saveChanges: 'மாற்றங்களைச் சேமிக்கவும்',
      cancel: 'ரத்து செய்',
    },
    auth: {
      signIn: 'உள்நுழைக',
      signUp: 'உழவர் புதிய பதிவு',
      signOut: 'வெளியேறு',
      loginTitle: 'அக்ரிபாரத் (AgriBharat) உள்நுழைவு',
      loginSubtitle: 'விவசாயி அல்லது கொள்முதல் மைய அலுவலராக உள்நுழையவும்.',
      registerTitle: 'புதிய உழவர் கணக்கு பதிவு',
      registerSubtitle: 'உங்கள் கைபேசி எண் மூலம் பதிவு செய்து நேரடி கொள்முதல் மற்றும் வானிலை ஆலோசனைகளை பெறுங்கள்.',
      mobileLabel: '10 இலக்க அலைபேசி எண்',
      passwordLabel: 'கடவுச்சொல்',
      confirmPasswordLabel: 'கடவுச்சொல்லை உறுதிசெய்க',
      fullNameLabel: 'விவசாயியின் முழுப்பெயர்',
      villageLabel: 'கிராமம் / தாலுகா',
      districtLabel: 'மாவட்டம்',
      stateLabel: 'மாநிலம்',
      prefLangLabel: 'விருப்ப மொழி',
      selectRole: 'உங்கள் பொறுப்பை தேர்வு செய்க',
      farmerRole: 'விவசாயி (Farmer)',
      staffRole: 'கொள்முதல் அலுவலர் (Staff)',
      farmerRoleDesc: 'விவசாய ஆலோசனை, பயிர் நோய் ஆய்வு மற்றும் நேரடி முன்பதிவு.',
      staffRoleDesc: 'ஒழுங்குமுறை விற்பனைக்கூட எடை மற்றும் வரிசை மேலாண்மை.',
      dontHaveAccount: 'புதிய உழவர் கணக்கு இல்லையா?',
      alreadyHaveAccount: 'ஏற்கனவே பதிவு செய்துள்ளீர்களா? உள்நுழைக',
      loginBtn: 'உள்நுழைக',
      registerBtn: 'புதிய கணக்கை உருவாக்குக',
      loginSuccess: 'உள்நுழைவு வெற்றிகரமாக முடிந்தது!',
      registerSuccess: 'பதிவு உறுதியானது! உழவர் அட்டை எண் வழங்கப்பட்டுள்ளது.',
      demoFillFarmer: 'மாதிரி: உழவர் விபரம்',
      demoFillStaff: 'மாதிரி: அலுவலர் விபரம் (Staff)',
      staffPortalTitle: 'நேரடி கொள்முதல் மைய கட்டுப்பாட்டு தளம்',
      staffPortalSubtitle: 'வாகன வரிசை, தானிய ஈரப்பதம், எடை மேடை பதிவு மற்றும் DBT வங்கி செலுத்துகை மேலாண்மை.',
      roleBadgeFarmer: 'விவசாயி',
      roleBadgeStaff: 'கொள்முதல் அலுவலர்',
    },
    welcome: {
      greeting: 'வணக்கம்,',
      farmerName: 'திரு. செல்வகுமார் ரா.',
      todayBadge: 'சம்பா பருவம் 2026 நடைமுறையில்',
      tagline: 'தஞ்சாவூர் கபிஸ்தலம் பகுதியில் உள்ள உங்கள் 3.5 ஏக்கர் நிலத்தின் தற்போதைய பாசன நிலை, பயிர் பாதுகாப்பு மற்றும் நேரடி கொள்முதல் விவரங்கள்.',
      statCrop: 'சம்பா நெல் (CR 1009 Sub 1)',
      statSoil: 'வண்டல் மண் (pH 6.8 நடுநிலை)',
      statIrrigation: 'ஈரப்பதம் 64% - நீர் சேமிப்பு',
      statMandi: 'டோக்கன் #TN-DPC-042 (18 அக்)',
      quickAssistantBtn: 'AI விவசாய ஆலோசனை',
      quickDiseaseBtn: 'இலை நோய் ஆய்வு',
      quickMandiBtn: 'நேரடி கொள்முதல் முன்பதிவு',
    },
    dashboard: {
      title: 'விவசாயி கட்டுப்பாட்டு பலகை',
      subtitle: 'உங்கள் நிலத்தின் வானிலை, பயிர் ஆரோக்கியம் மற்றும் ஒழுங்குமுறை கொள்முதல் விபரம்.',
      farmDetailsTitle: 'விவசாய நில விபரம்',
      weatherTitle: 'வேளாண் வானிலை',
      irrigationTitle: 'பாசன ஆலோசனை',
      cropHealthTitle: 'பயிர் ஆரோக்கிய கண்காணிப்பு',
      procurementTitle: 'நேரடி நெல்/தானிய கொள்முதல் முன்பதிவு',
      marketPricesTitle: 'சந்தை தினசரி விலை நிலவரம்',
      quickActionsTitle: 'விரைவு விவசாய சேவைகள்',
      labels: {
        farmerName: 'விவசாயி பெயர்',
        farmerId: 'உழவர் அட்டை எண்',
        landSize: 'நிலப்பரப்பு',
        soilType: 'மண் வகை',
        primaryCrop: 'முக்கிய பயிர்',
        irrigationSource: 'பாசன ஆதாரம்',
        acres: 'ஏக்கர்',
        temperature: 'வெப்பநிலை',
        humidity: 'காற்றின் ஈரப்பதம்',
        rainfallChance: 'மழை வாய்ப்பு',
        windSpeed: 'காற்றின் வேகம்',
        soilMoisture: 'மண் ஈரப்பதம்',
        nextIrrigation: 'அடுத்த பாசன நேரம்',
        waterSaved: 'சேமிக்கப்பட்ட நீர்',
        advice: 'பாசன பரிந்துரை',
        healthScore: 'ஆரோக்கிய மதிப்பு',
        cropStage: 'பயிர் வளர்ச்சி நிலை',
        lastScanned: 'கடைசி ஆய்வு',
        bookingId: 'முன்பதிவு அடையாள எண்',
        procurementCenter: 'ஒழுங்குமுறை விற்பனைக்கூடம்',
        quantity: 'பதிவு செய்யப்பட்ட பயிர்',
        bags: 'மூட்டைகள்',
        tokenNo: 'வரிசை எண் டோக்கன்',
        slotTime: 'அனுமதி நேரம்',
        confirmed: 'முன்பதிவு உறுதியானது',
        optimal: 'ஈரப்பதம் போதுமானது',
        healthy: 'பயிர் நலமாக உள்ளது',
        viewAllMandis: 'அனைத்து சந்தை நிலவரம் →',
        modalPrice: 'சராசரி விலை',
        marketTrends: 'இன்றைய போக்கு',
      },
    },
    schemesPage: {
      title: 'அரசு நலத்திட்டங்கள்',
      subtitle: 'மத்திய மற்றும் தமிழ்நாடு மாநில அரசு உழவர் & கால்நடை நலத்திட்டங்கள் மற்றும் நேரடி மானியங்கள்',
      allCategories: 'அனைத்தும்',
      stateCategory: 'மாநில அரசு',
      centralCategory: 'மத்திய அரசு',
      insuranceCategory: 'காப்பீடு',
      irrigationCategory: 'பாசனம்',
      machineryCategory: 'இயந்திரங்கள்',
      animalsCategory: 'கால்நடைகள் & வளர்ப்பு',
      searchPlaceholder: 'திட்டத்தின் பெயர், துறை, கால்நடை (மாடு, ஆடு, கோழி) அல்லது முக்கிய வார்த்தைகளால் தேடவும்...',
      filterLevel: 'அரசு நிலை',
      allLevels: 'அனைத்து நிலைகளும்',
      filterLivestock: 'கால்நடை வகை',
      allAnimals: 'அனைத்து கால்நடைகளும்',
      benefitsLabel: 'முக்கிய நன்மைகள் & மானியங்கள்',
      eligibilityLabel: 'தகுதி வரம்புகள்',
      documentsLabel: 'தேவையான ஆவணங்கள்',
      viewDetails: 'விவரங்களை காண்க',
      visitPortal: 'அதிகாரப்பூர்வ தளம் செல்க',
      viewSource: 'அரசு ஆதாரத்தை காண்க',
      verifiedNotice: 'சரிபார்க்கப்பட்ட அரசு தளம்',
      verificationDate: 'சரிபார்க்கப்பட்ட நாள்',
      statusActive: 'செயலில் உள்ளது',
      statusUnknown: 'விண்ணப்ப காலம் அறியப்படவில்லை',
      statusClosed: 'முடிவடைந்தது',
      statusUnverified: 'சரிபார்க்கப்படாதது',
      disclaimerModal: 'அதிகாரப்பூர்வ அறிவிப்பு: திட்ட மானிய ஒப்புதல் மற்றும் நிதி ஒதுக்கீடு அனைத்தும் சம்பந்தப்பட்ட அரசுத் துறை அலுவலர்களின் கள ஆய்வுக்கு உட்பட்டது. அதிகாரப்பூர்வ அரசு இணையதளங்கள் மூலமாக மட்டுமே விண்ணப்பிக்கவும்.',
      closeModal: 'மூடுக',
    },
    irrigationPage: {
      title: 'நுண்ணீர் பாசன மேலாண்மை',
      subtitle: 'நேரடி வானிலை ஆவியாதல் (ET₀) மற்றும் மாதிரி மண் இயற்பியல் ஆலோசனை (FAO-56 / TNAU)',
      locationCardTitle: 'பண்ணை அமைவிடம் & வானிலை நிலையம்',
      savedLocation: 'பதிவு செய்யப்பட்ட முதன்மை பண்ணை அமைவிடம்',
      noSavedLocation: 'பண்ணை GPS அமைவிடம் இன்னும் பதிவு செய்யப்படவில்லை. உலாவி GPS மூலம் அல்லது மாவட்டத்தை தேர்வு செய்யவும்.',
      detectGpsBtn: 'தற்போதைய இருப்பிடத்தை கண்டறி (GPS)',
      detectingGps: 'GPS இருப்பிடம் கண்டறியப்படுகிறது...',
      selectDistrictLabel: 'அல்லது வேளாண் மாவட்டத்தை தேர்வு செய்க',
      manualCoordsLabel: 'துல்லியமான பண்ணை GPS ஆயத்தொலைவுகளை உள்ளிடவும்',
      latLabel: 'அட்சரேகை (°N)',
      lonLabel: 'தீர்க்கரேகை (°E)',
      savePrimaryConsent: 'தானியங்கி வானிலை ஆலோசனைக்காக இந்த ஆயத்தொலைவுகளை எனது முதன்மை பண்ணை இருப்பிடமாக சேமிக்க ஒப்புக்கொள்கிறேன்.',
      saveLocationBtn: 'பண்ணை இருப்பிடத்தை சேமி',
      savingLocation: 'ஒப்புதலுடன் சேமிக்கப்படுகிறது...',
      locationSavedSuccess: 'பண்ணை ஆயத்தொலைவுகள் சுயவிவரத்தில் வெற்றிகரமாக சேமிக்கப்பட்டன!',
      liveWeatherCardTitle: 'நேரடி வேளாண் வானிலை சுருக்கம்',
      weatherSource: 'வானிலை தகவல் ஆதாரம்',
      lastUpdated: 'கடைசி புதுப்பிப்பு நேரம்',
      temp: 'வெப்பநிலை',
      humidity: 'காற்று ஈரப்பதம்',
      rainProbability: 'மழை வாய்ப்பு',
      forecastPrecipitation: 'எதிர்பார்க்கப்படும் மழை (24 மணி)',
      et0Title: 'குறிப்பு ஆவியாதல் வீதம் (ET₀)',
      et0Desc: 'FAO பென்மேன்-மாண்டீத் முறையில் கணக்கிடப்பட்ட வளிமண்டல நீர் ஆவியாதல் தேவை.',
      soilMoistureTitle: 'மாதிரி வேர் மண்டல ஈரப்பதம் (0-28 செ.மீ)',
      soilMoistureDisclaimer: 'மாதிரி நிலப்பரப்பு மதிப்பீடு (Open-Meteo). கள நேரடி சென்சார் அளவீடு அல்ல.',
      soilMoistureUnavailable: 'மண் ஈரப்பதம் மதிப்பீடு கிடைக்கவில்லை',
      depth0_7: 'மேற்பரப்பு மண் (0-7 செ.மீ)',
      depth7_28: 'வேர் மண்டலம் (7-28 செ.மீ)',
      depth28_100: 'ஆழமான மண் (28-100 செ.மீ)',
      refreshWeather: 'வானிலையை புதுப்பி',
      refreshing: 'வானிலை தரவு பெறப்படுகிறது...',
      loadingWeather: 'Open-Meteo செயற்கைக்கோள் & வானிலை மாதிரிகளிலிருந்து தரவு பெறப்படுகிறது...',
      staleDataWarning: 'அறிவிப்பு: இணைய தாமதம் காரணமாக முந்தைய சேமிக்கப்பட்ட வானிலை காட்டப்படுகிறது.',
      locationRequiredWarning: 'நேரடி வானிலைத் தகவலைப் பெற கீழே உங்கள் பண்ணை ஆயத்தொலைவுகளை அமைக்கவும்.',
      providerError: 'வானிலை சேவையை தற்போது தொடர்பு கொள்ள முடியவில்லை. பாசன ஆலோசனைக்கு நேரடி வானிலை தேவை.',
      offlineWarning: 'உங்கள் உலாவி தற்போது ஆஃப்லைனில் உள்ளது. இணைய இணைப்பை சரிபார்க்கவும்.',
      cropSelection: 'பயிர் வகை',
      growthStage: 'பயிர் வளர்ச்சி நிலை',
      soilType: 'மண் வகை',
      irrigationMethod: 'பாசன முறை',
      calculateBtn: 'பாசன ஆலோசனையை பெறவும்',
      calculating: 'மண்-நீர் சமநிலை கணக்கிடப்படுகிறது...',
      rationaleTitle: 'வேளாண் காரணங்கள் & கள உற்றுநோக்கல்கள்:',
      waterDemandLabel: 'தினசரி பயிர் நீர் தேவை',
      cropFactorLabel: 'பயிர் காரணி (Kc)',
      estVolumeLabel: 'மதிப்பிடப்பட்ட பாசன அளவு',
      fieldAreaLabel: 'பயிரிடப்பட்ட நிலப்பரப்பு (ஏக்கர்)',
      fieldAreaHelp: 'மொத்த நீர் தேவையை லிட்டரில் கணக்கிட ஏக்கர் பரப்பளவை உள்ளிடவும் (1 ஏக்கருக்கு 1 மிமீ = 4,047 லிட்டர்).',
      recIrrigateNow: 'இன்றே பாசனம் செய்யவும்',
      recDelayReassess: 'தள்ளிப்போட்டு மறுமதிப்பீடு செய்யவும்',
      recMonitorConditions: 'நிலவரத்தைக் கண்காணிக்கவும்',
      irrigationWindowLabel: 'பரிந்துரைக்கப்பட்ட பாசன நேரம் (உள்ளூர் நேரம்)',
      grossDepthLabel: 'மொத்த பாசன ஆழம்',
      totalVolumeLabel: 'மொத்த பாசன நீர் அளவு',
      paddyWaterProtocolTitle: 'TNAU காவிரி டெல்டா நெல் பாசன மேலாண்மை',
      unitExplanationTitle: 'வேளாண் நீர் அலகுகள் விதிமுறை',
      confidenceLabel: 'கணக்கீட்டு நம்பிக்கை நிலை',
      limitationsTitle: 'வேளாண் வரம்புகள் & கருதுகோள்கள்:',
      refreshAdvisoryBtn: 'ஆலோசனையை புதுப்பி',
      noHardwareControlBanner: 'வேளாண் முடிவெடுக்கும் ஆலோசனை மட்டுமே. பம்புகள் அல்லது வால்வுகளை நேரடியாக இயக்கும் கட்டுப்பாடு இதில் இல்லை.',
      advisoryDisclaimer: 'அறிவுறுத்தல் குறிப்பு: இது வேளாண் நீர் சமநிலை விதிகளின் (TNAU / FAO-56 பென்மேன்-மாண்டீத்) அடிப்படையில் கணக்கிடப்பட்ட ஆலோசனை மட்டுமே. மாதிரி மண் ஈரப்பதம் நேரடி சென்சார் அளவீடு அல்ல. பாசனம் செய்வதற்கு முன் வயல் நிலையை சரிபார்க்கவும்.',
    },
  },
};

const regionalBundles: Partial<Record<Language, Partial<TranslationSchema>>> = {
  hi: hiTranslations,
  te: teTranslations,
  kn: knTranslations,
  ml: mlTranslations,
  mr: mrTranslations,
  bn: bnTranslations,
  gu: guTranslations,
  pa: paTranslations,
  or: orTranslations,
  as: asTranslations,
  ur: urTranslations,
  ks: ksTranslations,
  sd: sdTranslations,
  ne: neTranslations,
  sa: saTranslations,
  brx: brxTranslations,
  doi: doiTranslations,
  kok: kokTranslations,
  mai: maiTranslations,
  mni: mniTranslations,
  sat: satTranslations,
};

export function createFallbackProxy<T extends object>(target: Partial<T>, fallback: T): T {
  return new Proxy(target, {
    get(obj: any, prop: string | symbol) {
      const val = obj[prop];
      const fallbackVal = (fallback as any)[prop];
      if (val === undefined || val === null || val === '') {
        return fallbackVal;
      }
      if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
        if (typeof fallbackVal === 'object' && fallbackVal !== null) {
          return createFallbackProxy(val, fallbackVal);
        }
      }
      return val;
    },
  }) as T;
}

export interface LanguageOption {
  code: Language;
  name: string;
  nativeName: string;
  isFullyTranslated: boolean;
  tier: 'full' | 'core' | 'essential';
  coveragePercent: number;
  direction: 'ltr' | 'rtl';
}

export const REGIONAL_LANGUAGE_OPTIONS: LanguageOption[] = Object.values(CENTRAL_LOCALE_REGISTRY).map((meta) => ({
  code: meta.code,
  name: meta.name,
  nativeName: meta.nativeName,
  isFullyTranslated: meta.tier === 'full',
  tier: meta.tier,
  coveragePercent: meta.coveragePercent,
  direction: meta.direction,
}));

export const IRRIGATION_OPTIONS = [
  'Borewell / Tube Well',
  'Open Well',
  'Canal',
  'River / Stream',
  'Tank / Lake',
  'Farm Pond',
  'Dam / Reservoir',
  'Rainwater Harvesting',
  'Spring Water',
  'Community Irrigation',
  'Treated Wastewater',
  'Municipal Water',
  'Rain-fed / No Irrigation',
  'Other',
] as const;

export function getTranslationsForLanguage(lang: Language): TranslationSchema {
  if (lang === 'en') {
    return translations.en;
  }
  if (lang === 'ta') {
    return translations.ta;
  }
  const bundle = regionalBundles[lang];
  if (bundle) {
    return createFallbackProxy(bundle, translations.en);
  }
  return translations.en;
}

export {
  CENTRAL_LOCALE_REGISTRY,
  getLocaleMetadata,
  isRTL,
};


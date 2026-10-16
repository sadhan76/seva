import type { Language, NavTab } from '../types';

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
}

export const translations: Record<'en' | 'ta', TranslationSchema> = {
  en: {
    appName: 'Namma Vivasayi AI',
    appTagline: 'AI-Powered Farming & Smart Procurement Platform',
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
    },
    auth: {
      signIn: 'Sign In',
      signUp: 'Register as Farmer',
      signOut: 'Log Out',
      loginTitle: 'Sign In to Namma Vivasayi AI',
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
  },
  ta: {
    appName: 'நம்ம விவசாயி AI',
    appTagline: 'செயற்கை நுண்ணறிவு வேளாண்மை மற்றும் நேரடி கொள்முதல் தளம்',
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
    },
    auth: {
      signIn: 'உள்நுழைக',
      signUp: 'உழவர் புதிய பதிவு',
      signOut: 'வெளியேறு',
      loginTitle: 'நம்ம விவசாயி AI உள்நுழைவு',
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
  },
};

export interface LanguageOption {
  code: Language;
  name: string;
  nativeName: string;
  isFullyTranslated: boolean;
}

export const REGIONAL_LANGUAGE_OPTIONS: LanguageOption[] = [
  { code: 'en', name: 'English', nativeName: 'English', isFullyTranslated: true },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', isFullyTranslated: true },
  { code: 'hi', name: 'Hindi', nativeName: 'हिंदी', isFullyTranslated: false },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', isFullyTranslated: false },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', isFullyTranslated: false },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', isFullyTranslated: false },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', isFullyTranslated: false },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', isFullyTranslated: false },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', isFullyTranslated: false },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', isFullyTranslated: false },
  { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', isFullyTranslated: false },
  { code: 'as', name: 'Assamese', nativeName: 'অসমীয়া', isFullyTranslated: false },
  { code: 'ur', name: 'Urdu', nativeName: 'اردو', isFullyTranslated: false },
  { code: 'ne', name: 'Nepali', nativeName: 'नेपाली', isFullyTranslated: false },
  { code: 'sa', name: 'Sanskrit', nativeName: 'संस्कृतम्', isFullyTranslated: false },
  { code: 'other', name: 'Other', nativeName: 'Other', isFullyTranslated: false },
];

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
  if (lang === 'ta') {
    return translations.ta;
  }
  return translations.en;
}

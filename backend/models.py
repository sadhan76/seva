"""
Pydantic data models for input validation, authentication, and API responses.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any, List, Union
import re

# ============================================================================
# PHASE 19 CONSTANTS: IRRIGATION SOURCES & REGIONAL LANGUAGES
# ============================================================================

VALID_IRRIGATION_OPTIONS: List[str] = [
    "Borewell / Tube Well",
    "Open Well",
    "Canal",
    "River / Stream",
    "Tank / Lake",
    "Farm Pond",
    "Dam / Reservoir",
    "Rainwater Harvesting",
    "Spring Water",
    "Community Irrigation",
    "Treated Wastewater",
    "Municipal Water",
    "Rain-fed / No Irrigation",
    "Other",
]

REGIONAL_LANGUAGES: List[str] = [
    "English",
    "Tamil",
    "Hindi",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Marathi",
    "Bengali",
    "Gujarati",
    "Punjabi",
    "Odia",
    "Assamese",
    "Urdu",
    "Nepali",
    "Sanskrit",
    "Other",
]

LANGUAGE_CODE_MAP: Dict[str, str] = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "ne": "Nepali",
    "sa": "Sanskrit",
    "other": "Other",
}


def normalize_integer_land_acres(v: Any) -> int:
    """
    Strict validation for land acres:
    Accepts positive whole-number acre values only.
    Rejects decimals (e.g. 3.5), negatives, empty input, and non-numeric input.
    """
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError("Total land area is required and cannot be empty.")

    if isinstance(v, float):
        if not v.is_integer():
            raise ValueError("Total land area must be a positive whole number of acres (decimals not allowed).")
        v = int(v)
    elif isinstance(v, str):
        v = v.strip()
        if "." in v:
            parts = v.split(".")
            if len(parts) > 1 and parts[1] != "" and parts[1] != "0":
                raise ValueError("Total land area must be a positive whole number of acres (decimals not allowed).")
            v = parts[0]
        try:
            v = int(v)
        except ValueError:
            raise ValueError("Total land area must be a valid whole number integer.")

    try:
        val = int(v)
    except (TypeError, ValueError):
        raise ValueError("Total land area must be a valid positive whole number integer.")

    if val <= 0:
        raise ValueError("Total land area must be greater than zero.")
    if val > 10000:
        raise ValueError("Total land area cannot exceed 10,000 acres.")
    return val


class FarmerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: str = Field(..., description="10-digit Indian mobile number")
    village: str = Field(..., min_length=2, max_length=100, description="Village / Taluk")
    district: str = Field(default="Thanjavur", min_length=2, max_length=60)
    state: str = Field(default="Tamil Nadu", max_length=60)
    preferredLanguage: str = Field(default="en", description="Preferred regional language")
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)")
    confirmPassword: str = Field(..., min_length=6, max_length=100, description="Confirm password")

    # Positive whole-number acres only
    totalLandAcres: int = Field(default=3, description="Positive whole-number acres")
    primaryCrop: Optional[str] = Field(default="Samba Paddy (CR 1009 Sub 1)")
    soilType: Optional[str] = Field(default="Alluvial Clay Loam")

    # Multi-select irrigation sources
    irrigationSources: Optional[List[str]] = Field(default=None, description="Array of selected irrigation sources")
    irrigationSource: Optional[Union[str, List[str]]] = Field(default=None, description="Backward-compatible irrigation source")
    otherIrrigationDetail: Optional[str] = Field(default=None, max_length=150, description="Specification if 'Other' is selected")

    # Telegram verification token (if verified before registration submit)
    telegramVerifiedToken: Optional[str] = Field(default=None, description="Proof token from Telegram OTP verification")

    @field_validator("phone")
    def validate_phone(cls, v):
        cleaned = re.sub(r"[^\d]", "", v)
        if len(cleaned) == 12 and cleaned.startswith("91"):
            cleaned = cleaned[2:]
        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError("Mobile number must be a valid 10-digit Indian number starting with 6, 7, 8, or 9.")
        return cleaned

    @field_validator("totalLandAcres", mode="before")
    def validate_acres(cls, v):
        return normalize_integer_land_acres(v)

    @field_validator("preferredLanguage")
    def validate_language(cls, v):
        if not v or not v.strip():
            return "en"
        val = v.strip()
        # Accept valid language codes or capitalized language names
        if val in LANGUAGE_CODE_MAP:
            return val
        for code, name in LANGUAGE_CODE_MAP.items():
            if val.lower() == name.lower():
                return code
        return "en"

    @model_validator(mode="after")
    def verify_and_consolidate(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match. Please verify both fields.")

        # Consolidate irrigation sources
        sources = self.irrigationSources
        if sources is None and self.irrigationSource is not None:
            if isinstance(self.irrigationSource, list):
                sources = self.irrigationSource
            elif isinstance(self.irrigationSource, str):
                sources = [s.strip() for s in re.split(r"[,&]", self.irrigationSource) if s.strip()]

        if not sources:
            sources = ["Borewell / Tube Well"]

        clean_sources: List[str] = []
        for s in sources:
            s_clean = s.strip()
            if not s_clean:
                continue
            if s_clean == "Other" and self.otherIrrigationDetail:
                clean_sources.append(f"Other: {self.otherIrrigationDetail.strip()}")
            elif s_clean not in clean_sources:
                clean_sources.append(s_clean)

        self.irrigationSources = clean_sources
        self.irrigationSource = ", ".join(clean_sources)
        return self


class LoginRequest(BaseModel):
    phone: str = Field(..., description="Registered 10-digit mobile number")
    password: Optional[str] = Field(default=None, description="Password (optional when using Telegram OTP)")
    role: Literal["farmer", "staff"] = Field(default="farmer", description="Role to sign in as")
    authMethod: Optional[Literal["password", "telegram_otp"]] = Field(default="password", description="Authentication mode")
    telegramOtp: Optional[str] = Field(default=None, description="Telegram OTP for passwordless login")

    @field_validator("phone")
    def clean_phone(cls, v):
        cleaned = re.sub(r"[^\d]", "", v)
        if len(cleaned) == 12 and cleaned.startswith("91"):
            cleaned = cleaned[2:]
        return cleaned


class UserSummary(BaseModel):
    id: str
    name: str
    phone: str
    role: Literal["farmer", "staff"]
    preferredLanguage: str = "en"
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    mandiName: Optional[str] = None
    farmerId: Optional[str] = None
    totalLandAcres: Optional[Union[int, float]] = None
    primaryCrop: Optional[str] = None
    soilType: Optional[str] = None
    irrigationSource: Optional[str] = None
    irrigationSources: Optional[List[str]] = None
    aadhaarMasked: Optional[str] = None
    isAadhaarVerified: Optional[bool] = False
    createdAt: str
    telegramLinked: Optional[bool] = False
    telegramUsername: Optional[str] = None


class AuthTokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresInMinutes: int
    user: UserSummary


class FarmerProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Farmer full name")
    phone: str = Field(..., min_length=10, max_length=15, description="10-digit mobile number")
    location: str = Field(..., min_length=2, max_length=120, description="Village and block")
    district: str = Field(default="Thanjavur", min_length=2, max_length=60, description="District name")
    state: str = Field(default="Tamil Nadu", max_length=60)
    totalLandAcres: int = Field(..., description="Positive whole-number acres")
    primaryCrop: str = Field(..., min_length=2, max_length=100, description="Primary crop cultivated")
    soilType: str = Field(default="Alluvial Clay Loam", max_length=100, description="Dominant soil type")
    irrigationSource: Optional[str] = Field(default=None, max_length=250, description="Source of irrigation")
    irrigationSources: Optional[List[str]] = Field(default=None, description="Multiple irrigation sources")
    otherIrrigationDetail: Optional[str] = Field(default=None, max_length=150)
    aadhaarMasked: Optional[str] = Field(default="XXXX-XXXX-4921", description="Masked Aadhaar identifier")
    preferredLanguage: Optional[str] = Field(default=None, description="Preferred language")

    @field_validator("totalLandAcres", mode="before")
    def validate_acres(cls, v):
        return normalize_integer_land_acres(v)

    @model_validator(mode="after")
    def consolidate_profile_irrigation(self):
        sources = self.irrigationSources
        if sources is None and self.irrigationSource is not None:
            if isinstance(self.irrigationSource, list):
                sources = self.irrigationSource
            elif isinstance(self.irrigationSource, str):
                sources = [s.strip() for s in re.split(r"[,&]", self.irrigationSource) if s.strip()]

        if not sources:
            sources = ["Borewell / Tube Well"]

        clean_sources: List[str] = []
        for s in sources:
            s_clean = s.strip()
            if not s_clean:
                continue
            if s_clean == "Other" and self.otherIrrigationDetail:
                clean_sources.append(f"Other: {self.otherIrrigationDetail.strip()}")
            elif s_clean not in clean_sources:
                clean_sources.append(s_clean)

        self.irrigationSources = clean_sources
        self.irrigationSource = ", ".join(clean_sources)
        return self


class FarmerProfileResponse(BaseModel):
    id: str
    farmerId: str
    name: str
    phone: str
    location: str
    district: str
    state: str
    totalLandAcres: Union[int, float]
    primaryCrop: str
    soilType: str
    irrigationSource: str
    irrigationSources: Optional[List[str]] = None
    preferredLanguage: Optional[str] = None
    aadhaarMasked: Optional[str] = None
    createdAt: str


# ============================================================================
# PHASE 19: TELEGRAM OTP & ACCOUNT LINKING MODELS
# ============================================================================

class TelegramStatusResponse(BaseModel):
    configured: bool
    botUsername: Optional[str] = None
    message: str


class TelegramLinkTokenRequest(BaseModel):
    phone: str = Field(..., description="Mobile number to link with Telegram")


class TelegramLinkTokenResponse(BaseModel):
    linkToken: str
    deepLink: str
    botUsername: str
    expiresInSeconds: int
    configured: bool
    notice: str


class TelegramLinkStatusResponse(BaseModel):
    linked: bool
    verified: bool
    telegramUsername: Optional[str] = None
    telegramFirstName: Optional[str] = None
    phone: Optional[str] = None
    message: str


class TelegramSendOtpRequest(BaseModel):
    phone: str = Field(..., description="10-digit mobile number")
    purpose: Literal["login", "registration", "account_linking"] = Field(default="login")


class TelegramSendOtpResponse(BaseModel):
    success: bool
    message: str
    maskedChat: str
    cooldownSeconds: int
    expiresInSeconds: int


class TelegramVerifyOtpRequest(BaseModel):
    phone: str = Field(..., description="10-digit mobile number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    purpose: Literal["login", "registration", "account_linking"] = Field(default="login")


class TelegramVerifyOtpResponse(BaseModel):
    success: bool
    message: str
    phone: str
    verifiedToken: Optional[str] = None
    authToken: Optional[AuthTokenResponse] = None


class ProcurementBookingCreate(BaseModel):
    farmerName: str = Field(..., min_length=2, max_length=100, description="Farmer name")
    farmerId: Optional[str] = Field(default="TN-AGRI-2026-8841", description="Farmer ID")
    mandiName: str = Field(..., min_length=3, max_length=150, description="Regulated Market or DPC centre")
    crop: str = Field(..., min_length=2, max_length=100, description="Crop variety")
    quantityBags: int = Field(..., ge=1, le=5000, description="Number of bags")
    preferredDate: str = Field(..., description="Booking date (YYYY-MM-DD)")
    timeWindow: str = Field(default="08:30 AM - 11:30 AM", description="Reporting time window")


class ProcurementBookingResponse(BaseModel):
    id: str
    bookingId: str
    tokenNumber: str
    farmerName: str
    farmerId: str
    mandiName: str
    crop: str
    quantityBags: int
    estimatedWeightQuintals: float
    slotDate: str
    timeWindow: str
    status: str
    moisturePercent: Optional[float] = None
    actualNetWeightQuintals: Optional[float] = None
    qualityNotes: Optional[str] = None
    createdAt: str


class StaffBookingStatusUpdate(BaseModel):
    status: Literal["confirmed", "quality_checked", "weighed", "dbt_completed", "cancelled"]
    moisturePercent: Optional[float] = Field(None, ge=5.0, le=30.0)
    actualNetWeightQuintals: Optional[float] = Field(None, gt=0)
    qualityNotes: Optional[str] = None


# ============================================================================
# PHASE 4: SMART FARMING INTELLIGENCE MODELS
# ============================================================================

class IrrigationCalculateRequest(BaseModel):
    crop: str = Field(default="Paddy (Ponni)", min_length=2, max_length=100)
    growthStage: str = Field(default="Vegetative / Tillering", min_length=2, max_length=80)
    soilType: str = Field(default="Alluvial Clay Loam", min_length=2, max_length=100)
    irrigationMethod: str = Field(default="Controlled Basin Flooding", min_length=2, max_length=80)
    soilMoisturePercent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    recentRainMm: Optional[float] = Field(default=0.0, ge=0.0, le=500.0)
    forecastRainChance: Optional[float] = Field(default=20.0, ge=0.0, le=100.0)


class CropRecommendRequest(BaseModel):
    district: str = Field(default="Thanjavur", min_length=2, max_length=80)
    soilType: str = Field(default="Alluvial Clay Loam", min_length=2, max_length=80)
    season: str = Field(default="Samba (Aug - Jan)", min_length=2, max_length=80)
    waterAvailability: str = Field(default="High", min_length=2, max_length=30)
    cropPreference: Optional[str] = Field(default=None, max_length=80)


# ============================================================================
# PHASE 5: SMART PROCUREMENT TRACKING MODELS
# ============================================================================

class ProcurementCentreInfo(BaseModel):
    id: str
    centreCode: str
    name: str
    nameTa: str
    district: str
    taluk: str
    locationAddress: str
    supportedCrops: list[str]
    operatingHours: str
    dailyCapacityBags: int
    slotCapacityBags: int
    slotWindows: list[str]
    isDemoData: bool = True
    dataSourceLabel: str = "TNCSC Direct Purchase Centre (Model Reference)"


class SlotStatusInfo(BaseModel):
    timeWindow: str
    maxCapacityBags: int
    bookedBags: int
    availableBags: int
    status: Literal["available", "filling_fast", "full"]


class CentreSlotsResponse(BaseModel):
    centreCode: str
    centreName: str
    date: str
    totalDailyCapacityBags: int
    slots: list[SlotStatusInfo]


class TokenVerifyRequest(BaseModel):
    token: Optional[str] = Field(default=None, description="Opaque QR token or Token Number")
    bookingId: Optional[str] = Field(default=None, description="Booking ID reference")


class TokenVerifyResponse(BaseModel):
    isValid: bool
    status: str
    bookingId: str
    tokenNumber: str
    farmerName: str
    farmerId: str
    mandiName: str
    crop: str
    quantityBags: int
    estimatedWeightQuintals: float
    slotDate: str
    timeWindow: str
    canCheckIn: bool
    canWeigh: bool
    message: str
    disclaimer: str


class StaffCheckInRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=200, description="Gate remarks / Vehicle Reg No")


class StaffWeighingCreateRequest(BaseModel):
    bookingId: Optional[str] = Field(default=None, description="Optional bookingId if not in path")
    cropType: Optional[str] = Field(default=None, description="Crop name")
    acceptedWeightKg: Optional[float] = Field(default=None, gt=0, le=1000000, description="Accepted weight in kilograms")
    actualNetWeightQuintals: Optional[float] = Field(default=None, gt=0, le=10000, description="Actual weighed net quantity in Quintals")
    pricePerKg: Optional[float] = Field(default=None, gt=0, le=5000, description="Configured rate in INR per kg")
    pricePerQuintal: Optional[float] = Field(default=None, gt=0, le=50000, description="Agreed MSP / Unit Rate in INR per Quintal")
    qualityDeductionsAmount: float = Field(default=0.0, ge=0.0, description="Quality dockage / moisture deduction in INR")
    otherDeductionsAmount: float = Field(default=0.0, ge=0.0, description="Optional handling / cess deduction in INR")
    moisturePercent: Optional[float] = Field(default=14.0, ge=0.0, le=50.0, description="Moisture meter reading percentage")
    qualityGrade: str = Field(default="FAQ Grade A", max_length=80, description="Quality test result")
    customDeductionsAmount: Optional[float] = Field(default=0.0, ge=0.0, description="Backward compatibility alias for other deductions")
    paymentStatus: Literal["PENDING", "PROCESSING", "PAID"] = Field(default="PENDING", description="Initial payment status")
    notes: Optional[str] = Field(default=None, max_length=500)


class StaffTransactionRequest(BaseModel):
    actualNetWeightQuintals: Optional[float] = Field(default=None, gt=0, le=10000, description="Actual weighed net quantity in Quintals")
    acceptedWeightKg: Optional[float] = Field(default=None, gt=0, le=1000000, description="Accepted weight in kilograms")
    pricePerQuintal: Optional[float] = Field(default=None, gt=0, le=50000, description="Agreed MSP / Unit Rate in INR per Quintal")
    pricePerKg: Optional[float] = Field(default=None, gt=0, le=5000, description="Configured rate in INR per kg")
    moisturePercent: float = Field(default=14.0, ge=0.0, le=50.0, description="Moisture meter reading percentage")
    qualityGrade: str = Field(default="FAQ Grade A", max_length=80, description="Quality test result")
    qualityDeductionsAmount: Optional[float] = Field(default=0.0, ge=0.0, description="Quality dockage deduction in INR")
    otherDeductionsAmount: Optional[float] = Field(default=0.0, ge=0.0, description="Other deduction in INR")
    customDeductionsAmount: Optional[float] = Field(default=0.0, ge=0.0, description="Optional custom cess or handling deduction")
    paymentStatus: Literal["PENDING", "PROCESSING", "PAID"] = Field(default="PROCESSING", description="DBT ledger status")
    notes: Optional[str] = Field(default=None, max_length=500)


class WeighingCalculationPreviewRequest(BaseModel):
    acceptedWeightKg: float = Field(..., gt=0, le=1000000, description="Accepted weight in kilograms")
    pricePerKg: float = Field(..., gt=0, le=5000, description="Configured price per kilogram in INR")
    qualityDeductionsAmount: float = Field(default=0.0, ge=0.0, description="Quality deductions in INR")
    otherDeductionsAmount: float = Field(default=0.0, ge=0.0, description="Other deductions in INR")


class WeighingCalculationPreviewResponse(BaseModel):
    acceptedWeightKg: float
    pricePerKg: float
    grossAmount: float
    qualityDeductionsAmount: float
    otherDeductionsAmount: float
    totalDeductionsAmount: float
    netAmount: float
    isValid: bool
    validationError: Optional[str] = None


class PaymentStatusUpdateRequest(BaseModel):
    newStatus: Literal["PENDING", "PROCESSING", "PAID"]
    notes: Optional[str] = Field(default=None, max_length=300, description="Reason / banking reference / DBT notes")
    transactionReference: Optional[str] = Field(default=None, max_length=100, description="PFMS / e-Kuber / UTR number")


class AuditLogEntry(BaseModel):
    action: str
    by: str
    role: str
    timestamp: str
    notes: Optional[str] = None


class WeighingTransactionDetails(BaseModel):
    actualNetWeightQuintals: float
    acceptedWeightKg: Optional[float] = None
    pricePerQuintal: float
    pricePerKg: Optional[float] = None
    moisturePercent: float
    moistureDeductionAmount: float
    qualityDeductionsAmount: Optional[float] = None
    otherDeductionsAmount: float
    totalDeductionsAmount: float
    grossAmount: float
    netPayableAmount: float
    paymentStatus: Literal["PENDING", "PROCESSING", "PAID"]
    paymentMethod: str = "Direct Benefit Transfer (PFMS / e-Kuber Ledger)"
    disclaimer: str = "Ledger voucher recorded. Real fund disbursement requires state treasury DBT gateway authorization."
    weighedAt: str
    weighedByStaff: str
    billNumber: Optional[str] = None
    notes: Optional[str] = None


class DigitalBillResponse(BaseModel):
    billNumber: str
    bookingId: str
    farmerName: str
    farmerId: str
    mandiName: str
    crop: str
    acceptedWeightKg: float
    actualNetWeightQuintals: float
    pricePerKg: float
    pricePerQuintal: float
    grossAmount: float
    qualityDeductionsAmount: float
    otherDeductionsAmount: float
    totalDeductionsAmount: float
    netAmount: float
    paymentStatus: Literal["PENDING", "PROCESSING", "PAID"]
    paymentMethod: str = "Direct Benefit Transfer (PFMS / e-Kuber Ledger)"
    transactionDate: str
    weighedByStaff: str
    notes: Optional[str] = None
    paymentHistory: list[dict] = []
    auditHistory: list[dict] = []
    disclaimer: str = "Official electronic procurement bill and DBT ledger voucher."


class StaffQueueStatusUpdateRequest(BaseModel):
    newStatus: Literal["CHECKED_IN", "IN_QUEUE", "PROCESSING", "COMPLETED", "CANCELLED"]
    notes: Optional[str] = Field(None, max_length=300, description="Audit reason / remarks")


class QueueTrackingResponse(BaseModel):
    bookingId: str
    tokenNumber: str
    status: str
    mandiName: str
    slotDate: str
    timeWindow: str
    farmerName: str
    crop: str
    quantityBags: int
    vehiclesAhead: Optional[int] = None
    queuePosition: Optional[int] = None
    estimatedWaitMinutes: Optional[int] = None
    hasSufficientDataForEstimate: bool = False
    waitingTimeDisplay: str = "Waiting time unavailable"
    isInActiveQueue: bool = False
    currentStageNumber: int
    stages: list[dict]
    transaction: Optional[WeighingTransactionDetails] = None
    auditHistory: list[AuditLogEntry] = []
    lastPolledAt: str
    isDemoData: bool = False


# ============================================================================
# PHASE 6 & PHASE 17: AI ASSISTANT, NOTIFICATIONS, CHAT ACTIONS & SMS MODELS
# ============================================================================

class ChatAction(BaseModel):
    intent: str = Field(default="general_qa", description="Action intent: navigation, data_query, data_change, general_qa, unsupported")
    actionType: Optional[str] = Field(None, description="NAVIGATE, SHOW_DATA, REQUEST_CONFIRMATION, EXECUTE_ACTION, UNSUPPORTED")
    targetTab: Optional[str] = Field(None, description="Target application tab")
    actionName: Optional[str] = Field(None, description="Specific action identifier")
    parameters: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    requiresConfirmation: bool = False
    confirmationPrompt: Optional[str] = None
    confirmedActionPayload: Optional[Dict[str, Any]] = None


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Farmer query in preferred regional language")
    language: str = Field(default="en", description="Conversation language (en, ta, hi, te, kn, ml, mr, etc.)")
    conversationId: Optional[str] = Field(None, description="Client conversation thread identifier")
    includeFarmContext: bool = Field(default=True, description="Whether to ground response in saved farm profile")
    confirmedAction: Optional[Dict[str, Any]] = Field(None, description="Confirmed action payload when user confirms an action")


class ChatMessageResponse(BaseModel):
    id: str
    reply: str
    language: str = "en"
    provider: str
    isRealAI: bool
    providerNotice: str
    contextUsed: dict = {}
    followUpQuestion: Optional[str] = None
    timestamp: str
    conversationId: str
    action: Optional[ChatAction] = None


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str = "booking"
    isRead: bool = False
    createdAt: str
    isoTimestamp: Optional[str] = None
    bookingId: Optional[str] = None
    farmerId: Optional[str] = None
    userId: Optional[str] = None


class NotificationMarkReadResponse(BaseModel):
    success: bool
    notificationId: str
    message: str


class SMSStatusResponse(BaseModel):
    configured: bool
    provider: str
    senderId: Optional[str] = None
    message: str
    note: str


# ============================================================================
# CROP HEALTH & MULTI-CATEGORY DIAGNOSIS SCHEMAS
# Category 1: Pest and insect damage
# Category 2: Plant diseases (fungal, bacterial, viral)
# Category 3: Physiological and abiotic problems (nutrients, drought, waterlogging, heat, salinity)
# ============================================================================

DiagnosisCategory = Literal["pest_damage", "plant_disease", "abiotic_disorder", "healthy", "inconclusive"]
SeverityLevel = Literal["low", "moderate", "high", "critical", "unknown"]

class CropHealthDiagnosisDetails(BaseModel):
    isCropLeaf: bool = True
    category: DiagnosisCategory = "plant_disease"
    categoryLabelEn: str = "Plant Disease"
    categoryLabelTa: str = "பயிர் நோய்"
    suspectedCondition: str = "Unidentified Condition"
    suspectedConditionTa: Optional[str] = None
    affectedCrop: str = "Unknown Crop"
    affectedCropTa: Optional[str] = None
    plantPart: Optional[str] = "leaf"
    pathogenOrCausalAgent: Optional[str] = None
    confidencePercent: int = Field(default=0, ge=0, le=100)
    severityOrUrgency: SeverityLevel = "moderate"
    visualSymptoms: str = ""
    visualSymptomsTa: Optional[str] = None
    possibleCauses: List[str] = Field(default_factory=list)
    alternativeExplanations: List[str] = Field(default_factory=list)
    diagnosticLimitations: List[str] = Field(default_factory=list)
    recommendedNextSteps: List[str] = Field(default_factory=list)
    biologicalManagement: List[str] = Field(default_factory=list)
    chemicalTreatment: Optional[List[str]] = None
    chemicalPrecautions: Optional[str] = None
    preventionTips: List[str] = Field(default_factory=list)
    whenToConsultExpert: List[str] = Field(default_factory=list)
    verifiedGuidanceReferences: List[str] = Field(default_factory=list)
    verifiedTreatment: Optional[Dict[str, Any]] = None

    # Legacy compatibility fields
    crop: Optional[str] = None
    cropTa: Optional[str] = None
    diseaseName: Optional[str] = None
    diseaseNameTa: Optional[str] = None
    pathogen: Optional[str] = None
    severity: Optional[str] = None
    organicManagement: Optional[str] = None
    organicManagementTa: Optional[str] = None
    chemicalManagement: Optional[str] = None
    chemicalManagementTa: Optional[str] = None
    extensionAdvisory: Optional[str] = None
    extensionAdvisoryTa: Optional[str] = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self):
        if not self.crop:
            self.crop = self.affectedCrop
        if not self.cropTa:
            self.cropTa = self.affectedCropTa
        if not self.diseaseName:
            self.diseaseName = self.suspectedCondition
        if not self.diseaseNameTa:
            self.diseaseNameTa = self.suspectedConditionTa
        if not self.pathogen:
            self.pathogen = self.pathogenOrCausalAgent
        if not self.severity:
            self.severity = self.severityOrUrgency
        if not self.organicManagement and self.biologicalManagement:
            self.organicManagement = "; ".join(self.biologicalManagement)
        if not self.chemicalManagement and self.chemicalTreatment:
            self.chemicalManagement = "; ".join(self.chemicalTreatment)
        if not self.extensionAdvisory and self.whenToConsultExpert:
            self.extensionAdvisory = "; ".join(self.whenToConsultExpert)
        return self


DiseaseDiagnosisDetails = CropHealthDiagnosisDetails


class DiseaseAnalysisResponse(BaseModel):
    status: Literal["diagnosed", "suspected", "inconclusive", "quality_failure", "unavailable", "not_configured", "invalid_image"]
    diagnosticStatus: Optional[str] = None
    testedModelPresent: bool
    modelName: Optional[str] = None
    filename: str
    fileSizeBytes: Optional[int] = None
    contentType: Optional[str] = None
    messageEn: str
    messageTa: str
    truthfulnessNotice: str
    safeNextSteps: List[str]
    diagnosis: Optional[CropHealthDiagnosisDetails] = None
    verifiedTreatment: Optional[Dict[str, Any]] = None
    referenceCatalog: Optional[List[Dict[str, Any]]] = None
    imageQuality: Optional[Dict[str, Any]] = None
    reportId: Optional[str] = None
    saved: bool = False


CropHealthAnalysisResponse = DiseaseAnalysisResponse


# ============================================================================
# DIAGNOSIS HISTORY & REPORT MODELS (PERSISTENCE & SECURITY)
# ============================================================================

class DiagnosisReportEntity(BaseModel):
    id: str
    userId: str
    farmerId: Optional[str] = None
    farmerName: Optional[str] = None
    crop: str
    cropTa: Optional[str] = None
    plantPart: Optional[str] = "leaf"
    district: Optional[str] = None
    symptomDescription: Optional[str] = None
    category: str
    categoryLabelEn: str
    categoryLabelTa: str
    suspectedCondition: str
    suspectedConditionTa: Optional[str] = None
    pathogenOrCausalAgent: Optional[str] = None
    status: str
    confidencePercent: int = 0
    severityOrUrgency: str = "moderate"
    isUncertainOrInconclusive: bool = False
    uncertaintyReason: Optional[str] = None
    visualSymptoms: str = ""
    visualSymptomsTa: Optional[str] = None
    possibleCauses: List[str] = Field(default_factory=list)
    alternativeExplanations: List[str] = Field(default_factory=list)
    diagnosticLimitations: List[str] = Field(default_factory=list)
    recommendedNextSteps: List[str] = Field(default_factory=list)
    biologicalManagement: List[str] = Field(default_factory=list)
    chemicalTreatment: Optional[List[str]] = None
    chemicalPrecautions: Optional[str] = None
    verifiedTreatment: Optional[Dict[str, Any]] = None
    verifiedGuidanceReferences: List[str] = Field(default_factory=list)
    imageMetadata: Dict[str, Any] = Field(default_factory=dict)
    createdAt: str
    updatedAt: Optional[str] = None


class DiagnosisReportCreatePayload(BaseModel):
    crop: Optional[str] = None
    cropTa: Optional[str] = None
    plantPart: Optional[str] = "leaf"
    district: Optional[str] = None
    symptomDescription: Optional[str] = None
    diagnosis: Optional[CropHealthDiagnosisDetails] = None
    verifiedTreatment: Optional[Dict[str, Any]] = None
    status: Optional[str] = "diagnosed"
    filename: Optional[str] = "leaf.jpg"
    fileSizeBytes: Optional[int] = 0
    contentType: Optional[str] = "image/jpeg"


class DiagnosisReportListResponse(BaseModel):
    reports: List[DiagnosisReportEntity]
    total: int
    farmerId: Optional[str] = None
    farmerName: Optional[str] = None





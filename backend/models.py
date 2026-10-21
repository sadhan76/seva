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
    "Assamese",
    "Bengali",
    "Bodo",
    "Dogri",
    "English",
    "Gujarati",
    "Hindi",
    "Kannada",
    "Kashmiri",
    "Konkani",
    "Maithili",
    "Malayalam",
    "Manipuri (Meitei)",
    "Marathi",
    "Nepali",
    "Odia",
    "Punjabi",
    "Sanskrit",
    "Santali",
    "Sindhi",
    "Tamil",
    "Telugu",
    "Urdu",
    "Other",
]

LANGUAGE_CODE_MAP: Dict[str, str] = {
    "as": "Assamese",
    "bn": "Bengali",
    "brx": "Bodo",
    "doi": "Dogri",
    "en": "English",
    "gu": "Gujarati",
    "hi": "Hindi",
    "kn": "Kannada",
    "ks": "Kashmiri",
    "kok": "Konkani",
    "mai": "Maithili",
    "ml": "Malayalam",
    "mni": "Manipuri (Meitei)",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "pa": "Punjabi",
    "sa": "Sanskrit",
    "sat": "Santali",
    "sd": "Sindhi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu",
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
    country: Optional[str] = Field(default="India", max_length=50, description="Country name")
    state: str = Field(..., min_length=2, max_length=80, description="State / Union Territory")
    district: str = Field(..., min_length=2, max_length=80, description="District name")
    village: str = Field(..., min_length=2, max_length=100, description="Village / Town / Taluk")
    taluk: Optional[str] = Field(default=None, max_length=100, description="Taluk / Tehsil / Mandal")
    stateCode: Optional[str] = Field(default=None, description="ISO State Code e.g. IN-TN")
    districtCode: Optional[str] = Field(default=None, description="District Code")
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
    password: str = Field(..., min_length=1, description="Registered account password")
    role: Literal["farmer", "staff"] = Field(default="farmer", description="Role to sign in as")
    authMethod: Optional[Literal["password", "telegram_otp"]] = Field(default="password", description="Authentication mode (deprecated)")
    telegramOtp: Optional[str] = Field(default=None, description="Telegram OTP (deprecated)")

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
    country: Optional[str] = "India"
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    stateCode: Optional[str] = None
    districtCode: Optional[str] = None
    taluk: Optional[str] = None
    mandiName: Optional[str] = None
    farmerId: Optional[str] = None
    totalLandAcres: Optional[Union[int, float]] = None
    landUnit: Optional[str] = "Acres"
    primaryCrop: Optional[str] = None
    soilType: Optional[str] = None
    irrigationSource: Optional[str] = None
    irrigationSources: Optional[List[str]] = None
    otherIrrigationDetail: Optional[str] = None
    aadhaarMasked: Optional[str] = None
    isAadhaarVerified: Optional[bool] = False
    isPhoneVerified: Optional[bool] = False
    profilePhoto: Optional[str] = None
    createdAt: str
    telegramLinked: Optional[bool] = False
    telegramUsername: Optional[str] = None
    farmCoordinates: Optional[Dict[str, Any]] = None


class AuthTokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresInMinutes: int
    user: UserSummary


class FarmerProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Farmer full name")
    phone: str = Field(..., min_length=10, max_length=15, description="10-digit mobile number")
    country: Optional[str] = Field(default="India", max_length=50)
    village: Optional[str] = Field(default=None, max_length=120, description="Village or town")
    location: str = Field(..., min_length=2, max_length=120, description="Village and block")
    district: str = Field(..., min_length=2, max_length=80, description="District name")
    state: str = Field(..., min_length=2, max_length=80, description="State / Union Territory")
    taluk: Optional[str] = Field(default=None, max_length=100, description="Taluk / Tehsil / Mandal")
    stateCode: Optional[str] = None
    districtCode: Optional[str] = None
    totalLandAcres: int = Field(..., description="Positive whole-number acres")
    landUnit: Optional[str] = Field(default="Acres", max_length=20, description="Land measurement unit")
    primaryCrop: str = Field(..., min_length=2, max_length=100, description="Primary crop cultivated")
    soilType: str = Field(default="Alluvial Clay Loam", max_length=100, description="Dominant soil type")
    irrigationSource: Optional[str] = Field(default=None, max_length=250, description="Source of irrigation")
    irrigationSources: Optional[List[str]] = Field(default=None, description="Multiple irrigation sources")
    otherIrrigationDetail: Optional[str] = Field(default=None, max_length=150)
    aadhaarMasked: Optional[str] = Field(default="XXXX-XXXX-4921", description="Masked Aadhaar identifier")
    preferredLanguage: Optional[str] = Field(default=None, description="Preferred language")
    profilePhoto: Optional[str] = Field(default=None, description="Optional profile photo data URL or URI")

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


class FarmerProfileUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Farmer full name")
    phone: str = Field(..., min_length=10, max_length=15, description="10-digit mobile number")
    country: Optional[str] = Field(default="India", max_length=50)
    village: Optional[str] = Field(default=None, max_length=120, description="Village or town")
    location: Optional[str] = Field(default=None, max_length=150, description="Location description")
    district: str = Field(..., min_length=2, max_length=80, description="District name")
    state: str = Field(..., min_length=2, max_length=80, description="State / Union Territory")
    taluk: Optional[str] = Field(default=None, max_length=100, description="Taluk / Tehsil / Mandal")
    stateCode: Optional[str] = None
    districtCode: Optional[str] = None
    totalLandAcres: int = Field(default=2, ge=1, le=5000, description="Positive whole-number acres")
    landUnit: Optional[str] = Field(default="Acres", max_length=20, description="Land measurement unit")
    primaryCrop: str = Field(default="Paddy (Samba)", min_length=2, max_length=100, description="Primary crop cultivated")
    soilType: str = Field(default="Alluvial Clay Loam", max_length=100, description="Dominant soil type")
    irrigationSource: Optional[str] = Field(default=None, max_length=250, description="Source of irrigation")
    irrigationSources: Optional[List[str]] = Field(default=None, description="Multiple irrigation sources")
    otherIrrigationDetail: Optional[str] = Field(default=None, max_length=150)
    preferredLanguage: Optional[str] = Field(default="en", description="Preferred regional language")
    profilePhoto: Optional[str] = Field(default=None, description="Optional profile photo data URL or URI")

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
        if val in LANGUAGE_CODE_MAP:
            return val
        for code, name in LANGUAGE_CODE_MAP.items():
            if val.lower() == name.lower():
                return code
        return "en"

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
    country: Optional[str] = "India"
    village: Optional[str] = None
    location: str
    district: str
    state: str
    stateCode: Optional[str] = None
    districtCode: Optional[str] = None
    taluk: Optional[str] = None
    totalLandAcres: Union[int, float]
    landUnit: Optional[str] = "Acres"
    primaryCrop: str
    soilType: str
    irrigationSource: str
    irrigationSources: Optional[List[str]] = None
    preferredLanguage: Optional[str] = None
    aadhaarMasked: Optional[str] = None
    isPhoneVerified: Optional[bool] = False
    profilePhoto: Optional[str] = None
    createdAt: str


class ProcurementBookingCreate(BaseModel):
    farmerName: str = Field(..., min_length=2, max_length=100, description="Farmer name")
    farmerId: Optional[str] = Field(default="TN-AGRI-2026-8841", description="Farmer ID")
    mandiName: str = Field(..., min_length=3, max_length=150, description="Regulated Market or DPC centre")
    crop: str = Field(..., min_length=2, max_length=100, description="Crop variety")
    cropVariety: Optional[str] = Field(default=None, max_length=100, description="Specific variety (e.g. CR 1009 Sub 1, BPT 5204)")
    harvestDate: str = Field(..., description="Harvest date (YYYY-MM-DD)")
    quantityBags: int = Field(..., ge=1, le=5000, description="Number of bags")
    preferredDate: Optional[str] = Field(default=None, description="Booking date (YYYY-MM-DD)")
    slotDate: Optional[str] = Field(default=None, description="Booking date alias (YYYY-MM-DD)")
    timeWindow: str = Field(default="08:30 AM - 11:30 AM", description="Reporting time window")

    @model_validator(mode="after")
    def validate_booking_and_harvest_dates(self):
        b_date_str = (self.preferredDate or self.slotDate or "").strip()
        if not b_date_str:
            raise ValueError("Booking date ('preferredDate' or 'slotDate') is required.")
        self.preferredDate = b_date_str

        from datetime import date, timedelta
        # 1. Validate Booking Date
        try:
            b_date = date.fromisoformat(b_date_str)
        except ValueError:
            raise ValueError("Invalid booking date format. Expected YYYY-MM-DD.")
        if b_date < date.today():
            raise ValueError("Booking date cannot be in the past. Please select today or a future date.")

        # 2. Validate Harvest Date
        h_date_str = (self.harvestDate or "").strip()
        if not h_date_str:
            raise ValueError("Harvest date ('harvestDate') is required.")
        try:
            h_date = date.fromisoformat(h_date_str)
        except ValueError:
            raise ValueError("Invalid harvest date format. Expected YYYY-MM-DD.")
        if h_date < date.today():
            raise ValueError("Harvest date cannot be in the past. Please select today or a future date.")
        if h_date > date.today() + timedelta(days=30):
            raise ValueError("Harvest date cannot be more than 30 days ahead.")

        return self


class LanguagePreferenceRequest(BaseModel):
    preferredLanguage: str = Field(..., description="Preferred regional language code")

    @field_validator("preferredLanguage")
    def validate_lang(cls, v):
        if not v or not v.strip():
            return "en"
        val = v.strip().lower()
        if val in LANGUAGE_CODE_MAP:
            return val
        for code, name in LANGUAGE_CODE_MAP.items():
            if val == name.lower():
                return code
        return "en"


class ProcurementBookingResponse(BaseModel):
    id: str
    bookingId: str
    tokenNumber: str
    farmerName: str
    farmerId: str
    mandiName: str
    crop: str
    cropVariety: Optional[str] = None
    harvestDate: Optional[str] = None
    quantityBags: int
    estimatedWeightQuintals: float
    slotDate: str
    timeWindow: str
    status: str
    moisturePercent: Optional[float] = None
    actualNetWeightQuintals: Optional[float] = None
    qualityNotes: Optional[str] = None
    qualityInspection: Optional[Dict[str, Any]] = None
    noShowDetails: Optional[Dict[str, Any]] = None
    isNowServing: Optional[bool] = False
    createdAt: str


class StaffBookingStatusUpdate(BaseModel):
    status: Literal["confirmed", "quality_checked", "weighed", "dbt_completed", "cancelled"]
    moisturePercent: Optional[float] = Field(None, ge=5.0, le=30.0)
    actualNetWeightQuintals: Optional[float] = Field(None, gt=0)
    qualityNotes: Optional[str] = None


class StaffQualityInspectionRequest(BaseModel):
    qualityStatus: Literal["ACCEPTED", "PARTIALLY_ACCEPTED", "REJECTED"]
    qualityGrade: str = Field(default="FAQ Grade A", max_length=80)
    moisturePercent: float = Field(..., ge=5.0, le=35.0, description="Moisture reading percentage")
    declaredWeightKg: Optional[float] = Field(default=None, ge=0.0)
    acceptedWeightKg: float = Field(default=0.0, ge=0.0)
    rejectedWeightKg: float = Field(default=0.0, ge=0.0)
    rejectionReason: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_inspection(self):
        if self.qualityStatus in ("REJECTED", "PARTIALLY_ACCEPTED"):
            if not (self.rejectionReason and self.rejectionReason.strip()):
                raise ValueError("Rejection reason is required when quality is REJECTED or PARTIALLY_ACCEPTED.")
        if self.qualityStatus == "ACCEPTED":
            if self.acceptedWeightKg <= 0:
                raise ValueError("Accepted weight must be greater than zero for ACCEPTED outcome.")
        elif self.qualityStatus == "REJECTED":
            if self.rejectedWeightKg <= 0:
                raise ValueError("Rejected weight must be greater than zero for REJECTED outcome.")
        elif self.qualityStatus == "PARTIALLY_ACCEPTED":
            if self.acceptedWeightKg <= 0 or self.rejectedWeightKg <= 0:
                raise ValueError("Both accepted and rejected weights must be greater than zero for PARTIALLY_ACCEPTED outcome.")
        if self.declaredWeightKg and (self.acceptedWeightKg + self.rejectedWeightKg) > (self.declaredWeightKg + 0.1):
            raise ValueError(f"Total inspected weight ({self.acceptedWeightKg + self.rejectedWeightKg} kg) cannot exceed declared weight ({self.declaredWeightKg} kg).")
        return self


class StaffNoShowRequest(BaseModel):
    reason: Optional[str] = Field(default="Farmer did not report for allocated slot", max_length=300)


class CallNextTokenRequest(BaseModel):
    centreCode: Optional[str] = None
    date: Optional[str] = None
    slotDate: Optional[str] = None
    counterId: Optional[str] = "Counter-1"


class ProcurementRateCreate(BaseModel):
    crop: str = Field(..., min_length=2, max_length=100)
    cropVariety: Optional[str] = Field(default="All Varieties", max_length=100)
    centreCode: Optional[str] = Field(default="ALL", max_length=50)
    ratePerKg: float = Field(..., gt=0, le=5000)
    ratePerQuintal: Optional[float] = Field(default=None, gt=0, le=50000)
    effectiveDate: str = Field(..., description="Effective date (YYYY-MM-DD)")
    isActive: bool = Field(default=True)
    sourceLabel: str = Field(default="TNAU / TNCSC Minimum Support Price (MSP)", max_length=150)
    notes: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def compute_quintal_rate(self):
        if self.ratePerQuintal is None and self.ratePerKg:
            self.ratePerQuintal = round(self.ratePerKg * 100.0, 2)
        return self


class ProcurementRateResponse(BaseModel):
    id: str
    crop: str
    cropVariety: str
    centreCode: str
    ratePerKg: float
    ratePerQuintal: float
    effectiveDate: str
    isActive: bool
    sourceLabel: str
    notes: Optional[str] = None
    createdAt: str


class CounterInfo(BaseModel):
    counterId: str = Field(..., description="Unique counter identifier e.g. Counter-1")
    name: str = Field(..., description="Display name e.g. Weighbridge Counter #1")
    isActive: bool = Field(default=True)


class NowServingResponse(BaseModel):
    centreCode: str
    centreName: str
    date: str
    counterId: str = "Counter-1"
    counterName: Optional[str] = "Weighbridge Counter #1"
    counters: List[Dict[str, Any]] = Field(default_factory=list)
    currentServing: Optional[Dict[str, Any]] = None
    nextEligible: Optional[Dict[str, Any]] = None
    activeWaitingCount: int = 0
    lastCalledAt: Optional[str] = None


# ============================================================================
# PHASE 4: QUEUE ENHANCEMENT, CAPACITY & REPORTING MODELS
# ============================================================================

class CropReportSummary(BaseModel):
    crop: str
    totalBags: int = 0
    acceptedWeightKg: float = 0.0
    acceptedWeightQuintals: float = 0.0
    rejectedWeightKg: float = 0.0
    grossAmount: float = 0.0
    netAmount: float = 0.0
    completedCount: int = 0


class CounterThroughputSummary(BaseModel):
    counterId: str = "Counter-1"
    counterName: str = "Weighbridge #1"
    completedCount: int = 0
    tokensServed: int = 0
    totalWeightKg: float = 0.0
    totalAcceptedWeightKg: float = 0.0
    totalGrossAmount: float = 0.0


class DailyProcurementReportResponse(BaseModel):
    centreCode: str
    centreName: str
    date: str
    generatedAt: str
    totalBookings: int = 0
    cancelledCount: int = 0
    noShowCount: int = 0
    completedCount: int = 0
    checkedInCount: int = 0
    inQueueCount: int = 0
    processingCount: int = 0
    bookedCount: int = 0
    totalAcceptedWeightKg: float = 0.0
    totalAcceptedWeightQuintals: float = 0.0
    totalRejectedWeightKg: float = 0.0
    totalGrossAmount: float = 0.0
    totalDeductionsAmount: float = 0.0
    totalNetAmount: float = 0.0
    amountPending: float = 0.0
    amountProcessing: float = 0.0
    amountPaid: float = 0.0
    cropBreakdown: List[CropReportSummary] = Field(default_factory=list)
    counterThroughput: List[CounterThroughputSummary] = Field(default_factory=list)


class SlotCloseRequest(BaseModel):
    centreCode: str = Field(..., min_length=2, max_length=50)
    slotDate: str = Field(..., description="Target date YYYY-MM-DD")
    timeWindow: str = Field(..., description="Time window or 'all'")
    reason: str = Field(..., min_length=3, max_length=300, description="Mandatory closure reason")


class SlotReopenRequest(BaseModel):
    centreCode: str = Field(..., min_length=2, max_length=50)
    slotDate: str = Field(..., description="Target date YYYY-MM-DD")
    timeWindow: str = Field(..., description="Time window or 'all'")


class SlotClosureResponse(BaseModel):
    id: str
    centreCode: str
    slotDate: str
    timeWindow: str
    isClosed: bool
    closureReason: str
    closedByStaff: str
    closedAt: str
    reopenedByStaff: Optional[str] = None
    reopenedAt: Optional[str] = None


class FarmerQuantityLimitConfig(BaseModel):
    centreCode: Optional[str] = "ALL"
    maxBagsPerSlot: int = Field(default=100, ge=1, le=5000)
    maxBagsPerDay: int = Field(default=250, ge=1, le=10000)
    maxWeightKgPerSlot: Optional[float] = Field(default=4000.0, ge=40.0)
    maxWeightKgPerDay: Optional[float] = Field(default=10000.0, ge=40.0)
    updatedBy: Optional[str] = None
    updatedAt: Optional[str] = None


class FarmerQuotaCheckResponse(BaseModel):
    farmerId: str
    date: str
    timeWindow: str
    maxBagsPerSlot: int
    maxBagsPerDay: int
    bookedBagsToday: int
    bookedBagsSlot: int
    remainingBagsToday: int
    remainingBagsSlot: int
    canBook: bool
    reason: Optional[str] = None


class ProcurementCentreCreate(BaseModel):
    centreCode: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=3, max_length=150)
    nameTa: Optional[str] = Field(default=None, max_length=200)
    district: str = Field(..., min_length=2, max_length=100)
    taluk: Optional[str] = Field(default=None, max_length=100)
    locationAddress: str = Field(..., min_length=5, max_length=250)
    supportedCrops: List[str] = Field(..., min_items=1)
    operatingHours: str = Field(default="08:30 AM - 05:30 PM (Mon - Sat)")
    dailyCapacityBags: int = Field(default=800, ge=50, le=50000)
    slotCapacityBags: int = Field(default=250, ge=10, le=10000)
    slotWindows: List[str] = Field(
        default=["08:30 AM - 11:30 AM", "11:30 AM - 02:30 PM", "02:30 PM - 05:30 PM"]
    )
    counters: Optional[List[Dict[str, Any]]] = Field(
        default=[
            {"counterId": "Counter-1", "name": "Weighbridge Counter #1", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge Counter #2", "isActive": True}
        ]
    )
    isActive: bool = Field(default=True)
    isDemoData: bool = Field(default=False)
    dataSourceLabel: Optional[str] = Field(default="TNCSC Direct Purchase Centre")


class ProcurementCentreUpdate(BaseModel):
    name: Optional[str] = None
    nameTa: Optional[str] = None
    district: Optional[str] = None
    taluk: Optional[str] = None
    locationAddress: Optional[str] = None
    supportedCrops: Optional[List[str]] = None
    operatingHours: Optional[str] = None
    dailyCapacityBags: Optional[int] = None
    slotCapacityBags: Optional[int] = None
    slotWindows: Optional[List[str]] = None
    counters: Optional[List[Dict[str, Any]]] = None
    isActive: Optional[bool] = None
    dataSourceLabel: Optional[str] = None


class ProcurementCentreStatusUpdate(BaseModel):
    isActive: bool
    reason: Optional[str] = Field(default=None, max_length=300)



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
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Farm latitude (-90 to 90)")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Farm longitude (-180 to 180)")
    fieldAreaAcres: Optional[float] = Field(default=1.0, gt=0.0, le=500.0, description="Cultivated field area in acres")


class FarmLocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Farm latitude between -90 and 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Farm longitude between -180 and 180")
    locationName: Optional[str] = Field(default="My Farm", max_length=120, description="Optional label for the farm location")
    consent: bool = Field(..., description="Explicit user consent to store farm coordinates in profile")


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
    counters: Optional[List[Dict[str, Any]]] = None
    isActive: bool = True
    isDemoData: bool = True
    dataSourceLabel: str = "TNCSC Direct Purchase Centre (Model Reference)"


class SlotStatusInfo(BaseModel):
    timeWindow: str
    maxCapacityBags: int
    bookedBags: int
    availableBags: int
    status: Literal["available", "filling_fast", "full", "closed"]
    isClosed: bool = False
    closureReason: Optional[str] = None


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


# ============================================================================
# PHASE 3: SMART IRRIGATION NOTIFICATION & PREFERENCE MODELS
# ============================================================================

class NotificationPreferencesUpdate(BaseModel):
    rainAlerts: Optional[bool] = None
    irrigationDemandAlerts: Optional[bool] = None
    heatDemandAlerts: Optional[bool] = None
    staleWeatherAlerts: Optional[bool] = None
    adviceChangeAlerts: Optional[bool] = None
    pushEnabled: Optional[bool] = None
    # Mandi Price Alerts
    mandiPriceAlerts: Optional[bool] = None
    mandiPriceSurgeAlerts: Optional[bool] = None
    mandiPriceDropAlerts: Optional[bool] = None
    mandiStaleFeedAlerts: Optional[bool] = None
    mandiSelectedCommodities: Optional[List[str]] = None
    mandiSelectedMarkets: Optional[List[str]] = None
    mandiPriceThresholdPercent: Optional[float] = None


class NotificationPreferencesResponse(BaseModel):
    userId: str
    farmerId: Optional[str] = None
    rainAlerts: bool = True
    irrigationDemandAlerts: bool = True
    heatDemandAlerts: bool = True
    staleWeatherAlerts: bool = True
    adviceChangeAlerts: bool = True
    pushEnabled: bool = False
    pushConfigured: bool = False
    # Mandi Price Alerts
    mandiPriceAlerts: bool = True
    mandiPriceSurgeAlerts: bool = True
    mandiPriceDropAlerts: bool = True
    mandiStaleFeedAlerts: bool = True
    mandiSelectedCommodities: List[str] = Field(default_factory=list)
    mandiSelectedMarkets: List[str] = Field(default_factory=list)
    mandiPriceThresholdPercent: float = 5.0
    updatedAt: Optional[str] = None


class PushSubscriptionPayload(BaseModel):
    endpoint: str = Field(..., min_length=5, description="Browser push service endpoint URL")
    keys: Optional[Dict[str, str]] = Field(default_factory=dict, description="P-256 and auth crypto keys")
    expirationTime: Optional[float] = None


class PushStatusResponse(BaseModel):
    pushConfigured: bool
    inAppActive: bool
    vapidPublicKey: Optional[str] = None
    subscribed: bool = False
    note: str


class IrrigationAlertCheckSummary(BaseModel):
    checkedFarmers: int
    generatedAlerts: int
    skippedDeduplicated: int
    skippedByPreferences: int
    rateLimited: int
    workerId: str
    timestamp: str
    leaseAcquired: bool = True
    note: Optional[str] = None


# ============================================================================
# LIVE MARKET MANDI PRICES MODELS (DATA.GOV.IN AGMARKNET DATASET)
# Resource ID: 9ef84268-d588-465a-a308-a864a43d0070
# ============================================================================

class MarketCommodityItemModel(BaseModel):
    id: str
    state: str
    district: str
    market: str
    mandi: str
    commodity: str
    crop: str
    commodityTa: Optional[str] = None
    cropTa: Optional[str] = None
    variety: str
    grade: str
    arrivalDate: str
    arrivalDateHuman: str
    date: str
    minPrice: float
    maxPrice: float
    modalPrice: float
    unit: str = "Quintal"
    trend: str = "steady"
    change: str = "₹0"


class MarketPricesPaginationModel(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


class MarketPricesResponseModel(BaseModel):
    dataSource: str
    sourceUrl: str
    resourceId: str
    sourceStatus: str
    sourceConfigured: bool
    isLive: bool
    isStale: bool
    sourceArrivalDate: Optional[str] = None
    lastSuccessfulFetchTime: Optional[str] = None
    lastCheckedTime: str
    commodities: List[MarketCommodityItemModel]
    pagination: MarketPricesPaginationModel
    availableDistricts: List[str]
    availableCommodities: List[str]
    staleNoticeEn: Optional[str] = None
    staleNoticeTa: Optional[str] = None
    error: Optional[str] = None
    timestamp: str
    demoNoticeEn: Optional[str] = None
    demoNoticeTa: Optional[str] = None
    hasNewData: Optional[bool] = None
    syncStatus: Optional[str] = "UP_TO_DATE"
    syncMessageEn: Optional[str] = None
    syncMessageTa: Optional[str] = None
    refreshIntervalMinutes: Optional[int] = 15
    nextScheduledRefreshTime: Optional[str] = None


# ============================================================================
# FARMER SUPPORT FEATURES (SECTIONS 1-6) & MARKETPLACE (SECTION 7) MODELS
# ============================================================================

class BilingualText(BaseModel):
    en: str = Field(..., description="English text")
    ta: Optional[str] = Field(default="", description="Tamil translation")


class SupportContactInfo(BaseModel):
    name: Optional[str] = Field(default=None, description="Official nodal officer name (only when publicly gazetted)")
    designation: Optional[str] = Field(default=None, description="Official title / designation")
    contactType: Literal["institutional_office", "individual_officer", "helpline", "unverified"] = "institutional_office"
    officePhone: Optional[str] = Field(default=None, description="Verified institutional office desk or helpline number")
    email: Optional[str] = Field(default=None, description="Verified institutional email address")
    address: Optional[str] = Field(default=None, description="Official postal / campus address")
    verificationNote: Optional[str] = Field(default=None, description="Source excerpt or administrator verification notes")
    contactVerificationStatus: Literal["verified_official", "unverified", "no_contact_disclosed", "stale_review_needed"] = "verified_official"


class TrainingMeta(BaseModel):
    startDate: Optional[str] = Field(default=None, description="Training start date (YYYY-MM-DD)")
    endDate: Optional[str] = Field(default=None, description="Training end date (YYYY-MM-DD)")
    registrationDeadline: Optional[str] = Field(default=None, description="Registration deadline (YYYY-MM-DD)")
    mode: Optional[Literal["In-Person", "Online", "Hybrid"]] = "In-Person"
    venue: Optional[str] = Field(default=None, description="Physical venue or online meeting link notice")
    fees: Optional[str] = Field(default="Free", description="Fee status (e.g. Free, Subsidized ₹100/day)")
    capacity: Optional[int] = Field(default=None, description="Maximum participant intake")
    eligibility: Optional[str] = Field(default=None, description="Eligibility criteria")
    curriculumHighlights: Optional[List[str]] = Field(default_factory=list, description="Core practical skills taught")
    scheduleStatus: Literal["current_active", "recurring_monthly", "historical_reference", "unverified_schedule"] = "current_active"
    verificationNote: Optional[str] = Field(default=None, description="Verification note regarding currentness of schedule")


class CropStageGuidance(BaseModel):
    stageNumber: int = Field(..., ge=1, le=10)
    stageName: str = Field(..., description="Stage name (e.g., Nursery Preparation, Flowering)")
    stageNameTa: Optional[str] = None
    daysRange: str = Field(..., description="Timeline range (e.g., Day 1 to 20)")
    keyActivities: List[str] = Field(default_factory=list, description="Field operations required")
    keyActivitiesTa: Optional[List[str]] = Field(default_factory=list)
    waterManagement: str = Field(..., description="Irrigation scheduling & AWD water balance guidance")
    waterManagementTa: Optional[str] = None
    nutrientRegime: Optional[str] = Field(default=None, description="Basal and top-dressing fertilization or bio-inputs")
    pestMonitoring: Optional[str] = Field(default=None, description="Target pests and non-chemical IPM monitoring")
    criticalAlert: Optional[str] = Field(default=None, description="Key caution to avoid crop loss")


class CropGuideMeta(BaseModel):
    cropName: str = Field(..., description="Crop common name")
    cropNameTa: Optional[str] = None
    season: str = Field(..., description="Recommended cropping season in TN (e.g., Samba, Thaladi, Kuruvai)")
    durationDays: int = Field(..., gt=0, description="Total seed-to-harvest duration in days")
    stages: List[CropStageGuidance] = Field(default_factory=list, description="Ordered stage-by-stage agronomic steps")
    harvestIndices: List[str] = Field(default_factory=list, description="Visual and physical maturity signs")
    harvestIndicesTa: Optional[List[str]] = Field(default_factory=list)
    marketChannels: List[str] = Field(default_factory=list, description="Destination regulated mandis, DPC yards, or mills")
    marketChannelsTa: Optional[List[str]] = Field(default_factory=list)


class SupportSubsidyMeta(BaseModel):
    schemeName: str = Field(..., description="Associated state or central government scheme (MIDH, TNHM, PMFME, ACABC)")
    costNorm: str = Field(..., description="Official benchmark unit cost norm per unit/sq.m")
    subsidyPercent: Union[int, float] = Field(..., ge=0, le=100, description="Statutory subsidy percentage")
    maxEligibleArea: Optional[str] = Field(default=None, description="Maximum ceiling or area cap")
    applicationPortal: Optional[str] = Field(default=None, description="Official government application URL")
    applicableSectors: Optional[List[str]] = Field(default_factory=list)

class EntrepreneurshipMeta(BaseModel):
    businessIdea: BilingualText
    targetCustomers: List[str]
    requiredEquipment: List[str]
    inputsRequired: List[str]
    startupPlanningSteps: List[str]
    estimatedCapitalCost: str
    estimatedMonthlyOperatingCost: str
    revenueAssumptions: str
    riskAnalysis: List[str]
    officialSupportResources: List[str]


class OrganicMeta(BaseModel):
    soilHealthPractices: List[str]
    compostingMethods: List[str]
    bioInputsRecipes: List[Dict[str, Any]]
    cropRotationPlanning: List[str]
    organicPestManagement: List[str]
    transitionTimelineYears: int = 3
    certificationSteps: List[str]


class ProtectedCultivationMeta(BaseModel):
    structureType: str
    suitableCrops: List[str]
    irrigationFertigationRegime: str
    pestDiseaseManagement: List[str]
    setupRequirements: List[str]
    annualMaintenanceTips: List[str]
    applicableSchemes: List[str]


class ValueAdditionMeta(BaseModel):
    produceCategory: str
    processingIdea: BilingualText
    hygieneStandards: List[str]
    packagingOptions: List[str]
    shelfLifeExtensionDays: str
    estimatedCostingBreakdown: str
    marketingChannels: List[str]


class DirectMarketMeta(BaseModel):
    marketType: str = Field(..., description="e.g. e-NAM Electronic Exchange, Regulated APMC Yard, Uzhavar Sandhai Direct Farm Gate")
    platformPortal: Optional[str] = Field(default=None, description="Direct trading portal URL")
    helplinePhone: Optional[str] = Field(default=None, description="Official farmer trading helpline")
    tradingWorkflow: List[str] = Field(default_factory=list, description="Step-by-step registration, lot entry, assaying, and bidding procedure")
    tradingWorkflowTa: Optional[List[str]] = Field(default_factory=list)
    qualityAssayingParameters: List[str] = Field(default_factory=list, description="Moisture, foreign matter, and grading tolerances")
    disputeResolutionDesk: Optional[str] = Field(default=None, description="Market committee grievance and assaying appeal mechanism")
    buyerLinkageChannels: List[str] = Field(default_factory=list, description="Available buyer channels (Wholesale, Direct Retail, FPO Bulk, Inter-state)")


class FarmerSupportContentModel(BaseModel):
    contentId: str = Field(..., description="Unique alphanumeric identifier (e.g. fsc_trg_kvk_001)")
    category: Literal[
        "training",
        "entrepreneurship",
        "organic",
        "special_operation",
        "protected_cultivation",
        "value_addition",
        "direct_market"
    ]
    subCategory: Optional[str] = None
    contentType: Literal["static_educational", "training_announcement", "guidance_package", "market_protocol"] = "static_educational"
    title: BilingualText
    description: BilingualText
    district: str = Field(default="All", description="District name or 'All'")
    state: str = Field(default="Tamil Nadu", description="State name (e.g. Tamil Nadu, Andhra Pradesh, Karnataka, All-India)")
    language: Literal["en", "ta", "bilingual"] = "bilingual"
    institution: str = Field(..., description="Authoritative university or government institution")
    officialSourceUrl: str = Field(..., description="Direct HTTPS link to government/university publication")
    sourceExcerpt: Optional[str] = Field(default=None, description="Direct text excerpt from official source for audit")
    sourcePublicationDate: Optional[str] = Field(default=None, description="Official notice date (YYYY-MM-DD)")
    lastCheckedDate: str = Field(..., description="Date when source was last verified live (YYYY-MM-DD)")
    verificationStatus: Literal["verified_official", "pending_review", "stale_review_needed"] = "verified_official"
    activeStatus: Literal["active", "expired", "archived"] = "active"
    adminReviewed: bool = Field(default=False, description="Flag indicating administrator review; prevents automated seed overwrite")
    contact: SupportContactInfo
    trainingMeta: Optional[TrainingMeta] = None
    cropGuideMeta: Optional[CropGuideMeta] = None
    subsidyMeta: Optional[SupportSubsidyMeta] = None
    entrepreneurshipMeta: Optional[EntrepreneurshipMeta] = None
    organicMeta: Optional[OrganicMeta] = None
    protectedCultivationMeta: Optional[ProtectedCultivationMeta] = None
    valueAdditionMeta: Optional[ValueAdditionMeta] = None
    directMarketMeta: Optional[DirectMarketMeta] = None
    registrationInstructions: Optional[BilingualText] = None
    highlights: Optional[List[str]] = Field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class FarmerSupportContentResponse(BaseModel):
    items: List[FarmerSupportContentModel]
    total: int
    categories: List[str]
    districts: List[str]
    states: List[str] = Field(default_factory=lambda: ["Tamil Nadu", "All"])
    hasStaleNotice: bool = False


# ----------------------------------------------------------------------------
# FEATURE 7: FARMER MARKETPLACE MODELS & ORDER REQUEST WORKFLOW
# ----------------------------------------------------------------------------

class FarmerMarketplaceListingCreate(BaseModel):
    crop: str = Field(..., min_length=2, max_length=100, description="Produce or commodity name")
    variety: Optional[str] = Field(default=None, max_length=100, description="Specific variety or breed")
    category: str = Field(..., description="Category: Cereals, Pulses, Vegetables, Fruits, Spices, Oilseeds, Value Added")
    district: str = Field(..., description="Farm district in Tamil Nadu")
    village: Optional[str] = Field(default=None, max_length=100, description="Village or taluk location")
    quantity: float = Field(..., gt=0, description="Available stock quantity")
    unit: str = Field(..., description="Units: kg, Quintal, Bags (50kg), Bags (100kg), Tonnes, Litres, Dozen, Bunches")
    pricePerUnit: float = Field(..., gt=0, description="Direct expected price per unit in INR (₹)")
    isOrganicCertified: bool = Field(default=False, description="Is the produce certified organic?")
    certificationBody: Optional[str] = Field(default=None, max_length=200, description="Certification scope or agency (e.g. TNOCD)")
    harvestDate: Optional[str] = Field(default=None, description="Harvest date or availability date (YYYY-MM-DD)")
    availableUntil: Optional[str] = Field(default=None, description="Listing expiration date (YYYY-MM-DD)")
    fulfillmentModes: List[str] = Field(
        default=["Farm Gate Pickup"],
        description="Delivery/pickup options: Farm Gate Pickup, Local Delivery within District, Buyer Transport"
    )
    serviceArea: Optional[str] = Field(default=None, max_length=150, description="General delivery / service taluk radius")
    photoUrls: Optional[List[str]] = Field(default_factory=list, description="Produce photo preview URLs")
    showContactToBuyers: bool = Field(default=False, description="Explicit farmer consent to display phone/WhatsApp to public buyers")
    description: Optional[str] = Field(default=None, max_length=1000, description="Produce grade, freshness, or packaging note")
    isDemoData: bool = Field(default=False, description="Visibly marks simulated test records")


class FarmerMarketplaceListingUpdate(BaseModel):
    crop: Optional[str] = None
    variety: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    pricePerUnit: Optional[float] = None
    isOrganicCertified: Optional[bool] = None
    certificationBody: Optional[str] = None
    harvestDate: Optional[str] = None
    availableUntil: Optional[str] = None
    fulfillmentModes: Optional[List[str]] = None
    serviceArea: Optional[str] = None
    photoUrls: Optional[List[str]] = None
    showContactToBuyers: Optional[bool] = None
    description: Optional[str] = None
    listingStatus: Optional[Literal["active", "sold_out", "out_of_stock", "paused", "expired", "flagged"]] = None


class FarmerMarketplaceListingModel(BaseModel):
    listingId: str
    farmerId: str
    farmerName: str
    farmerPhone: str
    crop: str
    variety: Optional[str] = None
    category: str
    district: str
    village: Optional[str] = None
    quantity: float
    unit: str
    pricePerUnit: float
    isOrganicCertified: bool = False
    certificationBody: Optional[str] = None
    harvestDate: Optional[str] = None
    availableUntil: Optional[str] = None
    fulfillmentModes: List[str] = []
    serviceArea: Optional[str] = None
    photoUrls: List[str] = Field(default_factory=list)
    showContactToBuyers: bool = False
    description: Optional[str] = None
    listingStatus: Literal["active", "sold_out", "out_of_stock", "paused", "expired", "flagged"] = "active"
    viewCount: int = 0
    inquiryCount: int = 0
    reportCount: int = 0
    adminFlagged: bool = False
    flagReason: Optional[str] = None
    isDemoData: bool = False
    createdAt: str
    updatedAt: str


class MarketplaceListingReportRequest(BaseModel):
    reasonCategory: Literal["spam", "fake_price", "misleading_claims", "expired_produce", "other"]
    details: Optional[str] = Field(default=None, max_length=500)
    reporterPhone: Optional[str] = Field(default=None, max_length=15)


class FarmerMarketplaceResponse(BaseModel):
    items: List[FarmerMarketplaceListingModel]
    total: int
    page: int
    limit: int
    totalPages: int
    categories: List[str]
    districts: List[str]


class MarketplaceOrderRequestCreate(BaseModel):
    buyerName: str = Field(..., min_length=2, max_length=100, description="Buyer or wholesale customer name")
    buyerPhone: str = Field(..., min_length=10, max_length=15, description="Buyer phone number")
    requestedQuantity: float = Field(..., gt=0, description="Quantity requested to purchase")
    fulfillmentPreference: str = Field(default="Farm Gate Pickup", description="Pickup or delivery choice")
    deliveryAddress: Optional[str] = Field(default=None, max_length=300, description="Delivery location if local delivery requested")
    message: Optional[str] = Field(default=None, max_length=500, description="Special instructions, harvest timing, or packaging preferences")


class MarketplaceOrderRequestModel(BaseModel):
    orderId: str
    listingId: str
    farmerId: str
    crop: str
    unit: str
    pricePerUnit: float
    totalEstimatedPrice: float
    buyerName: str
    buyerPhone: str
    requestedQuantity: float
    fulfillmentPreference: str
    deliveryAddress: Optional[str] = None
    message: Optional[str] = None
    status: Literal["pending", "confirmed", "rejected", "completed"] = "pending"
    createdAt: str
    updatedAt: str


# ============================================================================
# SPECIAL OPERATION — FROM FIRST STEP TO FIRST SALE (10-STEP JOURNEY)
# ============================================================================

class SpecialOperationProfileInput(BaseModel):
    district: str = Field(default="Salem", description="Farmer district (e.g. Salem, Thanjavur, Coimbatore)")
    landArea: float = Field(default=1.0, ge=0.01, description="Size of available land")
    landUnit: Literal["acres", "cents", "guntas", "sq_ft", "unknown"] = "acres"
    waterAvailability: Literal["ample_borewell", "canal_seasonal", "rainfed_only", "tank_limited", "unknown"] = "ample_borewell"
    soilType: Literal["red_sandy_loam", "clay_loam", "alluvial", "black_cotton", "unknown"] = "unknown"
    season: Literal["samba_thaladi", "kuruvai", "navarai_summer", "rainfed_monsoon", "year_round", "unknown"] = "unknown"
    budgetRange: Literal["micro_under_15k", "low_15k_35k", "medium_35k_75k", "flexible_above_75k", "unknown"] = "low_15k_35k"
    availableLabour: Literal["family_only_1_2", "hired_occasional", "abundant", "unknown"] = "family_only_1_2"
    farmingGoal: Literal["commercial_income", "household_consumption", "low_risk_learning", "organic_lifestyle"] = "commercial_income"


class SpecialOperationCropRecommendation(BaseModel):
    cropId: str
    cropName: BilingualText
    varietySuggestions: List[str]
    durationDays: int
    suitabilityScore: int  # 0 - 100
    suitabilityReason: BilingualText
    waterNeedLevel: str
    waterNeedText: BilingualText
    budgetEstimatePerAcre: str
    tradeOffsAndRisks: List[BilingualText]
    marketChannels: List[str]
    verifiedReference: Dict[str, str]


class JourneyObservation(BaseModel):
    id: str
    date: str
    stageNumber: int
    note: str
    photoUrl: Optional[str] = None
    isDeviation: bool = False
    deviationReason: Optional[str] = None
    createdAt: str


class CostItemEntry(BaseModel):
    category: str  # 'seeds', 'land_prep', 'fertilizer', 'irrigation', 'plant_protection', 'labour', 'harvesting', 'transport'
    itemName: BilingualText
    benchmarkRatePerAcre: float
    userQuantity: float
    userUnitPrice: float
    isUserEdited: bool = False
    notes: Optional[str] = None


class JourneyCostsWorksheet(BaseModel):
    entries: List[CostItemEntry] = []
    totalOperatingCost: float = 0.0
    costPerUnitArea: float = 0.0
    disclaimer: str = "Estimates are illustrative guidelines based on TNAU Cost of Cultivation benchmarks. Profit is never guaranteed."


class JourneySalePlan(BaseModel):
    targetChannels: List[str] = []
    mandiPriceSnapshot: Optional[Dict[str, Any]] = None
    gradingPackagingDetails: List[str] = []
    transportConsiderations: str = ""
    disclaimer: str = "Quoted mandi prices are modal auction rates, not guaranteed buyback contracts."


class JourneyCompletionRecord(BaseModel):
    harvestDate: str
    harvestedQuantity: float
    harvestUnit: str
    gradeBreakdown: Dict[str, float] = {}  # e.g. {"gradeA": 75.0, "gradeB": 25.0}
    buyerNameOrChannel: str
    achievedPricePerUnit: float
    grossRevenue: float
    totalOperatingCost: float
    netProfitOrLoss: float
    farmerReflection: Optional[str] = None
    completedAt: str


class SpecialOperationJourneyModel(BaseModel):
    journeyId: str
    farmerId: str
    farmerName: str
    farmerPhone: str
    status: Literal["in_progress", "paused", "completed", "abandoned"] = "in_progress"
    currentStep: int = Field(default=1, ge=1, le=10)
    profileInput: SpecialOperationProfileInput
    selectedCropId: Optional[str] = None
    selectedCropName: Optional[BilingualText] = None
    plantingDate: Optional[str] = None
    landAreaNormalizedAcres: float = 1.0
    checklists: Dict[str, bool] = Field(default_factory=dict)
    observations: List[JourneyObservation] = Field(default_factory=list)
    costsWorksheet: JourneyCostsWorksheet = Field(default_factory=JourneyCostsWorksheet)
    salePlan: JourneySalePlan = Field(default_factory=JourneySalePlan)
    completionRecord: Optional[JourneyCompletionRecord] = None
    remindersActive: bool = True
    createdAt: str
    updatedAt: str


class SpecialOperationStepUpdateRequest(BaseModel):
    currentStep: int = Field(..., ge=1, le=10)
    status: Optional[Literal["in_progress", "paused", "completed", "abandoned"]] = None
    profileInput: Optional[SpecialOperationProfileInput] = None
    selectedCropId: Optional[str] = None
    plantingDate: Optional[str] = None
    checklists: Optional[Dict[str, bool]] = None
    costsWorksheet: Optional[JourneyCostsWorksheet] = None
    salePlan: Optional[JourneySalePlan] = None
    completionRecord: Optional[JourneyCompletionRecord] = None
    remindersActive: Optional[bool] = None


# ============================================================================
# MODULE A: AGRI ENTREPRENEURSHIP MODELS
# ============================================================================

class BusinessIdeaMatchRequest(BaseModel):
    interests: List[str] = Field(default_factory=list, description="Farmer interest areas: organic_inputs, value_addition, machinery_rental, solar_drying, cattle_feed, cold_storage, nursery")
    skills: List[str] = Field(default_factory=list, description="Skills possessed: technical_operations, marketing_sales, packaging, basic_accounts, mechanical")
    locationDistrict: str = Field(default="Salem", description="Tamil Nadu district for enterprise location")
    investmentBudget: float = Field(default=150000.0, ge=0, description="Available farmer investment budget in INR")
    availableProduce: List[str] = Field(default_factory=list, description="Raw farm crops or produce available: Tomato, Groundnut, Paddy, Tapioca, Millets, Coconut, Spices, Banana")
    landOrSpaceAvailable: Optional[str] = Field(default="shed_200sqft", description="Available working space or infrastructure")


class BusinessIdeaItem(BaseModel):
    ideaId: str
    title: BilingualText
    category: str
    matchScore: int = Field(..., ge=0, le=100)
    matchReasons: List[BilingualText] = Field(default_factory=list)
    suitabilitySummary: BilingualText
    estimatedStartupCapex: Dict[str, float] = Field(default_factory=dict)
    estimatedMonthlyOpex: Dict[str, float] = Field(default_factory=dict)
    typicalBreakevenMonths: str
    targetCustomers: List[BilingualText] = Field(default_factory=list)
    requiredSkillsAndEquipment: List[BilingualText] = Field(default_factory=list)
    officialResources: List[Dict[str, str]] = Field(default_factory=list)
    statutoryRequirements: List[BilingualText] = Field(default_factory=list)
    nonGuaranteeDisclaimer: str = "Indicative assumptions based on TNAU DABD and EDII-TN benchmarks. No loan approval, subsidy sanction, or profit is guaranteed."


class BusinessIdeaMatchResponse(BaseModel):
    matchedIdeas: List[BusinessIdeaItem]
    farmerContextSummary: Dict[str, Any]
    disclaimer: str = "Matched proposals are educational templates for planning. Real enterprise viability depends on local market demand, raw material prices, and operational execution."


class BusinessPlanWizardData(BaseModel):
    productOrService: str = Field(..., description="Target business idea / enterprise name")
    customerSegment: List[str] = Field(default_factory=list, description="Target customer segments")
    equipmentAndInfrastructure: List[Dict[str, Any]] = Field(default_factory=list, description="List of items with name, quantity, unitCost, totalCost")
    rawMaterialInputs: List[Dict[str, Any]] = Field(default_factory=list, description="Monthly raw material requirements")
    operatingCosts: Dict[str, float] = Field(default_factory=dict, description="Itemized monthly opex: labour, electricity_fuel, packaging, logistics, marketing, maintenance")
    pricingStrategy: Dict[str, Any] = Field(default_factory=dict, description="productUnit, unitProductionCost, targetSellingPrice, expectedMonthlySalesUnits")
    distributionChannels: List[str] = Field(default_factory=list, description="Planned distribution and retail touchpoints")
    risksAndMitigations: List[Dict[str, Any]] = Field(default_factory=list, description="Risk assessment entries: risk and mitigation")
    regulatoryChecklist: Dict[str, bool] = Field(default_factory=dict, description="Udyam, FSSAI, GST, Bank Current Account, Fire/Pollution status")
    nextStepsRoadmap: List[Dict[str, Any]] = Field(default_factory=list, description="Action items with timeline and official resource links")


class BusinessPlanCalculationResult(BaseModel):
    totalStartupCapex: float = 0.0
    totalMonthlyOpex: float = 0.0
    monthlyGrossRevenue: float = 0.0
    monthlyNetOperatingSurplus: float = 0.0
    breakevenMonthlyUnits: float = 0.0
    breakevenMonths: float = 0.0
    itemizedAssumptions: List[str] = Field(default_factory=list)
    disclaimer: str = "Estimates reflect user-entered figures and institutional benchmarks. Profit is never guaranteed."


class BusinessPlanModel(BaseModel):
    planId: str
    farmerId: str
    farmerName: str
    businessName: str
    ideaId: Optional[str] = None
    wizardData: BusinessPlanWizardData
    financialCalculations: BusinessPlanCalculationResult
    linkedSchemes: List[Dict[str, str]] = Field(default_factory=list)
    status: Literal["draft", "in_review", "finalized"] = "draft"
    createdAt: str
    updatedAt: str


class BusinessPlanCreateRequest(BaseModel):
    businessName: str = Field(..., min_length=2, max_length=150)
    ideaId: Optional[str] = None
    wizardData: BusinessPlanWizardData


class BusinessPlanUpdateRequest(BaseModel):
    businessName: Optional[str] = None
    wizardData: Optional[BusinessPlanWizardData] = None
    status: Optional[Literal["draft", "in_review", "finalized"]] = None


class BusinessPlanCalculationRequest(BaseModel):
    equipmentAndInfrastructure: List[Dict[str, Any]] = Field(default_factory=list)
    rawMaterialInputs: List[Dict[str, Any]] = Field(default_factory=list)
    operatingCosts: Dict[str, float] = Field(default_factory=dict)
    pricingStrategy: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MODULE B: VALUE-ADDED PRODUCTS MODELS
# ============================================================================

class ValueAdditionProductBlueprint(BaseModel):
    productId: str
    productName: BilingualText
    rawMaterial: str
    processingMethod: str
    processingMethodCategory: Literal["thermal_processing", "cold_extraction", "milling_pulverizing", "dehydration_drying", "fermentation_pickling"]
    fssaiCategory: str
    rawMaterialToFinishedRatio: float = Field(..., gt=0.0, le=1.0, description="Yield fraction: finished mass / raw material mass")
    typicalByproducts: List[Dict[str, Any]] = Field(default_factory=list)
    shelfLifeAndStorage: BilingualText
    storageTemperature: str
    requiredEquipment: List[Dict[str, Any]] = Field(default_factory=list)
    ingredientsAndRecipe: List[Dict[str, Any]] = Field(default_factory=list)
    standardOperatingProcedure: List[Dict[str, Any]] = Field(default_factory=list)
    foodSafetyAndHygiene: List[BilingualText] = Field(default_factory=list)
    packagingGuidance: BilingualText
    authoritativeReference: Dict[str, str] = Field(default_factory=dict)
    potentialSalesChannels: List[str] = Field(default_factory=list)
    trainingProviders: List[Dict[str, str]] = Field(default_factory=list)


class ValueAdditionCalculationRequest(BaseModel):
    productId: str
    rawMaterialQuantityKg: float = Field(..., gt=0)
    rawMaterialCostPerKg: float = Field(..., ge=0)
    yieldLossPercentage: Optional[float] = Field(default=None, ge=0.0, le=95.0, description="Optional override for yield waste %")
    processingCostPerKgOrBatch: float = Field(default=0.0, ge=0.0, description="Fuel, power, water, utility expenses per kg or batch")
    packagingCostPerFinishedUnit: float = Field(default=0.0, ge=0.0, description="Packaging bottle, pouch, sticker per unit")
    finishedUnitSize: float = Field(default=1.0, gt=0, description="Finished package size in kg or Litres (e.g. 0.5, 1.0)")
    labourCostTotal: float = Field(default=0.0, ge=0.0, description="Total labour cost for processing run")
    transportAndMarketingCost: float = Field(default=0.0, ge=0.0, description="Logistics and distribution cost")
    expectedSellingPricePerFinishedUnit: float = Field(..., gt=0, description="Anticipated sales price per finished pack")
    includeByproductRecovery: bool = Field(default=True)
    byproductSellingPricePerKg: Optional[float] = Field(default=None, ge=0.0)


class ValueAdditionCalculationResponse(BaseModel):
    productId: str
    productName: BilingualText
    rawMaterialQuantityKg: float
    effectiveYieldPercent: float
    yieldLossQuantityKg: float
    finishedProductQuantity: float
    finishedUnitsCount: int
    unitSize: float
    byproductQuantityKg: float
    byproductRevenue: float
    totalExpenses: Dict[str, float]
    finishedProductRevenue: float
    totalGrossRevenue: float
    estimatedGrossProfit: float
    estimatedProfitMarginPercent: float
    costPerFinishedUnit: float
    netProfitPerFinishedUnit: float
    breakevenSellingPricePerUnit: float
    itemizedAssumptions: List[str]
    authoritativeReference: Dict[str, str]
    disclaimer: str = "Yield ratios and processing steps cite official university and institute guidelines. Real farm gate profitability varies with raw material moisture, fuel efficiency, and market price realization."



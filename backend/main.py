"""
Namma Vivasayi AI - FastAPI Application with Authentication & RBAC
==================================================================
Provides REST APIs for:
1. System Health & Real MongoDB Connectivity Status
2. Farmer Registration & Login with Bcrypt & JWT
3. Role-Based Access Control (Farmer vs Procurement Staff)
4. Authenticated Farmer Profile & Procurement Bookings
5. Staff Procurement Centre Queue, Weighing & Transaction Management
"""

import os
import random
import re
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import (
    check_db_connection,
    get_farmers_collection,
    get_bookings_collection,
    get_users_collection,
    get_notifications_collection,
    get_centres_collection,
    get_telegram_link_tokens_collection,
)
from models import (
    FarmerRegisterRequest,
    LoginRequest,
    AuthTokenResponse,
    UserSummary,
    FarmerProfileCreate,
    FarmerProfileResponse,
    ProcurementBookingCreate,
    ProcurementBookingResponse,
    StaffBookingStatusUpdate,
    IrrigationCalculateRequest,
    CropRecommendRequest,
    ProcurementCentreInfo,
    CentreSlotsResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
    StaffCheckInRequest,
    StaffTransactionRequest,
    StaffWeighingCreateRequest,
    WeighingCalculationPreviewRequest,
    WeighingCalculationPreviewResponse,
    PaymentStatusUpdateRequest,
    DigitalBillResponse,
    StaffQueueStatusUpdateRequest,
    QueueTrackingResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    NotificationResponse,
    NotificationMarkReadResponse,
    SMSStatusResponse,
    # Phase 19 Models & Constants
    VALID_IRRIGATION_OPTIONS,
    REGIONAL_LANGUAGES,
    LANGUAGE_CODE_MAP,
    TelegramStatusResponse,
    TelegramLinkTokenRequest,
    TelegramLinkTokenResponse,
    TelegramLinkStatusResponse,
    TelegramSendOtpRequest,
    TelegramSendOtpResponse,
    TelegramVerifyOtpRequest,
    TelegramVerifyOtpResponse,
)
from telegram_auth import (
    is_telegram_configured,
    get_bot_username,
    generate_account_linking_token,
    check_or_poll_telegram_link,
    bind_verified_telegram_chat,
    send_telegram_otp,
    verify_telegram_otp,
)
from smart_farming import (
    get_district_weather,
    calculate_irrigation_advice,
    recommend_crops,
    analyze_plant_image_submission,
    get_market_prices,
    get_government_schemes,
    TNAU_DISEASE_REFERENCE_CATALOG,
    TN_DISTRICT_COORDINATES,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
    require_farmer,
    require_staff,
    bootstrap_staff_account,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from procurement import (
    get_all_centres,
    get_centre_slots_availability,
    create_booking_with_capacity_check,
    verify_procurement_token,
    process_gate_check_in,
    record_weighing_and_transaction_ledger,
    calculate_weighing_amounts,
    get_bill_by_id_or_number,
    get_farmer_bills,
    get_staff_bills,
    update_bill_payment_status,
    get_queue_tracking_for_booking,
    update_booking_queue_status,
    verify_staff_centre_access,
    cancel_booking_for_farmer,
)
from notifications import (
    create_in_app_notification,
    get_user_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    get_unread_notifications_count,
    sms_service,
    send_sms_notification_stub,
)
from ai_assistant import (
    process_farmer_chat_message,
    get_farmer_chat_history,
    clear_farmer_chat_history,
)

load_dotenv()

app = FastAPI(
    title="Namma Vivasayi AI API",
    description="Backend API with Authentication & Role-Based Access Control for Farmers & Procurement Staff",
    version="0.3.0"
)

# Configure CORS
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", r"^https:\/\/.*\.vercel\.app$").strip() or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event: provision initial trusted staff account
@app.on_event("startup")
async def startup_event():
    await bootstrap_staff_account()


def format_mongo_doc(doc: dict) -> dict:
    """Helper to convert MongoDB ObjectId to string and strip sensitive fields."""
    if not doc:
        return {}
    doc["id"] = str(doc.pop("_id", ""))
    doc.pop("hashed_password", None)
    return doc


@app.get("/")
async def root():
    return {
        "project": "Namma Vivasayi AI",
        "phase": "Phase 16 - Production & Hackathon Deployment Readiness",
        "status": "online",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "roles_supported": ["farmer", "staff"],
        "endpoints": {
            "health": "/api/health",
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "me": "GET /api/auth/me",
            "weather": "GET /api/weather",
            "chat": "POST /api/chat/message",
            "chat_status": "GET /api/chat/status",
            "bookings": "POST /api/procurement/bookings",
            "staff_queue": "GET /api/staff/queue",
            "docs": "/docs"
        }
    }


@app.get("/api/health")
async def health_check():
    """
    Checks backend health and performs a live ping against MongoDB.
    """
    db_status = await check_db_connection()
    return {
        "status": "healthy" if db_status["connected"] else "degraded",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": db_status
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS (PHASE 3)
# ============================================================================

# ============================================================================
# AUTHENTICATION & USER PROFILE HELPERS (PHASE 3 & PHASE 19)
# ============================================================================

async def build_user_summary(user: dict) -> UserSummary:
    """Constructs a fully populated, sanitized UserSummary object."""
    user_id_str = str(user.get("_id") or user.get("id"))
    farmers_col = get_farmers_collection()
    f_doc = None
    if user.get("role") == "farmer" and farmers_col is not None:
        f_doc = await farmers_col.find_one({
            "$or": [
                {"userId": user_id_str},
                {"farmerId": user.get("farmerId")},
                {"phone": user.get("phone")}
            ]
        })

    extra = f_doc or {}

    # Resolve land acres (whole integer or legacy float)
    raw_acres = extra.get("totalLandAcres", user.get("totalLandAcres"))
    acres_val = None
    if raw_acres is not None:
        try:
            acres_val = int(raw_acres) if float(raw_acres).is_integer() else float(raw_acres)
        except (ValueError, TypeError):
            acres_val = None

    # Resolve irrigation sources
    irr_sources = extra.get("irrigationSources") or user.get("irrigationSources")
    irr_source_str = extra.get("irrigationSource") or user.get("irrigationSource")
    if not irr_sources and irr_source_str:
        if isinstance(irr_source_str, list):
            irr_sources = irr_source_str
            irr_source_str = ", ".join(irr_source_str)
        else:
            irr_sources = [s.strip() for s in re.split(r"[,&]", str(irr_source_str)) if s.strip()]

    return UserSummary(
        id=user_id_str,
        name=user.get("name", ""),
        phone=user.get("phone", ""),
        role=user.get("role", "farmer"),
        preferredLanguage=user.get("preferredLanguage", "en"),
        village=extra.get("village") or extra.get("location") or user.get("village"),
        district=extra.get("district") or user.get("district"),
        state=user.get("state") or extra.get("state") or "Tamil Nadu",
        mandiName=user.get("mandiName"),
        farmerId=user.get("farmerId") or extra.get("farmerId"),
        totalLandAcres=acres_val,
        primaryCrop=extra.get("primaryCrop") or user.get("primaryCrop"),
        soilType=extra.get("soilType") or user.get("soilType"),
        irrigationSource=irr_source_str,
        irrigationSources=irr_sources,
        aadhaarMasked=extra.get("aadhaarMasked") or user.get("aadhaarMasked"),
        isAadhaarVerified=extra.get("isAadhaarVerified", False),
        createdAt=user.get("createdAt", ""),
        telegramLinked=bool(user.get("telegramLinked", False) or user.get("telegramChatId")),
        telegramUsername=user.get("telegramUsername")
    )


@app.get("/api/config/meta")
async def get_configuration_metadata():
    """
    Returns platform metadata: canonical irrigation options, regional languages,
    and Telegram bot integration status.
    """
    return {
        "irrigationOptions": VALID_IRRIGATION_OPTIONS,
        "languages": REGIONAL_LANGUAGES,
        "languageCodes": LANGUAGE_CODE_MAP,
        "telegram": {
            "configured": is_telegram_configured(),
            "botUsername": get_bot_username(),
        }
    }


# ============================================================================
# TELEGRAM AUTHENTICATION & ACCOUNT LINKING ENDPOINTS (PHASE 19)
# ============================================================================

@app.get("/api/auth/telegram/status", response_model=TelegramStatusResponse)
async def get_telegram_status():
    """Reports configuration status of the Telegram Bot authentication engine."""
    configured = is_telegram_configured()
    bot_user = get_bot_username()
    msg = (
        f"Telegram authentication is active via @{bot_user}."
        if configured
        else "Telegram bot is not configured on this server (TELEGRAM_BOT_TOKEN missing in backend environment). Password authentication is enabled."
    )
    return TelegramStatusResponse(
        configured=configured,
        botUsername=bot_user if configured else None,
        message=msg
    )


@app.post("/api/auth/telegram/link-token", response_model=TelegramLinkTokenResponse)
async def create_telegram_link_token(req: TelegramLinkTokenRequest):
    """Generates a cryptographically random, single-use, short-lived deep link token."""
    res = await generate_account_linking_token(req.phone)
    return TelegramLinkTokenResponse(**res)


@app.get("/api/auth/telegram/link-status", response_model=TelegramLinkStatusResponse)
async def get_telegram_link_status(token: str):
    """Checks whether a linking token has been bound to a verified Telegram Chat ID."""
    res = await check_or_poll_telegram_link(token)
    return TelegramLinkStatusResponse(**res)


@app.post("/api/auth/telegram/send-otp", response_model=TelegramSendOtpResponse)
async def request_telegram_otp(req: TelegramSendOtpRequest):
    """
    Dispatches a cryptographically secure 6-digit OTP to the verified Telegram chat.
    Stores only salted hash in MongoDB. Plaintext OTP is NEVER returned or logged.
    """
    res = await send_telegram_otp(req.phone, purpose=req.purpose)
    return TelegramSendOtpResponse(**res)


@app.post("/api/auth/telegram/verify-otp", response_model=TelegramVerifyOtpResponse)
async def verify_otp_endpoint(req: TelegramVerifyOtpRequest):
    """
    Verifies candidate OTP against stored hash.
    For login, authenticates the user directly and returns signed JWT AuthTokenResponse.
    """
    res = await verify_telegram_otp(req.phone, req.otp, purpose=req.purpose)
    auth_resp = None

    if req.purpose == "login":
        users_col = get_users_collection()
        if users_col is not None:
            clean_phone = re.sub(r"[^\d]", "", req.phone)
            if len(clean_phone) == 12 and clean_phone.startswith("91"):
                clean_phone = clean_phone[2:]
            user = await users_col.find_one({"phone": clean_phone})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No account found for mobile number {clean_phone}."
                )
            user_id_str = str(user["_id"])
            token_payload = {
                "sub": user_id_str,
                "phone": user["phone"],
                "role": user["role"],
                "name": user["name"],
                "farmerId": user.get("farmerId"),
                "mandiName": user.get("mandiName")
            }
            access_token = create_access_token(token_payload)
            user_summary = await build_user_summary(user)
            auth_resp = AuthTokenResponse(
                accessToken=access_token,
                tokenType="bearer",
                expiresInMinutes=ACCESS_TOKEN_EXPIRE_MINUTES,
                user=user_summary
            )

    return TelegramVerifyOtpResponse(
        success=True,
        message="OTP verified successfully.",
        phone=res["phone"],
        verifiedToken=res["verifiedToken"],
        authToken=auth_resp
    )


class TelegramMockLinkRequest(BaseModel):
    token: str
    chatId: str = "987654321"
    username: Optional[str] = "test_farmer_bot"
    firstName: Optional[str] = "Murugesan"


@app.post("/api/auth/telegram/mock-link-chat")
async def mock_telegram_link(req: TelegramMockLinkRequest):
    """
    Test helper to bind a simulated Telegram chat to an active link token.
    Enables end-to-end automated testing without making live Telegram API calls.
    """
    res = await bind_verified_telegram_chat(
        token=req.token,
        chat_id=req.chatId,
        username=req.username,
        first_name=req.firstName
    )
    return res


# ============================================================================
# AUTHENTICATION ENDPOINTS (PHASE 3 & PHASE 19)
# ============================================================================

@app.post("/api/auth/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_farmer(req: FarmerRegisterRequest):
    """
    Registers a new Farmer account.
    - Public registration is strictly restricted to the 'farmer' role.
    - Validates 10-digit mobile number, whole-number acre area, and matching passwords.
    - Stores multi-select irrigation sources as an array in MongoDB.
    - Hashes password using bcrypt. Never stores plain text.
    - Generates a unique Farmer ID (TN-AGRI-2026-XXXX).
    - Checks Telegram link status to bind verified chat ID if available.
    - Returns a signed JWT access token and user summary.
    """
    users_collection = get_users_collection()
    farmers_collection = get_farmers_collection()
    tokens_collection = get_telegram_link_tokens_collection()

    if users_collection is None or farmers_collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check if MongoDB is running."
        )

    # Check for duplicate phone
    existing_user = await users_collection.find_one({"phone": req.phone})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with mobile number {req.phone} already exists. Please log in instead."
        )

    # Check if a Telegram chat was verified/linked for this phone
    telegram_chat_id = None
    telegram_username = None
    telegram_linked = False

    if tokens_collection is not None:
        link_record = await tokens_collection.find_one(
            {"phone": req.phone, "status": "LINKED", "telegramChatId": {"$ne": None}},
            sort=[("createdAt", -1)]
        )
        if link_record:
            telegram_chat_id = link_record.get("telegramChatId")
            telegram_username = link_record.get("telegramUsername")
            telegram_linked = True

    # Generate unique Farmer ID
    random_code = random.randint(1000, 9999)
    farmer_id = f"TN-AGRI-2026-{random_code}"
    hashed_pwd = hash_password(req.password)
    created_at = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    # Create User Document (Always 'farmer' role for public registration)
    user_doc = {
        "name": req.name,
        "phone": req.phone,
        "role": "farmer",
        "village": req.village,
        "district": req.district,
        "state": req.state,
        "preferredLanguage": req.preferredLanguage,
        "farmerId": farmer_id,
        "hashed_password": hashed_pwd,
        "createdAt": created_at,
        "isActive": True,
        "totalLandAcres": req.totalLandAcres,
        "primaryCrop": req.primaryCrop,
        "soilType": req.soilType,
        "irrigationSources": req.irrigationSources,
        "irrigationSource": req.irrigationSource,
        "telegramLinked": telegram_linked,
        "telegramChatId": telegram_chat_id,
        "telegramUsername": telegram_username,
    }

    result = await users_collection.insert_one(user_doc)
    user_id_str = str(result.inserted_id)

    # Also sync into farmers collection for agricultural records
    farmer_profile_doc = {
        "userId": user_id_str,
        "farmerId": farmer_id,
        "name": req.name,
        "phone": req.phone,
        "location": f"{req.village}, {req.district}",
        "district": req.district,
        "state": req.state,
        "totalLandAcres": req.totalLandAcres,
        "primaryCrop": req.primaryCrop,
        "soilType": req.soilType,
        "irrigationSources": req.irrigationSources,
        "irrigationSource": req.irrigationSource,
        "preferredLanguage": req.preferredLanguage,
        "aadhaarMasked": None,
        "isAadhaarVerified": False,
        "createdAt": created_at,
        "telegramLinked": telegram_linked,
        "telegramChatId": telegram_chat_id,
        "telegramUsername": telegram_username,
    }
    await farmers_collection.insert_one(farmer_profile_doc)

    # Generate signed JWT token
    token_payload = {
        "sub": user_id_str,
        "phone": req.phone,
        "role": "farmer",
        "name": req.name,
        "farmerId": farmer_id
    }
    access_token = create_access_token(token_payload)
    user_doc["_id"] = result.inserted_id
    user_summary = await build_user_summary(user_doc)

    return AuthTokenResponse(
        accessToken=access_token,
        tokenType="bearer",
        expiresInMinutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_summary
    )


@app.post("/api/auth/login", response_model=AuthTokenResponse)
async def login(req: LoginRequest):
    """
    Authenticates a Farmer or Procurement Staff member.
    - Supports traditional password authentication OR Telegram OTP authentication.
    - Issues a signed JWT access token.
    """
    users_collection = get_users_collection()
    if users_collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable."
        )

    user = await users_collection.find_one({"phone": req.phone, "role": req.role})
    if not user:
        other_user = await users_collection.find_one({"phone": req.phone})
        if other_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"This mobile number is registered as a {other_user.get('role', 'different').capitalize()} account. Please select '{other_user.get('role', 'different').capitalize()}' to sign in."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No {req.role.capitalize()} account found with mobile number {req.phone}."
        )

    # Handle Telegram OTP login vs Password login
    if req.authMethod == "telegram_otp":
        if not req.telegramOtp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram OTP is required for OTP-based sign in."
            )
        await verify_telegram_otp(req.phone, req.telegramOtp, purpose="login")
    else:
        # Verify password hash
        if not req.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required."
            )
        if not verify_password(req.password, user.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Please verify and try again."
            )

    user_id_str = str(user["_id"])

    # Generate JWT
    token_payload = {
        "sub": user_id_str,
        "phone": user["phone"],
        "role": user["role"],
        "name": user["name"],
        "farmerId": user.get("farmerId"),
        "mandiName": user.get("mandiName")
    }
    access_token = create_access_token(token_payload)
    user_summary = await build_user_summary(user)

    return AuthTokenResponse(
        accessToken=access_token,
        tokenType="bearer",
        expiresInMinutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_summary
    )


@app.get("/api/auth/me", response_model=UserSummary)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user's profile based on the JWT bearer token.
    """
    return await build_user_summary(current_user)


# ============================================================================
# FARMER PROFILE ENDPOINTS
# ============================================================================

@app.post("/api/farmers", response_model=FarmerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_farmer_profile(
    profile: FarmerProfileCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    collection = get_farmers_collection()
    users_col = get_users_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = profile.dict()
    if current_user:
        doc["userId"] = current_user["id"]
        doc["farmerId"] = current_user.get("farmerId") or f"TN-AGRI-2026-{random.randint(1000, 9999)}"
        if users_col is not None and ObjectId.is_valid(current_user["id"]):
            await users_col.update_one(
                {"_id": ObjectId(current_user["id"])},
                {"$set": {
                    "district": profile.district,
                    "village": profile.location,
                    "name": profile.name
                }}
            )
        existing = await collection.find_one({
            "$or": [
                {"userId": current_user["id"]},
                {"phone": profile.phone}
            ]
        })
        if existing:
            doc["updatedAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
            doc["_id"] = existing["_id"]
            doc["farmerId"] = existing.get("farmerId", doc["farmerId"])
            await collection.update_one({"_id": existing["_id"]}, {"$set": doc})
            return format_mongo_doc(doc)
    else:
        random_code = random.randint(1000, 9999)
        doc["farmerId"] = f"TN-AGRI-2026-{random_code}"

    doc["createdAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return format_mongo_doc(doc)


@app.put("/api/farmers/me", response_model=UserSummary)
async def update_my_farmer_profile(
    profile: FarmerProfileCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates authenticated farmer's profile, including their registered district.
    Persists to both MongoDB 'farmers' and 'users' collections.
    """
    collection = get_farmers_collection()
    users_collection = get_users_collection()
    if collection is None or users_collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    # 1. Update users collection
    if ObjectId.is_valid(current_user["id"]):
        user_updates = {
            "name": profile.name,
            "district": profile.district,
            "village": profile.location,
            "state": profile.state,
            "totalLandAcres": profile.totalLandAcres,
            "primaryCrop": profile.primaryCrop,
            "soilType": profile.soilType,
            "irrigationSources": profile.irrigationSources,
            "irrigationSource": profile.irrigationSource,
        }
        if profile.preferredLanguage:
            user_updates["preferredLanguage"] = profile.preferredLanguage
        await users_collection.update_one(
            {"_id": ObjectId(current_user["id"])},
            {"$set": user_updates}
        )

    # 2. Update farmers collection
    farmer_doc = profile.dict()
    farmer_doc["userId"] = current_user["id"]
    farmer_doc["farmerId"] = current_user.get("farmerId") or f"TN-AGRI-2026-{random.randint(1000, 9999)}"
    farmer_doc["updatedAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    existing = await collection.find_one({
        "$or": [
            {"userId": current_user["id"]},
            {"phone": current_user["phone"]}
        ]
    })
    if existing:
        farmer_doc["farmerId"] = existing.get("farmerId", farmer_doc["farmerId"])
        await collection.update_one({"_id": existing["_id"]}, {"$set": farmer_doc})
    else:
        farmer_doc["createdAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
        await collection.insert_one(farmer_doc)

    # 3. Return fresh UserSummary
    if ObjectId.is_valid(current_user["id"]):
        fresh_user = await users_collection.find_one({"_id": ObjectId(current_user["id"])})
        if fresh_user:
            return await build_user_summary(fresh_user)
    return await build_user_summary(current_user)


@app.get("/api/farmers", response_model=List[FarmerProfileResponse])
async def list_farmer_profiles(
    limit: int = 50,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    collection = get_farmers_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    if not current_user:
        return []

    query = {}
    if current_user.get("role") == "farmer":
        query = {
            "$or": [
                {"userId": current_user["id"]},
                {"farmerId": current_user.get("farmerId")},
                {"phone": current_user.get("phone")}
            ]
        }

    cursor = collection.find(query).sort("_id", -1).limit(limit)
    farmers = []
    async for doc in cursor:
        farmers.append(format_mongo_doc(doc))
    return farmers


@app.get("/api/farmers/{farmer_id}", response_model=FarmerProfileResponse)
async def get_farmer_profile(farmer_id: str):
    collection = get_farmers_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    query = {"farmerId": farmer_id}
    if ObjectId.is_valid(farmer_id):
        query = {"$or": [{"farmerId": farmer_id}, {"_id": ObjectId(farmer_id)}]}

    doc = await collection.find_one(query)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Farmer '{farmer_id}' not found.")
    return format_mongo_doc(doc)


# ============================================================================
# PHASE 5: SMART PROCUREMENT TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/procurement/centres", response_model=List[ProcurementCentreInfo])
async def list_procurement_centres():
    """
    FEATURE 1: Display procurement centres with name, location, supported crops,
    operating hours, available capacity, and transparent demo data labeling.
    """
    return get_all_centres()


@app.get("/api/procurement/centres/{centre_id}/slots", response_model=CentreSlotsResponse)
async def get_procurement_slots(centre_id: str, date: str):
    """
    FEATURE 1 & 2: Returns live available capacity and status for each time slot
    on the chosen date based on real bookings in MongoDB.
    """
    return await get_centre_slots_availability(centre_id, date)


@app.post("/api/procurement/bookings", status_code=status.HTTP_201_CREATED)
async def create_procurement_booking(
    booking: ProcurementBookingCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    FEATURE 2: Slot booking with race-condition safe capacity checking,
    opaque QR token generation, initial BOOKED state, and MongoDB persistence.
    Works for both authenticated farmers (identity auto-filled from JWT) and
    unauthenticated submissions (identity taken from request body).
    """
    return await create_booking_with_capacity_check(booking.dict(), current_user)


@app.get("/api/procurement/bookings")
async def list_procurement_bookings(
    limit: int = 50,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Lists procurement bookings.
    - Farmer: filters strictly to their own bookings (farmerId or userId match).
    - Staff: lists all mandi bookings for operational monitoring.
    - Unauthenticated: returns empty list (no data leakage).
    """
    collection = get_bookings_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    if not current_user:
        return []  # No token = no data returned

    query = {}
    if current_user.get("role") == "farmer":
        farmer_id = current_user.get("farmerId")
        user_id = current_user.get("id")
        # FEATURE 6: Enforce strict farmer ownership — only their bookings
        query = {"$or": [{"farmerId": farmer_id}, {"userId": user_id}]}

    cursor = collection.find(query).sort("_id", -1).limit(limit)
    bookings = []
    async for doc in cursor:
        bookings.append(format_mongo_doc(doc))
    return bookings


@app.get("/api/procurement/my-bookings")
async def get_my_bookings(
    limit: int = 20,
    current_farmer: dict = Depends(require_farmer)
):
    """
    FEATURE 6: Farmer Booking History — strictly enforced ownership.
    Returns only the authenticated farmer's own bookings with full details
    (QR token, status, weighing bill, payment status).
    Does NOT expose other farmers' personal information.
    """
    collection = get_bookings_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    farmer_id = current_farmer.get("farmerId")
    user_id = current_farmer.get("id")
    query = {"$or": [{"farmerId": farmer_id}, {"userId": user_id}]}

    cursor = collection.find(query).sort("_id", -1).limit(limit)
    bookings = []
    async for doc in cursor:
        safe_doc = format_mongo_doc(doc)
        # Strip other farmers' sensitive fields if any cross-contamination existed
        safe_doc.pop("userId", None)  # Internal DB reference not needed by farmer
        bookings.append(safe_doc)
    return {
        "farmerId": farmer_id,
        "farmerName": current_farmer.get("name", ""),
        "totalBookings": len(bookings),
        "bookings": bookings
    }


@app.post("/api/procurement/bookings/{booking_id}/cancel")
async def farmer_cancel_booking(
    booking_id: str,
    current_farmer: dict = Depends(require_farmer)
):
    """
    FEATURE 4 & PHASE 17: Authenticated farmer cancels their own active procurement booking.
    Releases the reserved slot and updates audit trail.
    """
    return await cancel_booking_for_farmer(booking_id, current_farmer)


@app.get("/api/procurement/queue/{booking_id}", response_model=QueueTrackingResponse)
async def get_booking_queue_tracking(
    booking_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    FEATURE 4 & TASK 1 & 5: Real-time queue status, slot details, queue position,
    and estimated waiting time computed only when sufficient yard data exists.
    Enforces farmer ownership (farmers can only view their own booking queue).
    """
    return await get_queue_tracking_for_booking(booking_id, current_user)


# ============================================================================
# STAFF PORTAL OPERATIONS (ROLE-RESTRICTED: PROCUREMENT STAFF ONLY)
# ============================================================================

@app.post("/api/staff/verify-token", response_model=TokenVerifyResponse)
async def staff_verify_token_endpoint(
    req: TokenVerifyRequest,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 3 & 5: Verifies opaque QR token or manual token number.
    Rejects invalid, cancelled, or already completed bookings.
    """
    return await verify_procurement_token(token=req.token, booking_id=req.bookingId)


@app.post("/api/staff/bookings/{booking_id}/checkin")
async def staff_checkin_endpoint(
    booking_id: str,
    req: StaffCheckInRequest,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 5: Gate check-in operation. Validates token, marks vehicle as CHECKED_IN,
    records audit trail with staff identity, and sends in-app notification.
    """
    return await process_gate_check_in(booking_id, req.notes, staff_user)


@app.post("/api/staff/weighing/calculate", response_model=WeighingCalculationPreviewResponse)
async def preview_weighing_calculation(
    req: WeighingCalculationPreviewRequest
):
    """
    TASK 2: Pre-calculates gross amount, deductions, and net amount
    using consistent decimal arithmetic before saving to MongoDB.
    """
    try:
        calc = calculate_weighing_amounts(
            weight_kg=req.acceptedWeightKg,
            price_per_kg=req.pricePerKg,
            quality_deductions=req.qualityDeductionsAmount,
            other_deductions=req.otherDeductionsAmount
        )
        return WeighingCalculationPreviewResponse(
            acceptedWeightKg=calc["acceptedWeightKg"],
            pricePerKg=calc["pricePerKg"],
            grossAmount=calc["grossAmount"],
            qualityDeductionsAmount=calc["qualityDeductionsAmount"],
            otherDeductionsAmount=calc["otherDeductionsAmount"],
            totalDeductionsAmount=calc["totalDeductionsAmount"],
            netAmount=calc["netAmount"],
            isValid=True,
            validationError=None
        )
    except HTTPException as e:
        return WeighingCalculationPreviewResponse(
            acceptedWeightKg=req.acceptedWeightKg,
            pricePerKg=req.pricePerKg,
            grossAmount=round(req.acceptedWeightKg * req.pricePerKg, 2),
            qualityDeductionsAmount=req.qualityDeductionsAmount,
            otherDeductionsAmount=req.otherDeductionsAmount,
            totalDeductionsAmount=round(req.qualityDeductionsAmount + req.otherDeductionsAmount, 2),
            netAmount=0.0,
            isValid=False,
            validationError=e.detail
        )


@app.post("/api/staff/bookings/{booking_id}/weighing")
async def staff_record_weighing_endpoint(
    booking_id: str,
    req: StaffWeighingCreateRequest,
    staff_user: dict = Depends(require_staff)
):
    """
    TASK 1 & TASK 2 & TASK 3: Staff-only weighing endpoint.
    Records accepted weight, price, deductions, computes gross and net amounts,
    creates a unique Digital Bill, and records audit trail in MongoDB.
    """
    return await record_weighing_and_transaction_ledger(booking_id, req.dict(), staff_user)


@app.post("/api/staff/bookings/{booking_id}/transaction")
async def staff_record_transaction_endpoint(
    booking_id: str,
    req: StaffTransactionRequest,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 5 & 6 / TASK 1 & 3: Backward compatible transaction endpoint.
    Records electronic weighment, computes gross and net payable amounts,
    generates Digital Bill, persists ledger in MongoDB, and logs audit history.
    """
    return await record_weighing_and_transaction_ledger(booking_id, req.dict(), staff_user)


@app.get("/api/procurement/bills/{bill_id}")
async def get_digital_bill_endpoint(
    bill_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    TASK 3 & TASK 5: Retrieve a digital bill by billNumber or bookingId.
    Enforces role isolation: farmers can only view their own bill.
    Staff can view bills for their authorized centre.
    """
    return await get_bill_by_id_or_number(bill_id, current_user)


@app.get("/api/procurement/my-bills")
async def get_farmer_bills_endpoint(
    farmer_user: dict = Depends(require_farmer)
):
    """
    TASK 3 & TASK 6: Returns all digital bills for the logged-in farmer.
    """
    bills = await get_farmer_bills(farmer_user)
    return {"total": len(bills), "bills": bills}


@app.get("/api/staff/bills")
async def get_staff_bills_endpoint(
    date: Optional[str] = None,
    statusFilter: Optional[str] = None,
    staff_user: dict = Depends(require_staff)
):
    """
    TASK 3 & TASK 5: Returns digital bills for the staff member's centre.
    """
    bills = await get_staff_bills(staff_user, date_str=date, status_filter=statusFilter)
    return {"total": len(bills), "bills": bills}


@app.patch("/api/staff/bills/{bill_number}/payment-status")
@app.patch("/api/staff/bookings/{booking_id}/payment-status")
async def staff_update_payment_status_endpoint(
    req: PaymentStatusUpdateRequest,
    bill_number: Optional[str] = None,
    booking_id: Optional[str] = None,
    staff_user: dict = Depends(require_staff)
):
    """
    TASK 4: Update payment status (PENDING -> PROCESSING -> PAID).
    Logs timestamp, authorized staff member, and banking reference.
    """
    target_id = bill_number or booking_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Provide bill number or booking ID.")
    return await update_bill_payment_status(
        identifier=target_id,
        new_status=req.newStatus,
        notes=req.notes,
        tx_ref=req.transactionReference,
        staff_user=staff_user
    )


@app.get("/api/staff/queue")
async def get_staff_queue_overview(
    centreCode: Optional[str] = None,
    mandiName: Optional[str] = None,
    date: Optional[str] = None,
    timeWindow: Optional[str] = None,
    statusFilter: Optional[str] = None,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 4 & TASK 1: Returns operational queue overview.
    - Staff members only see bookings for their assigned mandi/centre.
    - Supports filtering by centre, date, time window, and status.
    - Returns segregated active queue, checked in, processing, and completed lists.
    - Consistent queue ordering rule: check-in time / MongoDB _id.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    staff_mandi = (staff_user.get("mandiName") or staff_user.get("mandiAssigned") or "").strip()
    is_unrestricted = not staff_mandi or staff_mandi.lower() == "all centres"

    # Enforce staff centre restrictions
    selected_centre = centreCode or mandiName or staff_mandi
    if not is_unrestricted and selected_centre:
        if staff_mandi.lower() not in selected_centre.lower() and selected_centre.lower() not in staff_mandi.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You are only authorized for '{staff_mandi}', not '{selected_centre}'."
            )

    query: dict = {}
    if not is_unrestricted:
        query["$or"] = [
            {"mandiName": staff_mandi},
            {"mandiName": {"$regex": staff_mandi[:20], "$options": "i"}}
        ]
    elif selected_centre:
        query["$or"] = [
            {"mandiName": selected_centre},
            {"centreCode": selected_centre},
            {"mandiName": {"$regex": selected_centre[:20], "$options": "i"}}
        ]

    if date:
        query["slotDate"] = date
    if timeWindow and timeWindow != "all":
        query["timeWindow"] = timeWindow
    if statusFilter and statusFilter != "all":
        query["status"] = statusFilter.upper()

    cursor = bookings_col.find(query).sort("_id", 1).limit(300)
    all_bookings = []
    async for b in cursor:
        all_bookings.append(format_mongo_doc(b))

    checked_in = [b for b in all_bookings if b.get("status") == "CHECKED_IN"]
    in_queue = [b for b in all_bookings if b.get("status") == "IN_QUEUE"]
    processing = [b for b in all_bookings if b.get("status") == "PROCESSING"]
    completed = [b for b in all_bookings if b.get("status") == "COMPLETED"]
    booked = [b for b in all_bookings if b.get("status") == "BOOKED"]
    cancelled = [b for b in all_bookings if b.get("status") == "CANCELLED"]

    # Active queue includes only eligible non-cancelled arrived trucks
    # Ordered consistently by check-in time / queue position
    active_queue = [b for b in all_bookings if b.get("status") in ["CHECKED_IN", "IN_QUEUE", "PROCESSING"]]

    total_bags = sum(b.get("quantityBags", 0) for b in all_bookings)
    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M:%S %p UTC")

    return {
        "staffName": staff_user["name"],
        "mandiName": staff_mandi or selected_centre or "All Centres",
        "selectedDate": date or "All Dates",
        "selectedTimeWindow": timeWindow or "All Slots",
        "totalBookings": len(all_bookings),
        "totalBagsRegistered": total_bags,
        "queueStatus": {
            "vehiclesWaiting": len(checked_in) + len(in_queue),
            "vehiclesProcessing": len(processing),
            "weighedCompleted": len(completed),
            "weighbridgeOperational": True
        },
        "checkedIn": checked_in,
        "inQueue": in_queue,
        "processing": processing,
        "completed": completed,
        "booked": booked,
        "cancelled": cancelled,
        "activeQueue": active_queue,
        "bookings": all_bookings,
        "lastUpdated": now_human
    }


@app.post("/api/staff/bookings/{booking_id}/queue")
async def staff_move_to_queue(
    booking_id: str,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 4: Staff operation — moves a CHECKED_IN vehicle to IN_QUEUE status,
    assigning it a yard queue number. Records audit trail with staff identity and timestamp.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "BOOKED").upper()
    if curr_status != "CHECKED_IN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot move to IN_QUEUE from status '{curr_status}'. Booking must be CHECKED_IN."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": "IN_QUEUE",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": "Assigned to yard weighbridge queue by procurement officer"
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "IN_QUEUE",
                "stageNumber": 3,
                "queuedAt": now_human,
                "queuedByStaff": staff_user["name"]
            },
            "$push": {"auditHistory": audit_entry}
        },
        return_document=True
    )

    # Notify farmer
    from notifications import create_in_app_notification
    await create_in_app_notification(
        title="Vehicle Assigned to Weighbridge Queue",
        message=f"Token {doc['tokenNumber']} assigned to yard queue at {doc['mandiName']}.",
        notification_type="queue",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_mongo_doc(updated)


@app.post("/api/staff/bookings/{booking_id}/processing")
async def staff_move_to_processing(
    booking_id: str,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 4: Staff operation — moves an IN_QUEUE vehicle to PROCESSING
    (actively on the weighbridge). Records audit trail.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "").upper()
    if curr_status != "IN_QUEUE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot move to PROCESSING from status '{curr_status}'. Booking must be IN_QUEUE."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": "PROCESSING",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": "Vehicle on weighbridge — moisture and tare weight testing in progress"
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "PROCESSING",
                "stageNumber": 4,
                "processingAt": now_human,
                "processingByStaff": staff_user["name"]
            },
            "$push": {"auditHistory": audit_entry}
        },
        return_document=True
    )
    return format_mongo_doc(updated)


@app.post("/api/staff/bookings/{booking_id}/cancel")
async def staff_cancel_booking(
    booking_id: str,
    staff_user: dict = Depends(require_staff)
):
    """
    FEATURE 4: Staff cancels a booking. Cannot cancel already COMPLETED or CANCELLED bookings.
    Records audit trail with reason and staff identity.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "").upper()
    if curr_status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a COMPLETED booking that has an existing transaction ledger."
        )
    if curr_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already CANCELLED."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": "CANCELLED",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": "Booking cancelled by procurement officer"
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "CANCELLED",
                "cancelledAt": now_human,
                "cancelledByStaff": staff_user["name"]
            },
            "$push": {"auditHistory": audit_entry}
        },
        return_document=True
    )
    return format_mongo_doc(updated)


@app.post("/api/staff/bookings/{booking_id}/status")
async def staff_update_status_endpoint(
    booking_id: str,
    req: StaffQueueStatusUpdateRequest,
    staff_user: dict = Depends(require_staff)
):
    """
    TASK 1 & 3: Unified staff queue transition endpoint.
    Strictly validates permitted business transitions and centre permissions.
    """
    return await update_booking_queue_status(booking_id, req.newStatus, req.notes, staff_user)


@app.patch("/api/staff/bookings/{booking_id}/status")
async def update_booking_status_by_staff(
    booking_id: str,
    update: StaffBookingStatusUpdate,
    staff_user: dict = Depends(require_staff)
):
    """
    Legacy staff status patch endpoint preserved for backward compatibility.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    query = {"bookingId": booking_id}
    if ObjectId.is_valid(booking_id):
        query = {"$or": [{"bookingId": booking_id}, {"_id": ObjectId(booking_id)}]}

    update_fields = {"status": update.status}
    if update.moisturePercent is not None:
        update_fields["moisturePercent"] = update.moisturePercent
    if update.actualNetWeightQuintals is not None:
        update_fields["actualNetWeightQuintals"] = update.actualNetWeightQuintals
    if update.qualityNotes is not None:
        update_fields["qualityNotes"] = update.qualityNotes
    update_fields["updatedByStaff"] = staff_user["name"]
    update_fields["updatedAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    result = await bookings_col.find_one_and_update(
        query,
        {"$set": update_fields},
        return_document=True
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID '{booking_id}' not found."
        )

    return format_mongo_doc(result)



# ============================================================================
# PHASE 4: SMART FARMING INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/api/weather")
async def get_weather_endpoint(district: str = "thanjavur"):
    """
    Returns microclimate weather, 5-day forecast, and agricultural spraying advisory
    for the selected Tamil Nadu district.
    """
    return await get_district_weather(district)


@app.get("/api/weather/districts")
async def get_weather_districts_list():
    """
    Returns list of supported Tamil Nadu agricultural districts with Tamil names and zones.
    """
    districts = [
        {"key": k, "name": v["name"], "nameTa": v["name_ta"], "zone": v["zone"]}
        for k, v in TN_DISTRICT_COORDINATES.items()
    ]
    return districts


@app.post("/api/irrigation/calculate")
async def calculate_irrigation_endpoint(req: IrrigationCalculateRequest):
    """
    Computes rule-based agronomic irrigation advisory without claiming connected physical hardware.
    """
    return calculate_irrigation_advice(
        crop=req.crop,
        growth_stage=req.growthStage,
        soil_type=req.soilType,
        irrigation_method=req.irrigationMethod,
        soil_moisture_percent=req.soilMoisturePercent,
        recent_rain_mm=req.recentRainMm,
        forecast_rain_chance=req.forecastRainChance,
    )


@app.post("/api/crops/recommend")
async def recommend_crops_endpoint(req: CropRecommendRequest):
    """
    Provides district-specific crop rotation and variety recommendations
    explaining suitability, assumptions, and non-guaranteed yield disclaimers.
    """
    return recommend_crops(
        district=req.district,
        soil_type=req.soilType,
        season=req.season,
        water_availability=req.waterAvailability,
        crop_preference=req.cropPreference,
    )


@app.post("/api/disease/analyze")
async def analyze_plant_disease_endpoint(file: UploadFile = File(...)):
    """
    Plant pathology upload endpoint.
    Checks file validity and honestly reports whether a machine vision pathology model
    is installed and configured, avoiding fabricated diagnoses.
    """
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Please upload a JPG, PNG, or WEBP image of the affected plant leaf."
        )

    # Read content to check size (< 5MB)
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit. Please upload a compressed image."
        )

    return analyze_plant_image_submission(
        filename=file.filename or "leaf_sample.jpg",
        file_size_bytes=file_size,
        content_type=file.content_type
    )


@app.get("/api/disease/catalog")
async def get_disease_catalog_endpoint():
    """
    Returns verified TNAU visual symptom keys and management guides for major Tamil Nadu crop diseases.
    """
    return {
        "catalog": TNAU_DISEASE_REFERENCE_CATALOG,
        "source": "Tamil Nadu Agricultural University (TNAU) Agritech Pathology Portal Reference"
    }


@app.get("/api/market/prices")
async def get_market_prices_endpoint(district: Optional[str] = None, search: Optional[str] = None):
    """
    Returns daily regulated mandi market commodity prices with transparent data source labeling.
    """
    return get_market_prices(district=district, search=search)


@app.get("/api/schemes")
async def get_government_schemes_endpoint(category: Optional[str] = None):
    """
    Returns official Central & Tamil Nadu State agricultural welfare schemes
    with eligibility requirements and verified official government application URLs.
    """
    return get_government_schemes(category=category)


# ============================================================================
# PHASE 6: AI FARMER CHAT ASSISTANT ENDPOINTS
# ============================================================================

@app.post("/api/chat/message", response_model=ChatMessageResponse)
async def chat_message_endpoint(
    req: ChatMessageRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    FEATURE 1 & 2: Bilingual AI Farmer Chat Assistant.
    Connects to external LLM if configured; otherwise transparently operates
    in rule-based agronomic advisory mode grounded in real farm, weather, and procurement context.
    """
    res = await process_farmer_chat_message(
        message=req.message,
        language=req.language,
        conversation_id=req.conversationId,
        user=current_user,
        confirmed_action=req.confirmedAction
    )
    return res


@app.get("/api/chat/history")
async def chat_history_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves previous chat turns strictly isolated to the authenticated farmer.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    history = await get_farmer_chat_history(user_id=user_id, farmer_id=farmer_id)
    return {"messages": history}


@app.delete("/api/chat/history")
async def clear_chat_history_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Clears saved chat history for the authenticated farmer.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    deleted = await clear_farmer_chat_history(user_id=user_id, farmer_id=farmer_id)
    return {"deletedCount": deleted, "message": "Chat history cleared successfully."}


@app.get("/api/chat/status")
async def chat_status_endpoint():
    """
    Returns AI Assistant status (whether Gemini is configured and active model),
    strictly without leaking any secret API keys.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    is_configured = bool(gemini_key)
    return {
        "geminiConfigured": is_configured,
        "model": gemini_model if is_configured else "RULE_BASED_LOCAL",
        "supportedLanguages": ["en", "ta"],
        "mode": "GOOGLE_GEMINI" if is_configured else "RULE_BASED_DEMO",
        "developerNotice": (
            f"Google Gemini configured ({gemini_model})."
            if is_configured
            else "Developer Action: Add GEMINI_API_KEY to backend/.env to activate live Google Gemini responses."
        )
    }


# ============================================================================
# PHASE 6: NOTIFICATIONS & SMS GATEWAY ENDPOINTS
# ============================================================================

@app.get("/api/notifications")
async def get_notifications_endpoint(
    unread_only: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    FEATURE 5: Retrieves real persisted notifications for the authenticated farmer.
    Strictly isolated: returns only notifications matching the authenticated user.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    items = await get_user_notifications(
        user_id=user_id,
        farmer_id=farmer_id,
        limit=limit,
        unread_only=unread_only
    )
    return items


@app.patch("/api/notifications/{notification_id}/read")
async def mark_notification_read_endpoint(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    FEATURE 5: Marks a specific notification as read, validating farmer ownership.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    success = await mark_notification_read(
        notification_id=notification_id,
        user_id=user_id,
        farmer_id=farmer_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied."
        )
    return {"success": True, "notificationId": notification_id, "message": "Notification marked as read."}


@app.patch("/api/notifications/read-all")
async def mark_all_notifications_read_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    FEATURE 5: Marks all notifications as read for the authenticated farmer.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    count = await mark_all_notifications_read(user_id=user_id, farmer_id=farmer_id)
    return {"success": True, "markedCount": count, "message": f"{count} notifications marked as read."}


@app.get("/api/notifications/unread-count")
async def get_unread_notifications_count_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    FEATURE 5: Fast unread notification counter for badges.
    """
    user_id = current_user.get("id")
    farmer_id = current_user.get("farmerId")
    count = await get_unread_notifications_count(user_id=user_id, farmer_id=farmer_id)
    return {"unreadCount": count}


@app.get("/api/notifications/sms-status")
async def get_sms_status_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    FEATURE 6: Returns SMS gateway status without leaking credentials.
    """
    return sms_service.get_status()



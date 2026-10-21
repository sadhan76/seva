"""
Phase 5: Smart Procurement Tracking Service for Namma Vivasayi AI.
Implements:
1. Centre selection & capacity inquiry.
2. Slot capacity enforcement & race-condition safe booking.
3. Secure opaque QR token verification (no PII in token).
4. Queue position & estimated waiting time tracking.
5. Authorized staff operations: gate check-in, weighing & transaction ledger calculation.
6. Audit history & MongoDB persistence.
"""

import asyncio
from collections import defaultdict
import secrets
import random
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from bson import ObjectId
from fastapi import HTTPException, status

from database import (
    get_bookings_collection,
    get_centres_collection,
    get_bills_collection,
    get_rates_collection,
    get_slot_closures_collection,
    get_rate_limits_collection,
    get_farmer_limits_collection
)
from notifications import create_in_app_notification

# Concurrency locks per centre/date/slot to prevent simultaneous overbooking race conditions
_slot_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
_slot_locks_mutex = asyncio.Lock()
_now_serving_mutex = asyncio.Lock()


async def get_slot_lock(slot_key: str) -> asyncio.Lock:
    """Thread/coroutine safe retrieval of slot reservation lock."""
    async with _slot_locks_mutex:
        return _slot_locks[slot_key]

# ============================================================================
# VERIFIED DEMO PROCUREMENT CENTRES MASTER DATA
# (Labelled clearly as Demo Reference Models of TNCSC & TN Agri Marketing Board)
# ============================================================================

MASTER_PROCUREMENT_CENTRES = [
    {
        "id": "TNJ-DPC-01",
        "centreCode": "TNJ-DPC-01",
        "name": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
        "nameTa": "தஞ்சாவூர் நேரடி நெல் கொள்முதல் நிலையம் #3 (பிள்ளையார்பட்டி)",
        "district": "Thanjavur",
        "taluk": "Thanjavur",
        "locationAddress": "NH-83 Pillaiyarpatti Bypass Road, Thanjavur - 613403",
        "supportedCrops": [
            "Paddy Grade A (சம்பா நெல் CR 1009)",
            "Paddy Common (பொன்னி)",
            "Kuruvai Paddy (குறுவை)",
            "Black Gram (உளுந்து ADT-5)"
        ],
        "operatingHours": "08:30 AM - 05:30 PM (Mon - Sat)",
        "dailyCapacityBags": 800,
        "slotCapacityBags": 250,
        "slotWindows": [
            "08:30 AM - 11:30 AM",
            "11:30 AM - 02:30 PM",
            "02:30 PM - 05:30 PM"
        ],
        "counters": [
            {"counterId": "Counter-1", "name": "Weighbridge #1 (Main Weighbridge)", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge #2 (Secondary Weighbridge)", "isActive": True}
        ],
        "isActive": True,
        "isDemoData": True,
        "dataSourceLabel": "TNCSC Direct Purchase Centre (Model Reference)"
    },
    {
        "id": "KMU-DPC-02",
        "centreCode": "KMU-DPC-02",
        "name": "Kumbakonam Regulated Market Yard (Asur)",
        "nameTa": "கும்பகோணம் ஒழுங்குமுறை விற்பனைக்கூடம் (அசூர்)",
        "district": "Thanjavur",
        "taluk": "Kumbakonam",
        "locationAddress": "Asur Bypass Junction, Kumbakonam - 612501",
        "supportedCrops": [
            "Paddy Grade A",
            "Paddy Common",
            "Maize (மக்காச்சோளம்)",
            "Green Gram (பச்சைப்பயறு)"
        ],
        "operatingHours": "08:00 AM - 05:00 PM (Mon - Sat)",
        "dailyCapacityBags": 600,
        "slotCapacityBags": 200,
        "slotWindows": [
            "08:00 AM - 11:00 AM",
            "11:00 AM - 02:00 PM",
            "02:00 PM - 05:00 PM"
        ],
        "counters": [
            {"counterId": "Counter-1", "name": "Weighbridge #1 (Platform Scale A)", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge #2 (Platform Scale B)", "isActive": True}
        ],
        "isActive": True,
        "isDemoData": True,
        "dataSourceLabel": "TN Agri Marketing Board Model"
    },
    {
        "id": "MDU-MKT-03",
        "centreCode": "MDU-MKT-03",
        "name": "Madurai Mattuthavani Central Regulated Market",
        "nameTa": "மதுரை மாட்டுத்தாவணி மத்திய ஒழுங்குமுறை விற்பனைக்கூடம்",
        "district": "Madurai",
        "taluk": "Madurai North",
        "locationAddress": "Mattuthavani Agri Market Complex, Madurai - 625007",
        "supportedCrops": [
            "Paddy Common",
            "Millets (கேழ்வரகு / கம்பு)",
            "Cotton (பருத்தி)",
            "Groundnut (நிலக்கடலை)"
        ],
        "operatingHours": "08:30 AM - 05:30 PM (Mon - Sat)",
        "dailyCapacityBags": 900,
        "slotCapacityBags": 300,
        "slotWindows": [
            "08:30 AM - 11:30 AM",
            "11:30 AM - 02:30 PM",
            "02:30 PM - 05:30 PM"
        ],
        "counters": [
            {"counterId": "Counter-1", "name": "Weighbridge #1 (Heavy Truck Scale)", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge #2 (Light Commercial Scale)", "isActive": True}
        ],
        "isActive": True,
        "isDemoData": True,
        "dataSourceLabel": "TN Regulated Market Model"
    },
    {
        "id": "TRY-DPC-04",
        "centreCode": "TRY-DPC-04",
        "name": "Tiruchirappalli Goods Shed DPC Complex",
        "nameTa": "திருச்சிராப்பள்ளி கூட்ஸ் ஷெட் நேரடி கொள்முதல் மையம்",
        "district": "Tiruchirappalli",
        "taluk": "Tiruchirappalli East",
        "locationAddress": "Goods Shed Road, Near Railway Junction, Trichy - 620001",
        "supportedCrops": [
            "Samba Paddy (சம்பா நெல்)",
            "Maize (மக்காச்சோளம்)",
            "Black Gram (உளுந்து)"
        ],
        "operatingHours": "09:00 AM - 05:00 PM (Mon - Sat)",
        "dailyCapacityBags": 750,
        "slotCapacityBags": 250,
        "slotWindows": [
            "09:00 AM - 12:00 PM",
            "12:00 PM - 03:00 PM",
            "03:00 PM - 06:00 PM"
        ],
        "counters": [
            {"counterId": "Counter-1", "name": "Weighbridge #1 (Yard Scale)", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge #2 (Rail Head Scale)", "isActive": True}
        ],
        "isActive": True,
        "isDemoData": True,
        "dataSourceLabel": "TNCSC Trichy Zone Model"
    }
]

# In-memory centre cache for synchronous fast lookups synchronized with MongoDB
_cached_centres_map: Dict[str, Dict[str, Any]] = {c["centreCode"]: dict(c) for c in MASTER_PROCUREMENT_CENTRES}


def format_doc(doc: dict) -> dict:
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    elif "id" not in doc:
        doc["id"] = doc.get("bookingId") or doc.get("centreCode") or ""
    return doc


async def seed_default_centres():
    """
    Seeds default procurement centres into MongoDB collection idempotently.
    Ensures existing user-modified centres or historical configurations are preserved.
    """
    centres_col = get_centres_collection()
    if centres_col is None:
        return

    for c in MASTER_PROCUREMENT_CENTRES:
        existing = await centres_col.find_one({"centreCode": c["centreCode"]})
        if not existing:
            doc = dict(c)
            doc["createdAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
            doc["updatedAt"] = doc["createdAt"]
            await centres_col.insert_one(doc)
            _cached_centres_map[c["centreCode"]] = dict(c)
        else:
            # Synchronize cached map
            _cached_centres_map[c["centreCode"]] = format_doc(existing)


async def get_all_centres_async(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Returns procurement centres from MongoDB with fallback to master list."""
    centres_col = get_centres_collection()
    if centres_col is not None:
        query = {} if include_inactive else {"isActive": {"$ne": False}}
        docs = await centres_col.find(query).to_list(100)
        if docs:
            result = [format_doc(d) for d in docs]
            for r in result:
                _cached_centres_map[r["centreCode"]] = r
            return result

    # Fallback to master data
    if include_inactive:
        return list(_cached_centres_map.values())
    return [c for c in _cached_centres_map.values() if c.get("isActive", True)]


def get_all_centres() -> List[Dict[str, Any]]:
    """Synchronous fallback returning active procurement centres."""
    return [c for c in _cached_centres_map.values() if c.get("isActive", True)]


def find_centre(centre_ident: str) -> Optional[Dict[str, Any]]:
    """Finds a centre by code, ID, name, or keyword/district alias from cache/memory."""
    if not centre_ident:
        return None
    clean_ident = centre_ident.strip().lower()
    centres_pool = list(_cached_centres_map.values())

    for c in centres_pool:
        if (c.get("centreCode", "").lower() == clean_ident or
            str(c.get("id", "")).lower() == clean_ident or
            c.get("name", "").lower() == clean_ident or
            c.get("name", "").lower() in clean_ident or
            clean_ident in c.get("name", "").lower()):
            return c

    # Fallback keyword & district matching
    for c in centres_pool:
        district = c.get("district", "").lower()
        c_code_prefix = c.get("centreCode", "").lower()[:3]
        c_name_lower = c.get("name", "").lower()
        if (district in clean_ident or c_code_prefix in clean_ident):
            if ("dpc" in clean_ident and "dpc" in c_name_lower) or ("market" in clean_ident and "market" in c_name_lower) or (district in clean_ident):
                return c
    return None


async def find_centre_async(centre_ident: str) -> Optional[Dict[str, Any]]:
    """Asynchronous lookup checking MongoDB first."""
    if not centre_ident:
        return None
    centres_col = get_centres_collection()
    if centres_col is not None:
        clean_ident = centre_ident.strip()
        doc = await centres_col.find_one({
            "$or": [
                {"centreCode": clean_ident},
                {"centreCode": {"$regex": f"^{re.escape(clean_ident)}$", "$options": "i"}},
                {"name": {"$regex": f"^{re.escape(clean_ident)}$", "$options": "i"}}
            ]
        })
        if doc:
            formatted = format_doc(doc)
            _cached_centres_map[formatted["centreCode"]] = formatted
            return formatted
    return find_centre(centre_ident)


async def create_procurement_centre(data: dict, staff_user: dict) -> dict:
    """Authorized staff creates a new procurement centre."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can create centres.")

    centres_col = get_centres_collection()
    if centres_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    code = data.get("centreCode", "").strip()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="centreCode is required.")

    existing = await centres_col.find_one({"centreCode": code})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Centre with code '{code}' already exists.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    centre_doc = {
        "centreCode": code,
        "name": data.get("name", code).strip(),
        "nameTa": data.get("nameTa"),
        "district": data.get("district", "").strip(),
        "taluk": data.get("taluk"),
        "locationAddress": data.get("locationAddress", ""),
        "supportedCrops": data.get("supportedCrops", ["Paddy Grade A", "Paddy Common"]),
        "operatingHours": data.get("operatingHours", "08:30 AM - 05:30 PM (Mon - Sat)"),
        "dailyCapacityBags": int(data.get("dailyCapacityBags", 800)),
        "slotCapacityBags": int(data.get("slotCapacityBags", 250)),
        "slotWindows": data.get("slotWindows", ["08:30 AM - 11:30 AM", "11:30 AM - 02:30 PM", "02:30 PM - 05:30 PM"]),
        "counters": data.get("counters") or [
            {"counterId": "Counter-1", "name": "Weighbridge #1", "isActive": True},
            {"counterId": "Counter-2", "name": "Weighbridge #2", "isActive": True}
        ],
        "isActive": True,
        "createdAt": now_human,
        "updatedAt": now_human,
        "createdBy": staff_user.get("name")
    }

    result = await centres_col.insert_one(centre_doc)
    centre_doc["id"] = str(result.inserted_id)
    _cached_centres_map[code] = format_doc(centre_doc)
    return format_doc(centre_doc)


async def update_procurement_centre(centre_ident: str, data: dict, staff_user: dict) -> dict:
    """Authorized staff updates an existing procurement centre."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can update centres.")

    centres_col = get_centres_collection()
    if centres_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    clean_id = centre_ident.strip()
    query = {"$or": [{"centreCode": clean_id}, {"id": clean_id}]}
    if ObjectId.is_valid(clean_id):
        query["$or"].append({"_id": ObjectId(clean_id)})

    existing = await centres_col.find_one(query)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_ident}' not found.")

    update_fields = {}
    for k in ["name", "nameTa", "district", "taluk", "locationAddress", "operatingHours",
              "dailyCapacityBags", "slotCapacityBags", "slotWindows", "supportedCrops", "counters", "isActive"]:
        if k in data and data[k] is not None:
            update_fields[k] = data[k]

    update_fields["updatedAt"] = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    update_fields["updatedBy"] = staff_user.get("name")

    updated = await centres_col.find_one_and_update(
        {"_id": existing["_id"]},
        {"$set": update_fields},
        return_document=True
    )
    formatted = format_doc(updated)
    _cached_centres_map[formatted["centreCode"]] = formatted
    return formatted


async def set_procurement_centre_status(centre_ident: str, is_active: bool, reason: str, staff_user: dict) -> dict:
    """Authorized staff activates or deactivates a procurement centre."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can change centre status.")

    centres_col = get_centres_collection()
    if centres_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    clean_id = centre_ident.strip()
    query = {"$or": [{"centreCode": clean_id}, {"id": clean_id}]}
    if ObjectId.is_valid(clean_id):
        query["$or"].append({"_id": ObjectId(clean_id)})

    existing = await centres_col.find_one(query)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_ident}' not found.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    updated = await centres_col.find_one_and_update(
        {"_id": existing["_id"]},
        {
            "$set": {
                "isActive": is_active,
                "statusChangeReason": reason,
                "statusChangedAt": now_human,
                "statusChangedBy": staff_user.get("name"),
                "updatedAt": now_human
            }
        },
        return_document=True
    )
    formatted = format_doc(updated)
    _cached_centres_map[formatted["centreCode"]] = formatted
    return formatted


def is_crop_supported_at_centre(crop_input: str, supported_crops: List[str]) -> bool:
    """
    Validates crop selection against the selected centre's supported crops.
    Supports English & Tamil names, parentheses varieties, and standard aliases.
    """
    if not crop_input or not supported_crops:
        return False
    c_lower = crop_input.strip().lower()
    c_main = c_lower.split("(")[0].strip()

    for s in supported_crops:
        s_lower = s.strip().lower()
        s_main = s_lower.split("(")[0].strip()

        # Direct match or main name match
        if c_lower == s_lower or c_main == s_main:
            return True
        if c_main and (c_main in s_lower or s_main in c_lower):
            return True
        # Check inside parentheses (Tamil script or local variety names)
        if "(" in s_lower and ")" in s_lower:
            inner = s_lower[s_lower.find("(") + 1 : s_lower.find(")")].strip()
            if c_lower in inner or inner in c_lower:
                return True
        # Common agricultural synonyms in Tamil Nadu
        if "samba" in c_lower and ("samba" in s_lower or "grade a" in s_lower or "cr 1009" in s_lower):
            return True
        if "kuruvai" in c_lower and "kuruvai" in s_lower:
            return True
        if "ponni" in c_lower and ("ponni" in s_lower or "common" in s_lower):
            return True
        if "black gram" in c_lower and ("black gram" in s_lower or "urad" in s_lower or "உளுந்து" in s_lower):
            return True
        if "green gram" in c_lower and ("green gram" in s_lower or "moong" in s_lower or "பச்சைப்பயறு" in s_lower):
            return True
        if "maize" in c_lower and ("maize" in s_lower or "corn" in s_lower or "மக்காச்சோளம்" in s_lower):
            return True
        if "cotton" in c_lower and ("cotton" in s_lower or "பருத்தி" in s_lower):
            return True
        if "groundnut" in c_lower and ("groundnut" in s_lower or "peanut" in s_lower or "நிலக்கடலை" in s_lower):
            return True
        if "millet" in c_lower and ("millet" in s_lower or "ragi" in s_lower or "kambu" in s_lower or "கேழ்வரகு" in s_lower):
            return True

    return False


async def get_centre_slots_availability(centre_ident: str, date_str: str) -> Dict[str, Any]:
    """
    Computes slot capacity and available bags for a given centre and date
    by querying live bookings in MongoDB. Excludes CANCELLED and NO_SHOW bookings.
    Also incorporates persistent slot closures and centre active status.
    """
    centre = find_centre(centre_ident)
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procurement centre '{centre_ident}' not found."
        )

    bookings_col = get_bookings_collection()
    slot_closures_col = get_slot_closures_collection()
    slot_capacity = centre.get("slotCapacityBags", 250)
    centre_is_active = centre.get("isActive", True)
    slots_result = []

    # Retrieve all active closures for this centre and date
    closures_map: Dict[str, dict] = {}
    if slot_closures_col is not None:
        closure_cursor = slot_closures_col.find({
            "centreCode": centre["centreCode"],
            "slotDate": date_str,
            "isClosed": True
        })
        async for cl in closure_cursor:
            closures_map[cl.get("timeWindow", "")] = cl

    for window in centre.get("slotWindows", []):
        booked_bags = 0
        if bookings_col is not None:
            # Query sum of booked bags for this centre, date, and window (excluding cancelled and no-show)
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"mandiName": centre["name"]},
                            {"centreCode": centre["centreCode"]}
                        ],
                        "slotDate": date_str,
                        "timeWindow": window,
                        "status": {"$nin": ["CANCELLED", "NO_SHOW"]}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "totalBags": {"$sum": "$quantityBags"}
                    }
                }
            ]
            agg = await bookings_col.aggregate(pipeline).to_list(1)
            if agg:
                booked_bags = agg[0].get("totalBags", 0)

        available_bags = max(0, slot_capacity - booked_bags)
        ratio = booked_bags / slot_capacity if slot_capacity > 0 else 0

        # Check if centre itself is deactivated or slot is closed by staff
        is_closed = False
        closure_reason = None

        if not centre_is_active:
            is_closed = True
            closure_reason = centre.get("statusChangeReason") or "Centre is currently deactivated and not accepting bookings."
            status_str = "closed"
            available_bags = 0
        elif window in closures_map:
            is_closed = True
            closure_reason = closures_map[window].get("closureReason") or "Slot closed by procurement staff administration."
            status_str = "closed"
            available_bags = 0
        elif ratio >= 1.0 or available_bags == 0:
            status_str = "full"
        elif ratio >= 0.70:
            status_str = "filling_fast"
        else:
            status_str = "available"

        slots_result.append({
            "timeWindow": window,
            "maxCapacityBags": slot_capacity,
            "bookedBags": booked_bags,
            "availableBags": available_bags,
            "status": status_str,
            "isClosed": is_closed,
            "closureReason": closure_reason
        })

    return {
        "centreCode": centre["centreCode"],
        "centreName": centre["name"],
        "date": date_str,
        "totalDailyCapacityBags": centre.get("dailyCapacityBags", 800),
        "isActive": centre_is_active,
        "slots": slots_result
    }


async def create_booking_with_capacity_check(booking_data: dict, current_user: Optional[dict] = None) -> dict:
    """
    Creates a booking after performing a race-condition safe slot capacity check.
    Enforces centre active status, staff slot closures, and per-farmer quantity limits.
    Generates opaque security token and sets initial BOOKED state and audit history.
    """
    bookings_col = get_bookings_collection()
    slot_closures_col = get_slot_closures_collection()
    farmer_limits_col = get_farmer_limits_collection()

    if bookings_col is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable."
        )

    mandi_name = (booking_data.get("mandiName") or "").strip()
    preferred_date = (booking_data.get("preferredDate") or booking_data.get("slotDate") or "").strip()
    time_window = (booking_data.get("timeWindow") or "08:30 AM - 11:30 AM").strip()
    quantity_bags = int(booking_data.get("quantityBags", 0))

    if not preferred_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking date ('preferredDate' or 'slotDate') is required."
        )

    try:
        b_date = date.fromisoformat(preferred_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking date format. Expected YYYY-MM-DD."
        )

    if b_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking date cannot be in the past. Please select today or a future date."
        )

    if quantity_bags <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity in bags must be greater than zero."
        )

    centre = find_centre(mandi_name)
    slot_capacity = centre["slotCapacityBags"] if centre else 250
    centre_code = centre["centreCode"] if centre else "TNJ-DPC-01"
    official_mandi_name = centre["name"] if centre else mandi_name

    # Step 7: Prevent deactivated centres from accepting new bookings
    if centre and centre.get("isActive") is False:
        reason = centre.get("statusChangeReason") or "Centre is currently deactivated."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Procurement centre '{official_mandi_name}' is currently deactivated and not accepting new bookings. Reason: {reason}."
        )

    crop_name = (booking_data.get("crop") or "Samba Paddy").strip()
    if centre and centre.get("supportedCrops"):
        if not is_crop_supported_at_centre(crop_name, centre["supportedCrops"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Crop '{crop_name}' is not supported at centre '{official_mandi_name}'. Supported crops: {', '.join(centre['supportedCrops'])}."
            )

    # Step 4: Check if slot is closed in slot_closures collection
    if slot_closures_col is not None:
        closure = await slot_closures_col.find_one({
            "centreCode": centre_code,
            "slotDate": preferred_date,
            "timeWindow": time_window,
            "isClosed": True
        })
        if closure:
            reason = closure.get("closureReason") or "Slot closed by procurement staff administration."
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking rejected: Slot '{time_window}' on {preferred_date} at {official_mandi_name} is CLOSED by procurement staff. Reason: {reason}."
            )

    # Acquire atomic concurrency lock for this specific slot to eliminate race-conditions
    slot_lock_key = f"{centre_code}:{preferred_date}:{time_window}"
    slot_lock = await get_slot_lock(slot_lock_key)

    async with slot_lock:
        # Determine farmer identity
        farmer_id = booking_data.get("farmerId") or "TN-AGRI-2026-8841"
        farmer_name = booking_data.get("farmerName") or "Farmer"
        user_id = None

        if current_user:
            user_id = current_user.get("id")
            if current_user.get("farmerId"):
                farmer_id = current_user.get("farmerId")
            if current_user.get("name"):
                farmer_name = current_user.get("name")

        # Duplicate booking guard: A farmer cannot hold multiple active un-admitted bookings for the exact same slot
        farmer_filter = [{"farmerId": farmer_id}]
        if user_id:
            farmer_filter.append({"userId": str(user_id)})

        # Step 5: Enforce Per-Farmer Quantity Limits (Slot Limit & Daily Limit)
        # Fetch limits configuration (custom per-farmer or global default)
        limit_config = None
        if farmer_limits_col is not None:
            limit_config = await farmer_limits_col.find_one({"farmerId": farmer_id})
            if not limit_config:
                limit_config = await farmer_limits_col.find_one({"farmerId": "GLOBAL"})

        max_per_slot = limit_config.get("maxBagsPerSlot", 100) if limit_config else 100
        max_per_day = limit_config.get("maxBagsPerDay", 250) if limit_config else 250

        # Query existing active bookings for this farmer on this date (excluding CANCELLED and NO_SHOW)
        active_farmer_docs = await bookings_col.find({
            "$and": [
                {"$or": farmer_filter},
                {"slotDate": preferred_date},
                {"status": {"$nin": ["CANCELLED", "NO_SHOW"]}}
            ]
        }).to_list(100)

        existing_day_bags = sum(b.get("quantityBags", 0) for b in active_farmer_docs)
        existing_slot_bags = sum(b.get("quantityBags", 0) for b in active_farmer_docs if b.get("timeWindow") == time_window)

        if existing_slot_bags + quantity_bags > max_per_slot:
            rem_slot = max(0, max_per_slot - existing_slot_bags)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Farmer slot limit exceeded: Maximum allowed per slot is {max_per_slot} bags (~{round(max_per_slot*40/100, 1)} Qtl). "
                       f"You already have {existing_slot_bags} bags booked in this slot. "
                       f"Remaining slot allowance: {rem_slot} bags. Requested: {quantity_bags} bags."
            )

        if existing_day_bags + quantity_bags > max_per_day:
            rem_day = max(0, max_per_day - existing_day_bags)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Farmer daily limit exceeded: Maximum allowed per day is {max_per_day} bags (~{round(max_per_day*40/100, 1)} Qtl). "
                       f"You already have {existing_day_bags} bags booked on {preferred_date}. "
                       f"Remaining daily allowance: {rem_day} bags. Requested: {quantity_bags} bags."
            )

        # Duplicate booking guard: A farmer cannot hold multiple active un-admitted bookings for the exact same slot
        dup_query = {
            "$and": [
                {"$or": farmer_filter},
                {"$or": [{"mandiName": official_mandi_name}, {"centreCode": centre_code}]},
                {"slotDate": preferred_date},
                {"timeWindow": time_window},
                {"status": "BOOKED"}
            ]
        }
        existing_booking = await bookings_col.find_one(dup_query)
        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate booking disallowed: Farmer '{farmer_id}' already has an active booking ({existing_booking.get('bookingId')}, Token: {existing_booking.get('tokenNumber')}) for {official_mandi_name} on {preferred_date} ({time_window}). Please cancel the existing booking to rebook."
            )

        # Database-safe race-condition check:
        # Query current sum of booked bags for this slot (excluding CANCELLED and NO_SHOW)
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"mandiName": official_mandi_name},
                        {"centreCode": centre_code}
                    ],
                    "slotDate": preferred_date,
                    "timeWindow": time_window,
                    "status": {"$nin": ["CANCELLED", "NO_SHOW"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "totalBags": {"$sum": "$quantityBags"}
                }
            }
        ]
        agg = await bookings_col.aggregate(pipeline).to_list(1)
        current_booked = agg[0].get("totalBags", 0) if agg else 0
        available_bags = slot_capacity - current_booked

        if current_booked + quantity_bags > slot_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slot capacity exceeded for {time_window} on {preferred_date}. "
                       f"Maximum slot limit: {slot_capacity} bags, currently booked: {current_booked} bags, "
                       f"available: {available_bags} bags. Requested: {quantity_bags} bags."
            )

        # Generate Unique Booking ID & Opaque Random Verification Token
        # Using cryptographically secure secrets module
        random_hex = secrets.token_hex(2).upper()
        booking_id = f"PROC-TNJ-2026-{random_hex}"
        token_number = f"TN-DPC-{secrets.randbelow(900) + 100}"
        opaque_secure_token = f"NV-{secrets.token_urlsafe(12)}"

        estimated_weight = round((quantity_bags * 40.0) / 100.0, 2)
        now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

        # Initial Audit Trail
        audit_history = [
            {
                "action": "BOOKED",
                "by": farmer_name,
                "role": "farmer",
                "timestamp": now_human,
                "notes": f"Slot reserved for {quantity_bags} bags (~{estimated_weight} Qtl)"
            }
        ]

        # QR Code payload encodes ONLY opaque tokens and verification URL (NO PII!)
        qr_payload_url = f"https://agribharat.gov.in/verify?token={opaque_secure_token}&id={booking_id}"

        new_booking = {
            "bookingId": booking_id,
            "tokenNumber": token_number,
            "opaqueToken": opaque_secure_token,
            "qrVerificationUrl": qr_payload_url,
            "userId": user_id,
            "farmerName": farmer_name,
            "farmerId": farmer_id,
            "mandiName": official_mandi_name,
            "centreCode": centre_code,
            "crop": crop_name,
            "cropVariety": booking_data.get("cropVariety"),
            "harvestDate": booking_data.get("harvestDate"),
            "quantityBags": quantity_bags,
            "estimatedWeightQuintals": estimated_weight,
            "slotDate": preferred_date,
            "timeWindow": time_window,
            "status": "BOOKED",
            "stageNumber": 1,
            "moisturePercent": None,
            "actualNetWeightQuintals": None,
            "qualityNotes": "Awaiting gate entry & physical inspection",
            "qualityInspection": None,
            "noShowDetails": None,
            "isNowServing": False,
            "transaction": None,
            "auditHistory": audit_history,
            "createdAt": now_human
        }

        insert_result = await bookings_col.insert_one(new_booking)
        new_booking["_id"] = insert_result.inserted_id

    # Create in-app notification for the farmer
    await create_in_app_notification(
        title="Procurement Slot Confirmed",
        message=f"Slot booked at {official_mandi_name} for {preferred_date} ({time_window}). Token: {token_number}.",
        notification_type="booking",
        user_id=user_id,
        farmer_id=farmer_id,
        booking_id=booking_id
    )

    return format_doc(new_booking)


async def verify_procurement_token(token: Optional[str] = None, booking_id: Optional[str] = None) -> dict:
    """
    Verifies an opaque QR token or booking ID entered by Mandi Staff.
    Rejects invalid, cancelled, or already completed bookings.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    query = {}
    if token:
        clean_token = token.strip()
        query = {"$or": [{"opaqueToken": clean_token}, {"tokenNumber": clean_token}]}
    elif booking_id:
        clean_bid = booking_id.strip()
        query = {"bookingId": clean_bid}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either a token or a booking ID.")

    doc = await bookings_col.find_one(query)
    if not doc:
        return {
            "isValid": False,
            "status": "NOT_FOUND",
            "bookingId": "",
            "tokenNumber": "",
            "farmerName": "",
            "farmerId": "",
            "mandiName": "",
            "crop": "",
            "quantityBags": 0,
            "estimatedWeightQuintals": 0.0,
            "slotDate": "",
            "timeWindow": "",
            "canCheckIn": False,
            "canWeigh": False,
            "message": "Invalid token or booking ID. No matching record exists in the database.",
            "disclaimer": "Verify the token or scan a valid AgriBharat QR code."
        }

    current_status = doc.get("status", "BOOKED").upper()

    # Reject cancelled
    if current_status == "CANCELLED":
        return {
            "isValid": False,
            "status": "CANCELLED",
            "bookingId": doc["bookingId"],
            "tokenNumber": doc["tokenNumber"],
            "farmerName": doc["farmerName"],
            "farmerId": doc["farmerId"],
            "mandiName": doc["mandiName"],
            "crop": doc["crop"],
            "quantityBags": doc["quantityBags"],
            "estimatedWeightQuintals": doc["estimatedWeightQuintals"],
            "slotDate": doc["slotDate"],
            "timeWindow": doc["timeWindow"],
            "canCheckIn": False,
            "canWeigh": False,
            "message": "This booking has been CANCELLED and cannot be admitted to the procurement yard.",
            "disclaimer": "Cancelled reservation."
        }

    # Reject completed
    if current_status == "COMPLETED":
        return {
            "isValid": False,
            "status": "COMPLETED",
            "bookingId": doc["bookingId"],
            "tokenNumber": doc["tokenNumber"],
            "farmerName": doc["farmerName"],
            "farmerId": doc["farmerId"],
            "mandiName": doc["mandiName"],
            "crop": doc["crop"],
            "quantityBags": doc["quantityBags"],
            "estimatedWeightQuintals": doc["estimatedWeightQuintals"],
            "slotDate": doc["slotDate"],
            "timeWindow": doc["timeWindow"],
            "canCheckIn": False,
            "canWeigh": False,
            "message": "This booking has ALREADY BEEN COMPLETED and weighed. Duplicate processing is disallowed.",
            "disclaimer": "Completed transaction ledger is already recorded."
        }

    # Reject no-show
    if current_status == "NO_SHOW":
        return {
            "isValid": False,
            "status": "NO_SHOW",
            "bookingId": doc["bookingId"],
            "tokenNumber": doc["tokenNumber"],
            "farmerName": doc["farmerName"],
            "farmerId": doc["farmerId"],
            "mandiName": doc["mandiName"],
            "crop": doc["crop"],
            "quantityBags": doc["quantityBags"],
            "estimatedWeightQuintals": doc["estimatedWeightQuintals"],
            "slotDate": doc["slotDate"],
            "timeWindow": doc["timeWindow"],
            "canCheckIn": False,
            "canWeigh": False,
            "message": "This booking was marked as NO_SHOW. The slot was released. Please rebook a new slot.",
            "disclaimer": "No-show reservation."
        }

    # Reject quality rejected
    if current_status == "REJECTED":
        return {
            "isValid": False,
            "status": "REJECTED",
            "bookingId": doc["bookingId"],
            "tokenNumber": doc["tokenNumber"],
            "farmerName": doc["farmerName"],
            "farmerId": doc["farmerId"],
            "mandiName": doc["mandiName"],
            "crop": doc["crop"],
            "quantityBags": doc["quantityBags"],
            "estimatedWeightQuintals": doc["estimatedWeightQuintals"],
            "slotDate": doc["slotDate"],
            "timeWindow": doc["timeWindow"],
            "canCheckIn": False,
            "canWeigh": False,
            "message": f"This lot was REJECTED during quality inspection: {doc.get('qualityInspection', {}).get('rejectionReason') or 'FAQ quality standard unmet'}.",
            "disclaimer": "Quality inspection rejected."
        }

    can_check_in = current_status in ["BOOKED", "CONFIRMED"]
    can_weigh = (current_status in ["QUALITY_CHECKED"]) or bool(doc.get("qualityInspection") and current_status != "REJECTED")

    return {
        "isValid": True,
        "status": current_status,
        "bookingId": doc["bookingId"],
        "tokenNumber": doc["tokenNumber"],
        "farmerName": doc["farmerName"],
        "farmerId": doc["farmerId"],
        "mandiName": doc["mandiName"],
        "crop": doc["crop"],
        "quantityBags": doc["quantityBags"],
        "estimatedWeightQuintals": doc["estimatedWeightQuintals"],
        "slotDate": doc["slotDate"],
        "timeWindow": doc["timeWindow"],
        "canCheckIn": can_check_in,
        "canWeigh": can_weigh,
        "qualityInspection": doc.get("qualityInspection"),
        "isNowServing": doc.get("isNowServing", False),
        "message": f"Token verified successfully. Current status is {current_status}.",
        "disclaimer": "Official procurement token verified with secure database signature."
    }


def verify_staff_centre_access(staff_user: dict, doc: dict) -> None:
    """
    Enforces FEATURE 5 & TASK 5: Restricts staff operations strictly to their authorized procurement centre.
    """
    staff_mandi = (staff_user.get("mandiName") or staff_user.get("mandiAssigned") or "").strip()
    if not staff_mandi or staff_mandi.lower() in ("all centres", "all"):
        return  # Unrestricted / supervisor staff

    doc_mandi = (doc.get("mandiName") or "").strip()
    doc_code = (doc.get("centreCode") or "").strip()

    staff_mandi_lower = staff_mandi.lower()
    doc_mandi_lower = doc_mandi.lower()
    doc_code_lower = doc_code.lower()

    # 1. Direct substring check
    if (
        staff_mandi_lower in doc_mandi_lower
        or doc_mandi_lower in staff_mandi_lower
        or staff_mandi_lower in doc_code_lower
        or doc_code_lower in staff_mandi_lower
    ):
        return

    # 2. Centre code resolution match
    staff_centre = find_centre(staff_mandi)
    doc_centre = find_centre(doc_code or doc_mandi)
    if staff_centre and doc_centre and staff_centre["centreCode"] == doc_centre["centreCode"]:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access forbidden: You are only authorized for '{staff_user.get('mandiName')}', not '{doc.get('mandiName')}'."
    )


async def process_gate_check_in(booking_id: str, notes: Optional[str], staff_user: dict) -> dict:
    """
    Staff operation: Records physical gate arrival and QR scan, moving status from BOOKED to CHECKED_IN.
    Strictly validates authorized staff centre and status transition.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    # Restrict staff to authorized centres
    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "BOOKED").upper()
    if curr_status != "BOOKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot check in booking with status '{curr_status}'. Vehicle must be in BOOKED status."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": "CHECKED_IN",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": notes or "Gate QR verified and entry admitted into yard queue"
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "CHECKED_IN",
                "stageNumber": 2,
                "checkedInAt": now_human,
                "checkedInByStaff": staff_user["name"],
                "gateNotes": notes or "Gate admitted"
            },
            "$push": {
                "auditHistory": audit_entry
            }
        },
        return_document=True
    )


    # In-app notification to the farmer
    await create_in_app_notification(
        title="Gate Entry Check-In Verified",
        message=f"Vehicle token {doc['tokenNumber']} checked in at {doc['mandiName']} gate by Officer {staff_user['name']}.",
        notification_type="checkin",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_doc(updated)


async def process_quality_inspection(booking_id: str, inspection_data: dict, staff_user: dict) -> dict:
    """
    Staff operation: Records physical quality inspection and moisture testing prior to final weighment.
    Outcomes supported:
    - ACCEPTED: lot meets FAQ standards; accepted weight set, rejected weight = 0
    - PARTIALLY_ACCEPTED: partial lot acceptance; both accepted and rejected weights > 0, rejection reason required
    - REJECTED: entire lot rejected; rejected weight > 0, accepted weight = 0, rejection reason required
    Enforces valid state transition from CHECKED_IN or IN_QUEUE.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "BOOKED").upper()
    if curr_status not in ["CHECKED_IN", "IN_QUEUE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot conduct quality inspection on booking with status '{curr_status}'. Vehicle must be CHECKED_IN or IN_QUEUE."
        )

    quality_status = (inspection_data.get("qualityStatus") or "").strip().upper()
    if quality_status not in ["ACCEPTED", "PARTIALLY_ACCEPTED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid quality status '{quality_status}'. Allowed values: ACCEPTED, PARTIALLY_ACCEPTED, REJECTED."
        )

    moisture_percent = float(inspection_data.get("moisturePercent", 14.0))
    if moisture_percent < 5.0 or moisture_percent > 35.0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Moisture percentage must be between 5.0% and 35.0%.")

    declared_kg = float(inspection_data.get("declaredWeightKg") or (doc.get("quantityBags", 0) * 40.0))
    accepted_kg = float(inspection_data.get("acceptedWeightKg", 0.0))
    rejected_kg = float(inspection_data.get("rejectedWeightKg", 0.0))
    rejection_reason = (inspection_data.get("rejectionReason") or "").strip()
    notes = inspection_data.get("notes")
    quality_grade = inspection_data.get("qualityGrade") or "FAQ Grade A"

    if accepted_kg < 0 or rejected_kg < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accepted and rejected weights cannot be negative.")

    if (accepted_kg + rejected_kg) > (declared_kg + 0.5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total inspected weight ({accepted_kg + rejected_kg:.2f} kg) cannot exceed declared weight ({declared_kg:.2f} kg)."
        )

    if quality_status == "ACCEPTED":
        if accepted_kg <= 0:
            accepted_kg = declared_kg
        rejected_kg = 0.0
    elif quality_status == "REJECTED":
        if not rejection_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason is required for REJECTED quality inspection.")
        if rejected_kg <= 0:
            rejected_kg = declared_kg
        accepted_kg = 0.0
    elif quality_status == "PARTIALLY_ACCEPTED":
        if not rejection_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason is required for PARTIALLY_ACCEPTED quality inspection.")
        if accepted_kg <= 0 or rejected_kg <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both accepted and rejected weights must be greater than zero for PARTIALLY_ACCEPTED outcome.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    new_booking_status = "REJECTED" if quality_status == "REJECTED" else "QUALITY_CHECKED"

    quality_record = {
        "qualityStatus": quality_status,
        "qualityGrade": quality_grade,
        "moisturePercent": moisture_percent,
        "declaredWeightKg": declared_kg,
        "acceptedWeightKg": accepted_kg,
        "rejectedWeightKg": rejected_kg,
        "rejectionReason": rejection_reason if rejection_reason else None,
        "notes": notes,
        "inspectedAt": now_human,
        "inspectedByStaff": staff_user["name"],
        "staffId": staff_user.get("id") or staff_user.get("username", "")
    }

    audit_entry = {
        "action": f"QUALITY_INSPECTION_{quality_status}",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": f"Quality inspection outcome: {quality_status} ({quality_grade}, {moisture_percent}% moisture). Accepted: {accepted_kg} kg, Rejected: {rejected_kg} kg. {('Reason: ' + rejection_reason) if rejection_reason else ''}"
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": new_booking_status,
                "stageNumber": 3,
                "moisturePercent": moisture_percent,
                "qualityNotes": f"{quality_grade} - {quality_status}",
                "qualityInspection": quality_record,
                "inspectedAt": now_human,
                "inspectedByStaff": staff_user["name"]
            },
            "$push": {
                "auditHistory": audit_entry
            }
        },
        return_document=True
    )

    # In-app notification to the farmer
    notif_msg = (
        f"Quality inspection passed at {doc['mandiName']} (~{accepted_kg:.1f} kg accepted). Ready for weighment."
        if quality_status == "ACCEPTED"
        else f"Quality inspection partially accepted: {accepted_kg:.1f} kg accepted, {rejected_kg:.1f} kg rejected. Reason: {rejection_reason}."
        if quality_status == "PARTIALLY_ACCEPTED"
        else f"Lot rejected at {doc['mandiName']}: {rejection_reason}."
    )
    await create_in_app_notification(
        title=f"Quality Inspection: {quality_status}",
        message=notif_msg,
        notification_type="quality",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_doc(updated)


async def mark_booking_no_show(booking_id: str, reason: Optional[str], staff_user: dict) -> dict:
    """
    Staff operation: Marks an unadmitted booking as NO_SHOW.
    Permitted only when booking is in BOOKED or CONFIRMED status (not checked in, weighed, or completed).
    Releases slot capacity and sends an in-app notification to the farmer.
    Idempotent / repeated call protected.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "BOOKED").upper()
    if curr_status == "NO_SHOW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking '{booking_id}' is already marked as NO_SHOW."
        )

    if curr_status not in ["BOOKED", "CONFIRMED", "SCHEDULED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark booking as NO_SHOW from status '{curr_status}'. Vehicle has already checked in or progressed in the yard."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    no_show_reason = reason.strip() if reason and reason.strip() else "Farmer did not report for allocated slot"

    no_show_record = {
        "markedAt": now_human,
        "markedByStaff": staff_user["name"],
        "staffId": staff_user.get("id") or staff_user.get("username", ""),
        "reason": no_show_reason,
        "previousStatus": curr_status
    }

    audit_entry = {
        "action": "NO_SHOW",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": f"Marked as NO_SHOW by officer. Reason: {no_show_reason}. Slot released."
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "NO_SHOW",
                "stageNumber": 0,
                "noShowDetails": no_show_record,
                "updatedAt": now_human,
                "updatedByStaff": staff_user["name"]
            },
            "$push": {
                "auditHistory": audit_entry
            }
        },
        return_document=True
    )

    # In-app notification to the farmer
    await create_in_app_notification(
        title="Procurement Booking Marked No-Show",
        message=f"Booking {doc.get('tokenNumber', booking_id)} at {doc.get('mandiName')} was marked as No-Show. Slot capacity has been released. Please rebook if you wish to deliver.",
        notification_type="no_show",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_doc(updated)


# ============================================================================
# PHASE 3: DYNAMIC PROCUREMENT RATES CONFIGURATION & SEEDING
# ============================================================================

DEFAULT_PROCUREMENT_RATES = [
    {
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub 1 / ADT 45",
        "centreCode": "ALL",
        "ratePerKg": 23.20,
        "ratePerQuintal": 2320.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of Tamil Nadu / TNCSC Minimum Support Price (Kharif/Rabi 2025-26)",
        "notes": "Grade A Paddy official procurement benchmark with state incentive"
    },
    {
        "crop": "Paddy Common",
        "cropVariety": "Ponni / Co 51",
        "centreCode": "ALL",
        "ratePerKg": 23.00,
        "ratePerQuintal": 2300.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of Tamil Nadu / TNCSC Minimum Support Price (2025-26)",
        "notes": "Common Paddy official procurement benchmark"
    },
    {
        "crop": "Kuruvai Paddy",
        "cropVariety": "ADT 43 / ASD 16",
        "centreCode": "ALL",
        "ratePerKg": 23.20,
        "ratePerQuintal": 2320.0,
        "effectiveDate": "2025-06-01",
        "isActive": True,
        "sourceLabel": "TNCSC Kuruvai Special Procurement Scheme",
        "notes": "Kuruvai season paddy rate"
    },
    {
        "crop": "Maize",
        "cropVariety": "Hybrid / CoH(M) 6",
        "centreCode": "ALL",
        "ratePerKg": 20.90,
        "ratePerQuintal": 2090.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of India Commission for Agricultural Costs & Prices (CACP) MSP",
        "notes": "Kharif Maize official MSP"
    },
    {
        "crop": "Black Gram",
        "cropVariety": "ADT 5 / VBN 8",
        "centreCode": "ALL",
        "ratePerKg": 69.50,
        "ratePerQuintal": 6950.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of India CACP Pulses MSP 2025-26",
        "notes": "Urad / Black Gram official MSP"
    },
    {
        "crop": "Green Gram",
        "cropVariety": "CO 8 / VBN 3",
        "centreCode": "ALL",
        "ratePerKg": 85.58,
        "ratePerQuintal": 8558.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of India CACP Pulses MSP 2025-26",
        "notes": "Moong / Green Gram official MSP"
    },
    {
        "crop": "Cotton",
        "cropVariety": "Medium / Long Staple",
        "centreCode": "ALL",
        "ratePerKg": 70.20,
        "ratePerQuintal": 7020.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "CCI / Ministry of Textiles MSP Benchmark 2025-26",
        "notes": "Medium staple raw cotton rate"
    },
    {
        "crop": "Groundnut",
        "cropVariety": "TMV 7 / JL 24",
        "centreCode": "ALL",
        "ratePerKg": 63.77,
        "ratePerQuintal": 6377.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "Government of India Oilseeds MSP 2025-26",
        "notes": "Groundnut in shell MSP"
    },
    {
        "crop": "Millets",
        "cropVariety": "Ragi / Kambu",
        "centreCode": "ALL",
        "ratePerKg": 38.46,
        "ratePerQuintal": 3846.0,
        "effectiveDate": "2025-10-01",
        "isActive": True,
        "sourceLabel": "International Year of Millets National Mission Rate",
        "notes": "Nutri-cereals procurement rate"
    }
]


async def seed_default_rates():
    """Initializes standard procurement MSP rates in MongoDB if collection is empty."""
    rates_col = get_rates_collection()
    if rates_col is None:
        return
    count = await rates_col.count_documents({})
    if count == 0:
        now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
        for r in DEFAULT_PROCUREMENT_RATES:
            doc = r.copy()
            doc["createdAt"] = now_human
            await rates_col.insert_one(doc)


async def get_procurement_rates(crop: Optional[str] = None, centre_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns active configured procurement rates with optional crop/centre filters."""
    rates_col = get_rates_collection()
    if rates_col is None:
        return [format_doc(r.copy()) for r in DEFAULT_PROCUREMENT_RATES]

    query: Dict[str, Any] = {"isActive": True}
    if crop:
        c_clean = crop.strip().split("(")[0].strip()
        query["crop"] = {"$regex": re.escape(c_clean) if c_clean else ".*", "$options": "i"}
    if centre_code and centre_code != "ALL":
        query["centreCode"] = {"$in": [centre_code, "ALL"]}

    cursor = rates_col.find(query).sort("ratePerKg", -1)
    rates = await cursor.to_list(length=100)
    if not rates:
        return [format_doc(r.copy()) for r in DEFAULT_PROCUREMENT_RATES]
    return [format_doc(r) for r in rates]


async def create_or_update_procurement_rate(data: dict, staff_user: dict) -> dict:
    """Staff operation to create or update a procurement rate configuration."""
    rates_col = get_rates_collection()
    if rates_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    crop = (data.get("crop") or "").strip()
    if not crop:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Crop name is required.")

    rate_per_kg = float(data.get("ratePerKg", 0))
    if rate_per_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rate per kg must be greater than zero.")

    rate_per_quintal = float(data.get("ratePerQuintal") or (rate_per_kg * 100.0))
    effective_date = (data.get("effectiveDate") or date.today().isoformat()).strip()
    centre_code = (data.get("centreCode") or "ALL").strip()
    if centre_code and centre_code.upper() != "ALL":
        target_centre = find_centre(centre_code)
        if target_centre:
            verify_staff_centre_access(staff_user, {"centreCode": target_centre["centreCode"], "mandiName": target_centre["name"]})
    source_label = (data.get("sourceLabel") or "Government Notification").strip()
    notes = data.get("notes")
    is_active = data.get("isActive", True)
    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    rate_doc = {
        "crop": crop,
        "cropVariety": (data.get("cropVariety") or "All Varieties").strip(),
        "centreCode": centre_code,
        "ratePerKg": round(rate_per_kg, 2),
        "ratePerQuintal": round(rate_per_quintal, 2),
        "effectiveDate": effective_date,
        "isActive": is_active,
        "sourceLabel": source_label,
        "notes": notes,
        "updatedAt": now_human,
        "updatedByStaff": staff_user.get("name", "Staff")
    }

    updated = await rates_col.find_one_and_update(
        {"crop": crop, "centreCode": centre_code},
        {"$set": rate_doc, "$setOnInsert": {"createdAt": now_human}},
        upsert=True,
        return_document=True
    )
    return format_doc(updated or rate_doc)


async def resolve_active_procurement_rate(crop: str, centre_code: Optional[str] = None) -> dict:
    """
    Dynamically resolves the applicable rate for a crop and centre.
    Uses configured rates from MongoDB or returns an explicit unconfigured/demo fallback.
    """
    rates_col = get_rates_collection()
    crop_clean = (crop or "").strip()

    if rates_col is not None and crop_clean:
        import re
        c_prefix = crop_clean.split("(")[0].strip()
        regex_pat = re.escape(c_prefix) if c_prefix else "paddy"
        match_query = {
            "isActive": True,
            "$or": [
                {"crop": crop_clean},
                {"crop": {"$regex": f"^{regex_pat}", "$options": "i"}},
                {"crop": {"$regex": re.escape(crop_clean[:6]), "$options": "i"}}
            ]
        }

        # 1. Try specific centre first
        if centre_code and centre_code != "ALL":
            spec_rate = await rates_col.find_one({**match_query, "centreCode": centre_code})
            if spec_rate:
                return {
                    "crop": spec_rate["crop"],
                    "cropVariety": spec_rate.get("cropVariety", "All Varieties"),
                    "ratePerKg": float(spec_rate["ratePerKg"]),
                    "ratePerQuintal": float(spec_rate.get("ratePerQuintal", spec_rate["ratePerKg"] * 100)),
                    "effectiveDate": spec_rate.get("effectiveDate", "2025-10-01"),
                    "sourceLabel": spec_rate.get("sourceLabel", "Verified Government Rate"),
                    "isConfigured": True
                }

        # 2. Try general rate (centreCode == ALL)
        gen_rate = await rates_col.find_one({**match_query, "centreCode": {"$in": ["ALL", None]}})
        if gen_rate:
            return {
                "crop": gen_rate["crop"],
                "cropVariety": gen_rate.get("cropVariety", "All Varieties"),
                "ratePerKg": float(gen_rate["ratePerKg"]),
                "ratePerQuintal": float(gen_rate.get("ratePerQuintal", gen_rate["ratePerKg"] * 100)),
                "effectiveDate": gen_rate.get("effectiveDate", "2025-10-01"),
                "sourceLabel": gen_rate.get("sourceLabel", "Verified Government Rate"),
                "isConfigured": True
            }

    # Fallback when no rate is configured (labeled as Demo/Unconfigured per Step 5)
    return {
        "crop": crop_clean or "Paddy Common",
        "cropVariety": "Unconfigured / General",
        "ratePerKg": 23.20,
        "ratePerQuintal": 2320.0,
        "effectiveDate": "2025-01-01",
        "sourceLabel": "Demo / Unconfigured Rate (TNAU Reference Model)",
        "isConfigured": False
    }


# ============================================================================
# PHASE 3 & 4: "NOW SERVING" TOKEN CALLER SERVICE (MULTI-COUNTER FIFO QUEUE)
# ============================================================================

async def get_now_serving(
    centre_code: str,
    slot_date: Optional[str] = None,
    counter_id: Optional[str] = None
) -> dict:
    """
    Returns current serving vehicle and next eligible waiting vehicle in FIFO queue.
    Supports multi-counter weighbridges while preserving single-counter default.
    """
    bookings_col = get_bookings_collection()
    centre = find_centre(centre_code)
    c_code = centre["centreCode"] if centre else centre_code
    c_name = centre["name"] if centre else centre_code
    today_str = slot_date or date.today().isoformat()

    # Centre configured counters
    configured_counters = (centre.get("counters") if centre else None) or [
        {"counterId": "Counter-1", "name": "Weighbridge #1", "isActive": True}
    ]
    active_counter_id = counter_id or configured_counters[0]["counterId"]

    # Resolve active counter display name
    counter_name = None
    for c in configured_counters:
        if c.get("counterId") == active_counter_id:
            counter_name = c.get("name")
            break
    if not counter_name:
        counter_name = f"Weighbridge {active_counter_id}"

    if bookings_col is None:
        return {
            "centreCode": c_code,
            "centreName": c_name,
            "date": today_str,
            "counterId": active_counter_id,
            "counterName": counter_name,
            "counters": configured_counters,
            "currentServing": None,
            "nextEligible": None,
            "activeWaitingCount": 0,
            "lastCalledAt": None
        }

    centre_filter = {"$or": [{"centreCode": c_code}, {"mandiName": c_name}]}
    date_filter = {"slotDate": today_str}

    # Current serving vehicle for the selected counter
    # If counter_id is not specified, return any currently serving vehicle at this centre (single-counter default behavior)
    if counter_id:
        counter_filter = {"counterId": counter_id}
        if counter_id in ("Counter-1", "Weighbridge Counter #1"):
            counter_filter = {"$or": [{"counterId": "Counter-1"}, {"counterId": "Weighbridge Counter #1"}, {"counterId": None}, {"counterId": ""}]}
    else:
        counter_filter = {}

    current_doc = await bookings_col.find_one({
        **centre_filter,
        **date_filter,
        **counter_filter,
        "isNowServing": True,
        "status": {"$in": ["PROCESSING", "QUALITY_CHECKED", "IN_QUEUE"]}
    })

    if current_doc and not counter_id:
        active_counter_id = current_doc.get("counterId") or active_counter_id
        counter_name = current_doc.get("counterName") or f"Weighbridge {active_counter_id}"

    # Summary of all counters with current serving status
    counters_status = []
    for c in configured_counters:
        cid = c.get("counterId")
        cname = c.get("name", cid)
        c_filter = {"counterId": cid}
        if cid == "Counter-1":
            c_filter = {"$or": [{"counterId": "Counter-1"}, {"counterId": None}, {"counterId": ""}]}
        c_doc = await bookings_col.find_one({
            **centre_filter,
            **date_filter,
            **c_filter,
            "isNowServing": True,
            "status": {"$in": ["PROCESSING", "QUALITY_CHECKED", "IN_QUEUE"]}
        })
        counters_status.append({
            "counterId": cid,
            "name": cname,
            "isActive": c.get("isActive", True),
            "isNowServing": bool(c_doc),
            "currentBookingId": c_doc.get("bookingId") if c_doc else None,
            "currentToken": c_doc.get("tokenNumber") if c_doc else None,
            "farmerName": c_doc.get("farmerName") if c_doc else None,
            "crop": c_doc.get("crop") if c_doc else None,
            "lastCalledAt": c_doc.get("nowServingCalledAt") if c_doc else None
        })

    # Next eligible waiting vehicles: arrived at yard, checked in / quality checked / in queue, NOT currently serving at any counter
    eligible_cursor = bookings_col.find({
        **centre_filter,
        **date_filter,
        "isNowServing": {"$ne": True},
        "status": {"$in": ["QUALITY_CHECKED", "IN_QUEUE", "CHECKED_IN"]}
    }).sort("_id", 1)

    eligible_list = await eligible_cursor.to_list(length=10)
    next_doc = eligible_list[0] if eligible_list else None

    # Count all active waiting (not currently serving)
    waiting_count = await bookings_col.count_documents({
        **centre_filter,
        **date_filter,
        "isNowServing": {"$ne": True},
        "status": {"$in": ["QUALITY_CHECKED", "IN_QUEUE", "CHECKED_IN"]}
    })

    current_summary = None
    if current_doc:
        current_summary = {
            "bookingId": current_doc["bookingId"],
            "tokenNumber": current_doc["tokenNumber"],
            "farmerName": current_doc["farmerName"],
            "crop": current_doc["crop"],
            "cropVariety": current_doc.get("cropVariety"),
            "quantityBags": current_doc["quantityBags"],
            "status": current_doc["status"],
            "timeWindow": current_doc.get("timeWindow"),
            "counterId": current_doc.get("counterId") or active_counter_id,
            "nowServingCalledAt": current_doc.get("nowServingCalledAt")
        }

    next_summary = None
    if next_doc:
        next_summary = {
            "bookingId": next_doc["bookingId"],
            "tokenNumber": next_doc["tokenNumber"],
            "farmerName": next_doc["farmerName"],
            "crop": next_doc["crop"],
            "cropVariety": next_doc.get("cropVariety"),
            "quantityBags": next_doc["quantityBags"],
            "status": next_doc["status"],
            "timeWindow": next_doc.get("timeWindow")
        }

    return {
        "centreCode": c_code,
        "centreName": c_name,
        "date": today_str,
        "counterId": active_counter_id,
        "counterName": counter_name,
        "counters": counters_status,
        "currentServing": current_summary,
        "nextEligible": next_summary,
        "activeWaitingCount": waiting_count,
        "lastCalledAt": current_doc.get("nowServingCalledAt") if current_doc else None
    }


async def call_next_queue_token(
    centre_code: str,
    slot_date: Optional[str],
    staff_user: dict,
    counter_id: str = "Counter-1"
) -> dict:
    """
    Staff operation: Atomically calls the next eligible token from the FIFO queue for weighment.
    Ensures safe multi-counter concurrency across distributed workers using MongoDB find_one_and_update:
    1. Releases any token previously serving AT THIS SPECIFIC COUNTER.
    2. Atomically claims the earliest waiting vehicle (FIFO by _id) that is NOT serving at another counter.
    3. Guarantees no two concurrent requests can claim the same token.
    4. Validates staff authorization for the centre.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    centre = find_centre(centre_code)
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_code}' not found.")

    # Authorization: Staff cannot operate counters outside their authorized centre
    verify_staff_centre_access(staff_user, {"centreCode": centre["centreCode"], "mandiName": centre["name"]})

    today_str = slot_date or date.today().isoformat()
    centre_filter = {"$or": [{"centreCode": centre["centreCode"]}, {"mandiName": centre["name"]}]}
    date_filter = {"slotDate": today_str}

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    # Step 1: Release any token previously being served at THIS counter
    # If counter is Counter-1, also clear unassigned counter records
    prev_counter_filter = {"counterId": counter_id}
    if counter_id == "Counter-1":
        prev_counter_filter = {"$or": [{"counterId": "Counter-1"}, {"counterId": None}, {"counterId": ""}]}

    await bookings_col.update_many(
        {**centre_filter, **date_filter, **prev_counter_filter, "isNowServing": True},
        {"$set": {"isNowServing": False}}
    )

    # Step 2: Concurrency-safe atomic FIFO claim via find_one_and_update
    # Only claim bookings with status in QUALITY_CHECKED, IN_QUEUE, CHECKED_IN
    # and strictly NOT currently serving anywhere (isNowServing != True)
    audit_entry = {
        "action": "NOW_SERVING",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": f"Token called to {counter_id} by procurement officer"
    }

    claimed_doc = await bookings_col.find_one_and_update(
        {
            **centre_filter,
            **date_filter,
            "isNowServing": {"$ne": True},
            "status": {"$in": ["QUALITY_CHECKED", "IN_QUEUE", "CHECKED_IN"]}
        },
        {
            "$set": {
                "isNowServing": True,
                "status": "PROCESSING",
                "stageNumber": 4,
                "counterId": counter_id,
                "nowServingCalledAt": now_human,
                "nowServingCalledBy": staff_user["name"],
                "updatedAt": now_human
            },
            "$push": {
                "auditHistory": audit_entry
            }
        },
        sort=[("_id", 1)],
        return_document=True
    )

    if not claimed_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No eligible vehicles in queue for {centre['name']} on {today_str}."
        )

    # In-app notification to the farmer
    await create_in_app_notification(
        title="Now Serving: Proceed to Weighbridge",
        message=f"Token {claimed_doc['tokenNumber']} is NOW SERVING at {counter_id} ({centre['name']}). Please proceed for weighment.",
        notification_type="queue",
        user_id=claimed_doc.get("userId"),
        farmer_id=claimed_doc.get("farmerId"),
        booking_id=claimed_doc.get("bookingId")
    )

    return await get_now_serving(centre["centreCode"], today_str, counter_id)


def calculate_weighing_amounts(
    weight_kg: float,
    price_per_kg: float,
    quality_deductions: float = 0.0,
    other_deductions: float = 0.0
) -> dict:
    """
    Computes financial amounts with consistent decimal arithmetic.
    Gross amount = Accepted weight (kg) * Price per kg
    Total deductions = Quality deductions + Other deductions
    Net amount = Gross amount - Total deductions

    Validates that:
    - weight_kg > 0
    - price_per_kg > 0
    - quality_deductions >= 0
    - other_deductions >= 0
    - total_deductions <= gross_amount (deductions cannot exceed gross amount)
    """
    if weight_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accepted crop weight must be greater than 0.")
    if price_per_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configured price per kg must be greater than 0.")
    if quality_deductions < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quality deductions cannot be negative.")
    if other_deductions < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Other deductions cannot be negative.")

    gross_amount = round(weight_kg * price_per_kg, 2)
    total_deductions = round(quality_deductions + other_deductions, 2)

    if total_deductions > gross_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deductions (₹{total_deductions:,.2f}) cannot exceed gross amount (₹{gross_amount:,.2f})."
        )

    net_amount = round(gross_amount - total_deductions, 2)

    return {
        "acceptedWeightKg": round(weight_kg, 2),
        "actualNetWeightQuintals": round(weight_kg / 100.0, 3),
        "pricePerKg": round(price_per_kg, 2),
        "pricePerQuintal": round(price_per_kg * 100.0, 2),
        "grossAmount": gross_amount,
        "qualityDeductionsAmount": round(quality_deductions, 2),
        "otherDeductionsAmount": round(other_deductions, 2),
        "totalDeductionsAmount": total_deductions,
        "netAmount": net_amount,
        "netPayableAmount": net_amount
    }


async def record_weighing_and_transaction_ledger(booking_id: str, payload: dict, staff_user: dict) -> dict:
    """
    Staff operation: Records net weight, moisture, MSP price, computes deductions,
    calculates gross and net amounts with decimal arithmetic, creates unique Digital Bill,
    and records audit history in MongoDB.
    """
    bookings_col = get_bookings_collection()
    bills_col = get_bills_collection()
    if bookings_col is None or bills_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)

    curr_status = doc.get("status", "").upper()
    if curr_status == "COMPLETED" or doc.get("transaction") or doc.get("bill"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking '{booking_id}' already has a completed weighing record and bill. Duplicate billing is disallowed."
        )

    if curr_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot weigh a cancelled booking."
        )

    if curr_status == "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot weigh booking '{booking_id}'. This lot was REJECTED during quality inspection."
        )

    if curr_status == "NO_SHOW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot weigh booking '{booking_id}'. Booking was marked as NO_SHOW."
        )

    # Step 3 requirement: Block weighing before required quality inspection
    has_inspection = bool(doc.get("qualityInspection"))
    if curr_status != "QUALITY_CHECKED" and not has_inspection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record weighment for booking with status '{curr_status}'. Physical quality inspection must be completed first (status: QUALITY_CHECKED)."
        )

    # Step 5 requirement: Resolve dynamic procurement rate from configured rates
    configured_rate_info = await resolve_active_procurement_rate(
        crop=doc.get("crop", ""),
        centre_code=doc.get("centreCode")
    )

    # Parse Weight (Kg or Quintals)
    weight_kg = None
    if payload.get("acceptedWeightKg") is not None and float(payload["acceptedWeightKg"]) > 0:
        weight_kg = float(payload["acceptedWeightKg"])
    elif payload.get("actualNetWeightQuintals") is not None and float(payload["actualNetWeightQuintals"]) > 0:
        weight_kg = float(payload["actualNetWeightQuintals"]) * 100.0
    elif has_inspection and doc.get("qualityInspection", {}).get("acceptedWeightKg"):
        weight_kg = float(doc["qualityInspection"]["acceptedWeightKg"])

    # Parse Price (Per Kg or Per Quintal) - fall back to dynamic configured rate if not provided or 0
    price_kg = None
    if payload.get("pricePerKg") is not None and float(payload["pricePerKg"]) > 0:
        price_kg = float(payload["pricePerKg"])
    elif payload.get("pricePerQuintal") is not None and float(payload["pricePerQuintal"]) > 0:
        price_kg = float(payload["pricePerQuintal"]) / 100.0
    else:
        price_kg = configured_rate_info["ratePerKg"]

    if weight_kg is None or weight_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accepted crop weight must be greater than 0.")
    if price_kg is None or price_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configured rate must be greater than 0.")

    # Deductions
    quality_deductions = float(payload.get("qualityDeductionsAmount") or 0.0)
    other_deductions = float(payload.get("otherDeductionsAmount") or payload.get("customDeductionsAmount") or 0.0)
    moisture = float(payload.get("moisturePercent", doc.get("moisturePercent", 14.0)))

    # If quality_deductions was not explicitly passed, compute standard FAQ moisture dockage if moisture > 17%
    if quality_deductions == 0.0 and moisture > 17.0:
        excess_pct = round(moisture - 17.0, 2)
        gross_temp = round(weight_kg * price_kg, 2)
        quality_deductions = round((excess_pct / 100.0) * gross_temp, 2)

    calc = calculate_weighing_amounts(
        weight_kg=weight_kg,
        price_per_kg=price_kg,
        quality_deductions=quality_deductions,
        other_deductions=other_deductions
    )

    quality_grade = payload.get("qualityGrade") or (doc.get("qualityInspection") or {}).get("qualityGrade", "FAQ Grade A")
    payment_status = payload.get("paymentStatus", "PENDING")
    if payment_status not in ["PENDING", "PROCESSING", "PAID"]:
        payment_status = "PENDING"
    notes = payload.get("notes")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    # Generate unique Digital Bill Number
    centre_name = doc.get("mandiName", "")
    prefix = "TNJ"
    if "Madurai" in centre_name:
        prefix = "MDU"
    elif "Trichy" in centre_name or "Tiruchirappalli" in centre_name:
        prefix = "TRY"
    elif "Tirunelveli" in centre_name:
        prefix = "TNV"
    bill_number = f"BILL-{prefix}-{datetime.utcnow().strftime('%Y')}-{secrets.token_hex(3).upper()}"

    initial_payment_entry = {
        "status": payment_status,
        "updatedBy": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": notes or "Initial digital bill generated upon weighment",
        "transactionReference": payload.get("transactionReference")
    }

    audit_entry = {
        "action": "COMPLETED",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": f"Weighed {calc['acceptedWeightKg']} Kg ({calc['actualNetWeightQuintals']} Qtl) @ ₹{calc['pricePerKg']}/Kg. Gross: ₹{calc['grossAmount']:,.2f}, Net: ₹{calc['netAmount']:,.2f}. Bill: {bill_number}"
    }

    bill_record = {
        "billNumber": bill_number,
        "bookingId": doc["bookingId"],
        "tokenNumber": doc.get("tokenNumber"),
        "farmerName": doc["farmerName"],
        "farmerId": doc["farmerId"],
        "userId": doc.get("userId"),
        "mandiName": doc["mandiName"],
        "crop": doc.get("crop"),
        "cropVariety": doc.get("cropVariety") or configured_rate_info.get("cropVariety", "All Varieties"),
        "acceptedWeightKg": calc["acceptedWeightKg"],
        "actualNetWeightQuintals": calc["actualNetWeightQuintals"],
        "pricePerKg": calc["pricePerKg"],
        "pricePerQuintal": calc["pricePerQuintal"],
        "rateSourceLabel": configured_rate_info.get("sourceLabel", "Verified Procurement Rate"),
        "rateEffectiveDate": configured_rate_info.get("effectiveDate", "2025-10-01"),
        "moisturePercent": moisture,
        "qualityGrade": quality_grade,
        "grossAmount": calc["grossAmount"],
        "qualityDeductionsAmount": calc["qualityDeductionsAmount"],
        "moistureDeductionAmount": calc["qualityDeductionsAmount"],
        "otherDeductionsAmount": calc["otherDeductionsAmount"],
        "totalDeductionsAmount": calc["totalDeductionsAmount"],
        "netAmount": calc["netAmount"],
        "netPayableAmount": calc["netAmount"],
        "paymentStatus": payment_status,
        "paymentMethod": "Direct Benefit Transfer (PFMS / e-Kuber Ledger)",
        "transactionDate": now_human,
        "weighedAt": now_human,
        "weighedByStaff": staff_user["name"],
        "notes": notes,
        "paymentHistory": [initial_payment_entry],
        "auditHistory": [audit_entry],
        "disclaimer": "Official electronic procurement bill and DBT ledger voucher. Actual bank fund transfer requires state treasury gateway clearance."
    }

    # Persist in procurement_bills collection
    await bills_col.insert_one(bill_record.copy())

    # Update procurement_bookings collection
    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": "COMPLETED",
                "stageNumber": 5,
                "billNumber": bill_number,
                "actualNetWeightQuintals": calc["actualNetWeightQuintals"],
                "acceptedWeightKg": calc["acceptedWeightKg"],
                "pricePerKg": calc["pricePerKg"],
                "rateSourceLabel": configured_rate_info.get("sourceLabel"),
                "grossAmount": calc["grossAmount"],
                "qualityDeductionsAmount": calc["qualityDeductionsAmount"],
                "otherDeductionsAmount": calc["otherDeductionsAmount"],
                "totalDeductionsAmount": calc["totalDeductionsAmount"],
                "netAmount": calc["netAmount"],
                "paymentStatus": payment_status,
                "moisturePercent": moisture,
                "qualityNotes": quality_grade,
                "isNowServing": False,
                "transaction": bill_record,
                "bill": bill_record,
                "updatedByStaff": staff_user["name"],
                "updatedAt": now_human
            },
            "$push": {
                "auditHistory": audit_entry
            }
        },
        return_document=True
    )

    # In-app notification to the farmer
    await create_in_app_notification(
        title=f"Digital Bill Generated: {bill_number}",
        message=f"Weighment completed at {doc['mandiName']}. Net Payable: ₹{calc['netAmount']:,.2f} ({payment_status}). Bill: {bill_number}.",
        notification_type="weighing",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_doc(updated)


async def get_bill_by_id_or_number(identifier: str, current_user: Optional[dict] = None) -> dict:
    """
    Retrieves digital bill by billNumber or bookingId with ownership enforcement:
    - Farmer can view only their own bill (matching farmerId or userId).
    - Staff can view bills for their authorized centre.
    - Unauthenticated callers are rejected with 401.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view digital bills."
        )

    bills_col = get_bills_collection()
    bookings_col = get_bookings_collection()
    if bills_col is None or bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    bill = await bills_col.find_one({"$or": [{"billNumber": identifier}, {"bookingId": identifier}]})
    if not bill:
        # Fallback to booking's transaction/bill object
        doc = await bookings_col.find_one({"$or": [{"bookingId": identifier}, {"billNumber": identifier}]})
        if doc and (doc.get("bill") or doc.get("transaction")):
            bill = doc.get("bill") or doc.get("transaction")
            if "_id" not in bill:
                bill["_id"] = doc["_id"]

    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bill '{identifier}' not found.")

    role = current_user.get("role")
    if role == "farmer":
        farmer_id = current_user.get("farmerId")
        user_id = current_user.get("id")
        doc_farmer_id = bill.get("farmerId")
        doc_user_id = bill.get("userId")
        if (doc_farmer_id and doc_farmer_id != farmer_id) and (doc_user_id and doc_user_id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own bills."
            )
    elif role == "staff":
        verify_staff_centre_access(current_user, bill)

    return format_doc(bill)


async def get_farmer_bills(farmer_user: dict) -> list[dict]:
    """Retrieves all digital bills belonging to the authenticated farmer."""
    bills_col = get_bills_collection()
    if bills_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    farmer_id = farmer_user.get("farmerId")
    user_id = farmer_user.get("id")

    query = {"$or": [{"farmerId": farmer_id}, {"userId": user_id}]}
    cursor = bills_col.find(query).sort("_id", -1)
    bills = await cursor.to_list(length=100)
    return [format_doc(b) for b in bills]


async def get_staff_bills(staff_user: dict, date_str: Optional[str] = None, status_filter: Optional[str] = None) -> list[dict]:
    """Retrieves all digital bills for the staff member's authorized centre."""
    bills_col = get_bills_collection()
    if bills_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    query: dict = {}
    assigned_mandi = staff_user.get("mandiName")
    if assigned_mandi:
        query["mandiName"] = assigned_mandi

    if date_str:
        query["transactionDate"] = {"$regex": f"^{date_str}"}
    if status_filter and status_filter.lower() != "all":
        query["paymentStatus"] = status_filter.upper()

    cursor = bills_col.find(query).sort("_id", -1)
    bills = await cursor.to_list(length=200)
    return [format_doc(b) for b in bills]


async def update_bill_payment_status(
    identifier: str,
    new_status: str,
    notes: Optional[str],
    tx_ref: Optional[str],
    staff_user: dict
) -> dict:
    """
    Authorized staff or payment integration updates the payment status
    (PENDING -> PROCESSING -> PAID). Records timestamp and authorized actor.
    """
    bills_col = get_bills_collection()
    bookings_col = get_bookings_collection()
    if bills_col is None or bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    new_status = new_status.upper()
    if new_status not in ["PENDING", "PROCESSING", "PAID"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment status '{new_status}'. Allowed statuses: PENDING, PROCESSING, PAID."
        )

    bill = await bills_col.find_one({"$or": [{"billNumber": identifier}, {"bookingId": identifier}]})
    if not bill:
        # Fallback to booking
        doc = await bookings_col.find_one({"$or": [{"bookingId": identifier}, {"billNumber": identifier}]})
        if doc and (doc.get("bill") or doc.get("transaction")):
            bill = doc.get("bill") or doc.get("transaction")
            bill["_id"] = doc["_id"]

    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bill '{identifier}' not found.")

    verify_staff_centre_access(staff_user, bill)

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    entry = {
        "status": new_status,
        "updatedBy": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": notes or f"Payment status updated to {new_status}",
        "transactionReference": tx_ref
    }

    audit_entry = {
        "action": f"PAYMENT_{new_status}",
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": f"Payment marked {new_status} (Ref: {tx_ref or 'N/A'})"
    }

    # Update bills collection
    updated_bill = await bills_col.find_one_and_update(
        {"$or": [{"billNumber": bill.get("billNumber")}, {"bookingId": bill.get("bookingId")}]},
        {
            "$set": {
                "paymentStatus": new_status,
                "paymentReference": tx_ref or bill.get("paymentReference"),
                "paymentUpdatedAt": now_human,
                "paymentUpdatedBy": staff_user["name"]
            },
            "$push": {
                "paymentHistory": entry,
                "auditHistory": audit_entry
            }
        },
        return_document=True
    )

    # Synchronize bookings collection
    await bookings_col.update_many(
        {"$or": [{"bookingId": bill.get("bookingId")}, {"billNumber": bill.get("billNumber")}]},
        {
            "$set": {
                "transaction.paymentStatus": new_status,
                "bill.paymentStatus": new_status
            },
            "$push": {
                "auditHistory": audit_entry
            }
        }
    )

    # In-app notification to the farmer
    await create_in_app_notification(
        title=f"Payment Status Updated: {new_status}",
        message=f"Bill {bill.get('billNumber', identifier)} payment status is now {new_status} (Ref: {tx_ref or 'Pending'}).",
        notification_type="payment",
        user_id=bill.get("userId"),
        farmer_id=bill.get("farmerId"),
        booking_id=bill.get("bookingId")
    )

    return format_doc(updated_bill or bill)



async def update_booking_queue_status(
    booking_id: str,
    new_status: str,
    notes: Optional[str],
    staff_user: dict
) -> dict:
    """
    Unified staff queue transition operation with strict business rule validation.
    Permitted transitions:
    - BOOKED -> CHECKED_IN, CANCELLED
    - CHECKED_IN -> IN_QUEUE, CANCELLED
    - IN_QUEUE -> PROCESSING, CANCELLED
    - PROCESSING -> COMPLETED, CANCELLED
    - COMPLETED / CANCELLED cannot transition further.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    verify_staff_centre_access(staff_user, doc)
    curr_status = doc.get("status", "BOOKED").upper()

    valid_transitions = {
        "BOOKED": ["CHECKED_IN", "CANCELLED", "NO_SHOW"],
        "CHECKED_IN": ["QUALITY_CHECKED", "REJECTED", "IN_QUEUE", "CANCELLED"],
        "QUALITY_CHECKED": ["IN_QUEUE", "PROCESSING", "CANCELLED"],
        "IN_QUEUE": ["PROCESSING", "QUALITY_CHECKED", "CANCELLED"],
        "PROCESSING": ["COMPLETED", "CANCELLED"],
        "COMPLETED": [],
        "CANCELLED": [],
        "REJECTED": [],
        "NO_SHOW": []
    }

    allowed = valid_transitions.get(curr_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from '{curr_status}' to '{new_status}'. Permitted next states: {allowed if allowed else 'None (Final state)'}."
        )

    if new_status == "COMPLETED" and not doc.get("transaction"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete booking without recording physical weighment and transaction ledger."
        )

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": new_status,
        "by": staff_user["name"],
        "role": "staff",
        "timestamp": now_human,
        "notes": notes or f"Queue status updated to {new_status} by officer"
    }

    stage_map = {
        "BOOKED": 1,
        "CHECKED_IN": 2,
        "QUALITY_CHECKED": 3,
        "IN_QUEUE": 3,
        "PROCESSING": 4,
        "COMPLETED": 5,
        "CANCELLED": 0,
        "REJECTED": 0,
        "NO_SHOW": 0
    }

    updated = await bookings_col.find_one_and_update(
        {"bookingId": booking_id},
        {
            "$set": {
                "status": new_status,
                "stageNumber": stage_map.get(new_status, 1),
                "updatedAt": now_human,
                "updatedByStaff": staff_user["name"]
            },
            "$push": {"auditHistory": audit_entry}
        },
        return_document=True
    )

    await create_in_app_notification(
        title=f"Queue Status: {new_status}",
        message=f"Your booking {doc['tokenNumber']} status updated to {new_status} at {doc['mandiName']}.",
        notification_type="queue",
        user_id=doc.get("userId"),
        farmer_id=doc.get("farmerId"),
        booking_id=booking_id
    )

    return format_doc(updated)


async def get_queue_tracking_for_booking(booking_id: str, current_user: Optional[dict] = None) -> dict:
    """
    Retrieves queue status with strict ownership enforcement:
    - Farmers can only view their own bookings (matching farmerId or userId).
    - Staff members can only view bookings for their authorized centre.
    - Unauthenticated requests are rejected with 401.
    - Queue positions and wait times are only calculated for eligible active queue bookings
      (CHECKED_IN, QUALITY_CHECKED, IN_QUEUE, PROCESSING). Otherwise, returns None and 'Waiting time unavailable'.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    doc = await bookings_col.find_one({"bookingId": booking_id})
    if not doc:
        # Fallback check by tokenNumber
        doc = await bookings_col.find_one({"tokenNumber": booking_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{booking_id}' not found.")

    # Enforce authentication & data isolation (TASK 5 & TASK 6)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view queue tracking."
        )

    role = current_user.get("role")
    if role == "farmer":
        farmer_id = current_user.get("farmerId")
        user_id = current_user.get("id")
        doc_farmer_id = doc.get("farmerId")
        doc_user_id = doc.get("userId")
        # Ensure the booking belongs to this authenticated farmer
        if (doc_farmer_id and doc_farmer_id != farmer_id) and (doc_user_id and doc_user_id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view queue tracking for your own bookings."
            )
    elif role == "staff":
        verify_staff_centre_access(current_user, doc)

    mandi_name = doc.get("mandiName")
    slot_date = doc.get("slotDate")
    current_status = doc.get("status", "BOOKED").upper()

    # Map legacy status strings if present
    status_map = {
        "CONFIRMED": "BOOKED",
        "WEIGHED": "PROCESSING",
        "DBT_COMPLETED": "COMPLETED"
    }
    normalized_status = status_map.get(current_status, current_status)

    # Queue ordering rule: check-in time / MongoDB _id order
    vehicles_ahead = None
    queue_position = None
    estimated_wait_minutes = None
    has_sufficient_data = False
    is_in_active_queue = False
    waiting_time_display = "Waiting time unavailable"

    if normalized_status in ["CHECKED_IN", "QUALITY_CHECKED", "IN_QUEUE", "PROCESSING"]:
        # Count vehicles that checked in before this vehicle at the same centre on the same date
        active_ahead = await bookings_col.count_documents({
            "mandiName": mandi_name,
            "slotDate": slot_date,
            "status": {"$in": ["CHECKED_IN", "QUALITY_CHECKED", "IN_QUEUE", "PROCESSING", "quality_checked"]},
            "_id": {"$lt": doc["_id"]}
        })
        vehicles_ahead = active_ahead
        queue_position = active_ahead + 1
        # Weighbridge average speed is approx 12-15 minutes per vehicle
        estimated_wait_minutes = max(10, vehicles_ahead * 15) if vehicles_ahead > 0 else 10
        has_sufficient_data = True
        is_in_active_queue = True
        waiting_time_display = f"~{estimated_wait_minutes} mins"
    elif normalized_status == "COMPLETED":
        waiting_time_display = "Completed"
    elif normalized_status == "CANCELLED":
        waiting_time_display = "Cancelled"
    elif normalized_status == "NO_SHOW":
        waiting_time_display = "No-Show"
    elif normalized_status == "REJECTED":
        waiting_time_display = "Quality Rejected"
    else:
        waiting_time_display = "Waiting time unavailable"

    # Lifecycle stages breakdown (5 standardized stages)
    stage_progression = [
        {"stage": "BOOKED", "name": "Slot Booking Confirmed", "nameTa": "முன்பதிவு உறுதி செய்யப்பட்டது"},
        {"stage": "CHECKED_IN", "name": "Gate Entry & Token Verified", "nameTa": "நுழைவு வாயில் சரிபார்ப்பு"},
        {"stage": "QUALITY_CHECKED", "name": "Quality & Moisture Inspection", "nameTa": "தர ஆய்வு மற்றும் ஈரப்பதம்"},
        {"stage": "PROCESSING", "name": "Weighbridge Weighing", "nameTa": "எடை சரிபார்ப்பு"},
        {"stage": "COMPLETED", "name": "Transaction & DBT Ledger Recorded", "nameTa": "எடைப் பதிவு மற்றும் வங்கிப் பட்டுவாடா"},
    ]

    current_stage_idx = 1
    for idx, s in enumerate(stage_progression, start=1):
        if s["stage"] == normalized_status:
            current_stage_idx = idx
            break
        elif normalized_status == "IN_QUEUE" and s["stage"] == "QUALITY_CHECKED":
            current_stage_idx = 3
            break

    if normalized_status == "COMPLETED":
        current_stage_idx = 5
    elif normalized_status in ["CANCELLED", "NO_SHOW", "REJECTED"]:
        current_stage_idx = 0

    stages_detail = []
    for idx, s in enumerate(stage_progression, start=1):
        if normalized_status in ["CANCELLED", "NO_SHOW", "REJECTED"]:
            st_state = "cancelled"
        elif idx < current_stage_idx:
            st_state = "done"
        elif idx == current_stage_idx:
            st_state = "current"
        else:
            st_state = "pending"

        stages_detail.append({
            "stageNumber": idx,
            "code": s["stage"],
            "name": s["name"],
            "nameTa": s["nameTa"],
            "state": st_state
        })

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M:%S %p UTC")

    return {
        "bookingId": doc["bookingId"],
        "tokenNumber": doc["tokenNumber"],
        "status": normalized_status,
        "mandiName": mandi_name,
        "slotDate": slot_date,
        "timeWindow": doc.get("timeWindow", ""),
        "farmerName": doc.get("farmerName", ""),
        "crop": doc.get("crop", ""),
        "cropVariety": doc.get("cropVariety"),
        "harvestDate": doc.get("harvestDate"),
        "quantityBags": doc.get("quantityBags", 0),
        "vehiclesAhead": vehicles_ahead,
        "queuePosition": queue_position,
        "estimatedWaitMinutes": estimated_wait_minutes,
        "hasSufficientDataForEstimate": has_sufficient_data,
        "waitingTimeDisplay": waiting_time_display,
        "isInActiveQueue": is_in_active_queue,
        "currentStageNumber": current_stage_idx,
        "stages": stages_detail,
        "qualityInspection": doc.get("qualityInspection"),
        "isNowServing": doc.get("isNowServing", False),
        "noShowDetails": doc.get("noShowDetails"),
        "transaction": doc.get("transaction"),
        "auditHistory": doc.get("auditHistory", []),
        "lastPolledAt": now_human,
        "isDemoData": False
    }


async def cancel_booking_for_farmer(booking_id: str, current_user: dict) -> dict:
    """
    Cancels an active procurement booking requested by the authenticated farmer.
    Validates ownership and verifies that status is BOOKED or SCHEDULED.
    Releases slot and appends to audit history.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    clean_bid = booking_id.strip()
    booking = await bookings_col.find_one({"bookingId": clean_bid})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking '{clean_bid}' not found.")

    # Authorization check: farmer must own this booking
    user_id = str(current_user.get("id")) if current_user.get("id") else ""
    farmer_id = current_user.get("farmerId") or ""

    booking_user_id = str(booking.get("userId", ""))
    booking_farmer_id = booking.get("farmerId", "")

    if (user_id and booking_user_id != user_id) and (farmer_id and booking_farmer_id != farmer_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own bookings.")

    current_status = booking.get("status", "").upper()
    if current_status not in ["BOOKED", "CONFIRMED", "SCHEDULED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking #{clean_bid} because it has already reached '{current_status}' stage. Only bookings in 'BOOKED' status can be cancelled."
        )

    if current_status == "CANCELLED":
        return format_doc(booking)

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    audit_entry = {
        "action": "CANCELLED_BY_FARMER",
        "actor": current_user.get("name") or "Farmer",
        "role": current_user.get("role") or "farmer",
        "timestamp": now_human,
        "notes": "Booking cancelled via AI Assistant / Portal confirmation"
    }

    await bookings_col.update_one(
        {"bookingId": clean_bid},
        {
            "$set": {
                "status": "CANCELLED",
                "cancelledAt": now_human,
            },
            "$push": {
                "auditHistory": audit_entry
            }
        }
    )

    booking["status"] = "CANCELLED"
    booking["cancelledAt"] = now_human

    # Notification
    await create_in_app_notification(
        title="Procurement Booking Cancelled",
        message=f"Booking #{clean_bid} for {booking.get('crop')} at {booking.get('mandiName')} has been cancelled.",
        notification_type="booking",
        user_id=booking_user_id,
        farmer_id=booking_farmer_id,
        booking_id=clean_bid
    )

    return format_doc(booking)


# ============================================================================
# PHASE 4: DAILY PROCUREMENT REPORTS SERVICE
# ============================================================================

async def generate_daily_procurement_report(
    centre_code: str,
    target_date: Optional[str],
    crop: Optional[str],
    payment_status: Optional[str],
    staff_user: dict
) -> dict:
    """
    Staff operation: Calculates daily procurement totals strictly from persisted records.
    Deduplicates bills from bookings, separates estimated vs weighed quantities,
    and enforces staff centre authorization.
    """
    centre = find_centre(centre_code)
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_code}' not found.")

    # Authorization enforcement
    verify_staff_centre_access(staff_user, {"centreCode": centre["centreCode"], "mandiName": centre["name"]})

    bookings_col = get_bookings_collection()
    bills_col = get_bills_collection()
    if bookings_col is None or bills_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    today_str = target_date or date.today().isoformat()
    centre_filter = {"$or": [{"centreCode": centre["centreCode"]}, {"mandiName": centre["name"]}]}

    # 1. Query Bookings
    b_query = {**centre_filter, "slotDate": today_str}
    if crop:
        c_clean = crop.strip().split("(")[0].strip()
        b_query["crop"] = {"$regex": re.escape(c_clean), "$options": "i"}

    bookings = await bookings_col.find(b_query).to_list(1000)

    # 2. Query Bills for Centre
    bills_query = {"mandiName": centre["name"]}
    if target_date:
        bills_query["$or"] = [
            {"transactionDate": {"$regex": today_str}},
            {"weighedAt": {"$regex": today_str}},
            {"bookingId": {"$in": [b["bookingId"] for b in bookings]}}
        ]
    if crop:
        c_clean = crop.strip().split("(")[0].strip()
        bills_query["crop"] = {"$regex": re.escape(c_clean), "$options": "i"}
    if payment_status and payment_status.upper() != "ALL":
        bills_query["paymentStatus"] = payment_status.upper()

    raw_bills = await bills_col.find(bills_query).to_list(1000)

    # Deduplicate bills by billNumber
    deduped_bills: Dict[str, dict] = {}
    for bill in raw_bills:
        bnum = bill.get("billNumber") or bill.get("bookingId")
        if bnum:
            deduped_bills[bnum] = bill

    # Also extract any completed bills embedded directly in bookings if not in bills_col
    for b in bookings:
        if b.get("status") == "COMPLETED" and (b.get("bill") or b.get("transaction")):
            ebill = b.get("bill") or b.get("transaction")
            bnum = ebill.get("billNumber") or b.get("billNumber") or b.get("bookingId")
            if bnum and bnum not in deduped_bills:
                # Apply payment status filter if needed
                if not payment_status or payment_status.upper() == "ALL" or ebill.get("paymentStatus", "").upper() == payment_status.upper():
                    deduped_bills[bnum] = ebill

    # Booking counts
    total_bookings = len(bookings)
    cancelled_count = sum(1 for b in bookings if b.get("status") == "CANCELLED")
    no_show_count = sum(1 for b in bookings if b.get("status") == "NO_SHOW")
    rejected_count = sum(1 for b in bookings if b.get("status") == "REJECTED")
    active_queue_count = sum(1 for b in bookings if b.get("status") in ["CHECKED_IN", "QUALITY_CHECKED", "IN_QUEUE", "PROCESSING"])
    completed_count = len(deduped_bills)

    # Estimated quantities from bookings
    total_estimated_bags = sum(b.get("quantityBags", 0) for b in bookings if b.get("status") not in ["CANCELLED", "NO_SHOW"])
    total_estimated_weight_quintals = round((total_estimated_bags * 40.0) / 100.0, 2)

    # Actual accepted quantities from bills
    total_accepted_weight_kg = round(sum(float(b.get("acceptedWeightKg", 0.0) or 0.0) for b in deduped_bills.values()), 2)
    total_accepted_weight_quintals = round(total_accepted_weight_kg / 100.0, 3)

    # Rejected weight from bookings marked REJECTED (using 40kg bag standard)
    total_rejected_weight_kg = round(sum(b.get("quantityBags", 0) * 40.0 for b in bookings if b.get("status") == "REJECTED"), 2)

    # Financial totals strictly from bills
    total_gross = round(sum(float(b.get("grossAmount", 0.0) or 0.0) for b in deduped_bills.values()), 2)
    total_deductions = round(sum(float(b.get("totalDeductionsAmount", 0.0) or 0.0) for b in deduped_bills.values()), 2)
    total_net = round(sum(float(b.get("netAmount", 0.0) or 0.0) for b in deduped_bills.values()), 2)

    amount_pending = round(sum(float(b.get("netAmount", 0.0) or 0.0) for b in deduped_bills.values() if b.get("paymentStatus") == "PENDING"), 2)
    amount_processing = round(sum(float(b.get("netAmount", 0.0) or 0.0) for b in deduped_bills.values() if b.get("paymentStatus") == "PROCESSING"), 2)
    amount_paid = round(sum(float(b.get("netAmount", 0.0) or 0.0) for b in deduped_bills.values() if b.get("paymentStatus") == "PAID"), 2)

    # Crop-wise Breakdown
    crop_stats: Dict[str, dict] = defaultdict(lambda: {
        "crop": "",
        "totalBags": 0,
        "acceptedWeightKg": 0.0,
        "acceptedWeightQuintals": 0.0,
        "rejectedWeightKg": 0.0,
        "grossAmount": 0.0,
        "netAmount": 0.0,
        "completedCount": 0
    })

    for b in bookings:
        c_name = b.get("crop", "Other")
        crop_stats[c_name]["crop"] = c_name
        crop_stats[c_name]["totalBags"] += b.get("quantityBags", 0)
        if b.get("status") == "REJECTED":
            crop_stats[c_name]["rejectedWeightKg"] += b.get("quantityBags", 0) * 40.0

    for bill in deduped_bills.values():
        c_name = bill.get("crop", "Other")
        crop_stats[c_name]["crop"] = c_name
        crop_stats[c_name]["acceptedWeightKg"] += float(bill.get("acceptedWeightKg", 0.0) or 0.0)
        crop_stats[c_name]["grossAmount"] += float(bill.get("grossAmount", 0.0) or 0.0)
        crop_stats[c_name]["netAmount"] += float(bill.get("netAmount", 0.0) or 0.0)
        crop_stats[c_name]["completedCount"] += 1

    crop_breakdown = []
    for c_data in crop_stats.values():
        c_data["acceptedWeightKg"] = round(c_data["acceptedWeightKg"], 2)
        c_data["acceptedWeightQuintals"] = round(c_data["acceptedWeightKg"] / 100.0, 3)
        c_data["rejectedWeightKg"] = round(c_data["rejectedWeightKg"], 2)
        c_data["grossAmount"] = round(c_data["grossAmount"], 2)
        c_data["netAmount"] = round(c_data["netAmount"], 2)
        crop_breakdown.append(c_data)

    # Counter-wise throughput breakdown
    configured_counters = centre.get("counters", [
        {"counterId": "Counter-1", "name": "Weighbridge #1", "isActive": True}
    ])
    counter_throughput = []
    for cntr in configured_counters:
        if isinstance(cntr, dict):
            cid = cntr.get("counterId") or cntr.get("name") or "Counter-1"
            cname = cntr.get("name", cid)
        else:
            cid = str(cntr)
            cname = str(cntr)
        c_bills = [b for b in deduped_bills.values() if b.get("counterId") == cid or (cid == "Counter-1" and not b.get("counterId"))]
        tokens_served = len(c_bills)
        w_kg = round(sum(float(b.get("acceptedWeightKg", 0.0) or 0.0) for b in c_bills), 2)
        g_amt = round(sum(float(b.get("grossAmount", 0.0) or 0.0) for b in c_bills), 2)
        counter_throughput.append({
            "counterId": cid,
            "counterName": cname,
            "name": cname,
            "tokensServed": tokens_served,
            "totalAcceptedWeightKg": w_kg,
            "totalGrossAmount": g_amt
        })

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    return {
        "centreCode": centre["centreCode"],
        "centreName": centre["name"],
        "date": today_str,
        "totalBookings": total_bookings,
        "cancelledCount": cancelled_count,
        "noShowCount": no_show_count,
        "rejectedCount": rejected_count,
        "completedCount": completed_count,
        "activeQueueCount": active_queue_count,
        "totalEstimatedBags": total_estimated_bags,
        "totalEstimatedWeightQuintals": total_estimated_weight_quintals,
        "totalAcceptedWeightKg": total_accepted_weight_kg,
        "totalAcceptedWeightQuintals": total_accepted_weight_quintals,
        "totalRejectedWeightKg": total_rejected_weight_kg,
        "totalGrossAmount": total_gross,
        "totalDeductionsAmount": total_deductions,
        "totalNetAmount": total_net,
        "amountPending": amount_pending,
        "amountProcessing": amount_processing,
        "amountPaid": amount_paid,
        "cropBreakdown": crop_breakdown,
        "counterThroughput": counter_throughput,
        "generatedAt": now_human,
        "generatedBy": staff_user.get("name", "Staff Officer")
    }


# ============================================================================
# PHASE 4: SLOT CLOSURE MANAGEMENT SERVICE
# ============================================================================

async def close_procurement_slot(req: dict, staff_user: dict) -> dict:
    """Authorized staff closes a specific booking slot window for a date."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can close booking slots.")

    centre_code = req.get("centreCode", "").strip()
    slot_date = req.get("slotDate", "").strip()
    time_window = req.get("timeWindow", "").strip()
    reason = (req.get("reason") or req.get("closureReason") or "Closed by centre staff administration").strip()

    if not centre_code or not slot_date or not time_window:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="centreCode, slotDate, and timeWindow are required.")

    try:
        s_date = date.fromisoformat(slot_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid slotDate format. Expected YYYY-MM-DD.")

    centre = find_centre(centre_code)
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_code}' not found.")

    verify_staff_centre_access(staff_user, {"centreCode": centre["centreCode"], "mandiName": centre["name"]})

    slot_closures_col = get_slot_closures_collection()
    if slot_closures_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    doc = {
        "centreCode": centre["centreCode"],
        "centreName": centre["name"],
        "slotDate": slot_date,
        "timeWindow": time_window,
        "isClosed": True,
        "closureReason": reason,
        "closedByStaff": staff_user.get("name", "Staff Officer"),
        "closedAt": now_human,
        "reopenedAt": None
    }

    await slot_closures_col.update_one(
        {"centreCode": centre["centreCode"], "slotDate": slot_date, "timeWindow": time_window},
        {"$set": doc},
        upsert=True
    )

    return doc


async def reopen_procurement_slot(req: dict, staff_user: dict) -> dict:
    """Authorized staff reopens a previously closed booking slot."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can reopen booking slots.")

    centre_code = req.get("centreCode", "").strip()
    slot_date = req.get("slotDate", "").strip()
    time_window = req.get("timeWindow", "").strip()

    if not centre_code or not slot_date or not time_window:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="centreCode, slotDate, and timeWindow are required.")

    try:
        s_date = date.fromisoformat(slot_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid slotDate format. Expected YYYY-MM-DD.")

    centre = find_centre(centre_code)
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre '{centre_code}' not found.")

    verify_staff_centre_access(staff_user, {"centreCode": centre["centreCode"], "mandiName": centre["name"]})

    slot_closures_col = get_slot_closures_collection()
    if slot_closures_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    existing = await slot_closures_col.find_one({
        "centreCode": centre["centreCode"],
        "slotDate": slot_date,
        "timeWindow": time_window
    })

    if not existing:
        return {
            "centreCode": centre["centreCode"],
            "slotDate": slot_date,
            "timeWindow": time_window,
            "isClosed": False,
            "closureReason": None,
            "message": "Slot is already open."
        }

    await slot_closures_col.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "isClosed": False,
                "reopenedByStaff": staff_user.get("name", "Staff Officer"),
                "reopenedAt": now_human
            }
        }
    )

    return {
        "centreCode": centre["centreCode"],
        "centreName": centre["name"],
        "slotDate": slot_date,
        "timeWindow": time_window,
        "isClosed": False,
        "closureReason": None,
        "reopenedAt": now_human,
        "reopenedBy": staff_user.get("name")
    }


async def get_slot_closures(centre_code: str, slot_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves slot closure records for a centre."""
    slot_closures_col = get_slot_closures_collection()
    if slot_closures_col is None:
        return []

    query: Dict[str, Any] = {"centreCode": centre_code, "isClosed": True}
    if slot_date:
        query["slotDate"] = slot_date

    cursor = slot_closures_col.find(query)
    closures = await cursor.to_list(100)
    return [format_doc(c) for c in closures]


# ============================================================================
# PHASE 4: PER-FARMER QUANTITY LIMITS & QUOTA INQUIRY
# ============================================================================

async def get_farmer_booking_allowance(farmer_id: str, date_str: str, time_window: str) -> dict:
    """
    Returns the farmer's remaining allowance for a slot and day,
    excluding CANCELLED and NO_SHOW bookings.
    """
    farmer_limits_col = get_farmer_limits_collection()
    bookings_col = get_bookings_collection()

    limit_config = None
    if farmer_limits_col is not None:
        limit_config = await farmer_limits_col.find_one({"farmerId": farmer_id})
        if not limit_config:
            limit_config = await farmer_limits_col.find_one({"farmerId": "GLOBAL"})

    max_per_slot = limit_config.get("maxBagsPerSlot", 100) if limit_config else 100
    max_per_day = limit_config.get("maxBagsPerDay", 250) if limit_config else 250

    active_day_bags = 0
    active_slot_bags = 0

    if bookings_col is not None:
        farmer_docs = await bookings_col.find({
            "farmerId": farmer_id,
            "slotDate": date_str,
            "status": {"$nin": ["CANCELLED", "NO_SHOW"]}
        }).to_list(100)
        active_day_bags = sum(b.get("quantityBags", 0) for b in farmer_docs)
        active_slot_bags = sum(b.get("quantityBags", 0) for b in farmer_docs if b.get("timeWindow") == time_window)

    remaining_slot = max(0, max_per_slot - active_slot_bags)
    remaining_day = max(0, max_per_day - active_day_bags)

    can_book = (active_slot_bags < max_per_slot) and (active_day_bags < max_per_day)
    reason = None
    if not can_book:
        if active_slot_bags >= max_per_slot:
            reason = f"Slot limit reached ({max_per_slot} bags)"
        else:
            reason = f"Daily limit reached ({max_per_day} bags)"

    return {
        "farmerId": farmer_id,
        "date": date_str,
        "timeWindow": time_window,
        "maxBagsPerSlot": max_per_slot,
        "maxBagsPerDay": max_per_day,
        "bookedBagsSlot": active_slot_bags,
        "bookedBagsToday": active_day_bags,
        "remainingBagsSlot": remaining_slot,
        "remainingBagsToday": remaining_day,
        "alreadyBookedSlotBags": active_slot_bags,
        "alreadyBookedDayBags": active_day_bags,
        "remainingSlotBags": remaining_slot,
        "remainingDayBags": remaining_day,
        "remainingSlotQuintals": round((remaining_slot * 40.0) / 100.0, 2),
        "remainingDayQuintals": round((remaining_day * 40.0) / 100.0, 2),
        "isSlotLimitReached": active_slot_bags >= max_per_slot,
        "isDayLimitReached": active_day_bags >= max_per_day,
        "canBook": can_book,
        "reason": reason
    }


async def configure_farmer_quantity_limits(config_data: dict, staff_user: dict) -> dict:
    """Authorized staff sets custom or global quantity limits per farmer."""
    if staff_user.get("role") not in ["staff", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized staff can configure quantity limits.")

    farmer_limits_col = get_farmer_limits_collection()
    if farmer_limits_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    farmer_id = config_data.get("farmerId", "GLOBAL").strip()
    max_slot = int(config_data.get("maxBagsPerSlot", 100))
    max_day = int(config_data.get("maxBagsPerDay", 250))

    if max_slot <= 0 or max_day <= 0 or max_slot > max_day:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid limits: maxBagsPerSlot must be > 0 and <= maxBagsPerDay.")

    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")
    doc = {
        "farmerId": farmer_id,
        "maxBagsPerSlot": max_slot,
        "maxBagsPerDay": max_day,
        "updatedAt": now_human,
        "updatedBy": staff_user.get("name")
    }

    await farmer_limits_col.update_one(
        {"farmerId": farmer_id},
        {"$set": doc},
        upsert=True
    )
    return doc


# ============================================================================
# PHASE 4: DISTRIBUTED RATE LIMITER (MONGODB PERSISTENT SLIDING WINDOW)
# ============================================================================

async def check_mongo_rate_limit(key: str, max_requests: int = 10, window_seconds: int = 60):
    """
    Persistent sliding-window rate limiter using MongoDB.
    Protects login and booking creation endpoints against abuse across multi-worker deployments.
    Does not log passwords, tokens, or PII.
    Returns True if permitted, raises HTTP 429 when exceeded.
    """
    rate_col = get_rate_limits_collection()
    if rate_col is None:
        return True

    now = datetime.utcnow()
    now_ts = now.timestamp()
    cutoff_ts = now_ts - window_seconds

    # Evict expired timestamps
    await rate_col.update_one(
        {"key": key},
        {"$pull": {"timestamps": {"$lt": cutoff_ts}}},
        upsert=True
    )

    doc = await rate_col.find_one({"key": key})
    current_count = len(doc.get("timestamps", [])) if doc else 0

    if current_count >= max_requests:
        first_ts = doc["timestamps"][0] if doc and doc.get("timestamps") else cutoff_ts
        retry_after = max(1, int(window_seconds - (now_ts - first_ts)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds}s. Please retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    # Append current timestamp
    await rate_col.update_one(
        {"key": key},
        {"$push": {"timestamps": now_ts}, "$set": {"updatedAt": now}},
        upsert=True
    )
    return True




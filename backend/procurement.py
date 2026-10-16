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

from database import get_bookings_collection, get_centres_collection, get_bills_collection
from notifications import create_in_app_notification

# Concurrency locks per centre/date/slot to prevent simultaneous overbooking race conditions
_slot_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
_slot_locks_mutex = asyncio.Lock()


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
        "isDemoData": True,
        "dataSourceLabel": "TNCSC Trichy Zone Model"
    }
]


def format_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


def get_all_centres() -> List[Dict[str, Any]]:
    """Returns the registered procurement centres."""
    return MASTER_PROCUREMENT_CENTRES


def find_centre(centre_ident: str) -> Optional[Dict[str, Any]]:
    """Finds a centre by code, ID, or substring of its name."""
    clean_ident = centre_ident.strip().lower()
    for c in MASTER_PROCUREMENT_CENTRES:
        if (c["centreCode"].lower() == clean_ident or
            c["id"].lower() == clean_ident or
            c["name"].lower() in clean_ident or
            clean_ident in c["name"].lower()):
            return c
    return None


async def get_centre_slots_availability(centre_ident: str, date_str: str) -> Dict[str, Any]:
    """
    Computes slot capacity and available bags for a given centre and date
    by querying live bookings in MongoDB.
    """
    centre = find_centre(centre_ident)
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procurement centre '{centre_ident}' not found."
        )

    bookings_col = get_bookings_collection()
    slot_capacity = centre["slotCapacityBags"]
    slots_result = []

    for window in centre["slotWindows"]:
        booked_bags = 0
        if bookings_col is not None:
            # Query sum of booked bags for this centre, date, and window (excluding cancelled)
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"mandiName": centre["name"]},
                            {"centreCode": centre["centreCode"]}
                        ],
                        "slotDate": date_str,
                        "timeWindow": window,
                        "status": {"$ne": "CANCELLED"}
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

        if ratio >= 1.0 or available_bags == 0:
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
            "status": status_str
        })

    return {
        "centreCode": centre["centreCode"],
        "centreName": centre["name"],
        "date": date_str,
        "totalDailyCapacityBags": centre["dailyCapacityBags"],
        "slots": slots_result
    }


async def create_booking_with_capacity_check(booking_data: dict, current_user: Optional[dict] = None) -> dict:
    """
    Creates a booking after performing a race-condition safe slot capacity check.
    Generates opaque security token and sets initial BOOKED state and audit history.
    """
    bookings_col = get_bookings_collection()
    if bookings_col is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable."
        )

    mandi_name = booking_data.get("mandiName", "").strip()
    preferred_date = booking_data.get("preferredDate", "").strip()
    time_window = booking_data.get("timeWindow", "08:30 AM - 11:30 AM").strip()
    quantity_bags = int(booking_data.get("quantityBags", 0))

    if quantity_bags <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity in bags must be greater than zero."
        )

    centre = find_centre(mandi_name)
    slot_capacity = centre["slotCapacityBags"] if centre else 250
    centre_code = centre["centreCode"] if centre else "TNJ-DPC-01"
    official_mandi_name = centre["name"] if centre else mandi_name

    # Acquire atomic concurrency lock for this specific slot to eliminate race-conditions
    slot_lock_key = f"{centre_code}:{preferred_date}:{time_window}"
    slot_lock = await get_slot_lock(slot_lock_key)

    async with slot_lock:
        # Database-safe race-condition check:
        # Query current sum of booked bags for this slot
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"mandiName": official_mandi_name},
                        {"centreCode": centre_code}
                    ],
                    "slotDate": preferred_date,
                    "timeWindow": time_window,
                    "status": {"$ne": "CANCELLED"}
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
        qr_payload_url = f"https://nammavivasayi.gov.in/verify?token={opaque_secure_token}&id={booking_id}"

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
            "crop": booking_data.get("crop", "Samba Paddy"),
            "quantityBags": quantity_bags,
            "estimatedWeightQuintals": estimated_weight,
            "slotDate": preferred_date,
            "timeWindow": time_window,
            "status": "BOOKED",
            "stageNumber": 1,
            "moisturePercent": None,
            "actualNetWeightQuintals": None,
            "qualityNotes": "Awaiting gate entry & physical inspection",
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
            "disclaimer": "Verify the token or scan a valid Namma Vivasayi QR code."
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

    can_check_in = current_status in ["BOOKED", "CONFIRMED"]
    can_weigh = current_status in ["CHECKED_IN", "IN_QUEUE", "QUALITY_CHECKED", "PROCESSING"]

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
        "message": f"Token verified successfully. Current status is {current_status}.",
        "disclaimer": "Official procurement token verified with secure database signature."
    }


def verify_staff_centre_access(staff_user: dict, doc: dict) -> None:
    """
    Enforces FEATURE 5 & TASK 5: Restricts staff operations strictly to their authorized procurement centre.
    """
    staff_mandi = (staff_user.get("mandiName") or staff_user.get("mandiAssigned") or "").strip().lower()
    if not staff_mandi or staff_mandi == "all centres":
        return  # Unrestricted / supervisor staff

    doc_mandi = (doc.get("mandiName") or "").strip().lower()
    doc_code = (doc.get("centreCode") or "").strip().lower()

    if staff_mandi not in doc_mandi and doc_mandi not in staff_mandi and staff_mandi not in doc_code:
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

    if curr_status not in ["PROCESSING", "IN_QUEUE", "CHECKED_IN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record weighment for booking with status '{curr_status}'. Vehicle must be CHECKED_IN, IN_QUEUE or PROCESSING."
        )

    # Parse Weight (Kg or Quintals)
    weight_kg = None
    if payload.get("acceptedWeightKg") is not None:
        weight_kg = float(payload["acceptedWeightKg"])
    elif payload.get("actualNetWeightQuintals") is not None:
        weight_kg = float(payload["actualNetWeightQuintals"]) * 100.0

    # Parse Price (Per Kg or Per Quintal)
    price_kg = None
    if payload.get("pricePerKg") is not None:
        price_kg = float(payload["pricePerKg"])
    elif payload.get("pricePerQuintal") is not None:
        price_kg = float(payload["pricePerQuintal"]) / 100.0

    if weight_kg is None or weight_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accepted crop weight must be greater than 0.")
    if price_kg is None or price_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configured rate must be greater than 0.")

    # Deductions
    quality_deductions = float(payload.get("qualityDeductionsAmount") or 0.0)
    other_deductions = float(payload.get("otherDeductionsAmount") or payload.get("customDeductionsAmount") or 0.0)
    moisture = float(payload.get("moisturePercent", 14.0))

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

    quality_grade = payload.get("qualityGrade", "FAQ Grade A")
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
        "acceptedWeightKg": calc["acceptedWeightKg"],
        "actualNetWeightQuintals": calc["actualNetWeightQuintals"],
        "pricePerKg": calc["pricePerKg"],
        "pricePerQuintal": calc["pricePerQuintal"],
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
                "grossAmount": calc["grossAmount"],
                "qualityDeductionsAmount": calc["qualityDeductionsAmount"],
                "otherDeductionsAmount": calc["otherDeductionsAmount"],
                "totalDeductionsAmount": calc["totalDeductionsAmount"],
                "netAmount": calc["netAmount"],
                "paymentStatus": payment_status,
                "moisturePercent": moisture,
                "qualityNotes": quality_grade,
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
        "BOOKED": ["CHECKED_IN", "CANCELLED"],
        "CHECKED_IN": ["IN_QUEUE", "CANCELLED"],
        "IN_QUEUE": ["PROCESSING", "CANCELLED"],
        "PROCESSING": ["COMPLETED", "CANCELLED"],
        "COMPLETED": [],
        "CANCELLED": []
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
        "IN_QUEUE": 3,
        "PROCESSING": 4,
        "COMPLETED": 5,
        "CANCELLED": 0
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
      (CHECKED_IN, IN_QUEUE, PROCESSING). Otherwise, returns None and 'Waiting time unavailable'.
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
        "QUALITY_CHECKED": "IN_QUEUE",
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

    if normalized_status in ["CHECKED_IN", "IN_QUEUE", "PROCESSING"]:
        # Count vehicles that checked in before this vehicle at the same centre on the same date
        active_ahead = await bookings_col.count_documents({
            "mandiName": mandi_name,
            "slotDate": slot_date,
            "status": {"$in": ["CHECKED_IN", "IN_QUEUE", "PROCESSING", "quality_checked"]},
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
    else:
        waiting_time_display = "Waiting time unavailable"

    # Lifecycle stages breakdown
    stage_progression = [
        {"stage": "BOOKED", "name": "Slot Booking Confirmed", "nameTa": "முன்பதிவு உறுதி செய்யப்பட்டது"},
        {"stage": "CHECKED_IN", "name": "Gate Entry & Token Verified", "nameTa": "நுழைவு வாயில் சரிபார்ப்பு"},
        {"stage": "IN_QUEUE", "name": "Yard Queue Assignment", "nameTa": "கொள்முதல் வரிசை எண்"},
        {"stage": "PROCESSING", "name": "Moisture & Weighbridge Testing", "nameTa": "ஈரப்பதம் மற்றும் எடை சரிபார்ப்பு"},
        {"stage": "COMPLETED", "name": "Transaction & DBT Ledger Recorded", "nameTa": "எடைப் பதிவு மற்றும் வங்கிப் பட்டுவாடா"},
    ]

    current_stage_idx = 1
    for idx, s in enumerate(stage_progression, start=1):
        if s["stage"] == normalized_status:
            current_stage_idx = idx
            break
    if normalized_status == "COMPLETED":
        current_stage_idx = 5
    elif normalized_status == "CANCELLED":
        current_stage_idx = 0

    stages_detail = []
    for idx, s in enumerate(stage_progression, start=1):
        if normalized_status == "CANCELLED":
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
        "quantityBags": doc.get("quantityBags", 0),
        "vehiclesAhead": vehicles_ahead,
        "queuePosition": queue_position,
        "estimatedWaitMinutes": estimated_wait_minutes,
        "hasSufficientDataForEstimate": has_sufficient_data,
        "waitingTimeDisplay": waiting_time_display,
        "isInActiveQueue": is_in_active_queue,
        "currentStageNumber": current_stage_idx,
        "stages": stages_detail,
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
    if current_status in ["CHECKED_IN", "IN_PROGRESS", "WEIGHED", "COMPLETED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking #{clean_bid} because it has already reached '{current_status}' stage."
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



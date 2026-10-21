"""
FARMER DIRECT MARKETPLACE SERVICE (FEATURE 7)
==============================================
Enables direct farmer-to-customer produce discovery, direct peer-to-peer inquiry,
and self-service inventory management for registered Tamil Nadu farmers.

Key Rules:
- Direct buyer contact via WhatsApp & phone (no commission, no escrow fees).
- Strict ownership isolation: Farmers can only edit/delete their own listings.
- Verified farmer identity bound to authenticated user profile.
- Admin moderation controls to flag and deactivate suspicious/spam listings.
"""

import logging
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Dict, Any, Optional

from database import get_farmer_marketplace_collection, get_farmer_marketplace_orders_collection

logger = logging.getLogger("marketplace_service")


def generate_listing_id(district: str) -> str:
    """Generates unique listing identifier (e.g. MKT-TNJ-2026-A1B2)."""
    dist_code = "".join([c for c in district.upper() if c.isalnum()])[:3] or "GEN"
    year = datetime.now().year
    rand_suffix = uuid.uuid4().hex[:4].upper()
    return f"MKT-{dist_code}-{year}-{rand_suffix}"


async def check_and_expire_listings() -> int:
    """Checks for active listings where availableUntil date has passed and marks them expired."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return 0
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res = await col.update_many(
        {
            "listingStatus": "active",
            "availableUntil": {"$exists": True, "$ne": None, "$lt": today_iso}
        },
        {
            "$set": {
                "listingStatus": "expired",
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    if res.modified_count > 0:
        logger.info(f"Auto-expired {res.modified_count} marketplace listings past availableUntil {today_iso}")
    return res.modified_count


async def create_produce_listing(farmer_user: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new direct produce listing linked to the authenticated farmer.
    Explicit consent (showContactToBuyers) is required to expose direct phone numbers.
    """
    col = get_farmer_marketplace_collection()
    if col is None:
        raise RuntimeError("Database service unavailable.")

    now_iso = datetime.now(timezone.utc).isoformat()
    listing_id = generate_listing_id(data.get("district", farmer_user.get("district", "TN")))

    doc = {
        "listingId": listing_id,
        "farmerId": farmer_user.get("id", farmer_user.get("userId", "UNKNOWN")),
        "farmerName": farmer_user.get("name", "Registered Farmer"),
        "farmerPhone": farmer_user.get("phone", ""),
        "crop": data["crop"].strip(),
        "variety": (data.get("variety") or "").strip() or None,
        "category": data.get("category", "Cereals"),
        "district": data.get("district") or farmer_user.get("district") or "Thanjavur",
        "village": data.get("village") or farmer_user.get("village") or None,
        "quantity": float(data["quantity"]),
        "unit": data.get("unit", "Quintal"),
        "pricePerUnit": float(data["pricePerUnit"]),
        "isOrganicCertified": bool(data.get("isOrganicCertified", False)),
        "certificationBody": data.get("certificationBody"),
        "harvestDate": data.get("harvestDate"),
        "availableUntil": data.get("availableUntil"),
        "fulfillmentModes": data.get("fulfillmentModes", ["Farm Gate Pickup"]),
        "serviceArea": data.get("serviceArea"),
        "photoUrls": data.get("photoUrls") or [],
        "showContactToBuyers": bool(data.get("showContactToBuyers", False)),
        "description": data.get("description"),
        "listingStatus": "active",
        "viewCount": 0,
        "inquiryCount": 0,
        "reportCount": 0,
        "adminFlagged": False,
        "flagReason": None,
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    await col.insert_one(doc)
    doc.pop("_id", None)
    logger.info(f"Created direct marketplace listing {listing_id} for farmer {farmer_user.get('name')}")
    return doc


async def get_marketplace_listings(
    district: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    organic_only: bool = False,
    page: int = 1,
    limit: int = 12
) -> Dict[str, Any]:
    """
    Returns public active marketplace listings with search and filter support.
    Masks farmer contact unless explicit consent (showContactToBuyers) was granted.
    """
    col = get_farmer_marketplace_collection()
    if col is None:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "totalPages": 1,
            "categories": [],
            "districts": []
        }

    # Automatically mark past listings as expired
    await check_and_expire_listings()

    query: Dict[str, Any] = {
        "listingStatus": "active",
        "adminFlagged": False
    }

    if district and district.lower() not in ["all", ""]:
        query["district"] = {"$regex": f"^{district.strip()}$", "$options": "i"}

    if category and category.lower() not in ["all", ""]:
        query["category"] = {"$regex": f"^{category.strip()}$", "$options": "i"}

    if organic_only:
        query["isOrganicCertified"] = True

    if search and search.strip():
        q = search.strip()
        query["$or"] = [
            {"crop": {"$regex": q, "$options": "i"}},
            {"variety": {"$regex": q, "$options": "i"}},
            {"village": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]

    total = await col.count_documents(query)
    total_pages = max(1, (total + limit - 1) // limit)
    skip = (page - 1) * limit

    cursor = col.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)

    # Privacy Protection: mask farmer contact unless explicit consent provided
    sanitized_items = []
    for item in items:
        item_copy = dict(item)
        if not item_copy.get("showContactToBuyers", False):
            item_copy["farmerPhone"] = "Protected (Use In-App Enquiry)"
        sanitized_items.append(item_copy)

    # Dynamic filter options
    districts = await col.distinct("district", {"listingStatus": "active", "adminFlagged": False})
    categories = await col.distinct("category", {"listingStatus": "active", "adminFlagged": False})

    return {
        "items": sanitized_items,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
        "categories": ["All"] + sorted([c for c in categories if c]),
        "districts": ["All"] + sorted([d for d in districts if d])
    }


async def get_farmer_my_listings(farmer_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns all listings belonging to the authenticated farmer."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return []

    farmer_id = farmer_user.get("id") or farmer_user.get("userId")
    cursor = col.find({"farmerId": farmer_id}, {"_id": 0}).sort("createdAt", -1)
    return await cursor.to_list(length=100)


async def get_listing_by_id(listing_id: str, record_view: bool = False, viewer_user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a listing, sanitizes phone if consent missing and viewer is not the owner."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return None

    if record_view:
        doc = await col.find_one_and_update(
            {"listingId": listing_id},
            {"$inc": {"viewCount": 1}},
            projection={"_id": 0}
        )
    else:
        doc = await col.find_one({"listingId": listing_id}, {"_id": 0})

    if doc and not doc.get("showContactToBuyers", False) and doc.get("farmerId") != viewer_user_id:
        doc["farmerPhone"] = "Protected (Use In-App Enquiry)"

    return doc


async def record_buyer_inquiry(listing_id: str) -> bool:
    """Increments buyer inquiry count when WhatsApp/Call action is clicked."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return False
    res = await col.update_one({"listingId": listing_id}, {"$inc": {"inquiryCount": 1}})
    return res.modified_count > 0


async def update_farmer_listing(
    farmer_user: Dict[str, Any],
    listing_id: str,
    update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Updates a listing with strict farmer ownership verification.
    """
    col = get_farmer_marketplace_collection()
    if col is None:
        return None

    farmer_id = farmer_user.get("id") or farmer_user.get("userId")
    is_admin = farmer_user.get("role") in ["admin", "staff"]

    existing = await col.find_one({"listingId": listing_id})
    if not existing:
        return None

    # Strict ownership check
    if not is_admin and existing.get("farmerId") != farmer_id:
        raise PermissionError("Access denied: You can only edit your own produce listings.")

    clean_updates = {k: v for k, v in update_data.items() if v is not None}
    clean_updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    updated = await col.find_one_and_update(
        {"listingId": listing_id},
        {"$set": clean_updates},
        projection={"_id": 0},
        return_document=True
    )
    return updated


async def delete_farmer_listing(farmer_user: Dict[str, Any], listing_id: str) -> bool:
    """Soft-deletes or removes a listing owned by the farmer."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return False

    farmer_id = farmer_user.get("id") or farmer_user.get("userId")
    is_admin = farmer_user.get("role") in ["admin", "staff"]

    existing = await col.find_one({"listingId": listing_id})
    if not existing:
        return False

    if not is_admin and existing.get("farmerId") != farmer_id:
        raise PermissionError("Access denied: You can only delete your own produce listings.")

    res = await col.delete_one({"listingId": listing_id})
    return res.deleted_count > 0


async def moderate_listing_admin(listing_id: str, admin_flagged: bool, reason: Optional[str] = None) -> bool:
    """Admin function: flags or in-activates inappropriate or deceptive listings."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return False

    update = {
        "adminFlagged": admin_flagged,
        "flagReason": reason if admin_flagged else None,
        "listingStatus": "flagged" if admin_flagged else "active",
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    res = await col.update_one({"listingId": listing_id}, {"$set": update})
    return res.modified_count > 0


async def report_marketplace_listing(listing_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submits a community flag/report against a listing for spam, fake price, or expired produce.
    Automatically flags the listing when reportCount reaches 3 or more.
    """
    col = get_farmer_marketplace_collection()
    if col is None:
        raise RuntimeError("Database unavailable.")

    existing = await col.find_one({"listingId": listing_id})
    if not existing:
        raise ValueError(f"Listing '{listing_id}' not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    current_reports = int(existing.get("reportCount", 0)) + 1
    reason = report_data.get("reasonCategory", "spam")

    updates: Dict[str, Any] = {
        "reportCount": current_reports,
        "updatedAt": now_iso
    }

    # Community threshold: Auto-flag listing on 3+ reports to prevent deceptive listings
    if current_reports >= 3:
        updates["adminFlagged"] = True
        updates["listingStatus"] = "flagged"
        updates["flagReason"] = f"Community reported for {reason} ({current_reports} reports)."

    await col.update_one({"listingId": listing_id}, {"$set": updates})
    logger.info(f"Listing {listing_id} reported ({reason}). Total reports: {current_reports}. Auto-flagged: {current_reports >= 3}")

    return {
        "listingId": listing_id,
        "reportCount": current_reports,
        "flagged": current_reports >= 3,
        "message": "Report recorded. Thank you for keeping the farmer marketplace safe and transparent."
    }


async def seed_demo_marketplace_listings() -> int:
    """Seeds initial demonstration marketplace listings for evaluation."""
    col = get_farmer_marketplace_collection()
    if col is None:
        return 0

    count = await col.count_documents({})
    if count > 0:
        return count

    demo_listings = [
        {
            "listingId": "MKT-TNJ-2026-DEMO1",
            "farmerId": "TN-AGRI-2026-4487",
            "farmerName": "Murugesan K.",
            "farmerPhone": "9876543299",
            "crop": "Mappillai Samba Heritage Paddy",
            "variety": "Traditional Red Rice (Hand-Pounded Grade)",
            "category": "Cereals",
            "district": "Thanjavur",
            "village": "Pillaiyarpatti",
            "quantity": 30.0,
            "unit": "Bags (50kg)",
            "pricePerUnit": 2400.0,
            "isOrganicCertified": True,
            "certificationBody": "TNOCD - Scope Cert #TNOCD-2025-081",
            "harvestDate": "2026-10-12",
            "availableUntil": "2026-11-30",
            "fulfillmentModes": ["Farm Gate Pickup", "Buyer Transport"],
            "description": "Authentic, nutrient-dense heritage rice grown using Panchagavya and organic compost. Stored dry.",
            "listingStatus": "active",
            "viewCount": 28,
            "inquiryCount": 4,
            "adminFlagged": False,
            "flagReason": None,
            "isDemoData": True,
            "createdAt": "2026-10-15T09:00:00Z",
            "updatedAt": "2026-10-15T09:00:00Z"
        },
        {
            "listingId": "MKT-SLM-2026-DEMO2",
            "farmerId": "TN-AGRI-2026-8819",
            "farmerName": "Selvakumar P.",
            "farmerPhone": "9842188776",
            "crop": "Organic Salem Turmeric",
            "variety": "Finger Turmeric (Curcumin >4.5%)",
            "category": "Spices",
            "district": "Salem",
            "village": "Attur",
            "quantity": 15.0,
            "unit": "Quintal",
            "pricePerUnit": 14500.0,
            "isOrganicCertified": True,
            "certificationBody": "TNOCD In-Conversion Year 2",
            "harvestDate": "2026-10-05",
            "availableUntil": "2026-12-15",
            "fulfillmentModes": ["Farm Gate Pickup", "Local Delivery within District"],
            "description": "Unpolished finger turmeric cured in hygienic solar boilers. High curcumin suitable for pharmaceuticals and food use.",
            "listingStatus": "active",
            "viewCount": 45,
            "inquiryCount": 8,
            "adminFlagged": False,
            "flagReason": None,
            "isDemoData": True,
            "createdAt": "2026-10-16T11:20:00Z",
            "updatedAt": "2026-10-16T11:20:00Z"
        },
        {
            "listingId": "MKT-CBE-2026-DEMO3",
            "farmerId": "TN-AGRI-2026-5532",
            "farmerName": "Vellingiri R.",
            "farmerPhone": "9842512390",
            "crop": "Marachekku Virgin Coconut Oil",
            "variety": "Cold-Pressed Raw (Wood Pressed)",
            "category": "Value Added",
            "district": "Coimbatore",
            "village": "Pollachi",
            "quantity": 200.0,
            "unit": "Litres",
            "pricePerUnit": 320.0,
            "isOrganicCertified": False,
            "certificationBody": None,
            "harvestDate": "2026-10-18",
            "availableUntil": "2026-12-31",
            "fulfillmentModes": ["Farm Gate Pickup", "Courier Available"],
            "description": "Pure wood-pressed coconut oil extracted at slow speeds without sulphur or chemical additives. Food-grade glass packaging.",
            "listingStatus": "active",
            "viewCount": 62,
            "inquiryCount": 11,
            "adminFlagged": False,
            "flagReason": None,
            "isDemoData": True,
            "createdAt": "2026-10-18T14:00:00Z",
            "updatedAt": "2026-10-18T14:00:00Z"
        }
    ]

    for item in demo_listings:
        await col.update_one(
            {"listingId": item["listingId"]},
            {"$set": item},
            upsert=True
        )

    logger.info(f"Seeded {len(demo_listings)} demonstration marketplace listings.")
    return len(demo_listings)


def generate_order_id() -> str:
    year = datetime.now().year
    suffix = uuid.uuid4().hex[:5].upper()
    return f"ORD-{year}-{suffix}"


async def create_listing_order_request(listing_id: str, buyer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new buyer inquiry / order request on a produce listing.
    Protects against spam by restricting rapid-fire submissions from the same contact number.
    """
    col_listings = get_farmer_marketplace_collection()
    col_orders = get_farmer_marketplace_orders_collection()
    if col_listings is None or col_orders is None:
        raise RuntimeError("Database unavailable.")

    listing = await col_listings.find_one({"listingId": listing_id})
    if not listing:
        raise ValueError(f"Listing '{listing_id}' not found.")

    if listing.get("listingStatus") not in ["active", "sold_out"]:
        raise ValueError(f"Listing is currently {listing.get('listingStatus')} and not accepting new order requests.")

    buyer_phone = buyer_data["buyerPhone"].strip()

    # Anti-spam protection: maximum 5 order requests per phone number within last 10 minutes
    ten_mins_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    recent_buyer_orders = await col_orders.count_documents({
        "buyerPhone": buyer_phone,
        "createdAt": {"$gte": ten_mins_ago}
    })
    if recent_buyer_orders >= 5:
        raise ValueError("Spam protection: Too many requests submitted in a short period. Please try again after 10 minutes.")

    qty = float(buyer_data["requestedQuantity"])
    unit_price = float(listing.get("pricePerUnit", 0.0))
    total_est = round(qty * unit_price, 2)
    order_id = generate_order_id()
    now_iso = datetime.now(timezone.utc).isoformat()

    order_doc = {
        "orderId": order_id,
        "listingId": listing_id,
        "farmerId": listing.get("farmerId"),
        "crop": listing.get("crop"),
        "unit": listing.get("unit"),
        "pricePerUnit": unit_price,
        "totalEstimatedPrice": total_est,
        "buyerName": buyer_data["buyerName"].strip(),
        "buyerPhone": buyer_phone,
        "requestedQuantity": qty,
        "fulfillmentPreference": buyer_data.get("fulfillmentPreference", "Farm Gate Pickup"),
        "deliveryAddress": buyer_data.get("deliveryAddress"),
        "message": buyer_data.get("message"),
        "status": "pending",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    await col_orders.insert_one(order_doc)
    order_doc.pop("_id", None)

    # Increment inquiry counter on listing
    await col_listings.update_one({"listingId": listing_id}, {"$inc": {"inquiryCount": 1}})
    logger.info(f"Recorded order request {order_id} on listing {listing_id} by {buyer_data.get('buyerName')}")
    return order_doc


async def get_farmer_listing_orders(farmer_user: Dict[str, Any], listing_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns order requests received by the authenticated farmer."""
    col_orders = get_farmer_marketplace_orders_collection()
    if col_orders is None:
        return []

    farmer_id = farmer_user.get("id") or farmer_user.get("userId")
    query: Dict[str, Any] = {"farmerId": farmer_id}
    if listing_id:
        query["listingId"] = listing_id

    cursor = col_orders.find(query, {"_id": 0}).sort("createdAt", -1)
    return await cursor.to_list(length=100)


async def update_order_request_status(
    farmer_user: Dict[str, Any],
    order_id: str,
    new_status: str
) -> Optional[Dict[str, Any]]:
    """
    Updates order status (confirmed, rejected, completed) with ownership verification.
    When an order is confirmed, the listing's available quantity is decremented.
    If stock is exhausted, the listing is automatically transitioned to 'out_of_stock'.
    """
    col_orders = get_farmer_marketplace_orders_collection()
    col_listings = get_farmer_marketplace_collection()
    if col_orders is None:
        return None

    farmer_id = farmer_user.get("id") or farmer_user.get("userId")
    is_admin = farmer_user.get("role") in ["admin", "staff"]

    existing = await col_orders.find_one({"orderId": order_id})
    if not existing:
        return None

    if not is_admin and existing.get("farmerId") != farmer_id:
        raise PermissionError("Access denied: You can only update orders for your own produce.")

    old_status = existing.get("status")
    now_iso = datetime.now(timezone.utc).isoformat()

    updated = await col_orders.find_one_and_update(
        {"orderId": order_id},
        {"$set": {"status": new_status, "updatedAt": now_iso}},
        projection={"_id": 0},
        return_document=True
    )

    # When transitioning to confirmed for the first time, decrement listing inventory
    if new_status == "confirmed" and old_status != "confirmed" and col_listings is not None:
        listing_id = existing.get("listingId")
        requested_qty = float(existing.get("requestedQuantity", 0.0))
        listing = await col_listings.find_one({"listingId": listing_id})
        if listing:
            current_qty = float(listing.get("quantity", 0.0))
            new_qty = max(0.0, round(current_qty - requested_qty, 2))
            listing_updates: Dict[str, Any] = {
                "quantity": new_qty,
                "updatedAt": now_iso
            }
            if new_qty <= 0.0:
                listing_updates["listingStatus"] = "out_of_stock"
            await col_listings.update_one({"listingId": listing_id}, {"$set": listing_updates})
            logger.info(f"Updated listing {listing_id} inventory: {current_qty} -> {new_qty} (Status: {listing_updates.get('listingStatus', listing.get('listingStatus'))})")

    return updated


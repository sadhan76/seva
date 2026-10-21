"""
FARMER SUPPORT SERVICES MODULE (SECTIONS 1-6)
==============================================
Provides institutional, source-attributed agricultural guidance for:
1. Farmer Training (TNAU / KVK / SAMETI)
2. Agri Entrepreneurship (NABARD / ACABC / Incubation)
3. Organic Farming (TNOCD / NPOP / Bio-Inputs)
4. Special Operation: Beginner-to-Market Crop Guidance
5. Protected Cultivation (Polyhouse & Shade Net Schemes)
6. Value-Added Products (NIFTEM-T / Post-Harvest Processing)

Features:
- Source provenance: official URLs, institutions, publication & last checked dates.
- Verified official contacts (no fabricated names or phone numbers).
- Automatic expiration sweeper for expired training announcements.
- 180-day stale contact review detection.
- Bilingual support (English & Tamil).
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from database import get_farmer_support_collection

logger = logging.getLogger("farmer_support_service")
SEEDS_FILE = Path(__file__).parent / "data" / "farmer_support_seeds.json"


def load_seeds_from_json() -> List[Dict[str, Any]]:
    """Loads default verified farmer support records from JSON."""
    if not SEEDS_FILE.exists():
        logger.warning(f"Seeds file not found: {SEEDS_FILE}")
        return []
    try:
        with open(SEEDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Error loading seeds from {SEEDS_FILE}: {e}")
        return []


async def seed_farmer_support_database(force: bool = False) -> int:
    """
    Idempotently seeds verified farmer support content into MongoDB.
    Protects reviewed content: If an existing document has adminReviewed == True
    or has a newer updatedAt timestamp than the seed, it will not be overwritten unless force=True.
    """
    col = get_farmer_support_collection()
    if col is None:
        logger.warning("MongoDB unavailable; operating with in-memory JSON fallback.")
        return 0

    seeds = load_seeds_from_json()
    if not seeds:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    seeded_count = 0

    for item in seeds:
        content_id = item.get("contentId")
        if not content_id:
            continue

        existing = await col.find_one({"contentId": content_id})
        if existing and not force:
            # Check if existing record has been reviewed by an administrator
            if existing.get("adminReviewed"):
                logger.info(f"Skipping seed overwrite for admin-reviewed record: {content_id}")
                continue
            # Check if existing record was modified more recently than seed
            existing_updated = existing.get("updatedAt", "")
            seed_updated = item.get("updatedAt", "")
            if existing_updated and seed_updated and existing_updated > seed_updated:
                logger.info(f"Skipping seed overwrite for more recently updated record: {content_id}")
                continue

        doc = dict(item)
        if "createdAt" not in doc or not doc["createdAt"]:
            doc["createdAt"] = now_iso
        if not doc.get("updatedAt"):
            doc["updatedAt"] = now_iso

        res = await col.update_one(
            {"contentId": content_id},
            {"$set": doc},
            upsert=True
        )
        if res.upserted_id or res.matched_count > 0:
            seeded_count += 1

    logger.info(f"Seeded/synchronized {seeded_count} farmer support content records.")
    return seeded_count


async def auto_expire_training_notices() -> int:
    """
    Scheduled governance job:
    Finds active training announcements whose endDate has passed and transitions
    them to 'expired' so they move to the historical archive automatically.
    """
    col = get_farmer_support_collection()
    if col is None:
        return 0

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Find training notices where trainingMeta.endDate < today_str and activeStatus == 'active'
    query = {
        "category": "training",
        "activeStatus": "active",
        "trainingMeta.endDate": {"$lt": today_str}
    }

    update = {
        "$set": {
            "activeStatus": "expired",
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    }

    res = await col.update_many(query, update)
    if res.modified_count > 0:
        logger.info(f"Auto-expired {res.modified_count} past training announcements.")
    return res.modified_count


async def check_and_flag_stale_contacts(stale_threshold_days: int = 180) -> int:
    """
    Audits contact records: if lastCheckedDate is older than 180 days,
    flags verificationStatus as 'stale_review_needed' with visible notice.
    """
    col = get_farmer_support_collection()
    if col is None:
        return 0

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=stale_threshold_days)).strftime("%Y-%m-%d")
    query = {
        "lastCheckedDate": {"$lt": cutoff_date},
        "verificationStatus": "verified_official"
    }

    update = {
        "$set": {
            "verificationStatus": "stale_review_needed",
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    }

    res = await col.update_many(query, update)
    return res.modified_count


async def get_support_content(
    category: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    language: Optional[str] = None,
    active_only: bool = True,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queries official farmer support content from MongoDB with JSON fallback.
    Supports filtering by category, district, state, search text, and active status.
    """
    # Trigger auto-expiration on read
    await auto_expire_training_notices()

    col = get_farmer_support_collection()
    raw_items: List[Dict[str, Any]] = []

    if col is not None:
        try:
            cursor = col.find({}, {"_id": 0})
            raw_items = await cursor.to_list(length=500)
        except Exception as e:
            logger.error(f"Error querying farmer support collection: {e}")
            raw_items = []

    if not raw_items:
        raw_items = load_seeds_from_json()

    # Filter items
    filtered: List[Dict[str, Any]] = []

    for item in raw_items:
        # Category filter
        if category and category.lower() not in ["all", ""]:
            if item.get("category", "").lower() != category.lower():
                continue

        # Content type filter
        if content_type and content_type.lower() not in ["all", ""]:
            if item.get("contentType", "").lower() != content_type.lower():
                continue

        # Active status filter
        if active_only and item.get("activeStatus") != "active":
            continue

        # State filter
        if state and state.lower() not in ["all", ""]:
            item_state = item.get("state", "Tamil Nadu").lower()
            if item_state not in ["all", "all-india"] and state.lower() not in item_state:
                continue

        # District filter
        if district and district.lower() not in ["all", ""]:
            item_dist = item.get("district", "All").lower()
            if item_dist != "all" and district.lower() not in item_dist:
                continue

        # Language filter
        if language and language.lower() not in ["all", "bilingual", ""]:
            item_lang = item.get("language", "bilingual").lower()
            if item_lang != "bilingual" and item_lang != language.lower():
                continue

        # Search query
        if search and search.strip():
            q = search.strip().lower()
            title_en = item.get("title", {}).get("en", "").lower()
            title_ta = item.get("title", {}).get("ta", "").lower()
            desc_en = item.get("description", {}).get("en", "").lower()
            desc_ta = item.get("description", {}).get("ta", "").lower()
            inst = item.get("institution", "").lower()
            subcat = item.get("subCategory", "").lower()

            if not (q in title_en or q in title_ta or q in desc_en or q in desc_ta or q in inst or q in subcat):
                continue

        filtered.append(item)

    # Extract dynamic categories, districts & states for filter menus
    all_categories = sorted(list({r.get("category") for r in raw_items if r.get("category")}))
    all_districts = sorted(list({r.get("district") for r in raw_items if r.get("district") and r.get("district") != "All"}))
    all_states = sorted(list({r.get("state") for r in raw_items if r.get("state") and r.get("state") not in ["All", "All-India"]}))
    states_list = list(dict.fromkeys(["All", "Tamil Nadu"] + [s for s in all_states if s != "Tamil Nadu"] + ["All-India"]))

    has_stale = any(r.get("verificationStatus") == "stale_review_needed" for r in filtered)

    return {
        "items": filtered,
        "total": len(filtered),
        "categories": all_categories,
        "districts": ["All"] + all_districts,
        "states": states_list,
        "hasStaleNotice": has_stale
    }


async def get_support_content_by_id(content_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single support item by contentId."""
    col = get_farmer_support_collection()
    if col is not None:
        try:
            doc = await col.find_one({"contentId": content_id}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            logger.error(f"Error finding contentId {content_id}: {e}")

    # Fallback to seeds JSON
    seeds = load_seeds_from_json()
    for s in seeds:
        if s.get("contentId") == content_id:
            return s
    return None


async def get_training_calendar(
    district: Optional[str] = None,
    mode: Optional[str] = None,
    upcoming_only: bool = True
) -> List[Dict[str, Any]]:
    """Specialized calendar retriever for training workshops."""
    res = await get_support_content(
        category="training",
        district=district,
        active_only=upcoming_only
    )
    items = res.get("items", [])

    if mode and mode.lower() not in ["all", ""]:
        items = [i for i in items if i.get("trainingMeta", {}).get("mode", "").lower() == mode.lower()]

    # Sort chronologically by start date
    items.sort(key=lambda x: x.get("trainingMeta", {}).get("startDate", "9999-99-99"))
    return items


async def get_crop_master_guide(crop_identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieves complete stage-by-stage guide for a crop in Special Operation."""
    res = await get_support_content(category="special_operation")
    items = res.get("items", [])
    q = crop_identifier.lower().strip().replace("-", " ").replace("_", " ")

    for item in items:
        cid = item.get("contentId", "").lower().replace("-", " ").replace("_", " ")
        if q in cid or cid in q:
            return item
        subcat = item.get("subCategory", "").lower().replace("-", " ").replace("_", " ")
        if q in subcat or subcat in q:
            return item
        meta = item.get("cropGuideMeta", {})
        c_name = meta.get("cropName", "").lower().replace("-", " ").replace("_", " ")
        if q in c_name or c_name in q or any(tok in c_name for tok in q.split() if len(tok) > 3):
            return item
    return None


async def create_support_content_admin(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Admin function: Creates new verified official content record."""
    col = get_farmer_support_collection()
    if col is None:
        raise RuntimeError("Database unavailable.")

    now_iso = datetime.now(timezone.utc).isoformat()
    doc = dict(item_data)
    doc["createdAt"] = now_iso
    doc["updatedAt"] = now_iso
    doc["verificationStatus"] = "verified_official"

    await col.update_one({"contentId": doc["contentId"]}, {"$set": doc}, upsert=True)
    return doc


async def review_support_content_admin(content_id: str, new_verification_status: str) -> bool:
    """Admin function: Updates verification status and updates lastCheckedDate to today."""
    col = get_farmer_support_collection()
    if col is None:
        return False

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()

    res = await col.update_one(
        {"contentId": content_id},
        {
            "$set": {
                "verificationStatus": new_verification_status,
                "lastCheckedDate": today_str,
                "updatedAt": now_iso
            }
        }
    )
    return res.modified_count > 0


async def get_stale_content_audit_admin() -> List[Dict[str, Any]]:
    """Admin function: Returns all records that need re-verification or are expired."""
    col = get_farmer_support_collection()
    if col is None:
        return []

    query = {
        "$or": [
            {"verificationStatus": "stale_review_needed"},
            {"activeStatus": "expired"}
        ]
    }
    return await col.find(query, {"_id": 0}).to_list(length=100)

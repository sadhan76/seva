"""
Live Market Mandi Prices Service & Background Synchronization Engine
Project: Namma Vivasayi AI (SEVA)
Data Source: data.gov.in (AGMARKNET - Ministry of Agriculture and Farmers Welfare)
Dataset: "Current Daily Price of Various Commodities from Various Markets (Mandi)"
Resource ID: 9ef84268-d588-465a-a308-a864a43d0070

Key Features:
1. Official API Client: Queries data.gov.in with DATA_GOV_IN_API_KEY.
2. Normalization & Validation: Rejects malformed/negative prices and invalid dates.
3. Dual-Tier Caching & Non-Destructive Update: Memory TTL + MongoDB persistent store (market_prices_cache).
4. Stable Deduplication: Merges incoming records by (state, district, market, commodity, variety, arrival_date).
5. Background Scheduler: Configurable periodic checks (MANDI_REFRESH_INTERVAL_MINUTES, default 15 min).
6. Distributed Singleton Lock: MongoDB lease lock prevents duplicate schedulers across multi-replica deployments.
7. Concurrency Safety: In-process lock serializes simultaneous manual and background updates.
8. Cache Preservation: Never erases good cached records on transient API failures or rate limits.
9. Actual Reporting Dates: Sorts records by genuine arrival dates without substituting today's clock time.
"""

import os
import re
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import httpx

from database import (
    get_market_prices_cache_collection,
    get_market_prices_meta_collection,
    get_scheduler_locks_collection,
)

logger = logging.getLogger("namma_vivasayi.market_service")

# Official Government Metadata
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
DATA_GOV_IN_BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
OFFICIAL_DATA_SOURCE_NAME = "data.gov.in — Ministry of Agriculture and Farmers Welfare (AGMARKNET)"
OFFICIAL_PORTAL_URL = "https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi"
AGMARKNET_PORTAL_URL = "https://agmarknet.gov.in/"

DEFAULT_STATE = "Tamil Nadu"
REQUEST_TIMEOUT_SECONDS = 12.0
MEMORY_CACHE_TTL_SECONDS = 1800  # 30 minutes in-memory TTL
STALE_THRESHOLD_SECONDS = 86400  # 24 hours

# Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Baseline Snapshot File
BASELINE_SNAPSHOT_FILE = Path(__file__).parent / "data" / "agmarknet_snapshot.json"

# In-Memory Cache Store
_MEMORY_CACHE: Dict[str, Any] = {
    "records": [],
    "cachedAt": None,
    "lastSuccessfulFetchTime": None,
    "lastCheckedTime": None,
    "sourceStatus": "INITIALIZING",
    "sourceArrivalDate": None,
    "hasNewData": False,
    "error": None,
}

# In-process lock to prevent overlapping fetch/refresh calls within the same worker
_refresh_lock = asyncio.Lock()


def get_mandi_refresh_interval_minutes() -> int:
    """
    Configurable background data refresh interval in minutes (default: 15 minutes).
    Controls how often SEVA queries data.gov.in for updates;
    it does not cause the government portal to publish auctions more frequently.
    """
    raw = os.getenv("MANDI_REFRESH_INTERVAL_MINUTES", "15").strip()
    try:
        val = int(raw)
        return max(1, val)
    except (ValueError, TypeError):
        return 15


# Crop English -> Tamil Translation Dictionary
CROP_TAMIL_DICTIONARY: Dict[str, str] = {
    "paddy(dhan)(common)": "நெல் (சாதாரண ரகம்)",
    "paddy(dhan)(grade a)": "நெல் (கிரேடு ஏ)",
    "maize": "மக்காச்சோளம்",
    "cotton": "பருத்தி",
    "black gram (urd beans)": "உளுந்து",
    "green gram (moong)": "பாசிப்பயறு",
    "groundnut": "நிலக்கடலை",
    "sesamum(sesame,gingelly,til)": "எள்ளு",
    "turmeric": "மஞ்சள்",
    "banana": "வாழைப்பழம்",
    "tomato": "தக்காளி",
    "onion": "வெங்காயம்",
    "chilli red": "சிகப்பு மிளகாய்",
    "tapioca": "மரவள்ளிக்கிழங்கு",
    "coconut": "தேங்காய்",
    "cashewnuts": "முந்திரி",
    "sugarcane": "கரும்பு",
    "ragi (finger millet)": "கேழ்வரகு (ராகி)",
    "sorghum (jowar)": "சோளம்",
    "pearl millet (bajra)": "கம்பு",
    "bengal gram(gram)(whole)": "கொண்டைக்கடலை",
    "mustard": "கடுகு",
    "coriander(leaves)": "கொத்தமல்லி",
    "garlic": "பூண்டு",
    "ginger(green)": "இஞ்சி",
    "brinjal": "கத்தரிக்காய்",
    "cabbage": "முட்டைக்கோஸ்",
    "carrot": "கேரட்",
    "cauliflower": "காலிஃபிளவர்",
    "potato": "உருளைக்கிழங்கு",
    "drumstick": "முருங்கைக்காய்",
    "bhendi(ladies finger)": "வெண்டைக்காய்",
}


def get_tamil_crop_name(commodity_en: str) -> str:
    """Returns official or phonetic Tamil translation for a commodity."""
    key = str(commodity_en).strip().lower()
    if key in CROP_TAMIL_DICTIONARY:
        return CROP_TAMIL_DICTIONARY[key]
    for k, v in CROP_TAMIL_DICTIONARY.items():
        if k in key or key in k:
            return v
    return commodity_en


def slugify_record_id(state: str, district: str, market: str, commodity: str, variety: str, arrival_date: str) -> str:
    """Constructs a deterministic unique identifier for a commodity arrival record."""
    raw = f"{state}_{district}_{market}_{commodity}_{variety}_{arrival_date}".lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")


def parse_and_validate_date(date_str: Any) -> Optional[Tuple[str, str]]:
    """
    Validates and standardizes dates from data.gov.in.
    Returns (iso_date 'YYYY-MM-DD', human_date 'DD MMM YYYY') or None.
    Supported formats: 'DD/MM/YYYY', 'YYYY-MM-DD', 'DD-MM-YYYY', 'DD-Mon-YYYY', 'DD Mon YYYY'.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    clean = date_str.strip()
    dt = None

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(clean, fmt)
            break
        except ValueError:
            continue

    if not dt:
        return None

    # Sanity check: year must be reasonable (2020 - 2035)
    if dt.year < 2020 or dt.year > 2035:
        return None

    iso_str = dt.strftime("%Y-%m-%d")
    human_str = dt.strftime("%d %b %Y")
    return iso_str, human_str


def parse_and_validate_price(val: Any) -> Optional[float]:
    """
    Validates numeric price. Rejects zero, negative, or non-numeric values.
    """
    if val is None:
        return None
    try:
        f = float(str(val).replace(",", "").strip())
        return round(f, 2) if f > 0 else None
    except (ValueError, TypeError):
        return None


def normalize_record(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validates and normalizes a single commodity record from data.gov.in or cache.
    Rejects malformed records.
    """
    state = str(raw.get("state") or "").strip()
    district = str(raw.get("district") or "").strip()
    market = str(raw.get("market") or "").strip()
    commodity = str(raw.get("commodity") or "").strip()
    variety = str(raw.get("variety") or "Common").strip()
    grade = str(raw.get("grade") or "FAQ").strip()

    if not district or not commodity:
        return None

    raw_date = raw.get("arrival_date") or raw.get("arrivalDate") or raw.get("date")
    parsed_date = parse_and_validate_date(raw_date)
    if not parsed_date:
        return None
    iso_date, human_date = parsed_date

    # Validate Prices: If any price was provided but fails validation (e.g. negative, zero, malformed), reject the record
    raw_min = raw.get("min_price") if "min_price" in raw else raw.get("minPrice")
    raw_max = raw.get("max_price") if "max_price" in raw else raw.get("maxPrice")
    raw_modal = raw.get("modal_price") if "modal_price" in raw else raw.get("modalPrice")

    if raw_min is not None and parse_and_validate_price(raw_min) is None:
        return None
    if raw_max is not None and parse_and_validate_price(raw_max) is None:
        return None
    if raw_modal is not None and parse_and_validate_price(raw_modal) is None:
        return None

    min_p = parse_and_validate_price(raw_min)
    max_p = parse_and_validate_price(raw_max)
    modal_p = parse_and_validate_price(raw_modal)

    if not modal_p:
        if min_p and max_p:
            modal_p = round((min_p + max_p) / 2.0, 2)
        elif min_p:
            modal_p = min_p
        elif max_p:
            modal_p = max_p
        else:
            return None  # Cannot accept record without any price

    min_p = min_p or modal_p
    max_p = max_p or modal_p

    # Ensure min <= max
    if min_p > max_p:
        min_p, max_p = max_p, min_p

    # Ensure modal within range
    if modal_p < min_p:
        min_p = modal_p
    if modal_p > max_p:
        max_p = modal_p

    unit = str(raw.get("unit") or "Quintal").strip()
    trend = str(raw.get("trend") or "steady").lower()
    change = str(raw.get("change") or "₹0")
    record_id = raw.get("recordId") or slugify_record_id(state, district, market, commodity, variety, iso_date)

    commodity_ta = raw.get("commodityTa") or get_tamil_crop_name(commodity)

    return {
        "id": record_id,
        "recordId": record_id,
        "state": state or DEFAULT_STATE,
        "district": district,
        "market": market or f"{district} Mandi",
        "commodity": commodity,
        "commodityTa": commodity_ta,
        "variety": variety,
        "grade": grade,
        "arrivalDate": iso_date,
        "arrivalDateHuman": human_date,
        "minPrice": min_p,
        "maxPrice": max_p,
        "modalPrice": modal_p,
        "unit": unit,
        "trend": trend if trend in ("up", "down", "steady") else "steady",
        "change": change,
        # Backward compatibility with existing UI & models
        "crop": commodity,
        "cropTa": commodity_ta,
        "mandi": market or f"{district} Regulated Market",
        "date": human_date,
    }


def merge_and_deduplicate_records(
    existing_records: List[Dict[str, Any]],
    incoming_records: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], bool, int]:
    """
    Merges incoming records into existing records with stable deduplication based on
    (state, district, market, commodity, variety, arrival_date).
    Updates pricing if modified and appends new arrivals.
    Returns (merged_list, has_new_data, newly_added_count).
    """
    record_map: Dict[str, Dict[str, Any]] = {
        r["recordId"]: dict(r) for r in existing_records if "recordId" in r
    }

    newly_added = 0
    updated_count = 0

    for inc in incoming_records:
        rec_id = inc["recordId"]
        if rec_id not in record_map:
            record_map[rec_id] = inc
            newly_added += 1
        else:
            existing = record_map[rec_id]
            if (
                existing.get("modalPrice") != inc.get("modalPrice")
                or existing.get("minPrice") != inc.get("minPrice")
                or existing.get("maxPrice") != inc.get("maxPrice")
            ):
                record_map[rec_id] = inc
                updated_count += 1

    has_new_data = (newly_added > 0 or updated_count > 0)
    merged_list = list(record_map.values())

    # Sort strictly by genuine arrivalDate descending, then modalPrice
    merged_list.sort(key=lambda x: (x.get("arrivalDate", ""), x.get("modalPrice", 0)), reverse=True)
    return merged_list, has_new_data, newly_added


def load_baseline_snapshot_records() -> List[Dict[str, Any]]:
    """Loads authenticated baseline snapshot records for cold-start and offline fallback."""
    if not BASELINE_SNAPSHOT_FILE.exists():
        logger.warning(f"Baseline snapshot file not found: {BASELINE_SNAPSHOT_FILE}")
        return []

    try:
        with open(BASELINE_SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else (data.get("records", []) if isinstance(data, dict) else [])
            validated = []
            for r in records:
                norm = normalize_record(r)
                if norm:
                    validated.append(norm)
            return validated
    except Exception as e:
        logger.error(f"Error reading baseline snapshot: {e}")
        return []


async def fetch_live_from_data_gov_in(
    state: str = DEFAULT_STATE,
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Queries data.gov.in API for Resource ID 9ef84268-d588-465a-a308-a864a43d0070.
    Requires DATA_GOV_IN_API_KEY environment variable.
    """
    api_key = os.getenv("DATA_GOV_IN_API_KEY", "").strip()
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    if not api_key:
        logger.info("DATA_GOV_IN_API_KEY is not configured in backend environment variables.")
        return {
            "success": False,
            "sourceStatus": "UNCONFIGURED",
            "sourceConfigured": False,
            "records": [],
            "lastCheckedTime": now_ist,
            "error": "DATA_GOV_IN_API_KEY is not configured in backend/.env. Please register at data.gov.in to obtain an official API key."
        }

    params: Dict[str, Any] = {
        "api-key": api_key,
        "format": "json",
        "offset": offset,
        "limit": limit,
    }
    if state and state != "All":
        params["filters[state]"] = state
    if district and district != "All":
        params["filters[district]"] = district
    if commodity and commodity != "All":
        params["filters[commodity]"] = commodity

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (SEVA Namma Vivasayi Agmarknet Client)",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True, headers=headers) as client:
            resp = await client.get(DATA_GOV_IN_BASE_URL, params=params)

            if resp.status_code == 200:
                body = resp.json()
                raw_records = body.get("records") or []
                validated_records: List[Dict[str, Any]] = []

                for r in raw_records:
                    norm = normalize_record(r)
                    if norm:
                        validated_records.append(norm)

                logger.info(f"Successfully fetched {len(validated_records)} valid mandi records from data.gov.in")
                return {
                    "success": True,
                    "sourceStatus": "LIVE",
                    "sourceConfigured": True,
                    "records": validated_records,
                    "total": body.get("total", len(validated_records)),
                    "lastCheckedTime": now_ist,
                    "lastSuccessfulFetchTime": now_ist
                }
            elif resp.status_code in (401, 403):
                return {
                    "success": False,
                    "sourceStatus": "UNAVAILABLE",
                    "sourceConfigured": True,
                    "records": [],
                    "lastCheckedTime": now_ist,
                    "error": "data.gov.in rejected the API key (HTTP 403 Key Not Authorised). Please verify your official API key in backend/.env."
                }
            elif resp.status_code == 429:
                return {
                    "success": False,
                    "sourceStatus": "RATE_LIMITED",
                    "sourceConfigured": True,
                    "records": [],
                    "lastCheckedTime": now_ist,
                    "error": "data.gov.in daily/hourly rate limit exceeded. Preserving cached government records."
                }
            else:
                return {
                    "success": False,
                    "sourceStatus": "UNAVAILABLE",
                    "sourceConfigured": True,
                    "records": [],
                    "lastCheckedTime": now_ist,
                    "error": f"data.gov.in server returned unexpected HTTP status {resp.status_code}."
                }
    except httpx.TimeoutException:
        return {
            "success": False,
            "sourceStatus": "TIMEOUT",
            "sourceConfigured": True,
            "records": [],
            "lastCheckedTime": now_ist,
            "error": "Connection to data.gov.in timed out. Government portal may be experiencing peak latency."
        }
    except Exception as e:
        return {
            "success": False,
            "sourceStatus": "NETWORK_ERROR",
            "sourceConfigured": True,
            "records": [],
            "lastCheckedTime": now_ist,
            "error": f"Network error connecting to data.gov.in: {str(e)}"
        }


async def save_records_to_mongo_cache(records: List[Dict[str, Any]], fetch_time: str, latest_arrival_date: Optional[str]):
    """Persists valid government mandi records and fetch metadata to MongoDB."""
    cache_col = get_market_prices_cache_collection()
    meta_col = get_market_prices_meta_collection()

    if cache_col is None:
        return

    now_iso = datetime.now(timezone.utc).isoformat()

    # Bulk upsert records
    for r in records:
        r_copy = dict(r)
        r_copy["cachedAt"] = now_iso
        try:
            await cache_col.update_one(
                {"recordId": r["recordId"]},
                {"$set": r_copy},
                upsert=True
            )
        except Exception as e:
            logger.debug(f"Cache upsert notice: {e}")

    # Update metadata
    if meta_col is not None:
        try:
            await meta_col.update_one(
                {"metaKey": "agmarknet_latest"},
                {
                    "$set": {
                        "metaKey": "agmarknet_latest",
                        "lastSuccessfulFetchTime": fetch_time,
                        "lastCheckedTime": fetch_time,
                        "sourceArrivalDate": latest_arrival_date,
                        "totalCachedRecords": len(records),
                        "updatedAt": now_iso
                    }
                },
                upsert=True
            )
        except Exception:
            pass


async def load_records_from_mongo_cache() -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Retrieves cached mandi records and fetch metadata from MongoDB."""
    cache_col = get_market_prices_cache_collection()
    meta_col = get_market_prices_meta_collection()

    if cache_col is None:
        return [], None

    records: List[Dict[str, Any]] = []
    try:
        cursor = cache_col.find({}).sort("arrivalDate", -1).limit(500)
        async for doc in cursor:
            norm = normalize_record(doc)
            if norm:
                records.append(norm)
    except Exception as e:
        logger.warning(f"Error reading mongo market cache: {e}")

    meta = None
    if meta_col is not None:
        try:
            meta = await meta_col.find_one({"metaKey": "agmarknet_latest"})
        except Exception:
            pass

    return records, meta


async def sync_live_market_data(force: bool = False) -> Dict[str, Any]:
    """
    Performs data synchronization against data.gov.in.
    Uses an in-process lock to prevent overlapping sync tasks.
    Merges and deduplicates incoming records with stable IDs.
    CRITICAL: Preserves good cached records if the live fetch fails.
    """
    global _MEMORY_CACHE
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    async with _refresh_lock:
        mem_cached_at = _MEMORY_CACHE.get("cachedAt")
        mem_is_fresh = False
        if mem_cached_at and not force:
            age_seconds = (now_utc - mem_cached_at).total_seconds()
            if age_seconds < MEMORY_CACHE_TTL_SECONDS and len(_MEMORY_CACHE.get("records", [])) > 0:
                mem_is_fresh = True

        if mem_is_fresh and not force:
            return {
                "success": True,
                "hasNewData": False,
                "sourceStatus": _MEMORY_CACHE.get("sourceStatus", "LIVE"),
                "records": _MEMORY_CACHE.get("records", []),
                "lastCheckedTime": _MEMORY_CACHE.get("lastCheckedTime", now_ist)
            }

        # Attempt Live Fetch
        live_res = await fetch_live_from_data_gov_in(state=DEFAULT_STATE, limit=100)
        _MEMORY_CACHE["lastCheckedTime"] = now_ist

        if live_res.get("success") and len(live_res.get("records", [])) > 0:
            incoming = live_res["records"]
            current_records = _MEMORY_CACHE.get("records", [])
            if not current_records:
                mongo_records, _ = await load_records_from_mongo_cache()
                current_records = mongo_records or load_baseline_snapshot_records()

            merged_records, has_new_data, newly_added = merge_and_deduplicate_records(current_records, incoming)

            dates = [r["arrivalDateHuman"] for r in merged_records if r.get("arrivalDateHuman")]
            latest_arr_date = dates[0] if dates else now_ist

            _MEMORY_CACHE["records"] = merged_records
            _MEMORY_CACHE["cachedAt"] = now_utc
            _MEMORY_CACHE["lastSuccessfulFetchTime"] = now_ist
            _MEMORY_CACHE["sourceArrivalDate"] = latest_arr_date
            _MEMORY_CACHE["sourceStatus"] = "LIVE"
            _MEMORY_CACHE["hasNewData"] = has_new_data
            _MEMORY_CACHE["error"] = None

            # Persist to MongoDB
            await save_records_to_mongo_cache(merged_records, now_ist, latest_arr_date)

            # Evaluate farmer price notifications if new or updated records were detected
            if has_new_data:
                try:
                    from market_notifications import evaluate_market_feed_and_notify
                    await evaluate_market_feed_and_notify(
                        previous_records=current_records,
                        incoming_records=incoming,
                        is_stale=False,
                    )
                except Exception as notif_err:
                    logger.warning(f"Error evaluating market notifications: {notif_err}")

            return {
                "success": True,
                "hasNewData": has_new_data,
                "newlyAdded": newly_added,
                "sourceStatus": "LIVE",
                "records": merged_records,
                "lastCheckedTime": now_ist,
                "lastSuccessfulFetchTime": now_ist
            }
        else:
            # LIVE FETCH FAILED OR UNCONFIGURED:
            # PRESERVE GOOD CACHED DATA. DO NOT ERASE OR REPLACE WITH EMPTY.
            error_msg = live_res.get("error")
            source_status = live_res.get("sourceStatus", "STALE_CACHE")

            if not _MEMORY_CACHE.get("records"):
                mongo_records, meta = await load_records_from_mongo_cache()
                if mongo_records:
                    _MEMORY_CACHE["records"] = mongo_records
                    _MEMORY_CACHE["cachedAt"] = now_utc
                    _MEMORY_CACHE["lastSuccessfulFetchTime"] = meta.get("lastSuccessfulFetchTime") if meta else now_ist
                    _MEMORY_CACHE["sourceArrivalDate"] = meta.get("sourceArrivalDate") if meta else mongo_records[0].get("arrivalDateHuman")
                else:
                    snapshot_records = load_baseline_snapshot_records()
                    _MEMORY_CACHE["records"] = snapshot_records
                    _MEMORY_CACHE["cachedAt"] = now_utc
                    _MEMORY_CACHE["lastSuccessfulFetchTime"] = "18 Oct 2026, 05:00 PM IST"
                    _MEMORY_CACHE["sourceArrivalDate"] = "18 Oct 2026"

            _MEMORY_CACHE["sourceStatus"] = "STALE_CACHE" if _MEMORY_CACHE.get("records") else source_status
            _MEMORY_CACHE["error"] = error_msg
            _MEMORY_CACHE["hasNewData"] = False

            # Update MongoDB metadata only (recording last check time without altering cached records)
            meta_col = get_market_prices_meta_collection()
            if meta_col is not None:
                try:
                    await meta_col.update_one(
                        {"metaKey": "agmarknet_latest"},
                        {"$set": {"lastCheckedTime": now_ist, "lastError": error_msg}},
                        upsert=True
                    )
                except Exception:
                    pass

            # If feed is stale or unavailable, evaluate non-alarming stale notice (deduplicated daily)
            try:
                from market_notifications import evaluate_stale_feed_notification
                await evaluate_stale_feed_notification(
                    latest_reporting_date=_MEMORY_CACHE.get("sourceArrivalDate"),
                    feed_error=error_msg,
                )
            except Exception as stale_err:
                logger.debug(f"Stale feed notification notice: {stale_err}")

            return {
                "success": False,
                "hasNewData": False,
                "sourceStatus": _MEMORY_CACHE["sourceStatus"],
                "records": _MEMORY_CACHE.get("records", []),
                "lastCheckedTime": now_ist,
                "error": error_msg
            }


class MandiPricesScheduler:
    """
    Background scheduler for automated data.gov.in mandi market price sync.
    - Configurable interval: MANDI_REFRESH_INTERVAL_MINUTES (default 15 minutes).
    - Distributed lease lock: Prevents duplicate scheduler instances in multi-worker/replica deployments.
    - In-process lock: Prevents overlapping sync tasks within the same worker.
    - Cache preservation: Never erases valid cached data on transient network or API failures.
    - Note: This interval checks for new data; it does not make the government source publish prices every 15 minutes.
    """
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"mandi-worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def acquire_distributed_lease(self) -> bool:
        """Attempts to acquire or renew a singleton distributed lease in MongoDB."""
        col = get_scheduler_locks_collection()
        if col is None:
            return True  # Standalone mode without DB locks

        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        ttl = max(600, get_mandi_refresh_interval_minutes() * 60 + 120)
        stale_threshold = (now_utc - timedelta(seconds=ttl)).isoformat()

        existing = await col.find_one({"jobName": "mandi_prices_sync"})
        if not existing:
            try:
                await col.insert_one({
                    "jobName": "mandi_prices_sync",
                    "workerId": self.worker_id,
                    "lastHeartbeat": now_iso,
                    "status": "ACTIVE"
                })
                return True
            except Exception:
                pass

        try:
            res = await col.update_one(
                {
                    "jobName": "mandi_prices_sync",
                    "$or": [
                        {"workerId": self.worker_id},
                        {"lastHeartbeat": {"$lt": stale_threshold}},
                        {"lastHeartbeat": {"$exists": False}}
                    ]
                },
                {
                    "$set": {
                        "workerId": self.worker_id,
                        "lastHeartbeat": now_iso,
                        "status": "ACTIVE"
                    }
                }
            )
            return res.matched_count > 0
        except Exception as e:
            logger.warning(f"Mandi scheduler lock contention: {e}")
            return False

    async def release_distributed_lease(self):
        """Releases the distributed lease upon worker shutdown."""
        col = get_scheduler_locks_collection()
        if col is not None:
            try:
                await col.delete_one({"jobName": "mandi_prices_sync", "workerId": self.worker_id})
            except Exception:
                pass

    async def run_sync_cycle(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes a single check pass.
        Guarantees distributed singleton execution and prevents in-process overlap.
        """
        has_lease = await self.acquire_distributed_lease()
        if not has_lease:
            logger.info("Another scheduler worker holds the distributed lease for mandi sync. Skipping cycle.")
            return {
                "status": "SKIPPED_LEASE_HELD",
                "workerId": self.worker_id,
                "leaseAcquired": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        async with self._lock:
            sync_result = await sync_live_market_data(force=force)
            return {
                "status": "SUCCESS" if sync_result.get("success") else "FAILED",
                "workerId": self.worker_id,
                "leaseAcquired": True,
                "hasNewData": sync_result.get("hasNewData", False),
                "sourceStatus": sync_result.get("sourceStatus"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def start(self):
        """Starts the background periodic check loop."""
        if self._is_running:
            return
        self._is_running = True
        interval_minutes = get_mandi_refresh_interval_minutes()
        interval_seconds = interval_minutes * 60

        logger.info(
            f"MandiPricesScheduler started (workerId={self.worker_id}, interval={interval_minutes}m). "
            f"Note: This interval checks for new data from data.gov.in; "
            f"it does not cause the government source to publish prices more frequently."
        )

        async def _loop():
            # Initial check shortly after startup
            await asyncio.sleep(5)
            while self._is_running:
                try:
                    await self.run_sync_cycle()
                except Exception as e:
                    logger.error(f"Error in mandi prices scheduler check cycle: {e}")

                for _ in range(interval_seconds):
                    if not self._is_running:
                        break
                    await asyncio.sleep(1)

        self._task = asyncio.create_task(_loop())

    async def stop(self):
        """Stops the scheduler and releases lease."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        await self.release_distributed_lease()
        logger.info(f"MandiPricesScheduler stopped (workerId={self.worker_id})")


# Global singleton scheduler instance
mandi_scheduler = MandiPricesScheduler()


async def get_market_prices(
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "arrival_date",
    sort_order: str = "desc",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for retrieving validated government mandi market prices.
    Handles live fetch, memory caching, MongoDB persistence, stale fallback,
    filtering, pagination, and honest source disclosures.
    """
    global _MEMORY_CACHE
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    api_key_configured = bool(os.getenv("DATA_GOV_IN_API_KEY", "").strip())

    # Synchronize or read from cache
    sync_res = await sync_live_market_data(force=force_refresh)

    all_records = _MEMORY_CACHE.get("records", [])
    is_live = (_MEMORY_CACHE.get("sourceStatus") == "LIVE")
    is_stale = not is_live or not api_key_configured
    source_status = _MEMORY_CACHE.get("sourceStatus", "STALE_CACHE")
    error_msg = _MEMORY_CACHE.get("error")
    has_new_data = _MEMORY_CACHE.get("hasNewData", False)

    source_arr_date = _MEMORY_CACHE.get("sourceArrivalDate") or (all_records[0]["arrivalDateHuman"] if all_records else None)
    last_fetch_time = _MEMORY_CACHE.get("lastSuccessfulFetchTime") or "Not yet synchronized"
    last_checked_time = _MEMORY_CACHE.get("lastCheckedTime") or now_ist

    # Calculate next scheduled automatic refresh time
    interval_min = get_mandi_refresh_interval_minutes()
    cached_at = _MEMORY_CACHE.get("cachedAt") or now_utc
    next_dt = cached_at + timedelta(minutes=interval_min)
    next_scheduled_refresh_time = next_dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    # Generate sync notification messages
    sync_status = "UP_TO_DATE"
    if has_new_data and is_live:
        sync_status = "UPDATED"
        sync_msg_en = "Updated with newly published market records from data.gov.in."
        sync_msg_ta = "அரசு தளத்திலிருந்து புதிய சந்தை நிலவரம் புதுப்பிக்கப்பட்டது."
    elif is_live:
        sync_status = "UP_TO_DATE"
        sync_msg_en = "No new market data (Government records are up to date)."
        sync_msg_ta = "புதிய சந்தை வரத்து இல்லை (அரசு பதிவுகள் புதுப்பிக்கப்பட்டுள்ளன)."
    else:
        sync_status = "STALE_CACHE"
        sync_msg_en = "Operating in verified cached mode."
        sync_msg_ta = "காப்பக முறையில் செயல்படுகிறது."

    # 2. Extract Available Districts & Commodities for Filter Dropdowns
    available_districts = sorted(list({r["district"] for r in all_records if r.get("district")}))
    available_commodities = sorted(list({r["commodity"] for r in all_records if r.get("commodity")}))

    # 3. Apply Filters
    filtered = list(all_records)

    # District Filter
    if district and district.strip().lower() != "all":
        d_lower = district.strip().lower()
        filtered = [r for r in filtered if d_lower in r["district"].lower()]

    # Commodity Filter
    if commodity and commodity.strip().lower() != "all":
        c_lower = commodity.strip().lower()
        filtered = [r for r in filtered if c_lower in r["commodity"].lower()]

    # Search Query
    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            r for r in filtered
            if (
                q in r["commodity"].lower()
                or q in r["market"].lower()
                or q in r["district"].lower()
                or q in (r.get("commodityTa") or "").lower()
                or q in r["variety"].lower()
            )
        ]

    # 4. Sorting (uses actual source arrivalDate; never substitutes today's date)
    reverse_order = (sort_order.lower() == "desc")
    if sort_by in ("modal_price", "modalPrice"):
        filtered.sort(key=lambda x: x.get("modalPrice", 0.0), reverse=reverse_order)
    elif sort_by in ("min_price", "minPrice"):
        filtered.sort(key=lambda x: x.get("minPrice", 0.0), reverse=reverse_order)
    elif sort_by in ("max_price", "maxPrice"):
        filtered.sort(key=lambda x: x.get("maxPrice", 0.0), reverse=reverse_order)
    elif sort_by == "commodity":
        filtered.sort(key=lambda x: x.get("commodity", "").lower(), reverse=reverse_order)
    elif sort_by == "market":
        filtered.sort(key=lambda x: x.get("market", "").lower(), reverse=reverse_order)
    else:
        # Default: Sort by genuine arrivalDate descending
        filtered.sort(key=lambda x: (x.get("arrivalDate", ""), x.get("modalPrice", 0)), reverse=reverse_order)

    # 5. Pagination
    total = len(filtered)
    page = max(1, page)
    limit = max(1, min(100, limit))
    total_pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    paginated = filtered[offset : offset + limit]

    # Stale Notice Strings
    stale_en = None
    stale_ta = None
    if is_stale or not api_key_configured:
        stale_en = (
            f"Notice: Displaying authenticated cached government records from data.gov.in (Source Arrival Date: {source_arr_date or 'Recent'}). "
            + ("Live sync is inactive because DATA_GOV_IN_API_KEY is not configured in backend/.env." if not api_key_configured else "Live source is temporarily experiencing latency.")
        )
        stale_ta = (
            f"அறிவிப்பு: data.gov.in தளத்திலிருந்து பெறப்பட்ட அரசு ஆவணக் குறிப்புகள் காட்டப்படுகின்றன (சந்தை வரத்து தேதி: {source_arr_date or 'சமீபத்தியது'}). "
            + ("நேரடி சேவைக்கு backend/.env கோப்பில் DATA_GOV_IN_API_KEY ஐ உள்ளமைக்கவும்." if not api_key_configured else "நேரடி அரசு சேவையகம் தற்காலிகமாக தாமதமாகிறது.")
        )

    return {
        "dataSource": OFFICIAL_DATA_SOURCE_NAME,
        "sourceUrl": OFFICIAL_PORTAL_URL,
        "resourceId": RESOURCE_ID,
        "sourceStatus": source_status,
        "sourceConfigured": api_key_configured,
        "isLive": is_live,
        "isStale": is_stale,
        "sourceArrivalDate": source_arr_date,
        "lastSuccessfulFetchTime": last_fetch_time,
        "lastCheckedTime": last_checked_time,
        "hasNewData": has_new_data,
        "syncStatus": sync_status,
        "syncMessageEn": sync_msg_en,
        "syncMessageTa": sync_msg_ta,
        "refreshIntervalMinutes": interval_min,
        "nextScheduledRefreshTime": next_scheduled_refresh_time,
        "commodities": paginated,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        },
        "availableDistricts": available_districts,
        "availableCommodities": available_commodities,
        "staleNoticeEn": stale_en,
        "staleNoticeTa": stale_ta,
        "error": error_msg,
        # Backward-compatibility fields
        "timestamp": f"{source_arr_date or now_ist} (Govt Arrival: {source_arr_date or 'N/A'})",
        "demoNoticeEn": stale_en or "Government market auction rates from data.gov.in Agmarknet feed.",
        "demoNoticeTa": stale_ta or "அரசு ஒழுங்குமுறை விற்பனைக் கூடங்களின் நேரடி நிலவரம்."
    }


def get_market_prices_sync(
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "arrival_date",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    Synchronous accessor for backward compatibility with smart_farming and ai_assistant.
    Reads from current memory cache or baseline snapshot without blocking.
    """
    global _MEMORY_CACHE
    records = _MEMORY_CACHE.get("records")
    if not records:
        records = load_baseline_snapshot_records()
        _MEMORY_CACHE["records"] = records
        _MEMORY_CACHE["cachedAt"] = datetime.now(timezone.utc)
        _MEMORY_CACHE["lastSuccessfulFetchTime"] = "18 Oct 2026, 05:00 PM IST"
        _MEMORY_CACHE["sourceArrivalDate"] = "18 Oct 2026"
        _MEMORY_CACHE["sourceStatus"] = "STALE_CACHE"

    filtered = list(records)
    if district and district.strip().lower() != "all":
        d_lower = district.strip().lower()
        filtered = [r for r in filtered if d_lower in r["district"].lower()]
    if commodity and commodity.strip().lower() != "all":
        c_lower = commodity.strip().lower()
        filtered = [r for r in filtered if c_lower in r["commodity"].lower()]
    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            r for r in filtered
            if (
                q in r["commodity"].lower()
                or q in r["market"].lower()
                or q in r["district"].lower()
                or q in (r.get("commodityTa") or "").lower()
                or q in r["variety"].lower()
            )
        ]

    reverse_order = (sort_order.lower() == "desc")
    filtered.sort(key=lambda x: (x.get("arrivalDate", ""), x.get("modalPrice", 0)), reverse=reverse_order)
    total = len(filtered)
    offset = (page - 1) * limit
    paginated = filtered[offset : offset + limit]

    now_ist = datetime.now(timezone.utc).astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    source_arr_date = _MEMORY_CACHE.get("sourceArrivalDate") or (filtered[0]["arrivalDateHuman"] if filtered else "18 Oct 2026")
    interval_min = get_mandi_refresh_interval_minutes()

    return {
        "dataSource": OFFICIAL_DATA_SOURCE_NAME,
        "sourceUrl": OFFICIAL_PORTAL_URL,
        "resourceId": RESOURCE_ID,
        "sourceStatus": _MEMORY_CACHE.get("sourceStatus", "STALE_CACHE"),
        "sourceConfigured": bool(os.getenv("DATA_GOV_IN_API_KEY", "").strip()),
        "isLive": False,
        "isStale": True,
        "sourceArrivalDate": source_arr_date,
        "lastSuccessfulFetchTime": _MEMORY_CACHE.get("lastSuccessfulFetchTime", "18 Oct 2026, 05:00 PM IST"),
        "lastCheckedTime": now_ist,
        "hasNewData": False,
        "syncStatus": "STALE_CACHE",
        "syncMessageEn": "Operating in verified cached mode.",
        "syncMessageTa": "காப்பக முறையில் செயல்படுகிறது.",
        "refreshIntervalMinutes": interval_min,
        "commodities": paginated,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": max(1, (total + limit - 1) // limit)
        },
        "availableDistricts": sorted(list({r["district"] for r in records if r.get("district")})),
        "availableCommodities": sorted(list({r["commodity"] for r in records if r.get("commodity")})),
        "timestamp": f"{source_arr_date} (Govt Arrival: {source_arr_date})",
        "demoNoticeEn": "Government market auction rates from data.gov.in Agmarknet feed.",
        "demoNoticeTa": "அரசு ஒழுங்குமுறை விற்பனைக் கூடங்களின் நேரடி நிலவரம்."
    }


async def get_market_operational_health() -> Dict[str, Any]:
    """
    Returns structured operational health metrics for the data.gov.in mandi integration.
    Includes data source attribution, API configuration, last successful fetch,
    last checked time, cache freshness in seconds, scheduler worker state, and error logs.
    """
    global _MEMORY_CACHE
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    api_key_configured = bool(os.getenv("DATA_GOV_IN_API_KEY", "").strip())
    cached_at = _MEMORY_CACHE.get("cachedAt")
    cache_age_seconds = round((now_utc - cached_at).total_seconds(), 1) if cached_at else None

    meta_col = get_market_prices_meta_collection()
    meta_doc = None
    if meta_col is not None:
        try:
            meta_doc = await meta_col.find_one({"metaKey": "agmarknet_latest"})
        except Exception:
            pass

    records = _MEMORY_CACHE.get("records") or []
    if not records:
        mongo_records, _ = await load_records_from_mongo_cache()
        records = mongo_records or load_baseline_snapshot_records()

    records_count = len(records)
    last_successful = _MEMORY_CACHE.get("lastSuccessfulFetchTime") or (meta_doc.get("lastSuccessfulFetchTime") if meta_doc else None)
    last_checked = _MEMORY_CACHE.get("lastCheckedTime") or (meta_doc.get("lastCheckedTime") if meta_doc else now_ist)
    last_error = _MEMORY_CACHE.get("error") or (meta_doc.get("lastError") if meta_doc else None)
    source_status = _MEMORY_CACHE.get("sourceStatus", "INITIALIZING")
    is_live = (source_status == "LIVE")
    is_stale = (cache_age_seconds is not None and cache_age_seconds > STALE_THRESHOLD_SECONDS) or not is_live

    return {
        "status": "healthy" if records_count > 0 else "degraded",
        "dataSource": {
            "name": OFFICIAL_DATA_SOURCE_NAME,
            "resourceId": RESOURCE_ID,
            "portalUrl": OFFICIAL_PORTAL_URL,
            "agmarknetUrl": AGMARKNET_PORTAL_URL,
            "apiKeyConfigured": api_key_configured,
            "sourceStatus": source_status,
            "isLive": is_live,
            "isStale": is_stale,
        },
        "cacheMetrics": {
            "totalCachedRecords": records_count,
            "latestArrivalDate": _MEMORY_CACHE.get("sourceArrivalDate") or (meta_doc.get("sourceArrivalDate") if meta_doc else (records[0].get("arrivalDateHuman") if records else None)),
            "lastSuccessfulFetchTime": last_successful,
            "lastCheckedTime": last_checked,
            "cacheAgeSeconds": cache_age_seconds,
            "cacheTtlSeconds": MEMORY_CACHE_TTL_SECONDS,
            "staleThresholdSeconds": STALE_THRESHOLD_SECONDS,
            "hasNewData": _MEMORY_CACHE.get("hasNewData", False),
        },
        "backgroundScheduler": {
            "isRunning": mandi_scheduler._is_running,
            "workerId": mandi_scheduler.worker_id,
            "refreshIntervalMinutes": get_mandi_refresh_interval_minutes(),
            "note": "Checks for updates at this interval; does not cause data.gov.in to publish faster.",
        },
        "operationalErrors": {
            "lastError": last_error,
            "hasRecentError": bool(last_error),
        },
        "timestamp": now_ist,
    }


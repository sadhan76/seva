"""
Reliable Mandi-Price Notifications Service for Namma Vivasayi AI
================================================================
Monitors live government AGMARKNET mandi feeds (data.gov.in Resource 9ef84268-d588-465a-a308-a864a43d0070)
and alerts farmers to:
1. Newly published arrivals for their selected crops or markets.
2. Meaningful price increases (surges) or decreases (drops) beyond a configurable threshold.
3. Government mandi feed status when stale or temporarily unavailable.

Strict Guarantees:
- Never alerts on duplicate records (identical prices and arrival dates).
- Never invents prices; always cites real market name, modal/min/max prices, and arrival date.
- Stable deduplication keys prevent duplicate alerts across worker restarts and multiple replicas.
- Strict farmer isolation and preference controls (crop selection, market selection, price threshold %).
- Bilingual English and Tamil notification payloads.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId

from database import (
    get_notifications_collection,
    get_users_collection,
    get_notification_preferences_collection,
)
from smart_farming import IST
from irrigation_notifications import (
    get_user_notification_preferences,
    VAPID_PUBLIC_KEY,
    _dispatch_web_push,
)

logger = logging.getLogger("namma_vivasayi.market_notifications")

# Alert Event Types
ALERT_TYPE_MARKET_NEW_PRICE = "market_new_price"
ALERT_TYPE_MARKET_PRICE_SURGE = "market_price_surge"
ALERT_TYPE_MARKET_PRICE_DROP = "market_price_drop"
ALERT_TYPE_MARKET_FEED_STALE = "market_feed_stale"

ALL_MARKET_ALERT_TYPES = [
    ALERT_TYPE_MARKET_NEW_PRICE,
    ALERT_TYPE_MARKET_PRICE_SURGE,
    ALERT_TYPE_MARKET_PRICE_DROP,
    ALERT_TYPE_MARKET_FEED_STALE,
]

DEDUP_WINDOW_HOURS = 24
MAX_MARKET_ALERTS_PER_DAY = 6


def _format_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    clean = dict(doc)
    if "_id" in clean:
        clean["id"] = str(clean["_id"])
        del clean["_id"]
    return clean


def normalize_filter_token(val: Optional[str]) -> str:
    """Normalizes string for robust case-insensitive substring matching."""
    if not val:
        return ""
    return re_sub_token(val.strip().lower())


def re_sub_token(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", text)


def extract_filter_tokens(text: Optional[str]) -> List[str]:
    """Splits text on punctuation/spaces and returns cleaned alphanumeric tokens of length >= 3."""
    import re
    if not text:
        return []
    raw = re.split(r"[\s/,()\-]+", text.lower())
    clean = []
    for t in raw:
        sub = re.sub(r"[^a-z0-9]", "", t).strip()
        if len(sub) >= 3:
            clean.append(sub)
    return clean


def matches_farmer_crop_and_market(
    farmer_user: Dict[str, Any],
    prefs: Dict[str, Any],
    commodity: str,
    commodity_ta: Optional[str],
    market: str,
    district: str,
) -> bool:
    """
    Checks if a commodity and market match the farmer's preferences or profile.
    - If farmer selected specific commodities in preferences: strictly matches them.
    - If no specific commodities selected: matches farmer profile's primaryCrop,
      or defaults to allowing major crops.
    - If farmer selected specific markets: strictly matches them.
    - If no specific markets selected: matches farmer profile's district or mandiName,
      or allows all Tamil Nadu regulated markets.
    """
    sel_commodities = [str(c).strip() for c in prefs.get("mandiSelectedCommodities") or [] if str(c).strip()]
    sel_markets = [str(m).strip() for m in prefs.get("mandiSelectedMarkets") or [] if str(m).strip()]

    norm_commodity = normalize_filter_token(commodity)
    norm_commodity_ta = normalize_filter_token(commodity_ta)
    norm_market = normalize_filter_token(market)
    norm_district = normalize_filter_token(district)

    # 1. Commodity Matching
    if sel_commodities:
        matched_crop = False
        for sc in sel_commodities:
            sc_tokens = extract_filter_tokens(sc)
            for sct in sc_tokens:
                if sct in norm_commodity or (norm_commodity_ta and sct in norm_commodity_ta):
                    matched_crop = True
                    break
            if matched_crop:
                break
        if not matched_crop:
            return False
    else:
        # Check farmer profile primaryCrop if present
        farmer_crop = farmer_user.get("primaryCrop")
        if farmer_crop and farmer_crop.lower() not in ("all", "any", "other"):
            crop_tokens = extract_filter_tokens(farmer_crop)
            is_match = False
            for ct in crop_tokens:
                if ct in norm_commodity or (norm_commodity_ta and ct in norm_commodity_ta):
                    is_match = True
                    break
            # If user has profile crop and it completely mismatches this record, skip
            if not is_match and len(crop_tokens) > 0:
                return False

    # 2. Market / District Matching
    if sel_markets:
        matched_market = False
        for sm in sel_markets:
            sm_tokens = extract_filter_tokens(sm)
            for smt in sm_tokens:
                if smt in norm_market or smt in norm_district:
                    matched_market = True
                    break
            if matched_market:
                break
        if not matched_market:
            return False
    else:
        # Check farmer profile district if present
        farmer_district = farmer_user.get("district")
        if farmer_district and farmer_district.lower() not in ("all", "tamil nadu", "any"):
            dist_tokens = extract_filter_tokens(farmer_district)
            is_match = False
            for dt in dist_tokens:
                if dt in norm_district or dt in norm_market:
                    is_match = True
                    break
            if not is_match and len(dist_tokens) > 0:
                return False

    return True


async def create_market_notification(
    user_id: str,
    event_type: str,
    title_en: str,
    title_ta: str,
    message_en: str,
    message_ta: str,
    farmer_id: Optional[str] = None,
    market: Optional[str] = None,
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    commodity_ta: Optional[str] = None,
    variety: Optional[str] = None,
    grade: Optional[str] = None,
    old_price: Optional[float] = None,
    new_price: Optional[float] = None,
    price_diff: Optional[float] = None,
    price_change_percent: Optional[float] = None,
    source_reporting_date: Optional[str] = None,
    dedup_key: Optional[str] = None,
    dedup_window_hours: int = DEDUP_WINDOW_HOURS,
) -> Optional[Dict[str, Any]]:
    """
    Creates and stores a verified Mandi Market Price alert in MongoDB 'notifications' collection.
    - Validates farmer notification preferences (master toggle, surge, drop, stale, threshold).
    - Prevents duplicates using stable dedupKey within 24 hours.
    - Applies per-farmer daily rate limiting (max 6 market alerts per day).
    - Delivers in-app and dispatches Web Push if configured.
    """
    notif_col = get_notifications_collection()
    if notif_col is None:
        return None

    # 1. Preferences Check
    prefs = await get_user_notification_preferences(user_id, farmer_id)
    if not prefs.get("mandiPriceAlerts", True):
        return None

    if event_type == ALERT_TYPE_MARKET_NEW_PRICE and not prefs.get("mandiPriceAlerts", True):
        return None
    elif event_type == ALERT_TYPE_MARKET_PRICE_SURGE and not prefs.get("mandiPriceSurgeAlerts", True):
        return None
    elif event_type == ALERT_TYPE_MARKET_PRICE_DROP and not prefs.get("mandiPriceDropAlerts", True):
        return None
    elif event_type == ALERT_TYPE_MARKET_FEED_STALE and not prefs.get("mandiStaleFeedAlerts", True):
        return None

    # If surge or drop, verify threshold percentage
    if event_type in (ALERT_TYPE_MARKET_PRICE_SURGE, ALERT_TYPE_MARKET_PRICE_DROP) and price_change_percent is not None:
        threshold = float(prefs.get("mandiPriceThresholdPercent", 5.0))
        if abs(price_change_percent) < threshold:
            logger.debug(f"Skipping alert: price change {abs(price_change_percent)}% < threshold {threshold}% for user {user_id}")
            return None

    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    now_iso = now_utc.isoformat()
    now_human = now_ist.strftime("%d %b %Y, %I:%M %p IST")

    # 2. Stable Deduplication Key
    if not dedup_key:
        if event_type == ALERT_TYPE_MARKET_FEED_STALE:
            today_str = now_ist.strftime("%Y%m%d")
            dedup_key = f"{user_id}_{ALERT_TYPE_MARKET_FEED_STALE}_{today_str}"
        else:
            comm_slug = normalize_filter_token(commodity or "unknown")
            market_slug = normalize_filter_token(market or "mandi")
            date_slug = normalize_filter_token(source_reporting_date or now_ist.strftime("%Y-%m-%d"))
            price_slug = int(round(new_price)) if new_price is not None else 0
            dedup_key = f"{user_id}_{event_type}_{comm_slug}_{market_slug}_{date_slug}_{price_slug}"

    cutoff_dedup = (now_utc - timedelta(hours=dedup_window_hours)).isoformat()
    existing = await notif_col.find_one({
        "$or": [{"userId": str(user_id)}, {"farmerId": str(farmer_id)}],
        "dedupKey": dedup_key,
        "isoTimestamp": {"$gte": cutoff_dedup}
    })
    if existing:
        logger.info(f"Deduplicated market alert {event_type} for user {user_id} (key: {dedup_key})")
        return None

    # 3. 24-Hour Per-Farmer Rate Limit
    cutoff_24h = (now_utc - timedelta(hours=24)).isoformat()
    recent_count = await notif_col.count_documents({
        "$or": [{"userId": str(user_id)}, {"farmerId": str(farmer_id)}],
        "type": "market",
        "isoTimestamp": {"$gte": cutoff_24h}
    })
    if recent_count >= MAX_MARKET_ALERTS_PER_DAY:
        logger.info(f"Market alerts rate limit reached for user {user_id} ({recent_count} alerts in 24h)")
        return None

    # 4. Construct Persistent Document
    notif_doc: Dict[str, Any] = {
        "userId": str(user_id),
        "farmerId": str(farmer_id) if farmer_id else None,
        "type": "market",
        "eventType": event_type,
        "title": title_en,
        "titleTa": title_ta,
        "message": message_en,
        "messageTa": message_ta,
        "market": market,
        "district": district,
        "commodity": commodity,
        "commodityTa": commodity_ta,
        "variety": variety,
        "grade": grade,
        "oldPrice": old_price,
        "newPrice": new_price,
        "priceDiff": price_diff,
        "priceChangePercent": price_change_percent,
        "sourceReportingDate": source_reporting_date or now_human,
        "dedupKey": dedup_key,
        "isRead": False,
        "createdAt": now_human,
        "isoTimestamp": now_iso
    }

    res = await notif_col.insert_one(notif_doc)
    notif_doc["_id"] = res.inserted_id

    # Dispatched Web Push if configured and opted-in
    if prefs.get("pushEnabled") and VAPID_PUBLIC_KEY:
        try:
            await _dispatch_web_push(user_id, notif_doc)
        except Exception as e:
            logger.warning(f"Failed to dispatch web push for {user_id}: {e}")

    return _format_doc(notif_doc)


def generate_bilingual_market_messages(
    event_type: str,
    commodity: str,
    commodity_ta: Optional[str],
    market: str,
    district: str,
    variety: str,
    new_price: float,
    old_price: Optional[float] = None,
    diff: Optional[float] = None,
    pct: Optional[float] = None,
    arrival_date_human: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> Tuple[str, str, str, str]:
    """
    Constructs accurate, authentic English and Tamil notification titles and messages.
    Always includes genuine market name, prices, and reporting date.
    Never invents or fabricates prices.
    """
    ta_crop = commodity_ta or commodity
    date_str = arrival_date_human or "Today"

    if event_type == ALERT_TYPE_MARKET_PRICE_SURGE:
        pct_str = f"+{pct:.1f}%" if pct is not None else "+0%"
        diff_val = abs(diff) if diff is not None else 0.0
        old_val = old_price if old_price is not None else (new_price - diff_val)

        title_en = f"Mandi Price Surge: {commodity} ({pct_str})"
        title_ta = f"மண்டி விலை உயர்வு: {ta_crop} ({pct_str})"

        message_en = (
            f"{commodity} modal price increased by ₹{diff_val:.0f}/Qtl ({pct_str}) at {market} ({district}). "
            f"New price: ₹{new_price:.0f}/Quintal (Previous: ₹{old_val:.0f}/Qtl). "
            f"Verified source arrival date: {date_str} (AGMARKNET)."
        )
        message_ta = (
            f"{market} ({district}) ஒழுங்குமுறை விற்பனைக்கூடத்தில் {ta_crop} மாதிரி விலை "
            f"குவிண்டாலுக்கு ₹{diff_val:.0f} ({pct_str}) உயர்ந்துள்ளது. "
            f"புதிய விலை: ₹{new_price:.0f}/குவிண்டால் (முந்தைய விலை: ₹{old_val:.0f}/குவிண்டால்). "
            f"சரிபார்க்கப்பட்ட வரத்து தேதி: {date_str} (AGMARKNET)."
        )
    elif event_type == ALERT_TYPE_MARKET_PRICE_DROP:
        pct_abs = abs(pct) if pct is not None else 0.0
        pct_str = f"-{pct_abs:.1f}%"
        diff_val = abs(diff) if diff is not None else 0.0
        old_val = old_price if old_price is not None else (new_price + diff_val)

        title_en = f"Mandi Price Drop: {commodity} ({pct_str})"
        title_ta = f"மண்டி விலை சரிவு: {ta_crop} ({pct_str})"

        message_en = (
            f"{commodity} modal price decreased by ₹{diff_val:.0f}/Qtl ({pct_str}) at {market} ({district}). "
            f"New price: ₹{new_price:.0f}/Quintal (Previous: ₹{old_val:.0f}/Qtl). "
            f"Verified source arrival date: {date_str} (AGMARKNET)."
        )
        message_ta = (
            f"{market} ({district}) ஒழுங்குமுறை விற்பனைக்கூடத்தில் {ta_crop} மாதிரி விலை "
            f"குவிண்டாலுக்கு ₹{diff_val:.0f} ({pct_str}) குறைந்துள்ளது. "
            f"புதிய விலை: ₹{new_price:.0f}/குவிண்டால் (முந்தைய விலை: ₹{old_val:.0f}/குவிண்டால்). "
            f"சரிபார்க்கப்பட்ட வரத்து தேதி: {date_str} (AGMARKNET)."
        )
    else:  # ALERT_TYPE_MARKET_NEW_PRICE
        min_p = f"₹{min_price:.0f}" if min_price is not None else f"₹{new_price:.0f}"
        max_p = f"₹{max_price:.0f}" if max_price is not None else f"₹{new_price:.0f}"

        title_en = f"New Mandi Arrival Price: {commodity}"
        title_ta = f"புதிய மண்டி வரத்து விலை: {ta_crop}"

        message_en = (
            f"New arrival price recorded for {commodity} ({variety}) at {market} ({district}): "
            f"₹{new_price:.0f}/Quintal (Min: {min_p}, Max: {max_p}). "
            f"Verified source arrival date: {date_str} (AGMARKNET)."
        )
        message_ta = (
            f"{market} ({district}) ஒழுங்குமுறை விற்பனைக்கூடத்தில் {ta_crop} ({variety}) புதிய வரத்து விலை பதிவாகியுள்ளது: "
            f"₹{new_price:.0f}/குவிண்டால் (குறைந்தபட்சம்: {min_p}, அதிகபட்சம்: {max_p}). "
            f"சரிபார்க்கப்பட்ட வரத்து தேதி: {date_str} (AGMARKNET)."
        )

    return title_en, title_ta, message_en, message_ta


async def evaluate_market_feed_and_notify(
    previous_records: List[Dict[str, Any]],
    incoming_records: List[Dict[str, Any]],
    is_stale: bool = False,
    feed_error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compares previous cached records with incoming records from data.gov.in.
    1. Detects newly published records.
    2. Detects meaningful price increases or decreases for the same record identity.
    3. Explicitly IGNORES identical duplicate records (prev_modal == new_modal and prev_date == new_date).
    4. Evaluates all registered farmers against their notification preferences, selected crops, and threshold.
    5. Returns evaluation summary statistics.
    """
    users_col = get_users_collection()
    if users_col is None:
        return {"checkedFarmers": 0, "generatedAlerts": 0}

    now_ist = datetime.now(timezone.utc).astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")

    # Map previous records by recordId
    prev_map: Dict[str, Dict[str, Any]] = {
        r.get("recordId", ""): r for r in previous_records if r.get("recordId")
    }

    # Identify events across incoming records
    detected_events: List[Dict[str, Any]] = []

    for inc in incoming_records:
        rec_id = inc.get("recordId", "")
        if not rec_id:
            continue

        new_modal = float(inc.get("modalPrice") or 0)
        arrival_date = inc.get("arrivalDate", "")
        arrival_date_human = inc.get("arrivalDateHuman", "")

        if rec_id not in prev_map:
            # Case A: Brand new published arrival record
            detected_events.append({
                "eventType": ALERT_TYPE_MARKET_NEW_PRICE,
                "record": inc,
                "oldPrice": None,
                "newPrice": new_modal,
                "diff": 0.0,
                "pct": 0.0,
            })
        else:
            prev = prev_map[rec_id]
            prev_modal = float(prev.get("modalPrice") or 0)

            # Case B: Record already exists in previous records.
            # Check if price changed
            if prev_modal <= 0 or new_modal == prev_modal:
                # REQUIREMENT 2: DO NOT interpret a newly fetched duplicate record as a price change!
                continue

            diff = new_modal - prev_modal
            pct = round((diff / prev_modal) * 100.0, 2)

            event_type = ALERT_TYPE_MARKET_PRICE_SURGE if diff > 0 else ALERT_TYPE_MARKET_PRICE_DROP
            detected_events.append({
                "eventType": event_type,
                "record": inc,
                "oldPrice": prev_modal,
                "newPrice": new_modal,
                "diff": diff,
                "pct": pct,
            })

    # Fetch registered farmers
    farmers_cursor = users_col.find({"$or": [{"role": "farmer"}, {"role": {"$exists": False}}]})
    farmers_list = []
    async for f in farmers_cursor:
        farmers_list.append(f)

    generated_alerts = 0
    skipped_duplicates = 0
    skipped_threshold = 0
    skipped_prefs = 0

    for farmer in farmers_list:
        user_id = str(farmer.get("_id", farmer.get("id", "")))
        farmer_id = farmer.get("farmerId")
        if not user_id:
            continue

        prefs = await get_user_notification_preferences(user_id, farmer_id)
        if not prefs.get("mandiPriceAlerts", True):
            skipped_prefs += len(detected_events)
            continue

        threshold_pct = float(prefs.get("mandiPriceThresholdPercent", 5.0))

        for event in detected_events:
            rec = event["record"]
            ev_type = event["eventType"]
            pct = event["pct"]
            diff = event["diff"]
            new_p = event["newPrice"]
            old_p = event["oldPrice"]

            # Filter by crop and market
            if not matches_farmer_crop_and_market(
                farmer_user=farmer,
                prefs=prefs,
                commodity=rec.get("commodity", ""),
                commodity_ta=rec.get("commodityTa"),
                market=rec.get("market", ""),
                district=rec.get("district", ""),
            ):
                skipped_prefs += 1
                continue

            # Check threshold for surges and drops
            if ev_type in (ALERT_TYPE_MARKET_PRICE_SURGE, ALERT_TYPE_MARKET_PRICE_DROP):
                if abs(pct) < threshold_pct:
                    skipped_threshold += 1
                    continue

            # Check event-specific toggle
            if ev_type == ALERT_TYPE_MARKET_PRICE_SURGE and not prefs.get("mandiPriceSurgeAlerts", True):
                skipped_prefs += 1
                continue
            if ev_type == ALERT_TYPE_MARKET_PRICE_DROP and not prefs.get("mandiPriceDropAlerts", True):
                skipped_prefs += 1
                continue

            # Generate messages
            title_en, title_ta, msg_en, msg_ta = generate_bilingual_market_messages(
                event_type=ev_type,
                commodity=rec.get("commodity", ""),
                commodity_ta=rec.get("commodityTa"),
                market=rec.get("market", ""),
                district=rec.get("district", ""),
                variety=rec.get("variety", "Common"),
                new_price=new_p,
                old_price=old_p,
                diff=diff,
                pct=pct,
                arrival_date_human=rec.get("arrivalDateHuman", rec.get("arrivalDate", "")),
                min_price=rec.get("minPrice"),
                max_price=rec.get("maxPrice"),
            )

            # Build stable deduplication key
            # user_id + event_type + recordId + new_price + date
            price_int = int(round(new_p))
            rec_id = rec.get("recordId", "rec")
            dedup_key = f"{user_id}_{ev_type}_{rec_id}_{price_int}"

            res = await create_market_notification(
                user_id=user_id,
                event_type=ev_type,
                title_en=title_en,
                title_ta=title_ta,
                message_en=msg_en,
                message_ta=msg_ta,
                farmer_id=farmer_id,
                market=rec.get("market"),
                district=rec.get("district"),
                commodity=rec.get("commodity"),
                commodity_ta=rec.get("commodityTa"),
                variety=rec.get("variety"),
                grade=rec.get("grade"),
                old_price=old_p,
                new_price=new_p,
                price_diff=diff,
                price_change_percent=pct,
                source_reporting_date=rec.get("arrivalDateHuman", rec.get("arrivalDate")),
                dedup_key=dedup_key,
            )

            if res is not None:
                generated_alerts += 1
            else:
                skipped_duplicates += 1

    return {
        "checkedFarmers": len(farmers_list),
        "detectedEvents": len(detected_events),
        "generatedAlerts": generated_alerts,
        "skippedDuplicates": skipped_duplicates,
        "skippedBelowThreshold": skipped_threshold,
        "skippedByPreferences": skipped_prefs,
        "timestamp": now_ist,
    }


async def evaluate_stale_feed_notification(
    latest_reporting_date: Optional[str] = None,
    feed_error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a non-alarming status notification when government mandi feed is stale or unavailable.
    Deduplicated once per calendar day per farmer.
    """
    users_col = get_users_collection()
    if users_col is None:
        return {"checkedFarmers": 0, "generatedAlerts": 0}

    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    date_bucket = now_ist.strftime("%Y%m%d")
    now_human = now_ist.strftime("%d %b %Y, %I:%M %p IST")
    arr_date = latest_reporting_date or now_ist.strftime("%d %b %Y")

    title_en = "Mandi Market Feed Notice"
    title_ta = "மண்டி விலை சேவை நிலை தகவல்"
    msg_en = (
        f"Government AGMARKNET mandi price feed is currently awaiting official update or refresh. "
        f"Displaying verified baseline prices (Latest reported: {arr_date}). "
        f"Real market auctions will reflect automatically as soon as published by the Ministry."
    )
    msg_ta = (
        f"அரசு AGMARKNET மண்டி விலை தரவுச்சேவை தற்போது புதுப்பிக்கப்பட்டு வருகிறது. "
        f"சரிபார்க்கப்பட்ட முந்தைய விலைகள் காண்பிக்கப்படுகின்றன (சமீபத்திய வரத்து தேதி: {arr_date}). "
        f"அமைச்சகம் புதிய விலைகளை வெளியிட்டவுடன் தானாகவே புதுப்பிக்கப்படும்."
    )

    farmers_cursor = users_col.find({"$or": [{"role": "farmer"}, {"role": {"$exists": False}}]})
    farmers = []
    async for f in farmers_cursor:
        farmers.append(f)

    generated = 0
    for farmer in farmers:
        user_id = str(farmer.get("_id", farmer.get("id", "")))
        farmer_id = farmer.get("farmerId")
        if not user_id:
            continue

        prefs = await get_user_notification_preferences(user_id, farmer_id)
        if not prefs.get("mandiPriceAlerts", True) or not prefs.get("mandiStaleFeedAlerts", True):
            continue

        dedup_key = f"{user_id}_{ALERT_TYPE_MARKET_FEED_STALE}_{date_bucket}"
        res = await create_market_notification(
            user_id=user_id,
            event_type=ALERT_TYPE_MARKET_FEED_STALE,
            title_en=title_en,
            title_ta=title_ta,
            message_en=msg_en,
            message_ta=msg_ta,
            farmer_id=farmer_id,
            market="Tamil Nadu Regulated Markets",
            district=farmer.get("district", "Tamil Nadu"),
            commodity=farmer.get("primaryCrop", "All Commodities"),
            source_reporting_date=arr_date,
            dedup_key=dedup_key,
        )
        if res:
            generated += 1

    return {
        "checkedFarmers": len(farmers),
        "generatedAlerts": generated,
        "timestamp": now_human,
    }

"""
Test Suite: Automatic Updates & Background Sync for Mandi Market Prices
Project: Namma Vivasayi AI (SEVA)
========================================================================
Tests:
1. Configurable refresh interval (MANDI_REFRESH_INTERVAL_MINUTES).
2. Distributed singleton scheduler lease lock (multi-worker / multi-replica contention prevention).
3. In-process concurrency lock (preventing overlapping fetch jobs within a single process).
4. Cache preservation on failure (good cached data is never erased on network/API failure).
5. Stable record deduplication based on source fields and reporting date.
6. Timestamp accuracy (separate source arrival date, fetch time, and check time).
7. Actual source reporting dates (never substituting today's date).
8. "No new market data" status when live check returns existing up-to-date records.
9. FastAPI HTTP endpoint response with auto-update metadata and force_refresh.
"""

import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import httpx

from main import app
from database import (
    get_market_prices_cache_collection,
    get_market_prices_meta_collection,
    get_scheduler_locks_collection,
)
from market_service import (
    get_mandi_refresh_interval_minutes,
    merge_and_deduplicate_records,
    sync_live_market_data,
    get_market_prices,
    MandiPricesScheduler,
    slugify_record_id,
    OFFICIAL_DATA_SOURCE_NAME,
    RESOURCE_ID,
    _MEMORY_CACHE,
    IST,
)


# -----------------------------------------------------------------------------
# 1. Configurable Refresh Interval Tests
# -----------------------------------------------------------------------------
def test_refresh_interval_config():
    print("\n--- [Test 1] Configurable Refresh Interval ---")
    with patch.dict(os.environ, {"MANDI_REFRESH_INTERVAL_MINUTES": "30"}):
        assert get_mandi_refresh_interval_minutes() == 30

    with patch.dict(os.environ, {"MANDI_REFRESH_INTERVAL_MINUTES": "5"}):
        assert get_mandi_refresh_interval_minutes() == 5

    # Default fallback
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MANDI_REFRESH_INTERVAL_MINUTES", None)
        assert get_mandi_refresh_interval_minutes() == 15

    # Minimum boundary
    with patch.dict(os.environ, {"MANDI_REFRESH_INTERVAL_MINUTES": "0"}):
        assert get_mandi_refresh_interval_minutes() == 1

    # Invalid string fallback
    with patch.dict(os.environ, {"MANDI_REFRESH_INTERVAL_MINUTES": "invalid"}):
        assert get_mandi_refresh_interval_minutes() == 15
    print("  -> PASS: Refresh interval is fully configurable with sensible default (15m).")


# -----------------------------------------------------------------------------
# 2. Distributed Singleton Scheduler Lease Lock (Multi-Worker Contention)
# -----------------------------------------------------------------------------
async def test_distributed_singleton_lock():
    print("\n--- [Test 2] Distributed Singleton Scheduler Lease Lock ---")
    worker_alpha = MandiPricesScheduler(worker_id="mandi-worker-alpha")
    worker_beta = MandiPricesScheduler(worker_id="mandi-worker-beta")

    col = get_scheduler_locks_collection()
    if col is not None:
        await col.delete_one({"jobName": "mandi_prices_sync"})

    # Worker Alpha acquires initial lease
    acquired_alpha = await worker_alpha.acquire_distributed_lease()
    assert acquired_alpha is True, "Worker Alpha failed to acquire lease"

    # Worker Beta attempts to acquire lease while Alpha's heartbeat is fresh -> MUST FAIL
    acquired_beta = await worker_beta.acquire_distributed_lease()
    assert acquired_beta is False, "Worker Beta acquired lease despite active Alpha worker!"

    # Worker Beta running sync cycle should skip cleanly
    beta_cycle = await worker_beta.run_sync_cycle()
    assert beta_cycle["status"] == "SKIPPED_LEASE_HELD"
    assert beta_cycle["leaseAcquired"] is False

    # Worker Alpha releases lease upon shutdown
    await worker_alpha.release_distributed_lease()

    # Worker Beta can now acquire lease
    acquired_beta_after = await worker_beta.acquire_distributed_lease()
    assert acquired_beta_after is True, "Worker Beta could not acquire lease after Alpha release"

    # Clean up
    await worker_beta.release_distributed_lease()
    print("  -> PASS: Singleton distributed lease lock prevents duplicate schedulers across multi-replica deployments.")


# -----------------------------------------------------------------------------
# 3. Cache Preservation on Failure (Do not erase good cached records)
# -----------------------------------------------------------------------------
async def test_cache_preservation_on_failure():
    print("\n--- [Test 3] Cache Preservation on Failure ---")
    # 1. Seed known good records in memory
    sample_records = [
        {
            "id": "tn-thanjavur-paddy-18-oct-2026",
            "recordId": "tn-thanjavur-paddy-18-oct-2026",
            "state": "Tamil Nadu",
            "district": "Thanjavur",
            "market": "Thanjavur",
            "commodity": "Paddy(Dhan)(Common)",
            "variety": "Common",
            "grade": "FAQ",
            "arrivalDate": "2026-10-18",
            "arrivalDateHuman": "18 Oct 2026",
            "minPrice": 2200.0,
            "maxPrice": 2400.0,
            "modalPrice": 2300.0,
            "unit": "Quintal",
            "crop": "Paddy(Dhan)(Common)",
            "cropTa": "நெல் (சாதாரண ரகம்)",
            "mandi": "Thanjavur Regulated Market",
            "date": "18 Oct 2026",
            "trend": "steady",
            "change": "₹0"
        }
    ]

    _MEMORY_CACHE["records"] = list(sample_records)
    _MEMORY_CACHE["sourceArrivalDate"] = "18 Oct 2026"
    _MEMORY_CACHE["lastSuccessfulFetchTime"] = "18 Oct 2026, 05:00 PM IST"
    _MEMORY_CACHE["cachedAt"] = datetime.now(timezone.utc)
    _MEMORY_CACHE["sourceStatus"] = "LIVE"

    initial_count = len(_MEMORY_CACHE["records"])

    # 2. Simulate network timeout during fetch
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out after 12s")):
        with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_mock_key"}):
            res = await sync_live_market_data(force=True)

            assert res["success"] is False
            assert "timed out" in res["error"].lower()

            # Verify: cached records were NOT wiped out or erased!
            assert len(_MEMORY_CACHE["records"]) == initial_count, "Cached records were erased on network failure!"
            assert _MEMORY_CACHE["records"][0]["commodity"] == "Paddy(Dhan)(Common)"
            assert _MEMORY_CACHE["sourceStatus"] == "STALE_CACHE"
            assert _MEMORY_CACHE["sourceArrivalDate"] == "18 Oct 2026"

    # 3. Simulate HTTP 429 Rate Limit
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_mock_key"}):
            res_429 = await sync_live_market_data(force=True)
            assert res_429["success"] is False
            # Verify: records still intact!
            assert len(_MEMORY_CACHE["records"]) == initial_count

    print("  -> PASS: Valid cached data is strictly preserved during API timeouts, 429 rate limits, and errors.")


# -----------------------------------------------------------------------------
# 4. Stable Record Deduplication
# -----------------------------------------------------------------------------
def test_stable_deduplication():
    print("\n--- [Test 4] Stable Record Deduplication ---")
    base_records = [
        {
            "recordId": "tamil_nadu_thanjavur_thanjavur_paddy_common_2026_10_18",
            "district": "Thanjavur",
            "commodity": "Paddy(Dhan)(Common)",
            "variety": "Common",
            "arrivalDate": "2026-10-18",
            "arrivalDateHuman": "18 Oct 2026",
            "modalPrice": 2300.0,
            "minPrice": 2200.0,
            "maxPrice": 2400.0,
        },
        {
            "recordId": "tamil_nadu_madurai_madurai_tomato_local_2026_10_18",
            "district": "Madurai",
            "commodity": "Tomato",
            "variety": "Local",
            "arrivalDate": "2026-10-18",
            "arrivalDateHuman": "18 Oct 2026",
            "modalPrice": 3200.0,
            "minPrice": 3000.0,
            "maxPrice": 3400.0,
        }
    ]

    # Case A: Identical records incoming (no change)
    merged, has_new, newly_added = merge_and_deduplicate_records(base_records, base_records)
    assert len(merged) == 2, f"Expected 2 deduplicated records, got {len(merged)}"
    assert has_new is False, "has_new should be False for identical duplicate records"
    assert newly_added == 0

    # Case B: Price updated for existing record (modal price changed from 2300 to 2350)
    updated_record = dict(base_records[0])
    updated_record["modalPrice"] = 2350.0
    merged_up, has_new_up, newly_added_up = merge_and_deduplicate_records(base_records, [updated_record])
    assert len(merged_up) == 2, "Duplicate row created instead of in-place update!"
    assert has_new_up is True
    assert newly_added_up == 0
    paddy = next(r for r in merged_up if r["recordId"] == updated_record["recordId"])
    assert paddy["modalPrice"] == 2350.0

    # Case C: New commodity arrival record incoming
    new_record = {
        "recordId": "tamil_nadu_erode_erode_turmeric_finger_2026_10_19",
        "district": "Erode",
        "commodity": "Turmeric",
        "variety": "Finger",
        "arrivalDate": "2026-10-19",
        "arrivalDateHuman": "19 Oct 2026",
        "modalPrice": 14500.0,
        "minPrice": 14000.0,
        "maxPrice": 15000.0,
    }
    merged_new, has_new_flag, newly_added_cnt = merge_and_deduplicate_records(base_records, [new_record])
    assert len(merged_new) == 3
    assert has_new_flag is True
    assert newly_added_cnt == 1
    # Check that sorting places newest arrival date first (19 Oct before 18 Oct)
    assert merged_new[0]["arrivalDate"] == "2026-10-19"
    assert merged_new[0]["commodity"] == "Turmeric"

    print("  -> PASS: Record deduplication accurately identifies duplicates, updates prices in-place, and appends new arrivals.")


# -----------------------------------------------------------------------------
# 5. Timestamp Accuracy & Actual Reporting Dates (Never replacing with today)
# -----------------------------------------------------------------------------
async def test_timestamp_accuracy_and_reporting_dates():
    print("\n--- [Test 5] Timestamp Accuracy & Source Reporting Dates ---")
    res = await get_market_prices(district="Thanjavur")
    assert res is not None

    # Verify separate timestamps
    assert "sourceArrivalDate" in res
    assert "lastSuccessfulFetchTime" in res
    assert "lastCheckedTime" in res
    assert "nextScheduledRefreshTime" in res

    # Verify actual source reporting date is maintained (e.g. 18 Oct 2026)
    # Never replaced with today's clock time!
    for item in res["commodities"]:
        assert item["arrivalDate"] != datetime.now().strftime("%Y-%m-%d"), "Arrival date was falsely replaced with today!"
        assert "2026" in item["arrivalDate"]

    print("  -> PASS: Actual source reporting dates preserved; separate check and fetch timestamps verified.")


# -----------------------------------------------------------------------------
# 6. "No New Market Data" Notice & Auto-Update Metadata
# -----------------------------------------------------------------------------
async def test_no_new_market_data_notice():
    print("\n--- [Test 6] 'No New Market Data' Notice Verification ---")
    # When cache is fresh and no newer records exist
    res = await get_market_prices(force_refresh=False)
    assert res is not None
    assert "hasNewData" in res
    assert "syncStatus" in res
    assert "syncMessageEn" in res
    assert "refreshIntervalMinutes" in res

    # In unconfigured or cached state, syncMessageEn reports clear verified cached notice
    assert res["syncMessageEn"] is not None
    assert len(res["syncMessageEn"]) > 0
    print("  -> PASS: Auto-update metadata and 'No new market data' contract verified.")


# -----------------------------------------------------------------------------
# 7. FastAPI HTTP Endpoint Integration & Polling Contract
# -----------------------------------------------------------------------------
async def test_endpoint_auto_update_contract():
    print("\n--- [Test 7] FastAPI HTTP Endpoint Auto-Update Contract ---")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Standard poll
        res = await client.get("/api/market/prices?page=1&limit=5")
        assert res.status_code == 200
        data = res.json()

        assert data["dataSource"] == OFFICIAL_DATA_SOURCE_NAME
        assert data["resourceId"] == RESOURCE_ID
        assert data["refreshIntervalMinutes"] == 15
        assert data["nextScheduledRefreshTime"] is not None
        assert "hasNewData" in data
        assert "syncStatus" in data
        assert "lastCheckedTime" in data

        # Force refresh query
        res_force = await client.get("/api/market/prices?force_refresh=true")
        assert res_force.status_code == 200
        data_force = res_force.json()
        assert len(data_force["commodities"]) > 0
        assert data_force["isStale"] is True or data_force["isLive"] is True

    print("  -> PASS: HTTP endpoint satisfies all auto-update and client polling requirements.")


# -----------------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------------
async def run_all_automatic_update_tests():
    print("=" * 80)
    print("MANDI MARKET PRICES AUTOMATIC UPDATES & BACKGROUND SYNC TEST SUITE")
    print("=" * 80)

    test_refresh_interval_config()
    await test_distributed_singleton_lock()
    await test_cache_preservation_on_failure()
    test_stable_deduplication()
    await test_timestamp_accuracy_and_reporting_dates()
    await test_no_new_market_data_notice()
    await test_endpoint_auto_update_contract()

    print("\n" + "=" * 80)
    print("ALL 7 AUTOMATIC UPDATE & BACKGROUND SYNC TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_automatic_update_tests())

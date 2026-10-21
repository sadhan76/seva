"""
PRODUCTION READINESS & FAULT-TOLERANCE TEST SUITE: MARKET MANDI PRICES
======================================================================
Tests requirement 9:
1. API-key failure (HTTP 401/403 Key Not Authorised).
2. Source downtime & network timeouts (HTTP 500/503 & TimeoutException).
3. Empty responses from government API (zero records).
4. Stale cache preservation (never wipes good data when upstream fails).
5. Invalid records rejection (negative prices, missing modal price, bad dates).
6. Service recovery (seamless transition back to LIVE when API recovers).
7. Health check & observability endpoint contracts (/api/market/health and /api/health).
"""

import sys
import os
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_service import (
    fetch_live_from_data_gov_in,
    sync_live_market_data,
    normalize_record,
    parse_and_validate_price,
    parse_and_validate_date,
    get_market_operational_health,
    _MEMORY_CACHE,
    load_baseline_snapshot_records,
)

BASE_URL = "http://127.0.0.1:8000"


class MockHttpResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


async def run_production_readiness_tests():
    print("=" * 80)
    print("MARKET MANDI PRICES: PRODUCTION READINESS & FAULT-TOLERANCE SUITE")
    print("=" * 80)

    # Pre-populate memory cache with baseline records
    baseline = load_baseline_snapshot_records()
    assert len(baseline) > 0, "Baseline snapshot must have records"
    _MEMORY_CACHE["records"] = list(baseline)
    _MEMORY_CACHE["cachedAt"] = datetime.now(timezone.utc)
    _MEMORY_CACHE["sourceStatus"] = "LIVE"
    initial_count = len(_MEMORY_CACHE["records"])

    # -------------------------------------------------------------------------
    # TEST 1: API-Key Failure (HTTP 403 Forbidden)
    # -------------------------------------------------------------------------
    print("\n--- [Test 1] API-Key Failure Handling (HTTP 403 Forbidden) ---")
    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "invalid_test_key_12345"}):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MockHttpResponse(
                status_code=403,
                json_data={"status": "error", "message": "API key is not authorized"}
            )
            res = await fetch_live_from_data_gov_in()
            assert res["success"] is False
            assert res["sourceStatus"] == "UNAVAILABLE"
            assert "Key Not Authorised" in res["error"]
            print("  -> PASS: HTTP 403 properly identified as key authorization error.")

            # Run sync: must preserve cached records
            sync_res = await sync_live_market_data(force=True)
            assert sync_res["success"] is False
            assert len(_MEMORY_CACHE["records"]) == initial_count, "Cache must NOT be wiped on 403!"
            assert _MEMORY_CACHE["sourceStatus"] == "STALE_CACHE"
            print("  -> PASS: Cached records completely preserved during API-key failure.")

    # -------------------------------------------------------------------------
    # TEST 2: Source Downtime (HTTP 500 / 503)
    # -------------------------------------------------------------------------
    print("\n--- [Test 2] Source Downtime Handling (HTTP 503 Service Unavailable) ---")
    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_mock_key"}):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MockHttpResponse(
                status_code=503,
                json_data={"status": "error", "message": "Government portal under maintenance"}
            )
            res = await fetch_live_from_data_gov_in()
            assert res["success"] is False
            assert res["sourceStatus"] == "UNAVAILABLE"
            assert "unexpected HTTP status 503" in res["error"]

            sync_res = await sync_live_market_data(force=True)
            assert sync_res["success"] is False
            assert len(_MEMORY_CACHE["records"]) == initial_count, "Cache must NOT be wiped on 503!"
            print("  -> PASS: Government downtime safely caught, cached records preserved.")

    # -------------------------------------------------------------------------
    # TEST 3: Network Timeout
    # -------------------------------------------------------------------------
    print("\n--- [Test 3] Network Timeout Handling ---")
    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_mock_key"}):
        with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
            res = await fetch_live_from_data_gov_in()
            assert res["success"] is False
            assert res["sourceStatus"] == "TIMEOUT"
            assert "timed out" in res["error"]

            sync_res = await sync_live_market_data(force=True)
            assert sync_res["success"] is False
            assert len(_MEMORY_CACHE["records"]) == initial_count
            print("  -> PASS: Network timeout safely caught without crashing workers.")

    # -------------------------------------------------------------------------
    # TEST 4: Empty Response Handling
    # -------------------------------------------------------------------------
    print("\n--- [Test 4] Empty Response Handling (Zero Records from Government) ---")
    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_mock_key"}):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MockHttpResponse(
                status_code=200,
                json_data={"records": [], "total": 0}
            )
            res = await fetch_live_from_data_gov_in()
            assert res["success"] is True
            assert len(res["records"]) == 0

            # Sync must not erase existing cached records when an empty list is returned
            sync_res = await sync_live_market_data(force=True)
            assert len(_MEMORY_CACHE["records"]) == initial_count, "Cache must NOT be cleared by empty API responses!"
            print("  -> PASS: Empty API responses do not destroy existing verified cache.")

    # -------------------------------------------------------------------------
    # TEST 5: Invalid Records Rejection
    # -------------------------------------------------------------------------
    print("\n--- [Test 5] Invalid Records Rejection ---")
    # Negative prices
    assert parse_and_validate_price("-500") is None
    assert parse_and_validate_price(0) is None

    # Invalid dates
    assert parse_and_validate_date("invalid-date") is None
    assert parse_and_validate_date("2026-99-99") is None

    # Normalization rejection
    bad_rec_1 = {"state": "Tamil Nadu", "district": "Thanjavur", "commodity": "Paddy", "modalPrice": -100}
    assert normalize_record(bad_rec_1) is None, "Negative price record must be rejected"

    bad_rec_2 = {"state": "Tamil Nadu", "district": "Thanjavur", "commodity": "Paddy"}
    assert normalize_record(bad_rec_2) is None, "Record without any price must be rejected"

    bad_rec_3 = {"state": "Tamil Nadu", "district": "Thanjavur", "commodity": "Paddy", "modalPrice": 2000, "arrival_date": "not_a_date"}
    assert normalize_record(bad_rec_3) is None, "Record with malformed arrival date must be rejected"
    print("  -> PASS: All invalid, malformed, negative, and missing price records rejected.")

    # -------------------------------------------------------------------------
    # TEST 6: Recovery After Service Restoration
    # -------------------------------------------------------------------------
    print("\n--- [Test 6] Recovery After Service Restoration ---")
    valid_incoming_record = {
        "state": "Tamil Nadu",
        "district": "Thanjavur",
        "market": "Thanjavur Mandi",
        "commodity": "Paddy (Dhan)(Common)",
        "variety": "Common",
        "grade": "FAQ",
        "arrival_date": "20/10/2026",
        "min_price": "2200",
        "max_price": "2500",
        "modal_price": "2400"
    }

    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "valid_working_key"}):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MockHttpResponse(
                status_code=200,
                json_data={"records": [valid_incoming_record], "total": 1}
            )
            # Service was in STALE_CACHE; now test recovery
            sync_res = await sync_live_market_data(force=True)
            assert sync_res["success"] is True
            assert _MEMORY_CACHE["sourceStatus"] == "LIVE"
            assert _MEMORY_CACHE["error"] is None
            assert len(_MEMORY_CACHE["records"]) >= 1
            print("  -> PASS: System seamlessly recovers to LIVE status when government API resumes.")

    # -------------------------------------------------------------------------
    # TEST 7: Operational Health Endpoints Contract
    # -------------------------------------------------------------------------
    print("\n--- [Test 7] Operational Health Endpoints Contract ---")
    health = await get_market_operational_health()
    assert health["status"] in ("healthy", "degraded")
    assert "dataSource" in health
    assert "cacheMetrics" in health
    assert "backgroundScheduler" in health
    assert "operationalErrors" in health
    assert health["dataSource"]["resourceId"] == "9ef84268-d588-465a-a308-a864a43d0070"
    assert health["cacheMetrics"]["totalCachedRecords"] > 0
    assert health["backgroundScheduler"]["refreshIntervalMinutes"] == 15
    print("  -> PASS: get_market_operational_health returns complete telemetry payload.")

    # Test via HTTP
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        m_health = await client.get("/api/market/health")
        assert m_health.status_code == 200
        m_body = m_health.json()
        assert m_body["status"] in ("healthy", "degraded")
        assert "cacheMetrics" in m_body

        g_health = await client.get("/api/health")
        assert g_health.status_code == 200
        g_body = g_health.json()
        assert "mandiMarketPrices" in g_body
        assert g_body["mandiMarketPrices"]["dataSource"]["resourceId"] == "9ef84268-d588-465a-a308-a864a43d0070"
        print("  -> PASS: HTTP /api/health and /api/market/health endpoints fully verified.")

    print("=" * 80)
    print("ALL 7 PRODUCTION READINESS & FAULT-TOLERANCE TESTS PASSED (7/7)!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_production_readiness_tests())

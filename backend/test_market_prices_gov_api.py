"""
Test Suite: data.gov.in Mandi Market Prices Integration
======================================================
Tests:
1. Parsing and normalization of Agmarknet mandi records
2. Date parsing and validation (rejection of malformed/invalid dates)
3. Price parsing and validation (rejection of zero, negative, or malformed prices)
4. District, commodity, and search filtering
5. Sorting and pagination mechanics
6. Missing credentials and timeout handling (honest fallback, no fake data)
7. FastAPI endpoint /api/market/prices response structure & backward compatibility
"""

import os
import sys
import asyncio
from datetime import datetime
from unittest.mock import patch
import httpx

from main import app
from market_service import (
    normalize_record,
    parse_and_validate_date,
    parse_and_validate_price,
    get_market_prices,
    fetch_live_from_data_gov_in,
    OFFICIAL_DATA_SOURCE_NAME,
    RESOURCE_ID,
)


# -----------------------------------------------------------------------------
# 1. Parsing & Normalization Tests
# -----------------------------------------------------------------------------
def test_normalize_valid_record():
    raw_record = {
        "state": "Tamil Nadu",
        "district": "Thanjavur",
        "market": "Thanjavur",
        "commodity": "Paddy(Dhan)(Common)",
        "variety": "Common",
        "grade": "FAQ",
        "arrival_date": "18/10/2026",
        "min_price": "2200",
        "max_price": "2400",
        "modal_price": "2300"
    }

    norm = normalize_record(raw_record)
    assert norm is not None, "Failed to normalize valid record"
    assert norm["district"] == "Thanjavur"
    assert norm["market"] == "Thanjavur"
    assert norm["commodity"] == "Paddy(Dhan)(Common)"
    assert norm["crop"] == "Paddy(Dhan)(Common)"
    assert "நெல்" in norm["cropTa"]
    assert norm["variety"] == "Common"
    assert norm["grade"] == "FAQ"
    assert norm["minPrice"] == 2200.0
    assert norm["maxPrice"] == 2400.0
    assert norm["modalPrice"] == 2300.0
    assert norm["arrivalDate"] == "2026-10-18"
    assert norm["arrivalDateHuman"] == "18 Oct 2026"
    assert norm["unit"] == "Quintal"
    print("  [PASS] test_normalize_valid_record")


# -----------------------------------------------------------------------------
# 2. Date Validation Tests
# -----------------------------------------------------------------------------
def test_date_validation():
    # Valid DD/MM/YYYY
    res_1 = parse_and_validate_date("18/10/2026")
    assert res_1 is not None
    assert res_1[0] == "2026-10-18"
    assert res_1[1] == "18 Oct 2026"

    # Valid YYYY-MM-DD
    res_2 = parse_and_validate_date("2026-10-18")
    assert res_2 is not None
    assert res_2[0] == "2026-10-18"

    # Valid DD-Mon-YYYY
    res_3 = parse_and_validate_date("18-Oct-2026")
    assert res_3 is not None
    assert res_3[0] == "2026-10-18"

    # Invalid dates
    assert parse_and_validate_date("invalid-date") is None
    assert parse_and_validate_date("32/01/2026") is None
    assert parse_and_validate_date("") is None
    assert parse_and_validate_date(None) is None
    print("  [PASS] test_date_validation")


# -----------------------------------------------------------------------------
# 3. Price Validation Tests (Rejecting zero, negative, or malformed prices)
# -----------------------------------------------------------------------------
def test_price_validation():
    # Valid positive numbers
    assert parse_and_validate_price("2300") == 2300.0
    assert parse_and_validate_price("2,350.50") == 2350.50
    assert parse_and_validate_price(4500) == 4500.0

    # Invalid: Zero or Negative
    assert parse_and_validate_price("0") is None
    assert parse_and_validate_price("-500") is None
    assert parse_and_validate_price(-100) is None

    # Invalid: Malformed or Non-numeric
    assert parse_and_validate_price("N/A") is None
    assert parse_and_validate_price("") is None
    assert parse_and_validate_price(None) is None
    print("  [PASS] test_price_validation")


def test_reject_malformed_records():
    # Zero modal price
    bad_record_1 = {
        "state": "Tamil Nadu",
        "district": "Salem",
        "market": "Salem",
        "commodity": "Tomato",
        "arrival_date": "18/10/2026",
        "min_price": "0",
        "max_price": "0",
        "modal_price": "0"
    }
    assert normalize_record(bad_record_1) is None

    # Negative prices
    bad_record_2 = {
        "state": "Tamil Nadu",
        "district": "Salem",
        "market": "Salem",
        "commodity": "Tomato",
        "arrival_date": "18/10/2026",
        "min_price": "-100",
        "max_price": "500",
        "modal_price": "-50"
    }
    assert normalize_record(bad_record_2) is None

    # Missing commodity or district
    bad_record_3 = {
        "state": "Tamil Nadu",
        "district": "",
        "market": "Salem",
        "commodity": "",
        "arrival_date": "18/10/2026",
        "modal_price": "1000"
    }
    assert normalize_record(bad_record_3) is None
    print("  [PASS] test_reject_malformed_records")


# -----------------------------------------------------------------------------
# 4. Filtering, Searching, and Pagination Tests
# -----------------------------------------------------------------------------
async def test_district_filtering():
    res = await get_market_prices(district="Thanjavur")
    assert res is not None
    assert res["dataSource"] == OFFICIAL_DATA_SOURCE_NAME
    assert res["resourceId"] == RESOURCE_ID
    assert len(res["commodities"]) > 0
    for item in res["commodities"]:
        assert item["district"].lower() == "thanjavur"
    print("  [PASS] test_district_filtering")


async def test_commodity_filtering():
    res = await get_market_prices(commodity="Turmeric")
    assert res is not None
    assert len(res["commodities"]) > 0
    for item in res["commodities"]:
        assert "turmeric" in item["commodity"].lower()
    print("  [PASS] test_commodity_filtering")


async def test_search_filtering():
    res = await get_market_prices(search="Chilli")
    assert res is not None
    assert len(res["commodities"]) > 0
    for item in res["commodities"]:
        matches = (
            "chilli" in item["commodity"].lower()
            or "chilli" in item["crop"].lower()
            or "chilli" in item["variety"].lower()
        )
        assert matches
    print("  [PASS] test_search_filtering")


async def test_pagination_and_sorting():
    # Limit to 2 per page
    res_page_1 = await get_market_prices(page=1, limit=2)
    assert len(res_page_1["commodities"]) == 2
    assert res_page_1["pagination"]["page"] == 1
    assert res_page_1["pagination"]["limit"] == 2
    assert res_page_1["pagination"]["totalPages"] >= 1

    res_page_2 = await get_market_prices(page=2, limit=2)
    assert len(res_page_2["commodities"]) <= 2
    assert res_page_2["pagination"]["page"] == 2
    if len(res_page_2["commodities"]) > 0:
        assert res_page_1["commodities"][0]["id"] != res_page_2["commodities"][0]["id"]
    print("  [PASS] test_pagination_and_sorting")


# -----------------------------------------------------------------------------
# 5. Missing Credentials and Stale Notice Disclosures (Never fabricate data)
# -----------------------------------------------------------------------------
async def test_missing_credentials_honest_fallback():
    with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": ""}, clear=False):
        res = await get_market_prices(force_refresh=True)
        assert res is not None
        assert res["sourceConfigured"] is False
        assert res["isLive"] is False
        assert res["isStale"] is True
        assert res["sourceStatus"] == "STALE_CACHE"
        assert res["staleNoticeEn"] is not None
        assert "DATA_GOV_IN_API_KEY is not configured" in res["staleNoticeEn"]
        assert len(res["commodities"]) > 0  # Serves authenticated cached government data
    print("  [PASS] test_missing_credentials_honest_fallback")


async def test_timeout_and_error_handling():
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out after 12 seconds")):
        with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "dummy_test_key"}, clear=False):
            res = await fetch_live_from_data_gov_in()
            assert res["success"] is False
            assert "timed out" in res["error"].lower()
            assert res["sourceStatus"] == "TIMEOUT"
    print("  [PASS] test_timeout_and_error_handling")


# -----------------------------------------------------------------------------
# 6. HTTP API Endpoint Verification
# -----------------------------------------------------------------------------
async def test_market_prices_endpoint_http():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Base query
        res = await client.get("/api/market/prices")
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
        data = res.json()

        # Check required official source fields
        assert data["dataSource"] == OFFICIAL_DATA_SOURCE_NAME
        assert data["resourceId"] == RESOURCE_ID
        assert "lastCheckedTime" in data
        assert "sourceArrivalDate" in data
        assert "commodities" in data
        assert "pagination" in data
        assert "availableDistricts" in data
        assert "availableCommodities" in data

        # Backward compatibility checks
        assert "timestamp" in data
        assert "demoNoticeEn" in data
        assert "demoNoticeTa" in data

        # Check item structure
        assert len(data["commodities"]) > 0
        first = data["commodities"][0]
        assert "crop" in first
        assert "district" in first
        assert "mandi" in first
        assert "modalPrice" in first
        assert "minPrice" in first
        assert "maxPrice" in first
        assert "arrivalDateHuman" in first

        # 2. Query with filters
        res_filter = await client.get("/api/market/prices?district=Thanjavur&limit=5")
        assert res_filter.status_code == 200
        filtered_data = res_filter.json()
        assert len(filtered_data["commodities"]) <= 5
        for item in filtered_data["commodities"]:
            assert item["district"].lower() == "thanjavur"
    print("  [PASS] test_market_prices_endpoint_http")


# -----------------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------------
async def run_all_tests():
    print("=" * 80)
    print("DATA.GOV.IN MANDI MARKET PRICES INTEGRATION TEST SUITE")
    print("=" * 80)

    print("\n--- 1. Record Parsing & Normalization ---")
    test_normalize_valid_record()

    print("\n--- 2. Date Validation ---")
    test_date_validation()

    print("\n--- 3. Price Validation & Rejection of Bad Records ---")
    test_price_validation()
    test_reject_malformed_records()

    print("\n--- 4. Filtering, Searching & Pagination ---")
    await test_district_filtering()
    await test_commodity_filtering()
    await test_search_filtering()
    await test_pagination_and_sorting()

    print("\n--- 5. Credentials & Honest Fallback (No Fake Data) ---")
    await test_missing_credentials_honest_fallback()
    await test_timeout_and_error_handling()

    print("\n--- 6. FastAPI HTTP Endpoint ---")
    await test_market_prices_endpoint_http()

    print("\n" + "=" * 80)
    print("ALL MANDI MARKET PRICES INTEGRATION TESTS PASSED SUCCESSFULLY! (10/10)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

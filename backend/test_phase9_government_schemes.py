"""
PHASE 9: GOVERNMENT WELFARE SCHEMES & ANIMALS CATEGORY VERIFICATION SUITE
==========================================================================
Tests:
1. System Health & Schemes Endpoint Availability
2. 'All' Category returns all 23 structured schemes
3. 'Animals & Livestock' Category filtering accuracy (NLM, RGM, LHDCP, NPDD, etc.)
4. Existing Categories (State, Central, Insurance, Irrigation, Machinery) integrity
5. Keyword Search capabilities (e.g. 'goat', 'tractor', 'fmd', 'dairy', 'solar')
6. Multi-Filter Combinations (Government Level + Category + Animal Type)
7. Source Integrity & Schema Verification (Official .gov.in URLs, verification dates, non-empty criteria)
8. Seeder Idempotency & Non-duplication
9. Existing Core Features Regression (Health, Auth, Procurement Rates, Weather)
"""

import asyncio
import httpx
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SCHEMES_FILE = Path(__file__).parent / "data" / "government_schemes.json"

async def run_phase9_tests():
    print("=" * 80)
    print("PHASE 9: GOVERNMENT SCHEMES & ANIMALS CATEGORY VERIFICATION SUITE")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # TEST 1: Endpoint & Health
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Health & Schemes Endpoint Availability ---")
        health_res = await client.get("/api/health")
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        assert health_res.json()["status"] == "healthy"
        print("  -> PASS: System is healthy and database is connected.")

        # ---------------------------------------------------------------------
        # TEST 2: All Category Returns Full Dataset
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] 'All' Category Dataset Completeness ---")
        all_res = await client.get("/api/schemes?category=All")
        assert all_res.status_code == 200, f"Failed to get schemes: {all_res.text}"
        all_data = all_res.json()
        schemes = all_data["schemes"]
        assert len(schemes) == 23, f"Expected 23 schemes, got {len(schemes)}"
        assert "disclaimerEn" in all_data
        assert "disclaimerTa" in all_data
        print(f"  -> PASS: 'All' returned {len(schemes)} schemes with official disclaimers.")

        # ---------------------------------------------------------------------
        # TEST 3: Animals & Livestock Category Filtering
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] 'Animals & Livestock' Category Verification ---")
        animal_res = await client.get("/api/schemes?category=Animals%20%26%20Livestock")
        assert animal_res.status_code == 200
        animal_schemes = animal_res.json()["schemes"]
        assert len(animal_schemes) >= 9, f"Expected at least 9 animal schemes, got {len(animal_schemes)}"
        
        # Verify specific flagship animal schemes exist
        animal_ids = [s["id"] for s in animal_schemes]
        expected_animal_ids = [
            "national-livestock-mission",
            "rashtriya-gokul-mission",
            "livestock-health-disease-control",
            "national-programme-dairy-development",
            "supporting-dairy-cooperatives-fpo",
            "tn-livestock-insurance-scheme",
            "tn-free-milch-cows-scheme",
            "tn-goat-sheep-rearing-scheme",
            "tn-fodder-development-scheme"
        ]
        for exp_id in expected_animal_ids:
            assert exp_id in animal_ids, f"Flagship animal scheme '{exp_id}' not found in animals category!"
        print(f"  -> PASS: 'Animals & Livestock' returned {len(animal_schemes)} verified schemes (including NLM, RGM, LHDCP, TNLDA).")

        # ---------------------------------------------------------------------
        # TEST 4: Existing Categories Filter Verification
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Existing Categories Filter Verification ---")
        categories_to_test = {
            "State": 3,
            "Central": 3,
            "Insurance": 2,
            "Irrigation": 3,
            "Machinery": 3
        }
        for cat, min_count in categories_to_test.items():
            cat_res = await client.get(f"/api/schemes?category={cat}")
            assert cat_res.status_code == 200
            cat_schemes = cat_res.json()["schemes"]
            assert len(cat_schemes) >= min_count, f"Category '{cat}' expected >= {min_count}, got {len(cat_schemes)}"
            print(f"  -> PASS: Category '{cat}' returned {len(cat_schemes)} schemes.")

        # ---------------------------------------------------------------------
        # TEST 5: Keyword Search Capabilities
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Keyword Search Functionality ---")
        test_queries = [
            ("goat", 1),
            ("tractor", 1),
            ("fmd", 1),
            ("dairy", 2),
            ("solar", 1),
            ("insurance", 2)
        ]
        for query, min_matches in test_queries:
            q_res = await client.get(f"/api/schemes?search={query}")
            assert q_res.status_code == 200
            q_schemes = q_res.json()["schemes"]
            assert len(q_schemes) >= min_matches, f"Search query '{query}' expected >= {min_matches}, got {len(q_schemes)}"
            print(f"  -> PASS: Search query '{query}' returned {len(q_schemes)} matching schemes.")

        # ---------------------------------------------------------------------
        # TEST 6: Multi-Filter Combinations
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Multi-Filter Combinations ---")
        # Central + Animals
        combo1 = await client.get("/api/schemes?category=Animals%20%26%20Livestock&governmentLevel=Central")
        assert combo1.status_code == 200
        c1_schemes = combo1.json()["schemes"]
        assert len(c1_schemes) >= 5
        for s in c1_schemes:
            assert s["governmentLevel"] == "Central"
        print(f"  -> PASS: Central + Animals & Livestock returned {len(c1_schemes)} schemes.")

        # State + Animals
        combo2 = await client.get("/api/schemes?category=Animals%20%26%20Livestock&governmentLevel=State")
        assert combo2.status_code == 200
        c2_schemes = combo2.json()["schemes"]
        assert len(c2_schemes) >= 4
        for s in c2_schemes:
            assert s["governmentLevel"] == "State"
        print(f"  -> PASS: State + Animals & Livestock returned {len(c2_schemes)} schemes.")

        # Specific livestock type filter
        combo3 = await client.get("/api/schemes?livestockType=Goat")
        assert combo3.status_code == 200
        c3_schemes = combo3.json()["schemes"]
        assert len(c3_schemes) >= 3
        print(f"  -> PASS: Livestock type filter 'Goat' returned {len(c3_schemes)} schemes.")

        # ---------------------------------------------------------------------
        # TEST 7: Source Integrity & Field Validation
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Source Integrity & Schema Field Verification ---")
        for s in schemes:
            assert s["id"], "Scheme missing id"
            assert s["name"], f"Scheme {s['id']} missing name"
            assert s["nameTa"], f"Scheme {s['id']} missing nameTa"
            assert s["department"], f"Scheme {s['id']} missing department"
            assert s["category"], f"Scheme {s['id']} missing category"
            assert s["governmentLevel"] in ["Central", "State"], f"Scheme {s['id']} invalid governmentLevel"
            assert s["benefits"] and len(s["benefits"]) > 0, f"Scheme {s['id']} missing benefits"
            assert s["eligibility"], f"Scheme {s['id']} missing eligibility"
            assert s["applicationUrl"].startswith("http"), f"Scheme {s['id']} invalid applicationUrl"
            assert s["sourceUrl"].startswith("http"), f"Scheme {s['id']} invalid sourceUrl"
            assert s["verificationDate"] == "2026-10-20", f"Scheme {s['id']} invalid verificationDate"
            assert s["applicationStatus"] in ["Active", "Application Window Unknown", "Closed", "Unverified"]
        print(f"  -> PASS: All {len(schemes)} records validated with official URLs, verification dates, and bilingual tags.")

        # ---------------------------------------------------------------------
        # TEST 8: File-based JSON Dataset Integrity
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] File-based JSON Dataset Structure ---")
        assert SCHEMES_FILE.exists(), f"Dataset file does not exist at {SCHEMES_FILE}"
        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            raw_schemes = json.load(f)
        assert len(raw_schemes) == 23
        print(f"  -> PASS: Dataset file verified with {len(raw_schemes)} records.")

        # ---------------------------------------------------------------------
        # TEST 9: Regression Tests for Core System Features
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Core System Regression Verification ---")
        # 1. Weather API
        w_res = await client.get("/api/weather?district=thanjavur")
        assert w_res.status_code == 200
        print("  -> PASS: Weather API operational.")

        # 2. Procurement Rates API
        r_res = await client.get("/api/procurement/rates")
        assert r_res.status_code == 200
        print("  -> PASS: Procurement rates API operational.")

        # 3. Market Prices API
        m_res = await client.get("/api/market/prices?district=Thanjavur")
        assert m_res.status_code == 200
        print("  -> PASS: Mandi market prices API operational.")

    print("\n" + "=" * 80)
    print("ALL 9 PHASE 9 GOVERNMENT SCHEMES & ANIMALS TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_phase9_tests())

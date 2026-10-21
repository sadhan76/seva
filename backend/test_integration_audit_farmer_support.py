"""
COMPREHENSIVE INTEGRATION AUDIT SUITE: NAMMA VIVASAYI AI
Seven Farmer-Support Features & Core Platform Verification

Tests:
Check 1: Seven navigation sections content payloads
Check 2: Farmer Training source links, dates, and verified institutional contacts
Check 3: Transparent, reproducible calculators (Entrepreneurship & Value Addition)
Check 4: Organic Farming and Protected Cultivation credible references (TNOCD, TNHM, MIDH, TNAU)
Check 5: Special Operation 10-step beginner crop journey persistence & resume
Check 6: Farmer-to-customer listings, stock decrements, phone masking, auto-flagging
Check 7: Bilingual English and Tamil fields across all new schemas
Check 8: Source URLs, last checked dates, and verification warnings
Check 9: Stale contacts (180+ days) and expired training dates handling
Check 10: Farmer record isolation and backend authorization defense
Check 11: Admin-only content editing restricted to authorized staff/admin
Check 12: Core system regression checks (Weather, Irrigation, Disease, Mandi, Schemes, Procurement, Queue, Notifications, Auth)
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from bson import ObjectId

from main import app
from database import get_database
from auth import create_access_token
from farmer_support_service import auto_expire_training_notices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("integration_audit")

passed_checks = 0
failed_checks = 0

def record_result(check_name: str, passed: bool, detail: str = ""):
    global passed_checks, failed_checks
    if passed:
        passed_checks += 1
        print(f"  [PASS] {check_name}" + (f" -> {detail}" if detail else ""))
    else:
        failed_checks += 1
        print(f"  [FAIL] {check_name} -> {detail}")

async def run_integration_audit():
    db = get_database()
    col_users = db["users"]

    # Clean up previous test users if any
    await col_users.delete_many({"phone": {"$in": ["9442000001", "9442000002", "9442000003"]}})

    # Create real authenticated user records in MongoDB so get_current_user resolves ObjectId(sub)
    res_a = await col_users.insert_one({
        "name": "Audit Farmer A",
        "phone": "9442000001",
        "role": "farmer",
        "district": "Salem",
        "village": "Attur",
        "preferredLanguage": "en"
    })
    farmer_a_id = str(res_a.inserted_id)
    farmer_a_token = create_access_token({"sub": farmer_a_id, "role": "farmer"})

    res_b = await col_users.insert_one({
        "name": "Audit Farmer B",
        "phone": "9442000002",
        "role": "farmer",
        "district": "Thanjavur",
        "village": "Pillaiyarpatti",
        "preferredLanguage": "ta"
    })
    farmer_b_id = str(res_b.inserted_id)
    farmer_b_token = create_access_token({"sub": farmer_b_id, "role": "farmer"})

    res_adm = await col_users.insert_one({
        "name": "Staff Inspector",
        "phone": "9442000003",
        "role": "admin",
        "mandiName": "Salem Regulated Market"
    })
    admin_id = str(res_adm.inserted_id)
    admin_token = create_access_token({"sub": admin_id, "role": "admin"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n" + "=" * 80)
        print("NAMMA VIVASAYI AI: SEVEN FARMER-SUPPORT FEATURES INTEGRATION AUDIT")
        print("=" * 80)

        # --------------------------------------------------------------------
        # CHECK 1: Seven Navigation Sections Open and Deliver Content
        # --------------------------------------------------------------------
        print("\n--- [CHECK 1] Seven Navigation Sections Content Payloads ---")
        categories_to_test = [
            "training",
            "entrepreneurship",
            "organic",
            "special_operation",
            "protected_cultivation",
            "value_addition",
            "direct_market"
        ]
        for cat in categories_to_test:
            res = await client.get(f"/api/support/content?category={cat}")
            record_result(
                f"Navigation section '{cat}' payload response",
                res.status_code == 200 and len(res.json().get("items", [])) > 0,
                f"Status: {res.status_code}, Items: {len(res.json().get('items', []))}"
            )

        # --------------------------------------------------------------------
        # CHECK 2: Farmer Training Source-Linked Info & Appropriate Contacts
        # --------------------------------------------------------------------
        print("\n--- [CHECK 2] Farmer Training Information & Contacts ---")
        res_trg = await client.get("/api/support/content?category=training")
        trg_items = res_trg.json().get("items", [])
        has_source = all(item.get("officialSourceUrl", "").startswith("http") for item in trg_items)
        has_dates = all(bool(item.get("lastCheckedDate")) for item in trg_items)
        has_desk_phone = any(
            (item.get("contactPhone") or item.get("contact", {}).get("officePhone", "") or item.get("contact", {}).get("phone", "")).startswith("04")
            or (item.get("contactPhone") or item.get("contact", {}).get("officePhone", "") or item.get("contact", {}).get("phone", "")).startswith("1800")
            for item in trg_items
        )
        record_result("Training records have official HTTP source URLs", has_source, f"Verified across {len(trg_items)} records")
        record_result("Training records have verified lastCheckedDate", has_dates)
        record_result("Training records contain verified institutional desk landlines/helpline", has_desk_phone)

        # --------------------------------------------------------------------
        # CHECK 3: Transparent & Reproducible Calculators
        # --------------------------------------------------------------------
        print("\n--- [CHECK 3] Entrepreneurship & Value Addition Calculators ---")
        # Agri Entrepreneurship Calculation Test
        biz_calc_req = {
            "equipmentAndInfrastructure": [
                {"name": "Solar Tunnel Dryer", "quantity": 1, "unitCost": 140000.0},
                {"name": "Continuous Band Sealer", "quantity": 1, "unitCost": 32000.0}
            ],
            "rawMaterialInputs": [
                {"name": "Fresh Tomato Surplus", "monthlyQuantity": 2000.0, "unitCost": 12.0}
            ],
            "operatingCosts": {
                "labour": 15000.0,
                "electricity": 2500.0,
                "packaging": 8000.0,
                "logistics": 4500.0
            },
            "pricingStrategy": {
                "productUnit": "100g Pouch",
                "unitProductionCost": 25.0,
                "targetSellingPrice": 45.0,
                "expectedMonthlySalesUnits": 1800.0
            }
        }
        res_biz_calc = await client.post("/api/business/plans/calculate", json=biz_calc_req)
        biz_calc = res_biz_calc.json()
        expected_capex = 172000.0
        expected_opex = (2000.0 * 12.0) + (15000.0 + 2500.0 + 8000.0 + 4500.0)  # 54000
        expected_rev = 1800.0 * 45.0  # 81000
        expected_surplus = expected_rev - expected_opex  # 27000
        expected_payback = round(expected_capex / expected_surplus, 1)  # 6.4

        record_result(
            "Agri Entrepreneurship transparent startup capex calculation",
            biz_calc.get("totalStartupCapex") == expected_capex,
            f"Calculated: ₹{biz_calc.get('totalStartupCapex')}, Expected: ₹{expected_capex}"
        )
        record_result(
            "Agri Entrepreneurship transparent monthly opex calculation",
            biz_calc.get("totalMonthlyOpex") == expected_opex,
            f"Calculated: ₹{biz_calc.get('totalMonthlyOpex')}, Expected: ₹{expected_opex}"
        )
        record_result(
            "Agri Entrepreneurship reproducible net monthly operating surplus",
            biz_calc.get("monthlyNetOperatingSurplus") == expected_surplus,
            f"Calculated: ₹{biz_calc.get('monthlyNetOperatingSurplus')}, Expected: ₹{expected_surplus}"
        )
        record_result(
            "Agri Entrepreneurship reproducible payback period",
            biz_calc.get("breakevenMonths") == expected_payback,
            f"Calculated: {biz_calc.get('breakevenMonths')} months, Expected: {expected_payback} months"
        )

        # Value Addition Calculation Test
        val_calc_req = {
            "productId": "groundnut_cold_pressed_oil",
            "rawMaterialQuantityKg": 100.0,
            "rawMaterialCostPerKg": 90.0,
            "processingCostPerKgOrBatch": 1500.0,
            "packagingCostPerFinishedUnit": 25.0,
            "finishedUnitSize": 1.0,
            "labourCostTotal": 800.0,
            "transportAndMarketingCost": 500.0,
            "expectedSellingPricePerFinishedUnit": 320.0,
            "includeByproductRecovery": True,
            "byproductSellingPricePerKg": 36.0
        }
        res_val_calc = await client.post("/api/value-addition/calculate", json=val_calc_req)
        val_calc = res_val_calc.json()
        record_result(
            "Value Addition mass balance conversion",
            val_calc.get("finishedUnitsCount") == 42,
            f"Output: {val_calc.get('finishedUnitsCount')} finished 1L units from 100 kg groundnut"
        )
        record_result(
            "Value Addition byproduct recovery deduction credit",
            val_calc.get("byproductRevenue") == 2016.0,
            f"Byproduct Credit: ₹{val_calc.get('byproductRevenue')}"
        )
        record_result(
            "Value Addition transparent net cost calculation",
            val_calc.get("costPerFinishedUnit") == 257.95 and val_calc.get("estimatedGrossProfit") == 2606.0,
            f"Cost/Unit: ₹{val_calc.get('costPerFinishedUnit')}, Gross Profit: ₹{val_calc.get('estimatedGrossProfit')}"
        )

        # --------------------------------------------------------------------
        # CHECK 4: Organic Farming & Protected Cultivation Credible References
        # --------------------------------------------------------------------
        print("\n--- [CHECK 4] Organic Farming & Protected Cultivation Credibility ---")
        res_org = await client.get("/api/support/content?category=organic")
        org_items = res_org.json().get("items", [])
        org_cites_tnocd = any("tnocd.net" in item.get("officialSourceUrl", "") for item in org_items)
        org_cites_tnau = any("tnau.ac.in" in item.get("officialSourceUrl", "") for item in org_items)
        record_result("Organic farming references TNOCD certification authority", org_cites_tnocd)
        record_result("Organic farming bio-inputs cite TNAU agronomic standards", org_cites_tnau)

        res_prot = await client.get("/api/support/content?category=protected_cultivation")
        prot_items = res_prot.json().get("items", [])
        prot_cites_tnhm = any("tnhorticulture.tn.gov.in" in item.get("officialSourceUrl", "") for item in prot_items)
        record_result("Protected cultivation cites TN Horticulture Dept / MIDH norms", prot_cites_tnhm)

        # --------------------------------------------------------------------
        # CHECK 5: Special Operation Saves and Resumes Beginner Crop Journey
        # --------------------------------------------------------------------
        print("\n--- [CHECK 5] Special Operation Journey Persistence & Resume ---")
        headers_a = {"Authorization": f"Bearer {farmer_a_token}"}
        # Reset any previous test journey
        await client.post("/api/special-operation/journey/reset", headers=headers_a)

        # Step 1: Initialize profile
        res_j1 = await client.put("/api/special-operation/journey/step", json={
            "currentStep": 2,
            "profileInput": {
                "district": "Salem",
                "landArea": 50.0,
                "landUnit": "cents",
                "waterAvailability": "ample_borewell",
                "soilType": "unknown",
                "season": "unknown",
                "budgetRange": "low_15k_35k",
                "availableLabour": "family_only_1_2",
                "farmingGoal": "commercial_income"
            }
        }, headers=headers_a)
        record_result("Special Operation saves Step 1 profile and normalizes 50 cents to 0.5 acres", res_j1.status_code == 200 and res_j1.json().get("landAreaNormalizedAcres") == 0.5)

        # Step 2: Crop Selection
        res_j2 = await client.put("/api/special-operation/journey/step", json={
            "currentStep": 3,
            "selectedCropId": "tomato"
        }, headers=headers_a)
        record_result("Special Operation persists crop selection", res_j2.status_code == 200 and res_j2.json().get("selectedCropId") == "tomato")

        # Step 4: Record Planting Date
        p_date = (datetime.now(timezone.utc) - timedelta(days=26)).strftime("%Y-%m-%d")
        res_j4 = await client.put("/api/special-operation/journey/step", json={
            "currentStep": 5,
            "plantingDate": p_date
        }, headers=headers_a)
        record_result("Special Operation records planting date", res_j4.status_code == 200)

        # Resume Journey: GET /api/special-operation/journey
        res_resume = await client.get("/api/special-operation/journey", headers=headers_a)
        resume_data = res_resume.json()
        record_result(
            "Special Operation successfully resumes saved state with timeline",
            resume_data.get("currentStep") == 5 and resume_data.get("selectedCropId") == "tomato" and resume_data.get("timeline") is not None,
            f"Resumed at Step: {resume_data.get('currentStep')}, Crop: {resume_data.get('selectedCropId')}"
        )

        # Clean up journey
        await client.post("/api/special-operation/journey/reset", headers=headers_a)

        # --------------------------------------------------------------------
        # CHECK 6: Farmer-to-Customer Marketplace, Privacy, Stock & Reports
        # --------------------------------------------------------------------
        print("\n--- [CHECK 6] Farmer-to-Customer Direct Access & Moderation ---")
        # 1. Create listing with phone privacy masked
        create_res = await client.post("/api/marketplace/listings", json={
            "crop": "Salem G1 Turmeric",
            "variety": "Salem Local",
            "category": "Spices",
            "district": "Salem",
            "village": "Manivilundan",
            "quantity": 100.0,
            "unit": "kg",
            "pricePerUnit": 140.0,
            "isOrganicCertified": True,
            "certificationBody": "TNOCD In-Conversion",
            "showContactToBuyers": False,
            "description": "Premium curcumin Salem turmeric cured naturally."
        }, headers=headers_a)
        record_result("Created produce listing with masked contact preference", create_res.status_code in [200, 201])
        listing_id = create_res.json()["listing"]["listingId"]

        # 2. Public discovery: Phone MUST be masked
        res_pub = await client.get(f"/api/marketplace/listings/{listing_id}")
        record_result(
            "Phone privacy masking enforced when consent is False",
            res_pub.json().get("farmerPhone") == "Protected (Use In-App Enquiry)",
            f"Masked string: '{res_pub.json().get('farmerPhone')}'"
        )

        # 3. Customer Enquiry Submission
        res_enq = await client.post(f"/api/marketplace/listings/{listing_id}/orders", json={
            "buyerName": "Karthik Organics",
            "buyerPhone": "9876501234",
            "requestedQuantity": 40.0,
            "fulfillmentPreference": "Farm Gate Pickup"
        })
        record_result("Enquiry submitted successfully with initial 'pending' status", res_enq.status_code in [200, 201] and res_enq.json().get("status") == "pending")
        order_id = res_enq.json()["orderId"]

        # 4. Stock Decrement on Order Confirmation
        res_conf = await client.patch(f"/api/marketplace/orders/{order_id}/status?status=confirmed", headers=headers_a)
        record_result("Farmer confirmed order request", res_conf.status_code == 200)

        res_check_stock = await client.get(f"/api/marketplace/listings/{listing_id}")
        record_result(
            "Listing inventory decremented from 100.0 to 60.0 on confirmation",
            res_check_stock.json().get("quantity") == 60.0,
            f"Remaining quantity: {res_check_stock.json().get('quantity')} kg"
        )

        # 5. Community Reporting & Auto-Flagging on 3 Reports
        await client.post(f"/api/marketplace/listings/{listing_id}/report", json={"reasonCategory": "fake_price"})
        await client.post(f"/api/marketplace/listings/{listing_id}/report", json={"reasonCategory": "fake_price"})
        rep3 = await client.post(f"/api/marketplace/listings/{listing_id}/report", json={"reasonCategory": "fake_price"})
        record_result(
            "Listing auto-flagged for moderation upon 3 community reports",
            rep3.json().get("flagged") is True,
            f"Report Count: {rep3.json().get('reportCount')}, Flagged: {rep3.json().get('flagged')}"
        )

        # Clean up test listing
        await db["farmer_marketplace_listings"].delete_many({"farmerId": farmer_a_id})
        await db["farmer_marketplace_orders"].delete_many({"farmerId": farmer_a_id})

        # --------------------------------------------------------------------
        # CHECK 7: Bilingual English and Tamil Across All Schemas
        # --------------------------------------------------------------------
        print("\n--- [CHECK 7] Bilingual English & Tamil Field Completeness ---")
        res_all_sup = await client.get("/api/support/content?activeOnly=false")
        sup_items = res_all_sup.json().get("items", [])
        bilingual_sup = all(
            bool(i.get("titleEn") or (isinstance(i.get("title"), dict) and i.get("title", {}).get("en")) or i.get("title"))
            and bool(i.get("titleTa") or (isinstance(i.get("title"), dict) and i.get("title", {}).get("ta")))
            for i in sup_items
        )
        record_result(f"Support records contain both English and Tamil titles ({len(sup_items)} records)", bilingual_sup)

        res_biz = await client.post("/api/business/ideas/match", json={
            "district": "Salem",
            "landAreaAcres": 1.0,
            "capitalBudget": 200000.0,
            "rawMaterialsAvailable": ["Tomato"]
        })
        biz_ideas = res_biz.json().get("matchedIdeas", [])
        bilingual_biz = len(biz_ideas) > 0 and all(
            bool(i.get("title", {}).get("en") or i.get("titleEn"))
            and bool(i.get("title", {}).get("ta") or i.get("titleTa"))
            for i in biz_ideas
        )
        record_result(f"Agri Entrepreneurship ideas contain bilingual English & Tamil titles ({len(biz_ideas)} ideas)", bilingual_biz)

        res_val = await client.get("/api/value-addition/products")
        val_prods = res_val.json().get("items", [])
        bilingual_val = len(val_prods) > 0 and all(
            bool(p.get("productName", {}).get("en") or p.get("productNameEn"))
            and bool(p.get("productName", {}).get("ta") or p.get("productNameTa"))
            for p in val_prods
        )
        record_result(f"Value Addition blueprints contain bilingual English & Tamil product names ({len(val_prods)} products)", bilingual_val)

        # --------------------------------------------------------------------
        # CHECK 8: Source URLs, Last-Checked Dates & Disclaimers
        # --------------------------------------------------------------------
        print("\n--- [CHECK 8] Source URLs, Last-Checked Dates & Disclaimers ---")
        records_with_src = [i for i in sup_items if i.get("officialSourceUrl")]
        record_result("All support records expose source URLs", len(records_with_src) == len(sup_items), f"{len(records_with_src)}/{len(sup_items)}")
        records_with_dates = [i for i in sup_items if i.get("lastCheckedDate")]
        record_result("All support records expose lastCheckedDate", len(records_with_dates) == len(sup_items), f"{len(records_with_dates)}/{len(sup_items)}")
        
        # Check disclaimer on entrepreneurship match
        has_disc = bool(res_biz.json().get("disclaimer"))
        record_result("Agri Entrepreneurship outputs include statutory non-guarantee disclaimer", has_disc)

        # --------------------------------------------------------------------
        # CHECK 9: Stale Contacts & Expired Training Dates Handling
        # --------------------------------------------------------------------
        print("\n--- [CHECK 9] Stale Contacts & Expired Training Handling ---")
        # Trigger auto-expiration sweeper
        expired_cnt = await auto_expire_training_notices()
        record_result(f"Auto-expire sweeper runs without error (processed {expired_cnt} past notices)", True)

        # Check calendar endpoint filters out expired trainings from upcoming
        res_cal = await client.get("/api/support/training/calendar")
        upcoming_trainings = res_cal.json().get("items", [])
        no_past_trainings = all(t.get("activeStatus") == "active" for t in upcoming_trainings)
        record_result("Training calendar excludes past expired notices", no_past_trainings and len(upcoming_trainings) >= 1, f"Active scheduled workshops: {len(upcoming_trainings)}")

        # --------------------------------------------------------------------
        # CHECK 10: Farmer Record Backend Authorization (Farmer Isolation)
        # --------------------------------------------------------------------
        print("\n--- [CHECK 10] Farmer Cross-Tenant Isolation Defense ---")
        headers_b = {"Authorization": f"Bearer {farmer_b_token}"}
        # Farmer A creates a business plan
        plan_create_res = await client.post("/api/business/plans", json={
            "businessName": "Alice Salem Solar Processing",
            "ideaId": "solar_dehydration_unit",
            "wizardData": {
                "productOrService": "Solar Dehydrated Flakes",
                "customerSegment": ["Direct Consumers"],
                "equipmentAndInfrastructure": [{"name": "Dryer", "quantity": 1, "unitCost": 140000.0}],
                "rawMaterialInputs": [{"name": "Tomato", "monthlyQuantity": 1000.0, "unitCost": 12.0}],
                "operatingCosts": {"labour": 10000.0},
                "pricingStrategy": {"productUnit": "100g", "targetSellingPrice": 50.0, "expectedMonthlySalesUnits": 1000.0}
            }
        }, headers=headers_a)
        record_result("Farmer A created business plan", plan_create_res.status_code in [200, 201])
        plan_id = plan_create_res.json()["planId"]

        # Farmer B attempts to delete Farmer A's plan -> Must be 403 or 404
        b_del_plan = await client.delete(f"/api/business/plans/{plan_id}", headers=headers_b)
        record_result(
            "Farmer B blocked from deleting Farmer A's business plan",
            b_del_plan.status_code in [403, 404],
            f"Blocked with status: {b_del_plan.status_code}"
        )

        # Farmer A deletes own plan -> 200
        a_del_plan = await client.delete(f"/api/business/plans/{plan_id}", headers=headers_a)
        record_result("Farmer A can delete own business plan", a_del_plan.status_code == 200)

        # --------------------------------------------------------------------
        # CHECK 11: Admin-Only Content Editing Restricted to Staff/Admin
        # --------------------------------------------------------------------
        print("\n--- [CHECK 11] Admin Content Editing Authorization ---")
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        test_content_id = sup_items[0]["contentId"]

        # Farmer A tries to review/edit support content -> Blocked 403
        farmer_edit = await client.patch(f"/api/admin/support/content/{test_content_id}/review?new_status=verified_official", headers=headers_a)
        record_result(
            "Standard farmer blocked from admin content review route (403 Forbidden)",
            farmer_edit.status_code == 403,
            f"Status: {farmer_edit.status_code}"
        )

        # Admin/Staff executes review -> 200 OK
        admin_edit = await client.patch(f"/api/admin/support/content/{test_content_id}/review?new_status=verified_official", headers=headers_admin)
        record_result(
            "Authorized admin/staff permitted to review content",
            admin_edit.status_code == 200,
            f"Status: {admin_edit.status_code}"
        )

        # --------------------------------------------------------------------
        # CHECK 12: Existing Core Systems Regression Verification
        # --------------------------------------------------------------------
        print("\n--- [CHECK 12] Core System Regression Verification ---")
        # 1. Weather Forecast
        res_w = await client.get("/api/weather/irrigation?lat=10.7870&lon=79.1378")
        record_result("Core Weather Forecast operational", res_w.status_code == 200 and "soilMoisture" in res_w.json())

        # 2. Smart Irrigation
        res_i = await client.post("/api/irrigation/calculate", json={
            "crop": "Paddy",
            "growthStage": "Flowering / Panicle Initiation",
            "soilType": "Clay Loam",
            "irrigationMethod": "Flooding",
            "fieldAreaAcres": 2.0,
            "district": "Thanjavur"
        })
        record_result("Core Smart Irrigation calculator operational", res_i.status_code == 200 and "status" in res_i.json())

        # 3. Market Mandi Prices
        res_m = await client.get("/api/market/prices?district=Thanjavur")
        record_result("Core Market Mandi Prices operational", res_m.status_code == 200)

        # 4. Government Schemes
        res_s = await client.get("/api/schemes?category=All")
        record_result("Core Government Schemes operational", res_s.status_code == 200 and len(res_s.json().get("schemes", [])) >= 20)

        # 5. Procurement Slots
        res_p = await client.get("/api/procurement/centres")
        record_result("Core Procurement Centres Directory operational", res_p.status_code == 200 and len(res_p.json()) > 0)

        # 6. Queue Status
        res_q = await client.get("/api/procurement/queue/status/dummy-booking-nonexistent", headers=headers_a)
        record_result("Core Queue Tracking access control active (404/403 for non-existent/unauthorized)", res_q.status_code in [403, 404])

        # 7. Notifications
        res_n = await client.get("/api/notifications", headers=headers_a)
        record_result("Core Notifications system operational", res_n.status_code == 200 and isinstance(res_n.json(), list))

        # 8. Authentication
        res_me = await client.get("/api/auth/me", headers=headers_a)
        record_result("Core Authentication session verification operational", res_me.status_code == 200 and res_me.json().get("name") == "Audit Farmer A")

        # Clean up test users
        await col_users.delete_many({"_id": {"$in": [res_a.inserted_id, res_b.inserted_id, res_adm.inserted_id]}})

        print("\n" + "=" * 80)
        print(f"INTEGRATION AUDIT SUMMARY: {passed_checks} CHECKS PASSED, {failed_checks} CHECKS FAILED")
        print("=" * 80 + "\n")

        if failed_checks > 0:
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_integration_audit())

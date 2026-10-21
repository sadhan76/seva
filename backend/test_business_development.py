"""
COMPREHENSIVE AUTOMATED TEST SUITE: BUSINESS DEVELOPMENT & DIRECT MARKETPLACE
Tests for:
1. Module A: Agri Entrepreneurship idea matching, financial calculations, 8-step planning wizard CRUD.
2. Module B: Value-Added Products catalog, yield loss calculation, byproduct recovery, unit economics.
3. Module C: Farmer Marketplace listing creation with contact consent, privacy protection (phone masking),
   stock updates upon confirmation, auto-expiry, anti-spam, community reporting, and ownership isolation.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from database import init_database_indexes, get_farmer_marketplace_collection, get_farmer_marketplace_orders_collection, get_farmer_business_plans_collection
from models import (
    BusinessIdeaMatchRequest,
    BusinessPlanWizardData,
    BusinessPlanCreateRequest,
    BusinessPlanUpdateRequest,
    ValueAdditionCalculationRequest,
    MarketplaceListingReportRequest,
)
from business_dev_service import (
    match_business_ideas,
    calculate_business_plan_finances,
    create_farmer_business_plan,
    get_farmer_business_plans,
    get_farmer_business_plan_by_id,
    update_farmer_business_plan,
    delete_farmer_business_plan,
    get_value_addition_products,
    get_value_addition_product_by_id,
    calculate_value_addition_profitability,
)
from marketplace_service import (
    create_produce_listing,
    get_marketplace_listings,
    get_listing_by_id,
    check_and_expire_listings,
    create_listing_order_request,
    update_order_request_status,
    report_marketplace_listing,
    update_farmer_listing,
    delete_farmer_listing,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_business_dev")

FARMER_ALICE = {
    "id": "farmer_alice_salem",
    "userId": "farmer_alice_salem",
    "name": "Alice Selvaraj",
    "phone": "9876543210",
    "district": "Salem",
    "village": "Attur",
    "role": "farmer"
}

FARMER_BOB = {
    "id": "farmer_bob_erode",
    "userId": "farmer_bob_erode",
    "name": "Bob Murugan",
    "phone": "9123456780",
    "district": "Erode",
    "village": "Bhavani",
    "role": "farmer"
}

passed_tests = 0
failed_tests = 0


def assert_test(condition: bool, description: str):
    global passed_tests, failed_tests
    if condition:
        passed_tests += 1
        print(f" [PASS] {description}")
    else:
        failed_tests += 1
        print(f" [FAIL] {description}")


async def run_all_tests():
    global passed_tests, failed_tests
    print("\n" + "=" * 80)
    print("STARTING TEST SUITE: AGRI-ENTREPRENEURSHIP, VALUE-ADDITION & DIRECT MARKETPLACE")
    print("=" * 80)

    await init_database_indexes()

    # ------------------------------------------------------------------------
    # 1. MODULE A: AGRI ENTREPRENEURSHIP
    # ------------------------------------------------------------------------
    print("\n--- TEST GROUP 1: Agri Entrepreneurship Matching & Planning Wizard ---")

    # Test 1.1: Match business ideas with high tomato/horticulture synergy
    match_req = BusinessIdeaMatchRequest(
        interests=["value_addition", "solar_drying"],
        skills=["farming_experience", "packaging"],
        locationDistrict="Salem",
        investmentBudget=180000.0,
        availableProduce=["Tomato", "Tapioca"],
        landOrSpaceAvailable="shed_200sqft"
    )
    match_resp = match_business_ideas(match_req)
    assert_test(len(match_resp.matchedIdeas) >= 4, f"Matched {len(match_resp.matchedIdeas)} business blueprints")
    top_idea = match_resp.matchedIdeas[0]
    assert_test("solar" in top_idea.ideaId or "bio" in top_idea.ideaId or top_idea.matchScore >= 75,
                f"Top matched idea '{top_idea.ideaId}' scored {top_idea.matchScore} with relevant reasons")
    assert_test(bool(top_idea.title.en and top_idea.title.ta), "Top idea has bilingual English & Tamil titles")
    assert_test("guaranteed" in top_idea.nonGuaranteeDisclaimer.lower(), "Includes mandatory non-guarantee disclaimer")
    assert_test(len(top_idea.officialResources) >= 1, "Links official training/incubation (TNAU DABD / EDII-TN)")

    # Test 1.2: Financial Calculation Engine
    equipment = [
        {"name": "Solar Tunnel Dryer", "quantity": 1, "unitCost": 140000.0},
        {"name": "Continuous Band Sealer", "quantity": 1, "unitCost": 32000.0}
    ]
    raw_materials = [
        {"name": "Fresh Tomato Surplus", "monthlyQuantity": 2000.0, "unitCost": 12.0}
    ]
    opex = {
        "labour": 15000.0,
        "electricity": 2500.0,
        "packaging": 8000.0,
        "logistics": 4500.0
    }
    pricing = {
        "productUnit": "100g Pouch",
        "unitProductionCost": 25.0,
        "targetSellingPrice": 45.0,
        "expectedMonthlySalesUnits": 1800.0
    }
    calc_res = calculate_business_plan_finances(equipment, raw_materials, opex, pricing)
    assert_test(calc_res.totalStartupCapex == 172000.0, f"Calculated capex ₹{calc_res.totalStartupCapex:,.2f} == ₹172,000.00")
    expected_monthly_opex = (2000 * 12) + (15000 + 2500 + 8000 + 4500)
    assert_test(calc_res.totalMonthlyOpex == expected_monthly_opex, f"Calculated monthly opex ₹{calc_res.totalMonthlyOpex:,.2f} == ₹54,000.00")
    expected_rev = 1800.0 * 45.0
    assert_test(calc_res.monthlyGrossRevenue == expected_rev, f"Calculated gross revenue ₹{calc_res.monthlyGrossRevenue:,.2f} == ₹81,000.00")
    assert_test(calc_res.monthlyNetOperatingSurplus > 0, f"Net operating surplus is positive: ₹{calc_res.monthlyNetOperatingSurplus:,.2f}")
    assert_test(calc_res.breakevenMonths > 0 and calc_res.breakevenMonths < 24, f"Breakeven payback is reasonable: {calc_res.breakevenMonths} months")

    # Test 1.3: Farmer Business Plan CRUD & Isolation
    wizard_data = BusinessPlanWizardData(
        productOrService="Solar Dried Tomato Flakes & Powder",
        customerSegment=["Bakeries", "Urban Direct Consumers"],
        equipmentAndInfrastructure=equipment,
        rawMaterialInputs=raw_materials,
        operatingCosts=opex,
        pricingStrategy=pricing,
        distributionChannels=["Uzhavar Sandhai", "AgriBharat Marketplace"],
        risksAndMitigations=[{"risk": "Rainy weather", "mitigation": "Backup LPG tray heating"}],
        regulatoryChecklist={"udyam": True, "fssai": False},
        nextStepsRoadmap=[{"stepNumber": 1, "title": "Apply for FSSAI Basic", "timeline": "Week 1"}]
    )
    plan_create = BusinessPlanCreateRequest(
        businessName="Attur Solar Agro Foods",
        ideaId="solar_dehydration_unit",
        wizardData=wizard_data
    )
    created_plan = await create_farmer_business_plan(FARMER_ALICE, plan_create)
    assert_test(bool(created_plan.planId), f"Created plan with planId: {created_plan.planId}")
    assert_test(created_plan.farmerId == FARMER_ALICE["id"], "Plan bound to Farmer Alice")

    # Retrieve Alice's plans
    alice_plans = await get_farmer_business_plans(FARMER_ALICE["id"])
    assert_test(len(alice_plans) >= 1, f"Retrieved {len(alice_plans)} plans for Alice")

    # Retrieve single plan
    fetched_plan = await get_farmer_business_plan_by_id(created_plan.planId, FARMER_ALICE["id"])
    assert_test(fetched_plan is not None and fetched_plan.businessName == "Attur Solar Agro Foods", "Fetched plan details match")

    # Unauthorized access: Farmer Bob cannot view or edit Alice's plan
    bob_attempt = await get_farmer_business_plan_by_id(created_plan.planId, FARMER_BOB["id"])
    assert_test(bob_attempt is None, "Farmer Bob cannot view Alice's business plan (Ownership isolation)")

    # Update plan
    updated_plan = await update_farmer_business_plan(
        created_plan.planId,
        FARMER_ALICE["id"],
        BusinessPlanUpdateRequest(businessName="Attur Solar Agro Foods (Export Grade)")
    )
    assert_test(updated_plan is not None and updated_plan.businessName == "Attur Solar Agro Foods (Export Grade)", "Updated plan title")

    # Unauthorized delete
    bob_delete = await delete_farmer_business_plan(created_plan.planId, FARMER_BOB["id"])
    assert_test(bob_delete is False, "Farmer Bob cannot delete Alice's business plan")

    # Authorized delete
    alice_delete = await delete_farmer_business_plan(created_plan.planId, FARMER_ALICE["id"])
    assert_test(alice_delete is True, "Farmer Alice successfully deleted her business plan")

    # ------------------------------------------------------------------------
    # 2. MODULE B: VALUE-ADDED PRODUCTS
    # ------------------------------------------------------------------------
    print("\n--- TEST GROUP 2: Value-Added Products Catalog & Costing Calculator ---")

    # Test 2.1: Catalog Retrieval and Filtering
    all_products = get_value_addition_products()
    assert_test(len(all_products) >= 5, f"Catalog contains {len(all_products)} verified products")

    tomato_prods = get_value_addition_products(raw_material="Tomato")
    assert_test(len(tomato_prods) >= 1 and tomato_prods[0].rawMaterial == "Tomato", "Filtered products by raw material 'Tomato'")

    cold_press_prods = get_value_addition_products(method_category="cold_extraction")
    assert_test(len(cold_press_prods) >= 1 and cold_press_prods[0].productId == "groundnut_cold_pressed_oil",
                "Filtered products by method category 'cold_extraction'")

    # Test 2.2: Product Details & Authoritative References
    puree_blueprint = get_value_addition_product_by_id("tomato_puree")
    assert_test(puree_blueprint is not None, "Retrieved Tomato Puree blueprint")
    assert_test("TNAU" in puree_blueprint.authoritativeReference.get("institute", ""), "Cites authoritative reference from TNAU PHTC")
    assert_test(puree_blueprint.rawMaterialToFinishedRatio == 0.62, "Accurate mass conversion ratio: 0.62 (38% moisture/skin loss)")
    assert_test(len(puree_blueprint.standardOperatingProcedure) >= 4, "Includes step-by-step Standard Operating Procedure")
    assert_test(len(puree_blueprint.trainingProviders) >= 1, "Includes verified training providers with contact")

    # Test 2.3: Precision Costing & Profitability Calculation
    # Cold-Pressed Groundnut Oil: 100 kg kernels @ ₹90/kg, 42% oil yield (42 L) + 56% cake byproduct (56 kg @ ₹36/kg)
    va_calc_req = ValueAdditionCalculationRequest(
        productId="groundnut_cold_pressed_oil",
        rawMaterialQuantityKg=100.0,
        rawMaterialCostPerKg=90.0,
        processingCostPerKgOrBatch=1500.0,  # Chekku power & wood wear
        packagingCostPerFinishedUnit=25.0,  # 1L food-grade tin/bottle
        finishedUnitSize=1.0,               # 1 Litre pack
        labourCostTotal=800.0,
        transportAndMarketingCost=500.0,
        expectedSellingPricePerFinishedUnit=320.0,
        includeByproductRecovery=True,
        byproductSellingPricePerKg=36.0
    )
    va_calc_res = calculate_value_addition_profitability(va_calc_req)

    assert_test(va_calc_res.finishedUnitsCount == 42, f"Produced {va_calc_res.finishedUnitsCount} finished 1L units from 100 kg groundnut")
    expected_byproduct_qty = 56.0
    expected_byproduct_rev = 56.0 * 36.0  # ₹2,016
    assert_test(va_calc_res.byproductQuantityKg == expected_byproduct_qty, f"Byproduct groundnut cake {va_calc_res.byproductQuantityKg} kg")
    assert_test(va_calc_res.byproductRevenue == expected_byproduct_rev, f"Byproduct cake revenue ₹{va_calc_res.byproductRevenue:,.2f}")

    total_exp = (100 * 90) + 1500 + (42 * 25) + 800 + 500  # 9000 + 1500 + 1050 + 800 + 500 = 12,850
    assert_test(va_calc_res.totalExpenses["total"] == total_exp, f"Total calculated expenses ₹{va_calc_res.totalExpenses['total']:,.2f} == ₹{total_exp:,.2f}")

    finished_rev = 42 * 320.0  # ₹13,440
    gross_rev = finished_rev + expected_byproduct_rev  # 13440 + 2016 = ₹15,456
    assert_test(va_calc_res.totalGrossRevenue == gross_rev, f"Total gross revenue ₹{va_calc_res.totalGrossRevenue:,.2f} == ₹{gross_rev:,.2f}")
    assert_test(va_calc_res.estimatedGrossProfit == (gross_rev - total_exp), f"Gross profit ₹{va_calc_res.estimatedGrossProfit:,.2f} is positive")
    assert_test(va_calc_res.costPerFinishedUnit < 320.0, f"Net unit cost ₹{va_calc_res.costPerFinishedUnit:,.2f} gives healthy margin below selling price")

    # ------------------------------------------------------------------------
    # 3. MODULE C: FARMER-TO-CUSTOMER DIRECT ACCESS (MARKETPLACE)
    # ------------------------------------------------------------------------
    print("\n--- TEST GROUP 3: Direct Marketplace, Privacy, Stock & Moderation ---")

    # Test 3.1: Listing Creation with Contact Consent = False
    listing_data_private = {
        "crop": "Organic Country Tomato",
        "variety": "PKM-1",
        "category": "Vegetables",
        "district": "Salem",
        "village": "Attur",
        "quantity": 500.0,
        "unit": "kg",
        "pricePerUnit": 28.0,
        "isOrganicCertified": True,
        "harvestDate": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
        "availableUntil": (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d"),
        "fulfillmentModes": ["Farm Gate Pickup", "Local Delivery within District"],
        "serviceArea": "Salem & Attur taluks within 25 km",
        "photoUrls": ["https://images.unsplash.com/photo-1592924357228-91a4daadcfea"],
        "showContactToBuyers": False,  # Explicit consent NOT given
        "description": "Naturally ripened, vine-fresh local country tomatoes."
    }
    created_listing_private = await create_produce_listing(FARMER_ALICE, listing_data_private)
    assert_test(bool(created_listing_private.get("listingId")), "Created private listing for Alice")

    # Test 3.2: Listing Creation with Contact Consent = True
    listing_data_public = {
        "crop": "Cold-Pressed Groundnut Oil",
        "variety": "VRI-2",
        "category": "Value Added",
        "district": "Salem",
        "village": "Attur",
        "quantity": 100.0,
        "unit": "Litres",
        "pricePerUnit": 320.0,
        "isOrganicCertified": False,
        "harvestDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "availableUntil": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "fulfillmentModes": ["Farm Gate Pickup", "Courier Dispatch"],
        "serviceArea": "All Tamil Nadu via courier",
        "photoUrls": ["https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5"],
        "showContactToBuyers": True,  # Explicit consent given
        "description": "Pure unrefined wood-pressed groundnut oil."
    }
    created_listing_public = await create_produce_listing(FARMER_ALICE, listing_data_public)
    assert_test(bool(created_listing_public.get("listingId")), "Created public contact listing for Alice")

    # Test 3.3: Verify Public Directory Privacy Masking
    public_directory = await get_marketplace_listings(district="Salem", limit=50)
    alice_private_in_dir = next((x for x in public_directory["items"] if x["listingId"] == created_listing_private["listingId"]), None)
    alice_public_in_dir = next((x for x in public_directory["items"] if x["listingId"] == created_listing_public["listingId"]), None)

    assert_test(alice_private_in_dir is not None, "Private listing visible in marketplace directory")
    assert_test(alice_private_in_dir["farmerPhone"] == "Protected (Use In-App Enquiry)",
                f"Phone masked for private listing: {alice_private_in_dir['farmerPhone']}")

    assert_test(alice_public_in_dir is not None, "Public listing visible in marketplace directory")
    assert_test(alice_public_in_dir["farmerPhone"] == FARMER_ALICE["phone"],
                f"Phone visible when explicit consent granted: {alice_public_in_dir['farmerPhone']}")

    # Test 3.4: Auto-Expiry of Past Listings
    # Seed an expired listing
    col_listings = get_farmer_marketplace_collection()
    expired_listing_doc = {
        "listingId": "MKT-TEST-EXPIRED-01",
        "farmerId": FARMER_ALICE["id"],
        "farmerName": FARMER_ALICE["name"],
        "crop": "Perishable Guava",
        "category": "Fruits",
        "district": "Salem",
        "quantity": 50.0,
        "unit": "kg",
        "pricePerUnit": 40.0,
        "availableUntil": (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d"),  # Expired 2 days ago
        "listingStatus": "active",
        "showContactToBuyers": False,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    }
    await col_listings.delete_many({"listingId": "MKT-TEST-EXPIRED-01"})
    await col_listings.insert_one(expired_listing_doc)

    expired_count = await check_and_expire_listings()
    assert_test(expired_count >= 1, f"Auto-expiry updated {expired_count} past listings")

    refreshed_expired = await col_listings.find_one({"listingId": "MKT-TEST-EXPIRED-01"})
    assert_test(refreshed_expired.get("listingStatus") == "expired", "Listing status transitioned from 'active' to 'expired'")

    # Clean up test expired listing
    await col_listings.delete_one({"listingId": "MKT-TEST-EXPIRED-01"})

    # Test 3.5: Order Request & Anti-Spam Protection
    order_buyer = {
        "buyerName": "Karthik Restaurant",
        "buyerPhone": "9840123456",
        "requestedQuantity": 80.0,
        "fulfillmentPreference": "Farm Gate Pickup",
        "message": "Need delivery for morning cooking"
    }
    order_1 = await create_listing_order_request(created_listing_public["listingId"], order_buyer)
    assert_test(bool(order_1.get("orderId")), f"Created order enquiry: {order_1.get('orderId')}")
    assert_test(order_1.get("status") == "pending", "Initial order status is 'pending' (distinguished from confirmed)")

    # Anti-spam check: simulate 4 more orders, 6th should be rejected
    col_orders = get_farmer_marketplace_orders_collection()
    for i in range(4):
        await create_listing_order_request(created_listing_public["listingId"], {
            "buyerName": "Karthik Restaurant",
            "buyerPhone": "9840123456",
            "requestedQuantity": 10.0,
            "fulfillmentPreference": "Farm Gate Pickup"
        })

    spam_caught = False
    try:
        await create_listing_order_request(created_listing_public["listingId"], {
            "buyerName": "Karthik Restaurant",
            "buyerPhone": "9840123456",
            "requestedQuantity": 10.0,
            "fulfillmentPreference": "Farm Gate Pickup"
        })
    except ValueError as ve:
        if "spam" in str(ve).lower():
            spam_caught = True
    assert_test(spam_caught, "Anti-spam throttles buyer with > 5 requests in short window")

    # Test 3.6: Stock Updates on Order Confirmation
    # Current stock is 100.0 Litres. Confirming order_1 (80.0 Litres) should leave 20.0 Litres.
    confirmed_order = await update_order_request_status(FARMER_ALICE, order_1["orderId"], "confirmed")
    assert_test(confirmed_order["status"] == "confirmed", "Order status transitioned to 'confirmed'")

    listing_after_confirm = await col_listings.find_one({"listingId": created_listing_public["listingId"]})
    assert_test(listing_after_confirm["quantity"] == 20.0, f"Inventory decremented: 100.0 -> {listing_after_confirm['quantity']} Litres")
    assert_test(listing_after_confirm["listingStatus"] == "active", "Listing remains 'active' with remaining stock")

    # Place and confirm another order for 25.0 Litres -> should deplete to 0.0 and shift to 'out_of_stock'
    order_deplete = await create_listing_order_request(created_listing_public["listingId"], {
        "buyerName": "Saravana Bhavan",
        "buyerPhone": "9998887776",
        "requestedQuantity": 25.0,
        "fulfillmentPreference": "Farm Gate Pickup"
    })
    await update_order_request_status(FARMER_ALICE, order_deplete["orderId"], "confirmed")

    listing_depleted = await col_listings.find_one({"listingId": created_listing_public["listingId"]})
    assert_test(listing_depleted["quantity"] == 0.0, f"Stock depleted to {listing_depleted['quantity']}")
    assert_test(listing_depleted["listingStatus"] == "out_of_stock", "Listing automatically shifted to 'out_of_stock'")

    # Test 3.7: Community Reporting & Auto-Flagging Threshold
    report_res_1 = await report_marketplace_listing(created_listing_private["listingId"], {"reasonCategory": "fake_price"})
    assert_test(report_res_1["reportCount"] == 1 and not report_res_1["flagged"], "Report 1 recorded without auto-flag")

    report_res_2 = await report_marketplace_listing(created_listing_private["listingId"], {"reasonCategory": "fake_price"})
    assert_test(report_res_2["reportCount"] == 2 and not report_res_2["flagged"], "Report 2 recorded without auto-flag")

    report_res_3 = await report_marketplace_listing(created_listing_private["listingId"], {"reasonCategory": "spam"})
    assert_test(report_res_3["reportCount"] == 3 and report_res_3["flagged"], "Report 3 triggers auto-flagging for moderation")

    flagged_listing = await col_listings.find_one({"listingId": created_listing_private["listingId"]})
    assert_test(flagged_listing.get("adminFlagged") is True and flagged_listing.get("listingStatus") == "flagged",
                "Listing hidden from active directory after community reports")

    # Test 3.8: Strict Ownership Isolation on Listings
    unauthorized_edit = False
    try:
        await update_farmer_listing(FARMER_BOB, created_listing_public["listingId"], {"pricePerUnit": 150.0})
    except PermissionError:
        unauthorized_edit = True
    assert_test(unauthorized_edit, "Farmer Bob cannot edit Farmer Alice's produce listing (403 Permission Denied)")

    unauthorized_del = False
    try:
        await delete_farmer_listing(FARMER_BOB, created_listing_public["listingId"])
    except PermissionError:
        unauthorized_del = True
    assert_test(unauthorized_del, "Farmer Bob cannot delete Farmer Alice's produce listing (403 Permission Denied)")

    # Cleanup test listings
    await col_listings.delete_many({"farmerId": FARMER_ALICE["id"]})
    await col_orders.delete_many({"farmerId": FARMER_ALICE["id"]})

    print("\n" + "=" * 80)
    print(f"AUTOMATED VERIFICATION SUMMARY: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=" * 80 + "\n")

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

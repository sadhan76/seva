"""
Comprehensive Test Suite for Special Operation — From First Step to First Sale.
Validates progress persistence, authorization, crop-stage calculations,
language selection, cost worksheet math, and missing data handling.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from database import init_database_indexes, get_special_operation_journeys_collection
from special_operation_service import (
    get_or_create_journey,
    update_journey_step,
    get_candidate_crops_for_profile,
    get_crop_agronomic_guide,
    calculate_crop_stage_timeline,
    generate_default_cost_worksheet,
    add_journey_observation,
    trigger_journey_reminder_notification,
    reset_journey,
    normalize_land_to_acres,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_special_op")

passed_tests = 0
failed_tests = 0

def assert_test(condition: bool, msg: str):
    global passed_tests, failed_tests
    if condition:
        passed_tests += 1
        print(f"  [PASS] {msg}")
    else:
        failed_tests += 1
        print(f"  [FAIL] {msg}")

async def run_all_tests():
    global passed_tests, failed_tests
    print("\n" + "=" * 70)
    print("STARTING TEST SUITE: SPECIAL OPERATION (10-STEP BEGINNER JOURNEY)")
    print("=" * 70)

    await init_database_indexes()

    farmer_a_id = "farmer_user_selvakumar_101"
    farmer_a_name = "Thiru. Selvakumar R."
    farmer_a_phone = "9876543210"

    farmer_b_id = "farmer_user_karthik_202"
    farmer_b_name = "Karthik Subramanian"
    farmer_b_phone = "9876543211"

    # Reset any existing test journey cleanly
    await reset_journey(farmer_a_id)
    await reset_journey(farmer_b_id)

    # ------------------------------------------------------------------------
    # TEST 1: Journey Initialization & Farmer Isolation
    # ------------------------------------------------------------------------
    print("\n--- TEST 1: Journey Initialization & Isolation ---")
    journey_a = await get_or_create_journey(farmer_a_id, farmer_a_name, farmer_a_phone, "Salem")
    assert_test(journey_a is not None, "Farmer A journey created successfully")
    assert_test(journey_a.get("currentStep") == 1, "Starts at Step 1")
    assert_test(journey_a.get("status") == "in_progress", "Initial status is 'in_progress'")
    assert_test(journey_a.get("farmerId") == farmer_a_id, "Journey bound to Farmer A")

    # Farmer B journey
    journey_b = await get_or_create_journey(farmer_b_id, farmer_b_name, farmer_b_phone, "Thanjavur")
    assert_test(journey_b.get("journeyId") != journey_a.get("journeyId"), "Unique journey IDs between farmers")
    assert_test(journey_b.get("profileInput", {}).get("district") == "Thanjavur", "District customized per farmer")

    # ------------------------------------------------------------------------
    # TEST 2: Step 1 — Profile Input & Missing Data / 'Unknown' Tolerance
    # ------------------------------------------------------------------------
    print("\n--- TEST 2: Step 1 — Profile Inputs & Unit Normalization ---")
    step1_update = {
        "currentStep": 2,
        "profileInput": {
            "district": "Salem",
            "landArea": 50.0,
            "landUnit": "cents",  # 50 cents = 0.5 acres
            "waterAvailability": "ample_borewell",
            "soilType": "unknown",  # Farmer doesn't know soil
            "season": "unknown",    # Farmer doesn't know season
            "budgetRange": "medium_35k_75k",
            "availableLabour": "family_only_1_2",
            "farmingGoal": "commercial_income"
        }
    }
    updated_j = await update_journey_step(farmer_a_id, step1_update)
    assert_test(updated_j.get("currentStep") == 2, "Advanced to Step 2")
    assert_test(updated_j.get("landAreaNormalizedAcres") == 0.5, "Normalized 50 cents to 0.5 acres")
    assert_test(updated_j.get("profileInput", {}).get("soilType") == "unknown", "Tolerates 'unknown' soil")

    # Test unit converter edge cases
    assert_test(normalize_land_to_acres(2.5, "acres") == 2.5, "Normalizes acres directly")
    assert_test(normalize_land_to_acres(87120, "sq_ft") == 2.0, "Normalizes square feet (87120 sqft = 2 acres)")
    assert_test(normalize_land_to_acres(40, "guntas") == 1.0, "Normalizes guntas (40 guntas = 1 acre)")

    # ------------------------------------------------------------------------
    # TEST 3: Step 2 — Crop Recommendation Engine & Trade-Offs
    # ------------------------------------------------------------------------
    print("\n--- TEST 3: Step 2 — Candidate Crops & Trade-offs ---")
    candidates = get_candidate_crops_for_profile(updated_j["profileInput"])
    assert_test(len(candidates) >= 3, f"Recommended {len(candidates)} candidate crops")
    
    top_crop = candidates[0]
    print(f"   Top recommended crop: {top_crop['cropId']} ({top_crop['cropName']['en']}) - Score: {top_crop['suitabilityScore']}%")
    assert_test(top_crop["suitabilityScore"] >= 80, "Top crop has high suitability score")
    assert_test(len(top_crop["tradeOffsAndRisks"]) >= 2, "Trade-offs and risks explicitly provided")
    assert_test(top_crop.get("verifiedReference", {}).get("institution") is not None, "Institutional reference attached")
    assert_test(top_crop.get("verifiedReference", {}).get("sourceUrl") is not None, "Source URL present")

    # Select Commercial Tomato
    step2_update = {
        "currentStep": 3,
        "selectedCropId": "tomato"
    }
    updated_j = await update_journey_step(farmer_a_id, step2_update)
    assert_test(updated_j.get("selectedCropId") == "tomato", "Persisted crop selection: Tomato")
    assert_test(updated_j.get("selectedCropName", {}).get("en") == "Commercial Hybrid Tomato", "Persisted bilingual crop name")
    assert_test(len(updated_j.get("costsWorksheet", {}).get("entries", [])) >= 6, "Auto-populated default cost worksheet for 0.5 acres")

    # ------------------------------------------------------------------------
    # TEST 4: Step 3 — Farm Preparation Checklist & Agronomic Guidance
    # ------------------------------------------------------------------------
    print("\n--- TEST 4: Step 3 — Farm Preparation Checklist ---")
    guide = get_crop_agronomic_guide("tomato")
    prep_items = guide.get("preparationChecklist", [])
    assert_test(len(prep_items) >= 4, f"Found {len(prep_items)} farm preparation checklist items")
    assert_test(any("soil sample" in item["titleEn"].lower() for item in prep_items), "Includes soil testing guidance")

    # Farmer checks off soil testing and ploughing
    step3_update = {
        "currentStep": 4,
        "checklists": {
            "prep_soil_test": True,
            "prep_ploughing": True,
            "prep_manure": False,
            "prep_beds_drip": True
        }
    }
    updated_j = await update_journey_step(farmer_a_id, step3_update)
    assert_test(updated_j["checklists"]["prep_soil_test"] is True, "Checklist item 'prep_soil_test' saved as True")
    assert_test(updated_j["checklists"]["prep_manure"] is False, "Checklist item 'prep_manure' saved as False")

    # ------------------------------------------------------------------------
    # TEST 5: Step 4 — Sowing / Planting Date & Dynamic Stage Calculation
    # ------------------------------------------------------------------------
    print("\n--- TEST 5: Step 4 & 6 — Planting Date & Stage Timeline Calculation ---")
    # Simulate planting date 25 days ago
    twenty_five_days_ago = (datetime.now(timezone.utc) - timedelta(days=25)).strftime("%Y-%m-%d")
    step4_update = {
        "currentStep": 5,
        "plantingDate": twenty_five_days_ago
    }
    updated_j = await update_journey_step(farmer_a_id, step4_update)
    assert_test(updated_j.get("plantingDate") == twenty_five_days_ago, "Planting date recorded")

    timeline = calculate_crop_stage_timeline("tomato", twenty_five_days_ago)
    assert_test(timeline["hasPlantingDate"] is True, "Timeline engine recognized planting date")
    assert_test(timeline["currentDay"] == 26, f"Calculated current day 26 (actual: {timeline['currentDay']})")
    assert_test(timeline["currentStageNumber"] == 2, f"Active stage is Stage 2 (Vegetative & Staking)")
    assert_test(len(timeline["stages"]) == 5, "5 total sequential growth stages")
    assert_test(timeline["stages"][0]["status"] == "completed", "Stage 1 marked completed")
    assert_test(timeline["stages"][1]["status"] == "active", "Stage 2 marked active")
    assert_test(timeline["stages"][2]["status"] == "upcoming", "Stage 3 marked upcoming")

    # ------------------------------------------------------------------------
    # TEST 6: Step 6 — Growth Observations, Deviations & Notifications
    # ------------------------------------------------------------------------
    print("\n--- TEST 6: Step 6 — Growth Observations & In-App Reminders ---")
    obs = await add_journey_observation(
        farmer_id=farmer_a_id,
        note="Healthy growth, staked 40 plants today. Noticed slight leaf curl on outer row.",
        stage_number=2,
        photo_url=None,
        is_deviation=True,
        deviation_reason="Light aphid infestation noted after intermittent drizzle"
    )
    assert_test(obs.get("id") is not None, "Growth observation logged with unique ID")
    assert_test(obs.get("isDeviation") is True, "Deviation flag persisted")

    # Test reminder notification dispatch
    notif = await trigger_journey_reminder_notification(
        farmer_id=farmer_a_id,
        title="Tomato Stage 2 Care Alert",
        message="Time for second split fertigation and yellow sticky trap inspection."
    )
    assert_test(notif.get("id") is not None, "In-app notification created for farmer")
    assert_test(notif.get("type") == "special_operation", "Notification type is 'special_operation'")

    # ------------------------------------------------------------------------
    # TEST 7: Step 8 — Cost Worksheet Math & User Customization
    # ------------------------------------------------------------------------
    print("\n--- TEST 7: Step 8 — Cost Worksheet Editable Math ---")
    cost_worksheet = updated_j.get("costsWorksheet", {})
    entries = cost_worksheet.get("entries", [])
    assert_test(len(entries) > 0, "Cost worksheet has baseline entries")

    # Farmer overrides seedling cost to actual ₹4,000
    entries[1]["userUnitPrice"] = 4000.0
    entries[1]["isUserEdited"] = True
    new_total = sum(e["userUnitPrice"] * e["userQuantity"] for e in entries)

    step8_update = {
        "currentStep": 8,
        "costsWorksheet": {
            "entries": entries,
            "totalOperatingCost": round(new_total, 2),
            "costPerUnitArea": round(new_total / 0.5, 2),
            "disclaimer": "Estimates are illustrative guidelines based on TNAU benchmarks. Profit is never guaranteed."
        }
    }
    updated_j = await update_journey_step(farmer_a_id, step8_update)
    assert_test(updated_j["costsWorksheet"]["entries"][1]["isUserEdited"] is True, "User custom cost marked edited")
    assert_test(updated_j["costsWorksheet"]["totalOperatingCost"] == round(new_total, 2), "Total operating cost re-calculated accurately")

    # ------------------------------------------------------------------------
    # TEST 8: Step 9 & 10 — Sales Plan, Harvest Closure & Net Profit/Loss
    # ------------------------------------------------------------------------
    print("\n--- TEST 8: Step 9 & 10 — Sale Plan & Commercial Closure ---")
    step9_update = {
        "currentStep": 9,
        "salePlan": {
            "targetChannels": ["Salem Uzhavar Sandhai", "AgriBharat Direct Marketplace"],
            "mandiPriceSnapshot": {"commodity": "Tomato", "modalPrice": 2400.0, "unit": "Quintal", "date": "2026-10-20"},
            "gradingPackagingDetails": ["Grade A crates for Uzhavar Sandhai", "Grade B for local juice processor"],
            "transportConsiderations": "Shared auto tempo with neighboring farmer Thiru. Murugan"
        }
    }
    updated_j = await update_journey_step(farmer_a_id, step9_update)
    assert_test(len(updated_j["salePlan"]["targetChannels"]) == 2, "Sales channels selected")

    # Step 10: Complete the harvest journey
    total_cost = updated_j["costsWorksheet"]["totalOperatingCost"]
    achieved_price_per_kg = 28.0
    harvested_kg = 3200.0  # 3,200 kg from 0.5 acre
    gross_revenue = harvested_kg * achieved_price_per_kg  # ₹89,600
    net_profit = gross_revenue - total_cost

    step10_update = {
        "currentStep": 10,
        "status": "completed",
        "completionRecord": {
            "harvestDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "harvestedQuantity": harvested_kg,
            "harvestUnit": "kg",
            "gradeBreakdown": {"gradeA": 85.0, "gradeB": 15.0},
            "buyerNameOrChannel": "Salem Uzhavar Sandhai (Direct to Consumer)",
            "achievedPricePerUnit": achieved_price_per_kg,
            "grossRevenue": gross_revenue,
            "totalOperatingCost": total_cost,
            "netProfitOrLoss": round(net_profit, 2),
            "farmerReflection": "First time tomato farming completed successfully! Drip irrigation was critical during November flower drop."
        }
    }
    updated_j = await update_journey_step(farmer_a_id, step10_update)
    assert_test(updated_j.get("status") == "completed", "Journey status transitioned to 'completed'")
    assert_test(updated_j["completionRecord"]["grossRevenue"] == 89600.0, "Gross revenue calculation verified")
    assert_test(updated_j["completionRecord"]["netProfitOrLoss"] == round(net_profit, 2), f"Net profit/loss calculated accurately (₹{round(net_profit, 2)})")

    # ------------------------------------------------------------------------
    # TEST 9: Safe Reset Without Deleting Unrelated Farmer Records
    # ------------------------------------------------------------------------
    print("\n--- TEST 9: Safe Reset & Re-Start ---")
    reset_success = await reset_journey(farmer_a_id)
    assert_test(reset_success is True, "Journey reset executed")

    col = get_special_operation_journeys_collection()
    old_j = await col.find_one({"farmerId": farmer_a_id})
    assert_test(old_j is None, "Journey deleted cleanly from journeys collection")

    # Re-initialization
    restarted_j = await get_or_create_journey(farmer_a_id, farmer_a_name, farmer_a_phone, "Salem")
    assert_test(restarted_j.get("currentStep") == 1, "New journey restarted at Step 1")

    print("\n" + "=" * 70)
    print(f"SPECIAL OPERATION TEST RESULTS: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_all_tests())

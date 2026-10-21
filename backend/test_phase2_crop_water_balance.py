"""
Phase 2: Automated Verification Test Suite
Crop Water Balance and Smart Irrigation Advisory
Project: Namma Vivasayi AI (SEVA)
"""

import sys
import os
import unittest
import httpx

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_farming import (
    calculate_irrigation_advice,
    CROP_KC_FACTORS
)
from models import IrrigationCalculateRequest

BASE_URL = "http://127.0.0.1:8000"


class TestPhase2CropWaterBalance(unittest.TestCase):
    """
    Comprehensive test suite for Phase 2:
    - FAO-56 / TNAU Crop Coefficients
    - Effective Rainfall & Probability vs Amount separation
    - Unit Math (1 mm * 1 m² = 1 L; 1 mm * 1 acre = 4,047 L)
    - Missing Data & Qualitative Fallback
    - 3 Recommendation Outcomes (irrigate_now, delay_reassess, monitor_conditions)
    - Paddy-Specific Water Management (Basin Flooding, AWD, Flowering, Pre-harvest drainage)
    - Safety & No Physical Control Disclaimers
    - Bilingual English & Tamil Output
    - HTTP API Integration
    """

    def test_01_crop_coefficients_across_crops_and_stages(self):
        """Verify FAO-56 / TNAU crop coefficients across crops and growth stages."""
        # Ensure no universal Kc value is used
        paddy_flowering = calculate_irrigation_advice("Paddy", "Flowering / Panicle Initiation", "Clay Loam", "Basin Flooding")
        maize_initial = calculate_irrigation_advice("Maize", "Initial / Sowing", "Red Loam", "Drip")
        sugarcane_veg = calculate_irrigation_advice("Sugarcane", "Vegetative", "Alluvial Clay Loam", "Furrow")
        cotton_boll = calculate_irrigation_advice("Cotton", "Grain Filling / Pod Development", "Black Cotton Soil", "Drip")
        black_gram_mat = calculate_irrigation_advice("Black Gram", "Maturity", "Sandy Loam", "Sprinkler")

        self.assertAlmostEqual(paddy_flowering["cropFactorKc"], 1.30, places=2)
        self.assertAlmostEqual(maize_initial["cropFactorKc"], 0.40, places=2)
        self.assertAlmostEqual(sugarcane_veg["cropFactorKc"], 1.00, places=2)
        self.assertAlmostEqual(cotton_boll["cropFactorKc"], 0.95, places=2)
        self.assertAlmostEqual(black_gram_mat["cropFactorKc"], 0.45, places=2)

        # Assert Kc varies by crop and stage
        self.assertNotEqual(paddy_flowering["cropFactorKc"], maize_initial["cropFactorKc"])
        self.assertNotEqual(sugarcane_veg["cropFactorKc"], black_gram_mat["cropFactorKc"])

        # Check ETc formula ETc = ET0 * Kc
        eto = paddy_flowering["referenceEtoMmDay"]
        expected_etc = round(eto * 1.30, 2)
        self.assertEqual(paddy_flowering["cropWaterDemandMm"], expected_etc)

    def test_02_effective_rainfall_does_not_equate_probability_to_amount(self):
        """Verify effective rainfall logic: probability is not amount and low chance does not assume rain."""
        # Scenario A: Low probability (20%) but 15mm in forecast -> Peff forecast should be 0 mm!
        mock_low_prob = {
            "isLive": True,
            "et0EstimateMmDay": 4.5,
            "precipitationProbability": 20,
            "precipitationSumMm": 15.0,
            "soilMoisture": {"available": True, "rootZonePercent": 35.0}
        }
        res_low = calculate_irrigation_advice(
            crop="Hybrid Maize",
            growth_stage="Vegetative",
            soil_type="Red Loam",
            irrigation_method="Precision Drip",
            weather_summary=mock_low_prob
        )
        self.assertEqual(res_low["effectiveRainfallMm"], 0.0)
        # Low rain chance shouldn't block irrigation if soil is deficient
        self.assertEqual(res_low["recommendation"], "irrigate_now")

        # Scenario B: High probability (80%) with 20mm forecast -> expected rain weighted, Peff > 0
        mock_high_prob = {
            "isLive": True,
            "et0EstimateMmDay": 4.5,
            "precipitationProbability": 80,
            "precipitationSumMm": 20.0,
            "soilMoisture": {"available": True, "rootZonePercent": 35.0}
        }
        res_high = calculate_irrigation_advice(
            crop="Hybrid Maize",
            growth_stage="Vegetative",
            soil_type="Red Loam",
            irrigation_method="Precision Drip",
            weather_summary=mock_high_prob
        )
        self.assertGreater(res_high["effectiveRainfallMm"], 0.0)
        self.assertEqual(res_high["recommendation"], "delay_reassess")
        self.assertEqual(res_high["estimatedLitersPerAcre"], 0)

    def test_03_units_and_field_area_volume_scaling(self):
        """Verify units explanation and acreage volume math (1 mm over 1 m² = 1 L; 1 mm over 1 acre = 4,047 L)."""
        res_1_acre = calculate_irrigation_advice(
            crop="Sugarcane",
            growth_stage="Flowering",
            soil_type="Clay Loam",
            irrigation_method="Precision Drip",
            soil_moisture_percent=30.0,  # Deficit to trigger irrigate_now
            field_area_acres=1.0,
            recent_rain_mm=0.0,
            forecast_rain_chance=10.0
        )
        self.assertEqual(res_1_acre["recommendation"], "irrigate_now")
        self.assertTrue(res_1_acre["isWaterVolumeEstimated"])
        self.assertIn("1 mm depth of water over 1 square metre equals 1 litre", res_1_acre["unitExplanationEn"])
        self.assertIn("4,047", res_1_acre["unitExplanationEn"])
        self.assertIn("1 சதுர மீட்டர் பரப்பில் 1 மிமீ", res_1_acre["unitExplanationTa"])

        gir = res_1_acre["grossIrrigationRequirementMm"]
        self.assertIsNotNone(gir)
        expected_liters_1_acre = int(round(gir * 4047.0, -2))
        self.assertEqual(res_1_acre["estimatedLitersPerAcre"], expected_liters_1_acre)
        self.assertEqual(res_1_acre["totalEstimatedLiters"], expected_liters_1_acre)

        # 3.5 Acres test: total volume must scale linearly with area
        res_3_5_acres = calculate_irrigation_advice(
            crop="Sugarcane",
            growth_stage="Flowering",
            soil_type="Clay Loam",
            irrigation_method="Precision Drip",
            soil_moisture_percent=30.0,
            field_area_acres=3.5,
            recent_rain_mm=0.0,
            forecast_rain_chance=10.0
        )
        expected_total_3_5 = int(round(gir * 4047.0 * 3.5, -2))
        self.assertEqual(res_3_5_acres["totalEstimatedLiters"], expected_total_3_5)
        self.assertEqual(res_3_5_acres["estimatedLitersPerAcre"], expected_liters_1_acre)

    def test_04_missing_critical_data_qualitative_fallback(self):
        """Verify that when critical agronomic inputs are missing, a qualitative advisory is given without fabricating volumes."""
        res_missing = calculate_irrigation_advice(
            crop="",
            growth_stage="",
            soil_type="",
            irrigation_method=""
        )
        self.assertEqual(res_missing["recommendation"], "monitor_conditions")
        self.assertFalse(res_missing["isWaterVolumeEstimated"])
        self.assertIsNone(res_missing["grossIrrigationRequirementMm"])
        self.assertIsNone(res_missing["totalEstimatedLiters"])
        self.assertEqual(res_missing["estimatedLitersPerAcre"], 0)
        self.assertEqual(res_missing["confidenceLevel"], "Low")
        self.assertTrue(any("qualitative" in r.lower() or "missing" in r.lower() for r in res_missing["reasonsEn"]))
        self.assertTrue(len(res_missing["limitationsEn"]) > 0)

    def test_05_three_distinct_recommendation_outcomes(self):
        """Verify exact generation of all 3 recommendation outcomes: irrigate_now, delay_reassess, monitor_conditions."""
        # Outcome 1: Delay and Reassess (Heavy rain forecasted)
        res_delay = calculate_irrigation_advice(
            crop="Cotton",
            growth_stage="Vegetative",
            soil_type="Black Cotton Soil",
            irrigation_method="Precision Drip",
            recent_rain_mm=18.0,  # Recent heavy rain
            forecast_rain_chance=70.0
        )
        self.assertEqual(res_delay["recommendation"], "delay_reassess")
        self.assertEqual(res_delay["status"], "delay")
        self.assertEqual(res_delay["recommendationTitleEn"], "Delay and Reassess")
        self.assertEqual(res_delay["recommendationTitleTa"], "தள்ளிப்போட்டு மறுமதிப்பீடு செய்யவும்")
        self.assertEqual(res_delay["estimatedLitersPerAcre"], 0)
        self.assertEqual(res_delay["totalEstimatedLiters"], 0)
        self.assertIn("Reassess", res_delay["irrigationWindowEn"])

        # Outcome 2: Monitor Conditions (Adequate soil moisture)
        res_monitor = calculate_irrigation_advice(
            crop="Cotton",
            growth_stage="Vegetative",
            soil_type="Black Cotton Soil",
            irrigation_method="Precision Drip",
            soil_moisture_percent=55.0,  # Comfortably above 42% threshold
            recent_rain_mm=0.0,
            forecast_rain_chance=15.0
        )
        self.assertEqual(res_monitor["recommendation"], "monitor_conditions")
        self.assertEqual(res_monitor["status"], "adequate")
        self.assertEqual(res_monitor["recommendationTitleEn"], "Monitor Conditions")
        self.assertEqual(res_monitor["recommendationTitleTa"], "நிலவரத்தைக் கண்காணிக்கவும்")
        self.assertEqual(res_monitor["estimatedLitersPerAcre"], 0)
        self.assertIn("07:00 AM", res_monitor["irrigationWindowEn"])

        # Outcome 3: Irrigate Now (Root zone moisture deficit)
        res_irrigate = calculate_irrigation_advice(
            crop="Cotton",
            growth_stage="Flowering",
            soil_type="Black Cotton Soil",
            irrigation_method="Precision Drip",
            soil_moisture_percent=32.0,  # Below 42% threshold
            recent_rain_mm=0.0,
            forecast_rain_chance=10.0
        )
        self.assertEqual(res_irrigate["recommendation"], "irrigate_now")
        self.assertEqual(res_irrigate["recommendationTitleEn"], "Irrigate Now")
        self.assertEqual(res_irrigate["recommendationTitleTa"], "இன்றே பாசனம் செய்யவும்")
        self.assertGreater(res_irrigate["estimatedLitersPerAcre"], 0)
        self.assertGreater(res_irrigate["totalEstimatedLiters"], 0)
        self.assertIn("06:00 AM – 09:00 AM IST", res_irrigate["irrigationWindowEn"])
        self.assertIn("06:00 AM – 09:00 AM IST", res_irrigate["irrigationWindowTa"])

    def test_06_paddy_water_management_and_pre_harvest_drainage(self):
        """Verify paddy-specific agronomic management: AWD, flowering submergence, and terminal pre-harvest drainage."""
        # 1. Paddy Flowering Stage -> Critical panicle management note
        res_flowering = calculate_irrigation_advice(
            crop="Samba Paddy",
            growth_stage="Flowering / Panicle Initiation",
            soil_type="Alluvial Clay Loam",
            irrigation_method="Controlled Basin Flooding"
        )
        self.assertIsNotNone(res_flowering["paddySpecificNotesEn"])
        self.assertIn("Panicle", res_flowering["paddySpecificNotesEn"])
        self.assertIn("standing water", res_flowering["paddySpecificNotesEn"].lower())
        self.assertIn("கதிர் பருவ மேலாண்மை", res_flowering["paddySpecificNotesTa"])

        # 2. Paddy Vegetative Stage -> TNAU Alternate Wetting & Drying (AWD) note
        res_veg = calculate_irrigation_advice(
            crop="Paddy (Ponni)",
            growth_stage="Vegetative / Active Tillering",
            soil_type="Alluvial Clay Loam",
            irrigation_method="Controlled Basin Flooding"
        )
        self.assertIn("Alternate Wetting & Drying", res_veg["paddySpecificNotesEn"])
        self.assertIn("Pani pipe", res_veg["paddySpecificNotesEn"])
        self.assertIn("பாணி பைப்", res_veg["paddySpecificNotesTa"])

        # 3. Paddy Maturity / Ripening Stage -> Pre-harvest drainage triggers Delay and Reassess!
        res_maturity = calculate_irrigation_advice(
            crop="Samba Paddy",
            growth_stage="Maturity / Ripening",
            soil_type="Alluvial Clay Loam",
            irrigation_method="Controlled Basin Flooding",
            soil_moisture_percent=30.0  # Even if soil is drying, terminal drainage is required!
        )
        self.assertEqual(res_maturity["recommendation"], "delay_reassess")
        self.assertEqual(res_maturity["estimatedLitersPerAcre"], 0)
        self.assertIn("Terminal", res_maturity["paddySpecificNotesEn"])
        self.assertIn("drain", res_maturity["paddySpecificNotesEn"].lower())
        self.assertIn("வடிகால்", res_maturity["paddySpecificNotesTa"])

    def test_07_safety_and_no_hardware_control_disclaimer(self):
        """Verify that software does not claim physical pump or valve control."""
        res = calculate_irrigation_advice("Groundnut", "Flowering", "Red Loam", "Precision Drip")
        self.assertTrue(res["isAdvisoryOnly"])
        self.assertIn("does not physically operate", res["noHardwareControlNotice"])
        self.assertIn("IoT probe", res["disclaimerEn"])
        self.assertIn("நேரடி சென்சார் அளவீடு அல்ல", res["disclaimerTa"])

    def test_08_http_api_with_field_area_and_bilingual_response(self):
        """Verify POST /api/irrigation/calculate endpoint with fieldAreaAcres and Phase 2 fields."""
        with httpx.Client(base_url=BASE_URL, timeout=12.0) as client:
            payload = {
                "crop": "Paddy / Rice (சம்பா நெல்)",
                "growthStage": "Flowering / Panicle Initiation",
                "soilType": "Alluvial Clay Loam",
                "irrigationMethod": "Controlled Basin Flooding",
                "fieldAreaAcres": 2.5,
                "latitude": 10.7870,
                "longitude": 79.1378
            }
            res = client.post("/api/irrigation/calculate", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()

            # Verify Phase 2 fields
            self.assertIn("recommendation", data)
            self.assertIn(data["recommendation"], ["irrigate_now", "delay_reassess", "monitor_conditions"])
            self.assertIn("recommendationTitleEn", data)
            self.assertIn("recommendationTitleTa", data)
            self.assertIn("irrigationWindowEn", data)
            self.assertIn("irrigationWindowTa", data)
            self.assertEqual(data["fieldAreaAcres"], 2.5)
            self.assertIn("effectiveRainfallMm", data)
            self.assertIn("unitExplanationEn", data)
            self.assertIn("unitExplanationTa", data)
            self.assertIn("confidenceLevel", data)
            self.assertIn("limitationsEn", data)
            self.assertIn("limitationsTa", data)
            self.assertIn("noHardwareControlNotice", data)
            self.assertIn("paddySpecificNotesEn", data)
            self.assertIn("paddySpecificNotesTa", data)

            # Check volume math on 2.5 acres
            if data["recommendation"] == "irrigate_now":
                self.assertGreater(data["totalEstimatedLiters"], data["estimatedLitersPerAcre"])


if __name__ == "__main__":
    unittest.main()

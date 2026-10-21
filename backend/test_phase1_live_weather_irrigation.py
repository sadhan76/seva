"""
Phase 1: Automated Verification Test Suite
Live Weather Integration for Smart Irrigation & Farm Location Management
Project: Namma Vivasayi AI (SEVA)
"""

import sys
import os
import asyncio
import unittest
from datetime import datetime, timezone, timedelta
import httpx

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_farming import (
    validate_coordinates,
    get_irrigation_weather,
    calculate_irrigation_advice,
    IRRIGATION_WEATHER_CACHE,
    IRRIGATION_CACHE_TTL_SECONDS,
    IST
)
from models import IrrigationCalculateRequest, FarmLocationUpdateRequest

BASE_URL = "http://127.0.0.1:8000"


class TestPhase1LiveWeatherIrrigation(unittest.TestCase):
    """
    Test suite for Phase 1 Live Weather Integration in Smart Irrigation.
    """

    def test_01_coordinate_validation_success_and_failure(self):
        """Test coordinate boundary checking and validation."""
        # Valid coordinates
        lat, lon = validate_coordinates(10.7870, 79.1378)
        self.assertAlmostEqual(lat, 10.7870, places=4)
        self.assertAlmostEqual(lon, 79.1378, places=4)

        # String representation of numbers
        lat_s, lon_s = validate_coordinates("11.0168", "76.9558")
        self.assertAlmostEqual(lat_s, 11.0168, places=4)

        # Out-of-bounds latitude
        with self.assertRaises(ValueError):
            validate_coordinates(95.0, 78.0)
        with self.assertRaises(ValueError):
            validate_coordinates(-90.5, 78.0)

        # Out-of-bounds longitude
        with self.assertRaises(ValueError):
            validate_coordinates(10.0, 185.0)
        with self.assertRaises(ValueError):
            validate_coordinates(10.0, -180.5)

        # Non-numeric inputs
        with self.assertRaises(ValueError):
            validate_coordinates("invalid_lat", "79.0")

    def test_02_backend_irrigation_weather_parsing(self):
        """Test live Open-Meteo API parsing via get_irrigation_weather."""
        # Thanjavur coordinates
        data = asyncio.run(get_irrigation_weather(10.7870, 79.1378, force_refresh=True))

        self.assertIn("coordinates", data)
        self.assertEqual(data["timezone"], "Asia/Kolkata")
        self.assertIn("Open-Meteo", data["source"])
        self.assertIn("units", data)
        self.assertEqual(data["units"]["temperature"], "°C")
        self.assertEqual(data["units"]["et0"], "mm/day")
        self.assertEqual(data["units"]["soilMoisture"], "% (volumetric m³/m³)")

        # Verify current weather object
        curr = data.get("current")
        self.assertIsNotNone(curr)
        self.assertIn("temperatureC", curr)
        self.assertIn("humidity", curr)
        self.assertIn("condition", curr)
        self.assertIn("conditionTa", curr)

        # Verify agrometeorological variables
        self.assertIn("precipitationProbability", data)
        self.assertIn("precipitationSumMm", data)
        self.assertIn("et0EstimateMmDay", data)

        # Verify soil moisture structure
        sm = data.get("soilMoisture", {})
        self.assertIn("available", sm)
        self.assertIn("rootZonePercent", sm)
        self.assertIn("depth0To7cmPercent", sm)
        self.assertIn("depth7To28cmPercent", sm)
        self.assertIn("depth28To100cmPercent", sm)
        self.assertIn("disclaimer", sm)
        self.assertIn("not an in-situ", sm["disclaimer"].lower())

    def test_03_cache_behavior_and_ttl(self):
        """Test in-memory cache hit and force_refresh bypass."""
        lat, lon = 11.0168, 76.9558  # Coimbatore

        # First request (force_refresh)
        res1 = asyncio.run(get_irrigation_weather(lat, lon, force_refresh=True))
        self.assertTrue(res1["isLive"])
        self.assertFalse(res1["isCached"])

        # Second request without force_refresh (must hit cache)
        res2 = asyncio.run(get_irrigation_weather(lat, lon, force_refresh=False))
        self.assertTrue(res2["isCached"])
        self.assertFalse(res2["isStale"])
        self.assertIn("cacheAgeSeconds", res2)

    def test_04_advisory_calculation_with_and_without_live_weather(self):
        """Test smart irrigation advisory rule engine with live weather vs fallback."""
        # 1. Calculation with live weather summary
        mock_weather = {
            "isLive": True,
            "isCached": False,
            "et0EstimateMmDay": 4.5,
            "precipitationProbability": 85,
            "precipitationSumMm": 22.0,
            "soilMoisture": {
                "available": True,
                "rootZonePercent": 48.0
            }
        }

        advice_rain = calculate_irrigation_advice(
            crop="Paddy / Rice",
            growth_stage="Vegetative",
            soil_type="Alluvial Clay Loam",
            irrigation_method="Controlled Basin Flooding",
            weather_summary=mock_weather
        )

        self.assertTrue(advice_rain["isLiveWeatherUsed"])
        self.assertEqual(advice_rain["status"], "delay")
        self.assertEqual(advice_rain["estimatedLitersPerAcre"], 0)
        self.assertIn("Skip / Postpone", advice_rain["recommendationEn"])

        # 2. Calculation without weather (backward compatible)
        advice_default = calculate_irrigation_advice(
            crop="Paddy / Rice",
            growth_stage="Vegetative",
            soil_type="Alluvial Clay Loam",
            irrigation_method="Controlled Basin Flooding",
            soil_moisture_percent=None,
            recent_rain_mm=0.0,
            forecast_rain_chance=10.0
        )
        self.assertFalse(advice_default["isLiveWeatherUsed"])
        self.assertEqual(advice_default["status"], "moderate")
        self.assertGreater(advice_default["estimatedLitersPerAcre"], 0)

    def test_05_http_irrigation_weather_endpoint(self):
        """Test GET /api/weather/irrigation HTTP API."""
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            # Valid query
            res = client.get("/api/weather/irrigation?lat=10.7870&lon=79.1378")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["coordinates"]["lat"], 10.787)
            self.assertEqual(data["timezone"], "Asia/Kolkata")
            self.assertIn("soilMoisture", data)

            # Invalid query (latitude out of range)
            res_invalid = client.get("/api/weather/irrigation?lat=120.0&lon=79.1378")
            self.assertEqual(res_invalid.status_code, 422)

    def test_06_http_irrigation_calculate_endpoint_with_coordinates(self):
        """Test POST /api/irrigation/calculate HTTP API with coordinates."""
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            payload = {
                "crop": "Hybrid Maize (மக்காச்சோளம்)",
                "growthStage": "Flowering / Panicle Initiation",
                "soilType": "Red Loam",
                "irrigationMethod": "Precision Drip Irrigation",
                "latitude": 10.7870,
                "longitude": 79.1378
            }
            res = client.post("/api/irrigation/calculate", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("recommendationEn", data)
            self.assertIn("cropWaterDemandMm", data)
            self.assertIn("cropFactorKc", data)
            self.assertTrue(data.get("isLiveWeatherUsed"))
            self.assertIsNotNone(data.get("weatherSummary"))

    def test_07_farm_location_consent_requirement(self):
        """Test POST /api/farmer/farm-location enforces explicit user consent."""
        import random
        test_phone = f"98{random.randint(10000000, 99999999)}"
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            reg_payload = {
                "name": "Phase 1 Test Farmer",
                "phone": test_phone,
                "password": "FarmerPassword@2026",
                "confirmPassword": "FarmerPassword@2026",
                "role": "farmer",
                "village": "Thiruvaiyaru",
                "state": "Tamil Nadu",
                "district": "Thanjavur",
                "totalLandAcres": 3,
                "primaryCrop": "Paddy"
            }
            reg_res = client.post("/api/auth/register", json=reg_payload)
            self.assertEqual(reg_res.status_code, 201)
            token = reg_res.json()["accessToken"]
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Attempt to update farm location WITHOUT consent (must be rejected)
            no_consent_payload = {
                "latitude": 10.7870,
                "longitude": 79.1378,
                "locationName": "My Cauvery Delta Farm",
                "consent": False
            }
            res_no_consent = client.post("/api/farmer/farm-location", json=no_consent_payload, headers=headers)
            self.assertEqual(res_no_consent.status_code, 400)
            self.assertIn("consent", res_no_consent.json()["detail"].lower())

            # 2. Update farm location WITH explicit consent
            consent_payload = {
                "latitude": 10.7870,
                "longitude": 79.1378,
                "locationName": "My Cauvery Delta Farm",
                "consent": True
            }
            res_consent = client.post("/api/farmer/farm-location", json=consent_payload, headers=headers)
            self.assertEqual(res_consent.status_code, 200)
            user_data = res_consent.json()
            self.assertIn("farmCoordinates", user_data)
            self.assertIsNotNone(user_data["farmCoordinates"])
            self.assertEqual(user_data["farmCoordinates"]["latitude"], 10.787)
            self.assertTrue(user_data["farmCoordinates"]["consentGiven"])


if __name__ == "__main__":
    unittest.main()

"""
Automated Test Suite for Phase 4: Smart Farming Intelligence Endpoints
"""

import urllib.request
import urllib.error
import json
import io

BASE_URL = "http://127.0.0.1:8000"

def request_json(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(error_body)
        except:
            return e.code, {"raw": error_body}

def run_tests():
    print("=== STARTING PHASE 4 SMART FARMING TESTS ===")

    # 1. Weather districts list
    status, districts = request_json(f"{BASE_URL}/api/weather/districts")
    print(f"[1] Weather Districts: Status {status}, Count: {len(districts)}")
    assert status == 200 and len(districts) >= 10

    # 2. Weather endpoint for Thanjavur
    status, weather = request_json(f"{BASE_URL}/api/weather?district=thanjavur")
    print(f"[2] Weather (Thanjavur): Status {status}, Temp: {weather.get('temperatureC')}C, Condition: {weather.get('condition')}, Live: {weather.get('isLive')}")
    assert status == 200
    assert "sprayingAdvisory" in weather
    assert "forecast" in weather

    # 3. Smart Irrigation Advisory
    irrig_payload = {
        "crop": "Paddy (Ponni)",
        "growthStage": "Flowering / Panicle Initiation",
        "soilType": "Alluvial Clay Loam",
        "irrigationMethod": "Controlled Basin Flooding",
        "soilMoisturePercent": 48.0,
        "recentRainMm": 0.0,
        "forecastRainChance": 20.0
    }
    status, irrig = request_json(f"{BASE_URL}/api/irrigation/calculate", method="POST", data=irrig_payload)
    print(f"[3] Smart Irrigation: Status {status}, Rec: {irrig.get('recommendationEn')}, Kc: {irrig.get('cropFactorKc')}, Advisory: {irrig.get('isAdvisoryOnly')}")
    assert status == 200
    assert irrig.get("isAdvisoryOnly") is True
    assert "disclaimerEn" in irrig

    # 4. Crop Recommendations
    crop_payload = {
        "district": "Thanjavur",
        "soilType": "Alluvial Clay Loam",
        "season": "Samba (Aug - Jan)",
        "waterAvailability": "High",
        "cropPreference": "Pulses"
    }
    status, crops = request_json(f"{BASE_URL}/api/crops/recommend", method="POST", data=crop_payload)
    print(f"[4] Crop Recommendations: Status {status}, Total Suggested: {len(crops.get('recommendations', []))}")
    assert status == 200
    assert len(crops.get("recommendations", [])) > 0
    assert "assumptions" in crops
    assert "disclaimer" in crops

    # 5. Disease Reference Catalog
    status, catalog = request_json(f"{BASE_URL}/api/disease/catalog")
    print(f"[5] Disease Catalog: Status {status}, Entries: {len(catalog.get('catalog', []))}")
    assert status == 200 and len(catalog.get("catalog", [])) >= 4

    # 6. Disease Image Upload (Honest reporting: analysis not configured)
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode("utf-8"))
    body.write(b'Content-Disposition: form-data; name="file"; filename="test_leaf.jpg"\r\n')
    body.write(b"Content-Type: image/jpeg\r\n\r\n")
    body.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\xFF\xC0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xDA\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xBF\x00\xFF\xD9")
    body.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    raw_body = body.getvalue()

    req = urllib.request.Request(
        f"{BASE_URL}/api/disease/analyze",
        data=raw_body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        disease_res = json.loads(resp.read().decode("utf-8"))
        print(f"[6] Disease Upload Analysis: Status {resp.status}, Diagnosis State: {disease_res.get('status')}, Tested Model: {disease_res.get('testedModelPresent')}")
        assert disease_res.get("status") == "not_configured"
        assert disease_res.get("testedModelPresent") is False
        assert "truthfulnessNotice" in disease_res

    # 7. Regulated Mandi Market Prices
    status, market = request_json(f"{BASE_URL}/api/market/prices?district=Thanjavur")
    print(f"[7] Market Prices: Status {status}, Commodities: {len(market.get('commodities', []))}, Source: {market.get('dataSource')}")
    assert status == 200 and len(market.get("commodities", [])) >= 2
    assert "demoNoticeEn" in market

    # 8. Government Agricultural Schemes
    status, schemes = request_json(f"{BASE_URL}/api/schemes")
    print(f"[8] Government Schemes: Status {status}, Schemes Count: {len(schemes.get('schemes', []))}")
    assert status == 200 and len(schemes.get("schemes", [])) >= 5
    assert "disclaimerEn" in schemes

    print("=== ALL 8 PHASE 4 BACKEND TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()

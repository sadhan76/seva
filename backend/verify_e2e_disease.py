"""
NAMMA VIVASAYI AI - END-TO-END VERIFICATION SUITE
=================================================
Automated verification script covering:
1. Image Input & Boundary Validation (valid, >5MB, malformed, non-image)
2. Real AI Integration (actual bytes check, provider connectivity test, secret sanitization, error resilience)
3. Diagnostic Workflow (pest, disease, abiotic, inconclusive, untrusted category defense)
4. Treatment Safety & Agronomic Guardrails (biological vs chemical segregation, zero pesticides for abiotic)
5. Full Application Regression (all platform modules)
"""

import sys
import os
import io
import json
import time
import unittest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from plant_vision import (
    validate_leaf_image,
    sanitize_vision_error,
    parse_and_validate_diagnosis,
    DEFAULT_VISION_MODEL,
    MAX_IMAGE_SIZE_BYTES
)
from treatment_service import (
    get_verified_treatment_recommendation,
    build_uncertain_or_inconclusive_guidance
)
from database import get_diagnosis_reports_collection

client = TestClient(app)

results = {
    "image_input": {},
    "real_ai": {},
    "diagnostic_workflow": {},
    "treatment_safety": {},
    "regressions": {}
}


def make_test_image(format="JPEG", size=(200, 200), color=(34, 139, 34)):
    """Creates in-memory image bytes."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def run_image_input_tests():
    print("\n" + "="*70)
    print("1. IMAGE INPUT & VALIDATION VERIFICATION")
    print("="*70)

    # 1.1 Upload valid image
    valid_jpg = make_test_image("JPEG")
    is_valid, err, dims, mime = validate_leaf_image(valid_jpg, "image/jpeg")
    print(f"[1.1] Valid Image Check: valid={is_valid}, dims={dims}, mime={mime}")
    assert is_valid is True
    assert mime == "image/jpeg"
    results["image_input"]["valid_image"] = "PASSED"

    # 1.2 Reject file > 5 MB
    large_bytes = b"\x00" * (5 * 1024 * 1024 + 1024)
    is_valid, err, _, _ = validate_leaf_image(large_bytes, "image/jpeg")
    print(f"[1.2] File > 5MB Rejection: valid={is_valid}, error='{err}'")
    assert is_valid is False
    assert "exceeds" in err.lower()
    results["image_input"]["reject_over_5mb"] = "PASSED"

    # 1.3 Reject invalid file formats and malformed images
    corrupt_bytes = b"NOT_AN_IMAGE_FILE_JUST_TEXT_PAYLOAD_FOR_TESTING" * 5
    is_valid, err, _, _ = validate_leaf_image(corrupt_bytes, "image/jpeg")
    print(f"[1.3] Corrupted Bytes Rejection: valid={is_valid}, error='{err}'")
    assert is_valid is False
    assert "corrupt" in err.lower() or "cannot identify" in err.lower()
    results["image_input"]["reject_malformed"] = "PASSED"

    # 1.4 Reject sub-pixel images (< 20x20)
    tiny_img = make_test_image("JPEG", size=(10, 10))
    is_valid, err, _, _ = validate_leaf_image(tiny_img, "image/jpeg")
    print(f"[1.4] Tiny Sub-pixel Image (<20x20): valid={is_valid}, error='{err}'")
    assert is_valid is False
    assert "too small" in err.lower() or "dimensions" in err.lower()
    results["image_input"]["reject_subpixel"] = "PASSED"


def run_real_ai_integration_tests():
    print("\n" + "="*70)
    print("2. REAL AI INTEGRATION & MODEL CONNECTIVITY")
    print("="*70)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_VISION_MODEL).strip()

    print(f"[*] Configured Model: {model_name}")
    print(f"[*] API Key Present: {bool(api_key)} (Length: {len(api_key)} chars)")

    # 2.1 Verify secret sanitization: API key must NEVER be leaked
    sample_key = "AIzaSyFakeSecretKeyForTestingLeakage12345"
    raw_error = f"Error calling Google API at https://generativelanguage.googleapis.com with key {sample_key}: Quota exceeded"
    sanitized = sanitize_vision_error(raw_error, sample_key)
    print(f"[2.1] Secret Sanitization: '{sanitized}'")
    assert sample_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized or "quota" in sanitized.lower()
    results["real_ai"]["secret_protection"] = "PASSED"

    # 2.2 Provider resilience: Timeout & Rate limit fallback test
    rate_limit_err = "Resource has been exhausted (e.g. check quota). 429 RESOURCE_EXHAUSTED"
    safe_rate_msg = sanitize_vision_error(rate_limit_err)
    print(f"[2.2] Rate Limit Handling: '{safe_rate_msg}'")
    assert "quota" in safe_rate_msg.lower() or "operating in verified tnau" in safe_rate_msg.lower()
    results["real_ai"]["rate_limit_resilience"] = "PASSED"

    # 2.3 Provider live test (if key is set)
    if api_key:
        print("[2.3] Testing REAL LIVE Gemini Vision API call...")
        from plant_vision import analyze_leaf_image_with_vision
        import asyncio
        test_leaf = make_test_image("JPEG", size=(250, 250), color=(40, 160, 40))
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        resp = loop.run_until_complete(
            analyze_leaf_image_with_vision(
                image_bytes=test_leaf,
                filename="e2e_specimen.jpg",
                content_type="image/jpeg",
                crop_name="Paddy",
                plant_part="leaf",
                district="Thanjavur"
            )
        )
        print(f"[2.3] Real Gemini Response Status: {resp.get('status')}")
        print(f"[2.3] Model Name: {resp.get('modelName')}")
        print(f"[2.3] Truthfulness Notice: {resp.get('truthfulnessNotice')}")

        # Check that no secret key is exposed in any response field
        resp_json_str = json.dumps(resp)
        assert api_key not in resp_json_str
        results["real_ai"]["live_call_status"] = resp.get("status")
        results["real_ai"]["live_call_model"] = resp.get("modelName")
    else:
        print("[2.3] Live call skipped: GEMINI_API_KEY is not configured in environment.")
        results["real_ai"]["live_call_status"] = "KEY_NOT_CONFIGURED"


def run_diagnostic_workflow_tests():
    print("\n" + "="*70)
    print("3. DIAGNOSTIC WORKFLOW & CATEGORY SEPARATION")
    print("="*70)

    # 3.1 Untrusted input defense: Arbitrary/hallucinated category
    bad_output = json.dumps({
        "category": "alien_fungus_plague",
        "suspected_condition_en": "Alien Blight",
        "confidence_score": 99
    })
    is_ok, diag, err = parse_and_validate_diagnosis(bad_output, "Paddy")
    print(f"[3.1] Untrusted Category Defense: mapped category='{diag.category}'")
    assert diag.category == "inconclusive"
    results["diagnostic_workflow"]["untrusted_category_defense"] = "PASSED"

    # 3.2 Category 1: Pest Damage
    pest_output = json.dumps({
        "is_crop_leaf": True,
        "category": "pest_damage",
        "category_label_en": "Pest & Insect Damage",
        "suspected_condition_en": "Yellow Stem Borer",
        "affected_crop_en": "Paddy",
        "confidence_score": 88,
        "severity_or_urgency": "high",
        "visual_symptoms_observed_en": "Dead hearts observed in central tiller with caterpillar frass",
        "possible_causes_en": ["Scirpophaga incertulas larvae"],
        "alternative_explanations_en": ["Armyworm cut"],
        "diagnostic_limitations_en": ["Field sweep net sample recommended"],
        "recommended_next_steps_en": ["Place pheromone traps at 5 per acre"],
        "biological_management_en": ["Release Trichogramma japonicum egg parasitoids"],
        "chemical_treatment_en": ["Chlorantraniliprole 18.5% SC @ 0.3 ml/L"]
    })
    is_ok, diag, _ = parse_and_validate_diagnosis(pest_output, "Paddy")
    assert is_ok and diag.category == "pest_damage"
    print(f"[3.2] Pest Damage: condition='{diag.suspectedCondition}', confidence={diag.confidencePercent}%")
    results["diagnostic_workflow"]["pest_damage"] = "PASSED"

    # 3.3 Category 2: Plant Disease
    disease_output = json.dumps({
        "is_crop_leaf": True,
        "category": "plant_disease",
        "category_label_en": "Plant Disease",
        "suspected_condition_en": "Rice Leaf Blast",
        "affected_crop_en": "Paddy",
        "confidence_score": 92,
        "severity_or_urgency": "critical",
        "visual_symptoms_observed_en": "Diamond shaped spindle lesions with ash centers",
        "possible_causes_en": ["Pyricularia oryzae fungal infection"],
        "biological_management_en": ["Pseudomonas fluorescens foliar spray"],
        "chemical_treatment_en": ["Tricyclazole 75% WP @ 0.6 g/L"]
    })
    is_ok, diag, _ = parse_and_validate_diagnosis(disease_output, "Paddy")
    assert is_ok and diag.category == "plant_disease"
    print(f"[3.3] Plant Disease: condition='{diag.suspectedCondition}', severity={diag.severityOrUrgency}")
    results["diagnostic_workflow"]["plant_disease"] = "PASSED"

    # 3.4 Category 3: Abiotic Disorder
    abiotic_output = json.dumps({
        "is_crop_leaf": True,
        "category": "abiotic_disorder",
        "category_label_en": "Abiotic & Nutritional Disorder",
        "suspected_condition_en": "Potassium (K) Deficiency",
        "affected_crop_en": "Paddy",
        "confidence_score": 85,
        "severity_or_urgency": "moderate",
        "visual_symptoms_observed_en": "Marginal scorching and tip necrosis of older leaves",
        "possible_causes_en": ["Insufficient muriate of potash in sandy soils"],
        "biological_management_en": ["Incorporate well-decomposed FYM at 12.5 t/ha"],
        "chemical_treatment_en": ["MOP (Muriate of Potash) foliar or basal application"]
    })
    is_ok, diag, _ = parse_and_validate_diagnosis(abiotic_output, "Paddy")
    assert is_ok and diag.category == "abiotic_disorder"
    print(f"[3.4] Abiotic Disorder: condition='{diag.suspectedCondition}', causes={len(diag.possibleCauses)}")
    results["diagnostic_workflow"]["abiotic_disorder"] = "PASSED"


def run_treatment_safety_tests():
    print("\n" + "="*70)
    print("4. TREATMENT SAFETY & AGRONOMIC INTEGRITY")
    print("="*70)

    # 4.1 Abiotic disorder must NEVER trigger chemical pesticide recommendations
    abiotic_treatment = get_verified_treatment_recommendation(
        crop="Paddy / Rice",
        condition_name="Potassium (K) Deficiency / Marginal Firing",
        category="abiotic_disorder",
        confidence_percent=90,
        is_crop_leaf=True
    )
    print(f"[4.1] Abiotic Chemical Applicability: isApplicable={abiotic_treatment.chemicalManagement.isApplicable}")
    assert abiotic_treatment.chemicalManagement.isApplicable is False
    assert "not applicable" in abiotic_treatment.chemicalManagement.inapplicableReason.lower()
    results["treatment_safety"]["zero_pesticides_for_abiotic"] = "PASSED"

    # 4.2 Inconclusive condition must withhold chemical treatments
    inconclusive_guidance = build_uncertain_or_inconclusive_guidance("Paddy", "Unclear Specimen", "en")
    print(f"[4.2] Inconclusive Chemical Applicability: isApplicable={inconclusive_guidance.chemicalManagement.isApplicable}")
    assert inconclusive_guidance.chemicalManagement.isApplicable is False
    assert inconclusive_guidance.isUncertainOrInconclusive is True
    results["treatment_safety"]["inconclusive_withholds_chemicals"] = "PASSED"

    # 4.3 Verified Rice Blast chemical management includes dosage, CIBRC source, and safety precautions
    blast_treatment = get_verified_treatment_recommendation(
        crop="Paddy / Rice",
        condition_name="Blast (Pyricularia oryzae)",
        category="plant_disease",
        confidence_percent=90,
        is_crop_leaf=True
    )
    chem = blast_treatment.chemicalManagement
    print(f"[4.3] Rice Blast Verified Chemical: active='{chem.activeIngredient}', dosage='{chem.dosageAndApplication}'")
    assert chem.isApplicable is True
    assert "Tricyclazole" in chem.activeIngredient
    assert "120 g" in chem.dosageAndApplication
    assert chem.safetyPrecautions and len(chem.safetyPrecautions) > 0
    assert any("TNAU" in ref.organization or "TNAU" in ref.sourceTitle for ref in blast_treatment.references)
    results["treatment_safety"]["authoritative_chemical_guidance"] = "PASSED"

    # 4.4 Clear biological vs. chemical segregation
    bio = blast_treatment.biologicalManagement
    print(f"[4.4] Biological Segregation: cultural={len(bio.culturalPractices)}, bioControl={len(bio.biologicalControlAgents)}")
    assert len(bio.culturalPractices) > 0
    assert len(bio.biologicalControlAgents) > 0
    assert any("Pseudomonas" in b for b in bio.biologicalControlAgents)
    results["treatment_safety"]["biological_chemical_segregated"] = "PASSED"


def run_platform_regression_tests():
    print("\n" + "="*70)
    print("5. PLATFORM REGRESSION SUITE (LIVE SERVER)")
    print("="*70)

    # 5.1 Weather districts
    r = client.get("/api/weather/districts")
    assert r.status_code == 200 and len(r.json()) > 0
    print(f"[5.1] Weather Districts: Status 200, count={len(r.json())}")

    # 5.2 Weather Thanjavur
    r = client.get("/api/weather?district=thanjavur")
    assert r.status_code == 200
    print(f"[5.2] Weather Thanjavur: Status 200, temp={r.json().get('temperatureC')}C")

    # 5.3 Irrigation Calculation
    r = client.post("/api/irrigation/calculate", json={
        "crop": "Paddy (Ponni)",
        "growthStage": "Flowering / Panicle Initiation",
        "soilType": "Alluvial Clay Loam",
        "irrigationMethod": "Controlled Basin Flooding",
        "soilMoisturePercent": 45.0,
        "recentRainMm": 0.0,
        "forecastRainChance": 10.0
    })
    assert r.status_code == 200
    print(f"[5.3] Irrigation Advisory: Status 200, advice='{r.json().get('recommendationEn')}'")

    # 5.4 Crop Recommendation
    r = client.post("/api/crops/recommend", json={
        "district": "Thanjavur",
        "soilType": "Alluvial Clay Loam",
        "season": "Kuruvai",
        "waterAvailability": "Canal / Borewell"
    })
    assert r.status_code == 200 and len(r.json().get("recommendations", [])) > 0
    print(f"[5.4] Crop Recommendations: Status 200, count={len(r.json().get('recommendations', []))}")

    # 5.5 Market Prices
    r = client.get("/api/market/prices?district=Thanjavur")
    assert r.status_code == 200
    print(f"[5.5] Market Prices: Status 200, count={len(r.json().get('prices', []))}")

    # 5.6 Government Schemes
    r = client.get("/api/schemes")
    assert r.status_code == 200
    print(f"[5.6] Government Schemes: Status 200, count={len(r.json().get('schemes', []))}")

    # 5.7 Disease Reference Catalog
    r = client.get("/api/disease/catalog")
    assert r.status_code == 200 and len(r.json().get("catalog", [])) > 0
    print(f"[5.7] Disease Reference Catalog: Status 200, count={len(r.json().get('catalog', []))}")

    # 5.8 Diagnosis Reports (Auth protected)
    r = client.get("/api/disease/reports")
    assert r.status_code == 401
    print(f"[5.8] Diagnosis Reports (Unauthenticated): Status {r.status_code} (Properly protected)")

    results["regressions"]["all_endpoints"] = "PASSED"


if __name__ == "__main__":
    run_image_input_tests()
    run_real_ai_integration_tests()
    run_diagnostic_workflow_tests()
    run_treatment_safety_tests()
    run_platform_regression_tests()

    print("\n" + "="*70)
    print("END-TO-END VERIFICATION SUMMARY")
    print("="*70)
    print(json.dumps(results, indent=2))

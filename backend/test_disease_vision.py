"""
Unit and Integration Tests for Multi-Category Crop Health Vision Service (Phase 20)
==================================================================================
IMPORTANT SCIENTIFIC INTEGRITY & REGULATORY NOTICE:
The unit tests in this file utilize simulated (mocked) model responses to verify
backend pipeline integrity, schema validation, category partitioning, error handling,
and timeout resilience.

Execution and passing of these software tests verifies that the software pipeline
functions as implemented; it does NOT constitute clinical or scientific validation
of model diagnostic efficacy or accuracy under actual agricultural field conditions.

Categories Tested:
- Category 1: Pest and insect damage (e.g., Stem Borer / Brown Planthopper)
- Category 2: Plant diseases (e.g., Rice Leaf & Neck Blast - Pyricularia oryzae)
- Category 3: Physiological and abiotic disorders (e.g., Potassium Deficiency / Scorch)
- Category 4: Inconclusive / Insufficient evidence (blurry, non-crop, or ambiguous)
"""

import os
import io
import sys
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plant_vision import (
    validate_leaf_image,
    analyze_leaf_image_with_vision,
    parse_and_validate_diagnosis,
    MAX_IMAGE_SIZE_BYTES,
    MIN_IMAGE_SIZE_BYTES,
)


def create_test_image(width: int = 120, height: int = 120, color=(34, 139, 34), fmt="JPEG") -> bytes:
    """Helper to generate an in-memory valid image byte payload."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()


# ============================================================================
# 1. IMAGE VALIDATION TESTS (LOCAL / NO NETWORK)
# ============================================================================

def test_image_validation():
    print("\n--- [TEST SUITE 1] Image Validation Tests (Local / Mock) ---")

    # 1. Empty bytes
    valid, err, dim, mime = validate_leaf_image(b"")
    assert not valid and "empty" in err.lower()
    print("  ✓ Empty file rejected successfully.")

    # 2. Sub-100 byte payload
    valid, err, dim, mime = validate_leaf_image(b"\xFF\xD8\xFF" + b"\x00" * 40)
    assert not valid and "small" in err.lower()
    print("  ✓ Sub-100 byte payload rejected successfully.")

    # 3. Oversized payload (> 5MB)
    oversized = b"0" * (MAX_IMAGE_SIZE_BYTES + 1024)
    valid, err, dim, mime = validate_leaf_image(oversized)
    assert not valid and "exceeds" in err.lower()
    print("  ✓ Oversized (>5MB) file rejected successfully.")

    # 4. Corrupted non-image bytes
    corrupt = b"X" * 1500
    valid, err, dim, mime = validate_leaf_image(corrupt)
    assert not valid and "not a recognized" in err.lower()
    print("  ✓ Corrupt/random non-image bytes rejected successfully.")

    # 5. Tiny dimensions (5x5 pixels)
    tiny_img = create_test_image(5, 5, fmt="JPEG")
    valid, err, dim, mime = validate_leaf_image(tiny_img)
    assert not valid and "dimensions" in err.lower()
    print("  ✓ Tiny dimension (5x5) image rejected successfully.")

    # 6. Valid JPEG
    valid_jpeg = create_test_image(150, 150, fmt="JPEG")
    valid, err, dim, mime = validate_leaf_image(valid_jpeg)
    assert valid and mime == "image/jpeg"
    print(f"  ✓ Valid JPEG accepted (dimensions: {dim}, mime: {mime}).")

    # 7. Valid PNG
    valid_png = create_test_image(150, 150, fmt="PNG")
    valid, err, dim, mime = validate_leaf_image(valid_png)
    assert valid and mime == "image/png"
    print(f"  ✓ Valid PNG accepted (dimensions: {dim}, mime: {mime}).")


# ============================================================================
# 2. MULTI-CATEGORY MOCKED CROP HEALTH VISION TESTS
# ============================================================================

async def test_mocked_multi_category_suite():
    print("\n--- [TEST SUITE 2] Multi-Category Mocked Diagnosis Tests (SIMULATED) ---")
    print("    NOTE: These tests use simulated responses to verify software architecture.")
    print("    Passing software tests does not imply clinical agronomic validation.\n")

    valid_leaf_bytes = create_test_image(200, 200, color=(34, 139, 34), fmt="JPEG")

    # ------------------------------------------------------------------------
    # CATEGORY 1: PEST AND INSECT DAMAGE (SIMULATED)
    # ------------------------------------------------------------------------
    print("[Category 1: Pest Damage] Testing Yellow Stem Borer / Dead Heart diagnosis (SIMULATED)...")
    mock_pest_json = {
        "is_crop_leaf": True,
        "category": "pest_damage",
        "category_label_en": "Pest & Insect Damage",
        "category_label_ta": "பூச்சி தாக்குதல்",
        "suspected_condition_en": "Yellow Stem Borer (Dead Heart / White Earhead)",
        "suspected_condition_ta": "மஞ்சள் குருத்துப்பூச்சி தாக்குதல்",
        "affected_crop_en": "Paddy / Rice (நெல்)",
        "affected_crop_ta": "நெல்",
        "plant_part": "stem",
        "pathogen_or_causal_agent": "Scirpophaga incertulas (Lepidopteran Insect Pest)",
        "confidence_score": 88,
        "severity_or_urgency": "high",
        "visual_symptoms_observed_en": "Central tiller whorl dried up, turning straw-colored ('dead heart') with tiny entry pinhole at the base.",
        "visual_symptoms_observed_ta": "மத்திய குருத்து காய்ந்து வெண்மையாகியுள்ளது ('டெட் ஹார்ட்'). தண்டின் அடிப்பகுதியில் சிறிய துளை காணப்படுகிறது.",
        "possible_causes_en": [
            "Lepidopteran adult moth egg mass hatching on leaf tips during vegetative stage.",
            "Excess nitrogen fertilizer application leading to lush succulent tillers."
        ],
        "alternative_explanations_en": [
            "Rat or rodent gnawing damage at tiller base.",
            "Early bacterial foot rot infection."
        ],
        "diagnostic_limitations_en": [
            "Visual identification of 'dead heart' can occasionally mimic rodent or fungal foot rot damage.",
            "Requires splitting the stem open in the field to confirm larval presence."
        ],
        "recommended_next_steps_en": [
            "Step 1: Pull the affected central shoot gently; if it slips out easily, stem borer is confirmed.",
            "Step 2: Install pheromone traps @ 5 per acre to monitor adult moth activity."
        ],
        "biological_management_en": [
            "Release egg parasitoid Trichogramma japonicum @ 40,000/acre at weekly intervals.",
            "Clip seedling leaf tips before transplanting to eliminate egg masses."
        ],
        "chemical_treatment_en": [
            "Foliar spray with Chlorantraniliprole 18.5% SC @ 60 ml/acre or Cartap hydrochloride 50% SP @ 400g/acre."
        ],
        "chemical_precautions_en": "Spray when economic threshold level (ETL > 2 egg masses/sq.m or 10% dead hearts) is exceeded.",
        "prevention_tips_en": [
            "Avoid excessive basal urea; practice split application.",
            "Synchronize planting in adjacent fields to avoid continuous host availability."
        ],
        "when_to_consult_expert_en": [
            "When dead hearts exceed 10% across the field during active tillering stage.",
            "Consult your village Assistant Agricultural Officer (AAO) or call toll-free 1800-425-1661."
        ],
        "verified_guidance_references": [
            "TNAU Agritech Portal - Rice Entomology Protocol",
            "ICAR National Rice Research Institute Pest Management Guide"
        ]
    }

    mock_client_cat1 = MagicMock()
    mock_resp_cat1 = MagicMock()
    mock_resp_cat1.text = json.dumps(mock_pest_json)
    mock_client_cat1.aio.models.generate_content = AsyncMock(return_value=mock_resp_cat1)

    res_cat1 = await analyze_leaf_image_with_vision(
        image_bytes=valid_leaf_bytes,
        filename="paddy_stem_borer.jpg",
        content_type="image/jpeg",
        crop_name="Paddy / Rice (நெல்)",
        plant_part="stem",
        client_instance=mock_client_cat1
    )

    assert res_cat1["status"] in ("diagnosed", "suspected")
    assert res_cat1["diagnosis"]["category"] == "pest_damage"
    assert "Stem Borer" in res_cat1["diagnosis"]["suspectedCondition"]
    assert res_cat1["diagnosis"]["plantPart"] == "stem"
    assert res_cat1["diagnosis"]["severityOrUrgency"] == "high"
    assert len(res_cat1["diagnosis"]["possibleCauses"]) >= 1
    assert len(res_cat1["diagnosis"]["alternativeExplanations"]) >= 1
    assert len(res_cat1["diagnosis"]["diagnosticLimitations"]) >= 1
    assert len(res_cat1["diagnosis"]["biologicalManagement"]) >= 1
    assert "Chlorantraniliprole" in res_cat1["diagnosis"]["chemicalTreatment"][0]
    print("  ✓ PASS [Category 1 - Pest Damage]: Correctly categorized with alternative causes & bio-controls.")

    # ------------------------------------------------------------------------
    # CATEGORY 2: PLANT DISEASE (FUNGAL / BACTERIAL / VIRAL) (SIMULATED)
    # ------------------------------------------------------------------------
    print("\n[Category 2: Plant Disease] Testing Rice Leaf Blast - Pyricularia oryzae (SIMULATED)...")
    mock_disease_json = {
        "is_crop_leaf": True,
        "category": "plant_disease",
        "category_label_en": "Plant Disease",
        "category_label_ta": "பயிர் நோய்",
        "suspected_condition_en": "Rice Leaf & Neck Blast",
        "suspected_condition_ta": "நெல் இலைக்கருகல் / குலை நோய்",
        "affected_crop_en": "Paddy / Rice (நெல்)",
        "affected_crop_ta": "நெல்",
        "plant_part": "leaf",
        "pathogen_or_causal_agent": "Pyricularia oryzae (Fungal Pathogen)",
        "confidence_score": 92,
        "severity_or_urgency": "critical",
        "visual_symptoms_observed_en": "Spindle-shaped elliptical lesions with ash-grey center and dark brown necrotic margins.",
        "visual_symptoms_observed_ta": "இலைகளில் கண் வடிவில் சாம்பல் நிற மையமும் பழுப்பு ஓரமும் கொண்ட புள்ளிகள்.",
        "possible_causes_en": [
            "High relative humidity (>90%) with cloudy, rainy microclimate.",
            "Night temperatures below 20°C and heavy dew deposition on leaf canopy."
        ],
        "alternative_explanations_en": [
            "Brown spot (Bipolaris oryzae) which produces circular rather than spindle lesions.",
            "Early leaf scald lesions."
        ],
        "diagnostic_limitations_en": [
            "Visual leaf examination cannot determine systemic neck or node blast until heading stage.",
            "Microscopic spore mount is required for 100% taxonomic certainty."
        ],
        "recommended_next_steps_en": [
            "Immediately avoid top-dressing with nitrogenous fertilizers during active lesion spread.",
            "Maintain proper water depth (2-3 cm) and avoid water stress."
        ],
        "biological_management_en": [
            "Spray Pseudomonas fluorescens @ 1 kg/acre at boot leaf stage.",
            "Apply neem seed kernel extract (NSKE 5%) as preventive foliar wash."
        ],
        "chemical_treatment_en": [
            "Foliar spray with Tricyclazole 75% WP @ 120g/acre or Isoprothiolane 40% EC @ 300 ml/acre."
        ],
        "chemical_precautions_en": "Ensure complete canopy coverage; do not spray when rains are imminent.",
        "prevention_tips_en": [
            "Treat seeds with Carbendazim 2g/kg or Trichoderma viride 4g/kg seed before nursery sowing.",
            "Use certified blast-resistant cultivars such as CR 1009 Sub 1 or ADT 43."
        ],
        "when_to_consult_expert_en": [
            "When spindle lesions coalesce, causing complete leaf blade drying.",
            "Contact your nearest Krishi Vigyan Kendra (KVK) or Assistant Agricultural Officer."
        ],
        "verified_guidance_references": [
            "TNAU Agritech Portal - Rice Pathology Protocol",
            "ICAR National Institute of Plant Health Management"
        ]
    }

    mock_client_cat2 = MagicMock()
    mock_resp_cat2 = MagicMock()
    mock_resp_cat2.text = json.dumps(mock_disease_json)
    mock_client_cat2.aio.models.generate_content = AsyncMock(return_value=mock_resp_cat2)

    res_cat2 = await analyze_leaf_image_with_vision(
        image_bytes=valid_leaf_bytes,
        filename="paddy_blast.jpg",
        content_type="image/jpeg",
        crop_name="Paddy / Rice (நெல்)",
        client_instance=mock_client_cat2
    )

    assert res_cat2["status"] in ("diagnosed", "suspected")
    assert res_cat2["diagnosis"]["category"] == "plant_disease"
    assert "Blast" in res_cat2["diagnosis"]["suspectedCondition"]
    assert res_cat2["diagnosis"]["confidencePercent"] == 92
    assert "Tricyclazole" in res_cat2["diagnosis"]["chemicalTreatment"][0]
    print("  ✓ PASS [Category 2 - Plant Disease]: Identified infectious fungal pathogen with TNAU treatment.")

    # ------------------------------------------------------------------------
    # CATEGORY 3: PHYSIOLOGICAL & ABIOTIC PROBLEMS (SIMULATED)
    # ------------------------------------------------------------------------
    print("\n[Category 3: Abiotic Disorder] Testing Potassium (K) Deficiency / Marginal Firing (SIMULATED)...")
    mock_abiotic_json = {
        "is_crop_leaf": True,
        "category": "abiotic_disorder",
        "category_label_en": "Abiotic & Physiological Disorder",
        "category_label_ta": "உடலியல் / ஊட்டச்சத்து குறைபாடு",
        "suspected_condition_en": "Potassium (K) Deficiency (Marginal Scorch / Firing)",
        "suspected_condition_ta": "பொட்டாசியம் ஊட்டச்சத்து குறைபாடு (இலை ஓர கருகல்)",
        "affected_crop_en": "Paddy / Rice (நெல்)",
        "affected_crop_ta": "நெல்",
        "plant_part": "leaf",
        "pathogen_or_causal_agent": "Abiotic Soil Nutrient Deficiency (Potassium / K Deficit)",
        "confidence_score": 85,
        "severity_or_urgency": "moderate",
        "visual_symptoms_observed_en": "Yellowish-brown marginal chlorosis progressing from tip downward along leaf edges of older leaves, turning necrotic and scorched ('firing').",
        "visual_symptoms_observed_ta": "பழைய இலைகளின் நுனியிலிருந்து ஓரங்களில் பழுப்பு நிறமாக கருகி வரும்.",
        "possible_causes_en": [
            "Inadequate application of Muriate of Potash (MOP) during basal or active tillering stages.",
            "Sandy or light-textured soil with high leaching losses of available potassium.",
            "Poor root aeration in waterlogged, highly reduced soil conditions reducing K uptake."
        ],
        "alternative_explanations_en": [
            "Bacterial leaf blight (which exhibits wavy margins and water soaking, unlike uniform marginal scorch).",
            "Salinity / sodium toxicity injury."
        ],
        "diagnostic_limitations_en": [
            "Visual symptoms cannot quantify exact soil available K levels; a laboratory Soil Health Card test is required.",
            "Multiple nutrient stresses (e.g. Zinc and Potassium) often co-occur in delta alluvial soils."
        ],
        "recommended_next_steps_en": [
            "Send composite soil samples to the nearest Government Soil Testing Laboratory.",
            "Inspect root system for blackening or poor root hair development."
        ],
        "biological_management_en": [
            "Incorporate farmyard manure (FYM @ 5 tons/acre) or composted coir pith to improve soil cation exchange capacity.",
            "Apply potassium-solubilizing bacteria (KSB) biofertilizer @ 2 kg/acre mixed with FYM."
        ],
        "chemical_treatment_en": [
            "CHEMICAL PESTICIDES / FUNGICIDES ARE NOT APPLICABLE FOR ABIOTIC DISORDERS.",
            "Apply Muriate of Potash (MOP - 60% K2O) @ 20 kg/acre as top-dressing or foliar spray of 1% Potassium Chloride (KCl) in early stages."
        ],
        "chemical_precautions_en": "Do not spray chemical fungicides or insecticides; they will not resolve a nutritional deficiency.",
        "prevention_tips_en": [
            "Apply recommended N:P:K ratio (150:50:50 kg/ha for hybrid rice) based on soil test calibration.",
            "Incorporate paddy straw back into the field during land preparation to recycle potassium."
        ],
        "when_to_consult_expert_en": [
            "If marginal scorch persists 10 days after potash application.",
            "Contact your Assistant Agricultural Officer or Agricultural Development Officer (ADO)."
        ],
        "verified_guidance_references": [
            "TNAU Agritech Portal - Rice Nutrient Management Guidelines",
            "Tamil Nadu Department of Agriculture Soil Health Protocol"
        ]
    }

    mock_client_cat3 = MagicMock()
    mock_resp_cat3 = MagicMock()
    mock_resp_cat3.text = json.dumps(mock_abiotic_json)
    mock_client_cat3.aio.models.generate_content = AsyncMock(return_value=mock_resp_cat3)

    res_cat3 = await analyze_leaf_image_with_vision(
        image_bytes=valid_leaf_bytes,
        filename="paddy_potash_deficiency.jpg",
        content_type="image/jpeg",
        crop_name="Paddy / Rice (நெல்)",
        client_instance=mock_client_cat3
    )

    assert res_cat3["status"] in ("diagnosed", "suspected")
    assert res_cat3["diagnosis"]["category"] == "abiotic_disorder"
    assert "Potassium" in res_cat3["diagnosis"]["suspectedCondition"]
    assert "NOT APPLICABLE" in res_cat3["diagnosis"]["chemicalTreatment"][0]
    assert "KSB" in res_cat3["diagnosis"]["biologicalManagement"][1] or "biofertilizer" in res_cat3["diagnosis"]["biologicalManagement"][1]
    print("  ✓ PASS [Category 3 - Abiotic Disorder]: Accurately identified nutrient stress; chemical pesticides withheld.")

    # ------------------------------------------------------------------------
    # CATEGORY 4: INCONCLUSIVE / BLURRY / INSUFFICIENT EVIDENCE (SIMULATED)
    # ------------------------------------------------------------------------
    print("\n[Category 4: Inconclusive] Testing Blurry / Insufficient Evidence Photo (SIMULATED)...")
    mock_inconclusive_json = {
        "is_crop_leaf": False,
        "category": "inconclusive",
        "category_label_en": "Inconclusive Specimen",
        "category_label_ta": "முடிவற்ற மாதிரி",
        "inconclusive_reason_en": "The photograph is out of focus and has high glare; insufficient diagnostic visual cues.",
        "inconclusive_reason_ta": "புகைப்படம் மங்கலாக உள்ளது; தெளிவான அறிகுறிகள் இல்லை."
    }

    mock_client_cat4 = MagicMock()
    mock_resp_cat4 = MagicMock()
    mock_resp_cat4.text = json.dumps(mock_inconclusive_json)
    mock_client_cat4.aio.models.generate_content = AsyncMock(return_value=mock_resp_cat4)

    res_cat4 = await analyze_leaf_image_with_vision(
        image_bytes=valid_leaf_bytes,
        filename="blurry_leaf.jpg",
        content_type="image/jpeg",
        client_instance=mock_client_cat4
    )

    assert res_cat4["status"] == "inconclusive"
    assert "inconclusive" in res_cat4["messageEn"].lower() or "sufficient" in res_cat4["messageEn"].lower()
    print("  ✓ PASS [Category 4 - Inconclusive]: Truthfully reported insufficient evidence without guessing.")

    # ------------------------------------------------------------------------
    # STRICT UNTRUSTED MODEL VALIDATION
    # ------------------------------------------------------------------------
    print("\n[Schema Validation] Testing rejection of unsupported arbitrary categories...")
    bogus_model_output = json.dumps({
        "category": "space_alien_infection",  # Invalid arbitrary category
        "suspected_condition_en": "Martian Blight",
        "confidence_score": 999  # Invalid uncalibrated score
    })
    is_ok, diag, err = parse_and_validate_diagnosis(bogus_model_output)
    # System should sanitize invalid category to inconclusive and clamp confidence
    assert is_ok and diag is not None
    assert diag.category == "inconclusive"
    assert diag.confidencePercent <= 100
    print("  ✓ PASS [Untrusted Input Defense]: Arbitrary category rejected and mapped safely to inconclusive.")

    # ------------------------------------------------------------------------
    # TEST E: Backward Compatibility Test Stub Handling (< 100 bytes)
    # ------------------------------------------------------------------------
    print("\n[Regression Check] Testing legacy test stub handling (sub-100 byte stub)...")
    test_stub = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00" + b"\x00" * 40
    res_stub = await analyze_leaf_image_with_vision(
        image_bytes=test_stub,
        filename="test_leaf.jpg",
        content_type="image/jpeg"
    )

    assert res_stub["status"] == "not_configured"
    assert res_stub["testedModelPresent"] is False
    print("  ✓ PASS [Regression Safety]: Legacy test stubs correctly return status='not_configured'.")


# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    print("=======================================================================")
    print("NAMMA VIVASAYI AI - MULTI-CATEGORY CROP HEALTH DIAGNOSIS TEST RUNNER")
    print("=======================================================================")

    # 1. Image validation
    test_image_validation()

    # 2. Multi-category mocked suite
    asyncio.run(test_mocked_multi_category_suite())

    print("\n=======================================================================")
    print("ALL MULTI-CATEGORY CROP HEALTH UNIT TESTS PASSED SUCCESSFULLY!")
    print("=======================================================================")
    print("SCIENTIFIC INTEGRITY DISCLAIMER:")
    print("Unit tests verify software pipeline behavior with simulated responses.")
    print("Passing software tests does not imply clinical agronomic validation.")
    print("=======================================================================\n")


if __name__ == "__main__":
    main()

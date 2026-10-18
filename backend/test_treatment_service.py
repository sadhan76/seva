"""
NAMMA VIVASAYI AI - AUTOMATED TREATMENT SERVICE TEST SUITE (SIMULATED)
=======================================================================
Verifies the reliable agricultural treatment recommendation service grounded in:
- Tamil Nadu Agricultural University (TNAU) Agritech Portal & Crop Protection Guide
- Indian Council of Agricultural Research (ICAR)
- Central Insecticides Board & Registration Committee (CIBRC)

SCIENTIFIC INTEGRITY DISCLAIMER:
These automated tests verify software logic, data integrity, safety enforcement,
and schema adherence. Passing these tests verifies system reliability, NOT clinical
or field-level agronomic efficacy.
"""

import sys
import unittest
from fastapi.testclient import TestClient

from main import app
from treatment_service import (
    get_verified_treatment_recommendation,
    build_uncertain_or_inconclusive_guidance,
    AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE,
    VerifiedTreatmentGuidance,
)


class TestAuthoritativeTreatmentService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ------------------------------------------------------------------------
    # 1. CATEGORY 1: PEST DAMAGE - CROP SPECIFIC & SOURCE BACKED
    # ------------------------------------------------------------------------
    def test_category1_pest_rice_stem_borer(self):
        """[SIMULATED] Verify crop-specific treatment for Paddy Yellow Stem Borer."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy / Rice",
            condition_name="Yellow Stem Borer (Scirpophaga incertulas)",
            category="pest_damage",
            confidence_percent=88,
            is_crop_leaf=True,
            language="en"
        )
        self.assertIsInstance(rec, VerifiedTreatmentGuidance)
        self.assertEqual(rec.category, "pest_damage")
        self.assertEqual(rec.conditionKey, "yellow_stem_borer")

        # Biological management verification
        bio = rec.biologicalManagement
        self.assertTrue(any("Trichogramma" in b for b in bio.biologicalControlAgents))
        self.assertTrue(any("pheromone" in b.lower() for b in bio.biologicalControlAgents))
        self.assertTrue(any("dead heart" in s.lower() for s in bio.fieldSanitation))

        # Chemical treatment verification
        chem = rec.chemicalManagement
        self.assertTrue(chem.isApplicable)
        self.assertIn("Chlorantraniliprole 18.5% SC", chem.activeIngredient)
        self.assertIn("60 ml", chem.dosageAndApplication)
        self.assertEqual(chem.preHarvestIntervalDays, 21)
        self.assertEqual(chem.reEntryIntervalHours, 24)
        self.assertTrue(len(chem.personalProtectiveEquipment) >= 2)
        self.assertIn("CIBRC", chem.cibrcRegistrationStatus)

        # References verification
        self.assertTrue(any("TNAU" in r.organization for r in rec.references))
        self.assertTrue(any(r.url and "agritech.tnau.ac.in" in r.url for r in rec.references))

    def test_category1_pest_rice_bph(self):
        """[SIMULATED] Verify crop-specific treatment for Paddy Brown Planthopper (BPH)."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy",
            condition_name="Brown Planthopper",
            category="pest_damage",
            confidence_percent=92,
            is_crop_leaf=True
        )
        self.assertEqual(rec.conditionKey, "brown_planthopper")
        self.assertTrue(rec.chemicalManagement.isApplicable)
        self.assertIn("Triflumezopyrim 10% SC", rec.chemicalManagement.activeIngredient)
        self.assertIn("94 ml", rec.chemicalManagement.dosageAndApplication)
        self.assertTrue(any("alleyway" in c.lower() for c in rec.biologicalManagement.culturalPractices))
        self.assertTrue(any("Alternate Wetting" in c for c in rec.biologicalManagement.culturalPractices))

    # ------------------------------------------------------------------------
    # 2. CATEGORY 2: PLANT DISEASE - FUNGAL & BACTERIAL PATHOGENS
    # ------------------------------------------------------------------------
    def test_category2_disease_rice_blast(self):
        """[SIMULATED] Verify crop-specific treatment for Rice Leaf Blast (Pyricularia oryzae)."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy / Rice",
            condition_name="Rice Blast",
            category="plant_disease",
            confidence_percent=85,
            is_crop_leaf=True,
            language="en"
        )
        self.assertEqual(rec.conditionKey, "rice_blast")
        self.assertEqual(rec.category, "plant_disease")

        # Resistant varieties
        self.assertTrue(any("ADT 43" in v or "TPS 5" in v for v in rec.biologicalManagement.cropRotationAndVarieties))

        # Bio-agent
        self.assertTrue(any("Pseudomonas fluorescens" in b for b in rec.biologicalManagement.biologicalControlAgents))

        # Approved chemical
        self.assertTrue(rec.chemicalManagement.isApplicable)
        self.assertIn("Tricyclazole 75% WP", rec.chemicalManagement.activeIngredient)
        self.assertIn("120 g", rec.chemicalManagement.dosageAndApplication)
        self.assertEqual(rec.chemicalManagement.preHarvestIntervalDays, 30)
        self.assertIn("CIBRC", rec.chemicalManagement.cibrcRegistrationStatus)

    def test_category2_disease_groundnut_tikka(self):
        """[SIMULATED] Verify crop-specific treatment for Groundnut Tikka Leaf Spot."""
        rec = get_verified_treatment_recommendation(
            crop="Groundnut",
            condition_name="Tikka Leaf Spot",
            category="plant_disease",
            confidence_percent=89,
            is_crop_leaf=True
        )
        self.assertEqual(rec.conditionKey, "tikka_leaf_spot")
        self.assertTrue(rec.chemicalManagement.isApplicable)
        self.assertIn("Mancozeb 75% WP", rec.chemicalManagement.activeIngredient)
        self.assertTrue(any("Trichoderma" in b for b in rec.biologicalManagement.biologicalControlAgents))
        self.assertTrue(any("gypsum" in n.lower() for n in rec.biologicalManagement.soilAndNutrientManagement))

    # ------------------------------------------------------------------------
    # 3. CATEGORY 3: ABIOTIC / PHYSIOLOGICAL - STRICT CHEMICAL PROHIBITION
    # ------------------------------------------------------------------------
    def test_category3_abiotic_potassium_deficiency_prohibits_pesticides(self):
        """[SIMULATED] STRICT RULE: Verify pesticides are strictly NOT applicable for abiotic disorders."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy",
            condition_name="Potassium Deficiency",
            category="abiotic_disorder",
            confidence_percent=94,
            is_crop_leaf=True
        )
        self.assertEqual(rec.category, "abiotic_disorder")
        self.assertEqual(rec.conditionKey, "potassium_deficiency")

        # STRICT SAFETY RULE: Chemical is NOT applicable
        chem = rec.chemicalManagement
        self.assertFalse(chem.isApplicable)
        self.assertIsNotNone(chem.inapplicableReason)
        self.assertIn("NOT APPLICABLE", chem.inapplicableReason)
        self.assertIsNone(chem.activeIngredient)
        self.assertIsNone(chem.dosageAndApplication)

        # Agronomic correction must focus on soil / foliar nutrition
        bio = rec.biologicalManagement
        self.assertTrue(any("Potassium Solubilizing" in b or "KSB" in b for b in bio.biologicalControlAgents))
        self.assertTrue(any("Muriate of Potash" in n or "MOP" in n for n in bio.soilAndNutrientManagement))
        self.assertTrue(any("Potassium Nitrate" in n or "KNO3" in n for n in bio.soilAndNutrientManagement))

    def test_category3_abiotic_zinc_deficiency_prohibits_pesticides(self):
        """[SIMULATED] STRICT RULE: Verify Zinc deficiency prohibits chemical pesticides."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy",
            condition_name="Zinc Deficiency / Khaira Disease",
            category="abiotic_disorder",
            confidence_percent=90,
            is_crop_leaf=True
        )
        self.assertEqual(rec.category, "abiotic_disorder")
        self.assertFalse(rec.chemicalManagement.isApplicable)
        self.assertIn("NOT APPLICABLE", rec.chemicalManagement.inapplicableReason)
        self.assertTrue(any("Zinc sulphate" in s for s in rec.biologicalManagement.soilAndNutrientManagement))

    # ------------------------------------------------------------------------
    # 4. UNCERTAIN / INCONCLUSIVE DIAGNOSIS - DEFENSIVE WITHHOLDING
    # ------------------------------------------------------------------------
    def test_inconclusive_diagnosis_withholds_chemical_treatments(self):
        """[SIMULATED] STRICT RULE: Uncertain or blurry specimens must not recommend chemical pesticides."""
        rec = get_verified_treatment_recommendation(
            crop="Paddy",
            condition_name="Unidentified Blurry Lesion",
            category="inconclusive",
            confidence_percent=15,  # Low uncalibrated confidence
            is_crop_leaf=True
        )
        self.assertEqual(rec.category, "inconclusive")
        self.assertTrue(rec.isUncertainOrInconclusive)
        self.assertFalse(rec.chemicalManagement.isApplicable)
        self.assertIn("MUST NOT BE SELECTED SOLELY", rec.chemicalManagement.inapplicableReason)
        self.assertIsNone(rec.chemicalManagement.activeIngredient)
        self.assertTrue(any("Assistant Agricultural Officer" in o or "AAO" in o for o in rec.whenToConsultOfficer))

    def test_non_crop_specimen_returns_inconclusive(self):
        """[SIMULATED] Non-crop uploads safely return inconclusive guidance."""
        rec = get_verified_treatment_recommendation(
            crop="Living Room Floor",
            condition_name="Unknown Object",
            category="inconclusive",
            confidence_percent=0,
            is_crop_leaf=False
        )
        self.assertEqual(rec.category, "inconclusive")
        self.assertTrue(rec.isUncertainOrInconclusive)
        self.assertFalse(rec.chemicalManagement.isApplicable)

    # ------------------------------------------------------------------------
    # 5. UNMAPPED / UNCATALOGED CONDITION - SAFE EXTENSION FALLBACK
    # ------------------------------------------------------------------------
    def test_unmapped_condition_fails_safely_without_fabrication(self):
        """[SIMULATED] Never invent chemical brands or dosages for uncataloged conditions."""
        rec = get_verified_treatment_recommendation(
            crop="Dragonfruit",
            condition_name="Mysterious Purple Spotting",
            category="plant_disease",
            confidence_percent=60,
            is_crop_leaf=True
        )
        self.assertEqual(rec.conditionKey, "unmapped_condition")
        self.assertFalse(rec.chemicalManagement.isApplicable)
        self.assertIn("WITHHELD", rec.chemicalManagement.inapplicableReason)
        self.assertIsNone(rec.chemicalManagement.activeIngredient)
        self.assertTrue(any("Assistant Agricultural Officer" in o for o in rec.whenToConsultOfficer))

    def test_unmapped_condition_in_vision_preserves_diagnosed_status(self):
        """[SIMULATED] Valid diagnosis must remain status='diagnosed' even when treatment is unmapped."""
        import asyncio
        from unittest.mock import MagicMock
        from plant_vision import analyze_leaf_image_with_vision, prepare_image_for_vision
        from PIL import Image
        import io, json

        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 200, 0)).save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        mock_client = MagicMock()
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()

        async def mock_gen(*args, **kwargs):
            m = MagicMock()
            m.text = json.dumps({
                "is_crop_leaf": True,
                "category": "plant_disease",
                "category_label_en": "Plant Disease",
                "category_label_ta": "பயிர் நோய்",
                "suspected_condition_en": "Rare Uncataloged Leaf Spot",
                "affected_crop_en": "Dragonfruit",
                "confidence_score": 78,
                "severity_or_urgency": "moderate",
                "visual_symptoms_observed_en": "Unusual purple concentric rings.",
                "possible_causes_en": ["Novel fungus"],
                "biological_management_en": ["Remove affected foliage"],
                "chemical_treatment_en": [],
                "prevention_tips_en": ["Clean tools"]
            })
            return m

        mock_client.aio.models.generate_content = mock_gen
        res = asyncio.run(analyze_leaf_image_with_vision(image_bytes=img_bytes, client_instance=mock_client))
        
        # Must retain status='diagnosed' (never downgraded to inconclusive)
        self.assertEqual(res["status"], "diagnosed")
        self.assertEqual(res["diagnosis"]["suspectedCondition"], "Rare Uncataloged Leaf Spot")
        # Treatment must be attached with chemicals safely withheld
        self.assertIsNotNone(res["verifiedTreatment"])
        self.assertEqual(res["verifiedTreatment"]["conditionKey"], "unmapped_condition")
        self.assertFalse(res["verifiedTreatment"]["chemicalManagement"]["isApplicable"])
        self.assertIn("WITHHELD", res["verifiedTreatment"]["chemicalManagement"]["inapplicableReason"])


    # ------------------------------------------------------------------------
    # 6. BILINGUAL SUPPORT & PRESERVATION OF TECHNICAL TERMS
    # ------------------------------------------------------------------------
    def test_bilingual_support_preserves_technical_names(self):
        """[SIMULATED] Verify Tamil output preserves chemical names, dosages, and safety metrics."""
        rec_ta = get_verified_treatment_recommendation(
            crop="Paddy",
            condition_name="Rice Blast",
            category="plant_disease",
            confidence_percent=85,
            is_crop_leaf=True,
            language="ta"
        )
        # Tamil names provided
        self.assertEqual(rec_ta.cropTa, "நெல்")
        self.assertIn("குலை நோய்", rec_ta.conditionNameTa)
        self.assertIn("பூஞ்சாணம்", rec_ta.categoryLabelTa)

        # Technical active ingredients and units remain scientifically standardized
        self.assertIn("Tricyclazole 75% WP", rec_ta.chemicalManagement.activeIngredient)
        self.assertIn("120 g per acre", rec_ta.chemicalManagement.dosageAndApplication)
        self.assertEqual(rec_ta.chemicalManagement.preHarvestIntervalDays, 30)
        self.assertEqual(rec_ta.chemicalManagement.reEntryIntervalHours, 24)

    # ------------------------------------------------------------------------
    # 7. BACKEND API ENDPOINT VERIFICATION
    # ------------------------------------------------------------------------
    def test_get_disease_treatment_api_endpoint(self):
        """[SIMULATED] Verify GET /api/disease/treatment endpoint functionality."""
        response = self.client.get(
            "/api/disease/treatment",
            params={
                "crop": "Paddy / Rice",
                "condition": "Rice Leaf Blast",
                "category": "plant_disease",
                "confidence": 85,
                "language": "en"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["conditionKey"], "rice_blast")
        self.assertTrue(data["chemicalManagement"]["isApplicable"])
        self.assertEqual(data["chemicalManagement"]["activeIngredient"], "Tricyclazole 75% WP")
        self.assertTrue(len(data["references"]) >= 1)

    def test_get_disease_treatment_api_abiotic_endpoint(self):
        """[SIMULATED] Verify GET /api/disease/treatment correctly rejects chemicals for abiotic input."""
        response = self.client.get(
            "/api/disease/treatment",
            params={
                "crop": "Paddy",
                "condition": "Potassium Deficiency",
                "category": "abiotic_disorder",
                "confidence": 90,
                "language": "en"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["chemicalManagement"]["isApplicable"])
        self.assertIn("NOT APPLICABLE", data["chemicalManagement"]["inapplicableReason"])


if __name__ == "__main__":
    print("\n" + "=" * 75)
    print("NAMMA VIVASAYI AI - AUTHORITATIVE TREATMENT SERVICE TEST RUNNER")
    print("=" * 75)
    print("NOTE: Automated software verification tests using simulated agronomic data.")
    print("Passing software tests does not imply clinical agronomic validation.\n")
    unittest.main()

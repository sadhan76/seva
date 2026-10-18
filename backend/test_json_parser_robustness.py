"""
Test Suite for Balanced-Brace JSON Parser & Category Normalization in Plant Vision Engine.
Covers Requirement 3 and Requirement 4:
- Nested objects
- Arrays of objects
- Escaped quotes
- Braces inside strings
- Markdown code fences (both ```json and ```)
- Trailing commas before } and ]
- Empty output
- Truncated output
- Preceding/trailing explanatory text
- Category normalization safety against unsupported/fabricated certainty
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plant_vision import extract_json_object, normalize_diagnosis_category, normalize_severity, parse_and_validate_diagnosis

class TestBalancedBraceJsonParser(unittest.TestCase):

    def test_nested_objects(self):
        text = '{"outer": {"middle": {"inner": {"level": 4, "name": "deep"}}}}'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["outer"]["middle"]["inner"]["level"], 4)
        self.assertEqual(parsed["outer"]["middle"]["inner"]["name"], "deep")

    def test_arrays_of_objects(self):
        text = '{"diagnoses": [{"id": 1, "name": "Blast"}, {"id": 2, "name": "Blight"}]}'
        parsed = extract_json_object(text)
        self.assertEqual(len(parsed["diagnoses"]), 2)
        self.assertEqual(parsed["diagnoses"][1]["name"], "Blight")

    def test_escaped_quotes(self):
        text = '{"symptom": "Farmer said \\"severe burning\\" on tips", "confirmed": true}'
        parsed = extract_json_object(text)
        self.assertIn('"severe burning"', parsed["symptom"])
        self.assertTrue(parsed["confirmed"])

    def test_braces_inside_strings(self):
        text = '{"notes": "Pattern matches {concentric rings} on foliar surface", "score": 90}'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["notes"], "Pattern matches {concentric rings} on foliar surface")
        self.assertEqual(parsed["score"], 90)

    def test_markdown_code_fence_json(self):
        text = 'Here is the diagnosis:\n```json\n{\n  "category": "plant_disease",\n  "confidence_score": 85\n}\n```\nContact AAO.'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["category"], "plant_disease")
        self.assertEqual(parsed["confidence_score"], 85)

    def test_markdown_code_fence_generic(self):
        text = 'Result:\n```\n{\n  "category": "pest_damage",\n  "confidence_score": 75\n}\n```'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["category"], "pest_damage")
        self.assertEqual(parsed["confidence_score"], 75)

    def test_trailing_commas(self):
        text = '{\n  "category": "healthy",\n  "crops": ["Paddy", "Cotton",],\n  "score": 100,\n}'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["category"], "healthy")
        self.assertEqual(parsed["crops"], ["Paddy", "Cotton"])
        self.assertEqual(parsed["score"], 100)

    def test_empty_output_raises_value_error(self):
        with self.assertRaises(ValueError):
            extract_json_object("")
        with self.assertRaises(ValueError):
            extract_json_object("   \n\t  ")

    def test_truncated_output_raises_value_error(self):
        # Incomplete truncated JSON where braces do not balance
        with self.assertRaises(ValueError):
            extract_json_object('{"category": "plant_disease", "suspected_condition": "Rice Blast", "visual_symp')

    def test_preamble_and_postamble_text(self):
        text = 'The AI model evaluated the image and determined:\n{"category": "abiotic_disorder", "confidence_score": 80}\nThis is advisory only.'
        parsed = extract_json_object(text)
        self.assertEqual(parsed["category"], "abiotic_disorder")
        self.assertEqual(parsed["confidence_score"], 80)


class TestCategoryNormalizationSafety(unittest.TestCase):
    """
    Requirement 4: Verify that category normalization cannot turn malformed
    or unsupported model output into an unjustifiably certain diagnosis.
    """

    def test_unsupported_categories_map_to_inconclusive(self):
        unsupported_samples = [
            "alien_infection",
            "unknown_pathology",
            "crypto_virus",
            "random_gibberish",
            "maybe_pest_maybe_not",
            "partially_diseased_maybe",
            "inconclusive_specimen",
            "none",
            "",
            None
        ]
        for sample in unsupported_samples:
            normalized = normalize_diagnosis_category(sample)
            self.assertEqual(
                normalized, "inconclusive",
                f"Unsupported category '{sample}' must normalize to 'inconclusive', got '{normalized}'"
            )

    def test_legitimate_variations_normalize_accurately(self):
        self.assertEqual(normalize_diagnosis_category("pest"), "pest_damage")
        self.assertEqual(normalize_diagnosis_category("insects"), "pest_damage")
        self.assertEqual(normalize_diagnosis_category("insect_damage"), "pest_damage")
        self.assertEqual(normalize_diagnosis_category("fungal"), "plant_disease")
        self.assertEqual(normalize_diagnosis_category("bacterial_disease"), "plant_disease")
        self.assertEqual(normalize_diagnosis_category("viral"), "plant_disease")
        self.assertEqual(normalize_diagnosis_category("nutrient_deficiency"), "abiotic_disorder")
        self.assertEqual(normalize_diagnosis_category("physiological"), "abiotic_disorder")
        self.assertEqual(normalize_diagnosis_category("healthy_crop"), "healthy")

    def test_malformed_json_never_creates_fabricated_diagnosis(self):
        is_ok, diag, err = parse_and_validate_diagnosis("This is not JSON at all.")
        self.assertFalse(is_ok)
        self.assertIsNone(diag)
        self.assertIn("not valid JSON", err)

    def test_fabricated_category_in_full_json_maps_safely_to_inconclusive(self):
        raw_json = '{"is_crop_leaf": true, "category": "extraterrestrial_fungus", "confidence_score": 99}'
        is_ok, diag, err = parse_and_validate_diagnosis(raw_json)
        self.assertTrue(is_ok)
        self.assertIsNotNone(diag)
        self.assertEqual(diag.category, "inconclusive")


if __name__ == "__main__":
    unittest.main()

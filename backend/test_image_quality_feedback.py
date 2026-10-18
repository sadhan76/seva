"""
NAMMA VIVASAYI AI - IMAGE QUALITY FEEDBACK & PRE-ANALYSIS TRIAGE TESTS (PHASE C)
==============================================================================
Tests photographic quality heuristics:
1. Normal sharp foliage acceptance.
2. Severe darkness / underexposure rejection with retake guidance.
3. Excessive blur detection with retake instructions.
4. Non-plant image detection (low vegetation pixel fraction).
5. Verification that quality screening never invents a disease diagnosis.
"""

import sys
import os
import io
import unittest
import asyncio
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plant_vision import assess_leaf_image_quality, analyze_crop_health_image


class TestImageQualityFeedback(unittest.TestCase):

    def test_sharp_green_foliage_accepted(self):
        """A normal, clear photograph with green foliage passes quality triage."""
        img = Image.new("RGB", (320, 320), color=(34, 139, 34))
        draw = ImageDraw.Draw(img)
        # Add distinct leaf venation edges
        for y in range(40, 280, 20):
            draw.line([(50, y), (270, y)], fill=(144, 238, 144), width=3)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)

        assessment = assess_leaf_image_quality(buf.getvalue())
        self.assertTrue(assessment["isAcceptable"])
        self.assertGreaterEqual(assessment["qualityScore"], 70)
        self.assertGreaterEqual(assessment["plantPixelFraction"], 0.8)
        self.assertEqual(len(assessment["warnings"]), 0)

    def test_excessively_dark_image_detected(self):
        """Images that are too dark (underexposed) receive specific retake guidance."""
        dark_img = Image.new("RGB", (200, 200), color=(8, 8, 8))
        buf = io.BytesIO()
        dark_img.save(buf, format="JPEG")

        assessment = assess_leaf_image_quality(buf.getvalue())
        self.assertFalse(assessment["isAcceptable"])
        self.assertLess(assessment["luminance"], 20.0)
        self.assertTrue(any("dark" in w.lower() or "underexposed" in w.lower() for w in assessment["warnings"]))
        self.assertTrue(len(assessment["retakeGuidanceEn"]) > 0)
        self.assertTrue(len(assessment["retakeGuidanceTa"]) > 0)

    def test_blurry_image_triggers_focus_guidance(self):
        """Severely out-of-focus images trigger blur warnings and screen-tap focus guidance."""
        img = Image.new("RGB", (200, 200), color=(46, 125, 50))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 150, 150], fill=(200, 180, 50))
        blurred = img.filter(ImageFilter.GaussianBlur(radius=25))
        buf = io.BytesIO()
        blurred.save(buf, format="JPEG")

        assessment = assess_leaf_image_quality(buf.getvalue())
        # Should flag blur or low edge variance
        self.assertLess(assessment["edgeVariance"], 180.0)
        self.assertTrue(any("blur" in w.lower() or "focus" in w.lower() for w in assessment["warnings"]))
        self.assertTrue(any("focus" in g.lower() for g in assessment["retakeGuidanceEn"]))

    def test_non_plant_material_detected(self):
        """Images lacking botanical color profiles are flagged with foliage framing guidance."""
        # Solid blue image representing metallic sheet or non-crop wall
        blue_img = Image.new("RGB", (250, 250), color=(20, 60, 210))
        buf = io.BytesIO()
        blue_img.save(buf, format="JPEG")

        assessment = assess_leaf_image_quality(buf.getvalue())
        self.assertFalse(assessment["isAcceptable"])
        self.assertLess(assessment["plantPixelFraction"], 0.05)
        self.assertTrue(any("foliage" in w.lower() or "plant" in w.lower() for w in assessment["warnings"]))

    def test_unviable_image_returns_inconclusive_without_diagnosing(self):
        """When an image fails quality screening, the engine returns status='inconclusive' without fabricating a disease."""
        dark_bytes = io.BytesIO()
        Image.new("RGB", (200, 200), color=(5, 5, 5)).save(dark_bytes, format="JPEG")

        res = asyncio.run(analyze_crop_health_image(
            image_bytes=dark_bytes.getvalue(),
            filename="pitch_dark_specimen.jpg",
            content_type="image/jpeg"
        ))

        self.assertEqual(res["status"], "inconclusive")
        self.assertIn("imageQuality", res)
        self.assertFalse(res["imageQuality"]["isAcceptable"])
        self.assertNotIn("suspectedCondition", res)  # No condition fabricated!
        self.assertTrue(len(res["safeNextSteps"]) > 0)


if __name__ == "__main__":
    unittest.main()

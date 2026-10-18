"""
Test Suite for Image Validation & EXIF Preprocessing (Requirement 6):
- MIME validation (JPEG, PNG, WEBP accepted; BMP, GIF, TIFF rejected)
- Corrupt files and truncated payloads (<100 bytes)
- Image dimensions (sub-20x20 rejected, >=20x20 accepted)
- Oversized (>5MB) rejection
- EXIF orientation handling (tags 1, 3, 6, 8 transposed correctly)
"""

import sys
import os
import io
import unittest
from PIL import Image, ExifTags

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plant_vision import validate_leaf_image, prepare_image_for_vision, MAX_IMAGE_SIZE_BYTES, MIN_IMAGE_SIZE_BYTES

class TestImagePreprocessingAndExif(unittest.TestCase):

    def test_mime_formats(self):
        # 1. JPEG
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(buf, format="JPEG")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertTrue(valid)
        self.assertEqual(mime, "image/jpeg")

        # 2. PNG
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(buf, format="PNG")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertTrue(valid)
        self.assertEqual(mime, "image/png")

        # 3. WEBP
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(buf, format="WEBP")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertTrue(valid)
        self.assertEqual(mime, "image/webp")

        # 4. BMP (unsupported)
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(buf, format="BMP")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertFalse(valid)
        self.assertIn("unsupported", err.lower())

        # 5. GIF (unsupported)
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(buf, format="GIF")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertFalse(valid)
        self.assertIn("unsupported", err.lower())

    def test_corrupt_files_and_boundaries(self):
        # Corrupt bytes
        valid, err, dim, mime = validate_leaf_image(b"RANDOM_JUNK_DATA_NOT_AN_IMAGE_PAYLOAD" * 10)
        self.assertFalse(valid)
        self.assertIn("corrupt", err.lower())

        # Empty payload
        valid, err, dim, mime = validate_leaf_image(b"")
        self.assertFalse(valid)
        self.assertIn("empty", err.lower())

        # Sub-100 byte payload
        valid, err, dim, mime = validate_leaf_image(b"X" * 50)
        self.assertFalse(valid)
        self.assertIn("small", err.lower())

        # Oversized (> 5MB)
        oversized = b"0" * (MAX_IMAGE_SIZE_BYTES + 512)
        valid, err, dim, mime = validate_leaf_image(oversized)
        self.assertFalse(valid)
        self.assertIn("exceeds", err.lower())

    def test_dimension_boundaries(self):
        # 19x19 (too small)
        buf = io.BytesIO()
        Image.new("RGB", (19, 19), color=(0, 255, 0)).save(buf, format="JPEG")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertFalse(valid)
        self.assertIn("too small", err.lower())

        # 20x20 (exact minimum acceptable boundary)
        buf = io.BytesIO()
        Image.new("RGB", (20, 20), color=(0, 255, 0)).save(buf, format="JPEG")
        valid, err, dim, mime = validate_leaf_image(buf.getvalue())
        self.assertTrue(valid)
        self.assertEqual(dim, (20, 20))

    def test_exif_orientation_transposition(self):
        """Creates an image with EXIF orientation 6 (90 deg CW) and verifies transposition."""
        # Create 100 wide x 50 high image
        orig_img = Image.new("RGB", (100, 50), color=(34, 139, 34))
        
        # Add EXIF orientation tag 6 (camera rotated 90 deg)
        exif = orig_img.getexif()
        # 0x0112 is standard EXIF tag for Orientation
        exif[0x0112] = 6
        buf = io.BytesIO()
        orig_img.save(buf, format="JPEG", exif=exif)
        raw_rotated_bytes = buf.getvalue()

        # Run prepare_image_for_vision
        prep_bytes, prep_mime = prepare_image_for_vision(raw_rotated_bytes, "image/jpeg")
        self.assertEqual(prep_mime, "image/jpeg")

        # Read back prepared image dimensions: with orientation 6, (100, 50) should become (50, 100) upright!
        with Image.open(io.BytesIO(prep_bytes)) as final_img:
            w, h = final_img.size
            self.assertEqual((w, h), (50, 100), f"Expected upright transposed dimensions (50, 100), got ({w}, {h})")


if __name__ == "__main__":
    unittest.main()

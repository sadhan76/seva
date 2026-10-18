import os
import sys
import io
import asyncio
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from plant_vision import (
    PLANT_VISION_SYSTEM_INSTRUCTION,
    build_vision_prompt,
    parse_and_validate_diagnosis,
    DEFAULT_VISION_MODEL,
    analyze_leaf_image_with_vision
)

def make_healthy_leaf():
    """Vigorous healthy green leaf with realistic shading."""
    img = Image.new("RGB", (400, 400), color=(240, 248, 240))
    draw = ImageDraw.Draw(img)
    # Draw leaf shape
    draw.polygon([(200, 30), (320, 150), (280, 320), (200, 370), (120, 320), (80, 150)], fill=(34, 139, 34))
    # Main vein
    draw.line([(200, 40), (200, 360)], fill=(144, 238, 144), width=4)
    # Side veins
    for y in range(80, 340, 35):
        draw.line([(200, y), (140, y - 25)], fill=(144, 238, 144), width=2)
        draw.line([(200, y), (260, y - 25)], fill=(144, 238, 144), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_pest_chewed_leaf():
    """Leaf with insect holes, chewed margins, and a visible caterpillar."""
    img = Image.new("RGB", (400, 400), color=(245, 245, 240))
    draw = ImageDraw.Draw(img)
    # Leaf
    draw.polygon([(200, 30), (320, 150), (280, 320), (200, 370), (120, 320), (80, 150)], fill=(46, 125, 50))
    # Chewed holes (background showing through with ragged brown edges)
    draw.ellipse([140, 100, 180, 150], fill=(245, 245, 240), outline=(101, 67, 33))
    draw.ellipse([210, 160, 260, 220], fill=(245, 245, 240), outline=(101, 67, 33))
    draw.ellipse([160, 230, 200, 280], fill=(245, 245, 240), outline=(101, 67, 33))
    # Visible green/black caterpillar body
    draw.line([(220, 120), (260, 140)], fill=(30, 70, 32), width=8)
    draw.ellipse([258, 137, 266, 145], fill=(20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_abiotic_potassium_deficiency():
    """Leaf with distinct marginal firing/scorching around the entire leaf edge."""
    img = Image.new("RGB", (400, 400), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Leaf inner green
    draw.polygon([(200, 40), (300, 160), (260, 310), (200, 360), (140, 310), (100, 160)], fill=(50, 150, 50))
    # Outer scorched yellow and brown margin
    draw.polygon([(200, 30), (320, 150), (280, 320), (200, 370), (120, 320), (80, 150)], outline=(184, 134, 11), width=8)
    draw.line([(80, 150), (120, 320)], fill=(139, 69, 19), width=5)
    draw.line([(320, 150), (280, 320)], fill=(139, 69, 19), width=5)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_blurry_ambiguous():
    """Extremely blurry out-of-focus image."""
    img = Image.new("RGB", (400, 400), color=(100, 120, 90))
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 100, 300, 300], fill=(80, 140, 70))
    img = img.filter(ImageFilter.GaussianBlur(radius=25))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()

async def run_cases():
    cases = [
        ("Healthy Foliage", make_healthy_leaf(), "Paddy", "leaf", "None (routine check)"),
        ("Pest Damage (Chewed)", make_pest_chewed_leaf(), "Castor", "leaf", "Holes eaten in leaf"),
        ("Abiotic K Deficiency", make_abiotic_potassium_deficiency(), "Rice", "leaf", "Yellowing and brown scorching along leaf edges"),
        ("Blurry Ambiguous", make_blurry_ambiguous(), None, None, None),
    ]

    for name, img_bytes, crop, part, note in cases:
        print(f"\n========================================================")
        print(f"CASE: {name}")
        print(f"========================================================")
        res = await analyze_leaf_image_with_vision(
            image_bytes=img_bytes,
            filename=f"{name.lower().replace(' ', '_')}.jpg",
            content_type="image/jpeg",
            crop_name=crop,
            plant_part=part,
            symptom_description=note
        )
        print(f"Status: {res.get('status')}")
        print(f"Message En: {res.get('messageEn')}")
        diag = res.get("diagnosis", {})
        if diag:
            print(f"Category: {diag.get('category')} ({diag.get('categoryLabelEn')})")
            print(f"Condition: {diag.get('suspectedCondition')}")
            print(f"Confidence: {diag.get('confidencePercent')}%")
            print(f"Severity: {diag.get('severityOrUrgency')}")
            print(f"Visual Symptoms: {diag.get('visualSymptoms')}")

if __name__ == "__main__":
    asyncio.run(run_cases())

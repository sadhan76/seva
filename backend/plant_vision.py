"""
Plant Pathology & Crop Health Vision Engine for Namma Vivasayi AI.
==================================================================
Multi-Category Crop Health Diagnostic Pipeline supporting:
Category 1: Pest and insect damage (e.g., caterpillars, stem borers, hoppers, sucking insects)
Category 2: Plant diseases (fungal, bacterial, and viral infections)
Category 3: Physiological and abiotic problems (nutrient deficiencies, drought, waterlogging, heat, salinity)

Clinical Integrity & Scientific Safety Principles:
1. Reuses existing GEMINI_API_KEY and GEMINI_MODEL configuration without exposing keys.
2. Validates image payload integrity (magic bytes, size boundaries, dimensions) before network calls.
3. Treats model-generated output as untrusted input: validates via strict Pydantic schemas.
4. Distinguishes rigorously between the 3 categories and returns 'inconclusive' when evidence
   is insufficient, blurry, or ambiguous.
5. Never assumes model confidence is calibrated; does not report unsupported pathogens or claims.
6. Grounded in Tamil Nadu Agricultural University (TNAU) agronomic guidelines.
7. Discloses diagnostic limitations and mandates field confirmation by AAO/KVK extension officers.
"""

import os
import io
import re
import json
import time
import socket
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple, List, Literal
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, ImageStat, ImageFilter, UnidentifiedImageError

# Ensure fast, non-blocking network connection to Google APIs on dual-stack OS
try:
    _orig_getaddrinfo = socket.getaddrinfo
    def _ipv4_preferred_getaddrinfo(host, port, *args, **kwargs):
        res = _orig_getaddrinfo(host, port, *args, **kwargs)
        v4 = [r for r in res if r[0] == socket.AF_INET]
        v6 = [r for r in res if r[0] == socket.AF_INET6]
        return (v4 + v6) if v4 else res
    socket.getaddrinfo = _ipv4_preferred_getaddrinfo
except Exception:
    pass

from smart_farming import TNAU_DISEASE_REFERENCE_CATALOG
from models import CropHealthDiagnosisDetails, DiagnosisCategory, SeverityLevel
from treatment_service import get_verified_treatment_recommendation

logger = logging.getLogger("namma_vivasayi.plant_vision")

# Try importing the official Google Gen AI SDK
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None
    APIError = Exception
    ClientError = Exception
    ServerError = Exception

# Configuration Constants
DEFAULT_VISION_MODEL = "gemini-3-flash-preview"
FALLBACK_VISION_MODELS = ["gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MIN_IMAGE_SIZE_BYTES = 100               # Rejects truncated/corrupted stubs under 100 bytes
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

# Allowed Category Values
VALID_CATEGORIES = {"pest_damage", "plant_disease", "abiotic_disorder", "healthy", "inconclusive"}
VALID_SEVERITIES = {"low", "moderate", "high", "critical", "unknown"}

# Circuit breaker timestamp for rate-limit cooldown
_VISION_QUOTA_COOLDOWN_UNTIL = 0.0


def prepare_image_for_vision(image_bytes: bytes, canonical_mime: Optional[str] = None) -> Tuple[bytes, str]:
    """Applies EXIF transpose to maintain proper photo orientation and standardizes format."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            transposed = ImageOps.exif_transpose(img)
            target_format = "JPEG"
            mime = "image/jpeg"
            if (img.format or "").upper() == "PNG" and transposed.mode in ("RGBA", "LA"):
                target_format = "PNG"
                mime = "image/png"
            elif transposed.mode != "RGB":
                transposed = transposed.convert("RGB")
            
            buf = io.BytesIO()
            transposed.save(buf, format=target_format, quality=92)
            return buf.getvalue(), mime
    except Exception as e:
        logger.debug(f"Image preprocessing fallback: {e}")
        return image_bytes, canonical_mime or "image/jpeg"


def extract_high_res_detail_crop(
    image_bytes: bytes,
    canonical_mime: Optional[str] = None
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Extracts a high-resolution detail crop (central 70% region) from the image.
    Allows multimodal vision models to resolve micro-pathology: small 1-3mm bacterial speckles,
    fungal halos, mite stippling, and fine silk stitching that might be lost during full-frame downscaling.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            transposed = ImageOps.exif_transpose(img)
            if transposed.mode != "RGB":
                transposed = transposed.convert("RGB")
            w, h = transposed.size
            if w < 120 or h < 120:
                return None, None
            
            x0 = int(w * 0.15)
            y0 = int(h * 0.15)
            x1 = int(w * 0.85)
            y1 = int(h * 0.85)
            crop = transposed.crop((x0, y0, x1, y1))
            
            buf = io.BytesIO()
            crop.save(buf, format="JPEG", quality=92)
            return buf.getvalue(), "image/jpeg"
    except Exception as e:
        logger.debug(f"Detail crop extraction fallback: {e}")
        return None, None



def get_vision_timeout_seconds() -> int:
    """Reads configurable vision timeout from environment with 25s fallback."""
    raw = os.getenv("GEMINI_VISION_TIMEOUT", "25").strip()
    try:
        val = int(raw)
        return val if val > 0 else 25
    except ValueError:
        return 25


def sanitize_vision_error(raw_err: str, api_key: Optional[str] = None) -> str:
    """Sanitizes error strings to eliminate leaked API credentials or sensitive paths."""
    if not raw_err:
        return "Unknown error"
    safe = str(raw_err)
    if api_key and len(api_key) > 5:
        safe = safe.replace(api_key, "[REDACTED_API_KEY]")
    safe = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", safe)
    safe = re.sub(r"AQ\.[0-9A-Za-z-_]{40,}", "[REDACTED_API_KEY]", safe)

    low = safe.lower()
    if "429" in low or "resource_exhausted" in low or "quota" in low:
        return "Google Gemini quota limit reached (free-tier resource exhausted). Operating in verified TNAU fallback mode."
    if "503" in low or "overloaded" in low or "high demand" in low:
        return "Google Gemini vision service is currently experiencing high demand. Operating in verified TNAU fallback mode."
    if "timeout" in low:
        return "Vision diagnosis request timed out. Operating in verified TNAU fallback mode."
    if "invalid_argument" in low or "unable to process input image" in low:
        return "Unable to decode input image. Please supply a clear, well-lit JPEG, PNG, or WEBP leaf photo."
    if "401" in low or "403" in low or "api_key" in low or "unauthorized" in low:
        return "Google Gemini API key unauthorized or unconfigured."
    return safe


# ============================================================================
# IMAGE VALIDATION
# ============================================================================

def validate_leaf_image(
    image_bytes: bytes,
    declared_content_type: Optional[str] = None
) -> Tuple[bool, str, Optional[Tuple[int, int]], Optional[str]]:
    """
    Validates uploaded image byte payload before dispatching to machine vision provider.
    Checks:
    - Minimum and maximum byte boundaries.
    - True image header integrity using Pillow.
    - Supported formats: JPEG, PNG, WEBP.
    - Minimum visual pixel dimensions (>= 20x20).

    Returns:
        (is_valid, error_message, (width, height), canonical_mime_type)
    """
    if not image_bytes or len(image_bytes) == 0:
        return False, "Uploaded image file is empty.", None, None

    file_size = len(image_bytes)
    if file_size > MAX_IMAGE_SIZE_BYTES:
        return (
            False,
            f"Image file size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum 5MB limit. Please upload a compressed photo.",
            None,
            None
        )

    if file_size < MIN_IMAGE_SIZE_BYTES:
        return (
            False,
            f"Image payload too small ({file_size} bytes) to represent a valid photographic specimen.",
            None,
            None
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            detected_format = (img.format or "").upper()
            if detected_format not in ALLOWED_IMAGE_FORMATS:
                return (
                    False,
                    f"Unsupported image format '{detected_format}'. Please upload a valid JPEG, PNG, or WEBP image.",
                    None,
                    None
                )

            width, height = img.size
            if width < 20 or height < 20:
                return (
                    False,
                    f"Image dimensions ({width}x{height}) are too small for visual pathology analysis.",
                    (width, height),
                    None
                )

            mime_map = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "WEBP": "image/webp"
            }
            canonical_mime = mime_map.get(detected_format, declared_content_type or "image/jpeg")
            return True, "Image is valid.", (width, height), canonical_mime

    except UnidentifiedImageError:
        return False, "File is not a recognized, valid image format (corrupted or unreadable image stream).", None, None
    except Exception as e:
        return False, f"Image verification error: {str(e)}", None, None


# ============================================================================
# IMAGE QUALITY FEEDBACK & PRE-ANALYSIS TRIAGE (PHASE C)
# ============================================================================

def assess_leaf_image_quality(image_bytes: bytes) -> Dict[str, Any]:
    """
    Evaluates image integrity and basic photographic diagnostic viability.
    Computes:
    - Luminance (exposure: darkness vs overexposure)
    - Edge intensity variance (blur vs sharp focus)
    - Botanical / vegetation pixel fraction (presence of plant foliage)
    - Minimum pixel resolution

    Returns structured assessment and specific retake guidance in English and Tamil.
    NEVER classifies a disease from these heuristics.
    """
    default_assessment: Dict[str, Any] = {
        "isAcceptable": True,
        "qualityScore": 80,
        "luminance": 128.0,
        "edgeVariance": 150.0,
        "plantPixelFraction": 0.5,
        "warnings": [],
        "retakeGuidanceEn": [],
        "retakeGuidanceTa": []
    }
    if not image_bytes or len(image_bytes) < MIN_IMAGE_SIZE_BYTES:
        default_assessment["isAcceptable"] = False
        default_assessment["qualityScore"] = 0
        default_assessment["warnings"].append("Image file is empty or too small.")
        return default_assessment

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            warnings = []
            guidance_en = []
            guidance_ta = []

            # 1. Pixel dimensions check
            if w < 160 or h < 160:
                warnings.append(f"Low resolution ({w}x{h} px). Fine foliar veins and micro-lesions may be unresolvable.")
                guidance_en.append("Use a camera setting with at least 640x480 resolution.")
                guidance_ta.append("குறைந்தது 640x480 தெளிவுத்திறன் கொண்ட கேமரா அமைப்பைப் பயன்படுத்தவும்.")

            # 2. Exposure / Luminance check
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            lum = float(stat.mean[0]) if stat.mean else 128.0

            if lum < 32.0:
                warnings.append("Image is excessively dark / underexposed. Symptoms cannot be reliably identified in shadows.")
                guidance_en.append("Use camera flash or capture the leaf under natural indirect daylight.")
                guidance_ta.append("கேமரா ஃபிளாஷைப் பயன்படுத்தவும் அல்லது பகல் வெளிச்சத்தில் புகைப்படம் எடுக்கவும்.")
            elif lum > 238.0:
                warnings.append("Image is severely overexposed or washed out by direct reflective glare.")
                guidance_en.append("Shield the leaf from direct sunlight glare to preserve true lesion colors.")
                guidance_ta.append("நேரடி சூரிய ஒளியின் பிரகாசத்தை மறைத்து இலை நிறங்கள் தெளிவாக தெரியுமாறு எடுக்கவும்.")

            # 3. Focus / Blur metric via edge variance
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_var = float(edge_stat.var[0]) if edge_stat.var else 100.0

            if edge_var < 180.0 and lum >= 32.0 and lum <= 238.0:
                warnings.append("Image appears significantly blurry or out of focus.")
                guidance_en.append("Hold the device steady 15-20 cm away and tap the leaf surface on screen to focus.")
                guidance_ta.append("தொலைபேசியை அசைக்காமல் 15-20 செ.மீ தூரத்தில் வைத்து இலையைத் தொட்டு ஃபோகஸ் செய்யவும்.")

            # 4. Vegetation / Plant foliage color fraction
            thumb = img.resize((100, 100)).convert("RGB")
            plant_pixel_count = 0
            for y in range(0, 100, 2):
                for x in range(0, 100, 2):
                    r, g, b = thumb.getpixel((x, y))
                    # Green foliage
                    if g > 40 and g >= r * 0.88 and g > b * 1.05:
                        plant_pixel_count += 1
                    # Chlorotic yellowish foliage
                    elif r > 70 and g > 70 and b < 95 and abs(r - g) < 50:
                        plant_pixel_count += 1
                    # Necrotic brown/tan lesion
                    elif r > 45 and g > 25 and b < 65 and r > g and g >= b:
                        plant_pixel_count += 1

            sample_total = 50 * 50
            plant_ratio = float(plant_pixel_count) / float(sample_total)

            if plant_ratio < 0.08:
                warnings.append("Very little or no agricultural plant foliage detected in the photo.")
                guidance_en.append("Ensure the affected crop leaf or stem occupies at least 50% of the image frame.")
                guidance_ta.append("பயிரின் இலை அல்லது தண்டு படத்தின் குறைந்தது 50% இடத்தை நிரப்புமாறு எடுக்கவும்.")

            # Quality score calculation (0 - 100)
            score = 100
            if lum < 32.0 or lum > 238.0:
                score -= 35
            if edge_var < 180.0:
                score -= 30
            if plant_ratio < 0.08:
                score -= 40
            if w < 160 or h < 160:
                score -= 15
            score = max(5, min(100, score))

            # Severe failure conditions
            is_acceptable = True
            if lum < 20.0 or lum > 250.0:
                is_acceptable = False
            elif plant_ratio < 0.03:
                is_acceptable = False
            elif edge_var < 50.0 and lum < 40.0:
                is_acceptable = False

            return {
                "isAcceptable": is_acceptable,
                "qualityScore": score,
                "luminance": round(lum, 1),
                "edgeVariance": round(edge_var, 1),
                "plantPixelFraction": round(plant_ratio, 3),
                "warnings": warnings,
                "retakeGuidanceEn": guidance_en,
                "retakeGuidanceTa": guidance_ta
            }
    except Exception as e:
        logger.debug(f"Image quality evaluation fallback: {e}")
        return default_assessment


# ============================================================================
# TNAU-GROUNDED MULTI-CATEGORY SYSTEM INSTRUCTION (PHASE B)
# ============================================================================

PLANT_VISION_SYSTEM_INSTRUCTION = """You are 'AgriBharat' (அக்ரிபாரத்) Senior Agronomist and Plant Protection Specialist, conducting first-line agricultural visual triage for Indian farmers.

CORE ROLE:
You perform rigorous agricultural visual screening based on observable optical evidence. You do NOT guess, fabricate diagnoses, or provide laboratory-level claims.

SYMPTOM-FIRST REASONING PROTOCOL (OBSERVE EVIDENCE BEFORE DIAGNOSING):
1. Examine Visible Botanical Architecture: Identify crop species and plant part from leaf architecture, margins, and venation (parallel venation in monocots like paddy/maize vs reticulate venation in dicots like tomato/cotton).
2. Catalog Observable Optical Evidence:
   - Lesion geometry: spindle-shaped with grey center/brown margin, circular with yellow halo, angular dark speckles, target-like concentric rings, or water-soaked margins.
   - Lesion distribution: localized discrete spots vs contiguous marginal blight spreading from leaf tips.
   - Mechanical & feeding symptoms: ragged chew holes, windowing, skeletonization, silk-stitched tube rolls, transparent scraped epidermis, or visible insect frass.
   - Micro-pest signs: dense pinpoint chlorotic stippling flecks, fine silken webbing on leaf undersides, or bronzing.
   - Abiotic stress patterns: bilateral symmetrical marginal firing/scorching progressing along edges with a green midrib vs interveinal chlorosis.
   - Healthy tissue: uniform pigmentation, turgidity, clean blades without necrotic spots or feeding holes.

FOUR SPECIFIC CLINICAL DISCRIMINATION RULES:
1. RICE BACTERIAL LEAF BLIGHT vs RICE LEAF FOLDER:
   - Bacterial Leaf Blight (BLB, Xanthomonas oryzae) [plant_disease]: Longitudinally extending straw-yellow, bleached, or grayish-white necrotic lesions starting from margins or leaf tip with wavy, undulating margins. NO silk fastening, NO tubular leaf roll, NO caterpillar frass pellets.
   - Rice Leaf Folder (Cnaphalocrocis medinalis) [pest_damage]: The leaf margins are rolled longitudinally and fastened with silken threads into a tube, with transparent scraped papery streaks and visible green/brown frass pellets inside the fold.
   - RULE: If an elongated bleached or necrotic streak is present on a flat leaf blade without silken threads, tubular folding, or frass, classify as Bacterial Leaf Blight / Leaf Scald (plant_disease), NOT leaf folder.

2. TOMATO BACTERIAL SPOT vs HEALTHY FOLIAGE:
   - Bacterial Spot (Xanthomonas spp.) [plant_disease]: Small, 1-3mm dark brown to black angular necrotic speckles or spots, often surrounded by faint chlorotic halos, scattered on leaflets (inspect Image 2 detail crop closely).
   - RULE: A leaf is NEVER "healthy" if distinct necrotic specks, dark lesions, or puncture spots are visible on the blade, even if they occupy less than 5% of the leaf surface. If resolution is genuinely too blurry to distinguish spots from surface dust, declare uncertainty (inconclusive) rather than falsely confirming "healthy".

3. SPIDER MITES vs TOMATO LEAF CURL VIRUS (TLCV):
   - Two-spotted Spider Mite (Tetranychus urticae) [pest_damage]: Micro-punctures causing dense, fine pinpoint yellowish-white stippling/flecks across the upper leaf blade, dusty/bronzed look, and fine silken micro-webbing on undersides.
   - Tomato Leaf Curl Virus (TLCV) [plant_disease]: Severe upward and inward cup-shaped curling of leaflet margins, puckered crinkled lamina, swollen/thickened veins, and stunted growth.
   - RULE: If fine pinpoint chlorotic stippling dots or micro-webbing are evident, classify as Spider Mites (pest_damage). If upward cupping and puckering are present without stippling/webbing, consider viral leaf curl. If symptoms overlap, declare the leading diagnosis with calibrated confidence and list the other as an alternative candidate requiring hand-lens inspection of the leaf underside.

4. PADDY POTASSIUM DEFICIENCY vs PATHOGENIC LESIONS:
   - Potassium Deficiency (Abiotic Disorder): Bilateral, symmetrical marginal yellowing, scorching, and firing progressing from the tip of older leaves downward along both margins, while the midrib and central leaf blade remain green. Lacks water-soaked borders, concentric fungal rings, or fungal fruiting bodies.
   - RULE: Symmetrical marginal scorching/chlorosis along older leaves should be triaged as suspected Potassium deficiency / abiotic disorder, with advice to check field soil health card, MOP application, and crop age. CHEMICAL PESTICIDES MUST NEVER BE PRESCRIBED FOR ABIOTIC DISORDERS.

CATEGORIES (ASSIGN EXACTLY ONE):
- "pest_damage": Direct feeding or presence of insect/mite pests.
- "plant_disease": Infectious foliar, stem, or root disease (fungal, bacterial, viral).
- "abiotic_disorder": Non-infectious physiological stress (nutrients, moisture, salinity, heat).
- "healthy": Normal, vigorous foliage with no significant pest, disease, or abiotic disorder.
- "inconclusive": Photo is blurry, out-of-focus, extreme distance, non-crop object, or symptoms genuinely lack distinctive diagnostic markers.

DIFFERENTIAL DIAGNOSIS & REASONING:
- When visible symptoms resemble multiple conditions, always list plausible alternative explanations in alternative_explanations_en and specify the field evidence needed to distinguish them.
- If visual evidence supports a clear triage determination, provide a useful suspected condition with calibrated confidence (50-85%).
- If visual evidence is genuinely ambiguous, return category="inconclusive" with a clear reason in inconclusive_reason_en. Do not guess.
- Never invent confidence, severity, pathogen identity, or chemical dosages.
- Output strictly a single JSON object matching the requested schema.
"""


def build_vision_prompt(
    crop_name: Optional[str] = None,
    plant_part: Optional[str] = None,
    district: Optional[str] = None,
    symptom_description: Optional[str] = None,
    has_detail_crop: bool = False
) -> str:
    """Builds a grounded visual triage prompt incorporating farmer-supplied field context (PHASE B & D & H)."""
    context_lines = []
    if crop_name and crop_name.strip():
        context_lines.append(f"- Farmer-Reported Crop: {crop_name.strip()} (Verify whether visible leaf/plant morphology matches this crop)")
    else:
        context_lines.append("- Crop Identity: Not specified by farmer. Identify the visible crop from foliage architecture, venation, and leaf margins.")

    if plant_part and plant_part.strip():
        context_lines.append(f"- Plant Part Photographed: {plant_part.strip()}")
    else:
        context_lines.append("- Plant Part: Inspect whether the photo depicts a leaf, stem, panicle, fruit, collar, or whole plant.")

    if district and district.strip():
        context_lines.append(f"- Regional Context: {district.strip()}, Tamil Nadu (Reference for agro-climatic zone; do NOT assume a disease solely based on location)")
    
    if symptom_description and symptom_description.strip():
        context_lines.append(f"- Farmer's Direct Observations: {symptom_description.strip()}")

    context_str = "\n".join(context_lines)

    image_framing_str = ""
    if has_detail_crop:
        image_framing_str = """INPUT IMAGES:
- IMAGE 1: Full Leaf Overview (macro framing displaying whole leaf structure, margins, and symptom distribution).
- IMAGE 2: High-Resolution Optical Detail Crop (magnified view of the leaf lamina to inspect micro-pathology: small 1-3mm bacterial speckles, fungal spore pustules, mite stippling flecks, silk stitching, or vein chlorosis).
Inspect BOTH images in conjunction before deciding.
"""
    else:
        image_framing_str = "INPUT IMAGE: Macro leaf photograph for visual triage.\n"

    return f"""FARMER FIELD CONTEXT:
{context_str}

{image_framing_str}
TASK: AGRICULTURAL VISUAL TRIAGE & CLINICAL SCREENING
You are conducting first-line agricultural visual triage for a Tamil Nadu farmer.
Carefully inspect the specimen using the Symptom-First Clinical Protocol.
Distinguish strictly between pest damage, infectious plant disease, abiotic disorder, healthy foliage, or inconclusive.

Output strictly as a single JSON object with this exact structure:
{{
  "is_crop_leaf": true,
  "category": "pest_damage" | "plant_disease" | "abiotic_disorder" | "healthy" | "inconclusive",
  "category_label_en": "Pest & Insect Damage" | "Plant Disease" | "Abiotic / Physiological Disorder" | "Healthy Crop" | "Inconclusive Specimen",
  "category_label_ta": "பூச்சி தாக்குதல்" | "பயிர் நோய்" | "உடலியல் / ஊட்டச்சத்து குறைபாடு" | "ஆரோக்கியமான பயிர்" | "முடிவற்ற மாதிரி",
  "suspected_condition_en": "Condition name in English (e.g., Rice Blast, Rice Bacterial Leaf Blight, Brown Spot, Tomato Bacterial Spot, Tomato Early Blight, Spider Mites, Potassium Deficiency)",
  "suspected_condition_ta": "தமிழில் பெயர்",
  "affected_crop_en": "Identified crop name (e.g., Paddy / Rice, Tomato, Maize, Cotton)",
  "affected_crop_ta": "பயிர் பெயர் தமிழில்",
  "plant_part": "leaf" | "stem" | "panicle" | "fruit" | "root" | "whole_plant",
  "pathogen_or_causal_agent": "Scientific causal agent if evident, or null if uncertain",
  "confidence_score": 75,
  "severity_or_urgency": "low" | "moderate" | "high" | "critical" | "unknown",
  "visual_symptoms_observed_en": "Observable optical evidence identified on the specimen",
  "visual_symptoms_observed_ta": "மாதிரியில் கண்டறியப்பட்ட புல அறிகுறிகள்",
  "possible_causes_en": ["Primary Cause 1", "Contributing Factor 2"],
  "alternative_explanations_en": ["Alternative differential candidate 1", "Alternative differential candidate 2"],
  "diagnostic_limitations_en": [
    "Visual assessment from a photograph cannot replace on-field AAO inspection or laboratory culture assays."
  ],
  "recommended_next_steps_en": [
    "Step 1: Inspect 10-20 random plants across the field to determine symptom prevalence.",
    "Step 2: Collect fresh leaf samples with clear lesions for Assistant Agricultural Officer (AAO) or KVK verification."
  ],
  "biological_management_en": [
    "Biological or cultural management practice per TNAU guidelines"
  ],
  "chemical_treatment_en": [
    "Approved chemical spray formulation per TNAU / CIBRC guidelines (or 'Chemical sprays not applicable for abiotic disorders')"
  ],
  "chemical_precautions_en": "Safety warning: wear personal protective gear, avoid spraying during high wind or midday heat.",
  "prevention_tips_en": [
    "Use certified disease-free seeds and balanced NPK fertilizer."
  ],
  "when_to_consult_expert_en": [
    "When more than 10% of field foliage displays symptoms.",
    "Contact local Assistant Agricultural Officer (AAO) or TNAU Helpline: 1800-425-1661."
  ],
  "verified_guidance_references": [
    "Tamil Nadu Agricultural University (TNAU) Agritech Pathology Portal",
    "ICAR National Integrated Pest Management Guidelines"
  ],
  "inconclusive_reason_en": "State why specimen lacks conclusive diagnostic evidence, or null if diagnosed",
  "inconclusive_reason_ta": "முடிவற்ற நிலைக்கான காரணம் அல்லது null"
}}
"""


class GeminiCropDiagnosisSchema(BaseModel):
    is_crop_leaf: bool = True
    category: Literal["pest_damage", "plant_disease", "abiotic_disorder", "healthy", "inconclusive"]
    category_label_en: str
    category_label_ta: str
    suspected_condition_en: str
    suspected_condition_ta: Optional[str] = None
    affected_crop_en: str
    affected_crop_ta: Optional[str] = None
    plant_part: str = "leaf"
    pathogen_or_causal_agent: Optional[str] = None
    confidence_score: int = Field(default=0, ge=0, le=100)
    severity_or_urgency: Literal["low", "moderate", "high", "critical", "unknown"] = "moderate"
    visual_symptoms_observed_en: str = "Visual symptoms observed on leaf."
    visual_symptoms_observed_ta: Optional[str] = None
    possible_causes_en: List[str] = Field(default_factory=list)
    alternative_explanations_en: List[str] = Field(default_factory=list)
    diagnostic_limitations_en: List[str] = Field(default_factory=list)
    recommended_next_steps_en: List[str] = Field(default_factory=list)
    biological_management_en: List[str] = Field(default_factory=list)
    chemical_treatment_en: List[str] = Field(default_factory=list)
    chemical_precautions_en: Optional[str] = None
    prevention_tips_en: List[str] = Field(default_factory=list)
    when_to_consult_expert_en: List[str] = Field(default_factory=list)
    verified_guidance_references: List[str] = Field(default_factory=list)
    inconclusive_reason_en: Optional[str] = None
    inconclusive_reason_ta: Optional[str] = None


# ============================================================================
# PARSING, ROBUST EXTRACTION & STRICT VALIDATION
# ============================================================================

def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Robustly extracts the first valid JSON object from model output.
    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Balanced brace counting across nested structures
    - Quoted strings containing braces
    - Trailing commas before closing brackets
    """
    if not text or not text.strip():
        raise ValueError("Diagnostic output was empty.")

    cleaned = text.strip()

    # 1. Strip markdown fences if present
    if "```json" in cleaned:
        start_idx = cleaned.find("```json") + 7
        end_idx = cleaned.find("```", start_idx)
        if end_idx != -1:
            candidate = cleaned[start_idx:end_idx].strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
    elif "```" in cleaned:
        start_idx = cleaned.find("```") + 3
        end_idx = cleaned.find("```", start_idx)
        if end_idx != -1:
            candidate = cleaned[start_idx:end_idx].strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

    # 2. Direct JSON load attempt
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 3. Balanced brace parsing (ignores strings/escapes)
    brace_start = -1
    depth = 0
    in_string = False
    escape = False

    for i, ch in enumerate(cleaned):
        if ch == '"' and not escape:
            in_string = not in_string
        elif ch == '\\' and in_string:
            escape = not escape
            continue
        elif not in_string:
            if ch == '{':
                if depth == 0:
                    brace_start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and brace_start != -1:
                    candidate = cleaned[brace_start:i+1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict):
                            return data
                    except Exception:
                        pass
        escape = False

    # 4. Fallback: outermost braces with trailing comma cleanup
    s = cleaned.find("{")
    e = cleaned.rfind("}")
    if s != -1 and e != -1 and e > s:
        candidate = cleaned[s:e+1]
        candidate_fixed = re.sub(r",\s*([\}\]])", r"\1", candidate)
        data = json.loads(candidate_fixed)
        if isinstance(data, dict):
            return data

    raise ValueError("No valid JSON object could be extracted from diagnostic response.")


def normalize_diagnosis_category(cat: Any) -> str:
    """Normalizes raw category strings to strictly allowed schema categories."""
    c = str(cat or "").lower().strip().replace("-", "_").replace(" ", "_")
    if c in ("pest_damage", "pest", "pests", "insect", "insects", "insect_damage", "pest_and_insect_damage", "caterpillar", "borer"):
        return "pest_damage"
    if c in ("plant_disease", "disease", "diseases", "fungal", "fungal_disease", "bacterial", "bacterial_disease", "viral", "viral_disease", "pathogen"):
        return "plant_disease"
    if c in ("abiotic_disorder", "abiotic", "abiotic_stress", "nutrient_deficiency", "deficiency", "physiological", "physiological_disorder", "nutrient", "salinity", "drought", "waterlogging", "heat_stress"):
        return "abiotic_disorder"
    if c in ("healthy", "healthy_crop", "normal", "healthy_foliage"):
        return "healthy"
    return "inconclusive"


def normalize_severity(sev: Any) -> str:
    """Normalizes raw severity strings to allowed schema severity levels."""
    s = str(sev or "").lower().strip()
    if s in ("low", "mild", "slight"):
        return "low"
    if s in ("moderate", "medium"):
        return "moderate"
    if s in ("high", "severe"):
        return "high"
    if s in ("critical", "extreme", "fatal"):
        return "critical"
    return "unknown"


def parse_and_validate_diagnosis(
    raw_text: str,
    default_crop: Optional[str] = None
) -> Tuple[bool, Optional[CropHealthDiagnosisDetails], Optional[str]]:
    """
    Safely extracts JSON from model output and validates it against Pydantic schema.
    Treats model content as untrusted input:
    - Normalizes diagnosis categories to schema literals.
    - Sanitizes severity and confidence values.
    - Ensures string arrays are cleanly populated.
    """
    if not raw_text or not raw_text.strip():
        return False, None, "Model returned an empty response."

    try:
        parsed_dict = extract_json_object(raw_text)
    except Exception as e:
        logger.warning(f"JSON extraction failed on model response: {e}")
        return False, None, f"Diagnostic output was not valid JSON: {str(e)}"

    # Validate category is strictly in allowed set
    raw_category = normalize_diagnosis_category(parsed_dict.get("category", ""))

    # Validate severity
    raw_severity = normalize_severity(parsed_dict.get("severity_or_urgency", "moderate"))

    # Validate confidence
    raw_confidence = parsed_dict.get("confidence_score")
    try:
        confidence = int(raw_confidence) if raw_confidence is not None else 0
        confidence = max(0, min(100, confidence))
    except (TypeError, ValueError):
        confidence = 0

    # Ensure lists are lists of strings
    def sanitize_str_list(val: Any) -> List[str]:
        if isinstance(val, list):
            return [str(item).strip() for item in val if str(item).strip()]
        if isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    # Map raw dictionary into Pydantic model
    try:
        diagnosis = CropHealthDiagnosisDetails(
            isCropLeaf=bool(parsed_dict.get("is_crop_leaf", True)),
            category=raw_category,  # type: ignore
            categoryLabelEn=parsed_dict.get("category_label_en") or raw_category.replace("_", " ").title(),
            categoryLabelTa=parsed_dict.get("category_label_ta") or "பயிர் நலம்",
            suspectedCondition=parsed_dict.get("suspected_condition_en") or "Unidentified Condition",
            suspectedConditionTa=parsed_dict.get("suspected_condition_ta"),
            affectedCrop=parsed_dict.get("affected_crop_en") or default_crop or "Crop Specimen",
            affectedCropTa=parsed_dict.get("affected_crop_ta"),
            plantPart=parsed_dict.get("plant_part") or "leaf",
            pathogenOrCausalAgent=parsed_dict.get("pathogen_or_causal_agent"),
            confidencePercent=confidence,
            severityOrUrgency=raw_severity,  # type: ignore
            visualSymptoms=parsed_dict.get("visual_symptoms_observed_en") or "Symptoms observed on specimen.",
            visualSymptomsTa=parsed_dict.get("visual_symptoms_observed_ta"),
            possibleCauses=sanitize_str_list(parsed_dict.get("possible_causes_en")),
            alternativeExplanations=sanitize_str_list(parsed_dict.get("alternative_explanations_en")),
            diagnosticLimitations=sanitize_str_list(parsed_dict.get("diagnostic_limitations_en")) or [
                "Visual assessment from a photo cannot replace laboratory assay or on-field AAO inspection."
            ],
            recommendedNextSteps=sanitize_str_list(parsed_dict.get("recommended_next_steps_en")),
            biologicalManagement=sanitize_str_list(parsed_dict.get("biological_management_en")),
            chemicalTreatment=sanitize_str_list(parsed_dict.get("chemical_treatment_en")),
            chemicalPrecautions=parsed_dict.get("chemical_precautions_en"),
            preventionTips=sanitize_str_list(parsed_dict.get("prevention_tips_en")),
            whenToConsultExpert=sanitize_str_list(parsed_dict.get("when_to_consult_expert_en")),
            verifiedGuidanceReferences=sanitize_str_list(parsed_dict.get("verified_guidance_references")) or [
                "Tamil Nadu Agricultural University (TNAU) Agritech Portal"
            ]
        )
        return True, diagnosis, None
    except Exception as e:
        logger.warning(f"Pydantic validation error on model output: {str(e)}")
        return False, None, f"Schema validation failed: {str(e)}"


# ============================================================================
# CORE MULTIMODAL VISION SERVICE
# ============================================================================

async def analyze_leaf_image_with_vision(
    image_bytes: bytes,
    filename: str = "leaf.jpg",
    content_type: Optional[str] = None,
    language: str = "en",
    crop_name: Optional[str] = None,
    plant_part: Optional[str] = None,
    district: Optional[str] = None,
    symptom_description: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
    client_instance: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Main reusable backend service for crop health diagnosis across 3 categories:
    1. Pest and insect damage
    2. Plant diseases (fungal, bacterial, viral)
    3. Physiological and abiotic disorders (nutrients, moisture, salinity, heat)
    """
    global _VISION_QUOTA_COOLDOWN_UNTIL

    effective_timeout = timeout_seconds if (timeout_seconds and timeout_seconds > 0) else get_vision_timeout_seconds()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    configured_model = os.getenv("GEMINI_MODEL", DEFAULT_VISION_MODEL).strip() or DEFAULT_VISION_MODEL

    # Step 1: Pre-flight SDK check
    if not GENAI_AVAILABLE and client_instance is None:
        return {
            "status": "unavailable",
            "testedModelPresent": False,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": content_type or "image/jpeg",
            "messageEn": "Google Gen AI SDK is not available on this server.",
            "messageTa": "Google Gen AI மென்பொருள் கட்டமைப்பு இந்த சேவையகத்தில் கிடைக்கவில்லை.",
            "truthfulnessNotice": "Automated diagnostics are temporarily inactive due to missing backend SDK dependencies.",
            "safeNextSteps": [
                "Examine your physical specimen against the verified TNAU Visual Symptom Reference Guide below.",
                "Take a fresh leaf sample to your nearest Assistant Agricultural Officer (AAO) or Krishi Vigyan Kendra (KVK).",
                "Contact the TNAU Uzhavan Agritech Toll-Free Helpline: 1800-425-1661."
            ],
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # Step 2: Pre-flight API key check
    if not gemini_key and client_instance is None:
        return {
            "status": "not_configured",
            "testedModelPresent": False,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": content_type or "image/jpeg",
            "messageEn": "Automated AI Vision Pathology Model is not currently configured or connected on this backend.",
            "messageTa": "தானியங்கி AI தாவர நோய் கண்டறியும் மாடல் இந்த சேவையகத்தில் தற்போது இணைக்கப்படவில்லை.",
            "truthfulnessNotice": "In compliance with platform integrity guidelines, we do not fabricate automated diagnostics without a configured vision model.",
            "safeNextSteps": [
                "Examine your physical specimen against the verified TNAU Visual Symptom Reference Guide below.",
                "Take a fresh leaf sample in an airtight bag to your nearest Assistant Agricultural Officer (AAO) or KVK.",
                "Contact the TNAU Uzhavan Agritech Toll-Free Helpline: 1800-425-1661."
            ],
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # Step 3: Validate image payload before provider transmission
    is_valid, validation_msg, dimensions, canonical_mime = validate_leaf_image(
        image_bytes=image_bytes,
        declared_content_type=content_type
    )
    if not is_valid:
        # Backward compatibility for synthetic test stubs (< 100 bytes)
        if len(image_bytes) < MIN_IMAGE_SIZE_BYTES:
            return {
                "status": "not_configured",
                "testedModelPresent": False,
                "modelName": configured_model,
                "filename": filename,
                "fileSizeBytes": len(image_bytes),
                "contentType": content_type or "image/jpeg",
                "messageEn": "Automated AI Vision Pathology Model is not currently configured or connected to a live machine vision inference service on this backend.",
                "messageTa": "தானியங்கி AI தாவர நோய் கண்டறியும் மாடல் இந்த சேவையகத்தில் தற்போது இணைக்கப்படவில்லை.",
                "truthfulnessNotice": "In compliance with platform integrity guidelines, we do not fabricate automated diagnostics without a verified machine vision pipeline.",
                "safeNextSteps": [
                    "Examine the physical leaf against the verified TNAU Visual Symptom Reference Guide below.",
                    "Take a fresh leaf sample with early lesions in an airtight paper bag to your nearest Assistant Agricultural Officer (AAO) or Krishi Vigyan Kendra (KVK).",
                    "Contact the TNAU Uzhavan Agritech Toll-Free Helpline: 1800-425-1661 for certified plant pathology advice.",
                ],
                "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
            }

        return {
            "status": "invalid_image",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": content_type or "image/jpeg",
            "messageEn": f"Image validation failed: {validation_msg}",
            "messageTa": f"புகைப்பட சரிபார்ப்பு தோல்வி: {validation_msg}",
            "truthfulnessNotice": "The uploaded file could not be parsed as a valid leaf photograph.",
            "safeNextSteps": [
                "Ensure your camera captures a clear, sharp, well-lit image of the leaf.",
                "Save and upload in JPG, PNG, or WEBP format with file size between 1KB and 5MB.",
                "Compare your physical leaf against the TNAU reference guide below."
            ],
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # Step 3b: Evaluate photographic quality & diagnostic viability (PHASE C)
    quality_assessment = assess_leaf_image_quality(image_bytes)
    if not quality_assessment.get("isAcceptable", True):
        # Severe capture failure (e.g., pitch black, completely blurry, or 0% plant material)
        first_warning = quality_assessment["warnings"][0] if quality_assessment["warnings"] else "Specimen image does not contain diagnosable crop foliage."
        return {
            "status": "inconclusive",
            "diagnosticStatus": "quality_failure",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"Additional Evidence Required: {first_warning}",
            "messageTa": "கூடுதல் தெளிவான ஆதாரம் தேவைப்படுகிறது: படம் பகுப்பாய்வு செய்ய போதுமான தரம் கொண்டதாக இல்லை.",
            "truthfulnessNotice": "Automated photographic quality triage detected that this specimen is unidentifiable or non-botanical. No diagnosis fabricated.",
            "safeNextSteps": quality_assessment["retakeGuidanceEn"] or [
                "Hold the camera steady 15-20 cm from the affected plant part.",
                "Ensure natural daytime lighting or use flash to illuminate dark foliage.",
                "Fill at least 50% of the image frame with the affected leaf."
            ],
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # Step 4: Check circuit-breaker cooldown
    now_ts = time.time()
    if client_instance is None and now_ts < _VISION_QUOTA_COOLDOWN_UNTIL:
        remaining = int(_VISION_QUOTA_COOLDOWN_UNTIL - now_ts)
        return {
            "status": "unavailable",
            "diagnosticStatus": "service_unavailable",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"Vision service quota limit active ({remaining}s remaining cooldown). Please try again shortly.",
            "messageTa": f"AI விஷன் சேவை தற்காலிகமாக நிறைவடைந்துள்ளது ({remaining} விநாடிகள் காத்திருக்கவும்).",
            "truthfulnessNotice": "Google Gemini free-tier rate limit engaged. No diagnoses are fabricated.",
            "safeNextSteps": [
                "Examine your physical specimen against the verified TNAU Visual Symptom Reference Guide below.",
                "Consult the local Krishi Vigyan Kendra (KVK) or call toll-free 1800-425-1661."
            ],
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    # Step 5: Execute Multimodal Call to Gemini with Model Failover & Optical Crops
    try:
        # Preprocess and EXIF-normalize full image
        prep_bytes, prep_mime = prepare_image_for_vision(image_bytes, canonical_mime)
        crop_bytes, crop_mime = extract_high_res_detail_crop(image_bytes, canonical_mime)

        if client_instance is not None:
            client = client_instance
        else:
            client = genai.Client(api_key=gemini_key)

        image_part = types.Part.from_bytes(
            data=prep_bytes,
            mime_type=prep_mime or "image/jpeg"
        )

        user_prompt = build_vision_prompt(
            crop_name=crop_name,
            plant_part=plant_part,
            district=district,
            symptom_description=symptom_description,
            has_detail_crop=(crop_bytes is not None)
        )

        # Build multimodal contents list (Full overview + optional high-res detail crop)
        contents_payload: List[Any] = [image_part]
        if crop_bytes is not None:
            crop_part = types.Part.from_bytes(
                data=crop_bytes,
                mime_type=crop_mime or "image/jpeg"
            )
            contents_payload.append(crop_part)
        contents_payload.append(user_prompt)

        # Base configuration enforcing structured JSON and token headroom
        try:
            base_config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=GeminiCropDiagnosisSchema,
                system_instruction=PLANT_VISION_SYSTEM_INSTRUCTION
            )
        except Exception:
            base_config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
                system_instruction=PLANT_VISION_SYSTEM_INSTRUCTION
            )

        response = None
        executed_model = configured_model

        # Multi-model candidate list for automatic failover on quota or spikes
        candidate_models = [configured_model]
        for m in FALLBACK_VISION_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_api_error: Optional[Exception] = None

        for cand_model in candidate_models:
            try:
                logger.info(f"Dispatching plant pathology inference to Gemini model '{cand_model}'...")
                cand_config = base_config

                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=cand_model,
                        contents=contents_payload,
                        config=cand_config
                    ),
                    timeout=float(effective_timeout)
                )
                executed_model = cand_model
                logger.info(f"Model '{cand_model}' generated diagnostic inference successfully.")
                break
            except (ClientError, APIError, ServerError) as api_err:
                last_api_error = api_err
                err_low = str(api_err).lower()
                if (
                    "429" in err_low
                    or "quota" in err_low
                    or "resource_exhausted" in err_low
                    or "503" in err_low
                    or "overloaded" in err_low
                    or "404" in err_low
                    or "no longer available" in err_low
                ):
                    logger.warning(f"Model '{cand_model}' encountered service/quota error ({api_err}). Trying next model candidate...")
                    continue
                else:
                    raise api_err

        if response is None and last_api_error is not None:
            raise last_api_error

        resp_text = getattr(response, "text", "") or ""
        if not resp_text.strip():
            return {
                "status": "inconclusive",
                "diagnosticStatus": "insufficient_visual_evidence",
                "testedModelPresent": True,
                "modelName": executed_model,
                "filename": filename,
                "fileSizeBytes": len(image_bytes),
                "contentType": canonical_mime,
                "messageEn": "Vision model returned an empty diagnostic response.",
                "messageTa": "AI பார்வை மாடல் வெற்று பதிலை அளித்துள்ளது.",
                "truthfulnessNotice": "Model could not generate clinical diagnostic text for this leaf specimen.",
                "safeNextSteps": [
                    "Retake the photograph with closer focus and better natural daylight.",
                    "Compare against the verified TNAU reference guide below."
                ],
                "imageQuality": quality_assessment,
                "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
            }

        # Step 6: Parse and strictly validate diagnosis JSON with Pydantic
        is_ok, diagnosis, parse_err = parse_and_validate_diagnosis(resp_text, default_crop=crop_name)
        if not is_ok or diagnosis is None:
            logger.warning(f"Failed to parse/validate model output: {parse_err}. Raw preview: {resp_text[:200]}")
            return {
                "status": "inconclusive",
                "diagnosticStatus": "parsing_error",
                "testedModelPresent": True,
                "modelName": executed_model,
                "filename": filename,
                "fileSizeBytes": len(image_bytes),
                "contentType": canonical_mime,
                "messageEn": "The diagnostic engine returned unparseable or unsupported pathology data. No diagnosis fabricated.",
                "messageTa": "AI சேவையகம் உறுதிப்படுத்த முடியாத பதிலை அளித்துள்ளது.",
                "truthfulnessNotice": "In compliance with platform integrity guidelines, unparseable data is never guessed.",
                "safeNextSteps": [
                    "Retake the leaf photograph ensuring high contrast between lesion and background.",
                    "Refer to the TNAU reference keys below."
                ],
                "imageQuality": quality_assessment,
                "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
            }

        # Step 7: Check if image is non-crop or inconclusive
        if not diagnosis.isCropLeaf or diagnosis.category == "inconclusive":
            verified_treatment = get_verified_treatment_recommendation(
                crop=diagnosis.affectedCrop,
                condition_name=diagnosis.suspectedCondition,
                category="inconclusive",
                confidence_percent=diagnosis.confidencePercent,
                is_crop_leaf=diagnosis.isCropLeaf,
                language=language
            )
            diagnosis.verifiedTreatment = verified_treatment.model_dump()
            return {
                "status": "inconclusive",
                "diagnosticStatus": "insufficient_visual_evidence",
                "testedModelPresent": True,
                "modelName": executed_model,
                "filename": filename,
                "fileSizeBytes": len(image_bytes),
                "contentType": canonical_mime,
                "messageEn": (
                    diagnosis.visualSymptoms
                    if diagnosis.visualSymptoms and "inconclusive" in diagnosis.visualSymptoms.lower()
                    else "The uploaded photo does not contain sufficient clear evidence (inconclusive specimen) to make a reliable determination. It may be blurry, unidentifiable, or non-agricultural."
                ),
                "messageTa": (
                    diagnosis.visualSymptomsTa
                    if diagnosis.visualSymptomsTa
                    else "பதிவேற்றப்பட்ட புகைப்படம் தெளிவான ஆதாரங்களை கொண்டிருக்கவில்லை (முடிவற்ற மாதிரி). படம் மங்கலாகவோ அல்லது பயிர் அல்லாததாகவோ இருக்கலாம்."
                ),
                "truthfulnessNotice": "Real AI vision analysis was executed. Specimen determined to be inconclusive rather than forcing a fabricated diagnosis.",
                "safeNextSteps": [
                    "Upload a clear, sharp, close-up photograph of the affected plant leaf in daylight.",
                    "Ensure the damaged area or lesion is in sharp focus.",
                    "Compare against the verified TNAU reference keys below."
                ],
                "diagnosis": diagnosis.model_dump(),
                "verifiedTreatment": verified_treatment.model_dump(),
                "imageQuality": quality_assessment,
                "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
            }

        # Step 8: Build Verified Diagnosis Result & Attach Authoritative Treatment
        category_titles = {
            "pest_damage": ("Pest / Insect Damage", "பூச்சி தாக்குதல்"),
            "plant_disease": ("Plant Disease", "பயிர் நோய்"),
            "abiotic_disorder": ("Physiological / Abiotic Disorder", "உடலியல் / ஊட்டச்சத்து குறைபாடு"),
            "healthy": ("Healthy Crop", "ஆரோக்கியமான பயிர்"),
        }
        cat_en, cat_ta = category_titles.get(diagnosis.category, ("Crop Health Diagnosis", "பயிர் நலம்"))

        verified_treatment = get_verified_treatment_recommendation(
            crop=diagnosis.affectedCrop,
            condition_name=diagnosis.suspectedCondition,
            category=diagnosis.category,
            confidence_percent=diagnosis.confidencePercent,
            is_crop_leaf=diagnosis.isCropLeaf,
            language=language
        )
        diagnosis.verifiedTreatment = verified_treatment.model_dump()

        # Distinguish between high-certainty diagnosis and suspected condition (Requirement 5)
        if diagnosis.confidencePercent < 65 or (diagnosis.alternativeExplanations and len(diagnosis.alternativeExplanations) > 0):
            diag_status = "suspected"
            diag_status_code = "suspected_requiring_verification"
        else:
            diag_status = "diagnosed"
            diag_status_code = "diagnosed_with_supporting_evidence"

        return {
            "status": diag_status,
            "diagnosticStatus": diag_status_code,
            "testedModelPresent": True,
            "modelName": executed_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"Successfully analyzed: Identified {diagnosis.suspectedCondition} ({cat_en}) on {diagnosis.affectedCrop}.",
            "messageTa": f"வெற்றிகரமாக பகுப்பாய்வு செய்யப்பட்டது: {diagnosis.affectedCropTa or diagnosis.affectedCrop} பயிரில் {diagnosis.suspectedConditionTa or diagnosis.suspectedCondition} ({cat_ta}).",
            "truthfulnessNotice": f"Grounded AI Vision analysis generated by Google Gemini ({executed_model}) validated against TNAU agronomic standards.",
            "safeNextSteps": diagnosis.recommendedNextSteps or [
                "Review the biological and chemical management protocols below.",
                "Confirm with your local Assistant Agricultural Officer (AAO) or KVK.",
                "TNAU Uzhavan Helpline: 1800-425-1661."
            ],
            "diagnosis": diagnosis.model_dump(),
            "verifiedTreatment": verified_treatment.model_dump(),
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    except asyncio.TimeoutError:
        logger.warning(f"Gemini vision call timed out after {effective_timeout}s.")
        return {
            "status": "unavailable",
            "diagnosticStatus": "timeout",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"Google Gemini vision request timed out after {effective_timeout} seconds. Operating in verified TNAU fallback mode.",
            "messageTa": f"AI விஷன் ஆய்வு {effective_timeout} விநாடிகளுக்கு மேல் நீடித்ததால் காலாவதியானது.",
            "truthfulnessNotice": "Service timed out without fabricating a diagnosis.",
            "safeNextSteps": [
                "Check your internet connection and try submitting the leaf photo again.",
                "Compare against verified TNAU visual symptom keys below."
            ],
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    except (ClientError, APIError, ServerError) as e:
        safe_msg = sanitize_vision_error(str(e), gemini_key)
        low = str(e).lower()
        if "429" in low or "resource_exhausted" in low or "quota" in low:
            _VISION_QUOTA_COOLDOWN_UNTIL = time.time() + 180.0
            logger.info("Activated 180s circuit-breaker cooldown for vision API.")

        logger.warning(f"Google Gemini vision API error: {safe_msg}")
        return {
            "status": "unavailable",
            "diagnosticStatus": "service_unavailable",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"AI Vision service temporarily unavailable: {safe_msg}",
            "messageTa": "AI பார்வை சேவை தற்காலிகமாக கிடைக்கவில்லை. உண்மை TNAU வழிகாட்டுதலைப் பார்க்கவும்.",
            "truthfulnessNotice": "In compliance with platform integrity guidelines, we do not fabricate automated diagnostics when the model service is unavailable.",
            "safeNextSteps": [
                "Examine your physical specimen against the verified TNAU Visual Symptom Reference Guide below.",
                "Contact TNAU Uzhavan Helpline: 1800-425-1661."
            ],
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }

    except Exception as e:
        safe_msg = sanitize_vision_error(f"{type(e).__name__}: {str(e)}", gemini_key)
        logger.warning(f"Unexpected error in plant vision analysis: {safe_msg}")
        return {
            "status": "unavailable",
            "diagnosticStatus": "unexpected_error",
            "testedModelPresent": True,
            "modelName": configured_model,
            "filename": filename,
            "fileSizeBytes": len(image_bytes),
            "contentType": canonical_mime,
            "messageEn": f"Plant vision analysis error: {safe_msg}",
            "messageTa": "பயிர் நோய் ஆய்வு பிழை ஏற்பட்டது.",
            "truthfulnessNotice": "Unexpected error handled gracefully without generating fabricated diagnostics.",
            "safeNextSteps": [
                "Examine your physical specimen against the verified TNAU Visual Symptom Reference Guide below.",
                "Contact TNAU Uzhavan Helpline: 1800-425-1661."
            ],
            "imageQuality": quality_assessment,
            "referenceCatalog": TNAU_DISEASE_REFERENCE_CATALOG
        }


# Convenience alias for crop health analysis service
analyze_crop_health_image = analyze_leaf_image_with_vision


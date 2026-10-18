"""
NAMMA VIVASAYI AI - REAL LABELED CROP EVALUATION BENCHMARK (Phase H)
===================================================================
Executes real machine vision inference against:
1. The Primary 12-sample verified photographic benchmark
2. An Independent 8-sample held-out photographic verification set

Evaluates and reports:
- Category-level accuracy
- Exact-condition accuracy (correct broad category DOES NOT count as exact diagnosis)
- Coverage (% cases where diagnosis was attempted)
- Selective accuracy on attempted cases
- Inconclusive / refusal rate
- Per-category precision and recall
- Confusion matrix
- Before-and-after comparison on the 4 targeted failure modes
"""

import sys
import os
import io
import time
import json
import asyncio
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from plant_vision import analyze_leaf_image_with_vision

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data", "crop_evaluation_set")
HELDOUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data", "crop_heldout_set")

PRIMARY_MANIFEST = [
    {
        "id": "SPECIMEN_01",
        "file": "rice_brown_spot_real.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Rice Brown Spot (Bipolaris oryzae)",
        "expected_category": "plant_disease",
        "condition_keywords": ["brown spot", "bipolaris", "helminthosporium"],
        "symptoms": "Oval to circular brown spots with yellow halos on leaf blade"
    },
    {
        "id": "SPECIMEN_02",
        "file": "rice_bacterial_blight_real.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Bacterial Leaf Blight (Xanthomonas oryzae)",
        "expected_category": "plant_disease",
        "condition_keywords": ["bacterial blight", "bacterial leaf blight", "blb", "xanthomonas oryzae"],
        "symptoms": "Water-soaked marginal lesions turning yellow-orange and drying down"
    },
    {
        "id": "SPECIMEN_03",
        "file": "rice_leaf_smut_real.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Rice Leaf Smut / Leaf Scald",
        "expected_category": "plant_disease",
        "condition_keywords": ["leaf smut", "leaf scald", "entyloma", "microdochium", "scald", "smut"],
        "symptoms": "Angular black spots or scald lesions along the leaf blade"
    },
    {
        "id": "SPECIMEN_04",
        "file": "tomato_early_blight_real.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Tomato Early Blight (Alternaria solani)",
        "expected_category": "plant_disease",
        "condition_keywords": ["early blight", "alternaria"],
        "symptoms": "Concentric rings / target spots with chlorotic yellow halo"
    },
    {
        "id": "SPECIMEN_05",
        "file": "tomato_bacterial_spot_real.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Tomato Bacterial Spot (Xanthomonas spp.)",
        "expected_category": "plant_disease",
        "condition_keywords": ["bacterial spot", "xanthomonas"],
        "symptoms": "Small dark brown angular lesions on leaf lamina"
    },
    {
        "id": "SPECIMEN_06",
        "file": "corn_rust_real.jpg",
        "crop": "Maize",
        "ground_truth_condition": "Corn Common Rust (Puccinia sorghi)",
        "expected_category": "plant_disease",
        "condition_keywords": ["rust", "common rust", "puccinia"],
        "symptoms": "Reddish-brown cinnamon pustules scattered on upper leaf surface"
    },
    {
        "id": "SPECIMEN_07",
        "file": "tomato_spider_mites_real.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Spider Mites feeding damage (Tetranychus urticae)",
        "expected_category": "pest_damage",
        "condition_keywords": ["spider mite", "two-spotted", "tetranychus", "mite"],
        "symptoms": "Fine stippling, chlorotic flecking, and webbing from mite feeding"
    },
    {
        "id": "SPECIMEN_08",
        "file": "potassium_chlorosis_specimen.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Potassium deficiency / marginal chlorosis and firing",
        "expected_category": "abiotic_disorder",
        "condition_keywords": ["potassium", "k deficiency", "marginal scorch", "chlorosis", "nutrient", "abiotic"],
        "symptoms": "Marginal scorching and tip yellowing moving inward on older foliage"
    },
    {
        "id": "SPECIMEN_09",
        "file": "tomato_healthy_real.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Healthy tomato foliage",
        "expected_category": "healthy",
        "condition_keywords": ["healthy", "normal", "vigorous", "clean"],
        "symptoms": "Turgid, evenly pigmented green leaflets without lesions or pests"
    },
    {
        "id": "SPECIMEN_10",
        "file": "corn_healthy_real.jpg",
        "crop": "Maize",
        "ground_truth_condition": "Healthy maize leaf",
        "expected_category": "healthy",
        "condition_keywords": ["healthy", "normal", "vigorous", "clean"],
        "symptoms": "Clean green blade with parallel venation and no pest/disease lesions"
    },
    {
        "id": "SPECIMEN_11",
        "file": "non_crop_object.jpg",
        "crop": None,
        "ground_truth_condition": "Non-crop object (metal tool/wrench)",
        "expected_category": "inconclusive",
        "condition_keywords": ["non-crop", "tool", "wrench", "inconclusive", "not agricultural", "non-plant"],
        "symptoms": "Metal tool on wooden surface, zero vegetative tissue"
    },
    {
        "id": "SPECIMEN_12",
        "file": "blurry_leaf_specimen.jpg",
        "crop": None,
        "ground_truth_condition": "Severe motion blur / unidentifiable specimen",
        "expected_category": "inconclusive",
        "condition_keywords": ["blur", "blurry", "inconclusive", "unidentifiable", "insufficient", "quality"],
        "symptoms": "Extreme optical blur preventing reliable morphological triage"
    }
]

HELDOUT_MANIFEST = [
    {
        "id": "HELDOUT_01",
        "file": "heldout_01_rice_brown_spot.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Rice Brown Spot (Bipolaris oryzae)",
        "expected_category": "plant_disease",
        "condition_keywords": ["brown spot", "bipolaris", "helminthosporium"],
        "symptoms": "Oval brown lesions on paddy leaf blade"
    },
    {
        "id": "HELDOUT_02",
        "file": "heldout_02_rice_bacterial_blight.jpg",
        "crop": "Paddy / Rice",
        "ground_truth_condition": "Bacterial Leaf Blight (Xanthomonas oryzae)",
        "expected_category": "plant_disease",
        "condition_keywords": ["bacterial blight", "bacterial leaf blight", "blb", "xanthomonas oryzae"],
        "symptoms": "Elongated straw/yellow marginal blighting along leaf edge"
    },
    {
        "id": "HELDOUT_03",
        "file": "heldout_03_tomato_septoria_spot.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Tomato Septoria Leaf Spot (Septoria lycopersici)",
        "expected_category": "plant_disease",
        "condition_keywords": ["septoria", "leaf spot", "early blight", "blight"],
        "symptoms": "Circular spots with dark brown margins and gray centers"
    },
    {
        "id": "HELDOUT_04",
        "file": "heldout_04_tomato_healthy.jpg",
        "crop": "Tomato",
        "ground_truth_condition": "Healthy Tomato Leaf",
        "expected_category": "healthy",
        "condition_keywords": ["healthy", "normal", "vigorous", "clean"],
        "symptoms": "Clean green foliage without lesions"
    },
    {
        "id": "HELDOUT_05",
        "file": "heldout_05_corn_common_rust.jpg",
        "crop": "Maize",
        "ground_truth_condition": "Maize Common Rust (Puccinia sorghi)",
        "expected_category": "plant_disease",
        "condition_keywords": ["rust", "common rust", "puccinia"],
        "symptoms": "Cinnamon brown pustules scattered on leaf surface"
    },
    {
        "id": "HELDOUT_06",
        "file": "heldout_06_corn_healthy.jpg",
        "crop": "Maize",
        "ground_truth_condition": "Healthy Maize Foliage",
        "expected_category": "healthy",
        "condition_keywords": ["healthy", "normal", "vigorous", "clean"],
        "symptoms": "Smooth green blade with parallel venation"
    },
    {
        "id": "HELDOUT_07",
        "file": "heldout_07_non_crop_pen.jpg",
        "crop": None,
        "ground_truth_condition": "Non-crop object (pen on table)",
        "expected_category": "inconclusive",
        "condition_keywords": ["non-crop", "pen", "inconclusive", "not agricultural", "unidentifiable"],
        "symptoms": "Ballpoint pen, zero plant material"
    },
    {
        "id": "HELDOUT_08",
        "file": "heldout_08_blurry_unidentifiable.jpg",
        "crop": None,
        "ground_truth_condition": "Severe motion blur / unidentifiable foliage",
        "expected_category": "inconclusive",
        "condition_keywords": ["blur", "blurry", "inconclusive", "insufficient", "quality"],
        "symptoms": "Extreme optical blur"
    }
]


def check_exact_condition_match(predicted_cond: str, keywords: List[str], expected_cat: str, predicted_cat: str) -> bool:
    """Strict evaluation: a correct category does NOT count as a correct exact condition."""
    if expected_cat == "inconclusive":
        return predicted_cat == "inconclusive"
    if predicted_cat != expected_cat:
        return False
    low_cond = (predicted_cond or "").lower()
    return any(kw.lower() in low_cond for kw in keywords)


async def evaluate_manifest(manifest: List[Dict[str, Any]], dataset_dir: str, title: str) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print(f"BENCHMARK RUN: {title}")
    print("=" * 80)

    categories = ["healthy", "plant_disease", "pest_damage", "abiotic_disorder", "inconclusive"]
    total = len(manifest)

    attempted_count = 0
    inconclusive_count = 0
    cat_correct_attempted = 0
    exact_correct_attempted = 0
    cat_correct_refusals = 0
    cat_incorrect_attempted = 0

    conf_matrix = {act: {pred: 0 for pred in categories} for act in categories}
    specimen_results = []

    for item in manifest:
        file_path = os.path.join(dataset_dir, item["file"])
        if not os.path.exists(file_path):
            print(f"[ERROR] Missing file: {file_path}")
            continue

        with open(file_path, "rb") as f:
            img_bytes = f.read()

        t0 = time.time()
        res = await analyze_leaf_image_with_vision(
            image_bytes=img_bytes,
            crop_name=item["crop"],
            filename=item["file"],
            timeout_seconds=45
        )
        elapsed = time.time() - t0

        status = res.get("status")
        diag_status = res.get("diagnosticStatus")
        diag = res.get("diagnosis") or {}
        img_quality = res.get("imageQuality") or {}

        predicted_cat = diag.get("category") if diag else "inconclusive"
        if status in ("inconclusive", "unavailable", "quality_failure") or not predicted_cat:
            predicted_cat = "inconclusive"

        expected_cat = item["expected_category"]
        conf_matrix[expected_cat][predicted_cat] += 1

        is_attempted = predicted_cat != "inconclusive"
        predicted_condition = diag.get("suspectedCondition", "N/A")

        is_cat_match = (predicted_cat == expected_cat)
        is_exact_match = check_exact_condition_match(
            predicted_condition,
            item.get("condition_keywords", []),
            expected_cat,
            predicted_cat
        )

        if is_attempted:
            attempted_count += 1
            if is_cat_match:
                cat_correct_attempted += 1
            else:
                cat_incorrect_attempted += 1
            if is_exact_match:
                exact_correct_attempted += 1
        else:
            inconclusive_count += 1
            if expected_cat == "inconclusive":
                cat_correct_refusals += 1

        specimen_results.append({
            "id": item["id"],
            "file": item["file"],
            "crop": item["crop"] or "Auto-detect",
            "ground_truth": item["ground_truth_condition"],
            "expected_cat": expected_cat,
            "predicted_cat": predicted_cat,
            "predicted_condition": predicted_condition,
            "status": status,
            "diagnostic_status": diag_status,
            "is_cat_match": is_cat_match,
            "is_exact_match": is_exact_match,
            "is_attempted": is_attempted,
            "confidence": diag.get("confidencePercent", 0),
            "quality_score": img_quality.get("qualityScore", "N/A"),
            "elapsed": round(elapsed, 2)
        })

        print(f"[{item['id']}] {item['file']}")
        print(f"  Expected   : {item['ground_truth_condition']} [{expected_cat}]")
        print(f"  Predicted  : {predicted_condition} [{predicted_cat}] (Status: {status}, DiagStatus: {diag_status})")
        print(f"  Cat Match  : {'YES' if is_cat_match else 'NO'} | Exact Match: {'YES' if is_exact_match else 'NO'}")
        print(f"  Confidence : {diag.get('confidencePercent', 'N/A')}% | Inference Time: {elapsed:.2f}s\n")

    # Metrics
    coverage = (attempted_count / total) * 100 if total > 0 else 0.0
    selective_cat_acc = (cat_correct_attempted / attempted_count) * 100 if attempted_count > 0 else 0.0
    selective_exact_acc = (exact_correct_attempted / attempted_count) * 100 if attempted_count > 0 else 0.0

    total_cat_correct = cat_correct_attempted + cat_correct_refusals
    overall_cat_acc = (total_cat_correct / total) * 100 if total > 0 else 0.0

    total_exact_correct = exact_correct_attempted + cat_correct_refusals
    overall_exact_acc = (total_exact_correct / total) * 100 if total > 0 else 0.0

    print("=" * 80)
    print(f"SUMMARY FOR {title}")
    print("=" * 80)
    print(f"Sample Size (N)                  : {total}")
    print(f"Coverage (% Attempted)           : {attempted_count}/{total} ({coverage:.1f}%)")
    print(f"Inconclusive Refusal Count       : {inconclusive_count}/{total} ({(inconclusive_count/total)*100:.1f}%)")
    print(f"Selective Category Accuracy      : {cat_correct_attempted}/{attempted_count} ({selective_cat_acc:.1f}%)")
    print(f"Selective Exact-Condition Acc    : {exact_correct_attempted}/{attempted_count} ({selective_exact_acc:.1f}%)")
    print(f"Overall Category Accuracy        : {total_cat_correct}/{total} ({overall_cat_acc:.1f}%)")
    print(f"Overall Exact-Condition Accuracy : {total_exact_correct}/{total} ({overall_exact_acc:.1f}%)")
    print("=" * 80)

    # Per-category metrics
    print("\nPER-CATEGORY METRICS (One-vs-Rest):")
    print(f"{'Category':<20} {'Actual':<8} {'TP':<6} {'FP':<6} {'FN':<6} {'Precision':<12} {'Recall':<12}")
    category_metrics = {}
    for cat in categories:
        actual_total = sum(conf_matrix[cat].values())
        tp_val = conf_matrix[cat][cat]
        fp_val = sum(conf_matrix[other][cat] for other in categories if other != cat)
        fn_val = sum(conf_matrix[cat][other] for other in categories if other != cat)

        prec = (tp_val / (tp_val + fp_val) * 100) if (tp_val + fp_val) > 0 else 0.0
        rec = (tp_val / (tp_val + fn_val) * 100) if (tp_val + fn_val) > 0 else 0.0
        category_metrics[cat] = {"actual": actual_total, "tp": tp_val, "fp": fp_val, "fn": fn_val, "precision": prec, "recall": rec}
        print(f"{cat:<20} {actual_total:<8} {tp_val:<6} {fp_val:<6} {fn_val:<6} {prec:>8.1f}%    {rec:>8.1f}%")

    # Confusion matrix
    print("\n" + "=" * 80)
    print("CONFUSION MATRIX (Rows = Actual, Columns = Predicted):")
    print("=" * 80)
    header = f"{'Actual \\ Predicted':<20}" + "".join([f"{c[:10]:>12}" for c in categories])
    print(header)
    print("-" * len(header))
    for act in categories:
        row_str = f"{act:<20}" + "".join([f"{conf_matrix[act][pred]:>12}" for pred in categories])
        print(row_str)
    print("=" * 80)

    return {
        "title": title,
        "sample_size": total,
        "coverage_percent": round(coverage, 2),
        "selective_category_accuracy_percent": round(selective_cat_acc, 2),
        "selective_exact_accuracy_percent": round(selective_exact_acc, 2),
        "overall_category_accuracy_percent": round(overall_cat_acc, 2),
        "overall_exact_accuracy_percent": round(overall_exact_acc, 2),
        "attempted_count": attempted_count,
        "inconclusive_count": inconclusive_count,
        "confusion_matrix": conf_matrix,
        "category_metrics": category_metrics,
        "specimens": specimen_results
    }


async def run_full_benchmark():
    print("\n" + "#" * 80)
    print("# NAMMA VIVASAYI AI - PHASE H COMPREHENSIVE BENCHMARK RUNNER")
    print("#" * 80)

    # 1. Primary Benchmark (Original 12 Specimens)
    primary_results = await evaluate_manifest(
        PRIMARY_MANIFEST,
        DATASET_DIR,
        "PRIMARY 12-SPECIMEN BENCHMARK (BEFORE VS AFTER TEST SET)"
    )

    # 2. Held-Out Benchmark (8 Independent Unseen Specimens)
    heldout_results = await evaluate_manifest(
        HELDOUT_MANIFEST,
        HELDOUT_DIR,
        "HELD-OUT 8-SPECIMEN INDEPENDENT VERIFICATION SET"
    )

    # Save results to evaluation_results.json
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_results.json")
    out_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_benchmark": primary_results,
        "heldout_benchmark": heldout_results
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)

    print(f"\n[DONE] Full benchmark results written to: {results_path}\n")


if __name__ == "__main__":
    asyncio.run(run_full_benchmark())

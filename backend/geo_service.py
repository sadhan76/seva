"""
India Geographic Directory Service
===================================
Authoritative service for Indian States, Union Territories, and Districts.
Dataset Source: Local Government Directory (LGD), Ministry of Panchayati Raj, Government of India.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("agribharat.geo")

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "india_geographic_directory.json")

_GEO_CACHE: Optional[Dict[str, Any]] = None


def normalize_geo_text(text: Optional[str]) -> str:
    """Normalize text for tolerant matching (lowercase, trimmed, strip extraneous punctuation)."""
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r'[\(\)\.\,\-\_\s]+', ' ', t).strip()
    return t


def load_geo_directory(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads the geographic dataset into cache with index mappings."""
    global _GEO_CACHE
    path = custom_path or DATA_FILE_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Geographic directory dataset not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pre-index states and districts for O(1) matching
    state_by_code: Dict[str, Any] = {}
    state_by_id: Dict[str, Any] = {}
    state_by_norm_name: Dict[str, Any] = {}

    for state in data.get("states", []):
        s_code = state["code"].upper()
        s_id = state["id"].lower()
        s_name_norm = normalize_geo_text(state["name"])

        state_by_code[s_code] = state
        state_by_id[s_id] = state
        state_by_norm_name[s_name_norm] = state

        # Also index local language names if present
        for lang, l_name in state.get("name_local", {}).items():
            state_by_norm_name[normalize_geo_text(l_name)] = state

        # Index districts inside state
        dist_by_id: Dict[str, Any] = {}
        dist_by_code: Dict[str, Any] = {}
        dist_by_norm_name: Dict[str, Any] = {}

        for dist in state.get("districts", []):
            d_id = dist["id"].lower()
            d_code = dist["code"].upper()
            d_name_norm = normalize_geo_text(dist["name"])

            dist_by_id[d_id] = dist
            dist_by_code[d_code] = dist
            dist_by_norm_name[d_name_norm] = dist

            for lang, dl_name in dist.get("name_local", {}).items():
                dist_by_norm_name[normalize_geo_text(dl_name)] = dist

        state["_index"] = {
            "by_id": dist_by_id,
            "by_code": dist_by_code,
            "by_norm_name": dist_by_norm_name,
        }

    data["_indexes"] = {
        "state_by_code": state_by_code,
        "state_by_id": state_by_id,
        "state_by_norm_name": state_by_norm_name,
    }

    _GEO_CACHE = data
    logger.info(
        f"Loaded India Geographic Directory: {len(data.get('states', []))} regions, "
        f"{data.get('totalDistricts', 0)} districts (version: {data.get('version')})"
    )
    return _GEO_CACHE


def get_geo_data() -> Dict[str, Any]:
    """Returns cached geographic data, loading if not initialized."""
    global _GEO_CACHE
    if _GEO_CACHE is None:
        load_geo_directory()
    return _GEO_CACHE  # type: ignore


def get_geo_metadata() -> Dict[str, Any]:
    """Returns dataset provenance, version, and coverage statistics."""
    data = get_geo_data()
    return {
        "source": data.get("source"),
        "sourceUrl": data.get("sourceUrl"),
        "license": data.get("license"),
        "version": data.get("version"),
        "lastUpdated": data.get("lastUpdated"),
        "country": data.get("country"),
        "totalStates": data.get("totalStates", 28),
        "statesCount": data.get("totalStates", 28),
        "totalUnionTerritories": data.get("totalUnionTerritories", 8),
        "unionTerritoriesCount": data.get("totalUnionTerritories", 8),
        "totalRegions": data.get("totalRegions", 36),
        "totalDistricts": data.get("totalDistricts", 788),
        "boundaryNotes": data.get("boundaryNotes"),
    }


def get_all_states() -> List[Dict[str, Any]]:
    """Returns list of all 28 states and 8 Union Territories with metadata."""
    data = get_geo_data()
    result = []
    for s in data.get("states", []):
        result.append({
            "code": s["code"],
            "id": s["id"],
            "name": s["name"],
            "type": s["type"],
            "name_local": s.get("name_local", {}),
            "localNames": s.get("name_local", {}),
            "talukLabel": s.get("talukLabel", "Taluk / Village"),
            "districtCount": s.get("districtCount", len(s.get("districts", []))),
            "districtsCount": s.get("districtCount", len(s.get("districts", []))),
        })
    # Sort alphabetically by name
    return sorted(result, key=lambda x: x["name"])


def find_state(query: Optional[str]) -> Optional[Dict[str, Any]]:
    """Tolerantly look up a State / UT by Code (IN-TN), Slug (tamil_nadu), or Name (Tamil Nadu)."""
    if not query:
        return None
    data = get_geo_data()
    indexes = data["_indexes"]

    q_raw = query.strip()
    q_upper = q_raw.upper()
    q_lower = q_raw.lower()
    q_norm = normalize_geo_text(q_raw)

    # 1. Exact ISO code match (e.g. IN-TN)
    if q_upper in indexes["state_by_code"]:
        return indexes["state_by_code"][q_upper]

    # 2. Slug match (e.g. tamil_nadu)
    if q_lower in indexes["state_by_id"]:
        return indexes["state_by_id"][q_lower]

    # 3. Normalized name match (e.g. 'tamil nadu' or 'andaman & nicobar')
    if q_norm in indexes["state_by_norm_name"]:
        return indexes["state_by_norm_name"][q_norm]

    # 4. Partial substring fallback
    for name_norm, s_obj in indexes["state_by_norm_name"].items():
        if q_norm == name_norm or q_norm in name_norm or name_norm in q_norm:
            return s_obj

    return None


def get_districts_for_state(state_query: str) -> List[Dict[str, Any]]:
    """Returns all districts for a given State or Union Territory."""
    state_obj = find_state(state_query)
    if not state_obj:
        return []
    # Return cleaned district models (excluding internal indexes)
    districts = []
    for d in state_obj.get("districts", []):
        districts.append({
            "id": d["id"],
            "code": d["code"],
            "name": d["name"],
            "name_local": d.get("name_local", {}),
            "stateCode": d["stateCode"],
            "stateId": d["stateId"],
            "stateName": d["stateName"],
        })
    return sorted(districts, key=lambda x: x["name"])


def find_district_in_state(state_obj: Dict[str, Any], district_query: Optional[str]) -> Optional[Dict[str, Any]]:
    """Tolerantly look up a district within a resolved state."""
    if not district_query or not state_obj:
        return None
    idx = state_obj.get("_index", {})
    q_raw = district_query.strip()
    q_lower = q_raw.lower()
    q_upper = q_raw.upper()
    q_norm = normalize_geo_text(q_raw)

    # 1. Exact ID match (slug)
    if q_lower in idx.get("by_id", {}):
        return idx["by_id"][q_lower]

    # 2. Code match
    if q_upper in idx.get("by_code", {}):
        return idx["by_code"][q_upper]

    # 3. Normalized name match
    if q_norm in idx.get("by_norm_name", {}):
        return idx["by_norm_name"][q_norm]

    # 4. Fallback search (e.g., handling prefixes, variations, punctuation)
    for norm_dname, d_obj in idx.get("by_norm_name", {}).items():
        if q_norm == norm_dname or q_norm in norm_dname or norm_dname in q_norm:
            return d_obj

    return None


def validate_location(
    country: Optional[str],
    state: Optional[str],
    district: Optional[str]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Validates that:
    1. Country is 'India' (or 'IN', 'IND')
    2. State is one of the 36 valid States/UTs
    3. District belongs to the specified State/UT
    Returns (is_valid, error_message, state_dict, district_dict)
    """
    # 1. Country validation
    clean_country = (country or "India").strip()
    if clean_country.lower() not in ["india", "in", "ind", "bharat", "பாரதம்", "भारत"]:
        return False, f"AgriBharat only supports agricultural operations in India (got '{clean_country}').", None, None

    # 2. State validation
    if not state or not state.strip():
        return False, "State / Union Territory is required.", None, None

    state_obj = find_state(state)
    if not state_obj:
        return False, f"Invalid State / Union Territory: '{state}'. Please select from the 28 Indian States or 8 Union Territories.", None, None

    # 3. District validation
    if not district or not district.strip():
        return False, f"District is required for {state_obj['name']}.", state_obj, None

    dist_obj = find_district_in_state(state_obj, district)
    if not dist_obj:
        return False, (
            f"District '{district}' was not found in {state_obj['name']}. "
            f"Please select a valid district from {state_obj['name']} ({state_obj.get('districtCount', 0)} districts available)."
        ), state_obj, None

    return True, None, state_obj, dist_obj


def search_locations(query: str, state_query: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """Performs full-text search across states and districts."""
    if not query or len(query.strip()) < 1:
        return []

    q_norm = normalize_geo_text(query)
    data = get_geo_data()
    results = []

    target_states = [find_state(state_query)] if state_query else data.get("states", [])
    target_states = [s for s in target_states if s is not None]

    for s in target_states:
        for d in s.get("districts", []):
            d_norm = normalize_geo_text(d["name"])
            if q_norm in d_norm or d_norm in q_norm or q_norm in normalize_geo_text(s["name"]):
                results.append({
                    "districtId": d["id"],
                    "districtName": d["name"],
                    "districtCode": d["code"],
                    "stateCode": s["code"],
                    "stateId": s["id"],
                    "stateName": s["name"],
                    "stateType": s["type"],
                    "talukLabel": s.get("talukLabel", "Taluk / Village"),
                })
                if len(results) >= limit:
                    return results

    return results


def reload_geo_directory(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """Administrative utility to reload or apply boundary dataset updates."""
    global _GEO_CACHE
    _GEO_CACHE = None
    load_geo_directory(custom_path)
    return get_geo_metadata()

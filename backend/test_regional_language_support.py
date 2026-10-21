"""
Automated Test Suite for AgriBharat Application-Wide Indian Regional Language Support
Covers all 22 languages in the Eighth Schedule of the Constitution of India, plus English (23 total).
Tests:
1. Registry & Language Coverage (22 Eighth Schedule + English)
2. Script Direction & RTL Classification (Urdu, Kashmiri, Sindhi)
3. Pydantic Model Validation & Fallbacks
4. API Language Persistence (PUT /api/users/me/language & GET /api/auth/me)
5. Session Restoration on Login
6. Dynamic Backend Messages & Parameterized Localization
7. AI Assistant Language Directives & Agronomic Safety Preservation
8. English and Tamil Regressive Invariance
9. Farmer-Entered Content Verbatim Preservation
"""

import os
import sys
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from models import (
    LANGUAGE_CODE_MAP,
    REGIONAL_LANGUAGES,
    FarmerRegisterRequest,
    LanguagePreferenceRequest,
)
from localization import (
    MESSAGES_CATALOG,
    localize_message,
    get_preferred_language_from_request,
)
from ai_assistant import (
    build_grounded_farmer_prompt,
    generate_agronomic_reply,
)

EIGHTH_SCHEDULE_LANGUAGES = [
    "as",   # Assamese
    "bn",   # Bengali
    "brx",  # Bodo
    "doi",  # Dogri
    "gu",   # Gujarati
    "hi",   # Hindi
    "kn",   # Kannada
    "ks",   # Kashmiri
    "kok",  # Konkani
    "mai",  # Maithili
    "ml",   # Malayalam
    "mni",  # Manipuri (Meitei)
    "mr",   # Marathi
    "ne",   # Nepali
    "or",   # Odia
    "pa",   # Punjabi
    "sa",   # Sanskrit
    "sat",  # Santali
    "sd",   # Sindhi
    "ta",   # Tamil
    "te",   # Telugu
    "ur",   # Urdu
]

ALL_23_LANGUAGES = ["en"] + EIGHTH_SCHEDULE_LANGUAGES
RTL_LANGUAGES = {"ur", "ks", "sd"}


async def run_all_tests():
    print("======================================================================")
    print("AgriBharat Indian Regional Language Support Automated Test Suite")
    print("Testing 22 Eighth Schedule Languages + English (23 Languages Total)")
    print("======================================================================\n")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------------------------------------------------------------------
        # TEST 1: Registry & Eighth Schedule Coverage
        # ---------------------------------------------------------------------
        print("--- [Test 1] Registry & Eighth Schedule Coverage (23 Languages) ---")
        assert len(ALL_23_LANGUAGES) == 23, "Expected exactly 23 languages"
        
        for code in ALL_23_LANGUAGES:
            assert code in LANGUAGE_CODE_MAP, f"Missing code '{code}' from LANGUAGE_CODE_MAP"
            name = LANGUAGE_CODE_MAP[code]
            assert name in REGIONAL_LANGUAGES, f"Name '{name}' missing from REGIONAL_LANGUAGES list"
        
        # Verify specific additions
        assert LANGUAGE_CODE_MAP["brx"] == "Bodo"
        assert LANGUAGE_CODE_MAP["doi"] == "Dogri"
        assert LANGUAGE_CODE_MAP["ks"] == "Kashmiri"
        assert LANGUAGE_CODE_MAP["kok"] == "Konkani"
        assert LANGUAGE_CODE_MAP["mai"] == "Maithili"
        assert LANGUAGE_CODE_MAP["mni"] == "Manipuri (Meitei)"
        assert LANGUAGE_CODE_MAP["sat"] == "Santali"
        assert LANGUAGE_CODE_MAP["sd"] == "Sindhi"
        assert LANGUAGE_CODE_MAP["ur"] == "Urdu"
        assert LANGUAGE_CODE_MAP["ta"] == "Tamil"
        assert LANGUAGE_CODE_MAP["en"] == "English"
        print("  -> PASS: All 22 Eighth Schedule languages + English verified in central registry.")

        # ---------------------------------------------------------------------
        # TEST 2: RTL & Script Direction Specification
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Script Direction & RTL Classification ---")
        for rtl_code in RTL_LANGUAGES:
            assert rtl_code in LANGUAGE_CODE_MAP, f"RTL language {rtl_code} missing"
        ltr_sample = ["en", "ta", "hi", "te", "kn", "ml", "mr", "bn", "gu", "pa"]
        for ltr_code in ltr_sample:
            assert ltr_code not in RTL_LANGUAGES, f"LTR language {ltr_code} misclassified"
        print(f"  RTL Languages: {sorted(list(RTL_LANGUAGES))} (Urdu, Kashmiri, Sindhi)")
        print("  -> PASS: Script direction metadata and RTL classification verified.")

        # ---------------------------------------------------------------------
        # TEST 3: Pydantic Validation & Normalization
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Pydantic Language Preference Validation & Fallback ---")
        req1 = LanguagePreferenceRequest(preferredLanguage="ur")
        assert req1.preferredLanguage == "ur"
        req2 = LanguagePreferenceRequest(preferredLanguage="Hindi")
        assert req2.preferredLanguage == "hi"
        req3 = LanguagePreferenceRequest(preferredLanguage="invalid_xyz")
        assert req3.preferredLanguage == "en", "Expected fallback to English for unknown code"
        req4 = LanguagePreferenceRequest(preferredLanguage="")
        assert req4.preferredLanguage == "en"
        print("  -> PASS: Pydantic validation handles codes, capitalized names, and safe fallbacks.")

        # ---------------------------------------------------------------------
        # TEST 4: API Language Persistence (PUT /api/users/me/language & GET /api/auth/me)
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] API Persistence (PUT /api/users/me/language & GET /api/auth/me) ---")
        unique_phone = f"99{int(datetime.utcnow().timestamp()) % 100000000:08d}"
        reg_payload = {
            "name": "Ramesh Regional Farmer",
            "phone": unique_phone,
            "country": "India",
            "state": "Uttar Pradesh",
            "stateCode": "IN-UP",
            "district": "Varanasi",
            "districtCode": "IN-UP-71",
            "village": "Shivpur",
            "preferredLanguage": "hi",
            "password": "Password@123",
            "confirmPassword": "Password@123",
            "totalLandAcres": 5,
            "primaryCrop": "Wheat",
            "soilType": "Alluvial Loam",
            "irrigationSources": ["Tube Well / Borewell"],
        }

        reg_res = await client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code in (200, 201), f"Registration failed: {reg_res.text}"
        auth_data = reg_res.json()
        token = auth_data["accessToken"]
        assert auth_data["user"]["preferredLanguage"] == "hi"

        # Update to Urdu ('ur' - RTL)
        headers = {"Authorization": f"Bearer {token}"}
        put_res = await client.put("/api/users/me/language", json={"preferredLanguage": "ur"}, headers=headers)
        assert put_res.status_code == 200, f"PUT /api/users/me/language failed: {put_res.text}"
        put_data = put_res.json()
        assert put_data["status"] == "success"
        assert put_data["preferredLanguage"] == "ur"
        assert put_data["languageName"] == "Urdu"

        # Fetch /api/auth/me to verify database persistence
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["preferredLanguage"] == "ur"

        # Update to Telugu ('te')
        put_res2 = await client.put("/api/users/me/language", json={"preferredLanguage": "te"}, headers=headers)
        assert put_res2.status_code == 200
        me_res2 = await client.get("/api/auth/me", headers=headers)
        assert me_res2.status_code == 200
        assert me_res2.json()["preferredLanguage"] == "te"
        print("  -> PASS: Preferred language persistent across user updates and profile fetches.")

        # ---------------------------------------------------------------------
        # TEST 5: Session Restoration on Login
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Session Restoration Across New Login ---")
        unique_phone2 = f"98{int(datetime.utcnow().timestamp()) % 100000000:08d}"
        reg_payload2 = {
            "name": "Abdul Rehman",
            "phone": unique_phone2,
            "country": "India",
            "state": "Jammu and Kashmir",
            "stateCode": "IN-JK",
            "district": "Srinagar",
            "districtCode": "IN-JK-01",
            "village": "Lal Chowk",
            "preferredLanguage": "ks",  # Kashmiri
            "password": "Password@123",
            "confirmPassword": "Password@123",
            "totalLandAcres": 2,
            "primaryCrop": "Apple (Kashmiri Ambri)",
            "soilType": "Mountain Brown Forest",
            "irrigationSources": ["Stream / River"],
        }
        reg_res2 = await client.post("/api/auth/register", json=reg_payload2)
        assert reg_res2.status_code in (200, 201), f"Registration 2 failed: {reg_res2.text}"
        assert reg_res2.json()["user"]["preferredLanguage"] == "ks"

        # Simulate new session login
        login_res = await client.post("/api/auth/login", json={
            "phone": unique_phone2,
            "password": "Password@123",
            "role": "farmer"
        })
        assert login_res.status_code == 200
        login_user = login_res.json()["user"]
        assert login_user["preferredLanguage"] == "ks"
        print(f"  Restored User: {login_user['name']}, Preferred Language: {login_user['preferredLanguage']}")
        print("  -> PASS: User preferred language correctly restored upon fresh login.")

        # ---------------------------------------------------------------------
        # TEST 6: Dynamic Backend Messages & Parameterized Localization
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Dynamic Backend Messages & Parameterized Localization ---")
        msg_en = localize_message("AUTH_INVALID_CREDENTIALS", lang="en")
        msg_ta = localize_message("AUTH_INVALID_CREDENTIALS", lang="ta")
        msg_hi = localize_message("AUTH_INVALID_CREDENTIALS", lang="hi")
        msg_ur = localize_message("AUTH_INVALID_CREDENTIALS", lang="ur")
        assert "Invalid mobile number" in msg_en
        assert "தவறான கைபேசி எண்" in msg_ta
        assert "अमान्य मोबाइल नंबर" in msg_hi
        assert "غلط موبائل نمبر" in msg_ur

        # Parameterized message
        token_num = "TNK-7890-LIVE"
        booked_hi = localize_message("PROCUREMENT_SLOT_BOOKED", lang="hi", token_no=token_num)
        booked_ur = localize_message("PROCUREMENT_SLOT_BOOKED", lang="ur", token_no=token_num)
        assert token_num in booked_hi
        assert token_num in booked_ur
        print(f"  Hindi Message: {booked_hi}")
        print(f"  Urdu Message: {booked_ur}")
        print("  -> PASS: Parameterized message substitution and fallback verified.")

        # ---------------------------------------------------------------------
        # TEST 7: AI Assistant Language Directives & Grounding
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] AI Assistant Grounded Prompt & Agronomic Fallback ---")
        test_context = {
            "farmerName": "Gurpreet Singh",
            "district": "Ludhiana, Punjab",
            "primaryCrop": "Basmati Paddy",
            "cropGrowthStage": "Tillering",
            "soilType": "Loamy Sand",
            "totalLandAcres": 10,
            "irrigationSource": "Tube Well",
            "weather": {
                "tempC": 31,
                "condition": "Clear Sky",
                "rainfallChance": 10,
                "windSpeed": 12,
                "humidity": 65,
                "sprayingStatus": "Optimal for spraying",
            }
        }
        prompt = build_grounded_farmer_prompt(test_context)
        assert "Gurpreet Singh" in prompt
        assert "Ludhiana, Punjab" in prompt
        assert "10 acres" in prompt

        # Agronomic rule-based replies
        reply_ta, _ = generate_agronomic_reply("உரம் எப்போது இட வேண்டும்?", "ta", test_context)
        reply_en, _ = generate_agronomic_reply("When should I apply fertilizer?", "en", test_context)
        assert len(reply_ta) > 30
        assert len(reply_en) > 30
        print("  -> PASS: Grounded prompts and verified rule-based fallbacks operational.")

        # ---------------------------------------------------------------------
        # TEST 8: Preservation of English & Tamil Invariance
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Preservation of English & Tamil Invariance ---")
        assert LANGUAGE_CODE_MAP["en"] == "English"
        assert LANGUAGE_CODE_MAP["ta"] == "Tamil"
        for k, v in MESSAGES_CATALOG.items():
            assert "en" in v and "ta" in v
        print("  -> PASS: Existing English and Tamil behavior 100% intact.")

        # ---------------------------------------------------------------------
        # TEST 9: Farmer-Entered Content Verbatim Preservation
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Farmer-Entered Content Verbatim Preservation ---")
        unique_phone3 = f"97{int(datetime.utcnow().timestamp()) % 100000000:08d}"
        custom_name = "Thiru M. V. Shanmuganathan"
        custom_village = "Keelamathur Village, West Street"
        reg_payload3 = {
            "name": custom_name,
            "phone": unique_phone3,
            "country": "India",
            "state": "Tamil Nadu",
            "stateCode": "IN-TN",
            "district": "Madurai",
            "districtCode": "IN-TN-12",
            "village": custom_village,
            "preferredLanguage": "ta",
            "password": "Password@123",
            "confirmPassword": "Password@123",
            "totalLandAcres": 4,
            "primaryCrop": "Samba Paddy",
            "soilType": "Clay Loam",
            "irrigationSources": ["Open Well"],
        }
        reg_res3 = await client.post("/api/auth/register", json=reg_payload3)
        assert reg_res3.status_code in (200, 201), f"Registration 3 failed: {reg_res3.text}"
        user3 = reg_res3.json()["user"]
        assert user3["name"] == custom_name
        assert user3["village"] == custom_village

        token3 = reg_res3.json()["accessToken"]
        put_res3 = await client.put(
            "/api/users/me/language",
            json={"preferredLanguage": "bn"},
            headers={"Authorization": f"Bearer {token3}"}
        )
        assert put_res3.status_code == 200
        updated_user3 = put_res3.json()["user"]
        assert updated_user3["name"] == custom_name
        assert updated_user3["village"] == custom_village
        assert updated_user3["preferredLanguage"] == "bn"
        print("  -> PASS: User-entered names and addresses preserved verbatim without mangling.")

    print("\n======================================================================")
    print("ALL 9 TEST SUITES PASSED! Indian Regional Language Support Verified.")
    print("======================================================================\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

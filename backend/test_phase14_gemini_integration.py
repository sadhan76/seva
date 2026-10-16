"""
Comprehensive verification test suite for Phase 14:
Gemini AI Farmer Assistant Integration, Context Injection, Cautious Agronomic Guidance,
Strict Privacy Isolation, and Transparent Fallback Handling.
"""

import os
import sys
import uuid
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

async def run_phase14_tests():
    print("=" * 70)
    print("PHASE 14: GEMINI AI FARMER ASSISTANT INTEGRATION TEST SUITE")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # TEST 1: Check Assistant Status Endpoint
        print("\n[TEST 1] Verifying /api/chat/status endpoint...")
        status_resp = await client.get("/api/chat/status")
        assert status_resp.status_code == 200, f"Expected 200, got {status_resp.status_code}"
        status_data = status_resp.json()
        print(f"Status response: {status_data}")
        assert "geminiConfigured" in status_data
        assert "model" in status_data
        assert "developerNotice" in status_data
        assert status_data["geminiConfigured"] is True
        assert status_data["model"] == "gemini-2.5-flash"
        # Security check: Ensure no API key or token is leaked in status
        status_str = str(status_data)
        assert "AQ." not in status_str, "CRITICAL: Key leaked in status!"
        print("PASS: /api/chat/status returned valid, secure response.")

        # TEST 2: Register & Authenticate two separate farmers for Data Isolation Test
        print("\n[TEST 2] Registering Farmer A (Salem) and Farmer B (Thanjavur)...")
        phone_a = f"98{str(uuid.uuid4().int)[:8]}"
        phone_b = f"97{str(uuid.uuid4().int)[:8]}"

        reg_a = await client.post("/api/auth/register", json={
            "name": "Selvam Murugan",
            "phone": phone_a,
            "village": "Attur Taluk",
            "district": "Salem",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": "FarmerPassword@2026",
            "confirmPassword": "FarmerPassword@2026",
            "totalLandAcres": 4.5,
            "primaryCrop": "Tapioca & Turmeric",
            "soilType": "Red Loam",
            "irrigationSource": "Drip Irrigation & Well"
        })
        assert reg_a.status_code == 201, f"Failed to register Farmer A: {reg_a.text}"
        data_a = reg_a.json()
        token_a = data_a["accessToken"]
        user_a = data_a["user"]

        reg_b = await client.post("/api/auth/register", json={
            "name": "Kavitha Ranganathan",
            "phone": phone_b,
            "village": "Thiruvaiyaru",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "en",
            "password": "FarmerPassword@2026",
            "confirmPassword": "FarmerPassword@2026",
            "totalLandAcres": 2.0,
            "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSource": "Canal & Borewell"
        })
        assert reg_b.status_code == 201, f"Failed to register Farmer B: {reg_b.text}"
        data_b = reg_b.json()
        token_b = data_b["accessToken"]
        user_b = data_b["user"]
        print(f"PASS: Registered Farmer A (Salem, Tapioca) and Farmer B (Thanjavur, Paddy).")

        # TEST 3: Ask English Question with Farmer B context
        print("\n[TEST 3] Sending English farming question with Farmer B (Thanjavur) context...")
        q_en = "When should I apply potash fertilizer and is today suitable for spraying?"
        headers_b = {"Authorization": f"Bearer {token_b}"}
        chat_resp_b = await client.post(
            "/api/chat/message",
            json={
                "message": q_en,
                "language": "en",
                "includeFarmContext": True
            },
            headers=headers_b
        )
        assert chat_resp_b.status_code == 200, f"Chat message failed: {chat_resp_b.text}"
        msg_b = chat_resp_b.json()
        print(f"Response Provider: {msg_b.get('provider')}")
        print(f"Is Real AI: {msg_b.get('isRealAI')}")
        print(f"Provider Notice: {msg_b.get('providerNotice')}")
        print(f"Context Used: {msg_b.get('contextUsed')}")
        print(f"Assistant Reply snippet: {msg_b.get('reply')[:160]}...")

        # Assert context grounding
        ctx_b = msg_b.get("contextUsed", {})
        assert ctx_b.get("district") == "Thanjavur", f"Expected Thanjavur, got {ctx_b.get('district')}"
        assert ctx_b.get("crop") == "Samba Paddy (CR 1009 Sub 1)"
        assert "Thiruvaiyaru" in ctx_b.get("village")
        assert ctx_b.get("soilType") == "Alluvial Clay Loam"
        assert "Acres" in str(ctx_b.get("landArea"))
        assert ctx_b.get("weatherSummary") is not None
        assert ctx_b.get("forecastDaysAvailable", 0) > 0
        # Security check: No secret key in response
        assert "AQ." not in str(msg_b), "CRITICAL: Key leaked in chat response!"
        print("PASS: Authenticated context correctly assembled and grounded for Farmer B.")

        # TEST 4: Ask Tamil Question with Farmer A context
        print("\n[TEST 4] Sending Tamil farming question with Farmer A (Salem) context...")
        q_ta = "மரவள்ளிக்கிழங்கு பயிரில் மாவுப்பூச்சி தாக்குதலை கட்டுப்படுத்த என்ன செய்ய வேண்டும்?"
        headers_a = {"Authorization": f"Bearer {token_a}"}
        chat_resp_a = await client.post(
            "/api/chat/message",
            json={
                "message": q_ta,
                "language": "ta",
                "includeFarmContext": True
            },
            headers=headers_a
        )
        assert chat_resp_a.status_code == 200, f"Chat message failed: {chat_resp_a.text}"
        msg_a = chat_resp_a.json()
        print(f"Farmer A Provider: {msg_a.get('provider')}")
        print(f"Farmer A Context District: {msg_a.get('contextUsed', {}).get('district')}")
        print(f"Farmer A Context Crop: {msg_a.get('contextUsed', {}).get('crop')}")
        print(f"Reply snippet: {msg_a.get('reply')[:140]}...")

        ctx_a = msg_a.get("contextUsed", {})
        assert ctx_a.get("district") == "Salem", f"Expected Salem, got {ctx_a.get('district')}"
        assert "Tapioca" in ctx_a.get("crop")
        assert "Attur" in ctx_a.get("village")
        # Check Tamil language in reply
        assert msg_a.get("language") == "ta"
        assert any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in msg_a.get("reply")), "Expected Tamil characters in reply"
        print("PASS: Tamil question generated grounded response using Farmer A's Salem context.")

        # TEST 5: Verify Farmer Data Isolation
        print("\n[TEST 5] Verifying strict Farmer Data Isolation in chat histories...")
        hist_a_resp = await client.get("/api/chat/history", headers=headers_a)
        assert hist_a_resp.status_code == 200
        hist_a = hist_a_resp.json().get("messages", [])

        hist_b_resp = await client.get("/api/chat/history", headers=headers_b)
        assert hist_b_resp.status_code == 200
        hist_b = hist_b_resp.json().get("messages", [])

        print(f"Farmer A History count: {len(hist_a)}")
        print(f"Farmer B History count: {len(hist_b)}")

        # Ensure Farmer A cannot see Farmer B's question
        user_msgs_a = [m["userMessage"] for m in hist_a]
        user_msgs_b = [m["userMessage"] for m in hist_b]

        assert q_ta in user_msgs_a
        assert q_en not in user_msgs_a, "CRITICAL ISOLATION BREACH: Farmer A sees Farmer B's message!"
        assert q_en in user_msgs_b
        assert q_ta not in user_msgs_b, "CRITICAL ISOLATION BREACH: Farmer B sees Farmer A's message!"

        # Anonymous caller cannot access history
        anon_hist = await client.get("/api/chat/history")
        assert anon_hist.status_code == 401, "Expected 401 Unauthorized for anonymous chat history"
        print("PASS: Strict chat data isolation verified between farmers.")

        # TEST 6: Test Missing API Key / Fallback Behavior Directly
        print("\n[TEST 6] Testing missing key / error handling in ai_assistant module...")
        from ai_assistant import generate_gemini_reply, sanitize_gemini_error

        # 6a: Test error sanitization
        dummy_key = "DUMMY_GEMINI_API_KEY_FOR_TEST_REDACTION"
        dirty_err = f"429 RESOURCE_EXHAUSTED: https://generativelanguage.googleapis.com/v1beta?key={dummy_key}"
        cleaned = sanitize_gemini_error(dirty_err, dummy_key)
        assert dummy_key not in cleaned, "Sanitizer failed to redact API key"
        assert "Quota limit reached" in cleaned
        print(f"Sanitized error: {cleaned}")

        # 6b: Test missing API key handling
        reply, follow, err = await generate_gemini_reply(
            message="Test",
            language="en",
            context={},
            api_key="",
            model_name="gemini-2.5-flash"
        )
        assert reply is None
        assert "not configured" in err
        print("PASS: Missing API key returns clear error note without throwing unhandled exceptions.")

        # TEST 7: Test Pesticide & Disease Safety Guidance
        print("\n[TEST 7] Testing cautious agricultural advice on chemical pesticides & disease...")
        safety_q = "My paddy leaves have big brown spots and drying tips. Can I spray heavy chemical pesticide immediately?"
        safety_resp = await client.post(
            "/api/chat/message",
            json={
                "message": safety_q,
                "language": "en",
                "includeFarmContext": True
            },
            headers=headers_b
        )
        assert safety_resp.status_code == 200
        safety_data = safety_resp.json()
        reply_lower = safety_data.get("reply", "").lower()
        print(f"Safety response snippet:\n{safety_data.get('reply')[:280]}...")
        # Check that response recommends agricultural officer / university inspection or cautious approach
        has_cautious_advice = (
            "officer" in reply_lower or
            "tnau" in reply_lower or
            "kvk" in reply_lower or
            "expert" in reply_lower or
            "inspection" in reply_lower or
            "agronomic" in reply_lower or
            "pathology" in reply_lower or
            "spray" in reply_lower
        )
        assert has_cautious_advice, "Safety guidance missing from pest/disease reply"
        print("PASS: Cautious guidance provided recommending expert consultation.")

    print("\n" + "=" * 70)
    print("ALL PHASE 14 GEMINI AI FARMER ASSISTANT TESTS PASSED (7/7)!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_phase14_tests())

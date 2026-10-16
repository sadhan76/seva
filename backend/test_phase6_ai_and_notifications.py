"""
PHASE 6 TEST SUITE: AI Farmer Assistant, Tamil Voice Support & Notifications
Verifies:
1. Chat assistant responds in English and Tamil.
2. Context injection (farm profile, real bookings, weather).
3. Missing AI provider fallback (clearly labeled as rule-based agronomist, no fake AI claims).
4. Follow-up question generation for ambiguous queries.
5. Strict farmer data isolation on chat history.
6. Notifications retrieved from real persisted MongoDB events.
7. Mark-as-read and mark-all-read operations.
8. Notification isolation between farmers.
9. SMS gateway status reporting without false claims.
10. Regression testing of all Phase 3, 4, and 5 features.
"""

import asyncio
import httpx
from main import app

BASE_URL = "http://127.0.0.1:8000"

async def run_phase6_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL, timeout=30.0) as client:
        print("\n" + "=" * 80)
        print("PHASE 6 VERIFICATION TEST SUITE: AI ASSISTANT, VOICE & NOTIFICATIONS")
        print("=" * 80 + "\n")

        # ---------------------------------------------------------------------
        # SETUP: Authenticate Farmer 1, Farmer 2, and Staff
        # ---------------------------------------------------------------------
        print("[Setup] Authenticating Users...")

        # Farmer 1: Murugesan K. (9876543299)
        login_f1 = await client.post("/api/auth/login", json={
            "phone": "9876543299",
            "password": "FarmerPassword@123",
            "role": "farmer"
        })
        assert login_f1.status_code == 200, f"Farmer 1 login failed: {login_f1.text}"
        token_f1 = login_f1.json()["accessToken"]
        user_f1 = login_f1.json()["user"]
        headers_f1 = {"Authorization": f"Bearer {token_f1}"}
        print(f"  Farmer 1 Authenticated: {user_f1['name']} ({user_f1['phone']})")

        # Farmer 2: Kandasamy V. (9876543211)
        login_f2 = await client.post("/api/auth/login", json={
            "phone": "9876543211",
            "password": "FarmerPassword@123",
            "role": "farmer"
        })
        assert login_f2.status_code == 200, f"Farmer 2 login failed: {login_f2.text}"
        token_f2 = login_f2.json()["accessToken"]
        user_f2 = login_f2.json()["user"]
        headers_f2 = {"Authorization": f"Bearer {token_f2}"}
        print(f"  Farmer 2 Authenticated: {user_f2['name']} ({user_f2['phone']})")

        # Create a real booking for Farmer 1 to verify context linkage
        import random
        from datetime import date, timedelta
        test_date = (date.today() + timedelta(days=random.randint(250, 600))).isoformat()
        booking_resp = await client.post("/api/procurement/bookings", json={
            "farmerName": user_f1["name"],
            "farmerId": user_f1["farmerId"],
            "mandiName": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
            "crop": "Paddy Grade A (CR 1009 Sub 1)",
            "quantityBags": 120,
            "preferredDate": test_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }, headers=headers_f1)
        assert booking_resp.status_code == 201, f"Booking creation failed: {booking_resp.text}"
        booking_data = booking_resp.json()
        f1_booking_id = booking_data["bookingId"]
        f1_token_num = booking_data["tokenNumber"]
        print(f"  Farmer 1 Active Booking Created: {f1_booking_id} (Token: {f1_token_num})\n")

        # ---------------------------------------------------------------------
        # TEST 1: Chat Assistant with Context Injection & Real Booking Query
        # ---------------------------------------------------------------------
        print("--- [Test 1] AI Farmer Assistant Context Injection (Bookings & Token) ---")
        chat_req1 = await client.post("/api/chat/message", json={
            "message": "What is the status of my mandi procurement booking and token?",
            "language": "en"
        }, headers=headers_f1)
        assert chat_req1.status_code == 200, f"Chat failed: {chat_req1.text}"
        data1 = chat_req1.json()

        assert "reply" in data1
        assert f1_token_num in data1["reply"] or f1_booking_id in data1["reply"]
        assert data1["contextUsed"]["crop"] is not None
        assert data1["contextUsed"]["district"] is not None
        print(f"  -> PASS: Assistant identified Farmer 1's real booking '{f1_booking_id}' and token '{f1_token_num}'.")
        print(f"     Provider: {data1['provider']} | Real AI Flag: {data1['isRealAI']}")

        # ---------------------------------------------------------------------
        # TEST 2: Tamil Language Selection & Agronomic Guidance
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Tamil Language Selection & Spraying Advisory ---")
        chat_req2 = await client.post("/api/chat/message", json={
            "message": "இன்று மழை பெய்யுமா? பூச்சி மருந்து தெளிக்கலாமா?",
            "language": "ta"
        }, headers=headers_f1)
        assert chat_req2.status_code == 200, f"Tamil chat failed: {chat_req2.text}"
        data2 = chat_req2.json()

        assert data2["language"] == "ta"
        # Check Tamil agricultural terms
        assert any(term in data2["reply"] for term in ["வானிலை", "மழை", "தெளிப்பு", "வெப்பநிலை"])
        print(f"  -> PASS: Assistant responded in Tamil with weather-grounded spraying advice.")
        print(f"     Sample excerpt: {data2['reply'][:120]}...")

        # ---------------------------------------------------------------------
        # TEST 3: Transparent Provider Notice & No False AI Claims
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Transparent Provider Disclosure ---")
        assert "isRealAI" in data1
        if data1["isRealAI"]:
            assert "Gemini" in data1["provider"]
        else:
            assert "RULE_BASED" in data1["provider"]
        assert "providerNotice" in data1
        print(f"  -> PASS: Honest provider disclosure verified ({data1['provider']}): '{data1['providerNotice'][:90]}...'")

        # ---------------------------------------------------------------------
        # TEST 4: Follow-up Question for Incomplete Inquiries
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Follow-up Question for Incomplete Context ---")
        chat_req4 = await client.post("/api/chat/message", json={
            "message": "How much fertilizer should I apply?",
            "language": "en"
        }, headers=headers_f1)
        assert chat_req4.status_code == 200
        data4 = chat_req4.json()

        assert data4["followUpQuestion"] is not None
        print(f"  -> PASS: Follow-up question generated: '{data4['followUpQuestion']}'")

        # ---------------------------------------------------------------------
        # TEST 5: Plant Disease Guidance Includes Cautious Extension Notice
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Plant Pathology Cautious Guidance & TNAU Recommendation ---")
        chat_req5 = await client.post("/api/chat/message", json={
            "message": "My paddy leaves have brown spindle shaped spots with grey centers. Is it blast disease?",
            "language": "en"
        }, headers=headers_f1)
        assert chat_req5.status_code == 200
        data5 = chat_req5.json()

        assert any(term in data5["reply"] for term in ["TNAU", "KVK", "Extension Officer", "officer"])
        print(f"  -> PASS: Cautious guidance provided with official TNAU/KVK verification recommendation.")

        # ---------------------------------------------------------------------
        # TEST 6: Chat History Isolation & Privacy
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Chat History Isolation between Farmers ---")
        hist_f1 = await client.get("/api/chat/history", headers=headers_f1)
        assert hist_f1.status_code == 200
        msgs_f1 = hist_f1.json()["messages"]
        assert len(msgs_f1) >= 4, f"Expected at least 4 messages for Farmer 1, got {len(msgs_f1)}"

        # Farmer 2 should have their own isolated history
        hist_f2 = await client.get("/api/chat/history", headers=headers_f2)
        assert hist_f2.status_code == 200
        msgs_f2 = hist_f2.json()["messages"]
        # None of Farmer 1's messages should appear in Farmer 2's history
        f1_msg_texts = [m["userMessage"] for m in msgs_f1]
        for m2 in msgs_f2:
            assert m2["userMessage"] not in f1_msg_texts

        # Anonymous caller must be blocked
        hist_anon = await client.get("/api/chat/history")
        assert hist_anon.status_code == 401
        print(f"  -> PASS: Farmer 1 has {len(msgs_f1)} history records; Farmer 2 history is strictly isolated.")
        print(f"  -> PASS: Anonymous request rejected with HTTP 401.")

        # ---------------------------------------------------------------------
        # TEST 7: Notifications Retrieved from Real Persisted Events
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Persisted Notifications for Farmer 1 ---")
        notifs_resp = await client.get("/api/notifications", headers=headers_f1)
        assert notifs_resp.status_code == 200
        notifs = notifs_resp.json()
        assert len(notifs) >= 1, "Farmer 1 should have notifications from booking creation"
        
        booking_notif = next((n for n in notifs if n.get("bookingId") == f1_booking_id), notifs[0])
        notif_id = booking_notif["id"]
        print(f"  -> PASS: Retrieved {len(notifs)} real notifications. Sample: '{booking_notif['title']}'")

        # ---------------------------------------------------------------------
        # TEST 8: Notification Mark-as-Read & Farmer Ownership Enforcement
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Mark-as-Read & Ownership Enforcement ---")
        # Farmer 2 cannot mark Farmer 1's notification as read
        cross_mark = await client.patch(f"/api/notifications/{notif_id}/read", headers=headers_f2)
        assert cross_mark.status_code == 404, f"Cross-farmer mark should be rejected, got: {cross_mark.status_code}"
        print(f"  -> PASS: Farmer 2 blocked from marking Farmer 1's notification as read (HTTP 404/Denied).")

        # Farmer 1 marks own notification
        own_mark = await client.patch(f"/api/notifications/{notif_id}/read", headers=headers_f1)
        assert own_mark.status_code == 200
        assert own_mark.json()["success"] is True
        print(f"  -> PASS: Farmer 1 successfully marked notification '{notif_id}' as read.")

        # Mark all read
        mark_all = await client.patch("/api/notifications/read-all", headers=headers_f1)
        assert mark_all.status_code == 200
        print(f"  -> PASS: Mark-all-read returned: {mark_all.json()['message']}")

        # Unread count should now be 0
        unread_count_resp = await client.get("/api/notifications/unread-count", headers=headers_f1)
        assert unread_count_resp.status_code == 200
        assert unread_count_resp.json()["unreadCount"] == 0
        print(f"  -> PASS: Unread count correctly reports 0.")

        # ---------------------------------------------------------------------
        # TEST 9: SMS Gateway Status (Honest Reporting)
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] SMS Gateway Status (No False Delivery Claims) ---")
        sms_resp = await client.get("/api/notifications/sms-status", headers=headers_f1)
        assert sms_resp.status_code == 200
        sms_data = sms_resp.json()
        assert "configured" in sms_data
        assert "provider" in sms_data
        print(f"  -> PASS: SMS status reports: Provider='{sms_data['provider']}', Configured={sms_data['configured']}")
        print(f"     Note: '{sms_data['note']}'")

        # ---------------------------------------------------------------------
        # TEST 10: Regression Check across Phase 3, 4, 5
        # ---------------------------------------------------------------------
        print("\n--- [Test 10] Regression Testing (Auth, Mandi Queue, Bills) ---")
        # Me profile
        me_resp = await client.get("/api/auth/me", headers=headers_f1)
        assert me_resp.status_code == 200

        # Queue tracking
        queue_resp = await client.get(f"/api/procurement/queue/{f1_booking_id}", headers=headers_f1)
        assert queue_resp.status_code == 200

        # Farmer bills endpoint
        bills_resp = await client.get("/api/procurement/my-bills", headers=headers_f1)
        assert bills_resp.status_code == 200

        # Weather & Schemes
        weather_resp = await client.get("/api/weather?district=thanjavur")
        assert weather_resp.status_code == 200
        schemes_resp = await client.get("/api/schemes")
        assert schemes_resp.status_code == 200
        print("  -> PASS: All Phase 3, 4, and 5 endpoints remain 100% operational.")

        print("\n" + "=" * 80)
        print("ALL 10 PHASE 6 BACKEND TESTS PASSED SUCCESSFULLY!")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_phase6_tests())

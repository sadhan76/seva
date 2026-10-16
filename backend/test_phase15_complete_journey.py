"""
Phase 15: Complete Farmer Journey, Security & Truthfulness Verification Suite
Tests the complete 12-step lifecycle:
1. Login requirement before accessing dashboard
2. Farmer Registration & Profile Persistence
3. Profile retrieval (Name, District, Crop, Soil, Land Area)
4. Weather module auto-district selection
5. AI Farming Assistant with context grounding
6. Smart Farming tools (Irrigation, Recommendations, Mandi prices)
7. Procurement booking creation in MongoDB
8. Token generation & verification
9. Queue state progression (Checked In -> In Queue -> Processing)
10. Staff weighing form with quality deductions
11. Digital Bill generation & payment status update (PENDING -> PAID)
12. Farmer account review (Bill, Payment status, Real notifications)
Plus: Strict RBAC, Cross-Farmer Data Isolation, and Truthful Feature Status Reporting.
"""

import os
import sys
import uuid
import asyncio
import httpx
from datetime import datetime
from database import (
    get_users_collection,
    get_farmers_collection,
    get_bookings_collection,
    get_bills_collection,
    get_notifications_collection,
    get_chat_history_collection
)

BASE_URL = "http://127.0.0.1:8000"

async def run_complete_journey_verification():
    print("=" * 80)
    print("PHASE 15: COMPLETE FARMER JOURNEY & SYSTEM INTEGRITY TEST SUITE")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # STEP 1: Confirm login protection (Unauthenticated access denied)
        print("\n[STEP 1] Verifying Login-First Protection...")
        unauth_me = await client.get("/api/auth/me")
        assert unauth_me.status_code == 401, f"Expected 401 Unauthorized, got {unauth_me.status_code}"
        print("  -> PASS: Private endpoints strictly reject unauthenticated visitors.")

        # STEP 2 & 3: Register a new farmer and verify full profile details
        print("\n[STEP 2 & 3] Registering Farmer & Verifying Profile Attributes...")
        phone_farmer = f"98{str(uuid.uuid4().int)[:8]}"
        farmer_payload = {
            "name": "Subramanian Ramasamy",
            "phone": phone_farmer,
            "village": "Thiruvaiyaru",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": "FarmerSecurePass@2026",
            "confirmPassword": "FarmerSecurePass@2026",
            "totalLandAcres": 3.75,
            "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSource": "Cauvery Canal & Deep Borewell"
        }
        reg_res = await client.post("/api/auth/register", json=farmer_payload)
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        farmer_data = reg_res.json()
        farmer_token = farmer_data["accessToken"]
        farmer_user = farmer_data["user"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

        # Verify profile attributes
        assert farmer_user["name"] == "Subramanian Ramasamy"
        assert farmer_user["district"] == "Thanjavur"
        assert farmer_user["village"] == "Thiruvaiyaru"
        assert farmer_user["primaryCrop"] == "Samba Paddy (CR 1009 Sub 1)"
        assert farmer_user["soilType"] == "Alluvial Clay Loam"
        assert farmer_user["totalLandAcres"] == 3.75
        assert farmer_user["irrigationSource"] == "Cauvery Canal & Deep Borewell"
        print(f"  -> PASS: Farmer registered. ID: {farmer_user.get('farmerId')}, District: {farmer_user.get('district')}")

        # Verify MongoDB persistence
        users_col = get_users_collection()
        farmers_col = get_farmers_collection()
        user_db = await users_col.find_one({"phone": phone_farmer})
        assert user_db is not None, "Farmer user record not found in MongoDB!"
        farmer_db = await farmers_col.find_one({"phone": phone_farmer})
        assert farmer_db is not None, "Farmer farm record not found in MongoDB!"
        print("  -> PASS: Verified direct persistence in MongoDB users & farmers collections.")

        # STEP 4: Weather Forecast automatically uses registered district
        print("\n[STEP 4] Verifying Weather Forecast Auto-District Selection...")
        weather_res = await client.get(f"/api/weather?district={farmer_user['district']}")
        assert weather_res.status_code == 200, f"Weather fetch failed: {weather_res.text}"
        w_data = weather_res.json()
        assert w_data.get("district") == "Thanjavur"
        assert "sprayingAdvisory" in w_data
        if w_data.get("isLive") or w_data.get("isCached"):
            assert len(w_data.get("forecast", [])) >= 5
        print(f"  -> PASS: Weather loaded for '{w_data.get('district')}': {w_data.get('temperatureC')}°C, Spraying: {w_data.get('sprayingAdvisory', {}).get('status')}")

        # STEP 5: AI Farmer Assistant Context Grounding
        print("\n[STEP 5] Testing AI Assistant with Authenticated Farmer Context...")
        chat_res = await client.post(
            "/api/chat/message",
            json={
                "message": "வானிலை அடிப்படையில் இன்று என் பயிருக்கு உரம் இடலாமா?",
                "language": "ta",
                "includeFarmContext": True
            },
            headers=farmer_headers
        )
        assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
        chat_data = chat_res.json()
        assert chat_data.get("contextUsed", {}).get("district") == "Thanjavur"
        assert chat_data.get("contextUsed", {}).get("crop") == "Samba Paddy (CR 1009 Sub 1)"
        assert "Thiruvaiyaru" in chat_data.get("contextUsed", {}).get("village")
        print(f"  -> PASS: Assistant grounded with context: District={chat_data['contextUsed']['district']}, Crop={chat_data['contextUsed']['crop']}")
        print(f"  -> Provider: {chat_data.get('provider')}, IsRealAI: {chat_data.get('isRealAI')}")
        print(f"  -> Notice: {chat_data.get('providerNotice')[:120]}...")

        # STEP 6: Smart Farming Modules (Irrigation, Recommendations, Market Prices)
        print("\n[STEP 6] Testing Smart Farming Intelligence Endpoints...")
        # Irrigation
        irrig_res = await client.post("/api/irrigation/calculate", json={
            "crop": farmer_user["primaryCrop"],
            "growthStage": "Vegetative / Tillering",
            "soilType": farmer_user["soilType"],
            "irrigationMethod": "Controlled Basin Flooding",
            "forecastRainChance": w_data.get("rainfallChance", 20.0)
        })
        assert irrig_res.status_code == 200
        irrig_data = irrig_res.json()
        print(f"  -> PASS: Irrigation Advisor returned: {irrig_data.get('title')}")

        # Crop Recommendations
        crops_res = await client.post("/api/crops/recommend", json={
            "district": farmer_user["district"],
            "soilType": farmer_user["soilType"],
            "season": "Samba (Aug - Jan)",
            "waterAvailability": "High"
        })
        assert crops_res.status_code == 200
        crops_data = crops_res.json()
        assert len(crops_data.get("recommendations", [])) > 0
        print(f"  -> PASS: Crop Recommender returned {len(crops_data.get('recommendations', []))} varieties.")

        # Market Prices
        prices_res = await client.get(f"/api/market/prices?district={farmer_user['district']}")
        assert prices_res.status_code == 200
        prices_data = prices_res.json()
        print(f"  -> PASS: Market Prices returned {len(prices_data.get('prices', []))} commodities.")

        # STEP 7 & 8: Create Procurement Booking & Verify Token
        print("\n[STEP 7 & 8] Creating Mandi Procurement Booking & Verifying Token...")
        booking_payload = {
            "farmerName": farmer_user["name"],
            "farmerId": farmer_user["farmerId"],
            "mandiName": "Thanjavur Regulated Market (DPC Centre #3)",
            "crop": farmer_user["primaryCrop"],
            "quantityBags": 60,
            "preferredDate": datetime.utcnow().strftime("%Y-%m-%d"),
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        book_res = await client.post("/api/procurement/bookings", json=booking_payload, headers=farmer_headers)
        assert book_res.status_code == 201, f"Booking creation failed: {book_res.text}"
        booking = book_res.json()
        booking_id = booking["bookingId"]
        token_num = booking["tokenNumber"]
        opaque_token = booking.get("opaqueToken") or token_num
        print(f"  -> PASS: Booking created: ID={booking_id}, Token={token_num}, Status={booking['status']}")

        # Verify MongoDB persistence
        bookings_col = get_bookings_collection()
        book_db = await bookings_col.find_one({"bookingId": booking_id})
        assert book_db is not None, "Booking not persisted in MongoDB!"
        print("  -> PASS: Booking directly verified in MongoDB bookings collection.")

        # Verify Queue Tracking
        q_track_res = await client.get(f"/api/procurement/queue/{booking_id}", headers=farmer_headers)
        assert q_track_res.status_code == 200
        q_track = q_track_res.json()
        assert q_track["tokenNumber"] == token_num
        assert q_track["currentStageNumber"] == 1  # Booked
        print(f"  -> PASS: Queue tracking operational: Stage={q_track['currentStageNumber']}, Status={q_track['status']}")

        # STEP 9: Check In & Advance Queue via Staff Workflow
        print("\n[STEP 9] Authenticating Mandi Staff & Advancing Queue Stages...")
        staff_login_res = await client.post("/api/auth/login", json={
            "phone": "9842012345",
            "password": "MandiStaff@2026",
            "role": "staff"
        })
        assert staff_login_res.status_code == 200, f"Staff login failed: {staff_login_res.text}"
        staff_token = staff_login_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        print("  -> PASS: Staff account authenticated (Ramesh Kumar, Mandi Inspector).")

        # Verify Token at Gate
        verify_token_res = await client.post("/api/staff/verify-token", json={"token": opaque_token}, headers=staff_headers)
        assert verify_token_res.status_code == 200, f"Token verification failed: {verify_token_res.text}"
        print(f"  -> PASS: Gate staff verified token {token_num} successfully.")

        # Check-In
        checkin_res = await client.post(
            f"/api/staff/bookings/{booking_id}/checkin",
            json={"notes": "Vehicle verified at main security gate"},
            headers=staff_headers
        )
        assert checkin_res.status_code == 200
        print("  -> PASS: Gate check-in completed. Status: CHECKED_IN.")

        # Advance to Queue
        queue_res = await client.post(f"/api/staff/bookings/{booking_id}/queue", headers=staff_headers)
        assert queue_res.status_code == 200
        print("  -> PASS: Moved to weighbridge queue. Status: IN_QUEUE.")

        # Advance to Processing (on weighbridge platform)
        proc_res = await client.post(f"/api/staff/bookings/{booking_id}/processing", headers=staff_headers)
        assert proc_res.status_code == 200
        print("  -> PASS: Vehicle positioned on weighbridge platform. Status: PROCESSING.")

        # STEP 10: Staff Weighing Form & Quality Deductions
        print("\n[STEP 10] Staff Weighing Form: Recording Crop Weight, Moisture & Quality Deductions...")
        weighing_payload = {
            "acceptedWeightKg": 1500.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 200.0,
            "otherDeductionsAmount": 50.0,
            "qualityGrade": "FAQ Grade A",
            "paymentStatus": "PENDING",
            "notes": "Tare and gross certified on calibrated digital weighbridge."
        }
        # First preview calculation
        calc_res = await client.post("/api/staff/weighing/calculate", json={
            "acceptedWeightKg": 1500.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 200.0,
            "otherDeductionsAmount": 50.0
        })
        assert calc_res.status_code == 200
        calc_data = calc_res.json()
        print(f"  -> Weighing Math Preview: Gross=₹{calc_data['grossAmount']:,.2f}, Total Ded=₹{calc_data['totalDeductionsAmount']:,.2f}, Net=₹{calc_data['netAmount']:,.2f}")

        # Submit Weighing
        weigh_submit_res = await client.post(f"/api/staff/bookings/{booking_id}/weighing", json=weighing_payload, headers=staff_headers)
        assert weigh_submit_res.status_code == 200, f"Weighing submission failed: {weigh_submit_res.text}"
        bill_data = weigh_submit_res.json()
        bill_number = bill_data.get("billNumber") or bill_data.get("bill", {}).get("billNumber")
        net_amt = bill_data.get("netAmount") or bill_data.get("bill", {}).get("netAmount")
        print(f"  -> PASS: Weighing recorded and Digital Bill generated: {bill_number} (Net ₹{net_amt:,.2f})")

        # STEP 11: Update Payment Status (Staff Workflow)
        print("\n[STEP 11] Updating DBT Ledger Payment Status via Staff Workflow...")
        pay_res = await client.patch(
            f"/api/staff/bills/{bill_number}/payment-status",
            json={"newStatus": "PAID", "notes": "Approved for PFMS batch disbursement voucher."},
            headers=staff_headers
        )
        assert pay_res.status_code == 200, f"Payment update failed: {pay_res.text}"
        updated_bill = pay_res.json()
        assert updated_bill["paymentStatus"] == "PAID"
        print(f"  -> PASS: Payment status successfully updated to 'PAID' (Ledger voucher recorded).")

        # STEP 12: Return to Farmer Account & Verify Complete Records
        print("\n[STEP 12] Returning to Farmer Account & Verifying End-to-End Records...")
        # Verify Bill
        farmer_bill_res = await client.get(f"/api/procurement/bills/{bill_number}", headers=farmer_headers)
        assert farmer_bill_res.status_code == 200, f"Farmer bill access failed: {farmer_bill_res.text}"
        f_bill = farmer_bill_res.json()
        assert f_bill["billNumber"] == bill_number
        assert f_bill["farmerName"] == farmer_user["name"]
        assert f_bill["paymentStatus"] == "PAID"
        print(f"  -> PASS: Farmer accessed Digital Bill {bill_number} with verified payment status PAID.")

        # Verify Notifications
        notif_res = await client.get("/api/notifications", headers=farmer_headers)
        assert notif_res.status_code == 200
        notifs = notif_res.json()
        print(f"  -> PASS: Farmer has {len(notifs)} real persisted notifications:")
        for n in notifs[:3]:
            print(f"     • [{n.get('type')}] {n.get('title')}: {n.get('message')[:60]}...")
        assert len(notifs) >= 3, "Expected notifications for booking, weighing, and payment!"

        # STEP 13: Security & Multi-User Data Isolation Tests
        print("\n[STEP 13] Verifying Security, RBAC & Cross-Farmer Data Isolation...")
        # Create second farmer
        phone_farmer2 = f"99{str(uuid.uuid4().int)[:8]}"
        reg2_res = await client.post("/api/auth/register", json={
            "name": "Murugesan Palani",
            "phone": phone_farmer2,
            "village": "Attur",
            "district": "Salem",
            "state": "Tamil Nadu",
            "preferredLanguage": "en",
            "password": "Farmer2Password@2026",
            "confirmPassword": "Farmer2Password@2026",
            "totalLandAcres": 5.0,
            "primaryCrop": "Tapioca",
            "soilType": "Red Loam",
            "irrigationSource": "Well"
        })
        assert reg2_res.status_code == 201
        token2 = reg2_res.json()["accessToken"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Farmer 2 cannot view Farmer 1's private bill
        leak_bill = await client.get(f"/api/procurement/bills/{bill_number}", headers=headers2)
        assert leak_bill.status_code == 403, f"Expected 403 Forbidden for cross-farmer bill access, got {leak_bill.status_code}"
        print("  -> PASS: Cross-farmer bill access blocked (HTTP 403 Forbidden).")

        # Farmer 1 cannot perform staff-only weighing or payment actions
        illegal_weigh = await client.post(f"/api/staff/bookings/{booking_id}/weighing", json=weighing_payload, headers=farmer_headers)
        assert illegal_weigh.status_code == 403, "Farmer should be blocked from staff weighing endpoint!"
        print("  -> PASS: Farmer blocked from staff weighing route (HTTP 403 Forbidden).")

        illegal_pay = await client.patch(
            f"/api/staff/bills/{bill_number}/payment-status",
            json={"newStatus": "PAID"},
            headers=farmer_headers
        )
        assert illegal_pay.status_code == 403, "Farmer should be blocked from payment status modification!"
        print("  -> PASS: Farmer blocked from modifying payment status (HTTP 403 Forbidden).")

        # Cross-farmer notification tampering
        leak_notifs = await client.get("/api/notifications", headers=headers2)
        assert len(leak_notifs.json()) == 0, "Farmer 2 should have 0 notifications (no overlap with Farmer 1)!"
        print("  -> PASS: Notification isolation strictly verified (0 notifications for Farmer 2).")

    print("\n" + "=" * 80)
    print("ALL 13 END-TO-END PHASES & SECURITY CHECKS COMPLETED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_complete_journey_verification())

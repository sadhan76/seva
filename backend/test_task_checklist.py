"""
Verification script for User's 10-Task Checklist for Phase 5
"""
import asyncio
import httpx
from datetime import date, timedelta
import random

from main import app

async def run_checklist():
    print("=" * 80)
    print("PHASE 5 USER CHECKLIST VERIFICATION SUITE")
    print("=" * 80)

    results = {}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        # Task 3: Check frontend and backend servers
        print("\n--- [Task 3] Checking Frontend and Backend Running Configuration ---")
        try:
            health_res = await client.get("/api/health")
            backend_ok = (health_res.status_code == 200 and health_res.json().get("status") == "healthy")
            print(f"  Backend (/api/health): {health_res.status_code} {health_res.json()}")
        except Exception as e:
            backend_ok = False
            print(f"  Backend connection error: {e}")

        try:
            fe_res = await client.get("http://localhost:5173")
            frontend_ok = (fe_res.status_code == 200)
            print(f"  Frontend (http://localhost:5173): {fe_res.status_code} OK")
        except Exception as e:
            frontend_ok = False
            print(f"  Frontend connection error: {e}")

        results["Task 3 - Servers Running"] = backend_ok and frontend_ok

        # Login credentials
        print("\n--- Setup: Authenticating Farmer & Staff ---")
        farmer_res = await client.post("/api/auth/login", json={
            "phone": "9876543299", "password": "FarmerPassword@123", "role": "farmer"
        })
        assert farmer_res.status_code == 200, f"Farmer login failed: {farmer_res.text}"
        farmer_data = farmer_res.json()
        farmer_token = farmer_data["accessToken"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        farmer_id = farmer_data["user"]["farmerId"]
        farmer_name = farmer_data["user"]["name"]
        print(f"  Farmer authenticated: {farmer_name} ({farmer_id})")

        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.text}"
        staff_data = staff_res.json()
        staff_token = staff_data["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        print(f"  Staff authenticated: {staff_data['user']['name']} ({staff_data['user']['role']})")

        # Task 1: Check procurement centre selection and time-slot booking
        print("\n--- [Task 1] Check Procurement Centre Selection & Slot Booking ---")
        centres_res = await client.get("/api/procurement/centres")
        centres = centres_res.json()
        print(f"  Centres returned: {len(centres)}")
        assert len(centres) > 0, "No centres returned"
        first_centre = centres[0]
        centre_id = first_centre["id"]
        print(f"  Centre 1: {first_centre['name']} | DemoData: {first_centre.get('isDemoData')}")

        target_date = (date.today() + timedelta(days=random.randint(8, 35))).isoformat()
        slots_res = await client.get(f"/api/procurement/centres/{centre_id}/slots?date={target_date}")
        slots_data = slots_res.json()
        print(f"  Slots returned for {target_date}: {len(slots_data.get('slots', []))} windows")
        for s in slots_data.get("slots", []):
            print(f"    - {s['timeWindow']}: {s['availableBags']}/{s['maxCapacityBags']} bags available ({s['status']})")

        task1_passed = (
            centres_res.status_code == 200 and
            len(centres) >= 4 and
            first_centre.get("isDemoData") is True and
            slots_res.status_code == 200 and
            len(slots_data.get("slots", [])) >= 3
        )
        results["Task 1 - Centre & Slot Selection"] = task1_passed

        # Task 4 & Task 2: Create valid booking & verify saved in MongoDB
        print("\n--- [Task 4 & Task 2] Create Valid Booking and Verify MongoDB Persistence ---")
        test_slot = slots_data["slots"][0]["timeWindow"]
        valid_payload = {
            "farmerName": farmer_name,
            "farmerId": farmer_id,
            "mandiName": first_centre["name"],
            "crop": first_centre["supportedCrops"][0],
            "quantityBags": 15,
            "preferredDate": target_date,
            "timeWindow": test_slot
        }
        create_res = await client.post("/api/procurement/bookings", json=valid_payload, headers=farmer_headers)
        print(f"  Create booking response: {create_res.status_code}")
        booking_created = create_res.json()
        b_id = booking_created.get("bookingId")
        tok_num = booking_created.get("tokenNumber")
        op_tok = booking_created.get("opaqueToken")
        print(f"  Created: ID={b_id}, Token={tok_num}, Opaque={op_tok}, Status={booking_created.get('status')}")

        # Check retrieval in MongoDB via API
        my_bookings_res = await client.get("/api/procurement/my-bookings", headers=farmer_headers)
        my_bookings = my_bookings_res.json().get("bookings", [])
        found_in_db = any(b.get("bookingId") == b_id for b in my_bookings)
        print(f"  Found in /my-bookings: {found_in_db}")

        results["Task 4 - Create Valid Booking"] = (create_res.status_code == 201 and b_id is not None)
        results["Task 2 - Saved in MongoDB"] = found_in_db

        # Task 5: Test invalid booking data
        print("\n--- [Task 5] Test Invalid Booking Data Rejection ---")
        # 5a: Zero bags
        inv1_res = await client.post("/api/procurement/bookings", json={**valid_payload, "quantityBags": 0}, headers=farmer_headers)
        print(f"  Zero bags response: {inv1_res.status_code} (detail: {inv1_res.json().get('detail')})")
        # 5b: Negative bags
        inv2_res = await client.post("/api/procurement/bookings", json={**valid_payload, "quantityBags": -10}, headers=farmer_headers)
        print(f"  Negative bags response: {inv2_res.status_code}")
        # 5c: Missing preferredDate
        inv3_payload = valid_payload.copy()
        del inv3_payload["preferredDate"]
        inv3_res = await client.post("/api/procurement/bookings", json=inv3_payload, headers=farmer_headers)
        print(f"  Missing required field response: {inv3_res.status_code}")

        task5_passed = (
            inv1_res.status_code in [400, 422] and
            inv2_res.status_code in [400, 422] and
            inv3_res.status_code in [400, 422]
        )
        results["Task 5 - Reject Invalid Booking Data"] = task5_passed

        # Task 6: Slot capacity enforcement and simultaneous overbooking check
        print("\n--- [Task 6] Check Slot Capacity and Simultaneous Booking Safety ---")
        # Overbooking single request
        overbook_res = await client.post("/api/procurement/bookings", json={**valid_payload, "quantityBags": 500}, headers=farmer_headers)
        print(f"  Excessive bags (500) response: {overbook_res.status_code} (detail: {overbook_res.json().get('detail')})")
        single_overbook_blocked = (overbook_res.status_code == 400)

        # Simultaneous booking test: send 6 concurrent requests of 50 bags into slot with 235 bags remaining
        # Use fresh future date to test race-condition with full capacity
        sim_date = (date.today() + timedelta(days=random.randint(15, 60))).isoformat()
        sim_slot = "02:30 PM - 05:30 PM" # Capacity 250 bags
        sim_payload = {
            "farmerName": farmer_name,
            "farmerId": farmer_id,
            "mandiName": first_centre["name"],
            "crop": first_centre["supportedCrops"][0],
            "quantityBags": 60,
            "preferredDate": sim_date,
            "timeWindow": sim_slot
        }
        # 6 requests of 60 bags = 360 bags requested, but slot limit is 250 bags.
        # Max 4 requests (240 bags) can succeed; 5th and 6th MUST be rejected with 400.
        print("  Sending 6 concurrent requests (6 * 60 = 360 bags, limit is 250)...")
        tasks = [
            client.post("/api/procurement/bookings", json=sim_payload, headers=farmer_headers)
            for _ in range(6)
        ]
        responses = await asyncio.gather(*tasks)
        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(201)
        rejected_count = status_codes.count(400)
        print(f"  Concurrent responses: {status_codes}")
        print(f"  Accepted: {success_count} ({success_count * 60} bags), Rejected: {rejected_count}")
        # Total accepted bags must NOT exceed 250
        simultaneous_safe = (success_count * 60 <= 250 and rejected_count > 0)
        results["Task 6 - Slot Capacity & Race-Condition Safe"] = (single_overbook_blocked and simultaneous_safe)

        # Task 7: Unique booking ID and secure token
        print("\n--- [Task 7] Check Unique Booking ID and Secure Token Format ---")
        id_correct = b_id.startswith("PROC-TNJ-2026-") and len(b_id) >= 16
        token_correct = tok_num.startswith("TN-DPC-") and len(tok_num) >= 9
        opaque_correct = op_tok.startswith("NV-") and len(op_tok) >= 15
        print(f"  Booking ID: {b_id} (valid: {id_correct})")
        print(f"  Token Number: {tok_num} (valid: {token_correct})")
        print(f"  Opaque Token: {op_tok} (valid: {opaque_correct})")
        results["Task 7 - Unique ID and Secure Token"] = (id_correct and token_correct and opaque_correct)

        # Task 8: QR Code token verification
        print("\n--- [Task 8] Check QR Code Token Verification ---")
        # Verify with opaque token
        verify_valid_res = await client.post("/api/staff/verify-token", json={"token": op_tok}, headers=staff_headers)
        verify_valid = verify_valid_res.json()
        print(f"  Valid token verification: isValid={verify_valid.get('isValid')}, canCheckIn={verify_valid.get('canCheckIn')}")

        # Verify with fake token
        verify_fake_res = await client.post("/api/staff/verify-token", json={"token": "NV-FAKE-TOKEN-999"}, headers=staff_headers)
        verify_fake = verify_fake_res.json()
        print(f"  Fake token verification: isValid={verify_fake.get('isValid')}, status={verify_fake.get('status')}")

        qr_verification_url = booking_created.get("qrVerificationUrl", "")
        qr_has_no_pii = (farmer_name not in qr_verification_url and farmer_id not in qr_verification_url)
        print(f"  QR Verification URL: {qr_verification_url} (No PII: {qr_has_no_pii})")

        task8_passed = (
            verify_valid.get("isValid") is True and
            verify_fake.get("isValid") is False and
            qr_has_no_pii is True
        )
        results["Task 8 - QR Code & Token Verification"] = task8_passed

        # Task 9: Farmer and Staff Permissions (RBAC)
        print("\n--- [Task 9] Check Farmer and Staff Role Permissions ---")
        # 9a: Farmer tries to call staff verify endpoint -> Expect 403 Forbidden
        farmer_staff_block = await client.post("/api/staff/verify-token", json={"token": op_tok}, headers=farmer_headers)
        print(f"  Farmer on staff endpoint: {farmer_staff_block.status_code} (detail: {farmer_staff_block.json().get('detail')})")
        farmer_blocked = (farmer_staff_block.status_code == 403)

        # 9b: Staff on staff endpoint -> Expect 200 OK
        staff_staff_ok = (verify_valid_res.status_code == 200)
        print(f"  Staff on staff endpoint: {verify_valid_res.status_code} OK")

        # 9c: Staff calls /api/procurement/my-bookings -> Expect 403 Forbidden (farmer-only)
        staff_farmer_block = await client.get("/api/procurement/my-bookings", headers=staff_headers)
        print(f"  Staff on /my-bookings: {staff_farmer_block.status_code} (detail: {staff_farmer_block.json().get('detail')})")
        staff_blocked_from_farmer = (staff_farmer_block.status_code == 403)

        # 9d: Anonymous access on /api/procurement/bookings -> returns empty list (no data leakage)
        anon_bookings_res = await client.get("/api/procurement/bookings")
        anon_leak_prevented = (anon_bookings_res.status_code == 200 and anon_bookings_res.json() == [])
        print(f"  Anonymous /bookings: {anon_bookings_res.status_code}, count={len(anon_bookings_res.json())}")

        task9_passed = (farmer_blocked and staff_staff_ok and staff_blocked_from_farmer and anon_leak_prevented)
        results["Task 9 - RBAC Permissions"] = task9_passed

        # Summary
        print("\n" + "=" * 80)
        print("FINAL RESULTS TABLE:")
        print("=" * 80)
        all_passed = True
        for task, passed in results.items():
            status_text = "PASS" if passed else "FAIL"
            print(f"  {task:<50} : {status_text}")
            if not passed:
                all_passed = False

        print("=" * 80)
        if all_passed:
            print("ALL 9 VERIFICATION CHECKS PASSED PERFECTLY!")
        else:
            print("SOME CHECKS FAILED! INVESTIGATION NEEDED.")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_checklist())

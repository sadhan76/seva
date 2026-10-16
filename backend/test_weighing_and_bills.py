"""
Automated Test Suite for Phase 5 Part 3: Crop Weighing, Digital Bills, and Payment Tracking.
Tests all 8 requirements specified in TASK 7.
"""
import asyncio
import httpx
from datetime import date, timedelta
import random
import secrets

from main import app

async def run_weighing_and_bills_tests():
    print("=" * 80)
    print("PHASE 5: WEIGHING, DIGITAL BILLS & PAYMENT TRACKING - TASK 7 TEST SUITE")
    print("=" * 80)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # Setup: Log in Farmer 1, Farmer 2, and Mandi Staff
        # ---------------------------------------------------------------------
        print("\n[Setup] Authenticating Users...")

        # Farmer 1
        f1_res = await client.post("/api/auth/login", json={
            "phone": "9876543299", "password": "FarmerPassword@123", "role": "farmer"
        })
        assert f1_res.status_code == 200, f"Farmer 1 login failed: {f1_res.text}"
        f1_token = f1_res.json()["accessToken"]
        f1_headers = {"Authorization": f"Bearer {f1_token}"}
        f1_user = f1_res.json()["user"]
        print(f"  Farmer 1: {f1_user['name']} ({f1_user['farmerId']})")

        # Farmer 2 (ensure registered and login)
        f2_phone = "9876543211"
        f2_res = await client.post("/api/auth/login", json={
            "phone": f2_phone, "password": "FarmerPassword@123", "role": "farmer"
        })
        if f2_res.status_code != 200:
            reg_res = await client.post("/api/auth/register", json={
                "name": "Kandasamy V.",
                "phone": f2_phone,
                "village": "Thiruvaiyaru",
                "district": "Thanjavur",
                "password": "FarmerPassword@123",
                "confirmPassword": "FarmerPassword@123"
            })
            assert reg_res.status_code == 201
            f2_res = await client.post("/api/auth/login", json={
                "phone": f2_phone, "password": "FarmerPassword@123", "role": "farmer"
            })
        assert f2_res.status_code == 200
        f2_token = f2_res.json()["accessToken"]
        f2_headers = {"Authorization": f"Bearer {f2_token}"}
        f2_user = f2_res.json()["user"]
        print(f"  Farmer 2: {f2_user['name']} ({f2_user['farmerId']})")

        # Staff User
        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200
        staff_token = staff_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        staff_user = staff_res.json()["user"]
        assigned_mandi = staff_user.get("mandiName") or "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)"
        print(f"  Staff: {staff_user['name']} (Assigned: {assigned_mandi})")

        # Pick unique isolated test date
        test_date = (date.today() + timedelta(days=random.randint(40, 200))).isoformat()

        # Create Booking for Farmer 1
        b_payload = {
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": assigned_mandi,
            "crop": "Paddy Grade A (Samba NL CR 1009)",
            "quantityBags": 20,
            "preferredDate": test_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        res_create = await client.post("/api/procurement/bookings", json=b_payload, headers=f1_headers)
        assert res_create.status_code == 201
        booking = res_create.json()
        bid = booking["bookingId"]
        print(f"\n  Created Booking: {bid} (Token: {booking['tokenNumber']})")

        # ---------------------------------------------------------------------
        # TEST 2: Invalid weights, prices, and deductions are rejected
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Invalid weights, prices, and deductions are rejected ---")
        # 2a. Gate check-in and queue progression
        await client.post(f"/api/staff/bookings/{bid}/checkin", json={"notes": "Arrived"}, headers=staff_headers)
        await client.post(f"/api/staff/bookings/{bid}/queue", headers=staff_headers)

        # 2b. Zero / Negative weight
        inv_w = await client.post(f"/api/staff/bookings/{bid}/weighing", json={
            "acceptedWeightKg": -50.0, "pricePerKg": 23.20
        }, headers=staff_headers)
        assert inv_w.status_code in [400, 422], f"Expected 400/422, got {inv_w.status_code}"
        print("  -> PASS: Negative weight rejected with 400/422")

        # 2c. Zero / Negative price
        inv_p = await client.post(f"/api/staff/bookings/{bid}/weighing", json={
            "acceptedWeightKg": 1000.0, "pricePerKg": -10.0
        }, headers=staff_headers)
        assert inv_p.status_code in [400, 422]
        print("  -> PASS: Negative price rejected with 400/422")

        # 2d. Negative deductions
        inv_d = await client.post(f"/api/staff/bookings/{bid}/weighing", json={
            "acceptedWeightKg": 1000.0, "pricePerKg": 23.20, "qualityDeductionsAmount": -500.0
        }, headers=staff_headers)
        assert inv_d.status_code in [400, 422]
        print("  -> PASS: Negative deduction rejected with 400/422")

        # 2e. Deductions exceed gross amount
        # Gross = 1000 * 23.20 = 23,200. Deductions = 25,000.
        exc_d = await client.post(f"/api/staff/bookings/{bid}/weighing", json={
            "acceptedWeightKg": 1000.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 25000.0
        }, headers=staff_headers)
        assert exc_d.status_code == 400
        print(f"  -> PASS: Deductions exceeding gross amount rejected: 400 ({exc_d.json()['detail']})")

        # ---------------------------------------------------------------------
        # TEST 3: Gross and Net amounts calculated correctly
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Preview Calculation & Decimal Precision ---")
        # Preview endpoint
        prev_res = await client.post("/api/staff/weighing/calculate", json={
            "acceptedWeightKg": 1500.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 348.0,
            "otherDeductionsAmount": 150.0
        })
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert prev_data["isValid"] is True
        # Gross = 1500 * 23.20 = 34,800.00
        assert prev_data["grossAmount"] == 34800.00
        # Deductions = 348.00 + 150.00 = 498.00
        assert prev_data["totalDeductionsAmount"] == 498.00
        # Net = 34,800.00 - 498.00 = 34,302.00
        assert prev_data["netAmount"] == 34302.00
        print(f"  -> PASS: Gross: ₹{prev_data['grossAmount']:,.2f}, Deductions: ₹{prev_data['totalDeductionsAmount']:,.2f}, Net: ₹{prev_data['netAmount']:,.2f}")

        # ---------------------------------------------------------------------
        # TEST 1 & TEST 4: Authorized staff can save valid weighing & bill created
        # ---------------------------------------------------------------------
        print("\n--- [Test 1 & Test 4] Authorized staff saves weighing record & creates Digital Bill ---")
        # Move booking to PROCESSING
        await client.post(f"/api/staff/bookings/{bid}/processing", headers=staff_headers)

        valid_weighing = {
            "acceptedWeightKg": 1500.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 348.0,
            "otherDeductionsAmount": 150.0,
            "qualityGrade": "FAQ Grade A (Standard)",
            "paymentStatus": "PENDING",
            "notes": "Electronic weighbridge slip #WB-991 verified"
        }
        weigh_res = await client.post(f"/api/staff/bookings/{bid}/weighing", json=valid_weighing, headers=staff_headers)
        assert weigh_res.status_code == 200, f"Weighing failed: {weigh_res.text}"
        saved_booking = weigh_res.json()
        assert saved_booking["status"] == "COMPLETED"
        assert saved_booking["stageNumber"] == 5

        bill_info = saved_booking.get("bill") or saved_booking.get("transaction")
        assert bill_info is not None, "Bill was not created!"
        bill_num = bill_info["billNumber"]
        assert bill_num.startswith("BILL-")
        assert bill_info["grossAmount"] == 34800.00
        assert bill_info["netAmount"] == 34302.00
        assert bill_info["paymentStatus"] == "PENDING"
        print(f"  -> PASS: Valid weighing record saved. Created Digital Bill: {bill_num}")
        print(f"     Gross: ₹{bill_info['grossAmount']:,.2f}, Net: ₹{bill_info['netAmount']:,.2f}, Status: {bill_info['paymentStatus']}")

        # Duplicate weighing rejection
        dup_res = await client.post(f"/api/staff/bookings/{bid}/weighing", json=valid_weighing, headers=staff_headers)
        assert dup_res.status_code == 400
        print(f"  -> PASS: Duplicate weighing rejected: 400 ({dup_res.json()['detail']})")

        # ---------------------------------------------------------------------
        # TEST 5: Farmer can access their own bill but not another farmer's bill
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Farmer access control on Digital Bills ---")
        # Farmer 1 views own bill
        f1_bill_res = await client.get(f"/api/procurement/bills/{bill_num}", headers=f1_headers)
        assert f1_bill_res.status_code == 200
        f1_bill = f1_bill_res.json()
        assert f1_bill["billNumber"] == bill_num
        assert f1_bill["farmerId"] == f1_user["farmerId"]
        assert f1_bill["netAmount"] == 34302.00
        print(f"  -> PASS: Farmer 1 accessed own bill {bill_num} successfully.")

        # Farmer 1 fetches from /my-bills
        my_bills_res = await client.get("/api/procurement/my-bills", headers=f1_headers)
        assert my_bills_res.status_code == 200
        my_bills = my_bills_res.json()["bills"]
        assert any(b["billNumber"] == bill_num for b in my_bills)
        print(f"  -> PASS: Farmer 1 /my-bills contains {len(my_bills)} bills.")

        # Farmer 2 tries to access Farmer 1's bill -> 403 Forbidden!
        f2_access = await client.get(f"/api/procurement/bills/{bill_num}", headers=f2_headers)
        assert f2_access.status_code == 403
        print(f"  -> PASS: Farmer 2 blocked with 403: {f2_access.json()['detail']}")

        # Anonymous caller -> 401 Unauthorized!
        anon_access = await client.get(f"/api/procurement/bills/{bill_num}")
        assert anon_access.status_code == 401
        print("  -> PASS: Anonymous access blocked with 401.")

        # ---------------------------------------------------------------------
        # TEST 6: Unauthorized users cannot edit weighing or payment records
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Unauthorized users cannot update payment records ---")
        # Farmer tries to update payment status -> 403
        f1_pay = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
            "newStatus": "PAID"
        }, headers=f1_headers)
        assert f1_pay.status_code == 403
        print("  -> PASS: Farmer blocked from updating payment status: 403")

        # Anonymous tries to update payment status -> 401
        anon_pay = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
            "newStatus": "PAID"
        })
        assert anon_pay.status_code == 401
        print("  -> PASS: Anonymous blocked from updating payment status: 401")

        # ---------------------------------------------------------------------
        # TEST 4 (cont.): Payment Status transitions & Audit History
        # ---------------------------------------------------------------------
        print("\n--- [Test 4 & 7] Payment Status lifecycle (PENDING -> PROCESSING -> PAID) ---")
        # 1. Staff transitions to PROCESSING
        p1 = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
            "newStatus": "PROCESSING",
            "notes": "Sent to PFMS DBT gateway for treasury authorization",
            "transactionReference": "PFMS-TNJ-2026-9021"
        }, headers=staff_headers)
        assert p1.status_code == 200
        assert p1.json()["paymentStatus"] == "PROCESSING"
        print("  -> PASS: Status updated to PROCESSING with PFMS ref.")

        # 2. Staff transitions to PAID
        p2 = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
            "newStatus": "PAID",
            "notes": "Direct Benefit Transfer credited to Canara Bank A/C ending 4410",
            "transactionReference": "UTR-SBIN-2026-8877123"
        }, headers=staff_headers)
        assert p2.status_code == 200
        bill_paid = p2.json()
        assert bill_paid["paymentStatus"] == "PAID"
        assert len(bill_paid["paymentHistory"]) >= 3
        print(f"  -> PASS: Status updated to PAID. History contains {len(bill_paid['paymentHistory'])} records.")

        # Invalid payment status rejection
        inv_status = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
            "newStatus": "REFUNDED"
        }, headers=staff_headers)
        assert inv_status.status_code in [400, 422]
        print("  -> PASS: Invalid payment status rejected.")

        # ---------------------------------------------------------------------
        # TEST 7: Payment status & audit history persist in MongoDB
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Persistence verification ---")
        re_query = await client.get(f"/api/procurement/bills/{bill_num}", headers=f1_headers)
        assert re_query.status_code == 200
        rq_data = re_query.json()
        assert rq_data["paymentStatus"] == "PAID"
        assert rq_data["grossAmount"] == 34800.00
        assert rq_data["netAmount"] == 34302.00
        assert len(rq_data["paymentHistory"]) >= 3
        assert len(rq_data["auditHistory"]) >= 1
        print(f"  -> PASS: Persisted record verified. Payment={rq_data['paymentStatus']}, AuditEvents={len(rq_data['auditHistory'])}")

        # ---------------------------------------------------------------------
        # TEST 8: Existing login, booking, and queue features continue working
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Regression: Existing features ---")
        assert (await client.get("/api/weather?district=thanjavur")).status_code == 200
        assert (await client.get("/api/auth/me", headers=f1_headers)).status_code == 200
        assert (await client.get("/api/procurement/centres")).status_code == 200
        q_check = await client.get(f"/api/procurement/queue/{bid}", headers=f1_headers)
        assert q_check.status_code == 200
        assert q_check.json()["status"] == "COMPLETED"
        print("  -> PASS: Weather, Auth/Me, Centres, and Queue Tracking APIs are 100% operational.")

        print("\n" + "=" * 80)
        print("ALL 8 WEIGHING, BILLING & PAYMENT TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_weighing_and_bills_tests())

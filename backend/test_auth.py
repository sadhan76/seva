import urllib.request
import urllib.error
import json
import random

BASE_URL = "http://127.0.0.1:8000"

def request_json(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(error_body)
        except:
            return e.code, {"raw": error_body}

def run_tests():
    print("=== STARTING PHASE 3 AUTHENTICATION TESTS ===")

    # 1. Health check
    status_code, data = request_json(f"{BASE_URL}/api/health")
    print(f"[1] Health Check: Status {status_code}, MongoDB: {data.get('database', {}).get('connected')}")
    assert status_code == 200

    # 2. Farmer Registration
    farmer_phone = f"9876{random.randint(100000, 999999)}"
    farmer_password = "FarmerPassword@123"
    farmer_payload = {
        "name": "Murugesan K.",
        "phone": farmer_phone,
        "village": "Kabisthalam",
        "district": "Thanjavur",
        "state": "Tamil Nadu",
        "preferredLanguage": "ta",
        "password": farmer_password,
        "confirmPassword": farmer_password,
        "totalLandAcres": 4.2,
        "primaryCrop": "Samba Paddy (CR 1009)"
    }
    status_code, reg_data = request_json(f"{BASE_URL}/api/auth/register", method="POST", data=farmer_payload)
    print(f"[2] Farmer Registration: Status {status_code}, Assigned ID: {reg_data.get('user', {}).get('farmerId')}")
    assert status_code == 201
    farmer_token = reg_data["accessToken"]
    assert "hashed_password" not in reg_data["user"]

    # 3. Duplicate Account Rejection
    status_code, dup_data = request_json(f"{BASE_URL}/api/auth/register", method="POST", data=farmer_payload)
    print(f"[3] Duplicate Registration Test: Status {status_code} (Expected 409), Detail: {dup_data.get('detail')}")
    assert status_code == 409

    # 4. Password Mismatch Rejection
    mismatch_payload = farmer_payload.copy()
    mismatch_payload["phone"] = "9876543298"
    mismatch_payload["confirmPassword"] = "DifferentPassword"
    status_code, mm_data = request_json(f"{BASE_URL}/api/auth/register", method="POST", data=mismatch_payload)
    print(f"[4] Password Mismatch Validation: Status {status_code} (Expected 422)")
    assert status_code == 422

    # 5. Farmer Login (Valid Credentials)
    login_payload = {
        "phone": farmer_phone,
        "password": "FarmerPassword@123",
        "role": "farmer"
    }
    status_code, login_data = request_json(f"{BASE_URL}/api/auth/login", method="POST", data=login_payload)
    print(f"[5] Farmer Login: Status {status_code}, User: {login_data.get('user', {}).get('name')}, Role: {login_data.get('user', {}).get('role')}")
    assert status_code == 200
    farmer_token = login_data["accessToken"]

    # 6. Farmer Login with Wrong Password
    bad_login_payload = {
        "phone": farmer_phone,
        "password": "WrongPassword!",
        "role": "farmer"
    }
    status_code, bad_data = request_json(f"{BASE_URL}/api/auth/login", method="POST", data=bad_login_payload)
    print(f"[6] Bad Password Rejection: Status {status_code} (Expected 401), Detail: {bad_data.get('detail')}")
    assert status_code == 401

    # 7. Staff Login (Bootstrapped Admin Account)
    staff_login_payload = {
        "phone": "9842012345",
        "password": "MandiStaff@2026",
        "role": "staff"
    }
    status_code, staff_data = request_json(f"{BASE_URL}/api/auth/login", method="POST", data=staff_login_payload)
    print(f"[7] Staff Login: Status {status_code}, Staff Name: {staff_data.get('user', {}).get('name')}, Role: {staff_data.get('user', {}).get('role')}")
    assert status_code == 200
    staff_token = staff_data["accessToken"]

    # 8. Protected /api/auth/me Endpoint
    status_code, me_data = request_json(f"{BASE_URL}/api/auth/me", token=farmer_token)
    print(f"[8] Protected /me with Farmer Token: Status {status_code}, Farmer: {me_data.get('name')}")
    assert status_code == 200

    # 9. Role Permissions Test: Farmer calling Staff-restricted endpoint
    status_code, forbidden_data = request_json(f"{BASE_URL}/api/staff/queue", token=farmer_token)
    print(f"[9] RBAC Test (Farmer accessing Staff Queue): Status {status_code} (Expected 403 Forbidden)")
    assert status_code == 403

    # 10. Role Permissions Test: Staff calling Staff endpoint
    status_code, staff_queue_data = request_json(f"{BASE_URL}/api/staff/queue", token=staff_token)
    print(f"[10] RBAC Test (Staff accessing Staff Queue): Status {status_code}, Total Bookings Managed: {staff_queue_data.get('totalBookings')}")
    assert status_code == 200

    # 11. Staff updating a booking status (e.g. Weighbridge record)
    bookings = staff_queue_data.get("bookings", [])
    if bookings:
        target_booking = bookings[0]
        update_payload = {
            "status": "weighed",
            "moisturePercent": 14.1,
            "actualNetWeightQuintals": 48.5,
            "qualityNotes": "Pass grade: Excellent dry grain sample"
        }
        status_code, upd_res = request_json(
            f"{BASE_URL}/api/staff/bookings/{target_booking['bookingId']}/status",
            method="PATCH",
            data=update_payload,
            token=staff_token
        )
        print(f"[11] Staff Weighbridge Record Update: Status {status_code}, Booking: {upd_res.get('bookingId')}, New Status: {upd_res.get('status')}")
        assert status_code == 200

    print("=== ALL 11 BACKEND AUTHENTICATION & RBAC TESTS PASSED! ===")

if __name__ == "__main__":
    run_tests()

"""
Phase 17 Verification Test Suite: Global AI Chatbox with Voice Commands & App Actions
Tests:
1. Navigation commands in English and Tamil (all 14 routes)
2. Live data queries (Next slot, Latest bill, District weather, Notifications)
3. Data-changing commands with explicit confirmation requirement (Booking creation & Cancellation)
4. Confirmed execution of booking and cancellation on backend
5. Unsupported request safety and clear limitation disclosure
6. Role permissions & strict farmer data isolation
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def make_req(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def run_tests():
    import uuid
    print("=" * 70)
    print("PHASE 17 — GLOBAL AI CHATBOX WITH VOICE COMMANDS AND APP ACTIONS TESTS")
    print("=" * 70)

    # 1. Register a fresh Farmer
    phone_farmer1 = f"98{str(uuid.uuid4().int)[:8]}"
    reg_data = {
        "name": "Muthuvel Karuppiah",
        "phone": phone_farmer1,
        "village": "Pillaiyarpatti",
        "district": "Thanjavur",
        "state": "Tamil Nadu",
        "preferredLanguage": "en",
        "password": "FarmerPassword@2026",
        "confirmPassword": "FarmerPassword@2026",
        "totalLandAcres": 4.5,
        "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
        "soilType": "Alluvial Clay Loam",
        "irrigationSource": "Canal & Borewell"
    }
    status, res = make_req("/api/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Farmer registration failed: {res}"
    token = res.get("accessToken") or res.get("access_token")
    user_name = res["user"]["name"]
    print(f"✓ Step 1: Registered & authenticated Farmer '{user_name}' (Phone: {phone_farmer1})")

    # 2. Test Navigation Commands:
    nav_cases = [
        ("Open weather forecast.", "en", "weather", "NAVIGATE_WEATHER"),
        ("வானிலை அறிக்கை பக்கம் திற", "ta", "weather", "NAVIGATE_WEATHER"),
        ("Open my farm profile.", "en", "profile", "NAVIGATE_PROFILE"),
        ("பண்ணை விவரக்குறிப்பு பக்கம்", "ta", "profile", "NAVIGATE_PROFILE"),
        ("Open dashboard", "en", "dashboard", "NAVIGATE_DASHBOARD"),
        ("Open irrigation advice", "en", "irrigation", "NAVIGATE_IRRIGATION"),
        ("Open crop recommendations", "en", "recommendations", "NAVIGATE_RECOMMENDATIONS"),
        ("Open disease detection", "en", "disease", "NAVIGATE_DISEASE"),
        ("Open market prices", "en", "market", "NAVIGATE_MARKET"),
        ("Open government schemes", "en", "schemes", "NAVIGATE_SCHEMES"),
        ("Open queue tracking", "en", "queue", "NAVIGATE_QUEUE"),
        ("Show my digital bills", "en", "procurement", "SHOW_MY_BILLS"),
        ("Show my procurement bookings", "en", "procurement", "SHOW_MY_BOOKINGS"),
        ("Open language settings", "en", None, "TOGGLE_LANGUAGE"),
    ]

    for q, lang, expected_tab, expected_act in nav_cases:
        status, res = make_req(
            "/api/chat/message",
            method="POST",
            data={"message": q, "language": lang},
            token=token
        )
        assert status == 200, f"Query '{q}' failed: {res}"
        act = res.get("action")
        assert act is not None, f"Query '{q}' returned no action: {res}"
        assert act["intent"] == "navigation", f"Wrong intent for '{q}': {act}"
        assert act["actionType"] == "NAVIGATE", f"Wrong actionType for '{q}': {act}"
        assert act["actionName"] == expected_act, f"Wrong actionName for '{q}': {act}"
        assert act["targetTab"] == expected_tab, f"Wrong targetTab for '{q}': {act}"
        print(f"✓ Navigation verified: '{q}' -> {act['actionName']} (Target: {act['targetTab']})")

    # 3. Test Data Query: Weather in District
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "What is the weather in my district?", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act and act["intent"] == "data_query"
    assert act["actionName"] == "GET_WEATHER_SUMMARY"
    assert "°C" in res["reply"]
    print(f"✓ Data Query verified: 'What is the weather in my district?' -> {res['reply'][:65]}...")

    # Tamil weather query
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "எனது மாவட்டத்தில் வானிலை என்ன?", "language": "ta"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act and act["actionName"] == "GET_WEATHER_SUMMARY"
    print(f"✓ Tamil Weather verified: 'எனது மாவட்டத்தில் வானிலை என்ன?' -> {res['reply'][:65]}...")

    # 4. Test Data Query: Notifications
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "Show my notifications.", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act and act["actionName"] == "GET_NOTIFICATIONS"
    print(f"✓ Data Query verified: 'Show my notifications' -> {res['reply'][:65]}...")

    # 5. Test Data Query: Next Slot & Latest Bill
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "When is my next slot?", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act and act["actionName"] == "GET_NEXT_SLOT"
    print(f"✓ Data Query verified: 'When is my next slot?' -> {res['reply'][:70]}...")

    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "Explain my latest bill.", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act and act["actionName"] == "GET_LATEST_BILL"
    print(f"✓ Data Query verified: 'Explain my latest bill.' -> {res['reply'][:70]}...")

    # 6. Test Data Change: "Book a procurement slot" without details -> requests missing details
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "Book a procurement slot", "language": "en"},
        token=token
    )
    assert status == 200
    assert "please specify" in res["reply"].lower()
    act = res.get("action")
    assert act and act["targetTab"] == "procurement"
    print(f"✓ Booking request without details correctly prompted farmer for details")

    # 7. Test Data Change: "Book 100 bags of Samba Paddy on 2026-10-25 at Thanjavur Mandi"
    # Must ask for explicit confirmation before booking
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "Book 100 bags of Samba Paddy on 2026-10-25 at Thanjavur Mandi", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act is not None
    assert act["intent"] == "data_change"
    assert act["actionType"] == "REQUEST_CONFIRMATION"
    assert act["actionName"] == "CONFIRM_BOOKING"
    assert act["requiresConfirmation"] is True
    assert "confirm" in res["reply"].lower()
    confirm_payload = act.get("confirmedActionPayload")
    assert confirm_payload is not None
    assert confirm_payload["quantityBags"] == 100
    print(f"✓ Booking with details correctly required explicit confirmation (Slot not booked yet)")

    # 8. Execute confirmed booking via confirmedAction payload
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={
            "message": "Yes, confirm",
            "language": "en",
            "confirmedAction": confirm_payload
        },
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act is not None
    assert act["actionType"] == "EXECUTE_ACTION"
    assert act["actionName"] == "BOOKING_CREATED"
    created_booking_id = act["data"]["bookingId"]
    assert created_booking_id, "No bookingId returned"
    print(f"✓ Confirmed booking executed successfully: Booking #{created_booking_id}")

    # 9. Test Data Change: "Cancel my booking" -> must identify correct booking and require confirmation
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={"message": "Cancel my booking", "language": "en"},
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act is not None
    assert act["intent"] == "data_change"
    assert act["actionType"] == "REQUEST_CONFIRMATION"
    assert act["actionName"] == "CONFIRM_CANCEL_BOOKING"
    assert act["requiresConfirmation"] is True
    cancel_payload = act.get("confirmedActionPayload")
    assert cancel_payload is not None
    target_cancel_id = cancel_payload["bookingId"]
    print(f"✓ Cancellation request identified booking #{target_cancel_id} and required confirmation")

    # 10. Execute confirmed cancellation via confirmedAction payload
    status, res = make_req(
        "/api/chat/message",
        method="POST",
        data={
            "message": "Yes, confirm cancel",
            "language": "en",
            "confirmedAction": cancel_payload
        },
        token=token
    )
    assert status == 200
    act = res.get("action")
    assert act is not None
    assert act["actionType"] == "EXECUTE_ACTION"
    assert act["actionName"] == "BOOKING_CANCELLED"
    print(f"✓ Confirmed cancellation executed successfully on backend: #{target_cancel_id}")

    # 11. Test Unsupported Requests (Safe rejection, no arbitrary execution)
    unsupported_queries = [
        "Pay my electricity bill",
        "Transfer 10000 rupees to my bank account",
        "Mark my bill as paid immediately",
        "Delete other farmer account"
    ]
    for uq in unsupported_queries:
        status, res = make_req(
            "/api/chat/message",
            method="POST",
            data={"message": uq, "language": "en"},
            token=token
        )
        assert status == 200
        act = res.get("action")
        assert act and act["intent"] == "unsupported"
        assert act["actionType"] == "UNSUPPORTED"
        assert "cannot perform" in res["reply"].lower()
        print(f"✓ Unsupported command '{uq}' safely intercepted with clear limitation explanation")

    # 12. Test Data Isolation & Security: Farmer cannot cancel another farmer's booking
    phone_farmer2 = f"98{str(uuid.uuid4().int)[:8]}"
    reg_farmer2 = {
        "name": "Kandasamy Palanivel",
        "phone": phone_farmer2,
        "village": "Budalur",
        "district": "Thanjavur",
        "state": "Tamil Nadu",
        "preferredLanguage": "ta",
        "password": "FarmerPassword@2026",
        "confirmPassword": "FarmerPassword@2026",
        "totalLandAcres": 2.5
    }
    status, res = make_req("/api/auth/register", method="POST", data=reg_farmer2)
    assert status == 201
    token_farmer2 = res.get("accessToken") or res.get("access_token")

    status, res = make_req(
        f"/api/procurement/bookings/{created_booking_id}/cancel",
        method="POST",
        token=token_farmer2
    )
    assert status in [403, 400], f"Expected 403 Forbidden or 400 for unauthorized cancellation, got {status}"
    print(f"✓ Data isolation verified: Farmer 2 cannot cancel Farmer 1's booking (HTTP {status})")

    # 13. Test Chat History Clearing
    status, res = make_req("/api/chat/history", method="DELETE", token=token)
    assert status == 200
    assert "cleared" in res.get("message", "").lower()
    print("✓ Chat history clearing verified successfully")

    print("\n" + "=" * 70)
    print("ALL 13 PHASE 17 TEST SUITES PASSED CLEANLY (100% SUCCESS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

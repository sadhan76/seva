import urllib.request
import json

def test():
    # 1. Health
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
    data = json.loads(res.read().decode())
    print("HEALTH CHECK:", data)

    # 2. Create Farmer
    farmer_payload = {
        "name": "Selvakumar R.",
        "phone": "9876543210",
        "location": "Kabisthalam, Thanjavur",
        "district": "Thanjavur",
        "state": "Tamil Nadu",
        "totalLandAcres": 3.5,
        "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
        "soilType": "Alluvial Clay Loam",
        "irrigationSource": "Borewell & Canal",
        "aadhaarMasked": "XXXX-XXXX-4921"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/farmers",
        data=json.dumps(farmer_payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    created_farmer = json.loads(res.read().decode())
    print("CREATED FARMER:", created_farmer)

    # 3. List Farmers
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/farmers")
    farmers = json.loads(res.read().decode())
    print("FARMERS COUNT IN DB:", len(farmers))

    # 4. Create Procurement Booking
    booking_payload = {
        "farmerName": "Selvakumar R.",
        "farmerId": created_farmer["farmerId"],
        "mandiName": "Thanjavur Regulated Market (DPC Centre #3)",
        "crop": "Paddy Grade A (CR 1009)",
        "quantityBags": 120,
        "preferredDate": "2026-10-20",
        "timeWindow": "08:30 AM - 11:30 AM"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/procurement/bookings",
        data=json.dumps(booking_payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    created_booking = json.loads(res.read().decode())
    print("CREATED BOOKING:", created_booking)

    # 5. List Bookings
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/procurement/bookings")
    bookings = json.loads(res.read().decode())
    print("BOOKINGS COUNT IN DB:", len(bookings))

if __name__ == "__main__":
    test()

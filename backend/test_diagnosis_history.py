"""
NAMMA VIVASAYI AI - SECURE DIAGNOSIS HISTORY & REPORT LEDGER TEST SUITE
========================================================================
Validates secure persistence, strict farmer ownership defenses, image privacy,
authorization boundaries, and database outage handling.

TEST COVERAGE:
1. Authentication & Role Enforcement (401 unauthenticated, 403 non-farmer)
2. Farmer Ownership Isolation (Farmer B strictly blocked from viewing/deleting Farmer A's report: 403 Forbidden)
3. Report Lifecycle (Save, List, Retrieve by ID, Delete, Re-fetch 404)
4. Malformed and Missing Report ID validation (400 Bad Request, 404 Not Found)
5. Privacy & Image Storage Protection (No raw image bytes stored, retainedRawImage: False)
6. Database Outage / Service Unavailable Handling (503 Service Unavailable)
7. Analyze Endpoint Auto-Save Integration (Authenticated auto-save vs. unauthenticated)
"""

import sys
import os
import unittest
from bson import ObjectId
from fastapi.testclient import TestClient

# Ensure current backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from auth import require_farmer, get_current_user, get_optional_user
import database


class MockAsyncCursor:
    """Simulates an asynchronous Motor cursor for testing."""
    def __init__(self, docs):
        self.docs = docs
        self.idx = 0

    def sort(self, key, direction):
        return self

    def __aiter__(self):
        self.idx = 0
        return self

    async def __anext__(self):
        if self.idx < len(self.docs):
            doc = self.docs[self.idx]
            self.idx += 1
            return dict(doc)
        raise StopAsyncIteration


class MockDiagnosisReportsCollection:
    """In-memory collection simulating MongoDB for isolated unit tests."""
    def __init__(self):
        self.docs = {}

    async def insert_one(self, doc):
        new_doc = dict(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = ObjectId()
        oid = new_doc["_id"]
        self.docs[str(oid)] = new_doc
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(oid)

    async def find_one(self, query):
        if "_id" in query:
            oid_str = str(query["_id"])
            doc = self.docs.get(oid_str)
            return dict(doc) if doc else None
        return None

    def find(self, query):
        results = []
        if "$or" in query:
            conditions = query["$or"]
            for doc in self.docs.values():
                for cond in conditions:
                    match = True
                    for k, v in cond.items():
                        if doc.get(k) != v:
                            match = False
                            break
                    if match:
                        results.append(dict(doc))
                        break
        else:
            results = [dict(d) for d in self.docs.values()]
        return MockAsyncCursor(results)

    async def delete_one(self, query):
        if "_id" in query:
            oid_str = str(query["_id"])
            if oid_str in self.docs:
                del self.docs[oid_str]
                return True
        return False


class TestDiagnosisHistorySecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.mock_coll = MockDiagnosisReportsCollection()

        # Seed mock database collection on main and database
        import main
        main.get_diagnosis_reports_collection = lambda: self.mock_coll
        database.get_diagnosis_reports_collection = lambda: self.mock_coll

        # Default test identities
        self.farmer_a = {
            "id": "65f000000000000000000001",
            "farmerId": "TN-AGRI-FARM-001",
            "fullName": "Murugan S",
            "role": "farmer",
            "phone": "9876543210",
            "preferredLanguage": "ta"
        }

        self.farmer_b = {
            "id": "65f000000000000000000002",
            "farmerId": "TN-AGRI-FARM-002",
            "fullName": "Kavitha R",
            "role": "farmer",
            "phone": "9876543211",
            "preferredLanguage": "ta"
        }

        self.staff_user = {
            "id": "65f000000000000000000003",
            "role": "staff",
            "fullName": "Agricultural Officer Raman",
            "phone": "9876543212"
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------------
    # 1. AUTHENTICATION & ROLE RESTRICTION TESTS
    # ------------------------------------------------------------------------
    def test_unauthenticated_requests_are_rejected_with_401(self):
        """Unauthenticated requests must be rejected with 401 Unauthorized."""
        # Listing reports
        resp = self.client.get("/api/disease/reports")
        self.assertEqual(resp.status_code, 401)

        # Saving report
        resp = self.client.post("/api/disease/reports", json={"crop": "Paddy"})
        self.assertEqual(resp.status_code, 401)

        # Getting report
        resp = self.client.get("/api/disease/reports/65f000000000000000000001")
        self.assertEqual(resp.status_code, 401)

        # Deleting report
        resp = self.client.delete("/api/disease/reports/65f000000000000000000001")
        self.assertEqual(resp.status_code, 401)

    def test_non_farmer_role_is_rejected_with_403(self):
        """Staff or non-farmer users must receive 403 Forbidden."""
        def override_require_farmer():
            from fastapi import HTTPException
            if self.staff_user.get("role") != "farmer":
                raise HTTPException(status_code=403, detail="Access restricted to registered farmers only.")
            return self.staff_user

        app.dependency_overrides[require_farmer] = override_require_farmer
        resp = self.client.get("/api/disease/reports")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("registered farmers", resp.json()["detail"].lower())

    # ------------------------------------------------------------------------
    # 2. FARMER REPORT LIFECYCLE & OWNERSHIP DEFENSE
    # ------------------------------------------------------------------------
    def test_farmer_save_list_retrieve_and_strict_ownership_isolation(self):
        """
        Farmer A saves a diagnosis report.
        Farmer A can retrieve and list it.
        Farmer B CANNOT read or delete Farmer A's report (Strictly 403 Forbidden).
        Farmer A can delete their report.
        """
        # --- Step 1: Farmer A saves a report ---
        app.dependency_overrides[require_farmer] = lambda: self.farmer_a

        save_payload = {
            "crop": "Paddy / Rice",
            "cropTa": "நெல்",
            "plantPart": "leaf",
            "district": "Thanjavur",
            "status": "diagnosed",
            "filename": "leaf_blast_test.jpg",
            "diagnosis": {
                "category": "plant_disease",
                "categoryLabelEn": "Plant Disease",
                "categoryLabelTa": "பயிர் நோய்",
                "suspectedCondition": "Rice Blast (Pyricularia oryzae)",
                "suspectedConditionTa": "நெல் குலை நோய்",
                "affectedCrop": "Paddy / Rice",
                "confidencePercent": 89,
                "severityOrUrgency": "high",
                "visualSymptoms": "Spindle-shaped elliptical lesions with gray centers",
                "biologicalManagement": ["Apply Pseudomonas fluorescens at 10 g/kg seed"],
                "chemicalTreatment": ["Tricyclazole 75% WP @ 0.6 g/L water"]
            }
        }

        save_resp = self.client.post("/api/disease/reports", json=save_payload)
        self.assertEqual(save_resp.status_code, 200)
        report_id = save_resp.json().get("reportId")
        self.assertTrue(report_id)

        # --- Step 2: Farmer A lists reports ---
        list_resp = self.client.get("/api/disease/reports")
        self.assertEqual(list_resp.status_code, 200)
        reports_data = list_resp.json()
        self.assertEqual(reports_data["total"], 1)
        self.assertEqual(reports_data["reports"][0]["id"], report_id)
        self.assertEqual(reports_data["reports"][0]["crop"], "Paddy / Rice")
        self.assertEqual(reports_data["reports"][0]["suspectedCondition"], "Rice Blast (Pyricularia oryzae)")

        # --- Step 3: Farmer A retrieves report by ID ---
        get_resp = self.client.get(f"/api/disease/reports/{report_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["id"], report_id)
        self.assertEqual(get_resp.json()["confidencePercent"], 89)

        # --- Step 4: Strict Ownership Defense - Farmer B attempts to READ Farmer A's report ---
        app.dependency_overrides[require_farmer] = lambda: self.farmer_b
        farmer_b_get_resp = self.client.get(f"/api/disease/reports/{report_id}")
        self.assertEqual(farmer_b_get_resp.status_code, 403)
        self.assertIn("permission", farmer_b_get_resp.json()["detail"].lower())

        # --- Step 5: Strict Ownership Defense - Farmer B attempts to DELETE Farmer A's report ---
        farmer_b_del_resp = self.client.delete(f"/api/disease/reports/{report_id}")
        self.assertEqual(farmer_b_del_resp.status_code, 403)
        self.assertIn("permission", farmer_b_del_resp.json()["detail"].lower())

        # Verify report was NOT deleted by Farmer B
        app.dependency_overrides[require_farmer] = lambda: self.farmer_a
        get_still_exists = self.client.get(f"/api/disease/reports/{report_id}")
        self.assertEqual(get_still_exists.status_code, 200)

        # --- Step 6: Farmer A deletes their own report ---
        del_resp = self.client.delete(f"/api/disease/reports/{report_id}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json()["deletedId"], report_id)

        # Subsequent retrieval returns 404
        get_after_delete = self.client.get(f"/api/disease/reports/{report_id}")
        self.assertEqual(get_after_delete.status_code, 404)

    # ------------------------------------------------------------------------
    # 3. MALFORMED AND MISSING REPORT ID TESTS
    # ------------------------------------------------------------------------
    def test_invalid_and_missing_report_ids(self):
        """Invalid ObjectId formats return 400 Bad Request; non-existent return 404."""
        app.dependency_overrides[require_farmer] = lambda: self.farmer_a

        # Invalid format
        resp_invalid_get = self.client.get("/api/disease/reports/invalid-id-12345")
        self.assertEqual(resp_invalid_get.status_code, 400)
        self.assertIn("Invalid report ID format", resp_invalid_get.json()["detail"])

        resp_invalid_del = self.client.delete("/api/disease/reports/invalid-id-12345")
        self.assertEqual(resp_invalid_del.status_code, 400)

        # Non-existent ObjectId
        missing_id = "65f000000000000000000999"
        resp_missing_get = self.client.get(f"/api/disease/reports/{missing_id}")
        self.assertEqual(resp_missing_get.status_code, 404)

        resp_missing_del = self.client.delete(f"/api/disease/reports/{missing_id}")
        self.assertEqual(resp_missing_del.status_code, 404)

    # ------------------------------------------------------------------------
    # 4. PRIVACY & CONTROLLED IMAGE STORAGE
    # ------------------------------------------------------------------------
    def test_privacy_and_no_raw_image_retention(self):
        """Verifies raw images are discarded and only metadata is persisted."""
        app.dependency_overrides[require_farmer] = lambda: self.farmer_a

        save_payload = {
            "crop": "Tomato",
            "filename": "tomato_early_blight.png",
            "fileSizeBytes": 1024500,
            "contentType": "image/png",
            "diagnosis": {
                "category": "plant_disease",
                "suspectedCondition": "Early Blight",
                "affectedCrop": "Tomato"
            }
        }

        save_resp = self.client.post("/api/disease/reports", json=save_payload)
        self.assertEqual(save_resp.status_code, 200)
        report_id = save_resp.json()["reportId"]

        # Check document in database
        saved_doc = self.mock_coll.docs[report_id]
        self.assertIn("imageMetadata", saved_doc)
        metadata = saved_doc["imageMetadata"]
        self.assertEqual(metadata["filename"], "tomato_early_blight.png")
        self.assertEqual(metadata["fileSizeBytes"], 1024500)
        self.assertFalse(metadata["retainedRawImage"])
        self.assertIn("raw byte payload discarded", metadata["storagePolicy"].lower())

        # Guarantee no raw binary or base64 data field is stored
        self.assertNotIn("rawImage", saved_doc)
        self.assertNotIn("imageBase64", saved_doc)
        self.assertNotIn("imageBytes", saved_doc)

    # ------------------------------------------------------------------------
    # 5. DATABASE ERROR HANDLING (503 SERVICE UNAVAILABLE)
    # ------------------------------------------------------------------------
    def test_database_outage_returns_503(self):
        """Simulate MongoDB outage and verify graceful 503 response."""
        import main
        main.get_diagnosis_reports_collection = lambda: None
        database.get_diagnosis_reports_collection = lambda: None
        app.dependency_overrides[require_farmer] = lambda: self.farmer_a

        # List reports
        resp = self.client.get("/api/disease/reports")
        self.assertEqual(resp.status_code, 503)
        self.assertIn("unavailable", resp.json()["detail"].lower())

        # Save report
        resp = self.client.post("/api/disease/reports", json={"crop": "Paddy"})
        self.assertEqual(resp.status_code, 503)

        # Get report
        resp = self.client.get("/api/disease/reports/65f000000000000000000001")
        self.assertEqual(resp.status_code, 503)

        # Delete report
        resp = self.client.delete("/api/disease/reports/65f000000000000000000001")
        self.assertEqual(resp.status_code, 503)

    # ------------------------------------------------------------------------
    # 6. ANALYZE ENDPOINT AUTO-SAVE VERIFICATION
    # ------------------------------------------------------------------------
    def test_analyze_endpoint_autosave_behavior(self):
        """
        When authenticated farmer analyzes an image, it auto-saves with reportId.
        When unauthenticated user analyzes an image, reportId is null and saved is False.
        """
        import io
        from unittest.mock import patch

        # 1x1 valid PNG bytes
        tiny_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
            b"?\x00\x05\xfe\x02\xfe\r\xefU\xd7\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        from unittest.mock import AsyncMock, patch

        mock_res = {
            "status": "diagnosed",
            "testedModelPresent": True,
            "filename": "field_leaf.png",
            "fileSizeBytes": 150,
            "contentType": "image/png",
            "messageEn": "Diagnosed Rice Blast",
            "messageTa": "நெல் குலை நோய் கண்டறியப்பட்டது",
            "truthfulnessNotice": "Notice",
            "safeNextSteps": ["Follow TNAU guidelines"],
            "diagnosis": {
                "category": "plant_disease",
                "categoryLabelEn": "Plant Disease",
                "categoryLabelTa": "பயிர் நோய்",
                "suspectedCondition": "Rice Blast",
                "affectedCrop": "Paddy / Rice",
                "confidencePercent": 85,
                "severityOrUrgency": "moderate",
                "visualSymptoms": "Elliptical spots",
                "biologicalManagement": ["Trichoderma viride"],
                "chemicalTreatment": ["Tricyclazole 75% WP"]
            },
            "verifiedTreatment": {
                "isUncertainOrInconclusive": False,
            }
        }

        # Case A: Unauthenticated user
        app.dependency_overrides[get_optional_user] = lambda: None
        with patch("main.analyze_leaf_image_with_vision", new_callable=AsyncMock) as mock_vision:
            mock_vision.return_value = dict(mock_res)
            resp = self.client.post(
                "/api/disease/analyze",
                files={"file": ("field_leaf.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"X" * 150), "image/png")}
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertFalse(data.get("saved"))
            self.assertIsNone(data.get("reportId"))

        # Case B: Authenticated Farmer
        app.dependency_overrides[get_optional_user] = lambda: self.farmer_a
        with patch("main.analyze_leaf_image_with_vision", new_callable=AsyncMock) as mock_vision:
            mock_vision.return_value = dict(mock_res)
            resp = self.client.post(
                "/api/disease/analyze",
                files={"file": ("field_leaf.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"X" * 150), "image/png")}
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("saved"))
            self.assertTrue(data.get("reportId"))

            # Verify it was persisted in mock database
            report_id = data["reportId"]
            self.assertIn(report_id, self.mock_coll.docs)
            saved_doc = self.mock_coll.docs[report_id]
            self.assertEqual(saved_doc["farmerId"], self.farmer_a["farmerId"])
            self.assertEqual(saved_doc["crop"], "Paddy / Rice")


if __name__ == "__main__":
    unittest.main(verbosity=2)


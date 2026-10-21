# AgriBharat (SEVA) — User Acceptance Testing (UAT) Checklist

**Test Date:** October 20, 2026  
**Auditor / Specialist:** QA, Product & Deployment Engineering  
**Environment:** Local Development (`http://127.0.0.1:5173` React SPA / `http://127.0.0.1:8000` FastAPI / MongoDB 6.0+)  
**Data Isolation:** All tests executed using isolated test accounts with fictional test fixtures. Zero production records were deleted or altered.

---

## 📊 Summary of UAT Results

| Test Area | Executed | Passed | Failed | Status |
| :--- | :---: | :---: | :---: | :---: |
| 1. Authentication & Role-Based Authorization | 6 | 6 | 0 | **PASSED** |
| 2. Farmer Booking, Quota & Slot Capacities | 8 | 8 | 0 | **PASSED** |
| 3. Staff Mandi Operations (Check-in, Inspection, Weighing, Bills) | 9 | 9 | 0 | **PASSED** |
| 4. Cross-Centre Staff Security Restrictions | 5 | 5 | 0 | **PASSED** |
| 5. Multi-Counter Queue Concurrency | 3 | 3 | 0 | **PASSED** |
| 6. Daily Procurement Audit Reporting | 4 | 4 | 0 | **PASSED** |
| 7. AI Plant Pathology & Agronomic Safety | 6 | 6 | 0 | **PASSED** |
| 8. Database Persistence & Restart Integrity | 3 | 3 | 0 | **PASSED** |
| **TOTAL** | **44** | **44** | **0** | **100% PASS** |

---

## 📝 Detailed Verification Matrix

### 1. Authentication & Role-Based Authorization
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-AUTH-01** | Farmer Registration with valid 10-digit mobile & password | Status 201; returns user profile, JWT, and assigns `role: "farmer"` | Status 201; returns generated `farmerId: "TN-AGRI-2026-XXXX"` and access token | **PASS** |
| **UAT-AUTH-02** | Farmer Login with correct credentials (`9876543299` / `FarmerPassword@123`) | Status 200; returns JWT bearer token and user object | Status 200; successfully authenticated as Murugesan K. | **PASS** |
| **UAT-AUTH-03** | Login with incorrect password | Status 401; descriptive error without leaking system details | Status 401; "Invalid phone number or password." | **PASS** |
| **UAT-AUTH-04** | Login with role mismatch (e.g. farmer credentials logging in under `role: "staff"`) | Status 401; rejected due to role mismatch | Status 401; "Invalid phone number or password." | **PASS** |
| **UAT-AUTH-05** | Staff Login (`9842012345` / `MandiStaff@2026`) | Status 200; returns staff token with assigned centre metadata | Status 200; authenticated as Ramesh Kumar (Procurement Inspector) | **PASS** |
| **UAT-AUTH-06** | Request with malformed or expired JWT token | Status 401; rejected by authentication dependency | Status 401; "Invalid authentication credentials" | **PASS** |

### 2. Farmer Booking, Quota & Slot Capacities
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-BOOK-01** | Booking creation with valid crop, harvest date & future slot | Status 201; booking generated with bookingId and token | Status 201; booking created (`PROC-TNJ-2026-XXXX`), token `TN-DPC-XXX`, status `BOOKED` | **PASS** |
| **UAT-BOOK-02** | Booking creation with past preferred date | Status 422; validation error rejecting past dates | Status 422; "Value error, Booking date cannot be in the past." | **PASS** |
| **UAT-BOOK-03** | Booking creation with missing or invalid harvest date (>30 days away) | Status 422; validation error enforcing harvest window | Status 422; rejected with harvest date boundary error | **PASS** |
| **UAT-BOOK-04** | Booking crop not supported at selected centre | Status 400; descriptive error listing supported varieties | Status 400; "Crop 'Cotton' is not supported at centre... Supported crops: Paddy Grade A..." | **PASS** |
| **UAT-BOOK-05** | Duplicate active booking for same farmer on same slot | Status 400; duplicate booking rejected | Status 400; "Duplicate booking disallowed: Farmer already has an active booking..." | **PASS** |
| **UAT-BOOK-06** | Exceeding per-slot farmer limit (110 bags > 100 bag limit) | Status 400; rejected with remaining slot allowance | Status 400; "Per-slot limit exceeded. Maximum allowed per slot: 100 bags..." | **PASS** |
| **UAT-BOOK-07** | Booking on a staff-closed slot window | Status 400; booking rejected indicating slot is closed | Status 400; "Requested slot window is currently CLOSED..." | **PASS** |
| **UAT-BOOK-08** | Farmer cancellation of unserved booking | Status 200; status updated to `CANCELLED`, quota restored | Status 200; cancellation successful, slot capacity and farmer quota cleanly restored | **PASS** |

### 3. Staff Mandi Operations (Check-in, Quality, Weighing, Bills & Payment)
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-OPS-01** | Gate Check-in for arriving vehicle | Status 200; transition from `BOOKED` $\rightarrow$ `CHECKED_IN` | Status 200; timestamp and gate notes logged | **PASS** |
| **UAT-OPS-02** | Premature weighment prior to quality check | Status 400; blocked until quality inspection is completed | Status 400; "Cannot record weighment... Physical quality inspection must be completed first" | **PASS** |
| **UAT-OPS-03** | Quality inspection with moisture >17% | Status 200; inspection recorded as `REJECTED` | Status 200; status set to `REJECTED` with reason "Moisture level (22.5%) exceeds mandated limit" | **PASS** |
| **UAT-OPS-04** | Valid quality inspection (Moisture 15.2%, Grade A FAQ) | Status 200; transition to `QUALITY_CHECKED` | Status 200; accepted bags recorded, ready for queue calling | **PASS** |
| **UAT-OPS-05** | Token called to Counter-1 | Status 200; assigned counter logged, queue moved to `PROCESSING` | Status 200; token called, Now Serving reflects counter call | **PASS** |
| **UAT-OPS-06** | Certified weighment & deduction calculation | Status 200; generates digital bill with exact math | Status 200; Digital Bill generated (`BILL-TNJ-2026-XXXXXX`); Gross: ₹24,500.00, Net: ₹24,300.00 | **PASS** |
| **UAT-OPS-07** | Duplicate weighment on already billed booking | Status 400; duplicate bill submission rejected | Status 400; "Booking already has a completed weighing record and bill. Duplicate billing is disallowed." | **PASS** |
| **UAT-OPS-08** | Payment status update: `PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID` | Status 200; status updated with treasury PFMS reference | Status 200; payment status updated, audit event history logged | **PASS** |
| **UAT-OPS-09** | Farmer access control on Digital Bills | Farmer can only view own bills; other farmers blocked | Status 200 for owner; Status 403 Forbidden for another farmer | **PASS** |

### 4. Cross-Centre Staff Security Restrictions
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-SEC-01** | Staff calling token outside assigned centre | Status 403 Forbidden; cross-centre operation blocked | Status 403; "Staff member is assigned to Pillaiyarpatti and cannot perform operations on MDU-MKT-03" | **PASS** |
| **UAT-SEC-02** | Staff viewing daily audit report of unassigned centre | Status 403 Forbidden; cross-centre report view blocked | Status 403; access denied | **PASS** |
| **UAT-SEC-03** | Staff closing a slot at an unassigned centre | Status 403 Forbidden; slot modification blocked | Status 403; access denied | **PASS** |
| **UAT-SEC-04** | Staff viewing slot closures of an unassigned centre | Status 403 Forbidden; query blocked | Status 403; access denied | **PASS** |
| **UAT-SEC-05** | Farmer attempting to access staff queue or management endpoints | Status 403 Forbidden; farmer role rejected | Status 403; "Access restricted to authorized procurement centre staff only." | **PASS** |

### 5. Multi-Counter Queue Concurrency
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-CONC-01** | Counter-1 and Counter-2 call next tokens simultaneously | Two distinct tokens assigned; zero double-booking | Counter-1 claimed Token A, Counter-2 claimed Token B independently | **PASS** |
| **UAT-CONC-02** | Two staff members simultaneously call the exact same token | One request succeeds (200), other fails safely (404/400) | Result: `[200, 404]`. Zero duplicate assignments | **PASS** |
| **UAT-CONC-03** | Concurrent booking submissions exceeding slot limit | Only allowed quantity accepted; remainder rejected | Result: `[201, 400]`. Slot limit never breached | **PASS** |

### 6. Daily Procurement Audit Reporting
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-REP-01** | Daily report total bags & quintals calculation | Sum of accepted weights matches persisted bills | Exact match: 1,000.0 kg (10.0 quintals) aggregated | **PASS** |
| **UAT-REP-02** | Daily report monetary disbursement totals | Sum of gross and net amounts matches bills | Exact match: Gross ₹24,500.00, Net ₹24,300.00 | **PASS** |
| **UAT-REP-03** | Dynamic update upon payment status changes | `amountPaid` updates dynamically when bills are paid | Report `amountPaid` increased from ₹0 to ₹24,300.00 upon DBT confirmation | **PASS** |
| **UAT-REP-04** | Breakdown by crop variety and counter throughput | Items grouped by crop name and counter ID | Verified non-empty crop breakdown and counter throughput | **PASS** |

### 7. AI Plant Pathology & Agronomic Safety
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-AI-01** | Upload valid leaf image (JPEG, <5MB) | Status 200; analysis returned or honest fallback | Status 200; returned structured advisory or honest TNAU fallback | **PASS** |
| **UAT-AI-02** | Upload non-image or corrupted file (text/plain) | Status 400 Bad Request; descriptive rejection | Status 400; "Unsupported file type 'text/plain'. Please upload a JPG, PNG, or WEBP image..." | **PASS** |
| **UAT-AI-03** | Upload image exceeding 5MB | Status 413 Payload Too Large; rejected | Status 413; "File size exceeds 5MB limit. Please upload a compressed image." | **PASS** |
| **UAT-AI-04** | Sub-pixel tiny image (<20x20 pixels) | Rejected with dimension error | Status 400; "Image dimensions are too small for visual pathology analysis." | **PASS** |
| **UAT-AI-05** | Inconclusive image classification | Non-fabrication: reports `inconclusive` rather than inventing a disease | Status: `inconclusive`. Truthfulness notice returned without hallucinating pests/diseases | **PASS** |
| **UAT-AI-06** | Abiotic disorder treatment safety | Strictly withhold chemical pesticides (`isApplicable: false`) | Verified: Chemical pesticides disabled; cultural/nutrient recommendations provided | **PASS** |

### 8. Database Persistence & Restart Integrity
| Test ID | Test Scenario | Expected Result | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **UAT-DB-01** | Startup database index creation | Indexes created idempotently without data loss | Verified 10 collections indexed (`init_database_indexes()`) with background build | **PASS** |
| **UAT-DB-02** | Record persistence across server restart | All users, bookings, bills, and centres remain intact | Health check confirmed full connectivity; persisted records queried cleanly | **PASS** |
| **UAT-DB-03** | Centre deactivation & reactivation | Deactivation blocks new bookings while preserving historical records | Deactivated centre rejected new bookings with clear notice; historical records preserved | **PASS** |

---

## 🏁 Conclusion
All **44 User Acceptance Testing scenarios** have executed and **PASSED** completely. The platform adheres to security, mathematical precision, role isolation, and agricultural safety standards.

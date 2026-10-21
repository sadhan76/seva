# Namma Vivasayi AI (நம்ம விவசாயி AI) — 5–7 Minute Demonstration Script

> **Notice:** All demonstration credentials, farmer records, and transaction IDs used in this walkthrough are **fictional demonstration fixtures** created for evaluation purposes. They do not represent real farmers, government approvals, or official state partnership endorsements.

---

## ⏱️ Demonstration Timeline Overview

| Section | Duration | Screen / Feature | Key Message |
| :--- | :--- | :--- | :--- |
| **Part 1** | 0:00 – 1:00 | Title & Architecture | Problem statement: Middlemen, queue delays, paper bills & crop diseases in Tamil Nadu. Solution: Unified AI Agronomy + Direct Mandi Procurement. |
| **Part 2** | 1:00 – 2:15 | Farmer Sign-In & Booking | Bilingual login (Tamil/English), personalized farmer profile (Thanjavur), live weather, and Direct Purchase Centre (DPC) slot booking with instant QR token. |
| **Part 2B** | 2:15 – 3:00 | Government Schemes & Livestock | Curated directory of 23 verified state & central schemes, Animals & Livestock filtering, official .gov.in URLs, and statutory disclaimers. |
| **Part 3** | 3:00 – 3:45 | AI Plant Health & Advisory | Leaf disease inspection, Gemini Vision integration, honest disclosure on non-leaf photos, zero chemical pesticide recommendations for abiotic stress, TNAU safety guidance. |
| **Part 4** | 3:45 – 5:00 | Staff Mandi Operations | DPC Staff gate check-in, moisture & physical quality grading, multi-counter queue calling, precision weighing, instant digital bill generation, and DBT payment lifecycle. |
| **Part 5** | 5:00 – 6:00 | Daily Reports & Management | Aggregated procurement audit reports (quintals, gross/net disbursements), emergency slot closures, and centre management. |
| **Part 6** | 6:00 – 7:00 | Security & Technology Stack | Role-based isolation, Bcrypt, JWT, dual rate-limiting, Web Speech API voice synthesis, and deployment readiness. |

---

## 🎬 Step-by-Step Presenter Script

### Part 1: Introduction & Problem Context (0:00 – 1:00)
* **Presenter Visual:** Open `http://localhost:5173` on the Sign In screen.
* **Talking Points:**
  > "Good morning. In Tamil Nadu, paddy and pulses farmers face two critical challenges every season:
  > 1. In the field, timely and accurate crop protection advice is difficult to access, leading to yield loss or excessive chemical pesticide usage.
  > 2. At the harvest stage, delivering produce to Direct Procurement Centres (DPCs) involves unorganized physical queues, non-transparent weighing, paper bills, and uncertainty regarding Direct Benefit Transfer (DBT) bank disbursements.
  >
  > Today we present **Namma Vivasayi AI (SEVA)** — a unified digital agronomic intelligence and direct procurement management platform designed specifically for Tamil Nadu farmers."

---

### Part 2: Farmer Experience & Smart Procurement Booking (1:00 – 2:30)
* **Presenter Visual:** 
  1. Click the Language Toggle to switch between **English** and **தமிழ் (Tamil)** to highlight accessibility.
  2. Select **Farmer** role. Enter demo credentials:
     - Phone: `9876543299`
     - Password: `FarmerPassword@123` (or click *Farmer (Murugesan)* in local dev fill).
  3. Click **Sign In**.
* **Talking Points:**
  > "Here, our farmer **Murugesan K.** logs in. The interface immediately greets him in his preferred language with localized data for his registered village in **Thanjavur**.
  > 
  > Notice the dashboard:
  > - Live microclimate weather retrieved from Open-Meteo for Thanjavur, with rainfall probability and spraying advisories.
  > - FAO-56 irrigation recommendations calculating soil-moisture deficit for Alternate Wetting & Drying (AWD).
  > 
  > Now let us book a mandi procurement slot. We navigate to **Procurement Booking**:
  > - We select **Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)**.
  > - We choose **Paddy Grade A (CR 1009 Sub-1)**, enter **25 bags** (approx. 10 quintals), set our harvest date, pick an open date, and choose the **08:30 AM – 11:30 AM** slot window.
  > 
  > When we submit, the platform verifies our quota and atomically reserves the slot capacity. In milliseconds, we receive an official booking ID `PROC-TNJ-2026-XXXX`, an opaque queue token `TN-DPC-XXX`, and a printable QR code for gate check-in."

---

### Part 2B: Government Welfare Schemes & Livestock Directory (2:15 – 3:00)
* **Presenter Visual:** Navigate to **Govt Schemes** in the sidebar.
  1. Show the category filter bar with the new **Animals & Livestock** (`கால்நடைகள் & வளர்ப்பு`) tab with the `PawPrint` icon.
  2. Click **Animals & Livestock** to filter schemes down to livestock initiatives.
  3. Type `goat` in the search bar to demonstrate real-time keyword filtering.
  4. Click **View Details** on *National Livestock Mission* or *Tamil Nadu Vetri Magalir Goat Scheme*.
  5. Point out the official department name, verified eligibility criteria, required documents checklist, source verification date (`2026-10-20`), and statutory disclaimer.
  6. Click **Official Portal** to show direct navigation to the official `.gov.in` portal.
* **Talking Points:**
  > "Farmers often struggle to find authentic government subsidies and welfare schemes amidst commercial blog aggregators and outdated notices.
  > 
  > In our **Government Schemes** module:
  > - We provide a curated, structured catalog of **23 verified Central and Tamil Nadu State schemes** across categories: *State*, *Central*, *Insurance*, *Irrigation*, *Machinery*, and our newly launched **Animals & Livestock** category.
  > - Livestock farmers can instantly find schemes for milch cattle, goat and sheep rearing, fodder seeds, and disease control.
  > - Every record links exclusively to verified government domains (`dahd.gov.in`, `tnlda.tn.gov.in`, `pmfby.gov.in`, `tnagrisnet.tn.gov.in`).
  > - Transparency is paramount: we display the source verification date and distinguish active online application portals from schemes requiring local veterinary or Grama Sabha committee selection.
  > - Crucially, we display a clear statutory disclaimer that final eligibility and approval remain solely with the responsible government departments."

---

### Part 3: AI Plant Health & Agronomic Advisory Safety (3:00 – 3:45)
* **Presenter Visual:** Navigate to **Plant Health** (Disease Detection) in the sidebar.
* **Talking Points:**
  > "In the field, plant health is vital. Let's inspect our AI Plant Pathology module.
  > 
  > Farmers can photograph an affected leaf and upload it for instant analysis. When configured with a live vision API key, multimodal vision models analyze the visual symptoms.
  > 
  > Crucially, our system enforces strict safety boundaries:
  > 1. **Non-Fabrication Policy:** If an image is unreadable, corrupted, or inconclusive, the AI does *not* hallucinate a disease. It truthfully reports status as *inconclusive* or *not configured*.
  > 2. **Pesticide Safety Guard:** If the issue is an abiotic disorder — like potassium deficiency or heat stress — the platform strictly forbids chemical pesticide recommendations and suggests soil nutrient correction.
  > 3. **Authoritative Extension Reference:** All guidance references verified Tamil Nadu Agricultural University (TNAU) protocols and provides direct contact to local Krishi Vigyan Kendras (KVK) and the Uzhavan Helpline (`1800-425-1661`)."

---

### Part 4: Mandi Staff Operations, Certified Weighing & Digital Bill (3:30 – 5:00)
* **Presenter Visual:** 
  1. Click user menu $\rightarrow$ **Logout**.
  2. Select **Staff** role. Enter credentials:
     - Phone: `9842012345`
     - Password: `MandiStaff@2026` (or click *Staff Inspector (Ramesh)* in local dev fill).
  3. Click **Sign In** to land on the **Staff Portal**.
* **Talking Points:**
  > "Now, let us switch to the perspective of **Ramesh Kumar**, Procurement Inspector at the Pillaiyarpatti DPC.
  > 
  > Notice the role-based security: Ramesh's permissions are strictly restricted to his assigned centre. If he attempts to access reports or tokens from a Madurai or Salem mandi, the API returns HTTP 403 Forbidden.
  > 
  > In the Staff Portal:
  > 1. **Gate Check-In:** When the farmer's vehicle arrives at the yard gate, staff scan the QR code or enter token `TN-DPC-XXX` to record arrival.
  > 2. **Quality Inspection:** The inspector tests moisture content on a certified meter. Here we record 15.2% (well within the 17% mandated maximum) and assign *Grade A FAQ*. Premature weighment before quality check is programmatically blocked.
  > 3. **Queue Calling:** Staff call the token to **Weighbridge Counter-1**. Live queue screens instantly display 'Now Serving'.
  > 4. **Certified Weighing & Deductions:** The weighbridge records gross weight (1,000 kg). MSP price is locked at ₹24.50/kg. Deductions for moisture allowance (₹200.00) are verified.
  > 5. **Instant Tamper-Proof Digital Bill:** Clicking 'Generate Digital Bill' creates bill `BILL-TNJ-2026-XXXXXX` with Gross ₹24,500.00 and Net ₹24,300.00. Duplicate billing is strictly rejected.
  > 6. **DBT Payment Tracking:** When the treasury dispatches funds, staff update payment status to `PROCESSING` and then `PAID` with the bank PFMS transaction reference."

---

### Part 5: Daily Audit Reports & Centre Management (5:00 – 6:00)
* **Presenter Visual:** Click on **Daily Reports** tab in the Staff Portal.
* **Talking Points:**
  > "At the end of each shift, procurement officers and district agricultural officers need verifiable reporting.
  > 
  > Our **Daily Procurement Audit Report** aggregates all persisted transactions in real time:
  > - Total bookings, completed count, and queue throughput.
  > - Exact accepted weight in kilograms and quintals.
  > - Total gross amount, net payable amount, amounts disbursed vs pending.
  > - Complete breakdowns by crop variety and individual weighbridge counters.
  > 
  > In the **Slot Management** tab, staff can immediately close a time window for emergency scale recalibration, preventing farmer overbooking, and cleanly reopen it once certified. Cancelled and no-show bookings automatically return quota back to farmers and slot capacity back to the centre."

---

### Part 6: Security, Multilingual Voice & Technical Summary (6:00 – 7:00)
* **Presenter Visual:** Open the Global Floating AI Assistant in the bottom right corner.
* **Talking Points:**
  > "Finally, let's review the technical and security foundation of Namma Vivasayi AI:
  > - **Voice Accessibility:** Farmers who prefer speaking over typing can use our Web Speech API integration in Tamil or English with automated secret scrubbing (passwords and tokens are never read aloud).
  > - **Security & Hardening:** Passwords hashed with Bcrypt (salt 12), stateless PyJWT authentication, dual-layer rate limiting (IP + phone) against credential stuffing, and dead-code elimination in Vite that strips all demo credentials from production bundles.
  > - **Data Integrity:** Fully indexed MongoDB database with atomic capacity checks, compound unique constraints, and zero floating-point arithmetic drift on monetary calculations.
  > 
  > The application has been verified through 59 automated test cases across 6 test suites with a 100% pass rate.
  > 
  > Thank you for your time. We welcome any questions regarding architecture, security, or deployment planning."

---

## 📋 Demonstration Reference Data (Fictional Test Fixtures)

| Entity | Field | Demonstration Value |
| :--- | :--- | :--- |
| **Farmer Account** | Full Name | Murugesan K. |
| | Phone Number | `9876543299` |
| | Password | `FarmerPassword@123` |
| | Village & District | Pillaiyarpatti, Thanjavur |
| | Landholding & Crop | 4.5 Acres, Paddy (CR 1009 Sub-1) |
| **Staff Account** | Full Name | Ramesh Kumar (Procurement Inspector) |
| | Phone Number | `9842012345` |
| | Password | `MandiStaff@2026` |
| | Assigned Mandi | Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti) |
| **Procurement Centre** | Centre Code | `TNJ-DPC-01` |
| | Address | Near Pillaiyarpatti Bus Stop, Vallam Road, Thanjavur — 613403 |
| | Capacity | 250 bags / 100 quintals per slot window |
| **Sample Delivery** | Crop | Paddy Grade A (CR 1009 Sub-1) |
| | Bags / Weight | 25 Bags / 1,000 kg (10.0 Quintals) |
| | Quality Grade | Grade A FAQ (Moisture: 15.2%) |
| | Pricing & Net | ₹24.50/kg • Gross: ₹24,500.00 • Net: ₹24,300.00 |
| | Payment Reference | `PFMS-TN-2026-908123` (Direct Benefit Transfer) |

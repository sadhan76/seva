# AgriBharat — Smart Farming Intelligence & Agricultural Marketplace
> **அக்ரிபாரத் (AgriBharat)** — ஸ்மார்ட் வேளாண் நுண்ணறிவு மற்றும் நேரடி வேளாண் சந்தை

Welcome to **AgriBharat**, a unified agronomic intelligence and direct agricultural marketplace and procurement platform. The platform pairs AI-driven farm advisory services with a direct mandi purchase centre (DPC) workflow, eliminating middlemen, reducing wait times at regulated market yards, providing transparent digital weighing, and tracking Direct Benefit Transfer (DBT) payments.

---

## 🌾 Platform Highlights & Feature Capabilities

### 1. Bilingual AI Farmer Chat Assistant & Tamil Voice Support
* **Multi-Turn Agricultural Advisory:** Delivers contextual advice on crop care, irrigation scheduling, weather warnings, soil types, market prices, and government schemes.
* **Bilingual Operation:** Supports both **English** and **Tamil (`தமிழ்`)** with dynamic language switching.
* **Grounded Farm Context:** Connects to the authenticated farmer's registered profile (crop, district, landholding, soil), live Open-Meteo microclimate weather, and live mandi procurement bookings.
* **Text-to-Speech (TTS):** Browser Web Speech API integration with **Listen**, **Play**, **Pause**, **Resume**, and **Stop** controls. Automatically strips markdown and scrubs security secrets (tokens, passwords) before speech synthesis.
* **Speech-to-Text (STT):** Microphone speech recognition in Tamil (`ta-IN`) and English (`en-IN`) with transcript review before sending, with keyboard typing fallback.
* **Transparent AI Mode:** Truthfully reports when running in **Rule-Based Agronomic Mode (Demo)** when no external LLM key is configured, and connects to Gemini when `GEMINI_API_KEY` is present.

### 2. Smart Farming Intelligence & Plant Health
* **Live Weather & Microclimate:** District-specific agricultural weather via Open-Meteo, featuring 5-day forecasts and spraying advisories.
* **FAO-56 Irrigation Engine:** Calculates crop-water demand, crop coefficient ($K_c$), and soil-moisture deficit for Alternate Wetting & Drying (AWD) water management.
* **Crop Variety Recommendations:** Agro-climatic variety suggestions tailored to Tamil Nadu districts, soil types, and seasonal monsoons.
* **Diagnostic Plant Pathology:** Upload interface for leaf disease inspection with verified TNAU Visual Symptom Reference Guide, strict non-fabrication on unreadable/inconclusive images, and zero chemical pesticide recommendations for abiotic/nutritional disorders.
* **Mandi Commodity Rates (data.gov.in Official Integration):** Real-time daily market arrival prices directly from the Ministry of Agriculture & Farmers Welfare (Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`).
  - **Zero Simulation:** Strictly genuine government records; no fabricated prices.
  - **Automated Background Refresh:** Configurable 15-minute background sync (`MANDI_REFRESH_INTERVAL_MINUTES=15`) with a distributed singleton lease lock in MongoDB (`scheduler_locks`).
  - **Frontend Auto-Refresh:** Automatically polls every 60 seconds with Page Visibility API integration (pauses when backgrounded, checks instantly upon focus).
  - **Smart Price-Change Alerts:** Configurable price surge, drop, new arrivals, and stale feed notifications with 24-hour deterministic deduplication and farmer crop/market preferences.
  - **Resilient Fault Tolerance:** Cache preserved 100% on API key failures (403), government portal downtime (500/503), timeouts, and empty responses, with seamless recovery once upstream recovers.
* **Agricultural & Livestock Welfare Schemes (Phase 9):** Curated directory of 23 officially verified Central and Tamil Nadu State welfare schemes (PM-KISAN, National Livestock Mission, Rashtriya Gokul Mission, LHDCP, TN Micro-Irrigation, TN Livestock Insurance, Free Milch Cows, Farm Ponds, SMAM) with official portal links, responsible departments, eligibility guidelines, statutory disclaimers, and interactive filtering across `All`, `State`, `Central`, `Insurance`, `Irrigation`, `Machinery`, and `Animals & Livestock`.

### 3. Smart Procurement Tracking, Weighing & Digital Bills
* **Direct Purchase Centre (DPC) Booking:** Select local regulated market yards, view real-time slot capacity, and generate unique booking IDs (`PROC-TNJ-2026-XXXX`) with opaque tokens (`TN-DPC-XXX`) and printable QR verification codes.
* **Gate Check-In & Live Queue Tracking:** Gate staff verify tokens and check in vehicles. Live queue status tracks the 5-stage procurement lifecycle:
  `BOOKED` $\rightarrow$ `CHECKED_IN` $\rightarrow$ `IN_QUEUE` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED`.
* **Certified Digital Weighing:** Staff record gross truck weight, tare weight, moisture content, and authorized deductions with real-time two-decimal math verification.
* **Cryptographic Digital Bills:** Generates tamper-proof Digital Bills (`BILL-TNJ-2026-XXXXXX`) detailing gross weight, MSP unit price, itemized deductions, net payable amount, and PFMS payment reference.
* **Direct Benefit Transfer (DBT) Payment Tracking:** Tracks payment lifecycle (`PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID`) with role-restricted staff update privileges.
* **Daily Procurement Audit Reports:** Real-time shift reporting summarizing total bags, accepted quintals, gross amounts, disbursements, pending payments, counter throughput, and crop variety breakdowns.
* **Emergency Slot Management:** Staff can close specific slot windows for weighbridge calibration or weather events and reopen them cleanly when operational.

### 4. In-App Notifications & Modular Alert Adapter
* **Real Persisted Notifications:** Automatically stores and streams critical events (booking confirmations, queue movement, weighing completion, bill generation, DBT disbursement).
* **Mark-as-Read & Unread Badges:** Supports individual mark-as-read, mark-all-read, and header badge counters.
* **Modular SMS Gateway Adapter:** Pluggable `SMSNotificationService` interface ready for Indian DLT-compliant SMS providers, reporting honest configuration status without claiming delivery when unconfigured.

### 5. Robust Security & Data Isolation
* **Role-Based Access Control (RBAC):** Strict separation between `farmer` and `staff` roles.
* **Cross-Centre Authorization Enforcement:** Staff accounts are strictly bound to their assigned Direct Procurement Centre. Cross-centre token calling, slot closures, and report views are blocked with HTTP 403 Forbidden.
* **Dual-Layer Rate Limiting:** Sliding-window rate limiting on login by Client IP and Phone number to defend against distributed credential stuffing.
* **Farmer Data Privacy:** Farmers cannot inspect or alter another farmer's booking records, queue tokens, digital bills, chat histories, or notifications.
* **Password Hashing:** Passwords encrypted using Bcrypt with salt factor 12. Stateless JWT bearer tokens expire automatically.
* **Bundle Security:** Vite `import.meta.env.DEV` stripping ensures demo buttons and passwords never leak into production JavaScript assets.

---

## 🛠️ Architecture & Technology Stack

```text
SEVA/
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/             # Login & Registration Modals & Pages
│   │   │   ├── common/           # Header, Sidebar, StateViews, DigitalBillModal
│   │   │   ├── dashboard/        # WelcomeHero, FarmCards, Weather, Procurement
│   │   │   └── views/            # Assistant, Disease, Procurement, Queue, StaffPortal, Notifications
│   │   ├── context/              # AuthContext (JWT/RBAC), LanguageContext (EN/TA)
│   │   ├── services/             # api.ts (Typed REST Client for FastAPI)
│   │   ├── utils/                # speech.ts (Web Speech API TTS/STT with security filters)
│   │   └── types/                # Core TypeScript Interfaces
│   └── package.json
│
├── backend/                      # Python FastAPI REST Backend
│   ├── main.py                   # FastAPI Application, CORS, Route Controllers
│   ├── auth.py                   # Bcrypt, JWT Signing/Decoding, RBAC Dependencies
│   ├── database.py               # Motor Asynchronous MongoDB Client & Automated Indexing
│   ├── models.py                 # Pydantic Schemas & Data Validation
│   ├── procurement.py            # Mandi Booking, Capacity Checking, Weighing & Bills
│   ├── smart_farming.py          # Weather, FAO-56 Irrigation, TNAU Pathology, Market Rates
│   ├── ai_assistant.py           # Grounded Agronomic Chat Engine & History Isolation
│   ├── notifications.py          # In-App Notifications Store & SMS Gateway Adapter
│   └── requirements.txt          # Python Dependencies
│
├── DEMO_SCRIPT.md                # 5-7 Minute Presenter Demonstration Walkthrough
├── DEPLOYMENT_GUIDE.md           # Production Deployment, MongoDB Replica Set & Operations Guide
├── UAT_CHECKLIST.md              # User Acceptance Testing Matrix (44/44 Scenarios Passed)
└── README.md                     # Project Master Documentation
```

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite | Fast, responsive, strictly-typed single-page application |
| **Styling** | Tailwind CSS | Light-green agricultural aesthetic (`emerald-700`, `emerald-50`) |
| **Voice** | Browser Web Speech API | Client-side Tamil/English Speech Synthesis & Speech Recognition |
| **Backend** | Python 3.10+, FastAPI | High-performance asynchronous REST API with auto-generated Swagger |
| **Database** | MongoDB 6.0+ (`motor`) | Non-blocking document persistence across 10 indexed collections |
| **Security** | Bcrypt & PyJWT (HS256) | Password hashing, JWT token generation, role verification |
| **AI Inference** | Google Gemini Vision | Multimodal crop health reasoning with TNAU offline fallback |

---

## 🚀 Step-by-Step Running Instructions

### Prerequisites
* **Node.js**: v18+ (Tested on Node v20/v24)
* **Python**: 3.10+ (Tested on Python 3.12/3.14)
* **MongoDB**: Community Server 6.0+ (Running on `localhost:27017`)

---

### Step 1: Start MongoDB
Ensure MongoDB is running locally as a service or via command line:
```powershell
# Windows
net start MongoDB
# Or if running manually:
mongod --dbpath "C:\data\db"
```

---

### Step 2: Start the FastAPI Backend
```powershell
# Navigate to backend directory
cd d:\SEVA\backend

# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (first time only)
pip install -r requirements.txt

# Start backend server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Health Check Endpoint:** `http://127.0.0.1:8000/api/health`

---

### Step 3: Start the React Frontend
```powershell
# Open a new terminal and navigate to frontend directory
cd d:\SEVA\frontend

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```
* **Frontend Application URL:** `http://127.0.0.1:5173`

---

## 🧪 Automated Test Execution & Verification Results

All tests run against isolated test accounts and test dates. Real farmer records are never modified.

```powershell
cd d:\SEVA\backend

# 1. Phase 5 End-to-End Verification Suite (8 Test Blocks)
.\venv\Scripts\python test_phase5_e2e_verification.py

# 2. Phase 4 Queue Enhancement & Audit Reporting Suite (10 Tests)
.\venv\Scripts\python test_phase4_queue_and_reporting.py

# 3. Phase 3 Core Procurement Workflow Suite (11 Tests)
.\venv\Scripts\python test_phase3_core_workflow.py

# 4. Phase 2A Critical Safety Verification Suite (6 Tests)
.\venv\Scripts\python test_phase2a_safety.py

# 5. Weighing, Digital Bills & Payment Tracking Suite (8 Tests)
.\venv\Scripts\python test_weighing_and_bills.py

# 6. Queue Tracking & Now-Serving Suite (9 Tests)
.\venv\Scripts\python test_queue_tracking.py

# 7. AI Plant Pathology & Treatment Service Safety Suite (7 Tests)
.\venv\Scripts\python verify_e2e_disease.py

# 8. Phase 7 Full End-to-End Integration & Security Suite (8 Tests)
.\venv\Scripts\python test_phase7_end_to_end_readiness.py

# 9. Phase 3 Smart Irrigation Notification System (11 Tests)
.\venv\Scripts\python test_phase3_irrigation_notifications.py

# 10. Data.gov.in Mandi Market Prices Integration Suite (10 Tests)
.\venv\Scripts\python test_market_prices_gov_api.py

# 11. Mandi Market Prices Automatic Updates & Scheduler Suite (7 Tests)
.\venv\Scripts\python test_market_prices_automatic_updates.py

# 12. Mandi Price Notifications & Preferences Suite (9 Tests)
.\venv\Scripts\python test_market_notifications.py

# 13. Market Mandi Prices Production Readiness & Fault Tolerance Suite (7 Tests)
.\venv\Scripts\python test_market_prices_production_readiness.py
```

### Verification Test Summary
| Test Suite | Total Tests | Passed | Failed | Result |
| :--- | :---: | :---: | :---: | :---: |
| Phase 5 E2E Verification | 8 | 8 | 0 | **100% PASS** |
| Phase 4 Queue & Reporting | 10 | 10 | 0 | **100% PASS** |
| Phase 3 Core Workflow | 11 | 11 | 0 | **100% PASS** |
| Phase 2A Safety Fixes | 6 | 6 | 0 | **100% PASS** |
| Weighing & Digital Bills | 8 | 8 | 0 | **100% PASS** |
| Queue Tracking | 9 | 9 | 0 | **100% PASS** |
| AI Pathology Safety | 7 | 7 | 0 | **100% PASS** |
| Phase 7 E2E Integration & Security | 8 | 8 | 0 | **100% PASS** |
| Phase 3 Smart Irrigation Notifications | 11 | 11 | 0 | **100% PASS** |
| Data.gov.in Mandi Prices Integration | 10 | 10 | 0 | **100% PASS** |
| Mandi Automatic Updates & Distributed Lock | 7 | 7 | 0 | **100% PASS** |
| Mandi Price Notifications & Preferences | 9 | 9 | 0 | **100% PASS** |
| Market Prices Production Fault-Tolerance | 7 | 7 | 0 | **100% PASS** |
| **TOTAL** | **111** | **111** | **0** | **100% PASS (111/111)** |

---

## 🔑 Fictional Demonstration Accounts & Isolated Demo Setup

> **Notice:** These accounts are pre-configured test fixtures for evaluation and demonstration. Real farmer records are never modified.

### 1. Fictional Demo Credentials
* **Farmer Demonstration Account:**
  - Name: **Murugesan K.**
  - Phone Number: `9876543299`
  - Password: `FarmerPassword@123`
  - Registered Location: Pillaiyarpatti, Thanjavur District (4.5 Acres, Samba Paddy)
* **Staff Demonstration Account:**
  - Name: **Ramesh Kumar (Procurement Inspector)**
  - Phone Number: `9842012345`
  - Password: `MandiStaff@2026`
  - Assigned DPC: Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)

### 2. Seeding an Isolated Demo Database
To run demonstrations in a completely isolated database without touching any other records:
```powershell
cd d:\SEVA\backend
# Seed fictional accounts and workflow records into namma_vivasayi_demo_db
.\venv\Scripts\python seed_demo_environment.py --db-name namma_vivasayi_demo_db
```
Then set in `backend/.env`:
```env
MONGODB_DB_NAME=namma_vivasayi_demo_db
```
Restart the backend to view the pre-seeded demo records.

### 3. Synchronizing Government Welfare Schemes Database (Phase 9)
The verified schemes dataset is stored in `backend/data/government_schemes.json` (23 officially verified schemes).
To synchronize or update MongoDB without affecting any user, farmer, booking, or bill records:
```powershell
cd d:\SEVA\backend
# Idempotently seed schemes into the active database:
.\venv\Scripts\python seed_government_schemes.py

# Or target the isolated demo database:
.\venv\Scripts\python seed_government_schemes.py --db namma_vivasayi_demo_db

# Run Phase 9 automated verification tests:
.\venv\Scripts\python test_phase9_government_schemes.py
```

---

## 📋 Comprehensive Deliverables & Guides

1. **[PHASE10_SOURCE_VERIFICATION_REPORT.md](file:///d:/SEVA/PHASE10_SOURCE_VERIFICATION_REPORT.md):** Independent source verification audit, per-scheme official evidence table, and demo polish report.
2. **[PHASE9_GOVERNMENT_SCHEMES_REPORT.md](file:///d:/SEVA/PHASE9_GOVERNMENT_SCHEMES_REPORT.md):** Verified government schemes database & Animals & Livestock category audit, official sources, and 100% test verification.
3. **[DEMO_SCRIPT.md](file:///d:/SEVA/DEMO_SCRIPT.md):** 5–7 minute presenter walkthrough script covering problem statement, farmer booking, AI pathology, staff weighing, digital bills, and daily audit reports.
3. **[PRESENTATION_OUTLINE.md](file:///d:/SEVA/PRESENTATION_OUTLINE.md):** Complete 10-slide presentation deck plan with key bullets, suggested visuals, and speaker talking points.
4. **[PILOT_READINESS.md](file:///d:/SEVA/PILOT_READINESS.md):** Controlled pilot prerequisites: consent, PII masking, staff training, support contacts, backup/restore, monitoring, AI fallback, and payment/SMS boundaries.
5. **[DEPLOYMENT_GUIDE.md](file:///d:/SEVA/DEPLOYMENT_GUIDE.md):** Production deployment architecture covering hosting options, MongoDB Atlas replica set setup, security controls, backup/restore runbook, AI quotas, cost breakdown, and deployment safeguards.
6. **[UAT_CHECKLIST.md](file:///d:/SEVA/UAT_CHECKLIST.md):** Comprehensive User Acceptance Testing verification matrix covering 44 test scenarios across 8 core functional areas with 100% pass rate.
7. **[TROUBLESHOOTING.md](file:///d:/SEVA/TROUBLESHOOTING.md):** One-page troubleshooting guide for common startup, database, authentication, AI API, and frontend issues.
8. **[FINAL_HANDOFF.md](file:///d:/SEVA/FINAL_HANDOFF.md):** Concise project status, evaluation checklist, demo sequence, and handoff documentation.

---

## ⚠️ Known Limitations & Future Deployment Prerequisites

1. **In-Memory Async Lock vs Distributed Locking:**
   - In-memory `asyncio.Lock` protects concurrent requests within a single Python process.
   - For multi-worker deployments (e.g. `uvicorn --workers 4`), database-level unique constraints (`bookingId`, `billNumber`, `closureId`) enforce integrity. For clustered multi-node scaling, distributed Redis locking (`aioredlock`) is recommended.
2. **Transactional SMS / WhatsApp Delivery:**
   - In the local development environment, notifications are recorded in MongoDB and surfaced in the in-app notification center.
   - For live carrier SMS delivery in India, registration with a DLT telecom portal (Entity, Header `TNDPC`, approved templates) is required before connecting CDAC Gov SMS or Twilio.
3. **Automated Bank Wire Transfers:**
   - The platform provides an administrative payment audit progression (`PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID`) with PFMS transaction references. Direct automated bank account transfers require a formal bilateral integration with the Public Financial Management System (PFMS) or NPCI DBT Bharat gateway.
4. **Frontend Bundle Splitting:**
   - The production JavaScript bundle is ~752 kB minified (~185 kB gzipped). While highly performant on broadband and 4G, implementing route-level code splitting (`React.lazy`) is recommended before low-bandwidth rural rollout.

---

## 📄 License & Attribution
* Built for **AgriBharat** Agricultural Platform Hackathon 2026.
* Agronomic knowledge and disease visual reference keys referenced from **Tamil Nadu Agricultural University (TNAU)** Agritech Portal.
* Meteorological data provided by **Open-Meteo**.

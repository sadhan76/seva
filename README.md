# Namma Vivasayi AI — AI-Powered Farming & Smart Procurement Platform
> **நம்ம விவசாயி AI** — உழவர்களுக்கான செயற்கை நுண்ணறிவு வேளாண்மை மற்றும் நேரடி கொள்முதல் தளம்

Welcome to **Namma Vivasayi AI**, a unified agronomic intelligence and direct agricultural procurement platform designed specifically for Tamil Nadu farmers. The platform pairs AI-driven farm advisory services with a direct mandi purchase centre (DPC) workflow, eliminating middlemen, reducing wait times at regulated market yards, providing transparent digital weighing, and tracking Direct Benefit Transfer (DBT) payments.

---

## 🌾 Platform Highlights & Feature Capabilities

### 1. Bilingual AI Farmer Chat Assistant & Tamil Voice Support
* **Multi-Turn Agricultural Advisory:** Delivers contextual advice on crop care, irrigation scheduling, weather warnings, soil types, market prices, and government schemes.
* **Bilingual Operation:** Supports both **English** and **Tamil (`தமிழ்`)** with language selection.
* **Grounded Farm Context:** Connects to the authenticated farmer's registered profile (crop, district, landholding, soil), live Open-Meteo microclimate weather, and live mandi procurement bookings.
* **Text-to-Speech (TTS):** Browser Web Speech API integration with **Listen**, **Play**, **Pause**, **Resume**, and **Stop** controls. Automatically strips markdown and scrubs security secrets (tokens, passwords) before speech synthesis.
* **Speech-to-Text (STT):** Microphone speech recognition in Tamil (`ta-IN`) and English (`en-IN`) with transcript review before sending, with keyboard typing fallback.
* **Transparent AI Mode:** Truthfully reports when running in **Rule-Based Agronomic Mode (Demo)** when no external LLM key is configured, and connects to Gemini when `GEMINI_API_KEY` is present.

### 2. Smart Farming Intelligence & Plant Health
* **Live Weather & Microclimate:** District-specific agricultural weather via Open-Meteo, featuring 5-day forecasts and spraying advisories.
* **FAO-56 Irrigation Engine:** Calculates crop-water demand, crop coefficient ($K_c$), and soil-moisture deficit for Alternate Wetting & Drying (AWD) water management.
* **Crop Variety Recommendations:** Agro-climatic variety suggestions tailored to Tamil Nadu districts, soil types, and seasonal monsoons.
* **Diagnostic Plant Pathology:** Upload interface for leaf disease inspection with verified TNAU Visual Symptom Reference Guide and honest disclosure when machine vision weights are not installed.
* **Mandi Commodity Rates:** Daily benchmark market rates for regulated market yards across Tamil Nadu.
* **Agricultural Welfare Schemes:** Verified directory of central and state welfare initiatives (PM-KISAN, TN Micro-Irrigation, Kalaignarin Scheme) with application links.

### 3. Smart Procurement Tracking, Weighing & Digital Bills
* **Direct Purchase Centre (DPC) Booking:** Select local regulated market yards, view real-time slot capacity, and generate unique booking IDs (`PROC-TNJ-2026-XXXX`) with opaque tokens (`TN-DPC-XXX`) and printable QR verification codes.
* **Gate Check-In & Live Queue Tracking:** Gate staff verify tokens and check in vehicles. Live queue status tracks the 5-stage procurement lifecycle:
  `BOOKED` $\rightarrow$ `CHECKED_IN` $\rightarrow$ `IN_QUEUE` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED`.
* **Certified Digital Weighing:** Staff record gross truck weight, tare weight, moisture content, and authorized deductions with real-time math verification.
* **Cryptographic Digital Bills:** Generates tamper-proof Digital Bills (`BILL-TNJ-2026-XXXXXX`) detailing gross weight, MSP unit price, itemized deductions, net payable amount, and PFMS payment reference.
* **Direct Benefit Transfer (DBT) Payment Tracking:** Tracks payment lifecycle (`PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID`) with role-restricted staff update privileges.

### 4. In-App Notifications & SMS Adapter
* **Real Persisted Notifications:** Automatically stores and streams critical events (booking confirmations, queue movement, weighing completion, bill generation, DBT disbursement).
* **Mark-as-Read & Unread Badges:** Supports individual mark-as-read, mark-all-read, and header badge counters.
* **Pluggable SMS Gateway:** Backend `SMSNotificationService` interface ready for SMS providers, reporting honest configuration status without claiming delivery when unconfigured.

### 5. Robust Security & Data Isolation
* **Role-Based Access Control (RBAC):** Strict separation between `farmer` and `staff` roles.
* **Privilege Escalation Defense:** Public registration endpoints force `role = "farmer"`. Staff accounts are bootstrapped through secure backend configuration.
* **Farmer Data Privacy:** Farmers cannot inspect or alter another farmer's booking records, queue tokens, digital bills, chat histories, or notifications.
* **Password Hashing:** Passwords encrypted using Bcrypt with salt factor 12. JWT bearer tokens expire automatically.

---

## 🛠️ Architecture & Technology Stack

```text
SEVA/
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/             # Login & Registration Modals
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
│   ├── database.py               # Motor Asynchronous MongoDB Client
│   ├── models.py                 # Pydantic Schemas & Data Validation
│   ├── procurement.py            # Mandi Booking, Capacity Checking, Weighing & Bills
│   ├── smart_farming.py          # Weather, FAO-56 Irrigation, TNAU Pathology, Market Rates
│   ├── ai_assistant.py           # Grounded Agronomic Chat Engine & History Isolation
│   ├── notifications.py          # In-App Notifications Store & SMS Gateway Adapter
│   └── requirements.txt          # Python Dependencies
│
└── README.md                     # Project Master Documentation
```

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite | Fast, responsive, strictly-typed single-page application |
| **Styling** | Tailwind CSS | Light-green agricultural aesthetic (`emerald-700`, `emerald-50`) |
| **Voice** | Browser Web Speech API | Client-side Tamil/English Speech Synthesis & Speech Recognition |
| **Backend** | Python 3.10+, FastAPI | High-performance asynchronous REST API with auto-generated Swagger |
| **Database** | MongoDB 6.0+ (`motor`) | Non-blocking document persistence across 6 collections |
| **Security** | Bcrypt & PyJWT (HS256) | Password hashing, JWT token generation, role verification |

---

## 🚀 Step-by-Step Windows Running Instructions

### Prerequisites
* **Node.js**: v18+ (Tested on Node v20/v24)
* **Python**: 3.10+ (Tested on Python 3.12/3.14)
* **MongoDB**: Community Server (Running on `localhost:27017`)

---

### Step 1: Start MongoDB
Ensure MongoDB is running locally as a Windows service or via command line:
```powershell
mongod --dbpath "C:\data\db"
```

---

### Step 2: Start the FastAPI Backend

1. Open PowerShell and navigate to `backend`:
   ```powershell
   cd d:\SEVA\backend
   ```

2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```

3. Start the FastAPI development server:
   ```powershell
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. Verify backend health and interactive Swagger docs:
   * **Health Check:** `http://127.0.0.1:8000/api/health`
   * **Interactive API Docs:** `http://127.0.0.1:8000/docs`

---

### Step 3: Start the React Frontend

1. Open a second PowerShell terminal and navigate to `frontend`:
   ```powershell
   cd d:\SEVA\frontend
   ```

2. Start the Vite development server:
   ```powershell
   npm run dev
   ```

3. Open your browser and access the application:
   👉 **`http://localhost:5173/`**

---

## 🔑 Pre-Configured Demonstration Accounts

| Role | Mobile Number | Password | Assigned Centre / Profile |
| :--- | :--- | :--- | :--- |
| **Farmer 1** | `9876543299` | `FarmerPassword@123` | Murugesan K. (Thanjavur, 3.5 Acres, Samba Paddy) |
| **Farmer 2** | `9876543211` | `FarmerPassword@123` | Kandasamy V. (Budalur, 2.0 Acres, Groundnut) |
| **Procurement Staff** | `9842012345` | `MandiStaff@2026` | Ramesh Kumar (Thanjavur Regulated Market DPC #3) |

> 💡 **Public Registration:** Anyone can register as a new farmer using the **Register** button. All public registrations are automatically assigned the `farmer` role.

---

## 🧪 Comprehensive Automated Test Suites

The codebase includes 5 automated test suites covering all system layers:

```powershell
cd d:\SEVA\backend

# 1. Full Phase 7 End-to-End Integration & Security Test Suite
.\venv\Scripts\python.exe test_phase7_end_to_end_readiness.py

# 2. Phase 6 AI Assistant, Voice Controls & Notifications Test Suite
.\venv\Scripts\python.exe test_phase6_ai_and_notifications.py

# 3. Phase 5 Weighing, Digital Bills & DBT Payment Tracking Test Suite
.\venv\Scripts\python.exe test_weighing_and_bills.py

# 4. Phase 5 Smart Procurement Queue Management Test Suite
.\venv\Scripts\python.exe test_queue_tracking.py

# 5. Phase 3 Authentication, Bcrypt Hashing & RBAC Test Suite
.\venv\Scripts\python.exe test_auth.py
```

### Frontend Build & Type Validation
```powershell
cd d:\SEVA\frontend
cmd.exe /c "npm run build"
```
* **Result:** `✓ built in 1.69s` (0 TypeScript errors, 0 compilation issues).

---

## 🔍 Honest Disclosures & Benchmark Data

In compliance with hackathon and platform integrity guidelines, simulated or demo modules are transparently declared:

| Feature | Operational Status | Data Source / Behavior | Requires External API Key? |
| :--- | :--- | :--- | :--- |
| **User Authentication & RBAC** | **100% Live** | MongoDB + Bcrypt + JWT | No |
| **Procurement Booking & Slots**| **100% Live** | Real-time capacity check in MongoDB | No |
| **Queue Management** | **100% Live** | 5-stage audit-logged state machine | No |
| **Weighing & Digital Billing** | **100% Live** | Decimal arithmetic ledger in MongoDB | No |
| **In-App Notifications** | **100% Live** | Real persisted MongoDB alerts | No |
| **Local Weather & Spraying** | **100% Live** | Open-Meteo Public Meteorological API | No |
| **AI Farmer Chat Assistant** | **Live Rule-Based** | Expert agronomic engine (Optional: Gemini) | Optional (`GEMINI_API_KEY`) |
| **Voice Support (TTS / STT)** | **100% Live** | Browser Web Speech API (`ta-IN`, `en-IN`) | No |
| **Market Mandi Prices** | **Benchmark Mode** | Agmarknet reference rates with demo notice | No |
| **Disease Vision Inference** | **Honest Notice** | Discloses unconfigured vision model; links TNAU guide | Optional (`PLANT_VISION_API_KEY`) |
| **SMS Gateway** | **Interface Ready**| Reports `UNCONFIGURED`; uses in-app delivery | Optional (Twilio/MSG91) |

---

## 🎭 Step-by-Step Hackathon Presentation Guide

For a 5-minute live judging demonstration, follow this recommended walkthrough:

1. **Farmer Authentication & Bilingual Interface (Minute 1):**
   * Log in as Farmer (`9876543299` / `FarmerPassword@123`).
   * Switch language to **தமிழ்** using the language toggle in the header. Show instant bilingual UI translation.
   * View the unified dashboard: farm profile, microclimate weather, spraying recommendation, and irrigation advice.

2. **Agronomic AI Assistant with Voice Controls (Minute 2):**
   * Open the **Farming Assistant** tab.
   * Highlight the grounded farm context strip showing the farmer's registered crop and district.
   * Ask: *"Can I spray pesticide on my paddy today?"*
   * Show the weather-grounded advisory citing rainfall probability.
   * Click **Listen (கேளுங்கள்)** to demonstrate Tamil text-to-speech with Play/Pause/Stop controls.
   * Click the **Microphone** button to show speech-to-text recognition in Tamil or English.

3. **Mandi Procurement Booking & Token Generation (Minute 3):**
   * Open the **Procurement Booking** tab.
   * Select *Thanjavur Regulated Market (DPC Centre #3)* and an available time window.
   * Submit a booking for 30 bags. Note the instant generation of unique booking ID `PROC-TNJ-2026-XXXX` and token `TN-DPC-XXX`.
   * Click **Track Live Queue** to show Stage 1 (`BOOKED`).

4. **Staff Weighbridge, Weighing & Digital Bill Creation (Minute 4):**
   * Log out and log in as Staff (`9842012345` / `MandiStaff@2026`).
   * Automatically navigate to the **Staff Portal**.
   * Perform Gate Check-In for the farmer's vehicle $\rightarrow$ Status moves to `CHECKED_IN`.
   * Assign to yard queue $\rightarrow$ `IN_QUEUE`. Move onto weighbridge $\rightarrow$ `PROCESSING`.
   * Open the Weighing form: enter 1500 kg, configure Grade A MSP price, and record deductions.
   * Click **Save Weighment & Generate Bill**. Show the generated Digital Bill modal with itemized net payable calculations.

5. **Farmer Payment Tracking & Notifications (Minute 5):**
   * As staff, update DBT Payment status from `PENDING` $\rightarrow$ `PROCESSING` (PFMS reference) $\rightarrow$ `PAID`.
   * Log back in as Farmer (`9876543299`).
   * Open the **Notifications** page to show all real-time persisted alerts (booking confirmation, queue entry, weighing completion, and DBT disbursement).
   * Open **My Procurement Bills** and click **View & Print** to display the official farmer digital voucher.

---

## 🌐 Production Deployment Guide (Vercel, Render & MongoDB Atlas)

Follow these step-by-step instructions to deploy **Namma Vivasayi AI** to production for hackathon showcase.

### 1. Database: MongoDB Atlas (Free Tier)
1. Sign up or log in at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas).
2. Create a free **M0 Shared Cluster** (e.g. AWS `ap-south-1` Mumbai region).
3. Under **Database Access**, create a user (e.g., `namma_admin`) with a secure password and `Read and write to any database` privileges.
4. Under **Network Access**, click **Add IP Address** and choose **Allow Access from Anywhere** (`0.0.0.0/0`) so hosted backends can connect.
5. In **Database Deployments**, click **Connect** $\rightarrow$ **Drivers (Python)**.
6. Copy the connection string (`mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority`).
7. Set `MONGODB_URI` in your backend environment variables.

### 2. Backend: Hosting on Render / Railway
1. Push your repository to GitHub.
2. In [render.com](https://render.com) or [railway.app](https://railway.app), create a new **Web Service** pointing to the `backend/` directory.
3. Configure the build settings:
   * **Runtime:** Python 3.10+
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (or use the provided `Procfile`)
4. Add the following **Environment Variables** in the provider dashboard:
   * `ENVIRONMENT`: `production`
   * `MONGODB_URI`: `mongodb+srv://<user>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority`
   * `MONGODB_DB_NAME`: `namma_vivasayi_db`
   * `SECRET_KEY`: Generate via `python -c "import secrets; print(secrets.token_hex(32))"`
   * `JWT_SECRET_KEY`: Generate via `python -c "import secrets; print(secrets.token_hex(32))"`
   * `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app`
   * `ALLOWED_ORIGIN_REGEX`: `^https:\/\/.*\.vercel\.app$`
   * `GEMINI_API_KEY`: Your Google AI Studio API key
   * `GEMINI_MODEL`: `gemini-2.5-flash`
5. Deploy and verify health check: `https://your-backend.onrender.com/api/health`.

### 3. Frontend: Hosting on Vercel
1. In [vercel.com](https://vercel.com), click **Add New** $\rightarrow$ **Project** and select your GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. In **Environment Variables**, add:
   * `VITE_API_URL`: `https://your-backend.onrender.com/api`
5. The included `frontend/vercel.json` automatically ensures client-side routing rewrites (`/*` $\rightarrow$ `/index.html`) without 404 errors on page reload.
6. Deploy and access your live application URL.

---

## 🤖 Google Gemini AI Setup & Quota Management

1. **Obtaining an API Key:**
   * Visit [Google AI Studio](https://aistudio.google.com/) and create a project API key.
   * Add to `backend/.env` as `GEMINI_API_KEY=<key>`.
2. **Quota Availability & Billing:**
   * **Free Tier:** Limited to 20 requests per day per project/model (`gemini-2.5-flash`).
   * **Usage & Rate Limits:** Monitor current consumption at [ai.dev/rate-limit](https://ai.dev/rate-limit).
   * **Enabling Pay-As-You-Go:** Link a Google Cloud Billing Account to your project in Google Cloud Console to lift the 20-request daily cap for high-traffic demonstrations.
3. **Built-in Circuit Breaker & Fallback:**
   * When Google Gemini returns `429 RESOURCE_EXHAUSTED`, the backend activates an automatic 180-second circuit breaker cooldown.
   * Requests during quota cooldown avoid redundant failing network requests and immediately serve the **TNAU Rule-Based Agronomic Engine**.
   * Responses transparently label the mode as `Fallback: TNAU Agronomic Engine` without masquerading as Gemini.

---

## 📄 License & Attribution
* Built for **Namma Vivasayi AI** Agricultural Platform Hackathon 2026.
* Agronomic knowledge and disease visual reference keys referenced from **Tamil Nadu Agricultural University (TNAU)** Agritech Portal.
* Meteorological data provided by **Open-Meteo**.

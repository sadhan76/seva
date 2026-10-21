# AgriBharat (SEVA) — One-Page Troubleshooting Guide

> **Quick Diagnostic Command:**  
> Run `curl http://127.0.0.1:8000/api/health` or `Invoke-RestMethod http://127.0.0.1:8000/api/health` to immediately inspect service health and MongoDB connectivity.

---

## 🛠️ Common Issues & Fast Resolutions

### 1. Application Startup & Port Collisions
* **Symptom:** `OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`.
  - **Cause:** A previous Uvicorn backend process is still running in the background.
  - **Resolution:** Identify and terminate the lingering process:
    ```powershell
    # Find process listening on port 8000
    netstat -ano | findstr :8000
    # Terminate process using PID (e.g. PID 12345)
    Stop-Process -Id <PID> -Force
    ```
* **Symptom:** Frontend port `5173` occupied (`Port 5173 is in use, trying another one...`).
  - **Resolution:** Explicitly bind Vite: `npm run dev -- --host 127.0.0.1 --port 5173`. If occupied, kill the node process using `Get-Process node | Stop-Process -Force`.

---

### 2. MongoDB Database Connection Issues
* **Symptom:** Backend logs `[Warning] Failed to initialize MongoDB client: ServerSelectionTimeoutError`. Health check returns `database.connected: false`.
  - **Cause:** Local MongoDB service is stopped, or invalid connection string in `.env`.
  - **Resolution:**
    ```powershell
    # Verify MongoDB service status
    Get-Service -Name MongoDB
    # Start MongoDB service
    Start-Service -Name MongoDB
    # Or start mongod manually
    mongod --dbpath "C:\data\db"
    ```
  - **Check `.env`:** Verify `MONGODB_URI=mongodb://localhost:27017` and `MONGODB_DB_NAME=namma_vivasayi_db` (or `namma_vivasayi_demo_db` for demo).

---

### 3. Authentication & Login Failures
* **Symptom:** Login returns `HTTP 401: Invalid phone number or password`.
  - **Check 1: Role Mismatch:** Logging in with farmer credentials while the "Staff" tab is selected will fail with 401. Ensure the correct role tab (Farmer vs Staff) is chosen.
  - **Check 2: Demo Credentials:** Use verified fictional test fixtures:
    - *Farmer:* Phone `9876543299` | Password `FarmerPassword@123`
    - *Staff:* Phone `9842012345` | Password `MandiStaff@2026`
  - **Check 3: Missing Demo Accounts in Clean DB:** If testing with a new database name, run:
    ```powershell
    python seed_demo_environment.py --db-name <your_db_name>
    ```

---

### 4. AI Plant Pathology & Gemini API Issues
* **Symptom:** AI diagnosis returns `status: not_configured` or `inconclusive`.
  - **Expected Behavior:** This is a **built-in safety safeguard**, not a bug. If `GEMINI_API_KEY` is omitted, exhausted, or returns 503 high demand, the platform cleanly falls back to the verified TNAU Visual Symptom Reference Guide without crashing or inventing a diagnosis.
  - **Check API Key:** In `backend/.env`, verify `GEMINI_API_KEY=<valid_key>` and `GEMINI_MODEL=gemini-2.5-flash`.
* **Symptom:** Upload rejected with `HTTP 400 Unsupported file type` or `HTTP 413 Payload Too Large`.
  - **Resolution:** Uploaded leaf images must be JPG, PNG, or WEBP, dimensions at least 20x20 pixels, and file size under 5MB.

---

### 5. Mandi Procurement Workflow Constraints
* **Symptom:** `HTTP 400: Slot capacity exceeded for [timeWindow] on [date]`.
  - **Cause:** The slot has reached its maximum limit (250 bags).
  - **Resolution:** Select an alternate time window or a different harvest date.
* **Symptom:** `HTTP 400: Cannot record weighment... Physical quality inspection must be completed first`.
  - **Cause:** Mandi workflow integrity safeguard: Produce must be inspected for moisture ($\le 17\%$) and graded (`Grade A FAQ`) before weighbridge entry. Complete Step 2 (Quality Inspection) before Step 3 (Weighing).
* **Symptom:** `HTTP 403: Staff member is assigned to Pillaiyarpatti and cannot perform operations on MDU-MKT-03`.
  - **Cause:** Cross-centre RBAC security restriction: Staff can only check in, inspect, and weigh at their assigned centre.

---

### 6. Frontend Build & Asset Issues
* **Symptom:** `npm run build` fails with TypeScript errors.
  - **Resolution:** Run type-check in isolation: `npx tsc -b`. If node modules are out of sync:
    ```powershell
    cd d:\SEVA\frontend
    npm clean-install
    npm run build
    ```
* **Symptom:** Demo login autofill buttons do not appear.
  - **Expected Behavior:** In production builds (`npm run build`), demo buttons and default passwords are intentionally stripped via `import.meta.env.DEV` to protect secrets. They appear only in local development (`npm run dev`).

---

## ⚡ Quick Diagnostic One-Liners (PowerShell)

```powershell
# 1. Probe Backend Health
Invoke-RestMethod http://127.0.0.1:8000/api/health

# 2. Probe AI Assistant Mode
Invoke-RestMethod http://127.0.0.1:8000/api/chat/status

# 3. Test Farmer Login via CLI
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/login -Method Post -ContentType 'application/json' -Body '{"phone":"9876543299","password":"FarmerPassword@123","role":"farmer"}'

# 4. Check Frontend HTTP Status
(Invoke-WebRequest -Uri http://127.0.0.1:5173 -UseBasicParsing).StatusCode

# 5. Run Complete Regression Suite
cd d:\SEVA\backend; .\venv\Scripts\python test_phase5_e2e_verification.py
```

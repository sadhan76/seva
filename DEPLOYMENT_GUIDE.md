# AgriBharat (SEVA) — Production Deployment & Operations Guide

> **Notice:** This document serves as the official deployment and operations blueprint for **AgriBharat (SEVA)**. In compliance with Phase 6 instructions, no public infrastructure has been altered, no external services purchased, and all environment variables are presented with placeholder values only.

---

## 1. System Architecture Overview

```text
                                  +---------------------------------------+
                                  |         DNS / Cloudflare CDN          |
                                  |   (SSL/TLS Termination, DDoS Guard)   |
                                  +-------------------+-------------------+
                                                      |
                          +---------------------------+---------------------------+
                          |                                                       |
                          v                                                       v
        +-----------------------------------+                   +-----------------------------------+
        |      Frontend SPA (React 18)      |                   |       Backend API (FastAPI)       |
        |  Hosted: Cloudflare Pages/Vercel  |                   |   Hosted: Docker/AWS EC2/Render   |
        |  Static HTML5/JS/Tailwind Assets  |                   |   Uvicorn Worker Async Event Loop |
        +-----------------------------------+                   +-----------------+-----------------+
                                                                                  |
                                                        +-------------------------+-------------------------+
                                                        |                         |                         |
                                                        v                         v                         v
                                            +-----------------------+ +-----------------------+ +-----------------------+
                                            |  MongoDB Production   | |   Google Gemini AI    | |  Gov SMS / WhatsApp   |
                                            |  Replica Set (3-Node) | |  Multimodal Vision &  | |   Gateway (DLT Reg.)  |
                                            |  Atlas M10+ / Self-Host| |  Agronomic Reasoning | | (Transactional Alerts)|
                                            +-----------------------+ +-----------------------+ +-----------------------+
```

---

## 2. Hosting Options & Stack Recommendations

### Frontend (Single Page Application)
- **Recommended Providers:** Cloudflare Pages, Vercel, or AWS S3 + CloudFront.
- **Build Command:** `npm run build` (outputs to `dist/`).
- **Routing:** Must configure single-page application (SPA) rewrite rule directing all routes (`/*`) to `/index.html`.
- **Static Assets Caching:** Cache `dist/assets/*` with immutable headers (`Cache-Control: public, max-age=31536000, immutable`).

### Backend (REST API Service)
- **Recommended Providers:**
  - *Containerized:* AWS ECS (Fargate), Google Cloud Run, or Render Web Service.
  - *Virtual Machine:* AWS EC2 (`t4g.small` / `t4g.medium` with Ubuntu 24.04 LTS) or DigitalOcean Droplet.
- **Application Server:** `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers`
- **Reverse Proxy:** Nginx with HTTP/2 and Let's Encrypt SSL/TLS.
- **Process Supervisor:** Systemd service unit or Docker Compose restart policy `always`.

---

## 3. Production MongoDB Configuration

### Topologies Supported
1. **Managed Service (Recommended):** **MongoDB Atlas**
   - Tier: Dedicated M10 Cluster (10GB storage, 2GB RAM, 1000 IOPS).
   - Region: `ap-south-1` (Mumbai, India) to minimize network latency to Tamil Nadu users.
   - High Availability: 3-Node Primary-Secondary-Secondary (P-S-S) automated failover.
2. **Self-Hosted Enterprise:**
   - 3-Node Replica Set across independent availability zones.

### Mandatory Security Controls
- **Authentication:** Enforce SCRAM-SHA-256 with distinct service accounts for application workers and database administrators.
- **Network Isolation:** Atlas IP Access List restricted strictly to backend application egress IP addresses or VPC Peering / PrivateLink.
- **Encryption in Transit:** TLS 1.3 enforced (`tls=true&retryWrites=true&w=majority`).
- **Encryption at Rest:** AES-256 storage engine encryption enabled.

### Connection String Template
```text
mongodb+srv://<db_username>:<db_password>@<cluster-endpoint>.mongodb.net/namma_vivasayi_db?retryWrites=true&w=majority&maxPoolSize=50&minPoolSize=10&serverSelectionTimeoutMS=5000
```

### Automated Startup Indexes
The backend automatically executes `init_database_indexes()` at application startup in [database.py](file:///d:/SEVA/backend/database.py). The following indexes are created idempotently with `background=True`:

| Collection | Indexed Field(s) | Type / Constraints | Purpose |
| :--- | :--- | :--- | :--- |
| `users` | `phone` | Unique, Sparse | Fast farmer/staff auth lookup |
| `users` | `phone, role` | Compound | Fast role-based login validation |
| `farmers` | `phone` | Unique, Sparse | Farmer registry uniqueness |
| `farmers` | `farmerId` | Unique, Sparse | Fast identifier resolution |
| `procurement_bookings` | `bookingId` | Unique | Primary transaction key |
| `procurement_bookings` | `tokenNumber` | Standard Index | Quick yard gate lookup |
| `procurement_bookings` | `farmerId` | Standard Index | My-bookings farmer queries |
| `procurement_bookings` | `centreCode, slotDate, status` | Compound | Active slot capacity aggregation |
| `procurement_centres` | `centreCode` | Unique | Centre master identity |
| `procurement_bills` | `billNumber` | Unique | Audited billing identity |
| `procurement_bills` | `bookingId` | Unique | Prevents duplicate billing |
| `procurement_bills` | `centreCode, date, paymentStatus`| Compound | Fast daily audit reporting |
| `slot_closures` | `closureId` | Unique | Slot closure record identity |
| `slot_closures` | `centreCode, slotDate, timeWindow`| Compound | Fast slot status inquiry |
| `rate_limits` | `key, timestamp` | Compound | Fast rate limit sliding window |
| `rate_limits` | `timestamp` | TTL Index (expireAfterSeconds=3600) | Automatic cleanup of expired logs |
| `notifications` | `userId, createdAt` | Compound, Descending | Real-time notification inbox |
| `notifications` | `dedupKey` | Sparse Index | 24-hour alert deduplication |
| `notification_preferences` | `userId` | Unique, Sparse | Farmer notification settings isolation |
| `push_subscriptions` | `userId` | Standard Index | Browser Web Push subscription registry |
| `scheduler_locks` | `jobName` | Unique, Sparse | Distributed singleton scheduler lease lock |
| `irrigation_advisories_history` | `userId, isoTimestamp` | Compound, Descending | Agronomic advisory transition tracking |
| `government_schemes` | `id` | Unique, Sparse | Welfare scheme identity |
| `government_schemes` | `category` / `governmentLevel` | Standard Indexes | Fast scheme filtering |
| `market_prices_cache` | `recordId` | Unique, Sparse | Agmarknet arrival record deduplication |
| `market_prices_cache` | `district, commodity, arrival_date` | Compound | Filtered commodity queries |
| `market_prices_cache` | `cachedAt` | Standard Index | Cache freshness & TTL metrics |
| `market_prices_meta` | `metaKey` | Unique, Sparse | Source status & last-fetch metadata |

---

## 4. Environment Variables & Secret Management

> **CRITICAL RULE:** Never commit production `.env` files to source repositories. Inject secrets through container environment managers (AWS Secrets Manager, Doppler, or Render/Vercel Environment Variables).

```bash
# ==============================================================================
# PRODUCTION ENVIRONMENT VARIABLES (PLACEHOLDERS ONLY)
# ==============================================================================

# Application Runtime Mode
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# Database Persistence
MONGODB_URI=mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=namma_vivasayi_db

# CORS Allowed Origins (Comma-separated exact domains; NO wildcard '*')
ALLOWED_ORIGINS=https://nammavivasayi.tn.gov.in,https://app.nammavivasayi.in
ALLOWED_ORIGIN_REGEX=

# Cryptographic Keys (Generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=<generate_secure_random_64_character_hex_secret>
JWT_SECRET_KEY=<generate_separate_secure_random_64_character_hex_secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

# DPC Staff Bootstrap (Used on first system startup only)
STAFF_BOOTSTRAP_PHONE=9842012345
STAFF_BOOTSTRAP_PASSWORD=<strong_random_master_staff_password>
STAFF_BOOTSTRAP_NAME=Ramesh Kumar (Procurement Inspector)
STAFF_BOOTSTRAP_MANDI=Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)

# Google Gemini AI Inference (Google AI Studio / Vertex AI)
GEMINI_API_KEY=<your_production_google_gemini_api_key>
GEMINI_MODEL=gemini-2.5-flash

# SMS / WhatsApp Gateway (CDAC Gov SMS / Twilio / Kaleyra - Optional)
# When unconfigured, farmer accounts are secured via password; phone ownership is unverified.
SMS_GATEWAY_URL=<your_sms_gateway_endpoint_url>
SMS_GATEWAY_API_KEY=<your_sms_gateway_credential>
SMS_SENDER_ID=TNDPC
SMS_DLT_TEMPLATE_ID=<approved_dlt_template_registration_id>

# Data.gov.in Mandi Market Prices (Resource: 9ef84268-d588-465a-a308-a864a43d0070)
# Register and generate API key at https://data.gov.in/
DATA_GOV_IN_API_KEY=<your_production_data_gov_in_api_key>

# Background refresh interval in minutes for polling data.gov.in (Default: 15 minutes)
MANDI_REFRESH_INTERVAL_MINUTES=15

# Browser Web Push Notifications (VAPID)
# Generate with: npx web-push generate-vapid-keys
VAPID_PUBLIC_KEY=<your_vapid_public_key>
VAPID_PRIVATE_KEY=<your_vapid_private_key>
VAPID_CLAIM_EMAIL=mailto:support@nammavivasayi.tn.gov.in
```

---

## 5. Security & Network Hardening

1. **HTTPS / TLS Enforcement:**
   - Force HTTP $\rightarrow$ HTTPS redirection.
   - Enforce HSTS (`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`).
2. **CORS Restrictions:**
   - Disallow wildcards (`*`).
   - Only allow official frontend domain origins.
   - Enforce `allow_credentials=True` for authorization headers.
3. **Rate Limiting:**
   - Dual-layer protection active on `/api/auth/login`:
     - Client IP sliding window: 10 requests / min.
     - Phone identifier sliding window: 10 requests / min.
   - Booking creation limit: 5 requests / min per farmer account.
4. **Credential Stripping in Bundles:**
   - Vite `import.meta.env.DEV` completely removes development demo buttons and default passwords from production assets (`dist/assets/*.js`).

---

## 6. Backup, Restore & Disaster Recovery Runbook

### Automated Backup Schedule
- **Full Snapshot:** Every 24 hours at 01:00 AM IST.
- **Oplog Point-in-Time Recovery (PITR):** Continuous oplog streaming with 7-day retention.
- **Target RTO (Recovery Time Objective):** < 30 minutes.
- **Target RPO (Recovery Point Objective):** < 1 hour.

### Manual Backup Command (`mongodump`)
```bash
# Create timestamped compressed archive
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mongodump \
  --uri="mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/namma_vivasayi_db" \
  --archive="/var/backups/namma_vivasayi_${TIMESTAMP}.gz" \
  --gzip

# Upload to secure offsite cold storage (e.g. AWS S3 with Glacier Lifecycle)
aws s3 cp "/var/backups/namma_vivasayi_${TIMESTAMP}.gz" "s3://tn-agri-backups-bucket/namma_vivasayi_${TIMESTAMP}.gz"
```

### Manual Restore Command (`mongorestore`)
```bash
# Restore specific archive into staging or recovered production database
mongorestore \
  --uri="mongodb+srv://<db_user>:<db_password>@<cluster>.mongodb.net/namma_vivasayi_db" \
  --archive="/var/backups/namma_vivasayi_20261020_010000.gz" \
  --gzip \
  --nsInclude="namma_vivasayi_db.*"
```

---

## 7. Health Checks, Monitoring & Troubleshooting

### Health Check Endpoints

#### 1. System-Wide Health Endpoint
- **URL:** `GET /api/health`
- **Response Format:**
  ```json
  {
    "status": "healthy",
    "environment": "production",
    "timestamp": "2026-10-20T13:45:00.000000Z",
    "database": {
      "connected": true,
      "database_name": "namma_vivasayi_db",
      "message": "Connected to MongoDB"
    },
    "mandiMarketPrices": {
      "status": "healthy",
      "dataSource": {
        "provider": "data.gov.in (Agmarknet Daily Mandi Prices)",
        "resourceId": "9ef84268-d588-465a-a308-a864a43d0070",
        "state": "Tamil Nadu",
        "sourceStatus": "LIVE",
        "sourceConfigured": true
      },
      "cacheMetrics": {
        "totalCachedRecords": 182,
        "isCacheFresh": true,
        "cacheAgeMinutes": 4.2
      },
      "backgroundScheduler": {
        "refreshIntervalMinutes": 15,
        "isSingletonLocked": true,
        "activeWorker": "worker-1"
      }
    }
  }
  ```
- **Load Balancer Configuration:** Configure load balancer health probe to poll `/api/health` every 15 seconds with a 5-second timeout and 2 consecutive failure thresholds.

#### 2. Dedicated Mandi Market Prices Operational Health Endpoint
- **URL:** `GET /api/market/health`
- **Purpose:** Deep health metrics for SRE monitoring, Datadog/Prometheus synthetic checks, and upstream government API telemetry.
- **Payload Includes:**
  - `dataSource.sourceStatus`: `LIVE` | `STALE_CACHE` | `COLD_START_FALLBACK` | `UNAVAILABLE`
  - `dataSource.lastCheckedAt` & `dataSource.lastFetchSuccessAt`
  - `cacheMetrics.totalCachedRecords`, `uniqueCommodities`, `uniqueDistricts`, `isCacheFresh`
  - `backgroundScheduler.isRunning`, `refreshIntervalMinutes`, `schedulerType="distributed_mongo_lease_lock"`
  - `operationalErrors.lastError`, `lastErrorTime`, `consecutiveFailures`

### Logging & Observability
- All HTTP requests logged with structured timing (`duration_ms`), status codes, and scrubbed parameters.
- Secrets, passwords, OTPs, and access tokens are automatically sanitized before writing to logs.

---

## 8. AI Pathology API Quotas & Offline Fallback Strategy

1. **Primary Provider:** Google Gemini API (`gemini-2.5-flash` / `gemini-3-flash-preview`).
2. **Model Cascade Fallback:**
   - Candidate 1: `gemini-2.5-flash` (High-speed multimodal)
   - Candidate 2: `gemini-3.1-flash-lite` (Lightweight fallback)
   - Candidate 3: **Verified TNAU Rule-Based Offline Engine**
3. **Behavior When AI Service Unavailable / Quota Exhausted:**
   - The platform **never halts or errors out**.
   - It returns status `not_configured` or `inconclusive`.
   - It outputs the verified TNAU Visual Symptom Reference Guide.
   - It supplies contact details for local AAOs and the Uzhavan Helpline (`1800-425-1661`).

---

## 9. SMS & WhatsApp Gateway Integration Status

| Component | Status | Required Production Actions |
| :--- | :--- | :--- |
| **In-App Notifications** | **Operational** | Stored in MongoDB `notifications` collection with unread badges. |
| **Notification Service Interface** | **Operational** | `notifications.py` contains modular `SMSNotificationService`. |
| **CDAC Gov SMS / Twilio** | **Pending Configuration** | Requires registration with Indian Telecom DLT portal (Telecom Commercial Communications Customer Preference Regulations - TCCCPR):<br>1. Register Entity & Header (`TNDPC`).<br>2. Register 5 transactional SMS templates (Booking, Gate Check-In, Quality Grade, Digital Bill, DBT Credit).<br>3. Populate `SMS_GATEWAY_URL` and `SMS_GATEWAY_API_KEY`. |

---

## 10. Operational Cost Estimates

> **Note on Cost Methodology:** The figures below clearly distinguish **verified vendor pricing** from **variable usage estimates** based on pilot volumes (10 Direct Procurement Centres, ~5,000 active farmers/season).

| Service Layer | Provider / Resource | Verified Pricing Model | Estimated Monthly Cost |
| :--- | :--- | :--- | :---: |
| **Database** | MongoDB Atlas Dedicated M10 | $0.08/hr ($57.00/month flat rate, verified) | **$57.00** |
| **Backend Compute** | AWS ECS / Fargate (2 vCPU, 4GB RAM) or 2x t4g.small | ~$0.04/hr per instance (verified AWS pricing) | **$28.00** |
| **Frontend Hosting** | Cloudflare Pages / Vercel Pro | Free Tier ($0) / Pro ($20/month flat rate) | **$0.00 – $20.00** |
| **AI Inference** | Google Gemini API (Pay-as-you-go) | $0.10 / 1M input tokens, $0.40 / 1M output tokens | **$5.00 – $15.00** |
| **Domain & SSL** | Cloudflare / NIC.in / GoDaddy | Domain: ~$12.00/year; SSL: Free (Let's Encrypt) | **$1.00** |
| **Transactional SMS** | Indian DLT Telecom Gateway | ~₹0.12 per transactional SMS (~$0.0014) | **$15.00 – $35.00** |
| **TOTAL ESTIMATE** | | | **~$106.00 – $156.00 / month** |

---

## 11. Market Mandi Prices (data.gov.in) Production Operations & SRE Blueprint

### 1. Official Data Source Contract
- **Authoritative Publisher:** Ministry of Agriculture & Farmers Welfare, Government of India (Agmarknet).
- **Open Data Portal:** [data.gov.in](https://data.gov.in/)
- **Dataset Title:** "Current Daily Price of Various Commodities from Various Markets (Mandi)"
- **Resource ID:** `9ef84268-d588-465a-a308-a864a43d0070`
- **Base Endpoint:** `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Query Parameters Enforced:**
  - `api-key`: Injected from `DATA_GOV_IN_API_KEY` environment variable.
  - `format=json`
  - `filters[state]=Tamil Nadu`
  - `limit=100` (paginated up to total available records)
- **Zero Simulation Policy:** Simulated or synthetic prices are strictly forbidden. The system displays only genuine government records. If the government API is unavailable or credentials are missing, the system gracefully operates in authenticated cache mode with transparent English/Tamil status notices.

### 2. Secret Management & Hosting Configuration
Configure the following secrets in your persistent host's secret management dashboard:

| Variable Name | Required | Sample Value / Pattern | Host Secret Management Location |
| :--- | :---: | :--- | :--- |
| `DATA_GOV_IN_API_KEY` | Recommended | `579b464db66ec23bdd000001...` | **Render:** Environment > Secret Files / Environment Variables<br>**Railway:** Variables Tab<br>**AWS:** Secrets Manager / Parameter Store<br>**Doppler:** Secret Store |
| `MANDI_REFRESH_INTERVAL_MINUTES` | Optional | `15` (Default: 15 minutes) | Host Environment Variables |
| `ALLOWED_ORIGINS` | Mandatory | `https://nammavivasayi.vercel.app` | Host Environment Variables |
| `MONGODB_URI` | Mandatory | `mongodb+srv://...` | Host Secret Environment Variables |

> **Privacy & Logging Security:** The backend code scrubs and redacts the `DATA_GOV_IN_API_KEY` from all application logs, error traces, and operational telemetry. Only a boolean `apiKeyConfigured` flag is ever returned in health endpoints.

### 3. Persistent Hosting Architecture & Distributed Singleton Scheduler
- **Why Persistent Hosting is Required:**
  The Mandi Prices automatic refresh process runs as a managed asynchronous background loop within FastAPI. Persistent hosting services (**Render Web Service**, **Railway**, **Fly.io**, **AWS ECS/EC2**, **DigitalOcean**) keep the event loop alive. Serverless platforms (AWS Lambda, Vercel Serverless Functions) freeze background tasks between requests and cannot maintain scheduled intervals without external webhook cron triggers.
- **Distributed Singleton Lease Lock Architecture:**
  To guarantee that multi-worker or multi-container deployments (e.g. `uvicorn main:app --workers 4` or multiple Kubernetes pods) do not spawn redundant schedulers or duplicate API calls against data.gov.in, the system implements a **MongoDB-backed Distributed Singleton Lease Lock**:
  - **Collection:** `scheduler_locks`
  - **Job Name:** `mandi_market_refresh`
  - **Lease Duration:** 15 minutes (`900 seconds`)
  - **Worker Identity:** Unique worker token (`worker-{uuid4()[:8]}`) generated per process.
  - **Acquisition Protocol:** Atomic `find_one_and_update` with filter `{"jobName": "mandi_market_refresh", "$or": [{"leaseExpiresAt": {"$lt": now}}, {"lockedBy": worker_id}]}`.
  - **Failure Recovery:** If the primary worker crashes or restarts, its lease automatically expires after 15 minutes, allowing a healthy worker to acquire the lock immediately.

### 4. Frontend Automatic Page Refresh & User Experience
- **Auto-Refresh Cadence:** The frontend (`MandiPricesView.tsx`) polls `GET /api/market-prices` every **60 seconds** while the user is actively viewing the Market Prices page.
- **Browser Visibility Lifecycle:**
  Uses the standard **Page Visibility API** (`document.addEventListener('visibilitychange')`).
  - When the farmer switches browser tabs or minimizes the window: polling automatically pauses to conserve mobile data and client battery.
  - When the farmer returns to the tab: polling resumes immediately and initiates an instant freshness check.
- **User Interface Features:**
  - Real-time search by commodity or market.
  - District filter dropdown covering all 38 districts of Tamil Nadu.
  - Commodity category quick-filter pills (Cereals, Vegetables, Fruits, Oilseeds, Pulses, Spices).
  - Clear bilingual status badges:
    - `🟢 LIVE SOURCE (data.gov.in)`: Live feed synchronized.
    - `🟡 CACHED ARCHIVE (Offline Fallback)`: Displayed when API key is unconfigured or upstream is down.
    - `🔵 NO NEW MARKET DATA`: Displayed when government board hasn't published new arrivals since last poll.

### 5. Mandi Price-Change Alert Engine & Notification Deduping
The notification subsystem (`market_notifications.py`) runs automatically after every background sync:
1. **Price Surge Alert (`mandi_price_surge`):** Triggered when modal price increases by $\ge$ configured threshold (Default: +5.0%).
2. **Price Drop Alert (`mandi_price_drop`):** Triggered when modal price decreases by $\ge$ configured threshold (Default: -5.0%).
3. **New Commodity Arrival Alert (`mandi_new_arrival`):** Triggered when a new crop variety arrives at the farmer's designated market.
4. **Stale Feed Informational Notice (`mandi_stale_feed`):** Non-alarming notification when the government feed experiences delays exceeding 24 hours.
- **Farmer Preference Filtering:**
  Farmers configure alert preferences in the **Notifications > Mandi Settings** tab:
  - Master Mandi Alerts toggle.
  - Granular surge, drop, and stale feed toggles.
  - Sensitivity slider (1% to 25% price change threshold).
  - Targeted commodity and market selector (e.g., only alert for *Paddy* at *Thanjavur Mandi*).
- **24-Hour Deduplication Guarantee:**
  Every alert generates a deterministic, stable deduplication key:
  `{user_id}_{event_type}_{record_id}_{modal_price}`
  Indexed uniquely with a 24-hour expiration window in MongoDB `notifications`. Scheduler restarts and multi-worker concurrent checks cannot trigger duplicate alerts.

### 6. Fault Tolerance & Resilience Matrix

| Failure Mode | Upstream Behavior | Platform Response | Cache Safety |
| :--- | :--- | :--- | :--- |
| **Invalid / Revoked API Key** | HTTP 403 Forbidden | Logs operational warning; flags `sourceStatus="UNAVAILABLE"`; presents clear disclosure to user. | **100% Preserved** (Cache never cleared). |
| **Government Portal Downtime** | HTTP 500 / 503 Service Unavailable | Caught gracefully in `httpx` error handler; switches to `STALE_CACHE`; increments consecutive failure count. | **100% Preserved**. |
| **Network Latency / Timeout** | Request exceeds 20s budget | `httpx.TimeoutException` caught; logs timeout notice without crashing scheduler. | **100% Preserved**. |
| **Empty Government Response** | Returns `{"records": []}` | Validates empty payload; updates `lastCheckedAt`; retains all existing cached records. | **100% Preserved**. |
| **Malformed / Invalid Records** | Negative prices, missing modal prices, bad dates | `normalize_record()` rejects bad entries during ingestion; only valid records are written to MongoDB. | Corrupt records discarded. |
| **Service Restoration** | Government API returns HTTP 200 | Automatically clears error state; updates `lastFetchSuccessAt`; transitions status back to `LIVE`. | Seamless recovery. |
| **Cold-Start Deployment** | Clean MongoDB with zero cached records | Reads authenticated baseline snapshot (`data/agmarknet_snapshot.json`) to populate initial cache. | Zero downtime cold start. |

### 7. Data Freshness Realities & Government Publication Cadence
- **Cadence Limitation:** Agricultural Produce Market Committees (APMCs) and regulated mandis in Tamil Nadu upload daily auction summaries to Agmarknet once or twice per working day (usually between 12:00 PM and 6:00 PM IST).
- **Polling vs Publishing:** The 15-minute backend refresh interval polls data.gov.in to discover new records promptly. Setting a faster polling interval (e.g. 1 minute) will **not** cause government mandi officers to publish prices faster.
- **Authentic Arrival Dates:** The platform always displays the authentic government arrival date (e.g. `20 Oct 2026`). It never manufactures synthetic timestamps to appear "live" when government offices have not reported new arrivals.

### 8. Mandi Prices Rollback & Failover Runbook
In the event of an upstream government schema change or API endpoint deprecation:
1. **Immediate Failover to Authenticated Cache:**
   - In your host dashboard (e.g. Render/Railway), set `DATA_GOV_IN_API_KEY=""`.
   - The application instantly transitions to authenticated cache mode, serving verified baseline prices with an honest status notice. No service downtime occurs.
2. **Diagnose via Health Endpoint:**
   - Query `GET /api/market/health` to inspect `operationalErrors.lastError` and `lastCheckedAt`.
3. **Validate Restored API Key or Resource ID:**
   - Test new credentials via curl:
     ```bash
     curl "https://api.data.gov.in/resource/<RESOURCE_ID>?api-key=<NEW_KEY>&format=json&filters[state]=Tamil%20Nadu&limit=5"
     ```
4. **Reactivate Live Sync:**
   - Update `DATA_GOV_IN_API_KEY` with the verified key in the host settings.
   - Trigger an immediate forced sync:
     ```bash
     curl -X POST "https://your-backend-service.onrender.com/api/market/sync?force=true"
     ```
   - Confirm `sourceStatus` returns to `"LIVE"`.

---

## 12. Rollout & Rollback Strategy

1. **Blue/Green Deployment:** Deploy new Docker container image alongside running version; switch load balancer traffic only after `/api/health` probe returns 200 OK.
2. **Database Migrations:** Schema changes must be backward-compatible and additive.
3. **Instant Rollback:** If error rate on `/api/procurement/bookings` or `/api/market-prices` exceeds 1% over 5 minutes, immediately revert load balancer target group to previous container release.

---

## 13. Deployment Safeguards & Unresolved Blockers Audit

### Technical Safeguards Assessment

| Area | Safeguard Status | Technical Details |
| :--- | :---: | :--- |
| **Multi-Worker Concurrency** | **Protected at DB Layer** | In-memory `asyncio.Lock` synchronizes coroutines inside a single process. Across multiple Uvicorn workers (`--workers 4`), duplicate claims and overbooking are prevented by MongoDB unique constraints (`bookingId`, `billNumber`, `closureId`) and atomic `find_one_and_update` with status preconditions. Distributed Redis locking (`aioredlock`) is recommended for multi-node clusters. |
| **Database Index Integrity** | **Automated & Idempotent** | `init_database_indexes()` runs on FastAPI startup, creating unique and compound indexes with `background=True` across 10 collections. Existing records are never disrupted or locked. |
| **Environment Variable Hygiene**| **Verified Clean** | All templates (`.env.example`) use placeholder values. Real secrets (JWT secrets, API keys, database credentials) are injected exclusively through environment variables. |
| **Production Bundle Hardening** | **Verified Clean** | Vite `import.meta.env.DEV` conditions eliminate demo credentials and mock helper buttons from production JavaScript bundles (`frontend/dist/`). |
| **HTTPS & Transport Security**  | **Prerequisite for Prod** | Enforce TLS 1.3 with HSTS headers at the reverse proxy (Nginx or Cloudflare CDN). Direct unencrypted HTTP traffic must be rejected with 301 redirects. |

### Documented Production Blockers (Pre-Launch Action Items)

1. **Carrier SMS Delivery (DLT Registration):**
   - *Status:* **BLOCKED on External Regulatory Approval**.
   - *Requirement:* Must register Entity, Header (`TNDPC`), and 5 transactional templates on an Indian Telecom DLT portal before cellular SMS can be dispatched. In-app notifications function independently.
2. **Automated Bank Wire Transfers (PFMS / NPCI DBT Gateway):**
   - *Status:* **BLOCKED on Government Banking Authorization**.
   - *Requirement:* Payment tracking currently provides an administrative status progression with manual PFMS reference logging. Direct bank account credit requires a bilateral agreement with the Public Financial Management System.
3. **Distributed Redis Locking (Scale Requirement):**
   - *Status:* **RECOMMENDED for Clustered Multi-Node Deployments**.
   - *Requirement:* For horizontal scaling beyond a single server (e.g., Kubernetes or multi-VM clusters), deploy a managed Redis cluster to provide cross-node mutex locks for slot reservations.


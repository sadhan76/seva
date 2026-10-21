# AgriBharat (SEVA) — Controlled Pilot Readiness Checklist

> **Scope & Purpose:** This checklist defines the mandatory operational, technical, legal, and safety prerequisites required before deploying **AgriBharat (SEVA)** into a controlled live pilot with real farmers and Direct Procurement Centres.

---

## 1. Pilot Scope & Controlled Boundary

- **Target Location:** 1 Pilot Direct Procurement Centre — **Thanjavur DPC #3 (Pillaiyarpatti)**.
- **Cohort Size:** 100 to 250 verified participating farmers across adjacent revenue villages (Pillaiyarpatti, Vallam, Nanjikottai).
- **Target Crop:** Samba Paddy (Grade A & Common).
- **Operating Period:** 30 days during active harvest procurement window.

---

## 2. Prerequisites Verification Matrix

| Domain | Prerequisite Item | Status | Verification Criteria |
| :--- | :--- | :---: | :--- |
| **Consent & Legal** | Farmer Informed Consent Form | 📋 Ready | Bilingual (Tamil/English) consent form explaining that slot booking reserves yard capacity; digital weighment data will be shared with the Civil Supplies department. |
| **Data Privacy** | PII Minimization & Protection | ✅ Verified | Aadhaar numbers strictly masked (last-4 digits only: `XXXX-XXXX-4410`). Passwords hashed with Bcrypt (cost 12). Tokens expire in 12 hours. |
| **User Accounts** | Farmer & Staff Pilot Provisioning | ✅ Verified | Pilot farmers register via phone number with OTP verification. DPC staff provisioned via backend bootstrap with centre-restricted authorization. |
| **Staff Training** | Yard Staff Operational Training | 📋 Ready | Half-day training module for DPC inspectors covering: QR gate check-in, moisture meter recording, counter queue calling, digital weighment entry, and error correction. |
| **Support Contacts** | Support Desk & Escalation Roster | 📋 Ready | Primary support contact: Assistant Agricultural Officer (AAO) / DPC Superintendent.<br>TNAU Agritech Toll-Free Helpline: `1800-425-1661`.<br>Technical escalation phone: designated on-call engineer. |
| **Backup & Restore**| Automated Database Snapshot Plan | ✅ Verified | Automated daily mongodump backup at 01:00 AM IST. Tested manual restore runbook documented in [DEPLOYMENT_GUIDE.md](file:///d:/SEVA/DEPLOYMENT_GUIDE.md). RTO < 30 mins; RPO < 1 hour. |
| **System Health** | Health Probes & Error Logging | ✅ Verified | Continuous `/api/health` monitoring probe. Structured JSON error logs with automatic secret and token sanitization. |
| **AI Fallback** | Automated Offline Advisory Engine | ✅ Verified | If Gemini Vision API quota is exhausted or latency exceeds 15 seconds, the system transparently engages the verified TNAU rule-based advisory catalog without failing or inventing diagnoses. |
| **Rollback Plan** | Zero-Downtime Rollback Procedure | ✅ Verified | In the event of system failure, staff revert to manual physical weighment registers. All digital bookings and weighments remain persisted in MongoDB for later reconciliation. |

---

## 3. Critical Verification: Demo Features vs. Live Integrations

To ensure transparency and prevent misunderstandings during the pilot, the following technical distinctions are strictly established:

### A. Payment Tracking vs. Real Banking Wire Transfer
> **IMPORTANT CLARIFICATION:**
> - **Current System Functionality:** The digital bill and payment status tracking module provides an **administrative audit lifecycle** (`PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `PAID`) where authorized procurement staff record transaction reference numbers (e.g. `PFMS-TN-2026-908123`) when funds are approved or released by the district treasury.
> - **Limitation:** The platform **does NOT directly trigger an automated electronic wire transfer** or bank account debit/credit from the UI. It reflects the administrative progression of treasury disbursements. Direct automated banking integration requires an approved API bridge to the Public Financial Management System (PFMS) or National Payments Corporation of India (NPCI) DBT Bharat gateway.

### B. In-App Notifications vs. Carrier SMS / WhatsApp Delivery
> **IMPORTANT CLARIFICATION:**
> - **Current System Functionality:** All critical procurement milestones (booking confirmed, gate checked in, quality inspected, bill generated, payment updated) are **persisted in real-time in the MongoDB `notifications` collection** and surfaced in the farmer's in-app notification inbox with unread badges.
> - **Limitation:** Direct cellular carrier SMS / WhatsApp delivery to farmer feature phones is **pending DLT regulatory registration**. Before live carrier SMS can be dispatched in India, the operating entity must register under TRAI TCCCPR regulations:
>   1. Principal Entity Registration on Telecom DLT Portal (e.g., Vilpower / Jio / Airtel DLT).
>   2. Header Registration (`TNDPC` or `NMVIVA`).
>   3. Approval of 5 Transactional SMS Content Templates.
>   4. Population of `SMS_GATEWAY_URL` and `SMS_GATEWAY_API_KEY` in production environment.

### C. AI Vision Diagnostics vs. Certified Pathology Diagnosis
> **IMPORTANT CLARIFICATION:**
> - **Current System Functionality:** The AI leaf disease module provides an **advisory second opinion** based on multimodal vision pattern matching against common Tamil Nadu crop pathologies (Blast, Blight, Stem Borer, Tikka).
> - **Limitation:** AI predictions are **strictly advisory** and clearly labeled with confidence metrics. For ambiguous, unreadable, or severe conditions, the system directs the farmer to collect a fresh leaf sample and consult their local Assistant Agricultural Officer (AAO) or Krishi Vigyan Kendra (KVK). For non-parasitic abiotic stress, chemical pesticide suggestions are strictly disabled.

---

## 4. Controlled Pilot Rollout Phases

```text
+-----------------------------------------------------------------------------------+
| Phase 1: Shadow Simulation (Days 1 - 5)                                           |
| - DPC staff operate SEVA in parallel with existing physical registers.            |
| - Verify weighbridge calculation parity against physical weigh slips.             |
| - Zero impact on existing farmer delivery routines.                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Phase 2: Controlled Cohort Pilot (Days 6 - 20)                                    |
| - 100 enrolled farmers use SEVA to book advance slot windows.                     |
| - QR gate check-in and Counter-1 queue calling activated.                         |
| - Digital bills issued to farmers' mobile phones alongside printed slips.         |
| - Daily review of slot adherence and queue wait times.                            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Phase 3: Shift Evaluation & Scale-Up (Days 21 - 30)                               |
| - Audit daily procurement reports against district treasury records.              |
| - Measure farmer satisfaction (wait-time reduction, transparency perception).     |
| - Formal submission of pilot findings to District Agricultural Officer.           |
+-----------------------------------------------------------------------------------+
```

---

## 5. Escalation Contacts & On-Call Roster

| Role | Contact Entity | Responsibilities |
| :--- | :--- | :--- |
| **DPC Yard Lead** | Ramesh Kumar (Procurement Inspector) | On-site weighbridge operations, dispute resolution, truck queuing. |
| **Agronomic Extension Lead**| Assistant Agricultural Officer (AAO) — Thanjavur Block | Plant pathology queries, moisture meter calibration, TNAU advisory verification. |
| **Technical Support Lead** | On-Call Platform Engineer | API uptime, database replication, JWT/auth issue resolution. |
| **Emergency Farmer Hotline**| TNAU Uzhavan Agritech Helpline (`1800-425-1661`) | 24/7 general farming, disease identification, and weather emergency support. |

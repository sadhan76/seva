# Namma Vivasayi AI - FastAPI Backend (Phase 2 Active)

This folder contains the Python FastAPI backend connected to MongoDB for the **Namma Vivasayi AI** platform.

---

### Prerequisites (Windows)
- **Python**: 3.10+ (Available via `py` or `python` command)
- **MongoDB**: Community Server (Running on `localhost:27017`)

---

### Setup Instructions (Windows)
1. Open Command Prompt or PowerShell in `backend`:
   ```cmd
   cd backend
   ```
2. Activate the pre-configured virtual environment:
   ```cmd
   .\venv\Scripts\activate
   ```
   *(If creating fresh: `py -m venv venv` followed by `.\venv\Scripts\pip install -r requirements.txt`)*
3. Verify the `.env` configuration file exists:
   ```cmd
   copy .env.example .env
   ```
4. Run the FastAPI dev server:
   ```cmd
   .\venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
5. Interactive OpenAPI Swagger documentation will be available at:
   👉 **`http://127.0.0.1:8000/docs`**

---

### Implemented Endpoints
- `GET /api/health` — Checks backend status and performs live ping on MongoDB.
- `POST /api/farmers` — Registers a new farmer profile in MongoDB with validation.
- `GET /api/farmers` — Lists all registered farmer profiles sorted by newest first.
- `GET /api/farmers/{farmer_id}` — Retrieves a specific farmer profile by ID.
- `POST /api/procurement/bookings` — Creates a regulated mandi procurement booking, calculates estimated weight in quintals, generates unique queue token (`TN-DPC-XXX`), and stores it in MongoDB.
- `GET /api/procurement/bookings` — Lists all confirmed procurement bookings from MongoDB.

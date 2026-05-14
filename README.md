# ⚡ AxiLex — Electrician Contractor Management System (MySQL Version)

# Link - https://electrician-contractor-management.netlify.app

Enterprise-level Electrician Contractor Management System built for **AXILEX PVT LTD**.

---

## 🛠️ Tech Stack
| Layer | Technology |
|-------|-----------|
| **Frontend** | Vanilla HTML, CSS, JavaScript (Premium Dark Theme) |
| **Backend** | Python FastAPI + SQLAlchemy ORM |
| **Auth** | JWT Tokens (Role-Based: Admin / Client / Electrician) |
| **Database** | MySQL (Connection via pymysql) |
| **API Docs** | Auto-generated Swagger UI at `/docs` |

---

## 👤 Demo Login Credentials
| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@axilex.com` | `Admin@123` |
| **Client** | `client@axilex.com` | `Client@123` |
| **Electrician** | `electrician@axilex.com` | `Elec@123` |

> Create these by running `python seed.py` after database setup.

---

## 🚀 Setup & Installation (MySQL)

### Step 1: Database Setup
1. Open your MySQL client (XAMPP, MySQL Workbench, etc.).
2. Create a new database:
   ```sql
   CREATE DATABASE axilex_db;
   ```
3. Open `backend/.env` and update your MySQL credentials:
   ```
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/axilex_db
   ```

### Step 2: Install Backend Dependencies
```powershell
cd backend
python -m pip install -r requirements.txt
```

### Step 3: Seed Demo Data
```powershell
python seed.py
```
This will automatically create all tables in MySQL and insert the demo users.

### Step 4: Start Backend Server
```powershell
python -m uvicorn main:app --reload
```
Backend runs at: **http://localhost:8000**

### Step 5: Run Frontend
Simply open `frontend/index.html` in your browser or run a simple server:
```powershell
cd frontend
python -m http.server 3000
```

---

## ✅ API Endpoints Summary
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ❌ | Register new user |
| POST | `/login` | ❌ | Login (returns JWT) |
| GET | `/admin/stats` | Admin | Dashboard statistics |
| POST | `/requests` | Client | Submit service request |
| GET | `/jobs` | Electrician | Get available jobs |
| PATCH | `/jobs/{id}/status` | Electrician | Update job status |

# Fayda ID Postal Tracking & Desk Dispatch System (FDS)

An operational postal counter tracking, storage bin retrieval, and automated desk dispatch system built for Ethiopia's **Fayda National ID** distribution at postal branches (e.g., Adama Main Post Office).

---

## 🚀 Key Features

- **Dynamic Counter Desk Dispatch**:
  - ⚡ **Desk 1 (Priority & Accessibility Counter)**: Automatically routes senior citizens (Age $\ge$ 60), expectant mothers, and citizens requesting accessibility assistance.
  - 🏢 **Desk 2 (Counter Desk 2)**: Physical storage bin `Shelf A` cards.
  - 🏢 **Desk 3 (Counter Desk 3)**: Physical storage bin `Shelf B` cards.
- **Citizen Self-Service Kiosk (`/`)**:
  - High-visibility counter directions with interactive accessibility/priority toggle.
  - 1-Click quick testing presets for all branch workflows.
- **Staff Counter Terminal (`/clerk.html`)**:
  - Secure authentication barrier (`/login.html`) with shared branch credentials.
  - Physical storage locator cards highlighting exact shelf and box coordinates (`Shelf A / Box 04`).
  - Live handover confirmation with real-time audit logging and daily counters.
- **FastAPI RESTful Backend**:
  - SQLite database with SQLAlchemy ORM.
  - Comprehensive automated test suite with 100% test pass rate.
  - Interactive OpenAPI Swagger docs at `/docs`.

---

## 📁 Project Structure

```
fayda-dispatch-system/
├── backend/
│   ├── database.py         # SQLite engine and session configuration
│   ├── models.py           # FaydaCard and HandoverAuditLog database models
│   ├── schemas.py          # Pydantic request and response schemas
│   ├── seed.py             # Database seed data populator
│   ├── test_dispatch.py    # Automated test suite (9 test cases)
│   ├── main.py             # FastAPI routing, auth, static file mounts
│   └── requirements.txt    # Backend dependencies
└── frontend/
    ├── index.html          # Public Citizen Self-Service Kiosk
    ├── login.html          # Postal Clerk Authentication Portal
    ├── clerk.html          # Counter Terminal & Storage Bin Retrieval
    ├── css/
    │   └── style.css       # Design system & responsive layout styles
    └── js/
        ├── citizen.js      # Citizen tracking lookup & desk dispatch logic
        └── clerk.js        # Counter operations, handover issuing, audit logs
```

---

## ⚡ Quick Start

### 1. Install Backend Dependencies
```bash
cd fayda-dispatch-system/backend
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python seed.py
```

### 3. Run Automated Tests
```bash
python test_dispatch.py
```

### 4. Start the Application
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 Application Endpoints

| Portal / Resource | URL | Description |
| :--- | :--- | :--- |
| **Citizen Kiosk** | `http://127.0.0.1:8000/` | Public self-service desk lookup |
| **Clerk Login** | `http://127.0.0.1:8000/login.html` | Postal staff authentication |
| **Clerk Terminal** | `http://127.0.0.1:8000/clerk.html` | Counter handover & inventory terminal |
| **API Documentation** | `http://127.0.0.1:8000/docs` | Interactive Swagger UI |

### Clerk Default Credentials
- **Username**: `clerk` (or `clerk1`, `clerk2`, `admin`)
- **Password**: `fayda2026` (or `clerk123`)

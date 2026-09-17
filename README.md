# Fayda ID Postal Tracking & Desk Dispatch System (FDS)

An operational postal counter tracking, storage bin retrieval, and automated desk dispatch system built for Ethiopia's **Fayda National ID** distribution at postal branches (e.g., Adama Main Post Office).

---

## 🏛️ System Architecture: Separated Domains

The application is structured into two completely isolated frontend portals connecting to a central FastAPI backend:

```
┌────────────────────────────────────────────────────────┐
│ 🖥️ Citizen Public Kiosk                                │
│ http://127.0.0.1:3000                                  │
│ • Entrance lobby self-service kiosk                    │
│ • Zero staff links or administrative data              │
│ • Real-time counter desk routing (Desk 1, 2, or 3)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ REST API
┌────────────────────────────────────────────────────────┐
│ ⚙️ Central Dispatch API & Database Engine               │
│ http://127.0.0.1:8000  • Swagger: /docs                │
│ • Routing engine, age & priority evaluation            │
│ • Immutable handover audit ledger & statistics         │
└───────────────────────────▲────────────────────────────┘
                            │ REST API
┌───────────────────────────┴────────────────────────────┐
│ 🔒 Postal Staff Counter Portal                         │
│ http://127.0.0.1:5000                                  │
│ • Employee login gateway (shared branch credentials)   │
│ • Storage bin retrieval locator (Shelf A / Box 04)     │
│ • Live card handover confirmation & audit logging      │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **Dynamic Counter Desk Dispatch**:
  - ⚡ **Desk 1 (Priority & Accessibility Counter)**: Automatically routes senior citizens (Age $\ge$ 60), expectant mothers, and citizens requesting accessibility assistance.
  - 🏢 **Desk 2 (Counter Desk 2)**: Physical storage bin `Shelf A` cards.
  - 🏢 **Desk 3 (Counter Desk 3)**: Physical storage bin `Shelf B` cards.
- **Dedicated Citizen Kiosk App (`kiosk/` - Port 3000)**:
  - Clean, high-visibility counter directions with accessibility toggle.
  - 1-Click quick testing presets for all branch workflows.
- **Dedicated Staff Portal (`staff/` - Port 5000)**:
  - Employee login gateway (`index.html`) with shared credentials and workstation selection.
  - Storage bin locator (`terminal.html`) with visual bin tags (`Shelf A / Box 04`).
  - Master registry browser with 1-click **Select** shortcuts.
  - Immutable handover audit trail with operator clerk logging.
- **Central FastAPI Backend (`backend/` - Port 8000)**:
  - SQLite database with SQLAlchemy ORM.
  - Comprehensive automated test suite with 100% pass rate.
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
│   ├── main.py             # FastAPI routing, auth, and API endpoints
│   └── requirements.txt    # Backend dependencies
├── kiosk/                  # Dedicated Citizen Public Kiosk (Port 3000)
│   ├── index.html          # Public self-service kiosk UI
│   ├── css/style.css
│   └── js/citizen.js       # Kiosk lookup and desk dispatch logic
└── staff/                  # Dedicated Postal Staff Portal (Port 5000)
    ├── index.html          # Staff authentication login
    ├── terminal.html       # Counter service & bin locator terminal
    ├── css/style.css
    └── js/clerk.js         # Handover issuing, bin retrieval, audit logs
```

---

## ⚡ Quick Start

### 1. Install Backend Dependencies
```bash
cd fayda-dispatch-system/backend
pip install -r requirements.txt
```

### 2. Seed Sample Database
```bash
npm run seed
# or: python fayda-dispatch-system/backend/seed.py
```

### 3. Run Automated Tests
```bash
npm test
# or: python fayda-dispatch-system/backend/test_dispatch.py
```

### 4. Start All Services (Multi-Domain)
```bash
npm run dev
# or: python launch_servers.py
```

---

## 🌐 Application Endpoints

| Portal | URL | Audience | Description |
| :--- | :--- | :--- | :--- |
| **Citizen Public Kiosk** | `http://127.0.0.1:3000` | Citizens | Public counter desk lookup |
| **Postal Staff Portal** | `http://127.0.0.1:5000` | Postal Staff | Employee login & counter terminal |
| **Central Dispatch API** | `http://127.0.0.1:8000/docs` | Developers/API | Swagger API documentation |

### Staff Credentials
- **Username**: `clerk` (or `clerk1`, `clerk2`, `admin`)
- **Password**: `fayda2026` (or `clerk123`)

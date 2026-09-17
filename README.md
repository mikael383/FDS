# Fayda ID Postal Tracking & Desk Dispatch System (FDS)

An operational postal counter tracking, storage bin retrieval, and automated desk dispatch system built for Ethiopia's **Fayda National ID** distribution at postal branches (e.g., Adama Main Post Office).

---

## 🏛️ System Architecture: Separated Portals

```
┌────────────────────────────────────────────────────────┐
│ 🖥️ Citizen Public Kiosk                                │
│ http://localhost:3000  (or http://127.0.0.1:3000)      │
│ • Entrance lobby self-service kiosk                    │
│ • Zero staff links or administrative data              │
│ • Real-time counter desk routing (Desk 1, 2, or 3)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ REST API
┌────────────────────────────────────────────────────────┐
│ ⚙️ Central Dispatch API & Database Engine               │
│ http://localhost:8000  • Swagger: /docs                │
│ • Dynamic routing rules, age & priority evaluation     │
│ • Handover audit ledger & operational statistics       │
└───────────────────────────▲────────────────────────────┘
                            │ REST API
┌───────────────────────────┴────────────────────────────┐
│ 🔒 Postal Staff Counter Portal                         │
│ http://localhost:4000  (or http://127.0.0.1:4000)      │
│ • Employee login gateway (`index.html`)                │
│ • Storage bin retrieval locator (`terminal.html`)      │
│ • Live card handover confirmation & audit logging      │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure (Root Level)

```
FDS/
├── backend/                # Central API Engine (Port 8000)
│   ├── main.py             # FastAPI REST endpoints & auth
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── seed.py             # Seed data generator
│   ├── test_dispatch.py    # Automated test suite
│   └── requirements.txt    # Python dependencies
├── kiosk/                  # Citizen Public Kiosk (Port 3000)
│   ├── index.html          # Public self-service kiosk UI
│   ├── css/style.css
│   └── js/citizen.js       # Kiosk lookup and desk dispatch logic
├── staff/                  # Postal Staff Portal (Port 4000)
│   ├── index.html          # Staff authentication login
│   ├── terminal.html       # Counter service & bin locator terminal
│   ├── css/style.css
│   └── js/clerk.js         # Handover issuing, bin retrieval, audit logs
├── launch_servers.py       # Multi-service launcher script
├── package.json            # NPM scripts runner
└── README.md
```

---

## ⚡ Quick Start

### 1. Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Seed Database
```bash
npm run seed
# or: python backend/seed.py
```

### 3. Run Automated Tests
```bash
npm test
# or: python backend/test_dispatch.py
```

### 4. Start All Services
```bash
npm run dev
# or: python launch_servers.py
```

---

## 🌐 Application Endpoints

| Portal | URL | Audience | Description |
| :--- | :--- | :--- | :--- |
| **Citizen Public Kiosk** | `http://localhost:3000` | Citizens | Public counter desk lookup |
| **Postal Staff Portal** | `http://localhost:4000` | Postal Staff | Employee login & counter terminal |
| **Central Dispatch API** | `http://localhost:8000/docs` | Developers/API | Swagger API documentation |

### Staff Credentials
- **Username**: `clerk` (or `clerk1`, `clerk2`, `admin`)
- **Password**: `fayda2026` (or `clerk123`)

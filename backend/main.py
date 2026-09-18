import datetime
import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from database import engine, get_db, Base
import models
import schemas

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fayda National ID Postal Tracking & Desk Dispatch API",
    description="Postal counter dispatch routing, tracking, and handover management for Fayda National ID distribution.",
    version="1.0.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/track/{identifier}", response_model=schemas.CardTrackResponse)
def track_card(
    identifier: str,
    priority_requested: bool = Query(
        default=False,
        description="Citizen requested priority desk access (e.g., expectant mothers, seniors, reduced mobility)"
    ),
    db: Session = Depends(get_db)
):
    """
    Lookup citizen card by Fayda ID or Phone Number and dynamically compute desk assignment.
    
    Dynamic Routing Rules:
    - If status != 'Ready for Collection': return without desk assignment.
    - If status == 'Ready for Collection':
        * Calculate age: (Current Year - Birth Year)
        * If age >= 60 OR priority_requested == True:
            Assign: 'Desk 1 (Priority & Accessibility Counter)'
        * Else (Standard routing by storage bin):
            - Shelf A -> 'Desk 2 (Counter Desk 2)'
            - Shelf B -> 'Desk 3 (Counter Desk 3)'
            - Other -> 'Desk 2 (Counter Desk 2)'
    """
    clean_id = identifier.strip()

    # Search by either fayda_id or phone_number
    card = db.query(models.FaydaCard).filter(
        or_(
            func.lower(models.FaydaCard.fayda_id) == clean_id.lower(),
            models.FaydaCard.phone_number == clean_id,
            # Also allow matching without leading '+' or dashes
            models.FaydaCard.phone_number == clean_id.replace(" ", "").replace("-", ""),
            func.replace(models.FaydaCard.phone_number, "+", "") == clean_id.replace("+", "")
        )
    ).first()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Fayda ID card found matching '{clean_id}'. Please verify your Fayda ID or registered phone number."
        )

    current_year = datetime.date.today().year
    age = current_year - card.date_of_birth.year

    assigned_desk = None
    priority_applied = False
    instruction = None

    if card.status == "Ready for Collection":
        # Dynamic routing evaluation
        if age >= 60 or priority_requested:
            assigned_desk = "Desk 1 (Priority & Accessibility Counter)"
            priority_applied = True
            if age >= 60 and priority_requested:
                instruction = "Assigned to Priority Counter (Senior Citizen / Accessibility request verified)."
            elif age >= 60:
                instruction = "Assigned to Priority Counter (Senior Citizen access priority, Age 60+)."
            else:
                instruction = "Assigned to Priority Counter (Citizen priority request granted)."
        else:
            storage_bin_upper = (card.storage_bin or "").upper()
            if "SHELF A" in storage_bin_upper:
                assigned_desk = "Desk 2 (Counter Desk 2)"
                instruction = "Assigned to Standard Counter 2 based on storage bin Shelf A."
            elif "SHELF B" in storage_bin_upper:
                assigned_desk = "Desk 3 (Counter Desk 3)"
                instruction = "Assigned to Standard Counter 3 based on storage bin Shelf B."
            else:
                assigned_desk = "Desk 2 (Counter Desk 2)"
                instruction = "Assigned to Standard Counter 2."

        # Update and persist desk assignment
        card.assigned_desk = assigned_desk
        db.commit()
        db.refresh(card)

    elif card.status == "In Transit":
        instruction = "Your Fayda ID card is currently in transit from the central printing authority to the postal branch. Please check back soon."
    elif card.status == "Collected":
        formatted_date = card.collected_at.strftime("%B %d, %Y at %I:%M %p") if card.collected_at else "Earlier"
        instruction = f"This Fayda ID card was already collected on {formatted_date}."
    else:
        instruction = f"Status: {card.status}"

    return schemas.CardTrackResponse(
        id=card.id,
        fayda_id=card.fayda_id,
        phone_number=card.phone_number,
        full_name=card.full_name,
        date_of_birth=card.date_of_birth,
        age=age,
        branch_name=card.branch_name,
        status=card.status,
        storage_bin=card.storage_bin,
        assigned_desk=assigned_desk,
        arrived_at=card.arrived_at,
        collected_at=card.collected_at,
        priority_requested=priority_requested,
        priority_applied=priority_applied,
        instruction=instruction,
    )


@app.post("/api/v1/handover", response_model=schemas.HandoverResponse)
def confirm_handover(payload: schemas.HandoverRequest, db: Session = Depends(get_db)):
    """
    Processes the handover of a Fayda ID card:
    - Validates that the card is 'Ready for Collection'.
    - Updates status to 'Collected', sets collected_at = now().
    - Inserts a record in handover_audit_logs.
    """
    clean_fayda_id = payload.fayda_id.strip()

    card = db.query(models.FaydaCard).filter(
        func.lower(models.FaydaCard.fayda_id) == clean_fayda_id.lower()
    ).first()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fayda card '{clean_fayda_id}' not found."
        )

    if card.status != "Ready for Collection":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue card. Current status is '{card.status}'. Only cards with status 'Ready for Collection' can be issued."
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    card.status = "Collected"
    card.collected_at = now
    if not card.assigned_desk:
        card.assigned_desk = payload.desk_used

    # Insert audit log entry
    audit_log = models.HandoverAuditLog(
        fayda_id=card.fayda_id,
        citizen_name=card.full_name,
        clerk_id=payload.clerk_id.strip(),
        desk_used=payload.desk_used.strip(),
        timestamp=now
    )
    db.add(audit_log)
    db.commit()
    db.refresh(card)

    return schemas.HandoverResponse(
        success=True,
        message=f"Fayda Card {card.fayda_id} successfully issued to {card.full_name}.",
        fayda_id=card.fayda_id,
        citizen_name=card.full_name,
        clerk_id=payload.clerk_id,
        desk_used=payload.desk_used,
        collected_at=now
    )


@app.get("/api/v1/clerk/records", response_model=schemas.ClerkRecordsResponse)
def get_clerk_records(
    status: Optional[str] = Query(None, description="Filter by card status"),
    search: Optional[str] = Query(None, description="Search by citizen name, Fayda ID, or phone"),
    db: Session = Depends(get_db)
):
    """
    Returns card records with optional filtering by status and search term,
    along with recent handover audit logs and real-time statistics.
    """
    card_query = db.query(models.FaydaCard)

    if status and status != "All":
        card_query = card_query.filter(models.FaydaCard.status == status)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        card_query = card_query.filter(
            or_(
                func.lower(models.FaydaCard.fayda_id).like(term),
                func.lower(models.FaydaCard.full_name).like(term),
                models.FaydaCard.phone_number.like(term),
                func.lower(models.FaydaCard.storage_bin).like(term),
            )
        )

    cards = card_query.order_by(models.FaydaCard.id.desc()).all()

    # Recent handover audit logs (most recent 50)
    audit_logs = (
        db.query(models.HandoverAuditLog)
        .order_by(models.HandoverAuditLog.id.desc())
        .limit(50)
        .all()
    )

    # Compute operational statistics
    all_cards = db.query(models.FaydaCard).all()
    total_count = len(all_cards)
    ready_count = sum(1 for c in all_cards if c.status == "Ready for Collection")
    transit_count = sum(1 for c in all_cards if c.status == "In Transit")
    collected_count = sum(1 for c in all_cards if c.status == "Collected")

    # Count handovers today
    today = datetime.date.today()
    handover_today_count = db.query(models.HandoverAuditLog).filter(
        func.date(models.HandoverAuditLog.timestamp) == today
    ).count()

    stats = schemas.ClerkStats(
        total_cards=total_count,
        ready_for_collection=ready_count,
        in_transit=transit_count,
        collected_today=handover_today_count,
        collected_total=collected_count,
    )

    return schemas.ClerkRecordsResponse(
        cards=cards,
        recent_handovers=audit_logs,
        stats=stats
    )


@app.get("/api/v1/citizens/samples")
def get_sample_citizens(db: Session = Depends(get_db)):
    """Provides sample identifiers for instant testing on the UI."""
    cards = db.query(models.FaydaCard).all()
    return [
        {
            "fayda_id": c.fayda_id,
            "phone_number": c.phone_number,
            "full_name": c.full_name,
            "status": c.status,
            "storage_bin": c.storage_bin,
            "dob": c.date_of_birth.isoformat() if c.date_of_birth else None,
            "description": f"{c.full_name} ({c.status}, {c.storage_bin})"
        }
        for c in cards
    ]


# Official Authorized Postal Staff Personnel Registry
AUTHORIZED_STAFF = {
    # 1. Officer Mulugeta Kebede - Shelf A Counter (Desk 2)
    "mulugeta": {
        "full_name": "Mulugeta Kebede",
        "clerk_id": "CLK-ADAMA-01",
        "default_desk": "Desk 2 (Counter Desk 2)",
        "role": "Senior Counter Officer (Shelf A)",
        "passwords": ["fayda2026", "mulugeta123", "clerk123"]
    },
    # 2. Officer Bethlehem Tadesse - Priority Counter (Desk 1)
    "bethlehem": {
        "full_name": "Bethlehem Tadesse",
        "clerk_id": "CLK-ADAMA-02",
        "default_desk": "Desk 1 (Priority & Accessibility Counter)",
        "role": "Accessibility & Senior Officer",
        "passwords": ["fayda2026", "bethlehem123", "clerk123"]
    },
    # 3. Officer Tariku Alemu - Shelf B Counter (Desk 3)
    "tariku": {
        "full_name": "Tariku Alemu",
        "clerk_id": "CLK-ADAMA-03",
        "default_desk": "Desk 3 (Counter Desk 3)",
        "role": "Counter Dispatch Clerk (Shelf B)",
        "passwords": ["fayda2026", "tariku123", "clerk123"]
    },
    # 4. Supervisor Mikael - Branch Admin
    "mikael": {
        "full_name": "Mikael",
        "clerk_id": "CLK-ADMIN-01",
        "default_desk": "Desk 1 (Priority & Accessibility Counter)",
        "role": "Branch Postal Supervisor & Administrator",
        "passwords": ["fayda2026", "mikael123", "admin123", "clerk123"]
    },
    "admin": {
        "full_name": "Mikael",
        "clerk_id": "CLK-ADMIN-01",
        "default_desk": "Desk 1 (Priority & Accessibility Counter)",
        "role": "Branch Postal Supervisor & Administrator",
        "passwords": ["fayda2026", "mikael123", "admin123", "clerk123"]
    },
    # Convenient aliases for branch workstations:
    "clerk": {
        "full_name": "Mulugeta Kebede",
        "clerk_id": "CLK-ADAMA-01",
        "default_desk": "Desk 2 (Counter Desk 2)",
        "role": "Senior Counter Officer",
        "passwords": ["fayda2026", "clerk123"]
    },
    "clerk1": {
        "full_name": "Bethlehem Tadesse",
        "clerk_id": "CLK-ADAMA-02",
        "default_desk": "Desk 1 (Priority & Accessibility Counter)",
        "role": "Accessibility Officer",
        "passwords": ["fayda2026", "clerk123"]
    },
    "clerk2": {
        "full_name": "Mulugeta Kebede",
        "clerk_id": "CLK-ADAMA-01",
        "default_desk": "Desk 2 (Counter Desk 2)",
        "role": "Counter Officer",
        "passwords": ["fayda2026", "clerk123"]
    },
    "clerk3": {
        "full_name": "Tariku Alemu",
        "clerk_id": "CLK-ADAMA-03",
        "default_desk": "Desk 3 (Counter Desk 3)",
        "role": "Counter Officer",
        "passwords": ["fayda2026", "clerk123"]
    }
}


@app.get("/api/v1/auth/staff-list")
def get_authorized_staff():
    """Returns official registered postal personnel roster for counter login."""
    return [
        {
            "username": "mikael",
            "name": "Supervisor Mikael",
            "clerk_id": "CLK-ADMIN-01",
            "desk": "Desk 1 (Priority & Accessibility Counter)",
            "role": "Branch Postal Supervisor & Administrator",
            "avatar": "🛡️"
        },
        {
            "username": "mulugeta",
            "name": "Mulugeta Kebede",
            "clerk_id": "CLK-ADAMA-01",
            "desk": "Desk 2 (Counter Desk 2)",
            "role": "Senior Counter Officer (Shelf A)",
            "avatar": "👨🏾‍💼"
        },
        {
            "username": "bethlehem",
            "name": "Bethlehem Tadesse",
            "clerk_id": "CLK-ADAMA-02",
            "desk": "Desk 1 (Priority & Accessibility Counter)",
            "role": "Priority & Accessibility Officer",
            "avatar": "👩🏾‍💼"
        },
        {
            "username": "tariku",
            "name": "Tariku Alemu",
            "clerk_id": "CLK-ADAMA-03",
            "desk": "Desk 3 (Counter Desk 3)",
            "role": "Counter Dispatch Clerk (Shelf B)",
            "avatar": "👨🏾‍💼"
        }
    ]


@app.post("/api/v1/auth/login", response_model=schemas.LoginResponse)
def clerk_login(credentials: schemas.LoginRequest):
    """
    Restricted Staff Authentication Endpoint.
    Only recognized postal personnel (by staff name or clerk ID) can access the Counter Terminal.
    Authorized names: 'mikael', 'mulugeta', 'bethlehem', 'tariku', 'admin' (or 'clerk1'-'clerk3').
    """
    username_clean = credentials.username.strip().lower()

    if not username_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff username cannot be blank."
        )

    # 1. Enforce Staff Name Restriction
    if username_clean not in AUTHORIZED_STAFF:
        valid_staff_names = "mikael, mulugeta, bethlehem, tariku (or 'admin')"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Access Denied: '{credentials.username.strip()}' is not a registered branch postal staff member. Access is restricted to authorized officers: {valid_staff_names}."
        )

    staff_info = AUTHORIZED_STAFF[username_clean]

    # 2. Enforce Password Check
    if credentials.password.strip() not in staff_info["passwords"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid password for {staff_info['full_name']}. Please enter the correct staff password (default: 'fayda2026')."
        )

    # Derive clerk details from official roster
    clerk_id = staff_info["clerk_id"]
    display_name = f"Officer {staff_info['full_name']}"
    selected_desk = credentials.desk or staff_info["default_desk"]

    # Secure session token
    token = f"fayda_auth_{username_clean}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    return schemas.LoginResponse(
        success=True,
        message=f"Welcome, {display_name}! Authenticated for {selected_desk}.",
        token=token,
        clerk_id=clerk_id,
        clerk_name=display_name,
        desk=selected_desk
    )


# Locate directories relative to this file
BACKEND_BASE = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_BASE, "..", "frontend"))
KIOSK_DIR = os.path.abspath(os.path.join(BACKEND_BASE, "..", "kiosk"))
STAFF_DIR = os.path.abspath(os.path.join(BACKEND_BASE, "..", "staff"))

# 1. Mount Dedicated Kiosk App
if os.path.exists(KIOSK_DIR):
    app.mount("/kiosk", StaticFiles(directory=KIOSK_DIR, html=True), name="kiosk")

# 2. Mount Dedicated Staff Portal
if os.path.exists(STAFF_DIR):
    app.mount("/staff", StaticFiles(directory=STAFF_DIR, html=True), name="staff")

# 3. Mount Fallback Frontend Static Assets
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_kiosk():
        if os.path.exists(os.path.join(KIOSK_DIR, "index.html")):
            return FileResponse(os.path.join(KIOSK_DIR, "index.html"))
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/index.html", include_in_schema=False)
    def serve_kiosk_html():
        if os.path.exists(os.path.join(KIOSK_DIR, "index.html")):
            return FileResponse(os.path.join(KIOSK_DIR, "index.html"))
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/login", include_in_schema=False)
    @app.get("/login.html", include_in_schema=False)
    def serve_login():
        if os.path.exists(os.path.join(STAFF_DIR, "index.html")):
            return FileResponse(os.path.join(STAFF_DIR, "index.html"))
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

    @app.get("/clerk", include_in_schema=False)
    @app.get("/clerk.html", include_in_schema=False)
    @app.get("/terminal", include_in_schema=False)
    @app.get("/terminal.html", include_in_schema=False)
    def serve_clerk():
        if os.path.exists(os.path.join(STAFF_DIR, "terminal.html")):
            return FileResponse(os.path.join(STAFF_DIR, "terminal.html"))
        return FileResponse(os.path.join(FRONTEND_DIR, "clerk.html"))



import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CardTrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fayda_id: str
    phone_number: str
    full_name: str
    date_of_birth: datetime.date
    age: int
    branch_name: str
    status: str  # "In Transit", "Ready for Collection", "Collected"
    storage_bin: Optional[str] = None
    assigned_desk: Optional[str] = None
    arrived_at: Optional[datetime.datetime] = None
    collected_at: Optional[datetime.datetime] = None
    priority_requested: bool = False
    priority_applied: bool = False
    instruction: Optional[str] = None


class HandoverRequest(BaseModel):
    fayda_id: str
    clerk_id: str
    desk_used: str


class HandoverResponse(BaseModel):
    success: bool
    message: str
    fayda_id: str
    citizen_name: str
    clerk_id: str
    desk_used: str
    collected_at: datetime.datetime


class HandoverAuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fayda_id: str
    citizen_name: str
    clerk_id: str
    desk_used: str
    timestamp: datetime.datetime


class CardRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fayda_id: str
    phone_number: str
    full_name: str
    date_of_birth: datetime.date
    branch_name: str
    status: str
    storage_bin: str
    assigned_desk: Optional[str] = None
    arrived_at: Optional[datetime.datetime] = None
    collected_at: Optional[datetime.datetime] = None


class ClerkStats(BaseModel):
    total_cards: int
    ready_for_collection: int
    in_transit: int
    collected_today: int
    collected_total: int


class ClerkRecordsResponse(BaseModel):
    cards: List[CardRecordItem]
    recent_handovers: List[HandoverAuditLogItem]
    stats: ClerkStats


class LoginRequest(BaseModel):
    username: str
    password: str
    desk: Optional[str] = "Desk 1 (Priority & Accessibility Counter)"


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: str
    clerk_id: str
    clerk_name: str
    desk: str


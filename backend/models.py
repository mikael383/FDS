import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime
from database import Base


class FaydaCard(Base):
    __tablename__ = "fayda_cards"

    id = Column(Integer, primary_key=True, index=True)
    fayda_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    branch_name = Column(String, default="Adama Main Post Office", nullable=False)
    status = Column(String, default="In Transit", nullable=False)  # "In Transit", "Ready for Collection", "Collected"
    storage_bin = Column(String, nullable=False)  # e.g., "Shelf A / Box 04", "Shelf B / Box 12"
    assigned_desk = Column(String, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, nullable=True)


class HandoverAuditLog(Base):
    __tablename__ = "handover_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    fayda_id = Column(String, index=True, nullable=False)
    citizen_name = Column(String, nullable=False)
    clerk_id = Column(String, nullable=False)
    desk_used = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

import datetime
from database import SessionLocal, engine, Base
import models

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def seed_database():
    db = SessionLocal()
    try:
        # Clear existing data to ensure idempotent runs
        db.query(models.HandoverAuditLog).delete()
        db.query(models.FaydaCard).delete()
        db.commit()

        now = datetime.datetime.now(datetime.timezone.utc)
        today = datetime.date.today()

        # Current year for dynamic age calculations
        curr_year = today.year

        sample_citizens = [
            # 1. Standard arrival (Shelf A -> Desk 2)
            models.FaydaCard(
                fayda_id="FAN-1029-8472-9901",
                phone_number="+251911223344",
                full_name="Abebe Bikila Kebede",
                date_of_birth=datetime.date(curr_year - 28, 4, 12),  # Age 28
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 04",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=2, hours=4),
                collected_at=None,
            ),
            # 2. Standard arrival (Shelf B -> Desk 3)
            models.FaydaCard(
                fayda_id="FAN-3849-5721-6623",
                phone_number="+251922334455",
                full_name="Selamawit Desta Haile",
                date_of_birth=datetime.date(curr_year - 33, 8, 24),  # Age 33
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf B / Box 12",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=1, hours=8),
                collected_at=None,
            ),
            # 3. Senior citizen (Age >= 60 -> Desk 1 Priority Counter)
            models.FaydaCard(
                fayda_id="FAN-7734-1920-4411",
                phone_number="+251933445566",
                full_name="Wro. Aster Lemma Tesfaye",
                date_of_birth=datetime.date(curr_year - 68, 11, 3),  # Age 68 (Senior Citizen)
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 09",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=3, hours=1),
                collected_at=None,
            ),
            # 4. In Transit card
            models.FaydaCard(
                fayda_id="FAN-9921-6634-1188",
                phone_number="+251944556677",
                full_name="Dawit Yohannes Mengistu",
                date_of_birth=datetime.date(curr_year - 25, 2, 19),  # Age 25
                branch_name="Adama Main Post Office",
                status="In Transit",
                storage_bin="Dispatch Center / Batch #409",
                assigned_desk=None,
                arrived_at=None,
                collected_at=None,
            ),
            # 5. Already Collected card
            models.FaydaCard(
                fayda_id="FAN-5512-8839-2244",
                phone_number="+251955667788",
                full_name="Tigist Worku Alemayehu",
                date_of_birth=datetime.date(curr_year - 41, 6, 15),  # Age 41
                branch_name="Adama Main Post Office",
                status="Collected",
                storage_bin="Shelf B / Box 01",
                assigned_desk="Desk 3 (Counter Desk 3)",
                arrived_at=now - datetime.timedelta(days=5),
                collected_at=now - datetime.timedelta(hours=3, minutes=20),
            ),
        ]

        db.add_all(sample_citizens)
        db.commit()

        # Add initial audit log entry for the collected citizen
        initial_log = models.HandoverAuditLog(
            fayda_id="FAN-5512-8839-2244",
            citizen_name="Tigist Worku Alemayehu",
            clerk_id="CLK-ADAMA-04",
            desk_used="Desk 3 (Counter Desk 3)",
            timestamp=now - datetime.timedelta(hours=3, minutes=20),
        )
        db.add(initial_log)
        db.commit()

        print("Database successfully seeded with 5 test citizens covering all dispatch scenarios:")
        for c in sample_citizens:
            print(f" - {c.full_name} | {c.fayda_id} | {c.phone_number} | {c.status} | {c.storage_bin}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

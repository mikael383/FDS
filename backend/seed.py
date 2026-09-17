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
        curr_year = today.year

        sample_citizens = [
            # ================================================================
            # 1. READY FOR COLLECTION: SHELF A -> DESK 2 (Standard Routing)
            # ================================================================
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
            models.FaydaCard(
                fayda_id="FAN-2045-6612-8833",
                phone_number="+251911334455",
                full_name="Meron Tadesse Girma",
                date_of_birth=datetime.date(curr_year - 24, 7, 19),  # Age 24
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 01",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=1, hours=3),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-8831-2904-7719",
                phone_number="+251911445566",
                full_name="Henok Getachew Bekele",
                date_of_birth=datetime.date(curr_year - 37, 9, 8),   # Age 37
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 15",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=3, hours=6),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-6629-4103-5582",
                phone_number="+251911556677",
                full_name="Yared Hailu Demissie",
                date_of_birth=datetime.date(curr_year - 45, 1, 30),  # Age 45
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 08",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=2, hours=9),
                collected_at=None,
            ),

            # ================================================================
            # 2. READY FOR COLLECTION: SHELF B -> DESK 3 (Standard Routing)
            # ================================================================
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
            models.FaydaCard(
                fayda_id="FAN-4920-1845-7761",
                phone_number="+251922445566",
                full_name="Binyam Kebede Assefa",
                date_of_birth=datetime.date(curr_year - 29, 3, 15),  # Age 29
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf B / Box 05",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=2, hours=1),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-3318-9042-6655",
                phone_number="+251922556677",
                full_name="Bethlehem Assefa Taye",
                date_of_birth=datetime.date(curr_year - 31, 10, 5),  # Age 31
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf B / Box 03",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=4, hours=2),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-7201-3849-1122",
                phone_number="+251922667788",
                full_name="Robel Teklu Wolde",
                date_of_birth=datetime.date(curr_year - 52, 12, 18), # Age 52
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf B / Box 18",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=1, hours=11),
                collected_at=None,
            ),

            # ================================================================
            # 3. READY FOR COLLECTION: SENIORS (Age >= 60) -> DESK 1 (Priority Counter)
            # ================================================================
            models.FaydaCard(
                fayda_id="FAN-7734-1920-4411",
                phone_number="+251933445566",
                full_name="Wro. Aster Lemma Tesfaye",
                date_of_birth=datetime.date(curr_year - 68, 11, 3),  # Age 68 (Senior)
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 09",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=3, hours=1),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-8491-0023-7744",
                phone_number="+251933556677",
                full_name="Ato Berhanu Woldeyesus",
                date_of_birth=datetime.date(curr_year - 74, 5, 21),  # Age 74 (Senior)
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf B / Box 07",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=4, hours=5),
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-6184-9923-4401",
                phone_number="+251933667788",
                full_name="Wro. Almaz Negash Kassa",
                date_of_birth=datetime.date(curr_year - 62, 8, 14),  # Age 62 (Senior)
                branch_name="Adama Main Post Office",
                status="Ready for Collection",
                storage_bin="Shelf A / Box 02",
                assigned_desk=None,
                arrived_at=now - datetime.timedelta(days=1, hours=7),
                collected_at=None,
            ),

            # ================================================================
            # 4. IN TRANSIT (Courier Delivery from Central Printing Facility)
            # ================================================================
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
            models.FaydaCard(
                fayda_id="FAN-5109-8832-7711",
                phone_number="+251944667788",
                full_name="Eden Mulatu Solomon",
                date_of_birth=datetime.date(curr_year - 27, 6, 28),  # Age 27
                branch_name="Adama Main Post Office",
                status="In Transit",
                storage_bin="Addis Logistics Hub / Batch #412",
                assigned_desk=None,
                arrived_at=None,
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-4481-9023-5599",
                phone_number="+251944778899",
                full_name="Kalkidan Fikru Belay",
                date_of_birth=datetime.date(curr_year - 30, 11, 9),  # Age 30
                branch_name="Adama Main Post Office",
                status="In Transit",
                storage_bin="National Printing Center / Batch #501",
                assigned_desk=None,
                arrived_at=None,
                collected_at=None,
            ),
            models.FaydaCard(
                fayda_id="FAN-9144-2281-0033",
                phone_number="+251944889900",
                full_name="Samuel Girma Kassahun",
                date_of_birth=datetime.date(curr_year - 39, 4, 3),   # Age 39
                branch_name="Adama Main Post Office",
                status="In Transit",
                storage_bin="Courier Transit / Truck #08",
                assigned_desk=None,
                arrived_at=None,
                collected_at=None,
            ),

            # ================================================================
            # 5. ALREADY COLLECTED (Official Handover Completed & Logged)
            # ================================================================
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
            models.FaydaCard(
                fayda_id="FAN-6689-1024-3388",
                phone_number="+251955778899",
                full_name="Mulugeta Tesfaye Gebre",
                date_of_birth=datetime.date(curr_year - 36, 1, 10),  # Age 36
                branch_name="Adama Main Post Office",
                status="Collected",
                storage_bin="Shelf A / Box 06",
                assigned_desk="Desk 2 (Counter Desk 2)",
                arrived_at=now - datetime.timedelta(days=4),
                collected_at=now - datetime.timedelta(hours=1, minutes=45),
            ),
            models.FaydaCard(
                fayda_id="FAN-7901-4432-8855",
                phone_number="+251955889900",
                full_name="Wro. Gennet Ayalew Zeleke",
                date_of_birth=datetime.date(curr_year - 65, 3, 25),  # Age 65 (Senior)
                branch_name="Adama Main Post Office",
                status="Collected",
                storage_bin="Shelf A / Box 11",
                assigned_desk="Desk 1 (Priority & Accessibility Counter)",
                arrived_at=now - datetime.timedelta(days=6),
                collected_at=now - datetime.timedelta(minutes=50),
            ),
            models.FaydaCard(
                fayda_id="FAN-8120-9943-2211",
                phone_number="+251955990011",
                full_name="Solomon Desta Birru",
                date_of_birth=datetime.date(curr_year - 48, 10, 12), # Age 48
                branch_name="Adama Main Post Office",
                status="Collected",
                storage_bin="Shelf B / Box 10",
                assigned_desk="Desk 3 (Counter Desk 3)",
                arrived_at=now - datetime.timedelta(days=7),
                collected_at=now - datetime.timedelta(days=1, hours=2),
            ),
        ]

        db.add_all(sample_citizens)
        db.commit()

        # Add realistic audit logs for all collected citizens
        audit_logs = [
            models.HandoverAuditLog(
                fayda_id="FAN-5512-8839-2244",
                citizen_name="Tigist Worku Alemayehu",
                clerk_id="CLK-ADAMA-04",
                desk_used="Desk 3 (Counter Desk 3)",
                timestamp=now - datetime.timedelta(hours=3, minutes=20),
            ),
            models.HandoverAuditLog(
                fayda_id="FAN-6689-1024-3388",
                citizen_name="Mulugeta Tesfaye Gebre",
                clerk_id="CLK-ADAMA-01",
                desk_used="Desk 2 (Counter Desk 2)",
                timestamp=now - datetime.timedelta(hours=1, minutes=45),
            ),
            models.HandoverAuditLog(
                fayda_id="FAN-7901-4432-8855",
                citizen_name="Wro. Gennet Ayalew Zeleke",
                clerk_id="CLK-ADAMA-02",
                desk_used="Desk 1 (Priority & Accessibility Counter)",
                timestamp=now - datetime.timedelta(minutes=50),
            ),
            models.HandoverAuditLog(
                fayda_id="FAN-8120-9943-2211",
                citizen_name="Solomon Desta Birru",
                clerk_id="CLK-ADAMA-03",
                desk_used="Desk 3 (Counter Desk 3)",
                timestamp=now - datetime.timedelta(days=1, hours=2),
            ),
        ]
        db.add_all(audit_logs)
        db.commit()

        print(f"Database successfully seeded with {len(sample_citizens)} test citizens across all scenarios:")
        print(f" • Ready for Collection: 11 cards (Shelf A: 6, Shelf B: 5, Seniors/Priority: 3)")
        print(f" • In Transit:           4 cards")
        print(f" • Already Collected:    4 cards with full audit records")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

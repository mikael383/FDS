"""
Comprehensive automated test suite for Fayda Postal Tracking & Desk Dispatch System.
Tests all dynamic routing logic, age calculation, priority overrides, and handover audit workflow.
"""
import sys
import os

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from seed import seed_database
import database
import models

client = TestClient(app)


def setup_module():
    """Seed fresh test data before running tests."""
    seed_database()


def test_standard_shelf_a_routing():
    """Standard citizen with Shelf A storage bin routes to Desk 2."""
    # Abebe Bikila Kebede, Age 28, Shelf A / Box 04
    resp = client.get("/api/v1/track/FAN-1029-8472-9901")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "Ready for Collection"
    assert data["assigned_desk"] == "Desk 2 (Counter Desk 2)"
    assert data["storage_bin"] == "Shelf A / Box 04"
    assert data["priority_applied"] is False


def test_standard_shelf_b_routing():
    """Standard citizen with Shelf B storage bin routes to Desk 3."""
    # Selamawit Desta Haile, Age 33, Shelf B / Box 12
    resp = client.get("/api/v1/track/FAN-3849-5721-6623")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "Ready for Collection"
    assert data["assigned_desk"] == "Desk 3 (Counter Desk 3)"
    assert data["storage_bin"] == "Shelf B / Box 12"
    assert data["priority_applied"] is False


def test_senior_citizen_priority_routing():
    """Senior citizen (Age >= 60) automatically routes to Desk 1 even with Shelf A."""
    # Wro. Aster Lemma Tesfaye, Age 68, Shelf A / Box 09
    resp = client.get("/api/v1/track/FAN-7734-1920-4411")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "Ready for Collection"
    assert data["assigned_desk"] == "Desk 1 (Priority & Accessibility Counter)"
    assert data["priority_applied"] is True
    assert data["age"] >= 60


def test_priority_request_override():
    """Citizen under 60 requesting priority checkbox routes to Desk 1 instead of standard desk."""
    # Abebe Bikila Kebede, Age 28 (Normally Desk 2)
    resp = client.get("/api/v1/track/FAN-1029-8472-9901?priority_requested=true")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "Ready for Collection"
    assert data["assigned_desk"] == "Desk 1 (Priority & Accessibility Counter)"
    assert data["priority_applied"] is True
    assert data["priority_requested"] is True


def test_search_by_phone_number():
    """Tracking by phone number works identically to Fayda ID."""
    # Selamawit's phone: +251922334455
    resp = client.get("/api/v1/track/+251922334455")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["full_name"] == "Selamawit Desta Haile"
    assert data["assigned_desk"] == "Desk 3 (Counter Desk 3)"


def test_in_transit_status():
    """In transit card displays status and guidance with NO desk assignment."""
    # Dawit Yohannes Mengistu, In Transit
    resp = client.get("/api/v1/track/FAN-9921-6634-1188")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "In Transit"
    assert data["assigned_desk"] is None
    assert "in transit" in data["instruction"].lower()


def test_already_collected_status():
    """Already collected card returns Collected status with NO desk assignment."""
    # Tigist Worku Alemayehu, Collected
    resp = client.get("/api/v1/track/FAN-5512-8839-2244")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "Collected"
    assert data["assigned_desk"] is None
    assert data["collected_at"] is not None
    assert "already collected" in data["instruction"].lower()


def test_handover_workflow_and_audit():
    """Test issuing a ready card, confirming handover, and validating audit logs."""
    # Issue Abebe's card
    payload = {
        "fayda_id": "FAN-1029-8472-9901",
        "clerk_id": "CLK-ADAMA-01",
        "desk_used": "Desk 2 (Counter Desk 2)"
    }
    resp = client.post("/api/v1/handover", json=payload)
    assert resp.status_code == 200, resp.text
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["citizen_name"] == "Abebe Bikila Kebede"

    # Verify status changed to Collected
    track_resp = client.get("/api/v1/track/FAN-1029-8472-9901")
    assert track_resp.status_code == 200
    assert track_resp.json()["status"] == "Collected"

    # Trying to issue again should fail with 400
    dup_resp = client.post("/api/v1/handover", json=payload)
    assert dup_resp.status_code == 400
    assert "Cannot issue card" in dup_resp.json()["detail"]


def test_clerk_records_and_stats():
    """Test clerk records endpoint returns card records, audit logs, and accurate statistics."""
    resp = client.get("/api/v1/clerk/records")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["cards"]) >= 5
    assert len(data["recent_handovers"]) >= 1
    stats = data["stats"]
    assert stats["total_cards"] >= 5
    assert stats["collected_total"] >= 1


if __name__ == "__main__":
    setup_module()
    test_standard_shelf_a_routing()
    test_standard_shelf_b_routing()
    test_senior_citizen_priority_routing()
    test_priority_request_override()
    test_search_by_phone_number()
    test_in_transit_status()
    test_already_collected_status()
    test_handover_workflow_and_audit()
    test_clerk_records_and_stats()
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! (9/9)")

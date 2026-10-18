import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def test_user(client):
    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    user_data = {
        "email": unique_email,
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "admin"
    }
    r = client.post("/api/v1/auth/register", json=user_data)
    assert r.status_code == 200, f"Register failed: {r.text}"
    
    r_login = client.post("/api/v1/auth/login", data={"username": unique_email, "password": "testpassword123"})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    return {"email": unique_email, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()

def test_docs_endpoint(client):
    r = client.get("/docs")
    assert r.status_code == 200

def test_user_endpoints(client, test_user):
    r = client.get("/api/v1/users/me", headers=test_user["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == test_user["email"]

    r_users = client.get("/api/v1/users/", headers=test_user["headers"])
    assert r_users.status_code == 200
    assert isinstance(r_users.json(), list)

def test_task_crud(client, test_user):
    # Create task
    task_data = {
        "title": "Automated Test Task",
        "description": "Task created during system check",
        "status": "todo",
        "priority": "high"
    }
    r = client.post("/api/v1/tasks/", json=task_data, headers=test_user["headers"])
    assert r.status_code == 200
    task_id = r.json()["id"]

    # List tasks
    r_list = client.get("/api/v1/tasks/", headers=test_user["headers"])
    assert r_list.status_code == 200
    assert any(t["id"] == task_id for t in r_list.json())

    # Update task
    r_update = client.put(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"}, headers=test_user["headers"])
    assert r_update.status_code == 200
    assert r_update.json()["status"] == "in_progress"

    # Delete task
    r_del = client.delete(f"/api/v1/tasks/{task_id}", headers=test_user["headers"])
    assert r_del.status_code == 200

def test_attendance_endpoints(client, test_user):
    # Check-in
    r_in = client.post("/api/v1/attendance/check-in", headers=test_user["headers"])
    assert r_in.status_code == 200

    # List attendance
    r_list = client.get("/api/v1/attendance/", headers=test_user["headers"])
    assert r_list.status_code == 200
    assert len(r_list.json()) > 0

    # Check-out
    r_out = client.post("/api/v1/attendance/check-out", headers=test_user["headers"])
    assert r_out.status_code == 200
    assert r_out.json()["check_out"] is not None

def test_analytics_and_ml(client, test_user):
    # Dashboard stats
    r_stats = client.get("/api/v1/analytics/dashboard-stats", headers=test_user["headers"])
    assert r_stats.status_code == 200
    assert "total_employees" in r_stats.json()
    assert "avg_productivity_score" in r_stats.json()

    # ML Productivity Prediction
    predict_data = {
        "tasks_completed": 8.0,
        "hours_worked": 40.0,
        "lines_of_code": 450.0,
        "bugs_fixed": 4.0,
        "meetings_attended": 3.0
    }
    r_pred = client.post("/api/v1/analytics/predict-productivity", json=predict_data, headers=test_user["headers"])
    assert r_pred.status_code == 200
    assert "productivity_score" in r_pred.json()
    score = r_pred.json()["productivity_score"]
    assert isinstance(score, (int, float))

def test_pdf_report(client, test_user):
    r_pdf = client.get("/api/v1/reports/productivity-report", headers=test_user["headers"])
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert len(r_pdf.content) > 100

"""
tests/test_api.py
-----------------
Integration tests for the Dashway FastAPI backend.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# StaticPool force toutes les connexions à partager la même DB en mémoire
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def register_and_login(username="testuser", password="secret123"):
    client.post("/auth/register", json={"username": username, "password": password})
    resp = client.post("/auth/login", data={"username": username, "password": password})
    return resp.json()["access_token"]


class TestHealth:
    def test_health(self):
        assert client.get("/").status_code == 200


class TestAuth:
    def test_register(self):
        r = client.post("/auth/register", json={"username": "alice", "password": "pass123"})
        assert r.status_code == 201

    def test_register_duplicate(self):
        client.post("/auth/register", json={"username": "bob", "password": "pass123"})
        r = client.post("/auth/register", json={"username": "bob", "password": "pass123"})
        assert r.status_code == 409

    def test_login_success(self):
        client.post("/auth/register", json={"username": "carol", "password": "pass123"})
        r = client.post("/auth/login", data={"username": "carol", "password": "pass123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self):
        client.post("/auth/register", json={"username": "dave", "password": "pass123"})
        r = client.post("/auth/login", data={"username": "dave", "password": "wrong"})
        assert r.status_code == 401


class TestScores:
    def test_leaderboard_empty(self):
        r = client.get("/scores/leaderboard")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_submit_valid_score(self):
        from security import compute_digest
        token  = register_and_login("player1", "pass123")
        digest = compute_digest("player1", 42, 95.0)
        r = client.post(
            "/scores/submit",
            json={"score": 42, "duration_s": 95.0, "hmac": digest},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201

    def test_submit_invalid_hmac(self):
        token = register_and_login("player2", "pass123")
        r = client.post(
            "/scores/submit",
            json={"score": 9999, "duration_s": 1.0, "hmac": "fakedigest"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_submit_without_token(self):
        r = client.post("/scores/submit", json={"score": 10, "duration_s": 30.0, "hmac": "any"})
        assert r.status_code == 401

    def test_leaderboard_after_submit(self):
        from security import compute_digest
        token  = register_and_login("player3", "pass123")
        digest = compute_digest("player3", 100, 120.0)
        client.post(
            "/scores/submit",
            json={"score": 100, "duration_s": 120.0, "hmac": digest},
            headers={"Authorization": f"Bearer {token}"},
        )
        r      = client.get("/scores/leaderboard")
        scores = [e["score"] for e in r.json()]
        assert 100 in scores

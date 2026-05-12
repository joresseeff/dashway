"""
tests/test_database.py
----------------------
Unit tests for the Database class using a temporary in-memory SQLite database.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scr"))

import pytest
from database import Database


@pytest.fixture
def db(tmp_path):
    """Return a fresh Database backed by a temp file."""
    return Database(path=str(tmp_path / "test.db"))


class TestPlayerSave:
    def test_defaults_to_zero(self, db):
        coins, bombs = db.load_player()
        assert coins == 0 and bombs == 0

    def test_save_and_load(self, db):
        db.save_player(coins=10, bombs=3)
        coins, bombs = db.load_player()
        assert coins == 10 and bombs == 3

    def test_overwrite(self, db):
        db.save_player(5, 1)
        db.save_player(99, 7)
        coins, bombs = db.load_player()
        assert coins == 99 and bombs == 7


class TestLeaderboard:
    def test_empty_best_score(self, db):
        assert db.get_best_score() == 0

    def test_add_and_get_best(self, db):
        db.add_score(42)
        db.add_score(17)
        assert db.get_best_score() == 42

    def test_top_scores_ordered(self, db):
        for s in [10, 50, 30, 20, 40]:
            db.add_score(s)
        top = db.get_top_scores()
        scores = [e["score"] for e in top]
        assert scores == sorted(scores, reverse=True)

    def test_top_scores_capped_at_5(self, db):
        for s in range(10):
            db.add_score(s * 10)
        assert len(db.get_top_scores()) <= 5

    def test_rank_field(self, db):
        db.add_score(100)
        db.add_score(50)
        top = db.get_top_scores()
        assert top[0]["rank"] == 1
        assert top[1]["rank"] == 2

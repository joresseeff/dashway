"""
database.py
-----------
Persistent storage layer for Dashway using SQLite.

Replaces the old save.txt with a proper relational database containing:
  - ``player``  : single-row table for coins and bombs inventory
  - ``scores``  : top-5 leaderboard with score, date, and session duration

Usage::

    db = Database()
    db.save_player(coins=12, bombs=3)
    coins, bombs = db.load_player()
    db.add_score(42, duration=95.3)
    top5 = db.get_top_scores()
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashway.db")


class Database:
    """Manages all read/write operations to the SQLite database.

    The database file is created automatically on first run.
    All public methods open and close their own connection so the class
    is safe to instantiate once and reuse across the whole session.

    Attributes:
        path (str): Absolute path to the .db file.
    """

    TOP_N = 5  # Number of scores kept in the leaderboard

    def __init__(self, path: str = DB_PATH) -> None:
        """Initialise the database and create tables if they don't exist.

        Args:
            path: Path to the SQLite file. Defaults to ``dashway.db``
                  one level above the ``scr/`` directory.
        """
        self.path = path
        self._init_tables()

    # ------------------------------------------------------------------
    # Player inventory (coins & bombs)
    # ------------------------------------------------------------------

    def load_player(self) -> tuple[int, int]:
        """Load the player's persisted coins and bombs.

        Returns:
            Tuple ``(coins, bombs)``. Returns ``(0, 0)`` on first run.
        """
        with self._connect() as con:
            row = con.execute(
                "SELECT coins, bombs FROM player WHERE id = 1"
            ).fetchone()
        return (row[0], row[1]) if row else (0, 0)

    def save_player(self, coins: int, bombs: int) -> None:
        """Persist the player's coins and bombs inventory.

        Uses INSERT OR REPLACE so the single player row is always
        up-to-date without needing a separate UPDATE path.

        Args:
            coins: Current coin count.
            bombs: Current bomb count.
        """
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO player (id, coins, bombs) VALUES (1, ?, ?)",
                (coins, bombs),
            )

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    def get_top_scores(self) -> list[dict]:
        """Return the top-N scores ordered from highest to lowest.

        Returns:
            List of dicts with keys ``rank``, ``score``, ``date``,
            ``duration_s``. Empty list if no scores recorded yet.
        """
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT score, date, duration_s
                FROM scores
                ORDER BY score DESC
                LIMIT ?
                """,
                (self.TOP_N,),
            ).fetchall()

        return [
            {
                "rank": i + 1,
                "score": row[0],
                "date": row[1],
                "duration_s": row[2],
            }
            for i, row in enumerate(rows)
        ]

    def get_best_score(self) -> int:
        """Return the single highest score ever recorded.

        Returns:
            Best score as an integer, or 0 if no games played yet.
        """
        with self._connect() as con:
            row = con.execute(
                "SELECT MAX(score) FROM scores"
            ).fetchone()
        return row[0] if row and row[0] is not None else 0

    def add_score(self, score: int, duration_s: float = 0.0) -> None:
        """Insert a new score entry and prune old entries beyond TOP_N.

        Args:
            score: Score achieved in the finished session.
            duration_s: Session duration in seconds (optional).
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._connect() as con:
            con.execute(
                "INSERT INTO scores (score, date, duration_s) VALUES (?, ?, ?)",
                (score, now, round(duration_s, 1)),
            )
            # Keep only the top-N rows to avoid unbounded growth
            con.execute(
                """
                DELETE FROM scores
                WHERE id NOT IN (
                    SELECT id FROM scores ORDER BY score DESC LIMIT ?
                )
                """,
                (self.TOP_N,),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with row_factory and WAL journal mode.

        Returns:
            An open sqlite3.Connection (use as context manager).
        """
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def _init_tables(self) -> None:
        """Create tables if they do not already exist."""
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS player (
                    id      INTEGER PRIMARY KEY,
                    coins   INTEGER NOT NULL DEFAULT 0,
                    bombs   INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS scores (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    score       INTEGER NOT NULL,
                    date        TEXT    NOT NULL,
                    duration_s  REAL    NOT NULL DEFAULT 0
                );
                """
            )

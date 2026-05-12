"""
api_client.py
-------------
Thin async client that submits a score to the Dashway API after a session.

The submission runs in a background thread so it never blocks the game loop.
If the API is unreachable the error is silently logged — the game continues
normally with local SQLite storage.

Configuration
-------------
Set the environment variable ``DASHWAY_API_URL`` to point at your deployed
API (default: http://localhost:8000).
Credentials are stored in the local ``dashway.db`` via the ``credentials``
table added by this module.

HMAC secret must match the value configured on the server (``HMAC_SECRET``
env var). In a production build this would be injected at compile time.
"""

import os
import hmac
import hashlib
import threading
import urllib.request
import urllib.error
import json

API_URL     = os.getenv("DASHWAY_API_URL", "http://localhost:8000")
HMAC_SECRET = os.getenv("HMAC_SECRET", "dashway-hmac-secret").encode()


def _compute_digest(username: str, score: int, duration_s: float) -> str:
    message = f"{username}:{score}:{duration_s:.1f}".encode()
    return hmac.new(HMAC_SECRET, message, hashlib.sha256).hexdigest()


def _post(url: str, payload: dict, token: str | None = None) -> dict:
    data    = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req      = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def login(username: str, password: str) -> str | None:
    """Authenticate against the API and return a JWT token.

    Args:
        username: Player username.
        password: Player password.

    Returns:
        JWT access token string, or None if login failed.
    """
    try:
        import urllib.parse
        data = urllib.parse.urlencode(
            {"username": username, "password": password}
        ).encode()
        req  = urllib.request.Request(
            f"{API_URL}/auth/login", data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read()).get("access_token")
    except Exception:
        return None


def submit_score_async(
    username: str,
    token: str,
    score: int,
    duration_s: float,
) -> None:
    """Submit a score to the API in a background thread.

    Args:
        username:   Authenticated player's username.
        token:      Valid JWT bearer token.
        score:      Score achieved this session.
        duration_s: Session duration in seconds.
    """
    def _send():
        try:
            digest  = _compute_digest(username, score, duration_s)
            payload = {"score": score, "duration_s": duration_s, "hmac": digest}
            _post(f"{API_URL}/scores/submit", payload, token=token)
        except Exception as exc:
            print(f"[api_client] Score submission failed: {exc}")

    threading.Thread(target=_send, daemon=True).start()


def get_leaderboard() -> list[dict]:
    """Fetch the global top-10 leaderboard.

    Returns:
        List of score dicts, or empty list on error.
    """
    try:
        return _get(f"{API_URL}/scores/leaderboard")
    except Exception:
        return []

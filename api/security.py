"""
security.py
-----------
HMAC-SHA256 score integrity verification (basic anti-cheat).

How it works
------------
1. Before submitting a score the game client computes:
       HMAC-SHA256(SHARED_SECRET, f"{username}:{score}:{duration_s:.1f}")
2. The digest is sent alongside the score.
3. The API recomputes the expected digest and compares it with
   ``hmac.compare_digest`` (constant-time, no timing oracle).

The shared secret is an environment variable (HMAC_SECRET) that must
match the value baked into the game client build.  This is a lightweight
deterrent — not a cryptographic guarantee — but it raises the bar for
casual score tampering significantly.
"""

import hmac
import hashlib
import os

HMAC_SECRET = os.getenv("HMAC_SECRET", "dashway-hmac-secret").encode()


def compute_digest(username: str, score: int, duration_s: float) -> str:
    """Compute the expected HMAC digest for a score submission.

    Args:
        username:   Player's username.
        score:      Claimed score value.
        duration_s: Session duration in seconds (1 decimal place).

    Returns:
        Hex-encoded HMAC-SHA256 digest string.
    """
    message = f"{username}:{score}:{duration_s:.1f}".encode()
    return hmac.new(HMAC_SECRET, message, hashlib.sha256).hexdigest()


def verify_digest(username: str, score: int, duration_s: float, digest: str) -> bool:
    """Return True if *digest* matches the expected HMAC for this submission.

    Uses ``hmac.compare_digest`` to prevent timing-based oracle attacks.

    Args:
        username:   Player's username.
        score:      Claimed score value.
        duration_s: Session duration in seconds.
        digest:     HMAC digest provided by the client.

    Returns:
        True if the digest is valid, False otherwise.
    """
    expected = compute_digest(username, score, duration_s)
    return hmac.compare_digest(expected, digest)

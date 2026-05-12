"""
main.py
-------
Dashway FastAPI application entry point.

Run locally::

    cd api
    uvicorn main:app --reload --port 8000

Swagger UI available at http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database import init_db
from routers.scores import limiter
from routers import auth, scores

app = FastAPI(
    title="Dashway API",
    description="Online leaderboard and authentication for the Dashway arcade game.",
    version="1.0.0",
    docs_url="/docs",
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS (allow the game client and any future web frontend) ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(scores.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", tags=["health"])
def health():
    """Health-check endpoint."""
    return {"status": "ok", "game": "Dashway"}

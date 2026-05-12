"""
database.py
-----------
SQLAlchemy models and session factory for the Dashway API.

Tables
------
users  — registered players (id, username, hashed_password, created_at)
scores — submitted scores   (id, user_id, score, duration_s, hmac, submitted_at)
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker, Session


DATABASE_URL = "sqlite:///./dashway_api.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(32), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("Score", back_populates="user")


class Score(Base):
    __tablename__ = "scores"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    score        = Column(Integer, nullable=False)
    duration_s   = Column(Float, default=0.0)
    hmac_digest  = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scores")


def get_db():
    """FastAPI dependency that yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)

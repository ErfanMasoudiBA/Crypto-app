"""
Database configuration and session management for the unified API application.

This module handles database initialization, connection management,
and provides session generators for dependency injection.
"""

from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")

# Use SQLite-specific connect args only when using SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )


def create_db_and_tables() -> None:
    """Create database tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Database session generator for dependency injection.
    
    Yields:
        Session: SQLModel database session
    """
    with Session(engine) as session:
        yield session
import os
import atexit
from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
from dotenv import load_dotenv


load_dotenv()

# Modern, centralized database configuration
# Use DATABASE_URL for Neon compatibility, with fallbacks for existing envs
DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("LOG_PG_DSN", "postgresql://ruh:ruhpass@localhost:5432/happyruh"))

# SQLAlchemy setup for ORM-based interactions (used by logger and new models)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Connection Pool for raw psycopg access ---
# Use a connection pool for efficient, thread-safe connection management.
# This is a best practice for server applications and serverless environments.
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=2,  # Start with a few connections ready
    max_size=10, # Max concurrent connections
    open=True,
    # name for monitoring
    name="happyruh-pool",
)

# Ensure the pool is closed when the application exits
atexit.register(pool.close)

@contextmanager
def get_db_session():
    """Provides a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_connection():
    """
    Provides a raw psycopg connection from the pool.
    The connection is automatically returned to the pool.
    """
    with pool.connection() as conn:
        yield conn

def create_tables():
    """
    Creates all tables defined in the models module.
    This is idempotent and can be run safely on startup.
    """
    from . import models
    print("Attempting to create database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created or already exist.")
    except Exception as e:
        print(f"Error creating tables: {e}")

# For FastAPI dependency injection, if needed
def get_db():
    """FastAPI dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
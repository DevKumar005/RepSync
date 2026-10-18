import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# Load root .env
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./repsync.db"
DATABASE_URL = DATABASE_URL.strip().strip('"').strip("'")

# Clean pgbouncer parameter which is unsupported by psycopg3 libpq parser
if "pgbouncer=true" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

# Render / Supabase compatibility: convert postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)



connect_args = {}
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Supabase / PgBouncer transaction pooler settings (disables prepared statements)
    connect_args = {"prepare_threshold": None}
    engine_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)



def init_db() -> None:
    """Create all SQLModel tables in database."""
    # Ensure all models are registered
    import backend.app.models.entities  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    with Session(engine) as session:
        yield session

from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# For SQLite compatibility, add connect_args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL, 
    echo=False, 
    connect_args=connect_args
)

def create_db_and_tables():
    """Build all schemas in PostgreSQL/SQLite database."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Session generator injected into FastAPI routes."""
    with Session(engine) as session:
        yield session

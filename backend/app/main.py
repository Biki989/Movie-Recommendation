from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import User
from app.auth import hash_password
from app.routes import auth, movies, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook managing startup database initialization and seeds."""
    # 1. Build PostgreSQL or SQLite tables
    create_db_and_tables()
    
    # 2. Seed Default Administrator Account if none exists (safe check)
    with Session(engine) as session:
        admin_exists = session.query(User).filter(User.is_admin == True).first()
        if not admin_exists:
            hashed_pw = hash_password("Mistbigg4010")
            default_admin = User(
                username="admin",
                email="bikikalita1000@gmail.com",
                password=hashed_pw,
                is_admin=True
            )
            session.add(default_admin)
            session.commit()
            print("[App Startup] Seeded default administrator -> bikikalita1000@gmail.com / [ENCRYPTED]")
            
    yield
    # Clean up operations on shutdown go here
    print("[App Shutdown] Shutting down web app cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Decoupled high-performance movie recommendation engine api utilizing PyTorch NCF.",
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS POLICY CONFIGURATION ─────────────────────────────────────────────────
# Restricts access strictly to Next.js default dev and prod hosts
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Mandatory to support HttpOnly session cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ── ROUTE REGISTRATIONS ────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(movies.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# ── GLOBAL SYSTEM EXCEPTION SECURE WRAPPER ────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all secure handler.
    Prevents raw trace information from leaking to attackers in HTTP responses.
    """
    # In full production log this exception to Sentry/Cloudwatch internally
    print(f"[SECURITY UNHANDLED ERROR] {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A critical system error occurred. Please contact support."}
    )


@app.get("/api/health")
async def health_check():
    """Verify backend server liveliness."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

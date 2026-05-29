import os
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlmodel import Session

from app.database import get_session
from app.models import User, UserRating, Bookmark
from app.auth import get_current_admin
from app.config import settings
import app.services.recommender as rec

try:
    from app.services.train_job import train_model, HISTORY_PATH
except ImportError:
    train_model = None
    _routes_dir = os.path.dirname(os.path.abspath(__file__))
    _app_dir    = os.path.dirname(_routes_dir)
    MODEL_DIR   = os.path.join(_app_dir, "models")
    HISTORY_PATH = os.path.join(MODEL_DIR, "training_history.json")

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# Global thread-safe-like memory progress state for background retraining
_training_status = {"running": False, "message": "idle", "progress": 0}


def _run_async_retraining(progress_callback):
    """Executes full retraining and forces recommendation cache reload on complete."""
    global _training_status
    try:
        train_model(progress_callback=progress_callback)
        # Force reload loaded PyTorch state in the recommender module
        rec.force_reload_model()
    except Exception as e:
        _training_status = {"running": False, "message": f"Retrain Error: {str(e)}", "progress": 0}


def update_progress_callback(message: str, progress: int):
    """Callback triggered from PyTorch train loops."""
    global _training_status
    _training_status["message"] = message
    _training_status["progress"] = progress
    if progress >= 100:
        _training_status["running"] = False


# ── ROUTE ENDPOINTS ───────────────────────────────────────────────────────────

@router.get("/stats")
async def get_system_stats(
    admin_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """Fetch database metrics for admin dashboard panel."""
    return {
        "total_users": session.query(User).count(),
        "total_ratings": session.query(UserRating).count(),
        "total_bookmarks": session.query(Bookmark).count(),
        "model_ready": rec.is_model_ready()
    }


@router.post("/retrain")
async def trigger_retraining(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_current_admin)
):
    """Triggers asynchronous PyTorch model retraining in background tasks thread pool."""
    global _training_status
    if train_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model training is not supported in the serverless production environment. Please run retraining locally."
        )
    if _training_status["running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A training job is already actively running."
        )
        
    _training_status = {"running": True, "message": "Queueing preprocessing job…", "progress": 5}
    
    # Offload heavy computing to FastAPI BackgroundTasks worker pool
    background_tasks.add_task(_run_async_retraining, update_progress_callback)
    
    return {"success": True, "message": "Model retraining initialized in background."}


@router.get("/training-status")
async def get_training_status(admin_user: User = Depends(get_current_admin)):
    """Poll current background training progress state."""
    return _training_status


@router.get("/training-history")
async def get_training_history(admin_user: User = Depends(get_current_admin)):
    """Retrieve historical loss/MAE JSON metrics to build graphs."""
    if not os.path.exists(HISTORY_PATH):
        return {"loss": [], "val_loss": [], "mae": [], "val_mae": []}
        
    try:
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load training history: {str(e)}"
        )

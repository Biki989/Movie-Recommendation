import os
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import RedirectResponse, FileResponse
from sqlmodel import Session

from app.database import get_session
from app.models import (
    User, UserRating, Bookmark, RecHistory, 
    RatingCreate, BookmarkCreate, BookmarkResponse, RatingResponse
)
from app.auth import get_current_user
from app.config import settings
import app.services.recommender as rec

router = APIRouter(prefix="/movies", tags=["Movies"])

# ── POSTER SECURE PROXY ENDPOINT ──────────────────────────────────────────────

@router.get("/poster")
async def get_movie_poster(title: str):
    """
    Secure backend image proxy endpoint.
    Hides TMDB_API_KEY from the frontend and fetches posters on-demand.
    """
    placeholder_path = os.path.join(settings.BASE_DIR, "..", "static", "images", "placeholder.png")
    
    if not settings.TMDB_API_KEY:
        if os.path.exists(placeholder_path):
            return FileResponse(placeholder_path, media_type="image/png")
        return Response(status_code=404)
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": settings.TMDB_API_KEY, "query": title, "language": "en-US"},
                timeout=2.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results and results[0].get("poster_path"):
                    poster_path = results[0]["poster_path"]
                    return RedirectResponse(url=f"https://image.tmdb.org/t/p/w500{poster_path}")
    except Exception:
        pass
        
    if os.path.exists(placeholder_path):
        return FileResponse(placeholder_path, media_type="image/png")
    return Response(status_code=404)


# ── CORE MOVIE RECS & SEARCH ENDPOINTS ────────────────────────────────────────

@router.get("/trending")
async def get_trending():
    """Fetch top trending movies approved by model scoring approximation."""
    if not rec.is_model_ready():
        return []
    try:
        return rec.get_trending_movies(top_n=24)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load trending list: {str(e)}"
        )


@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    """Search movies by title query."""
    try:
        return rec.search_movies(q, limit=20)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/recommendations")
async def get_recommendations(
    genre: Optional[str] = None,
    limit: int = 24,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate personalized neural collaborative filtering recommendations."""
    if not rec.is_model_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not trained yet. Admin action required."
        )
        
    try:
        recs = rec.get_recommendations(
            user_id=current_user.id, 
            top_n=limit, 
            genre_filter=genre
        )
        
        # Persist top 10 recommendations to user watch/recommendation history
        for r in recs[:10]:
            history_entry = RecHistory(
                user_id=current_user.id,
                movie_id=r["movieId"],
                title=r["title"],
                genres=r["genres"],
                confidence=r.get("confidence_pct", 0.0)
            )
            session.add(history_entry)
        session.commit()
        
        return recs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation engine error: {str(e)}"
        )


# ── RATING & BOOKMARKING USER ACTIONS ─────────────────────────────────────────

@router.post("/rate")
async def rate_movie(
    payload: RatingCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit or edit rating for a specific movie."""
    if not (0.5 <= payload.rating <= 5.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be a value between 0.5 and 5.0."
        )
        
    # Check if rating already exists for this user/movie combo
    existing = session.query(UserRating).filter(
        UserRating.user_id == current_user.id,
        UserRating.movie_id == payload.movie_id
    ).first()
    
    if existing:
        existing.rating = payload.rating
    else:
        new_rating = UserRating(
            user_id=current_user.id,
            movie_id=payload.movie_id,
            title=payload.title,
            genres=payload.genres,
            rating=payload.rating
        )
        session.add(new_rating)
        
    session.commit()
    return {"success": True, "message": "Rating updated."}


@router.post("/bookmark")
async def toggle_bookmark(
    payload: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Toggle bookmark status of a movie."""
    existing = session.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.movie_id == payload.movie_id
    ).first()
    
    if existing:
        session.delete(existing)
        session.commit()
        return {"success": True, "bookmarked": False}
    else:
        new_bookmark = Bookmark(
            user_id=current_user.id,
            movie_id=payload.movie_id,
            title=payload.title,
            genres=payload.genres
        )
        session.add(new_bookmark)
        session.commit()
        return {"success": True, "bookmarked": True}


@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_bookmarks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrieve current user's bookmarked movies."""
    return session.query(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).order_by(Bookmark.bookmarked_at.desc()).all()


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrieve current user's personalized recommendation log."""
    history = session.query(RecHistory).filter(
        RecHistory.user_id == current_user.id
    ).order_by(RecHistory.recommended_at.desc()).limit(50).all()
    
    return [
        {
            "movieId": h.movie_id,
            "title": h.title,
            "genres": h.genres,
            "confidence": h.confidence,
            "recommended_at": h.recommended_at.strftime("%b %d, %Y %H:%M")
        }
        for h in history
    ]


@router.get("/genres")
async def get_genres():
    """Retrieve all unique genres present in the database."""
    try:
        return rec.get_all_genres()
    except Exception:
        return []

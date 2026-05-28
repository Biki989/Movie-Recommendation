"use client";

import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function MovieCard({ 
  movie, 
  initialBookmarked = false,
  showConfidence = false,
  onBookmarkToggled = null
}) {
  const { user } = useAuth();
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [hoverRating, setHoverRating] = useState(0);
  const [userRating, setUserRating] = useState(0);
  const [ratingMessage, setRatingMessage] = useState("");

  const handleBookmarkToggle = async (e) => {
    e.stopPropagation();
    if (!user) {
      alert("Please sign in to bookmark movies!");
      return;
    }
    
    try {
      const resp = await fetch("http://localhost:8000/api/movies/bookmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movie_id: movie.movieId,
          title: movie.title,
          genres: movie.genres
        }),
        credentials: "include"
      });
      if (resp.status === 200) {
        const data = await resp.json();
        setBookmarked(data.bookmarked);
        if (onBookmarkToggled) {
          onBookmarkToggled(movie.movieId, data.bookmarked);
        }
      }
    } catch (e) {}
  };

  const handleRateSubmit = async (stars, e) => {
    e.stopPropagation();
    if (!user) {
      alert("Please sign in to rate movies!");
      return;
    }
    
    try {
      const resp = await fetch("http://localhost:8000/api/movies/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movie_id: movie.movieId,
          title: movie.title,
          genres: movie.genres,
          rating: stars
        }),
        credentials: "include"
      });
      if (resp.status === 200) {
        setUserRating(stars);
        setRatingMessage(`Rated ${stars} ⭐`);
        setTimeout(() => setRatingMessage(""), 2000);
      }
    } catch (e) {}
  };

  const posterUrl = `http://localhost:8000/api/movies/poster?title=${encodeURIComponent(movie.title)}`;

  return (
    <div className="movie-card animate-fade-in">
      <div className="poster-container">
        <img 
          src={posterUrl} 
          alt={movie.title} 
          className="poster-image" 
          loading="lazy"
        />
        <div className="card-overlay">
          {showConfidence && movie.confidence_pct !== undefined && (
            <div className="badge-confidence">
              🤖 {movie.confidence_pct}%
            </div>
          )}
          <button 
            className={`bookmark-btn ${bookmarked ? "active" : ""}`} 
            onClick={handleBookmarkToggle}
            title={bookmarked ? "Remove Bookmark" : "Bookmark Movie"}
          >
            {bookmarked ? "❤️" : "🤍"}
          </button>
        </div>
      </div>
      
      <div className="movie-info">
        <h3 className="movie-title" title={movie.title}>{movie.title}</h3>
        <span className="movie-genres">{movie.genres}</span>
        
        {/* Progress Confidence bar if requested */}
        {showConfidence && movie.confidence_pct !== undefined && (
          <div style={{ marginBottom: "0.8rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600 }}>
              <span>AI Confidence</span>
              <span>{movie.confidence_pct}%</span>
            </div>
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${movie.confidence_pct}%` }}></div>
            </div>
          </div>
        )}

        <div className="movie-footer">
          {/* Average/Predicted Rating */}
          <div className="rating-display">
            ⭐ {movie.predicted_rating || movie.avg_score || "N/A"}
          </div>
          
          {/* Interactive User Rating Stars */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            {ratingMessage ? (
              <span style={{ fontSize: "0.75rem", color: "var(--accent)", fontWeight: 700 }}>{ratingMessage}</span>
            ) : (
              <div style={{ display: "flex", gap: "0.1rem" }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <span
                    key={star}
                    style={{ 
                      cursor: "pointer", 
                      fontSize: "0.85rem",
                      color: star <= (hoverRating || userRating) ? "var(--accent)" : "var(--text-dimmed)",
                      transition: "color 0.1s ease"
                    }}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={(e) => handleRateSubmit(star, e)}
                  >
                    ★
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

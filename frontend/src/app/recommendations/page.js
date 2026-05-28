"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import MovieCard from "../components/MovieCard";

export default function Recommendations() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [recs, setRecs] = useState([]);
  const [genres, setGenres] = useState([]);
  const [activeGenre, setActiveGenre] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Route protection gate
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading]);

  // Fetch unique genres on load
  useEffect(() => {
    if (!user) return;
    async function fetchGenres() {
      try {
        const resp = await fetch("http://localhost:8000/api/movies/genres");
        if (resp.status === 200) {
          const data = await resp.json();
          setGenres(["All", ...data]);
        }
      } catch (e) {}
    }
    fetchGenres();
  }, [user]);

  // Query personalized recommendations when activeGenre changes
  useEffect(() => {
    if (!user) return;
    
    async function fetchRecs() {
      setLoading(true);
      setError("");
      try {
        const url = activeGenre === "All" 
          ? "http://localhost:8000/api/movies/recommendations"
          : `http://localhost:8000/api/movies/recommendations?genre=${encodeURIComponent(activeGenre)}`;
          
        const resp = await fetch(url, { credentials: "include" });
        if (resp.status === 200) {
          const data = await resp.json();
          setRecs(data);
        } else if (resp.status === 503) {
          setError("The Neural Recommender model is currently offline. Please ask an Administrator to retrain the model.");
        } else {
          setError("Failed to fetch recommendation feed.");
        }
      } catch (e) {
        setError("Network connection to FastAPI server failed.");
      } finally {
        setLoading(false);
      }
    }
    
    fetchRecs();
  }, [user, activeGenre]);

  if (authLoading || !user) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "8rem 0" }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "2rem", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.8rem", fontWeight: 800 }}>✨ Handpicked For You</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          NCF AI Collaborative recommendations matching your taste and favorite genres
        </p>
      </div>

      <div className="sidebar-layout">
        {/* Genre Sidebar Selector */}
        <div className="glass-panel" style={{ height: "fit-content", padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.1rem", textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.05em", marginBottom: "1rem" }}>
            🎭 Filter by Genre
          </h3>
          <div className="sidebar-menu">
            {genres.length > 0 ? (
              genres.map((g) => (
                <button
                  key={g}
                  className={`sidebar-btn ${activeGenre === g ? "active" : ""}`}
                  onClick={() => setActiveGenre(g)}
                >
                  {g === "All" ? "⭐" : "🎬"} {g}
                </button>
              ))
            ) : (
              // Fallback default list if database is initializing
              ["All", "Action", "Adventure", "Comedy", "Drama", "Sci-Fi", "Thriller"].map((g) => (
                <button
                  key={g}
                  className={`sidebar-btn ${activeGenre === g ? "active" : ""}`}
                  onClick={() => setActiveGenre(g)}
                >
                  🎬 {g}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Recommendations Card Grid */}
        <div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
              <div className="spinner"></div>
            </div>
          ) : error ? (
            <div className="glass-panel" style={{ textAlign: "center", padding: "4rem 2rem", border: "1px solid var(--primary)" }}>
              <span style={{ fontSize: "3rem" }}>⚠️</span>
              <h3 style={{ marginTop: "1rem", color: "#ff8080" }}>NCF Engine Offline</h3>
              <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "0.5rem", maxWidth: "480px", margin: "0.5rem auto 0" }}>
                {error}
              </p>
            </div>
          ) : recs.length > 0 ? (
            <div className="movie-grid" style={{ marginTop: 0 }}>
              {recs.map((movie) => (
                <MovieCard 
                  key={movie.movieId} 
                  movie={movie} 
                  showConfidence={true}
                />
              ))}
            </div>
          ) : (
            <div className="glass-panel" style={{ textAlign: "center", padding: "4rem 2rem" }}>
              <span style={{ fontSize: "3rem" }}>🎬</span>
              <h3 style={{ marginTop: "1rem" }}>No recommendations matched</h3>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Try selecting another genre or submitting star ratings.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

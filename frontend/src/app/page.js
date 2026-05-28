"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "./context/AuthContext";
import MovieCard from "./components/MovieCard";

export default function Home() {
  const { user } = useAuth();
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch trending movies on load
  useEffect(() => {
    async function fetchTrending() {
      try {
        const resp = await fetch("http://localhost:8000/api/movies/trending");
        if (resp.status === 200) {
          const data = await resp.json();
          setTrending(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchTrending();
  }, []);

  return (
    <div className="container">
      {/* ── HERO BANNER SECTION ────────────────────────────────────────────────── */}
      <section style={{ 
        position: "relative",
        padding: "6rem 0",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        borderBottom: "1px solid var(--border-light)",
        marginBottom: "4rem"
      }}>
        <div style={{ position: "absolute", zIndex: -1, top: 0, opacity: 0.1, pointerEvents: "none" }}>
          <span style={{ fontSize: "15rem" }}>🎬</span>
        </div>
        
        <h1 className="text-gradient" style={{ fontSize: "4.2rem", lineHeight: "1.1", fontWeight: 900, marginBottom: "1.5rem" }}>
          Infinite Stories.<br/>Personalized for You.
        </h1>
        <p style={{ fontSize: "1.25rem", color: "var(--text-muted)", maxWidth: "650px", marginBottom: "2.5rem" }}>
          Discover movies you'll love with CinematIX's state-of-the-art **Neural Collaborative Filtering** recommendation engine. Powered by PyTorch.
        </p>
        
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", justifyContent: "center" }}>
          {user ? (
            <Link href="/recommendations" className="btn btn-primary" style={{ padding: "1rem 2.5rem", fontSize: "1.1rem" }}>
              ✨ Go to Feed
            </Link>
          ) : (
            <>
              <Link href="/register" className="btn btn-primary" style={{ padding: "1rem 2.5rem", fontSize: "1.1rem" }}>
                🚀 Start Free Now
              </Link>
              <Link href="/login" className="btn" style={{ padding: "1rem 2.5rem", fontSize: "1.1rem" }}>
                🔑 Sign In
              </Link>
            </>
          )}
        </div>
      </section>

      {/* ── TRENDING / TOP RATED SECTION ──────────────────────────────────────── */}
      <section className="animate-fade-in">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h2 style={{ fontSize: "2rem", fontWeight: 800 }}>🔥 Trending Movies</h2>
            <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>Popular movies estimated by collaborative rating predictions</p>
          </div>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
            <div className="spinner"></div>
          </div>
        ) : trending.length > 0 ? (
          <div className="movie-grid">
            {trending.map((movie) => (
              <MovieCard 
                key={movie.movieId} 
                movie={movie} 
                showConfidence={false}
              />
            ))}
          </div>
        ) : (
          <div className="glass-panel" style={{ textAlign: "center", padding: "4rem 2rem" }}>
            <span style={{ fontSize: "3rem" }}>📭</span>
            <h3 style={{ marginTop: "1rem" }}>No trending movies loaded</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Please trigger PyTorch model training via Admin Panel.</p>
          </div>
        )}
      </section>
    </div>
  );
}

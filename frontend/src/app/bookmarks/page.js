"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import MovieCard from "../components/MovieCard";
import { API_BASE } from "../config";

export default function Bookmarks() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Route protection
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading]);

  // Fetch bookmarks
  useEffect(() => {
    if (!user) return;
    async function fetchBookmarks() {
      try {
        const resp = await fetch(`${API_BASE}/api/movies/bookmarks`, { credentials: "include" });
        if (resp.status === 200) {
          const data = await resp.json();
          setBookmarks(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchBookmarks();
  }, [user]);

  const handleBookmarkRemoved = (movieId, isBookmarked) => {
    if (!isBookmarked) {
      // Filter out removed bookmarks from current React state
      setBookmarks((prev) => prev.filter((b) => b.movie_id !== movieId));
    }
  };

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
        <h1 style={{ fontSize: "2.8rem", fontWeight: 800 }}>❤️ Your Watchlist</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Saves and favorites you have bookmarked for later viewing
        </p>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
          <div className="spinner"></div>
        </div>
      ) : bookmarks.length > 0 ? (
        <div className="movie-grid" style={{ marginTop: 0 }}>
          {bookmarks.map((b) => (
            <MovieCard 
              key={b.id} 
              movie={{
                movieId: b.movie_id,
                title: b.title,
                genres: b.genres
              }} 
              initialBookmarked={true}
              showConfidence={false}
              onBookmarkToggled={handleBookmarkRemoved}
            />
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ textAlign: "center", padding: "6rem 2rem" }}>
          <span style={{ fontSize: "3.5rem" }}>❤️</span>
          <h3 style={{ marginTop: "1rem", fontSize: "1.5rem" }}>Your Watchlist is empty</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "0.5rem" }}>
            Add movies to your bookmarks to keep track of what to watch next!
          </p>
        </div>
      )}
    </div>
  );
}

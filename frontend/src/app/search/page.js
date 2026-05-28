"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import MovieCard from "../components/MovieCard";

function SearchResultsContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!query) {
      setResults([]);
      setLoading(false);
      return;
    }

    async function fetchSearch() {
      setLoading(true);
      setError("");
      try {
        const resp = await fetch(`http://localhost:8000/api/movies/search?q=${encodeURIComponent(query)}`);
        if (resp.status === 200) {
          const data = await resp.json();
          setResults(data);
        } else {
          setError("Failed to fetch search results.");
        }
      } catch (e) {
        setError("Connection to backend server failed.");
      } finally {
        setLoading(false);
      }
    }

    fetchSearch();
  }, [query]);

  return (
    <div className="container">
      <div style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "2rem", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.8rem", fontWeight: 800 }}>🔍 Search Results</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Showing movies matching the query: <span style={{ color: "#fff", fontWeight: 700 }}>"{query}"</span>
        </p>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
          <div className="spinner"></div>
        </div>
      ) : error ? (
        <div className="glass-panel" style={{ textAlign: "center", padding: "4rem 2rem", border: "1px solid var(--primary)" }}>
          <span style={{ fontSize: "3rem" }}>⚠️</span>
          <h3 style={{ marginTop: "1rem", color: "#ff8080" }}>Search failed</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>{error}</p>
        </div>
      ) : results.length > 0 ? (
        <div className="movie-grid" style={{ marginTop: 0 }}>
          {results.map((movie) => (
            <MovieCard 
              key={movie.movieId} 
              movie={movie} 
              showConfidence={false}
            />
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ textAlign: "center", padding: "6rem 2rem" }}>
          <span style={{ fontSize: "3.5rem" }}>📂</span>
          <h3 style={{ marginTop: "1rem", fontSize: "1.5rem" }}>No movies matched</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "0.5rem" }}>
            We couldn't find any movies matching your search query. Try searching for "Inception", "Godfather", or "Matrix".
          </p>
        </div>
      )}
    </div>
  );
}

export default function SearchResults() {
  return (
    <Suspense fallback={
      <div className="container" style={{ display: "flex", justifyContent: "center", padding: "8rem 0" }}>
        <div className="spinner"></div>
      </div>
    }>
      <SearchResultsContent />
    </Suspense>
  );
}

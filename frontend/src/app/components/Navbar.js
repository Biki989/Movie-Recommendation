"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { API_BASE } from "../config";

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const searchRef = useRef(null);
  const userMenuRef = useRef(null);

  // Close dropdowns on outside clicks
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setSuggestions([]);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced AJAX suggestion query
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/movies/search?q=${encodeURIComponent(searchQuery)}`);
        if (resp.status === 200) {
          const data = await resp.json();
          setSuggestions(data);
        }
      } catch (e) {}
    }, 200);

    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSuggestions([]);
    }
  };

  const selectSuggestion = (movieTitle) => {
    setSearchQuery(movieTitle);
    router.push(`/search?q=${encodeURIComponent(movieTitle)}`);
    setSuggestions([]);
  };

  return (
    <nav className="navbar">
      <div className="container navbar-content">
        {/* Brand Logo */}
        <Link href="/" className="logo">
          🎬 CinematIX <span className="ai-badge">AI</span>
        </Link>

        {/* Live Suggestion Search */}
        <form onSubmit={handleSearchSubmit} className="nav-search-form" style={{ position: "relative", width: "40%", maxWidth: "450px" }} ref={searchRef}>
          <div style={{ display: "flex", width: "100%", position: "relative" }}>
            <input
              type="text"
              className="input-field"
              placeholder="🔍 Search movies..."
              style={{ paddingRight: "40px", borderRadius: suggestions.length > 0 ? "8px 8px 0 0" : "8px" }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {suggestions.length > 0 && (
              <div className="suggestions-box">
                {suggestions.map((m) => (
                  <div key={m.movieId} className="suggestion-item" onClick={() => selectSuggestion(m.title)}>
                    <span style={{ fontWeight: 600 }}>{m.title}</span>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-dimmed)" }}>{m.genres}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </form>

        {/* Nav Links */}
        <div className="nav-links">
          <Link href="/" className={`nav-link ${pathname === "/" ? "active" : ""}`}>
            Home
          </Link>
          
          {user ? (
            <>
              <Link href="/recommendations" className={`nav-link ${pathname.startsWith("/recommendations") ? "active" : ""}`}>
                For You
              </Link>
              <Link href="/bookmarks" className={`nav-link ${pathname.startsWith("/bookmarks") ? "active" : ""}`}>
                Bookmarks
              </Link>
              
              {/* User Avatar & Menu */}
              <div className="user-badge" style={{ position: "relative" }} onClick={() => setShowUserMenu(!showUserMenu)} ref={userMenuRef}>
                <div className="avatar-circle">{user.username[0].toUpperCase()}</div>
                <span>{user.username}</span>
                
                {showUserMenu && (
                  <div className="glass-panel" style={{ 
                    position: "absolute", 
                    top: "120%", 
                    right: 0, 
                    width: "220px", 
                    padding: "1rem", 
                    zIndex: 101, 
                    display: "flex", 
                    flexDirection: "column", 
                    gap: "0.75rem",
                    boxShadow: "var(--shadow-premium)"
                  }}>
                    <div style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "0.5rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Logged in as</span>
                      <span style={{ fontWeight: 700, fontSize: "0.85rem", overflow: "hidden", textOverflow: "ellipsis", display: "block" }}>{user.email}</span>
                    </div>
                    <Link href="/history" className="sidebar-btn" style={{ padding: "0.4rem 0.5rem" }}>
                      ⏳ Watch History
                    </Link>
                    {user.is_admin && (
                      <Link href="/dashboard" className="sidebar-btn" style={{ padding: "0.4rem 0.5rem", color: "var(--accent)" }}>
                        ⚙️ Admin Panel
                      </Link>
                    )}
                    <button onClick={logout} className="btn btn-primary" style={{ padding: "0.4rem", fontSize: "0.8rem", width: "100%" }}>
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div style={{ display: "flex", gap: "1rem" }}>
              <Link href="/login" className="btn" style={{ padding: "0.5rem 1.2rem", fontSize: "0.85rem" }}>
                Sign In
              </Link>
              <Link href="/register" className="btn btn-primary" style={{ padding: "0.5rem 1.2rem", fontSize: "0.85rem" }}>
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, login, loading: authLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (user && !authLoading) {
      router.push("/recommendations");
    }
  }, [user, authLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    
    if (!email.trim() || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setSubmitting(true);
    const result = await login(email, password);
    setSubmitting(false);

    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "70vh", padding: "2rem 0" }}>
      <div className="glass-panel animate-fade-in" style={{ width: "100%", maxWidth: "450px" }}>
        <h2 className="text-gradient" style={{ fontSize: "2.2rem", fontWeight: 800, textAlign: "center", marginBottom: "0.5rem" }}>
          Welcome Back
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", marginBottom: "2rem" }}>
          Sign in to access your neural movie recommendations
        </p>

        {error && (
          <div style={{ 
            background: "rgba(229, 9, 20, 0.15)", 
            border: "1px solid var(--primary)", 
            color: "#ff8080", 
            padding: "0.75rem 1rem", 
            borderRadius: "8px", 
            fontSize: "0.85rem",
            fontWeight: 600,
            marginBottom: "1.5rem",
            animation: "fadeIn 0.2s ease"
          }}>
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div>
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "0.4rem" }}>
              Email Address
            </label>
            <input
              type="email"
              className="input-field"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
              <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                Password
              </label>
            </div>
            <input
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%", padding: "0.9rem", fontSize: "1rem", marginTop: "1rem" }} disabled={submitting}>
            {submitting ? <div className="spinner" style={{ width: "18px", height: "18px" }}></div> : "Sign In"}
          </button>
        </form>

        <p style={{ marginTop: "2rem", textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          New to CinematIX?{" "}
          <Link href="/register" style={{ color: "var(--primary)", fontWeight: 700, textDecoration: "underline" }}>
            Create Account
          </Link>
        </p>
      </div>
    </div>
  );
}

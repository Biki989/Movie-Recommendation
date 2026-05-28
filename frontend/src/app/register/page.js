"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { user, register, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  
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

    // Input Validations
    if (!username.trim() || !email.trim() || !password || !confirm) {
      setError("Please fill in all fields.");
      return;
    }
    
    if (username.length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    const result = await register(username.trim(), email.trim(), password);
    setSubmitting(false);

    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="container" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh", padding: "3rem 0" }}>
      <div className="glass-panel animate-fade-in" style={{ width: "100%", maxWidth: "450px" }}>
        <h2 className="text-gradient" style={{ fontSize: "2.2rem", fontWeight: 800, textAlign: "center", marginBottom: "0.5rem" }}>
          Get Started
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", marginBottom: "2rem" }}>
          Create an account to personalize your cinematic feed
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
              Username
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="movielover99"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

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
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "0.4rem" }}>
              Password
            </label>
            <input
              type="password"
              className="input-field"
              placeholder="Min 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "0.4rem" }}>
              Confirm Password
            </label>
            <input
              type="password"
              className="input-field"
              placeholder="Re-type password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%", padding: "0.9rem", fontSize: "1rem", marginTop: "1rem" }} disabled={submitting}>
            {submitting ? <div className="spinner" style={{ width: "18px", height: "18px" }}></div> : "Create Account"}
          </button>
        </form>

        <p style={{ marginTop: "2rem", textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--primary)", fontWeight: 700, textDecoration: "underline" }}>
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}

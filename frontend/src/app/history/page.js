"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function History() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Route protection
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading]);

  // Fetch watch history log
  useEffect(() => {
    if (!user) return;
    async function fetchHistory() {
      try {
        const resp = await fetch("http://localhost:8000/api/movies/history", { credentials: "include" });
        if (resp.status === 200) {
          const data = await resp.json();
          setHistory(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [user]);

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
        <h1 style={{ fontSize: "2.8rem", fontWeight: 800 }}>⏳ Recommendation History</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Audit log of AI predictions generated for your session and logged to database
        </p>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
          <div className="spinner"></div>
        </div>
      ) : history.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {history.map((h, i) => (
            <div key={i} className="glass-panel animate-fade-in" style={{ 
              display: "flex", 
              justifyContent: "space-between", 
              alignItems: "center", 
              padding: "1.2rem 2rem",
              flexWrap: "wrap",
              gap: "1.5rem"
            }}>
              <div>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.2rem" }}>{h.title}</h3>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>{h.genres}</span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "2rem", minWidth: "250px", flexWrap: "wrap" }}>
                {/* Confidence metrics */}
                <div style={{ flexGrow: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: "0.2rem" }}>
                    <span>Confidence Score</span>
                    <span style={{ color: "var(--primary)" }}>{h.confidence}%</span>
                  </div>
                  <div className="progress-container">
                    <div className="progress-bar" style={{ width: `${h.confidence}%` }}></div>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-dimmed)", display: "block" }}>Logged at</span>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{h.recommended_at}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ textAlign: "center", padding: "6rem 2rem" }}>
          <span style={{ fontSize: "3.5rem" }}>⏳</span>
          <h3 style={{ marginTop: "1rem", fontSize: "1.5rem" }}>No history found</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "0.5rem" }}>
            History is logged as the AI engine generates personalized recommendations.
          </p>
        </div>
      )}
    </div>
  );
}
